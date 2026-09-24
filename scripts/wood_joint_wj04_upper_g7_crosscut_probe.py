"""Source-bound WJ-04 upper G7-clearance crosscut hypothesis.

This is a separate unaccepted geometry proposal. The earlier full-length upper
pair hypothesis remains preserved unchanged. Running this module without
``--materialize`` prints only its source-bound plan and does not build CAD.
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
from mini_moonboard.hold_tnut_reinforcement import datums as hold_datums
from mini_moonboard.wood_joint_frame import bolt_axis_stroke_shapes
from mini_moonboard.wood_joint_geometry import BoltStack, StackLayer, WasherSeat
from mini_moonboard.wood_joint_panel_machining import candidate_panel_replacements
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import owner_layout_protected
from scripts import wood_joint_wj04_full_stock_probe as stack_probe
from scripts import wood_joint_wj04_probe as base_probe
from scripts import wood_joint_wj04_tool_access as tool_access
from scripts import wood_joint_wj04_upper_pair_probe as prior_probe

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = "docs/wood-joints-mvp/source-inventory.json"
LOWER_STATION = "clip_horizontal_lower_right_1"
UPPER_STATION = "clip_horizontal_upper_right_1"
LOWER_CLEAT = "wj04_lower_full_stock_cleat"
UPPER_CLEAT = "wj04_upper_g7_crosscut_full_stock_cleat"
PRINCIPAL = "base_principal_center_right"
LOWER_RAIL = "base_rail_service_lower_right"
UPPER_RAIL = "base_rail_service_upper_right"

SCHEMA = "wood_joint_wj04_upper_g7_crosscut_probe/v1"
TRIAL_ID = "upper_g7_clearance_n86p9_reversed_rail_hypothesis"
PRIOR_FAILED_REPORT_SHA256 = (
    "2df952ff8b01a9b56b1c445d54d5aea8ea7b94b75b818bcc002a1719168b9d9f"
)

CLEAT_SIZE_MM = (88.9, 88.9, 119.7)
LOWER_CLEAT_ORIGIN_MM = (89.05, 1353.874134, 229.840968)
UPPER_CLEAT_ORIGIN_MM = (89.05, 1497.924134, 262.640968)
UPPER_CLEAT_SIZE_MM = (88.9, 88.9, 86.9)
RAIL_X_MM = 134.5
LOWER_RAIL_N_MM = (273.190968, 306.190968)
UPPER_RAIL_N_MM = (289.590968, 322.590968)
PRINCIPAL_X_MM = 177.95
LOWER_PRINCIPAL_N_MM = 289.690968
UPPER_PRINCIPAL_N_MM = 306.090968
LOWER_PRINCIPAL_T_MM = (1381.874134, 1414.874134)
UPPER_PRINCIPAL_T_MM = (1525.924134, 1558.924134)
UPPER_RAIL_HEAD_T_MM = 1459.824134
G7_CLEARANCE_RESERVE_MM = 2.0
CONTACT_PROBE_MM = 0.1
HIT_TOLERANCE_MM3 = 1e-6

SOURCE_INPUTS = tuple(
    dict.fromkeys(
        (
            *prior_probe.SOURCE_INPUTS,
            "scripts/wood_joint_wj04_upper_pair_probe.py",
            "mini_moonboard/model.py",
            "mini_moonboard/hold_tnut_reinforcement.py",
            "mini_moonboard/panel_grid.py",
            "mini_moonboard/panel_grid_v2.py",
            "mini_moonboard/floor_flush_width.py",
            "mini_moonboard/compact_floor_flush_frame.py",
            "mini_moonboard/compact_floor_taper_frame.py",
            "mini_moonboard/compact_floor_recess_frame.py",
            "mini_moonboard/compact_base_finish.py",
            "mini_moonboard/compact_spliced_kicker.py",
            "mini_moonboard/compact_spliced_trimmed.py",
            "mini_moonboard/compact_spliced_installation.py",
            "mini_moonboard/compact_spliced_knee_frame.py",
            "mini_moonboard/no_shoes_frame.py",
            "mini_moonboard/round_structural_frame.py",
            "mini_moonboard/wide_frame.py",
        )
    )
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
    *,
    station_id: str,
    prefix: str,
    cleat_id: str,
    host_rail_id: str,
    rail_head_t_mm: float,
    rail_n_mm: tuple[float, float],
    rail_direction: tuple[float, float, float],
    rail_layers: tuple[tuple[str, float], tuple[str, float]],
    principal_n_mm: float,
    principal_t_mm: tuple[float, float],
) -> tuple[StackSpec, ...]:
    return (
        StackSpec(
            f"{prefix}_rail_1",
            station_id,
            cleat_id,
            "rail_to_cleat",
            (RAIL_X_MM, rail_head_t_mm, rail_n_mm[0]),
            rail_direction,
            rail_layers,
        ),
        StackSpec(
            f"{prefix}_rail_2",
            station_id,
            cleat_id,
            "rail_to_cleat",
            (RAIL_X_MM, rail_head_t_mm, rail_n_mm[1]),
            rail_direction,
            rail_layers,
        ),
        StackSpec(
            f"{prefix}_principal_1",
            station_id,
            cleat_id,
            "principal_to_cleat",
            (PRINCIPAL_X_MM, principal_t_mm[0], principal_n_mm),
            (-1.0, 0.0, 0.0),
            ((cleat_id, 88.9), (PRINCIPAL, 38.1)),
        ),
        StackSpec(
            f"{prefix}_principal_2",
            station_id,
            cleat_id,
            "principal_to_cleat",
            (PRINCIPAL_X_MM, principal_t_mm[1], principal_n_mm),
            (-1.0, 0.0, 0.0),
            ((cleat_id, 88.9), (PRINCIPAL, 38.1)),
        ),
    )


STACK_SPECS = (
    *_station_specs(
        station_id=LOWER_STATION,
        prefix="lower",
        cleat_id=LOWER_CLEAT,
        host_rail_id=LOWER_RAIL,
        rail_head_t_mm=LOWER_CLEAT_ORIGIN_MM[1] + CLEAT_SIZE_MM[1],
        rail_n_mm=LOWER_RAIL_N_MM,
        rail_direction=(0.0, -1.0, 0.0),
        rail_layers=((LOWER_CLEAT, 88.9), (LOWER_RAIL, 38.1)),
        principal_n_mm=LOWER_PRINCIPAL_N_MM,
        principal_t_mm=LOWER_PRINCIPAL_T_MM,
    ),
    *_station_specs(
        station_id=UPPER_STATION,
        prefix="upper",
        cleat_id=UPPER_CLEAT,
        host_rail_id=UPPER_RAIL,
        rail_head_t_mm=UPPER_RAIL_HEAD_T_MM,
        rail_n_mm=UPPER_RAIL_N_MM,
        rail_direction=(0.0, 1.0, 0.0),
        rail_layers=((UPPER_RAIL, 38.1), (UPPER_CLEAT, 88.9)),
        principal_n_mm=UPPER_PRINCIPAL_N_MM,
        principal_t_mm=UPPER_PRINCIPAL_T_MM,
    ),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_snapshot() -> dict[str, str]:
    return {path: _sha256(ROOT / path) for path in SOURCE_INPUTS}


def _source_inventory() -> dict[str, Any]:
    payload = json.loads((ROOT / INVENTORY).read_text())
    if _sha256(ROOT / INVENTORY) != WJ04_TRIAL.source_inventory_sha256:
        raise ValueError("live source inventory differs from canonical WJ-04 pin")
    return payload


def _selected_duties(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return prior_probe._selected_duties(inventory)


def _stack_specs_valid(specs: tuple[StackSpec, ...]) -> None:
    ids = [spec.stack_id for spec in specs]
    if len(ids) != 8 or len(set(ids)) != 8:
        raise ValueError("hypothesis requires eight unique stack assignments")
    expected = {spec.stack_id: spec for spec in STACK_SPECS}
    if set(ids) != set(expected):
        raise ValueError("hypothesis requires all eight named stack assignments")
    for spec in specs:
        if spec != expected[spec.stack_id]:
            raise ValueError(f"{spec.stack_id}: differs from named hypothesis axes")
        if not math.isclose(sum(layer[1] for layer in spec.layers), 127.0):
            raise ValueError(f"{spec.stack_id}: expected 127 mm nominal wood grip")
        if spec.interface_id == "rail_to_cleat" and spec.station_id == LOWER_STATION:
            if spec.layers != ((spec.cleat_id, 88.9), (LOWER_RAIL, 38.1)):
                raise ValueError("lower rail stack head-to-nut layers changed")
        elif spec.interface_id == "rail_to_cleat":
            if spec.layers != ((UPPER_RAIL, 38.1), (UPPER_CLEAT, 88.9)):
                raise ValueError("upper reversed rail stack layer order changed")
        elif spec.layers != ((spec.cleat_id, 88.9), (PRINCIPAL, 38.1)):
            raise ValueError(f"{spec.stack_id}: principal stack layers changed")


def build_stacks(
    stack_specs: tuple[StackSpec, ...] = STACK_SPECS,
) -> dict[str, BoltStack]:
    """Build only this named hypothesis's eight candidate stacks."""
    _stack_specs_valid(stack_specs)
    template = stack_probe.build_stacks()["rail_1"]
    hardware = template.hardware
    result = {}
    for spec in stack_specs:
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


