#!/usr/bin/env python3
"""Apply the reviewed BG001/BG045 component methods to fresh K12-rear demand."""
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
ROOT = next(parent for parent in HERE.parents if (parent / ".git").exists())
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
EVAL = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
OUTPUT = HERE / "screen.json"
N_PER_LBF = 4.4482216152605
MM_PER_IN = 25.4
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")

SOURCES = {
    "k12_corner_report": BASE / "current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json",
    "k12_projection_freeze": BASE / "current-corner-k12-rear-case-bound-export-attempt01/projection-freeze.json",
    "k12_source_pins": BASE / "current-corner-k12-rear-case-bound-export-attempt01/source-pins.json",
    "k12_projector": BASE / "current-corner-k12-rear-case-bound-export-attempt01/project_k12_corner.py",
    "k12_model": BASE / "current-k12-rear-spr489-direct-native-attempt01/model.json",
    "k12_deck": BASE / "current-k12-rear-spr489-direct-native-attempt01/model.inp",
    "k12_dat": BASE / "current-k12-rear-spr489-direct-native-attempt01/model.dat",
    "k12_freeze": BASE / "current-k12-rear-spr489-direct-native-attempt01/freeze.json",
    "k12_execution": BASE / "current-k12-rear-spr489-direct-native-attempt01/execution.json",
    "k12_response": BASE / "current-k12-rear-spr489-direct-native-attempt01/response.json",
    "k12_all50_audit": BASE / "current-k12-rear-spr489-direct-native-attempt01/audit.json",
    "k12_parent_terminal": BASE / "current-k12-rear-spr489-direct-native-attempt01/parent-terminal-assessment.json",
    "k12_export_row_audit": BASE / "current-k12-rear-direct-parent-native-preparation-attempt01/corner-export-verification.json",
    "a12_corner_report": BASE / "current-corner-native-demand-export-attempt03/corner-demand-report.json",
    "a1_corner_report": BASE / "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json",
    "a12_parent_export_audit": BASE / "current-corner-parent-export-audit-attempt01/audit.json",
    "a1_parent_export_audit": BASE / "current-corner-a1-parent-export-audit-attempt01/audit.json",
    "two_case_comparison": BASE / "current-corner-two-case-demand-comparison-attempt01/comparison.json",
    "a12_component_screen": BASE / "current-corner-a12-conditional-resistance-screen-attempt01/screen.json",
    "a12_bg001_end_screen": BASE / "current-corner-bg001-signed-end-distance-attempt01/signed-end-distance-screen.json",
    "bg045_two_case_screen": BASE / "current-corner-bg045-two-case-wood-mode-screen-attempt01/screen.json",
    "resultant_direction_screen": BASE / "current-corner-resultant-direction-single-shear-attempt01/resultant-direction-screen.json",
    "bg001_conditional_reference": BASE / "current-knee-post-conditional-bolt-screen-attempt01/conditional-screen.json",
    "bg003_conditional_reference": BASE / "current-knee-three-member-transfer-attempt01/calculation.json",
    "bg045_conditional_reference": BASE / "current-knee-header-endgrain-screen-attempt01/conditional-screen.json",
    "washer_geometry_screen": BASE / "current-corner-washer-seat-screen-attempt01/seat-screen.json",
    "washer_axial_screen": BASE / "current-corner-axial-tie-seat-screen-attempt01/screen.json",
    "local_wood_geometry_screen": BASE / "current-corner-local-wood-screen-attempt01/section-screen.json",
    "bolt_group_geometry": BASE / "bolt-groups/bolt-groups.json",
    "finished_profile_query": BASE / "current-knee-finished-profile-attempt01/query.json",
    "frame_grain_map": EVAL / "current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json",
    "block_grain_map": EVAL / "current-block-material-frame-map-attempt02/material-frame-map.json",
    "bg001_geometry_method": BASE / "current-corner-bg001-signed-end-distance-attempt01/produce.py",
    "resultant_direction_method": BASE / "current-corner-resultant-direction-single-shear-attempt01/produce.py",
    "bg045_component_method": BASE / "current-corner-bg045-two-case-wood-mode-screen-attempt01/produce.py",
    "nds_single_bolt_method": BASE / "nds-screen/produce.py",
    "nds_scenarios": BASE / "nds-screen/single-bolt-scenarios.json",
    "tr12_helper": ROOT / "fea/dowel_yield.py",
    "bearing_helper": ROOT / "mini_moonboard/bolted_timber_checks.py",
}

EXPECTED_SHA256 = {
    "k12_corner_report": "a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0",
    "k12_projection_freeze": "ccc1a92a1b70b8ab9b8a2d6b291b84d0ba8fa3b7b7b0b1ec3faa15d1c237e763",
    "k12_source_pins": "4bf6a081c6726d2fbbc34dc0fe044fdaee0efb610739c3c24ad43f6189854da7",
    "k12_projector": "f095da83a1597185e69205eaacfaee0302a3faad88e7ad0d3b1d55316ab7ff42",
    "k12_model": "8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd",
    "k12_deck": "6c6f8dc02616d3b92dda2f15db1a196e47935233e47eee0afaa56fda694fd3aa",
    "k12_dat": "01dc25ae3636d6c36e1d6daf6c7a648a23938cc3615f9bde45bdc3fc77b05cf6",
    "k12_freeze": "3042faf789b88a090f16e1e163780437f6bb7c0f3d7ea4dd0415b6622247edd9",
    "k12_execution": "56d1b94e6f76a0b9d4c5450a360edafadca07f28830ee9ee17aa0633b2925071",
    "k12_response": "42ffb135d47bd3bd28874e886682b4f07175ee060fb383b6e3c128e5102073c6",
    "k12_all50_audit": "66c2b9aa397b16cd4c0b2420c5cf4588e15d12bfd3fbfd75b7df8f2b0d1d4bee",
    "k12_parent_terminal": "a6ba8407bd5d74b90b651b04b760ef6dce48d09fa02dd687c4871cb1d7a7cbd3",
    "k12_export_row_audit": "15cfdcb069c930a80d154a406d29a6d3f4049badf7e1d78e6dafd4d0a298ec35",
    "a12_corner_report": "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    "a1_corner_report": "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce",
    "a12_parent_export_audit": "79ee19224ad22717f76fed3abc8d164958aae7f6f0565850ad570bbbc3d253fd",
    "a1_parent_export_audit": "42627974be539962bc79e837aea99bd230776b7de6ed2a29c3fffeab70b948f0",
    "two_case_comparison": "7b687c17f03d2ab0ddaab39193f61cc66c144d86718c9934218761a22f4e6460",
    "a12_component_screen": "ee247af7e2271e63dcf1f8d8b86ef5eeca203f3dec3e37c55f2f6a8addb1e5cb",
    "a12_bg001_end_screen": "04df4147f276e1b866b076ea428d5d16e31007219653e395990aa2083a2d239e",
    "bg045_two_case_screen": "6b63e59dbbc1e77ad46eb582b97fead1a6d874a0df8e01353f0ff049065d864b",
    "resultant_direction_screen": "d3b1ce4448ea90929b6410424f0212d86b4caee5130bca7c93209e06ad5b3c10",
    "bg001_conditional_reference": "adbedaceec692936dcd2b2393c04fc985c5590a1a5a557b74868cee94eb3175c",
    "bg003_conditional_reference": "fb7fba30fdcdabf44c90a5ac7cfe167b6a9f659af8543a8070066f15ad45c5b1",
    "bg045_conditional_reference": "2c4e3cac2c1b951ccd99cff69c5678cc605651b752ff5f9f5cc5b2f7ee3eff28",
    "washer_geometry_screen": "67dda5964a9c2a864cdb5ee0e898bae3c9e6bea212e2eeb71d5b33f765481ef0",
    "washer_axial_screen": "cae5c67d1166205aaa442c8ae889c95245162b7d1569cf264b13bc260d712ac4",
    "local_wood_geometry_screen": "22209a82b0bda6dfc5c140ccc4e481717e0e7c71d30a5827271c81ac71070564",
    "bolt_group_geometry": "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4",
    "finished_profile_query": "32d3eb326cbd4e12e91f10418f340f2a9f21509f593e3f91421f10ae6aa574d2",
    "frame_grain_map": "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409",
    "block_grain_map": "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480",
    "bg001_geometry_method": "cdd69ff54c031c5b2cadd9771525ee9860234752bd6b667d8c4ef06787412348",
    "resultant_direction_method": "d14ece8fd0d32e790e4f3de67aa8d860e6881231d6421b650e5b47f699aab57f",
    "bg045_component_method": "26aea14034a147b84b671cf0df2f7a87b7b0c0dddb63c56b9f69cfc3a0eb772a",
    "nds_single_bolt_method": "21d3b2b254b1ceb9a6cf777b98eb492b52f989cc019afa2209b92be3e4a3cdb0",
    "nds_scenarios": "130041246af11fc8e3568a7091f585d0d75581b2e1fbb3a3f4b97b750d68a7ea",
    "tr12_helper": "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    "bearing_helper": "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13",
}

