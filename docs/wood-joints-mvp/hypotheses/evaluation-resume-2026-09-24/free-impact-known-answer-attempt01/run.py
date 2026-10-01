#!/usr/bin/env python3
"""Parent-operated freeze and two serialized free-impact contact method fixtures."""

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
ROOT = next(parent for parent in HERE.parents if (parent / ".git").exists())
FREEZE = HERE / "input-freeze.json"
OUTPUT = HERE / "output"
TIMEOUT = 60
OUTPUT_LIMIT = 16 * 1024 * 1024
EXECUTION_SCHEMA = "ccx223_free_impact_execution/v1"
FREEZE_SCHEMA = "ccx223_free_impact_freeze/v1"
NATIVE_FILES = ("coupon.dat", "coupon.sta", "coupon.cvg", "coupon.frd", "solver.stdout", "solver.stderr")
STATIC_FILES = (
    "fixture-design.md", "prepare.py", "run.py", "verifier.py", "expected.json",
    "acceptance.json", "input/coupon.inp",
    "independent-preflight.md", "parent-review.json", "parent-input-audit.json", "audit-input.py",
)
TRACE_ROOT = HERE.parent / "implicit-contact-point-trace-attempt01"
BUILD_PINS = {
    "baseline": {
        "image_id": "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38",
        "binary_path": "/usr/local/bin/ccx-upstream-2.23",
        "binary_sha256": "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863",
    },
    "trace": {
        "image_id": "sha256:f00deed9be383c1095cdc03a1556d00cf8982f54100217a05ffae079e8a3bb36",
        "binary_path": "/usr/local/bin/ccx-contact-point-trace-2.23",
        "binary_sha256": "3f949f639ead34b7ca62e2226480635cc0f5dbeda14afc200dcb523cf640b203",
    },
}
DEPENDENCIES = (
    "implicit-contact-free-impact-design-attempt01/README.md",
    "implicit-contact-free-impact-design-attempt01/parent-reference.py",
    "implicit-contact-free-impact-design-attempt01/parent-reference.json",
    "explicit-c3d10-mpc-known-answer-attempt01/verifier.py",
    "implicit-c3d10-mpc-known-answer-attempt01/verifier.py",
    "implicit-c3d10-mpc-known-answer-attempt01/input-freeze.json",
    "implicit-c3d10-mpc-known-answer-attempt01/output/execution.json",
    "implicit-c3d10-mpc-known-answer-attempt01/verifier.json",
    "implicit-c3d10-mpc-known-answer-attempt01/independent-postrun.md",
    "contact-penalty-touch-work-known-answer-attempt01/pair_output.py",
    "implicit-contact-point-trace-attempt01/input/implicit_point_trace.inp",
    "implicit-contact-point-trace-attempt01/trace-format.json",
    "implicit-contact-point-trace-attempt01/diagnostic.patch",
    "implicit-contact-point-trace-attempt01/code-review.md",
    "implicit-contact-point-trace-attempt01/build-attempt04/build-manifest.json",
    "implicit-contact-point-trace-attempt01/build-attempt04/execution.json",
    "implicit-contact-point-trace-attempt01/dynamic-known-answer-attempt01/verifier.py",
    "implicit-contact-point-trace-attempt01/static-regression-attempt02/input-freeze.json",
    "implicit-contact-point-trace-attempt01/static-regression-attempt02/output/execution.json",
    "implicit-contact-point-trace-attempt01/static-regression-attempt02/verifier.json",
    "calculix-2.23-upgrade-attempt01/build_manifest.json",
)

ARCHIVE = HERE.parent / "ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source.tar.bz2"



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
    def reject_constant(value):
        raise ValueError(f"Invalid JSON constant {value} in {path}")
    return json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                      parse_constant=reject_constant)


