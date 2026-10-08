"""Chain receipt seam coupons; synthetic admission is no body/force proof."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from scripts import thin_bolted_chain_post_admission as adapter
from scripts import thin_bolted_support_chain_admission as gate

# Load a private fixture namespace. Frozen priority fixtures remain unchanged;
# their receipt factory/source seam depend only on these explicit constants.
spec = importlib.util.spec_from_file_location(
    "chain_reused_adapter_fixtures", Path(__file__).with_name("test_thin_bolted_priority_post_admission.py"))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
fixtures.adapter, fixtures.gate = adapter, gate
original = adapter.original
real_source_seam = fixtures.real_source_seam


def test_chain_contract_matches_actual_gate_and_preserved_reducer():
    assert (adapter.GATE, adapter.SCHEMA, adapter.SUCCESS) == (gate.OWN, gate.SCHEMA, gate.SUCCESS)
    assert original.unit.sha(Path(original.__file__)) == adapter.FROZEN_REDUCER_SHA256
    assert adapter.FROZEN_REDUCER_SHA256 == "e63aa17cb56b71feb4c700d6bc0ffb4b801f7716753d350ae475409dc2470e5a"


def test_original_bytes_and_actual_chain_receipt_metadata_pass_unchanged(real_source_seam, monkeypatch):
    raw, field, receipt, sha = real_source_seam
    # These are explicitly synthetic metadata witnesses, never old q/forces.
    receipt.update(actual_support_mask_chain_execution={"synthetic_source_witness": True},
        reused_internal_support_search_execution={"synthetic_internal_witness": True},
        failed_chain_source={"synthetic_ancestor_cohorts": ["cohort-a", "cohort-b"], "old_q_or_forces_used": False},
        chain_schedule_checks={"synthetic_union_mask_count": 3})
    before, pure_before = fixtures.contract(), fixtures.pure_methods()
    raw_before, receipt_before = bytes(raw), copy.deepcopy(receipt)
    caller = {"synthetic-axis": [{"id": "reference-only", "diameter_mm": 12.7, "section_basis": "synthetic"}]}
    caller_before = copy.deepcopy(caller)
    seen = []
    def reduction(payload, admitted, *, admission_sha256, samples, caller_sections):
        assert fixtures.contract() == (adapter.GATE, adapter.SCHEMA, adapter.SUCCESS)
        assert payload is raw and admitted is receipt and caller_sections is caller
        assert fixtures.pure_methods() == pure_before
        original.require_admission(payload, field, admitted, admission_sha256)
        seen.append((samples, admission_sha256))
        return {"source_sha256": {}, "independent_fresh_support_search_admission": admitted,
                "complete_joint_resistance": None, "complete_joint_acceptance": False}
    monkeypatch.setattr(original, "post_admission_reductions", reduction)
    result = adapter.post_chain_admission_reductions(raw, receipt, admission_sha256=sha, samples=3, caller_sections=caller)
    assert seen == [(3, sha)]
    assert raw == raw_before and receipt == receipt_before and caller == caller_before
    assert result["independent_fresh_support_search_admission"] is receipt
    assert result["independent_fresh_support_search_admission"]["schema"] == adapter.SCHEMA
    assert result["source_sha256"][adapter.GATE] == sha
    assert result["source_sha256"][adapter.OWN] == adapter.LOADED_PRODUCER_SHA256
    assert result["explicit_admission_contract_adapter"]["frozen_reducer_contract_constants_restored"] is True
    assert result["explicit_admission_contract_adapter"]["receipt_or_field_relabelled"] is False
    assert result["complete_joint_resistance"] is None
    assert fixtures.contract() == before and fixtures.pure_methods() == pure_before


@pytest.mark.parametrize("change", ["priority-schema", "base-schema", "success", "raw", "canonical", "state",
                                    "case", "accessory", "final-q", "source", "release", "diagnostic-q"])
def test_old_mixed_or_unadmitted_inputs_reject_before_reductions(real_source_seam, monkeypatch, change):
    raw, field, receipt, sha = real_source_seam
    before, pure_before = fixtures.contract(), fixtures.pure_methods()
    if change == "priority-schema":
        receipt["schema"] = "thin_bolted_independent_support_priority_admission/v1"
    elif change == "base-schema":
        receipt["schema"] = before[1]
    elif change == "success":
        receipt[adapter.SUCCESS] = False
    elif change == "raw":
        raw += b" "
    elif change == "canonical":
        receipt["field_canonical_sha256"] = "0"*64
    elif change in ("state", "case", "accessory"):
        receipt[{"state": "state_id", "case": "case_id", "accessory": "accessory_placement"}[change]] = "mixed"
    elif change == "final-q":
        receipt["support_search_checks"]["final_q_canonical_sha256"] = "0"*64
    elif change == "source":
        receipt["source_sha256"] = {"scripts/thin_bolted_support_priority_admission.py": sha}
    elif change == "release":
        receipt["release"]["climbing_released"] = True
    else:
        field["response"]["diagnostic_last_q"] = field["response"].pop("q")
        raw = json.dumps(field).encode()
        receipt["field_sha256"] = hashlib.sha256(raw).hexdigest()
        receipt["field_canonical_sha256"] = original.references.canonical_sha(field)
    calls = []
    def reduction(payload, admitted, *, admission_sha256, **_):
        original.require_admission(payload, json.loads(payload), admitted, admission_sha256)
        calls.append(True)
        raise AssertionError("invalid chain receipt reached domain reductions")
    monkeypatch.setattr(original, "post_admission_reductions", reduction)
    with pytest.raises(ValueError):
        adapter.post_chain_admission_reductions(raw, receipt, admission_sha256=sha)
    assert calls == []
    assert fixtures.contract() == before and fixtures.pure_methods() == pure_before


@pytest.mark.parametrize("source", ["adapter", "reducer", "gate"])
def test_source_pin_mismatch_stops_before_reducer_entry(real_source_seam, monkeypatch, source):
    raw, _, receipt, sha = real_source_seam
    before = fixtures.contract()
    if source == "adapter":
        monkeypatch.setattr(adapter, "LOADED_PRODUCER_SHA256", "0"*64)
    elif source == "reducer":
        monkeypatch.setattr(adapter, "FROZEN_REDUCER_SHA256", "0"*64)
    else:
        sha = "0"*64
    calls = []
    monkeypatch.setattr(original, "post_admission_reductions", lambda *_a, **_k: calls.append(True))
    with pytest.raises(ValueError, match="source differs"):
        adapter.post_chain_admission_reductions(raw, receipt, admission_sha256=sha)
    assert calls == [] and fixtures.contract() == before


def test_original_contract_and_methods_restore_after_reduction_exception(real_source_seam, monkeypatch):
    raw, _, receipt, sha = real_source_seam
    before, pure_before = fixtures.contract(), fixtures.pure_methods()
    def fail(*_, **__):
        assert fixtures.contract() == (adapter.GATE, adapter.SCHEMA, adapter.SUCCESS)
        assert fixtures.pure_methods() == pure_before
        raise RuntimeError("synthetic reduction failure")
    monkeypatch.setattr(original, "post_admission_reductions", fail)
    with pytest.raises(RuntimeError, match="synthetic reduction failure"):
        adapter.post_chain_admission_reductions(raw, receipt, admission_sha256=sha)
    assert fixtures.contract() == before and fixtures.pure_methods() == pure_before


@pytest.mark.parametrize("mutation", [None, "field", "receipt"])
def test_unchanged_frozen_dispatcher_and_mutation_guards(tmp_path, monkeypatch, mutation):
    # Reused fixture explicitly stubs source/body/domain proofs; only frozen
    # orchestration and input guards execute through the new chain contract.
    raw, receipt, sha, calls = fixtures.fixtures.composition_fixture(tmp_path, monkeypatch, mutation)
    chain_receipt = fixtures.priority_receipt(receipt, sha)
    receipt.clear()
    receipt.update(chain_receipt)
    before, pure_before = fixtures.contract(), fixtures.pure_methods()
    if mutation:
        with pytest.raises(ValueError, match="input changed"):
            adapter.post_chain_admission_reductions(raw, receipt, admission_sha256=sha, samples=3)
    else:
        receipt_before = copy.deepcopy(receipt)
        result = adapter.post_chain_admission_reductions(raw, receipt, admission_sha256=sha, samples=3)
        assert result["field_sha256"] == hashlib.sha256(raw).hexdigest()
        assert len(result["governing_conditional_reference_dispositions"]) == 11
        assert result["complete_joint_resistance"] is None and not any(result["release"].values())
        assert result["explicit_admission_contract_adapter"]["frozen_reducer_contract_constants_restored"] is True
        assert receipt == receipt_before
    assert [name for name, _ in calls] == ["wood", "cuts", "metal", "panels"]
    assert len({identity for _, identity in calls}) == 1
    assert fixtures.contract() == before and fixtures.pure_methods() == pure_before
