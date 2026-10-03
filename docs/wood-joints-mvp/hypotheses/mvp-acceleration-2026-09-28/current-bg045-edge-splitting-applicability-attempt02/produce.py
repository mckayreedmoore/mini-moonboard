#!/usr/bin/env python3
"""Verify source-bound BG045 geometry/actions and emit conditional NDS checks."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
DOCS = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
PINS = HERE / "source-pins.json"
OUT = HERE / "results.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def check_hash(path: Path, expected: str, label: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"{label} SHA-256 mismatch: {actual} != {expected}")


def close_vec(a: list[float], b: list[float], tol: float = 1e-6) -> bool:
    return len(a) == len(b) and all(abs(float(x) - float(y)) <= tol for x, y in zip(a, b))


def face_name(axis: str, sign: int) -> str:
    return ("+" if sign > 0 else "-") + axis.upper()


def directed_hit(
    point: list[float], force: list[float], bounds: dict[str, list[float]]
) -> dict[str, Any]:
    candidates: list[tuple[float, str, float]] = []
    for idx, axis in enumerate(("x", "y")):
        q = float(force[idx])
        if abs(q) < 1e-10:
            continue
        sign = 1 if q > 0 else -1
        bound = float(bounds[axis][1] if sign > 0 else bounds[axis][0])
        distance = abs(bound - float(point[idx]))
        travel = distance / abs(q)
        candidates.append((travel, face_name(axis, sign), distance))
    if not candidates:
        raise ValueError("No nonzero in-plane force component for ray")
    travel, face, normal_distance = min(candidates)
    axis = face[1:].lower()
    sign = 1 if face[0] == "+" else -1
    opposite = face_name(axis, -sign)
    opposite_bound = float(bounds[axis][0] if sign > 0 else bounds[axis][1])
    opposite_distance = abs(opposite_bound - float(point[0 if axis == "x" else 1]))
    return {
        "first_intersected_source_envelope_face": face,
        "first_intersection_travel_parameter_mm_per_n": travel,
        "first_intersection_normal_distance_mm": normal_distance,
        "opposite_face": opposite,
        "opposite_face_distance_mm": opposite_distance,
    }


def edge_distance(point: list[float], component: float, bounds: list[float]) -> tuple[str, float]:
    if abs(component) < 1e-10:
        return "none", 0.0
    if component > 0:
        return "+Y", float(bounds[1]) - float(point[1])
    return "-Y", float(point[1]) - float(bounds[0])


def model_geometry(model: dict[str, Any], name: str) -> dict[str, Any]:
    record = model["body_geometry"][name]["geometry_record"]
    desc = record["source_descriptor"]
    return {
        "member": name,
        "grain_global_xyz": desc["grain_global_xyz"],
        "axis_global_xyz": desc["axis"],
        "start_global_xyz_mm": desc["start"],
        "end_global_xyz_mm": desc["end"],
        "length_mm": desc["length_mm"],
        "depth_mm": desc["depth_mm"],
        "width_mm": desc["width_mm"],
        "transverse_status": desc["transverse_status"],
        "step_path": desc["step_path"],
        "step_sha256": desc["step_sha256"],
        "material_frame_map": desc["material_frame_map"],
        "material_frame_map_sha256": desc["material_frame_map_sha256"],
        "actual_to_rectangular_volume_ratio": desc["actual_to_rectangular_volume_ratio"],
        "cylindrical_face_count": desc["cylindrical_face_count"],
    }


def main() -> dict[str, Any]:
    pins = read_json(PINS)
    for rel, expected in pins["input_files"].items():
        check_hash(ROOT / rel, expected, rel)

    edge = read_json(DOCS / "current-bg045-edge-applicability-attempt01/load-classification.json")
    edge_pins = read_json(DOCS / "current-bg045-edge-applicability-attempt01/source-pins.json")
    register = read_json(DOCS / "current-corner-complete-resistance-register-attempt01/signed-demands.json")
    section = read_json(DOCS / "current-bg045-header-transfer-section-demands-attempt01/section-demands.json")
    section_pins = read_json(DOCS / "current-bg045-header-transfer-section-demands-attempt01/source-pins.json")
    section_parent = read_json(DOCS / "current-bg045-header-transfer-section-demands-attempt01/parent-verification.json")
    if edge_pins["sources"]["nds_2024_chapter_12"]["sha256"] != pins["official_sources"]["nds_2024_chapter_12"]["sha256"]:
        raise ValueError("Official Chapter 12 digest no longer matches the reviewed source packet")

    # The source pins within each accepted producer must agree with the new packet pins.
    report_hashes = {
        rel: digest
        for rel, digest in register["source_pins"].items()
        if rel.endswith("corner-demand-report.json")
    }
    if set(pins["accepted_case_models"]) != {"a1-rear", "a12-rear", "k12-rear"}:
        raise ValueError("Accepted rear case set changed")
    if len(report_hashes) != 3:
        raise ValueError("Complete-corner register does not pin exactly three accepted reports")
    report_path_by_case = {
        "a1-rear": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json",
        "a12-rear": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/corner-demand-report.json",
        "k12-rear": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json",
    }
    for case_id, rel in report_path_by_case.items():
        if report_hashes.get(rel) != pins["input_files"].get(rel):
            raise ValueError(f"Case report pin absent from complete-corner register: {case_id}")
    if any(section_pins["source_sha256"].get(rel) != digest for rel, digest in register["source_pins"].items()):
        raise ValueError("Header section and complete-corner report pins no longer agree")
    if not (
        section_parent["status"] == "PASS_PARENT_NATIVE_POINT_FORCE_HEADER_SECTION_RECONSTRUCTION"
        and section_parent["case_count"] == 3
        and section_parent["one_sided_segment_wrench_comparisons"] == 84
        and section_parent["splitting_demand_or_resistance_established"] is False
        and section_parent["joint_accepted"] is False
    ):
        raise ValueError("Header section independent verification boundary changed")

    # Read and compare all three source models for the two receiver body geometry records.
    models: dict[str, dict[str, Any]] = {}
    geom_by_case: dict[str, dict[str, Any]] = {}
    for case_id, rel in pins["accepted_case_models"].items():
        model_path = ROOT / rel
        check_hash(model_path, pins["input_files"][rel], f"{case_id} model")
        models[case_id] = read_json(model_path)
        geom_by_case[case_id] = {
            "base_header": model_geometry(models[case_id], "base_header"),
            "block": model_geometry(models[case_id], "knee_outer_left_inner_frame_block"),
        }
    reference_geometry = geom_by_case["a12-rear"]
    for case_id, geometry in geom_by_case.items():
        for member in ("base_header", "block"):
            for key in ("grain_global_xyz", "axis_global_xyz", "start_global_xyz_mm", "end_global_xyz_mm", "length_mm", "depth_mm", "width_mm", "step_sha256"):
                if geometry[member][key] != reference_geometry[member][key]:
                    raise ValueError(f"{case_id} {member} geometry differs from A12 at {key}")
            desc = geometry[member]
            for path_key, hash_key in (("step_path", "step_sha256"), ("material_frame_map", "material_frame_map_sha256")):
                if pins["input_files"].get(desc[path_key]) != desc[hash_key]:
                    raise ValueError(f"{case_id} {member} source descriptor does not match pinned {path_key}")
    block_geom = reference_geometry["block"]
    header_geom = reference_geometry["base_header"]
    if block_geom["grain_global_xyz"] != [0.0, 0.0, 1.0] or header_geom["grain_global_xyz"] != [1.0, 0.0, 0.0]:
        raise ValueError("Source-proposed grain directions changed")

    # Cross-check six factor-one BG045 signed force pairs against the accepted complete register.
    reg_final: dict[tuple[str, str], dict[str, Any]] = {}
    for row in register["rows"]:
        if row.get("group") == "BG045" and abs(float(row.get("load_factor", 0)) - 1.0) < 1e-12:
            key = (row["case_id"], row["axis_id"])
            if key in reg_final:
                raise ValueError(f"duplicate register state {key}")
            reg_final[key] = row
    if len(reg_final) != 6:
        raise ValueError(f"Expected six BG045 factor-one actions; found {len(reg_final)}")
    modeled_bolt_axis_z_spans = set()
    for item in reg_final.values():
        tie = item["simultaneous_outer_tie"]
        modeled_bolt_axis_z_spans.add(tuple(sorted((round(float(tie["first_point_global_xyz_mm"][2]), 6), round(float(tie["second_point_global_xyz_mm"][2]), 6)))))
    if len(modeled_bolt_axis_z_spans) != 1:
        raise ValueError(f"BG045 modeled bolt-axis spans are not common: {modeled_bolt_axis_z_spans}")
    axis_z_start, axis_z_end = next(iter(modeled_bolt_axis_z_spans))
    modeled_axis_midpoint_z = (axis_z_start + axis_z_end) / 2.0

    case_rows: list[dict[str, Any]] = []
    for case_result in edge["case_results"]:
        case_id = case_result["case_id"]
        axis_results: list[dict[str, Any]] = []
        block_sum = [0.0, 0.0]
        header_sum = [0.0, 0.0]
        block_tie_sum = [0.0, 0.0, 0.0]
        header_tie_sum = [0.0, 0.0, 0.0]
        final_states = [r for r in case_result["per_increment_signed_actions"] if abs(float(r["load_factor"]) - 1.0) < 1e-12]
        if len(final_states) != 2:
            raise ValueError(f"Expected two factor-one actions for {case_id}")
        for action in final_states:
            axis_id = action["axis_id"]
            row = reg_final[(case_id, axis_id)]
            boundary = row["both_same_bolt_plane_actions"][0]
            if boundary["first"] == "base_header":
                reg_header = boundary["force_on_first_xyz_n"]
                reg_block = boundary["force_on_second_xyz_n"]
                point = boundary["first_point_global_xyz_mm"]
            elif boundary["second"] == "base_header":
                reg_header = boundary["force_on_second_xyz_n"]
                reg_block = boundary["force_on_first_xyz_n"]
                point = boundary["second_point_global_xyz_mm"]
            else:
                raise ValueError(f"BG045 boundary does not contain base_header: {case_id}/{axis_id}")
            f_block = [float(v) for v in action["force_on_block_xyz_n"]]
            f_header = [float(v) for v in action["force_on_header_xyz_n"]]
            if not close_vec(f_block, reg_block) or not close_vec(f_header, reg_header):
                raise ValueError(f"Classifier/register forces differ for {case_id}/{axis_id}")
            if not close_vec([f_block[i] + f_header[i] for i in range(3)], [0.0, 0.0, 0.0]):
                raise ValueError(f"BG045 receiver actions do not balance for {case_id}/{axis_id}")
            # Point/axis center must match the named two BG045 stations in the source report.
            if not close_vec([float(v) for v in point], [float(v) for v in row["point_global_xyz_mm"]]):
                raise ValueError(f"Register point mismatch for {case_id}/{axis_id}")
            block_sum[0] += f_block[0]
            block_sum[1] += f_block[1]
            header_sum[0] += f_header[0]
            header_sum[1] += f_header[1]

            tie = row["simultaneous_outer_tie"]
            if tie["first"] == "base_header":
                tie_header = [float(v) for v in tie["force_on_first_xyz_n"]]
                tie_block = [float(v) for v in tie["force_on_second_xyz_n"]]
            elif tie["second"] == "base_header":
                tie_header = [float(v) for v in tie["force_on_second_xyz_n"]]
                tie_block = [float(v) for v in tie["force_on_first_xyz_n"]]
            else:
                raise ValueError(f"BG045 tie action does not contain base_header: {case_id}/{axis_id}")
            if not close_vec([tie_header[i] + tie_block[i] for i in range(3)], [0.0, 0.0, 0.0]):
                raise ValueError(f"BG045 simultaneous bolt-axis tie actions do not balance for {case_id}/{axis_id}")
            for i in range(3):
                header_tie_sum[i] += tie_header[i]
                block_tie_sum[i] += tie_block[i]

            block_bounds = {
                "x": [block_geom["start_global_xyz_mm"][0] - block_geom["width_mm"] / 2,
                      block_geom["start_global_xyz_mm"][0] + block_geom["width_mm"] / 2],
                "y": [block_geom["start_global_xyz_mm"][1] - block_geom["depth_mm"] / 2,
                      block_geom["start_global_xyz_mm"][1] + block_geom["depth_mm"] / 2],
            }
            # Header section_u=Y and section_v=Z. Its source envelope is centered on the member axis.
            header_bounds = {
                "x": [header_geom["start_global_xyz_mm"][0], header_geom["end_global_xyz_mm"][0]],
                "y": [header_geom["start_global_xyz_mm"][1] - header_geom["width_mm"] / 2,
                      header_geom["start_global_xyz_mm"][1] + header_geom["width_mm"] / 2],
            }
            block_hit = directed_hit(point, f_block, block_bounds)
            header_hit = directed_hit(point, f_header, header_bounds)
            y_face, y_edge = edge_distance(point, f_header[1], header_bounds["y"])
            x_end_face = "+X" if f_header[0] > 0 else "-X"
            x_end_distance = (header_bounds["x"][1] - point[0]) if f_header[0] > 0 else (point[0] - header_bounds["x"][0])
            grain_angle = math.degrees(math.atan2(abs(f_header[1]), abs(f_header[0])))
            axis_results.append({
                "axis_id": axis_id,
                "point_global_xyz_mm": [round(float(v), 6) for v in point],
                "load_factor": 1.0,
                "block_force_xyz_N": [round(v, 6) for v in f_block],
                "block_full_action_vs_grain": "perpendicular; block proposed grain +Z and action is XY",
                "block_source_envelope_direction_ray": block_hit,
                "block_face_component_sensitivities": {
                    face: round(value, 6)
                    for face, value in {
                        "-X": point[0] - block_bounds["x"][0],
                        "+X": block_bounds["x"][1] - point[0],
                        "-Y": point[1] - block_bounds["y"][0],
                        "+Y": block_bounds["y"][1] - point[1],
                    }.items()
                },
                "header_force_xyz_N": [round(v, 6) for v in f_header],
                "header_full_action_vs_grain": "mixed; nonzero X parallel and Y perpendicular components relative to proposed +X grain",
                "header_acute_angle_to_grain_deg": round(grain_angle, 6),
                "header_signed_parallel_X_component_N": round(f_header[0], 6),
                "header_signed_crossgrain_Y_component_N": round(f_header[1], 6),
                "header_source_envelope_direction_ray_context_only": header_hit,
                "header_Y_component_edge_face": y_face,
                "header_Y_component_edge_distance_mm": round(y_edge, 6),
                "header_Y_component_distance_minus_conditional_4D_mm": round(y_edge - 4 * pins["conditional_scenario"]["bolt_diameter_mm"], 6),
                "header_signed_X_end_face_and_distance_mm": {"face": x_end_face, "distance_mm": round(x_end_distance, 6)},
                "header_X_component_conditional_end_distance_context": "X faces are member ends (parallel to header grain), not Table 12.5.1C edges; this component projection is not a full mixed-grain Table 12.5.1A check.",
                "simultaneous_outer_seat_bolt_axis_tie_force_on_header_xyz_N": [round(v, 6) for v in tie_header],
                "simultaneous_outer_seat_bolt_axis_tie_force_on_block_xyz_N": [round(v, 6) for v in tie_block],
                "modeled_bolt_axis_tie_endpoints_global_xyz_mm": {
                    "first": [round(float(v), 6) for v in tie["first_point_global_xyz_mm"]],
                    "second": [round(float(v), 6) for v in tie["second_point_global_xyz_mm"]],
                },
                "lateral_action_angle_to_bolt_axis_deg": 90.0,
            })
        case_rows.append({
            "case_id": case_id,
            "action_provenance": "accepted numerical demand report only; no joint acceptance",
            "axis_direction_stable_over_all_accepted_increments": all(
                r["direction_signs_stable_over_seven_increments"]["block_xy"]
                and r["direction_signs_stable_over_seven_increments"]["header_xy"]
                for r in case_result["axis_summaries"]
            ),
            "axis_actions": axis_results,
            "simultaneous_two_axis_group_resultants_XY_N_descriptive_only": {
                "on_block": [round(v, 6) for v in block_sum],
                "on_header": [round(v, 6) for v in header_sum],
                "simultaneous_outer_seat_bolt_axis_tie_resultants_xyz_N": {
                    "on_header": [round(v, 6) for v in header_tie_sum],
                    "on_block": [round(v, 6) for v in block_tie_sum],
                },
                "header_acute_angle_to_grain_deg": round(math.degrees(math.atan2(abs(header_sum[1]), abs(header_sum[0]))), 6),
                "axis_pitch_line_global": "Y",
                "axis_pitch_line_acute_angle_to_group_resultant_deg": {
                    "on_block": round(abs(90.0 - math.degrees(math.atan2(abs(block_sum[1]), abs(block_sum[0])))), 6),
                    "on_header": round(abs(90.0 - math.degrees(math.atan2(abs(header_sum[1]), abs(header_sum[0])))), 6),
                },
            },
        })

    # Header transfer sections are all-body closures, not local splitting stresses.
    section_rows: list[dict[str, Any]] = []
    for row in section["per_increment_header_sections"]:
        if abs(float(row["load_factor"]) - 1.0) < 1e-12:
            action = row["section_at_transfer_station"]["one_sided_sections"]["immediately_after_transfer"]["left_segment_material_action"]
            section_rows.append({
                "case_id": row["case_id"],
                "load_factor": 1.0,
                "header_section_at_x_mm": -1085.85,
                "side": "left segment immediately after BG045 transfer station",
                "force_xyz_N": [round(float(v), 6) for v in action["force_xyz_n"]],
                "normal_plus_X_N": round(float(action["N_global_plus_X_on_segment_n"]), 6),
                "shear_YZ_N": [round(float(v), 6) for v in action["V_global_YZ_on_segment_xyz_n"][1:]],
                "bending_My_Mz_Nmm": [round(float(v), 6) for v in action["bending_Myz_nmm"]],
                "torsion_Mx_Nmm": round(float(action["torsion_Mx_nmm"]), 6),
                "interpretation": "member-scale resultant after simultaneous tie, lateral, contact, screw and source-discrete gravity actions; not local splitting demand",
            })

    d = float(pins["conditional_scenario"]["bolt_diameter_mm"])
    spacing = abs(float(case_rows[0]["axis_actions"][0]["point_global_xyz_mm"][1]) - float(case_rows[0]["axis_actions"][1]["point_global_xyz_mm"][1]))
    ell_main = float(block_geom["length_mm"])
    ell_side = float(header_geom["depth_mm"])
    ell_over_d = min(ell_main, ell_side) / d
    edge_rules = {
        "conditional_scenario": {
            "bolt_diameter_mm": d,
            "D_at_least_1_4_in": abs(d - 6.35) < 1e-9,
            "4D_mm": 4 * d,
            "1_5D_mm": 1.5 * d,
            "3D_mm": 3 * d,
            "5D_mm": 5 * d,
            "5_in_mm": 127.0,
            "source_axis_pitch_Y_mm": spacing,
            "pitch_over_D": spacing / d,
            "modeled_fastener_length_main_member_mm": ell_main,
            "modeled_fastener_length_side_member_mm": ell_side,
            "conditional_l_over_D_less_of_main_and_side": ell_over_d,
            "qualification": "D=1/4 in and modeled wood lengths; delivered diameter, bearing lengths, actual role and finished profiles are not observed",
        },
        "conditional_table_screens": {
            "table_12_5_1A_end_distances": {
                "softwood_tension_Cdelta_1_comparator_mm": 7 * d,
                "compression_Cdelta_1_comparator_mm": 4 * d,
                "nearest_source_header_X_end_mm": min(
                    float(row["header_signed_X_end_face_and_distance_mm"]["distance_mm"])
                    for case in case_rows for row in case["axis_actions"]
                ),
                "conditional_block_perpendicular_grain_minima_mm": {"minimum_Cdelta_0_5": 2 * d, "minimum_Cdelta_1_0": 4 * d},
                "modeled_outer_seat_axis_z_endpoints_mm": [axis_z_start, axis_z_end],
                "block_modeled_full_axis_midpoint_z_mm": round(modeled_axis_midpoint_z, 6),
                "block_source_cut_end_distances_from_that_midpoint_mm": [round(abs(modeled_axis_midpoint_z - float(block_geom["start_global_xyz_mm"][2])), 6), round(abs(float(block_geom["end_global_xyz_mm"][2]) - modeled_axis_midpoint_z), 6)],
                "block_center_mapping_limit": "These are conditional source-axis midpoint projections from modeled outer-seat tie endpoints; NDS §12.1.2.2 calls for the center of the physical bolt, and the model axis/tie span is not an observed delivered bolt.",
                "finding": "The header's nearest X end projection is 133.35 mm, greater than the 7D softwood-tension and 4D compression comparators in the named D scenario, but its full action is mixed and the parallel component alone does not establish Table A compliance. For the block, a modeled-axis midpoint sensitivity gives 50.45/88.55 mm against a 25.4 mm perpendicular-grain Cdelta=1 comparator; this is not a final end-distance check because the delivered bolt center/profile is unknown.",
            },
            "table_12_5_1B_within_row_spacing": {
                "minimum_spacing_mm": 3 * d,
                "parallel_to_grain_Cdelta_1_mm": 4 * d,
                "perpendicular_to_grain_Cdelta_1_rule": "required spacing for attached members",
                "axis_pitch_mm": spacing,
                "finding": "The 93.35 mm source center pitch exceeds the numeric 3D floor and 4D parallel comparator, but it is not by itself an applicable Table B row check. NDS §12.1.2.4 defines a row as at least two fasteners aligned with the direction of load; the two axes lie along Y while the group resultants are oblique to that line by 13.80° (A1), 80.09° (A12), and 84.08° (K12). The Cdelta=1 perpendicular branch also depends on the attached-member category.",
            },
            "table_12_5_1C_edge_distance": {
                "block_branch": "perpendicular-to-grain category is conditionally applicable to all XY block actions; loaded edge 4D and opposite unloaded edge 1.5D, provided the action-to-edge interpretation is resolved",
                "header_branch": "full action is oblique to proposed +X grain; no 2024 table branch for that mixed angle, so individual Y component distances are not full Table C checks",
                "parallel_grain_Cdelta_1_edge_mm_if_pure_parallel": 1.5 * d,
                "parallel_grain_edge_rule_if_l_over_D_gt_6": "greater of 1.5D and one-half the spacing between rows",
            },
            "table_12_5_1D_between_rows": {
                "perpendicular_to_grain_minimum_if_l_over_D_at_least_6_mm": 5 * d,
                "parallel_to_grain_minimum_mm": 1.5 * d,
                "source_two_axis_pitch_mm": spacing,
                "finding": "At l/D=6 the conditional 5D perpendicular comparator is 31.75 mm and 1.5D parallel comparator is 9.525 mm; the 93.35 mm pitch exceeds both. The accepted load vectors do not show two or more fasteners aligned with the load direction, so the pair pitch does not establish Table D between-row applicability or compliance.",
            },
            "table_12_5_1_3_outermost_perpendicular_distance": {
                "conditional_sawn_lumber_maximum_mm": 127.0,
                "source_pair_distance_mm": spacing,
                "margin_to_5_in_mm": 127.0 - spacing,
                "finding": "The BG045 pair alone is 93.35 mm across Y, below the conditional 127 mm sawn-member value, but whole-member outermost fasteners and sawn-versus-glulam product category are not established; no whole-member check is claimed.",
            },
        },
    }
    return {
        "schema": "current_bg045_edge_splitting_applicability/v1",
        "status": "CONDITIONAL_EDGE_AND_GEOMETRY_DISPOSITION_COMPLETE_SPLITTING_CAPACITY_UNRESOLVED",
        "scope": "BG045 only; source-proposed grain and source envelope; three accepted rear numerical demand cases; no axis, geometry, frozen input, native, or resistance edits",
        "source_geometry": {
            "case_models_have_matching_header_and_block_source_geometry": True,
            "receiver_geometry_by_case": geom_by_case,
            "header_source_envelope_Y_mm": [round(float(header_geom["start_global_xyz_mm"][1] - header_geom["width_mm"] / 2), 6), round(float(header_geom["start_global_xyz_mm"][1] + header_geom["width_mm"] / 2), 6)],
            "block_source_envelope_X_mm": [round(float(block_geom["start_global_xyz_mm"][0] - block_geom["width_mm"] / 2), 6), round(float(block_geom["start_global_xyz_mm"][0] + block_geom["width_mm"] / 2), 6)],
            "block_source_envelope_Y_mm": [round(float(block_geom["start_global_xyz_mm"][1] - block_geom["depth_mm"] / 2), 6), round(float(block_geom["start_global_xyz_mm"][1] + block_geom["depth_mm"] / 2), 6)],
            "receiver_profile_limit": "Pinned source STEP identities are recorded, but the edge distances here are rectangular source-envelope distances. No BG045 finished-profile ray query, physical cut, bore, tolerance, actual grain or delivered bolt is asserted.",
        },
        "orientation": {
            "block_proposed_grain_global": block_geom["grain_global_xyz"],
            "header_proposed_grain_global": header_geom["grain_global_xyz"],
            "bolt_axis_global": [0.0, 0.0, 1.0],
            "block_action_class": "all three accepted BG045 lateral vectors are XY, perpendicular to proposed +Z block grain",
            "header_action_class": "all header lateral vectors have nonzero X and Y; mixed to proposed +X grain",
            "bolt_axis_shear_area_clause": "NDS §12.5.1.2(b) concerns loading at an angle to the fastener/bolt axis. BG045 lateral vectors lie in XY and bolt axes are +Z, so this is 90-degree lateral loading to the fastener; the header's grain obliquity is a separate classification.",
            "block_end_grain_factor_scope": "Conditional NDS §12.5.2.2 Ceg=0.67 reference lateral-value adjustment may fit the source-proposed block main-member/end-grain orientation; it does not waive Table 12.5.1 detail requirements and is not a splitting resistance.",
            "source_grain_is_not_inspected_stock_grain": True,
        },
        "conditional_table_distance_screen": edge_rules,
        "accepted_signed_actions_full_factor_one": case_rows,
        "header_transfer_section_resultants_full_factor_one": section_rows,
        "interpretation_and_stop": {
            "block_edge": "NDS-2024 Table 12.5.1C is the perpendicular-to-grain branch for the block under the named D=6.35 mm scenario. §12.1.2.1 defines loaded edge by the direction in which the fastener acts and the opposite edge as unloaded. A1-rear axis 2 points +X/-Y; its full ray in the rectangular source envelope first intersects -Y at 20.0 mm. Under that direction-facing-edge interpretation the conditional 4D comparison is short 5.4 mm; the opposite +Y face is 113.35 mm and exceeds 1.5D. This is a source-envelope conditional comparison, not a physical finding or approved axis shift.",
            "other_block_edges": "A12-rear and K12-rear axis 1 have a +Y component toward a 20.0 mm face but their full source-envelope rays first reach +X at 44.45 mm. The 20.0 mm numbers remain component sensitivities; requiring 4D at both cross-grain faces is not an NDS Table C rule. Axis-specific action signs reverse between the accepted cases, so loaded edge must follow each signed receiver force.",
            "header_edge": "All six full header vectors are oblique to +X grain (acute angles 1.19 to 74.16 degrees per bolt). Official 2024 Table 12.5.1C supplies parallel- and perpendicular-to-grain rows, not an oblique interpolation. The two 20.0 mm -Y component distances (A12 axis 2 and K12 axis 2) and A1 axis-1 26.35 mm +Y component are not full-vector NDS edge pass/fail findings. Official 2018 Commentary p.264 says NDS 12.5.1 has no specific edge guidance at load angles other than 0/90 degrees and no reduced-edge geometry factor; this is historical commentary, not claimed as 2024 Commentary wording.",
            "end_and_row": "Table 12.5.1A applies a 2D minimum and 4D Cdelta=1 perpendicular-to-grain end-distance branch to the block under the proposed +Z grain classification. Header end-distance measurement runs along +X to square-cut member ends; its 133.35 mm nearest X projection exceeds the conditional 7D softwood-tension and 4D compression comparators, but the full action is mixed and the X component alone does not establish Table A compliance. The block model represents bolt axis endpoints at z=238.9..416.0 mm and member cut ends z=277/416; the axis-span midpoint sensitivity gives 50.45/88.55 mm against 4D=25.4 mm, only if that analysis span midpoint is the physical bolt center. Table 12.1.2.2 requires actual bolt-center-to-square-cut-end measurement. The 93.35 mm Y pitch is not by itself a Table 12.5.1B row check: §12.1.2.4 defines a row as at least two fasteners aligned with the direction of load, while group resultants are oblique to the Y pitch line in all three cases. The same unresolved layout does not establish two rows for Table 12.5.1D. Pair pitch is below the conditional 5-in source-lumber outermost-fastener maximum, but other header fasteners and product class remain unresolved.",
            "splitting": "NDS §12.5.1.3/Table 12.5.1C footnote 2 addresses heavy/medium concentrated loads suspended below the neutral axis of a single sawn-lumber or glulam beam and requires mechanical or equivalent reinforcement for tension perpendicular to grain. The model header geometric section center is z=257.95 mm; outer-seat tie reactions act at z=238.9 mm, 19.05 mm below that center. The geometric center is not a verified material neutral axis for the finished, perforated member. Full-factor-one group tie resultants on the header are +Z 107.967338 N (A1), 139.224710 N (A12), and 38.096890 N (K12). This is source action relevant to a possible footnote trigger, but the report does not establish the NDS heavy/medium load class, actual beam/product status, or local tension-perpendicular transfer field. §§3.8.2/11.1.3 require avoiding or appropriately engineering perpendicular-to-grain tension/eccentric-connection effects; they provide no general BG045 splitting-resistance equation. Header section wrenches close and provide member-scale actions, not local tension-perpendicular stress/strain or an admissible split plane.",
            "net_section_and_group": "Official NDS-2024 Appendix E describes a method for closely spaced fastener groups loaded parallel to grain; E.2/E.3 use adjusted parallel-to-grain Ft/Fv and defined net/critical areas for net-section tension and row tear-out. The block BG045 lateral demand is perpendicular-to-grain; header vectors are all mixed, not pure parallel. No NDS interaction rule authorizes checking only Fx while omitting simultaneous Fy, bolt-axis tie, other contacts, or eccentricity. The signed actions and header section resultants support member-level reporting, but the actual hole/cut profile, adjusted material values, row topology and a mechanism-compatible local force-transfer model remain missing. No net-section, shear-out, group DCR, splitting demand, or splitting capacity is computed.",
            "current_errata": "AWC March 2026 errata was checked: it updates connection shear references to §3.4.4.1 and retains §11.1.2's mechanics/Appendix E route; no reviewed change alters the Table 12.5.1C distance values.",
            "proposal_status": "The existing +5.4 mm axis-2-only comparison is not approved and no one of the reviewed 92 axes is changed. Under the source-envelope first-hit interpretation, it reaches exactly 25.4 mm for the A1-rear block axis-2 -Y edge only; NDS does not state a first-hit face-selection rule for this oblique multi-face end-grain block action. It does not settle the unqueried finished BRep profile, mixed-grain header actions, other case directions, row/end-distance assignment, or splitting method.",
            "missing_inputs": [
                "Delivered bolt diameter and actual wood bearing/embedment lengths, including assembled main/side role and actual hole clearance.",
                "Finished continuous BG045 receiver profile at both axes: actual edge/end faces, cut effects, hole intersections/webs, and manufacturing tolerances.",
                "As-observed species/product/grade, moisture/service condition and grain orientation/defects; source grain is a model proposal, not an inspection.",
                "A supported NDS loaded-edge convention for the multi-face block direction and a supported mixed-grain header detailing/group interaction method.",
                "A topology-compatible local force-transfer field, tension-perpendicular splitting mechanism/resistance, and complete bolt/contact/seat interaction; section resultants alone are insufficient.",
                "For NDS member/group capacity: matching adjusted Ft/Fv/bearing values, load-duration and service factors, actual holes/cuts/net section and row/group definition, and applicable design-load combination.",
            ],
            "result_boundary": "Conditional applicability and source geometry/arithmetic only; no capacity, acceptance, fabrication, or climbability claim.",
        },
        "reused_header_section_verification": {
            "status": section_parent["status"],
            "case_count": section_parent["case_count"],
            "one_sided_segment_wrench_comparisons": section_parent["one_sided_segment_wrench_comparisons"],
            "maximum_force_difference_N": section_parent["maximum_force_difference_n"],
            "maximum_moment_difference_Nmm": section_parent["maximum_moment_difference_nmm"],
            "source_discrete_gravity_distribution_qualified": section_parent["physical_self_weight_distribution_qualified"],
            "splitting_demand_or_resistance_established": section_parent["splitting_demand_or_resistance_established"],
        },
        "checks": {
            "three_source_models_verified_and_geometry_equal": True,
            "six_factor_one_BG045_pairs_crosschecked_against_complete_corner_register": True,
            "all_signed_actions_balanced_equal_and_opposite": True,
            "three_case_direction_reversal_retained": True,
            "source_geometry_modified": False,
            "reviewed_92_axis_geometry_modified": False,
            "native_run": False,
            "capacity_or_DCR_calculated": False,
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write results.json")
    args = parser.parse_args()
    result = main()
    rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.write:
        OUT.write_text(rendered)
        print(f"WROTE {OUT.relative_to(ROOT)} sha256={sha256(OUT)}")
    else:
        if not OUT.exists() or OUT.read_text() != rendered:
            raise SystemExit("FAIL results.json differs; run this isolated producer with --write")
        print(f"PASS_BG045_NDS_APPLICABILITY results_sha256={sha256(OUT)}")
