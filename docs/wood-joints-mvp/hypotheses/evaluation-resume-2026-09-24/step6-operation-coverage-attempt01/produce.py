#!/usr/bin/env python3
"""Produce a pinned, diagnostic Step 6 operation-coverage register."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
OUT_DIR = Path(__file__).resolve().parent
JSON_PATH = OUT_DIR / "operation-coverage.json"
README_PATH = OUT_DIR / "README.md"
REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
REVIEWED_COMMIT = "b1e8707d"
SELECTED_CANDIDATE = "compact-floor-flush-development"
DEVELOPMENT_CANDIDATE = "compact-floor-flush-wood-joints-development"

CANDIDATE = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "access-screen-attempt03-exact-components.json"
)
CAPTURED = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "captured-nut-motion-attempt02/motion.json"
)
RETAINED = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "retained-access-attempt03/access.json"
)
RECEIVER = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "receiver-screen-attempt04.json"
)
SCENE = "site/owner-wood-joints-wj24-scene.json"
REVIEW = "site/owner-wood-joints-review-report.json"
PARTS = "site/hybrid/compact-floor-flush-kerf-right/parts.json"
TOPOLOGY = "docs/wood-joints-mvp/hypotheses/wj18-panel-harness-topology/topology.json"

STATIC_INPUTS: list[tuple[str, str]] = [
    ("wood-joints-candidate.json", "development-lane and reviewed-revision authority"),
    ("current-candidate.json", "selected-candidate authority"),
    (SCENE, "current scene, inventory, counts, and embedded electrical replacement meshes"),
    (REVIEW, "current reviewed geometry findings and replacement records"),
    (PARTS, "current baseline asset manifest and service-part inventory"),
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "geometry-snapshot.json",
        "frozen reviewed geometry identity and axis move inventory",
    ),
    (CANDIDATE, "92 current candidate-bolt component, wrench-proxy, and motion screens"),
    (CAPTURED, "four current-revision local captured-nut motion diagnostics"),
    (RETAINED, "12 separate current retained-frame-bolt operation screens and corridor rows"),
    (RECEIVER, "66 current Hillman axis receiver-envelope screens"),
    ("docs/wood-joints-mvp/next-mvp-plan.md", "current refined eight-step plan and gate definitions"),
    ("docs/wood-joints-mvp/plan.md", "ordinary local-N and scope requirements"),
    ("docs/wood-joints-mvp/transport-operations.md", "current assembly and reverse-sequence hypothesis"),
    ("docs/wood-joints-mvp/current-layout-obligations.md", "current service and access reconciliation"),
    ("docs/wood-joints-mvp/current-access-screen.md", "candidate access-screen limitations"),
    ("docs/wood-joints-mvp/current-retained-access.md", "retained-bolt access-screen limitations"),
    ("docs/wood-joints-mvp/current-receiver-screen.md", "Hillman receiver-screen limitations"),
    ("docs/wood-joints-mvp/current-hardware-coverage.md", "delivered-stack and hardware-fit boundary"),
    ("docs/wood-joints-mvp/current-retained-wire-sequence.md", "current retained-wire interaction and service limits"),
    ("docs/led-wiring-reference.json", "LED routing order and installation reference"),
    ("docs/round-service-wiring-reference.json", "provisional harness installation sequence and unknowns"),
    (TOPOLOGY, "panel-ownership topology only; no older geometry or operation result"),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(relative_path: str) -> Any:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def source_binding(path: str, role: str) -> dict[str, str]:
    absolute = ROOT / path
    require(absolute.is_file(), f"Missing pinned input: {path}")
    return {"path": path, "role": role, "sha256": sha256_file(absolute)}


def sorted_unique(values: list[str]) -> list[str]:
    return sorted(set(values))


def collision_summary(operation: dict[str, Any]) -> dict[str, Any]:
    screen = operation.get("collision_screen")
    if screen is None:
        screen = operation if "external_envelope_clear" in operation else {}
    reported_hits = screen.get("external_envelope_hits_mm3", {})
    blocker_ids = list(operation.get("potential_blocker_ids", []))
    overlap_entry_count = 0

    def add_obstacles(value: Any) -> None:
        nonlocal overlap_entry_count
        if isinstance(value, dict):
            for key, child in value.items():
                if isinstance(child, (int, float)):
                    overlap_entry_count += 1
                if isinstance(key, str) and (
                    key.startswith("wood/")
                    or key.startswith("protected/")
                    or key.startswith("candidate_stack/")
                ):
                    blocker_ids.append(key)
                add_obstacles(child)

    add_obstacles(reported_hits)
    return {
        "screen_result": (
            "clear_proxy_envelope"
            if screen.get("external_envelope_clear") is True
            else "proxy_envelope_intersection"
            if screen.get("external_envelope_clear") is False
            else "not_reported"
        ),
        "external_envelope_clear": screen.get("external_envelope_clear"),
        "potential_blocker_ids": sorted_unique(blocker_ids),
        "reported_overlap_entry_count": overlap_entry_count,
        "bounds_are_conservative": screen.get("bounds_are_conservative"),
        "physical_motion_established": operation.get("physical_motion_established", False),
        "physical_access_established": screen.get("physical_access_established", False),
        "clear_envelope_proves_access": screen.get("clear_envelope_proves_actual_tool_access", False),
        "scope": "current source geometry envelope only; not a physical-fit result",
    }


def check_summary(check: dict[str, Any]) -> dict[str, Any]:
    screen = check.get("collision_screen", {})
    overlap_entry_count = 0

    def count_entries(value: Any) -> None:
        nonlocal overlap_entry_count
        if isinstance(value, dict):
            for child in value.values():
                if isinstance(child, (int, float)):
                    overlap_entry_count += 1
                else:
                    count_entries(child)
        elif isinstance(value, list):
            for child in value:
                count_entries(child)

    count_entries(screen.get("external_envelope_hits_mm3", {}))
    return {
        "screen_result": (
            "clear_proxy_envelope"
            if screen.get("external_envelope_clear") is True
            else "proxy_envelope_intersection"
            if screen.get("external_envelope_clear") is False
            else "not_reported"
        ),
        "external_envelope_clear": screen.get("external_envelope_clear"),
        "potential_blocker_ids": sorted_unique(check.get("potential_blocker_ids", [])),
        "reported_overlap_entry_count": overlap_entry_count,
        "exact_tool_sweep": check.get("exact_tool_sweep", False),
    }


def summarize_wrench(wrench: dict[str, Any]) -> dict[str, Any]:
    approach: list[dict[str, Any]] = []
    turn: list[dict[str, Any]] = []
    angular: list[dict[str, Any]] = []
    blockers: list[str] = []
    for heading in wrench.get("pose_rows", []):
        approach.append(collision_summary(heading["approach_proxy"]))
        blockers.extend(heading["approach_proxy"].get("potential_blocker_ids", []))
        for sample in heading.get("discrete_turn_pose_samples", []):
            turn.append(check_summary(sample))
            blockers.extend(sample.get("potential_blocker_ids", []))
        for enclosure in heading.get("continuous_30_degree_AABB_enclosures", []):
            angular.append(check_summary(enclosure))
            blockers.extend(enclosure.get("potential_blocker_ids", []))

    def group(checks: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "checks": len(checks),
            "proxy_clear_count": sum(c["external_envelope_clear"] is True for c in checks),
            "proxy_intersection_count": sum(c["external_envelope_clear"] is False for c in checks),
            "not_reported_count": sum(c["external_envelope_clear"] is None for c in checks),
            "potential_blocker_ids": sorted_unique(
                [item for check in checks for item in check["potential_blocker_ids"]]
            ),
        }

    profile = wrench.get("profile_source", {})
    return {
        "target_role": wrench.get("target_role"),
        "profile_source": {
            key: profile.get(key)
            for key in (
                "manufacturer",
                "candidate_id",
                "head_width_mm",
                "head_thickness_mm",
                "overall_length_mm",
                "profile_is_current_selected_tool_or_fit",
            )
        },
        "synthetic_heading_samples_degrees": profile.get("synthetic_heading_samples_degrees", []),
        "sampled_turn_angles_degrees": wrench.get("sampled_turn_angles_degrees", []),
        "approach_proxy": group(approach),
        "discrete_turn_pose_proxies": group(turn),
        "continuous_30_degree_aabb_proxies": group(angular),
        "potential_blocker_ids": sorted_unique(blockers),
        "actual_tool_access_established": wrench.get("actual_tool_access_established", False),
        "unthreading_or_torque_screened": wrench.get("unthreading_or_torque_screened", False),
        "scope": "synthetic proxy checks; no jaw fit, hand space, physical tool, or torque proof",
    }


def captured_motion_summary(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    options = []
    for option in row.get("lateral_then_axial_options", []):
        options.append(
            {
                "lateral_displacement_xyz_mm": option.get("lateral_displacement_xyz_mm"),
                "lateral_screen": collision_summary(option.get("lateral_collision", {})),
                "following_nutward_displacement_xyz_mm": option.get(
                    "following_nutward_displacement_xyz_mm"
                ),
                "following_nutward_screen": collision_summary(
                    option.get("following_nutward_collision", {})
                ),
                "two_stage_cad_motion_clear": option.get("two_stage_cad_motion_clear"),
            }
        )
    return {
        "source_axis_id": row["axis_id"],
        "headward_travel_mm": row.get("headward_travel_mm"),
        "headward_terminal_allowance_mm": row.get("headward_terminal_allowance_mm"),
        "boreless_nut_shaft_display_overlap_initial_mm3": row.get(
            "shaft_nut_display_envelope_initial_overlap_mm3"
        ),
        "boreless_nut_shaft_display_overlap_swept_mm3": row.get(
            "shaft_nut_display_envelope_swept_overlap_mm3"
        ),
        "nut_shaft_overlap_interpretation": row.get("shaft_nut_overlap_interpretation"),
        "headward_screen": collision_summary(row.get("headward_external_collision", {})),
        "local_lateral_then_nutward_options": options,
        "full_scene_extraction_or_staging_established": False,
        "threading_capture_or_physical_tool_established": False,
        "scope": "bounded local CAD path after assumed unthreading; not loose-part retrieval",
    }


def operation_reference(path: str, locator: str) -> dict[str, str]:
    return {"path": path, "locator": locator}


def standard_limits(local_n: bool = True) -> dict[str, Any]:
    return {
        "modeled_proxy_geometry_only": True,
        "real_tool_fit_established": False,
        "delivered_hardware_fit_established": False,
        "physical_fit_established": False,
        "support_transfer_established": False,
        "part_capture_or_service_restraint_established": False,
        "tolerance_status": "unresolved_not_accounted_for",
        "ordinary_local_n_139_7_mm_status": "unresolved_not_assessed" if local_n else "not_applicable",
    }


def bolt_operation_statuses(
    source_row: dict[str, Any],
    source_path: str,
    captured_row: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    operations = source_row["operations"]
    head = operations["head_side_bolt"]
    nut = operations["nut"]
    nut_washer = operations["nut_washer"]
    source_locator = f"axis_operations/{source_row['axis_id']}"
    wrench_screens = {
        "head_end": summarize_wrench(operations["head_wrench"]),
        "nut_end": summarize_wrench(operations["nut_wrench"]),
    }

    install_details = {
        "status": "component_insertion_envelopes_screened_only",
        "head_side_bolt": collision_summary(head["reverse_assembly"]),
        "nut_reverse_assembly": collision_summary(nut["reverse_assembly"]),
        "nut_washer_reverse_assembly": collision_summary(nut_washer["reverse_assembly"]),
        "complete_joint_assembly_or_disassembly_proven": source_row.get(
            "complete_joint_assembly_or_disassembly_proven", False
        ),
        "physical_installation_established": False,
        "prerequisites_unresolved": [
            "matched delivered bolt/nut/washer stack and fit",
            "thread-compatible receiver path and full nut engagement",
            "real tool approach, turning, counterhold and hand clearance",
            "support and capture for each component",
            "tolerance-aware complete sequence",
        ],
    }
    turn = {
        "status": "synthetic_tool_proxy_screens_only",
        "head_end_and_nut_end_kept_separate": True,
        "actual_turning_or_torque_established": False,
        "screen_reference": source_locator,
    }
    counterhold = {
        "status": "not_established",
        "side_assignment": "No complete turn/counterhold pairing is assigned by the source screen.",
        "available_proxy_screens": ["head_end", "nut_end"],
        "actual_counterhold_tool_or_workspace_established": False,
    }

    nut_retrieval = {
        "derived_axial_travel_mm": nut.get("derived_axial_travel_mm"),
        "terminal_allowance_mm": nut.get("terminal_allowance_mm"),
        "threaded_disengagement_or_part_capture_established": nut.get(
            "threaded_disengagement_or_part_capture_established", False
        ),
        "axial_slide_screen": collision_summary(nut["removal"]),
    }
    washer_retrieval = {
        "derived_axial_travel_mm": nut_washer.get("derived_axial_travel_mm"),
        "terminal_allowance_mm": nut_washer.get("terminal_allowance_mm"),
        "threaded_disengagement_or_part_capture_established": nut_washer.get(
            "threaded_disengagement_or_part_capture_established", False
        ),
        "axial_slide_screen": collision_summary(nut_washer["removal"]),
    }
    retrieval = {
        "status": "capture_and_staging_not_established",
        "nut": nut_retrieval,
        "nut_washer": washer_retrieval,
        "captured_nut_local_motion": captured_motion_summary(captured_row),
        "complete_loose_part_retrieval_established": False,
        "note": (
            "A clear slide envelope assumes prior unthreading and does not show where a loose part "
            "is held or staged. The four local paths are bounded CAD motions only."
        ),
    }
    withdrawal = {
        "status": "component_envelopes_screened_only",
        "head_head_washer_and_shaft": {
            "components": ["head", "head_washer", "shaft"],
            "component_sweep_methods": head.get("component_sweep_methods", {}),
            "shaft_sweep_method": head.get("shaft_sweep_method"),
            "derived_travel_mm": head.get("derived_travel_mm"),
            "travel_basis": head.get("travel_basis"),
            "support_transfer_and_capture_established": head.get(
                "support_transfer_and_capture_established", False
            ),
            "screen": collision_summary(head["withdrawal"]),
        },
        "nut": nut_retrieval,
        "nut_washer": washer_retrieval,
        "physical_withdrawal_established": False,
    }
    reverse = {
        "status": "reverse_component_envelopes_screened_only",
        "head_side_bolt": collision_summary(head["reverse_assembly"]),
        "nut": collision_summary(nut["reverse_assembly"]),
        "nut_washer": collision_summary(nut_washer["reverse_assembly"]),
        "complete_reverse_sequence_established": False,
        "physical_reverse_installation_established": False,
    }
    operations_out = {
        "install": install_details,
        "turn": turn,
        "counterhold": counterhold,
        "retrieval": retrieval,
        "withdrawal": withdrawal,
        "reverse_assembly": reverse,
    }
    refs = {
        "motion_and_tool_proxy_screens": operation_reference(source_path, source_locator),
        "capture_motion": (
            operation_reference(CAPTURED, f"axis_operations/{source_row['axis_id']}")
            if captured_row
            else None
        ),
    }
    return operations_out, {"tool_proxy_screens": wrench_screens, "source_records": refs}


def make_axis_records(
    scene: dict[str, Any],
    candidate_access: dict[str, Any],
    captured: dict[str, Any],
    retained_access: dict[str, Any],
    receiver: dict[str, Any],
    moved_rows: dict[str, dict[str, Any]],
    block_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_inventory = scene["model_inventory"]["candidate_axes"]
    candidate_rows = {row["axis_id"]: row for row in candidate_access["axis_operations"]}
    captured_rows = {row["axis_id"]: row for row in captured["axis_operations"]}
    retained_inventory = {
        row["axis_id"]: row for row in scene["model_inventory"]["starting_frame_bolts"]
    }
    retained_rows = {row["axis_id"]: row for row in retained_access["axis_operations"]}
    receiver_rows = {row["axis_id"]: row for row in receiver["axes"]}
    records: list[dict[str, Any]] = []
    block_counts = {block_id: 0 for block_id in block_ids}

    for axis_id in sorted(candidate_inventory):
        inv = candidate_inventory[axis_id]
        row = candidate_rows[axis_id]
        owners = sorted(set(inv["receiver_ids"]) & block_ids)
        require(owners, f"Candidate axis must map to a current block: {axis_id}")
        for owner in owners:
            block_counts[owner] += 1
        operation_statuses, extras = bolt_operation_statuses(
            row, CANDIDATE, captured_rows.get(axis_id)
        )
        records.append(
            {
                "record_id": f"candidate-bolt:{axis_id}",
                "record_type": "candidate_bolt_stack",
                "entity_id": axis_id,
                "geometry_revision_id": REVISION_ID,
                "block_ids": owners,
                "station_id": inv.get("station_id"),
                "family": inv["family"],
                "trial_id": inv["trial_id"],
                "receiver_ids": inv["receiver_ids"],
                "modeled_component_roles": inv["installed_component_roles"],
                "modeled_stack_complete_operation_proven": row.get(
                    "complete_joint_assembly_or_disassembly_proven", False
                ),
                "operation_statuses": operation_statuses,
                **extras,
                "fit_and_use_limits": standard_limits(),
                "source_records": [
                    operation_reference(SCENE, f"model_inventory/candidate_axes/{axis_id}"),
                    operation_reference(CANDIDATE, f"axis_operations/{axis_id}"),
                ],
            }
        )

    for axis_id in sorted(retained_inventory):
        inv = retained_inventory[axis_id]
        row = retained_rows[axis_id]
        operation_statuses, extras = bolt_operation_statuses(row, RETAINED, None)
        records.append(
            {
                "record_id": f"retained-frame-bolt:{axis_id}",
                "record_type": "retained_frame_bolt_stack",
                "entity_id": axis_id,
                "geometry_revision_id": REVISION_ID,
                "receiver_ids": inv["members"],
                "nominal_source_occupied_length_mm": inv.get("source_occupied_length_mm"),
                "nominal_source_occupied_diameter_mm": inv.get("source_occupied_diameter_mm"),
                "modeled_component_count_in_scene": inv.get("installed_component_count"),
                "candidate_recheck_status": inv.get("candidate_recheck_status"),
                "operation_statuses": operation_statuses,
                **extras,
                "fit_and_use_limits": standard_limits(),
                "source_records": [
                    operation_reference(SCENE, f"model_inventory/starting_frame_bolts/{axis_id}"),
                    operation_reference(RETAINED, f"axis_operations/{axis_id}"),
                ],
            }
        )

    for axis_id in sorted(receiver_rows):
        row = receiver_rows[axis_id]
        move = moved_rows.get(axis_id)
        install_status = (
            "current_axis_envelope_clears_finished_receiver"
            if row.get("finished_receiver_axis_envelope_clear") is True
            else "current_axis_envelope_receiver_screen_not_clear"
        )
        records.append(
            {
                "record_id": f"hillman-axis:{axis_id}",
                "record_type": "hillman_42605_panel_kicker_axis",
                "entity_id": axis_id,
                "geometry_revision_id": REVISION_ID,
                "panel_member": row["panel_member"],
                "receiver_member": row["receiver_member"],
                "location_status": row["current_location_status"],
                "move_from_owner_directed_revision": move,
                "purchased_product_policy": row["purchased_product_policy"],
                "purchased_length_mm": row["purchased_length_mm"],
                "modeled_axis_envelope": {
                    "diameter_mm": row.get("source_occupied_diameter_mm"),
                    "current_axis_length_mm": row.get("materialized_axis_envelope", {}).get(
                        "axial_length_mm"
                    ),
                    "raw_receiver_intersection_mm3": row.get(
                        "raw_receiver_axis_envelope_intersection_volume_mm3"
                    ),
                    "finished_receiver_overlap_mm3": row.get(
                        "finished_receiver_axis_envelope_overlap_volume_mm3"
                    ),
                    "finished_receiver_axis_envelope_clear": row.get(
                        "finished_receiver_axis_envelope_clear"
                    ),
                    "status": row.get("materialized_axis_envelope", {}).get("status"),
                },
                "operation_statuses": {
                    "install": {
                        "status": install_status,
                        "physical_installation_or_embedment_established": False,
                        "evidence_scope": "current occupied-axis envelope against raw/finished receiver geometry",
                    },
                    "turn": {
                        "status": "driver_access_and_rotation_not_screened",
                        "actual_driver_access_established": False,
                    },
                    "counterhold": {
                        "status": "not_applicable_to_self_driven_screw; driver_route_unresolved",
                        "actual_driver_access_established": False,
                    },
                    "retrieval": {
                        "status": "not_screened",
                        "capture_or_panel_staging_established": False,
                    },
                    "withdrawal": {
                        "status": "not_screened",
                        "physical_withdrawal_established": False,
                    },
                    "reverse_assembly": {
                        "status": "not_screened",
                        "physical_reverse_installation_established": False,
                    },
                },
                "fit_and_use_limits": standard_limits(),
                "source_records": [operation_reference(RECEIVER, f"axes/{axis_id}")],
            }
        )

    require(len(candidate_rows) == 92, "Expected 92 current candidate access rows")
    require(len(retained_rows) == 12, "Expected 12 separate retained access rows")
    require(len(receiver_rows) == 66, "Expected 66 separate Hillman receiver rows")
    require(set(candidate_rows) == set(candidate_inventory), "Candidate axis join mismatch")
    require(set(retained_rows) == set(retained_inventory), "Retained frame-bolt join mismatch")
    require(set(receiver_rows) == (set(scene["model_inventory"]["fixed_panel_axes"])
            | {row["axis_id"] for row in scene["model_inventory"]["moved_panel_axes"]}),
            "Hillman axis join mismatch")
    require(set(captured_rows) == {axis for axis, row in candidate_rows.items()
                                   if row["operations"]["nut"]["removal"].get("potential_blocker_ids")},
            "Captured-nut rows must match the four current nut-slide blockers")

    block_rows = [
        {
            "block_id": block_id,
            "candidate_bolt_axis_count": block_counts[block_id],
            "candidate_bolt_axis_ids": sorted(
                axis_id for axis_id, row in candidate_inventory.items()
                if block_id in row["receiver_ids"]
            ),
            "geometry_revision_id": REVISION_ID,
            "complete_joint_acceptance": False,
            "support_and_tolerance_status": "unresolved",
        }
        for block_id in sorted(block_ids)
    ]
    return records, block_rows


def parse_tnut_location(description: str) -> tuple[str | None, str | None]:
    match = re.search(r"Panel ([A-Za-z0-9_]+); datum ([A-K]\d{1,2}|\d{1,2})\.", description)
    return (match.group(1), match.group(2)) if match else (None, None)


def inspect_hits(value: Any, needle: str, path: str = "") -> list[dict[str, Any]]:
    """Extract already-reported obstacle hits; this performs no geometry query."""
    hits: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            next_path = f"{path}/{key}"
            if isinstance(key, str) and needle in key:
                if isinstance(child, (int, float)):
                    hits.append({"screen_path": path})
                elif isinstance(child, dict):
                    hits.append({"screen_path": path})
            hits.extend(inspect_hits(child, needle, next_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(inspect_hits(child, needle, f"{path}/{index}"))
    return hits


def make_service_records(
    scene: dict[str, Any],
    review: dict[str, Any],
    parts_data: dict[str, Any],
    retained_access: dict[str, Any],
    candidate_access: dict[str, Any],
    led_reference: dict[str, Any],
    wiring_reference: dict[str, Any],
    topology: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    parts = parts_data["parts"]
    tnut_parts = {part["name"]: part for part in parts if part["name"].startswith("hold_tnut_")}
    led_parts = {part["name"]: part for part in parts if part["name"].startswith("light_")}
    wire_parts = {part["name"]: part for part in parts if part["name"].startswith("wire_")}
    corridor_rows = {
        row["shape_id"]: row
        for row in retained_access["scope"]["access_only_protected_envelopes_excluded_globally"]
        if row.get("family") == "hold_hole_and_provisional_projection"
    }
    require(len(tnut_parts) == len(corridor_rows) == 142, "Expected 142 one-to-one current T-nut corridor rows")
    require(set(tnut_parts) == set(corridor_rows), "T-nut part/corridor ID join mismatch")

    led_owner = topology["fixed_led_owner_by_label"]
    led_order = led_reference["routing"]["order"]
    require(len(led_order) == 132 and set(led_owner) == set(led_order), "LED topology/routing join mismatch")
    # Sort by numeric wire suffix, not lexically.
    wire_names = sorted(wire_parts, key=lambda name: int(name.split("_")[1]))
    require(len(wire_names) == 131, "Expected 131 baseline wire assets")
    expected_wire_by_index = {}
    for index, wire_name in enumerate(wire_names, start=1):
        suffix = wire_name.removeprefix("wire_")
        wire_number, left, right = suffix.split("_", 2)
        require(int(wire_number) == index, f"Noncontiguous current wire index: {wire_name}")
        require([left, right] == led_order[index - 1:index + 1], f"Wire route order mismatch: {wire_name}")
        expected_wire_by_index[index] = wire_name

    review_wire_changes = {
        row["wire"]: row for row in review["focused_geometry_checks"]["led_and_tail_clearance"]["wire_changes"]
    }
    report_solids = {solid["id"]: solid for solid in scene["solids"]}
    electrical_replacements = review.get("electrical_replacements", {})
    led_checks = {row["label"]: row for row in review.get("led_hole_review", [])}
    boundary_ids = {f"wire_{row['index']:03d}_{row['labels'][0]}_{row['labels'][1]}"
                    for row in topology.get("factory_string_boundaries", [])}
    cross_ids = {row["wire_id"] for row in topology.get("cross_panel_wires", [])}

    retained_wire_refs: dict[str, list[dict[str, Any]]] = {}
    for axis in retained_access["axis_operations"]:
        op = axis["operations"]["head_side_bolt"]["withdrawal"]
        screen = op.get("collision_screen", {})
        for wire_name in wire_parts:
            for hit in inspect_hits(screen.get("external_envelope_hits_mm3", {}), wire_name):
                retained_wire_refs.setdefault(wire_name, []).append(
                    {"axis_id": axis["axis_id"], "operation": "head_side_bolt_withdrawal",
                     **hit}
                )

    candidate_wire_refs: dict[str, list[dict[str, Any]]] = {}
    candidate_source_rows = {row["axis_id"]: row for row in candidate_access["axis_operations"]}
    for axis_id, axis in candidate_source_rows.items():
        for wire_name in wire_names:
            wire_id = "protected/wires/" + wire_name
            for hit in inspect_hits(axis.get("operations", {}), wire_id):
                candidate_wire_refs.setdefault(wire_name, []).append(
                    {"axis_id": axis_id, "source_locator": f"axis_operations/{axis_id}/operations",
                     **hit}
                )

    asset_pins: list[dict[str, str]] = []
    service_records: list[dict[str, Any]] = []
    baseline_assets = scene["baseline_asset_sha256"]

    for name in sorted(tnut_parts):
        part = tnut_parts[name]
        corridor = corridor_rows[name]
        panel, datum = parse_tnut_location(part["fabrication"].get("description", ""))
        asset_key = part["path"]
        actual_hash = sha256_file(ROOT / "site" / asset_key)
        expected_hash = baseline_assets.get(asset_key)
        require(expected_hash is not None and actual_hash == expected_hash,
                f"Baseline asset digest mismatch for {asset_key}")
        asset_pins.append({"path": "site/" + asset_key, "sha256": actual_hash,
                           "role": "current baseline T-nut display asset"})
        current_finding = None
        if datum == "G6":
            current_finding = "Middle corner block intersects provisional rear-clearance envelope; actual hold/bolt fit is unresolved."
        elif datum == "G12":
            current_finding = "Top-right center block retains overlap with provisional rear-clearance envelope; actual hold/bolt fit is unresolved."
        service_records.append(
            {
                "record_id": f"hold-tnut-corridor:{name}",
                "record_type": "hold_tnut_corridor",
                "entity_id": name,
                "geometry_revision_id": REVISION_ID,
                "panel_member": panel,
                "datum": datum,
                "baseline_tnut_asset": {"path": "site/" + asset_key, "sha256": actual_hash},
                "modeled_tnut_dimensions_mm": part["fabrication"].get("dimensions_mm"),
                "provisional_corridor": {
                    "classification": corridor["classification"],
                    "access_obstacle_id": corridor["obstacle_id"],
                    "bounds_min_xyz_mm": corridor["shape_summary"].get("min_xyz_mm"),
                    "bounds_max_xyz_mm": corridor["shape_summary"].get("max_xyz_mm"),
                    "volume_mm3": corridor["shape_summary"].get("volume_mm3"),
                    "screen_treatment": "temporary projection envelope; excluded globally from retained-bolt access screen",
                },
                "current_layout_finding": current_finding,
                "operation_statuses": {
                    "install": {
                        "status": "baseline_display_envelope_only",
                        "physical_tnut_installation_or_panel_fit_established": False,
                    },
                    "turn": {"status": "not_screened_for_a_selected_hold_or_bolt_product"},
                    "counterhold": {"status": "not_screened_for_a_selected_hold_or_bolt_product"},
                    "retrieval": {"status": "not_screened", "part_capture_established": False},
                    "withdrawal": {"status": "not_screened", "physical_withdrawal_established": False},
                    "reverse_assembly": {"status": "not_screened"},
                },
                "fit_and_use_limits": standard_limits(local_n=False),
                "source_records": [
                    operation_reference(PARTS, f"parts/{name}"),
                    operation_reference(RETAINED, "scope/access_only_protected_envelopes_excluded_globally"),
                    operation_reference(REVIEW, "findings"),
                ],
            }
        )

    for order_index, label in enumerate(led_order, start=1):
        name = f"light_{label}"
        part = led_parts[name]
        asset_key = part["path"]
        actual_hash = sha256_file(ROOT / "site" / asset_key)
        expected_hash = baseline_assets.get(asset_key)
        require(expected_hash is not None and actual_hash == expected_hash,
                f"Baseline asset digest mismatch for {asset_key}")
        asset_pins.append({"path": "site/" + asset_key, "sha256": actual_hash,
                           "role": "baseline LED display asset"})
        override = None
        if name in electrical_replacements:
            solid = report_solids.get(name)
            require(solid is not None, f"Missing current scene override mesh for {name}")
            override = {
                "scene_display_class": solid.get("display_class"),
                "triangle_topology_sha256": solid.get("mesh", {}).get("triangle_topology_sha256"),
                "bounds_xyz_mm": solid.get("mesh", {}).get("bounds_xyz_mm"),
                "current_override_source": "current scene embedded display mesh; scene SHA-256 is pinned",
            }
        check = led_checks.get(label)
        adjacent = []
        for index in (order_index - 1, order_index):
            if index in expected_wire_by_index:
                adjacent.append(expected_wire_by_index[index])
        service_records.append(
            {
                "record_id": f"led:{name}",
                "record_type": "modeled_led_service_item",
                "entity_id": name,
                "geometry_revision_id": REVISION_ID,
                "label": label,
                "route_order_index_1_based": order_index,
                "topology_owner_panel": led_owner[label],
                "owner_mapping_scope": "WJ18 panel ownership topology only; no prior geometry or fit result imported",
                "adjacent_modeled_wire_ids": adjacent,
                "baseline_asset": {"path": "site/" + asset_key, "sha256": actual_hash},
                "current_revision_display_override": override,
                "current_narrow_hole_check": (
                    {
                        "hole_path_diameter_mm": check.get("path_diameter_mm"),
                        "hole_path_depth_mm": check.get("path_depth_mm"),
                        "path_timber_hits": check.get("path_timber_hits"),
                        "light_body_timber_hits": check.get("light_body_timber_hits"),
                        "nearest_listed_block_clearance_mm": min(
                            (item["clearance_mm"] for item in check.get("nearby_block_clearances", [])),
                            default=None,
                        ),
                        "scope": "current G1/G2 nominal hole and body check only; not feeding, connector, tolerance, or extraction",
                    }
                    if check
                    else None
                ),
                "current_led_datum_override_mm": (
                    review.get("led_datum_overrides_mm", {}).get("G2") if label == "G2" else None
                ),
                "current_led_move": review.get("led_move") if label == "G2" else None,
                "operation_statuses": {
                    "install": {
                        "status": "documented_order_only",
                        "sequence": wiring_reference["installation"].get("sequence"),
                        "physical_feed_or_led_installation_established": False,
                    },
                    "turn": {"status": "not_applicable_to_led"},
                    "counterhold": {"status": "not_applicable_to_led"},
                    "retrieval": {"status": "not_established", "physical_capture_established": False},
                    "withdrawal": {"status": "not_screened_for_physical_led_extraction"},
                    "reverse_assembly": {"status": "not_established", "refeed_and_reseat_unverified": True},
                },
                "fit_and_use_limits": standard_limits(local_n=False),
                "source_records": [
                    operation_reference(PARTS, f"parts/{name}"),
                    operation_reference(TOPOLOGY, f"fixed_led_owner_by_label/{label}"),
                    operation_reference("docs/led-wiring-reference.json", f"routing/order/{order_index - 1}"),
                    operation_reference(REVIEW, "led_hole_review" if check else "electrical_replacements"),
                ],
            }
        )

    for wire_name in wire_names:
        part = wire_parts[wire_name]
        wire_number, left, right = wire_name.removeprefix("wire_").split("_", 2)
        index = int(wire_number)
        asset_key = part["path"]
        actual_hash = sha256_file(ROOT / "site" / asset_key)
        expected_hash = baseline_assets.get(asset_key)
        require(expected_hash is not None and actual_hash == expected_hash,
                f"Baseline asset digest mismatch for {asset_key}")
        asset_pins.append({"path": "site/" + asset_key, "sha256": actual_hash,
                           "role": "baseline modeled-wire display asset"})
        owner_pair = [led_owner[left], led_owner[right]]
        override = None
        if wire_name in electrical_replacements:
            solid = report_solids.get(wire_name)
            require(solid is not None, f"Missing current scene override mesh for {wire_name}")
            override = {
                "scene_display_class": solid.get("display_class"),
                "triangle_topology_sha256": solid.get("mesh", {}).get("triangle_topology_sha256"),
                "bounds_xyz_mm": solid.get("mesh", {}).get("bounds_xyz_mm"),
                "current_override_source": "current scene embedded display mesh; scene SHA-256 is pinned",
            }
        review_change = review_wire_changes.get(wire_name)
        known_interactions = []
        if review_change:
            known_interactions.append(
                {
                    "kind": "current_revision_display_geometry_check",
                    "hits": review_change.get("hits", []),
                    "interpretation": "fixed display-solid intersections; not flexible-cable blockage or physical fit",
                }
            )
        if wire_name == "wire_072_F1_G1":
            known_interactions.append(
                {
                    "kind": "current_review_finding_text",
                    "finding": "Taller right central block also crosses the wire between F1 and G1.",
                    "quantitative_screen": "No per-row overlap quantity included in the current revision summary.",
                }
            )
        service_records.append(
            {
                "record_id": f"wire:{wire_name}",
                "record_type": "modeled_wire_service_segment",
                "entity_id": wire_name,
                "geometry_revision_id": REVISION_ID,
                "routing_order_index_1_based": index,
                "endpoint_labels": [left, right],
                "topology_owner_panels": owner_pair,
                "cross_panel_by_topology": owner_pair[0] != owner_pair[1],
                "factory_string_boundary": wire_name in boundary_ids,
                "ownership_scope": "WJ18 topology only; current docs cite it for ownership, not geometry",
                "baseline_asset": {"path": "site/" + asset_key, "sha256": actual_hash},
                "current_revision_display_override": override,
                "current_review_geometry_interactions": known_interactions,
                "current_access_screen_proxy_references": candidate_wire_refs.get(wire_name, []),
                "current_retained_bolt_withdrawal_references": retained_wire_refs.get(wire_name, []),
                "operation_statuses": {
                    "install": {
                        "status": "documented_route_order_only",
                        "physical_feed_or_wire_attachment_established": False,
                    },
                    "turn": {"status": "not_applicable_to_wire_segment"},
                    "counterhold": {"status": "not_applicable_to_wire_segment"},
                    "retrieval": {"status": "not_established", "physical_capture_or_slack_established": False},
                    "withdrawal": {"status": "not_established", "feed_out_or_service_state_unverified": True},
                    "reverse_assembly": {"status": "not_established", "refeed_or_restoration_unverified": True},
                },
                "fit_and_use_limits": standard_limits(local_n=False),
                "source_records": [
                    operation_reference(PARTS, f"parts/{wire_name}"),
                    operation_reference(TOPOLOGY, "cross_panel_wires/factory_string_boundaries"),
                    operation_reference(REVIEW, "focused_geometry_checks/led_and_tail_clearance/wire_changes"),
                    operation_reference(CANDIDATE, "axis_operations/*/operations"),
                    operation_reference(RETAINED, "axis_operations/*/operations/head_side_bolt/withdrawal"),
                ],
            }
        )

    require(len(led_parts) == 132 and len(wire_parts) == 131, "Unexpected LED/wire service inventory")
    require(len(cross_ids) == 12, "Expected twelve topology cross-panel wire segments")
    derived_cross_ids = {
        row["entity_id"] for row in service_records
        if row["record_type"] == "modeled_wire_service_segment" and row["cross_panel_by_topology"]
    }
    require(derived_cross_ids == cross_ids,
            "WJ18 topology cross-panel wire IDs do not match joined route owners")
    require(sum(row["cross_panel_by_topology"] for row in service_records
                if row["record_type"] == "modeled_wire_service_segment") == 12,
            "Topology-derived cross-panel count does not reconcile")
    require(boundary_ids == {"wire_050_E2_E3", "wire_100_I4_I5"},
            "Current topology factory boundaries do not reconcile")
    require(len(service_records) == 405, "Expected 142 + 132 + 131 service rows")
    return service_records, sorted(asset_pins, key=lambda pin: pin["path"])


def build_artifact() -> dict[str, Any]:
    lane = read_json("wood-joints-candidate.json")
    selected = read_json("current-candidate.json")
    scene = read_json(SCENE)
    review = read_json(REVIEW)
    parts = read_json(PARTS)
    geometry = read_json(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json"
    )
    candidate_access = read_json(CANDIDATE)
    captured = read_json(CAPTURED)
    retained_access = read_json(RETAINED)
    receiver = read_json(RECEIVER)
    led_reference = read_json("docs/led-wiring-reference.json")
    wiring_reference = read_json("docs/round-service-wiring-reference.json")
    topology = read_json(TOPOLOGY)

    revision = lane["current_development_revision"]
    counts = scene["counts"]
    require(selected["candidate"] == SELECTED_CANDIDATE, "Selected candidate authority changed")
    require(lane["candidate"] == DEVELOPMENT_CANDIDATE, "Development candidate identity changed")
    require(revision["revision_id"] == REVISION_ID, "Reviewed development revision changed")
    require(revision["reviewed_repository_commit"] == REVIEWED_COMMIT,
            "Recorded reviewed commit changed")
    require(scene["revision_id"] == review["revision_id"] == geometry["revision_id"] == REVISION_ID,
            "Current scene/report/geometry revision mismatch")
    require(scene["counts"] == geometry["counts"],
            "Scene and frozen geometry-snapshot counts differ")
    moved_ids = {row["axis_id"] for row in scene["model_inventory"]["moved_panel_axes"]}
    require(moved_ids == {row["axis_id"] for row in review["moved_panel_axes"]}
            and moved_ids == {row["axis_id"] for row in geometry["panel_screws"]},
            "Current eight moved Hillman axes do not reconcile across frozen records")
    require(review["revision_id"] == REVISION_ID, "Current review report revision mismatch")
    require(Path(scene.get("revision_report_path", "")).name == Path(REVIEW).name,
            "Current scene references a different review report")
    require(scene["model_inventory"].get("electrical_replacements")
            == review.get("electrical_replacements"),
            "Current scene/review electrical replacement inventory mismatch")
    require(geometry["reviewed_repository_commit"] == REVIEWED_COMMIT,
            "Geometry snapshot reviewed-commit mismatch")
    require(sha256_file(ROOT / REVIEW) == scene["revision_report_sha256"],
            "Current scene report digest mismatch")
    manifest_path = Path(scene["baseline_manifest_path"])
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    require(sha256_file(manifest_path)
            == scene["baseline_manifest_sha256"], "Current scene manifest digest mismatch")
    require(counts["candidate_parts"] == 24 and counts["candidate_bores"] == 92,
            "Current block/bolt counts changed")
    require(counts["retained_frame_bolts"] == 12 and counts["panel_screw_axes_total"] == 66,
            "Current retained-bolt/Hillman counts changed")
    require(counts["fixed_panel_axes"] == 58 and counts["moved_panel_axes"] == 8,
            "Current Hillman fixed/moved counts changed")
    require(revision["candidate_blocks"] == counts["candidate_parts"]
            and revision["candidate_bolt_axes"] == counts["candidate_bores"]
            and revision["panel_kicker_screw_axes"] == counts["panel_screw_axes_total"]
            and revision["unchanged_panel_kicker_axes"] == counts["fixed_panel_axes"]
            and revision["previously_owner_directed_moved_axes"] == counts["moved_panel_axes"]
            and revision["starting_frame_bolts"] == counts["retained_frame_bolts"],
            "Lane manifest counts do not reconcile to current scene counts")
    require(candidate_access["geometry_revision_id"] == captured["geometry_revision_id"]
            == retained_access["geometry_revision_id"] == REVISION_ID,
            "Access/capture reports are not on the reviewed revision")
    require(receiver["revision_id"] == REVISION_ID, "Receiver report revision mismatch")

    block_ids = set(scene["model_inventory"]["candidate_parts"])
    moved_rows = {row["axis_id"]: row for row in scene["model_inventory"]["moved_panel_axes"]}
    axis_records, block_rows = make_axis_records(
        scene, candidate_access, captured, retained_access, receiver, moved_rows, block_ids
    )
    service_records, asset_pins = make_service_records(
        scene, review, parts, retained_access, candidate_access, led_reference,
        wiring_reference, topology
    )

    source_bindings = [source_binding(path, role) for path, role in STATIC_INPUTS]
    source_bindings.sort(key=lambda row: row["path"])
    active_axis_counts = {
        "candidate_bolt_stacks": 92,
        "retained_frame_bolt_stacks": 12,
        "hillman_panel_kicker_axes": 66,
    }
    service_counts = {"hold_tnut_corridors": 142, "modeled_leds": 132, "modeled_wire_segments": 131}
    artifact = {
        "schema": "mini_moonboard_step6_operation_coverage/v1",
        "status": "diagnostic_operation_coverage_only",
        "revision": {
            "development_candidate": DEVELOPMENT_CANDIDATE,
            "selected_candidate_authority_preserved": SELECTED_CANDIDATE,
            "revision_id": REVISION_ID,
            "reviewed_repository_commit": REVIEWED_COMMIT,
            "review_report_input_revision_id": review.get("input_revision_id"),
            "owner_review_status": revision.get("owner_review_status"),
            "owner_evaluation_pause_lifted": revision.get("joint_evaluation_pause_lifted"),
            "scene_revision_sha256": sha256_file(ROOT / SCENE),
            "review_report_sha256": sha256_file(ROOT / REVIEW),
            "lane_manifest_current_revision": revision,
            "scene_counts": counts,
            "geometry_snapshot_counts": geometry["counts"],
        },
        "counts": {
            "candidate_blocks": 24,
            "candidate_block_axis_link_count": sum(
                row["candidate_bolt_axis_count"] for row in block_rows
            ),
            **active_axis_counts,
            **service_counts,
            "operation_records": len(axis_records) + len(service_records),
            "candidate_block_grouping_rows": len(block_rows),
        },
        "release_flags": {
            key: scene.get(key)
            for key in (
                "candidate_accepted",
                "installation_proven",
                "complete_joint_acceptance",
                "capacity_established",
                "fabrication_released",
                "climbing_released",
            )
        },
        "ordinary_local_n_disposition": {
            "limit_mm": 139.7,
            "status": "unresolved",
            "station_by_station_extent_and_tool_envelope_assessed": False,
            "historical_local_n_results_used": False,
            "note": "This register has no current complete connector, installed-hardware, and tool-extents disposition.",
        },
        "operation_order_context": {
            "current_sequence_is_a_hypothesis_only": True,
            "forward_order": [
                "independently support and stage members and stacks",
                "assemble frame and recheck the 12 retained frame-bolt stacks",
                "place 24 candidate blocks and install 92 candidate bolt stacks",
                "install six panels/kickers using 66 separate Hillman axes",
                "feed the intact harness and install LEDs after panel placement",
            ],
            "reverse_order": [
                "support and capture the assembly; service lights and harness",
                "remove and stage panels/kickers",
                "remove candidate bolt stacks and blocks",
                "remove retained frame bolts and separate frame members",
            ],
            "accepted_operations": 0,
            "support_staging_and_within_family_order": "unresolved",
        },
        "candidate_block_coverage": block_rows,
        "axis_records": axis_records,
        "service_records": service_records,
        "service_context": {
            "tnut_corridor_scope": "142 modeled baseline T-nut assets joined to 142 temporary projection envelopes; current access source explicitly treats those envelopes as non-installed and excludes them globally.",
            "led_route_scope": "132 route labels joined to topology-only panel ownership; current G1/G2 checks are limited to nominal hole/body geometry.",
            "wire_route_scope": "131 modeled spans joined to topology-only owners; display-solid hits do not prove a flexible cable blocks an operation.",
            "current_review_wire_findings": [
                "Bottom rails cross ten modeled wire segments; the current review summary does not itemize those ten IDs here.",
                "The taller right central block crosses the F1-G1 modeled span.",
                "Current wire_073_G1_G2 replacement overlaps base_rail_bottom_right by 515.7566138961927 mm3 in the display-geometry check.",
                "Current wire_074_G2_G3 replacement has no checked intersection in that report; this is not physical cable clearance.",
                "Retained-bolt screen reports wire_010_A10_A11 and wire_130_K10_K11 intersections on four separate head-side bolt withdrawal paths.",
            ],
            "service_prerequisites_unresolved": [
                "actual LED, connector, harness and hold-bolt products/dimensions",
                "feed path, attachment points, slack, bend radius and connector handling",
                "physical capture/restraint and a reversible service state",
                "tolerance-aware clearance and handling workspace",
            ],
            "historical_service_geometry_or_28_body_104_axis_records_joined": False,
        },
        "source_bindings": source_bindings,
        "service_asset_pins": asset_pins,
        "claim_boundary": {
            "closes": [
                "A reproducible source-bound coverage inventory and per-operation evidence map for the current revision.",
                "Exact reconciliation of current 24 block IDs, 92 candidate axes, 12 separate retained stacks, 66 Hillman axes, and the 142/132/131 service inventories.",
            ],
            "does_not_close": [
                "real tool or hand access, matched delivered stack fit, tightening torque, or physical installation",
                "thread-compatible disengagement, loose-part capture, complete retrieval, or complete reverse transport",
                "independent support/load transfer, panel edge support, or service capture/restraint",
                "manufacturing or construction tolerances, complete wire/LED service, or physical fit",
                "ordinary 139.7 mm local-N disposition, mechanics, acceptance, fabrication release, or climbing release",
            ],
            "historical_data_policy": "No old 28-body/104-axis operation rows, local-N dispositions, or synthetic-wrench results are joined.",
            "geometry_policy": "No CAD model, geometry, solver input, or solver result is created or changed by this producer.",
        },
        "producer": {
            "path": OUT_DIR.relative_to(ROOT).as_posix() + "/produce.py",
            "sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    require(len(axis_records) == 170, "Expected 92 + 12 + 66 axis records")
    require(len(service_records) == 405, "Expected 142 + 132 + 131 service records")
    require(artifact["counts"]["operation_records"] == 575, "Unexpected operation-record count")
    return artifact


def make_readme(artifact: dict[str, Any], json_digest: str) -> str:
    return f"""# Step 6 operation-coverage attempt 01

