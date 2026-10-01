"""Parent terminal gate assessment of the one fresh K12-rear response."""
import hashlib
import json
import shutil
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROOT=HERE.parents[4]
NATIVE=BASE/'current-k12-rear-spr489-direct-native-attempt01'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    response=json.loads((NATIVE/'response.json').read_text())
    audit=json.loads((HERE/'all50-audit.json').read_text())
    execution=json.loads((NATIVE/'execution.json').read_text())
    assert execution['returncode']==0 and execution['container_confirmed_terminal']
    assert response['status']=='PASS_K12_REAR_SPR489_DIRECT_MASTER_RESPONSE_AUDIT_ONLY'
    assert audit['status']=='PASS_PARENT_ALL_BODY_RESPONSE_SUMS'
    assert audit['source_model_sha256']==sha(NATIVE/'model.json')
    assert audit['source_response_sha256']==sha(NATIVE/'response.json')
    assert response['source_input_model_json_sha256']==sha(NATIVE/'model.json')
    assert response['source_input_deck_sha256']==sha(NATIVE/'model.inp')
    assert response['native_data_sha256']==sha(NATIVE/'model.dat')
    summary=response['recovery_summary']
    required=['mpc_interval_checks_passed','springa_law_checks_passed','retained_bilateral_checks_passed',
              'selected_floor_complementarity_passed','inactive_floor_tangent_no_restraint_or_reaction_passed',
              'raw_body_and_global_balance_passed','rounding_interval_body_and_global_balance_passed']
    assert all(summary[k] is True for k in required)
    assert summary['native_increment_count']==7 and summary['physical_body_count']==50
    assert summary['nonlinear_springa_component_checks']==9044
    assert summary['active_exact_floor_tangent_reaction_rows_per_increment']==46
    assert summary['inactive_floor_tangent_rows_per_increment']==154
    assert [r['load_factor'] for r in response['increments']]==[.1,.2,.3,.45,.675,.925,1.]
    assert [r['load_factor'] for r in audit['increments']]==[.1,.2,.3,.45,.675,.925,1.]
    rows=[]
    for r in audit['increments']:
        assert r['passed'] and r['body_count']==50 and len(r['body_equilibrium'])==50
        rows.extend(list(r['body_equilibrium'].values())+[r['global_equilibrium']])
    maxF=max(abs(v) for r in rows for v in r['force_residual_xyz_n'])
    maxM=max(abs(v) for r in rows for v in r['moment_residual_xyz_nmm'])
    assert maxF<=.1 and maxM<=2.
    dest=NATIVE/'audit.json'
    assert not dest.exists()
    shutil.copyfile(HERE/'all50-audit.json',dest)
    sources=[Path(__file__),HERE/'prepare.py',
        BASE/'current-k12-rear-direct-parent-all50-method-attempt01/check.py',
        BASE/'current-k12-rear-direct-parent-all50-method-attempt01/prove_method.py',
        BASE/'current-k12-rear-direct-parent-all50-method-attempt01/method-equivalence-proof.json']
    source_pins={}
    for p in sources:
        relative=str(p.relative_to(ROOT));snapshot=NATIVE/'postprocessing-sources'/relative
        snapshot.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,snapshot)
        source_pins[relative]=sha(p)
    files=['model.json','model.inp','model.dat','freeze.json','execution.json','response.json','audit.json','case-context.json','parent-readiness-review.json']
    result={'status':'PASS_PARENT_K12_REAR_DIRECT_RESPONSE_AND_ALL50',
        'candidate':'compact-floor-flush-wood-joints-development',
        'geometry_revision_id':'led-clearance-2x6-runner-seated-blocks-v1','case_id':'k12-rear',
        'run_id':execution['run_id'],'returncode':0,'elapsed_seconds':execution['elapsed_seconds'],
        'container_confirmed_terminal':True,'native_increment_count':7,'physical_body_count':50,
        'strict_bearing_floor_cells':23,'strict_inactive_floor_cells':77,
        'native_table_checks_passed':9044,'independent_body_and_global_balances_passed':True,
        'max_printed_force_residual_N':maxF,'max_printed_moment_residual_Nmm':maxM,
        'unchanged_physical_tolerances_N_Nmm':[.1,2.],
        'response_usable_for_conditional_joint_checks':True,
        'input_method_variant':'spr489_direct_c3d20_master_interpolation/v1',
        'only_two_native_equations_changed':True,'automatic_mask_iteration_used':False,
        'files_sha256':{name:sha(NATIVE/name) for name in files},
        'postprocessing_sources_sha256':source_pins,
        'mechanical_acceptance':False,'complete_joint_resistance_established':False,
        'six_case_envelope_established':False,'floor_friction_or_anchorage_qualified':False,
        'qualification_limit':'Conditional source-bound K12-rear mechanics only. Original rejected output remains historical; no new geometry, hardware capacity, physical stiffness bound or climbing release.'}
    (NATIVE/'parent-terminal-assessment.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'maxF':maxF,'maxM':maxM}))

if __name__=='__main__': main()
