"""Append the authenticated direct-master K12 case to preserved six-case evidence."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROOT=HERE.parents[4]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(ROOT))

def produce():
    original=BASE/'current-six-case-corner-response-register-attempt01/register.json'
    old=json.loads(original.read_text())
    assert old['case_count']==6 and old['usable_conditional_physical_response_cases']==2
    assert old['usable_corner_demand_cases']==2
    for name,expected in old['source_pins_sha256'].items(): assert sha(ROOT/name)==expected,name
    packet=BASE/'current-k12-rear-spr489-direct-native-attempt01'
    assessment_path=packet/'parent-terminal-assessment.json'
    assessment=json.loads(assessment_path.read_text())
    assert assessment['status']=='PASS_PARENT_K12_REAR_DIRECT_RESPONSE_AND_ALL50'
    assert assessment['response_usable_for_conditional_joint_checks'] is True
    assert assessment['independent_body_and_global_balances_passed'] is True
    assert assessment['native_increment_count']==7 and assessment['physical_body_count']==50
    for name,expected in assessment['files_sha256'].items():assert sha(packet/name)==expected,name
    report_path=BASE/'current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json'
    report=json.loads(report_path.read_text())
    assert report['case_id']=='k12-rear'
    assert report['actual_case_demand_usable_for_conditional_joint_checks'] is True
    assert len(report['increments'])==7
    for r in report['increments']:
        assert r['all_five_corner_bodies_raw_and_interval_balance_passed'] is True
        assert r['incoming_and_onward_transfers_included'] is True
        assert r['primary_physical_bolt_groups']['BG003']['lateral_plane_count']==4
    result=copy.deepcopy(old)
    row=next(r for r in result['cases'] if r['case_id']=='k12-rear')
    prior=copy.deepcopy(row)
    row.clear();row.update(case_id='k12-rear',native_directory=rel(packet),
        run_id=assessment['run_id'],native_returncode=0,confirmed_terminal=True,
        elapsed_seconds=assessment['elapsed_seconds'],corner_demands_usable=True,
        conditional_physical_case_forces_usable=True,physical_failure_inferred=False,
        status='PASS_CONDITIONAL_K12_REAR_DIRECT_MASTER_RESPONSE_WITH_CORNER_EXPORT',
        full_load_factor=1.,increment_count=7,
        method_variant=assessment['input_method_variant'],preserved_prior_rejected_response=prior)
    result['usable_corner_demand_cases']=3
    result['usable_conditional_physical_response_cases']=3
    result['scope']='Three authenticated conditional source-bound responses with complete corner exports; three original rejected support branches remain unresolved. No complete resistance, six-case envelope or physical stiffness bound.'
    files=[original,assessment_path,report_path,Path(__file__)]
    result['source_pins_sha256'].update({rel(p):sha(p) for p in files})
    result['source_pins_sha256'].update({rel(packet/name):expected for name,expected in assessment['files_sha256'].items()})
    result['native_method_variant_does_not_transfer_to_other_cases']=True
    assert not result['joint_accepted'] and not result['six_case_envelope_complete']
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    value=produce();path=HERE/'register.json'
    if args.verify:assert json.loads(path.read_text())==value;print('Verified three-case conditional progress register')
    else:path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');print('Wrote three-case conditional progress register')
