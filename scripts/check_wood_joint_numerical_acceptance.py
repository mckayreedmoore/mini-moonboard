"""Authenticate the numerical extension without importing or running mechanics."""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import json
import math
import re
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = Path("docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/full-assessment-index.json")
COMPLETE = "complete_conditional_numerical_comparisons"
FINITE_DISPOSITION = "complete_finite_numerical_disposition"
FRAME_SCHEMA = "joint_frame_compatibility_completion/v1"
ACTION_SCHEMA = "joint_frame_action_reconciliation/v1"
MEMBER_SCHEMA = "member_opening_general_completion/v1"
SPLITTING_SCHEMA = "splitting_active_coupled_duty_coverage/v1"
SPLITTING_SCOPE = "active_finite_splitting_workload"
SPLITTING_WORKSTREAM = "three-dimensional conditional splitting resistance"
MOTION_SCHEMA = "joint_frame_fixed_force_motion_bounds/v1"
MOTION_SCOPE = "fixed_force_344_coordinate_motion"
MOTION_STATUS = "COMPLETE_FIXED_FORCE_MOTION_AND_FINITE_STABILITY_DISPOSITION"
REPRESENTATIVE_COMPLETE = "complete_representative_conditional_numerical_study"
REPRESENTATIVE_SCHEMA = "splitting_representative_coupled_study/v1"
REPRESENTATIVE_SCOPE = "representative_coupled_splitting_study"
REPRESENTATIVE_STATUS = "COMPLETE_SELECTED_REPRESENTATIVE_COUPLED_SPLITTING_STUDY"
WASHER_SCHEMA = "current_force_washer_plate_dispositions/v1"
WASHER_SCOPE = "current_accepted_washer_end_dispositions"
WASHER_STATUS = "COMPLETE_CURRENT_WASHER_END_NUMERICAL_DISPOSITIONS"
WASHER_FINITE = "FINITE_CURRENT_FORCE_ELASTIC_PLATE_REFERENCE"
WASHER_ZERO = "ANALYTIC_ZERO_DEMAND"
WASHER_HEAD = "HEAD_COMPRESSION_LOAD_PATH_LIMIT"
WASHER_TOPSIDE = "TOPSIDE_SOURCE_GEOMETRY_COUPLE_METHOD_LIMIT"
TOPSIDE_AXES = {f"top_outer/clip_single_top_{side}/{end}" for side in ("left_1", "right_2")
                for end in ("side_1", "side_2")}
