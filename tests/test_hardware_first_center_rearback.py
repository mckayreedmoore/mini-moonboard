"""Regression for the conditional rear-setback center concept."""

import json
from pathlib import Path

from scripts.hardware_first_center_rearback import screen_rearback

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs/bolted-candidate-prototypes/hardware_first_center_rearback.json"


def test_rearback_geometry_and_protected_axes():
    result = screen_rearback()
    assert result["protected_axis_count"] == 66
    assert result["kicker_center_axis_count"] == 4
    assert result["minimum_setback_for_front_seat_mm"] == 82.55
    assert result["trial_setback_mm"] == 83.55
    assert result["nominal_front_seat_panel_gap_mm"] == 1.0
    assert result["upper_backing_depth_mm"] == 79.0
    assert result["lower_backing_depth_mm"] == 83.55
    assert all(
        r["frozen_axis_in_backing_mm"] > 32.5 for r in result["kicker_center_axes"]
    )
    assert result["panel_plate_clashes"] == []
    assert result["panel_backing_clashes"] == []
    assert result["backing_front_angle_clashes"] == []
    assert result["backing_to_post_structural_connection"] == "unsolved"
    assert result["status"] == "rejected_incomplete_installed_trial"
    assert result["front_bolt_head_outward_clearance_mm"] == 0.0
    assert {x["name"] for x in result["header_other_wood_clashes"]} == {
        "base_side_left",
        "base_side_right",
        "base_principal_center_left",
        "base_principal_center_right",
    }
    assert json.loads(RESULT.read_text()) == result
