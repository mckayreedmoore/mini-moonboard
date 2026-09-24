"""Diagnostic assembly and access screens for the compact WJ-03 trial.

The frozen compact-outer producer remains the sole source of trial geometry.
This module materializes its third hypothesis and screens a bounded order of
panel, connector-body, and through-bolt motions. Results are not acceptance.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import cadquery as cq

from mini_moonboard import hold_tnut_reinforcement as hold_tnuts
from mini_moonboard.floor_flush_width import KERF_RIGHT
from mini_moonboard.wood_joint_frame import (
    LEGACY_DUTIES,
    SOURCE_HOST_IDS,
    TOOL_DIAMETER_MM,
    TOOL_LENGTH_MM,
    BoltStack,
    bolt_axis_stroke_shapes,
    detached_hardware_removal_shapes,
    installed_stack_shapes,
    validate_source_binding,
)
from mini_moonboard.wood_joint_geometry import FinishedPart
from mini_moonboard.wood_joint_panel_machining import (
    PANEL_CONNECTION_COUNT,
    PANEL_NAMES,
    RIGHT_PANEL_NAMES,
)
from scripts import wood_joint_wj03_compact_outer_probe as outer_probe
from scripts import wood_joint_wj03_sequence as sequence
from scripts.owner_layout_protected import (
    HOLD_HOLE_DIAMETER_MM,
    TRIAL_HOLD_REAR_PROJECTION_MM,
)
from scripts.wood_joint_clearance import _floor_plane_clearances
from scripts.wood_joints_wj05_center_backer_transfer_probe import (
    _source_and_candidate as build_wj05_center_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"
TRIAL_ID = "compact_bridge_rear_bevel_4x6_spine_137_7"
FLOOR_Z_MM = 0.0
FLOOR_DATUM = "global z=0; analytical plane only"
LOWER_PANEL_STROKE_MM = 250.0
KICKER_STROKE_MM = 100.0
BODY_CLEARANCE_MM = 5.0
BODY_SAMPLE_STEP_MM = 5.0
BOLT_HIT_TOLERANCE_MM3 = 1e-4

SOURCE_PIN_PATHS = (
    "docs/floor-flush-construction-kerf-right/connection-axes.csv",
    "docs/floor-flush-construction-kerf-right/stock-profiles.json",
    "docs/panel-insert-reference.json",
    "docs/wood-joints-mvp/source-inventory.json",
    "mini_moonboard/base_frame.py",
    "mini_moonboard/compact_floor_flush_frame.py",
    "mini_moonboard/floor_flush_width.py",
    "mini_moonboard/hold_tnut_reinforcement.py",
    "mini_moonboard/insert_frame.py",
    "mini_moonboard/model.py",
    "mini_moonboard/panel_grid.py",
    "mini_moonboard/panel_grid_v2.py",
    "mini_moonboard/round_service_wiring.py",
    "mini_moonboard/wood_joint_frame.py",
    "mini_moonboard/wood_joint_geometry.py",
    "mini_moonboard/wood_joint_panel_machining.py",
    "mini_moonboard/wood_joint_wj05_socket.py",
    "scripts/owner_layout_protected.py",
    "scripts/wood_joint_clearance.py",
    "scripts/wood_joint_wj03_compact_outer_access.py",
    "scripts/wood_joint_wj03_compact_outer_probe.py",
    "scripts/wood_joint_wj03_sequence.py",
    "scripts/wood_joints_wj05_center_backer_transfer_probe.py",
)


@dataclass(frozen=True)
class PanelShape:
    name: str
    shape: cq.Shape


@dataclass(frozen=True)
class SequenceHostObstacle:
    """Finished host shape adapter for sequence collision helpers only."""

    finished_shape: cq.Shape


@dataclass(frozen=True)
class CompactOuterGeometry:
    """One source-bound materialization shared by access and tool screens.

    `raw_source_wood` and `source_host_parts` retain source identity. Combined
    candidate obstacle geometry lives in `finished_wood`; `panels` is a
    six-entry view into that map. Maps are read-only to prevent baseline edits.
    """

    trial_id: str
    source: object
    source_binding: object
    raw_source_wood: Mapping[str, cq.Shape]
    source_current_parts: Mapping[str, cq.Shape]
    source_host_parts: Mapping[str, FinishedPart]
    host_wood: Mapping[str, cq.Shape]
    parts_by_side: Mapping[str, Mapping[str, FinishedPart]]
    stacks_by_side: Mapping[str, Mapping[str, BoltStack]]
    finished_wood: Mapping[str, cq.Shape]
    panels: Mapping[str, cq.Shape]
    panel_replacements: Mapping[str, PanelShape]
    protected: Mapping[str, object]
    wj05_raw_backers: Mapping[str, cq.Shape]
    wj05_candidate_wood: Mapping[str, cq.Shape]
    wj05_bolts: Mapping[str, cq.Shape]
    wj05_bores: Mapping[str, cq.Shape]
    wj05_stacks: Mapping[str, Mapping[str, cq.Shape]]
    wj05_tools: Mapping[str, Mapping[str, cq.Shape]]
    wj05_counterbores: Mapping[str, cq.Shape]
    installed_hardware: Mapping[str, cq.Shape]
    staged_panels: Mapping[str, cq.Shape]
    tnut_owners: Mapping[str, str]
    source_pins: Mapping[str, str]
    floor_z_mm: float = FLOOR_Z_MM
    floor_datum: str = FLOOR_DATUM

    @property
    def parts(self) -> Mapping[str, FinishedPart]:
        return MappingProxyType(
            {
                name: part
                for side_parts in self.parts_by_side.values()
                for name, part in side_parts.items()
            }
        )

    @property
    def stacks(self) -> Mapping[str, BoltStack]:
        return MappingProxyType(
            {
                name: stack
                for side_stacks in self.stacks_by_side.values()
                for name, stack in side_stacks.items()
            }
        )


def _sequence_host_adapter_map(
    geometry: CompactOuterGeometry, host_ids: set[str]
) -> dict[str, SequenceHostObstacle]:
    missing = host_ids - geometry.host_wood.keys()
    if missing:
        raise ValueError(f"Combined candidate hosts are missing: {sorted(missing)}")
    return {
        name: SequenceHostObstacle(geometry.host_wood[name])
        for name in sorted(host_ids)
    }


def _readonly_map(values):
    return MappingProxyType(dict(values))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_pins() -> dict[str, str]:
    return {name: _sha256(ROOT / name) for name in SOURCE_PIN_PATHS}


def _combined_header_shape(
    wj03_header: cq.Shape, wj05_bores: Mapping[str, cq.Shape]
) -> cq.Shape:
    """Add only WJ-05 bores to the WJ-03 finished host geometry."""
    combined = wj03_header
    for _bore_id, bore in sorted(wj05_bores.items()):
        combined = combined.cut(bore)
    return combined.clean()


def _frame_component_obstacles(protected: Mapping[str, object]) -> dict[str, cq.Shape]:
    """Keep installed frame heads, washers, and nuts in the retained map."""
    return {
        f"frame_bolt_component/{name}": shape
        for name, shape in protected["solids"]["frame_bolt_components"].items()
    }


def _source_protected_inventory(source) -> dict:
    """Build maintained protection shapes from the already-built source model."""
    inventory = json.loads(SOURCE_INVENTORY.read_text())
    parts = tuple(source.parts())
    tnut_solids = {
        part.name: part.shape for part in parts if part.name.startswith("hold_tnut_")
    }
    electrical = tuple(source.electrical_parts())
    lights = {part.name: part.shape for part in electrical if part.kind == "light"}
    wires = {part.name: part.shape for part in electrical if part.kind == "wire"}

    hold_paths = {}
    for datum in hold_tnuts.datums(source):
        rear = cq.Vector(*datum["rear_seating_xyz_mm"])
        into_panel = cq.Vector(*datum["barrel_into_panel_direction"]).normalized()
        hold_paths[datum["name"]] = cq.Solid.makeCylinder(
            HOLD_HOLE_DIAMETER_MM / 2,
            TRIAL_HOLD_REAR_PROJECTION_MM,
            rear,
            -into_panel,
        )

    connections = {row.name: row for row in source.panel_connections()}
    panel_records = {
        row["axis_id"]: row for row in inventory["fixed_panel_kicker_screws"]
    }
    if (
        set(connections) != set(panel_records)
        or len(connections) != PANEL_CONNECTION_COUNT
    ):
        raise ValueError("WJ-03 retained panel screw inventory changed")
    panel_screws = {}
    for axis_id, row in panel_records.items():
        connection = connections[axis_id]
        if connection.diameter != row["source_occupied_diameter_mm"]:
            raise ValueError(f"Panel screw diameter changed: {axis_id}")
        panel_screws[axis_id] = cq.Solid.makeCylinder(
            connection.diameter / 2,
            row["shop_purchased_length_mm"],
            connection.start,
            connection.direction.normalized(),
        )

    frame_components = {}
    frame_bolts = {}
    frame_tools = {}
    frame_withdrawal = {}
    for row in source.connections():
        if row.kind != "bolt":
            continue
        dimensions = source.bolt_dimensions(row)
        direction = row.direction.normalized()
        roles = ("shaft", "head_washer", "nut_washer", "head", "nut")
        components = row.components()
        if len(components) != len(roles):
            raise ValueError(f"Retained frame-bolt stack changed: {row.name}")
        frame_bolts[row.name] = cq.Solid.makeCylinder(
            row.diameter / 2,
            row.length,
            row.start,
            direction,
        )
        frame_components.update(
            {
                f"{row.name}/{role}": shape
                for role, shape in zip(roles, components, strict=True)
            }
        )
        frame_tools[f"{row.name}/head_tool"] = cq.Solid.makeCylinder(
            TOOL_DIAMETER_MM / 2,
            TOOL_LENGTH_MM,
            row.start - direction * TOOL_LENGTH_MM,
            direction,
        )
        nut_start = row.start + direction * (
            row.grip + dimensions["washer_thickness_mm"] + 2.0
        )
        frame_tools[f"{row.name}/nut_tool"] = cq.Solid.makeCylinder(
            TOOL_DIAMETER_MM / 2,
            TOOL_LENGTH_MM,
            nut_start,
            direction,
        )
        shaft_start = row.start - direction * row.length
        frame_withdrawal[f"{row.name}/shaft_withdrawal"] = cq.Solid.makeCylinder(
            row.diameter / 2,
            2 * row.length,
            shaft_start,
            direction,
        )
        frame_withdrawal[f"{row.name}/head_withdrawal"] = cq.Solid.makeCylinder(
            max(row.diameter, dimensions["washer_od_mm"]) / 2,
            row.length,
            shaft_start,
            direction,
        )

    target_duties = {duty for duties in LEGACY_DUTIES.values() for duty in duties}
    target_sds = {
        axis["axis_id"]
        for row in inventory["legacy_duties"]
        if row["legacy_station_id"] in target_duties
        for axis in row["legacy_sds_axes"]
    }
    panel_axes = set(connections)
    retained_sds = {
        row.name: cq.Solid.makeCylinder(
            row.diameter / 2,
            row.length,
            row.start,
            row.direction.normalized(),
        )
        for row in source.connections()
        if row.kind == "screw"
        and row.name not in panel_axes
        and row.name not in target_sds
    }
    retained_connectors = {
        part.name: part.shape
        for part in parts
        if part.name.startswith("clip_") and part.name not in target_duties
    }
    solids = {
        "tnuts": tnut_solids,
        "hold_hole_and_trial_projection": hold_paths,
        "lights": lights,
        "wires": wires,
        "panel_screws": panel_screws,
        "frame_bolts": frame_bolts,
        "frame_bolt_components": frame_components,
        "frame_bolt_tools": frame_tools,
        "frame_bolt_withdrawal": frame_withdrawal,
        "retained_legacy_sds": retained_sds,
        "retained_legacy_connectors": retained_connectors,
    }
    expected = {
        "tnuts": 142,
        "hold_hole_and_trial_projection": 142,
        "lights": 132,
        "wires": 131,
        "panel_screws": 66,
        "frame_bolts": 12,
        "frame_bolt_components": 60,
        "frame_bolt_tools": 24,
        "frame_bolt_withdrawal": 24,
        "retained_legacy_sds": 120,
        "retained_legacy_connectors": 20,
    }
    counts = {name: len(rows) for name, rows in solids.items()}
    if counts != expected:
        raise ValueError(f"WJ-03 source protection inventory changed: {counts}")
    return {
        "schema": "wood_joint_wj03_compact_outer_access_protected/v1",
        "counts": counts,
        "solids": solids,
        "limitations": [
            "Hold rear projections are provisional removable envelopes; their removal is not screened.",
            "Panel screws use retained purchased-length envelopes and source occupied diameters, not verified delivered geometry.",
            "Electrical shapes are maintained display geometry, not field wiring clearance.",
        ],
    }


def _panel_staging(panels, protected, tnut_owners):
    staged = {}
    normal = cq.Vector(0, -math.sin(math.radians(50)), math.cos(math.radians(50)))
    offsets = {
        **{
            f"main_lower_{side}": -normal * LOWER_PANEL_STROKE_MM
            for side in ("left", "right")
        },
        **{
            f"kicker_{side}": cq.Vector(0, KICKER_STROKE_MM, 0)
            for side in ("left", "right")
        },
    }
    for panel_id, offset in offsets.items():
        members, _tnuts, _lights = sequence._moving_panel_assembly(
            panel_id, panels[panel_id], protected, tnut_owners
        )
        for member_id, shape in sequence._translated_members(members, offset):
            staged[f"staged/{panel_id}/{member_id}"] = shape
    return staged


def materialize_geometry() -> CompactOuterGeometry:
    """Materialize the frozen third hypothesis from one WJ-05 source build."""
    (
        source,
        raw_source_wood,
        wj05_candidate_wood,
        wj05_raw_backers,
        wj05_bolts,
        wj05_bores,
        wj05_stacks,
        wj05_tools,
        wj05_counterbores,
    ) = build_wj05_center_candidate()
    if getattr(source, "option", None) != KERF_RIGHT:
        raise ValueError("Compact WJ-03 access requires the kerf-right source")
    binding = validate_source_binding(source)
    spec = next((row for row in outer_probe.HYPOTHESES if row.id == TRIAL_ID), None)
    if spec is None:
        raise ValueError(f"Frozen compact-outer hypothesis missing: {TRIAL_ID}")

    current_parts = tuple(source.parts())
    current = {part.name: part.shape for part in current_parts}
    raw_wood = dict(raw_source_wood)
    if not set(SOURCE_HOST_IDS) <= raw_wood.keys():
        raise ValueError("Maintained source host inventory changed")
    if not RIGHT_PANEL_NAMES <= wj05_candidate_wood.keys():
        raise ValueError("WJ-05 candidate lacks remachined kerf-right panels")
    if len(wj05_bores) != 4 or len(wj05_bolts) != 4 or len(wj05_stacks) != 4:
        raise ValueError("WJ-05 candidate must retain four backer/header bolt stations")

    panels = {name: current[name] for name in PANEL_NAMES}
    panel_replacements = {
        name: PanelShape(name, wj05_candidate_wood[name]) for name in RIGHT_PANEL_NAMES
    }
    panels.update({name: part.shape for name, part in panel_replacements.items()})
    if set(panels) != PANEL_NAMES:
        raise ValueError("Compact WJ-03 panel obstacle map must contain six panels")
    if len(source.panel_connections()) != PANEL_CONNECTION_COUNT:
        raise ValueError("Compact WJ-03 must retain all 66 panel screw axes")

    inventory = json.loads(SOURCE_INVENTORY.read_text())
    ids_by_side = {
        side: {
            "spine": f"knee_outer_{side}_spine",
            "bridge": f"knee_outer_{side}_rear_bridge",
            "under": f"knee_outer_{side}_under_header_link",
        }
        for side in outer_probe.SIDES
    }
    raw_by_side = {
        side: outer_probe._raw_parts(side, raw_wood, spec) for side in outer_probe.SIDES
    }
    stacks_by_side = {
        side: outer_probe._stacks(
            side,
            raw_wood,
            spec,
            ids_by_side[side],
            outer_probe._source_frame(inventory, f"base_side_{side}"),
        )
        for side in outer_probe.SIDES
    }
    all_stacks = {
        bolt_id: stack
        for side_stacks in stacks_by_side.values()
        for bolt_id, stack in side_stacks.items()
    }
    if len(all_stacks) != 20:
        raise ValueError(
            f"Compact WJ-03 must retain 20 trial bolt stacks, got {len(all_stacks)}"
        )
    host_parts = outer_probe._finished_source_hosts(
        raw_wood,
        {part_id: current[part_id] for part_id in SOURCE_HOST_IDS},
        source.connections(),
        all_stacks,
        binding,
    )
    parts_by_side = {
        side: outer_probe._finished_candidate_parts(
            side,
            raw_by_side[side],
            stacks_by_side[side],
            outer_probe._canonical_frame(raw_wood, side),
            spec,
            binding.inventory_sha256,
        )
        for side in outer_probe.SIDES
    }

    # Begin with the WJ-03 finished host: its replaced legacy SDS holes are
    # restored and all retained source openings remain. The full WJ-05 header
    # starts from uncut stock, so overlaying it would refill retained openings.
    # Add only the four WJ-05 incremental cutters to preserve both conditions.
    host_wood = {name: part.finished_shape for name, part in host_parts.items()}
    host_wood["base_header"] = _combined_header_shape(
        host_wood["base_header"], wj05_bores
    )
    finished_wood = {name: shape for name, shape in current.items() if name in raw_wood}
    finished_wood.update(panels)
    finished_wood.update(host_wood)
    for name in (
        "base_post_center_left",
        "base_post_center_right",
        "inner_kicker_backer_left",
        "inner_kicker_backer_right",
    ):
        if name in wj05_candidate_wood:
            finished_wood[name] = wj05_candidate_wood[name]
    for side_parts in parts_by_side.values():
        finished_wood.update(
            {name: part.finished_shape for name, part in side_parts.items()}
        )

    protected = _source_protected_inventory(source)
    tnut_owners = {row["name"]: row["panel"] for row in hold_tnuts.datums(source)}
    staged_panels = _panel_staging(panels, protected, tnut_owners)
    installed = {
        f"wj03/{bolt_id}/{component}": shape
        for bolt_id, stack in all_stacks.items()
        for component, shape in installed_stack_shapes(stack).items()
    }
    return CompactOuterGeometry(
        trial_id=TRIAL_ID,
        source=source,
        source_binding=binding,
        raw_source_wood=_readonly_map(raw_wood),
        source_current_parts=_readonly_map(current),
        source_host_parts=_readonly_map(host_parts),
        host_wood=_readonly_map(host_wood),
        parts_by_side=MappingProxyType(
            {side: _readonly_map(values) for side, values in parts_by_side.items()}
        ),
        stacks_by_side=MappingProxyType(
            {side: _readonly_map(values) for side, values in stacks_by_side.items()}
        ),
        finished_wood=_readonly_map(finished_wood),
        panels=_readonly_map(panels),
        panel_replacements=_readonly_map(panel_replacements),
        protected=_readonly_map(protected),
        wj05_raw_backers=_readonly_map(wj05_raw_backers),
        wj05_candidate_wood=_readonly_map(wj05_candidate_wood),
        wj05_bolts=_readonly_map(wj05_bolts),
        wj05_bores=_readonly_map(wj05_bores),
        wj05_stacks=MappingProxyType(
            {name: _readonly_map(rows) for name, rows in wj05_stacks.items()}
        ),
        wj05_tools=MappingProxyType(
            {name: _readonly_map(rows) for name, rows in wj05_tools.items()}
        ),
        wj05_counterbores=_readonly_map(wj05_counterbores),
        installed_hardware=_readonly_map(installed),
        staged_panels=_readonly_map(staged_panels),
        tnut_owners=_readonly_map(tnut_owners),
        source_pins=_readonly_map(_source_pins()),
    )


def _part_extent_along(shape: cq.Shape, direction: cq.Vector) -> float:
    direction = direction.normalized()
    box = shape.BoundingBox()
    points = [
        cq.Vector(x, y, z)
        for x in (box.xmin, box.xmax)
        for y in (box.ymin, box.ymax)
        for z in (box.zmin, box.zmax)
    ]
    projections = [point.dot(direction) for point in points]
    return max(projections) - min(projections)


def _motion_for_body(side: str, part_id: str, stacks: Mapping[str, object]):
    if part_id.endswith("_spine"):
        stack = stacks[f"knee_outer_{side}_post_1"]
        body_layer = next(layer for layer in stack.layers if layer.body_id == part_id)
        insert = cq.Vector(stack.direction).normalized()
        if stack.layers[0].body_id != body_layer.body_id:
            raise ValueError(f"Unexpected spine bolt penetration order: {part_id}")
        return insert, -insert, "spine enters head-side outer-frame receiver"
    if part_id.endswith("_under_header_link"):
        stack = stacks[f"knee_outer_{side}_header_1"]
        if stack.layers[-1].body_id != part_id:
            raise ValueError(f"Unexpected link bolt penetration order: {part_id}")
        remove = cq.Vector(stack.direction).normalized()
        return -remove, remove, "link lifts into the header from below"
    if part_id.endswith("_rear_bridge"):
        stack = stacks[f"knee_outer_{side}_bridge_spine_1"]
        if stack.layers[0].body_id != part_id:
            raise ValueError(f"Unexpected bridge bolt penetration order: {part_id}")
        insert = cq.Vector(stack.direction).normalized()
        return insert, -insert, "bridge enters its spine/link seats from the rear"
    raise ValueError(f"Unknown compact WJ-03 body: {part_id}")


def body_operation_plan(geometry: CompactOuterGeometry) -> list[dict]:
    """Return the bounded inverse assembly order and geometry-derived strokes."""
    plan = []
    for side in ("left", "right"):
        side_parts = geometry.parts_by_side[side]
        side_stacks = geometry.stacks_by_side[side]
        by_suffix = {
            "spine": f"knee_outer_{side}_spine",
            "under_header_link": f"knee_outer_{side}_under_header_link",
            "rear_bridge": f"knee_outer_{side}_rear_bridge",
        }
        # Assembly puts the two host-facing members in first; the rear bridge
        # closes the node. Removal reverses that dependency.
        for part_kind in ("rear_bridge", "under_header_link", "spine"):
            part_id = by_suffix[part_kind]
            part = side_parts[part_id]
            insert, remove, assumption = _motion_for_body(side, part_id, side_stacks)
            plan.append(
                {
                    "side": side,
                    "part_id": part_id,
                    "insert_direction_xyz": [round(v, 9) for v in insert.toTuple()],
                    "remove_direction_xyz": [round(v, 9) for v in remove.toTuple()],
                    "distance_mm": round(
                        _part_extent_along(part.finished_shape, remove)
                        + BODY_CLEARANCE_MM,
                        6,
                    ),
                    "sample_step_mm": BODY_SAMPLE_STEP_MM,
                    "orientation": "as-installed; translation only; no rotation",
                    "support_assumption": (
                        "Part is independently supported and held throughout the motion; "
                        "no fixture, hand position, or load transfer is modeled."
                    ),
                    "path_basis": assumption,
                }
            )
    return plan


def _box_overlap(a, b) -> bool:
    return not (
        a.xmax < b.xmin
        or b.xmax < a.xmin
        or a.ymax < b.ymin
        or b.ymax < a.ymin
        or a.zmax < b.zmin
        or b.zmax < a.zmin
    )


def _intersection_volume(first: cq.Shape, second: cq.Shape) -> float:
    a, b = first.BoundingBox(), second.BoundingBox()
    if not _box_overlap(a, b):
        return 0.0
    return first.intersect(second).Volume()


def _wj05_header_bore_screen(geometry: CompactOuterGeometry) -> dict[str, dict]:
    header = geometry.host_wood["base_header"]
    rows = {}
    for name, bore in sorted(geometry.wj05_bores.items()):
        overlap = _intersection_volume(header, bore)
        rows[name] = {
            "combined_header_intersection_volume_mm3": round(overlap, 9),
            "passes_bore_envelope_screen": overlap <= BOLT_HIT_TOLERANCE_MM3,
            "source_host_identity_retained": True,
            "screen_limit": "nominal volume intersection only; not fit or capacity",
        }
    return rows


def _obstacle_map_for_body_motion(
    geometry: CompactOuterGeometry,
    side: str,
    part_id: str,
    removed_before: set[str],
) -> dict[str, cq.Shape]:
    panel_ids = {"main_lower_left", "main_lower_right", "kicker_left", "kicker_right"}
    inventory = json.loads(SOURCE_INVENTORY.read_text())
    nodes = {
        node_side: SimpleNamespace(
            parts=geometry.parts_by_side[node_side],
            source_host_parts=_sequence_host_adapter_map(
                geometry,
                {
                    "base_header",
                    f"base_post_outer_{node_side}",
                    f"base_side_{node_side}",
                },
            ),
            stacks=geometry.stacks_by_side[node_side],
        )
        for node_side in ("left", "right")
    }
    obstacles = sequence._host_obstacles(
        geometry.source,
        nodes,
        geometry.protected,
        inventory,
        excluded=panel_ids,
        panel_replacements=geometry.panel_replacements,
    )
    obstacles.update(_frame_component_obstacles(geometry.protected))
    # Replace source center-post ghosts with the translated WJ-05 candidate.
    for name in ("base_post_center_left", "base_post_center_right"):
        obstacles.pop(f"wood/{name}", None)
    for name in panel_ids:
        obstacles.pop(f"wood/{name}", None)
    # Remove T-nuts carried by staged lower/kicker panels, then restore their
    # exact staged shape. LED and wire services intentionally remain fixed.
    staged_tnut_ids = {
        name.rsplit("/", 1)[1] for name in geometry.staged_panels if "/tnut/" in name
    }
    for name in staged_tnut_ids:
        obstacles.pop(f"tnut/{name}", None)
    obstacles.update(geometry.staged_panels)
    obstacles.update(
        {f"wj05_bolt/{name}": shape for name, shape in geometry.wj05_bolts.items()}
    )
    obstacles.update(
        {
            f"wj05_hardware/{bolt_id}/{component}": shape
            for bolt_id, components in geometry.wj05_stacks.items()
            for component, shape in components.items()
        }
    )
    # Add only WJ-05 shifted/added bodies and the combined header. Source
    # panels/hosts and WJ-03 connectors are already in the helper map.
    obstacles["wood/base_header"] = geometry.host_wood["base_header"]
    for name in (
        "base_post_center_left",
        "base_post_center_right",
        "inner_kicker_backer_left",
        "inner_kicker_backer_right",
    ):
        obstacles[f"wood/{name}"] = geometry.finished_wood[name]
    # A body is moved only after all of its own stacks have been removed.
    removed_stack_bodies = removed_before | {part_id}
    for stack_id, stack in geometry.stacks.items():
        stack_bodies = {layer.body_id for layer in stack.layers}
        if stack_bodies & removed_stack_bodies:
            for key in tuple(obstacles):
                if key.startswith(f"wj03_hardware/{stack_id}/"):
                    obstacles.pop(key)
    # Previously removed/current bodies are no longer in the work envelope.
    for removed in removed_before | {part_id}:
        obstacles.pop(f"connector/{removed}", None)
    return obstacles


def _body_path_screens(
    geometry: CompactOuterGeometry,
) -> tuple[list[dict], list[cq.Shape]]:
    rows = []
    swept_samples = []
    removed_parts = set()
    for operation in body_operation_plan(geometry):
        side = operation["side"]
        part_id = operation["part_id"]
        part = geometry.parts[part_id]
        _insert, remove, _assumption = _motion_for_body(
            side, part_id, geometry.stacks_by_side[side]
        )
        obstacles = _obstacle_map_for_body_motion(
            geometry, side, part_id, removed_parts
        )
        path = sequence._path_screen(
            part.finished_shape,
            obstacles,
            remove,
            operation["distance_mm"],
            operation["sample_step_mm"],
        )
        count = max(
            1, math.ceil(operation["distance_mm"] / operation["sample_step_mm"])
        )
        swept_samples.extend(
            part.finished_shape.translate(
                remove
                * min(operation["distance_mm"], index * operation["sample_step_mm"])
            )
            for index in range(count + 1)
        )
        rows.append(
            {
                **operation,
                "sequence": "remove rear bridge, then under-header link, then spine; "
                "assembly path is the inverse order",
                "removed_outer_parts_before_motion": sorted(removed_parts),
                "path": path,
                "passes_sampled_nominal_path": path["passes_sampled_nominal_path"],
            }
        )
        removed_parts.add(part_id)
    return rows, swept_samples


def _bolt_motion_screens(
    geometry: CompactOuterGeometry,
) -> tuple[list[dict], list[cq.Shape], list[cq.Shape]]:
    rows = []
    stroke_shapes = []
    detached_shapes = []
    inventory = json.loads(SOURCE_INVENTORY.read_text())
    removed_panel_ids = {
        "main_lower_left",
        "main_lower_right",
        "kicker_left",
        "kicker_right",
    }
    removed_panel_screw_ids = {
        row["axis_id"]
        for row in inventory["fixed_panel_kicker_screws"]
        if row["panel_member"] in removed_panel_ids
    }
    for bolt_id, stack in sorted(geometry.stacks.items()):
        own_installed = stack.installed_shapes()
        obstacles = {
            f"wood/{name}": shape
            for name, shape in geometry.finished_wood.items()
            if name not in removed_panel_ids
        }
        for family in (
            "tnuts",
            "lights",
            "wires",
            "frame_bolt_components",
            "retained_legacy_sds",
            "retained_legacy_connectors",
        ):
            obstacles.update(
                {
                    f"protected/{family}/{name}": shape
                    for name, shape in geometry.protected["solids"][family].items()
                }
            )
        obstacles.update(
            {
                f"protected/panel_screws/{name}": shape
                for name, shape in geometry.protected["solids"]["panel_screws"].items()
                if name not in removed_panel_screw_ids
            }
        )
        obstacles.update(
            {f"wj05_bolt/{name}": shape for name, shape in geometry.wj05_bolts.items()}
        )
        obstacles.update(
            {
                f"wj05_hardware/{other_id}/{component}": shape
                for other_id, components in geometry.wj05_stacks.items()
                for component, shape in components.items()
            }
        )
        obstacles.update(
            {
                name: shape
                for name, shape in geometry.installed_hardware.items()
                if not name.startswith(f"wj03/{bolt_id}/")
            }
        )
        # Removed holds and lower/kicker screws are absent during node-bolt
        # work; retained upper-panel screws and service geometry stay fixed.
        for name in geometry.tnut_owners:
            if geometry.tnut_owners[name] in {
                "main_lower_left",
                "main_lower_right",
                "kicker_left",
                "kicker_right",
            }:
                obstacles.pop(f"protected/tnuts/{name}", None)
        obstacles.update(geometry.staged_panels)

        strokes = bolt_axis_stroke_shapes(stack)
        row = {
            "bolt_id": bolt_id,
            "stack_origin_xyz_mm": [
                round(v, 9) for v in stack.under_head_origin.toTuple()
            ],
            "axis_direction_xyz": [round(v, 9) for v in stack.direction],
            "intended_wood_layers": [layer.body_id for layer in stack.layers],
            "own_installed_components_excluded": sorted(
                f"wj03/{bolt_id}/{name}" for name in own_installed
            ),
            "intended_bored_wood_layers_retained_as_obstacles": [
                layer.body_id for layer in stack.layers
            ],
            "obstacle_count": len(obstacles),
            "strokes": {},
        }
        for stroke_name, stroke in strokes.items():
            hits = {}
            stroke_box = stroke.BoundingBox()
            for obstacle_name, obstacle in obstacles.items():
                if not _box_overlap(stroke_box, obstacle.BoundingBox()):
                    continue
                volume = _intersection_volume(stroke, obstacle)
                if volume > BOLT_HIT_TOLERANCE_MM3:
                    hits[obstacle_name] = round(volume, 6)
            row["strokes"][stroke_name] = {
                "hits": dict(sorted(hits.items())),
                "passes_axial_envelope_screen": not hits,
                "screen_type": "full straight shaft/head axis swept envelope; no tool motion",
            }
            stroke_shapes.append(stroke)
        detached = detached_hardware_removal_shapes(stack)
        row["detached_hardware_floor_envelopes"] = {
            name: round(shape.BoundingBox().zmin, 6) for name, shape in detached.items()
        }
        detached_shapes.extend(detached.values())
        rows.append(row)
    return rows, stroke_shapes, detached_shapes


def build_access_report(geometry: CompactOuterGeometry | None = None) -> dict:
    """Build the bounded panel/body/bolt movement report; does not write files."""
    geometry = materialize_geometry() if geometry is None else geometry
    if geometry.trial_id != TRIAL_ID:
        raise ValueError("Compact-outer access report received another hypothesis")
    inventory = json.loads(SOURCE_INVENTORY.read_text())
    nodes = {
        side: SimpleNamespace(
            parts=geometry.parts_by_side[side],
            source_host_parts=_sequence_host_adapter_map(
                geometry,
                {
                    "base_header",
                    f"base_post_outer_{side}",
                    f"base_side_{side}",
                },
            ),
            stacks=geometry.stacks_by_side[side],
            source_binding=geometry.source_binding,
        )
        for side in ("left", "right")
    }
    candidate_obstacles = sequence._wj05_sequence_solids(
        geometry.wj05_candidate_wood,
        geometry.wj05_bolts,
        geometry.wj05_stacks,
    )
    candidate_obstacles.update(_frame_component_obstacles(geometry.protected))
    # Keep the combined header cut geometry as one host obstacle.
    candidate_obstacles["wood/base_header"] = geometry.host_wood["base_header"]
    panels = {
        side: sequence._panel_clearance_scenario(
            geometry.source,
            nodes,
            geometry.protected,
            inventory,
            geometry.tnut_owners,
            candidate_obstacles,
            side,
            geometry.panel_replacements,
        )
        for side in ("left", "right")
    }
    for report in panels.values():
        report["removed_holds_assumption"] = (
            "Panel paths start with holds and hold bolts absent. Their removal, "
            "support, capture, and reinstallation are unverified and not screened."
        )
        report["panel_transport_precondition"] = (
            "Required but unverified assumption: holds and hold bolts have already "
            "been removed and retained. This report does not establish that procedure."
        )
    body_rows, body_path_samples = _body_path_screens(geometry)
    bolt_rows, bolt_stroke_shapes, detached_shapes = _bolt_motion_screens(geometry)
    outer_parts = [part.finished_shape for part in geometry.parts.values()]
    wj05_installed_shapes = [
        *geometry.wj05_bolts.values(),
        *(
            shape
            for components in geometry.wj05_stacks.values()
            for shape in components.values()
        ),
    ]
    installed_shapes = [*geometry.installed_hardware.values(), *wj05_installed_shapes]
    wj05_tool_shapes = [
        shape
        for station_tools in geometry.wj05_tools.values()
        for shape in station_tools.values()
    ]
    frame_bolts = list(geometry.protected["solids"]["frame_bolt_components"].values())
    floor = _floor_plane_clearances(
        outer_parts,
        installed_shapes,
        wj05_tool_shapes,
        bolt_stroke_shapes,
        detached_shapes,
        {"retained_frame_bolt_installed_components": frame_bolts},
    )
    floor.update(
        {
            "body_insertion_and_removal_paths": round(
                min(shape.BoundingBox().zmin for shape in body_path_samples), 6
            ),
            "panel_staged_pose_min_z": round(
                min(
                    shape.BoundingBox().zmin
                    for shape in geometry.staged_panels.values()
                ),
                6,
            ),
            "analytical_plane_z_mm": geometry.floor_z_mm,
            "body_path_clearance_above_plane_mm": round(
                min(shape.BoundingBox().zmin for shape in body_path_samples)
                - geometry.floor_z_mm,
                6,
            ),
            "staged_panel_clearance_above_plane_mm": round(
                min(
                    shape.BoundingBox().zmin
                    for shape in geometry.staged_panels.values()
                )
                - geometry.floor_z_mm,
                6,
            ),
            "tool_family_scope": "WJ-05 diagnostic tool envelopes only; WJ-03 tool screen is separately owned",
        }
    )
    return {
        "schema": "wood_joint_wj03_compact_outer_access_diagnostic/v1",
        "candidate": "compact-floor-flush-wood-joints-development",
        "trial_id": geometry.trial_id,
        "status": "diagnostic_only_not_acceptance",
        "source_binding": {
            "source_option": "kerf-right",
            "source_inventory_sha256": geometry.source_binding.inventory_sha256,
            "direct_source_pins_sha256": dict(geometry.source_pins),
            "transitive_source_pins": "partial; see direct source pin list",
            "panel_screw_axis_count": len(geometry.source.panel_connections()),
            "candidate_outer_part_ids": sorted(geometry.parts),
            "candidate_outer_stack_ids": sorted(geometry.stacks),
        },
        "geometry_state": {
            "finished_wood_count": len(geometry.finished_wood),
            "panel_ids": sorted(geometry.panels),
            "staged_panel_assembly_ids": sorted(geometry.staged_panels),
            "host_ids": sorted(geometry.host_wood),
            "combined_header": {
                "source_host_geometry_retained_separately": True,
                "raw_source_header_retained_separately": True,
                "wj03_finished_header_shape_id": "source_host_parts/base_header",
                "wj05_finished_header_shape_id": "wj05_candidate_wood/base_header",
                "combined_finished_header_shape_id": "host_wood/base_header",
                "construction": "WJ-03 finished host plus only the WJ-05 incremental bore cutters; the full WJ-05 header is retained as provenance but not overlaid because it starts from uncut stock and would refill retained source openings",
            },
            "wj05_receiver_ids": sorted(
                name
                for name in geometry.wj05_candidate_wood
                if name.startswith("inner_kicker_backer_")
            ),
            "wj05_bolt_ids": sorted(geometry.wj05_bolts),
            "wj05_header_bores": _wj05_header_bore_screen(geometry),
        },
        "assumptions_and_limits": [
            "All four main-lower and kicker panels are screened through the existing straight translation order; no holds or hold bolts are present during these maps, and their removal/capture path is not screened.",
            "Panel T-nuts follow source panel ownership to the staged pose. LEDs and wires remain fixed because the maintained source installs lights after panels.",
            "Panel and connector paths are sampled straight translations with as-installed orientation; continuous motion, rotation, hand positions, support, temporary capture, mass, and tolerances are not modeled.",
            "The panel route stages lower panels 250 mm outward and kickers 100 mm in +Y, matching the existing WJ-03 route order.",
            "Outer body removal is bridge, under-header link, then spine; assembly is the inverse. Each body path ends one body extent plus 5 mm beyond its seat, not a complete carry-to-floor route.",
            "Outer node fastener motions screen shaft/head axial envelopes only. Tool fit, wrenching, nut/washer handling, thread transition, delivered hardware, and fit are outside this report.",
            "Global z=0 is an analytical floor plane only; this is not a verified floor or a complete staged-component handling route.",
            "WJ-05 backer receiver and header bore shapes are collision geometry only; no receiver or backer capacity is accepted.",
        ],
        "panel_and_kicker_sequences": panels,
        "outer_body_paths": body_rows,
        "outer_bolt_axis_paths": bolt_rows,
        "floor_minimum_z_mm": floor,
        "assembly_sequence": [
            "Assume required holds and hold bolts have already been removed; their operation remains unverified.",
            "Remove and stage same-side lower main panel, then remove and stage its kicker; repeat on the other side before exposing node bodies.",
            "Insert spine toward the outer frame, then under-header link upward into the header, then rear bridge forward into its spine/link seats; screen the reverse withdrawal paths with retained parts present.",
            "Insert the 20 provisional ordinary bolts only after all six bodies are seated. Shaft/head strokes are separate from tool and nut-removal checks.",
        ],
    }
