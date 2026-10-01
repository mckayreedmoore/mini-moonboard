#!/usr/bin/env python3
"""Recover source-bound conditional section resultants for the left corner."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
BASE = "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
HERE = Path(__file__).resolve().parent
OUT = HERE / "section-demands.json"
PLANE_TOLERANCE_MM = 1e-6
VECTOR_CHECK_TOLERANCE_N = 1e-9
MOMENT_CHECK_TOLERANCE_NMM = 1e-7

GEOMETRY_SCREEN = BASE + "current-corner-local-wood-screen-attempt01/section-screen.json"
GEOMETRY_PRODUCER = BASE + "current-corner-local-wood-screen-attempt01/produce.py"

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

GEOMETRY_SCREEN_SHA256 = "22209a82b0bda6dfc5c140ccc4e481717e0e7c71d30a5827271c81ac71070564"
GEOMETRY_PRODUCER_SHA256 = "e7223a65675051dda912e36b16e9ab697dace5cf3f21af3ece0322af87783d02"

TARGETS = {
    "knee_outer_left_spine": {
        "axis": [0.0, 0.0, 1.0],
        "stations": [
            ("knee_outer_left_post_1", "BG001", 171.45),
            ("knee_outer_left_post_2", "BG001", 213.5),
            ("knee_outer_left_side_1", "BG003", 331.31555301851245),
            ("knee_outer_left_side_2", "BG003", 365.7875529588667),
        ],
        "net_area_index": 0,
    },
    "knee_outer_left_inner_frame_block": {
        "axis": [0.0, 0.0, 1.0],
        "stations": [
            ("knee_outer_left_side_1", "BG003", 331.31555301851245),
            ("knee_outer_left_side_2", "BG003", 365.7875529588667),
        ],
        "net_area_index": 1,
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


def force_radius_to_moment_radius(point: list[float], radius: list[float]) -> list[float]:
    x, y, z = point
    rx, ry, rz = radius
    return [abs(y) * rz + abs(z) * ry, abs(z) * rx + abs(x) * rz, abs(x) * ry + abs(y) * rx]


def moment_radius_at_datum(point: list[float], datum: list[float], radius: list[float]) -> list[float]:
    r = [point[i] - datum[i] for i in range(3)]
    return force_radius_to_moment_radius(r, radius)


def close_vec(actual: list[float], expected: list[float], tol: float, label: str) -> None:
    if any(abs(a - e) > tol for a, e in zip(actual, expected)):
        raise AssertionError(f"{label} mismatch: actual={actual}, expected={expected}, tolerance={tol}")


def checked_source_manifest() -> dict:
    checked = {
        GEOMETRY_SCREEN: require_hash(GEOMETRY_SCREEN, GEOMETRY_SCREEN_SHA256),
        GEOMETRY_PRODUCER: require_hash(GEOMETRY_PRODUCER, GEOMETRY_PRODUCER_SHA256),
    }
    for spec in CASE_SOURCES.values():
        for key in ("report", "model", "response", "all_body_audit", "terminal", "parent_serialization"):
            relative = spec.get(key)
            expected = spec.get(key + "_sha256")
            if relative is not None:
                if not expected:
                    raise AssertionError(f"missing expected hash for {relative}")
                checked[relative] = require_hash(relative, expected)
    return checked


def rows_for_body(rows: list[dict], body: str) -> list[dict]:
    return [r for r in rows if r.get("first") == body or r.get("second") == body]


def endpoint(row: dict, body: str) -> tuple[str, list[float], list[float], list[float], list[float]]:
    if row["first"] == body:
        side = "first"
    elif row["second"] == body:
        side = "second"
    else:
        raise AssertionError(f"{body} is not an owner of {row.get('source_connection_name')}")
    return (
        side,
        row[f"{side}_point_global_xyz_mm"],
        row[f"force_on_{side}_xyz_n"],
        row.get("force_rounding_radius_xyz_n", [0.0, 0.0, 0.0]),
        [0.0, 0.0, 0.0],
    )


def endpoint_count_by_role(rows: list[dict], body: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows_for_body(rows, body):
        out[row["role"]] = out.get(row["role"], 0) + 1
    return dict(sorted(out.items()))


def full_wrench(points_forces_couples: list[tuple[list[float], list[float], list[float]]], datum: list[float]) -> tuple[list[float], list[float]]:
    force = sum_vectors([f for _, f, _ in points_forces_couples])
    moments = []
    for point, f, couple in points_forces_couples:
        arm = [point[i] - datum[i] for i in range(3)]
        moments.append(add(cross(arm, f), couple))
    return force, sum_vectors(moments)


def body_action_data(model: dict, rows: list[dict], body: str, load_factor: float) -> tuple[list[dict], list[dict]]:
    actions = []
    for row in rows_for_body(rows, body):
        side, point, force, radius, couple = endpoint(row, body)
        serialized_roundoff = row.get(f"{side}_side_wrench_at_owner_datum", {}).get("moment_xyz_nmm", [0.,0.,0.])
        assert max(map(abs,serialized_roundoff)) <= 1e-9, "Source supplies no physical endpoint couple"
        actions.append({
            "source_type": "physical_connection_force",
            "source_name": row.get("source_connection_name", row.get("axis_id")),
            "role": row.get("role"),
            "owner_side": side,
            "owner_point_global_xyz_mm": point,
            "force_xyz_n": force,
            "force_rounding_radius_xyz_n": radius,
            "free_moment_xyz_nmm": couple,
            "serialized_endpoint_moment_roundoff_xyz_nmm": serialized_roundoff,
            "source_row_ids": row.get("source_row_ids", []),
            "source_inventory_rows": row.get("source_inventory_rows", []),
            "report_row": row,
        })
    loads = []
    for node, reference_force in model["physical_body_loads"][body].items():
        point = model["nodes"].get(str(node), model["nodes"].get(node))
        if point is None:
            raise AssertionError(f"missing node coordinate {node} for {body}")
        loads.append({
            "source_type": "source_discrete_body_load",
            "source_name": f"{body}/node/{node}",
            "role": "source_discrete_gravity_and_attached_hardware_load",
            "owner_point_global_xyz_mm": point,
            "force_xyz_n": [load_factor * float(v) for v in reference_force],
            "force_rounding_radius_xyz_n": [0.0, 0.0, 0.0],
            "free_moment_xyz_nmm": [0.0, 0.0, 0.0],
            "source_row_ids": [],
            "source_inventory_rows": [],
        })
    return actions, loads


def sum_actions(actions: list[dict], datum: list[float]) -> tuple[list[float], list[float], list[float], list[float]]:
    force = sum_vectors([a["force_xyz_n"] for a in actions])
    moment_terms = []
    force_radius_terms = []
    moment_radius_terms = []
    for action in actions:
        point = action["owner_point_global_xyz_mm"]
        radius = action["force_rounding_radius_xyz_n"]
        force = force
        arm = [point[i] - datum[i] for i in range(3)]
        moment_terms.append(add(cross(arm, action["force_xyz_n"]), action["free_moment_xyz_nmm"]))
        force_radius_terms.append(radius)
        moment_radius_terms.append(moment_radius_at_datum(point, datum, radius))
    return (
        force,
        sum_vectors(moment_terms),
        sum_vectors(force_radius_terms),
        sum_vectors(moment_radius_terms),
    )


def negative_wrench(force: list[float], moment: list[float]) -> dict:
    return {
        "force_xyz_n": [-v for v in force],
        "moment_xyz_nmm": [-v for v in moment],
        "N_global_plus_Z_on_lower_segment_n": -force[2],
        "V_global_XY_on_lower_segment_xyz_n": [-force[0], -force[1], 0.0],
    }


def assert_response_accepted(case_id: str, report: dict, response: dict) -> None:
    if report.get("case_id") != case_id or response.get("case_id") != case_id:
        raise AssertionError(f"case identity mismatch for {case_id}")
    if not report.get("actual_case_demand_usable_for_conditional_joint_checks", False):
        raise AssertionError(f"corner report does not mark {case_id} usable for conditional demands")
    if not str(report.get("status", "")).startswith("PASS"):
        raise AssertionError(f"corner report not PASS for {case_id}: {report.get('status')}")
    if not str(response.get("status", "")).startswith("PASS"):
        raise AssertionError(f"response audit not PASS for {case_id}: {response.get('status')}")
    for gate in REQUIRED_RESPONSE_GATES:
        if response.get(gate) is not True:
            raise AssertionError(f"response root gate {gate} failed for {case_id}")
    if len(report.get("increments", [])) != 7 or len(response.get("increments", [])) != 7:
        raise AssertionError(f"expected exactly seven accepted states for {case_id}")
    final = report["increments"][-1]
    if float(final.get("load_factor", -1.0)) != 1.0:
        raise AssertionError(f"{case_id} report is not full-factor")


def source_body_wrench(model: dict, body: str) -> tuple[list[float], list[float]]:
    nodes = set(str(n) for n in model["physical_body_nodes"][body])
    loads = model["physical_body_loads"][body]
    if set(loads) != nodes:
        raise AssertionError(f"body node/load support mismatch for {body}")
    force_terms = []
    moment_terms = []
    for node, force in loads.items():
        point = model["nodes"].get(str(node), model["nodes"].get(node))
        if point is None:
            raise AssertionError(f"missing body load coordinate for {body} node {node}")
        force_terms.append(force)
        moment_terms.append(cross(point, force))
    force = sum_vectors(force_terms)
    moment = sum_vectors(moment_terms)
    expected = model["physical_body_wrenches"][body]
    close_vec(force, expected["force_xyz_n"], 1e-9, f"source full-factor force {body}")
    close_vec(moment, expected["moment_about_global_origin_xyz_nmm"], 1e-6, f"source full-factor moment {body}")
    return force, moment


def cut_partition(actions: list[dict], station_z: float, datum: list[float]) -> dict:
    below: list[dict] = []
    plane: list[dict] = []
    above: list[dict] = []
    for action in actions:
        dz = action["owner_point_global_xyz_mm"][2] - station_z
        if dz < -PLANE_TOLERANCE_MM:
            below.append(action)
        elif dz > PLANE_TOLERANCE_MM:
            above.append(action)
        else:
            plane.append(action)

    q_minus_lower = below
    q_minus_upper = plane + above
    q_plus_lower = below + plane
    q_plus_upper = above
    sides = {}
    for name, (lower, upper) in {
        "just_below": (q_minus_lower, q_minus_upper),
        "just_above": (q_plus_lower, q_plus_upper),
    }.items():
        lower_ext = sum_actions(lower, datum)
        upper_ext = sum_actions(upper, datum)
        lower_reaction = negative_wrench(lower_ext[0], lower_ext[1])
        upper_reaction = {
            "force_xyz_n": [-v for v in upper_ext[0]],
            "moment_xyz_nmm": [-v for v in upper_ext[1]],
            "N_global_plus_Z_on_upper_segment_n": -upper_ext[0][2],
            "V_global_XY_on_upper_segment_xyz_n": [-upper_ext[0][0], -upper_ext[0][1], 0.0],
        }
        sides[name] = {
            "lower_segment_material_action": lower_reaction,
            "lower_segment_material_action_rounding_radius": {
                "force_xyz_n": lower_ext[2],
                "moment_xyz_nmm": lower_ext[3],
            },
            "upper_segment_material_action": upper_reaction,
            "upper_segment_material_action_rounding_radius": {
                "force_xyz_n": upper_ext[2],
                "moment_xyz_nmm": upper_ext[3],
            },
            "lower_external_force_count": len(lower),
            "upper_external_force_count": len(upper),
        }

    plane_ext = sum_actions(plane, datum)
    plane_refs = []
    for action in plane:
        report_row = action.get("report_row")
        plane_refs.append({
            "source_type": action["source_type"],
            "source_name": action["source_name"],
            "role": action["role"],
            "owner_side": action.get("owner_side"),
            "owner_point_global_xyz_mm": action["owner_point_global_xyz_mm"],
            "force_xyz_n": action["force_xyz_n"],
            "free_moment_xyz_nmm": action["free_moment_xyz_nmm"],
            "source_row_ids": action["source_row_ids"],
            "source_inventory_rows": action["source_inventory_rows"],
            "reference_report_row_source_name": report_row.get("source_connection_name") if report_row else None,
        })

    plane_reaction = {
        "force_xyz_n": [-v for v in plane_ext[0]],
        "moment_xyz_nmm": [-v for v in plane_ext[1]],
    }
    lower_jump = [
        sides["just_above"]["lower_segment_material_action"]["force_xyz_n"][i]
        - sides["just_below"]["lower_segment_material_action"]["force_xyz_n"][i]
        for i in range(3)
    ]
    lower_moment_jump = [
        sides["just_above"]["lower_segment_material_action"]["moment_xyz_nmm"][i]
        - sides["just_below"]["lower_segment_material_action"]["moment_xyz_nmm"][i]
        for i in range(3)
    ]
    upper_jump = [
        sides["just_above"]["upper_segment_material_action"]["force_xyz_n"][i]
        - sides["just_below"]["upper_segment_material_action"]["force_xyz_n"][i]
        for i in range(3)
    ]
    upper_moment_jump = [
        sides["just_above"]["upper_segment_material_action"]["moment_xyz_nmm"][i]
        - sides["just_below"]["upper_segment_material_action"]["moment_xyz_nmm"][i]
        for i in range(3)
    ]
    for actual, expected, label in (
        (lower_jump, plane_reaction["force_xyz_n"], "lower point-force jump"),
        (lower_moment_jump, plane_reaction["moment_xyz_nmm"], "lower point-moment jump"),
        (upper_jump, [-v for v in plane_reaction["force_xyz_n"]], "upper point-force jump"),
        (upper_moment_jump, [-v for v in plane_reaction["moment_xyz_nmm"]], "upper point-moment jump"),
    ):
        close_vec(actual, expected, 1e-7, label)

    return {
        "just_below": sides["just_below"],
        "just_above": sides["just_above"],
        "plane_coincident_external_wrench": {
            "force_xyz_n": plane_ext[0],
            "moment_xyz_nmm_about_cut_datum": plane_ext[1],
            "force_rounding_radius_xyz_n": plane_ext[2],
            "moment_rounding_radius_xyz_nmm": plane_ext[3],
            "point_action_count": len(plane),
            "point_actions": plane_refs,
        },
        "point_action_jump": {
            "lower_segment_action_just_above_minus_just_below": {
                "force_xyz_n": lower_jump,
                "moment_xyz_nmm": lower_moment_jump,
            },
            "upper_segment_action_just_above_minus_just_below": {
                "force_xyz_n": upper_jump,
                "moment_xyz_nmm": upper_moment_jump,
            },
            "identity": "lower-side jump equals minus the plane-coincident external wrench; upper-side jump equals plus that wrench, all moments about the same cut datum.",
        },
    }


def report_increment_gate_passed(report_increment: dict) -> bool:
    return report_increment.get("all_five_corner_bodies_raw_and_interval_balance_passed") is True


def result() -> dict:
    hashes = checked_source_manifest()
    geometry = load_json(GEOMETRY_SCREEN)
    if geometry.get("schema") != "current_corner_local_wood_geometry_screen/v1":
        raise AssertionError("local geometry screen schema changed")
    if geometry.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise AssertionError("local geometry screen revision mismatch")
    net_inputs = {item["member_id"]: item for item in geometry["candidate_net_section_inputs"]}

    prepared = {}
    all_rows = []
    case_auth = []
    for case_id, spec in CASE_SOURCES.items():
        report = load_json(spec["report"])
        model = load_json(spec["model"])
        response = load_json(spec["response"])
        assert_response_accepted(case_id, report, response)
        if model.get("case_id") != case_id or model.get("geometry_revision_id") != geometry["geometry_revision_id"]:
            raise AssertionError(f"model identity/revision mismatch for {case_id}")
        if response.get("source_input_model_json_sha256") != spec["model_sha256"]:
            raise AssertionError(f"response does not pin expected model for {case_id}")
        if len(report["increments"]) != len(response["increments"]):
            raise AssertionError(f"report/response increment count mismatch for {case_id}")

        # The parent all-body audit is a separate acceptance gate; require its source-bound pass.
        auth = report.get("authenticated_source_case", report.get("authenticated_sources", {}))
        if case_id == "a12-rear":
            terminal = load_json(spec["terminal"])
            all_body = load_json(spec["all_body_audit"])
            if terminal.get("status") != "PASS_CONDITIONAL_NUMERICAL_RESPONSE" or terminal.get("conditional_case_forces_usable") is not True:
                raise AssertionError("A12 parent terminal assessment is not accepted")
            if all_body.get("status") != "PASS_PARENT_ALL_BODY_RESPONSE_SUMS" or not (len(all_body.get("increments", [])) == 7 and all(r["passed"] and r["body_count"] == 50 for r in all_body["increments"])):
                raise AssertionError("A12 parent all-body audit is not accepted")
            case_auth.append({
                "case_id": case_id,
                "conditional_response_status": terminal["status"],
                "parent_all_body_audit_status": all_body["status"],
                "usable_for_conditional_corner_demands": True,
                "joint_acceptance": False,
                "source_paths": {k: spec[k] for k in ("report", "model", "response", "terminal", "all_body_audit")},
                "source_sha256": {k: hashes[spec[k]] for k in ("report", "model", "response", "terminal", "all_body_audit")},
            })
        elif case_id == "a1-rear":
            all_body = load_json(spec["all_body_audit"])
            serialization = load_json(spec["parent_serialization"])
            if all_body.get("status") != "PASS_PARENT_ALL_BODY_RESPONSE_SUMS" or not (len(all_body.get("increments", [])) == 7 and all(r["passed"] and r["body_count"] == 50 for r in all_body["increments"])):
                raise AssertionError("A1 parent all-body audit is not accepted")
            if serialization.get("status", "").startswith("FAIL"):
                raise AssertionError("A1 parent serialization evidence failed")
            case_auth.append({
                "case_id": case_id,
                "conditional_response_status": response["status"],
                "parent_all_body_audit_status": all_body["status"],
                "usable_for_conditional_corner_demands": True,
                "joint_acceptance": False,
                "source_paths": {k: spec[k] for k in ("report", "model", "response", "all_body_audit", "parent_serialization")},
                "source_sha256": {k: hashes[spec[k]] for k in ("report", "model", "response", "all_body_audit", "parent_serialization")},
            })
        else:
            terminal = load_json(spec["terminal"])
            all_body = load_json(spec["all_body_audit"])
            if terminal.get("status") != "PASS_PARENT_K12_REAR_DIRECT_RESPONSE_AND_ALL50" or terminal.get("response_usable_for_conditional_joint_checks") is not True or terminal.get("independent_body_and_global_balances_passed") is not True:
                raise AssertionError("K12 parent terminal assessment is not accepted")
            if all_body.get("status") not in ("PASS_PARENT_ALL_BODY_RESPONSE_SUMS", "PASS_PARENT_ALL_50_BODY_RESPONSE_SUMS"):
                raise AssertionError("K12 parent all-body audit is not accepted")
            case_auth.append({
                "case_id": case_id,
                "conditional_response_status": terminal["status"],
                "parent_all_body_audit_status": all_body["status"],
                "usable_for_conditional_corner_demands": True,
                "joint_acceptance": False,
                "source_paths": {k: spec[k] for k in ("report", "model", "response", "terminal", "all_body_audit")},
                "source_sha256": {k: hashes[spec[k]] for k in ("report", "model", "response", "terminal", "all_body_audit")},
            })

        if len(model["nodes"]) == 0:
            raise AssertionError(f"missing coordinates in {case_id} source model")
        for body, target in TARGETS.items():
            source_body_wrench(model, body)
            axis_row = model["body_geometry"][body]["geometry_record"]
            if axis_row["axis"] != target["axis"]:
                raise AssertionError(f"expected the source {body} axis to be global +Z")
            body_nodes = {str(n) for n in model["physical_body_nodes"][body]}
            if body_nodes != set(model["physical_body_loads"][body]):
                raise AssertionError(f"discrete body load node coverage changed for {case_id}/{body}")

        prepared[case_id] = (report, response, model)

        for i, (report_inc, response_inc) in enumerate(zip(report["increments"], response["increments"])):
            if not report_increment_gate_passed(report_inc):
                raise AssertionError(f"corner report body/interval balance gate failed for {case_id} at {report_inc.get('time')}")
            if any(response_inc.get({"raw_body_and_global_balance_passed":"raw_balance_passed", "rounding_interval_body_and_global_balance_passed":"rounding_interval_balance_passed"}.get(gate,gate)) is not True for gate in REQUIRED_RESPONSE_GATES):
                raise AssertionError(f"response increment gate failed for {case_id} at {response_inc.get('time')}")
            if report_inc.get("time") != response_inc.get("time") or report_inc.get("load_factor") != response_inc.get("load_factor"):
                raise AssertionError(f"report/response increment identity mismatch for {case_id}")
            if len(report_inc.get("all_corner_interfaces", [])) != 338:
                raise AssertionError(f"corner interface count changed for {case_id}")
            if len(response_inc.get("physical_connection_forces", {})) != 1466:
                raise AssertionError(f"physical connection force inventory count changed for {case_id}")
            floor_rows = response_inc.get("exact_floor_tangent_reactions", [])
            floor_target = [
                row for row in floor_rows
                if row.get("first") in TARGETS or row.get("second") in TARGETS
            ]
            if floor_target:
                raise AssertionError(f"direct floor tangent action appears on screened member in {case_id}")

            interface_rows = report_inc["all_corner_interfaces"]
            response_rows = response_inc["physical_connection_forces"]
            for body in TARGETS:
                target_report_rows = rows_for_body(interface_rows, body)
                target_response_rows = [
                    (name, row) for name, row in response_rows.items()
                    if row.get("first") == body or row.get("second") == body
                ]
                report_names = {row.get("source_connection_name", row.get("axis_id")) for row in target_report_rows}
                response_names = {name for name, _ in target_response_rows}
                if report_names != response_names:
                    raise AssertionError(f"response/export owner inventory mismatch for {case_id}/{body}: {report_names ^ response_names}")
                if len(target_report_rows) != (24 if body == "knee_outer_left_spine" else 16):
                    raise AssertionError(f"unexpected target interface count {case_id}/{body}: {len(target_report_rows)}")
                for row in target_report_rows:
                    source_name = row.get("source_connection_name", row.get("axis_id"))
                    physical = response_rows[source_name]
                    if physical.get("first") != row.get("first") or physical.get("second") != row.get("second"):
                        raise AssertionError(f"owner mismatch between response/export for {case_id}/{source_name}")
                    close_vec(physical["force_on_first_xyz_n"], row["force_on_first_xyz_n"], 1e-10, f"first force {case_id}/{source_name}")
                    close_vec(physical["force_on_second_xyz_n"], row["force_on_second_xyz_n"], 1e-10, f"second force {case_id}/{source_name}")

            step_actions: dict[str, list[dict]] = {}
            step_loads: dict[str, list[dict]] = {}
            step_body_balance = {}
            for body in TARGETS:
                actions, loads = body_action_data(model, interface_rows, body, float(report_inc["load_factor"]))
                step_actions[body] = actions
                step_loads[body] = loads
                points_forces_couples = [
                    (a["owner_point_global_xyz_mm"], a["force_xyz_n"], a["free_moment_xyz_nmm"])
                    for a in actions + loads
                ]
                body_force, body_moment = full_wrench(points_forces_couples, [0.0, 0.0, 0.0])
                force_radius = sum_vectors([a["force_rounding_radius_xyz_n"] for a in actions + loads])
                moment_radius = sum_vectors([
                    force_radius_to_moment_radius(a["owner_point_global_xyz_mm"], a["force_rounding_radius_xyz_n"])
                    for a in actions + loads
                ])
                if any(abs(body_force[j]) > force_radius[j] + VECTOR_CHECK_TOLERANCE_N for j in range(3)):
                    raise AssertionError(f"independent force closure fails for {case_id}/{body} at {report_inc['time']}: {body_force}, radius {force_radius}")
                if any(abs(body_moment[j]) > moment_radius[j] + MOMENT_CHECK_TOLERANCE_NMM for j in range(3)):
                    raise AssertionError(f"independent moment closure fails for {case_id}/{body} at {report_inc['time']}: {body_moment}, radius {moment_radius}")
                max_couple = max((abs(v) for a in actions for v in a["serialized_endpoint_moment_roundoff_xyz_nmm"]), default=0.0)
                step_body_balance[body] = {
                    "passed_force_rounding_interval": True,
                    "passed_moment_force_rounding_interval": True,
                    "connection_endpoint_count": len(actions),
                    "source_discrete_load_node_count": len(loads),
                    "force_residual_xyz_n": body_force,
                    "force_rounding_radius_xyz_n": force_radius,
                    "moment_residual_about_global_origin_xyz_nmm": body_moment,
                    "moment_rounding_radius_about_global_origin_xyz_nmm": moment_radius,
                    "maximum_serialized_free_couple_magnitude_nmm": max_couple,
                    "direct_floor_tangent_endpoint_count": len(floor_target),
                }

            for body, target in TARGETS.items():
                geometry_row = model["body_geometry"][body]["geometry_record"]
                start = geometry_row["start"]
                datum_x_y = [float(start[0]), float(start[1])]
                stations = []
                for axis_id, group_id, z in target["stations"]:
                    datum = [datum_x_y[0], datum_x_y[1], z]
                    net = net_inputs[body]
                    action_result = cut_partition(step_actions[body] + step_loads[body], z, datum)
                    qminus = action_result["just_below"]
                    qplus = action_result["just_above"]
                    low_minus = qminus["lower_segment_material_action"]
                    up_minus = qminus["upper_segment_material_action"]
                    low_plus = qplus["lower_segment_material_action"]
                    up_plus = qplus["upper_segment_material_action"]
                    for side_name, low, high in (("just_below", low_minus, up_minus), ("just_above", low_plus, up_plus)):
                        whole_force, whole_moment, whole_fr, whole_mr = sum_actions(step_actions[body] + step_loads[body], datum)
                        close_vec(add(low["force_xyz_n"], high["force_xyz_n"]), [-v for v in whole_force], 1e-7, f"opposite force residual identity {case_id}/{body}/{z}/{side_name}")
                        close_vec(add(low["moment_xyz_nmm"], high["moment_xyz_nmm"]), [-v for v in whole_moment], 1e-5, f"opposite moment residual identity {case_id}/{body}/{z}/{side_name}")
                        assert max(map(abs,whole_force)) <= .1 and max(map(abs,whole_moment)) <= 2., "Unchanged physical resultant limits"
                        sides_residual = {"force_xyz_n": [-v for v in whole_force], "moment_xyz_nmm": [-v for v in whole_moment], "force_rounding_radius_xyz_n":whole_fr,"moment_rounding_radius_xyz_nmm":whole_mr,"physical_limits_N_Nmm":[.1,2.],"note":"The two reconstructed actions sum to minus the printed whole-body residual, not exact zero; no source reaction is corrected."}
                        action_result[side_name]["opposite_side_reconstruction_residual"] = sides_residual
                    coincident = action_result["plane_coincident_external_wrench"]["point_actions"]
                    expected_plane_roles = {"physical_bolt_outer_seat_tension", "candidate_bolt_lateral_plane"}
                    roles = {a["role"] for a in coincident if a["source_type"] == "physical_connection_force"}
                    if roles != expected_plane_roles:
                        raise AssertionError(f"unexpected plane-coincident roles at {case_id}/{body}/{z}: {roles}")
                    if any(a["source_type"] == "source_discrete_body_load" for a in coincident):
                        raise AssertionError(f"source load node coincides with the connector station at {case_id}/{body}/{z}")
                    stations.append({
                        "station_id": f"{axis_id}_section",
                        "group_id": group_id,
                        "axis_id": axis_id,
                        "member_id": body,
                        "section_plane": "XY; normal +global Z",
                        "station_z_global_mm": z,
                        "cut_datum_global_xyz_mm": datum,
                        "normal_global_xyz": [0.0, 0.0, 1.0],
                        "nominal_net_section_area_mm2_from_pinned_geometry_screen": net["candidate_net_area_mm2"],
                        "net_area_note": "geometry-only context from the existing source screen; no section stress or resistance is computed",
                        "cut_resultant_sign_convention": "Report each material action on the isolated lower/upper segment. Positive N is +global Z on the lower segment; V is global XY force; M is right-hand-rule global moment about the stated datum.",
                        "one_sided_cut_results": action_result,
                    })

                all_rows.append({
                    "case_id": case_id,
                    "time": report_inc["time"],
                    "load_factor": report_inc["load_factor"],
                    "all_corner_export_rows": len(interface_rows),
                    "source_physical_connection_force_rows": len(response_rows),
                    "body": body,
                    "body_endpoint_role_counts": endpoint_count_by_role(interface_rows, body),
                    "body_equilibrium": step_body_balance[body],
                    "section_stations": stations,
                })

    # Per-station component envelopes summarize the bounded conditional results.
    envelope = {}
    for body in TARGETS:
        station_values = {}
        for row in all_rows:
            if row["body"] != body:
                continue
            for station in row["section_stations"]:
                key = station["station_id"]
                comps = station_values.setdefault(key, {
                    "member_id": body,
                    "axis_id": station["axis_id"],
                    "group_id": station["group_id"],
                    "station_z_global_mm": station["station_z_global_mm"],
                    "net_area_mm2": station["nominal_net_section_area_mm2_from_pinned_geometry_screen"],
                    "max_abs_component_across_all_states": {
                        "just_below_lower_segment": {"N_global_Z_n": 0.0, "V_global_X_n": 0.0, "V_global_Y_n": 0.0, "Mx_nmm": 0.0, "My_nmm": 0.0, "Mz_nmm": 0.0},
                        "just_above_lower_segment": {"N_global_Z_n": 0.0, "V_global_X_n": 0.0, "V_global_Y_n": 0.0, "Mx_nmm": 0.0, "My_nmm": 0.0, "Mz_nmm": 0.0},
                    },
                })
                for side, location in (("just_below", "just_below_lower_segment"), ("just_above", "just_above_lower_segment")):
                    demand = station["one_sided_cut_results"][side]["lower_segment_material_action"]
                    vals = {
                        "N_global_Z_n": demand["force_xyz_n"][2],
                        "V_global_X_n": demand["force_xyz_n"][0],
                        "V_global_Y_n": demand["force_xyz_n"][1],
                        "Mx_nmm": demand["moment_xyz_nmm"][0],
                        "My_nmm": demand["moment_xyz_nmm"][1],
                        "Mz_nmm": demand["moment_xyz_nmm"][2],
                    }
                    for key_name, value in vals.items():
                        comps["max_abs_component_across_all_states"][location][key_name] = max(
                            comps["max_abs_component_across_all_states"][location][key_name], abs(value)
                        )
        envelope[body] = [station_values[k] for k in sorted(station_values)]

    return {
        "schema": "current_corner_conditional_section_demands/v1",
        "status": "PASS_SOURCE_BOUND_CONDITIONAL_SECTION_RESULTANTS_ONLY",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": {
            "cases": list(CASE_SOURCES),
            "increments_per_case": 7,
            "screened_members": list(TARGETS),
            "stations_per_member": {body: len(target["stations"]) for body, target in TARGETS.items()},
            "section_count_per_case_increment": sum(len(target["stations"]) for target in TARGETS.values()),
            "cut_side_states": ["just_below", "just_above"],
            "included_action_sources": [
                "all source-bound physical_connection_forces incident on the target body in the authenticated corner export (contacts, candidate bolt planes/ties, and any other owner action)",
                "source model physical_body_loads at their explicit nodes, multiplied by that increment's load_factor",
                "exact_floor_tangent_reactions were audited at each increment; zero rows act directly on either screened body",
            ],
            "excluded": [
                "native RF ghosts or unowned residual actions",
                "actions on other members that do not act on the screened body",
                "load distribution within a bore, across a plane, or between physical connector routes",
                "wood stresses, strength values, resistance, DCR, complete-joint acceptance, and qualification",
            ],
        },
        "method": {
            "force_sign": "Each physical endpoint vector is force on its named owner; first/second endpoint vectors are used as serialized in the authenticated export.",
            "body_load_scaling": "physical_body_loads are the unit/full-factor source reference discrete body loads; multiply by the response increment load_factor. This scaling is checked by independent body equilibrium at every state.",
            "cut_normal_and_axes": "Sections are XY planes normal to source body axis +global Z; N is global Z and V is global XY.",
            "cut_datum": "Each section resultant is transported to the section's centerline point [body_geometry.start.x, body_geometry.start.y, station_z].",
            "one_sided_limit": "q^- excludes station-coincident point actions from the lower segment and includes them on the upper segment. q^+ includes them on the lower segment and excludes them from the upper segment. Points within 1e-6 mm of q are classified as coincident to account for serialized coordinate roundoff.",
            "moment_transport": "M_datum = (point - datum) cross force + serialized endpoint free moment at its owner datum. The largest serialized free couple is recorded; no bore/contact stress field is inferred.",
            "rounding_intervals": "Connector force half-last-place component radii are summed; their cross-product moment radii are transported to each global-origin/cut datum. Source model load vectors/coordinates are treated as exact serialized inputs for this arithmetic.",
            "closure": "At every state each screened body's connector endpoints plus factor-scaled source discrete loads close force and moment within propagated connector-force rounding intervals. The two segment cut actions are independently checked to be opposite within numerical tolerance.",
        },
        "case_authentication": case_auth,
        "source_hashes": hashes,
        "section_geometry_source": {
            "path": GEOMETRY_SCREEN,
            "sha256": hashes[GEOMETRY_SCREEN],
            "source_producer_path": GEOMETRY_PRODUCER,
            "source_producer_sha256": hashes[GEOMETRY_PRODUCER],
            "geometry_revision_id": geometry["geometry_revision_id"],
            "candidate_net_section_inputs": net_inputs,
        },
        "not_calculated_or_claimed": [
            "member stress or strength",
            "NDS/EC5 net-tension, bending, shear, bearing, splitting, or interaction resistance",
            "material grade/species/moisture adjusted resistance",
            "local hole-wall/contact stress and distribution of bolt-plane load through the section",
            "physical gravity distribution beyond the explicit source-model discrete nodal load pattern",
            "complete BG001/BG003/BG045 joint acceptance or climber/design qualification",
        ],
        "remaining_material_and_mechanics_gaps": [
            "No source-bound member-specific adjusted wood strengths or bending section modulus/neutral axis are established for these exact members.",
            "No adopted net-tension resistance basis is established for these connection topologies.",
            "The multi-bore BG003 section does not provide a validated splitting topology/method or a local bearing-to-net-section stress-transfer field.",
            "The reported body load pattern is the analytical source-discrete gravity distribution, not a measured physical mass distribution.",
            "Resultants at a bore center plane retain an explicit point-force jump; the source data do not support spreading that jump or inferring a singular/local stress field.",
        ],
        "per_increment_body_sections": all_rows,
        "seven_state_absolute_component_envelopes_on_lower_segment": envelope,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="write the reproducible result in this packet")
    group.add_argument("--verify", action="store_true", help="compare the existing result byte-for-byte")
    args = parser.parse_args()
    data = result()
    encoded = (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if args.write:
        HERE.mkdir(parents=True, exist_ok=True)
        OUT.write_bytes(encoded)
        print(f"wrote {OUT.relative_to(ROOT)} ({len(data['per_increment_body_sections'])} body-state rows)")
    else:
        if not OUT.exists():
            raise SystemExit(f"missing result: {OUT.relative_to(ROOT)}")
        if OUT.read_bytes() != encoded:
            raise SystemExit("verification failed: result differs; run --write, inspect, and repin")
        print(f"verified {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
