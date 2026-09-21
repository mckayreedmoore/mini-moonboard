"""Retained PB05 first-case evidence must authenticate and fail closed."""

import json

import pytest

from scripts import simple_pb05_first_case_evidence as evidence


def test_retained_first_case_authenticates():
    result = evidence.screen()
    assert result["case"] == "a12-forward"
    assert result["cycle_count"] == 9
    assert result["fixed_panel_kicker_axis_count"] == 66
    assert result["legacy_station_count"] == 14
    assert result["pb05_bolt_count"] == 32
    assert result["pb05_contact_cell_count"] == 64
    assert result["source_snapshot_authentication"] == {
        "file_count": 293,
        "producer_file_count": 206,
    }
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False


def test_summary_hash_corruption_fails(tmp_path, monkeypatch):
    target = tmp_path / "summary.json"
    target.write_bytes(evidence.SUMMARY.read_bytes() + b"\n")
    monkeypatch.setattr(evidence, "SUMMARY", target)
    with pytest.raises(ValueError, match="summary hash"):
        evidence.screen()


def test_retained_artifact_hash_corruption_fails(tmp_path, monkeypatch):
    report = json.loads((evidence.ATTEMPT / "report.json").read_text())
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    target = attempt / "model.pkl"
    target.write_bytes(b"changed")
    monkeypatch.setattr(evidence, "ATTEMPT", attempt)
    with pytest.raises(ValueError, match="retained artifact"):
        evidence._authenticate_artifacts(report)


def test_source_identity_fails_even_if_hash_repin():
    summary = json.loads(evidence.SUMMARY.read_text())
    summary["mechanics_identity"]["source_fingerprint_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="summary identity"):
        evidence._validate_summary(summary)


@pytest.mark.parametrize(
    "field,value",
    [
        ("legacy_station_count", 13),
        ("fixed_panel_kicker_axis_count", 65),
        ("pb05_tension_only_bolt_count", 31),
        ("pb05_contact_cell_count", 63),
    ],
)
def test_topology_fails_even_if_hash_repin(field, value):
    summary = json.loads(evidence.SUMMARY.read_text())
    summary["topology_inventory"][field] = value
    with pytest.raises(ValueError, match="summary identity"):
        evidence._validate_summary(summary)


def test_load_and_equilibrium_fail_even_if_hash_repin():
    summary = json.loads(evidence.SUMMARY.read_text())
    inventory = evidence._validate_summary(summary)
    report = json.loads((evidence.ATTEMPT / "report.json").read_text())
    report["parameters"]["force_xyz_n"][1] = -299.0
    with pytest.raises(ValueError, match="report identity"):
        evidence._validate_report(report, summary, inventory)
    report["parameters"]["force_xyz_n"] = evidence.FORCE_XYZ_N
    report["force_residual_n"][0] = 0.2
    with pytest.raises(ValueError, match="numerical equilibrium"):
        evidence._validate_report(report, summary, inventory)


def test_release_flag_fails_even_if_hash_repin():
    summary = json.loads(evidence.SUMMARY.read_text())
    summary["drilling_released"] = True
    with pytest.raises(ValueError, match="summary identity"):
        evidence._validate_summary(summary)


def test_source_snapshot_hash_corruption_fails(tmp_path, monkeypatch):
    summary = json.loads(evidence.SUMMARY.read_text())
    report = json.loads((evidence.ATTEMPT / "report.json").read_text())
    snapshots = tmp_path / "source_snapshots"
    snapshots.mkdir()
    (snapshots / "unrelated.py").write_text("pass\n")
    monkeypatch.setattr(evidence, "SNAPSHOTS", snapshots)
    with pytest.raises(ValueError, match="source snapshot closure"):
        evidence._authenticate_sources(summary, report)


def test_package_inventory_rejects_extra_bulk(tmp_path, monkeypatch):
    package = tmp_path / "package"
    package.mkdir()
    (package / "extra.frd").write_text("bulk")
    monkeypatch.setattr(evidence, "PACKAGE", package)
    monkeypatch.setattr(evidence, "SUMMARY", package / "summary.json")
    monkeypatch.setattr(evidence, "ATTEMPT", package / "attempt")
    monkeypatch.setattr(evidence, "SNAPSHOTS", package / "snapshots")
    with pytest.raises(ValueError, match="missing or extra files"):
        evidence._authenticate_package_inventory({"source_sha256": {}})
