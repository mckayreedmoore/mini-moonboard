"""Independent mechanics identities and numerical-enclosure controls."""
import cmath
import itertools
import math
from fractions import Fraction as F

import numpy as np
import pytest
from numpy.polynomial.legendre import leggauss

from scripts import eoere_curved_bend_field as field


@pytest.mark.parametrize('slot', range(6))
def test_exact_body_free_complete_wrench(slot):
    values = [F(i+2) for i in range(6)]
    values[slot] *= -1
    a, t, w, c, s = F(3), F(2), F(8), F(3, 5), F(4, 5)
    force, moment = [F(0)]*3, [F(0)]*3
    for i, j in itertools.product(range(3), repeat=2):
        r, z = a+t*i/2, w*(j-1)/2
        _, tt, _, rt, _, tz = field.body_free(r, z, c, s, a=a, t=t, w=w,
                                            force=values[:3], moment=values[3:])
        traction, point = [rt*c-tt*s, rt*s+tt*c, tz], [r*c, r*s, z]
        weight = t*w*F((1, 4, 1)[i]*(1, 4, 1)[j], 36)
        for k in range(3):
            force[k] += weight*traction[k]
            moment[k] += weight*(point[(k+1)%3]*traction[(k+2)%3]-point[(k+2)%3]*traction[(k+1)%3])
    assert force == values[:3] and moment == values[3:]


@pytest.mark.parametrize('density', [(1, 0, 0), (0, -1, 0), (0, 0, 1), (2, -3, 5)])
def test_exact_gravity_free_sides(density):
    a, t, w, theta, c, s = F(2), F(3), F(4), F(1, 3), F(3, 5), F(4, 5)
    for r, z in itertools.product((a, a+t), (-w/2, F(0), w/2)):
        stress = field.gravity(r, z, theta, c, s, a=a, t=t, w=w, density=density)
        assert stress[0] == stress[3] == stress[4] == 0
    for r, z in itertools.product((a+t/4, a+3*t/4), (-w/2, w/2)):
        stress = field.gravity(r, z, theta, c, s, a=a, t=t, w=w, density=density)
        assert stress[2] == stress[4] == stress[5] == 0


@pytest.mark.parametrize('density', [(1., 0., 0.), (0., -1., 0.), (0., 0., 1.), (2., -3., 5.)])
def test_gravity_divergence_and_complete_end_wrench(density):
    a, t, w = 6.35, 6.35, 88.9
    params = {'a': a, 't': t, 'w': w, 'density': density}
    for theta, r, z in itertools.product((0., .31, math.pi/2), (a+t/4, a+3*t/4), (-w/4, w/4)):
        c, s, step = math.cos(theta), math.sin(theta), 1e-24
        stress = field.gravity(r, z, theta, c, s, **params)
        dr = [v.imag/step for v in field.gravity(r+step*1j, z, theta, c, s, **params)]
        dz = [v.imag/step for v in field.gravity(r, z+step*1j, theta, c, s, **params)]
        angle = theta+step*1j
        dt = [v.imag/step for v in field.gravity(r, z, angle, cmath.cos(angle), cmath.sin(angle), **params)]
        rr, tt, _, rt, rz, _ = stress
        gr, gt = density[0]*c+density[1]*s, -density[0]*s+density[1]*c
        assert max(map(abs, (dr[0]+dt[3]/r+dz[4]+(rr-tt)/r+gr,
                            dr[3]+dt[1]/r+dz[5]+2*rt/r+gt,
                            dr[4]+dt[5]/r+dz[2]+rz/r+density[2]))) < 1e-10
    nodes, weights = leggauss(64)
    axial, axial_weights = leggauss(5)
    r, z = a+t*(nodes[:, None]+1)/2, w*axial[None, :]/2
    for theta in (0., .31, math.pi/2):
        c, s = math.cos(theta), math.sin(theta)
        _rr, tt, _zz, rt, _rz, tz = np.broadcast_arrays(*field.gravity(r, z, theta, c, s, **params))
        traction = np.stack((rt*c-tt*s, rt*s+tt*c, tz), axis=-1)
        points = np.stack(np.broadcast_arrays(r*c, r*s, z), axis=-1)
        measures = (weights[:, None]*axial_weights[None, :]*t*w/4)[:, :, None]
        force = (traction*measures).sum(axis=(0, 1))
        moment = (np.cross(points, traction)*measures).sum(axis=(0, 1))
        r1, r2 = ((a+t)**2-a*a)/2, ((a+t)**3-a**3)/3
        expected_f = -w*r1*theta*np.array(density)
        expected_m = w*r2*np.array((density[2]*c, density[2]*s, -density[0]*c-density[1]*s))
        assert max(abs(force-expected_f)) < 1e-8
        assert max(abs(moment-expected_m)) < 1e-7


