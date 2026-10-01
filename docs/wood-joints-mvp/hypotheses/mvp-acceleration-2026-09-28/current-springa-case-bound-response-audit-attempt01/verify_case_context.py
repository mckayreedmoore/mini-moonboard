"""Validate one explicit case context and its prepared selected-floor input only.

This check imports no native runner and consumes no DAT. It validates the
case-specific all-bearing source, diagnostic screen, selected model/deck and
the unchanged physical recovery contract. Negative probes exercise fail-closed
case/hash/source and source-law/load/geometry input binding.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
CONTEXT = HERE / "a12-forward-context-example.json"
OUTPUT = HERE / "input_contract_check.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_auditor():
    path = HERE / "response_audit.py"
    spec = importlib.util.spec_from_file_location("case_bound_springa_response_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import the case-bound response auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def must_reject(label: str, action: Callable[[], Any], error_type: type[Exception]) -> str:
    try:
        action()
    except error_type as error:
        return f"{label}: rejected ({error})"
    raise AssertionError(f"Case-bound input check accepted invalid probe: {label}")


def main() -> None:
    auditor = import_auditor()
    context = json.loads(CONTEXT.read_text())
    context_pin = auditor._validate_case_context(context)
    model_path = auditor._context_path(context["selected_input_model_json_path"])
    deck_path = auditor._context_path(context["selected_input_deck_path"])
    record = json.loads(model_path.read_text())
    deck = deck_path.read_text()
    contract = auditor._validate_model(record, deck, context)

    expected = {
        "source_carrier_rows": 1840,
        "native_springa_rows": 1292,
        "retained_bilateral_spring2_rows": 348,
        "selected_floor_tangent_reaction_rows": 70,
        "inactive_floor_tangent_rows_without_restraint": 130,
        "selected_bearing_cells": 35,
        "inactive_separated_cells": 65,
        "physical_body_count": 50,
        "new_candidate_bolt_axes": 92,
        "retained_leg_runner_bolt_axes": 12,
        "panel_screw_axes": 66,
        "legacy_linear_auditor_reused": False,
    }
    for key, value in expected.items():
        if contract["inventory_summary"].get(key) != value:
            raise AssertionError(f"Unexpected case-bound method inventory for {key}")
    if contract["selected_cells"] != set(context["selected_cells"]):
        raise AssertionError("Selected cell mask differs from explicit parent screen context")
    if contract["inactive_cells"] != set(context["inactive_cells"]):
        raise AssertionError("Inactive cell mask differs from explicit parent screen context")
    if (contract["source_point_wrench_force_error_N"] > 1.0e-9
            or contract["source_point_wrench_moment_error_Nmm"] > 1.0e-6
            or contract["floor_load_correction_max_abs_error_N"] > 1.0e-7):
        raise AssertionError("Case-specific selected floor transform/correction exceeded its pinned tolerance")

    rejected: list[str] = []
    for label, key, value in (
        ("case identity", "case_id", "a12-left"),
        ("case record hash", "case_record_sha256", "0" * 64),
        ("candidate", "candidate", "compact-floor-flush-development"),
        ("geometry revision", "geometry_revision_id", "old-revision"),
        ("controls deck hash", "source_controls_deck_sha256", "0" * 64),
        ("diagnostic screen status", "diagnostic_floor_screen_status", "ACCEPTED"),
        ("selected model hash", "selected_input_model_json_sha256", "0" * 64),
    ):
        altered = copy.deepcopy(context)
        altered[key] = value
        rejected.append(must_reject(
            label, lambda altered=altered: auditor._validate_case_context(altered),
            auditor.ResponseAuditError,
        ))

    for label, field, mutate in (
        ("serialized physical load", "loads", lambda value: {**value, next(iter(value)): [float(x) + (1.0 if i == 0 else 0.0) for i, x in enumerate(next(iter(value.values())))]}),
        ("serialized carrier law", "unilateral_springa_bindings", lambda value: [{**value[0], "stiffness_n_per_mm": float(value[0]["stiffness_n_per_mm"]) + 1.0}, *value[1:]]),
        ("serialized geometry", "nodes", lambda value: {**value, next(iter(value)): [float(x) + (1.0 if i == 0 else 0.0) for i, x in enumerate(next(iter(value.values())))]}),
    ):
        altered_record = copy.deepcopy(record)
        altered_record[field] = mutate(altered_record[field])
        rejected.append(must_reject(
            label,
            lambda altered_record=altered_record: auditor._validate_model(altered_record, deck, context),
            auditor.ResponseAuditError,
        ))

    method_replay_path = HERE / "method_fixture_check.json"
    method_replay = json.loads(method_replay_path.read_text())
    if (method_replay.get("status") != "PASS_READ_ONLY_METHOD_FIXTURE_REPLAYS"
            or method_replay.get("native_solver_launched_by_replayer") is not False
            or method_replay.get("prior_native_fixtures_replayed") != 3
            or method_replay.get("near_zero_endpoint_length_roundoff_check", {}).get("passed") is not True):
        raise AssertionError("The pinned method coupons/serialization replay are absent or failed")

    # Export only JSON-native scalars and arrays. Internal contract objects
    # intentionally contain sets and NumPy values and are not serialized.
    result: dict[str, Any] = {
        "schema": "current_springa_case_bound_selected_floor_input_contract/v1",
        "status": "PASS_CASE_BOUND_SELECTED_FLOOR_INPUT_CONTRACT_ONLY",
        "native_solve_launched_by_check": False,
        "native_response_consumed": False,
        "frame_ready_for_native_run": False,
        "mechanical_acceptance": False,
        "corner_demands_usable": False,
        "case_context_path": str(CONTEXT.relative_to(ROOT)),
        "case_context_sha256": sha(CONTEXT),
        "input_model_path": str(model_path.relative_to(ROOT)),
        "input_model_sha256": sha(model_path),
        "input_deck_path": str(deck_path.relative_to(ROOT)),
        "input_deck_sha256": sha(deck_path),
        "response_audit_source_sha256": sha(HERE / "response_audit.py"),
        "stable_recovery_source_sha256": auditor.STABLE_AUDIT_SHA256,
        "case_context_provenance": {
            "case_id": context_pin["case_id"],
            "case_record_sha256": context_pin["case_record_sha256"],
            "source_model_inputs_sha256": context_pin["source_model_inputs_sha256"],
            "source_case_load_register_sha256": context_pin["register_sha256"],
            "controls_model_sha256": context_pin["controls_model_sha256"],
            "controls_deck_sha256": context_pin["controls_deck_sha256"],
            "diagnostic_screen_sha256": context_pin["screen_sha256"],
            "diagnostic_screen_status": context_pin["screen_status"],
        },
        "source_inventory": contract["inventory_summary"],
        "selected_constraint_checks": {
            "constraint_reconstruction_max_abs_error": float(contract["source_constraint_reconstruction_residual"]),
            "reference_transfer_max_abs_error": float(contract["source_reference_transform_residual"]),
            "pivot_identity_max_abs_error": float(contract["source_pivot_identity_residual"]),
            "source_point_wrench_force_error_N": float(contract["source_point_wrench_force_error_N"]),
            "source_point_wrench_moment_error_Nmm": float(contract["source_point_wrench_moment_error_Nmm"]),
            "emitted_source_load_correction_error_N": float(contract["floor_load_correction_max_abs_error_N"]),
            "inactive_floor_rows_have_no_reference_equation_or_load": True,
        },
        "fail_closed_probes": rejected,
        "method_fixture_replay": {
            "status": str(method_replay["status"]),
            "fixture_count": int(method_replay["prior_native_fixtures_replayed"]),
            "near_zero_length_roundoff_passed": bool(method_replay["near_zero_endpoint_length_roundoff_check"]["passed"]),
        },
        "serialization_round_trip_passed": True,
        "limits": [
            "This is one a12-forward input-contract check; it contains no selected-floor native frame response.",
            "The three native method coupons establish only scalar SPRINGA, exact-floor transform, and endpoint-roundoff methods.",
            "A later case response requires a parent-owned frozen context whose selected input hashes point to that exact frozen run.",
            "The proposed monotone zero-gap mask does not establish recontact, branch uniqueness, floor qualification, or mechanical acceptance.",
        ],
    }
    encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
    round_trip = json.loads(encoded)
    if round_trip["status"] != result["status"] or round_trip["source_inventory"] != result["source_inventory"]:
        raise AssertionError("Scalar-only report JSON serialization round trip changed values")
    OUTPUT.write_text(encoded)
    print(result["status"])


if __name__ == "__main__":
    main()
