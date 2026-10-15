"""Exact local elastic-core certificates, without a response calculation.

The saved symmetric energy matrix need not annihilate its registered rigid
map exactly. Keep that matrix immutable. For datum rows with invertible R_d,
z=q_f-R_f*R_d^-1*q_d defines an explicit comparator E0=z.T*G*z/2, where G
is the saved symmetric free/free block. A verified positive G makes E0 PSD
with exactly the registered rigid kernel. This is a declared mathematical
idealization, not a stiffness calibration or a new admitted response.

A shifted approximate Cholesky factor selects a witness. Exact integer
products verify lambda_min(G) >= shift-||G-shift*I-L*L.T||inf > 0.
"""
from __future__ import annotations

import hashlib
import math
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.linalg import qr

from scripts import eoere_recession_certificate as exact

OWN = Path(__file__).resolve()
with OWN.open('rb') as _source:
    LOADED_SHA = hashlib.file_digest(_source, 'sha256').hexdigest()
require, rational = exact.require, exact.rational


def transpose(rows, columns):
    out = [{} for _ in range(columns)]
    for i, row in enumerate(rows):
        for j, value in row.items():
            if value:
                out[j][i] = value
    return out


def norm_inf(rows):
    return max((sum(map(abs, row.values()), F(0)) for row in rows), default=F(0))


def symmetrize(rows):
    n = len(rows)
    rows = exact.normalized_rows(rows, n)
    transposed = transpose(rows, n)
    symmetric, skew = [], []
    for row, other in zip(rows, transposed, strict=True):
        keys = row.keys() | other.keys()
        symmetric.append({j: (row.get(j, 0)+other.get(j, 0))/2 for j in keys
                          if row.get(j, 0)+other.get(j, 0)})
        skew.append({j: (row.get(j, 0)-other.get(j, 0))/2 for j in keys
                     if row.get(j, 0)-other.get(j, 0)})
    return symmetric, skew


def product(left, right):
    """Exact sparse row product; never drop a small coefficient."""
    out = []
    for row in left:
        result = {}
        for k, value in row.items():
            for j, coefficient in right[k].items():
                result[j] = result.get(j, F(0))+value*coefficient
        out.append({j: value for j, value in result.items() if value})
    return out


def action(rows, vector):
    return [sum((value*rational(vector[j]) for j, value in row.items()), F(0)) for row in rows]


def exact_inverse(rows):
    """Small datum-coordinate inverse, with exact Gauss-Jordan elimination."""
    n = len(rows)
    rows = exact.normalized_rows(rows, n)
    a = [[row.get(j, F(0)) for j in range(n)]+[F(i == j) for j in range(n)]
         for i, row in enumerate(rows)]
    for j in range(n):
        pivot = next((i for i in range(j, n) if a[i][j]), None)
        require(pivot is not None, 'registered datum rigid map is singular')
        a[j], a[pivot] = a[pivot], a[j]
        divisor = a[j][j]
        a[j] = [v/divisor for v in a[j]]
        for i in range(n):
            if i != j and a[i][j]:
                multiplier = a[i][j]
                a[i] = [v-multiplier*w for v, w in zip(a[i], a[j], strict=True)]
    result = [{j: v for j, v in enumerate(row[n:]) if v} for row in a]
    require(product(rows, result) == [{i: F(1)} for i in range(n)], 'exact datum inverse identity failed')
    return result


