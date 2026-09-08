"""Optimistic normal-only retention bound; no physical contact solution."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from fea.wide_backing_leverage import build as geometry
from mini_moonboard import wide_frame as frame

OUTPUT = Path("fea/results/wide-backing-contact-bound.json")


def minimum_retention(bolts, corners, load):
    """Minimize total tensile support reaction for a unit outward load.

    Coordinates are (X,S). Contact pushes outward, bolts retain inward. Arbitrary
    nonnegative corner forces represent a relaxed convex contact footprint,
    without pressure, stiffness or compatibility constraints. Dual feasibility
    and matching primal/dual objectives certify only this linear program.
    """
    bolts, corners, load = (np.asarray(v, dtype=float) for v in (bolts, corners, load))
    if (bolts.ndim != 2 or corners.ndim != 2 or bolts.shape[1:] != (2,)
            or corners.shape[1:] != (2,) or len(bolts) < 1 or len(corners) < 1
            or load.shape != (2,) or not all(np.isfinite(v).all() for v in (bolts, corners, load))):
        raise ValueError("Finite nonempty (X,S) supports and load required")
    points = np.vstack((bolts, corners))
    signs = np.r_[np.ones(len(bolts)), -np.ones(len(corners))]
    matrix = np.vstack((np.ones(len(points)), points.T))*signs
    rhs = np.r_[1., load]
    cost = np.r_[np.ones(len(bolts)), np.zeros(len(corners))]
    solved = linprog(cost, A_eq=matrix, b_eq=rhs, bounds=(0, None), method="highs")
    if not solved.success:
        raise ValueError("No certified feasible relaxed support solution: "+solved.message)
    dual = solved.eqlin.marginals
    residual = matrix@solved.x-rhs
    slack = cost-matrix.T@dual
    gap = cost@solved.x-rhs@dual
    if (min(solved.x) < -1e-8 or min(slack) < -1e-8 or max(abs(residual)) > 1e-7
            or abs(gap) > 1e-7):
        raise ValueError("Primal/dual equilibrium certificate failed")
    return {"minimum_total_retention_per_n": float(solved.fun),
        "bolt_reactions_per_n": solved.x[:len(bolts)].tolist(),
        "contact_reactions_per_n": solved.x[len(bolts):].tolist(),
        "dual": dual.tolist(), "dual_slack": slack.tolist(),
        "equilibrium_residual": residual.tolist(), "duality_gap": float(gap)}


def build():
    source = geometry()  # Authenticates current export and attachment identities.
    raw = {p.name: p for p in frame.wood_parts(False)}
    height = raw["timber_bottom_backing"].blank[1]
    corners = [[x, s] for side in ("left", "right")
               for x in frame.UPRIGHTS[side] for s in (0., height)]
    bolts = [[x, source["support_s_mm"]] for x in source["support_x_mm"]]
    return {"candidate": frame.KEY, "bolt_x_s_mm": bolts, "contact_corners_x_s_mm": corners,
        "limits": "Optimistic minimum total retention within an isolated normal-only model. "
                  "Full housing rectangles include removed material; arbitrary pressure and no compatibility. "
                  "Not actual bolt sharing, physical contact FEA, whole-frame lower bound or capacity. "
                  "Panel transfer, side restraint, friction and non-normal forces are excluded.",
        "rows": [{"attachment": r["attachment"], "load_x_s_mm": [r["x_mm"], r["s_mm"]],
                  **minimum_retention(bolts, corners, [r["x_mm"], r["s_mm"]])}
                 for r in source["rows"]]}


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build(), indent=2)+"\n")
