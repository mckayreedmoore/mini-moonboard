"""Source and fabricated-action controls; never consume a genuine force field."""
from __future__ import annotations

import builtins
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
BASE = OWN.parents[2]
TARGET = BASE / "current-component-bridge-v1/followups-v1"
PINS = {
    TARGET / "followups.py": "a27bacf7260905f69c2a69bae60c0f2cf4ed1f4efd229100e3c8fb846b892798",
    TARGET / "test_followups.py": "eec79c2a9f33305f9cccfbec14520806f69a4a46a34efb995e4dc7ab31df912f",
    TARGET / "verification.json": "1390a83569c7885e0006645e1a8fb11814c1751900ebad6f0118daeea454173f",
}
IDENTITY = {"state_id": "independent-synthetic-only", "case_id": "fabricated-actions", "accessory_placement": "synthetic"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path, label):
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[label] = module
    spec.loader.exec_module(module)
    return module


def verify_sources():
    for path, digest in PINS.items():
        assert sha(path) == digest, str(path)


def zero_cut_tables(exported):
    rows = []
    for shaft in exported["shafts"]:
        stations = sorted({v for s in shaft["surfaces"] for v in s["interval_mm"]})
        rows.append({"axis_id": shaft["axis_id"], "body": shaft["body"],
            "elastic_section_diameter_mm": shaft["diameter_mm"],
            "cuts": [{"station_from_axis_point_mm": s,
                      "point_xyz_mm": (np.asarray(shaft["point"]) + s*np.asarray(shaft["basis"][0])).tolist(),
                      "local_N_V1_V2_T_M1_M2_n_nmm": [0.]*6} for s in stations]})
    return rows


def washer_probe(m, methods, exported, geometry, parent, facts, pins, refs):
    field = {**IDENTITY, "source_inputs": {
        "shafts": copy.deepcopy(exported["shafts"]), "timber_rows": copy.deepcopy(exported["raw_gross_timber_rows"]),
        "fitting_poses": copy.deepcopy(exported["fitting_poses"]),
        "all_factory_holes": copy.deepcopy(exported["all_factory_holes"])},
        "fitting_operator_descriptors": [{"body": pose["id"], "own_fitting_scenario": {
            "arm_length_mm": 88.9, "width_mm": 88.9, "thickness_mm": 6.35, "factory_hole_diameter_mm": 10.}}
            for pose in exported["fitting_poses"]], "shaft_end_capture_actions": []}
    expected_N = {}
    for index, shaft in enumerate(field["source_inputs"]["shafts"]):
        for end in shaft["ends"]:
            direction = np.asarray(end["direction_on_shaft_xyz"])
            direction /= np.linalg.norm(direction)
            N = float(10 + index % 5 + (end["end"] == "nut"))
            identity = shaft["axis_id"] + "/synthetic-" + end["end"]
            expected_N[identity] = N
            field["shaft_end_capture_actions"].append({**IDENTITY, "id": identity,
                "axis_id": shaft["axis_id"], "first": shaft["body"], "second": end["host"], "end": copy.deepcopy(end),
                "host_support_point_xyz_mm": (np.asarray(shaft["point"]) + end["support_s_mm"]*np.asarray(shaft["basis"][0])).tolist(),
                "compression_n": N, "force_on_first_xyz_n": (N*direction).tolist(),
                "force_on_second_xyz_n": (-N*direction).tolist(),
                "unilateral_axial_centre_capture_without_rotational_clamp": True,
                "physical_pressure_or_prying_resolved": False,
                "moment_on_first_at_point_xyz_nmm": [0, 0, 0], "moment_on_second_at_point_xyz_nmm": [0, 0, 0]})
    composition = m.washer_geometry(field, geometry, parent, refs)
    before = m.canonical(field)
    result = methods.washer["calculate"](field, composition, facts, pins, {"synthetic_only": True})
    assert m.canonical(field) == before
    assert result["census"]["physical_axes"] == 100 and result["census"]["physical_end_captures"] == 200
    assert result["census"]["head"] == result["census"]["nut"] == 100
    assert result["census"]["receiver_kind"] == {"wood": 112, "steel": 88}
    for row in result["all200_own_end_diagnostics"]:
        assert row["N_n"] == expected_N[row["capture_id"]]
        metrics = row["nominal_own_hardware_geometry"]
        assert metrics["combined_washer_strength_index"] is None and metrics["physical_contact_pressure_bound_mpa"] is None
        assert metrics["physical_pressure_couple_Nmm"] is None
    return {"fabricated_positive_captures": 200, "wood_ends": 112, "steel_ends": 88,
            "exact_own_end_force_preservation": True, "field_not_mutated": True,
            "actual_pressure_product_strength_and_complete_joint_remain_unknown": True}


