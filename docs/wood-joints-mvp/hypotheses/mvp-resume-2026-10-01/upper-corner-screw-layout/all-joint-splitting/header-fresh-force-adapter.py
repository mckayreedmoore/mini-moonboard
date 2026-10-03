"""Adapt fresh six-case member actions to header cleat boundary fields and v cuts.

This producer binds the fresh 104-row global connector response with the
unadopted 108-inventory planning gravity source. It reuses saved finished
geometry and existing boundary/field integration methods, but never reads the
historical header force, mass, or cut-result payloads.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import platform
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
UPPER = HERE.parent
RESUME = UPPER.parent
ROOT = next(path for path in HERE.parents if (path / "current-candidate.json").is_file())
RAW = HERE / "rawlocal/header-fresh-force-adapter"
FRESH = RESUME / "member-screen-attempt02/knee-bridge-gravity01"
GRAVITY = UPPER / "rawlocal/knee-bridge-gravity/attempt01"
FRAME = UPPER / "rawlocal/knee-bridge-frame/attempt02"
CONTRACT = UPPER / "rawlocal/header-local-transfer/attempt01"
ALL_JOINT_README = HERE / "README.md"
MEMBER_METHOD = UPPER / "knee-bridge-remaining-sections.py"
HEADER_METHOD = HERE / "header-boundary.py"
VCUT_METHOD = HERE / "header-v-cuts.py"
HEADER_GEOMETRY = UPPER / "header-traction-map.py"
BORE_METHOD = UPPER / "corner-bore-wall.py"
TILE_METHOD = UPPER / "top-host-physical-actions.py"
WRENCH_METHOD = UPPER / "header-net-section.py"
NORMAL_METHOD = UPPER / "corner-split-closure.py"
ORIENTATION_METHOD = UPPER / "member-opening-remainder.py"
PROJECTION_BASE = UPPER.parent.parent / "mvp-acceleration-2026-09-28"
PROJECTION_CONTRACT = PROJECTION_BASE / "current-frame-physical-connector-projection-contract-attempt01/projection-contract.json"
PROJECTION_INPUTS = PROJECTION_BASE / "current-frame-connector-compliance-attempt04/inputs.json"

CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
BODIES = (
    "center_post_cleat_left",
    "center_post_cleat_right",
    "center_principal_cleat_left",
    "center_principal_cleat_right",
    "knee_outer_left_inner_frame_block",
    "knee_outer_right_inner_frame_block",
)
WASHER_INNER_RADIUS_MM = 4.1529
WASHER_OUTER_RADIUS_MM = 9.2329
POINT_TOL_MM = 1e-6
FORCE_TOL_N = 1e-7
MOMENT_TOL_NMM = 1e-5

PINS = {
    FRESH / "member-results.json": "5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0",
    FRESH / "action-section-arrays.npz": "3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596",
    FRESH / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    FRESH / "inputs.json": "34219c91e8b23588f76f4e2e2b6c564b25e1b979ccd4106dd0002c9f03cc0457",
    GRAVITY / "operator-assessment.json": "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    GRAVITY / "receipt.json": "315c16d2a592b12dcd0160af47f9d4bababb6afaf54c6c74ddcbd41e01d45b6c",
    FRAME / "response/comparison.json": "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    FRAME / "response/response.npz": "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    FRAME / "receipt.json": "6acb01eb1b07dc9f9175cb3a0e916fe74a9a32a7b90941cf3b18e84a24d9c599",
    CONTRACT / "model.json": "eae4fc005cdd079f90f527be611e45a137aa275b129e16eebf964c422d69ae52",
    CONTRACT / "receipt.json": "3b3afc6924dee426c4f0073077e119d906efddcb5ed03a683ec4a3f16fc189a8",
    ALL_JOINT_README: "e474d0668d9962e4504c8dce0d37a8da05440f01921e8d641b612469194e4056",
    MEMBER_METHOD: "e2a08ca075fdb397696889d22d8cbbfb30d83a3d4bb5e3af1726574c38ca2e15",
    HEADER_METHOD: "5108639d6a1afa955f4f0a1db44aa10e194ad93d24b525011bb13b09b887d43c",
    VCUT_METHOD: "6614559cf623c643818cb66eca39324b04ee775165d6c1c695034c62f9e17537",
    HEADER_GEOMETRY: "87bd3b14e6961b95e04788d89ece412334ff5cc5f4ad735433a8ced97472d34d",
    BORE_METHOD: "0ad9c88be2496f1b2ae9b06cb31f0cb7d9d95a236ffb4b2dc586873b7cf4a185",
    TILE_METHOD: "0f005656656d26d1003c3ff4317c696172f2399de438c287ff9a8ea12e926b49",
    WRENCH_METHOD: "d413a2ae912df6bf56086ad6ddda59526db32cc6325f1b4bf2b71f984d86a328",
    NORMAL_METHOD: "e090270a3bea195800ed3b04b806fe4ea0c5e221ae57faf01f602c8dba769d5e",
    ORIENTATION_METHOD: "5db858b30a69f393f46b493bc06c46ca2b786e85ed4ac520475d29cf51b25e62",
    PROJECTION_CONTRACT: "4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3",
    PROJECTION_INPUTS: "3d17f953df265035e95fdb3543e19eb0f7505d81778067f28783e4bb9b0b3208",
    UPPER / "header-traction-map.md": "d1a1f1af6036551b420ef8c52f01887184d4e43f730483dde290a6258c823a76",
}

FLOOR_ORIENTATION_FAMILY = "conditional_floor_tangent_constraint"

FLAGS = {
    "formal_qualification": False,
    "new_resistance_established": False,
    "splitting_qualified": False,
    "complete_joint_acceptance": False,
    "physical_release": False,
    "fabrication_release": False,
    "proposal_108_adopted": False,
    "fully_coupled_108_axis_response": False,
    "historical_104_force_or_cut_result_transferred": False,
    "native_mechanics_or_cad_executed": False,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def line(stream: Any, value: Any) -> None:
    stream.write(json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n")


def key(path: Path) -> str:
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def authenticate(pins: dict[Path, str]) -> None:
    for path, expected in pins.items():
        require(path.is_file(), f"missing pinned source: {path}")
        require(sha(path) == expected, f"changed pinned source: {path}")


def module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"helper unavailable: {path}")
    value = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(value)
    finally:
        sys.dont_write_bytecode = previous
    return value


def vector(value: Any, shape: tuple[int, ...] = (3,)) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    require(result.shape == shape and np.isfinite(result).all(), "invalid saved vector")
    return result


def max_abs(value: Any) -> float:
    array = np.asarray(value, dtype=float)
    return float(np.max(np.abs(array))) if array.size else 0.0


def check_wrench(actual: Any, expected: Any, label: str) -> list[float]:
    delta = vector(actual, (6,)) - vector(expected, (6,))
    require(max_abs(delta[:3]) < FORCE_TOL_N and max_abs(delta[3:]) < MOMENT_TOL_NMM,
            f"{label}: {delta.tolist()}")
    return delta.tolist()


def floor_orientation_scope(orientation: Any, pins: dict[Path, str],
                            rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Bind saved floor-row signs and prove target rows do not use that adapter."""
    source_api = SimpleNamespace(read=read, GRAVITY=GRAVITY)
    source_map = orientation.floor_direction_metadata(source_api, pins)
    require(len(rows) == 1888 and all(row.get("row") == index
                                      for index, row in enumerate(rows)),
            "fresh gravity row identity index differs")
    floor_rows = {row["row"] for row in rows
                  if row.get("family") == FLOOR_ORIENTATION_FAMILY}
    mappings = source_map["mappings"]
    mapped_rows = {mapping["row"] for mapping in mappings}
    sign_counts = Counter(mapping["source_owner_point_rigid_row_sign"]
                          for mapping in mappings)
    require(source_map["row_count"] == 200 and len(floor_rows) == 200
            and mapped_rows == floor_rows and sign_counts == {-1: 200},
            "saved floor orientation contract census differs")

    target_census = []
    for body in BODIES:
        incident = [row for row in rows
                    if body in (row["ownership"]["first_body"],
                                row["ownership"]["second_body"])]
        floor_incident = [row for row in incident
                          if row.get("family") == FLOOR_ORIENTATION_FAMILY]
        require(not floor_incident,
                f"header target unexpectedly uses floor orientation rows: {body}")
        family_counts = Counter(row["family"] for row in incident)
        require(len(incident) == 20 and family_counts == {
            "bilateral_spring2": 8, "unilateral_springa": 12,
        }, f"header target incident row census differs: {body}")
        target_census.append({
            "body": body,
            "incident_mechanical_row_count": len(incident),
            "incident_family_counts": dict(sorted(family_counts.items())),
            "incident_floor_orientation_row_count": 0,
            "incident_row_ids": [row["row_id"] for row in incident],
        })
    return {
        "schema": "fresh_header_floor_orientation_scope/v1",
        "resolver_sha256": pins[ORIENTATION_METHOD],
        "projection_contract_sha256": pins[PROJECTION_CONTRACT],
        "projection_inputs_sha256": pins[PROJECTION_INPUTS],
        "resolved_source_family": FLOOR_ORIENTATION_FAMILY,
        "resolved_source_row_count": len(mappings),
        "saved_owner_point_rigid_row_sign_counts": {str(k): v for k, v in sorted(sign_counts.items())},
        "target_rows_modified": False,
        "target_incident_row_census": target_census,
    }


