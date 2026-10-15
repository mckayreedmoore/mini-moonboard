"""Independent traction work, plastic limits, support integration and claim guards."""
import copy
from fractions import Fraction as F
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import eoere_cleat_section_dual as dual

STRENGTHS = {'tension': 2., 'compression': 3., 'parallel_shear': 4., 'rolling_shear': 5.}
SYMMETRIC = dict.fromkeys(STRENGTHS, 1.)


def inputs():
    return dual.current.read(dual.current.ref(dual.INPUT))


def ratio(multiplier, wrench, width=2., height=2., strengths=STRENGTHS):
    support, _ = dual.support(multiplier, width, height, strengths)
    return sum(F(str(a))*F(str(b)) for a, b in zip(multiplier, wrench, strict=True))/support


@pytest.mark.parametrize('plane,expected', [
    ((0, 1, 0), (F(2), F(1), F(0))),
    ((0, 1, 1), (F(2), F(2, 3), F(2, 3))),
    ((-3, 1, 0), (F(0), F(0), F(0))),
    ((3, 1, 0), (F(4), F(0), F(0)))])
def test_exact_clipping_matches_independent_half_square_triangle_and_empty_moments(plane, expected):
    square = [(F(-1), F(-1)), (F(1), F(-1)), (F(1), F(1)), (F(-1), F(1))]
    polygon = dual.clip(square, tuple(map(F, plane)))
    assert dual.moments(polygon, F(0)) == expected


def test_duplicate_affine_pieces_are_counted_once_and_boundary_ties_have_zero_area():
    forms = [(F(0), F(1), F(0)), (F(0), F(1), F(0)), (F(0), F(-1), F(0))]
    cells = dual.cells(forms, F(1))
    assert len(cells) == 2 and sum(m[0] for _, _, m in cells) == 4
    assert sum(sum(c*m for c, m in zip(forms[i], measure, strict=True)) for i, _, measure in cells) == 2
    for i, polygon, _ in cells:
        for u, v in polygon:
            assert all(forms[i][0]+forms[i][1]*u+forms[i][2]*v >= f[0]+f[1]*u+f[2]*v for f in forms)


@pytest.mark.parametrize('axis,sign,strength', [(0, 1, 2.), (0, -1, 3.), (1, 1, 4.), (1, -1, 4.),
                                               (2, 1, 5.), (2, -1, 5.)])
def test_pure_force_limits_are_the_exact_area_times_own_signed_traction_cap(axis, sign, strength):
    multiplier, wrench = [0.]*6, [0.]*6
    multiplier[axis], wrench[axis] = sign, sign*4*strength
    assert ratio(multiplier, wrench) == 1


def test_pure_asymmetric_normal_bending_matches_the_known_plastic_neutral_axis_capacity():
    # Width=height=2; neutral q=-1/5 gives zero resultant for sigma=+2/-3.
    # Exact moment capacity A*a*Ft*Fc/(Ft+Fc) = 24/5.
    multiplier = [F(1, 5), 0, 0, 0, 1, 0]
    assert ratio(multiplier, [0, 0, 0, 0, F(24, 5), 0]) == 1
    assert ratio([F(1, 5), 0, 0, 0, -1, 0], [0, 0, 0, 0, -F(24, 5), 0]) == 1


def test_pure_torque_square_support_is_the_known_integral_of_max_abs_coordinates():
    support, certificate = dual.support([0, 0, 0, 1, 0, 0], 2., 2., SYMMETRIC)
    assert support == F(8, 3)
    assert len(certificate['normalized_cells']) == 4
    assert ratio([0, 0, 0, 1, 0, 0], [0, 0, 0, F(8, 3), 0, 0], strengths=SYMMETRIC) == 1


