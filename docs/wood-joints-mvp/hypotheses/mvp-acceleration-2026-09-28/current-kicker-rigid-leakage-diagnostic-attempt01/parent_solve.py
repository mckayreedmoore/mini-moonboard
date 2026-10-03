"""One parent-owned replay retaining the stopped iterate for an equation audit."""
from pathlib import Path
import fcntl
import hashlib
import importlib.util
import json
import resource

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def run():
    import numpy as np
    import scipy.sparse as sp
    output = HERE / 'parent-result.json'
    assert not output.exists(), 'Preserve the first replay; no automatic retry'
    packet = json.loads((HERE / 'packet.json').read_text())
    assert packet['status'] == 'PASS_EXACT_KICKER_CHUNK_PREPARED_NO_SOLVE'
    for name, key in [('body-K.npz', 'body_K_sha256'), ('basis.npz', 'basis_sha256'), ('source-rows.json', 'source_rows_sha256')]:
        assert sha(HERE / name) == packet[key]
    parent = HERE.parent / 'current-frame-connector-compliance-attempt02'
    assert sha(parent / 'assessment.json') == packet['parent_attempt02_assessment_sha256']
    assert sha(parent / 'inputs.json') == packet['parent_attempt02_inputs_sha256']
    inputs = json.loads((parent / 'inputs.json').read_text())
    for rel, expected in inputs['source_sha256'].items():
        assert sha(ROOT / rel) == expected
    helper = module('kicker_parent_helper', HERE.parent / 'current-frame-free-body-condensation-preflight-attempt01/condensation.py')
    wrapper = module('kicker_parent_refine', HERE.parent / 'current-bordered-refinement-diagnostic-attempt01/bounded_refinement.py')
    resource.setrlimit(resource.RLIMIT_AS, (6 * 1024**3, 6 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    ledger = ROOT / 'docs/wood-joints-mvp/luna-max-native-run-ledger.json'
    with ledger.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert json.loads(ledger.read_text())['slot']['state'] == 'idle'
        K = sp.load_npz(HERE / 'body-K.npz')
        data = np.load(HERE / 'basis.npz')
        factor, A = helper.factor_bordered(K, data['R'])
        result = wrapper.solve_bordered_chunk_refined(factor, A, data['R'], data['projected'])
    assert result['status'] == 'UNRESOLVED_REFINEMENT_STAGNATION'
    original = json.loads((parent / 'assessment.json').read_text())['stopping_gate']['numerical_result']
    assert result['history'] == original['history']
    u, lam = result['displacement_mm'], result['gauge_multiplier_N']
    # The wrapper retains the last improving iterate on a stagnation stop,
    # rather than the last rejected candidate listed in history.
    np.savez_compressed(HERE / 'parent-iterate.npz', displacement_mm=u, gauge_multiplier_N=lam)
    ld = np.longdouble
    upper = K.astype(ld) @ u.astype(ld) + data['R'].astype(ld) @ lam.astype(ld) - data['projected'].astype(ld)
    saved = {k: v for k, v in result.items() if k not in ('displacement_mm', 'gauge_multiplier_N')}
    saved.update({
        'schema': 'parent_stopped_kicker_iterate/v1',
        'packet_sha256': sha(HERE / 'packet.json'),
        'producer_sha256': sha(Path(__file__)),
        'iterate_sha256': sha(HERE / 'parent-iterate.npz'),
        'saved_iterate_semantics': 'Last improving iterate, correction 3; correction 4 candidate rejected for stagnation',
        'saved_iterate_upper_force_residual_max_N': float(abs(upper).max()),
        'saved_iterate_gauge_displacement_max_mm': float(abs(data['R'].astype(ld).T @ u.astype(ld)).max()),
        'saved_iterate_gauge_multiplier_max_N': float(abs(lam).max()),
        'native_solve_run': False,
        'full_compliance_computed': False,
        'mechanical_acceptance': False,
        'numerical_gate_relaxed': False,
    })
    output.write_text(json.dumps(saved, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: saved[k] for k in ('status', 'corrections', 'saved_iterate_upper_force_residual_max_N', 'saved_iterate_gauge_multiplier_max_N')}))


if __name__ == '__main__':
    run()
