"""Current admission/source/census guards without a frame or CAD solve."""

import copy
import json
from types import SimpleNamespace

import pytest

from scripts import thin_bolted_finite_steel_consumer as writer

STATE = {"state_id": "finite-one", "case_id": "a12", "accessory_placement": "rear"}


def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(writer, "ROOT", tmp_path)
    gate = tmp_path/writer.ADMISSION_SOURCE
    gate.parent.mkdir()
    gate.write_text("reviewed current-state audit source")
    finite = tmp_path/"scripts/thin_bolted_finite_frame.py"
    finite.write_text("frozen current map reader")
    monkeypatch.setattr(writer.recovery, "FINITE_SHA", writer.digest(finite))
    recovery = tmp_path/writer.RECOVERY_SOURCE
    recovery.write_text("frozen current recovery source")
    monkeypatch.setattr(writer, "RECOVERY_SHA", writer.digest(recovery))
    method = tmp_path/"method.json"
    method.write_text("frozen current recovery method receipt")
    monkeypatch.setattr(writer, "METHOD_RECEIPT", method)
    monkeypatch.setattr(writer, "METHOD_RECEIPT_SHA", writer.digest(method))
    dependency_pins = {writer.RECOVERY_SOURCE: writer.digest(recovery),
                       "scripts/thin_bolted_finite_frame.py": writer.digest(finite)}
    monkeypatch.setattr(writer.recovery, "source_pins", lambda: dependency_pins.copy())
    field = {"schema": writer.FIELD_SCHEMA, "candidate": "thin", **STATE, "parameters": {}, "release": {"climbing": False},
             "response": {"q": [2.]}, "source_sha256": dependency_pins.copy()}
    source = tmp_path/"field.json"
    source.write_text(json.dumps(field))
    def audit(path):
        current = json.loads(path.read_bytes())
        return {"schema": writer.ADMISSION_SCHEMA, **writer.recovery.state_fields(current), writer.ADMISSION_KEY: True,
            "field_sha256": writer.digest(path), "field_canonical_sha256": writer.canonical_sha(current),
            "source_sha256": {**dependency_pins, writer.ADMISSION_SOURCE: writer.digest(gate)}}
    module = SimpleNamespace(__file__=str(gate), LOADED_PRODUCER_SHA256=writer.digest(gate), audit_finite_state=audit)
    def load(name):
        assert name == writer.ADMISSION_MODULE
        return module
    monkeypatch.setattr(writer.importlib, "import_module", load)
    monkeypatch.setattr(writer, "geometry_inputs", lambda: ({}, []))
    values = {**STATE, "source_sha256": dependency_pins.copy(),
        "current_shaft_section_cut_actions": [{} for _ in range(70)], "current_steel_port_actions": [{} for _ in range(72)],
        "current_flange_section_actions": [{} for _ in range(72)], "current_shaft_circle_references": [{} for _ in range(70)],
        "current_own_washer_capture_actions": [{} for _ in range(140)], "own_metal_role_gravity_count": 350}
    monkeypatch.setattr(writer.recovery, "recover_current_actions", lambda *_args, **_kwargs: copy.deepcopy(values))
    return source, gate, module, values


