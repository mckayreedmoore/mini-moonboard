"""Source-bound diagnostic for the WJ-04 full-4x4 cleat hypothesis.

This is a separate, unaccepted geometry hypothesis. It leaves the canonical
WJ-04 trial untouched and reuses only its pinned source hosts, retained cuts,
protected inventory, and catalog envelopes. A clear model is not joint
acceptance, a hardware selection, or a release to build.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import (
    ORDINARY_REAR_ENVELOPE_MM,
    access_shapes,
    bolt_axis_stroke_shapes,
    detached_hardware_removal_shapes,
)
from mini_moonboard.wood_joint_geometry import (
    BoltHardware,
    BoltStack,
    StackLayer,
    WasherSeat,
    washer_support_report,
)
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_probe as base_probe
from scripts import wood_joint_wj04_tool_access as tool_access

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_wj04_full_stock_probe/v1"
TRIAL_ID = "full_x88p9_ordinary_bolt_hypothesis"
CLEAT_ORIGIN_X_T_N_MM = (89.05, 1353.874134, 229.840968)
CLEAT_SIZE_X_T_N_MM = (88.9, 88.9, 119.7)
RAIL_BOLT_X_MM = 134.5
RAIL_BOLT_N_MM = (273.190968, 306.190968)
PRINCIPAL_BOLT_N_MM = 289.690968
PRINCIPAL_BOLT_T_MM = (1381.874134, 1414.874134)
BOLT_LENGTH_MM = 152.4
HIT_TOLERANCE_MM3 = 1e-6
CONTACT_PROBE_MM = 0.1
TOOL_SWEEP_DEGREES = 30.0
SOURCE_INPUTS = (
    "docs/wood-joints-mvp/source-inventory.json",
    "docs/wood-joints-mvp/stock-and-cut-basis.md",
    "docs/wood-joints-mvp/ordinary-hardware-basis.md",
    "docs/wood-joints-mvp/wood-limit-state-basis.md",
    "mini_moonboard/floor_flush_width.py",
    "mini_moonboard/wood_joint_frame.py",
    "mini_moonboard/wood_joint_geometry.py",
    "mini_moonboard/wood_joint_wj04_config.py",
    "scripts/owner_layout_protected.py",
    "scripts/wood_joint_clearance.py",
    "scripts/wood_joint_wj04_probe.py",
    "scripts/wood_joint_wj04_tool_access.py",
)


@dataclass(frozen=True)
class StackSpec:
    stack_id: str
    interface_id: str
    axis_point_basis_mm: tuple[float, float, float]
    axis_direction_basis: tuple[float, float, float]
    layers: tuple[tuple[str, float], tuple[str, float]]


STACK_SPECS = (
    StackSpec(
        "rail_1",
        "rail_to_cleat",
        (RAIL_BOLT_X_MM, 1442.774134, RAIL_BOLT_N_MM[0]),
        (0.0, -1.0, 0.0),
        (("wj04_cleat", 88.9), ("base_rail_service_lower_right", 38.1)),
    ),
    StackSpec(
        "rail_2",
        "rail_to_cleat",
        (RAIL_BOLT_X_MM, 1442.774134, RAIL_BOLT_N_MM[1]),
        (0.0, -1.0, 0.0),
        (("wj04_cleat", 88.9), ("base_rail_service_lower_right", 38.1)),
    ),
    StackSpec(
        "upright_1",
        "principal_to_cleat",
        (177.95, PRINCIPAL_BOLT_T_MM[0], PRINCIPAL_BOLT_N_MM),
        (-1.0, 0.0, 0.0),
        (("wj04_cleat", 88.9), ("base_principal_center_right", 38.1)),
    ),
    StackSpec(
        "upright_2",
        "principal_to_cleat",
        (177.95, PRINCIPAL_BOLT_T_MM[1], PRINCIPAL_BOLT_N_MM),
        (-1.0, 0.0, 0.0),
        (("wj04_cleat", 88.9), ("base_principal_center_right", 38.1)),
    ),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _input_snapshot() -> dict[str, str]:
    return {name: _sha256(ROOT / name) for name in SOURCE_INPUTS}


def _stack_hardware() -> BoltHardware:
    candidate = WJ04_TRIAL.fasteners.bolt_by_id("kl_jack_25c600hcs5z")
    envelope = WJ04_TRIAL.stacks[0].cad_envelope
    # The shared CAD record requires thread bounds. Lg is not a full-form
    # thread-start measurement; these values remain geometry metadata only.
    return BoltHardware(
        candidate_sku=candidate.sku,
        under_head_length_mm=BOLT_LENGTH_MM,
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


def build_stacks(
    stack_specs: tuple[StackSpec, ...] = STACK_SPECS,
) -> dict[str, BoltStack]:
    """Build the four provisional 6-in stacks without changing WJ04_TRIAL."""
    if len(stack_specs) != 4 or len({spec.stack_id for spec in stack_specs}) != 4:
        raise ValueError("full-stock hypothesis must define four unique stacks")
    if sum(spec.interface_id == "rail_to_cleat" for spec in stack_specs) != 2:
        raise ValueError("full-stock hypothesis needs two rail stacks")
    if sum(spec.interface_id == "principal_to_cleat" for spec in stack_specs) != 2:
        raise ValueError("full-stock hypothesis needs two principal stacks")

    hardware = _stack_hardware()
    result = {}
    expected_layers = {
        "rail_to_cleat": (
            ("wj04_cleat", 88.9),
            ("base_rail_service_lower_right", 38.1),
        ),
        "principal_to_cleat": (
            ("wj04_cleat", 88.9),
            ("base_principal_center_right", 38.1),
        ),
    }
    for spec in stack_specs:
        if spec.interface_id not in expected_layers:
            raise ValueError(f"{spec.stack_id}: unknown full-stock interface")
        if spec.layers != expected_layers[spec.interface_id]:
            raise ValueError(f"{spec.stack_id}: layer order or dimensions changed")
        if not math.isclose(sum(layer[1] for layer in spec.layers), 127.0):
            raise ValueError(f"{spec.stack_id}: expected 127 mm actual wood grip")
        direction = cq.Vector(
            *WJ04_TRIAL.frame.vector_to_global(spec.axis_direction_basis)
        ).normalized()
        axis = cq.Vector(*WJ04_TRIAL.frame.to_global(spec.axis_point_basis_mm))
        layers = tuple(
            StackLayer(member_id, thickness) for member_id, thickness in spec.layers
        )
        under_head = axis - direction * hardware.washer_thickness_mm
        nut_seat = axis + direction * 127.0
        result[spec.stack_id] = BoltStack(
            id=spec.stack_id,
            hardware=hardware,
            under_head_origin=under_head,
            direction=direction,
            layers=layers,
            head_seat=WasherSeat(layers[0].body_id, axis, direction),
            nut_seat=WasherSeat(layers[-1].body_id, nut_seat, -direction),
            required_tip_projection_mm=(
                WJ04_TRIAL.stacks[0].cad_envelope.required_tip_projection_mm
            ),
        )
    return result


def trial_plan() -> dict[str, Any]:
    """Return the immutable proposal and dimensional screens without CAD."""
    stacks = build_stacks()
    candidate = WJ04_TRIAL.fasteners.bolt_by_id("kl_jack_25c600hcs5z")
    hardware = next(iter(stacks.values())).hardware
    grip_min_mm, grip_nominal_mm, grip_max_mm = 126.0, 127.0, 128.0
    washer_min_mm = 2 * WJ04_TRIAL.fasteners.washer.thickness_range_mm[0]
    washer_max_mm = 2 * WJ04_TRIAL.fasteners.washer.thickness_range_mm[1]
    nut_min_mm, nut_max_mm = WJ04_TRIAL.fasteners.nut.thickness_range_mm
    length_min_mm = candidate.nominal_length_mm - candidate.length_minus_tolerance_mm
    earliest_nut_face_mm = grip_min_mm + washer_min_mm
    latest_nut_face_mm = grip_max_mm + washer_max_mm
    minimum_projection_mm = length_min_mm - latest_nut_face_mm - nut_max_mm
    require_tip_mm = WJ04_TRIAL.stacks[0].cad_envelope.required_tip_projection_mm
    bolt_diameter_mm = hardware.steel_diameter_mm
    four_d_mm = 4 * bolt_diameter_mm
    five_d_mm = 5 * bolt_diameter_mm
    seven_d_mm = 7 * bolt_diameter_mm
    envelope = WJ04_TRIAL.stacks[0].cad_envelope
    rail_end_n_mm = min(
        RAIL_BOLT_N_MM[0] - CLEAT_ORIGIN_X_T_N_MM[2],
        CLEAT_ORIGIN_X_T_N_MM[2] + CLEAT_SIZE_X_T_N_MM[2] - RAIL_BOLT_N_MM[1],
    )
    rail_end_factor_mm = 3.5 * bolt_diameter_mm
    principal_low_edge_mm = PRINCIPAL_BOLT_T_MM[0] - CLEAT_ORIGIN_X_T_N_MM[1]
    principal_high_edge_mm = (
        CLEAT_ORIGIN_X_T_N_MM[1] + CLEAT_SIZE_X_T_N_MM[1] - PRINCIPAL_BOLT_T_MM[1]
    )
    return {
        "schema": SCHEMA,
        "trial_id": TRIAL_ID,
        "status": "unaccepted_geometry_hypothesis",
        "source_station": WJ04_TRIAL.station_id,
        "canonical_wj04_config_sha256": WJ04_TRIAL.canonical_sha256,
        "candidate_geometry": {
            "origin_x_t_n_mm": list(CLEAT_ORIGIN_X_T_N_MM),
            "size_x_t_n_mm": list(CLEAT_SIZE_X_T_N_MM),
            "grain_axis": "N",
            "source_host_ids": [
                "base_rail_service_lower_right",
                "base_principal_center_right",
            ],
            "source_face_ids": {
                "rail_upper_t_contact": "planar_face_04",
                "rail_rear_n_contact": "planar_face_02",
                "principal_x_end_contact": "planar_face_07",
                "principal_rear_n_contact": "planar_face_04",
            },
            "nominal_contact_rectangle_mm2": 88.9 * 119.7,
            "material_source": "one listed actual 88.9 x 88.9 mm 4x4; square crosscut to 119.7 mm along N",
            "stock_source_url": "https://www.homedepot.com/p/4-in-x-4-in-x-8-ft-2-Premium-Grade-Dimensional-Lumber-279542/300874740",
            "post_rip_regrade_required": False,
            "received_grade_species_moisture_treatment_and_minimum_section_verified": False,
            "bolt_zone_defects_checked": False,
        },
        "stacks": [
            {
                "stack_id": spec.stack_id,
                "interface_id": spec.interface_id,
                "axis_point_basis_mm": list(spec.axis_point_basis_mm),
                "axis_direction_basis": list(spec.axis_direction_basis),
                "layers_head_to_nut": [
                    {"member_id": member_id, "thickness_mm": thickness}
                    for member_id, thickness in spec.layers
                ],
                "grip_mm": round(stacks[spec.stack_id].grip_mm, 6),
                "bolt_sku": candidate.sku,
                "bolt_nominal_length_mm": candidate.nominal_length_mm,
                "bolt_status": candidate.status,
                "modeled_bore_occupancy_mm": WJ04_TRIAL.stacks[
                    0
                ].cad_envelope.bore_occupancy_diameter_mm,
                "bore_occupancy_is_not_a_drill_instruction": True,
            }
            for spec in STACK_SPECS
        ],
        "hardware_model": {
            "candidate_id": candidate.candidate_id,
            "sku": candidate.sku,
            "status": candidate.status,
            "nominal_underhead_length_mm": candidate.nominal_length_mm,
            "minus_only_length_tolerance_mm": candidate.length_minus_tolerance_mm,
            "shaft_occupied_diameter_mm": envelope.shaft_diameter_mm,
            "bore_occupancy_diameter_mm": envelope.bore_occupancy_diameter_mm,
            "head_diameter_max_mm": envelope.head_diameter_mm,
            "head_height_max_mm": envelope.head_height_mm,
            "washer_inner_diameter_min_mm": envelope.washer_inner_diameter_mm,
            "washer_outer_diameter_max_mm": envelope.washer_outer_diameter_mm,
            "washer_thickness_max_mm": envelope.washer_thickness_mm,
            "nut_across_corners_max_mm": envelope.nut_diameter_mm,
            "nut_height_max_mm": envelope.nut_height_mm,
            "required_tip_projection_assumption_mm": envelope.required_tip_projection_mm,
            "washers_per_stack": WJ04_TRIAL.fasteners.washers_per_stack,
            "dimensional_envelopes_are_not_received_part_measurements": True,
            "bore_occupancy_is_not_a_drill_instruction": True,
        },
        "conditional_placement_screen": {
            "bolt_diameter_mm": round(bolt_diameter_mm, 6),
            "conditional_4d_mm": round(four_d_mm, 6),
            "conditional_5d_mm": round(five_d_mm, 6),
            "conditional_7d_mm": round(seven_d_mm, 6),
            "rail_group": {
                "first_center_from_host_x_butt_mm": round(RAIL_BOLT_X_MM - 89.05, 6),
                "first_center_minus_conditional_7d_mm": round(
                    RAIL_BOLT_X_MM - 89.05 - seven_d_mm, 6
                ),
                "pitch_along_cleat_grain_n_mm": round(
                    RAIL_BOLT_N_MM[1] - RAIL_BOLT_N_MM[0], 6
                ),
                "pitch_minus_conservative_5d_mm": round(
                    RAIL_BOLT_N_MM[1] - RAIL_BOLT_N_MM[0] - five_d_mm, 6
                ),
                "cleat_grain_n_end_distance_each_mm": round(rail_end_n_mm, 6),
                "cleat_n_end_minus_softwood_tension_3p5d_mm": round(
                    rail_end_n_mm - rail_end_factor_mm, 6
                ),
                "conditional_c_delta_if_7d_tension_end_rule_applies": round(
                    rail_end_n_mm / seven_d_mm, 6
                ),
                "signed_loading_classified": False,
            },
            "principal_group": {
                "cleat_t_edge_distances_mm": [
                    round(principal_low_edge_mm, 6),
                    round(principal_high_edge_mm, 6),
                ],
                "minimum_t_edge_minus_conditional_4d_mm": round(
                    min(principal_low_edge_mm, principal_high_edge_mm) - four_d_mm,
                    6,
                ),
                "pitch_along_t_mm": round(
                    PRINCIPAL_BOLT_T_MM[1] - PRINCIPAL_BOLT_T_MM[0], 6
                ),
                "pitch_minus_conservative_5d_mm": round(
                    PRINCIPAL_BOLT_T_MM[1] - PRINCIPAL_BOLT_T_MM[0] - five_d_mm,
                    6,
                ),
                "signed_loading_classified": False,
            },
            "interpretation": "Conditional dimensional screen only; no load classification, NDS acceptance, or capacity is implied.",
        },
        "fastener_stack_dimensional_screen": {
            "candidate_nominal_length_mm": candidate.nominal_length_mm,
            "candidate_minus_only_length_tolerance_mm": candidate.length_minus_tolerance_mm,
            "candidate_minimum_length_mm": round(length_min_mm, 6),
            "wood_grip_assumption_mm": {
                "min": grip_min_mm,
                "nominal": grip_nominal_mm,
                "max": grip_max_mm,
                "basis": "two nominal wood layers, each screened at ±0.5 mm",
            },
            "two_washer_extreme_total_mm": {
                "min": round(washer_min_mm, 6),
                "max": round(washer_max_mm, 6),
            },
            "nut_extreme_mm": {"min": nut_min_mm, "max": nut_max_mm},
            "earliest_nut_bearing_face_from_underhead_mm": round(
                earliest_nut_face_mm, 6
            ),
            "farthest_nut_face_from_underhead_mm": round(
                latest_nut_face_mm + nut_max_mm, 6
            ),
            "minimum_delivered_tip_projection_mm": round(minimum_projection_mm, 6),
            "projection_remaining_after_receiving_reserve_mm": round(
                minimum_projection_mm - require_tip_mm, 6
            ),
            "catalog_Lb_min_last_thread_scratch_mm": candidate.minimum_smooth_body_mm,
            "catalog_Lg_max_ring_gage_inspection_plane_mm": candidate.maximum_full_thread_start_mm,
            "earliest_nut_face_minus_Lb_mm": round(
                earliest_nut_face_mm - candidate.minimum_smooth_body_mm, 6
            ),
            "Lg_max_minus_earliest_nut_face_mm": round(
                candidate.maximum_full_thread_start_mm - earliest_nut_face_mm, 6
            ),
            "actual_full_thread_transition_window_mm": "unresolved; Lb and Lg are inspection bounds, not exact thread start/end",
            "delivered_body_end_thread_start_and_functional_nut_engagement_verified": False,
            "receiving_measurement_required": True,
            "standard_sources": [
                "https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws",
                "https://www.szjlin.com/static/upload/file/20210111/1610336127463997.pdf",
            ],
            "interpretation": "Dimensional fit only. Lb is underhead bearing to last thread scratch; Lg is a GO ring-gage inspection plane. Neither guarantees delivered full-form thread location or functional nut engagement.",
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
    }


@dataclass(frozen=True)
class FullStockGeometry:
    base_geometry: Any
    parts: dict[str, cq.Shape]
    cleat: cq.Shape
    stacks: dict[str, BoltStack]
    bores: dict[str, cq.Shape]
    bore_reports: dict[str, dict[str, Any]]
    finished: dict[str, cq.Shape]
    installed: dict[str, dict[str, cq.Shape]]
    contact_area_mm2: dict[str, float]
    cleat_hits: dict[str, dict[str, float]]


def materialize_full_stock_geometry(base_geometry=None) -> FullStockGeometry:
    """Reuse pinned pretrial hosts, then cut only this hypothesis's four bores."""
    if base_geometry is None:
        base_geometry = base_probe.materialize_trial_geometry(WJ04_TRIAL)
    if base_geometry.config.canonical_sha256 != WJ04_TRIAL.canonical_sha256:
        raise ValueError(
            "source geometry must come from the unchanged canonical WJ-04 config"
        )
    if (
        base_geometry.source_binding.inventory_sha256
        != WJ04_TRIAL.source_inventory_sha256
    ):
        raise ValueError(
            "full-stock hypothesis source inventory does not match WJ-04 pin"
        )

    rail_id = "base_rail_service_lower_right"
    principal_id = "base_principal_center_right"
    cleat_id = "wj04_cleat"
    # `parts` contains retained source hosts before the active narrow trial's
    # four candidate bores. `finished` contains those old bores and is not used.
    parts = {
        rail_id: base_geometry.parts[rail_id],
        principal_id: base_geometry.parts[principal_id],
    }
    cleat = base_probe._box_in_trial_frame(
        WJ04_TRIAL, CLEAT_ORIGIN_X_T_N_MM, CLEAT_SIZE_X_T_N_MM
    )
    parts[cleat_id] = cleat
    stacks = build_stacks()
    x_axis, t_axis, _ = base_probe._frame_axes(WJ04_TRIAL)

    bores = {}
    bore_reports = {}
    for stack_id, stack in stacks.items():
        direction = stack.direction
        start = stack.head_seat.center - direction * CONTACT_PROBE_MM
        bore = cq.Solid.makeCylinder(
            stack.hardware.drill_diameter_mm / 2,
            stack.grip_mm + 2 * CONTACT_PROBE_MM,
            start,
            direction,
        )
        bores[stack_id] = bore
        progress = 0.0
        layer_fractions = {}
        for layer in stack.layers:
            segment = cq.Solid.makeCylinder(
                stack.hardware.drill_diameter_mm / 2,
                layer.thickness_mm,
                stack.head_seat.center + direction * progress,
                direction,
            )
            layer_fractions[layer.body_id] = round(
                base_probe._intersect_volume(segment, parts[layer.body_id])
                / segment.Volume(),
                6,
            )
            progress += layer.thickness_mm
        bore_reports[stack_id] = {
            "layer_material_fractions_before_cut": layer_fractions,
            "other_wood_hits": base_probe._hits(bore, base_geometry.other_wood),
            "panel_hits": base_probe._hits(bore, base_geometry.panels),
            "protected_hits": base_probe._hits(bore, base_geometry.protected),
        }

    finished = {}
    for part_id, part in parts.items():
        part_bores = [
            bores[stack_id]
            for stack_id, stack in stacks.items()
            if any(layer.body_id == part_id for layer in stack.layers)
            and base_probe._intersect_volume(part, bores[stack_id]) > HIT_TOLERANCE_MM3
        ]
        finished[part_id] = part.cut(*part_bores).clean()

    installed = {
        stack_id: dict(stack.installed_shapes()) for stack_id, stack in stacks.items()
    }
    rail = parts[rail_id]
    principal = parts[principal_id]
    contact_area = {
        "rail_to_cleat": round(
            cleat.translate(-t_axis * CONTACT_PROBE_MM).intersect(rail).Volume()
            / CONTACT_PROBE_MM,
            6,
        ),
        "principal_to_cleat": round(
            cleat.translate(-x_axis * CONTACT_PROBE_MM).intersect(principal).Volume()
            / CONTACT_PROBE_MM,
            6,
        ),
    }
    cleat_hits = {
        "hosts": base_probe._hits(cleat, {rail_id: rail, principal_id: principal}),
        "other_wood": base_probe._hits(cleat, base_geometry.other_wood),
        "panels": base_probe._hits(cleat, base_geometry.panels),
        "protected": base_probe._hits(cleat, base_geometry.protected),
    }
    return FullStockGeometry(
        base_geometry=base_geometry,
        parts=parts,
        cleat=cleat,
        stacks=stacks,
        bores=bores,
        bore_reports=bore_reports,
        finished=finished,
        installed=installed,
        contact_area_mm2=contact_area,
        cleat_hits=cleat_hits,
    )


