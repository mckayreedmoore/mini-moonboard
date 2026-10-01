#!/usr/bin/env python3
"""Prepare a frozen-baseline regression packet; never launches CalculiX."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
TRACE = HERE.parent
ROOT = next(parent for parent in HERE.parents if (parent / ".git").exists())
EVAL_REL = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
BUILD = TRACE / "build-attempt04"
OLD = ROOT / EVAL_REL / "ordinary-external-force-transient-attempt04-diagnostic/coupon-known-answer-attempt02"
OLD_TRACE_EXECUTION_SHA = "69b7d733f07946d12ce88f86d0bccb36b12a0d6b7e31c838d7ec3844c09e1095"
OLD_TRACE_VERIFIER_SHA = "d1addc19d8961325f54a45b9c2bdd8914732168a9b91f998a84363be369cf356"
INPUT_SHA = "73f32786bf6dee6c88e78f8e3d4e24f67afb9548225868fd10850c77e27298ab"
BUILD_EXECUTION_SHA = "e53e7934c87d0e0ec26726e9a7ce1bb9fffb241249d1ceff4964d49b78402c0f"
BUILD_MANIFEST_SHA = "58d2d4c82a1a353cecbf6c9fd6a91286da2d48074c9047690649fa94fb24528b"
SOURCE_ARCHIVE_SHA = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
TRACE_FORMAT_NAME = "trace-format.json"
OUTPUT_LIMIT_BYTES = 16 * 1024 * 1024
OLD_COMPARE_EXACT = (
    "coupon.12d", "coupon.cel", "coupon.cvg", "coupon.dat",
    "coupon.sta", "spooles.out",
)
OLD_COMPARE_FRD = ("coupon.frd", "ResultsForLastIterations.frd")
REFERENCE_CAPTURE_FILES = (
    *OLD_COMPARE_EXACT, *OLD_COMPARE_FRD, "solver.stdout", "solver.stderr",
)
UTIME_RE = re.compile(
    rb"(?m)^([ \t]*1UTIME[ \t]+)[0-9]{2}:[0-9]{2}:[0-9]{2}([^\r\n]*)$"
)
LEGACY_KEYS = {
    "CCX223_ATTEMPT04_CONTACT": {
        "event", "step", "increment", "attempt", "iteration",
        "contact_old", "contact_new", "delcon", "contact_change_flag",
    },
    "CCX223_ATTEMPT04_CONVERGENCE": {
        "event", "step", "increment", "attempt", "iteration",
        "mechanical_applicable", "iteration_ok", "mechanical_residual_ok",
        "displacement_ok", "visco_ok", "contact_change_gate_clear",
        "no_contact_now", "no_contact_at_start", "contact_present",
        "mechanical_gate_ok", "no_contact_energy_eligible",
        "contact_energy_eligible", "iconvergence", "idivergence",
        "final_convergence_ok",
    },
}
LEGACY_COUNTS = {
    "CCX223_ATTEMPT04_CONTACT": 8,
    "CCX223_ATTEMPT04_CONVERGENCE": 16,
}


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


def normalized_frd(data: bytes) -> bytes:
    replaced, count = UTIME_RE.subn(rb"\1<UTIME>\2", data)
    require(count == 1, f"Expected exactly one 1UTIME row, found {count}")
    return replaced


def legacy_events(stdout: bytes) -> list[dict]:
    records = []
    for lineno, raw in enumerate(stdout.splitlines(), 1):
        if b"CCX223_ATTEMPT04_" not in raw:
            continue
        try:
            record = json.loads(raw.decode("ascii"))
        except Exception as exc:
            raise RuntimeError(f"Invalid inherited event at stdout line {lineno}: {exc}") from exc
        event = record.get("event")
        require(event in LEGACY_KEYS,
                f"Unknown inherited attempt04 event at stdout line {lineno}: {event}")
        require(set(record) == LEGACY_KEYS[event],
                f"Inherited event fields differ at stdout line {lineno}: {event}")
        for key, value in record.items():
            if key == "event":
                continue
            if isinstance(value, float):
                require(math.isfinite(value), f"Nonfinite inherited event {key}")
            else:
                require(isinstance(value, int) and not isinstance(value, bool),
                        f"Unexpected inherited event type for {key}")
        records.append(record)
    counts = Counter(record["event"] for record in records)
    require(dict(counts) == LEGACY_COUNTS,
            f"Old inherited event counts differ: {dict(counts)}")
    conv_keys = {(r["step"], r["increment"], r["attempt"], r["iteration"])
                 for r in records if r["event"] == "CCX223_ATTEMPT04_CONVERGENCE"}
    expected_conv = {(1, inc, 1, it) for inc in range(1, 9) for it in (1, 2)}
    require(conv_keys == expected_conv, "Old convergence-event coverage differs")
    contact_keys = {(r["step"], r["increment"], r["attempt"], r["iteration"])
                    for r in records if r["event"] == "CCX223_ATTEMPT04_CONTACT"}
    expected_contact = {(1, inc, 1, 2) for inc in range(1, 9)}
    require(contact_keys == expected_contact, "Old contact-event coverage differs")
    return records


def build_pin_artifacts() -> tuple[dict[str, bytes], dict]:
    execution_path = BUILD / "execution.json"
    manifest_path = BUILD / "build-manifest.json"
    build_freeze_path = BUILD / "input-freeze.json"
    patch_path = BUILD / "context/diagnostic.patch"
    lock_path = BUILD / "context/diagnostic-lock.json"
    trace_format_path = TRACE / TRACE_FORMAT_NAME
    for path in (execution_path, manifest_path, build_freeze_path,
                 patch_path, lock_path, trace_format_path):
        require(path.is_file(), f"Required final build/source artifact missing: {path}")
    require(file_sha(execution_path) == BUILD_EXECUTION_SHA,
            "Build-attempt04 execution pin changed")
    require(file_sha(manifest_path) == BUILD_MANIFEST_SHA,
            "Build-attempt04 manifest pin changed")
    execution = read_json(execution_path)
    manifest = read_json(manifest_path)
    lock = read_json(lock_path)
    require(execution.get("schema") == "ccx_contact_point_trace_build_execution/v1" and
            execution.get("exit_code") == 0 and execution.get("timed_out") is False and
            execution.get("context_unchanged") is True,
            "Build-attempt04 did not complete cleanly")
    require(execution.get("image_id") == "sha256:f00deed9be383c1095cdc03a1556d00cf8982f54100217a05ffae079e8a3bb36" and
            execution.get("image_tag") == "mini-moonboard-fea:ccx-contact-point-trace-20260927-v3" and
            execution.get("binary_path") == "/usr/local/bin/ccx-contact-point-trace-2.23" and
            execution.get("binary_sha256") == "3f949f639ead34b7ca62e2226480635cc0f5dbeda14afc200dcb523cf640b203",
            "Build-attempt04 image or binary identity differs")
    require(file_sha(patch_path) == lock.get("patch", {}).get("sha256") ==
            manifest.get("patch_sha256"), "Build patch does not match lock and manifest")
    require(file_sha(lock_path) == manifest.get("diagnostic_lock_sha256"),
            "Build lock differs from build manifest")
    require(manifest.get("upstream_source_archive_sha256") ==
            lock.get("official_source_archive", {}).get("sha256") == SOURCE_ARCHIVE_SHA and
            manifest.get("complete_source_manifest_match") is True and
            manifest.get("patched_binary_sha256") == execution.get("binary_sha256") and
            manifest.get("patched_binary_path") == execution.get("binary_path") and
            manifest.get("mechanical_acceptance") is False,
            "Build manifest source, binary, or scope pins differ")
    trace_format = read_json(trace_format_path)
    require(trace_format.get("schema") == "ccx223_contact_point_trace_format/v1",
            "Unexpected trace-format schema")
    expected_lengths = {
        "CCXPT_MAP": (13, 12), "CCXPT_UNMAPPED": (10, 0),
        "CCXPT_TRIAL": (11, 13),
    }
    for tag, (n_int, n_real) in expected_lengths.items():
        spec = trace_format.get("tags", {}).get(tag, {})
        require(len(spec.get("integer_fields", [])) == n_int and
                len(spec.get("real_fields", [])) == n_real,
                f"Trace-format field count mismatch for {tag}")
    build_pins = {
        "schema": "contact_point_trace_static_regression_build_pins/v1",
        "build_attempt": "build-attempt04",
        "build_execution_sha256": file_sha(execution_path),
        "build_manifest_sha256": file_sha(manifest_path),
        "build_freeze_sha256": file_sha(build_freeze_path),
        "build_completed_utc": execution["ended_utc"],
        "image_tag": execution["image_tag"],
        "image_id": execution["image_id"],
        "binary_path": execution["binary_path"],
        "binary_sha256": execution["binary_sha256"],
        "base_image_id": manifest["base_image_id"],
        "source_archive_sha256": manifest["upstream_source_archive_sha256"],
        "diagnostic_patch_sha256": manifest["patch_sha256"],
        "diagnostic_lock_sha256": file_sha(lock_path),
        "patched_source_member_sha256": manifest["patched_source_member_sha256"],
        "original_source_member_sha256": manifest["original_source_member_sha256"],
        "trace_format_sha256": file_sha(trace_format_path),
        "trace_format_source": str(trace_format_path.relative_to(ROOT)),
        "scope": "coupon-only output instrumentation; not a mechanics or joint acceptance build",
        "mechanical_acceptance": False,
        "joint_acceptance": False,
    }
    build_bytes = (json.dumps(build_pins, indent=2, sort_keys=True) + "\n").encode()
    return {
        "diagnostic.patch": patch_path.read_bytes(),
        "trace-format.json": trace_format_path.read_bytes(),
        "build-pins.json": build_bytes,
    }, build_pins


def build_all() -> tuple[dict[str, bytes], dict]:
    build_artifacts, build_pins = build_pin_artifacts()
    input_src = OLD / "input/coupon.inp"
    old_exec_path = OLD / "execution.json"
    old_verifier_path = OLD / "verifier.json"
    stdout_src = OLD / "output/solver.stdout"
    stderr_src = OLD / "output/solver.stderr"
    for path in (input_src, old_exec_path, old_verifier_path, stdout_src, stderr_src):
        require(path.is_file(), f"Required frozen attempt04 source missing: {path}")
    input_bytes = input_src.read_bytes()
    require(sha(input_bytes) == INPUT_SHA, "Coupon input SHA differs from required contract")
    old_exec = read_json(old_exec_path)
    old_verifier = read_json(old_verifier_path)
    require(file_sha(old_exec_path) == OLD_TRACE_EXECUTION_SHA and
            old_exec.get("status") == "PASS" and old_exec.get("input_sha256") == INPUT_SHA and
            old_exec.get("working_deck_sha256") == INPUT_SHA and
            old_exec.get("numerical_output_equivalence") is True and
            old_exec.get("trace_alignment_pass") is True and
            old_exec.get("mechanical_acceptance") is False and
            old_exec.get("joint_acceptance") is False and old_exec.get("errors") == [],
            "Old attempt04 result is not the expected passing coupon baseline")
    require(file_sha(old_verifier_path) == OLD_TRACE_VERIFIER_SHA and
            old_verifier.get("status") == "PASS" and
            old_verifier.get("execution_sha256") == file_sha(old_exec_path) and
            old_verifier.get("verifier_script_sha256") == file_sha(OLD / "run_and_verify.py") and
            old_verifier.get("numerical_and_iteration_checks", {}).get(
                "numerical_output_equivalence") is True and
            old_verifier.get("numerical_and_iteration_checks", {}).get(
                "trace_alignment_pass") is True and
            old_verifier.get("mechanical_acceptance") is False and
            old_verifier.get("joint_acceptance") is False,
            "Old attempt04 verifier is not the expected baseline")
    require(old_exec.get("verifier_script_sha256") == file_sha(OLD / "run_and_verify.py") and
            old_exec.get("stdout_sha256") == file_sha(stdout_src) and
            old_exec.get("stderr_sha256") == file_sha(stderr_src),
            "Old baseline source/run output hashes do not cross-check")
    event_records = legacy_events(stdout_src.read_bytes())
    require(old_exec.get("expected_trace_counts") == {
        "iterations": 16, "increments": 8,
        "convergence_events": 16, "contact_events": 8,
    }, "Old execution trace-count contract differs")

    ref_files = {}
    artifacts: dict[str, bytes] = dict(build_artifacts)
    artifacts["input/coupon.inp"] = input_bytes
    for name in REFERENCE_CAPTURE_FILES:
        source = OLD / "output" / name
        require(source.is_file(), f"Old attempt04 baseline artifact missing: {name}")
        payload = source.read_bytes()
        dest = f"reference/{name}"
        artifacts[dest] = payload
        item = {"sha256": sha(payload), "size_bytes": len(payload)}
        if name in OLD_COMPARE_FRD:
            normalized = normalized_frd(payload)
            item["normalized_1utime_sha256"] = sha(normalized)
            item["normalization"] = "single 1UTIME clock token replaced; all other bytes preserved"
        ref_files[name] = item
    legacy_raw_lines = [line for line in (OLD / "output/solver.stdout").read_bytes().splitlines()
                        if b"CCX223_ATTEMPT04_" in line]
    expected = {
        "schema": "ccx223_contact_point_trace_static_regression/v1",
        "preparation_script_sha256": file_sha(HERE / "prepare.py"),
        "runner_script_sha256": file_sha(HERE / "run.py"),
        "verifier_script_sha256": file_sha(HERE / "verifier.py"),
        "readme_sha256": file_sha(HERE / "README.md"),
        "input": {"path": "input/coupon.inp", "sha256": INPUT_SHA},
        "baseline": {
            "origin": str(OLD.relative_to(ROOT)),
            "execution_sha256": file_sha(old_exec_path),
            "verifier_sha256": file_sha(old_verifier_path),
            "stdout_sha256": file_sha(stdout_src),
            "stderr_sha256": file_sha(stderr_src),
            "status": "PASS",
            "numerical_output_equivalence": True,
            "trace_alignment_pass": True,
            "mechanical_acceptance": False,
            "joint_acceptance": False,
            "legacy_event_counts": LEGACY_COUNTS,
            "legacy_event_lines_sha256": sha(b"\n".join(legacy_raw_lines) + b"\n"),
            "reference_artifacts": ref_files,
            "byte_equal_outputs": list(OLD_COMPARE_EXACT),
            "frd_utime_only_outputs": list(OLD_COMPARE_FRD),
        },
        "source_binding": build_pins,
        "trace_contract": read_json(TRACE / TRACE_FORMAT_NAME),
        "run_limits": {
            "wall_seconds": 60,
            "cpus": 1,
            "memory_bytes": 1073741824,
            "memory_plus_swap_bytes": 1073741824,
            "network": "none",
            "aggregate_native_output_bytes": OUTPUT_LIMIT_BYTES,
        },
        "trace_coverage_requirements": {
            "CCXPT_MAP_min_rows": 1,
            "CCXPT_TRIAL_min_rows": 1,
            "CCXPT_UNMAPPED_min_rows": 0,
            "trial_row_count_equals_cvg_contact_count_per_identity": True,
            "trial_identity_fields": ["step", "increment", "attempt", "iteration"],
            "trial_unique_within_identity": ["element", "gauss_index"],
            "interpretation": "Counts only; do not join generation and corrected-state trial rows as same-state identities.",
            "native_isol": "Preserve as integer; nonzero indicates generated, not a Boolean encoding.",
            "spring_energy": "Available only when energy_enabled==1; otherwise emitted zero is an unavailable placeholder.",
        },
        "scope": {
            "case": "same frozen mechanical coupon input; static surface-to-surface mortar contact",
            "mechanical_acceptance": False,
            "joint_acceptance": False,
            "force_qualification": False,
            "current_joint_eligibility": False,
        },
    }
    artifacts["expected.json"] = (json.dumps(expected, indent=2, sort_keys=True) + "\n").encode()
    readiness = {
        "schema": "ccx223_contact_point_trace_static_regression_readiness/v1",
        "status": "PREPARED_FOR_PARENT_REVIEW_NOT_FROZEN_NOT_EXECUTED",
        "generated_utc": build_pins["build_completed_utc"],
        "expected_sha256": sha(artifacts["expected.json"]),
        "input_sha256": INPUT_SHA,
        "baseline_execution_sha256": file_sha(old_exec_path),
        "build_execution_sha256": build_pins["build_execution_sha256"],
        "patch_sha256": build_pins["diagnostic_patch_sha256"],
        "image_id": build_pins["image_id"],
        "binary_sha256": build_pins["binary_sha256"],
        "trace_format_sha256": build_pins["trace_format_sha256"],
        "freeze_created": False,
        "native_execution": False,
        "joint_acceptance": False,
    }
    artifacts["readiness.json"] = (json.dumps(readiness, indent=2, sort_keys=True) + "\n").encode()
    return artifacts, {
        "input_sha256": INPUT_SHA,
        "expected_sha256": sha(artifacts["expected.json"]),
        "build_execution_sha256": build_pins["build_execution_sha256"],
        "patch_sha256": build_pins["diagnostic_patch_sha256"],
        "artifact_count": len(artifacts),
    }


def write_exclusive(artifacts: dict[str, bytes]) -> None:
    paths = [HERE / relative for relative in artifacts]
    require(all(not path.exists() for path in paths),
            "Refusing to overwrite prepared artifact(s)")
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    for relative, payload in artifacts.items():
        with (HERE / relative).open("xb") as stream:
            stream.write(payload)


def check_artifacts(artifacts: dict[str, bytes]) -> None:
    for relative, expected in artifacts.items():
        path = HERE / relative
        require(path.is_file(), f"Prepared artifact missing: {relative}")
        require(path.read_bytes() == expected,
                f"Prepared artifact differs from current source snapshot: {relative}")
    actual = {str(path.relative_to(HERE)) for path in HERE.rglob("*") if path.is_file()}
    expected_paths = set(artifacts) | {
        "README.md", "prepare.py", "run.py", "verifier.py",
    }
    if (HERE / "input-freeze.json").exists():
        expected_paths.add("input-freeze.json")
    if (HERE / "parent-review.json").exists():
        expected_paths.add("parent-review.json")
    for optional in ("verifier.json", "RESULTS.md", "independent-review.md"):
        if (HERE / optional).exists():
            expected_paths.add(optional)
    if (HERE / "output").exists():
        expected_paths |= {str(path.relative_to(HERE)) for path in (HERE / "output").rglob("*") if path.is_file()}
    extra = actual - expected_paths
    missing = expected_paths - actual
    require(not extra, f"Unexpected packet files: {sorted(extra)}")
    require(not missing, f"Expected packet files missing: {sorted(missing)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verify prepared bytes read-only")
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
