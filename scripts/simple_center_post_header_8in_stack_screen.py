"""Bounded PB-02 vertical-bolt axial screen; no hardware selection."""

import json

from scripts.simple_pb01_thread_stack_screen import evaluate_grip_interval


def screen() -> dict:
    """Compare the two wood grips with two published 8-in thread-length leads."""
    cases = {}
    for label, grip_mm in (("grip_202_mm", 202), ("grip_182_mm", 182)):
        grip_in = grip_mm / 25.4
        cases[label] = {}
        for lead, assumed_start in (
            ("everbilt_800696", 2.0),
            ("prime_line_9058821", 7.0),
        ):
            common = {
                "bolt_length_in": 8.0,
                "wood_grip_range_in": (grip_in - 0.05, grip_in + 0.05),
                "usable_thread_start_in": assumed_start,
                "nut_height_range_in": (0.20, 0.25),
                "required_tip_projection_in": 0.25,
            }
            # Reuse the existing limiting-plane helper for each washer bound.
            seat = evaluate_grip_interval(**common, washer_each_side_in=0.050)
            tip = evaluate_grip_interval(**common, washer_each_side_in=0.075)
            cases[label][lead] = {
                "assumed_usable_thread_start_in": assumed_start,
                "thin_washer_seating": seat,
                "thick_washer_tip": tip,
                "passes_assumed_interval": (
                    seat["minimum_grip_seating_margin_in"] >= 0
                    and tip["maximum_grip_tip_projection_margin_in"] >= 0
                ),
            }
        cases[label]["minimum_nominal_length_at_max_sensitivity_in"] = round(
            grip_in + 0.05 + 2 * 0.075 + 0.25 + 0.25, 6
        )
        # Illustrations only: no 9/10-in SKU or delivered thread was verified.
        cases[label]["illustrative_one_inch_tip_thread"] = {
            f"{length}_in": evaluate_grip_interval(
                bolt_length_in=length,
                wood_grip_range_in=(grip_in - 0.05, grip_in + 0.05),
                washer_each_side_in=0.050,
                usable_thread_start_in=length - 1.0,
                nut_height_range_in=(0.20, 0.25),
                required_tip_projection_in=0.25,
            )
            for length in (9, 10)
        }
    cases["selected_purchase"] = False
    cases["strength_verified"] = False
    cases["drilling_released"] = False
    return cases


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
