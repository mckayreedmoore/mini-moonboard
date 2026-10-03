#!/usr/bin/env python3
"""Replay bounded refinement fixtures and verify, but do not solve, parent inputs."""
import argparse, hashlib, importlib.util, json
from pathlib import Path
import numpy as np
import scipy, scipy.linalg as la, scipy.sparse as sp
import scipy.sparse.linalg as sla

from bounded_refinement import refine_existing_factor, solve_bordered_chunk_refined

HERE=Path(__file__).resolve().parent
P=HERE.parent
ROOT=HERE.parents[4]
CUBE=P/'current-free-c3d20-matrix-export-native-attempt01'
ORACLE=P/'current-free-body-elastic-condensation-fixture-attempt01'
PARSER=P/'current-native-elastic-operator-export-preflight-attempt01'/'matrix_export_oracle.py'
HELPER=P/'current-frame-free-body-condensation-preflight-attempt01'/'condensation.py'
CASE=P/'current-bordered-refinement-parent-case-attempt01'
ROTATION_SCALE_MM=1000.

def mod(path,name):
    spec=importlib.util.spec_from_file_location(name,path); value=importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_parent_case():
    case=json.loads((CASE/'case.json').read_text())
    for rel,want in case['source_sha256'].items():
        if sha(ROOT/rel)!=want: raise ValueError(f'parent-case source changed: {rel}')
    for name,want in case['outputs_sha256'].items():
        if sha(CASE/name)!=want: raise ValueError(f'parent-case output changed: {name}')
    K=sp.load_npz(CASE/'body-K.npz')
    with np.load(CASE/'basis.npz',allow_pickle=False) as z: R,raw,balanced=(z[k].copy() for k in ('R','raw','balanced'))
    if K.shape!=(6567,6567) or K.nnz!=920143 or R.shape!=(6567,6) or raw.shape!=(6567,16) or balanced.shape!=raw.shape: raise ValueError('exact parent-case shapes changed')
    contract=json.loads((P/'current-frame-physical-connector-projection-contract-attempt01'/'projection-contract.json').read_text())
    positions=case['source_row_positions']; records=[contract['rows'][i] for i in positions]
    if positions!=list(range(268,276))+list(range(568,576)): raise ValueError('source-position sequence changed')
    if [r['source_group'] for r in records]!=case['source_group_names']: raise ValueError('source groups no longer match exact positions')
    q,_=np.linalg.qr(R,mode='reduced'); projected=raw-q@(q.T@raw)
    diff=float(np.max(np.abs(projected-balanced)))
    if diff>2e-12 or np.max(np.abs(R.T@balanced))>2e-12: raise ValueError('saved projected RHS does not replay from exact raw basis')
    identities=[{'source_row_position':i,'source_group':r.get('source_group'),'source_element':r.get('source_element'),'source_inventory_row_index':r.get('source_inventory_row_index')} for i,r in zip(positions,records)]
    return {'case_sha256':sha(CASE/'case.json'),'body_K_sha256':sha(CASE/'body-K.npz'),'basis_sha256':sha(CASE/'basis.npz'),'body':case['body'],'dofs':K.shape[0],'matrix_nnz':K.nnz,'source_row_positions':positions,'source_group_names':case['source_group_names'],'source_row_identities':identities,'raw_source_wrench_Rt_raw':(R.T@raw).tolist(),'max_saved_projection_replay_difference':diff,'max_projected_rigid_wrench':float(np.max(np.abs(R.T@balanced))),'physical_response_computed':False,'factor_or_refinement_run':False}

