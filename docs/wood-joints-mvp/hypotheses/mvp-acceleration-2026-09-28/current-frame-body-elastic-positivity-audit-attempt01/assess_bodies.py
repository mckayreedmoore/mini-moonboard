"""Parent-owned, sequential numerical audit of the 50 exported body operators."""
from pathlib import Path
import fcntl
import hashlib
import importlib.util
import json
import os
import resource
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
sys.path.insert(0, str(ROOT))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def run():
    if (HERE / 'assessment.json').exists() or (HERE / 'inputs.json').exists():
        raise ValueError('This one-shot audit already has a record; no automatic retry')
    assert os.environ.get('OPENBLAS_NUM_THREADS') == '1'
    resource.setrlimit(resource.RLIMIT_AS, (6 * 1024**3, 6 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    import numpy as np
    import scipy
    native = BASE / 'current-frame-pure-solid-matrix-export-native-attempt01'
    helper_path = BASE / 'current-frame-free-body-condensation-preflight-attempt01/condensation.py'
    parser_path = BASE / 'current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py'
    model_path = BASE / 'current-springa-frame-input-adapter-attempt01/a12-rear/model.json'
    files = [native / name for name in ['model.sti', 'model.dof', 'freeze.json', 'execution.json', 'assessment.json', 'assess.py']]
    preflight = helper_path.parent
    files += [helper_path, preflight / 'verify_preflight.py', preflight / 'assessment.json',
              parser_path, model_path, Path(__file__)]
    inputs = {'schema': 'parent_body_operator_audit_inputs/v1',
              'scope': '50 isolated source-solid operators: numerical rigid-lift positivity and conditioning only',
              'source_sha256': {str(p.relative_to(ROOT)): digest(p) for p in files},
              'rcond_floor': 1e-12,
              'rotation_coordinate_scale_mm': 1000.,
              'memory_limit_bytes': 6 * 1024**3, 'cpu_limit_seconds': 180,
              'native_launch': False, 'frame_response': False}
    write_json(HERE / 'inputs.json', inputs)
    for path in files:
        if path.suffix == '.py':
            snapshot = HERE / 'sources' / path.relative_to(ROOT)
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_bytes(path.read_bytes())
    assessor = load_module(native / 'assess.py', 'parent_authenticated_frame_operator')
    assert assessor.assess() == json.loads((native / 'assessment.json').read_text())
    helper = load_module(helper_path, 'parent_body_condensation_method')
    parser = load_module(parser_path, 'parent_body_sparse_reader')
    source = parser.load_frame_source_model(model_path)
    labels = parser.parse_dof_file(native / 'model.dof')
    parser.require_dof_bijection(labels, source['physical_nodes'], 37647)
    owner = np.array([source['owner_by_node'][node] for node, _ in labels])
    parsed = parser.parse_upper_triangle_file(native / 'model.sti', len(labels),
                                             owner_by_row=owner, owner_names=list(source['bodies']))
    parser.require_no_cross_body_coupling(parsed)
    matrix = parsed['matrix']
    bodies = list(source['bodies'])
    # Test the largest blocks first, then release each dense audit allocation.
    order = sorted(range(len(bodies)), key=lambda i: len(source['bodies'][bodies[i]]), reverse=True)
    report = {'schema': 'parent_native_body_elastic_positivity_audit/v1',
              'status': 'RUNNING', 'candidate': source['model']['candidate'],
              'geometry_revision_id': source['model']['geometry_revision_id'],
              'input_record_sha256': digest(HERE / 'inputs.json'),
              'runtime': {'numpy': np.__version__, 'scipy': scipy.__version__},
              'body_count_expected': 50, 'bodies': [],
              'original_physical_stiffness_modified': False,
              'native_launch': False, 'frame_response': False,
              'support_or_contact_state_selected': False,
              'mechanical_acceptance': False}
    started = time.monotonic()
    try:
        for body_id in order:
            body_started = time.monotonic()
            body = bodies[body_id]
            rows = np.flatnonzero(owner == body_id)
            local_labels = [labels[int(row)] for row in rows]
            _, rigid, _ = helper.rigid_basis(local_labels, source['coordinates'], rotation_scale_mm=1000.)
            block = matrix[rows, :][:, rows].tocsr()
            result = helper.audit_rigid_lift(block, rigid, rcond_floor=1e-12)
            result.update(body=body, physical_dofs=len(rows),
                          elapsed_seconds=time.monotonic()-body_started)
            report['bodies'].append(result)
            write_json(HERE / 'partial.json', report)
            print(body, result['status'], flush=True)
            if result['status'] != helper.PASS_RIGID_LIFT_SPD:
                report['status'] = 'STOP_BODY_OPERATOR_NUMERICAL_AUDIT'
                break
        else:
            report['status'] = 'PASS_ALL_50_NATIVE_BODY_RIGID_LIFT_NUMERICAL_AUDITS'
    except Exception as error:
        report['status'] = 'STOP_AUDIT_EXCEPTION'
        report['exception'] = repr(error)
        raise
    finally:
        report['elapsed_seconds'] = time.monotonic()-started
        report['body_count_assessed'] = len(report['bodies'])
        report['limits'] = ['Rigid lift is an audit device, not a physical support or modified body operator.',
                            'Cholesky and reciprocal-condition estimates are numerical evidence under the declared tolerances, not exact symbolic rank proofs.',
                            'No connector compliance, load response, contact state, strength or joint acceptance is computed.']
        for rel, expected in inputs['source_sha256'].items():
            if digest(ROOT / rel) != expected:
                report['status'] = 'STOP_SOURCE_CHANGED_DURING_AUDIT'
        write_json(HERE / 'assessment.json', report)
        write_json(HERE / 'output-pin.json', {'assessment_sha256': digest(HERE / 'assessment.json')})


if __name__ == '__main__':
    if '--verify-record' in sys.argv:
        inputs = json.loads((HERE / 'inputs.json').read_text())
        for rel, expected in inputs['source_sha256'].items():
            assert digest(ROOT / rel) == expected
            if Path(rel).suffix == '.py':
                assert digest(HERE / 'sources' / rel) == expected
        report = json.loads((HERE / 'assessment.json').read_text())
        assert report['input_record_sha256'] == digest(HERE / 'inputs.json')
        assert json.loads((HERE / 'output-pin.json').read_text())['assessment_sha256'] == digest(HERE / 'assessment.json')
        print('PASS_BODY_AUDIT_RECORD_PROVENANCE', report['status'])
    else:
        # Share the native run lock; no heavy native execution can overlap.
        lock = ROOT / 'docs/wood-joints-mvp/luna-max-native-run-ledger.lock'
        with lock.open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            ledger = json.loads(lock.with_suffix('.json').read_text())
            assert ledger['slot']['state'] == 'idle'
            run()
