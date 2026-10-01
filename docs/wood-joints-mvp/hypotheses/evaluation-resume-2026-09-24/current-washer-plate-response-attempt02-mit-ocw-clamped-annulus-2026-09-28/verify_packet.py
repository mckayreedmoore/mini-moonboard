#!/usr/bin/env python3
"""Verify this append-only source packet and its predecessor pins."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[5]
PACKET = pathlib.Path(__file__).resolve().parent
SUMS = PACKET / "SHA256SUMS"


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    errors: list[str] = []
    for line in SUMS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, rel = line.split(None, 1)
        rel = rel.lstrip("* ")
        path = PACKET / rel
        if not path.is_file():
            errors.append(f"missing packet file: {rel}")
        elif sha256(path) != expected:
            errors.append(f"checksum mismatch: {rel}")

    try:
        data = json.loads((PACKET / "source-observations.json").read_text(encoding="utf-8"))
        if data.get("record_id") != PACKET.name:
            errors.append("source observation record_id does not match packet directory")
        for pin in data.get("predecessor_pins", []):
            path = ROOT / pin["path"]
            if not path.is_file():
                errors.append(f"missing predecessor pin: {pin['path']}")
            elif sha256(path) != pin["sha256"]:
                errors.append(f"predecessor hash mismatch: {pin['path']}")
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        errors.append(f"invalid source-observations.json: {exc}")

    if errors:
        print("FAIL: " + "; ".join(errors), file=sys.stderr)
        return 1
    print("OK: packet checksums and predecessor pins match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
