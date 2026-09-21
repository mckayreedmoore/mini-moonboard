"""Upright stack interval remains a measured-parts gate, not a selected bolt."""

import pytest

from scripts.simple_pb01_upright_receiving_envelope import screen


def test_upright_minimum_grip_seating_and_maximum_grip_projection():
    result = screen()
    geometry = result["geometry"]
    assert geometry["nut_bearing_plane_in"] == pytest.approx((7.06, 7.20))
    assert geometry["nut_outer_face_in"] == pytest.approx((7.26, 7.45))
    assert geometry["usable_thread_end_in"] == pytest.approx((7.825, 8.05))
    assert geometry["complete_thread_projection_in"] == pytest.approx((0.375, 0.79))
    assert geometry["full_nut_engagement_for_all_assumed_limits"] is True
    assert geometry["minimum_projection_for_all_assumed_limits"] is True
    assert geometry["complete_thread_in_wood_in"] == pytest.approx((0.0, 0.175))
    assert result["receiving_accepted"] is False
    assert result["drilling_released"] is False
