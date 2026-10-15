"""Closed-form spectral and box controls, independent of engineering assets."""
from fractions import Fraction as F
from itertools import product
from types import SimpleNamespace

import pytest
from scipy.sparse import csr_matrix

from scripts import eoere_elastic_core_certificate as core
from scripts import eoere_normal_patch_polynomial_gap as model
from scripts import eoere_original_load_bounds as bounds
from scripts import eoere_recession_certificate as exact

G = [{0: 3, 1: 1}, {0: 1, 1: 3}]


@pytest.mark.parametrize('vector,answer', [([1, 0], F(3, 8)+F(1, 4**65)),
                                         ([1, -2], F(19, 8)+F(9, 4**65))])
def test_fixed_64_term_energy_matches_independent_two_eigenspace_answers(vector, answer):
    value, upper = model.polynomial_energy(G, vector, 1, 64, core)
    assert upper == 4 and value == answer


def test_both_spectral_endpoints_are_exact_and_interior_remainder_is_positive():
    matrix = [{0: 1}, {1: 2}, {2: 4}]
    value, upper = model.polynomial_energy(matrix, [1, 1, 1], 1, 64, core)
    assert upper == 4 and value == F(7, 4)+F(1, 2**129)
    assert model.polynomial_energy(matrix, [3, 0, 0], 1, 64, core)[0] == 9
    assert model.polynomial_energy(matrix, [0, 0, 3], 1, 64, core)[0] == F(9, 4)


def test_zero_residual_and_fixed_power_counts_bracket_the_known_inverse_energy():
    energies = [model.polynomial_energy(G, [1, -2], 1, p, core)[0] for p in (0, 1, 2, 16, 64)]
    assert energies[0] == 5 and energies == sorted(energies, reverse=True)
    assert all(F(19, 8) <= v <= 5 for v in energies)
    assert model.polynomial_energy(G, [0, 0], 1, 64, core)[0] == 0


def test_sign_and_rational_scaling_preserve_the_quadratic_form():
    energy = model.polynomial_energy(G, [1, -2], 1, 64, core)[0]
    for scale in (-F(7, 13), 0, F(10**20, 3)):
        assert model.polynomial_energy(G, [scale, -2*scale], 1, 64, core)[0] == scale**2*energy


def test_uncertainty_box_encloses_closed_form_inverse_energy_at_all_corners():
    vector, box = [F(1), F(-2)], [F(1, 100), F(1, 5)]
    energy = model.polynomial_energy(G, vector, 1, 64, core)[0]
    upper = model.box_energy(energy, box, 1, bounds)
    for signs in product((-1, 1), repeat=2):
        x, y = [v+s*e for v, s, e in zip(vector, signs, box, strict=True)]
        assert (3*x*x-2*x*y+3*y*y)/8 <= upper
    assert model.box_energy(0, [0, 0], 1, bounds) == 0
    assert model.box_energy(0, box, 1, bounds) >= sum(e*e for e in box)


@pytest.mark.parametrize('change', ['degree_boolean', 'degree_negative', 'degree_excess', 'short_vector',
    'missing_row', 'asymmetric', 'index_boolean', 'index_negative', 'index_excess', 'index_text',
    'zero_mu', 'negative_mu', 'excess_mu', 'zero_matrix'])
def test_invalid_polynomial_controls_are_refused(change):
    matrix, vector, mu, degree = [dict(r) for r in G], [1, -2], 1, 64
    if change == 'degree_boolean': degree = True
    if change == 'degree_negative': degree = -1
    if change == 'degree_excess': degree = 65
    if change == 'short_vector': vector.pop()
    if change == 'missing_row': matrix.pop()
    if change == 'asymmetric': matrix[0][1] = 2
    if change == 'index_boolean': matrix[0] = {False: 3, 1: 1}
    if change == 'index_negative': matrix[0][-1] = 1
    if change == 'index_excess': matrix[0][2] = 1
    if change == 'index_text': matrix[0]['0'] = 1
    if change == 'zero_mu': mu = 0
    if change == 'negative_mu': mu = -1
    if change == 'excess_mu': mu = 5
    if change == 'zero_matrix': matrix = [{}, {}]
    with pytest.raises(ValueError):
        model.polynomial_energy(matrix, vector, mu, degree, core)


@pytest.mark.parametrize('energy,box,mu', [(-1, [0, 0], 1), (0, [-1, 0], 1), (0, [], 1), (0, [0], 0)])
def test_invalid_box_bound_is_refused(energy, box, mu):
    with pytest.raises(ValueError):
        model.box_energy(energy, box, mu, bounds)


def certificate():
    return {'coordinates': 3, 'global_coordinates': [0, 1, 2], 'datum_local_coordinates': [0],
        'constructed_core_PSD_and_exact_registered_kernel_proven': True,
        'quotient_positive_certificate': {'exact_matrix_sha256': exact.matrix_digest(G), 'exact_smallest_eigenvalue_lower': '1'}}


def test_extraction_uses_own_free_coordinates_and_matches_the_certified_exact_digest():
    matrix = csr_matrix([[9., 0., 0.], [0., 3., 1.], [0., 1., 3.]])
    free, block, mu = model.certified_free_block(matrix, certificate(), core, exact)
    assert free == [1, 2] and block == G and mu == 1


@pytest.mark.parametrize('change', ['digest', 'matrix', 'asymmetry', 'false_proof', 'duplicate_coordinate',
    'coordinate_boolean', 'coordinate_excess', 'datum_excess', 'datum_duplicate', 'count', 'zero_mu'])
def test_incompatible_block_or_certificate_is_refused(change):
    cert = certificate(); matrix = csr_matrix([[9., 0., 0.], [0., 3., 1.], [0., 1., 3.]])
    if change == 'digest': cert['quotient_positive_certificate']['exact_matrix_sha256'] = '0'*64
    if change == 'matrix': matrix[1, 1] = 4.
    if change == 'asymmetry': matrix[1, 2] = 2.
    if change == 'false_proof': cert['constructed_core_PSD_and_exact_registered_kernel_proven'] = False
    if change == 'duplicate_coordinate': cert['global_coordinates'] = [0, 1, 1]
    if change == 'coordinate_boolean': cert['global_coordinates'] = [False, 1, 2]
    if change == 'coordinate_excess': cert['global_coordinates'] = [0, 1, 3]
    if change == 'datum_excess': cert['datum_local_coordinates'] = [3]
    if change == 'datum_duplicate': cert['datum_local_coordinates'] = [0, 0]
    if change == 'count': cert['coordinates'] = 4
    if change == 'zero_mu': cert['quotient_positive_certificate']['exact_smallest_eigenvalue_lower'] = '0'
    with pytest.raises(ValueError):
        model.certified_free_block(matrix, cert, core, exact)


def test_bootstrap_uses_captured_bytes_instead_of_a_poisoned_module_cache(monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, 'scripts.eoere_mixed_shaft_projection_limit', SimpleNamespace(bootstrap=None))
    assert callable(model.bootstrap({}).bootstrap)
    with pytest.raises(ValueError, match='bootstrap changed'):
        model.bootstrap({model.BOOT['path']: '0'*64})
