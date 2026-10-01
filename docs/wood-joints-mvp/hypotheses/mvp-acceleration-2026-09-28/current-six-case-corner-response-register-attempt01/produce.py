"""Consolidate authenticated terminal responses; never solve or promote failed forces."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[5]
BASE=Path(__file__).resolve().parent.parent
HERE=Path(__file__).resolve().parent
CASES=[('a12-rear','03'),('a12-forward','03'),('a12-left','03'),('k12-right','03'),('k12-rear','03'),('a1-rear','02')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rows=[];pins={}
 def read(p):
  pins[str(p.relative_to(ROOT))]=sha(p)
  return json.loads(p.read_text())
 source_register=read(BASE/'current-six-case-source-load-register-attempt01/register.json')
 for case,attempt in CASES:
  d=BASE/f'current-springa-selected-floor-{case}-attempt{attempt}'
  model=read(d/'model.json');execution=read(d/'execution.json')
  assert model['case_id']==case and execution['returncode']==0 and execution['container_confirmed_terminal']
  for name in ['model.json','model.inp','model.dat']:
   p=d/name;pins[str(p.relative_to(ROOT))]=sha(p)
   if name in execution['outputs_sha256']:assert sha(p)==execution['outputs_sha256'][name]
  row={'case_id':case,'native_directory':str(d.relative_to(ROOT)),'run_id':execution['run_id'],'native_returncode':0,'confirmed_terminal':True,'elapsed_seconds':execution['elapsed_seconds'],'corner_demands_usable':False,'physical_failure_inferred':False}
  if case=='a1-rear':
   response=read(d/'response-zero-u-token.json');audit=read(d/'parent-all-body-response-audit.json');assessment=read(d/'parent-terminal-assessment.json')
   assert response['status']=='PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY' and audit['status']=='PASS_PARENT_ALL_BODY_RESPONSE_SUMS'
   assert audit['source_response_sha256']==sha(d/'response-zero-u-token.json') and audit['source_model_sha256']==sha(d/'model.json')
   assert assessment['conditional_case_forces_usable'] and assessment['independent_parent_all_body_pass'] and assessment['response_sha256']==sha(d/'response-zero-u-token.json')
   assert len(response['increments'])==len(audit['increments'])==7 and response['increments'][-1]['load_factor']==1
   assert all(x['passed'] and x['body_count']==50 for x in audit['increments'])
   report_path=BASE/'current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json'
   report=read(report_path);corner_audit=read(BASE/'current-corner-a1-parent-export-audit-attempt01/audit.json')
   assert report['case_id']==case and report['status']=='PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY' and report['actual_case_demand_usable_for_conditional_joint_checks'] is True
   assert corner_audit['status']=='PASS_PARENT_CORNER_INVENTORY_AND_EXACT_SIGNED_FORCE_AUDIT' and corner_audit['report_sha256']==sha(report_path) and corner_audit['response_sha256']==sha(d/'response-zero-u-token.json')
   assert len(report['increments'])==len(corner_audit['increments'])==7
   row.update(status='PASS_CONDITIONAL_RESPONSE_WITH_SIGNED_CORNER_EXPORT',corner_demands_usable=True,conditional_physical_case_forces_usable=True,full_load_factor=1,increment_count=7,corner_report_sha256=sha(report_path))
  elif case=='a12-rear':
   response=read(d/'response.json');audit=read(d/'parent-all-body-response-audit.json')
   assert response['status']=='PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY'
   assert audit['status']=='PASS_PARENT_ALL_BODY_RESPONSE_SUMS'
   assert audit['source_response_sha256']==sha(d/'response.json') and audit['source_model_sha256']==sha(d/'model.json')
   assert len(response['increments'])==len(audit['increments'])==7 and response['increments'][-1]['load_factor']==1
   assert all(x['passed'] and x['body_count']==50 for x in audit['increments'])
   report=read(BASE/'current-corner-native-demand-export-attempt03/corner-demand-report.json')
   assert report['status']=='PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY' and report['actual_case_demand_usable_for_conditional_joint_checks'] is True
   auth=report['authenticated_source_case']
   assert auth['case_id']==case and auth['input_model_json_sha256']==sha(d/'model.json') and auth['response_audit_json_sha256']==sha(d/'response.json')
   assert auth['audited_deck_sha256']==sha(d/'model.inp') and auth['audited_native_data_sha256']==sha(d/'model.dat')
   row.update(status='PASS_CONDITIONAL_REAR_RESPONSE_WITH_CORNER_EXPORT',corner_demands_usable=True,conditional_physical_case_forces_usable=True,full_load_factor=1,increment_count=7)
  else:
   assessment=read(d/'parent-terminal-assessment.json')
   assert assessment['corner_demands_usable'] is False
   if 'sources_sha256' in assessment:
    assert assessment['joint_accepted'] is False
    for name,want in assessment['sources_sha256'].items():assert sha(d/name)==want
    exception=assessment['strict_response_exception']
   else:
    assert case=='k12-right' and assessment['mechanical_acceptance'] is False
    for name,key in [('model.json','model_sha256'),('model.inp','deck_sha256'),('model.dat','dat_sha256')]:assert sha(d/name)==assessment[key]
    exception=assessment['gate_failure']
   row.update(status=assessment['status'],strict_response_exception=exception)
  rows.append(row)
 pins[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
 out={'schema':'current_six_case_corner_response_register/v1','candidate':'compact-floor-flush-wood-joints-development','revision':'led-clearance-2x6-runner-seated-blocks-v1','case_count':len(rows),'usable_corner_demand_cases':sum(r['corner_demands_usable'] for r in rows),'usable_conditional_physical_response_cases':sum(r.get('conditional_physical_case_forces_usable',False) for r in rows),'cases':rows,'source_pins_sha256':pins,'scope':'Ring A, zero bolt gap, Hillman axial/lateral proxy ratio 1, zero accessory, unverified conditional no-slip floor. Two complete source-bound signed corner exports; no six-case demand envelope.','new_block_axis_count':92,'original_leg_runner_arrangement_count':12,'hillman_axis_count':66,'joint_accepted':False,'six_case_envelope_complete':False,'complete_corner_resistance':False,'full_frame_stiffness_engagement_sensitivity_complete':False,'next_dependencies':['Resolve source-bound support compatibility for rejected case responses; no automatic mask iteration.','Recover signed complete corner actions across compatible cases and engagement/stiffness scenarios.','Applicable coupled BG003 unequal/non-collinear three-member resistance.','Signed internal critical-section actions and supported wood-failure/bolt/washer interaction checks.']}
 (HERE/'register.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'case_count':len(rows),'usable_corner_demand_cases':out['usable_corner_demand_cases'],'all_executions_confirmed_terminal':True}))
if __name__=='__main__':main()
