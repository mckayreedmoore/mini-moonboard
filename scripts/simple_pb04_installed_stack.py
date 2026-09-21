"""Detached installed 8-inch PB04 outer-upright stack screen; no approval."""

import json
import math

from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_outer_counterbore_revision as pocket
from scripts import simple_pb04_native as pb04


def _hits(shape, others):
    return {
        name: round(volume, 6)
        for name, other in others.items()
        if (volume := lower._intersection_volume(shape, other)) > lower.TOL_MM3
    }


def screen(*, required_tolerance_reserve_mm=1.0):
    """Seat the actual hardware against PB04 pockets and screen fit/access."""
    if (
        not math.isfinite(required_tolerance_reserve_mm)
        or required_tolerance_reserve_mm <= 0
    ):
        raise ValueError("A positive dimensional tolerance reserve is required")
    module = pb04.PB04Native()
    if (
        module.KEY != pb04.SOURCE_ID
        or module.ACTIVE_FINGERPRINT != pb04.PB03Native.ACTIVE_FINGERPRINT
    ):
        raise ValueError("PB04 source identity changed")
    geometries = module.pb03_geometries()
    pockets, cut_blocks = pocket.build_counterbored_blocks(geometries)
    parts = {part.name: part.shape for part in module.wood_parts()}
    fixed_axes = lower._fixed_axis_solids(module.panel_connections())
    if (
        len(geometries) != 8
        or len(pockets) != 12
        or len(module.panel_connections()) != 66
    ):
        raise ValueError("PB04 source inventory changed")
    if any(
        abs(parts[geometries[station].block_name].Volume() - block.Volume()) > 1e-5
        for station, block in cut_blocks.items()
    ):
        raise ValueError("PB04 installed pocket solids changed")

    depth = pocket._required_depth_mm()
    grip = pocket.ORIGINAL_GRIP_MM - depth
    pitch = pocket.THREAD_PITCH_MM
    under_head_to_nut = pocket.WASHER_EACH_SIDE_MM * 2 + grip + pocket.NUT_HEIGHT_MM
    margin = pocket.BOLT_LENGTH_MM - under_head_to_nut - pocket.TWO_THREAD_PROJECTION_MM
    thread_start = pocket.BOLT_LENGTH_MM - pocket.BOLT_LISTED_THREAD_LENGTH_MM
    axial = {
        "nominal_under_head_length": pocket.BOLT_LENGTH_MM,
        "usable_thread_length": pocket.BOLT_LISTED_THREAD_LENGTH_MM,
        "thread_start_from_under_head": thread_start,
        "original_wood_grip": pocket.ORIGINAL_GRIP_MM,
        "wood_grip": grip,
        "pocket_depth": depth,
        "near_washer": pocket.WASHER_EACH_SIDE_MM,
        "far_washer": pocket.WASHER_EACH_SIDE_MM,
        "nut_height": pocket.NUT_HEIGHT_MM,
        "thread_pitch": pitch,
        "nut_start_from_under_head": under_head_to_nut - pocket.NUT_HEIGHT_MM,
        "nut_engagement_threads": pocket.NUT_HEIGHT_MM / pitch,
        "end_projection_threads": (pocket.BOLT_LENGTH_MM - under_head_to_nut) / pitch,
        "nominal_length_margin": round(margin, 9),
        "required_tolerance_reserve": required_tolerance_reserve_mm,
        "tolerance_reserve_pass": margin >= required_tolerance_reserve_mm,
        "threaded_nut_pass": under_head_to_nut - pocket.NUT_HEIGHT_MM >= thread_start,
        "two_thread_projection_pass": margin >= -1e-8,
    }

    installed = {}
    tools = {}
    rows = {}
    gross_bores_preserved = True
    socket_outside = {}
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
            if not math.isclose(bolt.grip, pocket.ORIGINAL_GRIP_MM, abs_tol=1e-8):
                raise ValueError(f"{key}: gross grip changed")
            expected_bore = pocket._cylinder(
                bolt.start.toTuple(),
                direction.toTuple(),
                bolt.length,
                lower.BORE_DIAMETER_MM,
            )
            gross_bores_preserved &= geometry.bores[bolt.name].distance(
                expected_bore
            ) <= 1e-8 and math.isclose(
                geometry.bores[bolt.name].Volume(), expected_bore.Volume(), abs_tol=1e-5
            )
            if not math.isclose(
                lower._intersection_volume(pockets[key], geometry.block),
                pockets[key].Volume(),
                abs_tol=lower.TOL_MM3,
            ):
                raise ValueError(f"{key}: pocket left gross block")
            washer_near_start = near - direction * pocket.WASHER_EACH_SIDE_MM
            washer_far_end = floor + direction * pocket.WASHER_EACH_SIDE_MM
            cylinder = lambda start, length, diameter, axis=direction: pocket._cylinder(
                start.toTuple(), axis.toTuple(), length, diameter
            )
            installed[key] = {
                "shaft": cylinder(
                    washer_near_start, pocket.BOLT_LENGTH_MM, lower.BOLT_DIAMETER_MM
                ),
                "head_envelope": cylinder(
                    washer_near_start - direction * 6.0, 6.0, lower.HEAD_NUT_DIAMETER_MM
                ),
                "near_washer": cylinder(
                    washer_near_start,
                    pocket.WASHER_EACH_SIDE_MM,
                    pocket.WASHER_OUTSIDE_DIAMETER_MM,
                ),
                "far_washer": cylinder(
                    floor, pocket.WASHER_EACH_SIDE_MM, pocket.WASHER_OUTSIDE_DIAMETER_MM
                ),
                "nut_envelope": cylinder(
                    washer_far_end,
                    pocket.NUT_HEIGHT_MM,
                    pocket.NUT_MAX_ACROSS_CORNERS_MM,
                ),
            }
            socket = cylinder(floor, depth, pocket.SOCKET_DIAMETER_MM)
            outside = socket.cut(pockets[key]).Volume()
            if outside > lower.TOL_MM3:
                socket_outside[key] = round(outside, 6)
            tools[key] = pocket._cylinder(
                far.toTuple(),
                direction.toTuple(),
                pocket.TOOL_APPROACH_MM,
                pocket.FORSTNER_DIAMETER_MM,
            )
            rows[key] = {
                "near_washer_at_original_face": math.isclose(
                    near.dot(direction),
                    min(
                        vertex.Center().dot(direction)
                        for vertex in parts[geometry.upright_name].Vertices()
                    ),
                    abs_tol=1e-6,
                ),
                "far_washer_at_pocket_floor": math.isclose(
                    floor.dot(direction),
                    min(
                        vertex.Center().dot(direction)
                        for vertex in pockets[key].Vertices()
                    ),
                    abs_tol=1e-6,
                ),
                "gross_bore_length_mm": bolt.length,
                "bore_start_to_near_face_mm": lower.END_ALLOWANCE_MM,
                "bolt_end_from_under_head_mm": pocket.BOLT_LENGTH_MM,
                "nut_end_from_under_head_mm": under_head_to_nut,
            }

    if len(installed) != 12:
        raise ValueError("PB04 upright installed stack inventory changed")
    other_stacks = {
        f"{station}/{bolt}/{role}": shape
        for station, geometry in geometries.items()
        for bolt, stack in geometry.stacks.items()
        if f"{station}/{bolt}" not in installed
        for role, shape in stack.items()
    }
    all_stacks = {
        **other_stacks,
        **{
            f"{key}/{role}": shape
            for key, stack in installed.items()
            for role, shape in stack.items()
        },
    }
    panels = {
        name: shape
        for name, shape in parts.items()
        if name.startswith(("main_", "kicker_"))
    }
    timber = {name: shape for name, shape in parts.items() if name not in panels}
    permanent_hits = {}
    tool_permanent_hits = {}
    tool_panel_hits = {}
    for key, stack in installed.items():
        station, bolt_name = key.split("/", 1)
        geometry = geometries[station]
        own_bore = geometry.bores[bolt_name]
        wood = {
            name: shape.cut(own_bore)
            if name in {geometry.upright_name, geometry.block_name}
            else shape
            for name, shape in timber.items()
        }
        others = {
            name: shape
            for name, shape in all_stacks.items()
            if not name.startswith(key + "/")
        }
        for role, shape in stack.items():
            hits = _hits(
                shape,
                {
                    **{f"wood/{name}": solid for name, solid in wood.items()},
                    **{f"panel/{name}": solid for name, solid in panels.items()},
                    **{f"axis/{name}": solid for name, solid in fixed_axes.items()},
                    **{f"stack/{name}": solid for name, solid in others.items()},
                },
            )
            permanent_hits.update(
                {f"{key}/{role}|{name}": volume for name, volume in hits.items()}
            )
        tool = tools[key]
        tool_permanent_hits.update(
            {
                f"{key}|{name}": volume
                for name, volume in _hits(
                    tool,
                    {
                        **{
                            f"wood/{name}": shape
                            for name, shape in timber.items()
                            if name != geometry.block_name
                        },
                        **{f"axis/{name}": shape for name, shape in fixed_axes.items()},
                        **{f"stack/{name}": shape for name, shape in others.items()},
                    },
                ).items()
            }
        )
        tool_panel_hits.update(
            {f"{key}|{name}": volume for name, volume in _hits(tool, panels).items()}
        )

    gates = {
        "gross_bores_preserved": gross_bores_preserved,
        "permanent_collisions_clear": not permanent_hits,
        "permanent_tool_access_clear": not tool_permanent_hits and not socket_outside,
        "threaded_nut": axial["threaded_nut_pass"],
        "two_thread_projection": axial["two_thread_projection_pass"],
        "tolerance_reserve": axial["tolerance_reserve_pass"],
    }
    return {
        "schema": "simple_pb04_installed_stack/v1",
        "source_id": pb04.SOURCE_ID,
        "source_fingerprint_sha256": pb04._source_fingerprint(module),
        "hardware_sources": pocket.HARDWARE_SOURCES,
        "fixed_panel_kicker_axes": len(module.panel_connections()),
        "gross_bores_preserved": gross_bores_preserved,
        "axial_mm": axial,
        "stacks": rows,
        "permanent_collision_hits_mm3": permanent_hits,
        "tool_permanent_hits_mm3": tool_permanent_hits,
        "tool_removable_panel_hits_mm3": tool_panel_hits,
        "socket_outside_pocket_mm3": socket_outside,
        "gates": gates,
        "decision": "PASS_GEOMETRY_ONLY" if all(gates.values()) else "REVISE",
        "qualified_for_design": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
