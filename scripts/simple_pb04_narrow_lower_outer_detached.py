"""One detached PB04 lower-outer narrow-block geometry and nominal stack screen."""

import json
import math
from unittest.mock import patch

from scripts import simple_pb03_cross_family as cross
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_outer_counterbore_revision as hardware
from scripts import simple_pb04_native as pb04

STATION = lower.LOWER_OUTER_STATIONS[0]
BLOCK_X_MM = 95.25
RAIL_X_OFFSETS_MM = (25.0, 70.0)
CONDITIONAL_SHORTFALL_MM = 4.572


def _hits(shape, others):
    return {
        name: round(volume, 6)
        for name, other in others.items()
        if (volume := lower._intersection_volume(shape, other)) > lower.TOL_MM3
    }


def screen():
    """Use actual kerf-right hosts and seven unchanged PB04 station solids."""
    module = pb04.PB04Native()
    if (
        module.KEY != pb04.SOURCE_ID
        or module.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT
    ):
        raise ValueError("PB04 source changed")
    reference = module.pb03_geometries()
    parts, finished, panels, _, _ = lower._source_inventory()
    if len(reference) != 8 or len(panels) != 66:
        raise ValueError("PB04 station or panel-axis inventory changed")
    axes = lower._fixed_axis_solids(panels)
    # ponytail: scope the two producer constants to this one detached rebuild.
    with (
        patch.object(lower, "BLOCK_X_MM", BLOCK_X_MM),
        patch.object(lower, "RAIL_X_OFFSETS_MM", RAIL_X_OFFSETS_MM),
    ):
        trial = lower._build_station(
            lower.STATION_SPECS[STATION], parts, finished, axes
        )
    old = reference[STATION]
    others = {name: row for name, row in reference.items() if name != STATION}
    if not math.isclose(old.report["block_dimensions_mm"][0], 139.7):
        raise ValueError("original block width changed")
    cross_result = cross.screen_cross_family({STATION: trial}, others)
    upright = [row for row in trial.bolts if row.members[0] == trial.upright_name]
    rail = [row for row in trial.bolts if row.members[0] == trial.rail_name]
    if len(upright) != 2 or len(rail) != 2:
        raise ValueError("four-bolt station changed")

    # X offsets are measured inward from the actual rail/upright butt face.
    butt = trial.report["butt_faces_x_mm"]["upright"]
    sign = 1 if trial.rail_extension_direction == "right" else -1
    rail_offsets = tuple(sign * (bolt.start.x - butt) for bolt in rail)
    edge = (rail_offsets[0], BLOCK_X_MM - rail_offsets[1])
    rail_spacing = rail_offsets[1] - rail_offsets[0]
    rail_envelope_radius = lower.TOOL_DIAMETER_MM / 2
    layout = {
        "rail_x_offsets_from_butt_mm": rail_offsets,
        "rail_center_spacing_mm": rail_spacing,
        "rail_center_end_distances_mm": edge,
        "rail_tool_edge_reserves_mm": tuple(x - rail_envelope_radius for x in edge),
        "upright_n_offsets_mm": lower.UPRIGHT_N_OFFSETS_MM,
        "distinct_upright_axes": upright[0].start != upright[1].start,
        "rail_layout_clear": rail_spacing > lower.TOOL_DIAMETER_MM
        and min(edge) > rail_envelope_radius,
    }

    installed = {}
    tools = {}
    for bolt in upright:
        direction = bolt.direction.normalized()
        near = bolt.start + direction * lower.END_ALLOWANCE_MM
        far = near + direction * bolt.grip
        head_start = near - direction * hardware.WASHER_EACH_SIDE_MM
        cylinder = lambda point, length, diameter, direction=direction: (
            hardware._cylinder(point.toTuple(), direction.toTuple(), length, diameter)
        )
        installed[bolt.name] = {
            "shaft": cylinder(
                head_start, hardware.BOLT_LENGTH_MM, lower.BOLT_DIAMETER_MM
            ),
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
        tools[bolt.name] = {
            "socket": cylinder(
                far, hardware.TOOL_APPROACH_MM, hardware.SOCKET_DIAMETER_MM
            ),
            "approach": cylinder(
                far, hardware.TOOL_APPROACH_MM, hardware.FORSTNER_DIAMETER_MM
            ),
        }

    neighboring = {
        **{f"block/{name}": row.block for name, row in others.items()},
        **{
            f"bore/{name}/{bolt}": bore
            for name, row in others.items()
            for bolt, bore in row.bores.items()
        },
        **{
            f"stack/{name}/{bolt}/{role}": shape
            for name, row in others.items()
            for bolt, stack in row.stacks.items()
            for role, shape in stack.items()
        },
    }
    panels_solids = {
        name: shape
        for name, shape in finished.items()
        if name.startswith(("main_", "kicker_"))
    }
    nonhosts = {
        name: shape
        for name, shape in finished.items()
        if name not in (trial.block_name, trial.upright_name, trial.rail_name)
    }
    blockers = {
        **neighboring,
        **{f"panel/{name}": shape for name, shape in panels_solids.items()},
        **{f"axis/{name}": shape for name, shape in axes.items()},
        **{f"wood/{name}": shape for name, shape in nonhosts.items()},
    }
    hardware_hits = {}
    tool_hits = {}
    for name, stack in installed.items():
        own_bore = trial.bores[name]
        own_other = {
            f"own/{bolt}/{role}": shape
            for bolt, components in installed.items()
            if bolt != name
            for role, shape in components.items()
        }
        own_other.update(
            {
                f"rail/{bolt}/{role}": shape
                for bolt, components in trial.stacks.items()
                if bolt in {row.name for row in rail}
                for role, shape in components.items()
            }
        )
        own_other.update(
            {
                f"bore/{bolt}": shape
                for bolt, shape in trial.bores.items()
                if bolt != name
            }
        )
        host_wood = {
            f"host/{member}": (
                trial.block if member == trial.block_name else finished[member]
            ).cut(own_bore)
            for member in (trial.block_name, trial.upright_name)
        }
        for role, shape in stack.items():
            hardware_hits.update(
                {
                    f"{name}/{role}|{target}": volume
                    for target, volume in _hits(
                        shape, {**blockers, **own_other, **host_wood}
                    ).items()
                }
            )
        for role, shape in tools[name].items():
            tool_hits.update(
                {
                    f"{name}/{role}|{target}": volume
                    for target, volume in _hits(
                        shape,
                        {
                            **blockers,
                            **own_other,
                            **{
                                f"host/{member}": finished[member]
                                for member in (trial.upright_name, trial.rail_name)
                            },
                        },
                    ).items()
                }
            )

    grip = upright[0].grip
    nominal_need = (
        grip
        + 2 * hardware.WASHER_EACH_SIDE_MM
        + hardware.NUT_HEIGHT_MM
        + hardware.TWO_THREAD_PROJECTION_MM
    )
    nominal_margin = hardware.BOLT_LENGTH_MM - nominal_need
    conditional_margin = (
        hardware.BOLT_LENGTH_MM - CONDITIONAL_SHORTFALL_MM - nominal_need
    )
    stack = {
        "nominal_bolt_under_head_mm": hardware.BOLT_LENGTH_MM,
        "wood_grip_mm": grip,
        "washers_total_mm": 2 * hardware.WASHER_EACH_SIDE_MM,
        "nut_height_mm": hardware.NUT_HEIGHT_MM,
        "two_thread_projection_mm": hardware.TWO_THREAD_PROJECTION_MM,
        "nominal_required_mm": nominal_need,
        "nominal_margin_mm": nominal_margin,
        "conditional_shortfall_mm": CONDITIONAL_SHORTFALL_MM,
        "conditional_margin_mm": conditional_margin,
        "conditional_case_is_product_tolerance": False,
        "nut_starts_on_listed_thread": hardware.WASHER_EACH_SIDE_MM
        + grip
        + hardware.WASHER_EACH_SIDE_MM
        >= hardware.BOLT_LENGTH_MM - hardware.BOLT_LISTED_THREAD_LENGTH_MM,
    }
    gates = {
        "host_faces_coincident": trial.report["butt_faces_coincident"]
        and trial.report["contact_verified"],
        "uncut_upright_grip": all(
            math.isclose(bolt.grip, 184.15, abs_tol=1e-8) for bolt in upright
        ),
        "rail_layout": layout["rail_layout_clear"] and layout["distinct_upright_axes"],
        "four_complete_bores": trial.report["complete_bores"],
        "local_envelopes": trial.report["collision_clear"]
        and trial.report["access_clear"],
        "seven_neighbors": cross_result["all_cross_family_collision_gates_pass"],
        "exact_stack_envelopes": not hardware_hits,
        "exact_tool_envelopes": not tool_hits,
        "fixed_66_axes": len(axes) == 66,
        "nominal_eight_inch_stack": nominal_margin >= 0
        and stack["nut_starts_on_listed_thread"],
    }
    return {
        "station": STATION,
        "source_id": pb04.SOURCE_ID,
        "block_dimensions_mm": trial.report["block_dimensions_mm"],
        "original_upright_wood_grip_mm": upright[0].grip + (139.7 - BLOCK_X_MM),
        "layout": layout,
        "stack": stack,
        "local_report": trial.report,
        "neighbor_hits": {
            key: value
            for key, value in cross_result.items()
            if key.endswith("hits_mm3") and value
        },
        "exact_hardware_hits_mm3": hardware_hits,
        "exact_tool_hits_mm3": tool_hits,
        "gates": gates,
        "decision": "ADVANCE_GEOMETRY_ONLY"
        if all(gates.values())
        else "REJECT_GEOMETRY",
        "old_force_transfer": False,
        "solve_run": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
