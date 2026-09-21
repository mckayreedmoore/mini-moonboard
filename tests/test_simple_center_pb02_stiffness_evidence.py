"""Compact PB02 stiffness evidence is deterministic and fails closed."""

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from scripts import simple_center_pb02_stiffness_evidence as evidence

TRIALS = (5000.0, 10000.0, 15000.0)
CASES = ("a12-forward", "a12-rear")
ARTIFACTS = ("input.json", "frame.dat", "frame.frd", "frame.12d")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_suite(root: Path, stiffness: float, source_map: dict[str, str]) -> None:
    accepted = {}
    reports = {}
    for index, case in enumerate(CASES):
        relative = f"attempts/{case}-01-all-unseeded"
        directory = root / relative
        cycle = f"cycle-{index:02d}"
        (directory / cycle).mkdir(parents=True)
        snapshots = directory / "source_snapshots"
        snapshots.mkdir()
        (snapshots / "producer.py").write_text("VALUE = 1\n")
        model_data = f"model:{stiffness}:{case}\n".encode()
        (directory / "model.pkl").write_bytes(model_data)
        artifact_hashes = {}
        for filename in ARTIFACTS:
            data = (
                b""
                if filename == "frame.12d"
                else f"{stiffness}:{case}:{filename}\n".encode()
            )
            path = directory / cycle / filename
            path.write_bytes(data)
            artifact_hashes[f"{cycle}/{filename}"] = _sha256(data)
        report = {
            "candidate": "candidate",
            "pb02_model_identity": _sha256(model_data),
            "parameters": {
                "hold": "A12",
                "stiffnesses": {"floor": stiffness},
                "force_xyz_n": [float(index), 0.0, -1.0],
            },
            "contact_cycles": [{"directory": cycle}],
            "artifact_sha256": artifact_hashes,
            "source_sha256": source_map,
            "contact_active_set_converged": True,
            "axial_tension_active_set_converged": True,
            "axial_tension_assumption_passed": True,
            "closed_bearing_assumption_passed": True,
            "global_equilibrium_passed": True,
            "member_equilibrium_passed": True,
            "mpc_check_passed": True,
            "numerically_accepted": True,
            "diagnostic_scope": {
                "case": case,
                "candidate": "candidate",
                "deterministic_input_fingerprint": f"scope-{stiffness}",
                "stiffness_selection": {
                    "exact_selected_values": {"floor_contact_n_per_mm": stiffness}
                },
                "developmental_only": True,
                "qualified_for_design": False,
                "actual_joint_demands_qualified": False,
                "resistance_checked": False,
                "acceptance": False,
                "drilling_released": False,
                "fabrication_released": False,
            },
            "qualified_for_design": False,
            "actual_joint_demands_qualified": False,
            "drilling_released": False,
            "fabrication_released": False,
        }
        report_path = directory / "report.json"
        report_path.write_text(json.dumps(report, sort_keys=True))
        report_hash = _sha256(report_path.read_bytes())
        accepted[case] = {
            "path": relative,
            "report_sha256": report_hash,
            "numerically_accepted": True,
            "forces_reported_only_in_authenticated_case_report": True,
        }
        reports[case] = report
    summary = {
        "schema": "simple_center_pb02_diagnostic_run/v1",
        "candidate": "candidate",
        "active_geometry_fingerprint": "geometry",
        "case_order": list(CASES),
        "loads": {
            case: {
                "hold": "A12",
                "horizontal_force_xy_n": [float(index), 0.0],
            }
            for index, case in enumerate(CASES)
        },
        "geometry_inventory": {"candidate": "candidate"},
        "accepted_case_count": len(CASES),
        "accepted_cases": accepted,
        "producer_source_sha256": source_map,
        "stiffness_selection": {
            "exact_selected_values": {"floor_contact_n_per_mm": stiffness}
        },
        "validation": evidence.EXPECTED_VALIDATION,
        "rejected_attempt_forces_included": False,
        "developmental_only": True,
        "qualified_for_design": False,
        "actual_joint_demands_qualified": False,
        "resistance_checked": False,
        "acceptance": False,
        "drilling_released": False,
        "fabrication_released": False,
    }
    identity = {key: summary[key] for key in evidence.SUMMARY_IDENTITY_FIELDS}
    summary["deterministic_input_fingerprint"] = evidence._canonical_sha256(identity)
    for case in CASES:
        relative = summary["accepted_cases"][case]["path"]
        report_path = root / relative / "report.json"
        report = json.loads(report_path.read_text())
        report["diagnostic_scope"]["deterministic_input_fingerprint"] = summary[
            "deterministic_input_fingerprint"
        ]
        report_path.write_text(json.dumps(report, sort_keys=True))
        summary["accepted_cases"][case]["report_sha256"] = _sha256(
            report_path.read_bytes()
        )
    (root / "pb02-six-case-diagnostic.json").write_text(
        json.dumps(summary, sort_keys=True)
    )
    del reports


