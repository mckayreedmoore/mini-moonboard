"""Source-bound signed corner response comparison at one stiffness point."""
import argparse
import hashlib
import json
import math
from pathlib import Path

BASE=Path(__file__).resolve().parent.parent
OLD=BASE/'current-springa-selected-floor-a12-rear-attempt03'
NEW=BASE/'current-a12-rear-bg001-seat-stiffness-native-attempt01'
OUTPUT=Path(__file__).parent/'corner-sensitivity-comparison.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())

def build():
    old,new=load(OLD/'response.json'),load(NEW/'response.json')
    audit=load(NEW/'audit.json')
    assert audit['status']=='PASS_PARENT_ALL_BODY_RESPONSE_SUMS'
    assert audit['source_response_sha256']==sha(NEW/'response.json')
    assert audit['source_model_sha256']==sha(NEW/'model.json')
    for folder,report in [(OLD,old),(NEW,new)]:
        assert report['status']=='PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY'
        assert report['source_input_model_json_sha256']==sha(folder/'model.json')
        assert report['source_input_deck_sha256']==sha(folder/'model.inp')
        assert report['native_data_sha256']==sha(folder/'model.dat')
        execution=load(folder/'execution.json')
        assert execution['returncode']==0 and execution['container_confirmed_terminal']
        assert all(report[k] for k in ['mpc_interval_checks_passed','springa_law_checks_passed',
            'retained_bilateral_checks_passed','selected_floor_complementarity_passed',
            'inactive_floor_tangent_no_restraint_or_reaction_passed',
            'raw_body_and_global_balance_passed','rounding_interval_body_and_global_balance_passed'])
    assert len(old['increments'])==len(new['increments'])==7
    rows=[]
    for a,b in zip(old['increments'],new['increments']):
        assert a['load_factor']==b['load_factor'] and a['time']==b['time']
        selected=lambda r:{k:v for k,v in r['physical_connection_forces'].items()
                           if k.startswith('knee_outer_left_')}
        aa,bb=selected(a),selected(b)
        assert set(aa)==set(bb) and len(aa)==14
        for name in sorted(aa):
            x,y=aa[name],bb[name]
            for field in ['first','second','role','axis_id','point']:
                assert x[field]==y[field],(name,field)
            for field in ['first_point','second_point']:
                assert x.get(field,x['point'])==y.get(field,y['point']),(name,field)
            for r in (x,y):
                assert max(abs(i+j) for i,j in zip(r['force_on_first_xyz_n'],r['force_on_second_xyz_n']))<1e-10
            f,g=x['force_on_first_xyz_n'],y['force_on_first_xyz_n']
            nf,ng=math.sqrt(math.fsum(v*v for v in f)),math.sqrt(math.fsum(v*v for v in g))
            rows.append({'load_factor':a['load_factor'],'name':name,'role':x['role'],
                         'first':x['first'],'second':x['second'],'first_point_mm':x.get('first_point',x['point']),
                         'second_point_mm':x.get('second_point',x['point']),'baseline_force_on_first_N':f,
                         'variant_force_on_first_N':g,'signed_change_on_first_N':[j-i for i,j in zip(f,g)],
                         'baseline_resultant_N':nf,'variant_resultant_N':ng,
                         'variant_to_baseline_resultant':ng/nf if nf else None})
    body_rows=[v for z in audit['increments'] for v in [*z['body_equilibrium'].values(),z['global_equilibrium']]]
    paths=[Path(__file__),NEW/'audit.json']
    paths += [folder/name for folder in (OLD,NEW) for name in ['model.json','model.inp','model.dat','response.json','freeze.json','execution.json']]
    return {'status':'PASS_SOURCE_BOUND_SINGLE_POINT_CORNER_SENSITIVITY_COMPARISON',
            'candidate':'compact-floor-flush-wood-joints-development',
            'geometry_revision_id':'led-clearance-2x6-runner-seated-blocks-v1',
            'case_id':'a12-rear','baseline_tie_stiffness_N_per_mm':4670.054188242363,
            'variant_tie_stiffness_N_per_mm':2401.714359616974,
            'scope':'BG001/BG003/BG045 complete left outer corner path; fourteen signed bolt actions at seven matched increments',
            'independent_all50_max_printed_force_residual_N':max(abs(v) for r in body_rows for v in r['force_residual_xyz_n']),
            'independent_all50_max_printed_moment_residual_Nmm':max(abs(v) for r in body_rows for v in r['moment_residual_xyz_nmm']),
            'source_sha256':{str(p):sha(p) for p in paths},'signed_action_count':len(rows),'rows':rows,
            'mechanical_acceptance':False,'six_case_sensitivity_envelope':False,'physical_stiffness_bound':False,
            'standard_711_case_context_validation_claimed':False,
            'limits':['One uncalibrated source-derived stiffness point only; not a physical bound.',
                      'Fresh strict floor compatibility and all physical gates pass at every increment for this conditional branch.',
                      'No connection capacity, splitting, group qualification, floor friction, branch uniqueness or fabrication acceptance follows.',
                      'Four other base-case responses and wider sensitivity remain unresolved; original12 bolt arrangements remain separate.']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    result=build()
    if args.verify:assert result==load(OUTPUT);print('PASS: signed14-action sensitivity comparison reproduced')
    else:
        assert not OUTPUT.exists();OUTPUT.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        for r in result['rows']:
            if r['load_factor']==1:print(r['name'],round(r['baseline_resultant_N'],6),round(r['variant_resultant_N'],6))
        print('Independent force/moment maxima',result['independent_all50_max_printed_force_residual_N'],result['independent_all50_max_printed_moment_residual_Nmm'])
