"""Synthetic grain/area and stub-admission bridge seams, not a body proof."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

SOURCE = Path(__file__).with_name("component_reductions.py")
SPEC = importlib.util.spec_from_file_location("complete_contact_component_fixture", SOURCE)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def face_fixture():
    identity = {"state_id": "synthetic", "case_id": "synthetic", "accessory_placement": "synthetic"}
    rows, members = [], []
    directions = ([1., 0., 0.], [0., 0., 1.], [0., np.sin(np.deg2rad(40.)), np.cos(np.deg2rad(40.))])
    for pair in range(30):
        a, b = f"a{pair}", f"b{pair}"
        members.extend([{"member": a, "grain_axis_xyz": [1., 0., 0.]},
                        {"member": b, "grain_axis_xyz": directions[pair % 3]}])
        for index in range(20 if pair < 29 else 4):
            area = index + 2.
            pressure = 2. if index == 0 else 0. if index == 1 else 1.
            rows.append({**identity, "id": f"pair{pair}/cell{index}", "kind": "timber_face_contact",
                "first": a, "second": b, "point_xyz_mm": [float(pair), float(index), 0.],
                "direction_xyz": [0., 0., 1.], "cell_area_mm2": area, "compression_n": pressure * area})
    return {**identity, "contact_actions": rows, "timber_face_contact_actions": copy.deepcopy(rows)}, {
        "finished_member_sections": members}


def test_584_reference_cells_preserve_zero_and_both_own_grain_classes_without_allowables():
    field, full = face_fixture()
    rows = helper.face_diagnostics(field, full)
    assert len(rows) == 30
    assert sum(r["cells_including_zeros"] for r in rows) == 584
    assert sum(r["loaded_cells"] for r in rows) == 554
    for index, row in enumerate(rows):
        witness = row["governing_discrete_reference_area_pressure_witness"]
        assert witness["compression_n"] == 4.
        assert witness["reference_cell_area_mm2"] == 2.
        assert witness["normal_force_over_reference_cell_area_mpa"] == 2.
        a, b = witness["own_host_grain_geometry"]
        assert a["reference_grain_classification"] == "perpendicular"
        assert b["reference_grain_classification"] == ("perpendicular", "parallel", "oblique")[index % 3]
        assert b["acute_normal_to_reference_grain_degrees"] == pytest.approx((90., 0., 40.)[index % 3])
        assert all(r["allowable_pressure_mpa"] is None and r["adjusted_bearing_resistance_or_ratio"] is None
                   for r in (a, b))
        assert row["own_host_material_allowables_or_joint_capacity"] is None


@pytest.mark.parametrize("change", ["old272", "duplicate", "alias", "identity", "grain", "normal"])
def test_wrong_face_census_identity_or_geometry_rejected(change):
    field, full = face_fixture()
    if change == "old272":
        field["contact_actions"] = field["contact_actions"][:272]
        field["timber_face_contact_actions"] = copy.deepcopy(field["contact_actions"])
    elif change == "duplicate":
        field["contact_actions"][-1] = copy.deepcopy(field["contact_actions"][0])
    elif change == "alias":
        field["timber_face_contact_actions"][0]["compression_n"] = 7.
    elif change == "grain":
        full["finished_member_sections"][0]["grain_axis_xyz"] = [2., 0., 0.]
    else:
        field["contact_actions"][0]["case_id" if change == "identity" else "direction_xyz"] = "other" if change == "identity" else [0., 0., 2.]
        field["timber_face_contact_actions"] = copy.deepcopy(field["contact_actions"])
    with pytest.raises(ValueError):
        helper.face_diagnostics(field, full)


def seam_fixture(tmp_path, monkeypatch):
    """Stub validates byte forwarding only; no production equilibrium claim."""
    gate = tmp_path / "admission.py"
    gate.write_text("synthetic source hash, not a production gate")
    gate_sha = hashlib.sha256(gate.read_bytes()).hexdigest()
    own = tmp_path / "component_reductions.py"
    own.write_text("synthetic source identity only")
    pure_source = tmp_path / "frozen_pure_source.py"
    pure_source.write_text("synthetic source identity only; pure functions remain unchanged")
    monkeypatch.setattr(helper, "ROOT", tmp_path)
    monkeypatch.setattr(helper, "OWN", own)
    monkeypatch.setattr(helper, "LOADED_SHA", hashlib.sha256(own.read_bytes()).hexdigest())
    monkeypatch.setattr(helper, "GATE", gate)
    monkeypatch.setattr(helper.pure, "__file__", str(pure_source))
    field = {"linear_timber_face_method": helper.METHOD,
        "state_id": "stub", "case_id": "stub", "accessory_placement": "stub", "source_sha256": {}}
    payload = json.dumps(field).encode()
    path = tmp_path / "field.json"
    path.write_bytes(payload)
    receipt = {"stub_receipt_only": True, "source_sha256": {"admission.py": gate_sha}}
    events = []

    def validate(received, admitted, *, admission_sha256):
        assert isinstance(received, bytes) and received == payload
        assert admitted is receipt and admission_sha256 == gate_sha
        events.append(("new_validator", received))
        return json.loads(received), {"admission.py": gate_sha}

    monkeypatch.setattr(helper, "_load_gate", lambda expected: SimpleNamespace(require_admitted_payload=validate))
    monkeypatch.setattr(helper.pure, "verify_pins", lambda pins: events.append(("source_guard", dict(pins))))

    def reduce(demand, *, samples, caller_sections):
        events.append(("pure_reduction_stub", demand, samples, caller_sections))
        return {"unchanged_pure_dispatch_stub": True}, {}

    monkeypatch.setattr(helper, "_reduce", reduce)
    return path, payload, receipt, gate_sha, events, gate


def test_same_bytes_receipt_and_caller_forwarded_without_legacy_or_constant_patch(tmp_path, monkeypatch):
    path, payload, receipt, digest, events, _ = seam_fixture(tmp_path, monkeypatch)
    old_constants = helper.pure.GATE, helper.pure.ADMISSION_SCHEMA, helper.pure.ADMISSION_SUCCESS
    method_ids = tuple(id(getattr(helper.pure, name)) for name in ("panel_reductions", "flange_torsion_reductions"))
    monkeypatch.setattr(helper.pure, "require_admission", lambda *a, **k: pytest.fail("legacy admission called"))
    monkeypatch.setattr(helper.pure, "face_reference_summaries", lambda *a, **k: pytest.fail("old272 formatter called"))
    caller = {"explicit_unadopted_root_scenario": []}
    result = helper.consume(path, receipt, expected_field_sha256=hashlib.sha256(payload).hexdigest(),
                            admission_sha256=digest, samples=7, caller_sections=caller)
    assert result["independent_complete_timber_admission"] is receipt
    assert result["field_sha256"] == hashlib.sha256(payload).hexdigest()
    assert next(r for r in events if r[0] == "pure_reduction_stub")[2:] == (7, caller)
    assert old_constants == (helper.pure.GATE, helper.pure.ADMISSION_SCHEMA, helper.pure.ADMISSION_SUCCESS)
    assert method_ids == tuple(id(getattr(helper.pure, name)) for name in ("panel_reductions", "flange_torsion_reductions"))
    assert result["complete_joint_resistance"] is None and result["complete_joint_acceptance"] is False
    assert not any(result["release"].values())


@pytest.mark.parametrize("change", ["field", "receipt", "caller", "parsed", "gate"])
def test_after_read_or_input_mutation_rejected(tmp_path, monkeypatch, change):
    path, payload, receipt, digest, _, gate = seam_fixture(tmp_path, monkeypatch)
    caller = {}

    def mutate(demand, **kwargs):
        if change == "field":
            path.write_bytes(payload + b" ")
        elif change == "receipt":
            receipt["changed"] = True
        elif change == "caller":
            caller["changed"] = True
        elif change == "parsed":
            demand["changed"] = True
        else:
            gate.write_text("changed source")
        return {}, {}

    monkeypatch.setattr(helper, "_reduce", mutate)
    with pytest.raises(ValueError, match="changed"):
        helper.consume(path, receipt, expected_field_sha256=hashlib.sha256(payload).hexdigest(),
                       admission_sha256=digest, caller_sections=caller)


def test_wrong_released_hash_stops_before_gate_or_reduction(tmp_path, monkeypatch):
    path, _, receipt, digest, events, _ = seam_fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="raw byte hash"):
        helper.consume(path, receipt, expected_field_sha256="0" * 64, admission_sha256=digest)
    assert events == []


def test_new_gate_source_hash_is_mandatory_before_import(tmp_path, monkeypatch):
    gate = tmp_path / "admission.py"
    gate.write_text("raise AssertionError('must not be imported')")
    monkeypatch.setattr(helper, "GATE", gate)
    for digest in (None, "invalid", "0" * 64):
        with pytest.raises(ValueError, match="gate SHA"):
            helper._load_gate(digest)
