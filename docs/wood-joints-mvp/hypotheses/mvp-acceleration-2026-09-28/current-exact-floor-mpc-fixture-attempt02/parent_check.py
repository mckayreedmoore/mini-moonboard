"""Independent parent hand solution at every printed native increment."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
raw = (HERE / 'native/model.dat').read_text()
blocks = {}
for match in re.finditer(r'^\s*(displacements|forces) [^\n]*time\s+([\d.E+-]+)\n', raw, re.M):
    rows = {}
    for line in raw[match.end():].splitlines():
        fields = line.split()
        if len(fields) == 4 and fields[0].isdigit():
            rows[int(fields[0])] = tuple(map(float, fields[1:]))
        elif rows:
            break
    key = (match[1], float(match[2]))
    assert key not in blocks
    blocks[key] = rows
max_u = max_force = max_balance = 0.
records = []
for kind, time in sorted(blocks):
    if kind != 'displacements':
        continue
    u, rf = blocks[(kind, time)], blocks[('forces', time)]
    assert set(u) == set(rf) == set(range(1, 9))
    # Applied forces ramp from zero to case 1, then from case 1 to case 2.
    wx = 6*time if time <= 1 else 6-10*(time-1)
    wz = -20*time if time <= 1 else -20-20*(time-1)
    # x=0. Structural Kzz=100; normal closed-branch k=100.
    z = wz/200
    expected_u = {1:(0.,0.,z), 2:(0.,0.,0.), 3:(z/4,0.,0.),
                  4:(0.,0.,0.), 5:(0.,0.,z), 6:(0.,0.,0.),
                  7:(0.,0.,-z), 8:(0.,0.,0.)}
    max_u = max(max_u, *(abs(u[n][d]-v[d]) for n,v in expected_u.items() for d in range(3)))
    # RF at the fixed reference includes the eliminated CLOAD. Its raw
    # value equals the structural x internal force here, not the reaction.
    fs, fz, normal = 5*z, 98.75*z, -100*z
    expected_rf = {1:(0.,0.,wz), 2:(fs,0.,0.), 3:(fs,0.,0.),
                   4:(-fs,0.,0.), 5:(0.,0.,fz), 6:(0.,0.,-fz),
                   7:(0.,0.,normal), 8:(0.,0.,-normal)}
    max_force = max(max_force, *(abs(rf[n][d]-v[d]) for n,v in expected_rf.items() for d in range(3)))
    reaction_x = rf[2][0]-wx
    balances = (wx+reaction_x-20*u[3][0],
                wz-5*u[3][0]-98.75*u[5][2]+rf[7][2])
    max_balance = max(max_balance, *map(abs, balances))
    records.append({'time':time, 'applied_x_z_N':[wx,wz],
                    'recovered_floor_x_N':reaction_x,
                    'physical_body_residual_x_z_N':balances})
assert len(records) == 12
assert max_u < 2e-6 and max_force < .002 and max_balance < .002
result = {'status':'PASS_PARENT_ALL_PRINTED_INCREMENT_CHECK',
          'printed_increment_count':len(records), 'max_displacement_error_mm':max_u,
          'max_RF_error_N':max_force, 'max_body_balance_residual_N':max_balance,
          'reaction_rule':'RF_REFERENCE_MINUS_DEPENDENT_CLOAD',
          'numerical_normal_ground_is_physical_support':False,
          'frame_ready':False, 'complete_joint_validated':False,
          'model_dat_sha256':hashlib.sha256((HERE/'native/model.dat').read_bytes()).hexdigest(),
          'records':records}
(HERE/'parent-all-increment-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='records'}))
