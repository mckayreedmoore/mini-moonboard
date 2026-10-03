from __future__ import annotations

import copy
import importlib.util
import math
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "right_finished_section_actions_test", Path(__file__).with_name("actions.py")
)
assert SPEC is not None and SPEC.loader is not None
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)

ORIGIN = [10.0, 20.0, 30.0]
G = [0.0, 1.0, 0.0]
Q = [-1.0, 0.0, 0.0]
R = [0.0, 0.0, 1.0]
DATUM = [0.0, 0.0, 0.0]
LOADS = {
    "base_header": [1.0, 2.0, -3.0],
    "base_post_outer_right": [0.0, -1.0, 2.0],
    "base_side_right": [2.0, 0.0, 1.0],
    "knee_outer_right_spine": [-1.0, 1.0, 0.0],
    "knee_outer_right_inner_frame_block": [0.0, 0.5, 0.25],
}
LOAD_POINTS = {
    "base_header": [10.0, 18.0, 30.0],
    "base_post_outer_right": [10.0, 20.0, 30.0],
    "base_side_right": [10.0, 20.0, 30.0],
    "knee_outer_right_spine": [10.0, 20.0, 30.0],
    "knee_outer_right_inner_frame_block": [10.0, 20.0, 30.0],
}


def _cross(first, second):
    return [
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    ]


def _sub(first, second):
    return [a - b for a, b in zip(first, second, strict=True)]


def _sum_vectors(rows):
    return [math.fsum(row[index] for row in rows) for index in range(3)]


def _known_wrench(records, datum):
    forces = [record[1] for record in records]
    moments = [_cross(_sub(record[0], datum), record[1]) for record in records]
    force_radii = [record[2] for record in records]
    moment_radii = []
    for point, _, radius in records:
        arm = _sub(point, datum)
        x, y, z = (abs(value) for value in arm)
        rx, ry, rz = radius
        moment_radii.append([y * rz + z * ry, z * rx + x * rz, x * ry + y * rx])
    return {
        "force_xyz_n": _sum_vectors(forces),
        "moment_xyz_nmm": _sum_vectors(moments),
        "force_rounding_radius_xyz_n": _sum_vectors(force_radii),
        "moment_rounding_radius_xyz_nmm": _sum_vectors(moment_radii),
    }


def _source_rows(factor, case):
    rows = {}
    definitions = [
        (
            "internal_header_post",
            "base_header",
            "base_post_outer_right",
            "frame_connection",
            [10.0, 20.0, 30.0],
            [10.0, 20.0, 30.0],
            [1.0, 2.0, 3.0],
            [0.01, 0.02, 0.03],
        ),
        (
            "contact_cross_side_panel",
            "base_side_right",
            "panel",
            "timber_or_panel_contact",
            [12.0, 19.0, 33.0],
            [12.0, 25.0, 33.0],
            [2.0, 4.0, 3.0],
            [0.04, 0.05, 0.06],
        ),
    ]
    for index in range(4):
        definitions.append(
            (
                f"floor_tangent_{index}",
                "base_post_outer_right",
                "floor",
                "assumed_no_slip_floor",
                [10.0 + index, 20.0, 30.0 + index],
                [10.0 + index, 20.0, 30.0 + index],
                [float(index + 1), -float(index + 1), 0.5],
                [0.001, 0.002, 0.003],
            )
        )

    for index, (
        name,
        first,
        second,
        role,
        first_point,
        second_point,
        base_force,
        radius,
    ) in enumerate(definitions):
        owner = {"first": first, "second": second, "point": first_point, "role": role}
        if role == "timber_or_panel_contact":
            owner.update({"scalar_normal": [0.0, 0.0, 1.0], "source_area_mm2": 12.5})
        state = None
        if role == "assumed_no_slip_floor":
            floor_index = index - 2
            state = (
                "released_inactive_floor_tangent_zero_action"
                if case == "k12-rear" or floor_index >= 2
                else "active_selected_floor_tangent_reaction"
            )
        force = (
            [0.0, 0.0, 0.0]
            if state == "released_inactive_floor_tangent_zero_action"
            else [factor * value for value in base_force]
        )
        row = {
            "name": name,
            "source_connection_name": name,
            "first": first,
            "second": second,
            "point": first_point,
            "first_point": first_point,
            "second_point": second_point,
            "force_on_first_xyz_n": force,
            "force_on_second_xyz_n": [-value for value in force],
            "force_rounding_radius_xyz_n": (
                [0.0, 0.0, 0.0]
                if state == "released_inactive_floor_tangent_zero_action"
                else radius
            ),
            "source_row_ids": [f"native-row-{index}"],
            "source_inventory_rows": [
                {
                    "source_inventory_row_index": index,
                    "source_connection_name": name,
                    "source_row_id": f"native-row-{index}",
                }
            ],
        }
        if state is not None:
            row["floor_tangent_state"] = state
        else:
            row["role"] = role
        if role == "timber_or_panel_contact":
            row["scalar_normal"] = [0.0, 0.0, 1.0]
            row["source_area_mm2"] = 12.5
        rows[name] = {"row": row, "owner": owner, "index": index}
    return rows


