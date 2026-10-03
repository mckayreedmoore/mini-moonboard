#!/usr/bin/env python3
"""Recover signed base-header section resultants around the BG045 station."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
BASE = "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
HERE = Path(__file__).resolve().parent
OUT = HERE / "section-demands.json"
TRANSFER_X_MM = -1085.85
PLANE_TOLERANCE_MM = 1e-6
FORCE_TOLERANCE_N = 1e-9
MOMENT_TOLERANCE_NMM = 1e-7

CASE_SOURCES = {
    "a12-rear": {
        "report": BASE + "current-corner-native-demand-export-attempt03/corner-demand-report.json",
        "report_sha256": "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
        "model": BASE + "current-springa-selected-floor-a12-rear-attempt03/model.json",
        "model_sha256": "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
        "response": BASE + "current-springa-selected-floor-a12-rear-attempt03/response.json",
        "response_sha256": "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274",
        "terminal": BASE + "current-springa-selected-floor-a12-rear-attempt03/parent-terminal-assessment.json",
        "terminal_sha256": "e19dd495bf6ca910a0aa6a070e38dfc00e214974d8e62fbf72624387c80ce075",
        "all_body_audit": BASE + "current-springa-selected-floor-a12-rear-attempt03/parent-all-body-response-audit.json",
        "all_body_audit_sha256": "3da26086016c01f830e055bfa72c8a55370c9adc138b28d73127596924c410d5",
    },
    "a1-rear": {
        "report": BASE + "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json",
        "report_sha256": "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce",
        "model": BASE + "current-springa-selected-floor-a1-rear-attempt02/model.json",
        "model_sha256": "72d043e1a70702d8d464c21a039e897036e17c95e368ec776063584dac74f5fd",
        "response": BASE + "current-springa-selected-floor-a1-rear-attempt02/response-zero-u-token.json",
        "response_sha256": "257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c",
        "all_body_audit": BASE + "current-springa-selected-floor-a1-rear-attempt02/parent-all-body-response-audit.json",
        "all_body_audit_sha256": "247845921630a092c3f7a79d9ac11c92d732f021d2cb1dc5214e54b1a344deca",
        "parent_serialization": BASE + "current-springa-selected-floor-a1-rear-attempt02/parent-report-serialization.json",
        "parent_serialization_sha256": "ecdc1d3fb21bccd5192516bac99d5c286b8a9d9b2b13a18875c929780cbeb818",
    },
    "k12-rear": {
        "report": BASE + "current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json",
        "report_sha256": "a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0",
        "model": BASE + "current-k12-rear-spr489-direct-native-attempt01/model.json",
        "model_sha256": "8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd",
        "response": BASE + "current-k12-rear-spr489-direct-native-attempt01/response.json",
        "response_sha256": "42ffb135d47bd3bd28874e886682b4f07175ee060fb383b6e3c128e5102073c6",
        "terminal": BASE + "current-k12-rear-spr489-direct-native-attempt01/parent-terminal-assessment.json",
        "terminal_sha256": "a6ba8407bd5d74b90b651b04b760ef6dce48d09fa02dd687c4871cb1d7a7cbd3",
        "all_body_audit": BASE + "current-k12-rear-spr489-direct-native-attempt01/audit.json",
        "all_body_audit_sha256": "66c2b9aa397b16cd4c0b2420c5cf4588e15d12bfd3fbfd75b7df8f2b0d1d4bee",
    },
}

REQUIRED_RESPONSE_GATES = (
    "mpc_interval_checks_passed",
    "springa_law_checks_passed",
    "retained_bilateral_checks_passed",
    "selected_floor_complementarity_passed",
    "inactive_floor_tangent_no_restraint_or_reaction_passed",
    "raw_body_and_global_balance_passed",
    "rounding_interval_body_and_global_balance_passed",
)

EXPECTED_BG045_ACTIONS = {
    "knee_outer_left_inner_header_1/outer-seat-axial-tie",
    "knee_outer_left_inner_header_1/plane-33",
    "knee_outer_left_inner_header_2/outer-seat-axial-tie",
    "knee_outer_left_inner_header_2/plane-34",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def require_hash(relative: str, expected: str) -> str:
    observed = sha256(ROOT / relative)
    if observed != expected:
        raise RuntimeError(f"source hash mismatch for {relative}: {observed}")
    return observed


def add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b)]


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def sum_vectors(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return [0.0, 0.0, 0.0]
    return [math.fsum(v[i] for v in vectors) for i in range(3)]


def moment_radius_at_datum(point: list[float], datum: list[float], radius: list[float]) -> list[float]:
    r = [point[i] - datum[i] for i in range(3)]
    return [
        abs(r[1]) * radius[2] + abs(r[2]) * radius[1],
        abs(r[2]) * radius[0] + abs(r[0]) * radius[2],
        abs(r[0]) * radius[1] + abs(r[1]) * radius[0],
    ]


def close_vec(actual: list[float], expected: list[float], tol: float, label: str) -> None:
    if any(abs(a - e) > tol for a, e in zip(actual, expected)):
        raise AssertionError(f"{label} mismatch: actual={actual}, expected={expected}, tolerance={tol}")


def source_manifest() -> dict:
    checked = {}
    for spec in CASE_SOURCES.values():
        for key, relative in spec.items():
            if key.endswith("_sha256"):
                continue
            checked[relative] = require_hash(relative, spec[key + "_sha256"])
    return checked


def owner_rows(rows: list[dict], body: str) -> list[dict]:
    return [row for row in rows if row.get("first") == body or row.get("second") == body]


def endpoint_action(row: dict, body: str) -> dict:
    side = "first" if row["first"] == body else "second"
    point = row[f"{side}_point_global_xyz_mm"]
    serialized = row.get(f"{side}_side_wrench_at_owner_datum", {}).get("moment_xyz_nmm", [0.0, 0.0, 0.0])
    if max(map(abs, serialized)) > 1e-9:
        raise AssertionError(f"unexpected endpoint couple on {row.get('source_connection_name')}: {serialized}")
    return {
        "source_type": "physical_connection_force",
        "source_name": row.get("source_connection_name", row.get("axis_id")),
        "role": row["role"],
        "point_global_xyz_mm": point,
        "force_xyz_n": row[f"force_on_{side}_xyz_n"],
        "force_rounding_radius_xyz_n": row.get("force_rounding_radius_xyz_n", [0.0, 0.0, 0.0]),
        "free_moment_xyz_nmm": [0.0, 0.0, 0.0],
        "source_row_ids": row.get("source_row_ids", []),
        "source_inventory_rows": row.get("source_inventory_rows", []),
        "serialized_endpoint_moment_roundoff_xyz_nmm": serialized,
        "report_row": row,
    }


def source_load_actions(model: dict, body: str, load_factor: float) -> list[dict]:
    nodes = {str(node) for node in model["physical_body_nodes"][body]}
    loads = model["physical_body_loads"][body]
    if nodes != {str(node) for node in loads}:
        raise AssertionError(f"source node/load coverage mismatch for {body}")
    out = []
    for node, force in loads.items():
        point = model["nodes"].get(str(node), model["nodes"].get(node))
        if point is None:
            raise AssertionError(f"missing source node coordinate {node}")
        out.append({
            "source_type": "source_discrete_body_load",
            "source_name": f"{body}/node/{node}",
            "role": "source_discrete_gravity_and_attached_hardware_load",
            "point_global_xyz_mm": point,
            "force_xyz_n": [load_factor * float(v) for v in force],
            "force_rounding_radius_xyz_n": [0.0, 0.0, 0.0],
            "free_moment_xyz_nmm": [0.0, 0.0, 0.0],
            "source_row_ids": [],
            "source_inventory_rows": [],
        })
    return out


def wrench(actions: list[dict], datum: list[float]) -> tuple[list[float], list[float], list[float], list[float]]:
    force = sum_vectors([a["force_xyz_n"] for a in actions])
    moment = sum_vectors([
        add(cross([a["point_global_xyz_mm"][i] - datum[i] for i in range(3)], a["force_xyz_n"]), a["free_moment_xyz_nmm"])
        for a in actions
    ])
    force_radius = sum_vectors([a["force_rounding_radius_xyz_n"] for a in actions])
    moment_radius = sum_vectors([
        moment_radius_at_datum(a["point_global_xyz_mm"], datum, a["force_rounding_radius_xyz_n"])
        for a in actions
    ])
    return force, moment, force_radius, moment_radius


def negative_wrench(force: list[float], moment: list[float]) -> dict:
    return {
        "force_xyz_n": [-v for v in force],
        "moment_xyz_nmm": [-v for v in moment],
        "N_global_plus_X_on_segment_n": -force[0],
        "V_global_YZ_on_segment_xyz_n": [0.0, -force[1], -force[2]],
        "torsion_Mx_nmm": -moment[0],
        "bending_Myz_nmm": [-moment[1], -moment[2]],
    }


def source_body_full_factor_wrench(model: dict, body: str) -> tuple[list[float], list[float]]:
    force_terms = []
    moment_terms = []
    for node, force in model["physical_body_loads"][body].items():
        point = model["nodes"].get(str(node), model["nodes"].get(node))
        force_terms.append(force)
        moment_terms.append(cross(point, force))
    force = sum_vectors(force_terms)
    moment = sum_vectors(moment_terms)
    expected = model["physical_body_wrenches"][body]
    close_vec(force, expected["force_xyz_n"], 1e-9, f"full-factor source force for {body}")
    close_vec(moment, expected["moment_about_global_origin_xyz_nmm"], 1e-6, f"full-factor source moment for {body}")
    return force, moment


def validate_acceptance(case_id: str, report: dict, model: dict, response: dict, spec: dict) -> dict:
    if report.get("case_id") != case_id or model.get("case_id") != case_id or response.get("case_id") != case_id:
        raise AssertionError(f"case identity mismatch for {case_id}")
    if not report.get("actual_case_demand_usable_for_conditional_joint_checks") or not str(report.get("status", "")).startswith("PASS"):
        raise AssertionError(f"corner demand report not accepted for conditional demands: {case_id}")
    if not str(response.get("status", "")).startswith("PASS"):
        raise AssertionError(f"response not accepted: {case_id}")
    for gate in REQUIRED_RESPONSE_GATES:
        if response.get(gate) is not True:
            raise AssertionError(f"response root gate {gate} did not pass for {case_id}")
    if response.get("source_input_model_json_sha256") != spec["model_sha256"]:
        raise AssertionError(f"response source model pin mismatch for {case_id}")
    if len(report.get("increments", [])) != 7 or len(response.get("increments", [])) != 7:
        raise AssertionError(f"expected seven source increments for {case_id}")

    body = "base_header"
    geom = model["body_geometry"][body]["geometry_record"]
    if geom.get("axis") != [1.0, 0.0, 0.0]:
        raise AssertionError("base_header axis is not proposed grain +X")
    if geom.get("source_descriptor", {}).get("grain_global_xyz") != [1.0, 0.0, 0.0]:
        raise AssertionError("base_header model descriptor no longer records proposed grain +X")
    if len(model["physical_body_nodes"][body]) != 212 or len(model["physical_body_loads"][body]) != 212:
        raise AssertionError("base_header node/load inventory changed")
    source_body_full_factor_wrench(model, body)

    terminal_status = None
    all_body_status = None
    serialization_status = None
    if "terminal" in spec:
        terminal = load_json(spec["terminal"])
        terminal_status = terminal.get("status")
        if case_id == "a12-rear":
            if terminal_status != "PASS_CONDITIONAL_NUMERICAL_RESPONSE" or terminal.get("conditional_case_forces_usable") is not True:
                raise AssertionError("A12 source terminal acceptance changed")
        elif case_id == "k12-rear":
            if terminal_status != "PASS_PARENT_K12_REAR_DIRECT_RESPONSE_AND_ALL50" or terminal.get("response_usable_for_conditional_joint_checks") is not True:
                raise AssertionError("K12 source terminal acceptance changed")
    all_body = load_json(spec["all_body_audit"])
    all_body_status = all_body.get("status")
    if all_body_status not in ("PASS_PARENT_ALL_BODY_RESPONSE_SUMS", "PASS_PARENT_ALL_50_BODY_RESPONSE_SUMS"):
        raise AssertionError(f"all-body audit no longer passes for {case_id}")
    if len(all_body.get("increments", [])) != 7 or any(not row.get("passed") or row.get("body_count") != 50 for row in all_body["increments"]):
        raise AssertionError(f"all-body audit inventory changed for {case_id}")
    if "parent_serialization" in spec:
        serialization = load_json(spec["parent_serialization"])
        serialization_status = serialization.get("status")
        if str(serialization_status).startswith("FAIL"):
            raise AssertionError("A1 parent serialization audit failed")
    return {
        "conditional_report_status": report["status"],
        "usable_for_conditional_demands": True,
        "terminal_assessment_status": terminal_status,
        "parent_all_body_audit_status": all_body_status,
        "parent_serialization_status": serialization_status,
        "joint_acceptance": False,
    }


def validate_report_response_owner_inventory(report_inc: dict, response_inc: dict) -> tuple[list[dict], dict]:
    body = "base_header"
    report_rows = owner_rows(report_inc["all_corner_interfaces"], body)
    response_rows = {
        name: row for name, row in response_inc["physical_connection_forces"].items()
        if row.get("first") == body or row.get("second") == body
    }
    report_by_name = {row.get("source_connection_name", row.get("axis_id")): row for row in report_rows}
    if len(report_rows) != 160 or len(report_by_name) != 160 or set(report_by_name) != set(response_rows):
        raise AssertionError(f"base_header action inventory is incomplete: report={len(report_by_name)}, response={len(response_rows)}, symmetric_difference={sorted(set(report_by_name) ^ set(response_rows))}")
    max_point_difference = 0.0
    max_force_difference = 0.0
    role_counts = Counter()
    for name, row in report_by_name.items():
        physical = response_rows[name]
        if physical.get("first") != row.get("first") or physical.get("second") != row.get("second"):
            raise AssertionError(f"owner mismatch for {name}")
        side = "first" if row["first"] == body else "second"
        for j, (a, b) in enumerate(zip(row[f"{side}_point_global_xyz_mm"], physical.get(f"{side}_point", physical["point"]))):
            max_point_difference = max(max_point_difference, abs(a - b))
        for a, b in zip(row[f"force_on_{side}_xyz_n"], physical[f"force_on_{side}_xyz_n"]):
            max_force_difference = max(max_force_difference, abs(a - b))
        close_vec(
            row.get("force_rounding_radius_xyz_n", [0.0, 0.0, 0.0]),
            physical.get("force_rounding_radius_xyz_n", [0.0, 0.0, 0.0]),
            1e-12,
            f"source force rounding radius {name}",
        )
        close_vec(row[f"force_on_{side}_xyz_n"], physical[f"force_on_{side}_xyz_n"], 1e-10, f"source force {name}")
        close_vec(row[f"{side}_point_global_xyz_mm"], physical.get(f"{side}_point", physical["point"]), 1e-10, f"source point {name}")
        role_counts[row["role"]] += 1
    if max_point_difference > 1e-10 or max_force_difference > 1e-10:
        raise AssertionError("corner report and physical response differ beyond source tolerance")

    bg045_rows = [row for name, row in report_by_name.items() if name in EXPECTED_BG045_ACTIONS]
    if {r.get("source_connection_name") for r in bg045_rows} != EXPECTED_BG045_ACTIONS or len(bg045_rows) != 4:
        raise AssertionError("BG045 transfer station action rows changed")
    for row in bg045_rows:
        side = "first" if row["first"] == body else "second"
        if abs(row[f"{side}_point_global_xyz_mm"][0] - TRANSFER_X_MM) > PLANE_TOLERANCE_MM:
            raise AssertionError(f"BG045 endpoint moved from the pinned header station: {row['source_connection_name']}")
    return report_rows, {
        "report_header_owner_row_count": len(report_rows),
        "response_header_owner_row_count": len(response_rows),
        "matched_source_connection_names": len(set(report_by_name) & set(response_rows)),
        "max_report_response_point_difference_mm": max_point_difference,
        "max_report_response_force_difference_n": max_force_difference,
        "header_owner_role_counts": dict(sorted(role_counts.items())),
        "bg045_transfer_action_names": sorted(EXPECTED_BG045_ACTIONS),
        "direct_floor_tangent_action_count_on_header": sum(
            1 for r in response_inc.get("exact_floor_tangent_reactions", [])
            if r.get("first") == body or r.get("second") == body
        ),
        "inactive_floor_tangent_zero_action_count_on_header": sum(
            1 for r in response_inc.get("inactive_floor_tangent_zero_actions", [])
            if r.get("first") == body or r.get("second") == body
        ),
    }


def cut_result(actions: list[dict], x_cut: float, datum: list[float]) -> dict:
    full_wrench = wrench(actions, datum)
    left, plane, right = [], [], []
    for action in actions:
        dx = action["point_global_xyz_mm"][0] - x_cut
        if dx < -PLANE_TOLERANCE_MM:
            left.append(action)
        elif dx > PLANE_TOLERANCE_MM:
            right.append(action)
        else:
            plane.append(action)

    # Before the transfer station, all plane-coincident point forces remain on
    # the right free body; after it, all are on the left free body.
    states = {}
    for name, (left_ext, right_ext) in {
        "immediately_before_transfer": (left, plane + right),
        "immediately_after_transfer": (left + plane, right),
    }.items():
        left_wrench = wrench(left_ext, datum)
        right_wrench = wrench(right_ext, datum)
        states[name] = {
            "left_segment_external_action_count": len(left_ext),
            "left_segment_external_action_counts_by_role": dict(sorted(Counter(a["role"] for a in left_ext).items())),
            "left_segment_source_discrete_load_node_count": sum(a["source_type"] == "source_discrete_body_load" for a in left_ext),
            "left_segment_material_action": negative_wrench(left_wrench[0], left_wrench[1]),
            "left_segment_material_action_rounding_radius": {"force_xyz_n": left_wrench[2], "moment_xyz_nmm": left_wrench[3]},
            "right_segment_external_action_count": len(right_ext),
            "right_segment_external_action_counts_by_role": dict(sorted(Counter(a["role"] for a in right_ext).items())),
            "right_segment_source_discrete_load_node_count": sum(a["source_type"] == "source_discrete_body_load" for a in right_ext),
            "right_segment_material_action": negative_wrench(right_wrench[0], right_wrench[1]),
            "right_segment_material_action_rounding_radius": {"force_xyz_n": right_wrench[2], "moment_xyz_nmm": right_wrench[3]},
            "complementary_internal_action_sum_xyz": {
                "force_xyz_n": add(negative_wrench(left_wrench[0], left_wrench[1])["force_xyz_n"], negative_wrench(right_wrench[0], right_wrench[1])["force_xyz_n"]),
                "moment_xyz_nmm": add(negative_wrench(left_wrench[0], left_wrench[1])["moment_xyz_nmm"], negative_wrench(right_wrench[0], right_wrench[1])["moment_xyz_nmm"]),
            },
        }

    plane_wrench = wrench(plane, datum)
    plane_rows = []
    for action in plane:
        plane_rows.append({
            "source_type": action["source_type"],
            "source_name": action["source_name"],
            "role": action["role"],
            "point_global_xyz_mm": action["point_global_xyz_mm"],
            "force_xyz_n": action["force_xyz_n"],
            "free_moment_xyz_nmm": action["free_moment_xyz_nmm"],
            "source_row_ids": action["source_row_ids"],
        })
    plane_reaction = negative_wrench(plane_wrench[0], plane_wrench[1])
    lower_force_jump = [
        states["immediately_after_transfer"]["left_segment_material_action"]["force_xyz_n"][i]
        - states["immediately_before_transfer"]["left_segment_material_action"]["force_xyz_n"][i]
        for i in range(3)
    ]
    lower_moment_jump = [
        states["immediately_after_transfer"]["left_segment_material_action"]["moment_xyz_nmm"][i]
        - states["immediately_before_transfer"]["left_segment_material_action"]["moment_xyz_nmm"][i]
        for i in range(3)
    ]
    right_force_jump = [
        states["immediately_after_transfer"]["right_segment_material_action"]["force_xyz_n"][i]
        - states["immediately_before_transfer"]["right_segment_material_action"]["force_xyz_n"][i]
        for i in range(3)
    ]
    right_moment_jump = [
        states["immediately_after_transfer"]["right_segment_material_action"]["moment_xyz_nmm"][i]
        - states["immediately_before_transfer"]["right_segment_material_action"]["moment_xyz_nmm"][i]
        for i in range(3)
    ]
    close_vec(lower_force_jump, plane_reaction["force_xyz_n"], FORCE_TOLERANCE_N, "left segment force jump")
    close_vec(lower_moment_jump, plane_reaction["moment_xyz_nmm"], MOMENT_TOLERANCE_NMM, "left segment moment jump")
    close_vec(right_force_jump, [-v for v in plane_reaction["force_xyz_n"]], FORCE_TOLERANCE_N, "right segment force jump")
    close_vec(right_moment_jump, [-v for v in plane_reaction["moment_xyz_nmm"]], MOMENT_TOLERANCE_NMM, "right segment moment jump")

    for name, state in states.items():
        expected_force = [-v for v in full_wrench[0]]
        expected_moment = [-v for v in full_wrench[1]]
        close_vec(state["complementary_internal_action_sum_xyz"]["force_xyz_n"], expected_force, FORCE_TOLERANCE_N, f"{name} full-body force closure")
        close_vec(state["complementary_internal_action_sum_xyz"]["moment_xyz_nmm"], expected_moment, MOMENT_TOLERANCE_NMM, f"{name} full-body moment closure")

    return {
        "cut_datum_global_xyz_mm": datum,
        "normal_axis_global": [1.0, 0.0, 0.0],
        "section_axis_basis": {"axial": "+X", "shear": "Y,Z", "bending_moment": "My,Mz", "torsion": "Mx"},
        "whole_header_external_wrench_about_cut_datum": {
            "force_xyz_n": full_wrench[0],
            "moment_xyz_nmm": full_wrench[1],
            "force_rounding_radius_xyz_n": full_wrench[2],
            "moment_rounding_radius_xyz_nmm": full_wrench[3],
            "physical_connection_action_count": sum(a["source_type"] == "physical_connection_force" for a in actions),
            "source_discrete_body_load_node_count": sum(a["source_type"] == "source_discrete_body_load" for a in actions),
        },
        "plane_coincident_external_wrench": {
            "force_xyz_n": plane_wrench[0],
            "moment_xyz_nmm_about_cut_datum": plane_wrench[1],
            "force_rounding_radius_xyz_n": plane_wrench[2],
            "moment_rounding_radius_xyz_nmm": plane_wrench[3],
            "point_action_count": len(plane),
            "point_actions": plane_rows,
        },
        "one_sided_sections": states,
        "cut_jump_check": {
            "left_segment_action_jump_after_minus_before": {"force_xyz_n": lower_force_jump, "moment_xyz_nmm": lower_moment_jump},
            "right_segment_action_jump_after_minus_before": {"force_xyz_n": right_force_jump, "moment_xyz_nmm": right_moment_jump},
            "expected_left_jump_is_negative_plane_external_wrench": True,
            "expected_right_jump_is_positive_plane_external_wrench": True,
        },
    }


def force_couple_transport_oracle() -> dict:
    force = [0.0, 10.0, 0.0]
    point = [2.0, 0.0, 0.0]
    couple = [0.0, 0.0, 3.0]
    at_origin = add(cross(point, force), couple)
    shifted_datum = [1.0, 0.0, 0.0]
    at_shifted_datum = add(cross([point[i] - shifted_datum[i] for i in range(3)], force), couple)
    close_vec(at_origin, [0.0, 0.0, 23.0], 1e-12, "force/couple transport oracle at origin")
    close_vec(at_shifted_datum, [0.0, 0.0, 13.0], 1e-12, "force/couple transport oracle at shifted datum")
    return {
        "status": "PASS_KNOWN_FORCE_COUPLE_TRANSPORT_ORACLE",
        "force_xyz_n": force,
        "application_point_global_xyz_mm": point,
        "free_couple_xyz_nmm": couple,
        "moment_about_global_origin_xyz_nmm": at_origin,
        "translated_datum_global_xyz_mm": shifted_datum,
        "moment_about_translated_datum_xyz_nmm": at_shifted_datum,
        "identity": "M_d = (p - d) x F + C; the same force/couple gives +23 Nmm about the origin and +13 Nmm about the datum at x=1 mm.",
    }


def result() -> dict:
    hashes = source_manifest()
    case_auth = []
    rows = []
    load_roles = Counter()

    for case_id, spec in CASE_SOURCES.items():
        report = load_json(spec["report"])
        model = load_json(spec["model"])
        response = load_json(spec["response"])
        auth = validate_acceptance(case_id, report, model, response, spec)
        case_auth.append({
            "case_id": case_id,
            **auth,
            "source_paths": {key: value for key, value in spec.items() if not key.endswith("_sha256")},
            "source_sha256": {key: hashes[spec[key]] for key in spec if not key.endswith("_sha256")},
        })

        for report_inc, response_inc in zip(report["increments"], response["increments"]):
            if report_inc.get("time") != response_inc.get("time") or report_inc.get("load_factor") != response_inc.get("load_factor"):
                raise AssertionError(f"increment identity mismatch for {case_id}")
            if report_inc.get("all_five_corner_bodies_raw_and_interval_balance_passed") is not True:
                raise AssertionError(f"corner report balance gate changed for {case_id} at {report_inc['time']}")
            if len(report_inc.get("all_corner_interfaces", [])) != 338 or len(response_inc.get("physical_connection_forces", {})) != 1466:
                raise AssertionError(f"source interaction inventory count changed for {case_id}")
            for gate in REQUIRED_RESPONSE_GATES:
                key = {"raw_body_and_global_balance_passed": "raw_balance_passed", "rounding_interval_body_and_global_balance_passed": "rounding_interval_balance_passed"}.get(gate, gate)
                if response_inc.get(key) is not True:
                    raise AssertionError(f"response increment gate {key} failed for {case_id} at {report_inc['time']}")

            report_rows, inventory_audit = validate_report_response_owner_inventory(report_inc, response_inc)
            load_factor = float(report_inc["load_factor"])
            connections = [endpoint_action(row, "base_header") for row in owner_rows(report_rows, "base_header")]
            loads = source_load_actions(model, "base_header", load_factor)
            actions = connections + loads
            load_roles.update(a["role"] for a in loads)
            datum = [TRANSFER_X_MM, -105.85, 257.95]
            body_wrench = wrench(actions, [0.0, 0.0, 0.0])
            if any(abs(body_wrench[0][j]) > body_wrench[2][j] + FORCE_TOLERANCE_N for j in range(3)):
                raise AssertionError(f"header full-body force does not close for {case_id}/{report_inc['time']}: {body_wrench[0]} +/- {body_wrench[2]}")
            if any(abs(body_wrench[1][j]) > body_wrench[3][j] + MOMENT_TOLERANCE_NMM for j in range(3)):
                raise AssertionError(f"header full-body moment does not close for {case_id}/{report_inc['time']}: {body_wrench[1]} +/- {body_wrench[3]}")

            section = cut_result(actions, TRANSFER_X_MM, datum)
            # Retain the full-body closure residual about the cut datum as the
            # identity target for the complementary left/right section actions.
            cut_body_wrench = wrench(actions, datum)
            for state in section["one_sided_sections"].values():
                close_vec(state["complementary_internal_action_sum_xyz"]["force_xyz_n"], [-v for v in cut_body_wrench[0]], FORCE_TOLERANCE_N, "section force closure at cut datum")
                close_vec(state["complementary_internal_action_sum_xyz"]["moment_xyz_nmm"], [-v for v in cut_body_wrench[1]], MOMENT_TOLERANCE_NMM, "section moment closure at cut datum")
            section["whole_header_external_wrench_about_cut_datum"] = {
                "force_xyz_n": cut_body_wrench[0],
                "moment_xyz_nmm": cut_body_wrench[1],
                "force_rounding_radius_xyz_n": cut_body_wrench[2],
                "moment_rounding_radius_xyz_nmm": cut_body_wrench[3],
                "physical_connection_action_count": len(connections),
                "source_discrete_body_load_node_count": len(loads),
            }
            rows.append({
                "case_id": case_id,
                "time": report_inc["time"],
                "load_factor": load_factor,
                "full_base_header_external_action_inventory": inventory_audit,
                "base_header_body_load_node_count": len(loads),
                "base_header_full_body_closure_about_global_origin": {
                    "force_residual_xyz_n": body_wrench[0],
                    "force_rounding_radius_xyz_n": body_wrench[2],
                    "moment_residual_about_global_origin_xyz_nmm": body_wrench[1],
                    "moment_rounding_radius_about_global_origin_xyz_nmm": body_wrench[3],
                    "passed_with_source_rounding_intervals": True,
                },
                "section_at_transfer_station": section,
            })

    return {
        "schema": "current_bg045_header_transfer_section_demands/v1",
        "status": "PASS_SOURCE_PINNED_CONDITIONAL_SIGNED_HEADER_SECTION_ACTIONS",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": "Source-bound signed base_header section actions immediately on both sides of the left BG045 transfer station using the three accepted rear numerical-demand cases; no splitting stress, resistance, capacity ratio, or joint acceptance.",
        "member_and_cut": {
            "member_id": "base_header",
            "proposed_grain_global_xyz": [1.0, 0.0, 0.0],
            "header_axis_global_xyz": [1.0, 0.0, 0.0],
            "section_normal_global_xyz": [1.0, 0.0, 0.0],
            "transfer_station_global_x_mm": TRANSFER_X_MM,
            "section_datum_global_xyz_mm": [TRANSFER_X_MM, -105.85, 257.95],
            "station_basis": "The four exported BG045 header endpoint actions (two lateral planes and two outer-seat axial ties) lie on this same source station within 1e-6 mm; no source header load node lies on the station.",
            "side_convention": "Left segment is x < station; right segment is x > station. The before-cut assigns plane-coincident actions to the right segment; the after-cut assigns them to the left. Each segment material action is minus its simultaneous external wrench about the fixed cut datum.",
            "conditional_source_geometry_only": True,
        },
        "source_case_authorization": case_auth,
        "known_force_couple_transport_oracle": force_couple_transport_oracle(),
        "per_increment_header_sections": rows,
        "load_inventory": {
            "header_discrete_load_role": "source_discrete_gravity_and_attached_hardware_load",
            "load_node_count_per_case_increment": 212,
            "load_scaling": "source physical_body_loads[base_header] multiplied by the accepted report load_factor; no new/self-weight distribution introduced",
            "all_discrete_load_nodes_partitioned_by_global_X": True,
        },
        "method_checks": {
            "header_report_owner_rows_match_physical_response_owner_inventory_each_increment": True,
            "full_header_body_force_and_moment_close_with_source_rounding_intervals_each_increment": True,
            "both_complementary_segment_actions_sum_to_negative_full_body_external_residual": True,
            "left_and_right_one_sided_cut_jumps_match_plane_external_wrench": True,
            "source_endpoint_free_couples": "None; serialized endpoint moment remnants are required to be <=1e-9 Nmm and are not counted as physical couples.",
            "source_discrete_load_nodes_on_transfer_plane": 0,
        },
        "scope_limits": [
            "The output is a conditional source-discrete force and moment resultant, not a local stress or strain field.",
            "It does not define tension-perpendicular demand at the BG045 bolt, washer, contact edge, or header grain; a validated local transfer field and a compatible splitting method remain missing.",
            "NDS splitting provisions identify concern and analysis/test obligations but do not supply a general resistance equation for this BG045 block/header topology in the reviewed source record.",
            "No member resistance, capacity ratio, complete-joint acceptance, actual-stock observation, fabrication instruction, or climber/design qualification follows.",
            "The 10 modeled parametric screw-withdrawal rows remain in equilibrium bookkeeping although their response role is explicitly non-qualifying for resistance.",
        ],
        "execution_boundary": {
            "native_solver_run": False,
            "CAD_query_or_rebuild": False,
            "geometry_or_axis_files_modified": False,
            "92_axis_inventory_changed": False,
            "selected_baseline_or_master_study_modified": False,
            "capacity_or_design_DCR_calculated": False,
            "splitting_demand_or_resistance_calculated": False,
            "complete_joint_accepted": False,
        },
        "source_sha256": hashes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    data = result()
    encoded = (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if args.write:
        OUT.write_bytes(encoded)
        print(f"wrote {OUT.relative_to(ROOT)}")
    else:
        if not OUT.exists() or OUT.read_bytes() != encoded:
            raise SystemExit("FAIL: current section result is absent or differs; use --write only for an intentional source-bound refresh")
        print("PASS: authenticated header sections, full-body closure, and cut jumps reproduce byte-for-byte")


if __name__ == "__main__":
    main()
