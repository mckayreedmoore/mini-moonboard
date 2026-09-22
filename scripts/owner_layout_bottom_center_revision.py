"""One detached 77-mm-X same-side bottom-center pose; owner layout only."""

import json
import math

from scripts import owner_layout_bottom_center_pair as first

SOURCE_ID = "owner-bottom-center-pair-x180-77x139p7-layout-v2"
BLOCK_X_MM = 77.0
RAIL_X_MM = (26.0, 51.0)


def principal_tool_reserve_gate():
    """Bound the 77-mm right pose with its provisional G1 path and 40-mm tool.

    This is a necessary 2D occupied-space screen, not a complete CAD or NDS
    joint check. Its datums are the source-bound values in the revision note.
    """
    if first.BLOCK_T_MM != 57.15 or first.BLOCK_N_MM != 139.7:
        raise ValueError("Bottom-center block envelope changed")
    bolt_diameter = 6.35
    four_d = 4 * bolt_diameter
    washer_radius = 12.7
    tool_radius = 20.0
    hold_radius = 5.55625
    block_t_mid = 307.299134
    hold_t = 299.824134
    block_n_min = 209.840968
    hold_n_min, hold_n_max = 245.840968, 296.640968
    t_max = block_t_mid + first.BLOCK_T_MM / 2 - washer_radius
    t_separation = t_max - hold_t
    occupied_radius = tool_radius + hold_radius
    if not 0 < t_separation < occupied_radius:
        raise ValueError("G1 tool/path projection changed")
    required_n_separation = math.sqrt(occupied_radius**2 - t_separation**2)
    axis_n_min = block_n_min + four_d
    axis_n_max = block_n_min + first.BLOCK_N_MM - four_d
    low_width = hold_n_min - required_n_separation - axis_n_min
    high_width = axis_n_max - (hold_n_max + required_n_separation)
    extra_reserve = 1.0
    two_rows_with_reserve = (
        (low_width >= extra_reserve and high_width >= extra_reserve)
        or low_width >= four_d + 2 * extra_reserve
        or high_width >= four_d + 2 * extra_reserve
    )
    return {
        "source_id": SOURCE_ID,
        "assumed_tool_diameter_mm": 2 * tool_radius,
        "assumed_hold_projection_diameter_mm": 2 * hold_radius,
        "assumed_washer_diameter_mm": 2 * washer_radius,
        "four_d_end_and_row_marker_mm": four_d,
        "max_separated_t_mm": round(t_separation, 6),
        "nominal_low_n_interval_width_mm": round(max(low_width, 0.0), 6),
        "nominal_high_n_interval_width_mm": round(max(high_width, 0.0), 6),
        "two_rows_with_1mm_extra_end_reserve": two_rows_with_reserve,
        "disposition": "REVISE_TOOL_OR_TOPOLOGY"
        if not two_rows_with_reserve
        else "TRIAL_ONLY",
        "limits": (
            "Necessary X77 tool/G1 projection only; delivered hold bolt, actual "
            "socket, washer, wood grade, full 3D obstacles and joint capacity "
            "remain unverified."
        ),
    }


def screen():
    """Keep first-trial evidence intact while screening one revised pose."""
    report = first.screen_variant(SOURCE_ID, BLOCK_X_MM, RAIL_X_MM)
    if report["source_id"] != SOURCE_ID:
        raise ValueError("Detached bottom-center source binding changed")
    return {
        **report,
        "revision_basis": {
            "first_trial_source_id": first.SOURCE_ID,
            "left_rail_existing_passage_center_x_mm": -189.2,
            "left_rail_existing_passage_diameter_mm": 38.1,
            "first_trial_second_rail_bore_x_mm": -174.05,
            "first_trial_second_rail_bore_diameter_mm": first.joints.BORE_DIAMETER_MM,
            "right_G1_tnut_flange_near_x_mm": 180.8 - 12.7,
            "right_block_far_x_mm": 89.05 + BLOCK_X_MM,
            "right_G1_flange_nominal_x_gap_mm": 180.8 - 12.7 - (89.05 + BLOCK_X_MM),
            "nominal_far_rail_bolt_end_distance_mm": BLOCK_X_MM - RAIL_X_MM[1],
            "tolerance_and_load_direction_verified": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
