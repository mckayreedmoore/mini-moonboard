"""Reference postprocessing of accepted source-bound reviewed104 coupled states.

No source producer, local shaft solve, frame solve, CAD or native entry point
is called. Direct scalar references and saved continuous fields stay distinct.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKET = HERE.parent
RAW = HERE / "rawlocal/joint-frame-bolt-reference"
OPERATORS = HERE / "operators-attempt02"
API = HERE / "all-joint-splitting/closure.py"
ACTION_METHOD = HERE / "joint-frame-action-reconciliation.py"
STEEL = ROOT / "mini_moonboard/wood_joint_bolt_resistance.py"
LATERAL = PACKET / "lateral_reference.py"
NDS = ROOT / "mini_moonboard/nds_2024_multi_member_bolt_yield.py"
TOP = PACKET / "corner_checks.py"
PURE_LOADER = HERE / "knee-bridge-corner-references.py"
RETAINED = Path("/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json")
HARDWARE = PACKET / "assembly-package/hardware_engagement.py"
HARDWARE_AXES = HARDWARE.parent / "rawlocal/hardware-axes.csv"
MATERIAL = PACKET.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
FASTENERS = MATERIAL.with_name("fastener-inputs.json")
CONTINUOUS = frozenset(f"knee_outer_{side}_side_{i}" for side in ("left", "right") for i in (1, 2))
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear", "dead-only")
FY_MPA, PSI_MPA, N_PER_LBF = 92000. * .006894757293168, .006894757293168, 4.4482216152605
PINS = {
    API: "095cc122b4f0292fecd108446c24744a2671a703d156527afcd243eb8de9035d",
    ACTION_METHOD: "8eaf209dc594be9468b9bea60ddd02974e1a05f2bc915fd2dc41dcf2b11eaf8c",
    STEEL: "488e58bbd58fbc2f22af5d4122e734732bae09de79dad71bbf2623eeca60b166",
    LATERAL: "845409d1daf0214bbd41484f0a0a58867cd266bbc7f19060d9eef9d342657e94",
    NDS: "575d7de88d5f138412fef633ef946bccba884c1953b67e8d9211fc028d74ab89",
    TOP: "177e13712575b735dfb2cd4d1314d006e3f8fc77d3cbc9b3e117609fbe561bb0",
    PURE_LOADER: "188b7626d989eb16fb09ee75b8218dd9968974c95c72830dcd83c33f856c4b83",
    RETAINED: "c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1",
    HARDWARE: "d8e2a08e46fd9507a89d8e7ecb238ddf229490f4909345cbb641374ee8133295",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    FASTENERS: "ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2",
    ROOT / "fea/dowel_yield.py": "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    OPERATORS / "model-inputs.json": "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    OPERATORS / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
}
FLAGS = {"complete_joint_acceptance": False, "physical_release": False,
         "formal_criterion_acceptance": False, "proposal_forces_or_acceptance_transferred": False,
         "actual_hardware_capacity_qualified": False, "scalar_shaft_bending_complete": False,
         "washer_metal_resistance_complete": False, "source_producer_or_solve_executed": False}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def read(path):
    return json.loads(Path(path).read_text())


def status(index):
    return "METHOD_LIMIT" if index is None else "REFERENCE_EXCEEDANCE" if index > 1. else "SUPPORTED_CONDITIONAL_COMPARISON"


def direct(steel, tension, components, diameter):
    stress_area = {.25: .0318, .375: .0775, .5: .1419}[round(diameter / 25.4, 8)] * 25.4**2
    area = math.pi * diameter**2 / 4
    return steel.bolt_first_yield_reference(axial_force_n=tension, lateral_shear_vector_n=tuple(map(float, components)),
        minimum_tensile_area_mm2=stress_area, shear_plane_area_mm2=area, specified_min_yield_mpa=FY_MPA,
        property_scenario_id="source_nominal_UNC_At_and_smooth_D_92ksi",
        material_basis="Frozen conditional Grade5 92ksi scenario; no delivered-product qualification",
        tensile_area_basis="Existing nominal UNC tensile area; no measured minimum thread root",
        shear_area_basis="Source nominal smooth shank at its scalar interface",
        combined_action_area_mm2=area,
        combined_action_section_basis="Simultaneous same-section T and average V; scalar connector supplies no shaft bending")


def self_check():
    require(sha(STEEL) == PINS[STEEL], "steel helper changed")
    steel = module(STEEL, "joint_bolt_oracle")
    diameter = 6.35
    area = math.pi * diameter**2 / 4
    result = direct(steel, 0., (3., 4.), diameter)
    expected = math.sqrt(3.) * 5. / (area * FY_MPA)
    require(abs(result["interaction_utilization"] - expected) < 1e-14, "3/4/5 direct reference oracle differs")
    return {"same_state_average_shear_index": result["interaction_utilization"], "expected": expected,
            "absolute_error": abs(result["interaction_utilization"] - expected), "source_helper_sha256": PINS[STEEL]}


def accepted_scope(api, pins, response, summary, frame):
    """Authenticate exported state identities against actual audited source rows."""
    required = {(case, gap) for case in CASES for gap in (0., 1.)}
    def identity(row):
        key = row["case_id"], row["gap_scale"]
        require(key in required, "state lies outside recorded original104 case/gap inventory")
        return key
    def tag(key):
        return key[0] + ("_zero" if key[1] == 0. else "_gap")
    source_path = api.key(response / "comparison.json")
    source_hash = pins[response / "comparison.json"]
    def record(pointer):
        return {"path": source_path, "sha256": source_hash, "pointer": pointer}
    accepted = {}
    for i, row in enumerate(frame["states"]):
        key = identity(row)
        audit = row["audit"]
        require(key not in accepted and audit["all_passed"] is True and audit["checks"]
                and all(value is True for value in audit["checks"].values()), "duplicate or unaccepted source force field")
        accepted[key] = record("/states/" + str(i))
    require(accepted, "no accepted source force fields")
    dispositions = frame.get("case_dispositions")
    declared = {}
    if dispositions is not None:
        require(frame["complete_requested_state_inventory"] is True, "source disposition inventory is incomplete")
        for i, row in enumerate(dispositions):
            key = identity(row)
            require(key not in declared and row["physical_release"] is False, "invalid source disposition identity")
            declared[key] = row, record("/case_dispositions/" + str(i))
    else:
        require(frame["status"] == "COMPLETE_CONDITIONAL_COUPLED_FRAME_STATES" and set(accepted) == required,
                "partial source must preserve exact case dispositions")
    inventory = summary["required_state_inventory"]
    inventory_keys = [identity(row) for row in inventory]
    require(len(inventory_keys) == len(required) and set(inventory_keys) == required, "required disposition census differs")
    for row in inventory:
        key = identity(row)
        require(row["state_tag"] == tag(key) and row["physical_release"] is False, "exported disposition tag/release differs")
        require(row["accepted_force_field_exists"] is (key in accepted), "unavailable state changed to accepted demand")
        if key in declared:
            original, pointer = declared[key]
            require(row["source_disposition_record"] == pointer
                    and all(row.get(name) == value for name, value in original.items()), "source disposition bytes/record identity differ")
        else:
            require(row["source_disposition_record"] is None, "invented source disposition pointer")
        if key in accepted:
            require(row["status"] == "PASS_CONDITIONAL_COMPATIBLE_EQUILIBRIUM"
                    and row["source_state_record"] == accepted[key], "accepted disposition/source record differs")
        else:
            require(row["status"] in ("STOP_NO_AUDITED_POSITIVE_BEARING_FLOOR_BRANCH",
                    "STOP_NUMERICAL_QUALIFICATION_OPEN", "UNASSESSED_REQUIRED_STATE")
                    and "source_state_record" not in row, "stopped source force field transferred")
    exported = {}
    for row in summary["states"]:
        key = identity(row)
        require(key not in exported and key in accepted and row["state_tag"] == tag(key)
                and row["source_state_record"] == accepted[key], "exported action state/source field differs")
        exported[key] = row
    require(set(exported) == set(accepted) and summary["completed_states"] == len(accepted)
            and summary["counts"]["accepted_states"] == len(accepted)
            and summary["counts"]["required_states"] == len(required)
            and summary["counts"]["rejected_force_fields_exported"] == 0
            and summary["action_exports_complete_for_accepted_states"] is True
            and summary["all14_required_states"] is (set(accepted) == required)
            and summary["action_state_scope"] == ("all14_accepted_states" if set(accepted) == required else "accepted_state_subset"),
            "accepted action/source inventory disagrees")
    require((frame["status"] == "PARTIAL_CONDITIONAL_COUPLED_FRAME_STATES_WITH_DECLARED_STOPS")
            == any(not row["accepted_force_field_exists"] for row in inventory if identity(row) in declared),
            "partial source status contradicts declared states")
    return {"required_states": len(required), "accepted_states": len(accepted),
            "unavailable_states": len(required) - len(accepted), "all14_accepted_states": set(accepted) == required,
            "finite_state_disposition_inventory_complete": summary["finite_state_disposition_inventory_complete"],
            "required_state_inventory": inventory, "accepted_source_records": accepted}


def sources(actions, expected_receipt):
    require(sha(API) == PINS[API], "authentication helper changed")
    api = module(API, "joint_bolt_bindings")
    actions = Path(actions).resolve()
    require(actions.parent == HERE / "rawlocal/joint-frame-action-reconciliation"
            and sha(actions / "receipt.json") == expected_receipt, "action packet receipt identity differs")
    pins = dict(PINS)
    api.bind(pins, Path(__file__).resolve(), sha(__file__))
    api.bind(pins, actions / "receipt.json", expected_receipt)
    api.receipt_sources(pins, actions / "receipt.json")
    receipt, summary, inputs = [read(actions / name) for name in ("receipt.json", "summary.json", "inputs.json")]
    require(receipt["schema"] == "joint_frame_action_reconciliation_receipt/v1"
            and receipt["status"] == summary["status"] == "COMPLETE_SAVED_COUPLED_ACTION_RECONCILIATION_NOT_RESISTANCE_QUALIFICATION"
            and summary["source_force_basis"] == inputs["source_force_basis"] == "reviewed104_coupled_knee_sensitivity",
            "completed original104 action export required")
    require(pins[ACTION_METHOD] == PINS[ACTION_METHOD], "action producer changed")
    response = ROOT / inputs["response"]
    require(response / "comparison.json" in pins and response / "response.npz" in pins
            and response / "receipt.json" in pins, "compatible shaft response is outside action closure")
    frame = read(response / "comparison.json")
    require(frame["status"] in ("COMPLETE_CONDITIONAL_COUPLED_FRAME_STATES",
            "PARTIAL_CONDITIONAL_COUPLED_FRAME_STATES_WITH_DECLARED_STOPS")
            and frame["reviewed_geometry_changed"] is False
            and read(response / "inputs.json")["proposal_ties_included"] is False, "compatible source branch differs")
    scope = accepted_scope(api, pins, response, summary, frame)
    for helper in (HARDWARE_AXES, ROOT / "mini_moonboard/bolted_timber_checks.py"):
        if helper not in pins:
            api.bind(pins, helper, sha(helper))
    api.authenticate(pins)
    return api, pins, summary, inputs, frame, scope


def summarize(rows, key):
    finite = [r for r in rows if r[key] is not None]
    peak = max(finite, key=lambda r: r[key]) if finite else None
    return {"finite_states": len(finite), "method_limits": len(rows)-len(finite),
            "maximum": peak[key] if peak else None,
            "peak": {k: peak[k] for k in ("case_id", "gap_scale", "axis_id")} if peak else None,
            "reference_exceedances": [{k:r[k] for k in ("case_id", "gap_scale", "axis_id", key)} for r in finite if r[key]>1.]}


def build(output, actions, expected_receipt, prepare_only=False):
    output = Path(output).absolute()
    require(output.resolve() == output and output.parent == RAW and not output.exists(), "fresh immediate owned output child required")
    old_path, old_bytecode = list(sys.path), sys.dont_write_bytecode
    sys.path[:0] = [str(ROOT), str(PACKET)]
    sys.dont_write_bytecode = True
    started = time.monotonic()
    try:
        api, pins, action_summary, action_inputs, frame, scope = sources(actions, expected_receipt)
        known = self_check()
        source_binding = {"action_packet": api.key(Path(actions).resolve()), "action_receipt_sha256": expected_receipt,
                          "force_basis": "reviewed104_coupled_knee_sensitivity", "response": action_inputs["response"]}
        public_scope = {key: value for key, value in scope.items() if key != "accepted_source_records"}
        output.mkdir(parents=True, exist_ok=False)
        (output / ".gitignore").write_text("*\n")
        (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
        (output / "documentation.md.snapshot").write_bytes(Path(__file__).with_suffix(".md").read_bytes())
        payloads = {"known-answer.json": known, "input-plan.json": {**source_binding,
                    **public_scope, "expected_scalar_axis_states": 100 * scope["accepted_states"],
                    "expected_continuous_shaft_states": 4 * scope["accepted_states"],
                    "unavailable_scalar_axis_states": 100 * scope["unavailable_states"],
                    "unavailable_continuous_axis_states": 4 * scope["unavailable_states"],
                    "new_solves": 0, "complete_capacity_claimed": False}}
        if not prepare_only:
            import numpy as np
            require(np.__version__ == "2.5.2", "recorded NumPy runtime differs")
            geometry = read(OPERATORS / "model-inputs.json")
            rows = read(OPERATORS / "row-identities.json")
            require(len(rows) == 1888 and [r["row"] for r in rows] == list(range(1888)), "canonical row census differs")
            bolts = {b["axis_id"]:b for b in geometry["connections"] if b["kind"] in ("candidate_bolt", "retained_bolt")}
            require(len(bolts) == 104 and CONTINUOUS.issubset(bolts), "reviewed104 bolt census differs")
            members = {r["member_id"]:r["reduced_geometry_descriptor"] for r in geometry["members"] if r["member_kind"] != "panel"}
            steel, lateral, nds, hardware = [module(path, name) for path, name in
                ((STEEL,"joint_bolt_steel"),(LATERAL,"joint_bolt_lateral"),(NDS,"joint_bolt_nds"),(HARDWARE,"joint_bolt_hardware"))]
            top = module(PURE_LOADER,"joint_bolt_pure_loader").pure_functions(TOP,("lateral_reference",),
                {"math":math,"correction":SimpleNamespace(lateral=lateral)})
            require(Path(sys.modules["fea.dowel_yield"].__file__).resolve() == ROOT/"fea/dowel_yield.py", "wrong lateral dependency")
            require(read(MATERIAL)["conditional_DF_L_No2_base_row"]["base_properties"]["G_for_dowel_bearing"] == .5
                    and 1000*read(FASTENERS)["material_boundaries"]["sae_j429_grade5_1_4_through_1_in"]["machine_test_yield_ksi_min"] == 92000., "material scenario differs")
            retained = read(RETAINED)["axis_register"]
            with HARDWARE_AXES.open(newline="", encoding="utf-8") as stream:
                family_ids = {r["axis_id"]:r["family_id"] for r in csv.DictReader(stream)}
            require(set(bolts).issubset(family_ids), "hardware axis census differs")
            def unit(value):
                value = np.asarray(value, dtype=float)
                require(value.shape==(3,) and np.isfinite(value).all() and np.linalg.norm(value)>0, "invalid direction")
                return value / np.linalg.norm(value)
            scalar, continuous = [], []
            response_states = {(s["case_id"],s["gap_scale"]):s for s in frame["states"]}
            require(set(response_states) == set(scope["accepted_source_records"]), "accepted response census differs")
            with np.load(Path(actions)/"source-row-response.npz", allow_pickle=False) as saved:
                require(set(saved.files) == {"canonical_raw_row_available", "canonical_raw_row_to_kept_lumped_position", "old_kept_lumped_rows"}
                        | {state["state_tag"] + suffix for state in action_summary["states"] for suffix in
                           ("_raw_force_n", "_kept_lumped_relative_motion_mm", "_coupled_force_n")},
                        "canonical export contains missing or rejected state fields")
                available = saved["canonical_raw_row_available"]
                require(available.shape==(1888,) and np.count_nonzero(~available)==20, "replaced-row mask differs")
                for state in action_summary["states"]:
                    case,gap,tag=state["case_id"],state["gap_scale"],state["state_tag"]
                    source_state_record = scope["accepted_source_records"][(case, gap)]
                    force=saved[tag+"_raw_force_n"]
                    require(force.shape==(1888,) and np.isfinite(force).all(), "invalid sourceD raw force")
                    cd=.9 if case=="dead-only" else 1.
                    require(state["duration_factor_for_downstream_strength"]==cd, "duration branch differs")
                    for axis in sorted(set(bolts)-CONTINUOUS):
                        bolt=bolts[axis]
                        owned=[r for r in rows if r["row_id"].startswith(axis+"/")]
                        planes=[r for r in owned if "bolt_lateral_plane" in r["ownership"]["role"]]
                        ties=[r for r in owned if r["ownership"]["role"]=="physical_bolt_outer_seat_tension"]
                        require(len(planes)==2 and len(ties)==1 and planes[0]["row_id"]==planes[1]["row_id"], "scalar bolt row partition differs: "+axis)
                        indices=[r["row"] for r in planes];tie=ties[0]
                        require(available[indices].all() and available[tie["row"]], "replaced placeholder used as scalar bolt demand")
                        bodies=[planes[0]["ownership"][k] for k in ("first_body","second_body")]
                        require(set(bodies)==set(bolt["receiver_member_ids"]) and len(bodies)==2, "scalar receiver identity differs")
                        require(all([r["ownership"][k] for k in ("first_body","second_body")]==bodies for r in planes), "mixed lateral ownership")
                        basis=np.asarray([r["ownership"]["direction_global_xyz"] for r in planes]);axis_unit=unit(bolt["axis_xyz"])
                        require(np.max(abs(basis@basis.T-np.eye(2)))<1e-8 and np.max(abs(basis@axis_unit))<1e-8, "invalid scalar lateral basis")
                        components=force[indices];vector=components@basis;V=float(np.linalg.norm(vector));T=float(force[tie["row"]])
                        grains=[unit(members[b]["axis"]) for b in bodies];angles=[lateral.angle(vector,g) for g in grains]
                        if bolt["kind"]=="retained_bolt":
                            spans={r["member"]:[r["interval_from_axis_datum_mm"]] for r in retained[axis]["finished_receivers"]}
                            diameter=bolt["source_record"]["source_occupied_diameter_mm"]
                        else:
                            geom=bolt["source_record"]["geometry"]
                            spans={r["receiver_id"]:r["current_shaft_intersection_solid_intervals_from_underhead_mm"] for r in geom["wood_receiver_intervals"]}
                            diameter=geom["modeled_shaft_diameter_mm"]
                        require(set(spans)==set(bodies) and all(len(v)==1 and v[0][1]>v[0][0] for v in spans.values()), "scalar bearing intervals differ")
                        lengths=[spans[b][0][1]-spans[b][0][0] for b in bodies]
                        nominal_d=round(diameter/25.4,8)
                        nominal_diameter=nominal_d*25.4
                        dref=direct(steel,T,components,nominal_diameter)
                        endgrain=[b for b,g in zip(bodies,grains,strict=True) if abs(axis_unit@g)>1-1e-8]
                        lat_n=None;lat_method=None;lat_limit=None
                        if endgrain:
                            main=endgrain[0]
                            require(len(endgrain)==1 and "base_header" in bodies and nominal_d==.25, "endgrain method domain differs")
                            sorted_spans=sorted(v[0] for v in spans.values())
                            if abs(sorted_spans[1][0]-sorted_spans[0][1])<=1e-7:
                                reference=lateral.reference([lengths[bodies.index(main)],lengths[bodies.index("base_header")]],
                                    [90.,angles[bodies.index("base_header")]],92000.)
                                lat_n=.67*reference["reference_lateral_lbf"]*N_PER_LBF
                                lat_method="EXISTING_Ceg_0p67_SINGLE_SHEAR_REFERENCE"
                            else:lat_limit="Ceg source intervals do not meet zero-interface-gap domain"
                        elif any(abs(axis_unit@g)>1e-8 for g in grains):
                            lat_limit="Oblique bolt-to-grain lies outside the existing crossgrain/endgrain routes"
                        elif bolt["kind"]=="retained_bolt":
                            receiving=[{"bearing_length_in":length/25.4,"fe_theta_psi":nds._fe_theta_psi(specific_gravity=.5,diameter_in=nominal_d,angle_degrees=angle)} for length,angle in zip(lengths,angles,strict=True)]
                            modes=nds._single_shear_modes(*receiving,nominal_d,92000.,nds._reduction_terms(diameter_in=nominal_d,nominal_diameter_in=nominal_d,angle_max_degrees=max(angles)))
                            lat_n=min(modes.values())*N_PER_LBF;lat_method="EXISTING_RETAINED_PRIMARY_NDS"
                        elif axis.startswith("top_outer/"):
                            lat_n=top.lateral_reference(vector,nominal_diameter,lengths,grains,92000.)["reference_n"]
                            lat_method="EXISTING_TOP_DIAMETER_DEPENDENT_Fe"
                        else:
                            lat_n=lateral.reference(lengths,angles,92000.)["reference_lateral_lbf"]*N_PER_LBF
                            lat_method="EXISTING_CANDIDATE_ROUNDED_Fe"
                        lat_ratio=V/(cd*lat_n) if lat_n else None
                        catalog=hardware.STACKS[hardware.ROUTES[family_ids[axis]][0]]
                        hardware_match=math.isclose(catalog["diameter_mm"],nominal_diameter,abs_tol=1e-6)
                        source_catalog=catalog if hardware_match else hardware.STACKS["qtr_kl"]
                        washer=source_catalog["washer"]
                        bore=max(2*r["unique_bore_radius_mm"] for r in bolt.get("receiver_clearance_geometry",[]) if r.get("unique_bore_radius_mm")) if bolt["kind"]=="candidate_bolt" else washer["inside_diameter_mm"][1]
                        woodref=steel.wood_washer_annulus_reference_lbf(washer_outer_diameter_in=washer["outside_diameter_mm"][0]/25.4,
                            washer_inner_diameter_in=washer["inside_diameter_mm"][1]/25.4,wood_bore_diameter_in=bore/25.4)
                        woodref_n=woodref["wood_bearing_reference_lbf"]*N_PER_LBF
                        limits=["Scalar law contains no compatible continuous shaft bending or own-end washer moment field",
                                "Ideal annular wood reference does not establish support, tilted contact or washer metal resistance"]
                        if not hardware_match:limits.append("Current shop diameter differs from source scalar shaft; source nominal reference retained")
                        if axis=="center_principal_right_2":limits.append("Recorded partial washer seat: full-annulus support is unavailable")
                        if endgrain:limits.append("Ceg single-fastener reference precedes group/geometry adjustments and actual joint qualification")
                        scalar.append({"case_id":case,"gap_scale":gap,"state_tag":tag,"axis_id":axis,"kind":bolt["kind"],
                            "source_state_record": source_state_record,
                            "source_rows":indices+[tie["row"]],"source_row_availability_checked":True,"receivers":bodies,
                            "point_mm":planes[0]["ownership"]["point_mm"],"signed_T_n":T,"lateral_components_n":components.tolist(),
                            "signed_sourceD_lateral_vector_xyz_n":vector.tolist(),"V_n":V,"source_diameter_mm":nominal_diameter,
                            "source_bearing_lengths_mm":lengths,"grain_angles_degrees":angles,"duration_factor":cd,
                            "direct_steel":dref,"thread_tension_index":dref["tension_first_yield_utilization"],
                            "average_T_V_index":dref["interaction_utilization"],"lateral_reference_n":lat_n,
                            "lateral_reference_method":lat_method,"lateral_reference_index":lat_ratio,"lateral_method_limit":lat_limit,
                            "ideal_annulus_wood_reference_n":woodref_n,"ideal_annulus_wood_index":max(0.,T)/woodref_n,
                            "current_shop_diameter_matches_source":hardware_match,"continuous_shaft_bending_index":None,
                            "complete_same_state_steel_index":None,"own_end_washer_M_nmm":None,"limits":limits,
                            "direct_status":status(dref["interaction_utilization"]),"lateral_status":status(lat_ratio),**FLAGS})
                    diags=response_states[(case,gap)]["compatible_shaft_diagnostics"]
                    require(len(diags)==4 and {r["axis_id"] for r in diags}==CONTINUOUS, "compatible continuous shaft census differs")
                    for row in diags:
                        axis=row["axis_id"]
                        original_rows=[r["row"] for r in rows if r["row_id"].startswith(axis+"/") and ("bolt_lateral_plane" in r["ownership"]["role"] or r["ownership"]["role"]=="physical_bolt_outer_seat_tension")]
                        require(len(original_rows)==5 and not available[original_rows].any(), "continuous oldrows must remain unavailable")
                        peak=row["peak_same_state_same_position_smooth_proxy"]
                        index=peak["over_declared_yield_sensitivity"]["92ksi"]
                        require(math.isfinite(index) and index>=0 and peak["signed_single_tie_n"]==row["physical_axial_force_n"], "same-state continuous peak join differs")
                        continuous.append({"case_id":case,"gap_scale":gap,"state_tag":tag,"axis_id":axis,
                            "source_state_record": source_state_record,
                            "signed_physical_T_n":row["physical_axial_force_n"],"continuous_shaft_bending_index":index,
                            "status":status(index),"compatible_source_diagnostics":row,"source_old_rows_unavailable":original_rows,
                            "proposal_or_scalar_placeholder_fields_used":False,**FLAGS})
            count = scope["accepted_states"]
            require(len(scalar) == 100 * count and len(continuous) == 4 * count
                    and len({(r["case_id"],r["gap_scale"],r["axis_id"]) for r in scalar+continuous}) == 104 * count,
                    "accepted axis-state census differs")
            unavailable = [{"case_id":row["case_id"],"gap_scale":row["gap_scale"],"state_tag":row["state_tag"],
                "axis_id":axis,"kind":"continuous_shaft" if axis in CONTINUOUS else "scalar_bolt",
                "source_disposition":row,"accepted_force_field_exists":False,"bolt_demand_fields_available":False,
                "signed_T_n":None,"V_n":None,"reference_index":None,"status":"SOURCE_STATE_UNAVAILABLE",**FLAGS}
                for row in scope["required_state_inventory"] if not row["accepted_force_field_exists"] for axis in sorted(bolts)]
            require(len(unavailable) == 104 * scope["unavailable_states"], "unavailable axis-state census differs")
            payloads.update({"scalar-bolts.jsonl":scalar,"continuous-shafts.jsonl":continuous,"unavailable-axis-states.jsonl":unavailable,
                "summary.json":{"schema":"joint_frame_bolt_reference/v1",
                "status":"COMPLETE_DIRECT_REFERENCES_WITH_DECLARED_METHOD_LIMITS" if scope["all14_accepted_states"] else
                    "COMPLETE_DIRECT_REFERENCES_FOR_ACCEPTED_SUBSET_WITH_DECLARED_METHOD_LIMITS_AND_UNAVAILABLE_STATES",
                **source_binding,**public_scope,
                "counts":{"required_states":14,"accepted_states":count,"unavailable_states":scope["unavailable_states"],
                    "scalar_axes":100,"scalar_axis_states":len(scalar),"continuous_axes":4,"continuous_axis_states":len(continuous),
                    "unavailable_axis_states":len(unavailable)},
                "scalar_references":{k:summarize(scalar,k) for k in ("thread_tension_index","average_T_V_index","lateral_reference_index","ideal_annulus_wood_index")},
                "continuous_shaft_reference":summarize(continuous,"continuous_shaft_bending_index"),
                "scalar_full_bending_and_washer_moment_method_limits":len(scalar),
                "shop_diameter_binding_limits":sum(not r["current_shop_diameter_matches_source"] for r in scalar),
                "lateral_method_limit_census":dict(Counter(r["lateral_method_limit"] for r in scalar if r["lateral_method_limit"])),
                "comparison_inventory_complete_for_accepted_states":True,
                "all14_required_state_comparisons_complete":scope["all14_accepted_states"],**FLAGS}})
        else:
            payloads["summary.json"]={"status":"PREPARED_SOURCE_AUTHENTICATION_AND_DIRECT_ORACLE_ONLY",**source_binding,**public_scope,
                                      "target_state_postprocessing_executed":False,**FLAGS}
        api.authenticate(pins)
        for name,value in payloads.items():
            with (output/name).open("w") as stream:
                for item in value if name.endswith(".jsonl") else [value]:
                    stream.write(json.dumps(item,sort_keys=True,allow_nan=False)+"\n")
        (output/"sources.json").write_text(json.dumps({api.key(p):h for p,h in pins.items()},sort_keys=True)+"\n")
        outputs={path.name:sha(path) for path in sorted(output.iterdir()) if path.is_file()}
        receipt={"schema":"joint_frame_bolt_reference_receipt/v1","status":payloads["summary.json"]["status"],
                 "source_sha256":{api.key(p):h for p,h in pins.items()},"output_sha256":outputs,
                 "documentation_input_sha256":outputs["documentation.md.snapshot"],
                 "source_authenticated_before_and_after":True,"elapsed_seconds":time.monotonic()-started,**FLAGS}
        (output/"receipt.json").write_text(json.dumps(receipt,sort_keys=True,allow_nan=False)+"\n")
        api.authenticate(pins)
        return {"status":receipt["status"],"receipt_sha256":sha(output/"receipt.json"),"output":str(output),**FLAGS}
    finally:
        sys.path[:],sys.dont_write_bytecode=old_path,old_bytecode


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-check",action="store_true")
    parser.add_argument("--prepare",action="store_true")
    parser.add_argument("--actions",type=Path)
    parser.add_argument("--receipt-sha256")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    if args.self_check:result=self_check()
    else:
        require(args.actions is not None and args.receipt_sha256 is not None and args.output is not None,"actions, receipt-sha256 and output are required")
        result=build(args.output,args.actions,args.receipt_sha256,args.prepare)
    print(json.dumps(result,sort_keys=True,allow_nan=False))
