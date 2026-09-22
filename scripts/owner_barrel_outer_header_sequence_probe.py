"""Bounded rim-first sequence screen for recessed outer-header barrel bolts.

This is a dependency and nominal wood-withdrawal check, not a fabrication or
structural release. Fixed fastener *axes* remain unchanged; temporary removal
of their hardware is a condition of the proposed service sequence.
"""

import json
from itertools import pairwise

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import owner_barrel_coordinates as coordinates
from scripts import simple_owner_duty_ledger as ledger

SCHEMA = "owner_barrel_outer_header_sequence_probe/v1"
SIDES = ("left", "right")
WITHDRAWAL_SAMPLES_MM = tuple(range(0, 161, 5))
HIT_TOL_MM3 = 1.0
EXPECTED_RIM_FAMILIES = frozenset(
    {"top_outer", "bottom_outer", "lower_outer", "upper_outer", "base_outer_side"}
)


def _bounds_overlap(first, second):
    return (
        min(first.xmax, second.xmax) > max(first.xmin, second.xmin)
        and min(first.ymax, second.ymax) > max(first.ymin, second.ymin)
        and min(first.zmax, second.zmax) > max(first.zmin, second.zmin)
    )


def _wood_withdrawal(wood, side, samples_mm):
    """Sample a straight board-normal pull; do not infer a continuous swept fit."""
    rim_name = f"base_side_{side}"
    rim = wood[rim_name]
    n0, n1 = coordinates.local_bounds(rim)["n"]
    others = {name: shape for name, shape in wood.items() if name != rim_name}
    direction = cq.Vector(0, *coordinates.N)
    rows = []
    for distance in samples_mm:
        moving = rim.translate(direction * distance)
        moving_box = moving.BoundingBox()
        hits = {}
        for name, other in others.items():
            if not _bounds_overlap(moving_box, other.BoundingBox()):
                continue
            volume = moving.intersect(other).Volume()
            if volume > HIT_TOL_MM3:
                hits[name] = round(volume, 6)
        rows.append({"withdrawal_mm": distance, "other_uncut_wood_hits_mm3": hits})
    return {
        "direction_xyz": [0.0, *coordinates.N],
        "rim_normal_depth_mm": round(n1 - n0, 6),
        "last_sample_exceeds_rim_normal_depth": samples_mm[-1] > n1 - n0,
        "samples": rows,
        "sampled_wood_clear": all(not row["other_uncut_wood_hits_mm3"] for row in rows),
        "continuous_sweep_verified": False,
        "hardware_and_service_features_verified": False,
    }


def probe(*, source=None, duties=None, samples_mm=WITHDRAWAL_SAMPLES_MM):
    """Expose release dependencies on both sides without changing the design."""
    source = variant(KERF_RIGHT) if source is None else source
    duties = ledger.selected_duties() if duties is None else duties
    source_connections = tuple(source.connections())
    panel = tuple(source.panel_connections())
    frame = tuple(row for row in source_connections if row.kind == "bolt")
    if len(panel) != 66 or len(frame) != 12:
        raise ValueError("Fixed kerf-right screw/bolt inventory changed")
    if len({row.name for row in panel}) != 66 or len({row.name for row in frame}) != 12:
        raise ValueError("Fixed fastener names are not unique")
    if (
        not samples_mm
        or samples_mm[0] != 0
        or any(b <= a for a, b in pairwise(samples_mm))
    ):
        raise ValueError("Withdrawal samples must start at zero and increase")
    wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    result = {}
    for side in SIDES:
        rim_name = f"base_side_{side}"
        header_name = f"clip_timber_header_outer_{side}"
        if rim_name not in wood or header_name not in duties:
            raise ValueError(f"Missing source rim/header duty on {side}")
        header_duty = duties[header_name]
        if header_duty["family"] != "header_outer_post" or set(
            header_duty["timber"]
        ) != {"base_header", f"base_post_outer_{side}"}:
            raise ValueError(f"Outer-header duty unexpectedly depends on {rim_name}")
        rim_screws = sorted(row.name for row in panel if rim_name in row.members)
        rim_frame_bolts = sorted(row.name for row in frame if rim_name in row.members)
        rim_duties = {
            name: duty for name, duty in duties.items() if rim_name in duty["timber"]
        }
        families = {duty["family"] for duty in rim_duties.values()}
        if (
            len(rim_screws) != 8
            or len(rim_frame_bolts) != 2
            or families != EXPECTED_RIM_FAMILIES
            or len(rim_duties) != 5
            or any(duty["side"] != side for duty in rim_duties.values())
        ):
            raise ValueError(f"Unmodeled direct rim attachment on {side}")
        legacy_sds = {name for duty in rim_duties.values() for name in duty["sds_axes"]}
        source_rim_connections = {
            row.name for row in source_connections if rim_name in row.members
        }
        source_legacy_rim = (
            source_rim_connections - set(rim_screws) - set(rim_frame_bolts)
        )
        if (
            len(legacy_sds) != 30
            or len(source_legacy_rim) != 15
            or not source_legacy_rim <= legacy_sds
        ):
            raise ValueError(f"Unclassified source rim connection on {side}")
        release = {
            "fixed_panel_screws": rim_screws,
            "fixed_frame_bolts": rim_frame_bolts,
            "candidate_barrel_stations": sorted(rim_duties),
        }
        result[side] = {
            "outer_header_station": header_name,
            "outer_header_members": list(header_duty["timber"]),
            "outer_header_bolts_can_remain_installed_during_rim_release": True,
            "release_before_rim_withdrawal": release,
            "side_rim_connected_to_header_station": False,
            "graph_condition_if_all_direct_fasteners_released": "rim_detached",
            "graph_condition_if_fixed_screws_or_bolts_stay_installed": "blocked",
            "nominal_wood_withdrawal": _wood_withdrawal(wood, side, samples_mm),
            "sequence": [
                "Unload and independently support the board and panels",
                "Undo listed rim-receiver panel screws and two leg/rim frame bolts",
                "Undo both trial barrel bolts at each listed rim-touching station",
                "Withdraw the rim along the sampled rearward board normal",
                "Operate the recessed outer-header/post bolts with the rim absent",
                "Reassemble in reverse order using the same fixed axes",
            ],
            "operational_result": "conditional_unverified",
        }
    return {
        "schema": SCHEMA,
        "width_option": KERF_RIGHT,
        "fixed_axis_inventory": {
            "panel_kicker_screws": len(panel),
            "frame_bolts": len(frame),
        },
        "fixed_axis_coordinates_changed": False,
        "temporary_fixed_fastener_removal_required": True,
        "sides": result,
        "conclusion": (
            "No fastener-dependency cycle: with the listed attachments temporarily "
            "released, a rim-first order is possible in the connection graph. "
            "The sampled bare-wood withdrawal does not establish a continuous, "
            "hardware-clear, supported, or repeatable real assembly sequence."
        ),
        "unverified": [
            "Tool access and actual removal of every rim-touching trial barrel bolt",
            "Delivered fastener heads, nuts, washers, cross-dowels, and projections",
            "A continuous rim-withdrawal sweep, tolerances, flex and safe handling",
            "Hold/T-nut and electrical clearance during service",
            "Recessed outer-header head geometry and tool path after rim removal",
            "Connection resistance, wood strength, preload and repeatability",
        ],
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
