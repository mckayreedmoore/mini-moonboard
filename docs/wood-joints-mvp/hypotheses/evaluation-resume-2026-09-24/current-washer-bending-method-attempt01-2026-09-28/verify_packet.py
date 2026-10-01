#!/usr/bin/env python3
"""Verify local source pins and packet SHA-256 checksums; standard library only."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_root(start: Path) -> Path:
    for parent in (start, *start.parents):
        if (parent / ".git").exists() and (parent / "AGENTS.md").is_file():
            return parent
    raise RuntimeError("could not locate repository root from packet path")


def verify_local_sources(root: Path, pins_path: Path) -> list[str]:
    data = json.loads(pins_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    for item in data["local_inputs"]:
        path = root / item["path"]
        if not path.is_file():
            failures.append(f"missing local source: {item['path']}")
            continue
        observed = sha256(path)
        if observed != item["sha256"]:
            failures.append(
                f"local source drift: {item['path']} expected {item['sha256']} observed {observed}"
            )
    return failures


def verify_packet_files(packet: Path) -> list[str]:
    sums_path = packet / "SHA256SUMS"
    if not sums_path.is_file():
        return ["missing packet SHA256SUMS"]

    failures: list[str] = []
    seen: set[str] = set()
    for raw_line in sums_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            expected, relative = raw_line.split(maxsplit=1)
            relative = relative.lstrip("*")
        except ValueError:
            failures.append(f"malformed checksum line: {raw_line!r}")
            continue
        if relative in seen:
            failures.append(f"duplicate checksum entry: {relative}")
            continue
        seen.add(relative)
        path = (packet / relative).resolve()
        if packet.resolve() not in path.parents:
            failures.append(f"checksum path escapes packet: {relative}")
            continue
        if not path.is_file():
            failures.append(f"missing packet file: {relative}")
            continue
        observed = sha256(path)
        if observed != expected:
            failures.append(
                f"packet checksum mismatch: {relative} expected {expected} observed {observed}"
            )
    if not seen:
        failures.append("SHA256SUMS contains no file entries")
    return failures


def main() -> int:
    packet = Path(__file__).resolve().parent
    root = repository_root(packet)
    pins_path = packet / "source-pins.json"
    failures = verify_local_sources(root, pins_path)
    failures.extend(verify_packet_files(packet))
    if failures:
        print("FAIL: washer-bending method packet verification")
        for failure in failures:
            print(f"- {failure}")
        return 1

    pin_data = json.loads(pins_path.read_text(encoding="utf-8"))
    print(
        "PASS: "
        f"{len(pin_data['local_inputs'])} local source pins and "
        f"{len([line for line in (packet / 'SHA256SUMS').read_text(encoding='utf-8').splitlines() if line.strip()])} packet checksums verified"
    )
    print("External sources are version/identifier pins; this verifier does not fetch network resources.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
