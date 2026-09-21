"""Focused PB01 short-block net-section geometry checks."""

import math

import pytest

from scripts.simple_pb01_short_bored_section_probe import screen


def test_critical_grain_normal_sections_use_all_four_pose_bores():
    result = screen()
    assert result["variant"] == "quarter_short"
    assert result["fixed_panel_axes"] == 66
    assert result["bore_names"] == ["u1", "u2", "r1", "r2"]
    assert result["diameter_mm_diagnostic_only"] == 7.5
    assert result["size_x_t_n_mm"] == [139.7, 57.15, 152.4]
    assert result["grain_normal_planes_n_mm"] == [265.0, 290.0, 310.0]
    cuts = result["sections"]
    gross = 139.7 * 57.15
    for index in (0, 2):
        row = cuts[index]
        assert row["bore_names"] == [["u1"], ["u2"]][index // 2]
        assert row["removed_area_mm2"] == pytest.approx(139.7 * 7.5)
        assert row["net_area_mm2"] == pytest.approx(gross - 139.7 * 7.5)
        assert row["centroid_x_t_mm"] == pytest.approx([69.85, 28.575])
        assert row["principal_second_moments_mm4"] == pytest.approx(
            sorted(
                [
                    139.7 * (57.15**3 - 7.5**3) / 12,
                    (57.15 - 7.5) * 139.7**3 / 12,
                ]
            )
        )
    rail = cuts[1]
    assert rail["bore_names"] == ["r1", "r2"]
    assert rail["removed_area_mm2"] == pytest.approx(2 * 7.5 * 57.15)
    assert rail["net_area_mm2"] == pytest.approx(gross - 2 * 7.5 * 57.15)
    assert rail["centroid_x_t_mm"][0] < 69.85
    assert rail["centroid_x_t_mm"][1] == pytest.approx(28.575)
    assert rail["principal_second_moments_mm4"][0] == pytest.approx(
        (139.7 - 15) * 57.15**3 / 12
    )
    assert result["minimum_net_area_mm2"] == pytest.approx(cuts[0]["net_area_mm2"])
    assert result["material_strength_assessed"] is False
    assert result["wall_tearout_splitting_assessed"] is False
    assert result["capacity_n"] is None
    assert result["drilling_released"] is False


def test_section_moments_are_positive_and_less_than_gross():
    result = screen()
    gross_x = 139.7 * 57.15**3 / 12
    gross_t = 57.15 * 139.7**3 / 12
    for row in result["sections"]:
        assert 0 < row["net_area_mm2"] < result["gross_area_mm2"]
        assert all(
            math.isfinite(v) and v > 0 for v in row["principal_second_moments_mm4"]
        )
        assert row["principal_second_moments_mm4"][0] < gross_x
        assert row["principal_second_moments_mm4"][1] < gross_t
