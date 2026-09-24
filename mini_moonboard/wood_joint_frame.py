"""WJ-03 outer-node geometry for wood-joint development.

This is nominal layout geometry.  It does not establish wood or bolt strength,
procurement suitability, drilling dimensions, or a fabrication release.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from mini_moonboard.wood_joint_geometry import (
    BoltHardware,
    BoltStack,
    CutRecord,
    FinishedPart,
    InterfaceRecord,
    LocalFrame,
    StackLayer,
    WasherSeat,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"
CANDIDATE = "compact-floor-flush-wood-joints-development"

SIDES = ("left", "right")
LEGACY_DUTIES = {
    side: (
        f"clip_timber_header_outer_{side}",
        f"clip_angle_base_{side}",
    )
    for side in SIDES
}

BOLT_DIAMETER_MM = 6.35
DRILL_DIAMETER_MM = 7.5
WASHER_OD_MM = 18.6436
WASHER_ID_MM = 8.0
TOOL_DIAMETER_MM = 25.4
TOOL_LENGTH_MM = 50.0
REQUIRED_TIP_PROJECTION_MM = 2.54

SPINE_SECTION_MM = 88.9
SPINE_LENGTH_MM = 269.95
BRIDGE_LENGTH_MM = 383.2
LINK_LENGTH_MM = 185.2
LINK_POST_GAP_MM = 71.0
SPINE_Z0_MM = 146.05
LINK_Z0_MM = 150.0
REAR_FACE_Y_MM = -182.05
SPINE_FRONT_Y_MM = -93.15
BRIDGE_REAR_Y_MM = -270.95
ORDINARY_REAR_ENVELOPE_MM = 139.7
SOURCE_HOST_IDS = (
    "base_header",
    "base_post_outer_left",
    "base_post_outer_right",
    "base_side_left",
    "base_side_right",
)
LEGACY_DUTY_HOSTS = {
    "clip_timber_header_outer_left": ("base_header", "base_post_outer_left"),
    "clip_timber_header_outer_right": ("base_header", "base_post_outer_right"),
    "clip_angle_base_left": ("base_header", "base_side_left"),
    "clip_angle_base_right": ("base_header", "base_side_right"),
}


@dataclass(frozen=True)
class SourceBinding:
    inventory_sha256: str
    runtime_module_sha256: dict[str, str]
    uncut_part_shapes_sha256: str
    uncut_host_shape_sha256: dict[str, str]
    duty_host_mapping: dict[str, tuple[str, str]]
    fixed_screw_axes_sha256: str
    frame_bolt_axes_sha256: str


@dataclass(frozen=True)
class OuterNode:
    side: str
    owner_id: str
    duties: tuple[str, str]
    source_hosts: tuple[str, str, str]
    parts: dict[str, FinishedPart]
    source_host_parts: dict[str, FinishedPart]
    stacks: dict[str, BoltStack]
    interfaces: tuple[InterfaceRecord, ...]
    contact_areas_mm2: dict[str, float]
    source_binding: SourceBinding

    @property
    def rear_projection_from_header_front_mm(self) -> float:
        return -36.0 - BRIDGE_REAR_Y_MM

    @property
    def rear_envelope_exception_mm(self) -> float:
        return self.rear_projection_from_header_front_mm - ORDINARY_REAR_ENVELOPE_MM


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _point(value: cq.Vector) -> tuple[float, float, float]:
    return tuple(float(component) for component in value.toTuple())


def _unit(value: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(component * component for component in value))
    return tuple(component / length for component in value)


def _planar_faces(shape: cq.Shape) -> list[dict[str, object]]:
    angle = math.radians(50.0)
    basis = (
        (1.0, 0.0, 0.0),
        (0.0, math.cos(angle), math.sin(angle)),
        (0.0, -math.sin(angle), math.cos(angle)),
    )
    records = []
    for face in shape.Faces():
        if face.geomType() != "PLANE":
            continue
        vertices = [_point(vertex.Center()) for vertex in face.Vertices()]
        normal = _unit(_point(face.normalAt()))
        records.append(
            {
                "area_mm2": face.Area(),
                "center_global_xyz_mm": _point(face.Center()),
                "normal_global_xyz": normal,
                "spans_local_mm": {
                    name: max(
                        sum(a * b for a, b in zip(vertex, axis, strict=True))
                        for vertex in vertices
                    )
                    - min(
                        sum(a * b for a, b in zip(vertex, axis, strict=True))
                        for vertex in vertices
                    )
                    for name, axis in zip(("X", "T", "N"), basis, strict=True)
                },
            }
        )
    records.sort(
        key=lambda row: (
            tuple(round(value, 8) for value in row["center_global_xyz_mm"]),
            tuple(round(value, 8) for value in row["normal_global_xyz"]),
            round(row["area_mm2"], 8),
        )
    )
    return [
        {"face_id": f"planar_face_{index:02d}", **record}
        for index, record in enumerate(records, 1)
    ]


def _source_shape_fingerprint(shape: cq.Shape) -> str:
    return _canonical_sha256(
        {
            "volume_mm3": round(shape.Volume(), 7),
            "vertices_mm": sorted(
                tuple(round(value, 7) for value in _point(vertex.Center()))
                for vertex in shape.Vertices()
            ),
            "planar_faces": _planar_faces(shape),
        }
    )


def validate_source_binding(source=None) -> SourceBinding:
    """Fail if live source modules, solids, or the four owned duties drift."""
    inventory = json.loads(SOURCE_INVENTORY.read_text())
    source = variant(KERF_RIGHT) if source is None else source
    recorded_modules = inventory["source_runtime_module_hashes_sha256"]
    live_modules = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in recorded_modules
    }
    if live_modules != recorded_modules:
        raise ValueError(
            "WJ-03 source runtime modules drifted from source-inventory.json"
        )

    shapes = {part.name: part.shape for part in source.uncut_wood_parts()}
    live_shape_hashes = {
        name: _source_shape_fingerprint(shape) for name, shape in shapes.items()
    }
    aggregate = _canonical_sha256(live_shape_hashes)
    if aggregate != inventory["source_part_shapes_sha256"]:
        raise ValueError(
            "WJ-03 live uncut source-part shapes drifted from source-inventory.json"
        )
    recorded_parts = {row["part_id"]: row for row in inventory["parts"]}
    host_hashes = {name: live_shape_hashes[name] for name in SOURCE_HOST_IDS}
    if any(
        digest != recorded_parts[name]["source_shape_sha256"]
        for name, digest in host_hashes.items()
    ):
        raise ValueError(
            "WJ-03 uncut source-host shapes drifted from source-inventory.json"
        )

    inventory_duties = {
        row["legacy_station_id"]: tuple(row["legacy_host_members"])
        for row in inventory["legacy_duties"]
        if row["legacy_station_id"] in LEGACY_DUTY_HOSTS
    }
    if inventory_duties != LEGACY_DUTY_HOSTS:
        raise ValueError("WJ-03 duty-host mapping drifted from source-inventory.json")

    def axis_record(row) -> dict:
        record = {
            "axis_id": row.name,
            "members": list(row.members),
            "origin_global_xyz_mm": [round(value, 9) for value in row.start.toTuple()],
            "axis_global_xyz": [
                round(value, 12) for value in row.direction.normalized().toTuple()
            ],
            "source_occupied_length_mm": round(row.length, 9),
            "source_occupied_diameter_mm": round(row.diameter, 9),
        }
        if row.kind == "bolt":
            record["source_grip_mm"] = round(row.grip, 9)
        return record

    def inventory_axis(row) -> dict:
        record = {
            "axis_id": row["axis_id"],
            "members": row["members"],
            "origin_global_xyz_mm": [
                round(value, 9) for value in row["origin_global_xyz_mm"]
            ],
            "axis_global_xyz": [round(value, 12) for value in row["axis_global_xyz"]],
            "source_occupied_length_mm": round(row["source_occupied_length_mm"], 9),
            "source_occupied_diameter_mm": round(row["source_occupied_diameter_mm"], 9),
        }
        if "source_grip_mm" in row:
            record["source_grip_mm"] = round(row["source_grip_mm"], 9)
        return record

    fixed_live = sorted(
        (axis_record(row) for row in source.panel_connections()),
        key=lambda row: row["axis_id"],
    )
    fixed_recorded = sorted(
        (inventory_axis(row) for row in inventory["fixed_panel_kicker_screws"]),
        key=lambda row: row["axis_id"],
    )
    frame_live = sorted(
        (axis_record(row) for row in source.connections() if row.kind == "bolt"),
        key=lambda row: row["axis_id"],
    )
    frame_recorded = sorted(
        (inventory_axis(row) for row in inventory["starting_frame_bolts"]),
        key=lambda row: row["axis_id"],
    )
    if _canonical_sha256(fixed_live) != _canonical_sha256(fixed_recorded):
        raise ValueError("WJ-03 fixed panel/kicker axes drifted from source inventory")
    if _canonical_sha256(frame_live) != _canonical_sha256(frame_recorded):
        raise ValueError("WJ-03 retained frame-bolt axes drifted from source inventory")
    return SourceBinding(
        inventory_sha256=hashlib.sha256(SOURCE_INVENTORY.read_bytes()).hexdigest(),
        runtime_module_sha256=live_modules,
        uncut_part_shapes_sha256=aggregate,
        uncut_host_shape_sha256=host_hashes,
        duty_host_mapping=inventory_duties,
        fixed_screw_axes_sha256=_canonical_sha256(fixed_recorded),
        frame_bolt_axes_sha256=_canonical_sha256(frame_recorded),
    )


def _contact_geometry(
    first: cq.Shape,
    second: cq.Shape,
    normal: tuple[float, float, float],
) -> tuple[float, LocalFrame]:
    """Derive a contact frame from the actual net solids using a thin probe."""
    depth = 0.1
    n = cq.Vector(*normal).normalized()
    patch = first.translate(n * depth).intersect(second)
    if patch.Volume() <= 0:
        raise ValueError("WJ-03 expected finished-solid contact is absent")
    origin = patch.Center() - n * (depth / 2)
    preferred_x = cq.Vector(1, 0, 0)
    if abs(preferred_x.dot(n)) > 0.9:
        preferred_x = cq.Vector(0, 0, 1)
    tangent_x = (preferred_x - n * preferred_x.dot(n)).normalized()
    tangent_t = n.cross(tangent_x).normalized()
    return patch.Volume() / depth, LocalFrame(origin, tangent_x, tangent_t, n)


def _hardware(length_mm: float, grip_mm: float) -> BoltHardware:
    return BoltHardware(
        candidate_sku=(
            f"provisional ordinary 1/4-20 x {length_mm / 25.4:g}-in through-bolt; "
            "grade, thread length, washer product, and supplier unselected"
        ),
        under_head_length_mm=length_mm,
        steel_diameter_mm=BOLT_DIAMETER_MM,
        cad_occupied_diameter_mm=BOLT_DIAMETER_MM,
        drill_diameter_mm=DRILL_DIAMETER_MM,
        head_diameter_mm=12.827,
        head_height_mm=4.1656,
        washer_od_mm=WASHER_OD_MM,
        washer_id_mm=WASHER_ID_MM,
        washer_thickness_mm=1.651,
        nut_diameter_mm=12.827,
        nut_height_mm=5.7404,
        # Layout-only provisional thread envelope. Procurement must replace it.
        usable_thread_start_mm=grip_mm + 2.0,
        usable_thread_end_mm=length_mm,
    )


def _stack(
    bolt_id: str,
    origin: tuple[float, float, float],
    direction: tuple[float, float, float],
    layers: tuple[tuple[str, float], ...],
    length_mm: float,
) -> BoltStack:
    unit = cq.Vector(*direction).normalized()
    grip = sum(thickness for _, thickness in layers)
    wood_origin = cq.Vector(*origin)
    hardware = _hardware(length_mm, grip)
    under_head = wood_origin - unit * hardware.washer_thickness_mm
    far = wood_origin + unit * grip
    return BoltStack(
        id=bolt_id,
        hardware=hardware,
        under_head_origin=under_head,
        direction=direction,
        layers=tuple(StackLayer(body_id, thickness) for body_id, thickness in layers),
        head_seat=WasherSeat(layers[0][0], wood_origin, direction),
        nut_seat=WasherSeat(layers[-1][0], far, tuple(-v for v in direction)),
        required_tip_projection_mm=REQUIRED_TIP_PROJECTION_MM,
    )


def installed_stack_shapes(stack: BoltStack) -> dict[str, cq.Shape]:
    """Return full installed bolt envelopes with washers outside wood faces."""
    return dict(stack.installed_shapes())


def access_shapes(stack: BoltStack) -> dict[str, cq.Shape]:
    """Return nominal 50 mm socket/tool approaches at both stack ends."""
    origin = stack.head_seat.center
    direction = cq.Vector(stack.direction).normalized()
    far = stack.nut_seat.center
    return {
        "head": cq.Solid.makeCylinder(
            TOOL_DIAMETER_MM / 2,
            TOOL_LENGTH_MM,
            origin - direction * TOOL_LENGTH_MM,
            direction,
        ),
        "nut": cq.Solid.makeCylinder(
            TOOL_DIAMETER_MM / 2,
            TOOL_LENGTH_MM,
            far + direction * 2.0,
            direction,
        ),
    }


def bolt_axis_stroke_shapes(stack: BoltStack) -> dict[str, cq.Shape]:
    """Return straight insertion/withdrawal sweeps from the head side.

    Insertion and reverse withdrawal occupy the same swept volumes.  The shaft
    sweep includes one full nominal bolt length outside the under-head datum;
    the head sweep stops at the installed head position and never enters wood.
    """
    spec = stack.hardware
    origin = cq.Vector(stack.under_head_origin)
    direction = cq.Vector(stack.direction).normalized()
    shaft_start = origin - direction * spec.under_head_length_mm
    head_start = origin - direction * (spec.under_head_length_mm + spec.head_height_mm)
    return {
        "shaft_insertion_and_withdrawal": cq.Solid.makeCylinder(
            spec.cad_occupied_diameter_mm / 2,
            2 * spec.under_head_length_mm,
            shaft_start,
            direction,
        ),
        "head_insertion_and_withdrawal": cq.Solid.makeCylinder(
            spec.head_diameter_mm / 2,
            spec.under_head_length_mm + spec.head_height_mm,
            head_start,
            direction,
        ),
    }


def detached_hardware_removal_shapes(stack: BoltStack) -> dict[str, cq.Shape]:
    """Return conservative 50 mm outward sweeps for detached stack hardware."""
    spec = stack.hardware
    direction = cq.Vector(stack.direction).normalized()
    head_seat = stack.head_seat.center
    nut_seat = stack.nut_seat.center
    return {
        "head_washer_outward": cq.Solid.makeCylinder(
            spec.washer_od_mm / 2,
            TOOL_LENGTH_MM + spec.washer_thickness_mm,
            head_seat - direction * (TOOL_LENGTH_MM + spec.washer_thickness_mm),
            direction,
        ),
        "nut_washer_outward": cq.Solid.makeCylinder(
            spec.washer_od_mm / 2,
            TOOL_LENGTH_MM + spec.washer_thickness_mm,
            nut_seat,
            direction,
        ),
        "nut_outward": cq.Solid.makeCylinder(
            spec.nut_diameter_mm / 2,
            TOOL_LENGTH_MM + spec.nut_height_mm,
            nut_seat + direction * spec.washer_thickness_mm,
            direction,
        ),
    }


def _make_parts(side: str, wood: dict[str, cq.Shape]) -> dict[str, cq.Shape]:
    post_box = wood[f"base_post_outer_{side}"].BoundingBox()
    left = side == "left"
    outer_x = post_box.xmin if left else post_box.xmax
    spine_x = outer_x - SPINE_SECTION_MM if left else outer_x
    link_x = (
        post_box.xmax + LINK_POST_GAP_MM
        if left
        else post_box.xmin - LINK_POST_GAP_MM - LINK_LENGTH_MM
    )
    bridge_x = spine_x if left else link_x
    return {
        f"knee_outer_{side}_spine": cq.Solid.makeBox(
            SPINE_SECTION_MM,
            SPINE_SECTION_MM,
            SPINE_LENGTH_MM,
            cq.Vector(spine_x, REAR_FACE_Y_MM, SPINE_Z0_MM),
        ),
        f"knee_outer_{side}_rear_bridge": cq.Solid.makeBox(
            BRIDGE_LENGTH_MM,
            SPINE_SECTION_MM,
            SPINE_SECTION_MM,
            cq.Vector(bridge_x, BRIDGE_REAR_Y_MM, LINK_Z0_MM),
        ),
        f"knee_outer_{side}_under_header_link": cq.Solid.makeBox(
            LINK_LENGTH_MM,
            SPINE_SECTION_MM,
            SPINE_SECTION_MM,
            cq.Vector(link_x, REAR_FACE_Y_MM, LINK_Z0_MM),
        ),
    }


def _make_stacks(
    side: str, wood: dict[str, cq.Shape], shape_ids: dict[str, str]
) -> dict[str, BoltStack]:
    left = side == "left"
    sign = 1.0 if left else -1.0
    post_box = wood[f"base_post_outer_{side}"].BoundingBox()
    outer_x = post_box.xmin if left else post_box.xmax
    head_x = outer_x - SPINE_SECTION_MM if left else outer_x + SPINE_SECTION_MM
    stacks: dict[str, BoltStack] = {}

    for index, z in enumerate((171.45, 213.5), 1):
        bolt_id = f"knee_outer_{side}_post_{index}"
        stacks[bolt_id] = _stack(
            bolt_id,
            (head_x, -137.6, z),
            (sign, 0.0, 0.0),
            (
                (shape_ids["spine"], 88.9),
                (f"base_post_outer_{side}", 38.1),
            ),
            152.4,
        )

    # Two rows across the inclined side's local-N direction, centered on the
    # authenticated former outer-base side axis.
    for index, (y, z) in enumerate(((-147.0, 310.0), (-119.0, 362.0)), 1):
        bolt_id = f"knee_outer_{side}_side_{index}"
        stacks[bolt_id] = _stack(
            bolt_id,
            (head_x, y, z),
            (sign, 0.0, 0.0),
            ((shape_ids["spine"], 88.9), (f"base_side_{side}", 88.9)),
            203.2,
        )

    bridge_spine_x = (-1280.0, -1245.0) if left else (1276.825, 1241.825)
    for index, x in enumerate(bridge_spine_x, 1):
        bolt_id = f"knee_outer_{side}_bridge_spine_{index}"
        stacks[bolt_id] = _stack(
            bolt_id,
            (x, BRIDGE_REAR_Y_MM, 189.8),
            (0.0, 1.0, 0.0),
            ((shape_ids["bridge"], 88.9), (shape_ids["spine"], 88.9)),
            203.2,
        )

    bridge_link_x = (-1022.35, -950.0) if left else (1019.175, 946.825)
    for index, x in enumerate(bridge_link_x, 1):
        bolt_id = f"knee_outer_{side}_bridge_link_{index}"
        stacks[bolt_id] = _stack(
            bolt_id,
            (x, BRIDGE_REAR_Y_MM, 194.45),
            (0.0, 1.0, 0.0),
            ((shape_ids["bridge"], 88.9), (shape_ids["under"], 88.9)),
            203.2,
        )

    header_x = (-1080.0, -1045.0) if left else (1076.825, 1041.825)
    for index, x in enumerate(header_x, 1):
        bolt_id = f"knee_outer_{side}_header_{index}"
        stacks[bolt_id] = _stack(
            bolt_id,
            (x, -137.6, 277.0),
            (0.0, 0.0, -1.0),
            (("base_header", 38.1), (shape_ids["under"], 88.9)),
            152.4,
        )
    return stacks


def _connector_bores(
    part_shapes: dict[str, cq.Shape], stacks: dict[str, BoltStack]
) -> dict[str, list[tuple[str, cq.Shape]]]:
    result = {part_id: [] for part_id in part_shapes}
    for stack in stacks.values():
        position = stack.head_seat.center
        direction = cq.Vector(stack.direction).normalized()
        for layer in stack.layers:
            if layer.body_id in result:
                cutter = cq.Solid.makeCylinder(
                    stack.hardware.drill_diameter_mm / 2,
                    layer.thickness_mm,
                    position,
                    direction,
                )
                result[layer.body_id].append((stack.id, cutter))
            position += direction * layer.thickness_mm
    return result


def _finished_source_hosts(
    source_shapes: dict[str, cq.Shape],
    source_finished_shapes: dict[str, cq.Shape],
    source_connections,
    stacks: dict[str, BoltStack],
    binding: SourceBinding,
) -> dict[str, FinishedPart]:
    inventory = json.loads(SOURCE_INVENTORY.read_text())
    records = {row["part_id"]: row for row in inventory["parts"]}
    raw = {name: source_shapes[name] for name in SOURCE_HOST_IDS}
    cuts = _connector_bores(raw, stacks)
    target_axes = {
        axis["axis_id"]
        for duty in inventory["legacy_duties"]
        if duty["legacy_station_id"] in LEGACY_DUTY_HOSTS
        for axis in duty["legacy_sds_axes"]
    }
    connections = {row.name: row for row in source_connections}
    result = {}
    for part_id, uncut in raw.items():
        source_record = records[part_id]
        # Start from the selected candidate's fully machined host, then restore
        # only the four replaced stations' SDS holes before adding WJ-03 bores.
        source_finished = source_finished_shapes[part_id]
        for axis_id in target_axes:
            connection = connections[axis_id]
            if part_id not in connection.members:
                continue
            cutter = cq.Solid.makeCylinder(
                connection.diameter / 2,
                connection.length + 2.0,
                connection.start - connection.direction.normalized(),
                connection.direction.normalized(),
            )
            source_finished = source_finished.fuse(cutter.intersect(uncut)).clean()
        for axis in inventory["fixed_panel_kicker_screws"]:
            connection = connections[axis["axis_id"]]
            if part_id not in connection.members:
                continue
            purchased_envelope = cq.Solid.makeCylinder(
                connection.diameter / 2,
                axis["shop_purchased_length_mm"],
                connection.start,
                connection.direction.normalized(),
            )
            source_finished = source_finished.cut(purchased_envelope).clean()
        retained_openings = uncut.cut(source_finished).clean()
        finished = source_finished
        modifications = [
            CutRecord(
                f"{part_id}/retained_source_openings",
                part_id,
                "other",
                retained_openings,
                "selected-candidate retained bores and service openings; four replaced SDS stations restored",
            )
        ]
        for bolt_id, cutter in cuts[part_id]:
            finished = finished.cut(cutter)
            modifications.append(
                CutRecord(
                    f"{part_id}/{bolt_id}",
                    part_id,
                    "bore",
                    cutter,
                    "candidate through-bore; jig and bit unselected",
                )
            )
        transform = source_record["local_to_global_transform"]
        axes = source_record["local_axes"]
        result[part_id] = FinishedPart(
            id=part_id,
            stock_product=source_record["stock_product"],
            actual_dimensions_mm=tuple(source_record["source_blank_dimensions_mm"]),
            material="DF-L No. 2 assumed; delivered source member unobserved",
            grain_axis=tuple(source_record["grain_axis_global_xyz"]),
            frame=LocalFrame(
                tuple(row[3] for row in transform[:3]),
                tuple(axes["X"]),
                tuple(axes["T"]),
                tuple(axes["N"]),
            ),
            transport_owner=source_record["transport_owner"],
            uncut_shape=uncut,
            finished_shape=finished.clean(),
            modifications=tuple(modifications),
            source_sha256=binding.uncut_host_shape_sha256[part_id],
            fabrication_method="source member plus recorded WJ-03 through-bores",
        )
    return result


def _finished_parts(
    side: str, raw: dict[str, cq.Shape], stacks: dict[str, BoltStack]
) -> dict[str, FinishedPart]:
    source_hash = hashlib.sha256(SOURCE_INVENTORY.read_bytes()).hexdigest()
    cuts = _connector_bores(raw, stacks)
    result = {}
    for part_id, uncut in raw.items():
        finished = uncut
        records = []
        for bolt_id, cutter in cuts[part_id]:
            finished = finished.cut(cutter)
            records.append(
                CutRecord(
                    f"{part_id}/{bolt_id}",
                    part_id,
                    "bore",
                    cutter,
                    "through-drill from recorded face; jig and bit unselected",
                )
            )
        box = uncut.BoundingBox()
        dimensions = (box.xlen, box.ylen, box.zlen)
        grain = (0.0, 0.0, 1.0) if part_id.endswith("spine") else (1.0, 0.0, 0.0)
        result[part_id] = FinishedPart(
            id=part_id,
            stock_product="nominal 4x4 solid-sawn DF-L No. 2 cutoff",
            actual_dimensions_mm=dimensions,
            material="DF-L No. 2 assumed; delivered stock unobserved",
            grain_axis=grain,
            frame=LocalFrame(
                (box.xmin, box.ymin, box.zmin), (1, 0, 0), (0, 1, 0), (0, 0, 1)
            ),
            transport_owner=f"knee_outer_{side}",
            uncut_shape=uncut,
            finished_shape=finished.clean(),
            modifications=tuple(records),
            source_sha256=source_hash,
            fabrication_method="square crosscuts plus recorded through-bores; no primary-member notch",
        )
    return result


def _interfaces(
    side: str,
    stacks: dict[str, BoltStack],
    ids: dict[str, str],
    contact_frames: dict[str, LocalFrame],
) -> tuple[InterfaceRecord, ...]:
    duties = LEGACY_DUTIES[side]

    def row(
        suffix: str,
        bodies: tuple[str, str],
        contacts: tuple[str, str],
        prefixes: tuple[str, ...],
        penetration: tuple[str, ...],
        duties_for_interface: tuple[str, ...],
        behavior: str = "fastened",
    ) -> InterfaceRecord:
        bolt_ids = tuple(
            bolt_id
            for bolt_id in stacks
            if any(prefix in bolt_id for prefix in prefixes)
        )
        access_sequence = (
            (
                "support connector parts",
                "separate compression contact after adjacent fastened interfaces are released",
            )
            if behavior == "compression_only"
            else (
                "remove retained panels as required by complete move sequence",
                "support connector parts",
                "remove nut, washer, bolt, and second washer with recorded tools",
            )
        )
        return InterfaceRecord(
            id=f"knee_outer_{side}_{suffix}",
            body_ids=bodies,
            legacy_duties=duties_for_interface,
            contact_face_ids=contacts,
            frame=contact_frames[suffix],
            behavior=behavior,
            bolt_group_ids=bolt_ids,
            bolt_penetration_order=penetration,
            force_reference_point=contact_frames[suffix].origin,
            separates_for_move=True,
            access_sequence=access_sequence,
        )

    return (
        row(
            "spine_post",
            (ids["spine"], f"base_post_outer_{side}"),
            (f"{ids['spine']}:inner_x", f"base_post_outer_{side}:outer_x"),
            ("_post_",),
            (ids["spine"], f"base_post_outer_{side}"),
            (duties[0],),
        ),
        row(
            "spine_side",
            (ids["spine"], f"base_side_{side}"),
            (f"{ids['spine']}:inner_x", f"base_side_{side}:outer_x"),
            ("_side_",),
            (ids["spine"], f"base_side_{side}"),
            (duties[1],),
        ),
        row(
            "bridge_spine",
            (ids["bridge"], ids["spine"]),
            (f"{ids['bridge']}:front_y", f"{ids['spine']}:rear_y"),
            ("_bridge_spine_",),
            (ids["bridge"], ids["spine"]),
            duties,
        ),
        row(
            "bridge_link",
            (ids["bridge"], ids["under"]),
            (f"{ids['bridge']}:front_y", f"{ids['under']}:rear_y"),
            ("_bridge_link_",),
            (ids["bridge"], ids["under"]),
            duties,
        ),
        row(
            "link_header",
            (ids["under"], "base_header"),
            (f"{ids['under']}:top_z", "base_header:bottom_z"),
            ("_header_",),
            ("base_header", ids["under"]),
            duties,
        ),
        row(
            "spine_header_end",
            (ids["spine"], "base_header"),
            (f"{ids['spine']}:inner_x", "base_header:outer_end_x"),
            ("_no_bolt_group_",),
            (),
            duties,
            "compression_only",
        ),
    )


def _build_outer_nodes() -> dict[str, OuterNode]:
    source = variant(KERF_RIGHT)
    binding = validate_source_binding(source)
    wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    raw_by_side = {side: _make_parts(side, wood) for side in SIDES}
    ids_by_side = {
        side: {
            "spine": f"knee_outer_{side}_spine",
            "bridge": f"knee_outer_{side}_rear_bridge",
            "under": f"knee_outer_{side}_under_header_link",
        }
        for side in SIDES
    }
    stacks_by_side = {
        side: _make_stacks(side, wood, ids_by_side[side]) for side in SIDES
    }
    all_stacks = {
        bolt_id: stack
        for stacks in stacks_by_side.values()
        for bolt_id, stack in stacks.items()
    }
    source_finished = {part.name: part.shape for part in source.parts()}
    source_host_parts = _finished_source_hosts(
        wood, source_finished, source.connections(), all_stacks, binding
    )
    result = {}
    for side in SIDES:
        ids = ids_by_side[side]
        stacks = stacks_by_side[side]
        parts = _finished_parts(side, raw_by_side[side], stacks)
        sign = 1.0 if side == "left" else -1.0
        physical = {
            **{part_id: part.finished_shape for part_id, part in parts.items()},
            **{
                part_id: part.finished_shape
                for part_id, part in source_host_parts.items()
            },
        }
        contact_specs = {
            "spine_post": (
                physical[ids["spine"]],
                physical[f"base_post_outer_{side}"],
                (sign, 0.0, 0.0),
            ),
            "spine_side": (
                physical[ids["spine"]],
                physical[f"base_side_{side}"],
                (sign, 0.0, 0.0),
            ),
            "bridge_spine": (
                physical[ids["bridge"]],
                physical[ids["spine"]],
                (0.0, 1.0, 0.0),
            ),
            "bridge_link": (
                physical[ids["bridge"]],
                physical[ids["under"]],
                (0.0, 1.0, 0.0),
            ),
            "link_header": (
                physical[ids["under"]],
                physical["base_header"],
                (0.0, 0.0, 1.0),
            ),
            "spine_header_end": (
                physical[ids["spine"]],
                physical["base_header"],
                (sign, 0.0, 0.0),
            ),
        }
        geometry = {
            name: _contact_geometry(*spec) for name, spec in contact_specs.items()
        }
        contacts = {name: area for name, (area, _) in geometry.items()}
        contact_frames = {name: frame for name, (_, frame) in geometry.items()}
        relevant_hosts = (
            "base_header",
            f"base_post_outer_{side}",
            f"base_side_{side}",
        )
        result[side] = OuterNode(
            side=side,
            owner_id=f"knee_outer_{side}",
            duties=LEGACY_DUTIES[side],
            source_hosts=relevant_hosts,
            parts=parts,
            source_host_parts={
                name: source_host_parts[name] for name in relevant_hosts
            },
            stacks=stacks,
            interfaces=_interfaces(side, stacks, ids, contact_frames),
            contact_areas_mm2=contacts,
            source_binding=binding,
        )
    return result


def build_outer_node(side: str) -> OuterNode:
    if side not in SIDES:
        raise ValueError(f"Unknown outer-node side: {side}")
    return _build_outer_nodes()[side]


def build_outer_nodes() -> dict[str, OuterNode]:
    return _build_outer_nodes()
