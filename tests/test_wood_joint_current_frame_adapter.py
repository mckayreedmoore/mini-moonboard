import hashlib
import json
from pathlib import Path

import pytest

from fea.wood_joint_current_frame_adapter import (
    ATTEMPT_REL,
    AdapterError,
    audit_current_frame,
    validate_body_id_set,
    validate_load_contract,
    validate_mass_identity_rows,
    verify_file_pin,
)

ROOT = Path(__file__).resolve().parents[1]


def _mass_row(name: str, entity_id: str) -> dict:
    return {
        "inventory_name": name,
        "group": "test",
        "mass_kg": 1.0,
        "mass_center_global_xyz_mm": [0.0, 0.0, 0.0],
        "gravity_force_global_xyz_n": [0.0, 0.0, -9.80665],
        "gravity_moment_about_global_origin_nmm": [0.0, 0.0, 0.0],
        "source_mass_entity": {"id": entity_id, "kind": "test_role"},
    }


def _centroid_row(name: str) -> dict:
    row = _mass_row(name, f"source/{name}")
    return {
        "name": row["inventory_name"],
        "group": row["group"],
        "mass_kg": row["mass_kg"],
        "mass_center_global_xyz_mm": row["mass_center_global_xyz_mm"],
        "gravity_force_global_xyz_n": row["gravity_force_global_xyz_n"],
        "gravity_moment_about_global_origin_nmm": row[
            "gravity_moment_about_global_origin_nmm"
        ],
    }


def test_pinned_source_hash_detects_tampered_bytes(tmp_path):
    source = tmp_path / "source.json"
    frozen_bytes = b'{"frozen":true}\n'
    source.write_bytes(frozen_bytes)
    pin = {
        "path": "source.json",
        "sha256": hashlib.sha256(frozen_bytes).hexdigest(),
    }
    assert verify_file_pin(tmp_path, pin) == pin["sha256"]
    source.write_bytes(b'{"frozen":false}\n')

    with pytest.raises(AdapterError, match="source hash mismatch"):
        verify_file_pin(tmp_path, pin)


@pytest.mark.parametrize(
    ("observed", "expected", "message"),
    [
        (["body-a", "body-a"], ["body-a", "body-b"], "duplicate body mapping IDs"),
        (["body-a", "body-x"], ["body-a", "body-b"], "unknown="),
    ],
)
def test_body_mapping_rejects_duplicate_or_unknown_identity(
    observed, expected, message
):
    with pytest.raises(AdapterError, match=message):
        validate_body_id_set(observed, expected)


def test_mass_join_rejects_lost_source_role():
    rows = [_mass_row("mass-a", "role/a")]
    centroids = [_centroid_row("mass-a"), _centroid_row("mass-b")]

    with pytest.raises(AdapterError, match="mass inventory name mismatch"):
        validate_mass_identity_rows(
            rows, centroids, expected_kind_counts={"test_role": 2}
        )


def test_mass_join_rejects_doubled_source_role():
    rows = [_mass_row("mass-a", "role/a"), _mass_row("mass-b", "role/a")]
    centroids = [_centroid_row("mass-a"), _centroid_row("mass-b")]

    with pytest.raises(AdapterError, match="mass source role is duplicated"):
        validate_mass_identity_rows(
            rows, centroids, expected_kind_counts={"test_role": 2}
        )


def test_load_wrench_reference_must_match_panel_datum():
    base = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    loads = json.loads((base / "current-load-cases.json").read_text(encoding="utf-8"))
    datums = json.loads((base / "current-load-datums.json").read_text(encoding="utf-8"))
    loads["cases"][0]["applied_wrench"]["reference_point_global_xyz_mm"][0] += 1.0

    with pytest.raises(
        AdapterError, match="wrench reference point does not match the panel datum"
    ):
        validate_load_contract(loads, datums)


def test_current_attempt_audits_source_joins_but_keeps_materials_and_gates_open():
    pins_path = ROOT / ATTEMPT_REL / "source-pins.json"
    pins = json.loads(pins_path.read_text(encoding="utf-8"))
    audit, contract = audit_current_frame(ROOT, pins)

    assert audit["result"] == "source_audit_passed_readiness_blocked"
    assert audit["verified_counts"]["step_bodies"] == 50
    assert audit["verified_counts"]["mass_inventory_rows"] == 778
    assert audit["verified_counts"]["load_cases"] == 6
    assert audit["checks"]["body_to_mass_topology_identity"] == "PASS"
    assert audit["readiness"]["inputs_ready"] is False
    assert audit["readiness"]["launch_ready"] is False
    assert audit["readiness"]["criterion_resolved"] is False
    assert all(
        value is False
        for value in audit["readiness"].values()
        if isinstance(value, bool)
    )

    assert len(contract["body_bindings"]) == 50
    assert all(
        binding["solver_body_id"] is None for binding in contract["body_bindings"]
    )
    assert all(
        binding["solver_material_id"] is None for binding in contract["body_bindings"]
    )
    assert len(contract["mass_bindings"]) == 778
    assert all(
        binding["solver_dof_id"] is None for binding in contract["mass_bindings"]
    )
    assert all(case["solver_load_id"] is None for case in contract["load_cases"])
    assert all(value is None for value in contract["material_assignments"].values())
