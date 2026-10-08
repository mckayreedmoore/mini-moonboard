"""Small nested path/identity fixtures; no real candidate field is consumed."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location("eoere_ordered_gate_test", Path(__file__).with_name("ordered_gate.py"))
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)


def identities():
    return (method.reused.__file__, method.base.__file__, method.reused.GATE,
            method.base.GATE, method.reused.consume, method.base.consume)


def test_genuine_nested_frozen_consume_reaches_v3_gate_and_restores_on_error(tmp_path, monkeypatch):
    original = identities()
    payload = tmp_path/"synthetic-field.json"
    receipt = tmp_path/"synthetic-receipt.json"
    payload.write_bytes(b"{}")
    receipt.write_text(json.dumps({"schema": method.base.ADMISSION_SCHEMA, method.base.SUCCESS: True}))
    calls = []

    def reject(raw, record, *, admission_sha256):
        calls.append((raw, admission_sha256))
        raise ValueError("synthetic v3 rejection")

    def loader(path, digest, name):
        assert path == method.GATE and digest == "v3-sha"
        assert method.base.GATE == method.reused.GATE == method.GATE
        assert method.reused.__file__ == str(method.BASE)
        assert method.base.__file__ == str(method.reused.BASE)
        return SimpleNamespace(require_admitted_payload=reject)

    monkeypatch.setattr(method.base, "verify", lambda pins: None)
    monkeypatch.setattr(method.base, "load", loader)
    with pytest.raises(ValueError, match="synthetic v3 rejection"):
        method.consume(payload, receipt, expected_field_sha256=method.base.sha(payload),
                       admission_sha256="v3-sha", steel_sha256="unused")
    assert calls == [(b"{}", "v3-sha")] and identities() == original


def test_forwarded_metadata_binds_both_genuine_layers_and_new_gate(monkeypatch):
    original = identities()
    monkeypatch.setattr(method.base, "verify", lambda pins: None)
    calls = []

    def synthetic_bottom(field, receipt, **kwargs):
        calls.append((field, receipt, kwargs))
        assert method.reused.GATE == method.base.GATE == method.GATE
        return {"fresh_gate_sha256": "v3", "raw_field_sha256": "raw",
                "source_sha256": {str(method.GATE.relative_to(method.base.ROOT)): "v3"}}

    monkeypatch.setattr(method.reused, "FROZEN_CONSUME", synthetic_bottom)
    result = method.consume("F", "R", expected_field_sha256="raw", admission_sha256="v3", steel_sha256="S", samples=5)
    assert calls == [("F", "R", {"expected_field_sha256": "raw", "admission_sha256": "v3",
                                 "steel_sha256": "S", "samples": 5})]
    for key in ("consumer_gate_path_adapter", "consumer_order_gate_path_adapter"):
        assert result[key]["actual_gate_path"] == str(method.GATE.relative_to(method.base.ROOT))
        assert result[key]["actual_gate_sha256"] == "v3"
        assert result[key]["component_algorithms_changed"] is False
    assert result["source_sha256"][str(method.OWN.relative_to(method.base.ROOT))] == method.LOADED_SHA
    assert identities() == original


def test_wrong_gate_result_never_receives_new_outer_provenance(monkeypatch):
    monkeypatch.setattr(method.base, "verify", lambda pins: None)
    monkeypatch.setattr(method, "FROZEN_CONSUME", lambda *args, **kwargs: {
        "fresh_gate_sha256": "old", "raw_field_sha256": "raw", "source_sha256": {}})
    original = identities()
    with pytest.raises(ValueError, match="actual new gate"):
        method.consume("F", "R", expected_field_sha256="raw", admission_sha256="v3", steel_sha256="S")
    assert identities() == original


def test_genuine_nested_main_records_true_outer_argv_and_restores(tmp_path, monkeypatch):
    original = identities()
    out = tmp_path/"synthetic-cli-only.json"
    argv = [str(method.OWN), "--field", "F", "--receipt", "R", "--out", str(out),
            "--expected-field-sha256", "raw", "--admission-sha256", "v3", "--steel-sha256", "S"]
    actual = ["python", "-B", *argv]
    monkeypatch.setattr(method.base.sys, "argv", argv)
    monkeypatch.setattr(method.base.sys, "orig_argv", actual)
    monkeypatch.setattr(method, "consume", lambda *args, **kwargs: {"state_id": "SYNTHETIC-CLI-ONLY"})
    method.main()
    assert json.loads(out.read_text())["execution"]["sys_orig_argv"] == actual
    assert identities() == original


def test_outer_source_mutation_rejects_before_consumption(monkeypatch):
    monkeypatch.setattr(method, "LOADED_SHA", "changed")
    with pytest.raises(ValueError, match="component source differs"):
        method.source_pins()
