#!/usr/bin/env python3
"""Verify the immutable packet files listed in SHA256SUMS."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUMS = ROOT / "SHA256SUMS"


def main() -> int:
    failures: list[str] = []
    entries = 0
    for line_number, raw_line in enumerate(SUMS.read_text(encoding="utf-8").splitlines(), 1):
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
            failures.append(f"SHA256SUMS:{line_number}: path escapes packet: {relative}")
            continue
        if not candidate.is_file():
            failures.append(f"SHA256SUMS:{line_number}: missing file: {relative}")
            continue
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        entries += 1
        if actual != expected:
            failures.append(f"SHA256SUMS:{line_number}: digest mismatch: {relative}")
    if not entries:
        failures.append("SHA256SUMS contains no verifiable files")
    if failures:
        print("FAIL")
        print("\n".join(failures))
        return 1
    print(f"PASS: {entries} packet files match SHA256SUMS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
