"""Exact bore-wall wrench and stress-trace bounds, without a volume solve.

Select piecewise constant compressive radial pressures. Exact surface integrals
and a certified four-column correction establish a nearby balanced pressure
field. A separate unrestricted full-tensor traction support gives a necessary
bound. Neither result establishes equilibrium inside the timber or contact fit.
"""
from __future__ import annotations

import hashlib
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.linalg import qr
from scipy.optimize import linprog

from scripts import eoere_cleat_virtual_work as volume
from scripts import eoere_recession_certificate as correction
from scripts.eoere_section_patches import dot, rational

require = volume.require
OWN = Path(__file__).resolve()
with OWN.open('rb') as _stream:
    LOADED_SHA = hashlib.file_digest(_stream, 'sha256').hexdigest()


def normal(quarter, half_tangent):
    t = rational(half_tangent)
    require(type(quarter) is int and 0 <= quarter < 4 and 0 <= t <= 1, 'one quarter-circle chart required')
    c, s = (1-t*t)/(1+t*t), 2*t/(1+t*t)
    return ((c, s), (-s, c), (-c, -s), (s, -c))[quarter]


def product_interval(first, second):
    values = [a*b for a in first for b in second]
    return min(values), max(values)


def scale_interval(interval, value):
    return tuple(sorted(value*x for x in interval))


def sum_intervals(*intervals):
    return tuple(sum((item[i] for item in intervals), F(0)) for i in (0, 1))


def grid(radius, interval, angular_divisions, axial_divisions, strengths=volume.BASE_STRENGTHS):
    radius = rational(radius)
    low, high = map(rational, interval)
    strengths = {key: rational(value) for key, value in strengths.items()}
    require(radius > 0 and low < high and type(angular_divisions) is type(axial_divisions) is int
            and 1 <= angular_divisions <= 128 and 2 <= axial_divisions <= 128, 'positive bore and bounded complete pressure grid required')
    require(set(strengths) == set(volume.BASE_STRENGTHS) and min(strengths.values()) > 0, 'complete positive tensor strengths required')
    angles = []
    for quarter in range(4):
        for index in range(angular_divisions):
            a, b = F(index, angular_divisions), F(index+1, angular_divisions)
            first, last = normal(quarter, a), normal(quarter, b)
            c, s = [tuple(sorted((first[i], last[i]))) for i in (0, 1)]
            mc, ms = max(map(abs, c)), max(map(abs, s))
            gauge = mc*mc/strengths['compression_parallel']+ms*ms/strengths['compression_perpendicular']+mc*ms/strengths['parallel_shear']
            angles.append({'quarter': quarter, 'half_tangent': (a, b), 'normal_bounds': (c, s),
                'normal_integral': (last[1]-first[1], first[0]-last[0]), 'uniaxial_gauge_upper': gauge,
                'arc_angle_upper': 2*(b-a)/(1+a*a)})
    axial = [(low+(high-low)*F(i, axial_divisions), low+(high-low)*F(i+1, axial_divisions)) for i in range(axial_divisions)]
    columns, gauges = [], []
    for angle in angles:
        for a, b in axial:
            first, second = (radius*(b-a)*value for value in angle['normal_integral'])
            middle = (a+b)/2
            columns.append((first, second, middle*second, -middle*first))
            gauges.append(angle['uniaxial_gauge_upper'])
    require(all(sum(column[i] for column in columns) == 0 for i in range(4)), 'uniform full-ring pressure must have exactly zero wrench')
    return {'radius': radius, 'interval': (low, high), 'angles': angles, 'axial': axial,
            'columns': columns, 'gauges': gauges, 'strengths': strengths}


def matrix(data):
    return [list(row) for row in zip(*data['columns'], strict=True)]


def select(wrench, data):
    wrench = tuple(map(rational, wrench))
    require(len(wrench) == 4 and any(wrench), 'nonzero transverse force and first-moment wrench required')
    exact = matrix(data)
    a = np.asarray(exact, dtype=float)
    scales = np.maximum(np.max(abs(a), axis=1), 1.)
    n = a.shape[1]
    inequalities = sparse.hstack([sparse.diags(list(map(float, data['gauges']))), -np.ones((n, 1))], format='csr')
    result = linprog(np.r_[np.zeros(n), 1.], A_eq=np.c_[a/scales[:, None], np.zeros(4)],
        b_eq=np.asarray(wrench, dtype=float)/scales, A_ub=inequalities, b_ub=np.zeros(n),
        bounds=(0, None), method='highs-ds',
        options={'primal_feasibility_tolerance': 1e-9, 'dual_feasibility_tolerance': 1e-9})
    require(result.success and np.isfinite(result.x).all(), 'LP did not select a finite pressure witness; no failure follows')
    return {'pressures_mpa': result.x[:-1].tolist(), 'dual_multiplier': (result.eqlin.marginals/scales).tolist(),
            'LP_index': float(result.fun), 'LP_is_not_a_certificate': True}


