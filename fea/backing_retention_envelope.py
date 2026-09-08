"""Optimistic isolated-rail load ceiling under conditional bolt-bearing caps."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from fea.backing_bearing import envelope
from fea.wide_backing_contact_bound import build as geometry

OUTPUT = Path("fea/results/backing-retention-envelope.json")


def ceiling(bolts, corners, load, caps):
    """Maximize outward load with capped inward bolts and unlimited compression.

    Relaxed normal-only equilibrium, not real contact or an allowable load.
    The dual certificate proves this LP ceiling only, not a whole-frame bound.
    """
    bolts, corners, load, caps = (np.asarray(v, dtype=float) for v in (bolts, corners, load, caps))
    if (bolts.ndim != 2 or bolts.shape[1:] != (2,) or len(bolts) == 0
            or corners.ndim != 2 or corners.shape[1:] != (2,) or len(corners) == 0
            or load.shape != (2,) or caps.shape != (len(bolts),)
            or not all(np.isfinite(v).all() for v in (bolts, corners, load, caps))
            or np.any(caps <= 0)):
        raise ValueError("Require finite planar supports, load and positive per-bolt caps")
    points = np.vstack((bolts, corners, load))
    signs = np.r_[np.ones(len(bolts)), -np.ones(len(corners)+1)]
    matrix = np.vstack((np.ones(len(points)), points.T))*signs
    cost = np.zeros(len(points))
    cost[-1] = -1.
    bounds = [(0., float(cap)) for cap in caps]+[(0., None)]*(len(corners)+1)
    result = linprog(cost, A_eq=matrix, b_eq=np.zeros(3), bounds=bounds, method="highs")
    if not result.success:
        raise ValueError("Retention ceiling LP failed: "+result.message)
    dual = result.eqlin.marginals
    upper = result.upper.marginals
    lower = cost-matrix.T@dual-upper
    dual_value = caps@upper[:len(bolts)]
    if (min(result.x) < -1e-7 or np.max(result.x[:len(bolts)]-caps) > 1e-7
            or max(abs(matrix@result.x)) > 1e-6 or min(lower) < -1e-8
            or max(upper) > 1e-8 or max(abs(upper[len(bolts):])) > 1e-8
            or abs(cost@result.x-dual_value) > 1e-6):
        raise ValueError("Retention ceiling primal/dual certificate failed")
    return {"conditional_load_ceiling_n": float(result.x[-1]),
            "bolt_forces_n": result.x[:len(bolts)].tolist(),
            "compression_forces_n": result.x[len(bolts):-1].tolist(),
            "equilibrium_dual": dual.tolist(), "upper_bound_dual": upper.tolist(),
            "lower_bound_dual": lower.tolist(), "dual_objective_n": float(dual_value)}


def build():
    source = geometry()
    cases = {}
    for name, factor in (("dry", 1.), ("wet", .67), ("dry_002in", .73)):
        bearing = envelope(20.447, 11.1125, 625*.006894757293168361*factor)
        cap = bearing["conditional_wood_bearing_force_n"]
        cases[name] = {"bearing": bearing, "per_bolt_caps_n": [cap, cap], "rows": [
            {"attachment": row["attachment"], "load_x_s_mm": row["load_x_s_mm"],
             **ceiling(source["bolt_x_s_mm"], source["contact_corners_x_s_mm"],
                       row["load_x_s_mm"], [cap, cap])} for row in source["rows"]]}
    return {"candidate": source["candidate"], "bolt_x_s_mm": source["bolt_x_s_mm"],
            "contact_corners_x_s_mm": source["contact_corners_x_s_mm"],
            "limits": "Conditional isolated normal-load ceiling with zero preload and "
            "wood-bearing-only bolt caps; unlimited housing compression and no compatibility. "
            "NOT actual joint resistance, actual panel demand, whole-frame bound or approval. "
            "Washer bending, splitting, non-normal loads and other load paths excluded.",
            "cases": cases}


if __name__ == "__main__":
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite retention envelope")
    OUTPUT.write_text(json.dumps(build(), indent=2)+"\n")
