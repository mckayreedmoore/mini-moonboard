"""Analytic ring, wrench, full-tensor support and correction controls."""
from fractions import Fraction as F

import pytest

from scripts import eoere_bore_boundary_tractions as bore


@pytest.mark.parametrize('quarter', range(4))
def test_rational_circle_is_unit_and_joins_its_neighbor(quarter):
    for t in (F(0), F(1, 7), F(2, 3), F(1)):
        n = bore.normal(quarter, t)
        assert bore.dot(n, n) == 1
    assert bore.normal(quarter, 1) == bore.normal((quarter+1) % 4, 0)


@pytest.mark.parametrize('quarter,t', [(-1, 0), (4, 0), (0, -.1), (0, 1.1), (True, 0)])
def test_invalid_circle_charts_refuse(quarter, t):
    with pytest.raises(ValueError):
        bore.normal(quarter, t)


def test_exact_ring_force_integral_and_axial_first_moment_signs():
    data = bore.grid(2, (-2, 2), 1, 2)
    # First quadrant: integral (cos,sin)dtheta=(1,1), first width bin [-2,0].
    assert data['columns'][0] == (4, 4, -4, 4)
    assert data['columns'][1] == (4, 4, 4, -4)
    assert all(sum(column[i] for column in data['columns']) == 0 for i in range(4))


def test_uniaxial_stress_trace_gauge_encloses_the_complete_angular_interval():
    data = bore.grid(1, (-1, 1), 3, 2)
    strengths = data['strengths']
    for angle in data['angles']:
        a, b = angle['half_tangent']
        for t in (a, (2*a+b)/3, (a+b)/2, b):
            c, s = bore.normal(angle['quarter'], t)
            exact = c*c/strengths['compression_parallel']+s*s/strengths['compression_perpendicular']+abs(c*s)/strengths['parallel_shear']
            assert 0 < exact <= angle['uniaxial_gauge_upper']


def test_binary_strength_inputs_are_converted_before_exact_bounds():
    strengths = {key: float(value) for key, value in bore.volume.BASE_STRENGTHS.items()}
    data = bore.grid(1, (-1, 1), 1, 2, strengths)
    assert all(isinstance(value, F) for value in data['strengths'].values())
    assert data['strengths']['parallel_shear'] == F.from_float(2.144)
    assert all(isinstance(value, F) for value in data['gauges'])


@pytest.mark.parametrize('first,second,expected', [
    ((-2, 3), (-5, 7), (-15, 21)), ((-3, -1), (2, 4), (-12, -2)), ((0, 0), (-5, 9), (0, 0)),
])
def test_signed_interval_products(first, second, expected):
    assert bore.product_interval(first, second) == expected


def test_positive_exact_pressure_field_recovers_all_four_resultants_without_repair():
    data = bore.grid(F(3, 2), (-2, 3), 2, 3)
    pressures = [F(i+1, 32) for i in range(len(data['columns']))]
    target = [bore.dot(row, pressures) for row in bore.matrix(data)]
    proof = bore.certify(target, data, pressures)
    assert proof['exact_residual'] == ['0']*4
    assert proof['selected_correction_columns'] == []
    assert F(proof['exact_construction_upper']) == max(p*g for p, g in zip(pressures, data['gauges'], strict=True))


def test_exact_neumann_repair_is_confined_to_positive_pressure_columns():
    data = bore.grid(1, (-1, 1), 2, 2)
    pressures = [F(1, 8)]*len(data['columns'])
    target = [value*F(1, 2**90) for value in data['columns'][0]]
    proof = bore.certify(target, data, pressures)
    assert len(proof['selected_correction_columns']) == 4
    assert proof['rank_certificate']['full_rank_proven'] is True
    assert F(proof['exact_selected_pressure_correction_upper_mpa']) > 0
    assert F(proof['exact_minimum_selected_pressure_margin_mpa']) > 0
    assert proof['nearby_exact_nonnegative_pressure_field_exists'] is True
    assert proof['volume_stress_field_established'] is False


def test_negative_or_rank_deficient_pressure_corrections_refuse():
    data = bore.grid(1, (-1, 1), 1, 2)
    pressures = [F(0)]*len(data['columns'])
    pressures[0] = -F(1, 2**150)
    with pytest.raises(ValueError, match='nonnegative'):
        bore.certify([1, 0, 0, 0], data, pressures)
    with pytest.raises(ValueError, match='insufficient positive'):
        bore.certify([1, 0, 0, 0], data, [0]*len(pressures))


def test_tiny_generic_lp_selection_is_independently_certified():
    data = bore.grid(1, (-2, 2), 2, 4)
    pressures = [F((i*7) % 11+1, 16) for i in range(len(data['columns']))]
    target = [bore.dot(row, pressures) for row in bore.matrix(data)]
    chosen = bore.select(target, data)
    proof = bore.certify(target, data, chosen['pressures_mpa'])
    lower = bore.necessary(chosen['dual_multiplier'], target, data)
    assert 0 < F(lower['exact_necessary_lower']) <= F(proof['exact_construction_upper'])
    assert chosen['LP_is_not_a_certificate'] is True
    assert lower['radial_pressure_or_friction_restriction_used'] is False