def write_replace(path: Path, record: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("xb") as stream:
        stream.write((json.dumps(record, indent=2, sort_keys=True) + "\n").encode())
    os.replace(temp, path)


def verify_packet() -> tuple[dict, dict]:
    import tarfile
    expected = read_json(HERE / "expected.json")
    require(expected.get("schema") == "ccx223_free_impact_expected/v1" and
            expected.get("case_order") == ["baseline", "trace"], "Unexpected fixture contract")
    require((HERE / "acceptance.json").is_file(), "Acceptance thresholds must precede native execution")
    require(read_json(HERE / "parent-review.json")["ready_for_native_fixture_only"] is True,
            "Parent readiness is not established")
    subprocess.run([sys.executable, str(HERE / "prepare.py"), "--check"],
                   check=True, capture_output=True, text=True, timeout=15)
    subprocess.run([sys.executable, str(HERE / "audit-input.py")],
                   check=True, capture_output=True, text=True, timeout=15)
    for case, item in expected["inputs"].items():
        require(sha(HERE / item["path"]) == item["sha256"], f"Changed input: {case}")
    sources = expected["pinned_sources"]
    require(sha(ARCHIVE) == sources["source_archive_sha256"], "Source archive changed")
    with tarfile.open(ARCHIVE) as archive:
        for name, info in sources["source_files"].items():
            content = archive.extractfile("./CalculiX/ccx_2.23/src/" + name).read()
            require(sha_bytes(content) == info["sha256"], f"Source member changed: {name}")
    require(sha(ROOT / "fea/generated/ccx_2.23.pdf") == sources["manual_pdf_sha256"],
            "Pinned solver manual changed")
    expected["build_pins"] = BUILD_PINS
    expected["run_limits"] = {
        "wall_seconds_each_case": TIMEOUT, "cpus_each_case": 1,
        "memory_bytes_each_case": 1073741824, "memory_plus_swap_bytes_each_case": 1073741824,
        "network_each_case": "none", "aggregate_native_output_bytes_each_case": OUTPUT_LIMIT,
        "serialized_case_order": expected["case_order"], "omp_threads": 1,
        "ccx_solver_processes": 1, "no_overlap": True,
    }
    return expected, {"input_sha256": {case: item["sha256"] for case, item in expected["inputs"].items()},
                      "build_pins": BUILD_PINS}


def frozen_inventory() -> dict[str, str]:
    return {rel: sha(HERE / rel) for rel in sorted(STATIC_FILES)}


def external_dependency_inventory() -> dict[str, str]:
    paths = [ARCHIVE, ROOT / "fea/generated/ccx_2.23.pdf"]
    paths.extend(HERE.parent / relative for relative in DEPENDENCIES)
    return {str(path.relative_to(ROOT)): sha(path) for path in paths}


def freeze() -> dict:
    require(not FREEZE.exists(), "Refusing to replace an existing input freeze")
    require(not OUTPUT.exists(), "Refusing to freeze after native outputs exist")
    expected, summary = verify_packet()
    pins = expected["build_pins"]
    inventory = frozen_inventory()
    external = external_dependency_inventory()
    record = {
        "schema": FREEZE_SCHEMA,
        "created_utc": now(),
        "files_sha256": inventory,
        "external_dependencies_sha256": external,
        "expected_sha256": sha(HERE / "expected.json"),
        "input_sha256": {case: item["sha256"] for case, item in expected["inputs"].items()},
        "baseline_image_id": pins["baseline"]["image_id"],
        "baseline_binary_sha256": pins["baseline"]["binary_sha256"],
        "trace_image_id": pins["trace"]["image_id"],
        "trace_binary_sha256": pins["trace"]["binary_sha256"],
        "limits": expected["run_limits"],
        "case_order": expected["case_order"],
        "native_execution": False,
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "preparation_summary": summary,
    }
    with FREEZE.open("xb") as stream:
        stream.write((json.dumps(record, indent=2, sort_keys=True) + "\n").encode())
    return {"status": "FROZEN_FOR_PARENT_SERIALIZED_RUNS_ONLY",
            "freeze_sha256": sha(FREEZE),
            "expected_sha256": record["expected_sha256"],
            "local_file_count": len(inventory),
            "external_dependency_count": len(external)}


def verify_freeze(requested_sha: str) -> tuple[dict, dict]:
    require(FREEZE.is_file(), "Parent freeze required before native runs")
    require(sha(FREEZE) == requested_sha,
            "Supplied freeze hash does not match input-freeze.json")
    frozen = read_json(FREEZE)
    expected, _summary = verify_packet()
    pins = expected["build_pins"]
    require(frozen.get("schema") == FREEZE_SCHEMA and
            frozen.get("expected_sha256") == sha(HERE / "expected.json") and
            frozen.get("input_sha256") == {case: item["sha256"] for case, item in expected["inputs"].items()} and
            frozen.get("baseline_image_id") == pins["baseline"]["image_id"] and
            frozen.get("baseline_binary_sha256") == pins["baseline"]["binary_sha256"] and
            frozen.get("trace_image_id") == pins["trace"]["image_id"] and
            frozen.get("trace_binary_sha256") == pins["trace"]["binary_sha256"] and
            frozen.get("case_order") == ["baseline", "trace"] and
            frozen.get("native_execution") is False and
            frozen.get("mechanical_acceptance") is False and
            frozen.get("joint_acceptance") is False,
            "Freeze does not bind both cases and their non-qualification scope")
    require(frozen.get("files_sha256") == frozen_inventory(),
            "Frozen local packet files differ")
    require(frozen.get("external_dependencies_sha256") == external_dependency_inventory(),
            "Frozen external dependencies differ")
    return frozen, expected


def inspect_image(image_id: str) -> str:
    r = subprocess.run(["docker", "image", "inspect", image_id, "--format", "{{.Id}}"],
                       check=True, text=True, capture_output=True, timeout=20)
    return r.stdout.strip()


def inspect_container(name: str) -> dict:
    r = subprocess.run(["docker", "inspect", name], check=True, text=True,
                       capture_output=True, timeout=20)
    return json.loads(r.stdout)[0]


def stop_container(name: str) -> dict | None:
    try:
        current = inspect_container(name)
    except Exception:
        return None
    if current["State"].get("Running"):
        subprocess.run(["docker", "kill", name], capture_output=True,
                       text=True, timeout=15, check=False)
    try:
        return inspect_container(name)["State"]
    except Exception:
        return None


def output_bytes(directory: Path) -> int:
    excluded = {"coupon.inp", "case-execution.json", "case-execution.json.tmp"}
    return sum(p.stat().st_size for p in directory.rglob("*")
               if p.is_file() and p.name not in excluded)


def output_hashes(directory: Path) -> dict[str, str]:
    return {p.name: sha(p) for p in sorted(directory.iterdir())
            if p.is_file() and p.name not in {"case-execution.json", "case-execution.json.tmp"}}


def case_command(case: str, name: str, mount: Path, pins: dict) -> list[str]:
    source = pins[case]
    return [
        "docker", "run", "--pull=never", "--name", name,
        "--network", "none", "--cpus", "1", "--memory", "1g",
        "--memory-swap", "1g", "--user", f"{os.getuid()}:{os.getgid()}",
        "--env", "OMP_NUM_THREADS=1", "--env", "CCX_NPROC_EQUATION_SOLVER=1",
        "--mount", f"type=bind,src={mount},dst=/work", "--workdir", "/work",
        source["image_id"], source["binary_path"], "-i", "coupon",
    ]


def run_case(case: str, case_index: int, expected: dict,
             top_record: dict) -> dict:
    pins = expected["build_pins"]
    destination = OUTPUT / case
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(HERE / expected["inputs"][case]["path"], destination / "coupon.inp")
    require(sha(destination / "coupon.inp") == expected["inputs"][case]["sha256"],
            f"{case} working input differs from freeze")
    name = f"ccx-free-impact-{case}-{time.time_ns()}"
    command = case_command(case, name, destination, pins)
    record = {
        "schema": "ccx223_free_impact_case_execution/v1",
        "case": case,
        "case_order_index": case_index,
        "status": "RUNNING",
        "container_name": name,
        "image_id": pins[case]["image_id"],
        "binary_path": pins[case]["binary_path"],
        "binary_sha256": pins[case]["binary_sha256"],
        "command": command,
        "limits": expected["run_limits"],
        "started_utc": now(),
        "native_execution": True,
        "mechanical_acceptance": False,
        "joint_acceptance": False,
    }
    case_record_path = destination / "case-execution.json"
    process = None
    reason = None
    state = None
    container_image_id = None
    container_image_ref = None
    start = time.monotonic()
    try:
        require(inspect_image(pins[case]["image_id"]) == pins[case]["image_id"],
                f"Pinned {case} image is unavailable by immutable ID")
        with (destination / "solver.stdout").open("xb") as stdout, \
                (destination / "solver.stderr").open("xb") as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                       text=False, start_new_session=True)
            top_record["native_execution"] = True
            top_record["status"] = "CASE_RUNNING"
            top_record["currently_running_case"] = case
            top_record.setdefault("first_native_started_utc", now())
            write_replace(OUTPUT / "execution.json", top_record)
            while process.poll() is None:
                elapsed = time.monotonic() - start
                if elapsed > TIMEOUT:
                    reason = "wall_timeout"
                    state = stop_container(name)
                    process.kill()
                    break
                if output_bytes(destination) > OUTPUT_LIMIT:
                    reason = "aggregate_output_limit"
                    state = stop_container(name)
                    process.kill()
                    break
                time.sleep(0.1)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                reason = reason or "docker_cli_did_not_exit"
                process.kill()
                process.wait(timeout=10)
        if state is None:
            try:
                container_info = inspect_container(name)
                state = container_info["State"]
                container_image_id = container_info.get("Image")
                container_image_ref = container_info.get("Config", {}).get("Image")
            except Exception:
                state = None
        else:
            try:
                container_info = inspect_container(name)
                container_image_id = container_info.get("Image")
                container_image_ref = container_info.get("Config", {}).get("Image")
            except Exception:
                pass
        record["docker_cli_exit_code"] = process.returncode
        record["container_state"] = state
        record["container_image_id"] = container_image_id
        record["container_image_ref"] = container_image_ref
        record["elapsed_seconds"] = time.monotonic() - start
        record["ended_utc"] = now()
        record["native_output_bytes"] = output_bytes(destination)
        record["outputs_sha256"] = output_hashes(destination)
        record["stop_reason"] = reason
        outputs_present = set(NATIVE_FILES) <= set(record["outputs_sha256"])
        normal_marker = (b" Job finished" in (destination / "solver.stdout").read_bytes()
                         if (destination / "solver.stdout").exists() else False)
        if reason is not None:
            record["status"] = "FAIL_LIMIT_OR_PROCESS"
        elif (process.returncode == 0 and state is not None and
              state.get("ExitCode") == 0 and state.get("Running") is False and
              state.get("OOMKilled") is False and normal_marker and outputs_present and
              record["native_output_bytes"] <= OUTPUT_LIMIT):
            record["status"] = "PASS_NATIVE_CAPTURE"
        else:
            record["status"] = "FAIL_NATIVE_CAPTURE"
        write_replace(case_record_path, record)
    except Exception as exc:
        record["status"] = "FAIL_CAPTURE_EXCEPTION"
        record["exception"] = repr(exc)
        record["container_state"] = state or stop_container(name)
        try:
            container_info = inspect_container(name)
            record["container_image_id"] = container_info.get("Image")
            record["container_image_ref"] = container_info.get("Config", {}).get("Image")
        except Exception:
            record["container_image_id"] = None
            record["container_image_ref"] = None
        record["docker_cli_exit_code"] = process.returncode if process else None
        record["elapsed_seconds"] = time.monotonic() - start
        record["ended_utc"] = now()
        record["native_output_bytes"] = output_bytes(destination)
        record["outputs_sha256"] = output_hashes(destination)
        record["stop_reason"] = reason
        write_replace(case_record_path, record)
    return record


