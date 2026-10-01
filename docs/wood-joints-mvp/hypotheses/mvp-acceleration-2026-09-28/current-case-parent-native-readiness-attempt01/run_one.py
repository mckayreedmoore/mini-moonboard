"""Parent-only readiness and ONE execution of an explicitly frozen case."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
from fea.wood_joint_reduced_native import verify,launch
BASE=ROOT/'docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(directory,source_context,run_id):
 d=Path(directory).resolve();ctx_path=Path(source_context).resolve();verify(d)
 assert not (d/'execution.json').exists(),'An execution already exists; no automatic rerun'
 c=json.loads(ctx_path.read_text());case=c['case_id'];model=json.loads((d/'model.json').read_text());assert model['case_id']==case
 for field,name in [('selected_input_model_json','model.json'),('selected_input_deck','model.inp')]:c[field+'_path']=str(d/name);c[field+'_sha256']=sha(d/name)
 context=d/'case-context.json';context.write_text(json.dumps(c,indent=2)+'\n')
 p=BASE/'current-springa-case-bound-response-audit-attempt01/response_audit.py'
 assert sha(p)=='df1ed0eedb62ed3657a05a6d679d105e15e63b5ee18b999a731adab190b1b479'
 sp=importlib.util.spec_from_file_location('case_response_audit',p);a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
 a._validate_case_context(c);contract=a._validate_model(model,(d/'model.inp').read_text(),c)
 check=d/'parent-case-context-check.json';check.write_text(json.dumps({'status':'PASS_FROZEN_CASE_BOUND_INPUT_CONTRACT_ONLY','response_auditor_sha256':sha(p),'inventory':contract['inventory_summary'],'native_response_consumed':False},indent=2)+'\n')
 baseline=a._context_path(c['source_controls_model_json_path']).parent;screen=a._context_path(c['diagnostic_floor_screen_path']);input_audit=d/'parent-serialized-input-audit.json'
 subprocess.run([sys.executable,str(BASE/'current-springa-case-bound-parent-input-audit-attempt01/check.py'),str(d),'--baseline',str(baseline),'--screen',str(screen),'--output',str(input_audit)],check=True)
 verify(d);proof=[input_audit,check,context,BASE/'current-springa-case-bound-response-audit-attempt01/method_fixture_check.json',Path(__file__),ctx_path]
 review={'input_freeze_sha256':sha(d/'freeze.json'),'ready_for_scoped_native_run':True,'reviewer':'parent independent actual-deck equations/unit-wrench and frozen case-context checks using previously proven methods','max_launches':1,'timeout_seconds':240,'memory':'4g','case_id':case,'scope':model['scope'],'evidence_sha256':{str(x):sha(x) for x in proof},'response_auditor_sha256':sha(p),'geometry_law_load_materials_preserved':True,'physical_balance_tolerances_N_Nmm':[.1,2.0],'original_leg_runner_resistance_reopened':False,'joint_acceptance':False,'mechanical_acceptance':False,'stop_condition':'One terminal execution; forces withheld until all support/law/all-body checks pass at every increment; no automatic mask iteration.'}
 rp=d/'parent-readiness-review.json';rp.write_text(json.dumps(review,indent=2)+'\n');print('PASS_PARENT_FROZEN_READINESS',flush=True)
 print(json.dumps(launch(d,run_id,rp,timeout_seconds=240,memory='4g')))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('frozen_directory');p.add_argument('prepared_case_context');p.add_argument('--run-id',required=True);args=p.parse_args();main(args.frozen_directory,args.prepared_case_context,args.run_id)
