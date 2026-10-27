"""Finite-grid projected-bearing witness with directional and local caps.

This small additive variant reuses the shaft equilibrium and continuous beam
integration in :mod:`scripts.eoere_joint_vector_tests`.  Each cell has a
grain-oriented elliptical projected-bearing cap; a physical receiver's total
force and first moment remain aggregate constraints across all its cells.
The result is a statics/material-reference witness, not contact compatibility
or a complete NDS connection resistance.
"""

from __future__ import annotations

import math
from itertools import pairwise

import numpy as np
from scipy.optimize import linprog

from scripts import eoere_joint_vector_tests as vector


def _pair(value: object, name: str) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    if result.shape != (2,) or not np.isfinite(result).all():
        raise ValueError(f"{name} must be a finite two-vector")
    return result


def _region_map(region: dict) -> np.ndarray:
    grain = _pair(region["grain_parallel"], "grain-parallel direction")
    length = float(np.linalg.norm(grain))
    if not math.isfinite(length) or not math.isclose(length, 1.0, rel_tol=0.0, abs_tol=1e-10):
        raise ValueError("grain-parallel direction must be unit length in the transverse plane")
    cap_parallel = float(region["cap_parallel_n_per_mm"])
    cap_perpendicular = float(region["cap_perpendicular_n_per_mm"])
    if not all(math.isfinite(x) and x > 0 for x in (cap_parallel, cap_perpendicular)):
        raise ValueError("both directional projected-bearing caps must be positive")
    perpendicular = np.array([-grain[1], grain[0]])
    return np.column_stack((grain * cap_parallel, perpendicular * cap_perpendicular))


def _prepare(surfaces: list[dict], points: list[dict], domain: list[float],
             moment_caps: list[dict], cells: int, facets: int):
    if type(cells) is not int or not 2 <= cells <= 128:
        raise ValueError("2..128 cells per receiver required")
    if type(facets) is not int or not 8 <= facets <= 64 or facets % 4:
        raise ValueError("8..64 polygon facets, divisible by four, required")
    low, high = map(float, domain)
    if not (math.isfinite(low) and math.isfinite(high) and high > low):
        raise ValueError("positive finite shaft domain required")
    if len(surfaces) < 2 or not moment_caps:
        raise ValueError("at least two receivers and complete moment caps required")
    if float(moment_caps[0]["interval"][0]) != low or float(moment_caps[-1]["interval"][1]) != high:
        raise ValueError("moment caps must cover the complete shaft domain")
    previous = low
    for cap in moment_caps:
        a, b = map(float, cap["interval"])
        value = float(cap["cap"])
        if a != previous or b <= a or not math.isfinite(value) or value <= 0:
            raise ValueError("positive contiguous moment caps required")
        previous = b

    angles = (2 * np.arange(facets) + 1) * math.pi / facets
    normals = np.column_stack((np.cos(angles), np.sin(angles)))
    polygon_cos = math.cos(math.pi / facets)
    rows: list[dict] = []
    intervals: list[tuple[float, float]] = []
    for surface_index, surface in enumerate(surfaces):
        a, b = map(float, surface["interval"])
        if not (low <= a < b <= high):
            raise ValueError("receiver interval must lie inside the shaft")
        if any(not (b <= c or d <= a) for c, d in intervals):
            raise ValueError("overlapping receiver surfaces refused")
        intervals.append((a, b))
        force = _pair(surface["force"], "receiver force")
        first = _pair(surface["first_moment"], "receiver first moment")
        regions = surface["regions"]
        if not regions:
            raise ValueError("each receiver needs source-bounded cap regions")
        region_cursor = a
        region_intervals = []
        for region in regions:
            r0, r1 = map(float, region["interval"])
            if r0 != region_cursor or r1 <= r0 or r1 > b:
                raise ValueError("cap regions must exactly partition each receiver")
            mapping = _region_map(region)
            region_intervals.append((r0, r1, region, mapping))
            region_cursor = r1
        if region_cursor != b:
            raise ValueError("cap regions must cover the full receiver interval")

        stations = sorted({*np.linspace(a, b, cells + 1),
                           *[v for r0, r1, _, _ in region_intervals for v in (r0, r1)],
                           *[float(v) for cap in moment_caps for v in cap["interval"] if a < v < b]})
        for x, y in pairwise(stations):
            mid = (x + y) / 2.0
            found = [(region, mapping) for r0, r1, region, mapping in region_intervals if r0 <= mid <= r1]
            if len(found) != 1:
                raise ValueError("cell must map to exactly one cap region")
            region, mapping = found[0]
            rows.append({"surface": surface_index, "low": float(x), "high": float(y),
                         "region_id": region["id"], "region": region, "map": mapping,
                         "force": force, "first_moment": first, "midpoint": (a + b) / 2.0})

    total_force = sum((_pair(s["force"], "receiver force") for s in surfaces), np.zeros(2))
    total_force += sum((_pair(p["force"], "point force") for p in points), np.zeros(2))
    if np.linalg.norm(total_force, np.inf) >= 1e-5:
        raise ValueError("prescribed lateral forces do not balance")
    for point in points:
        if not math.isfinite(float(point["s"])):
            raise ValueError("point station must be finite")
        _pair(point["force"], "point force")
        _pair(point["couple"], "point couple")
    return rows, normals, polygon_cos


