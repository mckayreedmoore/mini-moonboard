#!/usr/bin/env python3
"""Verify generated washer/contact preparation hashes without a solver call."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(prepared: Path) -> dict:
    prepared = prepared.resolve()
    receipt_path = prepared / "preparation.json"
    receipt = json.loads(receipt_path.read_text())
    if receipt.get("schema") != "washer_contact_known_answer_preparation/v1":
        raise ValueError("unexpected preparation receipt schema")
    if receipt.get("native_solve_executed") is not False:
        raise ValueError("preparation receipt does not confirm no native solve")
    if receipt.get("input_freeze_created") is not False:
        raise ValueError("preparation receipt must not create an input freeze")
    if receipt.get("native_readiness") is not False or receipt.get("mechanical_acceptance") is not False:
        raise ValueError("preparation receipt overstates readiness or acceptance")

    for relative, expected in receipt["files_sha256"].items():
        path = (prepared / relative).resolve()
        if not path.is_relative_to(prepared) or not path.is_file():
            raise ValueError(f"missing or escaped generated file: {relative}")
        if sha256(path) != expected:
            raise ValueError(f"generated-file hash mismatch: {relative}")

    for name, job in receipt["jobs"].items():
        for artifact_key, hash_key in (("deck", "deck_sha256"),
                                       ("expected", "expected_sha256"),
                                       ("coordinates", "coordinates_sha256")):
            relative = job[artifact_key]
            if receipt["files_sha256"].get(relative) != job[hash_key]:
                raise ValueError(f"job manifest hash disagreement: {name}/{artifact_key}")

    for relative, expected in receipt["supporting_code_sha256"].items():
        path = (HERE / relative).resolve()
        if not path.is_relative_to(HERE) or not path.is_file():
            raise ValueError(f"missing or escaped supporting code: {relative}")
        if sha256(path) != expected:
            raise ValueError(f"supporting-code hash mismatch: {relative}")

    forbidden_names = {"freeze.json", "execution.json", "authorization.json",
                       "native.stdout", "native.stderr", "model.dat", "model.frd"}
    if any(path.name in forbidden_names for path in prepared.rglob("*")):
        raise ValueError("prepared directory contains freeze or native-execution artifacts")
    return {
        "status": "PASS_PREPARATION_HASH_RECEIPT",
        "preparation_only": True,
        "native_solve_executed": False,
        "generated_file_count": len(receipt["files_sha256"]),
        "supporting_code_count": len(receipt["supporting_code_sha256"]),
        "jobs": sorted(receipt["jobs"]),
        "preparation_json_sha256": sha256(receipt_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prepared", nargs="?", type=Path, default=HERE / "prepared")
    args = parser.parse_args()
    print(json.dumps(verify(args.prepared), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
