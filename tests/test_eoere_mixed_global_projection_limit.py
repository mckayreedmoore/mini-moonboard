"""Known-answer dual-norm and common-load controls, independent of raw assets."""
from fractions import Fraction as F
from types import SimpleNamespace

import pytest

from scripts import eoere_mixed_global_projection_limit as model


def test_two_exact_same_load_witnesses_give_a_metric_floor_for_every_projection():
    # D=(1,1,1), r1=(2,1,2), r2=(1,3,1), hence z=(1,-2,1).
    r1, r2 = [2, 1, 2], [1, 3, 1]
    assert sum(r1) == sum(r2)
    z = [a-b for a, b in zip(r1, r2, strict=True)]
    result = model.annihilator_floor(z, [1, 0, 0], [1, 1, 1], [], 0)
    assert F(result['exact_full_metric_lower_for_every_registered_kernel_projection']) == F(1, 6)
    for v in [-10**20, -F(1, 3), 0, 7]:
        assert (1+v)**2+2*v*v >= F(1, 6)


def test_both_correction_boxes_reduce_action_and_increase_the_norm_conservatively():
    result = model.annihilator_floor([1, -2, 1], [1, 0, 0], [2, 3, 5], [0, 2], F(1, 10))
    assert F(result['exact_nonnegative_action_lower']) == F(9, 10)
    expected = F(11, 10)**2/2+F(4, 3)+F(11, 10)**2/5
    assert F(result['exact_dual_density_norm_square_upper']) == expected
    assert F(result['exact_full_metric_lower_for_every_registered_kernel_projection']) == F(81, 100)/expected
    for first in [-F(1, 10), F(1, 10)]:
        for last in [-F(1, 10), F(1, 10)]:
            corrected = [F(1)+first, F(-2), F(1)+last]
            assert abs(corrected[0]) >= F(result['exact_nonnegative_action_lower'])
            assert sum(v*v/k for v, k in zip(corrected, [2, 3, 5], strict=True)) <= expected


def test_uniform_pressure_dual_norm_survives_disjoint_support_subdivision():
    # Density=2, kappa=3, area=5: integral(density²/kappa)=20/3.
    whole = model.annihilator_floor([10], [1], [15], [], 0)
    split = model.annihilator_floor([4, 6], [1, 1], [6, 9], [], 0)
    assert F(whole['exact_dual_density_norm_square_upper']) == F(split['exact_dual_density_norm_square_upper']) == F(20, 3)
    assert whole['exact_full_metric_lower_for_every_registered_kernel_projection'] == split['exact_full_metric_lower_for_every_registered_kernel_projection']


def test_additional_continuous_area_is_in_the_full_metric_even_outside_supports():
    # A candidate density z=1 on [0,1], zero elsewhere on [0,2].
    # A virtual field phi=1 on [0,1], then phi=x on [1,2] has full metric10/3.
    result = model.annihilator_floor([1], [1], [1], [], 0)
    floor = F(result['exact_full_metric_lower_for_every_registered_kernel_projection'])
    full_metric = 1+F(7, 3)
    assert full_metric >= floor == 1
    # The support metric alone is not asserted equal to the full metric.
    assert full_metric != 1


def test_continuous_two_support_and_spring_oracle_retains_affine_variation():
    # Omega=[-2,2], kappa=2, disjoint supports [-2,0],[0,2], plus k=3.
    # D has columns (1,-1),(1,1),(1,0). Both vectors balance p=(8,0).
    r1, r2 = [3, 3, 2], [2, 2, 4]
    assert [sum(r1), -r1[0]+r1[1]] == [sum(r2), -r2[0]+r2[1]] == [8, 0]
    result = model.annihilator_floor([a-b for a, b in zip(r1, r2, strict=True)], [0, 0, 1], [4, 4, 3], [], 0)
    assert F(result['exact_dual_density_norm_square_upper']) == F(11, 6)
    floor = F(result['exact_full_metric_lower_for_every_registered_kernel_projection'])
    assert floor == F(24, 11)
    for a, b in [(0, 0), (-F(3, 11), 0), (2, -7), (F(1, 10**20), F(1, 10**30))]:
        full = 8*a*a+F(32, 3)*b*b+3*(1+a)**2
        auxiliary = 4*(a-b)**2+4*(a+b)**2+3*(1+a)**2
        assert full == 11*(a+F(3, 11))**2+F(32, 3)*b*b+floor >= floor
        assert full-auxiliary == F(8, 3)*b*b


def test_action_uncertainty_that_spans_zero_produces_no_positive_obstruction():
    result = model.annihilator_floor([1, -1], [1, 0], [1, 1], [0], 2)
    assert result['exact_nonnegative_action_lower'] == '0'
    assert result['exact_full_metric_lower_for_every_registered_kernel_projection'] == '0'


@pytest.mark.parametrize('change', ['negative_box', 'negative_index', 'boolean_index', 'missing_metric', 'zero_metric', 'zero_norm'])
def test_invalid_metric_box_or_registration_is_refused(change):
    arguments = [[1, -1], [1, 0], [1, 1], [0], F(0)]
    if change == 'negative_box': arguments[4] = -1
    if change == 'negative_index': arguments[3] = [-1]
    if change == 'boolean_index': arguments[3] = [True]
    if change == 'missing_metric': arguments[2].pop()
    if change == 'zero_metric': arguments[2][1] = 0
    if change == 'zero_norm': arguments[0] = [0, 0]
    with pytest.raises(ValueError):
        model.annihilator_floor(*arguments)


def test_prior_arithmetic_uses_captured_bytes_instead_of_an_ordinary_module_cache(monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, 'scripts.eoere_mixed_shaft_projection_limit', SimpleNamespace(certificate_ceiling=None))
    prior = model.prior_method({})
    assert callable(prior.certificate_ceiling)
    assert prior.certificate_ceiling(0, 0, 1, 1, 1, 5)['exact_necessary_lower_endpoint_ceiling'] == '0'
    with pytest.raises(ValueError, match='arithmetic changed'):
        model.prior_method({model.PRIOR['path']: '0'*64})
