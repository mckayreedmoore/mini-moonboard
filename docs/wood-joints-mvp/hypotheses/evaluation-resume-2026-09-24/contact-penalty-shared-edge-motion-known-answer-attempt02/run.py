#!/usr/bin/env python3
"""Parent-gated freeze and serial capture for the shared-edge full-six motion fixture.

This module is preparation only until a reviewed parent-review.json approves
the exact expected.json hash and native execution. It has not been run here.
"""

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
import time


HERE = Path(__file__).resolve().parent
EVAL = HERE.parent
PREPARE = HERE / "prepare.py"
IMAGE = "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
BINARY = "/usr/local/bin/ccx-upstream-2.23"
BINARY_SHA = "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863"
TIMEOUT = 60
OUTPUT_LIMIT = 100 * 1024 * 1024
LOG_LIMIT = 5 * 1024 * 1024
CASES = ["shared_slave_motion", "cross_role_motion"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    def unique_pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key {key} in {path}")
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique_pairs)


def save(path: Path, record: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("x") as stream:
        stream.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_prepare_module():
    spec = importlib.util.spec_from_file_location("shared_edge_motion_packet_prepare", PREPARE)
    require(spec is not None and spec.loader is not None, "Cannot load prepare.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_parent_review(expected: dict) -> dict:
    review_path = HERE / "parent-review.json"
    require(review_path.is_file(), "Parent review record is required before freeze/run")
    review = read_json(review_path)
    require(review.get("ready_for_bounded_fixture") is True,
            "Parent has not recorded fixture readiness")
    require(review.get("motion_pair_energy_contract_reviewed") is True,
            "Parent has not reviewed the motion, pair-output and energy contract")
    require(review.get("reviewed_expected_sha256") == sha(HERE / "expected.json"),
            "Parent review does not bind the current expected.json")
    return review


def verify_packet_inputs(require_review: bool) -> tuple[dict, dict | None]:
    expected = read_json(HERE / "expected.json")
    require(expected.get("schema") == "calculix_penalty_shared_edge_motion_known_answer/v1",
            "Unexpected shared-edge motion packet schema")
    prep = load_prepare_module()
    files, _preflight = prep.build_all()
    for relative, data in files.items():
        require((HERE / relative).read_bytes() == data,
                f"Prepared artifact differs from in-memory reproduction: {relative}")
    require(expected["case_order"] == CASES, "Case order differs")
    review = verify_parent_review(expected) if require_review else None
    return expected, review


def freeze() -> None:
    freeze_path = HERE / "input-freeze.json"
    require(not freeze_path.exists(), "Refusing to replace an existing freeze")
    require(not (HERE / "execution.json").exists() and not (HERE / "output").exists(),
            "Refusing to freeze after an execution has started")
    expected, review = verify_packet_inputs(require_review=True)
    assert review is not None
    inputs = sorted((HERE / "input").glob("*.inp"))
    require([path.stem for path in inputs] == sorted(CASES),
            "Exactly two shared-edge motion inputs are required")
    required = ["README.md", "prepare.py", "readiness.json", "expected.json",
                "source-snapshot.json", "preflight.json", "prefreeze-amendment.md",
                "parent-review.json", "parent-map-audit.py", "verifier.py", "run.py",
                "lexical-audit.json",
                "../contact-penalty-touch-work-known-answer-attempt01/pair_output.py"]
    files = required + [str(path.relative_to(HERE)) for path in inputs]
    files_sha = {item: sha(HERE / item) for item in files}
    require(review.get("reviewed_packet_sha256") in (None, sha(HERE / "readiness.json")),
            "Parent review binds a different preparation record")
    record = {
        "schema": "contact_penalty_shared_edge_motion_freeze/v1",
        "created_at": now(),
        "files_sha256": files_sha,
        "cases": CASES,
        "image_id": IMAGE,
        "binary_path": BINARY,
        "binary_sha256": BINARY_SHA,
        "limits": {"seconds_per_case": TIMEOUT,
                   "output_bytes_per_case": OUTPUT_LIMIT,
                   "stdout_or_stderr_bytes": LOG_LIMIT,
                   "cpus": 1, "memory": "1g", "memory_plus_swap": "1g"},
        "scope": "Three-body C3D10 shared-edge full-six motion fixture only; no current-joint acceptance",
        "parent_reviewed_expected_sha256": sha(HERE / "expected.json"),
        "mechanical_acceptance": False,
        "work_energy_acceptance": False,
        "joint_acceptance": False,
        "release": False,
    }
    save(freeze_path, record)
    print(json.dumps({"frozen": CASES, "sha256": sha(freeze_path)}))


def capture(command: list[str]) -> str:
    return subprocess.check_output(command, text=True, timeout=20).strip()


def stop_container(name: str) -> dict:
    try:
        subprocess.run(["docker", "stop", "--time", "2", name],
                       capture_output=True, timeout=10, check=False)
    except subprocess.TimeoutExpired:
        pass
    state = json.loads(capture(["docker", "inspect", name]))[0]["State"]
    if state["Running"]:
        subprocess.run(["docker", "kill", name], capture_output=True,
                       timeout=10, check=True)
        state = json.loads(capture(["docker", "inspect", name]))[0]["State"]
    require(not state["Running"], f"Container still running: {name}")
    return state


def output_sizes(output: Path) -> tuple[int, int]:
    paths = [path for path in output.iterdir() if path.is_file()]
    total = sum(path.stat().st_size for path in paths)
    logs = max((output / "coupon.stdout").stat().st_size,
               (output / "coupon.stderr").stat().st_size)
    return total, logs


def verify_hashes(files: dict[str, str]) -> None:
    for relative, digest in files.items():
        require(sha(HERE / relative) == digest, f"Frozen file differs: {relative}")


def run_case(case: str) -> dict:
    output = HERE / "output" / case
    output.mkdir(parents=True, exist_ok=False)
    require(case in CASES, "Unknown shared-edge motion case")
    shutil.copyfile(HERE / "input" / f"{case}.inp", output / "coupon.inp")
    name = f"wj-shared-edge-motion-{case}-{time.time_ns()}"
    command = [
        "docker", "run", "--pull=never", "--name", name, "--network", "none",
        "--cpus", "1", "--memory", "1g", "--memory-swap", "1g",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "--env", "OMP_NUM_THREADS=1", "--env", "CCX_NPROC_EQUATION_SOLVER=1",
        "--mount", f"type=bind,src={output},dst=/work", "--workdir", "/work",
        IMAGE, BINARY, "-i", "coupon",
    ]
    record = {"case": case, "container": name, "command": command,
              "started_at": now(), "stop_reason": None, "status": "running"}
    save(output / "execution.json", record)
    started = time.monotonic()
    process = None
    try:
        with (output / "coupon.stdout").open("xb") as stdout, \
                (output / "coupon.stderr").open("xb") as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            while process.poll() is None:
                total, log_size = output_sizes(output)
                if time.monotonic() - started > TIMEOUT:
                    record["stop_reason"] = "wall_time_limit"
                elif total > OUTPUT_LIMIT or log_size > LOG_LIMIT:
                    record["stop_reason"] = "output_size_limit"
                if record["stop_reason"]:
                    record["stopped_container_state"] = stop_container(name)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    break
                time.sleep(0.1)
            record["docker_cli_exit_code"] = process.wait(timeout=10)
        total, log_size = output_sizes(output)
        record["total_output_bytes"] = total
        record["max_log_bytes"] = log_size
        if total > OUTPUT_LIMIT or log_size > LOG_LIMIT:
            record["stop_reason"] = "output_size_limit"
        inspected = json.loads(capture(["docker", "inspect", name]))[0]
        state = inspected["State"]
        record["container_state"] = state
        record["container_image"] = inspected["Image"]
        record["status"] = "completed" if (
            record["docker_cli_exit_code"] == 0 and state["ExitCode"] == 0
            and not state["OOMKilled"] and not state["Running"]
            and not record["stop_reason"] and inspected["Image"] == IMAGE
        ) else "failed_or_stopped"
    except BaseException as exc:
        record["status"] = "capture_exception"
        record["exception"] = repr(exc)
        try:
            record["stopped_container_state"] = stop_container(name)
        except Exception as stop_error:
            record["stop_exception"] = repr(stop_error)
        if process is not None and process.poll() is None:
            process.kill()
    finally:
        record["ended_at"] = now()
        record["elapsed_seconds"] = time.monotonic() - started
        record["outputs_sha256"] = {
            path.name: sha(path) for path in sorted(output.iterdir())
            if path.is_file() and path.name not in {"execution.json", "execution.json.tmp"}
        }
        save(output / "execution.json", record)
    return record


def run(freeze_sha: str) -> None:
    execution_path = HERE / "execution.json"
    require(not execution_path.exists() and not (HERE / "output").exists(),
            "Refusing rerun or overlapping output")
    expected, _ = verify_packet_inputs(require_review=True)
    freeze_path = HERE / "input-freeze.json"
    require(freeze_path.is_file() and sha(freeze_path) == freeze_sha,
            "Freeze missing or differs from parent-reviewed hash")
    frozen = read_json(freeze_path)
    require(frozen.get("schema") == "contact_penalty_shared_edge_motion_freeze/v1",
            "Unexpected shared-edge-motion freeze schema")
    verify_hashes(frozen["files_sha256"])
    require(frozen.get("cases") == CASES and frozen.get("image_id") == IMAGE
            and frozen.get("binary_sha256") == BINARY_SHA,
            "Frozen case/toolchain pins differ")
    require(frozen.get("parent_reviewed_expected_sha256") == sha(HERE / "expected.json"),
            "Expected contract changed after parent review")
    require(capture(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"])
            == IMAGE, "Docker image pin differs")
    binary = capture(["docker", "run", "--pull=never", "--rm", "--network", "none",
                      IMAGE, "sha256sum", BINARY]).split()[0]
    require(binary == BINARY_SHA, "CalculiX executable pin differs")
    record = {
        "schema": "contact_penalty_shared_edge_motion_execution/v1",
        "started_at": now(), "status": "running", "runs": [],
        "input_freeze_sha256": sha(freeze_path), "binary_sha256": binary,
        "image_id": IMAGE, "mechanical_acceptance": False,
        "work_energy_acceptance": False, "joint_acceptance": False, "release": False,
    }
    save(execution_path, record)
    try:
        for case in CASES:
            verify_hashes(frozen["files_sha256"])
            record["runs"].append(run_case(case))
            save(execution_path, record)
            if record["runs"][-1]["status"] != "completed":
                break
        verify_hashes(frozen["files_sha256"])
        require(sha(freeze_path) == freeze_sha, "Freeze changed during execution")
        record["frozen_inputs_unchanged"] = True
        record["status"] = "completed_pending_audit" if (
            [item["case"] for item in record["runs"]] == CASES
            and all(item["status"] == "completed" for item in record["runs"])
        ) else "failed_or_stopped"
    except BaseException as exc:
        record["status"] = "capture_exception"
        record["exception"] = repr(exc)
    finally:
        record["ended_at"] = now()
        save(execution_path, record)
    print(json.dumps({"status": record["status"], "execution_sha256": sha(execution_path)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["freeze", "run"])
    parser.add_argument("--freeze-sha", help="Parent-reviewed immutable freeze SHA-256")
    args = parser.parse_args()
    if args.action == "freeze":
        freeze()
    else:
        require(args.freeze_sha, "run requires --freeze-sha from parent review")
        run(args.freeze_sha)
