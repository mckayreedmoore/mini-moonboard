"""Bounded staging and access screen for the unaccepted WJ-04 right pair.

The default output is a source-bound operation plan. ``--materialize`` runs
the frozen G7 crosscut geometry and screens two one-axis rail moves plus local
principal-bolt wrench poses. It does not establish a field procedure, a stable
temporary frame, joint acceptance, or hardware fit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from mini_moonboard.hold_tnut_reinforcement import datums as hold_datums
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_tool_access as tool_access
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as g7_probe

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = "docs/wood-joints-mvp/source-inventory.json"
SCHEMA = "wood_joint_wj04_pair_access/v1"
LOWER_STATION = g7_probe.LOWER_STATION
UPPER_STATION = g7_probe.UPPER_STATION
LOWER_RAIL = g7_probe.LOWER_RAIL
UPPER_RAIL = g7_probe.UPPER_RAIL
LOWER_CLEAT = g7_probe.LOWER_CLEAT
UPPER_CLEAT = g7_probe.UPPER_CLEAT
PRINCIPAL = g7_probe.PRINCIPAL
RIGHT_PANELS = ("main_lower_right", "main_upper_right")
OUTER_DUTIES = (
    "clip_horizontal_lower_right_2",
    "clip_horizontal_upper_right_2",
)
PANEL_FASTENER_COUNT = 12
RIGHT_PANEL_TNUT_COUNT = 30
ALL_MAIN_TNUT_COUNT = 142
LIGHT_COUNT = 132
WIRE_COUNT = 131
HIT_TOLERANCE_MM3 = 1e-6
EXIT_CLEARANCE_MM = 25.0
WORKING_STROKE_DEGREES = 30.0

SOURCE_INPUTS = tuple(
    dict.fromkeys(
        (
            INVENTORY,
            "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py",
            *g7_probe.SOURCE_INPUTS,
            "scripts/wood_joint_wj04_pair_access.py",
            "scripts/owner_layout_protected.py",
            "scripts/wood_joint_clearance.py",
            "mini_moonboard/hold_tnut_reinforcement.py",
            "mini_moonboard/panel_grid.py",
            "mini_moonboard/panel_grid_v2.py",
            "scripts/wood_joint_wj04_tool_access.py",
        )
    )
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_snapshot() -> dict[str, str]:
    return {path: _sha256(ROOT / path) for path in SOURCE_INPUTS}


def _inventory() -> dict[str, Any]:
    result = json.loads((ROOT / INVENTORY).read_text())
    if _sha256(ROOT / INVENTORY) != WJ04_TRIAL.source_inventory_sha256:
        raise ValueError("live source inventory differs from the pinned WJ-04 input")
    return result


def _right_main_tnut_datums() -> tuple[dict[str, Any], ...]:
    """Return exact panel ownership for right-side main T-nut/projection IDs."""
    model = variant(KERF_RIGHT)
    rows = tuple(row for row in hold_datums(model) if row.get("panel") in RIGHT_PANELS)
    names = [row.get("name") for row in rows]
    if len(names) != 60 or len(set(names)) != 60:
        raise ValueError("right-panel T-nut datum inventory must contain 60 unique IDs")
    counts = {panel: sum(row.get("panel") == panel for row in rows) for panel in RIGHT_PANELS}
    if any(counts[panel] != RIGHT_PANEL_TNUT_COUNT for panel in RIGHT_PANELS):
        raise ValueError("right main panels must own 30 T-nuts each")
    if any(not row.get("name", "").startswith("hold_tnut_main_") for row in rows):
        raise ValueError("right main panel datum selected a non-main T-nut")
    return rows


def _panel_off_state(
    inventory: Mapping[str, Any], tnut_datums: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Validate and describe the limited, reversible panel-off state."""
    axes = list(inventory.get("fixed_panel_kicker_screws", ()))
    axis_ids = [row.get("axis_id") for row in axes]
    if len(set(axis_ids)) != len(axis_ids):
        raise ValueError("duplicate panel fastener axis ID")
    if any(not isinstance(axis_id, str) or not axis_id for axis_id in axis_ids):
        raise ValueError("fixed panel fastener axis IDs must be nonempty strings")

    panel_fasteners: dict[str, list[str]] = {}
    for panel in RIGHT_PANELS:
        selected = [row["axis_id"] for row in axes if row.get("panel_member") == panel]
        if len(selected) != PANEL_FASTENER_COUNT or len(set(selected)) != PANEL_FASTENER_COUNT:
            raise ValueError(f"expected 12 unique panel fastener axes for {panel}")
        panel_fasteners[panel] = sorted(selected)
    if len(axes) != 66:
        raise ValueError("fixed panel/kicker inventory must contain 66 axes")

    tnut_rows = list(tnut_datums)
    tnut_ids = [row.get("name") for row in tnut_rows]
    if len(tnut_ids) != 60 or len(set(tnut_ids)) != 60:
        raise ValueError("right main T-nut removals must contain 60 unique IDs")
    if any(not isinstance(name, str) or not name for name in tnut_ids):
        raise ValueError("right main T-nut IDs must be nonempty strings")
    for panel in RIGHT_PANELS:
        selected = [row for row in tnut_rows if row.get("panel") == panel]
        if len(selected) != RIGHT_PANEL_TNUT_COUNT:
            raise ValueError(f"expected 30 attached T-nuts for {panel}")

    frame_bolts = list(inventory.get("starting_frame_bolts", ()))
    frame_ids = [row.get("axis_id") for row in frame_bolts]
    if len(frame_bolts) != 12 or len(set(frame_ids)) != 12:
        raise ValueError("starting frame-bolt inventory must contain 12 unique axes")

    return {
        "panels_removed": list(RIGHT_PANELS),
        "attached_tnut_ids_removed": sorted(tnut_ids),
        "hold_projection_ids_removed_with_panels": sorted(tnut_ids),
        "panel_fastener_axis_ids_removed_for_detachment": sorted(
            axis_id for rows in panel_fasteners.values() for axis_id in rows
        ),
        "panel_fastener_axis_ids_by_panel": panel_fasteners,
        "panel_fastener_axes_temporarily_removed": 24,
        "hold_hardware_and_projection_scope": (
            "Only the right-panel T-nuts and matching provisional hold projection "
            "envelopes move with the two detached panels; no delivered hold bolt "
            "fit is represented."
        ),
        "lights_remain_fixed_count": LIGHT_COUNT,
        "wires_remain_fixed_count": WIRE_COUNT,
        "frame_bolt_obligations_retained": len(frame_bolts),
        "panel_kicker_axis_obligations_retained": len(axes),
        "panel_removal_path_verified": False,
        "panel_screw_removal_path_verified": False,
    }


