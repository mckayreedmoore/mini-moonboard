"""One-piece wood reserve follow-up to the nominal deep-principal BR904 screen."""

import argparse
import json
from pathlib import Path
from unittest.mock import patch

from scripts import hardware_first_br904_deep_principal as deep
from scripts import hardware_first_br904_outward_seat as outward
from scripts.hardware_first_center_hybrid import ROOT

OUTPUT = ROOT / "docs/bolted-candidate-prototypes/hardware_first_br904_reserve.json"
DEEPENING = 80.0
HEADER_HALF_RAISE = 242.0
TARGET_RESERVE = 10.0
LOWES_LISTING = "https://www.lowes.com/pd/4-in-x-10-in-x-12-ft-Douglas-Fir-Lumber-Common-3-562-in-x-9-5-in-x-12-ft-Actual/1000028861"
LOWES_ACTUAL_MM = [90.4748, 241.3, 3657.6]


def screen_reserve():
    """Reuse every parent clash check with only the two wood profile dimensions changed."""
    with (
        patch.object(deep, "DEEPENING", DEEPENING),
        patch.object(outward, "HEADER_HALF_RAISE", HEADER_HALF_RAISE),
    ):
        result = deep.screen_deep_principal()

    principal = min(
        min(row["transverse_4d_play_margins_mm"])
        for row in result["principal_wood_filters"].values()
    )
    shoulder = min(
        row["raised_shoulder_3_5d_play_margin_mm"]
        for row in result["header_wood_filters"].values()
    )
    toe = min(
        row["oblique_toe_3_5d_play_margin_mm"]
        for row in result["principal_wood_filters"].values()
    )
    if principal < TARGET_RESERVE:
        result["failures"].append("principal_transverse_reserve_below_target")
    if shoulder < TARGET_RESERVE:
        result["failures"].append("header_shoulder_reserve_below_target")
    result.update(
        status=(
            "rejected_nominal_geometry"
            if result["failures"]
            else "geometry_only_stock_unverified"
        ),
        parent_report=str(deep.OUTPUT.relative_to(ROOT)),
        header_raised_half_width_mm=HEADER_HALF_RAISE,
        target_reserve_mm=TARGET_RESERVE,
        minimum_principal_transverse_reserve_mm=principal,
        minimum_header_shoulder_reserve_mm=shoulder,
        minimum_principal_oblique_toe_reserve_mm=toe,
        lowes_dimensional_lead={
            "listing": LOWES_LISTING,
            "listed_actual_envelope_mm": LOWES_ACTUAL_MM,
            "geometric_envelope_fit_only": {
                name: all(
                    a <= b for a, b in zip(sorted(blank), sorted(LOWES_ACTUAL_MM))
                )
                for name, blank in result["principal_minimum_sampled_blank_mm"].items()
            },
            "status": "Dimensional lead only; delivered stock and usable machining allowance unverified.",
        },
        filter_limit=(
            "Principal 3.5D oblique-toe and reversible 4D transverse markers, "
            "plus header 3.5D shoulder/4D Y-edge markers, include nominal "
            "factory-hole play. These are search filters, not classified NDS "
            "end/edge acceptance. The oblique-toe minimum remains below 10 mm."
        ),
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_reserve(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
