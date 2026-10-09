"""Independent frozen catalog-adapter review using physical-coordinate corners."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import math
import runpy
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
PACKET = OWN.parents[2]
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "inputs.json": "dd0df7d6b5eb30aab11184c4d4471333e545b270232333ba9577678c9155282d",
    "adapter.py": "f3831931d6c89330e07d76d1099cc4ecdf9a9a0c6e7be1b069413a7a1bc22a04",
    "result-v2.json": "e5e34e992365aedf30b56710efd9dcbb4d1a64e77e4ede29ff656d0479ff17de",
    "result-v2.svg": "4b52eaba8f98d5457b606061f5d51eace14bc222d38dc6bc0f873d91ff2e1b6b",
    "verify.py": "dd755dc20baf508cb03896062f317d5e4a6171e732b1a7329461da4b8a3931d3",
    "verification-v1.json": "7cc2edc01fbdf98536e0a2029ea7e090503e135df7d698395127bbc30bea55b1",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def close(a, b, message):
    require(math.isclose(a, b, rel_tol=0, abs_tol=2e-10), message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "changed frozen bytes: "+path)


def audit(inp, facts, old_inp, old, saved):
    catalog = facts["sources"]["Carr_Lane_H"]["facts"]
    install = facts["sources"]["Carr_Lane_installation"]["facts"]
    d, c, e = old_inp["dimensions_mm"], inp["changes"], inp["retained_error_conditions"]
    t = install["unlisted_standard_ANSI_dimension_plus_minus_mm"]
    require(t == .381 and catalog["H_40_12_row_has_counterbore_asterisk"] is False,
            "current source tolerance and body convention")
    ranges = [[catalog[key]-t, catalog[key]+t]
              for key in ("underhead_length_nominal_mm", "head_OD_F_nominal_mm", "head_height_G_nominal_mm")]
    for key, values in zip(("underhead_body_length", "head_F_diameter", "head_G_height"), ranges, strict=True):
        require(saved["catalog_dimensional_intervals_mm"][key] == values, "catalog interval: "+key)
    require(saved["catalog_dimensional_intervals_mm"]["body_OD"]
            == [catalog["body_OD_nominal_mm"]+x for x in catalog["body_OD_additional_tolerance_mm"]],
            "body OD tolerance is separate")
    angle, play = e["guide_normal_angle_max_deg"], e["bushing_diametral_play_max_mm"]
    require(angle == old_inp["error_budget"]["guide_normal_angle_max_deg"] == .08
            and play == old_inp["error_budget"]["bushing_diametral_play_max_mm"] == .1,
            "original angle/play conditions retained")
    retained_other = {k: v for k, v in old_inp["error_budget"]["terms_mm"].items()
                      if k not in {"guide_angle_full_path_allowance", "bushing_play_and_angular_slop_full_path"}}
    require(e["other_relative_error_terms_mm"] == retained_other, "other full-path terms retained")
    require(e["relative_bore_screw_target_mm"] == 1.5 and e["maximum_effective_cutting_diameter_mm"] == 11.1125,
            "no target or cutter envelope relaxation")
    height_error = c["noncatalog_fixture_height_aggregate_deviation_max_mm"]
    effective = c["effective_contiguous_guidance_min_mm"]
    aperture = [c["cap_hole_nominal_D_mm"]-c["cap_hole_D_deviation_max_mm"],
                c["cap_hole_nominal_D_mm"]+c["cap_hole_D_deviation_max_mm"]]
    require(effective == 18 and effective < min(ranges[0]), "conditional contiguous guidance fits body")
    # Enumerate physical w coordinates, including placement of the effective
    # span at either extreme of the underhead body. This independently avoids
    # substituting body length for effective guidance.
    paths, lower_gaps, lower_paths, captures, far_slops, cap_slops, cap_margins, effective_paths = [], [], [], [], [], [], [], []
    corner_count, line_count = 0, 0
    conditions = (*ranges, [-height_error, height_error],
                  [2*d["member_thickness"]-d["matched_stack_deviation_max"],
                   2*d["member_thickness"]+d["matched_stack_deviation_max"]],
                  c["cap_to_head_top_gap_design_mm"], aperture,
                  [0., c["cap_hole_to_flange_axis_eccentricity_max_mm"]])
    for length, flange, head, jig_shift, wood, capture_gap, opening, eccentricity in itertools.product(*conditions):
        plate_top = c["guide_top_w_nominal_mm"]+jig_shift
        body_bottom = plate_top-length
        wood_top = d["guide_w"][0]
        far = wood_top-wood-d["breakout_travel"]
        cap_top = plate_top+head+capture_gap+c["cap_thickness_mm"]
        paths.append(cap_top-far)
        lower_gaps.append(body_bottom-wood_top)
        lower_paths.append(body_bottom-far)
        captures.append((flange-opening)/2-eccentricity)
        for span_top in (plate_top, body_bottom+effective):
            span_bottom = span_top-effective
            require(span_bottom >= body_bottom-1e-12 and span_top <= plate_top+1e-12, "span inside body")
            effective_paths.append(span_bottom-far)
            for top_error, bottom_error in itertools.product((-play/2, play/2), repeat=2):
                # Line through two actual constraining endpoints, extrapolated
                # downstream to the far point and upstream to the cap aperture.
                far_error = bottom_error+(bottom_error-top_error)*(span_bottom-far)/effective
                cap_error = top_error+(top_error-bottom_error)*(cap_top-span_top)/effective
                far_slops.append(abs(far_error))
                cap_slops.append(abs(cap_error))
                cap_margins.append((opening-e["maximum_effective_cutting_diameter_mm"])/2
                                   -abs(cap_error)-eccentricity)
                line_count += 1
        corner_count += 1
    require(corner_count == 256 and line_count == 2048, "independent physical corner census")
    reach, route, cap = saved["reach_and_guidance"], saved["chip_routes"], saved["cap_and_mounting"]
    close(reach["worst_cap_to_point_breakout_mm"], max(paths), "maximum physical full route")
    close(reach["worst_free_chuck_projection_mm"], max(paths)+d["free_chuck_to_cap_axial_gap_min"], "free projection")
    for actual, expected in zip(route["physical_bushing_exit_to_wood_gap_interval_mm"],
                                [min(lower_gaps), max(lower_gaps)], strict=True):
        close(actual, expected, "physical body outlet interval")
    close(reach["worst_physical_lower_bushing_exit_to_far_path_mm"], max(lower_paths), "physical lower route")
    close(reach["worst_last_effective_guidance_to_far_path_mm"], max(effective_paths), "effective span downstream lever")
    close(cap["conditional_minimum_radial_capture_lip_mm"], min(captures), "head/cap tolerance capture")
    # The producer additionally retains the aggregate height allowance at the
    # cap, although common plate translation cancels in this local calculation.
    # Its slightly larger cap slop is conservative, not an actual fit claim.
    close(cap["cap_top_bit_center_slop_bound_mm"], max(cap_slops)+height_error*play/effective,
          "conservative cap centerline bound")
    expected_cap_margin = (min(aperture)-e["maximum_effective_cutting_diameter_mm"])/2
    expected_cap_margin -= cap["cap_top_bit_center_slop_bound_mm"]+c["cap_hole_to_flange_axis_eccentricity_max_mm"]
    close(cap["conditional_cap_hole_swept_bit_margin_mm"], expected_cap_margin, "conditional cap margin")
    require(0 < cap["conditional_cap_hole_swept_bit_margin_mm"] <= min(cap_margins)+1e-12,
            "cap clearance arithmetic remains conservative")
    nominal_cap_bottom = c["guide_top_w_nominal_mm"]+catalog["head_height_G_nominal_mm"]
    close(cap["nominal_cap_bottom_w_mm"], nominal_cap_bottom, "nominal head-matched spacer height")
    close(cap["nominal_cap_top_w_mm"], nominal_cap_bottom+c["cap_thickness_mm"], "nominal cap top")
    close(cap["remaining_0p15_axis_location_budget_after_TIR_mm"], .15-install["ID_to_OD_concentricity_TIR_mm"],
          "full TIR debit is conservative")
    minimum_center_gap = min(math.dist(f, [u, d["bore_v"]])
                             for f in d["retainer_fastener_centers_uv"] for u in d["bore_u"])
    close(cap["conditional_fastener_head_to_flange_gap_mm"],
          minimum_center_gap-max(ranges[1])/2-d["retainer_fastener_head_OD_max"]/2, "nominal fastener plan clearance")
    tilt, slop = max(paths)*math.tan(math.radians(angle)), max(far_slops)
    needed = sum(retained_other.values())+tilt+slop
    for key, value, target in (("guide_tilt", tilt, .16), ("insert_play", slop, .5),
                                ("relative_bore_screw", needed, 1.5)):
        row = saved["generic_error_allowance_comparisons"][key]
        close(row["derived_bound_mm"], value, "derived comparison: "+key)
        close(row["excess_mm"], value-target, "retained exceedance: "+key)
        require(value > target and row.get("within_generic_allocation", row.get("within_generic_target")) is False,
                "unmet comparison must stay unmet")
    close(saved["derived_relative_bound_under_declared_unobserved_conditions_mm"], needed, "derived total")
    gaps = old["nominal_primitive_clearance"]["cases"]
    close(saved["minimum_body_capsule_separation_after_derived_bound_mm"],
          gaps["current_body"]["minimum"]["capsule_separation_lower_bound_mm"]-needed, "body residual is conditional")
    close(saved["hypothetical_whole_screw9p525_separation_after_derived_bound_mm"],
          gaps["whole_screw_9p525_containing_capsule_reference"]["minimum"]["capsule_separation_lower_bound_mm"]-needed,
          "whole-screw residual is hypothetical")
    nominal_parts = {p["id"]: p for p in old["parts"]}
    new_parts = {p["id"]: p for p in saved["temporary_parts"]}
    require(len(new_parts) == len(saved["temporary_parts"]) == 10, "eight temporary parts plus two feet")
    require({k for k in nominal_parts if nominal_parts[k] != new_parts[k]}
            == {"guide", "retainer", "cleat_guide_bottom_stop"}, "only three original fixture parts change")
    for name, part in new_parts.items():
        for axis, size in zip("uvw", part["size_uvw_mm"], strict=True):
            close(size, part[axis+"_interval_mm"][1]-part[axis+"_interval_mm"][0], "part dimensions close")
        if name in nominal_parts:
            require(part["u_interval_mm"] == nominal_parts[name]["u_interval_mm"]
                    and part["v_interval_mm"] == nominal_parts[name]["v_interval_mm"], "all handed plan coordinates remain")
    for label in ("guide_rear", "guide_front"):
        foot = new_parts["guide_foot_"+label]
        pad = old["support_and_clamp_requirements"]["pad_rectangles_uv_mm"][label]
        require([foot["u_interval_mm"], foot["v_interval_mm"]] == pad, "feet over reviewed support contacts")
        require(foot["w_interval_mm"] == [88.9, 95.25] and foot["v_interval_mm"][0] == 209.55,
                "feet retain nominal open bore band")
    require(new_parts["guide"]["w_interval_mm"] == [95.25, 114.3]
            and new_parts["cleat_guide_bottom_stop"]["w_interval_mm"] == [50.8, 114.3], "raised plate and stop")
    close(saved["clamps"]["guide_bare_opening_nominal_mm"], 114.3-(-19.05), "clamp stack opening")
    require(route["front_outlet_v_interval_mm"] == [139.7, 209.55], "front route band")
    close(route["front_outlet_plan_circle_margin_mm"], 209.55-180-11.1125/2, "nominal open-band margin")
    close(route["gap_minimum_minus_general_reference_mm"], min(lower_gaps)-11.1125/2, "general gap diagnostic")
    bit = facts["sources"]["FISCH_pen_drill"]["facts"]
    reported_bit = saved["FISCH_nominal_comparison"]
    wood_reference = 76.7+6.35
    for key, value in {"NL_minus_wood_exposure_reference_mm": bit["catalog_NL_mm"]-wood_reference,
                       "NL_minus_physical_lower_exit_reference_mm": bit["catalog_NL_mm"]-max(lower_paths),
                       "NL_minus_full_cap_chip_path_reference_mm": bit["catalog_NL_mm"]-max(paths),
                       "GL_minus_worst_projection_mm": bit["catalog_GL_mm"]-max(paths)-2}.items():
        close(reported_bit[key], value, "distinct nominal bit comparison: "+key)
    require(len(saved["configured_ID_cases"]) == 3, "three distinct ID references")
    for row, reference in zip(saved["configured_ID_cases"], inp["configured_ID_reference_in"], strict=True):
        close(row["reference_ID_in"], reference, "ID order reference")
        for i, offset in enumerate(catalog["ID_additional_standard_tolerance_mm"]):
            close(row["catalog_ID_interval_mm"][i], reference*25.4+offset, "ID tolerance conversion")
            close(row["printed_nominal_diametral_gap_range_mm"][i], reference*25.4+offset-bit["catalog_diameter_mm"],
                  "printed gap is not actual fit")
        close(row["minimum_effective_bit_guiding_D_for_declared_play_mm"], reference*25.4+.0127-play,
              "minimum conditional guiding diameter")
        require(row["actual_bit_fit_established"] is False, "no actual ID/bit fit")
    require(all(v is False for v in saved["release"].values())
            and all(v == "" for v in saved["actual_observations"].values()), "no release or actual observation")
    require(saved["preserved"]["current_forces_transferred_to_Z180"] is False
            and cap["mount_hole_material_fit_retention_and_stiffness_qualified"] is False,
            "force transfer and fixture acceptance remain false")
    return {"physical_catalog_corners": corner_count, "effective_span_and_line_endpoint_cases": line_count,
            "physical_gap_interval_mm": [min(lower_gaps), max(lower_gaps)],
            "full_cap_path_interval_mm": [min(paths), max(paths)], "lower_exit_path_maximum_mm": max(lower_paths),
            "maximum_effective_span_slop_mm": slop, "maximum_cap_slop_from_physical_corners_mm": max(cap_slops),
            "derived_relative_bound_mm": needed, "generic_target_mm": 1.5,
            "temporary_original_parts_changed": 3, "temporary_feet_added": 2}


def main():
    destination = OWN.with_name("receipt.json")
    require(not destination.exists(), "preserve prior receipt")
    inp, saved = read(PACKET / "inputs.json"), read(PACKET / "result-v2.json")
    pins = dict(saved["source_sha256"])
    pins.update({str((PACKET / n).relative_to(ROOT)): digest for n, digest in EXPECTED.items()})
    verify(pins)
    method = runpy.run_path(str(PACKET / "adapter.py"))
    replay = method["calculate"]()
    require(replay == {k: v for k, v in saved.items() if k != "drawing"}, "exact scalar replay")
    require(method["drawing"](saved) == (PACKET / "result-v2.svg").read_bytes(), "exact SVG byte replay")
    _, facts, old_inp, old, _, _, _ = method["load"]()
    outcome = audit(inp, facts, old_inp, old, saved)
    controls = []

    def reject(label, fn):
        try:
            fn()
        except ValueError:
            controls.append(label)
        else:
            raise ValueError("accepted control: "+label)

    mutations = [
        ("wrong_full_path", lambda x: x["reach_and_guidance"].__setitem__("worst_cap_to_point_breakout_mm", 119.85625)),
        ("wrong_lower_gap", lambda x: x["chip_routes"]["physical_bushing_exit_to_wood_gap_interval_mm"].__setitem__(0, 6.35)),
        ("nominal_body_as_effective_guidance", lambda x: x["reach_and_guidance"].__setitem__("worst_last_effective_guidance_to_far_path_mm", 89.981)),
        ("generic_budget_marked_passed", lambda x: x["generic_error_allowance_comparisons"]["relative_bore_screw"].__setitem__("within_generic_target", True)),
        ("cap_margin_overstatement", lambda x: x["cap_and_mounting"].__setitem__("conditional_cap_hole_swept_bit_margin_mm", .48)),
        ("flange_tolerance_ignored", lambda x: x["cap_and_mounting"].__setitem__("conditional_minimum_radial_capture_lip_mm", 3.57)),
        ("lower_route_as_full_route", lambda x: x["FISCH_nominal_comparison"].__setitem__("NL_minus_full_cap_chip_path_reference_mm", 30.019)),
        ("tiny_printed_gap_as_fit", lambda x: x["configured_ID_cases"][0].__setitem__("actual_bit_fit_established", True)),
        ("feet_block_bore_band", lambda x: x["temporary_parts"][-1].__setitem__("v_interval_mm", [170, 195.4])),
        ("current_force_transfer", lambda x: x["preserved"].__setitem__("current_forces_transferred_to_Z180", True)),
        ("mount_qualified", lambda x: x["cap_and_mounting"].__setitem__("mount_hole_material_fit_retention_and_stiffness_qualified", True)),
        ("physical_release", lambda x: x["release"].__setitem__("physical_operation", True)),
    ]
    for label, mutate in mutations:
        changed = copy.deepcopy(saved)
        mutate(changed)
        reject(label, lambda v=changed: audit(inp, facts, old_inp, old, v))
    reject("existing_result_output", lambda: method["output_paths"](PACKET / "result-v2.json"))
    reject("non_json_output", lambda: method["output_paths"](PACKET / "unused.txt"))
    reject("nested_output", lambda: method["output_paths"](OWN.parent / "unused.json"))
    bad_pins = dict(pins)
    bad_pins[next(iter(bad_pins))] = "0"*64
    reject("source_digest_change", lambda: verify(bad_pins))
    require(not ({"cadquery", "OCP", "numpy", "scipy"} & set(sys.modules)), "no native/numerical imports")
    verify(pins)
    receipt = {"schema": "catalog_adapter_v1_independent_correctness_review/v1", "findings": [],
               "target_sha256": EXPECTED, "target_and_direct_source_files_rehashed": len(pins),
               "target_and_direct_source_sha256": dict(sorted(pins.items())), "before_after_bytes_unchanged": True,
               "exact_scalar_and_svg_replay": True, "physical_coordinate_corner_audit": outcome,
               "rejected_controls": controls, "review_helper_sha256": sha(OWN), "release": saved["release"],
               "limits": [
                   "Stdlib source/JSON, byte hashing and in-memory arithmetic only. No native/CAD/BREP/FEA/global/physical/browser/site work or shared edits.",
                   "The generic fixture's authenticated source replay and prior bounded source/finished-solid proofs are reused. No native observations, inherited closure or manufacturer source-page facts are independently regenerated; the shared FISCH PDF is byte-authenticated only.",
                   "Catalog dimensions and contiguous 18-mm guidance are conditional inputs. Mounting material/fit/concentricity, guide alignment, cap retention, actual bit diameter/point/flutes/chuck projection, chip clearing and achieved tolerances remain unobserved.",
                   "Three generic error comparisons remain unmet; negative full-cap NL comparison is diagnostic and is distinct from a separately justified lower outlet. No product/fixture/strength acceptance or budget relaxation.",
                   "Current Z200/100 bolts/66 screws/forces/HOLD stay unchanged. Z180 remains unadopted, panel remedies stopped, and no physical release follows.",
                   "Three read-only output rejection controls rerun; eight saved output-guard results and exclusive-create source are reviewed without writing guard fixtures outside the owned review folder."],
               }
    with destination.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"receipt_sha256": sha(destination), "helper_sha256": sha(OWN),
                      "source_and_target_files": len(pins), "rejected_controls": len(controls), "findings": []}))


if __name__ == "__main__":
    main()
