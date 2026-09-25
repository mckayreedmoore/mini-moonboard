"""Parent-only bounded execution and printed-motion monitoring of a frozen pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import time
from pathlib import Path

from fea.wood_joint_current_native_launch import BINARY_SHA
from fea.wood_joint_current_native_preflight import SOLVER_IMAGE, sha

HEADER = re.compile(
    r"displacements \(vx,vy,vz\) for set PILOT_MONITOR and time\s+(\S+)"
)


def _lines_from(text, start):
    """Read only the rows consumed, without copying the remaining DAT history."""
    while start < len(text):
        end = text.find("\n", start)
        if end < 0:
            return
        yield text[start:end]
        start = end + 1


def observations(text, freeze):
    """Accept only complete, unique monitor-node blocks, including a partial tail."""
    # The solver can be in the middle of writing a numeric token during a poll.
    text = text[: text.rfind("\n") + 1]
    result = []
    expected = set(freeze["monitor_nodes"])
    for block in HEADER.finditer(text):
        rows = {}
        for line in _lines_from(text, block.end()):
            fields = line.split()
            if not fields and not rows:
                continue
            if len(fields) != 4 or not fields[0].isdigit():
                break
            node = int(fields[0])
            if node not in expected or node in rows:
                raise ValueError("unexpected or duplicate monitor node")
            rows[node] = tuple(float(x.replace("D", "E")) for x in fields[1:])
            if not all(math.isfinite(v) for v in rows[node]):
                raise ValueError("nonfinite native motion")
            if len(rows) == len(expected):
                break
        if set(rows) != expected:
            continue
        load_nodes = freeze["serialized_unit_load_nodes"]
        q = math.fsum(
            float(f) * rows[int(node)][axis]
            for node, row in load_nodes.items()
            for axis, f in enumerate(row["force_xyz_n"])
        )
        displacement = max(
            math.sqrt(sum(v * v for v in rows[int(n)])) for n in load_nodes
        )
        rotation = max(
            math.sqrt(sum(v * v for v in rows[n])) for n in freeze["rotation_nodes"]
        )
        reasons = []
        for value, key, label in (
            (abs(q), "sampled_travel_stop_mm", "relative_travel"),
            (
                displacement,
                "sampled_loaded_node_displacement_stop_mm",
                "loaded_node_motion",
            ),
            (
                rotation,
                "sampled_controller_rotation_stop_rad",
                "nut_controller_rotation",
            ),
        ):
            if value > freeze[key]:
                reasons.append(label)
        result.append(
            {
                "time_seconds": float(block.group(1).replace("D", "E")),
                "q_mm": q,
                "maximum_loaded_displacement_mm": displacement,
                "maximum_controller_rotation_rad": rotation,
                "stop_reasons": reasons,
            }
        )
    return result


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(directory, *, timeout_seconds=600, threads=1):
    if not isinstance(threads, int) or not 1 <= threads <= 4:
        raise ValueError("current pilot thread budget must be 1..4")
    directory = Path(directory).resolve()
    freeze = json.loads((directory / "input-freeze.json").read_text())
    if (
        freeze["schema"] != "wood_joint_current_transient/v1"
        or freeze["solver_image"] != SOLVER_IMAGE
    ):
        raise ValueError("not the frozen current transient")
    pins = freeze["artifacts_sha256"]
    if not all(sha(directory / name) == value for name, value in pins.items()):
        raise ValueError("frozen inputs changed")
    if (directory / "execution.json").exists():
        raise FileExistsError("preserve terminal and live attempts")
    live = subprocess.check_output(
        ["docker", "ps", "--format", "{{.Names}}"], text=True
    ).splitlines()
    if any(name.startswith("wj-current-native-") for name in live):
        raise RuntimeError("another current native job is running")
    # Hash the binary in the same immutable image before starting the heavy job.
    actual = subprocess.check_output(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            SOLVER_IMAGE,
            "sha256sum",
            "/usr/bin/ccx",
        ],
        text=True,
    ).split()[0]
    if actual != BINARY_SHA:
        raise ValueError("solver binary hash mismatch")
    name = "wj-current-native-" + directory.name
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        name,
        "--network",
        "none",
        "--cpus",
        str(max(2, threads)),
        "--memory",
        "10g",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--env",
        f"OMP_NUM_THREADS={threads}",
        "--env",
        f"CCX_NPROC_EQUATION_SOLVER={threads}",
        "--mount",
        f"type=bind,src={directory},dst=/work",
        "--workdir",
        "/work",
        SOLVER_IMAGE,
        "/usr/bin/ccx",
        "-i",
        "pilot",
    ]
    (directory / "parent-launch.py.snapshot").write_bytes(Path(__file__).read_bytes())
    record = {
        "schema": "wood_joint_current_transient_execution/v1",
        "status": "running",
        "command": command,
        "solver_binary_sha256": actual,
        "input_freeze_sha256": sha(directory / "input-freeze.json"),
        "timeout_seconds": timeout_seconds,
        "mechanical_acceptance": False,
        "observations": [],
        "scope": freeze["step_scope"],
    }

    def save():
        (directory / "execution.json").write_text(json.dumps(record, indent=2) + "\n")

    def stop(reason):
        record["status"] = reason
        subprocess.run(
            ["docker", "stop", "--time", "5", name], capture_output=True, check=False
        )

    save()
    started = time.monotonic()
    with (directory / "pilot.log").open("x") as output:
        process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT)
        try:
            while process.poll() is None:
                dat = directory / "pilot.dat"
                if dat.exists():
                    record["observations"] = observations(
                        dat.read_text(errors="replace"), freeze
                    )
                    if any(row["stop_reasons"] for row in record["observations"]):
                        stop("sampled_motion_limit")
                        break
                if time.monotonic() - started > timeout_seconds:
                    stop("bounded_timeout")
                    break
                save()
                time.sleep(2)
        except Exception as exc:  # noqa: BLE001 - stop the native job on any monitor failure
            record["monitor_error"] = repr(exc)
            stop("monitor_error")
        record["returncode"] = process.wait(timeout=30)
    if record["status"] == "running":
        record["status"] = (
            "process_finished" if record["returncode"] == 0 else "process_failed"
        )
    dat = directory / "pilot.dat"
    if dat.exists():
        try:
            record["observations"] = observations(
                dat.read_text(errors="replace"), freeze
            )
            if any(row["stop_reasons"] for row in record["observations"]):
                record["sampled_motion_limit_observed"] = True
        except ValueError as exc:
            record["final_monitor_error"] = repr(exc)
    record["elapsed_seconds"] = time.monotonic() - started
    record["frozen_inputs_unchanged"] = all(
        sha(directory / n) == h for n, h in pins.items()
    )
    record["outputs_sha256"] = {
        p.name: digest(p)
        for p in directory.iterdir()
        if p.is_file() and p.name not in pins and p.name != "execution.json"
    }
    save()
    return {k: v for k, v in record.items() if k not in ("outputs_sha256", "command")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()
    print(
        json.dumps(
            run(args.directory, timeout_seconds=args.timeout, threads=args.threads),
            indent=2,
        )
    )