def fresh_context(pins: dict[Path, str]) -> tuple[dict[str, Any], ...]:
    fresh = read(FRESH / "member-results.json")
    inputs = read(FRESH / "inputs.json")
    geometry = read(FRESH / "geometry.json")
    assessment = read(GRAVITY / "operator-assessment.json")
    gravity_receipt = read(GRAVITY / "receipt.json")
    comparison = read(FRAME / "response/comparison.json")
    frame_receipt = read(FRAME / "receipt.json")
    static_geometry = read(CONTRACT / "model.json")
    geometry_receipt = read(CONTRACT / "receipt.json")

    require(fresh["status"] == "COMPLETE_CONDITIONAL_ELEMENTARY_MEMBER_SCREENS_NOT_QUALIFICATION",
            "fresh member archive status differs")
    require(inputs["source_sha256"] == fresh["source_sha256"], "fresh member receipt source differs")
    for name in ("geometry.json", "action-section-arrays.npz", "inputs.json"):
        require(fresh["output_sha256"][name] == pins[FRESH / name], f"fresh member output binding differs: {name}")
    for path in (FRAME / "response/comparison.json", FRAME / "response/response.npz",
                 GRAVITY / "operator-assessment.json"):
        require(fresh["source_sha256"][key(path)] == pins[path], f"fresh member source binding differs: {key(path)}")
    require(tuple(case["case_id"] for case in fresh["cases"]) == CASES
            and tuple(inputs["selected_force_keys"]) == tuple(case + "_gap_raw_force_n" for case in CASES),
            "fresh six-case/member force-key order differs")
    require(fresh["counts"]["timber_members"] == 44
            and fresh["counts"]["whole_member_balances"] == 264,
            "fresh member archive coverage differs")

    for path, output_name in (
        (GRAVITY / "model.json", "model.json"),
        (GRAVITY / "row-identities.json", "row-identities.json"),
        (GRAVITY / "operators.npz", "operators.npz"),
    ):
        digest = assessment["output_sha256"][output_name]
        require(gravity_receipt["output_sha256"][output_name] == digest and sha(path) == digest,
                f"fresh planning-gravity output receipt differs: {output_name}")
        pins[path] = digest
    require(assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS"
            and assessment["operator_ready"] is True
            and assessment["proposal_adopted"] is False,
            "fresh 108-planning-mass gravity assessment differs")
    require(assessment["authority_changed"] is False
            and assessment["current_global_operator_files_changed"] is False
            and assessment["new_internal_bolt_stiffness_rows_added"] is False,
            "fresh source no longer separates 104 global rows from internal ties")
    require(comparison["schema"] == "coupled_two_receiver_frame_clearance/v1"
            and comparison["modeled_mass_kg"] == assessment["modeled_mass_kg"]
            and comparison["response_sha256"] == pins[FRAME / "response/response.npz"],
            "fresh frame/gravity source binding differs")
    nominal = [state for state in comparison["states"] if state["gap_scale"] == 1.0]
    require(tuple(state["case_id"] for state in nominal) == CASES,
            "fresh nominal frame cases differ")
    require(frame_receipt["output_sha256"]["response/comparison.json"] == pins[FRAME / "response/comparison.json"]
            and frame_receipt["output_sha256"]["response/response.npz"] == pins[FRAME / "response/response.npz"],
            "fresh frame output receipt differs")

    require(geometry_receipt["output_sha256"]["model.json"] == pins[CONTRACT / "model.json"],
            "static finished-geometry receipt differs")
    require(static_geometry["schema"] == "header_local_transfer_frozen_geometry/v1",
            "static header geometry schema differs")
    require(len(static_geometry["header_connections"]) == 12,
            "static header bolt geometry no longer covers the twelve selected 104 axes")
    require(tuple(fresh["source_force_state_scope"]["bounded_nominal_cases"]) == CASES,
            "fresh source force scope differs")
    require(assessment["modeled_mass_kg"] == comparison["modeled_mass_kg"],
            "fresh planning inventory mass differs between gravity/frame sources")

    for body in BODIES:
        member = geometry["members"][body]
        saved = static_geometry["bodies"][body]["member_geometry"]
        require(member["current_finished_step_sha256"] == saved["current_finished_step_sha256"]
                and member["geometry"] == saved["geometry"],
                f"finished target body changed: {body}")
        surface = static_geometry["bodies"][body]["finished_surface_record"]
        require(surface["step_binding"]["file_sha256"] == member["current_finished_step_sha256"],
                f"finished target surface binding changed: {body}")
        pins[ROOT / member["current_finished_step"]] = member["current_finished_step_sha256"]
    header = static_geometry["bodies"]["base_header"]["member_geometry"]
    fresh_header = geometry["members"]["base_header"]
    require(fresh_header["current_finished_step_sha256"] == header["current_finished_step_sha256"]
            and fresh_header["geometry"] == header["geometry"],
            "finished header host identity changed")
    require(static_geometry["bodies"]["base_header"]["finished_surface_record"]["step_binding"]["file_sha256"]
            == fresh_header["current_finished_step_sha256"], "finished header surface binding changed")
    pins[ROOT / fresh_header["current_finished_step"]] = fresh_header["current_finished_step_sha256"]
    authenticate(pins)
    return fresh, inputs, geometry, assessment, comparison, static_geometry


