"""Compare the PB01 bolted solid-wood corner block length trial without load transfer."""

import json
import math

from scripts.simple_pb01_quarter_member_screen import screen as member_screen
from scripts.simple_pb01_thread_stack_screen import screen as stack_screen
from scripts.simple_rail_joint_comparison import (
    PB01_GROUP_TRIAL_SIZE_MM,
    compare,
)

POSE = "cleat_grain_n_4x6_group_quarter"


def screen() -> dict:
    baseline = compare()
    trial = compare(quarter_n_length=PB01_GROUP_TRIAL_SIZE_MM[2])
    before, after = baseline[POSE], trial[POSE]
    if baseline["fixed_panel_axes"] != 66 or trial["fixed_panel_axes"] != 66:
        raise ValueError("fixed panel inventory changed")
    fixed = (
        "adjusted_front_n_mm",
        "upright_bolt_n_centers_mm",
        "rail_bolt_n_centers_mm",
        "rail_bolt_x_from_butt_mm",
        "trial_envelope_grips_mm_not_purchased_lengths",
        "nominal_face_contact_area_mm2",
    )
    if any(before[key] != after[key] for key in fixed):
        raise ValueError("fixed PB01 datum, centers, grip, or contact changed")
    if before["size_local_x_t_n_mm"][:2] != after["size_local_x_t_n_mm"][:2]:
        raise ValueError("X/T section changed")
    front = after["adjusted_front_n_mm"]
    rear = front + PB01_GROUP_TRIAL_SIZE_MM[2]
    last_upright = max(after["upright_bolt_n_centers_mm"])
    diameter = after["nominal_trial_bolt_diameter_mm_not_selected"]
    stack = stack_screen()
    wood_grips = {
        family: after["trial_envelope_grips_mm_not_purchased_lengths"][key] - 5
        for family, key in (("upright", "u1"), ("rail", "r1"))
    }
    if any(
        abs(wood_grips[family] / 25.4 - stack[family]["wood_grip_in"]) > 1e-6
        for family in wood_grips
    ):
        raise ValueError("wood grips differ from stack screen")
    before_member = member_screen(baseline)
    trial_member = member_screen(trial)
    return {
        "member_label": "bolted solid-wood corner block",
        "machine_pose": POSE,
        "geometry": {
            "before_x_t_n_mm": before["size_local_x_t_n_mm"],
            "trial_x_t_n_mm": after["size_local_x_t_n_mm"],
            "front_n_mm": front,
            "trial_rear_n_mm": round(rear, 3),
            "upright_bolt_n_mm": after["upright_bolt_n_centers_mm"],
            "rail_bolt_n_mm": after["rail_bolt_n_centers_mm"],
            "rail_bolt_x_mm": after["rail_bolt_x_from_butt_mm"],
            "bore_diameter_mm_trial_not_drill_instruction": after[
                "diagnostic_wood_bore_diameter_mm_not_drill_instruction"
            ],
            "fixed_panel_axes": trial["fixed_panel_axes"],
            "contact_area_before_mm2": before["measured_face_contact_area_mm2"],
            "contact_area_trial_mm2": after["measured_face_contact_area_mm2"],
            "trial_rear_end_from_last_upright_bolt_mm": round(rear - last_upright, 3),
            "conditional_7d_rear_reserve_mm": round(
                rear - last_upright - 7 * diameter, 3
            ),
            "status": after["status"],
            "parent_clashes_mm3": after["cleat_parent_clashes_mm3"],
            "panel_clashes_mm3": after["cleat_panel_clashes_mm3"],
            "host_clashes_mm3": after["cleat_host_clashes_mm3"],
            "protected_axis_clashes_mm3": after["protected_axis_envelope_clashes_mm3"],
        },
        "member": {
            "before_components_lbf": before_member["components_lbf"],
            "trial_components_lbf": trial_member["components_lbf"],
            "conditional_only": True,
            "joint_capacity_lbf": None,
            "rear_end_and_bored_section_check_complete": False,
        },
        "stack": {
            "wood_grips_mm": wood_grips,
            "grips_unchanged_mm": after[
                "trial_envelope_grips_mm_not_purchased_lengths"
            ],
            "rail_nominal": stack["rail"]["nominal"],
            "upright_nominal": stack["upright"]["nominal"],
            "purchased_lengths_selected": False,
        },
        "cost": {
            "volume_before_mm3": round(math.prod(before["size_local_x_t_n_mm"]), 3),
            "volume_trial_mm3": round(math.prod(after["size_local_x_t_n_mm"]), 3),
            "volume_reduction_percent": round(
                100
                * (
                    1
                    - after["size_local_x_t_n_mm"][2] / before["size_local_x_t_n_mm"][2]
                ),
                2,
            ),
            "hardware_count_unchanged": True,
            "installed_cost_usd": None,
            "stock_yield_and_price_verified": False,
        },
        "native_forces_transferred": False,
        "joint_accepted": False,
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
