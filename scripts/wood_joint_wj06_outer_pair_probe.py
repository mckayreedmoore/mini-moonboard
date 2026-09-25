"""Source-bound installed-geometry hypothesis for the two right outer rails.

This diagnostic targets only the lower and upper right outer service-rail
stations. It keeps the source's other finished cuts, models full-depth 4x4
cleats and provisional bolt envelopes, and makes no structural, drilling,
fabrication, procurement, or assembly-sequence claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from mini_moonboard.wood_joint_frame import _make_parts as make_wj03_trial_parts
from mini_moonboard.wood_joint_frame import validate_source_binding
from mini_moonboard.wood_joint_geometry import (
    BoltHardware,
    BoltStack,
    StackLayer,
    WasherSeat,
    washer_support_report,
)
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_full_stock_probe as wj04_stock
from scripts import wood_joint_wj04_probe as wj04_base
from scripts import wood_joint_wj06_residual_probe as wj06_residual

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "docs/wood-joints-mvp/source-inventory.json"
INVENTORY = "docs/wood-joints-mvp/source-inventory.json"
SCHEMA = "wood_joint_wj06_outer_pair_probe/v1"
TRIAL_ID = "right_outer_full_4x4_paired_rail_hypothesis"
CANDIDATE = "compact-floor-flush-wood-joints-development"

LOWER_STATION = "clip_horizontal_lower_right_2"
UPPER_STATION = "clip_horizontal_upper_right_2"
LOWER_RAIL = "base_rail_service_lower_right"
UPPER_RAIL = "base_rail_service_upper_right"
SIDE_HOST = "base_side_right"
LOWER_CLEAT = "wj06_outer_lower_right_cleat"
UPPER_CLEAT = "wj06_outer_upper_right_cleat"

CLEAT_SIZE_MM = (88.9, 88.9, 119.7)
CLEAT_X_ORIGIN_MM = 1038.225
CLEAT_N_ORIGIN_MM = 229.840968
LOWER_CLEAT_T_ORIGIN_MM = 1353.874134
UPPER_CLEAT_T_ORIGIN_MM = 1497.924134
RAIL_X_MM = 1081.675
RAIL_N_MM = (273.190968, 306.190968)
SIDE_N_MM = 289.690968
LOWER_SIDE_T_MM = (1381.874134, 1414.874134)
UPPER_SIDE_T_MM = (1525.924134, 1558.924134)
SIDE_BOLT_LENGTH_MM = 203.2
SIDE_BOLT_MIN_LENGTH_MM = 198.628  # 8 in less the ASME ordinary-bolt 0.18 in bound.
SIDE_BOLT_HEAD_HEIGHT_MAX_MM = 0.188 * 25.4
SIDE_BOLT_CATALOG_URL = (
    "https://shop.forcesinc.ca/products/hex-head-bolt-1-4-20-x-8-"
    "partial-thread-plain-steel-grade-5"
)
RAIL_BOLT_CANDIDATE = next(
    bolt for bolt in WJ04_TRIAL.fasteners.bolts if bolt.sku == "25C600HCS5Z"
)
RAIL_BOLT_LENGTH_MM = RAIL_BOLT_CANDIDATE.nominal_length_mm
# The shared 6-in cap-screw basis uses a 0.10-in minus tolerance, not the
# 0.06-in tolerance of the shorter 3-3/4-in WJ-04 rail candidate.
RAIL_BOLT_MIN_LENGTH_MM = (
    RAIL_BOLT_LENGTH_MM - RAIL_BOLT_CANDIDATE.length_minus_tolerance_mm
)
RAIL_BOLT_X_MIN_FROM_BUTT_MM = 45.45
NOMINAL_4D_MM = 4 * 6.35
NOMINAL_5D_MM = 5 * 6.35
NOMINAL_7D_MM = 7 * 6.35
CONTACT_PROBE_MM = 0.1
HIT_TOLERANCE_MM3 = 1e-6
_volume = wj04_base._intersect_volume
_hits = wj04_base._hits

SOURCE_INPUTS = (
    INVENTORY,
    "docs/wood-joints-mvp/stock-and-cut-basis.md",
    "docs/wood-joints-mvp/ordinary-hardware-basis.md",
    "docs/wood-joints-mvp/wood-limit-state-basis.md",
    "docs/wood-joints-mvp/wj03-hardware-procurement.md",
    "mini_moonboard/floor_flush_width.py",
    "mini_moonboard/hold_tnut_reinforcement.py",
    "mini_moonboard/compact_floor_flush_frame.py",
    "mini_moonboard/wood_joint_frame.py",
    "mini_moonboard/wood_joint_geometry.py",
    "mini_moonboard/wood_joint_panel_machining.py",
    "mini_moonboard/wood_joint_wj04_config.py",
    "scripts/wood_joint_wj04_probe.py",
    "scripts/wood_joint_wj04_full_stock_probe.py",
    "scripts/wood_joint_wj06_residual_probe.py",
    "scripts/wood_joint_clearance.py",
)

X_BASIS = (1.0, 0.0, 0.0)
T_BASIS = (0.0, math.cos(math.radians(50.0)), math.sin(math.radians(50.0)))
N_BASIS = (0.0, -math.sin(math.radians(50.0)), math.cos(math.radians(50.0)))
BASIS = (X_BASIS, T_BASIS, N_BASIS)


@dataclass(frozen=True)
class StackSpec:
    stack_id: str
    station_id: str
    cleat_id: str
    interface_id: str
    host_id: str
    axis_point_basis_mm: tuple[float, float, float]
    axis_direction_basis: tuple[float, float, float]
    layers: tuple[tuple[str, float], tuple[str, float]]
    nominal_bolt_length_mm: float
    minimum_length_mm: float
    hardware_model: str

    @property
    def grip_mm(self) -> float:
        return sum(thickness for _, thickness in self.layers)


def _stack_specs() -> tuple[StackSpec, ...]:
    rows: list[StackSpec] = []
    for (
        station_id,
        cleat_id,
        rail_id,
        rail_head_t,
        rail_direction,
        rail_layers,
        side_ts,
    ) in (
        (
            LOWER_STATION,
            LOWER_CLEAT,
            LOWER_RAIL,
            LOWER_CLEAT_T_ORIGIN_MM + CLEAT_SIZE_MM[1],
            (0.0, -1.0, 0.0),
            ((LOWER_CLEAT, 88.9), (LOWER_RAIL, 38.1)),
            LOWER_SIDE_T_MM,
        ),
        (
            UPPER_STATION,
            UPPER_CLEAT,
            UPPER_RAIL,
            UPPER_CLEAT_T_ORIGIN_MM - 38.1,
            (0.0, 1.0, 0.0),
            ((UPPER_RAIL, 38.1), (UPPER_CLEAT, 88.9)),
            UPPER_SIDE_T_MM,
        ),
    ):
        prefix = "lower" if station_id == LOWER_STATION else "upper"
        for index, n_mm in enumerate(RAIL_N_MM, 1):
            rows.append(
                StackSpec(
                    f"{prefix}_rail_{index}",
                    station_id,
                    cleat_id,
                    "rail_to_cleat",
                    rail_id,
                    (RAIL_X_MM, rail_head_t, n_mm),
                    rail_direction,
                    rail_layers,
                    RAIL_BOLT_LENGTH_MM,
                    RAIL_BOLT_MIN_LENGTH_MM,
                    "K.L. Jack 25C600HCS5Z 6-in model; provisional geometry only",
                )
            )
        for index, t_mm in enumerate(side_ts, 1):
            rows.append(
                StackSpec(
                    f"{prefix}_side_{index}",
                    station_id,
                    cleat_id,
                    "cleat_to_side",
                    SIDE_HOST,
                    (CLEAT_X_ORIGIN_MM, t_mm, SIDE_N_MM),
                    (1.0, 0.0, 0.0),
                    ((cleat_id, 88.9), (SIDE_HOST, 88.9)),
                    SIDE_BOLT_LENGTH_MM,
                    SIDE_BOLT_MIN_LENGTH_MM,
                    "Forces F086013 ordinary hex-bolt catalog lead; unselected/unreceived",
                )
            )
    return tuple(rows)


STACK_SPECS = _stack_specs()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inventory(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.loads(INVENTORY_PATH.read_text()) if payload is None else payload
    if data.get("candidate") != CANDIDATE:
        raise ValueError("source inventory candidate changed")
    if payload is None and _sha(INVENTORY_PATH) != WJ04_TRIAL.source_inventory_sha256:
        raise ValueError(
            "live source inventory differs from canonical WJ-04 source pin"
        )
    if len(data.get("legacy_duties", ())) != 24:
        raise ValueError("expected 24 source duties")
    if (
        sum(len(duty.get("legacy_sds_axes", ())) for duty in data["legacy_duties"])
        != 144
    ):
        raise ValueError("expected 144 source SDS axes")
    if len(data.get("fixed_panel_kicker_screws", ())) != 66:
        raise ValueError("expected exactly 66 fixed panel/kicker axes")
    if len(data.get("starting_frame_bolts", ())) != 12:
        raise ValueError("expected exactly 12 starting frame-bolt axes")
    return data


def _selected_duties(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected = {LOWER_STATION, UPPER_STATION}
    rows = {
        row["legacy_station_id"]: row
        for row in inventory["legacy_duties"]
        if row["legacy_station_id"] in expected
    }
    if set(rows) != expected:
        raise ValueError(
            "outer-pair probe requires exactly both right-outer source duties"
        )
    expected_hosts = {
        LOWER_STATION: [LOWER_RAIL, SIDE_HOST],
        UPPER_STATION: [UPPER_RAIL, SIDE_HOST],
    }
    all_ids: list[str] = []
    for station_id, row in rows.items():
        if row["legacy_host_members"] != expected_hosts[station_id]:
            raise ValueError(f"{station_id}: source host mapping changed")
        axes = row["legacy_sds_axes"]
        if len(axes) != 6 or len({axis["axis_id"] for axis in axes}) != 6:
            raise ValueError(f"{station_id}: expected six unique replaced SDS axes")
        if any(axis.get("shop_opening_kind") != "sds_wood" for axis in axes):
            raise ValueError(
                f"{station_id}: only former SDS wood openings are removable"
            )
        if {axis.get("axis_role") for axis in axes} != {"beam", "upright"}:
            raise ValueError(f"{station_id}: source axis roles changed")
        all_ids.extend(axis["axis_id"] for axis in axes)
    if len(set(all_ids)) != 12:
        raise ValueError(
            "the two target stations must have exactly 12 unique old SDS IDs"
        )
    return rows


def _basis_point(point: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(sum(a * b for a, b in zip(point, axis, strict=True)) for axis in BASIS)


def _basis_direction(
    direction: tuple[float, float, float],
) -> tuple[float, float, float]:
    return _basis_point(direction)


def _part_basis_bounds(part: dict[str, Any]) -> dict[str, tuple[float, float]]:
    """Project inventory's actual local extents through its source transform."""
    extents = part["actual_shape_extents_local_mm"]
    matrix = part["local_to_global_transform"]
    corners = []
    for x in extents["X"]:
        for t in extents["T"]:
            for n in extents["N"]:
                xyz = tuple(
                    sum(matrix[i][j] * (x, t, n, 1.0)[j] for j in range(4))
                    for i in range(3)
                )
                corners.append(_basis_point(xyz))
    return {
        name: (
            round(min(row[index] for row in corners), 6),
            round(max(row[index] for row in corners), 6),
        )
        for index, name in enumerate(("X", "T", "N"))
    }


