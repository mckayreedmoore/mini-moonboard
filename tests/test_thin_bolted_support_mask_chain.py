"""Tiny fresh equilibria and authenticated synthetic lineage; no candidate run."""

import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import block_diag, csr_matrix

from scripts import thin_bolted_support_mask_chain as chain


def reuse(name):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location(name + "_reused", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


priority_fixtures = reuse("test_thin_bolted_support_priority_admission")
sources, priority = priority_fixtures.sources, priority_fixtures.priority


def eight_host_fixture():
    # Extend the existing exact two-host coupling by six independent positive
    # compression/zero horizontal-load hosts. No original geometry is used.
    K, applied, groups, contacts, tangents = reuse("test_thin_bolted_support_state_search").cycling_fixture()
    hosts = sorted(chain.lineage.core.support.FLOOR_HOSTS)
    replace = {"foot-A": hosts[0], "foot-B": hosts[1]}
    for row in [*contacts, *tangents]:
        row["id"] = row["id"].replace(row["first"], replace[row["first"]])
        row["first"] = replace[row["first"]]
        row["B"] = csr_matrix(np.pad(row["B"].toarray(), ((0, 0), (0, 18))))
    K = block_diag([K, 5000. * np.eye(18)], format="csr")
    applied = np.r_[applied, np.tile([5000., 0., 0.], 6)]
    for index, host in enumerate(hosts[2:]):
        base = 6 + 3 * index
        for corner in range(4):
            B = np.zeros((1, 24)); B[0, base] = 1.
            contacts.append({"id": host + f"/floor-{corner}", "kind": "floor_normal",
                             "first": host, "second": "floor", "B": csr_matrix(B), "stiffness": 25000.})
        for component in range(2):
            B = np.zeros((1, 24)); B[0, base + 1 + component] = 1.
            tangents.append({"id": host + f"/no-slip-{component}", "kind": "floor_tangent",
                             "first": host, "B": csr_matrix(B), "stiffness": 100000.})
    return K, applied, groups, contacts, tangents


def plain(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, dict): return {key: plain(item) for key, item in value.items()}
    if isinstance(value, list): return [plain(item) for item in value]
    return value


def set_budget(field, budget=2):
    execution = field["support_state_search_execution"]
    execution["mask_budget"] = budget
    execution["command"] += ["--support-mask-budget", str(budget)]
    field["parameters"]["support_state_search_mask_budget"] = budget


@pytest.fixture
def two_failures(priority, monkeypatch):
    """Reuse isolated synthetic source fixtures with actual tiny branch laws."""
    field, priority_args, _ = priority
    gate = chain.lineage
    old = priority_fixtures.gate
    monkeypatch.setattr(gate, "ROOT", old.ROOT)
    monkeypatch.setattr(gate, "PRIORITY_ARGS", {key: priority_args[key] for key in (
        "priority_driver_sha256", "schedule_sha256", "method_receipt_path", "method_receipt_sha256")})
    reference = copy.deepcopy(field)
    reference["counts"] = {"dofs": 24, "structural_bodies": 8}
    hosts = sorted(gate.core.support.FLOOR_HOSTS)
    reference["body_identities"] = hosts
    reference["finished_floor_footprints"] = [{"member": host} for host in hosts]
    reference["floor_actions"] = []
    reference.update(usable_conditional_actions=False, failed_response_without_recovered_actions=True,
                     compatible_numerical_mvp_complete=False)
    set_budget(reference)
    core_events = []
    first = chain.scheduling.FROZEN_CORE_SOLVE(*eight_host_fixture(), mask_budget=2, branch_observer=core_events.append)
    root = copy.deepcopy(reference)
    root.pop("support_priority_execution")
    root["source_sha256"].pop(gate.relative(priority_args["prior_failure_path"]))
    root["parameters"] = {key: value for key, value in root["parameters"].items() if not key.startswith("support_priority_")}
    root["response"] = plain(first)
    root["support_state_search_execution"]["branch_events"] = core_events
    priority_fixtures.fixtures.bind_identity(root)
    root_path = priority_args["prior_failure_path"]
    root_path.write_bytes(priority_fixtures.fixtures.payload(root))
    root_sha = gate.core.support.digest(root_path)
    root_ids = [row["mask_id"] for row in first["support_state_search_v1"]["tested_masks"]]
    second_events = []
    with chain.scheduling.preferred_unvisited_masks({"previous_host_order": hosts, "previous_mask_ids": root_ids}):
        second = chain.scheduling.FROZEN_CORE_SOLVE(*eight_host_fixture(), mask_budget=2, branch_observer=second_events.append)
    leaf = copy.deepcopy(reference)
    leaf["response"] = plain(second)
    leaf["support_state_search_execution"]["branch_events"] = second_events
    leaf["source_sha256"][gate.relative(root_path)] = root_sha
    leaf["parameters"]["support_priority_prior_failure_sha256"] = root_sha
    execution = leaf["support_priority_execution"]
    execution["prior_failure_sha256"] = root_sha
    internal = leaf["support_state_search_execution"]["command"]
    execution["command"] = [internal[0], "-m", "scripts.run_thin_bolted_support_priority_frame",
        "--support-prior-failure", str(root_path), "--support-prior-sha256", root_sha,
        "--support-priority-method-receipt", str(priority_args["method_receipt_path"]),
        "--support-priority-method-sha256", priority_args["method_receipt_sha256"], *internal[3:]]
    prior, _ = old.read_prior_failure(root_path, root_sha, leaf)
    leaf["response"]["support_mask_schedule_v1"] = {
        "schema": old.SCHEDULE_SCHEMA, "method": old.SCHEDULE_METHOD,
        "previous_field_path": prior["path"], "previous_field_sha256": prior["sha256"],
        "previous_field_canonical_sha256": prior["canonical_sha256"], "previous_state_id": prior["state_id"],
        "previous_case_id": prior["case_id"], "previous_accessory_placement": prior["accessory_placement"],
        "previous_host_order": hosts, "previous_mask_ids": prior["mask_ids"],
        "physical_input_signature_sha256": prior["physical_input_signature_sha256"],
        "scheduling_only": True, "old_q_or_forces_used": False, "previous_results_are_nonexistence_proof": False,
        "physical_laws_changed": False, "first_all_host_branch_remains_fresh": True}
    priority_fixtures.fixtures.bind_identity(leaf)
    leaf_path = old.ROOT / "priority-failed.json"
    leaf_path.write_bytes(priority_fixtures.fixtures.payload(leaf))
    # The isolated source graph is verified by the real lineage reader. The
    # actual frozen engine retains its repository source checks separately.
    def synthetic_pins(value=None):
        if value is None: return {}
        chain._validate_union(value)
        gate.verify_pins(value["source_sha256"])
        return value["source_sha256"].copy()
    monkeypatch.setattr(chain, "source_pins", synthetic_pins)
    kwargs = {"chain_driver_sha256": "synthetic-chain-driver", "method_receipt_path": old.ROOT / "chain-receipt.json",
              "method_receipt_sha256": "synthetic-chain-receipt"}
    return leaf_path, gate.core.support.digest(leaf_path), kwargs, root, leaf


def test_two_authenticated_failures_then_fresh_hand_equilibrium(two_failures):
    path, sha, kwargs, root, leaf = two_failures
    previous = chain.load_failed_chain(path, sha, **kwargs)
    assert [row["policy"] for row in previous["cohorts"]] == ["original-core", "priority"]
    assert previous["union_mask_ids"] == ["centroid-mask-11111111", "centroid-mask-00111111", "centroid-mask-01111111"]
    assert all(row["termination_kind"] == "mask-budget-or-exhaustion" for row in previous["cohorts"])
    assert all(row["pending_branch_start"] is None for row in previous["cohorts"])
    assert previous["physical_input_signature_sha256"] == chain.scheduling.physical_input_signature_sha256(leaf)
    events = []
    result = chain.compatible_contact_solve(*eight_host_fixture(), previous_chain=previous,
                                          mask_budget=2, branch_observer=events.append)
    assert result["converged"]
    assert [row["mask_id"] for row in result["support_state_search_v1"]["tested_masks"]] == [
        "centroid-mask-11111111", "centroid-mask-10111111"]
    assert result["gradient_inf_n"] < 1e-5
    K, applied, _, _, _ = eight_host_fixture()
    diagonal = np.array([100000., 0., 100000., 0., 100000., 0., *np.tile([100000., 100000., 100000.], 6)])
    np.testing.assert_allclose(result["q"], np.linalg.solve(K.toarray() + np.diag(diagonal), applied), atol=2e-10)
    assert not events[0]["initialization_from_previous_fresh_branch_only"]
    assert "support_mask_schedule_v1" not in result
    assert result["support_mask_chain_schedule_v1"] == chain.chain_metadata(previous)
    assert "diagnostic_last_q" not in previous and "floor_normal_force_n_by_host" not in previous
    assert root["response"]["converged"] is False and leaf["response"]["converged"] is False


@pytest.mark.parametrize("mutation", ["raw-sha", "ancestor", "policy", "physics", "prior-masks", "accepted-q"])
def test_forged_ancestry_policy_or_prior_masks_reject_before_execution(two_failures, mutation):
    path, sha, kwargs, _, leaf = two_failures
    if mutation == "raw-sha":
        sha = "0" * 64
    else:
        if mutation == "ancestor": leaf["support_priority_execution"]["prior_failure_path"] = "missing.json"
        if mutation == "policy": leaf["support_priority_execution"]["command"][2] = "scripts.run_thin_bolted_support_search_frame"
        if mutation == "physics": leaf["parameters"]["floor_corner_contact_n_mm"] = 25001.
        if mutation == "prior-masks": leaf["response"]["support_mask_schedule_v1"]["previous_mask_ids"].pop()
        if mutation == "accepted-q": leaf["response"]["q"] = [0.] * 24
        priority_fixtures.fixtures.bind_identity(leaf)
        path.write_bytes(priority_fixtures.fixtures.payload(leaf))
        sha = chain.lineage.core.support.digest(path)
    with pytest.raises((ValueError, OSError)):
        chain.load_failed_chain(path, sha, **kwargs)


@pytest.mark.parametrize("mutation", ["insert", "omit", "order", "policy", "leaf"])
def test_mutated_cumulative_union_or_cohort_rejects_before_core_solve(two_failures, mutation):
    path, sha, kwargs, _, _ = two_failures
    previous = chain.load_failed_chain(path, sha, **kwargs)
    if mutation == "insert": previous["union_mask_ids"].append("centroid-mask-00000000")
    if mutation == "omit": previous["union_mask_ids"].pop(1)
    if mutation == "order": previous["union_mask_ids"].reverse()
    if mutation == "policy": previous["cohorts"][0]["policy"] = "invented-policy"
    if mutation == "leaf": previous["previous_state_id"] = "forged-state"
    with pytest.raises(ValueError):
        chain.compatible_contact_solve(*eight_host_fixture(), previous_chain=previous, mask_budget=2)


def test_full_field_wall_cohort_keeps_ended_masks_and_real_pending_start(two_failures):
    path, _, kwargs, _, leaf = two_failures
    events = leaf["support_state_search_execution"]["branch_events"]
    leaf["support_state_search_execution"]["branch_events"] = events[:3]
    leaf["response"] = {"converged": False, "termination": "lean case wall-time limit",
        "wall_time_limit_reached": True, "diagnostic_last_q": ["unaccepted and unused"]}
    path.write_bytes(priority_fixtures.fixtures.payload(leaf))
    previous = chain.load_failed_chain(path, chain.lineage.core.support.digest(path), **kwargs)
    cohort = previous["cohorts"][-1]
    assert cohort["termination_kind"] == "full-field-wall-interruption"
    assert cohort["local_mask_ids"] == ["centroid-mask-11111111"]
    assert cohort["pending_branch_start"]["mask_id"] == "centroid-mask-01111111"
    assert previous["union_mask_ids"] == ["centroid-mask-11111111", "centroid-mask-00111111"]


@pytest.mark.parametrize("mutation", ["end-before-start", "mismatched-end", "pending-mask", "sidecar-only"])
def test_wall_trace_mutations_do_not_manufacture_completed_masks(two_failures, mutation):
    path, _, kwargs, _, leaf = two_failures
    events = leaf["support_state_search_execution"]["branch_events"][:3]
    leaf["response"] = {"converged": False, "termination": "lean case wall-time limit", "wall_time_limit_reached": True}
    if mutation == "end-before-start": events = events[1:]
    if mutation == "mismatched-end": events[1]["selection_reason"] = "forged"
    if mutation == "pending-mask": events[2]["mask_id"] = "centroid-mask-00000000"
    leaf["support_state_search_execution"]["branch_events"] = events
    if mutation == "sidecar-only": leaf = {"schema": "thin_bolted_support_priority_interrupted/v1"}
    path.write_bytes(priority_fixtures.fixtures.payload(leaf))
    with pytest.raises((ValueError, KeyError)):
        chain.load_failed_chain(path, chain.lineage.core.support.digest(path), **kwargs)


def test_current_physical_inputs_and_external_q_remain_independently_guarded(two_failures):
    path, sha, kwargs, _, leaf = two_failures
    previous = chain.load_failed_chain(path, sha, **kwargs)
    chain.validate_current_report(leaf, previous)
    changed = copy.deepcopy(leaf)
    changed["parameters"]["floor_no_slip_xy_penalty_n_mm"] = 99999.
    with pytest.raises(ValueError, match="unchanged complete physical inputs"):
        chain.validate_current_report(changed, previous)
    with pytest.raises(ValueError, match="external q"):
        chain.compatible_contact_solve(*eight_host_fixture(), previous_chain=previous,
                                      mask_budget=2, warm_q=np.zeros(24))