def _outer_duty_prerequisites(inventory: Mapping[str, Any]) -> dict[str, Any]:
    expected = set(OUTER_DUTIES)
    rows = {
        row.get("legacy_station_id"): row
        for row in inventory.get("legacy_duties", ())
        if row.get("legacy_station_id") in expected
    }
    if set(rows) != expected:
        raise ValueError("both right outer legacy duties are required as prerequisites")
    duties = {}
    all_axis_ids: list[str] = []
    for duty_id in OUTER_DUTIES:
        row = rows[duty_id]
        axes = row.get("legacy_sds_axes", ())
        axis_ids = [axis.get("axis_id") for axis in axes]
        if len(axis_ids) != 6 or len(set(axis_ids)) != 6:
            raise ValueError(f"{duty_id}: expected six unique unresolved SDS axes")
        if not all(isinstance(axis_id, str) and axis_id for axis_id in axis_ids):
            raise ValueError(f"{duty_id}: every legacy SDS axis needs a stable ID")
        all_axis_ids.extend(axis_ids)
        duties[duty_id] = {
            "status": "unresolved_prerequisite",
            "legacy_host_members": list(row.get("legacy_host_members", ())),
            "legacy_sds_axis_count": len(axis_ids),
            "legacy_sds_axis_ids": sorted(axis_ids),
            "replacement_owner": "unresolved",
            "replacement_accepted": False,
        }
    if len(all_axis_ids) != len(set(all_axis_ids)):
        raise ValueError("right outer duty SDS axis IDs must be unique across duties")
    return {
        "status": "unresolved_prerequisite",
        "removed_from_obstacle_map": False,
        "accepted_replacement_count": 0,
        "duties": duties,
        "staging_dependency": (
            "Service-rail release/removal and the eventual far-end replacement "
            "connection are unresolved; this probe retains their source angle/SDS "
            "geometry as obstacles."
        ),
    }