CONTINUOUS_AXES = {f"knee_outer_{side}_side_{end}" for side in ("left", "right") for end in (1, 2)}
PROJECTED_OPERATOR_METHOD = "orthogonal_symmetric_retained_rigid_quotient_v1"
SHAFT_SCOPE = "current_accepted_shaft_dispositions"
SHAFT_STATUS = "ASSESSED_ISOLATED_CURRENT_FORCE_FIELDS_WITH_DECLARED_STOPS"
ORIGINAL_SPLITTING_INVENTORY_SHA256 = "83cc1a958382c0b756600625d4426b6d7d597e614f16c5344a6d932b99477b17"
PARTIAL_ENERGY_CONSTANT = "selected_body_load_matrix_plus_unchanged_constant"
CURRENT_COUPLED_PORT_COUNT = 3192
REPRESENTATIVE_FIELD_GATES = {
    "source_and_output_authentication", "source_port_order_and_body_ownership",
    "same_external_load_basis_and_rigid_work", "source_side_footprint_wrench_and_affine_work",
    "actual_profile_bore_volume_and_crack_area", "original_mesh_and_stiffness_identity", "rigid_quotient_and_gauge",
    "port_compliance_reciprocity_and_load_cross_terms", "old_body_removed_once_and_new_body_added_once",
    "assembled_equilibrium_and_spring_law", "recovered_full_body_equilibrium",
    "assembled_energy_and_external_work_identity", "unchanged_energy_constant_token", "retained_fields_and_port_reactions",
}
FRAME_COMPLETE = "COMPLETE_CONDITIONAL_COUPLED_FRAME_STATES"
FRAME_PARTIAL = "PARTIAL_CONDITIONAL_COUPLED_FRAME_STATES_WITH_DECLARED_STOPS"
ACCEPTED_STATE = "PASS_CONDITIONAL_COMPATIBLE_EQUILIBRIUM"
FLOOR_STOP = "STOP_NO_AUDITED_POSITIVE_BEARING_FLOOR_BRANCH"
FLOOR_PREFIX = "STOP: no audited coupled floor branch among 256 masks: "
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear", "dead-only")
REQUIRED_STATES = {(case, gap) for case in CASES for gap in (0, 1)}
RELEASE_FLAGS = {
    "climbing_released", "drilling_released", "engineering_mvp_complete",
    "fabrication_released", "geometry_accepted", "layout_complete",
    "physical_prototype_complete", "structural_released",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def file_path(root, value, *, absolute=False):
    require(isinstance(value, str) and value and "\x00" not in value, "invalid artifact path")
    path = Path(value)
    require(".." not in path.parts, "parent traversal in artifact path: " + value)
    require(absolute or not path.is_absolute(), "absolute artifact path: " + value)
    result = path.resolve() if path.is_absolute() else (root / path).resolve()
    require(path.is_absolute() or result.is_relative_to(root), "artifact escapes repository: " + value)
    return result


def read_json(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "JSON object required: " + str(path))
    return value


def fingerprint(path, cache):
    if path not in cache:
        with path.open("rb") as stream:
            cache[path] = (hashlib.file_digest(stream, "sha256").hexdigest(), path.stat().st_size)
    return cache[path]


def authenticate(root, source, expected, resolutions, cache, *, size=None):
    require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected),
            "invalid SHA256: " + str(source))
    path = file_path(root, source, absolute=True)
    # A redirect preserves original bytes; it never repins the original source.
    if source in resolutions:
        resolution = resolutions[source]
        require(isinstance(resolution, dict) and resolution.get("original_path") == source
                and isinstance(resolution.get("sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", resolution["sha256"]), "invalid source redirect: " + source)
        if resolution["sha256"] == expected:
            path = file_path(root, resolution.get("snapshot_path"))
    actual, actual_size = fingerprint(path, cache)
    require(actual == expected, "SHA256 mismatch: " + str(path))
    require(size is None or type(size) is int and actual_size == size,
            "byte count mismatch: " + str(path))
    return path


def output_path(root, packet, name):
    require(isinstance(name, str), "invalid receipt output name")
    prefix = packet.relative_to(root).as_posix() + "/"
    return file_path(root, name if name.startswith(prefix) else prefix + name)


def bound_output(root, packet, receipt, name, cache):
    outputs = receipt.get("output_sha256", {})
    path = packet / name
    matches = [digest for key, digest in outputs.items() if output_path(root, packet, key) == path]
    require(len(matches) == 1, "artifact absent from receipt outputs: " + str(path))
    authenticate(root, path.relative_to(root).as_posix(), matches[0], {}, cache)
    return path


def source_document(root, reference, sources, resolutions, cache):
    require(isinstance(reference, dict) and sources.get(reference.get("path")) == reference.get("sha256")
            and reference.get("sha256") is not None, "record absent from source bindings")
    path = authenticate(root, reference["path"], reference["sha256"], resolutions, cache)
    value = read_json(path)
    pointer = reference.get("pointer", "")
    require(isinstance(pointer, str) and pointer.startswith("/"), "invalid source record pointer")
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    require(isinstance(value, dict), "source pointer does not identify a record")
    return path, value


def state_key(record):
    case, gap = record.get("case_id"), record.get("gap_scale")
    require(case in CASES and type(gap) in (int, float) and gap in (0, 1), "unsupported case/gap identity")
    return case, gap


def state_tag(key):
    return key[0] + ("_zero" if key[1] == 0 else "_gap")


def state_map(records):
    require(isinstance(records, list), "missing state inventory")
    result = {}
    for record in records:
        require(isinstance(record, dict), "invalid state record")
        key = state_key(record)
        require(key not in result, "duplicate case/gap identity: " + state_tag(key))
        result[key] = record
    return result


def accepted_audit(state):
    audit = state.get("audit", {})
    require(isinstance(audit, dict), "invalid accepted state audit")
    checks = audit.get("checks", {})
    require(audit.get("all_passed") is True and isinstance(checks, dict) and checks
            and all(value is True for value in checks.values()), "accepted state has a failed or missing audit gate")


def floor_summary(exception):
    require(isinstance(exception, str) and exception.startswith(FLOOR_PREFIX), "stop is not a finite mask disposition")
    history = json.loads(exception[len(FLOOR_PREFIX):])
    require(isinstance(history, list) and len(history) == 256, "finite search does not have 256 masks")
    masks, statuses, failures = set(), {}, {}
    for record in history:
        mask = record["bearing_footprints"]
        require(isinstance(mask, list) and all(type(i) is int and 0 <= i < 8 for i in mask)
                and len(set(mask)) == len(mask), "invalid finite-search mask")
        masks.add(sum(1 << i for i in mask))
        if "solver" in record:
            status = record["solver"]["status"]
            audit = record["original_physical_law_audit"]
            checks = audit["checks"]
            require(audit.get("all_passed") is False and checks and all(type(v) is bool for v in checks.values())
                    and not all(checks.values()), "stopped trace contains an accepted or unaudited force field")
            for gate, passed in checks.items():
                if not passed:
                    failures[gate] = failures.get(gate, 0) + 1
        else:
            message = record["numerical_branch_stop"]
            status = next((word for word in ("PrimalInfeasible", "InsufficientProgress", "AlmostSolved",
                          "NumericalError", "MaxIterations", "MaxTime") if word in message), "OtherNumericalStop")
        require(isinstance(status, str) and status, "invalid finite-search solver status")
        statuses[status] = statuses.get(status, 0) + 1
    require(masks == set(range(256)), "finite search omitted or repeated a mask")
    return {"attempted_unique_masks": 256, "solver_status_counts": statuses,
            "failed_audit_gate_counts": failures, "accepted_force_field_exists": False,
            "scope": "No branch passed the unchanged physical audit; numerical stops are not physical infeasibility proofs."}


def stop_check(root, item, current_packet, current_receipt, inputs, sources, resolutions, cache):
    require(item.get("status") == FLOOR_STOP and item.get("accepted_force_field_exists") is False
            and "response_tag" not in item and item.get("physical_frame_failure_claim") is False
            and item.get("physical_equilibrium_nonexistence_proven", False) is False,
            "stopped state claims a force field or physical failure proof")
    evidence = item.get("stop_evidence", {})
    packet, trace = file_path(root, evidence.get("packet")), file_path(root, evidence.get("trace_path"))
    require(trace.is_relative_to(packet) and evidence.get("pointer") == "exception", "invalid stop trace location")
    digest = evidence.get("receipt_sha256")
    if packet == current_packet:
        receipt = current_receipt
        if digest is not None:
            authenticate(root, (packet / "receipt.json").relative_to(root).as_posix(), digest, {}, cache)
    else:
        name = (packet / "receipt.json").relative_to(root).as_posix()
        require(digest is not None and sources.get(name) == digest, "external stop receipt is unbound")
        receipt = read_json(authenticate(root, name, digest, resolutions, cache))
        require(receipt.get("status") in {"STOP_COUPLED_FRAME_NUMERICAL_QUALIFICATION_OPEN", FRAME_PARTIAL},
                "unsupported stop receipt")
        if receipt["status"] == FRAME_PARTIAL:
            source = read_json(bound_output(root, packet, receipt, "comparison.json", cache))
            require(source.get("schema") == FRAME_SCHEMA and source.get("status") == FRAME_PARTIAL,
                    "external partial receipt lacks a matching frame aggregate")
            original = state_map(source.get("case_dispositions")).get(state_key(item), {})
            original_evidence = original.get("stop_evidence", {})
            require(original.get("status") == FLOOR_STOP and original.get("accepted_force_field_exists") is False
                    and state_key(item) not in state_map(source.get("states"))
                    and original.get("floor_search_summary") == item.get("floor_search_summary")
                    and all(original_evidence.get(field) == evidence.get(field) for field in
                            ("packet", "trace_path", "trace_sha256", "pointer")),
                    "external partial source lacks the exact stopped disposition")
    actual_trace = bound_output(root, packet, receipt, trace.relative_to(packet).as_posix(), cache)
    require(fingerprint(actual_trace, cache)[0] == evidence.get("trace_sha256"), "stop trace digest mismatch")
    data = read_json(actual_trace)
    stopped_inputs = read_json(bound_output(root, packet, receipt, "inputs.json", cache))
    require(all(stopped_inputs.get(field) == inputs.get(field) for field in
                ("preparation", "wood_reduction", "dead_load_factor"))
            and stopped_inputs.get("proposal_ties_included") is False, "stop uses different source physics")
    if "washer_joint_update" in inputs or "washer_joint_update" in stopped_inputs:
        require(all(stopped_inputs.get(field) == inputs.get(field) for field in
                    ("washer_joint_update", "joint_update_sha256", "source_frame_sha256",
                     "energy_constant_scope", "unchanged_constant_token")),
                "reused stop transfers a different washer law or body-energy source")
    key = state_key(item)
    require(state_key(data) == key if "case_id" in data else
            stopped_inputs.get("cases") == [key[0]] and stopped_inputs.get("gap_scales") == [key[1]],
            "stop trace has a different case/gap")
    require(data.get("accepted_force_field_exists", False) is False and data.get("physical_release", False) is False,
            "stopped trace claims an accepted field or release")
    require(canonical(item.get("floor_search_summary")) == canonical(floor_summary(data.get("exception"))),
            "finite-search census differs from authenticated trace")


def npz_keys(path, expected):
    # Inspect the saved export inventory without importing NumPy or reading mechanics fields.
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    require(len(names) == len(set(names)) and set(names) == {name + ".npy" for name in expected},
            "response exports missing, unlisted or rejected force states: " + str(path))


def frame_dispositions(root, result, packet, receipt, sources, resolutions, cache):
    require(result.get("schema") == FRAME_SCHEMA and result.get("status") in {FRAME_COMPLETE, FRAME_PARTIAL},
            "unsupported finite frame result")
    require(receipt.get("status") == result["status"], "source frame result/receipt status mismatch")
    for document in (result, receipt):
        require(document.get("physical_release", False) is False and document.get("complete_joint_acceptance", False) is False,
                "source frame claims release or complete joint acceptance")
    dispositions = state_map(result.get("case_dispositions"))
    require(set(dispositions) == REQUIRED_STATES and result.get("complete_requested_state_inventory") is True,
            "frame has unassessed required identities")
    accepted = state_map(result.get("states"))
    inputs = read_json(bound_output(root, packet, receipt, "inputs.json", cache))
    require({(c, g) for c in inputs.get("cases", []) for g in inputs.get("gap_scales", [])} == REQUIRED_STATES,
            "frame request is not the exact 14 required identities")
    for key, item in dispositions.items():
        require(item.get("physical_release") is False, "released frame disposition")
        if item.get("status") == ACCEPTED_STATE:
            require(item.get("accepted_force_field_exists") is True and item.get("response_tag") == state_tag(key)
                    and key in accepted, "accepted disposition/field identity mismatch")
            accepted_audit(accepted[key])
        else:
            require(key not in accepted, "stopped force field exported as accepted")
            stop_check(root, item, packet, receipt, inputs, sources, resolutions, cache)
    require(set(accepted) == {key for key, item in dispositions.items() if item.get("status") == ACCEPTED_STATE},
            "accepted state/disposition census mismatch")
    require((result["status"] == FRAME_COMPLETE) == (set(accepted) == REQUIRED_STATES),
            "partial frame falsely claims all accepted states")
    live = {key for key in REQUIRED_STATES if key[0] != "dead-only"}
    permanent = REQUIRED_STATES - live
    require(result.get("complete_six_case_zero_and_nominal_scope") is (live <= set(accepted))
            and result.get("complete_permanent_zero_and_nominal_scope") is (permanent <= set(accepted)),
            "frame accepted-scope flags differ from saved states")
    if "completed_states" in receipt:
        require(receipt["completed_states"] == len(accepted), "frame receipt accepted count mismatch")
    npz_keys(bound_output(root, packet, receipt, "response.npz", cache),
             {state_tag(key) + suffix for key in accepted for suffix in
              ("_force_n", "_relative_motion_mm", "_rigid_scaled_mm", "_shaft_pose_mm", "_bearing")})
    return dispositions, accepted


def finite_disposition_check(root, result, packet, receipt, sources, resolutions, cache):
    if result.get("schema") == FRAME_SCHEMA:
        return frame_dispositions(root, result, packet, receipt, sources, resolutions, cache)
    require(result.get("schema") == ACTION_SCHEMA and result.get("status") ==
            "COMPLETE_SAVED_COUPLED_ACTION_RECONCILIATION_NOT_RESISTANCE_QUALIFICATION",
            "finite disposition class requires a supported frame/action aggregate")
    inventory = state_map(result.get("required_state_inventory"))
    require(set(inventory) == REQUIRED_STATES, "action inventory has unassessed required identities")
    accepted, frames = state_map(result.get("states")), {}
    for key, item in inventory.items():
        require(item.get("state_tag") == state_tag(key) and item.get("finite_disposition_completed") is True
                and item.get("physical_release") is False, "action has an unfinished or mismatched disposition")
        path, original = source_document(root, item.get("source_disposition_record"), sources, resolutions, cache)
        require(re.fullmatch(r"/case_dispositions/[0-9]+", item["source_disposition_record"]["pointer"]),
                "action disposition pointer is not a source disposition")
        if path not in frames:
            name = (path.parent / "receipt.json").relative_to(root).as_posix()
            require(name in sources, "action source frame receipt is unbound")
            source_receipt = read_json(authenticate(root, name, sources[name], resolutions, cache))
            require(bound_output(root, path.parent, source_receipt, path.name, cache) == path,
                    "action source comparison is absent from receipt outputs")
            frames[path] = frame_dispositions(root, read_json(path), path.parent, source_receipt,
                                             sources, resolutions, cache)
        for field in ("case_id", "gap_scale", "status", "accepted_force_field_exists", "response_tag",
                      "stop_evidence", "floor_search_summary"):
            require(item.get(field) == original.get(field), "action disposition differs from source: " + field)
        require(state_key(original) == key and key in frames[path][0], "action source pointer has another identity")
        if item.get("status") == ACCEPTED_STATE:
            require(key in accepted and accepted[key].get("state_tag") == state_tag(key), "action accepted state mismatch")
            state_path, state = source_document(root, item.get("source_state_record"), sources, resolutions, cache)
            require(state_path == path and state_key(state) == key
                    and re.fullmatch(r"/states/[0-9]+", item["source_state_record"]["pointer"])
                    and accepted[key].get("source_state_record") == item["source_state_record"], "action state source mismatch")
            accepted_audit(state)
        else:
            require(item.get("status") == FLOOR_STOP and key not in accepted
                    and item.get("physical_equilibrium_nonexistence_proven") is False,
                    "action stop is unfinished or exports rejected force")
    require(len(frames) == 1 and set(accepted) == {key for key, item in inventory.items() if item["status"] == ACCEPTED_STATE},
            "action accepted census differs from source inventory")
    expected = {"required_states": 14, "accepted_states": len(accepted), "finite_floor_search_dispositions": 14-len(accepted),
                "assessed_states": 14, "unassessed_states": 0, "unresolved_numerical_stops": 0, "rejected_force_fields_exported": 0}
    require(canonical(result.get("counts")) == canonical(expected)
            and result.get("finite_state_disposition_inventory_complete") is True
            and result.get("action_exports_complete_for_accepted_states") is True
            and result.get("completed_states") == len(accepted)
            and result.get("all14_required_states") is (set(accepted) == REQUIRED_STATES), "action census or completion flag mismatch")
    require(result.get("source_response_status") == (FRAME_COMPLETE if len(accepted) == 14 else FRAME_PARTIAL)
            and result.get("action_state_scope") == ("all14_accepted_states" if len(accepted) == 14 else "accepted_state_subset"),
            "action falsely claims a full accepted-state scope")
    for field in ("required_state_inventory", "counts", "finite_state_disposition_inventory_complete",
                  "action_state_scope", "action_exports_complete_for_accepted_states"):
        require(canonical(receipt.get(field)) == canonical(result[field]), "action receipt differs from result: " + field)
    npz_keys(bound_output(root, packet, receipt, "source-row-response.npz", cache),
             {"canonical_raw_row_available", "canonical_raw_row_to_kept_lumped_position", "old_kept_lumped_rows"}
             | {state_tag(key) + suffix for key in accepted for suffix in
                ("_raw_force_n", "_kept_lumped_relative_motion_mm", "_coupled_force_n")})
    return inventory, accepted


def member_field_scope(entry, result):
    if entry.get("numerical_scope") != "finished_longitudinal_and_shear":
        return
    require(result.get("schema") == MEMBER_SCHEMA and result.get("elastic_whole_domain_shear_executed") is True,
            "finished member scope lacks executed elastic shear comparisons")
    comparison = result.get("comparison")
    require(isinstance(comparison, dict) and comparison, "finished member scope lacks named comparisons")
    fields = ("target_cuts", "finite_normal_cuts", "finite_elastic_shear_cuts", "resolved_one_sided_terminal_count",
              "one_sided_zero_limits", "one_sided_divergent_limits", "coupled_ligament_input_count", "unresolved_endpoint_input_count")
    for basis, counts in comparison.items():
        require(isinstance(basis, str) and basis and isinstance(counts, dict)
                and all(type(counts.get(field)) is int and counts[field] >= 0 for field in fields),
                "invalid finished member comparison counters")
        require(counts["finite_elastic_shear_cuts"] == counts["finite_normal_cuts"]
                and counts["target_cuts"] == counts["finite_normal_cuts"] + counts["resolved_one_sided_terminal_count"]
                and counts["one_sided_zero_limits"] + counts["one_sided_divergent_limits"] == counts["resolved_one_sided_terminal_count"]
                and counts["coupled_ligament_input_count"] == counts["unresolved_endpoint_input_count"] == 0,
                "finished member scope has missing comparisons or an unresolved endpoint partition: " + basis)
    require(sum(counts["finite_normal_cuts"] for counts in comparison.values()) > 0,
            "finished member scope has no finite section comparisons")


def finite_number(value, *, positive=False):
    return type(value) in (int, float) and math.isfinite(value) and (not positive or value > 0)


def source_json(root, reference, sources, resolutions, cache):
    require(isinstance(reference, dict) and sources.get(reference.get("path")) == reference.get("sha256")
            and reference.get("sha256") is not None, "artifact absent from source bindings")
    return read_json(authenticate(root, reference["path"], reference["sha256"], resolutions, cache))


def shaft_scope_check(root, entry, result, packet, receipt, sources, resolutions, cache):
    """Complete only saved current scalar fields or the four exact quarter-source limits."""
    if entry.get("numerical_scope") != SHAFT_SCOPE:
        return
    require(entry.get("status") == FINITE_DISPOSITION and result.get("status") == SHAFT_STATUS
            and result.get("all100_final_current_force_sweep") is True
            and result.get("finite_source_geometry_dispositions_complete") is True
            and result.get("ordinary_numerical_stops_are_pending") is False,
            "shaft disposition has incomplete fields or ordinary solver stops")
    for flag in ("actual_washer_metal_stress_complete", "common_host_compatibility_established",
                 "globally_compatible_scalar_shaft_curvature_established", "historical_force_or_acceptance_transferred",
                 "isolated_fields_used_to_refresh_global_forces", "native_or_CAD_or_frame_run", "reviewed_geometry_changed"):
        require(result.get(flag) is False, "shaft disposition overclaims its isolated source field: " + flag)
    binding = result.get("active_action_binding", {})
    require(isinstance(binding, dict) and binding.get("source_force_fields_relabelled") is False
            and result.get("source_join", {}).get("active_action_binding") == binding
            and result["source_join"].get("force_branch") == "washer_updated_compatible_frame",
            "shaft disposition lacks its actual new action branch")
    action_packet = file_path(root, binding.get("action_packet"))
    action_name = (action_packet / "receipt.json").relative_to(root).as_posix()
    action_receipt = source_json(root, {"path": action_name, "sha256": binding.get("action_receipt_sha256")}, sources, resolutions, cache)
    action = read_json(bound_output(root, action_packet, action_receipt, "summary.json", cache))
    _inventory, accepted = finite_disposition_check(root, action, action_packet, action_receipt, sources, resolutions, cache)
    require(len(accepted) == 12 and result.get("accepted_scope", {}).get("required_state_inventory") == action["required_state_inventory"]
            and result["accepted_scope"].get("accepted_states") == 12 and result["accepted_scope"].get("required_states") == 14
            and result["accepted_scope"].get("unavailable_states") == 2, "shaft scope is not the actual 12-state/14-disposition branch")
    tags = {state_tag(key): item for key, item in accepted.items()}
    frame_packet = file_path(root, binding.get("response"))
    for field, filename in (("response_receipt_sha256", "receipt.json"), ("response_comparison_sha256", "comparison.json"),
                            ("response_npz_sha256", "response.npz"), ("joint_update_sha256", "joint-update.json")):
        name = (frame_packet / filename).relative_to(root).as_posix()
        require(binding.get(field) == sources.get(name), "shaft new response binding differs")
    frame = read_json(frame_packet / "comparison.json")
    require(frame.get("analytical_branch") == "working_washer_profile_with_explicit_member_replacements"
            and all(item["source_state_record"]["path"] == (frame_packet / "comparison.json").relative_to(root).as_posix()
                    and item["source_state_record"]["sha256"] == binding["response_comparison_sha256"] for item in tags.values()),
            "shaft source state belongs to an old frame branch")

    def audit(binding_name, required_status, primary_field):
        reference = entry.get(binding_name, {})
        require(isinstance(reference, dict) and set(reference) == {"receipt", "result"}, "shaft independent audit binding missing")
        receipt_ref, result_ref = reference["receipt"], reference["result"]
        audit_path = authenticate(root, receipt_ref["path"], receipt_ref["sha256"], {}, cache)
        document = read_json(audit_path)
        redirects = {**resolutions, **document.get("source_resolution", {})}
        require(isinstance(document.get("source_sha256"), dict) and document["source_sha256"], "shaft audit source closure missing")
        for name, digest in document["source_sha256"].items():
            # Some frozen auditors wrote absolute source keys. Resolve only a
            # byte-identical declared original pin, never an arbitrary redirect.
            for original, resolution in resolutions.items():
                if file_path(root, original, absolute=True) == file_path(root, name, absolute=True) \
                        and resolution.get("sha256") == digest:
                    redirects[name] = {**resolution, "original_path": name}
            authenticate(root, name, digest, redirects, cache)
        require(any(file_path(root, name, absolute=True) == file_path(root, entry["receipt"])
                    and digest == entry["receipt_sha256"] for name, digest in document["source_sha256"].items()),
                "shaft audit belongs to another raw packet")
        path = bound_output(root, audit_path.parent, document, Path(result_ref["path"]).name, cache)
        require(path == file_path(root, result_ref["path"]) and fingerprint(path, cache)[0] == result_ref["sha256"],
                "shaft audit result lacks paired output authority")
        value = read_json(path)
        require(value.get("status") == required_status and value.get(primary_field) == entry["receipt_sha256"]
                and value.get("active_action_binding") == binding, "shaft audit status/field/action basis differs")
        return value

    field_audit = audit("field_audit_binding", "PASS_INDEPENDENT_SAVED_FIELD_AND_SOURCE_AUDIT", "packet_receipt_sha256")
    support = audit("support_audit_binding", "PASS_INDEPENDENT_CURRENT_TOPSIDE_ACTION_ORACLE_AND_NULL_END_AUDIT", "shaft_receipt_sha256")
    require(field_audit.get("original_numerical_auditor_AST_reverse_identity") is True
            and field_audit.get("source_solves_or_optimizers_or_native_or_CAD_run") is False
            and field_audit.get("geometry_limit_own_moments_and_metal_stresses_remain_null") is True
            and field_audit.get("current_T_and_signed_two_component_source_rows_authenticated") == 1200
            and field_audit.get("record_maps_authenticated") == field_audit.get("current_geometry_end_checks") == 2400
            and field_audit.get("actual_source_geometry_limit_axis_states") == 48
            and isinstance(field_audit.get("independent_arithmetic_errors"), dict)
            and field_audit["independent_arithmetic_errors"] and all(finite_number(value) and value >= 0
                for value in field_audit["independent_arithmetic_errors"].values()), "shaft independent saved-field/source audit is incomplete")
    original_error_limits = {"moment_nmm": 1e-5, "beam_shear_n": 1e-6, "stress_mpa": 1e-6,
        "bore_motion_mm": 1e-9, "bore_force_n": 1e-6, "gradient_difference_n": 1e-7,
        "annular_force_residual_n": 1e-7, "annular_moment_error_nmm": 1e-6}
    require(set(field_audit["independent_arithmetic_errors"]) == {*original_error_limits, "energy_nmm"}
            and all(field_audit["independent_arithmetic_errors"][name] <= limit
                    for name, limit in original_error_limits.items()), "shaft saved-field arithmetic exceeds the original audit gates")
    require(support.get("scope") == "isolated original-quarter source-geometry full-wrench normal-contact method; current working5/16 geometry remains a separate mismatch"
            and support.get("new_action_couple_values_recomputed") is True
            and support.get("signed_source_axial_and_lateral_full_actions_joined") is True
            and support.get("numerical_null_moments_or_metal_substituted") is False
            and support.get("quarter_fields_transferred_to_5_16") is False,
            "shaft quarter-source limitation was transferred to working hardware or null moments were zeroed")
    support_rows = {(item["state_tag"], item["axis_id"]): item for item in support.get("axis_states", [])}
    require(len(support_rows) == len(support.get("axis_states", [])) == 48
            and set(support_rows) == {(tag, axis) for tag in tags for axis in TOPSIDE_AXES}, "shaft TOPSIDE support audit identity set differs")
    for row in support_rows.values():
        require(row.get("own_end_moments_and_metal_stress_null") is True
                and row.get("quarter_forces_transferred_to_working_5_16_field") is False
                and finite_number(row.get("source_quarter_diameter_mm")) and abs(row["source_quarter_diameter_mm"]-6.35) < 1e-6
                and row.get("working_diameter_mm") == 7.9375 and row.get("working_bore_diameter_mm") == 9.0,
                "shaft exact source-quarter/working5/16 geometry boundary differs")
    states_path = bound_output(root, packet, receipt, "shaft-states.jsonl", cache)
    ends_path = bound_output(root, packet, receipt, "washer-ends.jsonl", cache)
    states = [json.loads(line) for line in states_path.read_text().splitlines()]
    ends = [json.loads(line) for line in ends_path.read_text().splitlines()]
    own_geometry = result.get("current_geometry_audit", {})
    geometry = {(row["axis_id"], row["end_role"], row["receiver_member"]) for row in own_geometry.get("own_ends", [])}
    axes = {axis for axis, _, _ in geometry}
    require(len(geometry) == len(own_geometry.get("own_ends", [])) == 200 and len(axes) == 100
            and TOPSIDE_AXES <= axes and not CONTINUOUS_AXES & axes
            and own_geometry.get("supported_scalar_own_ends") == 192
            and own_geometry.get("displaced_TOPSIDE_nominal_support_datums") == 8
            and all(own_geometry.get(flag) is False for flag in ("historical_fields_transferred", "physical_geometry_changed",
                "loaded_support_or_actual_hardware_qualified")), "shaft current canonical scalar geometry inventory differs")
    state_rows = {(row["state_tag"], row["axis_id"]): row for row in states}
    end_rows = {(row["state_tag"], row["axis_id"], row["end_role"], row["receiver_member"]): row for row in ends}
    require(len(state_rows) == len(states) == 1200 and set(state_rows) == {(tag, axis) for tag in tags for axis in axes}
            and len(end_rows) == len(ends) == 2400 and set(end_rows) == {(tag, *identity) for tag in tags for identity in geometry},
            "shaft raw accepted axis/end identity inventory is missing or duplicated")
    completed, limits, steel_exceedances = 0, 0, 0
    for (tag, axis), row in state_rows.items():
        join = row.get("source_join", {})
        require(join.get("active_action_binding") == binding
                and join.get("source_state_record") == tags[tag]["source_state_record"], "shaft state is a stale or rejected force branch")
        state = row.get("state")
        if axis in TOPSIDE_AXES:
            require(row.get("status") == "SOURCE_GEOMETRY_COUPLE_METHOD_LIMIT" and state is None
                    and row.get("same_state_steel_index") is None and row.get("shaft_same_state_same_position_index") is None,
                    "shaft TOPSIDE source-method limit carries an invented field or metal stress")
            limits += 1
        else:
            require(row.get("status") in {"SUPPORTED_ISOLATED_CURRENT_FORCE_FIELD", "REFERENCE_EXCEEDANCE"}
                    and isinstance(state, dict), "ordinary shaft solver STOP is not a finite method disposition")
            original = row.get("source_record", {})
            family = row.get("effective_family", {})
            length = family.get("host_length_mm", 0)+family.get("cleat_length_mm", 0)
            stationary = state.get("scaled_gradient_residuals_n", [])
            require(finite_number(length, positive=True) and stationary and all(finite_number(x) and abs(x) <= 1e-6 for x in stationary)
                    and finite_number(state.get("host_force_balance_residual_n")) and abs(state["host_force_balance_residual_n"]) <= 1e-6
                    and finite_number(state.get("host_moment_balance_residual_nmm")) and abs(state["host_moment_balance_residual_nmm"]) <= length*1e-6
                    and state.get("signed_T_n") == original.get("signed_T_n") and state.get("V_n") == original.get("V_n"),
                    "shaft finite field failed original equilibrium or current signed T/V")
            require(finite_number(row.get("same_state_steel_index")) and row["same_state_steel_index"] >= 0,
                    "shaft actual finite same-state metal reference is missing")
            completed += 1
            steel_exceedances += row["same_state_steel_index"] > 1
        for identity in (key for key in end_rows if key[:2] == (tag, axis)):
            end = end_rows[identity]
            require(end.get("source_join", {}).get("active_action_binding") == binding
                    and end["source_join"].get("source_state_record") == tags[tag]["source_state_record"], "shaft own-end uses a stale source")
            if axis in TOPSIDE_AXES:
                require(end.get("status") == "NULL_UNSUPPORTED" and end.get("own_end_M_signed_xyz_nmm") is None
                        and end.get("own_end_M_magnitude_nmm") is None
                        and end.get("actual_washer_metal_stress_complete") is False,
                        "shaft source-method null end was converted to zero or a metal pass")
            else:
                moment = end.get("own_end_M_signed_xyz_nmm")
                require(end.get("status") == "COMPLETE_ISOLATED_END_SOURCE" and isinstance(moment, list) and len(moment) == 3
                        and all(finite_number(x) for x in moment) and finite_number(end.get("own_end_M_magnitude_nmm"))
                        and math.isclose(end["own_end_M_magnitude_nmm"], math.hypot(*moment), rel_tol=1e-8, abs_tol=1e-6),
                        "shaft actual completed own-end moment is missing or inconsistent")
    expected = {"attempted_shaft_states": 1200, "bore_samples": 48*completed, "complete_own_end_sources": 2*completed,
        "completed_shaft_states": completed, "field_positions": 80*completed, "own_end_source_limits": 2*limits,
        "shaft_numerical_stops": 0, "source_geometry_couple_method_limits": limits, "steel_reference_exceedances": steel_exceedances}
    require(completed == 1152 and limits == 48 and result.get("counts") == field_audit.get("counts") == expected
            and receipt.get("counts", expected) == expected, "shaft finite/source-limit disposition partition differs")


def washer_scope_check(root, entry, result, packet, receipt, sources, resolutions, cache):
    """Authenticate current end dispositions; null metal limits never become metal passes."""
    if entry.get("numerical_scope") != WASHER_SCOPE and result.get("schema") != WASHER_SCHEMA:
        return
    require(entry.get("numerical_scope") == result.get("numerical_scope") == WASHER_SCOPE
            and entry.get("status") == FINITE_DISPOSITION and result.get("schema") == WASHER_SCHEMA
            and result.get("status") == WASHER_STATUS and result.get("numerical_end_disposition_complete") is True,
            "washer completion requires the typed finite end-disposition scope")
    for flag in ("actual_hardware_inspected", "isolated_scalar_curvature_is_globally_compatible",
                 "plate_fields_refresh_coupled_forces", "historical_forces_transferred", "native_CAD_or_frame_solve_run"):
        require(result.get(flag) is False, "washer disposition inferred an unsupported qualification: " + flag)
    require(result.get("actual_washer_capacity_n") is None and result.get("actual_washer_yield_mpa") is None,
            "washer reference inferred an actual product capacity")
    values, authorities = {}, {}

    def reference_path(reference):
        require(isinstance(reference, dict) and sources.get(reference.get("path")) == reference.get("sha256")
                and reference.get("sha256") is not None, "washer reference is outside authenticated source closure")
        return authenticate(root, reference["path"], reference["sha256"], resolutions, cache)

    # Only actual receipt outputs can supply records and fields. Merely listing
    # an arbitrary NPZ as a source cannot make it a saved mechanics result.
    for name, digest in sources.items():
        if Path(name).name != "receipt.json":
            continue
        path = authenticate(root, name, digest, resolutions, cache)
        document = read_json(path)
        for output, expected in document.get("output_sha256", {}).items():
            target = output_path(root, path.parent, output)
            require(target.is_relative_to(path.parent), "washer raw output escapes its receipt parent")
            authorities.setdefault(target, set()).add((path, expected))

    authenticated_packet_sources = set()

    def packet_sources(path, document):
        identity = (path, fingerprint(path, cache)[0])
        if identity in authenticated_packet_sources:
            return
        local_resolutions = {**resolutions, **document.get("source_resolution", {})}
        for source, expected in document.get("source_sha256", {}).items():
            target = authenticate(root, source, expected, local_resolutions, cache)
            target_name = target.relative_to(root).as_posix() if target.is_relative_to(root) else str(target)
            require(sources.get(target_name) == expected or sources.get(str(target)) == expected,
                    "washer raw receipt source is absent or has another basis")
        authenticated_packet_sources.add(identity)

    def artifact(reference, owner=None):
        path = reference_path(reference)
        owners = {receipt_path for receipt_path, digest in authorities.get(path, set()) if digest == reference["sha256"]}
        if owner is None:
            require(len(owners) == 1, "washer record or field has missing or ambiguous output authority")
            owner = next(iter(owners))
        else:
            require(owner in owners, "washer current plate receipt does not own this record or field")
        packet_sources(owner, read_json(owner))
        return path

    def record(reference):
        path = artifact(reference)
        if path not in values:
            if path.name.endswith(".jsonl.gz"):
                with gzip.open(path, "rt", encoding="utf-8") as stream:
                    values[path] = [json.loads(line) for line in stream]
            elif path.name.endswith(".jsonl"):
                values[path] = [json.loads(line) for line in path.read_text().splitlines()]
            else:
                values[path] = json.loads(path.read_text())
        value = values[path]
        pointer = reference.get("pointer", "")
        require(isinstance(pointer, str) and (not pointer or pointer.startswith("/")), "invalid washer record pointer")
        if pointer:
            for token in pointer[1:].split("/"):
                token = token.replace("~1", "/").replace("~0", "~")
                value = value[int(token)] if isinstance(value, list) else value[token]
        return value

    def raw_packet(reference):
        path = reference_path(reference)
        document = read_json(path)
        require(path.name == "receipt.json" and isinstance(document.get("output_sha256"), dict),
                "washer raw packet lacks output bindings")
        # Authenticate the directly consumed packet's sources through its own
        # frozen redirects. Historical receipt bytes in the closure are not a
        # request to flatten every older source version onto its original path.
        packet_sources(path, document)
        summary = read_json(bound_output(root, path.parent, document, "summary.json", cache))
        return path.parent, document, summary

    def vector(value):
        require(isinstance(value, list) and len(value) == 3 and all(finite_number(x) for x in value),
                "invalid signed washer vector")
        return value

    def close(first, second, tolerance=1e-7):
        return all(abs(a-b) <= tolerance for a, b in zip(vector(first), vector(second), strict=True))

    def dot(first, second):
        return sum(a*b for a, b in zip(vector(first), vector(second), strict=True))

    def cross(first, second):
        a, b, c = vector(first)
        d, e, f = vector(second)
        return [b*f-c*e, c*d-a*f, a*e-b*d]

    action_packet, action_receipt, action = raw_packet(result.get("action_source_receipt"))
    _inventory, accepted = finite_disposition_check(root, action, action_packet, action_receipt, sources, resolutions, cache)
    require(result.get("required_state_inventory") == action["required_state_inventory"] and accepted
            and result.get("force_branch") == "washer_updated_compatible_frame", "washer accepted source inventory differs")
    tags = {state_tag(key): item for key, item in accepted.items()}
    source_comparisons = {item["source_state_record"]["path"] for item in tags.values()}
    require(len(source_comparisons) == 1, "washer states use different response packets")
    comparison_name = next(iter(source_comparisons))
    comparison_path = authenticate(root, comparison_name, sources[comparison_name], resolutions, cache)
    comparison = read_json(comparison_path)
    frame_inputs = read_json(authenticate(root, (comparison_path.parent / "inputs.json").relative_to(root).as_posix(),
        sources[(comparison_path.parent / "inputs.json").relative_to(root).as_posix()], resolutions, cache))
    update = frame_inputs.get("washer_joint_update", {})
    require(comparison.get("analytical_branch") == "working_washer_profile_with_explicit_member_replacements"
            and frame_inputs.get("source_force_fields_relabelled") is False
            and update.get("schema") == "joint_frame_scalar_seat_update/v1" and update.get("geometry_changed") is False
            and update.get("preload_n") == 0, "washer results lack the new profile force branch")
    plate_packet, _plate_receipt, plate = raw_packet(result.get("raw_plate_receipt"))
    for name in ("end-states.jsonl", "input-plan.json"):
        path = bound_output(root, plate_packet, _plate_receipt, name, cache)
        require(path == plate_packet / name, "washer current plate record path differs")
        artifact({"path": path.relative_to(root).as_posix(), "sha256": fingerprint(path, cache)[0]},
                 plate_packet / "receipt.json")
    shaft_packet, _shaft_receipt, shaft = raw_packet(result.get("raw_shaft_receipt"))
    require(plate.get("action_source_receipt") == result["action_source_receipt"]
            and plate.get("profile_contract") == result.get("profile_contract")
            and plate.get("required_state_inventory") == action["required_state_inventory"]
            and plate.get("force_branch") == result["force_branch"]
            and shaft.get("source_join", {}).get("force_branch") == result["force_branch"]
            and shaft.get("source_join", {}).get("action_receipt_sha256") == result["action_source_receipt"]["sha256"]
            and shaft.get("all100_final_current_force_sweep") is True,
            "washer raw shaft/plate results have an old or incomplete force basis")
    profile = record(result.get("profile_contract"))
    require(profile.get("schema") == "washer_working_profile_contract/v1"
            and profile.get("status") == "FROZEN_NUMERICAL_PROFILE_CONTRACT"
            and profile.get("hypotheses") == {"E_mpa": 200000.0, "nu": 0.3, "Fy_mpa": 250.0,
                "Kwood_mpa_per_mm": 20.0, "Khead_mpa_per_mm": 10000.0, "preload_n": 0.0,
                "first_order": True, "concentric_nominal_seats": True}, "washer plate material/contact reference hypotheses differ")
    geometry_reference = result.get("canonical_geometry")
    require(reference_path(geometry_reference) == plate_packet / "input-plan.json"
            and geometry_reference.get("pointer") == "/geometry_joins", "washer geometry is not the actual plate input plan")
    geometry = record(geometry_reference)
    require(isinstance(geometry, list), "washer geometry joins are not an inventory")
    by_geometry = {(row["axis_id"], row["end_role"], row["receiver_member"]): row for row in geometry}
    axes = {axis for axis, _, _ in by_geometry}
    require(len(geometry) == len(by_geometry) == 208 and len(axes) == 104
            and TOPSIDE_AXES | CONTINUOUS_AXES <= axes
            and all({role for candidate, role, _ in by_geometry if candidate == axis} == {"head", "nut"}
                    for axis in axes), "washer canonical 104-axis/208-end geometry differs")
    plan = read_json(artifact({**geometry_reference, "pointer": ""}))
    require(plan.get("pilot_source_only") is False and plate.get("counts", {}).get("unperformed_accepted_plate_inputs") == 0
            and plate.get("counts", {}).get("missing_accepted_own_ends") == 0, "washer pilot or missing raw inputs cannot close scope")
    oracle_reference = result.get("support_oracle")
    oracle = record(oracle_reference)
    shaft_plan_name = (reference_path(oracle_reference).parent / "input-plan.json").relative_to(root).as_posix()
    shaft_plan = record({"path": shaft_plan_name, "sha256": sources.get(shaft_plan_name)})
    require(oracle.get("schema") == "joint_frame_prescribed_shaft_normal_contact_support/v1"
            and oracle.get("status") == "COMPLETE_ACTUAL_ACCEPTED_SOURCE_GEOMETRY_COUPLE_DISPOSITIONS_NOT_METAL_COMPARISONS"
            and oracle.get("historical_action_couple_values_transferred") is False
            and oracle.get("metal_comparisons_complete") is False
            and oracle.get("active_action_binding") == shaft.get("active_action_binding"), "washer TOPSIDE oracle is stale or incomplete")
    binding = oracle["active_action_binding"]
    require(binding.get("action_packet") == action_packet.relative_to(root).as_posix()
            and binding.get("action_receipt_sha256") == result["action_source_receipt"]["sha256"]
            and binding.get("response") == comparison_path.parent.relative_to(root).as_posix()
            and binding.get("source_force_fields_relabelled") is False,
            "washer TOPSIDE oracle uses another action/response basis")
    for field, filename in (("response_receipt_sha256", "receipt.json"), ("response_comparison_sha256", "comparison.json"),
                            ("response_npz_sha256", "response.npz"), ("joint_update_sha256", "joint-update.json")):
        name = (comparison_path.parent / filename).relative_to(root).as_posix()
        require(binding.get(field) == sources.get(name), "washer TOPSIDE oracle response binding differs")
    require(binding.get("joint_update_sha256") == frame_inputs.get("joint_update_sha256")
            and binding.get("profile_receipt_sha256") == update.get("profile_receipt_sha256"), "washer profile update binding differs")
    law_receipts = [name for name, digest in sources.items() if Path(name).name == "receipt.json"
                    and digest == oracle.get("historical_law_oracle_receipt_sha256")]
    require(len(law_receipts) == 1, "washer normal-traction known-answer receipt is unbound or ambiguous")
    law_receipt_path = authenticate(root, law_receipts[0], sources[law_receipts[0]], resolutions, cache)
    law_receipt = read_json(law_receipt_path)
    law = read_json(bound_output(root, law_receipt_path.parent, law_receipt, "result.json", cache))
    require(law.get("status") == "PASS_NORMAL_TRACTION_TORSION_SUPPORT_ORACLE_AND_SAVED_ACTION_DECOMPOSITION"
            and oracle.get("analytical_normal_traction_law") == law.get("proof") and law.get("proof")
            and oracle.get("hypotheses") == law.get("hypotheses") == {
                "circular_coaxial_bore": True, "first_order_normal_traction_directions": True, "friction": 0.0,
                "installation_preload_n": 0.0, "tangential_contact_or_anti_rotation_feature_credited": False,
                "washer_traction_parallel_to_shaft": True}, "washer TOPSIDE normal-contact law proof differs")
    require(law.get("known_answer_fixtures") and all(
        finite_number(row.get("bore_axial_torque_nmm")) and abs(row["bore_axial_torque_nmm"]) < 1e-10
        and finite_number(row.get("normal_end_axial_torque_nmm"))
        and abs(row["normal_end_axial_torque_nmm"]) < 2e-12 for row in law["known_answer_fixtures"]),
        "washer TOPSIDE known-answer torque identity failed")
    body_path = bound_output(root, action_packet, action_receipt, "body-actions.jsonl.gz", cache)
    body_reference = {"path": body_path.relative_to(root).as_posix(), "sha256": fingerprint(body_path, cache)[0]}
    body_records = record(body_reference)
    bodies = {(row["state_tag"], row["body"]): row for row in body_records}
    require(len(bodies) == len(body_records) == 50*len(tags), "washer current body-action census differs")
    oracle_rows = {}
    for index, row in enumerate(oracle.get("axis_states", [])):
        identity = (row["state_tag"], row["axis_id"])
        require(identity not in oracle_rows and identity[0] in tags and identity[1] in TOPSIDE_AXES
                and row.get("numerical_disposition_finite_within_declared_domain") is True
                and row.get("own_end_moments_or_metal_stress_available") is False
                and row.get("required_torsion_treated_as_zero") is False
                and row.get("source_join", {}).get("active_action_binding") == binding,
                "washer TOPSIDE oracle has an unsupported identity or claim")
        source = record(row["source_axis_state_record"])
        require(all(source.get(k) == row.get(k) for k in
            ("case_id", "gap_scale", "state_tag", "axis_id", "signed_T_n", "components_n", "V_n", "source_state_record"))
            and row["source_state_record"] == tags[identity[0]]["source_state_record"], "washer TOPSIDE source axis/state differs")
        couples = source["unrepresented_source_couples_at_physical_interface"]
        family = shaft_plan["families"][identity[1]]
        require(row.get("geometry_applicability") == family.get("geometry_applicability")
                and row.get("first_body") == source["receivers"][0]
                and row.get("second_body") == source["receivers"][1], "washer TOPSIDE physical geometry/body ordering differs")
        physical = vector(row["geometry_applicability"]["physical_interface_point_xyz_mm"])
        require(couples.get("body_action_path") == body_reference["path"]
                and couples.get("body_action_sha256") == body_reference["sha256"], "washer TOPSIDE body actions are stale")
        body = bodies[(identity[0], row["first_body"])]
        selected = [action for action in body["actions"] if action.get("row") in source["component_rows"] + [source["tie_row"]]]
        require(selected == row["exact_source_body_actions_on_first_body"] == couples["exact_source_body_actions_on_first_body"]
                and len(selected) == 3 and all(action.get("source_force_available") is True
                    and action.get("replaced_source_row_placeholder") is False for action in selected),
                "washer TOPSIDE couples do not join exact current physical body actions")
        axis = vector(row["shaft_axis_head_to_nut_xyz"])
        direction = vector(family["direction"])
        length = math.hypot(*direction)
        require(length > 0 and abs(dot(axis, axis)-1) < 1e-8 and close(axis, [x/length for x in direction]),
                "washer TOPSIDE shaft axis is not the source geometry unit axis")
        selected_by_row = {action["row"]: action for action in selected}
        require(len(source["component_rows"]) == len(source["components_n"]) == 2
                and all(finite_number(x) for x in source["components_n"])
                and finite_number(source.get("signed_T_n"))
                and all(selected_by_row[number].get("scalar_row_force_n") == value
                        for number, value in zip(source["component_rows"], source["components_n"], strict=True))
                and selected_by_row[source["tie_row"]].get("scalar_row_force_n") == source["signed_T_n"],
                "washer TOPSIDE current scalar T/V force join differs")
        lateral_force = [sum(vector(selected_by_row[number]["force_n"])[j] for number in source["component_rows"])
                         for j in range(3)]
        require(finite_number(source.get("V_n")) and math.isclose(source["V_n"], math.hypot(*lateral_force), rel_tol=1e-12, abs_tol=1e-8),
                "washer TOPSIDE current physical lateral force magnitude differs")
        components = {}
        for name, rows, stored in (("lateral", source["component_rows"], "exported_lateral_full_force_equivalent_couple_xyz_nmm"),
                                    ("axial_tie", [source["tie_row"]], "exported_axial_full_force_equivalent_couple_xyz_nmm")):
            full = [0., 0., 0.]
            for action in selected:
                if action["row"] in rows:
                    offset = [a-b for a, b in zip(vector(action["point_mm"]), physical, strict=True)]
                    moment = cross(offset, action["force_n"])
                    full = [a+b+c for a, b, c in zip(full, moment, vector(action["free_moment_nmm"]), strict=True)]
            require(close(full, couples[stored], 1e-6), "washer TOPSIDE current full couple arithmetic differs")
            components[name] = full
        components["total"] = [a+b for a, b in zip(components["lateral"], components["axial_tie"], strict=True)]
        for name, full in components.items():
            part, signed = row["components"][name], dot(axis, full)
            parallel = [signed*x for x in axis]
            perpendicular = [a-b for a, b in zip(full, parallel, strict=True)]
            require(close(part["full_couple_xyz_nmm"], full, 1e-6)
                    and finite_number(part.get("signed_parallel_nmm")) and abs(part["signed_parallel_nmm"]-signed) <= 1e-6
                    and close(part["parallel_couple_xyz_nmm"], parallel, 1e-6)
                    and close(part["perpendicular_couple_xyz_nmm"], perpendicular, 1e-6), "washer TOPSIDE decomposition differs")
        require(isinstance(source.get("bearing_lengths_mm"), list) and len(source["bearing_lengths_mm"]) == 2
                and all(finite_number(x, positive=True) for x in source["bearing_lengths_mm"]), "invalid TOPSIDE bearing lengths")
        gate = sum(source["bearing_lengths_mm"])*1e-6
        above = abs(dot(axis, components["total"])) > gate
        classification = ("LOAD_PATH_INCOMPATIBILITY_OF_ISOLATED_FULL_SOURCE_WRENCH_NORMAL_CONTACT_BRANCH" if above else
                          "SOURCE_GEOMETRY_COUPLE_LIMIT_WITH_TORSION_WITHIN_ORIGINAL_ABSOLUTE_GATE")
        require(row.get("original_length_scaled_moment_gate_nmm") == gate
                and row.get("required_torsion_exceeds_original_moment_gate") is above
                and row.get("classification") == classification, "washer TOPSIDE torque disposition differs")
        oracle_rows[identity] = ({**oracle_reference, "pointer": f"/axis_states/{index}"}, row)
    require(set(oracle_rows) == {(tag, axis) for tag in tags for axis in TOPSIDE_AXES}
            and oracle.get("counts", {}).get("accepted_states") == len(tags)
            and oracle["counts"].get("limited_axis_states") == 4*len(tags)
            and oracle["counts"].get("own_ends_remaining_null") == 8*len(tags), "washer TOPSIDE oracle inventory differs")
    required = {(result["force_branch"], tag, *identity) for tag in tags for identity in by_geometry}
    rows = result.get("end_dispositions", [])
    seen, histogram, exceedances = set(), {}, 0
    for row in rows:
        key = tuple(row.get("join_key", []))
        require(key in required and key not in seen, "washer disposition has a missing, duplicate or foreign end identity")
        seen.add(key)
        _, tag, axis, role, body = key
        raw = record(row.get("source_plate_record"))
        require(reference_path(row["source_plate_record"]) == plate_packet / "end-states.jsonl"
                and re.fullmatch(r"/[0-9]+", row["source_plate_record"].get("pointer", "")), "washer raw plate pointer differs")
        source = raw["source"]
        end = record(row.get("source_own_end_record"))
        end_reference = dict(source["source_endrecord"])
        if "line_index" in end_reference:
            end_reference["pointer"] = "/" + str(end_reference.pop("line_index"))
        require(tuple(source.get("join_key", [])) == key and row["source_own_end_record"] == end_reference
                and row.get("source_state_record") == source.get("source_state_record") == tags[tag]["source_state_record"]
                and row.get("source_force_compatibility") is (axis in CONTINUOUS_AXES)
                and source.get("source_force_compatibility") is row["source_force_compatibility"], "washer signed source end/state join differs")
        require((end.get("state_tag"), end.get("axis_id"), end.get("end_role"),
                 end.get("receiver_member", end.get("receiver"))) == (tag, axis, role, body), "washer own-end pointer identifies another end")
        if axis not in CONTINUOUS_AXES:
            shaft_state = record(row.get("source_shaft_state_record"))
            axis_source = record(row.get("source_axis_state_record"))
            require(reference_path(row["source_shaft_state_record"]).is_relative_to(shaft_packet)
                    and (shaft_state.get("state_tag"), shaft_state.get("axis_id")) == (tag, axis)
                    and (axis_source.get("state_tag"), axis_source.get("axis_id")) == (tag, axis)
                    and axis_source.get("source_state_record") == tags[tag]["source_state_record"], "washer scalar shaft source basis differs")
        status = row.get("status")
        require(status in {WASHER_FINITE, WASHER_ZERO, WASHER_HEAD, WASHER_TOPSIDE},
                "ordinary missing/solver STOP is not a finite washer disposition")
        histogram[status] = histogram.get(status, 0)+1
        if status == WASHER_TOPSIDE:
            oracle_binding, oracle_row = oracle_rows[(tag, axis)]
            require(axis in TOPSIDE_AXES and raw.get("status") == "SOURCE_END_MOMENT_UNAVAILABLE"
                    and end.get("status") == "NULL_UNSUPPORTED" and end.get("own_end_M_signed_xyz_nmm") is None
                    and shaft_state.get("status") == source.get("source_shaft_status") == "SOURCE_GEOMETRY_COUPLE_METHOD_LIMIT"
                    and row.get("source_axis_state_record") == oracle_row["source_axis_state_record"]
                    and row.get("support_oracle_record") == oracle_binding
                    and row.get("source_couple_classification") == oracle_row["classification"]
                    and row.get("source_moments_unavailable_not_zero") is True
                    and row.get("nominal_source_point_support_does_not_qualify_actual_shaft_seat") is True,
                    "washer TOPSIDE method limit is not the exact authenticated four-axis limitation")
        else:
            require(raw.get("status") == status and source.get("geometry") == by_geometry[(axis, role, body)],
                    "washer disposition differs from actual plate status/geometry")
            if axis in CONTINUOUS_AXES:
                require(end.get("continuous_own_end") is True and end.get("own_end_moment_unknown_not_zero") is False,
                        "washer continuous own-end moment is unavailable")
                tension, moment = end["signed_end_compression_n"], vector(end["own_end_wood_moment_xyz_nmm"])
                datum = vector(end["support"]["seat_point_xyz_mm"])
            else:
                require(end.get("status") == "COMPLETE_ISOLATED_END_SOURCE", "washer source end is not actually completed")
                require(shaft_state.get("status") in {"SUPPORTED_ISOLATED_CURRENT_FORCE_FIELD", "REFERENCE_EXCEEDANCE"}
                        and shaft_state.get("source_join", {}).get("active_action_binding") == binding
                        and end.get("source_join", {}).get("active_action_binding") == binding,
                        "washer completed end is attached to a stopped or stale scalar shaft")
                state, family = shaft_state.get("state", {}), shaft_state.get("effective_family", {})
                shaft_length = family.get("host_length_mm", 0)+family.get("cleat_length_mm", 0)
                stationary = state.get("scaled_gradient_residuals_n", [])
                require(finite_number(shaft_length, positive=True) and stationary
                        and all(finite_number(x) and abs(x) <= 1e-6 for x in stationary)
                        and finite_number(state.get("host_force_balance_residual_n")) and abs(state["host_force_balance_residual_n"]) <= 1e-6
                        and finite_number(state.get("host_moment_balance_residual_nmm"))
                        and abs(state["host_moment_balance_residual_nmm"]) <= shaft_length*1e-6
                        and (state.get("state_tag"), state.get("axis_id")) == (tag, axis)
                        and state.get("signed_T_n") == axis_source.get("signed_T_n")
                        and state.get("V_n") == axis_source.get("V_n"), "washer scalar shaft original signed equilibrium gate failed")
                tension, moment = end["normal_compression_T_n"], vector(end["own_end_M_signed_xyz_nmm"])
                datum = vector(end["end_wrench_datum_global_xyz_mm"])
                require(close(end["normal_into_receiver_xyz"], source["normal_into_receiver_xyz"])
                        and close(end["force_on_receiver_xyz_n"], source["force_on_receiver_xyz_n"]), "washer own-end signed force differs")
            normal = vector(source["normal_into_receiver_xyz"])
            magnitude = math.hypot(*moment)
            require(finite_number(tension) and tension >= 0 and abs(dot(normal, normal)-1) < 1e-8
                    and abs(dot(normal, moment)) <= 1e-6 and source.get("T_n") == tension
                    and close(source["source_signed_own_M_xyz_nmm"], moment, 1e-6)
                    and source.get("M_magnitude_nmm") == magnitude
                    and close(source["force_on_receiver_xyz_n"], [tension*x for x in normal], 1e-6)
                    and close(source["own_seat_xyz_mm"], datum, 1e-5)
                    and close(datum, by_geometry[(axis, role, body)]["datum_xyz_mm"], 1e-5), "washer current signed load arithmetic differs")
            geometry_normal = by_geometry[(axis, role, body)].get("saved_normal_into_receiver_xyz")
            require(geometry_normal is None or close(normal, geometry_normal), "washer force reverses its saved support normal")
            chart = [vector(source["chart_x_xyz"]), vector(source["chart_y_xyz"])]
            first = source["plate_pressure_first_moment_targets_nmm"]
            require(len(first) == 2 and all(finite_number(x) for x in first)
                    and close([sum(first[i]*cross(chart[i], normal)[j] for i in range(2)) for j in range(3)], moment, 1e-6),
                    "washer pressure chart loses the signed own-end moment")
            if status == WASHER_FINITE:
                stress = raw.get("sampled_stress_proxy_mpa")
                require(finite_number(stress) and stress >= 0 and row.get("metal_stress_mpa") == stress
                        and row.get("metal_reference_index") == raw.get("stress_proxy_over_Fy250") == stress/250
                        and raw.get("sampled_reference_exceeded") is (stress > 250)
                        and row.get("actual_field_exists") is raw.get("actual_field_exists") is True
                        and row.get("retained_field") == raw.get("retained_field"), "washer saved metal reference arithmetic differs")
                shapes = npz_shapes(artifact(row["retained_field"], plate_packet / "receipt.json"))
                require(len(shapes.get("pose_mm", ())) == 1 and shapes["pose_mm"][0] > 0, "washer actual saved plate pose is absent")
                contacts = raw.get("signed_equilibrium_and_contact", [])
                require(len(contacts) == 2 and {r.get("contact") for r in contacts} == {"wood", "head"}, "washer signed contact audits missing")
                for contact in contacts:
                    name = contact["contact"]
                    require(len(shapes.get(name+"_pressure_mpa", ())) == 1 and shapes[name+"_pressure_mpa"][0] > 0
                            and shapes.get(name+"_area_mm2") == shapes[name+"_pressure_mpa"]
                            and shapes.get(name+"_local_xy_mm") == (shapes[name+"_pressure_mpa"][0], 2), "washer saved pressure field is absent")
                    require(contact.get("signed_equilibrium_passed") is True
                            and finite_number(contact.get("force_vector_max_residual_n")) and 0 <= contact["force_vector_max_residual_n"] <= .001
                            and finite_number(contact.get("moment_vector_max_residual_nmm")) and 0 <= contact["moment_vector_max_residual_nmm"] <= .02
                            and contact.get("inactive_pressure_max_mpa") == contact.get("unilateral_law_residual_mpa") == 0
                            and finite_number(contact.get("pressure_peak_mpa")) and contact["pressure_peak_mpa"] >= 0
                            and close(contact["force_on_receiver_xyz_n"], source["force_on_receiver_xyz_n"], .001)
                            and close(contact["own_seat_M_signed_xyz_nmm"], moment, .02), "washer actual signed force/contact gate failed")
                exceedances += stress > 250
            elif status == WASHER_ZERO:
                require(tension == magnitude == 0 and moment == [0, 0, 0] and source["force_on_receiver_xyz_n"] == [0, 0, 0]
                        and row.get("metal_stress_mpa") == row.get("metal_reference_index") == raw.get("sampled_stress_proxy_mpa")
                        == raw.get("stress_proxy_over_Fy250") == 0, "washer rounded or unknown demand was called exact zero")
            else:
                radius = by_geometry[(axis, role, body)]["profile_binding"]["plate_profile"]["head_radius_mm"]
                require(finite_number(radius, positive=True) and magnitude > tension*radius
                        and source.get("head_compression_certificate", {}).get("status") == WASHER_HEAD
                        and source["head_compression_certificate"].get("pressing_outer_radius_mm") == radius
                        and source["head_compression_certificate"].get("necessary_condition_only") is True
                        and row.get("head_circle_bound") == {"T_n": tension, "M_magnitude_nmm": magnitude,
                            "signed_M_xyz_nmm": moment, "pressing_radius_mm": radius,
                            "maximum_normal_contact_moment_nmm": tension*radius, "necessary_bound_exceeded": True,
                            "no_steel_stress_or_capacity_inferred": True}, "washer head-circle bound is not satisfied by current signed loads")
        if status != WASHER_FINITE:
            require(row.get("actual_field_exists") is raw.get("actual_field_exists") is False
                    and "retained_field" not in row and "retained_field" not in raw, "washer no-field disposition carries an invented metal field")
        if status in {WASHER_HEAD, WASHER_TOPSIDE}:
            require(row.get("metal_stress_mpa") is row.get("metal_reference_index") is raw.get("sampled_stress_proxy_mpa")
                    is raw.get("stress_proxy_over_Fy250") is None, "washer source-method limit was turned into a metal pass")
    expected = {"accepted_states": len(tags), "canonical_physical_ends": 208, "required_accepted_end_states": 208*len(tags),
        "recorded_end_dispositions": len(rows), "unassessed_accepted_end_states": 0,
        "unavailable_required_state_ends": 208*(14-len(tags)), "status_counts": histogram,
        "finite_metal_fields": histogram.get(WASHER_FINITE, 0), "TOPSIDE_null_metal_ends": histogram.get(WASHER_TOPSIDE, 0),
        "sampled_Fy250_exceedances": exceedances}
    require(seen == required and histogram.get(WASHER_TOPSIDE) == 8*len(tags)
            and result.get("counts") == expected and receipt.get("counts") == expected
            and result.get("metal_comparisons_complete") is all(row["status"] in {WASHER_FINITE, WASHER_ZERO} for row in rows),
            "washer finite-disposition census/comparison completion differs from actual accepted ends")


def npz_shapes(path):
    """Read only NumPy headers; never materialize a mechanics matrix or field."""
    shapes = {}
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            require(name.endswith(".npy") and name[:-4] not in shapes, "invalid or duplicate saved array")
            with archive.open(name) as stream:
                magic = stream.read(8)
                require(magic[:6] == b"\x93NUMPY" and magic[6:] in (b"\x01\x00", b"\x02\x00", b"\x03\x00"),
                        "invalid saved NumPy header")
                size_format = "<H" if magic[6] == 1 else "<I"
                size = struct.unpack(size_format, stream.read(struct.calcsize(size_format)))[0]
                require(0 < size <= 65536, "oversized saved NumPy header")
                header = ast.literal_eval(stream.read(size).decode("utf-8" if magic[6] == 3 else "latin1"))
                require(isinstance(header, dict), "invalid saved NumPy header object")
                shape = header.get("shape")
                require(isinstance(shape, tuple) and all(type(n) is int and n >= 0 for n in shape)
                        and isinstance(header.get("descr"), str) and "O" not in header["descr"]
                        and type(header.get("fortran_order")) is bool, "invalid saved array layout")
                dtype = re.fullmatch(r"[<>=|][biufc](\d+)", header["descr"])
                require(dtype is not None and archive.getinfo(name).file_size
                        == stream.tell() + math.prod(shape) * int(dtype[1]), "truncated or unsupported saved numeric array")
                shapes[name[:-4]] = shape
    return shapes


def small_numeric_array(path, name, shape):
    """Read a bounded numerical witness, never a large stiffness or response field."""
    require(math.prod(shape) <= 4096 and npz_shapes(path).get(name) == shape, "invalid small numerical witness shape")
    with zipfile.ZipFile(path) as archive, archive.open(name + ".npy") as stream:
        magic = stream.read(8)
        size_format = "<H" if magic[6] == 1 else "<I"
        size = struct.unpack(size_format, stream.read(struct.calcsize(size_format)))[0]
        header = ast.literal_eval(stream.read(size).decode("utf-8" if magic[6] == 3 else "latin1"))
        require(header["descr"] in ("<f8", "=f8") and header["fortran_order"] is False,
                "small witness must use contiguous float64 values")
        values = struct.unpack("<" + "d" * math.prod(shape), stream.read())
    require(all(finite_number(value) for value in values), "nonfinite small numerical witness")
    return values


def assembled_energy_check(energy, load_matrix):
    """Check recorded total Pi up to the declared unchanged-body constant."""
    fields = ("potential_nmm", "body_elastic_energy_nmm", "connector_energy_nmm", "external_work_nmm",
              "body_load_chi_nmm", "interface_body_load_cross_work_nmm", "interface_elastic_energy_nmm",
              "rigid_external_work_nmm", "complementary_energy_nmm", "primal_complementary_identity_error_nmm")
    require(isinstance(energy, dict) and all(finite_number(energy.get(field)) for field in fields),
            "assembled energy has missing or nonfinite terms")
    c = energy.get("external_coefficients")
    require(isinstance(c, list) and len(c) == 12 and all(finite_number(value) for value in c)
            and energy.get("energy_constant_scope") == PARTIAL_ENERGY_CONSTANT
            and isinstance(energy.get("unchanged_constant_token"), str) and energy["unchanged_constant_token"]
            and all(energy.get(field) is None for field in ("unchanged_body_load_chi_nmm",
                "body_elastic_energy_unchanged_offset_nmm", "external_work_unchanged_offset_nmm"))
            and all(isinstance(energy.get(field), str) and re.fullmatch(r"[0-9a-f]{64}", energy[field])
                    for field in ("external_wrench_sha256", "joint_law_sha256")),
            "assembled load or common-constant contract missing")
    chi = .5 * sum(c[i] * load_matrix[12 * i + j] * c[j] for i in range(12) for j in range(12))
    cross = energy["interface_body_load_cross_work_nmm"]
    values = {"body_load_chi_nmm": chi,
              "body_elastic_energy_nmm": energy["interface_elastic_energy_nmm"] - cross + chi,
              "external_work_nmm": energy["rigid_external_work_nmm"] + 2 * chi - cross,
              "potential_nmm": energy["body_elastic_energy_nmm"] + energy["connector_energy_nmm"] - energy["external_work_nmm"],
              "primal_complementary_identity_error_nmm": abs(energy["potential_nmm"] + chi + energy["complementary_energy_nmm"])}
    require(all(math.isclose(energy[field], value, rel_tol=1e-9, abs_tol=1e-7) for field, value in values.items()),
            "assembled potential or full load-matrix cross terms differ")
    require(energy["connector_energy_nmm"] >= 0 and energy["interface_elastic_energy_nmm"] >= 0,
            "negative stored connector or interface energy")


def representative_field_audit(audit, gates):
    accepted_audit({"audit": audit})
    accepted_audit({"audit": audit.get("original_frame_audit")})
    residuals, tolerances = audit.get("actual_scalar_residuals"), audit.get("tolerances")
    require(set(gates) <= set(audit.get("checks", {}))
            and isinstance(residuals, dict) and residuals and isinstance(tolerances, dict)
            and set(residuals) <= set(tolerances)
            and all(finite_number(value) and finite_number(tolerances[name], positive=True)
                    and abs(value) <= tolerances[name] for name, value in residuals.items()),
            "selected full-field numerical residuals fail or lack their audit thresholds")


def body_field_shape_check(shapes):
    nodes, elements = shapes.get("nodes_mm", ()), shapes.get("elements", ())
    require(len(nodes) == len(elements) == 2 and nodes[0] > 0 and nodes[1] == 3
            and elements[0] > 0 and elements[1] == 20
            and all(shapes.get(name) == (3 * nodes[0],) for name in
                    ("recovered_U_mm", "total_U_mm", "force_n", "all_node_residual_n")),
            "selected comparison has no complete nonempty C3D20 body field")


def operator_field_shape_check(shapes):
    nodes, elements, active = shapes.get("nodes_mm", ()), shapes.get("elements", ()), shapes.get("active_port_rows", ())
    require(len(nodes) == len(elements) == 2 and nodes[0] > 0 and nodes[1] == 3
            and elements[0] > 0 and elements[1] == 20 and len(active) == 1
            and 0 < active[0] <= CURRENT_COUPLED_PORT_COUNT, "selected native operator mesh or active port inventory missing")
    n, dofs, ports = CURRENT_COUPLED_PORT_COUNT, 3 * nodes[0], active[0]
    expected = {"H": (n, n), "e": (n, 12), "L": (12, 12), "D": (n, 6), "W": (6, 12),
                "physical_R": (dofs, 6), "external_F_n": (dofs, 12), "U_F_mm": (dofs, 12),
                "U_B_mm": (dofs, ports), "port_B_indptr": (n + 1,), "port_B_shape": (2,),
                "original_scalar_gauges": (6,), "projected_rhs_n": (dofs, ports + 12),
                "projected_residual_n": (dofs, ports + 12)}
    data = shapes.get("port_B_data", ())
    require(all(shapes.get(name) == shape for name, shape in expected.items())
            and len(data) == 1 and data[0] > 0 and shapes.get("port_B_indices") == data,
            "selected operator lacks its full port/load basis, quotient solution or CSR footprint")


def mapping_audit_check(port, external):
    require(port.get("full_native_affine_targets_retained") is True and port.get("physical_side_ownership_retained") is True
            and port.get("kinematic_tie_or_crack_stitch_added") is False
            and external.get("original_full_body_load_basis_affine_targets_retained") is True
            and external.get("contact_adhesion_or_crack_stitch_credited") is False
            and external.get("signed_consistent_external_body_forces_permitted") is True,
            "mapping changes source affine work, physical side ownership or contact law")
    columns = external.get("columns", [])
    require(len(columns) == 12 and {row.get("column") for row in columns} == set(range(12)),
            "mapping omits an original external load column")
    require(isinstance(port.get("columns"), list) and port["columns"], "physical port mapping columns missing")
    for row in port["columns"] + columns:
        if row.get("zero_external_basis_column") is True:
            continue
        require(type(row.get("affine_rank")) is int and 0 < row["affine_rank"] <= 4
                and finite_number(row.get("scaled_force_first_moment_residual"))
                and 0 <= row["scaled_force_first_moment_residual"] < 1e-8
                and row.get("first_moment_scale_mm") == 100.
                and row.get("recovered_contact_pressure_or_preload_claimed") is False
                and type(row.get("signed_bilateral_tractions_permitted")) is bool,
                "source affine footprint audit fails or invents pressure/preload")
        if row["signed_bilateral_tractions_permitted"] is False:
            normal = row.get("normal_only_nonnegative_traction_audit", {})
            require(normal.get("status") in {"Solved", "AlmostSolved"}
                    and normal.get("nonnegative_weight_tolerance") == 1e-10
                    and finite_number(normal.get("minimum_scalar_weight"))
                    and normal["minimum_scalar_weight"] >= -1e-10
                    and finite_number(normal.get("maximum_scalar_equality_residual"))
                    and 0 <= normal["maximum_scalar_equality_residual"] < 1e-8,
                    "normal footprint needs adhesion or fails its scalar equality")


def mapping_known_answer_check(proof, output):
    require(proof.get("schema") == "splitting_coupled_interface_operator_known_answer/v1"
            and proof.get("status") == "PASS_SOURCE_SIDE_MAPPING_AND_LOCALIZED_OPERATOR_KNOWN_ANSWER"
            and proof.get("configurations") == 6 and proof.get("external_load_basis_columns") == 12
            and all(proof.get(key) is True for key in ("source_moment_and_rigid_virtual_work_retained",
                "same_physical_footprints_across_intact_initial_final", "normal_contact_nonnegative_scalar_traction_assessed",
                "unbalanced_unit_columns_projected_only_for_elastic_inverse"))
            and all(proof.get(key) is False for key in ("full_assembly_energy_known_answer_replaced",
                "project_body_domain_or_resource_feasibility_transferred", "physical_or_complete_joint_acceptance")),
            "coupled affine/load mapping known-answer scope is missing or overclaimed")
    groups = proof.get("records", [])
    require(len(groups) == 2 and {group.get("RT_binding") for group in groups} == {"R=u,T=v", "R=v,T=-u"},
            "mapping known answer omits a material orientation")
    for group in groups:
        operators = group.get("operators", [])
        require(len(operators) == 3 and {op.get("configuration") for op in operators} == {"intact", "initial", "final"},
                "mapping known answer omits a crack phase")
        for operator in operators:
            accepted_audit({"audit": operator.get("operator_audit")})
            accepted_audit({"audit": operator.get("solution_audit")})
            errors = operator.get("relative_operator_errors", {})
            require(set(errors) == {"H", "e", "L", "D", "W"}
                    and operator.get("complete_native_force_and_nine_first_moments_retained") is True
                    and all(finite_number(value) and 0 <= value < 1e-8 for value in [*errors.values(),
                        operator.get("relative_U_error"), operator.get("rigid_virtual_work_error_nmm"),
                        operator.get("general_affine_virtual_work_error_nmm")]),
                    "localized/mapped known answer differs from the monolithic field or affine work")
            mapping_audit_check(operator.get("physical_port_mapping_audit", {}),
                                operator.get("external_body_load_mapping_audit", {}))
            require({"nodes_mm", "elements", "original_raw_rhs", "projected_rhs", "recovered_U_mm",
                    "monolithic_U_mm", "residual_n", "physical_R", "port_B", "external_F", "H", "e", "L", "D", "W"}
                    <= set(npz_shapes(output(operator.get("field")))), "mapping known answer lacks its actual saved field")


def projected_receipt_resolutions(root, receipt, resolutions):
    """Preserve legacy snapshot audit lists without treating them as redirects."""
    local = receipt.get("source_resolution", {})
    if isinstance(local, dict):
        return {**resolutions, **local}
    require(isinstance(local, list), "invalid projected proof source resolution")
    for item in local:
        require(isinstance(item, dict) and item.get("resolution") == "DECLARED_EXACT_PRODUCER_SNAPSHOT"
                and receipt.get("source_sha256", {}).get(item.get("resolved_path")) == item.get("expected_sha256")
                and isinstance(item.get("expected_sha256"), str), "legacy snapshot audit lacks its exact retained source pin")
        file_path(root, item.get("source_key"), absolute=True)
        file_path(root, item.get("resolved_path"))
    # Historical lists can contain several frozen versions of one producer.
    # Their source_sha256 already names each snapshot; none redirects live bytes.
    return dict(resolutions)


def projected_operator_method_check(group, expected, paired_output, source_packet):
    """Join the explicit Schur correction to its original fields and known answer."""
    operators = group.get("operators", [])
    require(group.get("schema") == "splitting_coupled_body_operator_group/v1"
            and group.get("status") == "PASS_ACTUAL_COUPLED_BODY_OPERATOR_GROUP"
            and len(operators) == group.get("native_operator_count") == 3
            and {item.get("variant", {}).get("id") for item in operators} == set(expected),
            "projected/native operator publication has a different phase inventory")
    for item in operators:
        require(item.get("variant") == expected[item["variant"]["id"]], "projected operator literal variant differs")
        accepted_audit({"audit": item.get("physical_audit")})
    method = group.get("numerical_method_id")
    if method is None:
        require(all(item.get("assembly_method", {}).get("numerical_method_id") is None for item in operators),
                "projected operator method was omitted from its group")
        return
    require(method == PROJECTED_OPERATOR_METHOD and group.get("raw_rejection_preserved") is True,
            "unrecognized or concealed projected operator method")
    proof = paired_output(group.get("precision_recovery_binding"))
    known = paired_output(group.get("saved_monolithic_cross_work_proof"))
    require(proof.get("schema") == "splitting_factor_free_schur_precision_diagnostic/v1"
            and proof.get("status") == "PASS_FACTOR_FREE_PROJECTED_ELASTIC_QUOTIENT_AND_ORIGINAL_FIELD_GATES"
            and proof.get("raw_rejection_preserved") is True and proof.get("accepted_body_operator_published") is False
            and proof.get("original_packet") == group.get("raw_factor_rejection_binding")
            and len(proof.get("records", [])) == 1, "projected operator correction lacks its paired actual proof")
    raw_reference = group.get("raw_factor_rejection_binding")
    raw = source_packet(raw_reference)
    if raw.get("status") != "PASS_ACTUAL_COUPLED_BODY_OPERATOR_GROUP":
        output_sha = raw.get("output_sha256", {}).get("stop.json")
        require(isinstance(output_sha, str), "projected method has no authenticated raw gate disposition")
        stop = paired_output({"path": (Path(raw_reference["path"]).parent / "stop.json").as_posix(), "sha256": output_sha})
        require(stop.get("exception") == "RuntimeError" and stop.get("message") == "Localized rigid operator audit failed",
                "ordinary native STOP cannot be waived by projected method")
    report = proof["records"][0]
    accepted_audit({"audit": report})
    require(report.get("numerical_method_id") == method and report.get("RHS_projection_added") is False,
            "projected operator changes its source RHS or method")
    certificate = report.get("quotient_projection", {})
    accepted_audit({"audit": certificate})
    require(certificate.get("method_id") == method
            and all(certificate.get(flag) is False for flag in ("full_native_stiffness_projected",
                "source_rhs_projected_again", "per_variant_elastic_quotient_preservation_assumed"))
            and {"six_physical_rigid_columns_full_rank", "QR_orthogonality", "correction_formula_roundoff_bound",
                 "union_elastic_quotient_defect_within_measured_orthogonality_and_roundoff"} <= set(certificate["checks"]),
            "projected operator lacks the explicit six-mode correction certificate")
    for field in ("orthogonality_error_fro", "correction_formula_error_fro_n_per_mm", "union_elastic_quotient_defect_fro_n_per_mm",
                  "measured_orthogonality_bound_n_per_mm", "matrix_product_roundoff_bound_n_per_mm"):
        require(finite_number(certificate.get(field)) and certificate[field] >= 0, "invalid projected operator correction bound")
    require(certificate["orthogonality_error_fro"] < 1e-12
            and certificate["correction_formula_error_fro_n_per_mm"] <= certificate["matrix_product_roundoff_bound_n_per_mm"]
            and certificate["union_elastic_quotient_defect_fro_n_per_mm"] <=
            certificate["measured_orthogonality_bound_n_per_mm"] + certificate["matrix_product_roundoff_bound_n_per_mm"],
            "projected operator correction exceeds its measured formula/quotient bound")
    recoveries = report.get("native_rhs_recovery", [])
    require(len(recoveries) == 3 and {item.get("variant", {}).get("id") for item in recoveries} == set(expected),
            "projected operator original recovery omits a phase")
    for recovery in recoveries:
        variant = recovery.get("variant", {})
        require(variant == expected.get(variant.get("id")), "projected recovery belongs to another grid/material/phase")
        accepted_audit({"audit": recovery})
        rigid = recovery.get("original_rigid_audit", {})
        require(rigid.get("status") == "PASS_ELASTIC_QUOTIENT_SCREEN" and rigid.get("rigid_leakage_rel_limit") == 5e-14
                and finite_number(rigid.get("relative_KR_inf")) and 0 <= rigid["relative_KR_inf"] <= 5e-14,
                "projected operator bypassed the original rigid screen")
        effects = recovery.get("projection_effects", {})
        accepted_audit({"audit": effects})
        for field in ("actual_exported_full_K_force_residual_n", "projection_port_force_effect_peak_n",
                      "projection_diagonal_work_effect_relative", "full_rhs_work_reciprocity_relative"):
            require(finite_number(effects.get(field)) and effects[field] >= 0, "invalid projected operator physical effect")
        error = recovery.get("relative_energy_identity_error")
        require(finite_number(error) and error >= 0
                and effects["actual_exported_full_K_force_residual_n"] + effects["projection_port_force_effect_peak_n"] < 1e-5
                and effects["projection_diagonal_work_effect_relative"] + error < 1e-8
                and effects["full_rhs_work_reciprocity_relative"] < 1e-8,
                "projected operator force/work correction exceeds the original budget")
        for field in ("full_H_e_L_cross_work_relative_errors", "full_H_e_L_change_relative_errors"):
            errors = effects.get(field, {})
            require(set(errors) == {"H", "e", "L"} and all(finite_number(x) and 0 <= x < 1e-8 for x in errors.values()),
                    "projected operator omits or fails full H/e/L cross-work")
        item = next(item for item in operators if item["variant"]["id"] == variant["id"])
        assembly = item.get("assembly_method", {})
        require(assembly.get("numerical_method_id") == method
                and assembly.get("precision_recovery_binding") == group["precision_recovery_binding"]
                and assembly.get("saved_monolithic_cross_work_proof") == group["saved_monolithic_cross_work_proof"]
                and assembly.get("original_factor_packet") == group.get("raw_factor_rejection_binding"),
                "projected operator metadata has a stale correction/known-answer/raw binding")
        for name in ("operator", "solution"):
            audit = item["physical_audit"].get(name, {})
            accepted_audit({"audit": audit})
            require(audit.get("precision_recovery_binding") == group["precision_recovery_binding"]
                    and audit.get("projection_effects") == effects, "projected exported operator changed its actual effect audit")
    require(known.get("schema") == "splitting_schur_precision_saved_known_answer_audit/v1"
            and known.get("status") == "PASS_SAVED_MONOLITHIC_FIELDS_AND_FULL_H_e_L_CROSS_WORK"
            and known.get("new_matrix_assembly_or_factorization") is False
            and known.get("project_body_acceptance_transferred") is False
            and len(known.get("records", [])) == 6
            and {(item.get("RT_binding"), item.get("configuration")) for item in known["records"]}
            == {(rt, phase) for rt in ("R=u,T=v", "R=v,T=-u") for phase in ("intact", "initial", "final")},
            "projected method lacks the exact six saved monolithic known answers")
    for item in known["records"]:
        errors = item.get("relative_H_e_L_work_errors", {})
        require(item.get("all_passed") is True and set(errors) == {"H", "e", "L"}
                and all(finite_number(x) and 0 <= x < 1e-8 for x in errors.values())
                and finite_number(item.get("relative_U_error")) and 0 <= item["relative_U_error"] < 1e-8
                and finite_number(item.get("relative_full_rhs_work_reciprocity"))
                and 0 <= item["relative_full_rhs_work_reciprocity"] < 1e-8, "projected saved monolithic field/cross-work oracle failed")


def representative_scope_check(root, entry, result, packet, receipt, sources, resolutions, cache):
    """Validate the frozen selected coupled scope without completing historical fixed-F rows."""
    if entry.get("numerical_scope") != REPRESENTATIVE_SCOPE:
        require(entry.get("status") != REPRESENTATIVE_COMPLETE and result.get("schema") != REPRESENTATIVE_SCHEMA,
                "representative completion lacks its typed scope")
        return
    require(entry.get("status") == REPRESENTATIVE_COMPLETE and result.get("schema") == REPRESENTATIVE_SCHEMA
            and result.get("status") == REPRESENTATIVE_STATUS and result.get("representative_study_complete") is True
            and result.get("selected_comparison_inventory_complete") is True
            and result.get("original_inventory_completed") is False and result.get("full_splitting_qualification") is False
            and result.get("historical_force_basis_transferred") is False,
            "representative study overclaims completion or transfers a historical force basis")
    selection = source_json(root, result.get("selection_binding"), sources, resolutions, cache)
    require(selection.get("schema") == "splitting_representative_coupled_selection/v1"
            and selection.get("numerical_scope") == REPRESENTATIVE_SCOPE
            and selection.get("original_inventory_count") == 37056
            and selection.get("original_unsampled_disposition") == "UNASSESSED_OUTSIDE_REVISED_SCOPE"
            and selection.get("original_inventory_completion_transferred") is False,
            "selection loses the original inventory or labels unsampled paths as passes")
    original_binding = selection.get("original_inventory_binding", {})
    require(original_binding.get("sha256") == ORIGINAL_SPLITTING_INVENTORY_SHA256, "original splitting inventory pin changed")
    original = source_json(root, original_binding, sources, resolutions, cache)
    old_paths = {}
    for body in original.get("records", []):
        for path in body.get("finite_paths", []):
            key = body["body"], path["id"]
            require(key not in old_paths, "duplicate original splitting path")
            old_paths[key] = path
    require(len(original.get("records", [])) == 44 and len(old_paths) == 772,
            "original 44-body/772-path inventory changed")
    prepared_reference = selection.get("prepared_binding")
    prepared = source_json(root, prepared_reference, sources, resolutions, cache)
    prepared_packet = file_path(root, prepared_reference["path"]).parent
    plan = read_json(bound_output(root, prepared_packet, prepared, "plan.json", cache))
    duties = {row["joint_id"]: row for row in plan.get("duties", [])}
    families = selection.get("family_manifest", {}).get("families", [])
    duty_ids = [name for family in families for name in family.get("duty_ids", [])]
    timber_names = {body["body"] for body in original["records"]}
    require(len(duties) == len(duty_ids) == len(set(duty_ids)) == 30 and set(duty_ids) == set(duties)
            and len(families) == len({family.get("id") for family in families}) == 8
            and set(selection.get("family_manifest", {}).get("canonical_timber_names", [])) == timber_names
            and {name for duty in duties.values() for name in duty.get("timber_sides", [])} == timber_names,
            "selected family manifest omits original duties or timber contexts")
    for family in families:
        require(set(family.get("timber_sides", [])) == {name for duty in family["duty_ids"] for name in duties[duty]["timber_sides"]}
                and family.get("nominal_screen_is_fracture_or_capacity_proof") is False
                and family.get("mirror_force_or_geometry_pass_transferred") is False,
                "selected family context transfers nominal or mirror acceptance")
    state_requirements = state_map(selection.get("required_state_dispositions"))
    eligible_states = REQUIRED_STATES
    eligibility = selection.get("baseline_eligibility_binding")
    baseline_inputs = None
    if eligibility is not None:
        require(isinstance(eligibility, dict) and set(eligibility) == {"receipt", "comparison"},
                "selected baseline eligibility binding missing")
        baseline_receipt = source_json(root, eligibility["receipt"], sources, resolutions, cache)
        baseline_packet = file_path(root, eligibility["receipt"]["path"]).parent
        baseline = source_json(root, eligibility["comparison"], sources, resolutions, cache)
        require(bound_output(root, baseline_packet, baseline_receipt, "comparison.json", cache)
                == file_path(root, eligibility["comparison"]["path"]), "baseline comparison lacks its paired receipt")
        baseline_sources = baseline_receipt.get("source_sha256")
        require(isinstance(baseline_sources, dict) and baseline_sources, "eligible baseline source closure missing")
        baseline_resolutions = {**resolutions, **baseline_receipt.get("source_resolution", {})}
        for name, digest in baseline_sources.items():
            authenticate(root, name, digest, baseline_resolutions, cache)
        dispositions, accepted = frame_dispositions(root, baseline, baseline_packet, baseline_receipt,
                                                   baseline_sources, baseline_resolutions, cache)
        require(baseline.get("analytical_branch") == "working_washer_profile_with_explicit_member_replacements"
                and canonical(selection.get("baseline_state_dispositions")) == canonical(baseline["case_dispositions"])
                and selection.get("baseline_unavailable_dispositions_are_cracked_body_limits") is False
                and selection.get("repeated_baseline_floor_searches_per_crack_variant") is False,
                "selected baseline domain hides unavailable states or transfers cracked-body failure")
        eligible_states = set(accepted)
        require(eligible_states and set(state_requirements) == eligible_states,
                "eligible state inventory differs from audited baseline fields")
        outside = state_map(selection.get("outside_eligible_baseline_state_dispositions"))
        require(set(outside) == REQUIRED_STATES - eligible_states,
                "unavailable baseline state complement is incomplete")
        baseline_inputs = read_json(bound_output(root, baseline_packet, baseline_receipt, "inputs.json", cache))
        joint_update = selection.get("global_joint_update_binding")
        source_json(root, joint_update, sources, resolutions, cache)
        require(bound_output(root, baseline_packet, baseline_receipt, "joint-update.json", cache)
                == file_path(root, joint_update["path"]), "selected joint update lacks baseline output authority")
        for key, item in {**state_requirements, **outside}.items():
            reference = item.get("source_baseline_disposition", {})
            _, disposition = source_document(root, reference, sources, resolutions, cache)
            require(reference.get("path") == eligibility["comparison"]["path"]
                    and reference.get("sha256") == eligibility["comparison"]["sha256"]
                    and re.fullmatch(r"/case_dispositions/[0-9]+", reference.get("pointer", ""))
                    and disposition == dispositions[key]
                    and item.get("state_tag") == state_tag(key)
                    and item.get("baseline_accepted_force_field_exists") is (key in eligible_states),
                    "eligible source disposition pointer or force availability differs")
            if key in eligible_states:
                state_reference = item.get("baseline_response_state_ref", {})
                _, original_state = source_document(root, state_reference, sources, resolutions, cache)
                require(state_reference.get("path") == eligibility["comparison"]["path"]
                        and state_reference.get("sha256") == eligibility["comparison"]["sha256"]
                        and re.fullmatch(r"/states/[0-9]+", state_reference.get("pointer", ""))
                        and original_state == accepted[key], "eligible baseline response pointer differs")
            else:
                require(item.get("status") == item.get("unavailable_source_state_disposition")
                        == "OUTSIDE_ELIGIBLE_BASELINE_FORCE_FIELD_DOMAIN"
                        and item.get("unavailable_cracked_body_equilibrium_claim") is False
                        and item.get("cracked_variant_infeasibility_claimed") is False
                        and item.get("fresh_variant_floor_search_required") is False
                        and "baseline_response_state_ref" not in item,
                        "unavailable source state claims a fresh cracked-body result")
        require(selection.get("required_operator_state_disposition_count")
                == len(selection.get("operator_variants", [])) * len(eligible_states),
                "eligible operator-state count differs")
    require(set(state_requirements) == eligible_states and all(item.get("state_tag") == state_tag(key)
            and item.get("changed_model_requires_fresh_disposition") is True for key, item in state_requirements.items()),
            "representative required state inventory is incomplete or transfers old dispositions")
    action_binding = result.get("active_action_binding", {})
    action_receipt = source_json(root, {"path": action_binding.get("receipt"), "sha256": action_binding.get("sha256")},
                                 sources, resolutions, cache)
    action_inputs = read_json(bound_output(root, file_path(root, action_binding["receipt"]).parent,
                                          action_receipt, "inputs.json", cache))
    require(finite_number(action_inputs.get("dead_load_factor"), positive=True), "selected external dead-load factor missing")
    if eligibility is not None:
        action_packet = file_path(root, action_binding["receipt"]).parent
        action = read_json(bound_output(root, action_packet, action_receipt, "summary.json", cache))
        action_sources = action_receipt.get("source_sha256", {})
        for reference in eligibility.values():
            require(action_sources.get(reference["path"]) == reference["sha256"],
                    "selected action lacks its new baseline source binding")
        _, action_states = finite_disposition_check(root, action, action_packet, action_receipt,
                                                  sources, resolutions, cache)
        require(set(action_states) == eligible_states
                and action_inputs.get("dead_load_factor") == baseline_inputs.get("dead_load_factor")
                and all(item["source_disposition_record"]["path"] == eligibility["comparison"]["path"]
                        and item["source_disposition_record"]["sha256"] == eligibility["comparison"]["sha256"]
                        for item in action["required_state_inventory"]),
                "selected action transfers a historical force field or different baseline load")
    source_frame = result.get("source_frame_binding", {})
    source_json(root, source_frame, sources, resolutions, cache)
    if eligibility is not None:
        original_native_frame = result.get("original_native_frame_binding", {})
        source_json(root, original_native_frame, sources, resolutions, cache)
        require(source_frame == eligibility["receipt"]
                and baseline_inputs.get("source_frame_sha256") == original_native_frame["sha256"]
                and baseline_inputs.get("joint_update_sha256") == selection["global_joint_update_binding"]["sha256"],
                "eligible baseline uses different original body or joint-law sources")
        original_operator_selection = source_json(root, selection.get("operator_selection_binding"),
                                                 sources, resolutions, cache)
        require(canonical(selection.get("operator_variants")) == canonical(original_operator_selection.get("operator_variants")),
                "eligible selection changed its frozen native operator identities")
    variants, required = {}, {}
    for variant in selection.get("operator_variants", []):
        identifier = variant.get("id")
        require(isinstance(identifier, str) and identifier and identifier not in variants
                and variant.get("configuration") in {"intact", "initial", "final"}, "invalid or duplicate operator variant")
        variants[identifier] = variant
    domains = {}
    for row in selection.get("required_comparisons", []):
        identifier = row.get("id")
        identity = splitting_identity(row)
        key = state_key(row)
        require(isinstance(identifier, str) and identifier and identifier not in required
                and key in state_requirements
                and identity[1] == state_tag(key) and row.get("changed_model_requires_fresh_disposition") is True
                and row.get("absolute_assembled_potential_claimed") is False
                and row.get("old_fixed_force_contact_upper_bound_transferred") is False,
                "invalid or duplicate selected comparison identity")
        require(row.get("source_baseline_disposition") == state_requirements[key].get("source_baseline_disposition"),
                "selected comparison has a different baseline disposition")
        _, baseline = source_document(root, row["source_baseline_disposition"], sources, resolutions, cache)
        require(state_key(baseline) == key and baseline.get("accepted_force_field_exists")
                is row.get("baseline_accepted_force_field_exists"), "selected baseline state provenance differs")
        _, geometry = source_document(root, row.get("geometry_binding"), sources, resolutions, cache)
        require(hashlib.sha256(canonical(geometry).encode()).hexdigest() == row.get("geometry_sha256"),
                "selected geometry record digest differs")
        source_document(root, row.get("material_binding"), sources, resolutions, cache)
        action_field = "source_action_receipt"
        if eligibility is None:
            require(row.get(action_field) == {"path": action_binding.get("receipt"), "sha256": action_binding.get("sha256")},
                    "selected comparison uses a stale reconciled action basis")
        else:
            action_field = "historical_port_action_receipt"
            source_json(root, row.get(action_field), sources, resolutions, cache)
            require("source_action_receipt" not in row and row.get("baseline_eligibility_binding") == eligibility
                    and row.get("global_joint_update_binding") == selection["global_joint_update_binding"]
                    and row.get("source_action_force_transfer") is False
                    and row.get("baseline_accepted_force_field_exists") is True,
                    "selected comparison transfers old actions or a different profile baseline")
        domain = canonical({field: row.get(field) for field in ("body", "path", "mesh_size_mm", "RT_binding",
                            "geometry_binding", "material_binding", "boundary_footprint_id", "coupling_method_id")})
        require(key not in domains.setdefault(domain, set()), "duplicate selected variant/state identity")
        domains[domain].add(key)
        operators = row.get("operator_variants", {})
        require(set(operators) == {"intact", "initial", "final"}, "selected comparison omits a crack phase")
        for phase, operator_id in operators.items():
            variant = variants.get(operator_id, {})
            require(variant.get("configuration") == phase and all(variant.get(field) == row.get(field)
                    for field in ("body", "path", "mesh_size_mm", "RT_binding", "geometry_binding", "material_binding",
                                  "geometry_sha256", "boundary_footprint_id", "coupling_method_id"))
                    and variant.get("source_action_receipt") == row.get(action_field)
                    and variant.get("crack_interval_mm") == (None if phase == "intact" else row["path"][phase + "_interval_mm"]),
                    "selected operator phase/grid/material/boundary identity differs")
        projection = row.get("original_path_projection")
        if projection is not None:
            require(splitting_identity(projection) == identity and canonical(projection["path"])
                    == canonical(old_paths.get((row["body"], row["path"]["id"]))),
                    "original path projection is not a literal source identity")
        required[identifier] = row
    require(required and len(required) == selection.get("required_comparison_count")
            and len(variants) == selection.get("native_operator_variant_budget")
            and all(keys == eligible_states for keys in domains.values())
            and {operator for row in required.values() for operator in row["operator_variants"].values()} == set(variants),
            "selection omits requested state or operator variants")
    grid_material_domains = {}
    for row in required.values():
        key = canonical({field: row.get(field) for field in ("body", "path", "geometry_binding", "material_binding",
                                                            "boundary_footprint_id", "coupling_method_id")})
        grid_material_domains.setdefault(key, set()).add((row["mesh_size_mm"], row["RT_binding"]))
    require(all(values == {(size, binding) for size in (15, 20) for binding in ("R=u,T=v", "R=v,T=-u")}
                for values in grid_material_domains.values()), "selection omits a requested grid/R-T variant")
    authorities = {output_path(root, packet, name): digest for name, digest in receipt["output_sha256"].items()}
    for reference in result.get("artifact_receipts", []):
        paired = source_json(root, reference, sources, resolutions, cache)
        paired_packet = file_path(root, reference["path"]).parent
        redirects = projected_receipt_resolutions(root, paired, resolutions)
        for name, digest in paired.get("source_sha256", {}).items():
            authenticate(root, name, digest, redirects, cache)
        outputs = paired.get("output_sha256")
        require(isinstance(outputs, dict) and outputs, "selected artifact receipt has no output authority")
        for name, digest in outputs.items():
            path = output_path(root, paired_packet, name)
            authenticate(root, path.relative_to(root).as_posix(), digest, {}, cache)
            require(path not in authorities or authorities[path] == digest, "conflicting selected output authorities")
            authorities[path] = digest

    def output(reference):
        require(isinstance(reference, dict), "selected saved artifact reference missing")
        path = file_path(root, reference.get("path"))
        require(reference.get("sha256") is not None and authorities.get(path) == reference["sha256"],
                "selected field/checkpoint lacks paired receipt output authority")
        authenticate(root, reference["path"], reference["sha256"], {}, cache)
        return path

    def paired_method_output(reference):
        path = file_path(root, reference.get("path"))
        name = (path.parent / "receipt.json").relative_to(root).as_posix()
        paired = source_json(root, {"path": name, "sha256": sources.get(name)}, sources, resolutions, cache)
        require(bound_output(root, path.parent, paired, path.name, cache) == path
                and fingerprint(path, cache)[0] == reference.get("sha256"), "projected proof lacks paired output authority")
        redirects = {**resolutions, **paired.get("source_resolution", {})}
        for source, digest in paired.get("source_sha256", {}).items():
            authenticate(root, source, digest, redirects, cache)
        return read_json(path)

    validated_groups = {}
    operator_states = {}
    require(isinstance(result.get("operator_state_dispositions"), list), "operator-state disposition inventory missing")
    for item in result["operator_state_dispositions"]:
        key = item.get("operator_variant_id"), state_key(item)
        require(key[0] in variants and key not in operator_states, "duplicate or unknown operator-state disposition")
        require(item.get("status") in {ACCEPTED_STATE, FLOOR_STOP}, "unassessed or ordinary stopped operator state")
        if item["status"] == ACCEPTED_STATE:
            require(item.get("accepted_force_field_exists") is True, "accepted operator state has no force field")
            output(item.get("response_ref"))
            output(item.get("checkpoint_ref"))
        else:
            require(item.get("accepted_force_field_exists") is False and "response_ref" not in item
                    and "checkpoint_ref" not in item, "stopped operator state exports a reaction or body field")
            diagnostic = read_json(output(item.get("diagnostic_ref")))
            require(diagnostic.get("operator_variant_id") == key[0] and state_key(diagnostic["identity"]) == key[1]
                    and diagnostic.get("source_frame_receipt_sha256") == source_frame["sha256"]
                    and diagnostic.get("accepted_force_field_exists") is False
                    and diagnostic.get("physical_frame_failure_claim") is False
                    and diagnostic.get("physical_equilibrium_nonexistence_proven") is False
                    and not {"response_ref", "reaction_ref", "retained_field", "retained_reaction_field"} & set(diagnostic)
                    and diagnostic.get("floor_search_summary") == floor_summary(diagnostic.get("exception")),
                    "operator-state stop lacks its fresh finite model-specific trace")
        operator_states[key] = item
    require(set(operator_states) == {(identifier, key) for identifier in variants for key in eligible_states},
            "required operator-state dispositions remain unassessed")
    actual, finite = {}, {}
    for field, target in (("records", actual), ("finite_dispositions", finite)):
        require(isinstance(result.get(field), list), "selected result lacks its exact actual/finite partition")
        for row in result[field]:
            identifier = row.get("id")
            require(identifier in required and identifier not in actual and identifier not in finite
                    and canonical(row.get("identity")) == canonical(required[identifier]),
                    "missing, duplicate or altered selected comparison identity")
            target[identifier] = row
    require(set(actual) | set(finite) == set(required) and result.get("pending_comparison_ids") == [],
            "selected required comparisons remain unassessed")
    gates = selection.get("required_field_gates")
    require(isinstance(gates, list) and len(gates) == len(set(gates)) and REPRESENTATIVE_FIELD_GATES <= set(gates),
            "selected field gates omit required mechanics or source identities")

    def checkpoint_check(identity, phase, reference):
        checkpoint = read_json(output(reference))
        disposition = operator_states[identity["operator_variants"][phase], state_key(identity)]
        require(checkpoint.get("identity") == identity and checkpoint.get("phase") == phase
                and checkpoint.get("operator_variant_id") == identity["operator_variants"][phase]
                and disposition.get("status") == ACCEPTED_STATE
                and disposition.get("checkpoint_ref") == reference
                and disposition.get("response_ref") == checkpoint.get("reaction_ref"),
                "saved checkpoint has a different phase or selected identity")
        audit = checkpoint.get("physical_audit", {})
        representative_field_audit(audit, gates)
        body_shapes = npz_shapes(output(checkpoint.get("retained_field")))
        body_field_shape_check(body_shapes)
        operator = output(checkpoint.get("operator_ref"))
        operator_field_shape_check(npz_shapes(operator))
        L = small_numeric_array(operator, "L", (12, 12))
        reaction_reference = checkpoint.get("reaction_ref")
        reaction = read_json(output(reaction_reference))
        pointer = reaction_reference.get("pointer")
        if pointer is not None:
            require(isinstance(pointer, str) and pointer.startswith("/"), "invalid selected reaction pointer")
            for token in pointer[1:].split("/"):
                reaction = reaction[int(token)] if isinstance(reaction, list) else reaction[token]
        require(isinstance(reaction, dict) and state_key(reaction) == state_key(identity)
                and reaction.get("operator_variant_id") == identity["operator_variants"][phase]
                and reaction.get("accepted_force_field_exists") is True
                and (eligibility is None or reaction.get("joint_update_binding") == selection["global_joint_update_binding"]),
                "rejected, stale-law or wrong-state coupled force field exported")
        representative_field_audit(reaction.get("physical_audit", {}), gates)
        frame_shapes = npz_shapes(output(reaction.get("retained_reaction_field")))
        require(frame_shapes.get("frame_force_n") == frame_shapes.get("frame_relative_motion_mm") == (3192,)
                and frame_shapes.get("frame_rigid_scaled_mm") == (344,) and frame_shapes.get("frame_bearing") == (8,),
                "selected coupled field has a different current port/coordinate layout")
        energy = checkpoint.get("energy")
        require(energy == reaction.get("energy"), "checkpoint energy differs from its re-solved reaction state")
        assembled_energy_check(energy, L)
        coefficients = [0.] * 12
        column = 0 if identity["case_id"] == "dead-only" else 2 * CASES.index(identity["case_id"])
        coefficients[column] = action_inputs["dead_load_factor"]
        if identity["case_id"] != "dead-only":
            coefficients[column + 1] = 1.
        require(energy["external_coefficients"] == coefficients
                and energy["unchanged_constant_token"] == source_frame["sha256"]
                and checkpoint.get("source_frame_receipt_sha256") == source_frame["sha256"],
                "selected case load coefficients or unchanged-body source token differ")
        for field in ("external_load", "port_footprint"):
            contract_reference = checkpoint.get(field + "_contract_ref")
            output(contract_reference)
            require(contract_reference["sha256"] == checkpoint.get(field + "_contract_sha256"),
                        "selected immutable contract lacks its saved source artifact")
        external = read_json(output(checkpoint["external_load_contract_ref"]))
        footprint = read_json(output(checkpoint["port_footprint_contract_ref"]))
        require(external.get("schema") == "splitting_coupled_external_basis_contract/v1"
                and external.get("source_frame_binding") == source_frame
                and (eligibility is None or external.get("original_native_frame_binding") == original_native_frame)
                and external.get("baseline_eligibility_binding") == eligibility
                and external.get("active_action_binding") == action_binding
                and external.get("dead_load_factor") == action_inputs["dead_load_factor"]
                and external.get("original_complete_twelve_column_F_W_retained") is True
                and external.get("same_source_external_basis_between_crack_phases") is True
                and external.get("same_interface_reaction_between_crack_phases_required") is False,
                "selected external basis contract differs from the current case/source domain")
        native_body = source_json(root, external.get("native_source_body_binding"), sources, resolutions, cache)
        native_packet = file_path(root, external["native_source_body_binding"]["path"]).parent
        require(footprint.get("schema") == "splitting_coupled_physical_footprint_contract/v1"
                and footprint.get("geometry_sha256") == identity["geometry_sha256"]
                and footprint.get("working_joint_update_binding") == selection.get("global_joint_update_binding")
                and all(footprint.get(key) is True for key in ("original_force_and_all_nine_first_moments_preserved",
                    "retained_physical_source_side_only", "contact_normal_scalar_weights_nonnegative",
                    "crack_seam_nodes_excluded_without_stitching",
                    "bilateral_bolt_and_consistent_external_body_forces_are_declared_separately")),
                "selected source footprint changes affine work, normal traction or crack connectivity")
        for field, filename in (("native_source_B_authority", "source-body-B.npz"),
                                ("native_source_body_basis", "source-body.npz")):
            native_reference = footprint.get(field, {})
            require(sources.get(native_reference.get("path")) == native_reference.get("sha256")
                    and bound_output(root, native_packet, native_body, filename, cache)
                    == file_path(root, native_reference.get("path")), "selected native port/load source is not paired-output-owned")
        group_reference = footprint.get("operator_group_binding")
        group_key = canonical(group_reference)
        if group_key not in validated_groups:
            group = read_json(output(group_reference))
            expected = {identifier: variants[identifier] for identifier in identity["operator_variants"].values()}
            projected_operator_method_check(group, expected, paired_method_output,
                lambda reference: source_json(root, reference, sources, resolutions, cache))
            validated_groups[group_key] = group
        group = validated_groups[group_key]
        native_operator = next((item for item in group["operators"] if item["variant"]["id"] == checkpoint["operator_variant_id"]), {})
        require(native_operator.get("operator_ref") == checkpoint.get("operator_ref"),
                "selected checkpoint does not use its audited native operator publication")
        mappings = [read_json(output(item)) for item in footprint.get("actual_operator_mapping_records", [])]
        require(len(mappings) == 3 and {item.get("variant", {}).get("configuration") for item in mappings}
                == {"intact", "initial", "final"}, "selected physical mapping omits a crack phase")
        for mapping in mappings:
            variant = mapping.get("variant", {})
            require(variant == variants.get(variant.get("id")) and variant["id"] in identity["operator_variants"].values(),
                    "selected physical mapping belongs to another native operator")
            mapping_audit_check(mapping.get("port_mapping", {}), mapping.get("external_mapping", {}))
        area = checkpoint.get("actual_crack_area_mm2")
        require(finite_number(area) and area >= 0
                and checkpoint.get("absolute_assembled_potential_claimed") is False,
                "selected crack area or absolute potential claim invalid")
        return checkpoint, energy, area

    for row in actual.values():
        identity, energies, areas, checkpoints = row["identity"], {}, {}, {}
        for phase in ("intact", "initial", "final"):
            checkpoints[phase], energies[phase], areas[phase] = checkpoint_check(identity, phase, row.get(phase + "_checkpoint"))
        for field in ("external_coefficients", "external_wrench_sha256", "unchanged_constant_token", "joint_law_sha256"):
            require(all(energies[phase][field] == energies["intact"][field] for phase in ("initial", "final")),
                    "selected external load, connector law or shared energy constant changes between cracks")
        for field in ("external_load_contract_sha256", "port_footprint_contract_sha256", "source_frame_receipt_sha256"):
            value = checkpoints["intact"].get(field)
            require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
                    and all(checkpoints[phase].get(field) == value for phase in ("initial", "final")),
                    "selected immutable load/port/source-frame contracts differ between phases")
        area = areas["final"] - areas["initial"]
        G = (energies["initial"]["potential_nmm"] - energies["final"]["potential_nmm"]) / area if area > 0 else None
        require(finite_number(area, positive=True) and row.get("added_sound_area_mm2") == area
                and finite_number(row.get("signed_G_n_per_mm"))
                and math.isclose(row["signed_G_n_per_mm"], G, rel_tol=1e-9, abs_tol=1e-7)
                and row.get("Gc_n_per_mm") == identity.get("unmeasured_Gc_all_modes_n_per_mm")
                and finite_number(row.get("Gc_n_per_mm"), positive=True)
                and math.isclose(row.get("conditional_energy_reference_index", math.nan), max(0., G) / row["Gc_n_per_mm"],
                                 rel_tol=1e-9, abs_tol=1e-7)
                and row.get("upper_reference") is None, "selected signed total-Pi G/area/reference arithmetic differs")
        stress = checkpoints["intact"].get("sampled_sigma90_mpa")
        require(finite_number(stress) and row.get("intact_sampled_sigma90_mpa") == stress
                and row.get("Ft90_mpa") == identity.get("unmeasured_Ft90_mpa")
                and finite_number(row.get("Ft90_mpa"), positive=True)
                and math.isclose(row.get("conditional_initiation_reference_index", math.nan), stress / row["Ft90_mpa"],
                                 rel_tol=1e-9, abs_tol=1e-7), "selected intact stress/reference arithmetic differs")
    for row in finite.values():
        diagnostic = read_json(output(row.get("diagnostic_ref")))
        require(diagnostic.get("identity") == row["identity"] and diagnostic.get("status") == FLOOR_STOP
                and diagnostic.get("accepted_force_field_exists") is False
                and diagnostic.get("physical_frame_failure_claim") is False
                and diagnostic.get("physical_equilibrium_nonexistence_proven") is False
                and diagnostic.get("changed_model_requires_fresh_disposition") is True
                and diagnostic.get("floor_search_summary") == floor_summary(diagnostic.get("exception"))
                and row.get("forces_exported") is False and row.get("strength_pass_claimed") is False,
                "selected stop is not a fresh finite floor-search disposition")
        require(diagnostic.get("operator_variant_id") in row["identity"]["operator_variants"].values()
                and diagnostic.get("source_frame_receipt_sha256") == source_frame["sha256"],
                "selected finite diagnostic transfers a stale model branch")
        operator_field_shape_check(npz_shapes(output(diagnostic.get("operator_ref"))))
        phase_states = [operator_states[identifier, state_key(row["identity"])]
                        for identifier in row["identity"]["operator_variants"].values()]
        require(any(item.get("diagnostic_ref") == row.get("diagnostic_ref") for item in phase_states),
                "selected diagnostic differs from its operator-state disposition")
        for item in phase_states:
            if item["status"] == ACCEPTED_STATE:
                phase = variants[item["operator_variant_id"]]["configuration"]
                checkpoint_check(row["identity"], phase, item["checkpoint_ref"])
    coupon = read_json(output(result.get("assembled_known_answer")))
    require(coupon.get("schema") == "joint_frame_member_replacement_known_answer/v1"
            and coupon.get("status") == "PASS_ASSEMBLED_REPLACEMENT_ENERGY_KNOWN_ANSWER"
            and coupon.get("body_remove_reinsert_exact") is True and coupon.get("unchanged_rest_body_chi_cancellation") is True
            and math.isclose(coupon.get("G_n_per_mm", math.nan), .185142857142857, abs_tol=1e-7)
            and math.isclose(coupon.get("analytic_G_n_per_mm", math.nan), .185142857142857, abs_tol=1e-7)
            and coupon.get("cross_term_body_load_chi_nmm") == 26.125
            and math.isclose(coupon.get("explicit_body_load_potential_nmm", math.nan), -14.82, abs_tol=1e-7),
            "assembled coupling/energy known-answer evidence missing or inconsistent")
    mapping_known_answer_check(read_json(output(result.get("interface_mapping_known_answer"))), output)
    if result.get("splitting_workstream_complete") is True:
        coverage = result.get("family_coverage")
        require(isinstance(coverage, list) and len(coverage) == len(families) == 8
                and {row.get("family_id") for row in coverage} == {row.get("id") for row in families}
                and all(row.get("status") in {"DIRECT_AUDITED_SELECTED_RESULTS", "AUDITED_REPRESENTATIVE_BOUND",
                                               "JUSTIFIED_FINITE_NUMERICAL_DISPOSITION"} for row in coverage),
                "representative pilot falsely completes unresolved connection families")
        for row in coverage:
            evidence = read_json(output(row.get("evidence_ref")))
            family = next(item for item in families if item["id"] == row["family_id"])
            require(evidence.get("family_id") == row["family_id"] and evidence.get("status") == row["status"]
                    and evidence.get("strength_of_unsampled_paths_established") is False
                    and evidence.get("duty_ids") == family.get("duty_ids"),
                    "family coverage lacks its actual source-bound disposition")
            if row["status"] == "DIRECT_AUDITED_SELECTED_RESULTS":
                identifiers = evidence.get("comparison_ids")
                require(isinstance(identifiers, list) and identifiers and len(identifiers) == len(set(identifiers))
                        and all(identifier in actual and required[identifier]["body"] in family.get("timber_sides", [])
                                for identifier in identifiers), "family direct coverage has no applicable actual comparisons")
            elif row["status"] == "JUSTIFIED_FINITE_NUMERICAL_DISPOSITION":
                identifiers = evidence.get("finite_disposition_ids")
                require(isinstance(identifiers, list) and identifiers and len(identifiers) == len(set(identifiers))
                        and all(identifier in finite and required[identifier]["body"] in family.get("timber_sides", [])
                                for identifier in identifiers), "family finite coverage has no applicable diagnostic")
            else:
                identifiers = evidence.get("bound_witness_comparison_ids")
                require(isinstance(identifiers, list) and identifiers and all(identifier in actual for identifier in identifiers)
                        and evidence.get("actual_action_receipt_sha256") == action_binding["sha256"]
                        and evidence.get("nominal_resultant_only_bound") is False,
                        "family representative bound lacks current-force numerical witnesses")
                accepted_audit(evidence)


