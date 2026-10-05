"""A coherent receipt cannot promote prepared arithmetic or hide mutated bytes."""

import gzip
import hashlib
import json
import math
import struct
import subprocess
import zipfile
from copy import deepcopy

import pytest

from scripts import check_wood_joint_numerical_acceptance as acceptance
from scripts.check_wood_joint_numerical_acceptance import (
    ACCEPTED_STATE,
    ACTION_SCHEMA,
    CASES,
    COMPLETE,
    FINITE_DISPOSITION,
    FLOOR_PREFIX,
    FLOOR_STOP,
    FRAME_PARTIAL,
    FRAME_SCHEMA,
    MEMBER_SCHEMA,
    MOTION_SCHEMA,
    MOTION_SCOPE,
    MOTION_STATUS,
    RELEASE_FLAGS,
    REPRESENTATIVE_COMPLETE,
    REPRESENTATIVE_SCHEMA,
    REPRESENTATIVE_SCOPE,
    REPRESENTATIVE_STATUS,
    SPLITTING_SCHEMA,
    SPLITTING_SCOPE,
    assembled_energy_check,
    canonical,
    check,
    representative_scope_check,
    splitting_scope_check,
)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extension_fixture(tmp_path):
    pins = {}
    for number in range(217):
        name = f"sources/{number}.txt"
        path = tmp_path / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(str(number))
        pins[name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "size_bytes": path.stat().st_size}
    index = {
        "source_count": 217, "source_pins": pins,
        "source_pin_set_sha256": hashlib.sha256(json.dumps(
            {p: v["sha256"] for p,v in pins.items()}, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "authority": {"formal_criteria_count":47, "formal_pending_count":47,
                      "release_flags":{name:False for name in RELEASE_FLAGS}},
        "obligations": [{"id":str(n), "frozen_definition":{"status":"pending", "note":str(n)},
                         "formal_status":"pending", "parent_formal_acceptance":False} for n in range(47)],
        "complete_joint_acceptance":False,
    }
    previous_sha = write_json(tmp_path / "index.json", index)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "index.json"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=Evidence Fixture",
                    "-c", "user.email=evidence@example.test", "commit", "-qm", "Frozen index", "--no-gpg-sign"], check=True)
    commit = subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
                            check=True, capture_output=True, text=True).stdout.strip()
    # Maintained prose changes while its original bytes remain explicitly bound.
    (tmp_path / "original.txt.snapshot").write_bytes((tmp_path / "sources/0.txt").read_bytes())
    (tmp_path / "sources/0.txt").write_text("maintained current prose")
    index["maintained_source_resolution"] = {"sources/0.txt": {
        "original_path":"sources/0.txt", "snapshot_path":"original.txt.snapshot", "sha256":pins["sources/0.txt"]["sha256"]}}
    packet = tmp_path / "packet"
    packet.mkdir()
    snapshot = packet / "producer.py.snapshot"
    snapshot.write_text("frozen producer bytes")
    snapshot_sha = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    (tmp_path / "producer.py").write_text("later producer bytes")
    result = {"status":"COMPLETE_CONDITIONAL_COMPARISON", "counts":{"completed_states":1,"numerical_stops":0},
              "complete_joint_acceptance":False, "physical_release":False}
    result_sha = write_json(packet / "result.json", result)
    receipt = {"status":result["status"], "counts":result["counts"],
        "source_sha256":{"sources/0.txt":pins["sources/0.txt"]["sha256"], "producer.py":snapshot_sha,
                          str(tmp_path / "sources/1.txt"):pins["sources/1.txt"]["sha256"]},
        "output_sha256":{"result.json":result_sha,"producer.py.snapshot":snapshot_sha}}
    entry = {"status":COMPLETE, "result_status":result["status"], "counts":result["counts"],
        "result":"packet/result.json", "result_sha256":result_sha,
        "receipt":"packet/receipt.json", "receipt_sha256":write_json(packet / "receipt.json", receipt),
        "preserved_producer_snapshot":"packet/producer.py.snapshot", "preserved_producer_sha256":snapshot_sha}
    extension = {"status":"in_progress", "prior_assessment_scope_preserved":True,
        "formal_statuses_changed":False, "physical_or_structural_release_inferred":False,
        "previous_index_binding":{"path":"index.json", "git_commit":commit, "sha256":previous_sha},
        "workstreams":["study"], "workstream_results":{"study":["study"]}, "results":{"study":entry}}
    index["numerical_acceptance_extension"] = extension
    write_json(tmp_path / "index.json", index)
    return index, extension, entry, result, receipt


def write_arrays(path, arrays):
    """Write tiny real numeric arrays without importing or executing mechanics."""
    with zipfile.ZipFile(path, "w") as archive:
        for name, shape in arrays.items():
            header = repr({"descr": "<f8", "fortran_order": False, "shape": shape}).encode()
            header += b" " * ((-10 - len(header) - 1) % 64) + b"\n"
            archive.writestr(zipfile.ZipInfo(name + ".npy", date_time=(2000, 1, 1, 0, 0, 0)),
                             b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header))
                             + header + b"\0" * (math.prod(shape) * 8))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def projected_method_fixture():
    """A three-phase correction with actual physical effects and six oracle rows."""
    method = acceptance.PROJECTED_OPERATOR_METHOD
    variants = {phase: {"id": phase, "phase": phase, "grid_mm": 20} for phase in ("intact", "initial", "final")}
    proof_ref, known_ref, raw_ref = [{"path": name, "sha256": "a"*64} for name in
                                   ("proof/result.json", "known/audit.json", "raw/receipt.json")]
    effects = {"all_passed": True, "checks": {"original_force_work": True},
        "actual_exported_full_K_force_residual_n": 1e-10, "projection_port_force_effect_peak_n": 1e-10,
        "projection_diagonal_work_effect_relative": 1e-12, "full_rhs_work_reciprocity_relative": 1e-12,
        "full_H_e_L_cross_work_relative_errors": dict.fromkeys(("H", "e", "L"), 1e-12),
        "full_H_e_L_change_relative_errors": dict.fromkeys(("H", "e", "L"), 1e-12)}
    recoveries = [{"variant": variant, "all_passed": True, "checks": {"original_field": True},
        "original_rigid_audit": {"status": "PASS_ELASTIC_QUOTIENT_SCREEN", "rigid_leakage_rel_limit": 5e-14,
                                  "relative_KR_inf": 1e-15},
        "relative_energy_identity_error": 1e-12, "projection_effects": deepcopy(effects)} for variant in variants.values()]
    certificate = {"method_id": method, "all_passed": True, "checks": dict.fromkeys((
        "six_physical_rigid_columns_full_rank", "QR_orthogonality", "correction_formula_roundoff_bound",
        "union_elastic_quotient_defect_within_measured_orthogonality_and_roundoff"), True),
        "full_native_stiffness_projected": False, "source_rhs_projected_again": False,
        "per_variant_elastic_quotient_preservation_assumed": False, "orthogonality_error_fro": 1e-15,
        "correction_formula_error_fro_n_per_mm": 1e-10, "union_elastic_quotient_defect_fro_n_per_mm": 1e-10,
        "measured_orthogonality_bound_n_per_mm": 1e-9, "matrix_product_roundoff_bound_n_per_mm": 1e-9}
    proof = {"schema": "splitting_factor_free_schur_precision_diagnostic/v1",
        "status": "PASS_FACTOR_FREE_PROJECTED_ELASTIC_QUOTIENT_AND_ORIGINAL_FIELD_GATES",
        "raw_rejection_preserved": True, "accepted_body_operator_published": False, "original_packet": raw_ref,
        "records": [{"all_passed": True, "checks": {"original_field": True}, "numerical_method_id": method,
                     "RHS_projection_added": False, "quotient_projection": certificate, "native_rhs_recovery": recoveries}]}
    known = {"schema": "splitting_schur_precision_saved_known_answer_audit/v1",
        "status": "PASS_SAVED_MONOLITHIC_FIELDS_AND_FULL_H_e_L_CROSS_WORK",
        "new_matrix_assembly_or_factorization": False, "project_body_acceptance_transferred": False,
        "records": [{"RT_binding": rt, "configuration": phase, "all_passed": True,
            "relative_H_e_L_work_errors": dict.fromkeys(("H", "e", "L"), 1e-12), "relative_U_error": 1e-12,
            "relative_full_rhs_work_reciprocity": 1e-12}
            for rt in ("R=u,T=v", "R=v,T=-u") for phase in variants]}
    operators = [{"variant": recovery["variant"], "physical_audit": {"all_passed": True,
        "checks": {"original_field": True}, **{name: {"all_passed": True, "checks": {"original_field": True},
            "precision_recovery_binding": proof_ref, "projection_effects": deepcopy(recovery["projection_effects"])}
            for name in ("operator", "solution")}}, "assembly_method": {"numerical_method_id": method,
        "precision_recovery_binding": proof_ref, "saved_monolithic_cross_work_proof": known_ref,
        "original_factor_packet": raw_ref}} for recovery in recoveries]
    group = {"schema": "splitting_coupled_body_operator_group/v1", "status": "PASS_ACTUAL_COUPLED_BODY_OPERATOR_GROUP",
        "native_operator_count": 3, "operators": operators, "numerical_method_id": method, "raw_rejection_preserved": True,
        "precision_recovery_binding": proof_ref, "saved_monolithic_cross_work_proof": known_ref,
        "raw_factor_rejection_binding": raw_ref}
    raw = {"status": "STOP_NATIVE_OPERATOR_GATE", "output_sha256": {"stop.json": "a"*64}}
    stop = {"exception": "RuntimeError", "message": "Localized rigid operator audit failed"}
    documents = {proof_ref["path"]: proof, known_ref["path"]: known, "raw/stop.json": stop}
    return group, variants, proof, known, raw, stop, lambda: acceptance.projected_operator_method_check(
        group, variants, lambda ref: documents[ref["path"]], lambda _ref: raw)


@pytest.mark.parametrize("fault", [None, "missing_pin", "different_digest", "arbitrary_redirect"])
def test_projected_legacy_snapshot_audit_does_not_redirect_live_sources(tmp_path, fault):
    row = {"resolution": "DECLARED_EXACT_PRODUCER_SNAPSHOT", "source_key": "producer.py",
           "resolved_path": "retained/producer.py.snapshot", "expected_sha256": "a"*64}
    receipt = {"source_resolution": [row], "source_sha256": {row["resolved_path"]: row["expected_sha256"]}}
    assert acceptance.projected_receipt_resolutions(tmp_path, receipt, {}) == {}
    if fault is None:
        return
    if fault == "missing_pin":
        receipt["source_sha256"] = {}
    elif fault == "different_digest":
        row["expected_sha256"] = "b"*64
    else:
        row["resolution"] = "USE_LIVE_REPLACEMENT"
    with pytest.raises(ValueError):
        acceptance.projected_receipt_resolutions(tmp_path, receipt, {})


@pytest.mark.parametrize("fault", [None, "raw_pass", "ordinary_stop", "method", "source_rhs", "rigid_gate",
    "force_budget", "work_budget", "cross_terms", "known_inventory", "known_work", "stale_binding", "phase"])
def test_projected_operator_retains_original_field_and_cross_work_gates(fault):
    group, _variants, proof, known, raw, stop, validate = projected_method_fixture()
    validate()
    report = proof["records"][0]
    if fault is None:
        return
    if fault == "raw_pass":
        raw["status"] = "PASS_ACTUAL_COUPLED_BODY_OPERATOR_GROUP"
        raw.pop("output_sha256")
        validate()
        return
    if fault == "ordinary_stop":
        stop["message"] = "Memory cap exceeded"
    elif fault == "method":
        group["numerical_method_id"] = "unproved_projection"
    elif fault == "source_rhs":
        report["RHS_projection_added"] = True
    elif fault == "rigid_gate":
        report["native_rhs_recovery"][0]["original_rigid_audit"]["relative_KR_inf"] = 6e-14
    elif fault == "force_budget":
        report["native_rhs_recovery"][0]["projection_effects"]["projection_port_force_effect_peak_n"] = 1e-5
    elif fault == "work_budget":
        report["native_rhs_recovery"][0]["relative_energy_identity_error"] = 1e-8
    elif fault == "cross_terms":
        report["native_rhs_recovery"][0]["projection_effects"]["full_H_e_L_cross_work_relative_errors"].pop("e")
    elif fault == "known_inventory":
        known["records"][0]["RT_binding"] = "unproved"
    elif fault == "known_work":
        known["records"][0]["relative_H_e_L_work_errors"]["L"] = 1e-8
    elif fault == "stale_binding":
        group["operators"][0]["assembly_method"]["precision_recovery_binding"] = {"path": "stale"}
    elif fault == "phase":
        report["native_rhs_recovery"][0]["variant"] = {"id": "intact", "grid_mm": 15}
    with pytest.raises(ValueError):
        validate()


