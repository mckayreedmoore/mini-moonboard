"""The new dependency ordering must preserve the full six-DOF relation."""

import numpy as np
import pytest

from fea.wood_joint_current_nut_pivot import parse_equations, pivot_fit


def test_full_relation_is_preserved_for_arbitrary_nonrigid_shaft_motion():
    rng = np.random.default_rng(347)
    matrix = rng.normal(size=(6, 51))
    pivots, new, inverse, condition, error = pivot_fit(matrix)
    original = np.column_stack((-matrix, np.eye(6)))
    np.testing.assert_allclose(new, -inverse @ original, atol=1e-12)
    shaft_motion = rng.normal(size=(51, 16))
    admissible_state = np.vstack((shaft_motion, matrix @ shaft_motion))
    np.testing.assert_allclose(new @ admissible_state, 0, atol=1e-12)
    assert len(set(pivots)) == 6
    assert condition < 100
    assert error < 1e-12
    # Six independent changes of the controls must each violate the new
    # equations: no rigid control or engagement component was dropped.
    assert np.linalg.matrix_rank(new[:, -6:]) == 6


def test_rank_deficient_relation_is_rejected():
    with pytest.raises(ValueError, match="do not span"):
        pivot_fit(np.ones((6, 20)))


def test_native_field_overflow_is_rejected_before_use():
    with pytest.raises(ValueError, match="f20.0"):
        parse_equations("*EQUATION\n1\n1,1,-1.2345678901234567e-04\n")
