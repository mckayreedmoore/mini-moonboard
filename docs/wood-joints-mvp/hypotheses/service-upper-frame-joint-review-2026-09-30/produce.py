#!/usr/bin/env python3
"""Apply the frozen upper-joint extractor to the four service-upper blocks."""

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SHARED = HERE.with_name("upper-frame-joint-review-2026-09-30") / "produce.py"
STATIONS = {
    "left_service_outer_upper_cleat": (
        "left_service/left_service_mirrored_inner_outer_hypothesis/"
        "clip_horizontal_upper_left_1/"
    ),
    "wj06_outer_upper_right_cleat": (
        "wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/"
    ),
    "left_service_inner_upper_cleat": (
        "left_service/left_service_mirrored_inner_outer_hypothesis/"
        "clip_horizontal_upper_left_2/"
    ),
    "wj04_upper_g7_crosscut_full_stock_cleat": (
        "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/"
    ),
}


def shared_module():
    freeze = json.loads((HERE / "freeze.json").read_text())
    expected = next(
        row["sha256"]
        for row in freeze["method_and_hardware_sources"]
        if ROOT / row["path"] == SHARED
    )
    import hashlib

    assert hashlib.sha256(SHARED.read_bytes()).hexdigest() == expected
    spec = importlib.util.spec_from_file_location("frozen_upper_extractor", SHARED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # These are this process's explicit packet/station inputs; no source file
    # or archived output is modified. All shared freeze/count guards remain.
    module.HERE = HERE
    module.STATIONS = STATIONS
    return module


def produce():
    module = shared_module()
    report = module.produce()
    report["schema"] = "service-upper-frame-joint-review/v1"
    report["status"] = "CONDITIONAL_SERVICE_UPPER_ACTIONS_AND_COMPONENT_REFERENCES_ONLY"
    report["shared_producer_sha256"] = module.sha(SHARED)
    report["producer_sha256"] = module.sha(Path(__file__))
    report["scope"] = (
        "Four service-upper blocks, including the shortened upper-right G7."
    )
    return module, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    module, report = produce()
    files = {
        "upper-joints.json": json.dumps(report, indent=2, sort_keys=True) + "\n",
        "bolt-actions.csv": module.csv_text(report),
    }
    for name, text in files.items():
        if args.verify:
            assert (HERE / name).read_text() == text, (
                name + " differs from frozen replay"
            )
        else:
            (HERE / name).write_text(text)
    print(
        json.dumps(
            {
                "verified": args.verify,
                "counts": report["counts"],
                "sampled_maxima_by_block": report["sampled_maxima_by_block"],
            },
            indent=2,
        )
    )
