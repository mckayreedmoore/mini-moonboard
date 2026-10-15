"""Closed-form equilibria and exact-domain controls for original-load bounds."""
from fractions import Fraction as F
from itertools import product

import numpy as np
import pytest

from scripts import eoere_original_load_bounds as bounds


def rows(values):
    return [{j: F(value) for j, value in enumerate(row) if value} for row in values]


@pytest.mark.parametrize('square', [F(0), F(4), F(2), F(1, 2**2000), F(10000001, 7)])
def test_root_enclosure_retains_every_exact_nonnegative_square(square):
    lo, hi = bounds.root_bounds(square)
    assert lo >= 0 and lo*lo <= square <= hi*hi and hi-lo <= F(1, 10**24)


@pytest.mark.parametrize('value', [F(0), F(1, 3), F(4), F(1, 2**2000), F(10**50, 31)])
def test_upper_rounding_never_discards_a_tiny_positive_term(value):
    result = bounds.upper(value)
    assert value <= result < value+F(1, 10**24)


@pytest.mark.parametrize('alpha,beta', [(1, 1), (F(1, 2), 2), (F(1, 10), 10)])
def test_parallel_spring_exact_load_equilibria_obey_the_new_dual_gap(alpha, beta):
    reference_k = [F(2), F(3)]
    q, candidate = F(2), [F(401, 100), F(599, 100)]
    assert sum(candidate) == 10
    for c1, c2 in product([alpha, 1, beta], repeat=2):
        stiffness = [reference_k[0]*c1, reference_k[1]*c2]
        equilibrium = [10*k/sum(stiffness) for k in stiffness]
        gap = sum(bounds.spring_gap([q], [x], [0], k, alpha, beta) for x, k in zip(candidate, reference_k, strict=True))
        actual = sum((r-x)**2/(2*k) for r, x, k in zip(equilibrium, candidate, stiffness, strict=True))
        assert actual <= gap
        for j in range(2):
            interval = bounds.functional([{j: F(1)}], candidate, [0, 0], [beta*k for k in reference_k], gap)
            lower = F(interval['exact_scalar_lower'])
            upper = F(interval['exact_norm_upper'])
            assert lower <= equilibrium[j] <= upper


def test_fixed_core_correction_gap_is_exact_without_a_response_or_residual_drop():
    assert bounds.elastic_gap(F(100), F(0), 1, 1) == 0
    assert bounds.elastic_gap(F(100), F(7, 1000), 1, 1) == F(7, 2000)


def test_noncommuting_elastic_family_and_nonzero_dual_residual_obey_the_core_bound():
    core = np.array([[4., 1.], [1., 2.]])
    eigen, basis = np.linalg.eigh(core)
    root = (basis*np.sqrt(eigen))@basis.T
    turn = np.array([[.6, -.8], [.8, .6]])
    q, error = np.array([2., -3.]), np.array([.12, -.23])
    for alpha, beta in [(.5, 2.), (.1, 10.), (1., 1.)]:
        trial = root@turn@np.diag([alpha, beta])@turn.T@root
        stress = core@q+error
        actual = .5*(q@trial@q+stress@np.linalg.solve(trial, stress))-q@stress
        upper = bounds.elastic_gap(q@core@q, error@np.linalg.solve(core, error), alpha, beta)
        assert actual <= float(upper)+1e-11


def test_radial_gap_retains_clearance_work_and_exact_conjugacy():
    assert bounds.spring_gap([3, 4], [F(24, 5), F(32, 5)], [0, 0], 2, 1, 1, clearance=1) == 0
    # Both zero and an opened radius are legitimate primal states.
    assert bounds.spring_gap([F(1, 5), F(1, 10)], [0, 0], [0, 0], 2, 1, 1, clearance=1) == 0
    upper = bounds.spring_gap([3, 4], [F(24, 5), F(32, 5)], [F(1, 10), F(1, 5)], 2, F(1, 2), 2, clearance=1)
    for e1, e2, multiplier in product([-.1, .1], [-.2, .2], [.5, 2.]):
        r = np.array([4.8+e1, 6.4+e2])
        k = 2*multiplier
        actual = k*16/2+float(r@r)/(2*k)+np.linalg.norm(r)-float(r@np.array([3., 4.]))
        assert actual <= float(upper)+1e-12


