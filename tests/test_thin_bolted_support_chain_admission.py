"""Cumulative lineage/command/wall coupons without candidate admission or solve."""

import importlib.util
from pathlib import Path

import pytest

from scripts import thin_bolted_support_chain_admission as gate

spec = importlib.util.spec_from_file_location(
    "support_priority_admission_fixtures", Path(__file__).with_name("test_thin_bolted_support_priority_admission.py"))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
sources, priority_fixture = fixtures.sources, fixtures.priority


def source_args(args):
    return {key: args[key] for key in ("chain_driver_sha256", "chain_method_sha256",
                                      "method_receipt_path", "method_receipt_sha256")}


def point_to(field, path, sha):
    execution = field["support_mask_chain_execution"]
    execution.update(prior_failure_path=gate.relative(path), prior_failure_sha256=sha)
    execution["command"][4] = str(path)
    execution["command"][6] = sha
    field["parameters"]["support_mask_schedule_chain_prior_failure_sha256"] = sha
    field["source_sha256"][gate.relative(path)] = sha
    fixtures.fixtures.bind_identity(field)


@pytest.fixture
def chain(priority_fixture, monkeypatch):
    field, priority_args, _ = priority_fixture
    monkeypatch.setattr(gate, "ROOT", gate.priority.ROOT)
    monkeypatch.setattr(gate, "PRIORITY_GATE_SHA256", gate.priority.LOADED_PRODUCER_SHA256)
    monkeypatch.setattr(gate, "PRIORITY_ARGS", {key: priority_args[key] for key in (
        "priority_driver_sha256", "schedule_sha256", "method_receipt_path", "method_receipt_sha256")})
    original_path = priority_args["prior_failure_path"]
    original = gate.json.loads(original_path.read_bytes())
    original["response"]["termination"] = "support-mask search budget"
    original_path.write_bytes(fixtures.fixtures.payload(original))
    original_sha = gate.core.support.digest(original_path)
    field["support_priority_execution"]["prior_failure_sha256"] = original_sha
    field["support_priority_execution"]["command"][6] = original_sha
    field["parameters"]["support_priority_prior_failure_sha256"] = original_sha
    field["source_sha256"][gate.relative(original_path)] = original_sha
    prior, _ = gate.priority.read_prior_failure(original_path, original_sha, field)
    field["response"]["support_mask_schedule_v1"].update(
        previous_field_sha256=original_sha, previous_field_canonical_sha256=prior["canonical_sha256"])
    fixtures.fixtures.bind_identity(field)
    predecessor = fixtures.failed_previous(field)
    predecessor["response"]["termination"] = "support-mask search budget"
    predecessor_path = gate.ROOT / "priority-failed.json"
    predecessor_path.write_bytes(fixtures.fixtures.payload(predecessor))
    predecessor_sha = gate.core.support.digest(predecessor_path)
    for key in list(field["parameters"]):
        if key.startswith("support_priority_"):
            field["parameters"].pop(key)
    field.pop("support_priority_execution")
    field["response"].pop("support_mask_schedule_v1")
    pins = gate.priority.source_pins(**gate.PRIORITY_ARGS)
    for name in (gate.OWN, gate.DRIVER, gate.METHOD, gate.METHOD_TEST):
        path = gate.ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic chain source: " + name)
        pins[name] = gate.core.support.digest(path)
    monkeypatch.setattr(gate, "LOADED_PRODUCER_SHA256", pins[gate.OWN])
    receipt_path = gate.ROOT / "chain-receipt.json"
    receipt_path.write_bytes(fixtures.fixtures.payload({"schema": gate.METHOD_SCHEMA,
        "method_checks_pass": True, "released": False, "release": dict.fromkeys(gate.core.RELEASE_KEYS, False),
        "source_sha256": pins}))
    monkeypatch.setattr(gate, "METHOD_RECEIPT", receipt_path)
    args = {"chain_driver_sha256": pins[gate.DRIVER], "chain_method_sha256": pins[gate.METHOD],
        "method_receipt_path": receipt_path, "method_receipt_sha256": gate.core.support.digest(receipt_path),
        "prior_failure_path": predecessor_path, "prior_failure_sha256": predecessor_sha}
    inner = field["support_state_search_execution"]["command"]
    field["support_mask_chain_execution"] = {
        "command": [inner[0], "-m", "scripts.run_thin_bolted_support_chain_frame",
            "--support-chain-prior-failure", str(predecessor_path), "--support-chain-prior-sha256", predecessor_sha,
            "--support-chain-method-receipt", str(receipt_path),
            "--support-chain-method-sha256", args["method_receipt_sha256"], *inner[3:]],
        "loaded_driver_sha256": args["chain_driver_sha256"], "loaded_method_sha256": args["chain_method_sha256"],
        "method_receipt_path": gate.relative(receipt_path), "method_receipt_sha256": args["method_receipt_sha256"],
        "prior_failure_path": gate.relative(predecessor_path), "prior_failure_sha256": predecessor_sha,
        "scheduling_only": True, "prior_q_or_forces_used": False,
        "nested_support_search_execution_is_reused_internal_call": True}
    field["parameters"].update({"support_mask_schedule_chain_driver_sha256": args["chain_driver_sha256"],
        "support_mask_schedule_chain_method_sha256": args["chain_method_sha256"],
        "support_mask_schedule_chain_method_receipt_sha256": args["method_receipt_sha256"],
        "support_mask_schedule_chain_prior_failure_sha256": predecessor_sha})
    field["source_sha256"].update(gate.source_pins(**source_args(args)))
    field["source_sha256"][gate.relative(predecessor_path)] = predecessor_sha
    fixtures.fixtures.bind_identity(field)
    ancestry = gate.read_failed_chain(predecessor_path, predecessor_sha, field, **source_args(args))
    field["response"]["support_mask_chain_schedule_v1"] = gate.chain_metadata(ancestry)
    monkeypatch.setattr(gate.priority, "audit_support_priority_state", lambda *_a, **_k: pytest.fail("old full priority gate called"))
    return field, args, ancestry


