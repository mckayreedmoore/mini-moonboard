"""Regression for one rejected rear-Y-face HL35 installed pose."""

import json
from pathlib import Path

from scripts.hardware_first_center_rear_yface import screen_rear_yface

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/bolted-candidate-prototypes/hardware_first_center_rear_yface.json"


def test_rear_yface_pose_preserves_axes_but_rejects_joint():
    result = screen_rear_yface()
    assert result["status"] == "rejected_installed_geometry_trial"
    assert result["protected_axis_count"] == 66
    assert result["retained_frame_bolt_axis_count"] == 12
    assert result["retained_frame_bolt_new_hardware_clashes"] == []
    assert result["post_bounds_mm"] == [-92.075, 92.075, -175.7, -36.0, 0.0, 238.9]
    assert len(result["kicker_center_receivers"]) == 4
    assert all(
        item["post_overlap_mm3"] > 400 for item in result["kicker_center_receivers"]
    )
    assert all(not items for items in result["plate_panel_clashes"].values())
    assert result["protected_screw_plate_clashes"] == []
    assert len(result["header_bore_crossings"]) == 2
    assert all(item["overlap_mm3"] > 3000 for item in result["header_bore_crossings"])
    assert all(
        item["outside_receiver_mm3"] > 22000
        for item in result["bore_missing_wood"]
        if "principal" in item["name"]
    )
    assert {item["name"] for item in result["new_wood_adjacent_clashes"]["header"]} == {
        "base_side_left",
        "base_side_right",
    }
    assert json.loads(REPORT.read_text()) == result
