"""Regression for one upper front-Y B66 center pose."""

import json
from pathlib import Path

from scripts.hardware_first_b66_front_y import screen_b66_front_y

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_b66_front_y.json"
)


def test_front_y_b66_pose_fails_complete_installed_geometry():
    result = screen_b66_front_y()
    assert result["status"] == "rejected_nominal_installed_geometry"
    assert result["protected_screw_axes"] == 66
    assert result["retained_frame_axes"] == 12
    assert result["protected_screw_receiver_intersections"] == 66
    assert result["kicker_inner_edges_backed"] == {"left": True, "right": True}
    assert result["brackets"] == 3
    assert result["factory_hole_paths"] == 12
    assert result["nominal_dxf_free_end_offsets_mm"] == [25.4, 126.744]
    assert result["minimum_receiver_thickness_mm"] >= 76.2
    assert result["front_upper_bore_missing_wood_mm3"] == {
        "principal_left_vertical_1": 5320.858,
        "principal_right_vertical_1": 5320.858,
    }
    assert result["front_upper_nominal_bore_exit_shortfall_mm"] == {
        "principal_left_vertical_2": 21.2,
        "principal_right_vertical_2": 21.2,
    }
    assert {c["a"] for c in result["front_upper_plate_wood_conflicts"]} == {
        "principal_left_vertical",
        "principal_left_seat",
        "principal_right_vertical",
        "principal_right_seat",
    }
    assert {c["b"] for c in result["changed_wood_panel_conflicts"]} == {
        "main_lower_left",
        "main_lower_right",
        "kicker_left",
        "kicker_right",
    }
    assert len(result["screw_plate_conflicts"]) == 2
    assert len(result["screw_bore_conflicts"]) == 2
    assert result["old_frame_hardware_conflicts"] == []
    assert json.loads(REPORT.read_text()) == result
