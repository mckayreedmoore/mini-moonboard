"""Bounded nominal toe-vs-header-seat shift screen; never drilling data."""

import argparse
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_center_hybrid import BORE, TOP, box

ROOT = Path(__file__).resolve().parents[1]
HEADER_FRONT_Y = -36.0
INITIAL_UPPER_BEND_Y = -175.7
HL35_BEND_LENGTH = 127.0
PRINCIPAL_WIDTH = 88.9


def _principal(side):
    original = {
        part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()
    }[f"base_principal_center_{side}"]
    bounds = original.BoundingBox()
    growth = (PRINCIPAL_WIDTH - bounds.xlen) / 2
    wide = original.fuse(
        original.translate((-growth, 0, 0)),
        original.translate((growth, 0, 0)),
    ).clean()
    b = wide.BoundingBox()
    return wide.intersect(
        box(b.xmin - 1, b.ymin - 1, TOP, b.xlen + 2, b.ylen + 2, b.zmax - TOP + 2)
    ).clean()


def _missing_first_bore(principal, shift_mm):
    b = principal.BoundingBox()
    bore = cq.Solid.makeCylinder(
        BORE / 2,
        PRINCIPAL_WIDTH,
        cq.Vector(b.xmin, INITIAL_UPPER_BEND_Y + shift_mm + 31.75, TOP + 50.8),
        cq.Vector(1, 0, 0),
    )
    return round(max(0.0, bore.Volume() - bore.intersect(principal).Volume()), 3)


def screen_toe_shift():
    """Compare full-bore containment with the unextended header-seat band."""
    maximum_supported_shift = round(
        HEADER_FRONT_Y - (INITIAL_UPPER_BEND_Y + HL35_BEND_LENGTH), 4
    )
    samples = {}
    for side in ("left", "right"):
        principal = _principal(side)
        samples[side] = {
            "unshifted_missing_wood_mm3": _missing_first_bore(principal, 0.0),
            "at_max_supported_shift_missing_wood_mm3": _missing_first_bore(
                principal, maximum_supported_shift
            ),
            "at_15_mm_shift_missing_wood_mm3": _missing_first_bore(principal, 15.0),
        }
    return {
        "status": "nominal_shift_band_rejected",
        "parent_pose": "docs/bolted-candidate-prototypes/hardware_first_center_hybrid.md",
        "width_option": KERF_RIGHT,
        "maximum_shift_with_full_127_mm_seat_on_existing_header_mm": maximum_supported_shift,
        "first_bore_samples": samples,
        "seat_overhang_at_15_mm_shift_mm": round(15.0 - maximum_supported_shift, 4),
        "disposition": "At the largest forward shift that keeps the full nominal upper HL35 seat on the existing front-limited header, both first upper principal bore cylinders still exit wood. A 15-mm shift contains the ideal bores but overhangs the header by 2.3 mm. This is a nominal geometry bound, not an NDS end-distance or bracket load-path check. Extending the header, changing bracket orientation, or reshaping the principal is a different installed design. No drilling or fabrication release.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_toe_shift(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