def test_distinct_chain_receipt_binds_union_source_and_new_final_q(chain):
    field, args, ancestry = chain
    result = gate.audit_support_chain_state(fixtures.fixtures.payload(field), **args)
    assert result[gate.SUCCESS] is True and result["schema"] == gate.SCHEMA
    assert [row["policy"] for row in ancestry["cohorts"]] == ["original-core", "priority"]
    assert ancestry["union_mask_ids"] == ["centroid-mask-11111111"]
    assert result["actual_support_mask_chain_execution"]["command"][2] == "scripts.run_thin_bolted_support_chain_frame"
    assert result["support_search_checks"]["final_q_canonical_sha256"] == gate.canonical_sha(field["response"]["q"])
    assert all(value is False for value in result["release"].values())


def test_repeated_chain_descendants_retain_local_cohorts_and_deterministic_union(chain):
    field, args, ancestry = chain
    for index in range(2):
        failed = fixtures.failed_previous(field)
        failed["response"]["termination"] = "support-mask search budget"
        path = gate.ROOT / f"chain-failed-{index}.json"
        path.write_bytes(fixtures.fixtures.payload(failed))
        sha = gate.core.support.digest(path)
        point_to(field, path, sha)
        args.update(prior_failure_path=path, prior_failure_sha256=sha)
        ancestry = gate.read_failed_chain(path, sha, field, **source_args(args))
        field["response"]["support_mask_chain_schedule_v1"] = gate.chain_metadata(ancestry)
        field["source_sha256"].update(ancestry["source_sha256"])
    assert [row["policy"] for row in ancestry["cohorts"]] == ["original-core", "priority", "chain", "chain"]
    assert len(ancestry["union_mask_ids"]) == 1
    assert gate.audit_support_chain_state(fixtures.fixtures.payload(field), **args)[gate.SUCCESS] is True