def _named_shapes(shapes: dict[str, cq.Shape], prefix: str) -> dict[str, cq.Shape]:
    return {f"{prefix}/{name}": shape for name, shape in shapes.items()}


def _compact_collisions(result: dict[str, Any]) -> dict[str, Any]:
    hits = result["external_envelope_hits_mm3"]
    return {
        "envelope_clear": not hits,
        "hits_mm3": hits,
        "physical_clearance_established": False,
        "broad_envelope_clash_proves_impossibility": False,
    }


def _obstacles(geometry: FullStockGeometry) -> dict[str, cq.Shape]:
    base = geometry.base_geometry
    wood = {**base.other_wood, **base.panels, **geometry.finished}
    hardware = {
        f"{stack_id}/{role}": shape
        for stack_id, shapes in geometry.installed.items()
        for role, shape in shapes.items()
    }
    return {
        **_named_shapes(wood, "wood"),
        **_named_shapes(base.protected, "protected"),
        **_named_shapes(hardware, "hardware"),
    }


def _reference_vector(stack: BoltStack) -> cq.Vector:
    direction = stack.direction.normalized()
    axes = tuple(
        cq.Vector(*axis)
        for axis in (
            WJ04_TRIAL.frame.x_global,
            WJ04_TRIAL.frame.t_global,
            WJ04_TRIAL.frame.n_global,
        )
    )
    cardinal = min(axes, key=lambda axis: abs(axis.dot(direction)))
    return (cardinal - direction * cardinal.dot(direction)).normalized()


