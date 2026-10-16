"""Parent-owned serialized runs for the current calculation corrections.

Each invocation freezes its own inputs in a fresh ignored output directory.
Historical packets and reviewed physical geometry are never overwritten.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def write(path,record):
    Path(path).write_text(json.dumps(record,indent=2,allow_nan=False)+"\n")


def output_directory(path):
    path=Path(path).resolve()
    if path.exists() or not path.is_relative_to((HERE/"rawlocal").resolve()):
        raise ValueError("Fresh ignored output directory required")
    path.mkdir(parents=True)
    (path/".gitignore").write_text("*\n")
    (path/"runner.py.snapshot").write_bytes(Path(__file__).read_bytes())
    return path


def washers(output,all_end_states=False):
    api=module(HERE/"washer-stack-correction.py","current_washer_stack_adapter")
    inputs=api.load_current_cases(include_all_selected_end_states=True) if all_end_states else api.load_current_cases()
    coupons=api.coupon_suite(inputs)
    engine=api.load_engine()
    output=output_directory(output)
    (output/"adapter.py.snapshot").write_bytes((HERE/"washer-stack-correction.py").read_bytes())
    write(output/"input-plan.json",inputs)
    write(output/"analytic-coupons.json",coupons)
    started=time.monotonic()
    results=[]
    profiles={case["profile_id"]:case["profile"] for case in inputs["cases"]}
    for profile_id,profile in profiles.items():
        selected=[c for c in inputs["cases"] if c["profile_id"]==profile_id]
        print("profile "+profile_id+"; "+str(len(selected))+" same-state solves",flush=True)
        model=api.make_stack_model(engine,profile,resolution="fine")
        write(output/(profile_id+"-discrete-coupons.json"),{k:model[k] for k in
            ("rigid_modes","assembled_plate_coupon","separate_plate_contact_coupon")})
        for case in selected:
            result=api.solve_case(engine,model,case)
            identity=case["state_tag"]+"-"+str(case["source_input"]["record_index"])
            record=result["result"]
            write(output/(identity+"-result.json"),record)
            with gzip.open(output/(identity+"-fields.json.gz"),"wt") as stream:
                json.dump(result["fields"],stream,allow_nan=False)
            results.append(record)
            write(output/"progress.json",{"elapsed_seconds":time.monotonic()-started,
                "completed_cases":len(results),"required_cases":len(inputs["cases"]),
                "latest_case":record["case"],"latest_index":record["stress_comparison"]["over_hypothetical_Fy250"]})
            print(identity+": "+str(record["stress_comparison"]["over_hypothetical_Fy250"]),flush=True)
        del model
    api._check_pins()
    peak=max(results,key=lambda r:r["stress_comparison"]["over_hypothetical_Fy250"])
    summary={"schema":"current_two_washer_stack_run/v1",
        "status":"COMPLETED_SELECTED_END_SAME_STATE_STACK_COMPARISONS",
        "cases":len(results),"all_selected_end_states":all_end_states,
        "peak":peak,"exceedance_count":sum(r["stress_comparison"]["over_hypothetical_Fy250"]>1. for r in results),
        "elapsed_seconds":time.monotonic()-started,"versions":engine["versions"],
        "source_inputs":inputs["source_pins"],
        "fit_grip_impacts":inputs["fit_grip_impacts_by_axis"],
        "global_force_feedback_evaluated":False,"actual_washer_yield_qualified":False,
        "reviewed_geometry_changed":False,"complete_joint_acceptance":False,"physical_release":False}
    write(output/"summary.json",summary)
    write(output/"receipt.json",{"schema":"current_method_correction_receipt/v1",
        "status":summary["status"],"source_sha256":{str(HERE.relative_to(ROOT)/"washer-stack-correction.py"):sha(HERE/"washer-stack-correction.py")},
        "output_sha256":{p.name:sha(p) for p in output.iterdir() if p.is_file() and p.name!=".gitignore"},
        "physical_release":False})
    print(json.dumps({"output":str(output.relative_to(ROOT)),"cases":len(results),
        "maximum":peak["stress_comparison"]["over_hypothetical_Fy250"],"exceedances":summary["exceedance_count"]},indent=2),flush=True)
    return summary


def extract_panels(output,frame,states,vectors,recovery=None):
    """Recover panel actions, optionally using a newly frozen port projection."""
    import numpy as np
    from scipy import sparse
    api=module(HERE/"panel-compatible-response.py","horizontal_current_panel_reference")
    data=api.static_sources()
    if recovery is not None:
        data.axes=recovery["axes"]
        data.rows=recovery["rows"]
    defs=data.definitions
    panel=defs(api.PANEL,("size_factor","panel_reference"),
        {"math":__import__("math"),"LBF_N":data.local.N,"PSI_MPA":data.local.N/25.4**2},("BASE",))
    helper=defs(api.N14,("comparison_row","panel_sections"),
        {"np":np,"math":__import__("math"),"N_PER_LBF":data.local.N,"require":api.require})
    wrench=defs(api.WRENCH,("wrench",),{"np":np}).wrench
    labels=[tuple(map(int,line.split("."))) for line in api.DOF.read_text().splitlines() if line.strip()]
    label_rows={label:i for i,label in enumerate(labels)}
    orientation_model=json.loads((HERE/"panel-width-operators-attempt01/model.json").read_text())
    data.model["material_binding"]["panel_axes"]=orientation_model["material_binding"]["panel_axes"]
    names=data.model["body_names"]
    mapping=json.loads((HERE/"rawlocal/joint-frame-action-reconciliation/profile-attempt01/source-row-map.json").read_text())
    if recovery is not None:
        mapping=recovery["mapping"]
    projection=(recovery["B"] if recovery is not None else sparse.load_npz(api.ORIGINAL/"B.npz")).tocsr()
    with np.load(api.ORIGINAL/"operators.npz",allow_pickle=False) as original:
        D,F=[original[k].copy() for k in ("D","F")]
    if recovery is not None:
        D,F=recovery["D"],recovery["F"]
    mechanics=module(HERE/"joint-frame-member-replacement.py","horizontal_panel_coefficients")
    screws,cuts,balances=[],[],[]
    for state in states:
        tag=state["state_tag"]
        f,q=vectors[tag+"_force"],vectors[tag+"_motion"]
        raw=np.zeros(projection.shape[0])
        for item in mapping["kept_map"]:
            raw[item["raw_rows"]]=np.asarray(item["weights"])*f[item["kept_position"]]
        coefficient=mechanics.load_coefficients(state["case_id"],frame["dead_load_factor"])
        nodal=F@coefficient-projection.T@raw
        for axis in data.axes:
            ids=axis["rows"]
            pb=6*names.index(axis["panel"])
            own=raw[ids]
            positions=[next(item["kept_position"] for item in mapping["kept_map"] if i in item["raw_rows"]) for i in ids]
            motions=q[positions]
            expected=np.array([data.rows[i]["law"]["stiffness_N_per_mm"]*(max(0.,motions[j]) if j==2 else motions[j])
                              for j,i in enumerate(ids)])
            if np.max(abs(own-expected))>=1e-4:
                raise ValueError("New panel screw law does not close")
            screws.append({"case_id":state["case_id"],"state_id":tag,"state_tag":tag,
                "gap_scale":state["gap_scale"],"axis_id":axis["axis_id"],"panel":axis["panel"],
                "scope":api.scope(state["case_id"],state["gap_scale"]),
                "receiver":axis["receiver"],"source_rows":ids,"point_mm":axis["point_mm"],
                "tension_n":max(0.,float(own[2])),"lateral_n":float(np.linalg.norm(own[:2])),
                "signed_force_on_panel_n":(-D[ids,pb:pb+3].T@own).tolist(),
                "signed_axial_relative_mm":float(motions[2]),"complete_screw_acceptance":False,
                "force_basis":"current_profile_owner_reported_horizontal_face_grain",
                "source_state_record":{"path":str((output/"comparison.json").relative_to(ROOT)),
                    "sha256":sha(output/"comparison.json"),"pointer":"/states/"+str(states.index(state))}})
        for name in data.geometry["panels"]:
            nodes=sorted(set(data.model["body_nodes"][name]))
            center=np.mean([data.model["physical_node_coordinates_mm"][str(n)] for n in nodes],axis=0)
            actions=[{"row":-1,"point_mm":data.model["physical_node_coordinates_mm"][str(n)],
                "force_n":nodal[[label_rows[n,d] for d in (1,2,3)]].tolist(),"free_moment_nmm":[0.,0.,0.]}
                for n in nodes]
            residual=wrench(actions,center)
            if np.max(abs(residual[:3]))>=1e-5 or np.max(abs(residual[3:]))>=.01:
                raise ValueError("New panel nodal equilibrium does not close")
            records=helper.panel_sections(np,panel,wrench,SimpleNamespace(model=data.model),tag,name,actions,center)
            cuts.extend({**r,"state_id":tag,"source_case_id":state["case_id"],"gap_scale":state["gap_scale"]} for r in records)
            balances.append({"state_tag":tag,"panel":name,"force_moment_residual_n_nmm":residual.tolist()})
    for filename,records in (("screw-states.jsonl",screws),("panel-cut-actions.jsonl",cuts),("panel-balances.jsonl",balances)):
        with (output/filename).open("w") as stream:
            for row in records:
                stream.write(json.dumps(row,allow_nan=False)+"\n")
    return {"screw_states":len(screws),"gross_panel_cuts":len(cuts),"panel_balances":len(balances),
        "peak_head_tension_n":max(screws,key=lambda r:r["tension_n"]) if screws else None,
        "gross_rolling_shear_peak":max(cuts,key=lambda r:r["comparisons"]["Group1_saved_scenario"]["transverse_shear"]["ratio"]) if cuts else None}


def horizontal_frame(output,retry_source=None,solver_feas_tol=None):
    """Apply the proved panel-only orientation delta to the current force model."""
    import numpy as np
    follow=module(HERE/"joint-frame-profile-followup.py","horizontal_current_profile")
    mechanics=follow.mechanics()
    frame=follow.profile_frame(mechanics)
    solver=mechanics.compatibility()
    settings=dict(solver.SOLVER_SETTINGS if retry_source is not None else solver.REFINEMENT_SETTINGS)
    if solver_feas_tol is not None:
        if retry_source is None or not 1e-10 <= solver_feas_tol <= 1e-9:
            raise ValueError("A bounded feasibility retry requires an authenticated stopped source")
        settings["tol_feas"]=solver_feas_tol
    slope=HERE/"operators-attempt02/operators.npz"
    width=HERE/"panel-width-operators-attempt01/operators.npz"
    authority=HERE/"panel-width-operators-attempt01/operator-assessment.json"
    pins={slope:"c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
          width:"bf7cfd24800a0c551fa136465d8d92172ec9dd9b619d86d43930ab7f17b87387",
          authority:"47e3405e15e3d97f8666ffdead694f1a83fe6f3f76608fc81882112075e98fe0"}
    for path,digest in pins.items():
        if sha(path)!=digest:
            raise ValueError("Cached orientation input changed: "+str(path))
    with np.load(slope,allow_pickle=False) as original,np.load(width,allow_pickle=False) as changed:
        dH=changed["H"]-original["H"]
        de=changed["e"]-original["e"]
        if not all(np.array_equal(original[k],changed[k]) for k in ("D","F","W")):
            raise ValueError("Orientation cache changed geometry or external loads")
    kept=frame["joint"]["old_kept_lumped_rows"]
    count=len(kept)
    if count!=1592 or len(set(map(int,kept)))!=count:
        raise ValueError("Current old-row panel map differs")
    from scipy import sparse
    row_map_path=HERE/"rawlocal/joint-frame-action-reconciliation/profile-attempt01/source-row-map.json"
    row_map=json.loads(row_map_path.read_text())
    if row_map["old_kept_lumped_rows"]!=kept.tolist():
        raise ValueError("Current canonical-to-lumped map differs")
    map_rows,map_columns,map_weights=[],[],[]
    for item in row_map["kept_map"]:
        map_rows.extend([item["kept_position"]]*len(item["raw_rows"]))
        map_columns.extend(item["raw_rows"])
        map_weights.extend(item["weights"])
    P=sparse.coo_matrix((map_weights,(map_rows,map_columns)),shape=(count,1888)).tocsr()
    affected=set(np.flatnonzero(np.any(abs(dH)>1e-12,axis=0))) | set(np.flatnonzero(np.any(abs(de)>1e-12,axis=1)))
    if not affected.issubset(set(map_columns)):
        raise ValueError("A changed panel contribution has an unavailable current port")
    frame["H"][:count,:count]+=(P@dH)@P.T
    frame["e"][:count]+=P@de
    if np.min(np.diag(frame["H"])) < -1e-12:
        raise ValueError("Mapped orientation compliance has a negative diagonal before solving")
    pins[row_map_path]=sha(row_map_path)
    baseline=HERE/"rawlocal/joint-frame-profile-followup/profile-enriched01"
    if sha(baseline/"receipt.json")!="317f8800d0f1ad947778d4f553a46403b50fbb9d921d0b70f8854928f9994455":
        raise ValueError("Current wider-washer response basis changed")
    report=json.loads((baseline/"comparison.json").read_text())
    output=output_directory(output)
    write(output/"inputs.json",{"owner_reported_face_grain":"horizontal_across_board",
        "changed_panels":["main_lower_left","main_lower_right","main_upper_left","main_upper_right"],
        "source_sha256":{p.relative_to(ROOT).as_posix():h for p,h in {**frame["source_sha256"],**pins}.items()},
        "baseline_response_receipt_sha256":sha(baseline/"receipt.json"),
        "old_rows_updated":count,"appended_continuous_shaft_rows_updated":0,
        "plywood_source_geometry_thickness_mm":18.25625,"owner_reported_nominal_thickness_mm":19.05,
        "unchanged_physical_geometry":True,"maximum_fixed_floor_calls":len(report["states"]),
        "original_solver_audit_gates_preserved":True,"physical_release":False})
    started=time.monotonic()
    states,vectors,dispositions=[],{},[]
    reuse_states,reuse_vectors={},{}
    if retry_source is not None:
        retry_source=Path(retry_source).resolve()
        receipt=json.loads((retry_source/"receipt.json").read_text())
        for filename in ("comparison.json","response.npz"):
            if sha(retry_source/filename)!=receipt["output_sha256"][filename]:
                raise ValueError("Retry/reuse response bytes changed")
        prior=json.loads((retry_source/"comparison.json").read_text())
        reuse_states={s["state_tag"]:s for s in prior["states"] if s["audit"]["all_passed"]}
        with np.load(retry_source/"response.npz",allow_pickle=False) as saved:
            reuse_vectors={k:saved[k].copy() for k in saved.files}
        write(output/"retry-input.json",{"source":str(retry_source.relative_to(ROOT)),
            "receipt_sha256":sha(retry_source/"receipt.json"),"reused_accepted_states":sorted(reuse_states),
            "retry_method":"Reuse accepted fields; retry stopped fields with recorded settings and unchanged physical gates",
            "solver_settings":settings,
            "feasibility_tolerance_reason":"Original stop residual 1.265e-10 narrowly exceeded solver tol_feas=1e-10; independently audited physics gates remain unchanged" if solver_feas_tol else None})
    with np.load(baseline/"response.npz",allow_pickle=False) as source:
        for original in report["states"]:
            case,gap=original["case_id"],original["gap_scale"]
            tag=case+("_zero" if gap==0. else "_gap")
            if tag in reuse_states:
                states.append({**reuse_states[tag],"reused_audited_field_source":str(retry_source.relative_to(ROOT)),
                    "source_response_sha256":sha(retry_source/"response.npz")})
                vectors.update({tag+suffix:reuse_vectors[tag+suffix] for suffix in
                    ("_force","_motion","_rigid","_shaft_pose","_bearing")})
                dispositions.append({"case_id":case,"gap_scale":gap,"state_tag":tag,
                    "status":"PASS_REUSED_SAME_MODEL_AUDITED_EQUILIBRIUM","accepted_force_field_exists":True})
                continue
            bearing=source[tag+"_bearing"].copy()
            coefficient=mechanics.load_coefficients(case,frame["dead_load_factor"])
            print(tag+": horizontal grain, current washer profile, fixed source floor mask",flush=True)
            try:
                f,q,a,details,audit=solver.fixed_floor_branch(frame["H"],frame["D"],frame["e"]@coefficient,
                    frame["W"]@coefficient,frame["joint"],bearing,gap,
                    settings)
                if not audit["all_passed"]:
                    raise ValueError("Original physical gates failed")
                pose=follow.recover_shaft_pose(frame,f,a)
            except ValueError as error:
                trial=getattr(error,"trial",None)
                write(output/(tag+"-stop.json"),{"error":str(error),"trial_audit":trial.get("audit") if trial else None,
                    "accepted_force_field_exists":False,"physical_failure_claimed":False})
                dispositions.append({"case_id":case,"gap_scale":gap,"state_tag":tag,
                    "status":"STOP_CHANGED_ORIENTATION_FIXED_MASK_OR_NUMERICAL_AUDIT","accepted_force_field_exists":False})
                continue
            states.append({"case_id":case,"gap_scale":gap,"state_tag":tag,"audit":audit,"solver":details,
                "floor_mask_source":"same_state_current_profile_baseline","physical_release":False})
            vectors.update({tag+suffix:value for suffix,value in zip(("_force","_motion","_rigid","_shaft_pose","_bearing"),
                (f,q,a,pose,bearing),strict=True)})
            dispositions.append({"case_id":case,"gap_scale":gap,"state_tag":tag,
                "status":"PASS_CONDITIONAL_COMPATIBLE_EQUILIBRIUM","accepted_force_field_exists":True})
            write(output/"progress.json",{"elapsed_seconds":time.monotonic()-started,"completed":len(states),"state_tag":tag})
            print(tag+": original physical audit passed",flush=True)
    unavailable=[{**r,"horizontal_orientation_state":"UNASSESSED_OUTSIDE_BASELINE_FORCE_FIELD_SCOPE"}
                 for r in report["case_dispositions"] if not r["accepted_force_field_exists"]]
    write(output/"comparison.json",{"schema":"current_horizontal_panel_frame_correction/v1","states":states,
        "case_dispositions":dispositions,"baseline_unavailable_states":unavailable,
        "requested_states":len(report["states"]),"accepted_states":len(states),
        "physical_geometry_changed":False,"complete_joint_acceptance":False,"physical_release":False})
    np.savez_compressed(output/"response.npz",**vectors)
    recovered=extract_panels(output,frame,states,vectors)
    write(output/"summary.json",{"accepted_states":len(states),"stopped_requested_states":len(report["states"])-len(states),
        "baseline_unavailable_states":len(unavailable),"elapsed_seconds":time.monotonic()-started,**recovered,
        "actual_plywood_properties_qualified":False,"physical_release":False})
    write(output/"receipt.json",{"schema":"current_method_correction_receipt/v1",
        "status":"COMPLETED_CURRENT_HORIZONTAL_PANEL_DISPOSITIONS_AND_ACCEPTED_ACTIONS",
        "source_sha256":json.loads((output/"inputs.json").read_text())["source_sha256"],
        "output_sha256":{p.name:sha(p) for p in output.iterdir() if p.is_file() and p.name!=".gitignore"},"physical_release":False})
    print(json.dumps({"output":str(output.relative_to(ROOT)),"accepted_states":len(states),"panel_recovery":recovered},indent=2),flush=True)


def panel_references(output,source):
    """Pure scalar/net-section recovery from the newly authenticated forces."""
    import copy

    import numpy as np
    source=Path(source).resolve()
    receipt=json.loads((source/"receipt.json").read_text())
    for filename in ("comparison.json","screw-states.jsonl","panel-cut-actions.jsonl"):
        if sha(source/filename)!=receipt["output_sha256"][filename]:
            raise ValueError("Panel source bytes differ from their receipt")
    api=module(HERE/"panel-method-correction.py","current_panel_scalar_methods")
    api._check_pins()
    output=output_directory(output)
    (output/"panel-method-correction.py.snapshot").write_bytes((HERE/"panel-method-correction.py").read_bytes())
    binding={"orientation":"horizontal_strong_x","force_profile_id":str(source.relative_to(ROOT)),
        "action_receipt_sha256":sha(source/"receipt.json"),
        "screw_states_sha256":sha(source/"screw-states.jsonl"),
        "panel_cut_actions_sha256":sha(source/"panel-cut-actions.jsonl")}
    context_path=source/"panel-reference-context.json"
    context=None
    if context_path.exists():
        if sha(context_path)!=receipt["output_sha256"].get(context_path.name):
            raise ValueError("Changed-axis panel geometry is not receipt-bound")
        context=json.loads(context_path.read_text())
        if context["schema"]!="panel_remedy_reference_context/v1" or context["screw_axis_count"] not in (66,98):
            raise ValueError("Unsupported panel-remedy reference context")
        binding["panel_reference_geometry_sha256"]=sha(context_path)
    result=api.correct_panel_sources(source/"screw-states.jsonl",source/"panel-cut-actions.jsonl",
        source_binding=binding,orientation="horizontal_strong_x",
        expected_screws_per_state=context["screw_axis_count"] if context else 66,
        expected_state_count=len(json.loads((source/"comparison.json").read_text())["states"]),
        panel_head_esg=context.get("head_pull_through_esg",0.42) if context else 0.42)
    compatible=module(HERE/"panel-compatible-response.py","current_horizontal_net_reference")
    data=compatible.static_sources()
    geometry=copy.deepcopy(data.geometry)
    if context:
        geometry=copy.deepcopy(context["geometry"])
    orientation_model=json.loads((HERE/"panel-width-operators-attempt01/model.json").read_text())
    data.model["material_binding"]["panel_axes"]=orientation_model["material_binding"]["panel_axes"]
    transforms=[]
    for name,panel in geometry["panels"].items():
        if not name.startswith("main_"):
            continue
        old_basis,old_bounds=panel["basis"],panel["bounds_mm"]
        panel["basis"]=[[-x for x in old_basis[1]],old_basis[0],old_basis[2]]
        panel["bounds_mm"]=[[-old_bounds[1][1],-old_bounds[1][0]],old_bounds[0],old_bounds[2]]
        for opening in panel["openings"]:
            for key in ("xy_mm","frozen_xy_mm"):
                if key in opening:
                    xy=opening[key]
                    opening[key]=[-xy[1],xy[0]]
        for axis,key in enumerate(("assumed_apa_direction_1_global_xyz","assumed_apa_direction_2_global_xyz")):
            if np.max(abs(np.asarray(panel["basis"][axis])-np.asarray(data.model["material_binding"]["panel_axes"][name][key])))>1e-10:
                raise ValueError("Net section basis differs from horizontal-grain material")
        transforms.append({"panel":name,"old_basis":old_basis,"new_basis":panel["basis"],
            "coordinate_transform":"new_x=-old_y; new_y=old_x; normal unchanged",
            "physical_geometry_changed":False})
    panel=data.definitions(compatible.PANEL,("size_factor","panel_reference"),
        {"math":__import__("math"),"LBF_N":data.local.N,"PSI_MPA":data.local.N/25.4**2},("BASE",))
    cuts=[json.loads(line) for line in (source/"panel-cut-actions.jsonl").read_text().splitlines()]
    rows,integration=data.local.net_rows(cuts,geometry,data.model,data.layers,panel,(1.,))
    with gzip.open(output/"net-panel-cuts.jsonl.gz","wt") as stream:
        for row in rows:
            stream.write(json.dumps(row,allow_nan=False)+"\n")
    peak=max(rows,key=lambda r:r["net_planar_shear_ratio"])
    result["current_equivalent_layer_net_sections"]={"rows":len(rows),"peak":peak,
        "rolling_shear_exceedances":sum(r["net_planar_shear_ratio"]>1. for r in rows),
        "section_integration":integration,"physical_coordinate_transforms":transforms,
        "D510F_350lbf_per_ft_reference_matches_frozen_PLANAR":abs(data.local.PLANAR-350.*data.local.N/304.8)<1e-12,
        "C_D":1.,"actual_panel_layup_or_transverse_properties_qualified":False,
        "frozen_net_void_geometry_retained":context is None,"complete_panel_acceptance":False}
    pins={str(p.relative_to(ROOT)):h for p,h in data.pins.items()}
    pins.update({str(p.relative_to(ROOT)):h for p,h in api.PINS.items()})
    for p in (Path(__file__),HERE/"panel-method-correction.py",source/"receipt.json",source/"comparison.json",
              source/"screw-states.jsonl",source/"panel-cut-actions.jsonl"):
        pins[str(p.relative_to(ROOT))]=sha(p)
    if context:
        pins[str(context_path.relative_to(ROOT))]=sha(context_path)
    write(output/"result.json",result)
    compatible.authenticate(data.pins)
    api._check_pins()
    write(output/"receipt.json",{"source_sha256":pins,
        "output_sha256":{p.name:sha(p) for p in output.iterdir() if p.is_file() and p.name!=".gitignore"},
        "no_frame_or_native_solve":True,"physical_release":False})
    print(json.dumps({"net_rolling_peak":peak["net_planar_shear_ratio"],"witness":
        {k:peak[k] for k in ("case_id","panel","cut_axis","station_absolute_local_mm")},
        "rows":len(rows),"result_sha256":sha(output/"result.json")},indent=2),flush=True)


def washer_census_fit(output,source):
    """Combine the proved 144 substitutions and recalculate exterior grip."""
    import csv
    api=module(HERE/"washer-stack-correction.py","current_washer_combined")
    api._check_pins()
    source=Path(source).resolve()
    receipt=json.loads((source/"receipt.json").read_text())
    pins={str(p.relative_to(ROOT)):h for p,h in api.PINS.items()}
    replacements={}
    for p in sorted(source.glob("*-result.json")):
        if sha(p)!=receipt["output_sha256"][p.name]:
            raise ValueError("Calculated stack result changed")
        row=json.loads(p.read_text())
        key=tuple(row["case"]["join_key"])
        if key in replacements:
            raise ValueError("Duplicate substituted washer end-state")
        replacements[key]={"index":row["stress_comparison"]["over_hypothetical_Fy250"],
            "source_result":str(p.relative_to(ROOT)),"sha256":sha(p)}
    if len(replacements)!=144:
        raise ValueError("Incomplete selected-end substitution")
    dispositions=json.loads((api.DISPOSITION_DIR/"summary.json").read_text())["end_dispositions"]
    combined=[]
    replaced=set()
    for row in dispositions:
        key=tuple(row["join_key"])
        if row.get("metal_reference_index") is None:
            continue
        original=row["metal_reference_index"]
        if key in replacements:
            replaced.add(key)
        combined.append({"join_key":list(key),"index":replacements[key]["index"] if key in replacements else original,
            "two_plate_result":replacements.get(key),"source_single_plate_index":original})
    if len(combined)!=2400 or replaced!=set(replacements):
        raise ValueError("Combined source census does not close")
    hardware_path=HERE.parent/"assembly-package/hardware_engagement.py"
    hardware=module(hardware_path,"current_washer_stack_grip")
    csv_path=hardware.OUT/"hardware-engagement-axes.csv"
    hardware_summary=hardware.OUT/"hardware-engagement.json"
    if sha(hardware_summary)!="93c24fe5fb421152b0294cc35106bfb6d595b558f45e0be826406405084c111a":
        raise ValueError("Current hardware fit packet changed")
    with csv_path.open() as stream:
        axes={r["axis_id"]:r for r in csv.DictReader(stream)}
    cases=api.load_current_cases(include_all_selected_end_states=True)
    affected=cases["fit_grip_impacts_by_axis"]
    fit=[]
    for item in affected:
        axis=item["axis_id"]
        old=axes[axis]
        catalog=hardware.STACKS[hardware.ROUTES[old["family_id"]][0]]
        old_min,old_max=catalog["washer"]["thickness_mm"]
        if axis.startswith("top_outer/"):
            new_head,new_nut=(5.,5.),(2.5,2.5)
            thickness_scope="Working-profile 2.5-mm washers; actual manufacturing range unqualified"
        else:
            new_head=new_nut=(2*old_min,2*old_max)
            thickness_scope="Published source washer minimum/maximum thickness ranges"
        head_delta=new_head[1]-old_max
        total_min_delta=new_head[0]+new_nut[0]-2*old_min
        total_max_delta=new_head[1]+new_nut[1]-2*old_max
        old_interval=json.loads(old["full_form_male_thread_required_interval_mm"])
        window=[old_interval[0]+total_min_delta,old_interval[1]+total_max_delta]
        three_pitch=window[1]+3*25.4/catalog["tpi"]
        nominal=float(old["proposed_nominal_order_length_mm"])
        listed=json.loads(old["listed_product_length_range_mm"]) if old["listed_product_length_range_mm"] else None
        members=json.loads(old["member_bearing_intervals"])
        for member in members:
            member["underhead_interval_mm"]=[x+head_delta for x in member["underhead_interval_mm"]]
            member["nds_nominal_D_quarter_thread_LB_min_mm"]+=head_delta
        fit.append({"axis_id":axis,"head_washer_count":2,"nut_washer_count":1 if axis.startswith("top_outer/") else 2,
            "thickness_scope":thickness_scope,"head_stack_mm":list(new_head),"nut_stack_mm":list(new_nut),
            "member_bearing_intervals":members,"required_LB_each_member_max_mm":float(old["required_LB_each_member_max_mm"])+head_delta,
            "smooth_shank_LB_through_all_shear_planes_mm":float(old["smooth_shank_LB_through_all_shear_planes_mm"])+head_delta,
            "full_form_male_thread_required_interval_mm":window,"physical_three_pitch_length_min_mm":three_pitch,
            "nominal_order_length_mm":nominal,"listed_length_range_mm":listed,
            "physical_nut_face_margin_at_nominal_length_mm":nominal-window[1],
            "physical_nut_face_margin_at_listed_min_mm":listed[0]-window[1] if listed else None,
            "three_pitch_margin_at_nominal_length_mm":nominal-three_pitch,
            "three_pitch_margin_at_listed_min_mm":listed[0]-three_pitch if listed else None,
            "actual_full_form_thread_and_LB_windows_verified":False,
            "three_pitch_is_declared_fit_scenario_not_universal_rule":True})
    output=output_directory(output)
    for p in (Path(__file__),HERE/"washer-stack-correction.py",hardware_path,csv_path,hardware_summary,source/"receipt.json"):
        pins[str(p.relative_to(ROOT))]=sha(p)
    result={"schema":"current_two_washer_combined_census_and_grip/v1","finite_fields":len(combined),
        "substituted_fields":len(replaced),"unchanged_finite_fields":len(combined)-len(replaced),
        "source_geometry_limits":96,"combined_peak":max(combined,key=lambda r:r["index"]),
        "stacked_peak":max((r for r in combined if r["two_plate_result"]),key=lambda r:r["index"]),
        "exceedances":sum(r["index"]>1. for r in combined),"affected_axes":len(fit),
        "additional_washers":sum(r["head_washer_count"]+r["nut_washer_count"]-2 for r in fit),
        "conditional_total_washers":208+sum(r["head_washer_count"]+r["nut_washer_count"]-2 for r in fit),
        "fit":fit,"longer_leg_candidate":{"url":"https://boltdepot.com/Product-Details?product=408",
            "nominal_length_mm":228.6,"listed_min_length_mm":224.536,
            "diameter_mm":12.7,"grade":"SAE J429 Grade5","fully_threaded":False,
            "minimum_listed_thread_length_mm":38.1,"candidate_selected":False,
            "actual_full_form_window_verified":False,"protrusion_and_access_not_rechecked":True},
        "force_basis":"Same saved wider-washer profile; no horizontal-grain or doubled-stack global force feedback",
        "actual_washer_Fy_qualified":False,"complete_joint_acceptance":False,"reviewed_geometry_changed":False,"physical_release":False}
    write(output/"result.json",result)
    api._check_pins()
    write(output/"receipt.json",{"source_sha256":pins,
        "output_sha256":{p.name:sha(p) for p in output.iterdir() if p.is_file() and p.name!=".gitignore"},
        "no_new_solve":True,"physical_release":False})
    print(json.dumps({"combined_peak":result["combined_peak"]["index"],"stacked_peak":result["stacked_peak"]["index"],
        "fields":len(combined),"exceedances":result["exceedances"],"additional_washers":result["additional_washers"],
        "sha256":sha(output/"result.json")},indent=2),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=("washers","horizontal-frame","panel-references","washer-census-fit"))
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--all-end-states",action="store_true")
    parser.add_argument("--retry-source",type=Path)
    parser.add_argument("--solver-feas-tol",type=float)
    parser.add_argument("--source",type=Path)
    args=parser.parse_args()
    sys.path[:0]=[str(ROOT),str(HERE.parent)]
    if args.stage=="washers":
        washers(args.output,args.all_end_states)
    elif args.stage=="horizontal-frame":
        horizontal_frame(args.output,args.retry_source,args.solver_feas_tol)
    elif args.stage=="panel-references":
        panel_references(args.output,args.source)
    else:
        washer_census_fit(args.output,args.source)