def motion_scope_check(root, entry, result, packet, receipt, sources, resolutions, cache):
    """Authenticate finite fixed-force pose bounds without extending their stability claim."""
    if entry.get("numerical_scope") != MOTION_SCOPE:
        require(result.get("schema") != MOTION_SCHEMA, "motion result lacks its typed numerical scope")
        return
    require(entry.get("status") == COMPLETE and result.get("schema") == MOTION_SCHEMA
            and result.get("status") == MOTION_STATUS
            and result.get("first_order_stability_implication_assessment_complete") is True,
            "motion scope is not a completed fixed-force disposition")
    for flag in ("second_order_stability_established", "source_force_fields_changed",
                 "source_producers_frame_native_or_CAD_executed", "numerical_goal_complete"):
        require(result.get(flag) is False, "motion scope overclaims: " + flag)
    require(result.get("baseline_300_certificate_transferred", False) is False
            and result.get("current_system_coordinate_count", 344) == 344,
            "historical 300-coordinate certificate transferred")
    if "fixed_force_reference_bounds" in result:
        bounds = result["fixed_force_reference_bounds"]
        require(bounds.get("classification") == "CONSERVATIVE_NUMERICAL_FIXED_FORCE_POSE_BOUNDS"
                and bounds.get("coordinate_layout") == {"body_scaled_coordinates": 300, "shaft_scaled_coordinates": 20,
                                                       "washer_scaled_coordinates": 24}
                and bounds.get("coordinate_interval_count") == 344 * len(result.get("states", []))
                and bounds.get("reviewed_bolt_axis_count") == 104 and bounds.get("Hillman_screw_axis_count") == 66,
                "motion current-system reference metadata differs")
        for field in ("original_contact_clearance_and_spring_laws_preserved", "original_no_slip_floor_law_preserved",
                      "source_100_mm_hold_lever_preserved", "norm_bounds_are_conservative_component_box_bounds",
                      "actual_disk_witnesses_original_law_audited"):
            require(bounds.get(field) is True, "motion source law or bound interpretation differs: " + field)
        for field in ("source_geometry_and_hardware_changed", "absolute_elastic_deformed_node_motion_envelope_established",
                      "changed_force_branch_envelope_established", "outer_polyhedron_extrema_are_accepted_contact_poses"):
            require(bounds.get(field) is False, "motion reference scope overclaims: " + field)
    request = read_json(bound_output(root, packet, receipt, "request.json", cache))
    require(request.get("schema") == "joint_frame_fixed_force_motion_request/v1"
            and request.get("fixed_force_only") is True and request.get("motion_tolerance_mm") == 1e-8
            and request.get("coefficient_roundoff_threshold") == 1e-11,
            "motion source-law or numerical contract differs")
    require(canonical(result.get("source_sha256")) == canonical(sources)
            and canonical(request.get("required_state_inventory")) == canonical(result.get("required_state_inventory")),
            "motion request or source closure differs")
    action_name, frame_name = request["actions"] + "/receipt.json", request["response"] + "/receipt.json"
    action_receipt = source_json(root, {"path": action_name, "sha256": sources.get(action_name)}, sources, resolutions, cache)
    frame_receipt = source_json(root, {"path": frame_name, "sha256": sources.get(frame_name)}, sources, resolutions, cache)
    action = read_json(bound_output(root, file_path(root, request["actions"]), action_receipt, "summary.json", cache))
    frame = read_json(bound_output(root, file_path(root, request["response"]), frame_receipt, "comparison.json", cache))
    frame_record_path = request["response"] + "/comparison.json"
    frame_record_sha256 = fingerprint(file_path(root, frame_record_path), cache)[0]
    require(action.get("schema") == ACTION_SCHEMA and frame.get("schema") == FRAME_SCHEMA
            and canonical(result["required_state_inventory"]) == canonical(action.get("required_state_inventory")),
            "motion uses a different reconciled force inventory")
    inventory, states = state_map(result["required_state_inventory"]), state_map(result.get("states"))
    require(set(inventory) == REQUIRED_STATES, "motion required-state inventory is incomplete")
    accepted = {key for key, item in inventory.items() if item.get("accepted_force_field_exists") is True
                and item.get("status") == ACCEPTED_STATE}
    require(set(states) == accepted and set(request.get("accepted_tags", [])) == {state_tag(key) for key in accepted}
            and len(request["accepted_tags"]) == len(accepted), "motion exports missing or rejected states")
    shapes = npz_shapes(bound_output(root, packet, receipt, "certificates.npz", cache))
    extra_arrays = "certificate_arrays" in result
    suffixes = ("nullspace", "A_ub", "b_ub", "dual_multipliers", "coordinate_extrema")
    if extra_arrays:
        suffixes += ("fixed_rows", "inactive_rows", "free_pairs", "free_gaps")
        binding = result["certificate_arrays"]
        require(binding == {"path": (packet / "certificates.npz").relative_to(root).as_posix(),
                            "sha256": fingerprint(packet / "certificates.npz", cache)[0]},
                "motion certificate-array binding differs")
    require(set(shapes) == {state_tag(key) + "_" + suffix for key in accepted for suffix in suffixes},
            "motion saved certificate inventory contains missing or rejected states")
    for key, item in inventory.items():
        require(item["source_disposition_record"].get("path") == frame_record_path
                and item["source_disposition_record"].get("sha256") == frame_record_sha256,
                "motion uses stale frame-disposition provenance")
        _, disposition = source_document(root, item["source_disposition_record"], sources, resolutions, cache)
        require(state_key(disposition) == key and disposition.get("status") == item.get("status")
                and disposition.get("accepted_force_field_exists") is item.get("accepted_force_field_exists"),
                "motion disposition points to a different source state")
        if key not in accepted:
            require(item.get("status") == FLOOR_STOP and item.get("accepted_force_field_exists") is False
                    and item.get("physical_equilibrium_nonexistence_proven") is False,
                    "motion unavailable state lacks its finite source disposition")
    bounded_bodies = bounded_all = witnesses = 0
    for key, state in states.items():
        tag = state_tag(key)
        require(state.get("state_tag") == tag and state.get("source_state_record") == inventory[key]["source_state_record"],
                "motion accepted state provenance differs")
        require(state["source_state_record"].get("path") == frame_record_path
                and state["source_state_record"].get("sha256") == frame_record_sha256,
                "motion uses stale frame-state provenance")
        _, original = source_document(root, state["source_state_record"], sources, resolutions, cache)
        require(state_key(original) == key, "motion source pointer identifies another state")
        accepted_audit(original)
        accepted_audit({"audit": state.get("original_law_audit")})
        intervals, certificates = state.get("coordinate_increment_intervals_scaled_mm"), state.get("coordinate_bound_certificates")
        nullity, rank = state.get("coordinate_nullity"), state.get("fixed_row_svd", {}).get("rank")
        require(type(nullity) is int and type(rank) is int and 0 <= nullity <= 344 and rank + nullity == 344
                and type(state.get("body_projection_rank")) is int
                and state["body_projection_rank"] + state.get("metal_only_nullity", -1) == nullity
                and shapes[tag + "_nullspace"] == (344, nullity)
                and isinstance(intervals, list) and len(intervals) == 344
                and isinstance(certificates, list) and len(certificates) == 344,
                "motion does not assess the full 344-coordinate system")
        require(len(shapes[tag + "_A_ub"]) == 2 and shapes[tag + "_A_ub"][1] == nullity
                and shapes[tag + "_b_ub"] == (shapes[tag + "_A_ub"][0],)
                and len(shapes[tag + "_dual_multipliers"]) == 2
                and shapes[tag + "_dual_multipliers"][1] == shapes[tag + "_A_ub"][0]
                and len(shapes[tag + "_coordinate_extrema"]) == 2
                and shapes[tag + "_coordinate_extrema"][1] == nullity,
                "motion certificate array dimensions differ")
        rays = state.get("recession_certificates")
        require(isinstance(rays, list), "motion recession certificate inventory missing")
        for interval, certificate in zip(intervals, certificates, strict=True):
            require(isinstance(interval, list) and len(interval) == 2 and isinstance(certificate, dict), "invalid motion interval")
            for i, side in enumerate(("lower", "upper")):
                support = certificate.get(side, {})
                if interval[i] is None:
                    index = support.get("recession_certificate")
                    require(support.get("status") == "unbounded" and type(index) is int and 0 <= index < len(rays),
                            "motion unbounded coordinate lacks a recession certificate")
                else:
                    require(finite_number(interval[i]) and support.get("status") == "finite"
                            and finite_number(support.get("maximum"))
                            and math.isclose(support["maximum"], (-1 if i == 0 else 1) * interval[i], abs_tol=1e-9),
                            "motion interval differs from its support certificate")
                    if support.get("zero_observable") is True:
                        require(support["maximum"] == 0, "nonzero motion has a zero-observable certificate")
                    else:
                        require(all(finite_number(support.get(field)) for field in
                                    ("primal_value", "dual_residual", "primal_violation_mm", "minimum_dual"))
                                and support["dual_residual"] < 1e-8 and support["primal_violation_mm"] < 1e-8
                                and support["minimum_dual"] >= -1e-9
                                and abs(support["primal_value"] - support["maximum"]) < 1e-7 * max(abs(support["primal_value"]), 1),
                                "motion finite support has a failed primal/dual certificate")
                        if extra_arrays:
                            row = support.get("dual_multiplier_row")
                            require(type(row) is int and 0 <= row < shapes[tag + "_dual_multipliers"][0],
                                    "motion dual support lacks its saved row")
            require(interval[0] is None or interval[1] is None or interval[0] <= interval[1], "inverted motion interval")
        for ray in rays:
            checks = ray.get("checks", {})
            require(isinstance(ray.get("coordinate_direction"), list) and len(ray["coordinate_direction"]) == 344
                    and all(finite_number(checks.get(field)) and checks[field] < 1e-8 for field in
                            ("fixed_motion_residual_mm", "disk_direction_residual_mm", "inactive_direction_excess_mm"))
                    and finite_number(checks.get("objective_gain"), positive=True), "motion recession ray violates source laws")
        body_bounded = all(value is not None for interval in intervals[:300] for value in interval)
        all_bounded = all(value is not None for interval in intervals for value in interval)
        require(state.get("body_seating_bounded") is body_bounded and state.get("all_coordinate_seating_bounded") is all_bounded,
                "motion boundedness differs from actual coordinate dispositions")
        bounds = state.get("body_motion_bounds")
        require(isinstance(bounds, list) and len(bounds) == 50 and len({row.get("body") for row in bounds}) == 50
                and sum(row.get("kind") == "timber" for row in bounds) == 44
                and sum(row.get("kind") == "panel" for row in bounds) == 6
                and all(row.get("absolute_elastic_deformed_node_motion_recovered") is False for row in bounds),
                "motion body inventory or absolute elastic envelope claim differs")
        implication = state.get("stability_implications", {})
        witness = state.get("original_law_nonunique_body_witness")
        require(implication.get("fixed_force_local_reactions_changed") is False
                and implication.get("source_linear_elastic_field_unchanged_at_fixed_forces") is True
                and implication.get("second_order_buckling_or_dynamic_stability_established") is False
                and implication.get("admissible_body_flat_direction_demonstrated") is (witness is not None),
                "motion stability implication exceeds its fixed-force scope")
        if witness is not None:
            require(witness.get("force_field_changed") is False and len(witness.get("coordinate_increment", [])) == 344,
                    "motion witness changes forces or transfers historical coordinates")
            accepted_audit({"audit": witness.get("original_physical_law_audit")})
        bounded_bodies += body_bounded
        bounded_all += all_bounded
        witnesses += witness is not None
    require(result.get("counts") == {"required_states": 14, "accepted_states_assessed": len(accepted),
            "source_floor_stops_without_pose_field": 14 - len(accepted), "body_seating_bounded_states": bounded_bodies,
            "all_coordinate_bounded_states": bounded_all, "nonunique_body_witness_states": witnesses},
            "motion actual disposition census differs")
    coupon = read_json(bound_output(root, packet, receipt, "known-answer.json", cache))
    require(coupon.get("status") == "PASS_ANALYTIC_FIXED_FORCE_POSE_COUPONS"
            and coupon.get("disk_intervals") == [[-2.00000001, 2.00000001], [-2.00000001, 2.00000001], [None, None]]
            and coupon.get("open_unilateral_interval") == [None, 1e-8], "motion analytic known answer differs")


