"""Independent known-answer controls for exact static recession certificates."""
from fractions import Fraction as F

import numpy as np
import pytest

from scripts import eoere_recession_certificate as c


def test_exact_integer_inverse_enclosure_and_neumann_bound():
    rows = [{0: F(2), 1: F(1, 3)}, {0: F(-1, 5), 1: F(3)}]
    proof = c.inverse_bound(rows)
    exact = np.asarray([[F(45, 91), F(-5, 91)], [F(3, 91), F(30, 91)]])
    expected = max(sum(abs(v) for v in row) for row in exact)
    assert F(proof['exact_inverse_norm_upper']) >= expected
    assert F(proof['exact_inverse_residual_inf']) < F(1, 10**14)


def test_singular_or_inaccurate_inverse_cannot_prove_rank():
    with pytest.raises(np.linalg.LinAlgError):
        c.inverse_bound([{0: F(1), 1: F(1)}, {0: F(1), 1: F(1)}])
    with pytest.raises(ValueError, match='nonsingularity'):
        c.inverse_bound([{0: F(2)}], [[0.]])


def test_tiny_stored_matrix_terms_survive_the_exact_integer_product():
    tiny = F(1, 10**80)
    proof = c.inverse_bound([{0: 1, 1: tiny}, {1: 1}], np.eye(2))
    assert F(proof['exact_inverse_residual_inf']) == tiny
    assert F(proof['exact_inverse_norm_upper']) == 1/(1-tiny)


def test_one_sided_gravity_support_has_a_strict_static_certificate():
    # Coordinate is upward displacement; compression acts through C=-1.
    result = c.select_witness([{0: -1}], 1, 0, [-10])
    proof = result['load_certificate']
    assert proof['exact_balanced_strict_dual_exists'] is True
    assert F(proof['exact_strict_weight_margin_lower']) == 10
    for opening_direction in (F(1, 10), F(1), F(10)):
        assert -opening_direction <= 0 and -10*opening_direction < 0


def test_lifting_load_is_not_misclassified_as_supported():
    with pytest.raises(ValueError, match='not a nonexistence certificate'):
        c.select_witness([{0: -1}], 1, 0, [10])


def test_free_unloaded_rigid_direction_cannot_be_claimed_coercive():
    with pytest.raises((ValueError, np.linalg.LinAlgError)):
        c.select_witness([{0: -1}, {}], 2, 0, [-10, 0])


def test_bilateral_direction_and_two_foot_support_resist_moment_and_weight():
    # x, upward z, rotation. A restrains x; two C rows measure compression.
    rows = [{0: 1}, {1: -1, 2: -1}, {1: 2, 2: -2}]
    result = c.select_witness(rows, 3, 1, [3, -10, 4])
    weights = result['candidate_auxiliary_weights']
    assert np.allclose(weights, [3, 6, 4], rtol=0, atol=1e-12)
    assert result['load_certificate']['exact_balanced_strict_dual_exists'] is True
    for rz in ((F(1), F(0)), (F(2), F(1)), (F(2), F(-1))):
        z, rotation = rz
        assert -z+2*rotation <= 0 and -z-2*rotation <= 0
        assert -10*z+4*rotation < 0


def test_postcorrection_sign_guard_refuses_an_insufficient_margin():
    rank = c.inverse_bound([{0: 1}])
    with pytest.raises(ValueError, match='strict one-sided'):
        c.certify([{0: 1}], 1, 0, [-1], [1.], [0], rank)


def test_exact_residual_correction_can_cover_a_nonzero_floating_residual():
    rank = c.inverse_bound([{0: F(3)}])
    proof = c.certify([{0: F(3)}], 1, 0, [1], [1/3], [0], rank)
    assert F(proof['exact_candidate_balance_residual_inf']) > 0
    assert F(proof['exact_strict_weight_margin_lower']) > F(3, 10)


def test_rank_certificate_cannot_transfer_to_another_matrix():
    rank = c.inverse_bound([{0: F(3)}])
    with pytest.raises(ValueError, match='another matrix'):
        c.certify([{0: F(4)}], 1, 0, [1], [1/4], [0], rank)


def test_shared_matrix_rank_proof_still_certifies_each_own_load(monkeypatch):
    first = c.select_witness([{0: -1}], 1, 0, [-10])
    def forbidden(*args, **kwargs):
        raise AssertionError('an unchanged rank proof should be reused')
    monkeypatch.setattr(c, 'inverse_bound', forbidden)
    second = c.select_witness([{0: -1}], 1, 0, [-20], rank_proof=first['rank_certificate'],
                              selected=first['selected_minor_columns'])
    assert F(second['load_certificate']['exact_strict_weight_margin_lower']) == 20


def test_nonprefix_minor_corrects_a_load_with_negative_bilateral_weight():
    rows = [{0: F(1), 1: F(2)}]
    rank = c.inverse_bound(c.minor(rows, [1]))
    proof = c.certify(rows, 2, 1, [F(11, 10)], [-1., 1.], [1], rank)
    assert F(proof['exact_selected_correction_inf_upper']) == F(1, 20)
    assert F(proof['exact_strict_weight_margin_lower']) == F(19, 20)


@pytest.mark.parametrize('bad', [float('inf'), float('nan')])
def test_nonfinite_values_are_refused(bad):
    with pytest.raises(ValueError, match='finite'):
        c.inverse_bound([{0: bad}])


def test_distinct_square_minor_and_valid_source_column_indices_are_required():
    with pytest.raises(ValueError, match='distinct'):
        c.minor([{0: 1}, {1: 1}], [0, 0])
    with pytest.raises(ValueError, match='column indices'):
        c.normalized_rows([{2: 1}], 2)
