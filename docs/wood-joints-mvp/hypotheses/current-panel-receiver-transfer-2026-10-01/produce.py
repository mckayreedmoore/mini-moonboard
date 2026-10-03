#!/usr/bin/env python3
"""Join frozen panel/screw inventory and actions without solving or accepting them."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
OUTPUT = HERE / "receiver-transfer.json"
PINS_OUTPUT = HERE / "source-pins.json"


def canonical(value: dict) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def pin(path: Path, root: Path) -> dict:
    raw = path.read_bytes()
    return {
        "path": path.resolve().relative_to(root.resolve()).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
    }


def merge_pins(*documents: dict) -> dict:
    by_path = {}
    for document in documents:
        for record in document["sources"]:
            previous = by_path.setdefault(record["path"], record)
            if previous != record:
                raise ValueError(f"conflicting source pins: {record['path']}")
    return {"sources": [by_path[path] for path in sorted(by_path)]}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot import packet module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build_report(root: Path = ROOT) -> tuple[dict, dict]:
    folder = root / HERE.relative_to(ROOT)
    inventory = load_module(folder / "inventory.py", "panel_transfer_inventory")
    actions = load_module(folder / "actions.py", "panel_transfer_actions")
    inventory_report, inventory_pins = inventory.build_report(root=root)
    action_report, action_pins = actions.build_report(
        root=root, inventory_report=inventory_report
    )
    for report in (inventory_report, action_report):
        if (
            report["candidate"] != CANDIDATE
            or report["geometry_revision_id"] != REVISION
        ):
            raise ValueError("inventory/action candidate or revision mismatch")
    local_pins = {
        "sources": [
            pin(folder / name, root)
            for name in (
                "produce.py",
                "test_produce.py",
                "inventory.py",
                "test_inventory.py",
                "actions.py",
                "test_actions.py",
                "inventory.md",
                "actions.md",
                "hillman-applicability.md",
            )
        ]
    }
    hardware_policy_pins = {
        "sources": [
            pin(root / path, root)
            for path in (
                "docs/current-panel-screw-purchase.md",
                "docs/floor-flush-shop-checklist.md",
            )
        ]
    }
    pins = merge_pins(inventory_pins, action_pins, local_pins, hardware_policy_pins)
    pins.update(schema="current_panel_receiver_transfer_source_pins/v1")
    report = {
        "schema": "current_panel_receiver_transfer/v1",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "inventory": inventory_report,
        "actions": action_report,
        "recursive_reduced_mpc_transfer_status": action_report[
            "panel_receiver_mpc_transfer_status"
        ],
        "source_pins_sha256": hashlib.sha256(canonical(pins)).hexdigest(),
        "claim_boundary": {
            "status": "NON_QUALIFYING_FROZEN_SOURCE_JOIN_ONLY",
            "native_solve_executed_by_this_packet": False,
            "geometry_changed": False,
            "hillman_physical_stiffness_established": False,
            "resistance_established": False,
            "complete_joint_accepted": False,
            "formal_criterion_pass_adopted": False,
            "fabrication_or_climbing_release": False,
        },
    }
    return report, pins


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    try:
        report, pins = build_report()
        for path, content in ((OUTPUT, report), (PINS_OUTPUT, pins)):
            raw = canonical(content)
            if args.verify:
                if path.read_bytes() != raw:
                    raise ValueError(f"saved output differs: {path}")
            else:
                path.write_bytes(raw)
        print(
            json.dumps(
                {
                    "inventory": report["inventory"]["counts"],
                    "actions": report["actions"]["counts"],
                    "recursive_reduced_mpc_transfer_status": report[
                        "recursive_reduced_mpc_transfer_status"
                    ],
                },
                sort_keys=True,
            )
        )
    except (OSError, ValueError, KeyError, ImportError) as exc:
        print(f"panel receiver source join refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