def timber_and_shaft_probe(methods, exported, template, facts, roots, pins, c):
    source = {"shafts": copy.deepcopy(exported["shafts"]), "timber_rows": copy.deepcopy(exported["raw_gross_timber_rows"]),
              "finished_receiver_wall_queries": copy.deepcopy(exported["finished_receiver_wall_queries"]),
              "fitting_port_bindings": copy.deepcopy(exported["fitting_ports"])}
    field = {**IDENTITY, "source_inputs": source, "common_shaft_bearing_actions": [],
             "shaft_end_capture_actions": [], "common_shaft_wood_bearing_actions": [],
             "common_shaft_section_cut_actions": zero_cut_tables(exported)}
    members = {row["name"]: row for row in source["timber_rows"]}
    for shaft in source["shafts"]:
        for index, surface in enumerate(shaft["surfaces"]):
            if surface["kind"] != "wood":
                continue
            station = sum(surface["interval_mm"])/2
            point = (np.asarray(shaft["point"]) + station*np.asarray(shaft["basis"][0])).tolist()
            own = []
            for sign in (-1, 1):
                identity = shaft["axis_id"] + "/synthetic-wood/" + str(index) + "/" + str(sign)
                own.append(identity)
                force = (sign*np.asarray(members[surface["host"]]["axis"])).tolist()
                field["common_shaft_bearing_actions"].append({**IDENTITY, "id": identity, "axis_id": shaft["axis_id"],
                    "kind": "common_shaft_bearing", "second": surface["host"], "point_xyz_mm": point,
                    "force_on_second_xyz_n": force, "moment_on_second_at_point_xyz_nmm": [0., 0., 0.]})
            field["common_shaft_wood_bearing_actions"].append({**IDENTITY, "axis_id": shaft["axis_id"],
                "host": surface["host"], "surface_index": index, "surface_interval_mm": surface["interval_mm"],
                "point_xyz_mm": point, "force_on_host_xyz_n": [0., 0., 0.],
                "moment_on_host_at_point_xyz_nmm": [0., 0., 0.], "own_bearing_points": own, "own_end_captures": []})
    manifest = {"files": {"field": "synthetic-field-not-on-disk"},
                **{key: template[key] for key in ("Fyb_purchase_design_psi", "generic_steel_Fe_psi", "steel_Fe_primary_basis")},
                "calculation_scope": "Independent synthetic source interface control only"}
    synthetic_pins = {**pins, "synthetic-field-not-on-disk": "0"*64}
    def intake(_):
        return manifest, field, facts, roots, None, synthetic_pins, methods.group, methods.ws, methods.ww, methods.resolved
    original = methods.timber.intake
    before = json.dumps(field, sort_keys=True)
    with c.BOUNDARY_LOCK, patch.object(methods.timber, "intake", intake), \
         patch.object(methods.timber, "verify", return_value=None):
        result = methods.timber.produce(OWN)
    assert methods.timber.intake is original and json.dumps(field, sort_keys=True) == before
    assert result["summary"]["wood_surfaces"] == 120 and result["summary"]["physical_shafts"] == 100
    assert result["summary"]["duties"] == 24 and result["summary"]["supported_component_reference_count"] == 92
    unknown = [row for row in result["shaft_components"] if row["component"] is None]
    assert len(unknown) == 8 and all(row["complete_joint_resistance_n"] is None for row in result["shaft_components"])
    assert not result["same_field_reused_gross_member_witnesses"]
    bolts = methods.bolt({row["axis_id"]: row for row in source["shafts"]}, field, facts, roots, methods.circles)
    assert len(bolts) == len({row["axis_id"] for row in bolts}) == 100
    assert all(row["governing"]["specified_material_first_yield_index"] == 0 for row in bolts)
    return {"fabricated_wood_surface_resultants": 120, "physical_shafts": 100, "duties": 24,
            "two_member_component_references": 92, "mixed_stack_unknowns": 8,
            "all100_shaft_zero_action_references_checked": True, "scoped_timber_intake_restored": True,
            "field_not_mutated": True, "historical_assessment_not_supplied": True,
            "pin_verifier_stubbed_only_for_the_explicit_synthetic_nonfile_key": True}


