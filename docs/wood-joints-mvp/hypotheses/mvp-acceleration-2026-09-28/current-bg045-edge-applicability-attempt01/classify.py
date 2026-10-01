#!/usr/bin/env python3
"""Repackage pinned BG045 force directions and edge geometry for a bounded review."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[5]
OUTPUT = HERE / "load-classification.json"
PINS_PATH = HERE / "source-pins.json"

REPORT_PATHS = {
    "a1-rear": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json",
    "a12-rear": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/corner-demand-report.json",
    "k12-rear": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pinned_json(path_text: str, expected_sha256: str) -> Any:
    path = ROOT / path_text
    actual = sha256(path)
    if actual != expected_sha256:
        raise ValueError(f"source digest changed: {path_text}: {actual}")
    return json.loads(path.read_text(encoding="utf-8"))


def sign(value: float, tolerance: float = 1e-9) -> str:
    if value > tolerance:
        return "+"
    if value < -tolerance:
        return "-"
    return "0"


def force_for_member(action: dict[str, Any], member: str) -> list[float]:
    if action.get("first") == member:
        value = action["force_on_first_xyz_n"]
    elif action.get("second") == member:
        value = action["force_on_second_xyz_n"]
    else:
        raise ValueError(f"member {member!r} is not an owner of {action.get('source_connection_name')}")
    return [float(component) for component in value]


def component_comparison(face: str, distance: float, loaded_4d: float) -> dict[str, Any]:
    return {
        "face": face,
        "source_envelope_center_to_face_distance_mm": distance,
        "distance_minus_conditional_4D_mm": round(distance - loaded_4d, 9),
        "interpretation": "component-face sensitivity only unless that face is established as the applicable loaded edge",
    }


def build() -> dict[str, Any]:
    pins = json.loads(PINS_PATH.read_text(encoding="utf-8"))
    report_meta = pins["case_demand_reports"]
    reports: dict[str, dict[str, Any]] = {}
    for case_id, path_text in REPORT_PATHS.items():
        report = load_pinned_json(path_text, report_meta[case_id]["sha256"])
        if report.get("case_id") != case_id:
            raise ValueError(f"wrong case identity in {path_text}")
        if not str(report.get("status", "")).startswith("PASS"):
            raise ValueError(f"case report is not in its recorded conditional-pass state: {case_id}")
        if report.get("actual_case_demand_usable_for_conditional_joint_checks") is not True:
            raise ValueError(f"case demand is not marked usable for conditional checks: {case_id}")
        increments = report.get("increments", [])
        if len(increments) != 7 or increments[-1].get("load_factor") != 1.0:
            raise ValueError(f"expected seven increments ending at load factor 1.0: {case_id}")
        reports[case_id] = report

    component_pin = pins["reviewed_component_sources"]["a1_a12_bg045_component_screen"]
    component_screen = load_pinned_json(component_pin["path"], component_pin["sha256"])
    k12_pin = pins["reviewed_component_sources"]["k12_bg045_component_screen"]
    k12_screen = load_pinned_json(k12_pin["path"], k12_pin["sha256"])
    if not all(
        all(gates.values())
        for gates in (component_screen["source_case_checks"]["a1-rear"]["gates"], component_screen["source_case_checks"]["a12-rear"]["gates"])
    ):
        raise ValueError("A1/A12 component-screen source-case gates did not pass")
    if k12_screen.get("status") != "PASS_SOURCE_BOUND_CONDITIONAL_COMPONENT_SCREEN_ONLY":
        raise ValueError("K12 component screen status changed")
    if k12_screen.get("joint_accepted") is not False:
        raise ValueError("K12 component screen no longer withholds joint acceptance")

    geometry_screen = component_screen["nds_edge_and_end_distance_conditional_comparator"]
    d_mm = float(geometry_screen["conditional_thresholds_mm"]["assumed_bolt_diameter"])
    loaded_4d_mm = float(geometry_screen["conditional_thresholds_mm"]["Table_12_5_1C_perpendicular_loaded_edge_4D"])
    unloaded_15d_mm = float(geometry_screen["conditional_thresholds_mm"]["Table_12_5_1C_perpendicular_unloaded_edge_1_5D"])
    if not math.isclose(d_mm, 6.35, abs_tol=1e-8) or not math.isclose(loaded_4d_mm, 25.4, abs_tol=1e-8):
        raise ValueError("conditional Table 12.5.1C scenario changed")

    frame_data = component_screen["member_frames_and_source_envelopes"]
    block_frame = frame_data["knee_outer_left_inner_frame_block"]
    header_frame = frame_data["base_header"]
    block_geometry: dict[str, dict[str, dict[str, Any]]] = {}
    header_component_geometry: dict[str, dict[str, dict[str, Any]]] = {}

    for case_id in ("a1-rear", "a12-rear"):
        block_geometry[case_id] = {}
        for row in geometry_screen["block_perpendicular_to_grain_loaded_edge_comparator"][case_id]:
            distance_map = row["all_four_center_to_face_distances_mm"]
            block_geometry[case_id][row["axis_id"]] = {
                "source_envelope_center_to_face_distances_mm": distance_map,
                "first_ray_face": row["axis_force_ray_first_face"]["first_face_on_force_ray"],
                "first_ray_face_normal_distance_mm": row["axis_force_ray_first_face"]["center_to_face_distance_measured_normal_to_face_mm"],
                "first_ray_travel_mm": row["axis_force_ray_first_face"]["ray_travel_to_face_mm"],
                "opposite_face_for_candidate_ray_pair": {
                    "+X": "-X", "-X": "+X", "+Y": "-Y", "-Y": "+Y"
                }[row["axis_force_ray_first_face"]["first_face_on_force_ray"]],
                "component_face_sensitivities": [
                    component_comparison(
                        item["face_selected_by_signed_component"],
                        float(item["source_envelope_center_to_face_distance_mm"]),
                        loaded_4d_mm,
                    )
                    for item in row["component_face_comparators"]
                ],
                "screen_classification": row["grain_relation"],
            }
        header_component_geometry[case_id] = {
            row["axis_id"]: {
                "crossgrain_component_face": row["candidate_loaded_edge_from_crossgrain_component"],
                "crossgrain_component_n": row["signed_header_crossgrain_force_component_n"],
                "source_envelope_center_to_component_face_mm": row["source_envelope_edge_distance_mm"],
                "distance_minus_conditional_4D_mm": round(row["source_envelope_edge_distance_mm"] - loaded_4d_mm, 9),
                "interpretation": row["screen"],
            }
            for row in geometry_screen["header_crossgrain_component_edge_sensitivity"][case_id]
        }

    k12_edge_rows = {
        row["axis_id"]: row
        for row in k12_screen["all_seven_increment_results"][-1]["BG045"]["bolts"]
    }
    block_geometry["k12-rear"] = {}
    header_component_geometry["k12-rear"] = {}
    for axis_id, row in k12_edge_rows.items():
        edge = row["block_directional_edge_geometry"]
        first_face = edge["force_ray_first_face"]["first_face_on_force_ray"]
        block_geometry["k12-rear"][axis_id] = {
            "source_envelope_center_to_face_distances_mm": edge["source_model_envelope_distances_mm"],
            "first_ray_face": first_face,
            "first_ray_face_normal_distance_mm": edge["force_ray_first_face"]["center_to_face_distance_measured_normal_to_face_mm"],
            "first_ray_travel_mm": edge["force_ray_first_face"]["ray_travel_to_face_mm"],
            "opposite_face_for_candidate_ray_pair": {
                "+X": "-X", "-X": "+X", "+Y": "-Y", "-Y": "+Y"
            }[first_face],
            "component_face_sensitivities": [
                component_comparison(
                    item["face_selected_by_signed_component"],
                    float(item["source_envelope_center_to_face_distance_mm"]),
                    loaded_4d_mm,
                )
                for item in edge["signed_component_face_comparators"]
            ],
            "screen_classification": "perpendicular_to_proposed_grain",
            "edge_selection_status": edge["edge_selection_status"],
        }
        header = row["header_signed_end_and_edge_geometry"]
        header_component_geometry["k12-rear"][axis_id] = {
            "crossgrain_component_face": header["crossgrain_component_face"],
            "crossgrain_component_n": header["crossgrain_force_component_N"],
            "source_envelope_center_to_component_face_mm": header["source_model_envelope_edge_distance_mm"],
            "distance_minus_conditional_4D_mm": round(header["source_model_envelope_edge_distance_mm"] - loaded_4d_mm, 9),
            "full_vector_table_12_5_1c_check": header["full_vector_Table_12_5_1C_check"],
            "interpretation": "signed crossgrain component only; the source screen says the full vector is oblique to proposed +X grain",
        }

    case_results = []
    for case_id, report in reports.items():
        axis_rows: dict[str, list[dict[str, Any]]] = {}
        for increment in report["increments"]:
            bg045 = increment["primary_physical_bolt_groups"]["BG045"]
            for bolt in bg045["bolts"]:
                actions = [a for a in bolt["actions"] if a.get("role") == "candidate_bolt_lateral_plane"]
                if len(actions) != 1:
                    raise ValueError(f"expected one lateral-plane action for {case_id}/{bolt.get('axis_id')}")
                action = actions[0]
                block = force_for_member(action, "knee_outer_left_inner_frame_block")
                header = force_for_member(action, "base_header")
                axis_rows.setdefault(bolt["axis_id"], []).append({
                    "load_factor": increment["load_factor"],
                    "force_on_block_xyz_n": block,
                    "force_on_header_xyz_n": header,
                    "block_xy_direction_signs": [sign(block[0]), sign(block[1])],
                    "header_xy_direction_signs": [sign(header[0]), sign(header[1])],
                })

        axis_summaries = []
        for axis_id, rows in axis_rows.items():
            if len(rows) != 7:
                raise ValueError(f"expected seven force rows for {case_id}/{axis_id}")
            final = rows[-1]
            block = final["force_on_block_xyz_n"]
            header = final["force_on_header_xyz_n"]
            if case_id in ("a1-rear", "a12-rear"):
                reviewed_row = next(
                    row for row in component_screen["per_axis_signed_actions_and_geometry"][case_id]
                    if row["axis_id"] == axis_id
                )
                expected_block = reviewed_row["physical_lateral_action_on_block_xyz_n"]
                expected_header = reviewed_row["physical_lateral_action_on_header_xyz_n"]
            else:
                reviewed_row = next(
                    row for row in k12_edge_rows.values() if row["axis_id"] == axis_id
                )
                expected_block = reviewed_row["physical_lateral_action_on_block_xyz_n"]
                expected_header = reviewed_row["physical_lateral_action_on_header_xyz_n"]
            if any(not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-6) for a, b in zip(block, expected_block)):
                raise ValueError(f"full-factor block force does not reproduce reviewed screen: {case_id}/{axis_id}")
            if any(not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-6) for a, b in zip(header, expected_header)):
                raise ValueError(f"full-factor header force does not reproduce reviewed screen: {case_id}/{axis_id}")
            hmag = math.sqrt(sum(value * value for value in header))
            angle = math.degrees(math.acos(min(1.0, abs(header[0]) / hmag))) if hmag else None
            stable_signs = {
                "block_xy": len({tuple(row["block_xy_direction_signs"]) for row in rows}) == 1,
                "header_xy": len({tuple(row["header_xy_direction_signs"]) for row in rows}) == 1,
            }
            if not all(stable_signs.values()):
                raise ValueError(f"force direction changes across increments: {case_id}/{axis_id}")
            axis_summaries.append({
                "axis_id": axis_id,
                "final_load_factor": final["load_factor"],
                "final_force_on_block_xyz_n": block,
                "final_force_on_header_xyz_n": header,
                "direction_signs_stable_over_seven_increments": stable_signs,
                "block_proposed_grain": "+Z",
                "block_lateral_grain_classification": "perpendicular to proposed grain, as screened; exported Z component is numerical residue only",
                "header_proposed_grain": "+X",
                "header_signed_parallel_component_x_n": header[0],
                "header_crossgrain_components_yz_n": header[1:],
                "header_acute_force_to_grain_angle_degrees": round(angle, 9) if angle is not None else None,
                "header_grain_classification": "mixed parallel and crossgrain action; no single Table 12.5.1C loading direction is selected here",
                "component_sign_is_not_member_tension_or_compression_classification": True,
                "block_edge_geometry": block_geometry[case_id][axis_id],
                "header_edge_component_sensitivity": header_component_geometry[case_id][axis_id],
            })
        case_results.append({
            "case_id": case_id,
            "case_report_path": REPORT_PATHS[case_id],
            "case_report_sha256": report_meta[case_id]["sha256"],
            "case_status": report["status"],
            "demand_scope": "conditional numerical demand only; no complete-joint acceptance",
            "load_direction_signs_stable_for_all_BG045_axes": all(
                all(summary["direction_signs_stable_over_seven_increments"].values()) for summary in axis_summaries
            ),
            "per_increment_signed_actions": [
                {
                    "load_factor": row["load_factor"],
                    "axis_id": axis_id,
                    "force_on_block_xyz_n": row["force_on_block_xyz_n"],
                    "force_on_header_xyz_n": row["force_on_header_xyz_n"],
                    "block_xy_direction_signs": row["block_xy_direction_signs"],
                    "header_xy_direction_signs": row["header_xy_direction_signs"],
                }
                for axis_id, rows in axis_rows.items()
                for row in rows
            ],
            "axis_summaries": axis_summaries,
        })

    return {
        "schema": "current_bg045_edge_applicability_load_classification/v1",
        "status": "PASS_SOURCE_PINNED_DIRECTION_AND_APPLICABILITY_BOUNDARY_ONLY",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": "Classify signed BG045 lateral actions in the three accepted rear numerical-demand cases and compare source-envelope edges with conditional NDS-2024 Table 12.5.1C values; no joint resistance or acceptance.",
        "conditional_scenario": {
            "bolt_diameter_mm": d_mm,
            "table_12_5_1c_perpendicular_loaded_edge_4d_mm": loaded_4d_mm,
            "table_12_5_1c_perpendicular_unloaded_edge_1_5d_mm": unloaded_15d_mm,
            "status": "conditional geometry comparator for the named 1/4-in scenario; delivered bolt diameter and finished member edges are unverified",
        },
        "member_and_fastener_axes": {
            "block_proposed_grain_global": [0.0, 0.0, 1.0],
            "header_proposed_grain_global": [1.0, 0.0, 0.0],
            "BG045_bolt_axis_global": [0.0, 0.0, 1.0],
            "block_source_envelope": {
                "x_edge_bounds_mm": block_frame["x_edge_bounds_mm"],
                "y_edge_bounds_mm": block_frame["y_edge_bounds_mm"],
                "qualification": block_frame["qualification"],
            },
            "header_source_envelope": {
                "x_end_bounds_mm": header_frame["x_end_bounds_mm"],
                "y_edge_bounds_mm": header_frame["y_edge_bounds_mm"],
                "qualification": header_frame["qualification"],
            },
            "block_directional_result": "All source-screened lateral block actions lie in XY and are perpendicular to proposed +Z grain. Table 12.5.1C's perpendicular-to-grain categories are conditionally relevant; the NDS definition still leaves the face-selection convention for an oblique direction into a multi-face end-grain-axis block unresolved.",
            "header_directional_result": "All source-screened lateral header actions are in XY, while the proposed header grain is +X. They contain parallel-X and crossgrain-Y components, so the full header action is mixed to grain. The isolated Y-face results below are component sensitivities, not full-vector Table 12.5.1C determinations.",
        },
        "case_results": case_results,
        "source_pins": {
            "case_reports": report_meta,
            "a1_a12_component_screen": component_pin,
            "k12_component_screen": k12_pin,
        },
        "execution_boundary": {
            "native_solver_run": False,
            "CAD_query_or_rebuild": False,
            "geometry_or_axis_files_modified": False,
            "92_axis_inventory_changed": False,
            "capacity_or_design_DCR_calculated": False,
            "complete_joint_accepted": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    expected = (json.dumps(build(), ensure_ascii=False, indent=2) + "\n").encode()
    if args.write:
        OUTPUT.write_bytes(expected)
        print(f"WROTE {OUTPUT.relative_to(ROOT)} sha256={hashlib.sha256(expected).hexdigest()}")
        return 0
    actual = OUTPUT.read_bytes()
    if actual != expected:
        print("FAIL_SOURCE_REPRODUCTION_MISMATCH")
        return 1
    print(f"PASS_SOURCE_REPRODUCIBLE {OUTPUT.relative_to(ROOT)} sha256={hashlib.sha256(actual).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
