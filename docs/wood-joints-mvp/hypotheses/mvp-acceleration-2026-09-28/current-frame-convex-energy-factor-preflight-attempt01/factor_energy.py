"""Parent-owned numerical factor preflight, no frame state or native solve."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import resource
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
    import scipy.linalg as la
    assert os.environ.get('OPENBLAS_NUM_THREADS') == '1'
    assert not (HERE/'inputs.json').exists(), 'One-shot preflight already recorded'
    resource.setrlimit(resource.RLIMIT_AS, (6*1024**3, 6*1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    source = BASE/'current-frame-connector-compliance-attempt04'
    paths = [Path(__file__), source/'operators.npz', source/'assessment.json', source/'output-pin.json']
    pins = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    write(HERE/'inputs.json', {'source_sha256': pins, 'scope': 'H symmetric-part energy factor only',
                              'original_H_modified': False, 'native_launch': False,
                              'condition_estimate_floor': 1e-12})
    started = time.monotonic()
    report = {'status': 'RUNNING', 'physical_state_solved': False, 'native_launch': False}
    try:
        a = json.loads((source/'assessment.json').read_text())
        assert a['status'] == 'PASS_SOURCE_BOUND_FRAME_CONNECTOR_COMPLIANCE'
        assert sha(source/'assessment.json') == json.loads((source/'output-pin.json').read_text())['assessment_sha256']
        assert sha(source/'operators.npz') == a['outputs_sha256']['operators.npz']
        with np.load(source/'operators.npz') as z:
            H = z['H']
        assert H.shape == (1840, 1840) and np.isfinite(H).all()
        S = (H+H.T)/2
        L = la.cholesky(S, lower=True, check_finite=True)
        norm = float(np.linalg.norm(S, ord=1))
        rcond, info = la.lapack.dpocon(L, norm, uplo='L')
        assert info == 0 and rcond >= 1e-12
        reconstruction = float(np.linalg.norm(S-L@L.T, ord=np.inf)/np.linalg.norm(S, ord=np.inf))
        assert reconstruction <= 1e-12
        energy_errors = []
        for mode in range(4):
            x = np.sin(np.arange(1840)*(.017+mode*.011)) + .1*mode
            direct = float(x@S@x)
            transformed = float(np.linalg.norm(L.T@x)**2)
            error = abs(direct-transformed)/max(1., abs(direct))
            assert error <= 1e-12
            energy_errors.append(error)
        np.savez_compressed(HERE/'energy-factor.npz', L=L)
        report.update({'status': 'PASS_NUMERICAL_SYMMETRIC_ENERGY_FACTOR',
                       'H_shape': [1840, 1840], 'rcond_estimate': float(rcond),
                       'relative_factor_reconstruction_inf': reconstruction,
                       'deterministic_energy_relative_errors': energy_errors,
                       'max_absolute_Hsym_minus_raw_H_mm_per_N': float(np.max(np.abs(S-H))),
                       'Hsym_minus_raw_H_induced_inf_mm_per_N': float(np.linalg.norm(S-H, ord=np.inf)),
                       'L_diagonal_min': float(np.min(np.diag(L))),
                       'energy_factor_sha256': sha(HERE/'energy-factor.npz')})
    except Exception as error:
        report.update({'status': 'STOP_ENERGY_FACTOR_NUMERICAL_GATE', 'exception': repr(error)})
    finally:
        report['elapsed_seconds'] = time.monotonic()-started
        report['input_record_sha256'] = sha(HERE/'inputs.json')
        report['limits'] = ['Hsym is an explicitly recorded numerical energy approximation, not a rewritten raw operator.',
                            'Any later state must pass raw-H compatibility, raw D/W equilibrium and source laws.',
                            'No mask, event, gravity settlement, load case or joint acceptance follows.']
        if any(sha(ROOT/rel) != expected for rel, expected in pins.items()):
            report['status'] = 'STOP_SOURCE_CHANGED_DURING_ENERGY_FACTOR'
        write(HERE/'assessment.json', report)
        write(HERE/'output-pin.json', {'assessment_sha256': sha(HERE/'assessment.json')})
        print(json.dumps(report, indent=2))

if __name__ == '__main__':
    lock = ROOT/'docs/wood-joints-mvp/luna-max-native-run-ledger.lock'
    with lock.open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert json.loads(lock.with_suffix('.json').read_text())['slot']['state'] == 'idle'
        run()
