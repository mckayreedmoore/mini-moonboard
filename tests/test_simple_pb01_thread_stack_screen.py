"""PB-01 thread placement stays conditional and fails closed."""

import math

import pytest

from scripts.simple_pb01_thread_stack_screen import (
    evaluate_grip_interval,
    evaluate_stack,
    screen,
)


def test_minimum_grip_seating_and_maximum_grip_projection_are_separate():
    rail = evaluate_grip_interval(
        bolt_length_in=5,
        wood_grip_range_in=(3.70, 3.80),
        washer_each_side_in=0.065,
        usable_thread_start_in=0.25,
        nut_height_range_in=(0.20, 0.25),
        required_tip_projection_in=0.25,
    )
    assert rail["minimum_grip_nut_bearing_plane_in"] == pytest.approx(3.83)
    assert rail["maximum_grip_nut_bearing_plane_in"] == pytest.approx(3.93)
    assert rail["minimum_grip_seating_margin_in"] == pytest.approx(3.58)
    assert rail["maximum_grip_tip_projection_margin_in"] == pytest.approx(0.57)
    assert rail["passes_assumed_interval"] is True
    failed = evaluate_grip_interval(
        bolt_length_in=5,
        wood_grip_range_in=(3.70, 3.80),
        washer_each_side_in=0.065,
        usable_thread_start_in=4.25,
        nut_height_range_in=(0.20, 0.25),
        required_tip_projection_in=0.25,
    )
    assert failed["minimum_grip_seating_margin_in"] == pytest.approx(-0.42)
    assert failed["passes_assumed_interval"] is False


@pytest.mark.parametrize(
    "grip,nut,start",
    [
        ((3.8, 3.7), (0.2, 0.25), 0.25),
        ((3.7, 3.8), (0.25, 0.2), 0.25),
        ((3.7, 3.8), (0.2, 0.25), math.nan),
    ],
)
def test_grip_interval_rejects_invalid_dimensions(grip, nut, start):
    with pytest.raises(ValueError):
        evaluate_grip_interval(
            bolt_length_in=5,
            wood_grip_range_in=grip,
            washer_each_side_in=0.065,
            usable_thread_start_in=start,
            nut_height_range_in=nut,
            required_tip_projection_in=0.25,
        )


def test_prime_line_two_sided_intervals():
    result = screen()
    rail = result["rail"]
    upright = result["upright"]

    assert rail["bearing_plane_in"] == pytest.approx(3.88)
    assert rail["nominal"]["thread_start_in"] == pytest.approx(4.25)
    assert rail["nominal"]["thread_shortfall_in"] == pytest.approx(0.37)
    assert rail["nominal"]["nut_thread_engagement_in"] == pytest.approx([0, 0])
    assert rail["nominal"]["tip_projection_after_nut_in"] == pytest.approx([0.87, 0.92])
    assert rail["hypothetical_transition"]["thread_start_in"] == pytest.approx(4.00)
    assert rail["hypothetical_transition"]["thread_shortfall_in"] == pytest.approx(0.12)
    assert rail["hypothetical_transition"]["nut_thread_engagement_in"] == pytest.approx(
        [0.08, 0.13]
    )
    assert rail["hypothetical_transition"]["full_nut_on_thread"] is False

    assert upright["bearing_plane_in"] == pytest.approx(7.13)
    assert upright["nominal"]["thread_start_in"] == pytest.approx(7.00)
    assert upright["nominal"]["thread_shortfall_in"] == 0
    assert upright["nominal"]["nut_thread_engagement_in"] == pytest.approx([0.20, 0.25])
    assert upright["nominal"]["tip_projection_after_nut_in"] == pytest.approx(
        [0.62, 0.67]
    )
    assert upright["nominal"]["full_nut_on_thread"] is True
    assert result["stack_released"] is False
    assert result["drilling_released"] is False


@pytest.mark.parametrize(
    "overrides",
    [
        {"bolt_length_in": 0},
        {"wood_grip_in": -1},
        {"washer_in": math.nan},
        {"thread_length_in": 6},
        {"nut_height_range_in": (0.25, 0.20)},
        {"nut_height_range_in": (0.20, math.inf)},
        {"nut_height_range_in": (0.20,)},
        {"transition_in": -0.01},
        {"transition_in": 4.26},
        {"wood_grip_in": 4.9},
    ],
)
def test_invalid_or_unseatable_inputs_fail_closed(overrides):
    inputs = {
        "bolt_length_in": 5.0,
        "wood_grip_in": 3.75,
        "washer_in": 0.065,
        "thread_length_in": 0.75,
        "nut_height_range_in": (0.20, 0.25),
        "transition_in": 0.0,
    }
    inputs.update(overrides)
    with pytest.raises(ValueError):
        evaluate_stack(**inputs)
