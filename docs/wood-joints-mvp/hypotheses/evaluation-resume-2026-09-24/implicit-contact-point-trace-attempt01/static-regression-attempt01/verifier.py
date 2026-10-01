#!/usr/bin/env python3
"""Audit one frozen static coupon capture; this verifier never runs CCX."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
FREEZE = HERE / "input-freeze.json"
EXPECTED_SCHEMA = "ccx223_contact_point_trace_static_regression/v1"
FREEZE_SCHEMA = "ccx223_contact_point_trace_static_regression_freeze/v1"
EXECUTION_SCHEMA = "ccx223_contact_point_trace_static_regression_execution/v1"
VERIFIER_SCHEMA = "ccx223_contact_point_trace_static_regression_verifier/v1"
EXACT_OUTPUTS = ("coupon.12d", "coupon.cel", "coupon.cvg", "coupon.dat",
                 "coupon.sta", "spooles.out")
FRD_OUTPUTS = ("coupon.frd", "ResultsForLastIterations.frd")
NUMBER_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?\Z")
INT_RE = re.compile(r"[+-]?\d+\Z")
UTIME_RE = re.compile(
    rb"(?m)^([ \t]*1UTIME[ \t]+)[0-9]{2}:[0-9]{2}:[0-9]{2}([^\r\n]*)$"
)
LEGACY_TAGS = {
    "CCX223_ATTEMPT04_CONTACT",
    "CCX223_ATTEMPT04_CONVERGENCE",
}
OUTPUT_LIMIT = 16 * 1024 * 1024


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


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
        result = float(value)
        require(math.isfinite(result), f"Nonfinite JSON number {value} in {path}")
        return result

    return json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                      parse_float=finite_float, parse_constant=reject_constant)


def load_prepare():
    spec = importlib.util.spec_from_file_location("ccxpt_static_prepare", HERE / "prepare.py")
    require(spec is not None and spec.loader is not None, "Cannot load prepare.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_runner():
    spec = importlib.util.spec_from_file_location("ccxpt_static_runner", HERE / "run.py")
    require(spec is not None and spec.loader is not None, "Cannot load run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_packet(expected: dict) -> dict:
    require(expected.get("schema") == EXPECTED_SCHEMA, "Unexpected expected.json schema")
    prep = load_prepare()
    artifacts, summary = prep.build_all()
    prep.check_artifacts(artifacts)
    require(expected.get("preparation_script_sha256") == sha(HERE / "prepare.py") and
            expected.get("runner_script_sha256") == sha(HERE / "run.py") and
            expected.get("verifier_script_sha256") == sha(HERE / "verifier.py") and
            expected.get("readme_sha256") == sha(HERE / "README.md"),
            "Expected.json does not bind the current packet scripts and README")
    coverage = expected.get("trace_coverage_requirements", {})
    require(coverage.get("CCXPT_MAP_min_rows") == 1 and
            coverage.get("CCXPT_TRIAL_min_rows") == 1 and
            coverage.get("CCXPT_UNMAPPED_min_rows") == 0 and
            coverage.get("trial_row_count_equals_cvg_contact_count_per_identity") is True and
            coverage.get("trial_identity_fields") ==
            ["step", "increment", "attempt", "iteration"] and
            coverage.get("trial_unique_within_identity") == ["element", "gauss_index"],
            "Frozen trace coverage contract is incomplete or changed")
    return summary


def validate_trace_schema(contract: dict) -> dict:
    require(contract.get("schema") == "ccx223_contact_point_trace_format/v1",
            "Unexpected trace-format schema")
    tags = contract.get("tags")
    require(isinstance(tags, dict) and set(tags) == {
        "CCXPT_MAP", "CCXPT_UNMAPPED", "CCXPT_TRIAL"},
        "Trace tag inventory differs")
    wanted_counts = {"CCXPT_MAP": (13, 12), "CCXPT_UNMAPPED": (10, 0),
                     "CCXPT_TRIAL": (11, 13)}
    for tag, counts in wanted_counts.items():
        fields = tags[tag]
        require((len(fields.get("integer_fields", [])),
                 len(fields.get("real_fields", []))) == counts,
                f"Trace field cardinality differs for {tag}")
        require(len(set(fields["integer_fields"])) == len(fields["integer_fields"]) and
                len(set(fields["real_fields"])) == len(fields["real_fields"]),
                f"Duplicate field names for {tag}")
    return tags


def parse_trace(stdout: bytes, contract: dict) -> dict[str, list[dict]]:
    tags = validate_trace_schema(contract)
    parsed = {tag: [] for tag in tags}
    try:
        lines = stdout.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("Solver stdout is not strict ASCII") from exc
    for lineno, line in enumerate(lines, 1):
        if "CCXPT_" not in line:
            continue
        tokens = line.split()
        require(bool(tokens), f"Empty trace line {lineno}")
        tag = tokens[0]
        require(tag in tags,
                f"Unknown or malformed CCXPT record at line {lineno}: {tag}")
        spec = tags[tag]
        int_fields = spec["integer_fields"]
        real_fields = spec["real_fields"]
        require(len(tokens) == 1 + len(int_fields) + len(real_fields),
                f"Wrong field count on {tag} line {lineno}")
        row = {"tag": tag}
        offset = 1
        for field in int_fields:
            token = tokens[offset]
            require(INT_RE.fullmatch(token) is not None,
                    f"Noninteger field {field} on {tag} line {lineno}: {token}")
            row[field] = int(token, 10)
            offset += 1
        for field in real_fields:
            token = tokens[offset]
            require(NUMBER_RE.fullmatch(token) is not None,
                    f"Malformed real field {field} on {tag} line {lineno}: {token}")
            value = float(token)
            require(math.isfinite(value),
                    f"Nonfinite field {field} on {tag} line {lineno}")
            row[field] = value
            offset += 1
        if tag == "CCXPT_MAP":
            # `native_isol` is the native solver integer, not a Boolean field.
            row["generated"] = row["native_isol"] != 0
        elif tag == "CCXPT_TRIAL":
            # The trace code writes a zero placeholder if *nener is not 1.
            row["spring_energy_available"] = row["energy_enabled"] == 1
            row["spring_energy_observed"] = (
                row["spring_energy"] if row["spring_energy_available"] else None)
        parsed[tag].append(row)
    counts = {tag: len(rows) for tag, rows in parsed.items()}
    require(counts["CCXPT_MAP"] >= 1,
            "No mapped contact-generation records were captured")
    require(counts["CCXPT_TRIAL"] >= 1,
            "No corrected active-spring trial records were captured")
    return parsed


def parse_cvg(data: bytes) -> dict[tuple[int, int, int, int], int]:
    """Read strict convergence identities and the native contact-element count."""
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("coupon.cvg is not strict ASCII") from exc
    rows = {}
    for lineno, line in enumerate(lines, 1):
        tokens = line.split()
        if not tokens or INT_RE.fullmatch(tokens[0]) is None:
            continue
        require(len(tokens) == 9,
                f"Malformed numeric .cvg row at line {lineno}: expected 9 fields")
        require(all(INT_RE.fullmatch(token) for token in tokens[:5]),
                f"Malformed .cvg identity/count at line {lineno}")
        key = tuple(int(token, 10) for token in tokens[:4])
        contact_count = int(tokens[4], 10)
        require(contact_count >= 0, f"Negative contact count in .cvg row {lineno}")
        for token in tokens[5:]:
            require(NUMBER_RE.fullmatch(token) is not None,
                    f"Malformed numeric .cvg value at line {lineno}")
            value = float(token)
            require(math.isfinite(value), f"Nonfinite .cvg value at line {lineno}")
        require(key not in rows, f"Duplicate .cvg identity {key}")
        rows[key] = contact_count
    require(bool(rows), "coupon.cvg contains no parsed convergence states")
    return rows


def validate_trial_coverage(parsed: dict[str, list[dict]],
                            cvg_counts: dict[tuple[int, int, int, int], int]) -> dict:
    """Require exact CVG-key and native contact-count coverage for TRIAL rows."""
    groups = defaultdict(list)
    for row in parsed["CCXPT_TRIAL"]:
        key = (row["step"], row["increment"], row["attempt"], row["iteration"])
        groups[key].append(row)
    require(set(groups) == set(cvg_counts),
            "CCXPT_TRIAL identity set does not exactly cover .cvg states")
    per_state = {}
    for key, expected_count in cvg_counts.items():
        rows = groups[key]
        require(len(rows) == expected_count,
                f"CCXPT_TRIAL row count differs from .cvg native contact count at {key}")
        elements = [row["element"] for row in rows]
        gauss = [row["gauss_index"] for row in rows]
        pairs = [(row["element"], row["gauss_index"]) for row in rows]
        require(len(set(elements)) == len(elements),
                f"Duplicate trial element ID at {key}")
        require(len(set(gauss)) == len(gauss),
                f"Duplicate trial Gauss-point ID at {key}")
        require(len(set(pairs)) == len(pairs),
                f"Duplicate trial element/Gauss identity at {key}")
        per_state["/".join(str(value) for value in key)] = {
            "cvg_contact_count": expected_count,
            "trial_row_count": len(rows),
            "unique_element_ids": len(set(elements)),
            "unique_gauss_ids": len(set(gauss)),
        }
    return {"cvg_state_count": len(cvg_counts),
            "trial_state_count": len(groups), "per_state": per_state}


def legacy_event_lines(stdout: bytes) -> list[bytes]:
    lines = []
    for lineno, line in enumerate(stdout.splitlines(), 1):
        if b"CCX223_ATTEMPT04_" not in line:
            continue
        try:
            record = read_json_bytes(line)
        except Exception as exc:
            raise ValueError(f"Malformed inherited event at stdout line {lineno}: {exc}") from exc
        event = record.get("event")
        require(event in LEGACY_TAGS,
                f"Unexpected inherited attempt04 event at stdout line {lineno}: {event}")
        lines.append(line)
    return lines


def read_json_bytes(data: bytes) -> dict:
    def unique_pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"Duplicate JSON key {key} in event line")
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError(f"Nonfinite JSON constant {value}")
    def finite_float(value):
        parsed = float(value)
        require(math.isfinite(parsed), f"Nonfinite JSON number {value}")
        return parsed
    return json.loads(data.decode("ascii"), object_pairs_hook=unique_pairs,
                      parse_float=finite_float, parse_constant=reject_constant)


def check_legacy_event_coverage(stdout: bytes, expected_counts: dict) -> list[bytes]:
    lines = legacy_event_lines(stdout)
    records = [read_json_bytes(line) for line in lines]
    counts = Counter(record["event"] for record in records)
    require(dict(counts) == expected_counts,
            f"Inherited attempt04 event counts changed: {dict(counts)}")
    required_fields = {
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
    for record in records:
        require(set(record) == required_fields[record["event"]],
                f"Inherited event schema changed: {record['event']}")
    return lines


def require_legacy_events_unchanged(actual_stdout: bytes, reference_stdout: bytes,
                                    expected_counts: dict,
                                    expected_digest: str) -> list[bytes]:
    reference_lines = check_legacy_event_coverage(reference_stdout, expected_counts)
    actual_lines = check_legacy_event_coverage(actual_stdout, expected_counts)
    require(actual_lines == reference_lines,
            "Inherited attempt04 count/convergence event lines changed")
    require(sha_bytes(b"\n".join(actual_lines) + b"\n") == expected_digest,
            "Inherited attempt04 event-line digest differs from prepared baseline")
    return actual_lines


def normalize_frd(data: bytes) -> tuple[bytes, int]:
    normalized, count = UTIME_RE.subn(rb"\1<UTIME>\2", data)
    require(count == 1, f"FRD must contain exactly one 1UTIME record; found {count}")
    return normalized, count


def verify_freeze(expected: dict) -> dict:
    require(FREEZE.is_file(), "Parent-created input freeze is required")
    frozen = read_json(FREEZE)
    require(frozen.get("schema") == FREEZE_SCHEMA,
            "Unexpected input-freeze schema")
    require(frozen.get("expected_sha256") == sha(HERE / "expected.json") and
            frozen.get("input_sha256") == expected["input"]["sha256"] and
            frozen.get("image_id") == expected["source_binding"]["image_id"] and
            frozen.get("binary_sha256") == expected["source_binding"]["binary_sha256"],
            "Freeze does not bind expected input and build identities")
    require(frozen.get("native_execution") is False and
            frozen.get("joint_acceptance") is False,
            "Freeze scope overclaims this diagnostic")
    for relative, digest in frozen.get("files_sha256", {}).items():
        path = HERE / relative
        require(path.is_file() and sha(path) == digest,
                f"Frozen input changed or missing: {relative}")
    runner = load_runner()
    require(frozen.get("files_sha256") == runner.frozen_inventory(),
            "Freeze inventory does not cover the exact required packet files")
    return frozen


def trace_coverage(parsed: dict[str, list[dict]], trial_contract: dict) -> dict:
    map_rows = parsed["CCXPT_MAP"]
    unmapped_rows = parsed["CCXPT_UNMAPPED"]
    trial_rows = parsed["CCXPT_TRIAL"]
    by_tag = {tag: len(rows) for tag, rows in parsed.items()}
    identities = defaultdict(set)
    for row in map_rows:
        identities["map_generation_states"].add(
            (row["step"], row["increment"], row["attempt"],
             row["native_iteration"], row["generation_loop"]))
    for row in unmapped_rows:
        identities["unmapped_generation_states"].add(
            (row["step"], row["increment"], row["attempt"],
             row["native_iteration"], row["generation_loop"]))
    for row in trial_rows:
        identities["trial_states"].add(
            (row["step"], row["increment"], row["attempt"], row["iteration"]))
    return {
        "row_counts": by_tag,
        "map_generated_count_native_isol_nonzero": sum(r["generated"] for r in map_rows),
        "map_native_isol_zero_count": sum(not r["generated"] for r in map_rows),
        "trial_energy_available_count": sum(r["spring_energy_available"] for r in trial_rows),
        "trial_energy_unavailable_count": sum(not r["spring_energy_available"] for r in trial_rows),
        "distinct_observed_identities": {key: len(value) for key, value in identities.items()},
        "trial_rows_match_cvg": trial_contract,
        "state_join_performed": False,
        "force_qualification": False,
    }


def verify_run() -> dict:
    expected = read_json(HERE / "expected.json")
    summary = verify_packet(expected)
    frozen = verify_freeze(expected)
    execution_path = OUTPUT / "execution.json"
    require(execution_path.is_file(), "No native execution record exists")
    execution = read_json(execution_path)
    require(execution.get("schema") == EXECUTION_SCHEMA and
            execution.get("status") == "PASS_NATIVE_CAPTURE",
            "Native runner did not record a complete successful capture")
    require(execution.get("freeze_sha256") == sha(FREEZE) and
            execution.get("expected_sha256") == sha(HERE / "expected.json") and
            execution.get("input_sha256") == expected["input"]["sha256"],
            "Native execution source identities differ from freeze")
    pins = expected["source_binding"]
    binding = execution.get("source_binding", {})
    binding_to_pin = {
        "build_attempt": "build_attempt",
        "build_execution_sha256": "build_execution_sha256",
        "build_manifest_sha256": "build_manifest_sha256",
        "image_id": "image_id",
        "binary_path": "binary_path",
        "binary_sha256": "binary_sha256",
        "patch_sha256": "diagnostic_patch_sha256",
        "source_archive_sha256": "source_archive_sha256",
        "trace_format_sha256": "trace_format_sha256",
    }
    for run_key, pin_key in binding_to_pin.items():
        require(binding.get(run_key) == pins.get(pin_key),
                f"Native run provenance mismatch: {run_key}")
    limits = expected["run_limits"]
    require(execution.get("limits") == limits and
            execution.get("stop_reason") is None and
            execution.get("elapsed_seconds", float("inf")) <= limits["wall_seconds"] and
            execution.get("native_output_bytes", OUTPUT_LIMIT + 1) <= OUTPUT_LIMIT,
            "Native run violated frozen time/output limits")
    command = execution.get("command")
    require(isinstance(command, list) and len(command) >= 4 and
            command[0:2] == ["docker", "run"] and
            command[-4:] == [pins["image_id"], pins["binary_path"], "-i", "coupon"],
            "Native command does not invoke the frozen image/binary on the coupon")
    def option_value(option: str) -> str | None:
        try:
            index = command.index(option)
            return command[index + 1]
        except (ValueError, IndexError):
            return None
    require(option_value("--network") == "none" and option_value("--cpus") == "1" and
            option_value("--memory") == "1g" and option_value("--memory-swap") == "1g" and
            option_value("--name") == execution.get("container_name") and
            option_value("--workdir") == "/work",
            "Native command limits, container, or working directory differ")
    require("OMP_NUM_THREADS=1" in command and
            "CCX_NPROC_EQUATION_SOLVER=1" in command,
            "Native command does not pin solver threading to one CPU")
    mount = option_value("--mount")
    require(mount == f"type=bind,src={OUTPUT},dst=/work",
            "Native command mount does not isolate the output directory")
    state = execution.get("container_state") or {}
    require(execution.get("docker_cli_exit_code") == 0 and
            state.get("ExitCode") == 0 and state.get("Running") is False and
            state.get("OOMKilled") is False and
            execution.get("container_image") == pins["image_id"],
            "Native container did not exit normally without OOM on the pinned image")
    stdout_path = OUTPUT / "solver.stdout"
    stderr_path = OUTPUT / "solver.stderr"
    require(stdout_path.is_file() and stderr_path.is_file(),
            "Native stdout/stderr captures are required")
    stdout = stdout_path.read_bytes()
    stderr = stderr_path.read_bytes()
    require(stderr == (HERE / "reference/solver.stderr").read_bytes(),
            "Native stderr differs from the frozen baseline")
    require(b" Job finished" in stdout or b"\n Job finished" in stdout,
            "Native stdout lacks the normal CalculiX completion marker")
    actual_hashes = {
        path.name: sha(path)
        for path in sorted(OUTPUT.iterdir())
        if path.is_file() and path.name not in {"execution.json", "execution.json.tmp"}
    }
    require(execution.get("outputs_sha256") == actual_hashes,
            "Native outputs differ from their execution-record hashes")
    require(actual_hashes.get("coupon.inp") == expected["input"]["sha256"],
            "Working deck is not the exact frozen coupon input")
    all_size = sum(path.stat().st_size for path in OUTPUT.iterdir()
                   if path.is_file() and path.name not in {
                       "coupon.inp", "execution.json", "execution.json.tmp"})
    require(all_size == execution.get("native_output_bytes") and all_size <= OUTPUT_LIMIT,
            "Native output byte count differs or exceeds the cap")

    baseline = expected["baseline"]
    compared = {}
    for name in EXACT_OUTPUTS:
        actual = OUTPUT / name
        reference = HERE / "reference" / name
        require(actual.is_file(), f"Required native output missing: {name}")
        require(reference.is_file() and
                sha(reference) == baseline["reference_artifacts"][name]["sha256"],
                f"Frozen reference output missing or changed: {name}")
        same = actual.read_bytes() == reference.read_bytes()
        require(same, f"Output is not byte-identical to frozen baseline: {name}")
        compared[name] = {"byte_identical": True, "sha256": sha(actual)}
    for name in FRD_OUTPUTS:
        actual = OUTPUT / name
        reference = HERE / "reference" / name
        require(actual.is_file(), f"Required native FRD missing: {name}")
        ref_bytes = reference.read_bytes()
        act_bytes = actual.read_bytes()
        ref_norm, _ = normalize_frd(ref_bytes)
        act_norm, _ = normalize_frd(act_bytes)
        require(sha(reference) == baseline["reference_artifacts"][name]["sha256"] and
                act_norm == ref_norm,
                f"FRD differs beyond its single normalized 1UTIME field: {name}")
        compared[name] = {
            "equal_after_single_1utime_normalization": True,
            "actual_raw_sha256": sha(actual),
            "reference_raw_sha256": sha(reference),
            "actual_normalized_sha256": sha_bytes(act_norm),
            "reference_normalized_sha256": sha_bytes(ref_norm),
        }

    ref_stdout = (HERE / "reference/solver.stdout").read_bytes()
    new_lines = require_legacy_events_unchanged(
        stdout, ref_stdout, baseline["legacy_event_counts"],
        baseline["legacy_event_lines_sha256"])
    parsed = parse_trace(stdout, expected["trace_contract"])
    cvg_counts = parse_cvg((OUTPUT / "coupon.cvg").read_bytes())
    trial_contract = validate_trial_coverage(parsed, cvg_counts)
    coverage = trace_coverage(parsed, trial_contract)

    return {
        "schema": VERIFIER_SCHEMA,
        "status": "PASS_STATIC_REGRESSION_TRACE_CAPTURE",
        "expected_sha256": sha(HERE / "expected.json"),
        "freeze_sha256": sha(FREEZE),
        "execution_sha256": sha(execution_path),
        "preparation_summary": summary,
        "source_provenance": execution["source_binding"],
        "baseline": {
            "execution_sha256": baseline["execution_sha256"],
            "verifier_sha256": baseline["verifier_sha256"],
            "output_comparisons": compared,
            "inherited_attempt04_event_counts": baseline["legacy_event_counts"],
            "inherited_attempt04_event_lines_equal": True,
        },
        "trace_coverage": coverage,
        "trace_interpretation_limits": [
            "No same-state identity join between pre-Newton generation records and corrected-state trial records.",
            "native_isol is kept as an integer; generated means nonzero and values greater than one are valid.",
            "Trial energy is unavailable unless energy_enabled equals one; an emitted zero placeholder is not a measured zero.",
            "This is output instrumentation regression only; it does not qualify contact force, physical contact, or current-joint behavior.",
        ],
        "native_run": {
            "normal_exit": True,
            "oom": False,
            "elapsed_seconds": execution["elapsed_seconds"],
            "native_output_bytes": execution["native_output_bytes"],
            "output_cap_bytes": OUTPUT_LIMIT,
        },
        "mechanical_acceptance": False,
        "force_qualification": False,
        "joint_acceptance": False,
        "release": False,
    }


def expect_rejection(callable_, label: str) -> None:
    try:
        callable_()
    except (ValueError, RuntimeError, UnicodeDecodeError):
        return
    raise AssertionError(f"Fail-closed test did not reject {label}")


def synthetic_trace(contract: dict) -> bytes:
    tags = validate_trace_schema(contract)
    rows = []
    for tag, (ints, reals) in {
        "CCXPT_MAP": ([1, 1, 1, 2, 1, 1, 1, 5, 11, 21, 2, 4, 1],
                      [0.1] * 12),
        "CCXPT_UNMAPPED": ([1, 1, 1, 2, 1, 2, 3, 6, 12, 0], []),
        "CCXPT_TRIAL": ([1, 1, 1, 2, 55, 5, 11, 21, 31, 1, 0],
                        [0.2, 0.0, 0.0, -1.0, 0.0, 0.0, 0.1,
                         0.0, 0.0, 0.0, 1.0, 0.95, 0.2]),
    }.items():
        require(len(ints) == len(tags[tag]["integer_fields"]) and
                len(reals) == len(tags[tag]["real_fields"]),
                f"Bad internal self-test row {tag}")
        rows.append(tag + " " + " ".join(map(str, ints + reals)))
    return ("\n".join(rows) + "\n").encode("ascii")


def run_self_tests() -> dict:
    expected = read_json(HERE / "expected.json")
    prep = load_prepare()
    artifacts, _ = prep.build_all()
    prep.check_artifacts(artifacts)
    contract = expected["trace_contract"]
    sample = synthetic_trace(contract)
    parsed = parse_trace(sample, contract)
    require(parsed["CCXPT_MAP"][0]["native_isol"] == 2 and
            parsed["CCXPT_MAP"][0]["generated"] is True,
            "Native isol>1 self-test was not preserved as generated")
    trial = parsed["CCXPT_TRIAL"][0]
    require(trial["energy_enabled"] == 0 and
            trial["spring_energy_available"] is False and
            trial["spring_energy_observed"] is None,
            "Disabled-energy zero placeholder was misclassified as a measured zero")
    tags = validate_trace_schema(contract)
    valid_lines = sample.decode("ascii").splitlines()
    map_tokens = valid_lines[0].split()
    expect_rejection(lambda: parse_trace(
        (" ".join(map_tokens[:-1]) + "\n" + "\n".join(valid_lines[1:]) + "\n").encode(),
        contract), "missing trace field")
    nan_tokens = valid_lines[0].split()
    nan_tokens[-1] = "nan"
    expect_rejection(lambda: parse_trace(
        (" ".join(nan_tokens) + "\n" + "\n".join(valid_lines[1:]) + "\n").encode(),
        contract), "nonfinite trace float")
    fractional_integer = valid_lines[0].split()
    fractional_integer[1] = "1.5"
    expect_rejection(lambda: parse_trace(
        (" ".join(fractional_integer) + "\n" + "\n".join(valid_lines[1:]) + "\n").encode(),
        contract), "noninteger trace field")
    unknown = b"CCXPT_OTHER 1\n" + sample
    expect_rejection(lambda: parse_trace(unknown, contract), "unknown trace tag")
    embedded = b"prefix CCXPT_MAP 1\n" + sample
    expect_rejection(lambda: parse_trace(embedded, contract), "malformed trace tag line")
    expect_rejection(lambda: parse_trace(b"ordinary stdout only\n", contract),
                     "missing required map/trial coverage")

    old_stdout = (HERE / "reference/solver.stdout").read_bytes()
    old_events = check_legacy_event_coverage(
        old_stdout, expected["baseline"]["legacy_event_counts"])
    require(sha_bytes(b"\n".join(old_events) + b"\n") ==
            expected["baseline"]["legacy_event_lines_sha256"],
            "Frozen old inherited event digest differs")
    altered = list(old_events)
    altered[0] = altered[0] + b" "
    altered_stdout = b"\n".join(altered) + b"\n"
    expect_rejection(lambda: require_legacy_events_unchanged(
        altered_stdout, old_stdout, expected["baseline"]["legacy_event_counts"],
        expected["baseline"]["legacy_event_lines_sha256"]),
        "changed inherited count/gate event line")

    frd_sample = b"1PSTEP\n 1UTIME 12:34:56 GENERATED\n1PE0\n"
    normalized, count = normalize_frd(frd_sample)
    require(count == 1 and normalized == b"1PSTEP\n 1UTIME <UTIME> GENERATED\n1PE0\n",
            "FRD normalizer changed bytes outside 1UTIME")
    expect_rejection(lambda: normalize_frd(frd_sample + b" 1UTIME 12:34:56\n"),
                     "multiple FRD UTIME rows")
    return {
        "status": "PASS_SYNTHETIC_PARSER_AND_NEGATIVE_CONTROLS",
        "native_run": False,
        "trace_schema_tags": {tag: {"integer_fields": len(spec["integer_fields"]),
                                     "real_fields": len(spec["real_fields"])}
                              for tag, spec in tags.items()},
        "negative_controls_rejected": [
            "missing field", "nonfinite float", "noninteger field", "unknown tag",
            "malformed tag line", "missing required coverage", "multiple 1UTIME rows",
        ],
        "native_isol_2_preserved": True,
        "disabled_energy_zero_marked_unavailable": True,
        "legacy_line_change_detected": True,
        "frd_normalization_changes_only_utime": True,
    }


def run_integration_self_test() -> dict:
    """Exercise the full verifier against a disposable synthetic capture."""
    global OUTPUT, FREEZE
    require(not OUTPUT.exists() and not FREEZE.exists() and
            not (HERE / "execution.json").exists(),
            "Integration self-test refuses an existing output/freeze")
    expected = read_json(HERE / "expected.json")
    verify_packet(expected)
    runner = load_runner()
    original_output, original_freeze = OUTPUT, FREEZE
    with tempfile.TemporaryDirectory(prefix="ccxpt-static-integration-") as temp_root:
        temp_root = Path(temp_root)
        OUTPUT = temp_root / "output"
        FREEZE = temp_root / "input-freeze.json"
        try:
            OUTPUT.mkdir(parents=True, exist_ok=False)
            for name in (*EXACT_OUTPUTS, *FRD_OUTPUTS):
                shutil.copyfile(HERE / "reference" / name, OUTPUT / name)
            shutil.copyfile(HERE / "input/coupon.inp", OUTPUT / "coupon.inp")
            cvg_counts = parse_cvg((OUTPUT / "coupon.cvg").read_bytes())
            trace_lines = [
                "CCXPT_MAP 1 1 1 2 1 1 1 7 11 21 2 4 1 " + " ".join(["0.1"] * 12),
                "CCXPT_UNMAPPED 1 1 1 2 1 2 3 8 12 0",
            ]
            unique = 1
            for (step, increment, attempt, iteration), count in sorted(cvg_counts.items()):
                for _index in range(count):
                    ints = [step, increment, attempt, iteration,
                            100000 + unique, 200000 + unique, 1, 11, 21, 1, 0]
                    trace_lines.append("CCXPT_TRIAL " + " ".join(map(str, ints)) +
                                       " " + " ".join(["0.0"] * 13))
                    unique += 1
            stdout = (HERE / "reference/solver.stdout").read_bytes()
            stdout += ("\n" + "\n".join(trace_lines) + "\n").encode("ascii")
            (OUTPUT / "solver.stdout").write_bytes(stdout)
            shutil.copyfile(HERE / "reference/solver.stderr", OUTPUT / "solver.stderr")
            native_bytes = sum(path.stat().st_size for path in OUTPUT.iterdir()
                               if path.is_file() and path.name != "coupon.inp")
            require(native_bytes <= OUTPUT_LIMIT,
                    "Synthetic integration capture exceeds output cap")

            inventory = runner.frozen_inventory()
            pins = read_json(HERE / "build-pins.json")
            freeze_record = {
                "schema": FREEZE_SCHEMA,
                "created_utc": "synthetic-self-test",
                "files_sha256": inventory,
                "expected_sha256": sha(HERE / "expected.json"),
                "input_sha256": expected["input"]["sha256"],
                "image_id": pins["image_id"],
                "binary_sha256": pins["binary_sha256"],
                "native_execution": False,
                "joint_acceptance": False,
            }
            FREEZE.write_text(json.dumps(freeze_record, indent=2, sort_keys=True) + "\n")
            source = expected["source_binding"]
            source_binding = {
                "build_attempt": source["build_attempt"],
                "build_execution_sha256": source["build_execution_sha256"],
                "build_manifest_sha256": source["build_manifest_sha256"],
                "image_id": source["image_id"],
                "binary_path": source["binary_path"],
                "binary_sha256": source["binary_sha256"],
                "patch_sha256": source["diagnostic_patch_sha256"],
                "source_archive_sha256": source["source_archive_sha256"],
                "trace_format_sha256": source["trace_format_sha256"],
            }
            synthetic_name = "synthetic-static-coupon"
            synthetic_command = [
                "docker", "run", "--pull=never", "--name", synthetic_name,
                "--network", "none", "--cpus", "1", "--memory", "1g",
                "--memory-swap", "1g", "--user", "1000:1000",
                "--env", "OMP_NUM_THREADS=1", "--env", "CCX_NPROC_EQUATION_SOLVER=1",
                "--mount", f"type=bind,src={OUTPUT},dst=/work", "--workdir", "/work",
                source["image_id"], source["binary_path"], "-i", "coupon",
            ]
            output_hashes = {
                path.name: sha(path) for path in sorted(OUTPUT.iterdir())
                if path.is_file() and path.name != "execution.json"
            }
            run_record = {
                "schema": EXECUTION_SCHEMA,
                "status": "PASS_NATIVE_CAPTURE",
                "freeze_sha256": sha(FREEZE),
                "expected_sha256": sha(HERE / "expected.json"),
                "input_sha256": expected["input"]["sha256"],
                "source_binding": source_binding,
                "container_name": synthetic_name,
                "command": synthetic_command,
                "limits": expected["run_limits"],
                "stop_reason": None,
                "elapsed_seconds": 0.25,
                "native_output_bytes": native_bytes,
                "docker_cli_exit_code": 0,
                "container_state": {"ExitCode": 0, "Running": False, "OOMKilled": False},
                "container_image": source["image_id"],
                "outputs_sha256": output_hashes,
                "joint_acceptance": False,
            }
            (OUTPUT / "execution.json").write_text(
                json.dumps(run_record, indent=2, sort_keys=True) + "\n")
            report = verify_run()
            require(report["status"] == "PASS_STATIC_REGRESSION_TRACE_CAPTURE" and
                    report["trace_coverage"]["row_counts"]["CCXPT_TRIAL"] ==
                    sum(cvg_counts.values()),
                    "Synthetic end-to-end verifier pass did not cover all .cvg contacts")
            return {
                "status": "PASS_SYNTHETIC_END_TO_END_VERIFIER",
                "native_run": False,
                "synthetic_trial_rows": sum(cvg_counts.values()),
                "cvg_state_count": len(cvg_counts),
                "frd_baseline_copy_and_normalization": True,
                "legacy_event_exact_line_match": True,
                "source_provenance_binding": True,
            }
        finally:
            OUTPUT, FREEZE = original_output, original_freeze


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true",
                      help="Run synthetic parser/negative controls; no native solve")
    mode.add_argument("--verify", action="store_true",
                      help="Verify a parent-frozen completed capture")
    mode.add_argument("--integration-self-test", action="store_true",
                      help="Verify a disposable synthetic capture; no native solve")
    parser.add_argument("--write", action="store_true",
                        help="Write verifier.json exclusively after a passing audit")
    args = parser.parse_args()
    if args.self_test:
        require(not args.write, "--write is valid only with --verify")
        report = run_self_tests()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if args.integration_self_test:
        require(not args.write, "--write is valid only with --verify")
        report = run_integration_self_test()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    report = verify_run()
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.write:
        target = HERE / "verifier.json"
        with target.open("xb") as stream:
            stream.write(payload.encode())
    print(payload, end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        raise SystemExit(2)
