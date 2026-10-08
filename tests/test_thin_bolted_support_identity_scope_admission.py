"""Outer scope coupons reuse synthetic chain mechanics, with no candidate solve."""

import copy
import importlib.util
from pathlib import Path

import pytest

from scripts import thin_bolted_support_identity_scope_admission as gate

spec = importlib.util.spec_from_file_location(
    "identity_scope_chain_fixtures", Path(__file__).with_name("test_thin_bolted_support_chain_admission.py"))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
sources, priority_fixture, chain_fixture = fixtures.sources, fixtures.priority_fixture, fixtures.chain
payload, bind_identity = fixtures.fixtures.fixtures.payload, fixtures.fixtures.fixtures.bind_identity


@pytest.fixture
def scope(chain_fixture, monkeypatch):
    field, chain_args, ancestry = chain_fixture
    monkeypatch.setattr(gate, "ROOT", gate.chain.ROOT)
    monkeypatch.setattr(gate, "CHAIN_GATE_SHA256", gate.chain.LOADED_PRODUCER_SHA256)
    monkeypatch.setattr(gate, "CHAIN_ARGS", fixtures.source_args(chain_args))
    pins = gate.chain.source_pins(**gate.CHAIN_ARGS)
    for name in (gate.OWN, gate.DRIVER, gate.OWN_TEST):
        path = gate.ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic identity scope: " + name)
        pins[name] = gate.chain.core.support.digest(path)
    monkeypatch.setattr(gate, "LOADED_PRODUCER_SHA256", pins[gate.OWN])
    receipt_path = gate.ROOT / "scope-method.json"
    receipt_path.write_bytes(payload({"schema": gate.METHOD_SCHEMA, "method_checks_pass": True,
        "released": False, "release": dict(field["release"]), "source_sha256": pins}))
    monkeypatch.setattr(gate, "METHOD_RECEIPT", receipt_path)
    args = {"driver_sha256": pins[gate.DRIVER], "method_receipt_path": receipt_path,
        "method_receipt_sha256": gate.chain.core.support.digest(receipt_path),
        "prior_failure_path": chain_args["prior_failure_path"], "prior_failure_sha256": chain_args["prior_failure_sha256"]}
    field["parameters"].update({"support_mask_schedule_identity_scope_driver_sha256": args["driver_sha256"],
        "support_mask_schedule_identity_scope_method_receipt_sha256": args["method_receipt_sha256"]})
    bind_identity(field)
    sha = gate.canonical_sha(field["response"]["support_mask_chain_schedule_v1"])
    command = field["support_mask_chain_execution"]["command"]
    field["support_identity_scope_execution"] = {"command": [command[0], "-m",
        "scripts.run_thin_bolted_support_identity_scope_frame", "--support-identity-method-receipt", str(receipt_path),
        "--support-identity-method-sha256", args["method_receipt_sha256"], *command[3:]],
        "loaded_driver_sha256": args["driver_sha256"], "method_receipt_path": gate.chain.relative(receipt_path),
        "method_receipt_sha256": args["method_receipt_sha256"],
        "nested_support_mask_chain_execution_is_reused_internal_call": True,
        "historical_metadata_path": gate.HISTORICAL_PATH, "historical_metadata_before_canonical_sha256": sha,
        "historical_metadata_after_canonical_sha256": sha, "historical_metadata_restored_unchanged": True,
        "current_action_identities_verified": True}
    field["source_sha256"].update(gate.source_pins(args["driver_sha256"], receipt_path, args["method_receipt_sha256"]))
    field["nested_current_actions"] = [{"state_id": field["state_id"], "case_id": field["case_id"],
        "accessory_placement": field["accessory_placement"], "cuts": [{"state_id": field["state_id"]}]}]
    return field, args, ancestry


def outer_args(args):
    return {key: args[key] for key in ("driver_sha256", "method_receipt_path", "method_receipt_sha256")}


def test_actual_outer_receipt_delegates_identical_bytes_without_projection_or_relabelling(scope, monkeypatch):
    field, args, _ = scope
    before = copy.deepcopy(field)
    raw = payload(field) + b"\n"
    original = gate.chain.audit_support_chain_state
    seen = []
    def child(actual, **kwargs):
        assert actual is raw
        assert gate.canonical_sha(gate.json.loads(actual)) == gate.canonical_sha(before)
        result = original(actual, **kwargs)
        seen.append(result)
        return result
    monkeypatch.setattr(gate.chain, "audit_support_chain_state", child)
    result = gate.audit_support_identity_scope_state(raw, **args)
    assert result[gate.SUCCESS] is True and result["schema"] == gate.SCHEMA
    assert result["frozen_chain_mechanics_admission"] is seen[0]
    assert seen[0]["schema"] == gate.chain.SCHEMA and seen[0][gate.chain.SUCCESS] is True
    assert result["field_sha256"] == seen[0]["field_sha256"] == gate.hashlib.sha256(raw).hexdigest()
    assert result["state_id"] == seen[0]["state_id"] == field["state_id"]
    assert result["support_search_checks"] == seen[0]["support_search_checks"]
    assert result["actual_outer_execution"]["command"][2] == "scripts.run_thin_bolted_support_identity_scope_frame"
    assert seen[0]["actual_support_mask_chain_execution"]["command"][2] == "scripts.run_thin_bolted_support_chain_frame"
    assert field == before
    assert all(value is False for value in result["release"].values())


@pytest.mark.parametrize("change", ["outside-state", "outside-case", "unlabelled-case", "extra-exemption", "top-command", "inner-args",
    "snapshot-before", "snapshot-after", "exempt-path", "unrestored", "source", "state-source", "short-flag"])