def _wrench_operations(
    stack: BoltStack,
    side: str,
    target_shape: cq.Shape,
    obstacles: dict[str, cq.Shape],
    tool: Any,
) -> tuple[
    dict[str, dict[str, Any]], dict[float, cq.Shape], dict[float, dict[str, cq.Shape]]
]:
    outward = -stack.direction if side == "head" else stack.direction
    center = tool_access._seated_tool_center(
        stack.head_seat.center if side == "head" else stack.nut_seat.center,
        outward,
        target_shape,
        tool.head_thickness_mm,
    )
    reference = _reference_vector(stack)
    operations = {}
    seated = {}
    paths_by_offset = {}
    for offset in tool.head_offsets_degrees:
        wrench = tool_access.build_catalog_wrench_envelope(
            center,
            outward,
            reference,
            tool,
            offset_degrees=offset,
        )
        handle, _, _ = tool_access._tool_frame(outward, reference, offset)
        paths = tool_access.wrench_reindex_path(
            wrench,
            center,
            outward,
            handle,
            flat_stroke_degrees=TOOL_SWEEP_DEGREES,
            head_width_mm=tool.head_width_mm,
        )
        shape_paths = {
            name: shape for name, shape in paths.items() if isinstance(shape, cq.Shape)
        }
        operations[f"{offset:g}deg"] = _compact_collisions(
            tool_access.collision_report(
                {"seated": wrench, **shape_paths},
                obstacles,
                excluded_target_ids=(
                    f"hardware/{stack.id}/{side}",
                    f"hardware/{stack.id}/shaft",
                ),
            )
        )
        seated[offset] = wrench
        paths_by_offset[offset] = shape_paths
    return operations, seated, paths_by_offset


