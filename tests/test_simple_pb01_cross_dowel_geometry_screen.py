"""Focused connection checks for the PB01 retail cross-dowel lead."""

import pytest

from scripts.simple_pb01_cross_dowel_geometry_screen import connection_fit, screen


def test_nominal_hillman_body_has_a_bounded_offset_route_but_no_selected_connection():
    result = screen()
    assert result["hillman_nominal_mm"] == {
        "length": 16.002,
        "outside_diameter": 10.0076,
    }
    assert result["offset_interval_mm_not_hillman_specification"] == [6.0, 10.0]
    assert result["required_recess_interval_mm"] == pytest.approx([9.05, 13.05])
    assert result["minimum_nominal_wood_beyond_body_mm"] == pytest.approx(9.048)
    assert result["nominal_tip_beyond_axis_without_washer_mm"] == pytest.approx(18.9)
    assert result["nominal_tip_beyond_body_without_washer_mm"] == pytest.approx(13.8962)
    assert result["actual_hillman_axis_offset_known"] is False
    assert result["engagement_known"] is False
    assert result["structural_capacity_known"] is False
    assert result["selected"] is False


def test_measured_stack_can_close_geometry_but_never_structural_selection():
    fit = connection_fit(
        body_length_mm=16.002,
        body_od_mm=10.0076,
        axis_offset_mm=8.0,
        bolt_under_head_length_mm=127.0,
        washer_stack_mm=2.0,
        bolt_complete_thread_mm=(100.0, 126.0),
        nut_complete_thread_x_mm=(-3.0, 3.0),
        hole_depth_mm=126.0,
        required_tip_clearance_mm=1.0,
    )
    assert fit["recess_mm"] == pytest.approx(11.05)
    assert fit["tip_beyond_axis_mm"] == pytest.approx(16.9)
    assert fit["complete_thread_overlap_mm"] == pytest.approx(6.0)
    assert fit["tip_clearance_mm"] == pytest.approx(1.0)
    assert fit["geometry_fit"] is True
    assert fit["selected"] is False


def test_short_thread_or_bottomed_tip_fails_connection_fit():
    common = {
        "body_length_mm": 16.002,
        "body_od_mm": 10.0076,
        "axis_offset_mm": 8.0,
        "bolt_under_head_length_mm": 127.0,
        "washer_stack_mm": 2.0,
        "nut_complete_thread_x_mm": (-3.0, 3.0),
        "required_tip_clearance_mm": 1.0,
    }
    no_thread = connection_fit(
        **common, bolt_complete_thread_mm=(0.0, 100.0), hole_depth_mm=126.0
    )
    bottomed = connection_fit(
        **common, bolt_complete_thread_mm=(100.0, 126.0), hole_depth_mm=124.0
    )
    assert no_thread["complete_thread_overlap_mm"] == 0
    assert no_thread["geometry_fit"] is False
    assert bottomed["tip_clearance_mm"] == pytest.approx(-1.0)
    assert bottomed["geometry_fit"] is False


def test_offset_outside_body_or_thread_span_outside_barrel_is_rejected():
    common = {
        "body_length_mm": 16.002,
        "body_od_mm": 10.0076,
        "bolt_under_head_length_mm": 127.0,
        "washer_stack_mm": 2.0,
        "bolt_complete_thread_mm": (100.0, 126.0),
        "hole_depth_mm": 126.0,
        "required_tip_clearance_mm": 1.0,
    }
    with pytest.raises(ValueError):
        connection_fit(
            axis_offset_mm=14.0, nut_complete_thread_x_mm=(-3.0, 3.0), **common
        )
    with pytest.raises(ValueError):
        connection_fit(
            axis_offset_mm=8.0, nut_complete_thread_x_mm=(-6.0, 3.0), **common
        )