def test_independent_point_traction_virtual_work_recovers_all_six_signs_and_lever_arms():
    width, height = 8., 6.
    strengths = dict(STRENGTHS)
    multiplier = np.array([.7, -.3, .2, .11, -.13, .17])
    matrix = np.asarray(dual.form_matrix(width, height, strengths, 1.))
    for p, q in [(-2., 3.), (1., -2.), (.5, .7)]:
        axis_tractions = [[2., 0., 0.], [-3., 0., 0.], [0., 4., 0.], [0., -4., 0.],
                         [0., 0., 5.], [0., 0., -5.]]
        for i, (normal, vp, vq) in enumerate(axis_tractions):
            wrench = [normal, vp, vq, p*vq-q*vp, q*normal, -p*normal]
            affine = (matrix[i]@multiplier)@np.array([1., p/(height/2), q/(width/2)])
            assert affine == pytest.approx(multiplier@wrench, abs=1e-14)


def test_exact_affine_partition_agrees_with_independent_dense_midpoint_integration():
    multiplier = [.73, -.31, .27, .13, -.19, .17]
    width, height = 8., 6.
    exact, _ = dual.support(multiplier, width, height, STRENGTHS)
    n = 600
    u = -1+(np.arange(n)+.5)*2/n
    p, q = (height/2)*u[:, None], (width/2)*u[None, :]
    normal = multiplier[0]+q*multiplier[4]-p*multiplier[5]
    vp, vq = multiplier[1]-q*multiplier[3], multiplier[2]+p*multiplier[3]
    expected = np.maximum.reduce([2*normal, -3*normal, np.broadcast_to(4*vp, normal.shape),
                                  np.broadcast_to(-4*vp, normal.shape), np.broadcast_to(5*vq, normal.shape),
                                  np.broadcast_to(-5*vq, normal.shape)]).mean()*width*height
    assert float(exact) == pytest.approx(expected, abs=2e-4)
    value, gradient = dual.support_value_gradient(np.array(multiplier), width, height, STRENGTHS)
    assert value == pytest.approx(float(exact), rel=2e-14)
    assert gradient@multiplier == pytest.approx(value, rel=2e-14)
    for axis in range(6):
        h = 1e-6
        step = np.eye(6)[axis]*h
        above = dual.support_value_gradient(np.array(multiplier)+step, width, height, STRENGTHS)[0]
        below = dual.support_value_gradient(np.array(multiplier)-step, width, height, STRENGTHS)[0]
        assert gradient[axis] == pytest.approx((above-below)/(2*h), rel=1e-7, abs=1e-7)


def test_support_is_positively_homogeneous_and_convex_with_signed_asymmetric_normal_strength():
    first = [1., 2., -3., .4, .5, -.6]
    second = [-2., .7, .9, -.3, .2, -.1]
    h1 = dual.support(first, 2., 3., STRENGTHS)[0]
    h2 = dual.support(second, 2., 3., STRENGTHS)[0]
    assert dual.support([3*v for v in first], 2., 3., STRENGTHS)[0] == 3*h1
    assert dual.support([a+b for a, b in zip(first, second, strict=True)], 2., 3., STRENGTHS)[0] <= h1+h2


def test_arbitrary_known_equilibrated_traction_cannot_exceed_its_pointwise_interaction_upper_bound():
    # A piecewise constant 2x2 field inside the unit diamond, integrated independently.
    points = [(-.5, -.5), (-.5, .5), (.5, -.5), (.5, .5)]
    tractions = [[.2, 1., -.5], [-.3, -.4, .7], [.7, .3, .2], [-.4, .1, -.8]]
    wrench = np.zeros(6)
    for (p, q), (normal, vp, vq) in zip(points, tractions, strict=True):
        wrench += [normal, vp, vq, p*vq-q*vp, q*normal, -p*normal]
        assert max(normal/2, -normal/3)+abs(vp)/4+abs(vq)/5 < 1
    for multiplier in [[1., 2., -1., .3, .2, -.6], [-1., .7, -.3, -.2, .5, .8]]:
        assert ratio(multiplier, wrench.tolist()) < 1


def test_optimizer_candidate_matches_pure_load_analytic_limit_without_claiming_optimality():
    result = dual.search([8., 0., 0., 0., 0., 0.], 2., 2., STRENGTHS, inputs()['optimizer_options'])
    assert result['necessary_base_interaction_lower_bound'] == pytest.approx(1., rel=1e-8)
    assert not result['optimizer_diagnostic']['global_optimality_certified']