def _assembly_sequence_screen(geometry: FullStockGeometry) -> dict[str, Any]:
    """Find clear bolt insertion orders after one-time base/pair screens."""
    base = geometry.base_geometry
    fixed_obstacles = {
        **_named_shapes(
            {**base.other_wood, **base.panels, **geometry.finished}, "wood"
        ),
        **_named_shapes(base.protected, "protected"),
    }
    stack_ids = tuple(spec.stack_id for spec in STACK_SPECS)
    base_hits = {}
    prior_stack_hits = {}
    for stack_id in stack_ids:
        stack = geometry.stacks[stack_id]
        strokes = bolt_axis_stroke_shapes(stack)
        direction = stack.direction.normalized()
        head_washer = geometry.installed[stack_id]["head_washer"]
        head_washer_start = head_washer.translate(
            -direction * stack.hardware.under_head_length_mm
        )
        strokes["head_washer_insertion"] = tool_access.translation_sweep(
            head_washer_start,
            direction * stack.hardware.under_head_length_mm,
        )
        base_hits[stack_id] = tool_access.collision_report(strokes, fixed_obstacles)[
            "external_envelope_hits_mm3"
        ]
        for prior_id in stack_ids:
            if prior_id == stack_id:
                continue
            installed_prior = {
                f"hardware/{prior_id}/{role}": shape
                for role, shape in geometry.installed[prior_id].items()
            }
            prior_stack_hits[(stack_id, prior_id)] = tool_access.collision_report(
                strokes, installed_prior
            )["external_envelope_hits_mm3"]

    clear_orders = []
    blocked_orders = []
    for order in itertools.permutations(stack_ids):
        steps = []
        prior_ids = []
        for stack_id in order:
            hits = {
                name: dict(obstacles) for name, obstacles in base_hits[stack_id].items()
            }
            for prior_id in prior_ids:
                for path_name, obstacles in prior_stack_hits[
                    (stack_id, prior_id)
                ].items():
                    hits.setdefault(path_name, {}).update(obstacles)
            steps.append(
                {
                    "stack_id": stack_id,
                    "insertion_clear_with_prior_stacks_installed": not hits,
                    "hits_mm3": hits,
                }
            )
            prior_ids.append(stack_id)
        order_result = {"stack_order": list(order), "steps": steps}
        if all(row["insertion_clear_with_prior_stacks_installed"] for row in steps):
            clear_orders.append(order_result["stack_order"])
        else:
            blocked_orders.append(
                {
                    "stack_order": order_result["stack_order"],
                    "blocked_stack_ids": [
                        row["stack_id"]
                        for row in steps
                        if not row["insertion_clear_with_prior_stacks_installed"]
                    ],
                }
            )
    return {
        "orders_examined": math.factorial(len(stack_ids)),
        "clear_order_count": len(clear_orders),
        "clear_orders": clear_orders,
        "blocked_orders": blocked_orders,
        "insertion_path_hits_with_no_prior_stacks": base_hits,
        "insertion_path_hits_against_each_possible_prior_stack": {
            f"{stack_id}_after_{prior_id}": hits
            for (stack_id, prior_id), hits in prior_stack_hits.items()
        },
        "insertion_model": "Each shaft/head straight stroke and head washer ride-on path is screened with every source member, service cut, protected solid, and all previously installed complete stacks present.",
        "limitations": [
            "Order search does not model frame erection or temporary removal of the upper service rail.",
            "Open-end wrench sweeps and nut/washer installation remain separate required operations.",
            "A clear modeled order does not establish field access, tightening, or acceptance.",
        ],
    }


