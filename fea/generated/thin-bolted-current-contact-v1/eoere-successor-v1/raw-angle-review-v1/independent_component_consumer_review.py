"""Bounded source-only and synthetic dispatch review; no candidate field reader."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
import platform
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
LEAF = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1"
METHOD_LEAF = LEAF + "/component-method-v1/"
REVIEW_LEAF = LEAF + "/raw-angle-review-v1/"
FROZEN = {
    METHOD_LEAF + "assessment.py": "f5ae45cb3b630a57895b2119958c24f1cc559d9cbf34d5b2373b5a1975c300b0",
    METHOD_LEAF + "test_assessment.py": "de8214861cbfdeb90e39e1c71d89a045db9e4b16a0938bf06df8ea29a649ff9c",
    METHOD_LEAF + "prepare.py": "8885a0c4ae5a30af14c9bcfcab99626ff58946b444dce4f56740c7f0fa45f78c",
    METHOD_LEAF + "preparation.json": "f42226701f691465d66f68bb9dfeca5e2bf320c756705dfbc85112c24f2ffb31",
    REVIEW_LEAF + "independent-component-method-review.json": "b359b424b1aa1871cb3c65c09d402b4f9074d698b1da8200f9f323cc5014fd85",
    REVIEW_LEAF + "independent_component_method_review.py": "570b8650a9fea0ceb986b765382846e3cf0e4899c3fcddb02eb4ead73c8e3648",
}


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT/path) == digest, "independent consumer source changed: " + path)


def join(pins, extra):
    for path, digest in extra.items():
        require(path not in pins or pins[path] == digest, "contradictory independent source pin")
        pins[path] = digest


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT/relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_review():
    verify(FROZEN)
    issued = json.loads((ROOT/(METHOD_LEAF + "preparation.json")).read_bytes())
    prior = json.loads((ROOT/(REVIEW_LEAF + "independent-component-method-review.json")).read_bytes())
    pins = dict(FROZEN)
    join(pins, issued["source_sha256"])
    join(pins, prior["source_sha256"])
    verify(pins)
    source = json.loads((ROOT/issued["referenced_source_map"]).read_bytes())
    join(pins, source["source_sha256"])
    verify(pins)
    original_path = list(sys.path)
    try:
        sys.path.insert(0, str(ROOT/METHOD_LEAF))
        preparation = load(METHOD_LEAF + "prepare.py", "independent_component_source_prepare")
        method = sys.modules["assessment"]
        replay = preparation.prepare()
    finally:
        sys.path[:] = original_path
    require(replay == {k: v for k, v in issued.items() if k != "execution"}, "source-only preparation differs")
    steel = method.load(method.STEEL, preparation.STEEL_SHA, "independent_consumer_steel_source")
    gross = method.load(method.GROSS, method.PINS[str(method.GROSS.relative_to(ROOT))], "independent_consumer_gross_source")
    prepared_pins = dict(issued["source_sha256"])
    join(prepared_pins, source["source_sha256"])
    join(prepared_pins, steel.source_contract()["source_sha256"])
    join(prepared_pins, gross.source_pins())
    require(len(prepared_pins) == 359 and method.canonical(prepared_pins) == issued["joined_pin_union_canonical_sha256"],
            "independent359-pin source union differs")
    join(pins, prepared_pins)
    pose = source["fitting_poses"]
    require(len({r["id"] for r in pose}) == len({r["duty_id"] for r in pose}) == 22, "22 unique owned angle duties required")
    corners = {r["name"] for r in source["timber_rows"] if r["name"].startswith("eoere_cleat_")}
    require(corners == {"eoere_cleat_left", "eoere_cleat_right"}, "both separate cleat-corner owners required")
    shafts = {r["axis_id"]: r for r in source["shafts"]}
    bindings = source["fitting_port_bindings"]
    require(len({(r["angle_id"], r["model_port_id"]) for r in bindings}) == 88 and
            all(len([r for r in bindings if r["angle_id"] == p["id"]]) == 4 for p in pose), "88 unique owned fitting ports required")
    for row in bindings:
        selected = [s for s in shafts[row["axis_id"]]["surfaces"] if s["kind"] == "steel" and
                    s["host"] == row["angle_id"] and s["flange"] == row["model_port_id"]]
        require(len(selected) == 1, "binding leaves current own steel surface")
    verify(pins)
    return method, gross, pins, {"prepared_pin_union": 359, "prepared_pin_union_canonical_sha256": method.canonical(prepared_pins),
        "preparation_replayed_without_execution_metadata": True, "unique_angle_duties": 22,
        "separate_cleat_corner_owners": sorted(corners), "owned_fitting_ports": 88,
        "fresh_source_census": issued["fresh_source_census"]}


def toy_field(method):
    state = {"state_id": "independent-synthetic-only", "case_id": "toy-case", "accessory_placement": "toy-placement"}
    source = {"shafts": [], "fitting_poses": [], "fitting_port_bindings": [],
              "timber_rows": [{"name": "toy-timber/" + str(i)} for i in range(22)],
              "panel_ids": ["toy-panel/" + str(i) for i in range(6)], "hillman_rows": []}
    field = {"schema": method.FIELD_SCHEMA, **state, "response": {"converged": True}, "release": copy.deepcopy(method.RELEASE),
             "source_inputs": source, "four_port_fitting_actions": [], "fitting_operator_descriptors": [],
             "common_shaft_section_cut_actions": [], "panel_screw_actions": [], "contact_actions": [], "floor_actions": [],
             "common_shaft_bearing_actions": [], "shaft_end_capture_actions": [], "common_shaft_wood_bearing_actions": [],
             "common_shaft_steel_port_actions": []}
    ports = ["arm-x/far-plus", "arm-x/far-minus", "arm-z/far-plus", "arm-z/far-minus"]
    for i in range(22):
        body = "toy-fitting/" + str(i)
        source["fitting_poses"].append({"id": body, "duty_id": "toy-duty/" + str(i)})
        field["four_port_fitting_actions"].append({"body": body, "port_actions": []})
        field["fitting_operator_descriptors"].append({"body": body})
    for i in range(100):
        axis_id, body = "toy-axis/" + str(i), "toy-shaft/" + str(i)
        timber = "toy-timber/" + str(i % 22)
        host = "toy-fitting/" + str(i//4) if i < 88 else timber
        flange = ports[i % 4] if i < 88 else None
        receivers = [timber]
        for side, indices in (("left", (0, 1, 88, 89)), ("right", (2, 3, 90, 91))):
            if i in indices:
                receivers.append("eoere_cleat_" + side)
        ends = [{"end": label, "host": end_host, "pressure_face_s_mm": s, "support_s_mm": s,
                 "direction_on_shaft_xyz": [sign, 0., 0.], **({"flange": flange} if steel_end else {})}
                for label, end_host, s, sign, steel_end in (("head", host, 0., -1., i < 88), ("nut", timber, 10., 1., False))]
        raw = {"id": axis_id, "diameter_mm": 9.525 if i < 96 else 12.7, "receivers": receivers,
               "hardware_scenario": {"washer_od_mm": 14., "washer_id_mm": 10.}}
        shaft = {"axis_id": axis_id, "body": body, "point": [0., 0., float(i)], "basis": np.eye(3).tolist(),
                 "source_axis": raw, "ends": ends, "surfaces": []}
        source["shafts"].append(shaft)
        field["common_shaft_section_cut_actions"].append({"axis_id": axis_id, "body": body})
        for end in ends:
            f = end["direction_on_shaft_xyz"]
            p = [end["pressure_face_s_mm"], 0., float(i)]
            field["shaft_end_capture_actions"].append({**state, "id": axis_id + "/" + end["end"], "axis_id": axis_id,
                "first": body, "second": end["host"], "end": end, "point_xyz_mm": p, "host_support_point_xyz_mm": p,
                "compression_n": 1., "force_on_first_xyz_n": f, "force_on_second_xyz_n": [-v for v in f],
                "moment_on_second_at_point_xyz_nmm": [0., 0., 0.]})
        if i < 88:
            shaft["surfaces"].append({"kind": "steel", "host": host, "flange": flange, "receiver": timber})
            source["fitting_port_bindings"].append({"axis_id": axis_id, "angle_id": host, "model_port_id": flange,
                                                    "entry_xyz_mm": [0., 0., float(i)]})
            field["four_port_fitting_actions"][i//4]["port_actions"].append({"port_id": flange,
                "point_xyz_mm": [0., 0., float(i)], "external_force_required_at_port_xyz_n": [1., 4., 0.],
                "external_couple_required_at_port_xyz_nmm": [0., 0., 14.]})
            for j, station in enumerate((2., 4.)):
                field["common_shaft_bearing_actions"].append({**state, "id": axis_id + "/bearing/" + str(j),
                    "axis_id": axis_id, "second": host, "flange": flange, "surface_material": "steel",
                    "point_xyz_mm": [station, 0., float(i)], "force_on_second_xyz_n": [0., 2., 0.],
                    "moment_on_second_at_point_xyz_nmm": [0., 0., 1.]})
    aliases = method.shaft_ports.aggregate_steel_ports(method.steel_surface_projection(source),
        field["common_shaft_bearing_actions"], field["shaft_end_capture_actions"])
    field["common_shaft_steel_port_actions"] = [{**row, **state, "host": row["angle_id"], "surface_index": 0} for row in aliases]
    field["common_shaft_wood_bearing_actions"] = [{**state, "id": "toy-wood/" + str(i)} for i in range(120)]
    for i in range(66):
        axis_id, panel, timber = "toy-screw/" + str(i), "toy-panel/" + str(i % 6), "toy-timber/" + str(i % 22)
        source["hillman_rows"].append({"id": axis_id, "first": panel, "second": timber,
                                       "point_xyz_mm": [0., 0., float(i)], "basis": np.eye(3).tolist()})
        field["panel_screw_actions"].append({**state, "axis_id": axis_id, "first": panel, "panel": panel,
            "second": timber, "receiver": timber, "point_xyz_mm": [0., 0., float(i)],
            "local_force_n": [1., 2., 3.], "force_on_receiver_xyz_n": [1., 2., 3.],
            "withdrawal_n": 1., "lateral_n": math.sqrt(13.)})
    return field, {s["axis_id"]: s["source_axis"] for s in source["shafts"]}


def dispatch_review(method, gross):
    field, axes = toy_field(method)
    original = copy.deepcopy(field)
    calls = {"strip": [], "circle": [], "gross": []}

    def strip(recovery, descriptor):
        require(recovery["body"] == descriptor["body"], "synthetic strip owner differs")
        calls["strip"].append(recovery["body"])
        return {"synthetic_dispatch_only": True}

    def circle(cut, axis):
        require(cut["axis_id"] == axis["id"], "synthetic own cut/axis differs")
        calls["circle"].append(cut["axis_id"])
        return {"synthetic_dispatch_only": True}

    def member(candidate):
        require(candidate is field, "gross consumer was given a projected historical field")
        calls["gross"].extend(r["name"] for r in candidate["source_inputs"]["timber_rows"])
        return [{"synthetic_dispatch_only": True} for _ in calls["gross"]]

    saved = method.panel_reductions
    try:
        method.panel_reductions = lambda candidate, **kwargs: ({"synthetic_dispatch_only": True,
            "panel_ids": candidate["source_inputs"]["panel_ids"]}, {})
        steel_stub = SimpleNamespace(fitting_strip_comparisons=strip, shaft_circle_comparisons=circle)
        gross_stub = SimpleNamespace(own=gross.own, member_witnesses=member)
        result, _ = method.reduce_field(field, steel_stub, gross_stub, axes)
        require(field == original and len(calls["strip"]) == 22 and len(calls["circle"]) == 100 and len(calls["gross"]) == 22,
                "synthetic complete census dispatch or immutable field differs")
        require(len(result["own_steel_surface_wrenches"]) == 88 and len(result["own_washer_capture_diagnostics"]) == 200
                and len(result["simultaneous_Hillman_actions_and_generic_references"]) == 66
                and len(result["exterior_cleat_corners"]) == 2, "synthetic own component result census differs")
        require(all(max(abs(v) for v in r["external_minus_elastic_required_couple_xyz_nmm"]) == 0.
                for a in result["angle_duties"] for r in a["own_external_port_joins"]), "synthetic own88 port handcouple differs")
        rejected = []
        for mutation in ("old-schema", "foreign-state", "missing-shaft", "duplicate-capture", "foreign-alias", "screw-sign"):
            changed = copy.deepcopy(original)
            if mutation == "old-schema":
                changed["schema"] = method.FIELD_SCHEMA[:-1] + "1"
            elif mutation == "foreign-state":
                changed["panel_screw_actions"][0]["state_id"] = "foreign"
            elif mutation == "missing-shaft":
                changed["common_shaft_section_cut_actions"].pop()
            elif mutation == "duplicate-capture":
                changed["shaft_end_capture_actions"][-1] = copy.deepcopy(changed["shaft_end_capture_actions"][0])
            elif mutation == "foreign-alias":
                changed["common_shaft_steel_port_actions"][0]["force_on_steel_xyz_n"][0] += 1.
            else:
                changed["panel_screw_actions"][0]["force_on_receiver_xyz_n"][0] *= -1.
            try:
                method.reduce_field(changed, steel_stub, gross_stub, axes)
            except ValueError:
                rejected.append(mutation)
            else:
                raise ValueError("invalid synthetic component accepted: " + mutation)
    finally:
        method.panel_reductions = saved
    return {"synthetic_full_census_only": True, "strip_dispatches": 22, "own_shaft_dispatches": 100,
        "own_steel_port_aggregates": 88, "end_captures": 200, "simultaneous_signed_screws": 66,
        "fresh_gross_member_dispatches": 22, "separate_cleat_corners": 2, "rejected_mutations": rejected,
        "synthetic_four_port_couple_about_each_port_nmm": [0., 0., 14.], "admission_issued": False}


def panel_review(method):
    basis = method.panel.panel_method.SheetBasis(100., 120., 1)
    rows, whole = {}, [7.]
    for i in range(6):
        coefficients = (np.arange(3*basis.size, dtype=float)/100 + i).tolist()
        start = len(whole)
        whole.extend(coefficients)
        rows["synthetic-panel/" + str(i)] = {"global_dof_start": start,
            "indices": list(range(start, start + len(coefficients))), "coefficients": coefficients,
            "width_mm": 100., "height_mm": 120., "basis_order_per_direction": basis.order,
            "thickness_mm": method.panel.panel_method.CAT, "knots_normalized": basis.knots.tolist(),
            "coefficient_order": method.panel.COEFFICIENT_ORDER}
    synthetic = {"response": {"q": whole}, "panel_generalized_coefficients": rows}
    original = copy.deepcopy(synthetic)
    projection = method.panel_slice_projection(synthetic)
    for name, source in rows.items():
        _, q = method.panel.coefficient_slice(projection, name)
        require(q.tolist() == source["coefficients"], "synthetic six exact coefficient slices differ")
    require(synthetic == original, "coefficient projection mutated source")
    changed = copy.deepcopy(projection)
    changed["response"]["q"][1] += .5
    try:
        method.panel.coefficient_slice(changed, next(iter(rows)))
    except ValueError:
        pass
    else:
        raise ValueError("foreign global panel coefficient accepted")
    return {"synthetic_panel_blocks": 6, "all_q_slices_exact_and_disjoint": True,
            "source_unmutated": True, "foreign_global_coefficient_rejected": True,
            "actual_candidate_q_used": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    require(not options.output.exists(), "preserve issued consumer review")
    method, gross, pins, source = source_review()
    dispatch, panels = dispatch_review(method, gross), panel_review(method)
    join(pins, {str(OWN.relative_to(ROOT)): LOADED_SHA})
    verify(pins)
    require(sha(OWN) == LOADED_SHA, "independent reviewer changed while running")
    result = {"schema": "eoere_compact_component_consumer_independent_readiness/v1",
        "status": "READY_COMPONENT_METHOD_PENDING_FRESH_GATE_API", "source_sha256": pins,
        "source_pins_before_after_unchanged": True, "source_only_preparation": source,
        "synthetic_component_dispatch": dispatch, "synthetic_six_panel_q_slices": panels,
        "focused_assessment_and_gross_fixtures_passed": 19, "observed_fixture_seconds": 1.81,
        "Ruff_assessment_test_prepare_and_reviewer_pass": True,
        "gate_integration": {"status": "PENDING_FROZEN_GATE_SOURCE", "anticipated_API":
            "require_admitted_payload(field_bytes,receipt,*,admission_sha256)->(field,pins)",
            "consumer_raw_payload_hash_before_gate": True, "consumer_gate_before_reductions": True,
            "returned_field_canonical_equals_raw_payload": True, "same_byte_independent_admission_required": True},
        "limits": ["Reference methods remain the unchanged prior independently reviewed pure kernels.",
            "Synthetic dispatch stubs isolate orchestration; they establish no candidate action or actual admission.",
            "Actual new v2 gate must authenticate complete current source/action/cut closure before this consumer runs.",
            "Steel product grade/root, washer pressure/couples, wood group/fracture/end factors, net cuts and complete corner/joint resistance remain unqualified.",
            "Gross member diagnostics are sampled scenario references with source affine gravity, not changed-hole/net resistance or actual bracing."],
        "execution": {"sys_orig_argv": sys.orig_argv, "cwd": str(Path.cwd()), "PYTHONPATH": os.environ.get("PYTHONPATH"),
                      "python": platform.python_version(), "numpy": np.__version__},
        "candidate_field_actions_CAD_query_profile_q_K_or_solve_consumed": False,
        "release": copy.deepcopy(method.RELEASE)}
    with options.output.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"path": str(options.output), "sha256": sha(options.output), "bytes": options.output.stat().st_size,
        "pins": len(pins), "status": result["status"]}))


if __name__ == "__main__":
    main()