def steel_probe(methods, scenarios):
    body = "synthetic-angle"
    field = {**IDENTITY, "common_shaft_bearing_actions": [], "shaft_end_capture_actions": [], "contact_actions": [],
        "common_shaft_steel_port_actions": [], "four_port_fitting_actions": [{"body": body,
            "load_projection": {"physical_load_rows": []}}], "source_inputs": {"shafts": []}}
    data = {"fitting_basis_columns_xyz": np.eye(3).tolist(), "heel_reference_xyz_mm": [0., 0., 0.],
            "width_mm": 88.9, "arm_length_mm": 88.9, "thickness_mm": 6.35, "near_station_mm": 23.8125,
            "far_station_mm": 65.0875, "transverse_half_pitch_mm": 25.4, "factory_hole_diameter_mm": 10.,
            "flange_axes_local": {"beam": [1., 0., 0.], "post": [0., 0., 1.]},
            "elastic_modulus_mpa": 200000., "poisson_ratio": .3, "port_order": []}
    descriptor = {"body": body, "own_fitting_scenario": data, "ports": []}
    for flange, along in data["flange_axes_local"].items():
        axes = methods.core.flange_basis(along)
        normal = float(axes[:, 2] @ np.array([3.175, 0., 3.175]))
        for sign, side in ((-1, "minus"), (1, "plus")):
            port = flange + "/" + side
            data["port_order"].append(port)
            descriptor["ports"].append({"id": port, "flange": flange,
                "strip_root_xyz_mm": (axes @ [0., sign*88.9/4, normal]).tolist()})
            own = []
            for index, station in enumerate((45., 65.)):
                identity = port + "/bearing/" + str(index)
                own.append(identity)
                field["common_shaft_bearing_actions"].append({**IDENTITY, "id": identity, "host": body, "flange": port,
                    "point_xyz_mm": (axes @ [station, sign*25.4, normal]).tolist(),
                    "force_on_second_xyz_n": (np.asarray(along)*(100 if index == 0 else -100)).tolist(),
                    "moment_on_second_at_point_xyz_nmm": [0., 0., 0.]})
            cap = {**IDENTITY, "id": port+"/capture", "second": body, "end": {"flange": port},
                "point_xyz_mm": (axes @ [65., sign*25.4, normal]).tolist(), "force_on_second_xyz_n": [0., 0., 0.],
                "moment_on_second_at_point_xyz_nmm": [0., 0., 0.]}
            field["shaft_end_capture_actions"].append(cap)
            for index, station in enumerate((10., 30., 50., 70.)):
                field["contact_actions"].append({**IDENTITY, "id": port+"/contact/"+str(index), "first": body,
                    "kind": "flange_contact", "flange": port, "point_xyz_mm": (axes @ [station, sign*25.4, normal]).tolist(),
                    "force_on_first_xyz_n": [0., 0., 0.], "moment_at_point_model_xyz_nmm": [0., 0., 0.], "compression_n": 0.})
            field["common_shaft_steel_port_actions"].append({"angle_id": body, "axis_id": port, "flange": port,
                "own_bearing_points": own, "own_end_captures": [cap["id"]], "point_xyz_mm": cap["point_xyz_mm"],
                "force_on_steel_xyz_n": [0., 0., 0.], "moment_on_steel_at_point_xyz_nmm": [0., 0., 0.]})
            field["source_inputs"]["shafts"].append({"axis_id": port, "diameter_mm": 6.35})
    before = json.dumps(field, sort_keys=True)
    outputs = [methods.steel["reduce_angle"](field, descriptor, methods.net, scenario) for scenario in scenarios]
    assert json.dumps(field, sort_keys=True) == before
    for output in outputs:
        assert len(output["bands"]) == 4 and output["integrity"]["point_loads_retained"] == 28
        assert output["integrity"]["own_aggregate_max_error_n_nmm"] < 1e-10
        assert output["complete_joint_resistance_accepted"] is False
        assert methods.steel["summary"]([output])["physical_cut_nominal_combined"]["comparison_count"] == 4
    return {"synthetic_steel_owners": 1, "complete_scalar_scenarios_exercised": [s["id"] for s in scenarios],
            "retained_physical_point_loads_each_scenario": 28, "own_bands_each_scenario": 4,
            "field_not_mutated": True, "complete_joint_not_accepted": True}


