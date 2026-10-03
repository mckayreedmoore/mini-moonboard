"""Audited elastic-quotient checks for an unmodified free-body KKT operator.

The caller supplies an already factored bordered system using the original K
and six rigid columns R. Loads passed here must already represent a balanced
projected basis RHS; raw physical loads and source wrenches remain the global
controller's responsibility and may not be equilibrated by this projection.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import scipy.sparse as sp


PASS_ELASTIC_QUOTIENT_SCREEN = "PASS_ELASTIC_QUOTIENT_SCREEN"
REJECT_UNBALANCED_BODY_WRENCH = "REJECT_UNBALANCED_BODY_WRENCH"
REJECT_RIGID_LEAKAGE_LIMIT = "REJECT_RIGID_LEAKAGE_LIMIT"
REJECT_KKT_FORCE_RESIDUAL = "REJECT_KKT_FORCE_RESIDUAL"
REJECT_PROJECTED_ELASTIC_FORCE_RESIDUAL = "REJECT_PROJECTED_ELASTIC_FORCE_RESIDUAL"
REJECT_GAUGE_CONSTRAINT = "REJECT_GAUGE_CONSTRAINT"
REJECT_RIGID_IDENTITY_CLOSURE = "REJECT_RIGID_IDENTITY_CLOSURE"

RIGID_LEAKAGE_REL_LIMIT = 5.0e-14
KKT_FORCE_REL_LIMIT = 1.0e-10
PROJECTED_FORCE_REL_LIMIT = 1.0e-10
GAUGE_ATOL_MM = 2.0e-10
IDENTITY_ATOL_N = 1.0e-10
IDENTITY_RTOL = 1.0e-10
BALANCE_ATOL_N = 1.0e-10
BALANCE_RTOL = 1.0e-10
LEGACY_LAMBDA_ATOL_N = 2.0e-10
DEFAULT_ROTATION_SCALE_MM = 1000.0
MAX_CORRECTIONS = 5


def _maxabs(value) -> float:
    arr = np.asarray(value)
    return float(np.max(np.abs(arr))) if arr.size else 0.0


def _row_sum_inf(value) -> float:
    arr = np.asarray(value)
    return float(np.max(np.sum(np.abs(arr), axis=1))) if arr.shape[0] else 0.0


def _wrench(generalized: np.ndarray, rotation_scale_mm: float) -> dict:
    value = np.asarray(generalized, dtype=np.float64).reshape(6)
    return {
        "force_N": value[:3].tolist(),
        "moment_about_source_centroid_N_mm": (value[3:] * rotation_scale_mm).tolist(),
        "scaled_generalized_load_N": value.tolist(),
    }


def _longdouble_audit(matrix_ld, basis_ld, Q_ld, loads_ld, disp_ld, multiplier_ld,
                      rotation_scale_mm, operator, *, kkt_force_rel_limit,
                      projected_force_rel_limit, gauge_atol_mm, identity_atol_N,
                      identity_rtol, legacy_lambda_atol_N):
    """Compute body products in extended precision; Q is orthonormalized in float64."""
    Ku = np.asarray(matrix_ld @ disp_ld, dtype=np.longdouble)
    original = Ku - loads_ld
    upper = original + basis_ld @ multiplier_ld
    projected = original - Q_ld @ (Q_ld.T @ original)
    gauge = basis_ld.T @ disp_ld
    gram_lambda = (basis_ld.T @ basis_ld) @ multiplier_ld
    rt_ku = basis_ld.T @ Ku
    rt_p = basis_ld.T @ loads_ld
    actual_identity = rt_ku + gram_lambda - rt_p
    identity_rhs = rt_ku + gram_lambda - rt_p
    identity_lhs = basis_ld.T @ upper
    order_defect = identity_lhs - identity_rhs
    force_scale = max(np.longdouble(1.0), np.max(np.abs(loads_ld)))
    kkt_relative = float(np.max(np.abs(upper)) / force_scale)
    projected_relative = float(np.max(np.abs(projected)) / force_scale)
    gauge_max = float(np.max(np.abs(gauge)))
    identity_scale = max(np.longdouble(1.0), np.max(np.abs(rt_ku)),
                         np.max(np.abs(gram_lambda)), np.max(np.abs(rt_p)))
    identity_tolerance = np.longdouble(identity_atol_N) + np.longdouble(identity_rtol) * identity_scale
    actual_identity_error = float(np.max(np.abs(actual_identity)))
    order_error = float(np.max(np.abs(order_defect)))
    legacy_lambda_max = float(np.max(np.abs(multiplier_ld)))
    failed = []
    if operator["status"] != PASS_ELASTIC_QUOTIENT_SCREEN:
        failed.append(REJECT_RIGID_LEAKAGE_LIMIT)
    if kkt_relative > kkt_force_rel_limit:
        failed.append(REJECT_KKT_FORCE_RESIDUAL)
    if projected_relative > projected_force_rel_limit:
        failed.append(REJECT_PROJECTED_ELASTIC_FORCE_RESIDUAL)
    if gauge_max > gauge_atol_mm:
        failed.append(REJECT_GAUGE_CONSTRAINT)
    if actual_identity_error > float(identity_tolerance):
        failed.append(REJECT_RIGID_IDENTITY_CLOSURE)
    if order_error > float(identity_tolerance):
        failed.append(REJECT_RIGID_IDENTITY_CLOSURE)

    def wrench_ld(generalized):
        return _wrench(np.asarray(generalized, dtype=np.float64), rotation_scale_mm)

    raw_wrench = basis_ld.T @ original
    gauge_wrench = basis_ld.T @ (basis_ld @ multiplier_ld)
    p_wrench = basis_ld.T @ loads_ld
    rows = lambda x: [wrench_ld(x[:, j]) for j in range(x.shape[1])]
    return {
        "status": PASS_ELASTIC_QUOTIENT_SCREEN if not failed else failed[0],
        "failed_gates": failed,
        "operator": operator,
        "force_residual_scale_N": float(force_scale),
        "max_KKT_upper_force_residual_N": float(np.max(np.abs(upper))),
        "KKT_upper_force_residual_relative": kkt_relative,
        "KKT_upper_force_relative_limit": kkt_force_rel_limit,
        "max_projected_elastic_force_residual_N": float(np.max(np.abs(projected))),
        "projected_elastic_force_residual_relative": projected_relative,
        "projected_elastic_force_relative_limit": projected_force_rel_limit,
        "max_gauge_R_transpose_u_mm": gauge_max,
        "gauge_atol_mm": gauge_atol_mm,
        "max_abs_original_Ku_minus_p_N": float(np.max(np.abs(original))),
        "original_Ku_minus_p_body_wrenches": rows(raw_wrench),
        "max_abs_R_transpose_original_Ku_minus_p_scaled_N": float(np.max(np.abs(raw_wrench))),
        "p_body_wrenches": rows(p_wrench),
        "R_transpose_p_scaled_N": np.asarray(p_wrench, dtype=np.float64).tolist(),
        "lambda_scaled_N": np.asarray(multiplier_ld, dtype=np.float64).tolist(),
        "R_transpose_R_lambda_body_wrenches": rows(gauge_wrench),
        "legacy_zero_lambda_gate": {
            "status": "PASS" if legacy_lambda_max <= legacy_lambda_atol_N else "FAIL",
            "max_abs_lambda_scaled_N": legacy_lambda_max,
            "atol_N": legacy_lambda_atol_N,
            "gates_quotient_status": False,
        },
        "rigid_identity_closure": {
            "max_abs_actual_RtKu_plus_RtRlambda_minus_Rtp_N": actual_identity_error,
            "actual_identity_tolerance_N": float(identity_tolerance),
            "max_abs_order_difference_N": order_error,
            "max_abs_R_transpose_KKT_residual_N": float(np.max(np.abs(identity_lhs))),
            "max_abs_R_transpose_Ku_N": float(np.max(np.abs(rt_ku))),
            "max_abs_R_transpose_R_lambda_N": float(np.max(np.abs(gram_lambda))),
            "max_abs_R_transpose_p_N": float(np.max(np.abs(rt_p))),
            "atol_N": identity_atol_N,
            "rtol": identity_rtol,
        },
        "projection_used_to_repair_physical_load": False,
        "physical_response_accepted": False,
    }


def audit_quotient_operator(
    K: sp.spmatrix | np.ndarray,
    R: np.ndarray,
    rigid_leakage_rel_limit: float = RIGID_LEAKAGE_REL_LIMIT,
) -> dict:
    """Check the induced-infinity rigid leakage of the frozen stiffness.

    The screen is numerical, not a certified bound on pre-export assembly
    error. K is never modified or lifted.
    """
    matrix = sp.csr_matrix(K, dtype=np.float64)
    basis = np.asarray(R, dtype=np.float64)
    n = matrix.shape[0]
    if matrix.shape != (n, n) or basis.shape != (n, 6):
        raise ValueError("K and R must have shapes (n,n) and (n,6)")
    if not np.all(np.isfinite(matrix.data)) or not np.all(np.isfinite(basis)):
        raise ValueError("K and R must be finite")
    if rigid_leakage_rel_limit <= 0.0:
        raise ValueError("rigid leakage limit must be positive")
    matrix_ld = matrix.astype(np.longdouble)
    basis_ld = np.asarray(basis, dtype=np.longdouble)
    KR = matrix_ld @ basis_ld
    k_inf = np.max(np.asarray(np.abs(matrix_ld).sum(axis=1)).reshape(-1))
    r_inf = np.max(np.sum(np.abs(basis_ld), axis=1))
    kr_inf = np.max(np.sum(np.abs(KR), axis=1))
    relative = kr_inf / max(k_inf * r_inf, np.finfo(np.longdouble).tiny)
    return {
        "status": PASS_ELASTIC_QUOTIENT_SCREEN if relative <= rigid_leakage_rel_limit
        else REJECT_RIGID_LEAKAGE_LIMIT,
        "K_inf_N_per_mm": float(k_inf),
        "R_inf": float(r_inf),
        "KR_inf_N_per_mm": float(kr_inf),
        "relative_KR_inf": float(relative),
        "relative_KR_inf_definition": "max-row-sum(abs(K @ R)) / (max-row-sum(abs(K)) * max-row-sum(abs(R)))",
        "rigid_leakage_rel_limit": rigid_leakage_rel_limit,
        "limit_is_numerical_screen_not_assembly_error_bound": True,
    }


def _balance_records(
    R: np.ndarray,
    loads: np.ndarray,
    rotation_scale_mm: float,
    atol_N: float,
    rtol: float,
) -> tuple[np.ndarray, list[dict], np.ndarray, np.ndarray]:
    generalized = R.T @ loads
    records = [_wrench(generalized[:, j], rotation_scale_mm)
               for j in range(loads.shape[1])]
    thresholds = np.asarray([
        atol_N + rtol * max(1.0, float(np.linalg.norm(loads[:, j], ord=1)))
        for j in range(loads.shape[1])
    ])
    is_balanced = np.max(np.abs(generalized), axis=0) <= thresholds
    return generalized, records, thresholds, is_balanced


def audit_quotient_solution(
    K: sp.spmatrix | np.ndarray,
    R: np.ndarray,
    p: np.ndarray,
    u: np.ndarray,
    lam: np.ndarray,
    *,
    rotation_scale_mm: float = DEFAULT_ROTATION_SCALE_MM,
    rigid_leakage_rel_limit: float = RIGID_LEAKAGE_REL_LIMIT,
    kkt_force_rel_limit: float = KKT_FORCE_REL_LIMIT,
    projected_force_rel_limit: float = PROJECTED_FORCE_REL_LIMIT,
    gauge_atol_mm: float = GAUGE_ATOL_MM,
    identity_atol_N: float = IDENTITY_ATOL_N,
    identity_rtol: float = IDENTITY_RTOL,
    balance_atol_N: float = BALANCE_ATOL_N,
    balance_rtol: float = BALANCE_RTOL,
    legacy_lambda_atol_N: float = LEGACY_LAMBDA_ATOL_N,
    operator_report: dict | None = None,
) -> dict:
    """Audit KKT and quotient equations, retaining original residuals/lambda.

    ``p`` is a balanced RHS column (or columns), such as a projected connector
    basis load. This routine does not accept projection as a repair for an
    unbalanced physical load.
    """
    matrix = sp.csr_matrix(K, dtype=np.float64)
    basis = np.asarray(R, dtype=np.float64)
    loads = np.asarray(p, dtype=np.float64)
    disp = np.asarray(u, dtype=np.float64)
    multiplier = np.asarray(lam, dtype=np.float64)
    vector_input = loads.ndim == 1
    if vector_input:
        loads = loads[:, None]
        disp = disp[:, None] if disp.ndim == 1 else disp
        multiplier = multiplier[:, None] if multiplier.ndim == 1 else multiplier
    n = matrix.shape[0]
    if (matrix.shape != (n, n) or basis.shape != (n, 6)
            or loads.ndim != 2 or loads.shape[0] != n
            or disp.shape != loads.shape or multiplier.shape != (6, loads.shape[1])):
        raise ValueError("K, R, p, u, and lambda shapes do not agree")
    if not all(np.all(np.isfinite(x)) for x in (matrix.data, basis, loads, disp, multiplier)):
        raise ValueError("K, R, p, u, and lambda must be finite")
    if not np.isfinite(rotation_scale_mm) or rotation_scale_mm <= 0.0:
        raise ValueError("rotation_scale_mm must be positive and finite")

    operator = (audit_quotient_operator(matrix, basis, rigid_leakage_rel_limit)
                if operator_report is None else operator_report)
    generalized_p, p_wrenches, balance_thresholds, balanced = _balance_records(
        basis, loads, rotation_scale_mm, balance_atol_N, balance_rtol)
    if not np.all(balanced):
        return {
            "status": REJECT_UNBALANCED_BODY_WRENCH,
            "failed_gates": [REJECT_UNBALANCED_BODY_WRENCH],
            "balanced_columns": balanced.tolist(),
            "p_body_wrenches": p_wrenches,
            "p_balance_threshold_N": balance_thresholds.tolist(),
            "operator": operator,
            "projection_used_to_repair_physical_load": False,
            "physical_response_accepted": False,
        }

    Q, _ = np.linalg.qr(basis, mode="reduced")
    if Q.shape != (n, 6) or np.linalg.matrix_rank(basis) != 6:
        raise ValueError("R must have six independent columns")
    ld = np.longdouble
    matrix_ld = matrix.astype(ld)
    basis_ld = np.asarray(basis, dtype=ld)
    loads_ld = np.asarray(loads, dtype=ld)
    disp_ld = np.asarray(disp, dtype=ld)
    multiplier_ld = np.asarray(multiplier, dtype=ld)
    Q_ld = np.asarray(Q, dtype=ld)
    report = _longdouble_audit(
        matrix_ld, basis_ld, Q_ld, loads_ld, disp_ld, multiplier_ld,
        rotation_scale_mm, operator,
        kkt_force_rel_limit=kkt_force_rel_limit,
        projected_force_rel_limit=projected_force_rel_limit,
        gauge_atol_mm=gauge_atol_mm,
        identity_atol_N=identity_atol_N,
        identity_rtol=identity_rtol,
        legacy_lambda_atol_N=legacy_lambda_atol_N,
    )
    report["balanced_columns"] = balanced.tolist()
    report["p_balance_threshold_N"] = balance_thresholds.tolist()
    return report


def solve_quotient_chunk(
    factor,
    system: sp.spmatrix | np.ndarray,
    K: sp.spmatrix | np.ndarray,
    R: np.ndarray,
    p: np.ndarray,
    **audit_options,
) -> dict:
    """Solve balanced quotient RHS columns with a caller's original KKT factor.

    No projected or lifted stiffness is factored here. Unbalanced columns are
    rejected before invoking ``factor.solve``; the raw ``R.T @ p`` wrench is
    returned. The caller must separately retain raw physical D/W loads.
    """
    matrix = sp.csr_matrix(K, dtype=np.float64)
    bordered = sp.csc_matrix(system, dtype=np.float64)
    basis = np.asarray(R, dtype=np.float64)
    loads = np.asarray(p, dtype=np.float64)
    vector_input = loads.ndim == 1
    load_matrix = loads[:, None] if vector_input else loads
    n = matrix.shape[0]
    if (matrix.shape != (n, n) or basis.shape != (n, 6)
            or load_matrix.ndim != 2 or load_matrix.shape[0] != n
            or bordered.shape != (n + 6, n + 6)):
        raise ValueError("K, system, R, and p have incompatible shapes")
    if (not np.all(np.isfinite(matrix.data)) or not np.all(np.isfinite(bordered.data))
            or not np.all(np.isfinite(basis)) or not np.all(np.isfinite(load_matrix))):
        return {"status": "REJECT_NONFINITE_INPUT", "factor_called": False,
                "physical_response_accepted": False}
    max_corrections = audit_options.pop("max_corrections", MAX_CORRECTIONS)
    if not isinstance(max_corrections, int) or not 0 <= max_corrections <= MAX_CORRECTIONS:
        raise ValueError("max_corrections must be between zero and five")
    rotation_scale = audit_options.get("rotation_scale_mm", DEFAULT_ROTATION_SCALE_MM)
    balance_atol = audit_options.get("balance_atol_N", BALANCE_ATOL_N)
    balance_rtol = audit_options.get("balance_rtol", BALANCE_RTOL)
    generalized, records, thresholds, balanced = _balance_records(
        basis, load_matrix, rotation_scale, balance_atol, balance_rtol)
    if not np.all(balanced):
        return {
            "status": REJECT_UNBALANCED_BODY_WRENCH,
            "balanced_columns": balanced.tolist(),
            "R_transpose_p_scaled_N": generalized.tolist(),
            "p_body_wrenches": records,
            "p_balance_threshold_N": thresholds.tolist(),
            "factor_called": False,
            "projection_used_to_repair_physical_load": False,
            "physical_response_accepted": False,
        }
    op = audit_options.get("operator_report")
    if op is None:
        op = audit_quotient_operator(
            matrix, basis, audit_options.get("rigid_leakage_rel_limit", RIGID_LEAKAGE_REL_LIMIT))
    if op.get("status") != PASS_ELASTIC_QUOTIENT_SCREEN:
        return {
            "status": REJECT_RIGID_LEAKAGE_LIMIT,
            "balanced_columns": balanced.tolist(),
            "p_body_wrenches": records,
            "operator": op,
            "factor_called": False,
            "projection_used_to_repair_physical_load": False,
            "physical_response_accepted": False,
        }

    # Refine against the same original sparse bordered factor. The quotient
    # gates ignore lambda magnitude but keep it and the full Ku-p residual.
    refiner_path = (Path(__file__).resolve().parent.parent
                    / "current-bordered-refinement-diagnostic-attempt01"
                    / "bounded_refinement.py")
    spec = importlib.util.spec_from_file_location("elastic_quotient_bounded_refinement", refiner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import existing-factor refinement method at {refiner_path}")
    refinement = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(refinement)
    Q, _ = np.linalg.qr(basis, mode="reduced")
    matrix_ld = matrix.astype(np.longdouble)
    basis_ld = np.asarray(basis, dtype=np.longdouble)
    Q_ld = np.asarray(Q, dtype=np.longdouble)
    loads_ld = np.asarray(load_matrix, dtype=np.longdouble)
    opts = {
        "kkt_force_rel_limit": audit_options.get("kkt_force_rel_limit", KKT_FORCE_REL_LIMIT),
        "projected_force_rel_limit": audit_options.get("projected_force_rel_limit", PROJECTED_FORCE_REL_LIMIT),
        "gauge_atol_mm": audit_options.get("gauge_atol_mm", GAUGE_ATOL_MM),
        "identity_atol_N": audit_options.get("identity_atol_N", IDENTITY_ATOL_N),
        "identity_rtol": audit_options.get("identity_rtol", IDENTITY_RTOL),
        "legacy_lambda_atol_N": audit_options.get("legacy_lambda_atol_N", LEGACY_LAMBDA_ATOL_N),
    }

    def gate(candidate, residual_ld):
        x = np.asarray(candidate, dtype=np.float64)
        if x.shape != (n + 6, load_matrix.shape[1]) or not np.all(np.isfinite(x)):
            return False, {"candidate_finite_and_shaped": False}
        report = _longdouble_audit(
            matrix_ld, basis_ld, Q_ld, loads_ld,
            np.asarray(x[:n, :], dtype=np.longdouble),
            np.asarray(x[n:, :], dtype=np.longdouble), rotation_scale, op, **opts)
        return not report["failed_gates"], {
            "quotient_status": report["status"],
            "failed_gates": report["failed_gates"],
            "max_kkt_relative_residual": report["KKT_upper_force_residual_relative"],
            "max_projected_elastic_force_relative": report["projected_elastic_force_residual_relative"],
            "max_gauge_mm": report["max_gauge_R_transpose_u_mm"],
            "max_identity_defect_N": report["rigid_identity_closure"]["max_abs_actual_RtKu_plus_RtRlambda_minus_Rtp_N"],
            "lambda_zero_legacy_gate": report["legacy_zero_lambda_gate"]["status"],
        }

    rhs = np.vstack((load_matrix, np.zeros((6, load_matrix.shape[1]), dtype=np.float64)))
    refined = refinement.refine_existing_factor(
        bordered, factor, rhs, gate, max_corrections=max_corrections)
    solution = refined.get("solution")
    result = {
        "status": refined["status"],
        "refinement_status": refined["status"],
        "corrections": refined.get("corrections", 0),
        "refinement_history": refined.get("history", []),
        "refinement_stop_reason": refined.get("stop_reason"),
        "factor_called": refined.get("corrections", 0) >= 0 and solution is not None,
        "balanced_columns": balanced.tolist(),
        "p_body_wrenches": records,
        "operator": op,
        "projection_used_to_repair_physical_load": False,
        "physical_response_accepted": False,
    }
    if solution is None:
        result.update({"failed_gates": [refined["status"]], "displacement_mm": None})
        return result
    solution = np.asarray(solution, dtype=np.float64)
    report = audit_quotient_solution(
        matrix, basis, load_matrix, solution[:n, :], solution[n:, :],
        rotation_scale_mm=rotation_scale,
        rigid_leakage_rel_limit=audit_options.get("rigid_leakage_rel_limit", RIGID_LEAKAGE_REL_LIMIT),
        operator_report=op, **opts)
    result.update(report)
    result["refinement_status"] = refined["status"]
    result["corrections"] = refined.get("corrections", 0)
    result["refinement_history"] = refined.get("history", [])
    result["refinement_stop_reason"] = refined.get("stop_reason")
    result["factor_called"] = True
    result["displacement_mm"] = solution[:n, 0] if vector_input else solution[:n, :]
    if refined["status"] == refinement.PASS_REFINEMENT and report["status"] == PASS_ELASTIC_QUOTIENT_SCREEN:
        result["status"] = PASS_ELASTIC_QUOTIENT_SCREEN
    else:
        result["status"] = refined["status"]
    result["projection_used_to_repair_physical_load"] = False
    result["physical_response_accepted"] = False
    return result