def splitting_identity(row):
    require(isinstance(row, dict), "invalid splitting row")
    path = row.get("path", {})
    require(isinstance(path, dict), "missing splitting path descriptor")
    path_id, axis, plane = row.get("path_id", path.get("id")), row.get("axis", path.get("axis")), row.get("plane_mm", path.get("plane_mm"))
    require(isinstance(row.get("body"), str) and row["body"] and isinstance(row.get("state_tag"), str)
            and isinstance(path_id, str) and path_id and type(axis) is int and axis in (1, 2)
            and finite_number(plane) and row.get("RT_binding") in {"R=u,T=v", "R=v,T=-u"}
            and finite_number(row.get("mesh_size_mm"), positive=True), "invalid splitting row identity")
    require(path.get("id") == path_id and path.get("axis") == axis and path.get("plane_mm") == plane,
            "splitting row/path identity mismatch")
    initial, final = path.get("initial_interval_mm"), path.get("final_interval_mm")
    require(all(isinstance(interval, list) and len(interval) == 2 and all(finite_number(v) for v in interval)
                and interval[0] < interval[1] for interval in (initial, final))
            and final[0] <= initial[0] and initial[1] <= final[1] and final != initial,
            "invalid splitting crack intervals")
    return row["body"], row["state_tag"], path_id, axis, plane, row["RT_binding"], row["mesh_size_mm"]


