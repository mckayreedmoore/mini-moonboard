"""Independent provisional PB-01 upright stack interval; no receiving release."""

import json

from scripts.simple_pb01_rail_receiving_envelope import evaluate_envelope


def screen() -> dict:
    """Try an 8-in partial-thread lead with independent invented limits."""
    assumptions = {
        "bolt_length_in": (7.95, 8.05),
        "wood_grip_in": (6.95, 7.05),
        "head_washer_in": (0.055, 0.075),
        "nut_washer_in": (0.055, 0.075),
        "nut_height_in": (0.20, 0.25),
        "first_complete_thread_in": (6.95, 7.05),
        "unusable_tip_in": (0.0, 0.125),
        "minimum_complete_thread_projection_in": 0.05,
    }
    return {
        "retail_lead": "Prime-Line 9058821, 1/4-20 x 8 in, A307 Grade A listing",
        "assumed_limits_not_product_tolerances": assumptions,
        "geometry": evaluate_envelope(**assumptions),
        "receiving_accepted": False,
        "stack_released": False,
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
