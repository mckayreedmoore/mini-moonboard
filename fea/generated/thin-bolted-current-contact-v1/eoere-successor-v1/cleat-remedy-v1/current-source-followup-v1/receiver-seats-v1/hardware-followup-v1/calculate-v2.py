"""Correct the requested-entry output guard; retain the original arithmetic."""

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
ORIGINAL = {
    "inputs.json": "6cba1fb87b9cfa337f2c5418afe6c0f7fa6def8d6ae463e9f355701df3d75e33",
    "calculate.py": "ed7a16cbdb97bf15ddc74e2af49bb3b512dc57c7541358392db55ea25d8dfc0e",
    "result.json": "fbe6983488fc5c3017810654f43df0e0ef2188657387cc6a3b92b4e02fbb4c0a",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate():
    require(all(sha(HERE / name) == digest for name, digest in ORIGINAL.items()),
            "frozen original hardware packet changed")
    original = json.loads((HERE / "result.json").read_bytes())
    result = runpy.run_path(str(HERE / "calculate.py"))["evaluate"]()
    require(result == original, "original arithmetic or recorded source pins changed")
    pins = result["source_sha256"]
    for name, digest in ORIGINAL.items():
        path = str((HERE / name).relative_to(ROOT))
        require(path not in pins or pins[path] == digest, "contradictory original pin")
        pins[path] = digest
    pins[str(OWN.relative_to(ROOT))] = sha(OWN)
    result["source_pin_count"] = len(pins)
    result["output_guard_revision"] = {
        "original_three_files_unchanged": True,
        "original_numerical_and_hardware_findings_exact": True,
        "reject_existing_requested_entry_including_dangling_symlink": True,
        "exclusive_creation_uses_original_requested_path": True,
        "path_resolution_used_only_for_parent_ownership_test": True,
        "capacity_or_geometry_or_hardware_adoption_changed": False,
    }
    result["reproduction_command"] = (
        f"uv run python -B {OWN.relative_to(ROOT)} --out "
        f"{HERE.relative_to(ROOT)}/reproduction-v2-01.json"
    )
    result["execution"]["output_wrapper"] = str(OWN.relative_to(ROOT))
    require(all(sha(ROOT / path) == digest for path, digest in pins.items()),
            "source changed during wrapper calculation")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    requested = args.out
    require(requested.parent.resolve() == HERE and requested.suffix == ".json"
            and not os.path.lexists(requested),
            "output must be a fresh requested JSON entry in this owned subpacket")
    result = evaluate()
    # O_CREAT|O_EXCL from mode x rejects a newly occupied entry, including a
    # symlink inserted between the earlier test and this exclusive creation.
    with requested.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"out": str((HERE / requested.name).relative_to(ROOT)),
                      "sha256": sha(requested), "bytes": requested.stat().st_size,
                      "source_pin_count": result["source_pin_count"]}))


if __name__ == "__main__":
    main()
