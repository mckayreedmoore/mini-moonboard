#!/usr/bin/env python3
"""Read-only, source-pinned replay of the preserved SPR489 native output."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
PACKET = Path(__file__).resolve().parent
NATIVE = SERIES / "current-k12-rear-direct-scalar-native-attempt01"
ORIGINAL_METHOD = SERIES / "current-k12-rear-direct-scalar-parent-method-attempt01"
CHECKER = PACKET / "check.py"
ORIGINAL_CHECKER = ORIGINAL_METHOD / "check.py"
STABLE = SERIES / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
PARENT_DIAGNOSTIC = NATIVE / "parent-terminal-assessment.json"

PINS = {
    ORIGINAL_CHECKER: "8d26d27b54343fed08dfc39e2470b911ef2377ee781a6a901e1982e79dd791ef",
    STABLE: "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
    NATIVE / "freeze.json": "fbad45dcffeb56833052b21505bf0a8c484dfceb5d46a659fc3e526b7d2d43f4",
    NATIVE / "execution.json": "0dd64faad748a360fd13d784927c20fc7cde079b64da9db5cd21e3bf92f61a4b",
    NATIVE / "parent-terminal-assessment.json": "4a3d35471c46664daa9a8c3eade78ed8df9a10c72199502aee45c9e508b15ae9",
    NATIVE / "model.inp": "95057c23311105f953a9e99a35ae1e73e76d8c6f3137f464af957ef32e5a489c",
    NATIVE / "model.json": "c3cdc472b811e3e90c9d0df068edf82ec07c2b84d5b2d7d00bddc562e8ba426e",
    NATIVE / "model.dat": "f70cb84fcd59c1d7edbc370ace803ebd8757e7bd6166670af1e0fd4439cb8aed",
    NATIVE / "native.stdout": "451fd7a7f95dd3692246be9c9b54d1e4638e83282ec9577db71efea71ce0c02a",
    NATIVE / "native.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def write_once(path: Path, obj: object) -> None:
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite {path}")
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n")


def load_checker():
    spec = importlib.util.spec_from_file_location("spr489_geometric_replay_checker", CHECKER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import sibling post-hoc checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    for path, expected in PINS.items():
        actual = sha(path)
        if expected is not None and actual != expected:
            raise RuntimeError(f"Pinned source changed: {rel(path)}: {actual}")
    parent_assessment = json.loads(PARENT_DIAGNOSTIC.read_text())
    if parent_assessment["status"] != "TERMINAL_ZERO_EXIT_ORIGINAL_CHECKER_REJECTED":
        raise RuntimeError("Preserved attempt01 terminal status changed")
    if parent_assessment["original_failure"] != (
            "SPRINGA Q endpoint RF does not match table force at step 2 time 1.825"):
        raise RuntimeError("Preserved original failure text changed")
    if parent_assessment["checker_sha256"] != PINS[ORIGINAL_CHECKER]:
        raise RuntimeError("Original terminal assessment no longer identifies the frozen checker")

    checker = load_checker()
    native_audit = checker.assess_native(NATIVE)
    if native_audit["status"] != "PASS_POSTHOC_REPLAY_WITH_PINNED_GEOMETRIC_SPRINGA_INTERVAL":
        raise RuntimeError(f"Unexpected replay status {native_audit['status']}")
    if native_audit["this_checker_invoked_native_solver"] is not False:
        raise RuntimeError("Post-hoc checker claims to have launched native")
    if native_audit["output_state_count"] != 18:
        raise RuntimeError(f"Expected all 18 recorded states, got {native_audit['output_state_count']}")

    # Compare the geometry-based SPRINGA force intervals against the preserved
    # independent parent diagnostic, state by state.
    prior_rows = parent_assessment["parent_diagnostic_only"]["rows"]
    replay_rows = native_audit["all_recorded_states"]
    if len(prior_rows) != len(replay_rows):
        raise RuntimeError("Independent parent interval diagnostic has a different state count")
    for expected, actual in zip(prior_rows, replay_rows):
        if abs(expected["time"] - actual["total_time"]) > 1.0e-12:
            raise RuntimeError("Native state time differs from preserved parent diagnostic")
        for key in ("q_mm", "geometric_elongation_mm", "RF_N"):
            actual_key = {"q_mm": "q_from_native_Q_U_mm",
                          "geometric_elongation_mm": "SPRINGA_actual_geometric_elongation_mm",
                          "RF_N": "SPRINGA_Q_RF_N"}[key]
            if abs(expected[key] - actual[actual_key]) > 1.0e-15:
                raise RuntimeError(f"Parent/attempt02 {key} mismatch at time {expected['time']}")
        interval = actual["SPRINGA_Q_RF_table_force_interval_N"]
        if max(abs(expected["table_force_interval_N"][j] - interval[j]) for j in (0, 1)) > 1.0e-12:
            raise RuntimeError(f"Parent/attempt02 table interval mismatch at time {expected['time']}")
        if expected["existing_geometric_law_interval_passed"] is not True:
            raise RuntimeError("Preserved parent diagnostic has a geometric-law failure")

    input_audit = checker.input_audit()
    source_pins = {
        "schema": "current_spr489_geometric_interval_posthoc_replay_source_pins/v1",
        "scope": "read-only replay of existing terminal attempt01 native output; no solver run",
        "source_files_sha256": {rel(path): sha(path) for path in PINS},
        "original_checker_sha256": sha(ORIGINAL_CHECKER),
        "geometric_replay_checker_sha256": sha(CHECKER),
        "pinned_springa_auditor_sha256": sha(STABLE),
        "frozen_native_output_parent_assessment_sha256": sha(PARENT_DIAGNOSTIC),
    }
    state_step2 = next(row for row in native_audit["all_recorded_states"]
                       if row["step"] == 2 and abs(row["total_time"] - 1.825) <= 1.0e-12)
    table = checker.parse_deck((NATIVE / "model.inp").read_text())["nonlinear_springs"]["JOINT"]
    q_value = state_step2["q_from_native_Q_U_mm"]
    q_radius = state_step2["q_Q_U_token_radius_mm"]
    q_force_low = checker.table_force(q_value - q_radius, table)
    q_force_high = checker.table_force(q_value + q_radius, table)
    rf_q = state_step2["SPRINGA_Q_RF_N"]
    rf_q_radius = state_step2["SPRINGA_Q_RF_radius_N"]
    rf_ground = state_step2["SPRINGA_ground_RF_N_excluded_from_physical_owner_balance"]
    table_force_mid = state_step2["SPRINGA_table_force_from_dd_minus_dd0_N"]
    force_guard = 32.0 * checker.sys.float_info.epsilon * max(
        1.0, abs(rf_q), abs(rf_ground), abs(table_force_mid))
    q_only_miss = max(
        0.0,
        q_force_low - (rf_q + rf_q_radius) - force_guard,
        (rf_q - rf_q_radius) - q_force_high - force_guard,
    )
    q_force_mid = checker.table_force(q_value, table)
    geometric_force_difference = table_force_mid - q_force_mid
    geometry_interval_passed = state_step2["SPRINGA_Q_RF_table_interval_distance_N"] == 0.0
    if not geometry_interval_passed or q_only_miss <= 0.0:
        raise RuntimeError("Replay did not reproduce the specific original q-only false rejection")

    diagnosis = {
        "schema": "current_spr489_direct_scalar_checker_failure_diagnosis/v1",
        "status": "ORIGINAL_Q_ONLY_TABLE_COMPARISON_FALSE_REJECTS; GEOMETRIC_TABLE_INTERVAL_INTERSECTS",
        "original_failure": parent_assessment["original_failure"],
        "original_checker_sha256": sha(ORIGINAL_CHECKER),
        "original_freeze_sha256": sha(NATIVE / "freeze.json"),
        "original_execution_sha256": sha(NATIVE / "execution.json"),
        "original_native_dat_sha256": sha(NATIVE / "model.dat"),
        "original_native_deck_sha256": sha(NATIVE / "model.inp"),
        "original_native_model_sha256": sha(NATIVE / "model.json"),
        "posthoc_checker_sha256": sha(CHECKER),
        "pinned_geometric_method_sha256": sha(STABLE),
        "failure_state": {
            "step": 2,
            "total_time": 1.825,
            "step_time": 0.825,
            "q_from_native_U_mm": q_value,
            "q_token_radius_mm": q_radius,
            "native_RF_Q_N": rf_q,
            "native_RF_Q_token_radius_N": rf_q_radius,
            "initial_spring_length_mm": state_step2["SPRINGA_initial_length_mm"],
            "current_spring_length_mm": state_step2["SPRINGA_current_length_mm"],
            "actual_dd_minus_dd0_mm": state_step2["SPRINGA_actual_geometric_elongation_mm"],
            "dd_minus_dd0_minus_q_mm": (
                state_step2["SPRINGA_actual_geometric_elongation_mm"] - q_value
            ),
            "serialized_slope_N_per_mm": table[-1][0] / table[-1][1],
            "force_difference_between_q_and_dd_minus_dd0_N": geometric_force_difference,
            "old_q_only_table_interval_N": [q_force_low, q_force_high],
            "q_only_rf_interval_gap_after_original_force_guard_N": q_only_miss,
            "existing_16eps_span_length_guard_mm": state_step2["SPRINGA_geometric_length_subtraction_guard_mm"],
            "geometric_elongation_interval_radius_mm": state_step2["SPRINGA_geometric_elongation_interval_radius_mm"],
            "corrected_dd_minus_dd0_table_force_interval_N": state_step2["SPRINGA_Q_RF_table_force_interval_N"],
            "geometric_interval_intersects_RF_token_interval": geometry_interval_passed,
        },
        "full_recorded_state_count": 18,
        "geometric_springa_interval_passed_at_all_states": True,
        "corrected_replay_status": native_audit["status"],
        "corrected_replay_other_checks": {
            "all_state_direct_MPC_intervals": "PASS",
            "all_state_source_projection_intervals": "PASS",
            "all_state_springa_Q_GQ_action_reaction": "PASS",
            "all_state_numerical_support_laws": "PASS",
            "three_endpoint_rank_one_displacement_oracles": "PASS",
            "three_endpoint_owner_force_and_moment_recovery": "PASS",
        },
        "native_was_rerun": False,
        "method_validation_status": "PARENT_INDEPENDENT_REVIEW_PENDING",
        "mechanical_acceptance": False,
        "frame_forces_accepted": False,
        "qualified_for_design": False,
    }
    write_once(PACKET / "native-output-audit.json", native_audit)
    write_once(PACKET / "input-readiness-audit.json", input_audit)
    write_once(PACKET / "source-pins.json", source_pins)
    diagnosis["native_output_audit_sha256"] = sha(PACKET / "native-output-audit.json")
    diagnosis["input_readiness_audit_sha256"] = sha(PACKET / "input-readiness-audit.json")
    diagnosis["source_pins_sha256"] = sha(PACKET / "source-pins.json")
    diagnosis["producer_sha256"] = sha(Path(__file__).resolve())
    write_once(PACKET / "diagnosis.json", diagnosis)
    print(diagnosis["status"])
    print(PACKET)


if __name__ == "__main__":
    main()