def shaft_fixture(tmp_path, monkeypatch):
    """Real authenticated JSONL outputs, 12 current states and four null-source axes."""
    sources = {}

    def save(name, value):
        sources[name] = write_json(tmp_path/name, value)
        return sources[name]

    keys = [(case, gap) for case in CASES for gap in (0, 1)]
    accepted_keys = [key for key in keys if key not in {("a12-left", 0), ("k12-right", 0)}]
    comparison = {"analytical_branch": "working_washer_profile_with_explicit_member_replacements"}
    save("frame/comparison.json", comparison)
    for name in ("receipt.json", "response.npz", "joint-update.json"):
        save("frame/"+name, {"frozen": name})
    states = [{"case_id": case, "gap_scale": gap, "state_tag": acceptance.state_tag((case, gap)),
        "source_state_record": {"path": "frame/comparison.json", "sha256": sources["frame/comparison.json"],
                                "pointer": f"/states/{i}"}} for i, (case, gap) in enumerate(accepted_keys)]
    inventory = [{"case_id": case, "gap_scale": gap, "accepted_force_field_exists": (case, gap) in accepted_keys}
                 for case, gap in keys]
    action = {"required_state_inventory": inventory, "states": states}
    action_sha = save("action/summary.json", action)
    action_receipt = {"output_sha256": {"summary.json": action_sha}}
    save("action/receipt.json", action_receipt)
    accepted = dict(zip(accepted_keys, states, strict=True))
    monkeypatch.setattr(acceptance, "finite_disposition_check", lambda *args: (inventory, accepted))
    binding = {"action_packet": "action", "action_receipt_sha256": sources["action/receipt.json"], "response": "frame",
        "source_force_fields_relabelled": False, **{field: sources["frame/"+name] for field, name in (
        ("response_receipt_sha256", "receipt.json"), ("response_comparison_sha256", "comparison.json"),
        ("response_npz_sha256", "response.npz"), ("joint_update_sha256", "joint-update.json"))}}
    axes = sorted(acceptance.TOPSIDE_AXES) + [f"scalar-{i:02}" for i in range(96)]
    geometry = [{"axis_id": axis, "end_role": role, "receiver_member": role+"-body"}
                for axis in axes for role in ("head", "nut")]
    rows, ends, support_rows = [], [], []
    for source in states:
        tag = source["state_tag"]
        for axis in axes:
            top = axis in acceptance.TOPSIDE_AXES
            join = {"active_action_binding": binding, "source_state_record": source["source_state_record"]}
            rows.append({"state_tag": tag, "axis_id": axis, "source_join": join,
                "status": "SOURCE_GEOMETRY_COUPLE_METHOD_LIMIT" if top else "SUPPORTED_ISOLATED_CURRENT_FORCE_FIELD",
                "state": None if top else {"signed_T_n": 1., "V_n": 2., "scaled_gradient_residuals_n": [0.],
                    "host_force_balance_residual_n": 0., "host_moment_balance_residual_nmm": 0.},
                "source_record": {"signed_T_n": 1., "V_n": 2.}, "effective_family": {"host_length_mm": 10., "cleat_length_mm": 10.},
                "same_state_steel_index": None if top else .5, "shaft_same_state_same_position_index": None if top else .5})
            for role in ("head", "nut"):
                ends.append({"state_tag": tag, "axis_id": axis, "end_role": role, "receiver_member": role+"-body",
                    "source_join": join, "status": "NULL_UNSUPPORTED" if top else "COMPLETE_ISOLATED_END_SOURCE",
                    "own_end_M_signed_xyz_nmm": None if top else [0., 3., 4.], "own_end_M_magnitude_nmm": None if top else 5.,
                    "actual_washer_metal_stress_complete": False})
            if top:
                support_rows.append({"state_tag": tag, "axis_id": axis, "own_end_moments_and_metal_stress_null": True,
                    "quarter_forces_transferred_to_working_5_16_field": False, "source_quarter_diameter_mm": 6.35,
                    "working_diameter_mm": 7.9375, "working_bore_diameter_mm": 9.})
    counts = {"attempted_shaft_states": 1200, "bore_samples": 55296, "complete_own_end_sources": 2304,
        "completed_shaft_states": 1152, "field_positions": 92160, "own_end_source_limits": 96,
        "shaft_numerical_stops": 0, "source_geometry_couple_method_limits": 48, "steel_reference_exceedances": 0}
    result = {"status": acceptance.SHAFT_STATUS, "all100_final_current_force_sweep": True,
        "finite_source_geometry_dispositions_complete": True, "ordinary_numerical_stops_are_pending": False,
        "active_action_binding": binding, "source_join": {"active_action_binding": binding, "force_branch": "washer_updated_compatible_frame"},
        "accepted_scope": {"required_state_inventory": inventory, "accepted_states": 12, "required_states": 14, "unavailable_states": 2},
        "current_geometry_audit": {"own_ends": geometry, "supported_scalar_own_ends": 192, "displaced_TOPSIDE_nominal_support_datums": 8,
            "historical_fields_transferred": False, "physical_geometry_changed": False, "loaded_support_or_actual_hardware_qualified": False},
        "counts": counts, **dict.fromkeys(("actual_washer_metal_stress_complete", "common_host_compatibility_established",
        "globally_compatible_scalar_shaft_curvature_established", "historical_force_or_acceptance_transferred",
        "isolated_fields_used_to_refresh_global_forces", "native_or_CAD_or_frame_run", "reviewed_geometry_changed"), False)}
    receipt = {"source_sha256": sources, "output_sha256": {}}
    entry = {"status": FINITE_DISPOSITION, "numerical_scope": acceptance.SHAFT_SCOPE, "receipt": "raw/receipt.json"}
    field = {"status": "PASS_INDEPENDENT_SAVED_FIELD_AND_SOURCE_AUDIT", "active_action_binding": binding,
        "original_numerical_auditor_AST_reverse_identity": True, "source_solves_or_optimizers_or_native_or_CAD_run": False,
        "geometry_limit_own_moments_and_metal_stresses_remain_null": True,
        "current_T_and_signed_two_component_source_rows_authenticated": 1200, "record_maps_authenticated": 2400,
        "current_geometry_end_checks": 2400, "actual_source_geometry_limit_axis_states": 48, "counts": deepcopy(counts),
        "independent_arithmetic_errors": dict.fromkeys(("moment_nmm", "beam_shear_n", "stress_mpa", "bore_motion_mm",
            "bore_force_n", "gradient_difference_n", "annular_force_residual_n", "annular_moment_error_nmm", "energy_nmm"), 0.)}
    support = {"status": "PASS_INDEPENDENT_CURRENT_TOPSIDE_ACTION_ORACLE_AND_NULL_END_AUDIT", "active_action_binding": binding,
        "scope": "isolated original-quarter source-geometry full-wrench normal-contact method; current working5/16 geometry remains a separate mismatch",
        "new_action_couple_values_recomputed": True, "signed_source_axial_and_lateral_full_actions_joined": True,
        "numerical_null_moments_or_metal_substituted": False, "quarter_fields_transferred_to_5_16": False, "axis_states": support_rows}
    audits = {}

    def refresh():
        packet = tmp_path/"raw"
        packet.mkdir(exist_ok=True)
        for name, values in (("shaft-states.jsonl", rows), ("washer-ends.jsonl", ends)):
            path = packet/name
            path.write_text("".join(json.dumps(row)+"\n" for row in values))
            receipt["output_sha256"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
        entry["receipt_sha256"] = write_json(packet/"receipt.json", receipt)
        for name, document, primary_field in (("field", field, "packet_receipt_sha256"), ("support", support, "shaft_receipt_sha256")):
            document[primary_field] = entry["receipt_sha256"]
            result_sha = write_json(tmp_path/name/"result.json", document)
            audit_receipt = audits.setdefault(name, {"source_sha256": {}, "output_sha256": {}})
            audit_receipt["source_sha256"][str(packet/"receipt.json")] = entry["receipt_sha256"]
            audit_receipt["output_sha256"]["result.json"] = result_sha
            receipt_sha = write_json(tmp_path/name/"receipt.json", audit_receipt)
            entry[name+"_audit_binding"] = {"receipt": {"path": name+"/receipt.json", "sha256": receipt_sha},
                "result": {"path": name+"/result.json", "sha256": result_sha}}

    def validate():
        acceptance.shaft_scope_check(tmp_path, entry, result, tmp_path/"raw", receipt, sources, {}, {})

    refresh()
    return result, rows, ends, field, support, entry, audits, refresh, validate


@pytest.mark.parametrize("fault", [None, "ordinary_stop", "null_zero", "invented_top_field", "missing_state", "duplicate_end",
    "stale_force", "signed_T", "original_equilibrium", "missing_own_moment", "working_transfer", "wrong_geometry",
    "audit_arithmetic", "false_counts", "missing_audit", "audit_wrong_basis"])
def test_current_shaft_disposition_requires_actual_fields_or_exact_source_limits(tmp_path, monkeypatch, fault):
    result, rows, ends, field, support, entry, audits, refresh, validate = shaft_fixture(tmp_path, monkeypatch)
    validate()
    if fault is None:
        return
    top_row = next(row for row in rows if row["axis_id"] in acceptance.TOPSIDE_AXES)
    finite_row = next(row for row in rows if row["axis_id"] not in acceptance.TOPSIDE_AXES)
    top_end = next(row for row in ends if row["axis_id"] in acceptance.TOPSIDE_AXES)
    if fault == "ordinary_stop":
        finite_row.update(status="NUMERICAL_STOP", state=None)
    elif fault == "null_zero":
        top_end["own_end_M_signed_xyz_nmm"] = [0., 0., 0.]
    elif fault == "invented_top_field":
        top_row["state"] = {"signed_T_n": 0.}
    elif fault == "missing_state":
        rows.pop()
    elif fault == "duplicate_end":
        ends[-1] = deepcopy(ends[-2])
    elif fault == "stale_force":
        finite_row["source_join"] = {"active_action_binding": {"action_receipt_sha256": "b"*64}}
    elif fault == "signed_T":
        finite_row["state"]["signed_T_n"] = -1.
    elif fault == "original_equilibrium":
        finite_row["state"]["scaled_gradient_residuals_n"] = [2e-6]
    elif fault == "missing_own_moment":
        next(row for row in ends if row["axis_id"] not in acceptance.TOPSIDE_AXES)["own_end_M_signed_xyz_nmm"] = None
    elif fault == "working_transfer":
        support["quarter_fields_transferred_to_5_16"] = True
    elif fault == "wrong_geometry":
        support["axis_states"][0]["source_quarter_diameter_mm"] = 7.9375
    elif fault == "audit_arithmetic":
        field["independent_arithmetic_errors"]["gradient_difference_n"] = 2e-7
    elif fault == "false_counts":
        result["counts"]["completed_shaft_states"] += 1
    refresh()
    if fault == "missing_audit":
        entry.pop("field_audit_binding")
    elif fault == "audit_wrong_basis":
        audits["field"]["source_sha256"] = {"unrelated.json": write_json(tmp_path/"unrelated.json", {})}
        entry["field_audit_binding"]["receipt"]["sha256"] = write_json(tmp_path/"field/receipt.json", audits["field"])
    with pytest.raises(ValueError):
        validate()


def washer_fixture(tmp_path, monkeypatch):
    """One accepted state, all 208 actual end identities and three finite roles."""
    index, _extension, entry, _result, receipt = extension_fixture(tmp_path)
    entry.update(status=FINITE_DISPOSITION, numerical_scope=acceptance.WASHER_SCOPE,
                 result_status=acceptance.WASHER_STATUS)
    entry.pop("counts")
    receipt.update(status=acceptance.WASHER_STATUS)
    sources = receipt["source_sha256"]
    documents, raw_receipts, arrays = {}, {}, {}

    def ref(name, pointer=None):
        value = {"path": name, "sha256": sources[name]}
        return value if pointer is None else {**value, "pointer": pointer}

    def save(name, value, owner):
        documents[name] = value
        digest = write_json(tmp_path / name, value)
        sources[name] = digest
        raw_receipts.setdefault(owner, {"source_sha256": {}, "output_sha256": {}})["output_sha256"][name.split("/", 1)[1]] = digest
        return ref(name)

    inventory = [{"case_id": case, "gap_scale": gap, "state_tag": case+("_zero" if not gap else "_gap"),
                  "accepted_force_field_exists": case == CASES[0] and gap == 0}
                 for case in CASES for gap in (0, 1)]
    tag = inventory[0]["state_tag"]
    comparison = {"analytical_branch": "working_washer_profile_with_explicit_member_replacements", "states": [
        {"case_id": CASES[0], "gap_scale": 0, "audit": {"all_passed": True, "checks": {"law": True}}}]}
    save("frame/comparison.json", comparison, "frame")
    state_reference = ref("frame/comparison.json", "/states/0")
    update = {"schema": "joint_frame_scalar_seat_update/v1", "geometry_changed": False, "preload_n": 0,
              "profile_receipt_sha256": "a"*64}
    save("frame/joint-update.json", update, "frame")
    save("frame/inputs.json", {"washer_joint_update": update, "source_force_fields_relabelled": False,
        "joint_update_sha256": sources["frame/joint-update.json"]}, "frame")
    arrays["frame/response.npz"] = {"saved_force": (1,)}
    action = {"schema": ACTION_SCHEMA, "required_state_inventory": inventory, "states": [
        {"case_id": CASES[0], "gap_scale": 0, "state_tag": tag, "source_state_record": state_reference}]}
    save("action/summary.json", action, "action")
    accepted = {(CASES[0], 0): action["states"][0]}
    # The existing frame/action gate has its own full real 14-state fixtures.
    # This fixture isolates current end arithmetic, source joins and field authority.
    monkeypatch.setattr(acceptance, "finite_disposition_check", lambda *args: ({}, accepted))
    axes = sorted(acceptance.TOPSIDE_AXES | acceptance.CONTINUOUS_AXES) + [f"scalar-{i:02}" for i in range(96)]
    geometry, own_ends, shaft_states, axis_states, raw_rows, rows, oracle_rows = [], [], [], [], [], [], []
    bodies = [{"state_tag": tag, "body": f"body-{i}", "actions": []} for i in range(50)]
    finite_axis, head_axis = "scalar-00", "scalar-01"
    for number, axis in enumerate(axes):
        shaft_states.append({"state_tag": tag, "axis_id": axis,
            "status": "SOURCE_GEOMETRY_COUPLE_METHOD_LIMIT" if axis in acceptance.TOPSIDE_AXES else "SUPPORTED_ISOLATED_CURRENT_FORCE_FIELD",
            "state": {"state_tag": tag, "axis_id": axis, "signed_T_n": 1., "V_n": math.sqrt(5),
                "scaled_gradient_residuals_n": [0.], "host_force_balance_residual_n": 0., "host_moment_balance_residual_nmm": 0.},
            "effective_family": {"host_length_mm": 10., "cleat_length_mm": 10.}})
        axis_states.append({"case_id": CASES[0], "gap_scale": 0, "state_tag": tag, "axis_id": axis,
            "source_state_record": state_reference, "signed_T_n": 1., "components_n": [1., 2.], "V_n": math.sqrt(5),
            "component_rows": [3*number, 3*number+1], "tie_row": 3*number+2, "point_xyz_mm": [0., 0., 0.],
            "bearing_lengths_mm": [10., 10.], "receivers": [f"body-{number % 50}", f"body-{(number+1) % 50}"]})
        for role in ("head", "nut"):
            body = f"body-{number % 50 if role == 'head' else (number+1) % 50}"
            geom = {"axis_id": axis, "end_role": role, "receiver_member": body, "datum_xyz_mm": [0., 0., 0.],
                    "saved_normal_into_receiver_xyz": [1., 0., 0.],
                    "profile_binding": {"plate_profile": {"head_radius_mm": 5.}}}
            geometry.append(geom)
            top = axis in acceptance.TOPSIDE_AXES
            tension = 1. if axis in {finite_axis, head_axis} else 0.
            moment = [0., 10., 0.] if axis == head_axis else [0., 0., 0.]
            force = [tension, 0., 0.]
            end = {"state_tag": tag, "axis_id": axis, "end_role": role, "receiver_member": body,
                "status": "NULL_UNSUPPORTED" if top else "COMPLETE_ISOLATED_END_SOURCE",
                "own_end_M_signed_xyz_nmm": None if top else moment,
                "normal_compression_T_n": tension, "normal_into_receiver_xyz": [1., 0., 0.],
                "force_on_receiver_xyz_n": force, "end_wrench_datum_global_xyz_mm": [0., 0., 0.]}
            if axis in acceptance.CONTINUOUS_AXES:
                end.update(continuous_own_end=True, own_end_moment_unknown_not_zero=False, signed_end_compression_n=tension,
                           own_end_wood_moment_xyz_nmm=moment, support={"seat_point_xyz_mm": [0., 0., 0.]})
            own_ends.append(end)
            join_key = ["washer_updated_compatible_frame", tag, axis, role, body]
            status = acceptance.WASHER_TOPSIDE if top else acceptance.WASHER_FINITE if axis == finite_axis else (
                acceptance.WASHER_HEAD if axis == head_axis else acceptance.WASHER_ZERO)
            source = {"join_key": join_key, "source_state_record": state_reference,
                "source_force_compatibility": axis in acceptance.CONTINUOUS_AXES, "geometry": geom,
                "T_n": tension, "M_magnitude_nmm": math.hypot(*moment), "source_signed_own_M_xyz_nmm": moment,
                "force_on_receiver_xyz_n": force, "normal_into_receiver_xyz": [1., 0., 0.], "own_seat_xyz_mm": [0., 0., 0.],
                "chart_x_xyz": [0., 0., 1.], "chart_y_xyz": [0., -1., 0.],
                "plate_pressure_first_moment_targets_nmm": [moment[1], -moment[2]],
                "head_compression_certificate": {"status": acceptance.WASHER_HEAD, "pressing_outer_radius_mm": 5.,
                                                 "necessary_condition_only": True},
                "source_shaft_status": "SOURCE_GEOMETRY_COUPLE_METHOD_LIMIT" if top else "FINITE_SHAFT_FIELD"}
            raw = {"status": "SOURCE_END_MOMENT_UNAVAILABLE" if top else status, "source": source,
                   "sampled_stress_proxy_mpa": 300. if status == acceptance.WASHER_FINITE else 0. if status == acceptance.WASHER_ZERO else None,
                   "stress_proxy_over_Fy250": 1.2 if status == acceptance.WASHER_FINITE else 0. if status == acceptance.WASHER_ZERO else None,
                   "actual_field_exists": status == acceptance.WASHER_FINITE}
            row = {"join_key": join_key, "status": status, "source_state_record": state_reference,
                "source_force_compatibility": axis in acceptance.CONTINUOUS_AXES,
                "metal_stress_mpa": raw["sampled_stress_proxy_mpa"], "metal_reference_index": raw["stress_proxy_over_Fy250"],
                "actual_field_exists": raw["actual_field_exists"]}
            if status == acceptance.WASHER_FINITE:
                raw.update(sampled_reference_exceeded=True, signed_equilibrium_and_contact=[{
                    "contact": contact, "signed_equilibrium_passed": True, "force_vector_max_residual_n": 0.,
                    "moment_vector_max_residual_nmm": 0., "inactive_pressure_max_mpa": 0., "unilateral_law_residual_mpa": 0.,
                    "pressure_peak_mpa": 1., "force_on_receiver_xyz_n": force, "own_seat_M_signed_xyz_nmm": moment}
                    for contact in ("wood", "head")])
                filename = "plates/field-"+role+".npz"
                arrays[filename] = {"pose_mm": (3,), **{contact+suffix: shape for contact in ("wood", "head")
                    for suffix, shape in (("_pressure_mpa", (2,)), ("_area_mm2", (2,)), ("_local_xy_mm", (2, 2)))}}
                raw["retained_field"] = row["retained_field"] = {"path": filename}
            elif status == acceptance.WASHER_HEAD:
                row["head_circle_bound"] = {"T_n": tension, "M_magnitude_nmm": 10., "signed_M_xyz_nmm": moment,
                    "pressing_radius_mm": 5., "maximum_normal_contact_moment_nmm": 5.,
                    "necessary_bound_exceeded": True, "no_steel_stress_or_capacity_inferred": True}
            raw_rows.append(raw)
            rows.append(row)
        if axis in acceptance.TOPSIDE_AXES:
            selected = [{"row": 3*number+i, "point_mm": [0., 0., 0.], "force_n": force,
                "scalar_row_force_n": [1., 2., 1.][i],
                "free_moment_nmm": [1., 0., 0.] if i == 0 else [0., 0., 0.],
                "source_force_available": True, "replaced_source_row_placeholder": False}
                for i, force in enumerate(([0., 1., 0.], [0., 0., 2.], [1., 0., 0.]))]
            bodies[number % 50]["actions"] += selected
            axis_states[-1]["unrepresented_source_couples_at_physical_interface"] = {
                "exact_source_body_actions_on_first_body": selected,
                "exported_lateral_full_force_equivalent_couple_xyz_nmm": [1., 0., 0.],
                "exported_axial_full_force_equivalent_couple_xyz_nmm": [0., 0., 0.]}
            oracle_rows.append({**axis_states[-1], "first_body": f"body-{number % 50}",
                "second_body": f"body-{(number+1) % 50}",
                "geometry_applicability": {"physical_interface_point_xyz_mm": [0., 0., 0.]},
                "shaft_axis_head_to_nut_xyz": [1., 0., 0.], "exact_source_body_actions_on_first_body": selected,
                "numerical_disposition_finite_within_declared_domain": True, "own_end_moments_or_metal_stress_available": False,
                "required_torsion_treated_as_zero": False, "original_length_scaled_moment_gate_nmm": 20.*1e-6,
                "required_torsion_exceeds_original_moment_gate": True,
                "classification": "LOAD_PATH_INCOMPATIBILITY_OF_ISOLATED_FULL_SOURCE_WRENCH_NORMAL_CONTACT_BRANCH",
                "components": {name: {"full_couple_xyz_nmm": value, "signed_parallel_nmm": value[0],
                    "parallel_couple_xyz_nmm": value, "perpendicular_couple_xyz_nmm": [0., 0., 0.]}
                    for name, value in (("lateral", [1., 0., 0.]), ("axial_tie", [0., 0., 0.]), ("total", [1., 0., 0.]))}})
    save("plates/input-plan.json", {"geometry_joins": geometry, "pilot_source_only": False}, "plates")
    save("profile/contract.json", {"schema": "washer_working_profile_contract/v1", "status": "FROZEN_NUMERICAL_PROFILE_CONTRACT",
        "hypotheses": {"E_mpa": 200000., "nu": .3, "Fy_mpa": 250., "Kwood_mpa_per_mm": 20., "Khead_mpa_per_mm": 10000.,
                       "preload_n": 0., "first_order": True, "concentric_nominal_seats": True}}, "profile")
    law = {"status": "PASS_NORMAL_TRACTION_TORSION_SUPPORT_ORACLE_AND_SAVED_ACTION_DECOMPOSITION", "proof": ["normal torque zero"],
        "hypotheses": {"circular_coaxial_bore": True, "first_order_normal_traction_directions": True, "friction": 0.,
            "installation_preload_n": 0., "tangential_contact_or_anti_rotation_feature_credited": False,
            "washer_traction_parallel_to_shaft": True},
        "known_answer_fixtures": [{"bore_axial_torque_nmm": 0., "normal_end_axial_torque_nmm": 0.}]}
    save("law/result.json", law, "law")
    oracle = {"schema": "joint_frame_prescribed_shaft_normal_contact_support/v1",
        "status": "COMPLETE_ACTUAL_ACCEPTED_SOURCE_GEOMETRY_COUPLE_DISPOSITIONS_NOT_METAL_COMPARISONS",
        "historical_action_couple_values_transferred": False, "metal_comparisons_complete": False,
        "analytical_normal_traction_law": law["proof"], "hypotheses": law["hypotheses"], "axis_states": oracle_rows,
        "counts": {"accepted_states": 1, "limited_axis_states": 4, "own_ends_remaining_null": 8}}
    shaft = {"source_join": {"force_branch": "washer_updated_compatible_frame"}, "all100_final_current_force_sweep": True}
    plate = {"force_branch": "washer_updated_compatible_frame", "required_state_inventory": inventory,
             "counts": {"unperformed_accepted_plate_inputs": 0, "missing_accepted_own_ends": 0}}
    result = {"schema": acceptance.WASHER_SCHEMA, "numerical_scope": acceptance.WASHER_SCOPE,
        "status": acceptance.WASHER_STATUS, "numerical_end_disposition_complete": True, "metal_comparisons_complete": False,
        "required_state_inventory": inventory, "force_branch": "washer_updated_compatible_frame", "end_dispositions": rows,
        "counts": {"accepted_states": 1, "canonical_physical_ends": 208, "required_accepted_end_states": 208,
            "recorded_end_dispositions": 208, "unassessed_accepted_end_states": 0, "unavailable_required_state_ends": 2704,
            "status_counts": {acceptance.WASHER_FINITE: 2, acceptance.WASHER_HEAD: 2, acceptance.WASHER_ZERO: 196,
                              acceptance.WASHER_TOPSIDE: 8}, "finite_metal_fields": 2, "TOPSIDE_null_metal_ends": 8,
            "sampled_Fy250_exceedances": 2}, **{flag: False for flag in (
                "actual_hardware_inspected", "isolated_scalar_curvature_is_globally_compatible", "plate_fields_refresh_coupled_forces",
                "historical_forces_transferred", "native_CAD_or_frame_solve_run", "complete_joint_acceptance", "physical_release")},
        "actual_washer_capacity_n": None, "actual_washer_yield_mpa": None}

    def flush_jsonl(name, records, owner):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row, sort_keys=True)+"\n" for row in records))
        sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        raw_receipts.setdefault(owner, {"source_sha256": {}, "output_sha256": {}})["output_sha256"][name.split("/", 1)[1]] = sources[name]

    def refresh():
        for name, shape in arrays.items():
            path = tmp_path / name
            path.parent.mkdir(exist_ok=True)
            sources[name] = write_arrays(path, shape)
            raw_receipts.setdefault(name.split("/")[0], {"source_sha256": {}, "output_sha256": {}})["output_sha256"][name.split("/", 1)[1]] = sources[name]
        save("frame/comparison.json", comparison, "frame")
        for item in action["states"]:
            item["source_state_record"] = ref("frame/comparison.json", "/states/0")
        save("action/summary.json", action, "action")
        for owner in ("frame", "action", "law"):
            sources[owner+"/receipt.json"] = write_json(tmp_path / owner / "receipt.json", raw_receipts[owner])
        path = tmp_path / "action/body-actions.jsonl.gz"
        with gzip.open(path, "wt") as stream:
            stream.writelines(json.dumps(row)+"\n" for row in bodies)
        sources["action/body-actions.jsonl.gz"] = hashlib.sha256(path.read_bytes()).hexdigest()
        raw_receipts["action"]["output_sha256"]["body-actions.jsonl.gz"] = sources["action/body-actions.jsonl.gz"]
        sources["action/receipt.json"] = write_json(tmp_path / "action/receipt.json", raw_receipts["action"])
        binding = {"action_packet": "action", "action_receipt_sha256": sources["action/receipt.json"], "response": "frame",
            "response_receipt_sha256": sources["frame/receipt.json"], "response_comparison_sha256": sources["frame/comparison.json"],
            "response_npz_sha256": sources["frame/response.npz"], "joint_update_sha256": sources["frame/joint-update.json"],
            "profile_receipt_sha256": "a"*64, "source_force_fields_relabelled": False}
        for source in axis_states:
            if source["axis_id"] in acceptance.TOPSIDE_AXES:
                source["unrepresented_source_couples_at_physical_interface"].update(
                    body_action_path="action/body-actions.jsonl.gz", body_action_sha256=sources["action/body-actions.jsonl.gz"])
        save("preparation/source-force-records.json", {"records": axis_states}, "preparation")
        for item in shaft_states+own_ends:
            item["source_join"] = {"active_action_binding": binding}
        flush_jsonl("shafts/shaft-states.jsonl", shaft_states, "shafts")
        flush_jsonl("shafts/own-ends.jsonl", own_ends, "shafts")
        for i, row in enumerate(oracle_rows):
            axis_index = axes.index(row["axis_id"])
            row.update(source_axis_state_record=ref("preparation/source-force-records.json", f"/records/{axis_index}"),
                       source_join={"active_action_binding": binding})
        oracle.update(active_action_binding=binding, historical_law_oracle_receipt_sha256=sources["law/receipt.json"])
        save("preparation/input-plan.json", {"families": {row["axis_id"]: {
            "direction": row["shaft_axis_head_to_nut_xyz"], "geometry_applicability": row["geometry_applicability"]}
            for row in oracle_rows}}, "preparation")
        save("preparation/support-oracle.json", oracle, "preparation")
        for i, (raw, row) in enumerate(zip(raw_rows, rows)):
            raw["source"]["source_endrecord"] = ref("shafts/own-ends.jsonl", f"/{i}")
            row["source_own_end_record"] = raw["source"]["source_endrecord"]
            axis = row["join_key"][2]
            if axis not in acceptance.CONTINUOUS_AXES:
                row["source_shaft_state_record"] = ref("shafts/shaft-states.jsonl", f"/{axes.index(axis)}")
                row["source_axis_state_record"] = ref("preparation/source-force-records.json", f"/records/{axes.index(axis)}")
            if row["status"] == acceptance.WASHER_TOPSIDE:
                oracle_index = next(j for j, v in enumerate(oracle_rows) if v["axis_id"] == axis)
                row.update(support_oracle_record=ref("preparation/support-oracle.json", f"/axis_states/{oracle_index}"),
                    source_couple_classification=oracle_rows[oracle_index]["classification"],
                    source_moments_unavailable_not_zero=True, nominal_source_point_support_does_not_qualify_actual_shaft_seat=True)
            if raw.get("retained_field"):
                raw["retained_field"]["sha256"] = sources[raw["retained_field"]["path"]]
        flush_jsonl("plates/end-states.jsonl", raw_rows, "plates")
        for i, row in enumerate(rows):
            row["source_plate_record"] = ref("plates/end-states.jsonl", f"/{i}")
        plate.update(action_source_receipt=ref("action/receipt.json"), profile_contract=ref("profile/contract.json"))
        shaft.update(active_action_binding=binding)
        shaft["source_join"]["action_receipt_sha256"] = sources["action/receipt.json"]
        save("plates/summary.json", plate, "plates")
        save("shafts/summary.json", shaft, "shafts")
        for owner, document in raw_receipts.items():
            sources[owner+"/receipt.json"] = write_json(tmp_path / owner / "receipt.json", document)
        result.update(action_source_receipt=ref("action/receipt.json"), profile_contract=ref("profile/contract.json"),
            raw_plate_receipt=ref("plates/receipt.json"), raw_shaft_receipt=ref("shafts/receipt.json"),
            support_oracle=ref("preparation/support-oracle.json"), canonical_geometry=ref("plates/input-plan.json", "/geometry_joins"))
        receipt["counts"] = deepcopy(result["counts"])
        entry["result_sha256"] = receipt["output_sha256"]["result.json"] = write_json(tmp_path / "packet/result.json", result)
        entry["receipt_sha256"] = write_json(tmp_path / "packet/receipt.json", receipt)
        write_json(tmp_path / "index.json", index)

    refresh()
    return result, raw_rows, own_ends, oracle, bodies, arrays, raw_receipts, refresh


