"""Bind output to the canonical owned directory after validating a parent alias."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import runpy
from pathlib import Path

OWN = Path(__file__).resolve()
HERE = OWN.parent
ROOT = OWN.parents[8]
PREVIOUS = {
    "calculate-v2.py": "cafd8b00756e7cf5177fb8722f6139883d4c40aa28a7a08bf9d988575aa770f0",
    "result-v2.json": "2a70abd309932e497daeb0bebf152439077f776a28823d910d50c35c71c24f42",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate():
    require(all(sha(HERE / name) == digest for name, digest in PREVIOUS.items()),
            "frozen v2 hardware wrapper/result changed")
    previous = json.loads((HERE / "result-v2.json").read_bytes())
    result = runpy.run_path(str(HERE / "calculate-v2.py"))["evaluate"]()
    require(result == previous, "v2 arithmetic or recorded source pins changed")
    pins = result["source_sha256"]
    for name, digest in PREVIOUS.items():
        path = str((HERE / name).relative_to(ROOT))
        require(path not in pins or pins[path] == digest, "contradictory v2 pin")
        pins[path] = digest
    pins[str(OWN.relative_to(ROOT))] = sha(OWN)
    result["source_pin_count"] = len(pins)
    result["output_guard_revision"] = {
        "original_five_v1_v2_files_unchanged": True,
        "original_numerical_and_hardware_findings_exact": True,
        "requested_parent_resolved_and_validated_once": True,
        "destination_bound_to_canonical_owned_directory": True,
        "reject_existing_canonical_leaf_including_dangling_symlink": True,
        "exclusive_creation_uses_canonical_owned_destination": True,
        "requested_parent_alias_retarget_cannot_redirect_output": True,
        "capacity_or_geometry_or_hardware_adoption_changed": False,
    }
    result["reproduction_command"] = (
        f"uv run python -B {OWN.relative_to(ROOT)} --out "
        f"{HERE.relative_to(ROOT)}/reproduction-v3-01.json"
    )
    result["execution"]["output_wrapper"] = str(OWN.relative_to(ROOT))
    require(all(sha(ROOT / path) == digest for path, digest in pins.items()),
            "source changed during canonical-output wrapper calculation")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    requested = args.out
    parent = requested.parent.resolve()
    require(parent == HERE and requested.suffix == ".json",
            "output parent must resolve to this owned subpacket")
    destination = HERE / requested.name
    require(not os.path.lexists(destination),
            "output must be a fresh canonical JSON entry in this owned subpacket")
    result = evaluate()
    # The original parent alias is never used again. Mode x protects this
    # canonical leaf against an entry inserted after the earlier test.
    with destination.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"out": str(destination.relative_to(ROOT)),
                      "sha256": sha(destination), "bytes": destination.stat().st_size,
                      "source_pin_count": result["source_pin_count"]}))


if __name__ == "__main__":
    main()