def _g7_projection_bounds() -> dict[str, Any]:
    """Compute the provisional G7 cylinder bounds without source shape loading."""
    model = variant(KERF_RIGHT)
    row = next(
        datum for datum in hold_datums(model) if datum["name"] == "hold_tnut_main_G7"
    )
    rear = cq.Vector(*row["rear_seating_xyz_mm"])
    direction = -cq.Vector(*row["barrel_into_panel_direction"]).normalized()
    basis = tuple(
        cq.Vector(*axis)
        for axis in (
            WJ04_TRIAL.frame.x_global,
            WJ04_TRIAL.frame.t_global,
            WJ04_TRIAL.frame.n_global,
        )
    )
    length = owner_layout_protected.TRIAL_HOLD_REAR_PROJECTION_MM
    radius = owner_layout_protected.HOLD_HOLE_DIAMETER_MM / 2
    center = rear + direction * (length / 2)
    center_basis = tuple(center.dot(axis) for axis in basis)
    direction_basis = tuple(direction.dot(axis) for axis in basis)
    half_extents = tuple(
        length / 2 * abs(component)
        + radius * math.sqrt(max(0.0, 1.0 - component * component))
        for component in direction_basis
    )
    bounds = {
        axis: [round(center_value - extent, 9), round(center_value + extent, 9)]
        for axis, center_value, extent in zip(
            ("X", "T", "N"), center_basis, half_extents, strict=True
        )
    }
    return {
        "datum_id": row["name"],
        "panel_id": row["panel"],
        "rear_seating_x_t_n_mm": [round(rear.dot(axis), 9) for axis in basis],
        "projection_axis_x_t_n": [round(value, 9) for value in direction_basis],
        "diameter_mm": owner_layout_protected.HOLD_HOLE_DIAMETER_MM,
        "length_mm": length,
        "bounds_x_t_n_mm": bounds,
        "delivered_hold_bolt_geometry_verified": False,
    }


