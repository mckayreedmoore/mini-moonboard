"""Prepare exact radial wall-pressure placement of frozen bore resultants.

Only finite boundary algebra is available here. The angular pressure shape is
explicit, nonunique and unrelated to a new contact or timber stress solution.
Parent owns execution of the algebraic coupon and frozen-state mapping.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from itertools import pairwise
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/corner-bore-wall"
FIRST = HERE / "rawlocal/corner-first-order/attempt01/checks.json"
TIMBER = HERE / "rawlocal/corner-timber-sections/attempt02/checks.json"
CUTS = HERE / "rawlocal/corner-timber-sections/attempt02/cut-records.jsonl.gz"
SECTION_HELPER = HERE / "corner-timber-sections.py"
PINS = {
    FIRST: "b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe",
    TIMBER: "8b954edf5743999f427d2b99fcaaf9288578f02dc59a5cf1e632da634aa2e813",
    CUTS: "0294778e879733fd28c72fe4c2a9e246569d02ce0176ca58b6a0fbd11f650372",
    SECTION_HELPER: "d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633",
    HERE
    / "corner-timber-sections.md": "d7bc45e991a25396bf0ef2be48fe6a313c2229c77c7aa25e385fafa83e612fca",
    HERE
    / "cleat-traction.py": "2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764",
    HERE
    / "cleat-traction.md": "f382740c32bd81eb39c2f52af3e1a5b77ed724a91fb7315075de40ff7658d19c",
    HERE
    / "block-group-resistance.py": "e5df5f81168a0e700948816a5c292c521593b328ab86fb72b1a2e2f0cd98b3b0",
    HERE
    / "block-group-resistance.md": "8bcfbef56e69fb203fcc87a95c16df4d6eb16b7c544d83359dbf0b74c66bab77",
}
ANGLE_TOL = 1e-12
GEOMETRY_TOL = 1e-6


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, f"changed frozen input: {path}")


def module(path, name):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    require(
        spec is not None and spec.loader is not None, "arithmetic helper unavailable"
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def point_wrench(point, force, datum):
    force = np.asarray(force, dtype=float)
    return np.r_[force, np.cross(np.asarray(point) - datum, force)]


def wall_support(point, axis, radius, geom, identity):
    """Certify the whole circumference in stock and outside every other bore.

    The distance-minus-radius bound is conservative for different cylinder
    directions. Failure refuses this mapping; it is not a feasibility solve.
    """
    rows = np.array(geom["grain_frame_rows_xyz"])
    local = rows @ (np.asarray(point) - geom["start_xyz_mm"])
    axis_local = rows @ np.asarray(axis)
    reach = radius * np.sqrt(np.maximum(0, 1 - axis_local**2))
    width, depth = geom["width_depth_mm"]
    low = np.array([0.0, -width / 2, -depth / 2])
    high = np.array([geom["grain_length_mm"], width / 2, depth / 2])
    stock_margins = np.minimum(local - reach - low, high - local - reach)
    other_margins = {}
    for bore in geom["bores"]:
        if bore["axis_id"] == identity:
            continue
        j = bore["removed_interval_axis"]
        distance = math.hypot(
            local[0] - bore["station_mm"], local[j] - bore["transverse_center_mm"]
        )
        other_margins[bore["axis_id"]] = distance - radius - bore["radius_mm"]
    supported = (
        min(stock_margins) >= -GEOMETRY_TOL
        and min(other_margins.values(), default=math.inf) > GEOMETRY_TOL
    )
    return {
        "whole_circumference_support_certified": bool(supported),
        "stock_coordinate_margins_mm": stock_margins.tolist(),
        "other_cylinder_clearance_lower_bounds_mm": other_margins,
        "missing_assumption_if_not_certified": None
        if supported
        else "A supported angular contact domain and nonnegative radial pressure with the prescribed vector resultant are required. The fixed cosine pressure is refused; a failed conservative certificate alone is not proof that every other pressure distribution is impossible.",
    }


def pressure_profile(
    point_xyz_mm,
    force_xyz_n,
    axis_xyz,
    radius_mm,
    axial_weight_mm,
    *,
    identity="coupon",
    support=None,
):
    """Return an exact station-pressure representation, with no free couple.

    theta is relative to force unit e; h=n cross e. Pressure acts into wood
    along e*cos(theta)+h*sin(theta), on -pi/2 <= theta <= pi/2. Axial Gauss
    weight is a measure, not a constructed strip width or axial interpolation.
    """
    point, force, axis = (
        np.asarray(v, dtype=float) for v in (point_xyz_mm, force_xyz_n, axis_xyz)
    )
    require(
        point.shape == force.shape == axis.shape == (3,)
        and all(np.isfinite(v).all() for v in (point, force, axis)),
        "invalid vector",
    )
    require(
        abs(np.linalg.norm(axis) - 1) < 1e-8 and radius_mm > 0 and axial_weight_mm > 0,
        "invalid cylinder measure",
    )
    magnitude = float(np.linalg.norm(force))
    require(
        abs(force @ axis) <= 1e-9 * max(1, magnitude),
        "axial force cannot be represented by frictionless radial pressure",
    )
    if support is not None:
        require(
            support["whole_circumference_support_certified"],
            f"{identity}: unsupported cosine wall; {json.dumps(support, sort_keys=True)}",
        )
    if magnitude:
        e = force / magnitude
    else:
        seed = np.eye(3)[int(np.argmin(abs(axis)))]
        e = seed - seed @ axis * axis
        e /= np.linalg.norm(e)
    h = np.cross(axis, e)
    return {
        "axis_id": identity,
        "axis_point_xyz_mm": point.tolist(),
        "force_xyz_n": force.tolist(),
        "axis_unit_xyz": axis.tolist(),
        "radius_mm": radius_mm,
        "axial_gauss_weight_mm": axial_weight_mm,
        "pressure_basis_e_h_xyz": [e.tolist(), h.tolist()],
        "pressure_peak_mpa": 2 * magnitude / (math.pi * radius_mm * axial_weight_mm),
        "angular_force_coefficient_n": 2 * magnitude / math.pi,
        "active_angle_interval_rad": [-math.pi / 2, math.pi / 2],
        "support": support,
        "scope": "Chosen half-cosine station pressure; nonnegative, finite angular pressure, original axial quadrature measure. Not a recovered unique contact law or timber stress.",
    }


def pressure_arc_wrench(profile, datum_xyz_mm, low=-math.pi / 2, high=math.pi / 2):
    """Analytic full force/moment integral of a radial pressure arc."""
    require(
        -math.pi / 2 - ANGLE_TOL <= low <= high <= math.pi / 2 + ANGLE_TOL,
        "arc outside active pressure",
    )
    e, h = np.array(profile["pressure_basis_e_h_xyz"])
    coefficient = profile["angular_force_coefficient_n"]
    force = coefficient * (
        e * ((high - low) / 2 + (math.sin(2 * high) - math.sin(2 * low)) / 4)
        + h * (math.sin(high) ** 2 - math.sin(low) ** 2) / 2
    )
    # The radial offset cross each elemental radial force is exactly zero.
    return point_wrench(profile["axis_point_xyz_mm"], force, np.array(datum_xyz_mm))


def ray_wall_resultant(profile, datum_xyz_mm):
    """Equivalent positive point force on the actual wall, not finite pressure."""
    force = np.array(profile["force_xyz_n"])
    e = np.array(profile["pressure_basis_e_h_xyz"])[0]
    point = np.array(profile["axis_point_xyz_mm"]) + profile["radius_mm"] * e
    return {
        "point_xyz_mm": point.tolist(),
        "force_xyz_n": force.tolist(),
        "wrench_at_datum_n_nmm": point_wrench(
            point, force, np.array(datum_xyz_mm)
        ).tolist(),
        "scope": "Ray point is a force-placement witness. A concentrated point supplies no finite bearing pressure or unique distributed placement.",
    }


def coordinate_roots(a, b, target):
    """Exact roots of a*cos(theta)+b*sin(theta)=target on active half-circle."""
    amplitude = math.hypot(a, b)
    if amplitude <= ANGLE_TOL or abs(target) > amplitude + ANGLE_TOL:
        return []
    angle = math.acos(np.clip(target / amplitude, -1, 1))
    phase = math.atan2(b, a)
    roots = []
    for sign in (-1, 1):
        for turn in (-1, 0, 1):
            value = phase + sign * angle + 2 * math.pi * turn
            if -math.pi / 2 + ANGLE_TOL < value < math.pi / 2 - ANGLE_TOL:
                roots.append(value)
    return roots


def cut_pressure_arcs(profile, geom, section):
    """Partition wall pressure by grain half, adjacent wall branch and projection.

    A branch label identifies applied boundary pressure adjacent to a retained
    ligament, not the internal force in that ligament. Remote bores stay remote.
    """
    rows = np.array(geom["grain_frame_rows_xyz"])
    point = rows @ (np.array(profile["axis_point_xyz_mm"]) - geom["start_xyz_mm"])
    e, h = np.array(profile["pressure_basis_e_h_xyz"]) @ rows.T
    radius = profile["radius_mm"]
    station = section["station_mm"]
    bore = next(b for b in geom["bores"] if b["axis_id"] == profile["axis_id"])
    j = bore["removed_interval_axis"]
    intersecting = abs(station - bore["station_mm"]) < radius - ANGLE_TOL
    boundaries = [(0, station), (j, bore["transverse_center_mm"])]
    for region in section["regions"]:
        for coordinate in (1, 2):
            boundaries.extend(
                (coordinate, value) for value in region["bounds_uv_mm"][coordinate - 1]
            )
    angles = [-math.pi / 2, math.pi / 2]
    for coordinate, target in boundaries:
        angles.extend(
            coordinate_roots(
                radius * e[coordinate],
                radius * h[coordinate],
                target - point[coordinate],
            )
        )
    angles = sorted({round(a, 14) for a in angles})
    datum = np.array(geom["start_xyz_mm"]) + station * rows[0]
    output = []
    for low, high in pairwise(angles):
        if high - low <= ANGLE_TOL:
            continue
        theta = (low + high) / 2
        normal = e * math.cos(theta) + h * math.sin(theta)
        where = point + radius * normal
        half = "negative" if where[0] < station else "positive"
        projected = [
            i
            for i, region in enumerate(section["regions"])
            if all(
                region["bounds_uv_mm"][k][0] - GEOMETRY_TOL
                <= where[k + 1]
                <= region["bounds_uv_mm"][k][1] + GEOMETRY_TOL
                for k in (0, 1)
            )
        ]
        adjacent = []
        branch = "remote_bore_end_bridge"
        if intersecting:
            chord = math.sqrt(max(0, radius**2 - (station - bore["station_mm"]) ** 2))
            side = -1 if normal[j] < 0 else 1
            edge = bore["transverse_center_mm"] + side * chord
            branch = "lower_wall" if side < 0 else "upper_wall"
            other = 3 - j
            candidates = []
            for i, region in enumerate(section["regions"]):
                bounds = region["bounds_uv_mm"]
                if (
                    not bounds[other - 1][0] - GEOMETRY_TOL
                    <= where[other]
                    <= bounds[other - 1][1] + GEOMETRY_TOL
                ):
                    continue
                own = bounds[j - 1]
                if (side < 0 and own[1] <= edge + GEOMETRY_TOL) or (
                    side > 0 and own[0] >= edge - GEOMETRY_TOL
                ):
                    candidates.append((abs((own[1] if side < 0 else own[0]) - edge), i))
            if candidates:
                nearest = min(x[0] for x in candidates)
                adjacent = [
                    i
                    for distance, i in candidates
                    if abs(distance - nearest) < GEOMETRY_TOL
                ]
        output.append(
            {
                "angle_interval_rad": [low, high],
                "grain_half": half,
                "wall_branch": branch,
                "adjacent_cut_region_ids": adjacent,
                "projection_at_cut_region_ids": projected,
                "boundary_wrench_at_cut_n_nmm": pressure_arc_wrench(
                    profile, datum, low, high
                ).tolist(),
                "scope": "Applied wall-branch pressure only. Projection/adjacency labels assign no regional internal wrench; remote/end-bridge transfer and cross-branch sharing are uncalculated.",
            }
        )
    return output


def state_profiles(state, geom):
    """Match every cleat bore sample against the frozen applied-action inventory."""
    output = []
    for host in state["hosts"].values():
        family = host["geometry"]
        for bolt in host["state"]["bolts"]:
            identity = bolt["axis_id"]
            n = np.array(bolt["bolt_axis_head_to_nut_xyz"])
            bore = next(b for b in geom["bores"] if b["axis_id"] == identity)
            source = [
                a
                for a in state["physical_cleat_actions"]
                if a["kind"] == "bore_station_resultant" and a["identity"] == identity
            ]
            fields = [f for f in bolt["bore_fields"] if f["receiver"] == "cleat"]
            require(
                len(source) == len(fields) == 24, "actual bore sample census differs"
            )
            for index, (action, field) in enumerate(zip(source, fields, strict=True)):
                point = (
                    np.array(bolt["interface_point_xyz_mm"])
                    + (field["x_mm"] - family["host_length_mm"]) * n
                )
                force = -np.array(field["force_on_beam_xyz_n"])
                require(
                    np.max(abs(point - action["point_xyz_mm"])) < 1e-8
                    and np.max(abs(force - action["force_xyz_n"])) < 1e-8,
                    "saved bore resultant differs",
                )
                certificate = wall_support(point, n, bore["radius_mm"], geom, identity)
                profile = pressure_profile(
                    point,
                    force,
                    n,
                    bore["radius_mm"],
                    field["quadrature_weight_mm"],
                    identity=identity,
                    support=certificate,
                )
                profile["quadrature_index"] = index
                profile["source_axis_bearing_pressure_mpa"] = field["pressure_mpa"]
                output.append(profile)
    return output


def map_state_cut(state, geom, baseline_cut, profiles, section_helper):
    """Replace bore placement in one complete saved cut, keeping other loads once."""
    rows = np.array(geom["grain_frame_rows_xyz"])
    station, limit = baseline_cut["station_mm"], baseline_cut["limit"]
    section = section_helper.section(geom, station)
    datum = np.array(geom["start_xyz_mm"]) + station * rows[0]
    axis_negative, wall_negative = np.zeros(6), np.zeros(6)
    branch_wrenches = defaultdict(lambda: np.zeros(6))
    records = []
    for profile in profiles:
        distance = (np.array(profile["axis_point_xyz_mm"]) - datum) @ rows[0]
        included = distance < -GEOMETRY_TOL or (
            limit == "after" and distance <= GEOMETRY_TOL
        )
        original = point_wrench(
            profile["axis_point_xyz_mm"], profile["force_xyz_n"], datum
        )
        if included:
            axis_negative += original
        arcs = cut_pressure_arcs(profile, geom, section)
        mapped = np.sum([a["boundary_wrench_at_cut_n_nmm"] for a in arcs], axis=0)
        require(
            np.max(abs(mapped - original)) < 1e-6,
            "radial arc mapping changed full wrench",
        )
        for arc in arcs:
            value = np.array(arc["boundary_wrench_at_cut_n_nmm"])
            if arc["grain_half"] == "negative":
                wall_negative += value
            identity = (
                profile["axis_id"],
                arc["grain_half"],
                arc["wall_branch"],
                tuple(arc["adjacent_cut_region_ids"]),
                tuple(arc["projection_at_cut_region_ids"]),
            )
            branch_wrenches[identity] += value
        records.append(
            {
                "axis_id": profile["axis_id"],
                "quadrature_index": profile["quadrature_index"],
                "arcs": arcs,
            }
        )
    old_grain = np.array(baseline_cut["negative_half_internal_grain_u_v_n_nmm"])
    old_global = np.r_[rows.T @ old_grain[:3], rows.T @ old_grain[3:]]
    delta = axis_negative - wall_negative
    revised = old_global + delta
    return {
        "side": state["side"],
        "case_id": state["case_id"],
        "station_mm": station,
        "limit": limit,
        "datum_xyz_mm": datum.tolist(),
        "section": section,
        "source_axis_negative_half_external_bore_n_nmm": axis_negative.tolist(),
        "cosine_wall_negative_half_external_bore_n_nmm": wall_negative.tolist(),
        "complete_saved_cut_grain_u_v_n_nmm": old_grain.tolist(),
        "bore_placement_cut_correction_grain_u_v_n_nmm": np.r_[
            rows @ delta[:3], rows @ delta[3:]
        ].tolist(),
        "cosine_wall_complete_cut_grain_u_v_n_nmm": np.r_[
            rows @ revised[:3], rows @ revised[3:]
        ].tolist(),
        "applied_wall_branch_wrenches": [
            {
                "axis_id": key[0],
                "grain_half": key[1],
                "wall_branch": key[2],
                "adjacent_cut_region_ids": list(key[3]),
                "projection_at_cut_region_ids": list(key[4]),
                "wrench_at_cut_n_nmm": value.tolist(),
                "wrench_grain_u_v_n_nmm": np.r_[
                    rows @ value[:3], rows @ value[3:]
                ].tolist(),
            }
            for key, value in sorted(branch_wrenches.items())
        ],
        "sample_arc_allocation": records,
        "regional_internal_wrenches_established": False,
        "nonbore_actions_and_original_W": "Retained once through the saved complete-cut baseline; only bore-wall placement is replaced.",
        "balancing_free_couples_added": 0,
    }


def partial_wall_obstruction(supported_angle_intervals):
    """Necessary cone obstruction for a target along e; no pressure fitting."""
    maxima = []
    for low, high in supported_angle_intervals:
        require(
            -math.pi - ANGLE_TOL <= low <= high <= math.pi + ANGLE_TOL,
            "supported intervals must use relative angles in [-pi,pi]",
        )
        candidates = [math.cos(low), math.cos(high)]
        if any(low <= 2 * math.pi * turn <= high for turn in (-1, 0, 1)):
            candidates.append(1.0)
        maxima.append(max(candidates))
    excluded = not maxima or max(maxima) <= ANGLE_TOL
    return {
        "target_positive_e_component_cannot_be_carried": excluded,
        "supported_normal_maximum_dot_e": max(maxima) if maxima else None,
        "proof_if_excluded": "Every supported radial normal has nonpositive projection on the prescribed positive-e force. Nonnegative pressure cannot produce that force."
        if excluded
        else None,
        "scope": "Necessary cone obstruction only. Absence of obstruction does not recover a supported pressure shape or establish compatibility.",
    }


def algebraic_coupon():
    """Prepared known answers; parent may execute, no mechanics model involved."""
    point, force, datum = [3.0, 4.0, 5.0], [10.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    profile = pressure_profile(point, force, [0.0, 0.0, 1.0], 2.0, 5.0)
    full = pressure_arc_wrench(profile, datum)
    upper = pressure_arc_wrench(profile, datum, 0, math.pi / 2)
    lower = pressure_arc_wrench(profile, datum, -math.pi / 2, 0)
    expected = np.array([10, 0, 0, 0, 50, -40], dtype=float)
    expected_upper = np.array(
        [5, 10 / math.pi, 0, -50 / math.pi, 25, 30 / math.pi - 20]
    )
    # Grain X cut at x=4: radius=2, shaft station x=3 gives cos(theta)=1/2.
    positive = pressure_arc_wrench(profile, datum, -math.pi / 3, math.pi / 3)
    known_positive_force = 20 / 3 + 5 * math.sqrt(3) / math.pi
    obstruction = partial_wall_obstruction(
        [[-math.pi, -math.pi / 2], [math.pi / 2, math.pi]]
    )
    errors = [
        np.max(abs(full - expected)),
        np.max(abs(upper - expected_upper)),
        np.max(abs(upper + lower - full)),
        abs(positive[0] - known_positive_force),
        abs(profile["pressure_peak_mpa"] - 2 / math.pi),
    ]
    require(
        max(errors) < 1e-10
        and obstruction["target_positive_e_component_cannot_be_carried"],
        "algebraic known-answer coupon differs",
    )
    return {
        "profile": profile,
        "full_wrench_expected_n_nmm": expected.tolist(),
        "full_wrench_returned_n_nmm": full.tolist(),
        "upper_half_expected_n_nmm": expected_upper.tolist(),
        "upper_half_returned_n_nmm": upper.tolist(),
        "lower_half_returned_n_nmm": lower.tolist(),
        "x4_cut_positive_force_expected_n": known_positive_force,
        "x4_cut_positive_wrench_returned_n_nmm": positive.tolist(),
        "ray": ray_wall_resultant(profile, datum),
        "partial_wall_obstruction": obstruction,
        "maximum_arithmetic_error": float(max(errors)),
        "scope": "Finite exact angular integration and full-wrench placement coupon only; no solver, material or resistance.",
    }


def run(args):
    output = args.output.resolve()
    require(
        output.is_relative_to(RAW) and not output.exists(),
        "fresh owned raw output required",
    )
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__))}
    first, timber = read(FIRST), read(TIMBER)
    for record in (first, timber):
        for relative, digest in record["source_sha256"].items():
            path = Path(relative)
            path = path if path.is_absolute() else ROOT / path
            require(path not in pins or pins[path] == digest, "conflicting input pin")
            pins[path] = digest
    authenticate(pins)
    coupon = algebraic_coupon()
    result = {
        "schema": "corner_radial_wall_boundary/v1",
        "algebraic_coupon": coupon,
        "source_sha256": {
            str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): d
            for p, d in sorted(pins.items())
        },
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
        "pressure_shape_assumption": "Nonnegative half-cosine radial pressure at each original axial Gauss station. This shape is chosen, not inferred uniquely from the saved force or penetration law.",
        "balancing_free_couples_added": 0,
    }
    if not args.coupon_only:
        require(
            first["failure"] is None and len(first["states"]) == 12,
            "completed first-order source required",
        )
        helper = module(SECTION_HELPER, "frozen_bore_wall_section_arithmetic")
        summaries, all_profiles, profiles_by_state = [], [], {}
        for state in first["states"]:
            geom = timber["geometry"][state["side"]]
            profiles = state_profiles(state, geom)
            require(len(profiles) == 96, "four cleat bore quadratures required")
            datum = np.array(state["common_datum_xyz_mm"])
            old, mapped = np.zeros(6), np.zeros(6)
            for p in profiles:
                old += point_wrench(p["axis_point_xyz_mm"], p["force_xyz_n"], datum)
                mapped += pressure_arc_wrench(p, datum)
            require(
                np.max(abs(mapped - old)) < 1e-6,
                "wall mapping changed complete bore wrench",
            )
            summaries.append(
                {
                    "side": state["side"],
                    "case_id": state["case_id"],
                    "bore_station_count": len(profiles),
                    "source_bore_wrench_n_nmm": old.tolist(),
                    "mapped_bore_wrench_n_nmm": mapped.tolist(),
                    "mapped_minus_source_n_nmm": (mapped - old).tolist(),
                    "preserved_whole_cleat_residual_n_nmm": state[
                        "physical_whole_cleat_residual_n_nmm"
                    ],
                }
            )
            profiles_by_state[(state["side"], state["case_id"])] = profiles
            all_profiles.extend(
                {"side": state["side"], "case_id": state["case_id"], **p}
                for p in profiles
            )
        target_stations = {}
        for side, case in (("right", "k12-rear"), ("left", "a12-left")):
            saved = next(
                s
                for s in timber["states"]
                if s["side"] == side and s["case_id"] == case
            )
            target_stations[(side, case)] = [
                saved["deciding_unallocated_bore_section_witness"]["cut"]["station_mm"],
                next(
                    c["cut"]["station_mm"]
                    for c in saved["bolt_center_sections"]
                    if "/side_" in c["axis_id"]
                ),
            ]
        mappings = []
        with gzip.open(CUTS, "rt") as stream:
            for line in stream:
                cut = json.loads(line)
                key = (cut["side"], cut["case_id"])
                if key not in target_stations or not any(
                    abs(cut["station_mm"] - s) < 1e-9 for s in target_stations[key]
                ):
                    continue
                state = next(
                    s for s in first["states"] if (s["side"], s["case_id"]) == key
                )
                mappings.append(
                    map_state_cut(
                        state,
                        timber["geometry"][key[0]],
                        cut,
                        profiles_by_state[key],
                        helper,
                    )
                )
        require(len(mappings) == 8, "both limits of four target cuts required")
        result.update(
            {
                "states": summaries,
                "wall_pressure_profiles": all_profiles,
                "deciding_cut_mappings": mappings,
                "remaining_requirement": "Applied wall branches and exact cut-placement corrections are available under the chosen cosine profile. Ligament internal forces, end-bridge transfer, timber stress/warping and interaction/resistance remain unestablished; no regional sharing or Ft-perpendicular is assigned.",
            }
        )
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    dump(output / "checks.json", result)
    dump(
        output / "receipt.json",
        {
            "source_sha256": result["source_sha256"],
            "output_sha256": {
                name: sha(output / name)
                for name in ("checks.json", "producer.py.snapshot")
            },
        },
    )
    print(
        json.dumps(
            {
                "checks_sha256": sha(output / "checks.json"),
                "mapped_state_count": len(result.get("states", [])),
                "deciding_cut_count": len(result.get("deciding_cut_mappings", [])),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--coupon-only", action="store_true")
    run(parser.parse_args())
