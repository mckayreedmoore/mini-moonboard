"""Admit scheduling-only priority runs without relabelling frozen receipts.

Previous failed bytes supply discrete mask IDs only. The actual outer command
and selector are separately authenticated; all coordinate, action and body
checks reuse frozen pure functions on the unchanged new field. No K/CAD/solve.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts import thin_bolted_support_search_admission as core
from scripts import thin_bolted_support_state_search as search

ROOT, PACKET = core.ROOT, core.PACKET
OWN = str(Path(__file__).resolve().relative_to(ROOT))
LOADED_PRODUCER_SHA256 = core.support.digest(Path(__file__))
SCHEMA = "thin_bolted_independent_support_priority_admission/v1"
SUCCESS = "independent_support_priority_face_source_map_law_and_equilibrium_checks_pass"
DRIVER = "scripts/run_thin_bolted_support_priority_frame.py"
SCHEDULE = "scripts/thin_bolted_support_mask_schedule.py"
SCHEDULE_TEST = "tests/test_thin_bolted_support_mask_schedule.py"
METHOD_RECEIPT = PACKET / "support-priority-method-v4.json"
METHOD_SCHEMA = "thin_bolted_support_priority_method/v1"
SCHEDULE_SCHEMA = "thin_bolted_support_mask_schedule/v1"
SCHEDULE_METHOD = "authenticated-prior-mask-deprioritization"
CORE_GATE = "scripts/thin_bolted_support_search_admission.py"
CORE_GATE_SHA256 = "c7a70cebfe3640b82a151e358d32d0826d2c14b4d881059ed6c48a1c1a1cba84"
CORE_ARGS = {
    "driver_sha256": "8c4dc80937a4c6d1e45ae8451835f5ec589c6ce871d531a4678e9ec52e688634",
    "search_sha256": "c162d296306a263be4e6769c4249abf6491512e8f7d9af323ab2e9b10b1018e8",
    "method_receipt_path": core.METHOD_RECEIPT,
    "method_receipt_sha256": "3cbff2407511cfbf31a47d04819d1c851df9c0822c21d8fad64af912e307fda9",
}
require, canonical_sha, merge_pins = core.require, core.canonical_sha, core.merge_pins


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT))


def verify_pins(pins):
    for path, sha in pins.items():
        require(isinstance(path, str) and not Path(path).is_absolute() and ".." not in Path(path).parts
                and isinstance(sha, str) and len(sha) == 64 and core.support.digest(ROOT / path) == sha,
                "priority admission source changed: " + str(path))


def source_pins(*, priority_driver_sha256, schedule_sha256, method_receipt_path, method_receipt_sha256):
    receipt_path = Path(method_receipt_path).resolve()
    require(receipt_path == METHOD_RECEIPT.resolve(), "fresh priority method receipt path required")
    payload = receipt_path.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == method_receipt_sha256, "priority method receipt immutable bytes differ")
    receipt = json.loads(payload)
    require(receipt.get("schema") == METHOD_SCHEMA and receipt.get("method_checks_pass") is True
            and receipt.get("released") is False, "checked unreleased priority method receipt required")
    core.require_unreleased(receipt.get("release"))
    required = {DRIVER: priority_driver_sha256, SCHEDULE: schedule_sha256, CORE_GATE: CORE_GATE_SHA256,
                core.DRIVER: CORE_ARGS["driver_sha256"], core.SEARCH: CORE_ARGS["search_sha256"],
                relative(CORE_ARGS["method_receipt_path"]): CORE_ARGS["method_receipt_sha256"]}
    require(all(receipt.get("source_sha256", {}).get(path) == sha for path, sha in required.items())
            and SCHEDULE_TEST in receipt.get("source_sha256", {}), "priority receipt must bind all fresh and frozen producers")
    pins = merge_pins(core.source_pins(**CORE_ARGS), receipt["source_sha256"], required,
                      {OWN: LOADED_PRODUCER_SHA256, relative(receipt_path): method_receipt_sha256})
    verify_pins(pins)
    return pins


def mask_number(row, hosts):
    enabled = core.host_mask(row["enabled_centroid_xy_hosts"], hosts, "ordered unique support mask hosts required")
    disabled = core.host_mask(row["disabled_centroid_xy_hosts"], hosts, "ordered unique disabled support hosts required")
    number = sum(1 << i for i, host in enumerate(hosts) if host in enabled)
    identity = "centroid-mask-" + "".join("1" if host in enabled else "0" for host in hosts)
    require(disabled == set(hosts) - enabled and row.get("mask_id") == identity,
            "mask IDs must bind the complete enabled and disabled physical hosts")
    return number


def demanded_number(row, hosts):
    if row.get("fixed_branch_converged") is not True:
        require(row.get("fixed_branch_converged") is False, "explicit branch convergence status required")
        return None
    normals = core.normal_resultants(row["floor_normal_force_n_by_host"], hosts)
    demanded = sorted(host for host in hosts if normals[host] > 1e-7)
    require(row.get("demanded_enabled_centroid_xy_hosts") == demanded
            and 0. <= core.support.finite_scalar(row["fresh_original_gradient_inf_n"]) <= 1e-5,
            "resolved prior branch must retain its own normals, mask and original residual")
    return sum(1 << i for i, host in enumerate(hosts) if host in demanded)


def physical_input_signature(field):
    """Compare exact physical inputs while removing only numerical provenance."""
    keys = ("schema", "candidate", "revision", "case_id", "accessory_placement", "layout_report_sha256",
            "geometry_cache_sha256", "counts", "gravity", "applied_force_xyz_n",
            "applied_moment_about_global_origin_xyz_nmm", "body_applied_loads", "body_identities",
            "finished_floor_footprints")
    ignored = {"numerical_continuation_method", "numerical_newton_iteration_limit_per_floor_pattern",
               "lean_case_wall_time_limit_seconds"}
    parameters = {key: value for key, value in field["parameters"].items() if key not in ignored
                  and not key.startswith(("support_state_search_", "support_priority_", "support_mask_schedule_"))}
    return canonical_sha({**{key: field[key] for key in keys}, "parameters": parameters})


def read_prior_failure(path, expected_sha256, field):
    """Authenticate only a completed failed field's scheduling record."""
    path = Path(path)
    payload = path.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == expected_sha256, "prior failed field immutable bytes differ")
    previous = json.loads(payload)
    core.require_unreleased(previous.get("release"))
    require(previous.get("schema") == "thin_bolted_common_shaft_frame/v1"
            and previous.get("usable_conditional_actions") is False
            and previous.get("failed_response_without_recovered_actions") is True
            and previous.get("compatible_numerical_mvp_complete") is False
            and previous.get("response", {}).get("converged") is False
            and all(key not in previous["response"] for key in ("q", "connector_local_force_n", "normal_contact_force_n")),
            "terminal failed field with no accepted q or force arrays required for ordering only")
    require(all(previous.get(key) == field.get(key) for key in
                ("candidate", "case_id", "accessory_placement", "geometry_cache_sha256", "layout_report_sha256")),
            "prior scheduling record must retain the same case, candidate and geometry")
    identity = {key: previous[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    require(previous.get("state_id") == "thin-v4-" + canonical_sha(identity)[:24], "prior failed state identity differs")
    signature = physical_input_signature(previous)
    require(signature == physical_input_signature(field), "priority scheduling must preserve every physical input")
    core.verify_execution(previous, **CORE_ARGS)
    previous_sources = previous["source_sha256"]
    required = {core.DRIVER: CORE_ARGS["driver_sha256"], core.SEARCH: CORE_ARGS["search_sha256"],
                relative(CORE_ARGS["method_receipt_path"]): CORE_ARGS["method_receipt_sha256"]}
    require(all(previous_sources.get(name) == sha for name, sha in required.items()), "prior failed source bindings missing")
    verify_pins(previous_sources)
    diagnostic = previous["response"].get("support_state_search_v1", {})
    hosts = sorted(core.support.FLOOR_HOSTS)
    rows = diagnostic.get("tested_masks")
    require(diagnostic.get("schema") == core.SEARCH_SCHEMA and diagnostic.get("method") == core.METHOD
            and diagnostic.get("host_order") == hosts and diagnostic.get("floor_activation_threshold_n") == 1e-7
            and diagnostic.get("total_possible_masks") == 256
            and diagnostic.get("old_field_initialization_used") is False
            and diagnostic.get("physical_laws_changed") is False and diagnostic.get("no_fixed_point_proven") is False
            and diagnostic.get("accepted_pattern_index") is None
            and diagnostic.get("accepted_enabled_centroid_xy_hosts") is None
            and diagnostic.get("accepted_disabled_centroid_xy_hosts") is None
            and diagnostic.get("final_q_canonical_sha256") is None and diagnostic.get("final_mask_id") is None
            and isinstance(rows, list) and 1 <= len(rows) <= diagnostic.get("mask_budget", 0)
            and diagnostic.get("mask_budget") == previous["parameters"]["support_state_search_mask_budget"],
            "complete terminal failed support-search mask history required")
    visited, numbers = set(), []
    expected = 255
    for index, row in enumerate(rows):
        number = mask_number(row, hosts)
        require(row.get("pattern_index") == index and number == expected and number not in visited
                and row.get("self_consistent") is False, "prior masks must follow the frozen failed search without a fixed point")
        visited.add(number)
        numbers.append(number)
        demanded = demanded_number(row, hosts)
        require(demanded != number, "a resolved prior fixed point cannot be a failed scheduling source")
        expected, _ = search._next_mask(number, demanded, visited, 256)
    require(diagnostic.get("all_masks_visited") is (len(visited) == 256)
            and diagnostic.get("complete_enumeration") is (
                len(visited) == 256 and all(row["fixed_branch_converged"] for row in rows)),
            "failed mask history must distinguish attempted and resolved enumeration")
    require(core.support.digest(path) == expected_sha256, "prior failed bytes changed during scheduling authentication")
    return {"path": relative(path), "sha256": expected_sha256, "canonical_sha256": canonical_sha(previous),
            **{key: previous[key] for key in core.IDENTITIES}, "host_order": hosts,
            "mask_ids": [row["mask_id"] for row in rows], "mask_numbers": numbers,
            "physical_input_signature_sha256": signature,
            "scheduling_only": True, "old_q_or_forces_used": False, "previous_results_are_nonexistence_proof": False}, previous_sources


def verify_priority_execution(field, *, priority_driver_sha256, schedule_sha256, method_receipt_path,
                              method_receipt_sha256, prior_failure_path, prior_failure_sha256):
    execution = field.get("support_priority_execution", {})
    command = execution.get("command")
    internal = field["support_state_search_execution"]["command"]
    require(isinstance(command, list) and len(command) >= 3 and all(isinstance(v, str) and v for v in command)
            and command[1:3] == ["-m", "scripts.run_thin_bolted_support_priority_frame"], "actual priority runner command required")
    parser = argparse.ArgumentParser(add_help=False, exit_on_error=False, allow_abbrev=False)
    parser.add_argument("--support-prior-failure", type=Path)
    parser.add_argument("--support-prior-sha256")
    parser.add_argument("--support-priority-method-receipt", type=Path)
    parser.add_argument("--support-priority-method-sha256")
    try:
        args, remainder = parser.parse_known_args(command[3:])
    except (argparse.ArgumentError, SystemExit) as exc:
        raise ValueError("invalid actual priority runner arguments") from exc
    require(args.support_prior_failure is not None and args.support_priority_method_receipt is not None
            and relative(ROOT / args.support_prior_failure) == relative(prior_failure_path)
            and relative(ROOT / args.support_priority_method_receipt) == relative(method_receipt_path)
            and args.support_prior_sha256 == prior_failure_sha256
            and args.support_priority_method_sha256 == method_receipt_sha256
            and command[0] == internal[0] and remainder == internal[3:],
            "actual priority command must preserve exact internal arguments and authenticated ordering inputs")
    expected = {"loaded_driver_sha256": priority_driver_sha256, "loaded_schedule_sha256": schedule_sha256,
                "method_receipt_path": relative(method_receipt_path), "method_receipt_sha256": method_receipt_sha256,
                "prior_failure_path": relative(prior_failure_path), "prior_failure_sha256": prior_failure_sha256,
                "scheduling_only": True, "prior_q_or_forces_used": False,
                "nested_support_search_execution_is_reused_internal_call": True}
    require(all(execution.get(key) == value and (not isinstance(value, bool) or execution.get(key) is value)
                for key, value in expected.items()), "fresh priority producers and scheduling-only provenance required")
    params = {"support_priority_driver_sha256": priority_driver_sha256,
              "support_priority_schedule_sha256": schedule_sha256,
              "support_priority_method_receipt_sha256": method_receipt_sha256,
              "support_priority_prior_failure_sha256": prior_failure_sha256}
    require(all(field["parameters"].get(key) == value for key, value in params.items()), "priority state must bind all new sources")
    return execution


def verify_priority_schedule(field, prior):
    metadata = field["response"].get("support_mask_schedule_v1", {})
    expected = {"schema": SCHEDULE_SCHEMA, "method": SCHEDULE_METHOD,
                "previous_field_path": prior["path"], "previous_field_sha256": prior["sha256"],
                "previous_field_canonical_sha256": prior["canonical_sha256"],
                "previous_state_id": prior["state_id"], "previous_case_id": prior["case_id"],
                "previous_accessory_placement": prior["accessory_placement"],
                "previous_host_order": prior["host_order"], "previous_mask_ids": prior["mask_ids"],
                "physical_input_signature_sha256": prior["physical_input_signature_sha256"],
                "scheduling_only": True, "old_q_or_forces_used": False, "previous_results_are_nonexistence_proof": False,
                "physical_laws_changed": False, "first_all_host_branch_remains_fresh": True}
    require(all(metadata.get(key) == value and (not isinstance(value, bool) or metadata.get(key) is value)
                for key, value in expected.items()), "scheduling metadata must bind the authenticated failed mask IDs only")
    visited, previous = set(), set(prior["mask_numbers"])
    require([search._mask_id(prior["host_order"], mask) for mask in prior["mask_numbers"]] == prior["mask_ids"],
            "authenticated prior bit masks and mask IDs must agree")
    rows = field["response"]["support_state_search_v1"]["tested_masks"]
    next_mask, fresh_count, old_count = 255, 0, 0
    for row in rows:
        number = mask_number(row, prior["host_order"])
        require(number == next_mask and number not in visited, "current mask must follow independent priority scheduling replay")
        fresh_count += number not in previous
        old_count += number in previous
        visited.add(number)
        demanded = demanded_number(row, prior["host_order"])
        next_mask, _ = search._next_mask(number, demanded, visited | previous, 256)
        if next_mask is None:
            next_mask, _ = search._next_mask(number, demanded, visited, 256)
    return {"independent_priority_choices_replayed": True, "fresh_all_on_initialization_repeated": True,
            "globally_new_tested_mask_count": fresh_count, "previously_attempted_tested_mask_count": old_count,
            "combined_scheduling_mask_count": len(visited | previous),
            "old_q_or_forces_used": False, "combined_scheduling_census_is_nonexistence_proof": False}


def audit_support_priority_state(path_or_bytes, *, priority_driver_sha256, schedule_sha256,
                                 method_receipt_path, method_receipt_sha256,
                                 prior_failure_path, prior_failure_sha256):
    require(isinstance(path_or_bytes, (bytes, str, Path)), "immutable priority field bytes or path required")
    args = {"priority_driver_sha256": priority_driver_sha256, "schedule_sha256": schedule_sha256,
            "method_receipt_path": method_receipt_path, "method_receipt_sha256": method_receipt_sha256}
    pins = source_pins(**args)
    path = None if isinstance(path_or_bytes, bytes) else Path(path_or_bytes)
    payload = path.read_bytes() if path is not None else path_or_bytes
    field = json.loads(payload)
    before = canonical_sha(field)
    require(field.get("schema") == "thin_bolted_common_shaft_frame/v1", "fresh physical common-shaft field required")
    core.require_unreleased(field.get("release"))
    identity = {key: field[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    require(field.get("state_id") == "thin-v4-" + canonical_sha(identity)[:24], "priority field state identity differs")
    internal = core.verify_execution(field, **CORE_ARGS)
    actual = verify_priority_execution(field, **args, prior_failure_path=prior_failure_path,
                                       prior_failure_sha256=prior_failure_sha256)
    prior, prior_sources = read_prior_failure(prior_failure_path, prior_failure_sha256, field)
    support_checks = core.verify_support_search(field)
    schedule_checks = verify_priority_schedule(field, prior)
    _, cache, _, layout, _, _, base_pins = core.common.read_sources()
    proof_payload = core.linear.proof_method.PROOF.read_bytes()
    require(hashlib.sha256(proof_payload).hexdigest() == core.linear.proof_method.PROOF_SHA256, "frozen paired-face proof changed")
    proof = json.loads(proof_payload)
    required = merge_pins(base_pins, proof["source_sha256"], {
        DRIVER: priority_driver_sha256, SCHEDULE: schedule_sha256,
        core.DRIVER: CORE_ARGS["driver_sha256"], core.SEARCH: CORE_ARGS["search_sha256"],
        relative(CORE_ARGS["method_receipt_path"]): CORE_ARGS["method_receipt_sha256"],
        relative(method_receipt_path): method_receipt_sha256, relative(prior_failure_path): prior_failure_sha256,
        core.linear.DRIVER: core.linear.DRIVER_SHA256, core.linear.METHOD: core.linear.METHOD_SHA256,
        relative(core.linear.proof_method.PROOF): core.linear.proof_method.PROOF_SHA256,
        relative(core.linear.panel_sources.OPERATORS): core.linear.panel_sources.OPERATORS_SHA,
        relative(core.linear.panel_sources.coupled.DATUMS): core.linear.panel_sources.coupled.DATUMS_SHA,
    })
    require(all(field["source_sha256"].get(name) == sha for name, sha in required.items()), "priority field omits authenticated sources")
    pins = merge_pins(pins, prior_sources, required, field["source_sha256"])
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
            "sources or parsed field changed during priority admission")
    require(core.support.digest(Path(prior_failure_path)) == prior_failure_sha256, "prior failed bytes changed during admission")
    raw_sha = hashlib.sha256(payload).hexdigest()
    if path is not None:
        require(core.support.digest(path) == raw_sha, "raw priority field changed during admission")
    return {"schema": SCHEMA, SUCCESS: True, **{key: field[key] for key in core.IDENTITIES},
            "field_sha256": raw_sha, "field_canonical_sha256": before, "source_sha256": pins,
            "actual_support_priority_execution": actual, "reused_internal_support_search_execution": internal,
            "prior_scheduling_source": prior, "priority_schedule_checks": schedule_checks,
            "support_search_checks": support_checks, "floor_q_law_checks": floor,
            "linear_timber_map_checks_pass": True, "linear_timber_face_checks": faces,
            "timber_contact_geometry": inventory, "complete_action_census": census,
            "independent_common_shaft_audit": unchanged, "native_CAD_K_or_response_execution": False,
            "small_motion_applicability_physical_bounds_complete_capacity_or_release_established": False,
            "release": {key: False for key in field["release"]}}
