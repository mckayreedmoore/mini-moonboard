"""Current PB-02 ten-bore stack and permanent occupancy sensitivity screen."""

import json
import math
from itertools import combinations

import cadquery as cq

from scripts import simple_center_combined_cleats_probe as combined
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_post_header_two_bolt_probe as current
from scripts import simple_center_second_bolt_tolerance_probe as prior
from scripts import simple_center_wide_post_probe as wide
from scripts.simple_pb01_thread_stack_screen import evaluate_grip_interval

MM_PER_IN = 25.4
GRIP_SENSITIVITY_IN = 0.05
WASHER_RANGE_IN = (0.050, 0.075)
NUT_RANGE_IN = (0.20, 0.25)
TIP_REQUIREMENT_IN = 0.25
# Trial lengths only. None identifies an accepted bolt or usable thread interval.
TRIAL_LENGTH_IN = {
    "post_cleat_1": 8,
    "post_cleat_2": 8,
    "cleat_header_1": 8,
    "cleat_header_2": 8,
    "header_cleat": 5,
    "cleat_principal": 5,
    "post_low": 6,
    "post_high": 6,
    "upright": 6,
    "cleat_link": 5,
}
PAIRS = {
    "header_cleat": ("principal_header_bottom", "principal_cleat_top"),
    "cleat_principal": ("principal_cleat_left", "principal_right"),
    "post_low": ("post_rear_low", "post_front_low"),
    "post_high": ("post_rear_high", "post_front_high"),
    "upright": ("upright_left", "upright_right"),
    "cleat_link": ("link_rear", "link_front"),
}
for index in (1, 2):
    PAIRS[f"post_cleat_{index}"] = (
        f"post_cleat_{index}_left",
        f"post_cleat_{index}_right",
    )
    PAIRS[f"cleat_header_{index}"] = (
        f"cleat_header_{index}_bottom",
        f"cleat_header_{index}_top",
    )


def _geometry():
    """Use the maintained tolerance pose, then apply the short block's four axes."""
    parts, bores, ends = prior._geometry()
    bottom, post_y, post_z, vertical_x = current.VARIANTS["shorter_8in_trial"]
    parts["header_post_side_cleat"] = cq.Solid.makeBox(
        88.9, 88.9, 238.9 - bottom, cq.Vector(177.65, -175.7, bottom)
    )
    for name in ("post_cleat", "cleat_header"):
        bores.pop(name)
    for name in (
        "post_left",
        "post_cleat_right",
        "post_cleat_bottom",
        "post_header_top",
    ):
        ends.pop(name)
    for index, z in enumerate(post_z, 1):
        name = f"post_cleat_{index}"
        bores[name] = combined.cylinder(
            wide.BORE_RADIUS, 177.8, (88.75, post_y, z), (1, 0, 0)
        )
        ends[f"{name}_left"] = ((88.75, post_y, z), (-1, 0, 0), "shifted_right_post")
        ends[f"{name}_right"] = (
            (266.55, post_y, z),
            (1, 0, 0),
            "header_post_side_cleat",
        )
    for index, x in enumerate(vertical_x, 1):
        name = f"cleat_header_{index}"
        bores[name] = combined.cylinder(
            wide.BORE_RADIUS, 277 - bottom, (x, -130, bottom), (0, 0, 1)
        )
        ends[f"{name}_bottom"] = (
            (x, -130, bottom),
            (0, 0, -1),
            "header_post_side_cleat",
        )
        ends[f"{name}_top"] = ((x, -130, 277), (0, 0, 1), "base_header")
    return parts, bores, ends


