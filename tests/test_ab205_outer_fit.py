"""The outer-base AB205 trial is a geometry screen, never a release."""

import json
from pathlib import Path

import pytest

from scripts.bolted_candidate_ab205_outer_fit import screen_outer_fit, search_outer_fit


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
    search_record = record["ab205_bounded_row_search"]
    for side in ("left", "right"):
        options = search_outer_fit(side)["orientations"]
        for name, option in options.items():
            saved = search_record[side][name]
            assert saved["y_band_mm"] == [
                option["reversible_4d_y_lower_mm"],
                option["reversible_4d_y_upper_mm"],
            ]
            assert saved["band_width_mm"] == option["reversible_4d_y_band_width_mm"]
            assert saved["trial_row_y_mm"] == option["trial_row_y_mm"]
            assert saved["row_displacement_mm"] == option["row_displacement_mm"]
            assert (
                saved["rim_min_4d_reserve_mm"] == option["rim_hole_min_4d_reserve_mm"]
            )
            assert saved["header_4d_reserve_mm"] == option["header_row_4d_reserve_mm"]
            assert saved["raw_wood_bore_fractions"] == option["raw_wood_bore_fractions"]
            assert (
                saved["intersecting_retained_axis_ids"]
                == option["intersecting_retained_axis_ids"]
            )
            assert (
                saved["conditional_4d_both_members"]
                == option["conditional_4d_both_members"]
            )
    assert search_record["frozen_panel_axes_moved"] is False
    assert search_record["rim_end_distance_classified"] is False
    assert search_record["drilling_released"] is False


@pytest.mark.parametrize("side", ["left", "right"])
def test_short_vertical_alternate_is_still_conditional(side):
    trial = screen_outer_fit(side, "short")
    assert trial["factory_vertical_offsets_in"] == [0.8125, 2.6875]
    assert trial["raw_wood_bore_fractions"] == [1.0] * 4
    assert trial["rim_hole_min_4d_reserve_mm"] < 0
    assert trial["rim_end_distance_classified"] is False
    assert trial["drilling_released"] is False


@pytest.mark.parametrize("side", ["left", "right"])
def test_bounded_orientation_and_row_search_on_raw_cad(side):
    result = search_outer_fit(side)
    assert result["legacy_row_y_mm"] == pytest.approx(-105.85)
    assert result["maximum_row_displacement_mm"] == 50
    assert set(result["orientations"]) == {"long_vertical", "short_vertical"}
    for name, expected_width in (("long_vertical", 0.148), ("short_vertical", 9.774)):
        option = result["orientations"][name]
        assert option["reversible_4d_y_band_width_mm"] == pytest.approx(
            expected_width, abs=0.002
        )
        assert option["trial_row_y_mm"] > result["legacy_row_y_mm"]
        assert option["conditional_4d_both_members"] is True
        assert option["installed_bores_full_raw_wood"] is True
        assert option["intersecting_retained_axis_ids"] == []
        assert option["retained_axes_inspected"] == {
            "hillman_panel": 66,
            "bolt_clearance": 12,
        }
        assert option["rim_end_distance_classified"] is False
        assert option["drilling_released"] is False


def test_search_displacement_cap_can_exclude_both_bands():
    result = search_outer_fit("left", max_row_displacement_mm=5)
    assert all(
        option["conditional_4d_both_members"] is False
        for option in result["orientations"].values()
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1.0])
def test_invalid_row_search_displacement_rejected(value):
    with pytest.raises(ValueError):
        search_outer_fit("left", max_row_displacement_mm=value)


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_nonfinite_trial_row_rejected(value):
    with pytest.raises(ValueError):
        screen_outer_fit("left", row_y_mm=value)
