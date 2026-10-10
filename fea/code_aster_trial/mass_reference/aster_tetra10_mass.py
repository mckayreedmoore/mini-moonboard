#!/usr/bin/env python3
"""Independent scalar consistent-mass reference for Code_Aster TETRA10.

The node order and FPG15 constants follow the Code_Aster v17 R3.01.01
volumetric-element reference. Coordinates may use any consistent length unit;
``density`` must then be expressed as mass / length**3. The implementation
integrates the isoparametric quadratic map, including its pointwise curved
Jacobian. FPG15 is the Code_Aster discrete-rule reference, not a claim that a
curved TETRA10 mass integral is continuum-exact.
"""

from __future__ import annotations

from itertools import combinations
import math
from typing import Iterable

import numpy as np


def _fpg15_rule() -> tuple[np.ndarray, np.ndarray]:
    """Return FPG15 abscissae in (x,y,z) and weights on volume 1/6."""
    root15 = math.sqrt(15.0)
    a = 0.25
    b1, c1 = (7.0 + root15) / 34.0, (13.0 - 3.0 * root15) / 34.0
    b2, c2 = (7.0 - root15) / 34.0, (13.0 + 3.0 * root15) / 34.0
    d, e = (5.0 - root15) / 20.0, (5.0 + root15) / 20.0
    bary: list[tuple[tuple[float, float, float, float], float]] = [
        ((a, a, a, a), 8.0 / 405.0),
    ]
    # Four permutations of (b,b,b,c), where c is the distinct coordinate.
    for b, c, w in (
        (b1, c1, (2665.0 - 14.0 * root15) / 226800.0),
        (b2, c2, (2665.0 + 14.0 * root15) / 226800.0),
    ):
        for i in range(4):
            lam = [b, b, b, b]
            lam[i] = c
            bary.append((tuple(lam), w))
    # Six permutations of (d,d,e,e).
    for ix in combinations(range(4), 2):
        lam = [e, e, e, e]
        for i in ix:
            lam[i] = d
        bary.append((tuple(lam), 5.0 / 567.0))

    # Code_Aster's reference coordinates are x=lambda4, y=lambda1,
    # z=lambda2 (lambda3=1-x-y-z).
    points = np.array([(lam[3], lam[0], lam[1]) for lam, _ in bary], dtype=float)
    weights = np.array([w for _, w in bary], dtype=float)
    return points, weights


FPG15_POINTS, FPG15_WEIGHTS = _fpg15_rule()


def _fpg4_rule() -> tuple[np.ndarray, np.ndarray]:
    """Four-point, degree-2 tetra rule, supplied only as a discriminator."""
    lo = (5.0 - math.sqrt(5.0)) / 20.0
    hi = (5.0 + 3.0 * math.sqrt(5.0)) / 20.0
    # One barycentric coordinate hi, remaining three lo.
    pts = []
    for i in range(4):
        lam = [lo] * 4
        lam[i] = hi
        pts.append((lam[3], lam[0], lam[1]))
    return np.asarray(pts), np.full(4, 1.0 / 24.0)


FPG4_POINTS, FPG4_WEIGHTS = _fpg4_rule()


def shape_values_and_gradients(xyz: Iterable[float]) -> tuple[np.ndarray, np.ndarray]:
    """TETRA10 shape values and reference gradients in Code_Aster local order.

    Local nodes are corners 1..4 followed by edge midpoints 12, 23, 31, 14,
    24, 34; this is also Abaqus C3D10 order. The reference barycentric values
    are lambda1=y, lambda2=z, lambda3=1-x-y-z, lambda4=x.
    """
    x, y, z = np.asarray(tuple(xyz), dtype=float)
    lam = np.array((y, z, 1.0 - x - y - z, x), dtype=float)
    dlam = np.array(((0.0, 1.0, 0.0),
                     (0.0, 0.0, 1.0),
                     (-1.0, -1.0, -1.0),
                     (1.0, 0.0, 0.0)), dtype=float)
    n = np.empty(10, dtype=float)
    dn = np.empty((10, 3), dtype=float)
    for i in range(4):
        n[i] = lam[i] * (2.0 * lam[i] - 1.0)
        dn[i] = (4.0 * lam[i] - 1.0) * dlam[i]
    # Edge pairs in Code_Aster/Abaqus TETRA10 order.
    for k, (i, j) in enumerate(((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)), 4):
        n[k] = 4.0 * lam[i] * lam[j]
        dn[k] = 4.0 * (lam[i] * dlam[j] + lam[j] * dlam[i])
    return n, dn


