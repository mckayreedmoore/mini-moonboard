"""Candidate-only center-support displacement screen."""

import json
from pathlib import Path

from scripts.bolted_candidate_center_shift import (
    _same_axis_geometry,
    screen_center_shift,
)

ROOT = Path(__file__).resolve().parents[1]


def test_width_packet_axis_comparison_ignores_status_prose_but_rejects_geometry():
    official = {
        "name": "center_panel_screw",
        "kind": "screw",
        "first_member": "main_lower_left",
        "second_member": "base_principal_center_left",
        "start_x_mm": "-70.0",
        "start_y_mm": "20.152907240539378",
        "start_z_mm": "322.0702100411935",
        "direction_x": "0.0",
        "direction_y": "-0.766044443118978",
        "direction_z": "0.6427876096865393",
        "modeled_length_mm": "50.8",
        "modeled_diameter_mm": "4.1402",
        "occupied_length_mm": "50.8",
        "occupied_diameter_mm": "4.1402",
        "shop_opening_kind": "hillman_panel",
        "shop_finished_opening_min_mm": "",
        "shop_finished_opening_max_mm": "",
        "assessment_status": "official width status",
    }
    kerf_right = {**official, "assessment_status": "kerf-right width status"}

    assert _same_axis_geometry([official], [kerf_right])
    assert not _same_axis_geometry([official], [{**kerf_right, "start_x_mm": "-65.0"}])


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
