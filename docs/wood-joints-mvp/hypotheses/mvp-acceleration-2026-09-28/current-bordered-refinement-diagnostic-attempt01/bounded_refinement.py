"""Five-step, existing-factor iterative refinement with extended residuals."""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp

MAX_CORRECTIONS = 5
PASS_REFINEMENT = "PASS_REFINEMENT_GATES"
STOP_STAGNATION = "UNRESOLVED_REFINEMENT_STAGNATION"
STOP_BUDGET = "UNRESOLVED_REFINEMENT_BUDGET"
REJECT_NONFINITE_INPUT = "REJECT_NONFINITE_INPUT"
REJECT_NONFINITE_FACTOR = "REJECT_NONFINITE_FACTOR_OUTPUT"
REJECT_FACTOR_ERROR = "REJECT_FACTOR_SOLVE_ERROR"
UNRESOLVED_EXTRA_PRECISION = "UNRESOLVED_EXTRA_PRECISION_UNAVAILABLE"
REJECT_UNBALANCED = "REJECT_UNBALANCED_BODY_WRENCH"
PASS_BALANCED = "PASS_BALANCED_FREE_BODY"


def _extended_residual(A_ld, abs_A_ld, b_ld, x):
    x_ld = np.asarray(x, dtype=np.longdouble)
    residual = b_ld - A_ld @ x_ld
    scale = abs_A_ld @ np.abs(x_ld) + np.abs(b_ld)
    ratio = np.zeros_like(residual)
    positive = scale > 0
    ratio[positive] = np.abs(residual[positive]) / scale[positive]
    ratio[~positive & (residual != 0)] = np.inf
    backward_error = float(np.max(ratio)) if ratio.size else 0.0
    return residual, backward_error


