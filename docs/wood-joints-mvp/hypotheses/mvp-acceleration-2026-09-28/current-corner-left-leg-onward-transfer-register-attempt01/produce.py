"""Source-bound onward actions for the two retained left LEG arrangements only."""
from pathlib import Path
import hashlib, json, math
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
SOURCES={
 'a12-rear':('current-corner-native-demand-export-attempt03/corner-demand-report.json','812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17'),
 'a1-rear':('current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json','2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce'),
}
AXES={'lumber_leg_bolt_left_1','lumber_leg_bolt_left_2'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(v):return math.sqrt(math.fsum(x*x for x in v))
def main():
    rows=[];pins={}
    for case,(name,pin) in SOURCES.items():
        p=BASE/name;assert sha(p)==pin;pins[str(p)]=pin;r=json.loads(p.read_text())
        assert r['case_id']==case and r['actual_case_demand_usable_for_conditional_joint_checks']
        assert len(r['increments'])==7
        for state in r['increments']:
            assert state['all_five_corner_bodies_raw_and_interval_balance_passed']
            assert state['retained_original_arrangement_count']==12
            actions=[a for a in state['retained_original_leg_runner_interfaces']
                     if a['axis_id'] in AXES and 'base_side_left' in (a['first'],a['second'])]
            assert {a['axis_id'] for a in actions}==AXES
            assert len(actions)==4
            for a in actions:
                assert {a['first'],a['second']}=={'base_side_left','lumber_leg_left'}
                assert a['resistance_scope'].startswith('retained original LEG/FLOOR-RUNNER arrangement')
                assert all(abs(x+y)<1e-10 for x,y in zip(a['force_on_first_xyz_n'],a['force_on_second_xyz_n']))
                f=a['force_on_first_xyz_n'] if a['first']=='base_side_left' else a['force_on_second_xyz_n']
                rows.append({'case_id':case,'load_factor':state['load_factor'],'axis_id':a['axis_id'],
                             'source_connection_name':a['source_connection_name'],'role':a['role'],
                             'receivers':[a['first'],a['second']],'force_on_base_side_left_xyz_N':f,
                             'force_on_lumber_leg_left_xyz_N':[-x for x in f],
                             'force_resultant_N':norm(f),'source_interface':a})
    maxima=[]
    for case in SOURCES:
        keys=sorted({(r['axis_id'],r['role']) for r in rows if r['case_id']==case})
        for axis,role in keys:
            selected=[r for r in rows if (r['case_id'],r['axis_id'],r['role'])==(case,axis,role)]
            top=max(selected,key=lambda r:r['force_resultant_N'])
            maxima.append({'case_id':case,'axis_id':axis,'role':role,'maximum_resultant_N':top['force_resultant_N'],
                           'load_factor':top['load_factor'],'signed_force_on_side_xyz_N':top['force_on_base_side_left_xyz_N']})
    assert len(rows)==56
    pins[str(Path(__file__))]=sha(Path(__file__))
    out={'schema':'current_corner_left_leg_onward_transfer_register/v1','status':'CONDITIONAL_SIGNED_ONWARD_ACTIONS_ONLY',
         'source_sha256':pins,'case_count':2,'retained_original_axes':sorted(AXES),'new_block_axes_in_register':[],
         'rows':rows,'per_case_axis_role_maxima':maxima,'existing_resistance_recomputed':False,
         'six_case_envelope':False,'joint_accepted':False,
         'limits':['Only directly connected left LEG arrangements; no generalized original-bolt qualification.',
                   'Existing baseline geometry/hardware/resistance evidence must be mapped before any affected demand comparison.',
                   'Source interface moments are owner-datum wrenches, not internal bolt bending moments.']}
    (HERE/'register.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(maxima))
if __name__=='__main__':main()
