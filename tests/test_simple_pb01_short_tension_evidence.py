"""Source binding and claim boundaries for PB01 short tension evidence."""

import hashlib
import json
import zipfile

import pytest

from scripts.simple_pb01_short_tension_evidence import build, compare, verify


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _fixture(root):
    root.mkdir()
    files = {
        "diagnostic-scope.json": json.dumps(
            {
                "case": "a12-left",
                "diagnostic_only": True,
                "pb01_pose_variant": "quarter_short",
                "pb01_axial_law": "tension_only_no_preload",
                "pb01_face_contact_law": "compression_only",
                "qualified_for_design": False,
                "drilling_released": False,
            }
        ).encode(),
        "source_snapshots/scripts/producer.py": b"producer\n",
    }
    final = {
        "axial_tension": [
            {
                "name": "pb01_upright_u1",
                "active": False,
                "extension_mm": -0.01,
                "tension_force_n": 0.0,
                "tension_only_assumption_satisfied": True,
            },
            {
                "name": "pb01_rail_r1",
                "active": True,
                "extension_mm": 0.02,
                "tension_force_n": 20.0,
                "tension_only_assumption_satisfied": True,
            },
            {
                "name": "pb01_upright_u2",
                "active": False,
                "extension_mm": -0.02,
                "tension_force_n": 0.0,
                "tension_only_assumption_satisfied": True,
            },
            {
                "name": "pb01_rail_r2",
                "active": False,
                "extension_mm": -0.03,
                "tension_force_n": 0.0,
                "tension_only_assumption_satisfied": True,
            },
        ],
        "bearings": [
            {
                "name": "pb01_rail_compression_0_0",
                "active": True,
                "opening_mm": -0.03,
                "compression_force_n": 7.5,
                "compression_only_assumption_satisfied": True,
            },
        ]
        + [
            {
                "name": f"pb01_{family}_compression_{i}_{j}",
                "active": False,
                "opening_mm": 0.01,
                "compression_force_n": 0.0,
                "compression_only_assumption_satisfied": True,
            }
            for family in ("upright", "rail")
            for i in range(2)
            for j in range(2)
            if (family, i, j) != ("rail", 0, 0)
        ],
        "axial_tension_assumption_passed": True,
        "closed_bearing_assumption_passed": True,
    }
    for name in ("input.json", "frame.inp", "frame.dat", "frame.log", "frame.sta"):
        files[f"cycle-13/{name}"] = name.encode()
    files["cycle-13/input.json"] = b'{"hold": "A12"}'
    files["cycle-13/report.json"] = json.dumps(final).encode()
    report = {
        **final,
        "diagnostic_scope": json.loads(files["diagnostic-scope.json"]),
        "pb01_axial_law": "tension_only_no_preload",
        "contact_cycles": [
            {
                "directory": "cycle-13",
                "contact_passed": True,
                "axial_tension_passed": True,
                "axial_tension_active_names": ["pb01_rail_r1"],
            }
        ],
        "numerically_accepted": True,
        "contact_active_set_converged": True,
        "axial_tension_active_set_converged": True,
        "source_sha256": {
            "scripts/producer.py": _sha(files["source_snapshots/scripts/producer.py"])
        },
        "artifact_sha256": {name: _sha(data) for name, data in files.items()},
        "solver_image": "sha256:fixture",
    }
    files["report.json"] = json.dumps(report).encode()
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return root


def test_build_and_verify_signed_summary(tmp_path):
    source = _fixture(tmp_path / "run")
    archive = tmp_path / "pack.zip"
    build(source, archive)
    summary = verify(archive)
    axial = {row["name"]: row for row in summary["axial_tension"]}
    assert axial["pb01_rail_r1"]["extension_mm"] == 0.02
    assert axial["pb01_upright_u1"]["extension_mm"] == -0.01
    assert summary["face_contact"][0]["opening_mm"] == -0.03
    assert summary["qualified_for_design"] is False
    with zipfile.ZipFile(archive) as bundle:
        assert "cycle-13/frame.dat" in bundle.namelist()
        assert "source_snapshots/scripts/producer.py" in bundle.namelist()
    with pytest.raises(FileExistsError):
        build(source, archive)


def test_rejects_changed_source_and_unfinished_run(tmp_path):
    source = _fixture(tmp_path / "run")
    (source / "source_snapshots/scripts/producer.py").write_text("changed")
    with pytest.raises(ValueError, match="digest"):
        build(source, tmp_path / "bad.zip")
    source = _fixture(tmp_path / "run2")
    report_path = source / "report.json"
    report = json.loads(report_path.read_text())
    report["axial_tension_active_set_converged"] = False
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="converged"):
        build(source, tmp_path / "unfinished.zip")


def test_rejects_tampered_archive(tmp_path):
    source = _fixture(tmp_path / "run")
    archive = tmp_path / "pack.zip"
    build(source, archive)
    with zipfile.ZipFile(archive) as bundle:
        members = {name: bundle.read(name) for name in bundle.namelist()}
    members["cycle-13/frame.dat"] = b"tampered"
    with zipfile.ZipFile(archive, "w") as bundle:
        for name, data in members.items():
            bundle.writestr(name, data)
    with pytest.raises(ValueError, match="digest"):
        verify(archive)


def test_compare_signed_case_differences(tmp_path):
    a = _fixture(tmp_path / "a")
    k = _fixture(tmp_path / "k")
    scope_path = k / "diagnostic-scope.json"
    scope = json.loads(scope_path.read_text())
    scope["case"] = "k12-right"
    scope_path.write_text(json.dumps(scope))
    input_path = k / "cycle-13/input.json"
    input_path.write_text('{"hold": "K12"}')
    report_path = k / "report.json"
    report = json.loads(report_path.read_text())
    report["diagnostic_scope"] = scope
    report["artifact_sha256"]["diagnostic-scope.json"] = _sha(scope_path.read_bytes())
    report["artifact_sha256"]["cycle-13/input.json"] = _sha(input_path.read_bytes())
    report["axial_tension"][1]["extension_mm"] = 0.03
    report["axial_tension"][1]["tension_force_n"] = 30.0
    final_path = k / "cycle-13/report.json"
    final = json.loads(final_path.read_text())
    final["axial_tension"] = report["axial_tension"]
    final_path.write_text(json.dumps(final))
    report["artifact_sha256"]["cycle-13/report.json"] = _sha(final_path.read_bytes())
    report_path.write_text(json.dumps(report))
    left, right = tmp_path / "a.zip", tmp_path / "k.zip"
    build(a, left)
    build(k, right)
    result = compare(left, right, tmp_path / "comparison.json")
    rail = next(row for row in result["axial_tension"] if row["name"] == "pb01_rail_r1")
    assert rail["delta_extension_mm"] == pytest.approx(0.01)
    assert rail["delta_tension_force_n"] == 10.0
