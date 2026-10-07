"""Focused revised-admission and immutable input-binding fixtures."""

import json

import pytest

from scripts import thin_bolted_common_shaft_steel_bound as writer


def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(writer, "ROOT", tmp_path)
    helper, unit, head, gate = [tmp_path / name for name in ("helper.py", "unit.json", "head.json", "gate.py")]
    for path in (helper, unit, head, gate):
        path.write_text("preserved input")
    monkeypatch.setattr(writer.methods, "__file__", str(helper))
    adapter = tmp_path / "adapter.py"
    adapter.write_text("adapter source")
    monkeypatch.setattr(writer, "__file__", str(adapter))
    monkeypatch.setattr(writer.methods, "METHODS", unit)
    monkeypatch.setattr(writer.methods, "HEAD", head)
    receipt = tmp_path / "receipt.json"
    receipt.write_text("method receipt")
    monkeypatch.setattr(writer, "METHOD_RECEIPT", receipt)
    monkeypatch.setattr(writer, "METHOD_HELPER_SHA", writer.methods.sha(helper))
    monkeypatch.setattr(writer, "GATE_SHA", writer.methods.sha(gate))
    test = tmp_path / "tests/test_thin_bolted_common_shaft_steel_bound.py"
    test.parent.mkdir()
    test.write_text("test source")
    source = tmp_path / "field.json"
    source.write_text(json.dumps({"candidate": "thin", "state_id": "one", "case_id": "a12",
        "accessory_placement": "rear", "parameters": {}, "source_sha256": {},
        "common_shaft_steel_port_actions": [], "common_shaft_section_cut_actions": [],
        "shaft_end_capture_actions": [{"end": {"end": "head", "host": "fitting"}}]}))
    monkeypatch.setattr(writer, "require_gate", lambda demand: ({
        "independent_common_shaft_support_load_and_equilibrium_checks_pass": True}, gate))
    return source, gate


def test_failed_revised_gate_prevents_component_comparison(tmp_path, monkeypatch):
    source, _ = fixture(tmp_path, monkeypatch)
    def reject(_):
        raise ValueError("corrected independent physical common-shaft gate failed")
    monkeypatch.setattr(writer, "require_gate", reject)
    calls = []
    monkeypatch.setattr(writer, "component_values", lambda *_: calls.append(True))
    with pytest.raises(ValueError, match="gate failed"):
        writer.consume(source)
    assert calls == []


def test_revised_admission_preserves_actual_end_dictionary_and_pins_one_read(tmp_path, monkeypatch):
    source, _ = fixture(tmp_path, monkeypatch)
    received = []
    def components(demand, caller):
        received.append((demand["state_id"], demand["shaft_end_capture_actions"][0]["end"]))
        return {"independent_shaft_cut_replay": {"independent_same_cut_equilibrium_replay_pass": True}}
    monkeypatch.setattr(writer, "component_values", components)
    result = writer.consume(source)
    assert received == [("one", {"end": "head", "host": "fitting"})]
    assert result["source_sha256"]["field.json"] == writer.methods.sha(source)
    assert result["state_id"] == "one"
    assert result["complete_joint_acceptance"] is False


@pytest.mark.parametrize("mutation", ["state", "gate", "caller"])
def test_source_changes_during_comparison_reject_issuance(tmp_path, monkeypatch, mutation):
    source, gate = fixture(tmp_path, monkeypatch)
    caller = tmp_path / "sections.json"
    caller.write_text("{}")
    def components(*_):
        {"state": source, "gate": gate, "caller": caller}[mutation].write_text("changed")
        return {}
    monkeypatch.setattr(writer, "component_values", components)
    with pytest.raises(ValueError, match="changed during"):
        writer.consume(source, caller)


def state_alias_fixture():
    state = {"state_id": "one", "case_id": "load", "accessory_placement": "rear"}
    return {**state, "common_shaft_steel_port_actions": [state.copy()],
            "common_shaft_section_cut_actions": [{**state, "cuts": [state.copy()]}]}


def test_every_aggregate_and_nested_cut_uses_admitted_state_identity():
    writer.verify_component_state_labels(state_alias_fixture())


@pytest.mark.parametrize("mutation", ["steel-state", "steel-case", "steel-placement", "cut-row", "nested-cut", "missing"])
def test_state_alias_guard_rejects_numerically_equal_other_state_or_missing_labels(mutation):
    demand = state_alias_fixture()
    steel, cut = demand["common_shaft_steel_port_actions"][0], demand["common_shaft_section_cut_actions"][0]
    if mutation == "steel-state":
        steel["state_id"] = "another"
    elif mutation == "steel-case":
        steel["case_id"] = "another"
    elif mutation == "steel-placement":
        steel["accessory_placement"] = "front"
    elif mutation == "cut-row":
        cut["state_id"] = "another"
    elif mutation == "nested-cut":
        cut["cuts"][0]["case_id"] = "another"
    else:
        cut["cuts"][0].pop("state_id")
    with pytest.raises(ValueError, match="state/load identity"):
        writer.verify_component_state_labels(demand)