def _stack_geometry_report(geometry: FullStockGeometry) -> dict[str, Any]:
    base = geometry.base_geometry
    all_finished = {**base.other_wood, **base.panels, **geometry.finished}
    obstacles = _obstacles(geometry)
    tool = WJ04_TRIAL.fasteners.tools[0]
    stacks_out = {}
    for stack_id, stack in geometry.stacks.items():
        own_keys = {f"hardware/{stack_id}/{role}" for role in stack.installed_shapes()}
        own_names = {f"wood/{layer.body_id}" for layer in stack.layers}
        installed_hits = {}
        for role, shape in geometry.installed[stack_id].items():
            installed_hits[role] = {
                "wood": base_probe._hits(shape, all_finished),
                "protected": base_probe._hits(shape, base.protected),
                "other_stacks": base_probe._hits(
                    shape,
                    {
                        name: candidate
                        for name, candidate in obstacles.items()
                        if name.startswith("hardware/") and name not in own_keys
                    },
                ),
            }

        operations = {}
        simple_families = (
            ("50mm_axial_tool_approach", access_shapes(stack)),
            ("bolt_insertion_withdrawal", bolt_axis_stroke_shapes(stack)),
            ("detached_component_removal", detached_hardware_removal_shapes(stack)),
        )
        for family, shapes in simple_families:
            excluded = (
                tuple(own_keys)
                if family != "50mm_axial_tool_approach"
                else (
                    f"hardware/{stack_id}/head",
                    f"hardware/{stack_id}/nut",
                    f"hardware/{stack_id}/shaft",
                )
            )
            operations[family] = _compact_collisions(
                tool_access.collision_report(
                    shapes, obstacles, excluded_target_ids=excluded
                )
            )

        target_shapes = geometry.installed[stack_id]
        head_tools, head_seated, _head_paths = _wrench_operations(
            stack,
            "head",
            target_shapes["head"],
            obstacles,
            tool,
        )
        nut_tools, nut_seated, nut_paths = _wrench_operations(
            stack,
            "nut",
            target_shapes["nut"],
            obstacles,
            tool,
        )
        operations["catalog_open_end_wrench"] = {
            "head_end": head_tools,
            "nut_end": nut_tools,
            "paired_counterhold_vs_turning_sweep": {},
        }
        for head_offset, nut_offset in itertools.product(head_seated, nut_seated):
            key = f"head_{head_offset:g}_nut_{nut_offset:g}deg"
            head = head_seated[head_offset]
            nut_path_shapes = nut_paths[nut_offset]
            pair_hits = {
                shape_name: round(base_probe._intersect_volume(head, shape), 6)
                for shape_name, shape in nut_path_shapes.items()
                if base_probe._intersect_volume(head, shape) > HIT_TOLERANCE_MM3
            }
            operations["catalog_open_end_wrench"][
                "paired_counterhold_vs_turning_sweep"
            ][key] = {
                "envelopes_clear": not pair_hits,
                "hits_mm3": pair_hits,
                "physical_two_wrench_access_established": False,
            }

        target_keys = {
            role: f"hardware/{stack_id}/{role}"
            for role in ("head", "shaft", "nut", "nut_washer")
        }
        nut_removal = tool_access._nut_removal_screen(
            stack,
            tool,
            obstacles,
            target_keys,
            target_shapes,
        )
        operations["nut_and_nut_washer_assembly"] = {
            "reverse_of_bounded_removal_sweep_screened": True,
            "translation_and_rotation_envelopes_are_reversible": True,
            "thread_start_and_functional_nut_engagement_verified": False,
            "screen": nut_removal,
        }
        operations["bounded_nut_removal"] = nut_removal
        nominal_required_length = (
            2 * stack.hardware.washer_thickness_mm
            + stack.grip_mm
            + stack.hardware.nut_height_mm
            + stack.required_tip_projection_mm
        )
        nominal_length_margin = (
            stack.hardware.under_head_length_mm - nominal_required_length
        )
        seats = {
            "head": washer_support_report(
                stack.head_seat,
                geometry.finished[stack.head_seat.body_id],
                stack.hardware,
            ),
            "nut": washer_support_report(
                stack.nut_seat,
                geometry.finished[stack.nut_seat.body_id],
                stack.hardware,
            ),
        }
        stacks_out[stack_id] = {
            "grip_mm": round(stack.grip_mm, 6),
            "candidate_sku": stack.hardware.candidate_sku,
            "nominal_length_margin_mm_after_two_max_washers_nut_and_tip": round(
                nominal_length_margin, 6
            ),
            "catalog_gaging_bounds_establish_full_thread_at_nut": False,
            "thread_transition_and_functional_nut_engagement": "unresolved; receive and measure delivered bolt/nut stack",
            "washer_support": {
                side: {
                    "fraction": round(result.support_fraction, 6),
                    "full_annulus_supported": result.full_seat,
                }
                for side, result in seats.items()
            },
            "bore": geometry.bore_reports[stack_id],
            "installed_component_hits": installed_hits,
            "operations": operations,
            "intentional_layer_ids": [layer.body_id for layer in stack.layers],
            "excluded_wood_ids_from_stack_clearance_summary": sorted(own_names),
        }
    return stacks_out