def _write_failed_suite(root: Path, stiffness: float, source_map: dict[str, str]):
    root.mkdir()
    attempts = root / "attempts"
    for case, accepted, strategy in (
        ("a12-forward", True, "all"),
        ("a12-rear", False, "all"),
        ("a12-rear", False, "one_at_a_time"),
    ):
        suffix = "01-all-unseeded" if strategy == "all" else "02-one-at-a-time"
        directory = attempts / f"{case}-{suffix}"
        directory.mkdir(parents=True)
        model = f"failed-model:{case}:{strategy}".encode()
        (directory / "model.pkl").write_bytes(model)
        report = {
            "candidate": "candidate",
            "parameters": {
                "stiffnesses": {"floor": stiffness},
                "force_xyz_n": [9.0, 8.0, 7.0],
            },
            "source_sha256": source_map,
            "pb02_model_identity": _sha256(model) if accepted else None,
            "contact_active_set_converged": accepted,
            "numerically_accepted": accepted,
            "contact_update_strategy": strategy,
            "termination": ("converged" if accepted else "Contact active set repeated"),
            "contact_cycles": [{"directory": "cycle-00"}],
            "physical_connection_forces": {"must_not_be_retained": [1, 2, 3]},
            "qualified_for_design": False,
            "actual_joint_demands_qualified": False,
        }
        if accepted:
            report["diagnostic_scope"] = {"case": case}
        (directory / "report.json").write_text(json.dumps(report, sort_keys=True))


@pytest.fixture
def suites(tmp_path):
    source_map = {"producer.py": _sha256(b"VALUE = 1\n")}
    roots = {}
    for stiffness in TRIALS:
        root = tmp_path / f"suite-{int(stiffness)}"
        root.mkdir()
        _write_suite(root, stiffness, source_map)
        roots[stiffness] = root

    return roots


def _rewrite_manifest_checksum(package: Path) -> None:
    manifest = (package / "manifest.json").read_bytes()
    (package / "manifest.sha256").write_text(f"{_sha256(manifest)}  manifest.json\n")


def test_build_is_deterministic_deduplicated_and_self_authenticating(tmp_path, suites):
    first = tmp_path / "first"
    second = tmp_path / "second"

    evidence.build(suites, first, ordered_stiffnesses=TRIALS)
    evidence.build(suites, second, ordered_stiffnesses=TRIALS)

    assert (first / "manifest.json").read_bytes() == (
        second / "manifest.json"
    ).read_bytes()
    first_objects = sorted((first / "objects").rglob("*.gz"))
    second_objects = sorted((second / "objects").rglob("*.gz"))
    assert [path.relative_to(first) for path in first_objects] == [
        path.relative_to(second) for path in second_objects
    ]
    assert [path.read_bytes() for path in first_objects] == [
        path.read_bytes() for path in second_objects
    ]
    assert all(path.read_bytes()[4:8] == b"\0\0\0\0" for path in first_objects)

    result = evidence.authenticate(first)
    assert result["trial_floor_contact_n_per_mm"] == list(TRIALS)
    assert result["source_maps_identical"] is True
    assert result["producer_source_maps_identical"] is True
    assert result["single_variable_stiffness_comparison_eligible"] is True
    assert result["qualified_for_design"] is False
    assert result["structural_released"] is False
    assert set(result["reports"]) == set(TRIALS)
    assert set(result["reports"][5000.0]) == set(CASES)

    manifest = json.loads((first / "manifest.json").read_text())
    empty_digest = _sha256(b"")
    assert empty_digest in manifest["objects"]
    assert sum(
        artifact == empty_digest
        for trial in manifest["trials"].values()
        for case in trial["cases"].values()
        for artifact in case["artifacts"].values()
    ) == len(TRIALS) * len(CASES)
    empty_object = first / manifest["objects"][empty_digest]["path"]
    assert gzip.decompress(empty_object.read_bytes()) == b""