@pytest.mark.parametrize("fault", ["missing_end", "duplicate_end", "metal_claim", "raw_stop", "false_zero",
    "invalid_head_bound", "invented_topside_moment", "stale_couples", "torsion_ignored", "bad_field_shape",
    "failed_contact", "unowned_field", "bad_stress_index", "old_force_branch", "wrong_end_identity",
    "shaft_stop", "shaft_gate", "torsion_gate", "source_V"])
def test_washer_current_end_disposition_rejects_invented_or_missing_evidence(tmp_path, monkeypatch, fault):
    result, raw, ends, oracle, bodies, arrays, receipts, refresh = washer_fixture(tmp_path, monkeypatch)
    assert check("index.json", tmp_path)["finite_disposition_packets"] == 1
    finite = next(i for i, row in enumerate(result["end_dispositions"]) if row["status"] == acceptance.WASHER_FINITE)
    head = next(i for i, row in enumerate(result["end_dispositions"]) if row["status"] == acceptance.WASHER_HEAD)
    top = next(i for i, row in enumerate(result["end_dispositions"]) if row["status"] == acceptance.WASHER_TOPSIDE)
    zero = next(i for i, row in enumerate(result["end_dispositions"]) if row["status"] == acceptance.WASHER_ZERO)
    if fault == "missing_end":
        result["end_dispositions"].pop()
    elif fault == "duplicate_end":
        result["end_dispositions"][-1] = deepcopy(result["end_dispositions"][0])
    elif fault == "metal_claim":
        result["metal_comparisons_complete"] = True
    elif fault == "raw_stop":
        raw[finite]["status"] = "NUMERICAL_STOP_NOT_COMPLETE"
    elif fault == "false_zero":
        raw[zero]["source"]["T_n"] = 1e-12
    elif fault == "invalid_head_bound":
        result["end_dispositions"][head]["head_circle_bound"]["pressing_radius_mm"] = 50.
    elif fault == "invented_topside_moment":
        ends[top]["own_end_M_signed_xyz_nmm"] = [0., 0., 0.]
    elif fault == "stale_couples":
        next(body for body in bodies if body["actions"])["actions"][0] = {
            **next(body for body in bodies if body["actions"])["actions"][0], "free_moment_nmm": [2., 0., 0.]}
    elif fault == "torsion_ignored":
        oracle["axis_states"][0]["required_torsion_treated_as_zero"] = True
    elif fault == "bad_field_shape":
        arrays["plates/field-head.npz"]["wood_pressure_mpa"] = (0,)
    elif fault == "failed_contact":
        raw[finite]["signed_equilibrium_and_contact"][0]["force_vector_max_residual_n"] = .002
    elif fault == "unowned_field":
        refresh()
        receipts["plates"]["output_sha256"].pop("field-head.npz")
        arrays.pop("plates/field-head.npz")
    elif fault == "bad_stress_index":
        result["end_dispositions"][finite]["metal_reference_index"] = .9
    elif fault == "wrong_end_identity":
        ends[finite]["end_role"] = "nut"
    elif fault in {"shaft_stop", "shaft_gate"}:
        states = [json.loads(line) for line in (tmp_path / "shafts/shaft-states.jsonl").read_text().splitlines()]
        target = next(row for row in states if row["axis_id"] == result["end_dispositions"][finite]["join_key"][2])
        if fault == "shaft_stop":
            target["status"] = "STOP_NUMERICAL_FIELD_UNAVAILABLE"
        else:
            target["state"]["host_force_balance_residual_n"] = 2e-6
        # Refresh preserves the actual source list held by the fixture; replace
        # the authenticated raw file after its final publication below instead.
        refresh()
        path = tmp_path / "shafts/shaft-states.jsonl"
        path.write_text("".join(json.dumps(row)+"\n" for row in states))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        receipts["shafts"]["output_sha256"]["shaft-states.jsonl"] = digest
        index = json.loads((tmp_path / "index.json").read_text())
        packet_receipt = json.loads((tmp_path / "packet/receipt.json").read_text())
        packet_receipt["source_sha256"]["shafts/shaft-states.jsonl"] = digest
        shaft_receipt_sha = write_json(tmp_path / "shafts/receipt.json", receipts["shafts"])
        packet_receipt["source_sha256"]["shafts/receipt.json"] = shaft_receipt_sha
        result["raw_shaft_receipt"]["sha256"] = shaft_receipt_sha
        for row in result["end_dispositions"]:
            if "source_shaft_state_record" in row:
                row["source_shaft_state_record"]["sha256"] = digest
        result_sha = write_json(tmp_path / "packet/result.json", result)
        packet_receipt["output_sha256"]["result.json"] = result_sha
        index["numerical_acceptance_extension"]["results"]["study"].update(result_sha256=result_sha,
            receipt_sha256=write_json(tmp_path / "packet/receipt.json", packet_receipt))
        write_json(tmp_path / "index.json", index)
        with pytest.raises(ValueError, match="washer.*shaft"):
            check("index.json", tmp_path)
        return
    elif fault == "torsion_gate":
        oracle["axis_states"][0]["original_length_scaled_moment_gate_nmm"] = 1.
    elif fault == "source_V":
        oracle["axis_states"][0]["V_n"] = 6.
    else:
        result["force_branch"] = "historical_action03"
    refresh()
    with pytest.raises((ValueError, KeyError, IndexError), match="washer|TOPSIDE|metal|field"):
        check("index.json", tmp_path)


def publish_washer_source_bindings(tmp_path, result, bindings, *, removed=()):
    """Republish fixture metadata after changing a raw owner, preserving its fields."""
    receipt = json.loads((tmp_path / "packet/receipt.json").read_text())
    for name in removed:
        receipt["source_sha256"].pop(name)
    receipt["source_sha256"].update(bindings)
    for field in ("action_source_receipt", "raw_plate_receipt", "raw_shaft_receipt"):
        reference = result[field]
        if reference["path"] in bindings:
            reference["sha256"] = bindings[reference["path"]]
    result_sha = write_json(tmp_path / "packet/result.json", result)
    receipt["output_sha256"]["result.json"] = result_sha
    index = json.loads((tmp_path / "index.json").read_text())
    index["numerical_acceptance_extension"]["results"]["study"].update(
        result_sha256=result_sha, receipt_sha256=write_json(tmp_path / "packet/receipt.json", receipt))
    write_json(tmp_path / "index.json", index)