def solve(surfaces: list[dict], points: list[dict], domain: list[float],
          moment_caps: list[dict], *, cells: int = 16, facets: int = 16) -> dict:
    """Find a finite-grid witness under local directional bearing and moment caps.

    Each region cap is an inscribed-polygon approximation to
    ``(q_parallel/cap_parallel)^2 + (q_perp/cap_perp)^2 <= index^2``.
    ``cap_parallel_n_per_mm`` and ``cap_perpendicular_n_per_mm`` are supplied
    by the caller and must already include any chosen reduction factor.
    """
    rows, normals, polygon_cos = _prepare(surfaces, points, domain, moment_caps, cells, facets)
    low, high = map(float, domain)
    ncell = len(rows)
    lengths = np.asarray([r["high"] - r["low"] for r in rows])
    maps = [r["map"] for r in rows]
    force_scale = float(sum(length * np.linalg.svd(a, compute_uv=False)[0]
                            for length, a in zip(lengths, maps, strict=True)))
    if not math.isfinite(force_scale) or force_scale <= 0:
        raise ValueError("positive force scale required")
    estimates = []
    for surface_index, surface in enumerate(surfaces):
        indices = [i for i, r in enumerate(rows) if r["surface"] == surface_index]
        span = float(surface["interval"][1] - surface["interval"][0])
        capacity = math.fsum(lengths[i] * np.linalg.svd(maps[i], compute_uv=False)[0] for i in indices)
        estimates.append(np.linalg.norm(_pair(surface["force"], "receiver force")) / capacity)
        estimates.append(6.0 * np.linalg.norm(_pair(surface["first_moment"], "receiver first moment"))
                         / (capacity * span))
    min_moment_cap = min(float(c["cap"]) for c in moment_caps)
    shaft_length = high - low
    estimates.extend(
        (np.linalg.norm(_pair(p["force"], "point force")) * shaft_length
         + np.linalg.norm(_pair(p["couple"], "point couple"))) / min_moment_cap
        for p in points
    )
    index_scale = max(*estimates, 1e-15)

    size = 2 * ncell + 1
    eq_rows, eq_rhs = [], []
    for surface_index, surface in enumerate(surfaces):
        span = float(surface["interval"][1] - surface["interval"][0])
        midpoint = sum(surface["interval"]) / 2.0
        for component in range(2):
            row = np.zeros(size)
            for j, cell in enumerate(rows):
                if cell["surface"] == surface_index:
                    row[2*j:2*j+2] = cell["map"][component, :] * lengths[j] / force_scale
            eq_rows.append(row)
            eq_rhs.append(float(surface["force"][component]) / (force_scale * index_scale))
            row = np.zeros(size)
            for j, cell in enumerate(rows):
                if cell["surface"] == surface_index:
                    center = (cell["low"] + cell["high"]) / 2.0
                    row[2*j:2*j+2] = (cell["map"][component, :] * lengths[j]
                                       * (center - midpoint) / (force_scale * span))
            eq_rows.append(row)
            eq_rhs.append(float(surface["first_moment"][component]) / (force_scale * span * index_scale))
    eq, rhs = np.asarray(eq_rows), np.asarray(eq_rhs)

    objective = np.zeros(size)
    objective[-1] = 1.0
    bearing = np.zeros((ncell * len(normals), size))
    for j in range(ncell):
        for k, normal in enumerate(normals):
            bearing[j * len(normals) + k, 2*j:2*j+2] = normal
            bearing[j * len(normals) + k, -1] = -polygon_cos

    nodes = {(float(t), True) for r in rows for t in (r["low"], r["high"])}
    nodes.update((float(v), True) for cap in moment_caps for v in cap["interval"])
    nodes.update((float(p["s"]), include) for p in points if low <= p["s"] <= high
                 for include in (False, True))
    convergence = []
    for round_index in range(64):
        matrices, offsets = [bearing], [np.zeros(len(bearing))]
        for station, include in sorted(nodes):
            moment_cap = vector.cap_at(moment_caps, station)
            weights = np.asarray([
                (max(station - r["low"], 0.0) ** 2 - max(station - r["high"], 0.0) ** 2)
                / (2.0 * moment_cap) for r in rows
            ])
            block = np.zeros((len(normals), size))
            for j, cell in enumerate(rows):
                mapping = cell["map"]
                for k, normal in enumerate(normals):
                    block[k, 2*j:2*j+2] = weights[j] * (
                        normal[1] * mapping[0, :] - normal[0] * mapping[1, :])
                block[:, -1] = -polygon_cos
            matrices.append(block)
            offset = -normals @ vector.point_moment(points, station, include) / (moment_cap * index_scale)
            offsets.append(offset)
        aub, bub = np.vstack(matrices), np.concatenate(offsets)
        result = linprog(objective, A_ub=aub, b_ub=bub, A_eq=eq, b_eq=rhs,
                         bounds=[(None, None)] * (size - 1) + [(0.0, None)], method="highs-ds",
                         options={"primal_feasibility_tolerance": 1e-9,
                                  "dual_feasibility_tolerance": 1e-9, "time_limit": 20.0})
        if result.status != 0 or not result.success:
            raise ValueError(f"projected-bearing LP failed: {result.status}: {result.message}")
        local = result.x[:-1].reshape((-1, 2)) * index_scale
        density = np.asarray([mapping @ z for mapping, z in zip(maps, local, strict=True)])
        raw_index = float(result.fun) * index_scale
        replay_rows = [{"low": r["low"], "high": r["high"]} for r in rows]
        segments, end_force, end_moment = vector.recover(replay_rows, density, points, domain, moment_caps)
        cuts = []
        for segment in segments:
            a, b = segment["interval_mm"]
            cap = vector.cap_at(moment_caps, (a + b) / 2.0)
            segment["raw_moment_cap"] = cap
            segment["raw_index"] = segment["maximum_bending"]["magnitude"] / cap
            if segment["raw_index"] > raw_index * (1.0 + 1e-8) + 1e-10:
                cuts.append((segment["maximum_bending"]["station_mm"], True))
            coeff = np.asarray(segment["moment_coefficients_unit_interval_nmm"], dtype=float)
            if np.linalg.norm(coeff[3]) >= 1e-10:
                raise ValueError("expected quadratic bending over constant cells")
            projected = coeff[:3, 1:] @ normals.T
            for c0, c1, c2 in projected.T:
                if c2 < 0.0:
                    t = -c1 / (2.0 * c2)
                    if 0.0 < t < 1.0 and (c0 + c1*t + c2*t*t) / cap > raw_index * polygon_cos * (1.0 + 1e-8) + 1e-10:
                        cuts.append((a + t * (b - a), True))
        convergence.append({"reference_index": raw_index, "constraints": len(nodes), "new_cuts": len(set(cuts) - nodes)})
        if not cuts:
            break
        if not any(cut not in nodes for cut in cuts):
            raise ValueError("continuous moment cuts made no progress")
        nodes.update(cuts)
    else:
        raise ValueError("continuous moment cutting planes did not converge")

    dual = float(bub @ result.ineqlin.marginals + rhs @ result.eqlin.marginals)
    stationarity = objective - (aub.T @ result.ineqlin.marginals + eq.T @ result.eqlin.marginals
                                + result.lower.marginals + result.upper.marginals)
    lp_certificate = {"equality_residual": float(np.max(np.abs(eq @ result.x - rhs))),
                      "inequality_violation": float(max(0.0, np.max(aub @ result.x - bub))),
                      "dual_stationarity_residual": float(np.max(np.abs(stationarity))),
                      "primal_dual_gap": abs(float(result.fun) - dual),
                      "dual_sign_violation": float(max(0.0, np.max(result.ineqlin.marginals),
                                                        np.max(-result.lower.marginals),
                                                        np.max(result.upper.marginals)))}
    if max(lp_certificate.values()) >= 1e-7:
        raise ValueError("finite-grid LP optimality certificate failed")

    cells_out = []
    ellipse_indices = []
    polygon_indices = []
    for cell, q, z in zip(rows, density, local, strict=True):
        ellipse_index = float(np.linalg.norm(z))
        polygon_index = float(np.max(normals @ z) / polygon_cos)
        ellipse_indices.append(ellipse_index)
        polygon_indices.append(polygon_index)
        cells_out.append({"surface": cell["surface"], "region_id": cell["region_id"],
                          "low": cell["low"], "high": cell["high"],
                          "force_per_length_global": q.tolist(), "ellipse_coordinates": z.tolist(),
                          "cap_parallel_n_per_mm": cell["region"]["cap_parallel_n_per_mm"],
                          "cap_perpendicular_n_per_mm": cell["region"]["cap_perpendicular_n_per_mm"],
                          "ellipse_utilization": ellipse_index, "polygon_utilization": polygon_index})
    bending_index = max(segment["raw_index"] for segment in segments)
    certified = max(raw_index, max(ellipse_indices), bending_index)
    if max(polygon_indices) > raw_index * (1.0 + 2e-7) + 2e-10 or certified > raw_index * (1.0 + 2e-7) + 2e-10:
        raise ValueError("replayed witness exceeds finite-grid LP index")
    return {"LP_reference_index": raw_index, "certified_raw_reference_index": certified,
            "raw_ellipse_bearing_index": max(ellipse_indices),
            "raw_bearing_polygon_index": max(polygon_indices),
            "continuous_raw_bending_index": bending_index,
            "cells_per_receiver": cells, "facets": facets, "cell_count": len(rows),
            "polygon_maximum_radial_conservatism": 1.0 / polygon_cos - 1.0,
            "LP_certificate": lp_certificate, "convergence": convergence,
            "maximum_member_force_error_n": None,
            "maximum_member_first_moment_error_nmm": None,
            "end_force_error_n": float(np.linalg.norm(end_force, np.inf)),
            "end_moment_error_nmm": float(np.linalg.norm(end_moment, np.inf)),
            "cells": cells_out, "continuous_segments": segments,
            "physical_compatibility": False, "adjusted_capacity": None,
            "complete_joint_resistance": None}


