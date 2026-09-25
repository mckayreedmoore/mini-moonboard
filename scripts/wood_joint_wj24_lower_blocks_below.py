"""Viewer-only WJ24 revision with four lower service cleats below their rails.

This consumes an already composed WJ24 object. It never builds a source family
or runs the compositor. The returned geometry is a new immutable composition
view; the supplied baseline remains unchanged.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from types import MappingProxyType
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import _source_shape_fingerprint

SCHEMA = "wood_joint_wj24_lower_blocks_below/v1"
REVISION_ID = "lower-rear-blocks-below-v1"
BASE_LAYOUT_ID = "wj24-twenty-four-duty-integrated-static-v1"
BASE_TRIAL_ID = "wj24-wj18-plus-top-center-bottom-pairs-v1"
EXPECTED_CENTER_GLOBAL_T_MM = 1334.824
T_PLANE_TOLERANCE_MM = 0.002
T_SECTION_WIDTH_MM = 38.1
SHAPE_TOLERANCE_MM3 = 1e-5

# Candidate part -> rail host, station, family, and the other timber receiver.
TARGETS = {
    "wj04_lower_full_stock_cleat": {
        "rail": "base_rail_service_lower_right",
        "station": "clip_horizontal_lower_right_1",
        "family": "wj04_g7",
        "other_receiver": "base_principal_center_right",
        "axis_suffixes": ("lower_rail_1", "lower_rail_2", "lower_principal_1", "lower_principal_2"),
    },
    "wj06_outer_lower_right_cleat": {
        "rail": "base_rail_service_lower_right",
        "station": "clip_horizontal_lower_right_2",
        "family": "wj06_outer_pair",
        "other_receiver": "base_side_right",
        "axis_suffixes": ("lower_rail_1", "lower_rail_2", "lower_side_1", "lower_side_2"),
    },
    "left_service_inner_lower_cleat": {
        "rail": "base_rail_service_lower_left",
        "station": "clip_horizontal_lower_left_2",
        "family": "left_service",
        "other_receiver": "base_principal_center_left",
        "axis_suffixes": ("lower_rail_1", "lower_rail_2", "lower_principal_1", "lower_principal_2"),
    },
    "left_service_outer_lower_cleat": {
        "rail": "base_rail_service_lower_left",
        "station": "clip_horizontal_lower_left_1",
        "family": "left_service",
        "other_receiver": "base_side_left",
        "axis_suffixes": ("lower_rail_1", "lower_rail_2", "lower_side_1", "lower_side_2"),
    },
}
TARGET_PART_IDS = frozenset(TARGETS)
RAIL_IDS = frozenset(row["rail"] for row in TARGETS.values())
HOST_IDS = frozenset(
    {rail for rail in RAIL_IDS}
    | {row["other_receiver"] for row in TARGETS.values()}
)
HARDWARE_ROLES = frozenset({"shaft", "head", "head_washer", "nut_washer", "nut"})


def _proxy_map(values: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(values))


def _proxy_nested(values: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Mapping[str, Any]]:
    return MappingProxyType({key: _proxy_map(value) for key, value in values.items()})


def _shape(value: Any, label: str) -> cq.Shape:
    if not isinstance(value, cq.Shape) or not value.isValid() or not value.Solids():
        raise ValueError(f"{label}: expected a valid solid CAD shape")
    return value


def _unit(vector: cq.Vector, label: str) -> cq.Vector:
    length = float(vector.Length)
    if length <= 1e-12:
        raise ValueError(f"{label}: expected a nonzero vector")
    return vector / length


def _rail_center_plane(
    geometry: Any, rail_id: str
) -> tuple[cq.Vector, cq.Vector, dict[str, Any]]:
    """Derive the rail's mid-T plane from raw solid vertices and its source datum."""
    rows = {
        row["part_id"]: row
        for row in geometry.source_inventory.get("parts", ())
        if isinstance(row, Mapping) and row.get("part_id")
    }
    row = rows.get(rail_id)
    if row is None:
        raise ValueError(f"source inventory omits rail {rail_id}")
    matrix = row.get("local_to_global_transform")
    axes = row.get("local_axes")
    if not isinstance(matrix, (tuple, list)) or len(matrix) != 4 or not isinstance(axes, Mapping):
        raise ValueError(f"{rail_id}: incomplete source-local T frame")
    origin = cq.Vector(float(matrix[0][3]), float(matrix[1][3]), float(matrix[2][3]))
    raw = _shape(geometry.raw_hosts[rail_id], f"raw host {rail_id}")
    t_axis = _unit(cq.Vector(*map(float, axes["T"])), f"{rail_id}.T")
    vertices = raw.Vertices()
    if not vertices:
        raise ValueError(f"{rail_id}: raw rail has no vertices for T-bound derivation")
    t_values = [float((vertex.Center() - origin).dot(t_axis)) for vertex in vertices]
    t_min, t_max = min(t_values), max(t_values)
    if abs((t_max - t_min) - T_SECTION_WIDTH_MM) > 1e-3:
        raise ValueError(
            f"{rail_id}: raw rail T width {t_max - t_min:.6f} mm differs from full stock"
        )
    midpoint = (t_min + t_max) / 2.0
    plane_point = origin + t_axis * midpoint
    global_t = float(plane_point.dot(t_axis))
    if abs(global_t - EXPECTED_CENTER_GLOBAL_T_MM) > T_PLANE_TOLERANCE_MM:
        raise ValueError(
            f"{rail_id}: raw-derived center T {global_t:.6f} mm differs from pinned "
            f"{EXPECTED_CENTER_GLOBAL_T_MM:.6f} mm"
        )
    evidence = {
        "rail_id": rail_id,
        "normal_global_xyz": [round(value, 9) for value in t_axis.toTuple()],
        "plane_point_global_xyz_mm": [round(value, 6) for value in plane_point.toTuple()],
        "raw_t_bounds_local_mm": [round(t_min, 6), round(t_max, 6)],
        "raw_t_width_mm": round(t_max - t_min, 6),
        "center_global_t_mm": round(global_t, 6),
    }
    return t_axis, plane_point, evidence


