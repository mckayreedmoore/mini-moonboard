"""Synthetic source and joint-balance checks; no native solve."""

import hashlib
import json

import pytest

from scripts.bolted_center_candidate_extract import CANDIDATE, GEOMETRY, extract_files


def _row(first, second, point, force_z):
    return {
        "first": first,
        "second": second,
        "point": point,
        "force_on_first_xyz_n": [0, 0, force_z],
        "force_on_second_xyz_n": [0, 0, -force_z],
        "force_rounding_radius_xyz_n": [0.0001, 0.0001, 0.0001],
    }


def _fixture(tmp_path):
    upper, lower = "trial_upper", "trial_lower"
    spring_n_per_mm = 10_000.0
    spring = {"axial_n_per_mm": spring_n_per_mm, "lateral_n_per_mm": spring_n_per_mm}
    physical = {}
    angles = []
    stations = []
    for name, wood, sign, wood_z, steel_z in (
        (upper, "base_principal_center_left", 1, (2, 3), 1),
        (lower, "base_post_center_left", -1, (-2, -3), -1),
    ):
        vertical_points = [[0, 0, z] for z in wood_z]
        header_points = [[x, 0, steel_z] for x in (-1, 1)]
        contact_points = [[x, y, steel_z] for x in (-1, 1) for y in (-1, 1)]
        angles.append(
            {
                "name": name,
                "wood_member": wood,
                "vertical_points": vertical_points,
                "header_points": header_points,
                "contact_points": contact_points,
                "contact_inward_xyz": [0, 0, -sign],
            }
        )
        stations.append(
            {
                "name": f"old_{name}",
                "members": [wood, "base_header"],
                "origin": [0, 0, steel_z],
            }
        )
        for i, point in enumerate(vertical_points):
            physical[f"{name}_wood_{i}"] = _row(wood, name, point, 4.5 * sign)
        for i, point in enumerate(contact_points):
            physical[f"{name}_flange_contact_{i}"] = _row(
                "base_header", name, point, -sign
            )
        physical[f"{name}_direct_contact"] = _row(
            wood, "base_header", [0, 0, steel_z], 0
        )

    bolts = []
    springs = []
    for i, x in enumerate((-1, 1)):
        name = f"trial_bolt_{i}"
        top, bottom = [x, 0, 1], [x, 0, -1]
        bore_upper, bore_lower = [x, 0, 0.5], [x, 0, -0.5]
        bolts.append(
            {
                "name": name,
                "top_point": top,
                "bottom_point": bottom,
                "wood_upper_point": bore_upper,
                "wood_lower_point": bore_lower,
            }
        )
        physical[f"{name}_upper_steel"] = _row(upper, name, top, 2.5)
        physical[f"{name}_lower_steel"] = _row(lower, name, bottom, -2.5)
        for side, point in (("upper", bore_upper), ("lower", bore_lower)):
            branch = f"{name}_header_bearing_{side}"
            physical[branch] = _row("base_header", name, point, 0)
            springs.extend({"name": branch, "dof": dof} for dof in (1, 2))

    widths = {}
    for part in ("main_lower", "main_upper", "kicker"):
        for side, span in (
            ("left", [-1219.2, -1.5875]),
            ("right", [-1.5875, 1216.025]),
        ):
            widths[f"{part}_{side}"] = {"actual_x_mm": span, "mesh_x_mm": span}
    record = {
        "candidate": CANDIDATE,
        "hold": "A1",
        "pounds": 250.0,
        "equipment_kg": 25.0,
        "force_xyz_n": [0, 300, -2 * 250 * 0.45359237 * 9.80665],
        "diagnostic_only": True,
        "acceptance": False,
        "actual_joint_demands_qualified": False,
        "bolted_joint_demands": False,
        "qualified_for_design": False,
        "kerf_panel_bounds": widths,
        "springs": springs,
        "angle_stations": stations,
        "connection_ownership": {
            name: {key: row[key] for key in ("first", "second", "point")}
            for name, row in physical.items()
        },
        "diagnostic_center_joint": {
            "replaced_clips": ["old_principal", "old_post"],
            "angles": angles,
            "shared_header_bolts": bolts,
            "vertical_spring": spring,
            "steel_bolt_spring": spring,
            "wood_bearing_lateral_n_per_mm": spring_n_per_mm,
            "flange_contact_n_per_mm": spring_n_per_mm,
        },
    }
    scope = {
        "case": "a1-rear",
        "source_geometry": GEOMETRY,
        "spring_n_per_mm": spring_n_per_mm,
        "numerically_converged": True,
        "qualified_bolted_joint_demands": False,
        "resistance_checked": False,
        "acceptance": False,
        "drilling_released": False,
    }
    report = {
        "candidate": CANDIDATE,
        "numerically_accepted": True,
        "contact_active_set_converged": True,
        "global_equilibrium_passed": True,
        "member_equilibrium_passed": True,
        "mpc_check_passed": True,
        "member_equilibrium": {"base_header": {"passed": True}},
        "contact_cycles": [{"directory": "cycle-00", "contact_passed": True}],
        "diagnostic_scope": scope,
        "parameters": {"hold": "A1", "pounds": 250.0, "equipment_kg": 25.0,
                       "force_xyz_n": [0, 300, -2 * 250 * 0.45359237 * 9.80665]},
        "physical_connection_forces": physical,
    }
    root = tmp_path
    (root / "cycle-00").mkdir()
    (root / "cycle-00" / "input.json").write_text(json.dumps(record))
    (root / "diagnostic-scope.json").write_text(json.dumps(scope))
    sources = (
        "fea/current_response_run.py",
        "fea/current_response_model.py",
        "scripts/bolted_center_native_diagnostic.py",
        "scripts/bolted_center_joint_model.py",
        "scripts/clear_space_batch.py",
        "docs/floor-flush-construction-kerf-right/connection-axes.csv",
    )
    report["source_sha256"] = {}
    for name in sources:
        path = root / "source_snapshots" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            'CASES = {"a1-rear": ("A1", (0., 300.))}'
            if name == "scripts/clear_space_batch.py" else name
        )
        report["source_sha256"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    report["artifact_sha256"] = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }
    report_path = root / "report.json"
    report_path.write_text(json.dumps(report))
    return report_path


