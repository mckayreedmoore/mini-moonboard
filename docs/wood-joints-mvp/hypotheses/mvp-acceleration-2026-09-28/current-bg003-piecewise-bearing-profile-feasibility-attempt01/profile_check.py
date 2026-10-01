#!/usr/bin/env python3
"""Source-bound static feasibility check for one constructed BG003 profile."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
OUT = Path(__file__).resolve().parent / "profile-check.json"
TOL = 1e-6

PINS = {
    "current-corner-native-demand-export-attempt03/corner-demand-report.json":
        "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json":
        "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce",
    "current-knee-three-member-profile-attempt01/query.json":
        "5c820231ac4434e896ee708c72128672424ff158b3ee4458197cdadc1a4b0854",
    "current-knee-three-member-profile-attempt01/source-pins.json":
        "629552eba2b3dd2639df245dde56afb46dae7c01d2b2b9b1d774f98ca4a846c7",
    "current-knee-three-member-transfer-attempt01/calculation.json":
        "fb7fba30fdcdabf44c90a5ac7cfe167b6a9f659af8543a8070066f15ad45c5b1",
    "current-bg003-middle-zone-cut-feasibility-attempt01/screen.json":
        "4dbf472e7557c5828601e6545fa162b436dda32a8f12e0346f703790625f3324",
    "current-bg003-middle-zone-cut-feasibility-attempt01/screen.py":
        "7d243b4aa41fce2fb6c8c1e897cb1690afb3af10b1b9ffc5c992b1611a9f8e15",
    "bolt-groups/bolt-groups.json":
        "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4",
}

REPORTS = {
    "a12-rear": "current-corner-native-demand-export-attempt03/corner-demand-report.json",
    "a1-rear": "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(rel: str) -> Any:
    return json.loads((ROOT / BASE / rel).read_text())


def n(value: float) -> float:
    value = float(value)
    return 0.0 if abs(value) < 5e-13 else round(value, 12)


def vec(values: list[float]) -> list[float]:
    return [n(value) for value in values]


def add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b)]


def sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b)]


def scale(c: float, a: list[float]) -> list[float]:
    return [c * x for x in a]


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def norm(a: list[float]) -> float:
    return math.sqrt(dot(a, a))


def close(a: float, b: float, tol: float = TOL) -> bool:
    return abs(a - b) <= tol


def close_vec(a: list[float], b: list[float], tol: float = TOL) -> bool:
    return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))


def angle_degrees(a: list[float], b: list[float]) -> float | None:
    na, nb = norm(a), norm(b)
    if na == 0.0 or nb == 0.0:
        return None
    cosine = max(-1.0, min(1.0, dot(a, b) / (na * nb)))
    return n(math.degrees(math.acos(cosine)))


def source_hashes() -> dict[str, str]:
    observed: dict[str, str] = {}
    for rel, expected in PINS.items():
        path = ROOT / BASE / rel
        actual = sha256(path)
        if actual != expected:
            raise SystemExit(f"source pin mismatch: {path}: {actual} != {expected}")
        observed[str(BASE / rel)] = actual

    source_pins = read_json("current-knee-three-member-profile-attempt01/source-pins.json")
    for rel, expected in source_pins["source_sha256_verified"].items():
        if rel == "manifest_embedded_manifest_sha256":
            continue
        path = ROOT / rel
        actual = sha256(path)
        if actual != expected:
            raise SystemExit(f"profile source closure mismatch: {path}: {actual} != {expected}")
        observed[rel] = actual
    return dict(sorted(observed.items()))


def action_member_force(action: dict[str, Any], member: str) -> list[float]:
    if action["first"] == member:
        return action["force_on_first_xyz_n"]
    if action["second"] == member:
        return action["force_on_second_xyz_n"]
    raise AssertionError(f"{member} is not an endpoint of {action['source_connection_name']}")


def reconstruct_member_wrenches(bolt: dict[str, Any]) -> tuple[dict[str, dict[str, list[float]]], float]:
    datum = bolt["axis_datum_global_xyz_mm"]
    members: dict[str, dict[str, list[float]]] = {}
    for action in bolt["actions"]:
        for endpoint, point_key, force_key in (
            ("first", "first_point_global_xyz_mm", "force_on_first_xyz_n"),
            ("second", "second_point_global_xyz_mm", "force_on_second_xyz_n"),
        ):
            member = action[endpoint]
            point = action[point_key]
            force = action[force_key]
            row = members.setdefault(member, {"force_xyz_n": [0.0] * 3, "moment_xyz_nmm": [0.0] * 3})
            row["force_xyz_n"] = add(row["force_xyz_n"], force)
            row["moment_xyz_nmm"] = add(row["moment_xyz_nmm"], cross(sub(point, datum), force))

    expected = bolt["physical_member_wrenches_at_axis_datum"]
    max_error = 0.0
    if set(members) != set(expected):
        raise AssertionError(f"member set mismatch: {set(members)} != {set(expected)}")
    for member, row in members.items():
        for key in ("force_xyz_n", "moment_xyz_nmm"):
            errors = [abs(a - b) for a, b in zip(row[key], expected[member][key])]
            max_error = max(max_error, *errors)
            if max(errors, default=0.0) > TOL:
                raise AssertionError(f"source wrench reconstruction failed: {member} {key}: {row[key]} != {expected[member][key]}")
    return members, max_error


def main() -> None:
    source_pins = source_hashes()
    query = read_json("current-knee-three-member-profile-attempt01/query.json")
    calc = read_json("current-knee-three-member-transfer-attempt01/calculation.json")
    old_screen = read_json("current-bg003-middle-zone-cut-feasibility-attempt01/screen.json")
    bolt_inventory = read_json("bolt-groups/bolt-groups.json")

    assert query["scope"]["physical_stack_group_id"] == "BG003"
    assert query["scope"]["bolt_ids"] == ["knee_outer_left_side_1", "knee_outer_left_side_2"]
    assert calc["modeled_geometry_inputs"]["active_contact_or_bearing_law_verified"] is False
    intervals = calc["modeled_geometry_inputs"]["receiver_intervals_from_underhead_mm"]
    middle = intervals["base_side_left"]
    length = middle[1] - middle[0]
    assert close(length, 88.9, 1e-9)
    half = length / 2.0
    switch = half / math.sqrt(2.0)
    second_segment = half - switch
    zero_shear_station = half * (math.sqrt(2.0) - 1.0)
    assert close(half, 44.45, 1e-9)
    assert close(middle[0] + half, middle[1] - half, 1e-9)

    inventory_axes = [
        axis
        for group in bolt_inventory["candidate_groups"]
        if group["group_id"] == "BG003"
        for axis in group["axes"]
    ]
    assert {axis["axis_id"] for axis in inventory_axes} == set(query["scope"]["bolt_ids"])
    diameters = [float(axis["modeled_shaft_diameter_mm"]) for axis in inventory_axes]
    assert diameters and all(close(value, diameters[0], 1e-9) for value in diameters)
    shaft_diameter = diameters[0]
    modeled_fastener_lengths = [float(axis["modeled_shaft_occupied_length_mm"]) for axis in inventory_axes]
    assert all(close(value, modeled_fastener_lengths[0], 1e-9) for value in modeled_fastener_lengths)
    modeled_fastener_length = modeled_fastener_lengths[0]

    per_case: dict[str, Any] = {}
    all_plane_rows: list[dict[str, Any]] = []
    max_wrench_error = 0.0
    max_group_resultant = 0.0
    profile_force_residual_max = 0.0
    profile_moment_residual_max = 0.0
    modeled_tie_spans: list[float] = []
    required_gates = (
        "mpc_interval_checks_passed",
        "springa_law_checks_passed",
        "retained_bilateral_checks_passed",
        "selected_floor_complementarity_passed",
        "inactive_floor_tangent_no_restraint_or_reaction_passed",
        "raw_balance_passed",
        "rounding_interval_balance_passed",
    )

    for case_id, rel in REPORTS.items():
        report = read_json(rel)
        assert report["case_id"] == case_id
        assert report["status"] == "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY"
        assert report["actual_case_demand_usable_for_conditional_joint_checks"] is True
        assert report["native_solve_launched_by_exporter"] is False
        increments = report["increments"]
        assert len(increments) == 7
        case_rows: list[dict[str, Any]] = []
        for increment in increments:
            assert increment["all_five_corner_bodies_raw_and_interval_balance_passed"] is True
            assert all(increment["response_audit_gates"][key] is True for key in required_gates)
            group = increment["primary_physical_bolt_groups"]["BG003"]
            assert group["physical_bolt_count"] == 2
            assert group["lateral_plane_count"] == 4
            bolt_state_rows: list[dict[str, Any]] = []
            for bolt in group["bolts"]:
                axis = bolt["axis_id"]
                state_rows: list[dict[str, Any]] = []
                assert bolt["head_to_nut_unit_global_xyz"] == [1.0, 0.0, 0.0]
                reconstructed, wrench_error = reconstruct_member_wrenches(bolt)
                max_wrench_error = max(max_wrench_error, wrench_error)
                sum_force = [0.0] * 3
                sum_moment = [0.0] * 3
                for row in reconstructed.values():
                    sum_force = add(sum_force, row["force_xyz_n"])
                    sum_moment = add(sum_moment, row["moment_xyz_nmm"])
                max_group_resultant = max(max_group_resultant, norm(sum_force), norm(sum_moment))
                assert norm(sum_force) <= TOL and norm(sum_moment) <= TOL

                by_name = {action["source_connection_name"].rsplit("/", 1)[-1]: action for action in bolt["actions"]}
                axial = by_name["outer-seat-axial-tie"]
                tie = action_member_force(axial, "knee_outer_left_spine")[0]
                tie_span = norm(sub(axial["second_point_global_xyz_mm"], axial["first_point_global_xyz_mm"]))
                assert close(tie_span, 215.9, 1e-6)
                modeled_tie_spans.append(tie_span)
                plane_names = ("plane-37", "plane-38") if axis.endswith("_1") else ("plane-39", "plane-40")
                outer_by_plane = {
                    plane_names[0]: "knee_outer_left_spine",
                    plane_names[1]: "knee_outer_left_inner_frame_block",
                }
                axis_datum = bolt["axis_datum_global_xyz_mm"]
                for plane_index, plane_name in enumerate(plane_names):
                    action = by_name[plane_name]
                    outer = outer_by_plane[plane_name]
                    F = action_member_force(action, outer)
                    point1 = action["first_point_global_xyz_mm"]
                    point2 = action["second_point_global_xyz_mm"]
                    assert close_vec(point1, point2)
                    assert close(F[0], 0.0)
                    assert close_vec(add(action["force_on_first_xyz_n"], action["force_on_second_xyz_n"]), [0.0] * 3)
                    middle_member = action["second"] if action["first"] == outer else action["first"]
                    assert middle_member == "base_side_left"
                    assert close_vec(action_member_force(action, middle_member), scale(-1.0, F))

                    # p37/39 and p38/40 occur at opposite faces of the modeled middle receiver.
                    expected_x = -1219.2 if plane_index == 0 else -1130.3
                    assert close(point1[0], expected_x, 1e-6)
                    assert close(point1[1], axis_datum[1], 1e-6)
                    assert close(point1[2], axis_datum[2], 1e-6)
                    middle_interval = (
                        [middle[0], middle[0] + half]
                        if plane_index == 0
                        else [middle[1] - half, middle[1]]
                    )
                    interface_station = middle[0] if plane_index == 0 else middle[1]
                    middle_direction = 1 if plane_index == 0 else -1
                    outer_interval = intervals[outer]
                    assert close(outer_interval[1], interface_station, 1e-6) if plane_index == 0 else close(outer_interval[0], interface_station, 1e-6)
                    specifications = [
                        {
                            "segment_role": "middle-half",
                            "receiver": "base_side_left",
                            "interval": middle_interval,
                            "interface_station": interface_station,
                            "direction": middle_direction,
                            "resultant_on_fastener": F,
                            "remote_end": "base_side_left_center_cut",
                        },
                        {
                            "segment_role": "outer-member",
                            "receiver": outer,
                            "interval": outer_interval,
                            "interface_station": interface_station,
                            "direction": -middle_direction,
                            "resultant_on_fastener": scale(-1.0, F),
                            "remote_end": f"{outer}_outboard_free_face",
                        },
                    ]
                    magnitude = norm(F)
                    for spec in specifications:
                        segment_length = spec["interval"][1] - spec["interval"][0]
                        segment_switch = segment_length / math.sqrt(2.0)
                        segment_tail = segment_length - segment_switch
                        segment_zero_shear = segment_length * (math.sqrt(2.0) - 1.0)
                        resultant = spec["resultant_on_fastener"]
                        resultant_magnitude = norm(resultant)
                        q0 = resultant_magnitude / (segment_length * (math.sqrt(2.0) - 1.0)) if resultant_magnitude else 0.0

                        # The line profile acts on the bolt. It has a force equal to
                        # its target resultant and zero first moment about the interface.
                        integral_factor = segment_switch - segment_tail
                        computed_resultant = scale(q0 * integral_factor / resultant_magnitude, resultant) if resultant_magnitude else [0.0] * 3
                        force_residual = norm(sub(computed_resultant, resultant))
                        first_moment_factor = 0.5 * (segment_switch * segment_switch - (segment_length * segment_length - segment_switch * segment_switch))
                        moment_residual = abs(q0 * first_moment_factor)
                        profile_force_residual_max = max(profile_force_residual_max, force_residual)
                        profile_moment_residual_max = max(profile_moment_residual_max, moment_residual)
                        assert force_residual <= TOL and moment_residual <= TOL

                        switch_station = spec["interface_station"] + spec["direction"] * segment_switch
                        remote_station = spec["interval"][0] if spec["direction"] < 0 else spec["interval"][1]
                        interface_shear = F if plane_index == 0 else scale(-1.0, F)
                        local_axis = [float(spec["direction"]), 0.0, 0.0]
                        max_moment_vector = scale(segment_zero_shear / 2.0, cross(local_axis, interface_shear))
                        Mmax = norm(max_moment_vector)
                        row = {
                            "case_id": case_id,
                            "time": n(increment["time"]),
                            "load_factor": n(increment["load_factor"]),
                            "axis_id": axis,
                            "plane": plane_name,
                            "profile_segment_role": spec["segment_role"],
                            "profiled_receiver": spec["receiver"],
                            "source_outer_receiver": outer,
                            "source_action_F_on_outer_receiver_N": vec(F),
                            "profile_resultant_on_fastener_N": vec(resultant),
                            "source_interface_point_global_xyz_mm": vec(point1),
                            "outer_seat_axial_tie_signed_axis_force_N": n(tie),
                            "profile_receiver_interval_from_underhead_mm": vec(spec["interval"]),
                            "profile_segment_length_mm": n(segment_length),
                            "profile_coordinate_direction_global_x_sign": spec["direction"],
                            "profile_sign_switch_distance_from_interface_mm": n(segment_switch),
                            "profile_remaining_distance_after_switch_mm": n(segment_tail),
                            "profile_sign_switch_underhead_station_mm": n(switch_station),
                            "profile_remote_end": spec["remote_end"],
                            "profile_remote_end_underhead_station_mm": n(remote_station),
                            "peak_signed_line_reaction_N_per_mm": n(q0),
                            "peak_line_reaction_vector_N_per_mm": vec(scale(q0 / resultant_magnitude, resultant)) if resultant_magnitude else [0.0] * 3,
                            "net_profile_resultant_vector_N": vec(computed_resultant),
                            "profile_first_moment_about_actual_interface_Nmm": [0.0, 0.0, 0.0],
                            "conditional_fastener_internal_shear_max_N": n(resultant_magnitude),
                            "conditional_fastener_internal_shear_max_vector_global_N": vec(interface_shear),
                            "conditional_fastener_internal_moment_max_Nmm": n(Mmax),
                            "conditional_fastener_internal_moment_max_vector_global_Nmm": vec(max_moment_vector),
                            "conditional_moment_max_distance_from_interface_mm": n(segment_zero_shear),
                            "conditional_moment_max_underhead_station_mm": n(spec["interface_station"] + spec["direction"] * segment_zero_shear),
                            "conditional_V_at_profile_interface_N": n(norm(interface_shear)),
                            "conditional_M_at_profile_interface_Nmm": 0.0,
                            "conditional_V_at_profile_remote_end_N": 0.0,
                            "conditional_M_at_profile_remote_end_Nmm": 0.0,
                            "algebraic_profile_force_residual_N": n(force_residual),
                            "algebraic_profile_first_moment_residual_Nmm": n(moment_residual),
                        }
                        state_rows.append(row)
                        all_plane_rows.append(row)
                assert len(state_rows) == 4, f"expected four contiguous profiles for {case_id}/{axis}"
                by_profile = {(row["plane"], row["profile_segment_role"]): row for row in state_rows}
                for plane_name in plane_names:
                    middle_row = by_profile[(plane_name, "middle-half")]
                    outer_row = by_profile[(plane_name, "outer-member")]
                    assert close_vec(
                        middle_row["conditional_fastener_internal_shear_max_vector_global_N"],
                        outer_row["conditional_fastener_internal_shear_max_vector_global_N"],
                    )
                    assert close(middle_row["conditional_M_at_profile_interface_Nmm"], outer_row["conditional_M_at_profile_interface_Nmm"])
                ordered_intervals = sorted((row["profile_receiver_interval_from_underhead_mm"] for row in state_rows), key=lambda interval: interval[0])
                assert all(close(ordered_intervals[i][1], ordered_intervals[i + 1][0], 1e-6) for i in range(len(ordered_intervals) - 1))
                profile_resultant_sum = [0.0] * 3
                for row in state_rows:
                    profile_resultant_sum = add(profile_resultant_sum, row["profile_resultant_on_fastener_N"])
                    assert close(row["conditional_V_at_profile_remote_end_N"], 0.0)
                    assert close(row["conditional_M_at_profile_remote_end_Nmm"], 0.0)
                assert norm(profile_resultant_sum) <= TOL
                bolt_state_rows.append({"axis_id": axis, "profiles": state_rows})
            case_rows.append({
                "time": n(increment["time"]),
                "load_factor": n(increment["load_factor"]),
                "BG003_bolts": bolt_state_rows,
            })
        per_case[case_id] = {
            "source_report_sha256": sha256(ROOT / BASE / rel),
            "source_response_audit_gates_and_five_body_balance_passed_at_all_7_increments": True,
            "increments": case_rows,
        }

    full_load = [row for row in all_plane_rows if row["load_factor"] == 1.0]
    assert len(full_load) == 16
    assert modeled_tie_spans and all(close(value, modeled_tie_spans[0], 1e-9) for value in modeled_tie_spans)
    modeled_tie_span = modeled_tie_spans[0]
    action_relationships: dict[str, Any] = {}
    for case_id in REPORTS:
        for axis, first_plane, second_plane in (
            ("knee_outer_left_side_1", "plane-37", "plane-38"),
            ("knee_outer_left_side_2", "plane-39", "plane-40"),
        ):
            pair = [
                row for row in full_load
                if row["case_id"] == case_id and row["axis_id"] == axis
                and row["plane"] in (first_plane, second_plane)
                and row["profile_segment_role"] == "middle-half"
            ]
            by_plane = {row["plane"]: row for row in pair}
            first_F = by_plane[first_plane]["source_action_F_on_outer_receiver_N"]
            second_F = by_plane[second_plane]["source_action_F_on_outer_receiver_N"]
            first_magnitude, second_magnitude = norm(first_F), norm(second_F)
            action_relationships[f"{case_id}/{axis}"] = {
                "first_plane": first_plane,
                "second_plane": second_plane,
                "first_plane_F_N": vec(first_F),
                "second_plane_F_N": vec(second_F),
                "first_plane_magnitude_N": n(first_magnitude),
                "second_plane_magnitude_N": n(second_magnitude),
                "larger_to_smaller_magnitude_ratio": n(max(first_magnitude, second_magnitude) / min(first_magnitude, second_magnitude)),
                "angle_between_signed_plane_actions_degrees": angle_degrees(first_F, second_F),
            }
    envelopes: dict[str, Any] = {}
    for case_id in REPORTS:
        for plane in ("plane-37", "plane-38", "plane-39", "plane-40"):
            rows = [row for row in all_plane_rows if row["case_id"] == case_id and row["plane"] == plane]
            governing = max(rows, key=lambda row: row["conditional_fastener_internal_moment_max_Nmm"])
            q_governing = max(rows, key=lambda row: row["peak_signed_line_reaction_N_per_mm"])
            v_governing = max(rows, key=lambda row: row["conditional_fastener_internal_shear_max_N"])
            envelopes[f"{case_id}/{plane}"] = {
                "max_peak_line_reaction_N_per_mm": q_governing["peak_signed_line_reaction_N_per_mm"],
                "line_reaction_governing_segment": q_governing["profile_segment_role"],
                "line_reaction_governing_receiver": q_governing["profiled_receiver"],
                "max_conditional_fastener_internal_shear_N": v_governing["conditional_fastener_internal_shear_max_N"],
                "max_conditional_fastener_internal_moment_Nmm": governing["conditional_fastener_internal_moment_max_Nmm"],
                "moment_governing_segment": governing["profile_segment_role"],
                "moment_governing_receiver": governing["profiled_receiver"],
                "envelope_load_factor": max(row["load_factor"] for row in rows),
            }

    whole_fastener_envelopes: dict[str, Any] = {}
    for case_id in REPORTS:
        for axis in ("knee_outer_left_side_1", "knee_outer_left_side_2"):
            rows = [row for row in all_plane_rows if row["case_id"] == case_id and row["axis_id"] == axis]
            q_governing = max(rows, key=lambda row: row["peak_signed_line_reaction_N_per_mm"])
            v_governing = max(rows, key=lambda row: row["conditional_fastener_internal_shear_max_N"])
            m_governing = max(rows, key=lambda row: row["conditional_fastener_internal_moment_max_Nmm"])
            full_load_tie = next(row["outer_seat_axial_tie_signed_axis_force_N"] for row in rows if row["load_factor"] == 1.0)
            whole_fastener_envelopes[f"{case_id}/{axis}"] = {
                "max_profile_line_reaction_N_per_mm": q_governing["peak_signed_line_reaction_N_per_mm"],
                "line_reaction_governing_plane_and_receiver": f"{q_governing['plane']}/{q_governing['profiled_receiver']}",
                "max_conditional_full_stack_fastener_V_N": v_governing["conditional_fastener_internal_shear_max_N"],
                "V_governing_plane_and_receiver": f"{v_governing['plane']}/{v_governing['profiled_receiver']}",
                "V_governing_vector_global_N": v_governing["conditional_fastener_internal_shear_max_vector_global_N"],
                "max_conditional_full_stack_fastener_M_Nmm": m_governing["conditional_fastener_internal_moment_max_Nmm"],
                "M_governing_plane_and_receiver": f"{m_governing['plane']}/{m_governing['profiled_receiver']}",
                "M_governing_vector_global_Nmm": m_governing["conditional_fastener_internal_moment_max_vector_global_Nmm"],
                "M_governing_load_factor": m_governing["load_factor"],
                "envelope_load_factor": max(row["load_factor"] for row in rows),
                "lateral_V_and_M_at_both_modeled_outboard_free_faces_and_middle_center_cut_N_or_Nmm": [0.0, 0.0],
                "axial_tie_force_at_middle_cut_N": full_load_tie,
            }

    query_voids = [ray["initial_and_intermediate_void_intervals_mm"] for ray in query["rays"] if ray["initial_and_intermediate_void_intervals_mm"]]
    assert query_voids
    min_bore_radius = min(interval[1] for group in query_voids for interval in group)
    radial_gap = min_bore_radius - shaft_diameter / 2.0

    output = {
        "schema": "current-bg003-piecewise-bearing-profile-feasibility-attempt01-v1",
        "status": "PASS_CONSTRUCTED_STATIC_PROFILE_AND_MODELED_GEOMETRY_ONLY",
        "finding": "The signed piecewise profile statically balances each BG003 outer interface action within one disjoint middle-member half-zone and gives zero transverse shear and bending moment at the shared center cut. It does not remove the simultaneous axial tie force or prove contact compatibility, wood/steel strength, or a design capacity.",
        "scope": {
            "candidate": "compact-floor-flush-wood-joints-development",
            "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
            "group_id": "BG003",
            "cases": ["a12-rear", "a1-rear"],
            "increments_per_case": 7,
            "plane_count": 4,
            "fastener_axis_direction_global_xyz": [1.0, 0.0, 0.0],
            "mechanics_only_no_capacity_or_acceptance": True,
        },
        "source_pins_sha256": source_pins,
        "profile_geometry": {
            "member_intervals_from_underhead_mm": intervals,
            "middle_member": "base_side_left",
            "middle_member_length_mm": n(length),
            "two_half_zone_intervals_from_underhead_mm": [
                [n(middle[0]), n(middle[0] + half)],
                [n(middle[0] + half), n(middle[1])],
            ],
            "full_stack_nonoverlapping_profile_intervals_per_bolt_mm": [
                {"receiver": "knee_outer_left_spine", "interval": intervals["knee_outer_left_spine"], "plane": "plane-37 or plane-39", "profile_sign_resultant": "opposite adjoining middle-half profile"},
                {"receiver": "base_side_left", "interval": [n(middle[0]), n(middle[0] + half)], "plane": "plane-37 or plane-39", "profile_sign_resultant": "source outer-action vector F"},
                {"receiver": "base_side_left", "interval": [n(middle[0] + half), n(middle[1])], "plane": "plane-38 or plane-40", "profile_sign_resultant": "source outer-action vector F"},
                {"receiver": "knee_outer_left_inner_frame_block", "interval": intervals["knee_outer_left_inner_frame_block"], "plane": "plane-38 or plane-40", "profile_sign_resultant": "opposite adjoining middle-half profile"},
            ],
            "assigned_overlap_mm": 0.0,
            "assigned_gap_mm": 0.0,
            "half_zone_length_mm": n(half),
            "sign_switch_distance_from_each_interface_mm": n(switch),
            "remaining_segment_after_switch_mm": n(second_segment),
            "switch_coordinate_stations_from_underhead_mm": [n(middle[0] + switch), n(middle[1] - switch)],
            "conditional_modeled_shaft_diameter_mm": n(shaft_diameter),
            "modeled_shaft_occupied_length_mm": n(modeled_fastener_length),
            "modeled_outer_seat_tie_point_separation_mm": n(modeled_tie_span),
            "modeled_shaft_length_beyond_outer_seat_tie_span_mm": n(modeled_fastener_length - modeled_tie_span),
            "modeled_interface_gaps_mm": calc["modeled_geometry_inputs"]["modeled_interface_interval_gaps_mm"],
            "smallest_initial_ray_void_radius_mm": n(min_bore_radius),
            "conditional_radial_bore_to_shaft_clearance_mm": n(radial_gap),
            "actual_contact_or_bearing_law_verified": False,
            "physical_head_to_nut_order_verified": False,
        },
        "profile_definition_and_equilibrium": {
            "ell_mm": n(half),
            "a_over_ell": n(1.0 / math.sqrt(2.0)),
            "q0_definition": "q0 = |F| / [ell * (sqrt(2) - 1)] N/mm",
            "q_vector_definition": "For each profile segment of length ell, q(s) = +q0 * R_hat for 0 <= s <= ell/sqrt(2); q(s) = -q0 * R_hat for ell/sqrt(2) < s <= ell; R is the profile resultant on the fastener. Middle-half profiles use R = +F; the adjoining outer-member profiles use R = -F.",
            "net_profile_resultant_identity": "integral(q ds) = q0 * [2a - ell] * F_hat = F",
            "first_moment_identity": "integral(s cross q ds) = 0 because a^2 = ell^2/2",
            "local_point_action_moment_about_interface": "zero; each source plane action is a point force with coincident first/second interface coordinates and no independent couple field",
            "outer_member_and_middle_member_transfer": "The outer receiver point action is unchanged. On the middle receiver, the constructed distributed bolt-on-wood profile has resultant opposite q, matching the source middle-side point action; its zero local first moment preserves the reported member wrench at the interface.",
            "fastener_internal_V_and_M_at_each_profile_remote_end": [0.0, 0.0],
            "fastener_internal_V_and_M_at_both_outboard_receiver_faces": [0.0, 0.0],
            "fastener_internal_V_and_M_at_middle_center_cut": [0.0, 0.0],
            "fastener_internal_V_and_M_are_continuous_at_both_actual_plane_interfaces": True,
            "fastener_V_max_formula": "|F| at the interface",
            "fastener_M_max_formula": "|F| * ell * (sqrt(2) - 1) / 2 Nmm, at s = ell * (sqrt(2) - 1)",
            "maxima_scope": "Conditional internal resultant maxima for this idealized signed line-reaction profile only; no material resistance is calculated.",
        },
        "source_wrench_reconstruction": {
            "source_point_actions_reconstruct_reported_member_wrenches_at_each_bolt_axis_datum": True,
            "max_component_reconstruction_error_N_or_Nmm": n(max_wrench_error),
            "max_total_force_or_moment_resultant_norm_N_or_Nmm": n(max_group_resultant),
            "interpretation": "The profile preserves each plane action's force and zero local couple at its actual interface. Nonzero moments reported at the common shaft-axis datum arise from the axial spacing of the interfaces and are retained by transporting the point resultants; they are not set to zero.",
        },
        "cases": per_case,
        "seven_increment_per_plane_envelopes": envelopes,
        "seven_increment_whole_fastener_profile_envelopes": whole_fastener_envelopes,
        "full_load_increment_results": full_load,
        "full_load_plane_action_relationships": action_relationships,
        "checks": {
            "source_report_hashes_and_geometry_source_closure_verified": True,
            "all_14_source_case_increments_strict_audits_and_five_body_balances_passed": True,
            "all_112_profile_segment_state_force_and_moment_identities_passed": True,
            "all_28_full_stack_bolt_states_have_contiguous_profiles_and_zero_lateral_end_and_center_cut_resultants": True,
            "max_profile_force_residual_N": n(profile_force_residual_max),
            "max_profile_first_moment_residual_Nmm": n(profile_moment_residual_max),
            "all_28_per_bolt_member_wrenches_reconstructed": True,
        },
        "limits": [
            "This construction is a statically admissible idealization, not a verified compatible wood/bolt contact field. Its sign reversal means compression on opposite bore flanks, not tensile wood pressure; simultaneous engagement, the 0.575 mm modeled radial clearance, deformation compatibility, and the necessary contact law are unresolved.",
            "The assigned half-zones are adjacent subintervals of one continuous 88.9 mm receiver. They are nonoverlapping in axial coordinate only; geometry does not segregate bearing pressure into these zones.",
            "The reported source tie force remains longitudinal through the center cut. Zero transverse V and bending M do not give a zero full six-component internal wrench and do not check bolt tension interaction, thread/root section, washer-seat behavior, timber splitting, shear plug, withdrawal, or local bearing limits.",
            "Line reaction is reported in N/mm. Contact width and a constitutive law are absent, so it is not converted to N/mm^2 pressure or a wood stress.",
            "This field is not one of the specified AWC TR-12 ideally plastic yield-mode derivations and does not provide NDS/TR-12 Z, Rd, or an adjusted resistance. No capacity, lower-bound strength, connection acceptance, or general frame claim follows.",
        ],
    }
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"cases={len(per_case)} increments={sum(len(x['increments']) for x in per_case.values())} profile_segment_states={len(all_plane_rows)}")
    print(f"max profile residuals: force={n(profile_force_residual_max)} N, first moment={n(profile_moment_residual_max)} Nmm")
    print(f"max source wrench reconstruction error={n(max_wrench_error)}; max group resultant={n(max_group_resultant)}")
    print(f"output sha256={sha256(OUT)}")


if __name__ == "__main__":
    main()
