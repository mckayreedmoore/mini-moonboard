"""One parent-owned bounded convex gravity-direction selection, no native run."""
from pathlib import Path
import fcntl
import hashlib
import importlib.util
import json
import os
import resource
import signal
import time

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, x):
    p.write_text(json.dumps(x, indent=2, sort_keys=True, allow_nan=False)+'\n')

def run():
    import numpy as np
    assert not (HERE/'inputs.json').exists(), 'One-shot attempt already recorded'
    assert os.environ.get('OPENBLAS_NUM_THREADS') == '1'
    resource.setrlimit(resource.RLIMIT_AS, (6*1024**3, 6*1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    signal.signal(signal.SIGALRM, lambda *args: (_ for _ in ()).throw(TimeoutError('180 s wall cap')))
    signal.alarm(180)
    operators = BASE/'current-frame-connector-compliance-attempt04'
    method_dir = BASE/'current-floor-binary-convex-energy-adapter-attempt01'
    factor_dir = BASE/'current-frame-convex-energy-factor-preflight-attempt01'
    projection = BASE/'current-frame-physical-connector-projection-contract-attempt01/projection-contract.json'
    join = BASE/'current-floor-normal-tangent-join-contract-attempt01/join-contract.json'
    contract = BASE/'current-gravity-direction-initial-selector-contract-attempt01/README.md'
    native_replay = BASE/'current-frame-connector-compliance-attempt04-a12-response-replay-attempt01/assessment.json'
    paths = [Path(__file__), projection, join, contract, native_replay,
             operators/'inputs.json', operators/'assessment.json', operators/'output-pin.json',
             operators/'operators.npz', operators/'row-identities.json',
             method_dir/'adapter.py', method_dir/'verify_adapter.py', method_dir/'assessment.json',
             factor_dir/'factor_energy.py', factor_dir/'inputs.json', factor_dir/'assessment.json',
             factor_dir/'output-pin.json', factor_dir/'energy-factor.npz']
    inputs = {'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in paths},
              'scope': 'a12-rear beta->0+ gravity direction only; initial u=f=q=0; no guessed mask; provisional search only',
              'first_solve_limit_s': 45., 'second_floor_branch_limit_s': 30.,
              'wall_limit_s': 180, 'memory_limit_bytes': 6*1024**3,
              'native_launch': False, 'automatic_retry': False,
              'formulation': 'symmetric elastic energy; ordinary unilateral convex hinges; 100 floor binaries',
              'force_recovery': 'provisional SCIP g=L^-T*y; source audits mandatory; no frame-scale QP polish authorized here',
              'symmetrization': 'explicit approximation; raw H retained for compatibility audit'}
    write(HERE/'inputs.json', inputs)
    for p in paths:
        if p.suffix == '.py':
            target = HERE/'sources'/p.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(p.read_bytes())
    report = {'status': 'RUNNING', 'input_record_sha256': sha(HERE/'inputs.json'),
              'case_id': 'a12-rear', 'native_launch': False,
              'physical_response_accepted': False, 'accepted_case_count_changed': False,
              'initial_floor_references_mm': [0., 0.], 'solves': []}
    started = time.monotonic()
    try:
        assessment = json.loads((operators/'assessment.json').read_text())
        assert assessment['status'] == 'PASS_SOURCE_BOUND_FRAME_CONNECTOR_COMPLIANCE'
        assert sha(operators/'assessment.json') == json.loads((operators/'output-pin.json').read_text())['assessment_sha256']
        for rel, expected in json.loads((operators/'inputs.json').read_text())['source_sha256'].items():
            assert sha(ROOT/rel) == expected
        for name, expected in assessment['outputs_sha256'].items():
            assert sha(operators/name) == expected
        assert json.loads(native_replay.read_text())['status'] == 'PASS_A12_REAR_AUTHENTICATED_RESPONSE_REPLAY_AGAINST_FROZEN_REDUCTION'
        fixture = json.loads((method_dir/'assessment.json').read_text())
        assert fixture['status'] == 'PASS_TINY_FLOOR_BINARY_CONVEX_ENERGY_ADAPTER'
        for name in ['adapter.py', 'verify_adapter.py']:
            assert sha(method_dir/name) == fixture['source_sha256'][name]
        factor_record = json.loads((factor_dir/'assessment.json').read_text())
        assert factor_record['status'] == 'PASS_NUMERICAL_SYMMETRIC_ENERGY_FACTOR'
        assert sha(factor_dir/'energy-factor.npz') == factor_record['energy_factor_sha256']
        assert sha(factor_dir/'assessment.json') == json.loads((factor_dir/'output-pin.json').read_text())['assessment_sha256']
        for rel, expected in json.loads((factor_dir/'inputs.json').read_text())['source_sha256'].items():
            assert sha(ROOT/rel) == expected
        spec = importlib.util.spec_from_file_location('source_coupled_direction', method_dir/'adapter.py')
        method = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(method)
        with np.load(operators/'operators.npz') as z:
            H, D, e, W = z['H'], z['D'], z['e'][:, 0], z['W'][:, 0]
        with np.load(factor_dir/'energy-factor.npz') as z:
            L = z['L']
        assert np.linalg.norm(L@L.T-(H+H.T)/2, ord=np.inf)/np.linalg.norm(H, ord=np.inf) < 1e-12
        assert assessment['load_columns'][0] == {'column': 0, 'case_id': 'a12-rear', 'kind': 'gravity_nodal_map'}
        rows = json.loads(projection.read_text())['rows']
        laws = []
        for row in rows:
            family = row['family']
            if family == 'conditional_floor_tangent_constraint':
                laws.append({'kind': 'tangent'})
            else:
                laws.append({'kind': 'bilateral' if family == 'bilateral_spring2' else 'unilateral',
                             'k': row['law']['stiffness_N_per_mm']})
        joined = json.loads(join.read_text())['cells']
        cells = [{'normal_row': cell['normal_B_row_position'],
                  'tangent_rows_and_references': [(t['B_row_position'], 0.) for t in cell['tangent_rows']]}
                 for cell in joined]
        assert len(cells) == 100 and len(rows) == 1840
        excluded = []
        for number, limit in enumerate([45., 30.]):
            build_started = time.monotonic()
            model, variables = method.build_model(L, D, e, W, laws, cells, excluded, limit)
            qvar, avar, bits = variables['q'], variables['a'], variables['floor_bits']
            build_elapsed = time.monotonic()-build_started
            model.setLogfile(str(HERE/f'scip-solve-{number+1}.log'))
            model.optimize()
            status = str(model.getStatus())
            entry = {'solve': number+1, 'solver_status': status, 'solutions': model.getNSols(),
                     'build_elapsed_seconds': build_elapsed, 'solving_time_seconds': model.getSolvingTime(),
                     'nodes': model.getNNodes(), 'original_floor_binary_count': len(bits)}
            report['solves'].append(entry)
            if status == 'infeasible':
                report['status'] = 'NO_ENERGY_FEASIBLE_BRANCH_UNDER_SYMMETRIC_APPROXIMATION' if not excluded else 'UNIQUE_STRICT_FLOOR_DIRECTION_CANDIDATE_REQUIRES_FINAL_VALIDATION'
                break
            if status != 'optimal' or model.getNSols() == 0:
                report['status'] = 'BUDGET_OR_SOLVER_STOP'
                break
            sol = model.getBestSol()
            q = np.array([model.getSolVal(sol, x) for x in qvar])
            y = np.array([model.getSolVal(sol, x) for x in variables['y']])
            f = np.linalg.solve(L.T, y)
            a = np.array([model.getSolVal(sol, x) for x in avar])
            mask = [model.getSolVal(sol, x) > .5 for x in bits]
            assert mask not in excluded
            np.savez_compressed(HERE/f'candidate-{number+1}.npz', q=q, f=f, a=a, floor_mask=np.array(mask))
            balance = D.T@f-W
            spring_error = []
            selected = []
            for i, law in enumerate(laws):
                if law['kind'] == 'tangent':
                    continue
                expected = law['k']*(q[i] if law['kind'] == 'bilateral' else max(q[i], 0.))
                spring_error.append(abs(f[i]-expected))
                if law['kind'] == 'bilateral' or q[i] > 0:
                    selected.append(i)
            boundary, floor_error = [], 0.
            for j, (held, cell) in enumerate(zip(mask, cells)):
                ni = cell['normal_row']
                if (held and (q[ni] <= 2e-8 or f[ni] <= 1e-8)) or (not held and q[ni] >= -2e-8):
                    boundary.append(j)
                for ti, reference in cell['tangent_rows_and_references']:
                    if held:
                        selected.append(ti)
                        floor_error = max(floor_error, abs(q[ti]-reference))
                    else:
                        floor_error = max(floor_error, abs(f[ti]))
            singular = np.linalg.svd(D[selected, :], compute_uv=False)
            rank = int(np.count_nonzero(singular > 1e-10*singular[0]))
            entry.update({'bearing_cells': sum(mask), 'boundary_cells': boundary,
                          'actual_branch_rigid_rank': rank, 'actual_branch_nullity': 300-rank,
                          'max_raw_body_force_residual_N': float(np.max(np.abs(balance.reshape(50, 6)[:, :3]))),
                          'max_raw_body_moment_residual_Nmm': float(1000*np.max(np.abs(balance.reshape(50, 6)[:, 3:]))),
                          'max_compatibility_residual_mm': float(np.max(np.abs(q-D@a-e+H@f))),
                          'max_source_spring_law_residual_N': float(max(spring_error)),
                          'max_held_q_or_released_T_residual': float(floor_error),
                          'max_directional_extension_mm': float(np.max(np.abs(q[:1640])))})
            if entry['max_raw_body_force_residual_N'] > .1 or entry['max_raw_body_moment_residual_Nmm'] > 2. or entry['max_source_spring_law_residual_N'] > .1 or entry['max_compatibility_residual_mm'] > 2e-8 or floor_error > 2e-8:
                report['status'] = 'STOP_PROVISIONAL_ENERGY_CANDIDATE_REJECTED_UNRESOLVED'
                entry['limit'] = 'Not a no-state proof: other floor masks may have physical equilibria; frame-scale polishing is not validated here.'
                break
            if boundary:
                report['status'] = 'AMBIGUOUS_ZERO_BOUNDARY'
                break
            if rank < 300:
                report['status'] = 'STOP_ACTUAL_BRANCH_NULLSPACE_REQUIRES_IDENTIFICATION'
                break
            excluded.append(mask)
            if number == 1:
                report['status'] = 'MULTIPLE_PHYSICAL_FLOOR_EPISODE_BRANCHES'
    except Exception as error:
        report['status'] = 'STOP_DIRECTIONAL_SELECTION_EXCEPTION'
        report['exception'] = repr(error)
    finally:
        signal.alarm(0)
        report['elapsed_seconds'] = time.monotonic()-started
        report['outputs_sha256'] = {p.name: sha(p) for p in HERE.glob('candidate-*.npz')}
        report['solver_log_sha256'] = {p.name: sha(p) for p in HERE.glob('scip-solve-*.log')}
        report['limits'] = ['Directional coefficient only; no gravity settlement or climber ramp accepted.',
                            'Energy ranking never establishes physical history; provisional force recovery must pass all original gates.',
                            'Tiny fixed-mask polishing code is not applied to the full frame.',
                            'Actual branch nullspace is never removed by a guessed anchor.',
                            'Solver/boundary/multiple-state stop is missing usable evidence, not physical failure.']
        if any(sha(ROOT/rel) != expected for rel, expected in inputs['source_sha256'].items()):
            report['status'] = 'STOP_SOURCE_CHANGED_DURING_SELECTION'
        write(HERE/'assessment.json', report)
        write(HERE/'output-pin.json', {'assessment_sha256': sha(HERE/'assessment.json')})
        print(json.dumps(report, indent=2))

if __name__ == '__main__':
    lock = ROOT/'docs/wood-joints-mvp/luna-max-native-run-ledger.lock'
    with lock.open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert json.loads(lock.with_suffix('.json').read_text())['slot']['state'] == 'idle'
        run()
