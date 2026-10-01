#!/usr/bin/env python3
"""Verify this packet's checksums and immutable predecessor source pins."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = next((parent for parent in ROOT.parents if (parent / ".git").exists()), None)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    failures: list[str] = []
    sum_path = ROOT / "SHA256SUMS"
    entries = 0
    for line_number, raw_line in enumerate(sum_path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            expected, relative = line.split(maxsplit=1)
        except ValueError:
            failures.append(f"SHA256SUMS:{line_number}: malformed entry")
            continue
        relative = relative.lstrip("*").strip()
        candidate = (ROOT / relative).resolve()
        if ROOT not in candidate.parents:
            failures.append(f"SHA256SUMS:{line_number}: packet path escapes directory: {relative}")
            continue
        if not candidate.is_file():
            failures.append(f"SHA256SUMS:{line_number}: missing packet file: {relative}")
            continue
        entries += 1
        if digest(candidate) != expected:
            failures.append(f"SHA256SUMS:{line_number}: digest mismatch: {relative}")
    if entries == 0:
        failures.append("SHA256SUMS has no packet entries")

    if REPO is None:
        failures.append("could not locate repository root containing .git")
    else:
        pins_path = ROOT / "source-pins.json"
        pins = json.loads(pins_path.read_text(encoding="utf-8"))
        checked_pins = 0
        for pin in pins["pins"]:
            if not pin.get("immutable"):
                continue
            relative = Path(pin["path"])
            candidate = (REPO / relative).resolve()
            if REPO not in candidate.parents:
                failures.append(f"source pin escapes repository: {relative}")
                continue
            if not candidate.is_file():
                failures.append(f"missing immutable source pin: {relative}")
                continue
            checked_pins += 1
            if digest(candidate) != pin["sha256"]:
                failures.append(f"immutable source pin mismatch: {relative}")
        if checked_pins == 0:
            failures.append("no immutable source pins were checked")

    if failures:
        print("FAIL")
        print("\n".join(failures))
        return 1
    print(f"PASS: {entries} packet files and {checked_pins} immutable source pins verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
