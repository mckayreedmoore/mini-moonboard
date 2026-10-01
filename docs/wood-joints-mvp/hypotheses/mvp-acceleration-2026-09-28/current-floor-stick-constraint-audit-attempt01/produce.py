"""Check native-MPC expressibility of an all-bearing floor hypothesis; no solve."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.linalg import qr

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json'
PIN = 'd3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0'


def produce():
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PIN
    model = json.loads(raw)
    equations = {}
    for terms in model['equations']:
        key = tuple(terms[0][:2])
        assert key not in equations and terms[0][2] != 0
        equations[key] = terms
    fixed = {(n, d) for n in model['fixed_nodes'] for d in [1, 2, 3]}
    assert not fixed.intersection(equations)
    cache, visiting = {}, set()

    def expand(key):
        if key in cache:
            return cache[key]
        if key in visiting:
            raise ValueError('Circular original projection equation')
        visiting.add(key)
        if key in fixed:
            answer = {}
        elif key not in equations:
            answer = {key: 1.}
        else:
            terms = equations[key]
            answer = {}
            for n, d, c in terms[1:]:
                for master, weight in expand((n, d)).items():
                    answer[master] = answer.get(master, 0.) - c * weight / terms[0][2]
            answer = {k: v for k, v in answer.items() if v != 0.}
        visiting.remove(key)
        cache[key] = answer
        return answer

    floor_rows = []
    names = []
    for spring in model['springs']:
        owner = model['connection_ownership'][spring['name']]
        if owner['role'] != 'assumed_no_slip_floor':
            continue
        first, second = spring['nodes']
        dof = spring['dof']
        weights = dict(expand((first, dof)))
        for key, value in expand((second, dof)).items():
            weights[key] = weights.get(key, 0.) - value
        floor_rows.append(weights)
        names.append({'normal_cell': spring['name'].removesuffix('_friction'), 'local_dof': dof})
    assert len(floor_rows) == 200
    masters = sorted(set().union(*(set(row) for row in floor_rows)))
    physical_nodes = set().union(*(set(tags) for tags in model['physical_body_nodes'].values()))
    assert all(n in physical_nodes and key not in fixed and key not in equations for key in masters for n in [key[0]])
    columns = {key: i for i, key in enumerate(masters)}
    A = np.zeros((200, len(masters)))
    for i, row in enumerate(floor_rows):
        for key, value in row.items():
            A[i, columns[key]] = value
    # Row/column pivoting only changes representation of homogeneous constraints.
    # It neither adds floor stiffness nor selects a response/contact branch.
    singular = np.linalg.svd(A, compute_uv=False)
    rank = int(np.count_nonzero(singular > singular[0] * 1e-10))
    _, _, row_order = qr(A.T, pivoting=True, mode='economic')
    selected = row_order[:rank]
    _, _, column_order = qr(A[selected], pivoting=True, mode='economic')
    pivots = column_order[:rank]
    H = np.linalg.solve(A[np.ix_(selected, pivots)], A[selected])
    residual = float(np.max(np.abs(A - A[:, pivots] @ H)))
    pivot_residual = float(np.max(np.abs(H[:, pivots] - np.eye(rank))))
    assert residual < 1e-10 and pivot_residual < 1e-10
    assert len({masters[i] for i in pivots}) == rank
    # Test actual frozen shape/projection rows on an arbitrary admissible field.
    free = sorted(set(range(len(masters))) - set(map(int, pivots)))
    motion = np.zeros(len(masters))
    motion[free] = np.sin(np.arange(len(free)) + 1.)
    motion[pivots] = -H[:, free] @ motion[free]
    motion_residual = float(np.max(np.abs(A @ motion)))
    assert motion_residual < 1e-10
    np.savez_compressed(HERE / 'constraint-matrices.npz', original=A, reduced=H,
                        pivots=pivots, selected_rows=selected, singular_values=singular)
    result = {'schema': 'current_floor_stick_constraint_audit/v1', 'source_input_sha256': PIN,
              'status': 'PASS_INPUT_CONSTRAINT_SPACE_AND_NATIVE_DEPENDENT_DOF_AUDIT',
              'floor_cells': 100, 'original_tangent_rows': 200, 'independent_constraint_rank': rank,
              'physical_master_dof_count': len(masters), 'physical_master_dofs': masters,
              'row_owners': names, 'pivot_physical_dofs': [masters[i] for i in pivots],
              'reconstruction_max_coefficient_residual': residual,
              'identity_pivot_max_coefficient_residual': pivot_residual,
              'admissible_field_max_original_constraint_residual': motion_residual,
              'native_documentation': {'manual': 'https://www.dhondt.de/ccx_2.23.pdf',
                                       'section': '7.56 EQUATION, pp504-505',
                                       'rule': 'A DOF may occur only once as an equation-dependent term or SPC.'},
              'native_solve_executed': False, 'floor_bearing_verified': False,
              'frame_ready_for_native_run': False, 'complete_joint_validated': False,
              'limits': ['No floor forces, case response, friction coefficient or floor qualification.',
                         'This expresses a conditional all-bearing exact-stick constraint space; every paired normal must bear in a compatible response before it is applicable.',
                         'No native deck is generated. Table/relative-MPC transfer and exact floor constraint reaction recovery still need scoped method evidence.',
                         'Rank is a floating-point algebra screen at relative singular threshold 1e-10, not a material stiffness or capacity result.']}
    (HERE / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print({k: result[k] for k in ['status', 'independent_constraint_rank', 'physical_master_dof_count',
                                'reconstruction_max_coefficient_residual', 'admissible_field_max_original_constraint_residual']})


if __name__ == '__main__':
    produce()
