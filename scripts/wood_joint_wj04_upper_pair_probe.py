"""Source-bound paired WJ-04 full-stock hypothesis screen.

The lower and upper station blocks are a new-build geometry hypothesis. This
module does not change canonical WJ-04 configuration, old-stock holes,
hardware selection, load paths, or release status.
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

from mini_moonboard.wood_joint_frame import (
    bolt_axis_stroke_shapes,
)
from mini_moonboard.wood_joint_geometry import (
    BoltStack,
    StackLayer,
    WasherSeat,
)
from mini_moonboard.wood_joint_panel_machining import candidate_panel_replacements
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_full_stock_probe as lower_probe
from scripts import wood_joint_wj04_probe as base_probe
from scripts import wood_joint_wj04_tool_access as tool_access

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = "docs/wood-joints-mvp/source-inventory.json"
LOWER_STATION = "clip_horizontal_lower_right_1"
UPPER_STATION = "clip_horizontal_upper_right_1"
LOWER_CLEAT = "wj04_lower_full_stock_cleat"
UPPER_CLEAT = "wj04_upper_full_stock_cleat"
CLEAT_SIZE_MM = (88.9, 88.9, 119.7)
LOWER_CLEAT_ORIGIN_MM = (89.05, 1353.874134, 229.840968)
UPPER_CLEAT_ORIGIN_MM = (89.05, 1497.924134, 229.840968)
RAIL_BOLT_X_MM = 134.5
RAIL_BOLT_N_MM = (273.190968, 306.190968)
PRINCIPAL_BOLT_X_MM = 177.95
PRINCIPAL_BOLT_N_MM = 289.690968
LOWER_PRINCIPAL_BOLT_T_MM = (1381.874134, 1414.874134)
UPPER_PRINCIPAL_BOLT_T_MM = (1525.924134, 1558.924134)
LOWER_RAIL_HEAD_T_MM = round(LOWER_CLEAT_ORIGIN_MM[1] + CLEAT_SIZE_MM[1], 6)
UPPER_RAIL_HEAD_T_MM = round(UPPER_CLEAT_ORIGIN_MM[1] + CLEAT_SIZE_MM[1], 6)
HIT_TOLERANCE_MM3 = 1e-6
CONTACT_PROBE_MM = 0.1
SCHEMA = "wood_joint_wj04_upper_pair_probe/v1"

SOURCE_INPUTS = (
    INVENTORY,
    "docs/wood-joints-mvp/stock-and-cut-basis.md",
    "docs/wood-joints-mvp/ordinary-hardware-basis.md",
    "docs/wood-joints-mvp/wood-limit-state-basis.md",
    "docs/wood-joints-mvp/hypotheses/wj04-full-stock-stagger-probe.json",
    "mini_moonboard/base_frame.py",
    "mini_moonboard/floor_flush_width.py",
    "mini_moonboard/insert_frame.py",
    "mini_moonboard/panel_grid_v2.py",
    "mini_moonboard/wood_joint_frame.py",
    "mini_moonboard/wood_joint_geometry.py",
    "mini_moonboard/wood_joint_panel_machining.py",
    "mini_moonboard/wood_joint_wj04_config.py",
    "scripts/owner_layout_protected.py",
    "scripts/wood_joint_clearance.py",
    "scripts/wood_joint_wj04_probe.py",
    "scripts/wood_joint_wj04_tool_access.py",
    "scripts/wood_joint_wj04_full_stock_probe.py",
)


@dataclass(frozen=True)
class StackSpec:
    stack_id: str
    station_id: str
    cleat_id: str
    interface_id: str
    axis_point_basis_mm: tuple[float, float, float]
    axis_direction_basis: tuple[float, float, float]
    layers: tuple[tuple[str, float], tuple[str, float]]


def _station_specs(
    station_id: str,
    cleat_id: str,
    host_rail_id: str,
    head_t_mm: float,
    principal_t_mm: tuple[float, float],
    stack_prefix: str,
) -> tuple[StackSpec, ...]:
    return (
        StackSpec(
            f"{stack_prefix}_rail_1",
            station_id,
            cleat_id,
            "rail_to_cleat",
            (RAIL_BOLT_X_MM, head_t_mm, RAIL_BOLT_N_MM[0]),
            (0.0, -1.0, 0.0),
            ((cleat_id, 88.9), (host_rail_id, 38.1)),
        ),
        StackSpec(
            f"{stack_prefix}_rail_2",
            station_id,
            cleat_id,
            "rail_to_cleat",
            (RAIL_BOLT_X_MM, head_t_mm, RAIL_BOLT_N_MM[1]),
            (0.0, -1.0, 0.0),
            ((cleat_id, 88.9), (host_rail_id, 38.1)),
        ),
        StackSpec(
            f"{stack_prefix}_principal_1",
            station_id,
            cleat_id,
            "principal_to_cleat",
            (PRINCIPAL_BOLT_X_MM, principal_t_mm[0], PRINCIPAL_BOLT_N_MM),
            (-1.0, 0.0, 0.0),
            ((cleat_id, 88.9), ("base_principal_center_right", 38.1)),
        ),
        StackSpec(
            f"{stack_prefix}_principal_2",
            station_id,
            cleat_id,
            "principal_to_cleat",
            (PRINCIPAL_BOLT_X_MM, principal_t_mm[1], PRINCIPAL_BOLT_N_MM),
            (-1.0, 0.0, 0.0),
            ((cleat_id, 88.9), ("base_principal_center_right", 38.1)),
        ),
    )


STACK_SPECS = (
    *_station_specs(
        LOWER_STATION,
        LOWER_CLEAT,
        "base_rail_service_lower_right",
        LOWER_RAIL_HEAD_T_MM,
        LOWER_PRINCIPAL_BOLT_T_MM,
        "lower",
    ),
    *_station_specs(
        UPPER_STATION,
        UPPER_CLEAT,
        "base_rail_service_upper_right",
        UPPER_RAIL_HEAD_T_MM,
        UPPER_PRINCIPAL_BOLT_T_MM,
        "upper",
    ),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_snapshot() -> dict[str, str]:
    return {path: _sha256(ROOT / path) for path in SOURCE_INPUTS}


def _inventory() -> dict[str, Any]:
    result = json.loads((ROOT / INVENTORY).read_text())
    if _sha256(ROOT / INVENTORY) != WJ04_TRIAL.source_inventory_sha256:
        raise ValueError("live source inventory differs from the canonical WJ-04 pin")
    return result


def _selected_duties(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected = {LOWER_STATION, UPPER_STATION}
    rows = {
        row["legacy_station_id"]: row
        for row in inventory["legacy_duties"]
        if row["legacy_station_id"] in expected
    }
    if set(rows) != expected:
        raise ValueError(
            "paired probe requires both exact lower and upper source duties"
        )
    for station_id, row in rows.items():
        if len(row["legacy_sds_axes"]) != 6:
            raise ValueError(f"{station_id}: expected six replaced SDS axes")
        if len({axis["axis_id"] for axis in row["legacy_sds_axes"]}) != 6:
            raise ValueError(f"{station_id}: SDS axis IDs must be unique")
    if rows[LOWER_STATION]["legacy_host_members"] != [
        "base_rail_service_lower_right",
        "base_principal_center_right",
    ]:
        raise ValueError("lower duty source hosts changed")
    if rows[UPPER_STATION]["legacy_host_members"] != [
        "base_rail_service_upper_right",
        "base_principal_center_right",
    ]:
        raise ValueError("upper duty source hosts changed")
    ids = [axis["axis_id"] for row in rows.values() for axis in row["legacy_sds_axes"]]
    if len(ids) != len(set(ids)):
        raise ValueError("lower and upper replaced SDS axis IDs overlap")
    return rows


def _axis_to_basis(axis: dict[str, Any]) -> dict[str, Any]:
    frame = WJ04_TRIAL.frame
    point = cq.Vector(*axis["origin_global_xyz_mm"])
    direction = cq.Vector(*axis["axis_global_xyz"]).normalized()
    basis_point = (
        point.dot(cq.Vector(frame.x_global)),
        point.dot(cq.Vector(frame.t_global)),
        point.dot(cq.Vector(frame.n_global)),
    )
    basis_direction = (
        direction.dot(cq.Vector(frame.x_global)),
        direction.dot(cq.Vector(frame.t_global)),
        direction.dot(cq.Vector(frame.n_global)),
    )
    return {
        "axis_id": axis["axis_id"],
        "origin_x_t_n_mm": [round(value, 6) for value in basis_point],
        "direction_x_t_n": [round(value, 9) for value in basis_direction],
        "source_occupied_length_mm": axis["source_occupied_length_mm"],
    }


def build_stacks(
    stack_specs: tuple[StackSpec, ...] = STACK_SPECS,
) -> dict[str, BoltStack]:
    """Build eight provisional stacks; do not mutate canonical WJ-04 config."""
    expected_ids = {spec.stack_id for spec in STACK_SPECS}
    ids = [spec.stack_id for spec in stack_specs]
    if len(ids) != 8 or len(set(ids)) != 8 or set(ids) != expected_ids:
        raise ValueError("paired hypothesis must define its eight unique stacks")
    for station_id, prefix in ((LOWER_STATION, "lower"), (UPPER_STATION, "upper")):
        station_specs = [spec for spec in stack_specs if spec.station_id == station_id]
        if len(station_specs) != 4:
            raise ValueError(f"{station_id}: paired hypothesis needs four stacks")
        if sum(spec.interface_id == "rail_to_cleat" for spec in station_specs) != 2:
            raise ValueError(f"{station_id}: paired hypothesis needs two rail stacks")
        if (
            sum(spec.interface_id == "principal_to_cleat" for spec in station_specs)
            != 2
        ):
            raise ValueError(
                f"{station_id}: paired hypothesis needs two principal stacks"
            )
        if any(not spec.stack_id.startswith(f"{prefix}_") for spec in station_specs):
            raise ValueError(f"{station_id}: stack IDs must retain station prefix")

    expected_layers = {
        "rail_to_cleat": (88.9, 38.1),
        "principal_to_cleat": (88.9, 38.1),
    }
    expected_specs = {spec.stack_id: spec for spec in STACK_SPECS}
    template = lower_probe.build_stacks()["rail_1"]
    hardware = template.hardware
    result = {}
    for spec in stack_specs:
        if spec.interface_id not in expected_layers:
            raise ValueError(f"{spec.stack_id}: unknown interface")
        if (
            tuple(layer[1] for layer in spec.layers)
            != expected_layers[spec.interface_id]
        ):
            raise ValueError(f"{spec.stack_id}: expected 88.9 + 38.1 mm wood layers")
        if spec.layers[0][0] != spec.cleat_id:
            raise ValueError(
                f"{spec.stack_id}: head-side layer must be its station cleat"
            )
        if not math.isclose(sum(layer[1] for layer in spec.layers), 127.0):
            raise ValueError(f"{spec.stack_id}: expected 127 mm nominal grip")
        if spec != expected_specs[spec.stack_id]:
            raise ValueError(
                f"{spec.stack_id}: axis or member mapping differs from pinned proposal"
            )
        direction = cq.Vector(
            *WJ04_TRIAL.frame.vector_to_global(spec.axis_direction_basis)
        ).normalized()
        center = cq.Vector(*WJ04_TRIAL.frame.to_global(spec.axis_point_basis_mm))
        layers = tuple(StackLayer(name, thickness) for name, thickness in spec.layers)
        under_head = center - direction * hardware.washer_thickness_mm
        nut_center = center + direction * 127.0
        result[spec.stack_id] = BoltStack(
            id=spec.stack_id,
            hardware=hardware,
            under_head_origin=under_head,
            direction=direction,
            layers=layers,
            head_seat=WasherSeat(layers[0].body_id, center, direction),
            nut_seat=WasherSeat(layers[-1].body_id, nut_center, -direction),
            required_tip_projection_mm=template.required_tip_projection_mm,
        )
    return result


def trial_plan() -> dict[str, Any]:
    """Return axis/source plan without loading or cutting CAD solids."""
    inventory = _inventory()
    duties = _selected_duties(inventory)
    stacks = build_stacks()
    screw_count = len(inventory["fixed_panel_kicker_screws"])
    bolt_count = len(inventory["starting_frame_bolts"])
    if screw_count != 66 or bolt_count != 12:
        raise ValueError(
            "paired hypothesis must preserve exactly 66 screws and 12 bolts"
        )
    return {
        "schema": SCHEMA,
        "trial_id": "full_x88p9_lower_upper_pair_hypothesis",
        "status": "unaccepted_geometry_hypothesis",
        "source_inventory_sha256": _sha256(ROOT / INVENTORY),
        "canonical_wj04_config_sha256": WJ04_TRIAL.canonical_sha256,
        "source_candidate_id": WJ04_TRIAL.preserved_selected_candidate_id,
        "source_variant": WJ04_TRIAL.source_variant,
        "source_inputs_sha256": _source_snapshot(),
        "stations": {
            LOWER_STATION: {
                "cleat_origin_x_t_n_mm": list(LOWER_CLEAT_ORIGIN_MM),
                "cleat_size_x_t_n_mm": list(CLEAT_SIZE_MM),
                "host_members": duties[LOWER_STATION]["legacy_host_members"],
                "replaced_source_sds_axes": [
                    _axis_to_basis(axis)
                    for axis in duties[LOWER_STATION]["legacy_sds_axes"]
                ],
            },
            UPPER_STATION: {
                "cleat_origin_x_t_n_mm": list(UPPER_CLEAT_ORIGIN_MM),
                "cleat_size_x_t_n_mm": list(CLEAT_SIZE_MM),
                "host_members": duties[UPPER_STATION]["legacy_host_members"],
                "replaced_source_sds_axes": [
                    _axis_to_basis(axis)
                    for axis in duties[UPPER_STATION]["legacy_sds_axes"]
                ],
            },
        },
        "pair_spacing": {
            "lower_block_t_interval_mm": [
                LOWER_CLEAT_ORIGIN_MM[1],
                LOWER_CLEAT_ORIGIN_MM[1] + CLEAT_SIZE_MM[1],
            ],
            "upper_block_t_interval_mm": [
                UPPER_CLEAT_ORIGIN_MM[1],
                UPPER_CLEAT_ORIGIN_MM[1] + CLEAT_SIZE_MM[1],
            ],
            "nominal_clear_gap_mm": round(
                UPPER_CLEAT_ORIGIN_MM[1] - LOWER_CLEAT_ORIGIN_MM[1] - CLEAT_SIZE_MM[1],
                6,
            ),
            "cleat_pair_interference_screened": False,
        },
        "stacks": [
            {
                "stack_id": spec.stack_id,
                "station_id": spec.station_id,
                "interface_id": spec.interface_id,
                "axis_point_basis_mm": list(spec.axis_point_basis_mm),
                "axis_direction_basis": list(spec.axis_direction_basis),
                "layers_head_to_nut": [
                    {"member_id": name, "thickness_mm": thickness}
                    for name, thickness in spec.layers
                ],
                "grip_mm": round(stacks[spec.stack_id].grip_mm, 6),
                "bolt_sku": stacks[spec.stack_id].hardware.candidate_sku,
                "bolt_status": "provisional model candidate; delivery measurement required",
            }
            for spec in STACK_SPECS
        ],
        "fixed_obligations": {
            "panel_kicker_screw_axes": screw_count,
            "starting_frame_bolts": bolt_count,
            "preservation_required": True,
            "cad_environment_materialized": False,
        },
        "candidate_panel_overlay": {
            "planned_for_local_geometry_map": True,
            "applied_to_local_geometry_map": False,
            "panel_helper_sha256": _sha256(
                ROOT / "mini_moonboard/wood_joint_panel_machining.py"
            ),
            "raw_source_binding_mutated": False,
            "baseline_overlay_not_integrated_into_canonical_wj04": True,
        },
        "claim_boundary": {
            "selected_station_count": 2,
            "former_duty_count": 2,
            "former_sds_axis_count": 12,
            "accepted_replacement_count": 0,
            "physical_replacement_accepted": False,
            "structural_accepted": False,
            "purchase_approved": False,
            "drilling_released": False,
            "fabrication_released": False,
            "capacity_established": False,
        },
    }


def _axis_ids(duties: dict[str, dict[str, Any]]) -> set[str]:
    return {
        axis["axis_id"] for row in duties.values() for axis in row["legacy_sds_axes"]
    }


def _rebuild_hosts_with_removed_stations(
    source: Any,
    inventory: dict[str, Any],
    removed_axis_ids: set[str],
) -> dict[str, cq.Shape]:
    """Rebuild three hosts, restoring only both selected duties' SDS openings.

    Reapply every other named axis, service cut, machining cut, and purchased
    panel screw opening after restoration so crossing retained openings remain
    open. This mirrors the canonical materializer's source-cut policy.
    """
    removed_axes = {
        axis["axis_id"]: axis
        for duty in inventory["legacy_duties"]
        for axis in duty["legacy_sds_axes"]
        if axis["axis_id"] in removed_axis_ids
    }
    if set(removed_axes) != removed_axis_ids:
        raise ValueError("one or more selected removed axes are missing from inventory")
    if any(
        axis.get("shop_opening_kind") != "sds_wood" for axis in removed_axes.values()
    ):
        raise ValueError("only selected former SDS openings may be restored")

    hosts = {
        "base_rail_service_lower_right",
        "base_rail_service_upper_right",
        "base_principal_center_right",
    }
    uncut = {part.name: part.shape for part in source.uncut_wood_parts()}
    source_parts = {
        part.name: part.shape for part in source.parts() if part.name in uncut
    }
    connections = tuple(source.connections())
    by_name = {connection.name: connection for connection in connections}
    missing_connections = removed_axis_ids - by_name.keys()
    if missing_connections:
        raise ValueError(
            f"removed axes missing source connections: {sorted(missing_connections)}"
        )

    rebuilt = {}
    for host_id in sorted(hosts):
        finished = source_parts[host_id]
        raw_host = uncut[host_id]
        for axis_id in sorted(removed_axis_ids):
            connection = by_name[axis_id]
            if host_id not in connection.members:
                continue
            direction = connection.direction.normalized()
            opening = cq.Solid.makeCylinder(
                connection.diameter / 2,
                connection.length + 2.0,
                connection.start - direction,
                direction,
            )
            finished = finished.fuse(opening.intersect(raw_host)).clean()

        for connection in connections:
            if host_id not in connection.members or connection.name in removed_axis_ids:
                continue
            direction = connection.direction.normalized()
            diameter = (
                source.bolt_dimensions(connection)["hole_diameter_mm"]
                if connection.kind == "bolt"
                else connection.diameter
            )
            opening = cq.Solid.makeCylinder(
                diameter / 2,
                connection.length + 2.0,
                connection.start - direction,
                direction,
            )
            finished = finished.cut(opening).clean()

        for member_id, _, cutter in source.service_cutters():
            if member_id == host_id:
                finished = finished.cut(cutter).clean()
        for member_id, _, _, cutter in source.additional_machining_cutters():
            if member_id == host_id:
                finished = finished.cut(cutter).clean()
        for row in inventory["fixed_panel_kicker_screws"]:
            connection = by_name[row["axis_id"]]
            if host_id not in connection.members:
                continue
            opening = cq.Solid.makeCylinder(
                connection.diameter / 2,
                row["shop_purchased_length_mm"],
                connection.start,
                connection.direction.normalized(),
            )
            finished = finished.cut(opening).clean()
        rebuilt[host_id] = finished
    return rebuilt


@dataclass(frozen=True)
class PairGeometry:
    base: Any
    parts: dict[str, cq.Shape]
    finished: dict[str, cq.Shape]
    stacks: dict[str, BoltStack]
    bores: dict[str, cq.Shape]
    installed: dict[str, dict[str, cq.Shape]]
    all_wood: dict[str, cq.Shape]
    panels: dict[str, cq.Shape]
    protected: dict[str, cq.Shape]
    bore_reports: dict[str, dict[str, Any]]
    cleat_hits: dict[str, dict[str, dict[str, float]]]
    contact_area_mm2: dict[str, dict[str, float]]
    removed_axis_ids: set[str]
    panel_overlay_names: tuple[str, ...]


def materialize_pair_geometry(base_geometry: Any | None = None) -> PairGeometry:
    """Build two full cleats and eight provisional stacks on fresh local shapes."""
    if base_geometry is None:
        base_geometry = base_probe.materialize_trial_geometry(WJ04_TRIAL)
    if base_geometry.config.canonical_sha256 != WJ04_TRIAL.canonical_sha256:
        raise ValueError("pair requires unchanged canonical WJ-04 source configuration")
    if (
        base_geometry.source_binding.inventory_sha256
        != WJ04_TRIAL.source_inventory_sha256
    ):
        raise ValueError("pair source inventory differs from the canonical WJ-04 pin")

    inventory = _inventory()
    duties = _selected_duties(inventory)
    removed_axis_ids = _axis_ids(duties)
    hosts = _rebuild_hosts_with_removed_stations(
        base_geometry.source, inventory, removed_axis_ids
    )
    # The lower host reconstruction must match the already audited WJ-04
    # materializer before extending its exact retained-cut policy upward.
    lower_rail_delta = abs(
        hosts["base_rail_service_lower_right"].Volume()
        - base_geometry.parts["base_rail_service_lower_right"].Volume()
    )
    if lower_rail_delta > 1e-5:
        raise ValueError("paired source reconstruction disagrees with lower WJ-04 host")

    panel_parts = candidate_panel_replacements(
        base_geometry.source,
        current_parts=base_geometry.source.parts(),
        uncut_parts=base_geometry.source.uncut_wood_parts(),
    )
    panels = dict(base_geometry.panels)
    panels.update({name: part.shape for name, part in panel_parts.items()})
    protected = {
        name: shape
        for name, shape in base_geometry.protected.items()
        if LOWER_STATION not in name and UPPER_STATION not in name
    }
    all_wood = dict(base_geometry.all_wood)
    all_wood.update(hosts)

    parts: dict[str, cq.Shape] = dict(hosts)
    parts[LOWER_CLEAT] = base_probe._box_in_trial_frame(
        WJ04_TRIAL, LOWER_CLEAT_ORIGIN_MM, CLEAT_SIZE_MM
    )
    parts[UPPER_CLEAT] = base_probe._box_in_trial_frame(
        WJ04_TRIAL, UPPER_CLEAT_ORIGIN_MM, CLEAT_SIZE_MM
    )
    stacks = build_stacks()
    x_axis, t_axis, _n_axis = base_probe._frame_axes(WJ04_TRIAL)

    bores: dict[str, cq.Shape] = {}
    bore_reports: dict[str, dict[str, Any]] = {}
    for stack_id, stack in stacks.items():
        direction = stack.direction.normalized()
        bore = cq.Solid.makeCylinder(
            stack.hardware.drill_diameter_mm / 2,
            stack.grip_mm + 2 * CONTACT_PROBE_MM,
            stack.head_seat.center - direction * CONTACT_PROBE_MM,
            direction,
        )
        bores[stack_id] = bore
        progress = 0.0
        fractions = {}
        for layer in stack.layers:
            segment = cq.Solid.makeCylinder(
                stack.hardware.drill_diameter_mm / 2,
                layer.thickness_mm,
                stack.head_seat.center + direction * progress,
                direction,
            )
            fractions[layer.body_id] = round(
                base_probe._intersect_volume(segment, parts[layer.body_id])
                / segment.Volume(),
                6,
            )
            progress += layer.thickness_mm
        own_ids = {layer.body_id for layer in stack.layers}
        bore_reports[stack_id] = {
            "layer_material_fractions_before_cut": fractions,
            "other_wood_hits_mm3": base_probe._hits(
                bore,
                {
                    name: shape
                    for name, shape in all_wood.items()
                    if name not in own_ids
                },
            ),
            "panel_hits_mm3": base_probe._hits(bore, panels),
            "protected_hits_mm3": base_probe._hits(bore, protected),
        }

    for first_id, first in bores.items():
        for second_id, second in bores.items():
            if first_id >= second_id:
                continue
            if base_probe._intersect_volume(first, second) > HIT_TOLERANCE_MM3:
                raise ValueError(f"candidate bores overlap: {first_id}, {second_id}")

    finished = {}
    for part_id, shape in parts.items():
        cuts = [
            bores[stack_id]
            for stack_id, stack in stacks.items()
            if any(layer.body_id == part_id for layer in stack.layers)
            and base_probe._intersect_volume(shape, bores[stack_id]) > HIT_TOLERANCE_MM3
        ]
        finished[part_id] = shape.cut(*cuts).clean() if cuts else shape
    installed = {
        stack_id: dict(stack.installed_shapes()) for stack_id, stack in stacks.items()
    }

    cleat_hits = {}
    contact_area = {}
    for station_id, cleat_id, rail_id in (
        (LOWER_STATION, LOWER_CLEAT, "base_rail_service_lower_right"),
        (UPPER_STATION, UPPER_CLEAT, "base_rail_service_upper_right"),
    ):
        cleat = parts[cleat_id]
        principal_id = "base_principal_center_right"
        cleat_hits[station_id] = {
            "hosts": base_probe._hits(
                cleat, {rail_id: parts[rail_id], principal_id: parts[principal_id]}
            ),
            "other_wood": base_probe._hits(
                cleat,
                {
                    name: shape
                    for name, shape in all_wood.items()
                    if name not in (rail_id, principal_id)
                },
            ),
            "panels": base_probe._hits(cleat, panels),
            "protected": base_probe._hits(cleat, protected),
            "other_cleat": base_probe._hits(
                cleat,
                {
                    UPPER_CLEAT if cleat_id == LOWER_CLEAT else LOWER_CLEAT: parts[
                        UPPER_CLEAT if cleat_id == LOWER_CLEAT else LOWER_CLEAT
                    ]
                },
            ),
        }
        contact_area[station_id] = {
            "rail_to_cleat": round(
                cleat.translate(-t_axis * CONTACT_PROBE_MM)
                .intersect(parts[rail_id])
                .Volume()
                / CONTACT_PROBE_MM,
                6,
            ),
            "principal_to_cleat": round(
                cleat.translate(-x_axis * CONTACT_PROBE_MM)
                .intersect(parts[principal_id])
                .Volume()
                / CONTACT_PROBE_MM,
                6,
            ),
        }
    return PairGeometry(
        base=base_geometry,
        parts=parts,
        finished=finished,
        stacks=stacks,
        bores=bores,
        installed=installed,
        all_wood=all_wood,
        panels=panels,
        protected=protected,
        bore_reports=bore_reports,
        cleat_hits=cleat_hits,
        contact_area_mm2=contact_area,
        removed_axis_ids=removed_axis_ids,
        panel_overlay_names=tuple(sorted(panel_parts)),
    )


def _named(shapes: dict[str, cq.Shape], prefix: str) -> dict[str, cq.Shape]:
    return {f"{prefix}/{name}": shape for name, shape in shapes.items()}


def _hit_map(
    candidate: cq.Shape,
    obstacles: dict[str, cq.Shape],
    *,
    excluded: set[str] | None = None,
) -> dict[str, float]:
    excluded = excluded or set()
    return {
        name: round(volume, 6)
        for name, shape in obstacles.items()
        if name not in excluded
        and (volume := base_probe._intersect_volume(candidate, shape))
        > HIT_TOLERANCE_MM3
    }


def _all_fixed_obstacles(geometry: PairGeometry) -> dict[str, cq.Shape]:
    other_wood = {
        name: shape
        for name, shape in geometry.all_wood.items()
        if name not in geometry.parts
    }
    wood = {**other_wood, **geometry.panels, **geometry.finished}
    return {
        **_named(wood, "wood"),
        **_named(geometry.protected, "protected"),
    }


def _assembly_blocker_graph(geometry: PairGeometry) -> dict[str, Any]:
    """Compute fixed and prior-stack blockers; bounded subset search only."""
    stack_ids = tuple(spec.stack_id for spec in STACK_SPECS)
    fixed = _all_fixed_obstacles(geometry)
    installed = {
        f"hardware/{stack_id}/{role}": shape
        for stack_id, shapes in geometry.installed.items()
        for role, shape in shapes.items()
    }
    fixed_hits: dict[str, dict[str, dict[str, float]]] = {}
    prior_hits: dict[tuple[str, str], dict[str, dict[str, float]]] = {}
    for stack_id, stack in geometry.stacks.items():
        strokes = bolt_axis_stroke_shapes(stack)
        direction = stack.direction.normalized()
        head_washer = geometry.installed[stack_id]["head_washer"]
        washer_start = head_washer.translate(
            -direction * stack.hardware.under_head_length_mm
        )
        strokes["head_washer_insertion"] = tool_access.translation_sweep(
            washer_start, direction * stack.hardware.under_head_length_mm
        )
        fixed_hits[stack_id] = {
            path: _hit_map(shape, fixed) for path, shape in strokes.items()
        }
        for prior_id in stack_ids:
            if prior_id == stack_id:
                continue
            prior_shapes = {
                name: shape
                for name, shape in installed.items()
                if name.startswith(f"hardware/{prior_id}/")
            }
            prior_hits[(stack_id, prior_id)] = {
                path: _hit_map(shape, prior_shapes) for path, shape in strokes.items()
            }

    reachable = {0: ()}
    state_expansions = 0
    for mask in range(1 << len(stack_ids)):
        if mask not in reachable:
            continue
        order = reachable[mask]
        if mask == (1 << len(stack_ids)) - 1:
            break
        for index, stack_id in enumerate(stack_ids):
            bit = 1 << index
            if mask & bit or any(fixed_hits[stack_id].values()):
                continue
            installed_before = [
                prior_id
                for prior_index, prior_id in enumerate(stack_ids)
                if mask & (1 << prior_index)
            ]
            if any(
                any(prior_hits[(stack_id, prior_id)].values())
                for prior_id in installed_before
            ):
                continue
            next_mask = mask | bit
            if next_mask not in reachable:
                reachable[next_mask] = order + (stack_id,)
                state_expansions += 1
    final_mask = (1 << len(stack_ids)) - 1
    return {
        "orders_enumerated": 0,
        "subset_states_expanded": state_expansions,
        "subset_state_limit": 256,
        "clear_order_found": final_mask in reachable,
        "one_clear_order": list(reachable.get(final_mask, ())),
        "fixed_insertion_blockers": {
            stack_id: {path: hits for path, hits in paths.items() if hits}
            for stack_id, paths in fixed_hits.items()
        },
        "prior_stack_incompatibilities": {
            f"{stack_id}_after_{prior_id}": {
                path: hits for path, hits in paths.items() if hits
            }
            for (stack_id, prior_id), paths in prior_hits.items()
            if any(paths.values())
        },
        "assembly_pose": "all source service members remain installed",
        "limitations": [
            "Search checks stack-axis straight insertion and head-washer ride-on only.",
            "No temporary removal or repositioning of service rails is modeled.",
            "A clear order would not establish field access, tightening, or acceptance.",
        ],
    }


def _stack_diagnostics(geometry: PairGeometry) -> dict[str, Any]:
    """Reuse the audited generic per-stack collision and tool screens."""
    other_wood = {
        name: shape
        for name, shape in geometry.all_wood.items()
        if name not in geometry.parts
    }
    local_base = type(
        "PairCollisionContext",
        (),
        {
            "other_wood": other_wood,
            "panels": geometry.panels,
            "protected": geometry.protected,
        },
    )()
    generic_geometry = lower_probe.FullStockGeometry(
        base_geometry=local_base,
        parts=geometry.parts,
        cleat=geometry.parts[LOWER_CLEAT],
        stacks=geometry.stacks,
        bores=geometry.bores,
        bore_reports=geometry.bore_reports,
        finished=geometry.finished,
        installed=geometry.installed,
        contact_area_mm2={},
        cleat_hits=geometry.cleat_hits[LOWER_STATION],
    )
    return lower_probe._stack_geometry_report(generic_geometry)


def report(base_geometry: Any | None = None) -> dict[str, Any]:
    """Build paired geometry diagnostics; run only in approved CAD slot."""
    before = _source_snapshot()
    plan = trial_plan()
    geometry = materialize_pair_geometry(base_geometry)
    diagnostics = _stack_diagnostics(geometry)
    assembly = _assembly_blocker_graph(geometry)
    after = _source_snapshot()
    if before != after:
        raise RuntimeError("paired WJ-04 inputs changed during probe")
    return {
        **plan,
        "pair_spacing": {
            **plan["pair_spacing"],
            "cleat_pair_interference_screened": True,
            "pair_intersection_hits_mm3": {
                station_id: geometry.cleat_hits[station_id]["other_cleat"]
                for station_id in (LOWER_STATION, UPPER_STATION)
            },
        },
        "fixed_obligations": {
            **plan["fixed_obligations"],
            "cad_environment_materialized": True,
            "preserved_in_local_environment": True,
        },
        "candidate_panel_overlay": {
            **plan["candidate_panel_overlay"],
            "applied_to_local_geometry_map": True,
            "applied_panel_ids": list(geometry.panel_overlay_names),
        },
        "producer_sha256": _sha256(Path(__file__)),
        "source_inputs_sha256": before,
        "source_binding": {
            "inventory_sha256": geometry.base.source_binding.inventory_sha256,
            "runtime_module_sha256": geometry.base.source_binding.runtime_module_sha256,
            "uncut_part_shapes_sha256": geometry.base.source_binding.uncut_part_shapes_sha256,
            "uncut_host_shape_sha256": geometry.base.source_binding.uncut_host_shape_sha256,
            "fixed_screw_axes_sha256": geometry.base.source_binding.fixed_screw_axes_sha256,
            "frame_bolt_axes_sha256": geometry.base.source_binding.frame_bolt_axes_sha256,
        },
        "materialized_geometry": {
            "source_hosts_rebuilt_with_only_two_selected_sds_duties_removed": True,
            "retained_source_openings_reapplied_after_sds_restoration": True,
            "lower_rail_reconstruction_volume_delta_mm3": round(
                abs(
                    geometry.parts["base_rail_service_lower_right"].Volume()
                    - geometry.base.parts["base_rail_service_lower_right"].Volume()
                ),
                9,
            ),
            "canonical_narrow_trial_finished_hosts_reused": False,
            "candidate_panel_overlay_names": list(geometry.panel_overlay_names),
            "raw_source_binding_mutated": False,
            "removed_legacy_axes": sorted(geometry.removed_axis_ids),
            "removed_legacy_axis_count": len(geometry.removed_axis_ids),
            "cleat_hits_mm3": geometry.cleat_hits,
            "contact_area_mm2": geometry.contact_area_mm2,
            "pair_cleat_gap_mm": round(
                UPPER_CLEAT_ORIGIN_MM[1]
                - (LOWER_CLEAT_ORIGIN_MM[1] + CLEAT_SIZE_MM[1]),
                6,
            ),
        },
        "stack_diagnostics": diagnostics,
        "assembly_blocker_graph": assembly,
        "environment_obligations": {
            "fixed_panel_kicker_screw_count": len(
                _inventory()["fixed_panel_kicker_screws"]
            ),
            "starting_frame_bolt_count": len(_inventory()["starting_frame_bolts"]),
            "all_nonselected_legacy_connector_and_sds_geometry_retained": True,
            "corrected_candidate_right_panels_used_in_local_map": True,
            "panel_overlay_right_panel_ids": list(geometry.panel_overlay_names),
        },
        "claim_boundary": {
            "accepted_replacement_count": 0,
            "physical_replacement_accepted": False,
            "structural_accepted": False,
            "purchase_approved": False,
            "drilling_released": False,
            "fabrication_released": False,
            "capacity_established": False,
        },
        "limitations": [
            "This is one paired local geometry hypothesis, not a complete WJ-06 layout or load path.",
            "The result uses the source panel overlay locally; canonical WJ-04 remains unchanged.",
            "All service members are present in insertion checks; temporary member removal and frame erection are not modeled.",
            "Signed member loads, member-specific NDS checks, material condition, and delivered hardware remain unresolved.",
            "Envelope clashes do not prove physical tool impossibility; clear envelopes do not establish access.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="print immutable axis plan without materializing CAD geometry",
    )
    args = parser.parse_args()
    result = trial_plan() if args.plan_only else report()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
