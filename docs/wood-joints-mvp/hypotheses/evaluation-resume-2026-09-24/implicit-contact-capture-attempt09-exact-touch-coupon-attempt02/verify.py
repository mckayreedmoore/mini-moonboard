#!/usr/bin/env python3
"""Verify the attempt09 exact-touch coupon outputs without running a solver."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
FREEZE_PATH = HERE / "input-freeze.json"
READINESS_PATH = HERE / "readiness.json"
OUTPUT = HERE / "output"
VERIFY_PATH = HERE / "verify.py"
RESULT_PATH = OUTPUT / "verification.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def main() -> int:
    checks: dict[str, dict[str, object]] = {}
    issues: list[str] = []

    def check(name: str, condition: bool, detail: object) -> None:
        checks[name] = {"status": "PASS" if condition else "FAIL", "detail": detail}
        if not condition:
            issues.append(name)

    record: dict[str, object] = {
        "schema": "ccx223_attempt09_contact_capture_coupon_verification/v1",
        "recorded_at": utc_now(),
        "scope": "known-answer method coupon only; no current-joint or criterion acceptance",
        "native_solver_case_run": True,
        "current_joint_run": False,
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "checks": checks,
    }
    try:
        freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        readiness = json.loads(READINESS_PATH.read_text(encoding="utf-8"))
        authorization_path = HERE / "authorization.json"
        authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
        ledger_path = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.json"
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        execution_path = OUTPUT / "execution.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        expected_path = ROOT / freeze["known_answer"]["expected_path"]
        reader_contract_path = HERE / freeze["reader_contract"]["path"]
        expected_hash = sha256(expected_path)
        reader_contract_hash = sha256(reader_contract_path)
        check(
            "known_answer_hash",
            expected_hash == freeze["known_answer"]["expected_sha256"],
            {
                "expected": freeze["known_answer"]["expected_sha256"],
                "actual": expected_hash,
            },
        )
        check(
            "reader_contract_hash",
            reader_contract_hash == freeze["reader_contract"]["sha256"],
            {
                "expected": freeze["reader_contract"]["sha256"],
                "actual": reader_contract_hash,
            },
        )
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        frozen_source_pins = {
            freeze["authority_and_review"]["agents_md_path"]: freeze["authority_and_review"]["agents_md_sha256"],
            freeze["authority_and_review"]["attempt09_parent_review_path"]: freeze["authority_and_review"]["attempt09_parent_review_sha256"],
            freeze["authority_and_review"]["attempt09_source_pins_path"]: freeze["authority_and_review"]["attempt09_source_pins_sha256"],
            freeze["authority_and_review"]["build_review_path"]: freeze["authority_and_review"]["build_review_sha256"],
            freeze["solver"]["source_archive_path"]: freeze["solver"]["source_archive_sha256"],
            freeze["solver"]["patch_path"]: freeze["solver"]["patch_sha256"],
            freeze["solver"]["build_manifest_path"]: freeze["solver"]["build_manifest_sha256"],
            freeze["solver"]["build_execution_path"]: freeze["solver"]["build_execution_sha256"],
            freeze["solver"]["docker_build_log_path"]: freeze["solver"]["docker_build_log_sha256"],
            freeze["solver"]["capture_contract_path"]: freeze["solver"]["capture_contract_sha256"],
            freeze["solver"]["manual_path"]: freeze["solver"]["manual_sha256"],
            freeze["reader_contract"]["reader_path"]: freeze["reader_contract"]["reader_sha256"],
        }
        frozen_source_mismatches = {
            path: {"expected": digest, "actual": sha256(ROOT / path) if (ROOT / path).is_file() else None}
            for path, digest in frozen_source_pins.items()
            if not (ROOT / path).is_file() or sha256(ROOT / path) != digest
        }
        check("all_frozen_source_build_and_authority_pins", not frozen_source_mismatches, frozen_source_mismatches)
        local_pins = {
            freeze["input"]["path"]: freeze["input"]["sha256"],
            freeze["rosters"]["pair_roster_path"]: freeze["rosters"]["pair_roster_sha256"],
            freeze["rosters"]["face_roster_path"]: freeze["rosters"]["face_roster_sha256"],
            freeze["reader_contract"]["path"]: freeze["reader_contract"]["sha256"],
        }
        local_pin_mismatches = {
            path: {"expected": digest, "actual": sha256(HERE / path) if (HERE / path).is_file() else None}
            for path, digest in local_pins.items()
            if not (HERE / path).is_file() or sha256(HERE / path) != digest
        }
        check("local_freeze_input_roster_and_reader_pins", not local_pin_mismatches, local_pin_mismatches)
        work_fixture_pins = {
            freeze["known_answer"]["work_fixture_result_path"]: freeze["known_answer"]["work_fixture_result_sha256"],
            freeze["known_answer"]["work_fixture_independent_review_path"]: freeze["known_answer"]["work_fixture_independent_review_sha256"],
            freeze["known_answer"]["work_fixture_verifier_path"]: freeze["known_answer"]["work_fixture_verifier_sha256"],
            freeze["known_answer"]["work_fixture_execution_path"]: freeze["known_answer"]["work_fixture_execution_sha256"],
        }
        work_fixture_mismatches = {
            path: {"expected": digest, "actual": sha256(ROOT / path) if (ROOT / path).is_file() else None}
            for path, digest in work_fixture_pins.items()
            if not (ROOT / path).is_file() or sha256(ROOT / path) != digest
        }
        check("prior_exact_touch_work_fixture_pins", not work_fixture_mismatches, work_fixture_mismatches)
        reader_expectation = json.loads(
            reader_contract_path.read_text(encoding="utf-8")
        )
        frozen_bindings = {
            "input_sha256": freeze["input"]["sha256"],
            "include_closure_sha256": freeze["input"]["include_closure_sha256"],
            "source_archive_sha256": freeze["solver"]["source_archive_sha256"],
            "patch_sha256": freeze["solver"]["patch_sha256"],
            "binary_sha256": freeze["solver"]["binary_sha256"],
            "pair_roster_sha256": freeze["rosters"]["pair_roster_sha256"],
            "face_roster_sha256": freeze["rosters"]["face_roster_sha256"],
        }
        check(
            "all_capture_contract_bindings_match_freeze",
            reader_expectation.get("run_bindings") == frozen_bindings,
            {
                "expected": frozen_bindings,
                "actual": reader_expectation.get("run_bindings"),
            },
        )
        reader_path = ROOT / freeze["reader_contract"]["reader_path"]

        check(
            "readiness_status",
            readiness.get("status") == "READY_FOR_ONE_SERIALIZED_ATTEMPT09_METHOD_COUPON_RUN",
            readiness.get("status"),
        )
        check(
            "readiness_freeze_binding",
            readiness.get("input_freeze_sha256") == sha256(FREEZE_PATH),
            {
                "actual_freeze_sha256": sha256(FREEZE_PATH),
                "readiness_freeze_sha256": readiness.get("input_freeze_sha256"),
            },
        )
        check(
            "readiness_runner_binding",
            readiness.get("runner_sha256") == sha256(HERE / "run.py"),
            {
                "actual_runner_sha256": sha256(HERE / "run.py"),
                "readiness_runner_sha256": readiness.get("runner_sha256"),
            },
        )
        check(
            "readiness_verifier_binding",
            readiness.get("verifier_sha256") == sha256(VERIFY_PATH),
            {
                "actual_verifier_sha256": sha256(VERIFY_PATH),
                "readiness_verifier_sha256": readiness.get("verifier_sha256"),
            },
        )
        authorization_hash = sha256(authorization_path)
        freeze_hash = sha256(FREEZE_PATH)
        pre_run_review_path = ROOT / readiness.get("independent_pre_run_review_path", "")
        pre_run_review_hash = sha256(pre_run_review_path) if pre_run_review_path.is_file() else None
        check(
            "independent_pre_run_review_binding",
            readiness.get("independent_pre_run_review_status") == "PASS_BOUNDED_METHOD_COUPON_PREFLIGHT"
            and pre_run_review_hash == readiness.get("independent_pre_run_review_sha256")
            and authorization.get("independent_pre_run_review_sha256") == pre_run_review_hash,
            {"path": readiness.get("independent_pre_run_review_path"), "expected": readiness.get("independent_pre_run_review_sha256"), "actual": pre_run_review_hash},
        )
        ledger_rows = [row for row in ledger.get("runs", []) if row.get("run_id") == freeze.get("run_id")]
        check(
            "run_specific_authorization_binding",
            authorization.get("run_id") == freeze.get("run_id")
            and authorization.get("input_freeze_sha256") == freeze_hash
            and authorization.get("owner_authority_sha256") == freeze["authority_and_review"]["agents_md_sha256"]
            and readiness.get("authorization_sha256") == authorization_hash,
            {"authorization_sha256": authorization_hash, "authorization": authorization},
        )
        check(
            "readiness_source_review_binding",
            readiness.get("parent_review_sha256") == freeze["authority_and_review"]["attempt09_parent_review_sha256"]
            and readiness.get("build_review_sha256") == freeze["authority_and_review"]["build_review_sha256"],
            {"parent_review_sha256": readiness.get("parent_review_sha256"), "build_review_sha256": readiness.get("build_review_sha256")},
        )
        reservation_ok = (
            len(ledger_rows) == 1
            and ledger_rows[0].get("state", "").startswith("consumed_")
            and ledger_rows[0].get("launches_consumed") == 1
            and ledger_rows[0].get("input_freeze_sha256") == freeze_hash
            and ledger_rows[0].get("authorization_sha256") == authorization_hash
            and ledger_rows[0].get("readiness_sha256") == sha256(READINESS_PATH)
            and ledger_rows[0].get("parent_readiness") is True
            and ledger_rows[0].get("native_execution_authorized") is True
        )
        check("parent_ledger_run_consumed", reservation_ok, ledger_rows)

        check(
            "solver_execution_completed",
            execution.get("status") == "completed"
            and execution.get("docker_cli_exit_code") == 0
            and execution.get("timed_out") is False,
            {
                "status": execution.get("status"),
                "docker_cli_exit_code": execution.get("docker_cli_exit_code"),
                "timed_out": execution.get("timed_out"),
            },
        )
        check(
            "execution_scope",
            execution.get("case") == "exact_touch_output_capture_coupon"
            and execution.get("current_joint_run") is False
            and execution.get("run_id") == freeze.get("run_id")
            and execution.get("authorization_sha256") == authorization_hash
            and execution.get("input_freeze_sha256") == freeze_hash
            and execution.get("readiness_sha256") == sha256(READINESS_PATH),
            {
                "case": execution.get("case"),
                "current_joint_run": execution.get("current_joint_run"),
                "input_freeze_sha256": execution.get("input_freeze_sha256"),
                "readiness_sha256": execution.get("readiness_sha256"),
            },
        )
        check(
            "execution_output_caps",
            execution.get("output_caps_pass") is True
            and execution.get("capture_cap_pass") is True
            and int(execution.get("capture_bytes", -1))
            <= int(execution.get("capture_byte_cap", 0)),
            {
                "output_caps_pass": execution.get("output_caps_pass"),
                "capture_cap_pass": execution.get("capture_cap_pass"),
                "capture_bytes": execution.get("capture_bytes"),
                "capture_byte_cap": execution.get("capture_byte_cap"),
            },
        )

        frozen_input = HERE / freeze["input"]["path"]
        runtime_input = OUTPUT / "coupon.inp"
        check(
            "input_copy_matches_freeze",
            runtime_input.is_file()
            and sha256(runtime_input) == freeze["input"]["sha256"],
            {
                "expected": freeze["input"]["sha256"],
                "actual": sha256(runtime_input) if runtime_input.is_file() else None,
            },
        )
        check(
            "source_input_still_frozen",
            sha256(frozen_input) == freeze["input"]["sha256"],
            {"expected": freeze["input"]["sha256"], "actual": sha256(frozen_input)},
        )

        output_hashes = execution.get("output_sha256", {})
        actual_names = {
            path.name
            for path in OUTPUT.iterdir()
            if path.is_file()
            and path.name not in {"execution.json", "verification.json"}
        }
        check(
            "execution_output_inventory",
            isinstance(output_hashes, dict) and set(output_hashes) == actual_names,
            {
                "recorded_names": sorted(output_hashes)
                if isinstance(output_hashes, dict)
                else None,
                "actual_names": sorted(actual_names),
            },
        )
        output_hash_mismatches = (
            {
                name: {
                    "recorded": digest,
                    "actual": sha256(OUTPUT / name)
                    if (OUTPUT / name).is_file()
                    else None,
                }
                for name, digest in output_hashes.items()
                if not (OUTPUT / name).is_file() or sha256(OUTPUT / name) != digest
            }
            if isinstance(output_hashes, dict)
            else {"output_sha256": "not an object"}
        )
        check(
            "execution_output_hashes",
            not output_hash_mismatches,
            output_hash_mismatches,
        )

        standard_names = set(freeze["known_answer"]["baseline_output_sha256"])
        standard_mismatches = {}
        baseline_dir = ROOT / freeze["known_answer"]["baseline_output_path"]
        for name in sorted(standard_names):
            path = OUTPUT / name
            expected_hash = freeze["known_answer"]["baseline_output_sha256"][name]
            actual_hash = sha256(path) if path.is_file() else None
            baseline_hash = (
                sha256(baseline_dir / name) if (baseline_dir / name).is_file() else None
            )
            if actual_hash != expected_hash or baseline_hash != expected_hash:
                standard_mismatches[name] = {
                    "expected": expected_hash,
                    "actual": actual_hash,
                    "pinned_baseline_actual": baseline_hash,
                }
        check(
            "standard_solver_output_parity",
            not standard_mismatches,
            standard_mismatches,
        )

        spec = importlib.util.spec_from_file_location(
            "ccx_capture_reader_pinned", reader_path
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load the pinned capture reader")
        reader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reader)
        check(
            "capture_reader_hash",
            sha256(reader_path) == freeze["reader_contract"]["reader_sha256"],
            {
                "expected": freeze["reader_contract"]["reader_sha256"],
                "actual": sha256(reader_path),
            },
        )
        capture_path = OUTPUT / "capture.tsv"
        capture_bytes = capture_path.read_bytes()
        capture_result = reader.validate_capture(capture_bytes, reader_expectation)
        check(
            "capture_structure_and_bindings",
            capture_result.get("status") == "PASS_CAPTURE_STRUCTURE",
            {
                key: capture_result.get(key)
                for key in (
                    "status",
                    "generation_count",
                    "face_rows",
                    "point_candidates",
                    "trial_rows",
                    "iteration_links",
                )
            },
        )

        accepted = capture_result["accepted_states"]
        accepted_times = [float(item["time"]) for item in accepted]
        expected_times = [
            float(value)
            for value in expected["solver_contract"]["expected_accepted_total_times"]
        ]
        times_match = len(accepted_times) == len(expected_times) and all(
            abs(a - b) <= 1e-9 for a, b in zip(accepted_times, expected_times)
        )
        check(
            "accepted_state_coverage",
            times_match,
            {"accepted_times": accepted_times, "expected_times": expected_times},
        )

        compression_time = float(expected["solver_contract"]["states"][2]["total_time"])
        compression_states = [
            state
            for state in accepted
            if abs(float(state["time"]) - compression_time) <= 1e-9
        ]
        compression_summary: dict[str, object] | None = None
        force_error = math.inf
        force_tolerance = 0.0
        energy_error = math.inf
        energy_tolerance = 0.0
        if len(compression_states) == 1:
            generation = compression_states[0]["generation"]
            summaries = [
                row
                for row in capture_result["trial_summaries"]
                if row["generation"] == generation and row["tie"] == 1
            ]
            if len(summaries) == 1:
                compression_summary = summaries[0]
                measured_force = compression_summary["force_on_slave_N"]
                reference = expected["analytical_reference"]["pair_force"][
                    "compression_CFN_N"
                ]
                force_error = (
                    math.sqrt(
                        sum(
                            (float(measured_force[i]) - float(reference[i])) ** 2
                            for i in range(3)
                        )
                    )
                    if measured_force is not None
                    else math.inf
                )
                force_tolerance = float(
                    expected["analytical_reference"]["pair_force"]["force_abs_error_N"]
                ) + float(
                    expected["analytical_reference"]["pair_force"][
                        "force_relative_error"
                    ]
                ) * math.sqrt(sum(float(value) ** 2 for value in reference))
                measured_energy = compression_summary["stored_energy_N_mm"]
                reference_energy = float(
                    expected["analytical_reference"]["compression"]["contact_CELS_N_mm"]
                )
                energy_error = (
                    abs(float(measured_energy) - reference_energy)
                    if measured_energy is not None
                    else math.inf
                )
                energy_tolerance = max(
                    float(
                        expected["energy_output_contract"][
                            "endpoint_component_absolute_tolerance_N_mm"
                        ]
                    ),
                    float(
                        expected["energy_output_contract"][
                            "endpoint_component_relative_tolerance"
                        ]
                    )
                    * abs(reference_energy),
                )
        check(
            "compression_capture_summary_present",
            compression_summary is not None,
            {
                "compression_time": compression_time,
                "accepted_state_count": len(compression_states),
                "summary": compression_summary,
            },
        )
        check(
            "compression_slave_force_known_answer",
            math.isfinite(force_error) and force_error <= force_tolerance,
            {
                "force_error_norm_N": force_error,
                "tolerance_N": force_tolerance,
                "captured_force_N": compression_summary.get("force_on_slave_N")
                if compression_summary
                else None,
                "reference_force_N": expected["analytical_reference"]["pair_force"][
                    "compression_CFN_N"
                ],
            },
        )
        check(
            "compression_contact_energy_known_answer",
            math.isfinite(energy_error) and energy_error <= energy_tolerance,
            {
                "energy_error_N_mm": energy_error,
                "tolerance_N_mm": energy_tolerance,
                "captured_energy_N_mm": compression_summary.get("stored_energy_N_mm")
                if compression_summary
                else None,
                "reference_energy_N_mm": expected["analytical_reference"][
                    "compression"
                ]["contact_CELS_N_mm"],
            },
        )

        record["capture_result"] = capture_result
        record["compression_state"] = compression_summary
        record["capture_sha256"] = sha256(capture_path)
        record["solver_standard_output_hashes"] = {
            name: sha256(OUTPUT / name) for name in sorted(standard_names)
        }
    except Exception as exc:  # noqa: BLE001 - preserve a machine-readable failure record
        issues.append(f"verifier_exception: {type(exc).__name__}: {exc}")
        record["verifier_exception"] = f"{type(exc).__name__}: {exc}"

    record["status"] = (
        "PASS_ATTEMPT09_EXACT_TOUCH_METHOD_COUPON"
        if not issues
        else "FAIL_ATTEMPT09_EXACT_TOUCH_METHOD_COUPON"
    )
    record["failed_checks"] = issues
    record["verifier_sha256"] = sha256(VERIFY_PATH)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": record["status"],
                "failed_checks": issues,
                "verification": str(RESULT_PATH.relative_to(ROOT)),
            },
            indent=2,
        )
    )
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
