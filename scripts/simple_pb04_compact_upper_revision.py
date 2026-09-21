"""Detached upper-outer compact block screen against signed PB04 a12-forward."""

import json
import math
from dataclasses import replace

import cadquery as cq

from scripts import simple_pb03_cross_family as cross
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_outer_counterbore_revision as pocket
from scripts import simple_pb03_upper_outer_pair as upper
from scripts import simple_pb04_first_case_demand as demand
from scripts import simple_pb04_native as pb04
from scripts import simple_pb04_six_inch_block_screen as six
from scripts import simple_rail_joint_comparison as pb01

FRONT_EXTENSION_MM = 11.741
SIX_INCH_MM = 152.4
LENGTH_MM = SIX_INCH_MM + FRONT_EXTENSION_MM
STATION = upper.TARGET_STATIONS[0]


def _hits(shape, others):
    return six._hits(shape, others)


def screen():
    signed = demand.analyze()  # Authenticates the unchanged report and PB04 source.
    reference = pb04.PB04Native().pb03_geometries()
    parts, finished, panels, _, _ = lower._source_inventory()
    axes = lower._fixed_axis_solids(panels)
    built = lower._build_station(
        upper.STATION_SPECS[STATION],
        parts,
        finished,
        axes,
        rail_n_offset_mm=pb04.SELECTED_OFFSET_MM,
        block_length_mm=LENGTH_MM,
    )
    # ponytail: translate only the solid; the producer already fixes every bolt axis.
    shift = cq.Vector(0, *pb01.N) * -FRONT_EXTENSION_MM
    candidate = replace(built, block=built.block.translate(shift))
    old = reference[STATION]
    others = {name: item for name, item in reference.items() if name != STATION}
    composed = {**others, STATION: candidate}
    pockets, cut = pocket.build_counterbored_blocks(composed)
    own_pockets = {
        name: shape for name, shape in pockets.items() if name.startswith(STATION + "/")
    }
    other_pockets = {
        name: shape for name, shape in pockets.items() if name not in own_pockets
    }
    foreign = {
        **{f"block/{name}": item.block for name, item in others.items()},
        **{
            f"bore/{station}/{name}": shape
            for station, item in others.items()
            for name, shape in item.bores.items()
        },
        **{
            f"stack/{station}/{bolt}/{role}": shape
            for station, item in others.items()
            for bolt, stack in item.stacks.items()
            for role, shape in stack.items()
        },
    }
    all_tools = {
        f"{station}/{bolt}/{end}": shape
        for station, item in others.items()
        for bolt, ends in item.tools.items()
        for end, shape in ends.items()
    }
    other_hits = _hits(candidate.block, foreign)
    fixed_hits = _hits(candidate.block, axes)
    unrelated_timber = {
        name: shape
        for name, shape in finished.items()
        if name not in (candidate.upright_name, candidate.rail_name)
    }
    timber_hits = _hits(candidate.block, unrelated_timber)
    baseline_timber_hits = _hits(old.block, unrelated_timber)
    tool_hits = _hits(candidate.block, all_tools)
    cross_hits = cross.screen_cross_family({STATION: candidate}, others)
    own_pocket_hits = {
        name: _hits(
            shape,
            {
                **foreign,
                **{
                    f"own_bore/{bolt}": bore
                    for bolt, bore in candidate.bores.items()
                    if bolt != name.split("/", 1)[1]
                },
                **{
                    f"own_stack/{bolt}/{role}": solid
                    for bolt, stack in candidate.stacks.items()
                    if bolt != name.split("/", 1)[1]
                    for role, solid in stack.items()
                },
            },
        )
        for name, shape in own_pockets.items()
    }
    neighbor_pocket_hits = {
        name: _hits(shape, {"block": candidate.block})
        for name, shape in other_pockets.items()
    }
    pocket_inside = all(
        math.isclose(
            lower._intersection_volume(shape, candidate.block),
            shape.Volume(),
            abs_tol=lower.TOL_MM3,
        )
        for shape in own_pockets.values()
    )
    pocket_tool_hits = {}
    for name, shape in own_pockets.items():
        bolt = next(row for row in candidate.bolts if row.name == name.split("/", 1)[1])
        axis = bolt.direction.normalized()
        outside = bolt.start + axis * (lower.END_ALLOWANCE_MM + bolt.grip)
        approach = pocket._cylinder(
            outside.toTuple(),
            axis.toTuple(),
            pocket.TOOL_APPROACH_MM,
            pocket.FORSTNER_DIAMETER_MM,
        )
        pocket_tool_hits[name] = _hits(
            approach,
            {
                **{f"timber/{key}": value for key, value in finished.items()},
                **foreign,
                **{f"axis/{key}": value for key, value in axes.items()},
                **{
                    f"own_stack/{other}/{role}": solid
                    for other, stack in candidate.stacks.items()
                    if other != bolt.name
                    for role, solid in stack.items()
                },
            },
        )
    force_rows = {
        row["name"]: row for row in signed["bolts"] if row["station"] == STATION
    }
    signed_rows = {}
    for name, row in force_rows.items():
        members = {}
        for member in row["members"]:
            direction = row["member_directions"][member]
            shape = candidate.block if member == candidate.block_name else parts[member]
            members[member] = demand._direction(
                shape,
                row["point_xyz_mm"],
                direction["lateral_force_xyz_n"],
                direction["grain_axis_xyz"],
                direction["edge_axis_xyz"],
            )
        signed_rows[name] = members
    n_axis = (0, *pb01.N)
    front, rear = demand._extent(candidate.block, n_axis)
    old_front, old_rear = demand._extent(old.block, n_axis)
    six_rear = old_front + SIX_INCH_MM
    overlap = lower._intersection_volume(candidate.block, old.block)
    openings = six._opening_end_ligaments(candidate, own_pockets)
    # The producer's opening offsets are measured from the old front face.
    openings = {
        name: {
            **row,
            "near_mm": row["near_mm"] + FRONT_EXTENSION_MM,
            "far_mm": row["far_mm"] - FRONT_EXTENSION_MM,
            "center_near_mm": row["center_near_mm"] + FRONT_EXTENSION_MM,
            "center_far_mm": row["center_far_mm"] - FRONT_EXTENSION_MM,
        }
        for name, row in openings.items()
    }
    clearance = all(
        row["near_mm"] >= six.OPENING_LIGAMENT_ALLOWANCE_MM
        and row["far_mm"] >= six.OPENING_LIGAMENT_ALLOWANCE_MM
        and (
            not name.endswith("/bore")
            or min(row["center_near_mm"], row["center_far_mm"])
            >= 4 * lower.BOLT_DIAMETER_MM
        )
        for name, row in openings.items()
    )
    gates = {
        "bolts_unchanged": all(
            (a.start - b.start).Length < 1e-8
            and (a.direction - b.direction).Length < 1e-8
            for a, b in zip(candidate.bolts, old.bolts, strict=True)
        ),
        "compact_solid": math.isclose(
            overlap, old.block.Volume() * SIX_INCH_MM / 300, abs_tol=lower.TOL_MM3
        )
        and math.isclose(
            candidate.block.Volume(),
            old.block.Volume() * LENGTH_MM / 300,
            abs_tol=lower.TOL_MM3,
        ),
        "both_member_signed_7d_4d": all(
            check["passes"]
            for members in signed_rows.values()
            for check in members.values()
        ),
        "opening_4d_clearance": clearance,
        "complete_bores": all(
            math.isclose(
                lower._intersection_volume(candidate.block, bore),
                lower._intersection_volume(old.block, bore),
                abs_tol=lower.TOL_MM3,
            )
            for bore in candidate.bores.values()
        ),
        "contact": all(
            lower._contact_area(candidate.block, parts[member], inward) > 0
            for member, inward in (
                (candidate.rail_name, (0, -pb01.T[0], -pb01.T[1])),
                (
                    candidate.upright_name,
                    (1 if candidate.rail_extension_direction == "left" else -1, 0, 0),
                ),
            )
        ),
        "no_block_or_axis_collisions": not (other_hits or fixed_hits or timber_hits),
        "no_stack_tool_collisions": not tool_hits
        and cross_hits["all_cross_family_collision_gates_pass"],
        "pockets_clear": pocket_inside
        and not any(own_pocket_hits.values())
        and not any(neighbor_pocket_hits.values()),
        "pocket_tools_clear": not any(pocket_tool_hits.values()),
    }
    return {
        "schema": "simple_pb04_compact_upper_revision/v1",
        "station": STATION,
        "signed_case": signed["case"],
        "source_id": signed["candidate"],
        "block_length_mm": LENGTH_MM,
        "front_extension_mm": FRONT_EXTENSION_MM,
        "projected_n_ends_mm": {
            "front": front,
            "rear": rear,
            "pb04_front": old_front,
            "pb04_rear": old_rear,
            "unshifted_six_inch_rear": six_rear,
        },
        "block_volume_mm3": candidate.block.Volume(),
        "overlap_with_pb04_mm3": overlap,
        "cut_block_volume_mm3": cut[STATION].Volume(),
        "contact_areas_mm2": {
            "rail": lower._contact_area(
                candidate.block, parts[candidate.rail_name], (0, -pb01.T[0], -pb01.T[1])
            ),
            "upright": lower._contact_area(
                candidate.block,
                parts[candidate.upright_name],
                (1 if candidate.rail_extension_direction == "left" else -1, 0, 0),
            ),
        },
        "pb04_contact_areas_mm2": old.report["contact_area_mm2"],
        "signed_end_edge": signed_rows,
        "opening_end_clearances_mm": openings,
        "collision_hits_mm3": {
            "other": other_hits,
            "fixed_axes": fixed_hits,
            "timber_and_panels": timber_hits,
            "other_tools": tool_hits,
            "pb04_timber_and_panels": baseline_timber_hits,
            "cross_family": cross_hits,
            "own_pockets": own_pocket_hits,
            "other_pockets": neighbor_pocket_hits,
            "pocket_tools": pocket_tool_hits,
        },
        "fixed_panel_kicker_axes": len(panels),
        "gates": gates,
        "geometry_decision": "ADVANCE_GEOMETRY_ONLY"
        if all(gates.values())
        else "REVISE_GEOMETRY",
        "physical_barrier": "No cut-net-section, paired-bolt group, splitting, six-case demand envelope, or physical fit qualification; no fabrication release.",
        "solve_run": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
