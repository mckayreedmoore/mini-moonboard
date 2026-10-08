"""Priority receipt seam coupons; synthetic admission is no body/force proof."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from scripts import thin_bolted_priority_post_admission as adapter
from scripts import thin_bolted_support_priority_admission as gate

original = adapter.original
REAL_ROOT = original.ROOT
spec = importlib.util.spec_from_file_location(
    "post_admission_synthetic_fixtures", Path(__file__).with_name("test_thin_bolted_joint_post_admission.py"))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


def contract():
    return original.GATE, original.ADMISSION_SCHEMA, original.ADMISSION_SUCCESS


def pure_methods():
    return (original.timber.member_point_inputs, original.timber.aggregate_wood_bearings,
            original.timber.replay_existing_member_cuts, original.steel.component_values,
            original.panel.prepared_datums, original.panel.coefficient_slice,
            original.panel.plate_fields, original.panel.screw_references,
            original.torsion.simultaneous_section_bound)


def priority_receipt(receipt, gate_sha):
    result = copy.deepcopy(receipt)
    result.pop(original.ADMISSION_SUCCESS)
    result.update(schema=adapter.SCHEMA, **{adapter.SUCCESS: True}, source_sha256={adapter.GATE: gate_sha})
    return result


@pytest.fixture
def real_source_seam(tmp_path, monkeypatch):
    """Real adapter/reducer/gate bytes; only the tiny admission receipt is stubbed."""
    payload, field, receipt, _, _ = fixtures.admission_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(original, "ROOT", REAL_ROOT)
    gate_sha = original.unit.sha(REAL_ROOT/adapter.GATE)
    receipt = priority_receipt(receipt, gate_sha)
    return payload, field, receipt, gate_sha


def test_adapter_contract_matches_actual_priority_gate_and_frozen_reducer():
    assert (adapter.GATE, adapter.SCHEMA, adapter.SUCCESS) == (gate.OWN, gate.SCHEMA, gate.SUCCESS)
    assert original.unit.sha(Path(original.__file__)) == adapter.FROZEN_REDUCER_SHA256
    assert adapter.FROZEN_REDUCER_SHA256 == "e63aa17cb56b71feb4c700d6bc0ffb4b801f7716753d350ae475409dc2470e5a"


def test_exact_immutable_payload_receipt_and_caller_data_pass_unchanged(real_source_seam, monkeypatch):
    payload, field, receipt, gate_sha = real_source_seam
    before, methods_before = contract(), pure_methods()
    field_before, receipt_before = bytes(payload), copy.deepcopy(receipt)
    caller = {"synthetic-axis": [{"id": "synthetic-section", "diameter_mm": 12.7,
                                  "section_basis": "method fixture; no delivered product"}]}
    caller_before = copy.deepcopy(caller)
    received = []
    def reduction_seam(raw, admission, *, admission_sha256, samples, caller_sections):
        assert contract() == (adapter.GATE, adapter.SCHEMA, adapter.SUCCESS)
        assert pure_methods() == methods_before
        assert raw is payload and admission is receipt and caller_sections is caller
        original.require_admission(raw, field, admission, admission_sha256)
        received.append((samples, admission_sha256))
        return {"source_sha256": {}, "field_sha256": hashlib.sha256(raw).hexdigest(),
                "complete_joint_acceptance": False, "complete_joint_resistance": None}
    monkeypatch.setattr(original, "post_admission_reductions", reduction_seam)
    result = adapter.post_priority_admission_reductions(payload, receipt, admission_sha256=gate_sha,
                                                        samples=3, caller_sections=caller)
    assert received == [(3, gate_sha)]
    assert contract() == before and pure_methods() == methods_before
    assert payload == field_before and receipt == receipt_before and caller == caller_before
    assert result["source_sha256"][adapter.GATE] == gate_sha
    assert result["source_sha256"][adapter.OWN] == adapter.LOADED_PRODUCER_SHA256
    assert result["source_sha256"][str(Path(original.__file__).relative_to(REAL_ROOT))] == adapter.FROZEN_REDUCER_SHA256
    assert result["explicit_admission_contract_adapter"]["receipt_or_field_relabelled"] is False
    assert result["explicit_admission_contract_adapter"]["forces_coefficients_or_pure_reduction_methods_changed"] is False
    assert result["complete_joint_resistance"] is None


@pytest.mark.parametrize("change", ["old-schema", "false-success", "raw", "canonical", "state", "case", "accessory",
                                    "final-q", "source", "field-release", "receipt-release", "diagnostic-q", "mutable-bytes"])
def test_bad_contract_rejects_before_any_domain_reduction(real_source_seam, monkeypatch, change):
    payload, field, receipt, gate_sha = real_source_seam
    before, methods_before = contract(), pure_methods()
    if change == "old-schema":
        receipt["schema"] = before[1]
    elif change == "false-success":
        receipt[adapter.SUCCESS] = False
    elif change == "raw":
        payload += b" "
    elif change == "canonical":
        receipt["field_canonical_sha256"] = "0"*64
    elif change in ("state", "case", "accessory"):
        receipt[{"state": "state_id", "case": "case_id", "accessory": "accessory_placement"}[change]] = "mixed"
    elif change == "final-q":
        receipt["support_search_checks"]["final_q_canonical_sha256"] = "0"*64
    elif change == "source":
        receipt["source_sha256"] = {before[0]: gate_sha}
    elif change == "receipt-release":
        receipt["release"]["climbing_released"] = True
    elif change == "mutable-bytes":
        payload = bytearray(payload)
    else:
        if change == "field-release":
            field["release"]["candidate_accepted"] = True
        else:
            field["response"]["diagnostic_last_q"] = field["response"].pop("q")
        payload = json.dumps(field).encode()
        receipt["field_sha256"] = hashlib.sha256(payload).hexdigest()
        receipt["field_canonical_sha256"] = original.references.canonical_sha(field)
    domain_calls = []
    def reduction_seam(raw, admission, *, admission_sha256, **_):
        original.require_admission(raw, json.loads(raw), admission, admission_sha256)
        domain_calls.append(True)
        raise AssertionError("an invalid receipt reached domain reductions")
    monkeypatch.setattr(original, "post_admission_reductions", reduction_seam)
    with pytest.raises(ValueError):
        adapter.post_priority_admission_reductions(payload, receipt, admission_sha256=gate_sha)
    assert domain_calls == []
    assert contract() == before and pure_methods() == methods_before


@pytest.mark.parametrize("source", ["adapter", "reducer", "gate"])
def test_real_source_pin_mismatch_prevents_reducer_entry(real_source_seam, monkeypatch, source):
    payload, _, receipt, gate_sha = real_source_seam
    before = contract()
    if source == "adapter":
        monkeypatch.setattr(adapter, "LOADED_PRODUCER_SHA256", "0"*64)
    elif source == "reducer":
        monkeypatch.setattr(adapter, "FROZEN_REDUCER_SHA256", "0"*64)
    else:
        gate_sha = "0"*64
    calls = []
    monkeypatch.setattr(original, "post_admission_reductions", lambda *_a, **_k: calls.append(True))
    with pytest.raises(ValueError, match="source differs"):
        adapter.post_priority_admission_reductions(payload, receipt, admission_sha256=gate_sha)
    assert calls == [] and contract() == before


def test_three_contract_constants_restore_after_reducer_failure(real_source_seam, monkeypatch):
    payload, _, receipt, gate_sha = real_source_seam
    before, methods_before = contract(), pure_methods()
    def fail(*_, **__):
        assert contract() == (adapter.GATE, adapter.SCHEMA, adapter.SUCCESS)
        assert pure_methods() == methods_before
        raise RuntimeError("synthetic pure reduction failure")
    monkeypatch.setattr(original, "post_admission_reductions", fail)
    with pytest.raises(RuntimeError, match="synthetic pure reduction failure"):
        adapter.post_priority_admission_reductions(payload, receipt, admission_sha256=gate_sha)
    assert contract() == before and pure_methods() == methods_before


@pytest.mark.parametrize("mutation", [None, "field", "receipt"])
def test_frozen_reducer_dispatch_and_mutation_guards_through_priority_contract(tmp_path, monkeypatch, mutation):
    # Original composition_fixture explicitly stubs source/body/domain proofs.
    # The frozen e63 orchestration itself runs unchanged through this adapter.
    payload, receipt, gate_sha, calls = fixtures.composition_fixture(tmp_path, monkeypatch, mutation)
    priority = priority_receipt(receipt, gate_sha)
    receipt.clear()
    receipt.update(priority)
    before, methods_before = contract(), pure_methods()
    if mutation:
        with pytest.raises(ValueError, match="input changed"):
            adapter.post_priority_admission_reductions(payload, receipt, admission_sha256=gate_sha, samples=3)
    else:
        raw_before, receipt_before = bytes(payload), copy.deepcopy(receipt)
        result = adapter.post_priority_admission_reductions(payload, receipt, admission_sha256=gate_sha, samples=3)
        assert result["field_sha256"] == hashlib.sha256(payload).hexdigest()
        assert len(result["governing_conditional_reference_dispositions"]) == 11
        assert result["complete_joint_resistance"] is None and not any(result["release"].values())
        assert payload == raw_before and receipt == receipt_before
    assert [name for name, _ in calls] == ["wood", "cuts", "metal", "panels"]
    assert len({identity for _, identity in calls}) == 1
    assert contract() == before and pure_methods() == methods_before
