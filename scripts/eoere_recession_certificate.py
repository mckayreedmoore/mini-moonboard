"""Exact strict-dual certificates for a declared convex spring recession cone.

For rigid coordinates r, bilateral A*r=0 and one-sided C*r<=0 describe
directions with no quadratic energy growth. A full-row-rank D=[A.T,C.T]
and p=D*x with strictly positive one-sided x imply p.r<0 on every nonzero
such direction. With a PSD elastic core whose kernel is exactly the declared
rigid space, the complete nonnegative spring potential minus load work is
coercive. This conditional theorem does not calibrate stiffness or contact.

LP/QR/inversion only select witnesses. Exact binary-value arithmetic and a
Neumann inverse bound certify a nearby strictly positive exact witness.
"""
from __future__ import annotations

import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.linalg import qr
from scipy.optimize import linprog

OWN = Path(__file__).resolve()
with OWN.open('rb') as _source:
    LOADED_SHA = hashlib.file_digest(_source, 'sha256').hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def rational(value):
    if isinstance(value, F):
        return value
    if isinstance(value, (float, np.floating)):
        require(math.isfinite(value), 'finite binary value required')
        return F.from_float(float(value))
    return F(value)


def normalized_rows(rows, columns):
    require(type(columns) is int and columns > 0 and rows, 'nonempty finite matrix dimensions required')
    result = []
    for row in rows:
        require(all(type(k) is int and 0 <= k < columns for k in row), 'exact matrix column indices required')
        result.append({k: rational(v) for k, v in row.items() if rational(v)})
    return result


def dense_float(rows, columns):
    result = np.zeros((len(rows), columns))
    for i, row in enumerate(rows):
        for j, value in row.items():
            result[i, j] = float(value)
    require(np.isfinite(result).all(), 'finite floating witness-selection matrix required')
    return result


def matrix_digest(rows):
    data = [[(j, str(v)) for j, v in sorted(row.items())] for row in rows]
    return hashlib.sha256(json.dumps(data, separators=(',', ':')).encode()).hexdigest()


def minor(rows, selected):
    require(len(selected) == len(rows) and len(set(selected)) == len(selected), 'square distinct column minor required')
    lookup = {k: i for i, k in enumerate(selected)}
    return [{lookup[k]: v for k, v in row.items() if k in lookup} for row in rows]


def inverse_bound(rows, approximate_inverse=None):
    """Certify ||M^-1||inf via exact ||I-M*R||inf<1, retaining every term.

    Common denominators convert both matrices into integer arrays. Integer
    matrix products and row sums are exact; no BLAS error estimate is used.
    """
    n = len(rows)
    rows = normalized_rows(rows, n)
    inverse = np.linalg.inv(dense_float(rows, n)) if approximate_inverse is None else np.asarray(approximate_inverse, dtype=float)
    require(inverse.shape == (n, n) and np.isfinite(inverse).all(), 'finite square approximate inverse required')
    fractions = [[rational(v) for v in row] for row in inverse]
    md = math.lcm(*(v.denominator for row in rows for v in row.values()))
    rd = math.lcm(*(v.denominator for row in fractions for v in row))
    integers = np.asarray([[v.numerator*(rd//v.denominator) for v in row] for row in fractions], dtype=object)
    denominator, error_numerator = md*rd, 0
    for i, row in enumerate(rows):
        value = np.zeros(n, dtype=object)
        for j, coefficient in row.items():
            value += coefficient.numerator*(md//coefficient.denominator)*integers[j]
        value[i] -= denominator
        error_numerator = max(error_numerator, sum(abs(v) for v in value))
    error = F(error_numerator, denominator)
    require(error < 1, 'approximate inverse does not certify nonsingularity')
    norm = F(max(sum(abs(v) for v in row) for row in integers), rd)
    bound = norm/(1-error)
    return {'exact_inverse_residual_inf': str(error), 'exact_approximate_inverse_inf': str(norm),
            'exact_inverse_norm_upper': str(bound), 'inverse_norm_upper': float(bound),
            'approximate_inverse_binary64_sha256': hashlib.sha256(np.ascontiguousarray(inverse).tobytes()).hexdigest(),
            'full_rank_proven': True, 'minor_dimension': n, 'exact_minor_sha256': matrix_digest(rows)}


def certify(rows, columns, bilateral_count, load, candidate, selected, rank_proof):
    rows = normalized_rows(rows, columns)
    require(type(bilateral_count) is int and 0 <= bilateral_count < columns
            and len(load) == len(rows) and len(candidate) == columns, 'complete load and mixed-domain witness required')
    require(rank_proof['full_rank_proven'] is True and rank_proof['minor_dimension'] == len(rows)
            and len(selected) == len(rows) and len(set(selected)) == len(rows)
            and all(type(i) is int and 0 <= i < columns for i in selected), 'matching square rank certificate required')
    require(rank_proof['exact_minor_sha256'] == matrix_digest(minor(rows, selected)), 'rank certificate belongs to another matrix')
    x, p = tuple(map(rational, candidate)), tuple(map(rational, load))
    residual = tuple(value-sum((coefficient*x[j] for j, coefficient in row.items()), F(0))
                     for value, row in zip(p, rows, strict=True))
    rnorm = max(map(abs, residual))
    correction = F(rank_proof['exact_inverse_norm_upper'])*rnorm
    minimum = min(x[bilateral_count:])
    margin = minimum-correction
    require(minimum > 0 and margin > 0, 'strict one-sided exact witness not certified')
    return {'exact_candidate_balance_residual_inf': str(rnorm), 'exact_selected_correction_inf_upper': str(correction),
            'exact_minimum_candidate_one_sided_weight': str(minimum), 'exact_strict_weight_margin_lower': str(margin),
            'strict_weight_margin_lower': float(margin), 'exact_balanced_strict_dual_exists': True,
            'candidate_weights_binary64_sha256': hashlib.sha256(np.asarray(candidate, dtype='<f8').tobytes()).hexdigest()}


def select_witness(rows, columns, bilateral_count, load, minimum_weight=F(1, 1000), *, rank_proof=None, selected=None):
    """Select a static auxiliary witness; this is neither response nor forces."""
    rows = normalized_rows(rows, columns)
    minimum_weight = rational(minimum_weight)
    require(type(bilateral_count) is int and 0 <= bilateral_count < columns and minimum_weight > 0
            and len(load) == len(rows), 'positive static selection controls required')
    matrix = dense_float(rows, columns)
    objective = np.r_[np.zeros(bilateral_count), np.ones(columns-bilateral_count)]
    bounds = [(None, None)]*bilateral_count+[(float(minimum_weight), None)]*(columns-bilateral_count)
    candidate = linprog(objective, A_eq=matrix, b_eq=np.asarray(list(map(float, load))), bounds=bounds, method='highs-ds')
    require(candidate.success, 'LP did not select a strict witness; this is not a nonexistence certificate')
    if rank_proof is None:
        require(selected is None, 'unbound column selection cannot reuse a rank proof')
        selected = list(map(int, qr(matrix, mode='economic', pivoting=True)[2][:len(rows)]))
        rank_proof = inverse_bound(minor(rows, selected))
    else:
        require(selected is not None, 'reused rank proof needs its exact column selection')
    proof = certify(rows, columns, bilateral_count, load, candidate.x, selected, rank_proof)
    return {'selected_minor_columns': selected, 'rank_certificate': rank_proof,
            'candidate_auxiliary_weights': candidate.x.tolist(), 'load_certificate': proof}