def check():
    verify_sources()
    original_import = builtins.__import__
    blocked = []
    def guarded_import(name, *args, **kwargs):
        if name.split(".")[0] in {"cadquery", "OCP"}:
            blocked.append(name)
            raise AssertionError("CAD library import forbidden: " + name)
        return original_import(name, *args, **kwargs)
    with patch.object(builtins, "__import__", guarded_import), \
         patch.object(np, "load", side_effect=AssertionError("saved operator arrays forbidden")) as array_guard:
        m = load(TARGET / "followups.py", "independent_followup_correctness")
        c = m._consumer()
        plan = c._load_plan()
        contract = plan.component_plan()
        pins = dict(contract["source_sha256"])
        template, facts, roots, evidence = m._materials(c, plan, pins)
        methods = m._methods(c, plan, pins)
        exported = json.loads(plan.checked_bytes(plan.ARTIFACTS["descriptors"]))
        geometry = json.loads(plan.checked_bytes(plan.ARTIFACTS["geometry"]))
        parent = json.loads(plan.checked_bytes(plan.ARTIFACTS["parent_geometry"]))
        steel = steel_probe(methods, m.STEEL_SCENARIOS)
        washers = washer_probe(m, methods, exported, geometry, parent, facts, pins, plan.ARTIFACTS)
        timber = timber_and_shaft_probe(methods, exported, template, facts, roots, pins, c)
        c.verify(pins)
        recorded = json.loads((TARGET / "verification.json").read_bytes())["reused_source_closure"]
        assert m.canonical(contract["source_sha256"]) == recorded["frozen_plan_sources_canonical_sha256"]
        assert m.canonical(pins) == recorded["current_plus_followup_sources_canonical_sha256"]
        assert array_guard.call_count == 0 and not blocked
    verify_sources()
    return {"schema": "independent_current_component_followup_correctness_review/v1", "passed": True,
        "review_program_sha256": sha(OWN), "source_sha256": {str(p.relative_to(ROOT)): s for p, s in PINS.items()},
        "synthetic_steel": steel, "synthetic_washers": washers, "synthetic_timber_and_shafts": timber,
        "source_only_contract_pin_count": len(contract["source_sha256"]), "verified_source_pin_count": len(pins),
        "source_pin_union_matches_frozen_verification": True,
        "material_maps_remain_historical": all(not r["historical_field_or_viewer_map_imported_as_current"] for r in evidence["root_evidence_maps"]),
        "genuine_force_fields_consumed": 0, "saved_operator_array_load_calls": 0, "CAD_import_attempts": blocked,
        "K_native_frame_browser_executed": False, "substantial_confirmed_findings": [],
        "limits": ["Fabricated actions are controls only; no current six-case findings are admitted by this review.",
                   "Full current extraction and mechanics/release boundaries retain their separate authority."]}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2, sort_keys=True, allow_nan=False))