def screen(*, length_overrides=None):
    """Screen trial nominal lengths without selecting actual purchased bolts."""
    overrides = length_overrides or {}
    if set(overrides) - set(TRIAL_LENGTH_IN):
        raise ValueError("unknown center bolt in trial length override")
    if any(not math.isfinite(length) or length <= 0 for length in overrides.values()):
        raise ValueError("trial bolt lengths must be positive and finite")
    trial_lengths = TRIAL_LENGTH_IN | overrides
    parts, bores, ends = _geometry()
    _, screws = frame._fixed_screws()
    if set(bores) != set(PAIRS) or set(ends) != {
        end for pair in PAIRS.values() for end in pair
    }:
        raise ValueError("current center bore/end inventory changed")
    rows, occupancy = {}, {}
    for name, pair in PAIRS.items():
        near, far = (ends[end][0] for end in pair)
        grip_mm = sum(abs(a - b) for a, b in zip(near, far))
        length = trial_lengths[name]
        grip_in = grip_mm / MM_PER_IN
        common = {
            "bolt_length_in": length,
            "wood_grip_range_in": (
                grip_in - GRIP_SENSITIVITY_IN,
                grip_in + GRIP_SENSITIVITY_IN,
            ),
            "nut_height_range_in": NUT_RANGE_IN,
            "required_tip_projection_in": TIP_REQUIREMENT_IN,
        }
        # Seating is an upper bound on the first complete usable thread, not a claim it exists.
        latest_thread_start = grip_in - GRIP_SENSITIVITY_IN + 2 * WASHER_RANGE_IN[0]
        axial = evaluate_grip_interval(
            **common, washer_each_side_in=WASHER_RANGE_IN[1], usable_thread_start_in=0
        )
        max_tip_from_wood_mm = (
            length - (grip_in - GRIP_SENSITIVITY_IN) - WASHER_RANGE_IN[0]
        ) * MM_PER_IN
        rows[name] = {
            "wood_grip_mm": round(grip_mm, 3),
            "trial_length_in": length,
            "latest_usable_thread_start_in": round(latest_thread_start, 6),
            "minimum_projection_margin_in": axial[
                "maximum_grip_tip_projection_margin_in"
            ],
            "maximum_tip_from_wood_mm": round(max_tip_from_wood_mm, 3),
            "axial_length_screen_passes": axial["maximum_grip_tip_projection_margin_in"]
            >= 0,
            "actual_thread_nut_washer_verified": False,
        }
        for nut_end, head_end in (pair, pair[::-1]):
            point, outward, _ = ends[nut_end]
            occupancy[f"{name}:{nut_end}:tip"] = combined.cylinder(
                wide.BORE_RADIUS, max_tip_from_wood_mm, point, outward
            )
            occupancy[f"{name}:{nut_end}:washer_nut"] = combined.cylinder(
                10, (WASHER_RANGE_IN[1] + NUT_RANGE_IN[1]) * MM_PER_IN, point, outward
            )
            head_point, head_outward, _ = ends[head_end]
            occupancy[f"{name}:{head_end}:head"] = combined.cylinder(
                10, 5, head_point, head_outward
            )
    # Each orientation is a separate scenario; report wood/screw hits per end.
    per_end = {
        key: {
            "wood_hits_mm3": combined.hits({key: solid}, parts),
            "fixed_screw_hits_mm3": combined.hits({key: solid}, screws),
        }
        for key, solid in occupancy.items()
    }
    # Candidate collisions across distinct bolts; orientation compatibility is
    # intentionally unresolved and each reported pair needs an assembly choice.
    other_bolt_hits = {}
    for first, second in combinations(occupancy, 2):
        if first.split(":")[0] == second.split(":")[0]:
            continue
        a, b = occupancy[first].BoundingBox(), occupancy[second].BoundingBox()
        if (
            a.xmin >= b.xmax
            or b.xmin >= a.xmax
            or a.ymin >= b.ymax
            or b.ymin >= a.ymax
            or a.zmin >= b.zmax
            or b.zmin >= a.zmax
        ):
            continue
        if (volume := wide.hit_volume(occupancy[first], occupancy[second])) > wide.TOL:
            other_bolt_hits[f"{first}/{second}"] = round(volume, 5)
    return {
        "pose": "shorter_8in_trial; tolerance-pose principal block; ten current center bores",
        "block_bounds_mm": [177.65, 266.55, -175.7, -86.8, 95, 238.9],
        "rows": rows,
        "per_end_permanent_occupancy": per_end,
        "potential_other_bolt_permanent_hits_mm3": other_bolt_hits,
        "modeled_wood_and_fixed_screws_clear_both_orientations": all(
            not hits for end in per_end.values() for hits in end.values()
        ),
        "unknowns": [
            "actual bolt length and first/last complete usable thread",
            "nut height, engagement, washer thickness/diameter and bearing",
            "selected head/nut orientation and other installed bolt stacks",
            "socket internal tip depth, coupling, sweep, hand clearance and hold-and-turn access",
            "delivered stock, hole tolerances, load path and joint resistance",
        ],
        "procurement_or_drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
