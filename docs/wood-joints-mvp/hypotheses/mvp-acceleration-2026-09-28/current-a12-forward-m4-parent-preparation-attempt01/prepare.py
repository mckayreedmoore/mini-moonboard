"""Parent-owned bounded M4 freeze, response and independent balance; launch is explicit."""
import argparse, importlib.util, json, shutil, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[5]
BASE=Path(__file__).resolve().parent.parent
NATIVE=BASE/'current-springa-selected-floor-a12-forward-attempt04'
PROPOSAL=BASE/'current-springa-a12-forward-mask-update-proposal-attempt01'
CORE=BASE/'current-springa-zero-u-token-response-audit-attempt01/response_audit.py'
sys.path.insert(0,str(ROOT))
from fea.wood_joint_reduced_native import digest,verify,write_json,validate_numeric_fields

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module

def plain(value):
 if isinstance(value,np.generic):return value.item()
 if isinstance(value,dict):return {k:plain(v) for k,v in value.items()}
 if isinstance(value,(tuple,list)):return [plain(v) for v in value]
 return value

def freeze():
 manifest_path=PROPOSAL/'input-gate-source-pins.json';manifest=json.loads(manifest_path.read_text())
 pins={**manifest['direct_source_sha256'],**manifest['source_sha256']}
 for name,sha in pins.items():assert digest(ROOT/name)==sha,name
 core=load(CORE,'parent_forward_original_core');source=PROPOSAL/'a12-forward'
 context=json.loads((PROPOSAL/'case-context.json').read_text())
 core._validate_model(json.loads((source/'model.json').read_text()),(source/'model.inp').read_text(),context)
 validate_numeric_fields((source/'model.inp').read_text())
 helper=load(BASE/'current-springa-case-selected-native-preparation-attempt05/freeze_input.py','parent_forward_freeze_helper')
 extras=[ROOT/name for name in pins]+[manifest_path,Path(__file__),ROOT/'AGENTS.md']
 helper.main(source,NATIVE,PROPOSAL/'prepare_m4_proposal.py',extra_files=extras)
 context.update(selected_input_model_json_path=str((NATIVE/'model.json').relative_to(ROOT)),selected_input_model_json_sha256=digest(NATIVE/'model.json'),selected_input_deck_path=str((NATIVE/'model.inp').relative_to(ROOT)),selected_input_deck_sha256=digest(NATIVE/'model.inp'))
 core._validate_model(json.loads((NATIVE/'model.json').read_text()),(NATIVE/'model.inp').read_text(),context)
 write_json(NATIVE/'case-context.json',context)
 packet=json.loads((NATIVE/'freeze.json').read_text());packet['files_sha256']['case-context.json']=digest(NATIVE/'case-context.json');write_json(NATIVE/'freeze.json',packet);verify(NATIVE)
 write_json(NATIVE/'parent-readiness-review.json',{'input_freeze_sha256':digest(NATIVE/'freeze.json'),'ready_for_scoped_native_run':True,'max_launches':1,'no_automatic_mask_iteration':True,'scope':'One source-bound A12-forward M4 hypothesis; established methods and strict physical gates unchanged. No geometry, stiffness, load or acceptance change.','input_gate_sha256':digest(PROPOSAL/'input-gate.json'),'all_increment_floor_and_source_law_gates_required':True,'independent_all50_audit_required':True,'mechanical_acceptance':False})
 print('PASS_PARENT_M4_FREEZE_AND_UNCHANGED_INPUT_GATES')

def response():
 verify(NATIVE);core=load(CORE,'parent_forward_original_response')
 model=NATIVE/'model.json';deck=NATIVE/'model.inp';dat=NATIVE/'model.dat';exe=NATIVE/'execution.json';ctx=NATIVE/'case-context.json';context=json.loads(ctx.read_text())
 try:
  provenance=core._validate_execution(model,dat,deck,exe,dat.read_text(),context)
  report=core.audit_record(json.loads(model.read_text()),dat.read_text(),deck.read_text(),context)
 except Exception as exc:
  write_json(NATIVE/'parent-response-rejection.json',{'status':'REJECTED_UNCHANGED_PHYSICAL_RESPONSE_GATE','exception_type':type(exc).__name__,'reason':str(exc),'model_sha256':digest(model),'deck_sha256':digest(deck),'dat_sha256':digest(dat),'execution_sha256':digest(exe),'usable_corner_demands':False,'no_automatic_mask_iteration':True});raise
 report.update(source_input_model_json_path=str(model),source_input_deck_path=str(deck),native_data_path=str(dat),case_context_path=str(ctx),case_context_sha256=digest(ctx),terminal_execution_provenance=provenance,parent_report_renderer={'scope':'NumPy scalar .item conversion only','source_sha256':digest(Path(__file__))})
 write_json(NATIVE/'response.json',plain(report));print(report['status'])
 check=load(BASE/'current-springa-selected-floor-parent-response-audit-attempt01/check.py','parent_forward_independent_all50');check.HERE=NATIVE;check.run(model,NATIVE/'response.json')
 audit=json.loads((NATIVE/'audit.json').read_text());assert audit['status']=='PASS_PARENT_ALL_BODY_RESPONSE_SUMS'
 assert len(report['increments'])==7 and len(audit['increments'])==7
 write_json(NATIVE/'parent-terminal-assessment.json',{'status':'PASS_PARENT_A12_FORWARD_M4_RESPONSE_AND_ALL50','response_usable_for_conditional_joint_checks':True,'joint_accepted':False,'six_case_acceptance':False,'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in [model,deck,dat,exe,ctx,NATIVE/'freeze.json',NATIVE/'response.json',NATIVE/'audit.json',Path(__file__)]}})
 print('PASS_PARENT_A12_FORWARD_M4_RESPONSE_AND_ALL50')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['freeze','response']);args=parser.parse_args();{'freeze':freeze,'response':response}[args.operation]()
