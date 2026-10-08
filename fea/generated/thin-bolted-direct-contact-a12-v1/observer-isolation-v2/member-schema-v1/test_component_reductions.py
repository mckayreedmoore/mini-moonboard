"""Real saved writer-schema checks and explicit stub dispatch coupons."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).with_name("component_reductions.py")
SPEC = importlib.util.spec_from_file_location("member_schema_component_coupon", PATH)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)
FIELD = PATH.parent.parent / "a12-rear.json"
FIELD_SHA = "29b25f11794a171a1364268ed676a24cee2882e47c3018b3648267d2707a0ddf"


@pytest.fixture(scope="module")
def saved_field():
    payload = FIELD.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == FIELD_SHA
    return payload, json.loads(payload)


def test_real_205_writer_schema_and_all_full_aggregate_cut_labels_unchanged(saved_field):
    payload, field = saved_field
    before = helper.pure.references.canonical_sha(field)
    assert len(field["member_element_actions"]) == 205
    assert len({r["member"] for r in field["member_element_actions"]}) == 20
    assert all(r["state_id"] == field["state_id"] and "case_id" not in r and "accessory_placement" not in r
               for r in field["member_element_actions"])
    helper.verify_alias_state_labels(field)
    assert helper.pure.references.canonical_sha(field) == before
    assert FIELD.read_bytes() == payload


@pytest.mark.parametrize("key,value", [
    ("state_id", "foreign"), ("state_id", None), ("state_id", "missing"),
    ("case_id", "foreign"), ("case_id", None),
    ("accessory_placement", "foreign"), ("accessory_placement", None),
])
def test_foreign_missing_or_none_member_identity_rejected(saved_field, key, value):
    field = copy.deepcopy(saved_field[1])
    if value == "missing":
        del field["member_element_actions"][0][key]
    else:
        field["member_element_actions"][0][key] = value
    before = helper.pure.references.canonical_sha(field)
    with pytest.raises(ValueError, match="member own state"):
        helper.verify_alias_state_labels(field)
    assert helper.pure.references.canonical_sha(field) == before


@pytest.mark.parametrize("table,nested", [
    ("common_shaft_wood_bearing_actions", False), ("common_shaft_steel_port_actions", False),
    ("common_shaft_section_cut_actions", False), ("common_shaft_section_cut_actions", True),
])
def test_aggregate_and_nested_cut_labels_remain_strict(saved_field, table, nested):
    field = copy.deepcopy(saved_field[1])
    row = field[table][0]
    if nested:
        row = row["cuts"][0]
    del row["case_id"]
    with pytest.raises(ValueError, match="aggregate/cut alias"):
        helper.verify_alias_state_labels(field)


def test_present_matching_member_labels_allowed_without_stamping_others(saved_field):
    field = copy.deepcopy(saved_field[1])
    field["member_element_actions"][0].update({k: field[k] for k in ("case_id", "accessory_placement")})
    before = helper.pure.references.canonical_sha(field)
    helper.verify_alias_state_labels(field)
    assert helper.pure.references.canonical_sha(field) == before
    assert "case_id" not in field["member_element_actions"][1]


@pytest.mark.parametrize("fails", [False, True])
def test_only_validator_scope_and_restoration_with_unchanged_arguments(monkeypatch, fails):
    # Stub dispatch only; no field, force calculation or successful body proof.
    receipt, caller = {}, {}
    original = helper.pure.timber.verify_alias_state_labels
    originals = dict(helper.pure.timber.__dict__)
    result = {"source_sha256": {}}

    def seam(path, admitted, **kwargs):
        assert path == "stub-not-read.json" and admitted is receipt
        assert kwargs == {"expected_field_sha256": FIELD_SHA, "admission_sha256": helper.bridge.GATE_SHA,
                          "samples": 7, "caller_sections": caller}
        assert helper.pure.timber.verify_alias_state_labels is helper.verify_alias_state_labels
        assert {k for k in originals if helper.pure.timber.__dict__[k] is not originals[k]} == {"verify_alias_state_labels"}
        if fails:
            raise RuntimeError("stub dispatch failure")
        return result

    monkeypatch.setattr(helper.bridge, "consume", seam)
    if fails:
        with pytest.raises(RuntimeError, match="stub dispatch failure"):
            helper.consume("stub-not-read.json", receipt, expected_field_sha256=FIELD_SHA,
                           admission_sha256=helper.bridge.GATE_SHA, samples=7, caller_sections=caller)
    else:
        out = helper.consume("stub-not-read.json", receipt, expected_field_sha256=FIELD_SHA,
                             admission_sha256=helper.bridge.GATE_SHA, samples=7, caller_sections=caller)
        assert out is result
        assert out["enclosing_member_identity_schema_bridge"]["member_labels_payload_or_receipt_modified"] is False
        assert out["source_sha256"][str(PATH.resolve().relative_to(helper.ROOT))] == hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert helper.pure.timber.verify_alias_state_labels is original
    assert receipt == {} and caller == {}
