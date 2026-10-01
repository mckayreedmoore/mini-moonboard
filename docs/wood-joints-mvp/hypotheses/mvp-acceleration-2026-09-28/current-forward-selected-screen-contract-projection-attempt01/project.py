"""Project a rejected selected-stage screen into the shared diagnostic schema."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROOT=HERE.parents[4]
SOURCE=BASE/'current-springa-a12-forward-selected-floor-screen-attempt01/screen.json'
CONTROL=BASE/'current-springa-frame-a12-forward-all-bearing-attempt01'
RUN=BASE/'current-springa-selected-floor-a12-forward-attempt01'
PROOF=BASE/'current-forward-floor-parent-interval-audit-attempt01/audit.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=json.loads(SOURCE.read_text());c=json.loads((RUN/'case-context.json').read_text());proof=json.loads(PROOF.read_text())
 assert sha(SOURCE)=='e4c1c0f9b570b0225264c6f9610820d0ffc35bdf51a531bca100fc450504fee7'
 assert r['status']=='REJECTED_SELECTED_FLOOR_MASK_STRICT_COMPLEMENTARITY' and r['corner_demands_usable'] is False
 assert proof['status']=='PASS_PARENT_INDEPENDENT_NATIVE_NORMAL_CLASSIFICATIONS' and proof['cells_checked']==700
 assert proof['source_sha256'][str(SOURCE)]==sha(SOURCE)
 assert c['source_controls_model_json_sha256']==sha(CONTROL/'model.json') and c['source_controls_deck_sha256']==sha(CONTROL/'model.inp')
 pins=dict(r['source_sha256'])
 for name,expected in pins.items():assert sha(ROOT/name)==expected,name
 for p in (SOURCE,PROOF,HERE/'project.py',CONTROL/'model.json',CONTROL/'model.inp',CONTROL/'model.dat',CONTROL/'execution.json',CONTROL/'freeze.json'):
  pins[str(p.relative_to(ROOT))]=sha(p)
 states=[];positive_sets=[]
 for step in r['times']:
  assert len(step['rows'])==100
  rows=[{'source_group':x['source_group'],'cell_name':x['normal_cell'],'physical_owner':x['physical_owner'],'strictly_positive_after_rounding':x['strictly_positive_after_rounding'],'strictly_separating_after_rounding':x['strictly_separated_with_zero_rf_after_rounding'],'normal_force_diagnostic_N':x['native_endpoint_internal_force_N'],'normal_force_radius_N':x['native_law_check']['native_endpoint_internal_radius_N'],'q_diagnostic_mm':x['projected_q_mm'],'q_radius_mm':x['projected_q_rounding_radius_mm'],'classification_source':'complete original selected-stage interval row, independently replayed from DAT'} for x in step['rows']]
  positive={x['cell_name'] for x in rows if x['strictly_positive_after_rounding']};separate={x['cell_name'] for x in rows if x['strictly_separating_after_rounding']}
  assert len(positive)==31 and len(separate)==69 and not positive&separate and len(positive|separate)==100
  positive_sets.append(positive);states.append({'time':step['time'],'bearing_count':len(positive),'separating_count':len(separate),'rows':rows})
 assert all(s==positive_sets[0] for s in positive_sets)
 result={'schema':'current_case_bound_floor_diagnostic_screen/v1','case_id':r['case_id'],'candidate':r['candidate'],'geometry_revision_id':r['geometry_revision_id'],'status':'REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH','source_stage':'selected-proposal','direct_classification_source_path':str(SOURCE.relative_to(ROOT)),'direct_classification_source_sha256':sha(SOURCE),'lineage':{'original_all_bearing_controls_model_sha256':sha(CONTROL/'model.json'),'original_all_bearing_controls_deck_sha256':sha(CONTROL/'model.inp'),'screened_selected_model_sha256':sha(RUN/'model.json'),'screened_selected_deck_sha256':sha(RUN/'model.inp'),'screened_selected_dat_sha256':sha(RUN/'model.dat'),'original_mask_deltas':r['mask_deltas_vs_original_35_cell_proposal'],'shared_normal_carriers_and_physics_bound_by_source_context':True},'corner_demands_usable':False,'full_step_native_convergence':True,'all_printed_floor_laws_checked':True,'all_printed_times':[s['time'] for s in states],'same_positive_cell_set_at_all_printed_times':True,'diagnostic_positive_cells_at_final_time':sorted(positive_sets[-1]),'diagnostic_separating_cells_at_final_time':sorted(separate),'source_sha256':pins,'states':states,'limits':['Selected-stage diagnostic schema projection only; original all-bearing inputs remain physics authority, not the direct source of the 31/69 classifications.','No alternate input or accepted response is produced; any new mask is a separately parent-selected proposal requiring full compatibility and all-body balance.','No force adoption, automatic iteration, floor qualification, or joint acceptance.']}
 (HERE/'screen.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS_EXPLICIT_SELECTED_STAGE_SCREEN_PROJECTION',sha(HERE/'screen.json'))
if __name__=='__main__':main()
