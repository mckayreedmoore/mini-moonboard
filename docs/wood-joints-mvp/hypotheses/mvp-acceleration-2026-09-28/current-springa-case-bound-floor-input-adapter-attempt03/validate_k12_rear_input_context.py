#!/usr/bin/env python3
"""Run the pinned case-bound input-only validator on this K12-rear proposal."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
INPUT = BASE / "current-springa-case-bound-floor-input-adapter-attempt03/k12-rear"
AUDITOR = BASE / "current-springa-case-bound-response-audit-attempt01/response_audit.py"
OUTPUT = INPUT / "input_contract_check.json"

PINS = {
    INPUT / "model.json": "ecd1f05c2d42ebd208ee348457aa0f04c91774c4dfa5c5c349905f92c398d1fe",
    INPUT / "model.inp": "ff515e7006fc223e89df245f7bf31cda337611ac75c981df8d1b7cafebf0d691",
    INPUT / "case-bound-input-context.json": "133fe328dc00df1aac93fb183408c5f0d34ab646cc87db9653f2893f60df44f9",
    INPUT / "case-bound-input-context-contract.json": "7ea723e536e38c9c41ecbe119af3ca79c2b748951da551fe4100894c735e9f16",
    INPUT / "source-pins.json": "4d290ddc593a99001cc76eaca5ef504d991994df9e1a22ff157408464552f83a",
    INPUT / "audit.json": "8d5a5af4d2ef2aaa443c7d82557279ed32962449eeeab683e9331467e50effca",
    AUDITOR: "df1ed0eedb62ed3657a05a6d679d105e15e63b5ee18b999a731adab190b1b479",
    BASE / "current-springa-frame-response-audit-attempt01/response_audit.py":
        "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def main() -> dict[str, Any]:
    for path, expected in PINS.items():
        if expected:
            require(sha(path) == expected, f"K12 input-context pin mismatch: {path}")
    spec = importlib.util.spec_from_file_location("k12_rear_case_bound_input_validator", AUDITOR)
    require(spec is not None and spec.loader is not None, "cannot import pinned case-bound validator")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)

    context = load(INPUT / "case-bound-input-context.json")
    model = load(INPUT / "model.json")
    deck = (INPUT / "model.inp").read_text()
    context_pin = validator._validate_case_context(context)
    contract = validator._validate_model(model, deck, context)
    summary = contract["inventory_summary"]
    expected = {
        "source_carrier_rows": 1840,
        "native_springa_rows": 1292,
        "retained_bilateral_spring2_rows": 348,
        "selected_floor_tangent_reaction_rows": 32,
        "inactive_floor_tangent_rows_without_restraint": 168,
        "selected_bearing_cells": 16,
        "inactive_separated_cells": 84,
        "physical_body_count": 50,
        "new_candidate_bolt_axes": 92,
        "retained_leg_runner_bolt_axes": 12,
        "panel_screw_axes": 66,
        "legacy_linear_auditor_reused": False,
    }
    for key, value in expected.items():
        require(summary.get(key) == value, f"Unexpected case-bound input inventory field {key}")
    require(context_pin["case_id"] == "k12-rear"
            and context_pin["screen_status"] == "REJECTED_ALL_BEARING_SUPPORT_BRANCH"
            and context_pin["selected_cell_count"] == 16
            and context_pin["inactive_cell_count"] == 84
            and context_pin["active_tangent_row_count"] == 32
            and context_pin["inactive_tangent_row_count"] == 168,
            "Case context is not the explicitly pinned K12-rear 16/84 proposal")
    require(model.get("input_only") is True
            and model.get("native_solve_executed") is False
            and model.get("frame_ready_for_native_run") is False
            and model.get("mechanical_acceptance") is False
            and model.get("source_response_forces_read") is False,
            "K12 selected input makes an execution, readiness, acceptance, or force-adoption claim")
    checks = {
        "source_constraint_reconstruction_residual": float(contract["source_constraint_reconstruction_residual"]),
        "source_reference_transform_residual": float(contract["source_reference_transform_residual"]),
        "source_pivot_identity_residual": float(contract["source_pivot_identity_residual"]),
        "source_point_wrench_force_error_N": float(contract["source_point_wrench_force_error_N"]),
        "source_point_wrench_moment_error_Nmm": float(contract["source_point_wrench_moment_error_Nmm"]),
        "floor_load_correction_max_abs_error_N": float(contract["floor_load_correction_max_abs_error_N"]),
    }
    require(max(checks[key] for key in (
        "source_constraint_reconstruction_residual",
        "source_reference_transform_residual",
        "source_pivot_identity_residual",
    )) < 1e-10, "K12 emitted source constraint reconstruction exceeds tolerance")
    require(checks["source_point_wrench_force_error_N"] < 1e-9
            and checks["source_point_wrench_moment_error_Nmm"] < 1e-6
            and checks["floor_load_correction_max_abs_error_N"] < 1e-7,
            "K12 source-point wrench or load-correction audit exceeds its pinned tolerance")

    result = {
        "schema": "current_springa_case_bound_selected_floor_input_contract/v1",
        "status": "PASS_CASE_BOUND_SELECTED_FLOOR_INPUT_CONTRACT_ONLY",
        "native_solve_launched_by_check": False,
        "native_response_consumed": False,
        "frame_ready_for_native_run": False,
        "mechanical_acceptance": False,
        "corner_demands_usable": False,
        "case_id": "k12-rear",
        "case_context_path": str((INPUT / "case-bound-input-context.json").relative_to(ROOT)),
        "case_context_sha256": sha(INPUT / "case-bound-input-context.json"),
        "input_model_path": str((INPUT / "model.json").relative_to(ROOT)),
        "input_model_sha256": sha(INPUT / "model.json"),
        "input_deck_path": str((INPUT / "model.inp").relative_to(ROOT)),
        "input_deck_sha256": sha(INPUT / "model.inp"),
        "validator_source_sha256": sha(AUDITOR),
        "stable_recovery_source_sha256": validator.STABLE_AUDIT_SHA256,
        "case_context_provenance": {
            "case_record_sha256": context_pin["case_record_sha256"],
            "source_model_inputs_sha256": context_pin["source_model_inputs_sha256"],
            "source_case_load_register_sha256": context_pin["register_sha256"],
            "controls_model_sha256": context_pin["controls_model_sha256"],
            "controls_deck_sha256": context_pin["controls_deck_sha256"],
            "diagnostic_screen_sha256": context_pin["screen_sha256"],
            "diagnostic_screen_status": context_pin["screen_status"],
        },
        "source_inventory": summary,
        "selected_constraint_checks": checks,
        "limits": [
            "This validates only the serialized K12-rear selected-floor input and its source/load context.",
            "The 16/84 rejected-screen partition is a proposed input mask. Diagnostic forces are not adopted as response.",
            "No selected-floor native response, physical corner demand, floor qualification, or design acceptance is established.",
        ],
        "producer_sha256": sha(Path(__file__)),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True, allow_nan=False))
