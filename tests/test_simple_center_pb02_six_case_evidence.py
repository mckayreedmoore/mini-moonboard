"""The compact PB02 six-case package is authenticated fail closed."""

import copy
import hashlib
import json
import shutil

import pytest

from scripts import simple_center_pb02_six_case_evidence as evidence


def test_six_case_evidence_authenticates_complete_compact_package():
    result = evidence.screen()

    assert result["summary"] == {
        "path": "six-case/pb02-six-case-diagnostic.json",
        "sha256": evidence.EXPECTED_SUMMARY_SHA256,
        "candidate": evidence.CANDIDATE,
        "geometry_fingerprint": evidence.EXPECTED_GEOMETRY_FINGERPRINT,
        "deterministic_input_fingerprint": evidence.EXPECTED_SCOPE_FINGERPRINT,
        "partition_fingerprint": evidence.EXPECTED_PARTITION_FINGERPRINT,
        "floor_contact_n_per_mm": 10000.0,
        "accepted_case_count": 6,
    }
    assert set(result["cases"]) == set(evidence.EXPECTED_CASES)
    for name, row in result["cases"].items():
        assert (
            row["full_load_vector_xyz_n"]
            == evidence.EXPECTED_CASES[name]["force_xyz_n"]
        )
        assert set(row["final_cycle_artifact_sha256"]) == set(evidence.FINAL_ARTIFACTS)
    assert result["source_snapshot_authentication"] == {
        "path": "../source_snapshots",
        "file_count": 278,
        "source_sha256_map_identical_across_reports": True,
        "all_snapshot_hashes_match": True,
        "summary_producer_map_is_authenticated_subset": True,
    }
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False


def _mutated_summary(tmp_path, monkeypatch, mutate):
    summary = json.loads(evidence.SUMMARY.read_text())
    mutate(summary)
    target = tmp_path / "pb02-six-case-diagnostic.json"
    target.write_text(json.dumps(summary))
    monkeypatch.setattr(evidence, "SUMMARY", target)
    monkeypatch.setattr(
        evidence,
        "EXPECTED_SUMMARY_SHA256",
        hashlib.sha256(target.read_bytes()).hexdigest(),
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda summary: summary.update(active_geometry_fingerprint="changed"),
        lambda summary: summary.update(accepted_case_count=5),
        lambda summary: summary["loads"]["a12-left"].update(
            horizontal_force_xy_n=[300.0, 0.0]
        ),
        lambda summary: summary["stiffness_selection"]["exact_selected_values"].update(
            floor_contact_n_per_mm=9999.0
        ),
        lambda summary: summary.update(drilling_released=True),
        lambda summary: summary["validation"].update(six_case_load_inventory=False),
        lambda summary: summary.update(validation={}),
    ],
)
def test_summary_authentication_fails_closed(tmp_path, monkeypatch, mutate):
    _mutated_summary(tmp_path, monkeypatch, mutate)

    with pytest.raises(ValueError, match="summary identity changed"):
        evidence.screen()


def test_summary_hash_is_pinned(tmp_path, monkeypatch):
    target = tmp_path / "pb02-six-case-diagnostic.json"
    target.write_bytes(evidence.SUMMARY.read_bytes() + b"\n")
    monkeypatch.setattr(evidence, "SUMMARY", target)

    with pytest.raises(ValueError, match="summary hash changed"):
        evidence.screen()


