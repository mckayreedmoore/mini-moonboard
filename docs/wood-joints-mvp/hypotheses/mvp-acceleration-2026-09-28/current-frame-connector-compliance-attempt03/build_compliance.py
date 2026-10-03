"""Parent-owned reduction of authenticated body K to source connector rows."""
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def build():
    if (HERE / 'inputs.json').exists():
        raise ValueError('One-shot reduction already recorded; no automatic retry')
    assert os.environ.get('OPENBLAS_NUM_THREADS') == '1'
    resource.setrlimit(resource.RLIMIT_AS, (6 * 1024**3, 6 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (300, 300))
    import numpy as np
    import scipy
    import scipy.sparse as sp
    native = BASE / 'current-frame-pure-solid-matrix-export-native-attempt01'
    body_audit = BASE / 'current-frame-body-elastic-positivity-audit-attempt01'
    projection = BASE / 'current-frame-physical-connector-projection-contract-attempt01'
    method = BASE / 'current-frame-free-body-condensation-preflight-attempt01'
    refinement = BASE / 'current-bordered-refinement-diagnostic-attempt01'
    quotient_method = BASE / 'current-elastic-quotient-method-preflight-attempt01'
    parent_case = BASE / 'current-bordered-refinement-parent-case-attempt01'
    fixture = BASE / 'current-projected-connector-compliance-fixture-attempt01'
    load_packet = BASE / 'current-frame-pure-solid-matrix-export-preflight-attempt01'
    model_path = BASE / 'current-springa-frame-input-adapter-attempt01/a12-rear/model.json'
    parser_path = BASE / 'current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py'
    paths = [Path(__file__), model_path, parser_path,
             *[native / name for name in ['assess.py', 'freeze.json', 'execution.json', 'assessment.json', 'model.sti', 'model.dof']],
             *[body_audit / name for name in ['inputs.json', 'assessment.json', 'output-pin.json']],
             method / 'condensation.py', method / 'assessment.json',
             quotient_method / 'quotient_method.py', quotient_method / 'verify_quotient.py', quotient_method / 'assessment.json',
             refinement / 'bounded_refinement.py', refinement / 'verify_diagnostic.py', refinement / 'assessment.json',
             parent_case / 'test_refinement.py', parent_case / 'case.json', parent_case / 'refinement-result.json',
             fixture / 'verify_compliance.py', fixture / 'assessment.json',
             projection / 'projection-contract.json', projection / 'physical-index-map.json',
             load_packet / 'source-load-maps.json',
             BASE / 'current-physical-load-map-audit-attempt01/audit.json',
             BASE / 'current-six-case-operator-reuse-contract-attempt01/identity-contract.json']
    inputs = {'schema': 'parent_frame_connector_compliance_inputs/v1',
              'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in paths},
              'chunk_size': 16, 'rotation_coordinate_scale_mm': 1000.,
              'elastic_operator_interpretation': 'P K P on the rigid orthogonal complement; original K retained',
              'legacy_zero_multiplier_gate': 'Original failed records preserved; reported separately from new quotient method',
              'cpu_limit_seconds': 300, 'memory_limit_bytes': 6 * 1024**3,
              'scope': 'Elastic compliance and raw body wrench maps only; no frame/contact/load response',
              'native_launch': False, 'maximum_refinement_corrections_per_chunk': 5,
              'refinement_stop': 'Nonfinite, unchanged strict gate failure, stagnation or five-correction budget; no automatic retry'}
    write(HERE / 'inputs.json', inputs)
    for path in paths:
        if path.suffix == '.py':
            snapshot = HERE / 'sources' / path.relative_to(ROOT)
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_bytes(path.read_bytes())
    authenticated = module(native / 'assess.py', 'connector_authenticated_export')
    assert authenticated.assess() == json.loads((native / 'assessment.json').read_text())
    body_record = json.loads((body_audit / 'assessment.json').read_text())
    assert body_record['status'] == 'PASS_ALL_50_NATIVE_BODY_RIGID_LIFT_NUMERICAL_AUDITS'
    assert sha(body_audit / 'assessment.json') == json.loads((body_audit / 'output-pin.json').read_text())['assessment_sha256']
    for rel, expected in json.loads((body_audit / 'inputs.json').read_text())['source_sha256'].items():
        assert sha(ROOT / rel) == expected
    helper = module(method / 'condensation.py', 'connector_bordered_method')
    refined = module(refinement / 'bounded_refinement.py', 'connector_refinement_method')
    assert json.loads((parent_case / 'refinement-result.json').read_text())['status'] == 'PASS_BALANCED_FREE_BODY'
    quotient = module(quotient_method / 'quotient_method.py', 'connector_elastic_quotient_method')
    quotient_fixture = json.loads((quotient_method / 'assessment.json').read_text())
    assert quotient_fixture['status'] == 'PASS_ELASTIC_QUOTIENT_METHOD_KNOWN_ANSWER'
    for name in ['quotient_method.py', 'verify_quotient.py']:
        assert sha(quotient_method / name) == quotient_fixture['source_sha256'][name]
    parser = module(parser_path, 'connector_sparse_reader')
    source = parser.load_frame_source_model(model_path)
    labels = parser.parse_dof_file(native / 'model.dof')
    parser.require_dof_bijection(labels, source['physical_nodes'], 37647)
    owners = np.array([source['owner_by_node'][node] for node, _ in labels])
    row_for = {label: i for i, label in enumerate(labels)}
    parsed = parser.parse_upper_triangle_file(native / 'model.sti', len(labels),
                                             owner_by_row=owners, owner_names=list(source['bodies']))
    parser.require_no_cross_body_coupling(parsed)
    K = parsed['matrix']
    contract = json.loads((projection / 'projection-contract.json').read_text())
    index_map = json.loads((projection / 'physical-index-map.json').read_text())
    rows = contract['rows']
    assert len(rows) == 1840 and len(index_map) == 12549
    # Existing row_id text repeats for some distinct directional components;
    # source row position and source group/element preserve their identities.
    b_row, b_col, b_value = [], [], []
    for i, record in enumerate(rows):
        for term in record['physical_sparse_row']:
            coordinate = int(term['coordinate_index'])
            node = int(index_map[coordinate // 3]['node'])
            native_row = row_for[(node, coordinate % 3 + 1)]
            b_row.append(i); b_col.append(native_row); b_value.append(term['coefficient'])
    B = sp.csr_matrix((b_value, (b_row, b_col)), shape=(1840, len(labels)))
    assert B.nnz == 62607
    load_cases = json.loads((load_packet / 'source-load-maps.json').read_text())['cases']
    assert len(load_cases) == 6
    F = np.zeros((len(labels), 12))
    load_columns = []
    for case_index, case in enumerate(load_cases):
        for offset, kind in enumerate(['gravity_nodal_map', 'climber_nodal_map']):
            column = 2 * case_index + offset
            load_columns.append({'column': column, 'case_id': case['case_id'], 'kind': kind})
            for node, vector in case[kind].items():
                for direction, force in enumerate(vector, 1):
                    F[row_for[(int(node), direction)], column] = force
    H = np.zeros((1840, 1840))
    e = np.zeros((1840, 12))
    D = np.zeros((1840, 300))
    W = np.zeros((300, 12))
    body_names = list(source['bodies'])
    report = {'schema': 'parent_source_bound_frame_connector_compliance/v1',
              'status': 'RUNNING', 'input_record_sha256': sha(HERE / 'inputs.json'),
              'candidate': source['model']['candidate'], 'geometry_revision_id': source['model']['geometry_revision_id'],
              'dimensions': {'physical_dofs': 37647, 'connector_rows': 1840, 'rigid_coordinates': 300, 'separated_load_columns': 12},
              'runtime': {'numpy': np.__version__, 'scipy': scipy.__version__},
              'body_names_in_rigid_column_order': body_names, 'load_columns': load_columns,
              'bodies': [], 'original_K_modified': False, 'raw_wrenches_discarded': False,
              'physical_response_computed': False, 'contact_state_selected': False,
              'native_launch': False, 'mechanical_acceptance': False,
              'elastic_method': 'Audited original KKT solve interpreted on rigid orthogonal complement P K P; nonzero lambda recorded as exported-operator bookkeeping, never support',
              'physical_balance_contract': 'D.T*f=W; q=D*a+e-H*f. Raw body force/moment balance remains explicit.'}
    started = time.monotonic()
    try:
        for body_id in sorted(range(50), key=lambda i: len(source['bodies'][body_names[i]]), reverse=True):
            t = time.monotonic()
            body = body_names[body_id]
            dofs = np.flatnonzero(owners == body_id)
            _, R, Q = helper.rigid_basis([labels[int(j)] for j in dofs], source['coordinates'])
            Bb_all = B[:, dofs].tocsr()
            active_rows = np.flatnonzero(np.diff(Bb_all.indptr))
            Bb = Bb_all[active_rows, :].tocsr()
            Db = np.asarray(Bb @ R)
            D[np.ix_(active_rows, np.arange(6*body_id, 6*body_id+6))] = Db
            Fb = F[dofs, :]
            W[6*body_id:6*body_id+6, :] = R.T @ Fb
            body_K = K[dofs, :][:, dofs].tocsr()
            operator_audit = quotient.audit_quotient_operator(body_K, R)
            assert operator_audit['status'] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN
            factor, system = helper.factor_bordered(body_K, R)
            info = {'body': body, 'physical_dofs': len(dofs), 'active_source_rows': len(active_rows),
                    'max_kkt_relative_residual': 0., 'max_gauge_multiplier_N': 0.,
                    'total_refinement_corrections': 0, 'maximum_chunk_corrections': 0,
                    'operator_audit': operator_audit,
                    'legacy_zero_multiplier_failed_chunks': 0,
                    'max_original_Ku_minus_projected_load_N': 0.,
                    'max_original_residual_body_force_N': 0.,
                    'max_original_residual_body_moment_N_mm': 0.,
                    'raw_load_wrench_retained_in_W': True, 'raw_interface_wrench_retained_in_D': True}
            def elastic_solve(raw, description):
                projected = raw - Q @ (Q.T @ raw)
                solved = quotient.solve_quotient_chunk(factor, system, body_K, R, projected, operator_report=operator_audit)
                if solved['status'] != quotient.PASS_ELASTIC_QUOTIENT_SCREEN:
                    details = {k: v for k, v in solved.items() if k not in ['displacement_mm', 'gauge_multiplier_N']}
                    report['stopping_gate'] = {'body': body, 'basis': description, 'numerical_result': details}
                    raise RuntimeError('Projected basis numerical gate: ' + solved['status'])
                info['total_refinement_corrections'] += solved['corrections']
                info['maximum_chunk_corrections'] = max(info['maximum_chunk_corrections'], solved['corrections'])
                info['legacy_zero_multiplier_failed_chunks'] += solved['legacy_zero_lambda_gate']['status'] == 'FAIL'
                info['max_original_Ku_minus_projected_load_N'] = max(info['max_original_Ku_minus_projected_load_N'], solved['max_abs_original_Ku_minus_p_N'])
                for wrench in solved['original_Ku_minus_p_body_wrenches']:
                    info['max_original_residual_body_force_N'] = max(info['max_original_residual_body_force_N'], max(abs(v) for v in wrench['force_N']))
                    info['max_original_residual_body_moment_N_mm'] = max(info['max_original_residual_body_moment_N_mm'], max(abs(v) for v in wrench['moment_about_source_centroid_N_mm']))
                info['max_kkt_relative_residual'] = max(info['max_kkt_relative_residual'], solved['KKT_upper_force_residual_relative'])
                info['max_gauge_multiplier_N'] = max(info['max_gauge_multiplier_N'], solved['legacy_zero_lambda_gate']['max_abs_lambda_scaled_N'])
                return solved['displacement_mm']
            for first in range(0, len(active_rows), 16):
                selected = np.arange(first, min(first+16, len(active_rows)))
                raw = Bb[selected, :].T.toarray()
                displacement = elastic_solve(raw, f'interface columns {first}:{first+len(selected)}')
                H[np.ix_(active_rows, active_rows[selected])] += Bb @ displacement
            displacement = elastic_solve(Fb, '12 separate source gravity/climber columns')
            e[active_rows, :] += Bb @ displacement
            info['elapsed_seconds'] = time.monotonic()-t
            report['bodies'].append(info)
            write(HERE / 'partial.json', report)
            print(body, 'PASS_PROJECTED_ELASTIC_BASIS', flush=True)
        scale = max(float(np.linalg.norm(H, ord=np.inf)), np.finfo(float).tiny)
        reciprocity = float(np.linalg.norm(H-H.T, ord=np.inf)/scale)
        minimum_eigenvalue = float(np.linalg.eigvalsh(0.5*(H+H.T))[0])
        report['compliance_checks'] = {'reciprocity_relative_inf': reciprocity, 'reciprocity_tolerance': 1e-8,
                                       'min_symmetric_part_eigenvalue_mm_per_N': minimum_eigenvalue,
                                       'inf_scale_mm_per_N': scale, 'negative_eigenvalue_tolerance_mm_per_N': 1e-9*scale}
        assert reciprocity <= 1e-8 and minimum_eigenvalue >= -1e-9*scale
        np.savez_compressed(HERE / 'operators.npz', H=H, D=D, e=e, W=W)
        sp.save_npz(HERE / 'B.npz', B)
        write(HERE / 'row-identities.json', [{'row': i, 'row_id': r['row_id'], 'family': r['family'],
                                             'source_group': r.get('source_group'),
                                             'source_element': r.get('source_element'),
                                             'source_inventory_row_index': r.get('source_inventory_row_index'),
                                             'law': r['law'], 'ownership': r.get('ownership')} for i, r in enumerate(rows)])
        report['status'] = 'PASS_SOURCE_BOUND_FRAME_CONNECTOR_COMPLIANCE'
        report['outputs_sha256'] = {name: sha(HERE / name) for name in ['operators.npz', 'B.npz', 'row-identities.json']}
    except Exception as error:
        report['status'] = 'STOP_CONNECTOR_COMPLIANCE_NUMERICAL_GATE'
        report['exception'] = repr(error)
    finally:
        report['elapsed_seconds'] = time.monotonic()-started
        report['bodies_completed'] = len(report['bodies'])
        report['limits'] = ['Projected columns are elastic basis terms only; none is a physical body load response.',
                            'Raw D.T*f=W must hold before reconstructing a physical response.',
                            'No normal/tangent contact state, reference history, global frame response or joint strength is accepted.']
        for rel, expected in inputs['source_sha256'].items():
            if sha(ROOT / rel) != expected:
                report['status'] = 'STOP_SOURCE_CHANGED_DURING_REDUCTION'
        write(HERE / 'assessment.json', report)
        write(HERE / 'output-pin.json', {'assessment_sha256': sha(HERE / 'assessment.json')})
        print(report['status'], flush=True)


if __name__ == '__main__':
    if '--verify-record' in sys.argv:
        inputs = json.loads((HERE / 'inputs.json').read_text())
        for rel, expected in inputs['source_sha256'].items():
            assert sha(ROOT / rel) == expected
            if Path(rel).suffix == '.py':
                assert sha(HERE / 'sources' / rel) == expected
        report = json.loads((HERE / 'assessment.json').read_text())
        assert report['input_record_sha256'] == sha(HERE / 'inputs.json')
        assert json.loads((HERE / 'output-pin.json').read_text())['assessment_sha256'] == sha(HERE / 'assessment.json')
        for name, expected in report.get('outputs_sha256', {}).items():
            assert sha(HERE / name) == expected
        print('PASS_COMPLIANCE_RECORD_PROVENANCE', report['status'])
    else:
        lock = ROOT / 'docs/wood-joints-mvp/luna-max-native-run-ledger.lock'
        with lock.open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            assert json.loads(lock.with_suffix('.json').read_text())['slot']['state'] == 'idle'
            build()
