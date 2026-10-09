"""Source-only matched-pair fixture for four unadopted Z180 axes.

No CAD, BREP, mechanics or physical operation. Reuse authenticated scalar
profile, datum and finite-capsule helpers; write only fresh owned outputs.
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
from types import SimpleNamespace

OWN = Path(__file__).resolve()
HERE = OWN.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
INPUT = HERE / "inputs.json"
INPUT_SHA = "b17a8f72f41ab2b8ce75ffaac15af075432a0ffe7111daead6597cb34eff86be"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes(), parse_constant=lambda _: require(False, "nonfinite JSON"))


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "changed source: " + path)


def corners(rect):
    return [[u, v] for u in rect[0] for v in rect[1]]


def point_rectangle(point, rect):
    """Exact planar point-to-closed-axis-aligned-rectangle distance."""
    return math.hypot(*(max(lo - p, p - hi, 0.)
                        for p, (lo, hi) in zip(point, rect, strict=True)))


def parts(d):
    names = ("baseboard", "backer", "cleat_support", "rear_fence", "post_bottom_stop",
             "cleat_guide_bottom_stop", "guide", "retainer")
    return [{"id": name, "u_interval_mm": d[name + "_u"],
             "v_interval_mm": d[name + "_v"], "w_interval_mm": d[name + "_w"],
             "size_uvw_mm": [d[name + "_" + axis][1] - d[name + "_" + axis][0]
                             for axis in "uvw"]} for name in names]


def prepare():
    require(sha(INPUT) == INPUT_SHA, "exact fixture inputs required")
    inp = read(INPUT)
    pins = {r["path"]: r["sha256"] for r in inp["sources"].values()}
    pins.update({str(INPUT.relative_to(ROOT)): INPUT_SHA, str(OWN.relative_to(ROOT)): sha(OWN)})
    verify(pins)
    data = {k: read(ROOT / r["path"]) for k, r in inp["sources"].items()
            if r["path"].endswith(".json")}
    # This authenticated module has only standard-library imports and no top-level run.
    pure = runpy.run_path(str(ROOT / inp["sources"]["hardware_method"]["path"]))["pure_functions"]
    profile = pure(inp["sources"]["receiver_method"], {"require", "profile", "polygon_margin"})
    datum = SimpleNamespace(**pure(inp["sources"]["datum_method"], {"add", "world"}))
    capsule = SimpleNamespace(**pure(inp["sources"]["capsule_method"],
                                    {"require", "unit", "primitive", "axis_distance", "pair",
                                     "hardware", "known_answers"}))
    return inp, data, pins, profile, datum, capsule


def source_inventory(inp, data, profile, datum):
    g, placement = data["geometry"], data["placement"]
    require(g["revision"] == inp["current_revision"] == placement["base_revision"], "revision join")
    require(len(g["axes"]) == 100 and len(g["screw_axes"]) == 66, "current100/66 census")
    require(canonical(g["axes"]) == placement["current_100_axes_canonical_sha256"]
            and canonical(g["screw_axes"]) == placement["current_66_screws_canonical_sha256"],
            "unchanged current axes and screws")
    current = {a["id"]: a for a in g["axes"]}
    proposed = placement["proposed_axes"]
    ids = {f"cleat_post_bolt_{side}_{n}" for side in ("left", "right") for n in (1, 2)}
    require({a["id"] for a in proposed} == ids and placement["geometry_adopted"] is False,
            "four unadopted axes required")
    for a in proposed:
        expected = copy.deepcopy(current[a["id"]])
        require(expected["point_xyz_mm"][2] == inp["current_Z_mm"] == 200., "current Z200")
        expected["point_xyz_mm"][2] = inp["proposed_Z_mm"]
        require(expected == a and inp["proposed_Z_mm"] == 180., "only proposed Z180 translation")
    names = {n for a in proposed for n in a["receivers"]}
    shapes = {n: profile["profile"](data["profiles"][n], datum) for n in sorted(names)}
    own_cuts = {n: [a for a in g["axes"] if n in a["receivers"]] for n in names}
    require(all(len(rows) == 4 for rows in own_cuts.values()), "four own recorded cuts per host")
    native = data["native_result"]
    require(native["status"] == "UNADOPTED_LOCAL_FINISHED_GEOMETRY_OBSERVED"
            and set(native["receivers"]) == names and len(native["scenarios"]) == 3,
            "saved native result identity")
    native_rows = []
    for s in native["scenarios"]:
        walls, seats = s["wall_queries"], s["annular_queries"]
        require(len(walls) == len(seats) == 16
                and all(abs(w["full_wall_length_mm"] - 38.1) < 2e-7
                        and w["partial_wall_present"] is False for w in walls)
                and all(abs(w["observed_backing_fraction"] - 1.) < 2e-8 for w in seats),
                "saved full walls/annuli required")
        native_rows.append({"scenario": s["scenario"], "full_wall_occurrences": 16,
                            "nominal_annular_seats": 16})
    return proposed, shapes, own_cuts, native_rows


def transforms(inp, proposed, shapes):
    d, rear = inp["dimensions_mm"], inp["fixture_coordinates"]["rear_Y_mm"]
    rows = []
    for a in proposed:
        side = "left" if "_left_" in a["id"] else "right"
        outward = -1. if side == "left" else 1.
        post = shapes["base_post_outer_" + side]
        cleat = shapes["eoere_cleat_" + side]
        x_inner = max(post["X_interval_mm"]) if side == "left" else min(post["X_interval_mm"])
        x_zero = x_inner - outward * d["backer_w"][1]
        uvw = [a["point_xyz_mm"][1] - rear, a["point_xyz_mm"][2],
               outward * (a["point_xyz_mm"][0] - x_zero)]
        require(abs(uvw[2] - d["guide_w"][0]) < 2e-8
                and any(abs(uvw[0] - u) < 2e-8 for u in d["bore_u"])
                and uvw[1] == d["bore_v"], "world-to-fixture axis join")
        require(abs(a["grip_mm"] - 2*d["member_thickness"]) < 2e-8
                and a["direction_xyz"] == [-outward, 0., 0.]
                and abs(cleat["thickness_mm"] - d["member_thickness"]) < 2e-8
                and abs(post["thickness_mm"] - d["member_thickness"]) < 2e-8,
                "two member thickness and inward drilling join")
        rows.append({"axis_id": a["id"], "hand": side, "world_entry_xyz_mm": a["point_xyz_mm"],
                     "world_drill_direction": a["direction_xyz"], "fixture_entry_uvw_mm": uvw,
                     "world_X_at_fixture_w0_mm": x_zero, "world_X_per_fixture_w": outward,
                     "fixture_exit_w_mm": uvw[2] - a["grip_mm"],
                     "cleat_bottom_to_axis_mm": uvw[1] - d["cleat_bottom_v"],
                     "post_top_to_axis_mm": d["post_height"] - uvw[1]})
    return rows


def footprints(inp, shapes, own_cuts, profile):
    d, rear = inp["dimensions_mm"], inp["fixture_coordinates"]["rear_Y_mm"]
    half = d["clamp_pad_width"] / 2
    centers = {"guide_rear": d["guide_clamp_centers_uv"][0],
               "guide_front": d["guide_clamp_centers_uv"][1],
               "post_bottom": d["post_clamp_center_uv"], "cleat_upper": d["cleat_clamp_center_uv"]}
    pads = {k: [[c[0] - half, c[0] + half], [c[1] - half, c[1] + half]]
            for k, c in centers.items()}
    lanes = {"guide_rear": [[d["baseboard_u"][0], pads["guide_rear"][0][1]], pads["guide_rear"][1]],
             "guide_front": [[pads["guide_front"][0][0], d["baseboard_u"][1]], pads["guide_front"][1]],
             "post_bottom": [pads["post_bottom"][0], [d["baseboard_v"][0], pads["post_bottom"][1][1]]],
             "cleat_upper": [[pads["cleat_upper"][0][0], d["baseboard_u"][1]], pads["cleat_upper"][1]]}
    # The contact rectangles must lie in each actual source profile, away from every own bore.
    checks = []
    for name, shape in shapes.items():
        is_cleat = name.startswith("eoere_cleat")
        candidates = {k: pads[k] for k in (("guide_rear", "guide_front", "cleat_upper")
                                          if is_cleat else ("guide_rear", "guide_front", "post_bottom"))}
        if is_cleat:
            candidates["upper_riser"] = [d["cleat_support_u"], d["cleat_support_v"]]
        for label, rect in candidates.items():
            edge = min(profile["polygon_margin"]([u + rear, v], shape["YZ_polygon_mm"])
                       for u, v in corners(rect))
            bore = min(point_rectangle([a["point_xyz_mm"][1] - rear,
                                        180. if a["id"].startswith("cleat_post_bolt_")
                                        else a["point_xyz_mm"][2]], rect) - a["bore_diameter_mm"]/2
                       for a in own_cuts[name])
            require(edge >= -2e-8 and bore > 0., "contact rectangle crosses profile or recorded bore")
            checks.append({"receiver": name, "contact": label, "uv_rectangle_mm": rect,
                           "minimum_profile_margin_mm": max(0., edge),
                           "minimum_recorded_bore_margin_mm": bore})
    clearances = []
    for u in d["bore_u"]:
        center = [u, d["bore_v"]]
        for label, rect in lanes.items():
            margin = point_rectangle(center, rect) - d["chuck_nose_keepout_radius"]
            require(margin > 0., "clamp lane crosses local chuck-nose keepout")
            clearances.append({"bore_uv_mm": center, "clamp": label,
                               "keepout_to_lane_margin_mm": margin})
    require(d["cleat_support_v"][0] > d["post_height"], "riser must be separate from post")
    require(abs(d["cleat_support_w"][1] - d["backer_w"][1] - d["member_thickness"]) < 2e-8,
            "nominal riser must match post plus backer")
    base = d["baseboard_w"][1] - d["baseboard_w"][0]
    backer = d["backer_w"][1] - d["backer_w"][0]
    opening = {"guide_clamps": base + backer + 2*d["member_thickness"] + d["guide_w"][1] - d["guide_w"][0],
               "cleat_clamp": base + d["cleat_support_w"][1] + d["member_thickness"],
               "post_clamp": base + backer + d["member_thickness"]}
    throat = {"guide_clamps": centers["guide_rear"][0] - d["baseboard_u"][0],
              "cleat_clamp": d["baseboard_u"][1] - centers["cleat_upper"][0],
              "post_clamp": centers["post_bottom"][1] - d["baseboard_v"][0]}
    return {"pad_rectangles_uv_mm": pads, "clamp_arm_plan_lanes_uv_mm": lanes,
            "source_profile_and_recorded_cut_checks": checks, "chuck_lane_checks": clearances,
            "minimum_chuck_nose_to_clamp_lane_margin_mm": min(r["keepout_to_lane_margin_mm"] for r in clearances),
            "bare_opening_mm": opening, "minimum_nominal_throat_mm": throat,
            "opening_scope": "Nominal bare stack. Add actual pads, thickness deviations and required operating travel; no actual clamp fit or holding-force pass.",
            "rear_guide_clamp_minimum_jaw_drop_over_fence_mm": d["rear_fence_w"][1] - d["guide_w"][1],
            "fixture_attachment_scope": "Fence, stops, backer and riser must be secured to the temporary base without a fastener projecting into the frame, drill or clamp paths. Their attachment hardware/stiffness and the rear clamp arm clearing the 114.3-mm fence above its 107.95-mm contact plane are unqualified actual-fixture inputs.",
            "four_simultaneous_clamps_required": True,
            "full_drill_clamp_handle_hand_or_workholding_qualification": False}


def clearance(inp, data, proposed, capsule):
    scope = inp["primitive_scope"]
    bores = []
    for a in proposed:
        bores.append(capsule.primitive(a["id"], "wood_bore_cutter", a["point_xyz_mm"],
                                      a["direction_xyz"], -1., a["grip_mm"] + 1.,
                                      inp["error_budget"]["maximum_effective_cutting_diameter_mm"]/2))
    cases = {"current_body": scope["current_body"], "current_modeled_head": scope["current_modeled_head"]}
    cases.update({r["name"]: r for r in scope["extra_sensitivities"]})
    results = {}
    for label, spec in cases.items():
        screw_primitives = [capsule.primitive(s["axis_id"], label, s["origin_xyz_mm"], s["direction_xyz"],
                                             spec["near_mm"], spec["far_mm"], spec["radius_mm"])
                            for s in data["geometry"]["screw_axes"]]
        pairs = [capsule.pair(b, s) for b in bores for s in screw_primitives]
        minimum = min(pairs, key=lambda r: r["capsule_separation_lower_bound_mm"])
        results[label] = {"comparisons": len(pairs), "minimum": minimum,
                          "all_bounds_positive": all(r["capsule_separation_lower_bound_mm"] > 0 for r in pairs)}
    recorded = next(s for s in data["placement_result"]["screens"] if s["id"] == "proposed_Z180")
    expected = recorded["maximum_bore_vs_66_current_screws"]["minimum"]
    minimum = results["current_body"]["minimum"]
    require(minimum["first"] == expected["first"] and minimum["second"] == expected["second"]
            and abs(minimum["capsule_separation_lower_bound_mm"] - expected["capsule_separation_lower_bound_mm"]) < 1e-12,
            "recorded max-bore/screw gap reproduction")
    require(all(r["all_bounds_positive"] for r in results.values()), "source sensitivity separation")
    return {"wood_bore_capsules": bores, "cases": results,
            "modeled_body_and_head_comparisons": 528,
            "modeled_heads_already_in_existing_screen": True,
            "new_head_or_countersink_solid_or_cut": False,
            "scope": "Source capsule separation of the four wood paths from current66 nominal screw records. The extra 9.525-mm envelopes are conditional references only; actual Hillman heads/countersinks are unknown. Breakout in sacrificial fixture wood is outside this frame-clearance claim."}


def budget(inp, gaps):
    d, e = inp["dimensions_mm"], inp["error_budget"]
    wood = 2*d["member_thickness"]
    guide = d["retainer_w"][1] - d["guide_w"][0]
    max_wood = wood + d["matched_stack_deviation_max"]
    max_guide = guide + d["guide_cap_stack_deviation_max"]
    full = guide + wood + d["breakout_travel"]
    max_full = max_guide + max_wood + d["breakout_travel"]
    angle = max_full * math.tan(math.radians(e["guide_normal_angle_max_deg"]))
    radial = e["bushing_diametral_play_max_mm"]/2
    exposed = max_wood + d["breakout_travel"]
    play = radial + exposed * (2*radial/d["bushing_effective_length_min"])
    terms = e["terms_mm"]
    total = sum(terms.values())
    bound = e["total_relative_bore_screw_bound_mm"]
    require(angle <= terms["guide_angle_full_path_allowance"]
            and play <= terms["bushing_play_and_angular_slop_full_path"] and total <= bound,
            "full-path allocation exceeded")
    bore_bound = bound - terms["future_screw_axis_placement"]
    datum = d["square_end_datum_deviation_max"]
    return {"declared_terms_mm": terms, "allocated_sum_mm": total,
            "relative_bore_screw_bound_mm": bound, "unallocated_reserve_mm": bound-total,
            "pointwise_bound_proof": "For every centerline station inside both timbers, triangle inequality adds independent vector-magnitude bounds. Guide tilt uses the entire cap-to-breakout lever. Insert slop uses the two ends of its effective guiding length; cutting curvature and screw-axis placement have separate full-segment bounds. No cancellation or entry-point-only test is used.",
            "guide_tilt_formula": "Lmax*tan(theta)", "guide_tilt_max_mm": angle,
            "insert_slop_formula": "radial_play + (wood_max + breakout)*diametral_play/effective_length",
            "insert_slop_max_mm": play, "worst_cap_to_breakout_lever_mm": max_full,
            "inside_wood_path_sufficient_overshoot_mm": 1.,
            "axial_overshoot_condition": "Matched pair total thickness, including any interface gap, must stay within 76.2+/-0.5 mm; normal registration/seating adds at most 0.2 mm. Their 0.7-mm combined endpoint perturbation is within the declared source 1-mm overrun. Guide/cap changes are outside the frame wood capsule. Actual seating is unobserved.",
            "minimum_declared_body_clearance_after_budget_mm": gaps["cases"]["current_body"]["minimum"]["capsule_separation_lower_bound_mm"] - bound,
            "conditional_whole_screw9p525_clearance_after_budget_mm": gaps["cases"]["whole_screw_9p525_containing_capsule_reference"]["minimum"]["capsule_separation_lower_bound_mm"] - bound,
            "bore_only_bound_including_all_reserve_mm": bore_bound,
            "geometric_tie_lower_bounds_mm": {
                "cleat_bottom": d["bore_v"] - d["cleat_bottom_v"] - bore_bound - datum,
                "post_top": d["post_height"] - d["bore_v"] - bore_bound - datum,
                "nearest_crossgrain_raw_edge": min(d["bore_u"][0], d["member_width"]-d["bore_u"][1]) - bore_bound - datum},
            "tie_scope": "Distances only; no load direction, complete Cdelta, end/edge factor, net section, splitting or joint strength is adopted.",
            "reach_requirements_mm": {"nominal_wood_stack": wood, "nominal_guide_flange_cap_stack": guide,
                "nominal_guide_to_point_breakout": full,
                "nominal_free_projection_from_chuck": full + d["free_chuck_to_cap_axial_gap_min"],
                "worst_guide_to_point_breakout": max_full,
                "worst_free_projection_from_chuck": max_full + d["free_chuck_to_cap_axial_gap_min"],
                "worst_wood_exposed_flute_lower_bound": exposed,
                "full_chip_exit_path_reference": max_full,
                "increase_over_earlier_flush19p05_guide": guide - 19.05},
            "chip_clearing_scope": "Wood-exposed flute length alone does not prove chip exit through a guide. Actual bit flute/point, continuous guided engagement, chip exit or supported peck/clearing method and chuck projection remain required inputs. No speed/feed or physical trial is prescribed.",
            "actual_terms_observed_or_achieved": False}


def retainer(inp):
    d = inp["dimensions_mm"]
    lip = (d["bushing_flange_OD"] - d["retainer_clearance_hole_D"])/2
    centers = [[u, d["bore_v"]] for u in d["bore_u"]]
    screw_gap = min(math.dist(h, b) - d["retainer_fastener_head_OD_max"]/2
                    - d["bushing_flange_OD"]/2
                    for h in d["retainer_fastener_centers_uv"] for b in centers)
    require(lip > 0 and screw_gap > 0 and d["bushing_body_OD"] > d["retainer_clearance_hole_D"],
            "retainer capture or fastener/flange plan collision")
    other_flange = abs(d["bore_u"][1]-d["bore_u"][0]) - d["chuck_nose_keepout_radius"] - d["bushing_flange_OD"]/2
    fence = d["bore_u"][0] - d["chuck_nose_keepout_radius"]
    stop = d["bore_v"] - d["cleat_bottom_v"] - d["chuck_nose_keepout_radius"]
    require(min(other_flange, fence, stop) > 0, "local nose access collision")
    above_insert = d["retainer_w"][1] - d["guide_w"][1] + d["guide_cap_stack_deviation_max"]
    radial_play = inp["error_budget"]["bushing_diametral_play_max_mm"]/2
    cap_play = radial_play + above_insert*2*radial_play/d["bushing_effective_length_min"]
    cap_axis_registration = .15
    cap_opening_margin = (d["retainer_clearance_hole_D"] - inp["error_budget"]["maximum_effective_cutting_diameter_mm"])/2 - cap_play - cap_axis_registration
    require(cap_opening_margin > 0, "cap opening cannot contain specified swept bit and insert slop")
    return {"proposed_body_OD_mm": d["bushing_body_OD"], "minimum_effective_guide_length_mm": d["bushing_effective_length_min"],
            "proposed_flange_OD_mm": d["bushing_flange_OD"], "proposed_flange_height_mm": d["bushing_flange_height"],
            "guide_ID": "Match the chosen bit with no more than 0.10 mm diametral play over at least 19.05 mm effective length; an actual product is unselected.",
            "retainer_radial_capture_lip_mm": lip, "minimum_fastener_head_to_flange_plan_gap_mm": screw_gap,
            "cap_hole_to_insert_axis_registration_requirement_mm": cap_axis_registration,
            "bit_center_slop_at_cap_top_bound_mm": cap_play,
            "conditional_cap_hole_swept_bit_radial_margin_mm": cap_opening_margin,
            "fastener_centers_uv_mm": d["retainer_fastener_centers_uv"],
            "spacer_height_mm": d["retainer_spacer_height"],
            "fastener_scope": "Three temporary cap fasteners must end in the guide, stay flush or below the cap top and not penetrate either frame timber. Retaining hardware, cap stiffness and holding force are unqualified.",
            "chuck_nose_keepout_radius_mm": d["chuck_nose_keepout_radius"],
            "keepout_to_other_insert_flange_mm": other_flange,
            "keepout_to_rear_fence_mm": fence, "keepout_to_bottom_stop_mm": stop,
            "minimum_axial_nose_gap_mm": d["free_chuck_to_cap_axial_gap_min"],
            "keepout_scope": "Local nose cross-section above the cap, one bore at a time. The two keepout circles overlap; simultaneous drill heads are not intended. Full drill/handle/hand access is unverified."}


def controls(capsule):
    require(point_rectangle([3., 4.], [[0., 2.], [0., 2.]]) == math.sqrt(5.), "outside-corner fixture")
    require(point_rectangle([1., 1.], [[0., 2.], [0., 2.]]) == 0., "inside rectangle fixture")
    require(point_rectangle([-3., 1.], [[0., 2.], [0., 2.]]) == 3., "outside-edge fixture")
    require(point_rectangle([1., 0.], [[0., 2.], [0., 2.]]) - 1. < 0, "crossing circle control")
    return {"reused_finite_capsule_known_answers": capsule.known_answers(),
            "independent_plan_rectangle_known_answers": 3,
            "negative_contact_circle_control_rejected": True}


def evaluate():
    inp, data, pins, profile, datum, capsule = prepare()
    proposed, shapes, cuts, native = source_inventory(inp, data, profile, datum)
    gaps = clearance(inp, data, proposed, capsule)
    result = {"schema": "eoere_Z180_four_station_paired_fixture_design/v1",
              "status": "UNADOPTED_DIMENSIONED_SOURCE_ONLY_FIXTURE_REQUIREMENTS",
              "question": inp["question"], "source_sha256": dict(sorted(pins.items())),
              "source_pin_count": len(pins), "sources_unchanged_before_after": True,
              "current_Z_mm": inp["current_Z_mm"], "proposed_Z_mm": inp["proposed_Z_mm"],
              "current_revision": inp["current_revision"], "current_geometry_or_100_axes_or_66_screws_changed": False,
              "fixture_coordinates": inp["fixture_coordinates"], "parts": parts(inp["dimensions_mm"]),
              "four_station_coordinate_joins": transforms(inp, proposed, shapes),
              "support_and_clamp_requirements": footprints(inp, shapes, cuts, profile),
              "guide_and_retainer_requirements": retainer(inp), "nominal_primitive_clearance": gaps,
              "pointwise_error_and_reach_budget": budget(inp, gaps),
              "saved_native_four_host_evidence_authenticated_not_replayed": native,
              "saved_signed_end_scope": {"source": inp["sources"]["end_result"],
                  "Z180_geometric_rows": len(data["end_result"]["separate_unadopted_Z180_square_end_markers"]),
                  "current_Z200_actions_assigned_to_Z180": False, "complete_Cdelta_or_strength": None},
              "planned_sequence": inp["planned_sequence"], "genuine_missing_inputs": inp["genuine_missing_inputs"],
              "actual_observations": [{"item": item, "Actual": "", "Disposition": ""}
                                      for item in ("Drill/chuck/handles", "Bit/point/flutes/runout", "Insert/guide/retainer", "Clamps/workholding",
                                                   "Stock/backer/riser/seating", "Full-path error terms", "Hillman/countersink")],
              "method_controls": controls(capsule), "limits": inp["limits"], "release": inp["release"],
              "execution": {"standard_library_source_reads_and_scalar_arithmetic_only": True,
                  "native_BREP_CAD_mesh_FEA_global_force_or_physical_execution": False,
                  "shared_model_document_index_staging_or_commit_action": False,
                  "inherited_source_closures_or_native_query_reaudited": False,
                  "canonical_destination_exclusive_creation": True,
                  "python": sys.version,
                  "reproduce": f"uv run python -B {OWN.relative_to(ROOT)} --out {HERE.relative_to(ROOT)}/reproduction-01.json"}}
    require(not any(n in sys.modules for n in ("cadquery", "OCP", "numpy", "scipy")), "source-only execution")
    verify(pins)
    return inp, result, shapes


def drawing(inp, result, shapes):
    """Compact dimensioned plan and section; no scaled cutting/drilling template."""
    d = inp["dimensions_mm"]
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1260" viewBox="0 0 1600 1260">',
           '<style>text{font:17px sans-serif;fill:#152632}.small{font-size:14px}.title{font-size:27px;font-weight:bold}.dim{stroke:#233b4d;stroke-width:1;fill:none}.part{stroke:#455c69;stroke-width:1.3}.hold{fill:#9d382c;font-weight:bold}</style>',
           '<rect width="1600" height="1260" fill="white"/>']

    def text(x, y, value, cls=""):
        out.append(f'<text x="{x:.3f}" y="{y:.3f}" class="{cls}">{html.escape(value)}</text>')

    def xy(u, v):
        return 260 + 1.65*u, 1050 - 1.65*v

    def rect(u, v, fill, opacity=1):
        x, y = xy(u[0], v[1])
        out.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{(u[1]-u[0])*1.65:.3f}" height="{(v[1]-v[0])*1.65:.3f}" fill="{fill}" fill-opacity="{opacity}" class="part"/>')

    def circle(u, v, r, stroke, fill="none"):
        x, y = xy(u, v)
        out.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{r*1.65:.3f}" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')

    def dim(u1, v1, u2, v2, label, offset=-6):
        a, b = xy(u1, v1), xy(u2, v2)
        out.append(f'<path d="M {a[0]:.3f},{a[1]:.3f} L {b[0]:.3f},{b[1]:.3f}" class="dim"/>')
        for x, y in (a, b):
            out.append(f'<path d="M {x-4:.3f},{y-4:.3f} l 8,8 M {x-4:.3f},{y+4:.3f} l 8,-8" class="dim"/>')
        text((a[0]+b[0])/2, (a[1]+b[1])/2 + offset, label, "small")

    text(40, 42, "Proposed Z180 paired drilling fixture", "title")
    text(40, 70, "Four axes / both hands • dimensions in mm • source-only design • not a cutting or drilling template")
    text(40, 98, "Current Z200 stations remain HOLD. Z180 is unadopted; actual tools, tolerances and workholding are unverified.", "hold")
    text(40, 158, "PLAN", "title")
    rect(d["baseboard_u"], d["baseboard_v"], "#edf1f4")
    rect(d["backer_u"], d["backer_v"], "#d9cbb7")
    for name in ("eoere_cleat_left",):
        points = " ".join(f"{xy(y+175.7,z)[0]:.3f},{xy(y+175.7,z)[1]:.3f}" for y, z in shapes[name]["YZ_polygon_mm"])
        out.append(f'<polygon points="{points}" fill="#e8c98a" fill-opacity="0.55" class="part"/>')
    rect(d["cleat_support_u"], d["cleat_support_v"], "#76b9a8", .55)
    for name in ("rear_fence", "post_bottom_stop", "cleat_guide_bottom_stop"):
        rect(d[name+"_u"], d[name+"_v"], "#8aa0b2", .9)
    rect(d["guide_u"], d["guide_v"], "#86b7d4", .5)
    rect(d["retainer_u"], d["retainer_v"], "#e99767", .65)
    for name, rect_uv in result["support_and_clamp_requirements"]["clamp_arm_plan_lanes_uv_mm"].items():
        rect(*rect_uv, "#b07ab8", .25)
        rect(*result["support_and_clamp_requirements"]["pad_rectangles_uv_mm"][name], "#a351ad", .45)
    for u in d["bore_u"]:
        circle(u, 180, d["chuck_nose_keepout_radius"], "#bc4739")
        circle(u, 180, d["bushing_flange_OD"]/2, "#263a48", "white")
        circle(u, 180, d["retainer_clearance_hole_D"]/2, "#263a48")
    for u, v in d["retainer_fastener_centers_uv"]:
        circle(u, v, 3, "#455c69", "#455c69")
    dim(0, 100, 44.45, 100, "44.45")
    dim(44.45, 100, 95.25, 100, "50.80")
    dim(95.25, 100, 139.7, 100, "44.45")
    dim(160, 139.7, 160, 180, "40.30", -8)
    dim(160, 180, 160, 238.9, "58.90", -8)
    dim(-45, 0, -45, 180, "v180", -6)
    dim(-69.85, 540, 209.55, 540, "Baseboard 279.40 wide")
    dim(0, -10, 100, -10, "100 mm reference")
    text(115, 1130, "Baseboard: u −69.85…209.55; v −25.40…558.80; thickness19.05", "small")
    text(115, 1155, "Guide: u0…139.70; v139.70…241.30; thickness19.05", "small")
    text(115, 1180, "Riser: u0…139.70; v263.525…314.325; nominal height50.80", "small")
    text(115, 1205, "Four clamp pads:25.40 square. Purple = pad / permitted plan lane.", "small")
    text(770, 155, "SECTION at a bore: drilling toward decreasing w", "title")
    section = [("Base", -19.05, 0, "#edf1f4"), ("Backer", 0, 12.7, "#d9cbb7"),
               ("Post", 12.7, 50.8, "#d9cbb7"), ("Cleat", 50.8, 88.9, "#e8c98a"),
               ("Guide", 88.9, 107.95, "#86b7d4"), ("Flange / spacers", 107.95, 111.125, "#b1b9bd"),
               ("Cap", 111.125, 117.475, "#e99767")]
    for index, (label, lo, hi, color) in enumerate(section):
        y = 470 - hi*2.2
        out.append(f'<rect x="820" y="{y:.3f}" width="250" height="{(hi-lo)*2.2:.3f}" fill="{color}" class="part"/>')
        label_y = {4: 260, 5: 232, 6: 204}.get(index, y+13)
        out.append(f'<path d="M 1070,{y+(hi-lo)*1.1:.3f} L 1085,{label_y-5:.3f}" class="dim"/>')
        text(1090, label_y, f"{label}: w {lo:g}…{hi:g}", "small")
    out.append('<path d="M 945,180 V 455 m -7,-12 l 7,12 7,-12" stroke="#bc4739" fill="none" stroke-width="2"/>')
    text(770, 545, "Matched wood stack 76.20; guide/flange/cap 28.575; breakout 6.35.")
    text(770, 573, "Required free projection: 113.125 nominal / 113.825 worst.")
    text(770, 601, "Includes 2.00 chuck-to-cap gap. Overall bit length alone cannot prove fit.")
    text(770, 640, "Guide inserts / cap", "title")
    for y, line in zip(range(670, 811, 28), (
        "Proposed insert body Ø15.875; effective guidance ≥19.05.",
        "Flange Ø22.225×3.175; cap 6.35; cap holes Ø12.70.",
        "Insert IDs match chosen bit; diametral play ≤0.10.",
        "Cap fasteners at u 12.70 / 69.85 / 127.00, v 180; flush.",
        "Fasteners stay in guide; retention/stiffness unqualified.",
        "Red circles: local chuck nose radius 31.75, one axis at a time."), strict=True):
        text(770, y, line)
    text(770, 850, "Registration / full-path budget", "title")
    for y, line in zip(range(880, 1021, 28), (
        "Common rear fence: u 0. Post bottom: v 0. Cleat bottom: v 139.70.",
        "Hole u 44.45 / 95.25; v 180. Post top v 238.90.",
        "Both holes share one setup; separate post and cleat clamps remain.",
        "Relative bore/screw bound 1.50; allocated 1.46; body gap left 2.44375.",
        "Guide normal ≤0.08° over full 111.825-mm path; drift budget applies.",
        "Actuals remain blank. No joint, Cdelta, hardware or machining pass."), strict=True):
        text(770, y, line)
    text(770, 1060, "Handed mapping", "title")
    text(770, 1090, "Y = u −175.70; Z = v. Drill is inward through cleat then post.")
    text(770, 1118, "Left: X = −1168.40 − w. Right: X = 1165.225 + w.")
    text(770, 1146, "No frame member, permanent fastener, current viewer or field changed.")
    text(770, 1174, "Detailed intervals, clamp requirements and missing inputs: sibling JSON.")
    text(770, 1202, "Paper scaling does not establish precision. This drawing authorizes no cut.", "hold")
    out.append("</svg>")
    return ("\n".join(out)+"\n").encode()


def output_paths(requested):
    require(requested.parent.resolve() == HERE and requested.suffix == ".json",
            "output parent must resolve to this owned packet; JSON name required")
    result = HERE / requested.name
    svg = result.with_suffix(".svg")
    require(not os.path.lexists(result) and not os.path.lexists(svg), "fresh canonical JSON and SVG entries required")
    return result, svg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    destination, svg = output_paths(args.out)
    inp, result, shapes = evaluate()
    picture = drawing(inp, result, shapes)
    result["drawing"] = {"path": str(svg.relative_to(ROOT)), "sha256": hashlib.sha256(picture).hexdigest(),
                         "bytes": len(picture), "scale_is_not_a_template": True}
    raw = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+"\n").encode()
    verify(result["source_sha256"])
    with svg.open("xb") as stream:
        stream.write(picture)
    with destination.open("xb") as stream:
        stream.write(raw)
    verify(result["source_sha256"])
    print(json.dumps({"result": str(destination.relative_to(ROOT)), "sha256": hashlib.sha256(raw).hexdigest(),
                      "bytes": len(raw), "drawing": result["drawing"], "source_files": len(result["source_sha256"])}))


if __name__ == "__main__":
    main()
