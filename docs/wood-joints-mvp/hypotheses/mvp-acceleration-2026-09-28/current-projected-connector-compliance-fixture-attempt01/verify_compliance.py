#!/usr/bin/env python3
"""Known-answer fixture for projected connector compliance and rigid balance."""
import argparse, hashlib, importlib.util, json
from pathlib import Path
import numpy as np
import scipy, scipy.linalg as la, scipy.sparse as sp

HERE=Path(__file__).resolve().parent
P=HERE.parent
CUBE=P/'current-free-c3d20-matrix-export-native-attempt01'
OLD=P/'current-free-body-elastic-condensation-fixture-attempt01'
PARSER=P/'current-native-elastic-operator-export-preflight-attempt01'/'matrix_export_oracle.py'
HELPER=P/'current-frame-free-body-condensation-preflight-attempt01'/'condensation.py'
ROTATION_SCALE_MM=1000.

def mod(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    old=mod(OLD/'verify_condensation.py','old_cube_oracle')
    if old.run()!=json.loads((OLD/'assessment.json').read_text()): raise ValueError('prior cube oracle changed')
    helper=mod(HELPER,'shared_free_body_solver')
    parser=mod(PARSER,'cube_matrix_parser'); labels=parser.read_dof_map(CUBE/'model.dof')
    Ks,_=parser.read_symmetric_triplets(CUBE/'model.sti',len(labels)); K=sp.csr_matrix(Ks).toarray()
    packet=json.loads((CUBE/'model.json').read_text()); xyz,center,R=old.make_rigid_modes(labels,packet['nodes'])
    node_xyz={int(n):x for n,x in packet['nodes'].items()}
    _,Rscaled,Qrigid=helper.rigid_basis(labels,node_xyz,ROTATION_SCALE_MM)
    Q=la.null_space(R.T); Kr=Q.T@K@Q; Kplus=Q@la.solve(Kr,Q.T,assume_a='pos'); row={lab:i for i,lab in enumerate(labels)}
    labs=[(node,d) for node in (1,2,4) for d in (1,2,3)]; B=np.zeros((len(labs),len(labels)))
    for i,lab in enumerate(labs): B[i,row[lab]]=1.
    factor,system=helper.factor_bordered(sp.csr_matrix(K),Rscaled)
    raw_source=B.T; projected_source=raw_source-Qrigid@(Qrigid.T@raw_source)
    hsolve=helper.solve_bordered_chunk(factor,system,Rscaled,projected_source,ROTATION_SCALE_MM)
    if hsolve['status']!='PASS_BALANCED_FREE_BODY': raise ValueError(f'projected source columns failed bordered solve: {hsolve}')
    H=B@hsolve['displacement_mm']; H_dense=B@Kplus@B.T
    Dscaled=B@Rscaled; D=B@R; raw_wrench_map=R.T@raw_source
    strains=old.strain_basis(); E=packet['material']['E_N_per_mm2']; nu=packet['material']['nu']
    lam=nu*E/((1+nu)*(1-2*nu)); mu=E/(2*(1+nu))
    stress=[lam*np.trace(e)*np.eye(3)+2*mu*e for e in strains]
    F=np.column_stack([old.face_traction_load(labels,s) for s in stress]); W=R.T@F
    fsolve=helper.solve_bordered_chunk(factor,system,Rscaled,F,ROTATION_SCALE_MM)
    if fsolve['status']!='PASS_BALANCED_FREE_BODY': raise ValueError(f'balanced analytic load columns failed: {fsolve}')
    e=B@fsolve['displacement_mm']; e_dense=B@Kplus@F
    affine=np.column_stack([old.affine_field(labels,xyz,center,x) for x in strains]); e_ref=B@(Q@(Q.T@affine))
    H2=H[np.ix_([0,3],[0,3])]; old_H=np.asarray(json.loads((OLD/'assessment.json').read_text())['two_source_row_condensation']['projected_compliance_mm_per_N'])
    Dref=np.zeros_like(D)
    for i,(node,d) in enumerate(labs):
        Dref[i,:3]=np.eye(3)[d-1]; Dref[i,3:]=np.cross(np.eye(3),xyz[node]-center)[:,d-1]
    Dconversion=Dscaled.copy(); Dconversion[:,3:]*=ROTATION_SCALE_MM
    errs={'sparse_H_vs_dense_QKQ_max':float(np.max(np.abs(H-H_dense))), 'sparse_H_2row_vs_saved_dense_QKQ':float(np.max(np.abs(H2-old_H))), 'sparse_e_vs_dense_QKQ_max':float(np.max(np.abs(e-e_dense))), 'sparse_e_vs_affine_QKQ_max':float(np.max(np.abs(e-e_ref))), 'D_vs_source_rigid_fields':float(np.max(np.abs(D-Dref))), 'D_scaled_rotation_conversion_max':float(np.max(np.abs(D-Dconversion)))}
    if max(errs.values())>2e-9 or np.min(la.eigvalsh((H+H.T)/2)) < -1e-9: raise ValueError(f'compliance map mismatch: {errs}')
    f=np.zeros(len(labs)); f[0]=.7; f[3]=-.7; F0=F[:,0]; g=F0-B.T@f
    if np.max(np.abs(R.T@g))>1e-10: raise ValueError('balanced traction/source combination has residual wrench')
    a=np.array([.1,-.05,.03,.01,-.015,.02]); ascaled=a.copy(); ascaled[3:]*=ROTATION_SCALE_MM
    gsolve=helper.solve_bordered(factor,system,Rscaled,g,ROTATION_SCALE_MM)
    if gsolve['status']!='PASS_BALANCED_FREE_BODY': raise ValueError(f'balanced combined body load failed: {gsolve}')
    u=Rscaled@ascaled+gsolve['displacement_mm']
    q_direct=B@u; q_map=Dscaled@ascaled+e[:,0]-H@f; ku=float(np.max(np.abs(K@u-g)))
    work=float(abs(f@q_direct-(B.T@f)@u)); formula=float(np.max(np.abs(q_direct-q_map)))
    fpoint=np.zeros(len(labs)); fpoint[0]=1.; Fpoint=np.zeros(len(labels)); Fpoint[row[(1,1)]]=1.
    Wpoint=R.T@Fpoint; balance=float(np.max(np.abs(Wpoint-D.T@fpoint))); gp=Fpoint-B.T@fpoint
    point_proj=Fpoint-Qrigid@(Qrigid.T@Fpoint)
    point_solve=helper.solve_bordered(factor,system,Rscaled,point_proj,ROTATION_SCALE_MM)
    if point_solve['status']!='PASS_BALANCED_FREE_BODY': raise ValueError('projected point-load elastic solve failed')
    ep_sparse=B@point_solve['displacement_mm']; ep_dense=B@Kplus@Fpoint
    up=Rscaled@ascaled+np.zeros(len(labels)); qp=Dscaled@ascaled+ep_sparse-H@fpoint
    point={'status':'PASS_BALANCED_BODY_LOAD' if balance<1e-12 and np.max(np.abs(gp))<1e-12 else 'REJECT', 'W_N_and_Nmm':Wpoint.tolist(), 'D_transpose_f_N_and_Nmm':(D.T@fpoint).tolist(), 'raw_balance_residual':balance, 'projected_e_vs_dense_QKQ_mm':float(np.max(np.abs(ep_sparse-ep_dense))), 'projected_e_is_physical_alone':False, 'combined_physical_Ku_minus_load_max_N':float(np.max(np.abs(K@up-gp))), 'combined_q_map_error_mm':float(np.max(np.abs(B@up-qp))), 'combined_load_is_zero':bool(np.max(np.abs(gp))<1e-12)}
    fbad=np.zeros(len(labs)); fbad[0]=1.; Wzero=np.zeros(6); mismatch=float(np.max(np.abs(D.T@fbad-Wzero))); raw_bad=R.T@(-B.T@fbad)
    if formula>2e-9 or work>2e-9 or ku>2e-9 or point['status']!='PASS_BALANCED_BODY_LOAD' or mismatch<1e-3: raise ValueError('balanced/unbalanced connector fixture failed')
    return {'status':'PASS_PROJECTED_CONNECTOR_COMPLIANCE_FIXTURE','source_sha256':{'prior_oracle':sha(OLD/'verify_condensation.py'),'prior_assessment':sha(OLD/'assessment.json'),'shared_sparse_helper':sha(HELPER),'cube_stiffness':sha(CUBE/'model.sti'),'cube_dof':sha(CUBE/'model.dof')},'operator_used':'Shared sparse bordered factor/solve [K Rscaled; Rscaled.T 0], with only raw source columns projected by P=I-Qrigid Qrigid.T before their elastic solves.','rows':[f'{n}.{d}' for n,d in labs],'units':{'H':'mm/N','e':'mm','D':'mm per generalized translation-mm or rotation-radian','W':'N and Nmm','R':'translations mm; rotations rad'},'H_mm_per_N':H.tolist(),'H_dense_QKQ_reference_mm_per_N':H_dense.tolist(),'H_sparse_solve_residual_relative':hsolve['max_kkt_relative_residual'],'H_source_column_projection_max_Rscaled_transpose_load_N':float(np.max(np.abs(Rscaled.T@projected_source))),'e_mm_six_analytic_face_loads':e.tolist(),'e_dense_QKQ_reference_mm':e_dense.tolist(),'e_sparse_solve_residual_relative':fsolve['max_kkt_relative_residual'],'D_rigid_row_map_physical_rotation_radians':D.tolist(),'D_rigid_row_map_scaled_1000mm_radians':Dscaled.tolist(),'D_transpose_source_force_to_raw_wrench_N_and_Nmm':raw_wrench_map.tolist(),'six_analytic_case_W_R_transpose_F_N_and_Nmm':W.tolist(),'six_case_max_abs_W':float(np.max(np.abs(W))),'dense_QKQ_comparisons':errs,'H_reciprocity_max_abs':float(np.max(np.abs(H-H.T))),'H_min_eigenvalue_mm_per_N':float(np.min(la.eigvalsh((H+H.T)/2))),'balanced_source_combination':{'f_body_on_interface_N':f.tolist(),'raw_balance_max_N_or_Nmm':float(np.max(np.abs(R.T@g))),'q_Da_plus_e_minus_Hf_error_mm':formula,'Ku_minus_F_plus_Btf_max_N':ku,'dual_work_error_Nmm':work},'nonzero_W_point_load_balanced_by_connector':point,'unbalanced_connector_only':{'status':'REJECT_UNBALANCED_COMBINATION','F_wrench_W_N_and_Nmm':Wzero.tolist(),'D_transpose_f_N_and_Nmm':(D.T@fbad).tolist(),'body_load_wrench_R_transpose_F_minus_Btf':raw_bad.tolist(),'balance_residual_max':mismatch,'physical_displacement_computed':False,'projected_H_column_is_physical_response':False},'equilibrium_contract':'For physical use require D.T f = W, equivalently R.T(F-B.T f)=0; preserve W and raw R.T B.T source-wrench columns. P=QQ.T is only the elastic-basis projector used inside K+, never a replacement for physical load balance.','mechanical_acceptance':False,'numpy_version':np.__version__,'scipy_version':scipy.__version__}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--verify',action='store_true'); args=ap.parse_args(); result=run(); out=HERE/'assessment.json'
    if args.verify:
        if json.loads(out.read_text())!=result: raise SystemExit('saved compliance fixture does not replay')
        print('PASS_REPLAY_PROJECTED_CONNECTOR_COMPLIANCE_FIXTURE')
    else: out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n'); print(result['status'])
if __name__=='__main__': main()
