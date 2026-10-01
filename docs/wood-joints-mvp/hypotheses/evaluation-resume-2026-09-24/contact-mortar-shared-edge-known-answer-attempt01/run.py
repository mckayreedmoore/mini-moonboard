"""Freeze and serially capture the small, unpatched CalculiX 2.23 method fixture."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


HERE = Path(__file__).resolve().parent
IMAGE = "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
BINARY = "/usr/local/bin/ccx-upstream-2.23"
BINARY_SHA = "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863"
TIMEOUT = 60
OUTPUT_LIMIT = 100 * 1024 * 1024
LOG_LIMIT = 5 * 1024 * 1024
EXPECTED_CASES = {
    "shared_slave_mortar",
    "shared_slave_penalty",
    "cross_role_mortar",
    "cross_role_penalty",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, record):
    """Persist terminal evidence atomically without losing a prior partial record."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("x") as stream:
        stream.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def capture(command):
    return subprocess.check_output(command, text=True, timeout=20).strip()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def stop_container(name):
    """Stop the actual container, escalating independently of the Docker client."""
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


def output_sizes(output):
    paths = [p for p in output.iterdir() if p.is_file()]
    total = sum(p.stat().st_size for p in paths)
    logs = max((output / "coupon.stdout").stat().st_size,
               (output / "coupon.stderr").stat().st_size)
    return total, logs


def verify_hashes(files):
    for relative, digest in files.items():
        require(sha(HERE / relative) == digest, f"Frozen input differs: {relative}")


def freeze():
    path = HERE / "input-freeze.json"
    require(not path.exists(), "Refusing to replace a frozen packet")
    required = ["README.md", "prepare.py", "expected.json", "readiness.json", "parent-review.json",
                "verifier.py", "run.py"]
    review = json.loads((HERE / "parent-review.json").read_text())
    require(review.get("ready_for_bounded_fixture") is True,
            "Parent has not recorded fixture readiness")
    inputs = sorted(HERE.glob("input/*.inp"))
    expected = json.loads((HERE / "expected.json").read_text())
    case_order = expected.get("case_order")
    input_cases = [item.stem for item in inputs]
    require(len(input_cases) == len(EXPECTED_CASES)
            and set(input_cases) == EXPECTED_CASES,
            "Exactly the four shared-edge fixture decks required")
    require(isinstance(case_order, list) and len(case_order) == len(EXPECTED_CASES)
            and len(set(case_order)) == len(EXPECTED_CASES)
            and set(case_order) == EXPECTED_CASES,
            "expected.json case_order must contain each shared-edge case exactly once")
    require(set(expected.get("cases", {})) == EXPECTED_CASES,
            "expected.json case records differ from the required case set")
    files = required + [str(item.relative_to(HERE)) for item in inputs]
    record = {
        "schema": "mortar_shared_edge_freeze/v1",
        "created_at": now(),
        "files_sha256": {item: sha(HERE / item) for item in files},
        "cases": case_order,
        "image_id": IMAGE, "binary_path": BINARY, "binary_sha256": BINARY_SHA,
        "limits": {"seconds_per_case": TIMEOUT, "output_bytes_per_case": OUTPUT_LIMIT,
                   "stdout_or_stderr_bytes": LOG_LIMIT, "cpus": 1,
                   "memory": "1g", "memory_plus_swap": "1g"},
        "scope": "Small method fixture only; no joint or release acceptance",
    }
    save(path, record)
    print(json.dumps({"frozen": record["cases"], "sha256": sha(path)}))


def run_case(case):
    output = HERE / "output" / case
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(HERE / "input" / f"{case}.inp", output / "coupon.inp")
    name = "wj-mortar-fixture-" + case + "-" + str(time.time_ns())
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
        with (output / "coupon.stdout").open("wb") as out, \
                (output / "coupon.stderr").open("wb") as err:
            process = subprocess.Popen(command, stdout=out, stderr=err)
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
        record["container_state"] = inspected["State"]
        record["container_image"] = inspected["Image"]
        state = inspected["State"]
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
            p.name: sha(p) for p in sorted(output.iterdir())
            if p.is_file() and p.name not in {"execution.json", "execution.json.tmp"}
        }
        save(output / "execution.json", record)
    return record


def run(freeze_sha):
    path = HERE / "execution.json"
    require(not path.exists() and not (HERE / "output").exists(), "Refusing rerun")
    freeze_path = HERE / "input-freeze.json"
    require(sha(freeze_path) == freeze_sha, "Freeze differs from parent-reviewed hash")
    frozen = json.loads(freeze_path.read_text())
    verify_hashes(frozen["files_sha256"])
    expected = json.loads((HERE / "expected.json").read_text())
    case_order = expected.get("case_order")
    require(isinstance(case_order, list) and len(case_order) == len(EXPECTED_CASES)
            and len(set(case_order)) == len(EXPECTED_CASES)
            and set(case_order) == EXPECTED_CASES,
            "expected.json case_order must contain each shared-edge case exactly once")
    require(frozen.get("cases") == case_order,
            "Frozen run order differs from expected.json case_order")
    require(frozen["image_id"] == IMAGE and frozen["binary_sha256"] == BINARY_SHA,
            "Frozen toolchain differs")
    require(capture(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"] ) == IMAGE,
            "Image pin differs")
    binary = capture(["docker", "run", "--pull=never", "--rm", "--network", "none", IMAGE,
                      "sha256sum", BINARY]).split()[0]
    require(binary == BINARY_SHA, "Executable pin differs")
    record = {"schema": "mortar_shared_edge_execution/v1",
              "started_at": now(), "status": "running", "runs": [],
              "input_freeze_sha256": sha(freeze_path), "binary_sha256": binary,
              "image_id": IMAGE, "mechanical_acceptance": False,
              "joint_acceptance": False, "release": False}
    save(path, record)
    try:
        for case in frozen["cases"]:
            verify_hashes(frozen["files_sha256"])
            result = run_case(case)
            record["runs"].append(result)
            save(path, record)
            if result["status"] != "completed":
                break
        verify_hashes(frozen["files_sha256"])
        require(sha(freeze_path) == freeze_sha, "Freeze changed during execution")
        record["frozen_inputs_unchanged"] = True
        record["status"] = "completed_pending_audit" if (
            len(record["runs"]) == 4
            and all(r["status"] == "completed" for r in record["runs"])
        ) else "failed_or_stopped"
    except BaseException as exc:
        record["status"] = "capture_exception"
        record["exception"] = repr(exc)
    finally:
        record["ended_at"] = now()
        save(path, record)
    print(json.dumps({"status": record["status"], "execution_sha256": sha(path)}))


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
