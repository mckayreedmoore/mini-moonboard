"""Viewer-only WJ24 revision: raise the lowest rear support pair one T-nut row.

Consumes the WJ24 ``lower-rear-blocks-below-v1`` review geometry, moves the
bottom rails and their four cleats/bolt stacks together by one 200 mm T row,
and remachines the two affected lower panels and six receiver hosts. This is
not a source candidate, mechanics result, fabrication release, or acceptance.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import replace
from types import MappingProxyType
from typing import Any

import cadquery as cq

from mini_moonboard import floor_flush_width as width
from mini_moonboard import wood_joint_panel_machining as panel_machining
from mini_moonboard.wood_joint_frame import _source_shape_fingerprint
from scripts import wood_joint_wj24_lower_blocks_below as lower_blocks

SCHEMA = "wood_joint_wj24_bottom_support_up_one_row/v1"
REVISION_ID = "lower-rear-blocks-below-plus-bottom-support-up-one-row-v1"
INPUT_REVISION_ID = lower_blocks.REVISION_ID
T_ROW_PITCH_MM = 200.0
PANEL_SCREW_IDS = frozenset(
    f"round_panel_lower_{side}_edge_{index}"
    for side in ("left", "right")
    for index in (1, 2)
)
PANEL_SCREW_VISUAL_NAMES = {
    axis_id: f"fastener_{axis_id}" for axis_id in sorted(PANEL_SCREW_IDS)
}
MOVING_PART_AXES = {
    "bottom_center_left_cleat": tuple(
        f"bottom_center/clip_horizontal_bottom_left_2/{role}_{index}"
        for role in ("principal", "rail")
        for index in (1, 2)
    ),
    "bottom_center_right_cleat": tuple(
        f"bottom_center/clip_horizontal_bottom_right_1/{role}_{index}"
        for role in ("principal", "rail")
        for index in (1, 2)
    ),
    "bottom_outer_left_cleat": tuple(
        f"bottom_outer/clip_horizontal_bottom_left_1/{role}_{index}"
        for role in ("side", "rail")
        for index in (1, 2)
    ),
    "bottom_outer_right_cleat": tuple(
        f"bottom_outer/clip_horizontal_bottom_right_2/{role}_{index}"
        for role in ("side", "rail")
        for index in (1, 2)
    ),
}
MOVING_PART_IDS = frozenset(MOVING_PART_AXES)
MOVING_AXIS_IDS = frozenset(
    axis_id for axis_ids in MOVING_PART_AXES.values() for axis_id in axis_ids
)
MOVED_HOST_IDS = frozenset(
    {
        "base_rail_bottom_left",
        "base_rail_bottom_right",
        "base_principal_center_left",
        "base_principal_center_right",
        "base_side_left",
        "base_side_right",
    }
)
MOVED_RAIL_IDS = frozenset({"base_rail_bottom_left", "base_rail_bottom_right"})
PANEL_IDS = frozenset({"main_lower_left", "main_lower_right"})
HARDWARE_ROLES = frozenset({"shaft", "head", "head_washer", "nut_washer", "nut"})
AXIS_TOLERANCE_MM = 1e-6


def _proxy(values: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(values))


def _nested_proxy(values: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Mapping[str, Any]]:
    return MappingProxyType({key: MappingProxyType(dict(rows)) for key, rows in values.items()})


def _translation_from_inventory(
    inventory: Mapping[str, Any], distance_mm: float = T_ROW_PITCH_MM
) -> cq.Vector:
    rows = {
        row["part_id"]: row
        for row in inventory.get("parts", ())
        if isinstance(row, Mapping) and row.get("part_id")
    }
    axes = [rows.get(rail, {}).get("local_axes", {}).get("T") for rail in sorted(MOVED_RAIL_IDS)]
    if any(not isinstance(axis, (tuple, list)) or len(axis) != 3 for axis in axes):
        raise ValueError("source inventory must define both bottom-rail T axes")
    first, second = (cq.Vector(*map(float, axis)) for axis in axes)
    if (first - second).Length > AXIS_TOLERANCE_MM:
        raise ValueError("left and right bottom-rail T axes differ")
    if abs(first.Length - 1.0) > AXIS_TOLERANCE_MM:
        raise ValueError("source bottom-rail T axis must be unit length")
    if not math.isfinite(distance_mm):
        raise ValueError("support translation must be finite")
    return first * distance_mm


def _shape_map_translate(values: Mapping[str, cq.Shape], names: set[str], delta: cq.Vector) -> dict[str, cq.Shape]:
    return {
        name: shape.translate(delta) if name in names else shape
        for name, shape in values.items()
    }


def _panel_connections(
    source: Any, delta: cq.Vector, expected_axis_ids: set[str]
) -> tuple[Any, ...]:
    connections = tuple(source.panel_connections())
    by_name = {connection.name: connection for connection in connections}
    if len(connections) != 66 or len(by_name) != 66:
        raise ValueError("source must provide exactly 66 uniquely named panel axes")
    if set(by_name) != expected_axis_ids:
        raise ValueError("source panel-axis identities differ from the canonical inventory")
    if not PANEL_SCREW_IDS <= by_name.keys():
        raise ValueError("source panel-axis set omits one or more moved lower-edge screws")
    result = tuple(
        replace(connection, start=connection.start + delta)
        if connection.name in PANEL_SCREW_IDS
        else connection
        for connection in connections
    )
    return result


class _PanelModelProxy:
    """Provide only the attributes the existing kerf-right panel remesher needs."""

    option = width.KERF_RIGHT

    def __init__(self, source: Any, panel_connections: tuple[Any, ...]):
        self.b = source.b
        self.base = source.base
        self._panel_connections = panel_connections

    def panel_connections(self) -> tuple[Any, ...]:
        return self._panel_connections


def _remachine_panels(source: Any, moved_connections: tuple[Any, ...]) -> dict[str, cq.Shape]:
    current = tuple(source.parts())
    raw = tuple(source.uncut_wood_parts())
    proxy = _PanelModelProxy(source, moved_connections)
    # The shared remesher restores displaced right-panel grid bores before it
    # cuts the revised purchase axes. Only its lower-right result is consumed.
    right = panel_machining.candidate_panel_replacements(
        proxy, current_parts=current, uncut_parts=raw
    )["main_lower_right"]
    current_by_name = {part.name: part for part in current}
    raw_by_name = {part.name: part for part in raw}
    if "main_lower_left" not in current_by_name or "main_lower_left" not in raw_by_name:
        raise ValueError("source model omits the lower-left main panel")
    left_shape = raw_by_name["main_lower_left"].shape
    for connection in moved_connections:
        if connection.members[0] != "main_lower_left":
            continue
        for cutter in panel_machining._panel_connection_cutters(connection):
            left_shape = left_shape.cut(cutter)
    left = replace(current_by_name["main_lower_left"], shape=left_shape.clean())
    return {"main_lower_left": left.shape, "main_lower_right": right.shape}


def _rebuild_hosts(
    geometry: Any,
    raw_hosts: Mapping[str, cq.Shape],
    applied_cuts: Mapping[str, Mapping[str, cq.Shape]],
    bores: Mapping[str, Any],
) -> tuple[dict[str, cq.Shape], dict[str, dict[str, Any]]]:
    replaced = set(geometry.replaced_source_cutter_ids)
    finished: dict[str, cq.Shape] = {}
    replay: dict[str, dict[str, Any]] = {}
    for host_id in sorted(MOVED_HOST_IDS):
        retained = [
            shape for cutter_id, shape in applied_cuts[host_id].items()
            if cutter_id not in replaced
        ]
        host_bores = {
            axis_id: bore.shape
            for axis_id, bore in bores.items()
            if host_id in tuple(bore.receiver_ids)
        }
        tools = retained + list(host_bores.values())
        shape = raw_hosts[host_id].cut(*tools).clean() if tools else raw_hosts[host_id]
        if not isinstance(shape, cq.Shape) or not shape.isValid() or not shape.Solids():
            raise ValueError(f"{host_id}: revised host is not a valid positive solid")
        finished[host_id] = shape
        replay[host_id] = {
            "retained_source_and_purchase_cut_count": len(retained),
            "excluded_replaced_source_cut_count": len(applied_cuts[host_id]) - len(retained),
            "candidate_bore_axis_ids": sorted(host_bores),
            "candidate_bore_count": len(host_bores),
            "finished_shape_sha256": _source_shape_fingerprint(shape),
        }
    return finished, replay


def _union_display_ids(prior: Mapping[str, Any], current: Mapping[str, list[str]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for category in set(prior) | set(current):
        result[category] = sorted(set(prior.get(category, ())) | set(current.get(category, ())))
    return result


def build_wj24_bottom_support_up_one_row(
    geometry: Any,
    lower_blocks_report: Mapping[str, Any],
    *,
    translation_wall_t_mm: float = T_ROW_PITCH_MM,
    revision_id: str = REVISION_ID,
) -> tuple[Any, dict[str, Any]]:
    """Return revised lower-support viewer geometry and a source-bound report."""
    if getattr(geometry, "layout_id", None) != INPUT_REVISION_ID or getattr(
        geometry, "trial_id", None
    ) != INPUT_REVISION_ID:
        raise ValueError("input must be the lower-rear-blocks-below WJ24 viewer revision")
    if lower_blocks_report.get("revision_id") != INPUT_REVISION_ID:
        raise ValueError("the matching lower-block revision report is required")
    if getattr(geometry, "status", None) != "unaccepted_integrated_hypothesis":
        raise ValueError("input viewer revision status changed")
    for name in (
        "raw_hosts", "finished_hosts", "applied_source_cutters_by_host",
        "source_cutters_by_host", "purchased_panel_cutters_by_host",
        "candidate_bores", "raw_candidate_parts", "finished_candidate_parts",
        "candidate_installed_hardware", "fixed_axes", "protected", "source_inventory",
    ):
        if not hasattr(geometry, name):
            raise ValueError(f"WJ24 lower-block revision omits {name}")

    delta = _translation_from_inventory(geometry.source_inventory, translation_wall_t_mm)
    source_inventory_axes = {
        row["axis_id"]: row
        for row in geometry.source_inventory.get("fixed_panel_kicker_screws", ())
    }
    if len(source_inventory_axes) != 66 or not PANEL_SCREW_IDS <= source_inventory_axes.keys():
        raise ValueError("source inventory must preserve the exact 66 purchased panel axes")
    if set(geometry.fixed_axes) != set(source_inventory_axes):
        raise ValueError("WJ24 fixed panel axes differ from the source inventory")
    connections = _panel_connections(
        geometry.source, delta, set(source_inventory_axes)
    )

    raw_hosts = dict(geometry.raw_hosts)
    for host_id in MOVED_RAIL_IDS:
        raw_hosts[host_id] = raw_hosts[host_id].translate(delta)

    # Every cutter is part of its host-member geometry. Translate the complete
    # cut map on each moving rail, including service passages and the two new
    # panel-screw receiver cuts; other member maps retain their current frames.
    native_cuts = {host: dict(rows) for host, rows in geometry.source_cutters_by_host.items()}
    applied_cuts = {host: dict(rows) for host, rows in geometry.applied_source_cutters_by_host.items()}
    purchase_cuts = {host: dict(rows) for host, rows in geometry.purchased_panel_cutters_by_host.items()}
    for host_id in MOVED_RAIL_IDS:
        native_cuts[host_id] = {name: shape.translate(delta) for name, shape in native_cuts[host_id].items()}
        applied_cuts[host_id] = {name: shape.translate(delta) for name, shape in applied_cuts[host_id].items()}
        purchase_cuts[host_id] = {name: shape.translate(delta) for name, shape in purchase_cuts[host_id].items()}

    raw_parts = dict(geometry.raw_candidate_parts)
    finished_parts = dict(geometry.finished_candidate_parts)
    for part_id in MOVING_PART_IDS:
        raw_parts[part_id] = raw_parts[part_id].translate(delta)
        finished_parts[part_id] = finished_parts[part_id].translate(delta)

    bores = dict(geometry.candidate_bores)
    hardware = {axis_id: dict(roles) for axis_id, roles in geometry.candidate_installed_hardware.items()}
    if not MOVING_AXIS_IDS <= bores.keys() or not MOVING_AXIS_IDS <= hardware.keys():
        raise ValueError("four lowest cleats must own exactly the pinned 16 bolt axes")
    if any(set(hardware[axis_id]) != HARDWARE_ROLES for axis_id in MOVING_AXIS_IDS):
        raise ValueError("each moved bolt axis must retain its five component roles")
    for axis_id in MOVING_AXIS_IDS:
        bores[axis_id] = replace(bores[axis_id], shape=bores[axis_id].shape.translate(delta))
        hardware[axis_id] = {
            role: shape.translate(delta) for role, shape in hardware[axis_id].items()
        }

    fixed_axes = dict(geometry.fixed_axes)
    for axis_id in PANEL_SCREW_IDS:
        fixed_axes[axis_id] = fixed_axes[axis_id].translate(delta)

    panel_shapes = _remachine_panels(geometry.source, connections)
    panels = dict(geometry.panel_replacements)
    panels.update(panel_shapes)

    finished_hosts, host_replay = _rebuild_hosts(geometry, raw_hosts, applied_cuts, bores)
    new_finished_hosts = dict(geometry.finished_hosts)
    new_finished_hosts.update(finished_hosts)

    protected = {name: dict(rows) for name, rows in geometry.protected.items()}
    axis_protection_key = "fixed_66_hillman_axes_63p5mm"
    if axis_protection_key in protected:
        if set(protected[axis_protection_key]) != set(fixed_axes):
            raise ValueError("protected 66-Hillman axis map differs from the fixed-axis map")
        for axis_id in PANEL_SCREW_IDS:
            protected[axis_protection_key][axis_id] = fixed_axes[axis_id]

    checks = {
        **dict(geometry.composition_checks),
        "lowest_rear_support_pair_translated_by_recorded_T_offset": True,
        "four_bottom_cleats_and_all_16_bolt_axes_translated": True,
        "six_current_receiver_hosts_rebuilt_from_raw_and_current_cut_maps": True,
        "two_lower_panel_meshes_remachined_without_old_screw_holes": True,
        "four_fixed_hillman_axes_moved_with_66_axis_count_preserved": len(fixed_axes) == 66,
        "purchased_hillman_screw_policy_preserved": True,
        "baseline_native_source_reconstruction_is_not_reused_as_revision_validation": True,
        "complete_lower_edge_support_geometry_rechecked": False,
        "complete_static_scene_diagnostic": False,
        "complete_joint_acceptance": False,
        "capacity_established": False,
        "installation_proven": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    checks.pop("all_66_fixed_panel_axes_and_12_frame_bolts_preserved", None)
    revised = replace(
        geometry,
        layout_id=revision_id,
        trial_id=revision_id,
        status="unaccepted_viewer_geometry_revision",
        raw_hosts=_proxy(raw_hosts),
        finished_hosts=_proxy(new_finished_hosts),
        source_cutters_by_host=_nested_proxy(native_cuts),
        applied_source_cutters_by_host=_nested_proxy(applied_cuts),
        purchased_panel_cutters_by_host=_nested_proxy(purchase_cuts),
        raw_candidate_parts=_proxy(raw_parts),
        finished_candidate_parts=_proxy(finished_parts),
        candidate_bores=_proxy(bores),
        candidate_installed_hardware=_nested_proxy(hardware),
        fixed_axes=_proxy(fixed_axes),
        panel_replacements=_proxy(panels),
        protected=_nested_proxy(protected),
        composition_checks=_proxy(checks),
    )

    starts = {
        axis_id: [float(value) for value in source_inventory_axes[axis_id]["origin_global_xyz_mm"]]
        for axis_id in PANEL_SCREW_IDS
    }
    moved_panel_axes = [
        {
            "axis_id": axis_id,
            "visual_name": PANEL_SCREW_VISUAL_NAMES[axis_id],
            "panel_member": source_inventory_axes[axis_id]["members"][0],
            "receiver_member": source_inventory_axes[axis_id]["candidate_finished_receiver_member"],
            "old_start_global_xyz_mm": [round(value, 9) for value in starts[axis_id]],
            "new_start_global_xyz_mm": [round(value, 9) for value in (cq.Vector(*starts[axis_id]) + delta).toTuple()],
            "translation_global_xyz_mm": [round(value, 9) for value in delta.toTuple()],
            "axis_global_xyz_unchanged": list(source_inventory_axes[axis_id]["axis_global_xyz"]),
            "purchased_product_policy": "Hillman 42605; 63.5 mm nominal; no SPAX resistance, stiffness, pilot, or installation transfer",
        }
        for axis_id in sorted(PANEL_SCREW_IDS)
    ]
    current_display_ids = {
        "finished_candidate_parts": sorted(MOVING_PART_IDS),
        "finished_hosts": sorted(MOVED_HOST_IDS),
        "candidate_installed_hardware": sorted(
            f"{axis_id}/{role}" for axis_id in MOVING_AXIS_IDS for role in HARDWARE_ROLES
        ),
        "panel_replacements": sorted(PANEL_IDS),
        "fixed_panel_axes": [],
    }
    prior_display = lower_blocks_report.get("changed_display_solid_ids", {})
    report = {
        "schema": SCHEMA,
        "status": "unaccepted_viewer_geometry_revision",
        "revision_id": revision_id,
        "input_revision_id": INPUT_REVISION_ID,
        "upstream_revision_report": dict(lower_blocks_report),
        "summary": f"The lowest rear support rails move {translation_wall_t_mm:g} mm above their original position; four cleats, 16 bolt axes, and four lower-edge Hillman axes move with them.",
        "scope": "viewer geometry only; no source-level approval, force calculation, structural acceptance, drilling, or fabrication release",
        "translation_global_xyz_mm": [round(value, 9) for value in delta.toTuple()],
        "translation_wall_T_mm": translation_wall_t_mm,
        "target_rail_ids": sorted(MOVED_RAIL_IDS),
        "target_cleat_ids": sorted(MOVING_PART_IDS),
        "target_structural_axis_ids": sorted(MOVING_AXIS_IDS),
        "moved_panel_axes": moved_panel_axes,
        "baseline_display_translations_mm": {
            PANEL_SCREW_VISUAL_NAMES[axis_id]: [round(value, 9) for value in delta.toTuple()]
            for axis_id in sorted(PANEL_SCREW_IDS)
        },
        "remachined_panel_ids": sorted(PANEL_IDS),
        "replayed_host_ids": sorted(MOVED_HOST_IDS),
        "host_replay": host_replay,
        "preserved_counts": {
            "fixed_panel_axes": len(fixed_axes),
            "candidate_axes": len(bores),
            "candidate_hardware_roles": sum(map(len, hardware.values())),
            "retained_frame_bolts": len(geometry.frame_bolt_records),
        },
        "changed_display_solid_ids": _union_display_ids(prior_display, current_display_ids),
        "support_question": "The two lower-edge support rails and their receiver/backing relationships have moved; lower-panel edge support and complete load transfer remain a design-review item.",
        "checks": checks,
    }
    return revised, report
