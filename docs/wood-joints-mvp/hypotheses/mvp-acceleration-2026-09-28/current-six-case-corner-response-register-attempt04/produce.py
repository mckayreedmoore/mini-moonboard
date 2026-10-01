"""Preserve three usable cases and record the bounded forward M5 rejection."""
import argparse,copy,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=HERE.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(ROOT))
def produce():
 prior=BASE/'current-six-case-corner-response-register-attempt03/register.json';old=json.loads(prior.read_text())
 assert old['usable_corner_demand_cases']==3 and old['usable_conditional_physical_response_cases']==3
 for name,value in old['source_pins_sha256'].items():assert sha(ROOT/name)==value,name
 packet=BASE/'current-springa-selected-floor-a12-forward-attempt05';assessment_path=packet/'parent-terminal-assessment.json';assessment=json.loads(assessment_path.read_text())
 assert assessment['status']=='REJECTED_PARENT_A12_FORWARD_M5_PHYSICAL_COMPATIBILITY'
 assert not assessment['response_usable_for_conditional_joint_checks'] and not assessment['physical_failure_inferred']
 assert assessment['returncode']==0 and assessment['container_confirmed_terminal']
 for name,value in assessment['source_sha256'].items():assert sha(ROOT/name)==value,name
 result=copy.deepcopy(old);row=next(r for r in result['cases'] if r['case_id']=='a12-forward');prior_row=copy.deepcopy(row)
 row.clear();row.update(case_id='a12-forward',native_directory=rel(packet),run_id=assessment['run_id'],native_returncode=0,confirmed_terminal=True,elapsed_seconds=assessment['elapsed_seconds'],corner_demands_usable=False,conditional_physical_case_forces_usable=False,physical_failure_inferred=False,status=assessment['status'],strict_rejection=assessment['strict_rejection'],preserved_prior_rejected_response=prior_row,no_automatic_mask_iteration=True)
 result['scope']='Three authenticated conditional physical responses with complete corner exports; latest forward M5 support proposal strictly rejected, with left/right support cycles also unresolved. No complete resistance, six-case envelope or physical stiffness bound.'
 result['source_pins_sha256'].update({rel(p):sha(p) for p in [prior,assessment_path,Path(__file__)]})
 result['source_pins_sha256'].update(assessment['source_sha256'])
 assert result['case_count']==6 and not result['joint_accepted'] and not result['six_case_envelope_complete']
 return result
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args();result=produce();target=HERE/'register.json'
 if args.verify:assert json.loads(target.read_text())==result;print('Verified three usable cases and latest forward M5 rejection')
 else:target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print('Wrote preserved three-case register with forward M5 rejection')
