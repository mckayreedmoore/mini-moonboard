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
    assert len(actual["holes"]) == 4
    assert actual["retained_axes_inspected"] == {
        "hillman_panel": 66,
        "bolt_clearance": 12,
    }
    assert actual["angle_placement_verified"] is False
    assert actual["drilling_released"] is False


def test_invalid_orientation_rejected():
    with pytest.raises(ValueError):
        screen_narrow_fit("other")