def refine_existing_factor(A, factor, rhs, gate, *, max_corrections=5,
                           min_relative_improvement=1.0e-3):
    """Refine ``factor.solve(rhs)`` using that same factor and longdouble residuals.

    ``gate(x, residual_ld)`` returns ``(passed, metrics)``. Refinement uses at
    most five correction solves, never refactorizes or changes A, and stops on
    nonfinite values, insufficient backward-error progress, a passing gate, or
    the fixed correction budget. The residual is extra precision; corrections
    still use the existing float64 factor.
    """
    if not isinstance(max_corrections, int) or not 0 <= max_corrections <= MAX_CORRECTIONS:
        raise ValueError(f"max_corrections must be between 0 and {MAX_CORRECTIONS}")
    if not np.isfinite(min_relative_improvement) or min_relative_improvement < 0.0:
        raise ValueError("min_relative_improvement must be finite and nonnegative")
    if np.finfo(np.longdouble).eps >= np.finfo(np.float64).eps:
        return {"status": UNRESOLVED_EXTRA_PRECISION, "solution": None,
                "corrections": 0, "history": []}
    matrix = sp.csr_matrix(A, dtype=np.float64)
    b = np.asarray(rhs, dtype=np.float64)
    if b.ndim == 1:
        b = b[:, None]
    if matrix.shape[0] != matrix.shape[1] or b.ndim != 2 or b.shape[0] != matrix.shape[0]:
        raise ValueError("A and rhs have incompatible shapes")
    if not np.all(np.isfinite(matrix.data)) or not np.all(np.isfinite(b)):
        return {"status": REJECT_NONFINITE_INPUT, "solution": None,
                "corrections": 0, "history": []}
    A_ld = matrix.astype(np.longdouble)
    abs_A_ld = A_ld.copy()
    abs_A_ld.data = np.abs(abs_A_ld.data)
    b_ld = np.asarray(b, dtype=np.longdouble)
    try:
        x = np.asarray(factor.solve(b), dtype=np.float64)
    except Exception as exc:
        return {"status": REJECT_FACTOR_ERROR, "solution": None,
                "corrections": 0, "history": [], "error": repr(exc)}
    if x.ndim == 1:
        x = x[:, None]
    if x.shape != b.shape or not np.all(np.isfinite(x)):
        return {"status": REJECT_NONFINITE_FACTOR, "solution": None,
                "corrections": 0, "history": []}
    residual, berr = _extended_residual(A_ld, abs_A_ld, b_ld, x)
    if not np.isfinite(berr) or not np.all(np.isfinite(residual)):
        return {"status": REJECT_NONFINITE_FACTOR, "solution": None,
                "corrections": 0, "history": []}
    passed, metrics = gate(x, residual)
    history = [{"correction": 0, "componentwise_backward_error": berr, **metrics}]
    if passed:
        return {"status": PASS_REFINEMENT, "solution": x, "corrections": 0,
                "history": history, "stop_reason": "initial_solution_passed_strict_gates"}

    for step in range(1, max_corrections + 1):
        residual64 = np.asarray(residual, dtype=np.float64)
        if not np.all(np.isfinite(residual64)):
            return {"status": REJECT_NONFINITE_INPUT, "solution": x,
                    "corrections": step - 1, "history": history,
                    "stop_reason": "residual_not_representable_for_existing_factor"}
        try:
            correction = np.asarray(factor.solve(residual64), dtype=np.float64)
        except Exception as exc:
            return {"status": REJECT_FACTOR_ERROR, "solution": x,
                    "corrections": step - 1, "history": history, "error": repr(exc)}
        if correction.ndim == 1:
            correction = correction[:, None]
        if correction.shape != x.shape or not np.all(np.isfinite(correction)):
            return {"status": REJECT_NONFINITE_FACTOR, "solution": x,
                    "corrections": step - 1, "history": history}
        candidate = x + correction
        if not np.all(np.isfinite(candidate)):
            return {"status": REJECT_NONFINITE_FACTOR, "solution": x,
                    "corrections": step - 1, "history": history}
        candidate_residual, candidate_berr = _extended_residual(A_ld, abs_A_ld, b_ld, candidate)
        if not np.isfinite(candidate_berr) or not np.all(np.isfinite(candidate_residual)):
            return {"status": REJECT_NONFINITE_FACTOR, "solution": x,
                    "corrections": step - 1, "history": history}
        candidate_passed, candidate_metrics = gate(candidate, candidate_residual)
        history.append({"correction": step,
                        "componentwise_backward_error": candidate_berr,
                        **candidate_metrics})
        if candidate_passed:
            return {"status": PASS_REFINEMENT, "solution": candidate,
                    "corrections": step, "history": history,
                    "stop_reason": "refined_solution_passed_strict_gates"}
        if candidate_berr >= berr * (1.0 - min_relative_improvement):
            return {"status": STOP_STAGNATION, "solution": x,
                    "corrections": step, "history": history,
                    "stop_reason": "backward_error_did_not_improve_by_minimum_fraction"}
        x, residual, berr = candidate, candidate_residual, candidate_berr
    return {"status": STOP_BUDGET, "solution": x,
            "corrections": max_corrections, "history": history,
            "stop_reason": "fixed_correction_budget_exhausted"}


