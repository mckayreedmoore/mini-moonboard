"""BR904 search geometry is not a measured or approved joint."""

import pytest

from scripts.bolted_candidate_br904_center_envelope import screen_center_envelope


@pytest.mark.parametrize(
    ("diameter", "expected_ray_margin", "minimum_band"),
    [(12.7, 0.58, 1.8), (11.1125, 6.14, 16.4)],
)
def test_trial_layout_has_only_a_conditional_search_envelope(
    diameter, expected_ray_margin, minimum_band
):
    result = screen_center_envelope(diameter, 34.5, 36.5125)
    assert result["factory_vertical_offset_verified"] is False
    assert result["factory_horizontal_offset_verified"] is False
    assert result["hole_pitch_mm"] == pytest.approx(47.625)
    assert result["pitch_applies_to_both_legs_verified"] is False
    assert result["nearest_ray_proxy_margin_mm"] == pytest.approx(
        expected_ray_margin, abs=0.01
    )
    assert result["reversible_4d_band_width_mm"] >= minimum_band
    assert result["end_distance_classified"] is False
    assert result["drilling_released"] is False


def test_half_inch_trial_loses_ray_proxy_margin_to_possible_factory_hole_play():
    result = screen_center_envelope(12.7, 34.5, 36.5125)
    assert result["factory_hole_radial_clearance_mm"] == pytest.approx(0.79375)
    assert result["ray_proxy_margin_after_radial_hole_play_mm"] < 0


def test_trial_inputs_must_not_exceed_known_factory_hole() -> None:
    with pytest.raises(ValueError, match="bolt diameter"):
        screen_center_envelope(15, 34.5, 36.5125)
