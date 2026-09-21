"""Detached PB04 6-in versus 300-mm corner-block geometry screen; no release."""

import json
import math

from scripts import simple_pb03_cross_family as cross
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_outer_counterbore_revision as pocket
from scripts import simple_pb03_upper_outer_pair as upper
from scripts import simple_pb04_native as pb04

LENGTHS_MM = (152.4, lower.BLOCK_LENGTH_MM)
STATIONS = (lower.TARGET_STATIONS[0], upper.TARGET_STATIONS[0])
# Provisional geometric allowance only, not an NDS end-distance or resistance check.
GRAIN_END_ALLOWANCE_MM = 4 * lower.BOLT_DIAMETER_MM
OPENING_LIGAMENT_ALLOWANCE_MM = 3.0


def _hits(first, others):
    return {
        name: round(volume, 6)
        for name, second in others.items()
        if (volume := lower._intersection_volume(first, second)) > lower.TOL_MM3
    }


def _opening_end_ligaments(geometry, pockets):
    """Distances from the physical N ends to every bore, seat, and pocket."""
    openings = []
    for bolt in geometry.bolts:
        n = (
            lower.UPRIGHT_N_OFFSETS_MM[int(bolt.name.rsplit("_", 1)[1]) - 1]
            if bolt.members[0] == geometry.upright_name
            else geometry.report["rail_bore_n_offset_mm"]
        )
        openings.append((bolt.name + "/bore", n, lower.BORE_DIAMETER_MM / 2))
        openings.append((bolt.name + "/seat", n, lower.WASHER_DIAMETER_MM / 2))
    for name in pockets:
        index = int(name.rsplit("_", 1)[1]) - 1
        openings.append(
            (
                name + "/pocket",
                lower.UPRIGHT_N_OFFSETS_MM[index],
                pocket.FORSTNER_DIAMETER_MM / 2,
            )
        )
    return {
        name: {
            "near_mm": round(n - radius, 6),
            "far_mm": round(geometry.block_length_mm - n - radius, 6),
            "center_near_mm": round(n, 6),
            "center_far_mm": round(geometry.block_length_mm - n, 6),
        }
        for name, n, radius in openings
    }


