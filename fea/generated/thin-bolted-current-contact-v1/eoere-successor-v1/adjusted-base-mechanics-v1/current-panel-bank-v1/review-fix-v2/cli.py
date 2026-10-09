"""Reserve a fresh panel-plan output before loading frozen source methods.

The original bank and its API remain frozen. This corrected CLI reads source
metadata only. A reserved output records a preparation failure and is retained.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BANK = OWN.parent.parent / "panel_operators.py"
BANK_SHA = "014f867eac1e9286dee188024544b5853e5cda2aa1cd11037d7aee5a2b29966b"


def load_bank():
    if hashlib.sha256(BANK.read_bytes()).hexdigest() != BANK_SHA:
        raise ValueError("preserve the frozen current panel bank")
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    spec = importlib.util.spec_from_file_location("frozen_current_panel_bank_for_reserved_CLI", BANK)
    bank = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bank)
    return bank


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    # Atomic O_EXCL reservation also rejects dangling symlinks and concurrent writers.
    with args.out.open("x") as stream:
        try:
            bank = load_bank()
            plan, _, current, moved, pins = bank.read_sources()
            if hashlib.sha256(OWN.read_bytes()).hexdigest() != LOADED_SHA:
                raise ValueError("current panel CLI changed during source preparation")
            pins = {**pins, str(OWN.relative_to(ROOT)): LOADED_SHA}
            result = {"schema": "eoere_current_off_panel_source_plan/v1",
                "source_inputs": bank.input_record(plan, current, moved), "source_sha256": pins,
                "metadata_only_no_K_q_or_contact_construction": True,
                "production_bank_prepared": False, "current_observed_volume_COM_required": True,
                "fresh_contacts_loads_frame_response_and_independent_admission_required": True,
                "exclusive_output_reserved_before_source_preparation": True,
                "CLI_revision": "review-fix-v2", "release": copy.deepcopy(bank.raised.RELEASE)}
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        except BaseException as exc:
            stream.seek(0)
            stream.truncate()
            json.dump({"schema": "eoere_current_off_panel_source_plan_failure/v2",
                "status": "FAILED_RESERVED_OUTPUT_RETAINED", "exception_type": type(exc).__name__,
                "exception_message": str(exc), "production_bank_prepared": False,
                "source_sha256": {str(OWN.relative_to(ROOT)): LOADED_SHA},
                "exclusive_output_reserved_before_source_preparation": True}, stream, indent=2, sort_keys=True)
            stream.write("\n")
            raise


if __name__ == "__main__":
    main()
