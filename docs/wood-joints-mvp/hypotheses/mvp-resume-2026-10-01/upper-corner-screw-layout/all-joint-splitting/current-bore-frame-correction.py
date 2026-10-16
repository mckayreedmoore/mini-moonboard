"""Parent-only intact true-wood cut-cell correction, with assembled restraint.

Restores positive-volume cells, integrates stiffness outside exact bore voids,
maps physical port/external footprints only to wood nodes, and recovers stress
on the same material quadrature. The source C3D20 grid stays explicitly finite;
quadrature refinement is not represented as mesh or strength convergence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
UPPER=HERE.parent
ROOT=UPPER.parents[4]
RAW=HERE/"rawlocal/coupled-family-completion"
GEOMETRY=HERE/"rawlocal/splitting-capacity-completion/coupled-prepared01/geometry.json"


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+"\n")


def wood_nodes(np,nodes,geometry):
    retained=np.ones(len(nodes),dtype=bool)
    for bore in geometry["bores"]:
        direction=np.asarray(bore["axis"])
        delta=nodes-bore["origin"]
        axial=delta@direction
        radial=np.linalg.norm(delta-axial[:,None]*direction,axis=1)
        retained &= ~((axial>=bore["interval_mm"][0]-1e-8)&(axial<=bore["interval_mm"][1]+1e-8)
                       &(radial < bore["radius_mm"]-1e-8))
    return np.flatnonzero(retained)


def physical_maps(np,sparse,family,mesh,geometry,body,terms):
    nodes,elements=mesh["nodes_mm"],mesh["elements"]
    live=wood_nodes(np,nodes,geometry)
    live_mask=np.zeros(len(nodes),dtype=bool)
    live_mask[live]=True
    localB,active,port_audit=family.map_port_basis(np,sparse,None,nodes[live],geometry,terms,
        body["B"].shape[0],1,0.,body)
    local_dofs=(3*live[:,None]+np.arange(3)).ravel()
    expand=sparse.coo_matrix((np.ones(len(local_dofs)),(np.arange(len(local_dofs)),local_dofs)),
                             shape=(len(local_dofs),3*len(nodes))).tocsr()
    B=localB@expand
    # The native body-load basis has an unobserved consistent FE footprint.
    # Preserve all its affine work targets on positive sound-volume weights.
    weights=np.zeros(len(nodes))
    for e,bounds,bore_index in zip(elements,mesh["element_bounds_mm"],mesh["element_bore_indices"],strict=True):
        volume=float(np.prod(bounds[1]-bounds[0]))
        if bore_index is not None:
            volume-=module_cache["cut"].exact_cylinder_void_volume_mm3(bounds[0],bounds[1],geometry["bores"][bore_index])
        eligible=e[live_mask[e]]
        if len(eligible):
            weights[eligible]+=volume/len(eligible)
    chosen=live[(weights[live]>0.)&(abs(nodes[live,1])>1e-7)]
    targets=family.affine_targets(np,body["F"],body)
    frame=np.asarray(geometry["frame"])
    world=np.asarray(geometry["start"])+nodes[chosen]@frame
    F=np.zeros((3*len(nodes),12))
    audits=[]
    for column in range(12):
        target=targets[:,:,column]
        if np.max(abs(target),initial=0.)<1e-14:
            audits.append({"column":column,"zero_load":True})
            continue
        values,audit=family.affine_distribution(np,sparse,world,target,body["datum_mm"],weights[chosen]/weights[chosen].max())
        F[(3*chosen[:,None]+np.arange(3)).ravel(),column]=(values@frame.T).ravel()
        audits.append({"column":column,**audit})
    return B,active,F,{"port":port_audit,"external":audits,
        "void_nodes_excluded_from_physical_footprints":len(nodes)-len(live),
        "sound_volume_weighted_external_affine_work_preserved":True}


module_cache={}


def assembly(np,sparse,cut,brick,nodes,elements,bore_indices,geometry,constants,order,event):
    axes={"L":[1.,0.,0.],"R":[0.,1.,0.],"T":[0.,0.,1.]}
    C=brick.engineering_stiffness(constants,axes)
    cache={}
    rows,columns,values=[],[],[]
    element_keys=[]
    max_volume_error,max_moment_error=0.,0.
    for number,(e,bore_index) in enumerate(zip(elements,bore_indices,strict=True)):
        p=nodes[e]
        center=p.mean(axis=0)
        relative=p-center
        bore=geometry["bores"][bore_index] if bore_index is not None else None
        signature=(tuple(np.round(relative.ravel(),8)),None if bore is None else
            (tuple(np.round(np.asarray(bore["origin"])-center,8)),tuple(bore["axis"]),
             tuple(bore["interval_mm"]),bore["radius_mm"]))
        if signature not in cache:
            rule=cut.c3d20_cylinder_cut_rule(p,bore,order=order)
            if not len(rule["natural_points"]):
                raise ValueError("Positive-material mesh cell has empty quadrature: "+str(number))
            K,_=cut.c3d20_element_stiffness(p,C,rule)
            operator,_=cut._c3d20_B_matrices(p,rule["natural_points"])
            CB=np.einsum("ab,qbi->qai",C,operator)
            cache[signature]={"K":K,"CB":CB,"natural_points":rule["natural_points"],
                "physical_relative_points":rule["physical_points_mm"]-center,
                "weights_mm3":rule["weights_mm3"],"report":rule["report"]}
        entry=cache[signature]
        element_keys.append(signature)
        max_volume_error=max(max_volume_error,entry["report"]["relative_volume_error"])
        max_moment_error=max(max_moment_error,entry["report"]["moment_error_vs_2x_order"])
        dofs=(3*e[:,None]+np.arange(3)).ravel()
        rows.append(np.repeat(dofs,60))
        columns.append(np.tile(dofs,60))
        values.append(entry["K"].ravel())
        if number%1000==0:
            event("assemble",elements_completed=number,unique_quadrature_cells=len(cache),order=order)
    K=sparse.coo_matrix((np.concatenate(values),(np.concatenate(rows),np.concatenate(columns))),
                        shape=(3*len(nodes),)*2).tocsr()
    audit={"quadrature_order":order,"unique_element_rules":len(cache),
        "maximum_relative_cell_volume_error":max_volume_error,"maximum_moment_error_vs_double_order":max_moment_error,
        "stiffness_uses_exact_material_domain":True,"stress_uses_same_material_rule":True}
    return K,cache,element_keys,audit


def full_cell_coupon(np,cut,brick,constants):
    from fea.floor_recess_mesh import CORNERS, EDGES
    nodes=np.vstack((CORNERS,EDGES))*[2.5,.9125,.9125]
    axes={"L":[1.,0.,0.],"R":[0.,1.,0.],"T":[0.,0.,1.]}
    C=brick.engineering_stiffness(constants,axes)
    rule=cut.c3d20_cylinder_cut_rule(nodes,None,order=4)
    current,_=cut.c3d20_element_stiffness(nodes,C,rule)
    original,_=brick.brick_stiffness(nodes,constants,axes)
    difference=float(np.max(abs(current-original))/np.max(abs(original)))
    if difference>1e-12:
        raise ValueError("Uncut C3D20 stiffness differs from the pinned assembler")
    return {"uncut_C3D20_maximum_relative_K_difference":difference,
        "standard_full_cell_3x3x3_integration_retained":True}


def run(output,side,orders=(4,8)):
    import numpy as np
    from scipy import sparse
    from scipy.linalg import qr
    from scipy.sparse.linalg import splu
    output=Path(output).resolve()
    if output.exists() or not output.is_relative_to((HERE/"rawlocal").resolve()):
        raise ValueError("Fresh ignored output required")
    started=time.monotonic()
    output.mkdir(parents=True)
    (output/".gitignore").write_text("*\n")
    (output/"producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    def event(stage,**details):
        record={"stage":stage,"elapsed_seconds":time.monotonic()-started,**details}
        write(output/"progress.json",record)
        print(json.dumps(record),flush=True)
    family=module(HERE/"coupled-family-completion.py","current_cut_source_family")
    core=module(UPPER/"joint-frame-member-replacement.py","current_cut_replacement")
    cut=module(HERE/"bore-domain-correction.py","current_cut_domain")
    module_cache["cut"]=cut
    prototype=module(family.PROTOTYPE,"current_cut_pinned_prototype")
    _,_helper,_,_,_,_,_,_,scenario,brick,pins=prototype.setup()
    constants=scenario()["calculix_engineering_constants"]
    write(output/"known-answer.json",{"full_cell":full_cell_coupon(np,cut,brick,constants),
        "assembled_replacement_and_energy":core.known_answer(),
        "bore_rule_regression_command":".venv/bin/python -B "+str((HERE/"check-bore-domain-correction.py").relative_to(ROOT))})
    cache_path=UPPER/"rawlocal/joint-frame-member-replacement"/("source-body-"+side+"01")
    old_path=UPPER/"rawlocal/joint-frame-member-replacement"/("source-check01" if side=="left" else "source-check-right01")
    old_receipt=json.loads((old_path/"receipt.json").read_text())
    old_operator_path=old_path/"old-body-operators.npz"
    if sha(old_operator_path)!=old_receipt["output_sha256"][old_operator_path.name]:
        raise ValueError("Original body operator bytes changed")
    resolutions=[]
    body=family.cached_body(core,cache_path,pins,resolutions)
    name="center_post_cleat_"+side
    if body["member_id"]!=name:
        raise ValueError("Body/side mismatch")
    geometry=json.loads(GEOMETRY.read_text())[name]
    prior=RAW/(side+"-u20-operators-recovered01")/"intact-operator.npz"
    terms_path=RAW/("eligible-prepared02" if side=="left" else "right-central-control-prepared02")/"physical-port-terms.json"
    terms=json.loads(terms_path.read_text())["terms"]
    for path in (Path(__file__),HERE/"bore-domain-correction.py",HERE/"check-bore-domain-correction.py",GEOMETRY,
                 prior,terms_path,old_operator_path,cache_path/"receipt.json",UPPER/"panel-method-correction.py"):
        pins[path]=sha(path)
    for path in (HERE/"bore-domain-correction.py",HERE/"check-bore-domain-correction.py",UPPER/"panel-method-correction.py"):
        (output/(path.name+".snapshot")).write_bytes(path.read_bytes())
    with np.load(prior,allow_pickle=False) as previous:
        coordinates=previous["nodes_mm"][previous["elements"][:,:8]]
        original_grids=[np.unique(np.r_[coordinates[:,:,k].min(axis=1),coordinates[:,:,k].max(axis=1)]) for k in range(3)]
        grids=[np.unique(np.round(g,9)) for g in original_grids]
        grid_roundoff=max(float(np.max(abs(g-np.round(g,9)))) for g in original_grids)
        if grid_roundoff>1e-8:
            raise ValueError("Coincident-grid cleanup would move physical cell boundaries")
    mesh=cut.positive_volume_c3d20_mesh(*grids,geometry)
    nodes,elements=mesh["nodes_mm"],mesh["elements"]
    census={k:v for k,v in mesh.items() if k not in ("nodes_mm","elements","element_bore_indices","element_bounds_mm",
                                                   "element_material_volume_fractions")}
    census.update(nodes=len(nodes),elements=len(elements),grid_scope="Frozen20mm transverse / maximum80mm grain grid with exact bore partitions")
    census.update(coincident_grid_coordinates_merged=[len(a)-len(b) for a,b in zip(original_grids,grids,strict=True)],
                  maximum_grid_coordinate_roundoff_mm=grid_roundoff)
    if abs(mesh["relative_volume_error"])>1e-8:
        raise ValueError("True-wood domain does not reproduce the exact STEP volume")
    R,Q,_=family.rigid_basis(np,nodes,geometry,body["datum_mm"])
    B,active,F,mapping=physical_maps(np,sparse,family,mesh,geometry,body,terms)
    if np.max(abs(B@R-body["D"]))>=1e-8 or np.max(abs(R.T@F-body["W"]))>=1e-8:
        raise ValueError("Mapped physical rigid work differs")
    write(output/"geometry-mapping.json",{"mesh":census,"mapping":mapping,"active_ports":active.tolist()})
    raw=np.column_stack((B[active].T.toarray(),F))
    projected=raw-Q@(Q.T@raw)
    fixed=qr(Q.T,mode="economic",pivoting=True)[2][:6]
    free=np.setdiff1d(np.arange(len(R)),fixed)
    with np.load(old_operator_path,allow_pickle=False) as old_arrays:
        old={k:old_arrays[k].copy() for k in ("H","e","L","D","W")}
    follow=module(UPPER/"joint-frame-profile-followup.py","current_cut_profile")
    for key,digest in follow.source_bindings().items():
        path=ROOT/key
        if path in pins and pins[path]!=digest:
            raise ValueError("Frame source binding conflicts with local-body source")
        pins[path]=digest
    frame=follow.profile_frame(core)
    orientation=module(UPPER/"panel-method-correction.py","current_cut_horizontal_panel")
    frame["H"],frame["e"],orientation_audit=orientation.apply_cached_strong_x_delta(
        frame["H"],frame["e"],frame["joint"]["old_kept_lumped_rows"])
    frame=core.attach_body_load_energy(frame,[old],unchanged_constant_token=frame["unchanged_constant_token"])
    baseline=UPPER/"rawlocal/current-method-corrections/horizontal03"
    baseline_receipt=baseline/"receipt.json"
    pins[baseline_receipt]=sha(baseline_receipt)
    receipt=json.loads(baseline_receipt.read_text())
    for filename in ("comparison.json","response.npz"):
        path=baseline/filename
        if sha(path)!=receipt["output_sha256"][filename]:
            raise ValueError("Horizontal baseline bytes differ from their receipt")
        pins[path]=sha(path)
    baseline_result=json.loads((baseline/"comparison.json").read_text())
    if not any(s["state_tag"]=="a12-forward_zero" and s["audit"]["all_passed"] for s in baseline_result["states"]):
        raise ValueError("Horizontal source state not audited")
    with np.load(baseline/"response.npz",allow_pickle=False) as response:
        bearing=response["a12-forward_zero_bearing"].copy()
    write(output/"input-plan.json",{"source_sha256":{family.source_key(p):h for p,h in pins.items()},
        "body":name,"state":"a12-forward_zero","orders":list(orders),"mesh":census,
        "orientation_audit":orientation_audit,"Ft90_mpa_hypothesis":.5,
        "RT_binding":"R=u,T=v only; alternate RT binding not evaluated",
        "actual_Ft90_or_splitting_resistance":None,"physical_geometry_changed":False,
        "no_external_native_executable_launched":True,"maximum_body_factors":len(orders)})
    results=[]
    for order in orders:
        event("corrected_stiffness",body=name,order=order)
        K,cache,element_keys,assembly_audit=assembly(np,sparse,cut,brick,nodes,elements,mesh["element_bore_indices"],
            geometry,constants,order,event)
        rigid_leak=float(np.max(abs(K@Q)))
        if rigid_leak>1e-5:
            raise ValueError("Corrected material domain lost rigid modes")
        event("body_factor",dofs=len(free),nonzeros=K.nnz,order=order)
        diagonal=K.diagonal()[free]
        if np.any(diagonal<=0.):
            raise ValueError("An active material degree has no positive energy")
        scale=1./np.sqrt(diagonal)
        scaling=sparse.diags(scale)
        scaled_K=(scaling@K[free][:,free]@scaling).tocsc()
        # This material energy operator is symmetric positive definite after
        # the six rigid gauges. Symmetric ordering with zero threshold avoids
        # asymmetric pivot fill; physical residual/gauge gates remain exact.
        factor=splu(scaled_K,permc_spec="MMD_AT_PLUS_A",diag_pivot_thresh=0.,
                    options={"SymmetricMode":True,"IterRefine":"DOUBLE"})
        event("body_factor_complete",stored_factor_nonzeros=int(factor.nnz),order=order)
        U=np.zeros_like(projected)
        U[free]=scale[:,None]*factor.solve(scale[:,None]*projected[free])
        for _ in range(3):
            correction=projected[free]-K[free]@U
            if np.max(abs(correction))<1e-6:
                break
            U[free]+=scale[:,None]*factor.solve(scale[:,None]*correction)
        U-=Q@(Q.T@U)
        U-=Q@(Q.T@U)
        residual=K@U-projected
        maximum_residual=float(np.max(abs(residual)))
        gauge=float(np.max(abs(R.T@U)))
        if maximum_residual>1e-5 or gauge>2e-10:
            raise ValueError("Corrected quotient force/gauge audit failed")
        audit={"all_passed":True,"failed_gates":[],"maximum_projected_force_residual_n":maximum_residual,
            "maximum_R_transpose_U_mm":gauge,"maximum_KQ_rigid_leak_n_per_mm":rigid_leak,
            "linear_factor_settings":{"diagonal_energy_scaling":True,"permc_spec":"MMD_AT_PLUS_A",
                "diag_pivot_thresh":0.,"SymmetricMode":True,"IterRefine":"DOUBLE"}}
        target=core.reduce_body_from_solutions(B,F,R,U[:,:len(active)],U[:,len(active):],audit,active,K)
        stored_factor_nonzeros=int(factor.nnz)
        del factor,scaled_K,scaling
        assembled=core.replacement(frame,old,target)
        coefficient=core.load_coefficients("a12-forward",frame["dead_load_factor"])
        solver=core.compatibility()
        event("assembled_state",order=order,state="a12-forward_zero")
        f,q,a,details,frame_audit=solver.fixed_floor_branch(assembled["H"],assembled["D"],assembled["e"]@coefficient,
            assembled["W"]@coefficient,assembled["joint"],bearing,0.,solver.REFINEMENT_SETTINGS)
        if not frame_audit["all_passed"]:
            raise ValueError("Corrected assembled state failed unchanged physics audit")
        recovered=U[:,len(active):]@coefficient-U[:,:len(active)]@f[active]
        force=F@coefficient-B.T@f
        node_residual=float(np.max(abs(K@recovered-force)))
        if node_residual>.1:
            raise ValueError("Corrected full-body equilibrium failed")
        maximum=0.
        witness=None
        for number,(e,signature) in enumerate(zip(elements,element_keys,strict=True)):
            entry=cache[signature]
            stress=entry["CB"]@recovered[(3*e[:,None]+np.arange(3)).ravel()]
            principal=.5*(stress[:,1]+stress[:,2])+np.sqrt(.25*(stress[:,1]-stress[:,2])**2+stress[:,5]**2)
            point=int(principal.argmax())
            if principal[point]>maximum:
                maximum=float(principal[point])
                local=nodes[e].mean(axis=0)+entry["physical_relative_points"][point]
                witness={"element":number,"local_g_u_v_mm":local.tolist(),"natural":entry["natural_points"][point].tolist(),
                    "stress_g_u_v_gu_gv_uv_mpa":stress[point].tolist(),
                    "sample_is_true_wood":bool(len(wood_nodes(np,local[None,:],geometry))==1)}
        if witness is None or not witness["sample_is_true_wood"]:
            raise ValueError("Corrected stress peak is not in wood")
        result={"body":name,"state_tag":"a12-forward_zero","quadrature_order":order,"mesh":census,
            "RT_binding":"R=u,T=v only",
            "sampled_sigma90_mpa":maximum,"hypothetical_Ft90_mpa":.5,"conditional_initiation_index":maximum/.5,
            "stress_witness":witness,"assembly_audit":assembly_audit,"quotient_audit":audit,
            "original_assembled_physical_audit":frame_audit,"full_body_residual_n":node_residual,
            "solver":details,"stored_factor_nonzeros":stored_factor_nonzeros,
            "stress_mesh_convergence_established":False,"actual_splitting_capacity_established":False,
            "physical_geometry_changed":False,"physical_release":False}
        results.append(result)
        write(output/("order"+str(order)+"-result.json"),result)
        np.savez_compressed(output/("order"+str(order)+"-fields.npz"),nodes_mm=nodes,elements=elements,
            recovered_U_mm=recovered,force_n=force,frame_force_n=f,frame_motion_mm=q,frame_rigid_scaled_mm=a)
        event("true_wood_field_saved",order=order,sigma90_mpa=maximum,index=maximum/.5)
        del K,U,residual,cache,element_keys,assembled,target
    family.authenticate(pins)
    summary={"schema":"current_bore_domain_assembled_correction/v1","status":"COMPLETED_TRUE_WOOD_DOMAIN_QUADRATURE_COMPARISON",
        "body":name,"results":results,"relative_peak_change_4_to_8":abs(results[-1]["sampled_sigma90_mpa"]/results[0]["sampled_sigma90_mpa"]-1.),
        "RT_binding":"R=u,T=v only; alternate RT binding not evaluated",
        "mesh_convergence_established":False,"actual_Ft90_known":False,"full_joint_or_splitting_acceptance":False,
        "elapsed_seconds":time.monotonic()-started,"physical_release":False}
    write(output/"summary.json",summary)
    write(output/"receipt.json",{"schema":"current_bore_frame_correction_receipt/v1","status":summary["status"],
        "source_sha256":{family.source_key(p):h for p,h in pins.items()},
        "output_sha256":{p.name:sha(p) for p in output.iterdir() if p.is_file() and p.name!=".gitignore"},"physical_release":False})
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--side",choices=("left","right"),required=True)
    args=parser.parse_args()
    sys.path[:0]=[str(ROOT),str(UPPER.parent)]
    resource.setrlimit(resource.RLIMIT_AS,(10*1024**3,resource.getrlimit(resource.RLIMIT_AS)[1]))
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError("Parent bounded correction expired")))
    signal.alarm(1800)
    try:
        result=run(args.output,args.side)
        print(json.dumps({"body":result["body"],"indices":[r["conditional_initiation_index"] for r in result["results"]],
            "relative_peak_change":result["relative_peak_change_4_to_8"]},indent=2),flush=True)
    except BaseException as error:
        if args.output.exists():
            write(args.output/"stop.json",{"exception":type(error).__name__,"message":str(error),
                "accepted_corrected_strength_field":False,"physical_failure_claimed":False})
        raise
