#!/usr/bin/env python3
"""Verify attempt04's Olander link access record and pinned predecessors."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    audit = json.loads((HERE / "source-audit.json").read_text(encoding="utf-8"))
    terminal = json.loads((HERE / "terminal-hashes.json").read_text(encoding="utf-8"))
    checked = 0
    for row in terminal["artifacts"]:
        path = HERE / row["path"]
        require(path.is_file(), f"missing packet artifact: {row['path']}")
        require(digest(path) == row["sha256"], f"packet hash mismatch: {row['path']}")
        checked += 1

    require(audit["target"]["part_number"] == "05073287001", "wrong product target")
    require(audit["disposition"]["four_target_axes"], "missing target axis disposition")
    require(set(audit["disposition"]["four_target_axes"].values()) == {"NOT_RUN_SOURCE_GAP"}, "target axes must remain open")
    require(audit["model_identity_and_coverage"]["model_bytes_retrieved"] is False, "model bytes were not retrieved")
    require(audit["access_observations"]["account_or_login_required"] == "UNKNOWN_NOT_TESTED", "do not assert untested access gate")
    require(audit["access_observations"]["vendor_contacted"] is False, "vendor contact prohibited")
    require(audit["disposition"]["geometry_changed"] is False, "geometry changed")
    require(audit["disposition"]["tool_motion_or_fit_screen_run"] is False, "fit screen run")
    require(audit["authorization_assessment"]["acceptable_geometry_source"] is False, "unverified source accepted")

    for row in audit["context_pins"]["predecessor_hash_pins"]:
        path = ROOT / row["path"]
        require(path.is_file(), f"missing predecessor evidence: {row['path']}")
        require(digest(path) == row["sha256"], f"predecessor changed: {row['path']}")

    queue_path = ROOT / audit["context_pins"]["task_queue_path"]
    require(queue_path.is_file(), "missing task queue")
    require(
        digest(queue_path) == audit["context_pins"]["task_queue_sha256_at_preparation"],
        "task queue differs from the point-in-time preparation pin",
    )

    print(
        "attempt04 Olander source-access packet verified: "
        f"{checked} packet artifact hashes; {len(audit['context_pins']['predecessor_hash_pins'])} "
        "predecessor pins and task queue pin unchanged; "
        "four #407 axes remain NOT_RUN_SOURCE_GAP"
    )


if __name__ == "__main__":
    main()
