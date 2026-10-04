"""Prepare the owner-authorized representative assembled splitting study.

Importing this module performs no numerical work. Preparation authenticates the
existing geometry, actions and named paths, then freezes a small, distinct
selection. Native operator construction and assembled solves are parent-owned;
the old fixed-force inventory is never completed by this preparation.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import resource
import signal
import sys
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "current-candidate.json").is_file())
UPPER = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout"
HERE = UPPER / "all-joint-splitting"
RAW = HERE / "rawlocal/coupled-family-completion"
OLD = HERE / "rawlocal/splitting-capacity-completion"
READER = OLD / "project-draft14/active-group.py"
NOMINAL = OLD / "coupled-nominal02"
INVENTORY = OLD / "project-draft10/active-finite-workload.json"
BODY_RESULT = OLD / "active-solid01/center_post_cleat_left/result.json"
PROTOTYPE = OLD / "interface-condensation-prototype01/prototype.py"
LOCALIZED = OLD / "interface-condensation-localized-oracle01/oracle.py"
KERNEL = OLD / "project-draft08/producer-project-draft.py"
PLANE = OLD / "project-draft14/selected-plane-partition.py"
RADIAL = OLD / "project-draft12/radial-grid-correction.py"
CORE = UPPER / "joint-frame-member-replacement.py"
CACHE = UPPER / "rawlocal/joint-frame-member-replacement/source-body-left01"
OLD_OPERATORS = UPPER / "rawlocal/joint-frame-member-replacement/source-check01"
ALLOCATION = OLD / "project-draft15/chunked-assembly-install.py"
BASIS = "reviewed104_coupled_frame08_action03"
SCOPE = "representative_coupled_splitting_study"
COUPLING = "replace_one_body_full_frame_H_e_L_v1"
BOUNDARY = "source_physical_port_terms_retained_side_wrench_mapping_v1"
INITIAL_TAGS = ["a12-forward_zero", "a12-forward_gap", "dead-only_gap"]
EXPECTED = {
    READER: "cbbd027414b55a2691fe2909d8c6ff4bc1ae96fbdec4cf9d909e5ccfc83f3d78",
    INVENTORY: "83cc1a958382c0b756600625d4426b6d7d597e614f16c5344a6d932b99477b17",
    BODY_RESULT: "255c6666b8b5ac17d67b15a5a261c9cdb4dcfd2467bd5ff921a750c4bc3cd72d",
    PROTOTYPE: "8b7e940ee68318ffefb25ef9cd8d233d6c0c941cdabaf018464775c2f86eabab",
    LOCALIZED: "372609ca345a58d10ee39e1bb5a2eb40d298593334fbf7a2c9037502abc73a53",
    KERNEL: "1682cb15acdf9d24f77856cce8cc6f778a13f47148c76201b2a425aaeb1578a5",
    PLANE: "9a80701886dc90beab465a851a4f3d24873347c38cf2be33ddd03efade9f7372",
    RADIAL: "dbacb01cb9f9a9e6db609249157412941ff7f673530ab2a7c2328b27bcf151e8",
}
FAMILIES = (
    ("center_post", ("center_post_cleat_left", "center_post_cleat_right")),
    ("center_principal", ("center_principal_cleat_left", "center_principal_cleat_right")),
    ("outer_knee", ("knee_outer_left_inner_frame_block", "knee_outer_left_spine",
                    "knee_outer_right_inner_frame_block", "knee_outer_right_spine")),
    ("top_outer", ("top_outer_left_cleat", "top_outer_right_cleat")),
    ("ordinary_center_and_service", (
        "bottom_center_left_cleat", "bottom_center_right_cleat",
        "top_center_left_cleat", "top_center_right_cleat",
        "left_service_inner_lower_cleat", "left_service_inner_upper_cleat",
        "left_service_outer_lower_cleat", "left_service_outer_upper_cleat",
        "wj04_lower_full_stock_cleat", "wj04_upper_g7_crosscut_full_stock_cleat",
        "wj06_outer_lower_right_cleat", "wj06_outer_upper_right_cleat")),
    ("bottom_outer", ("bottom_outer_left_cleat", "bottom_outer_right_cleat")),
    ("retained_front_floor", ("rail_front_bolt_left", "rail_front_bolt_right")),
    ("rear_leg_upper_and_runner", ("lumber_leg_bolt_left", "lumber_leg_bolt_right",
                                   "rail_rear_bolt_left", "rail_rear_bolt_right")),
)
TARGETS = {
    "center_post": ("center_post_cleat_left", "Existing actual bore/end hotspot; compare assembled restraint before expanding paths."),
    "center_principal": ("base_principal_center_right", "Receiver side of the perpendicular header connection; distinguish receiver compliance from cleat compliance."),
    "outer_knee": ("knee_outer_left_spine", "Shared continuous shafts and two simultaneous receiving members require assembled redistribution."),
    "top_outer": ("top_outer_left_cleat", "Top rail/side couple and the supported top-rail washer revision need their own assembled source."),
    "ordinary_center_and_service": ("wj04_upper_g7_crosscut_full_stock_cleat", "Distinct short WJ04 upper blank; ordinary 119.7 mm blocks cannot establish its end-distance behavior."),
    "bottom_outer": ("bottom_outer_left_cleat", "Bottom rail/side force couple and receiver context differ from the header and service cleats."),
    "retained_front_floor": ("base_floor_left", "Receiver side of the retained front bolt pair, including the signed eccentric couple."),
    "rear_leg_upper_and_runner": ("lumber_leg_left", "Actual 1:12 leg profile and upper/runner receiving connections; reuse its proved profile adapters."),
}
FIELD_GATES = (
    "source_and_output_authentication", "source_port_order_and_body_ownership",
    "same_external_load_basis_and_rigid_work", "source_side_footprint_wrench_and_affine_work",
    "actual_profile_bore_volume_and_crack_area", "original_mesh_and_stiffness_identity",
    "rigid_quotient_and_gauge", "port_compliance_reciprocity_and_load_cross_terms",
    "old_body_removed_once_and_new_body_added_once", "assembled_equilibrium_and_spring_law",
    "recovered_full_body_equilibrium", "assembled_energy_and_external_work_identity",
    "unchanged_energy_constant_token", "retained_fields_and_port_reactions",
)


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def key(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def source_key(path):
    path = Path(path).resolve()
    return key(path) if path.is_relative_to(ROOT) else path.as_posix()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def reference(path, pointer=None):
    result = {"path": key(path), "sha256": sha(path)}
    if pointer is not None:
        result["pointer"] = pointer
    return result


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def bind(pins, path, value):
    path = Path(path).resolve()
    require(path not in pins or pins[path] == value, "Contradictory input digest: " + str(path))
    pins[path] = value


def bind_receipt(pins, path):
    record = read(path)
    bind(pins, path, sha(path))
    for name, value in record["source_sha256"].items():
        bind(pins, ROOT / name, value)
    for name, value in record["output_sha256"].items():
        bind(pins, path.parent / name, value)
    return record


def authenticate(pins):
    for path, value in pins.items():
        require(sha(path) == value, "Changed source: " + str(path))


def source_inputs():
    """Reuse the existing inert reader; no arrays or model assembly occur."""
    sys.dont_write_bytecode = True
    authenticate(EXPECTED)
    reader = module(READER, "representative_coupled_source_reader")
    pins, plan, geometries, source, actions = reader.inputs()
    for path, value in EXPECTED.items():
        bind(pins, path, value)
    bind_receipt(pins, NOMINAL / "receipt.json")
    bind(pins, Path(__file__).resolve(), sha(Path(__file__).resolve()))
    authenticate(pins)
    require(plan["active_basis"] == BASIS and len(plan["required_state_inventory"]) == 14,
            "Current geometry/action/state authority changed")
    return pins, plan, geometries, source, actions


def family_manifest(plan, geometries, nominal):
    duties = {d["joint_id"]: d for d in plan["duties"]}
    declared = [d for _, names in FAMILIES for d in names]
    require(len(declared) == len(set(declared)) == len(duties) == 30 and set(declared) == set(duties),
            "Eight-family partition must cover each current duty exactly once")
    timbers = sorted({b for d in duties.values() for b in d["timber_sides"]})
    require(len(timbers) == 44 and set(timbers) == set(geometries), "Canonical44 timber join changed")
    records = []
    for family, names in FAMILIES:
        bodies = sorted({b for name in names for b in duties[name]["timber_sides"]})
        candidates = [r for r in nominal["records"] if r["body"] in bodies]
        governing = max(candidates, key=lambda r: r["nominal_tension_reference_index"])
        target, reason = TARGETS[family]
        require(target in bodies, "Representative body is outside its physical family")
        record = {
            "id": family, "duty_ids": list(names), "duty_count": len(names),
            "timber_sides": bodies, "receiver_sides": {
                name: [b for b in duties[name]["timber_sides"] if b != name] for name in names},
            "physical_axis_ids": sorted({a for name in names for a in duties[name]["physical_axis_ids"]}),
            "candidate_target": target, "selection_reason": reason,
            "candidate_status": "PLANNED_AFTER_FIRST_BODY_METHOD_REVIEW",
            "signed_nominal_screen_witness": {k: governing[k] for k in (
                "body", "case_id", "axis", "plane_mm", "section_limit_side",
                "source_full_signed_wrench_g_u_v_n_nmm", "nominal_tension_reference_index")},
            "nominal_screen_is_fracture_or_capacity_proof": False,
            "mirror_force_or_geometry_pass_transferred": False,
            "path_selection": "Freeze two or three physical fronts only after the assembled intact comparison; retain signed force geometry and receiver context.",
        }
        if family == "ordinary_center_and_service":
            short = "wj04_upper_g7_crosscut_full_stock_cleat"
            record["distinct_subtypes"] = [{"body": short, "grain_length_mm": geometries[short]["length_mm"],
                                            "scope": "Short WJ04 upper crosscut remains a separate subtype."}]
        records.append(record)
    return {"families": records, "family_count": 8, "duty_count": 30,
            "timber_count": 44, "canonical_timber_names": timbers,
            "all_duties_evaluated": False, "all_timbers_evaluated": False}


def physical_port_terms(body, plan, actions):
    """Recover unit physical terms from authenticated linear source actions.

    Source actions use the existing convention force_on_wood=-B.T*port_force.
    Kept source-row weights are retained. Every nonzero saved witness for the
    same action is checked; a missing all-zero term is a method input gap.
    The native phase independently checks all active B rows and B*R.
    """
    row_map_path = UPPER / "rawlocal/joint-frame-action-reconciliation/attempt03/source-row-map.json"
    row_map = read(row_map_path)
    ports = {}
    for item in row_map["kept_map"]:
        for raw, weight in zip(item["raw_rows"], item["weights"], strict=True):
            require(raw not in ports, "A canonical source row belongs to multiple frame ports")
            ports[raw] = (item["kept_position"], weight)
    witnesses = {}
    for tag in plan["accepted_state_tags"]:
        for number, action in enumerate(actions[body, tag]["actions"]):
            if action["role"] == "discrete_body_load" or not action.get("source_force_available", True):
                continue
            if action.get("coupled_port_row") is not None:
                port, weight = action["coupled_port_row"], 1.
            else:
                require(action["row"] in ports, "Physical action lacks a current frame port")
                port, weight = ports[action["row"]]
            value = action["scalar_row_force_n"]
            require(value is not None, "Interface action has no scalar source witness")
            identity = (port, action["source_id"], tuple(action["point_mm"]), action["role"])
            if abs(value) > 1e-8:
                witnesses.setdefault(identity, []).append((tag, number, action, weight))
    terms = []
    for (port, identifier, point, role), seen in sorted(witnesses.items()):
        tag, number, action, weight = max(seen, key=lambda r: abs(r[2]["scalar_row_force_n"]))
        denominator = -action["scalar_row_force_n"]
        force = [weight * x / denominator for x in action["force_n"]]
        moment = [weight * x / denominator for x in action["free_moment_nmm"]]
        force_error, moment_error = 0., 0.
        for _, _, other, other_weight in seen:
            divisor = -other["scalar_row_force_n"]
            force_error = max(force_error, *(abs(a - other_weight * b / divisor)
                                            for a, b in zip(force, other["force_n"], strict=True)))
            moment_error = max(moment_error, *(abs(a - other_weight * b / divisor)
                                              for a, b in zip(moment, other["free_moment_nmm"], strict=True)))
        require(force_error < 1e-9 and moment_error < 1e-6,
                "Physical source term is not linear in its signed port force")
        terms.append({"port_row": port, "source_id": identifier, "point_mm": list(point), "role": role,
                      "force_global_xyz_per_unit_port_force": force,
                      "free_couple_global_xyz_mm_per_unit_port_force": moment,
                      "source_action_record": {"path": key(OLD / "coupled-prepared01/actions.jsonl.gz"),
                                               "sha256": sha(OLD / "coupled-prepared01/actions.jsonl.gz"),
                                               "body": body, "state_tag": tag, "action_index": number},
                      "nonzero_saved_witness_count": len(seen), "maximum_unit_force_difference": force_error,
                      "maximum_unit_free_couple_difference_mm": moment_error})
    require(terms, "No authenticated physical interface terms found")
    return {"schema": "splitting_coupled_physical_port_terms/v1", "body": body,
            "source_row_map": reference(row_map_path), "terms": terms,
            "active_port_rows_from_physical_actions": sorted({t["port_row"] for t in terms}),
            "source_force_convention": "Physical connector force on timber=-B.T*frame_port_force.",
            "native_active_B_row_and_rigid_work_check_required": True,
            "original_B_nodal_projection_copied_as_physical_pressure": False,
            "cross_crack_stitch_invented": False}


def prepare(output):
    """Freeze geometry and obligations before a separately approved native run."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "Fresh owned preparation child required")
    pins, plan, geometries, source, actions = source_inputs()
    inventory = read(INVENTORY)
    body = "center_post_cleat_left"
    original = next(r for r in inventory["records"] if r["body"] == body)
    path = next(p for p in original["finite_paths"] if p["id"] == "end/1/high")
    require(path["axis"] == 1 and path["plane_mm"] == 0. and path["initial_interval_mm"] == [123.9, 128.9]
            and path["final_interval_mm"] == [118.9, 128.9], "First physical upper end path changed")
    required_states = [{"state_tag": s["state_tag"], "case_id": s["case_id"], "gap_scale": s["gap_scale"],
                        "source_baseline_disposition": s["source_disposition_record"],
                        "baseline_accepted_force_field_exists": s["accepted_force_field_exists"],
                        "changed_model_requires_fresh_disposition": True} for s in plan["required_state_inventory"]]
    require(len({s["state_tag"] for s in required_states}) == 14
            and set(INITIAL_TAGS) <= {s["state_tag"] for s in required_states}, "Required state selection changed")
    contracts = {
        "geometry_binding": reference(OLD / "coupled-prepared01/geometry.json", "/" + body),
        "geometry_sha256": digest(geometries[body]),
        "material_binding": reference(OLD / "coupled-prepared01/plan.json", "/assumptions"),
        "external_load_basis": "Original full12 external gravity/live RHS columns; each case uses its immutable coefficient vector. Interface reactions are re-solved.",
        "port_B_contract": "Full current frame port order and signed source physical point/force/couple terms; restrict to this body without dropping terms. Actual retained-side footprints preserve resultant, moment and affine virtual work.",
        "boundary_footprint_id": BOUNDARY, "coupling_method_id": COUPLING,
        "energy_constant_scope": "selected_body_load_matrix_plus_unchanged_constant",
        "unchanged_body_load_chi_nmm": None, "absolute_assembled_potential_claimed": False,
        "energy_method": "G=(Pi_initial-Pi_final)/added_sound_area under the same external coefficient vector and unchanged additive-constant token, including connector energy, rigid work and full selected-body L cross-terms.",
        "contact_upper_bound_assessed": False,
        "old_fixed_force_contact_upper_bound_transferred": False,
        "unmeasured_Ft90_mpa": .5, "unmeasured_Gc_all_modes_n_per_mm": .1,
        "new_preload_friction_or_reinforcement_credited": False,
        "source_action_receipt": reference(UPPER / "rawlocal/joint-frame-action-reconciliation/attempt03/receipt.json"),
        "old_source_body_contribution_removal": "Remove the selected body's H/e/L exactly once, retaining all other wood, shaft, washer and contact operators, then add each actual target variant once.",
        "physical_crack_stitching": "Existing shared bolt/washer connector ports remain in the assembled model; source-side nodal force clouds alone supply no invented across-crack stitch.",
    }
    variants, comparisons = [], []
    for size in (20., 15.):
        for rt in ("R=u,T=v", "R=v,T=-u"):
            roles = []
            for role, interval in (("intact", None), ("initial", path["initial_interval_mm"]),
                                   ("final", path["final_interval_mm"])):
                identity = {"body": body, "path": path, "configuration": role, "crack_interval_mm": interval,
                            "mesh_size_mm": size, "RT_binding": rt, **contracts}
                identifier = "operator-" + digest(identity)[:24]
                variants.append({"id": identifier, **identity})
                roles.append(identifier)
            for state in required_states:
                identity = {"body": body, "path": path, "axis": 1, "plane_mm": 0.,
                            "mesh_size_mm": size, "RT_binding": rt, **state, **contracts}
                projection = {"body": body, "path": path, "state_tag": state["state_tag"],
                              "mesh_size_mm": size, "RT_binding": rt}
                comparisons.append({"id": "comparison-" + digest(identity)[:24], **identity,
                                    "operator_variants": dict(zip(("intact", "initial", "final"), roles, strict=True)),
                                    "original_path_projection": projection if state["baseline_accepted_force_field_exists"] else None,
                                    "initial_execution_selected": state["state_tag"] in INITIAL_TAGS})
    require(len(variants) == len({v["id"] for v in variants}) == 12 and len(comparisons) == 56,
            "Pilot12-operator/14-state explicit obligations changed")
    manifest = family_manifest(plan, geometries, read(NOMINAL / "nominal.json"))
    selection = {
        "schema": "splitting_representative_coupled_selection/v1", "numerical_scope": SCOPE,
        "status": "PREPARED_REPRESENTATIVE_SELECTION_PENDING_COUPLED_METHOD_PROOF",
        "original_inventory_binding": reference(INVENTORY), "prepared_binding": reference(OLD / "coupled-prepared01/receipt.json"),
        "original_inventory_count": 37056, "original_unsampled_disposition": "UNASSESSED_OUTSIDE_REVISED_SCOPE",
        "original_inventory_completion_transferred": False, "family_manifest": manifest,
        "operator_variants": variants, "required_comparisons": comparisons,
        "required_state_dispositions": required_states, "initial_execution_state_tags": INITIAL_TAGS,
        "initial_execution_comparison_count": sum(c["initial_execution_selected"] for c in comparisons),
        "required_comparison_count": len(comparisons), "native_operator_variant_budget": len(variants),
        "selected_body_count": 1, "candidate_body_budget": 8, "physical_paths_per_later_target_budget": [2, 3],
        "required_field_gates": list(FIELD_GATES),
        "initial_method_questions": [
            "Does the actual bored cleat with source-owned interfaces reproduce an auditable assembled intact equilibrium and energy, and how does it differ from the old filled-body compliance?",
            "Do source interface footprints preserve physical force/moment and rigid virtual work without imposing a crack stitch?",
            "Does total assembled potential decrease consistently when the bounded5mm front extends to10mm, after interface reactions redistribute under unchanged external loads?"],
        "method_readiness_requirements": [
            "Passed assembled replacement/energy known answer, including selected-L constant cancellation.",
            "Passed actual interface mapping known answer and exact full source port/external load basis binding.",
            "Parent-selected measured count/storage and resource bounds before each native operator group.",
            "Supported wider/thicker top-rail washer contract frozen as a separate global scenario before its results are compared."],
        "numerical_solid_solve_executed": False, "complete_representative_study": False,
        "splitting_workstream_complete": False, "full_splitting_qualification": False,
    }
    selected_actions = [{k: v for k, v in source[body, tag].items() if k != "source_actions"} for tag in INITIAL_TAGS]
    binding = {"schema": "splitting_representative_coupled_source_bindings/v1", "contracts": contracts,
               "initial_source_action_bindings": selected_actions,
               "same_physical_nodal_reaction_hash_required_between_crack_variants": False,
               "immutable_external_basis_hash_required_between_variants": True,
               "native_execution_ready": False, "missing_before_native_launch": selection["method_readiness_requirements"]}
    port_terms = physical_port_terms(body, plan, actions)
    output.mkdir(parents=True)
    write(output / "selection.json", selection)
    write(output / "source-bindings.json", binding)
    write(output / "physical-port-terms.json", port_terms)
    authenticate(pins)
    receipt = {"schema": "splitting_representative_coupled_preparation_receipt/v1", "status": selection["status"],
               "producer_sha256": sha(Path(__file__)), "source_sha256": {source_key(p): h for p, h in pins.items()},
               "source_before": {source_key(p): h for p, h in pins.items()}, "source_after": {source_key(p): sha(p) for p in pins},
               "output_sha256": {name: sha(output / name) for name in ("selection.json", "source-bindings.json", "physical-port-terms.json")},
               "numerical_solid_solve_executed": False, "complete_joint_acceptance": False}
    write(output / "receipt.json", receipt)
    return {"status": selection["status"], "selection": reference(output / "selection.json"),
            "receipt": reference(output / "receipt.json"), "operator_variants": 12, "required_comparisons": 56,
            "initial_comparisons": 12, "family_count": 8, "duty_count": 30, "timber_count": 44,
            "native_execution_ready": False}


