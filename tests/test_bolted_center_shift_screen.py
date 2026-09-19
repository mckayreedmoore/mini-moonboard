"""Candidate-only center-support displacement screen."""

import json
from pathlib import Path

from scripts.bolted_candidate_center_shift import screen_center_shift

ROOT = Path(__file__).resolve().parents[1]


def test_outward_shift_retains_all_twenty_center_panel_axes() -> None:
    result = screen_center_shift((0, 5, 10, 15))
    assert result["status"] == "geometry_screen_only"
    assert result["panel_axis_source"].startswith(
        "docs/floor-flush-construction-kerf-right/"
    )
    assert result["official_width_relevant_axes_identical"] is True
    assert result["center_panel_axis_count"] == 20
    assert result["dependent_center_clip_station_count"] == 12
    assert result["dependent_lower_rail_inner_edges_mm"] == [-89.05, 89.05]
    assert len(result["dependent_rail_inner_edges_mm"]) == 6
    assert result["dependent_rail_panel_axis_count"] == 12
    assert [item["delta_mm"] for item in result["samples"]] == [0, 5, 10, 15]
    assert all(
        item["axes_intersecting_shifted_timber"] == 20 for item in result["samples"]
    )
    assert all(
        item["minimum_intersection_volume_mm3"] > 0 for item in result["samples"]
    )
    assert all(
        item["rail_axes_intersecting_recut_timber"] == 12 for item in result["samples"]
    )
    assert all(
        item["rail_end_faces_follow_shifted_supports"] for item in result["samples"]
    )
    assert result["samples"][0]["clear_gap_mm"] == 101.9
    assert result["samples"][2]["clear_gap_mm"] == 121.9
    assert result["selected_offset_mm"] is None
    published = json.loads(
        (
            ROOT / "docs/bolted-candidate-prototypes/center-support-solid-screen.json"
        ).read_text()
    )
    assert published == result


def test_shift_rejects_offset_that_loses_panel_bore_edge_material() -> None:
    result = screen_center_shift((17,))
    assert result["samples"][0]["geometrically_inside_support"] is False


def test_prior_both_member_shift_does_not_select_owner_post_only_change() -> None:
    record = json.loads(
        (
            ROOT / "docs/bolted-candidate-prototypes/center-support-outward-shift.json"
        ).read_text()
    )
    assert (
        record["status"]
        == "prior_both_member_shift_screen_not_selected_for_post_only_direction"
    )
    assert "only the two center box posts" in record["user_direction"]
    assert (
        "not the clarified post-only option"
        in record["symmetric_outward_shift_screen"]["definition"]
    )
    assert "no offset is selected or released" in record["disposition"]
