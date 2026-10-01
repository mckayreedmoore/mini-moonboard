"""Recover only NumPy scalar serialization after the pinned audit passes."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parent.parent
AUDIT = BASE/'current-a12-rear-bg001-seat-stiffness-run-readiness-attempt01/audit_variant_run.py'
RUN = BASE/'current-a12-rear-bg001-seat-stiffness-native-attempt01'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def primitive(value):
    if isinstance(value,np.generic):
        return primitive(value.item())
    if isinstance(value,dict):
        return {k:primitive(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [primitive(v) for v in value]
    if value is None or isinstance(value,(str,bool,int,float)):
        return value
    raise TypeError('Unexpected report value type: '+type(value).__name__)

def main():
    contract=json.loads((AUDIT.parent/'readiness-contract.json').read_text())
    assert sha(AUDIT)==contract['postrun']['fork_audit_script_sha256']
    assert not (RUN/'response.json').exists()
    spec=importlib.util.spec_from_file_location('pinned_sensitivity_run_audit',AUDIT)
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    try:
        audit.run(RUN)
        raise AssertionError('Expected recorded NumPy scalar serialization failure')
    except TypeError as exc:
        # The complete pinned function has already performed execution/source
        # authentication and every mechanical gate. Recover its report only
        # at the final JSON rendering statement, never at a failed check.
        tb=exc.__traceback__;frame=None;line=None
        while tb:
            if tb.tb_frame.f_code is audit.run.__code__:
                frame=tb.tb_frame;line=tb.tb_lineno
            tb=tb.tb_next
        assert frame is not None
        source_line=AUDIT.read_text().splitlines()[line-1]
        assert 'output_path.write_text(json.dumps(report' in source_line
        assert str(exc)=='Object of type bool is not JSON serializable'
        report=frame.f_locals['report']
        assert report['status']=='PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY'
        assert report['mechanical_acceptance'] is False
        assert report['terminal_execution_provenance']['native_output_hashes_match'] is True
        rendered=primitive(report)
        rendered['parent_serialization_recovery']={
            'only_numpy_scalars_converted_via_item':True,
            'original_complete_audit_source_sha256':sha(AUDIT),
            'parent_writer_sha256':sha(Path(__file__)),
            'mechanical_gates_or_tolerances_changed':False,
            'original_failure':'NumPy bool scalar JSON serialization after every physical gate passed'}
        (RUN/'response.json').write_text(json.dumps(rendered,indent=2,allow_nan=False)+'\n')
        print(rendered['status'],len(rendered['increments']),'increments; serialization recovery only')

if __name__=='__main__':
    main()
