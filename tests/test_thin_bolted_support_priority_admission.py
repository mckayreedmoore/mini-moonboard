"""Priority provenance and scheduling coupons; no candidate/K/CAD/solve."""

import copy
import importlib.util
from pathlib import Path

import pytest

from scripts import thin_bolted_support_priority_admission as gate

# Reuse synthetic ports/source fixtures without copying frozen implementations.
spec = importlib.util.spec_from_file_location(
    "support_search_admission_fixtures", Path(__file__).with_name("test_thin_bolted_support_search_admission.py"))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
sources = fixtures.sources


def failed_previous(field):
    previous = copy.deepcopy(field)
    previous["usable_conditional_actions"] = False
    previous["failed_response_without_recovered_actions"] = True
    previous["compatible_numerical_mvp_complete"] = False
    previous["floor_actions"] = []
    response = previous["response"]
    response["converged"] = False
    response.pop("q")
    response["diagnostic_last_q"] = ["unused diagnostic payload"]
    trace = response["support_state_search_v1"]
    hosts = trace["host_order"]
    row = trace["tested_masks"][0]
    row["floor_normal_force_n_by_host"][hosts[0]] = 0.
    row["demanded_enabled_centroid_xy_hosts"] = hosts[1:]
    row["self_consistent"] = False
    trace.update(accepted_pattern_index=None, accepted_enabled_centroid_xy_hosts=None,
        accepted_disabled_centroid_xy_hosts=None, final_mask_id=None, final_q_canonical_sha256=None)
    return previous


@pytest.fixture
def priority(sources, monkeypatch):
    _, core_args = sources
    field, _ = fixtures.orchestration(sources, monkeypatch)
    field.update(candidate="synthetic candidate", revision="synthetic revision", layout_report_sha256="synthetic layout",
        gravity={"synthetic": True}, applied_force_xyz_n=[0., 0., -1.],
        applied_moment_about_global_origin_xyz_nmm=[0., 0., 0.], body_applied_loads=[], body_identities=[],
        finished_floor_footprints=[])
    monkeypatch.setattr(gate, "ROOT", gate.core.ROOT)
    monkeypatch.setattr(gate, "CORE_ARGS", core_args)
    monkeypatch.setattr(gate, "CORE_GATE_SHA256", gate.core.LOADED_PRODUCER_SHA256)
    pins = gate.core.source_pins(**core_args)
    for name in (gate.OWN, gate.DRIVER, gate.SCHEDULE, gate.SCHEDULE_TEST):
        path = gate.ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic priority source: " + name)
        pins[name] = gate.core.support.digest(path)
    monkeypatch.setattr(gate, "LOADED_PRODUCER_SHA256", pins[gate.OWN])
    receipt_path = gate.ROOT / "priority-receipt.json"
    receipt_path.write_bytes(fixtures.payload({"schema": gate.METHOD_SCHEMA, "method_checks_pass": True,
        "released": False, "release": dict.fromkeys(gate.core.RELEASE_KEYS, False), "source_sha256": pins}))
    monkeypatch.setattr(gate, "METHOD_RECEIPT", receipt_path)
    previous_path = gate.ROOT / "previous-failed.json"
    previous_path.write_bytes(fixtures.payload(failed_previous(field)))
    args = {"priority_driver_sha256": pins[gate.DRIVER], "schedule_sha256": pins[gate.SCHEDULE],
        "method_receipt_path": receipt_path, "method_receipt_sha256": gate.core.support.digest(receipt_path),
        "prior_failure_path": previous_path, "prior_failure_sha256": gate.core.support.digest(previous_path)}
    command = field["support_state_search_execution"]["command"]
    field["support_priority_execution"] = {
        "command": [command[0], "-m", "scripts.run_thin_bolted_support_priority_frame",
            "--support-prior-failure", str(previous_path), "--support-prior-sha256", args["prior_failure_sha256"],
            "--support-priority-method-receipt", str(receipt_path),
            "--support-priority-method-sha256", args["method_receipt_sha256"], *command[3:]],
        "loaded_driver_sha256": args["priority_driver_sha256"], "loaded_schedule_sha256": args["schedule_sha256"],
        "method_receipt_path": gate.relative(receipt_path), "method_receipt_sha256": args["method_receipt_sha256"],
        "prior_failure_path": gate.relative(previous_path), "prior_failure_sha256": args["prior_failure_sha256"],
        "scheduling_only": True, "prior_q_or_forces_used": False,
        "nested_support_search_execution_is_reused_internal_call": True}
    field["parameters"].update({"support_priority_driver_sha256": args["priority_driver_sha256"],
        "support_priority_schedule_sha256": args["schedule_sha256"],
        "support_priority_method_receipt_sha256": args["method_receipt_sha256"],
        "support_priority_prior_failure_sha256": args["prior_failure_sha256"]})
    prior, _ = gate.read_prior_failure(previous_path, args["prior_failure_sha256"], field)
    field["response"]["support_mask_schedule_v1"] = {"schema": gate.SCHEDULE_SCHEMA, "method": gate.SCHEDULE_METHOD,
        "previous_field_path": prior["path"], "previous_field_sha256": prior["sha256"],
        "previous_field_canonical_sha256": prior["canonical_sha256"], "previous_state_id": prior["state_id"],
        "previous_case_id": prior["case_id"], "previous_accessory_placement": prior["accessory_placement"],
        "previous_host_order": prior["host_order"], "previous_mask_ids": prior["mask_ids"],
        "physical_input_signature_sha256": prior["physical_input_signature_sha256"],
        "scheduling_only": True, "old_q_or_forces_used": False, "previous_results_are_nonexistence_proof": False,
        "physical_laws_changed": False, "first_all_host_branch_remains_fresh": True}
    field["source_sha256"].update(gate.source_pins(**{key: args[key] for key in (
        "priority_driver_sha256", "schedule_sha256", "method_receipt_path", "method_receipt_sha256")}))
    field["source_sha256"][gate.relative(previous_path)] = args["prior_failure_sha256"]
    fixtures.bind_identity(field)
    monkeypatch.setattr(gate.core, "audit_support_search_state", lambda *_a, **_k: pytest.fail("old full admission called"))
    return field, args, prior