@pytest.mark.parametrize("fault", [None, "missing_snapshot_pin", "wrong_owner_source_sha",
                                  "malformed_owner_redirect", "invalid_owner_source_sha", "ambiguous_owner"])
def test_washer_consumed_owner_preserves_its_own_source_snapshot(tmp_path, monkeypatch, fault):
    result, _raw, _ends, _oracle, _bodies, _arrays, receipts, _refresh = washer_fixture(tmp_path, monkeypatch)
    original, snapshot = "profile/producer.py", "profile/producer.py.snapshot"
    (tmp_path / snapshot).write_text("frozen profile producer")
    frozen_sha = hashlib.sha256((tmp_path / snapshot).read_bytes()).hexdigest()
    (tmp_path / original).write_text("later maintained profile producer")
    current_sha = hashlib.sha256((tmp_path / original).read_bytes()).hexdigest()
    owner = deepcopy(receipts["profile"])
    owner["source_sha256"] = {original: frozen_sha}
    owner["source_resolution"] = {original: {
        "original_path": original, "snapshot_path": snapshot, "sha256": frozen_sha}}
    # The primary closure stores the resolved snapshot using an absolute alias;
    # the current original bytes remain separately pinned, never repinned.
    snapshot_key = str(tmp_path / snapshot)
    bindings = {snapshot_key: frozen_sha, original: current_sha}
    if fault == "wrong_owner_source_sha":
        owner["source_sha256"][original] = "0" * 64
    elif fault == "malformed_owner_redirect":
        owner["source_resolution"][original]["original_path"] = "another-producer.py"
    elif fault == "invalid_owner_source_sha":
        owner["source_sha256"][original] = "not-a-SHA256"
    bindings["profile/receipt.json"] = write_json(tmp_path / "profile/receipt.json", owner)
    if fault == "ambiguous_owner":
        digest = json.loads((tmp_path / "packet/receipt.json").read_text())["source_sha256"]["profile/contract.json"]
        bindings["receipt.json"] = write_json(tmp_path / "receipt.json", {
            "source_sha256": {}, "output_sha256": {"profile/contract.json": digest}})
    else:
        # An unused historical receipt is preserved as context; it supplies no
        # current record authority and does not require a conflicting flattening.
        bindings["history/receipt.json"] = write_json(tmp_path / "history/receipt.json", {
            "source_sha256": {original: frozen_sha}, "output_sha256": {}})
    publish_washer_source_bindings(tmp_path, result, bindings)
    # Remove only after publication: the negative retains the actual old file
    # and owner redirect, but omits its authenticated primary source binding.
    if fault == "missing_snapshot_pin":
        publish_washer_source_bindings(tmp_path, result, {}, removed=(snapshot_key,))
    if fault is None:
        assert check("index.json", tmp_path)["finite_disposition_packets"] == 1
        assert hashlib.sha256((tmp_path / snapshot).read_bytes()).hexdigest() == frozen_sha
        assert hashlib.sha256((tmp_path / original).read_bytes()).hexdigest() == current_sha
    else:
        with pytest.raises(ValueError, match="washer|redirect|SHA256"):
            check("index.json", tmp_path)


@pytest.mark.parametrize("output", ["field-head.npz", "field-nut.npz", "input-plan.json", "end-states.jsonl"])
def test_washer_historical_advertiser_cannot_replace_current_plate_owner(tmp_path, monkeypatch, output):
    result, _raw, _ends, _oracle, _bodies, _arrays, receipts, _refresh = washer_fixture(tmp_path, monkeypatch)
    assert check("index.json", tmp_path)["finite_disposition_packets"] == 1
    owner = deepcopy(receipts["plates"])
    digest = owner["output_sha256"].pop(output)
    bindings = {"plates/receipt.json": write_json(tmp_path / "plates/receipt.json", owner),
        "receipt.json": write_json(tmp_path / "receipt.json", {
            "source_sha256": {}, "output_sha256": {"plates/" + output: digest}})}
    publish_washer_source_bindings(tmp_path, result, bindings)
    with pytest.raises(ValueError, match="current plate receipt|artifact absent from receipt outputs"):
        check("index.json", tmp_path)


@pytest.mark.parametrize("torque, accepted", [
    (2.34e-13, True), (-2.34e-13, True), (2e-12 - 1e-20, True),
    (2e-12, False), (-2e-12, False), (2e-12 + 1e-20, False),
])
def test_washer_normal_contact_oracle_uses_its_original_torque_bound(tmp_path, monkeypatch, torque, accepted):
    result, _raw, _ends, _oracle, _bodies, _arrays, receipts, refresh = washer_fixture(tmp_path, monkeypatch)
    law = json.loads((tmp_path / "law/result.json").read_text())
    law["known_answer_fixtures"][0]["normal_end_axial_torque_nmm"] = torque
    digest = write_json(tmp_path / "law/result.json", law)
    receipts["law"]["output_sha256"]["result.json"] = digest
    refresh()
    publish_washer_source_bindings(tmp_path, result, {"law/result.json": digest})
    if accepted:
        assert check("index.json", tmp_path)["finite_disposition_packets"] == 1
    else:
        with pytest.raises(ValueError, match="known-answer torque identity"):
            check("index.json", tmp_path)


def motion_fixture(tmp_path):
    index, _extension, entry, _result, receipt = extension_fixture(tmp_path)
    packet = tmp_path / "packet"
    sources = receipt["source_sha256"]

    def source(name, value):
        sources[name] = write_json(tmp_path / name, value)
        return {"path": name, "sha256": sources[name]}

    states, inventory = [], []
    for case in CASES:
        for gap in (0, 1):
            tag = case + ("_zero" if gap == 0 else "_gap")
            record = {"case_id": case, "gap_scale": gap, "audit": {"all_passed": True, "checks": {"law": True}}}
            states.append(record)
            inventory.append({"case_id": case, "gap_scale": gap, "state_tag": tag,
                              "status": ACCEPTED_STATE, "accepted_force_field_exists": True})
    comparison = {"schema": FRAME_SCHEMA, "states": states, "case_dispositions": deepcopy(inventory)}
    reference = source("frame/comparison.json", comparison)
    source("frame/receipt.json", {"output_sha256": {"comparison.json": reference["sha256"]}})
    for i, item in enumerate(inventory):
        item["source_state_record"] = {**reference, "pointer": f"/states/{i}"}
        item["source_disposition_record"] = {**reference, "pointer": f"/case_dispositions/{i}"}
    action = {"schema": ACTION_SCHEMA, "required_state_inventory": inventory}
    action_reference = source("action/summary.json", action)
    source("action/receipt.json", {"output_sha256": {"summary.json": action_reference["sha256"]}})
    motion_states, arrays = [], {}
    for item in inventory:
        tag = item["state_tag"]
        motion_states.append({**item, "original_law_audit": {"all_passed": True, "checks": {"law": True}},
            "fixed_row_svd": {"rank": 344}, "coordinate_nullity": 0, "body_projection_rank": 0,
            "metal_only_nullity": 0, "coordinate_increment_intervals_scaled_mm": [[0., 0.] for _ in range(344)],
            "coordinate_bound_certificates": [{side: {"status": "finite", "maximum": 0., "zero_observable": True}
                                                for side in ("lower", "upper")} for _ in range(344)],
            "recession_certificates": [], "body_seating_bounded": True, "all_coordinate_seating_bounded": True,
            "body_motion_bounds": [{"body": f"body-{i}", "kind": "timber" if i < 44 else "panel",
                                    "absolute_elastic_deformed_node_motion_recovered": False} for i in range(50)],
            "original_law_nonunique_body_witness": None,
            "stability_implications": {"fixed_force_local_reactions_changed": False,
                "source_linear_elastic_field_unchanged_at_fixed_forces": True,
                "second_order_buckling_or_dynamic_stability_established": False,
                "admissible_body_flat_direction_demonstrated": False}})
        arrays.update({tag + "_" + suffix: shape for suffix, shape in {
            "nullspace": (344, 0), "A_ub": (0, 0), "b_ub": (0,),
            "dual_multipliers": (0, 0), "coordinate_extrema": (0, 0)}.items()})
    request = {"schema": "joint_frame_fixed_force_motion_request/v1", "fixed_force_only": True,
               "motion_tolerance_mm": 1e-8, "coefficient_roundoff_threshold": 1e-11,
               "actions": "action", "response": "frame", "required_state_inventory": inventory,
               "accepted_tags": [item["state_tag"] for item in inventory]}
    result = {"schema": MOTION_SCHEMA, "status": MOTION_STATUS, "required_state_inventory": inventory,
              "states": motion_states, "source_sha256": sources,
              "first_order_stability_implication_assessment_complete": True,
              "second_order_stability_established": False, "source_force_fields_changed": False,
              "source_producers_frame_native_or_CAD_executed": False, "numerical_goal_complete": False,
              "counts": {"required_states": 14, "accepted_states_assessed": 14,
                         "source_floor_stops_without_pose_field": 0, "body_seating_bounded_states": 14,
                         "all_coordinate_bounded_states": 14, "nonunique_body_witness_states": 0}}
    coupon = {"status": "PASS_ANALYTIC_FIXED_FORCE_POSE_COUPONS",
              "disk_intervals": [[-2.00000001, 2.00000001], [-2.00000001, 2.00000001], [None, None]],
              "open_unilateral_interval": [None, 1e-8]}
    entry.update(numerical_scope=MOTION_SCOPE, result_status=MOTION_STATUS)
    receipt.update(status=MOTION_STATUS)
    entry.pop("counts")
    receipt.pop("counts")

    def refresh():
        receipt["output_sha256"]["request.json"] = write_json(packet / "request.json", request)
        receipt["output_sha256"]["certificates.npz"] = write_arrays(packet / "certificates.npz", arrays)
        receipt["output_sha256"]["known-answer.json"] = write_json(packet / "known-answer.json", coupon)
        entry["result_sha256"] = receipt["output_sha256"]["result.json"] = write_json(packet / "result.json", result)
        entry["receipt_sha256"] = write_json(packet / "receipt.json", receipt)
        write_json(tmp_path / "index.json", index)

    refresh()
    return result, entry, receipt, arrays, refresh


@pytest.mark.parametrize("fault", ["missing_state", "duplicate_state", "stale_pointer", "old_300_intervals",
    "old_300_array", "old_300_rank", "omitted_body", "second_order", "changed_forces", "failed_law",
    "bad_support", "unbounded_without_ray", "witness_changed_force", "untyped_scope", "bad_known_answer"])
def test_fixed_force_motion_rejects_incomplete_or_transferred_certificates(tmp_path, fault):
    result, entry, _receipt, arrays, refresh = motion_fixture(tmp_path)
    assert check("index.json", tmp_path)["pending_workstreams"] == 0
    state = result["states"][0]
    if fault == "missing_state":
        result["states"].pop()
    elif fault == "duplicate_state":
        result["states"][-1] = deepcopy(state)
    elif fault == "stale_pointer":
        state["source_state_record"] = {**state["source_state_record"], "pointer": "/states/1"}
    elif fault == "old_300_intervals":
        state["coordinate_increment_intervals_scaled_mm"] = state["coordinate_increment_intervals_scaled_mm"][:300]
    elif fault == "old_300_array":
        arrays[state["state_tag"] + "_nullspace"] = (300, 0)
    elif fault == "old_300_rank":
        state["fixed_row_svd"]["rank"] = 300
    elif fault == "omitted_body":
        state["body_motion_bounds"].pop()
    elif fault == "second_order":
        result["second_order_stability_established"] = True
    elif fault == "changed_forces":
        result["source_force_fields_changed"] = True
    elif fault == "failed_law":
        state["original_law_audit"]["checks"]["law"] = False
    elif fault == "bad_support":
        state["coordinate_bound_certificates"][0]["upper"]["maximum"] = 1.
    elif fault == "unbounded_without_ray":
        state["coordinate_increment_intervals_scaled_mm"][0][0] = None
        state["coordinate_bound_certificates"][0]["lower"] = {"status": "unbounded", "recession_certificate": 0}
    elif fault == "witness_changed_force":
        state["original_law_nonunique_body_witness"] = {"force_field_changed": True, "coordinate_increment": [0.] * 344}
        state["stability_implications"]["admissible_body_flat_direction_demonstrated"] = True
    elif fault == "untyped_scope":
        entry.pop("numerical_scope")
    else:
        # Change the saved coupon and its binding coherently; hashes alone must not prove the method.
        refresh()
        packet = tmp_path / "packet"
        coupon = json.loads((packet / "known-answer.json").read_text())
        coupon["disk_intervals"][0][1] = 3.
        _receipt["output_sha256"]["known-answer.json"] = write_json(packet / "known-answer.json", coupon)
        entry["receipt_sha256"] = write_json(packet / "receipt.json", _receipt)
        index = json.loads((tmp_path / "index.json").read_text())
        index["numerical_acceptance_extension"]["results"]["study"] = entry
        write_json(tmp_path / "index.json", index)
        with pytest.raises(ValueError):
            check("index.json", tmp_path)
        return
    refresh()
    with pytest.raises(ValueError):
        check("index.json", tmp_path)


