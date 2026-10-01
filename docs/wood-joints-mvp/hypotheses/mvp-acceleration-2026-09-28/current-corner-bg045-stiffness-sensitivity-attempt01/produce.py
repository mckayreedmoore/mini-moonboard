#!/usr/bin/env python3
"""Apply the pinned BG045 component references to one A12 stiffness case."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".git").exists())
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
VARIANT = BASE / "current-a12-rear-bg001-seat-stiffness-native-attempt01"
COMPARISON_DIR = BASE / "current-a12-rear-bg001-seat-stiffness-parent-native-preparation-attempt01"
BASELINE = BASE / "current-springa-selected-floor-a12-rear-attempt03"
REVIEWED = BASE / "current-corner-bg045-two-case-wood-mode-screen-attempt01"

FILES = {
    "variant_model": VARIANT / "model.json",
    "variant_deck": VARIANT / "model.inp",
    "variant_native_data": VARIANT / "model.dat",
    "variant_freeze": VARIANT / "freeze.json",
    "variant_execution": VARIANT / "execution.json",
    "variant_response": VARIANT / "response.json",
    "variant_parent_all50_audit": VARIANT / "audit.json",
    "variant_parent_terminal_assessment": VARIANT / "parent-terminal-assessment.json",
    "corner_sensitivity_comparison": COMPARISON_DIR / "corner-sensitivity-comparison.json",
    "corner_sensitivity_comparison_producer": COMPARISON_DIR / "compare_corner.py",
    "baseline_model": BASELINE / "model.json",
    "baseline_deck": BASELINE / "model.inp",
    "baseline_native_data": BASELINE / "model.dat",
    "baseline_freeze": BASELINE / "freeze.json",
    "baseline_execution": BASELINE / "execution.json",
    "baseline_response": BASELINE / "response.json",
    "reviewed_bg045_screen": REVIEWED / "screen.json",
    "reviewed_bg045_producer": REVIEWED / "produce.py",
}
EXPECTED = {
    "variant_model": "ddb65e7630eb0f6f5f44ae762eb00c61a53642122a62376f46959ccc7b1eccbb",
    "variant_deck": "dd38c90d0aef23e109449992061e885cc79278b26bc42ab1dd1e63d58cf5383c",
    "variant_native_data": "07b81caabf756a8521c79e7a0f21d5de721e1fa41208934825d1c7aaa4308a48",
    "variant_freeze": "e0d2d76b4d686d497c3b79de6c2fcfb6ff63031d7b9b50e09abf71f522663097",
    "variant_execution": "666a4df3758329c86aa6b8d25de01d027c0fbe5227bdd5116e51c5186efaa300",
    "variant_response": "5acbc31c39ad8008f310d4dea7c4e07abdaa6499456c5747af0e79b85ae4741a",
    "variant_parent_all50_audit": "0d1f438cdb7bee8dc97f989f168239917ccf6cdb39de2f8cb86fe53f814d819e",
    "variant_parent_terminal_assessment": "728ee7b0f21b9f2d66d3210b41d912af713e1b2c9736fdd1c0360fcf1a5d83b3",
    "corner_sensitivity_comparison": "f2dac0b2558ac8335f67afd209343332a5af63da6a3122b3129c094cc3048b68",
    "corner_sensitivity_comparison_producer": "78369ec28ee2b6501829944d830edc5ed0a11ef29d035878bc30841c86fced84",
    "baseline_model": "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
    "baseline_deck": "e8f7376817daa1e3ac0b7d5f85c52b16115c2cef39291486d1800e0e847e0aff",
    "baseline_native_data": "1f98a6737908286b86771ec4184e8ab08a4b3c1ce95b48a2d42e8284353ffd54",
    "baseline_freeze": "a362e551a39afcaed06ecbf0a0f1f18858fbc8677bdf2a927652b543ac67eb03",
    "baseline_execution": "6827b199681a574b744460e5b2b0e171a26fd68a51093843a897e1abb9744f00",
    "baseline_response": "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274",
    "reviewed_bg045_screen": "6b63e59dbbc1e77ad46eb582b97fead1a6d874a0df8e01353f0ff049065d864b",
}
OUTPUT = HERE / "sensitivity.json"
HEADER = "base_header"
BLOCK = "knee_outer_left_inner_frame_block"
AXIS_IDS = ("knee_outer_left_inner_header_1", "knee_outer_left_inner_header_2")
LATERAL_ROLE = "candidate_bolt_lateral_plane"
TIE_ROLE = "physical_bolt_outer_seat_tension"
REQUIRED_GATES = (
    "mpc_interval_checks_passed",
    "springa_law_checks_passed",
    "retained_bilateral_checks_passed",
    "selected_floor_complementarity_passed",
    "inactive_floor_tangent_no_restraint_or_reaction_passed",
    "raw_body_and_global_balance_passed",
    "rounding_interval_body_and_global_balance_passed",
)
INCREMENT_GATES = (
    "mpc_interval_checks_passed",
    "springa_law_checks_passed",
    "retained_bilateral_checks_passed",
    "selected_floor_complementarity_passed",
    "inactive_floor_tangent_no_restraint_or_reaction_passed",
    "raw_balance_passed",
    "rounding_interval_balance_passed",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot import pinned helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def norm(values: list[float]) -> float:
    return math.sqrt(math.fsum(float(x) * float(x) for x in values))


def sign(value: float, tol: float = 1.0e-9) -> str:
    if value > tol:
        return "+"
    if value < -tol:
        return "−"
    return "0"


def close_vec(a: list[float], b: list[float], tol: float = 1.0e-9) -> bool:
    return len(a) == len(b) and all(abs(float(x) - float(y)) <= tol * max(1.0, abs(float(x)), abs(float(y))) for x, y in zip(a, b, strict=True))


def unit_dot(a: list[float], b: list[float]) -> float:
    return max(-1.0, min(1.0, math.fsum(float(x) * float(y) for x, y in zip(a, b, strict=True)) / (norm(a) * norm(b))) )


def connection_rows(increment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return increment["physical_connection_forces"]


def axis_actions(increment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = connection_rows(increment)
    result: dict[str, dict[str, Any]] = {}
    for axis in AXIS_IDS:
        selected = [row for row in rows.values() if row.get("axis_id") == axis and row.get("role") in (LATERAL_ROLE, TIE_ROLE)]
        lateral = [row for row in selected if row["role"] == LATERAL_ROLE]
        tie = [row for row in selected if row["role"] == TIE_ROLE]
        if len(lateral) != 1 or len(tie) != 1:
            raise ValueError(f"{axis}: expected one lateral plane and one physical tie, got {len(lateral)}/{len(tie)}")
        result[axis] = {"lateral": lateral[0], "tie": tie[0]}
    return result


def compare_action_record(comparison_rows: dict[tuple[float, str], dict[str, Any]], load_factor: float, key: str, baseline: dict[str, Any], variant: dict[str, Any]) -> None:
    row = comparison_rows.get((load_factor, key))
    if row is None:
        raise ValueError(f"source comparison lacks {key} at load factor {load_factor}")
    for label, record in (("baseline", baseline), ("variant", variant)):
        expected = row[f"{label}_force_on_first_N"]
        if not close_vec(expected, record["force_on_first_xyz_n"], 1.0e-7):
            raise ValueError(f"comparison {label} force differs from response for {key} at {load_factor}")
        if row["role"] != record["role"] or row["first"] != record["first"] or row["second"] != record["second"]:
            raise ValueError(f"comparison owner/role differs for {key} at {load_factor}")


def validate_sources() -> tuple[dict[str, str], dict[str, Any]]:
    hashes = {name: sha(path) if path.is_file() else "MISSING" for name, path in FILES.items()}
    failed = [name for name, expected in EXPECTED.items() if hashes.get(name) != expected]
    if failed:
        raise ValueError("source pin mismatch or missing: " + ", ".join(failed))
    reviewed = read(FILES["reviewed_bg045_screen"])
    if reviewed.get("producer_source", {}).get("sha256") != hashes["reviewed_bg045_producer"]:
        raise ValueError("reviewed BG045 producer hash differs from pinned screen")
    dependency_hashes: dict[str, str] = {}
    for name, record in reviewed["source_pins"]["files"].items():
        path = ROOT / record["path"]
        actual = sha(path) if path.is_file() else "MISSING"
        if actual != record["sha256"]:
            raise ValueError(f"reviewed BG045 method dependency changed: {name}")
        dependency_hashes[name] = actual
    hashes.update({f"reviewed_method_dependency:{name}": value for name, value in dependency_hashes.items()})
    hashes["sensitivity_producer"] = sha(HERE / "produce.py")
    return hashes, reviewed


def validate_response_gate(response: dict[str, Any], model_hash: str, deck_hash: str, native_hash: str, execution: dict[str, Any], audit: dict[str, Any], parent: dict[str, Any], comparison_hash: str) -> dict[str, Any]:
    checks: dict[str, bool] = {
        "response_status_and_case": response.get("status") == "PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY" and response.get("case_id") == "a12-rear",
        "response_input_model_deck_and_native_data_pins": response.get("source_input_model_json_sha256") == model_hash and response.get("source_input_deck_sha256") == deck_hash and response.get("native_data_sha256") == native_hash,
        "execution_terminal_success": execution.get("native_solve_executed") is True and execution.get("returncode") == 0 and execution.get("container_confirmed_terminal") is True and execution.get("mechanical_acceptance") is False,
        "execution_output_hashes_bind_deck_model_and_DAT": execution.get("outputs_sha256", {}).get("model.json") == model_hash and execution.get("outputs_sha256", {}).get("model.inp") == deck_hash and execution.get("outputs_sha256", {}).get("model.dat") == native_hash,
        "parent_response_audit_status_and_hashes": audit.get("status") == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS" and audit.get("source_response_sha256") == sha(FILES["variant_response"]) and audit.get("source_model_sha256") == model_hash,
        "parent_terminal_assessment_binds_sources": parent.get("status") == "PASS_CONDITIONAL_A12_REAR_BG001_STIFFNESS_RESPONSE_AND_PARENT_ALL50" and parent.get("freeze_sha256") == sha(FILES["variant_freeze"]) and parent.get("execution_sha256") == sha(FILES["variant_execution"]) and parent.get("response_sha256") == sha(FILES["variant_response"]) and parent.get("independent_all50_sha256") == sha(FILES["variant_parent_all50_audit"]) and parent.get("comparison_sha256") == comparison_hash,
        "parent_terminal_scope_is_one_conditional_case": parent.get("increment_count") == 7 and parent.get("physical_body_count") == 50 and parent.get("strict_floor_selected_count") == 25 and parent.get("strict_floor_separated_count") == 75 and parent.get("mechanical_acceptance") is False and parent.get("six_case_envelope") is False and parent.get("physical_stiffness_bound") is False,
        "comparison_report_is_parent_pinned": comparison_hash == sha(FILES["corner_sensitivity_comparison"]) and comparison_hash == parent.get("comparison_sha256"),
    }
    recovery = response.get("recovery_summary", {})
    checks["all_top_level_physical_response_gates"] = all(response.get(name) is True and recovery.get(name) is True for name in REQUIRED_GATES)
    increments = response.get("increments", [])
    audits = audit.get("increments", [])
    checks["seven_matched_response_and_all50_audit_increments"] = len(increments) == len(audits) == 7 and all(a.get("load_factor") == b.get("load_factor") and a.get("time") == b.get("time") for a, b in zip(increments, audits, strict=True))
    all_inc_gates = bool(increments) and all(all(inc.get(name) is True for name in INCREMENT_GATES) for inc in increments)
    checks["all_seven_increment_response_gates"] = all_inc_gates
    checks["all_fifty_physical_bodies_and_global_equilibrium_pass_each_increment"] = bool(audits) and all(a.get("body_count") == 50 and all(v.get("printed_resultants_passed") is True and v.get("interval_resultants_passed") is True for v in [*a.get("body_equilibrium", {}).values(), a["global_equilibrium"]]) and len(a.get("body_equilibrium", {})) == 50 for a in audits)
    checks["comparison_contains_98_matched_signed_actions"] = read(FILES["corner_sensitivity_comparison"]).get("signed_action_count") == 98
    checks["nonacceptance_claims_retained"] = response.get("qualified_for_design") is False and response.get("mechanical_acceptance") is False and response.get("joint_demand_accepted") is False and parent.get("mechanical_acceptance") is False
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("sensitivity response provenance/gate failure: " + ", ".join(failed))
    return checks


def extract_force(record: dict[str, Any], member: str) -> list[float]:
    if record["first"] == member:
        return [float(x) for x in record["force_on_first_xyz_n"]]
    if record["second"] == member:
        return [float(x) for x in record["force_on_second_xyz_n"]]
    raise ValueError(f"{member} is not an owner on connector {record.get('axis_id')}")


def sign_xy(force: list[float]) -> list[str]:
    return [sign(force[0]), sign(force[1])]


def derive_member_bounds(reviewed: dict[str, Any]) -> dict[str, dict[str, Any]]:
    frames = reviewed["member_frames_and_source_envelopes"]
    return {
        HEADER: {"grain_unit_global_xyz": [1.0, 0.0, 0.0], "x_end_bounds_mm": frames[HEADER]["x_end_bounds_mm"], "y_edge_bounds_mm": frames[HEADER]["y_edge_bounds_mm"]},
        BLOCK: {"grain_unit_global_xyz": [0.0, 0.0, 1.0], "x_edge_bounds_mm": frames[BLOCK]["x_edge_bounds_mm"], "y_edge_bounds_mm": frames[BLOCK]["y_edge_bounds_mm"]},
    }


def case_pair_screen(load_factor: float, baseline_inc: dict[str, Any], variant_inc: dict[str, Any], comparison_rows: dict[tuple[float, str], dict[str, Any]], method: Any, nds: Any, bearing: Any, reviewed: dict[str, Any], geom: dict[str, Any], seat_reference: dict[str, Any]) -> dict[str, Any]:
    base_axes = axis_actions(baseline_inc)
    variant_axes = axis_actions(variant_inc)
    rows: list[dict[str, Any]] = []
    variant_block_group = [0.0, 0.0, 0.0]
    baseline_block_group = [0.0, 0.0, 0.0]
    for axis in AXIS_IDS:
        base_pair, variant_pair = base_axes[axis], variant_axes[axis]
        for role in ("lateral", "tie"):
            left, right = base_pair[role], variant_pair[role]
            if left["axis_id"] != axis or right["axis_id"] != axis or left["role"] != right["role"]:
                raise ValueError(f"{axis}: baseline/variant physical owner identity changed")
            for field in ("first", "second", "source_row_ids", "point", "first_point", "second_point"):
                if left.get(field) != right.get(field):
                    raise ValueError(f"{axis}/{role}: baseline/variant {field} changed")
            key = next(k for k, v in connection_rows(baseline_inc).items() if v is left)
            compare_action_record(comparison_rows, load_factor, key, left, right)
        base_lateral = base_pair["lateral"]
        variant_lateral = variant_pair["lateral"]
        base_tie = base_pair["tie"]
        variant_tie = variant_pair["tie"]
        base_header = extract_force(base_lateral, HEADER)
        variant_header = extract_force(variant_lateral, HEADER)
        base_block = extract_force(base_lateral, BLOCK)
        variant_block = extract_force(variant_lateral, BLOCK)
        base_tension = norm(extract_force(base_tie, HEADER))
        variant_tension = norm(extract_force(variant_tie, HEADER))
        baseline_block_group = [a + b for a, b in zip(baseline_block_group, base_block, strict=True)]
        variant_block_group = [a + b for a, b in zip(variant_block_group, variant_block, strict=True)]
        point = [float(x) for x in variant_lateral["point"]]
        def method_row(lateral: dict[str, Any], tie: dict[str, Any]) -> dict[str, Any]:
            bolt = {"axis_id": axis, "axis_datum_global_xyz_mm": point, "actions": [lateral, tie]}
            return method.conditional_lateral_screen(bolt, "a12-rear", nds, bearing, geom)
        base_method = method_row(base_lateral, base_tie)
        variant_method = method_row(variant_lateral, variant_tie)
        base_ray = method.ray_first_edge(point, base_block, geom[BLOCK])
        variant_ray = method.ray_first_edge(point, variant_block, geom[BLOCK])
        base_faces = method.edge_face_component(base_block, point, geom[BLOCK], BLOCK, 4.0 * 0.25 * method.MM_PER_IN)
        variant_faces = method.edge_face_component(variant_block, point, geom[BLOCK], BLOCK, 4.0 * 0.25 * method.MM_PER_IN)
        base_y_face = "+Y" if base_header[1] > 0.0 else ("-Y" if base_header[1] < 0.0 else None)
        variant_y_face = "+Y" if variant_header[1] > 0.0 else ("-Y" if variant_header[1] < 0.0 else None)
        edge_minimum = 4.0 * 0.25 * method.MM_PER_IN
        def face_states(face_rows: list[dict[str, Any]]) -> list[tuple[str, str]]:
            return [(row["face_selected_by_signed_component"], row["screen"]) for row in face_rows]
        header_bounds = geom[HEADER]["y_edge_bounds_mm"]
        header_component_distance = lambda face: (header_bounds[1] - point[1] if face == "+Y" else (point[1] - header_bounds[0] if face == "-Y" else None))
        base_header_edge_distance = header_component_distance(base_y_face)
        variant_header_edge_distance = header_component_distance(variant_y_face)
        base_ref = base_method["conditional_single_bolt_lateral_yield_reference"]["conditional_reference_after_Ceg_only_n"]
        variant_ref = variant_method["conditional_single_bolt_lateral_yield_reference"]["conditional_reference_after_Ceg_only_n"]
        base_pressure = base_tension / float(seat_reference["minimum_annulus_area_mm2"])
        variant_pressure = variant_tension / float(seat_reference["minimum_annulus_area_mm2"])
        base_seat_ratio = base_tension / float(seat_reference["conditional_header_Fc_perp_reference_n"])
        variant_seat_ratio = variant_tension / float(seat_reference["conditional_header_Fc_perp_reference_n"])
        rows.append({
            "axis_id": axis,
            "source_connector_names": {"lateral_plane": next(k for k, v in connection_rows(variant_inc).items() if v is variant_lateral), "outer_seat_tie": next(k for k, v in connection_rows(variant_inc).items() if v is variant_tie)},
            "source_row_ids": {"lateral_plane": variant_lateral["source_row_ids"], "outer_seat_tie": variant_tie["source_row_ids"]},
            "signed_actions_on_header": {"baseline_lateral_plane_xyz_n": base_header, "sensitivity_lateral_plane_xyz_n": variant_header, "baseline_outer_seat_tie_xyz_n": extract_force(base_tie, HEADER), "sensitivity_outer_seat_tie_xyz_n": extract_force(variant_tie, HEADER)},
            "direction_and_loaded_edge_flags": {
                "header_lateral_xy_sign_baseline": sign_xy(base_header),
                "header_lateral_xy_sign_sensitivity": sign_xy(variant_header),
                "header_lateral_component_signs_match_baseline": sign_xy(base_header) == sign_xy(variant_header),
                "block_lateral_xy_sign_baseline": sign_xy(base_block),
                "block_lateral_xy_sign_sensitivity": sign_xy(variant_block),
                "block_lateral_component_signs_match_baseline": sign_xy(base_block) == sign_xy(variant_block),
                "block_component_faces_baseline": [r["face_selected_by_signed_component"] for r in base_faces],
                "block_component_faces_sensitivity": [r["face_selected_by_signed_component"] for r in variant_faces],
                "block_component_face_flags_match_baseline": [r["face_selected_by_signed_component"] for r in base_faces] == [r["face_selected_by_signed_component"] for r in variant_faces],
                "block_component_face_threshold_states_baseline": face_states(base_faces),
                "block_component_face_threshold_states_sensitivity": face_states(variant_faces),
                "block_component_face_threshold_states_match_baseline": face_states(base_faces) == face_states(variant_faces),
                "block_force_ray_first_face_baseline": base_ray["first_face_on_force_ray"],
                "block_force_ray_first_face_sensitivity": variant_ray["first_face_on_force_ray"],
                "block_force_ray_face_matches_baseline": base_ray["first_face_on_force_ray"] == variant_ray["first_face_on_force_ray"],
                "header_crossgrain_component_face_baseline": base_y_face,
                "header_crossgrain_component_face_sensitivity": variant_y_face,
                "header_crossgrain_component_face_matches_baseline": base_y_face == variant_y_face,
                "header_crossgrain_component_edge_distance_baseline_mm": base_header_edge_distance,
                "header_crossgrain_component_edge_distance_sensitivity_mm": variant_header_edge_distance,
                "header_crossgrain_component_4D_state_baseline": "below_4D" if base_header_edge_distance is not None and base_header_edge_distance < edge_minimum else "at_or_above_4D",
                "header_crossgrain_component_4D_state_sensitivity": "below_4D" if variant_header_edge_distance is not None and variant_header_edge_distance < edge_minimum else "at_or_above_4D",
                "header_crossgrain_component_4D_state_matches_baseline": (base_header_edge_distance < edge_minimum) == (variant_header_edge_distance < edge_minimum),
                "header_tie_force_sign_baseline": [sign(v) for v in extract_force(base_tie, HEADER)],
                "header_tie_force_sign_sensitivity": [sign(v) for v in extract_force(variant_tie, HEADER)],
                "header_tie_force_sign_matches_baseline": [sign(v) for v in extract_force(base_tie, HEADER)] == [sign(v) for v in extract_force(variant_tie, HEADER)],
                "direction_cosine_header_sensitivity_vs_baseline": unit_dot(base_header, variant_header),
                "baseline_block_face_component_comparators": base_faces,
                "sensitivity_block_face_component_comparators": variant_faces,
                "baseline_block_force_ray": base_ray,
                "sensitivity_block_force_ray": variant_ray,
                "conditional_face_question": "For A12 plane 1, block +Y remains a 20 mm component-face sensitivity while the ray first meets +X; for header plane 2, the isolated −Y edge distance remains 20 mm. These are retained conditional face questions, not an adopted Table 12.5.1C result for the oblique header action or two independent loaded edges for the block.",
            },
            "conditional_resultant_angle_mode_iv_cEG_component": {
                "method_source": "unchanged reviewed six-mode NDS/TR12 producer and angle-dependent bearing helper, from pinned BG045 two-case screen",
                "baseline_lateral_demand_n": base_method["lateral_resultant_n"],
                "sensitivity_lateral_demand_n": variant_method["lateral_resultant_n"],
                "sensitivity_over_baseline_demand": variant_method["lateral_resultant_n"] / base_method["lateral_resultant_n"] if base_method["lateral_resultant_n"] else None,
                "baseline_header_angle_to_grain_degrees": base_method["acute_force_to_grain_angle_degrees"][HEADER],
                "sensitivity_header_angle_to_grain_degrees": variant_method["acute_force_to_grain_angle_degrees"][HEADER],
                "baseline_mode_iv_reference_after_Ceg_only_n": base_ref,
                "sensitivity_mode_iv_reference_after_Ceg_only_n": variant_ref,
                "baseline_lateral_demand_over_reference": base_method["conditional_single_bolt_lateral_yield_reference"]["resultant_over_reference_ratio"],
                "sensitivity_lateral_demand_over_reference": variant_method["conditional_single_bolt_lateral_yield_reference"]["resultant_over_reference_ratio"],
                "scope": "individual-bolt resultant-angle reference only: 1/4-in smooth full-body bolt, conditional DF-L No.2 SG=.50, stated main/side bearing lengths, zero gap, 45 ksi Fyb, Ceg=.67 once; not a group or full-joint capacity",
            },
            "conditional_header_axial_seat_component": {
                "baseline_tie_compression_on_header_n": base_tension,
                "sensitivity_tie_compression_on_header_n": variant_tension,
                "sensitivity_over_baseline_tie_demand": variant_tension / base_tension if base_tension else None,
                "baseline_uniform_pressure_over_candidate_annulus_mpa": base_pressure,
                "sensitivity_uniform_pressure_over_candidate_annulus_mpa": variant_pressure,
                "baseline_demand_over_conditional_header_Fc_perp_reference": base_seat_ratio,
                "sensitivity_demand_over_conditional_header_Fc_perp_reference": variant_seat_ratio,
                "reference_area_mm2": seat_reference["minimum_annulus_area_mm2"],
                "conditional_header_Fc_perp_reference_n": seat_reference["conditional_header_Fc_perp_reference_n"],
                "scope": "same-increment header seat compression compared with the prior candidate full-annulus, uniform-pressure DF-L No.2 Fc-perp component reference; washer not selected/delivered, support and pressure distribution unverified",
                "block_seat": "Tie action on block is parallel-to-grain compression; no block Fc_parallel reference is assigned and the header Fc_perp comparator is not transferred to block.",
            },
        })
    axis_points = [base_axes[axis]["lateral"]["point"] for axis in AXIS_IDS]
    variant_axis_points = [variant_axes[axis]["lateral"]["point"] for axis in AXIS_IDS]
    if axis_points != variant_axis_points:
        raise ValueError("BG045 axis datums differ between baseline and sensitivity")
    group_point = [math.fsum(float(point[i]) for point in axis_points) / len(axis_points) for i in range(3)]
    base_group_ray = method.ray_first_edge(group_point, baseline_block_group, geom[BLOCK])
    variant_group_ray = method.ray_first_edge(group_point, variant_block_group, geom[BLOCK])
    group_flags = {
        "baseline_block_group_resultant_xyz_n": baseline_block_group,
        "sensitivity_block_group_resultant_xyz_n": variant_block_group,
        "baseline_group_force_ray_first_face": base_group_ray["first_face_on_force_ray"],
        "sensitivity_group_force_ray_first_face": variant_group_ray["first_face_on_force_ray"],
        "group_force_ray_face_matches_baseline": base_group_ray["first_face_on_force_ray"] == variant_group_ray["first_face_on_force_ray"],
        "baseline_group_force_ray": base_group_ray,
        "sensitivity_group_force_ray": variant_group_ray,
    }
    for row in rows:
        flags = row["direction_and_loaded_edge_flags"]
        if not all(flags[name] for name in ("header_lateral_component_signs_match_baseline", "block_lateral_component_signs_match_baseline", "block_component_face_flags_match_baseline", "block_component_face_threshold_states_match_baseline", "block_force_ray_face_matches_baseline", "header_crossgrain_component_face_matches_baseline", "header_crossgrain_component_4D_state_matches_baseline", "header_tie_force_sign_matches_baseline")):
            raise ValueError(f"BG045 signed face/direction flags changed relative to baseline A12 at load factor {load_factor}, {row['axis_id']}")
    if not group_flags["group_force_ray_face_matches_baseline"]:
        raise ValueError(f"BG045 group ray face changed relative to baseline A12 at load factor {load_factor}")
    return {"time": variant_inc["time"], "load_factor": load_factor, "axis_results": rows, "block_group_direction_and_ray": group_flags}


def produce() -> dict[str, Any]:
    hashes, reviewed = validate_sources()
    variant_model = read(FILES["variant_model"])
    baseline_model = read(FILES["baseline_model"])
    variant_response = read(FILES["variant_response"])
    baseline_response = read(FILES["baseline_response"])
    variant_execution = read(FILES["variant_execution"])
    variant_audit = read(FILES["variant_parent_all50_audit"])
    variant_parent = read(FILES["variant_parent_terminal_assessment"])
    comparison = read(FILES["corner_sensitivity_comparison"])
    baseline_freeze = read(FILES["baseline_freeze"])
    variant_freeze = read(FILES["variant_freeze"])
    source_gate_checks = validate_response_gate(variant_response, hashes["variant_model"], hashes["variant_deck"], hashes["variant_native_data"], variant_execution, variant_audit, variant_parent, hashes["corner_sensitivity_comparison"])
    if comparison.get("status") != "PASS_SOURCE_BOUND_SINGLE_POINT_CORNER_SENSITIVITY_COMPARISON" or comparison.get("case_id") != "a12-rear" or comparison.get("signed_action_count") != 98:
        raise ValueError("source comparison schema/status/case changed")
    if baseline_model.get("case_id") != "a12-rear" or baseline_response.get("case_id") != "a12-rear" or baseline_response.get("status") != "PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY":
        raise ValueError("baseline A12 response/model status or case identity changed")
    baseline_summary = baseline_response.get("recovery_summary", {})
    baseline_gate_checks = {
        "baseline_A12_response_case_and_status": baseline_model.get("case_id") == "a12-rear" and baseline_response.get("case_id") == "a12-rear" and baseline_response.get("status") == "PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY",
        "baseline_source_model_deck_DAT_hashes": baseline_response.get("source_input_model_json_sha256") == hashes["baseline_model"] and baseline_response.get("source_input_deck_sha256") == hashes["baseline_deck"] and baseline_response.get("native_data_sha256") == hashes["baseline_native_data"],
        "baseline_top_level_response_gates": all(baseline_response.get(name) is True and baseline_summary.get(name) is True for name in REQUIRED_GATES),
        "baseline_all_seven_increment_gates": len(baseline_response.get("increments", [])) == 7 and all(all(inc.get(name) is True for name in INCREMENT_GATES) for inc in baseline_response["increments"]),
        "baseline_no_design_or_mechanical_acceptance": baseline_response.get("qualified_for_design") is False and baseline_response.get("mechanical_acceptance") is False and baseline_response.get("joint_demand_accepted") is False,
    }
    if not all(baseline_gate_checks.values()):
        raise ValueError("baseline A12 response gate/hash check failed")
    for label, freeze, execution, model_hash, deck_hash in (("variant", variant_freeze, variant_execution, hashes["variant_model"], hashes["variant_deck"]), ("baseline", baseline_freeze, read(FILES["baseline_execution"]), hashes["baseline_model"], hashes["baseline_deck"])):
        if (freeze.get("case_id") or "a12-rear") != "a12-rear" or freeze.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
            raise ValueError(f"{label} freeze is not the expected A12 geometry/case")
        if execution.get("returncode") != 0 or execution.get("container_confirmed_terminal") is not True:
            raise ValueError(f"{label} execution is not a terminal success")
        if execution.get("outputs_sha256", {}).get("model.json") != model_hash or execution.get("outputs_sha256", {}).get("model.inp") != deck_hash:
            raise ValueError(f"{label} execution output hash mismatch")
    if variant_response.get("native_data_sha256") != hashes["variant_native_data"] or baseline_response.get("native_data_sha256") != hashes["baseline_native_data"]:
        raise ValueError("response native DAT hash mismatch")
    for member in (HEADER, BLOCK):
        if variant_model["body_geometry"][member]["geometry_record"] != baseline_model["body_geometry"][member]["geometry_record"]:
            raise ValueError(f"BG045 member geometry changed between baseline and sensitivity: {member}")
    if len(variant_response.get("increments", [])) != 7 or len(baseline_response.get("increments", [])) != 7:
        raise ValueError("expected seven matched baseline/sensitivity response increments")
    comparison_rows: dict[tuple[float, str], dict[str, Any]] = {}
    for row in comparison["rows"]:
        key = (float(row["load_factor"]), row["name"])
        if key in comparison_rows:
            raise ValueError(f"duplicate signed comparison row {key}")
        comparison_rows[key] = row
    if len(comparison_rows) != 98:
        raise ValueError("source comparison does not contain 98 unique matched signed actions")

    geom = derive_member_bounds(reviewed)
    method = load_module("pinned_reviewed_bg045_method", FILES["reviewed_bg045_producer"])
    nds = load_module("pinned_reviewed_bg045_nds", method.SOURCES["nds_single_bolt_producer"])
    bearing = load_module("pinned_reviewed_bg045_bearing", method.SOURCES["bearing_helper"])
    seat = reviewed["washer_seat_bearing_component"]["common_conditional_scenario"]

    increment_results = []
    for baseline_inc, variant_inc in zip(baseline_response["increments"], variant_response["increments"], strict=True):
        if baseline_inc["load_factor"] != variant_inc["load_factor"] or baseline_inc["time"] != variant_inc["time"]:
            raise ValueError("baseline and stiffness-sensitivity increments do not match")
        increment_results.append(case_pair_screen(float(variant_inc["load_factor"]), baseline_inc, variant_inc, comparison_rows, method, nds, bearing, reviewed, geom, seat))

    # Assert the baseline load-factor-1 values reproduce the already reviewed
    # A12 BG045 screen; this does not transfer its broader dispositions.
    base_screen_final = {row["axis_id"]: row for row in reviewed["per_axis_signed_actions_and_geometry"]["a12-rear"]}
    final_rows = {row["axis_id"]: row for row in increment_results[-1]["axis_results"]}
    baseline_reproduction = {}
    prior_block_flags = {row["axis_id"]: row for row in reviewed["nds_edge_and_end_distance_conditional_comparator"]["block_perpendicular_to_grain_loaded_edge_comparator"]["a12-rear"]}
    prior_header_flags = {row["axis_id"]: row for row in reviewed["nds_edge_and_end_distance_conditional_comparator"]["header_crossgrain_component_edge_sensitivity"]["a12-rear"]}
    baseline_final_edge_flag_reproduction = {}
    for axis in AXIS_IDS:
        old = base_screen_final[axis]
        new = final_rows[axis]
        expected_lateral = float(old["lateral_resultant_n"])
        observed_lateral = float(new["conditional_resultant_angle_mode_iv_cEG_component"]["baseline_lateral_demand_n"])
        expected_tie = float(old["outer_seat_tie_action"]["positive_bolt_tension_magnitude_n"])
        observed_tie = float(new["conditional_header_axial_seat_component"]["baseline_tie_compression_on_header_n"])
        if abs(expected_lateral - observed_lateral) > 1e-7 or abs(expected_tie - observed_tie) > 1e-7:
            raise ValueError(f"final baseline A12 result does not reproduce reviewed BG045 method for {axis}")
        baseline_reproduction[axis] = {"reviewed_lateral_demand_n": expected_lateral, "reproduced_lateral_demand_n": observed_lateral, "reviewed_header_tie_n": expected_tie, "reproduced_header_tie_n": observed_tie, "passed": True}
        flags = new["direction_and_loaded_edge_flags"]
        old_block = prior_block_flags[axis]
        old_header = prior_header_flags[axis]
        old_component_faces = [(row["face_selected_by_signed_component"], row["screen"]) for row in old_block["component_face_comparators"]]
        new_component_faces = flags["block_component_face_threshold_states_baseline"]
        same = (
            old_block["axis_force_ray_first_face"]["first_face_on_force_ray"] == flags["block_force_ray_first_face_baseline"]
            and old_block["case_group_resultant_ray_first_face"]["first_face_on_force_ray"] == increment_results[-1]["block_group_direction_and_ray"]["baseline_group_force_ray_first_face"]
            and old_component_faces == [tuple(row) for row in new_component_faces]
            and old_header["candidate_loaded_edge_from_crossgrain_component"] == flags["header_crossgrain_component_face_baseline"]
            and abs(float(old_header["source_envelope_edge_distance_mm"]) - float(flags["header_crossgrain_component_edge_distance_baseline_mm"])) < 1.0e-8
        )
        if not same:
            raise ValueError(f"final baseline A12 edge/ray flags do not reproduce reviewed BG045 screen for {axis}: old block faces={old_component_faces}, new={new_component_faces}; axis ray old={old_block['axis_force_ray_first_face']['first_face_on_force_ray']} new={flags['block_force_ray_first_face_baseline']}; group ray old={old_block['case_group_resultant_ray_first_face']['first_face_on_force_ray']} new={increment_results[-1]['block_group_direction_and_ray']['baseline_group_force_ray_first_face']}; header face old={old_header['candidate_loaded_edge_from_crossgrain_component']} new={flags['header_crossgrain_component_face_baseline']}; header distance old={old_header['source_envelope_edge_distance_mm']} new={flags['header_crossgrain_component_edge_distance_baseline_mm']}")
        baseline_final_edge_flag_reproduction[axis] = {"reviewed_block_component_faces": old_component_faces, "reproduced_block_component_faces": [tuple(row) for row in new_component_faces], "reviewed_axis_ray_face": old_block["axis_force_ray_first_face"]["first_face_on_force_ray"], "reproduced_axis_ray_face": flags["block_force_ray_first_face_baseline"], "reviewed_group_ray_face": old_block["case_group_resultant_ray_first_face"]["first_face_on_force_ray"], "reproduced_group_ray_face": increment_results[-1]["block_group_direction_and_ray"]["baseline_group_force_ray_first_face"], "reviewed_header_crossgrain_face": old_header["candidate_loaded_edge_from_crossgrain_component"], "reproduced_header_crossgrain_face": flags["header_crossgrain_component_face_baseline"], "passed": True}

    flag_fields = ("header_lateral_component_signs_match_baseline", "block_lateral_component_signs_match_baseline", "block_component_face_flags_match_baseline", "block_component_face_threshold_states_match_baseline", "block_force_ray_face_matches_baseline", "header_crossgrain_component_face_matches_baseline", "header_crossgrain_component_4D_state_matches_baseline", "header_tie_force_sign_matches_baseline")
    same_flags_everywhere = all(all(row["direction_and_loaded_edge_flags"][name] for name in flag_fields) for inc in increment_results for row in inc["axis_results"]) and all(inc["block_group_direction_and_ray"]["group_force_ray_face_matches_baseline"] for inc in increment_results)
    if not same_flags_everywhere:
        raise ValueError("force/edge/ray classification differs from baseline A12")
    output_paths = {name: str(path.relative_to(ROOT)) for name, path in FILES.items()}
    return {
        "schema": "current_corner_bg045_stiffness_sensitivity/v1",
        "status": "PASS_SOURCE_BOUND_CONDITIONAL_BG045_COMPONENT_SENSITIVITY_ONLY",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "case_id": "a12-rear",
        "sensitivity_description": "A12 rear single conditional variant changing the two BG001 tie stiffnesses; the native response passed the pinned seven-increment physical gates and parent all-50 body/global audit. This report applies only the reviewed BG045 single-bolt resultant-angle Mode-IV*Ceg lateral reference and header Fc-perp washer-seat reference at matched increments.",
        "scope_boundary": {
            "complete_joint_accepted": False,
            "qualified_for_design": False,
            "six_case_envelope": False,
            "physical_stiffness_bound": False,
            "splitting_or_net_section_pass_inherited": False,
            "full_BG045_or_complete_corner_capacity_calculated": False,
            "geometry_or_native_model_changed_by_this_report": False,
            "baseline_comparison": "A12-rear baseline attempt03 only",
        },
        "source_pins": {
            "files": {name: {"path": output_paths[name], "sha256": value} for name, value in hashes.items() if name in output_paths},
            "reviewed_BG045_method_dependencies": {name: {"path": record["path"], "sha256": record["sha256"]} for name, record in reviewed["source_pins"]["files"].items()},
            "primary_NDS_sources_inherited_from_reviewed_BG045_screen": reviewed["source_pins"]["primary_nds_sources"],
            "all_primary_native_and_response_records_pinned": True,
        },
        "response_gate_checks": source_gate_checks,
        "baseline_A12_response_gate_checks": baseline_gate_checks,
        "stiffness_sensitivity_context": {
            "baseline_BG001_tie_stiffness_N_per_mm": comparison["baseline_tie_stiffness_N_per_mm"],
            "variant_BG001_tie_stiffness_N_per_mm": comparison["variant_tie_stiffness_N_per_mm"],
            "variant_to_baseline_tie_stiffness": comparison["variant_tie_stiffness_N_per_mm"] / comparison["baseline_tie_stiffness_N_per_mm"],
            "native_execution_return_code": variant_execution["returncode"],
            "physical_body_count": variant_parent["physical_body_count"],
            "increment_count": variant_parent["increment_count"],
            "strict_floor_selected_count": variant_parent["strict_floor_selected_count"],
            "strict_floor_separated_count": variant_parent["strict_floor_separated_count"],
            "parent_all50_audit_status": variant_audit["status"],
            "parent_all50_force_residual_max_abs_N": max(abs(float(x)) for inc in variant_audit["increments"] for body in [*inc["body_equilibrium"].values(), inc["global_equilibrium"]] for x in body["force_residual_xyz_n"]),
            "parent_all50_moment_residual_max_abs_Nmm": max(abs(float(x)) for inc in variant_audit["increments"] for body in [*inc["body_equilibrium"].values(), inc["global_equilibrium"]] for x in body["moment_residual_xyz_nmm"]),
        },
        "reviewed_conditional_reference_scenarios": {
            "lateral": base_screen_final[AXIS_IDS[0]]["conditional_single_bolt_lateral_yield_reference"]["assumptions"],
            "header_axial_seat": {key: seat[key] for key in ("candidate_washer_lead", "minimum_annulus_area_mm2", "conditional_header_Fc_perp_reference_n", "material", "support")},
            "edge_question": reviewed["nds_edge_and_end_distance_conditional_comparator"]["conditional_thresholds_mm"],
            "edge_interpretation_limit": "Reuses the previous screen's conditional directional comparisons; signed component faces and geometric ray flags are compared to baseline only. It does not elevate oblique ray-face selection into a universal Table 12.5.1C rule.",
        },
        "baseline_A12_final_reference_reproduction": baseline_reproduction,
        "baseline_A12_final_edge_flag_reproduction": baseline_final_edge_flag_reproduction,
        "signed_comparison_rows_consumed_for_BG045": 28,
        "signed_comparison_row_scope": "Two physical BG045 lateral planes and two outer-seat ties, each at seven matching A12 increments; compared to the baseline fields in the parent-pinned 98-row complete-corner signed-action comparison.",
        "all_increment_direction_and_edge_flags_match_baseline_A12": same_flags_everywhere,
        "increments": increment_results,
        "limits": [
            "This is one conditional BG001 tie-stiffness sensitivity point for A12 rear only. Its successful numerical response does not establish a physical stiffness range or branch uniqueness.",
            "Mode IV*Ceg values are individual-bolt lateral reference components with the prior explicit assumptions, not capacities to add across bolts, a combined lateral/axial check, or complete-joint resistance.",
            "Header seat ratios reuse an unadjusted Fc-perp uniform-annulus scenario; the washer is only a dimensional lead, support is assumed, and pressure is not uniformity-validated.",
            "The block seat remains parallel-grain compression with no assigned Fc-parallel reference. No splitting, net-section, group, mixed-force, bearing-distribution, or connection-acceptance conclusion is carried over.",
            "The A12 axis-1 block +Y component/20 mm face and axis-2 header −Y component/20 mm face remain conditional face questions. Baseline and sensitivity retain the same component signs and geometric ray flags; this comparison does not resolve code face-selection applicability for oblique force vectors or verify finished geometry.",
        ],
        "producer_source": {"path": str((HERE / "produce.py").relative_to(ROOT)), "sha256": hashes["sensitivity_producer"]},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = produce()
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)} sha256={sha(OUTPUT)}")
        return
    if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
        raise SystemExit("sensitivity.json differs from source-bound producer output")
    print(f"verified {OUTPUT.relative_to(ROOT)} sha256={sha(OUTPUT)}")


if __name__ == "__main__":
    main()
