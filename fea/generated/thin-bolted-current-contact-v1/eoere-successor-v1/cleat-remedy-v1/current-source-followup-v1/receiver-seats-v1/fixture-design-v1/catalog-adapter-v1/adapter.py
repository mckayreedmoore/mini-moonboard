"""Catalog-dimension adaptation of the frozen generic paired fixture.

Preserve unmet generic error allowances, nominal bit comparisons and actual
unknowns. Scalar source arithmetic only; no CAD or physical operation.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import math
import os
import runpy
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
HERE = OWN.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
INPUT = HERE / "inputs.json"
INPUT_SHA = "dd0df7d6b5eb30aab11184c4d4471333e545b270232333ba9577678c9155282d"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes(), parse_constant=lambda _: require(False, "nonfinite JSON"))


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "frozen source changed: " + path)


def load():
    require(sha(INPUT) == INPUT_SHA, "exact catalog adapter inputs required")
    inp = read(INPUT)
    pins = dict(inp["source_sha256"])
    pins.update({str(INPUT.relative_to(ROOT)): INPUT_SHA, str(OWN.relative_to(ROOT)): sha(OWN)})
    verify(pins)
    facts = read(ROOT / inp["catalog_facts_path"])
    pdf = facts["sources"]["FISCH_pen_drill"]["raw_active_cache"]
    pins[pdf["path"]] = pdf["sha256"]
    require((ROOT / pdf["path"]).stat().st_size == pdf["bytes"], "shared primary PDF byte count")
    generic_method = runpy.run_path(str(HERE.parent / "design.py"))
    old_input, replay, shapes = generic_method["evaluate"]()
    saved = read(ROOT / inp["generic_fixture_result_path"])
    require(replay == {k: v for k, v in saved.items() if k != "drawing"}, "generic result arithmetic differs")
    for path, digest in saved["source_sha256"].items():
        require(path not in pins or pins[path] == digest, "source pin contradiction")
        pins[path] = digest
    verify(pins)
    return inp, facts, old_input, saved, shapes, generic_method, pins


def calculate():
    inp, facts, generic_inp, generic, _shapes, method, pins = load()
    sources = facts["sources"]
    catalog = sources["Carr_Lane_H"]["facts"]
    install = sources["Carr_Lane_installation"]["facts"]
    d, c, e = generic_inp["dimensions_mm"], inp["changes"], inp["retained_error_conditions"]
    require(catalog["body_OD_nominal_mm"] == 15.875
            and catalog["underhead_length_nominal_mm"] == 19.05
            and catalog["head_OD_F_nominal_mm"] == 20.240625
            and catalog["head_height_G_nominal_mm"] == 5.55625
            and catalog["H_40_12_row_has_counterbore_asterisk"] is False,
            "catalog H-40-12 dimensional join")
    tolerance = install["unlisted_standard_ANSI_dimension_plus_minus_mm"]
    require(tolerance == .381 and install["recommended_metal_jig_hole_does_not_qualify_wood_plate"] is True,
            "current tolerance/material boundary")
    length = catalog["underhead_length_nominal_mm"]
    head = catalog["head_height_G_nominal_mm"]
    flange = catalog["head_OD_F_nominal_mm"]
    length_range = [length-tolerance, length+tolerance]
    head_range = [head-tolerance, head+tolerance]
    flange_range = [flange-tolerance, flange+tolerance]
    require(length_range[0] > c["effective_contiguous_guidance_min_mm"], "guidance requirement exceeds shortest body")
    height_error = c["noncatalog_fixture_height_aggregate_deviation_max_mm"]
    feet_height = c["temporary_guide_feet_height_mm"]
    thickness = c["guide_thickness_nominal_mm"]
    plate_top = c["guide_top_w_nominal_mm"]
    wood_entry = d["guide_w"][0]
    require(abs(wood_entry+feet_height-c["guide_bottom_w_nominal_mm"]) < 1e-12
            and abs(c["guide_bottom_w_nominal_mm"]+thickness-plate_top) < 1e-12,
            "feet/guide wood-entry datum join")
    cap_bottom = plate_top + head
    cap_top = cap_bottom + c["cap_thickness_mm"]
    gap_range = [feet_height+thickness-height_error-length_range[1],
                 feet_height+thickness+height_error-length_range[0]]
    require(gap_range[0] > 0, "catalog body can reach frame wood")
    max_wood = 2*d["member_thickness"]+d["matched_stack_deviation_max"]
    nominal_path = cap_top-wood_entry+2*d["member_thickness"]+d["breakout_travel"]
    max_path = (cap_top-wood_entry+height_error+tolerance+c["cap_to_head_top_gap_design_mm"][1]
                + max_wood + d["breakout_travel"])
    # A contiguous effective segment of length Le entirely inside the body
    # has its last constrained point no higher than guide_top-Le. This includes
    # an unknown entrance/exit relief without pretending physical body length
    # is the effective guidance length.
    effective = c["effective_contiguous_guidance_min_mm"]
    max_last_guidance_to_far = feet_height+thickness+height_error-effective+max_wood+d["breakout_travel"]
    play = e["bushing_diametral_play_max_mm"]
    slop = play/2 + max_last_guidance_to_far*play/effective
    tilt = max_path*math.tan(math.radians(e["guide_normal_angle_max_deg"]))
    other = sum(e["other_relative_error_terms_mm"].values())
    needed = other + slop + tilt
    comparisons = {
        "guide_tilt": {"derived_bound_mm": tilt, "generic_allocation_mm": e["original_guide_tilt_allocation_mm"],
                       "excess_mm": max(0., tilt-e["original_guide_tilt_allocation_mm"]),
                       "within_generic_allocation": tilt <= e["original_guide_tilt_allocation_mm"]},
        "insert_play": {"derived_bound_mm": slop, "generic_allocation_mm": e["original_insert_slop_allocation_mm"],
                        "excess_mm": max(0., slop-e["original_insert_slop_allocation_mm"]),
                        "within_generic_allocation": slop <= e["original_insert_slop_allocation_mm"]},
        "relative_bore_screw": {"derived_bound_mm": needed, "generic_target_mm": e["relative_bore_screw_target_mm"],
                                "excess_mm": max(0., needed-e["relative_bore_screw_target_mm"]),
                                "within_generic_target": needed <= e["relative_bore_screw_target_mm"]}}
    require(not any(r.get("within_generic_allocation", r.get("within_generic_target")) for r in comparisons.values()),
            "recorded generic allowance exceedances changed")
    # Update temporary part intervals only, reusing the frozen generic part helper.
    new_d = copy.deepcopy(d)
    new_d["guide_w"] = [c["guide_bottom_w_nominal_mm"], plate_top]
    new_d["retainer_w"] = [cap_bottom, cap_top]
    new_d["cleat_guide_bottom_stop_w"][1] = c["cleat_guide_bottom_stop_w_top_nominal_mm"]
    new_parts = method["parts"](new_d)
    feet = []
    for name in ("guide_rear", "guide_front"):
        u, v = generic["support_and_clamp_requirements"]["pad_rectangles_uv_mm"][name]
        feet.append({"id": "guide_foot_"+name, "u_interval_mm": u, "v_interval_mm": v,
                     "w_interval_mm": [wood_entry, c["guide_bottom_w_nominal_mm"]],
                     "size_uvw_mm": [u[1]-u[0], v[1]-v[0], feet_height]})
    front_band = [d["cleat_bottom_v"], generic["support_and_clamp_requirements"]["pad_rectangles_uv_mm"]["guide_front"][1][0]]
    outlet_margin = min(d["bore_v"]-e["maximum_effective_cutting_diameter_mm"]/2-front_band[0],
                        front_band[1]-d["bore_v"]-e["maximum_effective_cutting_diameter_mm"]/2)
    require(outlet_margin > 0 and all(f["v_interval_mm"][0] > d["bore_v"]+e["maximum_effective_cutting_diameter_mm"]/2 for f in feet),
            "feet or stop block nominal front chip route")
    general = sources["Carr_Lane_design"]["facts"]["general_drilling_chip_gap_diameter_multipliers"]
    general_low = general[0]*e["maximum_effective_cutting_diameter_mm"]
    cap_hole_range = [c["cap_hole_nominal_D_mm"]-c["cap_hole_D_deviation_max_mm"],
                      c["cap_hole_nominal_D_mm"]+c["cap_hole_D_deviation_max_mm"]]
    capture = (flange_range[0]-cap_hole_range[1])/2-c["cap_hole_to_flange_axis_eccentricity_max_mm"]
    fastener = min(math.dist(a, [u, d["bore_v"]])
                   for a in d["retainer_fastener_centers_uv"] for u in d["bore_u"])
    fastener -= flange_range[1]/2+d["retainer_fastener_head_OD_max"]/2
    cap_top_free = head_range[1]+c["cap_thickness_mm"]+height_error+c["cap_to_head_top_gap_design_mm"][1]+length_range[1]-effective
    cap_slop = play/2+cap_top_free*play/effective
    cap_margin = (cap_hole_range[0]-e["maximum_effective_cutting_diameter_mm"])/2-cap_slop-c["cap_hole_to_flange_axis_eccentricity_max_mm"]
    require(capture > 0 and fastener > 0 and cap_margin > 0, "conditional catalog capture/access dimensions fail")
    bit = sources["FISCH_pen_drill"]["facts"]
    id_cases = []
    for nominal_in in inp["configured_ID_reference_in"]:
        nominal = nominal_in*25.4
        low, high = [nominal+t for t in catalog["ID_additional_standard_tolerance_mm"]]
        id_cases.append({"reference_ID_in": nominal_in, "reference_nominal_ID_mm": nominal,
                         "catalog_ID_interval_mm": [low, high],
                         "printed_FISCH_diameter_mm": bit["catalog_diameter_mm"],
                         "printed_nominal_diametral_gap_range_mm": [low-bit["catalog_diameter_mm"], high-bit["catalog_diameter_mm"]],
                         "minimum_effective_bit_guiding_D_for_declared_play_mm": high-play,
                         "actual_bit_fit_established": False})
    old_gaps = generic["nominal_primitive_clearance"]["cases"]
    actual_gap_body = old_gaps["current_body"]["minimum"]["capsule_separation_lower_bound_mm"]-needed
    hypothetical_gap = old_gaps["whole_screw_9p525_containing_capsule_reference"]["minimum"]["capsule_separation_lower_bound_mm"]-needed
    verify(pins)
    result = {"schema": "eoere_Z180_catalog_fixture_adapter/v1",
        "status": "CATALOG_DIMENSIONS_ADAPTED_GENERIC_ERROR_ALLOWANCES_NOT_CARRIED_FORWARD",
        "source_sha256": dict(sorted(pins.items())), "source_pin_count": len(pins), "sources_unchanged_before_after": True,
        "generic_fixture": {"result": inp["generic_fixture_result_path"], "unchanged_six_file_source_bytes": True,
                            "four_world_axes_and_handed_plan_unchanged": True},
        "catalog_source_facts": {"path": inp["catalog_facts_path"], "manufacturer_references": {k: v["url"] for k, v in sources.items()}},
        "catalog_dimensional_intervals_mm": {"underhead_body_length": length_range, "head_F_diameter": flange_range,
            "head_G_height": head_range, "body_OD": [catalog["body_OD_nominal_mm"]+t for t in catalog["body_OD_additional_tolerance_mm"]],
            "unlisted_dimension_plus_minus": tolerance},
        "temporary_parts": new_parts+feet,
        "cap_and_mounting": {"nominal_cap_bottom_w_mm": cap_bottom, "nominal_cap_top_w_mm": cap_top,
            "cap_opening_D_interval_mm": cap_hole_range, "conditional_minimum_radial_capture_lip_mm": capture,
            "conditional_fastener_head_to_flange_gap_mm": fastener,
            "conditional_cap_hole_swept_bit_margin_mm": cap_margin,
            "cap_top_bit_center_slop_bound_mm": cap_slop,
            "cap_spacer_setting": c["retainer_spacer_scope"],
            "recommended_metal_jig_hole_mm": install["recommended_metal_jig_hole_mm"],
            "guide_axis_location_term_includes_mount_fit_and_ID_OD_concentricity": True,
            "conservative_ID_OD_TIR_contribution_mm": install["ID_to_OD_concentricity_TIR_mm"],
            "remaining_0p15_axis_location_budget_after_TIR_mm": .15-install["ID_to_OD_concentricity_TIR_mm"],
            "mount_hole_material_fit_retention_and_stiffness_qualified": False,
            "capture_scope": "Dimensions are conditional on the declared cap/hole eccentricity, aperture tolerance and actual head-matched spacers. Catalog F/G dimensions alone do not establish cap retention, antirotation or wood-plate mounting."},
        "clamps": {"four_generic_pad_and_plan_lanes_retained": True, "guide_feet_supported_at_existing_two_pad_rectangles": True,
            "guide_bare_opening_nominal_mm": generic["support_and_clamp_requirements"]["bare_opening_mm"]["guide_clamps"]+feet_height,
            "other_clamp_opening_and_throats_source": inp["generic_fixture_result_path"],
            "rear_fence_and_guide_contact_plane_nominal_w_mm": plate_top,
            "actual_clamp_geometry_and_force_qualified": False},
        "chip_routes": {"physical_bushing_exit_to_wood_gap_interval_mm": gap_range,
            "general_half_maximum_cutter_D_reference_mm": general_low,
            "gap_minimum_minus_general_reference_mm": gap_range[0]-general_low,
            "general_reference_is_not_a_wood_specific_or_actual_pass": True,
            "front_outlet_v_interval_mm": front_band, "front_outlet_plan_circle_margin_mm": outlet_margin,
            "front_outlet_u_mm": d["member_width"],
            "front_route_scope": "Two feet stay behind the bore row; the raised guide and extended bottom stop leave the front face open over this v band. This is a nominal fixture-space route, not a chip-flow, pecking, point or cutting-method qualification."},
        "reach_and_guidance": {"nominal_cap_to_point_breakout_mm": nominal_path,
            "worst_cap_to_point_breakout_mm": max_path,
            "nominal_free_chuck_projection_mm": nominal_path+d["free_chuck_to_cap_axial_gap_min"],
            "worst_free_chuck_projection_mm": max_path+d["free_chuck_to_cap_axial_gap_min"],
            "worst_wood_exposed_flute_reference_mm": max_wood+d["breakout_travel"],
            "worst_physical_lower_bushing_exit_to_far_path_mm": gap_range[1]+max_wood+d["breakout_travel"],
            "effective_contiguous_guidance_requirement_mm": effective,
            "worst_last_effective_guidance_to_far_path_mm": max_last_guidance_to_far,
            "effective_guidance_proof": "An effective contiguous segment lies within the underhead body. Its last point is no higher than guide_top minus its length. Use the entire guide_top-to-far interval, including standoff, possible nonbearing ends, both timbers and breakout. This avoids equating nominal body length with guidance or checking only the entry point.",
            "effective_guidance_observed_or_catalog_guaranteed": False},
        "retained_error_conditions": e, "generic_error_allowance_comparisons": comparisons,
        "derived_relative_bound_under_declared_unobserved_conditions_mm": needed,
        "minimum_body_capsule_separation_after_derived_bound_mm": actual_gap_body,
        "hypothetical_whole_screw9p525_separation_after_derived_bound_mm": hypothetical_gap,
        "clearance_scope": "Positive residuals are arithmetic under the listed unobserved conditions; the generic 1.50-mm error requirement is exceeded and is not relabeled as passed. Whole 9.525-mm screw containment remains hypothetical. No budget relaxation, bit selection, screw change or installed tolerance is adopted.",
        "configured_ID_cases": id_cases, "configured_ID_scope": inp["configured_ID_scope"],
        "ID_comparison_scope": "Arithmetic on printed nominal diameters and catalog ID tolerances. FISCH diameter tolerance, rounding, guided diameter, runout and ordering suffix remain unknown; a tiny positive printed gap is not a product fit guarantee.",
        "FISCH_nominal_comparison": {"article": bit["article"], "EAN": bit["EAN"],
            "catalog_diameter_mm": bit["catalog_diameter_mm"], "catalog_NL_mm": bit["catalog_NL_mm"],
            "catalog_GL_mm": bit["catalog_GL_mm"], "catalog_shank_S_mm": bit["catalog_shank_S_mm"],
            "NL_minus_wood_exposure_reference_mm": bit["catalog_NL_mm"]-max_wood-d["breakout_travel"],
            "NL_minus_physical_lower_exit_reference_mm": bit["catalog_NL_mm"]-gap_range[1]-max_wood-d["breakout_travel"],
            "NL_minus_full_cap_chip_path_reference_mm": bit["catalog_NL_mm"]-max_path,
            "GL_minus_worst_projection_mm": bit["catalog_GL_mm"]-max_path-d["free_chuck_to_cap_axial_gap_min"],
            "length_scope": "NL is the maker's nominal working-length label. The negative full-cap comparison is retained as a diagnostic; with a separately justified lower outlet it alone does not prove incompatibility. GL minus projection is only an available length difference, not permitted chuck engagement. Actual tip, flute and usable chuck projection remain unknown.",
            "wood_material_documented": True, "guided_handheld_use_or_actual_fit_qualified": False},
        "preserved": {"current_Z200_and_four_HOLD_stations": True, "100_frame_bolts_and66_Hillman": True,
            "generic_six_files_and_source_facts_unchanged": True, "current_forces_transferred_to_Z180": False},
        "actual_observations": {"guide": "", "bit": "", "mount_plate": "", "effective_guidance": "",
                               "chip_route": "", "drill_chuck": "", "clamps": "", "Actual": "", "Disposition": ""},
        "limits": inp["limits"], "release": inp["release"],
        "execution": {"source_only_scalar_arithmetic": True, "shared_primary_PDF_bytes_authenticated_not_rerendered_or_copied": True,
            "new_CAD_BREP_native_mechanics_mesh_or_physical_run": False,
            "shared_model_document_index_staging_commit_action": False,
            "generic_scalar_helpers_reused_without_copy": True,
            "reproduce": f"uv run python -B {OWN.relative_to(ROOT)} --out {HERE.relative_to(ROOT)}/reproduction-01.json"}}
    require(not any(n in sys.modules for n in ("cadquery", "OCP", "numpy", "scipy")), "source-only execution")
    return result


def drawing(result):
    rows = result["temporary_parts"]
    selected = {r["id"]: r for r in rows}
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="880" viewBox="0 0 1400 880">',
           '<style>text{font:18px sans-serif;fill:#1e3542}.title{font-size:27px;font-weight:bold}.hold{fill:#9c382e;font-weight:bold}.small{font-size:15px}</style>',
           '<rect width="1400" height="880" fill="white"/>']

    def text(x, y, value, cls=""):
        out.append(f'<text x="{x}" y="{y}" class="{cls}">{html.escape(value)}</text>')

    text(35, 42, "Catalog H-40-12 adaptation of the Z180 fixture", "title")
    text(35, 75, "Source dimensions only. The generic 1.50-mm error budget is exceeded under its retained conditions.", "hold")
    text(35, 105, "Both handed plans and four proposed axes stay in the frozen generic drawing. Current Z200 remains HOLD.")
    text(35, 145, "SECTION: local gap / guide / head / cap", "title")
    layers = [("Cleat (post below)", 50.8, 88.9, "#e4c793"), ("Open outlet; feet at clamps", 88.9, 95.25, "#f4faf7"),
              ("Guide", *selected["guide"]["w_interval_mm"], "#95bfd7"),
              ("H head / matched spacers", 114.3, selected["retainer"]["w_interval_mm"][0], "#b6bdc2"),
              ("Cap", *selected["retainer"]["w_interval_mm"], "#e5a17c")]
    for i, (label, lo, hi, fill) in enumerate(layers):
        y = 500-hi*2.4
        out.append(f'<rect x="80" y="{y:.3f}" width="220" height="{(hi-lo)*2.4:.3f}" fill="{fill}" stroke="#455c69"/>')
        label_y = {0: 340, 1: 285, 2: 250, 3: 215, 4: 180}[i]
        out.append(f'<path d="M300,{y+(hi-lo)*1.2:.3f} L325,{label_y-5}" stroke="#455c69" fill="none"/>')
        text(335, label_y, f"{label}: w {lo:g}…{hi:g}", "small")
    # Nominal H cross-section; no delivered shape or entrance profile claimed.
    for width, lo, hi in ((15.875, 95.25, 114.3), (20.240625, 114.3, 119.85625)):
        out.append(f'<rect x="{190-width*1.2:.3f}" y="{500-hi*2.4:.3f}" width="{width*2.4:.3f}" height="{(hi-lo)*2.4:.3f}" fill="#879097" stroke="#455c69"/>')
    out.append('<rect x="177.6175" y="212.345" width="24.765" height="74.82" fill="white"/>')
    out.append('<rect x="174.76" y="197.105" width="30.48" height="15.24" fill="white"/>')
    out.append('<path d="M190,160 V365 m-6,-10 l6,10 6,-10" stroke="#ae473a" fill="none" stroke-width="2"/>')
    text(35, 415, "Two feet: 25.4×25.4×6.35, beneath the existing guide clamp pads.")
    text(35, 447, "Guide u 0…139.7, v 139.7…241.3; bore u 44.45/95.25, v 180.")
    text(35, 479, "Bottom stop now reaches w 114.3. Front gap is open at the bore row.")
    text(35, 530, "Catalog intervals / capture", "title")
    for y, line in zip(range(565, 726, 32), (
        "Body L 18.669…19.431; flange F 19.859625…20.621625; G 5.17525…5.93725.",
        "Physical exit gap 5.769…6.931; general half-D reference 5.55625.",
        "Cap holes Ø12.7±0.1; conditional minimum radial capture 3.3798125.",
        "Spacers match actual head top; proposed capture gap 0…0.05.",
        "Nominal guide-clamp bare opening 133.35; actual clamp/plate fit unknown.",
        "H is a permanent press fit. The maker's metal jig fit does not qualify wood."), strict=True):
        text(35, y, line, "small")
    text(750, 160, "Reach / unchanged error conditions", "title")
    budget = result["generic_error_allowance_comparisons"]
    reach = result["reach_and_guidance"]
    for y, line in zip(range(198, 423, 32), (
        f"Nominal free projection {reach['nominal_free_chuck_projection_mm']:.5f} mm.",
        f"Worst free projection {reach['worst_free_chuck_projection_mm']:.5f} mm.",
        f"Full cap-to-breakout path {reach['worst_cap_to_point_breakout_mm']:.5f} mm.",
        "Retain guide normal ≤0.08° and diametral play ≤0.10.",
        "Effective guidance ≥18.0 is an unobserved condition.",
        f"Tilt {budget['guide_tilt']['derived_bound_mm']:.6f} >0.16 allocation.",
        f"Slop {budget['insert_play']['derived_bound_mm']:.6f} >0.50 allocation.",
        f"Relative bound {budget['relative_bore_screw']['derived_bound_mm']:.6f} >1.50 target."), strict=True):
        text(750, y, line)
    text(750, 475, "FISCH 013P1032150 comparison", "title")
    bit = result["FISCH_nominal_comparison"]
    for y, line in zip(range(510, 703, 32), (
        "Maker: Ø10.32, NL 120, GL 150, shank 10; wood use documented.",
        f"NL minus wood exposure: {bit['NL_minus_wood_exposure_reference_mm']:.5f} mm.",
        f"NL minus lower exit path: {bit['NL_minus_physical_lower_exit_reference_mm']:.5f} mm.",
        f"NL minus full cap path: {bit['NL_minus_full_cap_chip_path_reference_mm']:.5f} mm.",
        "Full-path deficit alone does not reject a separately justified lower outlet.",
        "No actual bit tolerance, guided use, chuck engagement or chip-flow pass.",
        "Exact bushing ID suffix and actual guide bearing remain unresolved."), strict=True):
        text(750, y, line, "small")
    text(35, 780, "Declared geometry and error conditions only. Do not use paper scaling as a machining template.", "hold")
    text(35, 815, "No frame change, tool selection, physical observation, drilling, strength or fabrication release is adopted.", "hold")
    text(35, 850, "Use the sibling JSON for exact intervals, source pins, comparison failures, chip-route limits and blank actuals.", "small")
    out.append("</svg>")
    return ("\n".join(out)+"\n").encode()


def output_paths(requested):
    require(requested.parent.resolve() == HERE and requested.suffix == ".json", "owned canonical JSON output required")
    destination = HERE / requested.name
    picture = destination.with_suffix(".svg")
    require(not os.path.lexists(destination) and not os.path.lexists(picture), "fresh canonical JSON and SVG entries required")
    return destination, picture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    destination, picture = output_paths(args.out)
    result = calculate()
    svg = drawing(result)
    result["drawing"] = {"path": str(picture.relative_to(ROOT)), "sha256": hashlib.sha256(svg).hexdigest(), "bytes": len(svg)}
    raw = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n").encode()
    verify(result["source_sha256"])
    with picture.open("xb") as stream:
        stream.write(svg)
    with destination.open("xb") as stream:
        stream.write(raw)
    verify(result["source_sha256"])
    print(json.dumps({"out": str(destination.relative_to(ROOT)), "sha256": sha(destination), "bytes": len(raw),
                      "drawing": result["drawing"], "source_pin_count": len(result["source_sha256"]),
                      "generic_relative_budget_met": False}))


if __name__ == "__main__":
    main()
