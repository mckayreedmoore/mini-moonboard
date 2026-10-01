#!/usr/bin/env python3
"""Verify this packet's local checksums and pinned source/code inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


PACKET = Path(__file__).resolve().parent
REPOSITORY = Path(__file__).resolve().parents[5]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def verify_packet_checksums() -> None:
    checksum_file = PACKET / "SHA256SUMS"
    if not checksum_file.is_file():
        fail("SHA256SUMS is missing")
    for line_number, line in enumerate(checksum_file.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            expected, relative_path = line.split(maxsplit=1)
        except ValueError:
            fail(f"malformed SHA256SUMS line {line_number}")
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            fail(f"unsafe packet checksum path on line {line_number}")
        target = PACKET / relative
        if not target.is_file():
            fail(f"packet file is missing: {relative_path}")
        if sha256(target) != expected:
            fail(f"packet checksum mismatch: {relative_path}")


def verify_pinned_inputs() -> None:
    pins_path = PACKET / "source-pins.json"
    record = json.loads(pins_path.read_text())
    if record.get("record_id") != "current-washer-plate-response-helper-attempt01-2026-09-28":
        fail("unexpected source-pins record_id")
    pins = record.get("sha256_pins")
    if not isinstance(pins, list) or not pins:
        fail("source-pins.json has no sha256_pins")
    for pin in pins:
        relative = Path(pin["path"])
        if relative.is_absolute() or ".." in relative.parts:
            fail(f"unsafe source pin path: {pin['path']}")
        target = REPOSITORY / relative
        if not target.is_file():
            fail(f"pinned input is missing: {pin['path']}")
        actual = sha256(target)
        if actual != pin["sha256"]:
            fail(f"pinned input checksum mismatch: {pin['path']}")


def main() -> None:
    verify_packet_checksums()
    verify_pinned_inputs()
    print("OK: helper packet checksums and source/code pins match")


if __name__ == "__main__":
    main()
