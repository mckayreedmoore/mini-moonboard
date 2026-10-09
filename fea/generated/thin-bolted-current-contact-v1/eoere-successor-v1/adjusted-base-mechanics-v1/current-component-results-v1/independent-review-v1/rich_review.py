"""Bounded review of all six frozen current followup component outputs.

Reuse this review packet's stdlib scalar/checking utilities, never the genuine
component methods. Authenticate own field/admission pairs via the frozen
six-case coarse review. Check source identity, census, null boundaries,
reference-scenario arithmetic and summary selection. No full reducer replay.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path

OWN = Path(__file__).resolve()
UTILITY = OWN.with_name("review.py")
UTILITY_SHA = "64dbd260245bbc6d349d0866cc882e7b811d0a97436c4caffebc9912fdb575a3"
COARSE = OWN.with_name("receipt-six-cases.json")
COARSE_SHA = "5973bb5c128a76fde59c3a6183cfd06ec3d42460f6be9921e2e7e1be80e0fec9"
FOLLOWUP_SHA = "a27bacf7260905f69c2a69bae60c0f2cf4ed1f4efd229100e3c8fb846b892798"
TARGETS = {
    "a12-forward": "235e0290ad55f43cad14ac55ca2873ae80ee53eba53fdc3d089f79bcb72dad02",
    "a12-rear": "d232aaa933dcd21f0506509dd67ef8ba52843b8bcaa4ed4007a2111c3ad494ec",
    "a12-left": "d3eae971965ae13eccfd46f96764adff72957c8e4cfc6ebe17501711c4c4d49c",
    "k12-right": "687b3544a60accff933d3250c0b12ef907c62c8bc18924652f114f5a30cc471a",
    "k12-rear": "e2abd3a855c306ce53058507d914976523d68cc3cf86d1658dc4fbe952a720cb",
    "a1-rear": "bd2656d5909e4d9c63bfaa5e2f351e9c0ed865591d389dbd820f3d896b128434",
}


def utility():
    import hashlib

    if hashlib.sha256(UTILITY.read_bytes()).hexdigest() != UTILITY_SHA:
        raise ValueError("exact independent scalar reviewer required")
    spec = importlib.util.spec_from_file_location("independent_current_component_scalar_utilities", UTILITY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


u = utility()
ROOT, MECH, BASE = u.ROOT, u.MECH, u.BASE
FOLLOWUP = MECH / "current-component-bridge-v1/followups-v1/followups.py"
CATALOG = BASE / "catalog-hardware-strength-v1/catalog-inputs.json"
ROOTS = BASE / "catalog-hardware-strength-v1/thread-root-design-v1/result.json"
PARENT = u.DOC / "occupied-adjusted-base-v3.json"
SCENARIOS = {
    "t6_r6": {"id": "t6_r6", "thickness_mm": 6., "inside_radius_scenario_mm": 6., "yield_factor": 1.67, "rupture_factor": 2.},
    "t6p35_r6p35": {"id": "t6p35_r6p35", "thickness_mm": 6.35, "inside_radius_scenario_mm": 6.35, "yield_factor": 1.67, "rupture_factor": 2.},
}


def common(report, field, coarse, case):
    u.same_state(field, report)
    u.same_state(field, coarse)
    u.require(report["case_id"] == case and report["schema"] == "eoere_current_same_state_followup_component_references/v1", "own rich current case/schema required")
    u.require(report["field_schema"] == field["schema"] == "eoere_extended_cleat_fixed_floor_candidate/v1", "current rich field schema required")
    for key in ("raw_field_sha256", "field_admission_receipt_sha256", "source_inputs_canonical_sha256", "current_geometry", "current_saved_descriptors", "fresh_gate_sha256"):
        u.require(report[key] == coarse[key], "rich/coarse actual source pair differs: " + key)
    u.require(report["current_source_manifest"] == field["source_inputs"]["geometry"]["source_manifest"], "current manifest differs")
    u.require(report["release"] == u.RELEASE and report["complete_joint_resistance"] is None, "rich conditional null/release boundary changed")
    u.require(report["source_sha256"][u.relative(FOLLOWUP)] == FOLLOWUP_SHA and report["source_sha256"][u.relative(u.CONSUMER)] == u.CONSUMER_SHA, "reviewed current source consumers required")
    execution = report["execution"]
    u.require(all(execution[k] is False for k in ("CAD_query_or_rebuild", "operator_K_or_preparation", "frame_K_q_native_or_browser", "historical_force_or_geometry_intake_called")) and execution["frozen_equations_and_tolerances_unchanged"] is True and execution["scoped_intake_restored"] is True, "current fixed-action execution boundary differs")


def steel(check, scenario, field):
    comparison = scenario["comparison"]
    u.require(comparison == SCENARIOS.get(comparison["id"]) and scenario["fixed_actions_scalar_scenario_only"] is True and scenario["product_strength_established"] is False, "two separate fixed-action steel reference scenarios required")
    angles = u.indexed(scenario["angles"], "body")
    descriptors = u.indexed(field["fitting_operator_descriptors"], "body")
    u.require(set(angles) == set(descriptors) and len(angles) == 22, "all 22 current steel owners required")
    categories = {key: [] for key in scenario["summary"]}
    for body, angle in angles.items():
        u.require(angle["actual_3D_heel_and_hole_stress_bound"] is False and angle["complete_joint_resistance_accepted"] is False, "steel scenario must not establish actual complete resistance")
        bindings = [r for r in field["source_inputs"]["fitting_port_bindings"] if r["angle_id"] == body]
        bands = u.indexed(angle["bands"], "port_id")
        u.require(set(bands) == {b["model_port_id"] for b in bindings} and len(bands) == 4, "four own physical half bands required")
        physical = [r["id"] for r in field["common_shaft_bearing_actions"] if r["second"] == body]
        physical += [r["id"] for r in field["shaft_end_capture_actions"] if r["second"] == body]
        physical += [r["id"] for r in field["contact_actions"] if r["kind"] == "flange_contact" and r["first"] == body]
        u.require(set(angle["integrity"]["physical_action_ids"]) == set(physical) and len(physical) == len(angle["integrity"]["physical_action_ids"]) == angle["integrity"]["point_loads_retained"] == 28, "all own current 28 point loads required")
        gravity = next(r for r in field["body_applied_loads"] if r["id"] == "self-weight/"+body)
        check.number(angle["own_physical_source_weight_n"], math.hypot(*gravity["force_xyz_n"]), "rich-steel/own-weight")
        descriptor = descriptors[body]
        source = descriptor["own_fitting_scenario"]
        ports = u.indexed(descriptor["ports"], "id")
        for key, band in bands.items():
            u.require(band["comparison_thickness_mm"] == comparison["thickness_mm"] and band["source_physical_thickness_mm"] == 6.35 and band["heel_component"]["inside_radius_scenario_mm"] == comparison["inside_radius_scenario_mm"], "scalar scenario must retain source geometry and declared radius")
            normal = u.cross(source["flange_axes_local"][band["flange"]], [0, 1, 0])
            world_normal = u.matvec(source["fitting_basis_columns_xyz"], normal)
            root_normal = u.dot(world_normal, u.sub(ports[key]["strip_root_xyz_mm"], source["heel_reference_xyz_mm"]))
            check.number(band["saved_operator_root_normal_mm"], root_normal, "rich-steel/source-neutral-line")
            check.number(band["physical_neutral_normal_mm"], 3.175 if band["flange"] == "arm-x" else -3.175, "rich-steel/source-midsurface")
            rows = {
                "physical_cut_nominal_combined": band["governing"]["governing_combined"],
                "near_hole_nominal_combined": band["near_hole"]["governing_combined"],
                "far_hole_nominal_combined": band["far_hole"]["governing_combined"],
                "radius_conditioned_heel_component_with_gravity": band["heel_component"],
            }
            for name, row in rows.items():
                stress = row["bounding_source_gravity_equivalent_mpa"] if name.startswith("radius_") else row["nominal_equivalent_mpa"]
                check.number(row["conditional_base_metal_first_yield_index"], stress/235, "rich-steel/base-metal-marker")
                check.number(row["conditional_combined_yield_reference_ratio"], stress*comparison["yield_factor"]/235, "rich-steel/combined-reference")
                categories[name].append({"body": body, "port_id": key, "flange": band["flange"], "comparison": row})
            categories["unused_near_hole_net_shear"].append({"body": body, "port_id": key, **band["unused_near_hole_center"]})
        u.require(len(angle["whole_flange_torsion_warping_references"]) == 2 and len(angle["used_hole_bearing_tearout"]) == 4, "two whole-flange and four used-hole references required")
        for row in angle["whole_flange_torsion_warping_references"]:
            u.require(row["additive_to_half_band_bending"] is False, "whole-flange sensitivity must remain separate")
            check.number(row["conditional_combined_yield_reference_ratio"], row["combined_reference_mpa"]*comparison["yield_factor"]/235, "rich-steel/whole-flange-reference")
            categories["separate_whole_flange_torsion_warping"].append({"body": body, "port_id": None, "flange": row["flange"], "comparison": {"body": body, **row}})
        bores = [{"body": body, **row} for row in angle["used_hole_bearing_tearout"]]
        u.require({r["axis_id"] for r in bores} == {r["axis_id"] for r in bindings}, "own used-hole axis selection differs")
        categories["used_hole_bearing"].extend(bores)
        categories["used_hole_tearout"].extend(bores)
    peaks = {}
    for name, rows in categories.items():
        summary = scenario["summary"][name]
        key = {"used_hole_bearing": "bearing_reference_ratio", "used_hole_tearout": "tearout_reference_ratio", "unused_near_hole_net_shear": "net_shear_rupture_reference_ratio"}.get(name)
        score = (lambda r, k=key: r[k]) if key else lambda r: r["comparison"]["conditional_combined_yield_reference_ratio"]
        expected = max(rows, key=score)
        exceeding = [r for r in rows if score(r) > 1]
        u.require(summary["comparison_count"] == len(rows) and summary["worst"] == expected and summary["exceedance_count"] == len(exceeding) and summary["exceedances"] == exceeding, "steel summary lost or changed reference findings: " + name)
        peaks[name] = {"reference_ratio": score(expected), "exceedance_count": len(exceeding), "body": expected["body"]}
    return {"scenario": comparison, "angles": 22, "bands": 88, "own_point_actions": 616, "separate_summary_peaks": peaks}


def timber(check, report, field, mixed):
    u.same_state(field, report)
    u.require(report["source_field_sha256"] == u.sha(MECH / "current-cases-v1" / field["case_id"] / "attempt01/field.json"), "timber raw field binding differs")
    u.require(all(v is False for v in report["release"].values()) and report["same_field_reused_gross_member_witnesses"] == [], "timber reuse must not transfer old gross witnesses or acceptance")
    material = report["material_scenario"]
    u.require(material["Fyb_purchase_design_psi"] == 92000 and material["generic_steel_Fe_psi"] == 87000 and material["generic_steel_Fe_is_eoere_product_qualification"] is False and material["root_floor_is_delivered_or_UNC_guarantee"] is False, "conditional timber material scenario differs")
    shafts = u.indexed(field["source_inputs"]["shafts"], "axis_id")
    records = u.indexed(report["shaft_components"], "axis_id")
    u.require(set(records) == set(shafts), "all 100 current timber shaft references required")
    unsupported = {key for key, row in records.items() if row["component"] is None}
    u.require(unsupported == set(mixed), "eight mixed/shared stacks must retain null references")
    referenced = []
    for key, row in records.items():
        source = shafts[key]
        woods = [r for r in source["surfaces"] if r["kind"] == "wood"]
        u.require(row["wood_surface_count"] == len(woods) and row["steel_surface_count"] == len(source["surfaces"])-len(woods) and row["wood_receivers"] == [r["host"] for r in woods], "own timber stack classification differs")
        u.require(row["Cg"] is None and row["Cdelta"] is None and row["complete_joint_resistance_n"] is None, "complete timber resistance invented")
        value = row["component"]
        if value is None:
            continue
        referenced.append(row)
        modes = value["six_mode_references_n"]
        u.require(set(modes) == {"Im", "Is", "II", "IIIm", "IIIs", "IV"} and all(v > 0 for v in modes.values()), "six positive conditional modes required")
        check.number(value["unadjusted_component_Z_n"], min(modes.values()), "rich-timber/mode-minimum")
        check.number(modes[value["governing_mode"]], min(modes.values()), "rich-timber/governing-mode")
        ratio = value["lateral_demand_n"] / min(modes.values())
        for k, expected in (("V_over_unadjusted_component_Z", ratio), ("required_Cg_times_Cdelta_at_CD1_component_only", ratio), ("Cdelta0p5_Cg1_CD1_sensitivity_ratio", 2*ratio)):
            check.number(value[k], expected, "rich-timber/"+k)
        u.require(value["exceeds_unadjusted_component_reference"] == (value["lateral_demand_n"] > value["unadjusted_component_Z_n"]) and value["Cg"] is None and value["Cdelta"] is None and value["complete_joint_Z_n"] is None, "conditional reference must retain actual group unknowns")
    surfaces = {(r["axis_id"], r["surface_index"]): r for r in field["common_shaft_wood_bearing_actions"]}
    rows = report["wood_surfaces"]
    u.require(len(rows) == len(surfaces) == 120 and len({(r["axis_id"], r["surface_index"]) for r in rows}) == 120, "all 120 own wood surfaces required")
    for row in rows:
        original = surfaces[row["axis_id"], row["surface_index"]]
        u.require(row["receiver"] == original["host"] and row["own_aggregate_point_xyz_mm"] == original["point_xyz_mm"], "own wood aggregate datum differs")
        check.vector(row["own_force_xyz_n"], original["force_on_host_xyz_n"], "rich-timber/own-force")
        check.vector(row["own_moment_at_aggregate_xyz_nmm"], original["moment_on_host_at_point_xyz_nmm"], "rich-timber/own-couple", atol=2e-7)
        u.require({r["id"] for r in row["own_point_actions"]} == set(original["own_bearing_points"]+original["own_end_captures"]), "own wood point action selection differs")
        u.require(row["complete_Cg"] is None and row["complete_Cdelta"] is None and row["splitting_or_group_fracture_reference_n"] is None, "wood surface/group strength invented")
    summary = report["summary"]
    u.require(summary["shaft_dispositions"] == dict(Counter(r["disposition"] for r in records.values())) and summary["physical_shafts"] == 100 and summary["wood_surfaces"] == 120 and summary["timber_members"] == 22 and summary["duties"] == len(report["duties"]) == 24 and summary["supported_component_reference_count"] == len(referenced) == 92, "timber reference census differs")
    u.require(summary["unadjusted_reference_exceedances"] == sum(r["component"]["exceeds_unadjusted_component_reference"] for r in referenced) and summary["Cdelta0p5_Cg1_CD1_sensitivity_exceedances"] == sum(r["component"]["Cdelta0p5_Cg1_CD1_sensitivity_ratio"] > 1 for r in referenced), "timber reference exceedances omitted")
    expected = [{"axis_id": r["axis_id"], "receivers": r["wood_receivers"], "disposition": r["disposition"], **r["component"]} for r in sorted(referenced, key=lambda r: r["component"]["V_over_unadjusted_component_Z"], reverse=True)[:12]]
    u.require(summary["worst_components"] == expected and summary["all_complete_Cg_Cdelta_and_joint_resistances_remain_null"] is True and all(r["complete_joint_resistance_n"] is None for r in report["duties"]), "timber summary selection/null boundary differs")
    starting = [r["axis_id"] for r in records.values() if r["source_axis_kind"] == "original_starting_frame_axis"]
    u.require(report["retained_starting_frame_axis_ids"] == starting and len(starting) == summary["retained_starting_frame_shafts"] == 12, "twelve starting frame axes must remain represented")
    return {"shaft_references": 100, "supported_individual_references": 92, "mixed_shared_references_still_null": sorted(unsupported), "duties": 24,
            "unadjusted_reference_exceedances": summary["unadjusted_reference_exceedances"], "Cdelta0p5_Cg1_sensitivity_exceedances": summary["Cdelta0p5_Cg1_CD1_sensitivity_exceedances"]}


def washer_scenario(check, scenario, row, fc_perp):
    a, b = scenario["ID_mm"]/2, scenario["OD_mm"]/2
    support = max(a, scenario["source_support_opening_diameter_mm"]/2)
    load = scenario["uniform_load_ring_outer_radius_mm"]
    n = row["N_n"]
    u.require(n >= 0 and 0 < a <= support < b and a < load <= b, "positive concentric washer scenario required")
    mean = n/(math.pi*(b*b-support*support))
    check.number(scenario["uniform_support_ring_inner_radius_mm"], support, "rich-washer/support-radius")
    check.number(scenario["uniform_supported_ring_mean_mpa_geometric_diagnostic"], mean, "rich-washer/ring-average")
    check.number(scenario["Fy_33ksi_reference_ratio_unadopted"], scenario["sampled_axial_only_Fy_required_mpa"]/(33000*0.006894757293168361), "rich-washer/unadopted-material-marker")
    for name, inner, outer in (("support_ring", support, b), ("load_ring", a, load)):
        check.number(scenario["affine_full_contact_couple_limit_Nmm"][name], n*(inner*inner+outer*outer)/(4*outer), "rich-washer/affine-contact-limit")
        check.number(scenario["necessary_compression_only_couple_limit_Nmm"][name], n*outer, "rich-washer/necessary-contact-limit")
    applicable = row["receiver_kind"] == "wood" and row["grain_axis_abs_cos_to_pressure_normal"] < 1e-8
    for key, condition in (("raw_ring_Fc_perp625psi_mean_ratio_conditional", applicable), ("nominal_supported_ring_Fc_perp625psi_mean_reference_index", applicable and scenario["source_nominal_supported_ring_landing_full"])):
        if condition:
            check.number(scenario[key], mean/fc_perp, "rich-washer/wood-reference")
        else:
            u.require(scenario[key] is None, "inapplicable wood washer reference must stay null")
    u.require(all(scenario[k] is None for k in ("actual_product_Fy_mpa", "physical_pressure_couple_Nmm", "physical_contact_pressure_bound_mpa", "combined_washer_strength_index")), "actual washer material/contact/combined strength invented")


def washers(check, report, field, geometry, parent, coarse):
    u.require(report["state_id"] == field["state_id"] and report["case_id"] == field["case_id"] and all(v is False for v in report["release"].values()), "own unreleased washer case required")
    composition = report["geometry_composition"]
    u.require(composition["axes"] == geometry["axes"] and composition["service_cuts"] == parent["service_cuts"] and len(composition["service_cuts"]) == 27 and composition["extension_report_contains_service_cuts_or_fitting_scenario"] is False, "explicit current washer geometry/v3 cut composition required")
    u.require(report["reviewed_nominal_seat_geometry"] == coarse["nominal_seat_geometry"] and report["input_authentication"]["current_geometry_composition_canonical_sha256"] == u.canonical(composition) and report["input_authentication"]["raw_field_sha256"] == coarse["raw_field_sha256"] and report["input_authentication"]["fresh_gate_sha256"] == u.GATE_SHA, "washer geometry/field evidence binding differs")
    captures = u.indexed(field["shaft_end_capture_actions"], "id")
    rows = report["all200_own_end_diagnostics"]
    u.require(set(u.indexed(rows, "capture_id")) == set(captures) and len(rows) == 200, "all 200 unique own washer ends required")
    axes = u.indexed(geometry["axes"], "id")
    fc = 625*0.006894757293168361
    check.number(report["references"]["wood_Fc_perp625psi_mpa_unincreased"], fc, "rich-washer/Fc-perp")
    u.require(report["references"]["catalog_numeric_washer_Fy_or_Fu_available"] is False, "catalog washer strength must stay unknown")
    for row in rows:
        action = captures[row["capture_id"]]
        u.require(row["axis_id"] == action["axis_id"] and row["end"] == action["end"]["end"] and row["host"] == action["end"]["host"] and row["N_n"] == action["compression_n"] and row["own_support_point_xyz_mm"] == action["host_support_point_xyz_mm"], "washer substituted another end or datum")
        check.vector(row["own_model_couple_xyz_Nmm"], action["moment_on_second_at_point_xyz_nmm"], "rich-washer/own-model-couple")
        u.require(row["physical_own_pressure_couple_xyz_Nmm"] is None and len(row["USS_catalog_corners_min_thickness"]) == 4, "physical washer couple must remain unknown; four catalog corners required")
        hardware = axes[row["axis_id"]]["hardware_scenario"]
        nominal = row["nominal_own_hardware_geometry"]
        u.require([nominal[k] for k in ("OD_mm", "ID_mm", "t_mm")] == [hardware[k] for k in ("washer_od_mm", "washer_id_mm", "washer_thickness_mm")], "own nominal hardware scenario differs")
        for scenario in (nominal, *row["USS_catalog_corners_min_thickness"]):
            washer_scenario(check, scenario, row, fc)
        u.require(row["own_max_catalog_axial_Fy_corner"] == max(row["USS_catalog_corners_min_thickness"], key=lambda s: s["sampled_axial_only_Fy_required_mpa"]) and row["own_max_catalog_geometric_mean_corner"] == max(row["USS_catalog_corners_min_thickness"], key=lambda s: s["uniform_supported_ring_mean_mpa_geometric_diagnostic"]), "washer own catalog corner selection differs")
    census = report["census"]
    u.require(census["physical_axes"] == 100 and census["physical_end_captures"] == len(rows) == 200 and census["head"] == census["nut"] == 100 and census["receiver_kind"] == dict(Counter(r["receiver_kind"] for r in rows)) == {"steel": 88, "wood": 112} and census["positive_own_captures"] == sum(r["N_n"] > 0 for r in rows), "own washer census differs")
    peak = max(rows, key=lambda r: r["own_max_catalog_axial_Fy_corner"]["sampled_axial_only_Fy_required_mpa"])
    u.require(report["worsts"]["all_catalog_axial_Fy_required"]["capture_id"] == peak["capture_id"] and report["worsts"]["all_catalog_axial_Fy_required"]["scenario"] == peak["own_max_catalog_axial_Fy_corner"], "catalog washer global peak selection differs")
    return {"own_ends": 200, "wood_ends": 112, "steel_ends": 88, "nominal_and_catalog_ring_scenarios": 1000,
            "largest_catalog_axial_only_required_Fy_mpa": peak["own_max_catalog_axial_Fy_corner"]["sampled_axial_only_Fy_required_mpa"], "actual_product_strength_established": False}


def shaft_references(check, report, field, catalog, roots):
    shafts = u.indexed(field["source_inputs"]["shafts"], "axis_id")
    cuts = u.indexed(field["common_shaft_section_cut_actions"], "axis_id")
    profiles = {round(r["nominal_diameter_in"]*25.4, 8): r for r in roots["profile_scenarios"]}
    dims = {round(r["diameter_in"]*25.4, 8): r for r in catalog["diameters"]}
    products = {(round(r["diameter_in"]*25.4, 8), round(r["nominal_length_in"]*25.4, 8)): r for r in catalog["bolts"]}
    rows = report["all100"]
    u.require(set(u.indexed(rows, "axis_id")) == set(shafts) and report["complete_bolt_resistance"] is None, "all current shafts and null complete bolt resistance required")
    fy = catalog["material_source"]["minimum_yield_psi"]*0.006894757293168361
    for row in rows:
        key = row["axis_id"]
        source, own_cuts = shafts[key], cuts[key]["cuts"]
        diameter = round(source["diameter_mm"], 8)
        product = products[diameter, round(source["source_axis"]["nominal_under_head_length_mm"], 8)]
        body, root = dims[diameter]["full_body_min_in"]*25.4, profiles[diameter]["downward_4dp_design_floor_mm"]
        floor = product["Lb_min_in"]*25.4
        scores = []
        for cut in own_cuts:
            distance = cut["station_from_axis_point_mm"]-source["shaft_interval_mm"][0]
            chosen = root if distance > floor else body
            scores.append((u.circle_stress(cut["local_N_V1_V2_T_M1_M2_n_nmm"], chosen), cut, distance, chosen))
        peak = row["governing"]
        chosen = next(v for v in scores if v[1]["station_from_axis_point_mm"] == peak["station_from_axis_point_mm"])
        u.require(row["cut_count"] == len(own_cuts) and peak["same_cut_n_nmm"] == chosen[1]["local_N_V1_V2_T_M1_M2_n_nmm"] and peak["diameter_scenario_mm"] == chosen[3], "catalog diameter/complete cut selection differs")
        check.number(peak["same_cut_vm_envelope_mpa"], chosen[0], "rich-shaft/same-cut-stress")
        check.number(chosen[0], max(v[0] for v in scores), "rich-shaft/catalog-maximum")
        check.number(peak["specified_material_first_yield_index"], chosen[0]/fy, "rich-shaft/material-marker")
        check.number(peak["underhead_distance_mm"], chosen[2], "rich-shaft/underhead-distance")
        check.number(row["reference_root_floor_mm"], root, "rich-shaft/root-scenario")
        check.number(row["material_specification_Fy_mpa"], fy, "rich-shaft/Fy-scenario")
        u.require(row["ordinary_UNC_guarantees_this_root_floor"] is False and row["root_notch_or_ASD_or_complete_bolt_acceptance"] is False and peak["region"] == ("conditional_root_or_runout_floor" if chosen[2] > floor else "catalog_minimum_body_circle"), "catalog purchase scenario must not qualify actual bolt")
    u.require(report["first_yield_reference_exceedances"] == [r["axis_id"] for r in rows if r["governing"]["specified_material_first_yield_index"] > 1], "catalog shaft reference exceedances omitted")
    return {"shafts": 100, "first_yield_reference_exceedances": report["first_yield_reference_exceedances"], "complete_bolt_resistance": None}


def check_case(report, field, coarse, case, geometry, parent, catalog, roots):
    common(report, field, coarse, case)
    check = u.Comparison()
    findings = report["findings"]
    for nested in (findings["timber"], findings["washers"]):
        u.require(nested["source_sha256"] == report["source_sha256"], "nested current source union differs")
    material = findings["static_material_evidence"]
    u.require(material["delivered_hardware_inspected"] is False and material["material_receipts_are_purchase_scenarios"] is True, "purchase evidence must not imply delivered inspection")
    for source in material["root_evidence_maps"]:
        data = u.read(ROOT / source["path"], source["raw_sha256"])[source["key"]]
        u.require(u.canonical(data) == source["canonical_sha256"] and source["historical_field_or_viewer_map_imported_as_current"] is False, "historical material evidence source-map binding differs")
        if "count" in source:
            u.require(len(data) == source["count"], "historical material source-map census differs")
    scenarios = {r["comparison"]["id"]: r for r in findings["rich_steel"]}
    u.require(len(scenarios) == len(findings["rich_steel"]) == 2 and set(scenarios) == set(SCENARIOS), "both independent thickness/radius scenarios required")
    mixed = next(r["mixed_shared_stack_axis_ids_resistance_still_null"] for r in COARSE_DATA["cases"] if r["case_id"] == case)
    u.require(set(findings["missing_current_inputs"]["mixed_stacks"]) == set(mixed) and set(findings["missing_current_inputs"]) == {"mixed_stacks", "finished_sections", "groups_and_splitting", "restraint_and_complete_joints", "washers"}, "current missing strength inputs must remain explicit")
    result = {"case_id": case, "state_id": field["state_id"],
              "steel": [steel(check, scenarios[key], field) for key in SCENARIOS],
              "timber": timber(check, findings["timber"], field, mixed),
              "shaft": shaft_references(check, findings["shaft"], field, catalog, roots),
              "washers": washers(check, findings["washers"], field, geometry, parent, coarse)}
    result["scalar_comparisons"] = check.count
    result["maximum_absolute_arithmetic_errors_by_quantity_family"] = dict(sorted(check.errors.items()))
    return result


def negative_controls(report, field, coarse):
    rejected = []

    def reject(label, value, mutate, evaluate):
        altered = copy.deepcopy(value)
        mutate(altered)
        try:
            evaluate(altered)
        except (ValueError, KeyError):
            rejected.append(label)
        else:
            raise ValueError("rich reviewer accepted altered evidence: " + label)

    reject("wrong_current_field_binding", {k: v for k, v in report.items() if k != "findings"}, lambda r: r.update(raw_field_sha256="0"*64), lambda r: common(r, field, coarse, field["case_id"]))
    scenario = report["findings"]["rich_steel"][0]
    reject("changed_reference_scenario", scenario, lambda r: r["comparison"].update(thickness_mm=7), lambda r: steel(u.Comparison(), r, field))
    reject("omitted_heel_exceedances", scenario, lambda r: r["summary"]["radius_conditioned_heel_component_with_gravity"].update(comparison_count=0), lambda r: steel(u.Comparison(), r, field))
    row = report["findings"]["washers"]["all200_own_end_diagnostics"][0]
    scenario = row["nominal_own_hardware_geometry"]
    reject("changed_ring_pressure", scenario, lambda r: r.update(uniform_supported_ring_mean_mpa_geometric_diagnostic=1e6), lambda r: washer_scenario(u.Comparison(), r, row, 625*0.006894757293168361))
    reject("invented_washer_product_strength", scenario, lambda r: r.update(actual_product_Fy_mpa=235), lambda r: washer_scenario(u.Comparison(), r, row, 625*0.006894757293168361))
    return rejected


COARSE_DATA = None


def main():
    global COARSE_DATA

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    u.require(args.out is None or args.out.resolve().parent == OWN.parent and not args.out.exists(), "fresh receipt in owned review directory required")
    COARSE_DATA = u.read(COARSE, COARSE_SHA)
    u.require(COARSE_DATA["all_six_case_coverage"] is True and COARSE_DATA["findings"] == [] and set(COARSE_DATA["reviewed_case_ids"]) == set(TARGETS), "exact clean six-case coarse review required")
    direct = {u.relative(OWN): u.sha(OWN), u.relative(UTILITY): UTILITY_SHA, u.relative(COARSE): COARSE_SHA}
    reports, union = {}, dict(direct)
    for case, digest in TARGETS.items():
        path = MECH / "current-component-followup-results-v1" / case / "attempt01/result.json"
        reports[case] = u.read(path, digest)
        u.merge(direct, {u.relative(path): digest})
        u.merge(union, reports[case]["source_sha256"])
    u.merge(direct, COARSE_DATA["targets_and_direct_sources_sha256"])
    u.merge(union, direct)
    u.require(union[u.relative(FOLLOWUP)] == FOLLOWUP_SHA, "exact followup consumer source required")
    u.verify(union)
    geometry, parent, catalog, roots = [u.read(path, union[u.relative(path)]) for path in (u.GEOMETRY, PARENT, CATALOG, ROOTS)]
    results, controls = [], None
    for case, report in reports.items():
        field_path = MECH / "current-cases-v1" / case / "attempt01/field.json"
        component_path = MECH / "current-component-results-v1" / case / ("attempt02" if case == "k12-right" else "attempt01") / "result.json"
        field = u.read(field_path, direct[u.relative(field_path)])
        coarse = u.read(component_path, direct[u.relative(component_path)])
        results.append(check_case(report, field, coarse, case, geometry, parent, catalog, roots))
        if controls is None:
            controls = negative_controls(report, field, coarse)
    u.require(not any(name in sys.modules for name in ("numpy", "scipy", "cadquery", "OCP", "scripts.thin_bolted_panel_coupled")), "review must not import computational producers or CAD")
    u.verify(union)
    receipt = {
        "schema": "eoere_current_rich_component_actual_output_independent_review/v1",
        "status": "CLEAN_SAVED_SIX_CASE_IDENTITIES_CENSUS_SCENARIOS_AND_SUMMARIES", "findings": [],
        "targets_and_direct_sources_sha256": dict(sorted(direct.items())),
        "source_union": {"paths": len(union), "canonical_sha256": u.canonical(union), "derivation": "union of six exact rich result source_sha256 maps and targets_and_direct_sources_sha256", "every_source_file_hashed_before_and_after": True},
        "cases": results, "negative_controls_rejected": controls,
        "execution": {"stdlib_only_and_own_frozen_review_utilities": True, "saved_JSON_and_streaming_source_hash_reads_only": True,
                      "genuine_producer_reducer_or_admission_gate_import_or_call": False, "CAD_native_global_or_panel_operator_execution": False,
                      "shared_document_or_source_writes_staging_or_commits": False},
        "limits": [
            "Authenticates exact current source, field/admission and six-case coarse review bindings. Relies upon their completed numerical admissions; no gate or component reducer is rerun.",
            "Checks census, source action selection, scalar scenario/reference ratios, current catalog-circle sample maxima, washer ring arithmetic, retained nulls and steel/timber summary selection. Does not reproduce rich steel event searches, curved heel fields, timber six-mode resistance derivations, signed placement rays, washer plate solutions or landing geometry.",
            "Thickness/radius t6/r6 and t6.35/r6.35 are separate fixed-action scenarios at the unchanged6.35mm source geometry. Reference exceedances remain recorded; a source numerical pass is not a strength pass.",
            "All eight mixed/shared stacks, current finished net sections, signed groups/splitting, actual restraint and complete joints remain unresolved. Actual delivered hardware and tool/product observations remain unknown.",
            "Nominal support carry, ring mean pressure, conditional catalog roots/body windows and unadopted material markers are distinct from actual pressure bounds or product capacities. No fabrication, physical-work or climbing release follows.",
        ],
        "command": list(sys.orig_argv), "python": sys.version, "complete_joint_resistance": None, "release": dict(u.RELEASE),
    }
    payload = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False)+"\n").encode()
    u.verify(union)
    if args.out:
        with args.out.open("xb") as stream:
            stream.write(payload)
        u.verify(union)
    import hashlib

    print(json.dumps({"status": receipt["status"], "cases": list(TARGETS), "source_union_paths": len(union),
                      "scalar_comparisons": sum(r["scalar_comparisons"] for r in results), "negative_controls": len(controls),
                      "helper_sha256": direct[u.relative(OWN)], "receipt_sha256": hashlib.sha256(payload).hexdigest() if args.out else None,
                      "receipt": u.relative(args.out) if args.out else None}, sort_keys=True))


if __name__ == "__main__":
    main()