def test_unsuccessful_optimizer_still_requires_an_independently_valid_exact_candidate(monkeypatch):
    def unfinished(fun, initial, **kwargs):
        return SimpleNamespace(x=initial, success=False, status=9, message='iteration budget', nit=200)
    monkeypatch.setattr(dual, 'minimize', unfinished)
    result = dual.search([8., 0., 0., 0., 0., 0.], 2., 2., STRENGTHS, inputs()['optimizer_options'])
    assert not result['optimizer_diagnostic']['success']
    assert F(result['exact_necessary_base_interaction_fraction']) == 1
    assert result['optimizer_diagnostic']['global_optimality_certified'] is False


@pytest.mark.parametrize('lo,hi,status', [(F(6, 5), F(3, 2), 'section_traction_hypothesis_infeasible'),
                                        (F(1, 2), F(3, 4), 'preserved_construction_within_section_hypothesis'),
                                        (F(1, 2), F(3, 2), 'section_traction_hypothesis_unresolved_between_bounds'),
                                        (F(1), F(3, 2), 'section_traction_hypothesis_unresolved_between_bounds')])
def test_necessary_and_constructive_bounds_distinguish_infeasible_unresolved_and_preserved_construction(lo, hi, status):
    candidate = {'exact_necessary_base_interaction_fraction': str(lo)}
    old = {'continuous_base_reference_interaction': {'exact_upper_fraction': str(hi)}, 'scenarios': [
        {'id': 'own', 'working_reference': True, 'strength_divisor': 1., 'whole_wrench_multiplier': 1.}]}
    row = dual.comparisons(candidate, old)[0]
    assert row['section_disposition'] == status
    assert row['complete_cleat_resistance'] is None and row['physical_failure_established'] is False
    with pytest.raises(ValueError):
        dual.comparisons({'exact_necessary_base_interaction_fraction': str(hi+1)}, old)


def test_divisor_and_load_magnification_scale_both_bounds_without_changing_material_hypothesis():
    old = {'continuous_base_reference_interaction': {'exact_upper_fraction': '3/4'}, 'scenarios': [
        {'id': 'own', 'working_reference': True, 'strength_divisor': 2., 'whole_wrench_multiplier': 1.5}]}
    row = dual.comparisons({'exact_necessary_base_interaction_fraction': '1/2'}, old)[0]
    assert row['necessary_interaction_lower_bound'] == 1.5
    assert row['preserved_construction_upper_bound'] == 2.25
    assert row['section_disposition'] == 'section_traction_hypothesis_infeasible'


@pytest.mark.parametrize('change', ['zero_width', 'negative_height', 'strength_zero', 'strength_nan',
                                   'multiplier_nan', 'missing_component'])
def test_invalid_support_geometry_strength_or_multiplier_is_refused(change):
    width, height, strengths, multiplier = 2., 2., dict(STRENGTHS), [1.]*6
    if change == 'zero_width':
        width = 0.
    elif change == 'negative_height':
        height = -1.
    elif change == 'strength_zero':
        strengths['rolling_shear'] = 0.
    elif change == 'strength_nan':
        strengths['compression'] = np.nan
    elif change == 'multiplier_nan':
        multiplier[3] = np.nan
    else:
        multiplier.pop()
    with pytest.raises(ValueError):
        dual.support(multiplier, width, height, strengths)


@pytest.mark.parametrize('key,value', [('current_bolt_count', 102), ('extra_grid', True), ('actual_observations', 'assumed'),
                                    ('physical_demand_bounds_established', True), ('structural_acceptance', True),
                                    ('optimizer_options', {'method': 'SLSQP', 'maxiter': 2, 'ftol': .1})])
def test_scope_observation_and_method_guards_cannot_be_weakened(key, value):
    data = copy.deepcopy(inputs())
    dual.validate(data)
    data[key] = value
    with pytest.raises(ValueError):
        dual.validate(data)