def _one_length(station, length, reference, source):
    parts, finished, panels, _, _ = source
    geometry = lower._build_station(
        (
            upper.STATION_SPECS
            if station in upper.TARGET_STATIONS
            else lower.STATION_SPECS
        )[station],
        parts,
        finished,
        lower._fixed_axis_solids(panels),
        rail_n_offset_mm=(
            pb04.SELECTED_OFFSET_MM
            if station in upper.TARGET_STATIONS
            else lower.RAIL_N_OFFSET_MM
        ),
        block_length_mm=length,
    )
    if length == lower.BLOCK_LENGTH_MM and (
        geometry.block.distance(reference[station].block) > 1.0e-8
        or not math.isclose(
            geometry.block.Volume(), reference[station].block.Volume(), abs_tol=1.0e-6
        )
        or any(
            (new.start - old.start).Length > 1.0e-8
            for new, old in zip(geometry.bolts, reference[station].bolts, strict=True)
        )
    ):
        raise ValueError("300-mm comparison does not reproduce PB04 geometry")
    others = {name: item for name, item in reference.items() if name != station}
    interactions = cross.screen_cross_family({station: geometry}, others)
    composed = {**others, station: geometry}
    pockets, cut_blocks = pocket.build_counterbored_blocks(composed)
    own_pockets = {
        name: shape for name, shape in pockets.items() if name.startswith(station + "/")
    }
    other_pockets = {
        name: shape
        for name, shape in pockets.items()
        if not name.startswith(station + "/")
    }
    own_bores = geometry.bores
    other_bores = {
        f"{name}/{bolt}": bore
        for name, item in others.items()
        for bolt, bore in item.bores.items()
    }
    all_stacks = {
        f"{name}/{bolt}/{role}": shape
        for name, item in composed.items()
        for bolt, stack in item.stacks.items()
        for role, shape in stack.items()
    }
    pocket_hits = {}
    pocket_inside = {}
    pocket_tool_hits = {}
    socket_outside_pocket = {}
    fixed_axes = lower._fixed_axis_solids(panels)
    for name, shape in own_pockets.items():
        own_bolt = name.split("/", 1)[1]
        unrelated = {
            key: value
            for key, value in {**other_bores, **own_bores}.items()
            if key != own_bolt
        }
        unrelated.update(
            {
                key: value
                for key, value in all_stacks.items()
                if not key.startswith(f"{station}/{own_bolt}/")
            }
        )
        unrelated.update({f"block/{key}": item.block for key, item in others.items()})
        pocket_hits[name] = _hits(shape, unrelated)
        pocket_inside[name] = math.isclose(
            lower._intersection_volume(shape, geometry.block),
            shape.Volume(),
            abs_tol=lower.TOL_MM3,
        )
        bolt = next(row for row in geometry.bolts if row.name == own_bolt)
        axis = bolt.direction.normalized()
        outside = bolt.start + axis * (lower.END_ALLOWANCE_MM + bolt.grip)
        approach = pocket._cylinder(
            outside.toTuple(),
            axis.toTuple(),
            pocket.TOOL_APPROACH_MM,
            pocket.FORSTNER_DIAMETER_MM,
        )
        obstructions = {
            **{f"timber/{key}": value for key, value in finished.items()},
            **{f"block/{key}": item.block for key, item in others.items()},
            **{f"axis/{key}": value for key, value in fixed_axes.items()},
            **{
                f"stack/{key}": value
                for key, value in all_stacks.items()
                if not key.startswith(f"{station}/{own_bolt}/")
            },
        }
        pocket_tool_hits[name] = _hits(approach, obstructions)
        seat = outside - axis * pocket._required_depth_mm()
        socket = pocket._cylinder(
            seat.toTuple(),
            axis.toTuple(),
            pocket._required_depth_mm(),
            pocket.SOCKET_DIAMETER_MM,
        )
        socket_outside_pocket[name] = round(socket.cut(shape).Volume(), 6)
    neighbor_pocket_hits = {
        name: _hits(
            shape,
            {
                "block": geometry.block,
                **{f"bore/{key}": value for key, value in own_bores.items()},
                **{
                    f"stack/{bolt}/{role}": value
                    for bolt, stack in geometry.stacks.items()
                    for role, value in stack.items()
                },
            },
        )
        for name, shape in other_pockets.items()
    }
    ligaments = _opening_end_ligaments(geometry, own_pockets)
    grain_end = min(value["far_mm"] for value in ligaments.values())
    net_ligaments = {
        "grain_end": grain_end,
        "x_wood_beyond_pocket": lower.BLOCK_X_MM - pocket._required_depth_mm()
        if own_pockets
        else None,
        "pocket_to_unintended_bore": min(
            (
                shape.distance(bore)
                for name, shape in own_pockets.items()
                for key, bore in {**other_bores, **own_bores}.items()
                if key != name.split("/", 1)[1]
            ),
            default=None,
        ),
        "between_pockets": min(
            (
                first.distance(second)
                for index, first in enumerate(own_pockets.values())
                for second in list(own_pockets.values())[index + 1 :]
            ),
            default=None,
        ),
    }
    required_length = max(
        max(
            length - value["far_mm"] + OPENING_LIGAMENT_ALLOWANCE_MM,
            length - value["center_far_mm"] + GRAIN_END_ALLOWANCE_MM
            if name.endswith("/bore")
            else 0,
        )
        for name, value in ligaments.items()
    )
    local = geometry.report
    gates = {
        "complete_bores": local["complete_bores"],
        "local_collision_clear": local["collision_clear"],
        "local_access_clear": local["access_clear"],
        "adjacent_blocks_clear": not interactions["cross_family_block_hits_mm3"],
        "adjacent_bores_stacks_clear": not any(
            interactions[key]
            for key in (
                "cross_family_bore_hits_mm3",
                "cross_family_stack_block_hits_mm3",
                "cross_family_stack_component_hits_mm3",
            )
        ),
        "adjacent_tool_paths_clear": not any(
            interactions[key]
            for key in (
                "cross_family_tool_block_hits_mm3",
                "cross_family_tool_stack_hits_mm3",
            )
        ),
        "counterbores_clear": all(pocket_inside.values())
        and not any(pocket_hits.values())
        and not any(neighbor_pocket_hits.values()),
        "counterbore_tool_paths_clear": not any(pocket_tool_hits.values())
        and not any(socket_outside_pocket.values()),
        "grain_end_screen_clear": all(
            value["near_mm"] >= OPENING_LIGAMENT_ALLOWANCE_MM
            and value["far_mm"] >= OPENING_LIGAMENT_ALLOWANCE_MM
            and (
                not name.endswith("/bore")
                or (
                    value["center_near_mm"] >= GRAIN_END_ALLOWANCE_MM
                    and value["center_far_mm"] >= GRAIN_END_ALLOWANCE_MM
                )
            )
            for name, value in ligaments.items()
        ),
    }
    upright = [
        bolt.grip for bolt in geometry.bolts if bolt.members[0] == geometry.upright_name
    ]
    rail = [
        bolt.grip for bolt in geometry.bolts if bolt.members[0] == geometry.rail_name
    ]
    return {
        "block_length_mm": length,
        "gross_volume_mm3": round(geometry.block.Volume(), 6),
        "net_volume_after_counterbores_mm3": round(
            cut_blocks.get(station, geometry.block).Volume(), 6
        ),
        "upright_wood_grip_mm": upright[0],
        "rail_wood_grip_mm": rail[0],
        "rail_contact_area_mm2": round(local["contact_area_mm2"]["rail"], 6),
        "upright_contact_area_mm2": round(local["contact_area_mm2"]["upright"], 6),
        "complete_bores": local["complete_bores"],
        "grain_end_ligament_mm": grain_end,
        "grain_end_openings_mm": ligaments,
        "net_ligaments_mm": net_ligaments,
        "minimum_length_for_provisional_end_allowance_mm": round(required_length, 6),
        "local_collision_hits": {
            key: local[key]
            for key in (
                "block_unrelated_timber_hits_mm3",
                "block_finished_panel_hits_mm3",
                "block_fixed_axis_hits_mm3",
                "same_station_bore_hits_mm3",
            )
            if local[key]
        },
        "adjacent_collision_hits": {
            key: value
            for key, value in interactions.items()
            if key.endswith("_hits_mm3") and value
        },
        "counterbore_hits_mm3": {"own": pocket_hits, "neighbor": neighbor_pocket_hits},
        "counterbore_tool_hits_mm3": pocket_tool_hits,
        "socket_outside_pocket_mm3": socket_outside_pocket,
        "gates": gates,
        "geometric_pass": all(gates.values()),
    }