def verify(prepared, expected_sha256):
    prepared = Path(prepared).resolve()
    require(prepared.parent == RAW.resolve(), "Owned preparation packet required")
    require(sha(prepared / "receipt.json") == expected_sha256, "Preparation receipt changed")
    pins = {}
    record = bind_receipt(pins, prepared / "receipt.json")
    authenticate(pins)
    selection = read(prepared / "selection.json")
    count = 4 * len(selection["required_state_dispositions"])
    require(selection["native_operator_variant_budget"] == 12 and selection["required_comparison_count"] == count
            and selection["initial_execution_comparison_count"] == 12 and not record["numerical_solid_solve_executed"],
            "Preparation scope or execution claim changed")
    return {"status": "PASS_REPRESENTATIVE_SELECTION_SOURCE_AUTHENTICATION", "source_and_output_bindings": len(pins),
            "native_execution_ready": False, "physical_or_complete_joint_acceptance": False}


def prepare_eligible(output, original_selection, original_sha256, baseline, baseline_sha256, active_actions, action_sha256):
    """Freeze only the audited new baseline's eligible external states.

    A baseline state without an audited field is a source-domain limitation.
    Its absence is never asserted to be a cracked-body impossibility, and this
    selection does not repeat a floor-mask search for it at every operator.
    """
    output, original_selection, baseline, active_actions = [Path(p).resolve() for p in
                                                          (output, original_selection, baseline, active_actions)]
    require(output.parent == RAW.resolve() and not output.exists(), "Fresh owned eligible selection required")
    require(sha(original_selection) == original_sha256 and sha(baseline / "receipt.json") == baseline_sha256,
            "Selection/baseline receipt changed")
    pins = {}
    bind_receipt(pins, original_selection.parent / "receipt.json")
    baseline_receipt = bind_receipt(pins, baseline / "receipt.json")
    require(sha(active_actions / "receipt.json") == action_sha256, "Current action receipt changed")
    action_receipt = bind_receipt(pins, active_actions / "receipt.json")
    action_inputs = read(active_actions / "inputs.json")
    require(action_receipt["source_sha256"].get(key(baseline / "receipt.json")) == baseline_sha256
            and action_inputs["response"] == key(baseline)
            and action_inputs["dead_load_factor"] == read(baseline / "inputs.json")["dead_load_factor"],
            "Fresh action export does not select the frozen new baseline/external load factor")
    action_binding = {"receipt": key(active_actions / "receipt.json"), "sha256": action_sha256}
    require(baseline_receipt["output_sha256"].get("comparison.json") == sha(baseline / "comparison.json")
            and baseline_receipt["output_sha256"].get("response.npz") == sha(baseline / "response.npz"),
            "Eligible baseline fields are not receipt-output-owned")
    report = read(baseline / "comparison.json")
    old = read(original_selection)
    dispositions = report["case_dispositions"]
    require(report["complete_requested_state_inventory"] and len(dispositions) == 14,
            "All fourteen baseline dispositions must be recorded before eligibility freezes")
    states = {(s["case_id"], s["gap_scale"]): (i, s) for i, s in enumerate(report["states"])}
    eligible, outside = [], []
    for i, disposition in enumerate(dispositions):
        case, gap = disposition["case_id"], disposition["gap_scale"]
        tag = case + ("_zero" if gap == 0 else "_gap")
        source = reference(baseline / "comparison.json", "/case_dispositions/" + str(i))
        record = {"state_tag": tag, "case_id": case, "gap_scale": gap,
                  "source_baseline_disposition": source,
                  "baseline_accepted_force_field_exists": disposition["accepted_force_field_exists"]}
        if disposition["accepted_force_field_exists"]:
            require((case, gap) in states and states[case, gap][1]["audit"]["all_passed"],
                    "Eligible baseline state lacks its audited field")
            record.update(changed_model_requires_fresh_disposition=True,
                          baseline_response_state_ref=reference(baseline / "comparison.json", "/states/" + str(states[case, gap][0])))
            eligible.append(record)
        else:
            require((case, gap) not in states, "Unaudited baseline state exposes a force field")
            outside.append({**record, "status": "OUTSIDE_ELIGIBLE_BASELINE_FORCE_FIELD_DOMAIN",
                            "unavailable_source_state_disposition": "OUTSIDE_ELIGIBLE_BASELINE_FORCE_FIELD_DOMAIN",
                            "unavailable_cracked_body_equilibrium_claim": False,
                            "cracked_variant_infeasibility_claimed": False,
                            "fresh_variant_floor_search_required": False})
    require(len(states) == len(eligible) and len({s["state_tag"] for s in eligible + outside}) == 14
            and set(INITIAL_TAGS) <= {s["state_tag"] for s in eligible},
            "Initial pilot states or complete baseline census differ")
    require({tuple(s) for s in action_inputs["states"]} == set(states), "New action export accepted state inventory differs")
    binding = {"receipt": reference(baseline / "receipt.json"),
               "comparison": reference(baseline / "comparison.json")}
    variants, role_groups, comparisons = [], {}, []
    for variant in old["operator_variants"]:
        variants.append(variant)
        role_groups.setdefault((variant["mesh_size_mm"], variant["RT_binding"]), {})[variant["configuration"]] = variant["id"]
    prototypes = {}
    for row in old["required_comparisons"]:
        prototypes.setdefault((row["mesh_size_mm"], row["RT_binding"]), row)
    old_accepted = {s["state_tag"] for s in old["required_state_dispositions"] if s["baseline_accepted_force_field_exists"]}
    for group, prototype in prototypes.items():
        for state in eligible:
            identity = {k: v for k, v in prototype.items() if k not in
                        ("id", "operator_variants", "original_path_projection", "initial_execution_selected",
                         "state_tag", "case_id", "gap_scale", "source_baseline_disposition",
                         "baseline_accepted_force_field_exists", "changed_model_requires_fresh_disposition")}
            identity.update(state, baseline_eligibility_binding=binding,
                            global_joint_update_binding=reference(baseline / "joint-update.json"),
                            active_action_binding=action_binding,
                            source_action_force_transfer=False)
            identity["historical_port_action_receipt"] = identity.pop("source_action_receipt")
            projection = {"body": identity["body"], "path": identity["path"], "state_tag": state["state_tag"],
                          "mesh_size_mm": identity["mesh_size_mm"], "RT_binding": identity["RT_binding"]}
            comparisons.append({"id": "comparison-" + digest(identity)[:24], **identity,
                                "operator_variants": role_groups[group],
                                "original_path_projection": projection if state["state_tag"] in old_accepted else None,
                                "initial_execution_selected": state["state_tag"] in INITIAL_TAGS})
    selection = dict(old, status="PREPARED_ELIGIBLE_REPRESENTATIVE_SELECTION_PENDING_NATIVE_OPERATORS",
                     superseded_preparation_binding=reference(original_selection),
                     operator_selection_binding=reference(original_selection),
                     baseline_eligibility_binding=binding, baseline_state_dispositions=dispositions,
                     active_action_binding=action_binding,
                     global_joint_update_binding=reference(baseline / "joint-update.json"),
                     outside_eligible_baseline_state_dispositions=outside,
                     required_state_dispositions=eligible, operator_variants=variants, required_comparisons=comparisons,
                     required_comparison_count=len(comparisons), required_operator_state_disposition_count=12 * len(eligible),
                     initial_execution_comparison_count=sum(r["initial_execution_selected"] for r in comparisons),
                     baseline_unavailable_dispositions_are_cracked_body_limits=False,
                     repeated_baseline_floor_searches_per_crack_variant=False)
    output.mkdir(parents=True)
    write(output / "selection.json", selection)
    (output / "physical-port-terms.json").write_bytes((original_selection.parent / "physical-port-terms.json").read_bytes())
    write(output / "source-bindings.json", {"schema": "splitting_representative_coupled_source_bindings/v1",
          "baseline_eligibility_binding": binding, "baseline_state_dispositions": dispositions,
          "original_port_terms_binding": reference(original_selection.parent / "physical-port-terms.json"),
          "old_source_action_force_fields_transferred": False,
          "same_physical_nodal_reaction_hash_required_between_crack_variants": False,
          "immutable_external_basis_hash_required_between_variants": True,
          "native_execution_ready": False})
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    bind(pins, output / "producer.py.snapshot", sha(output / "producer.py.snapshot"))
    authenticate(pins)
    sources = {source_key(p): h for p, h in pins.items()}
    write(output / "receipt.json", {"schema": "splitting_representative_coupled_preparation_receipt/v1",
          "status": selection["status"], "producer_sha256": sha(output / "producer.py.snapshot"),
          "source_sha256": sources, "source_before": sources, "source_after": {source_key(p): sha(p) for p in pins},
          "output_sha256": {p.name: sha(p) for p in output.iterdir() if p.is_file()},
          "numerical_solid_solve_executed": False, "complete_joint_acceptance": False})
    return {"selection": reference(output / "selection.json"), "receipt": reference(output / "receipt.json"),
            "eligible_states": len(eligible), "baseline_unavailable_states": len(outside),
            "required_comparisons": len(comparisons), "required_operator_states": 12 * len(eligible)}


