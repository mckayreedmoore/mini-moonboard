"""Distinct admission and direct-wood routing fixtures; frozen methods reused."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_thin_bolted_finite_steel_consumer import fixture as base_fixture
from test_thin_bolted_finite_steel_recovery import fixture as shaft_fixture
from test_thin_bolted_finite_steel_recovery import port_fixture, pose

from scripts import thin_bolted_timber_contact_steel_checks as writer


def fixture(tmp_path, monkeypatch):
    source, _, _, values = base_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(writer, "ROOT", tmp_path)
    (tmp_path/writer.BASE_SOURCE).write_bytes(Path(writer.base.__file__).read_bytes())
    receipt = tmp_path/"base-receipt.json"
    receipt.write_bytes(writer.BASE_RECEIPT.read_bytes())
    monkeypatch.setattr(writer, "BASE_RECEIPT", receipt)
    gate = tmp_path/writer.ADMISSION_SOURCE
    gate.write_text("reviewed new timber-contact admission")
    field = json.loads(source.read_bytes())
    field["finite_interaction_actions"] = [{**writer.base.recovery.state_fields(field), "id": "wood-direct",
        "kind": "timber_face_contact", "first": "timber-one", "second": "timber-two"}]
    source.write_text(json.dumps(field))
    seen = []
    def audit(payload):
        assert isinstance(payload, bytes)
        seen.append(payload)
        field = json.loads(payload)
        return {"schema": writer.ADMISSION_SCHEMA, writer.ADMISSION_KEY: True, **writer.base.recovery.state_fields(field),
            "field_sha256": writer.hashlib.sha256(payload).hexdigest(), "field_canonical_sha256": writer.base.canonical_sha(field),
            "source_sha256": {**field["source_sha256"], writer.ADMISSION_SOURCE: writer.base.digest(gate)}}
    module = SimpleNamespace(__file__=str(gate), LOADED_PRODUCER_SHA256=writer.base.digest(gate), audit_timber_contact_state=audit)
    def load(name):
        assert name == writer.ADMISSION_MODULE
        return module
    monkeypatch.setattr(writer.importlib, "import_module", load)
    return source, gate, module, values, seen


def test_new_gate_receives_original_bytes_and_only_steel_recovery_is_reused(tmp_path, monkeypatch):
    source, gate, _, values, seen = fixture(tmp_path, monkeypatch)
    received = []
    def recover(field, q, *_args, **_kwargs):
        received.append((q, field["finite_interaction_actions"][0]["kind"]))
        return copy.deepcopy(values)
    monkeypatch.setattr(writer.base.recovery, "recover_current_actions", recover)
    report = writer.consume(source, admission_sha256=writer.base.digest(gate))
    assert seen == [source.read_bytes()]
    assert received == [([2.], "timber_face_contact")]
    assert report["admitted_direct_timber_face_contact_count"] == 1
    assert report["direct_timber_face_contacts_routed_into_steel_or_shaft_loads"] is False
    assert report["actual_own_washer_face_pressure_feasibility"] is None
    assert report["structural_acceptance"] is False
    assert report["source_sha256"][writer.BASE_SOURCE] == writer.BASE_SHA


def test_old_receipt_cannot_admit_direct_timber_contact_field(tmp_path, monkeypatch):
    source, gate, module, _, _ = fixture(tmp_path, monkeypatch)
    module.audit_timber_contact_state = lambda _: {"schema": writer.base.ADMISSION_SCHEMA, writer.base.ADMISSION_KEY: True}
    calls = []
    monkeypatch.setattr(writer.base, "geometry_inputs", lambda: calls.append(True))
    with pytest.raises(ValueError, match="new timber-contact admission"):
        writer.consume(source, admission_sha256=writer.base.digest(gate))
    assert calls == []


@pytest.mark.parametrize("mutation", ["digest", "state", "bytes", "source"])
def test_wrong_new_gate_or_receipt_binding_rejects_before_recovery(tmp_path, monkeypatch, mutation):
    source, gate, module, _, _ = fixture(tmp_path, monkeypatch)
    original = module.audit_timber_contact_state
    def altered(payload):
        receipt = original(payload)
        if mutation == "state":
            receipt["state_id"] = "other"
        elif mutation == "bytes":
            receipt["field_sha256"] = "0"*64
        else:
            receipt["source_sha256"].pop(writer.ADMISSION_SOURCE)
        return receipt
    module.audit_timber_contact_state = altered
    calls = []
    monkeypatch.setattr(writer.base, "geometry_inputs", lambda: calls.append(True))
    with pytest.raises(ValueError):
        writer.consume(source, admission_sha256="0"*64 if mutation == "digest" else writer.base.digest(gate))
    assert calls == []


def test_direct_wood_contact_never_enters_actual_frozen_shaft_or_steel_reductions():
    recovery = writer.base.recovery
    shaft, specs = shaft_fixture(True)
    ports, layout = port_fixture()
    cuts_before = recovery.current_shaft_cuts(shaft, [0.], specs, pose=pose)
    ports_before = recovery.current_steel_ports(ports, [], layout, pose=pose)
    flanges_before = recovery.current_flange_sections(ports, [], layout, ports_before, pose=pose)
    direct = {**recovery.state_fields(shaft), "id": "wood-direct", "kind": "timber_face_contact",
        "first": "wood-one", "second": "wood-two", "force_on_first_xyz_n": [1e8, -2e8, 3e8],
        "moment_on_first_at_current_point_xyz_nmm": [4e9, 5e9, -6e9]}
    shaft["finite_interaction_actions"].append(direct)
    ports["finite_interaction_actions"].append(direct)
    assert recovery.current_shaft_cuts(shaft, [0.], specs, pose=pose) == cuts_before
    assert recovery.current_steel_ports(ports, [], layout, pose=pose) == ports_before
    assert recovery.current_flange_sections(ports, [], layout, ports_before, pose=pose) == flanges_before
    assert recovery.current_own_washer_captures(shaft) == []


def test_changed_direct_contact_field_after_admission_rejects_issue(tmp_path, monkeypatch):
    source, gate, _, values, _ = fixture(tmp_path, monkeypatch)
    def changed(*_args, **_kwargs):
        source.write_text("changed after current admission")
        return copy.deepcopy(values)
    monkeypatch.setattr(writer.base.recovery, "recover_current_actions", changed)
    with pytest.raises(ValueError, match="changed"):
        writer.consume(source, admission_sha256=writer.base.digest(gate))