def screen():
    """Compare two actual stations while retaining the other six PB04 stations."""
    module = pb04.PB04Native()
    if module.KEY != pb04.SOURCE_ID or not math.isclose(
        pb04.SELECTED_OFFSET_MM, 35.709
    ):
        raise ValueError("PB04 source or selected upper offset changed")
    reference = module.pb03_geometries()
    source = lower._source_inventory()
    if len(module.panel_connections()) != 66 or len(reference) != 8:
        raise ValueError("PB04 source inventory changed")
    if any(
        not math.isclose(reference[name].report["rail_bore_n_offset_mm"], 35.709)
        for name in ("clip_horizontal_upper_left_1", "clip_horizontal_upper_right_2")
    ):
        raise ValueError("PB04 upper-outer geometry is not at 35.709 mm")
    stations = {}
    for station in STATIONS:
        rows = {
            str(length): _one_length(station, length, reference, source)
            for length in LENGTHS_MM
        }
        stations[station] = {
            "lengths": rows,
            "six_inch_decision": "PASS_GEOMETRY_ONLY"
            if rows["152.4"]["geometric_pass"]
            else "REVISE_GEOMETRY",
            "required_length_mm": rows["152.4"][
                "minimum_length_for_provisional_end_allowance_mm"
            ],
        }
    return {
        "schema": "simple_pb04_six_inch_block_screen/v1",
        "source_id": pb04.SOURCE_ID,
        "upper_outer_offset_mm": pb04.SELECTED_OFFSET_MM,
        "lengths_mm": list(LENGTHS_MM),
        "fixed_panel_kicker_axes": 66,
        "stations": stations,
        "grain_end_allowance_basis": (
            "provisional 4D bolt-center and 3-mm net-opening screens; "
            "not NDS resistance or loaded-end qualification"
        ),
        "length_vs_x_grip": "block grain length changes; upright 9-in X-axis wood grip does not",
        "strength_checked": False,
        "active_design_integrated": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
