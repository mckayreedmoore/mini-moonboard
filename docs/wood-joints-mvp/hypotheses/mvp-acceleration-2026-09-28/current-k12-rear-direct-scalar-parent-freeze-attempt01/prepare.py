"""Parent preparation only; never invokes a solver."""
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from fea.wood_joint_reduced_native import freeze, write_json

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE / 'current-k12-rear-spr489-cascade-trace-attempt01'
DEST = BASE / 'current-k12-rear-direct-scalar-native-attempt01'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    pins = json.loads((SOURCE / 'source-pins.json').read_text())
    paths = []
    for mapping, root in [(pins['source_files'], ROOT), (pins['output_files'], SOURCE)]:
        for name, expected in mapping.items():
            path = root / name
            assert sha(path) == expected, name
            paths.append(path)
    deck = (SOURCE / 'direct-scalar-coupon/model.inp').read_text()
    meta = json.loads((SOURCE / 'direct-scalar-coupon/model.json').read_text())
    nodes, elements, fixed, loads, raw_eq = {}, [], set(), [], []
    spring_rows = {}
    card = ''
    for line in deck.splitlines():
        if line.startswith('**') or not line.strip():
            continue
        if line.startswith('*'):
            card = line.upper()
            if card.startswith('*CLOAD'):
                loads.append({})
            continue
        fields = [s.strip() for s in line.split(',') if s.strip()]
        if card.startswith('*NODE,'):
            nodes[int(fields[0])] = [float(s) for s in fields[1:]]
        elif card.startswith('*ELEMENT'):
            elements.append({'id': int(fields[0]), 'nodes': [int(s) for s in fields[1:]], 'card': card})
        elif card.startswith('*EQUATION'):
            raw_eq.extend(fields)
        elif card.startswith('*BOUNDARY'):
            if fields[1:3] == ['1','3']:
                fixed.add(int(fields[0]))
        elif card.startswith('*CLOAD'):
            loads[-1][(int(fields[0]), int(fields[1]))] = float(fields[2])
        elif card.startswith('*SPRING,'):
            spring_rows.setdefault(card, []).append([float(s) for s in fields])
    count = int(raw_eq.pop(0))
    assert count == 81 and len(raw_eq) == 3 * count
    equation = [(int(raw_eq[i]), int(raw_eq[i+1]), float(raw_eq[i+2])) for i in range(0,len(raw_eq),3)]
    assert equation[0] == (90001,1,1.0)
    c = {(n,d): -v for n,d,v in equation[1:]}
    assert len(c) == 80 and len(nodes) == 82 and len(elements) == 81 and len(loads) == 3
    assert spring_rows['*SPRING,ELSET=SUPPORT_Y'] == [[2.0,2.0],[100.0]]
    assert spring_rows['*SPRING,ELSET=SUPPORT_Z'] == [[3.0,3.0],[100.0]]
    table = spring_rows['*SPRING,ELSET=JOINT,NONLINEAR']
    assert table[:2] == [[0.0,-10.0],[0.0,0.0]] and table[2][1] == 10.0
    k = table[2][0] / table[2][1]
    oracle = []
    for step, (f, state) in enumerate(zip(loads, meta['known_answer_states']), 1):
        assert set(f) == set(c)
        bare = math.fsum(c[t]*f[t]/100.0 for t in c)
        q = bare / (1 + k*math.fsum(v*v for v in c.values())/100.0) if bare > 0 else bare
        force = k * max(q,0)
        u = {f'{n}:{d}': (f[n,d]-force*c[n,d])/100.0 for n,d in c}
        check_q = math.fsum(c[n,d]*u[f'{n}:{d}'] for n,d in c)
        assert abs(check_q-q) < 1e-12
        assert abs(q-state['serialized_equation_q_mm']) < 1e-12
        oracle.append({'step':step,'q_mm':q,'joint_force_N':force,'master_u_mm':u,'equation_residual_mm':check_q-q})
    audit = {'scope':'known-answer direct scalar method only; no production change or joint acceptance',
             'source_deck_sha256':sha(SOURCE/'direct-scalar-coupon/model.inp'),
             'serialized_rank_one_oracle':oracle, 'all_input_checks_passed':True}
    write_json(Path(__file__).parent/'parent-analytic-audit.json', audit)
    meta['scope'] = 'SPR489 direct scalar known-answer method coupon only; no frame demands or joint acceptance'
    meta['parent_serialized_oracle'] = oracle
    structure = SimpleNamespace(nodes=nodes,elements=elements,loads={},fixed=fixed,
                                equations=[equation],springs=[],panels={},rotation_masters=set())
    checker = BASE/'current-k12-rear-direct-scalar-parent-method-attempt01/check.py'
    assert checker.exists(), 'Independent output checker must exist before freeze'
    checker_audit_path = Path(__file__).parent/'independent-checker-input-audit-final.json'
    checker_audit = json.loads(checker_audit_path.read_text())
    assert checker_audit['checker_sha256'] == sha(checker)
    assert checker_audit['status'] == 'PASS_INPUT_ONLY_INDEPENDENT_RANK_ONE_ORACLE'
    for own, independent in zip(oracle, checker_audit['rank_one_serialized_oracle']):
        assert abs(own['q_mm']-independent['analytic_q_mm']) < 1e-12
        assert abs(own['joint_force_N']-independent['analytic_joint_force_N']) < 1e-9
        assert set(own['master_u_mm']) == set(independent['analytic_master_displacements_mm'])
        assert max(abs(v-independent['analytic_master_displacements_mm'][key])
                   for key,v in own['master_u_mm'].items()) < 1e-12
    paths += [Path(__file__).resolve(), Path(__file__).parent/'parent-analytic-audit.json',
              SOURCE/'source-pins.json', SOURCE/'produce.py',checker,checker_audit_path]
    paths += [p for p in checker.parent.iterdir() if p.is_file()]
    freeze(DEST,structure,meta,extra_sources=paths,deck_text=deck)
    print('Frozen method coupon:', DEST)

if __name__ == '__main__':
    main()