CASE_ID = "k12-rear"
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
BG001_POST = "base_post_outer_left"
BG001_SPINE = "knee_outer_left_spine"
BG003_SIDE = "base_side_left"
BG003_BLOCK = "knee_outer_left_inner_frame_block"
BG045_HEADER = "base_header"
BG045_BLOCK = "knee_outer_left_inner_frame_block"
BG001_AXES = ("knee_outer_left_post_1", "knee_outer_left_post_2")
BG003_AXES = ("knee_outer_left_side_1", "knee_outer_left_side_2")
BG045_AXES = ("knee_outer_left_inner_header_1", "knee_outer_left_inner_header_2")
ACTION_RECEIVER = {
    "knee_outer_left_post_1/plane-35": BG001_POST,
    "knee_outer_left_post_2/plane-36": BG001_POST,
    "knee_outer_left_side_1/plane-37": "knee_outer_left_spine",
    "knee_outer_left_side_1/plane-38": BG003_BLOCK,
    "knee_outer_left_side_2/plane-39": "knee_outer_left_spine",
    "knee_outer_left_side_2/plane-40": BG003_BLOCK,
    "knee_outer_left_inner_header_1/plane-33": BG045_HEADER,
    "knee_outer_left_inner_header_2/plane-34": BG045_HEADER,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def close(a: float, b: float, tolerance: float = 1.0e-8) -> bool:
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tolerance * max(1.0, abs(a), abs(b))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot import pinned method source: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def require(condition: bool, gate: str) -> None:
    if not condition:
        raise ValueError(f"failed source or applicability gate: {gate}")


def source_objects() -> tuple[dict[str, Any], dict[str, str]]:
    hashes: dict[str, str] = {}
    for name, path in SOURCES.items():
        require(path.is_file(), f"source_exists:{name}")
        actual = sha(path)
        require(actual == EXPECTED_SHA256[name], f"source_sha256:{name}")
        hashes[name] = actual
    objects = {name: read_json(path) for name, path in SOURCES.items() if path.suffix == ".json"}
    return objects, hashes


def validate_demand_report(report: dict[str, Any], case_id: str, expected_schema: str) -> None:
    require(report.get("schema") == expected_schema, f"{case_id}:report_schema")
    expected_status = "PASS_K12_REAR_NUMERICAL_CORNER_DEMAND_REPORT_ONLY" if case_id == CASE_ID else "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY"
    require(report.get("status") == expected_status, f"{case_id}:report_status")
    require(report.get("case_id") == case_id and report.get("candidate") == CANDIDATE
            and report.get("geometry_revision_id") == REVISION, f"{case_id}:case_candidate_revision")
    require(report.get("actual_case_demand_usable_for_conditional_joint_checks") is True,
            f"{case_id}:usable_conditional_case_demands")
    require(report.get("qualification_boundary", {}).get("complete_joint_accepted") is False
            and report.get("qualification_boundary", {}).get("qualified_for_design") is False,
            f"{case_id}:no_joint_or_design_acceptance")
    increments = report.get("increments", [])
    require(len(increments) == 7 and float(increments[-1].get("load_factor", -1)) == 1.0,
            f"{case_id}:seven_increments_full_load")
    # These report schemas authenticate case identity at the top level; the
    # nested fresh-source record binds the exact case-register/model inputs.
    identity = report.get("fresh_source_case") or report.get("authenticated_source_case") or {}
    require(report.get("case_id") == case_id and bool(identity),
            f"{case_id}:authenticated_source_case")
    if case_id == CASE_ID:
        gates = report.get("direct_master_response_audit", {}).get("root_gates", {})
    else:
        gates = report.get("response_audit_root_gates", {})
    require(bool(gates) and all(value is True for value in gates.values()), f"{case_id}:all_root_response_gates")
    for index, increment in enumerate(increments):
        require(increment.get("all_five_corner_bodies_raw_and_interval_balance_passed") is True,
                f"{case_id}:increment_{index}:five_corner_bodies")
        igates = increment.get("response_audit_gates", {})
        require(bool(igates) and all(value is True for value in igates.values()),
                f"{case_id}:increment_{index}:all_response_gates")
        groups = increment.get("primary_physical_bolt_groups", {})
        require(set(groups) >= {"BG001", "BG003", "BG045"}, f"{case_id}:increment_{index}:primary_groups")


def validate_inputs(objects: dict[str, Any], hashes: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    k12 = objects["k12_corner_report"]
    a12 = objects["a12_corner_report"]
    a1 = objects["a1_corner_report"]
    validate_demand_report(k12, CASE_ID, "current_corner_k12_rear_spr489_direct_master_case_bound_demand_report/v1")
    validate_demand_report(a12, "a12-rear", "current_corner_native_demand_report/v1")
    validate_demand_report(a1, "a1-rear", "current_corner_case_bound_demand_report/v1")

    terminal = objects["k12_parent_terminal"]
    execution = objects["k12_execution"]
    response = objects["k12_response"]
    all50 = objects["k12_all50_audit"]
    projection = objects["k12_projection_freeze"]
    row_audit = objects["k12_export_row_audit"]
    model = objects["k12_model"]
    require(terminal.get("status") == "PASS_PARENT_K12_REAR_DIRECT_RESPONSE_AND_ALL50"
            and terminal.get("case_id") == CASE_ID
            and terminal.get("response_usable_for_conditional_joint_checks") is True
            and terminal.get("mechanical_acceptance") is False
            and terminal.get("complete_joint_resistance_established") is False
            and terminal.get("six_case_envelope_established") is False,
            "parent_terminal_assessment_passes_only_conditional_demands")
    require(execution.get("returncode") == 0 and execution.get("container_confirmed_terminal") is True
            and execution.get("native_solve_executed") is True, "native_execution_terminal_zero")
    require(response.get("schema") == "current_k12_rear_spr489_direct_master_physical_response_audit/v1"
            and response.get("status") == "PASS_K12_REAR_SPR489_DIRECT_MASTER_RESPONSE_AUDIT_ONLY"
            and response.get("case_id") == CASE_ID
            and response.get("qualified_for_design") is False
            and response.get("mechanical_acceptance") is False,
            "sealed_k12_direct_master_response")
    require(response.get("source_input_model_json_sha256") == hashes["k12_model"]
            and response.get("source_input_deck_sha256") == hashes["k12_deck"]
            and response.get("native_data_sha256") == hashes["k12_dat"],
            "response_binds_exact_model_deck_dat")
    root_gates = response.get("recovery_summary", {})
    require(bool(root_gates) and all(root_gates.get(key) is True for key in (
        "mpc_interval_checks_passed", "springa_law_checks_passed", "retained_bilateral_checks_passed",
        "selected_floor_complementarity_passed", "inactive_floor_tangent_no_restraint_or_reaction_passed",
        "raw_body_and_global_balance_passed", "rounding_interval_body_and_global_balance_passed")),
        "all_direct_response_root_gates")
    require(len(response.get("increments", [])) == 7 and response["increments"][-1].get("load_factor") == 1.0,
            "direct_response_all_seven_increments_full_factor_one")
    require(all(all(value is True for value in inc.get("response_audit_gates", {}).values())
                for inc in response["increments"]), "direct_response_all_increment_gates")
    require(all50.get("status") == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS"
            and all50.get("source_model_sha256") == hashes["k12_model"]
            and all50.get("source_response_sha256") == hashes["k12_response"]
            and len(all50.get("increments", [])) == 7
            and all(row.get("passed") is True and row.get("body_count") == 50 for row in all50["increments"]),
            "parent_independent_all50_audit_passes_all_seven")
    terminal_file_hashes = terminal.get("files_sha256", {})
    for name, key in (("model.json", "k12_model"), ("model.inp", "k12_deck"), ("model.dat", "k12_dat"),
                      ("freeze.json", "k12_freeze"), ("execution.json", "k12_execution"),
                      ("response.json", "k12_response"), ("audit.json", "k12_all50_audit")):
        require(terminal_file_hashes.get(name) == hashes[key], f"parent_terminal_binds:{name}")
    require(projection.get("status") == "FROZEN_AFTER_PARENT_RESPONSE_AND_ALL50_GATES_BEFORE_EXPORT"
            and projection.get("case_id") == CASE_ID
            and projection.get("response_status") == response.get("status")
            and projection.get("parent_terminal_status") == terminal.get("status")
            and projection.get("parent_all_body_status") == all50.get("status")
            and projection.get("mechanical_acceptance") is False,
            "response_projection_freeze_is_conditional_only")
    require(k12.get("projection_input_freeze", {}).get("sha256") == hashes["k12_projection_freeze"]
            and k12.get("authenticated_sources", {}).get("response_audit_sha256") == hashes["k12_response"]
            and k12.get("authenticated_sources", {}).get("all_body_audit_sha256") == hashes["k12_all50_audit"],
            "corner_report_binds_response_audit_and_projection_freeze")
    require(row_audit.get("status") == "PASS_PARENT_EXACT_K12_CORNER_EXPORT_ROW_COMPARISON"
            and row_audit.get("source_response_sha256") == hashes["k12_response"]
            and row_audit.get("source_export_sha256") == hashes["k12_corner_report"]
            and row_audit.get("total_interface_rows_checked") == 2366
            and row_audit.get("mechanical_acceptance") is False
            and len(row_audit.get("increments", [])) == 7
            and all(r.get("exact_native_owner_point_force_radius_rows") == 334
                    and r.get("independently_summed_floor_vectors_and_radii") == 4
                    for r in row_audit["increments"]),
            "parent_export_owner_point_force_radius_row_comparison_passes")

    for case, report, audit in (("a12-rear", a12, objects["a12_parent_export_audit"]),
                                ("a1-rear", a1, objects["a1_parent_export_audit"])):
        require(audit.get("status") == "PASS_PARENT_CORNER_INVENTORY_AND_EXACT_SIGNED_FORCE_AUDIT"
                and audit.get("joint_accepted") is False
                and audit.get("report_sha256") == hashes["a12_corner_report" if case == "a12-rear" else "a1_corner_report"],
                f"{case}:parent_export_audit_binds_report")
        report_audit = report.get("parent_independent_export_audit", {})
        if report_audit:
            require(report_audit.get("mechanical_acceptance") is False, f"{case}:historical_audit_is_not_acceptance")

    two_case = objects["two_case_comparison"]
    require(two_case.get("status") == "CONDITIONAL_TWO_CASE_CORNER_ACTION_COMPARISON"
            and two_case.get("six_case_envelope_complete") is False
            and two_case.get("joint_accepted") is False
            and two_case.get("cases", {}).get("a12-rear", {}).get("increment_count") == 7
            and two_case.get("cases", {}).get("a1-rear", {}).get("increment_count") == 7,
            "existing_a12_a1_comparison_is_conditional_only")
    require(objects["a12_component_screen"].get("status") == "PASS_SOURCE_BOUND_CONDITIONAL_COMPARABILITY_SCREEN_ONLY"
            and objects["a12_component_screen"].get("mechanical_acceptance") is False,
            "existing_a12_comparability_screen")
    require(objects["a12_bg001_end_screen"].get("mechanical_acceptance") is False
            and objects["a12_bg001_end_screen"].get("case_id") == "a12-rear",
            "existing_bg001_signed_end_screen")
    require(objects["bg045_two_case_screen"].get("acceptance_boundary", {}).get("mechanical_acceptance") is False
            and objects["bg045_two_case_screen"].get("acceptance_boundary", {}).get("complete_joint_accepted") is False,
            "existing_bg045_two_case_screen")
    require(objects["resultant_direction_screen"].get("case_id") == "a12-rear"
            and objects["resultant_direction_screen"].get("mechanical_acceptance") is False,
            "existing_single_shear_method_known_answer")
    require(objects["washer_geometry_screen"].get("schema") == "current_corner_washer_seat_screen/v1"
            or objects["washer_geometry_screen"].get("schema") == "current_corner_washer_seat_geometry_screen/v1",
            "washer_seat_geometry_screen_schema")
    require(objects["bg001_conditional_reference"].get("group", {}).get("group_id") == "BG001"
            and objects["bg001_conditional_reference"].get("verification", {}).get("mechanical_acceptance") is False,
            "bg001_single_bolt_reference_is_conditional")
    require(objects["bg045_conditional_reference"].get("group_id") == "BG045"
            and objects["bg045_conditional_reference"].get("mechanical_acceptance") is False,
            "bg045_Ceg_reference_is_conditional")
    require(objects["bg003_conditional_reference"].get("group_id") == "BG003"
            and objects["bg003_conditional_reference"].get("no_capacity_or_acceptance") is not None,
            "bg003_reference_declares_compatibility_limit")
    return k12, a12, a1


def source_functions() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    return {
        "bg001": load_module("k12_bg001_end_distance_method", SOURCES["bg001_geometry_method"]),
        "direction": load_module("k12_single_shear_method", SOURCES["resultant_direction_method"]),
        "bg045": load_module("k12_bg045_component_method", SOURCES["bg045_component_method"]),
        "nds": load_module("k12_nds_single_bolt_method", SOURCES["nds_single_bolt_method"]),
        "fe": load_module("k12_dfl_bearing_helper", SOURCES["bearing_helper"]),
    }


def angle_deg(left: list[float], right: list[float], methods: dict[str, Any]) -> float:
    cosine = math.fsum(float(a) * float(b) for a, b in zip(methods["direction"].unit(left), methods["direction"].unit(right), strict=True))
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def find_axis(geometry: dict[str, Any], axis_id: str) -> dict[str, Any]:
    rows = [row for row in geometry.get("candidate_axes", []) if row.get("axis_id") == axis_id]
    require(len(rows) == 1, f"geometry_axis:{axis_id}")
    return rows[0]


def action_role(bolt: dict[str, Any], role: str, source_suffix: str | None = None) -> dict[str, Any]:
    rows = [row for row in bolt.get("actions", []) if row.get("role") == role]
    if source_suffix is not None:
        rows = [row for row in rows if row.get("source_connection_name", "").endswith(source_suffix)]
    require(len(rows) == 1, f"{bolt.get('axis_id')}:one_action:{role}:{source_suffix}")
    return rows[0]


def force_on(action: dict[str, Any], member: str) -> list[float]:
    if action.get("first") == member:
        return [float(value) for value in action["force_on_first_xyz_n"]]
    if action.get("second") == member:
        return [float(value) for value in action["force_on_second_xyz_n"]]
    raise ValueError(f"{member} is not an endpoint of {action.get('source_connection_name')}")


def tie_row(bolt: dict[str, Any], methods: dict[str, Any]) -> dict[str, Any]:
    tie = action_role(bolt, "physical_bolt_outer_seat_tension")
    first = [float(value) for value in tie["force_on_first_xyz_n"]]
    second = [float(value) for value in tie["force_on_second_xyz_n"]]
    require(methods["direction"].vector_close(first, [-value for value in second]),
            f"{bolt.get('axis_id')}:tie_action_reaction")
    tension = methods["direction"].norm(first)
    require(tension > 0.0 and close(tension, float(bolt.get("signed_outer_seat_tie_action_n", tension))),
            f"{bolt.get('axis_id')}:positive_tie_scalar")
    return {
        "source_connection_name": tie["source_connection_name"],
        "role": tie["role"],
        "positive_physical_bolt_tension_demand_N": tension,
        "first_owner": tie["first"],
        "force_on_first_owner_xyz_N": first,
        "first_point_global_xyz_mm": tie["first_point_global_xyz_mm"],
        "second_owner": tie["second"],
        "force_on_second_owner_xyz_N": second,
        "second_point_global_xyz_mm": tie["second_point_global_xyz_mm"],
        "sign_interpretation": "Positive scalar is tensile action in the physical outer-seat tie; signed endpoint vectors and source first/second owner order are preserved.",
    }


def bg001_member_geometry(
    axis_id: str,
    member: str,
    force: list[float],
    grain: list[float],
    profile: dict[str, Any],
    diameter_mm: float,
    methods: dict[str, Any],
) -> dict[str, Any]:
    row = methods["bg001"]
    grain_unit = row.unit([float(value) for value in grain])
    action = [float(value) for value in force]
    theta = methods["direction"].angle_to_grain_deg(action, grain_unit)
    signed_g = row.dot(action, grain_unit)
    if abs(signed_g) < 1.0e-8:
        end_ray = None
        end_distance = None
        c_delta = None
        c_status = "signed_parallel_component_zero_end_unresolved"
    else:
        end_ray = "g+" if signed_g > 0.0 else "g-"
        end_distance = row.unique_profile_distance(profile, axis_id, member, end_ray)
        d_actual = end_distance / diameter_mm
        interpolation = theta / 90.0
        d_full = (1.0 - interpolation) * 7.0 + interpolation * 4.0
        d_half = (1.0 - interpolation) * 3.5 + interpolation * 2.0
        if d_actual < d_half - 1.0e-8:
            c_delta = None
            c_status = "below_Cdelta_0_5_minimum"
        elif d_actual >= d_full:
            c_delta = 1.0
            c_status = "full_factor_end_distance"
        else:
            c_delta = d_actual / d_full
            c_status = "linear_Cdelta_between_0_5_and_1_0"

    e_axis = row.unit(row.cross(grain_unit, [1.0, 0.0, 0.0]))
    signed_e = row.dot(action, e_axis)
    if abs(signed_e) < 1.0e-8:
        edge_ray = None
        edge_distance = None
        unloaded_edge = None
        unloaded_distance = None
    else:
        edge_ray = "e+" if signed_e > 0.0 else "e-"
        unloaded_edge = "e-" if edge_ray == "e+" else "e+"
        edge_distance = row.unique_profile_distance(profile, axis_id, member, edge_ray)
        unloaded_distance = row.unique_profile_distance(profile, axis_id, member, unloaded_edge)
    full_d = ((1.0 - theta / 90.0) * 7.0 + (theta / 90.0) * 4.0) if signed_g else None
    half_d = ((1.0 - theta / 90.0) * 3.5 + (theta / 90.0) * 2.0) if signed_g else None
    return {
        "member": member,
        "signed_lateral_force_xyz_N": action,
        "proposed_grain_unit_global_xyz": grain_unit,
        "signed_grain_parallel_component_N": signed_g,
        "acute_force_to_grain_angle_deg": theta,
        "signed_loaded_grain_end": end_ray,
        "profile_loaded_end_distance_mm": end_distance,
        "loaded_end_distance_D": end_distance / diameter_mm if end_distance is not None else None,
        "conditional_interpolated_end_distance_for_Cdelta_1_D": full_d,
        "conditional_interpolated_end_distance_for_Cdelta_0_5_D": half_d,
        "conditional_Cdelta": c_delta,
        "Cdelta_branch": c_status,
        "signed_crossgrain_axis_unit_global_xyz": e_axis,
        "signed_crossgrain_component_N": signed_e,
        "signed_loaded_crossgrain_edge": edge_ray,
        "profile_loaded_crossgrain_edge_distance_mm": edge_distance,
        "profile_loaded_crossgrain_edge_distance_D": edge_distance / diameter_mm if edge_distance is not None else None,
        "opposite_unloaded_crossgrain_edge": unloaded_edge,
        "profile_unloaded_crossgrain_edge_distance_mm": unloaded_distance,
        "profile_unloaded_crossgrain_edge_distance_D": unloaded_distance / diameter_mm if unloaded_distance is not None else None,
        "conditional_Table_12_5_1C_loaded_edge_minimum_D": 4.0,
        "conditional_Table_12_5_1C_unloaded_edge_minimum_D": 1.5,
        "loaded_edge_geometry_meets_listed_comparator": (edge_distance / diameter_mm >= 4.0) if edge_distance is not None else None,
        "unloaded_edge_geometry_meets_listed_comparator": (unloaded_distance / diameter_mm >= 1.5) if unloaded_distance is not None else None,
        "edge_interpretation": "Signed crossgrain-component profile distance comparison only; under this oblique force, not promoted to a full mixed-direction Table 12.5.1C determination.",
    }


def single_bolt_references(
    force_by_member: dict[str, list[float]],
    grain_by_member: dict[str, list[float]],
    main_member: str,
    side_member: str,
    main_length_in: float,
    side_length_in: float,
    diameter_in: float,
    fyb_psi: float,
    ceg: float,
    methods: dict[str, Any],
) -> dict[str, Any]:
    angles = {member: methods["direction"].angle_to_grain_deg(force_by_member[member], grain_by_member[member])
              for member in (main_member, side_member)}
    fe = {member: float(methods["fe"].dfl_dowel_bearing_psi(diameter_in, angles[member]))
          for member in (main_member, side_member)}
    theta = max(angles.values())
    result = methods["nds"].calculate(diameter_in, main_length_in, side_length_in,
                                      fe[main_member], fe[side_member], theta)
    references = {mode: float(result["reference_values_lbf"][mode]) * N_PER_LBF for mode in MODES}
    governing = min(references, key=references.get)
    after_ceg = {mode: value * ceg for mode, value in references.items()}
    return {
        "reference_method": "Reviewed NDS/TR12 six-mode single-shear helper, angle-dependent Fe, and source-pinned member roles; arithmetic reproduced with the existing helper without adjustment changes.",
        "conditional_assumptions": {
            "wood": "DF-L No. 2, SG 0.50 scenario; actual stock not verified",
            "bolt_diameter_in": diameter_in,
            "bolt_shank": "smooth full-body shank scenario",
            "bolt_bending_yield_psi": fyb_psi,
            "main_bearing_length_in": main_length_in,
            "side_bearing_length_in": side_length_in,
            "interface_gap_in": 0.0,
            "theta_max_deg": theta,
            "Ceg": ceg,
            "Ceg_application": "once to each single-bolt lateral reference" if ceg != 1.0 else "not applied for BG001 side-grain reference",
            "other_adjustment_factors": [],
        },
        "member_acute_load_to_grain_angle_deg": angles,
        "angle_dependent_bearing_Fe_psi": fe,
        "all_six_unadjusted_single_bolt_references_N": references,
        "all_six_references_after_Ceg_only_N": after_ceg,
        "governing_mode": governing,
        "governing_reference_before_Ceg_N": references[governing],
        "governing_reference_after_Ceg_only_N": after_ceg[governing],
        "reference_ratios_not_design_DCR": True,
    }


def bg001_increment(
    increment: dict[str, Any],
    grain: dict[str, list[float]],
    profile: dict[str, Any],
    geometry: dict[str, Any],
    methods: dict[str, Any],
) -> dict[str, Any]:
    group = increment["primary_physical_bolt_groups"]["BG001"]
    require({row.get("axis_id") for row in group["bolts"]} == set(BG001_AXES), "BG001_two_source_bolts")
    geometry_axes = [find_axis(geometry, axis) for axis in BG001_AXES]
    centers = [row["shaft_center_global_xyz_mm"] for row in geometry_axes]
    row_axis = methods["direction"].unit([b - a for a, b in zip(centers[0], centers[1], strict=True)])
    require(abs(row_axis[0]) < 1e-8 and abs(row_axis[1]) < 1e-8 and row_axis[2] > 1.0 - 1e-8,
            "BG001_geometry_row_is_plus_Z")
    diameter_values = {float(row["modeled_shaft_diameter_mm"]) for row in geometry_axes}
    require(len(diameter_values) == 1 and close(next(iter(diameter_values)), 6.35), "BG001_conditional_quarter_in_geometry")
    diameter_mm = next(iter(diameter_values))
    diameter_in = diameter_mm / MM_PER_IN
    basis = methods["direction"].load_json(methods["direction"].BG001_REFERENCE_SCREEN)
    cond = basis["conditional_single_bolt_basis"]
    require(close(float(cond["diameter_in"]), diameter_in)
            and close(float(cond["bolt_bending_yield_psi_assumption"]), 45000.0)
            and close(float(cond["interface_gap_in"]), 0.0), "BG001_existing_reference_scenario")
    main_length_in, side_length_in = [float(x) for x in cond["main_and_side_bearing_lengths_in"]]
    provisional: list[dict[str, Any]] = []
    all_member_rows: list[dict[str, Any]] = []
    for bolt in sorted(group["bolts"], key=lambda row: row["axis_id"]):
        plane = action_role(bolt, "candidate_bolt_lateral_plane")
        on_post = force_on(plane, BG001_POST)
        on_spine = force_on(plane, BG001_SPINE)
        require(methods["direction"].vector_close(on_post, [-x for x in on_spine]),
                f"{bolt['axis_id']}:BG001_plane_action_reaction")
        require(abs(on_post[0]) < 1.0e-7 and abs(on_spine[0]) < 1.0e-7,
                f"{bolt['axis_id']}:lateral_plane_has_no_material_bolt_axis_force")
        member_geom = {
            BG001_POST: bg001_member_geometry(bolt["axis_id"], BG001_POST, on_post, grain[BG001_POST], profile, diameter_mm, methods),
            BG001_SPINE: bg001_member_geometry(bolt["axis_id"], BG001_SPINE, on_spine, grain[BG001_SPINE], profile, diameter_mm, methods),
        }
        references = single_bolt_references(
            {BG001_POST: on_post, BG001_SPINE: on_spine}, grain, BG001_POST, BG001_SPINE,
            main_length_in, side_length_in, diameter_in, float(cond["bolt_bending_yield_psi_assumption"]), 1.0, methods,
        )
        tie = tie_row(bolt, methods)
        resultant = methods["direction"].norm(on_post)
        force_unit = methods["direction"].unit(on_post)
        row_projection = math.fsum(a * b for a, b in zip(force_unit, row_axis, strict=True))
        row_alignment = math.sqrt(max(0.0, 1.0 - row_projection * row_projection))
        member_row = {"axis_id": bolt["axis_id"], "member_geometry": member_geom}
        all_member_rows.append(member_row)
        provisional.append({
            "axis_id": bolt["axis_id"],
            "lateral_plane_connection": plane["source_connection_name"],
            "first_owner": plane["first"],
            "force_on_first_owner_xyz_N": plane["force_on_first_xyz_n"],
            "second_owner": plane["second"],
            "force_on_second_owner_xyz_N": plane["force_on_second_xyz_n"],
            "conditional_main_member": BG001_POST,
            "conditional_side_member": BG001_SPINE,
            "force_on_post_xyz_N": on_post,
            "force_on_spine_xyz_N": on_spine,
            "lateral_resultant_N": resultant,
            "signed_direction_azimuth_in_YZ_deg": math.degrees(math.atan2(on_post[1], on_post[2])),
            "member_signed_end_edge_geometry": member_geom,
            "single_bolt_yield_references": references,
            "resultant_over_unadjusted_reference_by_mode": {
                mode: resultant / value for mode, value in references["all_six_unadjusted_single_bolt_references_N"].items()
            },
            "Cg_for_this_actual_action": None,
            "Cg_applied": False,
            "row_alignment_sine_for_main_action": row_alignment,
            "Cg_nontransfer_reason": "The reviewed Cg helper permits its retained Cg=1.0 only for an action aligned with the bolt row; this action has a nonzero off-row component. No mixed-direction Cg is introduced.",
            "physical_tie": tie,
        })
    cdelta_candidates = [
        (float(member["conditional_Cdelta"]), bolt["axis_id"], member_name)
        for bolt in provisional
        for member_name, member in bolt["member_signed_end_edge_geometry"].items()
        if member["conditional_Cdelta"] is not None
    ]
    require(len(cdelta_candidates) == 4, "BG001_all_four_member_end_Cdelta_values_resolved")
    group_cdelta, control_axis, control_member = min(cdelta_candidates, key=lambda row: row[0])
    for bolt in provisional:
        raw_refs = bolt["single_bolt_yield_references"]["all_six_unadjusted_single_bolt_references_N"]
        demand = bolt["lateral_resultant_N"]
        adjusted = {mode: value * group_cdelta for mode, value in raw_refs.items()}
        bolt["group_minimum_Cdelta_applied_to_individual_reference"] = group_cdelta
        bolt["group_minimum_Cdelta_control"] = {"axis_id": control_axis, "member": control_member}
        bolt["conditional_individual_reference_after_group_Cdelta_only_N"] = adjusted
        bolt["resultant_over_group_Cdelta_reference_by_mode"] = {
            mode: demand / value for mode, value in adjusted.items()
        }
        bolt["governing_mode"] = bolt["single_bolt_yield_references"]["governing_mode"]
        bolt["governing_Cdelta_only_reference_N"] = adjusted[bolt["governing_mode"]]
        bolt["resultant_over_governing_Cdelta_only_reference"] = demand / bolt["governing_Cdelta_only_reference_N"]
    bolt["capacity_or_group_resistance"] = None
    group_sum = [math.fsum(float(row["force_on_post_xyz_N"][k]) for row in provisional) for k in range(3)]
    group_unit = methods["direction"].unit(group_sum)
    group_projection = math.fsum(a * b for a, b in zip(group_unit, row_axis, strict=True))
    group_alignment = math.sqrt(max(0.0, 1.0 - group_projection * group_projection))
    return {
        "conditional_geometry_factor": {
            "group_minimum_Cdelta": group_cdelta,
            "controlling_axis_id": control_axis,
            "controlling_member": control_member,
            "application": "One minimum over the four receiver-end geometry values, applied to each individual BG001 bolt reference as in the pinned signed-end method.",
            "geometry_and_stock_status": "Source-proposed grain plus finished-profile query only; conditional geometry, not observed or inspected stock.",
        },
        "row_alignment": {
            "bolt_row_axis_unit_global_xyz": row_axis,
            "main_member_group_lateral_resultant_xyz_N": group_sum,
            "group_resultant_alignment_sine": group_alignment,
            "Cg_applied": False,
            "reason": "The per-bolt and group lateral directions are not aligned with the +Z bolt row; prior row-aligned Cg=1.0 results are not transferred.",
        },
        "bolts": provisional,
        "group_or_mixed_action_capacity_calculated": False,
    }


def bg003_increment(increment: dict[str, Any], grain_by_member: dict[str, list[float]], methods: dict[str, Any], bg003_ref: dict[str, Any]) -> dict[str, Any]:
    group = increment["primary_physical_bolt_groups"]["BG003"]
    require({row.get("axis_id") for row in group["bolts"]} == set(BG003_AXES), "BG003_two_source_bolts")
    scenarios = [
        {"scenario_id": row["scenario_id"],
         "reference_N": float(row["one_bolt_three_member_reference_Z_lbf"]) * N_PER_LBF,
         "governing_mode": row.get("governing_mode"),
         "input_direction_global_xyz": row.get("lateral_direction_global_xyz")}
        for row in bg003_ref["scenarios"]
    ]
    results = []
    for bolt in sorted(group["bolts"], key=lambda row: row["axis_id"]):
        ties = tie_row(bolt, methods)
        planes = [row for row in bolt["actions"] if row.get("role") == "candidate_bolt_lateral_plane"]
        require(len(planes) == 2, f"{bolt['axis_id']}:two_distinct_BG003_lateral_planes")
        by_suffix = {row["source_connection_name"].rsplit("/", 1)[-1]: row for row in planes}
        suffixes = ("plane-37", "plane-38") if bolt["axis_id"].endswith("side_1") else ("plane-39", "plane-40")
        action_spine, action_block = by_suffix[suffixes[0]], by_suffix[suffixes[1]]
        on_spine = force_on(action_spine, "knee_outer_left_spine")
        on_side_1 = force_on(action_spine, BG003_SIDE)
        on_block = force_on(action_block, BG003_BLOCK)
        on_side_2 = force_on(action_block, BG003_SIDE)
        require(methods["direction"].vector_close(on_spine, [-x for x in on_side_1])
                and methods["direction"].vector_close(on_side_2, [-x for x in on_block]),
                f"{bolt['axis_id']}:both_BG003_plane_action_reactions")
        m_spine = methods["direction"].norm(on_spine)
        m_block = methods["direction"].norm(on_block)
        require(m_spine > 0.0 and m_block > 0.0, f"{bolt['axis_id']}:nonzero_outer_plane_actions")
        cosine = math.fsum(a * b for a, b in zip(methods["direction"].unit(on_spine), methods["direction"].unit(on_block), strict=True))
        angle = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
        results.append({
            "axis_id": bolt["axis_id"],
            "physical_bolt_tie": ties,
            "first_outer_plane": {
                "source_connection_name": action_spine["source_connection_name"],
                "first_owner": action_spine["first"], "force_on_first_owner_xyz_N": action_spine["force_on_first_xyz_n"],
                "second_owner": action_spine["second"], "force_on_second_owner_xyz_N": action_spine["force_on_second_xyz_n"],
                "force_on_spine_xyz_N": on_spine, "force_on_middle_side_xyz_N": on_side_1,
                "lateral_resultant_on_spine_N": m_spine,
                "acute_angle_to_proposed_grain_deg": {
                    "spine": methods["direction"].angle_to_grain_deg(on_spine, grain_by_member["knee_outer_left_spine"]),
                    "middle_side": methods["direction"].angle_to_grain_deg(on_side_1, grain_by_member[BG003_SIDE]),
                },
            },
            "second_outer_plane": {
                "source_connection_name": action_block["source_connection_name"],
                "first_owner": action_block["first"], "force_on_first_owner_xyz_N": action_block["force_on_first_xyz_n"],
                "second_owner": action_block["second"], "force_on_second_owner_xyz_N": action_block["force_on_second_xyz_n"],
                "force_on_middle_side_xyz_N": on_side_2, "force_on_inner_block_xyz_N": on_block,
                "lateral_resultant_on_inner_block_N": m_block,
                "acute_angle_to_proposed_grain_deg": {
                    "middle_side": methods["direction"].angle_to_grain_deg(on_side_2, grain_by_member[BG003_SIDE]),
                    "inner_block": methods["direction"].angle_to_grain_deg(on_block, grain_by_member[BG003_BLOCK]),
                },
            },
            "outer_plane_resultant_ratio_spine_over_block": m_spine / m_block,
            "outer_action_vector_angle_deg": angle,
            "equal_same_direction_outer_action_scenario_matches": close(m_spine, m_block) and angle < 1.0e-6,
            "existing_conditional_three_member_reference_scenarios": scenarios,
            "reference_or_capacity_ratio": None,
            "applicability": "Existing three-member double-shear references require equal same-direction outer actions. These K12 outer-plane actions are unequal and non-collinear; no reference ratio is applicable, and the plane/bearing or bolt references must not be summed.",
        })
    return {"bolts": results, "double_shear_capacity_or_group_ratio_calculated": False}


def bg045_increment(
    increment: dict[str, Any],
    geometry_model: dict[str, Any],
    grains: dict[str, list[float]],
    geometry_bounds: dict[str, Any],
    methods: dict[str, Any],
) -> dict[str, Any]:
    group = increment["primary_physical_bolt_groups"]["BG045"]
    require({row.get("axis_id") for row in group["bolts"]} == set(BG045_AXES), "BG045_two_source_bolts")
    rows = []
    for bolt in sorted(group["bolts"], key=lambda row: row["axis_id"]):
        reference = methods["bg045"].conditional_lateral_screen(bolt, CASE_ID, methods["nds"], methods["fe"], geometry_bounds)
        action = action_role(bolt, "candidate_bolt_lateral_plane")
        on_header = force_on(action, BG045_HEADER)
        on_block = force_on(action, BG045_BLOCK)
        tie = tie_row(bolt, methods)
        require(methods["direction"].vector_close(on_header, [-x for x in on_block]),
                f"{bolt['axis_id']}:BG045_lateral_action_reaction")
        point = [float(x) for x in bolt["axis_datum_global_xyz_mm"]]
        block_ray = methods["bg045"].ray_first_edge(point, on_block, geometry_bounds[BG045_BLOCK])
        header_end_bounds = geometry_bounds[BG045_HEADER]["x_end_bounds_mm"]
        if on_header[0] > 0.0:
            header_end = "+X"
            header_end_distance = header_end_bounds[1] - point[0]
        else:
            header_end = "-X"
            header_end_distance = point[0] - header_end_bounds[0]
        header_y_bounds = geometry_bounds[BG045_HEADER]["y_edge_bounds_mm"]
        if on_header[1] > 0.0:
            header_edge = "+Y"
            header_edge_distance = header_y_bounds[1] - point[1]
        elif on_header[1] < 0.0:
            header_edge = "-Y"
            header_edge_distance = point[1] - header_y_bounds[0]
        else:
            header_edge = None
            header_edge_distance = None
        threshold = 4.0 * 6.35
        block_faces = methods["bg045"].edge_face_component(on_block, point, geometry_bounds[BG045_BLOCK], BG045_BLOCK, threshold)
        rows.append({
            **reference,
            "conditional_single_bolt_reference_after_Ceg_only_N": reference["conditional_single_bolt_lateral_yield_reference"]["conditional_reference_after_Ceg_only_n"],
            "resultant_over_reference_ratio": reference["conditional_single_bolt_lateral_yield_reference"]["resultant_over_reference_ratio"],
            "lateral_plane_connection": action["source_connection_name"],
            "axis_datum_global_xyz_mm": point,
            "first_owner": action["first"], "force_on_first_owner_xyz_N": action["force_on_first_xyz_n"],
            "second_owner": action["second"], "force_on_second_owner_xyz_N": action["force_on_second_xyz_n"],
            "signed_force_direction_preserved": True,
            "physical_tie": tie,
            "block_directional_edge_geometry": {
                "proposed_grain": "+Z",
                "lateral_action_on_block_xyz_N": on_block,
                "lateral_action_is_perpendicular_to_proposed_block_grain": abs(math.fsum(a * b for a, b in zip(on_block, grains[BG045_BLOCK], strict=True))) <= 1.0e-7,
                "source_model_envelope_distances_mm": reference["model_envelope_geometry_only"][BG045_BLOCK]["source_model_envelope_distances_mm"],
                "signed_component_face_comparators": block_faces,
                "force_ray_first_face": block_ray,
                "conditional_Table_12_5_1C_loaded_edge_minimum_mm": threshold,
                "conditional_Table_12_5_1C_unloaded_edge_minimum_mm": 1.5 * 6.35,
                "edge_selection_status": "The full block action is perpendicular to proposed grain, so Table 12.5.1C categories are relevant under the named 1/4-in scenario; component faces and the rectangular force ray are separate geometry comparisons. The reviewed text does not establish a universal oblique ray rule.",
                "force_ray_is_normative_NDS_selection_rule": False,
            },
            "header_signed_end_and_edge_geometry": {
                "proposed_grain": "+X",
                "parallel_force_component_N": on_header[0],
                "signed_end_toward_component": header_end,
                "source_model_envelope_end_distance_mm": header_end_distance,
                "distance_over_conditional_softwood_tension_7D": header_end_distance / (7.0 * 6.35),
                "distance_over_conditional_parallel_compression_4D": header_end_distance / (4.0 * 6.35),
                "parallel_end_classification": "Both tension and compression reference ratios shown as geometry comparisons; sign of an action component alone does not classify the member load as tension or compression.",
                "crossgrain_force_component_N": on_header[1],
                "crossgrain_component_face": header_edge,
                "source_model_envelope_edge_distance_mm": header_edge_distance,
                "distance_over_conditional_Table_12_5_1C_4D": header_edge_distance / threshold if header_edge_distance is not None else None,
                "full_vector_Table_12_5_1C_check": False,
                "geometry_status": "Source-model rectangular envelope only; not finished/as-built verification.",
            },
            "single_bolt_yield_method_applicability": {
                "single_shear_resultant_reference_applies_to_conditional_scenario": True,
                "reference_basis": "conditional BG045 inner block main member/header side member, smooth 1/4-in bolt, zero gap, 139.0/38.1 mm bearings, DF-L No.2 SG 0.50 Fe interpolation, Fyb 45 ksi, Ceg 0.67 once",
                "calculated_mode_references_or_ratios_are_group_capacity": False,
                "mixed_axis_interaction_calculated": False,
                "axial_tie_capacity_calculated": False,
            },
        })
    group_block = [math.fsum(float(row["physical_lateral_action_on_block_xyz_n"][k]) for row in rows) for k in range(3)]
    group_header = [math.fsum(float(row["physical_lateral_action_on_header_xyz_n"][k]) for row in rows) for k in range(3)]
    require(methods["direction"].vector_close(group_block, [-x for x in group_header]), "BG045_two_bolt_group_action_reaction")
    group_ray = methods["bg045"].ray_first_edge(rows[0]["axis_datum_global_xyz_mm"], group_block, geometry_bounds[BG045_BLOCK])
    return {
        "geometry_bounds": {
            "base_header_x_end_bounds_mm": geometry_bounds[BG045_HEADER]["x_end_bounds_mm"],
            "base_header_y_edge_bounds_mm": geometry_bounds[BG045_HEADER]["y_edge_bounds_mm"],
            "inner_block_x_edge_bounds_mm": geometry_bounds[BG045_BLOCK]["x_edge_bounds_mm"],
            "inner_block_y_edge_bounds_mm": geometry_bounds[BG045_BLOCK]["y_edge_bounds_mm"],
            "source_model_envelope_only": True,
        },
        "descriptive_two_bolt_lateral_sum_on_block_xyz_N": group_block,
        "descriptive_group_force_ray_first_face_from_axis_1_datum": group_ray,
        "descriptive_group_sum_is_not_a_group_capacity_or_member_section_resultant": True,
        "bolts": rows,
    }


def washer_seats(increment: dict[str, Any], methods: dict[str, Any]) -> list[dict[str, Any]]:
    area_rows = [row for row in methods["washer_geometry_screen"]["axes"]]
    area_axis_ids = {row["axis_id"] for row in area_rows}
    axis_to_group = {
        bolt["axis_id"]: group_id
        for group_id, group in increment["primary_physical_bolt_groups"].items()
        for bolt in group.get("bolts", [])
    }
    seats = increment.get("outer_washer_seats", [])
    require(len(seats) == 12, "twelve_outer_washer_seats_per_increment")
    output = []
    for seat in seats:
        axis_id = seat["axis_id"]
        require(axis_id in area_axis_ids and axis_id in axis_to_group, f"{axis_id}:source_washer_axis_and_physical_group")
        area = float(seat["modeled_outer_washer_annular_area_mm2"])
        tie = float(seat["signed_outer_seat_tie_action_n"])
        require(tie > 0.0 and area > 0.0, f"{axis_id}:positive_tie_and_modeled_washer_area")
        pressure = tie / area
        require(close(pressure, float(seat["conditional_full_annulus_uniform_average_pressure_mpa"]), 1.0e-7),
                f"{axis_id}:{seat['physical_member']}:reported_uniform_pressure_round_trip")
        reference = seat.get("conditional_fc_perp_reference_n")
        if reference is not None:
            require(seat["physical_member"] in (BG001_POST, BG045_HEADER),
                    f"{axis_id}:Fc_perp_reference_only_on_existing_transverse_timber_seats")
        output.append({
            "axis_id": axis_id,
            "group_id": axis_to_group[axis_id],
            "member": seat["physical_member"],
            "seat_role": seat["seat_role"],
            "seat_point_global_xyz_mm": seat["seat_point_global_xyz_mm"],
            "signed_force_on_member_xyz_N": seat["seat_force_on_member_xyz_n"],
            "positive_physical_bolt_tension_demand_N": tie,
            "modeled_full_annulus_area_mm2": area,
            "uniform_average_pressure_demand_MPa": pressure,
            "conditional_Fc_perp_reference_N": reference,
            "conditional_tie_over_Fc_perp_reference": tie / float(reference) if reference is not None else None,
            "Fc_perp_applicability": (
                "conditional perpendicular-grain comparison for named transverse timber seat"
                if reference is not None else
                "not applied; block parallel-grain washer action is not an Fc_perp check"
            ),
            "support_status": seat["support_area_status"],
            "seat_pressure_method": "Positive tie magnitude divided by source-modeled CAD annular area; uniform-average scenario only. The physical tie is tensile, while the scalar is an unsigned pressure-demand magnitude.",
            "applicability": "No washer product/lot, washer opening, actual footprint/support polygon, local pressure field, steel bending/spreading, or adjusted bearing resistance is established.",
        })
    return output


def index_bolts(report: dict[str, Any], increment: dict[str, Any], group_id: str) -> dict[str, dict[str, Any]]:
    return {row["axis_id"]: row for row in increment["primary_physical_bolt_groups"][group_id]["bolts"]}


def analyze_report(report: dict[str, Any], objects: dict[str, Any], methods: dict[str, Any], model: dict[str, Any], grains: dict[str, list[float]], bg045_bounds: dict[str, Any]) -> list[dict[str, Any]]:
    profile = objects["finished_profile_query"]
    geometry = objects["bolt_group_geometry"]
    out = []
    for increment in report["increments"]:
        bg001 = bg001_increment(increment, grains, profile, geometry, methods)
        bg003 = bg003_increment(increment, grains, methods, objects["bg003_conditional_reference"])
        bg045 = bg045_increment(increment, model, grains, bg045_bounds, methods)
        seats = washer_seats(increment, objects)
        require(len(bg001["bolts"]) == 2 and len(bg003["bolts"]) == 2 and len(bg045["bolts"]) == 2,
                "six_primary_bolts_each_increment")
        out.append({"time": increment["time"], "load_factor": increment["load_factor"],
                    "BG001": bg001, "BG003": bg003, "BG045": bg045,
                    "six_ties_twelve_washer_seats": seats})
    return out


def action_vectors_by_case(report: dict[str, Any], methods: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    actions: dict[str, list[dict[str, Any]]] = {}
    for increment in report["increments"]:
        current: dict[str, dict[str, Any]] = {}
        for group_id in ("BG001", "BG003", "BG045"):
            for bolt in increment["primary_physical_bolt_groups"][group_id]["bolts"]:
                for action in bolt["actions"]:
                    if action.get("role") != "candidate_bolt_lateral_plane":
                        continue
                    name = action["source_connection_name"]
                    member = ACTION_RECEIVER[name]
                    current[name] = {"member": member, "force_xyz_N": force_on(action, member),
                                     "resultant_N": methods["direction"].norm(force_on(action, member)),
                                     "time": increment["time"], "load_factor": increment["load_factor"]}
        require(set(current) == set(ACTION_RECEIVER), "eight_stable_physical_lateral_plane_actions")
        for name, row in current.items():
            actions.setdefault(name, []).append(row)
    return actions


def tie_demands_by_case(report: dict[str, Any], methods: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for increment in report["increments"]:
        for group_id in ("BG001", "BG003", "BG045"):
            for bolt in increment["primary_physical_bolt_groups"][group_id]["bolts"]:
                row = tie_row(bolt, methods)
                result.setdefault(bolt["axis_id"], []).append({"time": increment["time"],
                    "load_factor": increment["load_factor"], "tension_N": row["positive_physical_bolt_tension_demand_N"]})
    return result


def comparison_summary(k12: dict[str, Any], a12: dict[str, Any], a1: dict[str, Any], methods: dict[str, Any], analyses: dict[str, list[dict[str, Any]]], objects: dict[str, Any]) -> dict[str, Any]:
    action_maps = {"k12-rear": action_vectors_by_case(k12, methods),
                   "a12-rear": action_vectors_by_case(a12, methods),
                   "a1-rear": action_vectors_by_case(a1, methods)}
    actions = {}
    for name in sorted(ACTION_RECEIVER):
        rows_by_case = {}
        base_vec = max(action_maps["k12-rear"][name], key=lambda r: r["resultant_N"])["force_xyz_N"]
        for case_id in ("k12-rear", "a12-rear", "a1-rear"):
            peak = max(action_maps[case_id][name], key=lambda row: row["resultant_N"])
            rows_by_case[case_id] = {"maximum_resultant_N": peak["resultant_N"],
                "maximum_at_load_factor": peak["load_factor"], "signed_force_xyz_N_at_max": peak["force_xyz_N"],
                "comparison_member": peak["member"]}
        for case_id in ("a12-rear", "a1-rear"):
            vec = rows_by_case[case_id]["signed_force_xyz_N_at_max"]
            rows_by_case[case_id]["K12_to_case_resultant_ratio"] = rows_by_case["k12-rear"]["maximum_resultant_N"] / rows_by_case[case_id]["maximum_resultant_N"]
            rows_by_case[case_id]["angle_from_K12_max_vector_deg"] = angle_deg(base_vec, vec, methods)
            rows_by_case[case_id]["opposes_K12_max_vector"] = angle_deg(base_vec, vec, methods) > 90.0
        actions[name] = rows_by_case

    tie_maps = {case_id: tie_demands_by_case(report, methods) for case_id, report in (
        ("k12-rear", k12), ("a12-rear", a12), ("a1-rear", a1))}
    ties = {}
    for axis_id in [*BG001_AXES, *BG003_AXES, *BG045_AXES]:
        case_rows = {}
        for case_id, rows in tie_maps.items():
            peak = max(rows[axis_id], key=lambda row: row["tension_N"])
            case_rows[case_id] = {"maximum_positive_tie_tension_N": peak["tension_N"],
                                  "maximum_at_load_factor": peak["load_factor"]}
        ties[axis_id] = case_rows

    analysis_by_case = analyses
    def case_min_cdelta(case_id: str) -> dict[str, Any]:
        candidates = [(inc["BG001"]["conditional_geometry_factor"]["group_minimum_Cdelta"],
                       inc["BG001"]["conditional_geometry_factor"]["controlling_axis_id"],
                       inc["BG001"]["conditional_geometry_factor"]["controlling_member"],
                       inc["load_factor"]) for inc in analysis_by_case[case_id]]
        minimum = min(candidates, key=lambda row: row[0])
        return {"minimum_over_all_increments": minimum[0], "controlling_axis_id": minimum[1],
                "controlling_member": minimum[2], "at_load_factor": minimum[3]}
    bg001_cdelta = {case_id: case_min_cdelta(case_id) for case_id in analysis_by_case}
    def max_ratio(case_id: str, group: str, field: str) -> dict[str, Any]:
        rows = [(float(bolt[field]), bolt["axis_id"], inc["load_factor"])
                for inc in analysis_by_case[case_id] for bolt in inc[group]["bolts"]
                if bolt.get(field) is not None]
        best = max(rows, key=lambda row: row[0])
        return {"maximum_ratio": best[0], "axis_id": best[1], "load_factor": best[2]}
    bg001_ratios = {case_id: max_ratio(case_id, "BG001", "resultant_over_governing_Cdelta_only_reference")
                    for case_id in analysis_by_case}
    bg045_ratios = {case_id: max_ratio(case_id, "BG045", "resultant_over_reference_ratio")
                    for case_id in analysis_by_case}
    pressure_by_case = {}
    for case_id, incs in analysis_by_case.items():
        rows = [(float(seat["uniform_average_pressure_demand_MPa"]), seat["axis_id"], seat["member"], inc["load_factor"])
                for inc in incs for seat in inc["six_ties_twelve_washer_seats"]]
        best = max(rows, key=lambda row: row[0])
        pressure_by_case[case_id] = {"maximum_modeled_full_annulus_uniform_average_pressure_MPa": best[0],
                                     "axis_id": best[1], "member": best[2], "load_factor": best[3]}

    a12_bg001 = objects["a12_bg001_end_screen"]
    a12_bg045 = [row for row in objects["bg045_two_case_screen"]["per_axis_signed_actions_and_geometry"]["a12-rear"]]
    a1_bg045 = [row for row in objects["bg045_two_case_screen"]["per_axis_signed_actions_and_geometry"]["a1-rear"]]
    return {
        "lateral_plane_action_comparisons": actions,
        "positive_tie_demand_comparisons": ties,
        "same_method_conditional_reference_comparisons": {
            "BG001_group_Cdelta_minimum_by_case": bg001_cdelta,
            "BG001_maximum_individual_resultant_over_Cdelta_only_reference_by_case": bg001_ratios,
            "BG045_maximum_individual_resultant_over_Ceg_only_reference_by_case": bg045_ratios,
            "washer_modeled_annulus_pressure_demand_maximum_by_case": pressure_by_case,
            "interpretation": "The same reviewed individual-reference arithmetic is applied to these three authenticated reports for case comparison only. Cross-case peaks are never combined into a demand case or capacity.",
        },
        "prior_a12_a1_reviewed_screen_crosschecks": {
            "a12_BG001_minimum_Cdelta_source_value": a12_bg001["group_angle_interpolated_Cdelta"],
            "a12_BG001_signed_end_reference_scalings": a12_bg001["reference_scalings"],
            "BG045_existing_a12_resultant_and_after_Ceg_ratios": [
                {"axis_id": row["axis_id"], "resultant_N": row["lateral_resultant_n"],
                 "after_Ceg_ratio": row["conditional_single_bolt_lateral_yield_reference"]["resultant_over_reference_ratio"]}
                for row in a12_bg045],
            "BG045_existing_a1_resultant_and_after_Ceg_ratios": [
                {"axis_id": row["axis_id"], "resultant_N": row["lateral_resultant_n"],
                 "after_Ceg_ratio": row["conditional_single_bolt_lateral_yield_reference"]["resultant_over_reference_ratio"]}
                for row in a1_bg045],
            "A1_BG001_signed_end_Cdelta_screen": "No prior source-pinned A1 BG001 Cdelta screen was found in the current packet; A1 is a signed-force/demand comparator here only.",
        },
    }


def key_findings(analyses: dict[str, list[dict[str, Any]]], comparison: dict[str, Any]) -> list[dict[str, Any]]:
    k12 = analyses["k12-rear"]
    bg001_peak = max((bolt["resultant_over_governing_Cdelta_only_reference"], bolt["axis_id"], inc["load_factor"], bolt)
                     for inc in k12 for bolt in inc["BG001"]["bolts"])
    bg045_peak = max((bolt["resultant_over_reference_ratio"], bolt["axis_id"], inc["load_factor"], bolt)
                     for inc in k12 for bolt in inc["BG045"]["bolts"])
    max_seat = max((seat["uniform_average_pressure_demand_MPa"], seat["axis_id"], seat["member"], inc["load_factor"], seat)
                   for inc in k12 for seat in inc["six_ties_twelve_washer_seats"])
    bg001_cdelta = min((inc["BG001"]["conditional_geometry_factor"]["group_minimum_Cdelta"],
                        inc["BG001"]["conditional_geometry_factor"]["controlling_axis_id"],
                        inc["BG001"]["conditional_geometry_factor"]["controlling_member"], inc["load_factor"])
                       for inc in k12)
    return [
        {"finding": "BG001 conditional individual-bolt screen", "axis_id": bg001_peak[1],
         "load_factor": bg001_peak[2], "maximum_resultant_over_group_Cdelta_only_Mode_IV_reference": bg001_peak[0],
         "group_minimum_Cdelta": bg001_cdelta[0], "Cdelta_control": {"axis_id": bg001_cdelta[1], "member": bg001_cdelta[2]},
         "meaning": "Largest displayed conditional single-bolt ratio only; no Cg, mixed-axis interaction, group capacity, axial-bolt check, or acceptance."},
        {"finding": "BG003 three-member compatibility remains unresolved", "largest_plane_to_plane_resultant_ratio": max(
            max(bolt["outer_plane_resultant_ratio_spine_over_block"], 1.0 / bolt["outer_plane_resultant_ratio_spine_over_block"])
            for inc in k12 for bolt in inc["BG003"]["bolts"]),
         "meaning": "Actual outer plane actions are unequal and non-collinear, so the existing equal-same-direction double-shear references remain inapplicable; no capacity ratio is reported."},
        {"finding": "BG045 conditional individual-bolt screen", "axis_id": bg045_peak[1],
         "load_factor": bg045_peak[2], "maximum_resultant_over_Ceg_only_Mode_IV_reference": bg045_peak[0],
         "meaning": "Ceg=0.67 is applied once to the reviewed Mode IV reference. This is an individual-bolt comparison only; no mixed-axis interaction, group resistance, axial capacity, or acceptance."},
        {"finding": "K12 washer-seat uniform-pressure demand", "axis_id": max_seat[1], "member": max_seat[2],
         "load_factor": max_seat[3], "uniform_average_pressure_MPa": max_seat[0],
         "meaning": "Full modeled annulus conversion only; conditional Fc-perp comparisons are confined to the existing base-post and base-header timber references."},
        {"finding": "BG045 signed header-axis-2 tie convention", "axis_id": "knee_outer_left_inner_header_2",
         "load_factor": 1.0,
         "first_owner_force_on_inner_block_xyz_N": next(b for inc in k12 if inc["load_factor"] == 1.0 for b in inc["BG045"]["bolts"] if b["axis_id"] == "knee_outer_left_inner_header_2")["physical_tie"]["force_on_first_owner_xyz_N"],
         "second_owner_force_on_header_xyz_N": next(b for inc in k12 if inc["load_factor"] == 1.0 for b in inc["BG045"]["bolts"] if b["axis_id"] == "knee_outer_left_inner_header_2")["physical_tie"]["force_on_second_owner_xyz_N"],
         "meaning": "The positive scalar is physical tie tension; preserve the source first-owner order and signed endpoint forces. Do not relabel the axial tie as compression from one endpoint's force sign."},
    ]


def build_screen() -> dict[str, Any]:
    objects, observed_hashes = source_objects()
    k12, a12, a1 = validate_inputs(objects, observed_hashes)
    methods = source_functions()
    frame_map, block_map = objects["frame_grain_map"], objects["block_grain_map"]
    bolt_geometry = objects["bolt_group_geometry"]
    grains = methods["direction"].grain_maps(frame_map, block_map)
    # BG003's central side member is a frame member omitted by the older
    # BG001 resultant helper's narrow four-member return. Add its pinned frame
    # map axis only for source-bound direction reporting; BG003 still receives
    # no resistance ratio because its three-member unequal-plane method is not
    # applicable to this action set.
    frame_rows = {row["member_id"]: row for row in frame_map["members"]}
    grains[BG003_SIDE] = [float(v) for v in frame_rows[BG003_SIDE]["conditional_grain_assignment"]["proposed_global_xyz"]]
    grains_bg045 = methods["bg045"].source_grain_vectors(frame_map, block_map, bolt_geometry, {"k12-rear": objects["k12_model"]})
    grains.update(grains_bg045)
    for member in (BG001_POST, BG001_SPINE, BG003_SIDE, BG003_BLOCK):
        model_grain = objects["k12_model"]["body_geometry"][member]["geometry_record"]["source_descriptor"]["grain_global_xyz"]
        require(methods["direction"].vector_close(grains[member], [float(x) for x in model_grain]),
                f"K12_model_grain_matches_source_map:{member}")
    bg045_bounds = methods["bg045"].geometry_bounds(objects["k12_model"], grains_bg045)
    analyses = {
        "k12-rear": analyze_report(k12, objects, methods, objects["k12_model"], grains, bg045_bounds),
        "a12-rear": analyze_report(a12, objects, methods, objects["k12_model"], grains, bg045_bounds),
        "a1-rear": analyze_report(a1, objects, methods, objects["k12_model"], grains, bg045_bounds),
    }

    # Reproduce the existing A12/A1 known answers before using the same method
    # functions for K12. These are method checks, not acceptance transfers.
    a12_direction_rows = {row["axis_id"]: row for row in objects["resultant_direction_screen"]["results"]["BG001"]}
    a12_full = analyses["a12-rear"][-1]
    for bolt in a12_full["BG001"]["bolts"]:
        known = a12_direction_rows[bolt["axis_id"]]
        require(close(bolt["lateral_resultant_N"], float(known["lateral_resultant_demand_N"]), 1.0e-7),
                f"known_answer_A12_BG001_resultant:{bolt['axis_id']}")
        require(close(bolt["single_bolt_yield_references"]["governing_reference_before_Ceg_N"],
                      float(known["governing_unadjusted_reference_N"]), 1.0e-7),
                f"known_answer_A12_BG001_mode_reference:{bolt['axis_id']}")
    a12_bg001_cdelta = objects["a12_bg001_end_screen"]
    require(close(a12_full["BG001"]["conditional_geometry_factor"]["group_minimum_Cdelta"],
                  float(a12_bg001_cdelta["group_angle_interpolated_Cdelta"]), 1.0e-7),
            "known_answer_A12_BG001_group_Cdelta")
    bg045_known = {case: {row["axis_id"]: row for row in objects["bg045_two_case_screen"]["per_axis_signed_actions_and_geometry"][case]}
                   for case in ("a12-rear", "a1-rear")}
    for case, suffix in (("a12-rear", "A12"), ("a1-rear", "A1")):
        final = analyses[case][-1]
        for bolt in final["BG045"]["bolts"]:
            known = bg045_known[case][bolt["axis_id"]]
            require(close(bolt["lateral_resultant_n"], float(known["lateral_resultant_n"]), 1.0e-7),
                    f"known_answer_{suffix}_BG045_resultant:{bolt['axis_id']}")
            require(close(bolt["conditional_single_bolt_lateral_yield_reference"]["conditional_reference_after_Ceg_only_n"],
                          float(known["conditional_single_bolt_lateral_yield_reference"]["conditional_reference_after_Ceg_only_n"]), 1.0e-7),
                    f"known_answer_{suffix}_BG045_Ceg_reference:{bolt['axis_id']}")

    comparison = comparison_summary(k12, a12, a1, methods, analyses, objects)
    k12_analysis = analyses["k12-rear"]
    peak_summary = {}
    for group in ("BG001", "BG045"):
        rows = [(float(bolt["resultant_over_governing_Cdelta_only_reference"] if group == "BG001" else bolt["resultant_over_reference_ratio"]),
                 bolt["axis_id"], inc["load_factor"])
                for inc in k12_analysis for bolt in inc[group]["bolts"]]
        best = max(rows, key=lambda row: row[0])
        peak_summary[group] = {"maximum_conditional_individual_reference_ratio": best[0], "axis_id": best[1], "load_factor": best[2]}
    peak_seats = max((seat["uniform_average_pressure_demand_MPa"], seat["axis_id"], seat["member"], inc["load_factor"])
                     for inc in k12_analysis for seat in inc["six_ties_twelve_washer_seats"])

    return {
        "schema": "current_corner_k12_rear_conditional_component_screen/v1",
        "status": "PASS_SOURCE_BOUND_CONDITIONAL_COMPONENT_SCREEN_ONLY",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "case_id": CASE_ID,
        "scope": "One authenticated K12-rear, full-factor-one response; BG001, BG003, BG045, six positive axial tie demands and twelve source washer seats across all seven accepted increments.",
        "acceptance_boundary": {
            "numerical_case_demand_usable_for_conditional_component_screens": True,
            "conditional_reference_screen_only": True,
            "mechanical_acceptance": False,
            "qualified_for_design": False,
            "complete_joint_accepted": False,
            "resistance_qualification": False,
            "six_case_envelope_complete": False,
            "sensitivity_coverage_complete": False,
            "floor_friction_or_anchorage_qualified": False,
            "retained_original_leg_runner_resistance_reopened": False,
        },
        "provenance": {
            "source_case_report_path": str(SOURCES["k12_corner_report"].relative_to(ROOT)),
            "source_case_report_sha256": observed_hashes["k12_corner_report"],
            "response_sha256": observed_hashes["k12_response"],
            "input_model_sha256": observed_hashes["k12_model"],
            "input_deck_sha256": observed_hashes["k12_deck"],
            "native_DAT_sha256": observed_hashes["k12_dat"],
            "projection_freeze_sha256": observed_hashes["k12_projection_freeze"],
            "parent_terminal_assessment_sha256": observed_hashes["k12_parent_terminal"],
            "parent_all50_audit_sha256": observed_hashes["k12_all50_audit"],
            "parent_corner_export_row_verification_sha256": observed_hashes["k12_export_row_audit"],
            "response_status": objects["k12_response"]["status"],
            "parent_terminal_status": objects["k12_parent_terminal"]["status"],
            "parent_all50_status": objects["k12_all50_audit"]["status"],
            "parent_export_row_check_status": objects["k12_export_row_audit"]["status"],
            "native_increment_count": 7,
            "full_load_factor": 1.0,
            "parent_export_rows_checked": 2366,
            "all_five_corner_bodies_raw_and_interval_balance_passed_each_increment": True,
            "all_fifty_bodies_and_global_balance_passed_each_increment": True,
            "force_report_is_conditional_demand_only": True,
        },
        "existing_conditional_method_sources": {
            "BG001_single_shear_basis": {"path": str(SOURCES["bg001_conditional_reference"].relative_to(ROOT)), "sha256": observed_hashes["bg001_conditional_reference"], "Cdelta_direction_method_path": str(SOURCES["bg001_geometry_method"].relative_to(ROOT)), "Cdelta_direction_method_sha256": observed_hashes["bg001_geometry_method"]},
            "BG045_single_shear_Ceg_basis": {"path": str(SOURCES["bg045_conditional_reference"].relative_to(ROOT)), "sha256": observed_hashes["bg045_conditional_reference"], "screen_method_path": str(SOURCES["bg045_component_method"].relative_to(ROOT)), "screen_method_sha256": observed_hashes["bg045_component_method"]},
            "single_shear_helpers": {"NDS_method_path": str(SOURCES["nds_single_bolt_method"].relative_to(ROOT)), "NDS_method_sha256": observed_hashes["nds_single_bolt_method"], "TR12_helper_path": str(SOURCES["tr12_helper"].relative_to(ROOT)), "TR12_helper_sha256": observed_hashes["tr12_helper"], "bearing_helper_path": str(SOURCES["bearing_helper"].relative_to(ROOT)), "bearing_helper_sha256": observed_hashes["bearing_helper"]},
            "BG001_profile_geometry": {"path": str(SOURCES["finished_profile_query"].relative_to(ROOT)), "sha256": observed_hashes["finished_profile_query"], "conditional_diameter_mm": 6.35},
            "BG045_source_grains_and_envelopes": {"frame_grain_map_sha256": observed_hashes["frame_grain_map"], "block_grain_map_sha256": observed_hashes["block_grain_map"], "bolt_group_geometry_sha256": observed_hashes["bolt_group_geometry"], "model_geometry_status": "source envelope only"},
            "washer_geometry": {"path": str(SOURCES["washer_geometry_screen"].relative_to(ROOT)), "sha256": observed_hashes["washer_geometry_screen"], "pressure_basis": "source-modeled CAD washer annulus; uniform-average conversion only"},
            "BG003_transfer_reference": {"path": str(SOURCES["bg003_conditional_reference"].relative_to(ROOT)), "sha256": observed_hashes["bg003_conditional_reference"], "existing_equal_same_direction_assumption_matches_actual_outer_planes": False},
            "known_answer_validation": {"a12_existing_component_screen_sha256": observed_hashes["a12_component_screen"], "a12_signed_BG001_end_screen_sha256": observed_hashes["a12_bg001_end_screen"], "BG045_two_case_screen_sha256": observed_hashes["bg045_two_case_screen"], "resultant_direction_screen_sha256": observed_hashes["resultant_direction_screen"], "known_A12_BG001_resultant_reference_and_Cdelta_checks_passed": True, "known_A12_A1_BG045_resultant_and_Ceg_reference_checks_passed": True},
        },
        "conditional_scenario": {
            "wood": "DF-L No. 2 / SG 0.50 reference scenario; actual wood/grade/moisture/condition unobserved",
            "bolt": "smooth full-body 1/4-in shank, Fyb=45 ksi, zero gap; delivered bolt/thread/hole fit unverified",
            "BG001": "Two-member single-shear NDS/TR12 references; member-specific acute grain angles; signed tension-end Cdelta interpolation; minimum geometry factor applied to individual references; Cg omitted for off-row directions.",
            "BG003": "No applicable reference ratio because the current conditional three-member scenarios assume equal same-direction outer receiver actions.",
            "BG045": "Inner-frame-block main / header side; 139.0 mm / 38.1 mm bearing; angle-dependent Fe; Ceg=0.67 applied once to single-bolt reference.",
            "washers": "Source-modeled 222.726 mm^2 annulus and uniform pressure; conditional Fc_perp reference only where the source seat record supplies it.",
        },
        "all_seven_increment_results": k12_analysis,
        "conditional_peak_summary": {
            "individual_reference_ratio_maxima": peak_summary,
            "uniform_modeled_annulus_pressure_maximum": {"pressure_MPa": peak_seats[0], "axis_id": peak_seats[1], "member": peak_seats[2], "load_factor": peak_seats[3]},
            "BG003_capacity_ratio": None,
            "interpretation": "Maximums remain per-axis/per-seat conditional components; no group, mixed-axis, whole-joint, or cross-case capacity is inferred.",
        },
        "comparison_with_existing_A12_A1": comparison,
        "key_findings": key_findings(analyses, comparison),
        "open_failure_modes_and_limits": [
            "The BG003 unequal, non-collinear outer-plane actions remain outside the existing symmetric three-member double-shear reference; a compatible continuous-bolt/middle-member resistance method is not established.",
            "BG001 Cg is not applied because the reviewed helper rejects the off-row resultant; no mixed-direction group factor is invented.",
            "BG045 Ceg is applied only to each conditional single-bolt lateral reference; no two-bolt group or axial/lateral interaction is calculated.",
            "BG001 finished-profile distances and BG045 source-model envelopes are conditional geometry, not actual observed finished cuts/edges. The BG045 oblique block component-face and rectangular-ray outputs are separately labeled geometry interpretations, not a universal NDS loaded-edge selection rule.",
            "Washer pressure is a uniform-annulus conversion; washer opening, actual support footprint, pressure distribution, washer steel bending/spreading and local bearing qualification are absent.",
            "The report does not produce splitting, row-shear, tear-out, or net-section ratios because a supported signed section-demand/resistance method and complete strength basis are absent.",
            "Member/group wrenches at reporting datums are not internal bolt bending moments or complete section forces. No full-joint acceptance or design demand is established.",
            "The twelve original LEG/FLOOR-RUNNER arrangements remain separate and their unchanged resistance work is not reopened; 92 new candidate axes are not pooled with them.",
        ],
        "source_sha256": {str(path.relative_to(ROOT)): observed_hashes[name] for name, path in SOURCES.items()},
        "producer": {"path": str((HERE / "screen.py").relative_to(ROOT)), "sha256": sha(HERE / "screen.py")},
        "native_solve_launched_by_this_screen": False,
        "geometry_changed": False,
        "mechanical_acceptance": False,
        "joint_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = build_screen()
    rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    if args.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)} sha256={sha(OUTPUT)}")
    else:
        require(OUTPUT.is_file(), "screen_output_exists_for_verify")
        require(OUTPUT.read_text(encoding="utf-8") == rendered, "screen_json_matches_reproducible_source_bound_output")
        print(f"verified {OUTPUT.relative_to(ROOT)} sha256={sha(OUTPUT)}")


if __name__ == "__main__":
    main()
