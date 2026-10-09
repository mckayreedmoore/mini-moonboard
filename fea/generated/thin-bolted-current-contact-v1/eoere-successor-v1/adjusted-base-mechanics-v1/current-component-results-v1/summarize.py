"""Select per-case witnesses from twelve exact saved component outputs.

No force reducer or model code is imported. Maxima select whole saved witnesses;
cases and scalar steel scenarios remain separate. Reserve a fresh summary first.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[6]
SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
CASES = ("a12-forward", "a12-rear", "a12-left", "k12-right", "k12-rear", "a1-rear")
GATE = "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643"
BASE = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/"
COARSE = BASE + "current-component-bridge-v1/consumer-v1/consume.py"
RICH = BASE + "current-component-bridge-v1/followups-v1/followups.py"
PRODUCERS = {COARSE: "f11175782c7b29abbdfbcbf5fbad63f919596bc6a613b4c7a5b65acc1027bad9",
             RICH: "a27bacf7260905f69c2a69bae60c0f2cf4ed1f4efd229100e3c8fb846b892798"}
RELEASE = dict.fromkeys(("candidate_accepted", "complete_joint_acceptance", "capacity_established",
                         "fabrication_released", "structural_released", "climbing_released"), False)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def checked(ref):
    path = (ROOT / ref["path"]).resolve()
    require(path.is_relative_to(ROOT), "saved report references must be inside repository")
    raw = path.read_bytes()
    require(sha(raw) == ref["sha256"], "saved bytes changed: " + ref["path"])
    return raw


def merge(pins, extra):
    for path, digest in extra.items():
        require(path not in pins or pins[path] == digest, "conflicting exact source: " + path)
        pins[path] = digest


def pick(row, keys):
    return {k: row[k] for k in keys if k in row}


def maximum(rows, key):
    require(rows and all(type(r[key]) in (int, float) and math.isfinite(r[key]) for r in rows), "finite saved witnesses required")
    return max(rows, key=lambda r: r[key])


def coarse_findings(data):
    r = data["component_reductions"]
    members = r["fresh_gross_member_diagnostics"]
    require(len(members) == 22 and len(r["angle_duties"]) == 22 and len(r["exterior_cleat_corners"]) == 2,
            "22 current members/22angles/two corners required")
    require(all(a["complete_group_heel_hole_prying_or_corner_resistance"] is None for a in r["angle_duties"])
            and all(a["complete_corner_splitting_group_or_bearing_resistance"] is None for a in r["exterior_cleat_corners"]), "24 complete joints must stay unknown")
    gross = {}
    for witness, metric in (("fully_braced_normal", "fully_braced_component_normal_interaction"),
                           ("sufficient_shear_torsion", "equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio")):
        rows = [{"member": row["member"], "value": row["witnesses"][witness]["gross_CD1_comparison"][metric],
                 **pick(row["witnesses"][witness], ("station_global_grain_projection_mm", "local_N_Vu_Vv_T_Mu_Mv_n_nmm", "signed_same_cut_wrench"))}
                for row in members]
        gross[metric] = {"worst": maximum(rows, "value"), "saved_witness_exceedances": [v for v in rows if v["value"] > 1.]}
    panels = r["six_panel_reductions"]["panel_diagnostics"]
    require(len(panels) == 6 and r["six_panel_reductions"]["sample_count_per_axis"] == 41, "six current panels/41 samples required")
    panel = {"per_panel": [{"panel": p["panel"], "section_components": p["resolved_section_diagnostics"]["components"],
                            "deformation": pick(p["deformation_diagnostics"], (
                                "maximum_sampled_abs_outward_w_mm", "maximum_sampled_affine_removed_warp_mm", "maximum_sampled_slope_norm",
                                "outward_w_witness_xy_mm", "warp_witness_xy_mm", "slope_witness_xy_mm", "linear_plate_applicability_established"))} for p in panels]}
    panel["sampled_section_exceedances_CD1"] = [{"panel": p["panel"], "component": k, **v} for p in panels
        for k, v in p["resolved_section_diagnostics"]["components"].items() if v["sampled_ratio_CD1"] > 1.]
    screws = r["simultaneous_Hillman_actions_and_generic_references"]
    require(len(screws) == 66 and len(r["own_shaft_circle_comparisons"]) == 100
            and len(r["own_washer_capture_diagnostics"]) == 200 and len(r["own_wood_bearing_resultants_from_admitted_field"]) == 120,
            "current100shaft/200capture/120wall/66screw census required")
    screw = {"all66_own_axes": True, "generic_CD1_head_exceedance_axis_ids": [s["axis_id"] for s in screws if s["generic_head_ratio_CD1"] > 1.]}
    for metric in ("generic_head_ratio_CD1", "generic_withdrawal_required_effective_thread_mm_CD1", "same_axis_simultaneous_lateral_n"):
        screw[metric] = pick(maximum(screws, metric), ("axis_id", "panel", "receiver", metric, "withdrawal_n", "lateral_n", "gross_nominal_length_after_panel_mm"))
    return {"gross_raw_members": gross, "panels": panel, "generic_screw_references": screw,
            "complete24_joint_resistances": None, "source_limits": data["limits"]}


def rich_findings(data):
    r = data["findings"]
    require([s["comparison"]["id"] for s in r["rich_steel"]] == ["t6_r6", "t6p35_r6p35"], "separate original and owner steel scenarios required")
    timber = r["timber"]
    mixed = [s for s in timber["shaft_components"] if s["component"] is None]
    require(len(mixed) == 8 and len(timber["duties"]) == 24
            and all(d["complete_joint_resistance_n"] is None for d in timber["duties"]), "24 unknown joints and eight mixed stacks required")
    shafts = r["shaft"]["all100"]
    require(len(shafts) == 100 and r["shaft"]["complete_bolt_resistance"] is None, "100 reference-only shafts required")
    washer = r["washers"]
    require(washer["census"]["physical_end_captures"] == 200
            and washer["reviewed_nominal_seat_geometry"]["nominal_wood_seats"] == 112, "200 current ends and distinct112-seat geometry carry required")
    def steel_witness(row, metric):
        comparison = row.get("comparison", row)
        return {**pick(row, ("body", "flange", "port_id", "axis_id")), "saved_metric": metric,
                **pick(comparison, (metric, "station_mm", "side", "force_N_V1_V2_n", "moment_T_M1_M2_nmm",
                    "net_centroid_moment_T_M1_M2_nmm", "nominal_equivalent_mpa", "inside_radius_scenario_mm",
                    "pure_bending_peak_mpa", "bounding_source_gravity_equivalent_mpa", "own_in_plane_bearing_n"))}
    steel = []
    for scenario in r["rich_steel"]:
        categories = {}
        for key, value in scenario["summary"].items():
            metric = {"used_hole_bearing": "bearing_reference_ratio", "used_hole_tearout": "tearout_reference_ratio",
                      "unused_near_hole_net_shear": "net_shear_rupture_reference_ratio"}.get(key, "conditional_combined_yield_reference_ratio")
            categories[key] = {"comparison_count": value["comparison_count"], "exceedance_count": value["exceedance_count"],
                               "worst": steel_witness(value["worst"], metric),
                               "exceedances": [steel_witness(row, metric) for row in value["exceedances"]]}
        steel.append({"comparison": scenario["comparison"], "summary": categories, "fixed_actions_only": True, "product_strength": None})
    def washer_witness(row):
        if row is None:
            return None
        return {**pick(row, ("axis_id", "capture_id", "end", "host", "receiver_kind", "diameter_mm", "N_n", "value")),
                "scenario": pick(row["scenario"], ("ID_mm", "OD_mm", "t_mm", "sampled_axial_only_Fy_required_mpa",
                    "Fy_33ksi_reference_ratio_unadopted", "uniform_supported_ring_mean_mpa_geometric_diagnostic",
                    "nominal_supported_ring_Fc_perp625psi_mean_reference_index", "raw_ring_Fc_perp625psi_mean_ratio_conditional"))}
    worsts = {k: ({d: washer_witness(row) for d, row in value.items()} if k == "by_diameter" else washer_witness(value))
              for k, value in washer["worsts"].items()}
    timber_summary = {k: value for k, value in timber["summary"].items() if k != "worst_components"}
    timber_summary["worst_component"] = timber["summary"]["worst_components"][0]
    timber_summary["unadjusted_exceedance_axis_ids"] = [s["axis_id"] for s in timber["shaft_components"]
        if s["component"] is not None and s["component"]["exceeds_unadjusted_component_reference"]]
    timber_summary["Cdelta0p5_Cg1_CD1_sensitivity_exceedance_axis_ids"] = [s["axis_id"] for s in timber["shaft_components"]
        if s["component"] is not None and s["component"]["Cdelta0p5_Cg1_CD1_sensitivity_ratio"] > 1.]
    return {"steel_scenarios": steel,
            "timber": {"summary": timber_summary, "mixed_stacks": [pick(s, ("axis_id", "disposition", "missing_method")) for s in mixed],
                       "all24_complete_joint_resistances": None, "limits": timber["unsupported_mechanisms"]},
            "shaft": {"worst": max(shafts, key=lambda s: s["governing"]["specified_material_first_yield_index"]),
                      "first_yield_reference_exceedances": r["shaft"]["first_yield_reference_exceedances"], "complete_bolt_resistance": None},
            "washers": {"census": washer["census"], "worsts": worsts,
                        "exceeded_reference_diagnostics": washer["exceeded_reference_diagnostics"], "limits": washer["limits"],
                        "nominal_seat_geometry": washer["reviewed_nominal_seat_geometry"],
                        "geometry_composition_canonical_sha256": canonical(washer["geometry_composition"])},
            "missing_current_inputs": r["missing_current_inputs"]}


def build(manifest, manifest_ref):
    require(manifest["schema"] == "eoere_exact_six_case_component_summary_inputs/v1"
            and tuple(r["case_id"] for r in manifest["cases"]) == CASES, "six exact ordered case bindings required")
    require(manifest["source_sha256"][str(OWN.relative_to(ROOT))] == SHA, "exact summary program required")
    pins = dict(manifest["source_sha256"])
    merge(pins, {manifest_ref["path"]: manifest_ref["sha256"], **PRODUCERS})
    rows = []
    for binding in manifest["cases"]:
        loaded = {k: json.loads(checked(binding[k])) for k in ("field", "admission")}
        field, admission = loaded["field"], loaded["admission"]
        identity = {k: field[k] for k in ("state_id", "case_id", "accessory_placement")}
        require(identity["case_id"] == binding["case_id"] and all(admission[k] == v for k, v in identity.items())
                and admission["schema"] == "eoere_extended_cleat_fixed_floor_independent_field_admission/v1"
                and admission["current_extended_cleat_equilibrium_and_recovery_pass"] is True
                and field["release"] == RELEASE and admission["release"] == RELEASE, "own unreleased admitted case required")
        require(field["schema"] == "eoere_extended_cleat_fixed_floor_candidate/v1"
                and field["source_inputs"]["geometry"] == manifest["geometry"], "exact current field geometry/schema required")
        saved = {}
        for kind, producer in (("coarse", COARSE), ("rich", RICH)):
            refs = binding[kind]
            result, process = json.loads(checked(refs["result"])), json.loads(checked(refs["process"]))
            for log in ("stdout", "stderr"):
                checked(refs[log])
            require(process["exit_code"] == 0 and all(result[k] == v for k, v in identity.items())
                    and result["raw_field_sha256"] == binding["field"]["sha256"]
                    and result["field_admission_receipt_sha256"] == binding["admission"]["sha256"]
                    and result["fresh_gate_sha256"] == GATE and result["release"] == RELEASE
                    and result["complete_joint_resistance"] is None, "exact successful same-case component result required")
            expected_schema = ("eoere_extended_cleat_same_state_conditional_component_receipt/v1" if kind == "coarse"
                               else "eoere_current_same_state_followup_component_references/v1")
            require(result["schema"] == expected_schema and result["current_geometry"] == manifest["geometry"]["report"]
                    and result["current_saved_descriptors"] == manifest["geometry"]["cached_source_export"], "own current result schema/geometry/descriptors required")
            require(result["source_sha256"][producer] == PRODUCERS[producer]
                    and result["source_inputs_canonical_sha256"] == canonical(field["source_inputs"]), "own frozen producer/current source binding required")
            environment = process.get("environment", process.get("controlled_environment", {}))
            require(environment.get("OPENBLAS_NUM_THREADS") == environment.get("OMP_NUM_THREADS") == "1", "serialized single-thread environment required")
            require((ROOT / process["command"][2]).resolve() == ROOT / producer, "exact frozen CLI required")
            command = process["command"]
            require(process["cwd"] == str(ROOT)
                    and (ROOT / command[command.index("--field")+1]).resolve() == ROOT / binding["field"]["path"]
                    and (ROOT / command[command.index("--receipt")+1]).resolve() == ROOT / binding["admission"]["path"], "exact recorded command field/admission/cwd required")
            if kind == "coarse":
                require(process["command"][process["command"].index("--samples")+1] == "41", "original41 sample grid required")
            merge(pins, result["source_sha256"])
            merge(pins, {r["path"]: r["sha256"] for r in refs.values()})
            saved[kind] = {"bindings": refs, "source_map_count": len(result["source_sha256"]),
                           "source_map_canonical_sha256": canonical(result["source_sha256"]),
                           "process_elapsed_seconds": process["elapsed_seconds"],
                           "findings": coarse_findings(result) if kind == "coarse" else rich_findings(result)}
        merge(pins, {binding[k]["path"]: binding[k]["sha256"] for k in ("field", "admission")})
        rows.append({**identity, "field": binding["field"], "admission": binding["admission"], **saved})
    for path, digest in pins.items():
        require(sha((ROOT / path).read_bytes()) == digest, "source union changed: " + path)
    return {"schema": "eoere_exact_current_six_case_component_summary/v1", "source_manifest": manifest_ref,
            "source_sha256": manifest["source_sha256"], "verified_source_union": {"count": len(pins), "canonical_sha256": canonical(pins)},
            "current_geometry": manifest["geometry"], "cases": rows, "complete_joint_resistance": None, "release": RELEASE,
            "limits": ["Per-case saved witnesses only; no component maxima, loads or scalar scenarios combined across cases.",
                       "Steel6/r6 and6.35/r6.35 are fixed-action references; product/formed heel resistance is unknown.",
                       "All24 complete joints, eight mixed stacks, signed group/splitting/finished-section and restraint capacities remain unknown.",
                       "Nominal112-seat geometry carry establishes no current pressure or strength. Washer pressure, product strength and combined interaction remain unknown.",
                       "Generic Hillman and panel spatial references do not establish product fastener/installation or local opening/hold/head-seat resistance; no panel remedy is adopted.",
                       "Fixed-floor support is an analytical assumption; no physical floor, parts or build acceptance follows."],
            "execution": {"saved_JSON_and_source_bytes_only": True, "reducers_CAD_K_global_native_or_browser_called": False}}


def write(stream, value):
    stream.seek(0)
    json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
    stream.write("\n")
    stream.truncate()
    stream.flush()
    os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    attempt = {"schema": "eoere_six_case_summary_attempt/v1", "status": "STARTED", "release": RELEASE}
    with args.out.open("x") as stream:
        write(stream, attempt)
        try:
            ref = {"path": args.manifest, "sha256": args.manifest_sha256}
            result = build(json.loads(checked(ref)), ref)
            write(stream, result)
        except BaseException as error:
            attempt.update(status="FAILED", exception={"type": type(error).__name__, "message": str(error)})
            write(stream, attempt)
            raise
    print(json.dumps({"output": str(args.out), "cases": len(result["cases"]), "sha256": sha(args.out.read_bytes())}))


if __name__ == "__main__":
    main()
