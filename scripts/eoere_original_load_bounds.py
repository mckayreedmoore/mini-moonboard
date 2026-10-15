"""Exact-load dual-gap bounds for the certified fixed-reference comparator.

An LP selects nearby auxiliary spring weights, not a response. The frozen
minor certificate bounds an exact balance correction. A rigid-orthogonal
elastic residual is carried by the certified positive free/free blocks.
Fenchel gaps and weighted linear functionals then bound every equilibrium
reaction in a declared stiffness family. All proof arithmetic is rational,
with outward integer square-root enclosures. No physical extrema follow.
"""
from __future__ import annotations

import hashlib
import math
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, eye, hstack, vstack

from scripts import eoere_elastic_core_certificate as core

exact = core.exact
require, rational = exact.require, exact.rational
OWN = Path(__file__).resolve()
with OWN.open('rb') as _source:
    LOADED_SHA = hashlib.file_digest(_source, 'sha256').hexdigest()


def root_bounds(square, digits=24):
    square = rational(square)
    require(square >= 0 and type(digits) is int and 1 <= digits <= 40, 'nonnegative square and bounded root precision required')
    scale = 10**digits
    lower = math.isqrt(square.numerator*scale**2//square.denominator)
    upper = lower if lower**2*square.denominator == square.numerator*scale**2 else lower+1
    return F(lower, scale), F(upper, scale)


def upper(value, digits=24):
    """Outward rational rounding prevents denominator growth in long sums."""
    value = rational(value)
    require(value >= 0 and type(digits) is int and 1 <= digits <= 40, 'nonnegative upper bound and bounded precision required')
    scale = 10**digits
    return F(-(-value.numerator*scale//value.denominator), scale)


def family(alpha, beta):
    alpha, beta = rational(alpha), rational(beta)
    require(0 < alpha <= 1 <= beta, 'positive stiffness interval containing the reference required')
    return alpha, beta, max((alpha-1)**2/alpha, (beta-1)**2/beta)


def elastic_gap(twice_energy, residual_complementary_square, alpha, beta):
    """Half (sqrt(eta*q.K0.q)+sqrt(h.K0^+h/alpha)) squared."""
    a2, b2 = rational(twice_energy), rational(residual_complementary_square)
    require(a2 >= 0 and b2 >= 0, 'nonnegative primal and complementary squares required')
    alpha, _, eta = family(alpha, beta)
    return (eta*a2+b2/alpha)/2+root_bounds(eta*a2*b2/alpha)[1]


def spring_gap(displacement, candidate, radius, stiffness, alpha, beta, *, positive=False, clearance=0):
    d, x, r = [list(map(rational, values)) for values in (displacement, candidate, radius)]
    k, clearance = rational(stiffness), rational(clearance)
    alpha, beta, _ = family(alpha, beta)
    require(len(d) == len(x) == len(r) and len(d) in (1, 2) and k > 0 and min(r) >= 0 and clearance >= 0,
            'complete positive spring law and correction box required')
    if positive:
        require(len(d) == 1 and clearance == 0 and x[0]-r[0] >= 0, 'one-sided conjugate domain required')
        travel = max(d[0], 0)
    else:
        travel = max(root_bounds(sum(value*value for value in d))[1]-clearance, 0)
    square = sum((abs(value)+error)**2 for value, error in zip(x, r, strict=True))
    minimum_work = sum((value*movement-error*abs(movement) for value, error, movement in zip(x, r, d, strict=True)), F(0))
    constant = clearance*root_bounds(square)[1]-minimum_work
    gap = max(multiplier*k*travel**2/2+square/(2*multiplier*k) for multiplier in (alpha, beta))+constant
    require(gap >= 0, 'invalid negative Fenchel-gap upper bound')
    return gap


def functional(rows, candidate, radius, maximum_stiffness, gap):
    """Bound C*r_eq using its weighted Gram and a dual correction box."""
    n = len(candidate)
    rows = exact.normalized_rows(rows, n)
    x, r, k = [list(map(rational, values)) for values in (candidate, radius, maximum_stiffness)]
    gap = rational(gap)
    require(len(r) == len(k) == n and min(r) >= 0 and min(k) > 0 and gap >= 0,
            'complete positive reaction metric and nonnegative gap required')
    center = core.action(rows, x)
    correction_square = sum(sum((abs(value)*r[j] for j, value in row.items()), F(0))**2 for row in rows)
    gram = [[sum((value*k[j]*other.get(j, 0) for j, value in row.items()), F(0)) for other in rows] for row in rows]
    spectral_upper = max(sum(map(abs, row), F(0)) for row in gram)
    correction = root_bounds(correction_square)[1]
    equilibrium = root_bounds(2*gap*spectral_upper)[1]
    norm = root_bounds(sum(value*value for value in center))[1]+correction+equilibrium
    return {'exact_candidate_center': list(map(str, center)), 'exact_dual_correction_norm_upper': str(correction),
        'exact_equilibrium_change_norm_upper': str(equilibrium), 'exact_weighted_Gram_spectral_upper': str(spectral_upper),
        'exact_norm_upper': str(norm), 'norm_upper': float(norm),
        'exact_scalar_lower': str(center[0]-correction-equilibrium) if len(rows) == 1 else None}


def nearby_witness(rows, columns, bilateral, load, reference, stiffness, selected, rank_proof, minimum=F(1, 100000)):
    """Select a nearby static dual witness; exact correction supplies proof."""
    rows = exact.normalized_rows(rows, columns)
    reference, stiffness = list(map(rational, reference)), list(map(rational, stiffness))
    minimum = rational(minimum)
    require(len(reference) == len(stiffness) == columns and min(stiffness) > 0 and minimum > 0,
            'complete reference spring weights, positive stiffness and selection scale required')
    matrix = csr_matrix(exact.dense_float(rows, columns))
    old_projection = core.action(rows, reference)
    right = np.asarray([float((rational(p)-old)/minimum) for p, old in zip(load, old_projection, strict=True)])
    weights = 1/np.sqrt(np.asarray(list(map(float, stiffness))))
    identity = eye(columns, format='csr')
    inequalities = vstack([hstack([identity, -identity]), hstack([-identity, -identity])], format='csr')
    bounds = [(None, None)]*bilateral+[(float((minimum-value)/minimum), None) for value in reference[bilateral:]]+[(0., None)]*columns
    result = linprog(np.r_[np.zeros(columns), weights], A_eq=hstack([matrix, csr_matrix(matrix.shape)], format='csr'),
        b_eq=right, A_ub=inequalities, b_ub=np.zeros(2*columns), bounds=bounds, method='highs-ds',
        options={'primal_feasibility_tolerance': 1e-9, 'dual_feasibility_tolerance': 1e-9})
    require(result.success, 'nearby static witness selection failed; no response/nonexistence conclusion follows')
    candidate = np.asarray(list(map(float, reference)))+float(minimum)*result.x[:columns]
    proof = exact.certify(rows, columns, bilateral, load, candidate, selected, rank_proof)
    correction = F(proof['exact_selected_correction_inf_upper'])
    selected_set = set(selected)
    return {'candidate_auxiliary_weights': candidate.tolist(), 'load_certificate': proof,
            'component_correction_radius': [correction if j in selected_set else F(0) for j in range(columns)]}
