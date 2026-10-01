#!/usr/bin/env python3
"""Run the immutable attempt02 case-bound input adapter for the K12-rear 16-cell proposal."""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
CONTROL = BASE / "current-springa-frame-k12-rear-all-bearing-attempt01"
API = BASE / "current-springa-case-bound-floor-input-adapter-attempt02/prepare.py"
SCREEN = BASE / "current-springa-k12-rear-zero-u-token-screen-attempt02/floor-diagnostic-screen.json"
REGISTER = BASE / "current-six-case-source-load-register-attempt01/register.json"
FRESH = BASE / "current-springa-six-case-frame-input-adapter-attempt01/k12-rear/model.json"
OUTPUT = BASE / "current-springa-case-bound-floor-input-adapter-attempt03/k12-rear"

PINNED = {
    CONTROL / "model.json": "72cc39411bb92d3ee739a9b9aa9b025fe466f2b818f29feaa76a26c284366424",
    CONTROL / "model.inp": "0cdcee16de7be40e8a7a511c26f6cbf67f116d2475f76eab294fa661ee6fac68",
    CONTROL / "model.dat": "8c3c7590e11df6c8bce52e814ece2aba2f05ff24eb261517e95e74db41528807",
    CONTROL / "execution.json": "4e10033ba2a12952122ac790ae6c4dcf4a9585b936d239e86d73465be6db6ccc",
    CONTROL / "freeze.json": "161e9b8bfecb7ef4d5060db4d6fb25aeeb38df5fa4332a3ba47fbd92df70ac92",
    CONTROL / "authorization.json": "13050058f4090bb347503c64e18fad137da3ee1a8fcd24b6c5b40d56f116f670",
    CONTROL / "parent-serialized-input-audit.json": "31752ce76ff4310ae2d85327e4ea9436fc273fcfeddd025f7609e217b6533d80",
    SCREEN: "e7afbc79297178f1d0f98d25247d3ef51e3bd690213daad6bfd290cb04d380e6",
    REGISTER: "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508",
    FRESH: "46155d5637e5d39373cd40d973bdfc499439f7e36d7e1167a7edbb2402d061a8",
}
API_SHA256 = "1e9edd6d8d1a341c3cd70854710dd80431438f7287e425b1c3e62d94d0f963bc"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"Refusing to overwrite existing input proposal: {OUTPUT}")
    if sha(API) != API_SHA256:
        raise SystemExit("Attempt02 adapter API SHA-256 changed")
    for path, expected in PINNED.items():
        if sha(path) != expected:
            raise SystemExit(f"Pinned K12 input changed: {path}")

    flags = {
        CONTROL / "model.json": "--expected-control-model-sha256",
        CONTROL / "model.inp": "--expected-control-deck-sha256",
        CONTROL / "model.dat": "--expected-control-dat-sha256",
        CONTROL / "execution.json": "--expected-control-execution-sha256",
        CONTROL / "freeze.json": "--expected-control-freeze-sha256",
        CONTROL / "authorization.json": "--expected-control-authorization-sha256",
        CONTROL / "parent-serialized-input-audit.json": "--expected-control-parent-audit-sha256",
        SCREEN: "--expected-screen-sha256",
        REGISTER: "--expected-register-sha256",
        FRESH: "--expected-fresh-case-model-sha256",
    }
    command = [
        sys.executable, str(API), "--repo-root", str(ROOT),
        "--case-id", "k12-rear",
        "--control-dir", str(CONTROL),
        "--screen", str(SCREEN),
        "--register", str(REGISTER),
        "--fresh-case-model", str(FRESH),
        "--output-dir", str(OUTPUT),
        "--diagnostic-stage", "all-bearing",
    ]
    for path, flag in flags.items():
        command.extend([flag, PINNED[path]])
    subprocess.run(command, cwd=ROOT, check=True)

    outputs = {path.name for path in OUTPUT.iterdir()}
    forbidden = {"freeze.json", "execution.json", "model.dat", "model.frd"}
    if outputs & forbidden:
        raise SystemExit(f"Input adapter unexpectedly created response artifacts: {sorted(outputs & forbidden)}")
    print(f"Prepared input-only K12-rear proposal at {OUTPUT}")


if __name__ == "__main__":
    main()
