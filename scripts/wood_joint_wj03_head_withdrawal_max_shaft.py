"""Source-bound WJ-03 ordinary-bolt maximum-shaft sensitivity."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import cadquery as cq

from scripts import wood_joint_wj03_compact_outer_tools as compact_tools
from scripts import wood_joint_wj03_head_withdrawal as withdrawal
from scripts import wood_joint_wj03_head_withdrawal_exact_shaft as exact_shaft
from scripts import wood_joint_wj04_tool_access as tool_access

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_wj03_head_withdrawal_max_shaft/v1"
NOMINAL_REPORT_PATH = (
    ROOT / "docs/wood-joints-mvp/hypotheses/wj03-head-withdrawal-exact-shaft.json"
)
NOMINAL_REPORT_SHA256 = (
    "58dc1e5c5d070835970c05875ea9f9cd5fac5e2fd30f6f4b3bb944713704f6a7"
)
SCHEDULE_AUDIT_PATH = (
    ROOT / "docs/wood-joints-mvp/hypotheses/current-hardware-schedule-audit.md"
)
SCHEDULE_AUDIT_SHA256 = (
    "cc6a74bcd3f3143bdeb26b89661f10f72e33fb041262fa09ee65f1cf684f26e6"
)
STACK_COUNT = 20
AXIS_TOLERANCE_MM = 1e-6
VOLUME_RELATIVE_TOLERANCE = 1e-8

SOURCE_PIN_PATHS = (
    "docs/wood-joints-mvp/hypotheses/current-hardware-schedule-audit.md",
    "docs/wood-joints-mvp/hypotheses/wj03-head-withdrawal.json",
    "docs/wood-joints-mvp/hypotheses/wj03-head-withdrawal.md",
    "docs/wood-joints-mvp/hypotheses/wj03-head-withdrawal-exact-shaft.json",
    "mini_moonboard/wood_joint_frame.py",
    "mini_moonboard/wood_joint_geometry.py",
    "mini_moonboard/wood_joint_wj05_socket.py",
    "scripts/wood_joint_wj03_compact_outer_access.py",
    "scripts/wood_joint_wj03_compact_outer_tools.py",
    "scripts/wood_joint_wj03_head_withdrawal.py",
    "scripts/wood_joint_wj03_head_withdrawal_exact_shaft.py",
    "scripts/wood_joint_wj03_head_withdrawal_max_shaft.py",
    "scripts/wood_joint_wj04_tool_access.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_pins() -> dict[str, str]:
    return {relative: _sha256(ROOT / relative) for relative in SOURCE_PIN_PATHS}


def _ordinary_body_maximum_from_audit() -> dict[str, Any]:
    if _sha256(SCHEDULE_AUDIT_PATH) != SCHEDULE_AUDIT_SHA256:
        raise ValueError("pinned current hardware schedule audit changed")
    text = SCHEDULE_AUDIT_PATH.read_text()
    matches = re.findall(
        r"permit\s+up\s+to\s+([0-9]+(?:\.[0-9]+)?)\s+in\s+"
        r"\(([0-9]+(?:\.[0-9]+)?)\s+mm\)\s+body\s+diameter",
        text,
        flags=re.IGNORECASE,
    )
    if len(matches) != 1:
        raise ValueError("hardware schedule audit must give one ordinary-body bound")
    maximum_in, stated_mm = (float(value) for value in matches[0])
    converted_mm = maximum_in * 25.4
    if not math.isclose(converted_mm, stated_mm, abs_tol=1e-9):
        raise ValueError("ordinary-body inch/mm values in audit do not agree")
    return {
        "source_path": str(SCHEDULE_AUDIT_PATH),
        "source_sha256": SCHEDULE_AUDIT_SHA256,
        "ordinary_bolt_body_maximum_in": maximum_in,
        "ordinary_bolt_body_maximum_mm": round(converted_mm, 6),
        "source_wording": "ordinary 1/4-in nominal bolt body maximum; no SKU dimensions inferred",
    }


def _validate_nominal_report() -> tuple[dict[str, Any], dict[str, Any]]:
    if _sha256(NOMINAL_REPORT_PATH) != NOMINAL_REPORT_SHA256:
        raise ValueError("immutable nominal exact-shaft report hash changed")
    report = json.loads(NOMINAL_REPORT_PATH.read_text())
    if report.get("schema") != exact_shaft.SCHEMA:
        raise ValueError("nominal report schema changed")
    if report.get("base_report", {}).get("sha256") != (
        exact_shaft.ARCHIVED_BASE_REPORT_SHA256
    ):
        raise ValueError("nominal report is not bound to the immutable coarse report")
    if report.get("candidate_stack_count") != STACK_COUNT:
        raise ValueError("nominal report does not contain twenty WJ-03 positions")
    direct_pins = report.get("source_pins", {}).get("exact_shaft_direct_inputs")
    if not isinstance(direct_pins, Mapping) or not direct_pins:
        raise ValueError("nominal report lacks direct source pins")
    for relative, expected_sha in direct_pins.items():
        source_path = ROOT / relative
        if not source_path.is_file() or _sha256(source_path) != expected_sha:
            raise ValueError(f"nominal report input changed: {relative}")
    audit = _ordinary_body_maximum_from_audit()
    return report, audit


def validate_source_reports() -> dict[str, Any]:
    """Fail-fast validation suitable before the costly geometry materialization."""
    report, audit = _validate_nominal_report()
    return {
        "nominal_report_path": str(NOMINAL_REPORT_PATH),
        "nominal_report_sha256": NOMINAL_REPORT_SHA256,
        "coarse_base_report_sha256": report["base_report"]["sha256"],
        "hardware_schedule_audit": audit,
    }


def _alternate_shaft_and_sweep(
    stack: Any,
    installed_nominal_shaft: cq.Shape,
    diameter_mm: float,
) -> tuple[cq.Shape, cq.Shape, dict[str, Any]]:
    """Build only the larger shaft solids, retaining the source axis and length."""
    _nominal_sweep, nominal_record = exact_shaft._shaft_sweep(
        stack, installed_nominal_shaft
    )
    steel_diameter = float(stack.hardware.steel_diameter_mm)
    nominal_diameter = float(stack.hardware.cad_occupied_diameter_mm)
    if not math.isclose(steel_diameter, nominal_diameter, abs_tol=1e-9):
        raise ValueError(f"nominal design/CAD shaft diameter diverged: {stack.id}")
    if not math.isclose(steel_diameter, nominal_record["diameter_mm"], abs_tol=1e-9):
        raise ValueError(f"nominal report/source shaft diameter mismatch: {stack.id}")

    diameter = float(diameter_mm)
    if not math.isfinite(diameter) or diameter <= nominal_diameter:
        raise ValueError("alternate shaft diameter must exceed nominal and be finite")
    axis = cq.Vector(nominal_record["axis_xyz"]).normalized()
    shaft_start = cq.Vector(nominal_record["shaft_start_xyz_mm_from_installed_shape"])
    length = float(nominal_record["source_length_mm"])
    travel = float(nominal_record["withdrawal_travel_mm"])
    maximum_shaft = cq.Solid.makeCylinder(diameter / 2, length, shaft_start, axis)
    maximum_sweep = cq.Solid.makeCylinder(
        diameter / 2, length + travel, shaft_start - axis * travel, axis
    )
    if (
        not maximum_shaft.isValid()
        or len(maximum_shaft.Solids()) != 1
        or not maximum_sweep.isValid()
        or len(maximum_sweep.Solids()) != 1
    ):
        raise ValueError(f"alternate shaft geometry invalid: {stack.id}")
    expected_volume = math.pi * (diameter / 2) ** 2 * length
    if abs(maximum_shaft.Volume() - expected_volume) > max(
        1e-7, expected_volume * VOLUME_RELATIVE_TOLERANCE
    ):
        raise ValueError(f"alternate shaft volume is inconsistent: {stack.id}")
    if (maximum_shaft.Center() - installed_nominal_shaft.Center()).Length > (
        AXIS_TOLERANCE_MM
    ):
        raise ValueError(f"alternate shaft center moved: {stack.id}")

    record = {
        "nominal_steel_design_diameter_mm": steel_diameter,
        "nominal_cad_occupied_diameter_mm": nominal_diameter,
        "ordinary_class_maximum_cad_occupied_diameter_mm": diameter,
        "diameter_delta_mm": round(diameter - nominal_diameter, 6),
        "alternate_installed_shaft_volume_mm3": round(maximum_shaft.Volume(), 9),
        "alternate_sweep_volume_mm3": round(maximum_sweep.Volume(), 9),
        "axis_xyz": nominal_record["axis_xyz"],
        "shaft_start_xyz_mm": nominal_record["shaft_start_xyz_mm_from_installed_shape"],
        "source_length_mm": length,
        "withdrawal_travel_mm": travel,
        "sweep_length_mm": length + travel,
        "same_axis_and_source_length_as_nominal": True,
        "head_seats_nuts_washers_and_bores_changed": False,
        "nominal_design_diameter_changed": False,
        "sku_dimensions_inferred": False,
    }
    return maximum_shaft, maximum_sweep, record


def _heading_key(heading: float) -> str:
    return f"{heading:+g}deg"


def _hit_ids(screen: Mapping[str, Any], candidate_key: str) -> list[str]:
    return sorted(screen.get("external_envelope_hits_mm3", {}).get(candidate_key, {}))


def _replace_all_modeled_shafts(
    obstacles: Mapping[str, cq.Shape], alternate_shafts: Mapping[str, cq.Shape]
) -> dict[str, cq.Shape]:
    """Return an obstacle copy with only the mapped WJ-03 shafts replaced."""
    missing = set(alternate_shafts) - set(obstacles)
    if missing:
        raise ValueError(
            "maximum shaft keys are missing from retained map: "
            + ", ".join(sorted(missing))
        )
    result = dict(obstacles)
    result.update(alternate_shafts)
    return result


def _validate_geometry_binding(
    geometry: Any, nominal_report: Mapping[str, Any]
) -> None:
    if getattr(geometry, "trial_id", None) != nominal_report.get("trial_id"):
        raise ValueError("materialized geometry and nominal report trial IDs differ")
    stacks = getattr(geometry, "stacks", None)
    if not isinstance(stacks, Mapping) or len(stacks) != STACK_COUNT:
        raise ValueError(f"geometry must contain exactly {STACK_COUNT} WJ-03 stacks")
    if set(stacks) != set(nominal_report.get("stacks", {})):
        raise ValueError("materialized stack IDs differ from nominal archived report")
    if compact_tools._json_safe(geometry.source_binding) != nominal_report.get(
        "source_binding"
    ):
        raise ValueError("materialized source binding differs from nominal report")
    if compact_tools._json_safe(geometry.source_pins) != nominal_report.get(
        "source_pins", {}
    ).get("geometry_materializer_inputs"):
        raise ValueError("materializer input pins differ from nominal report")


def build_ordinary_body_maximum_sensitivity(geometry: Any) -> dict[str, Any]:
    """Compare the pinned nominal screen with all 20 shafts at class maximum."""
    nominal_report, audit = _validate_nominal_report()
    _validate_geometry_binding(geometry, nominal_report)
    stacks = geometry.stacks
    installed = compact_tools._flatten_shapes(
        geometry.installed_hardware, "installed_hardware"
    )
    obstacles, _classes, _panel_ids = compact_tools._geometry_maps(geometry)
    floor_z = float(geometry.floor_z_mm)
    if not math.isfinite(floor_z):
        raise ValueError("geometry floor datum must be finite")

    maximum_mm = float(audit["ordinary_bolt_body_maximum_mm"])
    alternate_shafts: dict[str, cq.Shape] = {}
    alternate_sweeps: dict[str, cq.Shape] = {}
    alternate_records: dict[str, dict[str, Any]] = {}
    shaft_keys: dict[str, str] = {}
    for stack_id, stack in sorted(stacks.items()):
        candidate_class = stack.hardware.candidate_sku.lower()
        if "ordinary" not in candidate_class or "1/4-20" not in candidate_class:
            raise ValueError(
                f"stack is not labeled as an ordinary 1/4-20 position: {stack_id}"
            )
        target_keys = withdrawal._target_component_keys(installed, stack_id)
        shaft_key = target_keys["shaft"]
        if shaft_key not in obstacles:
            raise ValueError(f"installed shaft is absent from obstacle map: {stack_id}")
        maximum_shaft, maximum_sweep, record = _alternate_shaft_and_sweep(
            stack, installed[shaft_key], maximum_mm
        )
        alternate_shafts[shaft_key] = maximum_shaft
        alternate_sweeps[stack_id] = maximum_sweep
        alternate_records[stack_id] = record
        shaft_keys[stack_id] = shaft_key

    maximum_obstacles = _replace_all_modeled_shafts(obstacles, alternate_shafts)
    rows: dict[str, Any] = {}
    for stack_id, stack in sorted(stacks.items()):
        target_keys = withdrawal._target_component_keys(installed, stack_id)
        target_shapes = {role: installed[key] for role, key in target_keys.items()}
        nominal_installed_obstacles = withdrawal._withdrawal_obstacles(
            obstacles, target_keys
        )
        nominal_installed_key = "nominal_installed_shaft_occupancy"
        nominal_installed_screen = tool_access.collision_report(
            {nominal_installed_key: target_shapes["shaft"]},
            nominal_installed_obstacles,
            exclusion_scope=(
                "Nominal installed shaft screened against retained geometry, peer "
                "shafts, and same-stack washer rings. Its own shaft/head/nut are "
                "removed as target assembly parts; nut internal thread fit is not "
                "modeled."
            ),
        )
        nominal_installed_screen["floor_screen"] = compact_tools._floor_bounds(
            target_shapes["shaft"], floor_z
        )

        maximum_installed_key = "ordinary_class_maximum_installed_shaft"
        maximum_installed_obstacles = withdrawal._withdrawal_obstacles(
            maximum_obstacles, target_keys
        )
        maximum_installed_shaft = alternate_shafts[shaft_keys[stack_id]]
        maximum_installed_screen = tool_access.collision_report(
            {maximum_installed_key: maximum_installed_shaft},
            maximum_installed_obstacles,
            exclusion_scope=(
                "All twenty ordinary WJ-03 shaft bodies use the schedule-audit "
                "maximum occupancy. This target shaft is screened against wood, "
                "protected geometry, peer maximum shafts, and its retained "
                "same-stack washer rings. Same-stack head/nut contacts are not a "
                "thread-fit claim."
            ),
        )
        maximum_installed_screen["floor_screen"] = compact_tools._floor_bounds(
            maximum_installed_shaft, floor_z
        )

        nominal_row = nominal_report["stacks"][stack_id]
        nominal_record = nominal_row["shaft_sweep_geometry"]
        alternate_record = alternate_records[stack_id]
        for field in (
            "axis_xyz",
            "shaft_start_xyz_mm_from_installed_shape",
            "source_length_mm",
            "withdrawal_travel_mm",
            "sweep_length_mm",
        ):
            expected_field = (
                "shaft_start_xyz_mm"
                if field == "shaft_start_xyz_mm_from_installed_shape"
                else field
            )
            if nominal_record[field] != alternate_record[expected_field]:
                raise ValueError(f"nominal base sweep datum changed for {stack_id}")
        if not math.isclose(
            float(nominal_record["diameter_mm"]),
            float(stack.hardware.steel_diameter_mm),
            abs_tol=1e-9,
        ):
            raise ValueError(f"nominal base design diameter changed for {stack_id}")

        nut_outward = cq.Vector(stack.direction).normalized()
        nut_socket, nut_drive_center, _datum = withdrawal._socket_pose(
            cq.Vector(stack.nut_seat.center), target_shapes["nut"], nut_outward
        )
        shaft_obstacles = withdrawal._withdrawal_obstacles(
            maximum_obstacles, target_keys
        )
        socket_id = "tool_pair/stationary_nut_socket"
        shaft_obstacles[socket_id] = nut_socket
        max_sweep = alternate_sweeps[stack_id]
        candidate_key = "ordinary_class_maximum_shaft_withdrawal"
        fixed_screen = tool_access.collision_report(
            {candidate_key: max_sweep},
            shaft_obstacles,
            excluded_target_ids=(socket_id,),
            exclusion_scope=(
                "Same retained map and target exclusions as the nominal exact-shaft "
                "screen. All twenty WJ-03 peer shafts use the schedule-audit class "
                "maximum; only shaft body occupancy changes."
            ),
        )
        fixed_screen["floor_screen"] = compact_tools._floor_bounds(max_sweep, floor_z)
        max_fixed_ids = _hit_ids(fixed_screen, candidate_key)

        ratchet_cases, _case_record = withdrawal._stationary_ratchet_case_shapes(
            nut_drive_center,
            nut_outward,
            compact_tools._face_reference(nut_outward),
        )
        heading_screens: dict[str, Any] = {}
        for heading in withdrawal.COUNTERHOLD_HEADINGS_DEGREES:
            heading_key = _heading_key(heading)
            heading_obstacles = exact_shaft._heading_ratchet_shapes(
                ratchet_cases, heading
            )
            heading_screen = tool_access.collision_report(
                {candidate_key: max_sweep},
                heading_obstacles,
                exclusion_scope=(
                    "One sampled stationary-nut ratchet heading only; other mutually "
                    "exclusive headings are not unioned."
                ),
            )
            heading_screen["floor_screen"] = compact_tools._floor_bounds(
                max_sweep, floor_z
            )
            ratchet_ids = _hit_ids(heading_screen, candidate_key)
            max_combined = sorted(set(max_fixed_ids) | set(ratchet_ids))
            nominal_heading = nominal_row["stationary_nut_ratchet_heading_screens"][
                heading_key
            ]
            nominal_combined = set(nominal_heading["exact_sweep_hit_obstacle_ids"])
            heading_screens[heading_key] = {
                "ordinary_class_maximum_collision": heading_screen,
                "ratchet_heading_hit_obstacle_ids": ratchet_ids,
                "exact_sweep_hit_obstacle_ids": max_combined,
                "nominal_hit_obstacle_ids": sorted(nominal_combined),
                "new_hit_obstacle_ids_vs_nominal": sorted(
                    set(max_combined) - nominal_combined
                ),
                "removed_hit_obstacle_ids_vs_nominal": sorted(
                    nominal_combined - set(max_combined)
                ),
                "heading_is_separate_alternative": True,
            }

        nominal_fixed_ids = set(nominal_row["exact_fixed_obstacle_hit_ids"])
        rows[stack_id] = {
            "nominal": {
                "steel_design_diameter_mm": float(stack.hardware.steel_diameter_mm),
                "cad_occupied_diameter_mm": float(
                    stack.hardware.cad_occupied_diameter_mm
                ),
                "installed_occupancy_hit_ids": _hit_ids(
                    nominal_installed_screen, nominal_installed_key
                ),
                "installed_occupancy_screen": nominal_installed_screen,
                "fixed_obstacle_hit_ids": sorted(nominal_fixed_ids),
                "heading_hit_obstacle_ids": {
                    key: value["exact_sweep_hit_obstacle_ids"]
                    for key, value in nominal_row[
                        "stationary_nut_ratchet_heading_screens"
                    ].items()
                },
                "floor_screen": nominal_row["analytic_sweep_collision"]["floor_screen"],
            },
            "ordinary_class_maximum": {
                "cad_occupied_diameter_mm": maximum_mm,
                "shaft_geometry": alternate_record,
                "installed_occupancy_collision": maximum_installed_screen,
                "installed_occupancy_hit_ids": _hit_ids(
                    maximum_installed_screen, maximum_installed_key
                ),
                "fixed_collision": fixed_screen,
                "fixed_obstacle_hit_ids": max_fixed_ids,
                "heading_screens": heading_screens,
            },
            "comparison": {
                "new_installed_occupancy_hit_ids_vs_nominal": sorted(
                    set(_hit_ids(maximum_installed_screen, maximum_installed_key))
                    - set(_hit_ids(nominal_installed_screen, nominal_installed_key))
                ),
                "new_fixed_obstacle_hit_ids_vs_nominal": sorted(
                    set(max_fixed_ids) - nominal_fixed_ids
                ),
                "removed_fixed_obstacle_hit_ids_vs_nominal": sorted(
                    nominal_fixed_ids - set(max_fixed_ids)
                ),
                "new_heading_hit_ids_by_heading": {
                    key: value["new_hit_obstacle_ids_vs_nominal"]
                    for key, value in heading_screens.items()
                },
            },
        }

    return {
        "schema": SCHEMA,
        "trial_id": geometry.trial_id,
        "status": "ordinary_body_diameter_sensitivity_only_not_acceptance",
        "nominal_exact_shaft_report": {
            "path": str(NOMINAL_REPORT_PATH),
            "sha256": NOMINAL_REPORT_SHA256,
            "coarse_base_sha256": nominal_report["base_report"]["sha256"],
            "preserved_without_overwrite": True,
        },
        "source_binding": compact_tools._json_safe(geometry.source_binding),
        "source_pins": {
            "geometry_materializer_inputs": compact_tools._json_safe(
                geometry.source_pins
            ),
            "direct_inputs": _source_pins(),
            "hardware_schedule_audit": {
                "path": audit["source_path"],
                "sha256": audit["source_sha256"],
            },
        },
        "ordinary_body_maximum_basis": audit,
        "scenario": {
            "nominal_design_diameter_unchanged": True,
            "maximum_occupancy_applied_to_all_20_wj03_shafts": True,
            "axes_and_under_head_lengths_unchanged": True,
            "bores_and_seats_unchanged": True,
            "heads_nuts_and_washers_unchanged": True,
            "selected_or_received_sku_inferred": False,
            "other_nonshaft_geometry_changed": False,
        },
        "scope_limits": {
            "shaft_sweep_against_each_sampled_counterhold_shape_screened": True,
            "tool_envelopes_against_enlarged_peer_shaft_map_screened": False,
            "nominal_tool_route_applies_to_maximum_shaft_scenario": False,
            "note": (
                "This report screens enlarged shafts against retained geometry and "
                "peer maximum shafts, and each moving shaft sweep against one sampled "
                "counterhold shape. It does not screen tool envelopes against the "
                "enlarged peer-shaft map; nominal tool-route results cannot be "
                "upgraded to a maximum-diameter route result."
            ),
        },
        "candidate_stack_count": len(rows),
        "summary": {
            "nominal_installed_occupancy_hit_stacks": sum(
                bool(row["nominal"]["installed_occupancy_hit_ids"])
                for row in rows.values()
            ),
            "maximum_installed_occupancy_hit_stacks": sum(
                bool(row["ordinary_class_maximum"]["installed_occupancy_hit_ids"])
                for row in rows.values()
            ),
            "stacks_with_new_installed_occupancy_hits": sum(
                bool(row["comparison"]["new_installed_occupancy_hit_ids_vs_nominal"])
                for row in rows.values()
            ),
            "nominal_fixed_hit_stacks": sum(
                bool(row["nominal"]["fixed_obstacle_hit_ids"]) for row in rows.values()
            ),
            "maximum_fixed_hit_stacks": sum(
                bool(row["ordinary_class_maximum"]["fixed_obstacle_hit_ids"])
                for row in rows.values()
            ),
            "stacks_with_new_fixed_hits": sum(
                bool(row["comparison"]["new_fixed_obstacle_hit_ids_vs_nominal"])
                for row in rows.values()
            ),
            "new_fixed_hit_pairs": sum(
                len(row["comparison"]["new_fixed_obstacle_hit_ids_vs_nominal"])
                for row in rows.values()
            ),
            "stacks_with_new_hits_by_heading": {
                heading: sum(
                    bool(row["comparison"]["new_heading_hit_ids_by_heading"][heading])
                    for row in rows.values()
                )
                for heading in next(iter(rows.values()))["comparison"][
                    "new_heading_hit_ids_by_heading"
                ]
            },
        },
        "stacks": rows,
        "release_claims": {
            "delivered_bolt_fit_verified": False,
            "maximum_diameter_tool_route_verified": False,
            "fabrication_released": False,
            "structural_released": False,
        },
    }
