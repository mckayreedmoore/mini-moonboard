"""Independent standard-library force/moment and normal-resultant checks."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
d=json.loads((HERE/'floor-wrench-screen.json').read_text())
for name,pin in d['pins'].items():assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==pin
model=json.loads((BASE/'reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json').read_text())
inputs=json.loads((BASE/'reduced-static-attempt01/model-inputs.json').read_text())
for name,point in zip(d['floor_cell_names'],d['floor_points_mm'],strict=True):
    source=model['connection_ownership'][name]
    assert source['role']=='floor_normal' and source['scalar_normal']==[0.,0.,1.]
    assert max(abs(a-b) for a,b in zip(source['point'],point,strict=True))<1e-10
def cross(p,f):
    x,y,z=p;fx,fy,fz=f
    return [y*fz-z*fy,z*fx-x*fz,x*fy-y*fx]
grav=[r for rows in inputs['assigned_gravity_by_member'].values() for r in rows]+inputs['unassigned_hardware_gravity']
assert len(grav)==778 and len({r['source_name'] for r in grav})==778
sourceF=[sum(r['force_xyz_n'][i] for r in grav) for i in range(3)]
sourceM=[sum(cross(r['point_xyz_mm'],r['force_xyz_n'])[i] for r in grav) for i in range(3)]
accessory={r['scenario_id']:r for r in inputs['accessory_placement_scenarios']['scenarios']}
cases={r['case_id']:r for r in inputs['cases']}
largestF=largestM=0.
assert len(d['case_results'])==12 and len(d['floor_points_mm'])==100
for case in d['case_results']:
    assert case['status']=='STRICTLY_POSITIVE_NORMAL_BALANCE_WITNESS'
    load=cases[case['case_id']]['source_applied_load']
    F_expected=[a+b for a,b in zip(sourceF,load['applied_force_global_xyz_n'],strict=True)]
    M_expected=[a+b for a,b in zip(sourceM,cross(load['force_application_point_global_xyz_mm'],load['applied_force_global_xyz_n']),strict=True)]
    scenario=case['accessory_scenario_id']
    if scenario!='recorded_no_accessory_diagnostic':
        extra=accessory[scenario]
        F_expected=[a+b for a,b in zip(F_expected,extra['accessory_gravity_force_global_xyz_n'],strict=True)]
        M_expected=[a+b for a,b in zip(M_expected,extra['accessory_gravity_moment_about_global_origin_nmm'],strict=True)]
    assert max(abs(a-b) for a,b in zip(F_expected,case['external_global_force_N'],strict=True))<1e-8
    assert max(abs(a-b) for a,b in zip(M_expected,case['external_global_moment_about_origin_Nmm'],strict=True))<1e-6
    F=case['external_global_force_N'][:];M=case['external_global_moment_about_origin_Nmm'][:]
    for point,force in zip(d['floor_points_mm'],case['witness_cell_forces_N'],strict=True):
        x,y,z=point;fx,fy,fz=force
        assert abs(z)<1e-9 and fz>0.
        for i in range(3):F[i]+=force[i]
        M[0]+=y*fz-z*fy;M[1]+=z*fx-x*fz;M[2]+=x*fy-y*fx
    errorF=max(map(abs,F));errorM=max(map(abs,M))
    assert errorF<1e-7 and errorM<1e-5
    largestF=max(largestF,errorF);largestM=max(largestM,errorM)
    P=sum(f[2] for f in case['witness_cell_forces_N'])
    cop=[sum(p[i]*f[2] for p,f in zip(d['floor_points_mm'],case['witness_cell_forces_N'],strict=True))/P for i in [0,1]]
    assert max(abs(a-b) for a,b in zip(cop,case['normal_resultant_point_xy_mm'],strict=True))<1e-8
print('12 full-wrench witnesses close independently; maximum residuals N/Nmm:',largestF,largestM)
print('Strictly positive algebraic normal forces do not establish contact compatibility or actual reactions')