def _interface_records(rows, member):
    records = []
    for data in rows.values():
        row = data["row"]
        for endpoint in ("first", "second"):
            if row[endpoint] != member:
                continue
            records.append(
                (
                    row.get(endpoint + "_point", row["point"]),
                    row["force_on_" + endpoint + "_xyz_n"],
                    row["force_rounding_radius_xyz_n"],
                )
            )
    return records


def _external_records(model, member, factor):
    return [
        (
            model["nodes"][node],
            [factor * component for component in force],
            [0.0, 0.0, 0.0],
        )
        for node, force in model["physical_body_loads"][member].items()
    ]


def _fixture():
    point_inventory = []
    row_definitions = _source_rows(1.0, "a1-rear")
    for name, data in row_definitions.items():
        owner = data["owner"]
        for endpoint in ("first", "second"):
            member = owner[endpoint]
            if member not in A.MEMBER_SET:
                continue
            point = owner.get(endpoint + "_point", owner["point"])
            point_inventory.append(
                {
                    "identity_key": f"interface:{name}:endpoint:{endpoint}",
                    "kind": A.INTERFACE_ENDPOINT,
                    "source_connection_name": name,
                    "endpoint": endpoint,
                    "member_id": member,
                    "point_global_xyz_mm": point,
                    "grain_station_mm": point[1] - ORIGIN[1],
                }
            )

    nodes = {}
    body_loads = {}
    for index, member in enumerate(A.MEMBERS, start=101):
        key = str(index)
        point = LOAD_POINTS[member]
        nodes[key] = point
        body_loads[member] = {key: LOADS[member]}
        point_inventory.append(
            {
                "identity_key": f"load:{member}:node:{index}",
                "kind": A.BODY_LOAD_NODE,
                "node_id": index,
                "source_cases": list(A.CASES),
                "member_id": member,
                "point_global_xyz_mm": point,
                "grain_station_mm": point[1] - ORIGIN[1],
            }
        )
    point_inventory.append(
        {
            "identity_key": "receiver_bore:axis-test:base_header:feature-test",
            "kind": A.BORE_CENTER,
            "member_id": "base_header",
            "point_global_xyz_mm": [12.0, 20.0, 33.0],
            "grain_station_mm": 0.0,
        }
    )
    point_inventory.sort(key=lambda row: row["identity_key"])

    frames = [
        {
            "member_id": member,
            "origin_global_xyz_mm": ORIGIN,
            "grain_axis_global_xyz": G,
            "section_u_global_xyz": Q,
            "section_v_global_xyz": R,
        }
        for member in A.MEMBERS
    ]
    planes = []
    for member in A.MEMBERS:
        identities = [
            {
                "identity_key": row["identity_key"],
                "kind": row["kind"],
            }
            for row in point_inventory
            if row["member_id"] == member and abs(row["grain_station_mm"]) <= 1e-6
        ]
        identities.sort(key=lambda row: row["identity_key"])
        planes.append(
            {
                "plane_id": f"{member}:station-zero",
                "member_id": member,
                "plane_origin_global_xyz_mm": ORIGIN,
                "grain_axis_global_xyz": G,
                "section_u_global_xyz": Q,
                "section_v_global_xyz": R,
                "grain_station_mm": 0.0,
                "coincidence_tolerance_mm": 1e-6,
                "source_identity_count": len(identities),
                "source_identities": identities,
            }
        )
    plan = {
        "member_frames_and_step_bindings": frames,
        "point_inventory": point_inventory,
        "section_planes": planes,
    }

    models = {}
    case_reports = {}
    datums = {member: list(DATUM) for member in A.MEMBERS}
    for case in A.CASES:
        model_rows = []
        case_inventory = []
        ownership = {}
        for name, data in row_definitions.items():
            owner = data["owner"]
            index = data["index"]
            model_rows.append(
                {
                    "name": name,
                    "first_body": owner["first"],
                    "second_body": owner["second"],
                    "physical_owner": owner,
                }
            )
            ownership[name] = {"role": owner["role"]}
            case_inventory.append(
                {
                    "source_connection_name": name,
                    "owner": owner,
                    "source_indices": [index],
                }
            )
        models[case] = {
            "case_id": case,
            "nodes": nodes,
            "physical_body_loads": body_loads,
            "connection_ownership": ownership,
            "raw_source_carrier_law_inventory_rows": model_rows,
        }
        case_reports[case] = {
            "interface_count": len(case_inventory),
            "inventory": case_inventory,
            "reporting_datums_xyz_mm": datums,
        }

    states = []
    for case in A.CASES:
        model = models[case]
        for index, factor in enumerate(A.LOAD_FACTORS):
            source_rows = _source_rows(factor, case)
            rows = {name: item["row"] for name, item in source_rows.items()}
            balance_rows = {}
            for member in A.MEMBERS:
                interface_records = _interface_records(source_rows, member)
                external_records = _external_records(model, member, factor)
                interface_wrench = _known_wrench(interface_records, DATUM)
                external_wrench = _known_wrench(external_records, DATUM)
                combined_wrench = _known_wrench(
                    interface_records + external_records, DATUM
                )
                balance_rows[member] = {
                    "datum_global_xyz_mm": list(DATUM),
                    "interface_action_wrench": {
                        "force_xyz_n": interface_wrench["force_xyz_n"],
                        "moment_xyz_nmm": interface_wrench["moment_xyz_nmm"],
                    },
                    "external_load_wrench": {
                        "force_xyz_n": external_wrench["force_xyz_n"],
                        "moment_xyz_nmm": external_wrench["moment_xyz_nmm"],
                    },
                    "combined_residual_wrench": {
                        "force_xyz_n": combined_wrench["force_xyz_n"],
                        "moment_xyz_nmm": combined_wrench["moment_xyz_nmm"],
                    },
                    "source_force_radius_N": interface_wrench[
                        "force_rounding_radius_xyz_n"
                    ],
                    "source_moment_radius_Nmm": interface_wrench[
                        "moment_rounding_radius_xyz_nmm"
                    ],
                    "interface_source_connection_names": sorted(
                        name
                        for name, data in source_rows.items()
                        if data["row"]["first"] == member
                        or data["row"]["second"] == member
                    ),
                    "raw_balance_passed": True,
                    "rounding_interval_balance_passed": True,
                }
            active_count = sum(
                row.get("floor_tangent_state")
                == "active_selected_floor_tangent_reaction"
                for row in rows.values()
            )
            released_count = sum(
                row.get("floor_tangent_state")
                == "released_inactive_floor_tangent_zero_action"
                for row in rows.values()
            )
            states.append(
                {
                    "case_id": case,
                    "increment_index": index,
                    "load_factor": factor,
                    "interface_actions": rows,
                    "internal_interface_count": 1,
                    "boundary_interface_count": len(rows) - 1,
                    "active_floor_tangent_groups": active_count,
                    "released_floor_tangent_groups": released_count,
                    "member_balances": balance_rows,
                }
            )
    boundary = {
        "status": "PASS_RIGHT_FIVE_BODY_BOUNDARY_RECONSTRUCTION_ONLY",
        "members": list(A.MEMBERS),
        "cases": case_reports,
        "states": states,
    }
    return plan, boundary, models


