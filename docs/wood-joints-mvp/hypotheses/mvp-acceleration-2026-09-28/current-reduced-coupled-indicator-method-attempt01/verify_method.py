"""Known-answer reduced indicator replay; no frame solve or native run."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pyscipopt

HERE = Path(__file__).resolve().parent

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    method = module(HERE/'method.py', 'reduced_source_indicator_method')
    source_path = HERE.parent/'current-coupled-indicator-selector-fixture-attempt01/select_states.py'
    source = module(source_path, 'reduced_indicator_known_oracles')
    source.verify_source_pins()
    records = []
    for case in source.source_cases():
        K = np.asarray(case['operator_n_per_mm'], dtype=float)
        F = np.asarray(case['external_wrench_n'], dtype=float)
        c = np.asarray(case['contact_basis_diagonal'], dtype=float)
        assert np.all(c[1::2] == -1)
        B = np.diag(-c)
        H = B @ np.linalg.solve(K, B.T)
        e = B @ np.linalg.solve(K, F)
        n = len(F)
        laws = [{'kind': 'tangent'} if i%2 == 0 else
                {'kind': 'unilateral', 'k': case['normal_penalty_n_per_mm']}
                for i in range(n)]
        cells = [{'normal_row': 2*i+1,
                  'tangent_rows_and_references': [(2*i, -c[2*i]*r)]}
                 for i, r in enumerate(case['tangent_reference_mm'])]
        excluded, states, statuses = [], [], []
        complete = False
        for _ in range(2**len(cells)+1):
            model, q, f, a, bits = method.build(H, np.zeros((n, 0)), e, [],
                                               laws, cells, excluded)
            model.optimize()
            status = str(model.getStatus())
            statuses.append(status)
            if status == 'infeasible':
                complete = True
                break
            assert status == 'optimal' and model.getNSols() > 0, status
            sol = model.getBestSol()
            fv = np.array([model.getSolVal(sol, x) for x in f])
            qv = np.array([model.getSolVal(sol, x) for x in q])
            uv = np.linalg.solve(K, F-B.T@fv)
            assert np.max(np.abs(qv-B@uv)) < 1e-8
            mask = [model.getSolVal(sol, x) > .5 for x in bits]
            assert mask not in excluded
            state = {'closed_mask': mask,
                     'u_mm': [source.clean(x) for x in uv],
                     'tangent_forces_n': [source.clean(x) for x in fv[::2]],
                     'normal_forces_n': [source.clean(x) for x in fv[1::2]]}
            source.validate_solution(case, state)
            source.expected_matches(case, state)
            states.append(state)
            excluded.append(mask)
        assert complete
        assert sorted(excluded) == sorted(case['expected_masks_closed_true'])
        states.sort(key=lambda x: x['closed_mask'])
        records.append({'id': case['id'], 'states': states,
                        'zero_boundary_ambiguity': source.zero_boundary_ambiguity(case, states),
                        'terminal_infeasibility_proves_no_remaining_masks': True})
    # Two grounded elastic receivers with one raw rigid equilibrium equation.
    # Both signs test bilateral force and raw W rather than projected W=0.
    raw_records = []
    for sign in [1, -1]:
        model, q, f, a, bits = method.build([[1., 0.], [0., 2.]], [[1.], [1.]],
                [0., 0.], [3.*sign], [{'kind': 'bilateral', 'k': 2.},
                                    {'kind': 'bilateral', 'k': 4.}], [])
        model.optimize()
        assert str(model.getStatus()) == 'optimal'
        sol = model.getBestSol()
        values = [model.getSolVal(sol, x) for x in f+q+a]
        oracle = np.asarray([1.8, 1.2, .9, .3, 2.7])*sign
        assert np.max(np.abs(np.asarray(values)-oracle)) < 1e-8
        raw_records.append({'W_N': 3*sign, 'f_q_a': [source.clean(x) for x in values]})
    return {'status': 'PASS_REDUCED_COUPLED_INDICATOR_KNOWN_ANSWERS',
            'source_sha256': {p.name: sha(p) for p in [HERE/'method.py', Path(__file__), source_path]},
            'runtime': {'numpy': np.__version__, 'pyscipopt': pyscipopt.__version__},
            'coupled_oracles': records, 'raw_wrench_oracles': raw_records,
            'full_frame_solved': False, 'native_run': False,
            'initial_floor_state_or_event_captured': False,
            'physical_response_accepted': False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    value = run()
    target = HERE/'assessment.json'
    if args.verify:
        assert json.loads(target.read_text()) == value
        print('PASS_REPLAY_REDUCED_COUPLED_INDICATOR_KNOWN_ANSWERS')
    else:
        target.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
        print(value['status'])
