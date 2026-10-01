#!/usr/bin/env python3
"""Independently validate the a12-left input context with the pinned case auditor."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[6]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
SCREEN = HERE.parent / "a12-left-screen.json"
CONTROL = BASE / "current-springa-frame-a12-left-all-bearing-attempt01"
REGISTER = BASE / "current-six-case-source-load-register-attempt01/register.json"
AUDITOR = BASE / "current-springa-case-bound-response-audit-attempt01/response_audit.py"
EXPECTED_AUDITOR = "df1ed0eedb62ed3657a05a6d679d105e15e63b5ee18b999a731adab190b1b479"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> dict[str, Any]:
    model_path = HERE / "model.json"
    deck_path = HERE / "model.inp"
    context_path = HERE / "case-bound-input-context.json"
    contract_path = HERE / "case-bound-input-context-contract.json"
    pins_path = HERE / "source-pins.json"
    adapter_audit_path = HERE / "audit.json"
    deck_audit_path = HERE / "independent-deck-audit.json"
    require(sha(AUDITOR) == EXPECTED_AUDITOR, "Pinned case-bound response auditor changed")

    model = load(model_path)
    deck = deck_path.read_text(encoding="utf-8")
    context = load(context_path)
    context_contract = load(contract_path)
    pins = load(pins_path)
    adapter_audit = load(adapter_audit_path)
    deck_audit = load(deck_audit_path)
    screen = load(SCREEN)

    require(pins.get("schema") == "current_springa_selected_floor_input_source_pins/v1"
            and pins.get("case_id") == "a12-left"
            and pins.get("screen_stage") == "selected-proposal"
            and pins.get("output_model_sha256") == sha(model_path)
            and pins.get("output_deck_sha256") == sha(deck_path),
            "Adapter pin ledger does not bind the exact a12-left output")
    for relative, value in pins.get("input_pins", {}).items():
        path = ROOT / relative
        require(path.is_file() and sha(path) == value.get("sha256"),
                f"Input pin mismatch: {relative}")
    require(context_contract.get("schema") == "current_springa_case_bound_input_context_contract/v1"
            and context_contract.get("instance_schema") == "current_springa_case_bound_input_context/v1",
            "Case context contract schema changed")
    missing = [key for key in context_contract.get("required_context_fields", [])
               if context.get(key) is None]
    require(not missing, f"Required context fields are missing: {missing}")
    require(context.get("case_id") == model.get("case_id") == screen.get("case_id") == "a12-left"
            and context.get("candidate") == model.get("candidate")
            and context.get("geometry_revision_id") == model.get("geometry_revision_id"),
            "Model, screen, and context case identity differs")
    require(context.get("source_controls_model_json_path") == str((CONTROL / "model.json").relative_to(ROOT))
            and context.get("source_controls_model_json_sha256") == sha(CONTROL / "model.json")
            and context.get("source_controls_deck_path") == str((CONTROL / "model.inp").relative_to(ROOT))
            and context.get("source_controls_deck_sha256") == sha(CONTROL / "model.inp")
            and context.get("source_case_load_register_path") == str(REGISTER.relative_to(ROOT))
            and context.get("source_case_load_register_sha256") == sha(REGISTER),
            "A12-left context is not bound to its original all-bearing controls and canonical load register")
    require(context.get("diagnostic_floor_screen_path") == str(SCREEN.relative_to(ROOT))
            and context.get("diagnostic_floor_screen_sha256") == sha(SCREEN)
            and context.get("diagnostic_floor_screen_status") == screen.get("status")
            and context.get("diagnostic_floor_screen_case_id") == "a12-left",
            "Context does not bind the exact projected a12-left screen")
    require(context.get("input_only") is True
            and context.get("native_solve_executed") is False
            and context.get("screen_positive_forces_or_active_states_reused_as_response") is False
            and context.get("mechanical_acceptance") is False,
            "Case context claims response adoption, native execution, or acceptance")
    proposed = set(screen.get("diagnostic_positive_cells_at_final_time", []))
    inactive = set(screen.get("diagnostic_separating_cells_at_final_time", []))
    require(len(proposed) == 11 and len(inactive) == 89 and proposed.isdisjoint(inactive)
            and proposed | inactive == {
                str(binding["name"]) for binding in load(CONTROL / "model.json")["unilateral_springa_bindings"]
                if binding.get("physical_owner", {}).get("role") == "floor_normal"
            }, "Projected floor mask is not the strict a12-left 11/89 partition")
    require(set(model.get("floor_selected_bearing_cells", [])) == proposed
            and model.get("input_only") is True
            and model.get("native_solve_executed") is False
            and model.get("mechanical_acceptance") is False,
            "Selected model differs from its diagnostic mask or makes an acceptance claim")
    require(adapter_audit.get("status") == "PASS_SELECTED_FLOOR_INPUT_ALGEBRA_AND_SOURCE_PRESERVATION"
            and deck_audit.get("status") == "PASS_PARENT_SELECTED_FLOOR_SERIALIZED_INPUT_AUDIT"
            and deck_audit.get("no_geometry_law_load_or_material_change") is True
            and deck_audit.get("candidate_bolt_axes") == 92
            and deck_audit.get("retained_leg_runner_axes") == 12
            and deck_audit.get("hillman_axes") == 66
            and deck_audit.get("corner_demands_usable") is False,
            "Adapter or independent serialized-deck audit gate changed")

    spec = importlib.util.spec_from_file_location("pinned_case_bound_response_auditor", AUDITOR)
    require(spec is not None and spec.loader is not None, "Cannot load pinned case-context validator")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    context_check = validator._validate_case_context(context)
    response_contract = validator._validate_model(model, deck, context)
    inventory = response_contract["inventory_summary"]
    expected_inventory = {
        "source_carrier_rows": 1840,
        "native_springa_rows": 1292,
        "retained_bilateral_spring2_rows": 348,
        "selected_floor_tangent_reaction_rows": 22,
        "inactive_floor_tangent_rows_without_restraint": 178,
        "selected_bearing_cells": 11,
        "inactive_separated_cells": 89,
        "physical_body_count": 50,
        "new_candidate_bolt_axes": 92,
        "retained_leg_runner_bolt_axes": 12,
        "panel_screw_axes": 66,
        "legacy_linear_auditor_reused": False,
    }
    require(all(inventory.get(key) == value for key, value in expected_inventory.items()),
            "Independent response-auditor input inventory differs from the 11/89 proposal")
    require(context_check["case_id"] == "a12-left"
            and context_check["screen_status"] == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
            and context_check["selected_cell_count"] == 11
            and context_check["inactive_cell_count"] == 89,
            "Independent context audit returned a different case/mask")

    result = {
        "schema": "current_springa_a12_left_independent_context_audit/v1",
        "status": "PASS_A12_LEFT_CASE_BOUND_INPUT_CONTEXT_ONLY",
        "case_id": "a12-left",
        "native_solve_launched_by_audit": False,
        "native_response_consumed": False,
        "mechanical_acceptance": False,
        "corner_demands_usable": False,
        "input_model_sha256": sha(model_path),
        "input_deck_sha256": sha(deck_path),
        "case_context_sha256": sha(context_path),
        "case_context_contract_sha256": sha(contract_path),
        "adapter_source_pins_sha256": sha(pins_path),
        "case_bound_response_auditor_sha256": sha(AUDITOR),
        "source_controls_model_sha256": sha(CONTROL / "model.json"),
        "source_controls_deck_sha256": sha(CONTROL / "model.inp"),
        "source_load_register_sha256": sha(REGISTER),
        "diagnostic_screen_sha256": sha(SCREEN),
        "independent_deck_audit_sha256": sha(deck_audit_path),
        "case_context_provenance": {
            "case_record_sha256": context_check["case_record_sha256"],
            "source_model_inputs_sha256": context_check["source_model_inputs_sha256"],
            "diagnostic_floor_screen_status": context_check["screen_status"],
            "selected_branch_id": context["selected_floor_branch_id"],
        },
        "source_inventory": inventory,
        "input_context_check": {
            "all_required_context_fields_present": True,
            "source_pins_match": True,
            "source_case_geometry_loads_laws_materials_bound_to_a12_left": True,
            "rejected_response_forces_adopted": False,
            "other_case_response_states_reused": False,
        },
        "limits": [
            "Input contract and context only; no selected-branch native response was run or audited.",
            "The 11/89 floor classification is a one-case proposal basis from a12-left's rejected selected-10 interval diagnostic, not accepted support.",
            "No corner demand, floor qualification, resistance, mechanical acceptance, or joint acceptance is established.",
        ],
        "producer_sha256": sha(Path(__file__)),
    }
    output = HERE / "independent-context-audit.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return result


if __name__ == "__main__":
    main()
