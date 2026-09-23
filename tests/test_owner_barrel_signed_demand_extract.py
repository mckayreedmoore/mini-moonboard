"""Signed-demand extraction is complete, authenticated, and never enveloped."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import owner_barrel_signed_demand_extract as demand

CASES = tuple(f"case-{index}" for index in range(6))


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _register():
    stations = {}
    barrel_count = 0
    for index in range(24):
        name = f"station-{index:02d}"
        members = [f"station-first-{index:02d}", f"station-second-{index:02d}"]
        bolt_count = 2 if index < 22 else 1
        bolts = {}
        for row in range(bolt_count):
            bolt = f"barrel-{barrel_count:02d}"
            barrel_count += 1
            bolts[bolt] = {
                "name": bolt,
                "members": members,
                "entry_member": members[0],
                "receiving_member": members[1],
                "direction_xyz": [1.0, 0.0, 0.0],
            }
        contact_count = 6 if index < 12 else 5
        stations[name] = {
            "identity": name,
            "timber_members": members,
            "bolts": bolts,
            "contact": {
                "gross_contact_centroid_xyz_mm": [float(index), 0.0, 0.0],
                "normal_outward_from_first_xyz": [0.0, 0.0, -1.0],
                "contact_cells": [
                    {
                        "name": f"{name}-contact-{row:02d}",
                        "point_xyz_mm": [float(index), float(row + 1), 0.0],
                        "tributary_area_mm2": 10.0,
                    }
                    for row in range(contact_count)
                ],
            },
        }
    assert barrel_count == 46
    retained = {}
    for joint in range(6):
        members = [f"retained-first-{joint}", f"retained-second-{joint}"]
        for row in range(2):
            name = f"retained-{joint}-{row}"
            retained[name] = {
                "name": name,
                "members": members,
                "direction_xyz": [1.0, 0.0, 0.0],
            }
    loads = {
        case: {
            "hold": f"H{index}",
            "requested_climber_weight_lbf": 250.0,
            "horizontal_force_xy_n": [float(index), float(-index)],
            "applied_force_xyz_n": [float(index), float(-index), -100.0],
        }
        for index, case in enumerate(CASES)
    }
    return {
        "candidate": "compact-floor-flush-bolted-development",
        "load_case_order": list(CASES),
        "load_cases": loads,
        "counts": {
            "stations": 24,
            "barrel_pairs": 46,
            "retained_frame_bolts": 12,
        },
        "contact_summary": {"contact_cell_count": 132},
        "stations": stations,
        "fixed_features": {"retained_frame_bolts": retained},
    }


def _force_row(owner, force):
    row = {
        **owner,
        "force_on_first_xyz_n": list(force),
        "force_on_second_xyz_n": [-value for value in force],
        "force_rounding_radius_xyz_n": [0.0, 0.0, 0.0],
    }
    if "axis" in owner:
        axial = sum(a * b for a, b in zip(force, owner["axis"], strict=True))
        transverse = [f - axial * a for f, a in zip(force, owner["axis"], strict=True)]
        row["axial_along_installation_direction_n"] = axial
        row["transverse_shear_n"] = sum(value * value for value in transverse) ** 0.5
    return row


def _case_data(register, case):
    case_index = CASES.index(case)
    owners = {}
    contacts = []
    physical = {}
    bearings = []
    for station_index, (station_name, station) in enumerate(register["stations"].items()):
        first, second = station["timber_members"]
        for row_index, name in enumerate(station["bolts"]):
            owner = {
                "first": first,
                "second": second,
                "point": [float(station_index), float(row_index), 0.0],
                "axis": [1.0, 0.0, 0.0],
            }
            owners[name] = owner
            # Alternating sign proves signed axial force survives extraction.
            axial = float((case_index + 1) * (station_index + 1))
            if case_index % 2:
                axial = -axial
            physical[name] = _force_row(owner, [axial, float(row_index + 1), 0.0])
        for cell_index, cell in enumerate(station["contact"]["contact_cells"]):
            contact = {
                "name": cell["name"],
                "station": station_name,
                "first": first,
                "second": second,
                "point_xyz_mm": cell["point_xyz_mm"],
                "normal_xyz": [0.0, 0.0, 1.0],
                "tributary_area_mm2": cell["tributary_area_mm2"],
            }
            contacts.append(contact)
            owner = {
                "first": first,
                "second": second,
                "point": cell["point_xyz_mm"],
                "scalar_normal": [0.0, 0.0, 1.0],
            }
            owners[cell["name"]] = owner
            compression = float(case_index + station_index + cell_index + 1)
            physical[cell["name"]] = _force_row(
                owner, [0.0, 0.0, compression]
            )
            bearings.append(
                {
                    "name": cell["name"],
                    "opening_mm": 0.0,
                    "compression_force_n": compression,
                    "active": True,
                }
            )

    retained = register["fixed_features"]["retained_frame_bolts"]
    for joint in range(6):
        first, second = retained[f"retained-{joint}-0"]["members"]
        for row in range(2):
            name = f"retained-{joint}-{row}"
            owner = {
                "first": first,
                "second": second,
                "point": [100.0 + joint, float(row), 0.0],
                "axis": [1.0, 0.0, 0.0],
            }
            owners[name] = owner
            physical[name] = _force_row(owner, [float(case_index + 1), float(row), 0.0])
        for row in range(12):
            name = f"retained-{joint}-contact-{row:02d}"
            point = [100.0 + joint, float(row), 1.0]
            contact = {
                "name": name,
                "first": first,
                "second": second,
                "point_xyz_mm": point,
                "normal_xyz": [0.0, 0.0, 1.0],
                "tributary_area_mm2": 5.0,
            }
            contacts.append(contact)
            owner = {
                "first": first,
                "second": second,
                "point": point,
                "scalar_normal": [0.0, 0.0, 1.0],
            }
            owners[name] = owner
            compression = float(case_index + row + 1)
            physical[name] = _force_row(owner, [0.0, 0.0, compression])
            bearings.append(
                {
                    "name": name,
                    "opening_mm": 0.0,
                    "compression_force_n": compression,
                    "active": True,
                }
            )

    scope = {
        "case": case,
        "candidate": demand.SOLVER_CANDIDATE,
        "case_load": {
            "hold": register["load_cases"][case]["hold"],
            "horizontal_force_xy_n": register["load_cases"][case]["horizontal_force_xy_n"],
            "applied_force_xyz_n": register["load_cases"][case]["applied_force_xyz_n"],
            "pounds": 250.0,
        },
        "conditional_stiffnesses": {
            "barrel_axial_n_per_mm": 1000.0,
            "barrel_lateral_n_per_mm": 500.0,
            "contact_n_per_mm3": 100.0,
        },
        "diagnostic_only": True,
        "conditional_only": True,
        "joint_resistance_qualified": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "diy_released": False,
    }
    report = {
        "candidate": demand.SOLVER_CANDIDATE,
        "owner_barrel_diagnostic_scope": scope,
        "physical_connection_forces": physical,
        "bearings": bearings,
        "force_residual_n": [0.01, -0.02, 0.0],
        "moment_residual_nmm": [0.1, 0.0, -0.1],
        "global_equilibrium_passed": True,
        "member_equilibrium": {
            "fixture-member": {
                "maximum_force_residual_n": 0.01,
                "maximum_moment_residual_nmm": 0.1,
                "passed": True,
            }
        },
        "member_equilibrium_passed": True,
        "member_equilibrium_criterion": "fixture equilibrium criterion",
        "mpc_check_passed": True,
        "mpc_printed_precision_audit": {"passed": True},
        "closed_bearing_assumption_passed": True,
        "contact_active_set_converged": True,
        "axial_tension_active_set_converged": True,
        "radial_clearance_active_set_converged": True,
        "axial_tension": [],
        "axial_tension_assumption_passed": True,
        "radial_clearance": [],
        "radial_clearance_assumption_passed": True,
        "numerically_accepted": True,
        "native_numerically_accepted": True,
        "owner_barrel_wrapper_accepted": True,
        "retry_checkpoint_eligible": False,
        "qualified_for_design": False,
        "acceptance": False,
        "joint_resistance_qualified": False,
        "structural_released": False,
        "drilling_released": False,
        "fabrication_released": False,
        "diy_released": False,
    }
    record = {
        "candidate": demand.SOLVER_CANDIDATE,
        "hold": register["load_cases"][case]["hold"],
        "force_xyz_n": register["load_cases"][case]["applied_force_xyz_n"],
        "connection_ownership": owners,
        "member_contacts": contacts,
    }
    return report, record


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")


def _artifact(tmp_path, register, case):
    directory = tmp_path / case
    cycle = directory / "cycle-00"
    report, record = _case_data(register, case)
    cycle_report = {key: copy.deepcopy(report[key]) for key in demand.MECHANICS_KEYS}
    _write_json(cycle / "input.json", record)
    _write_json(cycle / "report.json", cycle_report)
    _write_json(directory / "diagnostic-scope.json", report["owner_barrel_diagnostic_scope"])
    source = directory / "source_snapshots" / "fixture-source.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("FIXTURE = True\n")
    report["contact_cycles"] = [{"directory": "cycle-00", "contact_passed": True}]
    report["source_sha256"] = {"fixture-source.py": _sha(source.read_bytes())}
    paths = (cycle / "input.json", cycle / "report.json", directory / "diagnostic-scope.json", source)
    report["artifact_sha256"] = {
        path.relative_to(directory).as_posix(): _sha(path.read_bytes()) for path in paths
    }
    _write_json(directory / "report.json", report)
    return directory


@pytest.fixture()
def suite(tmp_path):
    register = _register()
    directories = {case: _artifact(tmp_path, register, case) for case in CASES}
    return register, directories


def test_authenticated_suite_has_exact_same_case_demand_coverage(suite):
    register, directories = suite
    result = demand.build(directories, register)

    assert result["counts"] == {
        "cases": 6,
        "station_case_records": 144,
        "barrel_fastener_case_records": 276,
        "retained_fastener_case_records": 72,
        "retained_joint_case_records": 36,
        "barrel_contact_cells": 132,
        "retained_contact_cells": 72,
        "combined_contact_cells": 204,
        "barrel_contact_cell_case_records": 792,
        "retained_contact_cell_case_records": 432,
        "combined_contact_cell_case_records": 1224,
    }
    assert len(result["case_equilibrium"]) == 6
    assert all(row["global"]["passed"] for row in result["case_equilibrium"])
    assert all(row["members"]["records"] for row in result["case_equilibrium"])
    assert result["aggregation_policy"] == {
        "simultaneous_case_records_only": True,
        "componentwise_extrema_generated": False,
        "mixed_case_force_moment_contact_prohibited": True,
    }
    for row in result["station_case_demands"]:
        assert row["same_case_force_moment_and_contact"] is True
        assert {cell["case"] for cell in row["contact_cells"]} == {row["case"]}
        assert row["complete_interface_resultants"]["action_reaction_residual"]["passed"]
    signed = {
        row["case"]: row["axial_along_installation_direction_n"]
        for row in result["barrel_fastener_case_demands"]
        if row["name"] == "barrel-00"
    }
    assert signed == {
        "case-0": 1.0,
        "case-1": -2.0,
        "case-2": 3.0,
        "case-3": -4.0,
        "case-4": 5.0,
        "case-5": -6.0,
    }
    assert not any("envelope" in key or "extrema" in key for key in result)
    assert all(result[key] is False for key in (
        "qualified_for_design",
        "joint_resistance_assessed",
        "structural_adequacy_claimed",
        "drilling_released",
        "fabrication_released",
        "diy_released",
    ))


def test_schema_freezes_counts_policy_and_release_boundary():
    path = Path(__file__).resolve().parents[1] / "docs/owner-barrel-signed-demands.schema.json"
    schema = json.loads(path.read_text())
    properties = schema["properties"]
    assert properties["schema"]["const"] == demand.SCHEMA
    assert properties["station_case_demands"]["minItems"] == 144
    assert properties["barrel_fastener_case_demands"]["maxItems"] == 276
    assert properties["retained_fastener_case_demands"]["minItems"] == 72
    assert properties["retained_joint_case_demands"]["maxItems"] == 36
    assert properties["counts"]["properties"]["barrel_contact_cells"]["const"] == 132
    assert properties["counts"]["properties"]["combined_contact_cells"]["const"] == 204
    assert properties["counts"]["properties"]["combined_contact_cell_case_records"]["const"] == 1224
    assert properties["aggregation_policy"]["properties"]["componentwise_extrema_generated"]["const"] is False
    assert properties["structural_adequacy_claimed"]["const"] is False
    assert properties["diy_released"]["const"] is False


def test_missing_case_or_wrong_output_cardinality_fails_closed(suite):
    register, directories = suite
    incomplete = dict(directories)
    incomplete.pop(CASES[-1])
    with pytest.raises(ValueError, match="Exactly the six"):
        demand.build(incomplete, register)

    result = demand.build(directories, register)
    result["station_case_demands"].pop()
    with pytest.raises(ValueError, match="station_case_demands"):
        demand.validate_output(result)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda report, record: report.update(global_equilibrium_passed=False), "equilibrium gate failed"),
        (
            lambda report, record: report["physical_connection_forces"].pop("barrel-00"),
            "physical force or ownership missing",
        ),
        (
            lambda report, record: report["physical_connection_forces"]["station-00-contact-00"].update(
                force_on_first_xyz_n=[0.0, 0.0, -1.0],
                force_on_second_xyz_n=[0.0, 0.0, 1.0],
            ),
            "contact carries tension",
        ),
    ],
)
def test_failed_equilibrium_missing_fastener_or_contact_tension_stops_extraction(mutation, message):
    register = _register()
    report, record = _case_data(register, CASES[0])
    mutation(report, record)
    with pytest.raises(ValueError, match=message):
        demand.extract_case(report, record, register, CASES[0])


def test_manifest_tamper_and_unauthenticated_root_mechanics_fail_closed(suite):
    register, directories = suite
    tampered = directories[CASES[0]] / "cycle-00/input.json"
    tampered.write_text(tampered.read_text() + " ")
    with pytest.raises(ValueError, match="artifact digest mismatch"):
        demand.build(directories, register)

    # Rebuild suite, then change root mechanics without changing authenticated cycle.
    tmp_root = directories[CASES[1]].parent / "second"
    rebuilt = {case: _artifact(tmp_root, register, case) for case in CASES}
    root_report_path = rebuilt[CASES[0]] / "report.json"
    root_report = json.loads(root_report_path.read_text())
    root_report["force_residual_n"] = [9.0, 0.0, 0.0]
    _write_json(root_report_path, root_report)
    with pytest.raises(ValueError, match="authenticated final-cycle mechanics"):
        demand.build(rebuilt, register)


def test_different_conditional_stiffnesses_cannot_be_combined(suite):
    register, directories = suite
    changed = directories[CASES[-1]]
    scope_path = changed / "diagnostic-scope.json"
    root_path = changed / "report.json"
    scope = json.loads(scope_path.read_text())
    scope["conditional_stiffnesses"]["contact_n_per_mm3"] = 101.0
    _write_json(scope_path, scope)
    root = json.loads(root_path.read_text())
    root["owner_barrel_diagnostic_scope"] = scope
    root["artifact_sha256"]["diagnostic-scope.json"] = _sha(scope_path.read_bytes())
    _write_json(root_path, root)
    with pytest.raises(ValueError, match="one conditional stiffness"):
        demand.build(directories, register)