def representative_fixture(tmp_path, monkeypatch, *, eligible=False):
    """A small saved-field contract; no matrix assembly, native model or solve."""
    monkeypatch.setattr(acceptance, "CURRENT_COUPLED_PORT_COUNT", 1)
    sources, outputs, documents, arrays = {}, {}, {}, {}
    packet, native = tmp_path / "aggregate", tmp_path / "native"
    packet.mkdir()
    native.mkdir()

    def source(name, value):
        sources[name] = write_json(tmp_path / name, value)
        return {"path": name, "sha256": sources[name]}

    def output(name, value):
        documents[name] = value
        outputs[name] = write_json(native / name, value)
        return {"path": "native/" + name, "sha256": outputs[name]}

    def field(name, shapes):
        arrays[name] = shapes
        outputs[name] = write_arrays(native / name, shapes)
        return {"path": "native/" + name, "sha256": outputs[name]}

    path = {"id": "end/1/high", "axis": 1, "plane_mm": 0., "initial_interval_mm": [5., 10.],
            "final_interval_mm": [0., 10.], "kind": "grain_end"}
    old_records = [{"body": f"body-{i}", "finite_paths": [{**path, "id": "end/1/high" if j == 0 else f"path-{j}"}
                    for j in range(18 if i < 24 else 17)]} for i in range(44)]
    old_reference = source("old.json", {"records": old_records})
    monkeypatch.setattr(acceptance, "ORIGINAL_SPLITTING_INVENTORY_SHA256", old_reference["sha256"])
    duties = [{"joint_id": f"duty-{i}", "timber_sides": [f"body-{i}"] + ([f"body-{30+i}"] if i < 14 else [])}
              for i in range(30)]
    prepared_plan = source("prepared/plan.json", {"duties": duties, "assumptions": {"conditional_material": True}})
    prepared_reference = source("prepared/receipt.json", {"output_sha256": {"plan.json": prepared_plan["sha256"]}})
    geometry = {"length_mm": 10., "thickness_mm": 5.}
    geometry_reference = source("geometry.json", {"body-0": geometry})
    families = []
    for i in range(8):
        names = [duty["joint_id"] for j, duty in enumerate(duties) if j % 8 == i]
        timbers = sorted({body for j, duty in enumerate(duties) if j % 8 == i for body in duty["timber_sides"]})
        families.append({"id": f"family-{i}", "duty_ids": names, "timber_sides": timbers,
                         "nominal_screen_is_fracture_or_capacity_proof": False, "mirror_force_or_geometry_pass_transferred": False})
    baseline_states = [{"case_id": case, "gap_scale": gap, "accepted_force_field_exists": (case, gap)
                        not in {("a12-left", 0), ("k12-right", 0)}} for case in CASES for gap in (0, 1)]
    baseline_reference = source("frame/comparison.json", {"case_dispositions": baseline_states})
    frame_reference = source("frame/receipt.json", {"output_sha256": {"comparison.json": baseline_reference["sha256"]}})
    original_native_frame = frame_reference
    inputs_reference = source("action/inputs.json", {"dead_load_factor": 1.})
    action_reference = source("action/receipt.json", {"output_sha256": {"inputs.json": inputs_reference["sha256"]}})
    historical_action = action_reference
    eligibility = None
    if eligible:
        joint_update = source("new-frame/joint-update.json", {"schema": "joint_frame_scalar_seat_update/v1"})
        inputs = {"cases": list(CASES), "gap_scales": [0, 1], "preparation": "fixed/preparation",
                  "wood_reduction": "fixed/reduction", "dead_load_factor": 1., "proposal_ties_included": False,
                  "source_frame_sha256": frame_reference["sha256"], "joint_update_sha256": joint_update["sha256"]}
        new_inputs = source("new-frame/inputs.json", inputs)
        dispositions, accepted, frame_arrays = [], [], {}
        frame_outputs = {"inputs.json": new_inputs["sha256"], "joint-update.json": joint_update["sha256"]}
        for state in baseline_states:
            case, gap = state["case_id"], state["gap_scale"]
            tag = acceptance.state_tag((case, gap))
            item = {**state, "physical_release": False}
            if state["accepted_force_field_exists"]:
                item.update(status=ACCEPTED_STATE, response_tag=tag)
                accepted.append({"case_id": case, "gap_scale": gap,
                                 "audit": {"all_passed": True, "checks": {"equilibrium": True}}})
                frame_arrays.update({tag + suffix: shape for suffix, shape in
                    (("_force_n", (3192,)), ("_relative_motion_mm", (3192,)), ("_rigid_scaled_mm", (344,)),
                     ("_shaft_pose_mm", (20,)), ("_bearing", (8,)))})
            else:
                history = [{"bearing_footprints": [i for i in range(8) if mask & (1 << i)],
                    "solver": {"status": "Solved"}, "original_physical_law_audit": {
                        "all_passed": False, "checks": {"bearing_floor_branch": False}}} for mask in range(256)]
                exception = FLOOR_PREFIX + json.dumps(history)
                trace = source("new-frame/" + tag + "-stop.json", {"case_id": case, "gap_scale": gap,
                    "exception": exception, "accepted_force_field_exists": False, "physical_release": False})
                frame_outputs[tag + "-stop.json"] = trace["sha256"]
                item.update(status=FLOOR_STOP, physical_frame_failure_claim=False,
                    stop_evidence={"packet": "new-frame", "receipt_sha256": None, "trace_path": trace["path"],
                        "trace_sha256": trace["sha256"], "pointer": "exception"},
                    floor_search_summary=acceptance.floor_summary(exception))
            dispositions.append(item)
        new_baseline = {"schema": FRAME_SCHEMA, "status": FRAME_PARTIAL, "case_dispositions": dispositions,
            "states": accepted, "complete_requested_state_inventory": True,
            "complete_six_case_zero_and_nominal_scope": False, "complete_permanent_zero_and_nominal_scope": True,
            "analytical_branch": "working_washer_profile_with_explicit_member_replacements"}
        baseline_reference = source("new-frame/comparison.json", new_baseline)
        frame_outputs["comparison.json"] = baseline_reference["sha256"]
        frame_outputs["response.npz"] = sources["new-frame/response.npz"] = write_arrays(tmp_path / "new-frame/response.npz", frame_arrays)
        new_receipt = source("new-frame/receipt.json", {"status": FRAME_PARTIAL,
            "source_sha256": dict(sources), "output_sha256": frame_outputs})
        eligibility = {"receipt": new_receipt, "comparison": baseline_reference}
        frame_reference = new_receipt
        inventory, action_states = deepcopy(dispositions), []
        action_arrays = {name: (1,) for name in ("canonical_raw_row_available",
            "canonical_raw_row_to_kept_lumped_position", "old_kept_lumped_rows")}
        state_positions = {acceptance.state_key(state): i for i, state in enumerate(accepted)}
        for i, item in enumerate(inventory):
            key = acceptance.state_key(item)
            tag = acceptance.state_tag(key)
            item.update(state_tag=tag, finite_disposition_completed=True,
                source_disposition_record={**baseline_reference, "pointer": f"/case_dispositions/{i}"})
            if item["accepted_force_field_exists"]:
                record = {**baseline_reference, "pointer": f"/states/{state_positions[key]}"}
                item["source_state_record"] = record
                action_states.append({"case_id": key[0], "gap_scale": key[1], "state_tag": tag,
                    "source_state_record": record})
                action_arrays.update({tag + suffix: (1,) for suffix in
                    ("_raw_force_n", "_kept_lumped_relative_motion_mm", "_coupled_force_n")})
            else:
                item["physical_equilibrium_nonexistence_proven"] = False
        action = {"schema": ACTION_SCHEMA, "status": "COMPLETE_SAVED_COUPLED_ACTION_RECONCILIATION_NOT_RESISTANCE_QUALIFICATION",
            "source_response_status": FRAME_PARTIAL, "required_state_inventory": inventory, "states": action_states,
            "counts": {"required_states": 14, "accepted_states": 12, "finite_floor_search_dispositions": 2,
                "assessed_states": 14, "unassessed_states": 0, "unresolved_numerical_stops": 0, "rejected_force_fields_exported": 0},
            "finite_state_disposition_inventory_complete": True, "action_exports_complete_for_accepted_states": True,
            "completed_states": 12, "all14_required_states": False, "action_state_scope": "accepted_state_subset"}
        action_inputs = source("new-action/inputs.json", {"dead_load_factor": 1.})
        action_summary = source("new-action/summary.json", action)
        action_response = sources["new-action/source-row-response.npz"] = write_arrays(
            tmp_path / "new-action/source-row-response.npz", action_arrays)
        action_reference = source("new-action/receipt.json", {"status": action["status"],
            **{field: action[field] for field in ("required_state_inventory", "counts",
                "finite_state_disposition_inventory_complete", "action_state_scope", "action_exports_complete_for_accepted_states")},
            "source_sha256": dict(sources), "output_sha256": {"inputs.json": action_inputs["sha256"],
                "summary.json": action_summary["sha256"], "source-row-response.npz": action_response}})
        baseline_states = dispositions
    states = [{**state, "state_tag": state["case_id"] + ("_zero" if state["gap_scale"] == 0 else "_gap"),
               "source_baseline_disposition": {**baseline_reference, "pointer": f"/case_dispositions/{i}"},
               "baseline_accepted_force_field_exists": state["accepted_force_field_exists"],
               "changed_model_requires_fresh_disposition": True} for i, state in enumerate(baseline_states)]
    for state in states:
        state.pop("accepted_force_field_exists")
    if eligible:
        outside = []
        for state in states:
            key = acceptance.state_key(state)
            if state["baseline_accepted_force_field_exists"]:
                state["baseline_response_state_ref"] = {**baseline_reference, "pointer": f"/states/{state_positions[key]}"}
            else:
                outside.append({**state, "status": "OUTSIDE_ELIGIBLE_BASELINE_FORCE_FIELD_DOMAIN",
                    "unavailable_source_state_disposition": "OUTSIDE_ELIGIBLE_BASELINE_FORCE_FIELD_DOMAIN",
                    "unavailable_cracked_body_equilibrium_claim": False, "cracked_variant_infeasibility_claimed": False,
                    "fresh_variant_floor_search_required": False})
        states = [state for state in states if state["baseline_accepted_force_field_exists"]]
    contract = {"geometry_binding": {**geometry_reference, "pointer": "/body-0"},
                "geometry_sha256": hashlib.sha256(canonical(geometry).encode()).hexdigest(),
                "material_binding": {**prepared_plan, "pointer": "/assumptions"},
                "boundary_footprint_id": "frozen-physical-footprint-hypothesis", "coupling_method_id": "full-frame-replacement",
                "source_action_receipt": historical_action, "absolute_assembled_potential_claimed": False,
                "old_fixed_force_contact_upper_bound_transferred": False, "unmeasured_Gc_all_modes_n_per_mm": .1,
                "unmeasured_Ft90_mpa": 1.}
    variants, required = [], []
    for size in (20, 15):
        for rt in ("R=u,T=v", "R=v,T=-u"):
            roles = {}
            for phase in ("intact", "initial", "final"):
                identifier = f"operator-{len(variants)}"
                roles[phase] = identifier
                variants.append({"id": identifier, "body": "body-0", "path": path, "mesh_size_mm": size,
                    "RT_binding": rt, "configuration": phase,
                    "crack_interval_mm": None if phase == "intact" else path[phase + "_interval_mm"], **contract})
            for state in states:
                row = {"id": f"comparison-{len(required)}", "body": "body-0", "path": path, "axis": 1,
                       "plane_mm": 0., "mesh_size_mm": size, "RT_binding": rt, **state, **contract,
                       "operator_variants": dict(roles)}
                if eligible:
                    row["historical_port_action_receipt"] = row.pop("source_action_receipt")
                    row.update(baseline_eligibility_binding=eligibility, global_joint_update_binding=joint_update,
                               source_action_force_transfer=False)
                row["original_path_projection"] = {field: row[field] for field in
                    ("body", "path", "state_tag", "mesh_size_mm", "RT_binding")} if row["baseline_accepted_force_field_exists"] else None
                required.append(row)
    selection = {"schema": "splitting_representative_coupled_selection/v1", "numerical_scope": REPRESENTATIVE_SCOPE,
        "original_inventory_binding": old_reference, "prepared_binding": prepared_reference,
        "original_inventory_count": 37056, "original_unsampled_disposition": "UNASSESSED_OUTSIDE_REVISED_SCOPE",
        "original_inventory_completion_transferred": False, "required_state_dispositions": states,
        "family_manifest": {"families": families, "canonical_timber_names": [f"body-{i}" for i in range(44)]},
        "operator_variants": variants, "required_comparisons": required, "required_comparison_count": len(required),
        "native_operator_variant_budget": 12, "required_field_gates": sorted(acceptance.REPRESENTATIVE_FIELD_GATES)
            + ["actual_equilibrium", "saved_original_field"]}
    if eligible:
        operator_selection = source("original-selection.json", {"operator_variants": deepcopy(variants)})
        selection.update(baseline_eligibility_binding=eligibility, baseline_state_dispositions=baseline_states,
            operator_selection_binding=operator_selection, global_joint_update_binding=joint_update,
            outside_eligible_baseline_state_dispositions=outside,
            required_operator_state_disposition_count=12 * len(states),
            baseline_unavailable_dispositions_are_cracked_body_limits=False,
            repeated_baseline_floor_searches_per_crack_variant=False)
    selection_reference = source("selection.json", selection)
    body_field = field("body-field.npz", {"recovered_U_mm": (12,), "total_U_mm": (12,), "force_n": (12,),
        "all_node_residual_n": (12,), "nodes_mm": (4, 3), "elements": (1, 20)})
    frame_field = field("frame-field.npz", {"frame_force_n": (3192,), "frame_relative_motion_mm": (3192,),
        "frame_rigid_scaled_mm": (344,), "frame_bearing": (8,)})
    operator_field = field("operators.npz", {"H": (1, 1), "e": (1, 12), "L": (12, 12), "D": (1, 6), "W": (6, 12),
        "nodes_mm": (4, 3), "elements": (1, 20), "active_port_rows": (1,), "physical_R": (12, 6),
        "external_F_n": (12, 12), "U_F_mm": (12, 12), "U_B_mm": (12, 1), "port_B_indptr": (2,),
        "port_B_shape": (2,), "port_B_data": (1,), "port_B_indices": (1,), "original_scalar_gauges": (6,),
        "projected_rhs_n": (12, 13), "projected_residual_n": (12, 13)})
    native_B = source("native-source/source-body-B.npz", {"frozen_native_B": True})
    native_F = source("native-source/source-body.npz", {"frozen_native_F_R_D_W": True})
    native_source = source("native-source/receipt.json", {"output_sha256": {
        "source-body-B.npz": native_B["sha256"], "source-body.npz": native_F["sha256"]}})
    current_action = {"receipt": action_reference["path"], "sha256": action_reference["sha256"]}
    external_contract = output("external-contract.json", {"schema": "splitting_coupled_external_basis_contract/v1",
        "source_frame_binding": frame_reference, "native_source_body_binding": native_source,
        "original_native_frame_binding": original_native_frame,
        "baseline_eligibility_binding": eligibility, "active_action_binding": current_action, "dead_load_factor": 1.,
        "original_complete_twelve_column_F_W_retained": True, "same_source_external_basis_between_crack_phases": True,
        "same_interface_reaction_between_crack_phases_required": False})

    def mapping_audits():
        def column(i, normal=False):
            return {"column": i, "affine_rank": 4, "scaled_force_first_moment_residual": 0.,
                "first_moment_scale_mm": 100., "signed_bilateral_tractions_permitted": not normal,
                "recovered_contact_pressure_or_preload_claimed": False,
                "normal_only_nonnegative_traction_audit": {"status": "Solved", "minimum_scalar_weight": 0.,
                    "nonnegative_weight_tolerance": 1e-10, "maximum_scalar_equality_residual": 0.} if normal else None}
        return ({"full_native_affine_targets_retained": True, "physical_side_ownership_retained": True,
            "kinematic_tie_or_crack_stitch_added": False, "columns": [column(i, normal=i == 2) for i in range(3)]},
            {"original_full_body_load_basis_affine_targets_retained": True, "contact_adhesion_or_crack_stitch_credited": False,
             "signed_consistent_external_body_forces_permitted": True, "columns": [column(i) for i in range(12)]})

    port_contracts = {}
    for i in range(0, len(variants), 3):
        group = variants[i:i+3]
        group_ref = output(f"operator-group-{i}.json", {"schema": "splitting_coupled_body_operator_group/v1",
            "status": "PASS_ACTUAL_COUPLED_BODY_OPERATOR_GROUP", "native_operator_count": 3,
            "operators": [{"variant": variant, "operator_ref": operator_field,
                           "physical_audit": {"all_passed": True, "checks": {"original_field": True}}} for variant in group]})
        mappings = []
        for variant in group:
            port, external = mapping_audits()
            mappings.append(output(variant["id"] + "-mapping.json", {
                "variant": variant, "port_mapping": port, "external_mapping": external}))
        port_contracts[group[0]["id"]] = output(f"port-contract-{i}.json", {
            "schema": "splitting_coupled_physical_footprint_contract/v1", "geometry_sha256": contract["geometry_sha256"],
            "working_joint_update_binding": joint_update if eligible else None,
            "native_source_B_authority": native_B, "native_source_body_basis": native_F,
            "original_force_and_all_nine_first_moments_preserved": True, "retained_physical_source_side_only": True,
            "contact_normal_scalar_weights_nonnegative": True, "crack_seam_nodes_excluded_without_stitching": True,
            "bilateral_bolt_and_consistent_external_body_forces_are_declared_separately": True,
            "actual_operator_mapping_records": mappings, "operator_group_binding": group_ref})
    records, operator_states = [], []
    for identity in required:
        port_contract = port_contracts[identity["operator_variants"]["intact"]]
        row = {"id": identity["id"], "identity": identity, "added_sound_area_mm2": 2., "signed_G_n_per_mm": 1.,
               "Gc_n_per_mm": .1, "conditional_energy_reference_index": 10., "upper_reference": None,
               "intact_sampled_sigma90_mpa": 2., "Ft90_mpa": 1., "conditional_initiation_reference_index": 2.}
        c = [0.] * 12
        column = 0 if identity["case_id"] == "dead-only" else 2 * CASES.index(identity["case_id"])
        c[column] = 1.
        if identity["case_id"] != "dead-only":
            c[column + 1] = 1.
        for phase, (port, connector, external, area) in {"intact": (1., 1., 3., 0.),
                "initial": (2., 3., 7., 1.), "final": (4., 1., 9., 3.)}.items():
            energy = {"potential_nmm": port + connector - external, "body_elastic_energy_nmm": port,
                "connector_energy_nmm": connector, "external_work_nmm": external, "body_load_chi_nmm": 0.,
                "interface_body_load_cross_work_nmm": 0., "interface_elastic_energy_nmm": port,
                "rigid_external_work_nmm": external, "complementary_energy_nmm": external - port - connector,
                "primal_complementary_identity_error_nmm": 0., "external_coefficients": c,
                "energy_constant_scope": acceptance.PARTIAL_ENERGY_CONSTANT,
                "unchanged_constant_token": frame_reference["sha256"], "external_wrench_sha256": "a" * 64,
                "joint_law_sha256": "b" * 64, "unchanged_body_load_chi_nmm": None,
                "body_elastic_energy_unchanged_offset_nmm": None, "external_work_unchanged_offset_nmm": None}
            audit = {"all_passed": True, "checks": {gate: True for gate in selection["required_field_gates"]},
                     "original_frame_audit": {"all_passed": True, "checks": {"spring_law": True}},
                     "actual_scalar_residuals": {"equilibrium": 0.}, "tolerances": {"equilibrium": 1e-8}}
            reaction = {"case_id": identity["case_id"], "gap_scale": identity["gap_scale"],
                        "operator_variant_id": identity["operator_variants"][phase],
                        "accepted_force_field_exists": True, "physical_audit": audit, "energy": energy,
                        "retained_reaction_field": frame_field}
            if eligible:
                reaction["joint_update_binding"] = joint_update
            reaction_reference = output(identity["id"] + "-" + phase + "-reaction.json", reaction)
            checkpoint = {"identity": identity, "phase": phase, "operator_variant_id": identity["operator_variants"][phase],
                "physical_audit": audit, "retained_field": body_field, "operator_ref": operator_field,
                "reaction_ref": reaction_reference, "energy": energy, "actual_crack_area_mm2": area,
                "absolute_assembled_potential_claimed": False, "source_frame_receipt_sha256": frame_reference["sha256"],
                "sampled_sigma90_mpa": 2.,
                "external_load_contract_ref": external_contract, "external_load_contract_sha256": external_contract["sha256"],
                "port_footprint_contract_ref": port_contract, "port_footprint_contract_sha256": port_contract["sha256"]}
            row[phase + "_checkpoint"] = output(identity["id"] + "-" + phase + ".json", checkpoint)
            operator_states.append({"operator_variant_id": identity["operator_variants"][phase],
                "case_id": identity["case_id"], "gap_scale": identity["gap_scale"], "status": ACCEPTED_STATE,
                "accepted_force_field_exists": True, "response_ref": reaction_reference,
                "checkpoint_ref": row[phase + "_checkpoint"]})
        records.append(row)
    coupon_reference = output("known-answer.json", {"schema": "joint_frame_member_replacement_known_answer/v1",
        "status": "PASS_ASSEMBLED_REPLACEMENT_ENERGY_KNOWN_ANSWER", "body_remove_reinsert_exact": True,
        "unchanged_rest_body_chi_cancellation": True, "G_n_per_mm": .185142857142857,
        "analytic_G_n_per_mm": .185142857142857, "cross_term_body_load_chi_nmm": 26.125,
        "explicit_body_load_potential_nmm": -14.82})
    mapping_field = field("mapping-known-answer.npz", {name: (1,) for name in ("nodes_mm", "elements", "original_raw_rhs",
        "projected_rhs", "recovered_U_mm", "monolithic_U_mm", "residual_n", "physical_R", "port_B", "external_F",
        "H", "e", "L", "D", "W")})
    proof_groups = []
    for rt in ("R=u,T=v", "R=v,T=-u"):
        proof_operators = []
        for phase in ("intact", "initial", "final"):
            port, external = mapping_audits()
            proof_operators.append({"configuration": phase, "complete_native_force_and_nine_first_moments_retained": True,
                "operator_audit": {"all_passed": True, "checks": {"quotient": True}},
                "solution_audit": {"all_passed": True, "checks": {"recovery": True}},
                "relative_operator_errors": {name: 0. for name in ("H", "e", "L", "D", "W")},
                "relative_U_error": 0., "rigid_virtual_work_error_nmm": 0., "general_affine_virtual_work_error_nmm": 0.,
                "physical_port_mapping_audit": port, "external_body_load_mapping_audit": external, "field": mapping_field})
        proof_groups.append({"RT_binding": rt, "operators": proof_operators})
    mapping_reference = output("mapping-known-answer.json", {"schema": "splitting_coupled_interface_operator_known_answer/v1",
        "status": "PASS_SOURCE_SIDE_MAPPING_AND_LOCALIZED_OPERATOR_KNOWN_ANSWER", "configurations": 6,
        "external_load_basis_columns": 12, "source_moment_and_rigid_virtual_work_retained": True,
        "same_physical_footprints_across_intact_initial_final": True, "normal_contact_nonnegative_scalar_traction_assessed": True,
        "unbalanced_unit_columns_projected_only_for_elastic_inverse": True, "full_assembly_energy_known_answer_replaced": False,
        "project_body_domain_or_resource_feasibility_transferred": False, "physical_or_complete_joint_acceptance": False,
        "records": proof_groups})
    paired = {"source_sha256": dict(sources), "output_sha256": outputs}
    paired_reference = source("native/receipt.json", paired)
    result = {"schema": REPRESENTATIVE_SCHEMA, "status": REPRESENTATIVE_STATUS,
        "representative_study_complete": True, "selected_comparison_inventory_complete": True,
        "original_inventory_completed": False, "full_splitting_qualification": False,
        "historical_force_basis_transferred": False, "selection_binding": selection_reference,
        "active_action_binding": {"receipt": action_reference["path"], "sha256": action_reference["sha256"]},
        "source_frame_binding": frame_reference, "artifact_receipts": [paired_reference], "records": records,
        "original_native_frame_binding": original_native_frame,
        "operator_state_dispositions": operator_states,
        "finite_dispositions": [], "pending_comparison_ids": [], "assembled_known_answer": coupon_reference,
        "interface_mapping_known_answer": mapping_reference,
        "splitting_workstream_complete": False}
    receipt = {"source_sha256": sources, "output_sha256": {}}
    entry = {"status": REPRESENTATIVE_COMPLETE, "numerical_scope": REPRESENTATIVE_SCOPE}

    def refresh():
        for name, shapes in arrays.items():
            outputs[name] = write_arrays(native / name, shapes)
        def update_references(value):
            if isinstance(value, dict):
                path_value = value.get("path", "")
                name = path_value.removeprefix("native/") if isinstance(path_value, str) else ""
                if isinstance(path_value, str) and path_value.startswith("native/") and name in outputs and "sha256" in value:
                    value["sha256"] = outputs[name]
                for child in value.values():
                    update_references(child)
            elif isinstance(value, list):
                for child in value:
                    update_references(child)
        for name, value in documents.items():
            update_references(value)
            outputs[name] = write_json(native / name, value)
        update_references(result)
        selection_reference["sha256"] = sources["selection.json"] = write_json(tmp_path / "selection.json", selection)
        paired["source_sha256"] = {name: digest for name, digest in sources.items() if name != "native/receipt.json"}
        paired_reference["sha256"] = sources["native/receipt.json"] = write_json(native / "receipt.json", paired)

    def validate():
        representative_scope_check(tmp_path, entry, result, packet, receipt, sources, {}, {})

    return result, selection, documents, arrays, outputs, refresh, validate


