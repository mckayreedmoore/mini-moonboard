"""Known-answer controls for exact equilibrium-equivalent scalar bounds."""
import sys
from fractions import Fraction as F
from types import SimpleNamespace

import pytest

from scripts import eoere_normal_patch_functionals as model
from scripts import eoere_original_load_bounds as bounds

AUDIT = SimpleNamespace(functional=bounds.functional)


def scalar(offset, coefficients, candidate=(0, 0), radius=(0, 0), stiffness=(100, 1), gap=F(1, 2)):
    return model.shifted_scalar(offset, coefficients, candidate, radius, stiffness, gap, AUDIT)


@pytest.mark.parametrize('multiplier', [-F(3, 2), 0, 1, F(7, 3)])
def test_nonzero_load_identity_with_signed_nonunit_multiplier(multiplier):
    target, direction, reaction = [1, 0], [1, 1], [2, 1]
    transformed = model.equivalent(target, direction, multiplier)
    load = sum(d*r for d, r in zip(direction, reaction, strict=True))
    assert multiplier*load+sum(c*r for c, r in zip(transformed, reaction, strict=True)) == 2


def test_leg_compression_sign_retains_own_downward_load_offset():
    # -N + B = p=-2, so N=2+B. The reference reaction is (N,B)=(4,2).
    assert model.equivalent([1, 0], [-1, 1], -1) == [0, 1]
    result = scalar(2, {1: 1}, candidate=[4, 2], gap=0)
    assert F(result['exact_signed_lower_n']) == F(result['exact_upper_n']) == 4


def test_balance_removes_stiff_floor_metric_in_a_known_two_spring_example():
    original = scalar(2, {0: 1})
    transformed = scalar(2, {1: -1})
    assert F(original['unchanged_metric_enclosure']['exact_equilibrium_change_norm_upper']) == 10
    assert F(transformed['unchanged_metric_enclosure']['exact_equilibrium_change_norm_upper']) == 1
    assert not original['strict_positive_normal_resultant_certified']
    assert transformed['strict_positive_normal_resultant_certified']


def test_offset_and_candidate_center_remain_signed():
    result = scalar(-3, {0: 1}, candidate=[2, 0], gap=0)
    assert F(result['exact_center_n']) == F(result['exact_signed_lower_n']) == F(result['exact_upper_n']) == -1
    assert not result['strict_positive_normal_resultant_certified']


def test_correction_box_and_gap_radius_cover_opposing_coefficients():
    result = scalar(-1, {0: -2, 1: 3}, candidate=[1, 2], radius=[F(1, 10), F(1, 5)],
                    stiffness=[2, 4], gap=F(1, 88))
    assert F(result['exact_center_n']) == 3
    assert F(result['exact_signed_lower_n']) == F(6, 5)
    assert F(result['exact_upper_n']) == F(24, 5)
    assert F(result['unchanged_metric_enclosure']['exact_weighted_Gram_spectral_upper']) == 44


def test_zero_transformed_functional_is_the_constant_exact_load():
    result = scalar(F(7, 3), {}, gap=1000000)
    assert F(result['exact_signed_lower_n']) == F(result['exact_upper_n']) == F(7, 3)


def test_one_pass_direction_and_integer_inputs_are_exact_without_mutation():
    target = [1, 0]
    assert model.equivalent(iter(target), (d for d in [-1, 1]), -1) == [F(0), F(1)]
    assert target == [1, 0]
    result = scalar(0, {0: 1}, candidate=[0, 0], stiffness=[3, 1], gap=F(1, 6))
    assert F(result['exact_upper_n']) == 1


@pytest.mark.parametrize('key', [True, F(1, 2), 0.5, -1, 2])
def test_noninteger_indices_are_not_truncated_or_reinterpreted(key):
    with pytest.raises(ValueError, match='integer scalar indices'):
        scalar(0, {key: 1})


def test_incomplete_direction_and_invalid_gap_are_refused():
    with pytest.raises(ValueError, match='same nonempty'):
        model.equivalent([1], [], 1)
    with pytest.raises(ValueError, match='nonnegative gap'):
        scalar(0, {0: 1}, gap=-1)


def test_negative_alias_cannot_be_counted_as_two_independent_reactions():
    with pytest.raises(ValueError, match='bounded nonnegative'):
        scalar(0, {-1: 1, 1: 1}, stiffness=[1, 1])


def test_incomplete_candidate_box_and_nonpositive_metric_are_refused():
    for radius, stiffness in (([0], [1, 1]), ([0, 0], [1]), ([0, -1], [1, 1]), ([0, 0], [0, 1])):
        with pytest.raises(ValueError, match='complete positive scalar'):
            scalar(0, {0: 1}, radius=radius, stiffness=stiffness)


def test_scalar_operand_iterators_are_normalized_once():
    result = scalar(2, {1: 1}, candidate=(v for v in [4, 2]), radius=iter([0, 0]), stiffness=iter([100, 1]), gap=0)
    assert F(result['exact_signed_lower_n']) == F(result['exact_upper_n']) == 4


def test_verified_bootstrap_ignores_a_poisoned_ordinary_base_cache(monkeypatch):
    def poison(*args, **kwargs):
        raise AssertionError('cached helper must not execute')
    cached = SimpleNamespace(captured=poison, prepare=poison, require=poison, distributed_gap=poison)
    monkeypatch.setitem(sys.modules, 'scripts.eoere_normal_patch_reactions', cached)
    pins = {}; actual = model.producer(pins)
    assert actual is not cached and pins == {model.BASE['path']: model.BASE['sha256']}
    assert actual.distributed_gap(F(0), [0], [{'stiffness': F(3)}], [F(1)], [F(0)], [F(0)]) == F(1, 6)


def test_bootstrap_rejects_a_conflicting_frozen_source_pin():
    with pytest.raises(ValueError, match='base source changed'):
        model.producer({model.BASE['path']: '0'*64})


def test_inherited_runtime_is_enforced_and_recordable():
    expected = {'python': model.platform.python_version(), 'numpy': model.np.__version__,
                'scipy': model.importlib.metadata.version('scipy')}
    assert model.check_runtime(expected) == expected
    for key in expected:
        with pytest.raises(ValueError, match='exact functional runtime'):
            model.check_runtime(dict(expected, **{key: 'different'}))
    with pytest.raises(ValueError, match='exact functional runtime'):
        model.check_runtime({})