def rigid_basis(np, nodes, geometry, datum, rotation_scale_mm=1000.):
    """Use the original body's global datum and physical frame coordinates."""
    frame, start, datum = [np.asarray(x) for x in (geometry["frame"], geometry["start"], datum)]
    world = start + nodes @ frame
    R = np.zeros((3 * len(nodes), 6))
    for number, point in enumerate(world):
        R[3 * number:3 * number + 3, :3] = frame
        for axis, unit in enumerate(np.eye(3)):
            R[3 * number:3 * number + 3, 3 + axis] = frame @ np.cross(unit, point - datum) / rotation_scale_mm
    Q, _ = np.linalg.qr(R, mode="reduced")
    return R, Q, world


def affine_targets(np, original, source_body):
    """Complete force and first moments of each original native RHS column."""
    values = np.asarray(original)
    targets = np.zeros((4, 3, values.shape[1]))
    datum = np.asarray(source_body["datum_mm"])
    for dof, (node, component) in enumerate(source_body["labels"]):
        point = np.asarray(source_body["coordinates"][node]) - datum
        targets[:, component - 1] += np.r_[1., point][:, None] * values[dof]
    return targets


def affine_distribution(np, sparse, points, target, datum, weights, nonnegative_normal=False):
    """Conditional finite patch with full native affine virtual-work targets.

    Bilateral traction uses weighted minimum norm. A unilateral normal patch
    additionally requires nonnegative scalar traction along its prescribed
    normal. No kinematic constraint is added to any nodes.
    """
    A = np.column_stack((np.ones(len(points)), (points - datum) / 100.)).T
    rhs = np.asarray(target).copy()
    rhs[1:] /= 100.
    left, singular, right = np.linalg.svd(A, full_matrices=False)
    rank = int(np.count_nonzero(singular > 1e-12 * singular[0]))
    require(rank > 0, "Empty affine footprint rank")
    reduced, projected = right[:rank], (left[:, :rank].T @ rhs) / singular[:rank, None]
    range_error = float(np.max(abs(A @ (reduced.T @ projected) - rhs), initial=0.))
    require(range_error < 1e-8, "Original native affine target is outside this retained physical patch range")
    if nonnegative_normal:
        import clarabel

        force = target[0]
        component = int(np.argmax(abs(force)))
        require(abs(force[component]) > 1e-12, "Normal-only footprint has no resultant")
        scalar_target = projected[:, component] / force[component]
        require(np.max(abs(projected - scalar_target[:, None] * force), initial=0.) < 1e-8,
                "Unilateral source first moments require non-normal traction")
        equality = sparse.csc_matrix(reduced)
        matrix = sparse.vstack((equality, -sparse.eye(len(points))), format="csc")
        settings = clarabel.DefaultSettings()
        settings.verbose = False
        settings.tol_gap_abs, settings.tol_gap_rel, settings.tol_feas = 1e-11, 1e-11, 1e-11
        solver = clarabel.DefaultSolver(sparse.diags(1. / weights, format="csc"), np.zeros(len(points)),
            matrix, np.r_[scalar_target, np.zeros(len(points))],
            [clarabel.ZeroConeT(rank), clarabel.NonnegativeConeT(len(points))], settings)
        solved = solver.solve()
        require(str(solved.status) in ("Solved", "AlmostSolved"),
                "No audited nonnegative normal affine footprint: " + str(solved.status))
        alpha = np.asarray(solved.x)
        require(np.min(alpha) >= -1e-10, "Normal footprint requires tensile/adhesive scalar weights")
        values = alpha[:, None] * force
        signed = False
        normal_audit = {"solver": "Clarabel", "solver_version": clarabel.__version__, "status": str(solved.status),
                        "minimum_scalar_weight": float(np.min(alpha)), "nonnegative_weight_tolerance": 1e-10,
                        "maximum_scalar_equality_residual": float(np.max(abs(reduced @ alpha - scalar_target), initial=0.))}
    else:
        gram = (reduced * weights) @ reduced.T
        values = weights[:, None] * (reduced.T @ np.linalg.solve(gram, projected))
        signed = True
        normal_audit = None
    error = float(np.max(abs(A @ values - rhs), initial=0.))
    require(error < 1e-8 and np.isfinite(values).all(), "Full affine footprint virtual-work audit failed")
    return values, {"affine_rank": rank, "scaled_force_first_moment_residual": error,
                    "first_moment_scale_mm": 100., "signed_bilateral_tractions_permitted": signed,
                    "normal_only_nonnegative_traction_audit": normal_audit,
                    "recovered_contact_pressure_or_preload_claimed": False}


def map_affine_columns(np, sparse, nodes, geometry, targets, datum, centers, axis, plane, normal_columns=()):
    frame, start = np.asarray(geometry["frame"]), np.asarray(geometry["start"])
    world = start + nodes @ frame
    result = np.zeros((3 * len(nodes), targets.shape[2]))
    audits = []
    for column, center in enumerate(centers):
        if np.max(abs(targets[:, :, column]), initial=0.) < 1e-14:
            audits.append({"column": column, "zero_external_basis_column": True})
            continue
        center = np.asarray(center)
        local = frame @ (center - start)
        distance = np.linalg.norm(world - center, axis=1)
        eligible = np.flatnonzero(nodes[:, axis] > plane + 1e-7 if local[axis] >= plane else nodes[:, axis] < plane - 1e-7)
        require(len(eligible), "No retained material on the source side")
        order = eligible[np.argsort(distance[eligible], kind="stable")]
        failures = []
        for radius in (15., 30.):
            chosen = order[distance[order] < distance[order[0]] + radius]
            weights = (1. - (distance[chosen] - distance[order[0]]) / radius) ** 2
            try:
                values, audit = affine_distribution(np, sparse, world[chosen], targets[:, :, column],
                                                    np.asarray(datum), weights, column in normal_columns)
                break
            except RuntimeError as exc:
                failures.append({"radius_increment_mm": radius, "reason": str(exc)})
        else:
            raise RuntimeError("No supported retained-side affine footprint for column " + str(column) + ": " + json.dumps(failures))
        result[(3 * chosen[:, None] + np.arange(3)).ravel(), column] = (values @ frame.T).ravel()
        audits.append({"column": column, "radius_increment_mm": radius, "chosen_nodes": chosen.tolist(),
                       "source_side": "positive" if local[axis] >= plane else "negative", "original_patch_failures": failures,
                       "maximum_distance_from_native_affine_center_mm": float(distance[chosen].max()), **audit})
    return result, {"columns": audits, "full_native_affine_targets_retained": True,
                    "physical_side_ownership_retained": True, "kinematic_tie_or_crack_stitch_added": False}


