"""Small source/path/receipt seams; stubs do not establish body admission."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).with_name("component_reductions.py")
SPEC = importlib.util.spec_from_file_location("observer_isolation_component_coupon", PATH)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def test_real_source_paths_and_only_gate_scope_restore_on_success(monkeypatch):
    receipt = {"explicit_stub_receipt_not_body_admission": True}
    caller = {"explicit_unadopted_circle_scenario": []}
    before = dict(helper.frozen.__dict__)
    field_path = Path("stub-only-field-not-read.json")
    digest = "a" * 64
    result = {"source_sha256": {}, "independent_complete_timber_admission": receipt, "field_sha256": digest}
    observed = []

    def seam(path, admitted, **kwargs):
        observed.append((path, admitted, kwargs))
        assert helper.frozen.GATE == helper.GATE
        assert Path(helper.frozen.__file__).resolve() == helper.BRIDGE
        assert Path(before["consume"].__code__.co_filename).resolve() == helper.BRIDGE
        changed = {key for key in before if helper.frozen.__dict__[key] is not before[key]}
        assert changed == {"GATE", "consume"}
        return result

    monkeypatch.setattr(helper.frozen, "consume", seam)
    out = helper.consume(field_path, receipt, expected_field_sha256=digest,
        admission_sha256=helper.GATE_SHA, samples=7, caller_sections=caller)
    assert observed == [(field_path, receipt, {"expected_field_sha256": digest,
        "admission_sha256": helper.GATE_SHA, "samples": 7, "caller_sections": caller})]
    assert out is result and out["independent_complete_timber_admission"] is receipt
    assert helper.frozen.GATE == before["GATE"]
    provenance = out["observer_isolation_component_reduction_bridge"]
    assert provenance["actual_admission"]["path"] == str(helper.GATE.relative_to(helper.ROOT))
    assert out["source_sha256"][str(PATH.resolve().relative_to(helper.ROOT))] == hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert provenance["only_gate_path_scoped_and_restored"] is True
    assert provenance["source_file_identity_or_receipt_schema_success_relabelled"] is False


def test_gate_path_restored_after_component_failure(monkeypatch):
    before = helper.frozen.GATE

    def fail(*args, **kwargs):
        assert helper.frozen.GATE == helper.GATE
        raise RuntimeError("explicit stub reduction failure")

    monkeypatch.setattr(helper.frozen, "consume", fail)
    with pytest.raises(RuntimeError, match="stub reduction failure"):
        helper.consume("not-read.json", {}, expected_field_sha256="a" * 64, admission_sha256=helper.GATE_SHA)
    assert helper.frozen.GATE == before


def test_wrong_gate_sha_rejected_before_scope_or_dispatch(monkeypatch):
    before = helper.frozen.GATE
    monkeypatch.setattr(helper.frozen, "consume", lambda *a, **k: pytest.fail("dispatch occurred"))
    with pytest.raises(ValueError, match="new gate SHA"):
        helper.consume("not-read.json", {}, expected_field_sha256="a" * 64, admission_sha256="0" * 64)
    assert helper.frozen.GATE == before


@pytest.mark.parametrize("schema", [
    "thin_bolted_independent_complete_timber_admission/v1",
    "thin_bolted_independent_complete_timber_observer_isolation_admission/v1",
])
def test_real_new_validator_rejects_old_or_unqualified_current_receipt(tmp_path, monkeypatch, schema):
    # Genuine validator rejection only: no successful production/domain proof.
    payload = b"{}"
    path = tmp_path / "unadmitted.json"
    path.write_bytes(payload)
    receipt = {"schema": schema}
    before = helper.frozen.GATE
    monkeypatch.setattr(helper.frozen, "_reduce", lambda *a, **k: pytest.fail("unadmitted reductions occurred"))
    with pytest.raises(ValueError, match="actual complete-field admission"):
        helper.consume(path, receipt, expected_field_sha256=hashlib.sha256(payload).hexdigest(),
                       admission_sha256=helper.GATE_SHA)
    assert helper.frozen.GATE == before
    assert receipt == {"schema": schema} and json.loads(path.read_bytes()) == {}