@pytest.mark.parametrize("fault", ["missing", "duplicate", "pending", "old_complete", "unsampled_pass", "projection",
    "missing_grid", "missing_state", "rejected_force", "failed_audit", "missing_gate", "no_body_field",
    "old_coordinates", "unowned_field", "energy", "chi", "G", "area", "changed_constant", "changed_external",
    "changed_port_contract", "changed_joint_law", "case_coefficients", "known_answer", "family_overclaim",
    "missing_operator_state", "duplicate_operator_state", "ordinary_operator_stop", "empty_body_field", "wrong_element",
    "missing_operator_basis", "wrong_operator_order", "residual", "original_frame_law", "weakened_gates",
    "stress", "stress_reference", "initiation_index", "mapping_coupon", "mapping_force_moments", "mapping_normal",
    "mapping_field", "external_basis_contract", "physical_footprint_contract", "actual_mapping", "missing_mapping_phase"])
def test_representative_coupled_scope_rejects_false_selected_completion(tmp_path, monkeypatch, fault):
    result, selection, documents, arrays, outputs, refresh, validate = representative_fixture(tmp_path, monkeypatch)
    validate()
    row = result["records"][0]
    checkpoint = documents[row["final_checkpoint"]["path"].removeprefix("native/")]
    reaction = documents[checkpoint["reaction_ref"]["path"].removeprefix("native/")]
    if fault == "missing":
        result["records"].pop()
    elif fault == "duplicate":
        result["records"].append(deepcopy(row))
    elif fault == "pending":
        result["pending_comparison_ids"] = [row["id"]]
    elif fault == "old_complete":
        result["original_inventory_completed"] = True
    elif fault == "unsampled_pass":
        selection["original_unsampled_disposition"] = "PASS_UNSAMPLED"
    elif fault == "projection":
        row["identity"]["original_path_projection"]["path"] = {**row["identity"]["path"], "plane_mm": 1.}
    elif fault == "missing_grid":
        selection["required_comparisons"] = [r for r in selection["required_comparisons"] if r["mesh_size_mm"] != 15]
        selection["required_comparison_count"] = len(selection["required_comparisons"])
        selection["operator_variants"] = [v for v in selection["operator_variants"] if v["mesh_size_mm"] != 15]
        selection["native_operator_variant_budget"] = len(selection["operator_variants"])
        result["records"] = [r for r in result["records"] if r["identity"]["mesh_size_mm"] != 15]
    elif fault == "missing_state":
        selection["required_comparisons"].pop()
        selection["required_comparison_count"] -= 1
        result["records"].pop()
    elif fault == "rejected_force":
        reaction["accepted_force_field_exists"] = False
    elif fault == "failed_audit":
        checkpoint["physical_audit"]["checks"]["actual_equilibrium"] = False
    elif fault == "missing_gate":
        checkpoint["physical_audit"]["checks"].pop("saved_original_field")
    elif fault == "no_body_field":
        arrays["body-field.npz"].pop("total_U_mm")
    elif fault == "empty_body_field":
        arrays["body-field.npz"]["nodes_mm"] = (0, 3)
    elif fault == "wrong_element":
        arrays["body-field.npz"]["elements"] = (1, 8)
    elif fault == "missing_operator_basis":
        arrays["operators.npz"].pop("U_B_mm")
    elif fault == "wrong_operator_order":
        arrays["operators.npz"]["H"] = (2, 2)
    elif fault == "residual":
        checkpoint["physical_audit"]["actual_scalar_residuals"]["equilibrium"] = 1.
    elif fault == "original_frame_law":
        checkpoint["physical_audit"]["original_frame_audit"]["checks"]["spring_law"] = False
    elif fault == "weakened_gates":
        selection["required_field_gates"] = ["actual_equilibrium"]
    elif fault == "old_coordinates":
        arrays["frame-field.npz"]["frame_rigid_scaled_mm"] = (300,)
    elif fault == "unowned_field":
        outputs.pop("body-field.npz")
        arrays.pop("body-field.npz")
    elif fault in {"energy", "chi", "changed_constant", "changed_external", "changed_joint_law", "case_coefficients"}:
        field = {"energy": "potential_nmm", "chi": "body_load_chi_nmm", "changed_constant": "unchanged_constant_token",
                 "changed_external": "external_wrench_sha256", "changed_joint_law": "joint_law_sha256",
                 "case_coefficients": "external_coefficients"}[fault]
        checkpoint["energy"][field] = [0.] * 12 if fault == "case_coefficients" else "c" * 64 if "changed" in fault else 1.
    elif fault == "G":
        row["signed_G_n_per_mm"] = 2.
        row["conditional_energy_reference_index"] = 20.
    elif fault == "area":
        row["added_sound_area_mm2"] = 4.
        row["signed_G_n_per_mm"] = .5
        row["conditional_energy_reference_index"] = 5.
    elif fault == "changed_port_contract":
        alternate = {"path": "native/external-contract.json", "sha256": outputs["external-contract.json"]}
        checkpoint["port_footprint_contract_ref"] = alternate
        checkpoint["port_footprint_contract_sha256"] = alternate["sha256"]
    elif fault == "known_answer":
        documents["known-answer.json"]["cross_term_body_load_chi_nmm"] = 0.
    elif fault == "missing_operator_state":
        result["operator_state_dispositions"].pop()
    elif fault == "duplicate_operator_state":
        result["operator_state_dispositions"][-1] = deepcopy(result["operator_state_dispositions"][0])
    elif fault == "ordinary_operator_stop":
        result["operator_state_dispositions"][0]["status"] = "STOP_TIMEOUT_PENDING_NUMERICAL_FIELD"
    elif fault == "stress":
        row["intact_sampled_sigma90_mpa"] = 3.
        row["conditional_initiation_reference_index"] = 3.
    elif fault == "stress_reference":
        row["Ft90_mpa"] = 2.
        row["conditional_initiation_reference_index"] = 1.
    elif fault == "initiation_index":
        row["conditional_initiation_reference_index"] = 1.
    elif fault == "mapping_coupon":
        documents["mapping-known-answer.json"]["records"].pop()
    elif fault == "mapping_force_moments":
        documents["mapping-known-answer.json"]["records"][0]["operators"][0]["general_affine_virtual_work_error_nmm"] = 1.
    elif fault == "mapping_normal":
        documents["mapping-known-answer.json"]["records"][0]["operators"][0]["physical_port_mapping_audit"]["columns"][2][
            "normal_only_nonnegative_traction_audit"]["minimum_scalar_weight"] = -.1
    elif fault == "mapping_field":
        arrays["mapping-known-answer.npz"].pop("monolithic_U_mm")
    elif fault == "external_basis_contract":
        documents["external-contract.json"]["same_source_external_basis_between_crack_phases"] = False
    elif fault == "physical_footprint_contract":
        documents["port-contract-0.json"]["crack_seam_nodes_excluded_without_stitching"] = False
    elif fault == "actual_mapping":
        documents["operator-0-mapping.json"]["port_mapping"]["full_native_affine_targets_retained"] = False
    elif fault == "missing_mapping_phase":
        documents["port-contract-0.json"]["actual_operator_mapping_records"].pop()
    else:
        result["splitting_workstream_complete"] = True
        result["family_coverage"] = []
    refresh()
    with pytest.raises(ValueError):
        validate()


def test_assembled_energy_retains_full_selected_load_cross_terms():
    c = [1., 2.] + [0.] * 10
    L = [0.] * 144
    L[0], L[1], L[12], L[13] = 2.25, 3.5, 3.5, 9.
    energy = {"potential_nmm": -82.125, "body_elastic_energy_nmm": 25.125,
        "connector_energy_nmm": 3., "external_work_nmm": 110.25, "body_load_chi_nmm": 26.125,
        "interface_body_load_cross_work_nmm": 2., "interface_elastic_energy_nmm": 1.,
        "rigid_external_work_nmm": 60., "complementary_energy_nmm": 56.,
        "primal_complementary_identity_error_nmm": 0., "external_coefficients": c,
        "energy_constant_scope": acceptance.PARTIAL_ENERGY_CONSTANT, "unchanged_constant_token": "same-rest",
        "external_wrench_sha256": "a" * 64, "joint_law_sha256": "b" * 64,
        "unchanged_body_load_chi_nmm": None, "body_elastic_energy_unchanged_offset_nmm": None,
        "external_work_unchanged_offset_nmm": None}
    assembled_energy_check(energy, L)
    L[1] = L[12] = 0.
    with pytest.raises(ValueError, match="cross terms"):
        assembled_energy_check(energy, L)


@pytest.mark.parametrize("fault", ["missing_eligible", "missing_outside", "false_crack_failure", "old_action",
    "wrong_baseline_pointer", "wrong_response_pointer", "unavailable_operator_export", "old_force_transfer",
    "changed_native_operator", "wrong_joint_update", "wrong_operator_census"])
def test_representative_eligibility_requires_current_audited_baseline_domain(tmp_path, monkeypatch, fault):
    result, selection, _documents, _arrays, _outputs, refresh, validate = representative_fixture(
        tmp_path, monkeypatch, eligible=True)
    assert len(selection["required_comparisons"]) == 48
    assert len(result["operator_state_dispositions"]) == 144
    validate()
    if fault == "missing_eligible":
        selection["required_state_dispositions"].pop()
    elif fault == "missing_outside":
        selection["outside_eligible_baseline_state_dispositions"].pop()
    elif fault == "false_crack_failure":
        selection["outside_eligible_baseline_state_dispositions"][0]["cracked_variant_infeasibility_claimed"] = True
    elif fault == "old_action":
        reference = selection["required_comparisons"][0]["historical_port_action_receipt"]
        result["active_action_binding"] = {"receipt": reference["path"], "sha256": reference["sha256"]}
    elif fault == "wrong_baseline_pointer":
        selection["required_state_dispositions"][0]["source_baseline_disposition"]["pointer"] = "/case_dispositions/4"
    elif fault == "wrong_response_pointer":
        selection["required_state_dispositions"][0]["baseline_response_state_ref"]["pointer"] = "/states/1"
    elif fault == "unavailable_operator_export":
        extra = deepcopy(result["operator_state_dispositions"][0])
        extra.update(case_id="a12-left", gap_scale=0)
        result["operator_state_dispositions"].append(extra)
    elif fault == "old_force_transfer":
        selection["required_comparisons"][0]["source_action_force_transfer"] = True
    elif fault == "changed_native_operator":
        selection["operator_variants"][0]["coupling_method_id"] = "altered-native-authority"
    elif fault == "wrong_joint_update":
        selection["global_joint_update_binding"] = selection["original_inventory_binding"]
    else:
        selection["required_operator_state_disposition_count"] = 168
    refresh()
    with pytest.raises(ValueError):
        validate()


