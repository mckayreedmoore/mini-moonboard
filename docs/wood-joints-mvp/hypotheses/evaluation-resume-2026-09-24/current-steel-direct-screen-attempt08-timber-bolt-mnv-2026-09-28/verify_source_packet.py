#!/usr/bin/env python3
"""Verify attempt08 packet checksums and immutable predecessor pins."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    try:
        terminal = json.loads((HERE / "terminal-hashes.json").read_text())
        pins = json.loads((HERE / "source-pins.json").read_text())
        json.loads((HERE / "source-observations.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read packet JSON: {exc}")

    terminal_entries = terminal.get("files", [])
    if terminal.get("schema") != "wood_joint_t06_attempt08_terminal_hashes/v1":
        fail("unexpected terminal-hashes schema")
    if not terminal_entries:
        fail("terminal-hashes has no file entries")
    for entry in terminal_entries:
        path = HERE / entry["path"]
        if not path.is_file():
            fail(f"missing packet file: {entry['path']}")
        actual = sha256(path)
        if actual != entry["sha256"]:
            fail(f"terminal hash mismatch: {entry['path']}")

    pin_entries = pins.get("pins", [])
    if pins.get("schema") != "wood_joint_t06_attempt08_immutable_source_pins/v1":
        fail("unexpected source-pins schema")
    if len(pin_entries) < 30:
        fail(f"only {len(pin_entries)} predecessor/context pins found")
    for entry in pin_entries:
        path = REPO / entry["path"]
        if not path.is_file():
            fail(f"missing pinned source: {entry['path']}")
        actual = sha256(path)
        if actual != entry["sha256"]:
            fail(f"pinned source changed: {entry['path']}")

    sum_path = HERE / "SHA256SUMS"
    try:
        sum_lines = [line.strip() for line in sum_path.read_text().splitlines() if line.strip()]
    except OSError as exc:
        fail(f"cannot read SHA256SUMS: {exc}")
    if not sum_lines:
        fail("SHA256SUMS is empty")
    sum_count = 0
    for line in sum_lines:
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            fail(f"malformed SHA256SUMS line: {line}")
        expected, name = parts
        name = name.lstrip("*")
        path = HERE / name
        if not path.is_file():
            fail(f"SHA256SUMS names missing file: {name}")
        if sha256(path) != expected:
            fail(f"SHA256SUMS mismatch: {name}")
        sum_count += 1

    print(
        "PASS: attempt08 packet JSON, "
        f"{len(terminal_entries)} terminal files, {len(pin_entries)} immutable "
        f"predecessor/context pins, and {sum_count} SHA256SUMS entries"
    )


if __name__ == "__main__":
    main()
