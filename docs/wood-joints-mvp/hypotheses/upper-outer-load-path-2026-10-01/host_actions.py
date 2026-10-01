#!/usr/bin/env python3
"""Extract conditional point-action host sections for the upper outer cleats.

All actions are reconstructed from the three frozen response families.  The
section resultants are equilibrium demands for the declared point-action
model; they are not integrated FE tractions or a strength check.
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

CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
UPPER = "docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/upper-joints.json"
UPPER_FREEZE = "docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/freeze.json"
CONTACT_GEOMETRY = "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json"
STEP_ROOT = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members"
OUTPUT = HERE / "host-actions.json"

CASES = {
    "a1-rear": {
        "model": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a1-rear-attempt02/model.json",
        "response": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a1-rear-attempt02/response-zero-u-token.json",
        "all_body_audit": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a1-rear-attempt02/parent-all-body-response-audit.json",
        "sha256": {
            "model": "72d043e1a70702d8d464c21a039e897036e17c95e368ec776063584dac74f5fd",
            "response": "257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c",
            "all_body_audit": "247845921630a092c3f7a79d9ac11c92d732f021d2cb1dc5214e54b1a344deca",
        },
    },
    "a12-rear": {
        "model": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/model.json",
        "response": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/response.json",
        "all_body_audit": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/parent-all-body-response-audit.json",
        "sha256": {
            "model": "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
            "response": "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274",
            "all_body_audit": "3da26086016c01f830e055bfa72c8a55370c9adc138b28d73127596924c410d5",
        },
    },
    "k12-rear": {
        "model": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-native-attempt01/model.json",
        "response": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-native-attempt01/response.json",
        "all_body_audit": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-native-attempt01/audit.json",
        "sha256": {
            "model": "8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd",
            "response": "42ffb135d47bd3bd28874e886682b4f07175ee060fb383b6e3c128e5102073c6",
            "all_body_audit": "66c2b9aa397b16cd4c0b2420c5cf4588e15d12bfd3fbfd75b7df8f2b0d1d4bee",
        },
    },
}

PINNED_SHA256 = {
    UPPER: "0fc5f9ce9c92effcb01d3213c38b33282c281539dab9d48cb06f33e15c1994a6",
    UPPER_FREEZE: "d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73",
    CONTACT_GEOMETRY: "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    **{
        CASES[case][kind]: digest
        for case in CASES
        for kind, digest in CASES[case]["sha256"].items()
    },
    f"{STEP_ROOT}/base_rail_top.step": "79b4f7f66f35928ed383d0e396ce221d9a4302136b088a7bcd41749c52a10a60",
    f"{STEP_ROOT}/base_side_left.step": "237c3fa6aa0b52c39124580810d048e38919b99b9a1fb5db5a2423e7eda62fdf",
    f"{STEP_ROOT}/base_side_right.step": "ddb6ac20f1f50a9036448eb5680fdc486532ff3826ce52d566baf685a800a59f",
}

HOSTS = {
    "base_rail_top": ("top_outer_left_cleat", "top_outer_right_cleat"),
    "base_side_left": ("top_outer_left_cleat",),
    "base_side_right": ("top_outer_right_cleat",),
}
BLOCK_HOSTS = {
    "top_outer_left_cleat": ("base_rail_top", "base_side_left"),
    "top_outer_right_cleat": ("base_rail_top", "base_side_right"),
}
LOAD_FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
TOLERANCE_N = 0.1
TOLERANCE_NMM = 2.0
STATION_BAND_MM = 1e-6
BRACKET_CLEARANCE_MM = 1.0


class SourceRefusal(ValueError):
    """A source pin, geometry relation, or ownership contract is not exact."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceRefusal(message)


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def _reject_constant(value: str) -> None:
    raise SourceRefusal(f"non-standard JSON numeric value: {value}")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(), parse_constant=_reject_constant)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SourceRefusal(f"cannot parse {path}: {exc}") from exc


def verify_pins(root: Path = ROOT) -> list[dict[str, str]]:
    records = []
    for relative, expected in sorted(PINNED_SHA256.items()):
        path = root / relative
        require(path.is_file(), f"required pinned input is missing: {relative}")
        actual = sha256_file(path)
        require(actual == expected, f"changed pinned input {relative}: {actual}")
        records.append({"path": relative, "sha256": expected})
    return records


def finite(value: Any, label: str) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{label} is not numeric")
    result = float(value)
    require(math.isfinite(result), f"{label} is nonfinite")
    return result


def vec(value: Any, label: str) -> list[float]:
    require(isinstance(value, (list, tuple)) and len(value) == 3, f"{label} is not a three-vector")
    return [finite(component, f"{label}[{index}]") for index, component in enumerate(value)]


def add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b, strict=True)]


def sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b, strict=True)]


def scale(a: list[float], factor: float) -> list[float]:
    return [factor * x for x in a]


