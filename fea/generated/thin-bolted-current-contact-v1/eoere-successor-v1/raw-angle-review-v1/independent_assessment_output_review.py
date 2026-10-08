"""Read saved curation bytes and compare every selected value to its source.

No producer, gate, component kernel, operator archive or solver is imported.
This is a selection/identity audit of the already reviewed conditional packet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
PACKET = OWN.parent.parent
RUN = PACKET / "a12-first-order-v2"
FIXED = {
    RUN / "assessment.json": "ca94da5882097c480052ab97bc64211683372ad2734f80c13a04175e734c3cfe",
    RUN / "field.json": "dad00e84ae98333beeb89a0c2403d48d9f40e9189c4525fc3746b8b3118de598",
    RUN / "admission-v3.json": "383772d00e6f6c9207a833f5a9a067b6eaa1ca01279eb367c6ef518e41f77ee0",
    RUN / "components-v3.json": "03e04dc47bb7b7705463d1883be9b18e76d8401d2e91cea2733517c5ef423d21",
    RUN / "compact_assessment.py": "0fedda2eb16bd688935eaa9896612d864eadf21a798e686693aef4fe510e577c",
    RUN / "test_compact_assessment.py": "b477b95b02536b7f6ff143fd7b4a9f313838ebcaa1e8306791c6b99eab78b09e",
    RUN / "curation-method-plan.json": "518fe312e8224aba27e21714368c6dc04ee0dd173d84d5f9116e4102a367a04e",
    OWN.with_name("independent-curation-method-review.json"): "64377bc4ddd60e3f3c1ef1d8495cd05921638918c8b2354f4d35f582fb6616aa",
}
STATE = "eoere-a12-2cc47f73f1c898d9663dd319"
RELEASE = dict.fromkeys(("candidate_accepted", "complete_joint_acceptance", "capacity_established",
                         "fabrication_released", "structural_released", "climbing_released"), False)


def check(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def merge(target, added):
    for path, digest in added.items():
        check(path not in target or target[path] == digest, "source collision: " + path)
        target[path] = digest


def verify(pins):
    for path, digest in pins.items():
        check(sha(ROOT / path) == digest, "source bytes differ: " + path)


def by(rows, key, count):
    result = {row[key]: row for row in rows}
    check(len(rows) == len(result) == count, "unique complete census: " + key)
    return result


def copied(out, source, keys):
    for key in keys:
        check(out[key] == source[key], "stored value differs: " + key)


def evaluate():
    verify({str(path.relative_to(ROOT)): digest for path, digest in FIXED.items()})
    output, field, receipt, component, plan = [json.loads((RUN / name).read_bytes()) for name in (
        "assessment.json", "field.json", "admission-v3.json", "components-v3.json", "curation-method-plan.json")]
    before = [canonical(value) for value in (output, field, receipt, component, plan)]
    binding = output["source_binding"]
    direct = plan["source_sha256"]
    check(binding["direct_source_sha256"] == direct and len(direct) == 12, "twelve fixed direct inputs")
    producer = {}
    for pins in (field["source_sha256"], receipt["source_sha256"], component["source_sha256"], direct):
        merge(producer, pins)
    check(len(producer) == binding["verified_full_source_pin_count"] == 394, "producer pin census")
    check(canonical(producer) == binding["verified_full_source_union_canonical_sha256"], "producer pin digest")
    closure = binding["source_closure_reference"]
    check(closure == {"path": str((RUN / "components-v3.json").relative_to(ROOT)),
                     "raw_sha256": FIXED[RUN / "components-v3.json"],
                     "component_source_map_canonical_sha256": canonical(component["source_sha256"])}, "component closure")
    for name, raw_key in (("field.json", "raw_field_sha256"), ("admission-v3.json", "admission_receipt_sha256"),
                          ("components-v3.json", "raw_components_sha256")):
        check(binding[raw_key] == FIXED[RUN / name], "direct raw join " + name)
    check(len(binding["external_provenance"]) == 7, "external reference census")
    for value in binding["external_provenance"].values():
        check(direct[value["path"]] == value["raw_sha256"], "external reference byte identity")
    check(binding["source_pins_before_after_unchanged"] is True and binding["component_algorithms_rerun"] is False,
          "curation execution scope")
    review_pins = dict(producer)
    merge(review_pins, {str(path.relative_to(ROOT)): digest for path, digest in FIXED.items()})
    merge(review_pins, {str(OWN.relative_to(ROOT)): sha(OWN)})
    verify(review_pins)
    for value in (output, field, receipt, component):
        check(value["state_id"] == STATE and value["case_id"] == "a12-rear"
              and value["accessory_placement"] == "retained-original-top-hold", "same current identity")
        check(value["release"] == RELEASE, "all releases false")
    check(output["schema"] == "eoere_compact_same_state_conditional_assessment/v1", "curation schema")
    check(output["disposition"] == "CONDITIONAL_A12_PACKET_COMPLETE_STRUCTURAL_ACCEPTANCE_UNQUALIFIED", "conditional scope")
    check(output["counts"] == field["counts"] and output["counts"]["physical_bodies"] == 150, "current count copy")
    check(receipt["input_raw_sha256"] == FIXED[RUN / "field.json"]
          and receipt["input_canonical_sha256"] == canonical(field), "saved real admission")
    check(receipt["independent_eoere_original_law_gradient_work_and_equilibrium_checks_pass"] is True
          and receipt["first_order_physical_applicability_established"] is False
          and receipt["physical_demand_bounds_established"] is False, "admission limits")
    check(component["raw_field_sha256"] == FIXED[RUN / "field.json"]
          and component["field_admission_receipt_sha256"] == FIXED[RUN / "admission-v3.json"]
          and component["fresh_gate_sha256"] == receipt["admission_source_sha256"], "component state joins")
    qhash = canonical(field["response"]["q"])
    check(qhash == field["response"]["q_canonical_sha256"], "unchanged exact q")
    check(canonical(field["response"]["gradient_n"]) == field["response"]["gradient_canonical_sha256"], "unchanged exact g")
    reduced, source = component["component_reductions"], field["source_inputs"]
    duties = by(output["duties"], "duty_id", 24)
    poses = by(source["fitting_poses"], "id", 22)
    endpoint_keys = ("cut_id", "point_xyz_mm", "same_section_force_N_V1_V2_n", "same_section_moment_T_M1_M2_nmm",
                     "nominal_normal_stress_bound_mpa", "nominal_transverse_shear_norm_bound_mpa",
                     "nominal_torsion_shear_norm_bound_mpa", "simultaneous_nominal_vm_bound_mpa")
    strip_maxima = []
    for row in reduced["angle_duties"]:
        out = duties[row["duty_id"]]
        copied(out, row, ("duty_id", "body", "physical_axis_ids", "own_external_port_joins"))
        check(poses[row["body"]]["duty_id"] == row["duty_id"], "own pose duty")
        ports = [r for r in source["fitting_port_bindings"] if r["angle_id"] == row["body"]]
        check(len(ports) == 4 and set(out["physical_axis_ids"]) == {r["axis_id"] for r in ports}, "own four-axis role")
        comparison = row["loaded_strip_comparison"]
        check(out["kind"] == "four-port-angle" and out["actual_Fy_Fu_or_formed_heel_hole_pressure_group_strength"] is None,
              "unknown fitting resistance")
        check(comparison["conditional_fy_mpa"] is None and comparison["physical_product_fy_mpa"] is None, "unknown Fy")
        strips = by(out["four_gross_half_strip_witnesses"], "port_id", 4)
        check(set(strips) == {r["model_port_id"] for r in ports}, "own four strip ports")
        for strip in comparison["strips"]:
            saved = strip["nominal_gross_prismatic_field_governing_endpoint"]
            copied(strips[strip["port_id"]], strip, ("port_id", "flange"))
            copied(strips[strip["port_id"]]["stored_governing_endpoint"], saved, endpoint_keys)
            check(saved["specified_fy_mpa"] is None and saved["simultaneous_nominal_first_yield_bound_index"] is None,
                  "unqualified nominal strip field")
            strip_maxima.append((saved["simultaneous_nominal_vm_bound_mpa"], row["body"], strip["port_id"], saved["cut_id"]))
        check(out["two_flange_root_wrenches_about_heel_n_nmm"] == comparison["flange_root_resultants_diagnostic_only_n_nmm"],
              "two own flange root wrench copies")
    axes = by(source["shafts"], "axis_id", 100)
    for row in reduced["exterior_cleat_corners"]:
        out = duties[row["duty_id"]]
        copied(out, row, ("duty_id", "members", "physical_axis_ids", "own_direct_contact_ids"))
        side = row["duty_id"].rsplit("-", 1)[1]
        check(out["kind"] == "exterior-cleat-corner" and out["upper_angle_reference"] == "eoere_clip_angle_base_" + side,
              "own cleat upper angle")
        check(out["upper_angle_reference"] in poses, "existing upper angle")
        check(set(out["physical_axis_ids"]) == {key for key, r in axes.items()
              if "eoere_cleat_" + side in r["source_axis"]["receivers"]}, "cleat shaft ownership")
        check("not added independent capacities" in out["limit"], "shared cleat capacity limit")
    shaft_output = by(output["nominal_shaft_governing_cuts"], "axis_id", 100)
    raw_cuts = by(field["common_shaft_section_cut_actions"], "axis_id", 100)
    check(set(shaft_output) == set(axes), "all current shafts")
    for row in reduced["own_shaft_circle_comparisons"]:
        out = shaft_output[row["axis_id"]]
        scenario, = row["section_scenarios"]
        cut = scenario["sampled_governing_same_cut"]
        copied(out, row, ("axis_id", "body"))
        check(out["sample_count"] == scenario["sample_count"] == len(raw_cuts[row["axis_id"]]["cuts"]), "all saved shaft samples")
        copied(out["stored_governing_cut"], cut, tuple(out["stored_governing_cut"]))
        actual = [r for r in raw_cuts[row["axis_id"]]["cuts"]
                  if r["station_from_axis_point_mm"] == cut["station_from_axis_point_mm"]]
        check(len(actual) == 1 and actual[0]["point_xyz_mm"] == cut["point_xyz_mm"]
              and actual[0]["local_N_V1_V2_T_M1_M2_n_nmm"] == cut["same_cut_N_V1_V2_T_M1_M2_n_nmm"], "own signed shaft cut")
        check(out["actual_thread_root_shank_or_grade_resistance"] is None
              and scenario["section_scenario"]["diameter_mm"] == axes[row["axis_id"]]["diameter_mm"], "nominal own shaft only")
    for output_key, source_key, key, count in (
        ("simultaneous_Hillman_generic_references", "simultaneous_Hillman_actions_and_generic_references", "axis_id", 66),
        ("own_annulus_average_diagnostics", "own_washer_capture_diagnostics", "id", 200)):
        records = by(output[output_key], key, count)
        stored = by(reduced[source_key], key, count)
        check(set(records) == set(stored), "all same own component IDs")
        for ident, row in records.items():
            copied(row, stored[ident], tuple(row))
    screws = by(field["panel_screw_actions"], "axis_id", 66)
    for row in output["simultaneous_Hillman_generic_references"]:
        copied(row, screws[row["axis_id"]], ("axis_id", "panel", "receiver", "point_xyz_mm", "local_force_n", "withdrawal_n", "lateral_n"))
    captures = by(field["shaft_end_capture_actions"], "id", 200)
    for row in output["own_annulus_average_diagnostics"]:
        raw = captures[row["id"]]
        check(row["axis_id"] == raw["axis_id"] and row["end"] == raw["end"]["end"]
              and row["host"] == raw["second"] and row["compression_n"] == raw["compression_n"], "own capture force and datum")
        check(row["actual_pressure_couple_nmm"] is None and row["actual_contact_area_or_peak_pressure"] is None,
              "average-only annulus diagnostic")
    panels = output["six_spatial_panel_checks"]
    check(panels == reduced["six_panel_reductions"]["panel_diagnostics"], "all full spatial panels copied exactly")
    panel_map = by(panels, "panel", 6)
    check(set(panel_map) == set(source["panel_ids"]), "same six source panels")
    for row in panels:
        check(set(row["resolved_section_diagnostics"]["components"]) == {"bending_x", "bending_y", "rolling_x", "rolling_y"}
              and row["deformation_diagnostics"]["linear_plate_applicability_established"] is False, "full spatial and pose limits")
    gross = by(output["fresh_gross_member_witnesses"], "member", 22)
    check(set(gross) == {row["name"] for row in source["timber_rows"]}, "all current gross owners")
    weak_exclusions = []
    for row in reduced["fresh_gross_member_diagnostics"]:
        out = gross[row["member"]]
        copied(out, row, ("member", "sample_count", "source_width_mm", "source_depth_mm", "source_span_mm"))
        check(set(out["two_stored_gross_witnesses"]) == set(row["witnesses"]) == {"fully_braced_normal", "sufficient_shear_torsion"},
              "both current gross witnesses")
        check(out["finished_net_resistance_or_actual_bracing"] is None and "not an independently governing stability search" in out["limit"],
              "gross-only non-governing sensitivity")
        for label, witness in row["witnesses"].items():
            saved = out["two_stored_gross_witnesses"][label]
            copied(saved, witness, ("station_global_grain_projection_mm", "local_N_Vu_Vv_T_Mu_Mv_n_nmm"))
            copied(saved["signed_cut"], witness["signed_same_cut_wrench"], tuple(saved["signed_cut"]))
            comparison = saved["conditional_CD1_comparison_at_this_cut"]
            copied(comparison, witness["gross_CD1_comparison"], tuple(comparison))
        if any(w["conditional_CD1_comparison_at_this_cut"]["full_length_over_weak_column_domain_limit"] > 1
               for w in out["two_stored_gross_witnesses"].values()):
            weak_exclusions.append(row["member"])
    check(set(weak_exclusions) == {"base_header", "base_principal_center_left", "base_principal_center_right", "base_rail_top"},
          "four unqualified weak-column domains retained")
    steel = reduced["own_steel_surface_wrenches"]
    raw_steel = {(r["axis_id"], r["angle_id"], r["flange"]): r for r in field["common_shaft_steel_port_actions"]}
    check(len(steel) == len(raw_steel) == 88, "complete own steel sources")
    for row in steel:
        raw = raw_steel[(row["axis_id"], row["angle_id"], row["flange"])]
        check(set(row["physical_action_ids"]) == set(raw["own_bearing_points"] + raw["own_end_captures"]), "own steel source actions")
    check(len(reduced["own_wood_bearing_resultants_from_admitted_field"]) == 120
          and reduced["own_wood_bearing_resultants_from_admitted_field"] == field["common_shaft_wood_bearing_actions"], "120 own wood rows")
    for table, digest in component["enclosed_unlabeled_recovery_table_canonical_sha256"].items():
        check(canonical(field[table]) == digest, "unchanged enclosed recovery " + table)
    motion = output["first_order_motion_markers"]
    check(motion["timber_node_markers"] == field["timber_deformation_diagnostics"], "full timber motion copied")
    heels = by(motion["fitting_loaded_heel_markers"], "body", 22)
    for row in field["four_port_fitting_actions"]:
        copied(heels[row["body"]], row, ("body", "loaded_heel_q_mm_rad"))
    check("not internal heel strain" in motion["limit"] and "not measured physical deflections" in motion["limit"], "motion qualifications")
    closure = output["numerical_closure"]
    copied(closure, field, tuple(key for key in closure if key != "response"))
    copied(closure["response"], field["response"], tuple(closure["response"]))
    check(output["case_definition_without_load_rows"] == {key: value for key, value in source["case"].items() if key != "loads"},
          "same declared case without large rows")
    check(len(output["limits"]) == 10 and all(any(term in limit for limit in output["limits"]) for term in (
        "no multi-case or physical demand bound", "Fy/Fu", "not mean-only", "changed net cuts", "No-slip", "oblique", "delivered tolerance")),
          "retained physical and reference limits")
    argv = [".venv/bin/python", "-B", str((RUN / "compact_assessment.py").relative_to(ROOT)),
            "--mode", "curate", "--out", str((RUN / "assessment.json").relative_to(ROOT))]
    check(output["execution"]["sys_orig_argv"] == argv and output["execution"]["PYTHONPATH"] == "."
          and output["execution"]["cwd"] == str(ROOT) and output["execution"]["no_CAD_K_or_solve"] is True, "actual curation command")
    check(before == [canonical(value) for value in (output, field, receipt, component, plan)], "review inputs unmodified in memory")
    verify(review_pins)
    screw_peak = max(output["simultaneous_Hillman_generic_references"], key=lambda row: row["generic_head_ratio_CD1"])
    shaft_peak = max(output["nominal_shaft_governing_cuts"], key=lambda row: row["stored_governing_cut"]["same_section_nominal_stress_envelope_mpa"])
    upper = panel_map["main_upper_left"]["resolved_section_diagnostics"]["components"]
    gross_witnesses = [w["conditional_CD1_comparison_at_this_cut"] for row in gross.values() for w in row["two_stored_gross_witnesses"].values()]
    return {
        "schema": "independent_eoere_saved_assessment_output_review/v1", "disposition": "PASS_SAVED_CURATION_MAPPING_ONLY",
        "assessment": {"path": str((RUN / "assessment.json").relative_to(ROOT)), "bytes": (RUN / "assessment.json").stat().st_size,
                       "raw_sha256": FIXED[RUN / "assessment.json"], "canonical_sha256": canonical(output)},
        "state_id": STATE, "q_canonical_sha256": qhash,
        "checked_census": {"duties": len(duties), "angles": 22, "cleat_corners": 2, "strip_witnesses": len(strip_maxima),
                           "flange_root_wrenches": 44, "shafts": 100, "stored_signed_shaft_cuts": sum(len(r["cuts"]) for r in raw_cuts.values()),
                           "Hillman": 66, "annuli": 200, "panels_full_spatial": 6, "gross_members": 22,
                           "gross_same_cut_witnesses": len(gross_witnesses), "steel_sources": 88, "wood_sources": 120},
        "stored_witness_readout": {
            "nominal_strip_peak_mpa_body_port_cut": max(strip_maxima),
            "nominal_shaft_peak": shaft_peak,
            "generic_Hillman_peak": screw_peak,
            "upper_left_spatial_bending_x_CD1": upper["bending_x"]["sampled_ratio_CD1"],
            "upper_left_spatial_rolling_x_CD1": upper["rolling_x"]["sampled_ratio_CD1"],
            "gross_CD1_normal_peak": max(w["fully_braced_component_normal_interaction"] for w in gross_witnesses),
            "gross_CD1_sufficient_shear_torsion_peak": max(w["equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio"] for w in gross_witnesses),
            "weak_column_domain_exclusions": sorted(weak_exclusions)},
        "source_authentication": {"producer_union_count": len(producer), "producer_union_canonical_sha256": canonical(producer),
                                  "review_union_count": len(review_pins), "review_union_canonical_sha256": canonical(review_pins),
                                  "full_union_source_reference": str((RUN / "components-v3.json").relative_to(ROOT)),
                                  "extra_review_pins": {path: digest for path, digest in review_pins.items() if path not in producer},
                                  "all_raw_before_after_unchanged": True},
        "checks": ["Every selected scalar/vector and full spatial dictionary agrees exactly with its stored authenticated source.",
                   "All own duty, shaft, port, receiver, annulus and gross-member joins are complete and unique.",
                   "Exact state, q, gradient, original numerical closure, case and execution command are unchanged.",
                   "Unknown actual resistance, all six release flags, full spatial deficits, four stability exclusions and motion limits are retained."],
        "release": RELEASE,
        "limits": ["Read-only curation mapping review; no admission, component algorithm or producer rerun.",
                   "No operator archive unpack, candidate preparation, K construction, CAD, native or solve.",
                   "No actual material strength, complete joint capacity, physical demand bound, finite-contact applicability or fabrication release inferred.",
                   "Gross comparisons remain sampled source-stock conditional references; panel deficits and unresolved contact/holes remain active.",
                   "Distributed panel RHS remains source-authenticated captured output, not independently regenerated here."],
        "execution": {"sys_orig_argv": list(sys.orig_argv), "cwd": str(Path.cwd()), "PYTHONPATH": os.environ.get("PYTHONPATH"),
                      "python": sys.version, "no_candidate_or_physics_evaluation": True},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    check(not options.out.exists(), "preserve existing independent review")
    result = evaluate()
    with options.out.open("x") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
        stream.write("\n")
    print(json.dumps({"disposition": result["disposition"], "out": str(options.out), "bytes": options.out.stat().st_size,
                      "sha256": sha(options.out), "producer_pins": result["source_authentication"]["producer_union_count"]}))


if __name__ == "__main__":
    main()
