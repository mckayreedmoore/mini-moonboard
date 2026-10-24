"""Separate current V9 material, connection and section-only comparisons.

Consume the frozen six-case bank. Recompute the conditional elastic steel
screen without a wood-connection group factor; retain the issued connection
references. Reuse exact six-resultant section-traction certificates to test
whether flagged rail cuts admit another stress allocation. Extract simultaneous
Hillman demands without assigning an unsupported resistance or slip law.
No frame/native solve, CAD change or complete-joint acceptance is performed.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import runpy
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np

from scripts import eoere_section_patches as patches
from scripts import eoere_v6_checks as selection
from scripts import eoere_v9_analysis as analysis
from scripts.eoere_bearing_envelope import affine_bearing_upper, utilization
from scripts.eoere_current_reference_review import CurrentIntake
from scripts.eoere_paired_frame_basis import ROOT, read, ref, sha
from scripts.thin_bolted_timber_common_shaft_checks import member_point_inputs
from scripts.thin_bolted_timber_demand_checks import member_cut_wrench
from scripts.timber_vector_shear_bound import section_upper

OWN = Path(__file__).resolve()
BASE = analysis.BASE / "reference-review-v1"
ISSUED = ROOT / "docs/bolted-frame-development/owner-frame-v9/reference-review.json"
ISSUED_SHA = "22529cc9b539ca540b5dd9e496d5a6af19126219b89ac6ae3476f61ea070c657"
NDS = ROOT / "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache/chapter11-2024-awc-20260911.pdf"
THREAD = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/catalog-hardware-strength-v1/thread-root-design-v1/input.json"
SECTION_MATH = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-net-section.py"
PSI = .006894757293168361


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_new(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def elastic_steel_index(axial, moment, shear, diameter, fy):
    """Preserve the issued conservative elastic envelope and Fy/2 hypothesis."""
    values = [float(v) for v in (axial, moment, shear, diameter, fy)]
    require(all(math.isfinite(v) and v >= 0 for v in values)
            and diameter > 0 and fy > 0, "finite nonnegative actions and positive material/section required")
    area = math.pi * diameter**2 / 4
    stress = math.hypot(axial/area + 32*moment/(math.pi*diameter**3), math.sqrt(3)*2*shear/area)
    return stress / (fy/2)


def equal_share_row_example(stiffnesses, load, single_resistance):
    """Distinguish an equal-share row reduction from individual force checks."""
    k = np.asarray(stiffnesses, dtype=float)
    require(k.ndim == 1 and len(k) > 0 and np.isfinite(k).all() and np.min(k) > 0,
            "positive finite parallel fastener stiffnesses required")
    require(load >= 0 and single_resistance > 0, "nonnegative load and positive resistance required")
    forces = load*k/k.sum()
    fraction = float(max(k/k.sum()))
    cg = 1/(len(k)*fraction)
    return {"individual_forces": forces.tolist(), "distribution_Cg": cg,
            "individual_index": float(max(forces)/single_resistance),
            "equal_share_row_index": load/(len(k)*cg*single_resistance),
            "individual_index_with_repeated_distribution_factor": float(max(forces)/(cg*single_resistance))}


def steel_review(geometry, fields, source):
    selected = {row["axis_id"]: row for row in selection.selections(geometry)}
    axes = {row["id"]: row for row in geometry["axes"]}
    profiles = read(THREAD, {})["profiles"]
    cases, maxima = [], []
    for _, case, binding, _ in fields:
        preflight = read(BASE / "complete-v1" / f"nominal-{case}-shafts-preflight-v1.json", {})
        axial = {row["axis"]: row["axial_envelope_N"] for row in preflight["shafts"]}
        own = next(row for row in source["cases"] if row["case_id"] == case)
        require(own["field"] == preflight["field"] == binding, "own current shaft field join required")
        rows = []
        for row in own["shafts"]:
            identity = row["axis_id"]
            a574 = "A574" in selected[identity]["selected_bolt_grade"]
            profile = profiles[1 if axes[identity]["diameter_mm"] > 10 else 0]
            body = 9.3218 if a574 else profile["full_body_minimum_in"]*25.4
            root = profile["proposed_root_floor_in"]*25.4
            fy = (153000 if a574 else 92000)*PSI
            segments = []
            for segment in row["metal"]:
                d = root if segment["root"] else body
                index = elastic_steel_index(axial[identity], segment["maximum_M_Nmm"],
                                            segment["maximum_V_N"], d, fy)
                require(math.isclose(index, segment["N_M_V_index_before_Cdelta"]*row["bounded_Cg"],
                                     rel_tol=1e-10, abs_tol=1e-10), "independent steel arithmetic differs")
                segments.append({"interval_s_mm": segment["interval_s_mm"], "root": segment["root"],
                                 "diameter_mm": d, "elastic_Fy_over_2_index": index})
            worst = max(segments, key=lambda item: item["elastic_Fy_over_2_index"])
            record = {"axis": identity, "case_id": case, "conditional_yield_MPa": fy,
                      "axial_envelope_N": axial[identity], "legacy_Cg": row["bounded_Cg"],
                      "legacy_group_reduced_elastic_index": row["maximum_N_M_V_index_before_Cdelta"],
                      "legacy_connection_yield_work_NM_index_retained": row["maximum_N_M_index_before_Cdelta"],
                      "elastic_Fy_over_2_index": worst["elastic_Fy_over_2_index"], "worst_segment": worst}
            rows.append(record)
            maxima.append(record)
        require(len(rows) == 96 and {row["axis"] for row in rows} == axes.keys(), "all current shafts required")
        cases.append({"case_id": case, "field": binding, "shafts": rows})
    return {"cases": cases, "maximum": max(maxima, key=lambda row: row["elastic_Fy_over_2_index"]),
            "direct_elastic_reference_exceedances": [row for row in maxima if row["elastic_Fy_over_2_index"] > 1],
            "connection_references_replaced_or_Cg_waived": False,
            "conditional_reference_only": True, "complete_joint_qualified": False}


def nondominated_points(points):
    return [p for p in points if not any(
        q["withdrawal_N"] >= p["withdrawal_N"] and q["lateral_N"] >= p["lateral_N"]
        and (q["withdrawal_N"] > p["withdrawal_N"] or q["lateral_N"] > p["lateral_N"])
        for q in points)]


def screw_review(fields):
    by_axis, all_points = {}, []
    for _, case, binding, field in fields:
        laws = {row["id"]: row for row in field["source_inputs"]["hillman_rows"]}
        require(len(laws) == len(field["panel_screw_actions"]) == 66, "all 66 current screw actions required")
        for action in field["panel_screw_actions"]:
            law = laws[action["axis_id"]]
            local = np.asarray(law["basis"]) @ action["force_on_receiver_xyz_n"]
            require(np.max(abs(local-action["local_force_n"])) < 1e-7,
                    "signed current screw force/local basis differs")
            require(math.isclose(math.hypot(*local[1:]), action["lateral_n"], abs_tol=1e-7),
                    "same-case screw lateral force differs")
            require(law["physical_Hillman_stiffness_or_capacity_qualified"] is False
                    and law["ka"] == law["kl"] == 1000., "preserve declared unqualified spring scenario")
            record = {"axis": action["axis_id"], "case_id": case, "field": binding,
                      "receiver": action["receiver"], "panel": action["panel"],
                      "withdrawal_N": action["withdrawal_n"], "lateral_N": action["lateral_n"],
                      "local_force_N": list(action["local_force_n"]),
                      "modeled_axial_extension_mm": action["withdrawal_n"]/law["ka"],
                      "modeled_lateral_slip_mm": action["lateral_n"]/law["kl"]}
            by_axis.setdefault(record["axis"], []).append(record)
            all_points.append(record)
    require(len(by_axis) == 66 and all(len(rows) == 6 for rows in by_axis.values()), "six cases for every screw required")
    return {"maximum_withdrawal": max(all_points, key=lambda p: p["withdrawal_N"]),
            "maximum_lateral": max(all_points, key=lambda p: p["lateral_N"]),
            "same_case_capacity_comparison_points": {axis: nondominated_points(rows) for axis, rows in sorted(by_axis.items())},
            "current_case_point_count": len(all_points), "actual_product_resistance_or_stiffness_established": False,
            "changing_real_stiffness_can_change_these_demands": True,
            "screw_strength_or_assembly_pass_established": False}


def interval_controls(field, member, profile, interval):
    """Reuse issued point-action and affine-gravity math on one fixed branch."""
    actions, gravity = member_point_inputs(field)
    frame = np.asarray(profile["basis_grain_u_v_xyz"])
    datum = np.asarray(profile["datum_xyz_mm"])
    require(np.array_equal(frame[0], [1., 0., 0.]), "current X-grain top rail required")
    low, high = member["source_centerline_grain_interval_mm"]
    lo, hi = interval["world_grain_interval_mm"]
    branch = [(np.asarray(p), np.asarray(f), np.asarray(m)) for p, f, m in actions[member["name"]]
              if frame[0] @ np.asarray(p) < (lo+hi)/2]
    values = []
    for t in (0., 1/3, 2/3, 1.):
        station = lo+t*(hi-lo)
        point = datum+frame[0]*(station-float(frame[0] @ datum))
        cut = member_cut_wrench(frame[0].tolist(), low, high, point.tolist(), *gravity[member["name"]], [])
        force = np.asarray(cut["force_on_lower_portion_xyz_n"])-sum((f for p, f, m in branch), np.zeros(3))
        moment = np.asarray(cut["moment_on_lower_portion_about_cut_xyz_nmm"])-sum(
            (np.cross(p-point, f)+m for p, f, m in branch), np.zeros(3))
        values.append([*map(float, frame@force), *map(float, frame@moment)])
    controls = patches.cubic_controls(values)
    require(min(max(abs(float(a)-b) for a, b in zip(q, interval["witness"]["control_wrench_at_profile_datum_N_Nmm"], strict=True))
                for q in controls) < 1e-5, "own issued control witness not reproduced")
    return controls


def top_section_review(geometry, fields, cores, sections):
    method = runpy.run_path(str(SECTION_MATH), run_name="v9_issued_section_math")
    core = next(row for row in cores["rows"] if row["member"] == "base_rail_top")
    refs = sections["member_properties"]["base_rail_top"]["refs"]
    strengths = {"tension": min(refs["Ft_parallel"], refs["Fb"]),
                 "compression": min(refs["Fc_parallel"], refs["Fb"]),
                 "parallel_shear": refs["Fv_parallel"], "rolling_shear": refs["Fv_parallel"]}
    rows = []
    for _, case, binding, field in fields:
        member = next(row for row in field["source_inputs"]["timber_rows"] if row["name"] == "base_rail_top")
        own = next(row for row in sections["cases"] if row["case_id"] == case)
        rail = next(row for row in own["members"] if row["member"] == "base_rail_top")
        for interval in rail["intervals"]:
            if interval["shear_torsion_reference_upper"] <= 1.:
                continue
            region = next(row for row in core["net_regions"]
                          if row["local_grain_interval_mm"] == interval["net_core_interval_local_L_mm"])
            controls = interval_controls(field, member, geometry["profiles"]["base_rail_top"], interval)
            original = max(section_upper(method["nominal_section"](
                list(map(float, q)), region["retained_rectangles"], refs), refs["Fv_parallel"]) for q in controls)
            require(math.isclose(original, interval["shear_torsion_reference_upper"], rel_tol=1e-8, abs_tol=1e-8),
                    "issued section upper not reproduced")
            boxes = [[*row["bounds_uv_mm"][0], *row["bounds_uv_mm"][1]] for row in region["retained_rectangles"]]
            certificates = []
            for q in controls:
                candidate = patches.candidate(q, boxes, strengths)
                certificate = patches.certify(q, boxes, strengths, candidate["corner_tractions_n_mm2"])
                require(certificate["exact_complete_wrench"] == certificate["exact_recovered_wrench"],
                        "all six encoded control resultants must be carried exactly")
                certificates.append(certificate)
            upper = max(row["construction_upper"] for row in certificates)
            rows.append({"case_id": case, "field": binding, "world_grain_interval_mm": interval["world_grain_interval_mm"],
                         "net_core_interval_local_L_mm": interval["net_core_interval_local_L_mm"],
                         "retained_boxes_uv_mm": boxes, "issued_prismatic_shear_torsion_upper": original,
                         "alternative_section_traction_upper": upper, "control_certificates": certificates,
                         "within_declared_pointwise_section_law": upper <= 1.,
                         "three_dimensional_compatibility_or_free_surface_equilibrium_proved": False,
                         "complete_joint_strength_proved": False})
    require(len(rows) == 5 and {row["case_id"] for row in rows} == {row[1] for row in fields if row[1] != "a1-rear"},
            "every currently flagged top-rail interval required")
    return {"declared_pointwise_strengths_MPa": strengths,
            "law": "max(sigma/Ft,-sigma/Fc)+abs(tau_u)/Fv+abs(tau_v)/Fv <= 1",
            "intervals": rows, "maximum_alternative_traction_upper": max(row["alternative_section_traction_upper"] for row in rows),
            "all_flagged_intervals_have_section_only_certificates_within_law": all(row["within_declared_pointwise_section_law"] for row in rows),
            "current_prismatic_reference_replaced": False, "physical_failure_or_capacity_determined": False}


def bearing_review(geometry, fields, source):
    """Close the endpoint-only method gap without changing any material input."""
    selected = {row["axis_id"]: row for row in selection.selections(geometry)}
    profiles = read(THREAD, {})["profiles"]
    records = []
    segment_count = 0
    for _, case, binding, field in fields:
        shafts = {row["axis_id"]: row for row in field["source_inputs"]["shafts"]}
        own = next(row for row in source["cases"] if row["case_id"] == case)
        require(own["field"] == binding, "own current bearing field required")
        for row in own["shafts"]:
            identity = row["axis_id"]
            shaft = shafts[identity]
            choice = selected[identity]
            profile = profiles[1 if shaft["diameter_mm"] > 10 else 0]
            body = 9.3218 if "A574" in choice["selected_bolt_grade"] else profile["full_body_minimum_in"]*25.4
            root = profile["proposed_root_floor_in"]*25.4
            transition = next(end for end in shaft["ends"] if end["end"] == "head")["pressure_face_s_mm"]+choice["minimum_body_mm"]
            for surface in row["surfaces"]:
                if surface["kind"] != "wood":
                    continue  # Steel pressure norm is convex; its endpoints enclose it.
                physical = next(s for s in shaft["surfaces"] if s["host"] == surface["host"] and s["kind"] == "wood")
                grain = physical["grain_axis_xyz"]
                plywood = surface["host"].startswith("eoere_cleat_")
                pieces = []
                for part in surface["parts"]:
                    lo, hi = part["interval_s_mm"]
                    q0, q1 = np.asarray(part["q0_on_host_N_per_mm"]), np.asarray(part["q1_on_host_N_per_mm"])
                    cuts = [lo, *([transition] if lo < transition < hi else []), hi]
                    for left, right in pairwise(cuts):
                        first = q0+(q1-q0)*(left-lo)/(hi-lo)
                        last = q0+(q1-q0)*(right-lo)/(hi-lo)
                        diameter = root if (left+right)/2 > transition else body
                        bound = affine_bearing_upper(first, last, grain, diameter, plywood=plywood)
                        pieces.append({"interval_s_mm": [left, right], "diameter_mm": diameter,
                                       "sampled_lower_after_Cg": bound["sampled_lower"]/row["bounded_Cg"],
                                       "whole_interval_upper_after_Cg": bound["whole_interval_upper"]/row["bounded_Cg"],
                                       "endpoint_reference_after_Cg": bound["endpoint_maximum"]/row["bounded_Cg"],
                                       "refinements": bound["refinements"]})
                        segment_count += 1
                lower = max(p["sampled_lower_after_Cg"] for p in pieces)
                upper = max(p["whole_interval_upper_after_Cg"] for p in pieces)
                legacy = surface["maximum_bearing_index_before_Cdelta"]
                records.append({"case_id": case, "field": binding, "axis": identity, "host": surface["host"],
                                "legacy_index": legacy, "Cg_retained": row["bounded_Cg"],
                                "sampled_lower": lower, "whole_interval_upper": upper,
                                "confirmed_legacy_underestimate_above_1e_7": lower > legacy+1e-7,
                                "segments": pieces})
    counter_q0, counter_q1 = np.array([-.3709190287, 1., 0.]), np.array([.3709190287, 1., 0.])
    scale = .99/max(utilization(q, [1, 0, 0], 9.525) for q in (counter_q0, counter_q1))
    counter = affine_bearing_upper(scale*counter_q0, scale*counter_q1, [1, 0, 0], 9.525)
    return {"wood_occurrences": records, "wood_occurrence_count": len(records), "affine_segment_count": segment_count,
            "maximum": max(records, key=lambda r: r["whole_interval_upper"]),
            "confirmed_current_legacy_underestimates": [r for r in records if r["confirmed_legacy_underestimate_above_1e_7"]],
            "counterexample_endpoint_pass_interior_exceedance": counter,
            "material_Cg_root_body_and_field_inputs_unchanged": True,
            "complete_Cdelta_or_connection_qualification_established": False}


def run(out, bearing_only=False):
    require(not out.exists() and out.resolve().is_relative_to(analysis.BASE), "fresh own V9 output directory required")
    require(sha(ISSUED) == ISSUED_SHA, "preserve frozen current component review")
    bindings = analysis.context("29db14a7cb6aaf37e5f65ab23f6c9362b1429456a29d4ca02c0e1d5266af00ef",
                                "7c2b913fe5e0efdc36adced6459e5fa79ca873c2a7bc6bcc82721ec02d473109")
    geometry, fields, pins = CurrentIntake(bindings, analysis).load()
    issued = read(ISSUED, pins, ISSUED_SHA)
    sources = {name: read(row["path"], pins, row["sha256"]) for name, row in issued["source_bindings"].items()
               if row["path"].endswith(".json")}
    for source in sources.values():
        for path, digest in source.get("source_sha256", {}).items():
            require(sha(path) == digest, "frozen evidence source changed: "+path)
    out.mkdir(parents=True)
    snapshot = out / "producer-snapshot.py"
    snapshot.write_bytes(OWN.read_bytes())
    for module in list(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if filename:
            path = Path(filename).resolve()
            if path.suffix == ".py" and path.is_relative_to(ROOT) and path != OWN:
                pins[ref(path)["path"]] = sha(path)
    for path in (NDS, THREAD, SECTION_MATH):
        pins[ref(path)["path"]] = sha(path)
    pins[ref(snapshot)["path"]] = sha(snapshot)
    write_new(out / "inputs.json", {"producer": ref(snapshot), "physical_geometry": bindings["receipt"],
              "issued_component_review": ref(ISSUED), "fields": [row[2] for row in fields],
              "source_sha256": pins, "global_native_or_CAD_execution": False})
    if bearing_only:
        result = {"schema": "eoere_v9_whole_affine_bearing_followup/v1", "producer": ref(snapshot),
                  "geometry_revision": analysis.PHYSICAL_REVISION, "physical_geometry": bindings["receipt"],
                  "issued_component_review": ref(ISSUED), "inputs": ref(out / "inputs.json"),
                  "bearing": bearing_review(geometry, fields, sources["shaft_Cg_only"]),
                  "source_sha256": pins, "global_native_or_CAD_execution": False,
                  "structural_acceptance": False}
        write_new(out / "result.json", result)
        print(json.dumps({"result": ref(out / "result.json"), "maximum": result["bearing"]["maximum"],
                          "underestimate_count": len(result["bearing"]["confirmed_current_legacy_underestimates"])}, indent=2))
        return
    result = {"schema": "eoere_v9_joint_criterion_scope_followup/v1", "producer": ref(snapshot),
              "geometry_revision": analysis.PHYSICAL_REVISION, "physical_geometry": bindings["receipt"],
              "issued_component_review": ref(ISSUED), "inputs": ref(out / "inputs.json"),
              "steel": steel_review(geometry, fields, sources["shaft_Cg_only"]),
              "screws": screw_review(fields),
              "top_rail": top_section_review(geometry, fields, sources["timber_cores"], sources["timber_vector"]),
              "known_distribution_example": equal_share_row_example([3., 1.], 100., 100.),
              "source_sha256": pins,
              "tools": {name: importlib.metadata.version(name) for name in ("numpy", "scipy")},
              "loads_geometry_resistances_or_original_criteria_changed": False,
              "full_joint_Cdelta_established": False, "structural_acceptance": False,
              "fabrication_released": False, "climbing_released": False}
    write_new(out / "result.json", result)
    print(json.dumps({"result": ref(out / "result.json"), "steel_max": result["steel"]["maximum"],
                      "top_section_upper": result["top_rail"]["maximum_alternative_traction_upper"],
                      "withdrawal": result["screws"]["maximum_withdrawal"],
                      "lateral": result["screws"]["maximum_lateral"]}, indent=2), flush=True)


def publish(out, public):
    """Publish typed conclusions while retaining every issued comparison."""
    require(not out.exists() and out.resolve().is_relative_to(analysis.BASE), "fresh own publication packet required")
    require(public.parent == ROOT / "docs/bolted-frame-development/owner-frame-v9", "own current public packet required")
    sources = {}
    joint_path = BASE / "joint-followup-v1/attempt-01/result.json"
    bearing_path = BASE / "joint-followup-v1/bearing-envelope-01/result.json"
    joint = read(joint_path, sources, "73a5a02061a80a8f774a8118a52609ac8dd8e1e7d228f2322dbd70495233404e")
    bearing = read(bearing_path, sources, "693fb2ee6440956830b0aa4647f2348a588ea72d5cbc35483795b7c34e947348")
    require(joint["physical_geometry"] == bearing["physical_geometry"] == ref(analysis.RECEIPT),
            "same current physical geometry required")
    require(joint["issued_component_review"] == bearing["issued_component_review"] == ref(ISSUED)
            and sha(ISSUED) == ISSUED_SHA, "frozen issued comparisons required")
    for data in (joint, bearing):
        for path, digest in data["source_sha256"].items():
            require(sha(path) == digest, "follow-up source changed: "+path)
            sources[path] = digest
    require(not joint["steel"]["direct_elastic_reference_exceedances"], "recheck the stated steel conclusion")
    require(joint["top_rail"]["all_flagged_intervals_have_section_only_certificates_within_law"],
            "recheck the section-only conclusion")
    require(not bearing["bearing"]["confirmed_current_legacy_underestimates"], "recheck the current bearing result")
    out.mkdir(parents=True)
    snapshot = out / "producer-snapshot.py"
    snapshot.write_bytes(OWN.read_bytes())
    sources[ref(snapshot)["path"]] = sha(snapshot)
    source_review = {
        "schema": "eoere_v9_joint_followup_sources/v1", "producer": ref(snapshot),
        "nds_2024": {"document": ref(NDS), "publisher": "American Wood Council", "edition": "2024, September 11 web chapter",
                     "recorded_url": "https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf",
                     "current_web_refetch_succeeded": False,
                     "inspection": "Read authenticated retained primary PDF using pypdf[crypto] 6.21.2. Section 11.2.3: PDF page 3, printed page 70. Section 11.3.6: PDF page 6, printed page 73.",
                     "scope": "Metal-controlled strength uses applicable metal procedures without NDS connection factors. Cg adjusts lateral connection reference Z. A separate elastic stress screen cannot replace dowel-bending/yield and complete-connection checks."},
        "awc_commentary": {"url": "https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf",
                           "locator": "C11.2.3, printed page 251; C11.3.6, printed pages 251-252",
                           "scope": "Corroborates the metal/connection distinction and explains nonuniform row loading. Earlier commentary supplies interpretation, not a new current capacity."},
        "hillman_listing": {"url": "https://www.lowes.com/pd/Hillman-10-x-2-1-2-in-Ceramic-Deck-Screws-50-Count/999995042",
                            "checked_UTC_date": "2026-10-24", "scope": "Owner-selected model 42605 metadata only. The inspected description/specifications give no structural resistance or load-slip curve. The older rating Q&A was not retrievable; no newly inspected manufacturer reply is claimed."},
        "icc_es": {"url": "https://cdn-v2.icc-es.org/wp-content/uploads/report-directory/ESL-1284.pdf",
                   "edition": "Reissued July 2026, renewal July 2027", "locator": "Page 1",
                   "scope": "Corrosion listing for Power-Pro, Deckplus and Profast families; it neither names Fas-n-Tite 42605 nor supplies its connection strength."},
        "astm": {"url": "https://store.astm.org/standards/d1761", "edition": "D1761-20(2025)",
                 "scope": "Withdrawal/lateral characterization framework. It supplies no measured result for this screw, wood, panel, pilot or countersink."},
        "no_product_capacity_stiffness_or_standard_conformity_invented": True}
    write_new(out / "source-review.json", source_review)
    top = joint["top_rail"]
    result = {
        "schema": "eoere_v9_joint_followup_scope_review/v1", "producer": ref(snapshot),
        "geometry_revision": analysis.PHYSICAL_REVISION, "physical_geometry": joint["physical_geometry"],
        "analysis_geometry": ref(analysis.GEOMETRY), "previous_reference_review": ref(ISSUED),
        "response_bank": ref(ROOT / "docs/bolted-frame-development/owner-frame-v9/response-bank.json"),
        "source_bindings": {"joint_scope": ref(joint_path), "whole_affine_bearing": ref(bearing_path),
                            "sources": ref(out / "source-review.json"), "nds_primary": ref(NDS)},
        "direct_elastic_steel_screen": {
            "maximum": joint["steel"]["maximum"], "case_count": 6, "bolts_per_case": 96,
            "reference": "Existing conditional elastic envelope divided by Fy/2; same N, M, V, body/root and grade inputs, without wood-connection Cg.",
            "exceedance_count": 0, "Cg_applied": False,
            "replaces_lateral_connection_yield_or_complete_joint_check": False,
            "applicable_metal_standard_design_or_delivered_strength_qualified": False},
        "retained_connection_references": {
            "reduced_axial_bending_maximum": 1.3700573621183423,
            "legacy_group_reduced_elastic_screen_maximum": 1.1543069526550356,
            "whole_affine_bearing_maximum": bearing["bearing"]["maximum"]["whole_interval_upper"],
            "Cg_waived_or_recomputed_from_unsupported_group_inputs": False,
            "complete_Cdelta": None,
            "interpretation": "The legacy 1.154 screen includes a wood-connection reduction and is not an independent direct steel-strength result. Connection yield-work, wood bearing, oblique detailing, seats and complete joints remain separate and unresolved."},
        "top_rail_section_followup": {
            "issued_prismatic_shear_torsion_maximum_retained": 1.1692252292298393,
            "flagged_intervals": len(top["intervals"]), "bernstein_controls_certified": 4*len(top["intervals"]),
            "alternative_section_traction_upper": top["maximum_alternative_traction_upper"],
            "pointwise_law": top["law"], "working_strengths_MPa": top["declared_pointwise_strengths_MPa"],
            "all_six_encoded_control_resultants_recovered_exactly": True,
            "every_hole_and_contained_ligament_preserved": True,
            "source_wrench_and_issued_upper_replay_tolerance": "1e-5 N/Nmm for witness; 1e-8 relative/absolute for issued upper",
            "interpretation": "Every flagged interval admits a different bounded section traction under the declared scalar hypothesis. The 17% prismatic overrun is therefore distribution-dependent; the new construction does not prove compatible three-dimensional stresses, free side faces, local fracture, load introduction or joint capacity.",
            "physical_capacity_or_safety_multiplier_established": False,
            "issued_top_reference_cleared_or_replaced": False},
        "bearing_method_correction": {
            "wood_occurrences_checked": bearing["bearing"]["wood_occurrence_count"],
            "affine_pressure_segments_checked": bearing["bearing"]["affine_segment_count"],
            "endpoint_only_utilization_is_a_general_bound": False,
            "counterexample": bearing["bearing"]["counterexample_endpoint_pass_interior_exceedance"],
            "method": "Whole affine interval upper uses enclosing norm/grain-angle bounds with branch refinement and explicit outward allowance; numerical floating enclosure, not a formal interval-arithmetic certificate.",
            "current_underestimates_above_1e_7": 0,
            "current_maximum": bearing["bearing"]["maximum"]["whole_interval_upper"]},
        "hillman_demand_requirements": {
            "product": "Purchased Hillman/Fas-n-Tite 42605, nominal #10 x 2.5 in; policy unchanged",
            "peak_withdrawal_with_simultaneous_lateral": joint["screws"]["maximum_withdrawal"],
            "peak_lateral_with_simultaneous_withdrawal": joint["screws"]["maximum_lateral"],
            "screws": 66, "current_simultaneous_case_points": joint["screws"]["current_case_point_count"],
            "separate_case_peaks_combined_into_false_load_point": False,
            "modeled_ka_kl_N_per_mm": [1000, 1000],
            "force_divided_by_model_stiffness_is_a_measured_slip": False,
            "supported_product_capacity_or_force_slip_curve_established": False,
            "changing_stiffness_requires_recomputed_coupled_demands": True,
            "missing_inputs": ["Exact-SKU major/root/head/thread dimensions and applicable material/standard evidence",
                               "Withdrawal/lateral force-slip and resistance for the actual receiver wood, penetration and pilot",
                               "Head pull-through and panel-edge resistance for the actual plywood/countersink",
                               "Applicable simultaneous withdrawal/lateral interaction and variability/design basis"],
            "physical_test_or_supplier_contact_performed": False},
        "next_actions": [
            "Keep material and connection criteria separate. Complete applicable oblique row/end/edge and mixed-stack connection checks without inferring a Cg waiver from the elastic screen.",
            "For a compatible 3D top-corner assessment, define and conserve the current bore, washer, panel-contact and screw load footprints; evaluate warping and brittle modes under the recorded orthotropic/material assumptions.",
            "Seek exact-product evidence or define representative withdrawal/lateral and panel-head characterization; use the saved same-case screw demand points. No physical work is authorized or claimed by this report.",
            "If a supported local criterion remains exceeded, investigate a small change in existing timber bearing or load entry; no geometry, new fastener policy, larger allowable or release is selected here."],
        "source_sha256": sources,
        "global_native_or_CAD_execution": False, "original_force_fields_or_frozen_reports_changed": False,
        "structural_acceptance": False, "complete_joint_qualified": False,
        "fabrication_released": False, "climbing_released": False}
    write_new(out / "review.json", result)
    write_new(public, result)
    print(ref(public), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--bearing-only", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--public", type=Path, default=ROOT / "docs/bolted-frame-development/owner-frame-v9/criterion-scope-review.json")
    args = parser.parse_args()
    if args.publish:
        publish(args.out.resolve(), args.public.resolve())
    else:
        run(args.out.resolve(), args.bearing_only)


if __name__ == "__main__":
    main()
