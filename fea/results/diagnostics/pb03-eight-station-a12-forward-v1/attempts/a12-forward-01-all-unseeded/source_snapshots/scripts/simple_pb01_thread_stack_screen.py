"""Bounded PB-01 bolt thread/stack geometry; no product or drilling release."""

import json
import math


def evaluate_grip_interval(
    *,
    bolt_length_in: float,
    wood_grip_range_in: tuple[float, float],
    washer_each_side_in: float,
    usable_thread_start_in: float,
    nut_height_range_in: tuple[float, float],
    required_tip_projection_in: float,
) -> dict:
    """Check limiting nut seating and projection for an assumed grip interval.

    This axial test does not establish a retail bolt's actual usable threads,
    nut strength, washer classification, or a construction tolerance.
    """
    if len(wood_grip_range_in) != 2 or len(nut_height_range_in) != 2:
        raise ValueError("grip and nut intervals must each have two bounds")
    grip_min, grip_max = wood_grip_range_in
    nut_min, nut_max = nut_height_range_in
    dimensions = (
        bolt_length_in,
        grip_min,
        grip_max,
        washer_each_side_in,
        usable_thread_start_in,
        nut_min,
        nut_max,
        required_tip_projection_in,
    )
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in dimensions
    ):
        raise ValueError("stack dimensions must be finite numbers")
    if (
        min(bolt_length_in, grip_min, washer_each_side_in, nut_min) <= 0
        or grip_max < grip_min
        or nut_max < nut_min
        or usable_thread_start_in < 0
        or required_tip_projection_in < 0
    ):
        raise ValueError("invalid grip or hardware dimensions")
    minimum_bearing = grip_min + 2 * washer_each_side_in
    maximum_bearing = grip_max + 2 * washer_each_side_in
    seating_margin = minimum_bearing - usable_thread_start_in
    projection_margin = (
        bolt_length_in - maximum_bearing - nut_max - required_tip_projection_in
    )
    return {
        "minimum_grip_nut_bearing_plane_in": round(minimum_bearing, 6),
        "maximum_grip_nut_bearing_plane_in": round(maximum_bearing, 6),
        "minimum_grip_seating_margin_in": round(seating_margin, 6),
        "maximum_grip_tip_projection_margin_in": round(projection_margin, 6),
        "passes_assumed_interval": seating_margin >= 0 and projection_margin >= 0,
    }


def evaluate_stack(
    *,
    bolt_length_in: float,
    wood_grip_in: float,
    washer_in: float,
    thread_length_in: float,
    nut_height_range_in: tuple[float, float],
    transition_in: float,
) -> dict:
    """Screen a nominal underside-of-head axis with two equal washers.

    A positive transition is a hypothetical earlier effective thread start,
    not a measured usable-thread allowance for any retail SKU.
    """
    if (
        not isinstance(nut_height_range_in, (tuple, list))
        or len(nut_height_range_in) != 2
    ):
        raise ValueError("nut height interval must have two bounds")
    values = (
        bolt_length_in,
        wood_grip_in,
        washer_in,
        thread_length_in,
        transition_in,
        *nut_height_range_in,
    )
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in values
    ):
        raise ValueError("stack inputs must be finite numbers")
    low_nut, high_nut = nut_height_range_in
    if (
        min(bolt_length_in, wood_grip_in, washer_in, thread_length_in, low_nut) <= 0
        or high_nut < low_nut
        or thread_length_in > bolt_length_in
        or not 0 <= transition_in <= bolt_length_in - thread_length_in
    ):
        raise ValueError("invalid stack dimension or interval")

    wood_end = washer_in + wood_grip_in
    bearing = wood_end + washer_in
    if bearing + high_nut > bolt_length_in:
        raise ValueError("nominal bolt cannot contain washer and full nut interval")

    thread_start = bolt_length_in - thread_length_in - transition_in

    # ponytail: axial overlap only; usable threads and nut seating need measurement.
    def engagement(nut_height: float) -> float:
        return min(nut_height, max(0.0, bearing + nut_height - thread_start))

    return {
        "bearing_plane_in": round(bearing, 6),
        "thread_start_in": round(thread_start, 6),
        "thread_shortfall_in": round(max(0.0, thread_start - bearing), 6),
        "thread_in_wood_in": round(
            max(0.0, wood_end - max(washer_in, thread_start)), 6
        ),
        "nut_thread_engagement_in": [
            round(engagement(n), 6) for n in (low_nut, high_nut)
        ],
        "tip_projection_after_nut_in": [
            round(bolt_length_in - bearing - n, 6) for n in (high_nut, low_nut)
        ],
        "full_nut_on_thread": thread_start <= bearing,
    }


def screen() -> dict:
    """Run the specified Prime-Line nominal pattern and one transition sensitivity."""
    cases = {
        "rail": (5.0, 3.75, 0.75),
        "upright": (8.0, 7.00, 1.00),
    }
    result = {}
    for name, (length, grip, thread_length) in cases.items():
        common = {
            "bolt_length_in": length,
            "wood_grip_in": grip,
            "washer_in": 0.065,
            "thread_length_in": thread_length,
            "nut_height_range_in": (0.20, 0.25),
        }
        nominal = evaluate_stack(**common, transition_in=0)
        hypothetical = evaluate_stack(**common, transition_in=0.25)
        result[name] = {
            "bolt_length_in": length,
            "wood_grip_in": grip,
            "assumed_nominal_thread_length_in": thread_length,
            "bearing_plane_in": nominal["bearing_plane_in"],
            "nominal": nominal,
            "hypothetical_transition": hypothetical,
        }
    # Illustrative ±0.05-in wood-grip development envelope, not a measured
    # fabrication tolerance or a published dimension of either retail bolt.
    result["provisional_interval_examples"] = {
        "rail_fully_threaded_assumed": evaluate_grip_interval(
            bolt_length_in=5,
            wood_grip_range_in=(3.70, 3.80),
            washer_each_side_in=0.065,
            usable_thread_start_in=0.25,
            nut_height_range_in=(0.20, 0.25),
            required_tip_projection_in=0.25,
        ),
        "rail_prime_line_nominal": evaluate_grip_interval(
            bolt_length_in=5,
            wood_grip_range_in=(3.70, 3.80),
            washer_each_side_in=0.065,
            usable_thread_start_in=4.25,
            nut_height_range_in=(0.20, 0.25),
            required_tip_projection_in=0.25,
        ),
        "upright_prime_line_nominal": evaluate_grip_interval(
            bolt_length_in=8,
            wood_grip_range_in=(6.95, 7.05),
            washer_each_side_in=0.065,
            usable_thread_start_in=7.00,
            nut_height_range_in=(0.20, 0.25),
            required_tip_projection_in=0.25,
        ),
    }
    return {
        **result,
        "washer_each_side_in": 0.065,
        "assumed_nut_height_range_in": [0.20, 0.25],
        "hypothetical_transition_in": 0.25,
        "stack_released": False,
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