def trial_plan() -> dict[str, Any]:
    """Build pure axis/layout data; do not materialize source or trial shapes."""
    inventory = _source_inventory()
    duties = _selected_duties(inventory)
    stacks = build_stacks()
    g7 = _g7_projection_bounds()
    screw_count = len(inventory["fixed_panel_kicker_screws"])
    frame_bolt_count = len(inventory["starting_frame_bolts"])
    if screw_count != 66 or frame_bolt_count != 12:
        raise ValueError("hypothesis must retain 66 panel axes and 12 frame bolts")

    g7_n_max = g7["bounds_x_t_n_mm"]["N"][1]
    cleat_n_min = UPPER_CLEAT_ORIGIN_MM[2]
    reserve = cleat_n_min - g7_n_max
    if not math.isclose(reserve, G7_CLEARANCE_RESERVE_MM, abs_tol=1e-6):
        raise ValueError("upper crosscut no longer retains the 2 mm G7 reserve")
    if not math.isclose(
        UPPER_CLEAT_ORIGIN_MM[2] + UPPER_CLEAT_SIZE_MM[2],
        WJ04_TRIAL.source_bounds.rail_n_max_mm,
        abs_tol=1e-8,
    ):
        raise ValueError("upper crosscut must remain within source N cap")

    rail_end_distances = (
        UPPER_RAIL_N_MM[0] - cleat_n_min,
        UPPER_CLEAT_ORIGIN_MM[2] + UPPER_CLEAT_SIZE_MM[2] - UPPER_RAIL_N_MM[1],
    )
    if not all(
        math.isclose(value, 26.95, abs_tol=1e-8) for value in rail_end_distances
    ):
        raise ValueError("upper rail row end distances changed from named hypothesis")
    washer_radius = WJ04_TRIAL.fasteners.washer.outer_diameter_range_mm[1] / 2
    upper_rail_critical_seat_margin = (
        WJ04_TRIAL.source_bounds.rail_n_max_mm - UPPER_RAIL_N_MM[1] - washer_radius
    )
    head_depth = (
        WJ04_TRIAL.fasteners.washer.thickness_range_mm[1]
        + WJ04_TRIAL.fasteners.head.height_range_mm[1]
    )
    lower_gap_face_t = LOWER_CLEAT_ORIGIN_MM[1] + CLEAT_SIZE_MM[1]
    upper_rail_low_t = UPPER_CLEAT_ORIGIN_MM[1] - 38.1
    opposing_head_gap = upper_rail_low_t - lower_gap_face_t - 2 * head_depth
    output_specs = []
    for spec in STACK_SPECS:
        output_specs.append(
            {
                "stack_id": spec.stack_id,
                "station_id": spec.station_id,
                "interface_id": spec.interface_id,
                "axis_point_basis_mm": list(spec.axis_point_basis_mm),
                "axis_direction_basis": list(spec.axis_direction_basis),
                "layers_head_to_nut": [
                    {"member_id": member, "thickness_mm": thickness}
                    for member, thickness in spec.layers
                ],
                "grip_mm": round(stacks[spec.stack_id].grip_mm, 6),
                "bolt_model_class": "25C600HCS5Z 6-in partially-threaded cap-screw envelope; provisional",
                "thread_transition_status": "unresolved; ASME Lg is a ring-gage plane, not first full-form thread",
            }
        )

    return {
        "schema": SCHEMA,
        "trial_id": TRIAL_ID,
        "status": "unaccepted_geometry_hypothesis",
        "predecessor_hypothesis": {
            "trial_id": "full_x88p9_lower_upper_pair_hypothesis",
            "report_sha256": PRIOR_FAILED_REPORT_SHA256,
            "preserved_separately": True,
        },
        "source_inventory_sha256": _sha256(ROOT / INVENTORY),
        "canonical_wj04_config_sha256": WJ04_TRIAL.canonical_sha256,
        "source_candidate_id": WJ04_TRIAL.preserved_selected_candidate_id,
        "source_variant": WJ04_TRIAL.source_variant,
        "source_inputs_sha256": _source_snapshot(),
        "fixed_obligations": {
            "panel_kicker_screw_axes": screw_count,
            "starting_frame_bolts": frame_bolt_count,
            "preservation_required": True,
            "cad_environment_materialized": False,
        },
        "pair_spacing": {
            "lower_block_t_interval_mm": [
                LOWER_CLEAT_ORIGIN_MM[1],
                LOWER_CLEAT_ORIGIN_MM[1] + CLEAT_SIZE_MM[1],
            ],
            "upper_block_t_interval_mm": [
                UPPER_CLEAT_ORIGIN_MM[1],
                UPPER_CLEAT_ORIGIN_MM[1] + UPPER_CLEAT_SIZE_MM[1],
            ],
            "nominal_clear_gap_mm": round(
                UPPER_CLEAT_ORIGIN_MM[1]
                - (LOWER_CLEAT_ORIGIN_MM[1] + CLEAT_SIZE_MM[1]),
                6,
            ),
        },
        "stations": {
            LOWER_STATION: {
                "cleat_origin_x_t_n_mm": list(LOWER_CLEAT_ORIGIN_MM),
                "cleat_size_x_t_n_mm": list(CLEAT_SIZE_MM),
                "host_members": duties[LOWER_STATION]["legacy_host_members"],
            },
            UPPER_STATION: {
                "cleat_origin_x_t_n_mm": list(UPPER_CLEAT_ORIGIN_MM),
                "cleat_size_x_t_n_mm": list(UPPER_CLEAT_SIZE_MM),
                "stock_note": "full 88.9 x 88.9 mm section; 86.9 mm N crosscut",
                "host_members": duties[UPPER_STATION]["legacy_host_members"],
                "g7_projection": g7,
                "g7_clearance_reserve_mm": round(reserve, 6),
                "g7_clearance_basis": (
                    "nominal datum-boundary difference; stock, hold, placement, and "
                    "cut tolerances are not included"
                ),
                "rail_row_end_distances_mm": [
                    round(value, 6) for value in rail_end_distances
                ],
                "rail_row_pitch_mm": round(UPPER_RAIL_N_MM[1] - UPPER_RAIL_N_MM[0], 6),
                "rail_end_distance_ratio_to_7d": round(
                    rail_end_distances[0] / (7 * 6.35), 9
                ),
                "rail_minimum_3p5d_mm": round(3.5 * 6.35, 6),
                "rail_full_factor_7d_mm": round(7 * 6.35, 6),
                "signed_demand_and_capacity_status": "unresolved; conditional end-distance factor is not resistance acceptance",
                "critical_rail_washer_support_margin_mm": round(
                    upper_rail_critical_seat_margin, 6
                ),
                "critical_rail_washer_outer_diameter_mm": WJ04_TRIAL.fasteners.washer.outer_diameter_range_mm[
                    1
                ],
                "contact_area_screen": {
                    "nominal_full_length_mm2": round(
                        CLEAT_SIZE_MM[0] * CLEAT_SIZE_MM[2], 6
                    ),
                    "crosscut_length_mm2": round(
                        UPPER_CLEAT_SIZE_MM[0] * UPPER_CLEAT_SIZE_MM[2], 6
                    ),
                    "nominal_area_reduction_fraction": round(
                        1 - UPPER_CLEAT_SIZE_MM[2] / CLEAT_SIZE_MM[2], 9
                    ),
                    "geometry_status": "analytic patch bound only; CAD and load transfer unverified",
                },
            },
        },
        "upper_rail_reversal": {
            "head_seat_t_mm": UPPER_RAIL_HEAD_T_MM,
            "axis_direction_x_t_n": [0.0, 1.0, 0.0],
            "head_to_nut_layers": [
                {"member_id": UPPER_RAIL, "thickness_mm": 38.1},
                {"member_id": UPPER_CLEAT, "thickness_mm": 88.9},
            ],
            "wood_face_gap_to_lower_cleat_mm": round(
                upper_rail_low_t - lower_gap_face_t, 6
            ),
            "max_head_plus_washer_depth_per_side_mm": round(head_depth, 6),
            "opposing_head_envelope_gap_mm": round(opposing_head_gap, 6),
            "installed_axial_overlap_removed_by_reversal": True,
            "tool_access_status": "unresolved; adjacent wood blocks straight axial access in all-members-installed pose",
            "assembly_prerequisite": "upper rail and cleat bolt subassembly must be installed before lower cleat occupies insertion path, or alternate erection path must be proven",
        },
        "stacks": output_specs,
        "claim_boundary": {
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


def _revised_stack_diagnostics(geometry: prior_probe.PairGeometry) -> dict[str, Any]:
    """Run audited component screens against revised geometry and stacks."""
    other_wood = {
        name: shape
        for name, shape in geometry.all_wood.items()
        if name not in geometry.parts
    }
    local_base = type(
        "RevisedPairCollisionContext",
        (),
        {
            "other_wood": other_wood,
            "panels": geometry.panels,
            "protected": geometry.protected,
        },
    )()
    generic = stack_probe.FullStockGeometry(
        base_geometry=local_base,
        parts=geometry.parts,
        cleat=geometry.parts[UPPER_CLEAT],
        stacks=geometry.stacks,
        bores=geometry.bores,
        bore_reports=geometry.bore_reports,
        finished=geometry.finished,
        installed=geometry.installed,
        contact_area_mm2={},
        cleat_hits=geometry.cleat_hits[UPPER_STATION],
    )
    return stack_probe._stack_geometry_report(generic)


def _hit_map(candidate: cq.Shape, obstacles: dict[str, cq.Shape]) -> dict[str, float]:
    return {
        name: round(volume, 6)
        for name, shape in obstacles.items()
        if (volume := base_probe._intersect_volume(candidate, shape))
        > HIT_TOLERANCE_MM3
    }


def _assembly_blocker_graph(geometry: prior_probe.PairGeometry) -> dict[str, Any]:
    """Use revised stack mapping; bound order search to at most 256 states."""
    stack_ids = tuple(geometry.stacks)
    fixed_wood = {
        name: shape
        for name, shape in geometry.all_wood.items()
        if name not in geometry.parts
    }
    fixed = {
        **{
            f"wood/{name}": shape
            for name, shape in {
                **fixed_wood,
                **geometry.panels,
                **geometry.finished,
            }.items()
        },
        **{f"protected/{name}": shape for name, shape in geometry.protected.items()},
    }
    fixed_hits: dict[str, dict[str, dict[str, float]]] = {}
    prior_hits: dict[tuple[str, str], dict[str, dict[str, float]]] = {}
    for stack_id, stack in geometry.stacks.items():
        strokes = bolt_axis_stroke_shapes(stack)
        direction = stack.direction.normalized()
        washer = geometry.installed[stack_id]["head_washer"]
        washer_start = washer.translate(
            -direction * stack.hardware.under_head_length_mm
        )
        strokes["head_washer_insertion"] = tool_access.translation_sweep(
            washer_start, direction * stack.hardware.under_head_length_mm
        )
        fixed_hits[stack_id] = {
            path: _hit_map(shape, fixed) for path, shape in strokes.items()
        }
        for prior_id, prior_shapes in geometry.installed.items():
            if prior_id == stack_id:
                continue
            obstacles = {
                f"hardware/{prior_id}/{role}": shape
                for role, shape in prior_shapes.items()
            }
            prior_hits[(stack_id, prior_id)] = {
                path: _hit_map(shape, obstacles) for path, shape in strokes.items()
            }

    reachable = {0: ()}
    expanded = 0
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
                expanded += 1
    final_mask = (1 << len(stack_ids)) - 1
    return {
        "orders_enumerated": 0,
        "subset_states_expanded": expanded,
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
            "Search uses revised geometry.stacks and checks straight insertion and washer ride-on only.",
            "Temporary member removal, frame erection, lateral wrench access and physical fitting are not modeled.",
            "A clear order would not establish field access or acceptance.",
        ],
    }


def materialize_geometry(
    base_geometry: Any | None = None,
) -> prior_probe.PairGeometry:
    """Build revised pair with restored selected SDS holes and retained cuts."""
    if base_geometry is None:
        base_geometry = base_probe.materialize_trial_geometry(WJ04_TRIAL)
    if base_geometry.config.canonical_sha256 != WJ04_TRIAL.canonical_sha256:
        raise ValueError("revised hypothesis requires unchanged canonical WJ-04 config")
    if (
        base_geometry.source_binding.inventory_sha256
        != WJ04_TRIAL.source_inventory_sha256
    ):
        raise ValueError("revised hypothesis source inventory differs from WJ-04 pin")

    inventory = _source_inventory()
    duties = _selected_duties(inventory)
    removed_ids = prior_probe._axis_ids(duties)
    hosts = prior_probe._rebuild_hosts_with_removed_stations(
        base_geometry.source, inventory, removed_ids
    )
    lower_delta = abs(
        hosts[LOWER_RAIL].Volume() - base_geometry.parts[LOWER_RAIL].Volume()
    )
    if lower_delta > 1e-5:
        raise ValueError("lower host reconstruction differs from audited WJ-04 source")

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
    parts = dict(hosts)
    parts[LOWER_CLEAT] = base_probe._box_in_trial_frame(
        WJ04_TRIAL, LOWER_CLEAT_ORIGIN_MM, CLEAT_SIZE_MM
    )
    parts[UPPER_CLEAT] = base_probe._box_in_trial_frame(
        WJ04_TRIAL, UPPER_CLEAT_ORIGIN_MM, UPPER_CLEAT_SIZE_MM
    )
    stacks = build_stacks()
    x_axis, t_axis, _n_axis = base_probe._frame_axes(WJ04_TRIAL)

    bores = {}
    bore_reports = {}
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
            if (
                first_id < second_id
                and base_probe._intersect_volume(first, second) > HIT_TOLERANCE_MM3
            ):
                raise ValueError(f"candidate bores overlap: {first_id}, {second_id}")

    finished = {}
    for part_id, shape in parts.items():
        cuts = [
            bore
            for stack_id, stack in stacks.items()
            if any(layer.body_id == part_id for layer in stack.layers)
            and base_probe._intersect_volume(shape, bores[stack_id]) > HIT_TOLERANCE_MM3
            for bore in (bores[stack_id],)
        ]
        finished[part_id] = shape.cut(*cuts).clean() if cuts else shape
    installed = {
        stack_id: dict(stack.installed_shapes()) for stack_id, stack in stacks.items()
    }

    cleat_hits = {}
    contact_area = {}
    for station, cleat_id, rail_id in (
        (LOWER_STATION, LOWER_CLEAT, LOWER_RAIL),
        (UPPER_STATION, UPPER_CLEAT, UPPER_RAIL),
    ):
        cleat = parts[cleat_id]
        cleat_hits[station] = {
            "hosts": base_probe._hits(
                cleat, {rail_id: parts[rail_id], PRINCIPAL: parts[PRINCIPAL]}
            ),
            "other_wood": base_probe._hits(
                cleat,
                {
                    name: shape
                    for name, shape in all_wood.items()
                    if name not in (rail_id, PRINCIPAL)
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
        contact_area[station] = {
            "rail_to_cleat": round(
                cleat.translate(-t_axis * CONTACT_PROBE_MM)
                .intersect(parts[rail_id])
                .Volume()
                / CONTACT_PROBE_MM,
                6,
            ),
            "principal_to_cleat": round(
                cleat.translate(-x_axis * CONTACT_PROBE_MM)
                .intersect(parts[PRINCIPAL])
                .Volume()
                / CONTACT_PROBE_MM,
                6,
            ),
        }

    return prior_probe.PairGeometry(
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
        removed_axis_ids=removed_ids,
        panel_overlay_names=tuple(sorted(panel_parts)),
    )


def report(base_geometry: Any | None = None) -> dict[str, Any]:
    """Build CAD diagnostics only when explicitly invoked after review."""
    before = _source_snapshot()
    plan = trial_plan()
    geometry = materialize_geometry(base_geometry)
    diagnostics = _revised_stack_diagnostics(geometry)
    assembly = _assembly_blocker_graph(geometry)
    after = _source_snapshot()
    if before != after:
        raise RuntimeError("revised WJ-04 inputs changed during probe")
    return {
        **plan,
        "producer_sha256": _sha256(Path(__file__)),
        "source_inputs_sha256": before,
        "source_binding": {
            "inventory_sha256": geometry.base.source_binding.inventory_sha256,
            "runtime_module_sha256": geometry.base.source_binding.runtime_module_sha256,
            "uncut_part_shapes_sha256": geometry.base.source_binding.uncut_part_shapes_sha256,
            "uncut_host_shape_sha256": geometry.base.source_binding.uncut_host_shape_sha256,
            "fixed_screw_axes_sha256": geometry.base.source_binding.fixed_screw_axes_sha256,
            "frame_bolt_axes_sha256": geometry.base.source_binding.frame_bolt_axes_sha256,
            "raw_source_binding_mutated": False,
        },
        "fixed_obligations": {
            **plan["fixed_obligations"],
            "cad_environment_materialized": True,
            "preserved_in_local_environment": True,
        },
        "candidate_panel_overlay": {
            "applied_panel_ids": list(geometry.panel_overlay_names),
            "applied_to_local_geometry_map": True,
            "raw_source_binding_mutated": False,
            "canonical_wj04_overlay_changed": False,
        },
        "materialized_geometry": {
            "removed_legacy_axes": sorted(geometry.removed_axis_ids),
            "removed_legacy_axis_count": len(geometry.removed_axis_ids),
            "retained_source_openings_reapplied_after_sds_restoration": True,
            "lower_rail_reconstruction_volume_delta_mm3": round(
                abs(
                    geometry.parts[LOWER_RAIL].Volume()
                    - geometry.base.parts[LOWER_RAIL].Volume()
                ),
                9,
            ),
            "cleat_hits_mm3": geometry.cleat_hits,
            "contact_area_mm2": geometry.contact_area_mm2,
            "canonical_narrow_trial_finished_hosts_reused": False,
        },
        "stack_diagnostics": diagnostics,
        "assembly_blocker_graph": assembly,
        "environment_obligations": {
            "fixed_panel_kicker_screw_count": len(
                _source_inventory()["fixed_panel_kicker_screws"]
            ),
            "starting_frame_bolt_count": len(
                _source_inventory()["starting_frame_bolts"]
            ),
            "all_nonselected_legacy_connector_and_sds_geometry_retained": True,
            "corrected_candidate_right_panels_used_in_local_map": True,
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
            "This is a local two-duty geometry hypothesis, not a complete WJ-06 layout or load path.",
            "The 50.8 mm G7 projection is a provisional keepout, not delivered hold-bolt geometry.",
            "Rail-row end-distance factor is conditional on signed demand and member-specific resistance checks.",
            "Crosscut reduces nominal two-face contact area; no load-transfer or resistance result is inferred.",
            "Bolt, thread transition, washers, tools, stock condition, and assembly sequence remain unverified.",
            "No physical replacement, drilling, fabrication, purchase, or structural acceptance is asserted.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--materialize",
        action="store_true",
        help="run full geometry diagnostics after separate review and slot approval",
    )
    args = parser.parse_args()
    result = report() if args.materialize else trial_plan()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
