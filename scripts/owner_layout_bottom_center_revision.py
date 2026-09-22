"""One detached 77-mm-X same-side bottom-center pose; owner layout only."""

import json

from scripts import owner_layout_bottom_center_pair as first

SOURCE_ID = "owner-bottom-center-pair-x180-77x139p7-layout-v2"
BLOCK_X_MM = 77.0
RAIL_X_MM = (26.0, 51.0)


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
