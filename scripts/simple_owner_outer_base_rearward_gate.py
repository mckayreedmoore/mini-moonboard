"""Necessary Y-clearance proof for the outer-base header bolt; no CAD solve."""

from mini_moonboard import compact_floor_flush_frame as frame
from scripts import owner_layout_outer_header_pair as outer_header
from scripts import simple_pb03_lower_center_pair as joints

TRIAL_BLOCK_REAR_Y_MM = -185.7
TRIAL_BLOCK_GRAIN_Y_MM = 70.0
TRIAL_HEADER_BOLT_Y_MM = -160.3


def screen():
    """Reject only a Y-only move at the already overlapping X/Z station."""
    rear = frame.HEADER_BACK_Y
    outer_face = outer_header.BLOCK_Y0_MM
    diameter = joints.BOLT_DIAMETER_MM
    washer_radius = joints.WASHER_DIAMETER_MM / 2
    tool_radius = joints.TOOL_DIAMETER_MM / 2
    four_d_min = rear + 4 * diameter
    shaft_max = outer_face - diameter / 2
    washer_max = outer_face - washer_radius
    tool_max = outer_face - tool_radius
    washer_seat_min = rear + washer_radius
    if not (
        rear == -175.7
        and outer_face == -150.3
        and abs(
            outer_header.BLOCK_Z0_MM
            + outer_header.BLOCK_Z_MM
            - frame.base.HEADER_BOTTOM
        )
        < 1e-6
        and four_d_min > shaft_max > washer_max > tool_max
    ):
        raise ValueError("Outer-base/header clearance source datums changed")
    trial_rear_edge = TRIAL_HEADER_BOLT_Y_MM - TRIAL_BLOCK_REAR_Y_MM
    trial_header_edge = TRIAL_HEADER_BOLT_Y_MM - rear
    trial_washer_overlap = max(0.0, TRIAL_HEADER_BOLT_Y_MM + washer_radius - outer_face)
    return {
        "header_rear_y_mm": rear,
        "outer_header_block_rear_y_mm": outer_face,
        "conditional_4d_min_center_y_mm": round(four_d_min, 6),
        "shaft_clear_max_center_y_mm": round(shaft_max, 6),
        "washer_clear_max_center_y_mm": round(washer_max, 6),
        "tool_clear_max_center_y_mm": round(tool_max, 6),
        "full_washer_seat_min_center_y_mm": round(washer_seat_min, 6),
        "trial_70mm_block": {
            "rear_y_mm": TRIAL_BLOCK_REAR_Y_MM,
            "front_y_mm": round(TRIAL_BLOCK_REAR_Y_MM + TRIAL_BLOCK_GRAIN_Y_MM, 6),
            "header_bolt_y_mm": TRIAL_HEADER_BOLT_Y_MM,
            "block_loaded_edge_mm": round(trial_rear_edge, 6),
            "header_receiver_rear_edge_mm": round(trial_header_edge, 6),
            "washer_y_overlap_mm": round(trial_washer_overlap, 6),
        },
        "decision": "REVISE_NO_REARWARD_ONLY_POSE",
        "cad_run_needed": False,
        "scope": "Same X/Z overlap; only header-bolt Y and outer-base block Y may move",
        "strength_checked": False,
        "drilling_released": False,
    }
