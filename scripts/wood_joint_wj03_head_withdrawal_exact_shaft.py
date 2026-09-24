"""Exact coaxial supplement for archived WJ-03 shaft-withdrawal envelopes."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import cadquery as cq

from scripts import wood_joint_wj03_compact_outer_access as compact_access
from scripts import wood_joint_wj03_compact_outer_tools as compact_tools
from scripts import wood_joint_wj03_head_withdrawal as withdrawal
from scripts import wood_joint_wj04_tool_access as tool_access

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_REPORT = ROOT / "docs/wood-joints-mvp/hypotheses/wj03-head-withdrawal.json"
DEFAULT_BASE_NOTE = DEFAULT_BASE_REPORT.with_suffix(".md")
ARCHIVED_BASE_REPORT_SHA256 = (
    "03cb0201b41b1a7dbded07bb5917301c078f698c950032c3524715583252b9f5"
)
SCHEMA = "wood_joint_wj03_head_withdrawal_exact_shaft/v1"
SOURCE_AXIS_TOLERANCE_MM = 1e-6
SOURCE_VOLUME_RELATIVE_TOLERANCE = 1e-8

SOURCE_PIN_PATHS = (
    "docs/wood-joints-mvp/hypotheses/wj03-head-withdrawal.json",
    "docs/wood-joints-mvp/hypotheses/wj03-head-withdrawal.md",
    "mini_moonboard/wood_joint_frame.py",
    "mini_moonboard/wood_joint_geometry.py",
    "mini_moonboard/wood_joint_wj05_socket.py",
    "scripts/wood_joint_wj03_compact_outer_access.py",
    "scripts/wood_joint_wj03_compact_outer_tools.py",
    "scripts/wood_joint_wj03_head_withdrawal.py",
    "scripts/wood_joint_wj03_head_withdrawal_exact_shaft.py",
    "scripts/wood_joint_wj04_tool_access.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_pins() -> dict[str, str]:
    return {name: _sha256(ROOT / name) for name in SOURCE_PIN_PATHS}


def _validate_archived_base(base_path: Path, base_data: Mapping[str, Any]) -> None:
    direct_inputs = base_data.get("source_pins", {}).get(
        "head_withdrawal_direct_inputs"
    )
    if not isinstance(direct_inputs, Mapping) or not direct_inputs:
        raise ValueError("base report has no head-withdrawal direct source pins")
    for relative_path, expected_sha in direct_inputs.items():
        path = ROOT / relative_path
        if not path.is_file() or _sha256(path) != expected_sha:
            raise ValueError(f"archived head-withdrawal input changed: {relative_path}")

    if base_path.resolve() == DEFAULT_BASE_REPORT.resolve():
        if _sha256(base_path) != ARCHIVED_BASE_REPORT_SHA256:
            raise ValueError("immutable archived base JSON hash changed")
        note = DEFAULT_BASE_NOTE.read_text()
        match = re.search(r"Archived JSON SHA256: `([0-9a-f]{64})`", note)
        if match is None or match.group(1) != ARCHIVED_BASE_REPORT_SHA256:
            raise ValueError(
                "archived base JSON hash does not match its companion note"
            )


def validate_base_report(
    base_report_path: Path = DEFAULT_BASE_REPORT,
) -> dict[str, str]:
    """Validate the archive and its source pins before geometry materialization."""
    base_path = Path(base_report_path)
    base_data = json.loads(base_path.read_text())
    if base_data.get("schema") != withdrawal.SCHEMA:
        raise ValueError("base report does not match frozen withdrawal schema")
    _validate_archived_base(base_path, base_data)
    return {
        "path": str(base_path),
        "sha256": _sha256(base_path),
        "schema": base_data["schema"],
    }


def _shaft_sweep(
    stack: Any, installed_shaft: cq.Shape
) -> tuple[cq.Shape, dict[str, Any]]:
    """Return exact cylinder swept by installed shaft along its own axis."""
    if not isinstance(installed_shaft, cq.Shape) or not installed_shaft.isValid():
        raise ValueError(f"installed shaft for {stack.id} must be valid solid geometry")
    if len(installed_shaft.Solids()) != 1:
        raise ValueError(f"installed shaft for {stack.id} must be one solid")

    axis = cq.Vector(stack.direction).normalized()
    origin = cq.Vector(stack.under_head_origin)
    hardware = stack.hardware
    length = float(hardware.under_head_length_mm)
    travel = length
    diameter = float(hardware.cad_occupied_diameter_mm)
    radius = diameter / 2
    if not all(math.isfinite(value) and value > 0 for value in (length, diameter)):
        raise ValueError(f"shaft dimensions for {stack.id} must be positive and finite")

    expected_center = origin + axis * (length / 2)
    actual_center = installed_shaft.Center()
    if (actual_center - expected_center).Length > SOURCE_AXIS_TOLERANCE_MM:
        raise ValueError(
            f"installed shaft center does not match stack datum: {stack.id}"
        )
    shaft_start = actual_center - axis * (length / 2)
    expected_volume = math.pi * radius**2 * length
    volume_tolerance = max(1e-7, expected_volume * SOURCE_VOLUME_RELATIVE_TOLERANCE)
    if abs(installed_shaft.Volume() - expected_volume) > volume_tolerance:
        raise ValueError(
            f"installed shaft volume does not match nominal cylinder: {stack.id}"
        )

    start = shaft_start - axis * travel
    sweep = cq.Solid.makeCylinder(radius, length + travel, start, axis)
    if not sweep.isValid() or len(sweep.Solids()) != 1:
        raise ValueError(f"exact shaft sweep invalid: {stack.id}")
    record = {
        "sweep_kind": "analytic cylinder union for translation along source cylinder axis",
        "installed_shaft_shape_center_xyz_mm": [
            round(value, 9) for value in actual_center.toTuple()
        ],
        "installed_shaft_source_volume_mm3": round(installed_shaft.Volume(), 9),
        "stack_under_head_origin_xyz_mm": [
            round(value, 9) for value in origin.toTuple()
        ],
        "shaft_start_xyz_mm_from_installed_shape": [
            round(value, 9) for value in shaft_start.toTuple()
        ],
        "sweep_start_xyz_mm": [round(value, 9) for value in start.toTuple()],
        "axis_xyz": [round(value, 9) for value in axis.toTuple()],
        "radius_mm": radius,
        "diameter_mm": diameter,
        "diameter_basis": "BoltHardware.cad_occupied_diameter_mm from materialized candidate stack",
        "ordinary_quarter_inch_shank_6_604mm_sensitivity_included": False,
        "source_length_mm": length,
        "withdrawal_travel_mm": travel,
        "sweep_length_mm": length + travel,
        "axis_xyz_source": "BoltStack.direction used by installed shaft constructor",
        "source_center_and_volume_verified_against_installed_shape": True,
    }
    return sweep, record


def _base_shaft_hit_ids(base_row: Mapping[str, Any]) -> list[str]:
    path = base_row["bolt_withdrawal_after_unthreading"]["shaft_path"]
    hits = path["external_envelope_hits_mm3"].get("shaft_axial_withdrawal", {})
    return sorted(hits)


def _heading_ratchet_shapes(
    ratchet_cases: Mapping[str, cq.Shape], heading: float
) -> dict[str, cq.Shape]:
    prefix = f"heading_{heading:+g}deg/"
    return {
        f"tool_pair/stationary_nut_ratchet/{name}": shape
        for name, shape in ratchet_cases.items()
        if name.startswith(prefix)
    }


def build_exact_shaft_supplement(
    geometry: Any,
    *,
    base_report_path: Path = DEFAULT_BASE_REPORT,
) -> dict[str, Any]:
    """Screen only exact WJ-03 shaft translations against original retained map."""
    if getattr(geometry, "trial_id", None) != compact_access.TRIAL_ID:
        raise ValueError("geometry must use the frozen compact WJ-03 trial")
    stacks = getattr(geometry, "stacks", None)
    if not isinstance(stacks, Mapping) or len(stacks) != compact_tools.STACK_COUNT:
        raise ValueError(
            f"geometry must provide exactly {compact_tools.STACK_COUNT} candidate stacks"
        )
    if any(stack_id != stack.id for stack_id, stack in stacks.items()):
        raise ValueError("stack mapping keys must match each BoltStack.id")

    base_path = Path(base_report_path)
    base_data = json.loads(base_path.read_text())
    validated_base = validate_base_report(base_path)
    if base_data.get("trial_id") != geometry.trial_id:
        raise ValueError("base report and geometry trial IDs differ")
    if set(base_data.get("stacks", {})) != set(stacks):
        raise ValueError("base report stack IDs differ from materialized geometry")

    safe_binding = compact_tools._json_safe(geometry.source_binding)
    safe_geometry_pins = compact_tools._json_safe(geometry.source_pins)
    if base_data.get("source_binding") != safe_binding:
        raise ValueError("base report source binding differs from geometry")
    base_geometry_pins = base_data.get("source_pins", {}).get(
        "geometry_materializer_inputs"
    )
    if base_geometry_pins != safe_geometry_pins:
        raise ValueError("base report geometry source pins differ from materialization")
    obstacles, _classes, _panel_ids = compact_tools._geometry_maps(geometry)
    installed = compact_tools._flatten_shapes(
        geometry.installed_hardware, "installed_hardware"
    )
    floor_z = float(geometry.floor_z_mm)
    if not math.isfinite(floor_z):
        raise ValueError("geometry.floor_z_mm must be finite")

    stack_rows: dict[str, Any] = {}
    for stack_id, stack in sorted(stacks.items()):
        target_keys = withdrawal._target_component_keys(installed, stack_id)
        target_shapes = {role: installed[key] for role, key in target_keys.items()}
        sweep, sweep_record = _shaft_sweep(stack, target_shapes["shaft"])

        direction = cq.Vector(stack.direction).normalized()
        nut_outward = direction
        nut_socket, nut_drive_center, _datum = withdrawal._socket_pose(
            cq.Vector(stack.nut_seat.center), target_shapes["nut"], nut_outward
        )
        nut_reference = compact_tools._face_reference(nut_outward)
        nut_ratchet_cases, _ratchet_record = withdrawal._stationary_ratchet_case_shapes(
            nut_drive_center, nut_outward, nut_reference
        )
        shaft_obstacles = withdrawal._withdrawal_obstacles(obstacles, target_keys)
        socket_obstacle_id = "tool_pair/stationary_nut_socket"
        shaft_obstacles[socket_obstacle_id] = nut_socket
        exclusion_scope = (
            "Same retained-obstacle state and exclusions as archived WJ-03 report: "
            "target shaft/head/nut removed as the translating through-bolt stack; "
            "stationary nut socket external envelope excluded for intended shaft "
            "passage through its unmodeled inner bore. Both washers, wood, services "
            "and unrelated stacks remain obstacles here. The stationary nut "
            "ratchet is screened separately for each sampled heading below."
        )
        exact_screen = tool_access.collision_report(
            {"exact_coaxial_shaft_withdrawal": sweep},
            shaft_obstacles,
            excluded_target_ids=(socket_obstacle_id,),
            exclusion_scope=exclusion_scope,
        )
        exact_screen["floor_screen"] = compact_tools._floor_bounds(sweep, floor_z)
        fixed_hit_ids = sorted(
            exact_screen["external_envelope_hits_mm3"].get(
                "exact_coaxial_shaft_withdrawal", {}
            )
        )
        heading_screens: dict[str, Any] = {}
        for heading in withdrawal.COUNTERHOLD_HEADINGS_DEGREES:
            heading_key = f"{heading:+g}deg"
            heading_obstacles = _heading_ratchet_shapes(nut_ratchet_cases, heading)
            heading_collision = tool_access.collision_report(
                {"exact_coaxial_shaft_withdrawal": sweep},
                heading_obstacles,
                exclusion_scope=(
                    "This report screens one sampled stationary-nut ratchet heading "
                    "only. Other mutually exclusive headings are omitted, not "
                    "unioned as simultaneous obstacles. The heading remains an "
                    "envelope proxy, not a demonstrated operating pose."
                ),
            )
            heading_collision["floor_screen"] = compact_tools._floor_bounds(
                sweep, floor_z
            )
            ratchet_hit_ids = sorted(
                heading_collision["external_envelope_hits_mm3"].get(
                    "exact_coaxial_shaft_withdrawal", {}
                )
            )
            combined_hit_ids = sorted(set(fixed_hit_ids) | set(ratchet_hit_ids))
            heading_screens[heading_key] = {
                "analytic_sweep_collision": heading_collision,
                "ratchet_heading_hit_obstacle_ids": ratchet_hit_ids,
                "exact_sweep_hit_obstacle_ids": combined_hit_ids,
                "sampled_pose_clear_with_this_heading": not combined_hit_ids,
            }
        old_hit_ids = _base_shaft_hit_ids(base_data["stacks"][stack_id])
        archived_heading_union_hit_ids = sorted(
            name
            for name in old_hit_ids
            if name.startswith("tool_pair/stationary_nut_ratchet/")
        )
        old_non_heading_ids = sorted(
            set(old_hit_ids) - set(archived_heading_union_hit_ids)
        )
        sampled_heading_clear = any(
            row["sampled_pose_clear_with_this_heading"]
            for row in heading_screens.values()
        )
        stack_rows[stack_id] = {
            "shaft_sweep_geometry": sweep_record,
            "analytic_sweep_collision": exact_screen,
            "archived_aabb_hit_obstacle_ids": old_hit_ids,
            "archived_counterhold_heading_union_hit_ids": archived_heading_union_hit_ids,
            "exact_fixed_obstacle_hit_ids": fixed_hit_ids,
            "aabb_only_nonheading_obstacle_ids": sorted(
                set(old_non_heading_ids) - set(fixed_hit_ids)
            ),
            "exact_only_nonheading_obstacle_ids": sorted(
                set(fixed_hit_ids) - set(old_non_heading_ids)
            ),
            "stationary_nut_ratchet_heading_screens": heading_screens,
            "any_sampled_heading_clear": sampled_heading_clear,
        }

    exact_fixed_hit_stacks = sum(
        bool(row["exact_fixed_obstacle_hit_ids"]) for row in stack_rows.values()
    )
    archived_hit_stacks = sum(
        bool(row["archived_aabb_hit_obstacle_ids"]) for row in stack_rows.values()
    )
    heading_clear_stack_count = sum(
        bool(row["any_sampled_heading_clear"]) for row in stack_rows.values()
    )
    heading_clear_cases = {
        f"{heading:+g}deg": sum(
            bool(
                row["stationary_nut_ratchet_heading_screens"][f"{heading:+g}deg"][
                    "sampled_pose_clear_with_this_heading"
                ]
            )
            for row in stack_rows.values()
        )
        for heading in withdrawal.COUNTERHOLD_HEADINGS_DEGREES
    }
    return {
        "schema": SCHEMA,
        "trial_id": geometry.trial_id,
        "status": "diagnostic_supplement_only_not_acceptance",
        "base_report": {
            **validated_base,
            "preserved_without_overwrite": True,
            "is_immutable_archive": base_path.resolve()
            == DEFAULT_BASE_REPORT.resolve(),
        },
        "source_binding": safe_binding,
        "source_pins": {
            "geometry_materializer_inputs": safe_geometry_pins,
            "exact_shaft_direct_inputs": _source_pins(),
            "coverage": "direct file pins only; base report hash pins archived coarse diagnostic",
        },
        "candidate_stack_count": len(stack_rows),
        "screen_method": {
            "shape": "single exact circular cylinder swept continuously along source shaft axis",
            "cross_section": "installed shaft nominal circular section; no bounding-box corner expansion",
            "diameter_limit": "uses the candidate's nominal 6.35 mm CAD diameter; the separate 6.604 mm generic ordinary 1/4-in shank sensitivity is not included",
            "path": "under-head origin minus axis times withdrawal travel through original source shaft tip",
            "travel_rule": "one source under-head length, matching archived operation",
            "retained_map_and_exclusions": "same geometry obstacle map and sequential target exclusions as archived shaft_path screen",
            "counterhold_headings": "screened as separate alternatives; no union of mutually exclusive headings is interpreted as a physical blockage",
            "physical_access_established": False,
            "clear_result_is_fabrication_or_access_acceptance": False,
        },
        "summary": {
            "archived_aabb_hit_stacks": archived_hit_stacks,
            "exact_fixed_obstacle_hit_stacks": exact_fixed_hit_stacks,
            "exact_fixed_obstacle_clear_stacks": len(stack_rows)
            - exact_fixed_hit_stacks,
            "stacks_with_at_least_one_sampled_counterhold_heading_clear": heading_clear_stack_count,
            "sampled_counterhold_heading_clear_stack_counts": heading_clear_cases,
            "aabb_only_obstacle_pairs": sum(
                len(row["aabb_only_nonheading_obstacle_ids"])
                for row in stack_rows.values()
            ),
            "exact_only_obstacle_pairs": sum(
                len(row["exact_only_nonheading_obstacle_ids"])
                for row in stack_rows.values()
            ),
        },
        "stacks": stack_rows,
        "release_claims": {
            "shaft_withdrawal_access_established": False,
            "threading_or_internal_socket_fit_verified": False,
            "fabrication_released": False,
            "structural_released": False,
        },
    }
