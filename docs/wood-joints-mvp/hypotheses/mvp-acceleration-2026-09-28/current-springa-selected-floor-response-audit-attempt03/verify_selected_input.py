"""Run only the selected-floor response auditor's input contract checks."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
INPUT_PACKET = SERIES / "current-springa-active-floor-input-adapter-attempt03/a12-rear"
OUTPUT = HERE / "input_contract_check.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_auditor():
    path = HERE / "response_audit.py"
    spec = importlib.util.spec_from_file_location("selected_floor_response_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import selected-floor response auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    model_path, deck_path = INPUT_PACKET / "model.json", INPUT_PACKET / "model.inp"
    record: dict[str, Any] = json.loads(model_path.read_text())
    deck = deck_path.read_text()
    auditor = import_auditor()
    contract = auditor._validate_model(record, deck)
    method_replay = json.loads((HERE / "method_fixture_check.json").read_text())
    if method_replay.get("status") != "PASS_READ_ONLY_METHOD_FIXTURE_REPLAYS":
        raise AssertionError("Previously passed native method-coupon replays are not recorded as passing")
    if method_replay.get("native_solver_launched_by_replayer") is not False:
        raise AssertionError("Method fixture verifier must remain read-only")
    result = {
        "schema": "current_springa_selected_floor_response_input_contract/v1",
        "status": "PASS_SELECTED_FLOOR_INPUT_CONTRACT_ONLY",
        "native_solve_launched_by_check": False,
        "input_contract_validated": True,
        "frame_ready_for_native_run": False,
        "mechanical_acceptance": False,
        "corner_demands_usable": False,
        "input_model_path": str(model_path),
        "input_model_sha256": sha(model_path),
        "input_deck_sha256": sha(deck_path),
        "response_audit_source_sha256": sha(HERE / "response_audit.py"),
        "stable_recovery_source_sha256": auditor.STABLE_AUDIT_SHA256,
        "floor_screen_sha256": contract["screen_sha256"],
        "source_inventory": contract["inventory_summary"],
        "selected_constraint_checks": {
            "constraint_reconstruction_max_abs_error": contract["source_constraint_reconstruction_residual"],
            "reference_transfer_max_abs_error": contract["source_reference_transform_residual"],
            "pivot_identity_max_abs_error": contract["source_pivot_identity_residual"],
            "source_point_wrench_force_error_N": contract["source_point_wrench_force_error_N"],
            "source_point_wrench_moment_error_Nmm": contract["source_point_wrench_moment_error_Nmm"],
            "emitted_source_load_correction_error_N": contract["floor_load_correction_max_abs_error_N"],
            "inactive_floor_rows_have_no_reference_equation_or_load": True,
        },
        "prior_native_method_fixture_replay": {
            "status": method_replay["status"],
            "fixture_count": method_replay["prior_native_fixtures_replayed"],
            "near_zero_length_roundoff_passed": method_replay["near_zero_endpoint_length_roundoff_check"]["passed"],
        },
        "limitations": [
            "No selected-floor native output has been consumed by this input-only check.",
            "The method coupons validate scalar SPRINGA and floor-reaction recovery methods, not the frame or 25/75 branch.",
            "The proposed mask is conditional, monotone, zero-gap, and not a general release/recontact or uniqueness method.",
        ],
    }
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(result["status"])


if __name__ == "__main__":
    main()
