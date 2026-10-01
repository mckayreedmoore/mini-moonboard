"""Generic response for an idealized, uniformly pressured clamped annulus.

This module implements only the classical, linear, isotropic thin-plate case
with uniform pressure over the full annular area and perfect clamping at both
radial edges. It does not model a washer assembly or contact.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

_MINIMUM_OUTER_TO_INNER_RADIUS_RATIO = 1.02


@dataclass(frozen=True)
class AnnularPlateResponse:
    """Point response in a consistent force-length unit system.

    ``deflection`` has units of length. ``radial_slope`` is ``dw/dr`` and is
    dimensionless. Positive pressure and deflection point in the same
    transverse direction; positive slope means positive deflection increases
    with increasing radius.
    """

    deflection: float
    radial_slope: float


def uniform_pressure_clamped_annulus(
    *,
    inner_radius: float,
    outer_radius: float,
    flexural_rigidity: float,
    pressure: float,
    radius: float,
) -> AnnularPlateResponse:
    """Return deflection and radial slope for the clamped-annulus benchmark.

    All lengths must use the same unit. ``flexural_rigidity`` is
    ``D = E h^3 / [12 (1 - nu^2)]`` in force·length units, and ``pressure``
    uses force/length². The model is linear elastic, isotropic, thin-plate,
    axisymmetric, constant-thickness, and loaded by uniform pressure across
    the entire annulus. Both edges are ideally clamped.

    The result uses positive deflection in the direction of positive pressure.
    ``radius`` must lie in the closed interval from the inner to outer edge.
    In double precision, this implementation fails closed when
    ``outer_radius / inner_radius < 1.02`` because the closed-form constants
    become cancellation-sensitive for thinner annuli. This lower cutoff is a
    numerical limit, not a physical plate limit.
    """

    inner = _finite_number(inner_radius, "inner_radius")
    outer = _finite_number(outer_radius, "outer_radius")
    rigidity = _finite_number(flexural_rigidity, "flexural_rigidity")
    load = _finite_number(pressure, "pressure")
    station = _finite_number(radius, "radius")

    if inner <= 0.0:
        raise ValueError("inner_radius must be positive")
    if outer <= inner:
        raise ValueError("outer_radius must be greater than inner_radius")
    if rigidity <= 0.0:
        raise ValueError("flexural_rigidity must be positive")
    if not inner <= station <= outer:
        raise ValueError("radius must lie between the annular edges")

    ratio = outer / inner
    xi = station / inner
    if not math.isfinite(ratio) or not math.isfinite(xi):
        raise ValueError("radius ratios must be finite")
    if ratio < _MINIMUM_OUTER_TO_INNER_RADIUS_RATIO:
        raise ValueError("outer_radius / inner_radius must be at least 1.02")
    if load == 0.0:
        return AnnularPlateResponse(deflection=0.0, radial_slope=0.0)

    try:
        coefficients = _clamped_coefficients(ratio)
        w_dimensionless, slope_dimensionless = _dimensionless_response(
            xi, coefficients
        )
        deflection = (load * inner**4 / rigidity) * w_dimensionless
        radial_slope = (load * inner**3 / rigidity) * slope_dimensionless
    except OverflowError as error:
        raise ValueError("input magnitudes exceed finite plate-response range") from error

    if not math.isfinite(deflection) or not math.isfinite(radial_slope):
        raise ValueError("input magnitudes exceed finite plate-response range")
    return AnnularPlateResponse(deflection=deflection, radial_slope=radial_slope)


def _finite_number(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite real number")
    try:
        converted = float(value)
    except (OverflowError, ValueError) as error:
        raise ValueError(f"{name} must be a finite real number") from error
    if not math.isfinite(converted):
        raise ValueError(f"{name} must be a finite real number")
    return converted


def _clamped_coefficients(outer_to_inner_ratio: float) -> tuple[float, ...]:
    """Solve the source's four normalized clamped-edge equations."""
    k = outer_to_inner_ratio
    log_k = math.log(k)
    try:
        k2 = k * k
        k3 = k2 * k
        k4 = k2 * k2
    except OverflowError as error:
        raise ValueError("radius ratio exceeds finite plate-response range") from error
    if not all(math.isfinite(value) for value in (k2, k3, k4)):
        raise ValueError("radius ratio exceeds finite plate-response range")

    # For W(xi)=A ln(xi)+B xi²+C xi² ln(xi)+F+xi⁴/64,
    # impose W=W'=0 at xi=1 and xi=k. The right-hand side is the
    # particular solution's value and derivative moved to the other side.
    matrix = [
        [0.0, 1.0, 0.0, 1.0],
        [1.0, 2.0, 1.0, 0.0],
        [log_k, k2, k2 * log_k, 1.0],
        [1.0 / k, 2.0 * k, k * (2.0 * log_k + 1.0), 0.0],
    ]
    rhs = [-1.0 / 64.0, -1.0 / 16.0, -k4 / 64.0, -k3 / 16.0]
    return _solve_four_by_four(matrix, rhs)


def _solve_four_by_four(
    matrix: list[list[float]], rhs: list[float]
) -> tuple[float, float, float, float]:
    augmented = [row[:] + [right] for row, right in zip(matrix, rhs, strict=True)]
    for column in range(4):
        pivot_row = max(range(column, 4), key=lambda row: abs(augmented[row][column]))
        pivot = augmented[pivot_row][column]
        if pivot == 0.0 or not math.isfinite(pivot):
            raise ValueError("annular boundary equations are numerically singular")
        augmented[column], augmented[pivot_row] = augmented[pivot_row], augmented[column]
        pivot = augmented[column][column]
        augmented[column] = [value / pivot for value in augmented[column]]
        for row in range(4):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                current - factor * pivot_value
                for current, pivot_value in zip(
                    augmented[row], augmented[column], strict=True
                )
            ]
    answer = tuple(augmented[row][4] for row in range(4))
    if not all(math.isfinite(value) for value in answer):
        raise ValueError("annular boundary equations are numerically singular")
    return answer[0], answer[1], answer[2], answer[3]


def _dimensionless_response(
    xi: float, coefficients: tuple[float, ...]
) -> tuple[float, float]:
    a, b, c, f = coefficients
    log_xi = math.log(xi)
    xi2 = xi * xi
    xi3 = xi2 * xi
    xi4 = xi2 * xi2
    response = a * log_xi + b * xi2 + c * xi2 * log_xi + f + xi4 / 64.0
    slope = a / xi + 2.0 * b * xi + c * xi * (2.0 * log_xi + 1.0) + xi3 / 16.0
    if not math.isfinite(response) or not math.isfinite(slope):
        raise ValueError("input magnitudes exceed finite plate-response range")
    return response, slope
