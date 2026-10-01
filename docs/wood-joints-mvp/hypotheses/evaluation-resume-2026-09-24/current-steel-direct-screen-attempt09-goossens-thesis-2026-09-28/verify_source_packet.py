#!/usr/bin/env python3
"""Verify the append-only attempt09 packet and immutable attempt08 pins."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    try:
        observations = json.loads((HERE / "source-observations.json").read_text())
        pins = json.loads((HERE / "source-pins.json").read_text())
        manifest = json.loads((HERE / "terminal-hashes.json").read_text())
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot read packet JSON: {error}")
        return 1

    if observations.get("schema") != "wood_joint_t06_goossens_thesis_route_screen_attempt09/v1":
        print("FAIL: unexpected observations schema")
        return 1
    if observations.get("target_thesis", {}).get("pdf_bytes_obtained") is not False:
        print("FAIL: packet must not claim thesis bytes were obtained")
        return 1
    if observations.get("page_level_thesis_facts", {}).get("status") != "not_observed_no_thesis_bytes":
        print("FAIL: unexpected page-level fact status")
        return 1

    failures: list[str] = []
    for record in pins.get("pins", []):
        path = ROOT / record["path"]
        if not path.is_file():
            failures.append(f"missing predecessor pin: {record['path']}")
        elif sha256(path) != record["sha256"]:
            failures.append(f"predecessor pin mismatch: {record['path']}")

    terminal = manifest.get("files", [])
    for record in terminal:
        path = HERE / record["path"]
        if not path.is_file():
            failures.append(f"missing terminal file: {record['path']}")
        elif sha256(path) != record["sha256"]:
            failures.append(f"terminal hash mismatch: {record['path']}")

    if failures:
        print("FAIL: " + "; ".join(failures))
        return 1
    print(
        "PASS: attempt09 packet JSON, "
        f"{len(terminal)} terminal files, and {len(pins.get('pins', []))} immutable attempt08 pins"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
