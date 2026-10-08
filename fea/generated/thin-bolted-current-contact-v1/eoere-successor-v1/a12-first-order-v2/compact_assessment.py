"""Authenticate and curate saved same-state findings; never recompute demands.

Plan mode reads hashes only. Parent-only curate mode calls the genuine cheap
v3 gate before selecting stored component witnesses into an exclusive output.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
PACKET = OWN.parent.parent
FIELD = OWN.with_name("field.json")
FIELD_SHA = "dad00e84ae98333beeb89a0c2403d48d9f40e9189c4525fc3746b8b3118de598"
ADMISSION = OWN.with_name("admission-v3.json")
ADMISSION_SHA = "383772d00e6f6c9207a833f5a9a067b6eaa1ca01279eb367c6ef518e41f77ee0"
COMPONENTS = OWN.with_name("components-v3.json")
COMPONENTS_SHA = "03e04dc47bb7b7705463d1883be9b18e76d8401d2e91cea2733517c5ef423d21"
GATE = PACKET/"four-port-method-v1/first_order_admission_v3.py"
GATE_SHA = "a32992a3a5f4fb8c16a0402ad522b938650d8744200ca4d8a28dfd38e07a0008"
PROVENANCE = {
    "actual_component_review": (PACKET/"raw-angle-review-v1/independent-actual-component-review.json",
        "4e3d643cff8cd869f4cf03af56e8e7a6efee269c910c590d3524fcfe6645722f"),
    "actual_steel_shaft_review": (OWN.with_name("independent-steel-shaft-review.json"),
        "a2ca357b20d11bb52b76aa10fa449bf4252e1e90760c0b15f2c28cdb802c09fe"),
    "input_review": (PACKET/"raw-angle-review-v1/independent-mechanics-inputs-review-final.json",
        "5f5a10265fb7a8e0eecbd083cc999cdd7cea11f65ae76dcae0a7c33d07d4783b"),
    "actual_admission_review": (PACKET/"raw-angle-review-v1/independent-actual-admission-review.json",
        "d0ad37536e4bf10bd4734ade646f69c82145f65920d4d21947b691ff4620988e"),
    "practical_inventory": (PACKET/"reuse-plan-v1/inventory-v2.json",
        "14d74a158c4af7cf57d0b1282eda41e6f7e849024130be3cf869080a6ee03de3"),
    "signed_connection_findings": (PACKET/"bolt-placement-v1/connection-signed-a12-v2.json",
        "0804764aa5df1499506ed6521c09341dd2475ccda24090db5c7ff557663a774b"),
    "connection_geometry_reference_limits": (PACKET/"bolt-placement-v1/connection-reference-disposition.json",
        "996c623c3904f75d14eafd0d25fd17660196dac778af6a5f9e75c73a47c36115"),
}
RELEASE = {key: False for key in ("candidate_accepted", "complete_joint_acceptance", "capacity_established",
    "fabrication_released", "structural_released", "climbing_released")}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT/path) == digest, "curation source differs: "+path)


def join(pins, extra):
    for path, digest in extra.items():
        require(path not in pins or pins[path] == digest, "curation source conflict: "+path)
        pins[path] = digest


def direct_pins():
    pins = {str(path.relative_to(ROOT)): digest for path, digest in (
        (OWN, LOADED_SHA), (FIELD, FIELD_SHA), (ADMISSION, ADMISSION_SHA), (COMPONENTS, COMPONENTS_SHA), (GATE, GATE_SHA))}
    join(pins, {str(path.relative_to(ROOT)): digest for path, digest in PROVENANCE.values()})
    verify(pins)
    return pins


def take(row, *keys):
    """Copy required stored values exactly; no fallback or arithmetic."""
    return {key: copy.deepcopy(row[key]) for key in keys}


def exact_ids(rows, key, expected, count):
    ids = [row[key] for row in rows]
    require(len(ids) == len(set(ids)) == count and set(ids) == set(expected), "complete unique own "+key+" census differs")


def keyed(rows, *keys):
    result = {tuple(row[key] for key in keys): row for row in rows}
    require(len(result) == len(rows), "duplicate own joint tuple")
    return result


def panels_record(rows):
    require(all(set(row["resolved_section_diagnostics"]["components"])
                == {"bending_x", "bending_y", "rolling_x", "rolling_y"} for row in rows),
            "spatial panel deficits cannot be replaced by mean-only findings")
    return copy.deepcopy(rows)


def angle_record(row):
    value = row["loaded_strip_comparison"]
    require(value["conditional_fy_mpa"] is None and value["physical_product_fy_mpa"] is None
            and value["complete_joint_acceptance"] is False, "no assumed fitting resistance permitted")
    strips = []
    for strip in value["strips"]:
        endpoint = strip["nominal_gross_prismatic_field_governing_endpoint"]
        require(endpoint["specified_fy_mpa"] is None and endpoint["simultaneous_nominal_first_yield_bound_index"] is None,
                "nominal stress cannot acquire a material utilization")
        strips.append({**take(strip, "port_id", "flange"), "stored_governing_endpoint": take(endpoint,
            "cut_id", "point_xyz_mm", "same_section_force_N_V1_V2_n", "same_section_moment_T_M1_M2_nmm",
            "nominal_normal_stress_bound_mpa", "nominal_transverse_shear_norm_bound_mpa",
            "nominal_torsion_shear_norm_bound_mpa", "simultaneous_nominal_vm_bound_mpa")})
    return {**take(row, "duty_id", "body", "physical_axis_ids", "own_external_port_joins"),
        "kind": "four-port-angle", "four_gross_half_strip_witnesses": strips,
        "two_flange_root_wrenches_about_heel_n_nmm": copy.deepcopy(value["flange_root_resultants_diagnostic_only_n_nmm"]),
        "disposition": "CONDITIONAL_NUMERICAL_FINDINGS_COMPLETE_JOINT_RESISTANCE_UNQUALIFIED",
        "actual_Fy_Fu_or_formed_heel_hole_pressure_group_strength": None}


def gross_record(row):
    witnesses = {}
    for label, witness in row["witnesses"].items():
        comparison = witness["gross_CD1_comparison"]
        witnesses[label] = {**take(witness, "station_global_grain_projection_mm", "local_N_Vu_Vv_T_Mu_Mv_n_nmm"),
            "signed_cut": take(witness["signed_same_cut_wrench"], "cut_point_xyz_mm", "force_on_lower_portion_xyz_n",
                               "moment_on_lower_portion_about_cut_xyz_nmm"),
            "conditional_CD1_comparison_at_this_cut": take(comparison,
                "fully_braced_component_normal_interaction", "equal_longitudinal_shear_moduli_rectangle_face_ratio",
                "equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio", "shear_reference_mpa",
                "full_length_K1_pin_end_normal_sensitivity", "full_length_over_weak_column_domain_limit")}
    return {**take(row, "member", "sample_count", "source_width_mm", "source_depth_mm", "source_span_mm"),
        "two_stored_gross_witnesses": witnesses, "finished_net_resistance_or_actual_bracing": None,
        "limit": "Sampled gross-stock witnesses; K1 sensitivity is at these two cuts, not an independently governing stability search. Changed bores, services, bevels, fracture and continuous maxima remain unresolved."}


def curate(field, receipt, components):
    """Select stored findings only, after the caller's genuine byte admission."""
    require(field["schema"] == "eoere_first_order_common_shaft_four_port_candidate/v2"
            and components["schema"] == "eoere_same_state_conditional_component_receipt/v1"
            and field["release"] == components["release"] == RELEASE, "unreleased current schemas required")
    for key in ("state_id", "case_id", "accessory_placement"):
        require(field[key] == components[key], "curation mixes current "+key)
    require(components["raw_field_sha256"] == FIELD_SHA and components["field_admission_receipt_sha256"] == ADMISSION_SHA
            and components["fresh_gate_sha256"] == GATE_SHA, "component raw field/admission/gate join differs")
    source, reduced = field["source_inputs"], components["component_reductions"]
    poses = {row["id"]: row for row in source["fitting_poses"]}
    exact_ids(reduced["angle_duties"], "body", poses, 22)
    exact_ids(reduced["exterior_cleat_corners"], "duty_id", ["exterior-cleat-corner-left", "exterior-cleat-corner-right"], 2)
    axes = {row["axis_id"]: row for row in source["shafts"]}
    exact_ids(reduced["own_shaft_circle_comparisons"], "axis_id", axes, 100)
    exact_ids(reduced["simultaneous_Hillman_actions_and_generic_references"], "axis_id", [r["id"] for r in source["hillman_rows"]], 66)
    exact_ids(reduced["own_washer_capture_diagnostics"], "id", [r["id"] for r in field["shaft_end_capture_actions"]], 200)
    exact_ids(reduced["fresh_gross_member_diagnostics"], "member", [r["name"] for r in source["timber_rows"]], 22)
    panels = reduced["six_panel_reductions"]["panel_diagnostics"]
    exact_ids(panels, "panel", source["panel_ids"], 6)
    require(len(reduced["own_steel_surface_wrenches"]) == 88 and len(reduced["own_wood_bearing_resultants_from_admitted_field"]) == 120,
            "all88steel/120wood own joins required")
    steel = keyed(reduced["own_steel_surface_wrenches"], "axis_id", "angle_id", "flange")
    saved_steel = keyed(field["common_shaft_steel_port_actions"], "axis_id", "angle_id", "flange")
    require(set(steel) == set(saved_steel), "all own steel tuples must match admitted field")
    for key, row in steel.items():
        saved = saved_steel[key]
        require(set(row["physical_action_ids"]) == set(saved["own_bearing_points"]+saved["own_end_captures"]),
                "own steel bearer/capture lineage differs")
    require(canonical(reduced["own_wood_bearing_resultants_from_admitted_field"])
            == canonical(field["common_shaft_wood_bearing_actions"]), "own wood alias table differs")
    for row in reduced["angle_duties"]:
        bindings = [r for r in source["fitting_port_bindings"] if r["angle_id"] == row["body"]]
        require(row["duty_id"] == poses[row["body"]]["duty_id"] and len(bindings) == 4
                and set(row["physical_axis_ids"]) == {r["axis_id"] for r in bindings}, "own duty/bolt join differs")
        ports = {r["model_port_id"] for r in bindings}
        exact_ids(row["own_external_port_joins"], "port_id", ports, 4)
        exact_ids(row["loaded_strip_comparison"]["strips"], "port_id", ports, 4)
    duties = [angle_record(row) for row in reduced["angle_duties"]]
    for row in reduced["exterior_cleat_corners"]:
        side = row["duty_id"].rsplit("-", 1)[1]
        expected = {key for key, shaft in axes.items() if "eoere_cleat_"+side in shaft["source_axis"]["receivers"]}
        require(len(expected) == 4 and set(row["physical_axis_ids"]) == expected, "four-axis cleat own join differs")
        duties.append({**take(row, "duty_id", "members", "physical_axis_ids", "own_direct_contact_ids"),
            "kind": "exterior-cleat-corner", "upper_angle_reference": "eoere_clip_angle_base_"+side,
            "disposition": "CONDITIONAL_NUMERICAL_PATH_COMPLETE_CORNER_RESISTANCE_UNQUALIFIED",
            "limit": "Shares the upper angle's two side bolts; these are not added independent capacities. Complete corner/group splitting/bearing and signed end/edge applicability remain unresolved."})
    shafts = []
    for row in reduced["own_shaft_circle_comparisons"]:
        require(row["conditional_fy_mpa"] is None and row["actual_thread_root_or_occupancy_adopted"] is False
                and len(row["section_scenarios"]) == 1, "only own nominal-circle unknown-Fy marker allowed")
        scenario = row["section_scenarios"][0]
        require(scenario["section_scenario"]["id"] == "nominal_model_circle"
                and scenario["section_scenario"]["diameter_mm"] == axes[row["axis_id"]]["diameter_mm"], "nominal own diameter differs")
        cut = scenario["sampled_governing_same_cut"]
        require(cut["same_section_nominal_first_yield_index"] is None, "shaft material index must remain unavailable")
        own = next(r for r in field["common_shaft_section_cut_actions"] if r["axis_id"] == row["axis_id"])
        matches = [r for r in own["cuts"] if r["station_from_axis_point_mm"] == cut["station_from_axis_point_mm"]]
        require(len(matches) == 1 and matches[0]["point_xyz_mm"] == cut["point_xyz_mm"]
                and matches[0]["local_N_V1_V2_T_M1_M2_n_nmm"] == cut["same_cut_N_V1_V2_T_M1_M2_n_nmm"],
                "nominal shaft marker must retain one actual own signed cut")
        shafts.append({**take(row, "axis_id", "body"), "stored_governing_cut": take(cut,
            "station_from_axis_point_mm", "point_xyz_mm", "same_cut_N_V1_V2_T_M1_M2_n_nmm",
            "diameter_at_loaded_section_mm", "same_section_nominal_stress_envelope_mpa"),
            "sample_count": scenario["sample_count"], "actual_thread_root_shank_or_grade_resistance": None})
    screws = [take(row, "axis_id", "panel", "receiver", "point_xyz_mm", "local_force_n", "withdrawal_n", "lateral_n",
        "generic_head_reference_n_CD1", "generic_head_ratio_CD1", "generic_head_ratio_conditional_CD1p6",
        "generic_withdrawal_required_effective_thread_mm_CD1", "generic_withdrawal_required_effective_thread_mm_conditional_CD1p6",
        "gross_nominal_length_after_panel_mm", "projected_annulus_mean_pressure_mpa")
        for row in reduced["simultaneous_Hillman_actions_and_generic_references"]]
    annuli = [take(row, "id", "axis_id", "end", "host", "compression_n", "nominal_full_annulus_area_mm2",
        "nominal_full_annulus_average_pressure_mpa", "actual_pressure_couple_nmm", "actual_contact_area_or_peak_pressure")
        for row in reduced["own_washer_capture_diagnostics"]]
    raw_screws = {r["axis_id"]: r for r in field["panel_screw_actions"]}
    for row in screws:
        require(take(row, "axis_id", "panel", "receiver", "point_xyz_mm", "local_force_n", "withdrawal_n", "lateral_n")
                == take(raw_screws[row["axis_id"]], "axis_id", "panel", "receiver", "point_xyz_mm", "local_force_n", "withdrawal_n", "lateral_n"),
                "same own simultaneous screw actions differ")
    raw_captures = {r["id"]: r for r in field["shaft_end_capture_actions"]}
    for row in annuli:
        raw = raw_captures[row["id"]]
        require(row["axis_id"] == raw["axis_id"] and row["end"] == raw["end"]["end"]
                and row["host"] == raw["second"] and row["compression_n"] == raw["compression_n"],
                "own annulus force/host lineage differs")
    require(all(r["actual_pressure_couple_nmm"] is None and r["actual_contact_area_or_peak_pressure"] is None for r in annuli),
            "point-capture pressure data cannot become an annular solution")
    for table in ("four_port_fitting_actions", "common_shaft_section_cut_actions"):
        require(components["enclosed_unlabeled_recovery_table_canonical_sha256"][table] == canonical(field[table]),
                "enclosed same-state recovery table differs")
    return {"schema": "eoere_compact_same_state_conditional_assessment/v1",
        **take(field, "state_id", "case_id", "accessory_placement", "counts"),
        "disposition": "CONDITIONAL_A12_PACKET_COMPLETE_STRUCTURAL_ACCEPTANCE_UNQUALIFIED",
        "duties": duties, "nominal_shaft_governing_cuts": shafts, "simultaneous_Hillman_generic_references": screws,
        "own_annulus_average_diagnostics": annuli, "six_spatial_panel_checks": panels_record(panels),
        "fresh_gross_member_witnesses": [gross_record(row) for row in reduced["fresh_gross_member_diagnostics"]],
        "first_order_motion_markers": {"timber_node_markers": copy.deepcopy(field["timber_deformation_diagnostics"]),
            "fitting_loaded_heel_markers": [take(r, "body", "loaded_heel_q_mm_rad") for r in field["four_port_fitting_actions"]],
            "limit": "First-order model motion includes frame movement; loaded heel coordinates are not internal heel strain. These are not measured physical deflections or finite contact applicability."},
        "numerical_closure": {**take(field, "equilibrium_verification", "global_equilibrium_residual_force_n",
            "global_equilibrium_residual_moment_nmm", "floor_support_summary", "original_operator_fingerprint_sha256"),
            "response": take(field["response"], "gradient_inf_n", "q_canonical_sha256", "gradient_canonical_sha256",
                "potential_energy_nmm", "nonbearing_no_slip_removed")},
        "case_definition_without_load_rows": {k: copy.deepcopy(v) for k, v in source["case"].items() if k != "loads"},
        "limits": ["One A12 declared first-order reference-contact/spring scenario; no multi-case or physical demand bound is adopted.",
            "Gross44.45x6.35 strips fill factory holes; nominal stress is not actual formed-heel/holed-plate resistance. Fy/Fu and delivered bolt grade/root/shank remain unknown.",
            "Shaft samples preserve same-cut N/V/T/M and shared ownership; individual port values are not summed or split equally into joint capacities.",
            "Full nominal annulus N/A is an average diagnostic. Annular couples, contact area, peak pressure, washer/head/nut/thread and wood-seat resistance are missing.",
            "Hillman generic head/withdrawal references retain simultaneous lateral demand, but screw product steel/lateral/edge/punching and actual threaded embedment remain unqualified.",
            "Panel entries retain spatial bending/rolling peaks, not mean-only checks. Spline third-derivative jumps, local openings/hold footprints/head seats and refinement are unresolved.",
            "Gross timber samples retain own support points/couples and affine gravity; changed net cuts/services/bevels, fracture, bracing and full joint/group resistance are separate. Four full-lengthK1 weak-column domain exclusions (header, principalcentersL/R, toprail) are unqualified sensitivities, not proven actual-bracing failures.",
            "Signed16member end/edge findings remain source-bound references: oblique/two-Gauss force reversal precludes a whole-group Cdelta. Right1cleat/post signs need not oppose because own gravity remains.",
            "Z200post38.9/cleat60.3 end markers and0.340625 nominal bore/screw gap are not delivered tolerance acceptance. Current rim resultant points away from the29.108short edge; unloaded-edge and bevel applicability remain explicit.",
            "No-slip whole-foot centroid support is an unverified analytical assumption. No friction/anchor, fabrication or climbing release."],
        "release": copy.deepcopy(RELEASE)}


