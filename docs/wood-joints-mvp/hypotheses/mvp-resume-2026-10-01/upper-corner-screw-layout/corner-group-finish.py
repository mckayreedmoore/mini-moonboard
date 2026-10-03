"""Finite signed corner-group assessment using the saved first-order loads.

Parent executes one static postprocessor and analytical coupon. This imports
no mechanics entry point and assigns no perpendicular-tension resistance.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import sys
from itertools import combinations, pairwise
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/corner-group-finish"
TOP = HERE / "rawlocal/corner-first-order/attempt01/checks.json"
BOTTOM = HERE / "rawlocal/bottom-corner-transfer/first-order-attempt01/checks.json"
TIMBER = HERE / "rawlocal/corner-timber-sections/attempt02/checks.json"
TOP_PATHS = HERE / "bolted-replay-results/corner-attempt01/component-results.json"
BOTTOM_PATHS = HERE / "bolted-replay-results/bottom-attempt01/component-results.json"
MEMBERS = (
    HERE.parent / "member-screen-attempt02/four-screw-layout01/member-results.json"
)
TOL = 1e-6
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PINS = {
    TOP: "b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe",
    BOTTOM: "4d255ba5ebd8f1f93fb41ef90511eb3da49906f4729f33f5f63766e0a0bd78ed",
    TIMBER: "8b954edf5743999f427d2b99fcaaf9288578f02dc59a5cf1e632da634aa2e813",
    TOP_PATHS: "401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6",
    BOTTOM_PATHS: "ec421ee35b9477842660faa6d2528bd957f8a06620f7d84c46d9654e40ce146a",
    MEMBERS: "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    HERE
    / "corner-bore-wall.py": "0ad9c88be2496f1b2ae9b06cb31f0cb7d9d95a236ffb4b2dc586873b7cf4a185",
    HERE
    / "corner-timber-sections.py": "d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633",
    HERE
    / "corner-net-section.py": "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    HERE
    / "cleat-traction.py": "2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764",
}


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


def authenticate(pins):
    for path, expected in pins.items():
        require(sha(path) == expected, f"changed frozen source: {path}")


def module(filename):
    path = HERE / filename
    spec = importlib.util.spec_from_file_location(filename.replace("-", "_")[:-3], path)
    require(spec is not None and spec.loader is not None, "unavailable frozen helper")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def rect_integrals(bounds):
    (a, b), (c, d) = bounds
    area = (b - a) * (d - c)
    center = np.array([(a + b) / 2, (c + d) / 2])
    central = area * np.diag([(b - a) ** 2 / 12, (d - c) ** 2 / 12])
    return integrals(area, center, central)


def integrals(area, center, central):
    first = area * center
    second = central + area * np.outer(center, center)
    return np.array([[area, *first], [first[0], *second[0]], [first[1], *second[1]]])


def circle_integrals(center, radius):
    area = math.pi * radius**2
    return integrals(area, np.array(center), np.eye(2) * area * radius**2 / 4)


def normal_field(q, matrix, bounds):
    """One explicit affine normal-traction hypothesis on the true net area."""
    coefficients = np.linalg.solve(matrix, [q[0], -q[5], q[4]])
    recovered = matrix @ coefficients
    require(
        np.max(abs(recovered - [q[0], -q[5], q[4]])) < 1e-7, "normal integral closure"
    )
    corners = [
        {"p_mm": p, "q_mm": r, "normal_stress_mpa": float(coefficients @ [1, p, r])}
        for p in bounds[0]
        for r in bounds[1]
    ]
    return {
        "affine_normal_a_b_c": coefficients.tolist(),
        "corners": corners,
        "minimum_normal_mpa": min(row["normal_stress_mpa"] for row in corners),
        "maximum_normal_mpa": max(row["normal_stress_mpa"] for row in corners),
        "net_area_mm2": matrix[0, 0],
        "normal_integral_error": float(np.max(abs(recovered - [q[0], -q[5], q[4]]))),
    }


def cut_material(geom, axis, station):
    """Exact plane rectangle minus disjoint full circles or through strips."""
    bounds3 = [
        [0, geom["grain_length_mm"]],
        *[[-v / 2, v / 2] for v in geom["width_depth_mm"]],
    ]
    perm = [axis, (axis + 1) % 3, (axis + 2) % 3]
    bounds = [bounds3[j] for j in perm[1:]]
    matrix = rect_integrals(bounds)
    voids = []
    for bore in geom["bores"]:
        shaft = 3 - bore["removed_interval_axis"]
        center = np.zeros(3)
        center[0] = bore["station_mm"]
        center[bore["removed_interval_axis"]] = bore["transverse_center_mm"]
        radius = bore["radius_mm"]
        if axis == shaft:
            own = circle_integrals(center[perm[1:]], radius)
            voids.append(
                {
                    "axis_id": bore["axis_id"],
                    "kind": "circle",
                    "radius_mm": radius,
                    "center_pq_mm": center[perm[1:]].tolist(),
                }
            )
        else:
            distance = abs(station - center[axis])
            if distance >= radius:
                continue
            half = math.sqrt(radius**2 - distance**2)
            other = next(j for j in range(3) if j not in (axis, shaft))
            strip = [list(v) for v in bounds]
            index = perm[1:].index(other)
            strip[index] = [center[other] - half, center[other] + half]
            require(
                strip[index][0] >= bounds[index][0] - TOL
                and strip[index][1] <= bounds[index][1] + TOL,
                "bore strip leaves rectangular blank",
            )
            own = rect_integrals(strip)
            voids.append(
                {
                    "axis_id": bore["axis_id"],
                    "kind": "through_strip",
                    "bounds_pq_mm": strip,
                }
            )
        matrix -= own
    require(matrix[0, 0] > 0 and np.linalg.det(matrix) > 0, "singular finished section")
    return perm, bounds, matrix, voids


def geometry_certificate(geom):
    """Check the disjoint full-cylinder premise of the plane integrals."""
    rows = np.array(geom["grain_frame_rows_xyz"])
    require(
        np.allclose(rows @ rows.T, np.eye(3), atol=1e-8)
        and abs(np.linalg.det(rows) - 1) < 1e-8,
        "invalid right-handed grain frame",
    )
    require(
        len(geom["bores"]) == len({b["axis_id"] for b in geom["bores"]}) == 4,
        "four distinct bores required",
    )
    half = np.array(geom["width_depth_mm"]) / 2
    margins = []
    for bore in geom["bores"]:
        s, r, j = bore["station_mm"], bore["radius_mm"], bore["removed_interval_axis"]
        require(j in (1, 2) and r > 0, "nontransverse or nonpositive bore")
        margins.extend(
            [
                s - r,
                geom["grain_length_mm"] - s - r,
                half[j - 1] - abs(bore["transverse_center_mm"]) - r,
            ]
        )
    pairs = []
    for a, b in combinations(geom["bores"], 2):
        ds = a["station_mm"] - b["station_mm"]
        distance = (
            math.hypot(ds, a["transverse_center_mm"] - b["transverse_center_mm"])
            if a["removed_interval_axis"] == b["removed_interval_axis"]
            else abs(ds)
        )
        clearance = distance - a["radius_mm"] - b["radius_mm"]
        pairs.append(
            {
                "axis_ids": [a["axis_id"], b["axis_id"]],
                "cylinder_clearance_mm": clearance,
            }
        )
    require(
        min(margins) > 0 and min(p["cylinder_clearance_mm"] for p in pairs) > 0,
        "cylinders intersect each other or a stock edge",
    )
    return {
        "minimum_radial_stock_margin_mm": min(margins),
        "pairs": pairs,
        "disjoint_full_cylinders": True,
    }


def bottom_geometry(state, prepared):
    group = next(g for g in prepared["groups"] if g["side"] == state["side"])
    record = group["finished_members"][state["cleat"]]
    g = record["geometry"]
    rows = np.array([g[k] for k in ("axis", "section_u", "section_v")])
    start = np.array(g["start"])
    require(
        np.allclose(rows @ rows.T, np.eye(3), atol=1e-8), "bottom grain frame differs"
    )
    length = float(rows[0] @ (np.array(g["end"]) - start))
    dimensions = [g["width_mm"], g["depth_mm"]]
    bores = []
    for own in (r for r in prepared["groups"] if r["side"] == state["side"]):
        direction = rows @ np.array(own["n"])
        shaft = int(np.argmax(abs(direction)))
        require(
            shaft in (1, 2) and abs(abs(direction[shaft]) - 1) < 1e-8,
            "bottom nontransverse shaft",
        )
        for bolt in own["bolts"]:
            center = rows @ (np.array(bolt["interface_point_xyz_mm"]) - start)
            other = 3 - shaft
            bores.append(
                {
                    "axis_id": bolt["axis_id"],
                    "station_mm": float(center[0]),
                    "transverse_center_mm": float(center[other]),
                    "removed_interval_axis": other,
                    "radius_mm": own["family"]["bore_mm"] / 2,
                }
            )
    volume = math.prod(dimensions) * length - sum(
        math.pi * b["radius_mm"] ** 2 * dimensions[2 - b["removed_interval_axis"]]
        for b in bores
    )
    require(
        len(bores) == 4
        and abs(volume - g["geometry_diagnostics"]["actual_step_volume_mm3"]) < 0.001,
        "bottom saved finished volume differs",
    )
    return {
        "block": state["cleat"],
        "start_xyz_mm": start.tolist(),
        "grain_frame_rows_xyz": rows.tolist(),
        "grain_length_mm": length,
        "width_depth_mm": dimensions,
        "bores": bores,
        "analytic_finished_volume_mm3": volume,
    }


def pressure_profiles(state, geom, wall, prepared=None):
    rows, start = np.array(geom["grain_frame_rows_xyz"]), np.array(geom["start_xyz_mm"])
    output = []
    actions = [
        a
        for a in state["physical_cleat_actions"]
        if a["kind"] == "bore_station_resultant"
    ]
    for host_id, host in state["hosts"].items():
        for bolt in host["state"]["bolts"]:
            identity = bolt["axis_id"]
            bore = next(b for b in geom["bores"] if b["axis_id"] == identity)
            n = np.array(
                bolt["bolt_axis_head_to_nut_xyz"]
                if prepared is None
                else next(
                    g["n"]
                    for g in prepared["groups"]
                    if g["side"] == state["side"] and g["host"] == host_id
                )
            )
            own = [a for a in actions if a["identity"] == identity]
            fields = [f for f in bolt["bore_fields"] if f["receiver"] == "cleat"]
            require(len(own) == len(fields) == 24, "bore field census differs")
            for action, field in zip(own, fields, strict=True):
                point, force = (
                    np.array(action["point_xyz_mm"]),
                    np.array(action["force_xyz_n"]),
                )
                require(
                    np.max(abs(force + np.array(field["force_on_beam_xyz_n"]))) < 1e-8,
                    "bore force differs",
                )
                support = wall.wall_support(point, n, bore["radius_mm"], geom, identity)
                require(
                    support["whole_circumference_support_certified"],
                    "unsupported finished bore wall",
                )
                profile = wall.pressure_profile(
                    rows @ (point - start),
                    rows @ force,
                    rows @ n,
                    bore["radius_mm"],
                    field["quadrature_weight_mm"],
                    identity=identity,
                )
                output.append(profile)
    return output


def weight_actions(state, geom, model, labels, array_f, factor):
    case = CASES.index(state["case_id"])
    nodes = sorted(set(model["body_nodes"][geom["block"]]))
    values = {node: np.zeros(3) for node in nodes}
    for index, (node, direction) in enumerate(labels):
        if node in values:
            values[node][direction - 1] = (
                factor * array_f[index, 2 * case] + array_f[index, 2 * case + 1]
            )
    return [
        {
            "kind": "original_current_mapped_W_node",
            "identity": str(node),
            "point_xyz_mm": model["physical_node_coordinates_mm"][str(node)],
            "force_xyz_n": values[node].tolist(),
        }
        for node in nodes
    ]


def partial_wall(profile, axis, station, limit, wall):
    point = np.array(profile["axis_point_xyz_mm"])
    e, h = np.array(profile["pressure_basis_e_h_xyz"])
    radius = profile["radius_mm"]
    angles = sorted(
        [
            -math.pi / 2,
            math.pi / 2,
            *wall.coordinate_roots(
                radius * e[axis], radius * h[axis], station - point[axis]
            ),
        ]
    )
    datum = np.zeros(3)
    datum[axis] = station
    answer = np.zeros(6)
    for a, b in pairwise(angles):
        theta = (a + b) / 2
        distance = (
            point[axis]
            + radius * (e[axis] * math.cos(theta) + h[axis] * math.sin(theta))
            - station
        )
        if distance < -1e-10 or (limit == "after" and abs(distance) <= 1e-10):
            answer += wall.pressure_arc_wrench(profile, datum, a, b)
    return answer


def signed_channels(profiles, wall):
    channels = {}
    for profile in profiles:
        e, h = np.array(profile["pressure_basis_e_h_xyz"])
        angles = sorted(
            [-math.pi / 2, math.pi / 2, *wall.coordinate_roots(e[0], h[0], 0)]
        )
        own = channels.setdefault(
            profile["axis_id"],
            {
                "positive_n": 0.0,
                "negative_n": 0.0,
                "complete_wrench_n_nmm": np.zeros(6),
            },
        )
        for a, b in pairwise(angles):
            q = wall.pressure_arc_wrench(profile, np.zeros(3), a, b)
            own["positive_n"] += max(q[0], 0)
            own["negative_n"] += max(-q[0], 0)
            own["complete_wrench_n_nmm"] += q
    return channels


def parallel_paths(geom, channels, paths, fv):
    output = []
    for axis_id, channel in channels.items():
        for sign, key in ((1, "positive_n"), (-1, "negative_n")):
            path = next(
                p
                for p in paths
                if p["axis_id"] == axis_id and p["grain_direction_sign"] == sign
            )
            reference = fv * path["minimum_finished_one_plane_area_mm2"]
            output.append(
                {
                    "axis_id": axis_id,
                    "grain_direction_sign": sign,
                    "distributed_parallel_channel_bound_n": channel[key],
                    "finished_one_plane_area_mm2": path[
                        "minimum_finished_one_plane_area_mm2"
                    ],
                    "single_fastener_E3_reference_n": reference,
                    "channel_over_reference": channel[key] / reference,
                    "complete_signed_bore_wrench_at_start_n_nmm": channel[
                        "complete_wrench_n_nmm"
                    ].tolist(),
                }
            )
    rails = [b for b in geom["bores"] if "/rail_" in b["axis_id"]]
    require(
        len(rails) == 2
        and rails[0]["removed_interval_axis"] == rails[1]["removed_interval_axis"]
        and abs(rails[0]["transverse_center_mm"] - rails[1]["transverse_center_mm"])
        < TOL,
        "rail pair is not a grain row",
    )
    rows = []
    for sign, key in ((1, "positive_n"), (-1, "negative_n")):
        own = [
            p
            for p in paths
            if p["axis_id"] in {r["axis_id"] for r in rails}
            and p["grain_direction_sign"] == sign
        ]
        require(len(own) == 2, "rail row path census differs")
        area = min(p["minimum_finished_one_plane_area_mm2"] for p in own)
        reference = 2 * fv * area
        demand = sum(channels[r["axis_id"]][key] for r in rails)
        rows.append(
            {
                "grain_direction_sign": sign,
                "fastener_count": 2,
                "minimum_finished_one_plane_area_mm2": area,
                "parallel_channel_bound_n": demand,
                "E3_row_reference_n": reference,
                "parallel_channel_over_E3_row_reference": demand / reference,
            }
        )
    return {
        "single_channels": output,
        "rail_row_channels": rows,
        "all_four_positive_parallel_bound_n": sum(
            c["positive_n"] for c in channels.values()
        ),
        "all_four_negative_parallel_bound_n": sum(
            c["negative_n"] for c in channels.values()
        ),
        "complete_crossed_group_capacity_n": None,
        "scope": "E.3 longitudinal channels only. Side bolts are separate rows. No four-bolt row, E.4 crossed-group resistance, eccentric/oblique interaction or crack capacity is inferred.",
    }


def coupon(net, wall):
    refs = {
        "Ft_parallel": 5.15383107664335,
        "Fc_parallel": 10.238714580355017,
        "Fb": 8.066866033006981,
        "Fv_parallel": 1.241056312770305,
    }
    rectangle = net.rectangular_known_answer(refs)
    bounds = [[2, 6], [-4, 2]]
    matrix = rect_integrals(bounds) - circle_integrals([4, -1], 1)
    n = 4.25 * (24 - math.pi)
    q = np.array(
        [
            n,
            12,
            -6,
            30,
            -n - 0.25 * (72 - math.pi / 4),
            -4 * n - 0.5 * (32 - math.pi / 4),
        ]
    )
    field = normal_field(q, matrix, bounds)
    require(
        np.allclose(field["affine_normal_a_b_c"], [2, 0.5, -0.25], atol=1e-12),
        "circle-void affine coupon",
    )
    require(
        abs(field["minimum_normal_mpa"] - 2.5) < 1e-12
        and abs(field["maximum_normal_mpa"] - 6) < 1e-12,
        "circle-void corner coupon",
    )
    pressure = wall.algebraic_coupon()
    profile = wall.pressure_profile([3, 4, 5], [10, 0, 0], [0, 0, 1], 2, 5)
    half = partial_wall(profile, 1, 4, "after", wall)
    require(
        np.max(abs(half[:3] - [5, -10 / math.pi, 0])) < 1e-12,
        "negative angular half-force coupon",
    )
    return {
        "translated_rectangle": rectangle,
        "rectangle_minus_circle": {"signed_q_n_nmm": q.tolist(), **field},
        "pressure": pressure,
        "negative_y_half_force_n": half[:3].tolist(),
        "coupon_satisfied": True,
    }


def build(output):
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW) and output != RAW and not output.exists(),
        "fresh owned output child required",
    )
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__).resolve())}
    authenticate(pins)
    top, bottom, timber, top_paths, bottom_paths, members = map(
        read, (TOP, BOTTOM, TIMBER, TOP_PATHS, BOTTOM_PATHS, MEMBERS)
    )
    for source in (top, bottom):
        require(
            source["failure"] is None and len(source["states"]) == 12,
            "incomplete first-order source",
        )
        require(
            not source["frame_response_changed"]
            and not source["geometric_shortening_and_preload_stiffness"],
            "changed working assumptions",
        )
    for source in (top, bottom, timber):
        for name, digest in source["source_sha256"].items():
            path = ROOT / name
            require(path not in pins or pins[path] == digest, "conflicting source pin")
            pins[path] = digest
    wall, sections, net, traction = (
        module(name)
        for name in (
            "corner-bore-wall.py",
            "corner-timber-sections.py",
            "corner-net-section.py",
            "cleat-traction.py",
        )
    )
    for path in (traction.DOF, traction.PARSER, net.TORSION_SOURCE):
        expected = traction.PINS[path] if path in traction.PINS else net.PINS[path]
        require(path not in pins or pins[path] == expected, "conflicting helper pin")
        pins[path] = expected
    authenticate(pins)
    parser_spec = importlib.util.spec_from_file_location(
        "corner_group_dof_labels", traction.PARSER
    )
    parser = importlib.util.module_from_spec(parser_spec)
    parser_spec.loader.exec_module(parser)
    labels = parser.parse_dof_file(traction.DOF)
    model, comparison = read(traction.MODEL), read(traction.COMPARISON)
    known = coupon(net, wall)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    records, geometries, peaks = [], {}, {}
    count, transverse_count, opening_count, max_balance = 0, 0, 0, np.zeros(6)
    geometry_certificates, parallel_peaks = {}, {}
    with (
        np.load(traction.OPERATORS, allow_pickle=False) as arrays,
        gzip.open(output / "cuts.jsonl.gz", "wt") as stream,
    ):
        for level, source, paths in (
            ("top", top, top_paths),
            ("bottom", bottom, bottom_paths),
        ):
            for state in source["states"]:
                require(state["case_id"] in CASES, "unknown force case")
                geom = (
                    timber["geometry"][state["side"]]
                    if level == "top"
                    else bottom_geometry(state, bottom["preparation"])
                )
                geometries[geom["block"]] = geom
                geometry_certificates[geom["block"]] = geometry_certificate(geom)
                rows, start = (
                    np.array(geom["grain_frame_rows_xyz"]),
                    np.array(geom["start_xyz_mm"]),
                )
                own_weights = (
                    weight_actions(
                        state,
                        geom,
                        model,
                        labels,
                        arrays["F"],
                        comparison["dead_load_factor"],
                    )
                    if level == "top"
                    else state["own_weight_actions_once"]
                )
                actions = [*state["physical_cleat_actions"], *own_weights]
                points = np.array([a["point_xyz_mm"] for a in actions])
                forces = np.array([a["force_xyz_n"] for a in actions])
                local_points, local_forces = (points - start) @ rows.T, forces @ rows.T
                datum = np.array(state["common_datum_xyz_mm"])
                weight_q = np.r_[
                    np.sum([a["force_xyz_n"] for a in own_weights], axis=0),
                    np.sum(
                        [
                            np.cross(
                                np.array(a["point_xyz_mm"]) - datum, a["force_xyz_n"]
                            )
                            for a in own_weights
                        ],
                        axis=0,
                    ),
                ]
                require(
                    np.max(abs(weight_q - state["current_weight_once_n_nmm"])) < 1e-7,
                    "mapped W not counted exactly once",
                )
                full = np.r_[
                    local_forces.sum(axis=0),
                    np.cross(local_points, local_forces).sum(axis=0),
                ]
                expected = state["physical_whole_cleat_residual_n_nmm"]
                actual = np.r_[
                    rows.T @ full[:3],
                    rows.T @ (full[3:] - np.cross(rows @ (datum - start), full[:3])),
                ]
                require(
                    np.max(abs(actual - expected)) < 1e-7,
                    "whole-cleat physical residual changed",
                )
                profiles = pressure_profiles(
                    state, geom, wall, None if level == "top" else bottom["preparation"]
                )
                mask = np.array(
                    [a["kind"] != "bore_station_resultant" for a in actions]
                )
                bore_q = np.r_[
                    local_forces[~mask].sum(axis=0),
                    np.cross(local_points[~mask], local_forces[~mask]).sum(axis=0),
                ]
                mapped_bore_q = sum(
                    (wall.pressure_arc_wrench(p, np.zeros(3)) for p in profiles),
                    np.zeros(6),
                )
                require(
                    np.max(abs(mapped_bore_q - bore_q)) < 1e-7,
                    "distributed bore force/moment changed",
                )
                point_q = np.c_[
                    local_forces[mask], np.cross(local_points[mask], local_forces[mask])
                ]
                point_p = local_points[mask]
                refs = (
                    timber["conditional_CF_only_reference_mpa"]
                    if level == "top"
                    else next(
                        m["conditional_material"]["CF_only_reference_mpa"]
                        for m in members["cases"][0]["members"]
                        if m["member"] == geom["block"]
                    )
                )
                channels = parallel_paths(
                    geom,
                    signed_channels(profiles, wall),
                    paths["finished_paths"],
                    refs["Fv_parallel"],
                )
                for name, entries, key in (
                    (
                        "single_longitudinal_channel_over_E3_reference",
                        channels["single_channels"],
                        "channel_over_reference",
                    ),
                    (
                        "two_bolt_rail_row_longitudinal_channel_over_E3_reference",
                        channels["rail_row_channels"],
                        "parallel_channel_over_E3_row_reference",
                    ),
                ):
                    entry = max(entries, key=lambda row: row[key])
                    witness = {
                        "value": entry[key],
                        "block": geom["block"],
                        "case_id": state["case_id"],
                        **entry,
                    }
                    if (
                        name not in parallel_peaks
                        or witness["value"] > parallel_peaks[name]["value"]
                    ):
                        parallel_peaks[name] = witness
                state_peaks = {}
                bounds3 = [
                    [0, geom["grain_length_mm"]],
                    *[[-v / 2, v / 2] for v in geom["width_depth_mm"]],
                ]
                for axis in range(3):
                    events = list(point_p[:, axis])
                    for profile in profiles:
                        p = profile["axis_point_xyz_mm"][axis]
                        reach = profile["radius_mm"] * math.sqrt(
                            max(0, 1 - profile["axis_unit_xyz"][axis] ** 2)
                        )
                        events.extend([p - reach, p, p + reach])
                    for bore in geom["bores"]:
                        center = (
                            bore["station_mm"]
                            if axis == 0
                            else bore["transverse_center_mm"]
                            if axis == bore["removed_interval_axis"]
                            else 0
                        )
                        events.extend(
                            [
                                center - bore["radius_mm"],
                                center,
                                center + bore["radius_mm"],
                            ]
                        )
                    low, high = bounds3[axis]
                    events = sorted(v for v in events if low + TOL < v < high - TOL)
                    stations = []
                    for value in events:
                        if not stations or value - stations[-1] > TOL:
                            stations.append(float(value))
                    stations.extend([(low + high) / 2, low + 1e-4, high - 1e-4])
                    for station in sorted(set(stations)):
                        perm, bounds, matrix, voids = cut_material(geom, axis, station)
                        for limit in ("before", "after"):
                            included = (
                                point_p[:, axis] < station - TOL
                                if limit == "before"
                                else point_p[:, axis] <= station + TOL
                            )
                            negative = point_q[included].sum(axis=0)
                            negative[3:] -= np.cross(
                                np.eye(3)[axis] * station, negative[:3]
                            )
                            for profile in profiles:
                                negative += partial_wall(
                                    profile, axis, station, limit, wall
                                )
                            internal = -negative
                            opposite = full.copy()
                            opposite[3:] -= np.cross(
                                np.eye(3)[axis] * station, opposite[:3]
                            )
                            opposite -= negative
                            error = internal - opposite
                            max_balance = np.maximum(max_balance, abs(error))
                            q = np.r_[internal[:3][perm], internal[3:][perm]]
                            normal = normal_field(q, matrix, bounds)
                            record = {
                                "block": geom["block"],
                                "case_id": state["case_id"],
                                "normal_axis_grain_u_v": axis,
                                "station_mm": station,
                                "limit": limit,
                                "signed_internal_n_nmm": q.tolist(),
                                "opposite_half_disagreement_n_nmm": np.r_[
                                    error[:3][perm], error[3:][perm]
                                ].tolist(),
                                "finished_voids": voids,
                                "normal_field": normal,
                            }
                            metrics = (
                                {
                                    "perpendicular_opening_normal_mpa": max(
                                        normal["maximum_normal_mpa"], 0
                                    )
                                }
                                if axis
                                else {}
                            )
                            if axis == 0:
                                own = sections.section(geom, station)
                                nominal = net.nominal_section(q, own["regions"], refs)
                                require(
                                    abs(
                                        nominal["net_section_integrals"]["area_mm2"]
                                        - normal["net_area_mm2"]
                                    )
                                    < 1e-5,
                                    "grain-section area differs",
                                )
                                metrics.update(
                                    {
                                        "grain_tension_over_Ft": max(
                                            c["comparisons"]["total_tension_over_Ft"]
                                            for r in nominal["regions"]
                                            for c in r["longitudinal_corners"]
                                        ),
                                        "grain_compression_over_Fc": max(
                                            c["comparisons"]["total_compression_over_Fc"]
                                            for r in nominal["regions"]
                                            for c in r["longitudinal_corners"]
                                        ),
                                        "grain_bending_over_Fb": max(
                                            c["comparisons"]["absolute_bending_over_Fb"]
                                            for r in nominal["regions"]
                                            for c in r["longitudinal_corners"]
                                        ),
                                        "grain_regional_shear_torsion_over_Fv": max(
                                            r["same_state_shear_bound_over_Fv"]
                                            for r in nominal["regions"]
                                        ),
                                    }
                                )
                                record["nominal_grain_regions"] = nominal["regions"]
                            else:
                                record["affine_compression_only_normal_route"] = (
                                    normal["maximum_normal_mpa"] <= 1e-10
                                )
                                transverse_count += 1
                                opening_count += not record[
                                    "affine_compression_only_normal_route"
                                ]
                                record["perpendicular_tension_capacity_mpa"] = None
                                record["transverse_shear_torsion_capacity"] = None
                            record["metrics"] = metrics
                            for name, value in metrics.items():
                                witness = {
                                    "value": value,
                                    "block": geom["block"],
                                    "case_id": state["case_id"],
                                    "axis": axis,
                                    "station_mm": station,
                                    "limit": limit,
                                    "signed_cut_n_nmm": q.tolist(),
                                }
                                if (
                                    name not in state_peaks
                                    or value > state_peaks[name]["value"]
                                ):
                                    state_peaks[name] = witness
                                if name not in peaks or value > peaks[name]["value"]:
                                    peaks[name] = witness
                            stream.write(json.dumps(record, allow_nan=False) + "\n")
                            count += 1
                records.append(
                    {
                        "block": geom["block"],
                        "case_id": state["case_id"],
                        "side": state["side"],
                        "parallel_channels": channels,
                        "whole_cleat_residual_n_nmm": actual.tolist(),
                        "same_state_peak_witnesses": state_peaks,
                    }
                )
    authenticate(pins)
    result = {
        "schema": "corner_group_static_finish/v1",
        "status": "COMPLETE_CONDITIONAL_STATIC_ASSESSMENT",
        "case_ids": CASES,
        "block_count": len(geometries),
        "state_count": len(records),
        "finite_cut_limit_count": count,
        "geometries": geometries,
        "coupon": known,
        "states": records,
        "peak_witnesses": peaks,
        "geometry_certificates": geometry_certificates,
        "parallel_peak_witnesses": parallel_peaks,
        "transverse_cut_limit_count": transverse_count,
        "transverse_cut_limits_with_nominal_opening": opening_count,
        "all_computed_longitudinal_reference_ratios_below_one": all(
            p["value"] < 1
            for p in [
                *parallel_peaks.values(),
                *[v for k, v in peaks.items() if k.startswith("grain_")],
            ]
        ),
        "maximum_opposite_half_balance_error_n_nmm": max_balance.tolist(),
        "working_disposition": "Finite signed static demand and applicable longitudinal-channel comparisons complete. Local cracking remains an explicit unqualified working assumption; no complete crossed-group resistance is assigned.",
        "limits": [
            "The affine normal field and grain regional shear/torsion sharing are explicit nominal hypotheses, not a recovered 3D elastic stress field.",
            "Cuts cover finite recorded action/bore events and selected bridge stations, not a proved continuous-station maximum or every crack surface.",
            "Perpendicular normal opening is a nominal demand diagnostic with capacity null; a compression-only normal route alone does not establish shear transfer or fracture resistance.",
            "NDS Appendix E.3 applies here to separate longitudinal channels only; E.4 does not supply a combined crossed-group resistance.",
            "EC5 beam F90 topology is not established for the complete crossed-group block; no characteristic/design conversion is adopted.",
            "Existing inward washer actions are counted once. No bolt reinforcement, preload, friction, extra tension or new hardware capacity is credited.",
            "The current K20/first-order/smooth-shank source and all full signed couples are preserved; no new local mechanics, native, frame, CAD or geometry run occurs.",
        ],
        "source_sha256": {
            str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): v
            for p, v in sorted(pins.items())
        },
        "Ft_perpendicular_mpa": None,
        "complete_crossed_group_capacity_n": None,
        "conditional_static_assessment_complete": True,
        "complete_joint_acceptance": False,
        "formal_criterion_acceptance": False,
        "physical_release": False,
        "fabrication_release": False,
    }
    require(
        len(geometries) == 4 and len(records) == 24,
        "four-corner six-case census incomplete",
    )
    dump(output / "checks.json", result)
    outputs = {p.name: sha(p) for p in output.iterdir()}
    dump(
        output / "receipt.json",
        {"source_sha256": result["source_sha256"], "output_sha256": outputs},
    )
    return {
        "status": result["status"],
        "cut_count": count,
        "peaks": peaks,
        "checks_sha256": outputs["checks.json"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), allow_nan=False))
