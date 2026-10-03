"""Sparse free-body condensation helpers; no finite-element kernel calls."""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
import scipy.linalg
import scipy.sparse as sp
import scipy.sparse.linalg as spla


PASS_RIGID_LIFT_SPD = "PASS_RIGID_LIFT_SPD"
UNRESOLVED_NEAR_SINGULAR = "UNRESOLVED_NEAR_SINGULAR"
REJECT_NOT_POSITIVE_DEFINITE = "REJECT_NOT_POSITIVE_DEFINITE"
REJECT_INVALID_RIGID_BASIS = "REJECT_INVALID_RIGID_BASIS"
REJECT_UNBALANCED_BODY_WRENCH = "REJECT_UNBALANCED_BODY_WRENCH"
PASS_BALANCED_FREE_BODY = "PASS_BALANCED_FREE_BODY"
UNRESOLVED_BORDERED_KKT_RESIDUAL = "UNRESOLVED_BORDERED_KKT_RESIDUAL"
UNRESOLVED_GAUGE_CONSTRAINT = "UNRESOLVED_GAUGE_CONSTRAINT"
UNRESOLVED_GAUGE_MULTIPLIER = "UNRESOLVED_GAUGE_MULTIPLIER"


def rigid_basis(
    labels: Sequence[tuple[int, int]],
    node_xyz: Mapping[int, Sequence[float]],
    rotation_scale_mm: float = 1000.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return centroid, scaled rigid columns R, and orthonormal span Q.

    Generalized rigid coordinates are translations in mm and rotations times
    ``rotation_scale_mm`` in mm. Thus all six coordinates have displacement
    units mm, ``R`` is dimensionless, and rotational entries of ``R.T @ F``
    are moments divided by ``rotation_scale_mm`` (N).
    """
    if not np.isfinite(rotation_scale_mm) or rotation_scale_mm <= 0.0:
        raise ValueError("rotation_scale_mm must be positive and finite")
    ids = sorted({int(node) for node, _ in labels})
    if not ids or any(node not in node_xyz for node in ids):
        raise ValueError("labels must refer to nodes with coordinates")
    xyz = {node: np.asarray(node_xyz[node], dtype=np.float64) for node in ids}
    if any(point.shape != (3,) or not np.all(np.isfinite(point)) for point in xyz.values()):
        raise ValueError("each node coordinate must be a finite 3-vector")
    center = np.mean(np.stack([xyz[node] for node in ids]), axis=0)
    row_for = {(int(node), int(direction)): i for i, (node, direction) in enumerate(labels)}
    if len(row_for) != len(labels):
        raise ValueError("duplicate node-direction labels")
    if set(row_for) != {(node, d) for node in ids for d in (1, 2, 3)}:
        raise ValueError("rigid basis requires exactly directions 1, 2, 3 for each node")
    R = np.zeros((len(labels), 6), dtype=np.float64)
    for node in ids:
        relative = xyz[node] - center
        for d in (1, 2, 3):
            R[row_for[(node, d)], d - 1] = 1.0
        for axis, omega in enumerate(np.eye(3)):
            displacement = np.cross(omega, relative) / rotation_scale_mm
            for d in (1, 2, 3):
                R[row_for[(node, d)], 3 + axis] = displacement[d - 1]
    if np.linalg.matrix_rank(R) != 6:
        raise ValueError("the six source-coordinate rigid modes are not independent")
    Q, _ = np.linalg.qr(R, mode="reduced")
    if Q.shape != (len(labels), 6) or not np.allclose(Q.T @ Q, np.eye(6), rtol=0.0, atol=1.0e-12):
        raise ValueError("could not form an orthonormal rigid span")
    return center, R, Q


def audit_rigid_lift(
    K: sp.spmatrix | np.ndarray,
    R: np.ndarray,
    rcond_floor: float = 1.0e-12,
    rigid_residual_tolerance: float = 1.0e-8,
) -> dict:
    """Audit elastic positivity with one dense body lift and Cholesky.

    Forms ``Khat = K + gamma * Q @ Q.T`` only for the supplied body, where Q
    spans the six source rigid fields and ``gamma = ||K||_infinity``. The lift
    is an audit/gauge device; callers must retain the unmodified K in the
    physical bordered equations. Cholesky success plus LAPACK ``pocon`` gives
    an SPD/conditioning screen, not a proof of source mapping or model validity.
    """
    matrix = sp.csr_matrix(K, dtype=np.float64)
    R = np.asarray(R, dtype=np.float64)
    n = matrix.shape[0]
    if matrix.shape != (n, n) or R.shape != (n, 6) or not np.all(np.isfinite(R)):
        return {"status": REJECT_INVALID_RIGID_BASIS, "reason": "shape_or_finiteness"}
    if not np.all(np.isfinite(matrix.data)):
        return {"status": REJECT_NOT_POSITIVE_DEFINITE, "reason": "nonfinite_stiffness"}
    if not (0.0 < rcond_floor < 1.0):
        raise ValueError("rcond_floor must lie strictly between zero and one")
    asym = matrix - matrix.T
    max_asym = float(np.max(np.abs(asym.data))) if asym.nnz else 0.0
    matrix_scale = float(np.max(np.abs(matrix.data))) if matrix.nnz else 0.0
    symmetry_relative = max_asym / max(matrix_scale, np.finfo(float).tiny)
    if symmetry_relative > 1.0e-11:
        return {
            "status": REJECT_NOT_POSITIVE_DEFINITE,
            "reason": "asymmetric_stiffness",
            "symmetry_relative": symmetry_relative,
        }
    Q, _ = np.linalg.qr(R, mode="reduced")
    if Q.shape != (n, 6) or np.linalg.matrix_rank(R) != 6:
        return {"status": REJECT_INVALID_RIGID_BASIS, "reason": "rank_not_six"}
    row_sums = np.asarray(np.abs(matrix).sum(axis=1)).reshape(-1)
    gamma = float(np.max(row_sums)) if row_sums.size else 0.0
    if not np.isfinite(gamma) or gamma <= 0.0:
        return {"status": REJECT_NOT_POSITIVE_DEFINITE, "reason": "zero_or_nonfinite_scale"}
    rigid_residual = float(
        np.linalg.norm(matrix @ R, ord=np.inf)
        / max(gamma * np.linalg.norm(R, ord=np.inf), np.finfo(float).tiny)
    )
    if rigid_residual > rigid_residual_tolerance:
        return {
            "status": REJECT_INVALID_RIGID_BASIS,
            "reason": "source_rigid_modes_not_in_stiffness_nullspace",
            "rigid_residual_relative": rigid_residual,
            "rigid_residual_tolerance": rigid_residual_tolerance,
        }

    # Allocate only one body's dense audit matrix and overwrite it with L.
    lifted = matrix.toarray()
    qqt = Q @ Q.T
    qqt *= gamma
    lifted += qqt
    del qqt
    one_norm = float(np.linalg.norm(lifted, ord=1))
    try:
        chol = scipy.linalg.cholesky(lifted, lower=True, overwrite_a=True, check_finite=False)
    except scipy.linalg.LinAlgError as exc:
        return {
            "status": REJECT_NOT_POSITIVE_DEFINITE,
            "reason": "cholesky_failure",
            "gamma_N_per_mm": gamma,
            "rigid_residual_relative": rigid_residual,
            "cholesky_error": str(exc),
            "symmetry_relative": symmetry_relative,
        }
    pocon = scipy.linalg.lapack.get_lapack_funcs("pocon", (chol,))
    reciprocal_condition, info = pocon(chol, one_norm, uplo="L")
    reciprocal_condition = float(reciprocal_condition)
    if info != 0 or not np.isfinite(reciprocal_condition):
        status = UNRESOLVED_NEAR_SINGULAR
        reason = "condition_estimate_failed"
    elif reciprocal_condition < rcond_floor:
        status = UNRESOLVED_NEAR_SINGULAR
        reason = "reciprocal_condition_below_floor"
    else:
        status = PASS_RIGID_LIFT_SPD
        reason = "cholesky_and_condition_floor_passed"
    return {
        "status": status,
        "reason": reason,
        "gamma_N_per_mm": gamma,
        "rigid_residual_relative": rigid_residual,
        "symmetry_relative": symmetry_relative,
        "cholesky_succeeded": True,
        "reciprocal_condition_1_estimate": reciprocal_condition,
        "rcond_floor": rcond_floor,
        "pocon_info": int(info),
        "dimension": int(n),
        "dense_lift_bytes": int(n * n * np.dtype(np.float64).itemsize),
    }


def factor_bordered(
    K: sp.spmatrix | np.ndarray,
    R: np.ndarray,
) -> tuple[spla.SuperLU, sp.csc_matrix]:
    """Factor the unmodified sparse free-body system ``[K R; R.T 0]``."""
    matrix = sp.csc_matrix(K, dtype=np.float64)
    R = np.asarray(R, dtype=np.float64)
    n = matrix.shape[0]
    if matrix.shape != (n, n) or R.shape != (n, 6):
        raise ValueError("K and R have incompatible shapes")
    if not np.all(np.isfinite(R)) or not np.all(np.isfinite(matrix.data)):
        raise ValueError("K and R must be finite")
    R_sparse = sp.csc_matrix(R)
    border = sp.csc_matrix((6, 6), dtype=np.float64)
    system = sp.bmat([[matrix, R_sparse], [R_sparse.T, border]], format="csc")
    return spla.splu(system), system


def _wrench(generalized: np.ndarray, rotation_scale_mm: float) -> dict:
    return {
        "force_N": generalized[:3].tolist(),
        "moment_about_source_centroid_N_mm": (generalized[3:] * rotation_scale_mm).tolist(),
        "scaled_generalized_load_N": generalized.tolist(),
    }


def solve_bordered_chunk(
    factor: spla.SuperLU,
    system: sp.spmatrix,
    R: np.ndarray,
    loads: np.ndarray,
    rotation_scale_mm: float = 1000.0,
    balance_atol_N: float = 1.0e-10,
    balance_rtol: float = 1.0e-10,
    kkt_residual_tolerance: float = 1.0e-10,
    gauge_constraint_atol_mm: float = 1.0e-10,
    gauge_constraint_rtol: float = 1.0e-10,
    gauge_multiplier_atol_N: float = 1.0e-10,
    gauge_multiplier_rtol: float = 1.0e-10,
) -> dict:
    """Solve balanced RHS columns; reject any body wrench before factor.solve."""
    R = np.asarray(R, dtype=np.float64)
    loads = np.asarray(loads, dtype=np.float64)
    vector_input = loads.ndim == 1
    if vector_input:
        loads = loads[:, None]
    n = R.shape[0]
    if R.shape != (n, 6) or loads.ndim != 2 or loads.shape[0] != n:
        raise ValueError("R and loads have incompatible shapes")
    if not np.all(np.isfinite(R)) or not np.all(np.isfinite(loads)):
        raise ValueError("R and loads must be finite")
    generalized = R.T @ loads
    wrench_records = [_wrench(generalized[:, j], rotation_scale_mm) for j in range(loads.shape[1])]
    thresholds = np.asarray([
        balance_atol_N + balance_rtol * max(1.0, float(np.linalg.norm(loads[:, j], ord=1)))
        for j in range(loads.shape[1])
    ])
    max_components = np.max(np.abs(generalized), axis=0)
    balanced = max_components <= thresholds
    if not np.all(balanced):
        return {
            "status": REJECT_UNBALANCED_BODY_WRENCH,
            "balanced_columns": balanced.tolist(),
            "rigid_generalized_load_N": generalized[:, 0].tolist() if vector_input else generalized.tolist(),
            "body_wrenches": wrench_records,
            "balance_threshold_N": thresholds.tolist(),
            "displacement_mm": None,
            "gauge_multiplier_N": None,
            "gauge_multiplier_used_as_support": False,
            "rigid_wrench_discarded": False,
        }
    rhs = np.vstack((loads, np.zeros((6, loads.shape[1]), dtype=np.float64)))
    solution = factor.solve(rhs)
    residual = system @ solution - rhs
    displacement = solution[:n, :]
    gauge_lambda = solution[n:, :]
    gauge_residual = R.T @ displacement
    # The top block is force equilibrium in N. The bottom block is the
    # displacement gauge in mm, so do not combine their raw norms.
    force_residual_relative = float(
        np.max(np.abs(residual[:n, :])) / max(1.0, float(np.max(np.abs(loads))))
    )
    displacement_scale = max(1.0, float(np.max(np.abs(displacement))))
    load_scale = max(1.0, float(np.max(np.abs(loads))))
    max_gauge_constraint = float(np.max(np.abs(gauge_residual)))
    max_gauge_multiplier = float(np.max(np.abs(gauge_lambda)))
    gauge_constraint_tolerance = gauge_constraint_atol_mm + gauge_constraint_rtol * displacement_scale
    gauge_multiplier_tolerance = gauge_multiplier_atol_N + gauge_multiplier_rtol * load_scale
    if force_residual_relative > kkt_residual_tolerance:
        solve_status = UNRESOLVED_BORDERED_KKT_RESIDUAL
    elif max_gauge_constraint > gauge_constraint_tolerance:
        solve_status = UNRESOLVED_GAUGE_CONSTRAINT
    elif max_gauge_multiplier > gauge_multiplier_tolerance:
        solve_status = UNRESOLVED_GAUGE_MULTIPLIER
    else:
        solve_status = PASS_BALANCED_FREE_BODY
    result = {
        "status": solve_status,
        "balanced_columns": balanced.tolist(),
        "rigid_generalized_load_N": generalized[:, 0].tolist() if vector_input else generalized.tolist(),
        "body_wrenches": wrench_records,
        "max_kkt_relative_residual": force_residual_relative,
        "max_force_balance_relative_residual": force_residual_relative,
        "kkt_residual_tolerance": kkt_residual_tolerance,
        "max_gauge_constraint_mm": max_gauge_constraint,
        "gauge_constraint_tolerance_mm": gauge_constraint_tolerance,
        "max_gauge_multiplier_N": max_gauge_multiplier,
        "gauge_multiplier_tolerance_N": gauge_multiplier_tolerance,
        "gauge_multiplier_used_as_support": False,
        "rigid_wrench_discarded": False,
        "displacement_mm": displacement[:, 0] if vector_input else displacement,
        "gauge_multiplier_N": gauge_lambda[:, 0] if vector_input else gauge_lambda,
    }
    return result


def solve_bordered(
    factor: spla.SuperLU,
    system: sp.spmatrix,
    R: np.ndarray,
    load: np.ndarray,
    rotation_scale_mm: float = 1000.0,
    balance_atol_N: float = 1.0e-10,
    balance_rtol: float = 1.0e-10,
    kkt_residual_tolerance: float = 1.0e-10,
    gauge_constraint_atol_mm: float = 1.0e-10,
    gauge_constraint_rtol: float = 1.0e-10,
    gauge_multiplier_atol_N: float = 1.0e-10,
    gauge_multiplier_rtol: float = 1.0e-10,
) -> dict:
    """Vector convenience wrapper for :func:`solve_bordered_chunk`."""
    return solve_bordered_chunk(
        factor, system, R, load, rotation_scale_mm, balance_atol_N, balance_rtol,
        kkt_residual_tolerance, gauge_constraint_atol_mm, gauge_constraint_rtol,
        gauge_multiplier_atol_N, gauge_multiplier_rtol,
    )