@pytest.mark.parametrize("fault", ["rejected_accepted_phase", "force_export", "missing_mask", "physical_failure"])
def test_representative_finite_floor_disposition_preserves_all_accepted_phase_audits(tmp_path, monkeypatch, fault):
    result, _selection, documents, _arrays, outputs, refresh, validate = representative_fixture(
        tmp_path, monkeypatch, eligible=True)
    row = result["records"].pop(0)
    identity = row["identity"]
    final_checkpoint = documents[row["final_checkpoint"]["path"].removeprefix("native/")]
    history = [{"bearing_footprints": [i for i in range(8) if mask & (1 << i)], "solver": {"status": "Solved"},
        "original_physical_law_audit": {"all_passed": False, "checks": {"bearing_floor_branch": False}}}
        for mask in range(256)]
    exception = FLOOR_PREFIX + json.dumps(history)
    diagnostic = {"identity": identity, "status": FLOOR_STOP, "operator_variant_id": identity["operator_variants"]["final"],
        "source_frame_receipt_sha256": final_checkpoint["source_frame_receipt_sha256"],
        "operator_ref": final_checkpoint["operator_ref"], "accepted_force_field_exists": False,
        "physical_frame_failure_claim": False, "physical_equilibrium_nonexistence_proven": False,
        "changed_model_requires_fresh_disposition": True, "exception": exception,
        "floor_search_summary": acceptance.floor_summary(exception)}
    documents["finite-stop.json"] = diagnostic
    outputs["finite-stop.json"] = write_json(tmp_path / "native/finite-stop.json", diagnostic)
    reference = {"path": "native/finite-stop.json", "sha256": outputs["finite-stop.json"]}
    disposition = next(item for item in result["operator_state_dispositions"]
        if item["operator_variant_id"] == diagnostic["operator_variant_id"]
        and acceptance.state_key(item) == acceptance.state_key(identity))
    disposition.pop("response_ref")
    disposition.pop("checkpoint_ref")
    disposition.update(status=FLOOR_STOP, accepted_force_field_exists=False, diagnostic_ref=reference)
    result["finite_dispositions"] = [{"id": row["id"], "identity": identity, "diagnostic_ref": reference,
        "forces_exported": False, "strength_pass_claimed": False}]
    refresh()
    validate()
    if fault == "rejected_accepted_phase":
        checkpoint = documents[row["intact_checkpoint"]["path"].removeprefix("native/")]
        documents[checkpoint["reaction_ref"]["path"].removeprefix("native/")]["accepted_force_field_exists"] = False
    elif fault == "force_export":
        diagnostic["retained_reaction_field"] = final_checkpoint["retained_field"]
    elif fault == "missing_mask":
        diagnostic["exception"] = FLOOR_PREFIX + json.dumps(history[:-1])
    else:
        diagnostic["physical_equilibrium_nonexistence_proven"] = True
    refresh()
    with pytest.raises(ValueError):
        validate()


@pytest.mark.parametrize("field", ["washer_joint_update", "joint_update_sha256", "source_frame_sha256",
                                  "energy_constant_scope", "unchanged_constant_token"])
def test_profile_floor_stop_cannot_transfer_across_changed_law_or_energy_source(tmp_path, field):
    previous = tmp_path / "previous"
    current = tmp_path / "current"
    previous.mkdir()
    current.mkdir()
    inputs = {"preparation": "fixed/preparation", "wood_reduction": "fixed/reduction", "dead_load_factor": 1.,
        "proposal_ties_included": False, "washer_joint_update": {"row": 1, "k": 100.}, "joint_update_sha256": "a" * 64,
        "source_frame_sha256": "b" * 64, "energy_constant_scope": acceptance.PARTIAL_ENERGY_CONSTANT,
        "unchanged_constant_token": "b" * 64}
    history = [{"bearing_footprints": [i for i in range(8) if mask & (1 << i)], "solver": {"status": "Solved"},
        "original_physical_law_audit": {"all_passed": False, "checks": {"bearing_floor_branch": False}}}
        for mask in range(256)]
    exception = FLOOR_PREFIX + json.dumps(history)
    trace = {"case_id": "a12-rear", "gap_scale": 0., "exception": exception,
        "accepted_force_field_exists": False, "physical_release": False}
    trace_sha = write_json(previous / "trace.json", trace)
    receipt = {"status": "STOP_COUPLED_FRAME_NUMERICAL_QUALIFICATION_OPEN", "output_sha256": {
        "trace.json": trace_sha, "inputs.json": write_json(previous / "inputs.json", inputs)}}
    receipt_sha = write_json(previous / "receipt.json", receipt)
    item = {"case_id": "a12-rear", "gap_scale": 0., "status": FLOOR_STOP, "accepted_force_field_exists": False,
        "physical_frame_failure_claim": False, "stop_evidence": {"packet": "previous", "receipt_sha256": receipt_sha,
            "trace_path": "previous/trace.json", "trace_sha256": trace_sha, "pointer": "exception"},
        "floor_search_summary": acceptance.floor_summary(exception)}
    sources = {"previous/receipt.json": receipt_sha}
    acceptance.stop_check(tmp_path, item, current, {}, inputs, sources, {}, {})
    inputs[field] = {"row": 1, "k": 200.} if field == "washer_joint_update" else "changed"
    with pytest.raises(ValueError, match="different washer law or body-energy source"):
        acceptance.stop_check(tmp_path, item, current, {}, inputs, sources, {}, {})


@pytest.mark.parametrize("fault", ["prepared", "plural_stop", "mutated_output", "changed_definition", "unconfirmed_complete", "redirect_hash",
                                  "normal_only_member", "member_endpoint_partition", "historical_splitting_completion"])
def test_receipt_bound_extension_rejects_false_completion(tmp_path, fault):
    index, extension, entry, result, receipt = extension_fixture(tmp_path)
    packet = tmp_path / "packet"
    if fault in {"normal_only_member", "member_endpoint_partition"}:
        entry["numerical_scope"] = "finished_longitudinal_and_shear"
        result.update(schema=MEMBER_SCHEMA,elastic_whole_domain_shear_executed=True,
            comparison={"named_original_basis":{"target_cuts":3,"finite_normal_cuts":1,"finite_elastic_shear_cuts":1,
                "resolved_one_sided_terminal_count":2,"one_sided_zero_limits":1,"one_sided_divergent_limits":1,
                "coupled_ligament_input_count":0,"unresolved_endpoint_input_count":0}})
        entry["result_sha256"] = receipt["output_sha256"]["result.json"] = write_json(packet / "result.json", result)
        entry["receipt_sha256"] = write_json(packet / "receipt.json", receipt)
        write_json(tmp_path / "index.json", index)
    assert check("index.json", tmp_path)["result_packets"] == 1

    if fault in {"prepared", "plural_stop"}:
        # All hashes/status metadata agree: the completion classification is the lie.
        result["status"] = entry["result_status"] = receipt["status"] = (
            "PREPARED_NOT_NUMERICALLY_EXECUTED" if fault == "prepared" else "COMPLETED_WITH_UNQUALIFIED_STOPS")
        entry["result_sha256"] = receipt["output_sha256"]["result.json"] = write_json(packet / "result.json", result)
        entry["receipt_sha256"] = write_json(packet / "receipt.json", receipt)
    elif fault == "mutated_output":
        (packet / "result.json").write_text("mutated numerical output")
    elif fault == "changed_definition":
        index["obligations"][0]["frozen_definition"]["note"] = "redefined requirement"
    elif fault == "redirect_hash":
        index["maintained_source_resolution"]["sources/0.txt"]["sha256"] = "0"*64
    elif fault in {"normal_only_member", "member_endpoint_partition"}:
        if fault == "normal_only_member":
            result["elastic_whole_domain_shear_executed"] = False
        else:
            result["comparison"]["named_original_basis"]["one_sided_divergent_limits"] = 0
        entry["result_sha256"] = receipt["output_sha256"]["result.json"] = write_json(packet / "result.json", result)
        entry["receipt_sha256"] = write_json(packet / "receipt.json", receipt)
    else:
        extension["status"] = "complete"
        if fault == "historical_splitting_completion":
            extension["parent_final_validation"] = {"confirmed": True}
            extension["workstreams"] = ["three-dimensional conditional splitting resistance"]
            extension["workstream_results"] = {extension["workstreams"][0]: ["study"]}
    write_json(tmp_path / "index.json", index)
    with pytest.raises(ValueError):
        check("index.json", tmp_path)


@pytest.mark.parametrize("fault", ["queued", "missing", "duplicate", "false_exclusion", "queued_exclusion", "wrong_load",
                                  "wrong_energy_index", "wrong_action_record", "omitted_free_couple",
                                  "altered_area", "altered_stress", "altered_threshold", "omitted_body",
                                  "deleted_retained_field", "mutated_body_only_source"])
def test_active_splitting_requires_source_bound_finished_workload(tmp_path, fault):
    """Coherent hashes cannot promote queued rows or a different physical state."""
    sources, outputs = {}, {}

    def source(name, value):
        digest = write_json(tmp_path / name, value)
        sources[name] = digest
        return {"path": name, "sha256": digest}

    state = {"case_id": "a12-rear", "gap_scale": 0., "audit": {"all_passed": True, "checks": {"equilibrium": True}}}
    state_reference = {**source("frame.json", {"states": [state]}), "pointer": "/states/0"}
    inventory = []
    for case in CASES:
        for gap in (0, 1):
            stopped = (case, gap) in {("a12-left", 0), ("k12-right", 0)}
            inventory.append({"case_id": case, "gap_scale": gap, "state_tag": case + ("_zero" if gap == 0 else "_gap"),
                              "status": FLOOR_STOP if stopped else ACCEPTED_STATE,
                              "accepted_force_field_exists": not stopped, "source_state_record": state_reference})
    action = {"body": "cleat", "state_tag": "a12-rear_zero", "case_id": "a12-rear", "gap_scale": 0.,
              "source_state_record": state_reference,
              "actions": [{"force_n": [1., 2., 3.], "free_moment_nmm": [4., 5., 6.], "source_force_available": True}]}
    action_file = tmp_path / "action/body-actions.jsonl.gz"
    action_file.parent.mkdir()

    def write_actions():
        with gzip.open(action_file, "wt", encoding="utf-8") as stream:
            stream.write(canonical(action) + "\n")
        digest = hashlib.sha256(action_file.read_bytes()).hexdigest()
        sources["action/body-actions.jsonl.gz"] = digest
        return digest

    actions_sha = write_actions()
    action_summary = {"schema": ACTION_SCHEMA, "required_state_inventory": inventory, "timber_members": 44}
    summary_sha = write_json(tmp_path / "action/summary.json", action_summary)
    action_receipt = {"output_sha256": {"summary.json": summary_sha, "body-actions.jsonl.gz": actions_sha}}
    action_binding = source("action/receipt.json", action_receipt)
    path = {"id": "end/1/low", "axis": 1, "plane_mm": 0.,
            "initial_interval_mm": [0., 5.], "final_interval_mm": [0., 10.]}
    canonical_bodies = ["cleat", *("timber" + str(i) for i in range(1, 44))]
    prepared_plan = {"current_timber_count": 44, "source_action_receipt_sha256": action_binding["sha256"],
                     "required_state_inventory": inventory, "duties": [{"timber_sides": canonical_bodies}],
                     "assumptions": {"Ft90_mpa": 1., "Gc_all_modes_n_per_mm": 2.}}
    plan_reference = source("prepared/plan.json", prepared_plan)
    geometry_reference = source("prepared/geometry.json", {body: {} for body in canonical_bodies})
    prepared_receipt = {"output_sha256": {"plan.json": plan_reference["sha256"], "geometry.json": geometry_reference["sha256"]}}
    prepared_reference = source("prepared/receipt.json", prepared_receipt)
    obligation_inventory = {"records": [{"body": body, "finite_paths": [path], "mesh_sizes_mm": [20, 15],
                                          "RT_bindings": ["R=u,T=v", "R=v,T=-u"]} for body in canonical_bodies]}
    obligation_reference = source("obligations.json", obligation_inventory)
    identity = {"body": "cleat", "state_tag": "a12-rear_zero", "path_id": path["id"], "axis": 1, "plane_mm": 0.,
                "RT_binding": "R=u,T=v", "mesh_size_mm": 15., "path": path}
    excluded_rows = []
    for body in canonical_bodies:
        for item in inventory:
            if item["status"] != ACCEPTED_STATE:
                continue
            for grid in (20, 15):
                for binding in ("R=u,T=v", "R=v,T=-u"):
                    excluded = {**deepcopy(identity), "body": body, "state_tag": item["state_tag"],
                                "mesh_size_mm": grid, "RT_binding": binding}
                    if excluded != identity:
                        excluded_rows.append(excluded)
    method_records = [{**deepcopy(row), "status": "EXCLUDED_METHOD_LIMIT"} for row in excluded_rows]
    method_reference = source("method-limit.json", {"rows": method_records})
    for i, excluded in enumerate(excluded_rows):
        excluded["method_limit"] = {**method_reference, "pointer": "/rows/" + str(i)}
    workload = {"required_rows": [deepcopy(identity)], "excluded_rows": excluded_rows,
                "prepared_binding": {"receipt": prepared_reference["path"], "sha256": prepared_reference["sha256"]},
                "obligation_inventory_binding": obligation_reference}
    workload_reference = source("workload.json", workload)
    load_hash = "1" * 64
    checkpoints = {}
    for name, energy, area in (("intact", 1., 0.), ("initial", 2., 5.), ("final", 4., 7.)):
        field_name = name + "_field.npz"
        field_path = tmp_path / "body" / field_name
        field_path.parent.mkdir(exist_ok=True)
        with zipfile.ZipFile(field_path, "w") as archive:
            archive.writestr("field.npy", b"synthetic retained field bytes; no mechanics")
        field_sha = hashlib.sha256(field_path.read_bytes()).hexdigest()
        outputs[field_name] = field_sha
        checkpoint = {"source_state_keys": [["active_coupled", "a12-rear_zero"]],
                      "strain_energy_nmm_by_state_tag": {"a12-rear_zero": energy},
                      "per_state_physical_nodal_load_sha256": {"a12-rear_zero": load_hash},
                      "mesh": {"crack_area_mm2": area}, "sampled_sigma90_mpa_by_state_tag": {"a12-rear_zero": 2.},
                      "retained_field": {"path": "body/" + field_name, "sha256": field_sha},
                      "all_passed": True, "checks": {"equilibrium": True}}
        file_name = "body/" + name + ".json"
        reference = source(file_name, checkpoint)
        outputs[name + ".json"] = reference["sha256"]
        checkpoints[name] = checkpoint
        identity[name + "_checkpoint"] = reference
    row = {**deepcopy(identity), "case_id": identity["state_tag"], "source_state_record": state_reference,
           "source_action_record": {"path": "action/body-actions.jsonl.gz", "sha256": actions_sha, "pointer": "/0/actions"},
           "source_action_dictionary_sha256": hashlib.sha256(canonical(action["actions"]).encode()).hexdigest(),
           "physical_nodal_load_sha256": load_hash, "intact_initial_final_energies_nmm": [1., 2., 4.],
           "added_sound_area_mm2": 2., "Ft90_mpa": 1., "Gc_n_per_mm": 2., "intact_sampled_sigma90_mpa": 2.,
           "initiation_index": 2., "fracture_index": .5, "contact_upper_reference_index": .75}
    body_result = {"status": "COMPARED_WITH_MESH_LIMITS", "records": [row],
                   "reference_hypotheses": {**plan_reference, "pointer": "/assumptions"}}
    body_reference = source("body/result.json", body_result)
    outputs["result.json"] = body_reference["sha256"]
    body_only_source = tmp_path / "body-input.txt"
    body_only_source.write_text("unchanged field input")
    body_source_sha = hashlib.sha256(body_only_source.read_bytes()).hexdigest()
    producer_snapshot = tmp_path / "body/producer.py.snapshot"
    producer_snapshot.write_text("frozen field producer")
    producer_sha = hashlib.sha256(producer_snapshot.read_bytes()).hexdigest()
    (tmp_path / "field-producer.py").write_text("maintained field producer")
    outputs["producer.py.snapshot"] = producer_sha
    body_receipt = {"status": body_result["status"], "output_sha256": outputs,
                    "source_sha256": {**sources, "body-input.txt": body_source_sha, "field-producer.py": producer_sha},
                    "source_resolution": {"field-producer.py": {"original_path": "field-producer.py",
                        "sha256": producer_sha, "snapshot_path": "body/producer.py.snapshot"}}}
    receipt_reference = source("body/receipt.json", body_receipt)
    result = {"schema": SPLITTING_SCHEMA, "splitting_workstream_complete": True, "full_splitting_qualification": False,
              "historical_force_basis_transferred": False, "pending_feasible_comparison_count": 0,
              "pending_feasible_solid_bodies": 0, "active_solid_comparison_count": 1,
              "active_action_binding": {"receipt": action_binding["path"], "sha256": action_binding["sha256"]},
              "workload_binding": workload_reference, "required_state_inventory": inventory,
              "unavailable_state_count": 2, "unavailable_timber_state_slots": 88,
              "bodies": [{"body": "cleat", "result": body_reference, "receipt": receipt_reference}]}
    entry = {"status": COMPLETE, "numerical_scope": SPLITTING_SCOPE}
    splitting_scope_check(tmp_path, entry, result, sources, {}, {})
    if fault == "queued":
        result["pending_feasible_comparison_count"] = 1
    elif fault == "missing":
        body_result["records"] = []
    elif fault == "duplicate":
        body_result["records"].append(deepcopy(row))
    elif fault in {"false_exclusion", "queued_exclusion"}:
        if fault == "false_exclusion":
            method_records[0]["path"]["id"] = "different/plane"
        else:
            method_records[0]["status"] = "QUEUED_FEASIBLE_WORK"
        new_reference = source("method-limit.json", {"rows": method_records})
        for excluded in excluded_rows:
            excluded["method_limit"].update(new_reference)
        result["workload_binding"] = source("workload.json", workload)
    elif fault == "wrong_load":
        checkpoints["final"]["per_state_physical_nodal_load_sha256"]["a12-rear_zero"] = "2" * 64
        row["final_checkpoint"].update(source("body/final.json", checkpoints["final"]))
        outputs["final.json"] = row["final_checkpoint"]["sha256"]
    elif fault == "wrong_energy_index":
        row["fracture_index"] = .25
    elif fault == "altered_area":
        row["added_sound_area_mm2"] = 4.
        row["fracture_index"] = .25
        row["contact_upper_reference_index"] = .375
    elif fault == "altered_stress":
        row["intact_sampled_sigma90_mpa"] = 1.
        row["initiation_index"] = 1.
    elif fault == "altered_threshold":
        row["Gc_n_per_mm"] = 4.
        row["fracture_index"] = .25
        row["contact_upper_reference_index"] = .375
    elif fault == "omitted_body":
        workload["required_rows"] = []
        workload["excluded_rows"] = [row for row in excluded_rows if row["body"] != "cleat"]
        result["workload_binding"] = source("workload.json", workload)
        result["bodies"] = []
        result["active_solid_comparison_count"] = 0
    elif fault == "deleted_retained_field":
        (tmp_path / "body/final_field.npz").unlink()
    elif fault == "mutated_body_only_source":
        body_only_source.write_text("changed input absent from aggregate source bindings")
    elif fault == "wrong_action_record":
        action["state_tag"] = "a12-forward_zero"
    else:
        row["source_action_dictionary_sha256"] = hashlib.sha256(canonical([{"force_n": [1., 2., 3.]}]).encode()).hexdigest()
    if fault == "wrong_action_record":
        actions_sha = write_actions()
        row["source_action_record"]["sha256"] = action_receipt["output_sha256"]["body-actions.jsonl.gz"] = actions_sha
        result["active_action_binding"]["sha256"] = source("action/receipt.json", action_receipt)["sha256"]
        prepared_plan["source_action_receipt_sha256"] = result["active_action_binding"]["sha256"]
        plan_reference.update(source("prepared/plan.json", prepared_plan))
        body_result["reference_hypotheses"]["sha256"] = plan_reference["sha256"]
        prepared_receipt["output_sha256"]["plan.json"] = plan_reference["sha256"]
        workload["prepared_binding"]["sha256"] = source("prepared/receipt.json", prepared_receipt)["sha256"]
        result["workload_binding"] = source("workload.json", workload)
    body_reference.update(source("body/result.json", body_result))
    outputs["result.json"] = body_reference["sha256"]
    body_receipt["source_sha256"] = {**{name: digest for name, digest in sources.items() if name != "body/receipt.json"},
                                     "body-input.txt": body_source_sha, "field-producer.py": producer_sha}
    receipt_reference.update(source("body/receipt.json", body_receipt))
    error = "canonical body/path/grid/R-T/state obligation" if fault == "omitted_body" else "area or stress differs" if fault in {"altered_area", "altered_stress"} else None
    with pytest.raises((ValueError, OSError), match=error):
        splitting_scope_check(tmp_path, entry, result, sources, {}, {})