def test_only_authenticated_history_can_escape_current_identity_checks(scope, change, monkeypatch):
    field, args, _ = scope
    row = field["nested_current_actions"][0]
    execution = field["support_identity_scope_execution"]
    if change == "outside-state":
        row["cuts"][0]["state_id"] = "old"
    elif change == "outside-case":
        row["case_id"] = "old"
    elif change == "unlabelled-case":
        field["unlabelled_current_load"] = {"case_id": "old"}
    elif change == "extra-exemption":
        field["another_historical_blob"] = {"state_id": "old"}
    elif change == "top-command":
        execution["command"][2] = "scripts.run_thin_bolted_support_chain_frame"
    elif change == "inner-args":
        execution["command"] += ["--cases", "a12-front"]
    elif change.startswith("snapshot-"):
        execution["historical_metadata_" + change.split("-")[1] + "_canonical_sha256"] = "0" * 64
    elif change == "exempt-path":
        execution["historical_metadata_path"] = "nested_current_actions"
    elif change == "unrestored":
        execution["historical_metadata_restored_unchanged"] = False
    elif change == "source":
        field["source_sha256"].pop(gate.DRIVER)
    elif change == "state-source":
        field["parameters"]["support_mask_schedule_identity_scope_driver_sha256"] = "0" * 64
    else:
        execution["command"][3] = "--support-identity-method-receip"
    monkeypatch.setattr(gate.chain, "audit_support_chain_state", lambda *_a, **_k: pytest.fail("invalid outer scope delegated"))
    with pytest.raises(ValueError):
        gate.audit_support_identity_scope_state(payload(field), **args)


@pytest.mark.parametrize("change", ["schema", "released", "release", "gate", "method-test"])
def test_checked_outer_method_receipt_cannot_omit_or_replace_its_source_contract(scope, change):
    _, args, _ = scope
    path = args["method_receipt_path"]
    receipt = gate.json.loads(path.read_bytes())
    if change == "schema":
        receipt["schema"] = gate.chain.METHOD_SCHEMA
    elif change == "released":
        receipt["released"] = True
    elif change == "release":
        receipt["release"]["candidate_selected"] = True
    else:
        receipt["source_sha256"].pop(gate.OWN if change == "gate" else gate.OWN_TEST)
    path.write_bytes(payload(receipt))
    with pytest.raises(ValueError):
        gate.source_pins(args["driver_sha256"], path, gate.chain.core.support.digest(path))


def test_historical_ids_remain_different_and_authenticate_against_actual_raw_ancestors(scope):
    field, args, _ = scope
    metadata = field["response"]["support_mask_chain_schedule_v1"]
    assert any(row["state_id"] != field["state_id"] for row in metadata["cohorts"])
    # Matching the outer snapshot cannot turn fabricated history into ancestry.
    metadata["cohorts"][0]["state_id"] = field["state_id"]
    sha = gate.canonical_sha(metadata)
    field["support_identity_scope_execution"].update(historical_metadata_before_canonical_sha256=sha,
        historical_metadata_after_canonical_sha256=sha)
    with pytest.raises(ValueError, match="exact authenticated cohorts"):
        gate.audit_support_identity_scope_state(payload(field), **args)


@pytest.mark.parametrize("change", [None, "command", "scope-source", "scope-omitted"])
def test_future_ancestor_outer_scopes_are_verified_from_preserved_raw_fields(scope, change):
    field, args, _ = scope
    failed = fixtures.fixtures.failed_previous(field)
    failed["response"]["termination"] = "support-mask search budget"
    if change == "command":
        failed["support_identity_scope_execution"]["command"][2] = "scripts.run_another"
    elif change == "scope-source":
        failed["source_sha256"].pop(gate.DRIVER)
    elif change == "scope-omitted":
        failed.pop("support_identity_scope_execution")
    path = gate.ROOT / "scope-failed.json"
    path.write_bytes(payload(failed))
    sha = gate.chain.core.support.digest(path)
    # Frozen lineage checks unchanged scheduling policy; the new adapter adds
    # independent authentication of the real outer identity-scope invocation.
    ancestry = gate.chain.read_failed_chain(path, sha, field, **gate.CHAIN_ARGS)
    if change:
        with pytest.raises(ValueError):
            gate.verify_recorded_ancestor_scopes(ancestry, **outer_args(args))
    else:
        result = gate.verify_recorded_ancestor_scopes(ancestry, **outer_args(args))
        assert result["scoped_ancestor_paths"] == [gate.chain.relative(path)]
        assert ancestry["cohorts"][-1]["policy"] == "chain"


@pytest.mark.parametrize("change", ["raw-current", "raw-ancestor", "driver-source", "child-identity", "child-success"])
def test_outer_admission_cannot_hide_mutations_or_failed_child_mechanics(scope, monkeypatch, change):
    field, args, ancestry = scope
    path = gate.ROOT / "outer-current.json"
    path.write_bytes(payload(field))
    original = gate.chain.audit_support_chain_state
    def child(actual, **kwargs):
        result = original(actual, **kwargs)
        if change == "raw-current":
            path.write_bytes(path.read_bytes() + b"\n")
        elif change == "raw-ancestor":
            ancestor = gate.ROOT / ancestry["cohorts"][0]["field_path"]
            ancestor.write_bytes(ancestor.read_bytes() + b"\n")
        elif change == "driver-source":
            (gate.ROOT / gate.DRIVER).write_text("changed source")
        elif change == "child-identity":
            result["state_id"] = "mixed child"
        else:
            result[gate.chain.SUCCESS] = False
        return result
    monkeypatch.setattr(gate.chain, "audit_support_chain_state", child)
    with pytest.raises(ValueError):
        gate.audit_support_identity_scope_state(path, **args)
