"""Regression for the one bounded nominal B66 center trial."""

import json
from pathlib import Path

from scripts.hardware_first_b66_center import screen_b66_center

RESULT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_b66_center.json"
)


def test_b66_center_rejects_installed_pose_without_self_bend_collisions():
    result = screen_b66_center()
    assert result["status"] == "rejected_nominal_installed_geometry"
    assert result["width_option"] == "kerf-right"
    assert result["protected_axis_count"] == 66
    assert result["protected_screw_receiver_intersection_count"] == 66
    assert all(result["kicker_edge_backed"].values())
    assert result["bracket_count"] == 4
    assert result["factory_circle_paths_screened"] == 16
    assert result["nominal_dxf_free_end_offsets_mm"] == [25.4, 126.744]
    assert result["plate_plate_conflicts"] == []
    assert (
        result["lower_post_outer_x_edge_screen"]["nominal_center_to_edge_mm"] == 22.075
    )
    assert result["lower_post_outer_x_edge_screen"]["conservative_4D_filter_mm"] == 38.1
    assert not result["lower_post_outer_x_edge_screen"]["passes_filter"]
    assert set(result["nominal_bores_missing_wood_mm3"]) == {
        "upper_left_vertical_1",
        "upper_right_vertical_1",
    }
    assert "header:base_side_left" in result["changed_wood_neighbor_conflicts"]
    assert (
        "upper_left_vertical:base_rail_bottom_left"
        in result["plate_neighbor_conflicts"]
    )
    assert (
        "pressure-treated" in result["one_piece_stock_envelope"]["retail_feasibility"]
    )
    assert json.loads(RESULT.read_text()) == result
