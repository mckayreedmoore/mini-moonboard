"""Compare saved 66-/98-screw packets using the existing force/law consumer.

Inventory and known operator-status adaptations support 20 screws per main
panel. References, force bases, screw laws and source authentication remain.
No frame, native, geometry or panel-allocation solve runs here.
"""

from __future__ import annotations

import argparse
import csv
import inspect
import json
from pathlib import Path

import head_check as source

HERE = Path(__file__).resolve().parent
SOURCE_SHA = "352fd499f3486037a401ab3b4dabeb4838a93aa8db67564f4ca30d0b3ea9382a"


def count_consumer():
    text = inspect.getsource(source.consume)
    replacements = {"66": "98", "132": "196", "792": "1176",
                    ": 144": ": 240", "12-per-main": "20-per-main",
                    'assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS"':
                    'assessment["status"] in {"PASS_UPDATED_ELASTIC_FRAME_OPERATORS", '
                    '"PASS_APPENDED_ELASTIC_FRAME_OPERATORS"}'}
    source.require([text.count(site) for site in replacements] == [2, 1, 3, 1, 1, 1],
                   "frozen force-consumer adaptation sites changed")
    for old, new in replacements.items():
        text = text.replace(old, new)
    namespace = source.__dict__.copy()
    exec(compile(text, "<98-screw-saved-force-consumer>", "exec"), namespace)  # noqa: S102 -- pinned source and checked inventory substitutions
    return namespace["consume"], text, replacements


def build(packets, output):
    source.require(output.is_relative_to(HERE / "rawlocal/count-head-check")
                   and output != HERE / "rawlocal/count-head-check",
                   "use a fresh rawlocal/count-head-check child")
    source.require(not output.exists(), "preserve previous calculations")
    source.require(source.sha(Path(source.__file__)) == SOURCE_SHA,
                   "changed frozen force consumer")
    pins = {source.label(Path(source.__file__)): SOURCE_SHA,
            source.label(Path(__file__)): source.sha(Path(__file__))}
    scenarios = source.reference_scenarios(pins)
    consume98, adapted, replacements = count_consumer()
    all_records, reports, seen = [], [], set()
    for packet in packets:
        comparison = source.read(packet / "comparison.json")
        operators = Path(comparison["frame_operator_directory"])
        operators = operators if operators.is_absolute() else source.ROOT / operators
        rows = source.read(operators / "row-identities.json")
        count = sum(r["ownership"]["role"] == source.AXIAL for r in rows)
        source.require(count in {66, 98}, "unsupported panel screw inventory")
        records, metadata = (source.consume if count == 66 else consume98)(packet, pins)
        source.require(metadata["source"] not in seen, "duplicate source packet")
        seen.add(metadata["source"])
        groups = {"all_saved_states": records,
                  "zero_gap": [r for r in records if r["gap_scale"] == 0],
                  "nominal_gap": [r for r in records if r["gap_scale"] == 1]}
        metadata["physical_axis_count_in_scenario"] = count
        metadata["proposed_main_panel_screw_count"] = 12 if count == 66 else 20
        metadata["demand_summaries"] = {name: source.summary(items, scenarios)
                                        for name, items in groups.items()}
        metadata["panel_nominal_gap_summaries"] = {
            panel: source.summary([r for r in groups["nominal_gap"] if r["panel"] == panel], scenarios)
            for panel in sorted({r["panel"] for r in records})
        }
        reports.append(metadata)
        all_records.extend(records)
    for path, digest in pins.items():
        source.require(source.sha(source.ROOT / path) == digest, "source changed: " + path)
    output.mkdir(parents=True)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    (output / "adapted-consumer.py.snapshot").write_text(adapted)
    report = {
        "schema": "conditional_panel_count_grain_force_comparison/v1",
        "producer_sha256": source.sha(Path(__file__)), "source_sha256": pins,
        "inventory_and_known_operator_status_adaptations": replacements,
        "source_packets": reports, "total_screw_states": len(all_records),
        "claim_boundary": {
            "physical_98_screw_inventory_adopted": False,
            "hillman_resistance_established": False,
            "qualified_connection_capacity": False,
            "lateral_or_combined_reference_transferred": False,
            "complete_joint_acceptance": False, "physical_release": False,
            "frame_or_native_solve_run_by_consumer": False,
        },
    }
    (output / "comparison.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    with (output / "screw-states.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(all_records[0]))
        writer.writeheader()
        writer.writerows(all_records)
    receipt = {
        "schema": "conditional_count_grain_force_receipt/v1",
        "source_sha256": pins, "source_packets": len(reports),
        "screw_states": len(all_records),
        "output_sha256": {name: source.sha(output / name) for name in
                          ("comparison.json", "screw-states.csv", "producer.py.snapshot",
                           "adapted-consumer.py.snapshot")},
        "complete_joint_acceptance": False, "physical_release": False,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": source.label(output), "screw_states": len(all_records),
                      "receipt_sha256": source.sha(output / "receipt.json")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build([p.resolve() for p in args.source], args.output.resolve())