def failed_masks(field, numbers, demands):
    hosts = sorted(gate.core.support.FLOOR_HOSTS)
    rows = [fixtures.fixtures.branch_row(field, gate.search._enabled(hosts, number),
        {host: float(demand & (1 << i) != 0) for i, host in enumerate(hosts)}, index)
        for index, (number, demand) in enumerate(zip(numbers, demands, strict=True))]
    field["response"]["support_state_search_v1"]["tested_masks"] = rows
    return rows


def test_union_skips_both_original_and_priority_masks_and_admits_only_fresh_final_q(chain):
    field, args, ancestry = chain
    original_path = gate.ROOT / ancestry["cohorts"][0]["field_path"]
    original = gate.json.loads(original_path.read_bytes())
    failed_masks(original, [255, 254], [254, 255])
    original_path.write_bytes(fixtures.fixtures.payload(original))
    original_sha = gate.core.support.digest(original_path)
    prior, _ = gate.priority.read_prior_failure(original_path, original_sha, field)
    path = args["prior_failure_path"]
    failed = gate.json.loads(path.read_bytes())
    failed["support_priority_execution"]["prior_failure_sha256"] = original_sha
    failed["support_priority_execution"]["command"][6] = original_sha
    failed["parameters"]["support_priority_prior_failure_sha256"] = original_sha
    failed["source_sha256"][gate.relative(original_path)] = original_sha
    failed["response"]["support_mask_schedule_v1"].update(previous_field_sha256=original_sha,
        previous_field_canonical_sha256=prior["canonical_sha256"], previous_mask_ids=prior["mask_ids"])
    failed_masks(failed, [255, 253], [254, 255])
    fixtures.fixtures.bind_identity(failed)
    path.write_bytes(fixtures.fixtures.payload(failed))
    sha = gate.core.support.digest(path)
    point_to(field, path, sha)
    args["prior_failure_sha256"] = sha
    field["source_sha256"][gate.relative(original_path)] = original_sha
    ancestry = gate.read_failed_chain(path, sha, field, **source_args(args))
    assert ancestry["union_mask_ids"] == [gate.search._mask_id(ancestry["host_order"], i) for i in (255, 254, 253)]
    rows = failed_masks(field, [255, 251], [254, 251])
    _, q = gate.core.linear.verify_timber_map(field, {}, {})
    fixtures.fixtures.apply_final_normal_state(field, q, rows[-1]["floor_normal_force_n_by_host"],
        rows[-1]["enabled_centroid_xy_hosts"], rows)
    field["response"]["support_mask_chain_schedule_v1"] = gate.chain_metadata(ancestry)
    checks = gate.audit_support_chain_state(fixtures.fixtures.payload(field), **args)
    assert checks[gate.SUCCESS] is True
    assert checks["chain_schedule_checks"]["globally_new_tested_mask_count"] == 1
    assert checks["chain_schedule_checks"]["previously_attempted_tested_mask_count"] == 1
    assert checks["support_search_checks"]["final_mask_id"] == "centroid-mask-11011111"
    assert checks["support_search_checks"]["final_q_canonical_sha256"] == gate.canonical_sha(q.tolist())


@pytest.mark.parametrize("all_prior", [False, True])
def test_unresolved_branch_follows_new_tier_then_local_fallback_without_acceptance_claim(chain, all_prior):
    field, _, _ = chain
    hosts = sorted(gate.core.support.FLOOR_HOSTS)
    previous = list(range(256)) if all_prior else [255, 254]
    next_mask = 254 if all_prior else 253
    rows = failed_masks(field, [255, next_mask], [255, next_mask])
    rows[0].update(fixed_branch_converged=False, self_consistent=False,
        fresh_original_gradient_inf_n=None, floor_normal_force_n_by_host=None, demanded_enabled_centroid_xy_hosts=None)
    rows[1]["initialization_from_previous_fresh_branch_only"] = False
    result = gate.replay_choices(rows, [gate.search._mask_id(hosts, mask) for mask in previous], hosts)
    assert result["combined_scheduling_census_is_nonexistence_proof"] is False
    assert result["previously_attempted_tested_mask_count"] == (2 if all_prior else 1)


