"""Representative vector bearing/bending tests under explicit raw references.

The fixed member forces and couples are preserved. An inscribed polygon
bounds both transverse components together; continuous bolt-moment extrema
are checked with the existing spatial integrator. This is a statics witness,
not a physical pressure law, adjusted design value or complete joint capacity.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import platform
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from scripts import eoere_mixed_stack_yield as spatial

current = spatial.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
HISTORY = current.DOC / "bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1"
HISTORICAL_INPUTS = {"path": str((HISTORY / "inputs.json").relative_to(current.ROOT)),
                     "sha256": "bab3f6c7d57c34e6b208c0d78462a7f5c18bf3f59111b67f659fe7f3084044a2"}
HISTORICAL_RESULT = {"path": str((HISTORY / "result.json").relative_to(current.ROOT)),
                     "sha256": "14a9633f8cc97b9179c9c42aee3b88a28ed4b35c434f9c2625bf06cc1c710c63"}
CURRENT_AFFINE = {"path": "fea/generated/selected-hardware-followup-v1/engineering-closure-v1/mixed-stack-affine-raw-v2.json",
                  "sha256": "36c2a7f03423690b39a762b10f08659afe4afdfe08d08feffcb8c44171be5e36"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pair(value):
    a = np.asarray(value, dtype=float)
    require(a.shape == (2,) and np.isfinite(a).all(), "finite transverse pair required")
    return a


def prepare(surfaces, points, domain, moment_caps, cells, facets):
    require(type(cells) is int and 2 <= cells <= 128, "2..128 cells per member required")
    require(type(facets) is int and 8 <= facets <= 64 and facets % 4 == 0,
            "8..64 polygon facets, divisible by four, required")
    low, high = domain
    require(np.isfinite(domain).all() and high > low, "positive finite shaft domain required")
    require(len(surfaces) >= 2, "at least two own bearing surfaces required")
    require(len(moment_caps) > 0 and moment_caps[0]["interval"][0] == low
            and moment_caps[-1]["interval"][1] == high, "complete ordered moment-cap domain required")
    previous = low
    for cap in moment_caps:
        a, b = cap["interval"]
        require(a == previous and b > a and math.isfinite(b)
                and math.isfinite(cap["cap"]) and cap["cap"] > 0.,
                "positive contiguous bending references required")
        previous = b
    intervals, rows = [], []
    cuts = [v for cap in moment_caps for v in cap["interval"]]
    for i, surface in enumerate(surfaces):
        a, b = surface["interval"]
        require(low <= a < b <= high and math.isfinite(surface["cap"]) and surface["cap"] > 0.,
                "positive own interval and bearing reference required")
        require(all(b <= c or d <= a for c, d in intervals), "overlapping bearing surfaces refused")
        intervals.append((a, b))
        pair(surface["force"])
        if surface["first_moment"] is not None:
            pair(surface["first_moment"])
        stations = sorted({*np.linspace(a, b, cells+1), *[x for x in cuts if a < x < b]})
        rows.extend({"surface": i, "low": float(x), "high": float(y), "cap": surface["cap"]}
                    for x, y in pairwise(stations))
    for p in points:
        require(math.isfinite(p["s"]), "finite own gravity/load station required")
        pair(p["force"])
        pair(p["couple"])
    residual = sum((pair(s["force"]) for s in surfaces), np.zeros(2))
    residual += sum((pair(p["force"]) for p in points), np.zeros(2))
    require(np.linalg.norm(residual, np.inf) < 1e-5, "own prescribed lateral forces do not balance")
    angles = (2*np.arange(facets)+1)*math.pi/facets
    normals = np.column_stack((np.cos(angles), np.sin(angles)))
    return rows, normals, math.cos(math.pi/facets)


def point_moment(points, station, include):
    result = np.zeros(2)
    for p in points:
        if p["s"] < station or (include and p["s"] == station):
            f = pair(p["force"])
            result += np.array([-f[1], f[0]])*(station-p["s"])-pair(p["couple"])
    return result


def cap_at(moment_caps, station):
    caps = [c["cap"] for c in moment_caps if c["interval"][0] <= station <= c["interval"][1]]
    require(bool(caps), "moment station outside own reference domain")
    return min(caps)


def recover(rows, density, points, domain, moment_caps):
    """Reuse the existing continuous 3D beam integrator, with both components."""
    surfaces = [{"low": r["low"], "high": r["high"], "q0": np.array([0., *q]),
                 "slope": np.zeros(3)} for r, q in zip(rows, density, strict=True)]
    loads = [{"s": p["s"], "force": [0., *p["force"]], "couple": [0., *p["couple"]]}
             for p in points]
    transitions = sorted({v for cap in moment_caps for v in cap["interval"]})
    segments, force, moment = spatial.bending_field([1., 0., 0.], domain, surfaces, loads, transitions)
    for segment in segments:
        a, b = segment["interval_mm"]
        cap = cap_at(moment_caps, (a+b)/2.)
        segment["raw_moment_cap"] = cap
        segment["raw_index"] = segment["maximum_bending"]["magnitude"]/cap
    return segments, force, moment


def solve(surfaces, points, domain, moment_caps, *, cells=16, facets=16):
    """Minimize a raw reference index while preserving own signed wrenches.

    first_moment = integral((s-member_midpoint)*q(s) ds), on the shaft.
    A None first_moment is allowed only for synthetic free-couple benchmarks;
    current joints must supply both components. No member stiffness is assumed.
    """
    rows, normals, polygon_cos = prepare(surfaces, points, domain, moment_caps, cells, facets)
    a, b, caps = (np.asarray([r[k] for r in rows]) for k in ("low", "high", "cap"))
    count, total = len(rows), domain[1]-domain[0]
    force_scale = float(sum((b-a)*caps))
    # Normalize unknown density/index together. Some admitted cases have only
    # roundoff-sized lateral actions (u about 1e-8); raw-index unknowns would
    # put those complete cases below the LP's absolute feasibility tolerance.
    estimates = []
    for surface in surfaces:
        length = surface["interval"][1]-surface["interval"][0]
        q = np.linalg.norm(pair(surface["force"]))/length
        if surface["first_moment"] is not None:
            q += 6.*np.linalg.norm(pair(surface["first_moment"]))/length**2
        estimates.append(q/surface["cap"])
    estimates.extend((np.linalg.norm(pair(p["force"]))*total+np.linalg.norm(pair(p["couple"])))
                     /min(c["cap"] for c in moment_caps) for p in points)
    index_scale = max(*estimates, 1e-15)
    size = 2*count+1
    eq, rhs = [], []
    for i, surface in enumerate(surfaces):
        mask = np.asarray([r["surface"] == i for r in rows])
        weights = caps*(b-a)*mask
        middle = sum(surface["interval"])/2.
        for component in range(2):
            row = np.zeros(size)
            row[component:-1:2] = weights/force_scale
            eq.append(row)
            rhs.append(surface["force"][component]/(force_scale*index_scale))
            if surface["first_moment"] is not None:
                row = np.zeros(size)
                row[component:-1:2] = weights*((a+b)/2.-middle)/(force_scale*total)
                eq.append(row)
                rhs.append(surface["first_moment"][component]/(force_scale*total*index_scale))
    # Free-couple synthetic benchmarks additionally impose complete shaft moment.
    # Fully prescribed current member wrenches retain their original roundoff;
    # the unchanged dimensional end-balance gates check that independently.
    if any(s["first_moment"] is None for s in surfaces):
        target = sum((np.array([-p["couple"][1], p["couple"][0]])
                      -p["s"]*pair(p["force"]) for p in points), np.zeros(2))
        for component in range(2):
            row = np.zeros(size)
            row[component:-1:2] = caps*(b-a)*(a+b)/2./(force_scale*total)
            eq.append(row)
            rhs.append(target[component]/(force_scale*total*index_scale))
    eq, rhs = np.asarray(eq), np.asarray(rhs)
    objective = np.zeros(size)
    objective[-1] = 1.
    nodes = {(float(t), True) for t in [*a, *b, *[v for c in moment_caps for v in c["interval"]]]}
    nodes.update((float(p["s"]), include) for p in points if domain[0] <= p["s"] <= domain[1]
                 for include in (False, True))
    bearing = np.zeros((count*len(normals), size))
    for j in range(count):
        bearing[j*len(normals):(j+1)*len(normals), 2*j:2*j+2] = normals
    bearing[:, -1] = -polygon_cos
    convergence = []
    for round_index in range(64):
        matrices, offsets = [bearing], [np.zeros(len(bearing))]
        for station, include in sorted(nodes):
            cap = cap_at(moment_caps, station)
            weights = caps*(np.maximum(station-a, 0.)**2-np.maximum(station-b, 0.)**2)/2./cap
            row = np.zeros((len(normals), size))
            row[:, :-1:2] = normals[:, 1, None]*weights
            row[:, 1:-1:2] = -normals[:, 0, None]*weights
            row[:, -1] = -polygon_cos
            matrices.append(row)
            offsets.append(-normals@point_moment(points, station, include)/(cap*index_scale))
        aub, bub = np.vstack(matrices), np.concatenate(offsets)
        result = linprog(objective, A_ub=aub, b_ub=bub, A_eq=eq, b_eq=rhs,
                         bounds=[(None, None)]*(size-1)+[(0., None)], method="highs-ds",
                         options={"primal_feasibility_tolerance": 1e-9,
                                  "dual_feasibility_tolerance": 1e-9, "time_limit": 20.})
        require(result.status == 0 and result.success, f"vector LP failed: {result.status}: {result.message}")
        density = result.x[:-1].reshape((-1, 2))*caps[:, None]*index_scale
        raw_index = float(result.fun)*index_scale
        segments, end_force, end_moment = recover(rows, density, points, domain, moment_caps)
        cuts = [(s["maximum_bending"]["station_mm"], True) for s in segments
                if s["raw_index"] > raw_index*(1.+1e-8)+1e-10]
        # A circular-norm maximum alone need not find the maximum projection
        # onto every inscribed-polygon facet. Check each quadratic projection
        # continuously as well, so nested meshes share the same feasible set.
        for segment in segments:
            coeff = np.asarray(segment["moment_coefficients_unit_interval_nmm"])
            require(np.linalg.norm(coeff[3]) < 1e-10, "constant-cell bending must be quadratic")
            projected = coeff[:3, 1:]@normals.T
            low, high = segment["interval_mm"]
            for c0, c1, c2 in projected.T:
                if c2 < 0.:
                    t = -c1/(2.*c2)
                    if 0. < t < 1. and (c0+c1*t+c2*t*t)/segment["raw_moment_cap"] > raw_index*polygon_cos*(1.+1e-8)+1e-10:
                        cuts.append((low+t*(high-low), True))
        convergence.append({"raw_index": raw_index, "constraint_stations": len(nodes), "new_peak_cuts": len(set(cuts)-nodes)})
        if not cuts:
            break
        require(any(t not in nodes for t in cuts),
                f"continuous vector moment cuts made no progress: u={raw_index}, cuts={cuts}, "
                f"max inequality residual={np.max(aub@result.x-bub)}")
        nodes.update(cuts)
    else:
        raise ValueError(f"continuous vector moment cuts did not converge: {convergence}")
    dual_objective = float(bub@result.ineqlin.marginals+rhs@result.eqlin.marginals)
    stationarity = objective-(aub.T@result.ineqlin.marginals+eq.T@result.eqlin.marginals
                             +result.lower.marginals+result.upper.marginals)
    certificate = {"equality_residual": float(np.max(np.abs(eq@result.x-rhs))),
                   "inequality_violation": float(max(0., np.max(aub@result.x-bub))),
                   "dual_stationarity_residual": float(np.max(np.abs(stationarity))),
                   "primal_dual_gap": abs(float(result.fun)-dual_objective),
                   "dual_sign_violation": float(max(0., np.max(result.ineqlin.marginals),
                                                    np.max(-result.lower.marginals),
                                                    np.max(result.upper.marginals)))}
    require(max(certificate.values()) < 1e-7, "vector LP primal/dual certificate fails")
    force_errors, moment_errors = [], []
    for i, surface in enumerate(surfaces):
        mask = np.asarray([r["surface"] == i for r in rows])
        force = np.sum(density*((b-a)*mask)[:, None], axis=0)
        force_errors.append(float(np.linalg.norm(force-pair(surface["force"]), np.inf)))
        if surface["first_moment"] is not None:
            middle = sum(surface["interval"])/2.
            first = np.sum(density*((b-a)*((a+b)/2.-middle)*mask)[:, None], axis=0)
            moment_errors.append(float(np.linalg.norm(first-pair(surface["first_moment"]), np.inf)))
    require(max(force_errors) < 1e-7 and max(moment_errors, default=0.) < 1e-5,
            "own dimensional member force/couple recovery fails")
    require(np.linalg.norm(end_force, np.inf) < 1e-5 and np.linalg.norm(end_moment, np.inf) < 1e-3,
            "complete own shaft end balance fails")
    bearing_index = float(np.max(np.linalg.norm(density, axis=1)/caps))
    bending_index = max(s["raw_index"] for s in segments)
    certified = max(raw_index, bearing_index, bending_index)
    require(certified <= raw_index*(1.+2e-7)+2e-10,
            "numerical reference enlargement exceeds its fixed gate")
    return {"cells_per_member": cells, "facets": facets, "cell_count": count,
            "polygon_maximum_radial_conservatism": 1./polygon_cos-1.,
            "LP_objective_normalization": index_scale,
            "LP_reference_index": raw_index, "certified_raw_reference_index": certified,
            "raw_bearing_index": bearing_index, "continuous_raw_bending_index": bending_index,
            "cut_rounds": round_index+1, "LP_certificate": certificate,
            "convergence": convergence,
            "maximum_member_force_error_n": max(force_errors),
            "maximum_member_first_moment_error_nmm": max(moment_errors, default=0.),
            "end_force_error_n": float(np.linalg.norm(end_force, np.inf)),
            "end_moment_error_nmm": float(np.linalg.norm(end_moment, np.inf)),
            "cells": [{**r, "density_yz": q.tolist()} for r, q in zip(rows, density, strict=True)],
            "continuous_segments": segments, "physical_compatibility": False,
            "adjusted_capacity": None, "complete_joint_resistance": None}


def verify_witness(surfaces, points, domain, moment_caps, result):
    """Direct dimensional integration, independent of LP/prefix assembly.

    Quadratics are reconstructed from three directly integrated moments.
    Their vector-norm extrema and both sides of every point couple are checked.
    This certifies the supplied field's feasibility, never physical optimality.
    """
    require(result["physical_compatibility"] is False and result["adjusted_capacity"] is None
            and result["complete_joint_resistance"] is None, "invented qualification claim refused")
    cells = result["cells"]
    require(len(cells) == result["cell_count"] and len(cells) > 0, "recorded cell count differs")
    grouped = [[] for _ in surfaces]
    for cell in cells:
        i = cell["surface"]
        require(type(i) is int and 0 <= i < len(surfaces), "unknown recorded surface")
        require(np.isfinite([cell["low"], cell["high"], cell["cap"]]).all()
                and cell["high"] > cell["low"] and cell["cap"] == surfaces[i]["cap"],
                "changed recorded interval or bearing reference")
        pair(cell["density_yz"])
        grouped[i].append(cell)
    force_errors, first_errors = [], []
    for i, surface in enumerate(surfaces):
        group = sorted(grouped[i], key=lambda c: c["low"])
        require(bool(group) and group[0]["low"] == surface["interval"][0]
                and group[-1]["high"] == surface["interval"][1]
                and all(x["high"] == y["low"] for x, y in pairwise(group)),
                "recorded cells do not partition their own complete surface")
        force = [math.fsum(c["density_yz"][j]*(c["high"]-c["low"]) for c in group) for j in range(2)]
        force_errors.append(max(abs(x-y) for x, y in zip(force, surface["force"], strict=True)))
        if surface["first_moment"] is not None:
            center = sum(surface["interval"])/2.
            first = [math.fsum(c["density_yz"][j]*(c["high"]-c["low"])
                              *((c["high"]+c["low"])/2.-center) for c in group) for j in range(2)]
            first_errors.append(max(abs(x-y) for x, y in zip(first, surface["first_moment"], strict=True)))

    def moment(station, include):
        terms = [[], []]
        for c in cells:
            h = (max(station-c["low"], 0.)**2-max(station-c["high"], 0.)**2)/2.
            terms[0].append(-c["density_yz"][1]*h)
            terms[1].append(c["density_yz"][0]*h)
        for p in points:
            if p["s"] < station or (include and p["s"] == station):
                terms[0].append(-p["force"][1]*(station-p["s"])-p["couple"][0])
                terms[1].append(p["force"][0]*(station-p["s"])-p["couple"][1])
        return np.array([math.fsum(t) for t in terms])

    stations = sorted({*domain, *[v for c in cells for v in (c["low"], c["high"])],
                       *[v for cap in moment_caps for v in cap["interval"]],
                       *[p["s"] for p in points if domain[0] < p["s"] < domain[1]]})
    bearing = max(math.hypot(*c["density_yz"])/c["cap"] for c in cells)
    bending, polygon_bending = 0., 0.
    facets = result["facets"]
    require(type(facets) is int and 8 <= facets <= 64 and facets % 4 == 0, "invalid recorded polygon")
    angles = (2*np.arange(facets)+1)*math.pi/facets
    normals = np.column_stack((np.cos(angles), np.sin(angles)))
    polygon_cos = math.cos(math.pi/facets)
    for a, b in pairwise(stations):
        m0, mm, m1 = moment(a, True), moment((a+b)/2., True), moment(b, False)
        c0, c1, c2 = m0, 4.*mm-3.*m0-m1, 2.*(m1+m0-2.*mm)
        derivative = np.array([4.*(c2@c2), 6.*(c1@c2),
                               2.*(c1@c1+2.*c0@c2), 2.*(c0@c1)])
        derivative = np.trim_zeros(derivative, "f")
        roots = np.roots(derivative) if len(derivative) > 1 else []
        fractions = [0., 1., *[float(z.real) for z in roots if abs(z.imag) < 1e-8 and 0. < z.real < 1.]]
        cap = min(c["cap"] for c in moment_caps if c["interval"][0] <= (a+b)/2. <= c["interval"][1])
        for t in fractions:
            value = moment(a+t*(b-a), t != 1.)
            bending = max(bending, float(np.linalg.norm(value))/cap)
        for normal in normals:
            p0, p1, p2 = [float(c@normal) for c in (c0, c1, c2)]
            candidates = [0., 1.]
            if p2 < 0. and 0. < -p1/(2.*p2) < 1.:
                candidates.append(-p1/(2.*p2))
            polygon_bending = max(polygon_bending, max(p0+p1*t+p2*t*t for t in candidates)/(cap*polygon_cos))
    # Separate left/right boundary values cover point couples and material changes.
    for station in stations:
        cap = min(c["cap"] for c in moment_caps if c["interval"][0] <= station <= c["interval"][1])
        for include in (False, True):
            bending = max(bending, float(np.linalg.norm(moment(station, include)))/cap)
            polygon_bending = max(polygon_bending, float(np.max(normals@moment(station, include)))/(cap*polygon_cos))
    end_force = [math.fsum([*[c["density_yz"][j]*(c["high"]-c["low"]) for c in cells],
                           *[p["force"][j] for p in points]]) for j in range(2)]
    end_moment = float(np.linalg.norm(moment(domain[1], True), np.inf))
    require(max(force_errors) < 1e-7 and max(first_errors, default=0.) < 1e-5
            and max(map(abs, end_force)) < 1e-5 and end_moment < 1e-3,
            "independent own force/couple balance fails")
    index, lp_index = result["certified_raw_reference_index"], result["LP_reference_index"]
    require(math.isfinite(index) and math.isfinite(lp_index) and 0 <= lp_index <= index
            and index <= lp_index*(1.+2e-7)+2e-10
            and max(bearing, bending) <= index*(1.+1e-8)+1e-10,
            "independent continuous raw references fail")
    polygon_bearing = max(float(np.max(normals@pair(c["density_yz"]))) / (c["cap"]*polygon_cos) for c in cells)
    require(max(polygon_bending, polygon_bearing) <= lp_index*(1.+2e-7)+2e-10,
            "independent continuous polygon references fail")
    require(abs(bearing-result["raw_bearing_index"]) < 1e-7
            and abs(bending-result["continuous_raw_bending_index"]) < 1e-7,
            "independent reference indices disagree with recorded result")
    return {"maximum_member_force_error_n": max(force_errors),
            "maximum_member_first_moment_error_nmm": max(first_errors, default=0.),
            "shaft_end_force_error_n": max(map(abs, end_force)), "shaft_end_moment_error_nmm": end_moment,
            "raw_bearing_index": bearing, "continuous_raw_bending_index": bending,
            "continuous_polygon_raw_index": max(polygon_bending, polygon_bearing),
            "independently_checked_cells": len(cells)}


def current_stack_inputs(shaft, trials, loads, reference):
    """Join current own spatial actions; retain axial/torsional projections separately."""
    axis = spatial.vector(shaft["basis"][0])
    transverse = np.asarray(shaft["basis"][1:])
    require(transverse.shape == (2, 3)
            and np.linalg.norm(np.asarray(shaft["basis"])@np.asarray(shaft["basis"]).T-np.eye(3)) < 1e-10
            and np.linalg.norm(np.cross(axis, transverse[0])-transverse[1]) < 1e-10,
            "own right-handed orthonormal shaft basis required")
    require(len(trials) == len(shaft["surfaces"]) == 3
            and reference["axis_id"] == shaft["axis_id"], "own three-member current stack required")
    bearing = {r["surface_index"]: r for r in reference["raw_bearing_trials"]}
    surfaces = []
    for i, (surface, row) in enumerate(zip(shaft["surfaces"], trials, strict=True)):
        require(row["axis_id"] == shaft["axis_id"] and row["surface_index"] == i
                and row["host"] == surface["host"] == bearing[i]["host"]
                and row["kind"] == surface["kind"] == bearing[i]["kind"]
                and row["interval_from_axis_point_mm"] == surface["interval_mm"],
                "current own member/interval join differs")
        # Authenticate the earlier affine trial, then retain its exact prescribed
        # force and couple while searching a different statics distribution.
        spatial.affine_surface(row, axis)
        surfaces.append({"host": surface["host"], "kind": surface["kind"],
                         "interval": surface["interval_mm"], "cap": bearing[i]["raw_bearing_reference_n_mm"],
                         "force": (-transverse@spatial.vector(row["lateral_force_on_host_xyz_n"])).tolist(),
                         "first_moment": (transverse@np.cross(axis, spatial.vector(
                             row["moment_on_host_about_interval_center_xyz_nmm"]))).tolist()})
    points, excluded = [], []
    origin = spatial.vector(shaft["point"])
    for load in loads:
        delta = spatial.vector(load["point_xyz_mm"])-origin
        force = spatial.vector(load["force_xyz_n"])
        station = float(delta@axis)
        couple = np.cross(delta-axis*station, force)+spatial.vector(load.get("moment_xyz_nmm", [0., 0., 0.]))
        points.append({"s": station, "force": (transverse@force).tolist(), "couple": (transverse@couple).tolist()})
        excluded.append({"id": load["id"], "axial_force_n": float(axis@force), "axial_torque_nmm": float(axis@couple)})
    caps = [{"interval": s["interval_mm"], "cap": s["raw_plastic_moment_reference_nmm"]}
            for s in reference["continuous_bending_segments"]]
    return {"surfaces": surfaces, "points": points, "domain": shaft["shaft_interval_mm"],
            "moment_caps": caps, "separate_axial_gravity_and_torque": excluded,
            "basis_axis_transverse_xyz": shaft["basis"]}


def historical_benchmarks():
    """Embed the 15 frozen scalar known answers in the new vector method.

    The old analytical values and original feasible loads are reference data;
    no material or candidate qualification transfers from those benchmarks.
    Convert their lbf/in units to N/mm before invoking dimensional gates.
    """
    inputs, prior = current.read(HISTORICAL_INPUTS), current.read(HISTORICAL_RESULT)
    specifications = inputs["published_cases"]+inputs["synthetic_cases"]
    require(len(specifications) == len(prior["cases"]) == 15, "complete frozen scalar benchmark set required")
    results = []
    pound = 4.4482216152605
    for source, old in zip(specifications, prior["cases"], strict=True):
        require(source["id"] == old["id"], "own historical benchmark join required")
        main, side, gap = [source[k]*25.4 for k in ("main_length_in", "side_length_in", "gap_in")]
        load = old["analytic_raw_yield_lbf"]*pound
        surfaces = [{"interval": [0., main], "cap": source["main_bearing_lb_in"]*pound/25.4,
                     "force": [load, 0.], "first_moment": None},
                    {"interval": [main+gap, main+gap+side], "cap": source["side_bearing_lb_in"]*pound/25.4,
                     "force": [-load, 0.], "first_moment": None}]
        domain = [0., main+gap+side]
        caps = [{"interval": domain, "cap": source["yield_moment_lb_in"]*pound*25.4}]
        grids = []
        for count, old_grid in zip((32, 64, 128), old["grids"], strict=True):
            require(old_grid["cells_per_member"] == count, "own historical grid required")
            field = solve(surfaces, [], domain, caps, cells=count, facets=8)
            check = verify_witness(surfaces, [], domain, caps, field)
            feasible_load = old["analytic_raw_yield_lbf"]/field["certified_raw_reference_index"]
            difference = abs(feasible_load-old_grid["scaled_statics_load_lbf"])/old["analytic_raw_yield_lbf"]
            require(difference < 1e-5 and 1.-1e-7 <= field["certified_raw_reference_index"],
                    "new vector method disagrees with frozen scalar known answer")
            grids.append({"cells_per_member": count, "certified_raw_reference_index": field["certified_raw_reference_index"],
                          "equivalent_feasible_load_lbf": feasible_load,
                          "relative_difference_from_frozen_scalar_witness": difference,
                          "relative_shortfall_from_analytic_load": 1.-feasible_load/old["analytic_raw_yield_lbf"],
                          "LP_certificate": field["LP_certificate"], "independent_check": check})
        require(grids[-1]["relative_shortfall_from_analytic_load"] <= 1e-4,
                "refined scalar benchmark misses analytical limit")
        results.append({"id": source["id"], "raw_governing_mode": old["raw_governing_mode"],
                        "analytic_raw_yield_lbf": old["analytic_raw_yield_lbf"], "grids": grids})
    return results


def run():
    """Test both mixed-stack families in all six current saved states."""
    from scipy.optimize._highspy import _core

    from scripts import eoere_current_washer_lands as intake_source

    # Import all methods before capturing their loaded-file identities.
    guard = current.load("bridge")
    cases, pins = intake_source.intake()
    prior = current.read(CURRENT_AFFINE)
    require(prior["case_sequence"] == spatial.SEQUENCE
            and [c["case_id"] for c in prior["cases"]] == spatial.SEQUENCE
            and prior["geometry_revision"] == "eoere-raised-kicker-screws-v1"
            and prior["hardware_revision"] == "eoere-selected-purchase-hardware-v1"
            and prior["extra_grid"] is False and prior["complete_joint_resistance"] is None,
            "exact current raw-reference report required")
    refs = [HISTORICAL_INPUTS, HISTORICAL_RESULT, CURRENT_AFFINE,
            current.ref(OWN), current.ref(current.ROOT/"tests/test_eoere_joint_vector_tests.py")]
    loaded = {str(Path(m.__file__).resolve()): current.sha(Path(m.__file__).resolve())
              for m in tuple(sys.modules.values())
              if getattr(m, "__file__", None) and Path(m.__file__).is_file()
              and (getattr(m, "__name__", "").startswith(("numpy", "scipy", "scripts", "mini_moonboard", "fea"))
                   or Path(m.__file__).resolve().is_relative_to(current.ROOT))}
    local = {str(Path(p).relative_to(current.ROOT)): h for p, h in loaded.items() if Path(p).is_relative_to(current.ROOT)}
    pins = current.join(pins, local, {r["path"]: r["sha256"] for r in refs})
    current.verify(pins)
    require(current.sha(OWN) == LOADED_SHA, "loaded vector producer changed")
    benchmarks = historical_benchmarks()
    results = []
    for (binding, field, data), old_case in zip(cases, prior["cases"], strict=True):
        require(all(old_case[k] == binding[k] for k in ("case_id", "state_id", "field", "admission"))
                and data["connected_mixed_stack_statics"]["mixed_axis_ids"] == spatial.MIXED_IDS
                and [s["axis_id"] for s in old_case["mixed_stacks"]] == spatial.MIXED_IDS,
                "own complete six-case/eight-stack join required")
        shafts = {s["axis_id"]: s for s in field["source_inputs"]["shafts"]}
        stacks = []
        for reference in old_case["mixed_stacks"]:
            aid = reference["axis_id"]
            shaft = shafts[aid]
            trials = [t for t in data["connected_mixed_stack_statics"]["own_surface_trials"] if t["axis_id"] == aid]
            loads = [r for r in field["body_applied_loads"] if r["body"] == shaft["body"]]
            require(len(loads) == len(shaft["metal_roles"]), "all own metal gravity roles required")
            inputs = current_stack_inputs(shaft, trials, loads, reference)
            arguments = {k: inputs[k] for k in ("surfaces", "points", "domain", "moment_caps")}
            grids = []
            for count in (8, 16, 32):
                try:
                    result = solve(**arguments, cells=count, facets=32)
                    check = verify_witness(**arguments, result=result)
                except ValueError as error:
                    raise ValueError(f"{binding['case_id']}/{aid}/N{count}: {error}") from error
                grids.append({**result, "independent_check": check})
            require(all(b["certified_raw_reference_index"] <= a["certified_raw_reference_index"]*(1.+1e-6)+1e-9
                        for a, b in pairwise(grids)), "nested cell refinement unexpectedly worsened witness")
            stacks.append({"axis_id": aid, "own_inputs": inputs, "grids": grids,
                           "previous_affine_raw_reference_index": reference["maximum_raw_material_trial_index"],
                           "physical_compatibility": False, "adjusted_capacity": None, "complete_joint_resistance": None})
        results.append({**binding, "mixed_stacks": stacks})
    for path, digest in loaded.items():
        require(current.sha(Path(path)) == digest, "loaded numerical execution source changed: "+path)
    current.verify(pins)
    require(current.sha(OWN) == LOADED_SHA and guard is not None, "loaded producer changed")
    runtime = {"python": platform.python_version(), "numpy": importlib.metadata.version("numpy"),
               "scipy": importlib.metadata.version("scipy"),
               "highs": ".".join(str(getattr(_core, "HIGHS_VERSION_"+s)) for s in ("MAJOR", "MINOR", "PATCH"))}
    return {"schema": "eoere_current_representative_vector_joint_tests/v1", "producer": current.ref(OWN),
            "current_affine_reference": CURRENT_AFFINE, "historical_benchmark_inputs": HISTORICAL_INPUTS,
            "historical_benchmark_result": HISTORICAL_RESULT, "source_sha256": pins,
            "loaded_numerical_execution_sha256": loaded, "runtime": runtime, "all_sources_unchanged": True,
            "case_sequence": spatial.SEQUENCE, "cases": results, "historical_benchmarks": benchmarks,
            "geometry_revision": "eoere-raised-kicker-screws-v1", "hardware_revision": "eoere-selected-purchase-hardware-v1",
            "extra_grid": False, "current_stack_case_count": 48, "current_statics_trial_count": 144,
            "maximum_refined_raw_reference_index": max(s["grids"][-1]["certified_raw_reference_index"] for c in results for s in c["mixed_stacks"]),
            "physical_compatibility": False, "physical_demand_bounds_established": False,
            "cleat_transverse_resistance": None, "complete_joint_resistance": None, "finished_member_capacity": None,
            "structural_acceptance": False, "panel_screw_exceedances_deferred": True,
            "native_solve_CAD_rebuild_geometry_change_or_actual_fit": False, "release": current.manifest()["release"],
            "limits": ["Signed vector statics under unchanged saved first-order forces and couples, including own metal gravity and all body/root references. This is not a compatible bearing/contact solution or complete collapse/resistance proof.",
                       "The inscribed 32-facet circle introduces at most sec(pi/32)-1 radial conservatism. Continuous moment norms, not only mesh endpoints, are checked independently; forces are never reduced to compensate for numerical error.",
                       "Raw G0.50/Fyb92000psi/Fu370MPa and catalog body/purchase root hypotheses are inherited unchanged. No NDS design reductions, group/local fracture, axial/torsional/washer/angle interaction or physical calibration are adopted.",
                       "Historical scalar known answers validate the changed numerical method. They do not transfer any earlier candidate pass or physical specimen properties."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
