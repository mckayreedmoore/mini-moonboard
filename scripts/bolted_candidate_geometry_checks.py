"""Deterministic integration checks for the unqualified AB90 candidate.

This checks identity, inventory, family coverage, and nominal envelope screens.
It deliberately does not claim exact CAD interference, bolt resistance, or a
native structural result.
"""

import argparse
import csv
import json
from pathlib import Path

from mini_moonboard import a66_layout_common
from mini_moonboard import compact_floor_flush_bolted_frame as candidate
from mini_moonboard.bolted_layouts import FAMILY_NAMES, registered_layouts
from mini_moonboard.demountable_connections import validate_records

ROOT = Path(__file__).resolve().parents[1]


def axes() -> list[dict[str, str]]:
    with (ROOT / "docs/floor-flush-construction/connection-axes.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


def report() -> dict[str, object]:
    rows = axes()
    layouts = registered_layouts()
    joints = candidate.structural_joint_records()
    fasteners = candidate.fastener_stack_records()
    interfaces = candidate.assembly_interface_records()
    validate_records(joints, fasteners, interfaces)
    a66_joints = a66_layout_common.all_records()
    a66_fasteners = a66_layout_common.all_fasteners()
    a66_interfaces = a66_layout_common.all_interfaces()
    validate_records(a66_joints, a66_fasteners, a66_interfaces)
    structural = [row for row in rows if row["shop_opening_kind"] == "sds_wood"]
    panels = [row for row in rows if row["shop_opening_kind"] == "hillman_panel"]
    frame_bolts = [row for row in rows if row["shop_opening_kind"] == "bolt_clearance"]
    station_ids = {row["first_member"] for row in structural}
    family_counts = {family: len(layouts[family]) for family in FAMILY_NAMES}
    return {
        "candidate": candidate.KEY,
        "baseline_candidate": candidate.BASELINE_KEY,
        "status": "prototype_only",
        "inventory": {
            "structural_axes": len(structural),
            "panel_axes": len(panels),
            "retained_frame_bolts": len(frame_bolts),
            "structural_stations": len(station_ids),
            "prototype_joints": len(joints),
            "prototype_fasteners": len(fasteners),
            "prototype_interfaces": len(interfaces),
        },
        "family_counts": family_counts,
        "parallel_a66_prototype": {
            "connector": "Simpson Strong-Tie A66",
            "joints": len(a66_joints),
            "fasteners": len(a66_fasteners),
            "interfaces": len(a66_interfaces),
            "status": "prototype_only; exact hole geometry, station fit, and resistance unresolved",
        },
        "nominal_envelope_screen": {
            "ab90_flange_a_mm": 88.0,
            "ab90_flange_b_mm": 88.0,
            "preserved_nominal_face_mm": 139.7,
            "within_preserved_nominal_face": True,
            "exact_solid_fit_checked": False,
            "tool_access_checked": False,
        },
        "scope_checks": {
            "panel_axes_unchanged": len(panels) == 66,
            "structural_wood_thread_policy_preserved": True,
            "selected_as_repository_default": False,
            "resistance_checked": False,
            "native_cases_complete": False,
            "fabrication_release": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = report()
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
