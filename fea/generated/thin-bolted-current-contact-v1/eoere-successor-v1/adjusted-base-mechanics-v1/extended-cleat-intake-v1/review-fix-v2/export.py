"""Reserve a fresh descriptor output before loading the frozen intake APIs.

Exclusive creation rejects existing files, dangling final-component symlinks
and competing calls. Failed or interrupted attempts retain their reserved path.
The frozen source, parent-manifest, slot and descriptor gates remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
FROZEN = OWN.parent.parent / "export.py"
FROZEN_SHA = "bdfa95b4da8dfcb3d183dcaf59574afdb2f42e938f8e535680739fa0637696bb"


def load_frozen():
    if hashlib.sha256(FROZEN.read_bytes()).hexdigest() != FROZEN_SHA:
        raise ValueError("preserve the frozen extended-cleat intake")
    spec = importlib.util.spec_from_file_location("frozen_extended_intake_after_output_reservation", FROZEN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_record(stream, record):
    encoded = json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n"
    stream.seek(0)
    stream.write(encoded)
    stream.truncate()
    stream.flush()
    os.fsync(stream.fileno())


def reserved_output(out, produce):
    start = time.monotonic()
    attempt = {"schema": "eoere_cached_descriptor_export_attempt/v2", "status": "STARTED",
               "output": str(out), "command": list(sys.orig_argv),
               "expected_source_sha256": {str(OWN.relative_to(ROOT)): LOADED_SHA,
                                           str(FROZEN.relative_to(ROOT)): FROZEN_SHA}}
    # O_CREAT|O_EXCL reserves before produce: Path.exists() follows symlinks
    # and cannot protect a dangling final component or a concurrent producer.
    with Path(out).open("x") as stream:
        write_record(stream, attempt)
        try:
            result = produce()
            result["execution"] = {"command": list(sys.orig_argv), "elapsed_seconds": time.monotonic()-start}
            result["descriptor_output_reservation"] = {"method": "exclusive-create-before-frozen-intake",
                                                       "failed_attempts_retained": True}
            write_record(stream, result)
        except BaseException as error:
            attempt.update(status="FAILED", exception={"type": type(error).__name__, "message": str(error)},
                           elapsed_seconds=time.monotonic()-start)
            write_record(stream, attempt)
            raise
    return result


def export_to_file(manifest_path, manifest_sha, out, *, extract=False, slot_path=None, slot_sha=None):
    def produce():
        frozen = load_frozen()
        frozen.a.verify({str(OWN.relative_to(ROOT)): LOADED_SHA})
        result = (frozen.export_native(manifest_path, manifest_sha, slot_path, slot_sha) if extract
                  else frozen.source_plan(manifest_path, manifest_sha))
        frozen.a.join(result["source_sha256"], {str(OWN.relative_to(ROOT)): LOADED_SHA})
        frozen.a.verify(result["source_sha256"])
        return result
    return reserved_output(out, produce)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--slot", type=Path)
    parser.add_argument("--slot-sha256")
    args = parser.parse_args()
    result = export_to_file(args.manifest, args.manifest_sha256, args.out, extract=args.extract,
                            slot_path=args.slot, slot_sha=args.slot_sha256)
    print(json.dumps({"output": str(args.out), "schema": result["schema"]}))


if __name__ == "__main__":
    main()
