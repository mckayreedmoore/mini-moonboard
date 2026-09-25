"""Source-bound provisional top-center cleat pair; never a fabrication release.

This producer consumes the retained WJ18 composition. It adds only the two
top-center duties and exports source cuts, candidate bores, and hardware for a
later complete-layout merge. It does not materialize a family or run mechanics.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import (
    _source_shape_fingerprint,
    access_shapes,
    validate_source_binding,
)
from mini_moonboard.wood_joint_geometry import BoltStack
from mini_moonboard.wood_joint_panel_machining import PANEL_NAMES
from scripts import wood_joint_right_rail_integration as right_rail
from scripts import wood_joint_top_outer_integration as top_outer
from scripts import wood_joint_wj06_outer_pair_probe as wj06_outer
from scripts import wood_joint_wj12_compositor as wj12
from scripts import wood_joint_wj18_compositor as wj18

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
SCHEMA = "wood_joint_top_center_integration/v1"
TRIAL_ID = "top_center_full_stock_pair_v1"
TARGET_DUTY_IDS = frozenset(
    {"clip_split_top_center_left", "clip_split_top_center_right"}
)
HOST_IDS = frozenset(
    {"base_rail_top", "base_principal_center_left", "base_principal_center_right"}
)
CLEAT_IDS = {
    "clip_split_top_center_left": "top_center_left_cleat",
    "clip_split_top_center_right": "top_center_right_cleat",
}
EXPECTED_CLEAT_SIZE_MM = (88.9, 88.9, 119.7)  # X, T, N; full 4x4 section
CLEAT_T_MIN_MM = -88.9
CLEAT_T_MAX_MM = 0.0
CLEAT_N_MIN_MM = 20.0
CLEAT_N_MAX_MM = 139.7
RAIL_BOLT_N_OFFSETS_MM = (-14.4, 14.4)
PRINCIPAL_BOLT_T_OFFSETS_MM = (-60.9, -27.9)
RAIL_ROW_SIGNED_X_OFFSET_MM = 1.0
WOOD_LAYER_THICKNESS_MM = 38.1
WOOD_LAYER_TOLERANCE_MM = 0.5
WASHER_THICKNESS_MIN_MM = 1.2954
WASHER_THICKNESS_MAX_MM = 2.032
NUT_THICKNESS_MAX_MM = 5.7404
TIP_PROJECTION_MM = 2.54
SUPPORT_PROBE_MM = 0.05
LAYER_PROBE_MM = 0.1
HIT_TOLERANCE_MM3 = 1e-5
AXIS_TOLERANCE_MM = 1e-6
SOURCE_RECONSTRUCTION_TOLERANCE_MM3 = 1e-3
NOMINAL_BOLT_DIAMETER_MM = 6.35
CONDITIONAL_7D_MM = 7 * NOMINAL_BOLT_DIAMETER_MM
ORDINARY_BOLT_LENGTH_MM = wj06_outer.RAIL_BOLT_LENGTH_MM
ORDINARY_BOLT_MIN_LENGTH_MM = wj06_outer.RAIL_BOLT_MIN_LENGTH_MM
ORDINARY_COMPONENT_ROLES = frozenset(
    {"shaft", "head", "head_washer", "nut_washer", "nut"}
)
RELEASE_FLAGS = (
    "candidate_accepted",
    "source_cutting_released",
    "drilling_released",
    "fabrication_released",
    "structural_accepted",
    "assembly_proven",
)

TOP_AXIS_STATION_IDS = {
    f"top_center/{duty_id}/{role}_{index}": duty_id
    for duty_id in sorted(TARGET_DUTY_IDS)
    for role in ("rail", "principal")
    for index in (1, 2)
}
TOP_CANDIDATE_AXIS_IDS = frozenset(TOP_AXIS_STATION_IDS)
TOP_CANDIDATE_PART_IDS = frozenset(CLEAT_IDS.values())

PRODUCER_HASH_PATHS = {
    "top_center_producer": "scripts/wood_joint_top_center_integration.py",
    "source_inventory": INVENTORY_PATH,
    "wj18_compositor": "scripts/wood_joint_wj18_compositor.py",
    "wj18_diagnostic": "scripts/wood_joint_wj18_diagnostic.py",
    "top_outer_producer": "scripts/wood_joint_top_outer_integration.py",
    "wj16_compositor": "scripts/wood_joint_wj16_compositor.py",
    "wj16_diagnostic": "scripts/wood_joint_wj16_diagnostic.py",
    "wj12_compositor": "scripts/wood_joint_wj12_compositor.py",
    "wj12_diagnostic": "scripts/wood_joint_wj12_diagnostic.py",
    "right_rail_integration": "scripts/wood_joint_right_rail_integration.py",
    "wj06_hardware_basis": "scripts/wood_joint_wj06_outer_pair_probe.py",
    "frame_geometry": "mini_moonboard/wood_joint_frame.py",
    "joint_geometry": "mini_moonboard/wood_joint_geometry.py",
    "panel_machining": "mini_moonboard/wood_joint_panel_machining.py",
}


@dataclass(frozen=True)
class TopCenterIntegrationGeometry:
    """Candidate delta over one retained WJ18 composition."""

    source: Any
    source_binding: Any
    source_inventory: Mapping[str, Any]
    source_inputs_sha256: Mapping[str, str]
    family_source_fingerprints: Mapping[str, Mapping[str, str]]
    family_trial_ids: Mapping[str, str]
    retained_layout_id: str
    retained_trial_id: str
    retained_counts: Mapping[str, int]
    trial_id: str
    duties: Mapping[str, Mapping[str, Any]]
    raw_candidate_parts: Mapping[str, cq.Shape]
    finished_candidate_parts: Mapping[str, cq.Shape]
    candidate_bores: Mapping[str, Any]
    candidate_bores_by_host: Mapping[str, Mapping[str, cq.Shape]]
    candidate_installed_hardware: Mapping[str, Mapping[str, cq.Shape]]
    source_native_cutters_by_host: Mapping[str, Mapping[str, cq.Shape]]
    source_panel_purchase_cutters_by_host: Mapping[str, Mapping[str, cq.Shape]]
    candidate_panel_purchase_cutters_by_part: Mapping[str, Mapping[str, cq.Shape]]
    replaced_source_axis_ids: frozenset[str]
    replaced_source_cutter_ids: frozenset[str]
    source_reconstruction: Mapping[str, Mapping[str, Any]]
    contact_checks: Mapping[str, Mapping[str, Any]]
    layer_checks: Mapping[str, Mapping[str, Any]]
    washer_support: Mapping[str, Mapping[str, Any]]
    candidate_body_checks: Mapping[str, Mapping[str, Any]]
    installed_component_checks: Mapping[str, Mapping[str, Any]]
    access_checks: Mapping[str, Mapping[str, Any]]
    source_face_evidence: Mapping[str, Mapping[str, Any]]
    placement_evidence: Mapping[str, Mapping[str, Any]]
    stack_rows: Mapping[str, Mapping[str, Any]]
    source_axis_entry_face_audit: Mapping[str, Mapping[str, Any]]
    conditional_edge_screen: Mapping[str, Any]
    dimensional_fit_screen: Mapping[str, Any]
    diagnostic_gates: Mapping[str, bool]
    release: Mapping[str, bool]
    status: str = "unaccepted_integrated_hypothesis"

    @property
    def counts(self) -> dict[str, int]:
        return {
            "target_duties": len(self.duties),
            "replaced_source_sds_axes": len(self.replaced_source_axis_ids),
            "candidate_cleats": len(self.raw_candidate_parts),
            "candidate_bores": len(self.candidate_bores),
            "candidate_installed_hardware_axes": len(
                self.candidate_installed_hardware
            ),
            "candidate_installed_cad_roles": sum(
                len(roles) for roles in self.candidate_installed_hardware.values()
            ),
            "candidate_washers": 2 * len(self.candidate_installed_hardware),
            "source_native_host_maps": len(self.source_native_cutters_by_host),
            "source_panel_purchase_host_maps": len(
                self.source_panel_purchase_cutters_by_host
            ),
            "source_finished_host_overrides_exported": 0,
        }


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def _readonly(values: Mapping) -> Mapping:
    return MappingProxyType(dict(values))


def _nested_readonly(values: Mapping[str, Mapping]) -> Mapping:
    return MappingProxyType(
        {name: MappingProxyType(dict(rows)) for name, rows in values.items()}
    )


def _readonly_tree(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _readonly_tree(item) for key, item in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_readonly_tree(item) for item in value)
    return value


def _sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def _unit(value: Any, name: str) -> cq.Vector:
    vector = cq.Vector(value)
    if not all(math.isfinite(value) for value in vector.toTuple()) or vector.Length < 1e-9:
        raise ValueError(f"{name} must be finite and nonzero")
    return vector.normalized()


def _vec(values: Any, name: str) -> cq.Vector:
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        raise ValueError(f"{name} must be a three-vector")
    return cq.Vector(*(float(value) for value in values))


def _tuple(vector: cq.Vector, digits: int = 6) -> list[float]:
    return [round(value, digits) for value in vector.toTuple()]


def _intersection_volume(first: cq.Shape, second: cq.Shape) -> float:
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


def _hits(shape: cq.Shape, obstacles: Mapping[str, cq.Shape]) -> dict[str, float]:
    return {
        name: round(volume, 6)
        for name, obstacle in sorted(obstacles.items())
        if (volume := _intersection_volume(shape, obstacle)) > HIT_TOLERANCE_MM3
    }


def _valid_shape(shape: Any, name: str) -> cq.Shape:
    if not isinstance(shape, cq.Shape) or not shape.isValid() or not shape.Solids():
        raise ValueError(f"{name} must be valid positive-volume solid geometry")
    if shape.Volume() <= 0:
        raise ValueError(f"{name} must have positive volume")
    return shape


def _source_parts(source: Any, method_name: str) -> dict[str, cq.Shape]:
    rows = tuple(getattr(source, method_name)())
    result = {row.name: row.shape for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"{method_name} returned duplicate part names")
    return result


def _frame_for_part(inventory: Mapping[str, Any], part_id: str) -> top_outer.SourceLocalFrame:
    rows = {row["part_id"]: row for row in inventory.get("parts", ())}
    row = rows.get(part_id)
    matrix = row.get("local_to_global_transform") if row else None
    axes = row.get("local_axes") if row else None
    if not isinstance(matrix, list) or len(matrix) != 4 or not isinstance(axes, Mapping):
        raise ValueError(f"source inventory lacks a frame for {part_id}")
    frame = top_outer.SourceLocalFrame(
        origin=cq.Vector(matrix[0][3], matrix[1][3], matrix[2][3]),
        x=_unit(axes["X"], f"{part_id}.X"),
        t=_unit(axes["T"], f"{part_id}.T"),
        n=_unit(axes["N"], f"{part_id}.N"),
    )
    if (
        abs(frame.x.dot(frame.t)) > 1e-8
        or abs(frame.x.dot(frame.n)) > 1e-8
        or abs(frame.t.dot(frame.n)) > 1e-8
        or frame.x.cross(frame.t).dot(frame.n) < 1 - 1e-8
    ):
        raise ValueError(f"source inventory frame is not right-handed: {part_id}")
    return frame


def _part_rows(inventory: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["part_id"]: dict(row) for row in inventory.get("parts", ())}


def _duty_rows(inventory: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    all_rows = {
        row["legacy_station_id"]: dict(row)
        for row in inventory.get("legacy_duties", ())
    }
    rows = {name: all_rows[name] for name in TARGET_DUTY_IDS if name in all_rows}
    expected_hosts = {
        "clip_split_top_center_left": [
            "base_rail_top",
            "base_principal_center_left",
        ],
        "clip_split_top_center_right": [
            "base_rail_top",
            "base_principal_center_right",
        ],
    }
    if set(rows) != TARGET_DUTY_IDS:
        raise ValueError("top-center slice requires exactly its two source duties")
    axis_ids = set()
    for duty_id, row in rows.items():
        if row.get("legacy_host_members") != expected_hosts[duty_id]:
            raise ValueError(f"{duty_id}: source host mapping changed")
        axes = row.get("legacy_sds_axes", ())
        if len(axes) != 6:
            raise ValueError(f"{duty_id}: expected six source SDS axes")
        for axis in axes:
            if (
                axis.get("shop_opening_kind") != "sds_wood"
                or axis.get("members", [None, None])[0] != duty_id
                or axis.get("members", [None, None])[1]
                not in expected_hosts[duty_id]
            ):
                raise ValueError(f"{duty_id}: invalid source SDS identity")
            axis_ids.add(axis["axis_id"])
    if len(axis_ids) != 12:
        raise ValueError("top-center slice must replace exactly 12 unique source axes")
    return rows


def _expected_source_axis_ids(duties: Mapping[str, Mapping[str, Any]]) -> frozenset[str]:
    return frozenset(
        axis["axis_id"]
        for row in duties.values()
        for axis in row["legacy_sds_axes"]
    )


def _proposed_placement(left_outer_face_x: float, right_outer_face_x: float) -> dict[str, Any]:
    """Return the explicitly provisional outboard-face placement in rail X."""
    size_x = EXPECTED_CLEAT_SIZE_MM[0]
    left_x_hi = float(left_outer_face_x)
    left_x_lo = left_x_hi - size_x
    right_x_lo = float(right_outer_face_x)
    right_x_hi = right_x_lo + size_x
    n_center = CLEAT_N_MIN_MM + EXPECTED_CLEAT_SIZE_MM[2] / 2
    rail_n = tuple(n_center + offset for offset in RAIL_BOLT_N_OFFSETS_MM)
    return {
        "left": {
            "x_interval_mm": [left_x_lo, left_x_hi],
            "rail_row_x_mm": (left_x_lo + left_x_hi) / 2 + RAIL_ROW_SIGNED_X_OFFSET_MM,
            "rail_bolt_n_mm": rail_n,
            "principal_bolt_x_mm": left_x_lo,
            "principal_bolt_direction_sign_x": 1.0,
        },
        "right": {
            "x_interval_mm": [right_x_lo, right_x_hi],
            "rail_row_x_mm": (right_x_lo + right_x_hi) / 2 - RAIL_ROW_SIGNED_X_OFFSET_MM,
            "rail_bolt_n_mm": rail_n,
            "principal_bolt_x_mm": right_x_hi,
            "principal_bolt_direction_sign_x": -1.0,
        },
        "cleat_T_interval_mm": [CLEAT_T_MIN_MM, CLEAT_T_MAX_MM],
        "cleat_N_interval_mm": [CLEAT_N_MIN_MM, CLEAT_N_MAX_MM],
        "principal_bolt_t_mm": PRINCIPAL_BOLT_T_OFFSETS_MM,
        "inward_face_pair_overlap_if_used_mm": max(
            0.0,
            2 * size_x
            - (
                float(right_outer_face_x)
                - float(left_outer_face_x)
                - 2 * WOOD_LAYER_THICKNESS_MM
            ),
        ),
    }


def _context_identity(geometry: Any) -> dict[str, int]:
    if (
        getattr(geometry, "layout_id", None) != wj18.LAYOUT_ID
        or getattr(geometry, "trial_id", None) != wj18.TRIAL_ID
    ):
        raise ValueError("top-center integration requires the fixed retained WJ18 composition")
    expected_counts = {
        "target_duties": 18,
        "source_hosts": 14,
        "replaced_source_sds_axes": 108,
        "candidate_bores": 80,
        "candidate_installed_hardware_components": 400,
        "candidate_parts": 22,
        "fixed_panel_axes": 66,
        "retained_frame_bolts": 12,
        "retained_frame_bolt_shapes": 72,
        "retained_legacy_clips": 6,
        "retained_legacy_sds_axes": 36,
    }
    counts = dict(geometry.counts)
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            raise ValueError(f"WJ18 {key} count differs from {expected}")
    if set(geometry.target_station_ids) != wj18.EXPECTED_TARGET_DUTY_IDS:
        raise ValueError("WJ18 target duty IDs differ from the exact eighteen-duty contract")
    if set(geometry.finished_hosts) != wj18.EXPECTED_SOURCE_HOST_IDS:
        raise ValueError("WJ18 finished host IDs differ from the exact fourteen-host contract")
    if set(geometry.candidate_bores) != wj18.EXPECTED_CANDIDATE_AXIS_IDS:
        raise ValueError("WJ18 candidate axis IDs differ from the exact 80-axis contract")
    if set(geometry.candidate_installed_hardware) != wj18.EXPECTED_CANDIDATE_AXIS_IDS:
        raise ValueError("WJ18 installed hardware axis IDs differ from the exact 80-axis contract")
    if sum(len(rows) for rows in geometry.candidate_installed_hardware.values()) != 400:
        raise ValueError("WJ18 must preserve exactly 400 installed hardware CAD roles")
    if set(geometry.finished_candidate_parts) != wj18.EXPECTED_CANDIDATE_PART_IDS:
        raise ValueError("WJ18 candidate part IDs differ from the exact 22-part contract")
    required_composition_checks = {
        "exact_wj16_base_contract",
        "exact_top_outer_two_duty_contract",
        "source_inventory_and_family_hashes_current",
        "all_108_source_sds_axes_replaced",
        "top_rail_purchase_overlay_absorbed_into_host_map",
        "two_bottom_rail_overlays_and_four_cuts_preserved",
        "native_and_purchase_maps_remain_distinct",
        "four_existing_backer_receiver_redirects_preserved",
        "all_80_candidate_axes_and_400_cad_roles_preserved",
        "candidate_axis_station_bindings_match_exact_contract",
        "all_14_shared_hosts_rebuilt_from_union_cut_maps_and_bores",
        "source_reconstruction_evidence_covers_all_14_hosts",
        "all_66_fixed_axes_and_12_frame_bolts_preserved",
    }
    observed_checks = dict(geometry.composition_checks)
    if not required_composition_checks <= observed_checks.keys() or any(
        observed_checks[name] is not True for name in required_composition_checks
    ):
        raise ValueError("WJ18 source/composition evidence is incomplete or failed")
    if len(geometry.fixed_axes) != 66:
        raise ValueError("WJ18 must retain all 66 fixed panel/kicker axes")
    if len(geometry.frame_bolt_records) != 12 or len(geometry.frame_bolt_shapes) != 72:
        raise ValueError("WJ18 frame-bolt inventory must remain twelve bolts and 72 shapes")
    return {key: int(value) for key, value in counts.items()}


def _validate_live_connections(
    source: Any,
    inventory: Mapping[str, Any],
    duties: Mapping[str, Mapping[str, Any]],
) -> None:
    connections = tuple(source.connections())
    by_name = {row.name: row for row in connections}
    if len(by_name) != len(connections):
        raise ValueError("source connection names must be unique")
    required = [
        axis for duty in duties.values() for axis in duty["legacy_sds_axes"]
    ]
    panel_rows = tuple(inventory.get("fixed_panel_kicker_screws", ()))
    if len(panel_rows) != 66:
        raise ValueError("top-center integration requires all 66 fixed panel axes")
    required.extend(panel_rows)
    for record in required:
        axis_id = record["axis_id"]
        live = by_name.get(axis_id)
        if live is None:
            raise ValueError(f"source connection missing inventory axis {axis_id}")
        start = _vec(record["origin_global_xyz_mm"], f"{axis_id} start")
        direction = _unit(record["axis_global_xyz"], f"{axis_id} direction")
        live_start = cq.Vector(live.start)
        live_direction = _unit(live.direction, f"{axis_id} live direction")
        expected_length = float(
            record.get("source_occupied_length_mm", record.get("shop_purchased_length_mm"))
        )
        if (start - live_start).Length > AXIS_TOLERANCE_MM:
            raise ValueError(f"{axis_id}: source start differs from canonical inventory")
        if direction.dot(live_direction) < 1 - 1e-8:
            raise ValueError(f"{axis_id}: source direction differs from canonical inventory")
        if not math.isclose(float(live.length), expected_length, abs_tol=AXIS_TOLERANCE_MM):
            raise ValueError(f"{axis_id}: source length differs from canonical inventory")


def _face_record(
    part_id: str,
    row: Mapping[str, Any],
    frame: top_outer.SourceLocalFrame,
    expected_normal: cq.Vector,
) -> dict[str, Any]:
    matches = []
    for face in row.get("actual_planar_faces", ()):
        normal = _unit(face.get("normal_global_xyz", ()), f"{part_id} face normal")
        if normal.dot(expected_normal) >= 1 - 1e-8:
            matches.append(dict(face))
    if len(matches) != 1:
        raise ValueError(
            f"{part_id}: expected one actual planar face normal to "
            f"{_tuple(expected_normal, 9)}, found {len(matches)}"
        )
    result = matches[0]
    result["center_local_in_top_rail_frame_mm"] = list(
        frame.coordinates(_vec(result["center_global_xyz_mm"], f"{part_id} face center"))
    )
    result["normal_global_xyz"] = _tuple(expected_normal, 9)
    return result


def _validate_aligned_host_frames(
    inventory: Mapping[str, Any], rail_frame: top_outer.SourceLocalFrame
) -> dict[str, top_outer.SourceLocalFrame]:
    result = {part_id: _frame_for_part(inventory, part_id) for part_id in HOST_IDS}
    for part_id, frame in result.items():
        if any(
            abs(a.dot(b) - expected) > 1e-8
            for a, b, expected in (
                (frame.x, rail_frame.x, 1.0),
                (frame.t, rail_frame.t, 1.0),
                (frame.n, rail_frame.n, 1.0),
            )
        ):
            raise ValueError(f"{part_id}: source frame is not aligned to the top rail frame")
    return result


def _placement_from_faces(
    inventory: Mapping[str, Any],
    rail_frame: top_outer.SourceLocalFrame,
    face_rows: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    part_rows = _part_rows(inventory)
    extents = {
        side: part_rows[f"base_principal_center_{side}"]["actual_shape_extents_local_mm"]["X"]
        for side in ("left", "right")
    }
    selected = {
        "left": face_rows["base_principal_center_left"],
        "right": face_rows["base_principal_center_right"],
    }
    local_x = {
        side: rail_frame.coordinates(
            _vec(face["center_global_xyz_mm"], f"principal {side} face center")
        )[0]
        for side, face in selected.items()
    }
    frames = _validate_aligned_host_frames(inventory, rail_frame)
    expected_face_x = {}
    for side, part_id in (
        ("left", "base_principal_center_left"),
        ("right", "base_principal_center_right"),
    ):
        low, high = (float(value) for value in extents[side])
        part_origin_x = rail_frame.coordinates(frames[part_id].origin)[0]
        expected_face_x[side] = part_origin_x + (low if side == "left" else high)
        if not math.isclose(local_x[side], expected_face_x[side], abs_tol=1e-4):
            raise ValueError(f"{part_id}: selected outboard face disagrees with stock X extent")
    placement = _proposed_placement(expected_face_x["left"], expected_face_x["right"])
    placement["selected_outboard_face_local_X_mm"] = local_x
    placement["principal_local_X_extents_mm"] = extents
    placement["source_face_ids"] = {
        host: row.get("face_id") for host, row in face_rows.items()
    }
    placement["rail_low_T_source_local_mm"] = 0.0
    placement["rail_source_local_origin_global_xyz_mm"] = _tuple(rail_frame.origin)
    placement["cleat_datum_global_xyz_mm"] = _tuple(rail_frame.origin)
    return placement


def _source_entry_audit(
    inventory: Mapping[str, Any],
    duties: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    part_rows = _part_rows(inventory)
    result = {}
    for duty in duties.values():
        for axis in duty["legacy_sds_axes"]:
            axis_id = axis["axis_id"]
            host_id = axis["members"][1]
            frame = _frame_for_part(inventory, host_id)
            result[axis_id] = top_outer._inventory_entry_face(
                axis,
                host_id,
                part_rows[host_id],
                frame,
            )
    return result


def _same_shape_maps(
    first: Mapping[str, cq.Shape], second: Mapping[str, cq.Shape], *, context: str
) -> None:
    if set(first) != set(second):
        raise ValueError(f"{context}: cutter IDs differ")
    for cut_id, shape in first.items():
        delta = top_outer._shape_difference_volume(shape, second[cut_id])
        if delta > 1e-6:
            raise ValueError(f"{context}/{cut_id}: cutter geometry differs by {delta:.9f} mm3")


def _source_reconstruction(
    source: Any,
    raw_hosts: Mapping[str, cq.Shape],
    native_cutters: Mapping[str, Mapping[str, cq.Shape]],
) -> dict[str, dict[str, Any]]:
    finished_source = _source_parts(source, "parts")
    records = {}
    for host_id in sorted(HOST_IDS):
        if host_id not in raw_hosts or host_id not in finished_source:
            raise ValueError(f"canonical source omitted reconstruction host {host_id}")
        tools = list(native_cutters[host_id].values())
        replayed = raw_hosts[host_id].cut(*tools).clean() if tools else raw_hosts[host_id]
        delta = replayed.cut(finished_source[host_id]).Volume() + finished_source[
            host_id
        ].cut(replayed).Volume()
        records[host_id] = {
            "native_source_cutter_ids": sorted(native_cutters[host_id]),
            "native_source_cutter_count": len(native_cutters[host_id]),
            "source_finished_shape_sha256": _source_shape_fingerprint(finished_source[host_id]),
            "replayed_shape_sha256": _source_shape_fingerprint(replayed),
            "symmetric_difference_mm3": round(delta, 9),
            "matches_canonical_source_finished_member": (
                delta <= SOURCE_RECONSTRUCTION_TOLERANCE_MM3
            ),
            "purchased_panel_cutters_in_native_reconstruction": False,
        }
    if any(not row["matches_canonical_source_finished_member"] for row in records.values()):
        raise ValueError("top-center native source reconstruction differs from canonical source")
    return records


def _compare_retained_source_maps(
    geometry: Any,
    native: Mapping[str, Mapping[str, cq.Shape]],
    purchase: Mapping[str, Mapping[str, cq.Shape]],
) -> None:
    retained_native = getattr(geometry, "source_cutters_by_host", {})
    retained_purchase = getattr(geometry, "purchased_panel_cutters_by_host", {})
    for host in HOST_IDS:
        if host not in retained_native or host not in retained_purchase:
            raise ValueError(f"WJ18 source cut maps omit shared top-center host {host}")
        _same_shape_maps(native[host], retained_native[host], context=f"WJ18 native map/{host}")
        _same_shape_maps(
            purchase[host], retained_purchase[host], context=f"WJ18 purchase map/{host}"
        )


def _preview_hosts(
    geometry: Any,
    raw_hosts: Mapping[str, cq.Shape],
    new_replaced_cutter_ids: frozenset[str],
    new_bores_by_host: Mapping[str, Mapping[str, cq.Shape]],
) -> tuple[dict[str, cq.Shape], dict[str, cq.Shape]]:
    applied = getattr(geometry, "applied_source_cutters_by_host", {})
    if set(applied) != wj18.EXPECTED_SOURCE_HOST_IDS:
        raise ValueError("WJ18 applied source cutter map differs from its fourteen-host contract")
    previous_bores = getattr(geometry, "candidate_bores", {})
    before: dict[str, cq.Shape] = {}
    after: dict[str, cq.Shape] = {}
    for host in HOST_IDS:
        source_tools = [
            shape
            for cut_id, shape in applied[host].items()
            if cut_id not in new_replaced_cutter_ids
        ]
        previous_tools = [
            bore.shape for bore in previous_bores.values() if host in bore.receiver_ids
        ]
        before_tools = [*source_tools, *previous_tools]
        before_shape = raw_hosts[host].cut(*before_tools).clean() if before_tools else raw_hosts[host]
        new_tools = list(new_bores_by_host[host].values())
        after_tools = [*before_tools, *new_tools]
        after_shape = raw_hosts[host].cut(*after_tools).clean() if after_tools else raw_hosts[host]
        before[host] = _valid_shape(before_shape, f"pre-top-center host/{host}")
        after[host] = _valid_shape(after_shape, f"finished top-center host/{host}")
    return before, after


def _candidate_scene(
    geometry: Any,
    source: Any,
    raw_source_parts: Mapping[str, cq.Shape],
    before_hosts: Mapping[str, cq.Shape],
    after_hosts: Mapping[str, cq.Shape],
) -> dict[str, cq.Shape]:
    canonical_finished = _source_parts(source, "parts")
    if not PANEL_NAMES <= canonical_finished.keys():
        raise ValueError("source must provide all six panels for the integration scene")
    scene = {
        name: shape
        for name, shape in canonical_finished.items()
        if name in raw_source_parts or name in PANEL_NAMES
    }
    scene.update(dict(geometry.finished_hosts))
    scene.update(dict(geometry.additional_finished_source_parts))
    scene.update(dict(geometry.panel_replacements))
    scene.update(before_hosts)
    scene.update(after_hosts)
    if not PANEL_NAMES <= scene.keys():
        raise ValueError("complete top-center scene omitted one or more source/replacement panels")
    return scene


def _layer_checks(
    stacks: Mapping[str, BoltStack],
    pre_bore_parts: Mapping[str, cq.Shape],
) -> dict[str, dict[str, Any]]:
    reports = {}
    for axis_id, stack in sorted(stacks.items()):
        direction = _unit(stack.direction, f"{axis_id} direction")
        progress = 0.0
        layer_rows = []
        for layer in stack.layers:
            start = stack.head_seat.center + direction * progress
            segment = cq.Solid.makeCylinder(
                stack.hardware.drill_diameter_mm / 2,
                layer.thickness_mm,
                start,
                direction,
            )
            volume = segment.Volume()
            material = _intersection_volume(segment, pre_bore_parts[layer.body_id])
            fraction = material / volume if volume else 0.0
            layer_rows.append(
                {
                    "member_id": layer.body_id,
                    "declared_layer_thickness_mm": layer.thickness_mm,
                    "source_material_fraction_before_new_bore": round(fraction, 9),
                    "full_declared_layer_present": fraction >= 1 - 1e-6,
                }
            )
            progress += layer.thickness_mm
        reports[axis_id] = {
            "layers_head_to_nut": layer_rows,
            "all_declared_layers_present": all(
                row["full_declared_layer_present"] for row in layer_rows
            ),
        }
    return reports


def _interface_slab(
    cleat: cq.Shape,
    frame: top_outer.SourceLocalFrame,
    host_id: str,
    face_x: float,
    depth_mm: float,
) -> cq.Shape:
    local = [frame.coordinates(vertex.Center()) for vertex in cleat.Vertices()]
    x_values, t_values, n_values = zip(*local, strict=True)
    x_lo, x_hi = min(x_values), max(x_values)
    t_lo, t_hi = min(t_values), max(t_values)
    n_lo, n_hi = min(n_values), max(n_values)
    if host_id == "base_rail_top":
        origin = frame.point(x_hi, CLEAT_T_MAX_MM, n_lo)
        plane = cq.Plane(origin=origin, xDir=-frame.x, normal=frame.t)
        length, width = x_hi - x_lo, n_hi - n_lo
    elif host_id == "base_principal_center_left":
        origin = frame.point(face_x, t_lo, n_lo)
        plane = cq.Plane(origin=origin, xDir=frame.t, normal=frame.x)
        length, width = t_hi - t_lo, n_hi - n_lo
    elif host_id == "base_principal_center_right":
        origin = frame.point(face_x, t_hi, n_lo)
        plane = cq.Plane(origin=origin, xDir=-frame.t, normal=-frame.x)
        length, width = t_hi - t_lo, n_hi - n_lo
    else:
        raise ValueError(f"unsupported top-center receiver host {host_id}")
    return cq.Workplane(plane).box(length, width, depth_mm, centered=False).val()


def _host_contact_checks(
    raw_cleats: Mapping[str, cq.Shape],
    finished_hosts: Mapping[str, cq.Shape],
    rail_frame: top_outer.SourceLocalFrame,
    face_rows: Mapping[str, Mapping[str, Any]],
    placement: Mapping[str, Mapping[str, Any]],
    bores_by_host: Mapping[str, Mapping[str, cq.Shape]],
) -> dict[str, dict[str, Any]]:
    checks = {}
    for duty_id, cleat_id in CLEAT_IDS.items():
        side = "left" if duty_id.endswith("left") else "right"
        principal_id = f"base_principal_center_{side}"
        host_ids = ("base_rail_top", principal_id)
        checks[cleat_id] = {}
        for host in host_ids:
            face = face_rows[host]
            face_center = _vec(face["center_global_xyz_mm"], f"{host} face center")
            normal = _unit(face["normal_global_xyz"], f"{host} face normal")
            live = top_outer._live_coplanar_face_check(
                finished_hosts[host],
                center=face_center,
                normal=normal,
                context=f"top-center/{host}",
            )
            host_x = (
                placement[side]["x_interval_mm"][1]
                if host == "base_principal_center_left"
                else placement[side]["x_interval_mm"][0]
            )
            if host == "base_rail_top":
                host_x = 0.0
            gross = _interface_slab(
                raw_cleats[cleat_id],
                rail_frame,
                host,
                host_x,
                SUPPORT_PROBE_MM,
            )
            intended_cutters = list(bores_by_host[cleat_id].values())
            net = gross.cut(*intended_cutters).clean() if intended_cutters else gross
            expected_volume = net.Volume()
            supported_volume = _intersection_volume(net, finished_hosts[host])
            fraction = supported_volume / expected_volume if expected_volume else 0.0
            checks[cleat_id][host] = {
                **live,
                "source_face_id": face.get("face_id"),
                "source_face_normal_global_xyz": _tuple(normal, 9),
                "support_probe_depth_mm": SUPPORT_PROBE_MM,
                "expected_net_contact_slab_mm3": round(expected_volume, 6),
                "supported_contact_slab_mm3": round(supported_volume, 6),
                "contact_slab_material_fraction": round(fraction, 9),
                "full_contact_slab_material_present": fraction >= 1 - 1e-6,
                "intended_new_bores_discounted_from_contact_area": True,
                "capacity_or_pressure_established": False,
            }
    return checks


def _physical_maps(
    geometry: Any,
    target_source_axes: frozenset[str],
) -> tuple[dict[str, cq.Shape], dict[str, cq.Shape], dict[str, cq.Shape]]:
    protected = geometry.protected
    target_duties = set(TARGET_DUTY_IDS)
    clips = dict(protected["retained_legacy_clips"])
    axes = dict(protected["retained_legacy_sds_axes"])
    if not target_duties <= clips.keys() or not target_source_axes <= axes.keys():
        raise ValueError("WJ18 protected maps omit one or more top-center legacy obstacles")
    clips = {name: shape for name, shape in clips.items() if name not in target_duties}
    axes = {name: shape for name, shape in axes.items() if name not in target_source_axes}
    physical = {}
    for category in (
        "fixed_66_hillman_axes_63p5mm",
        "retained_12_frame_bolt_components",
        "tnuts",
        "lights",
        "wires",
    ):
        physical.update(
            {f"{category}/{name}": shape for name, shape in protected[category].items()}
        )
    physical.update({f"retained_legacy_clips/{name}": shape for name, shape in clips.items()})
    physical.update({f"retained_legacy_sds_axes/{name}": shape for name, shape in axes.items()})
    access = {
        f"frame_access/{name}": shape
        for name, shape in protected["retained_12_frame_bolt_tools_withdrawals"].items()
    }
    access.update(
        {
            f"hold_projection/{name}": shape
            for name, shape in protected["hold_hole_and_provisional_projection"].items()
        }
    )
    proxies = {
        name: shape
        for name, shape in geometry.frame_bolt_shapes.items()
        if name.endswith("/source_occupied_axis")
    }
    if len(clips) != 4 or len(axes) != 24:
        raise ValueError("top-center replacement must leave four clips and 24 legacy SDS obstacles")
    return physical, access, proxies


def _scene_checks(
    geometry: Any,
    timber: Mapping[str, cq.Shape],
    candidate_parts: Mapping[str, cq.Shape],
    raw_cleats: Mapping[str, cq.Shape],
    finished_cleats: Mapping[str, cq.Shape],
    stacks: Mapping[str, BoltStack],
    installed: Mapping[str, Mapping[str, cq.Shape]],
    target_source_axes: frozenset[str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    physical, access_obstacles, frame_proxies = _physical_maps(geometry, target_source_axes)
    panels = {name: shape for name, shape in timber.items() if name in PANEL_NAMES}
    existing_hardware = {
        f"{axis_id}/{role}": shape
        for axis_id, roles in geometry.candidate_installed_hardware.items()
        for role, shape in roles.items()
    }
    own_new_hardware = {
        axis_id: roles for axis_id, roles in installed.items()
    }
    body_checks = {}
    for cleat_id, raw in raw_cleats.items():
        wood_hits = _hits(raw, timber)
        peer_hits = {
            name: round(volume, 6)
            for name, shape in candidate_parts.items()
            if name != cleat_id
            and (volume := _intersection_volume(raw, shape)) > HIT_TOLERANCE_MM3
        }
        body_checks[cleat_id] = {
            "finished_timber_hits_mm3": wood_hits,
            "other_candidate_part_hits_mm3": peer_hits,
            "fixed_or_retained_physical_hits_mm3": _hits(raw, physical),
            "frame_source_occupied_proxy_hits_mm3": _hits(raw, frame_proxies),
            "panel_replacement_hits_mm3": _hits(raw, panels),
            "existing_candidate_hardware_hits_mm3": _hits(raw, existing_hardware),
            "retained_access_envelope_hits_mm3": _hits(raw, access_obstacles),
            "static_body_conflicts_absent": not any(
                (
                    wood_hits,
                    peer_hits,
                    _hits(raw, physical),
                    _hits(raw, panels),
                    _hits(raw, existing_hardware),
                )
            ),
        }

    all_wood = {**timber, **candidate_parts}
    installed_checks = {}
    for axis_id, components in installed.items():
        installed_checks[axis_id] = {}
        for role, shape in components.items():
            wood_hits = _hits(shape, all_wood)
            physical_hits = _hits(shape, physical)
            proxy_hits = _hits(shape, frame_proxies)
            panel_hits = _hits(shape, panels)
            existing_hits = _hits(shape, existing_hardware)
            peer_hits = {
                f"{peer_axis}/{peer_role}": round(volume, 6)
                for peer_axis, peer_components in installed.items()
                if peer_axis != axis_id
                for peer_role, peer_shape in peer_components.items()
                if (volume := _intersection_volume(shape, peer_shape)) > HIT_TOLERANCE_MM3
            }
            access_hits = _hits(shape, access_obstacles)
            installed_checks[axis_id][role] = {
                "finished_wood_hits_mm3": wood_hits,
                "fixed_or_retained_physical_hits_mm3": physical_hits,
                "frame_source_occupied_proxy_hits_mm3": proxy_hits,
                "panel_replacement_hits_mm3": panel_hits,
                "existing_installed_hardware_hits_mm3": existing_hits,
                "peer_top_center_hardware_hits_mm3": peer_hits,
                "retained_access_envelope_hits_mm3": access_hits,
                "static_component_conflicts_absent": not any(
                    (wood_hits, physical_hits, panel_hits, existing_hits, peer_hits)
                ),
            }

    access_checks = {}
    tool_shapes_by_axis = {
        axis_id: access_shapes(stack) for axis_id, stack in stacks.items()
    }
    for axis_id, stack in stacks.items():
        own_hosts = {layer.body_id for layer in stack.layers}
        access_checks[axis_id] = {}
        for end, tool_shape in tool_shapes_by_axis[axis_id].items():
            nonreceiver_wood = {
                name: shape for name, shape in all_wood.items() if name not in own_hosts
            }
            wood_hits = _hits(tool_shape, nonreceiver_wood)
            physical_hits = _hits(tool_shape, physical)
            existing_hits = _hits(tool_shape, existing_hardware)
            path_hits = _hits(tool_shape, access_obstacles)
            proxy_hits = _hits(tool_shape, frame_proxies)
            peer_hardware = {
                f"{peer_axis}/{role}": shape
                for peer_axis, roles in own_new_hardware.items()
                if peer_axis != axis_id
                for role, shape in roles.items()
            }
            peer_tool_hits = {
                f"{peer_axis}/{peer_end}": round(volume, 6)
                for peer_axis in stacks
                if peer_axis != axis_id
                for peer_end, peer_tool in tool_shapes_by_axis[peer_axis].items()
                if (volume := _intersection_volume(tool_shape, peer_tool))
                > HIT_TOLERANCE_MM3
            }
            peer_hardware_hits = _hits(tool_shape, peer_hardware)
            access_checks[axis_id][end] = {
                "finished_nonreceiver_wood_hits_mm3": wood_hits,
                "fixed_or_retained_physical_hits_mm3": physical_hits,
                "existing_installed_hardware_hits_mm3": existing_hits,
                "retained_access_envelope_hits_mm3": path_hits,
                "frame_source_occupied_proxy_hits_mm3": proxy_hits,
                "peer_candidate_hardware_hits_mm3": peer_hardware_hits,
                "peer_tool_envelope_hits_mm3": peer_tool_hits,
                "recorded_nonreceiver_tool_approach_clear": not any(
                    (
                        wood_hits,
                        physical_hits,
                        existing_hits,
                        path_hits,
                        peer_hardware_hits,
                        peer_tool_hits,
                    )
                ),
                "receiver_member_tool_fit_unresolved": True,
                "complete_turning_stroke_and_counterhold_unresolved": True,
            }
    return body_checks, installed_checks, access_checks


def _dimensional_fit_screen() -> dict[str, Any]:
    # Both bolts cross one 88.9 mm cleat layer and one 38.1 mm member layer.
    nominal_grip = EXPECTED_CLEAT_SIZE_MM[1] + WOOD_LAYER_THICKNESS_MM
    grip_low = nominal_grip - 2 * WOOD_LAYER_TOLERANCE_MM
    grip_high = nominal_grip + 2 * WOOD_LAYER_TOLERANCE_MM
    earliest_nut_bearing = grip_low + 2 * WASHER_THICKNESS_MIN_MM
    farthest_nut_face = grip_high + 2 * WASHER_THICKNESS_MAX_MM + NUT_THICKNESS_MAX_MM
    required_with_tip = farthest_nut_face + TIP_PROJECTION_MM
    hardware = wj06_outer._hardware(ORDINARY_BOLT_LENGTH_MM, side=False)
    return {
        "basis": {
            "hardware_candidate": hardware.candidate_sku,
            "nominal_under_head_length_mm": ORDINARY_BOLT_LENGTH_MM,
            "minimum_length_bound_mm": ORDINARY_BOLT_MIN_LENGTH_MM,
            "wood_layer_tolerance_mm_each": WOOD_LAYER_TOLERANCE_MM,
            "washer_count_per_stack": 2,
            "washer_thickness_range_mm_each": [
                WASHER_THICKNESS_MIN_MM,
                WASHER_THICKNESS_MAX_MM,
            ],
            "maximum_nut_thickness_mm": NUT_THICKNESS_MAX_MM,
            "tip_projection_reserve_mm": TIP_PROJECTION_MM,
            "first_full_form_thread_location": "not supplied by this geometry or hardware model",
        },
        "per_127mm_grip_stack": {
            "nominal_grip_mm": nominal_grip,
            "grip_range_with_two_layer_tolerances_mm": [grip_low, grip_high],
            "earliest_nut_bearing_plane_mm": round(earliest_nut_bearing, 4),
            "farthest_nut_face_mm": round(farthest_nut_face, 4),
            "required_length_with_tip_reserve_mm": round(required_with_tip, 4),
            "minimum_length_envelope_margin_mm": round(
                ORDINARY_BOLT_MIN_LENGTH_MM - required_with_tip, 4
            ),
            "maximum_ring_gage_plane_mm": round(
                wj06_outer.RAIL_BOLT_CANDIDATE.maximum_full_thread_start_mm, 4
            ),
            "minimum_smooth_body_bound_mm": round(
                wj06_outer.RAIL_BOLT_CANDIDATE.minimum_smooth_body_mm, 4
            ),
            "earliest_nut_bearing_minus_minimum_smooth_body_bound_mm": round(
                earliest_nut_bearing
                - wj06_outer.RAIL_BOLT_CANDIDATE.minimum_smooth_body_mm,
                4,
            ),
            "maximum_ring_gage_plane_minus_earliest_nut_bearing_mm": round(
                wj06_outer.RAIL_BOLT_CANDIDATE.maximum_full_thread_start_mm
                - earliest_nut_bearing,
                4,
            ),
            "farthest_nut_face_minus_maximum_ring_gage_plane_mm": round(
                farthest_nut_face
                - wj06_outer.RAIL_BOLT_CANDIDATE.maximum_full_thread_start_mm,
                4,
            ),
            "gage_plane_is_not_first_full_form_thread": True,
            "conservative_bounds_are_not_an_actual_received_stack_measurement": True,
            "full_form_nut_engagement_established": False,
            "received_stack_fit_established": False,
        },
    }


def _conditional_edge_screen(placement: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    n_positions = tuple(placement["left"]["rail_bolt_n_mm"])
    lower_distance = min(value - CLEAT_N_MIN_MM for value in n_positions)
    upper_distance = min(CLEAT_N_MAX_MM - value for value in n_positions)
    min_grain_end = min(lower_distance, upper_distance)
    row_spacing = abs(n_positions[1] - n_positions[0])
    return {
        "cleat_grain_axis": "N",
        "cleat_N_interval_mm": [CLEAT_N_MIN_MM, CLEAT_N_MAX_MM],
        "rail_bolt_N_positions_mm": list(n_positions),
        "rail_bolt_row_spacing_mm": round(row_spacing, 6),
        "rail_bolt_grain_end_distances_mm": [
            round(value - CLEAT_N_MIN_MM, 6) for value in n_positions
        ] + [round(CLEAT_N_MAX_MM - value, 6) for value in n_positions],
        "minimum_rail_bolt_grain_end_distance_mm": round(min_grain_end, 6),
        "conditional_7D_reference_mm": CONDITIONAL_7D_MM,
        "conditional_7D_geometric_screen_clear": min_grain_end >= CONDITIONAL_7D_MM,
        "conditional_4D_row_spacing_reference_mm": 4 * NOMINAL_BOLT_DIAMETER_MM,
        "conditional_4D_row_spacing_screen_clear": row_spacing >= 4 * NOMINAL_BOLT_DIAMETER_MM,
        "signed_demand_directions_available": False,
        "conditional_end_distance_is_not_an_accepted_limit_state": True,
    }


def _false_release_flags() -> dict[str, bool]:
    return {name: False for name in RELEASE_FLAGS}


def _candidate_input_hashes(geometry: Any) -> dict[str, str]:
    current = {}
    for label, path in sorted(PRODUCER_HASH_PATHS.items()):
        try:
            current[label] = _sha256(path)
        except OSError as error:
            raise ValueError(f"top-center producer input is missing: {path}") from error
    fingerprints = _plain(getattr(geometry, "family_source_fingerprints", {}))
    if not fingerprints or not getattr(geometry, "family_trial_ids", {}):
        raise ValueError("retained WJ18 geometry lacks source family pins")
    for family, rows in fingerprints.items():
        for path, expected in rows.items():
            try:
                observed = _sha256(path)
            except OSError as error:
                raise ValueError(f"retained {family} input is missing: {path}") from error
            if observed != expected:
                raise ValueError(f"retained {family} input changed: {path}")
    return dict(sorted(current.items()))


def build_top_center_integration(geometry: Any) -> TopCenterIntegrationGeometry:
    """Build two top-center candidates over a retained WJ18 object only."""
    context_counts = _context_identity(geometry)
    source = geometry.source
    binding = validate_source_binding(source)
    if binding != geometry.source_binding:
        raise ValueError("retained WJ18 source binding changed before top-center integration")
    payload = (ROOT / INVENTORY_PATH).read_bytes()
    inventory_sha = hashlib.sha256(payload).hexdigest()
    if inventory_sha != binding.inventory_sha256:
        raise ValueError("retained source is not bound to the canonical inventory")
    inventory = json.loads(payload)
    wj12._inventory_matches_source_binding(inventory, binding)
    if _plain(geometry.source_inventory) != inventory:
        raise ValueError("WJ18 source inventory differs from the canonical inventory")

    expected_panel_ids = {
        row["axis_id"] for row in inventory.get("fixed_panel_kicker_screws", ())
    }
    expected_frame_ids = {
        row["axis_id"] for row in inventory.get("starting_frame_bolts", ())
    }
    if set(geometry.fixed_axes) != expected_panel_ids or len(expected_panel_ids) != 66:
        raise ValueError("WJ18 fixed panel axes differ from the exact canonical 66-axis set")
    if set(geometry.protected["fixed_66_hillman_axes_63p5mm"]) != expected_panel_ids:
        raise ValueError("WJ18 protected fixed-axis map differs from the canonical 66-axis set")
    if {row["axis_id"] for row in geometry.frame_bolt_records} != expected_frame_ids:
        raise ValueError("WJ18 frame-bolt IDs differ from the exact canonical twelve-bolt set")
    wj12._validate_frame_bolt_shapes(
        inventory, geometry.frame_bolt_records, geometry.frame_bolt_shapes
    )

    duties = _duty_rows(inventory)
    source_axes = _expected_source_axis_ids(duties)
    if source_axes & set(geometry.replaced_source_axis_ids):
        raise ValueError("WJ18 unexpectedly replaced one or more top-center legacy axes")
    if TOP_CANDIDATE_AXIS_IDS & set(geometry.candidate_bores):
        raise ValueError("top-center candidate axis IDs collide with retained WJ18 axes")
    if TOP_CANDIDATE_PART_IDS & set(geometry.finished_candidate_parts):
        raise ValueError("top-center candidate part IDs collide with retained WJ18 parts")
    _validate_live_connections(source, inventory, duties)
    if not source_axes <= set(geometry.protected["retained_legacy_sds_axes"]):
        raise ValueError("WJ18 retained legacy SDS map omits a top-center source axis")
    if not TARGET_DUTY_IDS <= set(geometry.protected["retained_legacy_clips"]):
        raise ValueError("WJ18 retained clip map omits one or more top-center duties")

    source_inputs = _candidate_input_hashes(geometry)
    family_fingerprints = _plain(geometry.family_source_fingerprints)
    family_trial_ids = _plain(geometry.family_trial_ids)

    raw_source_parts = _source_parts(source, "uncut_wood_parts")
    canonical_finished = _source_parts(source, "parts")
    if not HOST_IDS <= raw_source_parts.keys() or not HOST_IDS <= canonical_finished.keys():
        raise ValueError("canonical source omits a top-center receiver member")
    raw_hosts = {host: raw_source_parts[host] for host in HOST_IDS}

    native = right_rail.source_native_cutters_by_host(source, HOST_IDS)
    purchase = right_rail.candidate_panel_purchase_cutters_by_host(
        source, inventory, HOST_IDS
    )
    if set(native) != HOST_IDS or set(purchase) != HOST_IDS:
        raise ValueError("top-center source cut maps must cover exactly its three hosts")
    _compare_retained_source_maps(geometry, native, purchase)
    source_reconstruction = _source_reconstruction(source, raw_hosts, native)

    rail_frame = _frame_for_part(inventory, "base_rail_top")
    _validate_aligned_host_frames(inventory, rail_frame)
    part_rows = _part_rows(inventory)
    expected_normals = {
        "base_rail_top": -rail_frame.t,
        "base_principal_center_left": -rail_frame.x,
        "base_principal_center_right": rail_frame.x,
    }
    face_rows = {
        host: _face_record(host, part_rows[host], rail_frame, normal)
        for host, normal in expected_normals.items()
    }
    rail_extents = part_rows["base_rail_top"].get("actual_shape_extents_local_mm", {})
    low_t = rail_extents.get("T", [None, None])[0]
    n_extent = rail_extents.get("N")
    if low_t is None or not math.isclose(float(low_t), 0.0, abs_tol=1e-4):
        raise ValueError("top rail low-T face is no longer source-local T=0")
    if not isinstance(n_extent, list) or len(n_extent) != 2 or not math.isclose(
        float(n_extent[0]), 0.0, abs_tol=1e-4
    ) or not math.isclose(float(n_extent[1]), 139.7, abs_tol=1e-3):
        raise ValueError("top rail actual common N section differs from 0..139.7 mm")
    rail_face_t = rail_frame.coordinates(
        _vec(face_rows["base_rail_top"]["center_global_xyz_mm"], "top rail face center")
    )[1]
    if not math.isclose(rail_face_t, float(low_t), abs_tol=1e-4):
        raise ValueError("selected top rail face is not the actual source-local low-T face")
    if CLEAT_N_MIN_MM < float(n_extent[0]) or CLEAT_N_MAX_MM > float(n_extent[1]):
        raise ValueError("top-center cleat interval is outside the actual top-rail N face")

    placements = _placement_from_faces(inventory, rail_frame, face_rows)
    if not math.isclose(placements["inward_face_pair_overlap_if_used_mm"], 75.9, abs_tol=1e-3):
        raise ValueError("center-post inward-face spacing changed; review cleat topology")
    raw_cleats: dict[str, cq.Shape] = {}
    stacks: dict[str, BoltStack] = {}
    stack_rows: dict[str, dict[str, Any]] = {}
    rail_hardware = wj06_outer._hardware(ORDINARY_BOLT_LENGTH_MM, side=False)
    for duty_id in sorted(TARGET_DUTY_IDS):
        side = "left" if duty_id.endswith("left") else "right"
        cleat_id = CLEAT_IDS[duty_id]
        row = placements[side]
        x_lo = float(row["x_interval_mm"][0])
        raw_cleats[cleat_id] = top_outer._make_cleat(
            rail_frame, x_lo=x_lo, part_id=cleat_id
        )
        rail_x = float(row["rail_row_x_mm"])
        for index, n_mm in enumerate(row["rail_bolt_n_mm"], 1):
            axis_id = f"top_center/{duty_id}/rail_{index}"
            point = rail_frame.point(rail_x, CLEAT_T_MIN_MM, float(n_mm))
            stack = top_outer._make_stack(
                axis_id=axis_id,
                cleat_id=cleat_id,
                receiver_id="base_rail_top",
                point=point,
                direction=rail_frame.t,
                layers=((cleat_id, EXPECTED_CLEAT_SIZE_MM[1]), ("base_rail_top", WOOD_LAYER_THICKNESS_MM)),
                hardware=rail_hardware,
            )
            stacks[axis_id] = stack
            stack_rows[axis_id] = {
                "axis_id": axis_id,
                "station_id": duty_id,
                "interface": "top_center_cleat_to_top_rail",
                "receiver_ids": [cleat_id, "base_rail_top"],
                "local_point_top_rail_xyz_mm": [round(rail_x, 6), CLEAT_T_MIN_MM, round(float(n_mm), 6)],
                "global_point_xyz_mm": _tuple(point),
                "direction_global_xyz": _tuple(rail_frame.t, 9),
                "layer_thicknesses_mm": [EXPECTED_CLEAT_SIZE_MM[1], WOOD_LAYER_THICKNESS_MM],
                "grip_mm": EXPECTED_CLEAT_SIZE_MM[1] + WOOD_LAYER_THICKNESS_MM,
                "hardware_candidate": rail_hardware.candidate_sku,
                "nominal_under_head_length_mm": ORDINARY_BOLT_LENGTH_MM,
                "minimum_length_bound_mm": ORDINARY_BOLT_MIN_LENGTH_MM,
                "washer_count": 2,
                "cad_roles": sorted(ORDINARY_COMPONENT_ROLES),
                "thread_engagement_established": False,
            }

        principal_id = f"base_principal_center_{side}"
        start_x = float(row["principal_bolt_x_mm"])
        direction = rail_frame.x * float(row["principal_bolt_direction_sign_x"])
        for index, t_mm in enumerate(PRINCIPAL_BOLT_T_OFFSETS_MM, 1):
            axis_id = f"top_center/{duty_id}/principal_{index}"
            point = rail_frame.point(start_x, float(t_mm), CLEAT_N_MIN_MM + EXPECTED_CLEAT_SIZE_MM[2] / 2)
            stack = top_outer._make_stack(
                axis_id=axis_id,
                cleat_id=cleat_id,
                receiver_id=principal_id,
                point=point,
                direction=direction,
                layers=((cleat_id, EXPECTED_CLEAT_SIZE_MM[0]), (principal_id, WOOD_LAYER_THICKNESS_MM)),
                hardware=rail_hardware,
            )
            stacks[axis_id] = stack
            stack_rows[axis_id] = {
                "axis_id": axis_id,
                "station_id": duty_id,
                "interface": f"top_center_cleat_to_{principal_id}",
                "receiver_ids": [cleat_id, principal_id],
                "local_point_top_rail_xyz_mm": [round(start_x, 6), round(float(t_mm), 6), round(CLEAT_N_MIN_MM + EXPECTED_CLEAT_SIZE_MM[2] / 2, 6)],
                "global_point_xyz_mm": _tuple(point),
                "direction_global_xyz": _tuple(direction, 9),
                "layer_thicknesses_mm": [EXPECTED_CLEAT_SIZE_MM[0], WOOD_LAYER_THICKNESS_MM],
                "grip_mm": EXPECTED_CLEAT_SIZE_MM[0] + WOOD_LAYER_THICKNESS_MM,
                "hardware_candidate": rail_hardware.candidate_sku,
                "nominal_under_head_length_mm": ORDINARY_BOLT_LENGTH_MM,
                "minimum_length_bound_mm": ORDINARY_BOLT_MIN_LENGTH_MM,
                "washer_count": 2,
                "cad_roles": sorted(ORDINARY_COMPONENT_ROLES),
                "thread_engagement_established": False,
            }

    if set(raw_cleats) != TOP_CANDIDATE_PART_IDS or set(stacks) != TOP_CANDIDATE_AXIS_IDS:
        raise ValueError("top-center candidate parts/stacks differ from exact two-duty contract")

    bores_by_host: dict[str, dict[str, cq.Shape]] = {
        name: {} for name in HOST_IDS | TOP_CANDIDATE_PART_IDS
    }
    bores: dict[str, Any] = {}
    installed: dict[str, dict[str, cq.Shape]] = {}
    for axis_id, stack in stacks.items():
        bore = top_outer._through_bore(stack)
        receivers = tuple(layer.body_id for layer in stack.layers)
        if len(receivers) != 2 or len(set(receivers)) != 2:
            raise ValueError(f"{axis_id}: candidate axis needs exactly two distinct receivers")
        bores[axis_id] = wj12.CandidateBore(
            axis_id=axis_id,
            family="top_center",
            trial_id=TRIAL_ID,
            receiver_ids=receivers,
            shape=bore,
            station_id=stack_rows[axis_id]["station_id"],
        )
        for receiver in receivers:
            bores_by_host[receiver][axis_id] = bore
        roles = dict(stack.installed_shapes())
        if set(roles) != ORDINARY_COMPONENT_ROLES:
            raise ValueError(f"{axis_id}: ordinary hardware role map changed")
        installed[axis_id] = roles
    if sum(len(roles) for roles in installed.values()) != 40:
        raise ValueError("top-center pair must export exactly 40 installed hardware roles")
    expected_receiver_bore_counts = {
        "base_rail_top": 4,
        "base_principal_center_left": 2,
        "base_principal_center_right": 2,
        "top_center_left_cleat": 4,
        "top_center_right_cleat": 4,
    }
    if {name: len(rows) for name, rows in bores_by_host.items()} != expected_receiver_bore_counts:
        raise ValueError("top-center bore receiver map differs from exact eight-axis topology")

    panel_cutters = top_outer._make_candidate_panel_cutters(
        source, inventory, set(raw_cleats)
    )
    finished_cleats = {}
    for part_id, raw in raw_cleats.items():
        tools = [*bores_by_host[part_id].values(), *panel_cutters[part_id].values()]
        finished = raw.cut(*tools).clean() if tools else raw
        finished_cleats[part_id] = _valid_shape(finished, f"finished center cleat/{part_id}")

    target_cutter_ids = set(source_axes)
    replaced_cutter_ids = set(target_cutter_ids)
    applied_source_maps = geometry.applied_source_cutters_by_host
    present_native_ids = {
        cut_id
        for host_map in applied_source_maps.values()
        for cut_id in host_map
    }
    missing_target_cutters = target_cutter_ids - present_native_ids
    if missing_target_cutters:
        raise ValueError(
            "WJ18 applied source cutter map omits top-center legacy axes: "
            + ", ".join(sorted(missing_target_cutters))
        )
    for host_cuts in applied_source_maps.values():
        replaced_cutter_ids.update(
            f"{axis_id}/head" for axis_id in target_cutter_ids if f"{axis_id}/head" in host_cuts
        )
    replaced_cutter_ids = frozenset(replaced_cutter_ids)
    pre_bore_hosts, finished_hosts = _preview_hosts(
        geometry, raw_hosts, replaced_cutter_ids, bores_by_host
    )
    timber = _candidate_scene(
        geometry,
        source,
        raw_source_parts,
        pre_bore_hosts,
        finished_hosts,
    )
    candidate_parts = dict(geometry.finished_candidate_parts)
    candidate_parts.update(finished_cleats)
    pre_bore_timber = dict(timber)
    pre_bore_timber.update(pre_bore_hosts)
    pre_bore_parts = {
        **pre_bore_timber,
        **raw_cleats,
        **geometry.finished_candidate_parts,
    }
    layer_checks = _layer_checks(stacks, pre_bore_parts)
    contact_checks = _host_contact_checks(
        raw_cleats,
        finished_hosts,
        rail_frame,
        face_rows,
        placements,
        bores_by_host,
    )
    washer_checks = top_outer._washer_support_checks(
        stacks,
        {**timber, **candidate_parts},
    )
    body_checks, installed_checks, access_checks = _scene_checks(
        geometry,
        timber,
        candidate_parts,
        raw_cleats,
        finished_cleats,
        stacks,
        installed,
        source_axes,
    )

    # Native source cuts are verified independently from purchased panel paths.
    # No finished shared-host override is exported; the parent unions these maps
    # with the retained WJ18 maps and all candidate bores.
    if set(source_reconstruction) != HOST_IDS:
        raise ValueError("top-center source reconstruction omitted a receiver member")

    source_face_evidence = {}
    for host, row in face_rows.items():
        source_face_evidence[host] = {
            "face_id": row.get("face_id"),
            "face_center_global_xyz_mm": row["center_global_xyz_mm"],
            "face_center_top_rail_local_xyz_mm": row[
                "center_local_in_top_rail_frame_mm"
            ],
            "face_normal_global_xyz": row["normal_global_xyz"],
            "grain_axis_global_xyz": part_rows[host].get("grain_axis_global_xyz"),
            "stock_section_mm": part_rows[host].get("actual_source_section_mm"),
            "stock_product": part_rows[host].get("stock_product"),
            "actual_shape_extents_local_mm": part_rows[host].get(
                "actual_shape_extents_local_mm"
            ),
        }
    source_face_evidence["top_rail_frame"] = {
        "source_local_origin_global_xyz_mm": _tuple(rail_frame.origin),
        "cleat_datum_global_xyz_mm": _tuple(rail_frame.origin),
        "source_local_axes_global_xyz": {
            "X": _tuple(rail_frame.x, 9),
            "T": _tuple(rail_frame.t, 9),
            "N": _tuple(rail_frame.n, 9),
        },
        "low_T_face_source_local_T_mm": float(low_t),
        "rail_axis_entry_face_is_source_low_T": True,
    }

    edge_screen = _conditional_edge_screen(placements)
    dimensional_fit = _dimensional_fit_screen()
    gates = {
        "exact_wj18_context_bound": True,
        "exact_two_top_center_duties_and_twelve_source_axes": len(duties) == 2
        and len(source_axes) == 12,
        "two_full_section_cleats_and_eight_bolts": len(raw_cleats) == 2
        and len(bores) == 8,
        "all_66_fixed_axes_and_twelve_frame_bolts_bound": len(geometry.fixed_axes) == 66
        and len(geometry.frame_bolt_records) == 12,
        "source_native_reconstruction_matches_canonical_parts": all(
            row["matches_canonical_source_finished_member"]
            for row in source_reconstruction.values()
        ),
        "candidate_layer_material_present": all(
            row["all_declared_layers_present"] for row in layer_checks.values()
        ),
        "candidate_contact_slab_material_present": all(
            row["full_contact_slab_material_present"]
            for checks in contact_checks.values()
            for row in checks.values()
        ),
        "washer_seat_support_present": all(
            seat["full_annular_seat_support"]
            for axis in washer_checks.values()
            for seat in axis.values()
        ),
        "candidate_body_static_conflicts_absent": all(
            row["static_body_conflicts_absent"] for row in body_checks.values()
        ),
        "installed_component_static_conflicts_absent": all(
            row["static_component_conflicts_absent"]
            for axis in installed_checks.values()
            for row in axis.values()
        ),
        "recorded_nonreceiver_tool_approach_envelopes_clear": all(
            row["recorded_nonreceiver_tool_approach_clear"]
            for axis in access_checks.values()
            for row in axis.values()
        ),
        "conditional_7d_geometric_screen_clear": edge_screen[
            "conditional_7D_geometric_screen_clear"
        ],
        "complete_joint_acceptance": False,
        "capacity_established": False,
        "tool_fit_established": False,
        "installation_proven": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    release = _false_release_flags()
    return TopCenterIntegrationGeometry(
        source=source,
        source_binding=binding,
        source_inventory=_readonly(inventory),
        source_inputs_sha256=_readonly(source_inputs),
        family_source_fingerprints=_nested_readonly(family_fingerprints),
        family_trial_ids=_readonly(family_trial_ids),
        retained_layout_id=geometry.layout_id,
        retained_trial_id=geometry.trial_id,
        retained_counts=_readonly(context_counts),
        trial_id=TRIAL_ID,
        duties=_nested_readonly(duties),
        raw_candidate_parts=_readonly(raw_cleats),
        finished_candidate_parts=_readonly(finished_cleats),
        candidate_bores=_readonly(bores),
        candidate_bores_by_host=_nested_readonly(bores_by_host),
        candidate_installed_hardware=_nested_readonly(installed),
        source_native_cutters_by_host=_nested_readonly(native),
        source_panel_purchase_cutters_by_host=_nested_readonly(purchase),
        candidate_panel_purchase_cutters_by_part=_nested_readonly(panel_cutters),
        replaced_source_axis_ids=source_axes,
        replaced_source_cutter_ids=replaced_cutter_ids,
        source_reconstruction=_nested_readonly(source_reconstruction),
        contact_checks=_nested_readonly(contact_checks),
        layer_checks=_nested_readonly(layer_checks),
        washer_support=_nested_readonly(washer_checks),
        candidate_body_checks=_nested_readonly(body_checks),
        installed_component_checks=_nested_readonly(installed_checks),
        access_checks=_nested_readonly(access_checks),
        source_face_evidence=_nested_readonly(source_face_evidence),
        placement_evidence=_readonly_tree(placements),
        stack_rows=_nested_readonly(stack_rows),
        source_axis_entry_face_audit=_nested_readonly(_source_entry_audit(inventory, duties)),
        conditional_edge_screen=_readonly(edge_screen),
        dimensional_fit_screen=_readonly(dimensional_fit),
        diagnostic_gates=_readonly(gates),
        release=_readonly(release),
    )


def diagnostic_report(geometry: TopCenterIntegrationGeometry) -> dict[str, Any]:
    """Return the source-bound top-center delta report, with all release flags false."""
    if geometry.trial_id != TRIAL_ID:
        raise ValueError("top-center report requires its fixed candidate trial")
    if validate_source_binding(geometry.source) != geometry.source_binding:
        raise ValueError("top-center source binding changed before report creation")
    for label, path in PRODUCER_HASH_PATHS.items():
        if _sha256(path) != geometry.source_inputs_sha256[label]:
            raise ValueError(f"top-center report input changed: {path}")
    # Preserve axis-specific coordinates, layer order, and stack dimensions.
    stack_rows = _plain(geometry.stack_rows)
    axis_evidence = {
        axis_id: {
            "station_id": bore.station_id,
            "family": bore.family,
            "trial_id": bore.trial_id,
            "receiver_ids": list(bore.receiver_ids),
            "shape_sha256": _source_shape_fingerprint(bore.shape),
            "bounds_xyz_mm": [
                round(value, 6)
                for value in (
                    bore.shape.BoundingBox().xmin,
                    bore.shape.BoundingBox().xmax,
                    bore.shape.BoundingBox().ymin,
                    bore.shape.BoundingBox().ymax,
                    bore.shape.BoundingBox().zmin,
                    bore.shape.BoundingBox().zmax,
                )
            ],
            "installed_component_shape_sha256": {
                role: _source_shape_fingerprint(shape)
                for role, shape in sorted(
                    geometry.candidate_installed_hardware[axis_id].items()
                )
            },
        }
        for axis_id, bore in sorted(geometry.candidate_bores.items())
    }
    return {
        "schema": SCHEMA,
        "trial_id": geometry.trial_id,
        "status": geometry.status,
        "claim_boundary": (
            "Source-bound provisional top-center candidate geometry and static screens only. "
            "No joint capacity, signed demand, complete tool fit, assembly sequence, or release is established."
        ),
        "source": {
            "candidate": geometry.source_inventory.get("candidate"),
            "source_commit": geometry.source_inventory.get("source_commit"),
            "source_inventory_sha256": geometry.source_binding.inventory_sha256,
            "runtime_module_sha256": dict(
                sorted(geometry.source_binding.runtime_module_sha256.items())
            ),
            "family_source_fingerprints_sha256": _plain(
                geometry.family_source_fingerprints
            ),
            "family_trial_ids": dict(sorted(geometry.family_trial_ids.items())),
            "producer_inputs_sha256": dict(geometry.source_inputs_sha256),
        },
        "retained_context": {
            "layout_id": geometry.retained_layout_id,
            "trial_id": geometry.retained_trial_id,
            "counts": dict(geometry.retained_counts),
            "candidate_axes_preserved": 80,
            "candidate_installed_roles_preserved": 400,
            "fixed_panel_axes_preserved": 66,
            "frame_bolts_preserved": 12,
        },
        "counts": geometry.counts,
        "target_duties": {
            duty_id: {
                "legacy_host_members": list(row["legacy_host_members"]),
                "replaced_source_sds_axis_ids": [
                    axis["axis_id"] for axis in row["legacy_sds_axes"]
                ],
            }
            for duty_id, row in geometry.duties.items()
        },
        "stock_and_frame": {
            "cleat_stock_dimensions_X_T_N_mm": list(EXPECTED_CLEAT_SIZE_MM),
            "cleat_grain_axis": "top-rail source-local N; 119.7 mm grain length",
            "candidate_stock_basis": (
                "full-section solid-sawn DF-L No. 2 4x4 development stock; "
                "actual delivered stock is unobserved"
            ),
            "cleat_T_interval_relative_to_actual_low_T_face_mm": [
                CLEAT_T_MIN_MM,
                CLEAT_T_MAX_MM,
            ],
            "cleat_N_interval_mm": [CLEAT_N_MIN_MM, CLEAT_N_MAX_MM],
            "source_faces": _plain(geometry.source_face_evidence),
            "provisional_placements": _plain(geometry.placement_evidence),
            "conditional_signed_edge_screen": dict(geometry.conditional_edge_screen),
        },
        "candidate_stacks": axis_evidence,
        "stack_rows": stack_rows,
        "source_axis_entry_face_audit": _plain(
            geometry.source_axis_entry_face_audit
        ),
        "candidate_parts": {
            part_id: {
                "raw_shape_sha256": _source_shape_fingerprint(raw),
                "finished_shape_sha256": _source_shape_fingerprint(
                    geometry.finished_candidate_parts[part_id]
                ),
                "raw_volume_mm3": round(raw.Volume(), 6),
                "finished_volume_mm3": round(
                    geometry.finished_candidate_parts[part_id].Volume(), 6
                ),
            }
            for part_id, raw in sorted(geometry.raw_candidate_parts.items())
        },
        "candidate_bore_axes": {
            axis_id: {
                "station_id": bore.station_id,
                "receiver_ids": list(bore.receiver_ids),
                "shape_sha256": _source_shape_fingerprint(bore.shape),
            }
            for axis_id, bore in sorted(geometry.candidate_bores.items())
        },
        "source_cut_maps": {
            "native_source_cutters_by_host": {
                host: sorted(cuts)
                for host, cuts in geometry.source_native_cutters_by_host.items()
            },
            "purchased_panel_cutters_by_host": {
                host: sorted(cuts)
                for host, cuts in geometry.source_panel_purchase_cutters_by_host.items()
            },
            "candidate_panel_cutters_by_cleat": {
                host: sorted(cuts)
                for host, cuts in geometry.candidate_panel_purchase_cutters_by_part.items()
            },
            "replaced_source_axis_ids": sorted(geometry.replaced_source_axis_ids),
            "replaced_source_cutter_ids": sorted(geometry.replaced_source_cutter_ids),
            "native_and_purchase_maps_are_separate": True,
            "shared_finished_host_overrides_exported": False,
            "parent_union_with_WJ18_maps_and_all_candidate_bores_required": True,
        },
        "source_reconstruction": _plain(geometry.source_reconstruction),
        "receiver_layer_material": _plain(geometry.layer_checks),
        "contact_face_material": _plain(geometry.contact_checks),
        "washer_support": _plain(geometry.washer_support),
        "candidate_body_static_checks": _plain(geometry.candidate_body_checks),
        "installed_component_static_checks": _plain(geometry.installed_component_checks),
        "recorded_nonreceiver_approach_checks": _plain(geometry.access_checks),
        "ordinary_hardware_dimensional_comparison": dict(geometry.dimensional_fit_screen),
        "diagnostic_gates": dict(geometry.diagnostic_gates),
        "release": dict(geometry.release),
        "claim_limits": {
            "candidate_is_provisional": True,
            "complete_cross_family_parent_merge_required": True,
            "capacity_or_pressure_established": False,
            "signed_demand_directions_available": False,
            "full_form_thread_engagement_established": False,
            "receiver_member_tool_fit_established": False,
            "complete_tool_approach_or_turning_stroke_established": False,
            "installation_sequence_proven": False,
            "source_cutting_released": False,
            "drilling_released": False,
            "fabrication_released": False,
        },
    }
