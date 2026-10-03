"""Tiny convex-energy floor-mask adapter for pinned analytical fixtures.

This module consumes an already verified lower factor L with Hsym = L L.T.
It has no frame extraction, inversion, geometry, or CalculiX path.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def factor_spd(H: np.ndarray, symmetry_tol: float = 1e-12) -> tuple[np.ndarray, dict[str, float]]:
    """Factor a tiny symmetric SPD fixture matrix and verify its reconstruction."""
    H = np.asarray(H, dtype=float)
    assert H.ndim == 2 and H.shape[0] == H.shape[1]
    assert np.isfinite(H).all()
    skew = H - H.T
    skew_rel = float(np.linalg.norm(skew, ord=np.inf) /
                     max(np.linalg.norm(H, ord=np.inf), 1.0))
    assert skew_rel <= symmetry_tol, f"fixture is not reciprocal: {skew_rel}"
    S = 0.5 * (H + H.T)
    L = np.linalg.cholesky(S)
    residual = float(np.linalg.norm(S - L @ L.T, ord=np.inf) /
                     max(np.linalg.norm(S, ord=np.inf), 1.0))
    assert residual <= 1e-12, f"factor reconstruction residual {residual}"
    assert np.min(np.linalg.eigvalsh(S)) > 0.0
    return L, {"relative_skew_inf": skew_rel,
               "relative_factor_reconstruction_inf": residual,
               "minimum_eigenvalue": float(np.min(np.linalg.eigvalsh(S)))}


def build_model(
    L: np.ndarray,
    D: np.ndarray,
    e: np.ndarray,
    W: np.ndarray,
    laws: list[dict[str, Any]],
    floor_cells: list[dict[str, Any]],
    excluded_floor_masks: list[list[bool]] = (),
    time_limit_s: float = 3.0,
):
    """Build the floor-binary convex epigraph model; do not optimize here.

    ``laws[i]`` is bilateral with positive ``k``, unilateral with positive
    ``k``, or a tangent row. A floor normal is one of the unilateral rows.
    ``floor_cells`` maps that normal row to tangent rows and supplied episode
    references in the q coordinates. All continuous variables are signed and
    unbounded except the nonnegative hinge slack.
    """
    from pyscipopt import Model, quicksum

    L = np.asarray(L, dtype=float)
    D = np.asarray(D, dtype=float)
    e = np.asarray(e, dtype=float)
    W = np.asarray(W, dtype=float)
    n = len(e)
    if D.ndim == 1:
        D = D.reshape((n, 0))
    assert L.shape == (n, n) and D.shape[0] == n
    assert W.shape == (D.shape[1],) and len(laws) == n
    assert np.isfinite(L).all() and np.isfinite(D).all()
    assert np.isfinite(e).all() and np.isfinite(W).all()
    assert time_limit_s > 0.0

    normal_rows = [int(cell["normal_row"]) for cell in floor_cells]
    tangent_rows = [int(row) for cell in floor_cells
                    for row, _ in cell["tangent_rows_and_references"]]
    assert len(set(normal_rows)) == len(normal_rows)
    assert len(set(tangent_rows)) == len(tangent_rows)
    assert all(0 <= i < n for i in normal_rows + tangent_rows)
    assert all(laws[i]["kind"] == "unilateral" for i in normal_rows)
    assert set(tangent_rows) == {i for i, law in enumerate(laws)
                                 if law["kind"] == "tangent"}

    model = Model()
    model.hideOutput()
    model.setParam("limits/time", float(time_limit_s))
    model.setParam("parallel/maxnthreads", 1)
    model.setParam("numerics/feastol", 1e-9)

    # y=L.T*g; this diagonal energy form avoids a quadratic objective matrix.
    y = [model.addVar(name=f"y_{j}", lb=None, ub=None) for j in range(n)]
    a = [model.addVar(name=f"a_{j}", lb=None, ub=None)
         for j in range(D.shape[1])]
    q = [model.addVar(name=f"q_{i}", lb=None, ub=None) for i in range(n)]
    slack: dict[int, Any] = {}
    mode: dict[int, Any] = {}

    # q = D*a + e - L*y. Keep each row equation explicit.
    for i in range(n):
        expr = q[i] + quicksum(float(L[i, j]) * y[j]
                               for j in range(n) if L[i, j])
        expr -= quicksum(float(D[i, j]) * a[j]
                         for j in range(D.shape[1]) if D[i, j])
        model.addCons(expr == float(e[i]), name=f"compatibility_{i}")

    energy_terms = [0.5 * yj * yj for yj in y]
    for i, law in enumerate(laws):
        kind = law["kind"]
        if kind == "tangent":
            continue
        k = float(law["k"])
        assert np.isfinite(k) and k > 0.0
        domain = law.get("domain_mm")
        if domain is not None:
            lo, hi = map(float, domain)
            assert lo <= hi
            model.addCons(q[i] >= lo, name=f"table_domain_lower_{i}")
            model.addCons(q[i] <= hi, name=f"table_domain_upper_{i}")
        if kind == "bilateral":
            # Scale into the spring's energy coordinate so large k does not
            # become a large quadratic coefficient in the epigraph.
            eta = model.addVar(name=f"bilateral_energy_coordinate_{i}",
                               lb=None, ub=None)
            model.addCons(eta == np.sqrt(k) * q[i],
                          name=f"bilateral_energy_coordinate_def_{i}")
            energy_terms.append(0.5 * eta * eta)
        else:
            assert kind == "unilateral"
            s = slack[i] = model.addVar(name=f"hinge_{i}", lb=0.0, ub=None)
            model.addCons(s >= np.sqrt(k) * q[i], name=f"hinge_epigraph_{i}")
            energy_terms.append(0.5 * s * s)

    def indicator_le(expr, bit, activeone, name):
        model.addConsIndicator(expr <= 0, binvar=bit, activeone=activeone,
                               name=name)

    def indicator_eq(expr, bit, activeone, name):
        indicator_le(expr, bit, activeone, name + "_upper")
        indicator_le(-expr, bit, activeone, name + "_lower")

    for cell_number, cell in enumerate(floor_cells):
        nr = int(cell["normal_row"])
        bit = mode[nr] = model.addVar(name=f"floor_bearing_{cell_number}",
                                     vtype="B")
        # The normal hinge is always present. These sign constraints select
        # only the floor episode and do not supply a normal force law.
        indicator_le(-q[nr], bit, True, f"floor_closed_normal_{cell_number}")
        indicator_le(q[nr], bit, False, f"floor_open_normal_{cell_number}")
        for tangent_row, reference in cell["tangent_rows_and_references"]:
            tr = int(tangent_row)
            indicator_eq(q[tr] - float(reference), bit, True,
                         f"floor_held_reference_{cell_number}_{tr}")
            # Open tangent rows have no energy and no constraint. Their
            # recovered generalized effort must therefore be zero.

    floor_bits = [mode[row] for row in normal_rows]
    for mask_number, mask in enumerate(excluded_floor_masks):
        assert len(mask) == len(floor_bits)
        differs = [(1 - bit) if bool(is_closed) else bit
                   for is_closed, bit in zip(mask, floor_bits, strict=True)]
        model.addCons(quicksum(differs) >= 1,
                      name=f"exclude_floor_mask_{mask_number}")

    # SCIP requires a linear objective. Its pinned documentation recommends
    # exactly this epigraph-variable reformulation for nonlinear objectives.
    epigraph = model.addVar(name="total_elastic_energy", lb=None, ub=None)
    energy = quicksum(energy_terms)
    model.addCons(epigraph >= energy, name="elastic_energy_epigraph")
    objective = epigraph - quicksum(float(W[j]) * a[j]
                                    for j in range(len(a)))
    model.setObjective(objective, sense="minimize")
    return model, {"y": y, "a": a, "q": q, "slack": slack,
                   "floor_bits": floor_bits, "epigraph": epigraph}


def polish_fixed_mask_osqp(H_raw: np.ndarray, L: np.ndarray, D: np.ndarray,
                           e: np.ndarray, W: np.ndarray,
                           laws: list[dict[str, Any]],
                           floor_cells: list[dict[str, Any]],
                           mask: list[bool], tolerance: float = 2e-7) -> dict[str, Any]:
    """Polish one SCIP-selected tiny floor mask with its convex fixed-mask QP.

    This does not select a mask. It solves the same source spring potential
    with that mask fixed, then rejects any constraint-bound reaction that
    fails the original force laws. Intended only for analytical fixtures.
    """
    import osqp
    from scipy import sparse

    H_raw = np.asarray(H_raw, dtype=float)
    H = 0.5 * (H_raw + H_raw.T)
    L = np.asarray(L, dtype=float)
    D = np.asarray(D, dtype=float)
    e = np.asarray(e, dtype=float)
    W = np.asarray(W, dtype=float)
    n = len(e)
    m = D.shape[1]
    assert H.shape == L.shape == (n, n) and D.shape == (n, m)
    assert len(laws) == n and len(mask) == len(floor_cells)
    assert np.max(np.abs(H_raw - L @ L.T), initial=0.0) <= 1e-10

    unilateral = [i for i, law in enumerate(laws)
                  if law["kind"] == "unilateral"]
    s_index = {row: m + n + j for j, row in enumerate(unilateral)}
    size = m + n + len(unilateral)
    P = np.zeros((size, size), dtype=float)
    linear = np.zeros(size, dtype=float)
    if n:
        P[m:m+n, m:m+n] = H
    linear[:m] = -W

    # q = B*x + e, x=(a,g,s). Build the spring-potential Hessian.
    B = np.zeros((n, size), dtype=float)
    if m:
        B[:, :m] = D
    B[:, m:m+n] = -H
    for i, law in enumerate(laws):
        kind = law["kind"]
        if kind == "tangent":
            continue
        k = float(law["k"])
        assert np.isfinite(k) and k > 0.0
        if kind == "bilateral":
            row = B[i]
            P += k * np.outer(row, row)
            linear += k * e[i] * row
        else:
            assert kind == "unilateral"
            j = s_index[i]
            P[j, j] += 1.0

    rows: list[np.ndarray] = []
    lower: list[float] = []
    upper: list[float] = []

    def add_row(row: np.ndarray, lo: float = -np.inf,
                hi: float = np.inf) -> None:
        rows.append(np.asarray(row, dtype=float))
        lower.append(float(lo))
        upper.append(float(hi))

    for i, law in enumerate(laws):
        kind = law["kind"]
        if kind == "tangent":
            continue
        k = float(law["k"])
        if kind == "unilateral":
            hinge = np.zeros(size)
            hinge[s_index[i]] = 1.0
            hinge -= np.sqrt(k) * B[i]
            add_row(hinge, np.sqrt(k) * e[i], np.inf)
            slack_nonnegative = np.zeros(size)
            slack_nonnegative[s_index[i]] = 1.0
            add_row(slack_nonnegative, 0.0, np.inf)
        domain = law.get("domain_mm")
        if domain is not None:
            lo, hi = map(float, domain)
            add_row(B[i], lo - e[i], hi - e[i])

    for is_closed, cell in zip(mask, floor_cells, strict=True):
        normal = int(cell["normal_row"])
        if is_closed:
            add_row(B[normal], -e[normal], np.inf)
            for tangent_row, reference in cell["tangent_rows_and_references"]:
                tr = int(tangent_row)
                add_row(B[tr], float(reference) - e[tr],
                        float(reference) - e[tr])
        else:
            add_row(B[normal], -np.inf, -e[normal])

    A = np.vstack(rows) if rows else np.zeros((0, size))
    settings = {
        "verbose": False,
        "eps_abs": 1e-10,
        "eps_rel": 1e-10,
        "eps_prim_inf": 1e-10,
        "eps_dual_inf": 1e-10,
        "max_iter": 200000,
        "time_limit": 15.0,
        "polishing": True,
        "adaptive_rho": False,
        "rho": 0.1,
        "sigma": 1e-6,
        "scaling": 0,
        "check_termination": 1,
        "warm_starting": False,
    }
    qp = osqp.OSQP()
    qp.setup(P=sparse.triu(sparse.csc_matrix(0.5 * (P + P.T)), format="csc"),
             q=linear, A=sparse.csc_matrix(A), l=np.asarray(lower),
             u=np.asarray(upper), **settings)
    solved = qp.solve(raise_error=False)
    status = str(solved.info.status).lower()
    assert status == "solved", f"fixed-mask QP status {status} for mask {mask}"
    x = np.asarray(solved.x, dtype=float)
    a = x[:m]
    g = x[m:m+n]
    slack = {i: float(x[s_index[i]]) for i in unilateral}
    # Keep the operator used by the symmetric-QP compatibility and compare it
    # independently with the original raw operator. Source constitutive laws
    # below use raw-H q, not the optimizer's symmetric approximation.
    q_sym = B @ x + e
    q_raw = D @ a + e - H_raw @ g
    force_errors = []
    hinge_errors = []
    for i, law in enumerate(laws):
        if law["kind"] == "tangent":
            continue
        k = float(law["k"])
        expected = k * q_raw[i] if law["kind"] == "bilateral" else k * max(q_raw[i], 0.0)
        force_errors.append(abs(g[i] - expected))
        if law["kind"] == "unilateral":
            hinge_errors.append(abs(slack[i] - np.sqrt(k) * max(q_raw[i], 0.0)))

    tangent_errors = []
    normal_sign_errors = []
    for is_closed, cell in zip(mask, floor_cells, strict=True):
        normal = int(cell["normal_row"])
        normal_sign_errors.append(max(0.0, -q_raw[normal] if is_closed else q_raw[normal]))
        for tangent_row, reference in cell["tangent_rows_and_references"]:
            tr = int(tangent_row)
            tangent_errors.append(abs(q_raw[tr] - float(reference)) if is_closed
                                  else abs(g[tr]))

    state = {
        "mask": [bool(v) for v in mask],
        "a": a,
        "g": g,
        "q": q_raw,
        "q_sym": q_sym,
        "slack": slack,
        "objective": float(solved.info.obj_val),
        "solver": {"status": status, "iterations": int(solved.info.iter),
                   "primal_residual": float(solved.info.prim_res),
                   "dual_residual": float(solved.info.dual_res)},
        "raw_equilibrium_inf_N": float(np.max(np.abs(D.T @ g - W), initial=0.0)),
        "compatibility_sym_H_inf_mm": float(np.max(np.abs(
            q_sym - (D @ a + e - H @ g)), initial=0.0)),
        "compatibility_raw_H_inf_mm": float(np.max(np.abs(q_sym - q_raw), initial=0.0)),
        "max_source_force_law_error_N": max(force_errors, default=0.0),
        "max_hinge_error": max(hinge_errors, default=0.0),
        "max_floor_tangent_or_open_effort_error": max(tangent_errors, default=0.0),
        "max_floor_normal_sign_error_mm": max(normal_sign_errors, default=0.0),
        "max_floor_normal_bound_reaction_error_N": max(
            (abs(g[int(cell["normal_row"])] -
                 float(laws[int(cell["normal_row"])]["k"]) *
                 max(q_raw[int(cell["normal_row"])], 0.0)) for cell in floor_cells),
            default=0.0),
    }
    state["source_state_pass"] = all(state[key] <= tolerance for key in (
        "raw_equilibrium_inf_N", "compatibility_raw_H_inf_mm",
        "max_source_force_law_error_N", "max_hinge_error",
        "max_floor_tangent_or_open_effort_error",
        "max_floor_normal_sign_error_mm",
        "max_floor_normal_bound_reaction_error_N"))
    return state


def recover_and_check(L: np.ndarray, H_raw: np.ndarray, D: np.ndarray,
                      e: np.ndarray, W: np.ndarray,
                      laws: list[dict[str, Any]], floor_cells: list[dict[str, Any]],
                      model, variables, solution, tolerance: float = 2e-7) -> dict[str, Any]:
    """Recover g=L^-T*y and reject any normal-bound reaction by source laws."""
    L = np.asarray(L, dtype=float)
    H_raw = np.asarray(H_raw, dtype=float)
    D = np.asarray(D, dtype=float)
    e = np.asarray(e, dtype=float)
    W = np.asarray(W, dtype=float)
    y = np.asarray([model.getSolVal(solution, v) for v in variables["y"]])
    a = np.asarray([model.getSolVal(solution, v) for v in variables["a"]])
    q = np.asarray([model.getSolVal(solution, v) for v in variables["q"]])
    g = np.linalg.solve(L.T, y)
    reconstructed = D @ a + e - L @ y
    raw_q = D @ a + e - H_raw @ g
    force_errors = []
    slack_errors = []
    for i, law in enumerate(laws):
        kind = law["kind"]
        if kind == "tangent":
            continue
        k = float(law["k"])
        expected = k * q[i] if kind == "bilateral" else k * max(q[i], 0.0)
        force_errors.append(abs(g[i] - expected))
        if kind == "unilateral":
            s = model.getSolVal(solution, variables["slack"][i])
            slack_errors.append(abs(s - max(np.sqrt(k) * q[i], 0.0)))

    tangent_errors = []
    normal_sign_errors = []
    mask = [model.getSolVal(solution, bit) >= 0.5
            for bit in variables["floor_bits"]]
    for is_closed, cell in zip(mask, floor_cells, strict=True):
        normal_row = int(cell["normal_row"])
        normal_sign_errors.append(max(
            0.0, -q[normal_row] if is_closed else q[normal_row]))
        for tangent_row, reference in cell["tangent_rows_and_references"]:
            i = int(tangent_row)
            if is_closed:
                tangent_errors.append(abs(q[i] - float(reference)))
            else:
                # The tangent coordinate is unconstrained while open; source
                # work is zero exactly when its recovered conjugate effort is 0.
                tangent_errors.append(abs(g[i]))

    objective_energy = float(model.getSolVal(solution, variables["epigraph"]))
    actual_energy = 0.5 * float(y @ y)
    for i, law in enumerate(laws):
        if law["kind"] == "bilateral":
            actual_energy += 0.5 * float(law["k"]) * q[i] ** 2
        elif law["kind"] == "unilateral":
            s = model.getSolVal(solution, variables["slack"][i])
            actual_energy += 0.5 * s ** 2
    check = {
        "mask": mask,
        "y": y,
        "a": a,
        "q": q,
        "g": g,
        "compatibility_L_inf_mm": float(np.max(np.abs(q - reconstructed), initial=0.0)),
        "compatibility_raw_H_inf_mm": float(np.max(np.abs(q - raw_q), initial=0.0)),
        "raw_equilibrium_inf_N": float(np.max(np.abs(D.T @ g - W), initial=0.0)),
        "max_source_force_law_error_N": max(force_errors, default=0.0),
        "max_hinge_error": max(slack_errors, default=0.0),
        "max_floor_tangent_or_open_effort_error": max(tangent_errors, default=0.0),
        "max_floor_normal_sign_error_mm": max(normal_sign_errors, default=0.0),
        "energy_epigraph_gap": objective_energy - actual_energy,
        "max_floor_normal_bound_reaction_error_N": max(
            (abs(g[int(cell["normal_row"])] -
                 float(laws[int(cell["normal_row"])]["k"]) *
                 max(q[int(cell["normal_row"])], 0.0)) for cell in floor_cells),
            default=0.0),
    }
    state_pass = all(check[key] <= tolerance for key in (
        "compatibility_L_inf_mm", "compatibility_raw_H_inf_mm",
        "raw_equilibrium_inf_N", "max_source_force_law_error_N",
        "max_hinge_error", "max_floor_tangent_or_open_effort_error",
        "max_floor_normal_sign_error_mm",
        "max_floor_normal_bound_reaction_error_N"))
    state_pass = state_pass and abs(check["energy_epigraph_gap"]) <= tolerance
    check["source_state_pass"] = state_pass
    return check


def enumerate_floor_masks(H_raw: np.ndarray, L: np.ndarray, D: np.ndarray,
                          e: np.ndarray, W: np.ndarray,
                          laws: list[dict[str, Any]], floor_cells: list[dict[str, Any]],
                          time_limit_s: float = 3.0,
                          tolerance: float = 2e-7) -> dict[str, Any]:
    """Enumerate a tiny floor-mask set; never infer history from energy rank."""
    import time

    max_masks = 2 ** len(floor_cells)
    excluded: list[list[bool]] = []
    candidates: list[dict[str, Any]] = []
    provisional_rejections: list[dict[str, Any]] = []
    statuses: list[str] = []
    complete = False
    stop_reason = None
    start = time.monotonic()
    while len(statuses) <= max_masks:
        if time.monotonic() - start >= time_limit_s * (max_masks + 1):
            stop_reason = "fixture_wall_budget_exhausted"
            break
        model, variables = build_model(L, D, e, W, laws, floor_cells,
                                       excluded, time_limit_s)
        model.optimize()
        status = str(model.getStatus())
        statuses.append(status)
        if status == "infeasible":
            complete = True
            stop_reason = "all_remaining_floor_masks_proven_infeasible"
            break
        if status != "optimal" or model.getNSols() < 1:
            stop_reason = f"solver_status_{status}"
            break
        solution = model.getBestSol()
        check = recover_and_check(L, H_raw, D, e, W, laws, floor_cells,
                                  model, variables, solution, tolerance)
        mask = check["mask"]
        if mask in excluded:
            stop_reason = "solver_returned_excluded_floor_mask"
            break
        # SCIP provides a provisional optimizer candidate for this mask.
        # Force-law admissibility is decided only after a fixed-mask QP polish.
        candidates.append(check)
        if not check["source_state_pass"]:
            provisional_rejections.append({"mask": mask,
                "max_source_force_law_error_N": check["max_source_force_law_error_N"],
                "max_floor_normal_bound_reaction_error_N":
                    check["max_floor_normal_bound_reaction_error_N"],
                "max_raw_equilibrium_inf_N": check["raw_equilibrium_inf_N"],
                "max_compatibility_raw_H_inf_mm": check["compatibility_raw_H_inf_mm"]})
        excluded.append(mask)
        if len(excluded) == max_masks:
            complete = True
            stop_reason = "every_floor_mask_solved_once"
            break

    if not complete and stop_reason is None:
        stop_reason = "fixture_solver_budget_exhausted"
    candidates.sort(key=lambda state: tuple(state["mask"]))
    classification = "MASK_ENUMERATION_COMPLETE" if complete else "BUDGET_OR_SOLVER_STOP"
    return {"classification": classification,
            "complete": complete,
            "stop_reason": stop_reason,
            "solver_status_sequence": statuses,
            "candidate_masks": candidates,
            "provisional_rejections": provisional_rejections,
            "possible_floor_masks": max_masks}
