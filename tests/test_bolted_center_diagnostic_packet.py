"""Packet boundaries with synthetic report paths and a mocked native extractor."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts import bolted_center_diagnostic_packet as packet

REFERENCE_MANIFEST = Path(
    "docs/bolted-candidate-prototypes/center-reference-diagnostic.json"
)
ARCHIVED_MODEL_SHA256 = (
    "e724bbb74150923265b13be2513c2634c3cb02b4c3568c43b3aee55626507dce"
)


def make_case(root, series, case, accepted):
    folder = root / series / case
    folder.mkdir(parents=True)
    record_path = folder / "cycle-02" / "input.json"
    record_path.parent.mkdir()
    cases = {"a1-rear": ("A1", 0, 300), "a12-forward": ("A12", 0, -300)}
    hold, x_force, y_force = cases[case]
    force = [x_force, y_force, -2224.11080763025]
    proxy = "baseline ML24Z angles and SDS screws"
    record_path.write_text(
        json.dumps(
            {
                "candidate": "bolted-kerf-right-diagnostic-proxy",
                "hold": hold,
                "force_xyz_n": force,
                "provisional_structural_connectors": proxy,
                "diagnostic_only": True,
                "bolted_joint_demands": False,
            }
        )
    )
    scope = {
        "case": case,
        "source_geometry": "compact-floor-flush-bolted-development-kerf-right",
        "connector_proxy": proxy,
        "connection_scale": 1.0,
        "contact_stiffness_per_area_n_per_mm3": 100,
        "bolted_joint_demands": False,
        "acceptance": False,
        "drilling_released": False,
    }
    scope_path = folder / "diagnostic-scope.json"
    scope_path.write_text(json.dumps(scope))
    snapshots = {}
    for source in packet.SOURCE_KEYS:
        snapshot = folder / "source_snapshots" / source
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_text(source)
        snapshots[source] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    report = {
        "candidate": "bolted-kerf-right-diagnostic-proxy",
        "parameters": {
            "hold": hold,
            "pounds": 250,
            "force_xyz_n": force,
            "standoff_from_front_mm": 100,
        },
        "diagnostic_scope": scope,
        "numerically_accepted": accepted,
        "contact_active_set_converged": accepted,
        "global_equilibrium_passed": accepted,
        "member_equilibrium_passed": accepted,
        "mpc_check_passed": accepted,
        "contact_cycles": [{"directory": "cycle-02", "contact_passed": accepted}],
        "termination": "converged" if accepted else "repeated",
        "source_sha256": snapshots,
        "artifact_sha256": {
            "cycle-02/input.json": hashlib.sha256(record_path.read_bytes()).hexdigest(),
            "diagnostic-scope.json": hashlib.sha256(
                scope_path.read_bytes()
            ).hexdigest(),
            **{f"source_snapshots/{source}": digest for source, digest in snapshots.items()},
        },
    }
    (folder / "report.json").write_text(json.dumps(report))
    return folder


@pytest.mark.parametrize(
    "case",
    ("a1-rear", "a12-left", "a12-rear", "k12-rear", "k12-right"),
)
def test_accepted_reference_preserves_archived_identity(case):
    manifest = json.loads(REFERENCE_MANIFEST.read_text())
    reference = next(
        row for row in manifest["accepted_default_v2"] if row["case"] == case
    )
    source = reference["source"]
    report_path = Path(source["report"])
    record_path = Path(source["record"])
    report = json.loads(report_path.read_text())

    assert hashlib.sha256(report_path.read_bytes()).hexdigest() == source[
        "report_sha256"
    ]
    assert hashlib.sha256(record_path.read_bytes()).hexdigest() == source[
        "record_sha256"
    ]

    record_relative = record_path.relative_to(report_path.parent).as_posix()
    assert report["artifact_sha256"][record_relative] == source["record_sha256"]
    assert (
        report["source_sha256"]["fea/current_response_model.py"]
        == ARCHIVED_MODEL_SHA256
    )


def test_accepted_uses_final_record_and_both_center_sides(tmp_path, monkeypatch):
    folder = make_case(tmp_path, "proxy-default-v2", "a1-rear", True)
    calls = []

    def fake_extract(report_path, record_path, principal, post):
        calls.append((report_path, record_path, principal, post))
        return {
            "interfaces": {
                "principal_header": {"on_center_member": {"force_xyz_n": [1, 2, 3]}},
                "post_header": {"on_center_member": {"force_xyz_n": [4, 5, 6]}},
            },
            "header_free_body": {
                "selected_interfaces": {
                    "connection_names": ["a", "b"],
                    "wrench": {"force_xyz_n": [1, 0, 0]},
                },
                "other_attachments": {
                    "connection_names": ["other"],
                    "wrench": {"force_xyz_n": [2, 0, 0]},
                },
                "residual": {"passed": True},
            },
            "status": {"convergence": "passed"},
        }

    monkeypatch.setattr(packet, "extract_files", fake_extract)
    row = packet.case_row(tmp_path, "proxy-default-v2", "a1-rear")
    assert calls == [
        (
            folder / "report.json",
            folder / "cycle-02" / "input.json",
            "base_principal_center_left",
            "base_post_center_left",
        ),
        (
            folder / "report.json",
            folder / "cycle-02" / "input.json",
            "base_principal_center_right",
            "base_post_center_right",
        ),
    ]
    assert (
        row["source"]["report_sha256"]
        == hashlib.sha256((folder / "report.json").read_bytes()).hexdigest()
    )
    assert (
        row["source"]["record_sha256"]
        == hashlib.sha256((folder / "cycle-02" / "input.json").read_bytes()).hexdigest()
    )
    assert row["source"]["producer_source_sha256"]["scripts/clear_space_batch.py"]
    assert row["sides"]["left"]["interfaces"]["principal_header"]["on_center_member"][
        "force_xyz_n"
    ] == [1, 2, 3]
    header = row["sides"]["right"]["header_free_body"]
    assert header["other_attachments"] == {
        "connection_count": 1,
        "wrench": {"force_xyz_n": [2, 0, 0]},
    }
    assert header["selected_interfaces"]["connection_count"] == 2
    assert "connection_names" not in json.dumps(header)


def test_failed_case_carries_no_forces_or_demand(tmp_path, monkeypatch):
    make_case(tmp_path, "proxy-default-v2", "a12-forward", False)
    monkeypatch.setattr(
        packet, "extract_files", lambda *args: pytest.fail("must not extract")
    )
    row = packet.case_row(tmp_path, "proxy-default-v2", "a12-forward")
    assert row["status"] == "nonconverged"
    assert "sides" not in row
    assert "forces" not in json.dumps(row).lower()


@pytest.mark.parametrize(
    "target,key,value",
    [
        ("report", "candidate", "unrelated"),
        ("record", "provisional_structural_connectors", "other proxy"),
        ("report", "diagnostic_scope", {"case": "a12-forward"}),
        (
            "report",
            "parameters",
            {
                "hold": "A12",
                "pounds": 250,
                "force_xyz_n": [0, 300, -2224.11080763025],
                "standoff_from_front_mm": 100,
            },
        ),
    ],
)
def test_failed_case_rejects_mismatched_identity(
    tmp_path, monkeypatch, target, key, value
):
    folder = make_case(tmp_path, "proxy-default-v2", "a12-forward", False)
    path = folder / ("report.json" if target == "report" else "cycle-02/input.json")
    data = json.loads(path.read_text())
    data[key] = value
    path.write_text(json.dumps(data))
    if target == "record":
        report_path = folder / "report.json"
        report = json.loads(report_path.read_text())
        report["artifact_sha256"]["cycle-02/input.json"] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        report_path.write_text(json.dumps(report))
    monkeypatch.setattr(
        packet, "extract_files", lambda *args: pytest.fail("must not extract")
    )
    with pytest.raises(ValueError):
        packet.case_row(tmp_path, "proxy-default-v2", "a12-forward")


def test_failed_case_rejects_scope_sidecar_digest(tmp_path):
    folder = make_case(tmp_path, "proxy-default-v2", "a12-forward", False)
    (folder / "diagnostic-scope.json").write_text("{}")
    with pytest.raises(ValueError, match="Diagnostic scope"):
        packet.case_row(tmp_path, "proxy-default-v2", "a12-forward")


def test_failed_case_rejects_source_snapshot_digest(tmp_path):
    folder = make_case(tmp_path, "proxy-default-v2", "a12-forward", False)
    (folder / "source_snapshots" / "scripts/clear_space_batch.py").write_text("changed")
    with pytest.raises(ValueError, match="Producer source snapshot"):
        packet.case_row(tmp_path, "proxy-default-v2", "a12-forward")


def test_inconsistent_acceptance_is_rejected(tmp_path, monkeypatch):
    folder = make_case(tmp_path, "proxy-default-v2", "a1-rear", True)
    report_path = folder / "report.json"
    report = json.loads(report_path.read_text())
    report["contact_cycles"][-1]["contact_passed"] = False
    report_path.write_text(json.dumps(report))
    monkeypatch.setattr(
        packet, "extract_files", lambda *args: pytest.fail("must not extract")
    )
    with pytest.raises(ValueError, match="Inconsistent acceptance"):
        packet.case_row(tmp_path, "proxy-default-v2", "a1-rear")


def test_packet_rejects_forward_run_promoted_to_accepted(monkeypatch, tmp_path):
    def fake_row(root, series, case):
        return {"status": "accepted_proxy_reference", "case": case}

    monkeypatch.setattr(packet, "case_row", fake_row)
    with pytest.raises(ValueError, match="Expected nonconverged"):
        packet.build_packet(tmp_path)
