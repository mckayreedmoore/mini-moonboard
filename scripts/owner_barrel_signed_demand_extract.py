"""Extract authenticated, simultaneous signed barrel-candidate demands.

This module does not run a solver or assess resistance.  It accepts six
completed native diagnostic directories, verifies their manifested final-cycle
inputs and reports, and emits only per-case actions.  It intentionally creates
no componentwise envelope: force, moment, and contact compression in each row
come from one case and one authenticated final cycle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

SCHEMA = "owner_barrel_signed_demands/v1"
SOLVER_CANDIDATE = "owner-barrel-integrated-native-preparation-v3"
EXPECTED_CASE_COUNT = 6
EXPECTED_STATION_COUNT = 24
EXPECTED_BARREL_COUNT = 46
EXPECTED_BARREL_CONTACT_COUNT = 132
EXPECTED_RETAINED_FASTENER_COUNT = 12
EXPECTED_RETAINED_JOINT_COUNT = 6
EXPECTED_RETAINED_CONTACT_COUNT = 72
EXPECTED_COMBINED_CONTACT_COUNT = 204
VECTOR_TOLERANCE = 1.0e-7

MECHANICS_KEYS = (
    "physical_connection_forces",
    "bearings",
    "force_residual_n",
    "moment_residual_nmm",
    "global_equilibrium_passed",
    "member_equilibrium",
    "member_equilibrium_passed",
    "member_equilibrium_criterion",
    "mpc_check_passed",
    "mpc_printed_precision_audit",
    "closed_bearing_assumption_passed",
    "axial_tension",
    "axial_tension_assumption_passed",
    "radial_clearance",
    "radial_clearance_assumption_passed",
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _vector(value, label: str) -> list[float]:
    _require(isinstance(value, (list, tuple)) and len(value) == 3, f"{label} must be a 3-vector")
    result = [float(component) for component in value]
    _require(all(math.isfinite(component) for component in result), f"{label} must be finite")
    return result


def _dot(first, second) -> float:
    return sum(a * b for a, b in zip(first, second, strict=True))


def _cross(first, second) -> list[float]:
    return [
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    ]


def _add(first, second) -> list[float]:
    return [a + b for a, b in zip(first, second, strict=True)]


def _subtract(first, second) -> list[float]:
    return [a - b for a, b in zip(first, second, strict=True)]


def _scale(value, factor: float) -> list[float]:
    return [factor * component for component in value]


def _norm(value) -> float:
    return math.sqrt(_dot(value, value))


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest(path: Path) -> str:
    return _digest_bytes(path.read_bytes())


def _same_vector(first, second, *, tolerance=VECTOR_TOLERANCE) -> bool:
    return all(abs(a - b) <= tolerance for a, b in zip(first, second, strict=True))


def _force_on(row: dict, member: str, label: str) -> list[float]:
    first = row.get("first")
    second = row.get("second")
    _require(member in (first, second), f"{label}: member is absent from physical connection")
    key = "force_on_first_xyz_n" if member == first else "force_on_second_xyz_n"
    return _vector(row.get(key), f"{label} {key}")


def _wrench(rows: list[tuple[list[float], list[float]]], origin) -> dict:
    force = [0.0, 0.0, 0.0]
    moment = [0.0, 0.0, 0.0]
    for point, action in rows:
        force = _add(force, action)
        moment = _add(moment, _cross(_subtract(point, origin), action))
    return {"force_xyz_n": force, "moment_xyz_nmm": moment}


def _joint_id(members) -> str:
    values = sorted(members)
    _require(len(values) == 2 and values[0] != values[1], "Retained joint must join two members")
    return "--".join(values)


def _register_inventory(register: dict) -> dict:
    cases = tuple(register.get("load_case_order", ()))
    stations = register.get("stations", {})
    retained = register.get("fixed_features", {}).get("retained_frame_bolts", {})
    counts = register.get("counts", {})
    _require(register.get("candidate") == "compact-floor-flush-bolted-development", "Wrong barrel register candidate")
    _require(len(cases) == EXPECTED_CASE_COUNT and len(set(cases)) == EXPECTED_CASE_COUNT, "Require six distinct registered cases")
    _require(set(register.get("load_cases", {})) == set(cases), "Register case metadata is incomplete")
    _require(len(stations) == counts.get("stations") == EXPECTED_STATION_COUNT, "Require 24 registered barrel stations")
    _require(len(retained) == counts.get("retained_frame_bolts") == EXPECTED_RETAINED_FASTENER_COUNT, "Require 12 retained frame bolts")

    barrel_to_station = {}
    contact_to_station = {}
    for station_name, station in stations.items():
        _require(station.get("identity") == station_name, f"{station_name}: station identity mismatch")
        members = station.get("timber_members")
        _require(isinstance(members, list) and len(members) == 2 and len(set(members)) == 2, f"{station_name}: invalid member pair")
        bolts = station.get("bolts", {})
        cells = station.get("contact", {}).get("contact_cells", ())
        _require(bolts and cells, f"{station_name}: missing bolts or contact cells")
        for name, bolt in bolts.items():
            _require(name not in barrel_to_station and bolt.get("name") == name, f"{name}: duplicate or mismatched barrel bolt")
            _require(set(bolt.get("members", ())) == set(members), f"{name}: station member ownership mismatch")
            _require(
                {bolt.get("entry_member"), bolt.get("receiving_member")} == set(members)
                and bolt.get("entry_member") != bolt.get("receiving_member"),
                f"{name}: physical entry/receiver ownership mismatch",
            )
            barrel_to_station[name] = station_name
        for cell in cells:
            name = cell.get("name")
            _require(isinstance(name, str) and name not in contact_to_station, f"{station_name}: duplicate contact cell")
            point = _vector(cell.get("point_xyz_mm"), f"{name} point")
            area = cell.get("tributary_area_mm2")
            _require(isinstance(area, (int, float)) and math.isfinite(area) and area > 0, f"{name}: invalid tributary area")
            contact_to_station[name] = {"station": station_name, "point": point, "area": float(area)}
    _require(len(barrel_to_station) == counts.get("barrel_pairs") == EXPECTED_BARREL_COUNT, "Require 46 registered barrel fasteners")
    _require(
        len(contact_to_station) == EXPECTED_BARREL_CONTACT_COUNT
        and register.get("contact_summary", {}).get("contact_cell_count")
        == EXPECTED_BARREL_CONTACT_COUNT,
        "Require 132 exact barrel contact cells",
    )

    retained_groups = defaultdict(list)
    for name, bolt in retained.items():
        _require(name == bolt.get("name"), f"{name}: retained-bolt identity mismatch")
        members = bolt.get("members")
        _require(isinstance(members, list) and len(members) == 2, f"{name}: retained-bolt members missing")
        retained_groups[_joint_id(members)].append(name)
    _require(len(retained_groups) == EXPECTED_RETAINED_JOINT_COUNT, "Require six retained frame joints")
    _require(all(len(names) == 2 for names in retained_groups.values()), "Each retained joint must have two bolts")
    return {
        "cases": cases,
        "stations": stations,
        "barrel_to_station": barrel_to_station,
        "barrel_contacts": contact_to_station,
        "retained": retained,
        "retained_groups": {name: sorted(values) for name, values in retained_groups.items()},
    }


def _equilibrium(report: dict, case: str) -> dict:
    force = _vector(report.get("force_residual_n"), f"{case} force residual")
    moment = _vector(report.get("moment_residual_nmm"), f"{case} moment residual")
    members = report.get("member_equilibrium")
    _require(isinstance(members, dict) and members, f"{case}: member equilibrium metadata missing")
    _require(all(row.get("passed") is True for row in members.values()), f"{case}: a member equilibrium check failed")
    for name, row in members.items():
        for key in ("maximum_force_residual_n", "maximum_moment_residual_nmm"):
            value = row.get(key)
            _require(
                isinstance(value, (int, float)) and math.isfinite(value) and value >= 0,
                f"{case}: {name} has invalid {key}",
            )
    _require(
        report.get("numerically_accepted") is True
        and report.get("native_numerically_accepted") is True
        and report.get("owner_barrel_wrapper_accepted") is True
        and report.get("retry_checkpoint_eligible") is False
        and report.get("contact_active_set_converged") is True
        and report.get("axial_tension_active_set_converged") is True
        and report.get("radial_clearance_active_set_converged") is True
        and report.get("global_equilibrium_passed") is True
        and report.get("member_equilibrium_passed") is True
        and report.get("mpc_check_passed") is True
        and report.get("closed_bearing_assumption_passed") is True,
        f"{case}: native convergence or equilibrium gate failed",
    )
    audit = report.get("mpc_printed_precision_audit")
    _require(isinstance(audit, dict) and audit.get("passed") is True, f"{case}: MPC precision audit failed")
    return {
        "case": case,
        "global": {
            "force_residual_xyz_n": force,
            "moment_residual_xyz_nmm": moment,
            "passed": True,
        },
        "members": {
            "passed": True,
            "criterion": report.get("member_equilibrium_criterion"),
            "records": members,
        },
        "mpc": {"passed": True, "printed_precision_audit": audit},
        "contact_active_set_converged": True,
        "barrel_axial_active_set_converged": True,
        "barrel_radial_clearance_active_set_converged": True,
    }


def _validate_case_identity(report: dict, record: dict, register: dict, case: str) -> dict:
    scope = report.get("owner_barrel_diagnostic_scope")
    load = register["load_cases"][case]
    _require(report.get("candidate") == record.get("candidate") == SOLVER_CANDIDATE, f"{case}: solver candidate mismatch")
    _require(isinstance(scope, dict) and scope.get("case") == case, f"{case}: diagnostic scope mismatch")
    _require(
        scope.get("candidate") == SOLVER_CANDIDATE
        and scope.get("diagnostic_only") is True
        and scope.get("conditional_only") is True
        and scope.get("joint_resistance_qualified") is False
        and scope.get("qualified_for_design") is False
        and scope.get("drilling_released") is False
        and scope.get("fabrication_released") is False
        and scope.get("diy_released") is False,
        f"{case}: diagnostic scope or release boundary changed",
    )
    _require(
        report.get("qualified_for_design") is False
        and report.get("acceptance") is False
        and report.get("joint_resistance_qualified") is False
        and report.get("structural_released") is False
        and report.get("drilling_released") is False
        and report.get("fabrication_released") is False
        and report.get("diy_released") is False,
        f"{case}: report makes a release claim",
    )
    scope_load = scope.get("case_load")
    _require(
        isinstance(scope_load, dict)
        and scope_load.get("hold") == load["hold"]
        and scope_load.get("horizontal_force_xy_n") == load["horizontal_force_xy_n"]
        and _same_vector(
            _vector(scope_load.get("applied_force_xyz_n"), f"{case} scope force"),
            load["applied_force_xyz_n"],
        )
        and scope_load.get("pounds") == load["requested_climber_weight_lbf"],
        f"{case}: scope load mismatch",
    )
    _require(record.get("hold") == load["hold"], f"{case}: input hold mismatch")
    _require(_same_vector(_vector(record.get("force_xyz_n"), f"{case} input force"), load["applied_force_xyz_n"]), f"{case}: input force mismatch")
    stiffnesses = scope.get("conditional_stiffnesses")
    _require(
        isinstance(stiffnesses, dict)
        and set(stiffnesses) == {
            "barrel_axial_n_per_mm",
            "barrel_lateral_n_per_mm",
            "contact_n_per_mm3",
        }
        and all(isinstance(value, (int, float)) and math.isfinite(value) and value > 0 for value in stiffnesses.values()),
        f"{case}: conditional stiffness basis missing",
    )
    return scope


def _physical_row(name: str, physical: dict, owners: dict) -> dict:
    _require(name in physical and name in owners, f"{name}: physical force or ownership missing")
    row = physical[name]
    owner = owners[name]
    for key in ("first", "second", "point", "axis", "scalar_normal"):
        _require(row.get(key) == owner.get(key), f"{name}: physical ownership differs from final input")
    first = _vector(row.get("force_on_first_xyz_n"), f"{name} force on first")
    second = _vector(row.get("force_on_second_xyz_n"), f"{name} force on second")
    _require(_norm(_add(first, second)) <= VECTOR_TOLERANCE, f"{name}: action-reaction mismatch")
    return row


def _fastener_record(*, case: str, name: str, station: str, bolt: dict, physical: dict, owners: dict, origin, kind: str) -> dict:
    row = _physical_row(name, physical, owners)
    members = (
        [bolt["entry_member"], bolt["receiving_member"]]
        if kind == "barrel_bolt"
        else bolt["members"]
    )
    _require(row.get("first") == members[0] and row.get("second") == members[1], f"{name}: fastener direction or member order changed")
    axis = _vector(row.get("axis"), f"{name} axis")
    _require(abs(_norm(axis) - 1.0) <= 1.0e-8, f"{name}: fastener axis is not unit length")
    _require(
        _same_vector(axis, _vector(bolt.get("direction_xyz"), f"{name} registered axis")),
        f"{name}: fastener axis differs from register",
    )
    point = _vector(row.get("point"), f"{name} point")
    force = _vector(row.get("force_on_first_xyz_n"), f"{name} force")
    axial = _dot(force, axis)
    lateral = _subtract(force, _scale(axis, axial))
    _require(abs(float(row.get("axial_along_installation_direction_n")) - axial) <= 1.0e-6, f"{name}: reported axial decomposition changed")
    _require(abs(float(row.get("transverse_shear_n")) - _norm(lateral)) <= 1.0e-6, f"{name}: reported transverse decomposition changed")
    return {
        "case": case,
        "name": name,
        "kind": kind,
        "station_or_joint": station,
        "first_member": members[0],
        "second_member": members[1],
        "point_xyz_mm": point,
        "axis_xyz": axis,
        "force_on_first_xyz_n": force,
        "force_on_second_xyz_n": _vector(row["force_on_second_xyz_n"], f"{name} second force"),
        "axial_along_installation_direction_n": axial,
        "transverse_shear_xyz_n": lateral,
        "transverse_shear_n": _norm(lateral),
        "moment_about_station_or_joint_origin_nmm": _cross(_subtract(point, origin), force),
        "same_case_only": True,
    }


def _contact_record(*, case: str, name: str, contact: dict, physical: dict, owners: dict, bearings: dict) -> dict:
    row = _physical_row(name, physical, owners)
    bearing = bearings.get(name)
    _require(isinstance(bearing, dict) and isinstance(bearing.get("active"), bool), f"{name}: bearing state missing")
    normal = _vector(row.get("scalar_normal"), f"{name} normal")
    _require(abs(_norm(normal) - 1.0) <= 1.0e-8, f"{name}: contact normal is not unit length")
    _require(
        row.get("first") == contact.get("first")
        and row.get("second") == contact.get("second")
        and _same_vector(
            _vector(row.get("point"), f"{name} physical point"),
            _vector(contact.get("point_xyz_mm"), f"{name} contact point"),
        )
        and _same_vector(
            normal,
            _vector(contact.get("normal_xyz"), f"{name} contact normal"),
        ),
        f"{name}: contact metadata differs from physical ownership",
    )
    force = _vector(row.get("force_on_first_xyz_n"), f"{name} force")
    compression = _dot(force, normal)
    _require(compression >= -1.0e-6, f"{name}: contact carries tension")
    _require(abs(compression - float(bearing.get("compression_force_n"))) <= 1.0e-6, f"{name}: bearing force differs from physical force")
    _require(bearing["active"] or _norm(force) <= 1.0e-6, f"{name}: inactive contact carries force")
    area = float(contact["area"])
    return {
        "case": case,
        "name": name,
        "first_member": row["first"],
        "second_member": row["second"],
        "point_xyz_mm": _vector(row["point"], f"{name} point"),
        "normal_into_first_xyz": normal,
        "active": bearing["active"],
        "force_on_first_xyz_n": force,
        "compression_n": max(0.0, compression),
        "tributary_area_mm2": area,
        "average_cell_pressure_n_per_mm2": max(0.0, compression) / area,
    }


def _interface_resultants(first_member: str, rows: list[dict], origin) -> dict:
    first_actions = []
    second_actions = []
    for row in rows:
        label = row.get("name", "interface connection")
        point = _vector(row["point"], f"{label} point")
        first_actions.append((point, _force_on(row, first_member, label)))
        other = row["second"] if row["first"] == first_member else row["first"]
        second_actions.append((point, _force_on(row, other, label)))
    first = _wrench(first_actions, origin)
    second = _wrench(second_actions, origin)
    residual_force = _add(first["force_xyz_n"], second["force_xyz_n"])
    residual_moment = _add(first["moment_xyz_nmm"], second["moment_xyz_nmm"])
    _require(_norm(residual_force) <= VECTOR_TOLERANCE and _norm(residual_moment) <= 1.0e-5, "Interface action-reaction equilibrium failed")
    return {
        "on_first_member": first,
        "on_second_member": second,
        "action_reaction_residual": {
            "force_xyz_n": residual_force,
            "moment_xyz_nmm": residual_moment,
            "passed": True,
        },
    }


def extract_case(report: dict, record: dict, register: dict, case: str, source: dict | None = None) -> dict:
    """Extract one case from already-loaded, final-cycle solver records."""
    inventory = _register_inventory(register)
    _require(case in inventory["cases"], f"Unknown registered case: {case}")
    scope = _validate_case_identity(report, record, register, case)
    equilibrium = _equilibrium(report, case)
    physical = report.get("physical_connection_forces")
    owners = record.get("connection_ownership")
    contacts = record.get("member_contacts")
    _require(isinstance(physical, dict) and isinstance(owners, dict), f"{case}: physical connection inventory missing")
    _require(isinstance(contacts, list), f"{case}: member-contact inventory missing")
    contact_metadata = {row.get("name"): row for row in contacts}
    _require(None not in contact_metadata and len(contact_metadata) == len(contacts), f"{case}: duplicate contact metadata")
    bearings = {row.get("name"): row for row in report.get("bearings", ())}
    _require(None not in bearings and len(bearings) == len(report.get("bearings", ())), f"{case}: duplicate bearing rows")
    _require(set(contact_metadata) <= set(bearings), f"{case}: member-contact bearing rows are incomplete")

    barrel_contact_names = set(inventory["barrel_contacts"])
    _require(barrel_contact_names <= set(contact_metadata), f"{case}: barrel contact cells missing")
    retained_contact_names = set(contact_metadata) - barrel_contact_names
    _require(len(retained_contact_names) == EXPECTED_RETAINED_CONTACT_COUNT, f"{case}: require 72 retained-joint contact cells")

    retained_contact_groups = defaultdict(list)
    for name in retained_contact_names:
        row = contact_metadata[name]
        joint = _joint_id((row.get("first"), row.get("second")))
        _require(joint in inventory["retained_groups"], f"{name}: contact is not part of a retained joint")
        retained_contact_groups[joint].append(name)
    _require(set(retained_contact_groups) == set(inventory["retained_groups"]), f"{case}: retained-joint contacts incomplete")
    _require(all(len(names) == 12 for names in retained_contact_groups.values()), f"{case}: each retained joint needs 12 contact cells")

    barrel_fasteners = []
    station_rows = []
    for station_name, station in inventory["stations"].items():
        first, second = station["timber_members"]
        origin = _vector(station["contact"]["gross_contact_centroid_xyz_mm"], f"{station_name} origin")
        fastener_names = sorted(station["bolts"])
        contact_names = [cell["name"] for cell in station["contact"]["contact_cells"]]
        fastener_physical = [_physical_row(name, physical, owners) for name in fastener_names]
        contact_physical = [_physical_row(name, physical, owners) for name in contact_names]
        for name in fastener_names:
            barrel_fasteners.append(
                _fastener_record(
                    case=case,
                    name=name,
                    station=station_name,
                    bolt=station["bolts"][name],
                    physical=physical,
                    owners=owners,
                    origin=origin,
                    kind="barrel_bolt",
                )
            )
        cells = []
        for name in contact_names:
            metadata = contact_metadata[name]
            expected = inventory["barrel_contacts"][name]
            _require(metadata.get("station") == station_name, f"{name}: contact station mismatch")
            _require(metadata.get("first") == first and metadata.get("second") == second, f"{name}: contact member ownership mismatch")
            _require(_same_vector(_vector(metadata.get("point_xyz_mm"), f"{name} metadata point"), expected["point"]), f"{name}: contact point differs from register")
            outward = _vector(
                station["contact"]["normal_outward_from_first_xyz"],
                f"{station_name} outward contact normal",
            )
            _require(
                _same_vector(
                    _vector(metadata.get("normal_xyz"), f"{name} metadata normal"),
                    _scale(outward, -1.0),
                ),
                f"{name}: contact normal differs from register",
            )
            _require(
                isinstance(metadata.get("tributary_area_mm2"), (int, float))
                and math.isclose(float(metadata["tributary_area_mm2"]), expected["area"], abs_tol=1.0e-6),
                f"{name}: contact area differs from register",
            )
            cells.append(
                _contact_record(
                    case=case,
                    name=name,
                    contact={**metadata, "area": expected["area"]},
                    physical=physical,
                    owners=owners,
                    bearings=bearings,
                )
            )
        fastener_resultants = _interface_resultants(first, fastener_physical, origin)
        contact_resultants = _interface_resultants(first, contact_physical, origin)
        total_resultants = _interface_resultants(first, fastener_physical + contact_physical, origin)
        station_rows.append(
            {
                "case": case,
                "station": station_name,
                "first_member": first,
                "second_member": second,
                "reference_origin_xyz_mm": origin,
                "barrel_fastener_names": fastener_names,
                "contact_cells": cells,
                "barrel_fastener_resultants": fastener_resultants,
                "contact_resultants": contact_resultants,
                "complete_interface_resultants": total_resultants,
                "contact_compression": {
                    "total_n": sum(cell["compression_n"] for cell in cells),
                    "active_cell_count": sum(cell["active"] for cell in cells),
                    "active_tributary_area_mm2": sum(cell["tributary_area_mm2"] for cell in cells if cell["active"]),
                    "peak_average_cell_pressure_n_per_mm2": max(cell["average_cell_pressure_n_per_mm2"] for cell in cells),
                },
                "same_case_force_moment_and_contact": True,
            }
        )

    retained_fasteners = []
    retained_joints = []
    for joint, fastener_names in inventory["retained_groups"].items():
        contact_names = sorted(retained_contact_groups[joint])
        retained_rows = [_physical_row(name, physical, owners) for name in fastener_names]
        contact_rows = [_physical_row(name, physical, owners) for name in contact_names]
        points = [_vector(row["point"], f"{joint} point") for row in retained_rows + contact_rows]
        origin = [sum(point[index] for point in points) / len(points) for index in range(3)]
        first, second = inventory["retained"][fastener_names[0]]["members"]
        _require(all(inventory["retained"][name]["members"] == [first, second] for name in fastener_names), f"{joint}: retained bolt member order differs")
        for name in fastener_names:
            retained_fasteners.append(
                _fastener_record(
                    case=case,
                    name=name,
                    station=joint,
                    bolt=inventory["retained"][name],
                    physical=physical,
                    owners=owners,
                    origin=origin,
                    kind="retained_frame_bolt",
                )
            )
        cells = []
        for name in contact_names:
            metadata = contact_metadata[name]
            _require({metadata.get("first"), metadata.get("second")} == {first, second}, f"{name}: retained contact ownership mismatch")
            area = metadata.get("tributary_area_mm2")
            _require(isinstance(area, (int, float)) and math.isfinite(area) and area > 0, f"{name}: retained contact area missing")
            cells.append(
                _contact_record(
                    case=case,
                    name=name,
                    contact={**metadata, "area": float(area)},
                    physical=physical,
                    owners=owners,
                    bearings=bearings,
                )
            )
        retained_joints.append(
            {
                "case": case,
                "joint": joint,
                "first_member": first,
                "second_member": second,
                "reference_origin_xyz_mm": origin,
                "retained_fastener_names": fastener_names,
                "contact_cells": cells,
                "fastener_resultants": _interface_resultants(first, retained_rows, origin),
                "contact_resultants": _interface_resultants(first, contact_rows, origin),
                "complete_interface_resultants": _interface_resultants(first, retained_rows + contact_rows, origin),
                "contact_compression": {
                    "total_n": sum(cell["compression_n"] for cell in cells),
                    "active_cell_count": sum(cell["active"] for cell in cells),
                    "active_tributary_area_mm2": sum(cell["tributary_area_mm2"] for cell in cells if cell["active"]),
                    "peak_average_cell_pressure_n_per_mm2": max(cell["average_cell_pressure_n_per_mm2"] for cell in cells),
                },
                "same_case_force_moment_and_contact": True,
            }
        )

    _require(len(station_rows) == EXPECTED_STATION_COUNT, f"{case}: station record count changed")
    _require(len(barrel_fasteners) == EXPECTED_BARREL_COUNT, f"{case}: barrel fastener count changed")
    _require(len(retained_fasteners) == EXPECTED_RETAINED_FASTENER_COUNT, f"{case}: retained fastener count changed")
    _require(len(retained_joints) == EXPECTED_RETAINED_JOINT_COUNT, f"{case}: retained joint count changed")
    return {
        "case": case,
        "scope": scope,
        "source": source or {},
        "equilibrium": equilibrium,
        "stations": station_rows,
        "barrel_fasteners": barrel_fasteners,
        "retained_fasteners": retained_fasteners,
        "retained_joints": retained_joints,
    }


def _authenticated_artifact(directory: Path, case: str) -> tuple[dict, dict, dict]:
    directory = Path(directory)
    report_path = directory / "report.json"
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    cycles = report.get("contact_cycles")
    _require(isinstance(cycles, list) and cycles, f"{case}: contact-cycle history missing")
    final_name = cycles[-1].get("directory")
    _require(isinstance(final_name, str) and Path(final_name).name == final_name, f"{case}: invalid final-cycle directory")
    final = directory / final_name
    manifest = report.get("artifact_sha256")
    _require(isinstance(manifest, dict), f"{case}: artifact manifest missing")

    def manifested(path: Path) -> bytes:
        relative = path.relative_to(directory).as_posix()
        content = path.read_bytes()
        _require(manifest.get(relative) == _digest_bytes(content), f"{case}: artifact digest mismatch: {relative}")
        return content

    record_path = final / "input.json"
    cycle_report_path = final / "report.json"
    record_bytes = manifested(record_path)
    cycle_report_bytes = manifested(cycle_report_path)
    record = json.loads(record_bytes)
    cycle_report = json.loads(cycle_report_bytes)
    for key in MECHANICS_KEYS:
        _require(report.get(key) == cycle_report.get(key), f"{case}: root report differs from authenticated final-cycle mechanics: {key}")

    scope_path = directory / "diagnostic-scope.json"
    scope_bytes = manifested(scope_path)
    _require(json.loads(scope_bytes) == report.get("owner_barrel_diagnostic_scope"), f"{case}: diagnostic scope sidecar mismatch")
    sources = report.get("source_sha256")
    _require(isinstance(sources, dict) and sources, f"{case}: producer source hashes missing")
    for name, expected in sources.items():
        snapshot = directory / "source_snapshots" / name
        content = manifested(snapshot)
        _require(_digest_bytes(content) == expected, f"{case}: producer snapshot digest mismatch: {name}")
    return report, record, {
        "case": case,
        "report_path": str(report_path),
        "report_sha256": _digest_bytes(report_bytes),
        "final_cycle": final_name,
        "final_input_sha256": _digest_bytes(record_bytes),
        "final_cycle_report_sha256": _digest_bytes(cycle_report_bytes),
        "diagnostic_scope_sha256": _digest_bytes(scope_bytes),
        "producer_source_sha256": sources,
    }


def build(case_directories: dict[str, Path], register: dict) -> dict:
    """Build one six-case demand ledger from authenticated result directories."""
    inventory = _register_inventory(register)
    _require(set(case_directories) == set(inventory["cases"]), "Exactly the six registered case directories are required")
    extracted = []
    for case in inventory["cases"]:
        report, record, source = _authenticated_artifact(Path(case_directories[case]), case)
        extracted.append(extract_case(report, record, register, case, source))
    source_sets = [row["source"]["producer_source_sha256"] for row in extracted]
    stiffness_sets = [row["scope"]["conditional_stiffnesses"] for row in extracted]
    _require(all(value == source_sets[0] for value in source_sets[1:]), "Six cases do not share one producer source identity")
    _require(all(value == stiffness_sets[0] for value in stiffness_sets[1:]), "Six cases do not share one conditional stiffness set")

    station_rows = [item for case in extracted for item in case["stations"]]
    barrel_rows = [item for case in extracted for item in case["barrel_fasteners"]]
    retained_fasteners = [item for case in extracted for item in case["retained_fasteners"]]
    retained_joints = [item for case in extracted for item in case["retained_joints"]]
    result = {
        "schema": SCHEMA,
        "candidate": register["candidate"],
        "solver_candidate": SOLVER_CANDIDATE,
        "status": "authenticated_conditional_demands_not_resistance",
        "case_order": list(inventory["cases"]),
        "conditional_stiffnesses": stiffness_sets[0],
        "counts": {
            "cases": EXPECTED_CASE_COUNT,
            "station_case_records": len(station_rows),
            "barrel_fastener_case_records": len(barrel_rows),
            "retained_fastener_case_records": len(retained_fasteners),
            "retained_joint_case_records": len(retained_joints),
            "barrel_contact_cells": EXPECTED_BARREL_CONTACT_COUNT,
            "retained_contact_cells": EXPECTED_RETAINED_CONTACT_COUNT,
            "combined_contact_cells": EXPECTED_COMBINED_CONTACT_COUNT,
            "barrel_contact_cell_case_records": sum(
                len(row["contact_cells"]) for row in station_rows
            ),
            "retained_contact_cell_case_records": sum(
                len(row["contact_cells"]) for row in retained_joints
            ),
            "combined_contact_cell_case_records": sum(
                len(row["contact_cells"])
                for row in (*station_rows, *retained_joints)
            ),
        },
        "source_reports": [row["source"] for row in extracted],
        "case_equilibrium": [row["equilibrium"] for row in extracted],
        "station_case_demands": station_rows,
        "barrel_fastener_case_demands": barrel_rows,
        "retained_fastener_case_demands": retained_fasteners,
        "retained_joint_case_demands": retained_joints,
        "aggregation_policy": {
            "simultaneous_case_records_only": True,
            "componentwise_extrema_generated": False,
            "mixed_case_force_moment_contact_prohibited": True,
        },
        "qualified_for_design": False,
        "joint_resistance_assessed": False,
        "structural_adequacy_claimed": False,
        "drilling_released": False,
        "fabrication_released": False,
        "diy_released": False,
    }
    validate_output(result)
    return result


def validate_output(result: dict) -> None:
    """Fail closed on cardinality, same-case coverage, or release drift."""
    _require(result.get("schema") == SCHEMA, "Unexpected signed-demand schema")
    cases = result.get("case_order")
    _require(isinstance(cases, list) and len(cases) == EXPECTED_CASE_COUNT and len(set(cases)) == EXPECTED_CASE_COUNT, "Output requires six distinct cases")
    expected_counts = {
        "cases": EXPECTED_CASE_COUNT,
        "station_case_records": EXPECTED_STATION_COUNT * EXPECTED_CASE_COUNT,
        "barrel_fastener_case_records": EXPECTED_BARREL_COUNT * EXPECTED_CASE_COUNT,
        "retained_fastener_case_records": EXPECTED_RETAINED_FASTENER_COUNT * EXPECTED_CASE_COUNT,
        "retained_joint_case_records": EXPECTED_RETAINED_JOINT_COUNT * EXPECTED_CASE_COUNT,
        "barrel_contact_cells": EXPECTED_BARREL_CONTACT_COUNT,
        "retained_contact_cells": EXPECTED_RETAINED_CONTACT_COUNT,
        "combined_contact_cells": EXPECTED_COMBINED_CONTACT_COUNT,
        "barrel_contact_cell_case_records": EXPECTED_BARREL_CONTACT_COUNT
        * EXPECTED_CASE_COUNT,
        "retained_contact_cell_case_records": EXPECTED_RETAINED_CONTACT_COUNT
        * EXPECTED_CASE_COUNT,
        "combined_contact_cell_case_records": EXPECTED_COMBINED_CONTACT_COUNT
        * EXPECTED_CASE_COUNT,
    }
    _require(result.get("counts") == expected_counts, "Signed-demand output counts changed")
    for collection in ("source_reports", "case_equilibrium"):
        rows = result.get(collection)
        _require(
            isinstance(rows, list)
            and len(rows) == EXPECTED_CASE_COUNT
            and {row.get("case") for row in rows} == set(cases),
            f"{collection}: six-case coverage changed",
        )
    collections = (
        ("station_case_demands", "station", EXPECTED_STATION_COUNT),
        ("barrel_fastener_case_demands", "name", EXPECTED_BARREL_COUNT),
        ("retained_fastener_case_demands", "name", EXPECTED_RETAINED_FASTENER_COUNT),
        ("retained_joint_case_demands", "joint", EXPECTED_RETAINED_JOINT_COUNT),
    )
    for collection, identity, per_case in collections:
        rows = result.get(collection)
        _require(isinstance(rows, list) and len(rows) == per_case * EXPECTED_CASE_COUNT, f"{collection}: wrong row count")
        pairs = {(row.get("case"), row.get(identity)) for row in rows}
        identities = {row.get(identity) for row in rows}
        _require(None not in identities and len(identities) == per_case, f"{collection}: identity coverage changed")
        _require(pairs == {(case, name) for case in cases for name in identities}, f"{collection}: case coverage is incomplete or duplicated")
        if collection.endswith("fastener_case_demands"):
            _require(all(row.get("same_case_only") is True for row in rows), f"{collection}: same-case marker changed")
        else:
            _require(
                all(
                    row.get("same_case_force_moment_and_contact") is True
                    and all(cell.get("case") == row.get("case") for cell in row.get("contact_cells", ()))
                    for row in rows
                ),
                f"{collection}: mixed-case force, moment, or contact data",
            )
    policy = result.get("aggregation_policy", {})
    _require(
        policy.get("simultaneous_case_records_only") is True
        and policy.get("componentwise_extrema_generated") is False
        and policy.get("mixed_case_force_moment_contact_prohibited") is True,
        "Mixed-case extrema policy changed",
    )
    for key in (
        "qualified_for_design",
        "joint_resistance_assessed",
        "structural_adequacy_claimed",
        "drilling_released",
        "fabrication_released",
        "diy_released",
    ):
        _require(result.get(key) is False, f"Signed-demand extractor cannot set {key}")


def render(result: dict) -> str:
    validate_output(result)
    return json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "case_directory",
        nargs="+",
        metavar="CASE=DIR",
        help="One authenticated native result directory for each registered case",
    )
    args = parser.parse_args(argv)
    directories = {}
    for value in args.case_directory:
        case, separator, directory = value.partition("=")
        if not separator or not case or not directory or case in directories:
            parser.error(f"Invalid or duplicate CASE=DIR argument: {value}")
        directories[case] = Path(directory)
    register = json.loads(args.register.read_text())
    result = build(directories, register)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(result))


if __name__ == "__main__":
    main()