def event_add(events: dict[float, set[str]], value: float, reason: str,
              low: float, high: float) -> None:
    if math.isfinite(value) and low + POINT_TOL_MM < value < high - POINT_TOL_MM:
        events.setdefault(float(value), set()).add(reason)


def field_v_events(field: dict[str, Any], own: dict[str, Any], events: dict[float, set[str]],
                   low: float, high: float) -> None:
    frame_v = own["frame"][2]
    start = own["start"]
    kind = field["field_kind"]
    if kind == "uniform_compressive_pressure_on_supported_annulus":
        domain = field["domain"]
        center_v = float((vector(domain["plane_point_xyz_mm"]) - start) @ frame_v)
        basis = [vector(domain[name]) for name in ("basis_u_xyz", "basis_v_xyz")]
        reach = float(domain["outer_radius_mm"]) * math.hypot(*(axis @ frame_v for axis in basis))
        for station in (center_v - reach, center_v, center_v + reach):
            event_add(events, station, "washer_annulus_projection", low, high)
    elif kind == "uniform_frictionless_normal_pressure_on_saved_trimmed_cell":
        trimmed = field["domain"]["trimmed_domain"]
        for index, corner in enumerate(trimmed["cell_rectangle_member_guv_corners_mm"]):
            event_add(events, float(corner[2]), f"contact_cell_corner_{index}", low, high)
        for index, circle in enumerate(trimmed["excluded_circles_patch_uv"]):
            center = vector(circle["center_xyz_mm"])
            center_v = float((center - start) @ frame_v)
            radius = float(circle["radius_mm"])
            event_add(events, center_v - radius, f"contact_void_{index}_lower", low, high)
            event_add(events, center_v, f"contact_void_{index}_center", low, high)
            event_add(events, center_v + radius, f"contact_void_{index}_upper", low, high)
    elif kind == "nonnegative_half_cosine_radial_bore_pressure":
        profile = field["profile"]
        axis_point = vector(profile["axis_point_xyz_mm"])
        basis = [vector(row) for row in profile["pressure_basis_e_h_xyz"]]
        radius = float(profile["radius_mm"])
        center_v = float((axis_point - start) @ frame_v)
        reach = radius * math.hypot(*(float(axis @ frame_v) for axis in basis))
        event_add(events, center_v - reach, "bore_pressure_tangency_lower", low, high)
        event_add(events, center_v, "bore_pressure_axis", low, high)
        event_add(events, center_v + reach, "bore_pressure_tangency_upper", low, high)
    else:
        raise ValueError(f"unsupported fresh header field kind: {kind}")


