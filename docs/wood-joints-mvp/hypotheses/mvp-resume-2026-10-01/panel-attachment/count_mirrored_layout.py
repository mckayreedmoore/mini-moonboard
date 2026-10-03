"""Mirror the hypothetical horizontal gap choice across right-side panels.

The original count-layout packet is frozen. This wrapper changes only the
four right-side hypothetical horizontal additions from the inner gap to the
outer gap, preserving the middle-gap station and all source axes.
"""

from __future__ import annotations

import copy
import math
from typing import Any

from count_layout import MAIN_PANELS, PANEL_THICKNESS_MM
from count_layout import build_layout as build_count_layout


def _member_bounds(member: dict[str, Any]) -> tuple[float, ...]:
    return tuple(float(x) for x in member["graph_finished_geometry_summary"]["bounds_xyz_mm"])


def _inside(point: tuple[float, float, float], bounds: tuple[float, ...], tolerance: float = 1e-6) -> bool:
    return all(bounds[2 * i] - tolerance <= point[i] <= bounds[2 * i + 1] + tolerance for i in range(3))


def _point(connection: dict[str, Any]) -> tuple[float, float, float]:
    return tuple(float(x) for x in connection["source_point_xyz_mm"])


def _parameter(connection: dict[str, Any], tangent: tuple[float, ...]) -> float:
    return sum(a * b for a, b in zip(_point(connection), tangent))


def _closest_at_parameter(
    stations: list[dict[str, Any]], target: float, tangent: tuple[float, ...]
) -> dict[str, Any]:
    return min(
        stations,
        key=lambda connection: (abs(_parameter(connection, tangent) - target), connection["axis_id"]),
    )


