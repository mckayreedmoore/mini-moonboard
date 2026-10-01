"""Run the frozen attempt03 with terminal capture and bounded progress checks."""

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


ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fea.wood_joint_current_transient_launch import IncrementalMonitor


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
STA_ROW = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$")
CVG_ROW = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+.*$")


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def save_record(folder: Path, record: dict[str, Any]) -> None:
    temporary = folder / "execution.json.tmp"
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    os.replace(temporary, folder / "execution.json")


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


def last_cvg_row(path: Path) -> dict[str, int] | None:
    if not path.exists():
        return None
    raw = path.read_bytes()
    complete = raw[: raw.rfind(b"\n") + 1].decode("ascii", errors="replace")
    result = None
    for line in complete.splitlines():
        match = CVG_ROW.match(line)
        if match is None:
            continue
        step, increment, attempt, iteration, contact_elements = map(int, match.groups())
        result = {
            "step": step,
            "increment": increment,
            "attempt": attempt,
            "iteration": iteration,
            "contact_elements": contact_elements,
        }
    return result


def _inspect_container(name: str) -> dict[str, Any]:
    output = subprocess.check_output(["docker", "inspect", name], text=True)
    return json.loads(output)[0]["State"]


def run(folder: Path) -> dict[str, Any]:
    folder = folder.resolve()
    freeze_path = folder / "force-freeze.json"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    readiness_bytes = (folder / "independent-readiness.json").read_bytes()
    readiness = json.loads(readiness_bytes)
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    if (
        readiness.get("ready_for_bounded_dynamic_diagnostic") is not True
        or readiness.get("freeze_sha256") != freeze_sha
    ):
        raise ValueError("missing readiness audit bound to this force-freeze.json")
    pins = freeze["artifacts_sha256"]
    mismatches = [name for name, digest in pins.items() if sha256(folder / name) != digest]
    if mismatches:
        raise ValueError(f"frozen attempt03 artifacts changed: {mismatches}")
    monitor_source = ROOT / "fea/wood_joint_current_transient_launch.py"
    expected_monitor_source = pins.get("incremental-monitor.py.snapshot")
    if expected_monitor_source is None or sha256(monitor_source) != expected_monitor_source:
        raise ValueError("runtime motion monitor differs from its frozen snapshot")
    manual_path = ROOT / freeze["manual"]["local_path"]
    if sha256(manual_path) != freeze["manual"]["sha256"]:
        raise ValueError("pinned CalculiX 2.23 manual hash mismatch")
    if (folder / "execution.json").exists():
        raise FileExistsError("preserve existing execution record")
    if (folder / "execution.json.tmp").exists():
        raise FileExistsError("preserve existing temporary execution record")

    for name in OUTPUT_NAMES:
        if (folder / name).exists():
            raise FileExistsError(f"native output already exists: {name}")

    live = subprocess.check_output(
        ["docker", "ps", "--format", "{{.ID}} {{.Names}}"], text=True
    )
    active_native = []
    for line in live.splitlines():
        container_id, name = line.split(maxsplit=1)
        if name.startswith("wj-"):
            active_native.append({"container": name, "reason": "project_native_name"})
            continue
        process_list = subprocess.run(
            ["docker", "top", container_id, "-eo", "pid,comm,args"],
            capture_output=True,
            text=True,
        )
        if process_list.returncode != 0:
            raise RuntimeError(f"cannot inspect running container processes: {name}")
        if "ccx" in process_list.stdout.lower() or "calculix" in process_list.stdout.lower():
            active_native.append({"container": name, "reason": "solver_process"})
    if active_native:
        raise RuntimeError(f"another project native job is active: {active_native}")
    host_native = []
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            process_name = (process / "comm").read_text().strip()
        except (FileNotFoundError, PermissionError):
            continue
        if process_name.lower().startswith("ccx"):
            host_native.append({"pid": int(process.name), "comm": process_name})
    if host_native:
        raise RuntimeError(f"another host native solver is active: {host_native}")

    bounds = freeze["resource_bounds"]
    solver_check = subprocess.check_output(
        ["docker", "run", "--rm", "--network", "none", freeze["solver_image"],
         "sha256sum", freeze["solver_binary_path"]],
        text=True,
    ).split()[0]
    if solver_check != freeze["solver_binary_sha256"]:
        raise ValueError("pinned solver binary hash mismatch")

    container_name = "wj-external-force-cel-" + freeze_sha[:12]
    command = [
        "docker", "run", "--name", container_name, "--network", "none",
        "--cpus", str(bounds["cpus"]), "--memory", f"{bounds['memory_gib']}g",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "--env", "OMP_NUM_THREADS=2", "--env", "CCX_NPROC_EQUATION_SOLVER=2",
        "--mount", f"type=bind,src={folder},dst=/work", "--workdir", "/work",
        freeze["solver_image"], freeze["solver_binary_path"], "-i", "pilot",
    ]
    started_monotonic = time.monotonic()
    last_progress_monotonic = started_monotonic
    previous_rows: list[dict[str, Any]] = []
    monitor = IncrementalMonitor(freeze)
    record: dict[str, Any] = {
        "status": "running",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "container_name": container_name,
        "force_freeze_sha256": freeze_sha,
        "input_freeze_sha256": sha256(folder / "input-freeze.json"),
        "readiness_sha256": hashlib.sha256(readiness_bytes).hexdigest(),
        "solver_binary_sha256": solver_check,
        "monitor_runtime_source_sha256": sha256(monitor_source),
        "manual_sha256": sha256(manual_path),
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "accepted_states": [],
        "observations": [],
        "last_cvg_row": None,
        "stop_reason": None,
    }

    def request_stop(reason: str) -> None:
        if record["stop_reason"] is None:
            record["status"] = reason
            record["stop_reason"] = reason
            record["stop_requested_utc"] = datetime.now(timezone.utc).isoformat()
            save_record(folder, record)
        subprocess.run(["docker", "kill", container_name], capture_output=True, check=False)

    process: subprocess.Popen[bytes] | None = None
    try:
        save_record(folder, record)
        with (folder / "pilot.stdout").open("xb") as stdout:
            process = subprocess.Popen(command, stdout=stdout, stderr=subprocess.STDOUT)
            while process.poll() is None:
                before_observations = len(monitor.results)
                record["observations"] = monitor.poll(folder / "pilot.dat")
                current_rows = accepted_rows(folder / "pilot.sta")
                if current_rows[: len(previous_rows)] != previous_rows:
                    raise ValueError("accepted .sta history changed or was truncated")
                if len(current_rows) > len(previous_rows):
                    added_rows = current_rows[len(previous_rows) :]
                    record["accepted_states"].extend(added_rows)
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
                    > freeze["watchdog_semantics"]["pilot_cel_size_guard_bytes"]
                ):
                    request_stop("pilot_cel_size_bound")
                    break
                if (
                    time.monotonic() - last_progress_monotonic
                    > bounds["no_accepted_state_seconds"]
                ):
                    request_stop("no_accepted_or_monitor_progress_timeout")
                    break
                if elapsed > bounds["wallclock_seconds"]:
                    request_stop("bounded_wallclock_timeout")
                    break
                save_record(folder, record)
                time.sleep(2)
    except BaseException as error:
        record["runner_error"] = repr(error)
        request_stop("runner_error_or_interruption")
        if isinstance(error, KeyboardInterrupt):
            record["interrupted"] = True
    finally:
        if process is not None and process.poll() is None:
            subprocess.run(["docker", "kill", container_name], capture_output=True, check=False)
        if process is not None:
            try:
                record["returncode"] = process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                process.terminate()
                record["returncode"] = process.wait(timeout=10)

    try:
        state = _inspect_container(container_name)
    except subprocess.CalledProcessError as error:
        record["container_inspect_error"] = error.output
        save_record(folder, record)
        raise RuntimeError("could not confirm the native container's terminal state") from error
    if state.get("Running"):
        subprocess.run(["docker", "kill", container_name], capture_output=True, check=False)
        state = _inspect_container(container_name)
    if state.get("Running"):
        record["container_state"] = state
        save_record(folder, record)
        raise RuntimeError("native container is still running; refusing to hash outputs")

    record["container_state"] = state
    if record["status"] == "running":
        record["status"] = "process_finished" if record.get("returncode") == 0 else "process_failed"
    record["observations"] = monitor.poll(folder / "pilot.dat")
    final_rows = accepted_rows(folder / "pilot.sta")
    if final_rows[: len(previous_rows)] != previous_rows:
        record["terminal_sta_history_changed"] = True
    record["accepted_states"] = final_rows
    record["last_cvg_row"] = last_cvg_row(folder / "pilot.cvg")
    record["elapsed_seconds"] = time.monotonic() - started_monotonic
    record["ended_utc"] = datetime.now(timezone.utc).isoformat()
    record["frozen_inputs_unchanged"] = all(
        sha256(folder / name) == digest for name, digest in pins.items()
    )
    record["outputs_sha256"] = {
        name: sha256(folder / name)
        for name in OUTPUT_NAMES
        if (folder / name).is_file() and name not in pins
    }
    save_record(folder, record)
    return {
        "status": record["status"],
        "stop_reason": record["stop_reason"],
        "returncode": record.get("returncode"),
        "accepted_states": len(record["accepted_states"]),
        "iterations_at_termination": record["last_cvg_row"],
        "elapsed_seconds": record["elapsed_seconds"],
        "frozen_inputs_unchanged": record["frozen_inputs_unchanged"],
    }


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "run":
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} run <attempt-directory>")
    print(json.dumps(run(Path(sys.argv[2])), indent=2))