def map_header_action(body: str, action: dict[str, Any], static_model: dict[str, Any],
                      map_helper: Any, boundary: Any, bore_helper: Any,
                      contact_groups: dict[int, list[dict[str, Any]]], datum: np.ndarray) -> dict[str, Any]:
    connections = {
        connection["axis_id"]: connection for connection in static_model["header_connections"]
    }
    role = action["role"]
    if role == "physical_bolt_outer_seat_tension":
        axis_id = action["source_id"].split("/")[0]
        connection = connections[axis_id]
        body_cells = [cell for cell in static_model["contact_cells"].values()
                      if body in (cell["first"], cell["second"]) and "base_header" in
                      (cell["first"], cell["second"])]
        patch_ids = {int(cell["source_patch_index"]) for cell in body_cells}
        require(len(patch_ids) == 1, f"fresh header washer/contact patch identity differs: {body}")
        patch = static_model["contact_patches_by_global_source_index"][str(next(iter(patch_ids)))]
        return boundary.map_axial_seat(
            body, action, connection, static_model["bodies"][body]["member_geometry"]["geometry"],
            static_model["bodies"][body]["finished_surface_record"], patch,
            WASHER_INNER_RADIUS_MM, WASHER_OUTER_RADIUS_MM, datum,
        )
    if role == "timber_or_panel_contact":
        cell = static_model["contact_cells"][action["source_id"]]
        patch = static_model["contact_patches_by_global_source_index"][str(cell["source_patch_index"])]
        group = contact_groups[int(cell["source_patch_index"])]
        return boundary.map_contact_cell(
            body, action, cell, patch,
            static_model["bodies"][body]["member_geometry"]["geometry"],
            map_helper, group, datum,
        )
    if role == "candidate_bolt_lateral_plane":
        axis_id = action["source_id"].split("/")[0]
        return boundary.map_lateral_bore(
            body, action, connections[axis_id],
            static_model["bodies"][body]["member_geometry"]["geometry"],
            static_model["bodies"][body], datum, bore_helper,
        )
    return {
        "source_action": action,
        "field_kind": "unsupported_header_interface_role",
        "field_status": "UNSUPPORTED_ACTION_ROLE",
        "boundary_fields": [],
        "mapped_wrench_xyz_n_nmm": [0.0] * 6,
        "source_wrench_xyz_n_nmm": boundary.wrench([action], datum).tolist(),
        "source_to_field_wrench_residual_xyz_n_nmm": boundary.wrench([action], datum).tolist(),
        "unmapped_source_free_moment_nmm": action["free_moment_nmm"],
        "unmapped_source_force_xyz_n": action["force_n"],
    }


