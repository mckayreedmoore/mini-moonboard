"""Stdlib entrypoint for fresh reproductions of two immutable analysis packets.

The original CLIs remain preserved historical bytes. This entrypoint reserves
a new output directory before source authentication, imports or calculation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())
EXPECTED_ANALYSES = {
    "audit": "9ec29f1ba0dba1dbbec193366284abfd1604e09099822714335c28e226bd84ca",
    "connected": "56c84c7fbe06da68ddfe27fe147fff52344cf0cdd0ef72cda489d9163926e82b",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def serialized(value):
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "changed source: " + path)


def read_pinned(reference):
    verify({reference["path"]: reference["sha256"]})
    return json.loads((ROOT / reference["path"]).read_bytes())


def merge(pins, additional):
    for path, digest in additional.items():
        require(path not in pins or pins[path] == digest, "conflicting pin: " + path)
        pins[path] = digest


def load_inputs():
    path = HERE / "inputs.json"
    digest = sha(path)
    value = json.loads(path.read_bytes())
    require(sha(path) == digest, "guard inputs changed while reading")
    return value, digest


def authenticate(inputs, inputs_sha, packet):
    selected = inputs["packets"][packet]
    require(
        selected["analysis"]["sha256"] == EXPECTED_ANALYSES[packet],
        "unrecognized frozen analysis",
    )
    pins = {str((HERE / "inputs.json").relative_to(ROOT)): inputs_sha}
    require(
        set(inputs["packets"]) == set(EXPECTED_ANALYSES),
        "two supported immutable packets",
    )
    for key, record in inputs["packets"].items():
        require(
            record["analysis"]["sha256"] == EXPECTED_ANALYSES[key],
            "unrecognized frozen analysis",
        )
        require(
            len(record["issued_files"]) == 5
            and {Path(r["path"]).name for r in record["issued_files"]}
            == {
                "README.md",
                "analyze.py",
                "inputs.json",
                "result.json",
                "verification.json",
            },
            "five immutable packet files required",
        )
        merge(pins, {r["path"]: r["sha256"] for r in record["issued_files"]})
        merge(pins, {record["details"]["path"]: record["details"]["sha256"]})
    details = read_pinned(selected["details"])
    closure = details["complete_source_sha256"]
    require(
        len(closure) == selected["issued_pin_count"], "issued closure count differs"
    )
    require(
        canonical(closure) == selected["issued_closure_canonical_sha256"],
        "issued closure digest differs",
    )
    merge(pins, closure)
    for filename in ("run_fresh.py", "check_evidence.py", "check_guard.py"):
        path = HERE / filename
        merge(pins, {str(path.relative_to(ROOT)): sha(path)})
    verify(pins)
    return {
        "pins": pins,
        "issued_pin_count": len(closure),
        "issued_closure_canonical_sha256": canonical(closure),
        "guarded_pin_count": len(pins),
        "guarded_closure_canonical_sha256": canonical(pins),
    }


def reserve_output(path):
    # Do not resolve the final component: a dangling symlink must also fail.
    Path(path).mkdir(parents=True, exist_ok=False)


def write_new(path, value):
    with Path(path).open("xb") as stream:
        stream.write(serialized(value))


def load_analysis(path, packet):
    name = "guarded_frozen_" + packet
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def guarded_calculation(output, before, calculate, after, metadata, compare=None):
    """Reserve first; authenticate even when calculation raises; never clobber."""
    output = Path(output)
    reserve_output(output)
    snapshot = before()
    try:
        result, details = calculate()
    finally:
        after(snapshot)
    documents = {"result.json": result, "details.json": details}
    encoded = {name: serialized(value) for name, value in documents.items()}
    if compare is not None:
        for name, data in encoded.items():
            require(
                (Path(compare) / name).read_bytes() == data,
                "reproduction differs: " + name,
            )
    for name, value in documents.items():
        write_new(output / name, value)
    after(snapshot)
    provenance = {
        "schema": "frozen_analysis_fresh_reproduction/v1",
        "status": "VERIFIED_FRESH_OUTPUT",
        "entrypoint": {
            "path": str(Path(__file__).relative_to(ROOT)),
            "sha256": sha(__file__),
        },
        "packet": metadata,
        "source_pins_before_after_unchanged": True,
        "issued_pin_count": snapshot["issued_pin_count"],
        "issued_closure_canonical_sha256": snapshot["issued_closure_canonical_sha256"],
        "guarded_pin_count": snapshot["guarded_pin_count"],
        "guarded_closure_canonical_sha256": snapshot[
            "guarded_closure_canonical_sha256"
        ],
        "output_files": {
            name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in encoded.items()
        },
        "comparison_directory": None if compare is None else str(compare),
        "output_policy": "new directory reserved before authentication/import/run; exclusive file creation",
    }
    write_new(output / "run-provenance.json", provenance)
    return provenance


def execute(packet, output, compare=None):
    holder = {}
    metadata = {"key": packet, "expected_analysis_sha256": EXPECTED_ANALYSES[packet]}

    def before():
        inputs, digest = load_inputs()
        holder["selected"] = inputs["packets"][packet]
        metadata["guard_inputs"] = {
            "path": str((HERE / "inputs.json").relative_to(ROOT)),
            "sha256": digest,
        }
        metadata["issued_details"] = holder["selected"]["details"]
        return authenticate(inputs, digest, packet)

    def calculate():
        module = load_analysis(holder["selected"]["analysis"]["path"], packet)
        return module.run()

    return guarded_calculation(
        output,
        before,
        calculate,
        lambda snapshot: verify(snapshot["pins"]),
        metadata,
        compare,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, choices=EXPECTED_ANALYSES)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    try:
        provenance = execute(args.packet, args.out, args.compare)
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + "\n")
    print(json.dumps({"status": provenance["status"], "packet": args.packet}))


if __name__ == "__main__":
    main()
