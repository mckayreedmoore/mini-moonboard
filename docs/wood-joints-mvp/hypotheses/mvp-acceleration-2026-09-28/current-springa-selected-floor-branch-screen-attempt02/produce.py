from pathlib import Path
import importlib.util,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
BASE=ROOT/'docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28'
SOURCE=BASE/'current-springa-selected-floor-a12-rear-attempt02'
AUDITOR=BASE/'current-springa-selected-floor-response-audit-attempt02/response_audit.py'
spec=importlib.util.spec_from_file_location('current_response_auditor',AUDITOR);a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
model=json.loads((SOURCE/'model.json').read_text());deck=(SOURCE/'model.inp').read_text();contract=a._validate_model(model,deck);states=a.parse_native_blocks((SOURCE/'model.dat').read_text())
reports=[]
for time,state in states.items():
 rows=[]
 for binding in contract['bindings']:
  source=contract['source_by_group'][binding['group']]
  if source['role']!='floor_normal':continue
  force,radius,check=a.audit_springa(binding,source,state,contract['emitted_nodes'])
  q=check['q_relative_projection_mm'];qr=check['q_relative_projection_radius_mm']
  rows.append({'source_group':binding['group'],'cell_name':binding['name'],'physical_owner':binding['physical_owner'],'strictly_positive_after_rounding':force-radius>0,'strictly_separating_after_rounding':q+qr<0,'normal_force_diagnostic_N':force,'normal_force_radius_N':radius,'q_diagnostic_mm':q,'q_radius_mm':qr})
 assert len(rows)==100
 reports.append({'time':time,'bearing_count':sum(r['strictly_positive_after_rounding'] for r in rows),'separating_count':sum(r['strictly_separating_after_rounding'] for r in rows),'rows':rows})
sets=[set(r['cell_name'] for r in s['rows'] if r['strictly_positive_after_rounding']) for s in reports]
result={'status':'REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH','corner_demands_usable':False,'full_step_native_convergence':True,'all_printed_floor_laws_checked':True,'all_printed_times':list(states),'same_positive_cell_set_at_all_printed_times':all(s==sets[0] for s in sets),'diagnostic_positive_cells_at_final_time':sorted(sets[-1]),'diagnostic_separating_cells_at_final_time':[r['cell_name'] for r in reports[-1]['rows'] if r['strictly_separating_after_rounding']],'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE/'model.json',SOURCE/'model.inp',SOURCE/'model.dat',SOURCE/'execution.json',AUDITOR]},'states':reports,'limits':['Rejected selected-bearing branch outputs are diagnostic only; no physical corner demand or joint acceptance','Positive-cell inventory diagnoses the rejected branch; no next native branch is prepared or authorized by this screen','Any new branch must release tangent constraints at open cells and independently pass complete floor complementarity, physical law, MPC, global and all-body checks']}
result['diagnostic_added_bearing_cells']=sorted(sets[-1]-set(model['floor_selected_bearing_cells']))
result['diagnostic_lost_bearing_cells']=sorted(set(model['floor_selected_bearing_cells'])-sets[-1])
Path(__file__).with_name('screen.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['states','source_sha256','diagnostic_positive_cells_at_final_time','diagnostic_separating_cells_at_final_time']}));print([(s['time'],s['bearing_count'],s['separating_count']) for s in reports])