@pytest.mark.parametrize("value", [None, "", "0"*63, "g"*64, "A"*64, "0"*64])
def test_reviewed_gate_digest_required_before_import_or_recovery(tmp_path, monkeypatch, value):
    source, _, _, _ = fixture(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(writer.importlib, "import_module", lambda *_: calls.append("import"))
    monkeypatch.setattr(writer.recovery, "recover_current_actions", lambda *_args, **_kwargs: calls.append("recovery"))
    with pytest.raises(ValueError, match="admission"):
        writer.consume(source, admission_sha256=value)
    assert calls == []


@pytest.mark.parametrize("mutation", ["false", "schema", "state", "case", "placement", "bytes", "canonical", "gate", "map"])
def test_inconsistent_current_admission_receipt_prevents_recovery(tmp_path, monkeypatch, mutation):
    source, gate, module, _ = fixture(tmp_path, monkeypatch)
    original = module.audit_finite_state
    def mutated(path):
        receipt = original(path)
        if mutation == "false":
            receipt[writer.ADMISSION_KEY] = False
        elif mutation == "schema":
            receipt["schema"] = "old_reference_admission"
        elif mutation in ("state", "case", "placement"):
            receipt[{"state": "state_id", "case": "case_id", "placement": "accessory_placement"}[mutation]] = "other"
        elif mutation in ("bytes", "canonical"):
            receipt["field_sha256" if mutation == "bytes" else "field_canonical_sha256"] = "0"*64
        elif mutation == "gate":
            receipt["source_sha256"].pop(writer.ADMISSION_SOURCE)
        else:
            receipt["source_sha256"]["scripts/thin_bolted_finite_frame.py"] = "0"*64
        return receipt
    module.audit_finite_state = mutated
    calls = []
    monkeypatch.setattr(writer.recovery, "recover_current_actions", lambda *_args, **_kwargs: calls.append(True))
    with pytest.raises(ValueError, match="admission"):
        writer.consume(source, admission_sha256=writer.digest(gate))
    assert calls == []


def test_wrong_loaded_audit_code_rejects_even_when_file_digest_matches(tmp_path, monkeypatch):
    source, gate, module, _ = fixture(tmp_path, monkeypatch)
    module.LOADED_PRODUCER_SHA256 = "0"*64
    with pytest.raises(ValueError, match="loaded"):
        writer.consume(source, admission_sha256=writer.digest(gate))


def test_bound_current_admission_uses_exact_q_and_preserves_false_release(tmp_path, monkeypatch):
    source, gate, _, values = fixture(tmp_path, monkeypatch)
    received = []
    def recover(field, q, *_args, **_kwargs):
        received.append((field["state_id"], q))
        return copy.deepcopy(values)
    monkeypatch.setattr(writer.recovery, "recover_current_actions", recover)
    report = writer.consume(source, admission_sha256=writer.digest(gate))
    assert received == [(STATE["state_id"], [2.])]
    assert report["source_finite_field_sha256"] == writer.digest(source)
    assert report["source_sha256"][writer.ADMISSION_SOURCE] == writer.digest(gate)
    assert report["old_reference_datum_actions_or_gate_relabelled"] is False
    assert report["structural_acceptance"] is False
    assert report["fabrication_release"] is False
    assert report["climbing_release"] is False


@pytest.mark.parametrize("mutation", ["field", "gate", "caller"])
def test_bound_bytes_changed_during_current_recovery_reject_issuance(tmp_path, monkeypatch, mutation):
    source, gate, _, values = fixture(tmp_path, monkeypatch)
    caller = tmp_path/"sections.json"
    caller.write_text("{}")
    gate_digest = writer.digest(gate)
    def recover(*_args, **_kwargs):
        {"field": source, "gate": gate, "caller": caller}[mutation].write_text("changed source bytes")
        return copy.deepcopy(values)
    monkeypatch.setattr(writer.recovery, "recover_current_actions", recover)
    with pytest.raises(ValueError, match="changed"):
        writer.consume(source, admission_sha256=gate_digest, caller_sections_path=caller)


def test_reference_schema_rejected_before_current_audit(tmp_path, monkeypatch):
    source, gate, module, _ = fixture(tmp_path, monkeypatch)
    field = json.loads(source.read_bytes())
    field["schema"] = "thin_bolted_compatible_reference_response/v1"
    source.write_text(json.dumps(field))
    calls = []
    module.audit_finite_state = lambda *_: calls.append(True)
    with pytest.raises(ValueError, match="new finite"):
        writer.consume(source, admission_sha256=writer.digest(gate))
    assert calls == []


def test_missing_current_own_capture_census_rejects_report(tmp_path, monkeypatch):
    source, gate, _, values = fixture(tmp_path, monkeypatch)
    values["current_own_washer_capture_actions"].pop()
    with pytest.raises(ValueError, match="complete current"):
        writer.consume(source, admission_sha256=writer.digest(gate))
