"""Run a pinned saved-field gate with exclusive success/failure records."""
import argparse
import hashlib
import importlib.util
import json
import sys
import traceback
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
for name in ("gate", "field", "out"):
    parser.add_argument("--" + name, type=Path, required=True)
for name in ("gate-sha256", "field-sha256"):
    parser.add_argument("--" + name, required=True)
args = parser.parse_args()
failure = args.out.with_suffix(args.out.suffix + ".failure.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(args.gate) == args.gate_sha256
assert sha(args.field) == args.field_sha256
assert not args.out.exists() and not failure.exists()
spec = importlib.util.spec_from_file_location("eoere_parent_saved_output_gate", args.gate)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
try:
    result = gate.audit_first_order_state(args.field)
except Exception:
    with failure.open("x") as stream:
        json.dump({"command": sys.orig_argv, "gate_sha256": args.gate_sha256,
                   "field_sha256": args.field_sha256, "traceback": traceback.format_exc(),
                   "accepted_field": False}, stream, indent=2, sort_keys=True)
        stream.write("\n")
    raise
with args.out.open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
assert sha(args.gate) == args.gate_sha256 and sha(args.field) == args.field_sha256
print(json.dumps({"output": str(args.out), "sha256": sha(args.out),
                  "success": result[gate.SUCCESS],
                  "original_law_checks": result["original_law_checks"],
                  "motion_diagnostics": result["motion_diagnostics"]}, sort_keys=True))
