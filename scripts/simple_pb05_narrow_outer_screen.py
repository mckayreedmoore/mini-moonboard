"""Detached simultaneous PB04 narrow outer geometry and nominal hardware screen."""

import json
import math
from unittest.mock import patch

import cadquery as cq

from scripts import simple_pb03_bottom_outer_pair as bottom
from scripts import simple_pb03_cross_family as cross
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_outer_counterbore_revision as hardware
from scripts import simple_pb03_upper_outer_pair as upper
from scripts import simple_pb04_native as pb04

BLOCK_X_MM = 95.25
RAIL_X_OFFSETS_MM = (25.0, 70.0)
OUTER_STATIONS = (
    *lower.LOWER_OUTER_STATIONS,
    *upper.TARGET_STATIONS,
    *bottom.TARGET_STATIONS,
)


def _hits(shape, others):
    return {
        name: round(volume, 6)
        for name, other in others.items()
        if (volume := lower._intersection_volume(shape, other)) > lower.TOL_MM3
    }


def _nonempty(value):
    if isinstance(value, dict):
        return {key: kept for key, item in value.items() if (kept := _nonempty(item))}
    return value


def _axis(row):
    return cq.Solid.makeCylinder(row.diameter / 2, row.length, row.start, row.direction)


def _signature(row):
    return (
        row.name,
        row.start.toTuple(),
        row.direction.toTuple(),
        row.length,
        row.diameter,
        row.members,
        row.kind,
        row.grip,
    )


def _installed_upright(bolt):
    """Purchased 8-in shaft and actual washer/nut envelopes at nominal grip."""
    direction = bolt.direction.normalized()
    near = bolt.start + direction * lower.END_ALLOWANCE_MM
    far = near + direction * bolt.grip
    head_start = near - direction * hardware.WASHER_EACH_SIDE_MM

    def cylinder(point, length, diameter):
        return hardware._cylinder(
            point.toTuple(), direction.toTuple(), length, diameter
        )

    return {
        "shaft": cylinder(head_start, hardware.BOLT_LENGTH_MM, lower.BOLT_DIAMETER_MM),
        "head": cylinder(head_start - direction * 6, 6, lower.HEAD_NUT_DIAMETER_MM),
        "near_washer": cylinder(
            head_start,
            hardware.WASHER_EACH_SIDE_MM,
            hardware.WASHER_OUTSIDE_DIAMETER_MM,
        ),
        "far_washer": cylinder(
            far, hardware.WASHER_EACH_SIDE_MM, hardware.WASHER_OUTSIDE_DIAMETER_MM
        ),
        "nut": cylinder(
            far + direction * hardware.WASHER_EACH_SIDE_MM,
            hardware.NUT_HEIGHT_MM,
            hardware.NUT_MAX_ACROSS_CORNERS_MM,
        ),
    }


def _end_edge(geometry):
    """Provisional 4D N-center/3-mm net end and 3-mm tool X-edge screens."""
    openings = {}
    for bolt in geometry.bolts:
        n = (
            lower.UPRIGHT_N_OFFSETS_MM[int(bolt.name.rsplit("_", 1)[1]) - 1]
            if bolt.members[0] == geometry.upright_name
            else geometry.report["rail_bore_n_offset_mm"]
        )
        openings[bolt.name] = {
            "n_center_near_mm": n,
            "n_center_far_mm": geometry.block_length_mm - n,
            "n_net_near_mm": n - lower.WASHER_DIAMETER_MM / 2,
            "n_net_far_mm": geometry.block_length_mm - n - lower.WASHER_DIAMETER_MM / 2,
        }
    butt = geometry.report["butt_faces_x_mm"]["upright"]
    sign = 1 if geometry.rail_extension_direction == "right" else -1
    rail = [bolt for bolt in geometry.bolts if bolt.members[0] == geometry.rail_name]
    offsets = tuple(sign * (bolt.start.x - butt) for bolt in rail)
    x_reserves = tuple(
        min(
            offset - lower.TOOL_DIAMETER_MM / 2,
            BLOCK_X_MM - offset - lower.TOOL_DIAMETER_MM / 2,
        )
        for offset in offsets
    )
    return (
        openings,
        offsets,
        x_reserves,
        {
            "grain_end": all(
                min(row["n_center_near_mm"], row["n_center_far_mm"])
                >= 4 * lower.BOLT_DIAMETER_MM
                and min(row["n_net_near_mm"], row["n_net_far_mm"]) >= 3
                for row in openings.values()
            ),
            "rail_x_edge": min(x_reserves) >= 3
            and offsets[1] - offsets[0] > lower.TOOL_DIAMETER_MM,
        },
    )


