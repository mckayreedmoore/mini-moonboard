"""Build a hypothetical 20-screw layout for each main plywood panel.

The helper keeps the frozen 66-axis input intact and appends 32 proposed
main-panel axes. It uses saved coordinates only; it does not establish fit,
installation, resistance, or acceptance.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
MODEL_INPUTS = (
    HERE.parent
    / "upper-corner-screw-layout/operators-attempt02/model-inputs.json"
)
PANEL_THICKNESS_MM = 18.25625
MAIN_PANELS = (
    "main_lower_left",
    "main_lower_right",
    "main_upper_left",
    "main_upper_right",
)


def _load_inputs(inputs: dict[str, Any] | None) -> dict[str, Any]:
    if inputs is None:
        return json.loads(MODEL_INPUTS.read_text())
    if isinstance(inputs, dict):
        return inputs
    raise TypeError("inputs must be a model-input dict or None")


def _point(record: dict[str, Any]) -> tuple[float, float, float]:
    return tuple(float(x) for x in record["source_point_xyz_mm"])


def _member_bounds(member: dict[str, Any]) -> tuple[float, ...]:
    """Read saved STEP bounds in [xmin,xmax,ymin,ymax,zmin,zmax] order."""
    return tuple(float(x) for x in member["graph_finished_geometry_summary"]["bounds_xyz_mm"])


def _inside_bounds(point: tuple[float, float, float], bounds: tuple[float, ...], tol: float = 1e-6) -> bool:
    return all(bounds[2 * i] - tol <= point[i] <= bounds[2 * i + 1] + tol for i in range(3))


def _interpolate(a: tuple[float, float, float], b: tuple[float, float, float], t: float) -> tuple[float, float, float]:
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _longest_adjacent_gaps(
    stations: list[dict[str, Any]],
    coordinate,
    count: int,
    preferred_gap: int | None = None,
) -> list[tuple[dict[str, Any], dict[str, Any], int]]:
    ordered = sorted(stations, key=lambda station: coordinate(station))
    gaps = []
    for index, (left, right) in enumerate(zip(ordered, ordered[1:])):
        span = abs(coordinate(right) - coordinate(left))
        gaps.append((span, index, left, right))
    # Stable ties: lower station first; for horizontal rows, prefer the gap
    # adjoining the outer (rim) endpoint so mirrored panels remain symmetric.
    gaps.sort(key=lambda row: (-row[0], row[1] != preferred_gap if preferred_gap is not None else False, row[1]))
    return [(left, right, index) for _, index, left, right in gaps[:count]]


def _unit_between(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    delta = tuple(b[i] - a[i] for i in range(3))
    length = math.sqrt(sum(x * x for x in delta))
    if length == 0:
        raise ValueError("vertical stations must not coincide")
    return tuple(x / length for x in delta)


def _new_connection(
    template: dict[str, Any],
    axis_id: str,
    point: tuple[float, float, float],
    template_axis_id: str,
    panel_id: str,
    edge_role: str,
    gap_index: int,
) -> dict[str, Any]:
    source = copy.deepcopy(template["source_record"])
    source["axis_id"] = axis_id
    source["origin_global_xyz_mm"] = list(point)
    source["derived_from_axis_id"] = template_axis_id
    source["current_location_status"] = "hypothetical_count20_addition; not installed or owner-authorized"
    source["hypothetical_layout"] = "20_screws_per_main_panel"
    source["hypothetical"] = True
    source["hardware_status"] = "hypothetical Hillman 42605 type/pilot only; added quantity, purchase, receiving, installation, and resistance are unestablished"
    source["purchased_policy"] = "same fastener type/pilot approach as the source; these added screws are not part of the existing 66 purchased axes"
    # A neighboring axis's positive screen is not transferable to this point.
    source["receiver_screen"] = {"status": "not evaluated for this hypothetical station"}
    source.pop("owner_moved_axis_record", None)
    source.pop("previous_receiver_screen", None)
    source.pop("translation_from_source_xyz_mm", None)
    return {
        "kind": "panel_screw",
        "axis_id": axis_id,
        "receiver_member_ids": list(template["receiver_member_ids"]),
        "source_point_xyz_mm": list(point),
        "axis_xyz": list(template["axis_xyz"]),
        "source_record": source,
        "mechanical_attachment_defined": False,
        "template_axis_id": template_axis_id,
        "hypothetical_layout": "20_screws_per_main_panel",
        "hypothetical_panel_member": panel_id,
        "hypothetical_edge_role": edge_role,
        "hypothetical_gap_index": gap_index,
    }


def build_layout(inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return copied full inputs with 32 hypothetical axes plus checks/limits."""
    source = _load_inputs(inputs)
    model_inputs = copy.deepcopy(source)
    connections = model_inputs.get("connections")
    if not isinstance(connections, list):
        raise ValueError("model inputs have no connections list")
    source_connection_count = len(connections)

    existing = [
        connection for connection in connections
        if connection.get("kind") == "panel_screw"
        and connection.get("source_record", {}).get("panel_member") in MAIN_PANELS
    ]
    members = {member["member_id"]: member for member in model_inputs.get("members", [])}
    by_panel: dict[str, list[dict[str, Any]]] = {panel: [] for panel in MAIN_PANELS}
    for connection in existing:
        by_panel[connection["source_record"]["panel_member"]].append(connection)

    additions: list[dict[str, Any]] = []
    panel_comparisons = []
    for panel_id in MAIN_PANELS:
        panel_axes = by_panel[panel_id]
        if len(panel_axes) != 12:
            raise ValueError(f"expected 12 existing axes for {panel_id}; found {len(panel_axes)}")
        indexed = {axis["axis_id"]: axis for axis in panel_axes}
        panel_bounds = _member_bounds(members[panel_id])
        created_for_panel: list[dict[str, Any]] = []
        counts = {"vertical": 0, "horizontal": 0}

        for role in ("rim", "center"):
            vertical = [indexed[f"round_panel_{panel_id.removeprefix('main_')}_{role}_{i}"] for i in range(1, 5)]
            tangent = _unit_between(_point(vertical[0]), _point(vertical[-1]))
            parameter = lambda station: sum(x * y for x, y in zip(_point(station), tangent))
            for left, right, gap_index in _longest_adjacent_gaps(vertical, parameter, 2):
                new_point = _interpolate(_point(left), _point(right), 0.5)
                template = min((left, right), key=lambda axis: (parameter(axis), axis["axis_id"]))
                axis_id = f"hyp20_{panel_id}_{role}_gap_{gap_index + 1}"
                created_for_panel.append(_new_connection(template, axis_id, new_point, template["axis_id"], panel_id, role, gap_index + 1))
                counts["vertical"] += 1

        panel_key = panel_id.removeprefix("main_")
        for rail_role in ("edge", "service"):
            rail_screws = [indexed[f"round_panel_{panel_key}_{rail_role}_{i}"] for i in (1, 2)]
            rail_parameter = sum(x * y for x, y in zip(_point(rail_screws[0]), tangent))
            # The four current horizontal stations are the rail pair plus the
            # nearest current rim and center stations at this rail's row.
            vertical_ends = []
            for column in ("rim", "center"):
                stations = [indexed[f"round_panel_{panel_key}_{column}_{i}"] for i in range(1, 5)]
                vertical_ends.append(min(stations, key=lambda axis: (abs(parameter(axis) - rail_parameter), axis["axis_id"])))
            x_stations = [*vertical_ends, *rail_screws]
            xs = sorted(float(axis["source_point_xyz_mm"][0]) for axis in x_stations)
            if len(set(xs)) != 4:
                raise ValueError(f"expected four distinct {rail_role} horizontal stations for {panel_id}")
            rim_x = float(vertical_ends[0]["source_point_xyz_mm"][0])
            preferred_gap = 0 if rim_x < min(xs) + 1e-8 else 2
            for left, right, gap_index in _longest_adjacent_gaps(x_stations, lambda axis: axis["source_point_xyz_mm"][0], 2, preferred_gap):
                x = (float(left["source_point_xyz_mm"][0]) + float(right["source_point_xyz_mm"][0])) / 2
                # Preserve the actual horizontal rail station (not the
                # vertical endpoint row) and its receiver/direction reference.
                template = min(rail_screws, key=lambda axis: (abs(axis["source_point_xyz_mm"][0] - x), axis["axis_id"]))
                rail_point = _point(template)
                new_point = (x, rail_point[1], rail_point[2])
                axis_id = f"hyp20_{panel_id}_{rail_role}_gap_{gap_index + 1}"
                created_for_panel.append(_new_connection(template, axis_id, new_point, template["axis_id"], panel_id, rail_role, gap_index + 1))
                counts["horizontal"] += 1

        if counts != {"vertical": 4, "horizontal": 4}:
            raise AssertionError(f"unexpected addition census for {panel_id}: {counts}")

        interface_in_receiver = 0
        front_in_panel = 0
        for axis in created_for_panel:
            front = _point(axis)
            panel_ok = _inside_bounds(front, panel_bounds)
            direction = tuple(float(v) for v in axis["axis_xyz"])
            interface = tuple(front[i] + direction[i] * PANEL_THICKNESS_MM for i in range(3))
            receiver = axis["source_record"]["receiver_member"]
            receiver_ok = _inside_bounds(interface, _member_bounds(members[receiver]))
            axis["source_record"]["saved_coordinate_screen"] = {
                "panel_front_origin_inside_saved_finished_member_aabb": panel_ok,
                "interface_point_inside_saved_receiver_finished_member_aabb": receiver_ok,
                "interface_offset_along_axis_mm": PANEL_THICKNESS_MM,
                "screen_limit": "AABB only; not a B-rep intersection or installation-clearance check",
            }
            front_in_panel += bool(panel_ok)
            interface_in_receiver += bool(receiver_ok)
        additions.extend(created_for_panel)
        panel_comparisons.append({
            "panel_member": panel_id,
            "existing_main_panel_screws": len(panel_axes),
            "added_hypothetical_screws": len(created_for_panel),
            "proposed_main_panel_screws": len(panel_axes) + len(created_for_panel),
            "added_vertical": counts["vertical"],
            "added_horizontal": counts["horizontal"],
            "hypothetical_front_origins_inside_panel_aabb": front_in_panel,
            "hypothetical_interface_points_inside_receiver_aabb": interface_in_receiver,
            "hypothetical_additions": [axis["axis_id"] for axis in created_for_panel],
        })

    original_axis_ids = {axis["axis_id"] for axis in connections}
    if any(axis["axis_id"] in original_axis_ids for axis in additions):
        raise ValueError("hypothetical axis id collides with a source axis")
    model_inputs["connections"].extend(copy.deepcopy(additions))
    source_bytes = json.dumps(source, sort_keys=True, separators=(",", ":")).encode()
    return {
        "model_inputs": model_inputs,
        "added_connections": additions,
        "comparisons": {
            "source_model_inputs_canonical_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "source_connection_count": source_connection_count,
            "added_hypothetical_panel_screws": len(additions),
            "main_panel_screws": 80,
            "unchanged_kicker_screws": sum(
                1 for connection in connections
                if connection.get("kind") == "panel_screw"
                and connection.get("source_record", {}).get("panel_member", "").startswith("kicker_")
            ),
            "panel_screw_total_in_proposed_input": sum(
                1 for connection in model_inputs["connections"] if connection.get("kind") == "panel_screw"
            ),
            "panels": panel_comparisons,
            "all_saved_coordinate_aabb_checks_pass": all(
                panel["hypothetical_front_origins_inside_panel_aabb"] == 8
                and panel["hypothetical_interface_points_inside_receiver_aabb"] == 8
                for panel in panel_comparisons
            ),
        },
        "limits": [
            "32 new stations are hypothetical only; the existing 66 axes are preserved, while the added count is not purchased or approved.",
            "AABB membership is a coarse saved-coordinate screen; it does not test exact panel outlines, receiver solids, edges, fastener spacing, clearance, or structural resistance.",
            "Each added axis inherits direction and receiver identity from a named source template; that identity still needs exact receiver geometry and connection qualification.",
            "No screw force redistribution, capacity comparison, strength result, or acceptance is calculated.",
        ],
    }
