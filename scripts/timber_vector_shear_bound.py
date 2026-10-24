"""A convex vector upper bound for the existing rectangular-ligament model.

The direct shear vector lies in a component box. Saint-Venant rectangle
torsion lies in both its component box and its maximum-shear disk. Maximize
their vector sum over that larger, independent set. This bounds every point,
including the interior; it is not a selection of face probes. It establishes
no local loaded-hole, wood splitting or complete-joint qualification.

For a rectangle the torsion stress function is constant on the perimeter.
Each derivative is harmonic, and its squared gradient is subharmonic, so the
stress magnitude reaches its maximum on the boundary. There it has one
component; the classical midface coefficients bound the components and norm.
The issued rectangle series supplies those coefficients and its J tail.

The bound is a supremum of norms of linear functions of Vu, Vv and T over a
fixed symmetric set. It is convex, so the existing cubic Bernstein controls
continue to bound each whole fixed-action interval. No strength or load
factor is changed.
"""

from __future__ import annotations

import math


def box_disk_sum_upper(direct_u, direct_v, torsion_u, torsion_v, radius):
    """Exact nonnegative box/disk relaxation, rounded slightly outward."""
    values = tuple(float(v) for v in (direct_u, direct_v, torsion_u, torsion_v, radius))
    if not all(math.isfinite(v) and v >= 0 for v in values):
        raise ValueError("finite nonnegative shear bounds required")
    du, dv, a, b, radius = values
    a, b = min(a, radius), min(b, radius)
    if radius == 0 or math.hypot(a, b) <= radius:
        result = math.hypot(du + a, dv + b)
    else:
        # The remaining feasible Pareto frontier is the circle arc inside
        # the box. Its maximum aligns with D, or with the nearest arc end.
        lo = math.acos(min(1., a / radius))
        hi = math.asin(min(1., b / radius))
        angle = min(hi, max(lo, math.atan2(dv, du)))
        result = math.hypot(du + radius * math.cos(angle), dv + radius * math.sin(angle))
    return math.nextafter(result * (1. + 1e-14), math.inf) if result else 0.


def region_bound(region, fv):
    """Retain the whole signed regional wrench and issued common-twist model."""
    fv = float(fv)
    if not math.isfinite(fv) or fv <= 0:
        raise ValueError("positive finite shear reference required")
    area = float(region["area_mm2"])
    if not math.isfinite(area) or area <= 0:
        raise ValueError("positive finite regional area required")
    wrench = tuple(float(v) for v in region["wrench_at_regional_centroid_n_nmm"])
    if len(wrench) != 6 or not all(math.isfinite(v) for v in wrench):
        raise ValueError("complete finite six-component regional wrench required")
    torsion = region["rectangle_torsion"]
    j, tail = float(torsion["J_mm4"]), float(torsion["J_series_absolute_tail_bound_mm4"])
    if not math.isfinite(j) or not math.isfinite(tail) or not 0 <= tail < j:
        raise ValueError("positive series lower bound for J required")
    coefficients = tuple(float(v) for v in torsion["face_shear_coefficients_u_v_per_mm3"])
    if len(coefficients) != 2 or not all(math.isfinite(v) and v >= 0 for v in coefficients):
        raise ValueError("two finite nonnegative rectangle component coefficients required")
    # The finite J sum is high. Its explicit omitted positive tail lowers J;
    # finite subtracted sech numerators are already upper estimates.
    upper = tuple(c * j / (j - tail) for c in coefficients)
    direct = (1.5 * abs(wrench[1]) / area, 1.5 * abs(wrench[2]) / area)
    component = tuple(abs(wrench[3]) * c for c in upper)
    radius = max(component)
    bound = box_disk_sum_upper(*direct, *component, radius)
    return {"vector_shear_torsion_upper_mpa": bound, "upper_index": bound / fv,
            "direct_component_bounds_mpa": list(direct),
            "torsion_component_bounds_mpa": list(component), "torsion_norm_bound_mpa": radius,
            "separate_peak_sum_with_same_tail_mpa": math.hypot(*direct) + radius,
            "J_tail_multiplier": j / (j - tail)}


def section_upper(comparison, fv):
    return max(region_bound(region, fv)["upper_index"] for region in comparison["regions"])
