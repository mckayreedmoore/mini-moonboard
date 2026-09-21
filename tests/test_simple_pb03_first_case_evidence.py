"""The compact PB03 first-case evidence fails closed on identity and artifacts."""

import hashlib
import json
import shutil

import pytest

from scripts import simple_pb03_first_case_evidence as evidence


def test_retained_first_case_authenticates_completely():
    result = evidence.screen()

    assert result == {
        "schema": "simple_pb03_first_case_evidence/v1",
        "candidate": evidence.CANDIDATE,
        "case": "a12-forward",
        "deterministic_input_fingerprint": evidence.INPUT_FINGERPRINT,
        "summary_sha256": evidence.SUMMARY_SHA256,
        "report_sha256": evidence.REPORT_SHA256,
        "model_sha256": evidence.MODEL_SHA256,
        "final_cycle": "cycle-08",
        "cycle_count": 9,
        "tension_only_bolt_count": 42,
        "pb03_contact_cell_count": 64,
        "pb03_block_count": 8,
        "source_snapshot_authentication": {
            "path": "attempts/a12-forward-01-all-unseeded/source_snapshots",
            "file_count": 287,
            "all_snapshot_hashes_match": True,
            "summary_producer_map_is_authenticated_subset": True,
        },
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


def _summary():
    return json.loads(evidence.SUMMARY.read_text())


@pytest.mark.parametrize(
    "mutate",
    [
        lambda row: row.update(candidate="wrong"),
        lambda row: row.update(deterministic_input_fingerprint="wrong"),
        lambda row: row["loads"]["a12-forward"].update(
            horizontal_force_xy_n=[0.0, 300.0]
        ),
        lambda row: row.update(accepted_case_count=2),
        lambda row: row["topology_inventory"].update(pb03_tension_only_bolt_count=31),
        lambda row: row["topology_inventory"].update(pb03_contact_cell_count=63),
        lambda row: row["topology_inventory"].update(block_member_count=7),
        lambda row: row.update(drilling_released=True),
    ],
)
def test_summary_semantics_fail_closed_even_if_hash_were_repinned(mutate):
    summary = _summary()
    mutate(summary)

    with pytest.raises(ValueError, match="summary identity changed"):
        evidence._validate_summary(summary)


def test_summary_hash_is_pinned(tmp_path, monkeypatch):
    target = tmp_path / evidence.SUMMARY.name
    target.write_bytes(evidence.SUMMARY.read_bytes() + b"\n")
    monkeypatch.setattr(evidence, "SUMMARY", target)

    with pytest.raises(ValueError, match="summary hash changed"):
        evidence.screen()


def _report_and_inventory():
    report = json.loads((evidence.ATTEMPT / "report.json").read_text())
    inventory = evidence._validate_summary(_summary())
    return report, inventory


def _drop_pb03_contact(report):
    name = _summary()["topology_inventory"]["pb03_contact_names"][0]
    report["bearings"] = [row for row in report["bearings"] if row["name"] != name]


def _drop_pb03_block(report):
    name = _summary()["topology_inventory"]["block_member_names"][0]
    report["member_section_demands"].pop(name)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda row: row.update(candidate="wrong"), "report identity"),
        (lambda row: row.update(pb03_diagnostic_identity="wrong"), "report identity"),
        (
            lambda row: row["parameters"].update(
                force_xyz_n=[0.0, 300.0, -2224.11080763025]
            ),
            "report identity",
        ),
        (lambda row: row.update(global_equilibrium_passed=False), "report identity"),
        (lambda row: row["contact_cycles"].pop(), "report identity"),
        (lambda row: row["axial_tension_names"].pop(), "report identity"),
        (_drop_pb03_contact, "contact inventory"),
        (_drop_pb03_block, "block inventory"),
        (
            lambda row: row["physical_connection_forces"].pop(
                next(iter(_summary()["topology_inventory"]["required_physical_names"]))
            ),
            "physical-force inventory",
        ),
        (lambda row: row.update(fabrication_released=True), "report identity"),
    ],
)
def test_report_semantics_fail_closed_even_if_hash_were_repinned(mutate, message):
    report, inventory = _report_and_inventory()
    mutate(report)

    with pytest.raises(ValueError, match=message):
        evidence._validate_report(report, inventory)


def test_selected_artifact_hashes_are_pinned(tmp_path, monkeypatch):
    report, _ = _report_and_inventory()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    for relative in evidence.SELECTED_ARTIFACTS:
        source = evidence.ATTEMPT / relative
        target = attempt / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    (attempt / "cycle-08/input.json").write_bytes(
        (attempt / "cycle-08/input.json").read_bytes() + b"\n"
    )
    monkeypatch.setattr(evidence, "ATTEMPT", attempt)

    with pytest.raises(ValueError, match="retained artifact changed"):
        evidence._authenticate_artifacts(report)


def test_source_snapshot_map_is_complete(tmp_path, monkeypatch):
    summary = _summary()
    report, _ = _report_and_inventory()
    snapshots = tmp_path / "source_snapshots"
    snapshots.mkdir()
    producer_name, producer_digest = next(
        iter(summary["producer_source_sha256"].items())
    )
    target = snapshots / producer_name
    target.parent.mkdir(parents=True)
    target.write_text("wrong\n")
    assert hashlib.sha256(target.read_bytes()).hexdigest() != producer_digest
    monkeypatch.setattr(evidence, "SOURCE_SNAPSHOTS", snapshots)

    with pytest.raises(ValueError, match="source snapshot closure changed"):
        evidence._authenticate_sources(summary, report)


def test_package_inventory_rejects_extra_solver_bulk(tmp_path, monkeypatch):
    package = tmp_path / "package"
    package.mkdir()
    extra = package / "cycle-08/frame.frd"
    extra.parent.mkdir()
    extra.write_text("solver bulk")
    monkeypatch.setattr(evidence, "PACKAGE", package)
    monkeypatch.setattr(evidence, "SUMMARY", package / "summary.json")
    monkeypatch.setattr(evidence, "ATTEMPT", package / "attempt")
    monkeypatch.setattr(evidence, "SOURCE_SNAPSHOTS", package / "snapshots")
    report = {"source_sha256": {}}

    with pytest.raises(ValueError, match="missing or extra files"):
        evidence._authenticate_package_inventory(report)


def test_retained_package_ignores_python_cache_only(tmp_path, monkeypatch):
    package = tmp_path / "package"
    shutil.copytree(evidence.PACKAGE, package)
    attempt = package / evidence.ATTEMPT_PATH
    snapshots = attempt / "source_snapshots"
    cache = snapshots / "scripts/__pycache__/native.cpython-312.pyc"
    cache.parent.mkdir()
    cache.write_bytes(b"transient bytecode")
    monkeypatch.setattr(evidence, "PACKAGE", package)
    monkeypatch.setattr(evidence, "SUMMARY", package / evidence.SUMMARY.name)
    monkeypatch.setattr(evidence, "ATTEMPT", attempt)
    monkeypatch.setattr(evidence, "SOURCE_SNAPSHOTS", snapshots)

    assert evidence.screen()["source_snapshot_authentication"]["file_count"] == 287

    unlisted = snapshots / "scripts/unlisted.py"
    unlisted.write_text("pass\n")
    with pytest.raises(ValueError, match="extra=\\['scripts/unlisted.py'\\]"):
        evidence.screen()

    unlisted.unlink()
    (snapshots / "scripts/simple_pb03_native_mechanics.py").unlink()
    with pytest.raises(
        ValueError, match="missing=\\['scripts/simple_pb03_native_mechanics.py'\\]"
    ):
        evidence.screen()
