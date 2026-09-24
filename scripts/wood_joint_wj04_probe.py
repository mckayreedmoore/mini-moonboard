"""Source-bound WJ-04 ordinary rail-joint diagnostic; no build dimensions.

The model keeps both source hosts unnotched.  A sawn solid-wood cleat bears on
their actual faces.  Four provisional through-bolt stacks connect the two
serial interfaces.  Every reported failure is a development finding, not a
shop instruction or structural acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from mini_moonboard.wood_joint_frame import (
    ORDINARY_REAR_ENVELOPE_MM,
    access_shapes,
    bolt_axis_stroke_shapes,
    detached_hardware_removal_shapes,
    validate_source_binding,
)
from mini_moonboard.wood_joint_geometry import (
    BoltHardware,
    BoltStack,
    StackLayer,
    WasherSeat,
    bolt_stack_report,
    washer_support_report,
)
from mini_moonboard.wood_joint_panel_machining import (
    PANEL_CONNECTION_COUNT,
    RIGHT_PANEL_NAMES,
    candidate_panel_replacements,
)
from mini_moonboard.wood_joint_wj04_config import (
    WJ04_TRIAL,
    WJ04TrialConfig,
    validate_wj04_trial,
)
from scripts.wood_joint_clearance import _wj03_protected_inventory

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/wood-joints-mvp/wj04-probe.json"
NEIGHBOR = "base_rail_service_upper_right"
HIT_MM3 = 1e-6
CONTACT_PROBE_MM = 0.1
NUT_REMOVAL_REARWARD_TRAVEL_MM = 100.0

# Historical WJ-04 rescue consumers import these names. Active geometry below
# reads the canonical trial directly; these aliases carry no separate authority.
UPRIGHT = next(
    member.source_part_id for member in WJ04_TRIAL.members if member.role == "principal"
)
RAIL = next(
    member.source_part_id for member in WJ04_TRIAL.members if member.role == "rail"
)
LEGACY_DUTY = WJ04_TRIAL.station_id
X = cq.Vector(*WJ04_TRIAL.frame.x_global)
T = cq.Vector(*WJ04_TRIAL.frame.t_global)
N = cq.Vector(*WJ04_TRIAL.frame.n_global)
SECTION_X_MM = WJ04_TRIAL.cleat.size_x_t_n_mm[0]
SECTION_T_MM = WJ04_TRIAL.cleat.size_x_t_n_mm[1]
FRONT_SHIFT_MM = WJ04_TRIAL.cleat_front_offset_n_mm


@dataclass(frozen=True)
class MaterializedTrialGeometry:
    """Shared source-bound WJ-04 solids for probe, access screen, and viewer."""

    config: WJ04TrialConfig
    source_binding: Any
    source: Any
    wood: dict[str, cq.Shape]
    source_finished: dict[str, cq.Shape]
    parts: dict[str, cq.Shape]
    cleat: cq.Shape
    stacks: dict[str, BoltStack]
    bores: dict[str, cq.Shape]
    bore_reports: dict[str, dict[str, Any]]
    finished: dict[str, cq.Shape]
    installed: dict[str, cq.Shape]
    protected: dict[str, cq.Shape]
    all_wood: dict[str, cq.Shape]
    panels: dict[str, cq.Shape]
    panel_machining: dict[str, Any]
    other_wood: dict[str, cq.Shape]
    cleat_hits: dict[str, dict[str, float]]
    contact_area_mm2: dict[str, float]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frame_axes(config: WJ04TrialConfig) -> tuple[cq.Vector, cq.Vector, cq.Vector]:
    return tuple(
        cq.Vector(*axis)
        for axis in (
            config.frame.x_global,
            config.frame.t_global,
            config.frame.n_global,
        )
    )


def _world(*args) -> cq.Vector:
    if len(args) == 4 and isinstance(args[0], WJ04TrialConfig):
        config, x, t, n = args
    elif len(args) == 3:
        config, (x, t, n) = WJ04_TRIAL, args
    else:
        raise TypeError("_world expects (x, t, n) or (config, x, t, n)")
    return cq.Vector(*config.frame.to_global((x, t, n)))


def _point_basis(
    config: WJ04TrialConfig, point: cq.Vector
) -> tuple[float, float, float]:
    axes = tuple(
        cq.Vector(*axis)
        for axis in (
            config.frame.x_global,
            config.frame.t_global,
            config.frame.n_global,
        )
    )
    return tuple(point.dot(axis) for axis in axes)


def _box_in_trial_frame(
    config: WJ04TrialConfig,
    origin_basis_mm: tuple[float, float, float],
    size_x_t_n_mm: tuple[float, float, float],
) -> cq.Shape:
    x_axis, t_axis, n_axis = _frame_axes(config)
    global_x = cq.Vector(1, 0, 0)
    if (x_axis - global_x).Length > 1e-9 or (
        x_axis.cross(t_axis) - n_axis
    ).Length > 1e-9:
        raise ValueError("WJ-04 frame must be an X rotation of global X/T/N")
    angle_degrees = math.degrees(math.atan2(t_axis.z, t_axis.y))
    origin = cq.Vector(*config.frame.to_global(origin_basis_mm))
    shape = (
        cq.Solid.makeBox(*size_x_t_n_mm)
        .rotate((0, 0, 0), (1, 0, 0), angle_degrees)
        .translate(origin)
    )
    expected_ranges = tuple(
        (origin_basis_mm[index], origin_basis_mm[index] + size_x_t_n_mm[index])
        for index in range(3)
    )
    for axis, expected in zip((x_axis, t_axis, n_axis), expected_ranges, strict=True):
        values = [vertex.Center().dot(axis) for vertex in shape.Vertices()]
        if (
            abs(min(values) - expected[0]) > 1e-6
            or abs(max(values) - expected[1]) > 1e-6
        ):
            raise ValueError(
                "WJ-04 cleat transform does not preserve configured extents"
            )
    return shape


def _extent(shape: cq.Shape, axis: cq.Vector) -> tuple[float, float]:
    values = [vertex.Center().dot(axis) for vertex in shape.Vertices()]
    return min(values), max(values)


def _intersect_volume(first: cq.Shape, second: cq.Shape) -> float:
    a, b = first.BoundingBox(), second.BoundingBox()
    if (
        a.xmax < b.xmin
        or b.xmax < a.xmin
        or a.ymax < b.ymin
        or b.ymax < a.ymin
        or a.zmax < b.zmin
        or b.zmax < a.zmin
    ):
        return 0.0
    return first.intersect(second).Volume()


def _hits(shape: cq.Shape, others: dict[str, cq.Shape]) -> dict[str, float]:
    return {
        name: round(volume, 6)
        for name, other in others.items()
        if (volume := _intersect_volume(shape, other)) > HIT_MM3
    }


def _panel_axis_records(source) -> tuple[dict[str, Any], ...]:
    """Capture fixed panel-axis identity before and after panel replacement."""
    connections = tuple(source.panel_connections())
    names = [connection.name for connection in connections]
    if len(connections) != PANEL_CONNECTION_COUNT or len(set(names)) != len(names):
        raise ValueError(
            "WJ-04 panel remachining requires the exact unique source panel axes"
        )
    return tuple(
        {
            "axis_id": connection.name,
            "members": tuple(connection.members),
            "start_global_xyz_mm": tuple(
                float(value) for value in connection.start.toTuple()
            ),
            "direction_global_xyz": tuple(
                float(value) for value in connection.direction.toTuple()
            ),
            "length_mm": float(connection.length),
            "diameter_mm": float(connection.diameter),
            "kind": connection.kind,
        }
        for connection in connections
    )


def _candidate_panel_obstacles(
    source,
    source_panels: dict[str, cq.Shape],
    current_parts,
    uncut_parts,
) -> tuple[dict[str, cq.Shape], dict[str, Any]]:
    """Overlay candidate right-panel solids while preserving source geometry."""
    axes_before = _panel_axis_records(source)
    replacement_parts = candidate_panel_replacements(
        source, current_parts=current_parts, uncut_parts=uncut_parts
    )
    if set(replacement_parts) != RIGHT_PANEL_NAMES:
        raise ValueError(
            "WJ-04 panel remachining must replace exactly the three right panels"
        )
    if not RIGHT_PANEL_NAMES <= source_panels.keys():
        missing = sorted(RIGHT_PANEL_NAMES - source_panels.keys())
        raise ValueError(f"WJ-04 source panel obstacles are missing: {missing}")
    for name, part in replacement_parts.items():
        shape = getattr(part, "shape", None)
        if (
            getattr(part, "name", None) != name
            or not isinstance(shape, cq.Shape)
            or not shape.isValid()
            or not shape.Solids()
        ):
            raise ValueError(f"WJ-04 candidate panel replacement is invalid: {name}")

    axes_after = _panel_axis_records(source)
    if axes_after != axes_before:
        raise ValueError("WJ-04 panel remachining changed fixed source panel axes")
    obstacles = dict(source_panels)
    obstacles.update({name: part.shape for name, part in replacement_parts.items()})
    axis_identity = hashlib.sha256(
        json.dumps(axes_before, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return obstacles, {
        "replacement_names": sorted(replacement_parts),
        "fixed_panel_axis_count": len(axes_before),
        "fixed_panel_axis_identity_sha256": axis_identity,
        "fixed_panel_axes_preserved": True,
        "raw_source_panel_shapes_preserved_separately": True,
    }


def build_stacks(config: WJ04TrialConfig = WJ04_TRIAL) -> dict[str, BoltStack]:
    """Adapt canonical WJ-04 config records to shared CAD stack records."""
    validate_wj04_trial(config)
    result: dict[str, BoltStack] = {}
    for configured in config.stacks:
        candidate = configured.hardware_candidate
        envelope = configured.cad_envelope
        axis = cq.Vector(*config.axis_point_global(configured.stack_id))
        direction = cq.Vector(
            *config.axis_direction_global(configured.stack_id)
        ).normalized()
        layers = tuple(
            StackLayer(layer.member_id, layer.thickness_mm)
            for layer in configured.layers
        )
        hardware = BoltHardware(
            candidate_sku=candidate.sku,
            under_head_length_mm=candidate.nominal_length_mm,
            steel_diameter_mm=envelope.shaft_diameter_mm,
            cad_occupied_diameter_mm=envelope.shaft_diameter_mm,
            drill_diameter_mm=envelope.bore_occupancy_diameter_mm,
            head_diameter_mm=envelope.head_diameter_mm,
            head_height_mm=envelope.head_height_mm,
            washer_od_mm=envelope.washer_outer_diameter_mm,
            washer_id_mm=envelope.washer_inner_diameter_mm,
            washer_thickness_mm=envelope.washer_thickness_mm,
            nut_diameter_mm=envelope.nut_diameter_mm,
            nut_height_mm=envelope.nut_height_mm,
            usable_thread_start_mm=candidate.maximum_full_thread_start_mm,
            usable_thread_end_mm=candidate.nominal_length_mm,
        )
        result[configured.stack_id] = BoltStack(
            id=configured.stack_id,
            hardware=hardware,
            under_head_origin=axis - direction * hardware.washer_thickness_mm,
            direction=direction,
            layers=layers,
            head_seat=WasherSeat(layers[0].body_id, axis, direction),
            nut_seat=WasherSeat(
                layers[-1].body_id, axis + direction * configured.grip_mm, -direction
            ),
            required_tip_projection_mm=envelope.required_tip_projection_mm,
        )
    return result


def stack_adapter_records(
    config: WJ04TrialConfig = WJ04_TRIAL,
) -> dict[str, dict[str, Any]]:
    """Return cheap serializable stack records without source CAD materialization."""
    validate_wj04_trial(config)
    canonical = {row["stack_id"]: row for row in config.as_dict()["stacks"]}
    stacks = build_stacks(config)
    return {
        configured.stack_id: {
            "bolt_candidate_id": configured.hardware_candidate.candidate_id,
            "bolt_sku": configured.hardware_candidate.sku,
            "cad_envelope": canonical[configured.stack_id]["cad_envelope"],
            "grip_mm": stack.grip_mm,
            "nominal_under_head_length_mm": stack.hardware.under_head_length_mm,
            "axis_global_xyz_mm": [
                round(value, 6) for value in stack.head_seat.center.toTuple()
            ],
            "direction_global_xyz": [
                round(value, 9) for value in stack.direction.toTuple()
            ],
            "layers": [
                {"member_id": layer.body_id, "thickness_mm": layer.thickness_mm}
                for layer in stack.layers
            ],
        }
        for configured in config.stacks
        for stack in (stacks[configured.stack_id],)
    }


def trial_adapter_metadata(config: WJ04TrialConfig = WJ04_TRIAL) -> dict[str, Any]:
    """Return canonical trial/source/stock metadata without source CAD work."""
    validate_wj04_trial(config)
    return {
        "trial_id": config.trial_id,
        "trial_config_sha256": config.canonical_sha256,
        "source_inventory_sha256": config.source_inventory_sha256,
        "source_commit": config.source_commit,
        "stock": {
            "section_x_t_n_mm": list(config.cleat.size_x_t_n_mm or ()),
            "grain_axis": config.cleat.grain_axis,
            "dimensional_source": config.cleat.stock_note,
            "stock_source_urls": list(config.cleat.stock_source_urls),
            "actual_stock_and_grade_verified": config.stock_grade_verified,
        },
        "stacks": stack_adapter_records(config),
        "catalog_candidate_ids": {
            "bolts": [candidate.candidate_id for candidate in config.fasteners.bolts],
            "nut": config.fasteners.nut.candidate_id,
            "washer": config.fasteners.washer.candidate_id,
            "tools": [candidate.candidate_id for candidate in config.fasteners.tools],
        },
        "release_claims": {
            "purchase_approved": config.purchase_approved,
            "drilling_released": config.drilling_released,
            "fabrication_released": config.fabrication_released,
            "structural_released": config.structural_released,
        },
    }


def _member_by_role(config: WJ04TrialConfig, role: str):
    matches = [member for member in config.members if member.role == role]
    if len(matches) != 1:
        raise ValueError(f"WJ-04 config must have one {role!r} member")
    return matches[0]


def _protected(source, config: WJ04TrialConfig = WJ04_TRIAL) -> dict[str, cq.Shape]:
    # Keep WJ-03's purchased 63.5 mm Hillman and complete retained frame stacks.
    rows = _wj03_protected_inventory(source)["solids"]
    return {
        f"{family}/{name}": shape
        for family, family_rows in rows.items()
        for name, shape in family_rows.items()
        if config.station_id
        not in name  # This exact angle and its six SDS are removed.
    }


def _retained_source_hosts(
    config: WJ04TrialConfig,
    source,
    wood: dict[str, cq.Shape],
    source_finished: dict[str, cq.Shape],
    connections,
) -> dict[str, cq.Shape]:
    """Keep selected source machining; restore only SDS axes replaced at this station."""
    inventory = json.loads((ROOT / config.source_inventory_path).read_text())
    axes = {
        axis["axis_id"]
        for duty in inventory["legacy_duties"]
        if duty["legacy_station_id"] == config.station_id
        for axis in duty["legacy_sds_axes"]
    }
    by_id = {connection.name: connection for connection in connections}
    hosts = {
        member.source_part_id
        for member in config.members
        if member.source_part_id is not None
    }
    result = {}
    for host_id in hosts:
        finished = source_finished[host_id]
        uncut = wood[host_id]
        for axis_id in axes:
            connection = by_id[axis_id]
            if host_id not in connection.members:
                continue
            direction = connection.direction.normalized()
            replaced_sds_bore = cq.Solid.makeCylinder(
                connection.diameter / 2,
                connection.length + 2.0,
                connection.start - direction,
                direction,
            )
            restored_sds = replaced_sds_bore.intersect(uncut)
            finished = finished.fuse(restored_sds).clean()
        # Re-cut every retained named source axis after restoring this station's
        # six replaced SDS holes; this protects crossing openings directly.
        for connection in connections:
            if host_id not in connection.members or connection.name in axes:
                continue
            direction = connection.direction.normalized()
            diameter = (
                source.bolt_dimensions(connection)["hole_diameter_mm"]
                if connection.kind == "bolt"
                else connection.diameter
            )
            retained_axis_bore = cq.Solid.makeCylinder(
                diameter / 2,
                connection.length + 2.0,
                connection.start - direction,
                direction,
            )
            finished = finished.cut(retained_axis_bore).clean()
        for member_id, _, cutter in source.service_cutters():
            if member_id == host_id:
                finished = finished.cut(cutter).clean()
        for member_id, _, _, cutter in source.additional_machining_cutters():
            if member_id == host_id:
                finished = finished.cut(cutter).clean()
        for axis in inventory["fixed_panel_kicker_screws"]:
            connection = by_id[axis["axis_id"]]
            if host_id not in connection.members:
                continue
            purchased_envelope = cq.Solid.makeCylinder(
                connection.diameter / 2,
                axis["shop_purchased_length_mm"],
                connection.start,
                connection.direction.normalized(),
            )
            finished = finished.cut(purchased_envelope).clean()
        result[host_id] = finished
    return result


def materialize_trial_geometry(
    config: WJ04TrialConfig = WJ04_TRIAL,
) -> MaterializedTrialGeometry:
    """Materialize source-bound configured hosts, cleat, bores, and stacks."""
    validate_wj04_trial(config)
    source = variant(KERF_RIGHT)
    binding = validate_source_binding(source)
    if binding.inventory_sha256 != config.source_inventory_sha256:
        raise ValueError("WJ-04 source inventory hash differs from canonical config")
    uncut_parts = tuple(source.uncut_wood_parts())
    source_parts = tuple(source.parts())
    wood = {part.name: part.shape for part in uncut_parts}
    source_finished = {
        part.name: part.shape for part in source_parts if part.name in wood
    }
    source_connections = source.connections()
    retained_source_hosts = _retained_source_hosts(
        config, source, wood, source_finished, source_connections
    )
    rail_member = _member_by_role(config, "rail")
    principal_member = _member_by_role(config, "principal")
    if rail_member.source_part_id is None or principal_member.source_part_id is None:
        raise ValueError("WJ-04 source host bindings must name source parts")
    rail, upright = (
        retained_source_hosts[rail_member.source_part_id],
        retained_source_hosts[principal_member.source_part_id],
    )
    cleat_member = config.cleat
    if cleat_member.size_x_t_n_mm is None or cleat_member.origin_x_t_n_mm is None:
        raise ValueError("WJ-04 cleat requires configured size and origin")
    cleat = _box_in_trial_frame(
        config, cleat_member.origin_x_t_n_mm, cleat_member.size_x_t_n_mm
    )
    parts = {
        rail_member.member_id: rail,
        principal_member.member_id: upright,
        cleat_member.member_id: cleat,
    }
    stacks = build_stacks(config)
    x_axis, t_axis, _ = _frame_axes(config)
    protected = _protected(source, config)
    all_wood = {
        name: shape
        for name, shape in source_finished.items()
        if not name.startswith(("main_", "kicker_"))
    }
    source_panels = {
        name: shape
        for name, shape in source_finished.items()
        if name.startswith(("main_", "kicker_"))
    }
    panels, panel_machining = _candidate_panel_obstacles(
        source, source_panels, source_parts, uncut_parts
    )
    all_wood.update(
        {
            member.source_part_id: retained_source_hosts[member.source_part_id]
            for member in (rail_member, principal_member)
            if member.source_part_id is not None
        }
    )
    other_wood = {
        name: shape
        for name, shape in all_wood.items()
        if name not in (rail_member.source_part_id, principal_member.source_part_id)
    }
    cleat_hits = {
        "hosts": _hits(
            cleat,
            {
                rail_member.source_part_id: rail,
                principal_member.source_part_id: upright,
            },
        ),
        "other_wood": _hits(cleat, other_wood),
        "panels": _hits(cleat, panels),
        "protected": _hits(cleat, protected),
    }
    # The two interfaces are nominally face-to-face; thin inward probes record area.
    rail_contact = (
        cleat.translate(-t_axis * CONTACT_PROBE_MM).intersect(rail).Volume()
        / CONTACT_PROBE_MM
    )
    upright_contact = (
        cleat.translate(-x_axis * CONTACT_PROBE_MM).intersect(upright).Volume()
        / CONTACT_PROBE_MM
    )
    bores = {}
    bore_reports = {}
    for name, stack in stacks.items():
        start = stack.head_seat.center - stack.direction * CONTACT_PROBE_MM
        bores[name] = cq.Solid.makeCylinder(
            stack.hardware.drill_diameter_mm / 2,
            stack.grip_mm + 2 * CONTACT_PROBE_MM,
            start,
            stack.direction,
        )
        progress = 0.0
        layer_fractions = {}
        for layer in stack.layers:
            segment = cq.Solid.makeCylinder(
                stack.hardware.drill_diameter_mm / 2,
                layer.thickness_mm,
                stack.head_seat.center + stack.direction * progress,
                stack.direction,
            )
            layer_fractions[layer.body_id] = round(
                _intersect_volume(segment, parts[layer.body_id]) / segment.Volume(), 6
            )
            progress += layer.thickness_mm
        bore_reports[name] = {
            "layer_material_fractions": layer_fractions,
            "unrelated_wood_hits": _hits(bores[name], other_wood),
            "panel_hits": _hits(bores[name], panels),
            "protected_hits": _hits(bores[name], protected),
        }
    finished = {
        name: shape.cut(
            *[
                bore
                for bore in bores.values()
                if _intersect_volume(shape, bore) > HIT_MM3
            ]
        )
        for name, shape in parts.items()
    }
    installed = {
        f"{name}/{role}": shape
        for name, stack in stacks.items()
        for role, shape in stack.installed_shapes().items()
    }
    return MaterializedTrialGeometry(
        config=config,
        source_binding=binding,
        source=source,
        wood=wood,
        source_finished=source_finished,
        parts=parts,
        cleat=cleat,
        stacks=stacks,
        bores=bores,
        bore_reports=bore_reports,
        finished=finished,
        installed=installed,
        protected=protected,
        all_wood=all_wood,
        panels=panels,
        panel_machining=panel_machining,
        other_wood=other_wood,
        cleat_hits=cleat_hits,
        contact_area_mm2={
            "rail_to_cleat": rail_contact,
            "principal_to_cleat": upright_contact,
        },
    )


def report(config: WJ04TrialConfig = WJ04_TRIAL, geometry=None) -> dict:
    validate_wj04_trial(config)
    geometry = materialize_trial_geometry(config) if geometry is None else geometry
    if geometry.config.canonical_sha256 != config.canonical_sha256:
        raise ValueError(
            "WJ-04 report geometry was materialized from a different trial"
        )
    binding = geometry.source_binding
    wood = geometry.wood
    parts = geometry.parts
    rail_member = _member_by_role(config, "rail")
    principal_member = _member_by_role(config, "principal")
    cleat_member = config.cleat
    rail_id = rail_member.member_id
    rail = parts[rail_id]
    stacks = geometry.stacks
    protected = geometry.protected
    panels, other_wood = geometry.panels, geometry.other_wood
    bore_reports = geometry.bore_reports
    finished, installed = geometry.finished, geometry.installed
    cleat_hits = geometry.cleat_hits
    _, t_axis, n_axis = _frame_axes(config)
    rail_t0, rail_t1 = _extent(rail, t_axis)
    rail_n0, rail_n1 = _extent(rail, n_axis)
    all_finished = {**other_wood, **panels, **finished}
    stacks_out = {}
    adapter_rows = stack_adapter_records(config)
    for name, stack in stacks.items():
        own = {layer.body_id for layer in stack.layers}
        other_installed = {
            key: shape
            for key, shape in installed.items()
            if not key.startswith(f"{name}/")
        }
        # Installed shaft lies in its own through-bore.  Tools, nuts, and
        # removal sweeps must clear all unrelated occupied solids.
        installed_hits = {
            role: {
                "wood": _hits(shape, all_finished),
                "protected": _hits(shape, protected),
                "other_hardware": _hits(shape, other_installed),
            }
            for role, shape in stack.installed_shapes().items()
        }
        operations = {}
        for family, shapes in (
            ("tools_50mm", access_shapes(stack)),
            ("withdrawal", bolt_axis_stroke_shapes(stack)),
            ("detached", detached_hardware_removal_shapes(stack)),
        ):
            operations[family] = {
                role: {
                    "other_wood": _hits(
                        shape, {k: v for k, v in all_finished.items() if k not in own}
                    ),
                    "protected": _hits(shape, protected),
                    "other_hardware": _hits(shape, other_installed),
                }
                for role, shape in shapes.items()
            }
        if name.startswith("rail_"):
            spec = stack.hardware
            direction = stack.direction
            nut_start = stack.nut_seat.center + direction * spec.washer_thickness_mm
            tip = stack.under_head_origin + direction * spec.under_head_length_mm
            axial_travel = (tip - nut_start).dot(direction) + CONTACT_PROBE_MM
            axial_nut = cq.Solid.makeCylinder(
                spec.nut_diameter_mm / 2,
                axial_travel + spec.nut_height_mm,
                nut_start,
                direction,
            )
            # After the nut clears the shaft, move it rearward in the open
            # gap between service rails. This box encloses the round nut.
            lateral_start = nut_start + direction * axial_travel
            lateral_basis = _point_basis(config, lateral_start)
            lateral_end = _box_in_trial_frame(
                config,
                (
                    lateral_basis[0] - spec.nut_diameter_mm / 2,
                    lateral_basis[1],
                    _point_basis(config, stack.nut_seat.center)[2]
                    - spec.nut_diameter_mm / 2,
                ),
                (
                    spec.nut_diameter_mm,
                    spec.nut_height_mm,
                    NUT_REMOVAL_REARWARD_TRAVEL_MM + spec.nut_diameter_mm,
                ),
            )
            tool_sweeps = {
                f"{length}mm_tool_during_unthread": cq.Solid.makeCylinder(
                    25.4 / 2,
                    length + axial_travel,
                    stack.nut_seat.center + direction * 2.0,
                    direction,
                )
                for length in config.diagnostic_tool_widths_mm
            }
            physical_removal = {
                "axial_nut_to_tip": axial_nut,
                "rearward_nut_after_unthread": lateral_end,
                **tool_sweeps,
            }
            operations["bounded_rail_nut_removal"] = {
                role: {
                    "other_wood": _hits(
                        shape, {k: v for k, v in all_finished.items() if k not in own}
                    ),
                    "protected": _hits(shape, protected),
                    "other_hardware": _hits(shape, other_installed),
                }
                for role, shape in physical_removal.items()
            }
            operations["bounded_rail_nut_removal"]["axial_travel_mm"] = round(
                axial_travel, 6
            )
        seats = {
            "head": washer_support_report(
                stack.head_seat, finished[stack.head_seat.body_id], stack.hardware
            ),
            "nut": washer_support_report(
                stack.nut_seat, finished[stack.nut_seat.body_id], stack.hardware
            ),
        }
        length = bolt_stack_report(stack)
        configured_stack = config.stack_by_id(name)
        bolt_candidate = configured_stack.hardware_candidate
        stacks_out[name] = {
            **adapter_rows[name],
            "bolt_candidate_status": bolt_candidate.status,
            "bolt_catalog_source_urls": list(bolt_candidate.source_urls),
            "full_form_thread_end_guaranteed": bolt_candidate.full_form_thread_end_guaranteed,
            "receiving_measurement_required": bolt_candidate.receiving_measurement_required,
            "provisional_length_passes": length.passes,
            "provisional_length_margin_mm": round(length.length_margin_mm, 6),
            "provisional_nut_on_catalog_thread_interval": length.nut_on_usable_thread,
            "bore": bore_reports[name],
            "washer_support": {
                side: {
                    "fraction": round(seat.support_fraction, 6),
                    "full_seat": seat.full_seat,
                }
                for side, seat in seats.items()
            },
            "installed_hits": installed_hits,
            "operation_hits": operations,
        }
    cleat_origin = cleat_member.origin_x_t_n_mm
    cleat_size = cleat_member.size_x_t_n_mm
    assert cleat_origin is not None and cleat_size is not None
    cleat_n0, cleat_n1 = cleat_origin[2], cleat_origin[2] + cleat_size[2]
    rail_stacks = [
        stack for stack in config.stacks if stack.interface_id == "rail_to_cleat"
    ]
    principal_stacks = [
        stack for stack in config.stacks if stack.interface_id == "principal_to_cleat"
    ]
    rail_stacks.sort(key=lambda stack: stack.axis_point_basis_mm[0])
    principal_stacks.sort(key=lambda stack: stack.axis_point_basis_mm[2])
    if len(rail_stacks) != 2 or len(principal_stacks) != 2:
        raise ValueError("WJ-04 report requires two configured bolts per interface")
    rail_1, rail_2 = rail_stacks
    principal_1, principal_2 = principal_stacks
    bolt_diameter = config.stack_by_id(rail_1.stack_id).cad_envelope.shaft_diameter_mm
    four_d = 4 * bolt_diameter
    seven_d = 7 * bolt_diameter
    rail_axis_1 = rail_1.axis_point_basis_mm
    rail_axis_2 = rail_2.axis_point_basis_mm
    principal_axis_1 = principal_1.axis_point_basis_mm
    principal_axis_2 = principal_2.axis_point_basis_mm
    cleat_x_far = cleat_origin[0] + cleat_size[0]
    cleat_t_far = cleat_origin[1] + cleat_size[1]
    cleat_n_from_rail_front = [
        cleat_n0 - config.source_bounds.rail_n_min_mm,
        cleat_n1 - config.source_bounds.rail_n_min_mm,
    ]
    neighbor_t_min = _extent(wood[NEIGHBOR], t_axis)[0]
    rail_tool_gaps = {}
    for configured_stack in rail_stacks:
        stack = stacks[configured_stack.stack_id]
        tip_t = (
            stack.under_head_origin
            + stack.direction * stack.hardware.under_head_length_mm
        ).dot(t_axis)
        for tool_length in config.diagnostic_tool_widths_mm:
            gap = neighbor_t_min - (
                tip_t
                - stack.hardware.washer_thickness_mm
                + 2.0
                + tool_length
                + CONTACT_PROBE_MM
            )
            rail_tool_gaps[f"{configured_stack.stack_id}_{tool_length:g}mm"] = round(
                gap, 6
            )
    first_rail_tool_length = config.diagnostic_tool_widths_mm[0]
    first_rail_gap = rail_tool_gaps[f"{rail_1.stack_id}_{first_rail_tool_length:g}mm"]
    envelope = {
        "cleat_n_from_rail_front_mm": [
            round(value, 6) for value in cleat_n_from_rail_front
        ],
        "ordinary_limit_mm": ORDINARY_REAR_ENVELOPE_MM,
        "wood_body_excess_mm": round(max(0.0, cleat_n1 - rail_n1), 6),
        "temporary_rearward_nut_exit_excess_mm": round(
            rail_axis_1[2]
            + NUT_REMOVAL_REARWARD_TRAVEL_MM
            + stacks[rail_1.stack_id].hardware.nut_diameter_mm / 2
            - rail_n1,
            6,
        ),
        "rail_tool_gaps_to_upper_rail_mm": rail_tool_gaps,
        f"nominal_{first_rail_tool_length:g}mm_unthread_tool_gap_to_upper_rail_mm": first_rail_gap,
    }
    for tool_length in config.diagnostic_tool_widths_mm[1:]:
        envelope[f"nominal_{tool_length:g}mm_unthread_tool_gap_to_upper_rail_mm"] = (
            rail_tool_gaps[f"{rail_1.stack_id}_{tool_length:g}mm"]
        )
    rail_member_grain = rail_member.grain_axis
    principal_member_grain = principal_member.grain_axis
    cleat_member_grain = cleat_member.grain_axis
    rail_axis_direction = rail_1.axis_direction_basis
    principal_axis_direction = principal_1.axis_direction_basis
    axis_labels = ("X", "T", "N")
    rail_axis_label = axis_labels[
        max(range(3), key=lambda i: abs(rail_axis_direction[i]))
    ]
    principal_axis_label = axis_labels[
        max(range(3), key=lambda i: abs(principal_axis_direction[i]))
    ]
    cleat_t_edges = (
        principal_axis_1[1] - cleat_origin[1],
        cleat_t_far - principal_axis_1[1],
    )
    candidate_ids = trial_adapter_metadata(config)["catalog_candidate_ids"]
    rail_candidate = rail_1.hardware_candidate
    return {
        "schema": "wood_joint_wj04_probe/v1",
        "candidate": config.development_candidate_id,
        "preserved_selected_candidate_id": config.preserved_selected_candidate_id,
        "station": config.station_id,
        "status": "reject_protected_wire_clash"
        if cleat_hits["protected"]
        else "diagnostic_revise",
        "trial_id": config.trial_id,
        "trial_config_sha256": config.canonical_sha256,
        "rail_nominal_partial_thread_bolt_length_mm": rail_candidate.nominal_length_mm,
        "source_commit": config.source_commit,
        "source_inventory_sha256": binding.inventory_sha256,
        "producer_sha256": _sha(Path(__file__)),
        "producer_command": "uv run python -m scripts.wood_joint_wj04_probe --write",
        "dependency_sha256": {
            name: _sha(ROOT / name)
            for name in (
                "docs/panel-insert-reference.json",
                "mini_moonboard/base_frame.py",
                "mini_moonboard/floor_flush_width.py",
                "mini_moonboard/insert_frame.py",
                "mini_moonboard/panel_grid.py",
                "mini_moonboard/panel_grid_v2.py",
                "mini_moonboard/wood_joint_panel_machining.py",
                "mini_moonboard/wood_joint_frame.py",
                "mini_moonboard/wood_joint_geometry.py",
                "mini_moonboard/wood_joint_wj04_config.py",
                "scripts/owner_layout_protected.py",
                "scripts/wood_joint_clearance.py",
            )
        },
        "catalog_candidate_ids": candidate_ids,
        "source_faces": {
            "rail_rear": rail_member.source_face_ids[-1],
            "principal_rear": principal_member.source_face_ids[-1],
            "rail_t_end": rail_member.source_face_ids[0],
            "principal_x_end": principal_member.source_face_ids[0],
        },
        "panel_obstacles": geometry.panel_machining,
        "stock": {
            **trial_adapter_metadata(config)["stock"],
            "purchase_approved": config.purchase_approved,
        },
        "comparison_diagnostic": {
            "earlier_t_mm": 50.8,
            "earlier_rail_x_from_butt_mm": [44.45, 69.85],
            "earlier_rail_bolt_length_mm": 101.6,
            "earlier_40mm_dynamic_tool_gap_mm": 3.652,
            "earlier_50mm_dynamic_tool_upper_rail_collision": True,
            "earlier_generic_50mm_nut_removal_upper_rail_collision": True,
            "earlier_status": "diagnostic_revise",
            "scope": "preserved historical comparison; not regenerated from canonical WJ-04 trial",
        },
        "source_datum": {
            "rail_x_end_mm": round(config.source_bounds.rail_x_butt_x_mm, 6),
            "rail_t_mm": [round(rail_t0, 6), round(rail_t1, 6)],
            "rail_n_mm": [round(rail_n0, 6), round(rail_n1, 6)],
        },
        "contact_area_mm2": {
            key: round(value, 6) for key, value in geometry.contact_area_mm2.items()
        },
        "envelope": envelope,
        "conditional_1_4in_placement_mm": {
            "bolt_diameter_mm": bolt_diameter,
            "conditional_4d_mm": four_d,
            "conditional_7d_mm": seven_d,
            "rail_group": {
                "bolt_axis": rail_axis_label,
                "rail_grain": rail_member_grain,
                "cleat_grain": cleat_member_grain,
                "rail_end_along_grain_first": round(
                    rail_axis_1[0] - config.source_bounds.rail_x_butt_x_mm, 6
                ),
                "rail_end_minus_conditional_7d": round(
                    rail_axis_1[0] - config.source_bounds.rail_x_butt_x_mm - seven_d, 6
                ),
                "rail_bolt_pitch_along_x": round(rail_axis_2[0] - rail_axis_1[0], 6),
                "pitch_minus_conditional_4d": round(
                    rail_axis_2[0] - rail_axis_1[0] - four_d, 6
                ),
                "cleat_x_lateral_far_edge_second": round(
                    cleat_x_far - rail_axis_2[0], 6
                ),
                "cleat_x_edge_minus_conditional_4d": round(
                    cleat_x_far - rail_axis_2[0] - four_d, 6
                ),
                "rail_n_lateral_front_edge": round(rail_axis_1[2] - rail_n0, 6),
                "rail_n_lateral_rear_edge": round(rail_n1 - rail_axis_1[2], 6),
                "cleat_n_grain_front_end": round(principal_axis_1[2] - cleat_n0, 6),
                "cleat_n_grain_rear_end": round(cleat_n1 - principal_axis_2[2], 6),
                "t_dimension_is_bolt_bearing_length_not_lateral_edge": True,
            },
            "principal_group": {
                "bolt_axis": principal_axis_label,
                "principal_grain": principal_member_grain,
                "cleat_grain": cleat_member_grain,
                "cleat_t_lateral_edge_each": round(min(cleat_t_edges), 6),
                "cleat_t_edge_minus_conditional_4d": round(
                    min(cleat_t_edges) - four_d, 6
                ),
                "cleat_n_grain_front_end_first": round(
                    principal_axis_1[2] - cleat_n0, 6
                ),
                "cleat_n_grain_rear_end_second": round(
                    cleat_n1 - principal_axis_2[2], 6
                ),
                "principal_n_lateral_rear_edge_second": round(
                    rail_n1 - principal_axis_2[2], 6
                ),
            },
            "signed_load_and_applicable_2024_nds_classification_complete": False,
        },
        "cleat_hits": cleat_hits,
        "stacks": stacks_out,
        "limits": [
            "K.L. Jack bolts, candidate washers, and nuts supply catalog geometry envelopes only; no strength, delivered shank, full-form thread end, or nut engagement is accepted.",
            "Cleat uses configured 2x6 dimensional lead and rip; purchase, grade after rip, delivered dimensions, defects, kerf, and yield remain unverified.",
            "Four WJ-03 outer legacy angle stations are removed from this local protected inventory, while replacement outer-node geometry remains absent; this is not an integrated clash pass.",
            "Retained upper-rail SDS and connector geometry remain in this local screen until their own duties are replaced.",
            "Tool and reverse-order access are nominal diagnostics; delivered tolerances and physical fit remain unverified.",
            "No wood, bolt-group, washer-bearing, internal-cleat, or same-case mechanics acceptance.",
        ],
        "purchase_approved": config.purchase_approved,
        "drilling_released": config.drilling_released,
        "fabrication_released": config.fabrication_released,
        "structural_released": config.structural_released,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = report()
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write:
        OUTPUT.write_text(serialized)
    else:
        print(serialized)


if __name__ == "__main__":
    main()
