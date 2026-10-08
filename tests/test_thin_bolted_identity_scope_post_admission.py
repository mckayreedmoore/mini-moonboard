"""Same-byte outer receipt seam; fixtures do not qualify any candidate actions."""

import copy
import importlib.util
from pathlib import Path

import pytest

from scripts import thin_bolted_identity_scope_post_admission as adapter
from scripts import thin_bolted_support_identity_scope_admission as gate

spec = importlib.util.spec_from_file_location(
    "identity_scope_reduction_fixtures", Path(__file__).with_name("test_thin_bolted_priority_post_admission.py"))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
fixtures.adapter, fixtures.gate = adapter, gate
original = adapter.original
real_source_seam = fixtures.real_source_seam


def test_actual_outer_contract_and_preserved_reducer_match():
    assert (adapter.GATE, adapter.SCHEMA, adapter.SUCCESS) == (gate.OWN, gate.SCHEMA, gate.SUCCESS)
    assert original.unit.sha(Path(original.__file__)) == adapter.FROZEN_REDUCER_SHA256


def test_unchanged_actual_outer_receipt_and_bytes_reach_pure_reducer(real_source_seam, monkeypatch):
    raw, field, receipt, sha = real_source_seam
    receipt["frozen_chain_mechanics_admission"] = {"schema": "thin_bolted_independent_support_chain_admission/v1",
        "synthetic_subordinate_receipt_witness": True}
    before, methods = fixtures.contract(), fixtures.pure_methods()
    receipt_before = copy.deepcopy(receipt)
    received = []
    def reduction(payload, admitted, *, admission_sha256, samples, caller_sections):
        assert payload is raw and admitted is receipt
        assert fixtures.contract() == (adapter.GATE, adapter.SCHEMA, adapter.SUCCESS)
        assert fixtures.pure_methods() == methods
        original.require_admission(payload, field, admitted, admission_sha256)
        received.append(samples)
        return {"source_sha256": {}, "actual_admission": admitted, "complete_joint_acceptance": False}
    monkeypatch.setattr(original, "post_admission_reductions", reduction)
    result = adapter.post_identity_scope_admission_reductions(raw, receipt, admission_sha256=sha, samples=3)
    assert received == [3] and result["actual_admission"] is receipt
    assert receipt == receipt_before
    assert fixtures.contract() == before and fixtures.pure_methods() == methods
    assert result["source_sha256"][adapter.GATE] == sha
    assert result["explicit_admission_contract_adapter"]["receipt_or_field_relabelled"] is False


@pytest.mark.parametrize("change", ["chain-schema", "success", "raw", "canonical", "state", "final-q", "source"])
def test_old_or_mixed_receipts_stop_before_domain_reductions(real_source_seam, monkeypatch, change):
    raw, field, receipt, sha = real_source_seam
    before, methods = fixtures.contract(), fixtures.pure_methods()
    if change == "chain-schema":
        receipt["schema"] = "thin_bolted_independent_support_chain_admission/v1"
    elif change == "success":
        receipt[adapter.SUCCESS] = False
    elif change == "raw":
        raw += b" "
    elif change == "canonical":
        receipt["field_canonical_sha256"] = "0" * 64
    elif change == "state":
        receipt["state_id"] = "another state"
    elif change == "final-q":
        receipt["support_search_checks"]["final_q_canonical_sha256"] = "0" * 64
    else:
        receipt["source_sha256"] = {"scripts/thin_bolted_support_chain_admission.py": sha}
    calls = []
    def reduction(payload, admitted, *, admission_sha256, **_):
        original.require_admission(payload, field, admitted, admission_sha256)
        calls.append(True)
        raise AssertionError("invalid outer receipt reached reductions")
    monkeypatch.setattr(original, "post_admission_reductions", reduction)
    with pytest.raises(ValueError):
        adapter.post_identity_scope_admission_reductions(raw, receipt, admission_sha256=sha)
    assert calls == [] and fixtures.contract() == before and fixtures.pure_methods() == methods


def test_contract_restored_when_frozen_reducer_raises(real_source_seam, monkeypatch):
    raw, _, receipt, sha = real_source_seam
    before, methods = fixtures.contract(), fixtures.pure_methods()
    def fail(*_a, **_k):
        assert fixtures.contract() == (adapter.GATE, adapter.SCHEMA, adapter.SUCCESS)
        raise RuntimeError("synthetic domain failure")
    monkeypatch.setattr(original, "post_admission_reductions", fail)
    with pytest.raises(RuntimeError, match="synthetic domain failure"):
        adapter.post_identity_scope_admission_reductions(raw, receipt, admission_sha256=sha)
    assert fixtures.contract() == before and fixtures.pure_methods() == methods