def _mirror_shape(shape: cq.Shape, normal: cq.Vector, point: cq.Vector, label: str) -> cq.Shape:
    mirrored = _shape(shape, label).mirror(normal, point)
    return _shape(mirrored, f"mirrored {label}")


def _axis_direction_from_head_to_nut(roles: Mapping[str, cq.Shape], axis_id: str) -> cq.Vector:
    head = _shape(roles["head"], f"{axis_id}/head").Center()
    nut = _shape(roles["nut"], f"{axis_id}/nut").Center()
    return _unit(nut - head, f"{axis_id} head-to-nut direction")


def _read_target_axes(geometry: Any) -> dict[str, list[str]]:
    by_part: dict[str, list[str]] = {part_id: [] for part_id in TARGET_PART_IDS}
    for axis_id, bore in geometry.candidate_bores.items():
        receivers = tuple(getattr(bore, "receiver_ids", ()))
        part_id = next((part for part in receivers if part in TARGET_PART_IDS), None)
        if part_id is None:
            continue
        target = TARGETS[part_id]
        if getattr(bore, "family", None) != target["family"]:
            raise ValueError(f"{axis_id}: candidate family changed for {part_id}")
        suffix = axis_id.rsplit("/", 1)[-1]
        expected_receiver = (
            target["rail"] if suffix.startswith("lower_rail_") else target["other_receiver"]
        )
        if len(receivers) != 2 or receivers != (part_id, expected_receiver):
            raise ValueError(f"{axis_id}: receiver order/map omits its candidate or timber")
        station = getattr(bore, "station_id", None)
        if station is not None and station != target["station"]:
            raise ValueError(f"{axis_id}: explicit station differs from its lower cleat")
        by_part[part_id].append(axis_id)

    for part_id, target in TARGETS.items():
        axis_ids = sorted(by_part[part_id])
        suffixes = sorted(axis_id.rsplit("/", 1)[-1] for axis_id in axis_ids)
        if suffixes != sorted(target["axis_suffixes"]):
            raise ValueError(f"{part_id}: expected its four explicit lower bolt axes")
        by_part[part_id] = axis_ids
    return by_part