def test_builder_requires_exact_explicit_trials_and_identical_source_maps(
    tmp_path, suites
):
    with pytest.raises(ValueError, match="accepted suites must exactly match"):
        evidence.build(
            {5000.0: suites[5000.0]},
            tmp_path / "missing",
            ordered_stiffnesses=TRIALS,
        )

    report_path = suites[15000.0] / "attempts/a12-forward-01-all-unseeded/report.json"
    report = json.loads(report_path.read_text())
    report["source_sha256"] = {"producer.py": "f" * 64}
    report_path.write_text(json.dumps(report, sort_keys=True))
    summary_path = suites[15000.0] / "pb02-six-case-diagnostic.json"
    summary = json.loads(summary_path.read_text())
    summary["accepted_cases"]["a12-forward"]["report_sha256"] = _sha256(
        report_path.read_bytes()
    )
    summary_path.write_text(json.dumps(summary, sort_keys=True))
    with pytest.raises(ValueError, match="full source maps must be identical"):
        evidence.build(suites, tmp_path / "mismatch", ordered_stiffnesses=TRIALS)


def test_builder_rejects_suite_path_traversal(tmp_path, suites):
    summary_path = suites[5000.0] / "pb02-six-case-diagnostic.json"
    summary = json.loads(summary_path.read_text())
    summary["accepted_cases"]["a12-forward"]["path"] = "../escape"
    summary_path.write_text(json.dumps(summary, sort_keys=True))

    with pytest.raises(ValueError, match="escapes"):
        evidence.build(suites, tmp_path / "package", ordered_stiffnesses=TRIALS)


def test_builder_uses_retained_snapshot_closure_not_live_sources(tmp_path, suites):
    assert not hasattr(evidence, "SOURCE_ROOT")
    snapshot = (
        suites[5000.0]
        / "attempts/a12-forward-01-all-unseeded/source_snapshots/producer.py"
    )
    snapshot.unlink()

    with pytest.raises(ValueError, match="snapshot inventory changed"):
        evidence.build(suites, tmp_path / "package", ordered_stiffnesses=TRIALS)


def test_authenticator_rejects_tampered_missing_and_unreferenced_objects(
    tmp_path, suites
):
    package = tmp_path / "package"
    evidence.build(suites, package, ordered_stiffnesses=TRIALS)
    manifest = json.loads((package / "manifest.json").read_text())
    object_path = package / next(iter(manifest["objects"].values()))["path"]
    original = object_path.read_bytes()

    object_path.write_bytes(original + b"tampered")
    with pytest.raises(ValueError, match="compressed object changed"):
        evidence.authenticate(package)
    object_path.write_bytes(original)

    object_path.unlink()
    with pytest.raises(ValueError, match="object file is missing"):
        evidence.authenticate(package)
    object_path.parent.mkdir(parents=True, exist_ok=True)
    object_path.write_bytes(original)

    extra = package / "objects/ff" / ("f" * 64 + ".gz")
    extra.parent.mkdir(parents=True)
    extra.write_bytes(gzip.compress(b"extra", mtime=0))
    with pytest.raises(ValueError, match="object inventory changed"):
        evidence.authenticate(package)


def test_authenticator_rejects_manifest_path_traversal(tmp_path, suites):
    package = tmp_path / "package"
    evidence.build(suites, package, ordered_stiffnesses=TRIALS)
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    descriptor = next(iter(manifest["objects"].values()))
    descriptor["path"] = "../outside.gz"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    _rewrite_manifest_checksum(package)

    with pytest.raises(ValueError, match="object path"):
        evidence.authenticate(package)


