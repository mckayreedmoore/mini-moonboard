#!/usr/bin/env python3
"""Account for saved point actions at planned right-corner grain cuts.

This packet preserves point loads and their resultants. It does not recover
distributed finished-section tractions, assign actions to disconnected wood
regions, or establish strength or joint acceptance.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

MEMBERS = (
    "base_header",
    "base_post_outer_right",
    "base_side_right",
    "knee_outer_right_spine",
    "knee_outer_right_inner_frame_block",
)
MEMBER_SET = set(MEMBERS)
CASES = ("a1-rear", "a12-rear", "k12-rear")
LOAD_FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
INTERFACE_ENDPOINT = "interface_endpoint"
BODY_LOAD_NODE = "physical_body_load_node"
BORE_CENTER = "receiver_bore_center"
ACTION_KINDS = {INTERFACE_ENDPOINT, BODY_LOAD_NODE}
FORCE_ARITHMETIC_TOL_N = 1e-8
MOMENT_ARITHMETIC_TOL_NMM = 1e-6
FRAME_TOL = 1e-6
STATION_TOL = 1e-6


class ActionRefusal(ValueError):
    """An input join or saved point-action reconstruction is not exact."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ActionRefusal(message)


def _finite(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ActionRefusal(f"{label} is not numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ActionRefusal(f"{label} is nonfinite")
    return result


def _vec(value: Any, label: str) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ActionRefusal(f"{label} is not a three-vector")
    return [_finite(component, label) for component in value]


def _node_id(value: Any, label: str) -> int:
    if type(value) is int:
        result = value
    elif isinstance(value, str) and value.isascii() and value.isdigit():
        result = int(value)
    else:
        raise ActionRefusal(f"{label} is not a discrete node ID")
    if result <= 0:
        raise ActionRefusal(f"{label} is not positive")
    return result


def _sum_vectors(rows: list[list[float]]) -> list[float]:
    return [math.fsum(row[index] for row in rows) for index in range(3)]


def _dot(first: list[float], second: list[float]) -> float:
    return math.fsum(a * b for a, b in zip(first, second, strict=True))


def _sub(first: list[float], second: list[float]) -> list[float]:
    return [a - b for a, b in zip(first, second, strict=True)]


def _cross(first: list[float], second: list[float]) -> list[float]:
    return [
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    ]


def _close(
    first: list[float], second: list[float], tolerance: float, label: str
) -> None:
    if (
        len(first) != len(second)
        or max((abs(a - b) for a, b in zip(first, second, strict=True)), default=0.0)
        > tolerance
    ):
        raise ActionRefusal(f"{label} differs")


def _interval_cross_radius(arm: list[float], radius: list[float]) -> list[float]:
    x, y, z = (abs(value) for value in arm)
    rx, ry, rz = radius
    return [y * rz + z * ry, z * rx + x * rz, x * ry + y * rx]


def _project(vector: list[float], basis: list[list[float]]) -> list[float]:
    return [_dot(axis, vector) for axis in basis]


def _project_radius(radius: list[float], basis: list[list[float]]) -> list[float]:
    return [
        math.fsum(abs(axis[index]) * radius[index] for index in range(3))
        for axis in basis
    ]


def _frame(row: dict[str, Any], label: str) -> dict[str, Any]:
    origin = _vec(row.get("origin_global_xyz_mm"), f"{label} origin")
    basis = [
        _vec(row.get("grain_axis_global_xyz"), f"{label} grain axis"),
        _vec(row.get("section_u_global_xyz"), f"{label} section u axis"),
        _vec(row.get("section_v_global_xyz"), f"{label} section v axis"),
    ]
    for axis in basis:
        if abs(_dot(axis, axis) - 1.0) > FRAME_TOL:
            raise ActionRefusal(f"{label} saved frame is not unit length")
    if any(
        abs(_dot(basis[first], basis[second])) > FRAME_TOL
        for first, second in ((0, 1), (0, 2), (1, 2))
    ):
        raise ActionRefusal(f"{label} saved frame is not orthogonal")
    _close(
        _cross(basis[0], basis[1]),
        basis[2],
        FRAME_TOL,
        f"{label} saved frame handedness",
    )
    return {"origin": origin, "basis": basis}


def _frame_map(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = plan.get("member_frames_and_step_bindings")
    if not isinstance(rows, list):
        raise ActionRefusal("plan has no member frame list")
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ActionRefusal("plan member frame row is not an object")
        member = row.get("member_id")
        if member not in MEMBER_SET or member in result:
            raise ActionRefusal(
                "plan member frame inventory is missing, extra, or duplicated"
            )
        result[member] = {**_frame(row, f"{member} member"), "source": row}
    if set(result) != MEMBER_SET:
        raise ActionRefusal(
            "plan member frame inventory does not cover the five target bodies"
        )
    return result


def _check_plane_frame(
    plane: dict[str, Any], member_frame: dict[str, Any], plane_id: str
) -> dict[str, Any]:
    origin = _vec(plane.get("plane_origin_global_xyz_mm"), f"{plane_id} origin")
    basis = [
        _vec(plane.get("grain_axis_global_xyz"), f"{plane_id} grain axis"),
        _vec(plane.get("section_u_global_xyz"), f"{plane_id} section u axis"),
        _vec(plane.get("section_v_global_xyz"), f"{plane_id} section v axis"),
    ]
    for index, (actual, expected) in enumerate(
        zip(basis, member_frame["basis"], strict=True)
    ):
        _close(actual, expected, FRAME_TOL, f"{plane_id} saved frame vector {index}")
    _close(
        _cross(basis[0], basis[1]),
        basis[2],
        FRAME_TOL,
        f"{plane_id} frame handedness",
    )
    station = _finite(plane.get("grain_station_mm"), f"{plane_id} station")
    observed_station = _dot(_sub(origin, member_frame["origin"]), basis[0])
    _close(
        [station],
        [observed_station],
        STATION_TOL,
        f"{plane_id} station/origin join",
    )
    tolerance = _finite(
        plane.get("coincidence_tolerance_mm"), f"{plane_id} coincidence tolerance"
    )
    if tolerance <= 0:
        raise ActionRefusal(f"{plane_id} coincidence tolerance is not positive")
    return {
        "plane_origin_global_xyz_mm": origin,
        "basis": basis,
        "grain_station_mm": station,
        "coincidence_tolerance_mm": tolerance,
    }


def _identity_key(row: dict[str, Any]) -> str:
    identity = row.get("identity_key")
    if not isinstance(identity, str) or not identity:
        raise ActionRefusal("point inventory row has no stable identity key")
    return identity


def _point_inventory(
    plan: dict[str, Any], frames: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    rows = plan.get("point_inventory")
    if not isinstance(rows, list):
        raise ActionRefusal("plan has no point inventory")
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ActionRefusal("plan point inventory row is not an object")
        key = _identity_key(row)
        kind = row.get("kind")
        member = row.get("member_id")
        if kind not in {INTERFACE_ENDPOINT, BODY_LOAD_NODE, BORE_CENTER}:
            raise ActionRefusal(f"{key} has an unknown point inventory kind")
        if member not in MEMBER_SET or key in result:
            raise ActionRefusal(f"{key} has an invalid member or duplicate identity")
        point = _vec(row.get("point_global_xyz_mm"), f"{key} point")
        station = _finite(row.get("grain_station_mm"), f"{key} grain station")
        computed_station = _dot(
            _sub(point, frames[member]["origin"]), frames[member]["basis"][0]
        )
        _close([station], [computed_station], STATION_TOL, f"{key} grain station")
        normalized = dict(row)
        normalized["point_global_xyz_mm"] = point
        normalized["grain_station_mm"] = station
        if kind == INTERFACE_ENDPOINT:
            name, endpoint = row.get("source_connection_name"), row.get("endpoint")
            if not isinstance(name, str) or endpoint not in {"first", "second"}:
                raise ActionRefusal(f"{key} has an invalid interface endpoint identity")
            if key != f"interface:{name}:endpoint:{endpoint}":
                raise ActionRefusal(
                    f"{key} does not match its interface endpoint identity"
                )
        elif kind == BODY_LOAD_NODE:
            node = _node_id(row.get("node_id"), f"{key} node ID")
            if key != f"load:{member}:node:{node}":
                raise ActionRefusal(f"{key} does not match its body-load node identity")
            normalized["node_id"] = node
        else:
            if not key.startswith("receiver_bore:"):
                raise ActionRefusal(f"{key} does not match its bore-center identity")
        result[key] = normalized
    return result


def _plane_partitions(
    plan: dict[str, Any],
    frames: dict[str, dict[str, Any]],
    points: dict[str, dict[str, Any]],
    boundary_report: dict[str, Any],
    models_by_case: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    planes = plan.get("section_planes")
    if not isinstance(planes, list) or not planes:
        raise ActionRefusal("plan has no section planes")
    state_by_case = {
        case: next(
            state
            for state in boundary_report["states"]
            if state.get("case_id") == case and state.get("increment_index") == 0
        )
        for case in CASES
    }
    partitions, internals = [], {}
    seen = set()
    for plane in planes:
        if not isinstance(plane, dict):
            raise ActionRefusal("section plane row is not an object")
        plane_id, member = plane.get("plane_id"), plane.get("member_id")
        if not isinstance(plane_id, str) or not plane_id or plane_id in seen:
            raise ActionRefusal("section plane ID is missing or duplicated")
        seen.add(plane_id)
        if member not in MEMBER_SET:
            raise ActionRefusal(f"{plane_id} is not on a target member")
        frame = _check_plane_frame(plane, frames[member], plane_id)
        tolerance = frame["coincidence_tolerance_mm"]
        source_identities = plane.get("source_identities", [])
        if (
            not isinstance(source_identities, list)
            or type(plane.get("source_identity_count")) is not int
            or plane.get("source_identity_count") != len(source_identities)
        ):
            raise ActionRefusal(f"{plane_id} source identity count changed")
        source_keys = []
        for identity in source_identities:
            if not isinstance(identity, dict):
                raise ActionRefusal(f"{plane_id} has a malformed source identity")
            key = identity.get("identity_key")
            if not isinstance(key, str) or not key:
                raise ActionRefusal(f"{plane_id} has a source identity without a key")
            source_keys.append(key)
        if len(set(source_keys)) != len(source_keys):
            raise ActionRefusal(f"{plane_id} has duplicate source identities")
        expected_source_keys = sorted(
            key
            for key, point in points.items()
            if point["member_id"] == member
            and abs(point["grain_station_mm"] - frame["grain_station_mm"]) <= tolerance
        )
        if sorted(source_keys) != expected_source_keys:
            raise ActionRefusal(
                f"{plane_id} source identities do not match point inventory"
            )
        sides: dict[str, list[str]] = {"before": [], "on_plane": [], "after": []}
        for key, point in points.items():
            if point["member_id"] != member or point["kind"] not in ACTION_KINDS:
                continue
            signed_distance = _dot(
                _sub(point["point_global_xyz_mm"], frame["plane_origin_global_xyz_mm"]),
                frame["basis"][0],
            )
            station_distance = point["grain_station_mm"] - frame["grain_station_mm"]
            _close(
                [signed_distance],
                [station_distance],
                STATION_TOL,
                f"{plane_id} {key} station projection",
            )
            side = (
                "on_plane"
                if abs(signed_distance) <= tolerance
                else "before"
                if signed_distance < 0
                else "after"
            )
            sides[side].append(key)
        for values in sides.values():
            values.sort()

        contact_events = _contact_plane_events(
            plane_id,
            member,
            frame,
            state_by_case[CASES[0]]["interface_actions"],
            models_by_case[CASES[0]],
            points,
        )
        on_plane_contacts = []
        for key in sides["on_plane"]:
            point = points[key]
            if point["kind"] != INTERFACE_ENDPOINT:
                continue
            row = state_by_case[CASES[0]]["interface_actions"][
                point["source_connection_name"]
            ]
            role = _resolved_role(
                row,
                models_by_case[CASES[0]],
                point["source_connection_name"],
            )
            if role == "timber_or_panel_contact":
                on_plane_contacts.append(
                    _contact_source_identity(key, row, point["endpoint"], role)
                )
        partition = {
            "plane_id": plane_id,
            "member_id": member,
            "grain_station_mm": frame["grain_station_mm"],
            "plane_origin_global_xyz_mm": frame["plane_origin_global_xyz_mm"],
            "frame_g_q_r_global_xyz": frame["basis"],
            "coincidence_tolerance_mm": tolerance,
            "plan_source_identity_count": len(source_identities),
            "plan_source_identity_keys": sorted(source_keys),
            "action_identity_count": sum(len(values) for values in sides.values()),
            "before_action_identity_keys": sides["before"],
            "on_plane_jump_identity_keys": sides["on_plane"],
            "after_action_identity_keys": sides["after"],
            "on_plane_contact_source_identities": on_plane_contacts,
            "modeled_contact_segment_plane_events": contact_events,
            "contact_pressure_or_distributed_traction_established": False,
        }
        partitions.append(partition)
        internals[plane_id] = {**frame, "member_id": member, "sides": sides}
    if {row["member_id"] for row in partitions} != MEMBER_SET:
        raise ActionRefusal(
            "section plane inventory does not cover the five target members"
        )
    return partitions, internals


def _resolved_role(row: dict[str, Any], model: dict[str, Any], name: str) -> str | None:
    response_role = row.get("role")
    owner = model.get("connection_ownership", {}).get(name, {})
    owner_role = owner.get("role")
    raw_roles = {
        raw.get("physical_owner", {}).get("role")
        for raw in model.get("raw_source_carrier_law_inventory_rows", [])
        if raw.get("name") == name
    }
    raw_roles.discard(None)
    if len(raw_roles) > 1:
        raise ActionRefusal(f"{name} raw source rows have conflicting owner roles")
    raw_role = next(iter(raw_roles), None)
    if owner_role is not None and raw_role is not None and owner_role != raw_role:
        raise ActionRefusal(f"{name} model ownership/source roles disagree")
    model_role = owner_role if owner_role is not None else raw_role
    if (
        response_role is not None
        and model_role is not None
        and response_role != model_role
    ):
        raise ActionRefusal(f"{name} response/source roles disagree")
    return response_role if response_role is not None else model_role


def _contact_source_identity(
    identity_key: str, row: dict[str, Any], endpoint: str, role: str
) -> dict[str, Any]:
    normal = row.get("scalar_normal")
    area = row.get("source_area_mm2")
    return {
        "identity_key": identity_key,
        "source_connection_name": row.get("name"),
        "endpoint": endpoint,
        "role": role,
        "source_row_ids": list(row.get("source_row_ids", [])),
        "scalar_normal_global_xyz": _vec(normal, "contact source normal")
        if normal is not None
        else None,
        "source_area_mm2": _finite(area, "contact source area")
        if area is not None
        else None,
        "floor_tangent_state": row.get("floor_tangent_state"),
    }


def _contact_plane_events(
    plane_id: str,
    member: str,
    frame: dict[str, Any],
    interface_rows: dict[str, dict[str, Any]],
    model: dict[str, Any],
    points: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    events = []
    for name, row in sorted(interface_rows.items()):
        if member not in (row.get("first"), row.get("second")):
            continue
        if _resolved_role(row, model, name) != "timber_or_panel_contact":
            continue
        endpoint_data = []
        for endpoint in ("first", "second"):
            point = _vec(
                row.get(endpoint + "_point", row.get("point")),
                f"{name} {endpoint} contact point",
            )
            distance = _dot(
                _sub(point, frame["plane_origin_global_xyz_mm"]), frame["basis"][0]
            )
            tolerance = frame["coincidence_tolerance_mm"]
            side = (
                "on_plane"
                if abs(distance) <= tolerance
                else "before"
                if distance < 0
                else "after"
            )
            body = row[endpoint]
            identity_key = f"interface:{name}:endpoint:{endpoint}"
            endpoint_data.append(
                {
                    "endpoint": endpoint,
                    "member_id": body,
                    "point_global_xyz_mm": point,
                    "signed_distance_to_plane_mm": distance,
                    "side": side,
                    "identity_key": identity_key if identity_key in points else None,
                }
            )
        first_side, second_side = endpoint_data[0]["side"], endpoint_data[1]["side"]
        if first_side == second_side == "on_plane":
            event_kind = "both_endpoints_on_plane"
        elif "on_plane" in (first_side, second_side):
            event_kind = "touches_plane"
        elif {first_side, second_side} == {"before", "after"}:
            event_kind = "crosses_plane"
        else:
            continue
        events.append(
            {
                "event_kind": event_kind,
                "plane_id": plane_id,
                "source_connection_name": name,
                "source_row_ids": list(row.get("source_row_ids", [])),
                "role": "timber_or_panel_contact",
                "scalar_normal_global_xyz": _vec(
                    row["scalar_normal"], f"{name} contact normal"
                )
                if row.get("scalar_normal") is not None
                else None,
                "source_area_mm2": _finite(
                    row["source_area_mm2"], f"{name} contact area"
                )
                if row.get("source_area_mm2") is not None
                else None,
                "endpoints": endpoint_data,
                "force_or_traction_assigned_to_cut": False,
            }
        )
    return events


def _model_roles(model: dict[str, Any], case: str) -> dict[str, str | None]:
    ownership = model.get("connection_ownership", {})
    raw_by_name: dict[str, set[str]] = defaultdict(set)
    for raw in model.get("raw_source_carrier_law_inventory_rows", []):
        if not isinstance(raw, dict):
            raise ActionRefusal(f"{case} source carrier inventory has a malformed row")
        name = raw.get("name")
        owner = raw.get("physical_owner")
        if isinstance(name, str) and isinstance(owner, dict):
            role = owner.get("role")
            if role is not None:
                raw_by_name[name].add(role)
    result = {}
    for name, owner in ownership.items():
        if not isinstance(owner, dict):
            raise ActionRefusal(f"{case} model ownership row {name} is malformed")
        roles = raw_by_name.get(name, set())
        if len(roles) > 1:
            raise ActionRefusal(f"{case} {name} raw source owner roles conflict")
        raw_role = next(iter(roles), None)
        owner_role = owner.get("role")
        if owner_role is not None and raw_role is not None and owner_role != raw_role:
            raise ActionRefusal(f"{case} {name} model/source owner roles disagree")
        result[name] = owner_role if owner_role is not None else raw_role
    for name, roles in raw_by_name.items():
        if name not in result:
            if len(roles) > 1:
                raise ActionRefusal(f"{case} {name} raw source owner roles conflict")
            result[name] = next(iter(roles), None)
    return result


def _validated_interface_inventory(
    case: str, case_record: dict[str, Any], model: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    inventory = case_record.get("inventory")
    if not isinstance(inventory, list):
        raise ActionRefusal(f"{case} whole-boundary interface inventory is missing")
    raw_rows = model.get("raw_source_carrier_law_inventory_rows")
    if not isinstance(raw_rows, list):
        raise ActionRefusal(f"{case} model source carrier inventory is missing")

    grouped: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(raw_rows):
        if not isinstance(raw, dict):
            raise ActionRefusal(f"{case} source carrier row {index} is malformed")
        owner = raw.get("physical_owner")
        if not isinstance(owner, dict):
            raise ActionRefusal(f"{case} source carrier row {index} has no owner")
        first, second = owner.get("first"), owner.get("second")
        if not isinstance(first, str) or not isinstance(second, str) or first == second:
            raise ActionRefusal(
                f"{case} source carrier row {index} has invalid endpoints"
            )
        if first not in MEMBER_SET and second not in MEMBER_SET:
            continue
        name = raw.get("name")
        if not isinstance(name, str) or not name:
            raise ActionRefusal(f"{case} source carrier row {index} has no name")
        if raw.get("first_body") != first or raw.get("second_body") != second:
            raise ActionRefusal(f"{case} {name} raw owner/body endpoints disagree")
        group = grouped.setdefault(
            name, {"owner": owner, "source_inventory_row_indices": []}
        )
        if group["owner"] != owner:
            raise ActionRefusal(f"{case} {name} scalar rows have different owners")
        group["source_inventory_row_indices"].append(index)

    inventory_by_name = {}
    census = []
    for row in inventory:
        if not isinstance(row, dict):
            raise ActionRefusal(f"{case} interface inventory has a malformed row")
        name = row.get("source_connection_name")
        if not isinstance(name, str) or not name or name in inventory_by_name:
            raise ActionRefusal(
                f"{case} interface inventory name is missing or duplicated"
            )
        owner = row.get("owner")
        source_indices = row.get("source_indices")
        if not isinstance(owner, dict) or not isinstance(source_indices, list):
            raise ActionRefusal(
                f"{case} {name} inventory owner or indices are malformed"
            )
        if any(type(value) is not int or value < 0 for value in source_indices):
            raise ActionRefusal(f"{case} {name} scalar inventory indices are invalid")
        if len(set(source_indices)) != len(source_indices) or not source_indices:
            raise ActionRefusal(
                f"{case} {name} scalar inventory indices are empty or repeated"
            )
        grouped_row = grouped.get(name)
        if grouped_row is None:
            raise ActionRefusal(
                f"{case} {name} is absent from the model source inventory"
            )
        if owner != grouped_row["owner"]:
            raise ActionRefusal(f"{case} {name} boundary/model owner join differs")
        expected_indices = grouped_row["source_inventory_row_indices"]
        if source_indices != expected_indices:
            raise ActionRefusal(f"{case} {name} scalar source row membership differs")
        first, second = owner.get("first"), owner.get("second")
        selected_count = int(first in MEMBER_SET) + int(second in MEMBER_SET)
        if selected_count not in (1, 2):
            raise ActionRefusal(f"{case} {name} is not an in-scope interface")
        internal = selected_count == 2
        inventory_by_name[name] = {
            "owner": owner,
            "source_inventory_row_indices": list(source_indices),
            "interface_class": "internal" if internal else "boundary",
        }
        census.append(
            {
                "source_connection_name": name,
                "first_endpoint_member": first,
                "second_endpoint_member": second,
                "source_owner_role": owner.get("role"),
                "interface_class": "internal" if internal else "boundary",
                "source_inventory_row_indices": list(source_indices),
            }
        )

    if set(inventory_by_name) != set(grouped):
        raise ActionRefusal(
            f"{case} complete interface inventory does not match model rows"
        )
    if case_record.get("interface_count") != len(inventory_by_name):
        raise ActionRefusal(f"{case} whole-boundary interface count changed")
    census.sort(key=lambda row: row["source_connection_name"])
    return inventory_by_name, census


def _record_point(
    *,
    identity: dict[str, Any],
    force: list[float],
    radius: list[float],
    source_metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "identity_key": identity["identity_key"],
        "kind": identity["kind"],
        "member_id": identity["member_id"],
        "point_global_xyz_mm": identity["point_global_xyz_mm"],
        "grain_station_mm": identity["grain_station_mm"],
        "force_global_xyz_n": force,
        "force_rounding_radius_global_xyz_n": radius,
        "source_metadata": source_metadata,
    }


def _make_point_actions(
    case: str,
    load_factor: float,
    interface_rows: dict[str, dict[str, Any]],
    model: dict[str, Any],
    points: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    actions = []
    roles = _model_roles(model, case)
    for name, row in sorted(interface_rows.items()):
        if (
            row.get("name", name) != name
            or row.get("source_connection_name", name) != name
        ):
            raise ActionRefusal(f"{case} boundary interface name changed: {name}")
        first, second = row.get("first"), row.get("second")
        if not isinstance(first, str) or not isinstance(second, str) or first == second:
            raise ActionRefusal(f"{case} {name} has invalid source endpoints")
        resolved_role = _resolved_role(row, model, name)
        for endpoint in ("first", "second"):
            member = row[endpoint]
            if member not in MEMBER_SET:
                continue
            key = f"interface:{name}:endpoint:{endpoint}"
            identity = points.get(key)
            if identity is None or identity["kind"] != INTERFACE_ENDPOINT:
                raise ActionRefusal(
                    f"{case} {name} {endpoint} endpoint is not in the plan"
                )
            if identity["member_id"] != member:
                raise ActionRefusal(f"{case} {name} {endpoint} endpoint member changed")
            point = _vec(
                row.get(endpoint + "_point", row.get("point")),
                f"{case} {name} {endpoint} action point",
            )
            _close(
                point,
                identity["point_global_xyz_mm"],
                1e-8,
                f"{case} {name} {endpoint} plan/source point join",
            )
            force = _vec(
                row.get("force_on_" + endpoint + "_xyz_n"),
                f"{case} {name} {endpoint} force",
            )
            radius_value = row.get("force_rounding_radius_xyz_n")
            if radius_value is None:
                raise ActionRefusal(f"{case} {name} has no saved force rounding radius")
            radius = _vec(radius_value, f"{case} {name} force radius")
            if any(value < 0 for value in radius):
                raise ActionRefusal(f"{case} {name} force radius is negative")
            normal = row.get("scalar_normal")
            area = row.get("source_area_mm2")
            metadata = {
                "source_connection_name": name,
                "endpoint": endpoint,
                "other_endpoint_member": row[
                    "second" if endpoint == "first" else "first"
                ],
                "response_role": row.get("role"),
                "model_source_role": roles.get(name),
                "resolved_source_role": resolved_role,
                "source_role_origin": "boundary response"
                if row.get("role") is not None
                else "model ownership and carrier inventory",
                "source_row_ids": list(row.get("source_row_ids", [])),
                "source_inventory_rows": row.get("source_inventory_rows", []),
                "scalar_normal_global_xyz": _vec(normal, f"{case} {name} source normal")
                if normal is not None
                else None,
                "source_area_mm2": _finite(area, f"{case} {name} source area")
                if area is not None
                else None,
                "floor_tangent_state": row.get("floor_tangent_state"),
            }
            actions.append(
                _record_point(
                    identity=identity,
                    force=force,
                    radius=radius,
                    source_metadata=metadata,
                )
            )

    nodes = model.get("nodes", {})
    loads_by_body = model.get("physical_body_loads", {})
    for member in MEMBERS:
        load_rows = loads_by_body.get(member)
        if not isinstance(load_rows, dict):
            raise ActionRefusal(f"{case} has no physical body load map for {member}")
        seen_nodes = set()
        for raw_node, raw_force in sorted(
            load_rows.items(),
            key=lambda item: _node_id(item[0], f"{case} {member} load node"),
        ):
            node = _node_id(raw_node, f"{case} {member} load node")
            if node in seen_nodes:
                raise ActionRefusal(f"{case} {member} has a duplicate load node")
            seen_nodes.add(node)
            key = f"load:{member}:node:{node}"
            identity = points.get(key)
            if identity is None or identity["kind"] != BODY_LOAD_NODE:
                raise ActionRefusal(
                    f"{case} physical body load {key} is not in the plan"
                )
            if identity.get("node_id") != node or identity["member_id"] != member:
                raise ActionRefusal(
                    f"{case} physical body load identity changed: {key}"
                )
            model_point = nodes.get(str(node))
            if model_point is None:
                raise ActionRefusal(
                    f"{case} {member} load node {node} has no model coordinate"
                )
            _close(
                _vec(model_point, f"{case} {member} node {node} coordinate"),
                identity["point_global_xyz_mm"],
                1e-8,
                f"{case} {member} node {node} plan/model point join",
            )
            raw_vector = _vec(raw_force, f"{case} {member} node {node} raw load")
            force = [load_factor * component for component in raw_vector]
            actions.append(
                _record_point(
                    identity=identity,
                    force=force,
                    radius=[0.0, 0.0, 0.0],
                    source_metadata={
                        "node_id": node,
                        "load_factor": load_factor,
                        "unscaled_model_load_global_xyz_n": raw_vector,
                        "rounding_radius_source": "frozen model input load; no response-token radius supplied",
                    },
                )
            )
        planned = {
            key
            for key, identity in points.items()
            if identity["kind"] == BODY_LOAD_NODE and identity["member_id"] == member
        }
        observed = {f"load:{member}:node:{node}" for node in seen_nodes}
        if observed != planned:
            raise ActionRefusal(
                f"{case} {member} physical load node coverage differs from plan"
            )
    expected = {
        key for key, identity in points.items() if identity["kind"] in ACTION_KINDS
    }
    observed = {row["identity_key"] for row in actions}
    if len(observed) != len(actions) or observed != expected:
        raise ActionRefusal(
            f"{case} saved point actions do not exactly cover the plan inventory"
        )
    return actions


def _wrench(
    actions: list[dict[str, Any]], datum: list[float]
) -> dict[str, list[float]]:
    forces, moments, force_radii, moment_radii = [], [], [], []
    for action in actions:
        force = action["force_global_xyz_n"]
        radius = action["force_rounding_radius_global_xyz_n"]
        arm = _sub(action["point_global_xyz_mm"], datum)
        forces.append(force)
        moments.append(_cross(arm, force))
        force_radii.append(radius)
        moment_radii.append(_interval_cross_radius(arm, radius))
    return {
        "force_xyz_n": _sum_vectors(forces),
        "moment_xyz_nmm": _sum_vectors(moments),
        "force_rounding_radius_xyz_n": _sum_vectors(force_radii),
        "moment_rounding_radius_xyz_nmm": _sum_vectors(moment_radii),
    }


def _saved_vector(mapping: dict[str, Any], key: str, label: str) -> list[float]:
    return _vec(mapping.get(key), label)


def _reconstruct_member_balances(
    case: str,
    state: dict[str, Any],
    model: dict[str, Any],
    case_source: dict[str, Any],
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    balances = state.get("member_balances")
    if not isinstance(balances, dict) or set(balances) != MEMBER_SET:
        raise ActionRefusal(f"{case} saved member balance inventory changed")
    output = []
    for member in MEMBERS:
        saved = balances[member]
        datum = _vec(saved.get("datum_global_xyz_mm"), f"{case} {member} source datum")
        reporting_datum = case_source.get("reporting_datums_xyz_mm", {}).get(member)
        if reporting_datum is not None:
            _close(
                datum,
                _vec(reporting_datum, f"{case} {member} case datum"),
                1e-8,
                f"{case} {member} reporting datum join",
            )
        member_actions = [row for row in actions if row["member_id"] == member]
        interface_actions = [
            row for row in member_actions if row["kind"] == INTERFACE_ENDPOINT
        ]
        external_actions = [
            row for row in member_actions if row["kind"] == BODY_LOAD_NODE
        ]
        observed_interface = _wrench(interface_actions, datum)
        observed_external = _wrench(external_actions, datum)
        observed_combined = _wrench(member_actions, datum)
        saved_interface = saved.get("interface_action_wrench", {})
        saved_external = saved.get("external_load_wrench", {})
        saved_combined = saved.get("combined_residual_wrench", {})
        deltas = {}
        for label, observed, source in (
            ("interface", observed_interface, saved_interface),
            ("external", observed_external, saved_external),
            ("combined", observed_combined, saved_combined),
        ):
            force_key = "force_xyz_n"
            moment_key = "moment_xyz_nmm"
            force = _saved_vector(
                source, force_key, f"{case} {member} saved {label} force"
            )
            moment = _saved_vector(
                source, moment_key, f"{case} {member} saved {label} moment"
            )
            force_delta = [
                a - b for a, b in zip(observed["force_xyz_n"], force, strict=True)
            ]
            moment_delta = [
                a - b for a, b in zip(observed["moment_xyz_nmm"], moment, strict=True)
            ]
            _close(
                force_delta,
                [0.0] * 3,
                FORCE_ARITHMETIC_TOL_N,
                f"{case} {member} {label} force reconstruction",
            )
            _close(
                moment_delta,
                [0.0] * 3,
                MOMENT_ARITHMETIC_TOL_NMM,
                f"{case} {member} {label} moment reconstruction",
            )
            deltas[label] = {"force_xyz_n": force_delta, "moment_xyz_nmm": moment_delta}
        saved_force_radius = _vec(
            saved.get("source_force_radius_N"), f"{case} {member} source force radius"
        )
        saved_moment_radius = _vec(
            saved.get("source_moment_radius_Nmm"),
            f"{case} {member} source moment radius",
        )
        force_radius_delta = [
            a - b
            for a, b in zip(
                observed_interface["force_rounding_radius_xyz_n"],
                saved_force_radius,
                strict=True,
            )
        ]
        moment_radius_delta = [
            a - b
            for a, b in zip(
                observed_interface["moment_rounding_radius_xyz_nmm"],
                saved_moment_radius,
                strict=True,
            )
        ]
        _close(
            force_radius_delta,
            [0.0] * 3,
            FORCE_ARITHMETIC_TOL_N,
            f"{case} {member} force radius reconstruction",
        )
        _close(
            moment_radius_delta,
            [0.0] * 3,
            MOMENT_ARITHMETIC_TOL_NMM,
            f"{case} {member} moment radius reconstruction",
        )
        names = saved.get("interface_source_connection_names")
        observed_names = sorted(
            {
                row["source_metadata"]["source_connection_name"]
                for row in interface_actions
            }
        )
        if names != observed_names:
            raise ActionRefusal(f"{case} {member} interface source-name census changed")
        output.append(
            {
                "member_id": member,
                "reporting_datum_global_xyz_mm": datum,
                "interface_point_action_wrench": observed_interface,
                "external_model_load_wrench": observed_external,
                "combined_point_action_wrench": observed_combined,
                "interface_source_connection_names": observed_names,
                "saved_boundary_member_balance_arithmetic_deltas": deltas,
                "source_force_radius_reconstruction_delta_n": force_radius_delta,
                "source_moment_radius_reconstruction_delta_nmm": moment_radius_delta,
                "saved_source_raw_balance_passed": saved.get("raw_balance_passed"),
                "saved_source_rounding_interval_balance_passed": saved.get(
                    "rounding_interval_balance_passed"
                ),
                "arithmetic_match_status": "MATCH_SAVED_BOUNDARY_MEMBER_BALANCE",
            }
        )
    return output


def _aggregate_plane_actions(
    actions: list[dict[str, Any]],
    identity_keys: list[str],
    plane: dict[str, Any],
) -> dict[str, Any]:
    by_key = {row["identity_key"]: row for row in actions}
    selected = [by_key[key] for key in identity_keys]
    global_wrench = _wrench(selected, plane["plane_origin_global_xyz_mm"])
    basis = plane["basis"]
    local_wrench = {
        "force_gqr_n": _project(global_wrench["force_xyz_n"], basis),
        "moment_gqr_nmm": _project(global_wrench["moment_xyz_nmm"], basis),
        "force_rounding_radius_gqr_n": _project_radius(
            global_wrench["force_rounding_radius_xyz_n"], basis
        ),
        "moment_rounding_radius_gqr_nmm": _project_radius(
            global_wrench["moment_rounding_radius_xyz_nmm"], basis
        ),
    }
    return {
        "point_action_count": len(selected),
        "wrench_global": global_wrench,
        "wrench_in_saved_g_q_r_frame": local_wrench,
        "signed_actions_preserved": True,
    }


def build_actions(
    plan: dict[str, Any],
    boundary_report: dict[str, Any],
    models_by_case: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Join a frozen section plan to every saved boundary and body-load action."""
    frames = _frame_map(plan)
    points = _point_inventory(plan, frames)
    if set(models_by_case) != set(CASES):
        raise ActionRefusal("models_by_case must contain the three frozen rear cases")
    if (
        boundary_report.get("status")
        != "PASS_RIGHT_FIVE_BODY_BOUNDARY_RECONSTRUCTION_ONLY"
    ):
        raise ActionRefusal("whole-boundary source reconstruction did not pass")
    report_cases = boundary_report.get("cases")
    states = boundary_report.get("states")
    if not isinstance(report_cases, dict) or set(report_cases) != set(CASES):
        raise ActionRefusal("whole-boundary report case inventory changed")
    if not isinstance(states, list) or len(states) != len(CASES) * len(LOAD_FACTORS):
        raise ActionRefusal("whole-boundary report does not contain 21 states")
    if set(boundary_report.get("members", [])) != MEMBER_SET:
        raise ActionRefusal("whole-boundary report target-member inventory changed")

    point_actions_by_case = {}
    expected_interface_keys: set[str] | None = None
    expected_load_keys: set[str] | None = None
    source_interface_count: int | None = None
    expected_interface_census: list[dict[str, Any]] | None = None
    interface_census_by_case = {}
    interface_counts_by_case = {}
    for case in CASES:
        model = models_by_case[case]
        if model.get("case_id") != case:
            raise ActionRefusal(f"{case} model case identity changed")
        case_record = report_cases[case]
        interface_inventory, interface_census = _validated_interface_inventory(
            case, case_record, model
        )
        inventory_names = sorted(interface_inventory)
        if source_interface_count is None:
            source_interface_count = len(inventory_names)
        elif source_interface_count != len(inventory_names):
            raise ActionRefusal(
                "whole-boundary interface row count differs across cases"
            )
        if expected_interface_census is None:
            expected_interface_census = interface_census
        elif interface_census != expected_interface_census:
            raise ActionRefusal(
                "whole-boundary interface ownership differs across cases"
            )
        interface_census_by_case[case] = interface_census
        internal_inventory_count = sum(
            row["interface_class"] == "internal" for row in interface_census
        )
        boundary_inventory_count = len(interface_census) - internal_inventory_count
        interface_counts_by_case[case] = {
            "source_interface_row_count": len(interface_census),
            "internal_interface_row_count": internal_inventory_count,
            "boundary_interface_row_count": boundary_inventory_count,
            "scalar_source_row_count": sum(
                len(row["source_inventory_row_indices"]) for row in interface_census
            ),
        }
        case_states = [state for state in states if state.get("case_id") == case]
        if len(case_states) != len(LOAD_FACTORS):
            raise ActionRefusal(f"{case} whole-boundary increment count changed")
        model_load_keys = set()
        loads = model.get("physical_body_loads", {})
        for member in MEMBERS:
            member_loads = loads.get(member)
            if not isinstance(member_loads, dict):
                raise ActionRefusal(f"{case} model has no physical loads for {member}")
            for raw_node in member_loads:
                model_load_keys.add(
                    f"load:{member}:node:{_node_id(raw_node, f'{case} {member} load node')}"
                )
        if expected_load_keys is None:
            expected_load_keys = model_load_keys
        elif model_load_keys != expected_load_keys:
            raise ActionRefusal(
                "target-member physical load node set differs across cases"
            )
        load_inventory_keys = {
            key
            for key, identity in points.items()
            if identity["kind"] == BODY_LOAD_NODE
        }
        if load_inventory_keys != model_load_keys:
            raise ActionRefusal(
                f"{case} physical body load nodes do not match the plan"
            )
        for key in load_inventory_keys:
            source_cases = points[key].get("source_cases")
            if not isinstance(source_cases, list) or set(source_cases) != set(CASES):
                raise ActionRefusal(f"{key} does not join all three source cases")
        by_state = {}
        for state in case_states:
            index = state.get("increment_index")
            if type(index) is not int or index < 0 or index >= len(LOAD_FACTORS):
                raise ActionRefusal(f"{case} has an invalid increment index")
            factor = _finite(
                state.get("load_factor"), f"{case} increment {index} load factor"
            )
            if factor != LOAD_FACTORS[index] or index in by_state:
                raise ActionRefusal(f"{case} increment/load-factor sequence changed")
            rows = state.get("interface_actions")
            if not isinstance(rows, dict) or set(rows) != set(inventory_names):
                raise ActionRefusal(
                    f"{case} increment {index} interface action census changed"
                )
            actual_internal_count = 0
            actual_boundary_count = 0
            active_floor_names = []
            released_floor_names = []
            for name, row in rows.items():
                if not isinstance(row, dict):
                    raise ActionRefusal(
                        f"{case} {name} saved interface action is malformed"
                    )
                owner = interface_inventory[name]["owner"]
                if row.get("first") != owner.get("first") or row.get(
                    "second"
                ) != owner.get("second"):
                    raise ActionRefusal(
                        f"{case} {name} response/model endpoints disagree"
                    )
                source_rows = row.get("source_inventory_rows")
                if not isinstance(source_rows, list) or any(
                    not isinstance(source_row, dict) for source_row in source_rows
                ):
                    raise ActionRefusal(
                        f"{case} {name} response source rows are malformed"
                    )
                source_indices = [
                    source_row.get("source_inventory_row_index")
                    for source_row in source_rows
                ]
                source_row_ids = [
                    source_row.get("source_row_id") for source_row in source_rows
                ]
                if (
                    any(type(value) is not int for value in source_indices)
                    or source_indices
                    != interface_inventory[name]["source_inventory_row_indices"]
                    or any(
                        source_row.get("source_connection_name") != name
                        for source_row in source_rows
                    )
                    or any(
                        not isinstance(value, str) or not value
                        for value in source_row_ids
                    )
                    or len(set(source_row_ids)) != len(source_row_ids)
                    or row.get("source_row_ids") != source_row_ids
                ):
                    raise ActionRefusal(
                        f"{case} {name} response source scalar-row membership differs"
                    )
                if _resolved_role(row, model, name) != owner.get("role"):
                    raise ActionRefusal(
                        f"{case} {name} response/model source owner role differs"
                    )
                first_selected = row.get("first") in MEMBER_SET
                second_selected = row.get("second") in MEMBER_SET
                if first_selected and second_selected:
                    actual_internal_count += 1
                elif first_selected or second_selected:
                    actual_boundary_count += 1
                else:
                    raise ActionRefusal(
                        f"{case} {name} has no selected member endpoint"
                    )
                tangent_state = row.get("floor_tangent_state")
                if owner.get("role") == "assumed_no_slip_floor":
                    if tangent_state == "active_selected_floor_tangent_reaction":
                        active_floor_names.append(name)
                    elif tangent_state == "released_inactive_floor_tangent_zero_action":
                        released_floor_names.append(name)
                        for endpoint in ("first", "second"):
                            _close(
                                _vec(
                                    row.get("force_on_" + endpoint + "_xyz_n"),
                                    f"{case} {name} released floor force",
                                ),
                                [0.0, 0.0, 0.0],
                                0.0,
                                f"{case} {name} released floor action",
                            )
                        _close(
                            _vec(
                                row.get("force_rounding_radius_xyz_n"),
                                f"{case} {name} released floor radius",
                            ),
                            [0.0, 0.0, 0.0],
                            0.0,
                            f"{case} {name} released floor action radius",
                        )
                    else:
                        raise ActionRefusal(
                            f"{case} {name} assumed-floor action has no active/released state"
                        )
                elif tangent_state is not None:
                    raise ActionRefusal(
                        f"{case} {name} has a floor-tangent state under another source role"
                    )
            if actual_internal_count != state.get("internal_interface_count"):
                raise ActionRefusal(
                    f"{case} increment {index} internal interface count changed"
                )
            if actual_boundary_count != state.get("boundary_interface_count"):
                raise ActionRefusal(
                    f"{case} increment {index} boundary interface count changed"
                )
            if actual_internal_count + actual_boundary_count != len(rows):
                raise ActionRefusal(
                    f"{case} increment {index} interface partition is incomplete"
                )
            if (
                actual_internal_count != internal_inventory_count
                or actual_boundary_count != boundary_inventory_count
            ):
                raise ActionRefusal(
                    f"{case} increment {index} endpoint ownership partition differs from inventory"
                )
            if state.get("active_floor_tangent_groups") != len(active_floor_names):
                raise ActionRefusal(
                    f"{case} increment {index} active floor tangent count changed"
                )
            if state.get("released_floor_tangent_groups") != len(released_floor_names):
                raise ActionRefusal(
                    f"{case} increment {index} released floor tangent count changed"
                )
            endpoint_keys = {
                f"interface:{name}:endpoint:{endpoint}"
                for name, row in rows.items()
                for endpoint in ("first", "second")
                if row.get(endpoint) in MEMBER_SET
            }
            if expected_interface_keys is None:
                expected_interface_keys = endpoint_keys
            elif endpoint_keys != expected_interface_keys:
                raise ActionRefusal(
                    "target-member interface endpoint topology differs across states"
                )
            interface_inventory_keys = {
                key
                for key, identity in points.items()
                if identity["kind"] == INTERFACE_ENDPOINT
            }
            if interface_inventory_keys != endpoint_keys:
                raise ActionRefusal(f"{case} interface endpoints do not match the plan")
            point_actions = _make_point_actions(case, factor, rows, model, points)
            if len(point_actions) != len(endpoint_keys) + len(model_load_keys):
                raise ActionRefusal(
                    f"{case} increment {index} point action count changed"
                )
            balances = _reconstruct_member_balances(
                case, state, model, case_record, point_actions
            )
            by_state[index] = {
                "case_id": case,
                "increment_index": index,
                "load_factor": factor,
                "source_interface_row_count": len(rows),
                "internal_interface_row_count": actual_internal_count,
                "boundary_interface_row_count": actual_boundary_count,
                "active_floor_tangent_group_names": sorted(active_floor_names),
                "released_floor_tangent_group_names": sorted(released_floor_names),
                "active_floor_tangent_group_count": len(active_floor_names),
                "released_floor_tangent_group_count": len(released_floor_names),
                "target_member_interface_endpoint_action_count": len(endpoint_keys),
                "physical_body_load_node_action_count": len(model_load_keys),
                "point_action_count": len(point_actions),
                "point_actions": point_actions,
                "member_balance_reconstruction": balances,
            }
        if set(by_state) != set(range(len(LOAD_FACTORS))):
            raise ActionRefusal(
                f"{case} increments do not match the seven frozen factors"
            )
        point_actions_by_case[case] = [
            by_state[index] for index in range(len(LOAD_FACTORS))
        ]

    if expected_interface_keys is None or expected_load_keys is None:
        raise ActionRefusal("source action inventory is empty")
    non_action_bores = [
        key for key, point in points.items() if point["kind"] == BORE_CENTER
    ]
    partitions, plane_map = _plane_partitions(
        plan, frames, points, boundary_report, models_by_case
    )
    cut_states = []
    for case in CASES:
        for state in point_actions_by_case[case]:
            cuts = []
            for partition in partitions:
                plane = plane_map[partition["plane_id"]]
                by_side = {
                    side: _aggregate_plane_actions(
                        state["point_actions"],
                        plane["sides"][side],
                        plane,
                    )
                    for side in ("before", "on_plane", "after")
                }
                cuts.append(
                    {
                        "plane_id": partition["plane_id"],
                        "member_id": partition["member_id"],
                        "geometry_partition_id": partition["plane_id"],
                        "before": by_side["before"],
                        "on_plane_jump": by_side["on_plane"],
                        "after": by_side["after"],
                        "action_identity_counts": {
                            side: len(plane["sides"][side])
                            for side in ("before", "on_plane", "after")
                        },
                        "on_plane_contact_source_identity_count": len(
                            partition["on_plane_contact_source_identities"]
                        ),
                        "modeled_contact_segment_plane_event_count": len(
                            partition["modeled_contact_segment_plane_events"]
                        ),
                        "action_on_disconnected_regions_assigned": False,
                    }
                )
            cut_states.append(
                {
                    "case_id": state["case_id"],
                    "increment_index": state["increment_index"],
                    "load_factor": state["load_factor"],
                    "plane_cut_actions": cuts,
                }
            )

    flat_states = [state for case in CASES for state in point_actions_by_case[case]]
    interface_count = source_interface_count or 0
    return {
        "schema": "wood_joint_right_corner_finished_sections_saved_point_actions/v1",
        "status": "PASS_SAVED_POINT_ACTION_ACCOUNTING_ONLY",
        "members": list(MEMBERS),
        "cases": list(CASES),
        "counts": {
            "case_count": len(CASES),
            "increment_count_per_case": len(LOAD_FACTORS),
            "state_count": len(flat_states),
            "source_interface_rows_per_state": interface_count,
            "interface_counts_by_case": interface_counts_by_case,
            "target_member_interface_endpoint_actions_per_state": len(
                expected_interface_keys
            ),
            "physical_body_load_node_actions_per_state": len(expected_load_keys),
            "full_point_action_records_per_state": len(flat_states[0]["point_actions"]),
            "plan_point_inventory_count": len(points),
            "geometry_only_receiver_bore_center_count": len(non_action_bores),
            "section_plane_count": len(partitions),
            "state_plane_cut_count": len(cut_states) * len(partitions),
            "interface_census_preserved": all(
                state["source_interface_row_count"] == interface_count
                for state in flat_states
            ),
            "released_floor_zero_actions_retained": all(
                row["force_global_xyz_n"] == [0.0, 0.0, 0.0]
                for state in flat_states
                for row in state["point_actions"]
                if row["source_metadata"].get("floor_tangent_state")
                == "released_inactive_floor_tangent_zero_action"
            ),
        },
        "arithmetic_limits": {
            "force_n": FORCE_ARITHMETIC_TOL_N,
            "moment_nmm": MOMENT_ARITHMETIC_TOL_NMM,
            "purpose": "source point-action bookkeeping comparisons only; no change to source physical gates",
        },
        "method_boundary": {
            "action_point_records_stored_once_per_state": True,
            "side_identity_partitions_stored_once_per_plane": True,
            "before_on_plane_after_are_separate": True,
            "forces_are_signed_saved_point_actions": True,
            "source_interface_rounding_radii_propagated_by_absolute_bounds": True,
            "physical_body_loads_scaled_by_saved_load_factor": True,
            "external_model_load_rounding_radius": "zero radius supplied; retained as exact frozen model input",
            "point_action_sum_is_not_a_finished_section_traction_field": True,
            "disconnected_region_force_or_strain_assignment": False,
            "native_solve_or_new_physical_acceptance_gate": False,
        },
        "plane_identity_partitions": partitions,
        "source_interface_inventory_by_case": interface_census_by_case,
        "point_action_states": flat_states,
        "plane_cut_states": cut_states,
        "limits": [
            "Saved point actions do not recover distributed forces or finished-section tractions.",
            "A cut-side sum is not assigned to disconnected regions, wood fibres, or a capacity calculation.",
            "Contact point segments are geometric crossings only; no contact pressure is inferred.",
            "Source 0.1 N / 2 Nmm physical gates remain those already recorded upstream.",
            "No native solve, stress/strain split, stiffness or resistance qualification, or acceptance claim is made.",
        ],
    }
