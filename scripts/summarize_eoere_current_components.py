"""Compact six-case current component and selected finished-section evidence.

Consume exact saved outputs and genuine admissions. Select whole witnesses;
do not run a mechanics solver, repeat geometry queries or establish acceptance.
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
from pathlib import Path

from scripts import eoere_current_components as component
from scripts import eoere_current_response as current
from scripts import eoere_current_sections as section
from scripts.summarize_eoere_current_response import SEQUENCE, canonical_sha

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
STATIC = {"path": str(component.PACKET.parent.relative_to(current.ROOT)) + "/structural-assessment.json",
          "sha256": "399940c85b7cfda17cc971e9e5eeeedb7699c1099091652c99fede5194fc1261"}
LIMITS = ["Same-case first-order component references only; all complete-joint and finished-member capacities remain null.",
          "Generic screw head/withdrawal references are not Hillman product strength, lateral interaction, punching or end-distance qualification.",
          "Gross full-length K1/fully-braced and prismatic shear/torsion sensitivities do not qualify actual restraints or finished sections."]


def own_ref():
    component.canonical_dependency()
    current.require(current.sha(OWN) == LOADED_SHA, "loaded current component summary changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


def verify_saved_case(data, process, binding, summary, result_ref, input_ref):
    """Bind raw outputs to the actual current case, command and producer."""
    current.require(data["schema"] == "eoere_selected_hardware_current_component_case/v1"
                    and data["producer"] == component.own_ref() and data["case_id"] == binding["case_id"]
                    and data["state_id"] == binding["state_id"] and data["field"] == binding["field"]
                    and data["admission"] == binding["admission"] and data["geometry"] == summary["geometry"]
                    and data["hardware_model"] == summary["hardware_model"] and data["release"] == summary["release"],
                    "exact current saved component identity required")
    current.require(data["complete_joint_resistance"] is None and data["finished_member_capacity"] is None
                    and data["native_or_global_solve_performed"] is False and data["historical_pass_or_actions_transferred"] is False,
                    "unreleased reference-only component boundary required")
    # The capture records where execution happened. Restoring identical raw
    # evidence elsewhere must not rewrite that provenance to the live root.
    captured_root, result_path = Path(process["cwd"]), Path(result_ref["path"])
    current.require(captured_root.is_absolute() and not result_path.is_absolute()
                    and ".." not in result_path.parts, "absolute captured cwd and repository-relative result required")
    command = [process["command"][0], "-B", "-m", "scripts.eoere_current_components", "--case-id", binding["case_id"],
               "--out", str(captured_root/result_path)]
    required = {r["path"]: r["sha256"] for r in [component.own_ref(), input_ref, binding["field"], binding["admission"]]}
    current.require(process["schema"] == "eoere_current_component_process_capture/v1"
                    and process["case_id"] == binding["case_id"] and process["result"] == result_ref
                    and process["command"] == command
                    and process["controlled_environment"] == {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}
                    and process["status"] == "FINISHED" and process["exit_code"] == 0
                    and process["historical_state_or_actions_used"] is False
                    and process["pins_unchanged"] is True and process["pins_before"] == process["pins_after"]
                    and all(process["pins_before"].get(p) == h for p, h in required.items()),
                    "successful own component process and unchanged source pins required")
    current.require(datetime.datetime.fromisoformat(process["started_at_utc"]) <= datetime.datetime.fromisoformat(process["finished_at_utc"]),
                    "component process timestamps reversed")


def stability_findings(rows):
    records = []
    for row in rows:
        witnesses = [{"witness": name, "station_global_grain_projection_mm": w["station_global_grain_projection_mm"],
                      **w["gross_CD1_comparison"]["full_length_K1_pin_end_normal_sensitivity"]}
                     for name, w in row["witnesses"].items()]
        records.append({"member": row["member"], "span_mm": row["source_span_mm"],
                        "weak_column_domain_limit_mm": 50*min(row["source_width_mm"], row["source_depth_mm"]),
                        "full_length_over_weak_column_domain_limit": row["source_span_mm"]/(50*min(row["source_width_mm"], row["source_depth_mm"])),
                        "two_saved_witness_sensitivities": witnesses, "actual_restraint_or_complete_resistance": None})
    return {"member_count": len(records), "saved_sampled_witness_count": sum(len(r["two_saved_witness_sensitivities"]) for r in records),
            "all_member_witness_records": records,
            "full_length_domain_exceedances": [{k: r[k] for k in ["member", "span_mm", "weak_column_domain_limit_mm", "full_length_over_weak_column_domain_limit"]}
             for r in records if r["full_length_over_weak_column_domain_limit"] > 1.],
            "largest_saved_K1_normal_sensitivity": max([{"member": r["member"], **w} for r in records
             for w in r["two_saved_witness_sensitivities"]], key=lambda w: w["interaction_ratio"]),
            "saved_witness_reference_exceedances": [{"member": r["member"], **w} for r in records
             for w in r["two_saved_witness_sensitivities"] if w["ratio_exceeds_one"]],
            "limits": "Two saved sampled witnesses per member, not a stability-extrema search; full-span K1 and fully-braced hypotheses do not credit actual brace/joint stiffness or deformed equilibrium."}


def screw_exceedances(rows):
    """Retain strict-threshold head IDs and complete same-axis thread witnesses."""
    heads = [r["axis_id"] for r in rows if r["generic_head_ratio_CD1"] > 1.]
    threads = [r for r in rows if r["generic_withdrawal_required_effective_thread_mm_CD1"] > r["gross_nominal_length_after_panel_mm"]]
    return {"generic_CD1_head_exceedance_axis_ids": heads,
            "all_screw_reference_scalars": [{k: r[k] for k in ("axis_id", "generic_head_ratio_CD1",
                "generic_withdrawal_required_effective_thread_mm_CD1", "gross_nominal_length_after_panel_mm")}
                | {"effective_thread_exceedance_witness": r if r in threads else None} for r in rows],
            "all_effective_thread_length_reference_exceedances": threads,
            "reference_counts": {"axes": len(rows), "generic_CD1_head_exceedances": len(heads),
                                 "effective_thread_length_exceedances": len(threads)}}


def add_steel_disclosures(saved, compact):
    """Keep every existing steel reference scalar and whole exceeding witness."""
    current.require([r["comparison"] for r in saved] == [r["comparison"] for r in compact], "own steel scenarios required")
    for raw, scenario in zip(saved, compact, strict=True):
        bands = [b for a in raw["angles"] for b in a["bands"]]
        bores = [b for a in raw["angles"] for b in a["used_hole_bearing_tearout"]]
        groups = {
            "physical_cut_nominal_combined": [b["governing"]["governing_combined"] for b in bands],
            "near_hole_nominal_combined": [b["near_hole"]["governing_combined"] for b in bands],
            "far_hole_nominal_combined": [b["far_hole"]["governing_combined"] for b in bands],
            "radius_conditioned_heel_component_with_gravity": [b["heel_component"] for b in bands],
            "separate_whole_flange_torsion_warping": [b for a in raw["angles"] for b in a["whole_flange_torsion_warping_references"]],
            "used_hole_bearing": bores, "used_hole_tearout": bores,
            "unused_near_hole_net_shear": [b["unused_near_hole_center"] for b in bands],
        }
        current.require(groups.keys() == scenario["summary"].keys(), "all steel reference categories required")
        for name, rows in groups.items():
            category = scenario["summary"][name]
            metric = category["worst"]["saved_metric"]
            values = [r[metric] for r in rows]
            current.require(all(math.isfinite(v) and v >= 0 for v in values)
                            and len(values) == category["comparison_count"] and max(values) == category["worst"][metric]
                            and [v for v in values if v > 1.] == [w[metric] for w in category["exceedances"]]
                            and len(category["exceedances"]) == category["exceedance_count"], "complete own steel scalar/witness census required")
            category["all_reference_values"] = values
            category["whole_exceedance_witness_bindings"] = category["exceedances"]


def finished_findings(data, pointer, bindings):
    """Preserve every selected-plane exceedance and whole same-case extrema."""
    current.require(data["schema"] == "eoere_current_targeted_finished_sections/v1" and data["producer"] == section.own_ref()
                    and data["selected_unique_planes"] == 38 and data["same_plane_case_comparisons"] == 228
                    and data["source_pins_and_fields_unchanged"] is True and data["native_solve_or_CAD_rebuild"] is False
                    and data["continuous_finished_extrema_or_member_resistance"] is None,
                    "exact bounded current section output required")
    current.require([r["case_id"] for r in bindings] == SEQUENCE, "six own admitted section states required")
    states = {r["case_id"]: r["state_id"] for r in bindings}
    witnesses, planes = [], []
    for row in data["finished_sections"]:
        prop = row["section_properties"]
        planes.append({"member": row["member"], "station_global_grain_projection_mm": row["station_global_grain_projection_mm"],
                       "selection": row["selection"], "finished_source": row["finished_source"],
                       "finished_area_mm2": prop["finished_area_mm2"], "gross_stock_area_mm2": row["gross_stock_area_mm2"],
                       "centroid_xyz_mm": prop["centroid_xyz_mm"],
                       "centroidal_area_moment_matrix_uv_mm4": prop["centroidal_area_moment_matrix_uv_mm4"]})
        current.require([v["case_id"] for v in row["case_comparisons"]] == SEQUENCE, "six own cases at each plane required")
        for value in row["case_comparisons"]:
            current.require(value["state_id"] == states[value["case_id"]], "same admitted case/state at each plane required")
            witnesses.append({"member": row["member"], "station_global_grain_projection_mm": row["station_global_grain_projection_mm"],
                              "finished_area_mm2": prop["finished_area_mm2"], **value})
    current.require(len(planes) == 38 and len(witnesses) == 228 and len({r["member"] for r in planes}) == 22
                    and len({(r["member"], r["station_global_grain_projection_mm"]) for r in planes}) == 38,
                    "all current members and selected planes required")
    normal = lambda r: r["normal_reference"]["fully_braced_linear_normal_CD1_reference_index"]
    shear = lambda r: r["necessary_mean_shear_over_CD1_Fv"]
    per_case = [{"case_id": k, "normal_worst": max([r for r in witnesses if r["case_id"] == k], key=normal),
                 "necessary_shear_worst": max([r for r in witnesses if r["case_id"] == k], key=shear)} for k in SEQUENCE]
    return {"raw_result": pointer, "producer": data["producer"], "tool_versions": data["tool_versions"],
            "selected_unique_planes": 38, "same_plane_case_comparisons": 228, "members": 22,
            "planes": planes, "per_case_worst_witnesses": per_case,
            "all_selected_plane_reference_scalars": [{k: r[k] for k in (
                "member", "station_global_grain_projection_mm", "case_id", "state_id", "necessary_mean_shear_over_CD1_Fv")}
                | {"fully_braced_linear_normal_CD1_reference_index": normal(r),
                   "exceedance_witness": r if normal(r) > 1. or shear(r) > 1. else None} for r in witnesses],
            "maximum_normal_reference": max(witnesses, key=normal), "maximum_necessary_mean_shear": max(witnesses, key=shear),
            "all_selected_plane_normal_reference_exceedances": [r for r in witnesses if normal(r) > 1.],
            "all_selected_plane_necessary_shear_reference_exceedances": [r for r in witnesses if shear(r) > 1.],
            "continuous_finished_member_resistance": None, "limits": data["limits"]}


def summarize(sections_ref):
    own_ref()
    input_ref = current.ref(component.INPUTS)
    config = current.read(input_ref)
    forces = current.read(config["current_response"])
    current.require(forces["case_sequence"] == SEQUENCE and forces["all_six_saved_field_admissions_pass"] is True
                    and forces["geometry"] == current.manifest()["references"]["geometry"]
                    and forces["hardware_model"] == current.manifest()["references"]["hardware"]
                    and forces["extra_grid"] is False and forces["release"] == current.manifest()["release"],
                    "exact current six-case response required")
    pins = {r["path"]: r["sha256"] for r in [own_ref(), component.canonical_dependency(), input_ref, config["current_response"], sections_ref, STATIC]}
    static, saved_sections = current.read(STATIC), current.read(sections_ref)
    current.require(saved_sections["geometry"] == forces["geometry"] and saved_sections["hardware_model"] == forces["hardware_model"]
                    and saved_sections["extra_grid"] is False and saved_sections["release"] == forces["release"], "same current section geometry/hardware required")
    selection = finished_findings(saved_sections, sections_ref, forces["cases"])
    pins = current.join(pins, saved_sections["source_sha256"])
    helper = component.load(config["methods"]["summary"], "current_saved_summary")
    cases = []
    with current.response_context() as (gate, _):
        for binding in forces["cases"]:
            case_id = binding["case_id"]
            folder = component.RAW / "cases-v1" / case_id / component.CASE_ATTEMPT
            pointer, process_ref = current.ref(folder/"components.json"), current.ref(folder/"process.json")
            data, process = current.read(pointer), current.read(process_ref)
            verify_saved_case(data, process, binding, forces, pointer, input_ref)
            section_binding = next(r for r in saved_sections["cases"] if r["case_id"] == case_id)
            current.require(section_binding == {"case_id": case_id, "state_id": binding["state_id"], "components": pointer,
                                                "field": binding["field"], "admission": binding["admission"]}, "section/current component join differs")
            raw = (current.ROOT/binding["field"]["path"]).read_bytes()
            current.require(current.sha(current.ROOT/binding["field"]["path"]) == binding["field"]["sha256"], "exact raw field required")
            field, admitted = gate.require_admitted_payload(raw, current.read(binding["admission"]), admission_sha256=current.LOADED_SHA)
            current.require(canonical_sha(field) == data["raw_field_canonical_sha256"]
                            and canonical_sha(field["source_inputs"]) == data["source_inputs_canonical_sha256"], "own admitted source identity required")
            coarse = helper.coarse_findings({**data, "limits": LIMITS})
            screws = data["component_reductions"]["simultaneous_Hillman_actions_and_generic_references"]
            coarse["generic_screw_references"].update(screw_exceedances(screws))
            coarse["generic_screw_references"]["Hillman_product_capacity_or_complete_end_interaction"] = None
            rich = helper.rich_findings(data)
            add_steel_disclosures(data["findings"]["rich_steel"], rich["steel_scenarios"])
            spacer = []
            for r in data["findings"]["washers"]["all200_own_end_diagnostics"]:
                if "spacer_bore_and_od_mm" in r:
                    spacer.append({k: r[k] for k in ["axis_id", "capture_id", "host", "N_n", "spacer_nominal_axial_mean_stress_mpa",
                        "spacer_strength_nut_contact_or_compatible_pressure_bound", "washer_loading_basis"]}
                        | {"nominal_washer_ring_reference": {k: r["nominal_own_hardware_geometry"][k] for k in ["ID_mm", "OD_mm", "t_mm",
                               "uniform_load_ring_outer_radius_mm", "sampled_axial_only_Fy_required_mpa", "raw_ring_Fc_perp625psi_mean_ratio_conditional",
                               "physical_contact_pressure_bound_mpa", "actual_product_Fy_mpa", "combined_washer_strength_index"]}}
                        | {"ideal_projected_mean_pressure_mpa": {kind: r["N_n"]/area for kind, area in static["spacer_contact"]["nominal_projection_areas_mm2"].items()},
                           "ideal_projection_is_not_actual_contact_or_pressure_bound": True})
            current.require(len(spacer) == 8, "eight current spacer nut references required")
            cases.append({"case_id": case_id, "state_id": data["state_id"], "field": binding["field"], "admission": binding["admission"],
                          "raw_components": pointer, "producer_process": process_ref,
                          "coarse": coarse, "rich": rich, "spacer_nuts": spacer,
                          "mixed_stack_statics": {k: v for k, v in data["connected_mixed_stack_statics"].items() if k != "own_surface_trials"}
                              | {"own_surface_count": len(data["connected_mixed_stack_statics"]["own_surface_trials"])},
                          "gross_member_stability": stability_findings(data["component_reductions"]["fresh_gross_member_diagnostics"]),
                          "support_screen": data["support_screen"], "release": forces["release"]})
            pins = current.join(pins, data["source_sha256"], admitted, process["pins_before"],
                                {r["path"]: r["sha256"] for r in [pointer, process_ref, binding["field"], binding["admission"], *process["logs"].values()]})
    current.verify(pins)
    own_ref()
    result = {"schema": "eoere_current_six_case_structural_references/v1", "status": "BOUNDED_CURRENT_REFERENCES_COMPLETE_RESISTANCE_UNKNOWN",
              "geometry_revision": forces["geometry_revision"], "hardware_revision": forces["hardware_revision"],
              "geometry": forces["geometry"], "hardware_model": forces["hardware_model"], "extra_grid": False,
              "current_response": config["current_response"], "component_inputs": input_ref,
              "component_producer": component.own_ref(), "section_producer": section.own_ref(), "summary_producer": own_ref(),
              "case_sequence": SEQUENCE, "cases": cases, "targeted_finished_sections": selection,
              "static_geometry_only_reused": {"source": STATIC, "thread_catalog_envelope_counts": static["thread_catalog_envelope_counts"],
                                             "raised_screw_placement": static["raised_screw_placement"],
                                             "spacer_projection_areas_mm2": static["spacer_contact"]["nominal_projection_areas_mm2"],
                                             "historical_actions_ratios_or_passes_transferred": False},
              "complete_joint_resistance": None, "finished_member_capacity": None, "Hillman_product_capacity": None,
              "structural_acceptance": False, "native_solve_performed": False, "CAD_rebuilt": False,
              "actual_build_fit_work_performed": False, "remedies_attempted": False, "physical_demand_bounds_established": False,
              "missing_inputs": {"Hillman": "Product steel/head/thread, lateral/withdrawal/punching interaction and current receiver/end strength; generic springs and references do not supply them.",
                 "mixed_contact": "Compatible multi-plane connected wood/steel/shaft/thread/contact yield for eight mixed stacks; equilibrated affine bearing trials are statics only.",
                 "all_complete_joints": "Current signed group action/splitting/row and block fracture, axial/couple/bearing/washer/flange interaction and justified local joint restraint at all24 duties.",
                 "hardware_contact": "Delivered thread/runout conformance and root-floor specification, nut/spacer/washer contact/compliance, local pressure/prying and washer/spacer product resistance.",
                 "Eoere": "Product minimum thickness, heel radius/shape, material minima, heel/hole/rupture and complete fitting behavior; nominal Q235/6- or6.35-mm scalar scenarios are not a rating.",
                 "members": "Continuous finished critical sections and local hole/notch shear/torsion/fracture, connection development and justified bracing/effective lengths; only38 exact planes were compared.",
                 "panels": "Product/direction/adjustments, local holes/countersinks, screw/head punching and complete participation; current homogeneous linear-plate components retain exceedances.",
                 "support_applicability": "Actual no-slip friction/local pressure and distributed support/restraint, finished member/joint/screw stiffness and first-order applicability at the recorded motion/rotation. No physical demand bound."},
              "limits": LIMITS, "release": forces["release"]}
    return result, pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sections", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-map", type=Path, required=True)
    args = parser.parse_args()
    for path in [args.out, args.source_map]:
        path.parent.mkdir(parents=True, exist_ok=True)
    fixed = current.load("bridge")
    with fixed.reserve(args.out) as output, fixed.reserve(args.source_map) as sources:
        result, pins = summarize(current.ref(args.sections))
        sources.write(dict(sorted(pins.items())))
        result["source_union"] = {"count": len(pins), "canonical_sha256": canonical_sha(pins),
                                  "record": current.ref(args.source_map), "all_sources_unchanged": True}
        output.write(result)
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