def shifted_cholesky(rows, *, shift=None, factor=None):
    """Return a rigorous lower eigenvalue bound, not a floating SPD verdict."""
    n = len(rows)
    rows = exact.normalized_rows(rows, n)
    require(rows == transpose(rows, n), 'exact symmetric free/free energy matrix required')
    floating = exact.dense_float(rows, n)
    if shift is None:
        minimum = float(np.linalg.eigvalsh(floating)[0])
        require(minimum > 0 and math.isfinite(minimum), 'no positive shift selected; no indefiniteness conclusion follows')
        shift = rational(float(minimum/2))
    else:
        shift = rational(shift)
    require(shift > 0, 'positive verification shift required')
    if factor is None:
        factor = np.linalg.cholesky(floating-float(shift)*np.eye(n))
    factor = np.asarray(factor, dtype=float)
    require(factor.shape == (n, n) and np.isfinite(factor).all(), 'finite square witness factor required')
    fractions = [[rational(value) for value in row] for row in factor]
    denominator = math.lcm(*(value.denominator for row in fractions for value in row))
    integers = np.asarray([[v.numerator*(denominator//v.denominator) for v in row] for row in fractions], dtype=object)
    gram = integers @ integers.T
    squared = denominator**2
    residual = F(0)
    for i, row in enumerate(rows):
        residual = max(residual, sum((abs(row.get(j, F(0))-(shift if i == j else 0)-F(gram[i, j], squared))
                                      for j in range(n)), F(0)))
    lower = shift-residual
    require(lower > 0, 'exact shifted residual does not prove positive definiteness')
    return {'dimension': n, 'exact_matrix_sha256': exact.matrix_digest(rows), 'positive_definite_proven': True,
            'exact_verification_shift': str(shift), 'exact_factor_residual_inf': str(residual),
            'exact_smallest_eigenvalue_lower': str(lower), 'smallest_eigenvalue_lower': float(lower),
            'approximate_factor_binary64_sha256': hashlib.sha256(np.ascontiguousarray(factor).tobytes()).hexdigest()}


def rigid_negative_work(rows, rigid):
    """A negative exact quadratic is a matrix-arithmetic witness, not failure."""
    r = max((j for row in rigid for j in row), default=-1)+1
    gram = product(transpose(rigid, r), product(rows, rigid))
    values, vectors = np.linalg.eigh(exact.dense_float(gram, r))
    if values[0] >= 0:
        return None
    coefficients = list(map(rational, vectors[:, 0]))
    vector = action(rigid, coefficients)
    work = sum((v*w for v, w in zip(vector, action(rows, vector), strict=True)), F(0))
    if work >= 0:
        return None
    return {'exact_rigid_coefficients': list(map(str, coefficients)), 'exact_quadratic_work': str(work),
            'quadratic_work': float(work), 'source_energy_matrix_not_PSD_proven': True}


def certify_core(rows, rigid, *, datum=None):
    """Certify the comparator and quantify its exact local matrix difference."""
    n = len(rows)
    rows = exact.normalized_rows(rows, n)
    rigid = exact.normalized_rows(rigid, max((j for row in rigid for j in row), default=-1)+1)
    r = max(j for row in rigid for j in row)+1
    require(len(rigid) == n and 0 < r < n, 'complete lower-dimensional registered rigid map required')
    symmetric, skew = symmetrize(rows)
    if datum is None:
        datum = list(map(int, qr(exact.dense_float(rigid, r).T, mode='economic', pivoting=True)[2][:r]))
    require(len(datum) == r and len(set(datum)) == r
            and all(type(i) is int and 0 <= i < n for i in datum), 'distinct complete datum row selection required')
    inverse = exact_inverse([rigid[i] for i in datum])
    free = [i for i in range(n) if i not in datum]
    lookup = {j: i for i, j in enumerate(free)}
    quotient = [{lookup[j]: value for j, value in symmetric[i].items() if j in lookup} for i in free]
    positive = shifted_cholesky(quotient)
    kr = product(symmetric, rigid)
    # S has identity datum rows. P=S*E_d.T, K0=(I-P).T*Ksym*(I-P).
    # Ksym-K0 = Y*E_d.T + E_d*Y.T - E_d*(S.T*Y)*E_d.T, Y=Ksym*S.
    interpolation = product(rigid, inverse)
    require([interpolation[i] for i in datum] == [{j: F(1)} for j in range(r)], 'datum interpolation identity failed')
    y = product(kr, inverse)
    h = product(transpose(interpolation, r), y)
    delta = [{} for _ in rows]
    for i in free:
        for j, value in y[i].items():
            if value:
                delta[i][datum[j]] = value
                delta[datum[j]][i] = value
    for i, di in enumerate(datum):
        for j, dj in enumerate(datum):
            value = y[di].get(j, F(0))+y[dj].get(i, F(0))-h[i].get(j, F(0))
            if value:
                delta[di][dj] = value
    require(delta == transpose(delta, n), 'completion difference must be exactly symmetric')
    norm, change = norm_inf(symmetric), norm_inf(delta)
    nonzero = [(abs(value), i, j, value) for i, row in enumerate(kr) for j, value in row.items()]
    maximum = max(nonzero, default=(F(0), None, None, F(0)))
    negative = rigid_negative_work(symmetric, rigid)
    record = {'coordinates': n, 'registered_rigid_dimension': r, 'datum_local_coordinates': datum,
        'free_coordinate_count': len(free), 'exact_saved_matrix_sha256': exact.matrix_digest(rows),
        'exact_symmetric_energy_matrix_sha256': exact.matrix_digest(symmetric),
        'exact_registered_rigid_basis_sha256': exact.matrix_digest(rigid),
        'exact_datum_inverse_sha256': exact.matrix_digest(inverse), 'datum_rank_proven': True,
        'quotient_positive_certificate': positive, 'constructed_core_PSD_and_exact_registered_kernel_proven': True,
        'source_symmetric_matrix_annihilates_registered_rigid_basis': not nonzero,
        'nonzero_KR_entry_count': len(nonzero), 'exact_maximum_abs_KR_entry': str(maximum[0]),
        'maximum_KR_witness': {'local_row': maximum[1], 'rigid_column': maximum[2], 'exact_value': str(maximum[3])},
        'negative_rigid_quadratic_witness': negative,
        'literal_saved_energy_matrix_core_hypothesis_proven': not nonzero,
        'exact_saved_energy_matrix_inf': str(norm), 'exact_comparator_difference_inf': str(change),
        'exact_relative_comparator_difference_inf': str(change/norm) if norm else None,
        'relative_comparator_difference_inf': float(change/norm) if norm else None,
        'exact_comparator_difference_sha256': exact.matrix_digest(delta), 'exact_saved_skew_part_inf': str(norm_inf(skew))}
    return record, delta, skew
