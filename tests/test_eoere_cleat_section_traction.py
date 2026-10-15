"""Exact six-resultant closure, independent integration and sufficient-bound guards."""
import copy
from fractions import Fraction as F
from itertools import pairwise

import numpy as np
import pytest

from scripts import eoere_cleat_section_traction as traction

STRENGTHS = {'tension': 2., 'compression': 3., 'parallel_shear': 4., 'rolling_shear': 5.}


def inputs():
    return traction.current.read(traction.current.ref(traction.INPUT))


def fixture(wrench=None, multiplier=None, width=8., height=6., strengths=STRENGTHS):
    wrench = [6., -5., 4., 7., -8., 9.] if wrench is None else wrench
    multiplier = [.7, -.3, .2, .11, -.13, .17] if multiplier is None else multiplier
    integral, certificate = traction.dual.support(multiplier, width, height, strengths)
    work = sum(traction.rational(a)*traction.rational(b) for a, b in zip(multiplier, wrench, strict=True))
    bound = {'certificate': certificate, 'exact_necessary_base_interaction_fraction': str(work/integral),
             'exact_complete_wrench_dual_work_fraction': str(work)}
    return wrench, bound


def evaluate(*args):
    data = inputs()
    return traction.construct(*args, data['residual_field_interaction_tolerance'], data['bernstein_cell_budget'])


@pytest.mark.parametrize('axis,sign,strength', [(0, 1, 2.), (0, -1, 3.), (1, 1, 4.), (1, -1, 4.),
                                               (2, 1, 5.), (2, -1, 5.)])
def test_known_uniform_signed_force_capacity_needs_no_correction_and_has_exact_unit_bound(axis, sign, strength):
    wrench, multiplier = [0.]*6, [0.]*6
    wrench[axis], multiplier[axis] = sign*4*strength, sign
    result = evaluate(*fixture(wrench, multiplier, 2., 2.))
    assert list(map(F, result['exact_residual_six_resultants'])) == [0]*6
    assert F(result['exact_corrected_field_base_interaction_upper_fraction']) == 1
    assert result['section_only_six_resultant_equilibrium_certified'] is True
    assert result['three_dimensional_compatibility_volume_equilibrium_or_free_side_faces_certified'] is False
    assert result['complete_cleat_resistance'] is None


def test_known_asymmetric_plastic_bending_has_zero_normal_force_and_exact_moment_capacity():
    wrench = [0, 0, 0, 0, F(24, 5), 0]
    result = evaluate(*fixture(wrench, [F(1, 5), 0, 0, 0, 1, 0], 2., 2.))
    assert list(map(F, result['exact_extremal_field_six_resultants_at_unit_interaction'])) == wrench
    assert F(result['exact_corrected_field_base_interaction_upper_fraction']) == 1


def test_known_square_torque_keeps_both_opposing_shear_families_and_exact_zero_force():
    strengths = dict.fromkeys(STRENGTHS, 1.)
    wrench = [0, 0, 0, F(8, 3), 0, 0]
    result = evaluate(*fixture(wrench, [0, 0, 0, 1, 0, 0], 2., 2., strengths))
    assert list(map(F, result['exact_extremal_field_six_resultants_at_unit_interaction'])) == wrench
    assert list(map(F, result['exact_residual_six_resultants'])) == [0]*6
    assert F(result['exact_corrected_field_base_interaction_upper_fraction']) == 1