def _mutated_report(tmp_path, monkeypatch, name, mutate):
    package = tmp_path / "package"
    six_case = package / "six-case"
    shutil.copytree(evidence.SIX_CASE, six_case)
    monkeypatch.setattr(evidence, "PACKAGE", package)
    monkeypatch.setattr(evidence, "SIX_CASE", six_case)
    monkeypatch.setattr(evidence, "SUMMARY", six_case / evidence.SUMMARY.name)
    monkeypatch.setattr(
        evidence,
        "EXPECTED_SUMMARY_SHA256",
        hashlib.sha256(evidence.SUMMARY.read_bytes()).hexdigest(),
    )
    expected_cases = copy.deepcopy(evidence.EXPECTED_CASES)
    report_path = six_case / expected_cases[name]["path"] / "report.json"
    report = json.loads(report_path.read_text())
    mutate(report)
    report_path.write_text(json.dumps(report))
    digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
    expected_cases[name]["report_sha256"] = digest
    monkeypatch.setattr(evidence, "EXPECTED_CASES", expected_cases)
    summary = json.loads(evidence.SUMMARY.read_text())
    summary["accepted_cases"][name]["report_sha256"] = digest
    for attempt in summary["attempts"]:
        if attempt["case"] == name:
            attempt["native_report_sha256"] = digest
    evidence.SUMMARY.write_text(json.dumps(summary))
    monkeypatch.setattr(
        evidence,
        "EXPECTED_SUMMARY_SHA256",
        hashlib.sha256(evidence.SUMMARY.read_bytes()).hexdigest(),
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda report: report["parameters"].update(force_xyz_n=[0.0, 0.0, 0.0]),
        lambda report: report.update(pb02_model_identity="changed"),
        lambda report: report["diagnostic_scope"].update(
            deterministic_input_fingerprint="changed"
        ),
        lambda report: report["pb02_contact_aggregation"].update(
            partition_fingerprint="changed"
        ),
        lambda report: report["diagnostic_scope"]["stiffness_selection"][
            "exact_selected_values"
        ].update(floor_contact_n_per_mm=9999.0),
        lambda report: report.update(global_equilibrium_passed=False),
        lambda report: report.update(numerically_accepted=False),
        lambda report: report.update(fabrication_released=True),
    ],
)
def test_case_report_authentication_fails_closed(tmp_path, monkeypatch, mutate):
    _mutated_report(tmp_path, monkeypatch, "a12-forward", mutate)

    with pytest.raises(ValueError, match="authenticated report scope changed"):
        evidence.screen()


def test_retained_final_cycle_artifact_is_authenticated(tmp_path, monkeypatch):
    package = tmp_path / "package"
    shutil.copytree(evidence.PACKAGE, package)
    monkeypatch.setattr(evidence, "PACKAGE", package)
    monkeypatch.setattr(evidence, "SIX_CASE", package / "six-case")
    monkeypatch.setattr(
        evidence,
        "SUMMARY",
        package / "six-case/pb02-six-case-diagnostic.json",
    )
    monkeypatch.setattr(evidence, "SOURCE_SNAPSHOTS", package / "source_snapshots")
    case = evidence.EXPECTED_CASES["a12-forward"]
    artifact = package / "six-case" / case["path"] / "cycle-11/input.json"
    artifact.write_bytes(artifact.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="retained final-cycle artifact changed"):
        evidence.screen()


def test_common_source_snapshot_is_authenticated(tmp_path, monkeypatch):
    snapshots = tmp_path / "source_snapshots"
    shutil.copytree(evidence.SOURCE_SNAPSHOTS, snapshots)
    target = snapshots / "scripts/simple_center_pb02_geometry.py"
    target.write_text(target.read_text() + "\n# changed\n")
    monkeypatch.setattr(evidence, "SOURCE_SNAPSHOTS", snapshots)

    with pytest.raises(ValueError, match="common source snapshot closure changed"):
        evidence.screen()


def test_source_authentication_ignores_files_outside_pb02_manifest(
    tmp_path, monkeypatch
):
    snapshots = tmp_path / "source_snapshots"
    shutil.copytree(evidence.SOURCE_SNAPSHOTS, snapshots)
    unrelated = snapshots / "scripts/simple_pb03_future_study.py"
    unrelated.write_text("# unrelated PB03 source\n")
    monkeypatch.setattr(evidence, "SOURCE_SNAPSHOTS", snapshots)

    result = evidence.screen()

    assert result["source_snapshot_authentication"]["file_count"] == 278
