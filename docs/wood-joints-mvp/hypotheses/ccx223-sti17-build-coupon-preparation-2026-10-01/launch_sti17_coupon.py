"""Parent-only STI17 coupon launcher with forced termination of the solver.

The preserved stock runner remains unchanged. This scoped launch kernel is
copied from its pinned source; only the timeout command and preflight scope
bindings differ. It shares the same verifier, ledger, lock and output writer.
No function in this file has been used to launch a native run.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from fea.wood_joint_reduced_native import LEDGER, digest, verify, write_json

sys.path.insert(0, str(HERE))
from prepare_sti17_coupon import EXPECTED_DECK_SHA256, make_model_record

LEGACY_PATH = ROOT / "fea/wood_joint_reduced_native.py"
LEGACY_SHA256 = "ff7a81bc604090a4791eb584f9998bc76a35be2ac3ebaed15be970291583ff61"
SCOPE = "free unit C3D20 native MATRIXSTORAGE known-answer export only"
BINARY_PATH = "/usr/local/bin/ccx-upstream-2.23-sti17"
FREEZE_DIR = HERE / "sti17-free-c3d20-coupon-freeze-attempt01"
PREPARER_PATH = HERE / "prepare_sti17_coupon.py"
TIMEOUT_CONTROL = {
    "path": "/usr/bin/timeout",
    "sha256": "4fccd5b0192653a2446b745d5385ea547b78e466150e07ade9e2caff2b7f4e08",
}


def verify_launcher_bindings(directory):
    """Refuse an unpinned launcher or a widened/different freeze before Docker."""
    directory = Path(directory).resolve()
    if directory != FREEZE_DIR.resolve():
        raise ValueError("Coupon launcher requires its canonical attempt directory")
    if digest(LEGACY_PATH) != LEGACY_SHA256:
        raise ValueError("Preserved native runner source changed")
    packet = verify(directory)
    sources = packet["source_sha256"]
    launcher_relative = str(Path(__file__).resolve().relative_to(ROOT))
    if (
        sources.get("fea/wood_joint_reduced_native.py") != LEGACY_SHA256
        or sources.get(launcher_relative) != digest(Path(__file__))
        or sources.get(str(PREPARER_PATH.relative_to(ROOT))) != digest(PREPARER_PATH)
    ):
        raise ValueError("Coupon freeze does not bind both exact launch sources")
    profile = packet["solver_profile"]
    if (
        packet.get("scope") != SCOPE
        or packet.get("schema") != "wood_joint_reduced_native_freeze/v1"
        or packet.get("candidate") != "compact-floor-flush-wood-joints-development"
        or packet.get("geometry_revision_id")
        != "led-clearance-2x6-runner-seated-blocks-v1"
        or packet.get("candidate_export_authorized") is not False
        or packet.get("mechanical_acceptance") is not False
        or profile.get("version") != "2.23-sti17"
        or profile.get("binary_path") != BINARY_PATH
        or profile.get("candidate_export_authorized") is not False
        or profile.get("mechanical_acceptance") is not False
    ):
        raise ValueError("Hard-stop launcher is limited to the isolated STI17 coupon")
    if digest(directory / "model.inp") != EXPECTED_DECK_SHA256 or json.loads(
        (directory / "model.json").read_text()
    ) != make_model_record(EXPECTED_DECK_SHA256):
        raise ValueError("Coupon launcher requires the exact free-C3D20 deck and model")
    return packet


# ponytail: retain the pinned legacy entrypoint for historical live source pins.
# This scoped copy shares its ledger/verifier; recheck the copy on any legacy change.
def launch(directory, run_id, review_path):
    """Coordinator call only, after checking the concrete independent review."""
    timeout_seconds, memory = 60, "2g"
    verify_launcher_bindings(directory)
    directory = Path(directory).resolve()
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}", run_id):
        raise ValueError("Invalid native run ID")
    if timeout_seconds <= 0:
        raise ValueError("Native timeout must be positive")
    packet = verify(directory)
    freeze_digest = digest(directory / "freeze.json")
    review_path = Path(review_path).resolve()
    review_bytes = review_path.read_bytes()
    review_sha256 = hashlib.sha256(review_bytes).hexdigest()
    review = json.loads(review_bytes)
    if (
        review.get("input_freeze_sha256") != freeze_digest
        or review.get("ready_for_scoped_native_run") is not True
    ):
        raise ValueError("Review does not approve this exact freeze for its scoped run")
    profile = packet["solver_profile"]
    docker = ["docker", "--context", "default"]
    inspected = subprocess.run(
        docker + ["image", "inspect", profile["image_id"], "--format", "{{.Id}}"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if inspected.stdout.strip() != profile["image_id"]:
        raise ValueError("Native image identity mismatch")
    binary = subprocess.run(
        docker
        + [
            "run",
            "--rm",
            "--network=none",
            "--cpus=1",
            "--memory=256m",
            "--memory-swap=256m",
            profile["image_id"],
            "sha256sum",
            profile["binary_path"],
            TIMEOUT_CONTROL["path"],
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    hashes = [line.split() for line in binary.stdout.splitlines()]
    if hashes != [
        [profile["binary_sha256"], profile["binary_path"]],
        [TIMEOUT_CONTROL["sha256"], TIMEOUT_CONTROL["path"]],
    ]:
        raise ValueError("Native binary or absolute timeout utility hash mismatch")
    container = "moonboard-" + run_id.lower()
    command = docker + [
        "run",
        "--rm",
        "--name",
        container,
        "--network=none",
        "--cpus=1",
        "--memory=" + memory,
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "-e",
        "OMP_NUM_THREADS=1",
        "--memory-swap=2g",
        "-v",
        f"{directory}:/output",
        "-v",
        f"{directory / 'model.inp'}:/output/model.inp:ro",
        "-w",
        "/output",
        profile["image_id"],
        TIMEOUT_CONTROL["path"],
        "--signal=KILL",
        str(timeout_seconds) + "s",
        profile["binary_path"],
        "-i",
        "model",
    ]
    # Existing repository policy requires one parent native slot across packets.
    with LEDGER.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ledger = json.loads(LEDGER.read_text())
        if ledger["slot"]["state"] != "idle":
            raise ValueError("Another native run owns the parent slot")
        if any(row["run_id"] == run_id for row in ledger["runs"]):
            raise ValueError("Native run ID was already registered; no reuse")
        if (directory / "execution.json").exists():
            raise ValueError("This attempt directory already has an execution record")
        packet = verify_launcher_bindings(directory)
        if digest(directory / "freeze.json") != freeze_digest:
            raise ValueError("Reviewed coupon freeze changed before reservation")
        if review_path.read_bytes() != review_bytes:
            raise ValueError("Independent coupon review changed before reservation")
        authorization = {
            "run_id": run_id,
            "scope": packet["scope"],
            "input_freeze_sha256": freeze_digest,
            "parent_readiness": True,
            "native_execution_authorized": True,
            "independent_review": str(review_path.relative_to(ROOT)),
            "independent_review_sha256": review_sha256,
            "owner_authority": "AGENTS.md resumed reviewed wood-joint native-analysis authorization",
            "owner_authority_sha256": digest(ROOT / "AGENTS.md"),
            "command": command,
            "timeout_control": TIMEOUT_CONTROL,
            "mechanical_acceptance": False,
        }
        write_json(directory / "authorization.json", authorization)
        row = {
            "run_id": run_id,
            "scope": packet["scope"],
            "attempt_directory": str(directory.relative_to(ROOT)),
            "input_freeze_sha256": freeze_digest,
            "max_launches": 1,
            "launches_consumed": 1,
            "state": "consumed_running",
            "parent_readiness": True,
            "native_execution_authorized": True,
            "authorization_sha256": digest(directory / "authorization.json"),
            "execution_record_sha256": None,
            "outcome": None,
        }
        ledger["runs"].append(row)
        ledger["slot"] = {"state": "running", "active_run_id": run_id}
        write_json(LEDGER, ledger)
        started = time.time()
        execution = {
            "run_id": run_id,
            "command": command,
            "timeout_control": TIMEOUT_CONTROL,
            "started_unix": started,
            "native_solve_executed": True,
            "mechanical_acceptance": False,
        }
        terminal = False
        try:
            with (
                (directory / "native.stdout").open("w") as out,
                (directory / "native.stderr").open("w") as err,
            ):
                result = subprocess.run(
                    command,
                    stdout=out,
                    stderr=err,
                    timeout=timeout_seconds + 30,
                    check=False,
                )
            execution["returncode"] = result.returncode
            check = subprocess.run(
                docker + ["ps", "-aq", "--filter", "name=^/" + container + "$"],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            if check.stdout.strip():
                raise RuntimeError(
                    "Docker client returned but the native container still exists"
                )
            terminal = True
        except BaseException as exc:
            execution["exception"] = f"{type(exc).__name__}: {exc}"
            try:
                subprocess.run(
                    docker + ["rm", "-f", container],
                    capture_output=True,
                    timeout=30,
                    check=False,
                )
                check = subprocess.run(
                    docker + ["ps", "-aq", "--filter", "name=^/" + container + "$"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,
                )
                terminal = not check.stdout.strip()
            except (subprocess.SubprocessError, OSError) as cleanup_error:
                execution["cleanup_exception"] = repr(cleanup_error)
            raise
        finally:
            execution.update(
                elapsed_seconds=time.time() - started,
                container_confirmed_terminal=terminal,
            )
            execution["outputs_sha256"] = {
                p.name: digest(p)
                for p in directory.iterdir()
                if p.is_file()
                and (p.name.startswith("model.") or p.name.startswith("native."))
            }
            write_json(directory / "execution.json", execution)
            row["state"] = (
                "consumed_terminal" if terminal else "consumed_cleanup_unconfirmed"
            )
            row["execution_record_sha256"] = digest(directory / "execution.json")
            row["outcome"] = "Native exit " + str(
                execution.get("returncode", execution.get("exception"))
            )
            ledger["slot"] = (
                {"state": "idle", "active_run_id": None}
                if terminal
                else {"state": "cleanup_unconfirmed", "active_run_id": run_id}
            )
            write_json(LEDGER, ledger)
    return execution
