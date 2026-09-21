"""Detached PB06 bottom-center pair relocation; geometry only, no release."""

import json
from unittest.mock import patch

from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb06_horizontal_bottom_pair as previous
from scripts import simple_pb06_upper_center_native as pb06

RAIL_X_OFFSETS_MM = (70.0, 95.0)
BLOCK_LENGTH_MM = 295.0
STATION_SIDES = {
    previous.TARGET_STATIONS[0]: "left",
    previous.TARGET_STATIONS[1]: "right",
}


def screen(module=None):
    """Keep the old duties while testing shorter cleats and an inward rail row."""
    module = pb06.PB06Native() if module is None else module
    source = pb06.screen(module)
    build = lower._build_station

    def relocated(*args, **kwargs):
        return build(*args, **kwargs, block_length_mm=BLOCK_LENGTH_MM)

    # ponytail: reuse the complete PB06 collision screen without changing its source.
    with (
        patch.object(lower, "RAIL_X_OFFSETS_MM", RAIL_X_OFFSETS_MM),
        patch.object(lower, "_build_station", relocated),
        patch.object(previous.pb06, "screen", return_value=source),
    ):
        result = previous.screen(module)
    result["schema"] = "simple_pb06_bottom_pair_revision/v1"
    result["candidate_block_length_mm"] = BLOCK_LENGTH_MM
    result["candidate_rail_offsets_from_butt_mm"] = list(RAIL_X_OFFSETS_MM)
    result["prior_issues_resolved"] = {
        "second_rail_bores_complete": all(
            result["local"][station]["complete_bores_by_bolt"][
                f"pb06_bottom_center_{side}_rail_2"
            ]
            for station, side in STATION_SIDES.items()
        ),
        "right_side_cleat_clear": not result["local"][previous.TARGET_STATIONS[1]][
            "block_unrelated_timber_hits_mm3"
        ].get("upright_side_cleat"),
    }
    result["geometry_gates"] = {
        "conditional_signed_4d": result["minimum_signed_member_edge_margin_mm"]
        >= result["conditional_4d_target_mm"],
        "nominal_washer_seats_by_projection": result[
            "nominal_washer_seats_by_projection"
        ],
        "modelled_tool_and_stack_paths_clear": all(
            local["access_clear"] and local["collision_clear"]
            for local in result["local"].values()
        )
        and not any(result["protected_hits_mm3"].values()),
        "purchased_stock_length_shafts_verified": False,
    }
    result["decision"] = "REVISE"
    return result


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