def test_source_only_action_join_preserves_rotated_signed_cut_actions_and_census():
    plan, boundary, models = _fixture()

    report = A.build_actions(plan, boundary, models)

    assert report["status"] == "PASS_SAVED_POINT_ACTION_ACCOUNTING_ONLY"
    assert report["counts"]["case_count"] == 3
    assert report["counts"]["increment_count_per_case"] == 7
    assert report["counts"]["state_count"] == 21
    assert report["counts"]["source_interface_rows_per_state"] == 6
    assert report["counts"]["target_member_interface_endpoint_actions_per_state"] == 7
    assert report["counts"]["physical_body_load_node_actions_per_state"] == 5
    assert report["counts"]["full_point_action_records_per_state"] == 12
    assert report["counts"]["plan_point_inventory_count"] == 13
    assert report["counts"]["geometry_only_receiver_bore_center_count"] == 1
    assert report["counts"]["interface_census_preserved"] is True
    assert report["counts"]["released_floor_zero_actions_retained"] is True
    assert all(
        row["internal_interface_row_count"] == 1
        and row["boundary_interface_row_count"] == 5
        for row in report["point_action_states"]
    )
    assert (
        report["source_interface_inventory_by_case"]["a1-rear"]
        == report["source_interface_inventory_by_case"]["k12-rear"]
    )

    a1 = next(
        row
        for row in report["point_action_states"]
        if row["case_id"] == "a1-rear" and row["increment_index"] == 0
    )
    action_by_key = {row["identity_key"]: row for row in a1["point_actions"]}
    assert len(action_by_key) == len(a1["point_actions"]) == 12
    assert set(action_by_key) == {
        row["identity_key"]
        for row in plan["point_inventory"]
        if row["kind"] in {A.INTERFACE_ENDPOINT, A.BODY_LOAD_NODE}
    }
    load = action_by_key["load:base_header:node:101"]
    assert load["force_global_xyz_n"] == pytest.approx([0.1, 0.2, -0.3])
    assert load["source_metadata"]["load_factor"] == 0.1
    assert load["force_rounding_radius_global_xyz_n"] == [0.0, 0.0, 0.0]

    internal_first = action_by_key["interface:internal_header_post:endpoint:first"]
    internal_second = action_by_key["interface:internal_header_post:endpoint:second"]
    assert internal_first["force_global_xyz_n"] == pytest.approx([0.1, 0.2, 0.3])
    assert internal_second["force_global_xyz_n"] == pytest.approx([-0.1, -0.2, -0.3])

    floor = action_by_key["interface:floor_tangent_2:endpoint:first"]
    assert floor["force_global_xyz_n"] == [0.0, 0.0, 0.0]
    assert floor["source_metadata"]["response_role"] is None
    assert floor["source_metadata"]["resolved_source_role"] == "assumed_no_slip_floor"
    assert floor["source_metadata"]["floor_tangent_state"] == (
        "released_inactive_floor_tangent_zero_action"
    )
    assert a1["active_floor_tangent_group_count"] == 2
    assert a1["released_floor_tangent_group_count"] == 2

    side_cut = next(
        cut
        for cut in next(
            row
            for row in report["plane_cut_states"]
            if row["case_id"] == "a1-rear" and row["increment_index"] == 0
        )["plane_cut_actions"]
        if cut["plane_id"] == "base_side_right:station-zero"
    )
    assert side_cut["before"]["point_action_count"] == 1
    assert side_cut["before"]["wrench_global"]["moment_xyz_nmm"] == pytest.approx(
        [-1.5, 0.0, 1.0]
    )
    assert side_cut["before"]["wrench_global"][
        "moment_rounding_radius_xyz_nmm"
    ] == pytest.approx([0.21, 0.24, 0.14])
    assert side_cut["before"]["wrench_in_saved_g_q_r_frame"][
        "force_gqr_n"
    ] == pytest.approx([0.4, -0.2, 0.3])
    side_partition = next(
        row
        for row in report["plane_identity_partitions"]
        if row["plane_id"] == "base_side_right:station-zero"
    )
    event = side_partition["modeled_contact_segment_plane_events"][0]
    assert event["event_kind"] == "crosses_plane"
    assert event["force_or_traction_assigned_to_cut"] is False
    assert event["endpoints"][0]["identity_key"] == (
        "interface:contact_cross_side_panel:endpoint:first"
    )
    assert event["endpoints"][1]["identity_key"] is None
    assert report["counts"]["state_plane_cut_count"] == 21 * 5
    side_balance = next(
        row
        for row in a1["member_balance_reconstruction"]
        if row["member_id"] == "base_side_right"
    )
    assert side_balance["interface_point_action_wrench"][
        "force_xyz_n"
    ] == pytest.approx([0.2, 0.4, 0.3])
    assert side_balance["interface_point_action_wrench"][
        "moment_xyz_nmm"
    ] == pytest.approx([-7.5, 3.0, 1.0])
    assert side_balance["interface_point_action_wrench"][
        "moment_rounding_radius_xyz_nmm"
    ] == pytest.approx([2.79, 2.04, 1.36])
    assert (
        side_balance["arithmetic_match_status"] == "MATCH_SAVED_BOUNDARY_MEMBER_BALANCE"
    )


