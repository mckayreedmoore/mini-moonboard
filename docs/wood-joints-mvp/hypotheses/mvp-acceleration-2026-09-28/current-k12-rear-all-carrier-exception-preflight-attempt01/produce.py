"""Enumerate source-law exceptions in rejected output; never adopts forces."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
AUDIT=BASE/'current-springa-zero-u-token-response-audit-attempt01/response_audit.py'
NATIVE=BASE/'current-springa-selected-floor-k12-rear-attempt03'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def build():
    assert sha(AUDIT)=='711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0'
    spec=importlib.util.spec_from_file_location('pinned711carrier_preflight',AUDIT)
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    record=json.loads((NATIVE/'model.json').read_text())
    deck=(NATIVE/'model.inp').read_text()
    context=json.loads((NATIVE/'case-context.json').read_text())
    contract=audit._validate_model(record,deck,context)
    parsed=audit.parse_native_blocks((NATIVE/'model.dat').read_text())
    errors=[];count=0
    for time,state in parsed.items():
        for binding in contract['bindings']:
            source=contract['source_by_group'][str(binding['group'])]
            try:audit.audit_springa(binding,source,state,contract['emitted_nodes'])
            except (audit.ResponseAuditError,audit._stable.ResponseAuditError) as exc:
                errors.append({'time':time,'source_row_id':binding['source_row_id'],
                               'group':binding['group'],'error':str(exc)})
            count+=1
    paths=[Path(__file__),AUDIT,AUDIT.parent/'stable_response_audit.py']
    paths += [NATIVE/name for name in ['model.json','model.inp','model.dat','case-context.json','freeze.json','execution.json']]
    return {'scope':'Read-only diagnostic of rejected K12rear03 output; no forces accepted',
            'source_sha256':{str(p):sha(p) for p in paths},
            'checked_increment_count':len(parsed),'carrier_checks':count,
            'exception_count':len(errors),'exceptions':errors,
            'all_body_balance_or_corner_forces_accepted':False,'native_run_performed':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    result=build();out=HERE/'diagnosis.json'
    if args.verify:assert result==json.loads(out.read_text());print('PASS_REJECTED_OUTPUT_EXCEPTION_DIAGNOSIS_REPRODUCED')
    else:
        assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'checks':result['carrier_checks'],'errors':result['exceptions']},indent=2))
