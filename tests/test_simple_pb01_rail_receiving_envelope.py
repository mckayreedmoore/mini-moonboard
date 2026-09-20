"""The Everbilt rail lead remains conditional across the whole trial box."""

import pytest

from scripts.simple_pb01_rail_receiving_envelope import evaluate_envelope, screen


def test_trial_extremes_and_release_boundary():
    result = screen()
    geometry = result["geometry"]
    assert geometry["nut_bearing_plane_in"] == pytest.approx((3.81, 3.95))
    assert geometry["nut_outer_face_in"] == pytest.approx((4.01, 4.20))
    assert geometry["usable_thread_end_in"] == pytest.approx((4.825, 5.05))
    assert geometry["tip_projection_in"] == pytest.approx((0.75, 1.04))
    assert geometry["complete_thread_projection_in"] == pytest.approx((0.625, 1.04))
    assert geometry["complete_thread_in_wood_in"] == pytest.approx((3.505, 3.80))
    assert geometry["full_nut_engagement_for_all_assumed_limits"] is True
    assert geometry["minimum_projection_for_all_assumed_limits"] is True
    assert result["receiving_accepted"] is False
    assert result["stack_released"] is False
    assert result["drilling_released"] is False


@pytest.mark.parametrize(
    "change, failed_gate",
    [
        (
            {"first_complete_thread_in": (3.9, 4.0)},
            "full_nut_engagement_for_all_assumed_limits",
        ),
        ({"unusable_tip_in": (0.8, 0.8)}, "full_nut_engagement_for_all_assumed_limits"),
        (
            {"minimum_complete_thread_projection_in": 0.7},
            "minimum_projection_for_all_assumed_limits",
        ),
    ],
)
def test_adverse_limits_fail_the_respective_gate(change, failed_gate):
    inputs = screen()["assumed_limits_not_product_tolerances"] | change
    assert evaluate_envelope(**inputs)[failed_gate] is False


def test_invalid_interval_is_rejected():
    inputs = screen()["assumed_limits_not_product_tolerances"] | {
        "wood_grip_in": (3.8, 3.7)
    }
    with pytest.raises(ValueError):
        evaluate_envelope(**inputs)


def test_wood_thread_occupancy_stops_at_last_usable_thread():
    inputs = screen()["assumed_limits_not_product_tolerances"] | {
        "bolt_length_in": (4.0, 4.0),
        "first_complete_thread_in": (0.0, 0.0),
        "unusable_tip_in": (0.5, 0.5),
    }
    result = evaluate_envelope(**inputs)
    assert result["usable_thread_end_in"] == (3.5, 3.5)
    assert result["complete_thread_in_wood_in"] == pytest.approx((3.425, 3.445))