def run():
    old=mod(ORACLE/'verify_condensation.py','authenticated_cube_oracle')
    if old.run()!=json.loads((ORACLE/'assessment.json').read_text()): raise ValueError('cube oracle no longer replays')
    helper=mod(HELPER,'shared_condensation_helper'); parser=mod(PARSER,'cube_parser')
    labels=parser.read_dof_map(CUBE/'model.dof'); packet=json.loads((CUBE/'model.json').read_text())
    Ks,_=parser.read_symmetric_triplets(CUBE/'model.sti',len(labels)); K=sp.csr_matrix(Ks)
    _,R,Qrigid=helper.rigid_basis(labels,{int(n):x for n,x in packet['nodes'].items()},ROTATION_SCALE_MM)
    factor,system=helper.factor_bordered(K,R); row={lab:i for i,lab in enumerate(labels)}
    selected=[(n,d) for n in (1,2,4) for d in (1,2,3)]; B=np.zeros((9,len(labels)))
    for i,lab in enumerate(selected): B[i,row[lab]]=1.
    raw=B.T; projected=raw-Qrigid@(Qrigid.T@raw)
    refined=solve_bordered_chunk_refined(factor,system,R,projected,rotation_scale_mm=ROTATION_SCALE_MM)
    if refined['status']!='PASS_BALANCED_FREE_BODY': raise ValueError(f'cube shared-factor solve failed: {refined}')
    old_assess=json.loads((P/'current-projected-connector-compliance-fixture-attempt01'/'assessment.json').read_text())
    H=np.asarray(old_assess['H_dense_QKQ_reference_mm_per_N']); Href=B@refined['displacement_mm']
    h_error=float(np.max(np.abs(H-Href)))
    if h_error>2e-9: raise ValueError(f'cube H differs from dense QKQ: {h_error}')

    A=sp.eye(2,format='csc'); exact=sla.splu(A); b=np.ones((2,1))
    def toy_gate(x,r):
        val=float(np.max(np.abs(r))/max(1.,float(np.max(np.abs(b)))))
        return val<=1e-12,{'relative_residual':val}
    class CorruptOnce:
        def __init__(self): self.calls=0
        def solve(self,rhs):
            out=np.asarray(exact.solve(rhs)).copy(); self.calls+=1
            if self.calls==1: out[0,0]+=1e-3
            return out
    corrected=refine_existing_factor(A,CorruptOnce(),b,toy_gate)
    class NonfiniteFactor:
        def solve(self,rhs): return np.full_like(rhs,np.nan,dtype=float)
    nonfinite=refine_existing_factor(A,NonfiniteFactor(),b,toy_gate)
    class StagnantFactor:
        def __init__(self): self.calls=0
        def solve(self,rhs):
            self.calls+=1
            return .5*np.asarray(exact.solve(rhs)) if self.calls==1 else np.zeros_like(rhs,dtype=float)
    stagnant=refine_existing_factor(A,StagnantFactor(),b,toy_gate)
    class HalfFactor:
        def solve(self,rhs): return .5*np.asarray(exact.solve(rhs))
    budget=refine_existing_factor(A,HalfFactor(),b,toy_gate)
    bad_input=refine_existing_factor(A,exact,np.asarray([[np.nan],[1.]]),toy_gate)
    if (corrected['status']!= 'PASS_REFINEMENT_GATES' or corrected['corrections']!=1
        or nonfinite['status']!='REJECT_NONFINITE_FACTOR_OUTPUT'
        or stagnant['status']!='UNRESOLVED_REFINEMENT_STAGNATION'
        or budget['status']!='UNRESOLVED_REFINEMENT_BUDGET' or budget['corrections']!=5
        or bad_input['status']!='REJECT_NONFINITE_INPUT'):
        raise ValueError('bounded refinement stop/failure fixture did not match')

    # Compare supported SuperLU option values at .solve; source inspection is
    # recorded separately and is the decisive evidence for call-path behavior.
    delta=1e-12; Aill=sp.csc_matrix([[1.,1.],[1.,1.+delta]]); bill=np.asarray([1.,1.+2*delta])
    x_default=sla.splu(Aill).solve(bill); x_extra=sla.splu(Aill,options={'IterRefine':'EXTRA'}).solve(bill)
    iterrefine_probe={'scipy_version':scipy.__version__,'default_and_EXTRA_solve_bitwise_equal':bool(np.array_equal(x_default,x_extra)),'default_solution':x_default.tolist(),'EXTRA_solution':x_extra.tolist(),'interpretation':'runtime probe is supplementary; SciPy 1.18.1 SuperLU_solve source calls gstrs directly, so .solve does not run the expert-driver iterative-refinement loop'}
    if not iterrefine_probe['default_and_EXTRA_solve_bitwise_equal']: raise ValueError('SuperLU IterRefine option probe changed .solve result')
    cube_gate=refined['history'][-1]
    return {'status':'PASS_BOUNDED_BORDERED_REFINEMENT_DIAGNOSTIC','helper_sha256':sha(HELPER),'refinement_source_sha256':sha(HERE/'bounded_refinement.py'),'fixture_source_sha256':sha(Path(__file__)),'cube_shared_bordered_solve':{'status':refined['status'],'corrections':refined['corrections'],'H_max_abs_difference_from_dense_QKQ_mm_per_N':h_error,'max_force_residual_relative':cube_gate['max_kkt_relative_residual'],'max_gauge_mm':cube_gate['max_gauge_constraint_mm'],'max_gauge_multiplier_N':cube_gate['max_gauge_multiplier_N'],'strict_gates_preserved':{'force_relative':1e-10,'gauge_atol_mm':1e-10,'gauge_rtol':1e-10,'lambda_atol_N':1e-10,'lambda_rtol':1e-10}},'corrupt_initial_solution_corrected':{'status':corrected['status'],'corrections':corrected['corrections'],'final_backward_error':corrected['history'][-1]['componentwise_backward_error']},'nonfinite_factor_fixture':{'status':nonfinite['status']},'stagnation_fixture':{'status':stagnant['status'],'corrections':stagnant['corrections']},'fixed_budget_fixture':{'status':budget['status'],'corrections':budget['corrections'],'cap':5,'last_backward_error':budget['history'][-1]['componentwise_backward_error']},'nonfinite_input_fixture':{'status':bad_input['status']},'scipy_builtin_IterRefine_check':iterrefine_probe,'prepared_parent_case':verify_parent_case(),'mechanical_acceptance':False,'actual_parent_case_factorization_or_solve':False,'numpy_version':np.__version__,'scipy_version':scipy.__version__}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--verify',action='store_true'); args=ap.parse_args(); result=run(); out=HERE/'assessment.json'
    if args.verify:
        if json.loads(out.read_text())!=result: raise SystemExit('bounded refinement diagnostic does not replay')
        print('PASS_REPLAY_BOUNDED_BORDERED_REFINEMENT_DIAGNOSTIC')
    else: out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n'); print(result['status'])
if __name__=='__main__': main()
