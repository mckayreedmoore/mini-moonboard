"""Bound angle-dependent bearing utilization over a whole affine pressure.

The pressure norm is convex, but multiplying it by the Hankinson and Ktheta
terms need not be. Endpoint utilization alone is not a maximum certificate.
Subinterval bounds use a convex norm maximum, an affine cross-norm minimum,
and enclosing grain-angle bounds; branch refinement retains a global upper.
The result is a floating-point engineering enclosure with explicit outward
allowance, not a new material capacity or a complete connection check.
"""

from __future__ import annotations

import heapq
import math

import numpy as np

PSI = .006894757293168361
OUTWARD = 1e-12


def utilization(q, grain, diameter, *, plywood=False):
    q, grain = np.asarray(q, dtype=float), np.asarray(grain, dtype=float)
    norm = float(np.linalg.norm(q))
    if norm == 0:
        return 0.
    cosine = min(1., abs(float(q@grain))/norm)
    theta = math.acos(cosine)
    parallel = 5600.*PSI
    perpendicular = (3150. if plywood else 6100*.5**1.45/math.sqrt(diameter/25.4))*PSI
    inverse = cosine*cosine/parallel + (1-cosine*cosine)/perpendicular
    return norm*inverse*4*(1+theta/(2*math.pi))/diameter


def affine_bearing_upper(first, last, grain, diameter, *, plywood=False,
                         relative_tolerance=1e-8, absolute_tolerance=1e-10, maximum_cells=100000):
    a, b, g = [np.asarray(row, dtype=float) for row in (first, last, grain)]
    if any(row.shape != (3,) or not np.isfinite(row).all() for row in (a, b, g)):
        raise ValueError("three finite pressure and grain components required")
    if not math.isclose(float(g@g), 1., rel_tol=0, abs_tol=1e-8):
        raise ValueError("unit grain direction required")
    if not math.isfinite(diameter) or diameter <= 0:
        raise ValueError("positive finite diameter required")
    if relative_tolerance <= 0 or absolute_tolerance <= 0 or maximum_cells < 1:
        raise ValueError("positive refinement budget and tolerances required")
    g = g/np.linalg.norm(g)
    difference = b-a
    parallel = 5600.*PSI
    perpendicular = (3150. if plywood else 6100*.5**1.45/math.sqrt(diameter/25.4))*PSI

    def pressure(t):
        return a+t*difference

    def point(t):
        return utilization(pressure(t), g, diameter, plywood=plywood)

    def interval(lo, hi):
        first, last = pressure(lo), pressure(hi)
        norm_upper = max(float(np.linalg.norm(first)), float(np.linalg.norm(last)))*(1+OUTWARD)
        if norm_upper == 0:
            return 0.
        # atan2(cross, projection) avoids acos cancellation near parallel
        # grain. Both cross-norm maxima and projection extrema enclose the
        # whole affine interval, independently of where they occur.
        left, right = float(first@g), float(last@g)
        projection_low = 0. if left*right <= 0 else min(abs(left), abs(right))
        projection_high = max(abs(left), abs(right))
        cross_first, cross_last = np.cross(first, g), np.cross(last, g)
        cross_delta = cross_last-cross_first
        cross_denominator = float(cross_delta@cross_delta)
        cross_t = min(1., max(0., -float(cross_first@cross_delta)/cross_denominator)) if cross_denominator else 0.
        cross_low = max(0., float(np.linalg.norm(cross_first+cross_t*cross_delta))*(1-OUTWARD))
        cross_high = max(float(np.linalg.norm(cross_first)), float(np.linalg.norm(cross_last)))*(1+OUTWARD)
        theta_upper = math.atan2(cross_high, projection_low*(1-OUTWARD))
        theta_lower = math.atan2(cross_low, projection_high*(1+OUTWARD))
        cos_low, cos_high = math.cos(theta_upper), math.cos(theta_lower)
        inverse_upper = max(c*c/parallel+(1-c*c)/perpendicular for c in (cos_low, cos_high))
        return math.nextafter(norm_upper*inverse_upper*4*(1+theta_upper/(2*math.pi))/diameter*(1+OUTWARD), math.inf)

    lower = max(point(0.), point(.5), point(1.))
    heap = [(-interval(0., 1.), 0., 1.)]
    refinements = 0
    while -heap[0][0]-lower > max(absolute_tolerance, relative_tolerance*max(lower, 1e-30)):
        if refinements >= maximum_cells:
            raise ValueError("bearing enclosure refinement budget exhausted")
        _, lo, hi = heapq.heappop(heap)
        mid = (lo+hi)/2
        if mid in (lo, hi):
            raise ValueError("bearing enclosure reached floating resolution")
        lower = max(lower, point(mid), point((lo+mid)/2), point((mid+hi)/2))
        heapq.heappush(heap, (-interval(lo, mid), lo, mid))
        heapq.heappush(heap, (-interval(mid, hi), mid, hi))
        refinements += 1
    upper = max(lower, -heap[0][0])
    return {"sampled_lower": lower, "whole_interval_upper": upper,
            "endpoint_maximum": max(point(0.), point(1.)), "refinements": refinements,
            "absolute_gap": upper-lower, "outward_relative_allowance": OUTWARD,
            "relative_tolerance": relative_tolerance, "absolute_tolerance": absolute_tolerance}