def test_interval_arithmetic_contains_exact_rational_operations():
    intervals = [field.Interval(-3., -1.), field.Interval(-2., 4.), field.Interval(.125, 2.)]
    for first, second in itertools.product(intervals, repeat=2):
        for x, y in itertools.product((first.low, (first.low+first.high)/2, first.high),
                                      (second.low, (second.low+second.high)/2, second.high)):
            for actual, expected in ((first+second, F(x)+F(y)), (first-second, F(x)-F(y)),
                                     (first*second, F(x)*F(y))):
                assert F(actual.low) <= expected <= F(actual.high)
            if not second.low <= 0 <= second.high:
                actual = first/second
                assert F(actual.low) <= F(x)/F(y) <= F(actual.high)
        for power in (0, 1, 2, 3, 4):
            result = first**power
            for x in (first.low, (first.low+first.high)/2, first.high):
                assert F(result.low) <= F(x)**power <= F(result.high)
    with pytest.raises(ValueError, match='zero'):
        _ = intervals[0]/intervals[1]


@pytest.mark.parametrize('q', [0., .25, .5, .5001, .75, 1.])
def test_rational_half_angle_and_alternating_remainder(q):
    theta, c, s = field.angle_at(q)
    assert theta.low-1e-15 <= 2*math.atan(q) <= theta.high+1e-15
    assert c.low-1e-15 <= (1-q*q)/(1+q*q) <= c.high+1e-15
    assert s.low-1e-15 <= 2*q/(1+q*q) <= s.high+1e-15
    small = F.from_float(q)/2
    lo, hi = field.atan_series(small)
    inner_lo, inner_hi = field.atan_series(small, 64)
    assert lo <= inner_lo <= inner_hi <= hi


def test_machin_identity_uses_exact_rational_tangents():
    tangent = F(1, 5)
    for _ in range(2):
        tangent = 2*tangent/(1-tangent*tangent)
    assert (tangent-F(1, 239))/(1+tangent*F(1, 239)) == 1
    lo, hi = field.pi_bounds()
    assert 3 < lo <= hi < 4 and hi-lo < F(1, 10**40)


def test_whole_body_certificate_and_budget_failure_are_distinct():
    params = {'a': 6.35, 't': 6.35, 'w': 88.9, 'force': [100., -200., 50.],
              'moment': [2000., -3000., 1000.], 'density': [0., 0., -.0001]}
    result = field.enclose(params)
    assert result['all_material_boxes_covered'] and result['remaining_boxes'] == 0
    assert result['covering_upper_index_squared'] < 1
    for r, z, theta in itertools.product((6.35, 9.525, 12.7), (-44.45, 0., 44.45), (0., .7, math.pi/2)):
        stress = field.total_stress(r, z, theta, math.cos(theta), math.sin(theta), params)
        assert field.equivalent_squared(stress)*(1.67/235)**2 <= result['covering_upper_index_squared']
    params['force'] = [1e9, 0., 0.]
    result = field.enclose(params, cell_budget=1)
    assert result['status'] == 'INTERVAL_BUDGET_INCONCLUSIVE'
    assert not result['all_material_boxes_covered'] and result['remaining_boxes'] > 0
    assert result['covering_upper_index_squared'] is None


@pytest.mark.parametrize('changes', [{'a': 0.}, {'density': [1., 2.]}, {'w': math.nan}])
def test_invalid_physical_or_vector_inputs_are_rejected(changes):
    params = {'a': 6.35, 't': 6.35, 'w': 88.9, 'force': [0.]*3, 'moment': [0.]*3, 'density': [0.]*3}
    params.update(changes)
    with pytest.raises((ValueError, OverflowError)):
        field.enclose(params)
