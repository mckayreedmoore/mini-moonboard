"""Reuse original branches with a cumulative authenticated mask schedule."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from unittest.mock import patch

from scripts import run_thin_bolted_support_search_frame as core
from scripts import thin_bolted_support_mask_chain as scheduling
from scripts.thin_bolted_timber_face_contact import merge_pins

frame = core.frame
OWN = str(Path(__file__).resolve().relative_to(frame.ROOT))
LOADED_DRIVER_SHA256 = frame.sha(Path(__file__))
METHOD_PATH = "scripts/thin_bolted_support_mask_chain.py"
CORE_RECEIPT = frame.PACKET / "support-state-search-method-v4.json"
CORE_RECEIPT_SHA256 = "3cbff2407511cfbf31a47d04819d1c851df9c0822c21d8fad64af912e307fda9"
METHOD_RECEIPT = frame.PACKET / "support-chain-method-v4.json"
METHOD_SCHEMA = "thin_bolted_support_chain_method/v1"


def source_pins(receipt_path, receipt_sha256, chain):
    receipt_path = Path(receipt_path).resolve()
    if receipt_path != METHOD_RECEIPT.resolve():
        raise ValueError("fresh support-chain method receipt path required")
    if frame.sha(receipt_path) != receipt_sha256:
        raise ValueError("support-chain method receipt differs from frozen input")
    receipt = json.loads(receipt_path.read_bytes())
    if (receipt.get("schema") != METHOD_SCHEMA or receipt.get("method_checks_pass") is not True
            or receipt.get("released") is not False or receipt.get("release") != frame.RELEASE):
        raise ValueError("checked unreleased support-chain method receipt required")
    loaded = {OWN: LOADED_DRIVER_SHA256, METHOD_PATH: scheduling.LOADED_PRODUCER_SHA256}
    if any(receipt.get("source_sha256", {}).get(path) != sha for path, sha in loaded.items()):
        raise ValueError("chain receipt must bind its loaded runner and schedule producer")
    pins = merge_pins(core.source_pins(CORE_RECEIPT, CORE_RECEIPT_SHA256)[0],
                      scheduling.source_pins(chain), receipt["source_sha256"], loaded,
                      {str(receipt_path.relative_to(frame.ROOT)): receipt_sha256})
    for path, expected in pins.items():
        if frame.sha(frame.ROOT / path) != expected:
            raise ValueError("support-chain input changed: " + path)
    return pins


def main():
    arguments = sys.argv[1:]
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--support-chain-prior-failure", type=Path, required=True)
    parser.add_argument("--support-chain-prior-sha256", required=True)
    parser.add_argument("--support-chain-method-receipt", type=Path, required=True)
    parser.add_argument("--support-chain-method-sha256", required=True)
    custom, remainder = parser.parse_known_args(arguments)
    scope = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    scope.add_argument("--out", type=Path)
    scope.add_argument("--out-dir", type=Path)
    scope.add_argument("--support-method-receipt", type=Path, required=True)
    scope.add_argument("--support-method-sha256", required=True)
    selected, _ = scope.parse_known_args(remainder)
    if (selected.support_method_receipt.resolve() != CORE_RECEIPT.resolve()
            or selected.support_method_sha256 != CORE_RECEIPT_SHA256):
        parser.error("reuse the frozen original support-search receipt path and bytes")
    if custom.support_chain_method_receipt.resolve() != METHOD_RECEIPT.resolve():
        parser.error("reuse the checked chain method receipt path")
    if (selected.out is None) == (selected.out_dir is None):
        parser.error("one fresh output path or directory required")
    output = selected.out or selected.out_dir / "compatible-frame-a12-rear-v4.json"
    sidecar = output.with_name(output.name + ".chain-interrupted.json")
    if output.exists() or sidecar.exists() or output.with_name(output.name + ".interrupted.json").exists():
        parser.error("preserve prior fields and interruptions; choose a fresh output")
    chain = scheduling.load_failed_chain(
        custom.support_chain_prior_failure, custom.support_chain_prior_sha256,
        chain_driver_sha256=LOADED_DRIVER_SHA256,
        method_receipt_path=custom.support_chain_method_receipt,
        method_receipt_sha256=custom.support_chain_method_sha256)
    pins = source_pins(custom.support_chain_method_receipt, custom.support_chain_method_sha256, chain)
    execution = {
        "command": [sys.executable, "-m", "scripts.run_thin_bolted_support_chain_frame", *arguments],
        "loaded_driver_sha256": LOADED_DRIVER_SHA256,
        "loaded_method_sha256": scheduling.LOADED_PRODUCER_SHA256,
        "method_receipt_path": str(custom.support_chain_method_receipt.resolve().relative_to(frame.ROOT)),
        "method_receipt_sha256": custom.support_chain_method_sha256,
        "prior_failure_path": chain["previous_field_path"],
        "prior_failure_sha256": chain["previous_field_sha256"],
        "scheduling_only": True, "prior_q_or_forces_used": False,
        "nested_support_search_execution_is_reused_internal_call": True,
    }
    original_metadata = core.lean.common.bind_common_metadata
    finished = core.lean.common.finished
    original_finished_binding = finished.bind_finished_state

    def metadata(report, *args):
        report = original_metadata(report, *args)
        if source_pins(custom.support_chain_method_receipt, custom.support_chain_method_sha256, chain) != pins:
            raise ValueError("chain frozen inputs changed during the case")
        report["source_sha256"] = merge_pins(report["source_sha256"], pins)
        report["parameters"].update({
            "support_mask_schedule_chain_driver_sha256": LOADED_DRIVER_SHA256,
            "support_mask_schedule_chain_method_sha256": scheduling.LOADED_PRODUCER_SHA256,
            "support_mask_schedule_chain_method_receipt_sha256": custom.support_chain_method_sha256,
            "support_mask_schedule_chain_prior_failure_sha256": chain["previous_field_sha256"],
        })
        report["support_mask_chain_execution"] = copy.deepcopy(execution)
        # Input scheduling provenance survives a wall-time failure with no q.
        report["response"]["support_mask_chain_schedule_v1"] = scheduling.chain_metadata(chain)
        return report

    def bind_finished(report, *args):
        report = original_finished_binding(report, *args)
        scheduling.validate_current_report(report, chain)
        return report

    def solve(*args, **kwargs):
        return scheduling.compatible_contact_solve(*args, previous_chain=chain, **kwargs)

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
            source_pins(custom.support_chain_method_receipt, custom.support_chain_method_sha256, chain)
            report = {"schema": "thin_bolted_support_chain_interrupted/v1",
                      "support_mask_chain_execution": execution, "source_sha256": pins,
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
