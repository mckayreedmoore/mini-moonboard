"""Retained PB04 first-case evidence must fail closed."""

import json

import pytest

from scripts import simple_pb04_first_case_evidence as evidence


def test_retained_first_case_authenticates():
    result = evidence.screen()
    assert result["case"] == "a12-forward"
    assert result["cycle_count"] == 9
    assert result["pb04_bolt_count"] == 32
    assert result["pb04_contact_cell_count"] == 64
    assert result["source_snapshot_authentication"]["file_count"] == 292
    assert result["source_snapshot_authentication"]["producer_file_count"] == 205
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


def test_report_semantics_fail_even_if_hash_repin():
    report = json.loads((evidence.ATTEMPT / "report.json").read_text())
    inventory = evidence._validate_summary(json.loads(evidence.SUMMARY.read_text()))
    report["contact_cycles"].pop()
    with pytest.raises(ValueError, match="report identity"):
        evidence._validate_report(report, inventory)


@pytest.mark.parametrize(
    "field,value",
    [
        ("pb04_tension_only_bolt_count", 31),
        ("pb04_contact_cell_count", 63),
        ("fixed_panel_kicker_axis_count", 65),
    ],
)
def test_summary_inventory_fails_even_if_hash_repin(field, value):
    summary = json.loads(evidence.SUMMARY.read_text())
    summary["topology_inventory"][field] = value
    with pytest.raises(ValueError, match="summary identity"):
        evidence._validate_summary(summary)


def test_snapshot_membership_rejects_unrelated_file(tmp_path, monkeypatch):
    summary = json.loads(evidence.SUMMARY.read_text())
    report = json.loads((evidence.ATTEMPT / "report.json").read_text())
    snapshots = tmp_path / "source_snapshots"
    snapshots.mkdir()
    (snapshots / "unrelated.py").write_text("pass\n")
    monkeypatch.setattr(evidence, "SOURCE_SNAPSHOTS", snapshots)
    with pytest.raises(ValueError, match="source snapshot closure"):
        evidence._authenticate_sources(summary, report)


def test_source_producer_manifest_fails_if_reassigned():
    summary = json.loads(evidence.SUMMARY.read_text())
    report = json.loads((evidence.ATTEMPT / "report.json").read_text())
    name = next(iter(summary["producer_source_sha256"]))
    summary["producer_source_sha256"][name] = "0" * 64
    with pytest.raises(ValueError, match="source snapshot closure"):
        evidence._authenticate_sources(summary, report)


def test_package_inventory_rejects_extra_bulk(tmp_path, monkeypatch):
    package = tmp_path / "package"
    package.mkdir()
    (package / "extra.frd").write_text("bulk")
    monkeypatch.setattr(evidence, "PACKAGE", package)
    monkeypatch.setattr(evidence, "SUMMARY", package / "summary.json")
    monkeypatch.setattr(evidence, "ATTEMPT", package / "attempt")
    monkeypatch.setattr(evidence, "SOURCE_SNAPSHOTS", package / "snapshots")
    with pytest.raises(ValueError, match="missing or extra files"):
        evidence._authenticate_package_inventory({"source_sha256": {}})


def test_package_inventory_rejects_unrelated_snapshot(tmp_path, monkeypatch):
    package = tmp_path / "package"
    attempt = package / evidence.ATTEMPT_PATH
    snapshots = attempt / "source_snapshots"
    snapshots.mkdir(parents=True)
    (package / evidence.SUMMARY.name).write_text("summary")
    (attempt / "report.json").write_text("report")
    for relative in evidence.SELECTED_ARTIFACTS:
        target = attempt / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("artifact")
    (snapshots / "pinned.py").write_text("pinned")
    (snapshots / "unrelated.py").write_text("unrelated")
    monkeypatch.setattr(evidence, "PACKAGE", package)
    monkeypatch.setattr(evidence, "SUMMARY", package / evidence.SUMMARY.name)
    monkeypatch.setattr(evidence, "ATTEMPT", attempt)
    monkeypatch.setattr(evidence, "SOURCE_SNAPSHOTS", snapshots)
    with pytest.raises(ValueError, match="missing or extra files"):
        evidence._authenticate_package_inventory({"source_sha256": {"pinned.py": "x"}})


def test_retained_artifact_hash_corruption_fails(tmp_path, monkeypatch):
    report = json.loads((evidence.ATTEMPT / "report.json").read_text())
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "model.pkl").write_bytes(b"changed")
    monkeypatch.setattr(evidence, "ATTEMPT", attempt)
    with pytest.raises(ValueError, match="retained artifact"):
        evidence._authenticate_artifacts(report)