def _replace_hypothetical(
    existing: dict[str, Any],
    template: dict[str, Any],
    axis_id: str,
    point: tuple[float, float, float],
    gap_index: int,
    panel_id: str,
    rail_role: str,
    saved_members: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source = copy.deepcopy(template["source_record"])
    source.update(
        axis_id=axis_id,
        origin_global_xyz_mm=list(point),
        derived_from_axis_id=template["axis_id"],
        current_location_status="hypothetical_count20_addition; not installed or owner-authorized",
        hypothetical_layout="20_screws_per_main_panel",
        hypothetical=True,
        hardware_status=existing["source_record"]["hardware_status"],
        purchased_policy=existing["source_record"]["purchased_policy"],
        receiver_screen={"status": "not evaluated for this hypothetical station"},
    )
    source.pop("owner_moved_axis_record", None)
    source.pop("previous_receiver_screen", None)
    source.pop("translation_from_source_xyz_mm", None)
    receiver = source["receiver_member"]
    interface = tuple(point[i] + float(template["axis_xyz"][i]) * PANEL_THICKNESS_MM for i in range(3))
    panel_ok = _inside(point, _member_bounds(saved_members[panel_id]))
    receiver_ok = _inside(interface, _member_bounds(saved_members[receiver]))
    source["saved_coordinate_screen"] = {
        "panel_front_origin_inside_saved_finished_member_aabb": panel_ok,
        "interface_point_inside_saved_receiver_finished_member_aabb": receiver_ok,
        "interface_offset_along_axis_mm": PANEL_THICKNESS_MM,
        "screen_limit": "AABB only; not a B-rep intersection or installation-clearance check",
    }
    updated = copy.deepcopy(existing)
    updated.update(
        axis_id=axis_id,
        receiver_member_ids=list(template["receiver_member_ids"]),
        source_point_xyz_mm=list(point),
        axis_xyz=list(template["axis_xyz"]),
        source_record=source,
        template_axis_id=template["axis_id"],
        hypothetical_panel_member=panel_id,
        hypothetical_edge_role=rail_role,
        hypothetical_gap_index=gap_index,
    )
    return updated


def build_layout(inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the count-layout result with symmetric outer/middle row choices."""
    result = copy.deepcopy(build_count_layout(inputs))
    model_inputs = result["model_inputs"]
    members = {member["member_id"]: member for member in model_inputs["members"]}
    source_axes = {connection["axis_id"]: connection for connection in model_inputs["connections"]}
    added_by_id = {connection["axis_id"]: connection for connection in result["added_connections"]}
    replacements_by_old_id = {}
    changes = []

    for panel_id in MAIN_PANELS:
        if not panel_id.endswith("_right"):
            continue
        panel_key = panel_id.removeprefix("main_")
        for rail_role in ("edge", "service"):
            old_id = f"hyp20_{panel_id}_{rail_role}_gap_1"
            if old_id not in added_by_id:
                raise ValueError(f"missing original inner-gap addition {old_id}")
            old = added_by_id[old_id]
            rail = [source_axes[f"round_panel_{panel_key}_{rail_role}_{i}"] for i in (1, 2)]
            rim = [source_axes[f"round_panel_{panel_key}_rim_{i}"] for i in range(1, 5)]
            center = [source_axes[f"round_panel_{panel_key}_center_{i}"] for i in range(1, 5)]

            low, high = _point(center[0]), _point(center[-1])
            tangent = tuple((high[i] - low[i]) for i in range(3))
            length = math.sqrt(sum(v * v for v in tangent))
            if not length:
                raise ValueError(f"degenerate panel vertical axis: {panel_id}")
            tangent = tuple(v / length for v in tangent)
            rail_t = _parameter(rail[0], tangent)
            rim_end = _closest_at_parameter(rim, rail_t, tangent)
            center_end = _closest_at_parameter(center, rail_t, tangent)
            ordered = sorted([rim_end, center_end, *rail], key=lambda connection: float(connection["source_point_xyz_mm"][0]))
            outer_pair = ordered[-2:]
            outer_x = (float(outer_pair[0]["source_point_xyz_mm"][0]) + float(outer_pair[1]["source_point_xyz_mm"][0])) / 2
            template = min(rail, key=lambda connection: (abs(float(connection["source_point_xyz_mm"][0]) - outer_x), connection["axis_id"]))
            template_point = _point(template)
            new_point = (outer_x, template_point[1], template_point[2])
            new_id = f"hyp20_{panel_id}_{rail_role}_gap_3"
            if new_id in source_axes:
                raise ValueError(f"hypothetical id already exists: {new_id}")
            if old["template_axis_id"] != f"round_panel_{panel_key}_{rail_role}_1":
                raise ValueError(f"unexpected original inner-gap template for {old_id}")
            updated = _replace_hypothetical(
                old, template, new_id, new_point, 3, panel_id, rail_role, members
            )
            model_record = next(connection for connection in model_inputs["connections"] if connection["axis_id"] == old_id)
            model_record.clear()
            model_record.update(copy.deepcopy(updated))
            replacements_by_old_id[old_id] = model_record
            changes.append({
                "panel_member": panel_id,
                "rail_role": rail_role,
                "old_axis_id": old_id,
                "old_x_mm": old["source_point_xyz_mm"][0],
                "new_axis_id": new_id,
                "new_x_mm": new_point[0],
                "new_gap_index": 3,
                "template_axis_id": template["axis_id"],
                "receiver_member": updated["source_record"]["receiver_member"],
                "saved_coordinate_screen": updated["source_record"]["saved_coordinate_screen"],
            })

    if len(changes) != 4:
        raise AssertionError(f"expected four right-side horizontal changes; found {len(changes)}")
    result["added_connections"] = [
        replacements_by_old_id.get(connection["axis_id"], connection)
        for connection in result["added_connections"]
    ]

    for panel in result["comparisons"]["panels"]:
        panel["hypothetical_additions"] = [
            next((change["new_axis_id"] for change in changes if change["old_axis_id"] == axis_id), axis_id)
            for axis_id in panel["hypothetical_additions"]
        ]
    result["comparisons"]["mirrored_horizontal_adjustments"] = changes
    result["comparisons"]["all_saved_coordinate_aabb_checks_pass"] = all(
        addition["source_record"]["saved_coordinate_screen"]["panel_front_origin_inside_saved_finished_member_aabb"]
        and addition["source_record"]["saved_coordinate_screen"]["interface_point_inside_saved_receiver_finished_member_aabb"]
        for addition in result["added_connections"]
    )
    result["limits"].append("Mirrored layout selects the outer and middle adjacent gaps on each horizontal row; it changes only four hypothetical right-side stations.")
    return result
