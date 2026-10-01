"""Run immutable audit; convert NumPy scalar values for strict JSON only."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
import numpy as np
HERE=Path(__file__).resolve().parent
AUDITOR=HERE.parent/'current-springa-selected-floor-response-audit-attempt03/response_audit.py'
PIN='41536568057101155290880e1d6228ea9eda8fc283678cd06ee3acb5945797ed'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def primitive(v):
 if isinstance(v,np.generic):return primitive(v.item())
 if isinstance(v,dict):return {k:primitive(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [primitive(x) for x in v]
 if v is None or type(v) in (bool,int,float,str):return v
 raise TypeError(type(v))
def run(directory):
 d=Path(directory).resolve();assert sha(AUDITOR)==PIN
 spec=importlib.util.spec_from_file_location('immutable_response_auditor',AUDITOR);a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
 model=d/'model.json';dat=d/'model.dat';deck=d/'model.inp';execution=d/'execution.json'
 provenance=a._validate_execution(model,dat,deck,execution,dat.read_text())
 r=a.audit_record(json.loads(model.read_text()),dat.read_text(),deck.read_text())
 r.update(source_input_model_json_sha256=sha(model),source_input_model_json_path=str(model),source_input_deck_path=str(deck),native_data_path=str(dat),terminal_execution_provenance=provenance)
 output=primitive(r);encoded=json.dumps(output,indent=2,allow_nan=False)+'\n'
 assert json.loads(encoded)==output
 (d/'response.json').write_text(encoded)
 (d/'parent-report-serialization.json').write_text(json.dumps({'status':'PASS_NUMPY_SCALAR_JSON_CONVERSION_ONLY','auditor_sha256':sha(AUDITOR),'writer_sha256':sha(Path(__file__)),'response_sha256':sha(d/'response.json'),'frozen_auditor_changed':False,'native_rerun':False,'mechanical_tolerances_changed':False},indent=2)+'\n')
 print(json.dumps({'status':r['status'],'gates':output['recovery_summary'],'response_sha256':sha(d/'response.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory');run(p.parse_args().directory)
