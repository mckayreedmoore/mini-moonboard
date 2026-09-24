"""Diagnostic-only WJ-03 fastener and panel transport sequence screens.

This script tests nominal CAD movement envelopes against maintained geometry.
It does not select tools, prove support/retention, model wood tolerances, or
accept any fabrication or removal operation.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import cadquery as cq

from mini_moonboard import hold_tnut_reinforcement as hold_tnuts
from mini_moonboard.wood_joint_frame import (
    LEGACY_DUTIES,
    TOOL_DIAMETER_MM,
    TOOL_LENGTH_MM,
    access_shapes,
    build_outer_nodes,
)
from scripts.owner_layout_protected import inventory as protected_inventory
from scripts.wood_joints_wj05_center_backer_transfer_probe import (
    _source_and_candidate as build_wj05_center_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs/wood-joints-mvp/source-inventory.json"
OUTPUT = ROOT / "docs/wood-joints-mvp/wj03-sequence-diagnostic.json"
HIT_MM3 = 1e-4
SEQUENCE_DEPENDENCIES = (
    "mini_moonboard/connection_geometry.py",
    "mini_moonboard/floor_flush_width.py",
    "mini_moonboard/hold_tnut_reinforcement.py",
    "mini_moonboard/model.py",
    "mini_moonboard/panel_grid.py",
    "mini_moonboard/panel_grid_v2.py",
    "mini_moonboard/wood_joint_frame.py",
    "mini_moonboard/wood_joint_geometry.py",
    "scripts/owner_layout_protected.py",
    "scripts/wood_joints_wj05_center_backer_transfer_probe.py",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _vec(values) -> cq.Vector:
    return cq.Vector(*values)


def _bounds(shape: cq.Shape) -> dict[str, float]:
    box = shape.BoundingBox()
    return {
        "xmin": box.xmin,
        "xmax": box.xmax,
        "ymin": box.ymin,
        "ymax": box.ymax,
        "zmin": box.zmin,
        "zmax": box.zmax,
    }


def _overlap(a, b) -> bool:
    return not (
        a.xmax < b.xmin
        or b.xmax < a.xmin
        or a.ymax < b.ymin
        or b.ymax < a.ymin
        or a.zmax < b.zmin
        or b.zmax < a.zmin
    )


def _volume(first, second, first_box=None, second_box=None) -> float:
    first_box = first.BoundingBox() if first_box is None else first_box
    second_box = second.BoundingBox() if second_box is None else second_box
    if not _overlap(first_box, second_box):
        return 0.0
    return first.intersect(second).Volume()


def _axis_cylinder(record, length: float, diameter: float) -> cq.Shape:
    origin = _vec(record["origin_global_xyz_mm"])
    direction = _vec(record["axis_global_xyz"]).normalized()
    return cq.Solid.makeCylinder(diameter / 2, length, origin, direction)


def _path_screen(
    moving: cq.Shape,
    obstacles: dict[str, cq.Shape],
    direction: cq.Vector,
    distance: float,
    step: float,
) -> dict:
    """Sample one straight translation; report positive-volume intersections."""
    direction = direction.normalized()
    initial = moving.BoundingBox()
    terminal = moving.translate(direction * distance).BoundingBox()
    swept = initial.add(terminal)
    nearby = {
        name: (shape, shape.BoundingBox())
        for name, shape in obstacles.items()
        if _overlap(swept, shape.BoundingBox())
    }
    samples = max(1, math.ceil(distance / step))
    hits = defaultdict(
        lambda: {"first_mm": None, "last_mm": None, "max_volume_mm3": 0.0}
    )
    for index in range(1, samples + 1):
        moved_mm = min(distance, index * step)
        moved = moving.translate(direction * moved_mm)
        moved_box = moved.BoundingBox()
        for name, (obstacle, obstacle_box) in nearby.items():
            if not _overlap(moved_box, obstacle_box):
                continue
            volume = _volume(moved, obstacle, moved_box, obstacle_box)
            if volume <= HIT_MM3:
                continue
            row = hits[name]
            if row["first_mm"] is None:
                row["first_mm"] = round(moved_mm, 4)
            row["last_mm"] = round(moved_mm, 4)
            row["max_volume_mm3"] = max(row["max_volume_mm3"], volume)
    return {
        "distance_mm": distance,
        "step_mm": step,
        "positive_volume_hit_tolerance_mm3": HIT_MM3,
        "sampled_steps": samples,
        "screened_obstacles": len(nearby),
        "hits": {
            name: {**row, "max_volume_mm3": round(row["max_volume_mm3"], 6)}
            for name, row in sorted(hits.items())
        },
        "passes_sampled_nominal_path": not hits,
    }


def _fixed_screw_records(inventory: dict, panel_member: str) -> list[dict]:
    return [
        row
        for row in inventory["fixed_panel_kicker_screws"]
        if row["panel_member"] == panel_member
    ]


def _screw_screen(records, obstacles, own_panel: str) -> dict:
    results = {}
    for record in records:
        axis = _vec(record["axis_global_xyz"]).normalized()
        origin = _vec(record["origin_global_xyz_mm"])
        outside_start = origin - axis * TOOL_LENGTH_MM
        tool = cq.Solid.makeCylinder(
            TOOL_DIAMETER_MM / 2, TOOL_LENGTH_MM, outside_start, axis
        )
        # The complete shank travels one purchased under-head length outward.
        # Its modeled installed occupancy is retained from source inventory.
        occupied = record["source_occupied_length_mm"]
        purchased = record["shop_purchased_length_mm"]
        withdrawal = cq.Solid.makeCylinder(
            record["source_occupied_diameter_mm"] / 2,
            purchased + occupied,
            origin - axis * purchased,
            axis,
        )
        eligible = {
            name: shape for name, shape in obstacles.items() if name != own_panel
        }
        receiver_id = f"wood/{record['candidate_finished_receiver_member']}"
        intended_receiver = eligible.get(receiver_id)
        receiver_overlap_volume = (
            _volume(withdrawal, intended_receiver)
            if intended_receiver is not None
            else 0.0
        )
        tool_hits = {}
        withdrawal_hits = {}
        tool_box = tool.BoundingBox()
        withdrawal_box = withdrawal.BoundingBox()
        for name, shape in eligible.items():
            bounds = shape.BoundingBox()
            if _overlap(tool_box, bounds):
                volume = _volume(tool, shape, tool_box, bounds)
                if volume > HIT_MM3:
                    tool_hits[name] = round(volume, 6)
            # The receiver is expected to contain the screw's occupied axis.
            # Report that engagement separately; it is not a new obstacle to
            # withdrawing along the same threaded path. Keep every unrelated
            # body in the obstruction check.
            if name != receiver_id and _overlap(withdrawal_box, bounds):
                volume = _volume(withdrawal, shape, withdrawal_box, bounds)
                if volume > HIT_MM3:
                    withdrawal_hits[name] = round(volume, 6)
        results[record["axis_id"]] = {
            "panel_member": own_panel,
            "receiver_member": record["candidate_finished_receiver_member"],
            "fixed_axis_preserved": True,
            "purchased_length_mm": purchased,
            "source_occupied_length_mm": occupied,
            "intended_receiver_path": {
                "obstacle_id": receiver_id,
                "present": intended_receiver is not None,
                "source_occupied_length_mm": occupied,
                "shaft_receiver_intersection_volume_mm3": round(
                    receiver_overlap_volume, 6
                ),
                "intersection_volume_is_not_an_engagement_test": True,
                "excluded_from_withdrawal_obstruction_hits": intended_receiver
                is not None,
                "engagement_status": (
                    "not_assessed"
                    if intended_receiver is not None
                    else "blocked_missing_candidate_receiver"
                ),
            },
            "tool_envelope": {
                "diameter_mm": TOOL_DIAMETER_MM,
                "axial_length_mm": TOOL_LENGTH_MM,
                "hits": tool_hits,
                "passes_nominal_screen": not tool_hits,
            },
            "shank_withdrawal_sweep": {
                "diameter_mm": record["source_occupied_diameter_mm"],
                "axial_swept_length_mm": purchased + occupied,
                "hits": withdrawal_hits,
                "passes_nominal_screen": not withdrawal_hits,
            },
        }
    return results


def _moving_panel_assembly(
    panel_id: str,
    panel: cq.Shape,
    protected: dict,
    tnut_owners: dict[str, str],
) -> tuple[list[tuple[str, cq.Shape]], list[str], list[str]]:
    """Carry source-assigned T-nuts with panel; leave lights fixed.

    The source wiring model explicitly installs LED bodies after panels. An
    axis-aligned proximity box therefore cannot establish light ownership.
    T-nut datums name their host panel; volume intersection cannot determine
    ownership because the display flange may be exactly tangent to the panel.
    """
    tnut_shapes = protected["solids"]["tnuts"]
    if set(tnut_shapes) != set(tnut_owners):
        raise ValueError("Source T-nut host map does not match protected T-nut solids")
    attached = [
        (name, shape)
        for name, shape in sorted(tnut_shapes.items())
        if tnut_owners[name] == panel_id
    ]
    members = [("panel", panel)]
    members.extend((f"tnut/{name}", shape) for name, shape in attached)
    return members, [name for name, _ in attached], []


def _without_moving_panel_tnuts(obstacles, moving_tnut_ids):
    """Remove only T-nuts that travel with the currently removed panel(s)."""
    moving_tnut_keys = {f"tnut/{name}" for name in moving_tnut_ids}
    return {
        name: shape for name, shape in obstacles.items() if name not in moving_tnut_keys
    }


def _path_screen_group(members, obstacles, direction, distance, step) -> dict:
    rows = {
        member_id: _path_screen(shape, obstacles, direction, distance, step)
        for member_id, shape in members
    }
    hits = {
        f"{member_id} -> {obstacle}": record
        for member_id, result in rows.items()
        for obstacle, record in result["hits"].items()
    }
    first = next(iter(rows.values()))
    return {
        "distance_mm": distance,
        "step_mm": step,
        "sampled_steps": first["sampled_steps"],
        "sample_positions_mm": [
            round(i * step, 4) for i in range(1, first["sampled_steps"] + 1)
        ],
        "moving_member_count": len(members),
        "moving_members": [member_id for member_id, _ in members],
        "member_results": rows,
        "hits": hits,
        "passes_sampled_nominal_path": all(
            row["passes_sampled_nominal_path"] for row in rows.values()
        ),
    }


def _translated_members(members, offset: cq.Vector) -> list[tuple[str, cq.Shape]]:
    return [(member_id, shape.translate(offset)) for member_id, shape in members]


def _staged_obstacle_map(
    obstacles: dict[str, cq.Shape],
    panel_id: str,
    members: list[tuple[str, cq.Shape]],
    offset: cq.Vector,
) -> dict[str, cq.Shape]:
    """Retain a staged panel assembly and its attached T-nuts as obstacles."""
    staged_members = _translated_members(members, offset)
    staged_obstacles = {
        **obstacles,
        **{
            f"staged/{panel_id}/{member_id}": shape
            for member_id, shape in staged_members
        },
    }
    return staged_obstacles


def _closest_surface_distance(moving: cq.Shape, obstacles: dict[str, cq.Shape]) -> dict:
    """Return closest BRep separation among nearby envelopes at one pose."""
    moving_box = moving.BoundingBox()
    rows = []
    for name, obstacle in obstacles.items():
        box = obstacle.BoundingBox()
        dx = max(box.xmin - moving_box.xmax, moving_box.xmin - box.xmax, 0.0)
        dy = max(box.ymin - moving_box.ymax, moving_box.ymin - box.ymax, 0.0)
        dz = max(box.zmin - moving_box.zmax, moving_box.zmin - box.zmax, 0.0)
        if math.sqrt(dx * dx + dy * dy + dz * dz) > 25.0:
            continue
        rows.append((moving.distance(obstacle), name))
    if not rows:
        return {"distance_mm": None, "nearest_obstacle": None, "search_radius_mm": 25.0}
    distance, name = min(rows)
    return {
        "distance_mm": round(distance, 6),
        "nearest_obstacle": name,
        "search_radius_mm": 25.0,
    }


def _host_obstacles(
    source, nodes, protected, source_inventory, excluded=()
) -> dict[str, cq.Shape]:
    excluded = set(excluded)
    wood_names = {part.name for part in source.uncut_wood_parts()}
    obstacles = {
        f"wood/{part.name}": part.shape
        for part in source.parts()
        if part.name in wood_names and part.name not in excluded
    }
    # Use the actual WJ-03 through-bored host solids at the five changed hosts.
    for node in nodes.values():
        for name, part in node.source_host_parts.items():
            if name not in excluded:
                obstacles[f"wood/{name}"] = part.finished_shape
        for name, part in node.parts.items():
            obstacles[f"connector/{name}"] = part.finished_shape
        for bolt_id, stack in node.stacks.items():
            obstacles.update(
                {
                    f"wj03_hardware/{bolt_id}/{component}": shape
                    for component, shape in stack.installed_shapes().items()
                }
            )
    target_duties = {duty for values in LEGACY_DUTIES.values() for duty in values}
    for part in source.parts():
        if part.name in excluded or part.name in target_duties:
            continue
        if part.name.startswith("hold_tnut_"):
            continue
        if part.name.startswith("clip_"):
            obstacles[f"legacy_connector/{part.name}"] = part.shape
    panel_records = source_inventory["fixed_panel_kicker_screws"]
    for row in panel_records:
        if row["panel_member"] in excluded:
            continue
        obstacles[f"panel_screw/{row['axis_id']}"] = _axis_cylinder(
            row,
            row["shop_purchased_length_mm"],
            row["source_occupied_diameter_mm"],
        )
    for name, shape in protected["solids"]["frame_bolts"].items():
        obstacles[f"frame_bolt/{name}"] = shape
    for family in ("lights", "wires"):
        for name, shape in protected["solids"][family].items():
            obstacles[f"{family}/{name}"] = shape
    for name, shape in protected["solids"]["tnuts"].items():
        obstacles[f"tnut/{name}"] = shape
    retained_sds = {
        axis["axis_id"]: axis
        for duty in source_inventory["legacy_duties"]
        if duty["legacy_station_id"] not in target_duties
        for axis in duty["legacy_sds_axes"]
    }
    for name, row in retained_sds.items():
        obstacles[f"retained_sds/{name}"] = _axis_cylinder(
            row,
            row["source_occupied_length_mm"],
            row["source_occupied_diameter_mm"],
        )
    # Keep only the source-bounded legacy connector bodies not replaced here.
    for part in source.parts():
        if part.name.startswith("clip_") and part.name not in target_duties:
            obstacles[f"legacy_connector/{part.name}"] = part.shape
    # Avoid duplicate groups and retain a reproducible map.
    return obstacles


def _wj05_sequence_solids(candidate_wood, bolts, stacks) -> dict[str, cq.Shape]:
    """Return current WJ-05 permanent center geometry for WJ-03 path screens."""
    candidate_member_ids = sorted(
        member_id
        for member_id in candidate_wood
        if member_id.startswith(("base_post_center_", "inner_kicker_backer_"))
    )
    if len(candidate_member_ids) != 4:
        raise ValueError(
            "WJ-05 candidate must provide two shifted center posts and two finished backers"
        )
    solids = {
        f"wood/{member_id}": candidate_wood[member_id]
        for member_id in candidate_member_ids
    }
    solids.update({f"wj05_bolt/{bolt_id}": shape for bolt_id, shape in bolts.items()})
    solids.update(
        {
            f"wj05_hardware/{bolt_id}/{component}": shape
            for bolt_id, components in stacks.items()
            for component, shape in components.items()
        }
    )
    return solids


def _staged_reverse_route(lower: str, kicker: str) -> list[str]:
    """Describe conditional inverse order; path screens remain diagnostic."""
    return [
        "Restore and independently support the outer-node connectors before returning either panel; capture and retrieve all removed hardware.",
        f"With {lower} in its staged pose, return {kicker} opposite its +Y extraction direction; the sampled reverse path is not continuous-motion acceptance.",
        f"With {lower} still staged, refasten {kicker} at its unchanged 9 axes only after the four WJ-05 diagnostic backer receivers, real tool access, and service handling are verified.",
        f"Then return {lower} opposite its outward extraction direction (+N) and refasten it at its unchanged 12 axes only after its sampled reverse path, support, real tool access, and service handling are verified.",
    ]


def _panel_clearance_scenario(
    source, nodes, protected, inv, tnut_owners, wj05_solids, side: str
) -> dict:
    lower = f"main_lower_{side}"
    kicker = f"kicker_{side}"
    wood_names = {part.name for part in source.uncut_wood_parts()}
    source_parts = {
        part.name: part.shape for part in source.parts() if part.name in wood_names
    }
    wall_panel = source_parts[lower]
    kicker_panel = source_parts[kicker]
    protected_screws = _fixed_screw_records(inv, lower)
    kicker_screws = _fixed_screw_records(inv, kicker)

    # Screen each adjacent lower panel screw at its fixed source axis first.
    screw_obstacles = _host_obstacles(source, nodes, protected, inv, excluded=(lower,))
    screw_obstacles.update(wj05_solids)
    lower_screw_screen = _screw_screen(protected_screws, screw_obstacles, lower)
    kicker_obstacles = _host_obstacles(
        source, nodes, protected, inv, excluded=(kicker,)
    )
    kicker_obstacles.update(wj05_solids)
    kicker_screw_screen = _screw_screen(kicker_screws, kicker_obstacles, kicker)

    wall_members, wall_tnuts, wall_lights = _moving_panel_assembly(
        lower,
        wall_panel,
        protected,
        tnut_owners,
    )
    wall_obstacles = _host_obstacles(source, nodes, protected, inv, excluded=(lower,))
    wall_obstacles.update(wj05_solids)
    wall_obstacles = {
        name: shape
        for name, shape in wall_obstacles.items()
        if not (
            (name.startswith("tnut/") and name.split("/", 1)[1] in wall_tnuts)
            or (name.startswith("lights/") and name.split("/", 1)[1] in wall_lights)
        )
    }
    normal = cq.Vector(0, -math.sin(math.radians(50)), math.cos(math.radians(50)))
    outward = -normal
    lower_panel_path = _path_screen_group(
        wall_members, wall_obstacles, outward, 250.0, 25.0
    )

    # Kicker's head-side screws are removed before any rigid panel movement.
    # Test +Y with the adjacent lower panel retained, after only the screw axes
    # and service openings are applied from maintained state.
    retained_path_obstacles = _host_obstacles(
        source, nodes, protected, inv, excluded=(kicker,)
    )
    retained_path_obstacles.update(wj05_solids)
    kicker_members, kicker_tnuts, kicker_lights = _moving_panel_assembly(
        kicker,
        kicker_panel,
        protected,
        tnut_owners,
    )
    moving_kicker_ids = set(kicker_tnuts)
    moving_kicker_lights = set(kicker_lights)
    retained_path_obstacles = _without_moving_panel_tnuts(
        retained_path_obstacles,
        moving_kicker_ids,
    )
    retained_path_obstacles = {
        name: shape
        for name, shape in retained_path_obstacles.items()
        if not (
            name.startswith("lights/") and name.split("/", 1)[1] in moving_kicker_lights
        )
    }
    direct_kicker_path = _path_screen_group(
        kicker_members, retained_path_obstacles, cq.Vector(0, 1, 0), 100.0, 1.0
    )

    # Repeat after staging the one same-side adjacent lower panel away.
    open_wall_obstacles = _host_obstacles(
        source, nodes, protected, inv, excluded=(kicker, lower)
    )
    open_wall_obstacles.update(wj05_solids)
    open_wall_obstacles = _without_moving_panel_tnuts(
        open_wall_obstacles,
        set(moving_kicker_ids) | set(wall_tnuts),
    )
    open_wall_obstacles = {
        name: shape
        for name, shape in open_wall_obstacles.items()
        if name != f"wood/{lower}"
        and not (
            name.startswith("lights/") and name.split("/", 1)[1] in moving_kicker_lights
        )
    }
    # A staged panel remains a physical obstacle. Carry its source-assigned
    # T-nuts to the sampled staging pose instead of removing it from the scene.
    staged_wall_obstacles = _staged_obstacle_map(
        open_wall_obstacles,
        lower,
        wall_members,
        outward * 250.0,
    )
    after_lower_staged = _path_screen_group(
        kicker_members, staged_wall_obstacles, cq.Vector(0, 1, 0), 100.0, 1.0
    )
    staged_kicker_members = _translated_members(
        kicker_members,
        cq.Vector(0, 100.0, 0),
    )
    kicker_return_path = _path_screen_group(
        staged_kicker_members,
        staged_wall_obstacles,
        cq.Vector(0, -1, 0),
        100.0,
        1.0,
    )
    staged_lower_return_members = _translated_members(
        wall_members,
        outward * 250.0,
    )
    lower_return_path = _path_screen_group(
        staged_lower_return_members,
        wall_obstacles,
        normal,
        250.0,
        25.0,
    )

    return {
        "adjacent_panel": lower,
        "target_kicker": kicker,
        "fixed_screw_counts": {
            lower: len(protected_screws),
            kicker: len(kicker_screws),
        },
        "moving_tnut_source_ownership": {
            "basis": "hold_tnut_reinforcement.datums panel identity",
            lower: {"count": len(wall_tnuts), "ids": wall_tnuts},
            kicker: {"count": len(kicker_tnuts), "ids": kicker_tnuts},
        },
        "panel_transport_precondition": (
            "Remove and retain installed holds and hold bolts before panel screw removal. "
            "Motion maps start after that operation; hold-bolt withdrawal is not screened."
        ),
        "fixed_screws_and_tools": {
            lower: lower_screw_screen,
            kicker: kicker_screw_screen,
        },
        "adjacent_lower_panel_extraction": {
            "outward_direction_xyz": [round(v, 9) for v in outward.toTuple()],
            "translation_distance_mm": 250.0,
            "moving_panel_tnuts": wall_tnuts,
            "moving_panel_lights": wall_lights,
            "sampling_definition": "0 mm initial position excluded; then 10 equally spaced positions every 25 mm through 250 mm",
            "path": lower_panel_path,
            "panel_body_at_250_mm": _closest_surface_distance(
                wall_panel.translate(outward * 250.0), wall_obstacles
            ),
            "support_and_holding": "not modeled",
            "carry_and_rotation_after_translation": "not modeled",
            "staged_reverse_route": _staged_reverse_route(lower, kicker),
            "return_path_after_kicker_restored": lower_return_path,
        },
        "kicker_translation_after_screws_removed": {
            "direction_xyz": [0.0, 1.0, 0.0],
            "translation_distance_mm": 100.0,
            "with_adjacent_panel_retained": direct_kicker_path,
            "after_adjacent_panel_staged": after_lower_staged,
            "reverse_return_with_adjacent_panel_staged": kicker_return_path,
            "adjacent_panel_tnut_obstacle_state": {
                "with_adjacent_panel_retained": sorted(
                    name
                    for name in wall_tnuts
                    if f"tnut/{name}" in retained_path_obstacles
                ),
                "after_adjacent_panel_staged": sorted(
                    name
                    for name in wall_tnuts
                    if f"staged/{lower}/tnut/{name}" in staged_wall_obstacles
                ),
                "other_panel_tnuts_retained_after_staging": sorted(
                    name.split("/", 1)[1]
                    for name in open_wall_obstacles
                    if name.startswith("tnut/")
                ),
            },
            "kicker_body_at_25_mm_after_lower_staged": _closest_surface_distance(
                kicker_panel.translate(cq.Vector(0, 25.0, 0)), staged_wall_obstacles
            ),
        },
    }


def _short_nut_route(nodes, source, protected, inv, wj05_solids) -> dict:
    results = {}
    for node in nodes.values():
        for bolt_id, stack in node.stacks.items():
            if "bridge_link" not in bolt_id:
                continue
            direction = cq.Vector(stack.direction).normalized()
            tip_projection = (
                stack.hardware.under_head_length_mm
                - stack.grip_mm
                - stack.hardware.washer_thickness_mm
            )
            nut_travel = tip_projection - stack.hardware.washer_thickness_mm + 0.1
            washer_travel = tip_projection + 0.1
            nut_start = (
                stack.nut_seat.center + direction * stack.hardware.washer_thickness_mm
            )
            washer_start = stack.nut_seat.center
            nut_sweep = cq.Solid.makeCylinder(
                stack.hardware.nut_diameter_mm / 2,
                stack.hardware.nut_height_mm + nut_travel,
                nut_start,
                direction,
            )
            washer_outer = cq.Solid.makeCylinder(
                stack.hardware.washer_od_mm / 2,
                stack.hardware.washer_thickness_mm + washer_travel,
                washer_start,
                direction,
            )
            washer_inner = cq.Solid.makeCylinder(
                stack.hardware.washer_id_mm / 2,
                stack.hardware.washer_thickness_mm + washer_travel,
                washer_start,
                direction,
            )
            washer_sweep = washer_outer.cut(washer_inner)

            # Preserve all maintained geometry, excluding only this stack's
            # installed components to avoid treating simplified nut/shaft
            # thread overlap as a collision.
            obstacles = {
                f"wood/{part.name}": part.shape
                for part in source.parts()
                if part.name in {row.name for row in source.uncut_wood_parts()}
            }
            for side_node in nodes.values():
                obstacles.update(
                    {
                        f"connector/{name}": part.finished_shape
                        for name, part in side_node.parts.items()
                    }
                )
                obstacles.update(
                    {
                        f"wood/{name}": part.finished_shape
                        for name, part in side_node.source_host_parts.items()
                    }
                )
            obstacles.update(wj05_solids)
            for family in (
                "tnuts",
                "hold_hole_and_trial_projection",
                "lights",
                "wires",
                "frame_bolts",
            ):
                for name, shape in protected["solids"][family].items():
                    obstacles[f"protected/{family}/{name}"] = shape
            for other_id, other in node.stacks.items():
                if other_id == bolt_id:
                    continue
                obstacles.update(
                    {
                        f"hardware/{other_id}/{role}": shape
                        for role, shape in other.installed_shapes().items()
                    }
                )

            def hits(shape, _obstacles=obstacles):
                output = {}
                box = shape.BoundingBox()
                for name, obstacle in _obstacles.items():
                    obstacle_box = obstacle.BoundingBox()
                    if _overlap(box, obstacle_box):
                        volume = _volume(shape, obstacle, box, obstacle_box)
                        if volume > HIT_MM3:
                            output[name] = round(volume, 6)
                return output

            results[bolt_id] = {
                "direction_xyz": [round(v, 9) for v in direction.toTuple()],
                "provisional_tip_projection_mm": round(tip_projection, 6),
                "nut_clearance_travel_mm": round(nut_travel, 6),
                "washer_clearance_travel_mm": round(washer_travel, 6),
                "socket_access": {
                    role: {
                        "diameter_mm": TOOL_DIAMETER_MM,
                        "length_mm": TOOL_LENGTH_MM,
                        "hits_including_kicker": hits(shape),
                    }
                    for role, shape in access_shapes(stack).items()
                    if role == "nut"
                },
                "nut_minimum_disengagement_sweep_hits": hits(nut_sweep),
                "washer_minimum_disengagement_sweep_hits": hits(washer_sweep),
                "provisional_hardware_product_selected": False,
                "ratchet_handle_swing_screened": False,
                "capture_retention_screened": False,
            }
    return results


def build_report() -> dict:
    inv = json.loads(INPUT.read_text())
    (
        source,
        _wj05_source_wood,
        wj05_candidate_wood,
        _wj05_raw_backers,
        wj05_bolts,
        _wj05_bores,
        wj05_stacks,
        _wj05_tools,
        _wj05_counterbores,
    ) = build_wj05_center_candidate()
    nodes = build_outer_nodes()
    wj05_solids = _wj05_sequence_solids(
        wj05_candidate_wood,
        wj05_bolts,
        wj05_stacks,
    )
    protected = protected_inventory()
    tnut_owners = {row["name"]: row["panel"] for row in hold_tnuts.datums(source)}
    sides = {
        side: _panel_clearance_scenario(
            source,
            nodes,
            protected,
            inv,
            tnut_owners,
            wj05_solids,
            side,
        )
        for side in ("left", "right")
    }
    dependencies = tuple(
        sorted(
            {
                *SEQUENCE_DEPENDENCIES,
                *inv.get("source_runtime_module_hashes_sha256", {}),
            }
        )
    )
    return {
        "schema": "wood_joint_wj03_sequence_diagnostic/v1",
        "candidate": "compact-floor-flush-wood-joints-development",
        "status": "diagnostic_only_not_acceptance",
        "authority": {
            "retained_candidate": "compact-floor-flush-development",
            "width_option": "kerf-right",
            "fixed_panel_kicker_screws": 66,
            "frame_bolt_arrangements": 12,
            "axes_changed": False,
            "source_inventory_sha256": _sha(INPUT),
            "source_model_binding": nodes["left"].source_binding.inventory_sha256,
            "producer_sha256": _sha(Path(__file__).resolve()),
            "dependency_sha256": {name: _sha(ROOT / name) for name in dependencies},
        },
        "wj05_retained_geometry": {
            "candidate_id": "wj05-center-backer-header-through-bolt-diagnostic-v1",
            "members": sorted(
                name.removeprefix("wood/")
                for name in wj05_solids
                if name.startswith("wood/")
            ),
            "backer_header_bolts": sorted(wj05_bolts),
            "installed_stack_components": sorted(
                f"{bolt_id}/{component}"
                for bolt_id, components in wj05_stacks.items()
                for component in components
            ),
            "center_receiver_axes": sorted(
                row["axis_id"]
                for row in inv["fixed_panel_kicker_screws"]
                if row["candidate_finished_receiver_member"].startswith(
                    "inner_kicker_backer_"
                )
            ),
            "claim": "Candidate receivers and attachment envelopes included for nominal collision screening only; no backer-to-header capacity or center duty is accepted.",
        },
        "limitations": [
            "Nominal maintained CAD only; no delivered parts, fit/tolerance, operator, or field observation.",
            "The provisional bolt/nut dimensions are not a selected or procured product.",
            "Tool cylinder models coaxial access only; no real ratchet head, handle swing, or grip is modeled.",
            "Panel and connector support, weight, retention, hand positions, and human handling are not modeled.",
            "Straight paths are sampled; a collision-free sample screen is not continuous-motion or build acceptance.",
            "The provisional hold rear-projection solids are removable hold-bolt envelopes, not installed panel hardware; panel-motion maps start after holds and bolts are removed, and their withdrawal is not screened.",
            "Screw overlap with its named receiver is excluded from withdrawal obstruction hits; it is not a thread-engagement or receiver-capacity check.",
            "The four WJ-05 center-kicker receivers and their provisional backer/header attachment stacks are included as diagnostic geometry only; no receiver resistance or attachment capacity is established.",
            "Panel-carried T-nuts follow the maintained hold_tnut_reinforcement.datums panel identity; volume intersection is not used because flange-to-panel contact may be tangent. LED bodies and wiring stay fixed as separate services because source wiring installs lights after panels.",
            "Any panel/service collision requires an explicit service-disconnect and reinstallation operation; this diagnostic does not model one.",
        ],
        "nut_access_and_minimum_physical_extraction": _short_nut_route(
            nodes, source, protected, inv, wj05_solids
        ),
        "panel_and_kicker_sequences": sides,
        "recommended_diagnostic_sequence": [
            "Remove and retain installed holds and hold bolts; this sequence starts after that operation, whose withdrawal paths are not screened. Disconnect and label services that require handling; confirm panel-screw access, support, and retrieval before moving panels.",
            "Remove the same-side main-lower panel at its unchanged 12 axes, carrying its source-assigned T-nuts; move it along -N only if the sampled path and a supported staging position pass.",
            "With that lower panel physically staged, remove the kicker at its unchanged 9 axes, carrying its source-assigned T-nuts; the four center axes now have WJ-05 diagnostic backers, whose attachment and receiver resistance remain unaccepted.",
            "Move the kicker along +Y only if the sampled path includes the staged lower panel, WJ-05 backers and attachment stacks, WJ-03 node bodies and installed stacks, services, and support state and shows no blocker.",
            "Only after both panels clear, independently support the WJ-03 spine, bridge, and link; capture and remove node hardware through its screened paths. The short nut-disengagement sweep alone does not justify node-first disassembly.",
            "For return, restore and support node connections first; return and refasten kicker at 9 axes while lower panel stays staged, then return and refasten lower panel at 12 axes. Both reverse paths remain diagnostic until continuous motion, support, service handling, real tool access, and tolerances are resolved.",
        ],
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build_report(), indent=2, sort_keys=True) + "\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
