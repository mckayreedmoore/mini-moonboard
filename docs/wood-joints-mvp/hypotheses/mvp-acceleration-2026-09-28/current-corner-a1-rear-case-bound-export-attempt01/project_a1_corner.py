#!/usr/bin/env python3
"""Project one pinned, accepted A1-rear response into the existing corner map.

This does not launch a native solver. It authenticates the A1 response through
its frozen case context, six-case register, pinned 711 response-audit proof,
and parent all-body audit, then calls the unchanged legacy corner projection
functions. The generic df1 response auditor is not an A1 acceptance gate.
"""
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

ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
HERE = Path(__file__).resolve().parent
FREEZE_PATH = HERE / "projection-freeze.json"
OUTPUT_PATH = HERE / "corner-demand-report.json"
A1_DIR = BASE / "current-springa-selected-floor-a1-rear-attempt02"
MODEL_PATH = A1_DIR / "model.json"
DECK_PATH = A1_DIR / "model.inp"
DAT_PATH = A1_DIR / "model.dat"
RESPONSE_PATH = A1_DIR / "response-zero-u-token.json"
CONTEXT_PATH = A1_DIR / "case-context.json"
REGISTER_PATH = BASE / "current-six-case-source-load-register-attempt01/register.json"
SERIALIZATION_PATH = A1_DIR / "parent-report-serialization.json"
ALL_BODY_AUDIT_PATH = A1_DIR / "parent-all-body-response-audit.json"
CONTEXT_AUDIT_PATH = A1_DIR / "parent-case-context-check.json"
SERIALIZED_INPUT_AUDIT_PATH = A1_DIR / "parent-serialized-input-audit.json"
ZERO_U_AUDITOR_PATH = BASE / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py"
ZERO_U_AUDITOR_SHA256 = "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0"
LEGACY_EXPORTER_PATH = BASE / "current-corner-native-demand-export-attempt03/produce.py"
LEGACY_EXPORTER_SHA256 = ""  # Loaded from the immutable projection freeze.
OUTPUT_SCHEMA = "current_corner_case_bound_demand_report/v1"

