"""Parent-only bounded refinement of the exact rejected elastic-basis chunk."""
from pathlib import Path
import fcntl
import hashlib
import importlib.util
import json
import resource
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def run():
    import numpy as np
    import scipy.sparse as sp
    case = json.loads((HERE / 'case.json').read_text())
    for rel, expected in case['source_sha256'].items():
        assert sha(ROOT / rel) == expected
    for name, expected in case['outputs_sha256'].items():
        assert sha(HERE / name) == expected
    helper_path = HERE.parent / 'current-frame-free-body-condensation-preflight-attempt01/condensation.py'
    wrapper_path = HERE.parent / 'current-bordered-refinement-diagnostic-attempt01/bounded_refinement.py'
    assert sha(wrapper_path) == 'ee23cf09dc89b6a4c6581ea86379e0749c2c6559478da1e2f95a8a0b8b599c4e'
    helper = module('parent_chunk_helper', helper_path)
    wrapper = module('parent_chunk_refinement', wrapper_path)
    output = HERE / 'refinement-result.json'
    if '--verify' not in sys.argv:
        assert not output.exists(), 'Preserve the first diagnostic result'
    ledger = ROOT / 'docs/wood-joints-mvp/luna-max-native-run-ledger.json'
    resource.setrlimit(resource.RLIMIT_AS, (6 * 1024**3, 6 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    with Path(str(ledger) + '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        K = sp.load_npz(HERE / 'body-K.npz')
        data = np.load(HERE / 'basis.npz')
        factor, A = helper.factor_bordered(K, data['R'])
        result = wrapper.solve_bordered_chunk_refined(factor, A, data['R'], data['balanced'])
    saved = {k: v for k, v in result.items() if k not in ('displacement_mm', 'gauge_multiplier_N')}
    saved.update({
        'schema': 'parent_exact_rejected_chunk_refinement/v1',
        'producer_sha256': sha(Path(__file__)),
        'case_sha256': sha(HERE / 'case.json'),
        'helper_sha256': sha(helper_path),
        'wrapper_sha256': sha(wrapper_path),
        'physical_response_computed': False,
        'full_connector_compliance_computed': False,
        'native_solve_run': False,
        'numerical_gate_relaxed': False,
        'geometry_changed': False,
        'maximum_corrections': 5,
    })
    if '--verify' in sys.argv:
        assert saved == json.loads(output.read_text())
    else:
        output.write_text(json.dumps(saved, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: saved[k] for k in ('status', 'corrections', 'history')}))


if __name__ == '__main__':
    run()