def splitting_scope_check(root, entry, result, sources, resolutions, cache):
    """Check declared finite obligations and saved arithmetic, without executing mechanics."""
    if entry.get("numerical_scope") != SPLITTING_SCOPE:
        return
    require(entry.get("status") == COMPLETE and result.get("schema") == SPLITTING_SCHEMA
            and result.get("splitting_workstream_complete") is True
            and result.get("full_splitting_qualification") is False
            and result.get("historical_force_basis_transferred") is False,
            "active splitting role is not a completed conditional finite workload")
    require(result.get("pending_feasible_comparison_count") == result.get("pending_feasible_solid_bodies") == 0
            and type(result.get("pending_feasible_comparison_count")) is int
            and type(result.get("pending_feasible_solid_bodies")) is int,
            "active splitting has queued or unperformed feasible work")
    documents, action_arrays = {}, {}

    def reference_path(reference, bindings, source_resolutions=None):
        require(isinstance(reference, dict), "missing splitting artifact reference")
        path = file_path(root, reference.get("path"))
        digest = reference.get("sha256")
        require(any(digest == value and file_path(root, name, absolute=True) == path for name, value in bindings.items()),
                "splitting artifact absent from declared bindings: " + str(path))
        return authenticate(root, reference["path"], digest, resolutions if source_resolutions is None else source_resolutions, cache)

    def document(reference, bindings, source_resolutions=None):
        path = reference_path(reference, bindings, source_resolutions)
        if path not in documents:
            documents[path] = read_json(path)
        return documents[path]

    def pointed(reference, bindings, source_resolutions=None):
        value = document(reference, bindings, source_resolutions)
        pointer = reference.get("pointer")
        require(isinstance(pointer, str) and pointer.startswith("/"), "invalid splitting source pointer")
        for token in pointer[1:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            value = value[int(token)] if isinstance(value, list) else value[token]
        require(isinstance(value, dict), "splitting source pointer lacks a record")
        return value

    action_binding = result.get("active_action_binding", {})
    action_reference = {"path": action_binding.get("receipt"), "sha256": action_binding.get("sha256")}
    action_receipt = document(action_reference, sources)
    action_packet = file_path(root, action_reference["path"]).parent
    action_summary = read_json(bound_output(root, action_packet, action_receipt, "summary.json", cache))
    require(action_summary.get("schema") == ACTION_SCHEMA, "splitting source is not reconciled coupled actions")
    inventory = state_map(action_summary.get("required_state_inventory"))
    require(set(inventory) == REQUIRED_STATES and canonical(result.get("required_state_inventory"))
            == canonical(action_summary["required_state_inventory"]), "splitting required-state inventory differs from active actions")
    accepted = {state_tag(key): item for key, item in inventory.items() if item.get("status") == ACCEPTED_STATE
                and item.get("accepted_force_field_exists") is True}
    stopped = [item for item in inventory.values() if item.get("status") == FLOOR_STOP
               and item.get("accepted_force_field_exists") is False]
    require(len(accepted) + len(stopped) == len(REQUIRED_STATES)
            and result.get("unavailable_state_count") == len(stopped)
            and result.get("unavailable_timber_state_slots") == len(stopped) * action_summary.get("timber_members", -1),
            "splitting unavailable states differ from active finite dispositions")
    actions_path = bound_output(root, action_packet, action_receipt, "body-actions.jsonl.gz", cache)
    actions_digest = fingerprint(actions_path, cache)[0]
    workload = document(result.get("workload_binding"), sources)
    prepared_binding = workload.get("prepared_binding", {})
    prepared_reference = {"path": prepared_binding.get("receipt"), "sha256": prepared_binding.get("sha256")}
    prepared_receipt = document(prepared_reference, sources)
    prepared_packet = file_path(root, prepared_reference["path"]).parent
    prepared_plan = read_json(bound_output(root, prepared_packet, prepared_receipt, "plan.json", cache))
    prepared_geometry = read_json(bound_output(root, prepared_packet, prepared_receipt, "geometry.json", cache))
    require(prepared_plan.get("source_action_receipt_sha256") == action_reference["sha256"]
            and canonical(prepared_plan.get("required_state_inventory")) == canonical(action_summary["required_state_inventory"]),
            "splitting canonical preparation uses a different active action basis")
    canonical_bodies = {body for duty in prepared_plan.get("duties", []) for body in duty.get("timber_sides", [])}
    require(len(canonical_bodies) == prepared_plan.get("current_timber_count") == action_summary.get("timber_members") == 44
            and set(prepared_geometry) == canonical_bodies, "splitting canonical 44-timber inventory differs")
    obligation_inventory = document(workload.get("obligation_inventory_binding"), sources)
    obligation_rows = obligation_inventory.get("records")
    require(isinstance(obligation_rows, list), "splitting workload lacks a canonical path inventory")
    obligation_bodies, all_obligations = set(), {}
    for body_record in obligation_rows:
        body = body_record.get("body")
        require(body in canonical_bodies and body not in obligation_bodies, "splitting obligation inventory omitted or repeated a timber")
        obligation_bodies.add(body)
        grids, bindings, paths = body_record.get("mesh_sizes_mm"), body_record.get("RT_bindings"), body_record.get("finite_paths")
        require(isinstance(grids, list) and len(grids) == 2 and set(grids) == {20, 15}
                and isinstance(bindings, list) and len(bindings) == 2 and set(bindings) == {"R=u,T=v", "R=v,T=-u"}
                and isinstance(paths, list) and paths, "splitting canonical path/grid/R-T obligations missing")
        for path in paths:
            for tag in accepted:
                for grid in grids:
                    for binding in bindings:
                        row = {"body": body, "state_tag": tag, "path": path, "mesh_size_mm": grid, "RT_binding": binding}
                        identity = splitting_identity(row)
                        require(identity not in all_obligations, "duplicate canonical splitting path obligation")
                        all_obligations[identity] = path
    require(obligation_bodies == canonical_bodies, "splitting obligation inventory omitted a canonical timber")
    required, excluded = {}, {}
    for field, target in (("required_rows", required), ("excluded_rows", excluded)):
        require(isinstance(workload.get(field), list), "splitting workload lacks exact " + field)
        for row in workload[field]:
            identity = splitting_identity(row)
            require(identity not in required and identity not in excluded and identity[1] in accepted,
                    "duplicate, overlapping or unavailable splitting workload identity")
            target[identity] = row
            if field == "excluded_rows":
                evidence = pointed(row.get("method_limit"), sources)
                require(evidence.get("status") == "EXCLUDED_METHOD_LIMIT" and splitting_identity(evidence) == identity
                        and canonical(evidence.get("path")) == canonical(row["path"]),
                        "splitting exclusion lacks exact source-bound method disposition")
    assessed_obligations = {**required, **excluded}
    require(assessed_obligations.keys() == all_obligations.keys()
            and all(canonical(row["path"]) == canonical(all_obligations[identity]) for identity, row in assessed_obligations.items()),
            "splitting workload omitted or changed a canonical body/path/grid/R-T/state obligation")
    require(required, "active splitting workload has no finite comparisons")
    body_entries = result.get("bodies")
    require(isinstance(body_entries, list), "active splitting lacks per-body result/receipt bindings")
    body_names, completed = set(), {}
    expected_bodies = {identity[0] for identity in required}
    for body_entry in body_entries:
        require(isinstance(body_entry, dict) and body_entry.get("body") in expected_bodies
                and body_entry["body"] not in body_names, "duplicate or unrequired splitting body packet")
        body = body_entry["body"]
        body_names.add(body)
        body_receipt = document(body_entry.get("receipt"), sources)
        body_packet = file_path(root, body_entry["receipt"]["path"]).parent
        output_bindings = body_receipt.get("output_sha256")
        require(isinstance(output_bindings, dict) and output_bindings, "missing splitting body output bindings")
        body_outputs = {output_path(root, body_packet, name).relative_to(root).as_posix(): digest
                        for name, digest in output_bindings.items()}
        for name, digest in body_outputs.items():
            authenticate(root, name, digest, {}, cache)
        body_result = document(body_entry.get("result"), sources)
        reference_path(body_entry["result"], body_outputs)
        body_status = body_result.get("status")
        require(isinstance(body_status, str) and body_receipt.get("status") == body_status
                and not re.search(r"PREPAR|(?:^|_)STOPS?(?:_|$)|INCOMPLETE|PENDING|NOT_NUMERIC", body_status.upper())
                and isinstance(body_result.get("records"), list),
                "splitting body result/receipt status or records mismatch")
        body_sources = body_receipt.get("source_sha256", {})
        require(isinstance(body_sources, dict) and body_sources, "invalid splitting body source bindings")
        body_resolutions = dict(resolutions)
        for body_document in (body_receipt, body_entry):
            local_resolutions = body_document.get("source_resolution", {})
            require(isinstance(local_resolutions, dict), "invalid splitting body source resolutions")
            body_resolutions.update(local_resolutions)
        if "preserved_producer_snapshot" in body_entry:
            snapshot = body_entry["preserved_producer_snapshot"]
            snapshot_hash = body_entry.get("preserved_producer_sha256")
            reference_path({"path": snapshot, "sha256": snapshot_hash}, body_outputs, {})
            for name, digest in body_sources.items():
                if digest == snapshot_hash and name not in body_resolutions:
                    body_resolutions[name] = {"original_path": name, "sha256": digest, "snapshot_path": snapshot}
        for name, digest in body_sources.items():
            authenticate(root, name, digest, body_resolutions, cache)
        for field in ("source_before_sha256", "source_after_sha256"):
            if field in body_receipt:
                require(body_receipt[field] == body_sources, "splitting body receipt source-set mismatch")
        row_bindings = {**sources, **body_sources}
        hypotheses_reference = body_result.get("reference_hypotheses")
        hypotheses = pointed(hypotheses_reference, {**row_bindings, **body_outputs}, body_resolutions)
        require(file_path(root, hypotheses_reference["path"]) == prepared_packet / "plan.json"
                and hypotheses_reference.get("pointer") == "/assumptions"
                and hypotheses_reference.get("sha256") == fingerprint(prepared_packet / "plan.json", cache)[0],
                "splitting references are not the receipt-bound prepared hypotheses")
        for row in body_result["records"]:
            identity = splitting_identity(row)
            tag = identity[1]
            require(identity in required and identity not in completed and identity[0] == body
                    and row.get("case_id") == tag and canonical(row["path"]) == canonical(required[identity]["path"]),
                    "missing, repeated or mismatched finite splitting row")
            require(canonical(row.get("source_state_record")) == canonical(accepted[tag].get("source_state_record")),
                    "splitting row uses a different active source state")
            source_state = pointed(row["source_state_record"], row_bindings, body_resolutions)
            require(state_tag(state_key(source_state)) == tag, "splitting pointer identifies a different source state")
            accepted_audit(source_state)
            reference = row.get("source_action_record", {})
            require(file_path(root, reference.get("path")) == actions_path and reference.get("sha256") == actions_digest
                    and re.fullmatch(r"/[0-9]+/actions", reference.get("pointer", "")),
                    "splitting action dictionary is not from the active receipt-bound export")
            reference_path(reference, row_bindings, body_resolutions)
            if actions_path not in action_arrays:
                with gzip.open(actions_path, "rt", encoding="utf-8") as stream:
                    action_arrays[actions_path] = [json.loads(line) for line in stream]
            source_action = action_arrays[actions_path][int(reference["pointer"].split("/")[1])]
            action_hash = hashlib.sha256(canonical(source_action["actions"]).encode("utf-8")).hexdigest()
            require(source_action.get("body") == body and source_action.get("state_tag") == tag
                    and state_tag(state_key(source_action)) == tag
                    and canonical(source_action.get("source_state_record")) == canonical(row["source_state_record"])
                    and row.get("source_action_dictionary_sha256") == action_hash,
                    "splitting row action identity or full dictionary hash mismatch")
            energies, areas, source_keys, intact_stress = [], [], None, None
            for checkpoint_name in ("intact_checkpoint", "initial_checkpoint", "final_checkpoint"):
                checkpoint = document(row.get(checkpoint_name), body_outputs)
                retained_field = checkpoint.get("retained_field")
                retained_path = reference_path(retained_field, body_outputs, {})
                require(retained_path.suffix == ".npz", "splitting checkpoint lacks its retained NPZ field")
                checks = checkpoint.get("checks", {})
                require(checkpoint.get("all_passed") is True and isinstance(checks, dict) and checks
                        and all(value is True for value in checks.values())
                        and isinstance(checkpoint.get("source_state_keys"), list)
                        and sum(isinstance(key, list) and len(key) == 2 and key[1] == tag
                                for key in checkpoint["source_state_keys"]) == 1,
                        "splitting checkpoint lacks the audited same-state field")
                if source_keys is None:
                    source_keys = checkpoint["source_state_keys"]
                require(checkpoint["source_state_keys"] == source_keys,
                        "splitting checkpoints use different source state/basis inventories")
                load_hash = row.get("physical_nodal_load_sha256")
                require(isinstance(load_hash, str) and re.fullmatch(r"[0-9a-f]{64}", load_hash)
                        and checkpoint.get("per_state_physical_nodal_load_sha256", {}).get(tag) == load_hash,
                        "splitting checkpoint changed the same-state physical load")
                energies.append(checkpoint.get("strain_energy_nmm_by_state_tag", {}).get(tag))
                areas.append(checkpoint.get("mesh", {}).get("crack_area_mm2"))
                if checkpoint_name == "intact_checkpoint":
                    intact_stress = checkpoint.get("sampled_sigma90_mpa_by_state_tag", {}).get(tag)
            require(all(finite_number(value) for value in energies)
                    and row.get("intact_initial_final_energies_nmm") == energies
                    and finite_number(row.get("added_sound_area_mm2"), positive=True)
                    and finite_number(row.get("Ft90_mpa"), positive=True)
                    and finite_number(row.get("Gc_n_per_mm"), positive=True)
                    and finite_number(row.get("intact_sampled_sigma90_mpa")),
                    "splitting row lacks finite same-state energy/area/reference arithmetic")
            require(all(finite_number(value) and value >= 0 for value in areas)
                    and math.isclose(row["added_sound_area_mm2"], areas[2] - areas[1], rel_tol=1e-9, abs_tol=1e-12)
                    and finite_number(intact_stress) and row["intact_sampled_sigma90_mpa"] == intact_stress,
                    "splitting row area or stress differs from saved mesh/intact state")
            require(row["Ft90_mpa"] == hypotheses.get("Ft90_mpa")
                    and row["Gc_n_per_mm"] == hypotheses.get("Gc_all_modes_n_per_mm")
                    and ("reference_hypotheses" not in row or canonical(row["reference_hypotheses"]) == canonical(hypotheses_reference)),
                    "splitting row thresholds differ from receipt-bound conditional hypotheses")
            increment = (energies[2] - energies[1]) / row["added_sound_area_mm2"]
            upper = (energies[2] - energies[0]) / row["added_sound_area_mm2"]
            require(increment >= -1e-8 and upper - increment >= -1e-8,
                    "splitting row violates the saved energy ordering allowance")
            expected_indices = {"initiation_index": row["intact_sampled_sigma90_mpa"] / row["Ft90_mpa"],
                                "fracture_index": max(increment, 0.) / row["Gc_n_per_mm"],
                                "contact_upper_reference_index": max(upper, 0.) / row["Gc_n_per_mm"]}
            require(all(finite_number(row.get(name)) and math.isclose(row[name], expected, rel_tol=1e-9, abs_tol=1e-12)
                        for name, expected in expected_indices.items()), "splitting row indices do not recover saved arithmetic")
            completed[identity] = row
    require(body_names == expected_bodies and completed.keys() == required.keys()
            and type(result.get("active_solid_comparison_count")) is int
            and result["active_solid_comparison_count"] == len(required),
            "active splitting finite workload has missing or unperformed feasible rows")


def packet_check(root, key, entry, maintained, cache):
    require(isinstance(entry, dict), "packet object required: " + key)
    paths = {}
    for field, hash_field in (("result", "result_sha256"), ("receipt", "receipt_sha256"),
                              ("preserved_producer_snapshot", "preserved_producer_sha256")):
        file_path(root, entry.get(field))  # Packet artifacts must be repository-relative.
        paths[field] = authenticate(root, entry[field], entry.get(hash_field), {}, cache)
    result, receipt = read_json(paths["result"]), read_json(paths["receipt"])
    member_field_scope(entry, result)
    require(isinstance(entry.get("result_status"), str)
            and result.get("status") == entry["result_status"], "result status mismatch: " + key)
    if "status" in receipt or "receipt_status" in entry:
        require(receipt.get("status") == entry.get("receipt_status", entry["result_status"]),
                "receipt status mismatch: " + key)
    for field in ("counts", "same_state_peaks"):
        if field in entry:
            require(field in result and canonical(entry[field]) == canonical(result[field]),
                    field + " mismatch: " + key)
            if field in receipt:
                require(canonical(entry[field]) == canonical(receipt[field]),
                        "receipt " + field + " mismatch: " + key)
    if entry.get("status") == COMPLETE:
        status = entry["result_status"].upper()
        require(not re.search(r"PREPAR|\bSTOPS?\b|(?:^|_)STOPS?(?:_|$)|INCOMPLETE|NOT_NUMERIC", status),
                "preparation or numerical stop falsely completed: " + key)
        counts = result.get("counts", {})
        require(isinstance(counts, dict), "invalid counts: " + key)
        for field, value in counts.items():
            if re.search(r"numerical_stop|stopped_state|unassessed|unfinished|unperformed|pending|^null_(shaft|washer_end)_states$", field):
                require(value == 0 and type(value) is int, "unfinished numerical count: " + key + "/" + field)
    for document in (entry, result, receipt):
        for flag in ("complete_joint_acceptance", "physical_release", "fabrication_release",
                     "actual_product_or_complete_joint_acceptance"):
            require(document.get(flag, False) is False, "release or acceptance inferred: " + key + "/" + flag)

    outputs = receipt.get("output_sha256")
    require(isinstance(outputs, dict) and outputs, "missing receipt output bindings: " + key)
    matched = set()
    receipt_relative = paths["receipt"].parent.relative_to(root).as_posix() + "/"
    for name, expected in outputs.items():
        require(isinstance(name, str), "invalid output name: " + key)
        relative = name if name.startswith(receipt_relative) else receipt_relative + name
        output = authenticate(root, relative, expected, {}, cache)
        for field in ("result", "preserved_producer_snapshot"):
            if output == paths[field]:
                matched.add(field)
    require(matched == {"result", "preserved_producer_snapshot"},
            "result or snapshot absent from receipt outputs: " + key)

    resolutions = dict(maintained)
    for document in (receipt, entry):
        local = document.get("source_resolution", {})
        require(isinstance(local, dict), "invalid packet source_resolution: " + key)
        resolutions.update(local)
    sources = receipt.get("source_sha256")
    require(isinstance(sources, dict) and sources, "missing receipt source bindings: " + key)
    for name, expected in sources.items():
        # The explicitly declared producer snapshot also preserves its original source pin.
        if expected == entry["preserved_producer_sha256"] and name not in resolutions:
            resolutions[name] = {"original_path": name, "sha256": expected,
                                 "snapshot_path": entry["preserved_producer_snapshot"]}
        authenticate(root, name, expected, resolutions, cache)
    for field in ("source_before_sha256", "source_after_sha256"):
        if field in receipt:
            require(receipt[field] == sources, "receipt source-set mismatch: " + key + "/" + field)
    splitting_scope_check(root, entry, result, sources, resolutions, cache)
    motion_scope_check(root, entry, result, paths["receipt"].parent, receipt, sources, resolutions, cache)
    representative_scope_check(root, entry, result, paths["receipt"].parent, receipt, sources, resolutions, cache)
    washer_scope_check(root, entry, result, paths["receipt"].parent, receipt, sources, resolutions, cache)
    shaft_scope_check(root, entry, result, paths["receipt"].parent, receipt, sources, resolutions, cache)
    if entry.get("status") == FINITE_DISPOSITION and result.get("schema") != WASHER_SCHEMA and entry.get("numerical_scope") != SHAFT_SCOPE \
            or result.get("schema") in {FRAME_SCHEMA, ACTION_SCHEMA} and entry.get("status") == COMPLETE:
        inventory, accepted = finite_disposition_check(root, result, paths["receipt"].parent, receipt,
                                                     sources, resolutions, cache)
        require(entry.get("status") != COMPLETE or set(accepted) == REQUIRED_STATES,
                "finite stopped dispositions falsely classified as completed actual comparisons: " + key)
        if "counts" in entry and result.get("schema") == FRAME_SCHEMA:
            require(entry["counts"].get("assessed_states", len(inventory)) == len(inventory), "frame assessed count mismatch")
    return len(sources), len(outputs)


def coupled_basis_check(root, extension, results, mapping):
    """Select current coupled inputs without deleting distinct historical results."""
    basis = extension.get("selected_coupled_force_basis")
    if basis is None:
        require(extension.get("status") != "complete" or
                "compatible action reconciliation" not in extension.get("workstreams", []),
                "complete coupled workstream lacks a selected force basis")
        return 0
    require(isinstance(basis, dict), "invalid selected coupled force basis")
    frame_key, action_key = basis.get("frame_result"), basis.get("action_result")
    consumers = basis.get("consumer_results")
    require(isinstance(frame_key, str) and frame_key in results and isinstance(action_key, str)
            and action_key in results and frame_key != action_key and isinstance(consumers, list)
            and all(isinstance(key, str) and key in results for key in consumers)
            and len(set(consumers)) == len(consumers) and not {frame_key, action_key} & set(consumers),
            "unknown or repeated coupled basis result")
    mapped = {key for names in mapping.values() for key in names}
    require({frame_key, action_key, *consumers} <= mapped, "selected coupled results are absent from workstream maps")
    frame_entry, action_entry = results[frame_key], results[action_key]
    frame = read_json(file_path(root, frame_entry["result"]))
    action = read_json(file_path(root, action_entry["result"]))
    require(frame.get("schema") == FRAME_SCHEMA and action.get("schema") == ACTION_SCHEMA
            and frame_entry.get("status") == action_entry.get("status") == FINITE_DISPOSITION,
            "selected coupled basis is not the authenticated frame/action pair")

    def directly_bound(receipt, name, expected):
        path = file_path(root, name)
        return any(digest == expected and file_path(root, source, absolute=True) == path
                   for source, digest in receipt["source_sha256"].items())

    action_receipt = read_json(file_path(root, action_entry["receipt"]))
    require(directly_bound(action_receipt, frame_entry["receipt"], frame_entry["receipt_sha256"])
            and directly_bound(action_receipt, frame_entry["result"], frame_entry["result_sha256"])
            and all(item["source_disposition_record"]["path"] == frame_entry["result"]
                    and item["source_disposition_record"]["sha256"] == frame_entry["result_sha256"]
                    for item in action["required_state_inventory"]), "selected action uses a different frame basis")
    for key in consumers:
        entry = results[key]
        receipt = read_json(file_path(root, entry["receipt"]))
        result = read_json(file_path(root, entry["result"]))
        require(directly_bound(receipt, action_entry["receipt"], action_entry["receipt_sha256"]),
                "selected consumer uses a stale or unbound action receipt: " + key)
        if "action_receipt_sha256" in result:
            require(result["action_receipt_sha256"] == action_entry["receipt_sha256"], "consumer action digest differs: " + key)
        if "required_state_inventory" in result:
            require(canonical(result["required_state_inventory"]) == canonical(action["required_state_inventory"]),
                    "consumer required-state inventory differs from selected action: " + key)
        if entry.get("numerical_scope") in {SPLITTING_SCOPE, REPRESENTATIVE_SCOPE}:
            require(result.get("active_action_binding") == {"receipt": action_entry["receipt"], "sha256": action_entry["receipt_sha256"]},
                    "active splitting workload uses a different selected action receipt")
    require(extension.get("status") != "complete" or consumers, "complete coupled basis has no selected reference consumers")
    return len(consumers)


def check(index=INDEX, root=ROOT):
    """Check repository or fixture artifacts; return counts, never write files."""
    root = Path(root).resolve()
    index = Path(index)
    document = read_json(index if index.is_absolute() else root / index)
    extension = document.get("numerical_acceptance_extension")
    require(isinstance(extension, dict), "missing numerical acceptance extension")
    binding = extension.get("previous_index_binding", {})
    require(isinstance(binding, dict) and re.fullmatch(r"[0-9a-f]{40}", binding.get("git_commit", "")),
            "invalid previous index commit")
    file_path(root, binding.get("path"))
    previous_bytes = subprocess.run(["git", "-C", str(root), "show",
        binding["git_commit"] + ":" + binding["path"]], check=True, capture_output=True).stdout
    require(hashlib.sha256(previous_bytes).hexdigest() == binding.get("sha256"),
            "previous index SHA256 mismatch")
    previous = json.loads(previous_bytes)
    require(isinstance(previous, dict), "previous index must be an object")
    pins = document.get("source_pins", {})
    require(isinstance(pins, dict) and len(pins) == document.get("source_count") == 217
            and pins == previous.get("source_pins"), "original 217 source pins changed")
    pin_set = {path: value["sha256"] for path, value in pins.items()}
    require(hashlib.sha256(canonical(pin_set).encode()).hexdigest() == document.get("source_pin_set_sha256"),
            "source pin-set SHA256 mismatch")
    maintained = document.get("maintained_source_resolution", {})
    require(isinstance(maintained, dict) and set(maintained) <= set(pins), "invalid maintained source resolutions")
    for source, resolution in maintained.items():
        require(isinstance(resolution, dict) and resolution.get("sha256") == pins[source].get("sha256"),
                "maintained redirect changed original source hash: " + source)
    cache = {}
    for source, pin in pins.items():
        require(isinstance(pin, dict), "invalid original source pin: " + source)
        authenticate(root, source, pin.get("sha256"), maintained, cache, size=pin.get("size_bytes"))

    def obligations(value):
        rows = value.get("obligations", [])
        require(isinstance(rows, list) and len(rows) == 47, "original 47 obligations missing")
        mapping = {row["id"]: row for row in rows}
        require(len(mapping) == 47, "duplicate obligation IDs")
        return mapping
    before, after = obligations(previous), obligations(document)
    require(before.keys() == after.keys(), "original obligation IDs changed")
    for key, row in after.items():
        require(row.get("frozen_definition") == before[key].get("frozen_definition")
                and row.get("formal_status") == before[key].get("formal_status") == "pending"
                and row.get("parent_formal_acceptance") is False,
                "original definition or pending status changed: " + key)
    authority = document.get("authority", {})
    flags = authority.get("release_flags", {})
    require(set(flags) == RELEASE_FLAGS and all(value is False for value in flags.values())
            and flags == previous.get("authority", {}).get("release_flags"), "eight false release flags changed")
    require(authority.get("formal_criteria_count") == authority.get("formal_pending_count") == 47,
            "formal criterion count changed")
    require(document.get("complete_joint_acceptance") is False
            and extension.get("formal_statuses_changed") is False
            and extension.get("physical_or_structural_release_inferred") is False
            and extension.get("prior_assessment_scope_preserved") is True, "extension claim boundary changed")

    results = extension.get("results", {})
    require(isinstance(results, dict), "invalid extension result packets")
    source_count, output_count = 0, 0
    for key, entry in results.items():
        sources, outputs = packet_check(root, key, entry, maintained, cache)
        source_count += sources; output_count += outputs
    workstreams = extension.get("workstreams", [])
    mapping = extension.get("workstream_results", {})
    require(isinstance(workstreams, list) and workstreams and all(isinstance(x, str) and x for x in workstreams)
            and len(set(workstreams)) == len(workstreams) and isinstance(mapping, dict)
            and set(mapping) <= set(workstreams), "invalid workstream mapping")
    pending = []
    for workstream in workstreams:
        names = mapping.get(workstream, [])
        require(isinstance(names, list) and all(isinstance(name, str) and name in results for name in names),
                "unknown workstream result: " + workstream)
        selected_consumers = extension.get("selected_coupled_force_basis", {}).get("consumer_results", [])
        active_splitting = any(name in selected_consumers and (
            results[name].get("numerical_scope") == SPLITTING_SCOPE or
            results[name].get("numerical_scope") == REPRESENTATIVE_SCOPE
            and read_json(file_path(root, results[name]["result"])).get("splitting_workstream_complete") is True)
            for name in names)
        if not names or any(results[name].get("status") not in {COMPLETE, FINITE_DISPOSITION, REPRESENTATIVE_COMPLETE} for name in names) \
                or workstream == SPLITTING_WORKSTREAM and not active_splitting:
            pending.append(workstream)
    status = extension.get("status")
    require(status in {"in_progress", "complete"}, "invalid extension completion status")
    coherent_consumers = coupled_basis_check(root, extension, results, mapping)
    if status == "complete":
        validation = extension.get("parent_final_validation", {})
        require(isinstance(validation, dict) and validation.get("confirmed") is True and not pending,
                "complete extension lacks parent confirmation or completed workstreams")
    return {"status": status, "original_sources": len(pins), "original_criteria": len(after),
            "false_release_flags": len(flags), "result_packets": len(results),
            "complete_comparison_packets": sum(entry.get("status") == COMPLETE for entry in results.values()),
            "finite_disposition_packets": sum(entry.get("status") == FINITE_DISPOSITION for entry in results.values()),
            "representative_study_packets": sum(entry.get("status") == REPRESENTATIVE_COMPLETE for entry in results.values()),
            "selected_coupled_consumers": coherent_consumers,
            "packet_source_bindings": source_count, "packet_output_bindings": output_count,
            "pending_workstreams": len(pending)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="read-only check (default)")
    parser.add_argument("--index", type=Path, default=INDEX)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository or fixture root")
    args = parser.parse_args()
    try:
        print("OK " + canonical(check(args.index, args.root)))
    except (ValueError, OSError, KeyError, IndexError, TypeError, SyntaxError, struct.error,
            zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        print("FAIL " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
