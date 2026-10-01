"""Parent-only frozen, serialized stock-2.23 static executions.

This runner controls invocation provenance, not mechanical acceptance. An
independent review binds to the freeze; the coordinator still owns readiness.
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

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.json"
PROFILE = ROOT / "fea/calculix_223/solver-profile.json"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def validate_numeric_fields(deck):
    """Reject overlong numeric data before the pinned F20.0 parser truncates it."""
    numeric = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][+-]?\d+)?")
    card = ""
    for number, line in enumerate(deck.splitlines(), 1):
        if line.startswith("*"):
            card = line.split(",")[0]
            continue
        for token in line.split(","):
            token = token.strip()
            if numeric.fullmatch(token) and len(token) > 20:
                raise ValueError(f"{card} line {number}: numeric field exceeds CalculiX F20.0 width: {token}")


def freeze(directory, structure, metadata, extra_sources=(), *, deck_text=None, active_bearings=None):
    """Retain the exact deck, model record and imported project Python sources."""
    from fea.horizontal_panel_frame import record_structure

    deck = structure.deck(active_bearings=active_bearings) if deck_text is None else deck_text
    validate_numeric_fields(deck)
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    paths = {PROFILE, Path(__file__).resolve(), *(Path(p).resolve() for p in extra_sources)}
    for module in list(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if filename:
            path = Path(filename).resolve()
            if path.suffix == ".py" and path.is_relative_to(ROOT):
                paths.add(path)
    sources = {}
    for path in sorted(paths):
        relative = str(path.relative_to(ROOT))
        content = path.read_bytes()
        snapshot = directory / "sources" / relative
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(content)
        sources[relative] = hashlib.sha256(content).hexdigest()
    (directory / "model.inp").write_text(deck)
    write_json(directory / "model.json", record_structure(structure, metadata, active_bearings))
    profile = json.loads(PROFILE.read_text())
    if digest(ROOT / profile["manual"]["local_path"]) != profile["manual"]["sha256"]:
        raise ValueError("Pinned solver manual changed")
    packet = {
        "schema": "wood_joint_reduced_native_freeze/v1",
        "scope": metadata["scope"], "candidate": metadata["candidate"],
        "geometry_revision_id": metadata["geometry_revision_id"],
        "solver_profile": profile, "source_sha256": sources,
        "files_sha256": {name: digest(directory / name) for name in ("model.inp", "model.json")},
        "native_solve_executed": False, "mechanical_acceptance": False,
    }
    write_json(directory / "freeze.json", packet)
    verify(directory)
    return packet


def verify(directory, *, check_live=True):
    directory = Path(directory).resolve()
    packet = json.loads((directory / "freeze.json").read_text())
    for name, expected in packet["files_sha256"].items():
        if digest(directory / name) != expected:
            raise ValueError("Frozen native input changed: " + name)
    for name, expected in packet["source_sha256"].items():
        if digest(directory / "sources" / name) != expected or (check_live and digest(ROOT / name) != expected):
            raise ValueError("Frozen or live implementation changed: " + name)
    profile = packet["solver_profile"]
    if digest(ROOT / profile["manual"]["local_path"]) != profile["manual"]["sha256"]:
        raise ValueError("Pinned solver manual changed")
    return packet


def launch(directory, run_id, review_path, *, timeout_seconds=240, memory="4g"):
    """Coordinator call only, after checking the concrete independent review."""
    directory = Path(directory).resolve()
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}", run_id):
        raise ValueError("Invalid native run ID")
    if timeout_seconds <= 0:
        raise ValueError("Native timeout must be positive")
    packet = verify(directory)
    freeze_digest = digest(directory / "freeze.json")
    review_path = Path(review_path).resolve()
    review = json.loads(review_path.read_text())
    if review.get("input_freeze_sha256") != freeze_digest or review.get("ready_for_scoped_native_run") is not True:
        raise ValueError("Review does not approve this exact freeze for its scoped run")
    profile = packet["solver_profile"]
    docker = ["docker", "--context", "default"]
    inspected = subprocess.run(docker + ["image", "inspect", profile["image_id"], "--format", "{{.Id}}"],
                               check=True, capture_output=True, text=True, timeout=30)
    if inspected.stdout.strip() != profile["image_id"]:
        raise ValueError("Native image identity mismatch")
    binary = subprocess.run(docker + ["run", "--rm", "--network=none", "--cpus=1", "--memory=256m",
        profile["image_id"], "sha256sum", profile["binary_path"]],
        check=True, capture_output=True, text=True, timeout=30)
    if binary.stdout.split()[0] != profile["binary_sha256"]:
        raise ValueError("Native binary hash mismatch")
    container = "moonboard-" + run_id.lower()
    command = docker + ["run", "--rm", "--name", container, "--network=none", "--cpus=1",
        "--memory=" + memory, "--user", f"{os.getuid()}:{os.getgid()}", "-e", "OMP_NUM_THREADS=1",
        "-v", f"{directory}:/output", "-w", "/output", profile["image_id"],
        "timeout", str(timeout_seconds) + "s", profile["binary_path"], "-i", "model"]
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
        verify(directory)
        authorization = {
            "run_id": run_id, "scope": packet["scope"],
            "input_freeze_sha256": freeze_digest, "parent_readiness": True,
            "native_execution_authorized": True,
            "independent_review": str(review_path.relative_to(ROOT)),
            "independent_review_sha256": digest(review_path),
            "owner_authority": "AGENTS.md resumed reviewed wood-joint native-analysis authorization",
            "owner_authority_sha256": digest(ROOT / "AGENTS.md"),
            "command": command, "mechanical_acceptance": False,
        }
        write_json(directory / "authorization.json", authorization)
        row = {
            "run_id": run_id, "scope": packet["scope"],
            "attempt_directory": str(directory.relative_to(ROOT)),
            "input_freeze_sha256": freeze_digest, "max_launches": 1,
            "launches_consumed": 1, "state": "consumed_running",
            "parent_readiness": True, "native_execution_authorized": True,
            "authorization_sha256": digest(directory / "authorization.json"),
            "execution_record_sha256": None, "outcome": None,
        }
        ledger["runs"].append(row)
        ledger["slot"] = {"state": "running", "active_run_id": run_id}
        write_json(LEDGER, ledger)
        started = time.time()
        execution = {"run_id": run_id, "command": command, "started_unix": started,
                     "native_solve_executed": True, "mechanical_acceptance": False}
        terminal = False
        try:
            with (directory / "native.stdout").open("w") as out, (directory / "native.stderr").open("w") as err:
                result = subprocess.run(command, stdout=out, stderr=err, timeout=timeout_seconds + 30, check=False)
            execution["returncode"] = result.returncode
            check = subprocess.run(docker + ["ps", "-aq", "--filter", "name=^/" + container + "$"],
                                   capture_output=True, text=True, check=True, timeout=30)
            if check.stdout.strip():
                raise RuntimeError("Docker client returned but the native container still exists")
            terminal = True
        except BaseException as exc:
            execution["exception"] = f"{type(exc).__name__}: {exc}"
            try:
                subprocess.run(docker + ["rm", "-f", container], capture_output=True, timeout=30, check=False)
                check = subprocess.run(docker + ["ps", "-aq", "--filter", "name=^/" + container + "$"],
                                       capture_output=True, text=True, check=True, timeout=30)
                terminal = not check.stdout.strip()
            except (subprocess.SubprocessError, OSError) as cleanup_error:
                execution["cleanup_exception"] = repr(cleanup_error)
            raise
        finally:
            execution.update(elapsed_seconds=time.time()-started, container_confirmed_terminal=terminal)
            execution["outputs_sha256"] = {p.name: digest(p) for p in directory.iterdir()
                if p.is_file() and (p.name.startswith("model.") or p.name.startswith("native."))}
            write_json(directory / "execution.json", execution)
            row["state"] = "consumed_terminal" if terminal else "consumed_cleanup_unconfirmed"
            row["execution_record_sha256"] = digest(directory / "execution.json")
            row["outcome"] = "Native exit " + str(execution.get("returncode", execution.get("exception")))
            ledger["slot"] = ({"state": "idle", "active_run_id": None} if terminal
                              else {"state": "cleanup_unconfirmed", "active_run_id": run_id})
            write_json(LEDGER, ledger)
    return execution