def tetra10_mass_matrix(
    coords: Iterable[Iterable[float]], density: float, rule: str = "fpg15"
) -> np.ndarray:
    """Return the 10x10 scalar nodal mass block for one isoparametric TETRA10.

    The full 30x30 translational matrix is ``kron(M_scalar, I3)`` for a
    constant isotropic density. The Jacobian determinant is evaluated at each
    quadrature point; inverted/degenerate sampled maps are rejected.
    """
    xyz = np.asarray(tuple(tuple(row) for row in coords), dtype=float)
    if xyz.shape != (10, 3) or not np.all(np.isfinite(xyz)):
        raise ValueError("coords must be a finite 10x3 array in TETRA10 local order")
    if not math.isfinite(density) or density < 0.0:
        raise ValueError("density must be finite and nonnegative")
    key = rule.lower()
    if key == "fpg15":
        points, weights = FPG15_POINTS, FPG15_WEIGHTS
    elif key == "fpg4":
        points, weights = FPG4_POINTS, FPG4_WEIGHTS
    else:
        raise ValueError("rule must be 'fpg15' or 'fpg4'")
    mass = np.zeros((10, 10), dtype=float)
    for point, weight in zip(points, weights):
        n, dndref = shape_values_and_gradients(point)
        jac = xyz.T @ dndref
        detj = float(np.linalg.det(jac))
        if not math.isfinite(detj) or detj <= 0.0:
            raise ValueError(f"nonpositive or nonfinite det(J) at {point}: {detj}")
        mass += (density * weight * detj) * np.outer(n, n)
    return mass


def tetra10_mass_matrix_duffy(
    coords: Iterable[Iterable[float]], density: float, order: int = 8
) -> np.ndarray:
    """High-order numerical physical integral, separate from Aster's rule.

    Tensor Gauss-Legendre integration with a Duffy map integrates the complete
    curved isoparametric mass integrand. Since ``N_i*N_j*det(J)`` has total
    degree at most seven, order 6 or higher is exact for constant density:
    after the Duffy map the maximum coordinate degrees are 9, 8, and 7, while
    six-point Gauss-Legendre is exact through degree 11. This is an independent
    physical-integral reference, not the solver's discrete matrix.
    """
    xyz = np.asarray(tuple(tuple(row) for row in coords), dtype=float)
    if xyz.shape != (10, 3) or not np.all(np.isfinite(xyz)):
        raise ValueError("coords must be a finite 10x3 array in TETRA10 local order")
    if not math.isfinite(density) or density < 0.0:
        raise ValueError("density must be finite and nonnegative")
    if not isinstance(order, int) or order < 1:
        raise ValueError("order must be a positive integer")
    abscissa, weights = np.polynomial.legendre.leggauss(order)
    abscissa = 0.5 * (abscissa + 1.0)
    weights = 0.5 * weights
    mass = np.zeros((10, 10), dtype=float)
    for iu, u in enumerate(abscissa):
        for iv, v in enumerate(abscissa):
            for iw, w in enumerate(abscissa):
                # (x,y,z) maps the unit cube to x+y+z<=1; Jacobian is
                # (1-u)^2 (1-v), giving reference volume 1/6.
                point = (u, (1.0 - u) * v, (1.0 - u) * (1.0 - v) * w)
                n, dndref = shape_values_and_gradients(point)
                detj = float(np.linalg.det(xyz.T @ dndref))
                if not math.isfinite(detj) or detj <= 0.0:
                    raise ValueError(f"nonpositive or nonfinite det(J) at {point}: {detj}")
                dvol = (1.0 - u) ** 2 * (1.0 - v)
                mass += (
                    density * weights[iu] * weights[iv] * weights[iw]
                    * dvol * detj * np.outer(n, n)
                )
    return mass


