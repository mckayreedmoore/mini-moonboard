"""Create a one-case freeze or run the shared-slave penalty coupon."""

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
CASE = "shared_slave_penalty"
CASES = (CASE,)
INPUT_SHA256 = "d7e517bca0a63fc02bbb77bae8116bc2b014b3545a5c40566e64cdaac47668e7"
SOURCE_ORACLE_SHA256 = "29ce26d69e94579fb49af86b8608e0b001310f670a294eb596997a3ce2b538b0"
PARENT_ORACLE_SHA256 = "16c1df001392376d084d8c2d021ce8a884bfb96ea56bbdf528275b476f974c45"
ORACLE_SHA256 = "8c0344c1c7f98976cd1636532eb73925c9c896917c5110729834c816e4c0c9da"
ROUTE_REVIEW_SHA256 = "64feedb7f3746d6ebba0dc15d8cc0472ba8d2958bd564c7c25708b6d30d2e840"
IMAGE = "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
BINARY = "/usr/local/bin/ccx-upstream-2.23"
BINARY_SHA256 = "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863"
AUTHORIZATION_TRANSITION = (
    "External parent authorization must name this exact freeze and the exact "
    "frozen readiness snapshots; candidate snapshots remain false."
)
AUTHORIZATION_FIELDS = frozenset({
    "schema", "status", "native_execution_authorized", "parent_readiness",
    "input_freeze_sha256", "readiness_record_path", "readiness_record_sha256",
    "parent_readiness_record_path", "parent_readiness_record_sha256",
    "case_order", "source_input_sha256", "candidate_oracle_sha256",
    "reviewer", "reviewed_at_utc", "mechanical_or_joint_acceptance",
    "native_solver_launched", "release",
})
LIMITS = {
    "cases_per_freeze": 1,
    "runs_total": 1,
    "runs_per_case": 1,
    "max_active_native_processes": 1,
    "seconds_per_case": 60,
    "output_bytes_per_case": 104857600,
    "stdout_or_stderr_bytes": 5242880,
    "cpus": 1,
    "memory": "1g",
    "memory_plus_swap": "1g",
    "pids_per_container": 128,
}
FROZEN_FILES = (
    "README.md",
    "source-snapshot.json",
    "expected.json",
    "readiness.json",
    "parent-readiness.json",
    "external-authorization.schema.json",
    "verifier.py",
    "run.py",
    "tests/test_candidate.py",
    "input/shared_slave_penalty.inp",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_exclusive(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def verify_static_pins() -> tuple[dict, dict]:
    """Check the fixed input/oracle/source pins and exactly one case."""
    expected = read_json(HERE / "expected.json")
    source = read_json(HERE / "source-snapshot.json")
    readiness = read_json(HERE / "readiness.json")
    parent = read_json(HERE / "parent-readiness.json")

    require(sha(HERE / "input" / f"{CASE}.inp") == INPUT_SHA256,
            "Frozen coupon input pin differs")
    require(sha(HERE / "expected.json") == ORACLE_SHA256,
            "Frozen one-case oracle pin differs")
    require(expected.get("schema") == "calculix_shared_slave_penalty_known_answer/v1",
            "Unexpected one-case oracle schema")
    require(expected.get("case_order") == [CASE] and
            list(expected.get("cases", {})) == [CASE],
            "The oracle must contain only shared_slave_penalty")
    require(set(path.stem for path in (HERE / "input").glob("*.inp")) == {CASE},
            "The input directory must contain only shared_slave_penalty")
    require(expected.get("native_execution_authorized") is False and
            expected.get("native_solver_launched") is False and
            expected.get("mechanical_or_joint_acceptance") is False and
            expected.get("release") is False,
            "Oracle must not claim authorization, execution, acceptance, or release")
    require(expected["source"]["source_expected_contract"]["sha256"] ==
            SOURCE_ORACLE_SHA256,
            "Upstream expected-contract pin differs")
    require(expected["source"]["one_case_parent_oracle"]["sha256"] ==
            PARENT_ORACLE_SHA256,
            "Parent projection oracle pin differs")

    require(source["selected_input"]["sha256"] == INPUT_SHA256,
            "Source snapshot input pin differs")
    require(source["upstream_expected_contract"]["sha256"] ==
            SOURCE_ORACLE_SHA256,
            "Source snapshot expected-contract pin differs")
    require(source["projection_parent"]["sha256"] == PARENT_ORACLE_SHA256,
            "Source snapshot parent-oracle pin differs")
    require(source["candidate_oracle"]["sha256"] == ORACLE_SHA256 and
            source["candidate_oracle"]["case_order"] == [CASE],
            "Source snapshot candidate-oracle pin or scope differs")
    require(source["route_review_parent"]["sha256"] == ROUTE_REVIEW_SHA256 and
            source["route_review_parent"]["proposal_input_sha256"] == INPUT_SHA256 and
            source["route_review_parent"]["proposal_expected_contract_sha256"] ==
            SOURCE_ORACLE_SHA256,
            "Route-review parent pins differ")
    require(expected["solver"]["base_image_id"] == IMAGE and
            expected["solver"]["binary_path"] == BINARY and
            expected["solver"]["binary_sha256"] == BINARY_SHA256,
            "Pinned solver image or executable differs")

    require(readiness.get("schema") == "shared_slave_penalty_one_case_readiness/v1",
            "Unexpected readiness schema")
    require(type(readiness.get("native_execution_authorized")) is bool and
            type(readiness.get("parent_readiness")) is bool,
            "Readiness gates must be explicit booleans")
    require(parent.get("schema") == "shared_slave_penalty_one_case_parent_readiness/v1",
            "Unexpected parent-readiness schema")
    require(type(parent.get("native_execution_authorized")) is bool and
            type(parent.get("parent_readiness")) is bool,
            "Parent-readiness gates must be explicit booleans")
    return expected, readiness


def freeze() -> dict:
    """Write the immutable one-case candidate freeze; this does not run it."""
    path = HERE / "input-freeze.json"
    require(not path.exists(), "Refusing to replace an existing freeze")
    verify_static_pins()
    require(read_json(HERE / "readiness.json")["native_execution_authorized"] is False and
            read_json(HERE / "readiness.json")["parent_readiness"] is False,
            "This candidate freeze must remain unauthorized and not parent-ready")
    require(read_json(HERE / "parent-readiness.json")["native_execution_authorized"] is False and
            read_json(HERE / "parent-readiness.json")["parent_readiness"] is False,
            "This candidate freeze must retain false parent readiness and authorization")
    record = {
        "schema": "shared_slave_penalty_one_case_freeze/v1",
        "created_at": now(),
        "cases": [CASE],
        "files_sha256": {relative: sha(HERE / relative) for relative in FROZEN_FILES},
        "source_pins": {
            "input_sha256": INPUT_SHA256,
            "upstream_expected_contract_sha256": SOURCE_ORACLE_SHA256,
            "parent_oracle_sha256": PARENT_ORACLE_SHA256,
            "candidate_oracle_sha256": ORACLE_SHA256,
            "route_review_parent_sha256": ROUTE_REVIEW_SHA256,
        },
        "image_id": IMAGE,
        "binary_path": BINARY,
        "binary_sha256": BINARY_SHA256,
        "limits": LIMITS,
        "authorization_transition": AUTHORIZATION_TRANSITION,
        "native_execution_authorized_at_freeze": False,
        "parent_readiness_at_freeze": False,
        "scope": "One small static shared-slave penalty coupon only; no full-joint, dynamic, capacity, or release acceptance",
    }
    write_exclusive(path, record)
    print(json.dumps({"status": "FROZEN_CANDIDATE_NOT_AUTHORIZED",
                      "cases": record["cases"], "input_freeze_sha256": sha(path)}))
    return record


def verify_freeze(freeze_sha256: str) -> dict:
    freeze_path = HERE / "input-freeze.json"
    require(freeze_path.exists(), "Missing one-case candidate freeze")
    require(sha(freeze_path) == freeze_sha256,
            "Freeze differs from the exact parent-reviewed freeze hash")
    record = read_json(freeze_path)
    require(record.get("schema") == "shared_slave_penalty_one_case_freeze/v1",
            "Unexpected freeze schema")
    require(record.get("cases") == [CASE], "Freeze is not exactly one case")
    require(record.get("native_execution_authorized_at_freeze") is False and
            record.get("parent_readiness_at_freeze") is False,
            "Freeze-time authorization and parent-readiness must remain false")
    require(record.get("limits") == LIMITS, "Freeze limits differ from runner caps")
    require(record.get("authorization_transition") == AUTHORIZATION_TRANSITION,
            "Freeze authorization transition differs")
    require(record.get("source_pins") == {
        "input_sha256": INPUT_SHA256,
        "upstream_expected_contract_sha256": SOURCE_ORACLE_SHA256,
        "parent_oracle_sha256": PARENT_ORACLE_SHA256,
        "candidate_oracle_sha256": ORACLE_SHA256,
        "route_review_parent_sha256": ROUTE_REVIEW_SHA256,
    }, "Freeze source, input, or oracle pins differ")
    require(set(record.get("files_sha256", {})) == set(FROZEN_FILES),
            "Freeze artifact inventory differs")
    for relative, digest in record["files_sha256"].items():
        require(sha(HERE / relative) == digest, f"Frozen artifact differs: {relative}")
    verify_static_pins()
    require(record.get("image_id") == IMAGE and
            record.get("binary_path") == BINARY and
            record.get("binary_sha256") == BINARY_SHA256,
            "Frozen solver identity differs")
    return record


def check_external_authorization(
    freeze_sha256: str,
    readiness_sha256: str,
    parent_readiness_sha256: str,
    authorization: dict,
) -> None:
    """Purely validate an out-of-packet parent decision bound to this freeze."""
    require(isinstance(authorization, dict),
            "External authorization must be a JSON object")
    require(set(authorization) == AUTHORIZATION_FIELDS,
            "External authorization fields differ from the frozen schema")
    require(authorization.get("schema") ==
            "shared_slave_penalty_one_case_external_authorization/v1",
            "Unexpected external authorization schema")
    require(authorization.get("status") == "AUTHORIZED_FOR_ONE_CASE_COUPON_ONLY",
            "External authorization is not in the authorized state")
    require(authorization.get("native_execution_authorized") is True and
            authorization.get("parent_readiness") is True,
            "External authorization gates are false")
    require(authorization.get("input_freeze_sha256") == freeze_sha256,
            "External authorization does not name this exact input freeze")
    require(authorization.get("readiness_record_path") == "readiness.json" and
            authorization.get("readiness_record_sha256") == readiness_sha256,
            "External authorization does not name this exact readiness record")
    require(authorization.get("parent_readiness_record_path") ==
            "parent-readiness.json" and
            authorization.get("parent_readiness_record_sha256") ==
            parent_readiness_sha256,
            "External authorization does not name this exact parent-readiness record")
    require(authorization.get("case_order") == [CASE],
            "External authorization case scope differs")
    require(authorization.get("source_input_sha256") == INPUT_SHA256 and
            authorization.get("candidate_oracle_sha256") == ORACLE_SHA256,
            "External authorization source pins differ")
    require(isinstance(authorization.get("reviewer"), str) and
            bool(authorization["reviewer"].strip()),
            "External authorization has no reviewer")
    require(isinstance(authorization.get("reviewed_at_utc"), str) and
            bool(authorization["reviewed_at_utc"].strip()),
            "External authorization has no review timestamp")
    try:
        reviewed_at = datetime.fromisoformat(
            authorization["reviewed_at_utc"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError("External authorization timestamp is invalid") from exc
    require(reviewed_at.tzinfo is not None,
            "External authorization timestamp must include a timezone")
    require(reviewed_at.utcoffset() == timezone.utc.utcoffset(reviewed_at),
            "External authorization timestamp must be UTC")
    require(authorization.get("mechanical_or_joint_acceptance") is False and
            authorization.get("native_solver_launched") is False and
            authorization.get("release") is False,
            "External authorization must not claim execution, acceptance, or release")


def assert_execution_ready(
    freeze_sha256: str,
    authorization: dict | None = None,
) -> None:
    """Validate a separate parent authorization without editing frozen inputs.

    The candidate's readiness files are immutable pending-review snapshots.
    A parent decision supplied out-of-packet may authorize the exact snapshots
    and freeze after reviewing them. This function performs no process or
    Docker calls.
    """
    readiness = read_json(HERE / "readiness.json")
    parent = read_json(HERE / "parent-readiness.json")
    readiness_sha256 = sha(HERE / "readiness.json")
    parent_sha256 = sha(HERE / "parent-readiness.json")
    require(readiness.get("native_execution_authorized") is False and
            readiness.get("parent_readiness") is False and
            readiness.get("native_solver_launched") is False,
            "Frozen candidate readiness snapshot must remain false")
    require(parent.get("native_execution_authorized") is False and
            parent.get("parent_readiness") is False,
            "Frozen parent-readiness snapshot must remain false")
    require(authorization is not None,
            "Readiness is false; no external parent authorization was supplied")
    check_external_authorization(freeze_sha256, readiness_sha256,
                                parent_sha256, authorization)


def load_external_authorization(path: Path) -> tuple[dict, str]:
    """Read the parent decision from outside this immutable candidate packet."""
    resolved = path.expanduser().resolve(strict=True)
    try:
        resolved.relative_to(HERE.resolve())
    except ValueError:
        pass
    else:
        raise RuntimeError("External authorization must be stored outside the candidate packet")
    require(resolved.is_file(), "External authorization path is not a file")
    return read_json(resolved), sha(resolved)


def capture(command: list[str], timeout: int = 20) -> str:
    result = subprocess.run(command, check=True, capture_output=True,
                            text=True, timeout=timeout)
    return result.stdout.strip()


def output_sizes(output: Path) -> tuple[int, int]:
    files = [path for path in output.iterdir() if path.is_file()]
    total = sum(path.stat().st_size for path in files)
    log_sizes = [path.stat().st_size for path in
                 (output / "coupon.stdout", output / "coupon.stderr")
                 if path.exists()]
    return total, max(log_sizes, default=0)


def stop_container(name: str) -> None:
    subprocess.run(["docker", "stop", "--time", "2", name],
                   capture_output=True, timeout=10, check=False)
    state = json.loads(capture(["docker", "inspect", name]))[0]["State"]
    if state["Running"]:
        subprocess.run(["docker", "kill", name], capture_output=True,
                       timeout=10, check=True)
        state = json.loads(capture(["docker", "inspect", name]))[0]["State"]
    require(not state["Running"], f"Container is still running: {name}")


def run(freeze_sha256: str, authorization_path: Path | None = None) -> dict:
    """Run the sole frozen case once, after all authorization gates pass."""
    frozen = verify_freeze(freeze_sha256)
    authorization = None
    authorization_sha256 = None
    if authorization_path is not None:
        authorization, authorization_sha256 = load_external_authorization(
            authorization_path)
    assert_execution_ready(freeze_sha256, authorization)
    root_execution = HERE / "execution.json"
    output = HERE / "output" / CASE
    require(not root_execution.exists() and not (HERE / "output").exists(),
            "Refusing rerun or a second output path")
    require(frozen["cases"] == [CASE], "Refusing a multi-case or reordered run")
    require(capture(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"],
                    timeout=20) == IMAGE, "Docker image pin differs")
    executable = capture(["docker", "run", "--pull=never", "--rm", "--network", "none",
                          IMAGE, "sha256sum", BINARY], timeout=30).split()[0]
    require(executable == BINARY_SHA256, "Executable pin differs")

    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(HERE / "input" / f"{CASE}.inp", output / "coupon.inp")
    require(sha(output / "coupon.inp") == INPUT_SHA256,
            "Run input copy differs from the frozen coupon")
    name = "wj-shared-slave-penalty-" + CASE + "-" + str(time.time_ns())
    command = [
        "docker", "run", "--pull=never", "--name", name, "--network", "none",
        "--cpus", "1", "--memory", "1g", "--memory-swap", "1g",
        "--pids-limit", "128", "--user", f"{os.getuid()}:{os.getgid()}",
        "--env", "OMP_NUM_THREADS=1", "--env", "CCX_NPROC_EQUATION_SOLVER=1",
        "--mount", f"type=bind,src={output},dst=/work", "--workdir", "/work",
        IMAGE, BINARY, "-i", "coupon",
    ]
    started_at = now()
    started = time.monotonic()
    stop_reason = None
    process = None
    try:
        with (output / "coupon.stdout").open("xb") as stdout, \
                (output / "coupon.stderr").open("xb") as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            while process.poll() is None:
                total, log_bytes = output_sizes(output)
                if time.monotonic() - started > LIMITS["seconds_per_case"]:
                    stop_reason = "wall_time_limit"
                elif total > LIMITS["output_bytes_per_case"] or \
                        log_bytes > LIMITS["stdout_or_stderr_bytes"]:
                    stop_reason = "output_size_limit"
                if stop_reason:
                    stop_container(name)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    break
                time.sleep(0.1)
            docker_cli_exit_code = process.wait(timeout=10)
        total, log_bytes = output_sizes(output)
        if total > LIMITS["output_bytes_per_case"] or \
                log_bytes > LIMITS["stdout_or_stderr_bytes"]:
            stop_reason = "output_size_limit"
        inspected = json.loads(capture(["docker", "inspect", name]))[0]
        state = inspected["State"]
        status = "completed" if (
            docker_cli_exit_code == 0 and state["ExitCode"] == 0 and
            not state["Running"] and not state["OOMKilled"] and
            inspected["Image"] == IMAGE and stop_reason is None
        ) else "failed_or_stopped"
        record = {
            "case": CASE,
            "status": status,
            "container": name,
            "command": command,
            "container_image": inspected["Image"],
            "container_state": state,
            "docker_cli_exit_code": docker_cli_exit_code,
            "stop_reason": stop_reason,
            "started_at": started_at,
            "ended_at": now(),
            "elapsed_seconds": time.monotonic() - started,
            "total_output_bytes": total,
            "max_log_bytes": log_bytes,
            "outputs_sha256": {
                path.name: sha(path) for path in sorted(output.iterdir())
                if path.is_file()
            },
        }
    except BaseException as exc:
        if process is not None and process.poll() is None:
            try:
                stop_container(name)
            finally:
                process.kill()
        record = {
            "case": CASE,
            "status": "capture_exception",
            "container": name,
            "command": command,
            "stop_reason": stop_reason,
            "exception": repr(exc),
            "started_at": started_at,
            "ended_at": now(),
            "elapsed_seconds": time.monotonic() - started,
            "outputs_sha256": {
                path.name: sha(path) for path in sorted(output.iterdir())
                if path.is_file()
            },
        }

    record["input_freeze_sha256"] = freeze_sha256
    record["readiness_record_sha256"] = sha(HERE / "readiness.json")
    record["parent_readiness_record_sha256"] = sha(HERE / "parent-readiness.json")
    record["external_authorization_sha256"] = authorization_sha256
    record["source_input_sha256"] = INPUT_SHA256
    record["candidate_oracle_sha256"] = ORACLE_SHA256
    record["mechanical_acceptance"] = False
    record["joint_acceptance"] = False
    record["release"] = False
    write_exclusive(output / "execution.json", record)
    root_record = {
        "schema": "shared_slave_penalty_one_case_execution/v1",
        "status": "completed_pending_audit" if record["status"] == "completed"
                  else "failed_or_stopped",
        "cases": [CASE],
        "runs": [record],
        "started_at": started_at,
        "ended_at": record["ended_at"],
        "input_freeze_sha256": freeze_sha256,
        "readiness_record_sha256": sha(HERE / "readiness.json"),
        "parent_readiness_record_sha256": sha(HERE / "parent-readiness.json"),
        "external_authorization_sha256": authorization_sha256,
        "binary_sha256": BINARY_SHA256,
        "image_id": IMAGE,
        "frozen_inputs_unchanged": all(
            sha(HERE / relative) == digest
            for relative, digest in frozen["files_sha256"].items()
        ),
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "release": False,
    }
    write_exclusive(root_execution, root_record)
    require(root_record["frozen_inputs_unchanged"],
            "Frozen candidate changed during execution")
    print(json.dumps({"status": root_record["status"],
                      "execution_sha256": sha(root_execution)}))
    return root_record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "run"))
    parser.add_argument("--freeze-sha", help="Exact parent-reviewed input-freeze SHA-256")
    parser.add_argument("--authorization-json", type=Path,
                        help="External parent authorization JSON stored outside this packet")
    args = parser.parse_args()
    if args.action == "freeze":
        freeze()
    else:
        require(bool(args.freeze_sha), "run requires --freeze-sha")
        require(args.authorization_json is not None,
                "run requires --authorization-json outside this packet")
        run(args.freeze_sha, args.authorization_json)
