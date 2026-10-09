"""Final Z180 readiness DATA audit and one trapped genuine read_method call.

Dependency definitions may import. No candidate, panel preparation, operator,
K, q, force, field, admission, CAD/BREP query, native or browser work is run.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
E = OWN.parents[2]
ROOT = E.parents[6]
METHOD = E/"readiness-v1/method-input.json"
METHOD_SHA = "2549e962a5feac6617e27e8f324b6b7b576beb0683289c5dcfd1ee4b5d588654"
GATE = E/"review-fix-v2/bridge.py"
GATE_SHA = "dc224c51a46f78433df614ce53b76e2a8f4b1a7ac4c436b7d0d212f784388f55"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
ABSOLUTE = {
    "/home/mckay-linux/repos/mini-moonboard-cleanup-backups-2026-10-08/eoere-aligned-wire-cutouts-v1.tar.gz.manifest.json":
        "688acf55c2884086ff14352d6d5ac6377b8f6bcebeb29c0e8275e4ffcdf3a15c",
    "/home/mckay-linux/repos/mini-moonboard/scripts/eoere_2026_adjustments.py":
        "136d7e63f1e337ef8a65421d22d4614b336697cb1b8556ff099995fe26a92821",
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def name(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def read(ref):
    path = ROOT/ref["path"]
    require(sha(path) == ref["sha256"], "exact referenced bytes changed: "+ref["path"])
    return json.loads(path.read_bytes())


def verify(pins):
    for text, expected in pins.items():
        path = Path(text)
        if path.is_absolute():
            require(ABSOLUTE.get(text) == expected, "foreign absolute source reference")
        else:
            path = (ROOT/path).resolve()
            require(path.is_relative_to(ROOT), "source path escaped repository")
        require(sha(path) == expected, "readiness source pin differs: "+text)


def main():
    require(sha(METHOD) == METHOD_SHA and METHOD.stat().st_size == 185954, "exact final readiness data required")
    require(sha(GATE) == GATE_SHA, "exact final corrected metadata gate required")
    method = json.loads(METHOD.read_bytes())
    require(len(method["source_sha256"]) == 1171, "exact1171 readiness source closure required")
    pins = dict(method["source_sha256"])
    pins[name(METHOD)] = METHOD_SHA
    pins[name(GATE)] = GATE_SHA
    verify(pins)
    data = read(method["input"])
    review = read(method["input_review"])
    process = read(method["independent_input_review_process"])
    descriptor_review = read(method["descriptor_review"])
    descriptor = read(method["source_export"])
    old_method = read(method["reused_unchanged_numerical_method_record"])
    parent = read(old_method["input"])
    authority = read(method["source_manifest"])
    geometry = read(method["geometry"])
    require(method["schema"] == "eoere_z180_fixed_floor_method_inputs/v1"
            and method["geometry"] == data["geometry"]["report"] == descriptor["geometry"]
            and method["source_manifest"] == data["geometry"]["source_manifest"] == descriptor["manifest"]
            and method["source_export"] == data["geometry"]["cached_source_export"], "own exact proposal reference join differs")
    require(review["schema"] == "eoere_z180_mechanics_inputs_independent_review/v1"
            and review["success"] == "independent_z180_source_input_checks_pass"
            and review["actual_saved_input_review_performed"] is True and review["findings"] == []
            and review["input"] == method["input"] and review["saved_descriptor_review"] == method["descriptor_review"]
            and review["complete_reference_contact_inventory"] is True
            and review["inputs_canonical_sha256"] == method["source_input_canonical_sha256"] == canonical(data),
            "readiness requires authentic completed own raw-input review")
    require(process["exit_code"] == 0 and process["output_sha256"] == method["input_review"]["sha256"]
            and process["mechanics_operator_force_execution_authorized_or_performed"] is False
            and process["source_drift"] == [] and "--run" in process["command"]
            and method["input"]["sha256"] in process["command"]
            and method["descriptor_review"]["sha256"] in process["command"], "actual independent input-review process differs")
    require(descriptor_review["success"] == "independent_z180_descriptor_source_checks_pass"
            and descriptor_review["descriptor"] == method["source_export"] and descriptor_review["findings"] == [],
            "exact completed final descriptor review required")
    source_reviews = {}
    for key, ref in method["independent_reviews"].items():
        own = read(ref)
        require(own["findings"] == [], "unclean source review: "+key)
        require(method["source_sha256"].get(ref["path"]) == ref["sha256"], "source review absent from readiness closure")
        if key.startswith("descriptor_"):
            require(own["schema"] == "eoere_z180_geometry_descriptors_independent_review/v1"
                    and own["descriptor"] == method["source_export"]
                    and (own.get("success") == "independent_z180_descriptor_source_checks_pass"
                         or own.get("independent_z180_descriptor_source_checks_pass") is True), "final descriptor source review differs")
        else:
            targets = own.get("reviewed_sha256", own.get("frozen_target_sha256", own.get("four_corrected_target_sha256_before_after")))
            require(targets.get(name(GATE), targets.get("bridge.py")) == GATE_SHA,
                    "execution source review does not bind corrected gate")
        source_reviews[key] = {"schema":own["schema"], "findings":[]}
    require(set(source_reviews) == {prefix+kind for prefix in ("descriptor_", "execution_")
                                  for kind in ("correctness", "testing", "structure")}, "six final independent source reviews required")
    require(method["descriptor_review"] == method["independent_reviews"]["descriptor_correctness"], "selected own review differs")
    analysis_flags = ["method_checks_pass", "independent_readiness_pass", "parent_execution_bridge_readiness_pass",
                      "unchanged_panel_reuse_independently_reviewed"]
    require(all(method[k] is True for k in analysis_flags), "analysis readiness not complete")
    require(method["case_ids"] == CASES and [c["case_id"] for c in data["cases"]] == CASES+["gravity-only"]
            and set(review["selected_case_canonical_sha256"]) == set(CASES+["gravity-only"]), "six-run/seven-load roster differs")
    load_checks = review["checks"]["independent_permanent_live_loads_and_seven_wrenches"]
    require([r["case_id"] for r in load_checks] == CASES+["gravity-only"]
            and all(r["load_owner_count"] == 150 and r["load_count"] == len(c["loads"])
                    for r,c in zip(load_checks,data["cases"],strict=True)),
            "saved seven-load review census differs")
    require(method["support_contract"] == old_method["support_contract"]
            and data["floor_footprints"] == parent["floor_footprints"]
            and sum(len(v) for v in data["floor_footprints"].values()) == 32
            and data["parameters"] == parent["parameters"] and data["scenario"] == parent["scenario"],
            "recorded support/material/joint priors changed")
    require(method["panel_bank"] == authority["unchanged_panel_method"] == old_method["panel_bank"]
            and data["panel_operator_source_inputs"] == parent["panel_operator_source_inputs"]
            and data["panel_operator_source_inputs"]["geometry"] == old_method["geometry"]
            and method["geometry"] != old_method["geometry"], "original panel identity must remain distinct from proposal")
    require(all(method[k] is False for k in ("geometry_or_hardware_adopted", "nut_spacer_proposal_included", "optional_2026_extra",
            "native_FEA_or_physical_work_authorized_by_this_record", "candidate_response_or_resistance_established_by_this_record"))
            and data["nut_spacer_proposal_included"] is False and data["unadopted_proposal"] is True
            and data["historical_q"] is data["old_field"] is None
            and all(a["nominal_under_head_length_mm"] == 101.6 for a in geometry["proposed_axes"])
            and not any(geometry["release"].values()), "hardware/adoption/response boundary differs")
    require(method["release"] == data["release"] == review["release"] == old_method["release"]
            and not any(method["release"].values()) and not any(descriptor["release"].values())
            and old_method["candidate_response_or_resistance_established_by_this_record"] is False,
            "all physical releases must remain false and old readiness must not transfer response/capacity")
    require(all(method["source_sha256"].get(p) == h for p,h in data["source_sha256"].items()), "readiness omits raw-input source closure")
    # The following is the one authorized genuine metadata read_method call.
    # Imports instantiate definitions only; no operator/preparation is allowed.
    sys.path.insert(0,str(ROOT))
    spec = importlib.util.spec_from_file_location("z180_readiness_independent_corrected_gate", GATE)
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    a = c.original()
    w = a.production()
    b = w.frozen()
    callbacks = []
    def trapped(*_args, **_kwargs):
        callbacks.append("candidate/bank/preparation callback")
        raise AssertionError("forbidden candidate/bank/preparation callback reached")
    panel_view, panel_proof = a.panel_view(data, data["panel_operator_source_inputs"])
    require(panel_proof == review["checks"]["authentic_original_panel_geometry_proof"]
            and panel_view["geometry"]["report"] == old_method["geometry"]
            and canonical(data) == method["source_input_canonical_sha256"], "authentic saved panel proof differs or mutated raw input")
    require(b.law.contract() == method["support_contract"], "genuine frozen support definition differs")
    with c.corrected_context(a), a.context(w,b), ExitStack() as stack:
        for obj, attribute in ((a,"methods"),(b,"methods"),(b,"load"),(b.factory,"prepare"),(b.factory,"_prepare"),
                               (a.PanelProxy,"source_inputs"),(a.PanelProxy,"verify_panel_source_inputs"),(a.PanelProxy,"load_panel_dependencies")):
            stack.enter_context(patch.object(obj,attribute,trapped))
        result = b.read_method(METHOD,METHOD_SHA)
    require(result == {**method,"input_record":{"path":name(METHOD),"sha256":METHOD_SHA}}
            and callbacks == [], "genuine metadata gate result differs or reached candidate callbacks")
    verify(pins)
    pins[name(OWN)] = sha(OWN)
    receipt = {"schema":"eoere_z180_method_readiness_independent_data_review/v1",
        "success":"independent_z180_method_readiness_data_checks_pass", "findings":[],
        "method_input":{"path":name(METHOD),"sha256":METHOD_SHA}, "input":method["input"],
        "input_review":method["input_review"], "descriptor_review":method["descriptor_review"],
        "genuine_metadata_gate":{"path":name(GATE),"sha256":GATE_SHA},
        "checks":{"all1171_readiness_source_pins_before_after_unchanged":True,
            "six_clean_exact_final_source_reviews_and_actual_own_input_review":True,
            "four_true_analysis_readiness_flags_backed_by_completed_reviews":analysis_flags,
            "seven_load_recipes_and_six_loaded_run_cases":True,
            "original_support_material_joint_priors_and_all32_floor_points_unchanged":True,
            "authentic_original_panel_identity_and_saved_unchanged_six_panel_proof":True,
            "one_genuine_corrected_read_method_passed_with_zero_trapped_callbacks":True,
            "no_geometry_hardware_adoption_spacer_old_response_or_capacity_transfer":True},
        "case_ids":CASES,"saved_load_case_ids":CASES+["gravity-only"],"source_reviews":source_reviews,
        "source_sha256":dict(sorted(pins.items())), "status":"PASS_DATA_READINESS_METADATA_GATE_ONLY",
        "execution":{"genuine_metadata_read_method_calls":1,"trapped_callbacks_reached":0,
            "dependency_definitions_imported":True,"CAD_BREP_queries_or_construction":False,
            "candidate_panel_preparation_operator_K_q_forces_native_or_solve":False,
            "actual_field_or_admission_consumption":False,"new_numerical_experiment_or_test_suite":False},
        "limits":["This is a source/data readiness audit. Parent retains the serialized force slot and must obtain fresh own-field admission after any candidate solve.",
            "Old method readiness supports unchanged arithmetic and priors only. No historical response, resistance, geometry adoption or hardware qualification transfers.",
            "Authentic unchanged panels retain their original source geometry identity. No panel bank or preparation callback was reached.",
            "Unadopted Z180, no-slip floor and all recorded physical/capacity limits remain; all six physical release flags stay false."],
        "release":dict(method["release"]),"python":sys.version}
    out = OWN.with_name("receipt.json")
    with out.open("x") as handle:
        json.dump(receipt,handle,indent=2,sort_keys=True,allow_nan=False)
        handle.write("\n")
    print(json.dumps({"receipt":name(out),"sha256":sha(out),"review_helper_sha256":sha(OWN),
                      "status":receipt["status"],"source_union_pins":len(pins)},sort_keys=True))


if __name__ == "__main__":
    main()
