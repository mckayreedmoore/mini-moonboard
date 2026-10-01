"""Necessary whole-assembly balance witnesses; no frame/compatibility response."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import linprog
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
INPUT=BASE/'reduced-static-attempt01/model-inputs.json'
MODEL=BASE/'reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json'
PINS={INPUT:'178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9',MODEL:'d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0'}

def normal_witness(points,P,My,minusMx):
    n=len(points);xy=points[:,:2]
    equality=np.column_stack([np.vstack([np.ones(n),xy[:,0]/1000,xy[:,1]/1000]),np.zeros(3)])
    objective=np.r_[np.zeros(n),-1.]
    result=linprog(objective,A_ub=np.column_stack([-np.eye(n),np.ones(n)]),b_ub=np.zeros(n),
                   A_eq=equality,b_eq=[P,My/1000,minusMx/1000],bounds=[(0,None)]*(n+1),method='highs')
    return result

def build():
    for p,pin in PINS.items():assert hashlib.sha256(p.read_bytes()).hexdigest()==pin
    d=json.loads(INPUT.read_text());m=json.loads(MODEL.read_text())
    floor=[(name,row) for name,row in m['connection_ownership'].items() if row.get('role')=='floor_normal']
    assert len(floor)==100
    points=np.array([r['point'] for _,r in floor]);assert max(abs(points[:,2]))<1e-9
    assert all(np.allclose(r['scalar_normal'],[0,0,1],atol=1e-12,rtol=0) for _,r in floor)
    gravity=[r for rows in d['assigned_gravity_by_member'].values() for r in rows]+d['unassigned_hardware_gravity']
    assert len(gravity)==778 and len({r['source_name'] for r in gravity})==778
    gravityF=sum((np.array(r['force_xyz_n']) for r in gravity),np.zeros(3))
    gravityM=sum((np.cross(r['point_xyz_mm'],r['force_xyz_n']) for r in gravity),np.zeros(3))
    # Known answer: four square corner supports, centered 40 N load, max minimum=10 N.
    fixture=normal_witness(np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]],dtype=float),40.,0.,0.)
    assert fixture.success and abs(fixture.x[-1]-10.)<1e-8 and np.allclose(fixture.x[:-1],[10]*4,atol=1e-8)
    rejected=normal_witness(np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]],dtype=float),40.,80.,0.)
    assert rejected.status==2 # x-resultant=2 mm lies outside the +/-1 mm square.
    accessory=next(r for r in d['accessory_placement_scenarios']['scenarios'] if r['scenario_id']=='split_12_5_kg_hold_mean')
    scenarios=[('recorded_no_accessory_diagnostic',np.zeros(3),np.zeros(3)),
               (accessory['scenario_id'],np.array(accessory['accessory_gravity_force_global_xyz_n']),np.array(accessory['accessory_gravity_moment_about_global_origin_nmm']))]
    rows=[];count=len(floor)
    tangent=np.zeros((3,2*count));tangent[0,0::2]=1;tangent[1,1::2]=1
    tangent[2,0::2]=-points[:,1]/1000;tangent[2,1::2]=points[:,0]/1000
    for case in d['cases']:
        source=case['source_applied_load'];force=np.array(source['applied_force_global_xyz_n'])
        moment=np.cross(source['force_application_point_global_xyz_mm'],force)
        baseF=gravityF+force;baseM=gravityM+moment
        assert np.allclose(baseF,case['including_deferred_hardware_force_xyz_n'],atol=1e-8,rtol=0.)
        assert np.allclose(baseM,case['including_deferred_hardware_moment_about_origin_xyz_nmm'],atol=1e-6,rtol=0.)
        if case['case_id']=='a12-rear':
            assert np.allclose(baseF,m['case_assembly_audit']['expected_global_force_xyz_n'],atol=1e-8,rtol=0.)
            assert np.allclose(baseM,m['case_assembly_audit']['expected_global_moment_about_origin_xyz_nmm'],atol=1e-6,rtol=0.)
        for scenario,extraF,extraM in scenarios:
            F=baseF+extraF;M=baseM+extraM;P=-F[2]
            answer=normal_witness(points,P,M[1],-M[0])
            row={'case_id':case['case_id'],'accessory_scenario_id':scenario,'external_global_force_N':F.tolist(),
                 'external_global_moment_about_origin_Nmm':M.tolist(),'normal_resultant_point_xy_mm':[float(M[1]/P),float(-M[0]/P)]}
            if not answer.success:
                row.update(status='NO_NONNEGATIVE_NORMAL_BALANCE_WITNESS',linear_program_status=int(answer.status));rows.append(row);continue
            N=answer.x[:-1]
            rhs=np.array([-F[0],-F[1],-M[2]/1000]);T=tangent.T@np.linalg.solve(tangent@tangent.T,rhs)
            cellForces=np.column_stack([T[0::2],T[1::2],N])
            residualF=F+cellForces.sum(axis=0);residualM=M+np.cross(points,cellForces).sum(axis=0)
            assert max(abs(residualF))<1e-7 and max(abs(residualM))<1e-5
            assert min(N)>=-1e-9 and min(N)>=answer.x[-1]-1e-7
            row.update(status='STRICTLY_POSITIVE_NORMAL_BALANCE_WITNESS' if answer.x[-1]>1e-7 else 'NONNEGATIVE_NORMAL_BALANCE_WITNESS',
                       maximum_minimum_cell_force_N=float(answer.x[-1]),witness_cell_forces_N=cellForces.tolist(),
                       max_force_residual_N=float(max(abs(residualF))),max_moment_residual_Nmm=float(max(abs(residualM))))
            rows.append(row)
    return {'pins':{str(p.relative_to(BASE)):pin for p,pin in PINS.items()},'scipy_version':scipy.__version__,
            'floor_cell_names':[name for name,_ in floor],'floor_points_mm':points.tolist(),
            'gravity_source_count':778,'gravity_global_force_N':gravityF.tolist(),'gravity_global_moment_about_origin_Nmm':gravityM.tolist(),
            'method':'Maximize minimum normal cell force subject only to aggregate force/roll/pitch balance; least-norm unconstrained tangential force/yaw balance',
            'scope':'Six recorded external cases, with and without one recorded 25 kg mean-accessory placement. Algebraic force witnesses only, not frame reactions or contact compatibility.',
            'known_answers':'Centered 40 N on +/-1 mm square -> all four forces 10 N; x-resultant +2 mm -> infeasible',
            'qualified_for_design':False,'native_solve_executed':False,'case_results':rows}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    result=build();out=HERE/'floor-wrench-screen.json'
    if args.verify:
        prior=json.loads(out.read_text());assert prior['pins']==result['pins']
        for a,b in zip(prior['case_results'],result['case_results'],strict=True):
            assert a['status']==b['status']
            assert abs(a['maximum_minimum_cell_force_N']-b['maximum_minimum_cell_force_N'])<1e-6
    else:out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    for row in result['case_results']:print(row['case_id'],row['accessory_scenario_id'],row['status'],round(row.get('maximum_minimum_cell_force_N',0),4))
