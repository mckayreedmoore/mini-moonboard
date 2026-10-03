#!/usr/bin/env python3
"""Build a replayable three-case signed axial-tie and washer-seat register."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
SOURCE_PINS = HERE / "source-pins.json"
SOURCE_PINS_SHA256 = "f605387a7d854b2baef0045d11c1defa0890f15b45a5f5ceb23a05eb609a1b5c"
OUTPUT = HERE / "axial-seat-register.json"

CASE_SPECS = {
    "a12-rear": {
        "report": PACKET / "current-corner-native-demand-export-attempt03/corner-demand-report.json",
        "expected_sha256": "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
        "register_status": "PASS_CONDITIONAL_REAR_RESPONSE_WITH_CORNER_EXPORT",
        "report_status": "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY",
    },
    "a1-rear": {
        "report": PACKET / "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json",
        "expected_sha256": "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce",
        "register_status": "PASS_CONDITIONAL_RESPONSE_WITH_SIGNED_CORNER_EXPORT",
        "report_status": "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY",
    },
    "k12-rear": {
        "report": PACKET / "current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json",
        "expected_sha256": "a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0",
        "register_status": "PASS_CONDITIONAL_K12_REAR_DIRECT_MASTER_RESPONSE_WITH_CORNER_EXPORT",
        "report_status": "PASS_K12_REAR_NUMERICAL_CORNER_DEMAND_REPORT_ONLY",
    },
}

EXPECTED_GROUPS = {
    "BG001": {"knee_outer_left_post_1", "knee_outer_left_post_2"},
    "BG003": {"knee_outer_left_side_1", "knee_outer_left_side_2"},
    "BG045": {"knee_outer_left_inner_header_1", "knee_outer_left_inner_header_2"},
}
EXPECTED_AXES = set().union(*EXPECTED_GROUPS.values())
SIGN_EPSILON_N = 1e-9
NUMERIC_TOL = 1e-8


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"axial-seat source/method gate failed: {message}")


def close(a: float, b: float, *, abs_tol: float = NUMERIC_TOL) -> bool:
    return math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=abs_tol)


def verify_source_pins() -> tuple[dict, dict, dict]:
    require(sha256(SOURCE_PINS) == SOURCE_PINS_SHA256,
            "source-pins.json hash changed")
    pins = read_json(SOURCE_PINS)
    require(pins.get("schema") == "current_corner_three_case_axial_seat_source_pins/v1",
            "source pin schema")
    for item in pins.get("files", []):
        path = ROOT / item["path"]
        require(path.is_file(), f"pinned source missing: {item['path']}")
        actual = sha256(path)
        require(actual == item["sha256"],
                f"pinned source changed: {item['path']} ({actual})")

    register_pin = pins["source_response_register"]
    register_path = ROOT / register_pin["path"]
    producer_path = ROOT / register_pin["producer_path"]
    require(sha256(register_path) == register_pin["sha256"],
            "attempt04 source response register changed")
    require(sha256(producer_path) == register_pin["producer_sha256"],
            "attempt04 source response register producer changed")
    register = read_json(register_path)
    require(register.get("case_count") == 6 and
            register.get("joint_accepted") is False and
            register.get("six_case_envelope_complete") is False,
            "attempt04 register scope/acceptance boundary")

    pinned_by_path = {item["path"]: item["sha256"] for item in pins["files"]}
    for path, expected in register.get("source_pins_sha256", {}).items():
        if path in pinned_by_path:
            require(pinned_by_path[path] == expected,
                    f"local pin disagrees with response register: {path}")
    for case_id, spec in CASE_SPECS.items():
        report_path = rel(spec["report"])
        require(pinned_by_path.get(report_path) == spec["expected_sha256"],
                f"accepted {case_id} demand report is not in pinned source set")
    return pins, register, pinned_by_path


def report_register_row(register: dict, case_id: str, spec: dict) -> dict:
    rows = [row for row in register["cases"] if row.get("case_id") == case_id]
    require(len(rows) == 1, f"one response-register row for {case_id}")
    row = rows[0]
    require(row.get("status") == spec["register_status"],
            f"accepted response-register status for {case_id}")
    require(row.get("corner_demands_usable") is True and
            row.get("conditional_physical_case_forces_usable") is True and
            row.get("physical_failure_inferred") is False,
            f"conditional demand-use boundary for {case_id}")
    require(row.get("confirmed_terminal") is True and
            row.get("native_returncode") == 0 and
            row.get("increment_count") == 7 and
            row.get("full_load_factor") == 1.0,
            f"terminal seven-increment coverage for {case_id}")
    if case_id == "k12-rear":
        prior = row.get("preserved_prior_rejected_response", {})
        require(prior.get("status") == "REJECTED_PROPOSED_SELECTED_BEARING_RESPONSE_COMPATIBILITY" and
                prior.get("corner_demands_usable") is False,
                "K12 demand comes from accepted direct-master response, not rejected attempt03")
    return row


def source_artifact_summary(report: dict, case_id: str) -> dict:
    if case_id == "a12-rear":
        auth = report["authenticated_source_case"]
        return {
            "input_model_sha256": auth["input_model_json_sha256"],
            "response_sha256": auth["response_audit_json_sha256"],
            "response_audit_path": auth["response_audit_json_path"],
            "audited_deck_sha256": auth["audited_deck_sha256"],
            "audited_native_data_sha256": auth["audited_native_data_sha256"],
        }
    if case_id == "a1-rear":
        auth = report["authenticated_source_case"]
        return {
            "input_model_sha256": auth["selected_input_model_sha256"],
            "response_sha256": auth["response_audit_sha256"],
            "response_audit_path": auth["response_audit_path"],
            "selected_input_deck_sha256": auth["selected_input_deck_sha256"],
            "native_dat_sha256": auth["native_dat_sha256"],
            "external_case_context_sha256": auth["external_case_context_sha256"],
        }
    auth = report["authenticated_sources"]
    return {
        "native_model_path": auth["native_model_path"],
        "native_model_sha256": auth["native_model_sha256"],
        "response_audit_path": auth["response_audit_path"],
        "response_audit_sha256": auth["response_audit_sha256"],
        "all_body_audit_path": auth["all_body_audit_path"],
        "all_body_audit_sha256": auth["all_body_audit_sha256"],
        "parent_terminal_assessment_path": auth["parent_terminal_assessment_path"],
        "parent_terminal_assessment_sha256": auth["parent_terminal_assessment_sha256"],
        "input_deck_sha256": auth["input_deck_sha256"],
        "native_deck_sha256": auth["native_deck_sha256"],
    }


def map_groups_and_bolts(increment: dict) -> tuple[dict, dict]:
    groups = increment.get("primary_physical_bolt_groups", {})
    require(set(groups) == set(EXPECTED_GROUPS), "exact three corner tie groups")
    group_by_axis: dict[str, str] = {}
    bolt_by_axis: dict[str, dict] = {}
    for group_id, group in groups.items():
        require(set(group.get("axis_ids", [])) == EXPECTED_GROUPS[group_id],
                f"{group_id} axis inventory")
        require(group.get("physical_bolt_count") == 2 and
                group.get("outer_seat_tie_count") == 2,
                f"{group_id} physical bolt/tie inventory")
        for bolt in group.get("bolts", []):
            axis_id = bolt["axis_id"]
            require(axis_id not in bolt_by_axis, f"unique physical tie axis {axis_id}")
            group_by_axis[axis_id] = group_id
            bolt_by_axis[axis_id] = bolt
    require(set(bolt_by_axis) == EXPECTED_AXES, "exact six outer-seat physical ties")
    return group_by_axis, bolt_by_axis


def classify_signed_tie(value: float) -> str:
    if value > SIGN_EPSILON_N:
        return "tension"
    if value < -SIGN_EPSILON_N:
        return "compression"
    return "zero_within_1e-9_N"


def source_seat_record(row: dict, tie: dict, source_index: int) -> dict:
    signed_t = float(tie["signed_axis_force_on_first_n"])
    seat_t = float(row["signed_outer_seat_tie_action_n"])
    require(close(seat_t, signed_t, abs_tol=1e-9),
            f"axis {row['axis_id']} tie and seat signed actions agree")
    area = float(row["modeled_outer_washer_annular_area_mm2"])
    pressure = float(row["conditional_full_annulus_uniform_average_pressure_mpa"])
    require(area > 0.0, f"positive modeled washer annular area for {row['axis_id']}")
    expected_signed_pressure = signed_t / area
    require(close(pressure, expected_signed_pressure, abs_tol=2e-12),
            f"{row['axis_id']} source average pressure equals signed T/A")
    force = [float(x) for x in row["seat_force_on_member_xyz_n"]]
    point = [float(x) for x in row["seat_point_global_xyz_mm"]]
    require(len(force) == 3 and len(point) == 3,
            f"three-component force and global seat point for {row['axis_id']}")
    return {
        "source_seat_row_index": source_index,
        "physical_member": row["physical_member"],
        "seat_role": row["seat_role"],
        "seat_point_global_xyz_mm": point,
        "source_force_on_member_xyz_n": force,
        "signed_tie_action_n": seat_t,
        "signed_tie_state": classify_signed_tie(seat_t),
        "modeled_full_annulus_area_mm2": area,
        "source_signed_uniform_average_pressure_mpa": pressure,
        "absolute_uniform_average_pressure_magnitude_mpa": abs(pressure),
        "pressure_interpretation": "conditional full modeled CAD annulus uniform-average conversion only; not local pressure, verified support, or washer/wood qualification",
        "conditional_fc_perp_reference_n_as_exported": row.get("conditional_fc_perp_reference_n"),
        "conditional_fc_perp_reference_status_as_exported": row.get("conditional_fc_perp_reference_status"),
        "support_area_status_as_exported": row.get("support_area_status"),
    }


def verify_seat_pair(tie: dict, seats: list[dict], axis_id: str) -> None:
    require(len(seats) == 2, f"two physical outer seats for {axis_id}")
    require({row["seat_role"] for row in seats} == {"head_washer_seat", "nut_washer_seat"},
            f"head and nut outer-seat identities for {axis_id}")
    first, second = tie.get("first"), tie.get("second")
    require({row["physical_member"] for row in seats} == {first, second},
            f"outer seats close onto named tie receivers for {axis_id}")
    by_member = {row["physical_member"]: row for row in seats}
    first_seat = by_member[first]
    second_seat = by_member[second]
    for i in range(3):
        require(close(first_seat["source_force_on_member_xyz_n"][i], tie["force_on_first_xyz_n"][i], abs_tol=1e-8),
                f"first seat action matches tie source for {axis_id}")
        require(close(second_seat["source_force_on_member_xyz_n"][i], tie["force_on_second_xyz_n"][i], abs_tol=1e-8),
                f"second seat action matches tie source for {axis_id}")
        require(close(first_seat["source_force_on_member_xyz_n"][i] +
                      second_seat["source_force_on_member_xyz_n"][i], 0.0, abs_tol=1e-8),
                f"opposite outer seat force vectors for {axis_id}")
    require(close(first_seat["signed_tie_action_n"], second_seat["signed_tie_action_n"], abs_tol=1e-9),
            f"common signed axial tie scalar at both outer seats for {axis_id}")


def axis_geometry(washer: dict, axis_id: str) -> dict:
    rows = [row for row in washer["axes"] if row.get("axis_id") == axis_id]
    require(len(rows) == 1, f"one washer geometry record for {axis_id}")
    return rows[0]


def verify_geometry_identity(seats: list[dict], geometry: dict, axis_id: str) -> None:
    require(close(geometry["modeled_outer_washer_annular_area_mm2"],
                  seats[0]["modeled_full_annulus_area_mm2"], abs_tol=2e-7),
            f"{axis_id} CAD annular area matches washer screen")
    outer = geometry.get("outer_seats", [])
    require(len(outer) == 2, f"{axis_id} washer geometry has two seat records")
    geom_identity = {
        (row["outer_receiver_member_id"], row["seat_role"], tuple(row["seat_point_xyz_mm"]))
        for row in outer
    }
    demand_identity = {
        (row["physical_member"], row["seat_role"], tuple(row["seat_point_global_xyz_mm"]))
        for row in seats
    }
    require(len(geom_identity) == 2 and len(demand_identity) == 2,
            f"unique physical washer-seat identity for {axis_id}")
    for member, role, point in demand_identity:
        matches = [item for item in geom_identity if item[0] == member and item[1] == role]
        require(len(matches) == 1 and all(close(x, y, abs_tol=2e-7) for x, y in zip(point, matches[0][2])),
                f"{axis_id} export seat identity matches pinned washer geometry")


def prior_full_load_ties(screen: dict, case_id: str) -> dict[str, float]:
    result = {}
    for axis in screen.get("axes", []):
        key = "positive_outer_seat_tie_tension_demand_n" if case_id == "a12-rear" else "a1_rear_positive_tie_tension_demand_n"
        require(axis.get("axis_id") not in result, f"unique prior screen axis {axis.get('axis_id')}")
        result[axis["axis_id"]] = float(axis[key])
    require(set(result) == EXPECTED_AXES, f"prior {case_id} screen covers all six ties")
    return result


def build_register() -> dict:
    pins, source_register, pinned_by_path = verify_source_pins()
    washer = read_json(PACKET / "current-corner-washer-seat-screen-attempt01/seat-screen.json")
    a12_screen = read_json(PACKET / "current-corner-axial-tie-seat-screen-attempt01/screen.json")
    a1_screen = read_json(PACKET / "current-corner-a1-rear-axial-seat-screen-attempt01/screen.json")
    a12_parent = read_json(PACKET / "current-corner-axial-seat-parent-audit-attempt01/audit.json")
    a1_parent = read_json(PACKET / "current-corner-a1-axial-seat-parent-audit-attempt01/audit.json")
    require(washer.get("status") == "bounded_conditional_modeled_seat_geometry_only",
            "pinned washer geometry screen status")
    require(a12_parent.get("status") == "PASS_PARENT_CONDITIONAL_AXIAL_SEAT_ARITHMETIC_AND_INVENTORY" and
            a12_parent.get("joint_accepted") is False and a12_parent.get("bolt_count") == 6 and
            a12_parent.get("seat_count") == 12,
            "reused A12 axial-seat arithmetic audit status and scope")
    require(a1_parent.get("status") == "PASS_PARENT_A1_CONDITIONAL_AXIAL_SEAT_ARITHMETIC_AND_INVENTORY" and
            a1_parent.get("joint_accepted") is False and a1_parent.get("bolt_count") == 6 and
            a1_parent.get("seat_count") == 12,
            "reused A1 axial-seat arithmetic audit status and scope")
    a12_old_ties = prior_full_load_ties(a12_screen, "a12-rear")
    a1_old_ties = prior_full_load_ties(a1_screen, "a1-rear")

    case_records = []
    states = []
    state_by_case_factor = {}
    per_axis_max: dict[str, dict] = {
        axis_id: {"maximum_tension_demand_n": None, "case_id": None, "load_factor": None,
                  "time": None, "maximum_seat_average_pressure_mpa": None}
        for axis_id in EXPECTED_AXES
    }
    sign_counts = {"tension": 0, "compression": 0, "zero_within_1e-9_N": 0}
    expected_report_hashes = {}

    for case_id, spec in CASE_SPECS.items():
        report_path = spec["report"]
        report_sha = sha256(report_path)
        require(report_sha == spec["expected_sha256"], f"{case_id} corner-demand report hash")
        report = read_json(report_path)
        require(report.get("case_id") == case_id and report.get("status") == spec["report_status"],
                f"{case_id} source-bound report identity/status")
        require(report.get("actual_case_demand_usable_for_conditional_joint_checks") is True,
                f"{case_id} report conditional demand usability")
        require(len(report.get("increments", [])) == 7 and
                float(report["increments"][-1].get("load_factor", -1.0)) == 1.0,
                f"{case_id} full-load and seven-increment report coverage")
        if "response_audit_final_load_factor" in report:
            require(report["response_audit_final_load_factor"] == 1.0 and
                    report["response_audit_increment_count"] == 7,
                    f"{case_id} exported root increment summary")
        require(report.get("qualification_boundary", {}).get("complete_joint_accepted") is False and
                report.get("qualification_boundary", {}).get("qualified_for_design") is False,
                f"{case_id} report remains nonacceptance evidence")
        root_gates = report.get("response_audit_root_gates") or \
            report.get("direct_master_response_audit", {}).get("root_gates", {})
        require(root_gates and all(value is True for value in root_gates.values()),
                f"{case_id} source report root response gates")
        register_row = report_register_row(source_register, case_id, spec)
        require(register_row.get("increment_count") == len(report["increments"]),
                f"{case_id} source register/report increment count match")
        case_states = []
        last_factor = -math.inf

        for ordinal, increment in enumerate(report["increments"], start=1):
            load_factor = float(increment["load_factor"])
            require(load_factor > last_factor, f"{case_id} increments ordered by load factor")
            last_factor = load_factor
            gates = increment.get("response_audit_gates", {})
            require(gates and all(value is True for value in gates.values()),
                    f"{case_id} increment {ordinal} source response gates")
            require(increment.get("all_five_corner_bodies_raw_and_interval_balance_passed") is True,
                    f"{case_id} increment {ordinal} five-body balance")
            group_by_axis, bolt_by_axis = map_groups_and_bolts(increment)
            tie_interfaces = [row for row in increment["all_corner_interfaces"]
                              if row.get("role") == "physical_bolt_outer_seat_tension" and
                              row.get("axis_id") in EXPECTED_AXES]
            ties_by_axis = {row["axis_id"]: row for row in tie_interfaces}
            require(len(ties_by_axis) == 6 and set(ties_by_axis) == EXPECTED_AXES,
                    f"{case_id} increment {ordinal} exact six source tie actions")
            seat_rows = increment.get("outer_washer_seats", [])
            require(len(seat_rows) == 12, f"{case_id} increment {ordinal} exact twelve exported seats")
            state_ties = []

            for axis_id in sorted(EXPECTED_AXES):
                tie = ties_by_axis[axis_id]
                bolt = bolt_by_axis[axis_id]
                group_id = group_by_axis[axis_id]
                require(tie.get("axis_id") == axis_id and tie.get("role") == "physical_bolt_outer_seat_tension",
                        f"{case_id} {axis_id} source tie role")
                action_name = f"{axis_id}/outer-seat-axial-tie"
                require(tie.get("source_connection_name") == action_name,
                        f"{case_id} {axis_id} source connection name")
                signed = float(tie["signed_axis_force_on_first_n"])
                sign = classify_signed_tie(signed)
                sign_counts[sign] += 1
                tie_seats = [row for row in seat_rows if row.get("axis_id") == axis_id]
                require(len(tie_seats) == 2, f"{case_id} increment {ordinal} two seats on {axis_id}")
                seats = [source_seat_record(row, tie, index)
                         for index, row in enumerate(seat_rows)
                         if row.get("axis_id") == axis_id]
                verify_seat_pair(tie, seats, axis_id)
                geom = axis_geometry(washer, axis_id)
                verify_geometry_identity(seats, geom, axis_id)
                unit_axis = [float(x) for x in bolt["head_to_nut_unit_global_xyz"]]
                require(len(unit_axis) == 3 and math.isclose(sum(x*x for x in unit_axis), 1.0,
                                                              rel_tol=1e-7, abs_tol=1e-7),
                        f"{case_id} {axis_id} source head-to-nut axis unit vector")

                if case_id in ("a12-rear", "a1-rear") and load_factor == 1.0:
                    prior = a12_old_ties if case_id == "a12-rear" else a1_old_ties
                    require(axis_id in prior and close(signed, prior[axis_id], abs_tol=1e-9),
                            f"{case_id} {axis_id} full-load tie matches reused prior screen")

                tie_record = {
                    "axis_id": axis_id,
                    "group_id": group_id,
                    "source_connection_name": tie["source_connection_name"],
                    "source_role": tie["role"],
                    "tie_sign_convention": "source role is physical_bolt_outer_seat_tension; signed_axis_force_on_first_n is preserved as reported; positive=tension, negative=compression, zero=zero",
                    "signed_tie_action_n": signed,
                    "signed_tie_state": sign,
                    "first_receiver_member": tie["first"],
                    "second_receiver_member": tie["second"],
                    "source_force_on_first_xyz_n": [float(x) for x in tie["force_on_first_xyz_n"]],
                    "source_force_on_second_xyz_n": [float(x) for x in tie["force_on_second_xyz_n"]],
                    "continuous_receiver_members_from_source_bolt": list(bolt["continuous_receiver_members"]),
                    "axis_datum_global_xyz_mm": [float(x) for x in bolt["axis_datum_global_xyz_mm"]],
                    "head_to_nut_unit_global_xyz": unit_axis,
                    "seats": seats,
                }
                state_ties.append(tie_record)
                if sign == "tension":
                    magnitude = signed
                    seat_pressure = max(row["absolute_uniform_average_pressure_magnitude_mpa"]
                                        for row in seats)
                    current = per_axis_max[axis_id]["maximum_tension_demand_n"]
                    if current is None or magnitude > current:
                        per_axis_max[axis_id].update({
                            "maximum_tension_demand_n": magnitude,
                            "case_id": case_id,
                            "load_factor": load_factor,
                            "time": increment.get("time"),
                            "maximum_seat_average_pressure_mpa": seat_pressure,
                        })

            require(len(state_ties) == 6, f"{case_id} increment {ordinal} six ties")
            state = {
                "case_id": case_id,
                "source_case_register_status": register_row["status"],
                "source_demand_report_path": rel(report_path),
                "source_demand_report_sha256": report_sha,
                "increment_ordinal": ordinal,
                "time": increment.get("time"),
                "load_factor": load_factor,
                "source_response_audit_gates": gates,
                "all_five_corner_bodies_raw_and_interval_balance_passed": True,
                "ties": state_ties,
            }
            states.append(state)
            case_states.append(state)
            state_by_case_factor[(case_id, load_factor)] = state

        require(len(case_states) == 7 and case_states[-1]["load_factor"] == 1.0,
                f"{case_id} full seven source increments")
        expected_report_hashes[case_id] = report_sha
        case_records.append({
            "case_id": case_id,
            "response_register_status": register_row["status"],
            "response_register_native_directory": register_row["native_directory"],
            "demand_report_path": rel(report_path),
            "demand_report_sha256": report_sha,
            "source_native_artifact_binding": source_artifact_summary(report, case_id),
            "increment_count": len(case_states),
            "load_factors": [state["load_factor"] for state in case_states],
            "all_increment_response_and_five_corner_body_balance_gates_passed": True,
            "complete_joint_accepted": False,
        })

    require(len(states) == 21, "21 case-increment states")
    require(sum(len(state["ties"]) for state in states) == 126, "126 physical tie-state rows")
    require(sum(len(tie["seats"]) for state in states for tie in state["ties"]) == 252,
            "252 outer-seat state rows")
    require(sign_counts == {"tension": 126, "compression": 0, "zero_within_1e-9_N": 0},
            "signed tie-state inventory; preserve any non-tension state if source changes")

    for axis_id in EXPECTED_AXES:
        max_row = per_axis_max[axis_id]
        require(max_row["maximum_tension_demand_n"] is not None,
                f"observed tension state for {axis_id}")
    maximum = max(per_axis_max.items(), key=lambda item: item[1]["maximum_tension_demand_n"])
    max_axis, max_row = maximum
    max_pressure = max(row["maximum_seat_average_pressure_mpa"] for row in per_axis_max.values())

    prior_comparison = {
        "a12_rear_screen_path": rel(PACKET / "current-corner-axial-tie-seat-screen-attempt01/screen.json"),
        "a12_rear_screen_sha256": sha256(PACKET / "current-corner-axial-tie-seat-screen-attempt01/screen.json"),
        "a12_rear_parent_audit_path": rel(PACKET / "current-corner-axial-seat-parent-audit-attempt01/audit.json"),
        "a12_rear_parent_audit_sha256": sha256(PACKET / "current-corner-axial-seat-parent-audit-attempt01/audit.json"),
        "a1_rear_screen_path": rel(PACKET / "current-corner-a1-rear-axial-seat-screen-attempt01/screen.json"),
        "a1_rear_screen_sha256": sha256(PACKET / "current-corner-a1-rear-axial-seat-screen-attempt01/screen.json"),
        "a1_rear_parent_audit_path": rel(PACKET / "current-corner-a1-axial-seat-parent-audit-attempt01/audit.json"),
        "a1_rear_parent_audit_sha256": sha256(PACKET / "current-corner-a1-axial-seat-parent-audit-attempt01/audit.json"),
        "full_load_tie_demands_match_existing_a12_and_a1_screens": True,
        "k12_rear_screen_coverage_recovered_here_from_accepted_case_bound_export": True,
        "resistance_calculation_repeated_or_expanded": False,
    }
    source_pins_list = [{"path": item["path"], "sha256": item["sha256"]}
                        for item in pins["files"]]
    source_pins_list.extend([
        {"path": pins["source_response_register"]["path"],
         "sha256": pins["source_response_register"]["sha256"]},
        {"path": pins["source_response_register"]["producer_path"],
         "sha256": pins["source_response_register"]["producer_sha256"]},
    ])
    source_pins_list.append({"path": rel(SOURCE_PINS), "sha256": SOURCE_PINS_SHA256})
    producer_path = Path(__file__).resolve()
    source_pins_list.append({"path": rel(producer_path), "sha256": sha256(producer_path)})

    return {
        "schema": "current_corner_three_case_axial_seat_register/v1",
        "status": "PASS_AUTHENTICATED_AXIAL_TIE_AND_OUTER_SEAT_DEMAND_COVERAGE_ONLY",
        "scope": {
            "cases": ["a12-rear", "a1-rear", "k12-rear"],
            "groups": ["BG001", "BG003", "BG045"],
            "axis_ids": sorted(EXPECTED_AXES),
            "load_increment_states": 21,
            "physical_tie_state_rows": 126,
            "outer_washer_seat_state_rows": 252,
            "source_forces_and_signed_scalars_preserved": True,
            "pressure_quantity": "signed tie scalar divided by source modeled full CAD annular area; conditional uniform average only",
            "lateral_plane_demands_included_or_combined": False,
            "joint_or_product_accepted": False,
        },
        "source_response_register": {
            "path": pins["source_response_register"]["path"],
            "sha256": pins["source_response_register"]["sha256"],
            "producer_path": pins["source_response_register"]["producer_path"],
            "producer_sha256": pins["source_response_register"]["producer_sha256"],
            "usable_corner_demand_cases": source_register["usable_corner_demand_cases"],
            "usable_conditional_physical_response_cases": source_register["usable_conditional_physical_response_cases"],
        },
        "authenticated_cases": case_records,
        "reused_prior_screen_and_geometry_checks": prior_comparison,
        "conditional_basis_reused_without_recalculation": {
            "washer_geometry_path": rel(PACKET / "current-corner-washer-seat-screen-attempt01/seat-screen.json"),
            "washer_geometry_sha256": sha256(PACKET / "current-corner-washer-seat-screen-attempt01/seat-screen.json"),
            "cad_annular_area_mm2_by_axis": {
                axis_id: float(axis_geometry(washer, axis_id)["modeled_outer_washer_annular_area_mm2"])
                for axis_id in sorted(EXPECTED_AXES)
            },
            "a12_conditional_axial_bearing_and_bolt_reference_path": rel(PACKET / "current-corner-axial-tie-seat-screen-attempt01/README.md"),
            "a1_conditional_axial_bearing_and_bolt_reference_path": rel(PACKET / "current-corner-a1-rear-axial-seat-screen-attempt01/README.md"),
            "interpretation": "Existing DF-L No. 2 Fc-perp references apply only to their stated base-post/base-header, transverse, full-support conditional seats. Candidate-block elastic diagnostics do not assign a strength grade; BG045 block seat loads parallel to proposed grain, so Fc-perp is inapplicable there. This register carries exported reference values/status but calculates no new Fc-perp demand ratio, bolt resistance, washer resistance, or tension/lateral interaction.",
        },
        "signed_tie_state_counts": sign_counts,
        "maximum_tension_by_axis_across_these_three_cases_only": [
            {"axis_id": axis_id, **per_axis_max[axis_id]}
            for axis_id in sorted(EXPECTED_AXES)
        ],
        "maximum_tension_across_register": {
            "axis_id": max_axis,
            **max_row,
            "case_scope": "only the three authenticated A12-rear, A1-rear and K12-rear source cases; not the six-case envelope or a resistance/acceptance result",
        },
        "maximum_modeled_full_annulus_uniform_average_pressure_mpa_across_register": max_pressure,
        "exact_missing_resistance_and_interaction_inputs": [
            "Selected and delivered bolt, nut and washer product/lot identities and conformity; nominal length does not establish delivered shank, runout/thread placement, class, nut engagement or fit.",
            "Applicable bolt tensile fracture/yield design resistance, nut/thread stripping and pull-through resistance, and a reviewed combined axial/lateral/bending interaction method with controlling section and actual hardware inputs.",
            "Selected/delivered washer dimensions and opening, actual head/nut footprints, washer bending/spreading resistance, and finished seat support polygons, wood cuts/gaps/flatness and actual bearing area.",
            "Verified base-timber species/grade/condition and complete applicability inputs for any DF-L No. 2 Fc-perp comparison; candidate blocks have no assigned strength grade or perpendicular/parallel bearing resistance here.",
            "BG003 continuous three-member bolt/shared receiver compatibility and BG045 block end-bearing method; no equal-share assumption or lateral-plane capacity combination is provided by this axial register.",
        ],
        "limits": [
            "Conditional source-response demands only; this is not a physical tie force measurement or a six-case demand envelope.",
            "Average washer-seat pressure assumes the full modeled CAD annulus and uniform average; it is not a local pressure/contact solution or verified support area.",
            "Positive/negative/zero classes follow the signed scalar on the source physical_bolt_outer_seat_tension row; force vectors and raw sign are retained. The current source set contains tension only.",
            "No bolt, nut, washer, wood-seat, complete-joint or candidate acceptance is made; no actual product, wood or installation condition is inferred.",
            "No axial/lateral interaction is calculated; lateral source planes remain separate in the parent signed-demand register.",
        ],
        "source_pins": source_pins_list,
        "states": states,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="rebuild in memory and compare to saved JSON")
    parser.add_argument("--write", action="store_true", help="write the rebuilt JSON (default behavior)")
    args = parser.parse_args()
    result = build_register()
    if args.verify:
        require(OUTPUT.is_file(), "saved axial-seat-register.json exists")
        saved = read_json(OUTPUT)
        require(saved == result, "saved axial-seat-register.json matches pinned source replay")
        print("Verified 3 cases, 21 states, 126 signed tie rows, and 252 washer-seat rows")
    else:
        OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print("Wrote source-bound three-case axial tie and washer-seat register")


if __name__ == "__main__":
    main()