def test_source_owner_partition_and_complete_scalar_membership_are_failure_gates():
    plan, boundary, models = _fixture()
    mutated = copy.deepcopy(boundary)
    state = next(
        row
        for row in mutated["states"]
        if row["case_id"] == "a1-rear" and row["increment_index"] == 0
    )
    state["boundary_interface_count"] += 1
    with pytest.raises(A.ActionRefusal, match="boundary interface count changed"):
        A.build_actions(plan, mutated, models)

    plan, boundary, models = _fixture()
    mutated_models = copy.deepcopy(models)
    raw = mutated_models["a1-rear"]["raw_source_carrier_law_inventory_rows"][0]
    raw["physical_owner"]["second"] = "floor"
    with pytest.raises(A.ActionRefusal, match="raw owner/body endpoints disagree"):
        A.build_actions(plan, boundary, mutated_models)

    plan, boundary, models = _fixture()
    mutated_boundary = copy.deepcopy(boundary)
    mutated_boundary["cases"]["a1-rear"]["inventory"][0]["source_indices"] = [99]
    with pytest.raises(A.ActionRefusal, match="scalar source row membership differs"):
        A.build_actions(plan, mutated_boundary, models)

    plan, boundary, models = _fixture()
    mutated_boundary = copy.deepcopy(boundary)
    state = next(
        row
        for row in mutated_boundary["states"]
        if row["case_id"] == "a1-rear" and row["increment_index"] == 0
    )
    del state["interface_actions"]["contact_cross_side_panel"][
        "force_rounding_radius_xyz_n"
    ]
    with pytest.raises(A.ActionRefusal, match="no saved force rounding radius"):
        A.build_actions(plan, mutated_boundary, models)


