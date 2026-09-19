"""The outer-base AB205 trial is a geometry screen, never a release."""

import json
from pathlib import Path

import pytest

from scripts.bolted_candidate_ab205_outer_fit import screen_outer_fit


@pytest.mark.parametrize("side, sign", [("left", -1), ("right", 1)])
def test_outer_station_uses_raw_cad_and_retained_axes(side, sign):
    actual = screen_outer_fit(side)
    assert actual["station"] == f"clip_angle_base_{side}"
    assert actual["contact_x_mm"] == pytest.approx(sign * 1130.3)
    assert actual["contact_z_mm"] == pytest.approx(277)
    assert actual["contact_y_mm"] == pytest.approx(-105.85)
    assert actual["wood_bore_count"] == 4
    assert actual["nominal_wood_bore_diameter_mm"] == pytest.approx(14.2875)
    assert actual["raw_wood_bore_fractions"] == [1.0] * 4
    assert actual["rim_hole_min_4d_reserve_mm"] < 0
    assert actual["retained_axes_inspected"] == {
        "hillman_panel": 66,
        "bolt_clearance": 12,
    }
    assert actual["front_bolt_axis_ids"] == [
        f"rail_front_bolt_{side}_1",
        f"rail_front_bolt_{side}_2",
    ]
    assert actual["drilling_released"] is False
    assert actual["pad_clearance_verified"] is False
    assert actual["capacity_established"] is False


def test_fixture_matches_calculation_and_preserves_open_limits():
    record = json.loads(
        Path("docs/bolted-candidate-prototypes/outer-base.json").read_text()
    )
    for side in ("left", "right"):
        actual = screen_outer_fit(side)
        trial = record["ab205_nominal_trial"][side]
        for key, value in trial.items():
            assert value == actual[key]
    assert record["status"] == "incomplete_representative_prototype"
    assert record["engineering_disposition"] == "unresolved; geometry screen only"


@pytest.mark.parametrize("side", ["left", "right"])
def test_short_vertical_alternate_is_still_conditional(side):
    trial = screen_outer_fit(side, "short")
    assert trial["factory_vertical_offsets_in"] == [0.8125, 2.6875]
    assert trial["raw_wood_bore_fractions"] == [1.0] * 4
    assert trial["rim_hole_min_4d_reserve_mm"] < 0
    assert trial["rim_end_distance_classified"] is False
    assert trial["drilling_released"] is False
