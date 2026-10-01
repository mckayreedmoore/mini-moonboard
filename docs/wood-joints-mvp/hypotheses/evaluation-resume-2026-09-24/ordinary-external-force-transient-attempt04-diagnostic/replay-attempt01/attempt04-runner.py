"""Run the frozen attempt03 deck with bounded, auditable output capture."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fea.wood_joint_current_transient_launch import IncrementalMonitor


ATTEMPT_PARENT = Path(__file__).resolve().parent.parent
SOURCE_ATTEMPT03 = ROOT / (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "ordinary-external-force-transient-attempt03"
)
INPUT_BINDING_PATH = ATTEMPT_PARENT / "attempt03-input-binding.json"
BUILD_RESULT_PATH = ATTEMPT_PARENT / "build-attempt02/build_result.json"
BUILD_MANIFEST_PATH = ATTEMPT_PARENT / "build-attempt02/build_manifest.json"
COUPON_GATE_DIR = ATTEMPT_PARENT / "coupon-known-answer-attempt02"

EXPECTED_BINDING_SHA256 = (
    "cc9a3db03c8b408748c2ebc38a7fe7d134e5a494d19b792e461dd39f066f2c05"
)
EXPECTED_IMAGE_ID = (
    "sha256:1cc1d52946c5acddc9d4eeaf1dd1bf0bc4d3f564eb1c264f5d29b67c6386b7fa"
)
EXPECTED_BASE_IMAGE_ID = (
    "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
)
EXPECTED_BINARY_PATH = "/usr/local/bin/ccx-attempt04-diagnostic-2.23"
EXPECTED_BINARY_SHA256 = (
    "3aec6cfe0ca72a463d87c648ed6b4a83ee1bb6a08bf604a144c8a6553d2f439f"
)
EXPECTED_UPSTREAM_BINARY_SHA256 = (
    "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863"
)
STDOUT_SOFT_LIMIT_BYTES = 16 * 1024 * 1024
POLL_SECONDS = 2

OUTPUT_NAMES = (
    "pilot.12d",
    "pilot.cel",
    "pilot.cvg",
    "pilot.dat",
    "pilot.frd",
    "pilot.log",
    "pilot.sta",
    "pilot.stdout",
    "spooles.out",
    "ResultsForLastIterations.frd",
)
RESERVED_NAMES = {
    "README.md",
    "REPLAY.md",
    "input-copy-manifest.json",
    "attempt04-runner.py",
    "execution.json",
    "execution.json.tmp",
    "launch-gate.json",
    "launch-gate.json.tmp",
}
STA_ROW = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$")
CVG_ROW = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+.*$")
TRACE_EVENTS = {
    "CCX223_ATTEMPT04_CONTACT",
    "CCX223_ATTEMPT04_CONVERGENCE",
}


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def save_json(folder: Path, name: str, record: dict[str, Any]) -> None:
    temporary = folder / f"{name}.tmp"
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    os.replace(temporary, folder / name)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def accepted_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = path.read_bytes()
    complete = raw[: raw.rfind(b"\n") + 1].decode("ascii", errors="strict")
    result = []
    for line in complete.splitlines():
        match = STA_ROW.match(line)
        if match is None:
            continue
        step, increment, attempt, iterations = map(int, match.groups()[:4])
        times = [float(value.replace("D", "E")) for value in match.groups()[4:]]
        result.append(
            {
                "step": step,
                "increment": increment,
                "attempt": attempt,
                "iterations": iterations,
                "total_time": times[0],
                "step_time": times[1],
                "increment_time": times[2],
            }
        )
    return result


def cvg_rows(path: Path) -> list[dict[str, int]]:
    if not path.exists():
        return []
    raw = path.read_bytes()
    complete = raw[: raw.rfind(b"\n") + 1].decode("ascii", errors="replace")
    result = []
    for line in complete.splitlines():
        match = CVG_ROW.match(line)
        if match is None:
            continue
        step, increment, attempt, iteration, contact_elements = map(int, match.groups())
        result.append(
            {
                "step": step,
                "increment": increment,
                "attempt": attempt,
                "iteration": iteration,
                "contact_elements": contact_elements,
            }
        )
    return result


def last_cvg_row(path: Path) -> dict[str, int] | None:
    rows = cvg_rows(path)
    return rows[-1] if rows else None


def incomplete_tail(path: Path, window_bytes: int = 65536) -> dict[str, Any]:
    """Describe, without trimming, any final line fragment in a captured file."""
    if not path.exists():
        return {"exists": False, "incomplete": False}
    size = path.stat().st_size
    if size == 0:
        return {"exists": True, "incomplete": False, "size_bytes": 0}
    with path.open("rb") as stream:
        stream.seek(max(0, size - window_bytes))
        tail = stream.read(window_bytes)
    if tail.endswith(b"\n"):
        return {"exists": True, "incomplete": False, "size_bytes": size}
    fragment = tail[tail.rfind(b"\n") + 1 :]
    return {
        "exists": True,
        "incomplete": True,
        "size_bytes": size,
        "tail_window_bytes": len(tail),
        "fragment_bytes": len(fragment),
        "fragment_sha256": hashlib.sha256(fragment).hexdigest(),
        "fragment_text_prefix": fragment[:1024].decode("utf-8", errors="replace"),
        "fragment_may_exceed_window": size > window_bytes and b"\n" not in tail,
    }


def trace_audit(folder: Path) -> dict[str, Any]:
    """Count complete diagnostic events and compare convergence keys with .cvg."""
    stdout_path = folder / "pilot.stdout"
    events: dict[str, list[tuple[int, int, int, int]]] = {
        name: [] for name in TRACE_EVENTS
    }
    malformed = []
    if stdout_path.exists():
        raw = stdout_path.read_bytes()
        complete = raw[: raw.rfind(b"\n") + 1]
        for line_number, line in enumerate(complete.splitlines(), start=1):
            try:
                item = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not isinstance(item, dict) or item.get("event") not in TRACE_EVENTS:
                continue
            event = item["event"]
            try:
                key = tuple(
                    int(item[name])
                    for name in ("step", "increment", "attempt", "iteration")
                )
            except (KeyError, TypeError, ValueError):
                malformed.append({"line": line_number, "event": event})
                continue
            events[event].append(key)

    convergence_keys = events["CCX223_ATTEMPT04_CONVERGENCE"]
    contact_keys = events["CCX223_ATTEMPT04_CONTACT"]
    cvg_keys = [
        (row["step"], row["increment"], row["attempt"], row["iteration"])
        for row in cvg_rows(folder / "pilot.cvg")
    ]
    return {
        "convergence_event_count": len(convergence_keys),
        "contact_event_count": len(contact_keys),
        "cvg_complete_row_count": len(cvg_keys),
        "convergence_keys_match_cvg": convergence_keys == cvg_keys,
        "convergence_keys_missing_from_cvg": [
            list(key) for key in convergence_keys if key not in cvg_keys
        ],
        "cvg_keys_missing_convergence_event": [
            list(key) for key in cvg_keys if key not in convergence_keys
        ],
        "contact_keys": [list(key) for key in contact_keys],
        "contact_keys_missing_from_cvg": [
            list(key) for key in contact_keys if key not in cvg_keys
        ],
        "malformed_trace_identities": malformed,
        "terminal_incomplete_tails": {
            name: incomplete_tail(folder / name)
            for name in ("pilot.cvg", "pilot.sta", "pilot.cel", "pilot.stdout")
        },
        "interpretation": (
            "CONTACT events are emitted only at the later-iteration count branch; "
            "their count is not expected to equal CONVERGENCE or .cvg row count. "
            "Any incomplete terminal line remains in the hashed source output."
        ),
    }


def output_inventory(folder: Path, input_names: set[str]) -> dict[str, Any]:
    """Hash every captured non-input file and explicitly mark expected missing outputs."""
    outputs: dict[str, Any] = {}
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.name in input_names or path.name in RESERVED_NAMES:
            continue
        outputs[path.name] = {
            "exists": True,
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    for name in OUTPUT_NAMES:
        if name not in outputs:
            outputs[name] = {"exists": False, "size_bytes": None, "sha256": None}
    return outputs


def active_native_processes() -> dict[str, Any]:
    live = subprocess.check_output(
        ["docker", "ps", "--format", "{{.ID}} {{.Names}}"], text=True
    )
    active_containers = []
    for line in live.splitlines():
        container_id, name = line.split(maxsplit=1)
        if name.startswith("wj-"):
            active_containers.append(
                {"container": name, "reason": "project_native_name"}
            )
            continue
        process_list = subprocess.run(
            ["docker", "top", container_id, "-eo", "pid,comm,args"],
            capture_output=True,
            text=True,
        )
        if process_list.returncode != 0:
            raise RuntimeError(f"cannot inspect running container processes: {name}")
        if "ccx" in process_list.stdout.lower() or "calculix" in process_list.stdout.lower():
            active_containers.append(
                {"container": name, "reason": "solver_process"}
            )

    host_processes = []
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            command = (process / "cmdline").read_bytes().replace(b"\0", b" ")
            process_name = (process / "comm").read_text().strip()
        except (FileNotFoundError, PermissionError):
            continue
        combined = (process_name.encode() + b" " + command).lower()
        if b"ccx" in combined or b"calculix" in combined:
            host_processes.append(
                {"pid": int(process.name), "comm": process_name}
            )
    return {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "active_containers": active_containers,
        "active_host_processes": host_processes,
        "zero_active_solver": not active_containers and not host_processes,
    }


def coupon_gate_record() -> dict[str, Any]:
    execution_path = COUPON_GATE_DIR / "execution.json"
    verifier_path = COUPON_GATE_DIR / "verifier.json"
    record: dict[str, Any] = {
        "required": True,
        "directory": str(COUPON_GATE_DIR.relative_to(ROOT)),
        "execution_path": str(execution_path.relative_to(ROOT)),
        "verifier_path": str(verifier_path.relative_to(ROOT)),
        "status": "BLOCKED",
        "blockers": [],
    }
    if not execution_path.is_file() or not verifier_path.is_file():
        record["blockers"].append(
            "coupon-known-answer-attempt02 execution.json and verifier.json are required"
        )
        return record

    record["execution_sha256"] = sha256(execution_path)
    record["verifier_sha256"] = sha256(verifier_path)
    try:
        execution = read_json(execution_path)
        verifier = read_json(verifier_path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        record["blockers"].append(f"coupon records are unreadable: {error}")
        return record

    record["execution_status"] = execution.get("status")
    record["verifier_status"] = verifier.get("status")
    state = execution.get("container_state")
    record["container_state"] = state
    if execution.get("status") != "PASS":
        record["blockers"].append("coupon execution status is not PASS")
    if verifier.get("status") != "PASS":
        record["blockers"].append("coupon verifier status is not PASS")
    if verifier.get("execution_sha256") != record["execution_sha256"]:
        record["blockers"].append("coupon verifier is not bound to execution.json")
    if execution.get("patched_image_id") != EXPECTED_IMAGE_ID:
        record["blockers"].append("coupon execution used a different patched image")
    if execution.get("patched_binary_path") != EXPECTED_BINARY_PATH:
        record["blockers"].append("coupon execution used a different binary path")
    if execution.get("patched_binary_sha256") != EXPECTED_BINARY_SHA256:
        record["blockers"].append("coupon execution used a different patched binary")
    if execution.get("numerical_output_equivalence") is not True:
        record["blockers"].append("coupon numerical-output equivalence did not pass")
    if execution.get("trace_alignment_pass") is not True:
        record["blockers"].append("coupon trace alignment did not pass")
    if not isinstance(state, dict):
        record["blockers"].append("coupon container state is missing")
    else:
        if state.get("Running") is not False:
            record["blockers"].append("coupon container is not confirmed stopped")
        if state.get("OOMKilled") is not False:
            record["blockers"].append("coupon container OOM status is not false")
        if state.get("ExitCode") != 0:
            record["blockers"].append("coupon container exit code is not zero")
    source_binding = verifier.get("source_binding")
    if not isinstance(source_binding, dict):
        record["blockers"].append("coupon verifier source binding is missing")
    else:
        if source_binding.get("patched_image_id") != EXPECTED_IMAGE_ID:
            record["blockers"].append("coupon verifier binds a different image")
        if source_binding.get("patched_binary_sha256") != EXPECTED_BINARY_SHA256:
            record["blockers"].append("coupon verifier binds a different binary")

    record["status"] = "PASS" if not record["blockers"] else "BLOCKED"
    return record


def build_gate_record() -> dict[str, Any]:
    record: dict[str, Any] = {
        "status": "BLOCKED",
        "build_result_path": str(BUILD_RESULT_PATH.relative_to(ROOT)),
        "build_manifest_path": str(BUILD_MANIFEST_PATH.relative_to(ROOT)),
        "blockers": [],
    }
    if not BUILD_RESULT_PATH.is_file() or not BUILD_MANIFEST_PATH.is_file():
        record["blockers"].append("build-attempt02 records are missing")
        return record
    record["build_result_sha256"] = sha256(BUILD_RESULT_PATH)
    record["build_manifest_sha256"] = sha256(BUILD_MANIFEST_PATH)
    try:
        result = read_json(BUILD_RESULT_PATH)
        manifest = read_json(BUILD_MANIFEST_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        record["blockers"].append(f"build records are unreadable: {error}")
        return record
    record["image_id"] = result.get("image_id")
    record["binary_path"] = result.get("patched_binary_path")
    record["binary_sha256"] = result.get("patched_binary_sha256")
    if result.get("exit_code") != 0 or result.get("timed_out") is not False:
        record["blockers"].append("build-attempt02 did not finish successfully")
    if result.get("image_id") != EXPECTED_IMAGE_ID:
        record["blockers"].append("build-attempt02 image ID does not match the pin")
    if result.get("base_image_id") != EXPECTED_BASE_IMAGE_ID:
        record["blockers"].append("build-attempt02 base image does not match the pin")
    if result.get("patched_binary_path") != EXPECTED_BINARY_PATH:
        record["blockers"].append("build-attempt02 binary path does not match the pin")
    if result.get("patched_binary_sha256") != EXPECTED_BINARY_SHA256:
        record["blockers"].append("build-attempt02 binary hash does not match the pin")
    if manifest.get("patched_binary_sha256") != EXPECTED_BINARY_SHA256:
        record["blockers"].append("build manifest binary hash does not match the pin")
    if result.get("unpatched_2_23_binary_sha256") != EXPECTED_UPSTREAM_BINARY_SHA256:
        record["blockers"].append("upstream 2.23 binary hash does not match the pin")
    record["status"] = "PASS" if not record["blockers"] else "BLOCKED"
    return record


def verify_frozen_inputs(folder: Path) -> tuple[dict[str, str], dict[str, Any]]:
    binding_bytes = INPUT_BINDING_PATH.read_bytes()
    binding_sha = hashlib.sha256(binding_bytes).hexdigest()
    if binding_sha != EXPECTED_BINDING_SHA256:
        raise ValueError("attempt03 input-binding record differs from its pinned hash")
    binding = json.loads(binding_bytes)
    pins = binding.get("frozen_artifacts_sha256")
    if not isinstance(pins, dict) or len(pins) != 44:
        raise ValueError("input binding must contain exactly 44 frozen artifacts")
    if binding.get("attempt03_path") != str(SOURCE_ATTEMPT03.relative_to(ROOT)):
        raise ValueError("input binding names a different attempt03 source directory")

    freeze_path = SOURCE_ATTEMPT03 / "force-freeze.json"
    freeze = read_json(freeze_path)
    if sha256(freeze_path) != binding.get("force_freeze_sha256"):
        raise ValueError("attempt03 force-freeze record differs from its input binding")
    if freeze.get("artifacts_sha256") != pins:
        raise ValueError("attempt03 force-freeze record disagrees with the 44-input binding")
    freeze_sha = sha256(freeze_path)
    readiness_path = SOURCE_ATTEMPT03 / "independent-readiness.json"
    readiness = read_json(readiness_path)
    if (
        readiness.get("ready_for_bounded_dynamic_diagnostic") is not True
        or readiness.get("freeze_sha256") != freeze_sha
        or sha256(readiness_path) != binding.get("readiness_sha256")
    ):
        raise ValueError("attempt03 readiness record is not bound to its force freeze")
    input_freeze_path = folder / "input-freeze.json"
    input_freeze_sha = sha256(input_freeze_path)
    if (
        binding.get("input_freeze_sha256") != pins.get("input-freeze.json")
        or input_freeze_sha != binding.get("input_freeze_sha256")
    ):
        raise ValueError("input-freeze.json differs from the bound input-freeze hash")

    copy_manifest_path = folder / "input-copy-manifest.json"
    copy_manifest = read_json(copy_manifest_path)
    if copy_manifest.get("source_binding_sha256") != binding_sha:
        raise ValueError("input-copy manifest binds a different source binding")
    if copy_manifest.get("inputs_sha256") != dict(sorted(pins.items())):
        raise ValueError("input-copy manifest does not list the 44 bound hashes")
    if copy_manifest.get("source_force_freeze_sha256") != binding.get(
        "force_freeze_sha256"
    ):
        raise ValueError("input-copy manifest binds a different force freeze")
    if copy_manifest.get("source_readiness_sha256") != binding.get("readiness_sha256"):
        raise ValueError("input-copy manifest binds a different readiness record")
    if copy_manifest.get("input_freeze_sha256") != binding.get("input_freeze_sha256"):
        raise ValueError("input-copy manifest binds a different input freeze")

    input_hashes: dict[str, str] = {}
    mismatches = []
    for name, expected in sorted(pins.items()):
        source_path = SOURCE_ATTEMPT03 / name
        copy_path = folder / name
        if not source_path.is_file() or not copy_path.is_file():
            mismatches.append(name)
            continue
        source_hash = sha256(source_path)
        copy_hash = sha256(copy_path)
        if source_hash != expected or copy_hash != expected:
            mismatches.append(name)
        input_hashes[name] = copy_hash
    if mismatches:
        raise ValueError(f"frozen attempt03 input hash mismatch: {mismatches}")

    source_execution_path = SOURCE_ATTEMPT03 / "execution.json"
    if sha256(source_execution_path) != binding.get("execution_sha256"):
        raise ValueError("attempt03 execution record differs from its input binding")
    for name, expected in binding.get("outputs_sha256", {}).items():
        source_output = SOURCE_ATTEMPT03 / name
        if not source_output.is_file() or sha256(source_output) != expected:
            raise ValueError(f"attempt03 source output hash mismatch: {name}")

    monitor_source = ROOT / "fea/wood_joint_current_transient_launch.py"
    expected_monitor_source = pins.get("incremental-monitor.py.snapshot")
    if expected_monitor_source is None or sha256(monitor_source) != expected_monitor_source:
        raise ValueError("runtime motion monitor differs from its frozen snapshot")
    freeze_data = json.loads(freeze_path.read_text())
    manual_path = ROOT / freeze_data["manual"]["local_path"]
    if sha256(manual_path) != freeze_data["manual"]["sha256"]:
        raise ValueError("pinned CalculiX 2.23 manual hash mismatch")

    return input_hashes, {
        "binding_path": str(INPUT_BINDING_PATH.relative_to(ROOT)),
        "binding_sha256": binding_sha,
        "source_execution_sha256": binding["execution_sha256"],
        "source_force_freeze_sha256": freeze_sha,
        "source_readiness_sha256": sha256(readiness_path),
        "input_freeze_sha256": input_freeze_sha,
        "readiness_sha256": sha256(readiness_path),
        "input_copy_manifest_sha256": sha256(copy_manifest_path),
        "runtime_monitor_source_path": str(monitor_source.relative_to(ROOT)),
        "runtime_monitor_source_sha256": sha256(monitor_source),
        "manual_path": str(manual_path.relative_to(ROOT)),
        "manual_sha256": sha256(manual_path),
    }


def validate_empty_outputs(folder: Path) -> None:
    if (folder / "execution.json").exists() or (folder / "execution.json.tmp").exists():
        raise FileExistsError("preserve an existing execution record")
    if (folder / "launch-gate.json").exists() or (folder / "launch-gate.json.tmp").exists():
        raise FileExistsError("preserve an existing launch-gate record")
    copy_manifest = read_json(folder / "input-copy-manifest.json")
    expected_files = set(copy_manifest.get("inputs_sha256", {})) | {
        "REPLAY.md",
        "attempt04-runner.py",
        "input-copy-manifest.json",
    }
    observed_files = {path.name for path in folder.iterdir() if path.is_file()}
    unexpected = sorted(observed_files - expected_files)
    missing = sorted(expected_files - observed_files)
    if unexpected or missing:
        raise FileExistsError(
            f"replay folder contents differ from preparation: "
            f"unexpected={unexpected}, missing={missing}"
        )
    directories = [path.name for path in folder.iterdir() if path.is_dir()]
    if directories:
        raise FileExistsError(f"unexpected replay subdirectories: {directories}")
    for name in OUTPUT_NAMES:
        if (folder / name).exists():
            raise FileExistsError(f"native output already exists: {name}")


def inspect_container(name: str) -> dict[str, Any]:
    output = subprocess.check_output(["docker", "inspect", name], text=True)
    return json.loads(output)[0]["State"]


def inspect_image(image_id: str) -> str:
    return subprocess.check_output(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image_id],
        text=True,
    ).strip()


def verify_binary(image_id: str) -> dict[str, Any]:
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        image_id,
        "sha256sum",
        EXPECTED_BINARY_PATH,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    digest = result.stdout.split()[0] if result.returncode == 0 and result.stdout else None
    return {
        "command": command,
        "docker_cli_returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "observed_binary_sha256": digest,
        "pass": result.returncode == 0 and digest == EXPECTED_BINARY_SHA256,
    }


def run(folder: Path) -> dict[str, Any]:
    folder = folder.resolve()
    if folder != Path(__file__).resolve().parent:
        raise ValueError("runner only operates on its own replay-attempt01 directory")

    validate_empty_outputs(folder)
    gate: dict[str, Any] = {
        "schema": "calculix_attempt04_diagnostic_replay_launch_gate/v1",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BLOCKED",
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "blockers": [],
    }
    gate["coupon_known_answer"] = coupon_gate_record()
    gate["build"] = build_gate_record()
    try:
        input_hashes, provenance = verify_frozen_inputs(folder)
        gate["input_verification"] = {
            "status": "PASS",
            "count": len(input_hashes),
            "inputs_sha256": input_hashes,
            "provenance": provenance,
        }
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        input_hashes = {}
        provenance = {}
        gate["input_verification"] = {"status": "BLOCKED", "error": str(error)}
        gate["blockers"].append(f"frozen input verification failed: {error}")
    for label in ("coupon_known_answer", "build"):
        if gate[label]["status"] != "PASS":
            gate["blockers"].extend(
                f"{label}: {item}" for item in gate[label].get("blockers", [])
            )
    if gate["input_verification"]["status"] != "PASS":
        gate["blockers"].append("frozen input verification did not pass")
    if gate["blockers"]:
        save_json(folder, "launch-gate.json", gate)
        raise RuntimeError(f"launch blocked; see {folder / 'launch-gate.json'}")

    try:
        image_id = inspect_image(EXPECTED_IMAGE_ID)
        gate["actual_image_id"] = image_id
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        gate["blockers"].append(f"diagnostic image inspection failed: {error}")
        gate["image_inspection_error"] = repr(error)
        save_json(folder, "launch-gate.json", gate)
        raise RuntimeError(f"launch blocked; see {folder / 'launch-gate.json'}") from error
    if image_id != EXPECTED_IMAGE_ID:
        gate["blockers"].append("local diagnostic image ID does not match the pin")
    try:
        first_solver_check = active_native_processes()
        gate["initial_active_solver_check"] = first_solver_check
    except (OSError, subprocess.SubprocessError, RuntimeError) as error:
        gate["blockers"].append(f"initial active-solver scan failed: {error}")
        gate["initial_active_solver_check_error"] = repr(error)
        save_json(folder, "launch-gate.json", gate)
        raise RuntimeError(f"launch blocked; see {folder / 'launch-gate.json'}") from error
    if not first_solver_check["zero_active_solver"]:
        gate["blockers"].append("an active native solver is present")
    if gate["blockers"]:
        save_json(folder, "launch-gate.json", gate)
        raise RuntimeError(f"launch blocked; see {folder / 'launch-gate.json'}")

    try:
        binary_check = verify_binary(EXPECTED_IMAGE_ID)
        gate["binary_check"] = binary_check
    except (OSError, subprocess.SubprocessError) as error:
        gate["blockers"].append(f"diagnostic binary probe failed: {error}")
        gate["binary_check_error"] = repr(error)
        save_json(folder, "launch-gate.json", gate)
        raise RuntimeError(f"launch blocked; see {folder / 'launch-gate.json'}") from error
    if not binary_check["pass"]:
        gate["blockers"].append("diagnostic binary hash check did not pass")
    try:
        final_solver_check = active_native_processes()
        gate["prelaunch_active_solver_check"] = final_solver_check
    except (OSError, subprocess.SubprocessError, RuntimeError) as error:
        gate["blockers"].append(f"prelaunch active-solver scan failed: {error}")
        gate["prelaunch_active_solver_check_error"] = repr(error)
        save_json(folder, "launch-gate.json", gate)
        raise RuntimeError(f"launch blocked; see {folder / 'launch-gate.json'}") from error
    if not final_solver_check["zero_active_solver"]:
        gate["blockers"].append("an active native solver appeared before launch")
    gate["status"] = "PASS" if not gate["blockers"] else "BLOCKED"
    gate["launch_authorized_by_runner_gates"] = gate["status"] == "PASS"
    save_json(folder, "launch-gate.json", gate)
    if gate["status"] != "PASS":
        raise RuntimeError(f"launch blocked; see {folder / 'launch-gate.json'}")

    freeze = read_json(SOURCE_ATTEMPT03 / "force-freeze.json")
    bounds = freeze["resource_bounds"]
    container_name = "wj-at04diag-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    command = [
        "docker",
        "run",
        "--name",
        container_name,
        "--network",
        "none",
        "--cpus",
        str(bounds["cpus"]),
        "--memory",
        f"{bounds['memory_gib']}g",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--env",
        "OMP_NUM_THREADS=2",
        "--env",
        "CCX_NPROC_EQUATION_SOLVER=2",
        "--mount",
        f"type=bind,src={folder},dst=/work",
        "--workdir",
        "/work",
        EXPECTED_IMAGE_ID,
        EXPECTED_BINARY_PATH,
        "-i",
        "pilot",
    ]
    runner_path = Path(__file__).resolve()
    runner_sha = sha256(runner_path)
    started_monotonic = time.monotonic()
    last_progress_monotonic = started_monotonic
    previous_rows: list[dict[str, Any]] = []
    monitor = IncrementalMonitor(freeze)
    record: dict[str, Any] = {
        "schema": "calculix_attempt04_diagnostic_replay_execution/v1",
        "status": "starting",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "container_name": container_name,
        "attempt03_input_binding_sha256": provenance["binding_sha256"],
        "source_execution_sha256": provenance["source_execution_sha256"],
        "source_force_freeze_sha256": provenance["source_force_freeze_sha256"],
        "input_hashes_before_launch": input_hashes,
        "input_count": len(input_hashes),
        "input_copy_manifest_sha256": provenance["input_copy_manifest_sha256"],
        "runner_path": str(runner_path.relative_to(ROOT)),
        "runner_sha256": runner_sha,
        "launch_gate_path": str((folder / "launch-gate.json").relative_to(ROOT)),
        "launch_gate_sha256": sha256(folder / "launch-gate.json"),
        "coupon_known_answer_gate": gate["coupon_known_answer"],
        "coupon_execution_sha256": gate["coupon_known_answer"]["execution_sha256"],
        "coupon_verifier_sha256": gate["coupon_known_answer"]["verifier_sha256"],
        "build_result_sha256": gate["build"]["build_result_sha256"],
        "build_manifest_sha256": gate["build"]["build_manifest_sha256"],
        "solver_image_id": image_id,
        "solver_binary_path": EXPECTED_BINARY_PATH,
        "solver_binary_sha256": binary_check["observed_binary_sha256"],
        "binary_probe": binary_check,
        "initial_active_solver_check": gate["initial_active_solver_check"],
        "prelaunch_active_solver_check": final_solver_check,
        "monitor_runtime_source_sha256": provenance["runtime_monitor_source_sha256"],
        "manual_sha256": provenance["manual_sha256"],
        "limits": {
            "cpus": bounds["cpus"],
            "memory_gib": bounds["memory_gib"],
            "wallclock_seconds": bounds["wallclock_seconds"],
            "no_accepted_increment_or_monitor_progress_seconds": bounds[
                "no_accepted_state_seconds"
            ],
            "pilot_cel_soft_limit_bytes": freeze["watchdog_semantics"][
                "pilot_cel_size_guard_bytes"
            ],
            "stdout_soft_limit_bytes": STDOUT_SOFT_LIMIT_BYTES,
            "watchdog_poll_seconds": POLL_SECONDS,
        },
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "accepted_states": [],
        "observations": [],
        "last_cvg_row": None,
        "stop_reason": None,
        "docker_cli_returncode": None,
        "container_exit_code": None,
        "container_oom_killed": None,
    }

    def request_stop(reason: str) -> None:
        if record["stop_reason"] is None:
            record["stop_reason"] = reason
            record["runner_stop_request_reason"] = reason
            record["status"] = "stop_requested"
            record["stop_requested_utc"] = datetime.now(timezone.utc).isoformat()
            save_json(folder, "execution.json", record)
        result = subprocess.run(
            ["docker", "kill", container_name], capture_output=True, text=True
        )
        record["docker_kill"] = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    process: subprocess.Popen[bytes] | None = None
    try:
        save_json(folder, "execution.json", record)
        with (folder / "pilot.stdout").open("xb") as stdout:
            process = subprocess.Popen(command, stdout=stdout, stderr=subprocess.STDOUT)
            record["status"] = "running"
            record["container_launch_requested_utc"] = datetime.now(timezone.utc).isoformat()
            save_json(folder, "execution.json", record)
            while process.poll() is None:
                before_observations = len(monitor.results)
                record["observations"] = monitor.poll(folder / "pilot.dat")
                current_rows = accepted_rows(folder / "pilot.sta")
                if current_rows[: len(previous_rows)] != previous_rows:
                    raise ValueError("accepted .sta history changed or was truncated")
                if len(current_rows) > len(previous_rows):
                    record["accepted_states"].extend(
                        current_rows[len(previous_rows) :]
                    )
                    previous_rows = current_rows
                    last_progress_monotonic = time.monotonic()
                if len(monitor.results) > before_observations:
                    record["latest_monitor_observation"] = monitor.results[-1]
                    last_progress_monotonic = time.monotonic()
                record["last_cvg_row"] = last_cvg_row(folder / "pilot.cvg")
                elapsed = time.monotonic() - started_monotonic
                record["elapsed_seconds"] = elapsed

                if any(item["stop_reasons"] for item in record["observations"]):
                    request_stop("sampled_motion_limit")
                    break
                cel_path = folder / "pilot.cel"
                if (
                    cel_path.exists()
                    and cel_path.stat().st_size
                    > record["limits"]["pilot_cel_soft_limit_bytes"]
                ):
                    request_stop("sampled_pilot_cel_soft_limit")
                    break
                stdout_path = folder / "pilot.stdout"
                if (
                    stdout_path.exists()
                    and stdout_path.stat().st_size > STDOUT_SOFT_LIMIT_BYTES
                ):
                    request_stop("sampled_stdout_soft_limit")
                    break
                if (
                    time.monotonic() - last_progress_monotonic
                    > bounds["no_accepted_state_seconds"]
                ):
                    request_stop("no_accepted_increment_or_monitor_progress_timeout")
                    break
                if elapsed > bounds["wallclock_seconds"]:
                    request_stop("bounded_wallclock_timeout")
                    break
                save_json(folder, "execution.json", record)
                time.sleep(POLL_SECONDS)
    except BaseException as error:
        record["runner_error"] = repr(error)
        if record["stop_reason"] is None:
            record["stop_reason"] = "runner_error_or_interruption"
            record["runner_stop_request_reason"] = "runner_error_or_interruption"
            record["stop_requested_utc"] = datetime.now(timezone.utc).isoformat()
        record["status"] = "runner_error"
        if isinstance(error, KeyboardInterrupt):
            record["interrupted"] = True
        if process is not None and process.poll() is None:
            result = subprocess.run(
                ["docker", "kill", container_name], capture_output=True, text=True
            )
            record["docker_kill"] = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        save_json(folder, "execution.json", record)
    finally:
        if process is not None and process.poll() is None:
            result = subprocess.run(
                ["docker", "kill", container_name], capture_output=True, text=True
            )
            record.setdefault(
                "docker_kill",
                {
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )
        if process is not None:
            try:
                record["docker_cli_returncode"] = process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                process.terminate()
                record["docker_cli_terminated"] = True
                record["docker_cli_returncode"] = process.wait(timeout=10)

    try:
        state = inspect_container(container_name)
    except subprocess.CalledProcessError as error:
        record["container_state_inspect_error"] = error.output
        record["container_state_confirmed"] = False
        state = None
    if state is not None and state.get("Running"):
        result = subprocess.run(
            ["docker", "kill", container_name], capture_output=True, text=True
        )
        record["terminal_docker_kill"] = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        try:
            state = inspect_container(container_name)
        except subprocess.CalledProcessError as error:
            record["container_state_inspect_error"] = error.output
            record["container_state_confirmed"] = False
            state = None

    if state is not None:
        record["container_state"] = state
        record["container_state_confirmed"] = state.get("Running") is False
        record["container_exit_code"] = state.get("ExitCode")
        record["container_oom_killed"] = state.get("OOMKilled")
        record["container_error"] = state.get("Error")
        if state.get("Running"):
            terminal_reason = "container_still_running"
            record["container_terminal_reason"] = terminal_reason
            record["stop_reason"] = record.get("stop_reason") or "container_still_running"
            record["status"] = "terminal_state_unconfirmed"
        elif state.get("OOMKilled"):
            terminal_reason = "container_oom_killed"
            record["container_terminal_reason"] = terminal_reason
            record["stop_reason"] = record.get("stop_reason") or terminal_reason
            record["status"] = "container_oom_killed"
        elif record.get("stop_reason") is not None:
            terminal_reason = (
                f"container_exit_{state.get('ExitCode')}"
                if state.get("ExitCode") != 0
                else "container_exited_0_after_stop_request"
            )
            record["container_terminal_reason"] = terminal_reason
            record["status"] = "runner_stopped_container"
        elif state.get("ExitCode") == 0:
            terminal_reason = "container_exited_normally"
            record["container_terminal_reason"] = terminal_reason
            record["stop_reason"] = terminal_reason
            record["status"] = "container_exited"
        elif state.get("ExitCode") == 137:
            terminal_reason = "unattributed_container_exit_137"
            record["container_terminal_reason"] = terminal_reason
            record["stop_reason"] = terminal_reason
            record["status"] = "container_exited_nonzero"
        else:
            terminal_reason = f"container_exit_{state.get('ExitCode')}"
            record["container_terminal_reason"] = terminal_reason
            record["stop_reason"] = terminal_reason
            record["status"] = "container_exited_nonzero"
    elif record.get("status") == "running":
        record["status"] = "container_state_unconfirmed"

    record["observations"] = monitor.poll(folder / "pilot.dat")
    final_rows = accepted_rows(folder / "pilot.sta")
    if final_rows[: len(previous_rows)] != previous_rows:
        record["terminal_sta_history_changed"] = True
    record["accepted_states"] = final_rows
    record["last_cvg_row"] = last_cvg_row(folder / "pilot.cvg")
    record["trace_audit"] = trace_audit(folder)
    record["elapsed_seconds"] = time.monotonic() - started_monotonic
    record["ended_utc"] = datetime.now(timezone.utc).isoformat()
    record["input_hashes_after_run"] = {
        name: sha256(folder / name) for name in sorted(input_hashes)
    }
    record["frozen_inputs_unchanged"] = (
        record["input_hashes_after_run"] == record["input_hashes_before_launch"]
    )
    record["outputs"] = output_inventory(folder, set(input_hashes))
    record["outputs_sha256"] = {
        name: item["sha256"]
        for name, item in record["outputs"].items()
        if item["exists"]
    }
    record["actual_container_termination"] = {
        "docker_cli_returncode": record.get("docker_cli_returncode"),
        "container_state_confirmed": record.get("container_state_confirmed", False),
        "container_exit_code": record.get("container_exit_code"),
        "container_oom_killed": record.get("container_oom_killed"),
        "container_error": record.get("container_error"),
        "runner_stop_request_reason": record.get("runner_stop_request_reason"),
        "container_terminal_reason": record.get("container_terminal_reason"),
        "reported_stop_reason": record.get("stop_reason"),
    }
    save_json(folder, "execution.json", record)
    return {
        "status": record["status"],
        "stop_reason": record["stop_reason"],
        "docker_cli_returncode": record.get("docker_cli_returncode"),
        "container_exit_code": record.get("container_exit_code"),
        "container_oom_killed": record.get("container_oom_killed"),
        "accepted_states": len(final_rows),
        "last_cvg_row": record["last_cvg_row"],
        "trace_audit": record["trace_audit"],
        "elapsed_seconds": record["elapsed_seconds"],
        "frozen_inputs_unchanged": record["frozen_inputs_unchanged"],
    }


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "run":
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} run <replay-attempt01-directory>")
    print(json.dumps(run(Path(sys.argv[2])), indent=2))
