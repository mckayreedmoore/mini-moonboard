"""Detached PB04 outer-pocket depth sensitivity; never changes installed PB04."""

import json
import math
from itertools import combinations

from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_outer_counterbore_revision as pocket
from scripts import simple_pb04_native as pb04


def _hits(shape, solids):
    return {
        name: round(volume, 6)
        for name, other in solids.items()
        if _box_gap(shape.BoundingBox(), other.BoundingBox()) == 0
        if (volume := lower._intersection_volume(shape, other)) > lower.TOL_MM3
    }


def _box_gap(left, right):
    """Cheap lower bound; skip exact CAD operations for separated boxes."""
    return math.sqrt(
        sum(
            max(
                getattr(left, a) - getattr(right, b),
                getattr(right, a) - getattr(left, b),
                0,
            )
            ** 2
            for a, b in (("xmin", "xmax"), ("ymin", "ymax"), ("zmin", "zmax"))
        )
    )


def _nearest(shape, solids):
    bounds = shape.BoundingBox()
    nearest = math.inf
    for other in solids.values():
        if _box_gap(bounds, other.BoundingBox()) < nearest:
            nearest = min(nearest, shape.distance(other))
    return nearest


def _case(geometries, depth, original_pockets, parts, panel_axes):
    revised_pockets = {}
    revised_blocks = {}
    for station in pocket.TARGET_STATIONS:
        geometry = geometries[station]
        block = geometry.block
        for bolt in geometry.bolts:
            if bolt.members[0] != geometry.upright_name:
                continue
            key = f"{station}/{bolt.name}"
            direction = bolt.direction.normalized()
            outer_face = bolt.start + direction * (lower.END_ALLOWANCE_MM + bolt.grip)
            cut = pocket._cylinder(
                outer_face.toTuple(),
                (-direction).toTuple(),
                depth,
                pocket.FORSTNER_DIAMETER_MM,
            )
            if original_pockets[key].cut(cut).Volume() > lower.TOL_MM3:
                raise ValueError(f"{key}: deeper cut fails to contain original pocket")
            revised_pockets[key] = cut
            block = block.cut(cut)
        revised_blocks[station] = block

    timber = {
        name: shape
        for name, shape in parts.items()
        if not name.startswith(("main_", "kicker_"))
    }
    panels = {
        name: shape
        for name, shape in parts.items()
        if name.startswith(("main_", "kicker_"))
    }
    for station, block in revised_blocks.items():
        timber[geometries[station].block_name] = block
    axes = lower._fixed_axis_solids(panel_axes)
    bores = {
        f"{station}/{name}": shape
        for station, geometry in geometries.items()
        for name, shape in geometry.bores.items()
    }
    other_stacks = {
        f"{station}/{name}/{role}": shape
        for station, geometry in geometries.items()
        for name, stack in geometry.stacks.items()
        if f"{station}/{name}" not in revised_pockets
        for role, shape in stack.items()
    }

    installed = {}
    tools = {}
    sockets = {}
    rows = {}
    for station in pocket.TARGET_STATIONS:
        geometry = geometries[station]
        for bolt in geometry.bolts:
            if bolt.members[0] != geometry.upright_name:
                continue
            key = f"{station}/{bolt.name}"
            direction = bolt.direction.normalized()
            near = bolt.start + direction * lower.END_ALLOWANCE_MM
            far = near + direction * bolt.grip
            floor = far - direction * depth
            head_start = near - direction * pocket.WASHER_EACH_SIDE_MM
            cylinder = lambda start, length, diameter, axis=direction: pocket._cylinder(
                start.toTuple(), axis.toTuple(), length, diameter
            )
            installed[key] = {
                "shaft": cylinder(
                    head_start, pocket.BOLT_LENGTH_MM, lower.BOLT_DIAMETER_MM
                ),
                "head": cylinder(
                    head_start - direction * 6, 6, lower.HEAD_NUT_DIAMETER_MM
                ),
                "near_washer": cylinder(
                    head_start,
                    pocket.WASHER_EACH_SIDE_MM,
                    pocket.WASHER_OUTSIDE_DIAMETER_MM,
                ),
                "far_washer": cylinder(
                    floor, pocket.WASHER_EACH_SIDE_MM, pocket.WASHER_OUTSIDE_DIAMETER_MM
                ),
                "nut": cylinder(
                    floor + direction * pocket.WASHER_EACH_SIDE_MM,
                    pocket.NUT_HEIGHT_MM,
                    pocket.NUT_MAX_ACROSS_CORNERS_MM,
                ),
            }
            sockets[key] = cylinder(floor, depth, pocket.SOCKET_DIAMETER_MM)
            tools[key] = cylinder(
                far, pocket.TOOL_APPROACH_MM, pocket.FORSTNER_DIAMETER_MM
            )
            rows[key] = {
                "near_washer_start_from_head_mm": 0.0,
                "far_washer_start_from_head_mm": (
                    pocket.WASHER_EACH_SIDE_MM + bolt.grip - depth
                ),
                "nut_start_from_head_mm": (
                    2 * pocket.WASHER_EACH_SIDE_MM + bolt.grip - depth
                ),
                "socket_start_from_head_mm": (
                    pocket.WASHER_EACH_SIDE_MM + bolt.grip - depth
                ),
                "tool_start_from_head_mm": pocket.WASHER_EACH_SIDE_MM + bolt.grip,
                "bolt_tip_from_head_mm": pocket.BOLT_LENGTH_MM,
                "socket_outside_pocket_mm3": round(
                    sockets[key].cut(revised_pockets[key]).Volume(), 6
                ),
            }

    all_stacks = {
        **other_stacks,
        **{
            f"{key}/{role}": solid
            for key, stack in installed.items()
            for role, solid in stack.items()
        },
    }
    collisions = {
        name: {}
        for name in (
            "pocket_other_bores",
            "pocket_other_stacks",
            "pocket_other_wood",
            "pocket_panels",
            "pocket_panel_axes",
            "pocket_pairs",
            "hardware",
            "tool_permanent",
            "tool_removable_panels",
        )
    }
    minimum_bore = math.inf
    minimum_stack = math.inf
    pocket_inside = True
    intended_bores_open = True
    for key, cut in revised_pockets.items():
        station, bolt_name = key.split("/", 1)
        geometry = geometries[station]
        own_bore = f"{station}/{bolt_name}"
        other_bores = {name: shape for name, shape in bores.items() if name != own_bore}
        other_stacks_for_key = {
            name: shape
            for name, shape in all_stacks.items()
            if not name.startswith(key + "/")
        }
        other_wood = {
            name: shape for name, shape in timber.items() if name != geometry.block_name
        }
        pocket_inside &= math.isclose(
            lower._intersection_volume(cut, geometry.block),
            cut.Volume(),
            abs_tol=lower.TOL_MM3,
        )
        intended_bores_open &= (
            lower._intersection_volume(cut, bores[own_bore]) > lower.TOL_MM3
        )
        minimum_bore = min(minimum_bore, _nearest(cut, other_bores))
        minimum_stack = min(minimum_stack, _nearest(cut, other_stacks_for_key))
        for category, solids in (
            ("pocket_other_bores", other_bores),
            ("pocket_other_stacks", other_stacks_for_key),
            ("pocket_other_wood", other_wood),
            ("pocket_panels", panels),
            ("pocket_panel_axes", axes),
        ):
            collisions[category].update(
                {f"{key}|{name}": volume for name, volume in _hits(cut, solids).items()}
            )
        own_wood = {
            name: shape.cut(bores[own_bore])
            if name in {geometry.upright_name, geometry.block_name}
            else shape
            for name, shape in timber.items()
        }
        occupants = {
            **{f"wood/{name}": shape for name, shape in own_wood.items()},
            **{f"panel/{name}": shape for name, shape in panels.items()},
            **{f"axis/{name}": shape for name, shape in axes.items()},
            **{f"stack/{name}": shape for name, shape in other_stacks_for_key.items()},
        }
        for role, shape in installed[key].items():
            collisions["hardware"].update(
                {
                    f"{key}/{role}|{name}": volume
                    for name, volume in _hits(shape, occupants).items()
                }
            )
        tool_occupants = {
            **{
                f"wood/{name}": shape
                for name, shape in timber.items()
                if name != geometry.block_name
            },
            **{f"axis/{name}": shape for name, shape in axes.items()},
            **{f"stack/{name}": shape for name, shape in other_stacks_for_key.items()},
        }
        collisions["tool_permanent"].update(
            {
                f"{key}|{name}": volume
                for name, volume in _hits(tools[key], tool_occupants).items()
            }
        )
        collisions["tool_removable_panels"].update(
            {
                f"{key}|{name}": volume
                for name, volume in _hits(tools[key], panels).items()
            }
        )
    collisions["pocket_pairs"] = {
        f"{a}|{b}": round(volume, 6)
        for (a, first), (b, second) in combinations(revised_pockets.items(), 2)
        if (volume := lower._intersection_volume(first, second)) > lower.TOL_MM3
    }
    minimum_pair = min(
        first.distance(second)
        for first, second in combinations(revised_pockets.values(), 2)
        if _box_gap(first.BoundingBox(), second.BoundingBox()) < 50
    )

    grip = pocket.ORIGINAL_GRIP_MM - depth
    nut_start = 2 * pocket.WASHER_EACH_SIDE_MM + grip
    nut_end = nut_start + pocket.NUT_HEIGHT_MM
    margin = pocket.BOLT_LENGTH_MM - nut_end - pocket.TWO_THREAD_PROJECTION_MM
    thread_start = pocket.BOLT_LENGTH_MM - pocket.BOLT_LISTED_THREAD_LENGTH_MM
    geometry_clear = (
        pocket_inside
        and intended_bores_open
        and not any(
            value
            for name, value in collisions.items()
            if name != "tool_removable_panels"
        )
        and all(
            row["socket_outside_pocket_mm3"] <= lower.TOL_MM3 for row in rows.values()
        )
        and nut_start >= thread_start - 1e-8
        and margin >= -1e-8
    )
    return {
        "depth_mm": depth,
        "wood_grip_mm": grip,
        "axial_wood_beyond_pocket_mm": lower.BLOCK_X_MM - depth,
        "net_block_volume_mm3": round(
            sum(s.Volume() for s in revised_blocks.values()), 6
        ),
        "nut_start_from_head_mm": nut_start,
        "nut_end_from_head_mm": nut_end,
        "thread_start_from_head_mm": thread_start,
        "bolt_tip_from_head_mm": pocket.BOLT_LENGTH_MM,
        "end_projection_threads": (pocket.BOLT_LENGTH_MM - nut_end)
        / pocket.THREAD_PITCH_MM,
        "nominal_length_margin_mm": round(margin, 9),
        "minimum_pocket_to_other_bore_mm": minimum_bore,
        "minimum_pocket_to_other_stack_mm": minimum_stack,
        "minimum_between_pockets_mm": minimum_pair,
        "pocket_to_block_edge_mm": lower.BLOCK_T_MM / 2
        - pocket.FORSTNER_DIAMETER_MM / 2,
        "pocket_inside_block": pocket_inside,
        "intended_bores_open": intended_bores_open,
        "stacks": rows,
        "collisions_mm3": collisions,
        "geometry_clear": geometry_clear,
    }


