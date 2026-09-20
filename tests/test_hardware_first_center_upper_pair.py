"""Regression for opposing upper HL33s at the center-tongue pose."""

import json
from pathlib import Path

from scripts.hardware_first_center_upper_pair import screen_upper_pair

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_center_upper_pair.json"
)


def test_opposing_upper_pair_pose():
    result = screen_upper_pair()
    assert result["status"] == "rejected_installed_geometry_trial"
    assert result["protected_axis_count"] == 66
    assert result["retained_frame_axis_count"] == 12
    assert result["fixed_panel_outline_count"] == 6
    assert result["protected_screw_receiver_loss_mm3"] == {}
    assert result["protected_screw_receiver_missing"] == {}
    assert result["upper_principal_axis_relationship"] == "shared_per_principal"
    assert result["upper_header_axis_relationship"] == "independent"
    assert result["upper_pair_seat_overlap_x_mm"] > 0
    assert result["new_plate_pair_clashes_mm3"]
    assert "upper paired plate collision" in result["failures"]
    assert json.loads(REPORT.read_text()) == result