def _rebuild_affected_hosts(
    geometry: Any,
    bores: Mapping[str, Any],
    progress: Callable[[str], None] | None = None,
) -> tuple[dict[str, cq.Shape], dict[str, Any]]:
    replaced = set(geometry.replaced_source_cutter_ids)
    rebuilt: dict[str, cq.Shape] = {}
    replay: dict[str, Any] = {}
    for host_id in sorted(HOST_IDS):
        raw = _shape(geometry.raw_hosts[host_id], f"raw host {host_id}")
        source_map = geometry.applied_source_cutters_by_host[host_id]
        retained = [
            shape for cutter_id, shape in source_map.items() if cutter_id not in replaced
        ]
        host_bores = {
            axis_id: bore.shape
            for axis_id, bore in bores.items()
            if host_id in tuple(bore.receiver_ids)
        }
        tools = retained + list(host_bores.values())
        finished = raw.cut(*tools).clean() if tools else raw
        rebuilt[host_id] = _shape(finished, f"rebuilt host {host_id}")
        if progress is not None:
            progress(f"rebuilt {host_id}: {len(retained)} retained cutters, {len(host_bores)} candidate bores")
        replay[host_id] = {
            "retained_source_and_purchase_cutter_count": len(retained),
            "excluded_replaced_source_cutter_count": sum(
                cutter_id in replaced for cutter_id in source_map
            ),
            "candidate_bore_axis_ids": sorted(host_bores),
            "candidate_bore_count": len(host_bores),
            "finished_shape_sha256": _source_shape_fingerprint(finished),
        }
    return rebuilt, replay


