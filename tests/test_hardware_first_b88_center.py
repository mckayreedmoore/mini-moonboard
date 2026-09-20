"""Regression checks for the bounded nominal B88 installed fit screen."""

import json
from pathlib import Path

from scripts.hardware_first_b88_center import screen_b88_center

RESULT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_b88_center.json"
)


def test_b88_center_replays_protected_geometry_and_conflicts():
    result = screen_b88_center()
    assert result["width_option"] == "kerf-right"
    assert result["factory_pattern_source"].endswith("mitek-b88-drawing-followup.md")
    assert result["protected_axis_count"] == 66
    assert result["protected_screw_receiver_intersection_count"] == 66
    assert result["bracket_count"] == 4
    assert result["factory_circle_paths_screened"] == 24
    assert result["nominal_dxf_offsets_from_free_end_mm"] == {
        "horizontal": [28.6, 92.2, 155.8],
        "vertical": [29.0, 92.6, 156.2],
    }
    assert all(
        all(support.values())
        for support in result["kicker_inner_edge_support"].values()
    )
    assert result["panel_plate_conflicts"] == []
    assert result["plate_plate_conflicts"] == []
    assert len(result["protected_screw_nominal_hole_path_conflicts"]) == 4
    assert len(result["nominal_hole_paths_missing_wood"]) == 4
    assert "header:base_side_left" in result["changed_wood_neighbor_conflicts"]
    assert "header:base_side_right" in result["changed_wood_neighbor_conflicts"]
    assert result["status"] == "nominal_installed_geometry_diagnostic_only"
    assert json.loads(RESULT.read_text()) == result
