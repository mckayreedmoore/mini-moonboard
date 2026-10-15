"""Known energies and adversarial arithmetic for local core certificates."""
from fractions import Fraction as F

import numpy as np
import pytest

from scripts import eoere_elastic_core_certificate as method


def rows(values):
    return [{j: F(value) for j, value in enumerate(row) if value} for row in values]


def test_shifted_gram_certificate_has_an_exact_positive_lower_bound():
    matrix = rows([[3, 1], [1, 3]])
    proof = method.shifted_cholesky(matrix, shift=1, factor=np.linalg.cholesky([[2., 1.], [1., 2.]]))
    assert proof['positive_definite_proven']
    assert F(proof['exact_smallest_eigenvalue_lower']) == 1-F(proof['exact_factor_residual_inf'])
    assert .999999999999 < proof['smallest_eigenvalue_lower'] <= 1


def test_factorization_success_is_not_itself_the_verification():
    with pytest.raises(ValueError, match='residual does not prove'):
        method.shifted_cholesky(rows([[1, 0], [0, 1]]), shift=1, factor=np.eye(2))


@pytest.mark.parametrize('matrix', [[[0]], [[-1]], [[1, 2], [2, 1]]])
def test_no_positive_selected_shift_is_not_reported_as_a_certificate(matrix):
    with pytest.raises(ValueError, match='no positive shift'):
        method.shifted_cholesky(rows(matrix))


@pytest.mark.parametrize('matrix,shift,factor,match', [
    ([[2, 1], [0, 2]], 1, np.eye(2), 'symmetric'),
    ([[2]], 0, np.ones((1, 1)), 'positive verification shift'),
    ([[2]], 1, np.ones((2, 2)), 'square witness factor'),
    ([[2]], 1, [[np.nan]], 'square witness factor'),
])
def test_invalid_shift_witnesses_refuse(matrix, shift, factor, match):
    with pytest.raises(ValueError, match=match):
        method.shifted_cholesky(rows(matrix), shift=shift, factor=factor)


def test_tiny_exact_residual_is_retained_instead_of_snapped():
    tiny = F(1, 2**1074)
    proof = method.shifted_cholesky(rows([[2+tiny, 0], [0, 2]]), shift=1, factor=np.eye(2))
    assert F(proof['exact_factor_residual_inf']) == tiny
    assert F(proof['exact_smallest_eigenvalue_lower']) == 1-tiny


def test_cholesky_selection_handles_a_non_diagonal_known_energy():
    proof = method.shifted_cholesky(rows([[3, -1], [-1, 2]]))
    assert 0 < proof['smallest_eigenvalue_lower'] < (5-5**.5)/2


def test_exact_datum_inverse_pivots_and_rejects_singular_maps():
    source = rows([[0, 2], [3, 1]])
    assert method.product(source, method.exact_inverse(source)) == rows([[1, 0], [0, 1]])
    with pytest.raises(ValueError, match='singular'):
        method.exact_inverse(rows([[1, 2], [2, 4]]))


def test_symmetrization_preserves_energy_and_records_every_skew_term():
    tiny = F(1, 2**1000)
    matrix = rows([[2, tiny], [0, 3]])
    symmetric, skew = method.symmetrize(matrix)
    assert symmetric == rows([[2, tiny/2], [tiny/2, 3]])
    assert skew == rows([[0, tiny/2], [-tiny/2, 0]])
    q = [F(2), F(3)]
    assert sum(v*w for v, w in zip(q, method.action(skew, q), strict=True)) == 0
    assert method.norm_inf(skew) == tiny/2


def test_connected_three_station_spring_body_has_only_its_rigid_translation():
    matrix = rows([[1, -1, 0], [-1, 2, -1], [0, -1, 1]])
    rigid = rows([[1], [1], [1]])
    record, delta, skew = method.certify_core(matrix, rigid, datum=[0])
    assert record['literal_saved_energy_matrix_core_hypothesis_proven']
    assert record['free_coordinate_count'] == 2
    assert record['constructed_core_PSD_and_exact_registered_kernel_proven']
    assert record['nonzero_KR_entry_count'] == 0
    assert record['negative_rigid_quadratic_witness'] is None
    assert method.norm_inf(delta) == method.norm_inf(skew) == 0


def test_small_negative_rigid_work_is_not_hidden_by_a_positive_quotient():
    tiny = F(1, 2**60)
    matrix = rows([[1-tiny, -1, 0], [-1, 2, -1], [0, -1, 1]])
    record, delta, _ = method.certify_core(matrix, rows([[1], [1], [1]]), datum=[0])
    assert record['quotient_positive_certificate']['positive_definite_proven']
    assert not record['literal_saved_energy_matrix_core_hypothesis_proven']
    assert not record['source_symmetric_matrix_annihilates_registered_rigid_basis']
    assert record['negative_rigid_quadratic_witness']['source_energy_matrix_not_PSD_proven']
    assert F(record['negative_rigid_quadratic_witness']['exact_quadratic_work']) < 0
    assert method.norm_inf(delta) == tiny
    assert record['constructed_core_PSD_and_exact_registered_kernel_proven']


def test_sparse_completion_difference_matches_an_independent_dense_construction():
    rigid = rows([[1, 0], [0, 1], [1, 2], [-1, 1]])
    matrix = rows([[7, 2, 1, -3], [2, 8, -1, 2], [1, -1, 6, 1], [-3, 2, 1, 9]])
    datum = [2, 0]
    record, delta, _ = method.certify_core(matrix, rigid, datum=datum)
    free = [1, 3]
    r = np.asarray([[F(value) for value in row] for row in [[1, 0], [0, 1], [1, 2], [-1, 1]]], dtype=object)
    inv = np.asarray([[F(0), F(1)], [F(1, 2), F(-1, 2)]], dtype=object)
    s = r @ inv
    t = np.zeros((2, 4), dtype=object)
    for i, f in enumerate(free):
        t[i, f] = F(1)
        for j, d in enumerate(datum):
            t[i, d] = -s[f, j]
    k = np.asarray([[row.get(j, F(0)) for j in range(4)] for row in matrix], dtype=object)
    expected = k-t.T @ k[np.ix_(free, free)] @ t
    assert delta == rows(expected)
    assert record['exact_comparator_difference_inf'] == str(max(sum(abs(v) for v in row) for row in expected))
    assert method.product([{j: k[i, j]-delta[i].get(j, 0) for j in range(4)} for i in range(4)], rigid) == [{}, {}, {}, {}]


@pytest.mark.parametrize('datum', [[0, 0], [0], [0, 3], [0, 1.]])
def test_invalid_datum_coordinates_refuse(datum):
    with pytest.raises(ValueError, match='datum row selection'):
        method.certify_core(rows([[2, -1, 0], [-1, 2, -1], [0, -1, 2]]), rows([[1, 0], [0, 1], [1, 1]]), datum=datum)


def test_exact_singular_rigid_map_cannot_be_promoted_by_qr_selection():
    with pytest.raises(ValueError, match='singular'):
        method.certify_core(rows([[2, 0, 0], [0, 2, 0], [0, 0, 2]]), rows([[1, 2], [2, 4], [3, 6]]))


def test_a_nonpositive_free_mode_does_not_get_a_normalized_positive_core():
    with pytest.raises(ValueError, match='no positive shift'):
        method.certify_core(rows([[0, 0, 0], [0, 1, 0], [0, 0, -1]]), rows([[1], [0], [0]]), datum=[0])