def tetra10_inertia_duffy(
    coords: Iterable[Iterable[float]], density: float,
    pivot: Iterable[float] = (0.0, 0.0, 0.0), order: int = 8,
) -> np.ndarray:
    """Exact-polynomial physical inertia integral for a curved TETRA10 map.

    For constant density, the inertia integrand is also degree at most seven;
    Duffy Gauss-Legendre order 6 or higher integrates it exactly in exact
    arithmetic. Floating point accumulation remains.
    """
    xyz = np.asarray(tuple(tuple(row) for row in coords), dtype=float)
    p = np.asarray(tuple(pivot), dtype=float)
    if xyz.shape != (10, 3) or not np.all(np.isfinite(xyz)):
        raise ValueError("coords must be a finite 10x3 array in TETRA10 local order")
    if p.shape != (3,) or not np.all(np.isfinite(p)):
        raise ValueError("pivot must be a finite 3-vector")
    if not math.isfinite(density) or density < 0.0:
        raise ValueError("density must be finite and nonnegative")
    if not isinstance(order, int) or order < 1:
        raise ValueError("order must be a positive integer")
    abscissa, weights = np.polynomial.legendre.leggauss(order)
    abscissa = 0.5 * (abscissa + 1.0)
    weights = 0.5 * weights
    inertia = np.zeros((3, 3), dtype=float)
    for iu, u in enumerate(abscissa):
        for iv, v in enumerate(abscissa):
            for iw, w in enumerate(abscissa):
                point = (u, (1.0 - u) * v, (1.0 - u) * (1.0 - v) * w)
                shape, dndref = shape_values_and_gradients(point)
                detj = float(np.linalg.det(xyz.T @ dndref))
                if not math.isfinite(detj) or detj <= 0.0:
                    raise ValueError(f"nonpositive or nonfinite det(J) at {point}: {detj}")
                r = shape @ xyz - p
                dvol = (1.0 - u) ** 2 * (1.0 - v)
                inertia += (
                    density * weights[iu] * weights[iv] * weights[iw]
                    * dvol * detj * (float(r @ r) * np.eye(3) - np.outer(r, r))
                )
    return inertia


def fpg15_reference(
    coords: Iterable[Iterable[float]], density: float,
    pivot: Iterable[float] = (0.0, 0.0, 0.0),
) -> dict[str, object]:
    """Compute discrete FPG15 mass, centroid, inertia, and Jacobian diagnostics."""
    xyz = np.asarray(tuple(tuple(row) for row in coords), dtype=float)
    p = np.asarray(tuple(pivot), dtype=float)
    m = tetra10_mass_matrix(xyz, density, "fpg15")
    nsum = m.sum(axis=1)
    total = float(nsum.sum())
    if total <= 0.0:
        raise ValueError("positive total mass is required for centroid/inertia")
    center = nsum @ xyz / total
    inertia = np.zeros((3, 3), dtype=float)
    for point, weight in zip(FPG15_POINTS, FPG15_WEIGHTS):
        shape, dndref = shape_values_and_gradients(point)
        position = shape @ xyz
        detj = float(np.linalg.det(xyz.T @ dndref))
        r = position - p
        inertia += density * weight * detj * (float(r @ r) * np.eye(3) - np.outer(r, r))
    dets = np.array([
        np.linalg.det(xyz.T @ shape_values_and_gradients(q)[1])
        for q in FPG15_POINTS
    ])
    return {
        "mass": total,
        "centroid": center.tolist(),
        "inertia_about_pivot": inertia.tolist(),
        "det_j_min_fpg15": float(dets.min()),
        "det_j_max_fpg15": float(dets.max()),
        "scalar_mass_matrix": m.tolist(),
    }


if __name__ == "__main__":
    # Curved but smoothly perturbed unit tetrahedron used by the Aster native
    # matrix probe. Corners are followed by edge nodes 12,23,31,14,24,34.
    test_coords = np.array([
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
        (0.5, 0.0, 0.035), (0.5, 0.5, -0.020), (0.0, 0.5, 0.015),
        (0.0, 0.0, 0.5), (0.5, 0.0, 0.5), (0.0, 0.5, 0.5),
    ])
    mass15 = tetra10_mass_matrix(test_coords, 7.85e-9, "fpg15")
    mass4 = tetra10_mass_matrix(test_coords, 7.85e-9, "fpg4")
    print("FPG15 sum weights:", FPG15_WEIGHTS.sum())
    print("FPG15 curved volume:", mass15.sum() / 7.85e-9)
    print("FPG15 detJ range:", fpg15_reference(test_coords, 7.85e-9)["det_j_min_fpg15"], fpg15_reference(test_coords, 7.85e-9)["det_j_max_fpg15"])
    print("max abs FPG4-FPG15 scalar-matrix difference:", np.max(np.abs(mass4 - mass15)))
    print("max relative-entry difference:", np.max(np.abs(mass4 - mass15) / np.maximum(np.abs(mass15), 1e-300)))
