"""Read-only immutable case audit; convert NumPy scalars for JSON only."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
import numpy as np
HERE=Path(__file__).resolve().parent
AUDITOR=HERE.parent/'current-springa-zero-u-token-response-audit-attempt01/response_audit.py'
PIN='711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def primitive(v):
 if isinstance(v,np.generic):return primitive(v.item())
 if isinstance(v,dict):return {k:primitive(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [primitive(x) for x in v]
 if v is None or type(v) in (bool,int,float,str):return v
 raise TypeError(type(v))
def run(directory):
 d=Path(directory).resolve();assert sha(AUDITOR)==PIN
 sp=importlib.util.spec_from_file_location('immutable_zero_u_case_auditor',AUDITOR);a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
 cpath=d/'case-context.json';c=json.loads(cpath.read_text());model=d/'model.json';dat=d/'model.dat';deck=d/'model.inp';exe=d/'execution.json'
 provenance=a._validate_execution(model,dat,deck,exe,dat.read_text(),c)
 r=a.audit_record(json.loads(model.read_text()),dat.read_text(),deck.read_text(),c)
 assert r['status']=='PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY'
 r.update(source_input_model_json_sha256=sha(model),source_input_model_json_path=str(model),source_input_deck_path=str(deck),native_data_path=str(dat),case_context_path=str(cpath),case_context_sha256=sha(cpath),terminal_execution_provenance=provenance)
 out=primitive(r);encoded=json.dumps(out,indent=2,allow_nan=False)+'\n';assert json.loads(encoded)==out
 output=d/'response-zero-u-token.json';assert not output.exists(),'Do not replace an existing response'
 output.write_text(encoded)
 (d/'parent-report-serialization.json').write_text(json.dumps({'status':'PASS_NUMPY_SCALAR_JSON_CONVERSION_ONLY','auditor_sha256':sha(AUDITOR),'writer_sha256':sha(Path(__file__)),'response_sha256':sha(output),'frozen_auditor_changed':False,'native_rerun':False,'mechanical_tolerances_changed':False,'case_context_sha256':sha(cpath)},indent=2)+'\n')
 print(json.dumps({'status':out['status'],'response_sha256':sha(output),'case_id':c['case_id'],'increment_count':len(out['increments'])}))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('directory');run(ap.parse_args().directory)