def trial_plan() -> dict[str, Any]:
    """Return the explicit staging states without creating CAD geometry."""
    inventory = _inventory()
    panel_state = _panel_off_state(inventory, _right_main_tnut_datums())
    outer = _outer_duty_prerequisites(inventory)
    axes = list(inventory["fixed_panel_kicker_screws"])
    frame_bolts = list(inventory["starting_frame_bolts"])
    if len(axes) != 66 or len(frame_bolts) != 12:
        raise ValueError("paired access plan must retain 66 panel axes and 12 frame bolts")

    tool = WJ04_TRIAL.fasteners.tools[0]
    if tool.candidate_id != "facom_34_7_16":
        raise ValueError("paired access screen requires the pinned FACOM 34 proxy")
    principal_stacks = [
        "lower_principal_1",
        "lower_principal_2",
        "upper_principal_1",
        "upper_principal_2",
    ]
    return {
        "schema": SCHEMA,
        "trial_id": "wj04_right_pair_access_staging_hypothesis",
        "status": "unaccepted_access_hypothesis",
        "source_inventory_sha256": _sha256(ROOT / INVENTORY),
        "canonical_wj04_config_sha256": WJ04_TRIAL.canonical_sha256,
        "source_inputs_sha256": _source_snapshot(),
        "fixed_obligations": {
            "panel_kicker_screw_axes": len(axes),
            "starting_frame_bolts": len(frame_bolts),
            "accepted_replacement_count": 0,
            "cad_environment_materialized": False,
        },
        "operations": {
            "panel_off_state": panel_state,
            "off_frame_t_bolt_assembly": {
                "member_pairings": [
                    {"station_id": LOWER_STATION, "rail_id": LOWER_RAIL, "cleat_id": LOWER_CLEAT},
                    {"station_id": UPPER_STATION, "rail_id": UPPER_RAIL, "cleat_id": UPPER_CLEAT},
                ],
                "rail_to_cleat_stack_ids": [
                    "lower_rail_1",
                    "lower_rail_2",
                    "upper_rail_1",
                    "upper_rail_2",
                ],
                "principal_x_bolts_installed_off_frame": False,
                "service_rail_temporarily_out_of_frame": True,
                "outer_duty_prerequisite_status": "unresolved",
                "external_environment_screen": "not_modeled_off_frame",
                "field_assembly_or_stability_proven": False,
            },
            "rail_cleat_placement_removal": {
                "moving_member_sets": [
                    {"station_id": LOWER_STATION, "rail_id": LOWER_RAIL, "cleat_id": LOWER_CLEAT},
                    {"station_id": UPPER_STATION, "rail_id": UPPER_RAIL, "cleat_id": UPPER_CLEAT},
                ],
                "translation_axis": "source WJ04 global N axis",
                "directions_checked": ["+N", "-N"],
                "stand_off_strategy": (
                    "At materialization, extend each one-axis sweep until the moving "
                    "member's N projection clears the fixed obstacle projection by "
                    f"{EXIT_CLEARANCE_MM:g} mm. This is not a route around the frame."
                ),
                "outer_duty_obstacles_retained": True,
                "side_member_release_modeled": False,
                "screen_status": "pending_materialization",
            },
            "outer_duty_prerequisites": outer,
            "principal_x_bolt_tool_screen": {
                "stack_ids": principal_stacks,
                "environment_state": "panel_off_right_upper_and_lower",
                "candidate_id": tool.candidate_id,
                "catalog_description": tool.description,
                "external_proxy_dimensions_mm": {
                    "head_diameter_and_handle_width": tool.head_width_mm,
                    "head_thickness": tool.head_thickness_mm,
                    "overall_length": tool.overall_length_mm,
                },
                "catalog_head_offsets_degrees": list(tool.head_offsets_degrees),
                "offset_values_are_exact_jaw_pose": False,
                "working_stroke_degrees": WORKING_STROKE_DEGREES,
                "one_flat_reindex_degrees": 2.0 * WORKING_STROKE_DEGREES,
                "counterhold_pose": "stationary head-side FACOM external proxy",
                "nut_pose": "bounded nut-side open-end proxy stroke/exit/reindex/reseat",
                "full_repeatable_nut_removal_proven": False,
                "screen_status": "pending_materialization",
            },
            "final_fit_state": {
                "right_panels_and_attached_tnuts_restored": True,
                "all_66_panel_kicker_axes_present_as_obligations": True,
                "all_142_tnut_and_hold_projection_envelopes_restored": True,
                "all_lights_and_wires_fixed": True,
                "all_12_frame_bolt_obligations_retained": True,
                "screen_status": "pending_materialization",
            },
        },
        "claim_boundary": {
            "accepted_replacement_count": 0,
            "physical_assembly_procedure_accepted": False,
            "temporary_stability_established": False,
            "full_load_path_established": False,
            "hardware_fit_established": False,
            "drilling_released": False,
            "fabrication_released": False,
        },
    }


