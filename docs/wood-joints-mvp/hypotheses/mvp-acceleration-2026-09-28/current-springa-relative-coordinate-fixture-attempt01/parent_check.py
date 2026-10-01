"""Independent closed-form check of every converged printed fixture increment."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def check():
    data = (HERE / 'native/model.dat').read_text()
    blocks = {}
    for match in re.finditer(r'^\s*(displacements|forces)\s*\([^\n]*\btime\s+([0-9.EeDd+-]+)\s*\n', data, re.M):
        rows = {}
        for line in data[match.end():].splitlines():
            fields = line.split()
            if len(fields) == 4 and fields[0].isdigit():
                rows[int(fields[0])] = [float(x.replace('D', 'E')) for x in fields[1:]]
            elif rows:
                break
        blocks[float(match[2]), match[1]] = rows
    results = []
    for time in sorted({t for t, _ in blocks}):
        U, RF = blocks[time, 'displacements'], blocks[time, 'forces']
        assert set(U) == set(RF) == set(range(1, 11))
        force_a = -30*time if time <= 1 else (-30+60*(time-1) if time <= 2 else 30-60*(time-2))
        force_b = -force_a
        # Independent inversion of the closed 2x2 stiffness or open supports.
        if force_a < 0:
            expected_a, expected_b = force_a/175., -force_a/350.
        else:
            expected_a, expected_b = force_a/100., force_b/200.
        expected_joint = 50*max(expected_b-expected_a, 0.)
        assert abs(U[1][0]-expected_a) < 2e-6 and abs(U[2][0]-expected_b) < 2e-6
        assert abs(U[9][0]-(U[2][0]-U[1][0])) < 2e-6
        assert abs(RF[9][0]-expected_joint) < .002 and abs(RF[9][0]+RF[10][0]) < .002
        assert abs(RF[3][0]-100*U[1][0]) < .002 and abs(RF[5][0]-200*U[2][0]) < .002
        residual_a = force_a-RF[3][0]+RF[9][0]
        residual_b = force_b-RF[5][0]-RF[9][0]
        global_residual = force_a+force_b+RF[4][0]+RF[6][0]
        assert max(abs(residual_a), abs(residual_b), abs(global_residual)) < .002
        results.append({'time': time, 'body_A_residual_N': residual_a,
                        'body_B_residual_N': residual_b, 'global_physical_residual_N': global_residual,
                        'virtual_ground_RF_N_excluded': RF[10][0]})
    assert {1., 2., 3.}.issubset({x['time'] for x in results})
    assert any(abs(x['virtual_ground_RF_N_excluded']) > 1. for x in results)
    result = {'status': 'PASS_PARENT_ALL_INCREMENT_CLOSED_FORM_AND_PHYSICAL_BALANCE',
              'increment_count': len(results),
              'max_body_residual_N': max(max(abs(x['body_A_residual_N']), abs(x['body_B_residual_N'])) for x in results),
              'max_global_physical_residual_N': max(abs(x['global_physical_residual_N']) for x in results),
              'model_dat_sha256': hashlib.sha256((HERE/'native/model.dat').read_bytes()).hexdigest(),
              'increments': results, 'limits': 'Scalar known-answer coupling only, not floor/frame/joint capacity.'}
    (HERE / 'parent-check.json').write_text(json.dumps(result, indent=2)+'\n')
    print({k: v for k, v in result.items() if k != 'increments'})


if __name__ == '__main__':
    check()
