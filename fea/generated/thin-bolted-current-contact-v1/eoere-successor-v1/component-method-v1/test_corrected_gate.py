"""Bounded path/dispatch/source fixtures, no fabricated candidate admission."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location("eoere_corrected_gate_test", Path(__file__).with_name("corrected_gate.py"))
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)


def test_exact_original_file_identity_and_exception_restoration():
    original = method.base.GATE
    assert method.base.__file__ == str(method.BASE)
    assert method.sha(method.BASE) == method.BASE_SHA
    with pytest.raises(RuntimeError), method.gate_context():
        assert method.base.GATE == method.GATE
        assert method.base.__file__ == str(method.BASE)
        raise RuntimeError("synthetic failure")
    assert method.base.GATE == original


def test_genuine_frozen_consume_reaches_corrected_cheap_gate_before_reduction(tmp_path, monkeypatch):
    path, receipt = tmp_path/"toy-field.json", tmp_path/"toy-receipt.json"
    path.write_text("{}")
    receipt.write_text(json.dumps({"schema": method.base.ADMISSION_SCHEMA, method.base.SUCCESS: True}))
    calls = []
    original = method.base.GATE

    def reject(payload, record, *, admission_sha256):
        calls.append((payload, record, admission_sha256))
        raise ValueError("synthetic cheap gate rejection")

    def loader(actual_path, digest, name):
        assert actual_path == method.GATE and digest == "synthetic-gate-sha"
        return SimpleNamespace(require_admitted_payload=reject)

    monkeypatch.setattr(method.base, "verify", lambda pins: None)
    monkeypatch.setattr(method.base, "load", loader)
    with pytest.raises(ValueError, match="synthetic cheap gate rejection"):
        method.consume(path, receipt, expected_field_sha256=method.sha(path),
                       admission_sha256="synthetic-gate-sha", steel_sha256="unused")
    assert calls[0][0] == b"{}" and method.base.GATE == original


def test_unmodified_forwarding_adds_explicit_source_context(monkeypatch):
    calls = []
    original = method.base.GATE
    monkeypatch.setattr(method.base, "verify", lambda pins: None)

    def frozen(field, receipt, **kwargs):
        calls.append((field, receipt, kwargs))
        assert method.base.GATE == method.GATE
        return {"fresh_gate_sha256": "gate", "raw_field_sha256": "raw",
                "source_sha256": {str(method.GATE.relative_to(method.base.ROOT)): "gate"}}

    monkeypatch.setattr(method, "FROZEN_CONSUME", frozen)
    result = method.consume("field", "receipt", expected_field_sha256="raw", admission_sha256="gate",
                            steel_sha256="steel", samples=7)
    assert calls == [("field", "receipt", {"expected_field_sha256": "raw", "admission_sha256": "gate",
                                          "steel_sha256": "steel", "samples": 7})]
    assert result["consumer_gate_path_adapter"]["component_algorithms_changed"] is False
    assert result["source_sha256"][str(method.OWN.relative_to(method.base.ROOT))] == method.LOADED_SHA
    assert method.base.GATE == original


def test_wrong_gate_result_cannot_be_relabelled(monkeypatch):
    monkeypatch.setattr(method.base, "verify", lambda pins: None)
    monkeypatch.setattr(method, "FROZEN_CONSUME", lambda *args, **kwargs: {
        "fresh_gate_sha256": "old", "raw_field_sha256": "raw", "source_sha256": {}})
    with pytest.raises(ValueError, match="actual corrected gate"):
        method.consume("field", "receipt", expected_field_sha256="raw", admission_sha256="new", steel_sha256="s")


def test_genuine_cli_parser_preserves_actual_command_and_restores_dispatch(tmp_path, monkeypatch):
    out = tmp_path/"receipt.json"
    argv = [str(method.OWN), "--field", "new-field", "--receipt", "new-receipt", "--out", str(out),
            "--expected-field-sha256", "raw", "--admission-sha256", "gate", "--steel-sha256", "steel"]
    actual = ["python", "-B", *argv]
    monkeypatch.setattr(method.base.sys, "argv", argv)
    monkeypatch.setattr(method.base.sys, "orig_argv", actual)
    old = method.base.consume
    monkeypatch.setattr(method, "consume", lambda *args, **kwargs: {"state_id": "SYNTHETIC-CLI-ONLY"})
    method.main()
    assert json.loads(out.read_text())["execution"]["sys_orig_argv"] == actual
    assert method.base.consume is old and method.base.__file__ == str(method.BASE)


def test_source_change_is_rejected_without_new_gate_import(monkeypatch):
    genuine = method.sha
    monkeypatch.setattr(method, "sha", lambda path: "changed" if Path(path) == method.BASE else genuine(path))
    # source_pins uses the base verifier; independently mutate its SHA reader.
    monkeypatch.setattr(method.base, "sha", method.sha)
    with pytest.raises(ValueError, match="component source differs"):
        method.source_pins()
