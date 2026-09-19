"""Actual narrow/opposing AB205 screen remains conditional."""

import json
from pathlib import Path

import pytest

from scripts.bolted_candidate_ab205_narrow_fit import screen_narrow_fit


def test_narrow_fit_matches_record_and_keeps_release_closed():
    actual = screen_narrow_fit()
    record = json.loads(
        Path("docs/bolted-candidate-prototypes/narrow-opposing.json").read_text()
    )
    assert actual == record["ab205_actual_geometry_trial"]
    assert actual["station"] == "clip_horizontal_bottom_left_2"
    assert actual["contact_xyz_mm"] == pytest.approx([-89.05, -49.688439, 405.542066])
    assert actual["rail_through_thickness_mm"] == pytest.approx(38.1)
    assert actual["clear_gap_between_center_principals_mm"] == pytest.approx(101.9)
    assert actual["rail_broad_face_nearest_edge_mm"] == pytest.approx(50.8)
    assert actual["rail_broad_face_four_d_edge_reserve_mm"] == pytest.approx(0)
    assert actual["principal_broad_face_four_d_edge_reserve_mm"] == pytest.approx(0)
    assert actual["common_conditional_four_d_shift_bounds_mm"] == pytest.approx(
        [0, 38.1]
    )
    assert actual["common_nominal_flange_shift_bounds_mm"] == pytest.approx(
        [-30.1625, 68.2625]
    )
    assert len(actual["holes"]) == 4
    assert actual["retained_axes_inspected"] == {
        "hillman_panel": 66,
        "bolt_clearance": 12,
    }
    assert actual["angle_placement_verified"] is False
    assert actual["drilling_released"] is False


@pytest.mark.parametrize("rail_leg", ["long", "short"])
@pytest.mark.parametrize("row_shift_mm", [0.0, 19.05])
def test_leg_and_bounded_row_trials(rail_leg, row_shift_mm):
    record = json.loads(
        Path("docs/bolted-candidate-prototypes/narrow-opposing.json").read_text()
    )
    trial = screen_narrow_fit(rail_leg, row_shift_mm)
    summary = next(
        item
        for item in record["ab205_orientation_and_row_trials"]
        if item["rail_leg"] == rail_leg and item["row_shift_mm"] == row_shift_mm
    )
    assert trial["station"] == record["station"]
    assert trial["contact_xyz_mm"] == pytest.approx(summary["contact_xyz_mm"])
    assert trial["rail_broad_face_four_d_edge_reserve_mm"] == pytest.approx(
        summary["rail_four_d_margin_mm"]
    )
    assert trial["principal_broad_face_four_d_edge_reserve_mm"] == pytest.approx(
        summary["principal_four_d_margin_mm"]
    )
    assert [hole["offset_from_bend_in"] for hole in trial["holes"]] == summary[
        "hole_offsets_from_bend_in"
    ]
    assert (
        sum(hole["raw_wood_full_bore_fraction"] == 1 for hole in trial["holes"])
        == summary["full_raw_wood_bores"]
        == 4
    )
    assert (
        trial["intersecting_retained_axis_ids"]
        == summary["retained_axis_intersections"]
        == []
    )
    assert trial["clear_gap_between_center_principals_mm"] == pytest.approx(101.9)
    assert all(
        hole["opposing_face_xyz_mm"][0] == pytest.approx(-50.95)
        for hole in trial["holes"][2:]
    )
    assert trial["drilling_released"] is False


def test_invalid_orientation_rejected():
    with pytest.raises(ValueError):
        screen_narrow_fit("other")


@pytest.mark.parametrize("shift", [-30.163, 68.263, float("nan"), float("inf")])
def test_unbounded_or_nonfinite_shift_rejected(shift):
    with pytest.raises(ValueError):
        screen_narrow_fit(row_shift_mm=shift)