Diagnostic register for `{REVISION_ID}` (reviewed repository identity
`{REVIEWED_COMMIT}`). The selected candidate remains
`{SELECTED_CANDIDATE}`; this is a separate development lane.

`operation-coverage.json` contains 575 joined operation records: 92 candidate bolt stacks,
12 retained frame-bolt stacks, 66 Hillman axes, 142 T-nut corridor rows, 132 LEDs and 131
modeled wire segments. A separate 24-entry grouping table assigns the 92 candidate axes to
their current blocks. The table records {artifact['counts']['candidate_block_axis_link_count']}
block-axis links because an axis can serve multiple block receivers. Input documents, the 405
service asset files, and the three embedded current electrical replacement meshes are pinned
by digest.

## What the register records

- Candidate and retained bolts keep install, turn, counterhold, retrieval, withdrawal and
  reverse-assembly statuses separate. Motion envelopes and current-revision wrench poses are
  proxies; the wrench profile is unselected. They do not establish real-tool access, physical
  fit, capture or support.
- The 66 Hillman rows preserve the 58 fixed and eight moved axes. Their current receiver
  envelope check clears finished receivers; driver access, embedment, support, and reversal
  remain unverified.
- T-nut rows join each modeled baseline asset to its separate provisional corridor envelope.
  The corridor envelopes were excluded from the retained access screen as non-installed
  projections. G6 and G12 findings remain unresolved hold-product envelope conflicts.