def build_wj24_lower_blocks_below(
    geometry: Any,
    progress: Callable[[str], None] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Return a source-preserving WJ24 viewer revision and its replay report.

    ``geometry`` is an already composed WJ24 object. This function only
    transforms four lower service cleats, their 16 bore/hardware stacks, and
    rebuilds the six affected host shapes from raw timber plus retained cuts.
    """
    if getattr(geometry, "layout_id", None) != BASE_LAYOUT_ID or getattr(
        geometry, "trial_id", None
    ) != BASE_TRIAL_ID:
        raise ValueError("input must be the frozen complete WJ24 baseline composition")
    if getattr(geometry, "status", None) != "unaccepted_integrated_hypothesis":
        raise ValueError("input WJ24 status changed")
    for name in (
        "raw_hosts",
        "applied_source_cutters_by_host",
        "replaced_source_cutter_ids",
        "raw_candidate_parts",
        "finished_candidate_parts",
        "candidate_bores",
        "candidate_installed_hardware",
        "fixed_axes",
        "frame_bolt_records",
        "frame_bolt_shapes",
        "source_inventory",
    ):
        if not hasattr(geometry, name):
            raise ValueError(f"WJ24 composition lacks required map {name}")

    axes_by_part = _read_target_axes(geometry)
    if not TARGET_PART_IDS <= set(geometry.raw_candidate_parts) or not TARGET_PART_IDS <= set(
        geometry.finished_candidate_parts
    ):
        raise ValueError("WJ24 candidate part maps omit a requested lower cleat")
    for host_id in HOST_IDS:
        if host_id not in geometry.raw_hosts or host_id not in geometry.applied_source_cutters_by_host:
            raise ValueError(f"WJ24 raw/cut maps omit affected host {host_id}")

    planes: dict[str, tuple[cq.Vector, cq.Vector]] = {}
    plane_evidence: dict[str, Any] = {}
    for rail_id in sorted(RAIL_IDS):
        normal, point, evidence = _rail_center_plane(geometry, rail_id)
        planes[rail_id] = (normal, point)
        plane_evidence[rail_id] = evidence
    centers = [plane_evidence[rail]["center_global_t_mm"] for rail in sorted(RAIL_IDS)]
    if max(centers) - min(centers) > T_PLANE_TOLERANCE_MM:
        raise ValueError("left and right lower service rails do not share the center-T plane")

    raw_parts = dict(geometry.raw_candidate_parts)
    finished_parts = dict(geometry.finished_candidate_parts)
    bores: dict[str, Any] = dict(geometry.candidate_bores)
    hardware = {axis_id: dict(roles) for axis_id, roles in geometry.candidate_installed_hardware.items()}
    axis_reports: dict[str, Any] = {}
    changed_hardware_ids: list[str] = []
    for part_id, target in TARGETS.items():
        if progress is not None:
            progress(f"reflecting {part_id} and its four lower-axis stacks")
        normal, point = planes[target["rail"]]
        raw_parts[part_id] = _mirror_shape(
            geometry.raw_candidate_parts[part_id], normal, point, f"{part_id} raw block"
        )
        finished_parts[part_id] = _mirror_shape(
            geometry.finished_candidate_parts[part_id], normal, point, f"{part_id} finished block"
        )
        for axis_id in axes_by_part[part_id]:
            bore = bores[axis_id]
            receiver_order = tuple(bore.receiver_ids)
            bore_shape = _mirror_shape(bore.shape, normal, point, f"{axis_id} bore")
            bores[axis_id] = replace(bore, shape=bore_shape)
            roles = hardware.get(axis_id)
            if roles is None or set(roles) != HARDWARE_ROLES:
                raise ValueError(f"{axis_id}: installed hardware roles differ from the five-role contract")
            before_direction = _axis_direction_from_head_to_nut(roles, axis_id)
            moved_roles = {
                role: _mirror_shape(shape, normal, point, f"{axis_id}/{role}")
                for role, shape in roles.items()
            }
            after_direction = _unit(
                _axis_direction_from_head_to_nut(moved_roles, axis_id),
                f"{axis_id} reflected head-to-nut direction",
            )
            reflected_direction = _unit(
                before_direction - normal * (2.0 * before_direction.dot(normal)),
                f"{axis_id} reflected direction expectation",
            )
            if (after_direction - reflected_direction).Length > 1e-6:
                raise ValueError(f"{axis_id}: mirrored installed hardware changed its directed axis")
            if axis_id.rsplit("/", 1)[-1].startswith("lower_rail_"):
                before_t = float(before_direction.dot(normal))
                after_t = float(after_direction.dot(normal))
                if before_t * after_t >= 0 or abs(before_t + after_t) > 1e-6:
                    raise ValueError(f"{axis_id}: rail bolt did not reverse its T component")
            hardware[axis_id] = moved_roles
            changed_hardware_ids.extend(f"{axis_id}/{role}" for role in sorted(moved_roles))
            axis_reports[axis_id] = {
                "station_id": target["station"],
                "candidate_part_id": part_id,
                "receiver_order_head_to_nut": list(receiver_order),
                "receiver_order_preserved": True,
                "direction_label": "head_to_nut",
                "direction_before_global_xyz": [round(value, 9) for value in before_direction.toTuple()],
                "direction_after_global_xyz": [round(value, 9) for value in after_direction.toTuple()],
                "head_receiver": receiver_order[0],
                "nut_receiver": receiver_order[1],
            }

    finished_hosts, host_replay = _rebuild_affected_hosts(geometry, bores, progress)
    new_host_map = dict(geometry.finished_hosts)
    new_host_map.update(finished_hosts)

    # The moved cleats may touch, but must not interpenetrate, either receiver.
    contacts: dict[str, Any] = {}
    for part_id, target in TARGETS.items():
        candidate = finished_parts[part_id]
        for host_id in (target["rail"], target["other_receiver"]):
            receiver = _shape(finished_hosts[host_id], f"finished host {host_id}")
            overlap = float(candidate.intersect(receiver).Volume())
            distance = float(candidate.distance(receiver))
            if overlap > SHAPE_TOLERANCE_MM3:
                raise ValueError(f"{part_id}: moved block penetrates receiver {host_id}")
            contacts[f"{part_id}/{host_id}"] = {
                "intersection_volume_mm3": round(overlap, 9),
                "distance_mm": round(distance, 9),
                "no_solid_interpenetration": overlap <= SHAPE_TOLERANCE_MM3,
            }

    fixed_axes_before = set(geometry.fixed_axes)
    frame_shape_keys_before = set(geometry.frame_bolt_shapes)
    if len(fixed_axes_before) != 66:
        raise ValueError("WJ24 fixed 66-axis map changed")
    if len(geometry.frame_bolt_records) != 12 or len(frame_shape_keys_before) != 72:
        raise ValueError("WJ24 twelve-frame-bolt map changed")
    if len(axes_by_part) != 4 or sum(map(len, axes_by_part.values())) != 16:
        raise ValueError("lower-block transformation did not cover exactly four blocks and 16 axes")
    if len(changed_hardware_ids) != 80:
        raise ValueError("lower-block transformation did not cover exactly 80 hardware roles")

    checks = {
        "input_is_frozen_complete_wj24_baseline": True,
        "four_lower_service_cleats_reflected_about_raw_rail_center_T": True,
        "six_affected_hosts_rebuilt_from_raw_retained_cuts_and_candidate_bores": True,
        "all_16_target_bores_and_80_hardware_roles_reflected": True,
        "all_66_fixed_panel_axes_and_12_frame_bolts_preserved": True,
        "no_force_or_structural_acceptance_calculation_performed": True,
        "complete_joint_acceptance": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    revised = replace(
        geometry,
        layout_id=REVISION_ID,
        trial_id=REVISION_ID,
        raw_candidate_parts=_proxy_map(raw_parts),
        finished_candidate_parts=_proxy_map(finished_parts),
        candidate_bores=_proxy_map(bores),
        candidate_installed_hardware=_proxy_nested(hardware),
        finished_hosts=_proxy_map(new_host_map),
        composition_checks=_proxy_map(checks),
    )
    report = {
        "schema": SCHEMA,
        "status": "unaccepted_viewer_geometry_revision",
        "summary": "Four lower rear-service cleats and their bolt stacks are reflected below the raw rail center-T planes; six receivers are replayed from raw hosts and retained cuts.",
        "revision_id": REVISION_ID,
        "base_layout_id": geometry.layout_id,
        "base_trial_id": geometry.trial_id,
        "target_candidate_part_ids": sorted(TARGET_PART_IDS),
        "target_axis_count": 16,
        "target_hardware_role_count": 80,
        "base_composition_checks_preserved_separately": dict(geometry.composition_checks),
        "rebuilt_host_ids": sorted(HOST_IDS),
        "planes_by_raw_rail": plane_evidence,
        "axes": axis_reports,
        "target_receiver_contacts": contacts,
        "host_replay": host_replay,
        "preserved_counts": {
            "candidate_parts_before_after": [len(geometry.finished_candidate_parts), len(finished_parts)],
            "candidate_axes_before_after": [len(geometry.candidate_bores), len(bores)],
            "candidate_hardware_roles_before_after": [
                sum(map(len, geometry.candidate_installed_hardware.values())),
                sum(map(len, hardware.values())),
            ],
            "fixed_panel_axes": len(geometry.fixed_axes),
            "frame_bolts": len(geometry.frame_bolt_records),
        },
        "changed_display_solid_ids": {
            "finished_candidate_parts": sorted(TARGET_PART_IDS),
            "finished_hosts": sorted(HOST_IDS),
            "candidate_installed_hardware": sorted(changed_hardware_ids),
            "panel_replacements": [],
            "fixed_panel_axes": [],
        },
        "g7_relief_and_retained_source_cuts": {
            "all_nonreplaced_applied_source_and_panel_cuts_replayed": True,
            "replaced_source_cutter_ids_excluded_before_candidate_bores": True,
            "upper_wj04_g7_crosscut_candidate_unchanged": True,
        },
        "scope": "viewer geometry only; no source composition, force calculation, or acceptance claim",
    }
    return revised, report
