"""Serialized, bounded parent launch for an already frozen diagnostic deck."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

from fea.wood_joint_current_native_preflight import SOLVER_IMAGE, sha

BINARY_SHA = "6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b"


def run(directory, *, timeout_seconds=600):
    directory = Path(directory).resolve()
    freeze = json.loads((directory / "input-freeze.json").read_text())
    pins = freeze["artifacts_sha256"]
    if not all(sha(directory / name) == value for name, value in pins.items()):
        raise ValueError("frozen native inputs changed")
    if (directory / "execution.json").exists():
        raise FileExistsError("preserve each native attempt; select a new directory")
    # The parent must also coordinate all heavy jobs. This rejects overlapping
    # instances of this lane without stopping or taking ownership of any job.
    listing = subprocess.check_output(
        ["docker", "ps", "--format", "{{.Names}}"], text=True
    ).splitlines()
    if any(name.startswith("wj-current-native-") for name in listing):
        raise RuntimeError("a current native run is already active")
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
        "2",
        "--memory",
        "10g",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--env",
        "OMP_NUM_THREADS=1",
        "--mount",
        f"type=bind,src={directory},dst=/work",
        "--workdir",
        "/work",
        SOLVER_IMAGE,
        "/usr/bin/ccx",
        "-i",
        "preflight",
    ]
    (directory / "parent-launch.py.snapshot").write_bytes(Path(__file__).read_bytes())
    record = {
        "schema": "wood_joint_current_native_execution/v1",
        "status": "running",
        "command": command,
        "solver_image": SOLVER_IMAGE,
        "expected_binary_sha256": BINARY_SHA,
        "input_freeze_sha256": sha(directory / "input-freeze.json"),
        "parent_launcher_sha256": sha(Path(__file__)),
        "timeout_seconds": timeout_seconds,
        "mechanical_acceptance": False,
        "scope": freeze["step_scope"],
    }

    def save():
        (directory / "execution.json").write_text(json.dumps(record, indent=2) + "\n")

    save()
    started = time.monotonic()
    with (directory / "preflight.log").open("x") as output:
        try:
            result = subprocess.run(
                command,
                stdout=output,
                stderr=subprocess.STDOUT,
                timeout=timeout_seconds,
                check=False,
            )
            record.update(
                returncode=result.returncode,
                status="process_finished"
                if result.returncode == 0
                else "process_failed",
            )
        except subprocess.TimeoutExpired:
            subprocess.run(
                ["docker", "stop", "--time", "5", name],
                capture_output=True,
                check=False,
            )
            record.update(returncode=None, status="bounded_timeout")
    record["elapsed_seconds"] = time.monotonic() - started
    record["frozen_inputs_unchanged"] = all(
        sha(directory / filename) == value for filename, value in pins.items()
    )
    record["outputs_sha256"] = {}
    for path in directory.iterdir():
        if path.is_file() and path.name not in pins and path.name != "execution.json":
            # Matrix files can be large; hash incrementally.
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                    digest.update(block)
            record["outputs_sha256"][path.name] = digest.hexdigest()
    save()
    return {
        key: value
        for key, value in record.items()
        if key not in ("command", "outputs_sha256")
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    print(json.dumps(run(args.directory, timeout_seconds=args.timeout), indent=2))
