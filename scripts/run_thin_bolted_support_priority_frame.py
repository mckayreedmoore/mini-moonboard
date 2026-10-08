"""Prioritize untested floor masks while reusing the frozen lean joint runner."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from unittest.mock import patch

from scripts import run_thin_bolted_support_search_frame as core
from scripts import thin_bolted_support_mask_schedule as scheduling
from scripts.thin_bolted_timber_face_contact import merge_pins

frame = core.frame
OWN = str(Path(__file__).resolve().relative_to(frame.ROOT))
LOADED_DRIVER_SHA256 = frame.sha(Path(__file__))
SCHEDULE_PATH = "scripts/thin_bolted_support_mask_schedule.py"
CORE_RECEIPT = frame.PACKET / "support-state-search-method-v4.json"
CORE_RECEIPT_SHA256 = "3cbff2407511cfbf31a47d04819d1c851df9c0822c21d8fad64af912e307fda9"
PRIORITY_RECEIPT = frame.PACKET / "support-priority-method-v4.json"
METHOD_SCHEMA = "thin_bolted_support_priority_method/v1"


def source_pins(receipt_path, receipt_sha256, previous_schedule):
    receipt_path = Path(receipt_path).resolve()
    if receipt_path != PRIORITY_RECEIPT.resolve():
        raise ValueError("fresh priority method receipt path required")
    if frame.sha(receipt_path) != receipt_sha256:
        raise ValueError("priority method receipt differs from frozen input")
    receipt = json.loads(receipt_path.read_bytes())
    if (receipt.get("schema") != METHOD_SCHEMA or receipt.get("method_checks_pass") is not True
            or receipt.get("released") is not False or receipt.get("release") != frame.RELEASE):
        raise ValueError("checked unreleased support-priority method receipt required")
    loaded = {OWN: LOADED_DRIVER_SHA256, SCHEDULE_PATH: scheduling.LOADED_PRODUCER_SHA256}
    if any(receipt.get("source_sha256", {}).get(path) != sha for path, sha in loaded.items()):
        raise ValueError("priority receipt must bind its loaded runner and schedule producer")
    pins = merge_pins(core.source_pins(CORE_RECEIPT, CORE_RECEIPT_SHA256)[0],
                      previous_schedule["source_sha256"], receipt["source_sha256"], loaded,
                      {str(receipt_path.relative_to(frame.ROOT)): receipt_sha256})
    for path, expected in pins.items():
        if frame.sha(frame.ROOT / path) != expected:
            raise ValueError("priority input changed: " + path)
    return pins


def main():
    arguments = sys.argv[1:]
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--support-prior-failure", type=Path, required=True)
    parser.add_argument("--support-prior-sha256", required=True)
    parser.add_argument("--support-priority-method-receipt", type=Path, required=True)
    parser.add_argument("--support-priority-method-sha256", required=True)
    custom, remainder = parser.parse_known_args(arguments)
    output_parser = argparse.ArgumentParser(add_help=False)
    output_parser.add_argument("--out", type=Path)
    output_parser.add_argument("--out-dir", type=Path)
    output_parser.add_argument("--support-method-receipt", type=Path, required=True)
    output_parser.add_argument("--support-method-sha256", required=True)
    selected, _ = output_parser.parse_known_args(remainder)
    if (selected.support_method_receipt.resolve() != CORE_RECEIPT.resolve()
            or selected.support_method_sha256 != CORE_RECEIPT_SHA256):
        parser.error("reuse the frozen original support-search receipt path and bytes")
    if custom.support_priority_method_receipt.resolve() != PRIORITY_RECEIPT.resolve():
        parser.error("reuse the checked priority method receipt path")
    if (selected.out is None) == (selected.out_dir is None):
        parser.error("one fresh output path or directory required")
    output = selected.out or selected.out_dir / "compatible-frame-a12-rear-v4.json"
    sidecar = output.with_name(output.name + ".priority-interrupted.json")
    if output.exists() or sidecar.exists() or output.with_name(output.name + ".interrupted.json").exists():
        parser.error("preserve prior fields and interruptions; choose a fresh output")
    previous = scheduling.load_previous_schedule(custom.support_prior_failure, custom.support_prior_sha256)
    pins = source_pins(custom.support_priority_method_receipt, custom.support_priority_method_sha256, previous)
    command = [sys.executable, "-m", "scripts.run_thin_bolted_support_priority_frame", *arguments]
    execution = {
        "command": command, "loaded_driver_sha256": LOADED_DRIVER_SHA256,
        "loaded_schedule_sha256": scheduling.LOADED_PRODUCER_SHA256,
        "method_receipt_path": str(custom.support_priority_method_receipt.resolve().relative_to(frame.ROOT)),
        "method_receipt_sha256": custom.support_priority_method_sha256,
        "prior_failure_path": previous["previous_field_path"],
        "prior_failure_sha256": previous["previous_field_sha256"],
        "scheduling_only": True, "prior_q_or_forces_used": False,
        "nested_support_search_execution_is_reused_internal_call": True,
    }
    original_metadata = core.lean.common.bind_common_metadata
    finished = core.lean.common.finished
    original_finished_binding = finished.bind_finished_state

    def metadata(report, *args):
        report = original_metadata(report, *args)
        if source_pins(custom.support_priority_method_receipt, custom.support_priority_method_sha256, previous) != pins:
            raise ValueError("priority frozen inputs changed during the case")
        report["source_sha256"] = merge_pins(report["source_sha256"], pins)
        report["parameters"].update({
            "support_priority_driver_sha256": LOADED_DRIVER_SHA256,
            "support_priority_schedule_sha256": scheduling.LOADED_PRODUCER_SHA256,
            "support_priority_method_receipt_sha256": custom.support_priority_method_sha256,
            "support_priority_prior_failure_sha256": previous["previous_field_sha256"],
        })
        report["support_priority_execution"] = copy.deepcopy(execution)
        return report

    def bind_finished(report, *args):
        report = original_finished_binding(report, *args)
        scheduling.validate_current_report(report, previous)
        return report

    def solve(*args, **kwargs):
        return scheduling.compatible_contact_solve(*args, previous_schedule=previous, **kwargs)

    old_argv = sys.argv
    try:
        sys.argv = [old_argv[0], *remainder]
        with (patch.object(core.lean.common, "bind_common_metadata", metadata),
              patch.object(finished, "bind_finished_state", bind_finished),
              patch.object(core.search, "compatible_contact_solve", solve)):
            core.main()
    except SystemExit:
        inner_sidecar = output.with_name(output.name + ".interrupted.json")
        if inner_sidecar.exists():
            source_pins(custom.support_priority_method_receipt, custom.support_priority_method_sha256, previous)
            report = {"schema": "thin_bolted_support_priority_interrupted/v1",
                      "support_priority_execution": execution,
                      "source_sha256": pins,
                      "internal_interruption_path": str(inner_sidecar.resolve().relative_to(frame.ROOT)),
                      "internal_interruption_sha256": frame.sha(inner_sidecar),
                      "accepted_field_exported": False, "usable_conditional_actions": False,
                      "release": dict(frame.RELEASE)}
            with sidecar.open("x") as stream:
                stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        raise
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
