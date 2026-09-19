"""Candidate-only center-support displacement screen."""

from scripts.bolted_candidate_center_shift import screen_center_shift


def test_outward_shift_retains_all_twenty_center_panel_axes() -> None:
    result = screen_center_shift((0, 5, 10, 15))
    assert result["status"] == "geometry_screen_only"
    assert result["center_panel_axis_count"] == 20
    assert [item["delta_mm"] for item in result["samples"]] == [0, 5, 10, 15]
    assert all(item["axes_intersecting_shifted_timber"] == 20 for item in result["samples"])
    assert all(item["minimum_intersection_volume_mm3"] > 0 for item in result["samples"])
    assert result["samples"][0]["clear_gap_mm"] == 101.9
    assert result["samples"][2]["clear_gap_mm"] == 121.9
    assert result["selected_offset_mm"] is None


def test_shift_rejects_offset_that_loses_panel_bore_edge_material() -> None:
    result = screen_center_shift((17,))
    assert result["samples"][0]["geometrically_inside_support"] is False
