#!/usr/bin/env python3
"""Prepare a paired, matched-resource static comparison; never runs CCX."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / ".git").exists())
EVAL_REL = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
ATTEMPT01 = ROOT / EVAL_REL / "implicit-contact-point-trace-attempt01/static-regression-attempt01"
OLD_CAPTURE = ROOT / EVAL_REL / "ordinary-external-force-transient-attempt04-diagnostic/coupon-known-answer-attempt02"
OLD_BUILD = ROOT / EVAL_REL / "ordinary-external-force-transient-attempt04-diagnostic/build-attempt02"
TRACE_BUILD = ROOT / EVAL_REL / "implicit-contact-point-trace-attempt01/build-attempt04"

INPUT_SHA = "73f32786bf6dee6c88e78f8e3d4e24f67afb9548225868fd10850c77e27298ab"
OLD_EXECUTION_SHA = "69b7d733f07946d12ce88f86d0bccb36b12a0d6b7e31c838d7ec3844c09e1095"
OLD_VERIFIER_SHA = "d1addc19d8961325f54a45b9c2bdd8914732168a9b91f998a84363be369cf356"
OLD_BUILD_RESULT_SHA = "acd8ecda0285ce2c2983dcc7b67ca9b98d274403d9f4c60db7ee6ba2dc9f6338"
OLD_BUILD_MANIFEST_SHA = "9b1018291c33eb82ac46cb56dee23627eca76dc30f0fa217ed442396e2d27638"
OLD_SOURCE_ARCHIVE_SHA = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
OLD_PATCH_SHA = "aea55ec88be569a39a06482723d5da22260b071bf072c55491448b22ab273e54"
OLD_IMAGE = "sha256:1cc1d52946c5acddc9d4eeaf1dd1bf0bc4d3f564eb1c264f5d29b67c6386b7fa"
OLD_BINARY_PATH = "/usr/local/bin/ccx-attempt04-diagnostic-2.23"
OLD_BINARY_SHA = "3aec6cfe0ca72a463d87c648ed6b4a83ee1bb6a08bf604a144c8a6553d2f439f"
OLD_STDOUT_SHA = "445f9a6ac7fd4f815334c7b9600bcf65978b97712f3967a8121de31a91df8c94"
OLD_STDERR_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

TRACE_EXECUTION_SHA = "e53e7934c87d0e0ec26726e9a7ce1bb9fffb241249d1ceff4964d49b78402c0f"
TRACE_MANIFEST_SHA = "58d2d4c82a1a353cecbf6c9fd6a91286da2d48074c9047690649fa94fb24528b"
TRACE_PATCH_SHA = "8fb9e5a88a72109a095ccb1dab650860535102f7d806f0dd6d230c23127af7ff"
TRACE_FORMAT_SHA = "4b99257628d3a27723a02be6b547dad64ac9bbfe957697d89f19d14e53321917"
TRACE_PARSER_SHA = "ceed4ab5a626f9c2c78f5a6bae4c0977624b93aa9da388246641fad0bc6495e2"
TRACE_EXPECTED_SHA = "41dbbd68035a21d1252dafabd3aab77aea30fcdeb24c3f25df9f97dd962d6c45"
TRACE_IMAGE = "sha256:f00deed9be383c1095cdc03a1556d00cf8982f54100217a05ffae079e8a3bb36"
TRACE_BINARY_PATH = "/usr/local/bin/ccx-contact-point-trace-2.23"
TRACE_BINARY_SHA = "3f949f639ead34b7ca62e2226480635cc0f5dbeda14afc200dcb523cf640b203"

LEGACY_COUNTS = {"CCX223_ATTEMPT04_CONTACT": 8,
                 "CCX223_ATTEMPT04_CONVERGENCE": 16}
OUTPUT_LIMIT = 16 * 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


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
        raise ValueError(f"Nonfinite JSON constant {value} in {path}")

    def finite_float(value):
        result = float(value)
        require(math.isfinite(result), f"Nonfinite JSON number {value} in {path}")
        return result

    return json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                      parse_float=finite_float, parse_constant=reject_constant)


def dependency_rows() -> list[dict]:
    files = {
        "old_build_result": (OLD_BUILD / "build_result.json", OLD_BUILD_RESULT_SHA),
        "old_build_manifest": (OLD_BUILD / "build_manifest.json", OLD_BUILD_MANIFEST_SHA),
        "old_source_archive": (OLD_BUILD / "context/source.tar.bz2", OLD_SOURCE_ARCHIVE_SHA),
        "old_diagnostic_patch": (OLD_BUILD / "context/diagnostic.patch", OLD_PATCH_SHA),
        "historical_execution": (OLD_CAPTURE / "execution.json", OLD_EXECUTION_SHA),
        "historical_verifier": (OLD_CAPTURE / "verifier.json", OLD_VERIFIER_SHA),
        "historical_solver_stdout": (OLD_CAPTURE / "output/solver.stdout", OLD_STDOUT_SHA),
        "historical_solver_stderr": (OLD_CAPTURE / "output/solver.stderr", OLD_STDERR_SHA),
        "attempt01_expected": (ATTEMPT01 / "expected.json", TRACE_EXPECTED_SHA),
        "attempt01_parser": (ATTEMPT01 / "verifier.py", TRACE_PARSER_SHA),
        "trace_build_execution": (TRACE_BUILD / "execution.json", TRACE_EXECUTION_SHA),
        "trace_build_manifest": (TRACE_BUILD / "build-manifest.json", TRACE_MANIFEST_SHA),
        "trace_source_archive": (TRACE_BUILD / "context/source.tar.bz2", OLD_SOURCE_ARCHIVE_SHA),
        "trace_diagnostic_patch": (ATTEMPT01 / "diagnostic.patch", TRACE_PATCH_SHA),
        "trace_format": (ATTEMPT01 / "trace-format.json", TRACE_FORMAT_SHA),
    }
    rows = []
    for key, (path, expected) in files.items():
        require(path.is_file(), f"Pinned dependency missing: {path}")
        actual = file_sha(path)
        require(actual == expected,
                f"Pinned dependency changed for {key}: {actual} != {expected}")
        rows.append({"key": key, "repo_path": str(path.relative_to(ROOT)),
                     "sha256": expected})
    return rows


def build_all() -> tuple[dict[str, bytes], dict]:
    deps = dependency_rows()
    old_result_path = OLD_BUILD / "build_result.json"
    old_manifest_path = OLD_BUILD / "build_manifest.json"
    new_execution_path = TRACE_BUILD / "execution.json"
    new_manifest_path = TRACE_BUILD / "build-manifest.json"
    old_result = read_json(old_result_path)
    old_manifest = read_json(old_manifest_path)
    old_execution = read_json(OLD_CAPTURE / "execution.json")
    old_verifier = read_json(OLD_CAPTURE / "verifier.json")
    new_execution = read_json(new_execution_path)
    new_manifest = read_json(new_manifest_path)

    require(old_result.get("exit_code") == 0 and old_result.get("timed_out") is False and
            old_result.get("image_id") == OLD_IMAGE and
            old_result.get("patched_binary_path") == OLD_BINARY_PATH and
            old_result.get("patched_binary_sha256") == OLD_BINARY_SHA,
            "Historical attempt04 build identity differs")
    require(old_manifest.get("patched_binary_sha256") == OLD_BINARY_SHA and
            old_manifest.get("base_image_id") == old_result.get("base_image_id") and
            old_manifest.get("upstream_source_archive_sha256") == OLD_SOURCE_ARCHIVE_SHA and
            old_manifest.get("patch_sha256") == OLD_PATCH_SHA and
            old_result["build_context_sha256"]["diagnostic.patch"] == OLD_PATCH_SHA,
            "Historical attempt04 build manifest differs")
    require(old_execution.get("status") == "PASS" and
            old_execution.get("input_sha256") == INPUT_SHA and
            old_execution.get("working_deck_sha256") == INPUT_SHA and
            old_execution.get("patched_image_id") == OLD_IMAGE and
            old_execution.get("patched_binary_path") == OLD_BINARY_PATH and
            old_execution.get("patched_binary_sha256") == OLD_BINARY_SHA and
            old_execution.get("mechanical_acceptance") is False and
            old_execution.get("joint_acceptance") is False and
            old_execution.get("errors") == [],
            "Historical attempt04 execution is not the pinned passing output baseline")
    require(old_verifier.get("status") == "PASS" and
            old_verifier.get("execution_sha256") == OLD_EXECUTION_SHA and
            old_verifier.get("mechanical_acceptance") is False and
            old_verifier.get("joint_acceptance") is False and
            old_verifier.get("errors") == [],
            "Historical attempt04 verifier is not the pinned passing output baseline")
    require(new_execution.get("exit_code") == 0 and
            new_execution.get("image_id") == TRACE_IMAGE and
            new_execution.get("binary_path") == TRACE_BINARY_PATH and
            new_execution.get("binary_sha256") == TRACE_BINARY_SHA and
            new_execution.get("build_manifest_sha256") == TRACE_MANIFEST_SHA,
            "Trace build execution identity differs")
    require(new_manifest.get("patched_binary_sha256") == TRACE_BINARY_SHA and
            new_manifest.get("upstream_source_archive_sha256") == OLD_SOURCE_ARCHIVE_SHA and
            new_manifest.get("patch_sha256") == TRACE_PATCH_SHA,
            "Trace build manifest differs")

    old_pins = {
        "build_name": "ordinary-external-force-transient-attempt04-diagnostic/build-attempt02",
        "build_result_sha256": OLD_BUILD_RESULT_SHA,
        "build_manifest_sha256": OLD_BUILD_MANIFEST_SHA,
        "source_archive_sha256": OLD_SOURCE_ARCHIVE_SHA,
        "image_id": OLD_IMAGE,
        "binary_path": OLD_BINARY_PATH,
        "binary_sha256": OLD_BINARY_SHA,
        "patch_sha256": old_result["build_context_sha256"]["diagnostic.patch"],
    }
    trace_pins = {
        "build_name": "implicit-contact-point-trace-attempt01/build-attempt04",
        "build_execution_sha256": TRACE_EXECUTION_SHA,
        "build_manifest_sha256": TRACE_MANIFEST_SHA,
        "source_archive_sha256": OLD_SOURCE_ARCHIVE_SHA,
        "image_id": TRACE_IMAGE,
        "binary_path": TRACE_BINARY_PATH,
        "binary_sha256": TRACE_BINARY_SHA,
        "patch_sha256": TRACE_PATCH_SHA,
        "trace_format_sha256": TRACE_FORMAT_SHA,
    }
    pins = {
        "schema": "ccx223_static_regression_matched_build_pins/v1",
        "old": old_pins,
        "trace": trace_pins,
        "dependency_list_sha256": sha(json_bytes(deps)),
        "native_execution": False,
    }
    pins_bytes = json_bytes(pins)
    deps_record = {"schema": "ccx223_static_regression_external_dependencies/v1",
                   "files": deps, "native_execution": False}

    # The event-line digest and schema are inherited from the reviewed packet.
    old_expected_path = ATTEMPT01 / "expected.json"
    prior_expected = read_json(old_expected_path)
    trace_contract = read_json(ATTEMPT01 / "trace-format.json")
    require(prior_expected.get("trace_contract") == trace_contract and
            prior_expected.get("trace_coverage_requirements", {}).get(
                "trial_row_count_equals_cvg_contact_count_per_identity") is True and
            prior_expected.get("baseline", {}).get("legacy_event_counts") == LEGACY_COUNTS,
            "Attempt01 trace parser/coverage/event contract differs")
    old_event_digest = prior_expected["baseline"]["legacy_event_lines_sha256"]
    source_stdout = OLD_CAPTURE / "output/solver.stdout"
    require(file_sha(source_stdout) == OLD_STDOUT_SHA,
            "Historical output stdout does not match pinned baseline")
    input_src = OLD_CAPTURE / "input/coupon.inp"
    input_bytes = input_src.read_bytes()
    require(sha(input_bytes) == INPUT_SHA and
            sha((ATTEMPT01 / "input/coupon.inp").read_bytes()) == INPUT_SHA,
            "The copied coupon input differs from the required common input")

    expected = {
        "schema": "ccx223_static_regression_matched_comparison/v1",
        "preparation_script_sha256": file_sha(HERE / "prepare.py"),
        "runner_script_sha256": file_sha(HERE / "run.py"),
        "verifier_script_sha256": file_sha(HERE / "verifier.py"),
        "readme_sha256": file_sha(HERE / "README.md"),
        "input": {"path": "input/coupon.inp", "sha256": INPUT_SHA,
                  "source_execution_sha256": OLD_EXECUTION_SHA},
        "case_order": ["old", "trace"],
        "build_pins": {"old": old_pins, "trace": trace_pins},
        "historical_legacy_baseline": {
            "source_execution_sha256": OLD_EXECUTION_SHA,
            "source_verifier_sha256": OLD_VERIFIER_SHA,
            "stdout_sha256": OLD_STDOUT_SHA,
            "stderr_sha256": OLD_STDERR_SHA,
            "event_counts": LEGACY_COUNTS,
            "event_lines_sha256": old_event_digest,
        },
        "comparison": {
            "byte_exact_outputs": ["coupon.12d", "coupon.cel", "coupon.cvg",
                                   "coupon.dat", "coupon.sta", "spooles.out"],
            "frd_clock_only_outputs": ["coupon.frd", "ResultsForLastIterations.frd"],
            "frd_normalization": "replace the single 1UTIME token only",
            "legacy_attempt04_events_equal_historical_and_pair": True,
            "trace_only_case": "trace",
            "trace_contract_source_sha256": TRACE_PARSER_SHA,
            "trace_coverage_contract": prior_expected["trace_coverage_requirements"],
            "trace_contract": trace_contract,
            "no_force_or_mechanical_qualification": True,
        },
        "run_limits": {
            "wall_seconds_each_case": 60,
            "cpus_each_case": 1,
            "memory_bytes_each_case": 1073741824,
            "memory_plus_swap_bytes_each_case": 1073741824,
            "network_each_case": "none",
            "aggregate_native_output_bytes_each_case": OUTPUT_LIMIT,
            "serialized_case_order": ["old", "trace"],
            "omp_threads": 1,
            "ccx_solver_processes": 1,
            "no_overlap": True,
        },
        "source_dependency_list_sha256": sha(json_bytes(deps_record)),
        "scope": {
            "purpose": "matched-resource output regression between frozen old diagnostic binary and trace-instrumented build",
            "mechanical_acceptance": False,
            "force_qualification": False,
            "joint_acceptance": False,
            "current_joint_eligibility": False,
        },
    }
    input_src_bytes = input_bytes
    artifacts = {
        "build-pins.json": pins_bytes,
        "source-dependencies.json": json_bytes(deps_record),
        "input/coupon.inp": input_src_bytes,
        "expected.json": json_bytes(expected),
    }
    expected_sha = sha(artifacts["expected.json"])
    readiness = {
        "schema": "ccx223_static_regression_matched_readiness/v1",
        "status": "PREPARED_FOR_PARENT_REVIEW_NOT_FROZEN_NOT_EXECUTED",
        "expected_sha256": expected_sha,
        "input_sha256": INPUT_SHA,
        "source_dependency_list_sha256": sha(artifacts["source-dependencies.json"]),
        "case_order": ["old", "trace"],
        "matched_resources": {"cpus": 1, "threads": 1,
                              "memory_bytes": 1073741824,
                              "network": "none", "wall_seconds": 60,
                              "per_case_output_bytes": OUTPUT_LIMIT},
        "freeze_created": False,
        "native_execution": False,
        "mechanical_acceptance": False,
        "joint_acceptance": False,
    }
    artifacts["readiness.json"] = json_bytes(readiness)
    return artifacts, {"expected_sha256": expected_sha,
                       "input_sha256": INPUT_SHA,
                       "old_image_id": OLD_IMAGE,
                       "trace_image_id": TRACE_IMAGE,
                       "artifact_count": len(artifacts)}


def json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_exclusive(artifacts: dict[str, bytes]) -> None:
    paths = [HERE / rel for rel in artifacts]
    require(all(not path.exists() for path in paths),
            "Refusing to overwrite an existing prepared artifact")
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    for rel, payload in artifacts.items():
        with (HERE / rel).open("xb") as stream:
            stream.write(payload)


def check_artifacts(artifacts: dict[str, bytes]) -> None:
    for rel, expected in artifacts.items():
        path = HERE / rel
        require(path.is_file(), f"Prepared file missing: {rel}")
        require(path.read_bytes() == expected,
                f"Prepared bytes differ from source producer: {rel}")
    expected_paths = set(artifacts) | {"README.md", "prepare.py", "run.py", "verifier.py"}
    if (HERE / "input-freeze.json").is_file():
        expected_paths.add("input-freeze.json")
    if (HERE / "parent-review.json").is_file():
        expected_paths.add("parent-review.json")
    for name in ("verifier.json", "RESULTS.md", "independent-review.md"):
        if (HERE / name).is_file():
            expected_paths.add(name)
    if (HERE / "output").is_dir():
        expected_paths.update(str(p.relative_to(HERE)) for p in (HERE / "output").rglob("*") if p.is_file())
    actual = {str(p.relative_to(HERE)) for p in HERE.rglob("*") if p.is_file()}
    require(actual == expected_paths,
            f"Packet inventory differs; unexpected={sorted(actual-expected_paths)}, missing={sorted(expected_paths-actual)}")
    for row in read_json(HERE / "source-dependencies.json")["files"]:
        path = ROOT / row["repo_path"]
        require(path.is_file() and file_sha(path) == row["sha256"],
                f"Pinned external source changed: {row['repo_path']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Reproduce the prepared packet read-only")
    args = parser.parse_args()
    artifacts, summary = build_all()
    if args.check:
        check_artifacts(artifacts)
    else:
        write_exclusive(artifacts)
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write",
                      **summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
