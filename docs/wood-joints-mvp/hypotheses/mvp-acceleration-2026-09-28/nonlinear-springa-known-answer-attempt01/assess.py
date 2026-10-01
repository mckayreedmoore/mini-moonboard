"""Check native straight-line scalar-law, isolated endpoint force and load-step closure."""
import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;NATIVE=HERE/'native'

def evaluate():
    freeze=json.loads((NATIVE/'freeze.json').read_text())
    for name,pin in freeze['files_sha256'].items():
        assert hashlib.sha256((NATIVE/name).read_bytes()).hexdigest()==pin
    execution=json.loads((NATIVE/'execution.json').read_text())
    assert execution['native_solve_executed'] is True and execution['returncode']==0
    stdout=(NATIVE/'native.stdout').read_text();stderr=(NATIVE/'native.stderr').read_text()
    assert '*ERROR' not in (stdout+stderr).upper()
    data=(NATIVE/'model.dat').read_text()
    blocks={}
    pattern=r'^\s*(displacements|forces)\s*\([^\n]*\btime\s+([0-9.EeDd+-]+)\s*\n'
    for match in re.finditer(pattern,data,re.MULTILINE):
        rows={};started=False
        for line in data[match.end():].splitlines():
            fields=line.split()
            if len(fields)==4 and fields[0].isdigit():
                tag=int(fields[0]);assert tag not in rows
                rows[tag]=[float(v.replace('D','E')) for v in fields[1:]];started=True
            elif started:break
        time=float(match[2].replace('D','E'))
        assert (time,match[1]) not in blocks
        blocks[(time,match[1])]=rows
    model=json.loads((NATIVE/'model.json').read_text())
    results=[]
    for expected in model['known_answer']['steps']:
        time=expected['time'];U=blocks[(time,'displacements')];RF=blocks[(time,'forces')]
        assert set(U)==set(RF)==set(range(1,6))
        assert abs(U[1][0]-expected['u_mm'])<2e-6
        assert max(abs(U[n][j]) for n in U for j in [1,2])<2e-6
        assert abs(U[3][0])<2e-6 and abs(U[5][0])<2e-6
        assert abs(U[2][0]-U[1][0])<2e-6 and abs(U[4][0]-U[1][0])<2e-6
        spring_rows=[];physical=0.
        for name,first,second,law,expected_force in [
            ('positive',2,3,lambda delta:100*max(delta,0.),expected['positive_internal_force_N']),
            ('negative',4,5,lambda delta:200*min(delta,0.),expected['negative_internal_force_N'])]:
            delta=U[first][0]-U[second][0];assert abs(delta)<10. and 100.+delta>0.
            # Fixed transverse coordinates make current-length minus initial-length exactly delta.
            elongation=abs(100.+delta)-100.;assert abs(elongation-delta)<1e-12
            internal=law(delta)
            assert abs(internal-expected_force)<.002
            assert abs(RF[first][0]-internal)<.002 and abs(RF[second][0]+internal)<.002
            assert abs(RF[first][0]+RF[second][0])<.002
            on_first=.5*(RF[second][0]-RF[first][0]);physical+=on_first
            spring_rows.append({'name':name,'delta_mm':delta,'table_internal_force_N':internal,
                                'RF_first_second_N':[RF[first][0],RF[second][0]],'physical_force_on_first_N':on_first})
        residual=physical+expected['external_force_N'];assert abs(residual)<.002
        ground=RF[3][0]+RF[5][0];assert abs(ground+expected['external_force_N'])<.002
        results.append({'time':time,'physical_u_mm':U[1][0],'spring_rows':spring_rows,
                        'physical_equilibrium_residual_N':residual,'ground_reaction_N':ground})
    return {'status':'PASS_NATIVE_STRAIGHT_SPRINGA_LAW_AND_ENDPOINT_FORCE_FIXTURE','steps':results,
            'native_solve_executed':True,'method_fixture_passed':True,'qualified_for_design':False,
            'floor_conditional_stick_verified':False,'complete_joint_validated':False,
            'input_freeze_sha256':hashlib.sha256((NATIVE/'freeze.json').read_bytes()).hexdigest(),
            'execution_sha256':hashlib.sha256((NATIVE/'execution.json').read_bytes()).hexdigest(),
            'model_dat_sha256':hashlib.sha256((NATIVE/'model.dat').read_bytes()).hexdigest(),
            'limits':model['limits']}
if __name__=='__main__':
    try:result=evaluate()
    except Exception as exc:
        result={'status':'FAILED_METHOD_CHECK','method_fixture_passed':False,'qualified_for_design':False,
                'error':type(exc).__name__+': '+str(exc)}
        (HERE/'assessment.json').write_text(json.dumps(result,indent=2)+'\n')
        raise
    (HERE/'assessment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])
