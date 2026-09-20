"""Provisional PB-01 rail stack interval; never a receiving or drilling release."""

import json
import math
from itertools import product


def _bounds(name: str, interval: tuple[float, float], *, positive: bool = False):
    if (
        not isinstance(interval, (tuple, list))
        or len(interval) != 2
        or any(
            isinstance(x, bool)
            or not isinstance(x, (int, float))
            or not math.isfinite(x)
            for x in interval
        )
        or interval[0] < 0
        or interval[1] < interval[0]
        or (positive and interval[0] <= 0)
    ):
        raise ValueError(f"invalid {name} interval")
    return interval


def evaluate_envelope(
    *,
    bolt_length_in: tuple[float, float],
    wood_grip_in: tuple[float, float],
    head_washer_in: tuple[float, float],
    nut_washer_in: tuple[float, float],
    nut_height_in: tuple[float, float],
    first_complete_thread_in: tuple[float, float],
    unusable_tip_in: tuple[float, float],
    minimum_complete_thread_projection_in: float,
) -> dict:
    """Bound an axial stack from the underside of the head, in inches.

    Intervals are independent trial limits, not SKU tolerances. Usable thread
    ends before the assumed incomplete tip. The nut needs complete thread at
    its inner and outer faces, plus the specified complete-thread projection.
    """
    length = _bounds("bolt length", bolt_length_in, positive=True)
    wood = _bounds("wood grip", wood_grip_in, positive=True)
    head = _bounds("head washer", head_washer_in, positive=True)
    washer = _bounds("nut washer", nut_washer_in, positive=True)
    nut = _bounds("nut height", nut_height_in, positive=True)
    first = _bounds("first complete thread", first_complete_thread_in)
    tip = _bounds("unusable tip", unusable_tip_in)
    if (
        isinstance(minimum_complete_thread_projection_in, bool)
        or not isinstance(minimum_complete_thread_projection_in, (int, float))
        or not math.isfinite(minimum_complete_thread_projection_in)
        or minimum_complete_thread_projection_in < 0
        or first[1] + tip[1] > length[0]
    ):
        raise ValueError("invalid usable thread or projection requirement")

    bearing = (head[0] + wood[0] + washer[0], head[1] + wood[1] + washer[1])
    outer = (bearing[0] + nut[0], bearing[1] + nut[1])
    usable_end = (length[0] - tip[1], length[1] - tip[0])
    complete_projection = (usable_end[0] - outer[1], usable_end[1] - outer[0])
    tip_projection = (length[0] - outer[1], length[1] - outer[0])
    wood_thread_cases = [
        max(0.0, min(h + g, e) - max(h, f))
        for h, g, f, e in product(head, wood, first, usable_end)
    ]
    complete_thread_in_wood = (min(wood_thread_cases), max(wood_thread_cases))

    return {
        "nut_bearing_plane_in": bearing,
        "nut_outer_face_in": outer,
        "usable_thread_end_in": usable_end,
        "tip_projection_in": tip_projection,
        "complete_thread_projection_in": complete_projection,
        "complete_thread_in_wood_in": complete_thread_in_wood,
        "full_nut_engagement_for_all_assumed_limits": first[1] <= bearing[0]
        and usable_end[0] >= outer[1],
        "minimum_projection_for_all_assumed_limits": complete_projection[0]
        >= minimum_complete_thread_projection_in,
    }


def screen() -> dict:
    """Try the 800676 rail lead against explicit, unverified limits."""
    assumptions = {
        "bolt_length_in": (4.95, 5.05),
        "wood_grip_in": (3.70, 3.80),
        "head_washer_in": (0.055, 0.075),
        "nut_washer_in": (0.055, 0.075),
        "nut_height_in": (0.20, 0.25),
        "first_complete_thread_in": (0.0, 0.25),
        "unusable_tip_in": (0.0, 0.125),
        "minimum_complete_thread_projection_in": 0.05,
    }
    return {
        "retail_lead": "Everbilt 800676, 1/4-20 x 5 in, listed fully threaded",
        "assumed_limits_not_product_tolerances": assumptions,
        "geometry": evaluate_envelope(**assumptions),
        "receiving_accepted": False,
        "stack_released": False,
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