@pytest.mark.parametrize("fault", ["missing", "duplicate", "wrong_tag", "audit_gate", "stopped_force",
                                  "rejected_export", "wrong_trace", "wrong_census", "raw_stop", "actual_complete",
                                  "action_pointer", "action_full_scope", "action_export", "action_unassessed",
                                  "external_partial_binding", "coherence_stale_receipt", "coherence_inventory"])
def test_finite_disposition_requires_exact_inventory_and_accepted_exports(tmp_path, fault):
    index, extension, entry, _result, receipt = extension_fixture(tmp_path)
    packet = tmp_path / "packet"
    entry["status"] = FINITE_DISPOSITION
    for document in (entry, receipt):
        document.pop("counts")
    inputs = {"cases":list(CASES), "gap_scales":[0.,1.], "preparation":"fixed/preparation",
              "wood_reduction":"fixed/reduction", "dead_load_factor":1., "proposal_ties_included":False}
    history = [{"bearing_footprints":[i for i in range(8) if mask & (1 << i)],
                "solver":{"status":"Solved"},
                "original_physical_law_audit":{"all_passed":False,"checks":{"bearing_floor_branch":False}}}
               for mask in range(256)]
    trace = {"case_id":"a12-left", "gap_scale":0., "exception":FLOOR_PREFIX+json.dumps(history),
             "accepted_force_field_exists":False, "physical_release":False}
    trace_sha = write_json(packet / "case-stop.json", trace)
    dispositions, states, exports = [], [], set()
    for case in CASES:
        for gap in (0.,1.):
            tag = case + ("_zero" if gap == 0 else "_gap")
            item = {"case_id":case, "gap_scale":gap, "physical_release":False}
            if (case,gap) == ("a12-left",0.):
                item.update(status=FLOOR_STOP,accepted_force_field_exists=False,physical_frame_failure_claim=False,
                    stop_evidence={"packet":"packet", "receipt_sha256":None, "trace_path":"packet/case-stop.json",
                                   "trace_sha256":trace_sha, "pointer":"exception"},
                    floor_search_summary={"attempted_unique_masks":256,"solver_status_counts":{"Solved":256},
                        "failed_audit_gate_counts":{"bearing_floor_branch":256},"accepted_force_field_exists":False,
                        "scope":"No branch passed the unchanged physical audit; numerical stops are not physical infeasibility proofs."})
            else:
                item.update(status=ACCEPTED_STATE,accepted_force_field_exists=True,response_tag=tag)
                states.append({"case_id":case,"gap_scale":gap,"audit":{"all_passed":True,"checks":{"equilibrium":True}}})
                exports.update(tag+suffix for suffix in
                               ("_force_n","_relative_motion_mm","_rigid_scaled_mm","_shaft_pose_mm","_bearing"))
            dispositions.append(item)
    result = {"schema":FRAME_SCHEMA,"status":FRAME_PARTIAL,"states":states,"case_dispositions":dispositions,
              "complete_requested_state_inventory":True,"complete_six_case_zero_and_nominal_scope":False,
              "complete_permanent_zero_and_nominal_scope":True,"physical_release":False,"complete_joint_acceptance":False}
    entry["result_status"] = receipt["status"] = FRAME_PARTIAL
    receipt["completed_states"] = 13

    def refresh():
        receipt["output_sha256"]["inputs.json"] = write_json(packet / "inputs.json", inputs)
        receipt["output_sha256"]["case-stop.json"] = write_json(packet / "case-stop.json", trace)
        with zipfile.ZipFile(packet / "response.npz", "w") as archive:
            for name in sorted(exports):
                archive.writestr(name+".npy", b"synthetic saved field inventory")
        receipt["output_sha256"]["response.npz"] = hashlib.sha256((packet / "response.npz").read_bytes()).hexdigest()
        receipt["output_sha256"]["result.json"] = entry["result_sha256"] = write_json(packet / "result.json", result)
        entry["receipt_sha256"] = write_json(packet / "receipt.json", receipt)
        write_json(tmp_path / "index.json", index)

    refresh()
    extension["status"] = "complete"
    extension["parent_final_validation"] = {"confirmed":True}
    refresh()
    assert check("index.json", tmp_path)["pending_workstreams"] == 0
    if fault == "external_partial_binding":
        previous = tmp_path / "previous"
        previous.mkdir()
        source = deepcopy(result)
        source["case_dispositions"][4]["stop_evidence"].update(packet="previous",trace_path="previous/case-stop.json")
        previous_outputs = {"comparison.json":write_json(previous / "comparison.json", source),
                            "inputs.json":write_json(previous / "inputs.json", inputs),
                            "case-stop.json":write_json(previous / "case-stop.json", trace)}
        previous_receipt = {"status":FRAME_PARTIAL,"output_sha256":previous_outputs}
        previous_sha = write_json(previous / "receipt.json", previous_receipt)
        dispositions[4]["stop_evidence"].update(packet="previous",trace_path="previous/case-stop.json",receipt_sha256=previous_sha)
        receipt["source_sha256"]["previous/receipt.json"] = previous_sha
        refresh()
        assert check("index.json", tmp_path)["pending_workstreams"] == 0
    if fault.startswith(("action_", "coherence_")):
        frame_entry = deepcopy(entry)
        action = tmp_path / "action"
        action.mkdir()
        snapshot_sha = hashlib.sha256((packet / "producer.py.snapshot").read_bytes()).hexdigest()
        (action / "producer.py.snapshot").write_bytes((packet / "producer.py.snapshot").read_bytes())
        reference = {"path":"packet/result.json", "sha256":entry["result_sha256"]}
        inventory = deepcopy(dispositions)
        action_states, action_exports = [], {"canonical_raw_row_available", "canonical_raw_row_to_kept_lumped_position", "old_kept_lumped_rows"}
        state_positions = {(state["case_id"],state["gap_scale"]):i for i,state in enumerate(states)}
        for i,item in enumerate(inventory):
            key = item["case_id"], item["gap_scale"]
            tag = key[0] + ("_zero" if key[1] == 0 else "_gap")
            item.update(state_tag=tag,finite_disposition_completed=True,
                        source_disposition_record={**reference,"pointer":"/case_dispositions/"+str(i)})
            if item["status"] == ACCEPTED_STATE:
                record = {**reference,"pointer":"/states/"+str(state_positions[key])}
                item["source_state_record"] = record
                action_states.append({"case_id":key[0],"gap_scale":key[1],"state_tag":tag,"source_state_record":record})
                action_exports.update(tag+suffix for suffix in ("_raw_force_n","_kept_lumped_relative_motion_mm","_coupled_force_n"))
            else:
                item["physical_equilibrium_nonexistence_proven"] = False
        result = {"schema":ACTION_SCHEMA,"status":"COMPLETE_SAVED_COUPLED_ACTION_RECONCILIATION_NOT_RESISTANCE_QUALIFICATION",
            "source_response_status":FRAME_PARTIAL,"required_state_inventory":inventory,"states":action_states,
            "counts":{"required_states":14,"accepted_states":13,"finite_floor_search_dispositions":1,"assessed_states":14,
                      "unassessed_states":0,"unresolved_numerical_stops":0,"rejected_force_fields_exported":0},
            "finite_state_disposition_inventory_complete":True,"action_exports_complete_for_accepted_states":True,
            "completed_states":13,"all14_required_states":False,"action_state_scope":"accepted_state_subset"}
        receipt = {"status":result["status"],"source_sha256":{"packet/result.json":entry["result_sha256"],
                   "packet/receipt.json":entry["receipt_sha256"]},"output_sha256":{"producer.py.snapshot":snapshot_sha}}
        entry = {"status":FINITE_DISPOSITION,"result_status":result["status"],"result":"action/result.json",
                 "receipt":"action/receipt.json","preserved_producer_snapshot":"action/producer.py.snapshot",
                 "preserved_producer_sha256":snapshot_sha}
        extension["results"]["study"] = entry

        def refresh():
            receipt.update({field:result[field] for field in ("required_state_inventory", "counts",
                "finite_state_disposition_inventory_complete", "action_state_scope", "action_exports_complete_for_accepted_states")})
            with zipfile.ZipFile(action / "source-row-response.npz", "w") as archive:
                for name in sorted(action_exports):
                    archive.writestr(name+".npy", b"synthetic saved field inventory")
            receipt["output_sha256"]["source-row-response.npz"] = hashlib.sha256((action / "source-row-response.npz").read_bytes()).hexdigest()
            receipt["output_sha256"]["result.json"] = entry["result_sha256"] = write_json(action / "result.json", result)
            entry["receipt_sha256"] = write_json(action / "receipt.json", receipt)
            write_json(tmp_path / "index.json", index)

        refresh()
        assert check("index.json", tmp_path)["pending_workstreams"] == 0
        if fault.startswith("coherence_"):
            consumer = tmp_path / "consumer"
            consumer.mkdir()
            (consumer / "producer.py.snapshot").write_bytes((packet / "producer.py.snapshot").read_bytes())
            consumer_result = {"status":"COMPLETE_ACCEPTED_SUBSET_REFERENCES", "action_receipt_sha256":entry["receipt_sha256"],
                               "required_state_inventory":deepcopy(inventory)}
            consumer_receipt = {"status":consumer_result["status"],
                "source_sha256":{"action/receipt.json":entry["receipt_sha256"]},
                "output_sha256":{"producer.py.snapshot":snapshot_sha}}
            consumer_entry = {"status":COMPLETE,"result_status":consumer_result["status"],"result":"consumer/result.json",
                "receipt":"consumer/receipt.json","preserved_producer_snapshot":"consumer/producer.py.snapshot",
                "preserved_producer_sha256":snapshot_sha}
            extension["results"].update(frame=frame_entry,consumer=consumer_entry)
            extension["workstream_results"]["study"] = ["frame","study","consumer"]
            extension["selected_coupled_force_basis"] = {"frame_result":"frame","action_result":"study","consumer_results":["consumer"]}
            receipt["source_sha256"]["packet/result.json"] = frame_entry["result_sha256"]
            receipt["source_sha256"]["packet/receipt.json"] = frame_entry["receipt_sha256"]
            action_refresh = refresh

            def refresh():
                action_refresh()
                if fault != "coherence_stale_receipt" or "action/receipt.json" in consumer_receipt["source_sha256"]:
                    consumer_receipt["source_sha256"]["action/receipt.json"] = entry["receipt_sha256"]
                    consumer_result["action_receipt_sha256"] = entry["receipt_sha256"]
                consumer_receipt["output_sha256"]["result.json"] = consumer_entry["result_sha256"] = write_json(consumer / "result.json", consumer_result)
                consumer_entry["receipt_sha256"] = write_json(consumer / "receipt.json", consumer_receipt)
                write_json(tmp_path / "index.json", index)

            refresh()
            assert check("index.json", tmp_path)["selected_coupled_consumers"] == 1
    if fault == "missing":
        dispositions.pop()
    elif fault == "duplicate":
        dispositions[-1] = dispositions[0].copy()
    elif fault == "wrong_tag":
        dispositions[0]["response_tag"] = "a12-rear_gap"
    elif fault == "audit_gate":
        states[0]["audit"]["checks"]["equilibrium"] = False
    elif fault == "stopped_force":
        dispositions[4]["accepted_force_field_exists"] = True
    elif fault == "rejected_export":
        exports.add("a12-left_zero_force_n")
    elif fault == "wrong_trace":
        trace["case_id"] = "k12-right"
        dispositions[4]["stop_evidence"]["trace_sha256"] = write_json(packet / "case-stop.json", trace)
    elif fault == "wrong_census":
        dispositions[4]["floor_search_summary"]["solver_status_counts"]["Solved"] = 255
    elif fault == "raw_stop":
        result["status"] = entry["result_status"] = receipt["status"] = "STOP_COUPLED_FRAME_NUMERICAL_QUALIFICATION_OPEN"
    elif fault == "action_pointer":
        inventory[0]["source_state_record"]["pointer"] = "/states/1"
        action_states[0]["source_state_record"]["pointer"] = "/states/1"
    elif fault == "action_full_scope":
        result["all14_required_states"] = True
        result["action_state_scope"] = "all14_accepted_states"
    elif fault == "action_export":
        action_exports.add("a12-left_zero_coupled_force_n")
    elif fault == "action_unassessed":
        result["counts"]["unassessed_states"] = 1
    elif fault == "external_partial_binding":
        previous_receipt["output_sha256"].pop("comparison.json")
        dispositions[4]["stop_evidence"]["receipt_sha256"] = receipt["source_sha256"]["previous/receipt.json"] = write_json(previous / "receipt.json", previous_receipt)
    elif fault == "coherence_stale_receipt":
        stale_sha = write_json(tmp_path / "older-action/receipt.json", {"status":"preserved earlier action"})
        consumer_receipt["source_sha256"] = {"older-action/receipt.json":stale_sha}
        consumer_result["action_receipt_sha256"] = stale_sha
    elif fault == "coherence_inventory":
        consumer_result["required_state_inventory"][0]["gap_scale"] = 1.
    else:
        entry["status"] = COMPLETE
    refresh()
    with pytest.raises(ValueError):
        check("index.json", tmp_path)
