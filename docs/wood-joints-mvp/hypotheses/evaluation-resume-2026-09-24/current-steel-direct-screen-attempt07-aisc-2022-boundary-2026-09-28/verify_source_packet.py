#!/usr/bin/env python3
"""Verify local attempt07 artifacts and read-only context pins.

This verifier does not download or authenticate external AISC publications.
The packet records their retrieval limits separately.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
TERMINAL_PATH = HERE / "terminal-hashes.json"
SUMS_PATH = HERE / "SHA256SUMS"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def repo_root() -> Path:
    for parent in HERE.parents:
        if (parent / "AGENTS.md").is_file():
            return parent
    raise FileNotFoundError("Could not locate repository root containing AGENTS.md")


def main() -> int:
    observations_path = HERE / "source-observations.json"
    observations = json.loads(observations_path.read_text(encoding="utf-8"))
    terminal = json.loads(TERMINAL_PATH.read_text(encoding="utf-8"))
    root = repo_root()

    require(
        observations.get("schema") == "wood_joint_t06_aisc_360_22_boundary_attempt07/v1",
        "Unexpected source-observations schema",
    )
    decision = observations["decision"]
    require(decision["capacity_calculations"] == 0, "Capacity calculation count changed")
    require(decision["candidate_parts_selected"] == 0, "Candidate part selection count changed")
    require(decision["methods_adopted"] == 0, "Method adoption count changed")
    require(decision["criterion_dispositions_changed"] == 0, "Criterion disposition count changed")
    require(not decision["prior_attempts_modified"], "Prior-attempt preservation flag changed")
    require(not decision["candidate_or_geometry_changed"], "Candidate/geometry preservation flag changed")
    require(not decision["native_or_solver_execution"], "Native/solver execution flag changed")

    context_pins = observations.get("local_context_pins", [])
    require(bool(context_pins), "No local context pins recorded")
    for pin in context_pins:
        relative = pin["path"]
        require("luna-max-task-queue.json" not in relative, "Mutable task queue must not be a source pin")
        path = root / relative
        require(path.is_file(), f"Missing context file: {relative}")
        actual = sha256(path)
        require(actual == pin["sha256"], f"Context hash mismatch: {relative}")

    require(terminal.get("schema") == "wood_joint_t06_attempt07_terminal_hashes/v1", "Unexpected terminal schema")
    require(terminal.get("self_hash_excluded") is True, "Terminal manifest must exclude its own hash")
    for entry in terminal.get("artifacts", []):
        relative = entry["path"]
        path = HERE / relative
        require(path.is_file(), f"Missing terminal artifact: {relative}")
        actual = sha256(path)
        require(actual == entry["sha256"], f"Terminal hash mismatch: {relative}")

    sums_lines = [line.strip() for line in SUMS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(bool(sums_lines), "SHA256SUMS is empty")
    for line in sums_lines:
        parts = line.split(maxsplit=1)
        require(len(parts) == 2, f"Malformed SHA256SUMS line: {line}")
        expected, relative = parts[0], parts[1].lstrip("* ")
        require(relative != "SHA256SUMS", "SHA256SUMS must not hash itself")
        path = HERE / relative
        require(path.is_file(), f"Missing SHA256SUMS target: {relative}")
        require(sha256(path) == expected, f"SHA256SUMS mismatch: {relative}")

    print("PASS: attempt07 local artifacts, context pins, and status checks")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