def test_signed_simultaneous_actions(tmp_path):
    result = extract_files(_fixture(tmp_path))
    assert result["classification"] == "provisional_native_AB205_diagnostic"
    assert len(result["angles"]["trial_upper"]["branch_names"]["header_contact"]) == 4
    assert result["angles"]["trial_upper"]["on_angle_from_header_contact"][
        "force_xyz_n"
    ] == [0, 0, 4]
    bolt = result["shared_bolts"]["trial_bolt_0"]
    assert len(bolt["branches"]["middle_wood"]["connection_names"]) == 2
    assert bolt["branches"]["middle_wood"]["on_bolt"]["force_xyz_n"] == [0, 0, 0]
    assert bolt["branches"]["upper_steel"]["on_bolt"]["force_xyz_n"] == [0, 0, -2.5]
    assert bolt["equilibrium"]["passed"]
    assert result["interfaces"]["principal_header"]["direct_connection_names"] == [
        "trial_upper_direct_contact"
    ]
    assert result["interfaces"]["post_header"]["direct_connection_names"] == [
        "trial_lower_direct_contact"
    ]


@pytest.mark.parametrize(
    "artifact",
    [
        "cycle-00/input.json",
        "diagnostic-scope.json",
        "source_snapshots/scripts/bolted_center_joint_model.py",
        "source_snapshots/docs/floor-flush-construction-kerf-right/connection-axes.csv",
    ],
)
def test_tampered_artifact_rejected(tmp_path, artifact):
    report = _fixture(tmp_path)
    (tmp_path / artifact).write_text("tampered")
    with pytest.raises(ValueError, match="digest mismatch"):
        extract_files(report)


@pytest.mark.parametrize("artifact", ["cycle-00/input.json", "diagnostic-scope.json"])
def test_required_artifact_cannot_be_omitted_from_manifest(tmp_path, artifact):
    path = _fixture(tmp_path)
    report = json.loads(path.read_text())
    report["artifact_sha256"].pop(artifact)
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="required artifact"):
        extract_files(path)


def test_final_cycle_cannot_escape_report_directory(tmp_path):
    path = _fixture(tmp_path)
    report = json.loads(path.read_text())
    report["contact_cycles"][-1]["directory"] = "../../outside"
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="outside report directory|final cycle"):
        extract_files(path)