def screen():
    """Screen six revised outers together while preserving both PB04 centers."""
    module = pb04.PB04Native()
    reference = module.pb03_geometries()
    parts, finished, panels, _, source_connections = lower._source_inventory()
    if (
        module.KEY != pb04.SOURCE_ID
        or module.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT
        or len(reference) != 8
        or set(reference) != set(OUTER_STATIONS) | set(lower.TARGET_STATIONS)
        or not math.isclose(pb04.SELECTED_OFFSET_MM, 35.709, abs_tol=1e-9)
    ):
        raise ValueError("PB04 source or relocated row changed")
    panel_axes = tuple(module.panel_connections())
    frame_axes = tuple(
        row
        for row in module.connections()
        if row.kind == "bolt" and not row.name.startswith("pb03_")
    )
    source_frame = tuple(row for row in source_connections if row.kind == "bolt")
    if (
        len(panel_axes) != 66
        or len(panels) != 66
        or len(frame_axes) != 12
        or len(source_frame) != 12
    ):
        raise ValueError("fixed source axes changed")
    # Compare actual records, not just their counts.
    if (
        tuple(map(_signature, panel_axes)) != tuple(map(_signature, panels))
        or tuple(map(_signature, frame_axes)) != tuple(map(_signature, source_frame))
        or len(module.legacy_proxy_stations()) != 14
    ):
        raise ValueError("fixed source duties or axes changed")
    axes = lower._fixed_axis_solids(panel_axes)
    frame_solids = {row.name: _axis(row) for row in frame_axes}
    specs = {**lower.STATION_SPECS, **upper.STATION_SPECS, **bottom.STATION_SPECS}
    # ponytail: scope producer constants to this detached rebuild only.
    with (
        patch.object(lower, "BLOCK_X_MM", BLOCK_X_MM),
        patch.object(lower, "RAIL_X_OFFSETS_MM", RAIL_X_OFFSETS_MM),
    ):
        trial = {
            name: lower._build_station(
                specs[name],
                parts,
                finished,
                axes,
                rail_n_offset_mm=(
                    pb04.SELECTED_OFFSET_MM
                    if name in upper.TARGET_STATIONS
                    else lower.RAIL_N_OFFSET_MM
                ),
            )
            for name in OUTER_STATIONS
        }
    centers = {name: reference[name] for name in lower.TARGET_STATIONS}
    assembled = {**centers, **trial}
    panel_solids = {
        name: shape
        for name, shape in finished.items()
        if name.startswith(("main_", "kicker_"))
    }
    station_rows = {}
    for name, geometry in trial.items():
        old = reference[name]
        others = {key: item for key, item in assembled.items() if key != name}
        interactions = cross.screen_cross_family({name: geometry}, others)
        openings, offsets, x_reserves, end_edge = _end_edge(geometry)
        upright = [
            bolt for bolt in geometry.bolts if bolt.members[0] == geometry.upright_name
        ]
        rail = [
            bolt for bolt in geometry.bolts if bolt.members[0] == geometry.rail_name
        ]
        if len(upright) != 2 or len(rail) != 2:
            raise ValueError(f"{name}: four-bolt inventory changed")
        installed = {bolt.name: _installed_upright(bolt) for bolt in upright}
        for bolt in rail:
            # Generic PB03 seat/nut dimensions; nominal 5-in shaft reaches its real end.
            stack = dict(geometry.stacks[bolt.name])
            direction = bolt.direction.normalized()
            near = bolt.start + direction * lower.END_ALLOWANCE_MM
            stack["shaft"] = hardware._cylinder(
                (near - direction * 2).toTuple(),
                direction.toTuple(),
                5 * hardware.MM_PER_IN,
                lower.BOLT_DIAMETER_MM,
            )
            installed[bolt.name] = stack
        neighboring = {
            **{f"block/{key}": item.block for key, item in others.items()},
            **{
                f"bore/{key}/{bolt}": shape
                for key, item in others.items()
                for bolt, shape in item.bores.items()
            },
            **{
                f"stack/{key}/{bolt}/{role}": shape
                for key, item in others.items()
                for bolt, stack in item.stacks.items()
                for role, shape in stack.items()
            },
        }
        fixed = {
            **{f"panel/{key}": shape for key, shape in panel_solids.items()},
            **{f"panel_axis/{key}": shape for key, shape in axes.items()},
            **{f"frame_axis/{key}": shape for key, shape in frame_solids.items()},
            **{
                f"wood/{key}": shape
                for key, shape in finished.items()
                if key
                not in (geometry.upright_name, geometry.rail_name, geometry.block_name)
                and key not in panel_solids
            },
        }
        block_hits = _hits(geometry.block, {**neighboring, **fixed})
        bore_hits = {
            f"{bolt}|{target}": volume
            for bolt, shape in geometry.bores.items()
            for target, volume in _hits(shape, {**neighboring, **fixed}).items()
        }
        tool_hits = {
            f"{bolt}/{end}|{target}": volume
            for bolt, ends in geometry.tools.items()
            for end, shape in ends.items()
            for target, volume in _hits(shape, fixed).items()
        }
        stack_hits = {}
        for bolt in geometry.bolts:
            components = installed.get(bolt.name, geometry.stacks[bolt.name])
            own_other = {
                f"own/{other}/{role}": shape
                for other, stack in {**geometry.stacks, **installed}.items()
                if other != bolt.name
                for role, shape in stack.items()
            }
            own_other.update(
                {
                    f"own_bore/{other}": shape
                    for other, shape in geometry.bores.items()
                    if other != bolt.name
                }
            )
            for role, shape in components.items():
                stack_hits.update(
                    {
                        f"{bolt.name}/{role}|{target}": volume
                        for target, volume in _hits(
                            shape, {**neighboring, **fixed, **own_other}
                        ).items()
                    }
                )
        local = geometry.report
        local_hits = _nonempty(
            {key: value for key, value in local.items() if key.endswith("_hits_mm3")}
        )
        required_upright = (
            upright[0].grip
            + 2 * hardware.WASHER_EACH_SIDE_MM
            + hardware.NUT_HEIGHT_MM
            + hardware.TWO_THREAD_PROJECTION_MM
        )
        required_rail = (
            rail[0].grip
            + 2 * hardware.WASHER_EACH_SIDE_MM
            + hardware.NUT_HEIGHT_MM
            + hardware.TWO_THREAD_PROJECTION_MM
        )
        grip = {
            "upright_8in_nominal_margin_mm": hardware.BOLT_LENGTH_MM - required_upright,
            "rail_5in_nominal_margin_mm": 5 * hardware.MM_PER_IN - required_rail,
            "upright_nut_on_listed_thread": (
                hardware.WASHER_EACH_SIDE_MM
                + upright[0].grip
                + hardware.WASHER_EACH_SIDE_MM
                >= hardware.BOLT_LENGTH_MM - hardware.BOLT_LISTED_THREAD_LENGTH_MM
            ),
            "rail_5in_basis": "nominal length with generic PB03 rail stack; retail rail bolt unselected",
        }
        obstructions = {
            "local": local_hits,
            "other_stations": _nonempty(
                {
                    key: value
                    for key, value in interactions.items()
                    if key.endswith("hits_mm3")
                }
            ),
            "block": block_hits,
            "bore": bore_hits,
            "tool_to_fixed": tool_hits,
            "installed_or_generic_stack": stack_hits,
        }
        gates = {
            "contact_and_complete_bores": local["contact_verified"]
            and local["complete_bores"],
            "local_collision_and_access": local["collision_clear"]
            and local["access_clear"],
            "cross_family": interactions["all_cross_family_collision_gates_pass"],
            "block_bore_stack_tool_clear": not any(
                (block_hits, bore_hits, stack_hits, tool_hits)
            ),
            "nominal_grip": grip["upright_8in_nominal_margin_mm"] >= 0
            and grip["rail_5in_nominal_margin_mm"] >= 0
            and grip["upright_nut_on_listed_thread"],
            **end_edge,
        }
        station_rows[name] = {
            "block_dimensions_mm": local["block_dimensions_mm"],
            "upper_rail_n_offset_mm": local["rail_bore_n_offset_mm"],
            "rail_x_offsets_from_butt_mm": offsets,
            "rail_tool_x_edge_reserves_mm": x_reserves,
            "upright_grip_mm": upright[0].grip,
            "rail_grip_mm": rail[0].grip,
            "nominal_grip": grip,
            "end_openings_mm": openings,
            "end_edge_gates": end_edge,
            "contact_area_mm2": local["contact_area_mm2"],
            "contact_area_change_mm2": {
                face: local["contact_area_mm2"][face]
                - old.report["contact_area_mm2"][face]
                for face in ("rail", "upright")
            },
            "obstructions_mm3": obstructions,
            "gates": gates,
            "decision": "PASS_GEOMETRY_ONLY"
            if all(gates.values())
            else "REJECT_GEOMETRY",
        }
    return {
        "schema": "simple_pb05_narrow_outer_screen/v1",
        "source_id": pb04.SOURCE_ID,
        "fixed_axis_source": "PB02 kerf-right finished panel/connection inventory",
        "outer_geometry_source": "PB04 station geometry, detached uncounterbored six-station rebuild",
        "inventory": {
            "outer_stations": len(trial),
            "unchanged_center_stations": len(centers),
            "outer_bolt_axes": sum(len(item.bolts) for item in trial.values()),
            "fixed_panel_kicker_axes": len(axes),
            "original_frame_bolt_axes": len(frame_axes),
            "legacy_duties": len(module.legacy_proxy_stations()),
        },
        "counterbores": 0,
        "stations": station_rows,
        "decision": "ADVANCE_GEOMETRY_ONLY"
        if all(row["decision"] == "PASS_GEOMETRY_ONLY" for row in station_rows.values())
        else "REJECT_GEOMETRY",
        "force_transfer": False,
        "native_solve": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