def dot(a: list[float], b: list[float]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def norm(a: list[float]) -> float:
    return math.sqrt(dot(a, a))


def vector_sum(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return [0.0, 0.0, 0.0]
    return [math.fsum(vector[index] for vector in vectors) for index in range(3)]


def moment_radius(arm: list[float], radius: list[float]) -> list[float]:
    return [
        abs(arm[1]) * radius[2] + abs(arm[2]) * radius[1],
        abs(arm[2]) * radius[0] + abs(arm[0]) * radius[2],
        abs(arm[0]) * radius[1] + abs(arm[1]) * radius[0],
    ]


def wrench(actions: list[dict[str, Any]], datum: list[float]) -> dict[str, list[float]]:
    forces, moments, radii, moment_radii = [], [], [], []
    for action in actions:
        arm = sub(action["point_xyz_mm"], datum)
        force = action["force_xyz_n"]
        radius = action["force_rounding_radius_xyz_n"]
        forces.append(force)
        moments.append(cross(arm, force))
        radii.append(radius)
        moment_radii.append(moment_radius(arm, radius))
    return {
        "force_xyz_n": vector_sum(forces),
        "moment_about_datum_xyz_nmm": vector_sum(moments),
        "force_rounding_radius_xyz_n": vector_sum(radii),
        "moment_rounding_radius_xyz_nmm": vector_sum(moment_radii),
    }


def negated_wrench(source: dict[str, list[float]]) -> dict[str, list[float]]:
    return {
        "force_xyz_n": scale(source["force_xyz_n"], -1.0),
        "moment_about_datum_xyz_nmm": scale(source["moment_about_datum_xyz_nmm"], -1.0),
        "force_rounding_radius_xyz_n": list(source["force_rounding_radius_xyz_n"]),
        "moment_rounding_radius_xyz_nmm": list(source["moment_rounding_radius_xyz_nmm"]),
    }


def transport_wrench(source: dict[str, list[float]], from_datum: list[float], to_datum: list[float]) -> dict[str, list[float]]:
    """Transport a wrench from its current datum to a new datum."""
    arm = sub(from_datum, to_datum)
    moment = add(source["moment_about_datum_xyz_nmm"], cross(arm, source["force_xyz_n"]))
    mr = moment_radius(arm, source["force_rounding_radius_xyz_n"])
    return {
        "force_xyz_n": list(source["force_xyz_n"]),
        "moment_about_datum_xyz_nmm": moment,
        "force_rounding_radius_xyz_n": list(source["force_rounding_radius_xyz_n"]),
        "moment_rounding_radius_xyz_nmm": add(source["moment_rounding_radius_xyz_nmm"], mr),
    }


def negate_action(action: dict[str, Any]) -> dict[str, Any]:
    copied = dict(action)
    copied["force_xyz_n"] = scale(action["force_xyz_n"], -1.0)
    return copied


def interval_distance(value: float, radius: float) -> float:
    return max(0.0, abs(value) - radius)


def local_wrench(source: dict[str, list[float]], frame: dict[str, Any]) -> dict[str, Any]:
    force, moment = source["force_xyz_n"], source["moment_about_datum_xyz_nmm"]
    g, u, v = frame["grain_axis_global_xyz"], frame["section_u_global_xyz"], frame["section_v_global_xyz"]
    f_local = {"N": dot(force, g), "Vu": dot(force, u), "Vv": dot(force, v)}
    m_local = {"T": dot(moment, g), "Mu": dot(moment, u), "Mv": dot(moment, v)}
    uv = math.hypot(f_local["Vu"], f_local["Vv"])
    result = {
        "force_N_Vu_Vv_n": f_local,
        "moment_T_Mu_Mv_nmm": m_local,
        "transverse_uv_resultant_n_diagnostic_only": uv,
        "local_force_order": ["N along source grain g", "Vu along exact model section_u", "Vv along exact model section_v"],
        "local_moment_order": ["T about source grain g", "Mu about exact model section_u", "Mv about exact model section_v"],
    }
    if frame["host"] == "base_rail_top":
        plus_global_crossgrain_axis = v
    elif frame["host"] in ("base_side_left", "base_side_right"):
        plus_global_crossgrain_axis = scale(v, -1.0)
    else:
        plus_global_crossgrain_axis = None
    if plus_global_crossgrain_axis is not None:
        radius = source["force_rounding_radius_xyz_n"]
        result["candidate_global_plus_N_crossgrain_projection_n"] = dot(force, plus_global_crossgrain_axis)
        result["candidate_global_plus_N_crossgrain_rounding_radius_n"] = dot(radius, [abs(x) for x in plus_global_crossgrain_axis])
        result["candidate_global_plus_N_axis_xyz"] = plus_global_crossgrain_axis
        result["candidate_FvEd_status"] = "conditional source point-action component only; not EC5 Fv,Ed"
    return result


def close_vector(actual: list[float], expected: list[float], tolerance: float, label: str) -> None:
    require(max(abs(a - b) for a, b in zip(actual, expected, strict=True)) <= tolerance, label)


def source_documents(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    upper = read_json(root / UPPER)
    freeze = read_json(root / UPPER_FREEZE)
    require(upper["candidate"] == CANDIDATE, "upper-joints candidate mismatch")
    require(upper["geometry_revision_id"] == REVISION, "upper-joints revision mismatch")
    require(upper["freeze_sha256"] == PINNED_SHA256[UPPER_FREEZE], "upper-joints freeze identity mismatch")
    for case, sources in CASES.items():
        require(case in upper["source_cases"], f"upper-joints is missing case {case}")
        for kind in ("model", "response", "all_body_audit"):
            recorded = upper["source_cases"][case][kind]
            require(recorded["path"] == sources[kind], f"upper-joints {case} {kind} path mismatch")
            require(recorded["sha256"] == sources["sha256"][kind], f"upper-joints {case} {kind} pin mismatch")
            freeze_kind = "all_body_audit" if kind == "all_body_audit" else kind
            frozen = freeze["cases"][case][freeze_kind]
            require(frozen["path"] == sources[kind], f"freeze {case} {kind} path mismatch")
            require(frozen["sha256"] == sources["sha256"][kind], f"freeze {case} {kind} pin mismatch")
    return upper, read_json(root / CONTACT_GEOMETRY)


def frame_for_host(model: dict[str, Any], host: str) -> dict[str, Any]:
    require(host in model["body_geometry"], f"model does not own host {host}")
    geometry = model["body_geometry"][host]["geometry_record"]
    descriptor = geometry.get("source_descriptor", {})
    g = vec(geometry["axis"], f"{host} grain axis")
    u = vec(geometry["section_u"], f"{host} section_u")
    v = vec(geometry["section_v"], f"{host} section_v")
    start, end = vec(geometry["start"], f"{host} start"), vec(geometry["end"], f"{host} end")
    require(abs(norm(g) - 1.0) <= 1e-8 and abs(norm(u) - 1.0) <= 1e-8 and abs(norm(v) - 1.0) <= 1e-8, f"{host} frame has nonunit axes")
    require(max(abs(dot(g, u)), abs(dot(g, v)), abs(dot(u, v))) <= 1e-8, f"{host} frame axes are not orthogonal")
    require(dot(cross(g, u), v) >= 1.0 - 1e-8, f"{host} frame handedness changed")
    length = dot(sub(end, start), g)
    require(length > 0 and abs(norm(sub(end, start)) - length) <= 1e-6, f"{host} grain extent is not collinear with its source axis")
    source_step = f"{STEP_ROOT}/{host}.step"
    require(descriptor.get("step_path") in (None, source_step), f"{host} STEP path differs from its source descriptor")
    require(descriptor.get("step_sha256") in (None, PINNED_SHA256[source_step]), f"{host} STEP hash differs from its source descriptor")
    return {
        "host": host,
        "grain_axis_global_xyz": g,
        "section_u_global_xyz": u,
        "section_v_global_xyz": v,
        "section_u_source_label": descriptor.get("section_u_source_axis"),
        "section_v_source_label": descriptor.get("section_v_source_axis"),
        "member_start_xyz_mm": start,
        "member_end_xyz_mm": end,
        "member_grain_length_mm": length,
        "width_mm_from_source_model": finite(geometry["width_mm"], f"{host} width"),
        "depth_mm_from_source_model": finite(geometry["depth_mm"], f"{host} depth"),
        "step_path": source_step,
        "step_sha256": PINNED_SHA256[source_step],
        "transverse_assignment_status": descriptor.get("transverse_status", "source model axes retained verbatim"),
    }


def station(frame: dict[str, Any], point: list[float]) -> float:
    return dot(sub(point, frame["member_start_xyz_mm"]), frame["grain_axis_global_xyz"])


def contact_patch_for_row(
    row_name: str,
    row: dict[str, Any],
    contact_ownership: dict[str, dict[str, Any]],
    contact_geometry: dict[str, Any],
    frame: dict[str, Any],
) -> dict[str, Any] | None:
    if row["role"] != "timber_or_panel_contact":
        return None
    ownership = contact_ownership.get(row_name)
    require(ownership is not None, f"contact row has no source patch owner: {row_name}")
    patch_index = int(ownership["source_patch_index"])
    require(0 <= patch_index < len(contact_geometry["contact_patches"]), f"contact source patch index is invalid: {row_name}")
    patch = contact_geometry["contact_patches"][patch_index]
    expected_pair = [row["first"], row["second"]]
    require(patch["member_ids"] == expected_pair, f"contact source patch owners differ for {row_name}")
    vertices = [vec(vertex, f"{row_name} patch vertex") for vertex in patch["vertices_xyz_mm"]]
    require(len(vertices) >= 3, f"contact patch has no polygon vertices: {row_name}")
    bounds = [station(frame, vertex) for vertex in vertices]
    point = vec(row["point"], f"{row_name} point")
    return {
        "source_patch_index": patch_index,
        "source_patch_member_pair": expected_pair,
        "source_patch_area_mm2": finite(patch["area_mm2"], f"{row_name} source patch area"),
        "contact_cell_area_mm2": finite(ownership["area_mm2"], f"{row_name} cell area"),
        "contact_cell_centroid_station_mm": station(frame, point),
        "finite_patch_station_bounds_mm": [min(bounds), max(bounds)],
        "finite_patch_vertex_count": len(vertices),
        "footprint_method": "projection of all vertices of the frozen source contact-patch polygon onto the exact model grain axis",
    }


def point_action(
    name: str,
    row: dict[str, Any],
    body: str,
    side: str,
    frame: dict[str, Any],
    patch: dict[str, Any] | None,
    source_kind: str = "physical_connection",
) -> dict[str, Any]:
    point = row.get(f"{side}_point", row.get("point"))
    require(point is not None, f"{name} has no {body}-specific point")
    force = vec(row[f"force_on_{side}_xyz_n"], f"{name} force on {body}")
    radius = vec(row["force_rounding_radius_xyz_n"], f"{name} force radius")
    require(all(value >= 0 for value in radius), f"{name} has a negative force radius")
    xyz = vec(point, f"{name} point")
    s = station(frame, xyz)
    bounds = patch["finite_patch_station_bounds_mm"] if patch else [s, s]
    return {
        "action_id": f"{source_kind}:{name}",
        "source_name": name,
        "source_row_ids": list(row.get("source_row_ids", [row.get("source_row_id", name)])),
        "source_kind": source_kind,
        "role": row.get("role", "floor_tangent_reaction" if source_kind == "floor_tangent" else ""),
        "body": body,
        "other_body": row.get("second") if row.get("first") == body else row.get("first"),
        "point_xyz_mm": xyz,
        "force_xyz_n": force,
        "force_rounding_radius_xyz_n": radius,
        "grain_station_mm": s,
        "finite_footprint_station_bounds_mm": list(bounds),
        "source_area_mm2": row.get("source_area_mm2"),
        "contact_patch": patch,
    }


def host_actions_for_state(
    model: dict[str, Any], increment: dict[str, Any], host: str, frame: dict[str, Any], contact_geometry: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    load_factor = finite(increment["load_factor"], f"{host} increment load factor")
    require(load_factor > 0.0, f"{host} increment load factor is not positive")
    contact_ownership = {row["name"]: row for row in model["contact_cell_ownership"]}
    connections = []
    for name, row in sorted(increment["physical_connection_forces"].items()):
        if host not in (row["first"], row["second"]):
            continue
        side = "first" if row["first"] == host else "second"
        patch = contact_patch_for_row(name, row, contact_ownership, contact_geometry, frame)
        action = point_action(name, row, host, side, frame, patch)
        connections.append(action)
    tangents = []
    for row in increment["exact_floor_tangent_reactions"]:
        if host not in (row["first"], row["second"]):
            continue
        side = "first" if row["first"] == host else "second"
        tangents.append(point_action(row["source_row_id"], row, host, side, frame, None, "floor_tangent"))
    loads = []
    for node_text, force_value in sorted(model["physical_body_loads"][host].items(), key=lambda item: int(item[0])):
        node = int(node_text)
        point = vec(model["nodes"][str(node)], f"{host} node {node} coordinate")
        force = scale(vec(force_value, f"{host} node {node} discrete body load"), load_factor)
        s = station(frame, point)
        loads.append({
            "action_id": f"body_load:{host}:{node}",
            "source_name": f"body_load_node_{node}",
            "source_row_ids": [f"body_load_node_{node}"],
            "source_kind": "discrete_body_or_gravity_load",
            "role": "model.physical_body_loads",
            "body": host,
            "other_body": None,
            "point_xyz_mm": point,
            "force_xyz_n": force,
            "force_rounding_radius_xyz_n": [0.0, 0.0, 0.0],
            "grain_station_mm": s,
            "finite_footprint_station_bounds_mm": [s, s],
            "source_area_mm2": None,
            "contact_patch": None,
            "load_factor_applied": load_factor,
        })
    seen = [action["action_id"] for action in connections + tangents + loads]
    require(len(seen) == len(set(seen)), f"duplicate host point action identity for {host}")
    return connections + tangents + loads, connections + tangents, loads


def source_station_inventory(
    model: dict[str, Any],
    increment: dict[str, Any],
    host: str,
    frame: dict[str, Any],
    contact_geometry: dict[str, Any],
) -> dict[str, Any]:
    connections = []
    for row in sorted(model["connection_attachment_rows"], key=lambda item: str(item.get("lateral_spring_name", item.get("axis_id", "")))):
        if host not in (row["first"], row["second"]):
            continue
        # Attachment records identify axes; response records below provide all force stations.
        connections.append({
            "axis_id": row.get("axis_id"),
            "kind": row.get("kind"),
            "first": row["first"],
            "second": row["second"],
            "point_xyz_mm": vec(row["point_xyz_mm"], f"{host} attachment point"),
            "grain_station_mm": station(frame, vec(row["point_xyz_mm"], f"{host} attachment point")),
            "lateral_spring_name": row.get("lateral_spring_name"),
        })
    all_actions, response_connections, _ = host_actions_for_state(model, increment, host, frame, contact_geometry)
    response_rows = [
        {
            "action_id": row["action_id"],
            "source_name": row["source_name"],
            "source_row_ids": row["source_row_ids"],
            "source_kind": row["source_kind"],
            "role": row["role"],
            "other_body": row["other_body"],
            "point_xyz_mm": row["point_xyz_mm"],
            "grain_station_mm": row["grain_station_mm"],
            "finite_footprint_station_bounds_mm": row["finite_footprint_station_bounds_mm"],
            "source_patch_index": row["contact_patch"]["source_patch_index"] if row["contact_patch"] else None,
            "source_patch_area_mm2": row["contact_patch"]["source_patch_area_mm2"] if row["contact_patch"] else None,
        }
        for row in response_connections
    ]
    loads = [
        {
            "source_name": row["source_name"],
            "point_xyz_mm": row["point_xyz_mm"],
            "grain_station_mm": row["grain_station_mm"],
            "load_factor_applied": row["load_factor_applied"],
        }
        for row in all_actions
        if row["source_kind"] == "discrete_body_or_gravity_load"
    ]
    return {
        "host_connection_attachment_axes": connections,
        "all_host_source_connection_point_station_rows_at_reference_increment": response_rows,
        "host_discrete_body_load_node_stations": loads,
        "reference_load_factor_for_discrete_load_scaling": finite(increment["load_factor"], f"{host} inventory load factor"),
        "station_inventory_scope": "every incident physical connection point, exact floor tangent point, finite source contact-patch station bound where applicable, and every discrete body/gravity-load node; force changes by state but source point geometry is fixed",
    }


def target_group_actions(
    connections: list[dict[str, Any]], host: str, block: str
) -> list[dict[str, Any]]:
    rows = [row for row in connections if row["other_body"] == block]
    roles = {}
    for row in rows:
        roles[row["role"]] = roles.get(row["role"], 0) + 1
    require(roles == {
        "candidate_bolt_lateral_plane": 2,
        "physical_bolt_outer_seat_tension": 2,
        "timber_or_panel_contact": 4,
    }, f"{host} to {block} source connection ownership changed: {roles}")
    return rows


def verify_station_geometry_reproduced(
    actions: list[dict[str, Any]], inventory: dict[str, Any], host: str
) -> bool:
    expected_connections = {
        row["action_id"]: row
        for row in inventory["all_host_source_connection_point_station_rows_at_reference_increment"]
    }
    current_connections = {
        row["action_id"]: row for row in actions if row["source_kind"] != "discrete_body_or_gravity_load"
    }
    require(set(current_connections) == set(expected_connections), f"{host} incident connection action identities changed from reference station inventory")
    for action_id, row in current_connections.items():
        expected = expected_connections[action_id]
        close_vector(row["point_xyz_mm"], expected["point_xyz_mm"], 1e-8, f"{host} source point changed for {action_id}")
        require(abs(row["grain_station_mm"] - expected["grain_station_mm"]) <= 1e-8, f"{host} grain station changed for {action_id}")
        close_vector(row["finite_footprint_station_bounds_mm"], expected["finite_footprint_station_bounds_mm"], 1e-8, f"{host} finite footprint bounds changed for {action_id}")
    expected_loads = {row["source_name"]: row for row in inventory["host_discrete_body_load_node_stations"]}
    current_loads = {
        row["source_name"]: row for row in actions if row["source_kind"] == "discrete_body_or_gravity_load"
    }
    require(set(current_loads) == set(expected_loads), f"{host} discrete load node identities changed from reference station inventory")
    for source_name, row in current_loads.items():
        expected = expected_loads[source_name]
        close_vector(row["point_xyz_mm"], expected["point_xyz_mm"], 1e-8, f"{host} discrete load point changed for {source_name}")
        require(abs(row["grain_station_mm"] - expected["grain_station_mm"]) <= 1e-8, f"{host} discrete load station changed for {source_name}")
    return True


def bracket_plan(
    frame: dict[str, Any], target_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    lower = min(row["finite_footprint_station_bounds_mm"][0] for row in target_rows)
    upper = max(row["finite_footprint_station_bounds_mm"][1] for row in target_rows)
    length = frame["member_grain_length_mm"]
    require(lower >= -STATION_BAND_MM and upper <= length + STATION_BAND_MM, "target finite footprint extends beyond the host grain extent")
    low = max(0.0, lower - BRACKET_CLEARANCE_MM)
    high = min(length, upper + BRACKET_CLEARANCE_MM)
    require(low < high, "invalid or zero-length host bracket")
    group_points_inside = all(low - STATION_BAND_MM <= row["grain_station_mm"] <= high + STATION_BAND_MM for row in target_rows)
    group_footprints_inside = all(
        low - STATION_BAND_MM <= row["finite_footprint_station_bounds_mm"][0]
        and row["finite_footprint_station_bounds_mm"][1] <= high + STATION_BAND_MM
        for row in target_rows
    )
    require(group_points_inside and group_footprints_inside, "bracket cuts do not include every target point and finite contact footprint")
    return {
        "target_finite_group_station_bounds_mm": [lower, upper],
        "cut_before_group_station_mm": low,
        "cut_after_group_station_mm": high,
        "clearance_before_mm": lower - low,
        "clearance_after_mm": high - upper,
        "before_cut_at_host_terminal_boundary": abs(low) <= STATION_BAND_MM,
        "after_cut_at_host_terminal_boundary": abs(high - length) <= STATION_BAND_MM,
        "target_point_actions_all_between_cuts": group_points_inside,
        "target_finite_contact_footprints_all_between_or_touching_cuts": group_footprints_inside,
        "station_resolution_band_mm": STATION_BAND_MM,
        "host_bracket_limit": "A cut at a terminal host boundary is inclusive only when the frozen source contact-polygon projection proves the target footprint touches that boundary; it is not a strict exterior clearance.",
    }


def side_actions(
    actions: list[dict[str, Any]], cut_s: float, trace: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    require(trace in ("approached_from_negative_station", "approached_from_positive_station"), "unknown cut trace")
    positive, negative = [], []
    for action in actions:
        distance = action["grain_station_mm"] - cut_s
        on_plane = abs(distance) <= STATION_BAND_MM
        positive_side = distance > STATION_BAND_MM or (
            on_plane and trace == "approached_from_negative_station"
        )
        (positive if positive_side else negative).append(action)
    return positive, negative


def cut_trace(
    actions: list[dict[str, Any]],
    cut_s: float,
    frame: dict[str, Any],
    trace: str,
    all_body_external: dict[str, list[float]],
) -> dict[str, Any]:
    datum = add(frame["member_start_xyz_mm"], scale(frame["grain_axis_global_xyz"], cut_s))
    positive, negative = side_actions(actions, cut_s, trace)
    positive_ext = wrench(positive, datum)
    negative_ext = wrench(negative, datum)
    positive_cut = negated_wrench(positive_ext)
    negative_cut = negated_wrench(negative_ext)
    closure_force = add(positive_ext["force_xyz_n"], negative_ext["force_xyz_n"])
    closure_moment = add(positive_ext["moment_about_datum_xyz_nmm"], negative_ext["moment_about_datum_xyz_nmm"])
    closure_force_radius = add(positive_ext["force_rounding_radius_xyz_n"], negative_ext["force_rounding_radius_xyz_n"])
    closure_moment_radius = add(positive_ext["moment_rounding_radius_xyz_nmm"], negative_ext["moment_rounding_radius_xyz_nmm"])
    all_at_cut = transport_wrench(all_body_external, all_body_external["_datum_xyz_mm"], datum)
    close_vector(closure_force, all_at_cut["force_xyz_n"], 1e-7, "one-sided host force closure does not reproduce whole-body force")
    close_vector(closure_moment, all_at_cut["moment_about_datum_xyz_nmm"], 1e-6, "one-sided host moment closure does not reproduce whole-body moment")
    on_plane_connection = [a["source_name"] for a in actions if a["source_kind"] != "discrete_body_or_gravity_load" and abs(a["grain_station_mm"] - cut_s) <= STATION_BAND_MM]
    on_plane_loads = [a["source_name"] for a in actions if a["source_kind"] == "discrete_body_or_gravity_load" and abs(a["grain_station_mm"] - cut_s) <= STATION_BAND_MM]
    return {
        "cut_station_mm": cut_s,
        "cut_plane_origin_xyz_mm": datum,
        "section_plane_normal_global_xyz": frame["grain_axis_global_xyz"],
        "trace": trace,
        "on_plane_action_assignment": "positive-side external set" if trace == "approached_from_negative_station" else "negative-side external set",
        "source_actions_on_positive_station_side": [a["source_name"] for a in positive],
        "source_actions_on_negative_station_side": [a["source_name"] for a in negative],
        "body_load_nodes_on_positive_station_side": [a["source_name"] for a in positive if a["source_kind"] == "discrete_body_or_gravity_load"],
        "body_load_nodes_on_negative_station_side": [a["source_name"] for a in negative if a["source_kind"] == "discrete_body_or_gravity_load"],
        "positive_side_external_wrench_at_cut": positive_ext,
        "negative_side_external_wrench_at_cut": negative_ext,
        "internal_cut_wrench_on_positive_side_material": positive_cut,
        "internal_cut_wrench_on_negative_side_material": negative_cut,
        "internal_cut_wrench_on_positive_side_local": local_wrench(positive_cut, frame),
        "internal_cut_wrench_on_negative_side_local": local_wrench(negative_cut, frame),
        "two_side_external_closure_at_cut": {
            "force_residual_xyz_n": closure_force,
            "force_rounding_radius_xyz_n": closure_force_radius,
            "force_interval_distance_from_zero_n": [interval_distance(x, r) for x, r in zip(closure_force, closure_force_radius, strict=True)],
            "moment_residual_xyz_nmm": closure_moment,
            "moment_rounding_radius_xyz_nmm": closure_moment_radius,
            "moment_interval_distance_from_zero_nmm": [interval_distance(x, r) for x, r in zip(closure_moment, closure_moment_radius, strict=True)],
            "whole_host_residual_reproduced_at_cut": True,
        },
        "source_actions_on_plane": on_plane_connection,
        "discrete_load_nodes_on_plane": on_plane_loads,
        "force_radius_interval_contains_zero_on_both_half_body_closure": all(interval_distance(x, r) == 0 for x, r in zip(closure_force, closure_force_radius, strict=True)),
        "moment_radius_interval_contains_zero_on_both_half_body_closure": all(interval_distance(x, r) == 0 for x, r in zip(closure_moment, closure_moment_radius, strict=True)),
    }


def group_jump(
    all_actions: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    bracket: dict[str, Any],
    frame: dict[str, Any],
    lower_trace: dict[str, Any],
    upper_trace: dict[str, Any],
) -> dict[str, Any]:
    low_positive, _ = side_actions(all_actions, bracket["cut_before_group_station_mm"], "approached_from_negative_station")
    high_positive, _ = side_actions(all_actions, bracket["cut_after_group_station_mm"], "approached_from_positive_station")
    high_ids = {action["action_id"] for action in high_positive}
    interval_actions = [action for action in low_positive if action["action_id"] not in high_ids]
    target_ids = {action["action_id"] for action in target_rows}
    target_interval = [action for action in interval_actions if action["action_id"] in target_ids]
    competing_connections = [action for action in interval_actions if action["source_kind"] != "discrete_body_or_gravity_load" and action["action_id"] not in target_ids]
    interval_loads = [action for action in interval_actions if action["source_kind"] == "discrete_body_or_gravity_load"]
    low_datum = lower_trace["cut_plane_origin_xyz_mm"]
    high_datum = upper_trace["cut_plane_origin_xyz_mm"]
    common_datum = add(frame["member_start_xyz_mm"], scale(frame["grain_axis_global_xyz"], 0.5 * (bracket["cut_before_group_station_mm"] + bracket["cut_after_group_station_mm"])))
    interval_wrenches = {
        "target_group_point_actions": wrench(target_interval, common_datum),
        "competing_connection_and_support_actions": wrench(competing_connections, common_datum),
        "discrete_body_or_gravity_loads": wrench(interval_loads, common_datum),
        "all_actions_in_bracket_interval": wrench(interval_actions, common_datum),
    }
    low_positive_internal = lower_trace["internal_cut_wrench_on_positive_side_material"]
    high_positive_internal = upper_trace["internal_cut_wrench_on_positive_side_material"]
    low_at_common = transport_wrench(low_positive_internal, low_datum, common_datum)
    high_at_common = transport_wrench(high_positive_internal, high_datum, common_datum)
    jump_force = sub(high_at_common["force_xyz_n"], low_at_common["force_xyz_n"])
    jump_moment = sub(high_at_common["moment_about_datum_xyz_nmm"], low_at_common["moment_about_datum_xyz_nmm"])
    expected = interval_wrenches["all_actions_in_bracket_interval"]
    close_vector(jump_force, expected["force_xyz_n"], 1e-7, "positive-side internal force jump does not equal in-zone source actions")
    close_vector(jump_moment, expected["moment_about_datum_xyz_nmm"], 1e-5, "positive-side internal moment jump does not equal in-zone source actions")
    return {
        "common_datum_xyz_mm": common_datum,
        "interval_source_ownership": {
            "target_group_source_names": [action["source_name"] for action in target_interval],
            "competing_connection_source_names": [action["source_name"] for action in competing_connections],
            "discrete_body_or_gravity_load_node_names": [action["source_name"] for action in interval_loads],
            "target_group_source_count": len(target_interval),
            "competing_connection_source_count": len(competing_connections),
            "body_or_gravity_load_node_count": len(interval_loads),
            "all_point_action_identities_preserved": len(interval_actions) == len({action["action_id"] for action in interval_actions}),
        },
        "interval_wrenches_at_common_datum": interval_wrenches,
        "positive_side_internal_wrench_jump_at_common_datum": {
            "force_xyz_n": jump_force,
            "moment_about_datum_xyz_nmm": jump_moment,
            "matches_target_plus_competing_sources_and_body_loads": True,
        },
        "negative_side_internal_wrench_jump_equals_negative_interval_external_wrench": True,
        "cut_datum_transport_applied": True,
    }


def target_geometry_axes(upper: dict[str, Any], host: str, block: str) -> list[dict[str, Any]]:
    records = []
    for axis_id, record in sorted(upper["geometry_by_axis"].items()):
        if record.get("host") != host or record.get("block") != block:
            continue
        records.append({
            "axis_id": axis_id,
            "block": block,
            "host": host,
            "head_to_nut_axis_global_xyz": vec(record["head_to_nut_axis_xyz"], f"{axis_id} hardware axis"),
            "lateral_plane_xyz_mm": vec(record["lateral_plane_xyz_mm"], f"{axis_id} lateral plane"),
            "host_step_path": record["members"]["host"]["finished_step"],
            "host_step_sha256": record["members"]["host"]["finished_step_sha256"],
        })
    require(len(records) == 2, f"{host} to {block} must have two target fastener axes")
    return records


def host_balance(
    model: dict[str, Any],
    increment: dict[str, Any],
    audit_increment: dict[str, Any],
    host: str,
    all_actions: list[dict[str, Any]],
) -> dict[str, Any]:
    require(host in increment["physical_balance"]["body_equilibrium"], f"response has no all-body balance for {host}")
    response_balance = increment["physical_balance"]["body_equilibrium"][host]
    audit_balance = audit_increment["body_equilibrium"][host]
    datum = vec(audit_balance["reference_xyz_mm"], f"{host} audit datum")
    computed = wrench(all_actions, datum)
    for key, result_key in (
        ("force_residual_xyz_n", "force_xyz_n"),
        ("moment_residual_xyz_nmm", "moment_about_datum_xyz_nmm"),
        ("force_rounding_radius_xyz_n", "force_rounding_radius_xyz_n"),
        ("moment_rounding_radius_xyz_nmm", "moment_rounding_radius_xyz_nmm"),
    ):
        close_vector(computed[result_key], vec(response_balance[key], f"{host} response {key}"), 2e-8 if "force" in key else 2e-7, f"{host} action sum differs from response all-body {key}")
        close_vector(computed[result_key], vec(audit_balance[key], f"{host} audit {key}"), 2e-8 if "force" in key else 2e-7, f"{host} action sum differs from frozen all-body audit {key}")
    require(response_balance["printed_resultants_passed"] is True and response_balance["interval_resultants_passed"] is True, f"{host} source response body closure gate failed")
    require(audit_balance["printed_resultants_passed"] is True and audit_balance["interval_resultants_passed"] is True, f"{host} independent body audit gate failed")
    return {
        "host": host,
        "source_connection_action_count_including_floor_normal": sum(action["source_kind"] == "physical_connection" for action in all_actions),
        "source_floor_tangent_action_count": sum(action["source_kind"] == "floor_tangent" for action in all_actions),
        "discrete_body_or_gravity_load_node_count": sum(action["source_kind"] == "discrete_body_or_gravity_load" for action in all_actions),
        "datum_xyz_mm": datum,
        "point_action_external_residual_force_xyz_n": computed["force_xyz_n"],
        "point_action_external_residual_moment_xyz_nmm": computed["moment_about_datum_xyz_nmm"],
        "propagated_force_rounding_radius_xyz_n": computed["force_rounding_radius_xyz_n"],
        "propagated_moment_rounding_radius_xyz_nmm": computed["moment_rounding_radius_xyz_nmm"],
        "force_interval_distance_from_zero_n": [interval_distance(x, r) for x, r in zip(computed["force_xyz_n"], computed["force_rounding_radius_xyz_n"], strict=True)],
        "moment_interval_distance_from_zero_nmm": [interval_distance(x, r) for x, r in zip(computed["moment_about_datum_xyz_nmm"], computed["moment_rounding_radius_xyz_nmm"], strict=True)],
        "independent_frozen_all_body_audit_reproduced": True,
        "response_and_audit_limits": "The frozen 0.1 N / 2 N mm whole-body bookkeeping gates apply to extraction closure only.",
        "_external_wrench": {**computed, "_datum_xyz_mm": datum},
    }


def coverage_for_cut(
    all_actions: list[dict[str, Any]], cut_s: float, trace: str
) -> dict[str, Any]:
    positive, negative = side_actions(all_actions, cut_s, trace)
    return {
        "positive_side_connection_names": [a["source_name"] for a in positive if a["source_kind"] != "discrete_body_or_gravity_load"],
        "negative_side_connection_names": [a["source_name"] for a in negative if a["source_kind"] != "discrete_body_or_gravity_load"],
        "positive_side_body_load_node_names": [a["source_name"] for a in positive if a["source_kind"] == "discrete_body_or_gravity_load"],
        "negative_side_body_load_node_names": [a["source_name"] for a in negative if a["source_kind"] == "discrete_body_or_gravity_load"],
    }


def group_point_records(target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_name": row["source_name"],
            "source_row_ids": row["source_row_ids"],
            "role": row["role"],
            "point_xyz_mm": row["point_xyz_mm"],
            "grain_station_mm": row["grain_station_mm"],
            "force_on_host_xyz_n": row["force_xyz_n"],
            "force_rounding_radius_xyz_n": row["force_rounding_radius_xyz_n"],
            "finite_footprint_station_bounds_mm": row["finite_footprint_station_bounds_mm"],
            "source_patch_index": row["contact_patch"]["source_patch_index"] if row["contact_patch"] else None,
            "source_patch_area_mm2": row["contact_patch"]["source_patch_area_mm2"] if row["contact_patch"] else None,
        }
        for row in target_rows
    ]


def candidate_loaded_edge(
    group_wrench: dict[str, list[float]],
    frame: dict[str, Any],
    geometry: dict[str, Any],
    axes: list[dict[str, Any]],
    candidate_local_axis: str,
    local_axis_sign_for_positive_crossgrain: float,
) -> dict[str, Any]:
    component_name = ("+" if local_axis_sign_for_positive_crossgrain > 0 else "−") + ("Vu" if candidate_local_axis == "u" else "Vv")
    global_axis = frame[f"section_{candidate_local_axis}_global_xyz"]
    force_component = local_axis_sign_for_positive_crossgrain * dot(group_wrench["force_xyz_n"], global_axis)
    radius_component = abs(local_axis_sign_for_positive_crossgrain) * dot(group_wrench["force_rounding_radius_xyz_n"], [abs(x) for x in global_axis])
    side = "positive" if force_component > radius_component else "negative" if force_component < -radius_component else "unresolved_within_rounding_interval"
    coordinate = candidate_local_axis
    if side == "positive":
        boundary_is_maximum = local_axis_sign_for_positive_crossgrain > 0
        boundary_name = f"{coordinate}_{'maximum' if boundary_is_maximum else 'minimum'}"
        boundary = geometry["section_local_bounds_mm"][coordinate][1 if boundary_is_maximum else 0]
        bolt_projections = [dot(sub(axis["lateral_plane_xyz_mm"], geometry["plane_origin_xyz_mm"]), global_axis) for axis in axes]
        farthest = min(bolt_projections) if boundary_is_maximum else max(bolt_projections)
        he = boundary - farthest if boundary_is_maximum else farthest - boundary
        loaded_boundary_coord = boundary
    elif side == "negative":
        boundary_is_maximum = local_axis_sign_for_positive_crossgrain < 0
        boundary_name = f"{coordinate}_{'maximum' if boundary_is_maximum else 'minimum'}"
        boundary = geometry["section_local_bounds_mm"][coordinate][1 if boundary_is_maximum else 0]
        bolt_projections = [dot(sub(axis["lateral_plane_xyz_mm"], geometry["plane_origin_xyz_mm"]), global_axis) for axis in axes]
        farthest = min(bolt_projections) if boundary_is_maximum else max(bolt_projections)
        he = boundary - farthest if boundary_is_maximum else farthest - boundary
        loaded_boundary_coord = boundary
    else:
        boundary_name = None
        bolt_projections = [dot(sub(axis["lateral_plane_xyz_mm"], geometry["plane_origin_xyz_mm"]), global_axis) for axis in axes]
        farthest, he, loaded_boundary_coord = None, None, None
    return {
        "candidate_local_transverse_component": component_name,
        "source_model_section_axis": global_axis,
        "candidate_positive_crossgrain_global_axis": scale(global_axis, local_axis_sign_for_positive_crossgrain),
        "signed_group_force_component_on_host_n": force_component,
        "group_force_component_rounding_radius_n": radius_component,
        "loaded_boundary_sign_candidate": side,
        "candidate_boundary_name": boundary_name,
        "candidate_boundary_local_coordinate_mm": loaded_boundary_coord,
        "target_fastener_local_coordinates_mm": bolt_projections,
        "farthest_target_fastener_coordinate_mm": farthest,
        "candidate_edge_to_farthest_fastener_distance_mm": he,
        "status": "geometric signed-boundary candidate only; no Figure-plane, h_e, or resistance adoption",
    }


def interface_result(
    upper: dict[str, Any],
    host: str,
    block: str,
    frame: dict[str, Any],
    all_actions: list[dict[str, Any]],
    connection_actions: list[dict[str, Any]],
    balance: dict[str, Any],
    cad_sections: dict[str, Any],
) -> dict[str, Any]:
    target_rows = target_group_actions(connection_actions, host, block)
    contact_rows = [row for row in target_rows if row["contact_patch"] is not None]
    require(len(contact_rows) == 4, f"{host} to {block} must retain four contact-cell actions")
    patch_indices = {row["contact_patch"]["source_patch_index"] for row in contact_rows}
    require(len(patch_indices) == 1, f"{host} to {block} contact cells do not share one frozen source patch")
    patch_area = contact_rows[0]["contact_patch"]["source_patch_area_mm2"]
    cell_area = math.fsum(row["contact_patch"]["contact_cell_area_mm2"] for row in contact_rows)
    require(abs(cell_area - patch_area) <= 1e-6, f"{host} to {block} contact-cell areas do not cover their frozen source patch area")
    patch_station_bounds = contact_rows[0]["contact_patch"]["finite_patch_station_bounds_mm"]
    require(
        all(row["contact_patch"]["finite_patch_station_bounds_mm"] == patch_station_bounds for row in contact_rows),
        f"{host} to {block} contact-cell footprints refer to inconsistent source patch bounds",
    )
    bracket = bracket_plan(frame, target_rows)
    low_s, high_s = bracket["cut_before_group_station_mm"], bracket["cut_after_group_station_mm"]
    target_datum = add(frame["member_start_xyz_mm"], scale(frame["grain_axis_global_xyz"], 0.5 * (bracket["target_finite_group_station_bounds_mm"][0] + bracket["target_finite_group_station_bounds_mm"][1])))
    group_wrench = wrench(target_rows, target_datum)
    host_external = balance["_external_wrench"]
    low_negative = cut_trace(all_actions, low_s, frame, "approached_from_negative_station", host_external)
    low_positive = cut_trace(all_actions, low_s, frame, "approached_from_positive_station", host_external)
    high_negative = cut_trace(all_actions, high_s, frame, "approached_from_negative_station", host_external)
    high_positive = cut_trace(all_actions, high_s, frame, "approached_from_positive_station", host_external)
    # Bracket jump uses the traces immediately outside the interval: low's negative approach
    # puts an on-plane point into the positive half; high's positive approach puts it in negative.
    jump = group_jump(all_actions, target_rows, bracket, frame, low_negative, high_positive)
    selected_axis = "v"
    positive_crossgrain_local_sign = 1.0 if host == "base_rail_top" else -1.0
    edge_candidate = candidate_loaded_edge(
        group_wrench,
        frame,
        cad_sections["before"],
        target_geometry_axes(upper, host, block),
        selected_axis,
        positive_crossgrain_local_sign,
    )
    low_cut_geom = cad_sections["before"]
    high_cut_geom = cad_sections["after"]
    require(low_cut_geom["station_mm"] == low_s and high_cut_geom["station_mm"] == high_s, f"{host} CAD section stations do not match point-action bracket")
    return {
        "interface_id": f"{host}<-{block}",
        "host": host,
        "receiving_cleat": block,
        "target_group_definition": "all incident host-to-cleat lateral bolt planes, receiver-specific outer-seat bolt ties, and the four finite contact-cell point actions belonging to the frozen source contact patch",
        "target_fastener_axes": target_geometry_axes(upper, host, block),
        "frame": {key: frame[key] for key in ("grain_axis_global_xyz", "section_u_global_xyz", "section_v_global_xyz", "section_u_source_label", "section_v_source_label")},
        "bracket": bracket,
        "finite_target_contact_footprints": [
            {
                "source_patch_index": row["contact_patch"]["source_patch_index"],
                "member_pair": row["contact_patch"]["source_patch_member_pair"],
                "area_mm2": row["contact_patch"]["source_patch_area_mm2"],
                "cell_area_mm2": row["contact_patch"]["contact_cell_area_mm2"],
                "cell_center_station_mm": row["contact_patch"]["contact_cell_centroid_station_mm"],
                "projected_polygon_station_bounds_mm": row["contact_patch"]["finite_patch_station_bounds_mm"],
                "polygon_vertex_count": row["contact_patch"]["finite_patch_vertex_count"],
                "footprint_method": row["contact_patch"]["footprint_method"],
            }
            for row in target_rows if row["contact_patch"] is not None
        ],
        "finite_contact_patch_coverage": {
            "source_patch_index": next(iter(patch_indices)),
            "source_patch_area_mm2": patch_area,
            "four_contact_cell_areas_sum_mm2": cell_area,
            "cell_area_minus_source_patch_area_mm2": cell_area - patch_area,
            "cell_area_covers_frozen_source_patch": True,
            "footprint_bounds_are_from_source_polygon_vertices": True,
        },
        "target_source_point_actions_on_host": group_point_records(target_rows),
        "target_group_point_wrench_at_group_datum": {
            "datum_xyz_mm": target_datum,
            "global_wrench": group_wrench,
            "local_components": local_wrench(group_wrench, frame),
            "source_point_model_only": True,
        },
        "cut_sections": {
            "before_group": {
                "station_mm": low_s,
                "finished_step_section": low_cut_geom,
                "approached_from_negative_station": low_negative,
                "approached_from_positive_station": low_positive,
            },
            "after_group": {
                "station_mm": high_s,
                "finished_step_section": high_cut_geom,
                "approached_from_negative_station": high_negative,
                "approached_from_positive_station": high_positive,
            },
        },
        "candidate_shear_reporting": {
            "local_signed_shears_at_each_cut_and_half_body_are_in_cut_sections": True,
            "uv_transverse_norm_is_diagnostic_only": True,
            "candidate_fig8_projection_component": "Vv" if host == "base_rail_top" else "-Vv",
            "candidate_fig8_projection_source_axis": scale(frame[f"section_{selected_axis}_global_xyz"], positive_crossgrain_local_sign),
            "candidate_fig8_projection_status": "signed projection onto the candidate cross-grain source axis exposed for later Figure-plane mapping; no EC5 Fv,Ed assigned",
            "candidate_transverse_loaded_edge": edge_candidate,
            "other_transverse_component_and_all_N/T/M_components_retained": True,
        },
        "bracket_interval_source_identity": jump,
        "source_coverage_at_each_cut": {
            "before_group_approached_from_negative_station": coverage_for_cut(all_actions, low_s, "approached_from_negative_station"),
            "after_group_approached_from_positive_station": coverage_for_cut(all_actions, high_s, "approached_from_positive_station"),
            "point_actions_are_selected_by_their_receiver_specific_source_point": True,
            "finite_contact_patch_extent_is_reported_separately_from_cell_centers": True,
        },
        "actual_finished_section_traction_established": False,
        "interface_capacity_or_acceptance_established": False,
    }


def query_step_section(root: Path, frame: dict[str, Any], station_mm: float) -> dict[str, Any]:
    try:
        import cadquery as cq
        import OCP
    except ImportError as exc:
        raise SourceRefusal(f"CadQuery/OCP is needed for the already-frozen STEP section query: {exc}") from exc
    step_path = root / frame["step_path"]
    require(sha256_file(step_path) == frame["step_sha256"], f"host STEP source changed: {frame['step_path']}")
    shape = cq.importers.importStep(str(step_path)).val()
    origin = add(frame["member_start_xyz_mm"], scale(frame["grain_axis_global_xyz"], station_mm))
    span = max(shape.BoundingBox().xlen, shape.BoundingBox().ylen, shape.BoundingBox().zlen) * 4.0 + 1000.0
    cutter = cq.Face.makePlane(span, span, basePnt=origin, dir=frame["grain_axis_global_xyz"])
    split = shape.split(cutter)
    cut_faces = []
    for face in split.Faces():
        if face.geomType() != "PLANE":
            continue
        # A planar face that cannot be queried is a failed section extraction;
        # do not silently drop it from the net section sum.
        normal = vec(face.normalAt().toTuple(), "OCC planar face normal")
        center = vec(face.Center().toTuple(), "OCC planar face center")
        plane_distance = abs(dot(sub(center, origin), frame["grain_axis_global_xyz"]))
        if abs(abs(dot(normal, frame["grain_axis_global_xyz"])) - 1.0) > 1e-7 or plane_distance > 1e-5:
            continue
        area = finite(face.Area(), "OCC cut-face area")
        vertices = [vec(vertex.toTuple(), "OCC cut-face vertex") for vertex in face.Vertices()]
        require(bool(vertices), "OCC section face has no boundary vertices")
        u_values = [dot(sub(vertex, origin), frame["section_u_global_xyz"]) for vertex in vertices]
        v_values = [dot(sub(vertex, origin), frame["section_v_global_xyz"]) for vertex in vertices]
        cut_faces.append({
            "area_mm2": area,
            "center_xyz_mm": center,
            "normal_global_xyz": normal,
            "wire_count": len(face.Wires()),
            "vertex_count": len(vertices),
            "local_u_bounds_mm": [min(u_values), max(u_values)],
            "local_v_bounds_mm": [min(v_values), max(v_values)],
        })
    require(bool(cut_faces), f"OCC found no finished STEP section face for {frame['host']} at s={station_mm}")
    area_sum = math.fsum(face["area_mm2"] for face in cut_faces)
    all_u = [bound for face in cut_faces for bound in face["local_u_bounds_mm"]]
    all_v = [bound for face in cut_faces for bound in face["local_v_bounds_mm"]]
    return {
        "station_mm": station_mm,
        "plane_origin_xyz_mm": origin,
        "section_plane_normal_global_xyz": frame["grain_axis_global_xyz"],
        "step_path": frame["step_path"],
        "step_sha256": frame["step_sha256"],
        "kernel": {"cadquery": cq.__version__, "ocp": getattr(OCP, "__version__", "unknown")},
        "section_area_mm2_from_saved_finished_step": area_sum,
        "distinct_planar_component_face_count": len(cut_faces),
        "cut_face_wire_count": sum(face["wire_count"] for face in cut_faces),
        "component_faces": cut_faces,
        "section_local_bounds_mm": {"u": [min(all_u), max(all_u)], "v": [min(all_v), max(all_v)]},
        "source_geometry_status": "read-only query of the hash-pinned saved STEP BRep; no reframe or regeneration",
        "not_established": ["finished wood section in any built member", "cut or bore inspection", "section traction", "capacity"],
    }


def model_and_response(root: Path, case: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    sources = CASES[case]
    model = read_json(root / sources["model"])
    response = read_json(root / sources["response"])
    audit = read_json(root / sources["all_body_audit"])
    require(model["candidate"] == CANDIDATE and model["geometry_revision_id"] == REVISION, f"{case} model identity changed")
    require(response["candidate"] == CANDIDATE and response["geometry_revision_id"] == REVISION, f"{case} response identity changed")
    require(audit["source_model_sha256"] == sources["sha256"]["model"], f"{case} audit model pin mismatch")
    require(audit["source_response_sha256"] == sources["sha256"]["response"], f"{case} audit response pin mismatch")
    require(len(response["increments"]) == len(audit["increments"]) == len(LOAD_FACTORS), f"{case} must retain seven response/audit increments")
    for host in HOSTS:
        relative = f"{STEP_ROOT}/{host}.step"
        require(model["source_geometry_hashes"].get(relative) == PINNED_SHA256[relative], f"{case} model does not pin {host} STEP")
        require(model["body_geometry"][host]["geometry_record"]["geometry_diagnostics"]["geometry_sha256"] == PINNED_SHA256[relative], f"{case} host diagnostic STEP hash mismatch for {host}")
    require(model["geometry_source_documents"]["contact-geometry.json"]["path"] == CONTACT_GEOMETRY, f"{case} contact geometry path mismatch")
    require(model["geometry_source_documents"]["contact-geometry.json"]["sha256"] == PINNED_SHA256[CONTACT_GEOMETRY], f"{case} contact geometry hash mismatch")
    return model, response, audit


def build_report(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    pins = verify_pins(root)
    upper, contact_geometry = source_documents(root)
    source_objects = {case: model_and_response(root, case) for case in CASES}
    baseline_model = source_objects["a1-rear"][0]
    frames = {host: frame_for_host(baseline_model, host) for host in HOSTS}
    baseline_increment = source_objects["a1-rear"][1]["increments"][-1]

    host_static = {}
    for host, frame in frames.items():
        host_static[host] = {
            **frame,
            "source_station_inventory": source_station_inventory(
                baseline_model, baseline_increment, host, frame, contact_geometry
            ),
            "finished_step_bracket_sections": {},
        }

    # Build group footprints and their inclusive cuts once from frozen source geometry.
    bracket_plans = {}
    for host, blocks in HOSTS.items():
        frame = frames[host]
        # Use final A1 response only to obtain a representative same-geometry station set.
        model, response, _ = source_objects["a1-rear"]
        _actions, connections, _ = host_actions_for_state(model, response["increments"][-1], host, frame, contact_geometry)
        for block in blocks:
            target = target_group_actions(connections, host, block)
            plan = bracket_plan(frame, target)
            bracket_plans[(host, block)] = plan
            host_static[host]["finished_step_bracket_sections"][block] = {
                "before": query_step_section(root, frame, plan["cut_before_group_station_mm"]),
                "after": query_step_section(root, frame, plan["cut_after_group_station_mm"]),
            }

    states = []
    all_interface_records = 0
    all_host_records = 0
    for case in CASES:
        model, response, audit = source_objects[case]
        for index, (increment, audit_increment) in enumerate(zip(response["increments"], audit["increments"], strict=True)):
            require(abs(finite(increment["load_factor"], f"{case} load factor") - LOAD_FACTORS[index]) <= 1e-12, f"{case} load-factor sequence changed")
            require(audit_increment["passed"] is True, f"{case} all-body audit increment {index} failed")
            for gate in (
                "mpc_interval_checks_passed",
                "retained_bilateral_checks_passed",
                "springa_law_checks_passed",
                "selected_floor_complementarity_passed",
                "inactive_floor_tangent_no_restraint_or_reaction_passed",
                "raw_balance_passed",
                "rounding_interval_balance_passed",
            ):
                require(increment.get(gate) is True, f"{case} increment {index} source gate failed: {gate}")
            host_contexts = {}
            station_geometry_checks = {}
            for host, frame in frames.items():
                all_actions, connections, loads = host_actions_for_state(model, increment, host, frame, contact_geometry)
                station_geometry_checks[host] = verify_station_geometry_reproduced(
                    all_actions, host_static[host]["source_station_inventory"], host
                )
                balance = host_balance(model, increment, audit_increment, host, all_actions)
                host_contexts[host] = (all_actions, connections, loads, balance)
            interface_records = []
            for host, blocks in HOSTS.items():
                all_actions, connections, _, balance = host_contexts[host]
                for block in blocks:
                    cad = host_static[host]["finished_step_bracket_sections"][block]
                    result = interface_result(upper, host, block, frames[host], all_actions, connections, balance, cad)
                    result["case"] = case
                    result["increment_index"] = index
                    result["load_factor"] = increment["load_factor"]
                    interface_records.append(result)
                    all_interface_records += 1
            host_balance_records = {}
            for host, (_, _, _, balance) in host_contexts.items():
                public_balance = {key: value for key, value in balance.items() if not key.startswith("_")}
                host_balance_records[host] = public_balance
                all_host_records += 1
            states.append({
                "case": case,
                "increment_index": index,
                "load_factor": increment["load_factor"],
                "whole_host_point_action_balances": host_balance_records,
                "source_point_station_geometry_matches_reference_inventory": station_geometry_checks,
                "interfaces": interface_records,
            })

    report = {
        "schema": "upper-outer-host-point-actions/v1",
        "status": "conditional point-action host section extraction; no EC5 Fv,Ed, design capacity, or acceptance",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "source_pins": pins,
        "method": {
            "host_balance": "sum every physical connection action incident on the host, both receiver-specific points for seat ties, all exact floor tangent reactions when incident, and every discrete physical_body_load node; compare force/moment residuals and propagated RF intervals with the independent frozen all-body audit",
            "cut_equilibrium": "one-sided external point-action wrenches on each host half-body are balanced by their corresponding internal section action; station ties use two explicit one-sided traces",
            "target_group": "two lateral bolt-plane rows, two receiver-specific outer-seat ties, and four point forces representing four quadrature cells of the frozen finite contact patch",
            "finite_contact_footprint": "all frozen contact-patch polygon vertices are projected on the exact model grain axis; the resulting station bounds, not only cell centers, set the bracket cuts",
            "section_components": "N = F·g, Vu = F·section_u, Vv = F·section_v; T = M·g, Mu = M·section_u, Mv = M·section_v. Exact model basis and signs are retained.",
            "source_method_boundary": "CEN/AC and JRC Figure 8.1 inform what a later splitting demand needs; these response states are conditional model actions, not design actions. No Fv,Ed scalar or capacity is adopted here.",
        },
        "counts": {
            "hosts": len(HOSTS),
            "interfaces": 4,
            "cases": len(CASES),
            "increments_per_case": len(LOAD_FACTORS),
            "same_state_interface_records": all_interface_records,
            "whole_host_balance_records": all_host_records,
            "target_group_point_action_rows_per_interface_state": 8,
            "target_group_point_action_rows_total": all_interface_records * 8,
        },
        "claim_boundary": {
            "source_response_is_conditional": True,
            "point_action_model_only": True,
            "actual_finished_host_traction_established": False,
            "EC5_Fv_Ed_assigned": False,
            "design_conversion_or_resistance_calculated": False,
            "complete_joint_acceptance_established": False,
            "six_case_envelope_established": False,
            "native_solve_executed": False,
            "geometry_modified_or_regenerated": False,
        },
        "host_geometry_and_source_station_inventories": host_static,
        "states": states,
    }
    return report, {"schema": "upper-outer-host-source-pins/v1", "sources": pins}


def write(root: Path = ROOT) -> None:
    report, _ = build_report(root)
    (root / OUTPUT.relative_to(ROOT)).write_bytes(canonical_json(report))


def verify(root: Path = ROOT) -> None:
    expected, _ = build_report(root)
    path = root / OUTPUT.relative_to(ROOT)
    require(path.is_file(), "ignored host-actions.json is missing; run --write")
    actual_bytes = path.read_bytes()
    expected_bytes = canonical_json(expected)
    require(actual_bytes == expected_bytes, "host-actions.json differs from canonical pinned replay")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true", help="write ignored host-actions.json")
    modes.add_argument("--verify", action="store_true", help="rebuild and require byte-identical host-actions.json")
    args = parser.parse_args()
    if args.write:
        write()
        print(f"wrote {OUTPUT}")
    else:
        verify()
        print(f"verified {OUTPUT}")


if __name__ == "__main__":
    main()