def test_unrestricted_surface_support_encloses_the_known_isotropic_ring_integral():
    strengths = {key: F(1) for key in bore.volume.BASE_STRENGTHS}
    coarse = bore.grid(1, (-1, 1), 4, 2, strengths)
    fine = bore.grid(1, (-1, 1), 32, 2, strengths)
    upper, bands = bore.support_upper([1, 0, 0, 0], fine)
    old, _ = bore.support_upper([1, 0, 0, 0], coarse)
    # Integral over width 2 is 2*int_0^(2pi) max(|cos|,|sin|)dtheta=8*sqrt(2).
    assert sum(bands) == upper and 128 <= upper*upper < 150
    assert upper < old


def test_full_tensor_support_retains_axial_boundary_tractions_in_moment_capacity():
    data = bore.grid(1, (-1, 1), 4, 2)
    larger = dict(data, strengths={**data['strengths'], 'rolling_shear': F(10000)})
    first, _ = bore.support_upper([0, 0, 1, 0], data)
    second, _ = bore.support_upper([0, 0, 1, 0], larger)
    assert second > first


def direct_traction_work(multiplier, radius, n, axial, stress):
    """Independent Cauchy traction and 3-vector virtual-power oracle."""
    r = [radius*n[0], axial, radius*n[1]]
    force = [multiplier[0], F(0), multiplier[1]]
    moment = [multiplier[2], F(0), multiplier[3]]
    cross = [moment[1]*r[2]-moment[2]*r[1], moment[2]*r[0]-moment[0]*r[2], moment[0]*r[1]-moment[1]*r[0]]
    velocity = [force[i]+cross[i] for i in range(3)]
    nu = [-n[0], F(0), -n[1]]
    ll, uu, vv, lu, lv, uv = stress
    sigma = [[ll, lu, lv], [lu, uu, uv], [lv, uv, vv]]
    traction = [sum(row[i]*nu[i] for i in range(3)) for row in sigma]
    return sum(velocity[i]*traction[i] for i in range(3))


@pytest.mark.parametrize('quarter', range(4))
@pytest.mark.parametrize('axial', [F(-2, 3), F(4, 5)])
def test_mixed_force_moment_coefficients_match_independent_cauchy_traction_work(quarter, axial):
    multiplier, radius = [F(2), F(-3), F(5), F(-7)], F(17, 9)
    n = bore.normal(quarter, F(1, 3))
    exact = bore.strain_work_bounds(multiplier, radius, [(v, v) for v in n], (axial, axial))
    assert all(a == b for a, b in exact)
    stresses = [[F(i == j) for i in range(6)] for j in range(6)]+[[F(2, 3), F(-3, 5), F(5, 7), F(7, 11), F(-11, 13), F(13, 17)]]
    for stress in stresses:
        assert sum(value[0]*s for value, s in zip(exact, stress, strict=True)) == direct_traction_work(multiplier, radius, n, axial, stress)


def test_mixed_wrench_cell_support_encloses_every_asymmetric_tensor_vertex():
    data = bore.grid(F(17, 9), (F(-7, 3), F(11, 5)), 2, 3)
    multiplier = [F(2), F(-3), F(5), F(-7)]
    vertices = []
    # Independent declared C16 stress-domain vertices in LL,UU,VV,LU,LV,UV.
    for axis, values in enumerate([(F(17, 2), F(-17)), (F(2, 5), F(-11, 5)), (F(2, 5), F(-11, 5)),
                                  (F(268, 125), F(-268, 125)), (F(268, 125), F(-268, 125)), (F(4, 5), F(-4, 5))]):
        for value in values:
            vertex = [F(0)]*6; vertex[axis] = value; vertices.append(vertex)
    for angle in data['angles']:
        left, right = angle['half_tangent']
        for interval in data['axial']:
            strain = bore.strain_work_bounds(multiplier, data['radius'], angle['normal_bounds'], interval)
            upper = bore.support_density_upper(strain, data['strengths'])
            for t in (left, (left+right)/2, right):
                n = bore.normal(angle['quarter'], t)
                assert 2/(1+t*t) <= angle['arc_angle_upper']/(right-left)
                for axial in (*interval, sum(interval)/2):
                    assert max(direct_traction_work(multiplier, data['radius'], n, axial, stress) for stress in vertices) <= upper


@pytest.mark.parametrize('radius,interval,angles,axial', [(0, (-1, 1), 2, 2), (1, (1, 1), 2, 2), (1, (-1, 1), 0, 2), (1, (-1, 1), 2, 1)])
def test_invalid_pressure_domains_refuse(radius, interval, angles, axial):
    with pytest.raises(ValueError):
        bore.grid(radius, interval, angles, axial)
