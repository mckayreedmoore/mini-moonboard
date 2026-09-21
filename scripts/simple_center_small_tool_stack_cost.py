"""PB-02 revised combined-center bore grips and illustrative retail basket."""

import json
import math
from collections import Counter
from decimal import Decimal

from scripts import simple_center_combined_small_tool_probe as pose
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_pb01_thread_stack_screen as stack


def report():
    """Use the current CAD cylinders and the existing axial interval checker."""
    x0, x1, y0, y1, z0, z1 = pose.CLEAT_BOUNDS
    parts = frame._parts() | {
        "header_post_side_cleat": pose.combined.NEW_WOOD["header_post_side_cleat"],
        "header_side_cleat": pose.cq.Solid.makeBox(
            x1 - x0, y1 - y0, z1 - z0, pose.cq.Vector(x0, y0, z0)
        ),
    }
    bores = (
        pose.combined.new_bores()
        | {
            "header_cleat": pose.combined.cylinder(
                pose.wide.BORE_RADIUS,
                z1 - 238.9,
                (15.475, pose.VERTICAL_Y, 238.9),
                (0, 0, 1),
            ),
            "cleat_principal": pose.combined.cylinder(
                pose.wide.BORE_RADIUS,
                89.05 - x0,
                (x0, pose.CROSS_Y, pose.CROSS_Z),
                (1, 0, 0),
            ),
        }
        | pose.combined.inherited_bores()
    )
    intended = pose.combined.INTENDED | {
        "post_low": ("rear_cleat", "shifted_right_post"),
        "post_high": ("rear_cleat", "shifted_right_post"),
        "upright": ("base_principal_center_right", "upright_side_cleat"),
        "cleat_link": ("rear_cleat", "upright_side_cleat"),
    }
    lengths = {"5": Decimal("0.62"), "6": Decimal("0.71"), "8": Decimal("0.94")}
    rows = []
    for name, bore in bores.items():
        grip_mm = round(bore.Volume() / (math.pi * pose.wide.BORE_RADIUS**2), 2)
        received = sum(
            pose.wide.hit_volume(bore, parts[wood]) for wood in intended[name]
        )
        if not math.isclose(received, bore.Volume(), rel_tol=1e-6):
            raise ValueError(f"{name}: CAD bore is not fully in its two intended woods")
        grip_in = grip_mm / 25.4
        # The ±0.05 in range is an assumed axial sensitivity, not a wood tolerance.
        candidates = []
        for length in (5, 6, 8):
            common = {
                "bolt_length_in": length,
                "wood_grip_range_in": (grip_in - 0.05, grip_in + 0.05),
                "usable_thread_start_in": 0.25 if length < 8 else 2.0,
                "nut_height_range_in": (0.20, 0.25),
                "required_tip_projection_in": 0.25,
            }
            thin = stack.evaluate_grip_interval(**common, washer_each_side_in=0.05)
            thick = stack.evaluate_grip_interval(**common, washer_each_side_in=0.075)
            if (
                thin["minimum_grip_seating_margin_in"] >= 0
                and thick["maximum_grip_tip_projection_margin_in"] >= 0
            ):
                candidates.append((length, thin, thick))
        if not candidates:
            raise ValueError(f"{name}: no listed trial length passes")
        length, thin, thick = candidates[0]
        rows.append(
            {
                "axis": name,
                "wood_grip_mm": grip_mm,
                "wood_grip_in": round(grip_in, 4),
                "trial_bolt_in": length,
                "seating_margin_in": thin["minimum_grip_seating_margin_in"],
                "projection_margin_in": thick["maximum_grip_tip_projection_margin_in"],
                "interval_passes": True,
            }
        )
    quantities = Counter(str(row["trial_bolt_in"]) for row in rows)
    bolt_cost = sum(
        (lengths[key] * count for key, count in quantities.items()), Decimal(0)
    )
    old = stack.evaluate_grip_interval(
        bolt_length_in=6,
        wood_grip_range_in=(141.1 / 25.4 - 0.05, 141.1 / 25.4 + 0.05),
        washer_each_side_in=0.075,
        usable_thread_start_in=0.25,
        nut_height_range_in=(0.20, 0.25),
        required_tip_projection_in=0.25,
    )
    return {
        "axes": rows,
        "trial_bolt_quantities": dict(sorted(quantities.items())),
        "rejected_pose_141_1_mm_on_6_in": old,
        "hardware_usd": {
            "bolts": str(bolt_cost),
            "allocated": str(bolt_cost + 8 * Decimal("1.98") / 12 + Decimal("1.98")),
            "first_checkout": str(bolt_cost + 2 * Decimal("1.98")),
            "delta_from_published_rejected_pose_basket": str(
                bolt_cost - Decimal("5.96")
            ),
        },
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
