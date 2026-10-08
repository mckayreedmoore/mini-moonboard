"""Admit cumulative scheduling runs using unchanged frozen mechanics checks.

Failed ancestors supply authenticated ended mask IDs only. Their actual
policies are replayed without manufacturing an old response or receipt. Every
new q, floor/face law and132-body gate remains independent of old diagnostics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts import thin_bolted_support_priority_admission as priority

core, search = priority.core, priority.search
ROOT, PACKET = priority.ROOT, priority.PACKET
OWN = str(Path(__file__).resolve().relative_to(ROOT))
LOADED_PRODUCER_SHA256 = core.support.digest(Path(__file__))
SCHEMA = "thin_bolted_independent_support_chain_admission/v1"
SUCCESS = "independent_support_chain_face_source_map_law_and_equilibrium_checks_pass"
DRIVER = "scripts/run_thin_bolted_support_chain_frame.py"
METHOD = "scripts/thin_bolted_support_mask_chain.py"
METHOD_TEST = "tests/test_thin_bolted_support_mask_chain.py"
METHOD_RECEIPT = PACKET / "support-chain-method-v4.json"
METHOD_SCHEMA = "thin_bolted_support_chain_method/v1"
CHAIN_SCHEMA = "thin_bolted_support_mask_chain/v1"
CHAIN_METHOD = "authenticated-failed-chain-mask-deprioritization"
PRIORITY_GATE = "scripts/thin_bolted_support_priority_admission.py"
PRIORITY_GATE_SHA256 = "a9d746c8a1711477fb053532f0a17c21e84168ae5e9eac165f6c3469f750700c"
PRIORITY_ARGS = {
    "priority_driver_sha256": "5c6b7fc690f113107b3f5dcab5dabc86fb7ccf62e364c4b7f9f8a1b3370e6fd5",
    "schedule_sha256": "f4fdc453532698255c2e40aae3c78bb1f5d5c0d04d403b358039591f9b4db5c9",
    "method_receipt_path": priority.METHOD_RECEIPT,
    "method_receipt_sha256": "8635e718a4131523a3cc7cc46a7ec54f3a5d678aba42540a1b4671cb7d922141",
}
require, canonical_sha, merge_pins = core.require, core.canonical_sha, core.merge_pins
relative, verify_pins = priority.relative, priority.verify_pins


def source_pins(*, chain_driver_sha256, chain_method_sha256, method_receipt_path, method_receipt_sha256):
    receipt_path = Path(method_receipt_path).resolve()
    require(receipt_path == METHOD_RECEIPT.resolve(), "fixed chain method receipt path required")
    payload = receipt_path.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == method_receipt_sha256, "chain method receipt immutable bytes differ")
    receipt = json.loads(payload)
    require(receipt.get("schema") == METHOD_SCHEMA and receipt.get("method_checks_pass") is True
            and receipt.get("released") is False, "checked unreleased chain method receipt required")
    core.require_unreleased(receipt.get("release"))
    required = {DRIVER: chain_driver_sha256, METHOD: chain_method_sha256,
                PRIORITY_GATE: PRIORITY_GATE_SHA256, priority.DRIVER: PRIORITY_ARGS["priority_driver_sha256"],
                priority.SCHEDULE: PRIORITY_ARGS["schedule_sha256"],
                relative(PRIORITY_ARGS["method_receipt_path"]): PRIORITY_ARGS["method_receipt_sha256"]}
    require(all(receipt.get("source_sha256", {}).get(path) == sha for path, sha in required.items())
            and METHOD_TEST in receipt.get("source_sha256", {}), "chain receipt must bind all fresh and frozen producers")
    pins = merge_pins(priority.source_pins(**PRIORITY_ARGS), receipt["source_sha256"], required,
                      {OWN: LOADED_PRODUCER_SHA256, relative(receipt_path): method_receipt_sha256})
    verify_pins(pins)
    return pins


def verify_chain_execution(field, *, chain_driver_sha256, chain_method_sha256, method_receipt_path,
                           method_receipt_sha256, prior_failure_path, prior_failure_sha256):
    execution = field.get("support_mask_chain_execution", {})
    command, internal = execution.get("command"), field["support_state_search_execution"]["command"]
    require(isinstance(command, list) and len(command) >= 3 and all(isinstance(v, str) and v for v in command)
            and command[1:3] == ["-m", "scripts.run_thin_bolted_support_chain_frame"], "actual chain runner command required")
    parser = argparse.ArgumentParser(add_help=False, exit_on_error=False, allow_abbrev=False)
    parser.add_argument("--support-chain-prior-failure", type=Path)
    parser.add_argument("--support-chain-prior-sha256")
    parser.add_argument("--support-chain-method-receipt", type=Path)
    parser.add_argument("--support-chain-method-sha256")
    try:
        args, remainder = parser.parse_known_args(command[3:])
    except (argparse.ArgumentError, SystemExit) as exc:
        raise ValueError("invalid actual chain command arguments") from exc
    require(args.support_chain_prior_failure is not None and args.support_chain_method_receipt is not None
            and relative(ROOT / args.support_chain_prior_failure) == relative(prior_failure_path)
            and relative(ROOT / args.support_chain_method_receipt) == relative(method_receipt_path)
            and args.support_chain_prior_sha256 == prior_failure_sha256
            and args.support_chain_method_sha256 == method_receipt_sha256
            and command[0] == internal[0] and remainder == internal[3:],
            "actual chain command must preserve exact internal arguments and source pins")
    expected = {"loaded_driver_sha256": chain_driver_sha256, "loaded_method_sha256": chain_method_sha256,
                "method_receipt_path": relative(method_receipt_path), "method_receipt_sha256": method_receipt_sha256,
                "prior_failure_path": relative(prior_failure_path), "prior_failure_sha256": prior_failure_sha256,
                "scheduling_only": True, "prior_q_or_forces_used": False,
                "nested_support_search_execution_is_reused_internal_call": True}
    require(all(execution.get(key) == value and (not isinstance(value, bool) or execution.get(key) is value)
                for key, value in expected.items()), "fresh chain scheduling-only provenance required")
    params = {"support_mask_schedule_chain_driver_sha256": chain_driver_sha256,
              "support_mask_schedule_chain_method_sha256": chain_method_sha256,
              "support_mask_schedule_chain_method_receipt_sha256": method_receipt_sha256,
              "support_mask_schedule_chain_prior_failure_sha256": prior_failure_sha256}
    require(all(field["parameters"].get(key) == value for key, value in params.items()), "chain state must bind all new sources")
    return execution


def branch_events(field):
    """Authenticate completed callbacks and retain a real unfinished start."""
    events = field["support_state_search_execution"].get("branch_events")
    require(isinstance(events, list), "full-field wall interruption requires authenticated branch events")
    hosts = sorted(core.support.FLOOR_HOSTS)
    rows, pending = [], None
    for event in events:
        require(isinstance(event, dict), "branch event dictionary required")
        phase = event.get("phase")
        if phase == "branch_start":
            require(pending is None and event.get("pattern_index") == len(rows), "sequential unpaired branch start required")
            priority.mask_number(event, hosts)
            pending = event
        else:
            require(phase == "branch_end" and pending is not None
                    and all(event.get(key) == value for key, value in pending.items() if key != "phase"),
                    "branch end must match its actual authenticated start")
            rows.append({key: value for key, value in event.items() if key != "phase"})
            pending = None
    return rows, pending


def failed_rows(field):
    """Read actual diagnostic rows; never insert a synthetic old response."""
    response = field["response"]
    if response.get("wall_time_limit_reached") is True:
        require(response.get("termination") == "lean case wall-time limit"
                and "support_state_search_v1" not in response, "explicit full-field wall failure required")
        rows, pending = branch_events(field)
        return rows, pending, "full-field-wall-interruption"
    require(response.get("termination") in ("support-mask search budget", "support-mask search exhausted"),
            "complete mask-budget or exhaustion failure required")
    diagnostic = response.get("support_state_search_v1", {})
    hosts, rows = sorted(core.support.FLOOR_HOSTS), diagnostic.get("tested_masks")
    require(diagnostic.get("schema") == core.SEARCH_SCHEMA and diagnostic.get("method") == core.METHOD
            and diagnostic.get("host_order") == hosts and diagnostic.get("floor_activation_threshold_n") == 1e-7
            and diagnostic.get("total_possible_masks") == 256 and diagnostic.get("old_field_initialization_used") is False
            and diagnostic.get("physical_laws_changed") is False and diagnostic.get("no_fixed_point_proven") is False
            and isinstance(rows, list) and 1 <= len(rows) <= diagnostic.get("mask_budget", 0)
            and diagnostic.get("mask_budget") == field["parameters"]["support_state_search_mask_budget"]
            and all(diagnostic.get(key) is None for key in ("accepted_pattern_index", "accepted_enabled_centroid_xy_hosts",
                "accepted_disabled_centroid_xy_hosts", "final_mask_id", "final_q_canonical_sha256"))
            and all(row.get("self_consistent") is False for row in rows), "unaccepted complete support-search history required")
    if "branch_events" in field["support_state_search_execution"]:
        event_rows, pending = branch_events(field)
        require(pending is None and canonical_sha(event_rows) == canonical_sha(rows), "normal history and callbacks must agree")
    require(diagnostic.get("all_masks_visited") is (len(rows) == 256)
            and diagnostic.get("complete_enumeration") is (
                len(rows) == 256 and all(row["fixed_branch_converged"] for row in rows)), "attempted and resolved enumeration differ")
    return rows, None, "mask-budget-or-exhaustion"


def replay_choices(rows, previous_ids, hosts, pending=None):
    previous = set()
    for identity in previous_ids:
        require(isinstance(identity, str) and identity.startswith("centroid-mask-")
                and len(identity) == 22 and set(identity[14:]) <= {"0", "1"}, "complete physical prior mask ID required")
        previous.add(sum(1 << i for i, bit in enumerate(identity[14:]) if bit == "1"))
    visited, next_mask, fresh, repeated = set(), 255, 0, 0
    fresh_initialization_available = False
    for index, row in enumerate(rows):
        number = priority.mask_number(row, hosts)
        require(row.get("pattern_index") == index and number == next_mask and number not in visited,
                "branch order must match independent cumulative scheduling replay")
        require(row.get("initialization_from_previous_fresh_branch_only") is fresh_initialization_available,
                "branch initialization must use only its actual fresh predecessor")
        require(type(row.get("self_consistent")) is bool, "explicit branch consistency observation required")
        demanded = priority.demanded_number(row, hosts)
        require(row["self_consistent"] is (demanded == number), "recorded consistency must match its own resolved normal mask")
        fresh_initialization_available = row.get("fresh_original_gradient_inf_n") is not None
        visited.add(number)
        fresh += number not in previous
        repeated += number in previous
        next_mask, _ = search._next_mask(number, demanded, visited | previous, 256)
        if next_mask is None:
            next_mask, _ = search._next_mask(number, demanded, visited, 256)
        if row["self_consistent"]:
            require(index == len(rows) - 1 and pending is None, "no later branch may follow an observed fixed point")
    if pending is not None:
        require(pending["pattern_index"] == len(rows) and priority.mask_number(pending, hosts) == next_mask
                and next_mask not in visited
                and pending.get("initialization_from_previous_fresh_branch_only") is fresh_initialization_available,
                "pending start must match the actual next scheduled mask and fresh initialization")
    return {"independent_cumulative_choices_replayed": True, "globally_new_tested_mask_count": fresh,
            "previously_attempted_tested_mask_count": repeated, "old_q_or_forces_used": False,
            "combined_scheduling_census_is_nonexistence_proof": False}


def chain_metadata(chain):
    return {key: value for key, value in chain.items() if key != "source_sha256"}


def verify_chain_schedule(field, chain, *, rows=None, pending=None, require_metadata=True):
    if require_metadata:
        metadata = field["response"].get("support_mask_chain_schedule_v1")
        require(isinstance(metadata, dict) and canonical_sha(metadata) == canonical_sha(chain_metadata(chain)),
                "chain metadata must bind exact authenticated cohorts and mask union")
    if rows is None:
        rows = field["response"]["support_state_search_v1"]["tested_masks"]
    return replay_choices(rows, chain["union_mask_ids"], chain["host_order"], pending)


def leaf_prior(node):
    field, rows = node["field"], node["rows"]
    return {"path": node["path"], "sha256": node["sha256"], "canonical_sha256": node["canonical_sha256"],
            **{key: field[key] for key in core.IDENTITIES}, "host_order": sorted(core.support.FLOOR_HOSTS),
            "mask_ids": [row["mask_id"] for row in rows],
            "mask_numbers": [priority.mask_number(row, sorted(core.support.FLOOR_HOSTS)) for row in rows],
            "physical_input_signature_sha256": priority.physical_input_signature(field)}


def read_failed_chain(path, expected_sha256, field, *, chain_driver_sha256, chain_method_sha256,
                      method_receipt_path, method_receipt_sha256):
    """Authenticate a linear ancestry iteratively, then replay oldest first."""
    args = {"chain_driver_sha256": chain_driver_sha256, "chain_method_sha256": chain_method_sha256,
            "method_receipt_path": method_receipt_path, "method_receipt_sha256": method_receipt_sha256}
    signature = priority.physical_input_signature(field)
    nodes, seen, pins = [], set(), {}
    while True:
        name = relative(path)
        require(name not in seen, "failed-field lineage contains a cycle")
        seen.add(name)
        raw = (ROOT / name).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected_sha256, "failed ancestor immutable bytes differ")
        ancestor = json.loads(raw)
        core.require_unreleased(ancestor.get("release"))
        response = ancestor.get("response", {})
        require(ancestor.get("schema") == "thin_bolted_common_shaft_frame/v1"
                and ancestor.get("usable_conditional_actions") is False
                and ancestor.get("failed_response_without_recovered_actions") is True
                and ancestor.get("compatible_numerical_mvp_complete") is False and response.get("converged") is False
                and all(key not in response for key in ("q", "connector_local_force_n", "normal_contact_force_n")),
                "complete failed ancestor without accepted q or force arrays required")
        identity = {key: ancestor[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
        require(ancestor.get("state_id") == "thin-v4-" + canonical_sha(identity)[:24]
                and priority.physical_input_signature(ancestor) == signature, "ancestor state or physical inputs differ")
        core.verify_execution(ancestor, **priority.CORE_ARGS)
        rows, pending, termination = failed_rows(ancestor)
        has_priority, has_chain = "support_priority_execution" in ancestor, "support_mask_chain_execution" in ancestor
        require(not (has_priority and has_chain), "one actual outer scheduling policy per ancestor required")
        policy = "chain" if has_chain else "priority" if has_priority else "original-core"
        source = ancestor["source_sha256"]
        required = {core.DRIVER: priority.CORE_ARGS["driver_sha256"], core.SEARCH: priority.CORE_ARGS["search_sha256"],
                    relative(priority.CORE_ARGS["method_receipt_path"]): priority.CORE_ARGS["method_receipt_sha256"]}
        if policy != "original-core":
            execution = ancestor["support_mask_chain_execution" if has_chain else "support_priority_execution"]
            parent_path, parent_sha = execution["prior_failure_path"], execution["prior_failure_sha256"]
            if has_chain:
                verify_chain_execution(ancestor, **args, prior_failure_path=ROOT / parent_path, prior_failure_sha256=parent_sha)
                required.update({DRIVER: chain_driver_sha256, METHOD: chain_method_sha256,
                                 relative(method_receipt_path): method_receipt_sha256})
            else:
                priority.verify_priority_execution(ancestor, **PRIORITY_ARGS,
                    prior_failure_path=ROOT / parent_path, prior_failure_sha256=parent_sha)
                required.update({priority.DRIVER: PRIORITY_ARGS["priority_driver_sha256"],
                    priority.SCHEDULE: PRIORITY_ARGS["schedule_sha256"],
                    relative(PRIORITY_ARGS["method_receipt_path"]): PRIORITY_ARGS["method_receipt_sha256"]})
            required[relative(ROOT / parent_path)] = parent_sha
        require(all(source.get(key) == value for key, value in required.items()), "failed ancestor omits authenticated sources or parent")
        pins = merge_pins(pins, source, {name: expected_sha256})
        verify_pins(pins)
        nodes.append({"path": name, "sha256": expected_sha256, "canonical_sha256": canonical_sha(ancestor),
                      "field": ancestor, "rows": rows, "pending": pending, "termination": termination, "policy": policy})
        if policy == "original-core":
            break
        path, expected_sha256 = ROOT / parent_path, parent_sha
    cohorts, union, chain, previous = [], [], None, None
    hosts = sorted(core.support.FLOOR_HOSTS)
    for node in reversed(nodes):
        ancestor, rows, pending = node["field"], node["rows"], node["pending"]
        if node["policy"] == "original-core":
            if node["termination"] == "mask-budget-or-exhaustion":
                priority.read_prior_failure(ROOT / node["path"], node["sha256"], field)
            replay_choices(rows, [], hosts, pending)
        elif node["policy"] == "priority":
            if node["termination"] == "mask-budget-or-exhaustion":
                priority.verify_priority_schedule(ancestor, leaf_prior(previous))
            replay_choices(rows, leaf_prior(previous)["mask_ids"], hosts, pending)
        else:
            verify_chain_schedule(ancestor, chain, rows=rows, pending=pending)
        local = [row["mask_id"] for row in rows]
        cohorts.append({"field_path": node["path"], "field_sha256": node["sha256"],
            "field_canonical_sha256": node["canonical_sha256"], **{key: ancestor[key] for key in core.IDENTITIES},
            "policy": node["policy"], "local_mask_ids": local, "termination_kind": node["termination"],
            "pending_branch_start": pending})
        union.extend(identity for identity in local if identity not in union)
        chain = {"schema": CHAIN_SCHEMA, "method": CHAIN_METHOD,
            "previous_field_path": node["path"], "previous_field_sha256": node["sha256"],
            "previous_field_canonical_sha256": node["canonical_sha256"], "previous_state_id": ancestor["state_id"],
            "previous_case_id": ancestor["case_id"], "previous_accessory_placement": ancestor["accessory_placement"],
            "physical_input_signature_sha256": signature, "host_order": hosts, "union_mask_ids": union.copy(),
            "cohorts": cohorts.copy(), "scheduling_only": True, "old_q_or_forces_used": False,
            "previous_results_are_nonexistence_proof": False, "physical_laws_changed": False,
            "first_all_host_branch_remains_fresh": True, "source_sha256": pins}
        previous = node
    verify_pins(pins)
    return chain


def audit_support_chain_state(path_or_bytes, *, chain_driver_sha256, chain_method_sha256,
                              method_receipt_path, method_receipt_sha256, prior_failure_path, prior_failure_sha256):
    require(isinstance(path_or_bytes, (bytes, str, Path)), "immutable chain field bytes or path required")
    args = {"chain_driver_sha256": chain_driver_sha256, "chain_method_sha256": chain_method_sha256,
            "method_receipt_path": method_receipt_path, "method_receipt_sha256": method_receipt_sha256}
    pins = source_pins(**args)
    path = None if isinstance(path_or_bytes, bytes) else Path(path_or_bytes)
    payload = path.read_bytes() if path is not None else path_or_bytes
    field = json.loads(payload)
    before = canonical_sha(field)
    require(field.get("schema") == "thin_bolted_common_shaft_frame/v1", "fresh physical common-shaft field required")
    core.require_unreleased(field.get("release"))
    identity = {key: field[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    require(field.get("state_id") == "thin-v4-" + canonical_sha(identity)[:24], "chain field identity differs")
    internal = core.verify_execution(field, **priority.CORE_ARGS)
    actual = verify_chain_execution(field, **args, prior_failure_path=prior_failure_path, prior_failure_sha256=prior_failure_sha256)
    chain = read_failed_chain(prior_failure_path, prior_failure_sha256, field, **args)
    support_checks = core.verify_support_search(field)
    schedule_checks = verify_chain_schedule(field, chain)
    _, cache, _, layout, _, _, base_pins = core.common.read_sources()
    proof_payload = core.linear.proof_method.PROOF.read_bytes()
    require(hashlib.sha256(proof_payload).hexdigest() == core.linear.proof_method.PROOF_SHA256, "frozen paired-face proof changed")
    proof = json.loads(proof_payload)
    required = merge_pins(base_pins, proof["source_sha256"], {
        DRIVER: chain_driver_sha256, METHOD: chain_method_sha256,
        core.DRIVER: priority.CORE_ARGS["driver_sha256"], core.SEARCH: priority.CORE_ARGS["search_sha256"],
        relative(priority.CORE_ARGS["method_receipt_path"]): priority.CORE_ARGS["method_receipt_sha256"],
        relative(method_receipt_path): method_receipt_sha256, relative(prior_failure_path): prior_failure_sha256,
        core.linear.DRIVER: core.linear.DRIVER_SHA256, core.linear.METHOD: core.linear.METHOD_SHA256,
        relative(core.linear.proof_method.PROOF): core.linear.proof_method.PROOF_SHA256,
        relative(core.linear.panel_sources.OPERATORS): core.linear.panel_sources.OPERATORS_SHA,
        relative(core.linear.panel_sources.coupled.DATUMS): core.linear.panel_sources.coupled.DATUMS_SHA,
    })
    require(all(field["source_sha256"].get(key) == sha for key, sha in required.items()), "chain field omits authenticated sources")
    pins = merge_pins(pins, required, chain["source_sha256"], field["source_sha256"])
    verify_pins(pins)
    inventory = core.linear.proof_method.verify_patch_inventory(proof, cache, layout)
    mapping, q = core.linear.verify_timber_map(field, cache, core.linear.spans.read_member_span_geometry())
    floor = core.verify_floor_q_laws(field, mapping, q)
    faces = core.linear.verify_face_actions(field, proof, mapping, q)
    census = core.linear.verify_action_census(field, core.linear.panel_contact_sources())
    require(not field.get("attachment_actions") and not field.get("retained_bolt_actions"), "old bolt proxies cannot survive")
    unchanged = core.common_export.audit_common_shaft_state(field)
    require(unchanged[core.common_export.ACCEPTANCE_KEY] is True, "unchanged132-body support/load audit failed")
    pins = merge_pins(pins, unchanged["source_sha256"])
    verify_pins(pins)
    require(source_pins(**args).items() <= pins.items() and canonical_sha(field) == before,
            "sources or parsed field changed during chain admission")
    raw_sha = hashlib.sha256(payload).hexdigest()
    if path is not None:
        require(core.support.digest(path) == raw_sha, "raw chain field changed during admission")
    return {"schema": SCHEMA, SUCCESS: True, **{key: field[key] for key in core.IDENTITIES},
        "field_sha256": raw_sha, "field_canonical_sha256": before, "source_sha256": pins,
        "actual_support_mask_chain_execution": actual, "reused_internal_support_search_execution": internal,
        "failed_chain_source": chain, "chain_schedule_checks": schedule_checks, "support_search_checks": support_checks,
        "floor_q_law_checks": floor, "linear_timber_map_checks_pass": True, "linear_timber_face_checks": faces,
        "timber_contact_geometry": inventory, "complete_action_census": census, "independent_common_shaft_audit": unchanged,
        "native_CAD_K_or_response_execution": False,
        "small_motion_applicability_physical_bounds_complete_capacity_or_release_established": False,
        "release": {key: False for key in field["release"]}}
