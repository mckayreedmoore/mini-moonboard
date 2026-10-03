"""Measure the rejected chunk's arithmetic residual; accept no basis/forces."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    import numpy as np
    import scipy.sparse as sp
    case = json.loads((HERE / 'case.json').read_text())
    root = HERE.parents[4]
    for rel, expected in case['source_sha256'].items():
        assert sha(root / rel) == expected
    for name, expected in case['outputs_sha256'].items():
        assert sha(HERE / name) == expected
    helper_path = HERE.parent / 'current-frame-free-body-condensation-preflight-attempt01/condensation.py'
    spec = importlib.util.spec_from_file_location('rejected_chunk_helper', helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    K = sp.load_npz(HERE / 'body-K.npz')
    data = np.load(HERE / 'basis.npz')
    factor, A = helper.factor_bordered(K, data['R'])
    rhs = np.vstack((data['balanced'], np.zeros((6,16))))
    x = factor.solve(rhs)
    residual64 = A @ x - rhs
    residual_extended = A.astype(np.longdouble) @ x.astype(np.longdouble) - rhs.astype(np.longdouble)
    denominator = abs(A).astype(np.longdouble) @ abs(x).astype(np.longdouble) + abs(rhs).astype(np.longdouble)
    ratio = np.divide(abs(residual_extended), denominator, out=np.zeros_like(denominator), where=denominator != 0.)
    result = {'schema': 'rejected_chunk_arithmetic_residual_diagnostic/v1',
              'case_sha256': sha(HERE / 'case.json'),
              'source_sha256': sha(Path(__file__)),
              'max_abs_residual_float64': float(abs(residual64).max()),
              'max_abs_residual_extended': float(abs(residual_extended).max()),
              'max_abs_difference_due_to_residual_evaluation': float(abs(residual64.astype(np.longdouble)-residual_extended).max()),
              'max_componentwise_backward_error_extended': float(ratio.max()),
              'float64_epsilon': float(np.finfo(np.float64).eps),
              'extended_epsilon': float(np.finfo(np.longdouble).eps),
              'force_rhs_scale': max(1., float(abs(rhs).max())),
              'physical_response_computed': False,
              'basis_accepted': False,
              'numerical_gate_relaxed': False}
    if '--verify' in sys.argv:
        assert result == json.loads((HERE / 'residual-inspection.json').read_text())
    else:
        (HERE / 'residual-inspection.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    run()
