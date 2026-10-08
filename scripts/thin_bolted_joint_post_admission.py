"""Reduce one freshly admitted first-order joint field with frozen pure methods.

The caller runs the NEW support-search admission on these same immutable bytes.
This module does not call legacy consumers, assemble stiffness, query CAD, solve,
or replace missing complete resistances with nominal component references.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np

from scripts import thin_bolted_common_shaft_steel_bound as steel
from scripts import thin_bolted_flange_torsion as torsion
from scripts import thin_bolted_panel_coupled as panel
from scripts import thin_bolted_timber_common_shaft_checks as timber

references, unit = timber.previous, timber.unit
ROOT, PACKET = unit.ROOT, unit.PACKET
GATE = "scripts/thin_bolted_support_search_admission.py"
ADMISSION_SCHEMA = "thin_bolted_independent_support_search_admission/v1"
ADMISSION_SUCCESS = "independent_support_search_face_source_map_law_and_equilibrium_checks_pass"
IDENTITIES = ("state_id", "case_id", "accessory_placement")
SCHEMA = "thin_bolted_post_admission_joint_references/v1"
LOADED_PRODUCER_SHA256 = unit.sha(Path(__file__))
PINS = {
    "scripts/thin_bolted_timber_common_shaft_checks.py": "c27d8d0209f2b0a032c490314fe05cee8fbc949f608dabbf813676c044b90cc7",
    "scripts/thin_bolted_timber_demand_checks.py": timber.PREVIOUS_SHA,
    "scripts/thin_bolted_timber_resistance.py": "74d992cfbe4947587a8c6f0e65f7a8b47e0cd1c79f07721620c7137208919c2d",
    "scripts/thin_bolted_timber_section_properties.py": timber.SECTIONS_SHA,
    "scripts/thin_bolted_common_shaft.py": timber.COMMON_SHA,
    "scripts/thin_bolted_common_shaft_steel.py": timber.STEEL_SHA,
    "scripts/thin_bolted_common_shaft_steel_bound.py": "4b5973697d6ed5a5ca4ae39b2bd836ff044e1cb5858934879ff1e86649b0a037",
    "scripts/thin_bolted_steel_resistance.py": torsion.FROZEN_STEEL_SHA,
    "scripts/thin_bolted_flange_torsion.py": "48e3181f65772cb2d21be6687a011eaeba6a35491b6299cd179759f66ffc6871",
    "scripts/thin_bolted_panel_coupled.py": "abd6da1911ec79ec25b57fc2a5cc20b9e687057a15b6df2f5e8fb292a42c6bd0",
    "scripts/thin_bolted_panel_mechanics.py": panel.METHOD_SHA,
    str(panel.ASSESSMENT.relative_to(ROOT)): panel.ASSESSMENT_SHA,
    str(panel.VALIDATION.relative_to(ROOT)): panel.VALIDATION_SHA,
    str(panel.DATUMS.relative_to(ROOT)): panel.DATUMS_SHA,
    str(panel.panel_method.INTEGRATED.relative_to(ROOT)): panel.panel_method.INTEGRATED_SHA,
    str(timber.SPAN_SOURCE.relative_to(ROOT)): timber.SPAN_SOURCE_SHA,
    str(steel.methods.METHODS.relative_to(ROOT)): steel.methods.METHODS_SHA,
    str(steel.methods.HEAD.relative_to(ROOT)): steel.methods.HEAD_SHA,
    str(steel.METHOD_RECEIPT.relative_to(ROOT)): steel.METHOD_RECEIPT_SHA,
}
PROPERTY_PINS = {
    "timber-leg-recess-sections-v4.json": "94fd730a72bdb93efc5d654913a162bb9a9715af342e91ebb11e873006969574",
    "timber-service-cut-sections-v4.json": "5bef4fd71aaa9a6f817ca35a424fdde82fd92dcce1741bbb1f3e9f0f74859ce4",
}


def verify_pins(pins: dict) -> None:
    for relative, expected in pins.items():
        unit.require(isinstance(relative, str) and not Path(relative).is_absolute()
                     and ".." not in Path(relative).parts
                     and isinstance(expected, str) and re.fullmatch("[0-9a-f]{64}", expected) is not None
                     and unit.sha(ROOT / relative) == expected, "post-admission source differs: " + str(relative))


def require_admission(payload: bytes, field: dict, admission: dict, admission_sha256: str) -> None:
    unit.require(isinstance(payload, bytes), "same immutable released byte payload required")
    unit.require(re.fullmatch("[0-9a-f]{64}", admission_sha256 or "") is not None,
                 "mandatory reviewed NEW support-search admission SHA256 required")
    unit.require(ADMISSION_SCHEMA != "UNISSUED" and ADMISSION_SUCCESS != "UNISSUED",
                 "NEW support-search admission contract must be issued")
    unit.require(admission.get("schema") == ADMISSION_SCHEMA and admission.get(ADMISSION_SUCCESS) is True,
                 "NEW support-search admission receipt required; legacy receipts rejected")
    unit.require(admission.get("field_sha256") == hashlib.sha256(payload).hexdigest()
                 and admission.get("field_canonical_sha256") == references.canonical_sha(field)
                 and all(admission.get(key) == field[key] for key in IDENTITIES)
                 and admission.get("source_sha256", {}).get(GATE) == admission_sha256,
                 "NEW admission receipt does not bind exact raw/canonical/state/source identity")
    verify_pins({GATE: admission_sha256})
    unit.require(field.get("schema") == "thin_bolted_common_shaft_frame/v1"
                 and field.get("linear_timber_face_method") == "source-bound-linear-finished-paired-wood-compression-v1"
                 and field.get("candidate") == unit.CANDIDATE
                 and field.get("layout_report_sha256") == unit.LAYOUT_SHA
                 and field.get("geometry_cache_sha256") == references.NATIVE_SHA
                 and field.get("state_id") == references.state_identity(field), "first-order candidate/source/state differs")
    response = field.get("response", {})
    q = np.asarray(response.get("q", []), dtype=float)
    unit.require(response.get("converged") is True and field.get("usable_conditional_actions") is True
                 and q.shape == (field["counts"]["dofs"],) and np.isfinite(q).all(),
                 "accepted saved q required; diagnostic_last_q cannot supply reductions")
    unit.require(admission.get("support_search_checks", {}).get("final_q_canonical_sha256")
                 == references.canonical_sha(q.tolist()), "fresh receipt does not bind accepted final q")
    unit.require(field.get("release") and not any(field["release"].values())
                 and admission.get("release") and not any(admission["release"].values()), "release must remain false")
    unit.require(not field.get("attachment_actions") and not field.get("retained_bolt_actions"),
                 "legacy paired-force aliases cannot substitute for physical shafts")


def face_reference_summaries(field: dict, full: dict) -> list[dict]:
    """N/Aref beside Fc-perp for both own reference timbers; no pressure rating."""
    rows = [r for r in field["contact_actions"] if r["kind"] == "timber_face_contact"]
    alias = field["timber_face_contact_actions"]
    indexed = {r["id"]: r for r in rows}
    unit.require(len(rows) == len(indexed) == len(alias) == 272
                 and indexed == {r["id"]: r for r in alias}, "all272 unique faces and exact unused alias required")
    grains = {r["member"]: np.asarray(r["grain_axis_xyz"]) for r in full["finished_member_sections"]}
    groups = {}
    fc = 625. * unit.N_PER_LBF / 25.4**2
    for row in rows:
        unit.require(all(row.get(k) == field[k] for k in IDENTITIES), "face action mixes admitted identity")
        area, force = row["cell_area_mm2"], row["compression_n"]
        normal = np.asarray(row["direction_xyz"], dtype=float)
        unit.require(math.isfinite(area) and area > 0. and math.isfinite(force) and force >= 0.
                     and normal.shape == (3,) and np.isfinite(normal).all()
                     and abs(np.linalg.norm(normal)-1.) < 1e-8, "invalid reference-area face action")
        dots = {name: float(normal @ grains[name]) for name in (row["first"], row["second"])}
        unit.require(all(abs(dot) < 1e-8 for dot in dots.values()), "Fc-perp benchmark requires both reference grains perpendicular")
        groups.setdefault((row["first"], row["second"]), []).append({
            **{key: row[key] for key in (*IDENTITIES, "id", "first", "second", "point_xyz_mm")},
            "compression_n": force, "reference_cell_area_mm2": area,
            "normal_dot_each_reference_grain": dots, "normal_force_over_reference_cell_area_mpa": force/area,
            "unadjusted_Fc_perp_reference_mpa": fc, "CD_factor": 1., "CB_increase_applied": False,
            "reference_area_component_ratio": force/(area*fc), "physical_pressure_or_complete_joint_capacity": None})
    unit.require(len(groups) == 6, "all six own timber face pairs required")
    return [{"first": pair[0], "second": pair[1], "cell_count_including_zeros": len(cells),
             "loaded_cell_count": sum(c["compression_n"] > 0. for c in cells),
             "total_model_compression_n": sum(c["compression_n"] for c in cells),
             "total_reference_area_mm2": sum(c["reference_cell_area_mm2"] for c in cells),
             "governing_reference_area_cell_witness": max(cells, key=lambda c: c["reference_area_component_ratio"]),
             "limits": "First-order reference normals/areas and cell resultants only; current overlap, continuous/local pressure, bedding refinement, fracture and physical bearing capacity remain unresolved."}
            for pair, cells in groups.items()]


def panel_reductions(field: dict, layout: dict, samples: int) -> dict:
    """Reuse saved coefficients and preserve signed world/local screw ports."""
    unit.require(field["source_sha256"].get("scripts/thin_bolted_panel_mechanics.py") == panel.METHOD_SHA,
                 "admitted panel producer differs")
    assessment = json.loads(panel.ASSESSMENT.read_bytes())
    integrated = json.loads(panel.panel_method.INTEGRATED.read_bytes())
    panels = panel.prepared_datums(field, assessment, json.loads(panel.DATUMS.read_bytes()), integrated)
    expected = {row["axis_id"]: row for row in layout["screw_axes"]}
    actions = field["panel_screw_actions"]
    unit.require(len(actions) == len({r["axis_id"] for r in actions}) == 66
                 and {r["axis_id"] for r in actions} == set(expected), "all66 unique screw ports required")
    screws = []
    for row in actions:
        unit.require(all(row.get(k) == field[k] for k in IDENTITIES), "screw port mixes admitted identity")
        source, sheet = expected[row["axis_id"]], panels[row["panel"]]
        datum = sheet["geometry"]
        force = np.asarray(row["force_on_receiver_xyz_n"])
        projected = force @ datum["axes"][:, [2, 0, 1]]
        point = np.asarray(source["origin_xyz_mm"]) + datum["inward"]*sheet["thickness"]/2
        unit.require(row["panel"] == source["panel"] and row["receiver"] == source["receiver"]
                     and np.max(abs(point-np.asarray(row["point_xyz_mm"]))) < 1e-6
                     and np.max(abs(projected-np.asarray(row["local_force_n"]))) < 1e-6,
                     "same-axis ownership, point or signed world/local force differs")
        screws.append(panel.screw_references(row, sheet["thickness"]))
    rows = []
    for name, sheet in panels.items():
        q = sheet["q"]
        resolved = panel.panel_method.resolved_section_references(sheet, q, samples)
        points = np.asarray([r["xy_mm"] for r in resolved["components"].values()])
        simultaneous = panel.plate_fields(sheet, points, q)
        rows.append({"panel": name, **{k: field[k] for k in IDENTITIES},
                     "resolved_section_diagnostics": resolved,
                     "simultaneous_fields_at_section_witnesses": [
                         {"governing_component": key, "xy_mm": points[i].tolist(),
                          **{k: float(v[i]) for k, v in simultaneous.items()}}
                         for i, key in enumerate(resolved["components"])],
                     "integrated_net_section_diagnostics": panel.integrated_net_diagnostics(sheet, q, samples),
                     "edge_transfer_diagnostics": panel.panel_method.edge_transfer_diagnostics(sheet, q, samples),
                     "deformation_diagnostics": panel.deformation_diagnostics(sheet, q, samples)})
    return {"six_saved_coefficient_blocks_and_global_slices_verified": True,
            "all66_world_local_signed_screw_projections_verified": True,
            "panel_diagnostics": rows, "screw_actions_and_generic_references": screws,
            "complete_panel_or_Hillman_product_resistance": None}


def flange_torsion_reductions(field: dict, components: dict, layout: dict) -> list[dict]:
    """Reuse same-cut pure torsion arithmetic without constructing old receipts."""
    fittings = {r["angle_id"]: r for r in layout["raw_fittings"]}
    rows = components["fresh_flange_component_comparison"]["flange_comparisons"]
    output = []
    for row in rows:
        unit.require(all(row[k] == field[k] for k in ("case_id", "accessory_placement")), "flange mixes admitted case")
        cuts = torsion.frozen.flange_reference(fittings[row["angle_id"]], row["flange"],
                                               row["external_point_actions_on_steel"])["sections"]
        samples = {"gross_rectangle": [], "two_ligament_equal_twist_proxy": []}
        for cut in cuts:
            chord = max(0., torsion.frozen.WIDTH-cut["area_mm2"]/torsion.frozen.THICKNESS)
            for scenario, scenario_samples in samples.items():
                if scenario == "two_ligament_equal_twist_proxy" and chord <= 1e-8:
                    continue
                scenario_samples.append({"station_from_assumed_corner_mm": cut["station_from_assumed_corner_mm"],
                    **torsion.simultaneous_section_bound(width_mm=torsion.frozen.WIDTH,
                        thickness_mm=torsion.frozen.THICKNESS, removed_center_width_mm=chord,
                        force_local_n=cut["force_local_n"], moment_local_nmm=cut["moment_local_nmm"],
                        fy_mpa=torsion.frozen.FY_CATALOG, scenario=scenario)})
        output.append({**{k: field[k] for k in IDENTITIES}, "angle_id": row["angle_id"], "flange": row["flange"],
            "each_witness_retains_same_cut_N_V_M_T": True,
            "sampled_scenario_witnesses": {key: max(values, key=lambda r: r["simultaneous_nominal_vm_bound_mpa"], default=None)
                                           for key, values in samples.items()},
            "actual_hole_heel_warping_and_complete_fitting_resistance": None})
    unit.require(len(output) == len({(r["angle_id"], r["flange"]) for r in output}) == 72, "all72 own flange diagnostics required")
    return output


def governing_references(wood: dict, metal: dict, sheets: dict) -> dict:
    """Select coherent reference witnesses; index<=1 is never a joint pass."""
    cuts = wood["simultaneous_existing_member_cut_witnesses"]
    candidates = {
        "timber_average_tension_CD1": [(r["maximum_tension_average_area_witness"]["tension_average_area_reference"]["CD1_same_state_component_ratio"], r["maximum_tension_average_area_witness"]) for r in cuts],
        "timber_average_compression_CD1": [(r["maximum_compression_average_area_witness"]["compression_average_area_reference"]["CD1_same_state_component_ratio"], r["maximum_compression_average_area_witness"]) for r in cuts],
        "wood_ideal_capture_annulus_no_CD": [(r["own_model_capture_over_ideal_annulus_component_ratio"], r) for r in wood["own_direct_wood_capture_annulus_references"]],
        "timber_face_reference_area_no_CD": [(r["governing_reference_area_cell_witness"]["reference_area_component_ratio"], r["governing_reference_area_cell_witness"]) for r in wood["six_face_reference_area_summaries"]],
        "generic_screw_head_CD1": [(r["generic_head_ratio_CD1"], r) for r in sheets["screw_actions_and_generic_references"]],
        "shaft_elastic_circle_Grade5_Fy_scenario": [(s["sampled_governing_section"]["same_section_nominal_first_yield_index"], {"axis_id": r["axis_id"], **s})
            for r in metal["shaft_same_section_references"] for s in r["section_scenarios"] if s["section_scenario"]["id"] == "elastic_model_circle"],
    }
    for scenario in ("gross_rectangle", "two_ligament_equal_twist_proxy"):
        candidates["flange_"+scenario+"_torsion_bound_Fy33ksi"] = [
            (r["sampled_scenario_witnesses"][scenario]["simultaneous_nominal_first_yield_bound_index"], r)
            for r in metal["flange_torsion_diagnostics"] if r["sampled_scenario_witnesses"][scenario] is not None]
    for key in ("mean_net_bending_ratio_CD1", "mean_net_rolling_shear_ratio_CD1", "mean_net_axial_ratio_CD1"):
        candidates["panel_"+key] = [(r["integrated_net_section_diagnostics"]["simultaneous_signed_cut_witnesses"][key][key],
                                    {"panel": r["panel"], **r["integrated_net_section_diagnostics"]["simultaneous_signed_cut_witnesses"][key]})
                                   for r in sheets["panel_diagnostics"]]
    result = {}
    for key, values in candidates.items():
        index, witness = max(values, key=lambda r: r[0])
        unit.require(math.isfinite(index) and index >= 0., "nonfinite or negative governing reference index")
        result[key] = {"reference_index": index, "coherent_witness": witness,
                       "reference_index_above_one": index > 1., "status": "CONDITIONAL_COMPONENT_REFERENCE_ONLY",
                       "adopted_complete_resistance_or_joint_pass": None}
    return result


def post_admission_reductions(field: bytes, admission: dict, *, admission_sha256: str,
                             samples: int = 41, caller_sections: dict | None = None) -> dict:
    """Caller-admitted immutable bytes -> same-state conditional components."""
    unit.require(isinstance(field, bytes), "immutable field bytes required")
    demand = json.loads(field)
    field_before, admission_before = references.canonical_sha(demand), references.canonical_sha(admission)
    caller_before = references.canonical_sha(caller_sections)
    require_admission(field, demand, admission, admission_sha256)
    unit.require(isinstance(samples, int) and not isinstance(samples, bool) and 3 <= samples <= 101,
                 "panel sample count must be an integer from3 to101")
    pins = {**PINS, GATE: admission_sha256, str(Path(__file__).relative_to(ROOT)): LOADED_PRODUCER_SHA256}
    for source in (demand["source_sha256"], admission["source_sha256"]):
        for path, digest in source.items():
            unit.require(path not in pins or pins[path] == digest, "contradictory admitted source pin")
            pins[path] = digest
    verify_pins(pins)
    packet, _, layout = references.read_unit()
    for report in (packet, json.loads(steel.methods.METHODS.read_bytes()), json.loads(steel.methods.HEAD.read_bytes())):
        for path, digest in report["source_sha256"].items():
            unit.require(path not in pins or pins[path] == digest, "frozen component source contradicts admission")
            pins[path] = digest
    detail = packet["reproducible_detail_artifact"]
    pins.update({detail["path"]: detail["sha256"], str(references.UNIT.relative_to(ROOT)): references.UNIT_SHA})
    verify_pins(pins)
    full = json.loads((ROOT / detail["path"]).read_bytes())["finished_geometry_queries"]
    timber.verify_alias_state_labels(demand)
    steel.verify_component_state_labels(demand)
    wood = timber.aggregate_wood_bearings(layout, {"finished_geometry_queries": full}, demand)
    spans = timber.read_member_span_geometry()
    span_receipt = timber.verify_member_span_geometry(demand, spans)
    member_cuts = timber.replay_existing_member_cuts(demand, full, spans)
    duration = references.read_duration_sources()
    properties = []
    for name, digest in PROPERTY_PINS.items():
        path = PACKET / name
        pins[str(path.relative_to(ROOT))] = digest
        verify_pins({str(path.relative_to(ROOT)): digest})
        report = json.loads(path.read_bytes())
        unit.require(report["state_id"] is None and report["candidate"] == unit.CANDIDATE
                     and not any(report["release"].values()), "only unchanged geometry-only net properties may be reused")
        properties.extend(report["finished_sections"])
        for relative, expected in report["source_sha256"].items():
            unit.require(relative not in pins or pins[relative] == expected, "net property source contradicts admission")
            pins[relative] = expected
    receivers = {(r["axis_id"], r["member"]): r for r in full["receiver_boundary_geometry"]}
    wood_result = {"actual82wood_bearing_wrenches": wood,
        "actual164wood_body_root_bearing_parameter_diagnostics": timber.bearing_parameter_diagnostics(wood, layout),
        "own_direct_wood_capture_annulus_references": timber.own_wood_washer_references(demand, packet),
        "simultaneous_existing_member_cut_witnesses": member_cuts,
        "current70conditional_thread_windows": [references.standard_thread_window(a, receivers) for a in layout["installed_axes"]],
        "six_face_reference_area_summaries": face_reference_summaries(demand, full),
        "independent_member_span_geometry": span_receipt, "conditional_duration_source": duration,
        "five_existing_geometry_only_net_properties": properties,
        "actual_trimmed_section_normal_stress_extrema": None,
        "general_distributed_NDS_yield_group_splitting_shear_torsion_stability_resistance": None}
    metal = steel.component_values(demand, caller_sections)
    metal["flange_torsion_diagnostics"] = flange_torsion_reductions(demand, metal, layout)
    sheets = panel_reductions(demand, layout, samples)
    for row in duration["authenticated_primary_sources"]:
        pins[row["path"]] = row["sha256"]
    pins[duration["source_metadata_path"]] = duration["source_metadata_sha256"]
    unit.require(len(wood) == 82 and len(member_cuts) == 20
                 and len(wood_result["own_direct_wood_capture_annulus_references"]) == 68
                 and len(wood_result["current70conditional_thread_windows"]) == 70
                 and len(properties) == 5, "complete retained component census required")
    summary = governing_references(wood_result, metal, sheets)
    unit.require(references.canonical_sha(demand) == field_before
                 and references.canonical_sha(admission) == admission_before
                 and references.canonical_sha(caller_sections) == caller_before, "input changed during reductions")
    verify_pins(pins)
    return {"schema": SCHEMA, "candidate": demand["candidate"], **{k: demand[k] for k in IDENTITIES},
            "parameters": demand["parameters"], "field_sha256": hashlib.sha256(field).hexdigest(),
            "field_canonical_sha256": field_before, "independent_fresh_support_search_admission": admission,
            "source_sha256": pins, "timber": wood_result, "steel": metal, "panels": sheets,
            "governing_conditional_reference_dispositions": summary,
            "method": {"same_immutable_bytes_used_by_caller_admission": True, "legacy_consumers_called": False,
                       "timber_face_rows_consumed_once_from_contact_actions": True,
                       "face_alias_added_to_cuts": False, "old_paired_force_aliases_manufactured": False,
                       "shaft_cuts_use_only_own_bearing_capture_and_body_loads": True,
                       "CAD_query_K_assembly_native_or_response_execution": False},
            "limits": ["First-order source stiffness/material/contact scenarios are unmeasured and do not establish physical demand bounds.",
                       "Every selected cut keeps simultaneous signed actions. Separate extrema are never combined into a physical cut.",
                       "Generic Fyb/Fe/root sensitivities, Grade5 tensile-yield circle references and nominal flange bounds are not adopted product/joint resistances.",
                       "Reference face cells and washer annuli do not qualify actual continuous pressure, overlap, spreading, prying, head/nut/thread or local fracture.",
                       "Five saved net properties are geometry-only inputs; trimmed-boundary bending extrema, section stiffness, shear/fracture/stability and complete20-member assessment remain unresolved.",
                       "Hillman product withdrawal/lateral/steel and local panel seat/punching/edge capacities remain unavailable."],
            "complete_joint_resistance": None, "all18_completion_gates_open": True,
            "complete_joint_acceptance": False, "release": dict(unit.RELEASE)}
