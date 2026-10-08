"""Reuse the lean joint model with a source-bound finite floor-mask search.

The original preparation, constitutive laws, recovery and finished-support
writer remain unchanged. Only the order of fixed floor patterns is new. A
pattern is a solution only after its own normal forces reproduce its mask.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from unittest.mock import patch

from scripts import run_thin_bolted_linear_timber_frame as lean
from scripts import thin_bolted_support_state_search as search
from scripts.thin_bolted_timber_face_contact import merge_pins

frame = lean.frame
OWN = str(Path(__file__).resolve().relative_to(frame.ROOT))
LOADED_DRIVER_SHA256 = frame.sha(Path(__file__))
LEAN_DRIVER = "scripts/run_thin_bolted_linear_timber_frame.py"
LEAN_DRIVER_SHA256 = "4d1e1d86c70186f4cd2a1dfcc1da7714cbd761660c54de6a11f26a0738f37669"
SEARCH_PATH = "scripts/thin_bolted_support_state_search.py"
METHOD_SCHEMA = "thin_bolted_support_state_search_method/v1"


def source_pins(receipt_path: Path, expected_sha256: str) -> tuple[dict, dict]:
    """Bind loaded code to a parent-frozen method receipt before preparation."""
    receipt_path = receipt_path.resolve()
    relative = str(receipt_path.relative_to(frame.ROOT))
    if frame.sha(receipt_path) != expected_sha256:
        raise ValueError("support-search method receipt differs from frozen input")
    receipt = json.loads(receipt_path.read_bytes())
    if (receipt.get("schema") != METHOD_SCHEMA
            or receipt.get("method_checks_pass") is not True
            or receipt.get("released") is not False
            or not isinstance(receipt.get("release"), dict)
            or receipt["release"] != frame.RELEASE):
        raise ValueError("checked, unreleased support-search method receipt required")
    loaded = {OWN: LOADED_DRIVER_SHA256, LEAN_DRIVER: LEAN_DRIVER_SHA256,
              SEARCH_PATH: search.LOADED_PRODUCER_SHA256}
    if any(receipt.get("source_sha256", {}).get(path) != digest
           for path, digest in loaded.items()):
        raise ValueError("method receipt must bind the loaded runner and fixed-branch search")
    pins = merge_pins(receipt["source_sha256"], search.source_pins(), loaded,
                      {relative: expected_sha256})
    for path, expected in pins.items():
        if frame.sha(frame.ROOT / path) != expected:
            raise ValueError("support-search source changed: " + path)
    return pins, receipt


def bind_search_metadata(report, pins, command, receipt_path, receipt_sha, budget, events):
    """Add identity inputs before the frozen finished-floor identity binding."""
    report["parameters"].update({
        "support_state_search_driver_sha256": LOADED_DRIVER_SHA256,
        "support_state_search_method_sha256": search.LOADED_PRODUCER_SHA256,
        "support_state_search_method_receipt_sha256": receipt_sha,
        "support_state_search_mask_budget": budget,
    })
    report["source_sha256"] = merge_pins(report["source_sha256"], pins)
    report["support_state_search_execution"] = {
        "command": command,
        "loaded_driver_sha256": LOADED_DRIVER_SHA256,
        "loaded_method_sha256": search.LOADED_PRODUCER_SHA256,
        "method_receipt_path": str(receipt_path.resolve().relative_to(frame.ROOT)),
        "method_receipt_sha256": receipt_sha,
        "mask_budget": budget,
        "warm_initialization": None,
        "one_case_per_invocation": True,
        "frozen_floor_law_reused": True,
        "old_forces_or_acceptance_transferred": False,
        "new_solver_framework": False,
        "branch_events": copy.deepcopy(events),
        "nested_lean_execution_is_a_reused_internal_call": True,
    }
    report["limits"].append(
        "A finite nonrepeating support-mask search changes numerical ordering only. "
        "An exhausted budget or unresolved fixed branch does not prove that the "
        "declared centroid support law has no solution.")
    return report


def main() -> None:
    arguments = sys.argv[1:]
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--support-mask-budget", type=int, default=64)
    parser.add_argument("--support-method-receipt", type=Path, required=True)
    parser.add_argument("--support-method-sha256", required=True)
    custom, remainder = parser.parse_known_args(arguments)
    if not 1 <= custom.support_mask_budget <= 256:
        parser.error("support mask budget must be between one and 256")
    scope = argparse.ArgumentParser(add_help=False)
    scope.add_argument("--out", type=Path)
    scope.add_argument("--out-dir", type=Path)
    scope.add_argument("--beam-size", type=float, default=150.)
    scope.add_argument("--shaft-segment", type=float, default=25.)
    scope.add_argument("--wood-bedding", type=float, default=1.)
    scope.add_argument("--floor-tangent-stiffness", type=float, default=100000.)
    selected, _ = scope.parse_known_args(remainder)
    if (selected.out is None) == (selected.out_dir is None):
        parser.error("one fresh explicit output path or directory required")
    if (selected.beam_size != 150. or selected.shaft_segment != 25.
            or selected.wood_bedding != 1. or selected.floor_tangent_stiffness != 100000.):
        parser.error("reuse the reviewed beam, shaft, bedding and centroid-floor scenario")
    output = selected.out or selected.out_dir / "compatible-frame-a12-rear-v4.json"
    if output.exists() or output.with_name(output.name + ".interrupted.json").exists():
        parser.error("preserve earlier fields and interruptions; choose a fresh output")
    pins, _ = source_pins(custom.support_method_receipt, custom.support_method_sha256)
    command = [sys.executable, "-m", "scripts.run_thin_bolted_support_search_frame", *arguments]
    original_metadata = lean.common.bind_common_metadata
    events = []
    calls = 0

    def observe_branch(event):
        events.append(copy.deepcopy(event))
        print(json.dumps({"support_search_progress": event}), flush=True)

    def solve(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls != 1:
            raise ValueError("one joint case per support-search invocation required")
        return search.compatible_contact_solve(
            *args, **kwargs, mask_budget=custom.support_mask_budget,
            branch_observer=observe_branch)

    def metadata(report, system, inner_pins, inner_command):
        report = original_metadata(report, system, inner_pins, inner_command)
        if source_pins(custom.support_method_receipt, custom.support_method_sha256)[0] != pins:
            raise ValueError("support-search frozen inputs changed during the case")
        return bind_search_metadata(report, pins, command, custom.support_method_receipt,
                                    custom.support_method_sha256, custom.support_mask_budget, events)

    def interruption(path, _inner_command, prepared, panel_preparation, last):
        sidecar = path.with_name(path.name + ".interrupted.json")
        if source_pins(custom.support_method_receipt, custom.support_method_sha256)[0] != pins:
            raise ValueError("support-search inputs changed before interruption export")
        report = {
            "schema": "thin_bolted_support_search_interrupted/v1",
            "command": command, "termination": "lean case wall-time limit",
            "phase": last.get("phase"),
            "source_sha256": merge_pins(pins, prepared.get("source_sha256", {}),
                                        panel_preparation.get("source_sha256", {}),
                                        lean.PANEL_OPERATOR_PINS),
            "response": lean.failed_wall_response(last),
            "branch_events": copy.deepcopy(events),
            "usable_conditional_actions": False, "accepted_field_exported": False,
            "existing_output_sha256_not_admitted": frame.sha(path) if path.exists() else None,
            "release": frame.RELEASE,
        }
        with sidecar.open("x") as stream:
            stream.write(lean.common.finished.writer.dump(report))
        return sidecar

    old_argv = sys.argv.copy()
    try:
        sys.argv = [old_argv[0], *remainder]
        with (patch.object(lean.common, "bind_common_metadata", metadata),
              patch.object(lean.incremental, "compatible_contact_solve", solve),
              patch.object(lean, "write_interruption", interruption)):
            lean.main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