def certify(wrench, data, pressures):
    wrench, pressures = tuple(map(rational, wrench)), tuple(map(rational, pressures))
    require(len(wrench) == 4 and len(pressures) == len(data['columns']) and min(pressures) >= 0,
            'complete nonnegative pressure witness required')
    rows = matrix(data)
    recovered = [dot(row, pressures) for row in rows]
    residual = [a-b for a, b in zip(wrench, recovered, strict=True)]
    error, selected, rank = F(0), [], None
    if any(residual):
        positive = [i for i, value in enumerate(pressures) if value > 0]
        require(len(positive) >= 4, 'insufficient positive pressures for a certified balance correction')
        _, _, order = qr(np.asarray([[float(row[j]) for j in positive] for row in rows]), mode='economic', pivoting=True)
        selected = [positive[int(i)] for i in order[:4]]
        minor = [{j: row[k] for j, k in enumerate(selected)} for row in rows]
        rank = correction.inverse_bound(minor)
        error = F(rank['exact_inverse_norm_upper'])*max(map(abs, residual))
        require(min(pressures[j] for j in selected) > error, 'nonnegative nearby exact pressure field not certified')
    upper = max((value+(error if i in selected else 0))*gauge
                for i, (value, gauge) in enumerate(zip(pressures, data['gauges'], strict=True)))
    return {'exact_target_wrench': list(map(str, wrench)), 'exact_candidate_wrench': list(map(str, recovered)),
            'exact_residual': list(map(str, residual)), 'selected_correction_columns': selected, 'rank_certificate': rank,
            'exact_selected_pressure_correction_upper_mpa': str(error),
            'exact_minimum_selected_pressure_margin_mpa': str(min(pressures[j] for j in selected)-error) if selected else None,
            'exact_construction_upper': str(upper), 'construction_upper': float(upper),
            'nearby_exact_nonnegative_pressure_field_exists': True, 'volume_stress_field_established': False}


def strain_work_bounds(multiplier, radius, normal_bounds, axial_interval):
    """Six coefficients of sigma:(v tensor nu), retaining shear symmetry."""
    lf, vf, lm, vm = map(rational, multiplier)
    c, s = normal_bounds
    vu = scale_interval(sum_intervals(scale_interval(c, vm), scale_interval(s, -lm)), radius)
    vl = sum_intervals((lf, lf), scale_interval(axial_interval, -vm))
    vv = sum_intervals((vf, vf), scale_interval(axial_interval, lm))
    nl, nv = scale_interval(c, -1), scale_interval(s, -1)
    return [product_interval(vl, nl), (F(0), F(0)), product_interval(vv, nv),
            product_interval(vu, nl), sum_intervals(product_interval(vl, nv), product_interval(vv, nl)),
            product_interval(vu, nv)]


def support_density_upper(strain, strengths):
    bounds = [F(0)]
    for value, ft, fc in zip(strain[:3],
            (strengths['tension_parallel'], strengths['tension_perpendicular'], strengths['tension_perpendicular']),
            (strengths['compression_parallel'], strengths['compression_perpendicular'], strengths['compression_perpendicular']), strict=True):
        bounds.extend((ft*value[1], -fc*value[0]))
    bounds.extend(strength*max(map(abs, value)) for value, strength in zip(strain[3:],
        (strengths['parallel_shear'], strengths['parallel_shear'], strengths['rolling_shear']), strict=True))
    return max(bounds)


def support_upper(multiplier, data):
    """Outer interval integral for unrestricted full-tensor boundary tractions.

    v=lambda_F+lambda_M cross r. The wood outward normal is minus the radial
    normal. Each continuous full-tensor support is enclosed before integration;
    no pressure-only, friction or axial-traction restriction enters this bound.
    """
    radius, strengths = data['radius'], data['strengths']
    contributions = []
    for angle in data['angles']:
        total = F(0)
        for a, b in data['axial']:
            strain = strain_work_bounds(multiplier, radius, angle['normal_bounds'], (a, b))
            total += radius*(b-a)*angle['arc_angle_upper']*support_density_upper(strain, strengths)
        contributions.append(total)
    require(sum(contributions) > 0, 'nonzero continuous surface support required')
    return sum(contributions), contributions


def necessary(multiplier, wrench, data):
    multiplier, wrench = tuple(map(rational, multiplier)), tuple(map(rational, wrench))
    require(len(multiplier) == len(wrench) == 4, 'complete transverse wrench and multiplier required')
    work = dot(multiplier, wrench)
    if work < 0:
        multiplier, work = tuple(-v for v in multiplier), -work
    upper, contributions = support_upper(multiplier, data)
    lower = work/upper
    return {'exact_multiplier': list(map(str, multiplier)), 'exact_work': str(work),
            'exact_full_tensor_surface_support_upper': str(upper), 'exact_angle_band_support_uppers': list(map(str, contributions)),
            'exact_necessary_lower': str(lower), 'necessary_lower': float(lower),
            'radial_pressure_or_friction_restriction_used': False}
