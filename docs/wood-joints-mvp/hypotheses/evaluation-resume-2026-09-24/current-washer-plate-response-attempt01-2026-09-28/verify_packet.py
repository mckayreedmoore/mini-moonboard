#!/usr/bin/env python3
"""Verify this source-obstacle packet and its prior T06 context pins."""

from __future__ import annotations

import hashlib
from pathlib import Path


PACKET = Path(__file__).resolve().parent
REPOSITORY = PACKET.parents[4]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_packet_sums() -> list[str]:
    failures: list[str] = []
    sums_path = PACKET / "SHA256SUMS"
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split(maxsplit=1)
        path = PACKET / relative.lstrip("*")
        if not path.is_file():
            failures.append(f"missing packet file: {relative}")
        elif sha256(path) != expected:
            failures.append(f"packet hash mismatch: {relative}")
    return failures


def check_local_context_pins() -> list[str]:
    import json

    failures: list[str] = []
    pins = json.loads((PACKET / "source-pins.json").read_text(encoding="utf-8"))
    for pin in pins["local_context_pins"]:
        path = REPOSITORY / pin["path"]
        if not path.is_file():
            failures.append(f"missing prior packet context file: {pin['path']}")
        elif sha256(path) != pin["sha256"]:
            failures.append(f"prior packet context hash mismatch: {pin['path']}")
    return failures


def main() -> int:
    failures = check_packet_sums() + check_local_context_pins()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("OK: packet checksums and prior T06 context pins match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