@pytest.mark.parametrize("policy", ["original-core", "priority"])
def test_failed_ancestors_cannot_claim_historical_or_external_first_initialization(chain, policy):
    field, args, ancestry = chain
    path = gate.ROOT / next(row["field_path"] for row in ancestry["cohorts"] if row["policy"] == policy)
    failed = gate.json.loads(path.read_bytes())
    failed["response"]["support_state_search_v1"]["tested_masks"][0]["initialization_from_previous_fresh_branch_only"] = True
    path.write_bytes(fixtures.fixtures.payload(failed))
    with pytest.raises(ValueError, match="initialization"):
        gate.read_failed_chain(path, gate.core.support.digest(path), field, **source_args(args))


def event_pair(row):
    keys = ("pattern_index", "mask_id", "enabled_centroid_xy_hosts", "disabled_centroid_xy_hosts",
            "initialization_from_previous_fresh_branch_only")
    return [{"phase": "branch_start", **{key: row[key] for key in keys}}, {"phase": "branch_end", **row}]


def test_full_field_wall_history_retains_ended_masks_and_excludes_pending_start(chain):
    field, args, _ = chain
    path = args["prior_failure_path"]
    failed = gate.json.loads(path.read_bytes())
    row = failed["response"]["support_state_search_v1"]["tested_masks"][0]
    failed["response"].pop("support_state_search_v1")
    failed["response"].update(wall_time_limit_reached=True, termination="lean case wall-time limit")
    hosts = row["enabled_centroid_xy_hosts"]
    pending_row = fixtures.fixtures.branch_row(field, hosts[1:], row["floor_normal_force_n_by_host"], 1)
    pending = event_pair(pending_row)[0]
    failed["support_state_search_execution"]["branch_events"] = [*event_pair(row), pending]
    path.write_bytes(fixtures.fixtures.payload(failed))
    sha = gate.core.support.digest(path)
    point_to(field, path, sha)
    ancestry = gate.read_failed_chain(path, sha, field, **source_args(args))
    cohort = ancestry["cohorts"][-1]
    assert cohort["termination_kind"] == "full-field-wall-interruption"
    assert cohort["pending_branch_start"] == pending
    assert cohort["local_mask_ids"] == ["centroid-mask-11111111"]
    assert pending["mask_id"] not in ancestry["union_mask_ids"]


@pytest.mark.parametrize("change_metadata", [False, True])
def test_repeated_chain_wall_source_binds_exact_prior_cohorts(change_metadata, chain):
    field, args, ancestry = chain
    failed = fixtures.failed_previous(field)
    row = failed["response"].pop("support_state_search_v1")["tested_masks"][0]
    failed["response"].update(wall_time_limit_reached=True, termination="lean case wall-time limit")
    failed["support_state_search_execution"]["branch_events"] = event_pair(row)
    if change_metadata:
        failed["response"]["support_mask_chain_schedule_v1"]["union_mask_ids"] = []
    path = gate.ROOT / "chain-wall-failed.json"
    path.write_bytes(fixtures.fixtures.payload(failed))
    sha = gate.core.support.digest(path)
    if change_metadata:
        with pytest.raises(ValueError, match="exact authenticated cohorts"):
            gate.read_failed_chain(path, sha, field, **source_args(args))
    else:
        chain = gate.read_failed_chain(path, sha, field, **source_args(args))
        assert chain["cohorts"][:-1] == ancestry["cohorts"]
        assert chain["cohorts"][-1]["termination_kind"] == "full-field-wall-interruption"


