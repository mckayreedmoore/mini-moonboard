#!/usr/bin/env python3
"""Independent source-level replay of bottom outer section resultants.

This verifier reads frozen inputs and a producer replay, but imports neither
the producer nor its host-action or CAD extraction helpers. It rebuilds action
ownership, point forces, rounding intervals, half-body cuts, and wrench
transports from the raw case records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DEFAULT_REPORT = Path(
    "/tmp/mini-moonboard-bottom-outer-finished-sections-2026-10-01.json"
)
FEATURES = Path(
    "docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/axis-features.json"
)
FREEZE = Path(
    "docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/freeze.json"
)
CONTACT = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json"
)
PRODUCER = HERE / "produce.py"
HOST_METHOD = Path(
    "docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01/host_actions.py"
)
SECTION_METHOD = Path(
    "docs/wood-joints-mvp/hypotheses/upper-outer-finished-sections-2026-10-01/section_geometry.py"
)

# Exact files reviewed for this replay. A changed source requires a new review.
PINNED = {
    "producer": (
        PRODUCER,
        "662404918c93bb9d96fa48b0b9f02237aaf260b8db1c510dfe866334017e4da7",
    ),
    "axis_features": (
        FEATURES,
        "bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19",
    ),
    "three_case_freeze": (
        FREEZE,
        "d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73",
    ),
    "source_contact_geometry": (
        CONTACT,
        "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    ),
    "point_action_method": (
        HOST_METHOD,
        "39b3af2bdd468d20db868454cb81cce1ad2d3af30059c4204aa2284892cd390b",
    ),
    "finished_section_method": (
        SECTION_METHOD,
        "8672daac3cef4aa55641a3e1bf6cee636d779be48145858282ffb0ed4d76f8d3",
    ),
}

CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
CASES = ("a1-rear", "a12-rear", "k12-rear")
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
MEMBERS = (
    "base_rail_bottom_left",
    "base_side_left",
    "bottom_outer_left_cleat",
)
PREFIX = "bottom_outer/clip_horizontal_bottom_left_1/"
AXES = {f"{PREFIX}{role}_{index}" for role in ("rail", "side") for index in (1, 2)}
RECEIVERS = {
    "rail": {"bottom_outer_left_cleat", "base_rail_bottom_left"},
    "side": {"bottom_outer_left_cleat", "base_side_left"},
}
GATES = (
    "mpc_interval_checks_passed",
    "retained_bilateral_checks_passed",
    "springa_law_checks_passed",
    "selected_floor_complementarity_passed",
    "inactive_floor_tangent_no_restraint_or_reaction_passed",
    "raw_balance_passed",
    "rounding_interval_balance_passed",
)
STATION_BAND_MM = 1e-6
TRACE_NEGATIVE = "approached_from_negative_station"
TRACE_POSITIVE = "approached_from_positive_station"
TRACE_NAMES = (TRACE_NEGATIVE, TRACE_POSITIVE)
TOL_ABS = 3e-8
TOL_REL = 3e-12


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    def reject(value: str) -> None:
        raise ValueError(f"non-standard JSON value {value} in {path}")

    return json.loads(path.read_text(), parse_constant=reject)


def vector(value: Any, label: str) -> list[float]:
    need(
        isinstance(value, (list, tuple)) and len(value) == 3,
        f"{label}: expected 3-vector",
    )
    result = []
    for component in value:
        need(
            isinstance(component, (int, float)) and not isinstance(component, bool),
            f"{label}: nonnumeric component",
        )
        number = float(component)
        need(math.isfinite(number), f"{label}: nonfinite component")
        result.append(number)
    return result


def plus(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b, strict=True)]


def minus(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b, strict=True)]


def times(a: list[float], factor: float) -> list[float]:
    return [factor * x for x in a]


def inner(a: list[float], b: list[float]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def station(frame: dict[str, Any], point: list[float]) -> float:
    return inner(
        minus(point, frame["member_start_xyz_mm"]), frame["grain_axis_global_xyz"]
    )


def moment_radius(arm: list[float], radius: list[float]) -> list[float]:
    return [
        abs(arm[1]) * radius[2] + abs(arm[2]) * radius[1],
        abs(arm[2]) * radius[0] + abs(arm[0]) * radius[2],
        abs(arm[0]) * radius[1] + abs(arm[1]) * radius[0],
    ]


def sum_vectors(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return [0.0, 0.0, 0.0]
    return [math.fsum(v[index] for v in vectors) for index in range(3)]


def point_wrench(
    actions: list[dict[str, Any]], datum: list[float]
) -> dict[str, list[float]]:
    """Sum raw point forces, couples, and componentwise rounding radii."""
    force_rows, moment_rows, force_radii, moment_radii = [], [], [], []
    for action in actions:
        arm = minus(action["point_xyz_mm"], datum)
        force = action["force_xyz_n"]
        radius = action["force_rounding_radius_xyz_n"]
        force_rows.append(force)
        moment_rows.append(cross(arm, force))
        force_radii.append(radius)
        moment_radii.append(moment_radius(arm, radius))
    return {
        "force_xyz_n": sum_vectors(force_rows),
        "moment_about_datum_xyz_nmm": sum_vectors(moment_rows),
        "force_rounding_radius_xyz_n": sum_vectors(force_radii),
        "moment_rounding_radius_xyz_nmm": sum_vectors(moment_radii),
    }


def transported(
    source: dict[str, list[float]], old: list[float], new: list[float]
) -> dict[str, list[float]]:
    """Transport a wrench using M(new)=M(old)+(old-new)×F."""
    arm = minus(old, new)
    return {
        "force_xyz_n": list(source["force_xyz_n"]),
        "moment_about_datum_xyz_nmm": plus(
            source["moment_about_datum_xyz_nmm"], cross(arm, source["force_xyz_n"])
        ),
        "force_rounding_radius_xyz_n": list(source["force_rounding_radius_xyz_n"]),
        "moment_rounding_radius_xyz_nmm": plus(
            source["moment_rounding_radius_xyz_nmm"],
            moment_radius(arm, source["force_rounding_radius_xyz_n"]),
        ),
    }


def negated(source: dict[str, list[float]]) -> dict[str, list[float]]:
    return {
        "force_xyz_n": times(source["force_xyz_n"], -1.0),
        "moment_about_datum_xyz_nmm": times(source["moment_about_datum_xyz_nmm"], -1.0),
        "force_rounding_radius_xyz_n": list(source["force_rounding_radius_xyz_n"]),
        "moment_rounding_radius_xyz_nmm": list(
            source["moment_rounding_radius_xyz_nmm"]
        ),
    }


def interval_distance(value: float, radius: float) -> float:
    return max(0.0, abs(value) - radius)


def local_components(
    wrench: dict[str, list[float]], frame: dict[str, Any]
) -> dict[str, Any]:
    force, moment = wrench["force_xyz_n"], wrench["moment_about_datum_xyz_nmm"]
    g = frame["grain_axis_global_xyz"]
    u = frame["section_u_global_xyz"]
    v = frame["section_v_global_xyz"]
    f_local = {"N": inner(force, g), "Vu": inner(force, u), "Vv": inner(force, v)}
    m_local = {"T": inner(moment, g), "Mu": inner(moment, u), "Mv": inner(moment, v)}
    uv = math.hypot(f_local["Vu"], f_local["Vv"])
    result = {
        "force_N_Vu_Vv_n": f_local,
        "moment_T_Mu_Mv_nmm": m_local,
        "transverse_uv_resultant_n_diagnostic_only": uv,
        "local_force_order": [
            "N along source grain g",
            "Vu along exact model section_u",
            "Vv along exact model section_v",
        ],
        "local_moment_order": [
            "T about source grain g",
            "Mu about exact model section_u",
            "Mv about exact model section_v",
        ],
    }
    if frame["host"] == "base_side_left":
        plus_global_crossgrain_axis = times(v, -1.0)
        result.update(
            {
                "candidate_global_plus_N_crossgrain_projection_n": inner(
                    force, plus_global_crossgrain_axis
                ),
                "candidate_global_plus_N_crossgrain_rounding_radius_n": inner(
                    wrench["force_rounding_radius_xyz_n"],
                    [abs(x) for x in plus_global_crossgrain_axis],
                ),
                "candidate_global_plus_N_axis_xyz": plus_global_crossgrain_axis,
                "candidate_FvEd_status": "conditional source point-action component only; not EC5 Fv,Ed",
            }
        )
    return result


def close_number(actual: Any, expected: Any, label: str) -> None:
    need(
        isinstance(actual, (int, float))
        and isinstance(expected, (int, float))
        and not isinstance(actual, bool)
        and not isinstance(expected, bool)
        and math.isclose(
            float(actual), float(expected), rel_tol=TOL_REL, abs_tol=TOL_ABS
        ),
        f"{label}: {actual!r} != {expected!r}",
    )


def compare_tree(actual: Any, expected: Any, label: str) -> None:
    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        need(actual == expected, f"{label}: {actual!r} != {expected!r}")
    elif isinstance(expected, (int, float)):
        close_number(actual, expected, label)
    elif isinstance(expected, list):
        need(
            isinstance(actual, list) and len(actual) == len(expected),
            f"{label}: list shape differs",
        )
        for index, (a, e) in enumerate(zip(actual, expected, strict=True)):
            compare_tree(a, e, f"{label}[{index}]")
    elif isinstance(expected, dict):
        need(
            isinstance(actual, dict) and actual.keys() == expected.keys(),
            f"{label}: keys differ",
        )
        for key, value in expected.items():
            compare_tree(actual[key], value, f"{label}.{key}")
    else:
        raise TypeError(type(expected))


def verify_pins() -> dict[str, str]:
    seen = {}
    for name, (relative, expected) in PINNED.items():
        path = relative if relative.is_absolute() else ROOT / relative
        need(path.is_file(), f"pinned {name} is missing: {path}")
        actual = digest(path)
        need(actual == expected, f"pinned {name} changed: got {actual}")
        seen[name] = actual
    return seen


def verify_known_answer() -> None:
    action = {
        "point_xyz_mm": [2.0, 3.0, 0.0],
        "force_xyz_n": [0.0, 4.0, 0.0],
        "force_rounding_radius_xyz_n": [0.1, 0.2, 0.3],
    }
    at_origin = point_wrench([action], [0.0, 0.0, 0.0])
    need(at_origin["force_xyz_n"] == [0.0, 4.0, 0.0], "known answer: force sign")
    need(
        at_origin["moment_about_datum_xyz_nmm"] == [0.0, 0.0, 8.0],
        "known answer: cross product sign",
    )
    need(
        at_origin["force_rounding_radius_xyz_n"] == [0.1, 0.2, 0.3],
        "known answer: force interval",
    )
    compare_tree(
        at_origin["moment_rounding_radius_xyz_nmm"],
        [0.9, 0.6, 0.7],
        "known answer: moment interval",
    )
    at_shift = transported(at_origin, [0.0, 0.0, 0.0], [0.0, 0.0, 2.0])
    need(
        at_shift["moment_about_datum_xyz_nmm"] == [8.0, 0.0, 8.0],
        "known answer: signed datum shift",
    )
    compare_tree(
        at_shift["moment_rounding_radius_xyz_nmm"],
        [1.3, 0.8, 0.7],
        "known answer: transported interval",
    )


def frame_from_record(
    member: str, model: dict[str, Any], binding: dict[str, Any]
) -> dict[str, Any]:
    record = model["body_geometry"][member]["geometry_record"]
    descriptor = record["source_descriptor"]
    g, u, v = (
        vector(record[k], f"{member}.{k}") for k in ("axis", "section_u", "section_v")
    )
    start, end = (vector(record[k], f"{member}.{k}") for k in ("start", "end"))
    need(
        all(abs(math.sqrt(inner(axis, axis)) - 1.0) <= 1e-8 for axis in (g, u, v)),
        f"{member}: nonunit model frame",
    )
    need(
        max(abs(inner(a, b)) for a, b in ((g, u), (g, v), (u, v))) <= 1e-8,
        f"{member}: nonorthogonal model frame",
    )
    handed = inner(cross(g, u), v)
    need(handed >= 1.0 - 1e-8, f"{member}: model frame handedness")
    length_vector = minus(end, start)
    length = inner(length_vector, g)
    need(
        length > 0
        and abs(math.sqrt(inner(length_vector, length_vector)) - length) <= 1e-6,
        f"{member}: grain extent",
    )
    need(
        descriptor["step_path"] == binding["path"],
        f"{member}: model/feature STEP path mismatch",
    )
    need(
        descriptor["step_sha256"] == binding["file_sha256"],
        f"{member}: model/feature STEP hash mismatch",
    )
    step = ROOT / binding["path"]
    need(
        step.is_file() and digest(step) == binding["file_sha256"],
        f"{member}: finished STEP bytes differ",
    )
    return {
        "host": member,
        "grain_axis_global_xyz": g,
        "section_u_global_xyz": u,
        "section_v_global_xyz": v,
        "member_start_xyz_mm": start,
        "member_end_xyz_mm": end,
        "member_grain_length_mm": length,
        "step_path": binding["path"],
        "step_sha256": binding["file_sha256"],
        "transverse_assignment_status": descriptor["transverse_status"],
    }


def feature_axes(
    features: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    need(
        features["candidate"] == CANDIDATE
        and features["geometry_revision_id"] == REVISION,
        "feature register identity differs",
    )
    all_axes = features["source_axis_groups"]["candidate_bolt_axes"]["axes"]
    ids = [axis["axis_id"] for axis in all_axes]
    need(
        len(ids) == 92 and len(set(ids)) == 92,
        "feature register must contain 92 unique axes",
    )
    axes = {axis["axis_id"]: axis for axis in all_axes if axis["axis_id"] in AXES}
    need(set(axes) == AXES, "the four bottom-left axes are not complete")
    bindings = {}
    for axis_id, axis in axes.items():
        role = axis_id.removeprefix(PREFIX).split("_")[0]
        memberships = axis["receiver_memberships"]
        member_ids = [r["receiver_member_id"] for r in memberships]
        need(
            len(member_ids) == 2 and set(member_ids) == RECEIVERS[role],
            f"{axis_id}: receiver scope or uniqueness differs",
        )
        for receiver in memberships:
            member = receiver["receiver_member_id"]
            binding = receiver["current_finished_step_binding"]
            need(
                member not in bindings or bindings[member] == binding,
                f"{member}: inconsistent finished STEP binding",
            )
            bindings[member] = binding
    need(
        set(bindings) == set(MEMBERS),
        "bottom axes do not resolve to the three expected members",
    )
    return axes, bindings


def reconstruct_planes(
    axes: dict[str, dict[str, Any]], frames: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    planes: list[dict[str, Any]] = []
    for axis_id, axis in sorted(axes.items()):
        axis_fields = axis["source_axis_fields"]
        need(
            abs(float(axis_fields["occupied_diameter_mm"]) - 6.35) < 1e-6,
            f"{axis_id}: occupied diameter changed",
        )
        datum = vector(axis_fields["datum_global_xyz_mm"], f"{axis_id} datum")
        direction = vector(axis_fields["direction_global_xyz"], f"{axis_id} direction")
        need(
            abs(math.sqrt(inner(direction, direction)) - 1.0) <= 1e-8,
            f"{axis_id}: nonunit bolt axis",
        )
        for receiver in axis["receiver_memberships"]:
            member = receiver["receiver_member_id"]
            need(
                receiver["match_status"] == "matched_bore_patch",
                f"{axis_id}/{member}: bore not matched",
            )
            feature_ids = receiver["matched_feature_ids"]
            need(
                len(feature_ids) == 1, f"{axis_id}/{member}: bore identity is ambiguous"
            )
            candidates = [
                p
                for p in receiver["cylinder_surface_candidates"]
                if p["feature_id"] == feature_ids[0]
            ]
            need(
                len(candidates) == 1,
                f"{axis_id}/{member}: matched bore patch missing or duplicated",
            )
            patch = candidates[0]
            interval = patch["patch_interval_projected_from_axis_datum_mm"]
            need(
                len(interval) == 2 and all(math.isfinite(float(x)) for x in interval),
                f"{axis_id}/{member}: invalid bore interval",
            )
            low, high = map(float, interval)
            need(
                patch["association_status"] == "eligible_bore_patch" and high > low,
                f"{axis_id}/{member}: ineligible bore interval",
            )
            radius = float(patch["cylinder_radius_mm"])
            need(
                abs(radius - 3.75) < 1e-6,
                f"{axis_id}/{member}: modeled bore radius differs",
            )
            midpoint = plus(datum, times(direction, (low + high) / 2.0))
            frame = frames[member]
            source_station = station(frame, midpoint)
            need(
                0 < source_station < frame["member_grain_length_mm"],
                f"{axis_id}/{member}: bore plane outside member",
            )
            identity = {
                "axis_id": axis_id,
                "bore_feature_id": patch["feature_id"],
                "receiver_bore_midpoint_xyz_mm": midpoint,
                "source_grain_station_mm": source_station,
                "bore_radius_mm": patch["cylinder_radius_mm"],
            }
            prior = next(
                (
                    p
                    for p in planes
                    if p["member_id"] == member
                    and abs(p["cut_station_mm"] - source_station) <= 1e-6
                ),
                None,
            )
            if prior is None:
                planes.append(
                    {
                        "plane_id": f"{member}/bore-plane-{axis_id.split('/')[-1]}",
                        "member_id": member,
                        "cut_station_mm": source_station,
                        "plane_origin_xyz_mm": plus(
                            frame["member_start_xyz_mm"],
                            times(frame["grain_axis_global_xyz"], source_station),
                        ),
                        "plane_normal_xyz": frame["grain_axis_global_xyz"],
                        "axis_memberships": [identity],
                    }
                )
            else:
                prior["axis_memberships"].append(identity)
    need(
        len(planes) == 6 and sum(len(p["axis_memberships"]) for p in planes) == 8,
        "bottom planes must be six with eight memberships",
    )
    return sorted(planes, key=lambda p: (p["member_id"], p["cut_station_mm"]))


def action_geometry_fields(action: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "action_id",
        "source_name",
        "source_row_ids",
        "source_kind",
        "role",
        "body",
        "other_body",
        "point_xyz_mm",
        "grain_station_mm",
        "finite_footprint_station_bounds_mm",
    )
    return {key: action[key] for key in fields}


def source_point_action(
    source_name: str,
    row: dict[str, Any],
    member: str,
    side: str,
    frame: dict[str, Any],
    source_kind: str,
    contact_geometry: dict[str, Any],
) -> dict[str, Any]:
    point_value = row.get(f"{side}_point", row.get("point"))
    need(point_value is not None, f"{source_name}: missing point on {member}")
    point = vector(point_value, f"{source_name} point")
    force = vector(row[f"force_on_{side}_xyz_n"], f"{source_name} force on {member}")
    radius = vector(row["force_rounding_radius_xyz_n"], f"{source_name} force radius")
    need(
        all(value >= 0 for value in radius),
        f"{source_name}: negative force uncertainty",
    )
    s = station(frame, point)
    patch: dict[str, Any] | None = None
    bounds = [s, s]
    if (
        source_kind == "physical_connection"
        and row.get("role") == "timber_or_panel_contact"
    ):
        ownership = row["_contact_ownership"]
        index = int(ownership["source_patch_index"])
        patches = contact_geometry["contact_patches"]
        need(
            0 <= index < len(patches),
            f"{source_name}: contact patch index outside source",
        )
        raw_patch = patches[index]
        pair = [row["first"], row["second"]]
        need(
            raw_patch["member_ids"] == pair,
            f"{source_name}: contact patch owners differ",
        )
        vertices = [
            vector(v, f"{source_name} contact vertex")
            for v in raw_patch["vertices_xyz_mm"]
        ]
        need(len(vertices) >= 3, f"{source_name}: contact polygon is incomplete")
        projected = [station(frame, vertex) for vertex in vertices]
        bounds = [min(projected), max(projected)]
        patch = {"source_patch_index": index}
    return {
        "action_id": f"{source_kind}:{source_name}",
        "source_name": source_name,
        "source_row_ids": list(
            row.get("source_row_ids", [row.get("source_row_id", source_name)])
        ),
        "source_kind": source_kind,
        "role": row.get(
            "role", "floor_tangent_reaction" if source_kind == "floor_tangent" else ""
        ),
        "body": member,
        "other_body": row.get("second")
        if row.get("first") == member
        else row.get("first"),
        "point_xyz_mm": point,
        "force_xyz_n": force,
        "force_rounding_radius_xyz_n": radius,
        "grain_station_mm": s,
        "finite_footprint_station_bounds_mm": bounds,
        "contact_patch": patch,
    }


def raw_actions(
    model: dict[str, Any],
    increment: dict[str, Any],
    member: str,
    frame: dict[str, Any],
    contact_geometry: dict[str, Any],
) -> list[dict[str, Any]]:
    ownership = {row["name"]: row for row in model["contact_cell_ownership"]}
    connections = []
    for name, original in sorted(increment["physical_connection_forces"].items()):
        if member not in (original["first"], original["second"]):
            continue
        row = dict(original)
        if row.get("role") == "timber_or_panel_contact":
            need(name in ownership, f"{name}: source contact-cell owner missing")
            row["_contact_ownership"] = ownership[name]
        side = "first" if row["first"] == member else "second"
        connections.append(
            source_point_action(
                name, row, member, side, frame, "physical_connection", contact_geometry
            )
        )
    tangents = []
    for row in increment["exact_floor_tangent_reactions"]:
        if member not in (row["first"], row["second"]):
            continue
        side = "first" if row["first"] == member else "second"
        tangents.append(
            source_point_action(
                row["source_row_id"],
                row,
                member,
                side,
                frame,
                "floor_tangent",
                contact_geometry,
            )
        )
    loads = []
    factor = float(increment["load_factor"])
    for node_text, force_value in sorted(
        model["physical_body_loads"][member].items(), key=lambda item: int(item[0])
    ):
        node = int(node_text)
        point = vector(model["nodes"][str(node)], f"{member} node {node} coordinate")
        force = times(vector(force_value, f"{member} node {node} body load"), factor)
        s = station(frame, point)
        loads.append(
            {
                "action_id": f"body_load:{member}:{node}",
                "source_name": f"body_load_node_{node}",
                "source_row_ids": [f"body_load_node_{node}"],
                "source_kind": "discrete_body_or_gravity_load",
                "role": "model.physical_body_loads",
                "body": member,
                "other_body": None,
                "point_xyz_mm": point,
                "force_xyz_n": force,
                "force_rounding_radius_xyz_n": [0.0, 0.0, 0.0],
                "grain_station_mm": s,
                "finite_footprint_station_bounds_mm": [s, s],
                "contact_patch": None,
            }
        )
    actions = connections + tangents + loads
    action_ids = [action["action_id"] for action in actions]
    need(
        len(action_ids) == len(set(action_ids)),
        f"{member}: duplicate point-action identity",
    )
    return actions


def expected_body_balance(
    member: str,
    actions: list[dict[str, Any]],
    audit_increment: dict[str, Any],
    response_increment: dict[str, Any],
) -> dict[str, Any]:
    audit_body = audit_increment["body_equilibrium"][member]
    response_body = response_increment["physical_balance"]["body_equilibrium"][member]
    datum = vector(audit_body["reference_xyz_mm"], f"{member} audit datum")
    wrench = point_wrench(actions, datum)
    for audit_key, result_key in (
        ("force_residual_xyz_n", "force_xyz_n"),
        ("moment_residual_xyz_nmm", "moment_about_datum_xyz_nmm"),
        ("force_rounding_radius_xyz_n", "force_rounding_radius_xyz_n"),
        ("moment_rounding_radius_xyz_nmm", "moment_rounding_radius_xyz_nmm"),
    ):
        compare_tree(
            response_body[audit_key],
            audit_body[audit_key],
            f"{member} raw response/audit {audit_key}",
        )
        compare_tree(
            audit_body[audit_key],
            wrench[result_key],
            f"{member} raw point-action sum {audit_key}",
        )
    need(
        response_body["printed_resultants_passed"] is True
        and response_body["interval_resultants_passed"] is True,
        f"{member}: frozen response body balance gate failed",
    )
    need(
        audit_body["printed_resultants_passed"] is True
        and audit_body["interval_resultants_passed"] is True,
        f"{member}: frozen body audit gate failed",
    )
    connection_count = sum(a["source_kind"] == "physical_connection" for a in actions)
    tangent_count = sum(a["source_kind"] == "floor_tangent" for a in actions)
    load_count = sum(
        a["source_kind"] == "discrete_body_or_gravity_load" for a in actions
    )
    return {
        "host": member,
        "source_connection_action_count_including_floor_normal": connection_count,
        "source_floor_tangent_action_count": tangent_count,
        "discrete_body_or_gravity_load_node_count": load_count,
        "datum_xyz_mm": datum,
        "point_action_external_residual_force_xyz_n": wrench["force_xyz_n"],
        "point_action_external_residual_moment_xyz_nmm": wrench[
            "moment_about_datum_xyz_nmm"
        ],
        "propagated_force_rounding_radius_xyz_n": wrench["force_rounding_radius_xyz_n"],
        "propagated_moment_rounding_radius_xyz_nmm": wrench[
            "moment_rounding_radius_xyz_nmm"
        ],
        "force_interval_distance_from_zero_n": [
            interval_distance(x, r)
            for x, r in zip(
                wrench["force_xyz_n"],
                wrench["force_rounding_radius_xyz_n"],
                strict=True,
            )
        ],
        "moment_interval_distance_from_zero_nmm": [
            interval_distance(x, r)
            for x, r in zip(
                wrench["moment_about_datum_xyz_nmm"],
                wrench["moment_rounding_radius_xyz_nmm"],
                strict=True,
            )
        ],
        "independent_frozen_all_body_audit_reproduced": True,
        "response_and_audit_limits": "The frozen 0.1 N / 2 N mm whole-body bookkeeping gates apply to extraction closure only.",
        "_external": {**wrench, "_datum_xyz_mm": datum},
    }


def cut_expected(
    actions: list[dict[str, Any]],
    station_mm: float,
    frame: dict[str, Any],
    trace: str,
    body_external: dict[str, Any],
) -> dict[str, Any]:
    datum = plus(
        frame["member_start_xyz_mm"], times(frame["grain_axis_global_xyz"], station_mm)
    )
    positive, negative = [], []
    for action in actions:
        distance = action["grain_station_mm"] - station_mm
        on_plane = abs(distance) <= STATION_BAND_MM
        positive_side = distance > STATION_BAND_MM or (
            on_plane and trace == TRACE_NEGATIVE
        )
        (positive if positive_side else negative).append(action)
    positive_external = point_wrench(positive, datum)
    negative_external = point_wrench(negative, datum)
    positive_internal = negated(positive_external)
    negative_internal = negated(negative_external)
    closure_force = plus(
        positive_external["force_xyz_n"], negative_external["force_xyz_n"]
    )
    closure_moment = plus(
        positive_external["moment_about_datum_xyz_nmm"],
        negative_external["moment_about_datum_xyz_nmm"],
    )
    closure_force_radius = plus(
        positive_external["force_rounding_radius_xyz_n"],
        negative_external["force_rounding_radius_xyz_n"],
    )
    closure_moment_radius = plus(
        positive_external["moment_rounding_radius_xyz_nmm"],
        negative_external["moment_rounding_radius_xyz_nmm"],
    )
    all_at_cut = transported(body_external, body_external["_datum_xyz_mm"], datum)
    compare_tree(
        closure_force, all_at_cut["force_xyz_n"], "two-half-body force closure"
    )
    compare_tree(
        closure_moment,
        all_at_cut["moment_about_datum_xyz_nmm"],
        "two-half-body moment closure",
    )
    on_plane_connection = [
        a["source_name"]
        for a in actions
        if a["source_kind"] != "discrete_body_or_gravity_load"
        and abs(a["grain_station_mm"] - station_mm) <= STATION_BAND_MM
    ]
    on_plane_loads = [
        a["source_name"]
        for a in actions
        if a["source_kind"] == "discrete_body_or_gravity_load"
        and abs(a["grain_station_mm"] - station_mm) <= STATION_BAND_MM
    ]
    return {
        "cut_station_mm": station_mm,
        "cut_plane_origin_xyz_mm": datum,
        "section_plane_normal_global_xyz": frame["grain_axis_global_xyz"],
        "trace": trace,
        "on_plane_action_assignment": "positive-side external set"
        if trace == TRACE_NEGATIVE
        else "negative-side external set",
        "source_actions_on_positive_station_side": [a["source_name"] for a in positive],
        "source_actions_on_negative_station_side": [a["source_name"] for a in negative],
        "body_load_nodes_on_positive_station_side": [
            a["source_name"]
            for a in positive
            if a["source_kind"] == "discrete_body_or_gravity_load"
        ],
        "body_load_nodes_on_negative_station_side": [
            a["source_name"]
            for a in negative
            if a["source_kind"] == "discrete_body_or_gravity_load"
        ],
        "positive_side_external_wrench_at_cut": positive_external,
        "negative_side_external_wrench_at_cut": negative_external,
        "internal_cut_wrench_on_positive_side_material": positive_internal,
        "internal_cut_wrench_on_negative_side_material": negative_internal,
        "internal_cut_wrench_on_positive_side_local": local_components(
            positive_internal, frame
        ),
        "internal_cut_wrench_on_negative_side_local": local_components(
            negative_internal, frame
        ),
        "two_side_external_closure_at_cut": {
            "force_residual_xyz_n": closure_force,
            "force_rounding_radius_xyz_n": closure_force_radius,
            "force_interval_distance_from_zero_n": [
                interval_distance(x, r)
                for x, r in zip(closure_force, closure_force_radius, strict=True)
            ],
            "moment_residual_xyz_nmm": closure_moment,
            "moment_rounding_radius_xyz_nmm": closure_moment_radius,
            "moment_interval_distance_from_zero_nmm": [
                interval_distance(x, r)
                for x, r in zip(closure_moment, closure_moment_radius, strict=True)
            ],
            "whole_host_residual_reproduced_at_cut": True,
        },
        "source_actions_on_plane": on_plane_connection,
        "discrete_load_nodes_on_plane": on_plane_loads,
        "force_radius_interval_contains_zero_on_both_half_body_closure": all(
            interval_distance(x, r) == 0
            for x, r in zip(closure_force, closure_force_radius, strict=True)
        ),
        "moment_radius_interval_contains_zero_on_both_half_body_closure": all(
            interval_distance(x, r) == 0
            for x, r in zip(closure_moment, closure_moment_radius, strict=True)
        ),
        "_positive_internal": positive_internal,
        "_negative_internal": negative_internal,
        "_datum": datum,
    }


def expected_centroid_wrench(
    source: dict[str, list[float]], plane_datum: list[float], centroid: list[float]
) -> dict[str, list[float]]:
    return transported(source, plane_datum, centroid)


def verify_report(report_path: Path) -> dict[str, Any]:
    source_hashes = verify_pins()
    verify_known_answer()
    report = read_json(report_path)
    need(report["schema"] == "bottom_outer_finished_sections/v1", "wrong replay schema")
    need(
        report["status"] == "PASS_FROZEN_GEOMETRY_AND_POINT_ACTION_DEMAND_JOIN_ONLY",
        "unexpected replay status",
    )
    need(
        report["candidate"] == CANDIDATE and report["geometry_revision_id"] == REVISION,
        "replay candidate/revision identity differs",
    )
    need(
        report["producer_sha256"] == source_hashes["producer"],
        "report producer hash differs",
    )

    features = read_json(ROOT / FEATURES)
    freeze = read_json(ROOT / FREEZE)
    contact_geometry = read_json(ROOT / CONTACT)
    need(
        freeze["candidate"] == CANDIDATE and freeze["geometry_revision_id"] == REVISION,
        "freeze candidate/revision differs",
    )
    need(set(freeze["cases"]) == set(CASES), "freeze case family differs")
    expected_source_pins = {
        "axis_features": {
            "path": FEATURES.as_posix(),
            "sha256": source_hashes["axis_features"],
        },
        "three_case_freeze": {
            "path": FREEZE.as_posix(),
            "sha256": source_hashes["three_case_freeze"],
        },
        "source_contact_geometry": {
            "path": CONTACT.as_posix(),
            "sha256": source_hashes["source_contact_geometry"],
        },
        "point_action_method": {
            "path": HOST_METHOD.as_posix(),
            "sha256": source_hashes["point_action_method"],
        },
        "finished_section_method": {
            "path": SECTION_METHOD.as_posix(),
            "sha256": source_hashes["finished_section_method"],
        },
    }
    compare_tree(report["source_pins"], expected_source_pins, "report source pins")
    compare_tree(
        report["case_sources"], freeze["cases"], "report frozen case provenance"
    )

    axes, bindings = feature_axes(features)
    cases: dict[str, dict[str, Any]] = {}
    for case in CASES:
        files = freeze["cases"][case]
        for kind, pinned in files.items():
            source_path = ROOT / pinned["path"]
            need(
                source_path.is_file() and digest(source_path) == pinned["sha256"],
                f"{case}: changed frozen {kind}",
            )
        model = read_json(ROOT / files["model"]["path"])
        response = read_json(ROOT / files["response"]["path"])
        audit = read_json(ROOT / files["all_body_audit"]["path"])
        need(
            model["candidate"] == response["candidate"] == CANDIDATE,
            f"{case}: candidate mismatch",
        )
        need(
            model["geometry_revision_id"]
            == response["geometry_revision_id"]
            == REVISION,
            f"{case}: revision mismatch",
        )
        need(
            model["case_id"] == response["case_id"] == case,
            f"{case}: case identity mismatch",
        )
        need(
            len(response["increments"]) == len(audit["increments"]) == len(FACTORS),
            f"{case}: expected seven increments",
        )
        for index, (increment, audited, factor) in enumerate(
            zip(response["increments"], audit["increments"], FACTORS, strict=True)
        ):
            need(
                float(increment["load_factor"])
                == factor
                == float(audited["load_factor"]),
                f"{case}/{index}: load-factor sequence differs",
            )
            need(
                all(increment.get(gate) is True for gate in GATES)
                and audited["passed"] is True,
                f"{case}/{index}: frozen source gate failed",
            )
        cases[case] = {"model": model, "response": response, "audit": audit}

    frames_by_case = {
        case: {
            member: frame_from_record(member, records["model"], bindings[member])
            for member in MEMBERS
        }
        for case, records in cases.items()
    }
    frames = frames_by_case[CASES[0]]
    for case in CASES[1:]:
        compare_tree(frames_by_case[case], frames, f"{case} frozen member frames")
    compare_tree(
        report["member_frames"], frames, "report member frames and STEP bindings"
    )

    planes = reconstruct_planes(axes, frames)
    actual_planes = report["planes"]
    need(len(actual_planes) == len(planes), "report plane count differs")
    plane_by_id = {row["plane_id"]: row for row in actual_planes}
    need(len(plane_by_id) == len(actual_planes), "duplicate report plane id")
    for expected in planes:
        need(
            expected["plane_id"] in plane_by_id,
            f"report missing plane {expected['plane_id']}",
        )
        actual = plane_by_id[expected["plane_id"]]
        for key in (
            "member_id",
            "cut_station_mm",
            "plane_origin_xyz_mm",
            "plane_normal_xyz",
            "axis_memberships",
        ):
            compare_tree(
                actual[key], expected[key], f"plane {expected['plane_id']}.{key}"
            )
        section = actual["finished_section"]
        need(
            section["component_count"] == len(section["components"])
            and section["component_count"] >= 1,
            f"{expected['plane_id']}: section component census differs",
        )
        compare_tree(
            section["area_mm2"],
            math.fsum(float(c["area_mm2"]) for c in section["components"]),
            f"{expected['plane_id']} component areas",
        )
        need(
            section["common_strain_or_component_load_sharing_established"] is False,
            f"{expected['plane_id']}: unsupported load-sharing claim",
        )
        need(
            section["actual_integrated_traction_established"] is False
            and section["section_resistance_accepted"] is False,
            f"{expected['plane_id']}: unsupported mechanics/resistance claim",
        )
        centroid = vector(
            section["centroid_global_xyz_mm"], f"{expected['plane_id']} centroid"
        )
        need(
            abs(
                inner(
                    minus(centroid, actual["plane_origin_xyz_mm"]),
                    actual["plane_normal_xyz"],
                )
            )
            <= 1e-5,
            f"{expected['plane_id']}: section centroid is outside grain-normal plane",
        )
    expected_counts = {
        "axes": 4,
        "members": 3,
        "receiver_memberships": 8,
        "unique_planes": 6,
        "whole_body_states": 63,
        "two_trace_cut_states": 252,
    }
    compare_tree(report["counts"], expected_counts, "report coverage counts")
    expected_limits = {
        "current_cases": 3,
        "actual_traction": False,
        "common_strain": False,
        "per_ligament_force_sharing": False,
        "adopted_resistance": False,
        "criterion_pass": False,
        "joint_accepted": False,
        "native_solve": False,
        "geometry_changed": False,
    }
    compare_tree(report["claim_limits"], expected_limits, "report claim limits")

    expected_geometry: dict[str, list[dict[str, Any]]] = {}
    expected_bodies: dict[tuple[str, int, str], dict[str, Any]] = {}
    expected_cuts: dict[tuple[str, int, str, str, str], dict[str, Any]] = {}
    plane_by_member: dict[str, list[dict[str, Any]]] = {
        member: [] for member in MEMBERS
    }
    for plane in planes:
        plane_by_member[plane["member_id"]].append(plane)

    for case in CASES:
        model, response, audit = (
            cases[case][name] for name in ("model", "response", "audit")
        )
        for index, (increment, audited) in enumerate(
            zip(response["increments"], audit["increments"], strict=True)
        ):
            for member in MEMBERS:
                actions = raw_actions(
                    model, increment, member, frames[member], contact_geometry
                )
                geometry = [action_geometry_fields(a) for a in actions]
                if member not in expected_geometry:
                    expected_geometry[member] = geometry
                else:
                    compare_tree(
                        geometry,
                        expected_geometry[member],
                        f"{case}/{index}/{member} static action geometry",
                    )
                body = expected_body_balance(member, actions, audited, increment)
                expected_bodies[(case, index, member)] = {
                    "case_id": case,
                    "increment_index": index,
                    "load_factor": float(increment["load_factor"]),
                    "member_id": member,
                    "source_action_count": len(actions),
                    "whole_body_source_balance": {
                        k: v for k, v in body.items() if k != "_external"
                    },
                }
                for plane in plane_by_member[member]:
                    for trace in TRACE_NAMES:
                        cut = cut_expected(
                            actions,
                            plane["cut_station_mm"],
                            frames[member],
                            trace,
                            body["_external"],
                        )
                        centroid = plane_by_id[plane["plane_id"]]["finished_section"][
                            "centroid_global_xyz_mm"
                        ]
                        positive_centroid = expected_centroid_wrench(
                            cut["_positive_internal"], cut["_datum"], centroid
                        )
                        negative_centroid = expected_centroid_wrench(
                            cut["_negative_internal"], cut["_datum"], centroid
                        )
                        cut_public = {
                            k: v for k, v in cut.items() if not k.startswith("_")
                        }
                        crossing = sorted(
                            a["source_name"]
                            for a in actions
                            if a["contact_patch"] is not None
                            and a["finite_footprint_station_bounds_mm"][0]
                            + STATION_BAND_MM
                            < plane["cut_station_mm"]
                            < a["finite_footprint_station_bounds_mm"][1]
                            - STATION_BAND_MM
                        )
                        cut_key = (case, index, member, plane["plane_id"], trace)
                        expected_cuts[cut_key] = {
                            "case_id": case,
                            "increment_index": index,
                            "load_factor": float(increment["load_factor"]),
                            "plane_id": plane["plane_id"],
                            "member_id": member,
                            "source_point_action_cut": cut_public,
                            "positive_internal_wrench_at_finished_area_centroid": positive_centroid,
                            "negative_internal_wrench_at_finished_area_centroid": negative_centroid,
                            "positive_local_wrench_at_finished_area_centroid": local_components(
                                positive_centroid, frames[member]
                            ),
                            "negative_local_wrench_at_finished_area_centroid": local_components(
                                negative_centroid, frames[member]
                            ),
                            "finite_contact_patch_bounds_crossing_plane": crossing,
                            "finite_patch_or_ligament_force_distribution_established": False,
                            "section_resistance_accepted": False,
                        }

    plane_ids = {plane["plane_id"] for plane in planes}
    crossing_plane_ids = {
        key[3]
        for key, state in expected_cuts.items()
        if state["finite_contact_patch_bounds_crossing_plane"]
    }
    need(
        crossing_plane_ids == plane_ids,
        "not every bore plane crosses a finite source contact-patch extent",
    )

    compare_tree(
        report["member_action_geometry"],
        expected_geometry,
        "report complete raw action geometry",
    )
    body_rows = report["whole_body_states"]
    body_keys = [
        (r["case_id"], r["increment_index"], r["member_id"]) for r in body_rows
    ]
    need(
        len(body_rows) == 63 and len(set(body_keys)) == len(body_rows),
        "whole-body row identities are missing or duplicated",
    )
    need(set(body_keys) == set(expected_bodies), "whole-body identity coverage differs")
    for row in body_rows:
        key = (row["case_id"], row["increment_index"], row["member_id"])
        compare_tree(row, expected_bodies[key], f"whole-body state {key}")

    cut_rows = report["cut_states"]
    cut_keys = [
        (
            r["case_id"],
            r["increment_index"],
            r["member_id"],
            r["plane_id"],
            r["source_point_action_cut"]["trace"],
        )
        for r in cut_rows
    ]
    need(
        len(cut_rows) == 252 and len(set(cut_keys)) == len(cut_rows),
        "cut rows are missing or duplicated",
    )
    need(
        set(cut_keys) == set(expected_cuts),
        "two-trace plane/state identity coverage differs",
    )
    for row in cut_rows:
        key = (
            row["case_id"],
            row["increment_index"],
            row["member_id"],
            row["plane_id"],
            row["source_point_action_cut"]["trace"],
        )
        compare_tree(row, expected_cuts[key], f"cut state {key}")

    return {
        "status": "PASS_INDEPENDENT_RAW_SOURCE_REPLAY",
        "report_path": str(report_path),
        "producer_sha256": source_hashes["producer"],
        "point_action_method_sha256": source_hashes["point_action_method"],
        "finished_section_method_sha256": source_hashes["finished_section_method"],
        "axis_features_sha256": source_hashes["axis_features"],
        "freeze_sha256": source_hashes["three_case_freeze"],
        "contact_geometry_sha256": source_hashes["source_contact_geometry"],
        "case_families": len(CASES),
        "increments_per_family": len(FACTORS),
        "members": len(MEMBERS),
        "finished_step_bindings": len(bindings),
        "bore_memberships": sum(len(p["axis_memberships"]) for p in planes),
        "grain_normal_planes": len(planes),
        "planes_with_finite_contact_patch_crossings": len(crossing_plane_ids),
        "whole_body_states_replayed": len(body_rows),
        "two_trace_cut_states_replayed": len(cut_rows),
        "independent_known_answer": "PASS",
        "limitations": [
            "No STEP/CAD extraction was run here; finished-section properties and centroids were checked as report inputs against source-plane identity and the separate geometry review.",
            "This checks point-action equilibrium and bookkeeping only; it does not establish section traction, force sharing, resistance, strength, or joint acceptance.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help="producer replay JSON (default: %(default)s)",
    )
    args = parser.parse_args()
    result = verify_report(args.report)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
