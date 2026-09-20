"""Regression for one lower-only paired HL33 screen."""

import json
from pathlib import Path

from scripts.hardware_first_center_hl33_outer_post import screen_hl33_outer_post

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_center_hl33_outer_post.json"
)


def test_lower_only_hl33_outer_post_trial():
    result = screen_hl33_outer_post()
    assert result["status"] == "rejected_installed_geometry_trial"
    assert result["failures"] == [
        "new wood collision",
        "bore collision",
        "kicker seam or center receiver failure",
    ]
    assert result["scope"] == "lower-only; upper joint unmodeled"
    assert result["protected_axis_count"] == 66
    assert result["retained_frame_axis_count"] == 12
    assert result["catalog_minimum_wood_thickness_mm"] == 88.9
    assert result["receiver_thickness_mm"] == {"post": 190.5, "header": 88.9}
    assert result["post_bounds_mm"][2:4] == [-126.47, -36.0]
    assert result["shared_post_bolt_axis_count"] == 1
    assert result["header_bore_axis_count"] == 2
    assert result["bore_missing_receiver_wood_mm3"] == {}
    assert result["independent_bore_crossings_mm3"] == {}
    assert result["new_wood_adjacent_clashes_mm3"]["header"] == {
        "base_principal_center_left": 269700.459,
        "base_principal_center_right": 269700.459,
    }
    assert result["bore_adjacent_wood_clashes_mm3"] == {
        "left_header": {"base_principal_center_left": 130.436},
        "right_header": {"base_principal_center_right": 130.436},
    }
    assert result["protected_screw_hardware_clashes_mm3"] == {}
    assert result["existing_frame_axis_hardware_clashes_mm3"] == {}
    assert result["protected_screw_receiver_loss_mm3"] == {}
    assert result["kicker_seam_supported"] is False
    assert result["kicker_seam_vertical_support_gap_mm"] == 4.55
    assert result["seat_inner_gap_mm"] == 25.4
    assert all(result["one_piece_cad_solid"].values())
    assert json.loads(REPORT.read_text()) == result
