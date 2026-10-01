#!/usr/bin/env python3
"""Validate one generic case-bound response input without promoting forces.

The adapter checks the external case context and an already-produced strict
case-bound response audit. It emits provenance and gate status only; corner
force export remains blocked until the separately reviewed demand projector
consumes this authenticated input.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True


ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
HERE = Path(__file__).resolve().parent
AUDITOR_PATH = BASE / "current-springa-case-bound-response-audit-attempt01/response_audit.py"
AUDITOR_SHA256 = "df1ed0eedb62ed3657a05a6d679d105e15e63b5ee18b999a731adab190b1b479"
REGISTER_PATH = BASE / "current-six-case-source-load-register-attempt01/register.json"
REGISTER_SHA256 = "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508"
CONTRACT_PATH = BASE / "current-corner-demand-contract-attempt01/contract.json"
CONTRACT_SHA256 = "f09d341924b2aa4e50ad8ecea43e4fcd1a36d838c99ab4e0fb85712e7dfd6c74"
INTERFACE_MAP_PATH = BASE / "current-corner-interface-recovery-map-attempt01/interface-map.json"
INTERFACE_MAP_SHA256 = "c5ce97cbe1fffbb18dfaf1a544fa9a300991b06056b21b37ba3e08b8a1c6aec8"
OUTPUT_SCHEMA = "current_corner_case_bound_export_input/v1"
REQUIRED_ROOT_GATES = (
    "mpc_interval_checks_passed",
    "springa_law_checks_passed",
    "retained_bilateral_checks_passed",
    "selected_floor_complementarity_passed",
    "inactive_floor_tangent_no_restraint_or_reaction_passed",
    "raw_body_and_global_balance_passed",
    "rounding_interval_body_and_global_balance_passed",
)
REQUIRED_INCREMENT_GATES = (
    "mpc_interval_checks_passed",
    "springa_law_checks_passed",
    "retained_bilateral_checks_passed",
    "selected_floor_complementarity_passed",
    "inactive_floor_tangent_no_restraint_or_reaction_passed",
    "raw_balance_passed",
    "rounding_interval_balance_passed",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def import_auditor():
    path = ROOT / AUDITOR_PATH
    if not path.is_file() or sha256(path) != AUDITOR_SHA256:
        raise ValueError("pinned_case_bound_response_auditor_source_sha256")
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("pinned_case_bound_response_auditor", path)
    if spec is None or spec.loader is None:
        raise ValueError("pinned_case_bound_response_auditor_importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def blocked(response_path: Path | None, blockers: list[str], response: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema": OUTPUT_SCHEMA,
        "status": "BLOCKED_CASE_BOUND_RESPONSE_INPUT",
        "input_only_adapter": True,
        "response_forces_promoted": False,
        "corner_demands_exported": False,
        "increments": [],
        "response_force_rows": [],
        "blockers": sorted(set(blockers)),
        "observed_input": {
            "response_audit_path": str(response_path.resolve()) if response_path and response_path.is_file() else None,
            "response_audit_sha256": sha256(response_path) if response_path and response_path.is_file() else None,
            "response_schema": response.get("schema") if response else None,
            "response_status": response.get("status") if response else None,
            "case_id": response.get("case_id") if response else None,
        },
        "claim_boundary": "No force or demand values are emitted until the pinned generic auditor, external case context, and response report bind to one another.",
    }


def validate_inputs(context_path: Path | None, response_path: Path) -> dict[str, Any]:
    blockers: list[str] = []
    response: dict[str, Any] | None = None
    if not response_path.is_file():
        return blocked(response_path, ["response_audit_file_exists"])
    try:
        response = load_json(response_path)
    except (OSError, json.JSONDecodeError):
        return blocked(response_path, ["response_audit_is_readable_json"])

    if context_path is None:
        return blocked(response_path, [
            "external_generic_case_context_file_required",
            "historical_a12_response_has_no_generic_case_context_hash_or_provenance",
        ], response)
    if not context_path.is_file():
        return blocked(response_path, ["external_generic_case_context_file_exists"], response)

    try:
        auditor = import_auditor()
        context = load_json(context_path)
        case_pin = auditor._validate_case_context(context)
        model_path = auditor._context_path(context["selected_input_model_json_path"])
        deck_path = auditor._context_path(context["selected_input_deck_path"])
        model = load_json(model_path)
        deck = deck_path.read_text(encoding="utf-8")
        auditor._validate_model(model, deck, context)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, AttributeError) as error:
        detail = str(error) or type(error).__name__
        return blocked(response_path, [f"generic_case_context_and_selected_input_validate:{detail}"], response)

    if not (ROOT / REGISTER_PATH).is_file() or sha256(ROOT / REGISTER_PATH) != REGISTER_SHA256:
        blockers.append("pinned_six_case_source_load_register_sha256")
    if not (ROOT / CONTRACT_PATH).is_file() or sha256(ROOT / CONTRACT_PATH) != CONTRACT_SHA256:
        blockers.append("pinned_complete_corner_demand_contract_sha256")
    if not (ROOT / INTERFACE_MAP_PATH).is_file() or sha256(ROOT / INTERFACE_MAP_PATH) != INTERFACE_MAP_SHA256:
        blockers.append("pinned_corner_interface_recovery_map_sha256")

    context_hash = sha256(context_path)
    if response.get("schema") != "current_springa_selected_floor_physical_response_audit/v1":
        blockers.append("response_schema_is_pinned_case_bound_physical_audit")
    if response.get("status") != "PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY":
        blockers.append("response_status_is_strict_pass")
    if response.get("case_id") != context.get("case_id"):
        blockers.append("response_case_id_matches_external_context")
    if response.get("candidate") != context.get("candidate"):
        blockers.append("response_candidate_matches_external_context")
    if response.get("geometry_revision_id") != context.get("geometry_revision_id"):
        blockers.append("response_geometry_revision_matches_external_context")
    if response.get("branch_id") != context.get("selected_floor_branch_id"):
        blockers.append("response_selected_floor_branch_matches_external_context")
    if response.get("case_context_path") != str(context_path.resolve()):
        blockers.append("response_case_context_path_matches_external_context")
    if response.get("case_context_sha256") != context_hash:
        blockers.append("response_case_context_sha256_matches_external_context")
    if response.get("source_input_model_json_sha256") != sha256(model_path):
        blockers.append("response_input_model_sha256_matches_context_selected_model")
    if response.get("source_input_model_json_path") != str(model_path.resolve()):
        blockers.append("response_input_model_path_matches_context_selected_model")
    if response.get("source_model_record_canonical_sha256") != canonical_sha256(model):
        blockers.append("response_canonical_model_hash_matches_context_selected_model")
    if response.get("source_input_deck_sha256") != sha256(deck_path):
        blockers.append("response_input_deck_sha256_matches_context_selected_deck")
    if response.get("native_output_consumed") is not True or response.get("native_solve_launched_by_postprocessor") is not False:
        blockers.append("response_is_read_only_audit_of_consumed_native_output")
    for claim in ("qualified_for_design", "mechanical_acceptance", "joint_demand_accepted", "floor_capacity_established", "friction_qualified", "historical_c11_forces_or_active_states_used"):
        if response.get(claim) is not False:
            blockers.append(f"response_claim_boundary:{claim}")
    data_path_value = response.get("native_data_path")
    if not isinstance(data_path_value, str):
        blockers.append("response_native_data_path_present")
    else:
        data_path = Path(data_path_value)
        if not data_path.is_file() or sha256(data_path) != response.get("native_data_sha256"):
            blockers.append("response_native_data_path_and_sha256_match")
        observed_data = response.get("terminal_execution_provenance", {}).get("observed_file_sha256", {})
        if observed_data.get("model.dat") != response.get("native_data_sha256"):
            blockers.append("response_native_data_hash_matches_terminal_execution_record")
    if any(response.get(key) is not True for key in REQUIRED_ROOT_GATES):
        blockers.extend(f"response_root_gate:{key}" for key in REQUIRED_ROOT_GATES if response.get(key) is not True)
    summary = response.get("recovery_summary", {})
    if any(summary.get(key) is not True for key in REQUIRED_ROOT_GATES):
        blockers.extend(f"response_recovery_summary_gate:{key}" for key in REQUIRED_ROOT_GATES if summary.get(key) is not True)
    provenance = response.get("case_context_provenance", {})
    expected_provenance = {
        "case_id": case_pin["case_id"],
        "case_record_sha256": case_pin["case_record_sha256"],
        "source_model_inputs_sha256": case_pin["source_model_inputs_sha256"],
        "register_path": case_pin["register_path"],
        "register_sha256": case_pin["register_sha256"],
        "controls_model_path": case_pin["controls_model_path"],
        "controls_model_sha256": case_pin["controls_model_sha256"],
        "controls_deck_path": case_pin["controls_deck_path"],
        "controls_deck_sha256": case_pin["controls_deck_sha256"],
        "screen_path": case_pin["screen_path"],
        "screen_sha256": case_pin["screen_sha256"],
        "screen_status": case_pin["screen_status"],
    }
    for key, expected in expected_provenance.items():
        if provenance.get(key) != expected:
            blockers.append(f"response_case_context_provenance:{key}")
    terminal_gates = response.get("terminal_execution_provenance", {}).get("gates", {})
    if not terminal_gates or any(value is not True for value in terminal_gates.values()):
        blockers.append("response_terminal_execution_provenance_all_gates_pass")
    increments = response.get("increments")
    if not isinstance(increments, list) or not increments:
        blockers.append("response_increments_nonempty")
    else:
        if any(any(row.get(key) is not True for key in REQUIRED_INCREMENT_GATES) for row in increments):
            blockers.append("response_every_increment_strict_gates_pass")
        if abs(float(increments[-1].get("load_factor", -1.0)) - 1.0) > 1e-8:
            blockers.append("response_final_load_factor_equals_one")
        body_names = set(json.loads((ROOT / CONTRACT_PATH).read_text())["corner_body_names"])
        for index, row in enumerate(increments):
            balance = row.get("physical_balance", {})
            if set(balance.get("body_equilibrium", {})) < body_names:
                blockers.append(f"response_increment_{index}_all_corner_body_balances_present")
            for body, audit in balance.get("body_equilibrium", {}).items():
                if body in body_names and (audit.get("printed_resultants_passed") is not True or audit.get("interval_resultants_passed") is not True):
                    blockers.append(f"response_increment_{index}_body_balance_passed:{body}")
            global_audit = balance.get("global_equilibrium", {})
            if global_audit.get("printed_resultants_passed") is not True or global_audit.get("interval_resultants_passed") is not True:
                blockers.append(f"response_increment_{index}_global_balance_passed")

    if blockers:
        return blocked(response_path, blockers, response)
    return {
        "schema": OUTPUT_SCHEMA,
        "status": "PASS_CASE_BOUND_RESPONSE_INPUT_READY_NO_FORCE_PROMOTION",
        "input_only_adapter": True,
        "response_forces_promoted": False,
        "corner_demands_exported": False,
        "increments": [],
        "response_force_rows": [],
        "case_binding": {
            "case_id": case_pin["case_id"],
            "case_record_sha256": case_pin["case_record_sha256"],
            "source_load_register_path": case_pin["register_path"],
            "source_load_register_sha256": case_pin["register_sha256"],
            "case_context_path": str(context_path.resolve()),
            "case_context_sha256": context_hash,
            "response_audit_path": str(response_path.resolve()),
            "response_audit_sha256": sha256(response_path),
            "selected_input_model_path": str(model_path.resolve()),
            "selected_input_model_sha256": sha256(model_path),
            "selected_input_deck_path": str(deck_path.resolve()),
            "selected_input_deck_sha256": sha256(deck_path),
            "generic_response_auditor_path": str(AUDITOR_PATH),
            "generic_response_auditor_sha256": AUDITOR_SHA256,
            "increment_count": len(increments),
            "final_load_factor": increments[-1]["load_factor"],
            "corner_body_balance_gates_passed": True,
        },
        "next_scope": "This boundary authenticates one already-passed case-bound response. It does not project response forces into a corner-demand report.",
        "claim_boundary": "No capacity, joint acceptance, floor qualification, or design release is established.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-context", type=Path, help="external context accepted by the pinned case-bound auditor")
    parser.add_argument("--response-audit", type=Path, required=True, help="already-passed case-bound response audit JSON")
    parser.add_argument("--output", type=Path, default=HERE / "case-bound-export-input.json")
    args = parser.parse_args()
    try:
        report = validate_inputs(args.case_context, args.response_audit)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
        report = blocked(args.response_audit, [f"case_bound_response_input_readable_and_valid:{type(error).__name__}"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(report["status"])


if __name__ == "__main__":
    main()