def map_port_basis(np, sparse, helper, nodes, geometry, terms, total_port_count, axis, plane,
                   source_body=None):
    active = sorted({t["port_row"] for t in terms})
    records = [{"actions": [{"point_mm": t["point_mm"],
                             "force_n": t["force_global_xyz_per_unit_port_force"],
                             "free_moment_nmm": t["free_couple_global_xyz_mm_per_unit_port_force"]}
                            for t in terms if t["port_row"] == port]} for port in active]
    if source_body is None:
        loads, audit = helper.load_vector(nodes, geometry, records, axis, plane)
    else:
        original = source_body["B"][active].T.toarray()
        targets = affine_targets(np, original, source_body)
        centers, normal = [], []
        for column, port in enumerate(active):
            force = targets[0, :, column]
            magnitude = float(force @ force)
            require(magnitude > 1e-20, "Pure native couple needs an independently frozen physical patch")
            centers.append(np.asarray(source_body["datum_mm"]) + targets[1:, :, column] @ force / magnitude)
            roles = {t["role"] for t in terms if t["port_row"] == port}
            if roles <= {"timber_or_panel_contact", "physical_bolt_outer_seat_tension"}:
                normal.append(column)
        loads, audit = map_affine_columns(np, sparse, nodes, geometry, targets, source_body["datum_mm"],
                                         centers, axis, plane, normal)
    rows, columns = np.nonzero(loads.T)
    B = sparse.coo_matrix((loads.T[rows, columns], (np.asarray(active)[rows], columns)),
                          shape=(total_port_count, len(loads))).tocsr()
    return B, np.asarray(active, dtype=int), audit


def map_external_basis(np, sparse, nodes, elements, geometry, source_body, axis, plane):
    """Preserve the complete12-column original body-load affine signature.

    These original consistent finite-element loads are not observed point
    tractions. Positive incident-cell volume weights define the declared new
    body-load footprint; signed force values may result, as in the original
    consistent C3D20 body-load vector. This never supplies contact adhesion.
    """
    frame, start = np.asarray(geometry["frame"]), np.asarray(geometry["start"])
    world = start + nodes @ frame
    chosen = np.flatnonzero(abs(nodes[:, axis] - plane) > 1e-7)
    require(len(chosen) >= 4, "Body-load footprint has insufficient retained material nodes")
    weights = np.zeros(len(nodes))
    for element in elements:
        corners = nodes[element[:8]]
        volume = float(np.prod(corners.max(axis=0) - corners.min(axis=0)))
        weights[element] += volume / len(element)
    require(np.min(weights[chosen]) > 0., "Body-load footprint includes unowned/zero-volume nodes")
    weights = weights[chosen] / np.max(weights[chosen])
    targets = affine_targets(np, source_body["F"], source_body)
    mapped, audits = np.zeros((3 * len(nodes), 12)), []
    cache = {}
    for column in range(12):
        target = targets[:, :, column]
        signature = np.ascontiguousarray(target).tobytes()
        if signature in cache:
            values, audit = cache[signature]
        elif np.max(abs(target), initial=0.) < 1e-14:
            values, audit = np.zeros((len(chosen), 3)), {"zero_external_basis_column": True}
            cache[signature] = (values, audit)
        else:
            values, audit = affine_distribution(np, sparse, world[chosen], target,
                                               np.asarray(source_body["datum_mm"]), weights)
            cache[signature] = (values, audit)
        mapped[(3 * chosen[:, None] + np.arange(3)).ravel(), column] = (values @ frame.T).ravel()
        audits.append({"column": column, **audit})
    return mapped, {"columns": audits, "original_full_body_load_basis_affine_targets_retained": True,
                    "footprint": "Positive incident-cell-volume metric; seam nodes excluded without adding any ties.",
                    "signed_consistent_external_body_forces_permitted": True,
                    "contact_adhesion_or_crack_stitch_credited": False}


