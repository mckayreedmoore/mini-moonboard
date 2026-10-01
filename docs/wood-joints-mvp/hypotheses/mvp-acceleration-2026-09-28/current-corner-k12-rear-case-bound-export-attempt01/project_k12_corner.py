#!/usr/bin/env python3
"""Project only an authenticated, parent-passed K12-rear response to the corner map.

This packet does not run CalculiX.  ``--preflight`` authenticates the pinned
SPR489 direct-master input and the unchanged corner mapping sources without
reading response forces.  ``--export`` is deliberately gated on the exact
future native packet, the sealed SPR489 response audit, the parent 50-body
audit, and the parent terminal assessment.  It then reuses the A1-rear corner
mapper without transferring any A1/a12/K12 historical response values.
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

INPUT_DIR = BASE / "current-springa-k12-rear-spr489-direct-master-input-attempt02"
MODEL_PATH = INPUT_DIR / "model.json"
DECK_PATH = INPUT_DIR / "model.inp"
INPUT_AUDIT_PATH = INPUT_DIR / "input-audit.json"
INPUT_PINS_PATH = INPUT_DIR / "source-pins.json"

# Parent-owned future run directory.  This producer never creates, freezes,
# modifies, or launches that run directory.
RUN_DIR = BASE / "current-k12-rear-spr489-direct-native-attempt01"
RUN_MODEL_PATH = RUN_DIR / "model.json"
RUN_DECK_PATH = RUN_DIR / "model.inp"
RUN_DAT_PATH = RUN_DIR / "model.dat"
RUN_CONTEXT_PATH = RUN_DIR / "case-context.json"
RUN_FREEZE_PATH = RUN_DIR / "freeze.json"
RUN_EXECUTION_PATH = RUN_DIR / "execution.json"
RUN_RESPONSE_PATH = RUN_DIR / "response.json"
RUN_ALL_BODY_AUDIT_PATH = RUN_DIR / "audit.json"
RUN_TERMINAL_ASSESSMENT_PATH = RUN_DIR / "parent-terminal-assessment.json"

REGISTER_PATH = BASE / "current-six-case-source-load-register-attempt01/register.json"
SCREEN_PATH = BASE / "current-springa-case-bound-floor-input-adapter-attempt08/screen.json"
METHOD_REVIEW_PATH = BASE / "current-k12-rear-direct-parent-method-review-attempt01/review.json"
ALL_BODY_CHECKER_PATH = BASE / "current-k12-rear-direct-parent-all50-method-attempt01/check.py"
RESPONSE_CORE_PATH = BASE / "current-k12-rear-spr489-direct-response-audit-attempt02/response_core.py"
DIRECT_MASTER_VALIDATOR_PATH = BASE / "current-k12-rear-spr489-direct-response-audit-attempt02/validate_direct_master_input.py"
PINNED_711_WRAPPER_PATH = BASE / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py"
PINNED_711_RECOVERY_PATH = BASE / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"

CORNER_CONTRACT_PATH = BASE / "current-corner-demand-contract-attempt01/contract.json"
INTERFACE_MAP_PATH = BASE / "current-corner-interface-recovery-map-attempt01/interface-map.json"
ONWARD_REGISTER_PATH = BASE / "current-corner-left-leg-onward-transfer-register-attempt01/register.json"

A1_HELPER_PATH = BASE / "current-corner-a1-rear-case-bound-export-attempt01/project_a1_corner.py"
A1_FREEZE_PATH = BASE / "current-corner-a1-rear-case-bound-export-attempt01/projection-freeze.json"
LEGACY_EXPORTER_PATH = BASE / "current-corner-native-demand-export-attempt03/produce.py"

PREFLIGHT_PATH = HERE / "preflight.json"
SOURCE_PINS_PATH = HERE / "source-pins.json"
PROJECTION_FREEZE_PATH = HERE / "projection-freeze.json"
REPORT_PATH = HERE / "corner-demand-report.json"

EXPECTED = {
    str(MODEL_PATH): "8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd",
    str(DECK_PATH): "6c6f8dc02616d3b92dda2f15db1a196e47935233e47eee0afaa56fda694fd3aa",
    str(INPUT_AUDIT_PATH): "c593c94d206c6798b190d3b42b4956aaa898a503dfe11a1303b20a126266d8cf",
    str(INPUT_PINS_PATH): "470a89b3d354790216e095e2f0a57e3348c9660c091898f4c9bf621e980a0b96",
    str(REGISTER_PATH): "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508",
    str(SCREEN_PATH): "5300dd51d50f22308f57fd06b2ee1f026cb04944ad62a7ab959834dfd61f084d",
    str(METHOD_REVIEW_PATH): "168bd55bd3e2e76d13ddd3726630d645e0e5e3913443165381f765fbee612318",
    str(ALL_BODY_CHECKER_PATH): "7c9f0ecaa0e305934c812710d73a9c26d7b33e56891f2488e8bfe9c1c8c6823c",
    str(RESPONSE_CORE_PATH): "87e8624661fb30fd8d0ec23fee51ad421045bafaade0736f05439a26578ea1d8",
    str(DIRECT_MASTER_VALIDATOR_PATH): "ad01699a7f354d060e4a9f89be358285f84c57d30ba417d6aa1592cc868cf555",
    str(PINNED_711_WRAPPER_PATH): "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0",
    str(PINNED_711_RECOVERY_PATH): "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
    str(CORNER_CONTRACT_PATH): "f09d341924b2aa4e50ad8ecea43e4fcd1a36d838c99ab4e0fb85712e7dfd6c74",
    str(INTERFACE_MAP_PATH): "c5ce97cbe1fffbb18dfaf1a544fa9a300991b06056b21b37ba3e08b8a1c6aec8",
    str(ONWARD_REGISTER_PATH): "b435f23d059d8b8399bcc5ab4afdbaa71171bac476b3a50953d68f8189cac8b0",
    str(A1_HELPER_PATH): "fc0b1985d053a90a1019529f0dc55abf4cd6f77141a608dd2a951ccf954cc21e",
    str(A1_FREEZE_PATH): "34e019237ac44cd5c26b4fc3b982c503b198890bea45e170fe5a11f53f44c97c",
    str(LEGACY_EXPORTER_PATH): "0e6aa1b0ec50e3137d2f431f79365de899d109a5d5c61d37de344c9596681fe8",
}

CASE_ID = "k12-rear"
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
BRANCH_ID = "monotone_zero_gap_first_bearing_reference_zero"
METHOD_VARIANT = "spr489_direct_c3d20_master_interpolation/v1"
REPORT_SCHEMA = "current_corner_k12_rear_spr489_direct_master_case_bound_demand_report/v1"
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
LEFT_LEG_AXES = {"lumber_leg_bolt_left_1", "lumber_leg_bolt_left_2"}


class ExportBlocked(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExportBlocked(f"expected_json_object:{path}")
    return value


def require(condition: bool, name: str) -> None:
    if not condition:
        raise ExportBlocked(name)


def absolute(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def import_file(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    if spec is None or spec.loader is None:
        raise ExportBlocked(f"source_importable:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Any, Any]:
    observed: dict[str, str] = {}
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        require(path.is_file(), f"pinned_source_exists:{relative}")
        actual = sha256(path)
        require(actual == expected, f"pinned_source_hash:{relative}")
        observed[relative] = actual

    model = load_json(ROOT / MODEL_PATH)
    input_audit = load_json(ROOT / INPUT_AUDIT_PATH)
    variant_pins = load_json(ROOT / INPUT_PINS_PATH)
    contract = load_json(ROOT / CORNER_CONTRACT_PATH)
    interface_map = load_json(ROOT / INTERFACE_MAP_PATH)
    register = load_json(ROOT / REGISTER_PATH)
    onward = load_json(ROOT / ONWARD_REGISTER_PATH)
    screen = load_json(ROOT / SCREEN_PATH)
    review = load_json(ROOT / METHOD_REVIEW_PATH)

    require(model.get("schema") == "current_springa_selected_floor_input_model/v1", "input_model_schema")
    require(model.get("case_id") == CASE_ID and model.get("candidate") == CANDIDATE
            and model.get("geometry_revision_id") == REVISION, "input_model_case_candidate_revision")
    method = model.get("input_method_variant", {})
    require(method.get("schema") == "current_springa_direct_master_qghost_method_variant/v1"
            and method.get("variant_id") == METHOD_VARIANT and method.get("source_row_id") == "SPR489"
            and method.get("source_inventory_row_index") == 488, "exact_spr489_direct_master_method_variant")
    require(method.get("affected_equation_indices_zero_based") == [19433, 19434]
            and method.get("affected_equation_dependent_dofs") == [[19800, 2], [19800, 3]]
            and method.get("all_other_equations_preserved") is True
            and method.get("source_projection_inventory_preserved") is True
            and method.get("carrier_geometry_axis_spring_and_table_preserved") is True,
            "only_two_spr489_qghost_equations_replaced")
    require(model.get("frame_ready_for_native_run") is False and model.get("native_solve_executed") is False
            and model.get("mechanical_acceptance") is False and model.get("complete_joint_validated") is False,
            "source_input_remains_input_only")
    require(model.get("legacy_reduced_static_linear_response_schema_compatible") is False,
            "nonlinear_model_disallows_legacy_linear_response_schema")

    branch = model.get("floor_branch_metadata", {})
    require(branch.get("branch_id") == BRANCH_ID and branch.get("case_id") == CASE_ID
            and branch.get("selected_cell_count") == 23 and branch.get("inactive_cell_count") == 77
            and branch.get("selected_source_tangent_row_count") == 46
            and branch.get("inactive_source_tangent_row_count") == 154,
            "pinned_k12_23_77_floor_branch")
    require(branch.get("status") == "proposed_diagnostic_mask_only"
            and branch.get("physical_force_adoption") is False
            and branch.get("selected_branch_screen_outputs_adopted") is False
            and branch.get("positive_set_stable_at_all_7_printed_states") is True,
            "floor_mask_remains_diagnostic_and_nonadopted")
    require(branch.get("screen_packet_path") == str(SCREEN_PATH)
            and branch.get("screen_packet_sha256") == sha256(ROOT / SCREEN_PATH)
            and branch.get("selected_branch_screen_status") == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH",
            "selected_mask_is_bound_to_its_own_rejected_screen")
    selected_cells = set(branch.get("selected_cells", []))
    inactive_cells = set(branch.get("inactive_cells", []))
    selected_rows = set(map(int, model.get("floor_selected_original_row_indices", [])))
    inactive_rows = set(map(int, model.get("floor_inactive_original_row_indices", [])))
    require(screen.get("schema") == "current_case_bound_floor_diagnostic_screen/v1"
            and screen.get("status") == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
            and screen.get("case_id") == CASE_ID and screen.get("candidate") == CANDIDATE
            and screen.get("geometry_revision_id") == REVISION
            and screen.get("same_positive_cell_set_at_all_printed_times") is True
            and screen.get("corner_demands_usable") is False
            and screen.get("screen_forces_or_active_states_adopted") is False,
            "source_screen_is_rejected_context_only")
    screen_positive_sets: list[set[str]] = []
    screen_inactive_sets: list[set[str]] = []
    for state in screen.get("states", []):
        rows = state.get("rows", [])
        screen_positive_sets.append({row["cell_name"] for row in rows if row.get("strictly_positive_after_rounding") is True})
        screen_inactive_sets.append({row["cell_name"] for row in rows if row.get("strictly_separating_after_rounding") is True})
        require(len(rows) == 100 and state.get("bearing_count") == 23
                and state.get("separating_count") == 77 and state.get("ambiguous_or_unresolved_count") == 0,
                "source_screen_each_state_23_77_zero_ambiguity")
    require(len(screen_positive_sets) == len(screen_inactive_sets) == 7
            and all(cells == selected_cells for cells in screen_positive_sets)
            and all(cells == inactive_cells for cells in screen_inactive_sets),
            "source_screen_all_seven_state_sets_match_proposed_mask")
    require(len(selected_cells) == 23 and len(inactive_cells) == 77 and selected_cells.isdisjoint(inactive_cells)
            and selected_cells | inactive_cells == {row["cell_name"] for row in screen["states"][0]["rows"]},
            "floor_cell_partition_exact_and_screen_bound")
    require(len(selected_rows) == 46 and len(inactive_rows) == 154 and selected_rows.isdisjoint(inactive_rows)
            and selected_rows | inactive_rows == set(range(200)), "floor_original_row_partition_46_154")
    require(input_audit.get("schema") == "current_spr489_direct_master_frame_input_audit/v1"
            and input_audit.get("status") == "PASS_EXACT_SPR489_DIRECT_MASTER_INPUT_ARITHMETIC_ONLY",
            "direct_master_input_arithmetic_audit_pass")
    require(input_audit.get("emitted_model_sha256") == sha256(ROOT / MODEL_PATH)
            and input_audit.get("emitted_deck_sha256") == sha256(ROOT / DECK_PATH)
            and input_audit.get("all_other_model_json_equation_records_exactly_preserved") is True
            and input_audit.get("all_deck_lines_outside_two_replaced_equation_cards_identical") is True,
            "direct_master_input_audit_binds_exact_model_and_deck")
    require(input_audit.get("reviewed_axis_counts") == {
        "hillman_axes": 66,
        "new_block_bolt_axes": 92,
        "retained_original_leg_runner_arrangements": 12,
    }, "reviewed_66_92_12_axis_inventory")

    require(register.get("status") == "PASS_FRESH_SIX_CASE_SOURCE_LOAD_WRENCH_REGISTER"
            and register.get("candidate") == CANDIDATE and register.get("geometry_revision_id") == REVISION,
            "current_fresh_case_load_register")
    cases = [row for row in register.get("cases", []) if row.get("case_id") == CASE_ID]
    require(len(cases) == 1, "register_has_exact_k12_rear_case")
    case_record_sha = canonical_sha256(cases[0])
    identity = model.get("case_bound_source_identity", {})
    load_binding = model.get("source_load_register_binding", {})
    require(identity.get("case_record_sha256") == case_record_sha
            and load_binding.get("case_record_sha256") == case_record_sha
            and identity.get("source_model_inputs_sha256") == cases[0].get("source_model_inputs_sha256")
            and load_binding.get("physical_external_load_map_sha256") == cases[0].get("physical_external_load_map", {}).get("sha256"),
            "fresh_k12_case_source_load_identity")
    require(identity.get("source_case_load_register_sha256") == sha256(ROOT / REGISTER_PATH)
            and load_binding.get("register_sha256") == sha256(ROOT / REGISTER_PATH)
            and model.get("source_model_inputs_sha256") == cases[0].get("source_model_inputs_sha256"),
            "fresh_k12_load_register_sha256_and_source_inputs")

    require(review.get("status") == "PASS_PARENT_EXACT_INPUT_AND_UNCHANGED_PHYSICAL_GATES_REVIEW"
            and review.get("changed_model_equation_rows") == [19433, 19434]
            and review.get("all_physical_audit_statements_unchanged_except_scoped_callback") is True
            and review.get("direct_spring_geometric_law_intervals_and_physical_action_statements_unchanged") is True
            and review.get("native_solve_executed") is False
            and review.get("mechanical_acceptance") is False,
            "parent_review_passes_only_exact_spr489_method_input")
    review_sources = review.get("source_sha256", {})
    for path, expected in ((ROOT / MODEL_PATH, EXPECTED[str(MODEL_PATH)]),
                           (ROOT / DECK_PATH, EXPECTED[str(DECK_PATH)]),
                           (ROOT / INPUT_AUDIT_PATH, EXPECTED[str(INPUT_AUDIT_PATH)]),
                           (ROOT / RESPONSE_CORE_PATH, EXPECTED[str(RESPONSE_CORE_PATH)]),
                           (ROOT / DIRECT_MASTER_VALIDATOR_PATH, EXPECTED[str(DIRECT_MASTER_VALIDATOR_PATH)])):
        require(review_sources.get(str(path)) == expected, f"parent_method_review_binds:{path.name}")

    require(contract.get("candidate") == CANDIDATE and contract.get("geometry_revision_id") == REVISION
            and len(contract.get("interface_inventory", [])) == 338 and len(contract.get("corner_body_names", [])) == 5,
            "corner_contract_source_identity_and_size")
    groups = contract.get("primary_new_corner_groups", {})
    require(set(groups) == {"BG001", "BG003", "BG045"}, "corner_primary_groups_bg001_bg003_bg045")
    new_axes = {axis for row in groups.values() for axis in row.get("axis_ids", [])}
    retained_axes = set(contract.get("retained_original_axis_ids", []))
    require(len(new_axes) == 6 and len(retained_axes) == 12 and new_axes.isdisjoint(retained_axes)
            and contract.get("new_block_axis_count") == 92
            and contract.get("retained_original_leg_runner_axis_count") == 12,
            "six_corner_bolts_and_92_new_axes_distinct_from_12_retained")
    require(interface_map.get("geometry_revision_id") == REVISION, "interface_map_current_revision")
    require(onward.get("schema") == "current_corner_left_leg_onward_transfer_register/v1"
            and onward.get("status") == "CONDITIONAL_SIGNED_ONWARD_ACTIONS_ONLY"
            and onward.get("joint_accepted") is False
            and onward.get("new_block_axes_in_register") == [], "onward_register_is_conditional_and_not_rewritten")
    require(set(LEFT_LEG_AXES).issubset(set(onward.get("retained_original_axes", []))),
            "onward_register_separately_identifies_two_affected_left_leg_axes")
    # No K12 forces, masks, or accepted demands are read from this older register.
    require(not any(row.get("case_id") == CASE_ID for row in onward.get("rows", [])),
            "no_prior_k12_left_leg_force_transfer")

    a1 = import_file("pinned_a1_corner_export_helpers", A1_HELPER_PATH)
    a1_freeze = load_json(ROOT / A1_FREEZE_PATH)
    legacy_hash = a1_freeze.get("source_file_sha256", {}).get(str(LEGACY_EXPORTER_PATH))
    require(legacy_hash == EXPECTED[str(LEGACY_EXPORTER_PATH)], "a1_freeze_pins_unchanged_legacy_mapper")
    legacy = a1.import_legacy_exporter(legacy_hash)
    source_review = a1.check_corner_sources(legacy, contract, interface_map)
    validator = import_file("pinned_spr489_direct_master_validator", DIRECT_MASTER_VALIDATOR_PATH)
    validated_contract = validator.validate_input_contract(ROOT / MODEL_PATH, ROOT / DECK_PATH)
    observed[str(HERE.relative_to(ROOT) / Path(__file__).name)] = sha256(Path(__file__).resolve())
    return {
        "model": model,
        "branch": branch,
        "case_record": cases[0],
        "case_record_sha256": case_record_sha,
        "contract": contract,
        "interface_map": interface_map,
        "legacy": legacy,
        "a1_helpers": a1,
        "validator": validator,
        "validated_input_contract": validated_contract,
        "corner_source_review": source_review,
        "source_hashes": observed,
        "source_register_sha256": sha256(ROOT / REGISTER_PATH),
        "onward_register_sha256": sha256(ROOT / ONWARD_REGISTER_PATH),
        "selected_cells": sorted(selected_cells),
        "inactive_cells": sorted(inactive_cells),
        "selected_rows": sorted(selected_rows),
        "inactive_rows": sorted(inactive_rows),
    }


def write_preflight(static: dict[str, Any]) -> dict[str, Any]:
    pins = {
        "schema": "current_corner_k12_rear_spr489_direct_master_export_source_pins/v1",
        "scope": "Static inputs and producer only; no response force output, native execution, or force adoption.",
        "static_source_file_sha256": static["source_hashes"],
        "input_case": {
            "case_id": CASE_ID,
            "candidate": CANDIDATE,
            "geometry_revision_id": REVISION,
            "case_record_sha256": static["case_record_sha256"],
            "method_variant": METHOD_VARIANT,
            "input_model_sha256": sha256(ROOT / MODEL_PATH),
            "input_deck_sha256": sha256(ROOT / DECK_PATH),
            "input_arithmetic_audit_sha256": sha256(ROOT / INPUT_AUDIT_PATH),
            "input_source_pins_sha256": sha256(ROOT / INPUT_PINS_PATH),
        },
        "future_native_packet": {
            "path": str(RUN_DIR),
            "response_audit_path": str(RUN_RESPONSE_PATH),
            "all_body_audit_path": str(RUN_ALL_BODY_AUDIT_PATH),
            "parent_terminal_assessment_path": str(RUN_TERMINAL_ASSESSMENT_PATH),
            "run_input_must_be_byte_identical_to_pinned_method_input": True,
        },
        "corner_source": static["corner_source_review"],
        "reviewed_geometry_inventory": {
            "new_block_bolt_axes": 92,
            "retained_original_leg_runner_arrangements": 12,
            "hillman_panel_kicker_axes": 66,
            "primary_groups": ["BG001", "BG003", "BG045"],
            "primary_physical_bolts": 6,
            "lateral_plane_actions": 8,
            "outer_seat_ties": 6,
            "washer_seats": 12,
            "all_corner_interfaces": 338,
            "contact_rows": 232,
            "physical_bodies": 50,
        },
        "floor_proposal": {
            "branch_id": BRANCH_ID,
            "screen_path": str(SCREEN_PATH),
            "screen_sha256": sha256(ROOT / SCREEN_PATH),
            "screen_status": static["branch"].get("selected_branch_screen_status"),
            "selected_cells": static["selected_cells"],
            "inactive_cells": static["inactive_cells"],
            "selected_original_row_indices": static["selected_rows"],
            "inactive_original_row_indices": static["inactive_rows"],
            "mask_is_diagnostic_not_accepted": True,
            "screen_forces_or_active_states_reused": False,
        },
        "readiness": {
            "native_run_launched_by_exporter": False,
            "native_input_frozen_by_exporter": False,
            "response_consumed": False,
            "corner_demands_usable": False,
            "force_adoption": False,
            "mechanical_acceptance": False,
            "joint_accepted": False,
        },
    }
    preflight = {
        "schema": "current_corner_k12_rear_export_static_preflight/v1",
        "status": "PASS_STATIC_INPUT_AND_CORNER_SOURCE_PREFLIGHT_ONLY",
        "source_pins_path": str(SOURCE_PINS_PATH.relative_to(ROOT)),
        "source_pins_sha256": canonical_sha256(pins),
        "source_pins": pins,
        "limitations": [
            "No K12 native response exists in this packet until the parent-owned run is complete.",
            "No K12 forces or active states are read from a12, A1, or rejected earlier K12 packets.",
            "Projection remains blocked until the direct-master response audit, parent 50-body audit, and parent terminal assessment all bind the exact future run inputs and pass.",
        ],
    }
    for path, value in ((SOURCE_PINS_PATH, pins), (PREFLIGHT_PATH, preflight)):
        require(not path.exists(), f"write_once_output:{path.name}")
        path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return preflight


def validate_future_run(static: dict[str, Any]) -> dict[str, Any]:
    required_paths = (RUN_MODEL_PATH, RUN_DECK_PATH, RUN_DAT_PATH, RUN_CONTEXT_PATH, RUN_FREEZE_PATH,
                      RUN_EXECUTION_PATH, RUN_RESPONSE_PATH, RUN_ALL_BODY_AUDIT_PATH,
                      RUN_TERMINAL_ASSESSMENT_PATH)
    missing = [str(path) for path in required_paths if not (ROOT / path).is_file()]
    require(not missing, "parent_run_or_response_gates_missing:" + ",".join(missing))
    for path, expected in ((RUN_MODEL_PATH, EXPECTED[str(MODEL_PATH)]),
                           (RUN_DECK_PATH, EXPECTED[str(DECK_PATH)])):
        require(sha256(ROOT / path) == expected, f"future_run_input_byte_identical:{path.name}")

    model = load_json(ROOT / RUN_MODEL_PATH)
    response = load_json(ROOT / RUN_RESPONSE_PATH)
    context = load_json(ROOT / RUN_CONTEXT_PATH)
    execution = load_json(ROOT / RUN_EXECUTION_PATH)
    freeze = load_json(ROOT / RUN_FREEZE_PATH)
    body_audit = load_json(ROOT / RUN_ALL_BODY_AUDIT_PATH)
    terminal = load_json(ROOT / RUN_TERMINAL_ASSESSMENT_PATH)
    require(model == static["model"], "future_run_model_record_exactly_matches_attempt02")
    require(model.get("case_id") == CASE_ID and response.get("case_id") == CASE_ID
            and context.get("case_id") == CASE_ID, "future_run_case_id_k12_rear")
    require(response.get("schema") == "current_k12_rear_spr489_direct_master_physical_response_audit/v1"
            and response.get("status") == "PASS_K12_REAR_SPR489_DIRECT_MASTER_RESPONSE_AUDIT_ONLY",
            "sealed_direct_master_response_schema_and_status")
    require(response.get("candidate") == CANDIDATE and response.get("geometry_revision_id") == REVISION,
            "response_candidate_and_reviewed_revision")
    require(response.get("source_input_model_json_sha256") == sha256(ROOT / RUN_MODEL_PATH)
            and response.get("source_input_deck_sha256") == sha256(ROOT / RUN_DECK_PATH)
            and response.get("native_data_sha256") == sha256(ROOT / RUN_DAT_PATH)
            and response.get("source_model_record_canonical_sha256") == canonical_sha256(model),
            "response_exact_model_deck_and_DAT_hashes")
    require(response.get("source_input_model_json_path") == str((ROOT / RUN_MODEL_PATH).resolve())
            and response.get("source_input_deck_path") == str((ROOT / RUN_DECK_PATH).resolve())
            and response.get("native_data_path") == str((ROOT / RUN_DAT_PATH).resolve())
            and response.get("case_context_path") == str((ROOT / RUN_CONTEXT_PATH).resolve())
            and response.get("case_context_sha256") == sha256(ROOT / RUN_CONTEXT_PATH),
            "response_exact_run_and_context_paths")
    require(response.get("native_output_consumed") is True
            and response.get("native_solve_launched_by_postprocessor") is False
            and response.get("mechanical_acceptance") is False
            and response.get("joint_demand_accepted") is False
            and response.get("qualified_for_design") is False
            and response.get("historical_c11_forces_or_active_states_used") is False,
            "response_is_audited_numeric_only_and_uses_no_historical_response")
    method = response.get("response_method_variant_provenance", {})
    require(method.get("variant_id") == METHOD_VARIANT and method.get("source_row_id") == "SPR489"
            and method.get("source_inventory_row_index") == 488
            and method.get("changed_q_equation_dependent_dofs") == [[19800, 2], [19800, 3]]
            and method.get("input_audit_sha256") == sha256(ROOT / INPUT_AUDIT_PATH)
            and method.get("only_spr489_source_q_mean_and_radius_use_direct_master_map") is True
            and method.get("all_other_native_law_and_physical_recovery_methods_are_pinned_711") is True,
            "response_exact_direct_master_method_provenance")
    context_result = static["validator"].validate_variant_run_context(
        static["validated_input_contract"], context,
        model_path=ROOT / RUN_MODEL_PATH, deck_path=ROOT / RUN_DECK_PATH,
    )
    context_prov = response.get("case_context_provenance", {})
    require(context_prov.get("variant_context_was_parent_created_and_consumed") is True
            and context_prov.get("run_context_synthesized_by_auditor") is False
            and context_prov.get("context_case_id") == CASE_ID
            and context_result.get("case_id") == CASE_ID,
            "parent_created_exact_run_context_consumed_by_sealed_response_audit")
    expected_terminal = {
        "execution_sha256": sha256(ROOT / RUN_EXECUTION_PATH),
        "freeze_sha256": sha256(ROOT / RUN_FREEZE_PATH),
        "returncode": 0,
        "container_confirmed_terminal": True,
        "native_output_hashes_match": True,
        "solver_error_markers_absent": True,
    }
    terminal_prov = response.get("terminal_execution_provenance", {})
    for key, expected in expected_terminal.items():
        require(terminal_prov.get(key) == expected, f"response_terminal_execution_provenance:{key}")
    require(execution.get("native_solve_executed") is True and execution.get("returncode") == 0
            and execution.get("container_confirmed_terminal") is True,
            "parent_native_run_terminal_zero")
    require(freeze.get("candidate") == CANDIDATE and freeze.get("geometry_revision_id") == REVISION
            and freeze.get("case_id") == CASE_ID
            and freeze.get("native_solve_executed") is False
            and freeze.get("mechanical_acceptance") is False
            and freeze.get("files_sha256", {}).get("model.json") == sha256(ROOT / RUN_MODEL_PATH)
            and freeze.get("files_sha256", {}).get("model.inp") == sha256(ROOT / RUN_DECK_PATH),
            "parent_freeze_binds_exact_input_only_variant")

    for key in ROOT_GATES:
        require(response.get(key) is True, f"direct_response_root_gate:{key}")
        require(response.get("recovery_summary", {}).get(key) is True, f"direct_response_recovery_gate:{key}")
    increments = response.get("increments")
    require(isinstance(increments, list) and len(increments) == 7
            and math.isclose(float(increments[-1].get("load_factor", -1)), 1.0, rel_tol=0.0, abs_tol=1.0e-8),
            "response_has_all_seven_printed_increments_and_full_load")
    active_cells = set(static["branch"].get("selected_cells", []))
    inactive_cells = set(static["branch"].get("inactive_cells", []))
    selected_rows = set(static["selected_rows"])
    inactive_rows = set(static["inactive_rows"])
    for index, inc in enumerate(increments):
        for key in INCREMENT_GATES:
            require(inc.get(key) is True, f"response_increment_{index}_gate:{key}")
        normal = inc.get("floor_normal_complementarity", {})
        require(normal.get("selected_bearing_cell_count") == 23
                and normal.get("inactive_separated_cell_count") == 77
                and set(normal.get("selected_cell_ids", [])) == active_cells
                and set(normal.get("inactive_cell_ids", [])) == inactive_cells
                and len(normal.get("checks", [])) == 100,
                f"response_increment_{index}_same_exact_23_77_normal_state")
        active_tangent = inc.get("exact_floor_tangent_reactions", [])
        inactive_tangent = inc.get("inactive_floor_tangent_zero_actions", [])
        require(len(active_tangent) == 46 and {row.get("source_row_original_index") for row in active_tangent} == selected_rows
                and len(inactive_tangent) == 154
                and {row.get("source_row_original_index") for row in inactive_tangent} == inactive_rows,
                f"response_increment_{index}_exact_46_154_floor_row_partition")
        balance = inc.get("physical_balance", {})
        for body in static["contract"].get("corner_body_names", []):
            body_row = balance.get("body_equilibrium", {}).get(body)
            require(isinstance(body_row, dict) and body_row.get("printed_resultants_passed") is True
                    and body_row.get("interval_resultants_passed") is True,
                    f"response_increment_{index}_corner_body_balance:{body}")
        global_row = balance.get("global_equilibrium", {})
        require(global_row.get("printed_resultants_passed") is True
                and global_row.get("interval_resultants_passed") is True,
                f"response_increment_{index}_global_balance")

    require(body_audit.get("status") == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS"
            and body_audit.get("source_model_sha256") == sha256(ROOT / RUN_MODEL_PATH)
            and body_audit.get("source_response_sha256") == sha256(ROOT / RUN_RESPONSE_PATH),
            "parent_all50_audit_binds_exact_fresh_response")
    body_increments = body_audit.get("increments", [])
    require(len(body_increments) == 7, "parent_all50_audit_seven_increments")
    for index, item in enumerate(body_increments):
        require(item.get("body_count") == 50 and len(item.get("body_equilibrium", {})) == 50
                and item.get("passed") is True
                and all(row.get("printed_resultants_passed") is True and row.get("interval_resultants_passed") is True
                        for row in item.get("body_equilibrium", {}).values())
                and item.get("global_equilibrium", {}).get("printed_resultants_passed") is True
                and item.get("global_equilibrium", {}).get("interval_resultants_passed") is True,
                f"parent_all50_audit_increment_{index}")

    require(terminal.get("status") == "PASS_PARENT_K12_REAR_DIRECT_RESPONSE_AND_ALL50"
            and terminal.get("case_id") == CASE_ID
            and terminal.get("candidate") == CANDIDATE and terminal.get("geometry_revision_id") == REVISION
            and terminal.get("response_usable_for_conditional_joint_checks") is True
            and terminal.get("native_increment_count") == 7 and terminal.get("physical_body_count") == 50
            and terminal.get("strict_bearing_floor_cells") == 23
            and terminal.get("strict_inactive_floor_cells") == 77
            and terminal.get("native_table_checks_passed") == 9044
            and terminal.get("independent_body_and_global_balances_passed") is True
            and terminal.get("input_method_variant") == METHOD_VARIANT
            and terminal.get("only_two_native_equations_changed") is True
            and terminal.get("automatic_mask_iteration_used") is False
            and terminal.get("mechanical_acceptance") is False
            and terminal.get("complete_joint_resistance_established") is False
            and terminal.get("six_case_envelope_established") is False
            and terminal.get("floor_friction_or_anchorage_qualified") is False,
            "parent_terminal_assessment_explicitly_allows_only_conditional_case_demands")
    terminal_hashes = terminal.get("files_sha256", {})
    for name, path in (("model.json", RUN_MODEL_PATH), ("model.inp", RUN_DECK_PATH),
                       ("model.dat", RUN_DAT_PATH), ("freeze.json", RUN_FREEZE_PATH),
                       ("execution.json", RUN_EXECUTION_PATH), ("case-context.json", RUN_CONTEXT_PATH),
                       ("response.json", RUN_RESPONSE_PATH), ("audit.json", RUN_ALL_BODY_AUDIT_PATH)):
        require(terminal_hashes.get(name) == sha256(ROOT / path), f"parent_terminal_assessment_binds:{name}")
    for source_path, source_hash in terminal.get("postprocessing_sources_sha256", {}).items():
        path = Path(source_path)
        require(path.is_file() and sha256(path) == source_hash,
                f"parent_terminal_assessment_binds_postprocessor:{source_path}")

    return {
        "model": model,
        "response": response,
        "context": context,
        "execution": execution,
        "freeze": freeze,
        "all_body_audit": body_audit,
        "terminal_assessment": terminal,
        "run_context_proof": context_result,
        "increments": increments,
        "source_hashes": {str(path): sha256(ROOT / path) for path in required_paths},
    }


def make_report(static: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    model = run["model"]
    response = run["response"]
    branch = model["floor_branch_metadata"]
    contract = static["contract"]
    interface_map = static["interface_map"]
    legacy = static["legacy"]
    a1 = static["a1_helpers"]
    increments: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    left_leg_action_rows: list[dict[str, Any]] = []
    for index, source_increment in enumerate(run["increments"]):
        projected = legacy.build_increment(model, contract, interface_map, source_increment, CASE_ID)
        a1.stabilize_corner_balance_sum_order(legacy, projected, model, contract, interface_map, source_increment)
        shape = a1.summarize_increment(projected, source_increment, branch, contract)
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
            "diagnostic_screen_status": branch["selected_branch_screen_status"],
            "diagnostic_screen_forces_or_states_reused": False,
            "floor_support_physical_acceptance": False,
        }
        projected["increment_counts"] = shape
        left_leg_rows = [row for row in projected["retained_original_leg_runner_interfaces"]
                         if row.get("axis_id") in LEFT_LEG_AXES]
        require(len(left_leg_rows) == 4, f"increment_{index}_two_left_leg_axes_four_source_interfaces")
        require({row.get("axis_id") for row in left_leg_rows} == LEFT_LEG_AXES,
                f"increment_{index}_both_left_leg_axes_present")
        projected["affected_left_leg_original_axis_actions"] = left_leg_rows
        projected["affected_left_leg_resistance_reopened"] = False
        left_leg_action_rows.append({
            "time": projected["time"],
            "load_factor": projected["load_factor"],
            "axes": {axis: [row for row in left_leg_rows if row.get("axis_id") == axis]
                     for axis in sorted(LEFT_LEG_AXES)},
            "source": "fresh K12 direct-master audited response only",
            "resistance_reopened": False,
        })
        increments.append(projected)
        summaries.append({"time": projected["time"], "load_factor": projected["load_factor"], **shape})

    require(len(increments) == 7, "report_has_seven_fresh_k12_increments")
    groups = increments[-1]["primary_physical_bolt_groups"]
    counts = {
        "corner_interfaces_per_increment": len(increments[-1]["all_corner_interfaces"]),
        "contact_rows_per_increment": len(increments[-1]["member_contact_bearing"]["contact_cells"]),
        "physical_bolts": sum(item["physical_bolt_count"] for item in groups.values()),
        "lateral_plane_actions": sum(item["lateral_plane_count"] for item in groups.values()),
        "outer_seat_ties": sum(item["outer_seat_tie_count"] for item in groups.values()),
        "washer_seats": len(increments[-1]["outer_washer_seats"]),
        "retained_original_arrangements": 12,
        "new_candidate_axis_count_separate_from_retained": 92,
        "hillman_panel_kicker_axes": 66,
        "floor_active_cells": branch["selected_cell_count"],
        "floor_inactive_cells": branch["inactive_cell_count"],
    }
    require(counts == {
        "corner_interfaces_per_increment": 338,
        "contact_rows_per_increment": 232,
        "physical_bolts": 6,
        "lateral_plane_actions": 8,
        "outer_seat_ties": 6,
        "washer_seats": 12,
        "retained_original_arrangements": 12,
        "new_candidate_axis_count_separate_from_retained": 92,
        "hillman_panel_kicker_axes": 66,
        "floor_active_cells": 23,
        "floor_inactive_cells": 77,
    }, "all_expected_corner_and_source_counts")

    sources = {
        "input_model_path": str(MODEL_PATH),
        "input_model_sha256": sha256(ROOT / MODEL_PATH),
        "input_deck_path": str(DECK_PATH),
        "input_deck_sha256": sha256(ROOT / DECK_PATH),
        "input_audit_path": str(INPUT_AUDIT_PATH),
        "input_audit_sha256": sha256(ROOT / INPUT_AUDIT_PATH),
        "method_source_pins_path": str(INPUT_PINS_PATH),
        "method_source_pins_sha256": sha256(ROOT / INPUT_PINS_PATH),
        "fresh_case_register_path": str(REGISTER_PATH),
        "fresh_case_register_sha256": static["source_register_sha256"],
        "fresh_case_record_sha256": static["case_record_sha256"],
        "response_context_path": str(RUN_CONTEXT_PATH),
        "response_context_sha256": sha256(ROOT / RUN_CONTEXT_PATH),
        "native_model_path": str(RUN_MODEL_PATH),
        "native_model_sha256": sha256(ROOT / RUN_MODEL_PATH),
        "native_deck_path": str(RUN_DECK_PATH),
        "native_deck_sha256": sha256(ROOT / RUN_DECK_PATH),
        "native_dat_path": str(RUN_DAT_PATH),
        "native_dat_sha256": sha256(ROOT / RUN_DAT_PATH),
        "response_audit_path": str(RUN_RESPONSE_PATH),
        "response_audit_sha256": sha256(ROOT / RUN_RESPONSE_PATH),
        "response_auditor_path": str(RESPONSE_CORE_PATH),
        "response_auditor_sha256": sha256(ROOT / RESPONSE_CORE_PATH),
        "all_body_audit_path": str(RUN_ALL_BODY_AUDIT_PATH),
        "all_body_audit_sha256": sha256(ROOT / RUN_ALL_BODY_AUDIT_PATH),
        "parent_terminal_assessment_path": str(RUN_TERMINAL_ASSESSMENT_PATH),
        "parent_terminal_assessment_sha256": sha256(ROOT / RUN_TERMINAL_ASSESSMENT_PATH),
        "method_review_path": str(METHOD_REVIEW_PATH),
        "method_review_sha256": sha256(ROOT / METHOD_REVIEW_PATH),
        "corner_contract_sha256": sha256(ROOT / CORNER_CONTRACT_PATH),
        "interface_map_sha256": sha256(ROOT / INTERFACE_MAP_PATH),
        "onward_register_sha256": static["onward_register_sha256"],
        "legacy_mapper_sha256": sha256(ROOT / LEGACY_EXPORTER_PATH),
        "projection_helper_sha256": sha256(Path(__file__).resolve()),
    }
    return {
        "schema": REPORT_SCHEMA,
        "status": "PASS_K12_REAR_NUMERICAL_CORNER_DEMAND_REPORT_ONLY",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "case_id": CASE_ID,
        "scope": "Fresh source-bound K12-rear numerical demand projection for the complete left-outer BG001/BG003/BG045 five-member corner and its affected two left-leg bolt axes.",
        "method_variant": METHOD_VARIANT,
        "input_only_exporter": True,
        "native_solve_launched_by_exporter": False,
        "force_source": "Fresh K12 direct-master response audit only; no prior case response, force, or active floor state is transferred.",
        "actual_case_demand_usable_for_conditional_joint_checks": True,
        "qualification_boundary": {
            "conditional_numerical_demand_only": True,
            "qualified_for_design": False,
            "complete_joint_accepted": False,
            "joint_resistance_accepted": False,
            "climbing_or_fabrication_release": False,
            "six_case_coverage_complete": False,
            "sensitivity_coverage_complete": False,
            "floor_slip_or_anchorage_qualified": False,
            "parent_terminal_assessment_consumed": True,
            "retained_original_leg_runner_resistance_reopened": False,
        },
        "authenticated_sources": sources,
        "fresh_source_case": {
            "case_record_sha256": static["case_record_sha256"],
            "source_model_inputs_sha256": model.get("source_model_inputs_sha256"),
            "fresh_case_load_and_body_wrench_match_register": model.get("source_load_register_binding", {}).get("fresh_source_load_and_body_wrenches_match_register"),
            "historical_response_forces_used": False,
            "load_register_not_modified_or_used_as_response": True,
        },
        "source_contract": {
            "corner_contract_sha256": sha256(ROOT / CORNER_CONTRACT_PATH),
            "interface_map_sha256": sha256(ROOT / INTERFACE_MAP_PATH),
            "corner_body_names": contract["corner_body_names"],
            "new_block_axis_count": 92,
            "retained_original_leg_runner_axis_count": 12,
            "retained_original_axis_ids": sorted(contract["retained_original_axis_ids"]),
            "interface_inventory_count": 338,
            "primary_groups": ["BG001", "BG003", "BG045"],
            "six_physical_bolts_eight_separate_planes_six_outer_seat_ties_twelve_washer_seats": True,
        },
        "selected_floor_response_scope": {
            "branch_id": BRANCH_ID,
            "diagnostic_stage": branch.get("diagnostic_stage"),
            "screen_status": branch.get("selected_branch_screen_status"),
            "screen_path": str(SCREEN_PATH),
            "screen_sha256": sha256(ROOT / SCREEN_PATH),
            "selected_bearing_cells": branch["selected_cell_count"],
            "inactive_separated_cells": branch["inactive_cell_count"],
            "active_tangent_rows_per_increment": branch["selected_source_tangent_row_count"],
            "inactive_tangent_rows_per_increment": branch["inactive_source_tangent_row_count"],
            "diagnostic_screen_forces_or_states_reused": False,
            "floor_support_physical_acceptance": False,
        },
        "direct_master_response_audit": {
            "status": response["status"],
            "root_gates": {key: response.get(key) for key in ROOT_GATES},
            "increment_count": len(run["increments"]),
            "final_load_factor": run["increments"][-1]["load_factor"],
            "method_provenance": response["response_method_variant_provenance"],
            "mechanical_acceptance": False,
            "joint_demand_accepted": False,
        },
        "parent_independent_all_50_body_audit": {
            "status": run["all_body_audit"]["status"],
            "audit_path": str(RUN_ALL_BODY_AUDIT_PATH),
            "increment_count": len(run["all_body_audit"]["increments"]),
            "body_count_each_increment": 50,
            "all_body_and_global_interval_sums_passed": True,
            "joint_accepted": False,
        },
        "parent_terminal_assessment": {
            "status": run["terminal_assessment"]["status"],
            "conditional_case_forces_usable": True,
            "corner_demands_usable": True,
            "mechanical_acceptance": False,
            "joint_accepted": False,
        },
        "onward_transfer_scope": {
            "baseline_register_path": str(ONWARD_REGISTER_PATH),
            "baseline_register_sha256": static["onward_register_sha256"],
            "affected_original_left_leg_axes": sorted(LEFT_LEG_AXES),
            "per_increment_action_rows": left_leg_action_rows,
            "original_arrangement_count_remains_12": True,
            "old_resistance_requalified": False,
        },
        "all_increment_count_summary": counts,
        "increment_shape_summaries": summaries,
        "conditional_reference_evidence": legacy.conditional_evidence(),
        "increments": increments,
        "limits": [
            "Every signed corner interface, member contact row, and owner-datum force/moment action comes from the seven-increment fresh K12 direct-master response after the sealed response gates and the parent's 50-body audit and terminal assessment pass.",
            "The original 92 new block-bolt axes remain distinct from the twelve retained original LEG/FLOOR-RUNNER arrangements; this report separately exposes only the two affected left-leg bolt axes and does not reopen blanket resistance qualification of old axes.",
            "The six primary bolts, eight lateral planes, six outer-seat ties, 12 washer seats, all 338 corner interfaces, and 232 contact rows are retained. Signed plane actions remain separate; no capacity or equal-sharing assumption is inferred.",
            "The 23/77 selected-floor state is conditional to the audited monotone zero-gap branch and this exact K12 run. It establishes no recontact, uniqueness, floor friction, floor anchorage, or physical floor capacity.",
            "This numerical demand export does not establish joint resistance, complete-joint acceptance, design qualification, fabrication approval, or climbing release.",
        ],
    }


def freeze_record(static: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    files = dict(static["source_hashes"])
    files.update(run["source_hashes"])
    files[str(Path(__file__).resolve().relative_to(ROOT))] = sha256(Path(__file__).resolve())
    return {
        "schema": "current_corner_k12_rear_case_bound_projection_freeze/v1",
        "status": "FROZEN_AFTER_PARENT_RESPONSE_AND_ALL50_GATES_BEFORE_EXPORT",
        "case_id": CASE_ID,
        "scope": "One response-derived K12-rear corner projection only; not a native input freeze.",
        "source_file_sha256": dict(sorted(files.items())),
        "source_file_count": len(files),
        "source_file_set_canonical_sha256": canonical_sha256(dict(sorted(files.items()))),
        "response_status": run["response"]["status"],
        "parent_all_body_status": run["all_body_audit"]["status"],
        "parent_terminal_status": run["terminal_assessment"]["status"],
        "native_solve_launched_by_exporter": False,
        "force_output_written_before_all_gates": False,
        "mechanical_acceptance": False,
        "joint_accepted": False,
    }


def verify_frozen_projection(static: dict[str, Any], run: dict[str, Any]) -> None:
    require(PROJECTION_FREEZE_PATH.is_file() and REPORT_PATH.is_file(), "projection_freeze_and_report_exist")
    freeze = load_json(ROOT / PROJECTION_FREEZE_PATH)
    require(freeze.get("schema") == "current_corner_k12_rear_case_bound_projection_freeze/v1"
            and freeze.get("status") == "FROZEN_AFTER_PARENT_RESPONSE_AND_ALL50_GATES_BEFORE_EXPORT",
            "projection_freeze_scope")
    for relative, expected in freeze.get("source_file_sha256", {}).items():
        path = ROOT / relative
        require(path.is_file() and sha256(path) == expected, f"frozen_projection_source:{relative}")
    expected_freeze_set = canonical_sha256(freeze.get("source_file_sha256", {}))
    require(expected_freeze_set == freeze.get("source_file_set_canonical_sha256"), "projection_freeze_set_digest")
    expected_report = make_report(static, run)
    expected_report["projection_input_freeze"] = {
        "path": str(PROJECTION_FREEZE_PATH.relative_to(ROOT)),
        "sha256": sha256(ROOT / PROJECTION_FREEZE_PATH),
        "source_file_count": freeze["source_file_count"],
        "source_file_set_canonical_sha256": freeze["source_file_set_canonical_sha256"],
        "projection_program_path": str(Path(__file__).resolve().relative_to(ROOT)),
        "projection_program_sha256": sha256(Path(__file__).resolve()),
    }
    saved = load_json(ROOT / REPORT_PATH)
    require(saved == expected_report, "saved_corner_report_matches_authenticated_reprojection")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true", help="write static input/source audit only; no response forces")
    mode.add_argument("--export", action="store_true", help="write report only after fresh response and parent audits pass")
    mode.add_argument("--verify", action="store_true", help="revalidate all gates and compare a previously written report")
    args = parser.parse_args()
    static = load_sources()
    if args.preflight:
        result = write_preflight(static)
        print(f"{result['status']}: {PREFLIGHT_PATH.relative_to(ROOT)}")
        return
    require(SOURCE_PINS_PATH.is_file() and PREFLIGHT_PATH.is_file(), "static_preflight_must_be_written_first")
    pins = load_json(ROOT / SOURCE_PINS_PATH)
    require(pins.get("schema") == "current_corner_k12_rear_spr489_direct_master_export_source_pins/v1"
            and pins.get("static_source_file_sha256", {}).get(str(HERE.relative_to(ROOT) / Path(__file__).name))
            == sha256(Path(__file__).resolve()), "preflight_pins_current_producer_source")
    run = validate_future_run(static)
    if args.verify:
        verify_frozen_projection(static, run)
        print("verified current K12-rear direct-master response, parent all-50 gate, and all seven corner demand projections")
        return
    require(not PROJECTION_FREEZE_PATH.exists() and not REPORT_PATH.exists(), "projection_outputs_are_write_once")
    report = make_report(static, run)
    freeze = freeze_record(static, run)
    freeze_path = ROOT / PROJECTION_FREEZE_PATH
    freeze_path.write_text(json.dumps(freeze, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    report["projection_input_freeze"] = {
        "path": str(PROJECTION_FREEZE_PATH.relative_to(ROOT)),
        "sha256": sha256(freeze_path),
        "source_file_count": freeze["source_file_count"],
        "source_file_set_canonical_sha256": freeze["source_file_set_canonical_sha256"],
        "projection_program_path": str(Path(__file__).resolve().relative_to(ROOT)),
        "projection_program_sha256": sha256(Path(__file__).resolve()),
    }
    (ROOT / REPORT_PATH).write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(f"{report['status']}: wrote {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError) as error:
        print(f"BLOCKED_K12_REAR_CORNER_EXPORT: {error}", file=sys.stderr)
        raise