def screen(*, extra_depth_mm=1.0):
    """Compare source pockets with one deeper cut on the six outer blocks."""
    if not math.isfinite(extra_depth_mm) or extra_depth_mm <= 0:
        raise ValueError("Extra pocket depth must be positive finite")
    module = pb04.PB04Native()
    if (
        module.KEY != pb04.SOURCE_ID
        or module.ACTIVE_FINGERPRINT != pb04.PB03Native.ACTIVE_FINGERPRINT
    ):
        raise ValueError("PB04 source identity changed")
    geometries = module.pb03_geometries()
    original_pockets, original_blocks = pocket.build_counterbored_blocks(geometries)
    parts = {part.name: part.shape for part in module.wood_parts()}
    panel_axes = tuple(module.panel_connections())
    if (
        len(geometries) != 8
        or len(pocket.TARGET_STATIONS) != 6
        or len(original_pockets) != 12
        or len(panel_axes) != 66
        or any(
            abs(parts[geometries[s].block_name].Volume() - b.Volume()) > 1e-5
            for s, b in original_blocks.items()
        )
    ):
        raise ValueError("PB04 installed source inventory or pockets changed")
    depth = pocket._required_depth_mm()
    original = _case(geometries, depth, original_pockets, parts, panel_axes)
    deeper = _case(
        geometries, depth + extra_depth_mm, original_pockets, parts, panel_axes
    )
    return {
        "schema": "simple_pb04_pocket_reserve_trial/v1",
        "source_id": pb04.SOURCE_ID,
        "source_fingerprint_sha256": pb04._source_fingerprint(module),
        "inventory": {"outer_blocks": 6, "pockets": 12, "panel_axes": 66},
        "pocket_diameter_mm": pocket.FORSTNER_DIAMETER_MM,
        "extra_depth_mm": extra_depth_mm,
        "original": original,
        "deeper": deeper,
        "decision": (
            "ADVANCE_GEOMETRY_ONLY"
            if original["geometry_clear"]
            and deeper["geometry_clear"]
            and deeper["nominal_length_margin_mm"] >= 1.0
            else "REVISE_GEOMETRY"
        ),
        "manufacturing_tolerance_verified": False,
        "strength_checked": False,
        "qualified_for_design": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