def run_pair(freeze_sha: str) -> dict:
    _frozen, expected = verify_freeze(freeze_sha)
    for case, pin in BUILD_PINS.items():
        binary_check = subprocess.check_output(
            ["docker", "run", "--rm", "--pull=never", "--network", "none", pin["image_id"],
             "sha256sum", pin["binary_path"]], text=True, timeout=20)
        require(binary_check.split()[0] == pin["binary_sha256"],
                f"Pinned {case} binary identity differs")
    require(not OUTPUT.exists(), "Refusing rerun or overlapping paired output")
    OUTPUT.mkdir(parents=True, exist_ok=False)
    top = {
        "schema": EXECUTION_SCHEMA,
        "status": "RUNNING",
        "freeze_sha256": sha(FREEZE),
        "expected_sha256": sha(HERE / "expected.json"),
        "input_sha256": {case: item["sha256"] for case, item in expected["inputs"].items()},
        "case_order": expected["case_order"],
        "serialized": True,
        "native_execution": False,
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "cases": [],
    }
    write_replace(OUTPUT / "execution.json", top)
    for index, case in enumerate(expected["case_order"], start=1):
        case_record = run_case(case, index, expected, top)
        top["cases"].append({"case": case, "status": case_record["status"],
                             "execution_sha256": sha(OUTPUT / case / "case-execution.json")})
        top.pop("currently_running_case", None)
        top["last_case_ended_utc"] = case_record.get("ended_utc")
        if case_record["status"] != "PASS_NATIVE_CAPTURE":
            top["status"] = "STOPPED_AFTER_CASE_FAILURE"
            top["completed_utc"] = now()
            write_replace(OUTPUT / "execution.json", top)
            return top
        top["status"] = "CAPTURES_COMPLETE_PENDING_VERIFICATION" if index == 2 else "FIRST_CAPTURE_COMPLETE"
        write_replace(OUTPUT / "execution.json", top)
    top["status"] = "CAPTURES_COMPLETE_PENDING_VERIFICATION"
    top["completed_utc"] = now()
    write_replace(OUTPUT / "execution.json", top)
    return top


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Read-only packet and source pin check")
    mode.add_argument("--freeze", action="store_true", help="Create parent-owned input freeze")
    mode.add_argument("--run", action="store_true", help="Run two serialized cases after parent freeze")
    parser.add_argument("--freeze-sha", help="Required exact input-freeze SHA-256 for --run")
    args = parser.parse_args()
    if args.check:
        expected, summary = verify_packet()
        print(json.dumps({"status": "PASS_READ_ONLY", "case_order": expected["case_order"],
                          **summary}, sort_keys=True))
        return 0
    if args.freeze:
        print(json.dumps(freeze(), sort_keys=True))
        return 0
    require(bool(args.freeze_sha), "--run requires --freeze-sha <sha256>")
    result = run_pair(args.freeze_sha)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "CAPTURES_COMPLETE_PENDING_VERIFICATION" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        raise SystemExit(2)