def test_scope_sidecar_cannot_be_symlinked(tmp_path):
    path = _fixture(tmp_path)
    scope = tmp_path / "diagnostic-scope.json"
    scope.rename(tmp_path / "scope-backing.json")
    scope.symlink_to("scope-backing.json")
    with pytest.raises(ValueError, match="scope sidecar"):
        extract_files(path)


@pytest.mark.parametrize("changed_force", [-1000.0, 0.0])
def test_consistently_changed_vertical_load_is_rejected(tmp_path, changed_force):
    path = _fixture(tmp_path)
    record_path = tmp_path / "cycle-00/input.json"
    record = json.loads(record_path.read_text())
    report = json.loads(path.read_text())
    record["force_xyz_n"][2] = changed_force
    report["parameters"]["force_xyz_n"][2] = changed_force
    record_path.write_text(json.dumps(record))
    report["artifact_sha256"]["cycle-00/input.json"] = hashlib.sha256(
        record_path.read_bytes()
    ).hexdigest()
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="Candidate or case identity mismatch"):
        extract_files(path)


def test_authenticated_case_definition_controls_full_load_vector(tmp_path):
    path = _fixture(tmp_path)
    source_path = tmp_path / "source_snapshots/scripts/clear_space_batch.py"
    source_path.write_text('CASES = {"a1-rear": ("A1", (0., 301.))}')
    report = json.loads(path.read_text())
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    report["source_sha256"]["scripts/clear_space_batch.py"] = digest
    report["artifact_sha256"]["source_snapshots/scripts/clear_space_batch.py"] = digest
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="Candidate or case identity mismatch"):
        extract_files(path)


def test_consistently_changed_equipment_mass_is_rejected(tmp_path):
    path = _fixture(tmp_path)
    record_path = tmp_path / "cycle-00/input.json"
    record = json.loads(record_path.read_text())
    report = json.loads(path.read_text())
    record["equipment_kg"] = 0.0
    report["parameters"]["equipment_kg"] = 0.0
    record_path.write_text(json.dumps(record))
    report["artifact_sha256"]["cycle-00/input.json"] = hashlib.sha256(
        record_path.read_bytes()
    ).hexdigest()
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="Candidate or case identity mismatch"):
        extract_files(path)


def test_unconverged_report_rejected(tmp_path):
    path = _fixture(tmp_path)
    report = json.loads(path.read_text())
    report["contact_active_set_converged"] = False
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="acceptance failed"):
        extract_files(path)


def test_unequal_side_actions_rejected(tmp_path):
    path = _fixture(tmp_path)
    report = json.loads(path.read_text())
    report["physical_connection_forces"]["trial_bolt_0_upper_steel"][
        "force_on_second_xyz_n"
    ][2] = -6
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="action-reaction mismatch"):
        extract_files(path)


def test_unbalanced_joint_rejected(tmp_path):
    path = _fixture(tmp_path)
    report = json.loads(path.read_text())
    row = report["physical_connection_forces"]["trial_bolt_0_upper_steel"]
    row["force_on_first_xyz_n"][2] += 1
    row["force_on_second_xyz_n"][2] -= 1
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="Joint body equilibrium failed"):
        extract_files(path)


def test_wrong_bore_dof_rejected(tmp_path):
    path = _fixture(tmp_path)
    record_path = tmp_path / "cycle-00/input.json"
    record = json.loads(record_path.read_text())
    record["springs"][0]["dof"] = 3
    record_path.write_text(json.dumps(record))
    report = json.loads(path.read_text())
    report["artifact_sha256"]["cycle-00/input.json"] = hashlib.sha256(
        record_path.read_bytes()
    ).hexdigest()
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="lateral-only"):
        extract_files(path)


def test_scope_spring_mismatch_rejected(tmp_path):
    path = _fixture(tmp_path)
    scope_path = tmp_path / "diagnostic-scope.json"
    scope = json.loads(scope_path.read_text())
    scope["spring_n_per_mm"] = 20_000.0
    scope_path.write_text(json.dumps(scope))
    report = json.loads(path.read_text())
    report["diagnostic_scope"] = scope
    report["artifact_sha256"]["diagnostic-scope.json"] = hashlib.sha256(
        scope_path.read_bytes()
    ).hexdigest()
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="Joint slip scope"):
        extract_files(path)