def solve_bordered_chunk_refined(factor, system, R, loads, *,
                                 rotation_scale_mm=1000.0, max_corrections=5,
                                 balance_atol_N=1.0e-10, balance_rtol=1.0e-10,
                                 kkt_residual_tolerance=1.0e-10,
                                 gauge_constraint_atol_mm=1.0e-10,
                                 gauge_constraint_rtol=1.0e-10,
                                 gauge_multiplier_atol_N=1.0e-10,
                                 gauge_multiplier_rtol=1.0e-10):
    """Refine an existing free-body KKT factor under the original helper gates."""
    R = np.asarray(R, dtype=np.float64)
    loads = np.asarray(loads, dtype=np.float64)
    vector_input = loads.ndim == 1
    if vector_input:
        loads = loads[:, None]
    n = R.shape[0]
    if R.shape != (n, 6) or loads.ndim != 2 or loads.shape[0] != n:
        raise ValueError("R and loads have incompatible shapes")
    if not np.isfinite(rotation_scale_mm) or rotation_scale_mm <= 0.0:
        raise ValueError("rotation_scale_mm must be positive and finite")
    if not np.all(np.isfinite(R)) or not np.all(np.isfinite(loads)):
        return {"status": REJECT_NONFINITE_INPUT, "displacement_mm": None,
                "gauge_multiplier_N": None, "corrections": 0, "history": []}
    generalized = R.T @ loads
    thresholds = np.asarray([
        balance_atol_N + balance_rtol * max(1.0, float(np.linalg.norm(loads[:, j], ord=1)))
        for j in range(loads.shape[1])
    ])
    balanced = np.max(np.abs(generalized), axis=0) <= thresholds
    if not np.all(balanced):
        return {"status": REJECT_UNBALANCED, "displacement_mm": None,
                "gauge_multiplier_N": None, "balanced_columns": balanced.tolist(),
                "rigid_generalized_load_N": generalized.tolist(),
                "gauge_multiplier_used_as_support": False,
                "rigid_wrench_discarded": False}

    matrix = sp.csr_matrix(system, dtype=np.float64)
    rhs = np.vstack((loads, np.zeros((6, loads.shape[1]), dtype=np.float64)))
    if matrix.shape != (n + 6, n + 6):
        raise ValueError("bordered system has an unexpected shape")
    def gate(x, residual):
        u, lam = x[:n, :], x[n:, :]
        # Top rows have force units; lower rows are gauge displacement in mm.
        force_relative = float(np.max(np.abs(residual[:n, :]))
                               / max(1.0, float(np.max(np.abs(loads)))))
        gauge = float(np.max(np.abs(R.astype(np.longdouble).T
                                     @ np.asarray(u, dtype=np.longdouble))))
        displacement_scale = max(1.0, float(np.max(np.abs(u))))
        load_scale = max(1.0, float(np.max(np.abs(loads))))
        gauge_tolerance = gauge_constraint_atol_mm + gauge_constraint_rtol * displacement_scale
        lambda_max = float(np.max(np.abs(lam)))
        lambda_tolerance = gauge_multiplier_atol_N + gauge_multiplier_rtol * load_scale
        passed = (force_relative <= kkt_residual_tolerance
                  and gauge <= gauge_tolerance and lambda_max <= lambda_tolerance)
        return passed, {"max_kkt_relative_residual": force_relative,
                        "kkt_residual_tolerance": kkt_residual_tolerance,
                        "max_gauge_constraint_mm": gauge,
                        "gauge_constraint_tolerance_mm": gauge_tolerance,
                        "max_gauge_multiplier_N": lambda_max,
                        "gauge_multiplier_tolerance_N": lambda_tolerance}

    result = refine_existing_factor(matrix, factor, rhs, gate,
                                    max_corrections=max_corrections)
    solution = result.get("solution")
    out = {k: v for k, v in result.items() if k != "solution"}
    out["status"] = PASS_BALANCED if result["status"] == PASS_REFINEMENT else result["status"]
    out["balanced_columns"] = balanced.tolist()
    out["rigid_generalized_load_N"] = generalized.tolist()
    out["body_wrenches"] = [{
        "force_N": generalized[:3, j].tolist(),
        "moment_about_source_centroid_N_mm": (generalized[3:, j] * rotation_scale_mm).tolist(),
        "scaled_generalized_load_N": generalized[:, j].tolist(),
    } for j in range(loads.shape[1])]
    out["gauge_multiplier_used_as_support"] = False
    out["rigid_wrench_discarded"] = False
    out["displacement_mm"] = None if solution is None else (solution[:n, 0] if vector_input else solution[:n, :])
    out["gauge_multiplier_N"] = None if solution is None else (solution[n:, 0] if vector_input else solution[n:, :])
    return out
