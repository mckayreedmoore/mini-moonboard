"""Viewer-only revision of the two center principal/header blocks.

The caller supplies an already composed WJ24 geometry plus its immediately
preceding revision report. This module does not compose source families or run
CAD/mechanics jobs; it replaces two candidate blocks, relocates their eight
bolt stacks, and replays the three affected timber hosts from raw stock.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import replace
from types import MappingProxyType
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import _source_shape_fingerprint

SCHEMA = "wood_joint_wj24_center_header_blocks/v1"
REVISION_ID = "center-principal-header-blocks-plumb-full-section-v1"
INPUT_REVISION_ID = "kicker-posts-outside-central-tnuts-v1"
SIDES = ("left", "right")
TARGET_PARTS = frozenset(f"center_principal_cleat_{side}" for side in SIDES)
HOST_IDS = frozenset({"base_header", *(f"base_principal_center_{side}" for side in SIDES)})
BLOCK_BOUNDS_RIGHT_MM = ((89.05, 177.95), (-175.7, -36.0), (277.0, 416.7))
HEADER_START_Z_MM = 238.9
HEADER_BOLT_X_MM = 116.0
HEADER_BOLT_Y_MM = (-140.0, -75.0)
PRINCIPAL_T_OFFSETS_MM = (40.0, 60.0)
T_AXIS = cq.Vector(0.0, math.cos(math.radians(50.0)), math.sin(math.radians(50.0)))
HARDWARE_ROLES = frozenset({"shaft", "head", "head_washer", "nut_washer", "nut"})
def _proxy(values: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(values))


def _nested_proxy(values: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Mapping[str, Any]]:
    return MappingProxyType({key: _proxy(value) for key, value in values.items()})


def _shape(value: Any, label: str) -> cq.Shape:
    if not isinstance(value, cq.Shape) or not value.isValid() or not value.Solids():
        raise ValueError(f"{label}: expected a valid solid CAD shape")
    return value


def _unit(vector: cq.Vector, label: str) -> cq.Vector:
    length = float(vector.Length)
    if length <= 1e-12:
        raise ValueError(f"{label}: expected a nonzero axis")
    return vector / length


def _union_display_ids(
    prior: Mapping[str, Any], current: Mapping[str, list[str]]
) -> dict[str, list[str]]:
    return {
        category: sorted(set(prior.get(category, ())) | set(current.get(category, ())))
        for category in set(prior) | set(current)
    }


def _axis_ids() -> tuple[str, ...]:
    return tuple(
        axis_id
        for side in SIDES
        for axis_id in (
            f"center_principal_{side}_1",
            f"center_principal_{side}_2",
            f"center_principal_header_{side}_1",
            f"center_principal_header_{side}_2",
        )
    )


def _validate_axis_ownership(geometry: Any) -> dict[str, str]:
    expected: dict[str, str] = {}
    for side in SIDES:
        principal = f"base_principal_center_{side}"
        for index in (1, 2):
            expected[f"center_principal_{side}_{index}"] = principal
            expected[f"center_principal_header_{side}_{index}"] = "base_header"
    if not set(expected) <= set(geometry.candidate_bores):
        raise ValueError("current WJ24 is missing one or more center block axes")
    for axis_id, receiver in expected.items():
        side = "left" if "_left_" in axis_id else "right"
        part = f"center_principal_cleat_{side}"
        bore = geometry.candidate_bores[axis_id]
        if tuple(bore.receiver_ids) != (receiver, part):
            raise ValueError(f"{axis_id}: unexpected receiver order or candidate ownership")
        roles = geometry.candidate_installed_hardware.get(axis_id, {})
        if set(roles) != HARDWARE_ROLES:
            raise ValueError(f"{axis_id}: installed hardware roles differ from the five-role contract")
    return expected


def _block(side: str) -> cq.Shape:
    (xmin, xmax), (ymin, ymax), (zmin, zmax) = BLOCK_BOUNDS_RIGHT_MM
    if side == "left":
        xmin, xmax = -xmax, -xmin
    return cq.Solid.makeBox(xmax - xmin, ymax - ymin, zmax - zmin, cq.Vector(xmin, ymin, zmin))


def _vertical_bore(shape: cq.Shape, x: float, y: float, z0: float) -> tuple[cq.Shape, float, float]:
    box = shape.BoundingBox()
    length = float(box.zlen)
    if length <= 1e-9:
        raise ValueError("vertical center-header bore has no Z length")
    radius = math.sqrt(float(shape.Volume()) / (math.pi * length))
    if radius <= 1e-6:
        raise ValueError("vertical center-header bore radius cannot be derived")
    grip = BLOCK_BOUNDS_RIGHT_MM[2][1] - z0
    bore = cq.Solid.makeCylinder(radius, grip, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))
    return _shape(bore, "revised vertical center-header bore"), radius, grip


def _move_vertical_hardware(
    roles: Mapping[str, cq.Shape],
    *,
    dx: float,
    dy: float,
    z_start: float,
    old_grip: float,
    new_grip: float,
    axis_id: str,
) -> dict[str, cq.Shape]:
    xy = cq.Vector(dx, dy, 0.0)
    dz = new_grip - old_grip
    washer = _shape(roles["head_washer"], f"{axis_id}/head_washer").BoundingBox().zlen
    shaft_box = _shape(roles["shaft"], f"{axis_id}/shaft").BoundingBox()
    shaft_radius = min(float(shaft_box.xlen), float(shaft_box.ylen)) / 2.0
    shaft_length = float(shaft_box.zlen) + dz
    shaft = cq.Solid.makeCylinder(
        shaft_radius,
        shaft_length,
        cq.Vector(shaft_box.xmin + dx + shaft_radius, shaft_box.ymin + dy + shaft_radius, shaft_box.zmin),
        cq.Vector(0, 0, 1),
    )
    # The original head stays below the header; only its XY station changes.
    moved = {
        "head": _shape(roles["head"], f"{axis_id}/head").translate(xy),
        "head_washer": _shape(roles["head_washer"], f"{axis_id}/head_washer").translate(xy),
        "shaft": _shape(shaft, f"{axis_id}/revised shaft"),
        "nut_washer": _shape(roles["nut_washer"], f"{axis_id}/nut_washer").translate(
            cq.Vector(dx, dy, dz)
        ),
        "nut": _shape(roles["nut"], f"{axis_id}/nut").translate(cq.Vector(dx, dy, dz)),
    }
    expected_min_z = z_start - washer
    if abs(moved["shaft"].BoundingBox().zmin - expected_min_z) > 1e-5:
        raise ValueError(f"{axis_id}: rebuilt shaft does not start at the head washer")
    return moved


def _rebuild_hosts(
    geometry: Any,
    bores: Mapping[str, Any],
    progress: Callable[[str], None] | None,
) -> tuple[dict[str, cq.Shape], dict[str, Any]]:
    replaced = set(geometry.replaced_source_cutter_ids)
    finished: dict[str, cq.Shape] = {}
    replay: dict[str, Any] = {}
    for host_id in sorted(HOST_IDS):
        raw = _shape(geometry.raw_hosts[host_id], f"raw host {host_id}")
        source_cuts = geometry.applied_source_cutters_by_host[host_id]
        retained = [shape for cutter_id, shape in source_cuts.items() if cutter_id not in replaced]
        host_bores = {
            axis_id: bore.shape
            for axis_id, bore in bores.items()
            if host_id in tuple(bore.receiver_ids)
        }
        tools = retained + list(host_bores.values())
        rebuilt = raw.cut(*tools).clean() if tools else raw
        finished[host_id] = _shape(rebuilt, f"rebuilt host {host_id}")
        replay[host_id] = {
            "retained_source_and_purchase_cutter_count": len(retained),
            "excluded_replaced_source_cutter_count": len(source_cuts) - len(retained),
            "candidate_bore_axis_ids": sorted(host_bores),
            "finished_shape_sha256": _source_shape_fingerprint(rebuilt),
        }
        if progress is not None:
            progress(f"rebuilt {host_id}: {len(retained)} retained cuts and {len(host_bores)} candidate bores")
    return finished, replay


def build_wj24_center_header_blocks(
    geometry: Any,
    prior_report: Mapping[str, Any],
    *,
    progress: Callable[[str], None] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Return the plumb full-section center block revision for viewer review."""
    if getattr(geometry, "layout_id", None) != INPUT_REVISION_ID or getattr(
        geometry, "trial_id", None
    ) != INPUT_REVISION_ID:
        raise ValueError("input must be the current kicker-posts-outside-central-T-nuts revision")
    if prior_report.get("revision_id") != INPUT_REVISION_ID:
        raise ValueError("the matching immediately preceding revision report is required")
    if getattr(geometry, "status", None) != "unaccepted_viewer_geometry_revision":
        raise ValueError("input WJ24 viewer revision status changed")
    for name in (
        "raw_hosts", "finished_hosts", "applied_source_cutters_by_host",
        "replaced_source_cutter_ids", "raw_candidate_parts", "finished_candidate_parts",
        "candidate_bores", "candidate_installed_hardware", "fixed_axes",
        "frame_bolt_records", "frame_bolt_shapes", "purchased_panel_cutters_by_candidate_part",
    ):
        if not hasattr(geometry, name):
            raise ValueError(f"WJ24 center-header revision lacks {name}")
    if not TARGET_PARTS <= set(geometry.raw_candidate_parts) or not TARGET_PARTS <= set(
        geometry.finished_candidate_parts
    ):
        raise ValueError("WJ24 candidate maps omit a center principal/header block")
    if not HOST_IDS <= set(geometry.raw_hosts) or not HOST_IDS <= set(
        geometry.applied_source_cutters_by_host
    ):
        raise ValueError("WJ24 raw host/cut maps omit an affected center receiver")
    _validate_axis_ownership(geometry)

    raw_parts = dict(geometry.raw_candidate_parts)
    finished_parts = dict(geometry.finished_candidate_parts)
    bores = dict(geometry.candidate_bores)
    hardware = {axis_id: dict(roles) for axis_id, roles in geometry.candidate_installed_hardware.items()}
    axis_report: dict[str, Any] = {}
    target_axes = _axis_ids()

    for side in SIDES:
        part_id = f"center_principal_cleat_{side}"
        if progress is not None:
            progress(f"placing full-section plumb block {part_id}")
        raw_parts[part_id] = _block(side)
        block_tools = []
        for index, t_offset in enumerate(PRINCIPAL_T_OFFSETS_MM, 1):
            axis_id = f"center_principal_{side}_{index}"
            bore = bores[axis_id]
            before = {role: _shape(shape, f"{axis_id}/{role}") for role, shape in hardware[axis_id].items()}
            direction_before = _unit(before["nut"].Center() - before["head"].Center(), f"{axis_id} direction")
            expected_direction = cq.Vector(1.0 if side == "right" else -1.0, 0.0, 0.0)
            grip = float(bore.shape.BoundingBox().xlen)
            if (direction_before - expected_direction).Length > 1e-6:
                raise ValueError(f"{axis_id}: receiver order does not match head-to-nut direction")
            if abs(grip - 127.0) > 0.01:
                raise ValueError(f"{axis_id}: expected 127 mm horizontal timber grip, got {grip:.6f} mm")
            translation = T_AXIS * t_offset
            new_bore_shape = _shape(bore.shape.translate(translation), f"{axis_id} moved bore")
            bores[axis_id] = replace(bore, shape=new_bore_shape)
            hardware[axis_id] = {role: shape.translate(translation) for role, shape in before.items()}
            block_tools.append(new_bore_shape)
            axis_report[axis_id] = {
                "candidate_part_id": part_id,
                "receiver_order_head_to_nut": list(bore.receiver_ids),
                "direction_before_global_xyz": [round(v, 9) for v in direction_before.toTuple()],
                "direction_after_global_xyz": [round(v, 9) for v in direction_before.toTuple()],
                "translation_global_xyz_mm": [round(v, 9) for v in translation.toTuple()],
                "wood_grip_preserved_mm": round(grip, 6),
            }

        for index, y in enumerate(HEADER_BOLT_Y_MM, 1):
            axis_id = f"center_principal_header_{side}_{index}"
            bore = bores[axis_id]
            old_box = _shape(bore.shape, f"{axis_id} old bore").BoundingBox()
            old_grip = float(old_box.zlen)
            z0 = min(float(old_box.zmin), HEADER_START_Z_MM)
            sign = -1.0 if side == "left" else 1.0
            new_x = sign * HEADER_BOLT_X_MM
            old_x = (float(old_box.xmin) + float(old_box.xmax)) / 2.0
            old_y = (float(old_box.ymin) + float(old_box.ymax)) / 2.0
            new_bore_shape, radius, new_grip = _vertical_bore(bore.shape, new_x, y, z0)
            bores[axis_id] = replace(bore, shape=new_bore_shape)
            hardware[axis_id] = _move_vertical_hardware(
                hardware[axis_id],
                dx=new_x - old_x,
                dy=y - old_y,
                z_start=z0,
                old_grip=old_grip,
                new_grip=new_grip,
                axis_id=axis_id,
            )
            vertical_direction = _unit(
                hardware[axis_id]["nut"].Center() - hardware[axis_id]["head"].Center(),
                f"{axis_id} revised direction",
            )
            if (vertical_direction - cq.Vector(0, 0, 1)).Length > 1e-6:
                raise ValueError(f"{axis_id}: header-bolt receiver order is not head-to-nut +Z")
            block_tools.append(new_bore_shape)
            axis_report[axis_id] = {
                "candidate_part_id": part_id,
                "receiver_order_head_to_nut": list(bore.receiver_ids),
                "origin_global_xyz_mm": [round(new_x, 6), round(y, 6), round(z0, 6)],
                "direction_global_xyz": [0.0, 0.0, 1.0],
                "bore_radius_mm": round(radius, 6),
                "wood_grip_mm": round(new_grip, 6),
                "old_wood_grip_mm": round(old_grip, 6),
            }

        candidate_cuts = list(geometry.purchased_panel_cutters_by_candidate_part.get(part_id, {}).values())
        finished_parts[part_id] = _shape(
            raw_parts[part_id].cut(*(block_tools + candidate_cuts)).clean(),
            f"finished block {part_id}",
        )

    finished_hosts, host_replay = _rebuild_hosts(geometry, bores, progress)
    host_map = dict(geometry.finished_hosts)
    host_map.update(finished_hosts)

    if len(geometry.fixed_axes) != 66:
        raise ValueError("fixed panel-axis count changed before center block revision")
    if len(geometry.frame_bolt_records) != 12 or len(geometry.frame_bolt_shapes) != 72:
        raise ValueError("frame-bolt record/component count changed before center block revision")
    if len(target_axes) != 8 or sum(1 for axis_id in target_axes if axis_id in bores) != 8:
        raise ValueError("center block revision did not cover all eight owned bolt axes")

    checks = {
        "two_center_principal_blocks_replaced_with_plumb_full_section_boxes": True,
        "four_header_bolts_restationed_and_extended_through_new_blocks": True,
        "four_principal_cross_bolts_moved_along_50_degree_T_by_40_and_60_mm": True,
        "three_receiver_hosts_rebuilt_from_raw_retained_cuts_and_all_current_bores": True,
        "all_66_fixed_panel_axes_and_12_frame_bolts_preserved": True,
        "geometry_only_no_force_or_joint_acceptance_calculation": True,
        "complete_joint_acceptance": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    revised = replace(
        geometry,
        layout_id=REVISION_ID,
        trial_id=REVISION_ID,
        status="unaccepted_viewer_geometry_revision",
        raw_candidate_parts=_proxy(raw_parts),
        finished_candidate_parts=_proxy(finished_parts),
        candidate_bores=_proxy(bores),
        candidate_installed_hardware=_nested_proxy(hardware),
        finished_hosts=_proxy(host_map),
        composition_checks=_proxy(checks),
    )
    current_display = {
        "finished_candidate_parts": sorted(TARGET_PARTS),
        "finished_hosts": sorted(HOST_IDS),
        "candidate_installed_hardware": sorted(
            f"{axis_id}/{role}" for axis_id in target_axes for role in HARDWARE_ROLES
        ),
        "panel_replacements": [],
        "fixed_panel_axes": [],
    }
    prior_display = prior_report.get("changed_display_solid_ids", {})
    prior_removed_display = set(prior_report.get("removed_display_solid_ids", ()))
    prior_removed_parts = set(prior_report.get("removed_candidate_part_ids", ()))
    prior_removed_axes = set(prior_report.get("removed_candidate_axis_ids", ()))
    prior_moved_axes = set(prior_report.get("moved_candidate_axis_ids", ()))
    report = {
        "schema": SCHEMA,
        "status": "unaccepted_viewer_geometry_revision",
        "revision_id": REVISION_ID,
        "input_revision_id": INPUT_REVISION_ID,
        "prior_revision_report": dict(prior_report),
        "summary": "Two center principal/header blocks are plumb full-section 4x6 boxes with a flat header seat; four vertical header bolts move clear of the center posts and four cross-principal bolts move 40/60 mm along T.",
        "scope": "viewer geometry only; no source recomposition, force calculation, joint acceptance, fabrication, or drilling release",
        "block_bounds_right_global_mm": {
            "x": list(BLOCK_BOUNDS_RIGHT_MM[0]),
            "y": list(BLOCK_BOUNDS_RIGHT_MM[1]),
            "z": list(BLOCK_BOUNDS_RIGHT_MM[2]),
        },
        "target_candidate_part_ids": sorted(TARGET_PARTS),
        "target_axis_ids": sorted(target_axes),
        "axes": axis_report,
        "moved_candidate_axis_ids": sorted(prior_moved_axes | set(target_axes)),
        "moved_panel_axes": list(prior_report.get("moved_panel_axes", ())),
        "baseline_display_translations_mm": dict(
            prior_report.get("baseline_display_translations_mm", {})
        ),
        "removed_display_solid_ids": sorted(prior_removed_display),
        "removed_candidate_part_ids": sorted(prior_removed_parts),
        "removed_candidate_axis_ids": sorted(prior_removed_axes),
        "rebuilt_host_ids": sorted(HOST_IDS),
        "host_replay": host_replay,
        "preserved_counts": {
            "candidate_parts": len(finished_parts),
            "candidate_axes": len(bores),
            "candidate_hardware_roles": sum(map(len, hardware.values())),
            "fixed_panel_axes": len(geometry.fixed_axes),
            "frame_bolts": len(geometry.frame_bolt_records),
        },
        "changed_display_solid_ids": _union_display_ids(prior_display, current_display),
        "checks": checks,
    }
    return revised, report