def test_distinct_priority_receipt_preserves_bytes_and_truthful_internal_command(priority):
    field, args, _ = priority
    raw = fixtures.payload(field)
    result = gate.audit_support_priority_state(raw, **args)
    assert result["schema"] == gate.SCHEMA and result[gate.SUCCESS] is True
    assert result["field_sha256"] == gate.core.hashlib.sha256(raw).hexdigest()
    assert result["field_canonical_sha256"] == gate.canonical_sha(field)
    assert result["actual_support_priority_execution"]["command"][2] == "scripts.run_thin_bolted_support_priority_frame"
    assert result["reused_internal_support_search_execution"]["command"][2] == "scripts.run_thin_bolted_support_search_frame"
    assert result["prior_scheduling_source"]["old_q_or_forces_used"] is False
    assert result["support_search_checks"]["final_q_canonical_sha256"] == gate.canonical_sha(field["response"]["q"])
    assert all(value is False for value in result["release"].values())


@pytest.mark.parametrize("mutation", ["top-command", "internal-args", "prior-sha", "schedule-sha", "old-q-flag", "source", "identity"])
def test_top_priority_provenance_cannot_alias_a_frozen_run_or_transfer_old_q(priority, mutation):
    field, args, _ = priority
    execution = field["support_priority_execution"]
    if mutation == "top-command":
        execution["command"][2] = "scripts.run_thin_bolted_support_search_frame"
    elif mutation == "internal-args":
        execution["command"] += ["--beam-size", "100"]
    elif mutation == "prior-sha":
        execution["prior_failure_sha256"] = "0" * 64
    elif mutation == "schedule-sha":
        execution["loaded_schedule_sha256"] = "0" * 64
    elif mutation == "old-q-flag":
        field["response"]["support_mask_schedule_v1"]["old_q_or_forces_used"] = True
    elif mutation == "source":
        field["source_sha256"].pop(gate.SCHEDULE)
    else:
        field["state_id"] = "old-state"
    with pytest.raises(ValueError):
        gate.audit_support_priority_state(fixtures.payload(field), **args)