def report(base_geometry=None) -> dict[str, Any]:
    """Build full source-bound diagnostics; run only in the parent CAD slot."""
    before = _input_snapshot()
    candidate_geometry = materialize_full_stock_geometry(base_geometry)
    plan = trial_plan()
    base = candidate_geometry.base_geometry
    x_axis, t_axis, n_axis = base_probe._frame_axes(WJ04_TRIAL)
    cleat_n1 = CLEAT_ORIGIN_X_T_N_MM[2] + CLEAT_SIZE_X_T_N_MM[2]
    neighbor_id = "base_rail_service_upper_right"
    upper_rail = base.wood[neighbor_id]
    upper_rail_t_min = min(
        vertex.Center().dot(t_axis) for vertex in upper_rail.Vertices()
    )
    cleat_t_max = CLEAT_ORIGIN_X_T_N_MM[1] + CLEAT_SIZE_X_T_N_MM[1]
    stack_screens = _stack_geometry_report(candidate_geometry)
    assembly = _assembly_sequence_screen(candidate_geometry)
    after = _input_snapshot()
    if before != after:
        raise RuntimeError(
            "WJ-04 full-stock inputs changed during probe; rerun from a stable snapshot"
        )

    return {
        **plan,
        "producer_sha256": _sha256(Path(__file__)),
        "source_input_sha256": before,
        "source_binding": {
            "inventory_sha256": base.source_binding.inventory_sha256,
            "runtime_module_sha256": base.source_binding.runtime_module_sha256,
            "uncut_part_shapes_sha256": base.source_binding.uncut_part_shapes_sha256,
            "uncut_host_shape_sha256": base.source_binding.uncut_host_shape_sha256,
            "fixed_screw_axes_sha256": base.source_binding.fixed_screw_axes_sha256,
            "frame_bolt_axes_sha256": base.source_binding.frame_bolt_axes_sha256,
        },
        "materialized_geometry": {
            "source_hosts_pretrial_bores_used": True,
            "canonical_narrow_trial_finished_hosts_reused": False,
            "new_bores_cut_only_for_full_stock_hypothesis": True,
            "contact_area_mm2": candidate_geometry.contact_area_mm2,
            "cleat_hits_mm3": candidate_geometry.cleat_hits,
            "upper_service_rail": {
                "member_id": neighbor_id,
                "lower_t_face_mm": round(upper_rail_t_min, 6),
                "cleat_upper_t_face_mm": round(cleat_t_max, 6),
                "nominal_face_gap_mm": round(upper_rail_t_min - cleat_t_max, 6),
                "cleat_upper_face_to_full_50mm_axial_approach_gap_mm": round(
                    upper_rail_t_min - cleat_t_max - 50.0, 6
                ),
                "upper_rail_present_during_insertion_and_tool_screens": True,
            },
            "cleat_local_n_from_rail_front_mm": [
                round(
                    CLEAT_ORIGIN_X_T_N_MM[2] - WJ04_TRIAL.source_bounds.rail_n_min_mm, 6
                ),
                round(cleat_n1 - WJ04_TRIAL.source_bounds.rail_n_min_mm, 6),
            ],
            "ordinary_rear_envelope_mm": ORDINARY_REAR_ENVELOPE_MM,
            "cleat_rear_excess_mm": round(
                max(0.0, cleat_n1 - WJ04_TRIAL.source_bounds.rail_n_max_mm), 6
            ),
            "contact_axes_global": {
                "X": [round(value, 9) for value in x_axis.toTuple()],
                "T": [round(value, 9) for value in t_axis.toTuple()],
                "N": [round(value, 9) for value in n_axis.toTuple()],
            },
        },
        "stack_diagnostics": stack_screens,
        "assembly_order_screen": assembly,
        "limits": [
            "This is a new-build alternate geometry model; the six superseded WJ04 SDS axes are not retained as physical holes, and no used-lumber repair or reuse is assumed.",
            "Catalog dimensions and modeled tools are envelopes only; actual delivered bolts, thread transitions, washers, nuts, wrenches, and tolerances remain unverified.",
            "The conditional NDS comparisons require signed load classification and member-specific analysis; they are not capacity or acceptance results.",
            "Four WJ03 outer replacement nodes are absent from this local screen; it does not establish integrated service clearance or a complete-system load path.",
            "No physical assembly, material inspection, purchase, drilling, fabrication, structural, or replacement acceptance is asserted.",
        ],
        "claim_boundary": {
            "accepted_replacement_count": 0,
            "physical_replacement_accepted": False,
            "structural_accepted": False,
            "purchase_approved": False,
            "drilling_released": False,
            "fabrication_released": False,
            "capacity_established": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="print the lightweight proposal without source CAD materialization",
    )
    args = parser.parse_args()
    result = trial_plan() if args.plan_only else report()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