def test_authenticator_rejects_manifest_tampering(tmp_path, suites):
    package = tmp_path / "package"
    evidence.build(suites, package, ordered_stiffnesses=TRIALS)
    manifest = package / "manifest.json"
    manifest.write_bytes(manifest.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="manifest checksum changed"):
        evidence.authenticate(package)


def test_authenticator_rejects_rechecksummed_unreferenced_object(tmp_path, suites):
    package = tmp_path / "package"
    evidence.build(suites, package, ordered_stiffnesses=TRIALS)
    data = b"unreferenced"
    digest = _sha256(data)
    compressed = evidence._gzip_bytes(data)
    relative = f"objects/{digest[:2]}/{digest}.gz"
    path = package / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(compressed)
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["objects"][digest] = {
        "path": relative,
        "uncompressed_size": len(data),
        "gzip_size": len(compressed),
        "gzip_sha256": _sha256(compressed),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    _rewrite_manifest_checksum(package)

    with pytest.raises(ValueError, match="unreferenced or missing"):
        evidence.authenticate(package)


def test_failed_trial_is_sanitized_and_cannot_fill_an_accepted_slot(tmp_path, suites):
    failed = tmp_path / "suite-20000"
    source_map = json.loads(
        (suites[5000.0] / "pb02-six-case-diagnostic.json").read_text()
    )["producer_source_sha256"]
    _write_failed_suite(failed, 20000.0, source_map)
    package = tmp_path / "package"

    evidence.build(
        suites,
        package,
        ordered_stiffnesses=TRIALS,
        failed_suites={
            20000.0: evidence.FailedSuiteSpec(
                failed, "a12-rear", "bounded retries exhausted"
            )
        },
    )

    manifest = json.loads((package / "manifest.json").read_text())
    failed_record = manifest["failed_trials"]["20000"]
    assert failed_record["status"] == "failed_nonconverged_not_accepted"
    assert failed_record["accepted_comparison_slot"] is False
    assert failed_record["forces_retained"] is False
    assert failed_record["accepted_case_count_before_failure"] == 1
    assert failed_record["failure_reason"] == "bounded retries exhausted"
    assert failed_record["failure_case"] == "a12-rear"
    assert failed_record["attempts"][-1]["termination"] == (
        "Contact active set repeated"
    )
    assert "force_xyz_n" not in json.dumps(failed_record)
    assert "physical_connection_forces" not in json.dumps(failed_record)
    assert not (failed / "pb02-six-case-diagnostic.json").exists()
    assert manifest["accepted_trial_order_n_per_mm"] == list(TRIALS)
    assert 20000.0 not in evidence.authenticate(package)["trial_floor_contact_n_per_mm"]


def test_failed_trial_cannot_replace_missing_accepted_trial(tmp_path, suites):
    failed = tmp_path / "suite-15000-failed"
    source_map = json.loads(
        (suites[5000.0] / "pb02-six-case-diagnostic.json").read_text()
    )["producer_source_sha256"]
    _write_failed_suite(failed, 15000.0, source_map)

    with pytest.raises(ValueError, match="accepted suites must exactly match"):
        evidence.build(
            {5000.0: suites[5000.0], 10000.0: suites[10000.0]},
            tmp_path / "package",
            ordered_stiffnesses=TRIALS,
            failed_suites={
                15000.0: evidence.FailedSuiteSpec(
                    failed, "a12-rear", "bounded retries exhausted"
                )
            },
        )


def test_failed_trial_manifest_rejects_added_force_payload(tmp_path, suites):
    failed = tmp_path / "suite-20000"
    source_map = json.loads(
        (suites[5000.0] / "pb02-six-case-diagnostic.json").read_text()
    )["producer_source_sha256"]
    _write_failed_suite(failed, 20000.0, source_map)
    package = tmp_path / "package"
    evidence.build(
        suites,
        package,
        ordered_stiffnesses=TRIALS,
        failed_suites={
            20000.0: evidence.FailedSuiteSpec(
                failed, "a12-rear", "bounded retries exhausted"
            )
        },
    )
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["failed_trials"]["20000"]["attempts"][-1]["force_xyz_n"] = [1, 2, 3]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    _rewrite_manifest_checksum(package)

    with pytest.raises(ValueError, match="failed trial record changed"):
        evidence.authenticate(package)
