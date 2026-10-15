"""Portable known-answer and counterexample controls for the proof-family limit."""
from fractions import Fraction as F
from types import SimpleNamespace

import pytest

from scripts import eoere_mixed_shaft_projection_limit as model


def coupon():
    return [[[1, 0, 0, 0, 0], [1, 1, 0, 0, 0], [1, 2, 0, 0, 0]], [1, 0, 0], [1, 1, 1], [0, 1]]


def test_exact_null_witness_supplies_a_known_metric_floor_for_arbitrary_projections():
    arguments = coupon(); result = model.metric_obstruction(*arguments)
    assert list(map(F, result['exact_null_witness'])) == [1, -2, 1]
    assert F(result['exact_weighted_Gram_lower_for_every_shaft_projection']) == F(1, 6)
    # Includes an attaining projection; none is selected by an optimizer.
    for a, b in [(0, 0), (3, -7), (-F(5, 6), F(1, 2)), (F(1, 10**30), 10**20)]:
        shifted = [F(c)+row[0]*a+row[1]*b for row, c in zip(arguments[0], arguments[1], strict=True)]
        assert sum(v*v for v in shifted) >= F(1, 6)


@pytest.mark.parametrize('extra', [F(1), F(1, 10**100)])
def test_a_third_independent_column_must_not_be_silently_dropped(extra):
    arguments = coupon(); arguments[0][0][4] = extra
    with pytest.raises(ValueError, match='every retained'):
        model.metric_obstruction(*arguments)


def test_null_scaling_sign_and_nonuniform_metric_are_exact():
    arguments = coupon(); arguments[2] = [2, 3, 5]
    expected = F(30, 61)
    for scale, sign in [(1, 1), (-3, -1), (F(1, 10**25), 1)]:
        rows = [[scale*v for v in row] for row in arguments[0]]
        result = model.metric_obstruction(rows, [sign*v for v in arguments[1]], arguments[2], arguments[3])
        assert F(result['exact_weighted_Gram_lower_for_every_shaft_projection']) == expected


@pytest.mark.parametrize('change', ['zero_stiffness', 'singular_pivots', 'zero_work', 'negative_pivot', 'float_pivot', 'short_row'])
def test_invalid_or_noninformative_null_witness_is_refused(change):
    arguments = coupon()
    if change == 'zero_stiffness': arguments[2][1] = 0
    if change == 'singular_pivots': arguments[3] = [2, 3]
    if change == 'zero_work': arguments[1] = [1, 1, 1]
    if change == 'negative_pivot': arguments[3] = [-1, 0]
    if change == 'float_pivot': arguments[3] = [0., 1]
    if change == 'short_row': arguments[0][2].pop()
    with pytest.raises(ValueError):
        model.metric_obstruction(*arguments)


def test_ceiling_uses_a_lower_root_enclosure_and_the_full_signed_center():
    result = model.certificate_ceiling(-2, F(1, 4), 1, 1, 3, 5)
    radius = F(result['exact_formula_radius_lower']); step = F(1, 10**24)
    assert radius*radius <= 2 < (radius+step)**2
    assert F(result['exact_necessary_lower_endpoint_ceiling']) == 5*(F(9, 4)-radius)/3
    assert result['no_shaft_only_projection_can_certify_exceedance_with_this_fixed_certificate'] is False
    assert model.certificate_ceiling(0, 0, 1, 1, 3, 5)['exact_necessary_lower_endpoint_ceiling'] == '0'


def test_common_corrected_dual_controls_a_center_that_moves_with_the_projection():
    # D=[1,1], candidate x=[0,0], rho=[1,0], exact corrected r0=[1,0].
    # C=[1,0], fixed work=-1/4, p=1. The shifted center is -1/4-v.
    # Keeping the old center would be wrong, while the common-witness ceiling holds.
    original_absolute_upper = F(1, 4)+1
    for v in [-10**10, -2, -1, 0, 3, F(1, 3), 10**10]:
        shifted_center = -F(1, 4)-v
        shifted_box = abs(1+v)
        assert abs(shifted_center)-shifted_box <= original_absolute_upper


@pytest.mark.parametrize('values', [(0, -1, 1, 1, 1, 5), (0, 0, -1, 1, 1, 5),
                                    (0, 0, 1, 0, 1, 5), (0, 0, 1, 1, 0, 5)])
def test_invalid_ceiling_premises_are_refused(values):
    with pytest.raises(ValueError):
        model.certificate_ceiling(*values)


def test_verified_bootstrap_ignores_a_poisoned_ordinary_module(monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, 'scripts.eoere_normal_patch_functionals', SimpleNamespace(producer=None))
    boot = model.bootstrap({})
    assert callable(boot.producer) and boot.producer({}).LOADED_SHA == boot.BASE['sha256']
    with pytest.raises(ValueError, match='bootstrap changed'):
        model.bootstrap({model.BOOT['path']: '0'*64})