def test_plan_partition_and_floor_role_state_mutations_refuse():
    plan, boundary, models = _fixture()
    mutated_plan = copy.deepcopy(plan)
    first_plane = mutated_plan["section_planes"][0]
    first_plane["source_identities"].pop()
    first_plane["source_identity_count"] -= 1
    with pytest.raises(A.ActionRefusal, match="source identities do not match"):
        A.build_actions(mutated_plan, boundary, models)

    plan, boundary, models = _fixture()
    mutated = copy.deepcopy(boundary)
    state = next(
        row
        for row in mutated["states"]
        if row["case_id"] == "a1-rear" and row["increment_index"] == 0
    )
    state["interface_actions"]["floor_tangent_2"]["force_on_first_xyz_n"] = [
        1.0,
        0.0,
        0.0,
    ]
    with pytest.raises(A.ActionRefusal, match="released floor action"):
        A.build_actions(plan, mutated, models)

    plan, boundary, models = _fixture()
    mutated = copy.deepcopy(boundary)
    state = next(
        row
        for row in mutated["states"]
        if row["case_id"] == "a1-rear" and row["increment_index"] == 0
    )
    state["interface_actions"]["floor_tangent_2"]["role"] = "timber_or_panel_contact"
    with pytest.raises(A.ActionRefusal, match="response/source roles disagree"):
        A.build_actions(plan, mutated, models)