@pytest.mark.parametrize("mutation", ["accepted-q", "converged", "wrong-case", "mask-id", "resolved-fixed-point", "wrong-source"])
def test_prior_failure_supplies_only_authenticated_discrete_history(priority, mutation):
    field, args, _ = priority
    path = args["prior_failure_path"]
    previous = gate.json.loads(path.read_bytes())
    response = previous["response"]
    if mutation == "accepted-q":
        response["q"] = []
    elif mutation == "converged":
        response["converged"] = True
    elif mutation == "wrong-case":
        previous["case_id"] = "another-case"
    elif mutation == "mask-id":
        response["support_state_search_v1"]["tested_masks"][0]["mask_id"] = "centroid-mask-00000000"
    elif mutation == "resolved-fixed-point":
        row = response["support_state_search_v1"]["tested_masks"][0]
        row["floor_normal_force_n_by_host"] = dict.fromkeys(row["enabled_centroid_xy_hosts"], 1.)
        row["demanded_enabled_centroid_xy_hosts"] = row["enabled_centroid_xy_hosts"]
    else:
        previous["source_sha256"][gate.core.SEARCH] = "0" * 64
    path.write_bytes(fixtures.payload(previous))
    with pytest.raises(ValueError):
        gate.read_prior_failure(path, gate.core.support.digest(path), field)


def test_priority_choices_skip_prior_feedback_but_keep_fresh_all_on(priority):
    field, _, prior = priority
    hosts = prior["host_order"]
    prior["mask_numbers"] = [255, 254]
    prior["mask_ids"] = [gate.search._mask_id(hosts, number) for number in prior["mask_numbers"]]
    field["response"]["support_mask_schedule_v1"]["previous_mask_ids"] = prior["mask_ids"]
    masks = [hosts, [host for host in hosts if host != hosts[1]]]
    normals = [{host: 0. if host == hosts[0] else 1. for host in hosts},
               {host: 0. if host == hosts[1] else 1. for host in hosts}]
    rows = [fixtures.branch_row(field, mask, normal, index)
            for index, (mask, normal) in enumerate(zip(masks, normals, strict=True))]
    field["response"]["support_state_search_v1"]["tested_masks"] = rows
    checks = gate.verify_priority_schedule(field, prior)
    assert checks["globally_new_tested_mask_count"] == 1
    assert checks["previously_attempted_tested_mask_count"] == 1
    rows[1] = fixtures.branch_row(field, hosts[1:], normals[0], 1)
    with pytest.raises(ValueError, match="independent priority"):
        gate.verify_priority_schedule(field, prior)


def test_prior_masks_are_revisited_only_when_the_globally_new_tier_is_empty(priority):
    field, _, prior = priority
    hosts = prior["host_order"]
    prior["mask_numbers"] = list(range(256))
    prior["mask_ids"] = [gate.search._mask_id(hosts, number) for number in prior["mask_numbers"]]
    field["response"]["support_mask_schedule_v1"]["previous_mask_ids"] = prior["mask_ids"]
    normals = {host: 0. if host == hosts[0] else 1. for host in hosts}
    field["response"]["support_state_search_v1"]["tested_masks"] = [
        fixtures.branch_row(field, hosts, normals, 0), fixtures.branch_row(field, hosts[1:], normals, 1)]
    checks = gate.verify_priority_schedule(field, prior)
    assert checks["globally_new_tested_mask_count"] == 0
    assert checks["previously_attempted_tested_mask_count"] == 2
    assert checks["combined_scheduling_census_is_nonexistence_proof"] is False


def test_unlisted_physical_parameter_change_cannot_hide_behind_numerical_provenance(priority):
    field, args, _ = priority
    field["parameters"]["wood_E_mpa"] = 123.
    fixtures.bind_identity(field)
    with pytest.raises(ValueError, match="every physical input"):
        gate.audit_support_priority_state(fixtures.payload(field), **args)


@pytest.mark.parametrize("mutation", ["new-field", "prior-field", "producer", "parsed-field", "body-audit"])
def test_immutable_priority_issuance_rejects_changes_during_checks(priority, monkeypatch, mutation):
    field, args, _ = priority
    path = gate.ROOT / "priority-field.json"
    path.write_bytes(fixtures.payload(field))

    def audit(parsed):
        if mutation == "new-field":
            path.write_bytes(path.read_bytes() + b"\n")
        elif mutation == "prior-field":
            args["prior_failure_path"].write_bytes(args["prior_failure_path"].read_bytes() + b"\n")
        elif mutation == "producer":
            (gate.ROOT / gate.SCHEDULE).write_text("changed")
        elif mutation == "parsed-field":
            parsed["case_id"] = "changed"
        return {gate.core.common_export.ACCEPTANCE_KEY: mutation != "body-audit", "source_sha256": {}}

    monkeypatch.setattr(gate.core.common_export, "audit_common_shaft_state", audit)
    with pytest.raises(ValueError):
        gate.audit_support_priority_state(path, **args)