def _panel_off_maps(geometry: Any, plan: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Remove only the documented panel-owned obstacles for that state."""
    panel_state = plan["operations"]["panel_off_state"]
    panels = dict(geometry.panels)
    if not set(RIGHT_PANELS).issubset(panels):
        raise ValueError("geometry is missing one of the two right main panels")
    for panel_id in RIGHT_PANELS:
        panels.pop(panel_id)

    protected = dict(geometry.protected)
    inventory = _inventory()
    frame_bolt_ids = [row["axis_id"] for row in inventory["starting_frame_bolts"]]
    expected_removed = {
        *(f"tnuts/{tnut_id}" for tnut_id in panel_state["attached_tnut_ids_removed"]),
        *(
            f"hold_hole_and_trial_projection/{tnut_id}"
            for tnut_id in panel_state["hold_projection_ids_removed_with_panels"]
        ),
        *(
            f"panel_screws/{axis_id}"
            for axis_id in panel_state["panel_fastener_axis_ids_removed_for_detachment"]
        ),
    }
    missing = expected_removed - set(protected)
    if missing:
        raise ValueError(f"panel-off obstacle map is missing expected IDs: {sorted(missing)}")
    for obstacle_id in expected_removed:
        protected.pop(obstacle_id)

    for family in ("tnuts/", "hold_hole_and_trial_projection/"):
        if sum(name.startswith(family) for name in geometry.protected) != ALL_MAIN_TNUT_COUNT:
            raise ValueError(f"source protected map must contain 142 items in {family}")
        if sum(name.startswith(family) for name in protected) != (
            ALL_MAIN_TNUT_COUNT - len(panel_state["attached_tnut_ids_removed"])
        ):
            raise ValueError(f"panel-off state did not retain all unrelated {family} items")

    light_ids = {name for name in protected if name.startswith("lights/")}
    wire_ids = {name for name in protected if name.startswith("wires/")}
    if len(light_ids) != LIGHT_COUNT or len(wire_ids) != WIRE_COUNT:
        raise ValueError("panel-off state must retain all 132 lights and 131 wires")
    if len([name for name in protected if name.startswith("panel_screws/")]) != 42:
        raise ValueError("panel-off state must leave the other 42 panel axes present")
    frame_roles = ("shaft", "head_washer", "nut_washer", "head", "nut")
    expected_frame_components = {
        f"frame_bolt_components/{axis_id}/{role}"
        for axis_id in frame_bolt_ids
        for role in frame_roles
    }
    if not expected_frame_components.issubset(protected):
        raise ValueError("panel-off state must retain all 12 installed frame-bolt stacks")
    return panels, protected


def _outer_obstacle_ids(geometry: Any) -> set[str]:
    inventory = _inventory()
    expected = _outer_duty_prerequisites(inventory)
    protected_ids = set(geometry.protected)
    required = set()
    for duty_id, row in expected["duties"].items():
        required.add(f"retained_legacy_connectors/{duty_id}")
        required.update(
            f"retained_legacy_sds/{axis_id}" for axis_id in row["legacy_sds_axis_ids"]
        )
    missing = required - protected_ids
    if missing:
        raise ValueError(f"unresolved outer duty geometry is missing: {sorted(missing)}")
    return required


def _as_compound(shapes: Sequence[cq.Shape]) -> cq.Shape:
    if not shapes:
        raise ValueError("moving assembly must contain at least one shape")
    return cq.Compound.makeCompound(list(shapes))


def _projection_bounds(shape: cq.Shape, axis: cq.Vector) -> tuple[float, float]:
    bounds = shape.BoundingBox()
    corners = (
        cq.Vector(x, y, z)
        for x in (bounds.xmin, bounds.xmax)
        for y in (bounds.ymin, bounds.ymax)
        for z in (bounds.zmin, bounds.zmax)
    )
    projections = [corner.dot(axis) for corner in corners]
    if not projections or not all(math.isfinite(value) for value in projections):
        raise ValueError("source-bounded movement requires a finite shape bound")
    return min(projections), max(projections)


def _map_projection_bounds(shapes: Mapping[str, cq.Shape], axis: cq.Vector) -> tuple[float, float]:
    bounds = [_projection_bounds(shape, axis) for shape in shapes.values()]
    if not bounds:
        raise ValueError("movement screen requires fixed environment obstacles")
    return min(low for low, _high in bounds), max(high for _low, high in bounds)


def _final_environment(geometry: Any, panels: Mapping[str, cq.Shape], protected: Mapping[str, cq.Shape]) -> dict[str, cq.Shape]:
    other_wood = {
        name: shape
        for name, shape in geometry.all_wood.items()
        if name not in geometry.parts
    }
    wood = {**other_wood, **geometry.finished}
    return {
        **{f"wood/{name}": shape for name, shape in wood.items()},
        **{f"panels/{name}": shape for name, shape in panels.items()},
        **{f"protected/{name}": shape for name, shape in protected.items()},
        **{
            f"hardware/{stack_id}/{role}": shape
            for stack_id, components in geometry.installed.items()
            for role, shape in components.items()
        },
    }


def _rail_move_screens(
    geometry: Any,
    plan: Mapping[str, Any],
    panel_off_panels: Mapping[str, cq.Shape],
    panel_off_protected: Mapping[str, cq.Shape],
) -> dict[str, Any]:
    n_axis = cq.Vector(*WJ04_TRIAL.frame.n_global).normalized()
    outer_required = _outer_obstacle_ids(geometry)
    paired_environment = _final_environment(
        geometry, panel_off_panels, panel_off_protected
    )
    results = {}
    for station_id, rail_id, cleat_id, prefix in (
        (LOWER_STATION, LOWER_RAIL, LOWER_CLEAT, "lower"),
        (UPPER_STATION, UPPER_RAIL, UPPER_CLEAT, "upper"),
    ):
        rail_stack_ids = (f"{prefix}_rail_1", f"{prefix}_rail_2")
        moving_names = {f"wood/{rail_id}", f"wood/{cleat_id}"}
        moving_names.update(
            f"hardware/{stack_id}/{role}"
            for stack_id in rail_stack_ids
            for role in geometry.installed[stack_id]
        )
        moving = _as_compound(
            [
                geometry.finished[rail_id],
                geometry.finished[cleat_id],
                *(
                    shape
                    for stack_id in rail_stack_ids
                    for shape in geometry.installed[stack_id].values()
                ),
            ]
        )
        obstacles = {
            name: shape
            for name, shape in paired_environment.items()
            if name not in moving_names
            and not name.startswith(f"hardware/{prefix}_principal_")
        }
        obstacle_low, obstacle_high = _map_projection_bounds(obstacles, n_axis)
        moving_low, moving_high = _projection_bounds(moving, n_axis)
        plus_distance = max(
            1.0, obstacle_high - moving_low + EXIT_CLEARANCE_MM
        )
        minus_distance = max(
            1.0, moving_high - obstacle_low + EXIT_CLEARANCE_MM
        )
        direction_hits = {}
        for direction_id, displacement in (
            ("+N", n_axis * plus_distance),
            ("-N", -n_axis * minus_distance),
        ):
            swept = tool_access.translation_sweep(moving, displacement)
            hits = tool_access.collision_report(
                {"one_axis_rail_cleat_sweep": swept}, obstacles
            )["external_envelope_hits_mm3"]
            direction_hits[direction_id] = {
                "displacement_mm": round(displacement.Length, 6),
                "fixed_obstacle_projection_clearance_mm": EXIT_CLEARANCE_MM,
                "hit_obstacle_ids": sorted(
                    next(iter(hits.values()), {}).keys()
                ),
                "hits_mm3": next(iter(hits.values()), {}),
                "outer_duty_hit_ids": sorted(
                    obstacle_id.removeprefix("protected/")
                    for obstacle_id in next(iter(hits.values()), {})
                    if obstacle_id.removeprefix("protected/") in outer_required
                ),
                "envelope_clear": not hits,
                "bounds_are_conservative": True,
                "physical_move_proven": False,
            }
        results[station_id] = {
            "moving_member_ids": [rail_id, cleat_id],
            "attached_t_bolt_stack_ids": list(rail_stack_ids),
            "principal_x_bolts_installed_during_move": False,
            "retained_outer_duty_geometry_ids": sorted(
                obstacle_id for obstacle_id in obstacles if obstacle_id.removeprefix("protected/") in outer_required
            ),
            "directions": direction_hits,
            "side_member_release_modeled": False,
            "outer_duty_resolution_required_before_field_removal": True,
        }
    return results


def _reference_axis(direction: cq.Vector) -> cq.Vector:
    cardinals = (cq.Vector(1, 0, 0), cq.Vector(0, 1, 0), cq.Vector(0, 0, 1))
    reference = min(cardinals, key=lambda item: abs(item.dot(direction)))
    return (reference - direction * reference.dot(direction)).normalized()


def _principal_tool_screens(
    geometry: Any,
    panel_off_panels: Mapping[str, cq.Shape],
    panel_off_protected: Mapping[str, cq.Shape],
) -> dict[str, Any]:
    environment = _final_environment(geometry, panel_off_panels, panel_off_protected)
    tool = WJ04_TRIAL.fasteners.tools[0]
    results = {}
    for stack_id in (
        "lower_principal_1",
        "lower_principal_2",
        "upper_principal_1",
        "upper_principal_2",
    ):
        stack = geometry.stacks[stack_id]
        direction = cq.Vector(stack.direction).normalized()
        installed = geometry.installed[stack_id]
        center = cq.Vector(stack.head_seat.center)
        head_outward = -direction
        nut_outward = direction
        head_center = tool_access._seated_tool_center(
            center,
            head_outward,
            installed["head"],
            tool.head_thickness_mm,
        )
        nut_center = tool_access._seated_tool_center(
            stack.nut_seat.center,
            nut_outward,
            installed["nut"],
            tool.head_thickness_mm,
        )
        axis_reference = _reference_axis(direction)
        cases = []
        for heading in tool.head_offsets_degrees:
            head_wrench = tool_access.build_catalog_wrench_envelope(
                head_center,
                head_outward.toTuple(),
                axis_reference,
                tool,
                offset_degrees=heading,
            )
            nut_wrench = tool_access.build_catalog_wrench_envelope(
                nut_center,
                nut_outward.toTuple(),
                axis_reference,
                tool,
                offset_degrees=heading,
            )
            movement = tool_access.wrench_reindex_path(
                nut_wrench,
                nut_center,
                nut_outward.toTuple(),
                tool_access._tool_frame(
                    nut_outward, axis_reference, heading
                )[0],
                flat_stroke_degrees=WORKING_STROKE_DEGREES,
                head_width_mm=tool.head_width_mm,
            )
            stationary = tool_access.collision_report(
                {"head_counterhold": head_wrench},
                environment,
                excluded_target_ids=(
                    f"hardware/{stack_id}/head",
                    f"hardware/{stack_id}/shaft",
                ),
            )
            nut_motions = {
                "nut_turn_30deg": movement["stroke_sweep"],
                "nut_open_end_exit": movement["lateral_unseat_sweep"],
                "nut_reindex_60deg": movement["detached_reindex_sweep"],
                "nut_reseat": movement["lateral_reseat_sweep"],
            }
            nut_access = tool_access.collision_report(
                nut_motions,
                environment,
                excluded_target_ids=(
                    f"hardware/{stack_id}/nut",
                    f"hardware/{stack_id}/shaft",
                ),
            )
            paired = tool_access.collision_report(
                nut_motions,
                {"head_counterhold": head_wrench},
                exclusion_scope="No fastener or opposing wrench is excluded.",
            )
            cases.append(
                {
                    "synthetic_heading_degrees": heading,
                    "heading_is_exact_catalog_jaw_pose": False,
                    "head_counterhold": stationary,
                    "nut_turn_reindex_reseat": nut_access,
                    "nut_wrench_vs_counterhold": paired,
                    "motion_degrees": {
                        "working_stroke": movement["stroke_degrees"],
                        "one_flat_reindex": abs(movement["reindex_degrees"]),
                        "rotation_bounds_are_full_turn": False,
                        "open_end_exit_mm": movement["open_end_exit_distance_mm"],
                    },
                }
            )
        results[stack_id] = {
            "axis_point_global_xyz_mm": [round(value, 6) for value in center.toTuple()],
            "axis_direction_global_xyz": [round(value, 9) for value in direction.toTuple()],
            "head_wrench_count": 1,
            "nut_wrench_count": 1,
            "two_wrenches_required_for_counterhold": True,
            "heading_cases": cases,
            "full_repeatable_nut_removal_proven": False,
            "real_tool_fit_or_torque_proven": False,
        }
    return {
        "environment_state": "panel_off_right_upper_and_lower",
        "candidate_id": tool.candidate_id,
        "external_proxy_dimensions_mm": {
            "head_diameter_and_handle_width": tool.head_width_mm,
            "head_thickness": tool.head_thickness_mm,
            "overall_length": tool.overall_length_mm,
        },
        "working_stroke_degrees": WORKING_STROKE_DEGREES,
        "one_flat_reindex_degrees": 2.0 * WORKING_STROKE_DEGREES,
        "proxy_shape": (
            "Two circular 22 mm heads and a full-width 22 mm rectangular handle, "
            "3 mm thick and 100 mm overall; catalog external-envelope proxy, not "
            "exact FACOM wrench CAD or jaw-fit evidence."
        ),
        "stacks": results,
        "full_repeatable_nut_removal_proven": False,
    }


def report(base_geometry: Any | None = None) -> dict[str, Any]:
    """Materialize and run only the named staging and local tool screens."""
    before = _source_snapshot()
    plan = trial_plan()
    geometry = g7_probe.materialize_geometry(base_geometry)
    panel_off_panels, panel_off_protected = _panel_off_maps(geometry, plan)
    rail_moves = _rail_move_screens(
        geometry, plan, panel_off_panels, panel_off_protected
    )
    principal_tools = _principal_tool_screens(
        geometry, panel_off_panels, panel_off_protected
    )
    outer_ids = _outer_obstacle_ids(geometry)
    restored_outer = outer_ids.issubset(set(geometry.protected))
    after = _source_snapshot()
    if before != after:
        raise RuntimeError("WJ-04 pair-access inputs changed during materialization")
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
            "preserved_panel_kicker_axis_count": len(
                _inventory()["fixed_panel_kicker_screws"]
            ),
            "preserved_frame_bolt_count": len(_inventory()["starting_frame_bolts"]),
        },
        "operations": {
            **plan["operations"],
            "panel_off_state": {
                **plan["operations"]["panel_off_state"],
                "panel_shapes_excluded_in_this_state_only": list(RIGHT_PANELS),
                "removed_panel_owned_protected_count": 144,
                "lights_and_wires_remain_in_panel_off_environment": True,
            },
            "rail_cleat_placement_removal": {
                **plan["operations"]["rail_cleat_placement_removal"],
                "directions_by_station": rail_moves,
                "screen_status": "geometry_materialized; physical path unverified",
            },
            "principal_x_bolt_tool_screen": principal_tools,
            "final_fit_state": {
                **plan["operations"]["final_fit_state"],
                "right_panels_and_tnuts_restored_for_fit_map": True,
                "all_source_panel_and_protected_obstacles_included": True,
                "outer_duty_geometry_restored": restored_outer,
                "screen_status": "final pose map only; not a fit or acceptance result",
            },
        },
        "outer_duty_geometry": {
            "unresolved_obstacle_ids_retained": sorted(outer_ids),
            "all_required_ids_restored_in_source_map": restored_outer,
            "accepted_replacement_count": 0,
        },
        "claim_boundary": {
            **plan["claim_boundary"],
            "physical_assembly_procedure_accepted": False,
            "temporary_stability_established": False,
            "full_load_path_established": False,
            "hardware_fit_established": False,
        },
        "limitations": [
            "Panel removal itself is a declared state; screw extraction and safe panel handling are not modeled.",
            "The rail movement screen is one-axis only and its swept AABB can flag conservative false collisions; no route around the frame is searched.",
            "The two far-end legacy connector/SDS duties remain unresolved obstacles; no temporary release, replacement, or side-member removal is assumed.",
            "The FACOM external envelope is a catalog proxy; exact jaw orientation, fit, torque, delivered tool tolerances, and human access are unverified.",
            "The 30-degree stroke and 60-degree one-flat reindex are one bounded diagnostic, not proof of repeatable nut removal.",
            "Temporary support, stability, load transfer, bolt-thread engagement, and structural acceptance are not established.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--materialize",
        action="store_true",
        help="run bounded access geometry after review and a separately granted slot",
    )
    args = parser.parse_args()
    result = report() if args.materialize else trial_plan()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