@pytest.mark.parametrize("mutation", ["pending-mask", "unpaired-end", "different-start", "sidecar"])
def test_wall_sources_do_not_manufacture_complete_state_or_completed_branches(chain, mutation):
    field, args, _ = chain
    path = args["prior_failure_path"]
    failed = gate.json.loads(path.read_bytes())
    row = failed["response"]["support_state_search_v1"]["tested_masks"][0]
    events = event_pair(row)
    failed["response"].pop("support_state_search_v1")
    failed["response"].update(wall_time_limit_reached=True, termination="lean case wall-time limit")
    if mutation == "pending-mask":
        events.append({**events[0], "pattern_index": 1})
    elif mutation == "unpaired-end":
        events.pop(0)
    elif mutation == "different-start":
        events[0]["initialization_from_previous_fresh_branch_only"] = True
    else:
        failed["schema"] = "thin_bolted_support_priority_interrupted/v1"
    failed["support_state_search_execution"]["branch_events"] = events
    path.write_bytes(fixtures.fixtures.payload(failed))
    with pytest.raises(ValueError):
        gate.read_failed_chain(path, gate.core.support.digest(path), field, **source_args(args))


@pytest.mark.parametrize("mutation", ["union", "cohort", "top-command", "inner-args", "source", "physics", "failed-q", "predecessor"])
def test_chain_provenance_cannot_alias_older_admission_or_lose_ancestors(chain, mutation):
    field, args, _ = chain
    if mutation == "union":
        field["response"]["support_mask_chain_schedule_v1"]["union_mask_ids"] = []
    elif mutation == "cohort":
        field["response"]["support_mask_chain_schedule_v1"]["cohorts"].pop(0)
    elif mutation == "top-command":
        field["support_mask_chain_execution"]["command"][2] = "scripts.run_thin_bolted_support_priority_frame"
    elif mutation == "inner-args":
        field["support_mask_chain_execution"]["command"] += ["--cases", "a12-front"]
    elif mutation == "source":
        field["source_sha256"].pop(gate.METHOD)
    elif mutation == "physics":
        field["parameters"]["wood_E_mpa"] = 1.
        fixtures.fixtures.bind_identity(field)
    else:
        path = args["prior_failure_path"]
        failed = gate.json.loads(path.read_bytes())
        if mutation == "failed-q":
            failed["response"]["q"] = []
        else:
            failed["support_priority_execution"]["prior_failure_path"] = "missing.json"
        path.write_bytes(fixtures.fixtures.payload(failed))
        sha = gate.core.support.digest(path)
        point_to(field, path, sha)
        args["prior_failure_sha256"] = sha
    with pytest.raises((ValueError, FileNotFoundError)):
        gate.audit_support_chain_state(fixtures.fixtures.payload(field), **args)


@pytest.mark.parametrize("mutation", ["raw-current", "raw-ancestor", "source", "parsed-current", "body-check"])
def test_all_raw_ancestors_and_sources_remain_immutable_through_admission(chain, monkeypatch, mutation):
    field, args, ancestry = chain
    path = gate.ROOT / "current-chain-field.json"
    path.write_bytes(fixtures.fixtures.payload(field))

    def audit(parsed):
        if mutation == "raw-current":
            path.write_bytes(path.read_bytes() + b"\n")
        elif mutation == "raw-ancestor":
            ancestor = gate.ROOT / ancestry["cohorts"][0]["field_path"]
            ancestor.write_bytes(ancestor.read_bytes() + b"\n")
        elif mutation == "source":
            (gate.ROOT / gate.METHOD).write_text("changed source")
        elif mutation == "parsed-current":
            parsed["case_id"] = "another case"
        return {gate.core.common_export.ACCEPTANCE_KEY: mutation != "body-check", "source_sha256": {}}

    monkeypatch.setattr(gate.core.common_export, "audit_common_shaft_state", audit)
    with pytest.raises(ValueError):
        gate.audit_support_chain_state(path, **args)