- LED and wire rows preserve route order and use WJ18 only for panel-ownership topology.
  The current G1/G2 hole checks are narrow nominal checks; service feeding, capture and
  restoration are not proven. Fixed display-solid overlaps do not prove a flexible cable is
  physically blocked.

The 139.7 mm ordinary local-N disposition remains unresolved. No historical 28-body/104-axis
records, local-N results, or synthetic-wrench results are used. This artifact closes source
reconciliation and coverage mapping only; it does not close Step 6 fit/use readiness, mechanics,
fabrication, or climbing release.

## Reproduce and verify

```sh
cd {OUT_DIR.relative_to(ROOT).as_posix()}
python3 produce.py --write
python3 produce.py --verify
```

Machine JSON SHA-256: `{json_digest}`.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write the JSON register and README")
    mode.add_argument("--verify", action="store_true", help="rebuild in memory and compare both files")
    args = parser.parse_args()
    try:
        artifact = build_artifact()
        output = json_bytes(artifact)
        digest = sha256_bytes(output)
        readme = make_readme(artifact, digest).encode()
        if args.verify:
            require(JSON_PATH.is_file() and JSON_PATH.read_bytes() == output,
                    "operation-coverage.json differs from current pinned inputs")
            require(README_PATH.is_file() and README_PATH.read_bytes() == readme,
                    "README.md differs from the regenerated source-bound summary")
            print(f"verified: {JSON_PATH.relative_to(ROOT)}")
            print(f"verified: {README_PATH.relative_to(ROOT)}")
            print(f"records: {artifact['counts']['operation_records']}; sha256: {digest}")
            return 0
        JSON_PATH.write_bytes(output)
        README_PATH.write_bytes(readme)
        print(f"wrote: {JSON_PATH.relative_to(ROOT)}")
        print(f"wrote: {README_PATH.relative_to(ROOT)}")
        print(f"records: {artifact['counts']['operation_records']}; sha256: {digest}")
        return 0
    except (OSError, KeyError, TypeError, ValueError) as error:
        print(f"step6 operation coverage: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
