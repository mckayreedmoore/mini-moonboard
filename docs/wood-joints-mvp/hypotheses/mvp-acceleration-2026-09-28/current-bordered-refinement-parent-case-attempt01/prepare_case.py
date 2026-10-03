"""Prepare only the exact first rejected compliance chunk for diagnosis."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run():
    import numpy as np
    import scipy.sparse as sp
    failed = BASE / 'current-frame-connector-compliance-attempt01'
    record = json.loads((failed / 'assessment.json').read_text())
    assert record['status'] == 'STOP_CONNECTOR_COMPLIANCE_NUMERICAL_GATE'
    assert record['stopping_gate']['body'] == 'main_lower_left'
    assert record['stopping_gate']['basis'] == 'interface columns 16:32'
    for rel, expected in json.loads((failed / 'inputs.json').read_text())['source_sha256'].items():
        assert sha(ROOT / rel) == expected
    parser_path = BASE / 'current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py'
    helper_path = BASE / 'current-frame-free-body-condensation-preflight-attempt01/condensation.py'
    model_path = BASE / 'current-springa-frame-input-adapter-attempt01/a12-rear/model.json'
    native = BASE / 'current-frame-pure-solid-matrix-export-native-attempt01'
    projection = BASE / 'current-frame-physical-connector-projection-contract-attempt01'
    parser = mod(parser_path, 'refinement_sparse_parser')
    helper = mod(helper_path, 'refinement_fixed_body_helper')
    model = parser.load_frame_source_model(model_path)
    labels = parser.parse_dof_file(native / 'model.dof')
    row_for = {label: i for i, label in enumerate(labels)}
    owner = np.array([model['owner_by_node'][node] for node, _ in labels])
    body_id = list(model['bodies']).index('main_lower_left')
    dofs = np.flatnonzero(owner == body_id)
    K = parser.parse_upper_triangle_file(native / 'model.sti', len(labels))['matrix'][dofs, :][:, dofs]
    _, R, Q = helper.rigid_basis([labels[int(row)] for row in dofs], model['coordinates'])
    contract = json.loads((projection / 'projection-contract.json').read_text())
    index = json.loads((projection / 'physical-index-map.json').read_text())
    rr, cc, vv = [], [], []
    for i, row in enumerate(contract['rows']):
        for term in row['physical_sparse_row']:
            c = int(term['coordinate_index'])
            rr.append(i); cc.append(row_for[(int(index[c//3]['node']), c%3+1)]); vv.append(term['coefficient'])
    B = sp.csr_matrix((vv, (rr, cc)), shape=(1840, len(labels)))[:, dofs].tocsr()
    active = np.flatnonzero(np.diff(B.indptr))
    selected = active[16:32]
    raw = B[selected, :].T.toarray()
    balanced = raw - Q @ (Q.T @ raw)
    if (HERE / 'case.json').exists():
        raise ValueError('Refusing to replace the frozen diagnostic case')
    sp.save_npz(HERE / 'body-K.npz', K)
    np.savez_compressed(HERE / 'basis.npz', R=R, raw=raw, balanced=balanced)
    metadata = {'schema': 'parent_exact_failed_compliance_chunk/v1',
                'scope': 'Exact 16 rejected elastic-basis columns, not a physical response',
                'body': 'main_lower_left', 'physical_dofs': len(dofs),
                'source_row_positions': selected.tolist(),
                'source_group_names': [contract['rows'][int(row)].get('source_group') for row in selected],
                'raw_wrenches_preserved': True, 'physical_response_computed': False,
                'native_launch': False,
                'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__),
                    failed / 'inputs.json', failed / 'assessment.json',
                    parser_path, helper_path, model_path, native / 'model.sti', native / 'model.dof',
                    projection / 'projection-contract.json', projection / 'physical-index-map.json']},
                'outputs_sha256': {name: sha(HERE / name) for name in ['body-K.npz', 'basis.npz']}}
    (HERE / 'case.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')
    print('PREPARED_EXACT_REJECTED_BASIS_CHUNK', len(dofs), selected.tolist())


if __name__ == '__main__':
    run()