def test_positive_contacts_keep_opening_work_and_dual_cone():
    assert bounds.spring_gap([-2], [F(1, 10)], [0], 3, 1, 1, positive=True) == F(121, 600)
    with pytest.raises(ValueError, match='one-sided conjugate'):
        bounds.spring_gap([1], [F(1, 10)], [F(1, 5)], 3, 1, 1, positive=True)


@pytest.mark.parametrize('alpha,beta', [(0, 2), (-1, 2), (2, 3), (F(1, 2), F(3, 4))])
def test_invalid_stiffness_families_refuse(alpha, beta):
    with pytest.raises(ValueError, match='stiffness interval'):
        bounds.family(alpha, beta)


@pytest.mark.parametrize('square,digits', [(F(-1), 24), (F(1), 0), (F(1), 41)])
def test_invalid_root_requests_refuse(square, digits):
    with pytest.raises(ValueError, match='nonnegative square'):
        bounds.root_bounds(square, digits)


def test_weighted_gram_controls_nonorthogonal_vector_functionals_and_the_dual_box():
    matrix = rows([[1, 1], [1, -2]])
    candidate, radius, stiffness, gap = [1, -2], [F(1, 100), F(1, 50)], [2, 3], F(1, 5)
    result = bounds.functional(matrix, candidate, radius, stiffness, gap)
    assert F(result['exact_weighted_Gram_spectral_upper']) == 18
    for angle in np.linspace(0, 2*np.pi, 33):
        equilibrium_error = np.sqrt(2*float(gap))*np.sqrt(stiffness)*[np.cos(angle), np.sin(angle)]
        for signs in product([-1, 1], repeat=2):
            actual = np.array(candidate)+equilibrium_error+np.array(signs)*list(map(float, radius))
            value = np.array([[1, 1], [1, -2]])@actual
            assert np.linalg.norm(value) <= result['norm_upper']+1e-12


def test_auxiliary_lp_and_exact_minor_balance_at_a_known_original_load():
    matrix = rows([[1, 1, -1], [0, 1, 1]])
    selected = [0, 1]
    proof = bounds.exact.inverse_bound(bounds.exact.minor(matrix, selected))
    result = bounds.nearby_witness(matrix, 3, 1, [0, 2], [-1, 1, 1], [1, 1, 1], selected, proof)
    assert result['load_certificate']['exact_balanced_strict_dual_exists']
    assert F(result['load_certificate']['exact_strict_weight_margin_lower']) > 0
    assert result['component_correction_radius'][2] == 0


def test_inactive_contact_weights_gain_only_the_declared_static_selection_margin():
    matrix = rows([[1, -1]])
    proof = bounds.exact.inverse_bound(bounds.exact.minor(matrix, [0]))
    result = bounds.nearby_witness(matrix, 2, 0, [0], [0, 0], [2, 3], [0], proof)
    assert result['candidate_auxiliary_weights'] == pytest.approx([1e-5, 1e-5])
    assert result['load_certificate']['exact_balanced_strict_dual_exists']


def test_a_rank_certificate_from_a_different_matrix_cannot_admit_an_lp_witness():
    proof = bounds.exact.inverse_bound(rows([[2]]))
    with pytest.raises(ValueError, match='another matrix'):
        bounds.nearby_witness(rows([[1, -1]]), 2, 0, [0], [0, 0], [1, 1], [0], proof)


@pytest.mark.parametrize('displacement,candidate,radius,k', [([1], [1], [-1], 1), ([1], [1, 2], [0], 1), ([1], [1], [0], 0)])
def test_invalid_spring_boxes_and_laws_refuse(displacement, candidate, radius, k):
    with pytest.raises(ValueError, match='spring law'):
        bounds.spring_gap(displacement, candidate, radius, k, 1, 1)