def test_nonoptimal_pattern_recovers_every_signed_resultant_with_no_rounded_residual(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('No optimizer may be called for a frozen pattern')
    monkeypatch.setattr(traction.dual, 'search', forbidden)
    wrench, bound = fixture()
    result = evaluate(wrench, bound)
    residual = list(map(F, result['exact_residual_six_resultants']))
    assert all(value != 0 for value in residual)
    assert list(map(F, result['exact_correction_six_resultants'])) == residual
    assert list(map(F, result['exact_corrected_six_resultants'])) == list(map(traction.rational, wrench))
    assert result['exact_equilibrium_remainder_N_Vp_Vq_T_Mp_Mq'] == ['0']*6


def test_independent_gauss_integration_recovers_the_complete_polynomial_residual_wrench():
    wrench, bound = fixture()
    result = evaluate(wrench, bound)
    fields = [{(i, j): F(value) for i, j, value in field} for field in result['correction_polynomials_in_u_v']]
    nodes, weights = np.polynomial.legendre.leggauss(5)
    width, height = map(F, bound['certificate']['exact_rectangle_width_height_mm'])
    a, b, scale = float(width/2), float(height/2), float(width*height/4)
    actual = np.zeros(6)
    for u, wu in zip(nodes, weights, strict=True):
        for v, wv in zip(nodes, weights, strict=True):
            normal, parallel, rolling = [sum(float(c)*u**i*v**j for (i, j), c in field.items()) for field in fields]
            p, q = b*u, a*v
            actual += scale*wu*wv*np.array([normal, parallel, rolling, p*rolling-q*parallel, q*normal, -p*normal])
    assert actual == pytest.approx([float(F(v)) for v in result['exact_residual_six_resultants']], abs=2e-13)


def test_triangle_integration_of_signed_intercepts_independently_recovers_the_unit_pattern_wrench():
    _, bound = fixture()
    certificate = bound['certificate']
    width, height = map(F, certificate['exact_rectangle_width_height_mm'])
    a, b, scale = width/2, height/2, width*height/4
    intercepts = [[F(2), F(0), F(0)], [F(-3), F(0), F(0)], [F(0), F(4), F(0)],
                  [F(0), F(-4), F(0)], [F(0), F(0), F(5)], [F(0), F(0), F(-5)]]
    actual = [F(0)]*6
    for cell in certificate['normalized_cells']:
        vertices = [tuple(map(F, point)) for point in cell['vertices_u_v']]
        normal, parallel, rolling = intercepts[cell['traction_axis_intercept_index']]
        first = vertices[0]
        for second, third in pairwise(vertices[1:]):
            area = ((second[0]-first[0])*(third[1]-first[1])-(second[1]-first[1])*(third[0]-first[0]))/2
            p, q = b*(first[0]+second[0]+third[0])/3, a*(first[1]+second[1]+third[1])/3
            for i, value in enumerate([normal, parallel, rolling, p*rolling-q*parallel, q*normal, -p*normal]):
                actual[i] += scale*area*value
    result = evaluate(*fixture())
    assert actual == list(map(F, result['exact_extremal_field_six_resultants_at_unit_interaction']))


def test_pointwise_corrected_interaction_is_bounded_on_every_support_region():
    wrench, bound = fixture()
    result = evaluate(wrench, bound)
    mu = F(result['exact_extremal_field_multiplier_mu'])
    upper = F(result['exact_corrected_field_base_interaction_upper_fraction'])
    fields = [{(i, j): F(value) for i, j, value in field} for field in result['correction_polynomials_in_u_v']]
    intercepts = [[F(2), 0, 0], [F(-3), 0, 0], [0, F(4), 0], [0, F(-4), 0], [0, 0, F(5)], [0, 0, F(-5)]]
    for cell in bound['certificate']['normalized_cells']:
        points = [tuple(map(F, point)) for point in cell['vertices_u_v']]
        points.append(tuple(sum(p[i] for p in points)/len(points) for i in range(2)))
        for u, v in points:
            normal, parallel, rolling = [mu*base+sum(c*u**i*v**j for (i, j), c in field.items())
                                        for base, field in zip(intercepts[cell['traction_axis_intercept_index']], fields, strict=True)]
            interaction = max(normal/2, -normal/3)+abs(parallel)/4+abs(rolling)/5
            assert interaction <= upper


@pytest.mark.parametrize('change', ['force', 'mu', 'work', 'cell_index', 'cell_moment', 'cell_vertex', 'missing_cell',
                                   'width', 'strength', 'nonpositive_mu'])
def test_foreign_or_changed_wrench_normalization_and_certificate_cannot_enter_a_construction(change):
    wrench, bound = copy.deepcopy(fixture())
    if change == 'force':
        wrench[3] += 1.
    elif change == 'mu':
        bound['exact_necessary_base_interaction_fraction'] = '1'
    elif change == 'work':
        bound['exact_complete_wrench_dual_work_fraction'] = '1'
    elif change == 'cell_index':
        bound['certificate']['normalized_cells'][0]['traction_axis_intercept_index'] = 5
    elif change == 'cell_moment':
        bound['certificate']['normalized_cells'][0]['area_first_u_first_v_moments'][1] = '1'
    elif change == 'cell_vertex':
        bound['certificate']['normalized_cells'][0]['vertices_u_v'][0][0] = '1/2'
    elif change == 'missing_cell':
        bound['certificate']['normalized_cells'].pop()
    elif change == 'width':
        bound['certificate']['exact_rectangle_width_height_mm'][0] = '1'
    elif change == 'strength':
        bound['certificate']['exact_base_strengths_mpa']['tension'] = '100'
    else:
        bound['exact_necessary_base_interaction_fraction'] = '-1'
    with pytest.raises(ValueError):
        evaluate(wrench, bound)


@pytest.mark.parametrize('lo,hi,status', [('1/2', '1', 'section_only_traction_construction_within_hypothesis'),
                                       ('6/5', '3/2', 'section_only_traction_hypothesis_infeasible'),
                                       ('1/2', '3/2', 'section_only_traction_comparison_unresolved'),
                                       ('1', '100000000000000000001/100000000000000000000',
                                        'section_only_traction_comparison_unresolved')])
def test_exact_sufficient_and_necessary_dispositions_preserve_old_exceedances_and_null_full_resistance(lo, hi, status):
    candidate = {'exact_necessary_base_interaction_fraction': lo,
                 'exact_corrected_field_base_interaction_upper_fraction': hi}
    old = {'scenarios': [{'id': 'own', 'working_reference': True, 'strength_divisor': 1., 'whole_wrench_multiplier': 1.,
                          'construction_status': 'construction_exceeds_reference', 'interaction_upper': 1.51}]}
    result = traction.comparisons(candidate, old)[0]
    assert result['section_only_disposition'] == status
    assert result['old_polynomial_construction_status_preserved'] == 'construction_exceeds_reference'
    assert result['old_polynomial_construction_upper_preserved'] == 1.51
    assert result['complete_cleat_resistance'] is None and result['physical_failure_or_release_established'] is False


def test_unchanged_divisor_and_wrench_magnification_scale_both_exact_bounds():
    candidate = {'exact_necessary_base_interaction_fraction': '1/5',
                 'exact_corrected_field_base_interaction_upper_fraction': '1/4'}
    old = {'scenarios': [{'id': 'own', 'working_reference': False, 'strength_divisor': 3., 'whole_wrench_multiplier': 1.5,
                          'construction_status': 'construction_exceeds_reference', 'interaction_upper': 3.3975}]}
    result = traction.comparisons(candidate, old)[0]
    assert result['exact_necessary_lower_fraction'] == '9/10'
    assert result['exact_corrected_field_upper_fraction'] == '9/8'
    assert result['section_only_disposition'] == 'section_only_traction_comparison_unresolved'


@pytest.mark.parametrize('key,value', [('current_bolt_count', 102), ('current_screw_count', 68), ('extra_grid', True),
                                    ('actual_observations', 'assumed'), ('physical_demand_bounds_established', True),
                                    ('structural_acceptance', True), ('residual_field_interaction_tolerance', .1),
                                    ('bernstein_cell_budget', 1)])
def test_scope_observation_and_enclosure_guards_cannot_be_weakened(key, value):
    data = inputs()
    traction.validate(data)
    data[key] = value
    with pytest.raises(ValueError):
        traction.validate(data)


@pytest.mark.parametrize('module', [traction.dual, traction.previous])
def test_changed_loaded_helper_is_refused_before_a_construction(module, monkeypatch):
    data = inputs()
    traction.validate(data)
    monkeypatch.setattr(module, 'LOADED_SHA', '0'*64)
    with pytest.raises(ValueError):
        traction.validate(data)
