"""Parent exact freeze/context and unchanged response API; no implicit launch."""
import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
BASE = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
NATIVE = BASE/'current-k12-rear-spr489-direct-native-attempt01'
READY = BASE/'current-k12-rear-spr489-direct-run-readiness-attempt01'
METHOD = BASE/'current-k12-rear-spr489-direct-response-audit-attempt02'
REVIEW = BASE/'current-k12-rear-direct-parent-method-review-attempt01/review.json'
sys.path.insert(0,str(ROOT))
from fea.wood_joint_reduced_native import digest,verify,write_json,validate_numeric_fields

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

def freeze():
    review=json.loads(REVIEW.read_text())
    assert review['status']=='PASS_PARENT_EXACT_INPUT_AND_UNCHANGED_PHYSICAL_GATES_REVIEW'
    for name,sha in review['source_sha256'].items(): assert digest(name)==sha,name
    input_dir=BASE/'current-springa-k12-rear-spr489-direct-master-input-attempt02'
    validate_numeric_fields((input_dir/'model.inp').read_text())
    module=load(READY/'freeze_exact_inputs.py','parent_k12_exact_freeze_helper')
    result=module.prepare(NATIVE)
    assert result['status']=='PASS_PARENT_EXACT_BYTE_FREEZE_PREPARED_INPUT_ONLY'
    original=BASE/'current-springa-selected-floor-k12-rear-attempt03/case-context.json'
    context=json.loads(original.read_text())
    context.update(selected_input_model_json_path=str((NATIVE/'model.json').relative_to(ROOT)),
                   selected_input_model_json_sha256=digest(NATIVE/'model.json'),
                   selected_input_deck_path=str((NATIVE/'model.inp').relative_to(ROOT)),
                   selected_input_deck_sha256=digest(NATIVE/'model.inp'))
    core=load(METHOD/'response_core.py','parent_k12_direct_response_for_context')
    validator=core.load_direct_master_input_validator()
    contract=validator.validate_input_contract(NATIVE/'model.json',NATIVE/'model.inp')
    validator.validate_variant_run_context(contract,context,model_path=NATIVE/'model.json',deck_path=NATIVE/'model.inp')
    write_json(NATIVE/'case-context.json',context)
    packet=json.loads((NATIVE/'freeze.json').read_text())
    extra=[Path(__file__),READY/'source-pins.json',REVIEW,original]
    for source in extra:
        relative=str(source.resolve().relative_to(ROOT));snapshot=NATIVE/'sources'/relative
        snapshot.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,snapshot)
        packet['source_sha256'][relative]=digest(source)
    packet['files_sha256']['case-context.json']=digest(NATIVE/'case-context.json')
    write_json(NATIVE/'freeze.json',packet);verify(NATIVE)
    write_json(NATIVE/'parent-readiness-review.json',{
        'input_freeze_sha256':digest(NATIVE/'freeze.json'),
        'ready_for_scoped_native_run':True,'scope':packet['scope'],
        'max_launches':1,'no_automatic_mask_iteration':True,
        'method_review_sha256':digest(REVIEW),
        'all_unchanged_physical_gates_required':True,
        'independent_all50_audit_required':True,'mechanical_acceptance':False})
    print('PASS_PARENT_EXACT_FREEZE_AND_CASE_CONTEXT')

def plain(value):
    if isinstance(value,np.generic): return value.item()
    if isinstance(value,dict): return {key:plain(v) for key,v in value.items()}
    if isinstance(value,list): return [plain(v) for v in value]
    if isinstance(value,tuple): return [plain(v) for v in value]
    return value

def response():
    verify(NATIVE)
    core=load(METHOD/'response_core.py','parent_k12_direct_response_postprocessor')
    model=NATIVE/'model.json';deck=NATIVE/'model.inp';dat=NATIVE/'model.dat';exe=NATIVE/'execution.json'
    context_path=NATIVE/'case-context.json';context=json.loads(context_path.read_text())
    provenance=core._validate_execution(model,dat,deck,exe,dat.read_text(),context)
    validator=core.load_direct_master_input_validator()
    contract=validator.validate_input_contract(model,deck)
    report=core.audit_record_with_direct_master_contract(
        json.loads(model.read_text()),dat.read_text(),deck.read_text(),
        validated_contract=contract,model_path=model,deck_path=deck,case_context=context)
    report.update(source_input_model_json_path=str(model),source_input_deck_path=str(deck),
                  native_data_path=str(dat),case_context_path=str(context_path),
                  case_context_sha256=digest(context_path),terminal_execution_provenance=provenance)
    report['parent_report_renderer']={'source_path':str(Path(__file__).relative_to(ROOT)),
        'source_sha256':digest(Path(__file__)),'response_core_sha256':digest(METHOD/'response_core.py'),
        'scope':'NumPy scalar .item() conversion at JSON rendering only; no physical values, intervals, gates or tolerances changed'}
    write_json(NATIVE/'response.json',plain(report))
    print(report['status'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['freeze','response'])
    args=parser.parse_args()
    {'freeze':freeze,'response':response}[args.operation]()
