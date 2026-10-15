"""Original-load and directional-domain controls without recovered fields."""
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts import eoere_recession_audit as a


def maps():
    return [{0: F(1)}, {1: F(1)}, {0: F(1, 3), 1: F(-1, 7)}]


def test_original_load_projection_keeps_exact_binary_work_and_tiny_terms():
    load = np.asarray([.1, -2., 1e-80])
    actual = a.original_load(load, maps())
    assert actual == [F.from_float(.1)+F.from_float(1e-80)/3, -2-F.from_float(1e-80)/7]
    for rigid in ((F(1), F(2)), (F(-2, 3), F(5, 7))):
        q = [sum(coefficient*rigid[j] for j, coefficient in row.items()) for row in maps()]
        direct = sum(F.from_float(float(f))*v for f, v in zip(load, q, strict=True))
        assert direct == sum(p*r for p, r in zip(actual, rigid, strict=True))


def test_port_projection_retains_signed_same_owner_body_work_and_rejects_foreign_rows():
    matrix = csr_matrix([[.3, -.5, 1e-50]])
    projected = a.compose_row(matrix, 0, maps(), ['one', 'two', 'two'], {'first': 'one', 'second': 'two'})
    assert projected == {0: F.from_float(.3)+F.from_float(1e-50)/3,
                         1: -F.from_float(.5)-F.from_float(1e-50)/7}
    with pytest.raises(ValueError, match='foreign'):
        a.compose_row(matrix, 0, maps(), ['one', 'two', 'other'], {'first': 'one', 'second': 'two'})


def test_registered_basis_digest_detects_tiny_changes_even_with_unchanged_column_labels():
    original = maps()
    changed = [dict(row) for row in original]
    changed[0][0] += F(1, 10**80)
    assert [list(row) for row in original] == [list(row) for row in changed]
    assert a.method.matrix_digest(original) != a.method.matrix_digest(changed)


def test_captured_normal_is_one_sided_and_lateral_rows_are_bilateral_with_only_enabled_XY():
    descriptor = {'first': 'one', 'second': 'two'}
    group = {**descriptor, 'B': csr_matrix([[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]),
             'id': 'panel', 'ka': 2., 'kl': 3., 'clearance': .4, 'tension_only': True}
    contact = {**descriptor, 'B': csr_matrix([[-1., 0., 0.]]), 'id': 'contact', 'stiffness': 5.}
    tangents = [{**descriptor, 'B': csr_matrix([[0., 1., 0.]]), 'id': identity, 'stiffness': 6.}
                for identity in ('enabled', 'disabled')]
    rows, bilateral, ids = a.constraints({'groups': [group], 'contacts': [contact], 'tangents': tangents},
                                         maps(), ['one', 'two', 'two'], {'enabled'})
    assert bilateral == 3 and len(ids) == 5 and 'disabled' not in ids
    assert ids[-2:] == ['panel/axial', 'contact']
    assert rows[0][3] == 1 and rows[0][4] == -1


def test_rigid_basis_preserves_every_owner_and_drops_only_declared_shaft_spin():
    modes = np.eye(6)
    modes[3:, 3:] *= 1000
    chart = {'final_ndof': 6, 'rotation_scale': 1000., 'timber': {}, 'four_port_fittings': {}, 'panels': {},
             'shafts': {'shaft': {'index': [[0, 1, 2, -1, 3, 4], [5, -1, -1, -1, -1, -1]],
                                   'basis': [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]}}}
    rows, owners, body, count = a.rigid_basis(chart, modes)
    assert count == 5 and set(owners) == {'shaft'}
    assert body[0]['source_mode_columns'] == [0, 1, 2, 4, 5]
    assert rows[4] == {3: F(1)} and rows[5] == {4: F(1)}
    chart['timber'] = {'overlap': {'index': [[0, 1, 2, 3, 4, 5]]}}
    with pytest.raises(ValueError, match='duplicate'):
        a.rigid_basis(chart, modes)


@pytest.mark.parametrize('bad', [float('inf'), float('nan')])
def test_nonfinite_original_load_cannot_enter_a_certificate(bad):
    with pytest.raises(ValueError, match='original stored load'):
        a.original_load(np.asarray([bad, 0., 0.]), maps())
