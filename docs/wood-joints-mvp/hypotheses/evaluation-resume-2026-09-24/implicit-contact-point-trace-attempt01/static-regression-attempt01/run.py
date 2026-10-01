#!/usr/bin/env python3
"""Parent-operated freeze and one-case execution for the static coupon."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True


HERE = Path(__file__).resolve().parent
BUILD_PINS_PATH = HERE / "build-pins.json"
FREEZE = HERE / "input-freeze.json"
OUTPUT = HERE / "output"
OUTPUT_LIMIT = 16 * 1024 * 1024
TIMEOUT = 60
NATIVE_OUTPUTS = (
    "coupon.12d", "coupon.cel", "coupon.cvg", "coupon.dat", "coupon.sta",
    "spooles.out", "coupon.frd", "ResultsForLastIterations.frd",
)
STATIC_FREEZE_FILES = (
    "README.md", "prepare.py", "run.py", "verifier.py", "expected.json",
    "readiness.json", "build-pins.json", "diagnostic.patch",
    "trace-format.json", "input/coupon.inp",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    return json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError(f"Invalid JSON constant {value} in {path}")))


def save_new(path: Path, record: dict) -> None:
    payload = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(payload)


def save_replace(path: Path, record: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("xb") as stream:
        stream.write((json.dumps(record, indent=2, sort_keys=True) + "\n").encode())
    os.replace(temporary, path)


def load_prepare_module():
    spec = importlib.util.spec_from_file_location("ccxpt_static_prepare", HERE / "prepare.py")
    require(spec is not None and spec.loader is not None, "Cannot load prepare.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_packet() -> tuple[dict, dict]:
    prep = load_prepare_module()
    artifacts, summary = prep.build_all()
    prep.check_artifacts(artifacts)
    expected = read_json(HERE / "expected.json")
    pins = read_json(BUILD_PINS_PATH)
    require(expected.get("schema") == "ccx223_contact_point_trace_static_regression/v1",
            "Unexpected static regression expected.json schema")
    require(pins.get("schema") == "contact_point_trace_static_regression_build_pins/v1" and
            pins.get("image_id") and pins.get("binary_sha256"),
            "Build pin record is incomplete")
    return expected, summary


def frozen_inventory() -> dict[str, str]:
    paths = list(STATIC_FREEZE_FILES)
    paths.extend(f"reference/{name}" for name in
                 json.loads((HERE / "expected.json").read_text())[
                     "baseline"]["reference_artifacts"])
    unique = sorted(set(paths))
    result = {}
    for relative in unique:
        path = HERE / relative
        require(path.is_file(), f"Freeze input missing: {relative}")
        result[relative] = sha(path)
    return result


def freeze() -> dict:
    require(not FREEZE.exists(), "Refusing to replace an existing input freeze")
    require(not OUTPUT.exists() and not (HERE / "execution.json").exists(),
            "Refusing to freeze after native execution has started")
    expected, summary = verify_packet()
    inventory = frozen_inventory()
    pins = read_json(BUILD_PINS_PATH)
    record = {
        "schema": "ccx223_contact_point_trace_static_regression_freeze/v1",
        "created_utc": now(),
        "files_sha256": inventory,
        "expected_sha256": sha(HERE / "expected.json"),
        "input_sha256": expected["input"]["sha256"],
        "baseline_execution_sha256": expected["baseline"]["execution_sha256"],
        "image_id": pins["image_id"],
        "binary_path": pins["binary_path"],
        "binary_sha256": pins["binary_sha256"],
        "patch_sha256": pins["diagnostic_patch_sha256"],
        "limits": expected["run_limits"],
        "scope": "one static contact coupon; regression only; no current-joint eligibility",
        "native_execution": False,
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "preparation_summary": summary,
    }
    save_new(FREEZE, record)
    return {"frozen": True, "freeze_sha256": sha(FREEZE),
            "expected_sha256": record["expected_sha256"],
            "file_count": len(inventory)}


def verify_freeze(requested_sha: str) -> tuple[dict, dict]:
    require(FREEZE.is_file(), "Parent input freeze is required before native run")
    require(sha(FREEZE) == requested_sha,
            "Supplied freeze SHA-256 does not match input-freeze.json")
    record = read_json(FREEZE)
    require(record.get("schema") == "ccx223_contact_point_trace_static_regression_freeze/v1",
            "Unexpected static regression freeze schema")
    expected, _ = verify_packet()
    pins = read_json(BUILD_PINS_PATH)
    require(record.get("expected_sha256") == sha(HERE / "expected.json") and
            record.get("input_sha256") == expected["input"]["sha256"] and
            record.get("image_id") == pins["image_id"] and
            record.get("binary_sha256") == pins["binary_sha256"] and
            record.get("patch_sha256") == pins["diagnostic_patch_sha256"],
            "Freeze does not bind the current coupon/build identities")
    for relative, digest in record.get("files_sha256", {}).items():
        path = HERE / relative
        require(path.is_file() and sha(path) == digest,
                f"Frozen file changed or missing: {relative}")
    require(record.get("files_sha256") == frozen_inventory(),
            "Freeze inventory does not match the required packet file set")
    return record, expected


def docker_inspect_image(image_id: str) -> str:
    result = subprocess.run(["docker", "image", "inspect", image_id,
                             "--format", "{{.Id}}"], check=True,
                            text=True, capture_output=True, timeout=20)
    return result.stdout.strip()


def directory_output_bytes(directory: Path) -> int:
    total = 0
    for path in directory.iterdir():
        if path.is_file() and path.name not in {"coupon.inp", "execution.json", "execution.json.tmp"}:
            total += path.stat().st_size
    return total


def inspect_container(name: str) -> dict:
    result = subprocess.run(["docker", "inspect", name], check=True,
                            text=True, capture_output=True, timeout=20)
    return json.loads(result.stdout)[0]


def stop_container(name: str) -> dict | None:
    try:
        current = inspect_container(name)
    except Exception:
        return None
    if current["State"].get("Running"):
        subprocess.run(["docker", "kill", name], capture_output=True,
                       text=True, timeout=15, check=False)
    return inspect_container(name)["State"]


def output_hashes(directory: Path) -> dict[str, str]:
    return {
        path.name: sha(path)
        for path in sorted(directory.iterdir())
        if path.is_file() and path.name not in {"execution.json", "execution.json.tmp"}
    }


def run_native(freeze_sha: str) -> dict:
    freeze_record, expected = verify_freeze(freeze_sha)
    require(not OUTPUT.exists() and not (HERE / "execution.json").exists(),
            "Refusing rerun or overlapping static coupon output")
    pins = read_json(BUILD_PINS_PATH)
    image = pins["image_id"]
    require(docker_inspect_image(image) == image,
            "Pinned trace image is not present under its immutable ID")
    OUTPUT.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(HERE / expected["input"]["path"], OUTPUT / "coupon.inp")
    require(sha(OUTPUT / "coupon.inp") == expected["input"]["sha256"],
            "Working coupon input copy differs from freeze")
    name = f"ccxpt-static-regression-{time.time_ns()}"
    command = [
        "docker", "run", "--pull=never", "--name", name,
        "--network", "none", "--cpus", "1", "--memory", "1g",
        "--memory-swap", "1g", "--user", f"{os.getuid()}:{os.getgid()}",
        "--env", "OMP_NUM_THREADS=1", "--env", "CCX_NPROC_EQUATION_SOLVER=1",
        "--mount", f"type=bind,src={OUTPUT},dst=/work", "--workdir", "/work",
        image, pins["binary_path"], "-i", "coupon",
    ]
    record = {
        "schema": "ccx223_contact_point_trace_static_regression_execution/v1",
        "status": "running",
        "started_utc": now(),
        "freeze_sha256": sha(FREEZE),
        "expected_sha256": sha(HERE / "expected.json"),
        "input_sha256": expected["input"]["sha256"],
        "source_binding": {
            "build_attempt": pins["build_attempt"],
            "build_execution_sha256": pins["build_execution_sha256"],
            "build_manifest_sha256": pins["build_manifest_sha256"],
            "image_id": image,
            "binary_path": pins["binary_path"],
            "binary_sha256": pins["binary_sha256"],
            "patch_sha256": pins["diagnostic_patch_sha256"],
            "source_archive_sha256": pins["source_archive_sha256"],
            "trace_format_sha256": pins["trace_format_sha256"],
        },
        "container_name": name,
        "command": command,
        "limits": expected["run_limits"],
        "stop_reason": None,
        "container_state": None,
        "container_image": None,
        "native_output_bytes": 0,
        "outputs_sha256": {},
        "joint_acceptance": False,
    }
    record_path = OUTPUT / "execution.json"
    save_new(record_path, record)
    start = time.monotonic()
    process = None
    try:
        with (OUTPUT / "solver.stdout").open("xb") as stdout, \
                (OUTPUT / "solver.stderr").open("xb") as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            while process.poll() is None:
                elapsed = time.monotonic() - start
                native_bytes = directory_output_bytes(OUTPUT)
                if elapsed > TIMEOUT:
                    record["stop_reason"] = "wall_time_limit"
                elif native_bytes > OUTPUT_LIMIT:
                    record["stop_reason"] = "aggregate_output_limit"
                if record["stop_reason"]:
                    record["stopped_container_state"] = stop_container(name)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    break
                time.sleep(0.1)
            record["docker_cli_exit_code"] = process.wait(timeout=10)
        record["elapsed_seconds"] = time.monotonic() - start
        record["native_output_bytes"] = directory_output_bytes(OUTPUT)
        if record["native_output_bytes"] > OUTPUT_LIMIT:
            record["stop_reason"] = record["stop_reason"] or "aggregate_output_limit"
        container = inspect_container(name)
        record["container_state"] = container["State"]
        record["container_image"] = container["Image"]
        state = container["State"]
        record["status"] = "PASS_NATIVE_CAPTURE" if (
            record["docker_cli_exit_code"] == 0 and state.get("ExitCode") == 0 and
            state.get("Running") is False and state.get("OOMKilled") is False and
            record["stop_reason"] is None and container.get("Image") == image and
            record["elapsed_seconds"] <= TIMEOUT and
            record["native_output_bytes"] <= OUTPUT_LIMIT
        ) else "FAIL_NATIVE_CAPTURE"
    except BaseException as exc:
        record["status"] = "FAIL_CAPTURE_EXCEPTION"
        record["exception"] = repr(exc)
        record["stopped_container_state"] = stop_container(name)
        if process is not None and process.poll() is None:
            process.kill()
    finally:
        record["ended_utc"] = now()
        record["elapsed_seconds"] = time.monotonic() - start
        record["native_output_bytes"] = directory_output_bytes(OUTPUT)
        record["outputs_sha256"] = output_hashes(OUTPUT)
        save_replace(record_path, record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Read-only packet and baseline check")
    mode.add_argument("--freeze", action="store_true", help="Create the parent-owned freeze record")
    mode.add_argument("--run", action="store_true", help="Run only after a parent freeze exists")
    parser.add_argument("--freeze-sha", help="Required freeze hash for --run")
    args = parser.parse_args()
    if args.check:
        _expected, summary = verify_packet()
        print(json.dumps({"status": "PASS_READ_ONLY", **summary}, sort_keys=True))
        return 0
    if args.freeze:
        print(json.dumps(freeze(), sort_keys=True))
        return 0
    require(bool(args.freeze_sha), "--run requires --freeze-sha <sha256>")
    record = run_native(args.freeze_sha)
    print(json.dumps({"status": record["status"],
                      "execution_path": "output/execution.json",
                      "execution_sha256": sha(OUTPUT / "execution.json"),
                      "native_output_bytes": record["native_output_bytes"]}, sort_keys=True))
    return 0 if record["status"] == "PASS_NATIVE_CAPTURE" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        raise SystemExit(2)