ROOT_GATES = (
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


class ProjectionBlocked(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProjectionBlocked(f"expected_json_object:{path}")
    return value


def repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def require(condition: bool, name: str) -> None:
    if not condition:
        raise ProjectionBlocked(name)


def verify_frozen_sources() -> tuple[dict[str, Any], dict[str, str]]:
    freeze = load_json(FREEZE_PATH)
    require(freeze.get("schema") == "current_corner_a1_case_bound_projection_freeze/v1", "projection_freeze_schema")
    require(freeze.get("status") == "FROZEN_BEFORE_PROJECTION", "projection_inputs_frozen_before_projection")
    source_pins = freeze.get("source_file_sha256")
    require(isinstance(source_pins, dict) and source_pins, "projection_freeze_source_file_map")
    observed: dict[str, str] = {}
    for relative, expected in source_pins.items():
        path = ROOT / relative
        require(path.is_file(), f"frozen_source_exists:{relative}")
        actual = sha256(path)
        require(actual == expected, f"frozen_source_sha256:{relative}")
        observed[relative] = actual
    actual_set = canonical_sha256(observed)
    require(actual_set == freeze.get("source_file_set_canonical_sha256"), "projection_freeze_source_set_digest")
    return freeze, observed


def import_legacy_exporter(expected_sha: str):
    source = ROOT / LEGACY_EXPORTER_PATH
    require(source.is_file() and sha256(source) == expected_sha, "pinned_legacy_corner_projection_source")
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("pinned_legacy_corner_projection_for_a1", source)
    if spec is None or spec.loader is None:
        raise ProjectionBlocked("legacy_corner_projection_importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def context_binding(context: dict[str, Any], response: dict[str, Any], model: dict[str, Any],
                    freeze: dict[str, Any]) -> dict[str, Any]:
    require(context.get("schema") == "current_springa_case_bound_input_context/v1", "A1_external_case_context_schema")
    require(context.get("case_id") == "a1-rear" == response.get("case_id") == model.get("case_id"), "A1_case_id_matches_context_model_response")
    require(context.get("candidate") == model.get("candidate") == response.get("candidate"), "A1_candidate_binding")
    require(context.get("geometry_revision_id") == model.get("geometry_revision_id") == response.get("geometry_revision_id"), "A1_geometry_revision_binding")
    require(context.get("case_context_sha256") is None, "A1_context_does_not_self_hash")

    context_hash = sha256(CONTEXT_PATH)
    require(response.get("case_context_path") == str(CONTEXT_PATH.resolve()), "response_exact_adjacent_case_context_path")
    require(response.get("case_context_sha256") == context_hash, "response_case_context_sha256")
    require(response.get("source_input_model_json_path") == str(MODEL_PATH.resolve()), "response_exact_model_path")
    require(context.get("selected_input_model_json_path") == str(MODEL_PATH.resolve()), "context_exact_selected_model_path")
    require(context.get("selected_input_deck_path") == str(DECK_PATH.resolve()), "context_exact_selected_deck_path")
    require(context.get("selected_input_model_json_sha256") == sha256(MODEL_PATH) == response.get("source_input_model_json_sha256"), "A1_selected_model_sha256")
    require(context.get("selected_input_deck_sha256") == sha256(DECK_PATH) == response.get("source_input_deck_sha256"), "A1_selected_deck_sha256")
    require(response.get("native_data_sha256") == sha256(DAT_PATH), "A1_native_dat_sha256")
    require(context.get("source_case_load_register_path") == str(REGISTER_PATH), "A1_register_path_matches_context")
    require(context.get("source_case_load_register_sha256") == sha256(REGISTER_PATH), "A1_register_sha256_matches_context")
    require(model.get("source_model_inputs_sha256") == context.get("source_model_inputs_sha256"), "A1_source_model_inputs_digest")
    require(context.get("case_record_sha256") == freeze["accepted_response"].get("case_record_sha256", context.get("case_record_sha256")), "A1_case_record_hash_freeze")

    register = load_json(ROOT / REGISTER_PATH)
    require(register.get("status") == "PASS_FRESH_SIX_CASE_SOURCE_LOAD_WRENCH_REGISTER", "A1_source_register_status_present")
    require(register.get("candidate") == context.get("candidate"), "A1_register_candidate")
    require(register.get("geometry_revision_id") == context.get("geometry_revision_id"), "A1_register_revision")
    cases = [row for row in register.get("cases", []) if row.get("case_id") == "a1-rear"]
    require(len(cases) == 1, "A1_register_has_exact_case_row")
    case_record_sha = canonical_sha256(cases[0])
    require(case_record_sha == context.get("case_record_sha256"), "A1_register_case_record_canonical_sha256")

    provenance = response.get("case_context_provenance", {})
    expected_provenance = {
        "case_id": context.get("case_id"),
        "case_record_sha256": context.get("case_record_sha256"),
        "source_model_inputs_sha256": context.get("source_model_inputs_sha256"),
        "register_path": context.get("source_case_load_register_path"),
        "register_sha256": context.get("source_case_load_register_sha256"),
        "controls_model_path": context.get("source_controls_model_json_path"),
        "controls_model_sha256": context.get("source_controls_model_json_sha256"),
        "controls_deck_path": context.get("source_controls_deck_path"),
        "controls_deck_sha256": context.get("source_controls_deck_sha256"),
        "screen_path": context.get("diagnostic_floor_screen_path"),
        "screen_sha256": context.get("diagnostic_floor_screen_sha256"),
        "screen_status": context.get("diagnostic_floor_screen_status"),
    }
    for key, expected in expected_provenance.items():
        require(provenance.get(key) == expected, f"A1_response_external_case_context_provenance:{key}")

    bound_files: dict[str, str] = {}
    path_sha_pairs = (
        ("selected_floor_deck_path", "selected_floor_deck_sha256"),
        ("selected_floor_model_json_path", "selected_floor_model_json_sha256"),
        ("diagnostic_floor_screen_path", "diagnostic_floor_screen_sha256"),
        ("source_case_load_register_path", "source_case_load_register_sha256"),
        ("source_controls_deck_path", "source_controls_deck_sha256"),
        ("source_controls_execution_path", "source_controls_execution_sha256"),
        ("source_controls_model_json_path", "source_controls_model_json_sha256"),
        ("source_controls_terminal_dat_path", "source_controls_terminal_dat_sha256"),
        ("source_fresh_case_model_path", "source_fresh_case_model_sha256"),
    )
    for path_key, hash_key in path_sha_pairs:
        path_value = context.get(path_key)
        hash_value = context.get(hash_key)
        require(isinstance(path_value, str) and isinstance(hash_value, str), f"A1_context_has_source_pin:{path_key}")
        path = repo_path(path_value)
        require(path.is_file() and sha256(path) == hash_value, f"A1_context_source_pin:{path_key}")
        bound_files[str(path)] = hash_value
    controls_freeze = repo_path(context["source_controls_model_json_path"]).parent / "freeze.json"
    require(controls_freeze.is_file() and sha256(controls_freeze) == context.get("source_controls_freeze_sha256"), "A1_all_bearing_control_freeze_sha256")

    # The diagnostic branch screen is context only: its proposal is rejected
    # and neither its forces nor its active states may seed this projection.
    model_branch = model.get("floor_branch_metadata", {})
    require(context.get("diagnostic_floor_screen_status") == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH", "A1_diagnostic_screen_status_remains_rejected")
    require(context.get("screen_positive_forces_or_active_states_reused_as_response") is False, "A1_context_no_screen_force_or_state_reuse")
    require(model_branch.get("selected_branch_screen_outputs_adopted") is False, "A1_model_no_diagnostic_screen_force_or_state_reuse")
    require(response.get("historical_c11_forces_or_active_states_used") is False, "A1_response_no_historical_forces_or_state_reuse")
    return {
        "case_id": "a1-rear",
        "case_record_sha256": case_record_sha,
        "source_model_inputs_sha256": context["source_model_inputs_sha256"],
        "register_path": str(REGISTER_PATH),
        "register_sha256": sha256(REGISTER_PATH),
        "external_case_context_path": str(CONTEXT_PATH.resolve()),
        "external_case_context_sha256": context_hash,
        "case_context_provenance": provenance,
        "bound_external_source_files": bound_files,
        "diagnostic_screen_is_context_only": True,
        "diagnostic_screen_forces_or_states_reused": False,
    }


def validate_a1_response(model: dict[str, Any], response: dict[str, Any], freeze: dict[str, Any],
                         contract: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    frozen = freeze["accepted_response"]
    require(response.get("schema") == "current_springa_selected_floor_physical_response_audit/v1", "A1_711_response_schema")
    require(response.get("status") == "PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY", "A1_711_response_status")
    require(response.get("native_output_consumed") is True and response.get("native_solve_launched_by_postprocessor") is False, "A1_native_response_parser_provenance")
    require(response.get("qualified_for_design") is False and response.get("mechanical_acceptance") is False and response.get("joint_demand_accepted") is False, "A1_response_remains_numerical_only")
    require(response.get("source_input_model_json_sha256") == sha256(MODEL_PATH) == frozen["model_sha256"], "A1_response_exact_model_hash")
    require(response.get("source_input_deck_sha256") == sha256(DECK_PATH) == frozen["deck_sha256"], "A1_response_exact_deck_hash")
    require(response.get("native_data_sha256") == sha256(DAT_PATH) == frozen["native_dat_sha256"], "A1_response_exact_dat_hash")
    require(response.get("source_model_record_canonical_sha256") == canonical_sha256(model), "A1_response_model_record_canonical_hash")
    require(response.get("source_input_model_json_path") == str(MODEL_PATH.resolve()), "A1_response_exact_model_path")
    require(response.get("source_input_deck_path") == str(DECK_PATH.resolve()), "A1_response_exact_deck_path")

    run_freeze = load_json(A1_DIR / "freeze.json")
    execution = load_json(A1_DIR / "execution.json")
    frozen_files = run_freeze.get("files_sha256", {})
    require(frozen_files.get("model.json") == sha256(MODEL_PATH), "A1_original_freeze_binds_model")
    require(frozen_files.get("model.inp") == sha256(DECK_PATH), "A1_original_freeze_binds_deck")
    outputs = execution.get("outputs_sha256", {})
    require(execution.get("run_id") == "springa-selected-a1-rear-attempt02", "A1_execution_exact_run_id")
    require(execution.get("native_solve_executed") is True and execution.get("returncode") == 0 and execution.get("container_confirmed_terminal") is True, "A1_native_execution_terminal_zero")
    require(outputs.get("model.json") == sha256(MODEL_PATH) and outputs.get("model.inp") == sha256(DECK_PATH) and outputs.get("model.dat") == sha256(DAT_PATH), "A1_execution_output_hashes_bind_model_deck_dat")
    terminal = response.get("terminal_execution_provenance", {})
    require(terminal.get("execution_sha256") == sha256(A1_DIR / "execution.json"), "A1_711_terminal_execution_hash")
    require(terminal.get("freeze_sha256") == sha256(A1_DIR / "freeze.json"), "A1_711_terminal_freeze_hash")
    require(terminal.get("returncode") == 0 and terminal.get("container_confirmed_terminal") is True and terminal.get("native_output_hashes_match") is True and terminal.get("solver_error_markers_absent") is True, "A1_711_terminal_output_gates")
    terminal_outputs = terminal.get("observed_file_sha256", {})
    require(terminal_outputs.get("model.json") == sha256(MODEL_PATH) and terminal_outputs.get("model.inp") == sha256(DECK_PATH) and terminal_outputs.get("model.dat") == sha256(DAT_PATH), "A1_711_terminal_observed_hashes")

    serialization = load_json(SERIALIZATION_PATH)
    require(serialization.get("status") == "PASS_NUMPY_SCALAR_JSON_CONVERSION_ONLY", "A1_parent_serialization_status")
    require(serialization.get("auditor_sha256") == ZERO_U_AUDITOR_SHA256, "A1_pinned_711_auditor_sha256")
    require(serialization.get("response_sha256") == sha256(RESPONSE_PATH), "A1_serialization_binds_response")
    require(serialization.get("case_context_sha256") == sha256(CONTEXT_PATH), "A1_serialization_binds_case_context")
    require(serialization.get("frozen_auditor_changed") is False and serialization.get("native_rerun") is False and serialization.get("mechanical_tolerances_changed") is False, "A1_parent_serialization_no_method_or_native_change")
    run_source_pins = run_freeze.get("source_sha256", {})
    require(run_source_pins.get(str(ZERO_U_AUDITOR_PATH)) == ZERO_U_AUDITOR_SHA256, "A1_run_freeze_pins_711_auditor")

    branch = model.get("floor_branch_metadata", {})
    require(branch.get("branch_id") == frozen.get("branch_id"), "A1_floor_branch_id_matches_freeze")
    require(branch.get("physical_force_adoption") is False and branch.get("automatic_mask_iteration_authorized") is False, "A1_floor_branch_scope_is_one_diagnostic_proposal")
    selected_count = int(branch.get("selected_cell_count", -1))
    inactive_count = int(branch.get("inactive_cell_count", -1))
    selected_rows = list(map(int, model.get("floor_selected_original_row_indices", [])))
    inactive_rows = list(map(int, model.get("floor_inactive_original_row_indices", [])))
    require(selected_count == int(context.get("selected_floor_cell_count", -2)) == frozen.get("selected_floor_cells"), "A1_dynamic_selected_floor_cell_count")
    require(inactive_count == int(context.get("inactive_floor_cell_count", -2)) == frozen.get("inactive_floor_cells"), "A1_dynamic_inactive_floor_cell_count")
    selected_tangent_count = int(branch.get("selected_source_tangent_row_count", -1))
    inactive_tangent_count = int(branch.get("inactive_source_tangent_row_count", -1))
    require(selected_tangent_count == len(selected_rows) == int(context.get("active_original_tangent_row_count", -2)) == frozen.get("selected_tangent_rows"), "A1_dynamic_active_floor_tangent_count")
    require(inactive_tangent_count == len(inactive_rows) == int(context.get("inactive_original_tangent_row_count", -2)) == frozen.get("inactive_tangent_rows"), "A1_dynamic_inactive_floor_tangent_count")
    require(len(set(selected_rows)) == selected_tangent_count and len(set(inactive_rows)) == inactive_tangent_count and set(selected_rows).isdisjoint(inactive_rows), "A1_floor_tangent_row_partition_unique")
    require(set(selected_rows) | set(inactive_rows) == set(range(selected_tangent_count + inactive_tangent_count)), "A1_floor_tangent_row_partition_complete")
    selected_cells = set(branch.get("selected_cells", []))
    inactive_cells = set(branch.get("inactive_cells", []))
    require(len(selected_cells) == selected_count and len(inactive_cells) == inactive_count and selected_cells.isdisjoint(inactive_cells), "A1_floor_cell_partition_complete")
    require(len(selected_cells | inactive_cells) == 100, "A1_floor_normal_cell_inventory_is_100")

    for key in ROOT_GATES:
        require(response.get(key) is True, f"A1_711_root_gate:{key}")
        require(response.get("recovery_summary", {}).get(key) is True, f"A1_711_recovery_summary_gate:{key}")
    increments = response.get("increments")
    require(isinstance(increments, list) and len(increments) == 7, "A1_exactly_seven_increments")
    require(abs(float(increments[-1].get("load_factor", -1.0)) - 1.0) <= 1e-8, "A1_final_load_factor_one")
    local_floor_summaries = []
    for index, inc in enumerate(increments):
        prefix = f"A1_increment_{index}"
        for key in INCREMENT_GATES:
            require(inc.get(key) is True, f"{prefix}_gate:{key}")
        balance = inc.get("physical_balance", {})
        for body in contract.get("corner_body_names", []):
            body_audit = balance.get("body_equilibrium", {}).get(body)
            require(isinstance(body_audit, dict), f"{prefix}_corner_body_present:{body}")
            require(body_audit.get("printed_resultants_passed") is True and body_audit.get("interval_resultants_passed") is True, f"{prefix}_corner_body_balance:{body}")
        global_audit = balance.get("global_equilibrium", {})
        require(global_audit.get("printed_resultants_passed") is True and global_audit.get("interval_resultants_passed") is True, f"{prefix}_global_balance")

        selected_tangents = inc.get("exact_floor_tangent_reactions", [])
        inactive_tangents = inc.get("inactive_floor_tangent_zero_actions", [])
        require(len(selected_tangents) == selected_tangent_count, f"{prefix}_exact_selected_tangent_rows_dynamic_count")
        require(len(inactive_tangents) == inactive_tangent_count, f"{prefix}_inactive_zero_tangent_rows_dynamic_count")
        active_ids = [row.get("source_row_original_index") for row in selected_tangents]
        inactive_ids = [row.get("source_row_original_index") for row in inactive_tangents]
        require(all(isinstance(x, int) for x in active_ids) and set(active_ids) == set(selected_rows) and len(set(active_ids)) == len(active_ids), f"{prefix}_selected_tangent_rows_match_frozen_mask")
        require(all(isinstance(x, int) for x in inactive_ids) and set(inactive_ids) == set(inactive_rows) and len(set(inactive_ids)) == len(inactive_ids), f"{prefix}_inactive_tangent_rows_match_frozen_mask")
        for row in selected_tangents:
            require(row.get("normal_cell") in selected_cells and row.get("local_dof") in (2, 3), f"{prefix}_selected_tangent_owner_cell_dof")
        for row in inactive_tangents:
            require(row.get("normal_cell") in inactive_cells and row.get("local_dof") in (2, 3), f"{prefix}_inactive_tangent_owner_cell_dof")
            require(row.get("native_reference_or_tangent_equation_present") is False and row.get("native_tangent_spring_present") is False and row.get("carryover_rf_interval_contains_zero") is True, f"{prefix}_inactive_tangent_unrestrained_zero_rf")
            require(row.get("force_on_first_xyz_n") == [0.0, 0.0, 0.0] and row.get("force_on_second_xyz_n") == [0.0, 0.0, 0.0] and row.get("force_rounding_radius_xyz_n") == [0.0, 0.0, 0.0], f"{prefix}_inactive_tangent_explicit_zero_vector")
        normals = inc.get("floor_normal_complementarity", {})
        require(normals.get("selected_bearing_cell_count") == selected_count and normals.get("inactive_separated_cell_count") == inactive_count, f"{prefix}_normal_cell_counts")
        require(set(normals.get("selected_cell_ids", [])) == selected_cells and set(normals.get("inactive_cell_ids", [])) == inactive_cells, f"{prefix}_normal_cell_ids_match_model_mask")
        normal_checks = normals.get("checks", [])
        require(len(normal_checks) == selected_count + inactive_count, f"{prefix}_all_100_normal_cells_checked")
        require({row.get("normal_cell") for row in normal_checks} == selected_cells | inactive_cells, f"{prefix}_all_normal_cells_have_checks")
        local_floor_summaries.append({
            "increment_index": index,
            "time": inc.get("time"),
            "load_factor": inc.get("load_factor"),
            "selected_bearing_cells": selected_count,
            "inactive_separated_cells": inactive_count,
            "selected_tangent_reaction_rows": len(selected_tangents),
            "inactive_zero_tangent_rows": len(inactive_tangents),
            "normal_cell_checks": len(normal_checks),
            "selected_cell_ids": sorted(selected_cells),
            "inactive_cell_ids": sorted(inactive_cells),
            "selected_tangent_original_row_indices": sorted(active_ids),
            "inactive_tangent_original_row_indices": sorted(inactive_ids),
        })

    parent_all_body = load_json(ALL_BODY_AUDIT_PATH)
    require(parent_all_body.get("status") == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS", "A1_parent_independent_all_body_audit_status")
    require(parent_all_body.get("source_model_sha256") == sha256(MODEL_PATH), "A1_parent_all_body_audit_model_binding")
    require(parent_all_body.get("source_response_sha256") == sha256(RESPONSE_PATH), "A1_parent_all_body_audit_response_binding")
    body_increments = parent_all_body.get("increments", [])
    require(len(body_increments) == 7, "A1_parent_all_body_audit_seven_increments")
    for index, row in enumerate(body_increments):
        require(row.get("body_count") == 50 and len(row.get("body_equilibrium", {})) == 50, f"A1_parent_audit_50_bodies_increment_{index}")
        require(row.get("passed") is True, f"A1_parent_audit_passed_increment_{index}")
        require(all(item.get("printed_resultants_passed") is True and item.get("interval_resultants_passed") is True for item in row.get("body_equilibrium", {}).values()), f"A1_parent_audit_all_50_bodies_increment_{index}")
        require(row.get("global_equilibrium", {}).get("printed_resultants_passed") is True and row.get("global_equilibrium", {}).get("interval_resultants_passed") is True, f"A1_parent_audit_global_increment_{index}")
    require(abs(float(body_increments[-1].get("load_factor", -1.0)) - 1.0) <= 1e-8, "A1_parent_audit_final_load_factor_one")

    serialized_audit = load_json(SERIALIZED_INPUT_AUDIT_PATH)
    require(serialized_audit.get("status") == "PASS_PARENT_SELECTED_FLOOR_SERIALIZED_INPUT_AUDIT" and serialized_audit.get("physical_body_count") == 50, "A1_parent_serialized_input_audit")
    require(load_json(CONTEXT_AUDIT_PATH).get("status") == "PASS_FROZEN_CASE_BOUND_INPUT_CONTRACT_ONLY", "A1_parent_external_context_audit")

    source_file = ROOT / ZERO_U_AUDITOR_PATH
    require(sha256(source_file) == ZERO_U_AUDITOR_SHA256, "A1_711_parser_source_hash")
    require(response.get("recovery_summary", {}).get("physical_body_count") == 50, "A1_711_audited_physical_body_count_50")
    require(response.get("recovery_summary", {}).get("active_exact_floor_tangent_reaction_rows_per_increment") == selected_tangent_count, "A1_711_dynamic_active_tangent_count")
    require(response.get("recovery_summary", {}).get("inactive_floor_tangent_rows_per_increment") == inactive_tangent_count, "A1_711_dynamic_inactive_tangent_count")
    require(response.get("recovery_summary", {}).get("all_100_floor_normals_checked_at_every_increment") is True, "A1_711_all_floor_normal_checks")
    return {
        "response_schema": response["schema"],
        "response_status": response["status"],
        "response_sha256": sha256(RESPONSE_PATH),
        "model_sha256": sha256(MODEL_PATH),
        "deck_sha256": sha256(DECK_PATH),
        "native_dat_sha256": sha256(DAT_PATH),
        "native_run_id": execution.get("run_id"),
        "terminal_returncode": execution.get("returncode"),
        "native_terminal": execution.get("container_confirmed_terminal"),
        "711_parser_auditor_sha256": ZERO_U_AUDITOR_SHA256,
        "parent_serialization_record_sha256": sha256(SERIALIZATION_PATH),
        "parent_all_body_response_audit_sha256": sha256(ALL_BODY_AUDIT_PATH),
        "parent_all_body_audit_status": parent_all_body["status"],
        "parent_all_body_increment_count": len(body_increments),
        "parent_all_body_count_per_increment": 50,
        "parent_body_and_global_intervals_passed": True,
        "root_response_gates": {key: response.get(key) for key in ROOT_GATES},
        "increment_count": len(increments),
        "final_load_factor": increments[-1]["load_factor"],
        "local_floor_active_cell_count": selected_count,
        "local_floor_inactive_cell_count": inactive_count,
        "local_floor_active_tangent_row_count": selected_tangent_count,
        "local_floor_inactive_tangent_row_count": inactive_tangent_count,
        "local_floor_cell_summaries": local_floor_summaries,
    }


def check_corner_sources(legacy: Any, contract: dict[str, Any], interface_map: dict[str, Any]) -> dict[str, Any]:
    evidence, failures = legacy.evidence_pins()
    require(not failures, "pinned_legacy_conditional_evidence_and_helpers")
    require(sha256(ROOT / BASE / "current-corner-demand-contract-attempt01/contract.json") == legacy.PINNED_EVIDENCE[str(BASE / "current-corner-demand-contract-attempt01/contract.json")], "corner_demand_contract_source_pin")
    require(sha256(ROOT / BASE / "current-corner-interface-recovery-map-attempt01/interface-map.json") == legacy.PINNED_EVIDENCE[str(BASE / "current-corner-interface-recovery-map-attempt01/interface-map.json")], "corner_interface_map_source_pin")
    inventory = contract.get("interface_inventory", [])
    require(len(inventory) == 338, "corner_contract_exactly_338_interfaces")
    require(len(contract.get("corner_body_names", [])) == 5, "corner_contract_five_physical_bodies")
    groups = contract.get("primary_new_corner_groups", {})
    require(set(groups) == {"BG001", "BG003", "BG045"}, "corner_contract_three_primary_groups")
    new_axes = {axis for group in groups.values() for axis in group.get("axis_ids", [])}
    retained = set(contract.get("retained_original_axis_ids", []))
    require(len(new_axes) == 6 and len(retained) == 12 and new_axes.isdisjoint(retained), "new_six_axes_separate_from_twelve_retained_axes")
    require(contract.get("new_block_axis_count") == 92 and contract.get("retained_original_leg_runner_axis_count") == 12, "corner_contract_92_new_and_12_retained_axes")
    require(interface_map.get("geometry_revision_id") == contract.get("geometry_revision_id"), "corner_interface_map_revision")
    return {
        "contract_path": str(BASE / "current-corner-demand-contract-attempt01/contract.json"),
        "contract_sha256": sha256(ROOT / BASE / "current-corner-demand-contract-attempt01/contract.json"),
        "interface_map_path": str(BASE / "current-corner-interface-recovery-map-attempt01/interface-map.json"),
        "interface_map_sha256": sha256(ROOT / BASE / "current-corner-interface-recovery-map-attempt01/interface-map.json"),
        "interface_inventory_count": len(inventory),
        "corner_body_names": contract["corner_body_names"],
        "primary_group_ids": sorted(groups),
        "new_candidate_axis_count": len(new_axes),
        "retained_original_leg_runner_axis_count": len(retained),
        "retained_original_axis_ids": sorted(retained),
        "conditional_source_hashes": evidence,
        "resistance_qualification": False,
    }


def summarize_increment(projected: dict[str, Any], source_increment: dict[str, Any],
                        branch: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    interfaces = projected["all_corner_interfaces"]
    contacts = projected["member_contact_bearing"]["contact_cells"]
    corner_floor_normal_rows = [row for row in interfaces if row.get("role") == "floor_normal"]
    corner_floor_tangent_rows = [row for row in interfaces if row.get("role") == "assumed_no_slip_floor"]
    active_corner_floor_rows = [row for row in corner_floor_tangent_rows if row.get("floor_tangent_state") == "active_selected_floor_tangent_reaction"]
    inactive_corner_floor_rows = [row for row in corner_floor_tangent_rows if row.get("floor_tangent_state") == "released_inactive_floor_tangent_zero_action"]
    groups = projected["primary_physical_bolt_groups"]
    require(len(interfaces) == 338, "increment_projected_338_interfaces")
    require(len(contacts) == 232, "increment_projected_232_contact_rows")
    require(sum(row["physical_bolt_count"] for row in groups.values()) == 6, "increment_projected_six_physical_bolts")
    require(sum(row["lateral_plane_count"] for row in groups.values()) == 8, "increment_keeps_eight_lateral_planes")
    require(sum(row["outer_seat_tie_count"] for row in groups.values()) == 6, "increment_keeps_six_outer_seat_ties")
    require(set(groups) == {"BG001", "BG003", "BG045"}, "increment_has_exact_three_primary_groups")
    require(all(groups[group]["physical_bolt_count"] == 2 and groups[group]["outer_seat_tie_count"] == 2 for group in groups), "increment_two_bolts_and_ties_per_primary_group")
    require({group: groups[group]["lateral_plane_count"] for group in groups} == {"BG001": 2, "BG003": 4, "BG045": 2}, "increment_preserves_separate_lateral_plane_distribution")
    require(len(projected["outer_washer_seats"]) == 12, "increment_keeps_twelve_washer_seats")
    require(len(projected["corner_five_body_balance"]) == 5 and projected["all_five_corner_bodies_raw_and_interval_balance_passed"] is True, "increment_corner_five_body_balance")
    require(projected.get("incoming_and_onward_transfers_included") is True, "increment_incoming_and_onward_transfer_rows_included")
    require(len(projected["retained_original_leg_runner_interfaces"]) <= 12, "increment_keeps_original_arrangement_rows_separate")
    require(projected["retained_original_arrangement_count"] == 12 and projected["retained_resistance_reopened"] is False, "increment_retains_twelve_original_arrangements")
    for row in interfaces:
        for vector_key in ("force_on_first_xyz_n", "force_on_second_xyz_n", "force_rounding_radius_xyz_n"):
            vector = row.get(vector_key)
            require(isinstance(vector, list) and len(vector) == 3 and all(math.isfinite(float(value)) for value in vector), "increment_all_signed_interface_force_vectors_retained")
        for wrench_key in ("first_side_wrench_at_owner_datum", "second_side_wrench_at_owner_datum"):
            wrench = row.get(wrench_key)
            require(isinstance(wrench, dict), "increment_all_owner_datum_wrenches_retained")
            for vector_key in ("force_xyz_n", "moment_xyz_nmm"):
                vector = wrench.get(vector_key)
                require(isinstance(vector, list) and len(vector) == 3 and all(math.isfinite(float(value)) for value in vector), "increment_all_owner_datum_wrench_vectors_retained")
    # The whole-frame selected-floor branch audits 100 normal cells (46 active,
    # 54 separated for this A1 response). The corner map contains only the four
    # floor contacts incident to its five bodies; keep those subset counts
    # separate instead of mislabelling the mapped four as the full 100-cell set.
    require(len(corner_floor_normal_rows) == len(corner_floor_tangent_rows) == 4, "increment_corner_local_four_floor_contacts")
    require(len(active_corner_floor_rows) + len(inactive_corner_floor_rows) == len(corner_floor_tangent_rows), "increment_corner_local_floor_tangent_state_partition")
    require(len(source_increment.get("floor_normal_complementarity", {}).get("checks", [])) == 100, "increment_all_one_hundred_floor_normals_checked")
    normal_connection_names = {row.get("source_connection_name") for row in corner_floor_normal_rows}
    tangent_parent_connections = {str(row.get("source_connection_name", "")).removesuffix("_friction") for row in corner_floor_tangent_rows}
    require(normal_connection_names == tangent_parent_connections, "increment_corner_floor_normal_tangent_pairing")
    for row in corner_floor_tangent_rows:
        if row in active_corner_floor_rows:
            require(len(row.get("exact_floor_tangent_channels", [])) == 2 and not row.get("inactive_floor_tangent_zero_channels"), "increment_active_corner_floor_has_two_exact_tangent_channels")
        else:
            require(len(row.get("inactive_floor_tangent_zero_channels", [])) == 2 and not row.get("exact_floor_tangent_channels"), "increment_released_corner_floor_has_two_zero_tangent_channels")
    require(len(source_increment.get("exact_floor_tangent_reactions", [])) == branch["selected_source_tangent_row_count"], "increment_dynamic_local_active_tangent_channel_count")
    require(len(source_increment.get("inactive_floor_tangent_zero_actions", [])) == branch["inactive_source_tangent_row_count"], "increment_dynamic_local_inactive_tangent_channel_count")
    return {
        "corner_interface_count": len(interfaces),
        "contact_row_count": len(contacts),
        "physical_bolt_count": sum(row["physical_bolt_count"] for row in groups.values()),
        "lateral_plane_action_count": sum(row["lateral_plane_count"] for row in groups.values()),
        "outer_seat_tie_count": sum(row["outer_seat_tie_count"] for row in groups.values()),
        "washer_seat_count": len(projected["outer_washer_seats"]),
        "corner_body_balance_count": len(projected["corner_five_body_balance"]),
        "retained_original_arrangement_count": projected["retained_original_arrangement_count"],
        "retained_original_interface_row_count": len(projected["retained_original_leg_runner_interfaces"]),
        "case_selected_floor_normal_cell_count": branch["selected_cell_count"],
        "case_inactive_floor_normal_cell_count": branch["inactive_cell_count"],
        "case_floor_normal_cells_audited": len(source_increment.get("floor_normal_complementarity", {}).get("checks", [])),
        "corner_local_floor_contact_count": len(corner_floor_normal_rows),
        "corner_local_floor_selected_bearing_cell_count": len(active_corner_floor_rows),
        "corner_local_floor_released_separated_cell_count": len(inactive_corner_floor_rows),
        "local_floor_active_tangent_source_row_count": len(source_increment.get("exact_floor_tangent_reactions", [])),
        "local_floor_inactive_zero_tangent_source_row_count": len(source_increment.get("inactive_floor_tangent_zero_actions", [])),
        "all_signed_interface_vectors_retained": True,
        "member_wrenches_onward_transfer_retained": True,
        "floor_tangent_state_source": "response-zero-u-token.json only",
    }


def stabilize_corner_balance_sum_order(legacy: Any, projected: dict[str, Any], model: dict[str, Any],
                                       contract: dict[str, Any], interface_map: dict[str, Any],
                                       source_increment: dict[str, Any]) -> None:
    """Recompute only the five-body resultant sums in stable source-name order.

    The pinned legacy response mapper iterates an unordered set of floor-tangent
    connection names. That changes dictionary insertion order and therefore the
    final floating-point summation bits in its member-balance helper. Keep the
    legacy source untouched, but feed that same helper a source-name-sorted map.
    Per-interface response actions are unchanged.
    """
    response_rows = legacy.response_interfaces(source_increment, contract["interface_inventory"])
    stable_rows = {name: response_rows[name] for name in sorted(response_rows)}
    stable_balance = legacy.member_balance(
        model, contract, interface_map, stable_rows, float(source_increment["load_factor"])
    )
    require(set(stable_balance) == set(contract.get("corner_body_names", [])), "stable_balance_exact_five_corner_bodies")
    require(all(row.get("raw_balance_passed") is True and row.get("rounding_interval_balance_passed") is True
                for row in stable_balance.values()), "stable_balance_raw_and_interval_gates")
    projected["corner_five_body_balance"] = stable_balance
    projected["all_five_corner_bodies_raw_and_interval_balance_passed"] = True
    projected["corner_five_body_balance_sum_order"] = "source_connection_name ascending; pinned legacy member_balance helper"


def build_report(freeze: dict[str, Any], frozen_hashes: dict[str, str], legacy: Any) -> dict[str, Any]:
    model = load_json(ROOT / MODEL_PATH)
    response = load_json(ROOT / RESPONSE_PATH)
    context = load_json(ROOT / CONTEXT_PATH)
    contract_path = ROOT / BASE / "current-corner-demand-contract-attempt01/contract.json"
    map_path = ROOT / BASE / "current-corner-interface-recovery-map-attempt01/interface-map.json"
    contract = load_json(contract_path)
    interface_map = load_json(map_path)
    context_auth = context_binding(context, response, model, freeze)
    response_auth = validate_a1_response(model, response, freeze, contract, context)
    corner_source_auth = check_corner_sources(legacy, contract, interface_map)

    branch = model["floor_branch_metadata"]
    increments = []
    increment_shape_summaries = []
    for source_increment in response["increments"]:
        projected = legacy.build_increment(model, contract, interface_map, source_increment, "a1-rear")
        stabilize_corner_balance_sum_order(legacy, projected, model, contract, interface_map, source_increment)
        shape = summarize_increment(projected, source_increment, branch, contract)
        projected["case_bound_floor_state"] = {
            "branch_id": branch["branch_id"],
            "diagnostic_stage": branch.get("diagnostic_stage"),
            "selected_bearing_cells": branch["selected_cell_count"],
            "inactive_separated_cells": branch["inactive_cell_count"],
            "selected_tangent_source_rows": branch["selected_source_tangent_row_count"],
            "inactive_tangent_zero_source_rows": branch["inactive_source_tangent_row_count"],
            "normal_cells_checked": shape["case_floor_normal_cells_audited"],
            "corner_local_floor_contact_count": shape["corner_local_floor_contact_count"],
            "corner_local_floor_selected_bearing_cell_count": shape["corner_local_floor_selected_bearing_cell_count"],
            "corner_local_floor_released_separated_cell_count": shape["corner_local_floor_released_separated_cell_count"],
            "active_cell_ids_from_audited_response": source_increment["floor_normal_complementarity"]["selected_cell_ids"],
            "inactive_cell_ids_from_audited_response": source_increment["floor_normal_complementarity"]["inactive_cell_ids"],
            "diagnostic_screen_status": context["diagnostic_floor_screen_status"],
            "diagnostic_screen_forces_or_states_reused": False,
            "floor_support_physical_acceptance": False,
        }
        projected["increment_counts"] = shape
        increments.append(projected)
        increment_shape_summaries.append({
            "time": projected["time"],
            "load_factor": projected["load_factor"],
            **shape,
        })

    require(len(increments) == 7, "report_contains_all_seven_response_increments")
    primary_groups = increments[-1]["primary_physical_bolt_groups"]
    total_counts = {
        "corner_interfaces_per_increment": 338,
        "contact_rows_per_increment": 232,
        "physical_bolts": sum(group["physical_bolt_count"] for group in primary_groups.values()),
        "lateral_plane_actions": sum(group["lateral_plane_count"] for group in primary_groups.values()),
        "outer_seat_ties": sum(group["outer_seat_tie_count"] for group in primary_groups.values()),
        "washer_seats": len(increments[-1]["outer_washer_seats"]),
        "retained_original_arrangements": 12,
        "new_candidate_axis_count_separate_from_retained": 92,
        "local_floor_active_cells": branch["selected_cell_count"],
        "local_floor_inactive_cells": branch["inactive_cell_count"],
    }
    require(total_counts["physical_bolts"] == 6 and total_counts["lateral_plane_actions"] == 8 and total_counts["outer_seat_ties"] == 6 and total_counts["washer_seats"] == 12, "report_exact_bolt_plane_tie_washer_counts")

    input_freeze_sha = sha256(FREEZE_PATH)
    program_hash = sha256(Path(__file__).resolve())
    context_binding_output = {
        "case_id": "a1-rear",
        "source_case_register_path": str(REGISTER_PATH),
        "source_case_register_sha256": context_auth["register_sha256"],
        "case_record_sha256": context_auth["case_record_sha256"],
        "external_case_context_path": context_auth["external_case_context_path"],
        "external_case_context_sha256": context_auth["external_case_context_sha256"],
        "selected_input_model_sha256": sha256(MODEL_PATH),
        "selected_input_deck_sha256": sha256(DECK_PATH),
        "native_dat_sha256": sha256(DAT_PATH),
        "response_audit_path": str(RESPONSE_PATH),
        "response_audit_sha256": sha256(RESPONSE_PATH),
        "response_status": response["status"],
        "response_auditor_path": str(ZERO_U_AUDITOR_PATH),
        "response_auditor_sha256": ZERO_U_AUDITOR_SHA256,
        "parent_report_serialization_path": str(SERIALIZATION_PATH),
        "parent_report_serialization_sha256": sha256(SERIALIZATION_PATH),
        "source_controls": {
            "model_path": context["source_controls_model_json_path"],
            "model_sha256": context["source_controls_model_json_sha256"],
            "deck_path": context["source_controls_deck_path"],
            "deck_sha256": context["source_controls_deck_sha256"],
            "execution_path": context["source_controls_execution_path"],
            "execution_sha256": context["source_controls_execution_sha256"],
            "freeze_sha256": context["source_controls_freeze_sha256"],
        },
        "diagnostic_screen_context_only": {
            "path": context["diagnostic_floor_screen_path"],
            "sha256": context["diagnostic_floor_screen_sha256"],
            "status": context["diagnostic_floor_screen_status"],
            "screen_forces_or_states_reused": False,
        },
    }

    return {
        "schema": OUTPUT_SCHEMA,
        "status": "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY",
        "candidate": contract["candidate"],
        "geometry_revision_id": contract["geometry_revision_id"],
        "case_id": "a1-rear",
        "scope": "Source-bound left outer BG001/BG003/BG045 five-member assembly for one authenticated A1 selected-floor response.",
        "input_only_exporter": True,
        "native_solve_launched_by_exporter": False,
        "source_response_forces_promoted": True,
        "actual_case_demand_usable_for_conditional_joint_checks": True,
        "qualification_boundary": {
            "usable_scope": "Numerical demand input to pending conditional joint checks for this exact A1 case only.",
            "qualified_for_design": False,
            "complete_joint_accepted": False,
            "joint_resistance_accepted": False,
            "climbing_or_fabrication_release": False,
            "six_case_coverage_complete": False,
            "sensitivity_coverage_complete": False,
            "floor_slip_or_anchorage_qualified": False,
            "parent_terminal_assessment_consumed": False,
        },
        "projection_input_freeze": {
            "path": str(FREEZE_PATH),
            "sha256": input_freeze_sha,
            "source_file_count": freeze["source_file_count"],
            "source_file_set_canonical_sha256": freeze["source_file_set_canonical_sha256"],
            "projection_program_path": str(Path(__file__).resolve()),
            "projection_program_sha256": program_hash,
        },
        "authenticated_source_case": context_binding_output,
        "case_authority": context_auth,
        "source_contract": {
            "contract_sha256": corner_source_auth["contract_sha256"],
            "interface_map_sha256": corner_source_auth["interface_map_sha256"],
            "body_names": contract["corner_body_names"],
            "descriptor_midpoint_datums_mm": interface_map["descriptor_midpoint_datums_mm"],
            "datum_scope": interface_map["datum_scope"],
            "new_block_axis_count": contract["new_block_axis_count"],
            "retained_original_leg_runner_axis_count": contract["retained_original_leg_runner_axis_count"],
            "retained_original_axis_ids": corner_source_auth["retained_original_axis_ids"],
            "interface_inventory_count": corner_source_auth["interface_inventory_count"],
        },
        "selected_floor_response_scope": {
            "branch_id": branch["branch_id"],
            "diagnostic_stage": branch.get("diagnostic_stage"),
            "selected_bearing_cells": branch["selected_cell_count"],
            "inactive_separated_cells": branch["inactive_cell_count"],
            "active_exact_tangent_rows_per_increment": branch["selected_source_tangent_row_count"],
            "inactive_zero_tangent_rows_per_increment": branch["inactive_source_tangent_row_count"],
            "normal_cells_audited_per_increment": 100,
            "diagnostic_screen_status": context["diagnostic_floor_screen_status"],
            "diagnostic_screen_forces_or_states_reused": False,
            "response_branch_is_not_floor_or_joint_acceptance": True,
            "floor_slip_or_anchorage_qualified": False,
        },
        "response_audit_root_gates": response_auth["root_response_gates"],
        "response_audit_increment_count": response_auth["increment_count"],
        "response_audit_final_load_factor": response_auth["final_load_factor"],
        "parent_independent_all_body_response_audit": {
            "path": str(ALL_BODY_AUDIT_PATH),
            "sha256": response_auth["parent_all_body_response_audit_sha256"],
            "status": response_auth["parent_all_body_audit_status"],
            "increment_count": response_auth["parent_all_body_increment_count"],
            "physical_body_count_per_increment": response_auth["parent_all_body_count_per_increment"],
            "body_and_global_resultants_passed_each_increment": response_auth["parent_body_and_global_intervals_passed"],
            "joint_accepted": False,
        },
        "all_increment_count_summary": total_counts,
        "increment_shape_summaries": increment_shape_summaries,
        "conditional_reference_evidence": legacy.conditional_evidence(),
        "increments": increments,
        "limits": [
            "A1 forces are taken only from the pinned zero-U-token response audit and projected through the unchanged source-owned contract/interface map. No a12 force, selected mask, or active state is transferred.",
            "The rejected diagnostic screen remains context only; no positive force or active state from that screen is used. The A1 response's exact 46/54 normal-cell mask and 92/108 tangent-row partition are reported per increment.",
            "All 338 source-owned interfaces, six physical bolts, eight separate lateral planes, six outer-seat ties, 232 contacts, 12 washer seats, five-member balances, and seven increment force projections are retained. Twelve original LEG/FLOOR-RUNNER arrangements remain distinct from 92 new axes; their resistance is not reopened.",
            "BG003 has two continuous three-member bolts and two separate lateral planes per bolt. Signed plane actions remain separate; no plane capacities are summed or equal sharing is inferred from the demand projection.",
            "Contact pressures and washer annulus pressures are modeled geometry conversions only. Conditional resistance screens and geometry evidence are preserved as evidence, not promoted into A1 capacities.",
            "For deterministic last-bit output, the new case-bound wrapper recomputes five-body resultants with the unchanged pinned legacy member_balance helper after sorting source interface rows by connection name. This only fixes summation order; per-interface force vectors remain the audited A1 values.",
            "No design qualification, resistance, group capacity, accepted complete joint, verified floor, floor friction/anchor, fabrication approval, or climbing release is established. Parent owns final validation.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the pinned A1 numerical demand report")
    mode.add_argument("--verify", action="store_true", help="verify input pins and compare the committed A1 report")
    args = parser.parse_args()
    freeze, frozen_hashes = verify_frozen_sources()
    legacy_hash = freeze["source_file_sha256"].get(str(LEGACY_EXPORTER_PATH))
    require(isinstance(legacy_hash, str) and legacy_hash, "legacy_exporter_hash_present_in_freeze")
    legacy = import_legacy_exporter(legacy_hash)
    report = build_report(freeze, frozen_hashes, legacy)
    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    if args.write:
        OUTPUT_PATH.write_text(encoded, encoding="utf-8")
        print(f"{report['status']}: wrote {OUTPUT_PATH.relative_to(ROOT)}")
    else:
        saved = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
        if saved != json.loads(encoded):
            raise ProjectionBlocked("corner-demand-report.json differs from frozen A1 sources and legacy projection")
        print("verified A1 source context, 711 response, parent all-body audit, and all seven corner projections")


if __name__ == "__main__":
    try:
        main()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError) as error:
        print(f"BLOCKED_A1_CORNER_PROJECTION: {error}", file=sys.stderr)
        raise