def build(output: str | Path) -> dict[str, Any]:
    """Parent API: write one authenticated fresh-force child under RAW."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(),
            "use a new immediate child of the owned ignored raw folder")
    producer = Path(__file__).resolve()
    pins = {**PINS, producer: sha(producer)}
    authenticate(pins)
    fresh, _inputs, fresh_geometry, assessment, comparison, static_model = fresh_context(pins)
    gravity_model = read(GRAVITY / "model.json")
    rows = read(GRAVITY / "row-identities.json")
    require(static_model["source_identity"]["candidate"] == "compact-floor-flush-wood-joints-development",
            "static header geometry candidate differs")

    orientation = module(ORIENTATION_METHOD, "fresh_header_orientation_contract")
    orientation_scope = floor_orientation_scope(orientation, pins, rows)
    fresh_method = module(MEMBER_METHOD, "fresh_header_action_method")
    boundary = module(HEADER_METHOD, "fresh_header_boundary_methods")
    vcuts = module(VCUT_METHOD, "fresh_header_vcut_methods")
    map_helper = module(HEADER_GEOMETRY, "fresh_header_contact_geometry")
    bore_helper = module(BORE_METHOD, "fresh_header_bore_integrals")
    tile_helper = module(TILE_METHOD, "fresh_header_contact_integrals")
    wrench_helper = module(WRENCH_METHOD, "fresh_header_wrench_method")
    normal_helper = module(NORMAL_METHOD, "fresh_header_normal_hull_method")

    connections = {entry["axis_id"]: entry for entry in static_model["header_connections"]}
    contact_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for cell in static_model["contact_cells"].values():
        if "base_header" in (cell["first"], cell["second"]):
            for body in BODIES:
                if body in (cell["first"], cell["second"]):
                    contact_groups[int(cell["source_patch_index"])].append(cell)
                    break

    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(producer.read_bytes())
    fresh_states: list[dict[str, Any]] = []
    boundary_rows = 0
    unsupported_rows: list[dict[str, Any]] = []
    total_cut_states = 0

    with np.load(FRESH / "action-section-arrays.npz", allow_pickle=False) as arrays, \
         np.load(FRAME / "response/response.npz", allow_pickle=False) as response, \
         np.load(GRAVITY / "operators.npz", allow_pickle=False) as operators, \
         gzip.open(output / "fresh-header-actions.jsonl.gz", "wt", encoding="utf-8") as action_stream, \
         gzip.open(output / "fresh-v-cuts.jsonl.gz", "wt", encoding="utf-8") as cut_stream:
        D, W = operators["D"], operators["W"]
        require(D.shape == (len(rows), 6 * len(gravity_model["body_names"]))
                and W.shape == (6 * len(gravity_model["body_names"]), 12)
                and np.isfinite(D).all() and np.isfinite(W).all(),
                "fresh operator dimensions or values differ")
        disk_helper = tile_helper

        for case in fresh["cases"]:
            case_id = case["case_id"]
            for body in BODIES:
                member = fresh_geometry["members"][body]
                source, actions, _fresh_grain_cuts, source_audit = fresh_method.actions_for(
                    case, body, member, arrays, response, D, W,
                    gravity_model, rows, wrench_helper,
                )
                floor_action_rows = [
                    int(action["row"]) for action in actions
                    if int(action["row"]) >= 0
                    and rows[int(action["row"])].get("family") == FLOOR_ORIENTATION_FAMILY
                ]
                require(not floor_action_rows,
                        f"header source actions unexpectedly use floor orientation rows: {body}/{case_id}")
                own = {
                    "frame": np.asarray([member["geometry"][name]
                                         for name in ("axis", "section_u", "section_v")], dtype=float),
                    "start": vector(member["geometry"]["start"]),
                }
                datum = own["start"]
                fresh_header_actions = [
                    action for action in actions
                    if action["other_body"] == "base_header"
                    and action["role"] in (
                        "physical_bolt_outer_seat_tension",
                        "timber_or_panel_contact",
                        "candidate_bolt_lateral_plane",
                    )
                ]
                axis_ids = {
                    axis_id for axis_id, connection in connections.items()
                    if set(connection["receiver_member_ids"]) == {"base_header", body}
                }
                require(len(axis_ids) == 2 and len(fresh_header_actions) == 10,
                        f"fresh six-case header interface source count differs: {body}/{case_id}")
                require({action["source_id"].split("/")[0] for action in fresh_header_actions
                         if action["role"] != "timber_or_panel_contact"} == axis_ids,
                        f"fresh header axis identity differs: {body}/{case_id}")

                recoveries: dict[int, dict[str, Any]] = {}
                action_results = []
                for action in fresh_header_actions:
                    mapped = map_header_action(
                        body, action, static_model, map_helper, boundary,
                        bore_helper, contact_groups, datum,
                    )
                    recovery = vcuts.action_recovery(
                        mapped, own, datum, disk_helper, tile_helper, bore_helper,
                    )
                    recoveries[int(action["point_index"])] = recovery
                    action_results.append({"source_id": action["source_id"], "role": action["role"],
                                           "field_status": mapped["field_status"], "mapped": mapped,
                                           "recovery": recovery})
                    boundary_rows += 1
                    if recovery["unsupported_field_reason"] is not None:
                        unsupported_rows.append({
                            "body": body, "case_id": case_id,
                            "source_id": action["source_id"], "role": action["role"],
                            "status": recovery["field_recovery_status"],
                            "reason": recovery["unsupported_field_reason"],
                            "force_n": action["force_n"],
                            "free_moment_nmm": action["free_moment_nmm"],
                        })

                source_full_local = sum(
                    (vcuts.local_point_wrench(action, own) for action in actions), np.zeros(6)
                )
                mixed_full_local = np.zeros(6)
                for action in actions:
                    recovery = recoveries.get(int(action["point_index"]))
                    if recovery is None:
                        mixed_full_local += vcuts.local_point_wrench(action, own)
                    else:
                        mixed_full_local += vector(
                            recovery["mixed_full_wrench_local_about_body_start_n_nmm"], (6,)
                        )
                whole_body_delta = check_wrench(
                    mixed_full_local, source_full_local,
                    f"fresh full-body header boundary restoration {body}/{case_id}",
                )

                interface_source = sum(
                    (vcuts.local_point_wrench(action, own) for action in fresh_header_actions), np.zeros(6)
                )
                interface_mapped = sum(
                    (vector(recovery["mixed_full_wrench_local_about_body_start_n_nmm"], (6,))
                     for recovery in recoveries.values()), np.zeros(6)
                )
                interface_delta = check_wrench(
                    interface_mapped, interface_source,
                    f"fresh header interface wrench restoration {body}/{case_id}",
                )

                # New v stations come from fresh point loads and mapped field geometry.
                geometry = member["geometry"]
                depth = float(geometry["depth_mm"])
                low, high = -depth / 2.0, depth / 2.0
                events: dict[float, set[str]] = {}
                for action in actions:
                    local = (vector(action["point_mm"]) - own["start"]) @ own["frame"].T
                    event_add(events, float(local[2]), f"fresh_point:{action['source_id']}", low, high)
                for recovery in recoveries.values():
                    for field in recovery["fields"]:
                        field_v_events(field, own, events, low, high)
                stations: dict[float, set[str]] = {}
                for station, reasons in sorted(events.items()):
                    existing = next((prior for prior in stations if abs(prior - station) <= POINT_TOL_MM), None)
                    if existing is None:
                        stations[station] = set(reasons)
                    else:
                        stations[existing].update(reasons)

                for station, reasons in sorted(stations.items()):
                    for limit in ("before", "after"):
                        source_cut = sum(
                            (vcuts.local_point_wrench(action, own, station, limit) for action in actions),
                            np.zeros(6),
                        )
                        mapped_cut = np.zeros(6)
                        for action in actions:
                            recovery = recoveries.get(int(action["point_index"]))
                            if recovery is None:
                                mapped_cut += vcuts.local_point_wrench(action, own, station, limit)
                            else:
                                mapped_cut += vcuts.field_cut_local(
                                    recovery, own, station, disk_helper, tile_helper, bore_helper,
                                )
                                mapped_cut += vcuts.local_point_wrench(
                                    recovery["residual_point"], own, station, limit,
                                )
                        source_internal = vcuts.signed_q(-source_cut)
                        mapped_internal = vcuts.signed_q(-mapped_cut)
                        delta = (vector(mapped_internal, (6,))
                                 - vector(source_internal, (6,))).tolist()
                        grain_length = float(np.dot(
                            vector(geometry["end"]) - own["start"], own["frame"][0]
                        ))
                        hull = [[0.0, grain_length],
                                [-float(geometry["width_mm"]) / 2.0,
                                 float(geometry["width_mm"]) / 2.0]]
                        source_normal = normal_helper.normal_bound(source_internal.tolist(), hull)
                        mapped_normal = normal_helper.normal_bound(mapped_internal.tolist(), hull)
                        line(cut_stream, {
                            "schema": "fresh_header_v_cut/v1", "body": body, "case_id": case_id,
                            "axis": 2, "axis_name": "v", "station_mm": station, "limit": limit,
                            "station_event_sources": sorted(reasons),
                            "fresh_source_point_signed_internal_n_nmm": source_internal.tolist(),
                            "mapped_full_cut_signed_internal_n_nmm": mapped_internal.tolist(),
                            "mapped_minus_source_signed_internal_n_nmm": delta,
                            "partial_cut_delta_role": "signed_load_distribution_diagnostic",
                            "partial_cut_equality_enforced": False,
                            "source_normal_hull_diagnostic": source_normal,
                            "mapped_normal_hull_diagnostic": mapped_normal,
                            "pressure_or_tie_capacity_assigned": False,
                            "source_force_basis": "fresh_104_global_connector_rows_with_108_planning_mass",
                        })
                        total_cut_states += 1

                line(action_stream, {
                    "schema": "fresh_header_action_state/v1", "body": body, "case_id": case_id,
                    "source_force_key": case["source_force_key"],
                    "source_array_prefix": source["array_prefix"],
                    "fresh_source_action_count": len(actions),
                    "header_interface_action_count": len(fresh_header_actions),
                    "fresh_source_audit": source_audit,
                    "fresh_source_point_actions": actions,
                    "header_boundary_action_results": action_results,
                    "fresh_source_full_body_wrench_local_n_nmm": source_full_local.tolist(),
                    "mapped_fields_plus_exact_point_residual_full_body_wrench_local_n_nmm": mixed_full_local.tolist(),
                    "full_body_accounting_delta_n_nmm": whole_body_delta,
                    "fresh_header_interface_wrench_local_n_nmm": interface_source.tolist(),
                    "mapped_header_interface_wrench_local_n_nmm": interface_mapped.tolist(),
                    "header_interface_accounting_delta_n_nmm": interface_delta,
                    "complete_body_physical_boundary_recovered": False,
                    "other_interfaces_and_fresh_discrete_body_loads_remain_at_source_points": True,
                })
                fresh_states.append({
                    "body": body, "case_id": case_id,
                    "fresh_action_count": len(actions),
                    "header_boundary_action_count": len(fresh_header_actions),
                    "v_station_count": len(stations),
                    "v_cut_limit_count": 2 * len(stations),
                    "fresh_source_action_audit_passed": True,
                    "floor_orientation_source_action_count": 0,
                    "whole_body_boundary_accounting_passed": True,
                    "header_interface_accounting_passed": True,
                })

    require(len(fresh_states) == len(BODIES) * len(CASES), "fresh six-body/six-case output census differs")
    require(total_cut_states > 0, "fresh v cut catalog is empty")
    authenticate(pins)
    source_hashes = {key(path): digest for path, digest in sorted(pins.items())}
    result = {
        "schema": "fresh_header_cleat_force_adapter/v1",
        "status": "COMPLETE_FRESH_SOURCE_ADAPTATION_WITH_UNQUALIFIED_HEADER_BOUNDARY",
        "case_ids": list(CASES), "six_target_bodies": list(BODIES),
        "source_authority": {
            "reviewed_104_axis_history": "Preserved; referenced only as authority context.",
            "fresh_global_connector_axis_count": 104,
            "proposal_inventory_axis_count": 108,
            "proposal_adopted": False,
            "fresh_gravity_mass_basis": "108 planning inventory mass in updated gravity operators; not old 104 mass.",
            "force_basis": "104 global connector rows evaluated with the updated planning gravity source.",
            "four_internal_v_ties": {
                "count": 4,
                "global_connector_rows": 0,
                "force_and_couple_recovered": False,
                "qualified_by_this_adapter": False,
                "reason": "They remain separate static proposal allocations and have no global connector response rows.",
            },
            "floor_orientation_contract": orientation_scope,
        },
        "fresh_state_count": len(fresh_states), "fresh_boundary_action_count": boundary_rows,
        "fresh_v_cut_limit_count": total_cut_states,
        "fresh_states": fresh_states,
        "unsupported_physical_rows": unsupported_rows,
        "unsupported_physical_row_count": len(unsupported_rows),
        "source_sha256": source_hashes,
        "source_roles": {
            "fresh_member_actions_gravity_and_case_results": [key(FRESH / name) for name in (
                "member-results.json", "action-section-arrays.npz", "geometry.json", "inputs.json")],
            "fresh_global_frame_response": [key(FRAME / name) for name in (
                "response/comparison.json", "response/response.npz")],
            "fresh_planning_mass_operator": [key(GRAVITY / name) for name in (
                "operator-assessment.json", "model.json", "row-identities.json", "operators.npz")],
            "saved_floor_orientation_authority": [
                key(ORIENTATION_METHOD), key(PROJECTION_CONTRACT), key(PROJECTION_INPUTS),
            ],
            "historical_header_contract": "finished geometry and interface feature identities only; no historical actions, gravity, wrenches, cut results, or demand peaks consumed",
        },
        "methods": {
            "fresh_action_restoration": "knee-bridge-remaining-sections.actions_for",
            "floor_orientation_scope": "member-opening-remainder.floor_direction_metadata; original source signs authenticated, target rows unchanged",
            "boundary_mapping": "header-boundary.map_axial_seat/map_contact_cell/map_lateral_bore",
            "field_cut_integration": "header-v-cuts.field_global_wrench/contact integrals/action recovery",
            "normal_diagnostic": "corner-split-closure.normal_bound; diagnostic only",
        },
        "wrench_accounting_scope": {
            "per_action": "header-v-cuts.action_recovery closes each full source six-wrench with its field and exact point residual",
            "interface_and_body": "full integrated interface and body six-wrenches use the retained check_wrench tolerances",
            "partial_v_cuts": "source and mapped signed six-wrenches and their delta are retained as diagnostics; equality is not required for different spatial load distributions",
            "partial_cut_coupon_executed": False,
        },
        "limits": [
            "The 108 inventory is a planning-mass basis for gravity; this is not a fully coupled 108-axis response.",
            "Four proposed internal V ties have no global connector rows; their forces, couples and tie duties remain unrecovered and unqualified.",
            "Only six fresh nominal cases and six header-related cleats are included. Other joint duties remain outside this adapter.",
            "Annular washer pressure, trimmed frictionless contact pressure, and lateral bore pressure retain their saved placement assumptions; no compatibility or pressure peak is established.",
            "Source free couples and all unmapped force components remain at their original application points in the recovery records.",
            "The v catalog uses fresh action coordinates and current finished boundary-field geometry. It is a finite event catalog, not a continuous-station maximum.",
            "Normal-hull outputs are diagnostics only; shear, shear and torque remain unresolved and no splitting or tie capacity is assigned.",
        ],
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        **FLAGS,
    }
    write(output / "checks.json", result)
    write(output / "sources.json", {
        "source_sha256": source_hashes,
        "fresh_force_state_scope": fresh["source_force_state_scope"],
        "fresh_frame_assumptions": fresh["source_frame_assumptions"],
        "fresh_member_method_limits": fresh["method_limits"],
        "gravity_status": assessment["status"],
        "frame_source_schema": comparison["schema"],
        "historical_geometry_role": "geometry only",
        "historical_force_wrench_mass_cut_role": "not consumed",
        "floor_orientation_scope": orientation_scope,
        "four_internal_v_ties": result["source_authority"]["four_internal_v_ties"],
    })
    authenticate(pins)
    outputs = {
        path.name: sha(path)
        for path in sorted(output.iterdir())
        if path.is_file() and path.name != "receipt.json"
    }
    write(output / "receipt.json", {
        "schema": "fresh_header_cleat_force_adapter_receipt/v1",
        "status": result["status"], "producer_sha256": sha(producer),
        "source_sha256": source_hashes, "output_sha256": outputs,
        "fresh_state_count": len(fresh_states), "fresh_v_cut_limit_count": total_cut_states,
        "all_acceptance_flags_false": all(value is False for key_name, value in FLAGS.items()
                                            if key_name != "historical_104_force_or_cut_result_transferred"),
    })
    authenticate(pins)
    return {"status": result["status"], "output": str(output),
            "fresh_state_count": len(fresh_states), "fresh_boundary_action_count": boundary_rows,
            "fresh_v_cut_limit_count": total_cut_states,
            "unsupported_physical_row_count": len(unsupported_rows),
            "checks_sha256": sha(output / "checks.json"),
            "receipt_sha256": sha(output / "receipt.json")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    result = build(parser.parse_args().output)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