def execute():
    direct = direct_pins()
    spec = importlib.util.spec_from_file_location("compact_assessment_actual_v3_gate", GATE)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    raw, receipt_raw, component_raw = FIELD.read_bytes(), ADMISSION.read_bytes(), COMPONENTS.read_bytes()
    receipt = json.loads(receipt_raw)
    field, pins = gate.require_admitted_payload(raw, receipt, admission_sha256=GATE_SHA)
    components = json.loads(component_raw)
    join(pins, components["source_sha256"])
    join(pins, direct)
    verify(pins)
    original = (canonical(field), canonical(components), canonical(receipt))
    result = curate(field, receipt, components)
    require(original == (canonical(field), canonical(components), canonical(receipt)), "curation modified saved inputs")
    result["source_binding"] = {"direct_source_sha256": direct,
        "verified_full_source_pin_count": len(pins), "verified_full_source_union_canonical_sha256": canonical(pins),
        "source_closure_reference": {"path": str(COMPONENTS.relative_to(ROOT)), "raw_sha256": COMPONENTS_SHA,
                                     "component_source_map_canonical_sha256": canonical(components["source_sha256"])},
        "raw_field_sha256": FIELD_SHA, "admission_receipt_sha256": ADMISSION_SHA, "raw_components_sha256": COMPONENTS_SHA,
        "external_provenance": {name: {"path": str(path.relative_to(ROOT)), "raw_sha256": digest}
                                for name, (path, digest) in PROVENANCE.items()},
        "source_pins_before_after_unchanged": True, "component_algorithms_rerun": False}
    verify(pins)
    return result


def method_plan():
    pins = direct_pins()
    return {"schema": "eoere_compact_assessment_curation_plan/v1", "source_sha256": pins,
        "planned_census": {"duties": 24, "angle_strips": 88, "shafts": 100, "Hillman": 66, "captures": 200, "panels": 6, "gross_members": 22},
        "method": "Exact raw/source admission followed only by stored-value selection and identity/census checks; no component algorithms or demand arithmetic replay.",
        "parent_command": "PYTHONPATH=. .venv/bin/python -B "+str(OWN.relative_to(ROOT))+" --mode curate --out "+str(OWN.with_name("assessment.json").relative_to(ROOT)),
        "final_assessment_produced": False, "no_CAD_K_response_or_solve": True}


def main():
    argv = list(sys.orig_argv)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("plan", "curate"), default="plan")
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    require(not options.out.exists(), "preserve existing curation output")
    result = method_plan() if options.mode == "plan" else execute()
    result["execution"] = {"sys_orig_argv": argv, "PYTHONPATH": os.environ.get("PYTHONPATH"),
                           "cwd": str(Path.cwd()), "python": sys.version, "no_CAD_K_or_solve": True}
    with options.out.open("x") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(options.out), "mode": options.mode}))


if __name__ == "__main__":
    main()
