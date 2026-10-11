"""Current admitted-state component references; no frame solve or remedies.

Frozen reducers retain their arithmetic. This adapter supplies exact current
intake, axes, apertures and spacer loading, and preserves unknown resistance.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import eoere_current_response as current
from scripts import summarize_eoere_current_response as saved_force_summary
from scripts.summarize_eoere_current_response import SEQUENCE, canonical_sha

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
BASE = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/"
MECH = BASE + "adjusted-base-mechanics-v1/"
PACKET = current.DOC / "selected-hardware-v1/current-response-v1"
INPUTS = PACKET / "components-inputs.json"
RAW = current.RAW.parent / "current-components-v1"
CASE_ATTEMPT = "attempt02"
CANONICAL_HELPER = {"path": "scripts/summarize_eoere_current_response.py",
                    "sha256": "1d613e1151d61132e6e591d814cef8d1edc0cc209377ff5a6cf28aa461f6e34b"}
FROZEN = {
    "consumer": {"path": MECH + "current-component-bridge-v1/consumer-v1/consume.py",
                 "sha256": "f11175782c7b29abbdfbcbf5fbad63f919596bc6a613b4c7a5b65acc1027bad9"},
    "followups": {"path": MECH + "current-component-bridge-v1/followups-v1/followups.py",
                 "sha256": "a27bacf7260905f69c2a69bae60c0f2cf4ed1f4efd229100e3c8fb846b892798"},
    "plan": {"path": MECH + "current-component-bridge-v1/component_plan.py",
             "sha256": "caf5d1307d999843c3ea16f3536f5bdd25edb390ebbab6e624cf5f5a86dc727e"},
    "summary": {"path": MECH + "current-component-results-v1/summarize.py",
                "sha256": "0547b984f150bb9bbd4dbe25b50825a12c047de70bcb1d86a267abd58a935735"},
    "connected": {"path": str(current.DOC.relative_to(current.ROOT)) + "/bounded-strength-v1/connected-stack-followup-v1/analyze.py",
                  "sha256": "56c84c7fbe06da68ddfe27fe147fff52344cf0cdd0ef72cda489d9163926e82b"},
}


def own_ref():
    canonical_dependency()
    current.require(current.sha(OWN) == LOADED_SHA, "loaded current component adapter changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


def canonical_dependency():
    """Bind loaded and on-disk helper bytes before canonical hashes are used."""
    current.require(saved_force_summary.own_ref() == CANONICAL_HELPER, "exact frozen canonical helper required")
    return dict(CANONICAL_HELPER)


def load(ref, name):
    path = current.ROOT / ref["path"]
    current.require(current.sha(path) == ref["sha256"], "frozen component helper changed")
    spec = importlib.util.spec_from_file_location("eoere_selected_component_" + name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    current.require(current.sha(path) == ref["sha256"], "component helper changed during import")
    return module


def current_axes(field):
    _, _, expected, _, pins = current.current_metadata()
    axes = {row["id"]: row for row in expected}
    observed = {row["axis_id"]: row["source_axis"] for row in field["source_inputs"]["shafts"]}
    current.require(len(axes) == len(observed) == 100 and axes == observed,
                    "exact current selected source axes required")
    return axes, pins


def selected_catalog(facts, selections):
    """Rebind thread-window dimensions to the selected purchase records.

    Washer/nut/body/root/material references keep their existing conditional
    meaning. No old nominal bolt length or minimum smooth body is inherited.
    """
    facts = copy.deepcopy(facts)
    products = {}
    for row in selections.values():
        key = (round(row["selected_diameter_mm"] / 25.4, 8),
               round(row["selected_underhead_length_mm"] / 25.4, 8))
        product = {"diameter_in": key[0], "nominal_length_in": key[1],
                   "Lb_min_in": row["minimum_body_mm"] / 25.4,
                   "sku": row["selected_product"], "url": row["selected_product_url"]}
        current.require(key not in products or products[key] == product,
                        "conflicting selected catalog dimensions")
        current.require(0 <= product["Lb_min_in"] <= key[1], "selected smooth body outside bolt")
        products[key] = product
        dim = next(d for d in facts["diameters"] if round(d["diameter_in"], 8) == key[0])
        current.require(str(dim["washer"]["sku"]) == row["selected_washer_SKU"]
                        and str(dim["nut"]["sku"]) == row["selected_nut_SKU"],
                        "selected nut/washer family differs from conditional references")
    facts["bolts"] = list(products.values())
    facts["current_selected_length_and_minimum_body_basis"] = True
    return facts


def support_screen(field):
    """Necessary undeformed ground-plane statics; no floor capacity adopted."""
    import numpy as np
    from scipy.spatial import ConvexHull

    normal = [r for r in field["floor_actions"] if r["kind"] == "floor_normal"]
    tangent = [r for r in field["floor_actions"] if r["kind"] == "floor_tangent" and r["interaction_enabled"]]
    current.require(len(normal) == 32 and len(tangent) == 4, "current floor support census required")
    current.require(all(abs(r["point_xyz_mm"][2]) < 1e-7 for r in normal + tangent),
                    "ground-plane statics requires all reactions at Z0")
    current.require(all(r["compression_n"] >= 0 for r in normal), "compression-only normals required")
    force = np.zeros(3)
    moment = np.zeros(3)
    for row in field["body_applied_loads"]:
        f = np.asarray(row["force_xyz_n"], dtype=float)
        force += f
        moment += np.cross(row["point_xyz_mm"], f) + np.asarray(row.get("moment_xyz_nmm", [0., 0., 0.]))
    weight = -float(force[2])
    current.require(weight > 0, "positive net downward load required")
    zmp = np.array([moment[1], -moment[0]]) / weight
    points = np.unique(np.asarray([r["point_xyz_mm"][:2] for r in normal]), axis=0)
    hull = ConvexHull(points)
    margins = -(hull.equations[:, :2] @ zmp + hull.equations[:, 2])
    total = sum(r["compression_n"] for r in normal)
    current.require(total > 0, "positive saved floor normal resultant required")
    cop = sum(r["compression_n"] * np.asarray(r["point_xyz_mm"][:2]) for r in normal) / total
    return {"external_force_xyz_n": force.tolist(), "external_moment_about_world_origin_xyz_nmm": moment.tolist(),
            "floor_hull_vertices_xy_mm": points[hull.vertices].tolist(), "required_ground_normal_resultant_xy_mm": zmp.tolist(),
            "minimum_signed_hull_edge_margin_mm": float(min(margins)),
            "necessary_no_tension_ground_plane_screen_pass": bool(min(margins) >= -1e-7),
            "saved_compression_center_xy_mm": cop.tolist(), "required_vs_saved_center_error_mm": float(np.linalg.norm(zmp-cop)),
            "net_normal_balance_error_n": abs(total-weight),
            "global_required_friction_coefficient_lower_bound": float(np.linalg.norm(force[:2])) / weight,
            "horizontal_reactions_only_at_rear_leg_points": [r["id"] for r in tangent],
            "floor_friction_or_contact_pressure_capacity": None, "actual_no_slip_or_overturning_qualified": False,
            "scope": "Necessary global wrench screen on the reference plane; does not prove local friction, yaw equilibrium feasibility, pad pressure, floor capacity or deformed stability."}


def connected_references(field, detailed, methods, pins):
    """Reuse continuous bearing statics on all surfaces of the eight mixed stacks."""
    import numpy as np

    source = FROZEN["connected"]
    pure = methods.pure(source["path"], ["line_bound", "bearing_trial", "known_answers"],
                        {"np": np, "math": math, "parent": SimpleNamespace(require=current.require)})
    shafts = {r["axis_id"]: r for r in field["source_inputs"]["shafts"]}
    ports = {(r["axis_id"], r["surface_index"]): r for key in
             ("common_shaft_wood_bearing_actions", "common_shaft_steel_port_actions") for r in field[key]}
    bearings = {r["id"]: r for r in field["common_shaft_bearing_actions"]}
    captures = {r["id"]: r for r in field["shaft_end_capture_actions"]}
    mixed = [r["axis_id"] for r in detailed["timber"]["shaft_components"] if r["component"] is None]
    current.require(len(mixed) == 8 and pins[source["path"]] == source["sha256"], "eight current mixed stacks required")
    rows = []
    for aid in mixed:
        shaft = shafts[aid]
        for index in range(len(shaft["surfaces"])):
            rows.append({"axis_id": aid, **pure["bearing_trial"](shaft, index, ports[aid, index], bearings, captures)})
    return {"known_answers": pure["known_answers"](), "mixed_axis_ids": mixed, "own_surface_trials": rows,
            "worst_necessary_line_density": max(rows, key=lambda r: r["necessary_directional_peak_line_density_bound_n_mm"]),
            "worst_affine_trial_line_density": max(rows, key=lambda r: r["affine_trial_peak_line_density_n_mm"]),
            "compatible_threaded_contact_or_yield_capacity": None,
            "limits": ["Own simultaneous member force/couple, axial capture support point and raw action replay retained.",
                       "Necessary scalar directional lower bounds and affine equilibrium trials are not deformation-compatible pressure bounds, bearing allowables or complete joint resistance."]}


def washer_worsts(rows, dimensions):
    """Select whole same-case corrected witnesses, preserving original metrics."""
    def maximum(subset, key, scenario="own_max_catalog_axial_Fy_corner"):
        if not subset:
            return None
        row = max(subset, key=lambda r: r[scenario][key])
        return {**{k: row[k] for k in ["capture_id", "axis_id", "end", "host", "receiver_kind", "diameter_mm", "N_n"]},
                "scenario": row[scenario], "value": row[scenario][key]}
    wood = [r for r in rows if r["receiver_kind"] == "wood"]
    fullwood = [r for r in wood if r["own_max_catalog_geometric_mean_corner"][
        "nominal_supported_ring_Fc_perp625psi_mean_reference_index"] is not None]
    return {"all_catalog_axial_Fy_required": maximum(rows, "sampled_axial_only_Fy_required_mpa"),
            "all_nominal_axial_Fy_required": maximum(rows, "sampled_axial_only_Fy_required_mpa", "nominal_own_hardware_geometry"),
            "wood_geometric_ring_mean_conditional": maximum(wood, "raw_ring_Fc_perp625psi_mean_ratio_conditional", "own_max_catalog_geometric_mean_corner"),
            "wood_full_nominal_landing_mean_reference": maximum(fullwood, "nominal_supported_ring_Fc_perp625psi_mean_reference_index", "own_max_catalog_geometric_mean_corner"),
            "by_diameter": {str(d): maximum([r for r in rows if r["diameter_mm"] == d], "sampled_axial_only_Fy_required_mpa")
                            for d in sorted(dimensions)}}


def conditional_finished_land(original):
    """Do not let raw-stock containment qualify current finished washer lands."""
    def land(*args):
        result = original(*args)
        result["own_receiver_service_cut_count"] = None
        result["finished_local_service_cuts_proven_clear"] = False
        result["source_nominal_outer_landing_full"] = False
        result["current_finished_local_land_qualified"] = False
        result["current_finished_land_limit"] = "Raw stock/bore/recess bounds only; complete current local trim was not queried."
        return result
    return land


def spacer_washer_references(report, field, facts, metrics):
    """Eight nut washers receive a nominal spacer ring rather than a head proxy.

    The source spacer bore is smaller than every washer ID. Thus the existing
    annular-load equation uses the washer ID and spacer OD without modification.
    Uniform contact remains a conditional traction scenario, not a pressure bound.
    """
    shafts = {r["axis_id"]: r for r in field["source_inputs"]["shafts"]}
    dimensions = {round(r["diameter_in"] * 25.4, 6): r for r in facts["diameters"]}
    corrected = []
    for row in report["all200_own_end_diagnostics"]:
        shaft = shafts[row["axis_id"]]
        spacers = [r for r in shaft["metal_roles"] if r["kind"] == "spacer"]
        if row["end"] != "nut" or not spacers:
            continue
        current.require(len(spacers) == 1 and shaft["source_axis"]["nut_side_spacer_mm"] == 12.7,
                        "one own selected spacer required")
        washer = dimensions[row["diameter_mm"]]["washer"]
        scenarios = [row["nominal_own_hardware_geometry"], *row["USS_catalog_corners_min_thickness"]]
        current.require(all(s["ID_mm"] >= 10.31875 and s["OD_mm"] >= 19.05 for s in scenarios),
                        "current annular load equation requires spacer/washer overlap")
        surface = next(s for s in shaft["surfaces"] if s["host"] == row["host"]
                       and min(abs(v-next(e["support_s_mm"] for e in shaft["ends"] if e["end"] == "nut"))
                               for v in s["interval_mm"]) < 1e-6)
        def recalculate(scenario, row=row, surface=surface):
            return metrics(row["N_n"], scenario["ID_mm"], scenario["OD_mm"], scenario["t_mm"],
                           19.05 / 2, surface["bore_diameter_mm"], row["receiver_kind"],
                           row["outer_landing_for_max_nominal_or_catalog_OD"], row["grain_axis_abs_cos_to_pressure_normal"])
        row["nominal_own_hardware_geometry"] = recalculate(scenarios[0])
        row["USS_catalog_corners_min_thickness"] = [recalculate(s) for s in scenarios[1:]]
        row["own_max_catalog_axial_Fy_corner"] = max(row["USS_catalog_corners_min_thickness"], key=lambda s: s["sampled_axial_only_Fy_required_mpa"])
        row["own_max_catalog_geometric_mean_corner"] = max(row["USS_catalog_corners_min_thickness"], key=lambda s: s["uniform_supported_ring_mean_mpa_geometric_diagnostic"])
        row["washer_loading_basis"] = "uniform nominal spacer/washer overlap annulus; nut footprint acts on the separate spacer"
        row["spacer_bore_and_od_mm"] = [10.31875, 19.05]
        row["spacer_nominal_axial_mean_stress_mpa"] = row["N_n"] / (math.pi * (19.05**2 - 10.31875**2) / 4)
        row["spacer_strength_nut_contact_or_compatible_pressure_bound"] = None
        row["catalog_washer_sku"] = washer["sku"]
        corrected.append(row["capture_id"])
    expected = {s["axis_id"] + "/nut-capture" for s in shafts.values()
                if any(r["kind"] == "spacer" for r in s["metal_roles"])}
    current.require(len(corrected) == 8 and set(corrected) == expected, "all eight own spacer nut washers required")
    rows = report["all200_own_end_diagnostics"]
    report["worsts"] = washer_worsts(rows, dimensions)
    report["exceeded_reference_diagnostics"] = {
        "catalog_plate_over_unadopted33ksi_Fy_marker": [r["capture_id"] for r in rows if r["own_max_catalog_axial_Fy_corner"]["Fy_33ksi_reference_ratio_unadopted"] > 1],
        "full_nominal_landing_wood_mean_over625psi_reference": [r["capture_id"] for r in rows if (r["own_max_catalog_geometric_mean_corner"]["nominal_supported_ring_Fc_perp625psi_mean_reference_index"] or 0) > 1],
        "conditional_raw_wood_ring_mean_over625psi_reference": [r["capture_id"] for r in rows if (r["own_max_catalog_geometric_mean_corner"]["raw_ring_Fc_perp625psi_mean_ratio_conditional"] or 0) > 1]}
    report["spacer_nut_load_rings_refreshed"] = corrected
    report["limits"].append("Eight nut washer loads use uniform nominal spacer overlap rings; spacer/nut contact, compliance, actual pressure and complete resistance remain unknown.")
    return report


def consume_case(case_id):
    """Authenticate before importing any reducer or reaching its callbacks."""
    own_ref()
    input_ref = current.ref(INPUTS)
    config = current.read(input_ref)
    current.require(config["schema"] == "eoere_current_component_inputs/v1" and config["release"] == current.manifest()["release"],
                    "unreleased current component inputs required")
    summary = current.read(config["current_response"])
    current.require(summary["geometry"] == current.manifest()["references"]["geometry"]
                    and summary["hardware_model"] == current.manifest()["references"]["hardware"]
                    and summary["force_producer"] == current.ref(current.OWN)
                    and summary["extra_grid"] is False and summary["case_sequence"] == SEQUENCE
                    and summary["all_six_saved_field_admissions_pass"] is True
                    and summary["release"] == config["release"] and summary["structural_acceptance"] is False,
                    "exact current OFF response required")
    binding = next(row for row in summary["cases"] if row["case_id"] == case_id)
    pins = current.join({r["path"]: r["sha256"] for r in [own_ref(), canonical_dependency(), input_ref, config["current_response"]]},
                        {r["path"]: r["sha256"] for r in config["methods"].values()})
    current.verify(pins)
    raw = (current.ROOT / binding["field"]["path"]).read_bytes()
    current.require(current.sha(current.ROOT / binding["field"]["path"]) == binding["field"]["sha256"], "exact raw field required")
    receipt = current.read(binding["admission"])
    with current.response_context() as (gate, fixed):
        field, admitted = gate.require_admitted_payload(raw, receipt, admission_sha256=current.LOADED_SHA)
        current.require(field["case_id"] == case_id and field["state_id"] == binding["state_id"], "own current case/state required")
        before = canonical_sha(field)
        pins = current.join(pins, admitted, {r["path"]: r["sha256"] for r in [binding["field"], binding["admission"]]})
        axes, extra = current_axes(field)
        pins = current.join(pins, extra)
        frozen = config["methods"]
        for name, expected in FROZEN.items():
            current.require(frozen[name] == expected, "exact frozen component source required: " + name)
        c, rich, prior_plan = (load(frozen[k], k) for k in ["consumer", "followups", "plan"])
        plan = SimpleNamespace(BASE=prior_plan.BASE, METHODS=prior_plan.METHODS, merge=prior_plan.merge,
            checked_bytes=prior_plan.checked_bytes, indexed=prior_plan.indexed,
            ARTIFACTS={**prior_plan.ARTIFACTS, "geometry": summary["geometry"], "manifest": summary["source_manifest"],
                       "descriptors": field["source_inputs"]["geometry"]["cached_source_export"]})
        with patch.object(c, "FIELD_SCHEMA", current.FIELD_SCHEMA):
            coarse = c._reduce(field, axes, plan, pins, 41)
        scenario = {"leg_mm": 88.9, "width_mm": 88.9, "thickness_mm": 6.35, "factory_hole_mm": 10.}
        # Every receiver with a source service cut remains conditional in the
        # unchanged land method. No old nominal seat proof is transferred.
        composition = {"schema": "eoere_selected_current_washer_composition/v1", "axes": list(axes.values()),
                       "service_cuts": [], "current_finished_cut_inventory_used_for_landing_proof": False,
                       "scenario": scenario,
                       "source_composition": {"axes": summary["hardware_model"], "finished_sources": plan.ARTIFACTS["descriptors"]}}
        original_methods = rich._methods
        original_materials = rich._materials
        _, _, _, selections, selection_pins = current.current_metadata()
        pins = current.join(pins, selection_pins)
        def materials(*args):
            template, facts, roots, material = original_materials(*args)
            return template, selected_catalog(facts, selections), roots, material
        method_cache = []
        def methods(*args):
            result = original_methods(*args)
            land = conditional_finished_land(result.washer["wood_land"])
            original = result.washer["calculate"]
            def corrected(field, geometry, facts, pins, authenticated):
                # Compiled functions share their private exact-source namespace;
                # restore it immediately after the conditional land calculation.
                with patch.dict(original.__globals__, {"wood_land": land}):
                    data = original(field, geometry, facts, pins, authenticated)
                return spacer_washer_references(data, field, facts, result.washer["scenario_metrics"])
            result.washer["calculate"] = corrected
            method_cache.append(result)
            return result
        contract = {"nominal_seat_geometry": {"nominal_wood_seats": 112, "scope": "current end census only; no old support proof transferred",
                    "all_current_finished_wood_lands_qualified": False, "old_actions_or_strength_transferred": False}}
        # Only the unchanged checked-AST reader is reused here. The current
        # genuine admission above remains the sole field-intake authority.
        ast_reader = SimpleNamespace(checked_ast=fixed.checked_ast)
        with patch.object(c, "_load_gate", lambda _: ast_reader), patch.object(rich, "GATE_SHA", current.LOADED_SHA), \
                patch.object(rich, "washer_geometry", lambda *_: composition), patch.object(rich, "_methods", methods), \
                patch.object(rich, "_materials", materials):
            detailed = rich._reduce(field, current.ROOT / binding["field"]["path"], c, plan, pins, contract)
        connected = connected_references(field, detailed, method_cache[0], pins)
        support = support_screen(field)
        detailed["missing_current_inputs"]["finished_sections"] = "Current finished-section stress/shear/fracture/stability and restraint qualification; evaluated targeted geometry is reported separately."
        current.require(canonical_sha(field) == before, "component reducers changed the admitted field")
        current.verify(pins)
        own_ref()
    return {"schema": "eoere_selected_hardware_current_component_case/v1", "case_id": case_id,
            "state_id": field["state_id"], "accessory_placement": field["accessory_placement"],
            "field": binding["field"], "admission": binding["admission"], "geometry": summary["geometry"],
            "hardware_model": summary["hardware_model"], "producer": own_ref(), "source_sha256": pins,
            "component_reductions": coarse, "findings": detailed,
            "connected_mixed_stack_statics": connected, "support_screen": support,
            "source_inputs_canonical_sha256": canonical_sha(field["source_inputs"]),
            "raw_field_canonical_sha256": before,
            "complete_joint_resistance": None, "finished_member_capacity": None,
            "native_or_global_solve_performed": False, "historical_pass_or_actions_transferred": False,
            "release": current.manifest()["release"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", choices=SEQUENCE, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fixed = current.load("bridge")
    with fixed.reserve(args.out) as output:
        output.write(consume_case(args.case_id))
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
