"""Linear lateral bolt/wood-foundation coupon, not a calibrated joint model.

Euler-Bernoulli bolt with three contiguous, independently moving bearing regions.
Each region has transverse translation and rotation about its own midpoint.
No axial behavior, clearance, yielding, friction, contact opening or strength.
"""
from itertools import pairwise

import numpy as np


def stiffness(lengths_mm, foundation_n_per_mm2, bending_n_mm2, subdivisions=8):
    """Condense bolt DOFs; return 6x6 member stiffness and recovery matrices.

Member DOFs alternate [translation mm, rotation rad]. Work-conjugate forces
are [N, N mm]. Foundation input is distributed stiffness, NOT NDS bearing
strength or a point spring stiffness. Bolt EI is explicitly supplied.
"""
    lengths = np.asarray(lengths_mm, dtype=float)
    foundation = np.asarray(foundation_n_per_mm2, dtype=float)
    if (lengths.shape != (3,) or foundation.shape != (3,)
            or not np.isfinite(lengths).all() or not (lengths > 0).all()
            or not np.isfinite(foundation).all() or not (foundation > 0).all()
            or not np.isfinite(bending_n_mm2) or bending_n_mm2 <= 0
            or isinstance(subdivisions, bool) or not isinstance(subdivisions, int)
            or not 1 <= subdivisions <= 64):
        raise ValueError("Require three positive finite lengths/foundations, EI>0 and 1..64 subdivisions")
    boundaries = np.r_[0., np.cumsum(lengths)]
    centres = (boundaries[:-1]+boundaries[1:])/2
    x = np.r_[0., np.concatenate([np.linspace(a, b, subdivisions+1)[1:]
                                 for a, b in pairwise(boundaries)])]
    bolt_dofs = 2*len(x)
    matrix = np.zeros((bolt_dofs+6, bolt_dofs+6))
    gauss, weights = np.polynomial.legendre.leggauss(4)
    for element, (start, end) in enumerate(pairwise(x)):
        length = end-start
        member = element//subdivisions
        ids = np.arange(2*element, 2*element+4)
        beam = bending_n_mm2/length**3*np.array([
            [12, 6*length, -12, 6*length],
            [6*length, 4*length**2, -6*length, 2*length**2],
            [-12, -6*length, 12, -6*length],
            [6*length, 2*length**2, -6*length, 4*length**2]])
        matrix[np.ix_(ids, ids)] += beam
        for point, weight in zip(gauss, weights, strict=True):
            t = (point+1)/2
            shape = np.array([1-3*t*t+2*t**3, length*(t-2*t*t+t**3),
                              3*t*t-2*t**3, length*(-t*t+t**3)])
            slip = np.zeros(bolt_dofs+6)
            slip[ids] = shape
            slip[bolt_dofs+2*member] = -1
            slip[bolt_dofs+2*member+1] = -(start+t*length-centres[member])
            matrix += foundation[member]*weight*length/2*np.outer(slip, slip)
    a, b = matrix[:bolt_dofs, :bolt_dofs], matrix[:bolt_dofs, bolt_dofs:]
    recovery = -np.linalg.solve(a, b)
    condensed = matrix[bolt_dofs:, bolt_dofs:]+b.T@recovery
    if not np.isfinite(condensed).all() or not np.isfinite(recovery).all():
        raise ValueError("Nonfinite connector solution")
    return {"member_stiffness": condensed, "bolt_recovery": recovery,
            "full_stiffness": matrix, "bolt_x_mm": x, "member_centres_mm": centres}
