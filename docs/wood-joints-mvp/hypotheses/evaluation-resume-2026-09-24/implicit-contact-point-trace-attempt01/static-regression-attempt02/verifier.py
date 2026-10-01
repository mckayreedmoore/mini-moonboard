#!/usr/bin/env python3
"""Audit a matched-resource old/new static coupon pair without running CCX."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / ".git").exists())
EXPECTED_SCHEMA = "ccx223_static_regression_matched_comparison/v1"
VERIFIER_SCHEMA = "ccx223_static_regression_matched_verifier/v1"
NATIVE_FILES = ("coupon.12d", "coupon.cel", "coupon.cvg", "coupon.dat",
                "coupon.sta", "spooles.out", "coupon.frd",
                "ResultsForLastIterations.frd", "solver.stdout", "solver.stderr")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def read_json(path: Path) -> dict:
    def unique_pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"Duplicate JSON key {key} in {path}")
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError(f"Invalid JSON numeric constant {value} in {path}")
    def finite_float(value):
        number = float(value)
        require(math.isfinite(number), f"Nonfinite JSON number {value} in {path}")
        return number
    return json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                      parse_float=finite_float, parse_constant=reject_constant)


def load_prepare():
    spec = importlib.util.spec_from_file_location("matched_static_prepare", HERE / "prepare.py")
    require(spec is not None and spec.loader is not None, "Cannot import packet prepare.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_runner():
    spec = importlib.util.spec_from_file_location("matched_static_runner", HERE / "run.py")
    require(spec is not None and spec.loader is not None, "Cannot import packet run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_parser_helper(expected: dict):
    parser_dependency = next(row for row in read_json(HERE / "source-dependencies.json")["files"]
                             if row["key"] == "attempt01_parser")
    helper_path = ROOT / parser_dependency["repo_path"]
    require(sha(helper_path) == parser_dependency["sha256"],
            "Pinned attempt01 parser helper changed")
    spec = importlib.util.spec_from_file_location("pinned_attempt01_static_verifier", helper_path)
    require(spec is not None and spec.loader is not None, "Cannot load pinned attempt01 parser")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(parser_dependency["sha256"] == expected["comparison"]["trace_contract_source_sha256"],
            "Trace contract parser SHA differs from expected record")
    return module


def verify_packet() -> tuple[dict, dict, object, object]:
    prep = load_prepare()
    artifacts, summary = prep.build_all()
    prep.check_artifacts(artifacts)
    expected = read_json(HERE / "expected.json")
    require(expected.get("schema") == EXPECTED_SCHEMA,
            "Unexpected matched comparison expected schema")
    require(expected.get("preparation_script_sha256") == sha(HERE / "prepare.py") and
            expected.get("runner_script_sha256") == sha(HERE / "run.py") and
            expected.get("verifier_script_sha256") == sha(HERE / "verifier.py") and
            expected.get("readme_sha256") == sha(HERE / "README.md"),
            "Expected record does not bind current packet scripts")
    require(expected.get("run_limits", {}).get("serialized_case_order") == ["old", "trace"] and
            expected["run_limits"].get("omp_threads") == 1 and
            expected["run_limits"].get("ccx_solver_processes") == 1 and
            expected["run_limits"].get("no_overlap") is True,
            "Matched single-thread serialized limits are incomplete")
    helper = load_parser_helper(expected)
    runner = load_runner()
    return expected, summary, helper, runner


def option(command: list[str], name: str) -> str | None:
    try:
        i = command.index(name)
        return command[i + 1]
    except (ValueError, IndexError):
        return None


def case_hashes(directory: Path) -> dict[str, str]:
    return {path.name: sha(path) for path in sorted(directory.iterdir())
            if path.is_file() and path.name != "case-execution.json"}


def validate_case(case: str, index: int, expected: dict,
                  helper, output_root: Path, historical_stderr: bytes) -> dict:
    directory = output_root / case
    pins = expected["build_pins"][case]
    record_path = directory / "case-execution.json"
    require(record_path.is_file(), f"Missing {case} case-execution.json")
    record = read_json(record_path)
    require(record.get("schema") == "ccx223_static_regression_matched_case_execution/v1" and
            record.get("case") == case and record.get("case_order_index") == index and
            record.get("status") == "PASS_NATIVE_CAPTURE" and
            record.get("native_execution") is True and
            record.get("mechanical_acceptance") is False and
            record.get("joint_acceptance") is False,
            f"{case} did not produce a complete non-qualifying capture")
    require(record.get("image_id") == pins["image_id"] and
            record.get("binary_path") == pins["binary_path"] and
            record.get("binary_sha256") == pins["binary_sha256"],
            f"{case} build identity differs from the frozen pins")
    require(record.get("limits") == expected["run_limits"] and
            record.get("stop_reason") is None and
            isinstance(record.get("elapsed_seconds"), (int, float)) and
            0 <= record["elapsed_seconds"] <= expected["run_limits"]["wall_seconds_each_case"] and
            record.get("native_output_bytes", 2**63) <= expected["run_limits"]["aggregate_native_output_bytes_each_case"],
            f"{case} exceeded a frozen run limit")
    state = record.get("container_state") or {}
    require(record.get("docker_cli_exit_code") == 0 and
            state.get("ExitCode") == 0 and state.get("Running") is False and
            state.get("OOMKilled") is False and
            record.get("container_image_id") == pins["image_id"] and
            record.get("container_image_ref") == pins["image_id"],
            f"{case} container did not exit normally on the pinned image")

    command = record.get("command")
    require(isinstance(command, list) and len(command) >= 5 and
            command[:3] == ["docker", "run", "--pull=never"] and
            command[-4:] == [pins["image_id"], pins["binary_path"], "-i", "coupon"],
            f"{case} command does not invoke the pinned image/binary on the coupon")
    require(option(command, "--network") == "none" and
            option(command, "--cpus") == "1" and
            option(command, "--memory") == "1g" and
            option(command, "--memory-swap") == "1g" and
            option(command, "--name") == record.get("container_name") and
            option(command, "--workdir") == "/work" and
            "OMP_NUM_THREADS=1" in command and
            "CCX_NPROC_EQUATION_SOLVER=1" in command,
            f"{case} command does not use the matched frozen resources")
    expected_mount = f"type=bind,src={directory},dst=/work"
    require(option(command, "--mount") == expected_mount,
            f"{case} command mount does not match its isolated capture directory")
    native_source = option(command, "--user")

    actual_hashes = case_hashes(directory)
    require(set(actual_hashes) == set(NATIVE_FILES) | {"coupon.inp"},
            f"{case} native output file inventory is incomplete or has extras")
    require(record.get("outputs_sha256") == actual_hashes and
            actual_hashes["coupon.inp"] == expected["input"]["sha256"],
            f"{case} output inventory hash or working input differs")
    measured_bytes = sum((directory / name).stat().st_size for name in NATIVE_FILES)
    require(measured_bytes == record.get("native_output_bytes") and
            measured_bytes <= expected["run_limits"]["aggregate_native_output_bytes_each_case"],
            f"{case} measured native output bytes differ from the run record")
    stdout = (directory / "solver.stdout").read_bytes()
    stderr = (directory / "solver.stderr").read_bytes()
    require(b" Job finished" in stdout and stderr == historical_stderr,
            f"{case} lacks normal completion or stderr differs from historical reference")
    return {"record": record, "stdout": stdout, "stderr": stderr,
            "hashes": actual_hashes, "user_option": native_source,
            "output_bytes": measured_bytes}


def require_equal_bytes(left: bytes, right: bytes, label: str) -> None:
    require(left == right, f"Pair differs in byte-exact output {label}")


def compare_pair(expected: dict, helper, old: dict, trace: dict) -> dict:
    compared = {}
    for name in expected["comparison"]["byte_exact_outputs"]:
        a = (HERE / "output/old" / name).read_bytes()
        b = (HERE / "output/trace" / name).read_bytes()
        require_equal_bytes(a, b, name)
        compared[name] = {"byte_identical": True,
                          "old_sha256": sha_bytes(a), "trace_sha256": sha_bytes(b)}
    for name in expected["comparison"]["frd_clock_only_outputs"]:
        a = (HERE / "output/old" / name).read_bytes()
        b = (HERE / "output/trace" / name).read_bytes()
        an, ac = helper.normalize_frd(a)
        bn, bc = helper.normalize_frd(b)
        require(ac == 1 and bc == 1 and an == bn,
                f"Pair differs beyond the single 1UTIME field in {name}")
        compared[name] = {"equal_after_single_1utime_normalization": True,
                          "old_raw_sha256": sha_bytes(a), "trace_raw_sha256": sha_bytes(b),
                          "normalized_sha256": sha_bytes(an)}

    baseline_stdout = (load_prepare().OLD_CAPTURE / "output/solver.stdout").read_bytes()
    baseline = expected["historical_legacy_baseline"]
    old_events = helper.require_legacy_events_unchanged(
        old["stdout"], baseline_stdout, baseline["event_counts"],
        baseline["event_lines_sha256"])
    trace_events = helper.require_legacy_events_unchanged(
        trace["stdout"], baseline_stdout, baseline["event_counts"],
        baseline["event_lines_sha256"])
    require(old_events == trace_events,
            "Paired inherited contact/convergence event records differ")
    require(b"CCXPT_" not in old["stdout"],
            "The historical binary unexpectedly emitted trace-only records")

    trace_contract = expected["comparison"]["trace_contract"]
    parsed_trace = helper.parse_trace(trace["stdout"], trace_contract)
    old_cvg = helper.parse_cvg((HERE / "output/old/coupon.cvg").read_bytes())
    trace_cvg = helper.parse_cvg((HERE / "output/trace/coupon.cvg").read_bytes())
    require(old_cvg == trace_cvg,
            "Paired CVG state identities/contact counts differ")
    coverage = helper.validate_trial_coverage(parsed_trace, trace_cvg)
    trace_summary = helper.trace_coverage(parsed_trace, coverage)
    return {"output_comparisons": compared,
            "legacy_event_counts": baseline["event_counts"],
            "legacy_event_lines_equal_to_historical_and_pair": True,
            "legacy_event_digest": baseline["event_lines_sha256"],
            "trace_coverage": trace_summary,
            "same_state_map_trial_join": False,
            "mechanical_acceptance": False,
            "force_qualification": False,
            "joint_acceptance": False}


def verify_pair() -> dict:
    expected, summary, helper, runner = verify_packet()
    freeze_path = HERE / "input-freeze.json"
    require(freeze_path.is_file(), "Parent input-freeze.json is required")
    frozen, _ = runner.verify_freeze(sha(freeze_path))
    top_path = HERE / "output/execution.json"
    require(top_path.is_file(), "Paired execution record is missing")
    top = read_json(top_path)
    require(top.get("schema") == "ccx223_static_regression_matched_execution/v1" and
            top.get("status") == "CAPTURES_COMPLETE_PENDING_VERIFICATION" and
            top.get("freeze_sha256") == sha(freeze_path) and
            top.get("expected_sha256") == sha(HERE / "expected.json") and
            top.get("input_sha256") == expected["input"]["sha256"] and
            top.get("case_order") == ["old", "trace"] and
            top.get("serialized") is True and top.get("native_execution") is True and
            top.get("mechanical_acceptance") is False and
            top.get("joint_acceptance") is False,
            "Top-level execution record is incomplete or mismatched")
    require([row.get("case") for row in top.get("cases", [])] == ["old", "trace"] and
            all(row.get("status") == "PASS_NATIVE_CAPTURE" for row in top["cases"]),
            "Both serialized cases did not complete successfully")

    historical_stderr = (load_prepare().OLD_CAPTURE / "output/solver.stderr").read_bytes()
    require(sha_bytes(historical_stderr) == expected["historical_legacy_baseline"]["stderr_sha256"],
            "Pinned historical stderr hash differs")
    old = validate_case("old", 1, expected, helper, HERE / "output", historical_stderr)
    trace = validate_case("trace", 2, expected, helper, HERE / "output", historical_stderr)
    require(old["user_option"] == trace["user_option"],
            "Old and trace containers used different user mappings")
    comparisons = compare_pair(expected, helper, old, trace)
    return {
        "schema": VERIFIER_SCHEMA,
        "status": "PASS_MATCHED_STATIC_REGRESSION_TRACE_CAPTURE",
        "expected_sha256": sha(HERE / "expected.json"),
        "freeze_sha256": sha(freeze_path),
        "execution_sha256": sha(top_path),
        "preparation_summary": summary,
        "external_dependency_sha256": frozen["external_dependencies_sha256"],
        "case_order": ["old", "trace"],
        "matched_resources": expected["run_limits"],
        "case_captures": {
            case: {"case_execution_sha256": sha(HERE / "output" / case / "case-execution.json"),
                   "output_bytes": capture["output_bytes"],
                   "outputs_sha256": capture["hashes"],
                   "elapsed_seconds": capture["record"]["elapsed_seconds"]}
            for case, capture in (("old", old), ("trace", trace))
        },
        "comparisons": comparisons,
        "mechanical_acceptance": False,
        "force_qualification": False,
        "joint_acceptance": False,
        "release": False,
    }


def self_test() -> dict:
    expected, _summary, helper, _runner = verify_packet()
    # Parser behavior is already independently qualified in attempt01; this
    # control ensures the paired comparator remains strict and clock-only.
    require_equal_bytes(b"same", b"same", "self-test")
    try:
        require_equal_bytes(b"same", b"diff", "negative-control")
    except RuntimeError:
        rejected_byte_change = True
    else:
        raise RuntimeError("Pair byte comparator accepted a changed byte")
    frd = b"    1UTIME              20:49:13\nX\n"
    normalized, count = helper.normalize_frd(frd)
    require(count == 1 and normalized == b"    1UTIME              <UTIME>\nX\n",
            "Clock-only normalizer changed unexpected bytes")
    try:
        helper.normalize_frd(frd.replace(b"X", b"Y"))
        # This helper only normalizes clocks; the pair comparison rejects the
        # additional byte mutation.
        require_equal_bytes(normalized, b"    1UTIME              <UTIME>\nY\n", "FRD")
    except RuntimeError:
        rejected_frd_change = True
    else:
        raise RuntimeError("FRD comparator accepted a non-clock byte change")
    return {"status": "PASS_MATCHED_COMPARATOR_SELF_TEST",
            "native_run": False,
            "byte_change_rejected": rejected_byte_change,
            "frd_nonclock_change_rejected": rejected_frd_change,
            "trace_parser_source_sha256": expected["comparison"]["trace_contract_source_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Read-only prepared packet/dependency check")
    mode.add_argument("--self-test", action="store_true", help="Run small comparison controls, no native solver")
    mode.add_argument("--verify", action="store_true", help="Verify the two parent-run captures")
    parser.add_argument("--write", action="store_true", help="Write verifier.json after a successful verification")
    args = parser.parse_args()
    if args.check:
        expected, summary, _helper, _runner = verify_packet()
        report = {"status": "PASS_READ_ONLY", "case_order": expected["case_order"], **summary}
    elif args.self_test:
        report = self_test()
    else:
        report = verify_pair()
        if args.write:
            target = HERE / "verifier.json"
            with target.open("xb") as stream:
                stream.write((json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        raise SystemExit(2)
