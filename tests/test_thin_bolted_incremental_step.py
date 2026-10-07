"""Cancellation-resistant energy identities and unchanged-force warm coupons."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_incremental_step as incremental


@pytest.mark.parametrize("old,change", [(2., .001), (2., -3.), (-1., 2.), (-1., -.1)])
def test_unilateral_remainder_matches_factorized_original_energy(old, change):
    k = 17.
    direct = .5 * k * (max(old + change, 0.)**2 - max(old, 0.)**2) - k * max(old, 0.) * change
    assert incremental.positive_quadratic_remainder(old, change, k) == pytest.approx(direct, abs=1e-12)


@pytest.mark.parametrize("old,change", [([2., 0.], [.01, .2]), ([2., 0.], [-1.5, 0.]),
                                      ([.5, 0.], [1., .1]), ([2., 0.], [-4., 0.])])
def test_circular_remainder_matches_independent_force_and_energy(old, change):
    old, change = np.array(old), np.array(change)
    f, _, energy = frame.spring_constitutive(np.r_[0., old], 0., 100., 1., False)
    new_energy = frame.spring_constitutive(np.r_[0., old + change], 0., 100., 1., False)[2]
    reference = new_energy - energy - f[1:] @ change
    assert incremental.radial_remainder(old, change, 100., 1.) == pytest.approx(reference, abs=1e-10)


def dummy_contact(n):
    return [{"id": "zero-port", "B": csr_matrix((1, n)), "stiffness": 1.,
             "kind": "shaft_end_capture", "first": "coupon", "second": "fixed"}]


def test_linear_increment_resolves_change_lost_in_large_total_potential():
    K = csr_matrix([[1.]])
    q, applied = np.array([1e8]), np.array([1e8 + 1e-4])
    C, ck = csr_matrix((1, 1)), np.ones(1)
    candidate = q + 1e-4
    before = incremental.stable_fields(K, applied, [], C, ck, q)
    after = incremental.stable_fields(K, applied, [], C, ck, candidate)
    assert float(after[1]) - float(before[1]) == 0.
    h = candidate - q
    hand = float((q - applied) @ h + .5 * h @ h)
    assert hand < 0.
    assert before[1] - after[1] == pytest.approx(-hand, abs=1e-20)
    assert after[1] <= before[1] + .5 * hand


def test_radial_increment_resolves_transverse_curvature_below_total_energy_roundoff():
    K = csr_matrix(np.diag([1., 0., 0.]))
    q, applied = np.array([1e8, 2., 0.]), np.array([1e8, 100., 0.])
    B = np.zeros((3, 3)); B[1, 1], B[2, 2] = 1., 1.
    groups = [{"B": csr_matrix(B), "ka": 0., "kl": 100., "clearance": 1., "tension_only": False}]
    C, ck, h = csr_matrix((1, 3)), np.ones(1), np.array([0., 0., 1e-5])
    before = incremental.stable_fields(K, applied, groups, C, ck, q)
    after = incremental.stable_fields(K, applied, groups, C, ck, q + h)
    assert float(after[1]) - float(before[1]) == 0.
    radius_change = h[2]**2 / (np.hypot(2., h[2]) + 2.)
    expected = 50. * radius_change * (2. + radius_change)
    assert incremental.physical_energy_increment(K, applied, groups, C, ck, q, h) == pytest.approx(expected, rel=1e-12)


def test_increment_matches_direct_original_potential_at_ordinary_scales():
    rng = np.random.default_rng(413)
    K = csr_matrix(np.diag([3., 7., 11.]))
    groups = [{"B": csr_matrix(np.eye(3)), "ka": 17., "kl": 29., "clearance": .7, "tension_only": True}]
    C, ck, applied = csr_matrix([[1., -2., .5], [-1., 0., 1.]]), np.array([13., 19.]), np.array([2., 3., 5.])
    for _ in range(12):
        q, h = rng.normal(size=3), rng.normal(size=3)
        old = incremental.ORIGINAL_FIELDS(K, applied, groups, C, ck, q)[1]
        new = incremental.ORIGINAL_FIELDS(K, applied, groups, C, ck, q + h)[1]
        assert incremental.physical_energy_increment(K, applied, groups, C, ck, q, h) == pytest.approx(new - old, abs=1e-10)


def test_warm_iterate_is_rebalanced_against_original_force_law():
    K, applied, contacts = csr_matrix([[1.]]), np.array([1e8 + 1e-4]), dummy_contact(1)
    warm = np.array([1e8])
    response = incremental.compatible_contact_solve(K, applied, [], contacts, [], warm_q=warm)
    assert response["converged"]
    assert response["gradient_inf_n"] < 1e-5
    assert response["warm_iterate_used_only_as_initialization"]
    assert response["q"][0] == pytest.approx(applied[0], abs=1e-7)
    np.testing.assert_array_equal(warm, [1e8])
    assert type(response["potential_energy_nmm"]) is float
    assert response["newton_iterations"] < 10


def old_fixture_module():
    path = Path(__file__).with_name("test_thin_bolted_numerical_step.py")
    spec = importlib.util.spec_from_file_location("reused_numerical_fixtures", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reuses_inactive_and_unequal_support_answers_with_same_tolerances():
    coupons = old_fixture_module()
    for inputs in (coupons.inactive_fixture(), coupons.inactive_fixture(0., (0., 0.)), coupons.unequal_supported_shaft()[:4]):
        original = coupons.numerical.compatible_contact_solve(*inputs, [])
        new = incremental.compatible_contact_solve(*inputs, [])
        assert new["converged"]
        assert new["gradient_inf_n"] < 1e-5
        np.testing.assert_allclose(new["q"], original["q"], atol=2e-7)
        np.testing.assert_allclose(new["connector_local_force_n"], original["connector_local_force_n"], atol=1e-6)


@pytest.mark.parametrize("warm", [[1., 2.], [np.nan]])
def test_unmapped_or_nonfinite_warm_iterate_is_rejected(warm):
    with pytest.raises(ValueError, match="finite warm iterate"):
        incremental.compatible_contact_solve(csr_matrix([[1.]]), np.array([1.]), [], dummy_contact(1), [], warm_q=warm)