def _part_rows(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {row["part_id"]: row for row in inventory["parts"]}
    required = {LOWER_RAIL, UPPER_RAIL, SIDE_HOST}
    if not required <= result.keys():
        raise ValueError("source inventory is missing a target timber host")
    return result


def _validate_source_datums(inventory: dict[str, Any]) -> dict[str, Any]:
    parts = _part_rows(inventory)
    bounds = {
        name: _part_basis_bounds(parts[name])
        for name in (LOWER_RAIL, UPPER_RAIL, SIDE_HOST)
    }
    expected = {
        LOWER_RAIL: {
            "X": (89.05, 1127.125),
            "T": (1315.774, 1353.874),
            "N": (209.841, 349.541),
        },
        UPPER_RAIL: {
            "X": (89.05, 1127.125),
            "T": (1459.824, 1497.924),
            "N": (209.841, 349.541),
        },
        SIDE_HOST: {"X": (1127.125, 1216.025), "N": (209.841, 349.541)},
    }
    for member, axis_bounds in expected.items():
        for axis, limits in axis_bounds.items():
            if any(
                abs(actual - wanted) > 0.002
                for actual, wanted in zip(bounds[member][axis], limits, strict=True)
            ):
                raise ValueError(f"source inventory {member} {axis} bounds changed")
    if parts[LOWER_RAIL]["grain_axis_global_xyz"] != [1.0, 0.0, 0.0]:
        raise ValueError("lower service rail grain axis changed")
    if parts[UPPER_RAIL]["grain_axis_global_xyz"] != [1.0, 0.0, 0.0]:
        raise ValueError("upper service rail grain axis changed")
    expected_side_grain = WJ04_TRIAL.frame.t_global
    if any(
        abs(actual - expected) > 1e-9
        for actual, expected in zip(
            parts[SIDE_HOST]["grain_axis_global_xyz"], expected_side_grain, strict=True
        )
    ):
        raise ValueError("right side-host grain axis changed")
    section = {
        name: list(parts[name]["actual_source_section_mm"])
        for name in (LOWER_RAIL, UPPER_RAIL, SIDE_HOST)
    }
    expected_sections = {
        LOWER_RAIL: (38.1, 139.7),
        UPPER_RAIL: (38.1, 139.7),
        SIDE_HOST: (88.9, 139.7),
    }
    for member, dimensions in expected_sections.items():
        if any(
            abs(actual - wanted) > 0.002
            for actual, wanted in zip(section[member], dimensions, strict=True)
        ):
            raise ValueError(f"source inventory {member} section changed")
    return {
        "basis_bounds_mm": bounds,
        "source_section_mm": section,
        "grain_axis_global_xyz": {
            name: list(parts[name]["grain_axis_global_xyz"])
            for name in (LOWER_RAIL, UPPER_RAIL, SIDE_HOST)
        },
    }


def _axis_record(axis: dict[str, Any]) -> dict[str, Any]:
    return {
        "axis_id": axis["axis_id"],
        "origin_x_t_n_mm": [
            round(value, 6)
            for value in _basis_point(tuple(axis["origin_global_xyz_mm"]))
        ],
        "direction_x_t_n": [
            round(value, 9)
            for value in _basis_direction(tuple(axis["axis_global_xyz"]))
        ],
        "source_occupied_length_mm": axis["source_occupied_length_mm"],
        "shop_opening_kind": axis["shop_opening_kind"],
    }


def _expected_body_origin(station_id: str) -> tuple[float, float, float]:
    return (
        CLEAT_X_ORIGIN_MM,
        LOWER_CLEAT_T_ORIGIN_MM
        if station_id == LOWER_STATION
        else UPPER_CLEAT_T_ORIGIN_MM,
        CLEAT_N_ORIGIN_MM,
    )


def _stack_specs_valid(specs: tuple[StackSpec, ...]) -> None:
    expected = {spec.stack_id: spec for spec in STACK_SPECS}
    ids = [spec.stack_id for spec in specs]
    if len(ids) != 8 or len(set(ids)) != 8 or set(ids) != set(expected):
        raise ValueError(
            "outer-pair hypothesis requires eight unique stack assignments"
        )
    for spec in specs:
        if spec != expected[spec.stack_id]:
            raise ValueError(
                f"{spec.stack_id}: axis, grip, or host differs from named proposal"
            )
        expected_grip = 127.0 if spec.interface_id == "rail_to_cleat" else 177.8
        if not math.isclose(spec.grip_mm, expected_grip, abs_tol=1e-9):
            raise ValueError(f"{spec.stack_id}: unexpected member grip")


def _hardware(length_mm: float, *, side: bool) -> BoltHardware:
    base = wj04_stock._stack_hardware()
    if not side:
        return base
    # This sentinel thread interval prevents a false thread-fit pass. It is not
    # a claim about the 8-in bolt; installed collision geometry only uses the
    # nominal shaft, head, washer, and nut envelopes.
    return BoltHardware(
        candidate_sku="Forces F086013 catalog lead; unselected/unreceived",
        under_head_length_mm=length_mm,
        steel_diameter_mm=base.steel_diameter_mm,
        cad_occupied_diameter_mm=base.cad_occupied_diameter_mm,
        drill_diameter_mm=base.drill_diameter_mm,
        head_diameter_mm=base.head_diameter_mm,
        head_height_mm=(SIDE_BOLT_HEAD_HEIGHT_MAX_MM if side else base.head_height_mm),
        washer_od_mm=base.washer_od_mm,
        washer_id_mm=base.washer_id_mm,
        washer_thickness_mm=base.washer_thickness_mm,
        nut_diameter_mm=base.nut_diameter_mm,
        nut_height_mm=base.nut_height_mm,
        usable_thread_start_mm=length_mm - 0.001,
        usable_thread_end_mm=length_mm,
    )


def build_stacks(specs: tuple[StackSpec, ...] = STACK_SPECS) -> dict[str, BoltStack]:
    """Build physical envelopes; the side thread interval is intentionally a sentinel."""
    _stack_specs_valid(specs)
    result: dict[str, BoltStack] = {}
    for spec in specs:
        side = spec.interface_id == "cleat_to_side"
        hardware = _hardware(spec.nominal_bolt_length_mm, side=side)
        direction = cq.Vector(
            *WJ04_TRIAL.frame.vector_to_global(spec.axis_direction_basis)
        ).normalized()
        seat = cq.Vector(*WJ04_TRIAL.frame.to_global(spec.axis_point_basis_mm))
        layers = tuple(
            StackLayer(member_id, thickness) for member_id, thickness in spec.layers
        )
        under_head = seat - direction * hardware.washer_thickness_mm
        nut_seat = seat + direction * spec.grip_mm
        result[spec.stack_id] = BoltStack(
            id=spec.stack_id,
            hardware=hardware,
            under_head_origin=under_head,
            direction=direction,
            layers=layers,
            head_seat=WasherSeat(layers[0].body_id, seat, direction),
            nut_seat=WasherSeat(layers[-1].body_id, nut_seat, -direction),
            required_tip_projection_mm=WJ04_TRIAL.stacks[
                0
            ].cad_envelope.required_tip_projection_mm,
        )
    return result


def trial_plan(inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    """Produce exact source rows and station/stack plan without loading CAD."""
    source_inventory = _inventory(inventory)
    duties = _selected_duties(source_inventory)
    datums = _validate_source_datums(source_inventory)
    _stack_specs_valid(STACK_SPECS)
    stack_rows = []
    for spec in STACK_SPECS:
        stack_rows.append(
            {
                "stack_id": spec.stack_id,
                "station_id": spec.station_id,
                "interface_id": spec.interface_id,
                "host_member": spec.host_id,
                "axis_point_basis_mm": list(spec.axis_point_basis_mm),
                "axis_direction_basis": list(spec.axis_direction_basis),
                "layers_head_to_nut": [
                    {"member_id": member, "thickness_mm": thickness}
                    for member, thickness in spec.layers
                ],
                "wood_grip_mm": round(spec.grip_mm, 6),
                "nominal_bolt_length_mm": spec.nominal_bolt_length_mm,
                "minimum_length_bound_mm": spec.minimum_length_mm,
                "hardware_model": spec.hardware_model,
                "hardware_source_url": (
                    SIDE_BOLT_CATALOG_URL
                    if spec.interface_id == "cleat_to_side"
                    else None
                ),
                "thread_transition_status": (
                    "unresolved; side interval is a non-evidence sentinel"
                    if spec.interface_id == "cleat_to_side"
                    else "unresolved; ring-gage bound does not locate first full-form thread"
                ),
                "capacity_or_selection_status": "provisional model envelope only",
            }
        )
    cleats = {}
    for station_id, cleat_id in (
        (LOWER_STATION, LOWER_CLEAT),
        (UPPER_STATION, UPPER_CLEAT),
    ):
        cleats[station_id] = {
            "cleat_id": cleat_id,
            "origin_x_t_n_mm": list(_expected_body_origin(station_id)),
            "size_x_t_n_mm": list(CLEAT_SIZE_MM),
            "grain_axis": "N",
            "stock_lead": "full 4x4 solid-sawn section; crosscut to 119.7 mm grain length",
            "delivered_stock_observed": False,
            "grade_and_defect_status": "source/section confirmation required; no delivery observed",
        }
    rail_min_edge = min(
        RAIL_N_MM[0] - CLEAT_N_ORIGIN_MM,
        CLEAT_N_ORIGIN_MM + CLEAT_SIZE_MM[2] - RAIL_N_MM[1],
    )
    return {
        "schema": SCHEMA,
        "trial_id": TRIAL_ID,
        "status": "unaccepted installed-geometry hypothesis",
        "source_candidate": source_inventory["source_candidate"],
        "source_variant": source_inventory["width_variant"],
        "source_inventory_sha256": _sha(INVENTORY_PATH) if inventory is None else None,
        "source_datums": datums,
        "stations": {
            station_id: {
                "legacy_host_members": duties[station_id]["legacy_host_members"],
                "cleat": cleats[station_id],
                "replaced_source_sds_axes": [
                    _axis_record(axis) for axis in duties[station_id]["legacy_sds_axes"]
                ],
                "removed_old_sds_axis_count": 6,
            }
            for station_id in (LOWER_STATION, UPPER_STATION)
        },
        "pair_geometry": {
            "lower_cleat_t_interval_mm": [
                LOWER_CLEAT_T_ORIGIN_MM,
                LOWER_CLEAT_T_ORIGIN_MM + CLEAT_SIZE_MM[1],
            ],
            "upper_cleat_t_interval_mm": [
                UPPER_CLEAT_T_ORIGIN_MM,
                UPPER_CLEAT_T_ORIGIN_MM + CLEAT_SIZE_MM[1],
            ],
            "clear_t_gap_mm": round(
                UPPER_CLEAT_T_ORIGIN_MM - LOWER_CLEAT_T_ORIGIN_MM - CLEAT_SIZE_MM[1], 6
            ),
            "rail_end_x_mm": 1127.125,
            "side_inner_face_x_mm": 1127.125,
            "side_outer_face_x_mm": 1216.025,
            "rail_row_x_mm": RAIL_X_MM,
            "rail_rows_n_mm": list(RAIL_N_MM),
            "side_row_n_mm": SIDE_N_MM,
            "rail_butt_end_distance_mm": RAIL_BOLT_X_MIN_FROM_BUTT_MM,
            "nominal_7d_mm": NOMINAL_7D_MM,
            "rail_butt_margin_over_7d_mm": round(
                RAIL_BOLT_X_MIN_FROM_BUTT_MM - NOMINAL_7D_MM, 6
            ),
            "minimum_full_cleat_n_end_distance_mm": round(rail_min_edge, 6),
            "nominal_3p5d_mm": 3.5 * 6.35,
            "nominal_7d_mm_full_factor": NOMINAL_7D_MM,
            "rail_row_pitch_mm": RAIL_N_MM[1] - RAIL_N_MM[0],
            "nominal_5d_mm": NOMINAL_5D_MM,
            "side_loaded_t_edge_distances_lower_mm": [28.0, 27.9],
            "side_loaded_t_edge_distances_upper_mm": [28.0, 27.9],
            "nominal_4d_mm": NOMINAL_4D_MM,
            "cross_bore_centerline_clearance_mm": 16.5,
            "cross_bore_surface_gap_at_7p5_envelopes_mm": 9.0,
            "upper_g7_shifted_row_warning": (
                "Do not combine N289.590968/322.590968 rail rows with side row N289.690968; "
                "the first orthogonal axes would nearly coincide. This far-end full-length "
                "station uses the unshifted full-depth rows."
            ),
        },
        "stacks": stack_rows,
        "fixed_obligations": {
            "fixed_panel_kicker_axes": len(
                source_inventory["fixed_panel_kicker_screws"]
            ),
            "starting_frame_bolt_axes": len(source_inventory["starting_frame_bolts"]),
            "preserved": True,
            "former_outer_sds_axes_removed": 12,
            "all_other_source_openings_reapplied": True,
        },
        "provisional_length_arithmetic": {
            "washer_thickness_mm_max_each": 2.032,
            "washer_thickness_mm_min_each": 1.2954,
            "nut_thickness_mm_max": 5.7404,
            "tip_projection_mm_model": 2.54,
            "wood_layer_allowance_mm_each": 0.5,
            "rail_grip_nominal_min_max_mm": [127.0, 126.0, 128.0],
            "rail_earliest_nut_bearing_face_mm": 128.5908,
            "rail_farthest_nut_face_mm": 137.8044,
            "rail_6in_min_length_bound_mm": RAIL_BOLT_MIN_LENGTH_MM,
            "rail_required_length_with_reserve_mm": 140.3444,
            "rail_min_length_margin_with_layer_allowance_mm": round(
                RAIL_BOLT_MIN_LENGTH_MM - 140.3444, 6
            ),
            "side_grip_nominal_min_max_mm": [177.8, 176.8, 178.8],
            "side_earliest_nut_bearing_face_mm": 179.3908,
            "side_farthest_nut_face_mm": 188.6044,
            "side_required_length_with_reserve_mm": 191.1444,
            "side_8in_asme_min_length_bound_mm": SIDE_BOLT_MIN_LENGTH_MM,
            "side_min_length_margin_with_layer_allowance_mm": 7.4836,
            "side_thread_receive_check": (
                "verify delivered full-form start <=179.3908 mm and continuous "
                "full-form through 191.1444 mm including the project reserve; "
                "the catalog listing gives no transition coordinate"
            ),
            "thread_engagement": "unresolved; no received fastener or thread-transition measurement",
        },
        "assembly_status": {
            "static_installed_geometry_only": True,
            "side_release_required_for_plus_n_subassembly_insertion": True,
            "insertion_sweep_tested": False,
            "wrench_access_tested": False,
            "assembly_sequence_proven": False,
        },
        "claim_boundary": {
            "target_duty_count": 2,
            "target_old_sds_axis_count": 12,
            "accepted_replacement_count": 0,
            "capacity_established": False,
            "drilling_released": False,
            "fabrication_released": False,
            "purchase_approved": False,
            "structural_accepted": False,
            "assembly_proven": False,
        },
    }


def _vector_basis(point: tuple[float, float, float]) -> cq.Vector:
    return cq.Vector(*WJ04_TRIAL.frame.to_global(point))


def _rounded_vec(value: cq.Vector, digits: int = 6) -> list[float]:
    return [round(component, digits) for component in value.toTuple()]


def _installed_component_timber_hits(
    installed: dict[str, cq.Shape], finished_timber: dict[str, cq.Shape]
) -> dict[str, dict[str, float]]:
    """Check every component against all timber, including both host layers."""
    return {
        component: hits
        for component, shape in installed.items()
        if (hits := _hits(shape, finished_timber))
    }


def _finished_members_with_bores(
    parts: dict[str, cq.Shape],
    stacks: dict[str, BoltStack],
    bores: dict[str, cq.Shape],
) -> dict[str, cq.Shape]:
    """Cut each member with every candidate bore that actually crosses it."""
    finished = {}
    for part_id, shape in parts.items():
        cutters = [
            bores[stack_id]
            for stack_id, stack in stacks.items()
            if any(layer.body_id == part_id for layer in stack.layers)
            and _volume(shape, bores[stack_id]) > HIT_TOLERANCE_MM3
        ]
        finished[part_id] = shape.cut(*cutters).clean() if cutters else shape
    return finished


def _retained_source_clips(
    current_parts: tuple[Any, ...], inventory: dict[str, Any]
) -> dict[str, cq.Shape]:
    target_ids = {LOWER_STATION, UPPER_STATION}
    source_ids = {row["legacy_station_id"] for row in inventory["legacy_duties"]}
    retained_ids = source_ids - target_ids
    clips = {
        part.name: part.shape for part in current_parts if part.name in retained_ids
    }
    if set(clips) != retained_ids:
        raise ValueError("source parts changed; retained legacy clips are incomplete")
    return clips


def _target_hosts(source: Any) -> dict[str, cq.Shape]:
    """Apply the shared WJ-04 retained-opening policy to each target station."""
    raw = {part.name: part.shape for part in source.uncut_wood_parts()}
    source_parts = tuple(source.parts())
    source_finished = {
        part.name: part.shape for part in source_parts if part.name in raw
    }
    connections = source.connections()
    template_rail = next(
        member for member in WJ04_TRIAL.members if member.role == "rail"
    )
    template_upright = next(
        member for member in WJ04_TRIAL.members if member.role == "principal"
    )
    result: dict[str, cq.Shape] = {}
    side_variants: list[cq.Shape] = []
    for station_id, rail_id in (
        (LOWER_STATION, LOWER_RAIL),
        (UPPER_STATION, UPPER_RAIL),
    ):
        adapter = replace(
            WJ04_TRIAL,
            station_id=station_id,
            members=(
                replace(
                    template_rail,
                    member_id=f"{station_id}_rail",
                    source_part_id=rail_id,
                ),
                replace(
                    template_upright,
                    member_id=f"{station_id}_side",
                    source_part_id=SIDE_HOST,
                ),
            ),
        )
        station_hosts = wj04_base._retained_source_hosts(
            adapter, source, raw, source_finished, connections
        )
        result[rail_id] = station_hosts[rail_id]
        side_variants.append(station_hosts[SIDE_HOST])
    if set(result) != {LOWER_RAIL, UPPER_RAIL} or len(side_variants) != 2:
        raise ValueError("shared WJ-04 opening policy missed an outer-pair host")
    # Each station adapter retains the other station's six original SDS holes.
    # Their common source-cut geometry is identical, so unioning the two host
    # variants restores only both target sets while preserving shared cuts.
    result[SIDE_HOST] = side_variants[0].fuse(side_variants[1]).clean()
    return result


@dataclass(frozen=True)
class OuterPairGeometry:
    source: Any
    source_binding: Any
    inventory: dict[str, Any]
    duties: dict[str, dict[str, Any]]
    removed_axis_ids: set[str]
    all_wood: dict[str, cq.Shape]
    hosts: dict[str, cq.Shape]
    cleats: dict[str, cq.Shape]
    parts: dict[str, cq.Shape]
    finished: dict[str, cq.Shape]
    stacks: dict[str, BoltStack]
    bores: dict[str, cq.Shape]
    bore_reports: dict[str, dict[str, Any]]
    protected: dict[str, dict[str, cq.Shape]]
    panels: dict[str, cq.Shape]
    candidate_neighbors: dict[str, cq.Shape]
    contact_area_mm2: dict[str, dict[str, float]]
    body_hits: dict[str, dict[str, Any]]
    installed: dict[str, dict[str, cq.Shape]]


def materialize_geometry(source: Any | None = None) -> OuterPairGeometry:
    """Materialize source-finished hosts, two cleats, eight stacks, and bores."""
    inv = _inventory()
    duties = _selected_duties(inv)
    if source is None:
        source = variant(KERF_RIGHT)
    binding = validate_source_binding(source)
    if binding.inventory_sha256 != WJ04_TRIAL.source_inventory_sha256:
        raise ValueError(
            "materialized source differs from the canonical source inventory"
        )
    removed_ids = {
        axis["axis_id"] for row in duties.values() for axis in row["legacy_sds_axes"]
    }
    hosts = _target_hosts(source)

    current_parts = tuple(source.parts())
    uncut_parts = tuple(source.uncut_wood_parts())
    wood_names = {part.name for part in uncut_parts}
    # Keep non-target wood at its real source-finished geometry. Source parts
    # also include clip hardware; classify that separately below.
    all_wood = {
        part.name: part.shape
        for part in current_parts
        if part.name in wood_names
        and part.name not in {LOWER_RAIL, UPPER_RAIL, SIDE_HOST}
    }
    all_wood.update(hosts)
    parts = dict(hosts)
    cleats = {
        LOWER_CLEAT: wj04_base._box_in_trial_frame(
            WJ04_TRIAL, _expected_body_origin(LOWER_STATION), CLEAT_SIZE_MM
        ),
        UPPER_CLEAT: wj04_base._box_in_trial_frame(
            WJ04_TRIAL, _expected_body_origin(UPPER_STATION), CLEAT_SIZE_MM
        ),
    }
    parts.update(cleats)

    source_panels = {
        part.name: part.shape
        for part in current_parts
        if part.name.startswith(("main_", "kicker_"))
    }
    panels, _ = wj04_base._candidate_panel_obstacles(
        source, source_panels, current_parts, uncut_parts
    )
    all_wood.update(panels)
    protected = wj06_residual._obstacles(source, inv)
    protected["retained_legacy_clips"] = _retained_source_clips(current_parts, inv)
    raw_wood = {part.name: part.shape for part in uncut_parts}
    candidate_neighbors = {
        **make_wj03_trial_parts("left", raw_wood),
        **make_wj03_trial_parts("right", raw_wood),
        "wj04_workhorse_candidate": wj06_residual._wj04_body(raw_wood),
    }
    stacks = build_stacks()

    # Candidate holes are only envelopes in this diagnostic; they are not
    # drilling instructions. Keep their interaction with all finished hosts,
    # panels, protected items, and peer axes in the returned evidence.
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
        layer_fractions: dict[str, float] = {}
        for layer in stack.layers:
            segment = cq.Solid.makeCylinder(
                stack.hardware.drill_diameter_mm / 2,
                layer.thickness_mm,
                stack.head_seat.center + direction * progress,
                direction,
            )
            layer_fractions[layer.body_id] = round(
                _volume(segment, parts[layer.body_id]) / segment.Volume(), 6
            )
            progress += layer.thickness_mm
        intended = {layer.body_id for layer in stack.layers}
        bore_reports[stack_id] = {
            "layer_material_fractions_before_new_bore": layer_fractions,
            "other_finished_wood_hits_mm3": _hits(
                bore,
                {
                    name: shape
                    for name, shape in all_wood.items()
                    if name not in intended
                },
            ),
            "candidate_panel_hits_mm3": _hits(bore, panels),
            "protected_hits_mm3": {
                family: hits
                for family, shapes in protected.items()
                if (hits := _hits(bore, shapes))
            },
        }

    cross_bores: dict[str, dict[str, float]] = {name: {} for name in bores}
    for first_id, first in bores.items():
        for second_id, second in bores.items():
            if first_id >= second_id:
                continue
            overlap = _volume(first, second)
            if overlap > HIT_TOLERANCE_MM3:
                cross_bores[first_id][second_id] = round(overlap, 6)
                cross_bores[second_id][first_id] = round(overlap, 6)
    for stack_id, report in bore_reports.items():
        report["peer_bore_hits_mm3"] = cross_bores[stack_id]

    finished = _finished_members_with_bores(parts, stacks, bores)

    installed = {name: stack.installed_shapes() for name, stack in stacks.items()}
    body_hits: dict[str, dict[str, Any]] = {}
    for station_id, cleat_id, rail_id in (
        (LOWER_STATION, LOWER_CLEAT, LOWER_RAIL),
        (UPPER_STATION, UPPER_CLEAT, UPPER_RAIL),
    ):
        body = cleats[cleat_id]
        host_ids = (rail_id, SIDE_HOST)
        body_hits[station_id] = {
            "intended_host_penetration_mm3": {
                host_id: round(_volume(body, hosts[host_id]), 6)
                for host_id in host_ids
                if _volume(body, hosts[host_id]) > HIT_TOLERANCE_MM3
            },
            "other_finished_timber_hits_mm3": _hits(
                body,
                {
                    name: shape
                    for name, shape in all_wood.items()
                    if name not in host_ids
                },
            ),
            "candidate_neighbor_body_hits_mm3": _hits(body, candidate_neighbors),
            "candidate_panel_hits_mm3": _hits(body, panels),
            "protected_hits_mm3": {
                family: hits
                for family, shapes in protected.items()
                if (hits := _hits(body, shapes))
            },
        }

    contacts: dict[str, dict[str, float]] = {}
    t_axis = cq.Vector(*WJ04_TRIAL.frame.t_global)
    x_axis = cq.Vector(*WJ04_TRIAL.frame.x_global)
    for station_id, cleat_id, rail_id in (
        (LOWER_STATION, LOWER_CLEAT, LOWER_RAIL),
        (UPPER_STATION, UPPER_CLEAT, UPPER_RAIL),
    ):
        body = cleats[cleat_id]
        contacts[station_id] = {
            "rail_to_cleat_area_mm2": round(
                body.translate(-t_axis * CONTACT_PROBE_MM)
                .intersect(hosts[rail_id])
                .Volume()
                / CONTACT_PROBE_MM,
                6,
            ),
            "side_to_cleat_area_mm2": round(
                body.translate(x_axis * CONTACT_PROBE_MM)
                .intersect(hosts[SIDE_HOST])
                .Volume()
                / CONTACT_PROBE_MM,
                6,
            ),
            "expected_full_face_patch_mm2": round(
                CLEAT_SIZE_MM[0] * CLEAT_SIZE_MM[2], 6
            ),
            "geometry_status": "thin-probe contact area only; no load-transfer inference",
        }
    return OuterPairGeometry(
        source=source,
        source_binding=binding,
        inventory=inv,
        duties=duties,
        removed_axis_ids=removed_ids,
        all_wood=all_wood,
        hosts=hosts,
        cleats=cleats,
        parts=parts,
        finished=finished,
        stacks=stacks,
        bores=bores,
        bore_reports=bore_reports,
        protected=protected,
        panels=panels,
        candidate_neighbors=candidate_neighbors,
        contact_area_mm2=contacts,
        body_hits=body_hits,
        installed=installed,
    )


def _materialized_report(geometry: OuterPairGeometry) -> dict[str, Any]:
    finished_timber = {**geometry.all_wood, **geometry.finished}
    stack_rows = []
    for spec in STACK_SPECS:
        stack = geometry.stacks[spec.stack_id]
        shapes = geometry.installed[spec.stack_id]
        timber_hits = _installed_component_timber_hits(shapes, finished_timber)
        installed_hits = {
            component: {
                "finished_timber": timber_hits.get(component, {}),
                "protected": {
                    family: hits
                    for family, obstacles in geometry.protected.items()
                    if (hits := _hits(shape, obstacles))
                },
                "candidate_neighbors": _hits(shape, geometry.candidate_neighbors),
            }
            for component, shape in shapes.items()
        }
        head_support = washer_support_report(
            stack.head_seat,
            geometry.finished[stack.head_seat.body_id],
            stack.hardware,
        )
        nut_support = washer_support_report(
            stack.nut_seat,
            geometry.finished[stack.nut_seat.body_id],
            stack.hardware,
        )
        stack_rows.append(
            {
                "stack_id": spec.stack_id,
                "axis_point_global_xyz_mm": _rounded_vec(stack.head_seat.center),
                "axis_direction_global_xyz": _rounded_vec(stack.direction, 9),
                "wood_layers_head_to_nut": [
                    {"member_id": name, "thickness_mm": thickness}
                    for name, thickness in spec.layers
                ],
                "grip_mm": stack.grip_mm,
                "under_head_length_nominal_mm": spec.nominal_bolt_length_mm,
                "minimum_length_bound_mm": spec.minimum_length_mm,
                "length_margin_nominal_mm": round(
                    spec.nominal_bolt_length_mm
                    - (
                        stack.grip_mm
                        + 2 * stack.hardware.washer_thickness_mm
                        + stack.hardware.nut_height_mm
                        + stack.required_tip_projection_mm
                    ),
                    6,
                ),
                "length_margin_at_bound_mm": round(
                    spec.minimum_length_mm
                    - (
                        stack.grip_mm
                        + 2 * stack.hardware.washer_thickness_mm
                        + stack.hardware.nut_height_mm
                        + stack.required_tip_projection_mm
                    ),
                    6,
                ),
                "head_washer_support": {
                    "body_id": head_support.body_id,
                    "support_fraction": round(head_support.support_fraction, 6),
                    "unsupported_area_mm2": round(head_support.unsupported_area_mm2, 6),
                    "full_seat": head_support.full_seat,
                },
                "nut_washer_support": {
                    "body_id": nut_support.body_id,
                    "support_fraction": round(nut_support.support_fraction, 6),
                    "unsupported_area_mm2": round(nut_support.unsupported_area_mm2, 6),
                    "full_seat": nut_support.full_seat,
                },
                "installed_component_hits": installed_hits,
                "thread_transition_status": (
                    "unresolved; side interval is a non-evidence sentinel"
                    if spec.interface_id == "cleat_to_side"
                    else "unresolved; ring-gage bound does not locate first full-form thread"
                ),
                "capacity_status": "not evaluated",
            }
        )

    cross_stack_hits = {}
    stack_ids = [spec.stack_id for spec in STACK_SPECS]
    for i, first_id in enumerate(stack_ids):
        for second_id in stack_ids[i + 1 :]:
            intersections = {}
            for first_role, first_shape in geometry.installed[first_id].items():
                for second_role, second_shape in geometry.installed[second_id].items():
                    overlap = _volume(first_shape, second_shape)
                    if overlap > HIT_TOLERANCE_MM3:
                        intersections[f"{first_role}/{second_role}"] = round(overlap, 6)
            if intersections:
                cross_stack_hits[f"{first_id}__{second_id}"] = intersections

    removed_opening_fractions = {}
    by_connection = {row.name: row for row in geometry.source.connections()}
    raw_parts = {part.name: part.shape for part in geometry.source.uncut_wood_parts()}
    for axis_id in sorted(geometry.removed_axis_ids):
        connection = by_connection[axis_id]
        host_id = next(
            member for member in connection.members if member in geometry.hosts
        )
        direction = connection.direction.normalized()
        former_opening = cq.Solid.makeCylinder(
            connection.diameter / 2,
            connection.length + 2.0,
            connection.start - direction,
            direction,
        ).intersect(raw_parts[host_id])
        raw_volume = former_opening.Volume()
        remaining_solid_volume = _volume(former_opening, geometry.hosts[host_id])
        removed_opening_fractions[axis_id] = (
            round(remaining_solid_volume / raw_volume, 6) if raw_volume else None
        )

    return {
        "materialized": True,
        "source_binding": {
            "inventory_sha256": geometry.source_binding.inventory_sha256,
            "uncut_part_shapes_sha256": geometry.source_binding.uncut_part_shapes_sha256,
            "fixed_screw_axes_sha256": geometry.source_binding.fixed_screw_axes_sha256,
            "frame_bolt_axes_sha256": geometry.source_binding.frame_bolt_axes_sha256,
        },
        "opening_policy": {
            "removed_old_sds_axis_ids": sorted(geometry.removed_axis_ids),
            "removed_old_sds_axis_count": len(geometry.removed_axis_ids),
            "other_source_cuts_reapplied": True,
            "fixed_66_purchased_openings_reapplied": True,
            "removed_opening_material_fraction": removed_opening_fractions,
            "old_holes_are_not_reused": True,
        },
        "obstacle_counts": {
            "finished_source_timber_members": len(geometry.all_wood),
            "fixed_66_axis_envelopes": len(
                geometry.protected["fixed_66_hillman_axes_63p5mm"]
            ),
            "starting_12_installed_bolt_components": len(
                geometry.protected["retained_12_frame_bolt_components"]
            ),
            "starting_12_tool_withdrawal_envelopes": len(
                geometry.protected["retained_12_frame_bolt_tools_withdrawals"]
            ),
            "retained_legacy_clip_bodies": len(
                geometry.protected["retained_legacy_clips"]
            ),
            "hold_tnuts": len(geometry.protected["tnuts"]),
            "hold_projection_paths": len(
                geometry.protected["hold_hole_and_provisional_projection"]
            ),
            "lights": len(geometry.protected["lights"]),
            "wires": len(geometry.protected["wires"]),
            "candidate_neighbor_bodies": len(geometry.candidate_neighbors),
        },
        "station_checks": {
            station_id: {
                **geometry.body_hits[station_id],
                "contact_area_mm2": geometry.contact_area_mm2[station_id],
            }
            for station_id in (LOWER_STATION, UPPER_STATION)
        },
        "bores": geometry.bore_reports,
        "stacks": stack_rows,
        "cross_stack_installed_component_hits_mm3": cross_stack_hits,
        "assembly_status": {
            "side_released_for_plus_n_insertion": "external prerequisite only; not modeled in installed-state geometry",
            "insertion_sweep_tested": False,
            "wrench_access_tested": False,
            "assembly_sequence_proven": False,
        },
        "claim_boundary": {
            "accepted_replacement_count": 0,
            "capacity_established": False,
            "drilling_released": False,
            "fabrication_released": False,
            "purchase_approved": False,
            "structural_accepted": False,
            "assembly_proven": False,
        },
    }


def build_report(*, materialize: bool = False) -> dict[str, Any]:
    plan = trial_plan()
    report: dict[str, Any] = {
        **plan,
        "source_inputs_sha256": {name: _sha(ROOT / name) for name in SOURCE_INPUTS},
        "producer_sha256": _sha(Path(__file__)),
        "producer_command": "uv run python -m scripts.wood_joint_wj06_outer_pair_probe --materialize",
        "materialized_geometry": False,
    }
    if materialize:
        report["materialized_geometry"] = _materialized_report(materialize_geometry())
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--materialize",
        action="store_true",
        help="build source-bound CAD geometry and emit installed-state checks",
    )
    args = parser.parse_args()
    print(
        json.dumps(build_report(materialize=args.materialize), indent=2, sort_keys=True)
    )


if __name__ == "__main__":
    main()
