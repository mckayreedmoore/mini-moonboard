"""Finite signed cut assessment of the twenty remaining registered cleats.

Parent executes the frozen arithmetic. Mechanical point forces/free couples
remain the source idealization. Only mapped gravity is replaced by physical
retained-timber gravity and original allocated hardware point wrenches.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.machinery
import importlib.util
import json
import math
import sys
from functools import cache
from itertools import combinations, pairwise, product
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
HERE = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout"
)
RAW = HERE / "rawlocal/remaining-block-transverse"
MEMBERS = HERE.parent / "member-screen-attempt02/four-screw-layout01"
PHYSICAL = (
    HERE / "rawlocal/corner-physical-gravity/grain-attempt02/producer.py.snapshot"
)
NORMAL = (
    HERE
    / "rawlocal/corner-split-closure/finite-pressure-attempt01/producer.py.snapshot"
)
LONG = HERE / "longitudinal-bore-geometry.py"
LONG_CHECK = HERE / "rawlocal/longitudinal-bore-geometry/coupon-attempt02/checks.json"
LONG_RECEIPT = LONG_CHECK.with_name("receipt.json")
ADAPTER = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
)
MASS = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-centroids-attempt01/mass-centroids.json"
)
CONTACTS = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json"
)
CURRENT = HERE / "operators-attempt02/model.json"
ROWS = HERE / "operators-attempt02/row-identities.json"
REGISTER = HERE / "rawlocal/joint-register/attempt01/register.json"
MATERIAL = (
    HERE.parents[1] / "hardware-material-specification-2026-09-30/material-inputs.json"
)
TOL = 1e-6
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PACKETS = {
    HERE
    / "rawlocal/header-cleat-net-sections/attempt01/checks.json": "b70fd818654a4d6509186a2718a81fa0b564cfc7ad808be52946f0eddfead1a2",
    HERE
    / "rawlocal/knee-spine-net-sections/attempt02/checks.json": "6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85",
    HERE
    / "rawlocal/remaining-net-sections/attempt01/checks.json": "80600628f956f5a957efca382d2c4e2ca9110cefbff8c7aee21a1995a430892f",
}
PINS = {
    **PACKETS,
    PHYSICAL: "7666448f5f841d9a6d8a5cccededbb8047ec75df7463a4dd7c4a27a47693cf94",
    NORMAL: "e090270a3bea195800ed3b04b806fe4ea0c5e221ae57faf01f602c8dba769d5e",
    LONG: "faab8b5e5ff13dc4252329ed2f8917d9e2054f05e823a4e5fdbeb11da46accc4",
    LONG_CHECK: "b397fbe1a6b673401df4c61666eab2b1a3539a22319bba162af83ea57eef6aee",
    LONG_RECEIPT: "9ee33a58d6567d62529dee5bd7338eaf4ffd38ef572da8b4e29435ee6392aee3",
    ADAPTER: "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8",
    MASS: "4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a",
    CONTACTS: "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    CURRENT: "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    ROWS: "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    REGISTER: "79db8c6830dee42e47dcdcd75c331ce22a67cd3d27e38f9a8b616e820c37d3ca",
}


class UnsupportedBody(ValueError):
    """Stop only a body whose source or geometry does not support this method."""


def supported(condition, message):
    if not condition:
        raise UnsupportedBody(message)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def key(path):
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, f"changed frozen source: {path}")


def module(path):
    loader = importlib.machinery.SourceFileLoader(
        "remaining_" + path.stem.replace("-", "_"), str(path)
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    result = importlib.util.module_from_spec(spec)
    loader.exec_module(result)
    return result


def bounds3(geom):
    return [
        [0.0, geom["grain_length_mm"]],
        *[[-d / 2, d / 2] for d in geom["width_depth_mm"]],
    ]


def cylinders(geom):
    """Coordinates of the source-certified full, axis-aligned openings."""
    bounds = bounds3(geom)
    result = []
    for bore in geom["bores"]:
        shaft = 3 - bore["removed_interval_axis"]
        center = [0.0, 0.0, 0.0]
        center[0] = bore["station_mm"]
        center[bore["removed_interval_axis"]] = bore["transverse_center_mm"]
        center[shaft] = sum(bounds[shaft]) / 2
        result.append(
            {
                "axis_id": bore["axis_id"],
                "shaft": shaft,
                "center": center,
                "radius": bore["radius_mm"],
            }
        )
    for bore in geom.get("longitudinal_holes", []):
        result.append(
            {
                "axis_id": bore["axis_id"],
                "shaft": 0,
                "center": [geom["grain_length_mm"] / 2, *bore["disk_center_uv_mm"]],
                "radius": bore["radius_mm"],
            }
        )
    return result


def geometry_certificate(geom):
    """Certify retained hull corners and disjoint subtraction, not strength."""
    bounds, bores = bounds3(geom), cylinders(geom)
    supported(len(bores) == 4, "expected four source-certified cylinders")
    clearances = []
    for bore in bores:
        for axis in range(3):
            if axis != bore["shaft"]:
                lo, hi = bounds[axis]
                margin = min(
                    bore["center"][axis] - bore["radius"] - lo,
                    hi - bore["center"][axis] - bore["radius"],
                )
                supported(
                    margin > TOL, "opening reaches a hull corner or bounding edge"
                )
                clearances.append(margin)
    for a, b in combinations(bores, 2):
        if a["shaft"] == b["shaft"]:
            axes = [i for i in range(3) if i != a["shaft"]]
            distance = math.hypot(*[a["center"][i] - b["center"][i] for i in axes])
        else:
            axis = next(i for i in range(3) if i not in (a["shaft"], b["shaft"]))
            distance = abs(a["center"][axis] - b["center"][axis])
        supported(
            distance > a["radius"] + b["radius"] + TOL,
            "cylinder subtraction not certified disjoint",
        )
    return {
        "full_rectangular_stock_with_four_disjoint_cylinders": True,
        "all_cut_hull_corners_retained": True,
        "minimum_radial_boundary_clearance_mm": min(clearances),
    }


def rectangle_supported(geom, axis, station, rectangle):
    """Exact nearest-distance exclusion of circular or strip voids in a cut."""
    plane_axes = [(axis + 1) % 3, (axis + 2) % 3]
    for bore in cylinders(geom):
        if bore["shaft"] == axis:
            distance2 = 0.0
            for i, own_axis in enumerate(plane_axes):
                lo, hi = rectangle[i]
                center = bore["center"][own_axis]
                distance2 += max(lo - center, 0, center - hi) ** 2
        else:
            other = next(i for i in range(3) if i not in (axis, bore["shaft"]))
            lo, hi = rectangle[plane_axes.index(other)]
            center = bore["center"][other]
            distance2 = (station - bore["center"][axis]) ** 2 + max(
                lo - center, 0, center - hi
            ) ** 2
        if distance2 < bore["radius"] ** 2 - 1e-8:
            return False
    return True


def finite_pressure(q, geom, axis, station, normal_math):
    """Existing two end bands, or four clear edge/end bands around long holes."""
    normal = normal_math.normal_bound(
        q, [bounds3(geom)[i] for i in ((axis + 1) % 3, (axis + 2) % 3)]
    )
    if normal["minimum_tensile_normal_resultant_n"] > 0:
        return {"status": "NECESSARY_NORMAL_TENSION", **normal}
    if not geom.get("longitudinal_holes"):
        result = normal_math.finite_band_pressure(q, geom, axis)
    elif q[0] == 0:
        result = {"status": "ZERO_NORMAL_WRENCH", "pressure_peak_mpa": 0.0}
    else:
        axes = [(axis + 1) % 3, (axis + 2) % 3]
        g_index = axes.index(0)
        t_index, transverse_axis = 1 - g_index, next(i for i in (1, 2) if i != axis)
        centroid = [-q[5] / q[0], q[4] / q[0]]
        length = geom["grain_length_mm"]
        low, high = bounds3(geom)[transverse_axis]
        grain_clear = min(
            min(
                b["station_mm"] - b["radius_mm"],
                length - b["station_mm"] - b["radius_mm"],
            )
            for b in geom["bores"]
        )
        transverse_clear = (high - low) / 2
        for bore in geom["longitudinal_holes"]:
            center = bore["disk_center_uv_mm"]
            offset = station - center[axis - 1]
            if abs(offset) < bore["radius_mm"]:
                chord = math.sqrt(bore["radius_mm"] ** 2 - offset**2)
                other_center = center[transverse_axis - 1]
                transverse_clear = min(
                    transverse_clear,
                    other_center - chord - low,
                    high - other_center - chord,
                )
        g, t = centroid[g_index], centroid[t_index]
        height = min(grain_clear, length / 2, 2 * min(g, length - g))
        width = min(transverse_clear, (high - low) / 2, 2 * min(t - low, high - t))
        if min(width, height) <= 0:
            return {"status": "NO_FINITE_SUPPORTED_BAND_WITNESS", **normal}
        fg = (g - height / 2) / (length - height)
        ft = (t - low - width / 2) / (high - low - width)
        require(
            min(fg, ft) >= -1e-12 and max(fg, ft) <= 1 + 1e-12, "negative band fraction"
        )
        fg, ft = np.clip([fg, ft], 0, 1)
        patches, recovered = [], np.zeros(3)
        for g_end, t_end in product(range(2), repeat=2):
            g_bounds = [0.0, height] if not g_end else [length - height, length]
            t_bounds = [low, low + width] if not t_end else [high - width, high]
            rectangle = [g_bounds, t_bounds] if g_index == 0 else [t_bounds, g_bounds]
            center = np.mean(rectangle, axis=1)
            force = q[0] * (fg if g_end else 1 - fg) * (ft if t_end else 1 - ft)
            recovered += force * np.r_[1.0, center]
            patches.append(
                {
                    "bounds_pq_mm": rectangle,
                    "centroid_pq_mm": center.tolist(),
                    "compressive_force_n": float(-force),
                    "area_mm2": width * height,
                    "constant_pressure_mpa": float(-force / (width * height)),
                }
            )
        error = float(np.max(abs(recovered - [q[0], -q[5], q[4]])))
        require(error < 1e-7, "finite four-band normal-wrench recovery differs")
        result = {
            "status": "FINITE_COMPRESSION_EDGE_END_BAND_WITNESS",
            "patches": patches,
            "pressure_peak_mpa": max(p["constant_pressure_mpa"] for p in patches),
            "maximum_normal_recovery_error_n_nmm": error,
        }
    if "patches" in result:
        require(
            all(
                rectangle_supported(geom, axis, station, p["bounds_pq_mm"])
                for p in result["patches"]
            ),
            "compression rectangle enters an actual cylinder void",
        )
        result["every_pressure_patch_in_retained_material"] = True
    result["retained_full_signed_cut_n_nmm"] = q
    result["unresolved_shear_shear_torque_n_n_nmm"] = q[1:4]
    return result


def pressure_coupon(normal_math):
    geom = {
        "grain_length_mm": 10.0,
        "width_depth_mm": [10.0, 10.0],
        "bores": [
            {
                "axis_id": "t",
                "removed_interval_axis": 2,
                "station_mm": 5.0,
                "transverse_center_mm": 3.0,
                "radius_mm": 1.0,
            }
        ],
        "longitudinal_holes": [
            {"axis_id": "l", "disk_center_uv_mm": [0.0, 0.0], "radius_mm": 1.0}
        ],
    }
    q = [-10.0, 7.0, -3.0, 11.0, -50.0, 0.0]
    result = finite_pressure(q, geom, 1, 0.0, normal_math)
    require(
        abs(result["pressure_peak_mpa"] - 0.15625) < 1e-12,
        "longitudinal-hole finite-band known answer differs",
    )
    require(
        result["unresolved_shear_shear_torque_n_n_nmm"] == [7.0, -3.0, 11.0],
        "pressure coupon lost shear/torque",
    )
    return {
        "known_answer_satisfied": True,
        "expected_peak_pressure_mpa": 0.15625,
        **result,
    }


def action_prepared(physical_math, points, values, frame, start):
    actions = [
        {"point_xyz_mm": p, "force_xyz_n": q[:3], "free_couple_xyz_nmm": q[3:]}
        for p, q in zip(points, values, strict=True)
    ]
    return physical_math.prepare_points(actions, frame, start)


def cut_events(geom, points, hardware, vertices, axis):
    lo, hi = bounds3(geom)[axis]
    values = [*points[:, axis], *hardware[0][:, axis], *[v[axis] for v in vertices]]
    for bore in cylinders(geom):
        if bore["shaft"] != axis:
            values.extend(
                [
                    bore["center"][axis] - bore["radius"],
                    bore["center"][axis],
                    bore["center"][axis] + bore["radius"],
                ]
            )
    values.extend([lo + 1e-4, (lo + hi) / 2, hi - 1e-4])
    events = []
    for v in sorted(float(v) for v in values if lo + TOL < v < hi - TOL):
        if not events or v - events[-1] > TOL:
            events.append(v)
    return sorted(set(events + [(a + b) / 2 for a, b in pairwise(events)]))


def prepare_body(
    body,
    geom,
    member,
    adapter,
    masses,
    current,
    contacts,
    physical_math,
    long_math,
    factor,
):
    geometry = member["geometry"]
    frame = np.array([geometry[k] for k in ("axis", "section_u", "section_v")])
    start = np.array(geometry["start"])
    supported(
        np.max(abs(frame @ frame.T - np.eye(3))) < 1e-8
        and abs(np.linalg.det(frame) - 1) < 1e-8,
        "invalid right-handed local frame",
    )
    supported(
        abs(
            float(frame[0] @ (np.array(geometry["end"]) - start))
            - geom["grain_length_mm"]
        )
        < TOL,
        "grain length differs from source geometry",
    )
    supported(
        max(
            abs(
                np.array(geom["width_depth_mm"])
                - [geometry["width_mm"], geometry["depth_mm"]]
            )
        )
        < TOL,
        "stock dimensions differ from source geometry",
    )
    supported(
        not member["replaced_original_bore_features"]
        and member["recess_source"] is None,
        "changed source opening/recess geometry",
    )
    supported(
        body not in {r["body"] for r in current["wood_mass_changes"]},
        "current mass delta requires another physical field",
    )
    certificate = geometry_certificate(geom)
    volume_function = (
        long_math.volume_first
        if geom.get("longitudinal_holes")
        else physical_math.volume_first
    )
    volume, first = volume_function(geom, 0, geom["grain_length_mm"])
    first = np.asarray(first)
    source = next(
        r
        for r in adapter["gravity_load_audits"]["member_self_weight_rows"]
        if r["body"] == body
    )
    mass = next(r for r in masses["rows"] if r["name"] == body)
    center = start + frame.T @ (first / volume)
    density = source["source_mass_kg"] / volume * 1e9
    supported(
        abs(volume - geom["analytic_finished_volume_mm3"]) < 0.001
        and abs(volume - mass["current_volume_mm3"]) < 0.001,
        "retained volume contradicts source shape/mass",
    )
    supported(
        abs(density - mass["density_kg_m3"]) < TOL and mass["density_kg_m3"] == 600.0,
        "uniform density contradicts original600 source",
    )
    supported(
        np.max(abs(center - source["source_centroid_xyz_mm"])) < TOL,
        "retained centroid contradicts source selfweight",
    )
    hardware = [
        {
            "point_xyz_mm": r["application_point_xyz_mm"],
            "force_xyz_n": r["force_xyz_n"],
            "free_couple_xyz_nmm": r["couple_xyz_nmm_about_application_point"],
            "source_name": r["source_name"],
        }
        for r in adapter["gravity_load_audits"]["hardware_receiver_point_loads"]
        if r["receiver_body"] == body
    ]
    supported(len(hardware) == 12, "hardware receiver inventory differs")
    supported(
        set(adapter["physical_load_sources_by_body"][body])
        == {body, *[r["source_name"] for r in hardware]},
        "body load ownership includes a source other than selfweight/hardware",
    )
    cell_map = {
        c["name"]: c
        for c in adapter["contact_cell_ownership"]
        if c["kind"] == "timber_or_panel_contact"
    }
    vertices = []
    for row_id, role in zip(
        member["point_action_ids"], member["point_action_roles"], strict=True
    ):
        if role != "timber_or_panel_contact":
            continue
        supported(row_id in cell_map, "contact point lacks its original patch geometry")
        patch = contacts["contact_patches"][cell_map[row_id]["source_patch_index"]]
        supported(body in patch["member_ids"], "contact patch ownership differs")
        vertices.extend((np.array(patch["vertices_xyz_mm"]) - start) @ frame.T)
    body_force = frame @ np.array(source["gravity_force_xyz_n"]) * factor / volume
    hw = physical_math.prepare_points(hardware, frame, start, factor)
    full_gravity = np.r_[volume * body_force, np.cross(first, body_force)] + hw[1].sum(
        axis=0
    )
    return {
        "geom": geom,
        "frame": frame,
        "start": start,
        "volume_function": volume_function,
        "body_force": body_force,
        "hardware": hw,
        "vertices": vertices,
        "full_gravity": full_gravity,
        "certificate": certificate,
        "source_density_kg_m3": mass["density_kg_m3"],
        "retained_density_implied_by_source_mass_kg_m3": density,
        "retained_volume_mm3": volume,
        "retained_centroid_xyz_mm": center.tolist(),
    }


def grain_nominal(q, geom, station, sections, net, header, refs):
    section = (
        header.subset_section(geom, station, sections)
        if geom.get("longitudinal_holes")
        else sections.section(geom, station)
    )
    nominal = net.nominal_section(q, section["regions"], refs)
    corners = [c for r in nominal["regions"] for c in r["longitudinal_corners"]]
    metrics = {
        "tension_over_Ft": max(
            c["comparisons"]["total_tension_over_Ft"] for c in corners
        ),
        "compression_over_Fc": max(
            c["comparisons"]["total_compression_over_Fc"] for c in corners
        ),
        "bending_over_Fb": max(
            c["comparisons"]["absolute_bending_over_Fb"] for c in corners
        ),
        "axial_plus_bending_reference_sum": max(
            c["comparisons"]["axial_plus_bending_reference_sum"] for c in corners
        ),
        "regional_shear_torsion_over_Fv": max(
            r["same_state_shear_bound_over_Fv"] for r in nominal["regions"]
        ),
    }
    return {
        "metrics": metrics,
        "regions": nominal["regions"],
        "section_scope": "Original artificial rectangular subset excluding longitudinal-hole strips"
        if geom.get("longitudinal_holes")
        else "Actual retained grain-section rectangles",
        "actual_net_area_mm2": section.get(
            "actual_opening_area_mm2", section["net_area_mm2"]
        ),
        "comparison_area_mm2": section["net_area_mm2"],
    }


def build(output):
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW) and output != RAW and not output.exists(),
        "fresh owned output child required",
    )
    pins, geometries = dict(PINS), {}
    authenticate(pins)
    for path in PACKETS:
        packet = read(path)
        require(
            not set(geometries) & set(packet["geometry"]),
            "duplicate body in source packets",
        )
        geometries.update(packet["geometry"])
        for name, digest in packet["source_sha256"].items():
            own = ROOT / name
            require(own not in pins or pins[own] == digest, "conflicting source pin")
            pins[own] = digest
    authenticate(pins)
    physical_math, normal_math, long_math = [
        module(p) for p in (PHYSICAL, NORMAL, LONG)
    ]
    sections, net, header = [
        module(HERE / p)
        for p in (
            "corner-timber-sections.py",
            "corner-net-section.py",
            "header-cleat-net-sections.py",
        )
    ]
    net.rectangle_torsion = cache(net.rectangle_torsion)
    require(
        HERE / "header-cleat-net-sections.py" in pins,
        "header subset helper not authenticated",
    )
    geom_data, results = [
        read(MEMBERS / p) for p in ("geometry.json", "member-results.json")
    ]
    require(
        tuple(c["case_id"] for c in results["cases"]) == CASES,
        "source six cases differ",
    )
    require(len(geometries) == 20, "expected twenty remaining bodies")
    register = read(REGISTER)
    outer = {
        "top_outer_left_cleat",
        "top_outer_right_cleat",
        "bottom_outer_left_cleat",
        "bottom_outer_right_cleat",
    }
    require(
        set(geometries) | outer == {b["block_id"] for b in register["blocks"]},
        "remaining bodies do not complete registered24",
    )
    adapter, masses, current, contacts, rows = [
        read(p) for p in (ADAPTER, MASS, CURRENT, CONTACTS, ROWS)
    ]
    factor = read(HERE / "frame-250-attempt02/comparison.json")["dead_load_factor"]
    require(
        abs(factor - results["same_state_dead_load_factor"]) < 1e-12,
        "source load factors differ",
    )
    pressure_ref = (
        read(MATERIAL)["conditional_DF_L_No2_base_row"]["base_properties"][
            "Fc_perpendicular"
        ]
        * 0.006894757293168361
    )
    accepted_long = read(LONG_CHECK)
    require(
        accepted_long["status"] == "COMPLETE_ANALYTICAL_GEOMETRY_COUPON"
        and accepted_long["analytical_coupon"]["known_answers_satisfied"],
        "parent longitudinal geometry coupon not accepted",
    )
    known = {
        "existing_transverse_volume_first": physical_math.geometric_coupon(require),
        "accepted_parent_longitudinal_geometry": accepted_long,
        "existing_normal_hull": normal_math.coupon(),
        "existing_two_band_pressure": normal_math.band_coupon(),
        "longitudinal_four_band_pressure": pressure_coupon(normal_math),
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    snapshot = output / "producer.py.snapshot"
    snapshot.write_bytes(Path(__file__).read_bytes())
    digest = sha(Path(__file__))
    pins[snapshot] = digest
    states, skipped, whole_matches, body_records, peak_t, peak_pressure, grain_peaks = (
        [],
        [],
        [],
        {},
        None,
        None,
        {},
    )
    total, transverse_total, grain_total = 0, 0, 0
    with (
        np.load(MEMBERS / "action-section-arrays.npz", allow_pickle=False) as arrays,
        gzip.open(output / "cuts.jsonl.gz", "wt") as stream,
    ):
        for body, geom in sorted(geometries.items()):
            member = geom_data["members"][body]
            try:
                own = prepare_body(
                    body,
                    geom,
                    member,
                    adapter,
                    masses,
                    current,
                    contacts,
                    physical_math,
                    long_math,
                    factor,
                )
                points = arrays[body + "__point_xyz_mm"]
                point_rows = arrays[body + "__point_rows"]
                roles = np.array(member["point_action_roles"])
                supported(
                    len(roles) == len(points) == len(point_rows),
                    "action ownership lengths differ",
                )
                gravity_mask = point_rows == -1
                supported(
                    np.array_equal(gravity_mask, roles == "discrete_body_load"),
                    "body load ownership mismatch",
                )
                row_map = {r["row"]: r for r in rows}
                for row_index, action_id, role in zip(
                    point_rows,
                    member["point_action_ids"],
                    member["point_action_roles"],
                    strict=True,
                ):
                    if row_index >= 0:
                        source_row = row_map[int(row_index)]
                        owner = source_row["ownership"]
                        supported(
                            source_row["row_id"] == action_id
                            and owner["role"] == role
                            and body in (owner["first_body"], owner["second_body"]),
                            "mechanical action row identity/ownership differs",
                        )
                prepared_cases = {}
                for case in CASES:
                    values = arrays[f"{case}__{body}__point_force_free_couple_xyz"]
                    supported(
                        values.shape == (len(points), 6) and np.isfinite(values).all(),
                        "invalid full six-component action array",
                    )
                    all_points = action_prepared(
                        physical_math, points, values, own["frame"], own["start"]
                    )
                    gravity = action_prepared(
                        physical_math,
                        points[gravity_mask],
                        values[gravity_mask],
                        own["frame"],
                        own["start"],
                    )
                    mechanical = action_prepared(
                        physical_math,
                        points[~gravity_mask],
                        values[~gravity_mask],
                        own["frame"],
                        own["start"],
                    )
                    for action_id, archived in zip(
                        np.array(member["point_action_ids"])[gravity_mask],
                        values[gravity_mask],
                        strict=True,
                    ):
                        node = action_id.removeprefix("body_load_node_")
                        expected = np.r_[
                            np.array(
                                adapter["physical_external_loads"].get(node, [0, 0, 0])
                            )
                            * factor,
                            [0, 0, 0],
                        ]
                        supported(
                            np.max(abs(archived - expected)) < TOL,
                            "archived discrete load differs from original owned selfweight/hardware",
                        )
                    error = own["full_gravity"] - gravity[1].sum(axis=0)
                    supported(
                        np.max(abs(error[:3])) < TOL and np.max(abs(error[3:])) < TOL,
                        "whole gravity force/moment changed",
                    )
                    prepared_cases[case] = (all_points, gravity, mechanical, error)
            except UnsupportedBody as exc:
                skipped.append(
                    {
                        "block": body,
                        "status": "AFFECTED_BODY_SCOPE_STOPPED",
                        "reason": str(exc),
                    }
                )
                continue
            body_records[body] = {
                k: own[k]
                for k in (
                    "certificate",
                    "source_density_kg_m3",
                    "retained_density_implied_by_source_mass_kg_m3",
                    "retained_volume_mm3",
                    "retained_centroid_xyz_mm",
                )
            }
            local_points = (points - own["start"]) @ own["frame"].T
            for case in CASES:
                all_points, gravity, mechanical, error = prepared_cases[case]
                whole_matches.append(
                    {
                        "block": body,
                        "case_id": case,
                        "physical_minus_mapped_gravity_n_nmm": error.tolist(),
                        "retained_whole_body_residual_n_nmm": (
                            mechanical[1].sum(axis=0) + own["full_gravity"]
                        ).tolist(),
                    }
                )
                refs = next(
                    m["conditional_material"]["CF_only_reference_mpa"]
                    for c in results["cases"]
                    if c["case_id"] == case
                    for m in c["members"]
                    if m["member"] == body
                )
                for axis in range(3):
                    state = {
                        "block": body,
                        "case_id": case,
                        "axis": axis,
                        "cut_count": 0,
                        "positive_normal_tensile_bound_count": 0,
                        "finite_pressure_count": 0,
                        "finite_pressure_above_reference_count": 0,
                        "no_finite_pressure_construction_count": 0,
                        "normal_peak": None,
                        "pressure_peak": None,
                        "grain_peaks": {},
                    }
                    for station in cut_events(
                        geom, local_points, own["hardware"], own["vertices"], axis
                    ):
                        volume, first = own["volume_function"](geom, axis, station)
                        first = np.asarray(first)
                        timber = np.r_[
                            volume * own["body_force"],
                            np.cross(
                                first - np.eye(3)[axis] * station * volume,
                                own["body_force"],
                            ),
                        ]
                        for limit in ("before", "after"):
                            gp = timber + physical_math.point_gravity(
                                own["hardware"], axis, station, limit
                            )
                            old_gravity = physical_math.point_gravity(
                                gravity, axis, station, limit
                            )
                            old_internal = -physical_math.point_gravity(
                                all_points, axis, station, limit
                            )
                            internal = (
                                -physical_math.point_gravity(
                                    mechanical, axis, station, limit
                                )
                                - gp
                            )
                            require(
                                np.max(
                                    abs(internal - (old_internal + old_gravity - gp))
                                )
                                < TOL,
                                "gravity replacement double-count or sign error",
                            )
                            perm = [axis, (axis + 1) % 3, (axis + 2) % 3]
                            q = np.r_[internal[:3][perm], internal[3:][perm]].tolist()
                            record = {
                                "block": body,
                                "case_id": case,
                                "axis": axis,
                                "station_mm": station,
                                "limit": limit,
                                "signed_internal_n_nmm": q,
                                "original_mapped_gravity_signed_internal_n_nmm": np.r_[
                                    old_internal[:3][perm], old_internal[3:][perm]
                                ].tolist(),
                                "mapped_gravity_negative_half_n_nmm": np.r_[
                                    old_gravity[:3][perm], old_gravity[3:][perm]
                                ].tolist(),
                                "physical_gravity_negative_half_n_nmm": np.r_[
                                    gp[:3][perm], gp[3:][perm]
                                ].tolist(),
                            }
                            witness = dict(record)
                            if axis == 0:
                                nominal = grain_nominal(
                                    q, geom, station, sections, net, header, refs
                                )
                                record["grain_nominal"] = nominal
                                for name, value in nominal["metrics"].items():
                                    for peaks in (state["grain_peaks"], grain_peaks):
                                        if (
                                            name not in peaks
                                            or value > peaks[name]["value"]
                                        ):
                                            peaks[name] = {**witness, "value": value}
                                grain_total += 1
                            else:
                                hull = [bounds3(geom)[i] for i in perm[1:]]
                                normal = normal_math.normal_bound(q, hull)
                                pressure = finite_pressure(
                                    q, geom, axis, station, normal_math
                                )
                                witness.update(
                                    normal_hull=normal, finite_pressure=pressure
                                )
                                record.update(
                                    normal_hull=normal, finite_pressure=pressure
                                )
                                t = normal["minimum_tensile_normal_resultant_n"]
                                state["positive_normal_tensile_bound_count"] += t > 0
                                for owner, name in ((state, "normal_peak"),):
                                    if (
                                        owner[name] is None
                                        or t
                                        > owner[name]["normal_hull"][
                                            "minimum_tensile_normal_resultant_n"
                                        ]
                                    ):
                                        owner[name] = witness
                                if (
                                    peak_t is None
                                    or t
                                    > peak_t["normal_hull"][
                                        "minimum_tensile_normal_resultant_n"
                                    ]
                                ):
                                    peak_t = witness
                                if "pressure_peak_mpa" in pressure:
                                    state["finite_pressure_count"] += 1
                                    p = pressure["pressure_peak_mpa"]
                                    state["finite_pressure_above_reference_count"] += (
                                        p > pressure_ref
                                    )
                                    if (
                                        state["pressure_peak"] is None
                                        or p
                                        > state["pressure_peak"]["finite_pressure"][
                                            "pressure_peak_mpa"
                                        ]
                                    ):
                                        state["pressure_peak"] = witness
                                    if (
                                        peak_pressure is None
                                        or p
                                        > peak_pressure["finite_pressure"][
                                            "pressure_peak_mpa"
                                        ]
                                    ):
                                        peak_pressure = witness
                                elif t == 0:
                                    state["no_finite_pressure_construction_count"] += 1
                                transverse_total += 1
                            stream.write(json.dumps(record, allow_nan=False) + "\n")
                            total += 1
                            state["cut_count"] += 1
                    states.append(state)
    authenticate(pins)
    require(sha(Path(__file__)) == digest, "producer changed during calculation")
    require(
        len(states) == len(body_records) * 6 * 3,
        "incomplete evaluated body/case/orientation coverage",
    )
    result = {
        "schema": "remaining_block_transverse/v1",
        "status": "FINITE_REMAINING_BLOCK_ASSESSMENT_COMPLETE"
        if not skipped
        else "FINITE_ASSESSMENT_WITH_AFFECTED_BODY_SCOPE_STOPS",
        "registered_target_count": 20,
        "evaluated_body_count": len(body_records),
        "evaluated_body_case_orientation_count": len(states),
        "cut_count": total,
        "grain_cut_count": grain_total,
        "transverse_cut_count": transverse_total,
        "case_ids": list(CASES),
        "source_gravity_multiplier": factor,
        "source_force_state_scope": results["source_force_state_scope"],
        "grain_nominal_hypotheses": net.ASSUMPTIONS,
        "conditional_CF_only_reference_mpa_by_body": {
            m["member"]: m["conditional_material"]["CF_only_reference_mpa"]
            for m in results["cases"][0]["members"]
            if m["member"] in geometries
        },
        "body_records": body_records,
        "affected_scope_stops": skipped,
        "whole_gravity_matches": whole_matches,
        "known_answers": known,
        "states": states,
        "maximum_necessary_normal_tensile_resultant_witness": peak_t,
        "maximum_finite_pressure_witness": peak_pressure,
        "grain_nominal_peak_witnesses": grain_peaks,
        "existing_Fc_perpendicular_reference_mpa": pressure_ref,
        "source_sha256": {key(p): d for p, d in sorted(pins.items())},
        "executed_producer_sha256": digest,
        "limits": [
            "Mechanical actions remain the authenticated source point-force/free-couple idealization; no physical bore-wall pressure, washer-seat pressure, or spatial contact redistribution is transferred from corner calculations.",
            "Exact retained-timber gravity and original allocated hardware point forces/free couples replace owned mapped gravity once; same-state loads and complete whole-gravity wrench remain fixed.",
            "Each transverse rectangle hull is the actual retained section convex hull because source-certified disjoint cylinders miss all bounding corners; normal tension is a resultant lower bound with unbounded pressure, not an actual tie allocation or capacity.",
            "Finite compression uses rectangles individually checked outside actual cylinder voids; it is a sufficient normal equilibrium construction, not a compatible physical pressure field or an optimum.",
            "All simultaneous signed shears and torque remain in each cut; no transverse shear/torque, rolling shear, fracture, washer anchorage, or splitting capacity is supplied.",
            "Grain comparisons reuse original conditional references and nominal regional hypotheses; longitudinal-hole bodies retain their original artificial rectangle subsets, not a true local-stress bound.",
            "Only listed source point/geometry/patch boundary events and interval midpoints are evaluated; no continuous maxima or fabrication geometry is certified.",
        ],
        "splitting_capacity_n": None,
        "complete_joint_acceptance": False,
        "formal_criterion_acceptance": False,
        "fabrication_release": False,
        "physical_release": False,
    }
    dump(output / "checks.json", result)
    dump(
        output / "receipt.json",
        {
            "source_sha256": result["source_sha256"],
            "output_sha256": {p.name: sha(p) for p in output.iterdir()},
        },
    )
    return {
        "status": result["status"],
        "checks_sha256": sha(output / "checks.json"),
        "evaluated_body_count": len(body_records),
        "affected_scope_stops": skipped,
        "cut_count": total,
        "maximum_necessary_normal_tensile_resultant_witness": peak_t,
        "grain_nominal_peak_witnesses": grain_peaks,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), allow_nan=False))