def verify_witness(surfaces: list[dict], points: list[dict], domain: list[float],
                   moment_caps: list[dict], result: dict, *, cells: int = 16, facets: int | None = None) -> dict:
    """Independent aggregate-wrench, ellipse and continuous-bending replay."""
    if result.get("physical_compatibility") is not False or result.get("complete_joint_resistance") is not None:
        raise ValueError("projected witness cannot claim physical or complete resistance")
    facets = int(result["facets"] if facets is None else facets)
    rows, normals, polygon_cos = _prepare(surfaces, points, domain, moment_caps, cells, facets)
    saved = result["cells"]
    if len(saved) != len(rows):
        raise ValueError("saved cell count differs from region partition")
    density = []
    ellipse_indices, polygon_indices = [], []
    by_surface: list[list[tuple[dict, np.ndarray]]] = [[] for _ in surfaces]
    for row, cell in zip(rows, saved, strict=True):
        if (cell["surface"] != row["surface"] or cell["region_id"] != row["region_id"]
                or cell["low"] != row["low"] or cell["high"] != row["high"]
                or cell["cap_parallel_n_per_mm"] != row["region"]["cap_parallel_n_per_mm"]
                or cell["cap_perpendicular_n_per_mm"] != row["region"]["cap_perpendicular_n_per_mm"]):
            raise ValueError("cell/source-region join differs")
        q = _pair(cell["force_per_length_global"], "recorded force density")
        z = np.linalg.solve(row["map"], q)
        ellipse = float(np.linalg.norm(z))
        polygon = float(np.max(normals @ z) / polygon_cos)
        if not np.allclose(z, cell["ellipse_coordinates"], rtol=1e-10, atol=1e-10):
            raise ValueError("saved ellipse coordinates differ from physical force density")
        if not math.isclose(ellipse, cell["ellipse_utilization"], rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError("saved ellipse utilization differs")
        if not math.isclose(polygon, cell["polygon_utilization"], rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError("saved polygon utilization differs")
        ellipse_indices.append(ellipse)
        polygon_indices.append(polygon)
        density.append(q)
        by_surface[row["surface"]].append((row, q))

    force_errors, first_errors = [], []
    for i, surface in enumerate(surfaces):
        group = by_surface[i]
        force = np.zeros(2)
        first = np.zeros(2)
        midpoint = sum(surface["interval"]) / 2.0
        for row, q in group:
            length = row["high"] - row["low"]
            center = (row["high"] + row["low"]) / 2.0
            force += q * length
            first += q * length * (center - midpoint)
        force_errors.append(float(np.linalg.norm(force - _pair(surface["force"], "receiver force"), np.inf)))
        first_errors.append(float(np.linalg.norm(first - _pair(surface["first_moment"], "receiver first moment"), np.inf)))

    replay_rows = [{"low": r["low"], "high": r["high"]} for r in rows]
    segments, end_force, end_moment = vector.recover(replay_rows, density, points, domain, moment_caps)
    bending_index = 0.0
    polygon_bending_index = 0.0
    for segment in segments:
        a, b = segment["interval_mm"]
        cap = vector.cap_at(moment_caps, (a + b) / 2.0)
        magnitude = float(segment["maximum_bending"]["magnitude"])
        bending_index = max(bending_index, magnitude / cap)
        coeff = np.asarray(segment["moment_coefficients_unit_interval_nmm"], dtype=float)
        projected = coeff[:3, 1:] @ normals.T
        for c0, c1, c2 in projected.T:
            candidates = [0.0, 1.0]
            if c2 < 0.0:
                t = -c1 / (2.0 * c2)
                if 0.0 < t < 1.0:
                    candidates.append(t)
            polygon_bending_index = max(polygon_bending_index,
                                        max(c0 + c1*t + c2*t*t for t in candidates) / (cap * polygon_cos))
    if max(force_errors, default=0.0) >= 1e-7 or max(first_errors, default=0.0) >= 1e-5:
        raise ValueError("aggregate receiver force/first-moment replay failed")
    if np.linalg.norm(end_force, np.inf) >= 1e-5 or np.linalg.norm(end_moment, np.inf) >= 1e-3:
        raise ValueError("continuous shaft end closure failed")
    if max(ellipse_indices, default=0.0) > result["certified_raw_reference_index"] * (1 + 1e-8) + 1e-10:
        raise ValueError("ellipse bearing witness exceeds recorded reference")
    if max(polygon_indices, default=0.0) > result["LP_reference_index"] * (1 + 2e-7) + 2e-10:
        raise ValueError("cell polygon cap exceeds finite-grid LP index")
    if bending_index > result["certified_raw_reference_index"] * (1 + 1e-8) + 1e-10:
        raise ValueError("continuous bending witness exceeds recorded reference")
    if polygon_bending_index > result["LP_reference_index"] * (1 + 2e-7) + 2e-10:
        raise ValueError("continuous polygon bending exceeds finite-grid LP index")
    return {"maximum_member_force_error_n": max(force_errors, default=0.0),
            "maximum_member_first_moment_error_nmm": max(first_errors, default=0.0),
            "end_force_error_n": float(np.linalg.norm(end_force, np.inf)),
            "end_moment_error_nmm": float(np.linalg.norm(end_moment, np.inf)),
            "maximum_ellipse_index": max(ellipse_indices, default=0.0),
            "maximum_cell_polygon_index": max(polygon_indices, default=0.0),
            "continuous_bending_index": bending_index,
            "continuous_polygon_bending_index": polygon_bending_index,
            "independently_replayed_cells": len(rows),
            "physical_compatibility": False}
