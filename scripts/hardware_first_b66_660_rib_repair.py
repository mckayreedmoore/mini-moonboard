"""Two bounded nominal repairs of the B66 660-mm right-rib bore conflict.

This reuses the parent screen's exact four-bore and neighbor checks. It does
not produce fabrication dimensions or a connector capacity.
"""

import argparse
import csv
import json
from pathlib import Path
from unittest.mock import patch

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import hardware_first_b66_660_component_route as route
from scripts.hardware_first_b66_rear_y import REACH, WIDTH
from scripts.hardware_first_center_hybrid import AXES, ROOT, TOL, box, cylinder, hits
from scripts.hardware_first_hl53_660_parent_neighbor import (
    RAIL_NAME,
    _header_hardware,
    _parent,
)

OUTPUT = (
    ROOT / "docs/bolted-candidate-prototypes/hardware_first_b66_660_rib_repair.json"
)
FORWARD_SHIFT_MM = 6.0
REAR_RIB_EXTENSION_MM = 6.0


def _extended_parent(raw):
    wood, adjacent, header_bottom, rail_top = _parent(raw)
    rib = wood["rib_principal_right"]
    # A single continuous, wider timber profile, not a laminated add-on.
    wood["rib_principal_right"] = rib.fuse(
        rib.translate((0, -REAR_RIB_EXTENSION_MM, 0))
    ).clean()
    return wood, adjacent, header_bottom, rail_top


def _old_frame_axis_diagnostic(parent):
    """Record occupancy only; the old twelve axes are not reused/approved."""
    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    wood, _, _, _ = parent(raw)
    wood[RAIL_NAME], _ = route._rail_with_full_seat(raw, wood)
    changed = {name: wood[name] for name in ("rib_principal_right", RAIL_NAME)}
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    frame_rows = [row for row in rows if row["shop_opening_kind"] == "bolt_clearance"]
    if len(frame_rows) != 12:
        raise ValueError("expected twelve historical frame-bolt axes")
    return {row["name"]: hits(cylinder(row), changed) for row in frame_rows}


def _seat_and_extension_diagnostic(parent, joint_y):
    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    original_wood, _, _, _ = _parent(raw)
    wood, adjacent, header_bottom, _ = parent(raw)
    wood[RAIL_NAME], bend_z = route._rail_with_full_seat(raw, wood)
    rib = wood["rib_principal_right"]
    extension = rib.cut(original_wood["rib_principal_right"]).clean()
    face = rib.BoundingBox().xmax
    seat_footprint = box(face, joint_y - WIDTH / 2, bend_z - 0.1, REACH, WIDTH, 0.1)
    contact = seat_footprint.intersect(wood[RAIL_NAME]).Volume()
    brackets, bolts, washers, tools = _header_hardware(wood, header_bottom)
    parent_wood = {
        **{
            name: solid
            for name, solid in wood.items()
            if name not in ("rib_principal_right", RAIL_NAME)
        },
        **adjacent,
    }
    return {
        "rail_seat_contact_fraction": round(contact / seat_footprint.Volume(), 6),
        "rib_extension_volume_mm3": round(extension.Volume(), 3),
        "rib_extension_to_parent_wood": (
            hits(extension, parent_wood) if extension.Volume() > TOL else {}
        ),
        "rib_extension_to_parent_hardware": (
            hits(extension, {**brackets, **bolts, **washers, **tools})
            if extension.Volume() > TOL
            else {}
        ),
    }


def _trial(name, *, joint_y=None, parent=None):
    parent = parent or _parent
    overrides = {"_parent": parent}
    if joint_y is not None:
        overrides["JOINT_Y"] = joint_y
    with patch.multiple(route, **overrides):
        result = route.screen_b66_route()
    result["variant"] = name
    result["joint_y_mm"] = joint_y if joint_y is not None else route.JOINT_Y
    result["rear_rib_extension_mm"] = (
        REAR_RIB_EXTENSION_MM if parent is _extended_parent else 0.0
    )
    result["old_frame_axis_diagnostic"] = _old_frame_axis_diagnostic(parent)
    result["repair_diagnostic"] = _seat_and_extension_diagnostic(
        parent, result["joint_y_mm"]
    )
    result["old_frame_axes_approved"] = False
    result["all_four_full_bores_in_wood"] = all(
        hole["bore_missing_receiver_mm3"] <= TOL for hole in result["holes"]
    )
    result["nominal_local_checks_clear"] = (
        result["status"] == "partial_nominal_geometry_clear"
        and result["all_four_full_bores_in_wood"]
        and result["repair_diagnostic"]["rail_seat_contact_fraction"] >= 1 - TOL
        and not result["repair_diagnostic"]["rib_extension_to_parent_wood"]
        and not result["repair_diagnostic"]["rib_extension_to_parent_hardware"]
    )
    return result


def screen_repairs():
    original = route.screen_b66_route()
    missing = next(
        hole["bore_missing_receiver_mm3"]
        for hole in original["holes"]
        if hole["id"] == "rail_vertical_1"
    )
    return {
        "scope": "One bottom-right B66/UB66 station, kerf-right, 660-mm ribs",
        "original_bore_missing_mm3": missing,
        "variants": [
            _trial(
                "move_bracket_forward_6_mm", joint_y=route.JOINT_Y + FORWARD_SHIFT_MM
            ),
            _trial("one_piece_rib_rearward_6_mm", parent=_extended_parent),
        ],
        "other_rail_ends_open": 5,
        "connected_architecture_verdict": False,
        "normal_duration_rating_adopted": False,
        "drilling_released": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(screen_repairs(), indent=2) + "\n")


if __name__ == "__main__":
    main()
