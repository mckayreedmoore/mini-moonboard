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
LOCAL_UNSEATING_OVERTRAVEL_MM = 25.0
LOCAL_SAMPLE_MAX_GAP_MM = 5.0
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
                "global_projection_comparison": {
                    "clearance_mm": EXIT_CLEARANCE_MM,
                    "scope": "global fixed-obstacle projection; not a local extraction distance",
                },
                "stand_off_strategy": (
                    "Legacy comparison only: extend each one-axis swept AABB until "
                    "the moving pair clears the global fixed-obstacle N projection "
                    f"by {EXIT_CLEARANCE_MM:g} mm. These long distances are not a "
                    "local unseating stroke or a route around the frame."
                ),
                "local_plus_n_sampled_solid_screen": {
                    "direction": "+N",
                    "stroke_definition": (
                        "Conservative AABB-corner N projection extent of the source "
                        "rail plus cleat, then 25 mm overtravel. Attached rail T-bolts "
                        "move with them."
                    ),
                    "maximum_sample_gap_mm": LOCAL_SAMPLE_MAX_GAP_MM,
                    "floor_plane_z_mm": 0.0,
                    "placement_state": (
                        "The moving station's principal X-bolts are not yet installed; "
                        "opposite-station principal hardware stays in place."
                    ),
                    "continuous_path_clearance_proven": False,
                    "screen_status": "pending_materialization",
                },
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


def _bounds_overlap(first: cq.BoundBox, second: cq.BoundBox) -> bool:
    return not (
        first.xmax <= second.xmin
        or second.xmax <= first.xmin
        or first.ymax <= second.ymin
        or second.ymax <= first.ymin
        or first.zmax <= second.zmin
        or second.zmax <= first.zmin
    )