def localized_solutions(np, sparse, splu, prototype, helper, condensation, quotient, localized,
                        configs, constants, swap, event, limits):
    """Reuse the proved union/Schur solver for projected operator RHS columns.

    No new element, interface or constitutive equation is introduced. Original
    full fields are recovered from the existing latent node maps, then only a
    rigid pose is removed to obtain the orthogonal elastic inverse.
    """
    localized.LIMITS = dict(localized.LIMITS, maximum_union_dofs=limits["maximum_union_dofs"],
                            maximum_retained_dofs=limits["maximum_retained_dofs"])
    union_nodes, union_elements, keep, report = localized.make_union(np, sparse, prototype, configs)
    require(report["incidence_components"] == 1, "Disconnected wood requires an explicit multi-body quotient method")
    report.pop("expected_rigid_nulls_for_these_unbored_face_connected_fixtures", None)
    report.update(full_null_spectrum_assessed=False, connected_components_are_topology_only=True)
    retained = (3 * np.asarray(sorted(keep))[:, None] + np.arange(3)).ravel()
    K = helper.stiffness(union_nodes, union_elements, constants, swap)
    for config in configs:
        original = helper.stiffness(config["nodes"], config["elements"], constants, swap)
        difference = config["P"].T @ K @ config["P"] - original
        config["K_identity_relative"] = prototype.sparse_peak(np, difference) / max(1., prototype.sparse_peak(np, original))
        config["K_rigid_n_per_mm"] = prototype.peak(np, original @ config["Q"])
        require(config["K_identity_relative"] < 1e-13 and config["K_rigid_n_per_mm"] < 1e-5,
                "Original stiffness or rigid identity failed")
        del original, difference
    factors = []

    def factor(matrix, **kwargs):
        began = time.monotonic()
        event("factor_start", dofs=matrix.shape[0], matrix_nonzeros=int(matrix.nnz))
        result = splu(matrix, **kwargs)
        measured = {"dofs": matrix.shape[0], "matrix_nonzeros": int(matrix.nnz),
                    "stored_factor_nonzeros": int(result.nnz), "elapsed_seconds": time.monotonic() - began}
        factors.append(measured)
        event("factor_complete", **measured)
        cap = limits["maximum_global_factor_stored_nonzeros"] if len(factors) == 1 else limits["maximum_interface_factor_stored_nonzeros"]
        require(result.nnz <= cap, "Measured factor exceeds attempt bound; selected work stays pending")
        return result

    S_union, blocks, reduction = localized.condense_union(np, sparse, factor, helper, condensation, quotient,
                                                       union_nodes, union_elements, K, retained, prototype)
    for config in configs:
        raw, Q, P, dof_map = [config[k] for k in ("raw", "Q", "P", "dof_map")]
        projected = raw - Q @ (Q.T @ raw)
        Fs = localized.exact_source_lift(np, projected, dof_map)
        require(np.array_equal(P.T @ Fs, projected), "Projected original RHS export differs")
        ports = np.unique(dof_map[retained])
        T = sparse.csr_matrix((np.ones(len(retained)),
                              (np.arange(len(retained)), np.searchsorted(ports, dof_map[retained]))),
                             shape=(len(retained), len(ports)))
        S = (T.T @ S_union @ T).tocsr()
        quotient_audit = quotient.audit_quotient_operator(S, Q[ports])
        require(quotient_audit["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, "Original quotient rigid audit failed")
        fhat = np.zeros((len(retained), raw.shape[1]))
        constant = np.zeros(raw.shape[1])
        for block in blocks:
            Fi = Fs[block["i"]]
            inverse = block["factor"].solve(Fi)
            fhat[block["positions"]] = Fs[block["p"]] - block["Kpi"] @ inverse
            constant += .5 * np.sum(Fi * inverse, axis=0)
        fc = T.T @ fhat
        fixed = np.searchsorted(ports, config["fixed"])
        require(np.array_equal(ports[fixed], config["fixed"]), "Original gauges absent from retained ports")
        free = np.setdiff1d(np.arange(len(ports)), fixed)
        up = np.zeros(fc.shape)
        up[free] = factor(S[free][:, free].tocsc(), permc_spec="MMD_AT_PLUS_A").solve(fc[free])
        latent = np.zeros(Fs.shape)
        latent[retained] = T @ up
        for block in blocks:
            latent[block["i"]] = block["factor"].solve(Fs[block["i"]] - block["Kip"] @ latent[block["p"]])
        first = np.unique(dof_map, return_index=True)[1]
        recovered = latent[first]
        residual = P.T @ (K @ latent - Fs)
        require(np.array_equal(latent, recovered[dof_map]), "Recovered source ties differ")
        recovered -= Q @ (Q.T @ recovered)
        # A second projection removes accumulated reduction roundoff only.
        recovered -= Q @ (Q.T @ recovered)
        energy = .5 * np.sum(raw * recovered, axis=0)
        condensed = .5 * np.sum(fc * up, axis=0) + constant
        error = prototype.peak(np, (condensed - energy) / np.maximum(abs(energy), 1e-12))
        relative_rigid = prototype.peak(np, config["R"].T @ recovered)
        force_error = prototype.peak(np, residual)
        require(force_error < 1e-5 and error < 1e-8 and relative_rigid < 2e-10
                and np.min(energy) >= -1e-8, "Recovered quotient force/work/gauge identity failed")
        config.update(U=recovered, projected=projected, residual=residual, constant=constant,
                      solution_audit={"all_passed": True, "checks": {
                          "exact_original_K_and_node_identity": True, "original_rigid_operator": True,
                          "original_full_field_ties": True, "projected_full_force_equilibrium": True,
                          "orthogonal_rigid_pose_removed": True, "interior_constant_energy_identity": True},
                          "maximum_projected_force_residual_n": force_error,
                          "maximum_R_transpose_U_mm": relative_rigid,
                          "relative_energy_identity_error": error, "quotient_audit": quotient_audit})
        event("operator_field_recovered", configuration=config["id"], **config["solution_audit"])
    return report, reduction, factors


def mapping_known_answer(output, core_sha256, wall_seconds=45):
    """Parent-run small source-side mapping and projected inverse known answer."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "Fresh owned known-answer child required")
    require(sha(CORE) == core_sha256, "Frozen replacement API differs")
    pins = {p: h for p, h in EXPECTED.items() if p in (PROTOTYPE, LOCALIZED, KERNEL, PLANE, RADIAL)}
    bind(pins, CORE, core_sha256)
    bind(pins, Path(__file__).resolve(), sha(Path(__file__)))
    authenticate(pins)
    started = time.monotonic()
    output.mkdir(parents=True)

    def event(stage, **details):
        value = {"stage": stage, "elapsed_seconds": time.monotonic() - started, **details}
        write(output / "progress.json", value)
        print(json.dumps(value, sort_keys=True, allow_nan=False), flush=True)

    def timeout(_signal, _frame):
        raise TimeoutError("Known-answer attempt expired; no method pass")

    previous_handler = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(wall_seconds)
    status = "STOP_MAPPING_OPERATOR_KNOWN_ANSWER"
    try:
        prototype, localized = module(PROTOTYPE, "coupled_native_helpers"), module(LOCALIZED, "coupled_localized_helper")
        _, helper, condensation, quotient, np, sparse, splu, qr, scenario, _, kernel_pins = prototype.setup()
        for p, h in kernel_pins.items():
            bind(pins, p, h)
        core = module(CORE, "coupled_member_replacement_api")
        geometry = {"length_mm": 30., "width_mm": 20., "depth_mm": 20., "actual_volume_mm3": 12000.,
                    "frame": [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]],
                    "start": [-20., 10., 5.], "recess_source": None, "bores": []}
        datum = np.array([-18., 11., 17.])
        terms = [{"port_row": i, "point_mm": point, "force_global_xyz_per_unit_port_force": force,
                  "free_couple_global_xyz_mm_per_unit_port_force": moment,
                  "role": "timber_or_panel_contact" if i == 2 else "candidate_bolt_lateral_plane"}
                 for i, (point, force, moment) in enumerate((
                     ([-12., 15., 30.], [1., -.3, .2], [3., 2., -1.]),
                     ([-28., 6., 10.], [-.2, .4, 1.], [-1., 4., 2.]),
                     ([-12., 15., 35.], [0., 0., 1.], [0., 0., 0.])))]
        expected = []
        for term in terms:
            f = np.asarray(term["force_global_xyz_per_unit_port_force"])
            m = np.asarray(term["free_couple_global_xyz_mm_per_unit_port_force"])
            expected.append(np.r_[f, (np.cross(np.asarray(term["point_mm"]) - datum, f) + m) / 1000.])
        expected = np.asarray(expected)
        # Construct an exact source affine basis on the eight source corners.
        # This supplies all nine first moments, including the couple dipoles.
        source_local = np.array([[g, u, v] for g in (0., 30.) for u in (-10., 10.) for v in (-10., 10.)])
        source_world = np.asarray(geometry["start"]) + source_local @ np.asarray(geometry["frame"])
        A = np.column_stack((np.ones(len(source_world)), source_world - datum)).T
        source_values = []
        for term in terms:
            force = np.asarray(term["force_global_xyz_per_unit_port_force"])
            mx, my, mz = term["free_couple_global_xyz_mm_per_unit_port_force"]
            skew = np.array([[0., -mz, my], [mz, 0., -mx], [-my, mx, 0.]])
            first = np.outer(np.asarray(term["point_mm"]) - datum, force) - skew / 2
            target = np.vstack((force, first))
            source_values.append((A.T @ np.linalg.solve(A @ A.T, target)).ravel())
        original_B = sparse.csr_matrix(np.asarray(source_values))
        weights = np.arange(1., 37.).reshape(3, 12) / 37.
        source_body = {"B": original_B, "F": original_B.T @ weights,
                       "labels": [(i, c) for i in range(len(source_world)) for c in (1, 2, 3)],
                       "coordinates": dict(enumerate(source_world)), "datum_mm": datum}
        constants = scenario()["calculix_engineering_constants"]
        limits = {"maximum_union_dofs": 1800, "maximum_retained_dofs": 800,
                  "maximum_global_factor_stored_nonzeros": 2000000,
                  "maximum_interface_factor_stored_nonzeros": 1000000}
        records = []
        for swap in (False, True):
            configs = []
            first_cloud = None
            for role, interval in (("intact", None), ("initial", [25., 30.]), ("final", [20., 30.])):
                nodes, elements, census = helper.mesh(geometry, 10., 1, 0., crack_interval=interval)
                R, Q, world = rigid_basis(np, nodes, geometry, datum)
                B, active, mapper_audit = map_port_basis(np, sparse, helper, nodes, geometry, terms, 3, 1, 0., source_body)
                require(prototype.peak(np, B @ R - expected) < 1e-8, "Physical rigid force/moment map failed")
                # Twelve distinct source load columns exercise every L cross term.
                F, external_audit = map_external_basis(np, sparse, nodes, elements, geometry, source_body, 1, 0.)
                raw = np.column_stack((B.T.toarray(), F))
                nonzero = np.flatnonzero(np.any(abs(raw.reshape(len(nodes), 3, raw.shape[1])) > 1e-15, axis=(1, 2)))
                order = sorted(nonzero.tolist(), key=lambda i: tuple(nodes[i]))
                cloud = np.column_stack((nodes[order], raw.reshape(len(nodes), -1)[order]))
                if first_cloud is None:
                    first_cloud = cloud
                require(cloud.shape == first_cloud.shape and prototype.peak(np, cloud - first_cloud) < 1e-11,
                        "Crack configuration changed a physical port/body-load affine footprint")
                fixed = qr(Q.T, mode="economic", pivoting=True)[2][:6]
                require(np.linalg.matrix_rank(Q[fixed]) == 6 and np.linalg.cond(Q[fixed]) < 1e6,
                        "Small source gauge rank/condition failed")
                configs.append({"id": role, "interval": interval, "nodes": nodes, "elements": elements,
                                "census": census, "R": R, "Q": Q, "world": world, "B": B, "external_F": F,
                                "active": active, "raw": raw, "fixed": fixed, "mapper_audit": mapper_audit,
                                "external_mapper_audit": external_audit})
            report, reduction, factors = localized_solutions(np, sparse, splu, prototype, helper, condensation,
                quotient, localized, configs, constants, swap, event, limits)
            operators = []
            for config in configs:
                K = helper.stiffness(config["nodes"], config["elements"], constants, swap)
                reference_U, _ = helper.elastic_response(K, config["nodes"], config["projected"])
                reference_U -= config["Q"] @ (config["Q"].T @ reference_U)
                operator = core.reduce_body_from_solutions(config["B"], config["external_F"], config["R"],
                    config["U"][:, :3], config["U"][:, 3:], config["solution_audit"], K=K)
                reference_operator = core.reduce_body_from_solutions(config["B"], config["external_F"], config["R"],
                    reference_U[:, :3], reference_U[:, 3:], {"all_passed": True}, K=K)
                delta = prototype.peak(np, reference_U - config["U"]) / max(1e-12, prototype.peak(np, reference_U))
                errors = {name: prototype.peak(np, operator[name] - reference_operator[name]) /
                          max(1e-12, prototype.peak(np, reference_operator[name])) for name in ("H", "e", "L", "D", "W")}
                require(delta < 1e-8 and max(errors.values()) < 1e-8, "Localized projected operator differs from monolithic known answer")
                affine = np.array([[.001, -.002, .003], [.004, .001, -.002], [-.003, .002, .001]])
                translation = np.array([.2, -.1, .3])
                local_motion = ((config["world"] @ affine.T + translation) @ np.asarray(geometry["frame"]).T).ravel()
                work = config["B"] @ local_motion
                answer = np.array([np.asarray(t["force_global_xyz_per_unit_port_force"]) @
                                   (affine @ np.asarray(t["point_mm"]) + translation)
                                   + np.asarray(t["free_couple_global_xyz_mm_per_unit_port_force"]) @
                                   np.array([affine[2, 1] - affine[1, 2], affine[0, 2] - affine[2, 0],
                                             affine[1, 0] - affine[0, 1]]) / 2 for t in terms])
                affine_error = prototype.peak(np, work - answer)
                require(affine_error < 1e-8, "Complete original affine strain virtual work failed")
                rigid_motion = config["R"] @ np.array([.2, -.1, .3, 2., -3., 4.])
                rigid_error = prototype.peak(np, config["B"] @ rigid_motion - expected @ np.array([.2, -.1, .3, 2., -3., 4.]))
                require(rigid_error < 1e-8, "Mapped rigid virtual work failed")
                field = output / (("v-" if swap else "u-") + config["id"] + "-fields.npz")
                np.savez_compressed(field, nodes_mm=config["nodes"], elements=config["elements"],
                                    original_raw_rhs=config["raw"], projected_rhs=config["projected"],
                                    recovered_U_mm=config["U"], monolithic_U_mm=reference_U,
                                    residual_n=config["residual"], physical_R=config["R"],
                                    port_B=config["B"].toarray(), external_F=config["external_F"],
                                    **{name: operator[name] for name in ("H", "e", "L", "D", "W")})
                operators.append({"configuration": config["id"], "mesh": config["census"], "field": reference(field),
                                  "relative_U_error": delta, "relative_operator_errors": errors,
                                  "rigid_virtual_work_error_nmm": rigid_error,
                                  "general_affine_virtual_work_error_nmm": affine_error,
                                  "complete_native_force_and_nine_first_moments_retained": True,
                                  "physical_port_mapping_audit": config["mapper_audit"],
                                  "external_body_load_mapping_audit": config["external_mapper_audit"],
                                  "solution_audit": config["solution_audit"], "operator_audit": operator["audit"]})
            records.append({"RT_binding": "R=v,T=-u" if swap else "R=u,T=v", "union": report,
                            "reduction": reduction, "factors": factors, "operators": operators})
        status = "PASS_SOURCE_SIDE_MAPPING_AND_LOCALIZED_OPERATOR_KNOWN_ANSWER"
        result = {"schema": "splitting_coupled_interface_operator_known_answer/v1", "status": status,
                  "records": records, "configurations": 6, "external_load_basis_columns": 12,
                  "full_assembly_energy_known_answer_replaced": False,
                  "source_moment_and_rigid_virtual_work_retained": True,
                  "same_physical_footprints_across_intact_initial_final": True,
                  "normal_contact_nonnegative_scalar_traction_assessed": True,
                  "unbalanced_unit_columns_projected_only_for_elastic_inverse": True,
                  "project_body_domain_or_resource_feasibility_transferred": False,
                  "physical_or_complete_joint_acceptance": False}
        write(output / "result.json", result)
        authenticate(pins)
    except BaseException as exc:
        write(output / "stop.json", {"status": status, "exception": type(exc).__name__, "message": str(exc),
                                     "method_pass": False, "selected_work_pending": True})
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)
        write(output / "receipt.json", {"schema": "splitting_coupled_interface_operator_receipt/v1", "status": status,
              "source_sha256": {source_key(p): h for p, h in pins.items()},
              "source_before": {source_key(p): h for p, h in pins.items()}, "source_after": {source_key(p): sha(p) for p in pins},
              "output_sha256": {p.relative_to(output).as_posix(): sha(p) for p in output.rglob("*") if p.is_file()
                                and p.name != "receipt.json"}, "elapsed_seconds": time.monotonic() - started,
              "maximum_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "numerical_solid_solve_executed": True, "no_external_native_solver_or_CAD_executable": True,
              "physical_or_complete_joint_acceptance": False})
    return {"status": status, "result": reference(output / "result.json"), "receipt": reference(output / "receipt.json")}


def bind_cached_receipt(pins, path, resolutions):
    """Resolve only a changed producer to its exact declared frozen snapshot."""
    record = read(path)
    bind(pins, path, sha(path))
    candidates = [path.parent / name for name in record["output_sha256"] if name.endswith("producer.py.snapshot")]
    candidates += [ROOT / name for name in record["source_sha256"] if name.endswith("producer.py.snapshot")]
    for name, value in record["source_sha256"].items():
        source = ROOT / name
        if source == CORE and sha(source) != value:
            matches = [p for p in candidates if p.is_file() and sha(p) == value]
            require(len(matches) == 1, "Changed cached API producer lacks one exact snapshot")
            source = matches[0]
            resolutions.append({"source_key": name, "expected_sha256": value,
                                "resolved_path": key(source), "resolution": "DECLARED_EXACT_PRODUCER_SNAPSHOT"})
        bind(pins, source, value)
    for name, value in record["output_sha256"].items():
        bind(pins, path.parent / name, value)
    return record


def resolution_contract(records):
    return {item["source_key"]: {"original_path": item["source_key"],
                                "snapshot_path": item["resolved_path"], "sha256": item["expected_sha256"]}
            for item in records}


def cached_body(core, packet, pins, resolutions):
    """Reuse the frozen API loader with a narrowly replaced source binder."""
    tree = ast.parse(CORE.read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "load_source_body")
    edits = []

    class CachedBinding(ast.NodeTransformer):
        def visit_Call(self, node):
            self.generic_visit(node)
            if ast.unparse(node.func) == "compatibility().bind_packet":
                edits.append(ast.unparse(node))
                node.func = ast.Name(id="declared_cached_body_binding", ctx=ast.Load())
            return node

    adapted = ast.fix_missing_locations(ast.Module(body=[CachedBinding().visit(function)], type_ignores=[]))
    require(edits == ["compatibility().bind_packet(packet, pins)"], "Cached source loader binder changed")
    namespace = dict(core.__dict__)

    def declared_binding(actual_packet, local_pins):
        require(actual_packet == packet, "Cached loader changed the requested input packet")
        record = bind_cached_receipt(pins, actual_packet / "receipt.json", resolutions)
        local_pins.update(pins)
        authenticate(pins)
        return record

    namespace["declared_cached_body_binding"] = declared_binding
    exec(compile(adapted, str(CORE), "exec"), namespace)  # noqa: S102 - Exact authenticated loader AST; one audited binder replacement.
    return namespace["load_source_body"](packet)


def prepare_native(output, selection, selection_sha256, mapping_proof, mesh_size, rt, core_sha256):
    """Freeze one three-configuration operator group, without numerical imports."""
    output, selection, mapping_proof = [Path(p).resolve() for p in (output, selection, mapping_proof)]
    require(output.parent == RAW.resolve() and not output.exists(), "Fresh owned native preparation required")
    require(sha(selection) == selection_sha256 and sha(CORE) == core_sha256, "Selected source/API changed")
    value = read(selection)
    require(value["schema"] == "splitting_representative_coupled_selection/v1", "Unbound selection schema")
    require(mesh_size in (20., 15.) and rt in ("R=u,T=v", "R=v,T=-u"), "Unbound field grid/material orientation")
    pins, resolutions = {}, []
    bind_receipt(pins, selection.parent / "receipt.json")
    bind_receipt(pins, mapping_proof / "receipt.json")
    require(read(mapping_proof / "result.json")["status"] == "PASS_SOURCE_SIDE_MAPPING_AND_LOCALIZED_OPERATOR_KNOWN_ANSWER",
            "Source mapping/operator known answer did not pass")
    cached = bind_cached_receipt(pins, CACHE / "receipt.json", resolutions)
    old = bind_cached_receipt(pins, OLD_OPERATORS / "receipt.json", resolutions)
    require(cached["status"] == "EXPORTED_ORIGINAL_NATIVE_BODY_WITHOUT_FACTOR"
            and old["status"] == "PASS_SOURCE_BODY_REMOVE_REINSERT", "Old source body/cache did not pass")
    bind(pins, CORE, core_sha256)
    bind(pins, Path(__file__).resolve(), sha(Path(__file__)))
    allocation = module(ALLOCATION, "coupled_proved_allocation_binding")
    for path, h in allocation.bindings().items():
        bind(pins, path, h)
    variants = [r for r in value["operator_variants"] if r["mesh_size_mm"] == mesh_size and r["RT_binding"] == rt]
    require(len(variants) == 3 and {v["configuration"] for v in variants} == {"intact", "initial", "final"},
            "One exact three-configuration group required")
    bind(pins, BODY_RESULT, EXPECTED[BODY_RESULT])
    geometry_row = next(r for r in read(BODY_RESULT)["records"] if r["path"] == variants[0]["path"]
                        and r["mesh_size_mm"] == mesh_size and r["RT_binding"] == rt)
    geometry_reuse = {}
    for phase in ("intact", "initial", "final"):
        checkpoint = geometry_row[phase + "_checkpoint"]
        checkpoint_path = ROOT / checkpoint["path"]
        bind(pins, checkpoint_path, checkpoint["sha256"])
        old_checkpoint = read(checkpoint_path)
        field = old_checkpoint["retained_field"]
        bind(pins, ROOT / field["path"], field["sha256"])
        geometry_reuse[phase] = {"checkpoint": checkpoint, "retained_field": field,
                                 "mesh": old_checkpoint["mesh"], "scope": "GEOMETRY_AND_MESH_ONLY_NO_FORCE_TRANSFER"}
    limits = {"address_space_bytes": 10 * 1024**3, "wall_seconds": 1800,
              "maximum_union_dofs": 68000, "maximum_retained_dofs": 1200,
              "maximum_global_factor_stored_nonzeros": 650000000,
              "maximum_interface_factor_stored_nonzeros": 1200**2 + 1200}
    output.mkdir(parents=True)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    pins.pop(Path(__file__).resolve())
    bind(pins, output / "producer.py.snapshot", sha(output / "producer.py.snapshot"))
    job = {"schema": "splitting_coupled_body_operator_job/v1", "selection": reference(selection),
           "operator_variants": variants, "mesh_size_mm": mesh_size, "RT_binding": rt,
           "core": reference(CORE), "cached_body": reference(CACHE / "receipt.json"),
           "old_body_operators": reference(OLD_OPERATORS / "old-body-operators.npz"),
           "assembled_known_answer": reference(OLD_OPERATORS / "known-answer.json"),
           "mapping_known_answer": reference(mapping_proof / "result.json"),
           "physical_port_terms": reference(selection.parent / "physical-port-terms.json"),
           "preserved_geometry_only_reuse": geometry_reuse,
           "source_sha256": {source_key(p): h for p, h in pins.items()}, "source_resolution": resolutions,
           "stiffness_installation": {"path": key(ALLOCATION), "sha256": sha(ALLOCATION), "element_chunk": 1024},
           "limits": limits, "geometry_changed": False, "new_CAD_or_external_native_executable": False,
           "operator_field_only": True, "assembled_equilibrium_executed": False,
           "resource_bound_is_attempt_allowance_not_domain_disposition": True,
           "measured_source_count_basis": "Previously bounded same geometry 20/15 grids, with strict new actual union/ports/volume/bore/mapping gates before factors; new physical rigid datum may change QR gauge selection.",
           "native_factor_budget": {"global_interior": 1, "interfaces": 3}}
    write(output / "job.json", job)
    authenticate(pins)
    write(output / "receipt.json", {"schema": "splitting_coupled_body_operator_preparation/v1", "status": "PREPARED_NATIVE_OPERATOR_GROUP",
          "source_sha256": {source_key(p): h for p, h in pins.items()}, "source_resolution": resolution_contract(resolutions),
          "output_sha256": {name: sha(output / name) for name in ("job.json", "producer.py.snapshot")},
          "native_operator_construction_executed": False, "assembled_equilibrium_executed": False})
    return {"status": "PREPARED_NATIVE_OPERATOR_GROUP", "job": reference(output / "job.json"),
            "executing_snapshot": reference(output / "producer.py.snapshot"), "receipt": reference(output / "receipt.json"),
            "native_factor_budget": job["native_factor_budget"], "limits": limits}


def operators(output, job_path, job_sha256):
    """Parent-serialized actual bored/cracked body compliance operators."""
    output, job_path = Path(output).resolve(), Path(job_path).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "Fresh owned operator output required")
    require(sha(job_path) == job_sha256, "Native operator job changed")
    job = read(job_path)
    require(job["schema"] == "splitting_coupled_body_operator_job/v1", "Unbound operator job schema")
    pins = {ROOT / p: h for p, h in job["source_sha256"].items()}
    bind(pins, job_path, job_sha256)
    bind(pins, Path(__file__).resolve(), sha(Path(__file__)))
    authenticate(pins)
    limits, resolutions = job["limits"], list(job["source_resolution"])
    started = time.monotonic()
    output.mkdir(parents=True)
    status = "STOP_COUPLED_BODY_OPERATOR_GROUP"
    numerical_solve_executed = False

    def event(stage, **details):
        event_record = {"stage": stage, "elapsed_seconds": time.monotonic() - started, **details}
        write(output / "progress.json", event_record)
        print(json.dumps(event_record, sort_keys=True, allow_nan=False), flush=True)

    def timeout(_signal, _frame):
        raise TimeoutError("Parent native operator attempt expired; selected work stays pending")

    previous_handler = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(limits["wall_seconds"])
    previous_limit = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (limits["address_space_bytes"], previous_limit[1]))
    try:
        core = module(CORE, "actual_coupled_member_replacement")
        prototype, localized = module(PROTOTYPE, "actual_coupled_native_helpers"), module(LOCALIZED, "actual_coupled_localized_helper")
        _, helper, condensation, quotient, np, sparse, splu, qr, scenario, _, kernel_pins = prototype.setup()
        for p, h in kernel_pins.items():
            bind(pins, p, h)
        allocation = module(ALLOCATION, "actual_coupled_allocation_installation")
        assembly_metadata = allocation.install(helper, job, pins)
        original_grid = helper.mesh_grids
        radial, plane_method = module(RADIAL, "coupled_radial_partition"), module(PLANE, "coupled_plane_partition")

        def corrected_grid(geometry, size, axis, plane, coupon=False, grain_factor=4.):
            original = original_grid(geometry, size, axis, plane, coupon, grain_factor)
            aligned, _ = plane_method.resolve_selected_plane(np, original, axis, plane)
            return radial.correct_radial_partitions(np, aligned, geometry["bores"])[0]

        helper.mesh_grids = corrected_grid
        original_body = cached_body(core, CACHE, pins, resolutions)
        require(original_body["member_id"] == "center_post_cleat_left" and len(original_body["R"]) == 60,
                "Original selected body cache differs")
        geometry = read(OLD / "coupled-prepared01/geometry.json")[original_body["member_id"]]
        terms = read(ROOT / job["physical_port_terms"]["path"])["terms"]
        expected_active = np.flatnonzero(np.diff(original_body["B"].indptr))
        require(np.array_equal(expected_active, sorted({t["port_row"] for t in terms})),
                "Some original native B ports lack physical term authority")
        constants, swap = scenario()["calculix_engineering_constants"], job["RT_binding"] == "R=v,T=-u"
        configs, fixed_cloud = [], None
        for variant in job["operator_variants"]:
            require(variant["geometry_sha256"] == digest(geometry), "Frozen target geometry changed")
            path, interval = variant["path"], variant["crack_interval_mm"]
            event("original_actual_mesh", configuration=variant["configuration"])
            nodes, elements, census = helper.mesh(geometry, job["mesh_size_mm"], path["axis"], path["plane_mm"], crack_interval=interval)
            previous_geometry = job["preserved_geometry_only_reuse"][variant["configuration"]]
            with np.load(ROOT / previous_geometry["retained_field"]["path"], allow_pickle=False) as saved:
                require(np.array_equal(nodes, saved["nodes_mm"]) and np.array_equal(elements, saved["elements"]),
                        "Selected actual mesh differs from its preserved geometry-only evidence")
            require(census == previous_geometry["mesh"], "Selected actual bore/volume/front geometry census differs")
            R, Q, _ = rigid_basis(np, nodes, geometry, original_body["datum_mm"])
            B, active, mapping = map_port_basis(np, sparse, helper, nodes, geometry, terms,
                                               original_body["B"].shape[0], path["axis"], path["plane_mm"], original_body)
            F, external_mapping = map_external_basis(np, sparse, nodes, elements, geometry, original_body,
                                                     path["axis"], path["plane_mm"])
            rigid_port_error = prototype.peak(np, B @ R - original_body["D"])
            rigid_external_error = prototype.peak(np, R.T @ F - original_body["W"])
            require(rigid_port_error < 1e-8 and rigid_external_error < 1e-8, "Original D/W source wrench/rigid work differs")
            raw = np.column_stack((B[active].T.toarray(), F))
            nonzero = np.flatnonzero(np.any(abs(raw.reshape(len(nodes), 3, raw.shape[1])) > 1e-15, axis=(1, 2)))
            order = sorted(nonzero.tolist(), key=lambda i: tuple(nodes[i]))
            cloud = np.column_stack((nodes[order], raw.reshape(len(nodes), -1)[order]))
            if fixed_cloud is None:
                fixed_cloud = cloud
            require(cloud.shape == fixed_cloud.shape and prototype.peak(np, cloud - fixed_cloud) < 1e-10,
                    "Intact/crack variants changed the frozen physical port/external basis footprint")
            fixed = qr(Q.T, mode="economic", pivoting=True)[2][:6]
            condition = float(np.linalg.cond(Q[fixed]))
            require(np.linalg.matrix_rank(Q[fixed]) == 6 and condition < 1e6, "Actual scalar gauge rank/condition failed")
            configs.append({"id": variant["id"], "variant": variant, "interval": interval,
                            "nodes": nodes, "elements": elements, "census": census, "R": R, "Q": Q,
                            "B": B, "external_F": F, "active": active, "raw": raw, "fixed": fixed,
                            "mapping": mapping, "external_mapping": external_mapping,
                            "D_source_error": rigid_port_error, "W_source_error": rigid_external_error,
                            "gauge_condition": condition})
            write(output / (variant["configuration"] + "-mapping.json"), {"variant": variant,
                  "port_mapping": mapping, "external_mapping": external_mapping,
                  "source_D_error": rigid_port_error, "source_W_error": rigid_external_error, "mesh": census})
        numerical_solve_executed = True
        union, reduction, factors = localized_solutions(np, sparse, splu, prototype, helper, condensation,
            quotient, localized, configs, constants, swap, event, limits)
        results = []
        for config in configs:
            count = len(config["active"])
            op = core.reduce_body_from_solutions(config["B"], config["external_F"], config["R"],
                                                config["U"][:, :count], config["U"][:, count:], config["solution_audit"])
            filename = config["variant"]["configuration"] + "-operator.npz"
            np.savez_compressed(output / filename, **{k: op[k] for k in ("H", "e", "L", "D", "W")},
                                nodes_mm=config["nodes"], elements=config["elements"], physical_R=config["R"],
                                external_F_n=config["external_F"], active_port_rows=config["active"],
                                U_B_mm=config["U"][:, :count], U_F_mm=config["U"][:, count:],
                                port_B_data=config["B"].data, port_B_indices=config["B"].indices,
                                port_B_indptr=config["B"].indptr, port_B_shape=np.asarray(config["B"].shape),
                                projected_rhs_n=config["projected"], projected_residual_n=config["residual"],
                                original_scalar_gauges=config["fixed"])
            checks = {"source_port_order_and_body_ownership": True, "same_external_load_basis_and_rigid_work": True,
                      "source_side_footprint_wrench_and_affine_work": True, "actual_profile_bore_volume_and_crack_area": True,
                      "original_mesh_and_stiffness_identity": True, "rigid_quotient_and_gauge": True,
                      "port_compliance_reciprocity_and_load_cross_terms": True}
            metadata = {"schema": "splitting_coupled_body_operator/v1", "variant": config["variant"],
                        "operator_ref": reference(output / filename), "mesh": config["census"],
                        "mapping_ref": reference(output / (config["variant"]["configuration"] + "-mapping.json")),
                        "physical_audit": {"all_passed": True, "checks": checks,
                                           "solution": config["solution_audit"], "operator": op["audit"],
                                           "source_D_error": config["D_source_error"], "source_W_error": config["W_source_error"],
                                           "gauge_condition": config["gauge_condition"]},
                        "assembly_method": assembly_metadata, "assembled_response_executed": False,
                        "full_null_spectrum_assessed": False, "physical_release": False}
            write(output / (config["variant"]["configuration"] + "-operator.json"), metadata)
            results.append(metadata)
        status = "PASS_ACTUAL_COUPLED_BODY_OPERATOR_GROUP"
        write(output / "result.json", {"schema": "splitting_coupled_body_operator_group/v1", "status": status,
              "job_binding": reference(job_path), "operators": results, "union": union, "reduction": reduction,
              "factors": factors, "native_operator_count": 3, "assembled_equilibrium_executed": False,
              "splitting_workstream_complete": False, "physical_release": False})
        authenticate(pins)
    except BaseException as exc:
        write(output / "stop.json", {"status": status, "exception": type(exc).__name__, "message": str(exc),
                                     "selected_obligations_pending": True, "permanent_method_exclusion": False})
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)
        write(output / "receipt.json", {"schema": "splitting_coupled_body_operator_receipt/v1", "status": status,
              "source_sha256": {source_key(p): h for p, h in pins.items()}, "source_resolution": resolution_contract(resolutions),
              "source_before": {source_key(p): h for p, h in pins.items()}, "source_after": {source_key(p): sha(p) for p in pins},
              "output_sha256": {p.relative_to(output).as_posix(): sha(p) for p in output.rglob("*") if p.is_file()
                                and p.name != "receipt.json"}, "elapsed_seconds": time.monotonic() - started,
              "maximum_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "numerical_solid_solve_executed": numerical_solve_executed,
              "no_external_native_solver_or_CAD_executable": True, "physical_or_complete_joint_acceptance": False})
    return {"status": status, "result": reference(output / "result.json"), "receipt": reference(output / "receipt.json")}


def prepare_assembled(output, selection, selection_sha256, operator_packet, operator_receipt_sha256,
                      state_tags, core_sha256):
    """Freeze a small assembled replay of already solved native operators."""
    output, selection, operator_packet = [Path(p).resolve() for p in (output, selection, operator_packet)]
    require(output.parent == RAW.resolve() and not output.exists(), "Fresh owned assembled preparation required")
    require(sha(selection) == selection_sha256 and sha(CORE) == core_sha256
            and sha(operator_packet / "receipt.json") == operator_receipt_sha256, "Assembled preparation inputs changed")
    selected, group = read(selection), read(operator_packet / "result.json")
    require(group["status"] == "PASS_ACTUAL_COUPLED_BODY_OPERATOR_GROUP"
            and "baseline_eligibility_binding" in selected, "Passed operators and frozen current baseline eligibility required")
    require(state_tags and len(set(state_tags)) == len(state_tags)
            and set(state_tags) <= {s["state_tag"] for s in selected["required_state_dispositions"]},
            "Requested state lies outside eligible current baseline")
    ids = {item["variant"]["id"] for item in group["operators"]}
    require(len(ids) == 3 and ids <= {v["id"] for v in selected["operator_variants"]}, "Unbound native operator group")
    comparisons = [r for r in selected["required_comparisons"] if r["state_tag"] in state_tags
                   and set(r["operator_variants"].values()) == ids]
    require(len(comparisons) == len(state_tags), "One group/state must select one literal comparison")
    pins, resolutions = {}, []
    bind_receipt(pins, selection.parent / "receipt.json")
    bind_cached_receipt(pins, operator_packet / "receipt.json", resolutions)
    bind_cached_receipt(pins, OLD_OPERATORS / "receipt.json", resolutions)
    bind(pins, CORE, core_sha256)
    bind(pins, Path(__file__).resolve(), sha(Path(__file__)))
    operator_job = read(ROOT / group["job_binding"]["path"])
    mapping_answer = operator_job["mapping_known_answer"]
    mapping_receipt = reference((ROOT / mapping_answer["path"]).parent / "receipt.json")
    output.mkdir(parents=True)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    pins.pop(Path(__file__).resolve())
    bind(pins, output / "producer.py.snapshot", sha(output / "producer.py.snapshot"))
    job = {"schema": "splitting_coupled_assembled_job/v1", "selection_binding": reference(selection),
           "operator_group_binding": reference(operator_packet / "result.json"),
           "operator_group_receipt": reference(operator_packet / "receipt.json"),
           "required_comparisons": comparisons, "requested_state_tags": state_tags,
           "core": reference(CORE), "global_joint_update_binding": selected["global_joint_update_binding"],
           "baseline_eligibility_binding": selected["baseline_eligibility_binding"],
           "active_action_binding": selected["active_action_binding"],
           "old_body_operators": reference(OLD_OPERATORS / "old-body-operators.npz"),
           "assembled_known_answer": reference(OLD_OPERATORS / "known-answer.json"),
           "interface_mapping_known_answer": mapping_answer,
           "interface_mapping_known_answer_receipt": mapping_receipt,
           "source_sha256": {source_key(p): h for p, h in pins.items()}, "source_resolution": resolution_contract(resolutions),
           "stiffness_installation": {"path": key(ALLOCATION), "sha256": sha(ALLOCATION), "element_chunk": 1024},
           "limits": {"address_space_bytes": 10 * 1024**3, "wall_seconds": 1800},
           "equilibrium_method": "one_current_baseline_floor_mask_per_variant_state_v1",
           "maximum_conic_branch_calls": 3 * len(comparisons),
           "failed_source_mask_is_cracked_equilibrium_impossibility": False,
           "new_native_factorizations": 0, "local_stiffness_reassembled_for_full_residual_only": True,
           "force_exports_require_actual_variant_and_full_body_audits": True,
           "baseline_unavailable_states_executed": False, "physical_release": False}
    write(output / "job.json", job)
    authenticate(pins)
    write(output / "receipt.json", {"schema": "splitting_coupled_assembled_preparation_receipt/v1",
          "status": "PREPARED_BOUNDED_ASSEMBLED_REPLAY", "source_sha256": job["source_sha256"],
          "source_resolution": resolution_contract(resolutions),
          "output_sha256": {name: sha(output / name) for name in ("job.json", "producer.py.snapshot")},
          "assembled_equilibrium_executed": False, "physical_release": False})
    return {"job": reference(output / "job.json"), "executing_snapshot": reference(output / "producer.py.snapshot"),
            "receipt": reference(output / "receipt.json"), "selected_comparison_count": len(comparisons),
            "operator_state_count": 3 * len(comparisons), "new_native_factorizations": 0}


def fixed_baseline_state(core, frame, case, gap, bearing):
    """One existing conic branch, with unchanged full physical acceptance gates.

    A changed body may invalidate its baseline floor mask. That stopped branch
    remains pending; this bounded pilot does not rule out another valid mask.
    """
    solver = core.compatibility()
    c = core.load_coefficients(case, frame["dead_load_factor"])
    force, motion, rigid, details, audit = solver.fixed_floor_branch(
        frame["H"], frame["D"], frame["e"] @ c, frame["W"] @ c, frame["joint"], bearing, gap)
    require(audit["all_passed"], "Replacement baseline-mask branch failed unchanged original physical audit")
    energy = core.assembled_potential(force, motion, rigid, frame["H"], frame["e"], frame["W"],
        frame["L"], c, frame["joint"], gap, frame["energy_constant_scope"], frame["unchanged_constant_token"])
    return {"force": force, "motion": motion, "rigid": rigid, "bearing": bearing,
        "audit": audit, "energy": energy, "history": [{"step": 0,
            "bearing_footprints": [i for i, value in enumerate(bearing) if value],
            "solver": details, "original_physical_law_audit": audit,
            "baseline_floor_mask_only": True, "other_masks_unassessed": True}], "physical_release": False}


def assembled_replay(output, job_path, job_sha256):
    """Re-solve the original whole frame with one exact body replacement.

    Saved elastic inverse columns recover the local body. The same C3D20 K is
    reassembled for its full residual, without another body factorization.
    A rejected variant never exports an accepted reaction/body field.
    """
    output, job_path = Path(output).resolve(), Path(job_path).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "Fresh owned assembled output required")
    require(sha(job_path) == job_sha256, "Assembled replay job changed")
    job = read(job_path)
    require(job["schema"] == "splitting_coupled_assembled_job/v1", "Unbound assembled replay schema")
    require(job["equilibrium_method"] == "one_current_baseline_floor_mask_per_variant_state_v1"
            and job["maximum_conic_branch_calls"] == 3 * len(job["required_comparisons"]),
            "Bounded actual branch inventory changed")
    pins = {ROOT / name: value for name, value in job["source_sha256"].items()}
    bind(pins, job_path, job_sha256)
    bind(pins, Path(__file__).resolve(), sha(Path(__file__)))
    authenticate(pins)
    started = time.monotonic()
    output.mkdir(parents=True)
    status, records, dispositions = "STOP_BOUNDED_ASSEMBLED_REPLAY", [], []
    checkpoints = {}
    assembled_executed = False

    def event(stage, **details):
        record = {"stage": stage, "elapsed_seconds": time.monotonic() - started, **details}
        write(output / "progress.json", record)
        print(json.dumps(record, sort_keys=True, allow_nan=False), flush=True)

    def timeout(_signal, _frame):
        raise TimeoutError("Bounded assembled replay expired; unperformed selected work stays pending")

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(job["limits"]["wall_seconds"])
    old_limit = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (job["limits"]["address_space_bytes"], old_limit[1]))
    try:
        core = module(CORE, "representative_assembled_replacement")
        prototype = module(PROTOTYPE, "representative_assembled_native_helpers")
        _, helper, _, _, np, sparse, _, _, scenario, _, helper_pins = prototype.setup()
        for path, value in helper_pins.items():
            bind(pins, path, value)
        allocation = module(ALLOCATION, "representative_assembled_allocation")
        allocation.install(helper, job, pins)
        selected = read(ROOT / job["selection_binding"]["path"])
        group = read(ROOT / job["operator_group_binding"]["path"])
        frame = core.load_frame()
        for path, value in frame["source_sha256"].items():
            bind(pins, path, value)
        frame = core.apply_joint_update(frame, read(ROOT / job["global_joint_update_binding"]["path"]))
        with np.load(ROOT / job["old_body_operators"]["path"], allow_pickle=False) as data:
            old_operator = {name: data[name].copy() for name in ("H", "e", "L", "D", "W")}
        source_frame_binding = job["baseline_eligibility_binding"]["receipt"]
        original_native_frame_binding = reference(core.FRAME / "receipt.json")
        # The receipt identifies this fixed baseline branch's omitted body-load
        # constant. Its unknown value cancels only within the same branch.
        frame = core.attach_body_load_energy(frame, [old_operator],
                                            unchanged_constant_token=source_frame_binding["sha256"])
        body_id = read(CACHE / "source-body.json")["body_id"]
        require(body_id == 22, "Selected original body rigid coordinate ownership changed")
        baseline_packet = (ROOT / job["baseline_eligibility_binding"]["receipt"]["path"]).parent
        baseline_response = np.load(baseline_packet / "response.npz", allow_pickle=False)
        geometry = read(ROOT / selected["operator_variants"][0]["geometry_binding"]["path"])["center_post_cleat_left"]
        external_contract = {"schema": "splitting_coupled_external_basis_contract/v1",
             "source_frame_binding": source_frame_binding, "original_native_frame_binding": original_native_frame_binding,
             "native_source_body_binding": reference(CACHE / "receipt.json"),
             "original_complete_twelve_column_F_W_retained": True,
             "baseline_eligibility_binding": job["baseline_eligibility_binding"],
             "active_action_binding": job["active_action_binding"], "dead_load_factor": frame["dead_load_factor"],
             "same_source_external_basis_between_crack_phases": True,
             "same_interface_reaction_between_crack_phases_required": False}
        footprint_contract = {"schema": "splitting_coupled_physical_footprint_contract/v1",
             "native_source_B_authority": reference(CACHE / "source-body-B.npz"),
             "native_source_body_basis": reference(CACHE / "source-body.npz"),
             "original_force_and_all_nine_first_moments_preserved": True,
             "retained_physical_source_side_only": True, "contact_normal_scalar_weights_nonnegative": True,
             "crack_seam_nodes_excluded_without_stitching": True,
             "bilateral_bolt_and_consistent_external_body_forces_are_declared_separately": True,
             "actual_operator_mapping_records": [item["mapping_ref"] for item in group["operators"]],
             "operator_group_binding": job["operator_group_binding"], "geometry_sha256": digest(geometry),
             "working_joint_update_binding": job["global_joint_update_binding"]}
        write(output / "external-load-contract.json", external_contract)
        write(output / "port-footprint-contract.json", footprint_contract)
        contracts = {name: reference(output / filename) for name, filename in
                     (("external_load", "external-load-contract.json"), ("port_footprint", "port-footprint-contract.json"))}
        constants = scenario()["calculix_engineering_constants"]
        for metadata in group["operators"]:
            variant, phase = metadata["variant"], metadata["variant"]["configuration"]
            operator_path = ROOT / metadata["operator_ref"]["path"]
            with np.load(operator_path, allow_pickle=False) as saved:
                native = {name: saved[name].copy() for name in saved.files}
            B = sparse.csr_matrix((native["port_B_data"], native["port_B_indices"], native["port_B_indptr"]),
                                  shape=tuple(native["port_B_shape"]))
            active, nodes, elements = native["active_port_rows"], native["nodes_mm"], native["elements"]
            target = {name: native[name] for name in ("H", "e", "L", "D", "W")}
            assembled = core.replacement(frame, old_operator, target)
            # The only selected load-energy contribution is now the new body.
            require(prototype.peak(np, assembled["L"] - target["L"]) < 1e-12,
                    "Old body L was not removed exactly once")
            event("recover_full_body_stiffness_without_factor", operator_variant_id=variant["id"])
            K = helper.stiffness(nodes, elements, constants, variant["RT_binding"] == "R=v,T=-u")
            for identity in job["required_comparisons"]:
                require(identity["operator_variants"][phase] == variant["id"], "Actual phase is outside declared comparison")
                tag, case, gap = identity["state_tag"], identity["case_id"], identity["gap_scale"]
                event("assembled_variant_state", phase=phase, state_tag=tag, operator_variant_id=variant["id"])
                assembled_executed = True
                state = fixed_baseline_state(core, assembled, case, gap, baseline_response[tag + "_bearing"].copy())
                c, f = np.asarray(state["energy"]["external_coefficients"]), state["force"]
                recovered = native["U_F_mm"] @ c - native["U_B_mm"] @ f[active]
                force = native["external_F_n"] @ c - B.T @ f
                total = recovered + native["physical_R"] @ state["rigid"][6 * body_id:6 * body_id + 6]
                residual = K @ total - force
                maximum_residual = prototype.peak(np, residual)
                local_energy = .5 * float(force @ recovered)
                reduction_energy = (.5 * float(f @ target["H"] @ f) - float(f @ (target["e"] @ c))
                                    + .5 * float(c @ target["L"] @ c))
                local_energy_error = abs(local_energy - reduction_energy) / max(1., abs(local_energy), abs(reduction_energy))
                potential = state["energy"]
                potential_error = potential["primal_complementary_identity_error_nmm"] / max(
                    1., abs(potential["potential_nmm"]), abs(potential["body_elastic_energy_nmm"]),
                    abs(potential["connector_energy_nmm"]))
                require(maximum_residual <= .1 and local_energy_error < 1e-8 and potential_error < 1e-6,
                        "Actual assembled body force/work or total potential identity failed")
                peak, witness = helper.transverse_stress(nodes, elements, recovered[:, None], constants,
                                                        variant["RT_binding"] == "R=v,T=-u")
                force_error = prototype.peak(np, target["D"].T @ f - target["W"] @ c)
                require(force_error <= .1, "Selected body's assembled rigid equilibrium failed")
                checks = {name: True for name in FIELD_GATES}
                audit = {"all_passed": True, "checks": checks, "original_frame_audit": state["audit"],
                         "actual_scalar_residuals": {"all_node_force_residual_n": maximum_residual,
                             "selected_body_scaled_rigid_force_residual_n": force_error,
                             "local_field_vs_reduced_energy_relative": local_energy_error,
                             "assembled_primal_complementary_energy_relative": potential_error},
                         "tolerances": {"all_node_force_residual_n": .1,
                             "selected_body_scaled_rigid_force_residual_n": .1,
                             "local_field_vs_reduced_energy_relative": 1e-8,
                             "assembled_primal_complementary_energy_relative": 1e-6}}
                authenticate(pins)
                name = phase + "-" + tag
                np.savez_compressed(output / (name + "-fields.npz"), nodes_mm=nodes, elements=elements,
                    recovered_U_mm=recovered, total_U_mm=total, force_n=force, all_node_residual_n=residual,
                    frame_force_n=f, frame_relative_motion_mm=state["motion"], frame_rigid_scaled_mm=state["rigid"],
                    frame_bearing=state["bearing"])
                field_ref = reference(output / (name + "-fields.npz"))
                reaction = {"case_id": case, "gap_scale": gap, "state_tag": tag, "operator_variant_id": variant["id"],
                            "accepted_force_field_exists": True, "physical_audit": audit, "energy": potential,
                            "retained_reaction_field": field_ref, "floor_branch_history": state["history"],
                            "joint_update_binding": job["global_joint_update_binding"], "physical_release": False}
                write(output / (name + "-reaction.json"), reaction)
                reaction_ref = reference(output / (name + "-reaction.json"))
                checkpoint = {"schema": "splitting_representative_coupled_checkpoint/v1", "identity": identity,
                    "phase": phase, "operator_variant_id": variant["id"], "operator_ref": metadata["operator_ref"],
                    "reaction_ref": reaction_ref, "retained_field": field_ref, "physical_audit": audit,
                    "source_frame_receipt_sha256": source_frame_binding["sha256"], "energy": potential,
                    "actual_crack_area_mm2": metadata["mesh"]["crack_area_mm2"], "mesh": metadata["mesh"],
                    "sampled_sigma90_mpa": float(peak[0]), "stress_witness": witness[0],
                    "absolute_assembled_potential_claimed": False, "full_null_spectrum_assessed": False,
                    **{name + "_contract_ref": ref for name, ref in contracts.items()},
                    **{name + "_contract_sha256": ref["sha256"] for name, ref in contracts.items()}}
                write(output / (name + "-checkpoint.json"), checkpoint)
                checkpoint_ref = reference(output / (name + "-checkpoint.json"))
                checkpoints[identity["id"], phase] = checkpoint, checkpoint_ref
                dispositions.append({"operator_variant_id": variant["id"], "case_id": case, "gap_scale": gap,
                    "state_tag": tag, "status": "PASS_CONDITIONAL_COMPATIBLE_EQUILIBRIUM",
                    "accepted_force_field_exists": True, "response_ref": reaction_ref, "checkpoint_ref": checkpoint_ref})
                event("audited_assembled_field_saved", phase=phase, state_tag=tag, **audit["actual_scalar_residuals"])
            del native, K, B, assembled
        for identity in job["required_comparisons"]:
            triple = {phase: checkpoints[identity["id"], phase][0] for phase in ("intact", "initial", "final")}
            added = triple["final"]["actual_crack_area_mm2"] - triple["initial"]["actual_crack_area_mm2"]
            G = core.energy_release(triple["initial"]["energy"], triple["final"]["energy"], added)
            records.append({"id": identity["id"], "identity": identity,
                **{phase + "_checkpoint": checkpoints[identity["id"], phase][1] for phase in triple},
                "added_sound_area_mm2": added, "signed_G_n_per_mm": G,
                "Gc_n_per_mm": identity["unmeasured_Gc_all_modes_n_per_mm"],
                "conditional_energy_reference_index": max(0., G) / identity["unmeasured_Gc_all_modes_n_per_mm"],
                "intact_sampled_sigma90_mpa": triple["intact"]["sampled_sigma90_mpa"],
                "Ft90_mpa": identity["unmeasured_Ft90_mpa"],
                "conditional_initiation_reference_index": triple["intact"]["sampled_sigma90_mpa"] / identity["unmeasured_Ft90_mpa"],
                "upper_reference": None, "physical_split_or_joint_acceptance_claimed": False})
        status = "PASS_BOUNDED_AUDITED_REPRESENTATIVE_COUPLED_GROUP"
        required_ids = {r["id"] for r in selected["required_comparisons"]}
        write(output / "result.json", {"schema": "splitting_representative_coupled_study/v1", "numerical_scope": SCOPE,
            "status": status, "selection_binding": job["selection_binding"], "job_binding": reference(job_path),
            "active_action_binding": job["active_action_binding"], "source_frame_binding": source_frame_binding,
            "original_native_frame_binding": original_native_frame_binding,
            "artifact_receipts": [job["operator_group_receipt"], reference(OLD_OPERATORS / "receipt.json"),
                                  job["interface_mapping_known_answer_receipt"]],
            "assembled_known_answer": job["assembled_known_answer"], "records": records, "finite_dispositions": [],
            "interface_mapping_known_answer": job["interface_mapping_known_answer"],
            "operator_state_dispositions": dispositions,
            "pending_comparison_ids": sorted(required_ids - {r["id"] for r in records}),
            "original_inventory_completed": False, "full_splitting_qualification": False,
            "selected_comparison_inventory_complete": len(records) == len(required_ids),
            "representative_study_complete": False, "splitting_workstream_complete": False,
            "new_local_native_factorizations": 0, "physical_release": False})
        baseline_response.close()
    except BaseException as exc:
        write(output / "stop.json", {"status": status, "exception": type(exc).__name__, "message": str(exc),
            "audited_saved_operator_state_count": len(dispositions), "audited_saved_comparison_count": len(records),
            "selected_unperformed_work_pending": True, "permanent_method_exclusion": False,
            "unaudited_force_fields_exported": False, "physical_release": False})
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        write(output / "receipt.json", {"schema": "splitting_representative_coupled_replay_receipt/v1", "status": status,
            "source_sha256": {source_key(p): h for p, h in pins.items()},
            "source_resolution": job["source_resolution"], "source_before": {source_key(p): h for p, h in pins.items()},
            "source_after": {source_key(p): sha(p) for p in pins},
            "output_sha256": {p.relative_to(output).as_posix(): sha(p) for p in output.rglob("*") if p.is_file()
                              and p.name != "receipt.json"}, "elapsed_seconds": time.monotonic() - started,
            "maximum_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "assembled_equilibrium_executed": assembled_executed, "no_external_native_solver_or_CAD_executable": True,
            "physical_or_complete_joint_acceptance": False})
    return {"status": status, "result": reference(output / "result.json"), "receipt": reference(output / "receipt.json"),
            "actual_comparison_count": len(records), "actual_operator_state_count": len(dispositions)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--output", required=True, type=Path)
    eligible = commands.add_parser("prepare-eligible")
    eligible.add_argument("--output", required=True, type=Path)
    eligible.add_argument("--original-selection", required=True, type=Path)
    eligible.add_argument("--original-sha256", required=True)
    eligible.add_argument("--baseline", required=True, type=Path)
    eligible.add_argument("--baseline-sha256", required=True)
    eligible.add_argument("--active-actions", required=True, type=Path)
    eligible.add_argument("--action-sha256", required=True)
    check = commands.add_parser("verify")
    check.add_argument("--prepared", required=True, type=Path)
    check.add_argument("--receipt-sha256", required=True)
    known = commands.add_parser("mapping-known-answer")
    known.add_argument("--output", required=True, type=Path)
    known.add_argument("--core-sha256", required=True)
    known.add_argument("--wall-seconds", type=int, default=45)
    native = commands.add_parser("prepare-native")
    native.add_argument("--output", required=True, type=Path)
    native.add_argument("--selection", required=True, type=Path)
    native.add_argument("--selection-sha256", required=True)
    native.add_argument("--mapping-proof", required=True, type=Path)
    native.add_argument("--mesh-size", type=float, required=True)
    native.add_argument("--rt", choices=("R=u,T=v", "R=v,T=-u"), required=True)
    native.add_argument("--core-sha256", required=True)
    operator = commands.add_parser("operators")
    operator.add_argument("--output", required=True, type=Path)
    operator.add_argument("--job", required=True, type=Path)
    operator.add_argument("--job-sha256", required=True)
    assembled = commands.add_parser("prepare-assembled")
    assembled.add_argument("--output", required=True, type=Path)
    assembled.add_argument("--selection", required=True, type=Path)
    assembled.add_argument("--selection-sha256", required=True)
    assembled.add_argument("--operator-packet", required=True, type=Path)
    assembled.add_argument("--operator-receipt-sha256", required=True)
    assembled.add_argument("--state-tag", action="append", required=True)
    assembled.add_argument("--core-sha256", required=True)
    replay = commands.add_parser("assembled-replay")
    replay.add_argument("--output", required=True, type=Path)
    replay.add_argument("--job", required=True, type=Path)
    replay.add_argument("--job-sha256", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.output)
    elif args.command == "prepare-eligible":
        result = prepare_eligible(args.output, args.original_selection, args.original_sha256,
                                  args.baseline, args.baseline_sha256, args.active_actions, args.action_sha256)
    elif args.command == "verify":
        result = verify(args.prepared, args.receipt_sha256)
    elif args.command == "mapping-known-answer":
        result = mapping_known_answer(args.output, args.core_sha256, args.wall_seconds)
    elif args.command == "prepare-native":
        result = prepare_native(args.output, args.selection, args.selection_sha256, args.mapping_proof,
                                args.mesh_size, args.rt, args.core_sha256)
    elif args.command == "prepare-assembled":
        result = prepare_assembled(args.output, args.selection, args.selection_sha256, args.operator_packet,
                                  args.operator_receipt_sha256, args.state_tag, args.core_sha256)
    elif args.command == "assembled-replay":
        result = assembled_replay(args.output, args.job, args.job_sha256)
    else:
        result = operators(args.output, args.job, args.job_sha256)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
