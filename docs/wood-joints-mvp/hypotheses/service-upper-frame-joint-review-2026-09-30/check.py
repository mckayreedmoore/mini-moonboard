#!/usr/bin/env python3
"""Reuse the frozen direct DAT-token checker for service-upper actions."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SHARED = HERE.with_name("upper-frame-joint-review-2026-09-30") / "check.py"


def check():
    freeze = json.loads((HERE / "freeze.json").read_text())
    expected = next(
        row["sha256"]
        for row in freeze["method_and_hardware_sources"]
        if ROOT / row["path"] == SHARED
    )
    assert hashlib.sha256(SHARED.read_bytes()).hexdigest() == expected
    spec = importlib.util.spec_from_file_location("frozen_upper_checker", SHARED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE = HERE
    result = module.check()
    result["schema"] = "service-upper-frame-native-token-check/v1"
    result["shared_checker_sha256"] = module.sha(SHARED)
    result["checker_sha256"] = module.sha(Path(__file__))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = check()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.verify:
        assert (HERE / "verification.json").read_text() == text
    else:
        (HERE / "verification.json").write_text(text)
    print(text)