def _path_aabb(
    shape: cq.Shape, displacement: cq.Vector
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    bounds = shape.BoundingBox()
    delta = displacement.toTuple()
    lows = (bounds.xmin, bounds.ymin, bounds.zmin)
    highs = (bounds.xmax, bounds.ymax, bounds.zmax)
    path_lows = tuple(min(low, low + move) for low, move in zip(lows, delta, strict=True))
    path_highs = tuple(
        max(high, high + move) for high, move in zip(highs, delta, strict=True)
    )
    return path_lows, path_highs


def _path_aabb_overlaps_obstacle(
    path_bounds: tuple[tuple[float, float, float], tuple[float, float, float]],
    obstacle_bounds: cq.BoundBox,
) -> bool:
    lows, highs = path_bounds
    obstacle_lows = (
        obstacle_bounds.xmin,
        obstacle_bounds.ymin,
        obstacle_bounds.zmin,
    )
    obstacle_highs = (
        obstacle_bounds.xmax,
        obstacle_bounds.ymax,
        obstacle_bounds.zmax,
    )
    return all(
        high > obstacle_low and obstacle_high > low
        for low, high, obstacle_low, obstacle_high in zip(
            lows, highs, obstacle_lows, obstacle_highs, strict=True
        )
    )


def _solid_entries(name: str, shape: cq.Shape) -> dict[str, cq.Shape]:
    solids = shape.Solids()
    if not solids:
        raise ValueError(f"moving component {name} contains no solids")
    if len(solids) == 1:
        return {name: solids[0]}
    return {f"{name}/solid_{index}": solid for index, solid in enumerate(solids)}


def _sampled_solid_translation_screen(
    moving_solids: Mapping[str, cq.Shape],
    obstacles: Mapping[str, cq.Shape],
    direction: cq.Vector,
    stroke_mm: float,
    *,
    max_sample_gap_mm: float = LOCAL_SAMPLE_MAX_GAP_MM,
    floor_z_mm: float = 0.0,
) -> dict[str, Any]:
    """Sample exact BRep intersections along one straight translation.

    Swept AABBs limit the obstacle pairs considered. They remain a separate
    broadphase result; only translated source solids intersected at sampled
    offsets count as exact sample hits.
    """
    if not moving_solids:
        raise ValueError("sampled translation requires at least one moving solid")
    if not obstacles:
        raise ValueError("sampled translation requires fixed obstacle geometry")
    direction_values = direction.toTuple()
    if (
        not all(math.isfinite(value) for value in direction_values)
        or direction.Length <= 1e-12
    ):
        raise ValueError("sampled translation direction must be finite and nonzero")
    axis = direction.normalized()
    stroke = float(stroke_mm)
    step_limit = float(max_sample_gap_mm)
    floor = float(floor_z_mm)
    if not math.isfinite(stroke) or stroke < 0.0:
        raise ValueError("sampled translation stroke must be finite and nonnegative")
    if not math.isfinite(step_limit) or step_limit <= 0.0:
        raise ValueError("maximum sample gap must be finite and positive")
    if not math.isfinite(floor):
        raise ValueError("floor plane must be finite")

    interval_count = max(1, math.ceil(stroke / step_limit))
    offsets = [stroke * index / interval_count for index in range(interval_count + 1)]
    delta = axis * stroke
    obstacle_bounds = {name: shape.BoundingBox() for name, shape in obstacles.items()}
    path_bounds = {
        moving_id: _path_aabb(moving, delta)
        for moving_id, moving in moving_solids.items()
    }
    broadphase_pairs = {
        (moving_id, obstacle_id)
        for moving_id in moving_solids
        for obstacle_id in obstacles
        if _path_aabb_overlaps_obstacle(
            path_bounds[moving_id], obstacle_bounds[obstacle_id]
        )
    }
    broadphase_by_moving: dict[str, list[str]] = {
        moving_id: sorted(
            obstacle_id for candidate_id, obstacle_id in broadphase_pairs
            if candidate_id == moving_id
        )
        for moving_id in moving_solids
    }

    pair_stats: dict[tuple[str, str], dict[str, Any]] = {}
    per_pose = []
    minimum_z_by_solid = {moving_id: math.inf for moving_id in moving_solids}
    for sample_index, offset in enumerate(offsets):
        translation = axis * offset
        exact_hits = []
        floor_clearance = {}
        floor_penetration_ids = []
        candidate_pair_count = 0
        for moving_id, moving in moving_solids.items():
            moved = moving.translate(translation)
            moved_bounds = moved.BoundingBox()
            z_min = moved_bounds.zmin
            clearance = z_min - floor
            minimum_z_by_solid[moving_id] = min(minimum_z_by_solid[moving_id], z_min)
            floor_clearance[moving_id] = round(clearance, 6)
            if clearance < -HIT_TOLERANCE_MM3:
                floor_penetration_ids.append(moving_id)
            for obstacle_id in broadphase_by_moving[moving_id]:
                if not _bounds_overlap(moved_bounds, obstacle_bounds[obstacle_id]):
                    continue
                candidate_pair_count += 1
                overlap = moved.intersect(obstacles[obstacle_id]).Volume()
                if overlap <= HIT_TOLERANCE_MM3:
                    continue
                rounded = round(overlap, 6)
                exact_hits.append(
                    {
                        "moving_solid_id": moving_id,
                        "obstacle_id": obstacle_id,
                        "overlap_volume_mm3": rounded,
                    }
                )
                pair = (moving_id, obstacle_id)
                stats = pair_stats.setdefault(
                    pair,
                    {
                        "first_sample_index": sample_index,
                        "first_translation_mm": round(offset, 6),
                        "last_sample_index": sample_index,
                        "last_translation_mm": round(offset, 6),
                        "sampled_hit_count": 0,
                        "max_overlap_volume_mm3": rounded,
                        "max_overlap_sample_index": sample_index,
                    },
                )
                stats["last_sample_index"] = sample_index
                stats["last_translation_mm"] = round(offset, 6)
                stats["sampled_hit_count"] += 1
                if rounded > stats["max_overlap_volume_mm3"]:
                    stats["max_overlap_volume_mm3"] = rounded
                    stats["max_overlap_sample_index"] = sample_index
        per_pose.append(
            {
                "sample_index": sample_index,
                "translation_mm": round(offset, 6),
                "floor_clearance_by_moving_solid_mm": floor_clearance,
                "floor_penetrating_solid_ids": sorted(floor_penetration_ids),
                "broadphase_candidate_pair_count": candidate_pair_count,
                "exact_sample_hits": exact_hits,
            }
        )

    summaries = {}
    exact_pairs_by_moving: dict[str, set[str]] = {name: set() for name in moving_solids}
    for (moving_id, obstacle_id), stats in pair_stats.items():
        exact_pairs_by_moving[moving_id].add(obstacle_id)
    for moving_id in moving_solids:
        pair_rows = [
            {"obstacle_id": obstacle_id, **stats}
            for (candidate_id, obstacle_id), stats in sorted(pair_stats.items())
            if candidate_id == moving_id
        ]
        hit_sample_indices = [
            row["sample_index"]
            for row in per_pose
            if any(hit["moving_solid_id"] == moving_id for hit in row["exact_sample_hits"])
        ]
        all_samples = [
            hit
            for row in per_pose
            for hit in row["exact_sample_hits"]
            if hit["moving_solid_id"] == moving_id
        ]
        max_hit = max(
            all_samples,
            key=lambda row: row["overlap_volume_mm3"],
            default=None,
        )
        sampled_exact_ids = exact_pairs_by_moving[moving_id]
        candidates = set(broadphase_by_moving[moving_id])
        summaries[moving_id] = {
            "first_sample_with_any_exact_hit": min(hit_sample_indices, default=None),
            "last_sample_with_any_exact_hit": max(hit_sample_indices, default=None),
            "maximum_exact_sample_overlap_mm3": (
                max_hit["overlap_volume_mm3"] if max_hit else 0.0
            ),
            "maximum_overlap_obstacle_id": max_hit["obstacle_id"] if max_hit else None,
            "minimum_z_over_sampled_path_mm": round(minimum_z_by_solid[moving_id], 6),
            "broadphase_candidate_obstacle_ids": sorted(candidates),
            "exact_sample_hit_obstacle_ids": sorted(sampled_exact_ids),
            "broadphase_candidates_without_exact_sample_hit": sorted(
                candidates - sampled_exact_ids
            ),
            "exact_sample_hits_by_obstacle": pair_rows,
        }

    any_hits = any(row["exact_sample_hits"] for row in per_pose)
    any_floor_penetration = any(row["floor_penetrating_solid_ids"] for row in per_pose)
    return {
        "direction_global_xyz": [round(value, 9) for value in axis.toTuple()],
        "stroke_mm": round(stroke, 6),
        "maximum_sample_gap_mm": round(max(offsets[i + 1] - offsets[i] for i in range(len(offsets) - 1)), 6),
        "sampled_pose_count": len(offsets),
        "floor_plane_z_mm": floor,
        "swept_aabb_broadphase": {
            "candidate_pair_count": len(broadphase_pairs),
            "candidate_pairs": [
                {"moving_solid_id": moving_id, "obstacle_id": obstacle_id}
                for moving_id, obstacle_id in sorted(broadphase_pairs)
            ],
        },
        "sampled_actual_solid_translation": {
            "all_sampled_poses_clear": not any_hits and not any_floor_penetration,
            "continuous_path_clearance_proven": False,
            "per_moving_solid": summaries,
            "poses": per_pose,
        },
    }


def _local_plus_n_screens(
    geometry: Any,
    panel_off_panels: Mapping[str, cq.Shape],
    panel_off_protected: Mapping[str, cq.Shape],
) -> dict[str, Any]:
    n_axis = cq.Vector(*WJ04_TRIAL.frame.n_global).normalized()
    environment = _final_environment(geometry, panel_off_panels, panel_off_protected)
    outer_required = _outer_obstacle_ids(geometry)
    results = {}
    for station_id, rail_id, cleat_id, prefix, other_prefix in (
        (LOWER_STATION, LOWER_RAIL, LOWER_CLEAT, "lower", "upper"),
        (UPPER_STATION, UPPER_RAIL, UPPER_CLEAT, "upper", "lower"),
    ):
        stack_ids = (f"{prefix}_rail_1", f"{prefix}_rail_2")
        principal_stack_ids = (f"{prefix}_principal_1", f"{prefix}_principal_2")
        opposite_principal_stack_ids = (
            f"{other_prefix}_principal_1",
            f"{other_prefix}_principal_2",
        )
        source_moving_shapes: dict[str, cq.Shape] = {
            f"wood/{rail_id}": geometry.finished[rail_id],
            f"wood/{cleat_id}": geometry.finished[cleat_id],
        }
        for stack_id in stack_ids:
            for role, shape in geometry.installed[stack_id].items():
                source_moving_shapes[f"hardware/{stack_id}/{role}"] = shape
        moving_environment_ids = set(source_moving_shapes)
        moving_solids = {
            solid_id: solid
            for source_id, shape in source_moving_shapes.items()
            for solid_id, solid in _solid_entries(source_id, shape).items()
        }
        principal_environment_ids = {
            f"hardware/{stack_id}/{role}"
            for stack_id in principal_stack_ids
            for role in geometry.installed[stack_id]
        }
        opposite_principal_environment_ids = {
            f"hardware/{stack_id}/{role}"
            for stack_id in opposite_principal_stack_ids
            for role in geometry.installed[stack_id]
        }
        missing_opposite = opposite_principal_environment_ids - set(environment)
        if missing_opposite:
            raise ValueError(
                "local placement screen must retain opposite-station principal hardware: "
                f"{sorted(missing_opposite)}"
            )
        obstacles = {
            name: shape
            for name, shape in environment.items()
            if name not in moving_environment_ids | principal_environment_ids
        }
        missing_outer = {f"protected/{name}" for name in outer_required} - set(obstacles)
        if missing_outer:
            raise ValueError(
                f"local placement screen omitted unresolved outer obstacles: {sorted(missing_outer)}"
            )
        if "wood/base_side_right" not in obstacles:
            raise ValueError("local placement screen must retain base_side_right")

        wood_members = {
            f"wood/{rail_id}": geometry.finished[rail_id],
            f"wood/{cleat_id}": geometry.finished[cleat_id],
        }
        moving_low, moving_high = _map_projection_bounds(wood_members, n_axis)
        pair_extent = moving_high - moving_low
        stroke = pair_extent + LOCAL_UNSEATING_OVERTRAVEL_MM
        sampled = _sampled_solid_translation_screen(
            moving_solids,
            obstacles,
            n_axis,
            stroke,
            max_sample_gap_mm=LOCAL_SAMPLE_MAX_GAP_MM,
            floor_z_mm=0.0,
        )
        results[station_id] = {
            "moving_wood_member_ids": [rail_id, cleat_id],
            "attached_rail_t_bolt_stack_ids": list(stack_ids),
            "placement_state": "target station principal X-bolts are not yet installed",
            "not_installed_target_principal_stack_ids": list(principal_stack_ids),
            "opposite_station_principal_stack_ids_retained": list(
                opposite_principal_stack_ids
            ),
            "fixed_obstacle_count": len(obstacles),
            "retained_outer_duty_obstacle_ids": sorted(
                f"protected/{name}" for name in outer_required
            ),
            "base_side_right_retained": True,
            "side_member_release_modeled": False,
            "rail_plus_cleat_n_projection_extent_mm_conservative": round(
                pair_extent, 6
            ),
            "local_unseating_overtravel_mm": LOCAL_UNSEATING_OVERTRAVEL_MM,
            "floor_plane_z_mm": 0.0,
            "aabb_and_exact_results_are_separate": True,
            "physical_move_proven": False,
            **sampled,
        }
    return results


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
    local_plus_n_moves = _local_plus_n_screens(
        geometry, panel_off_panels, panel_off_protected
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
                "global_projection_aabb_diagnostics_by_station": rail_moves,
                "local_plus_n_sampled_solid_screens_by_station": local_plus_n_moves,
                "local_plus_n_sampled_solid_screen": {
                    **plan["operations"]["rail_cleat_placement_removal"][
                        "local_plus_n_sampled_solid_screen"
                    ],
                    "by_station": local_plus_n_moves,
                    "screen_status": (
                        "materialized; coarse sampled intersections and broadphase "
                        "only; continuous movement unverified"
                    ),
                },
                "screen_status": (
                    "global swept-AABB comparison and local sampled-solid diagnostic; "
                    "physical path unverified"
                ),
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
            "The legacy +/-N swept-AABB screen uses global fixed-obstacle projection clearance, not local unseating distance; it can overstate collisions and is not a route metric.",
            "The separate +N local screen checks source solids only at offsets no more than 5 mm apart; broadphase AABB candidates can be false positives, and inter-sample collisions can be missed. It proves neither continuous clearance nor a movement route.",
            "The local placement state omits only the target station's not-yet-installed principal X-bolts; opposite-station hardware, fixed services, unresolved far-end connector/SDS obstacles, and base_side_right remain.",
            "The z=0 floor plane is checked from each translated solid's bounding-box minimum at every sampled pose; temporary support, stability, and human handling are not modeled.",
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
