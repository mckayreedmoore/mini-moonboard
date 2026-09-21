"""Direct checks for the PB01 cross-dowel offset sensitivity."""

import pytest

from scripts.simple_pb01_cross_dowel_followup import screen


def test_offset_can_be_measured_then_absorbed_by_recess_without_moving_thread_axis():
    result = screen()
    assert result["analog_offset_range_mm_not_hillman_specification"] == [6.0, 10.0]
    assert result["all_cases_preserve_target_axis"]
    assert result["all_cases_nominally_fit"]
    assert result["minimum_wood_beyond_body_mm"] == pytest.approx(9.048)
    assert [case["required_body_recess_mm"] for case in result["cases"]] == (
        pytest.approx([13.05, 11.049, 9.05])
    )
    assert [case["cross_bore_depth_mm"] for case in result["cases"]] == (
        pytest.approx([29.052, 27.051, 25.052])
    )
    assert result["development_geometry_advance"] is True
    assert result["structural_advance"] is False
    assert result["hillman_thread_axis_established"] is False
    assert result["effective_thread_engagement_established"] is False
    assert result["steel_grade_or_strength_established"] is False
    assert result["wood_bearing_capacity_established"] is False
    assert result["fabrication_or_drilling_released"] is False
