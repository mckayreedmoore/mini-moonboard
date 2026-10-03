#!/usr/bin/env python3
"""Check the induced-norm propagation from nodal force residual to rigid wrench."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import scipy
import scipy.linalg as la
import scipy.sparse as sp

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parent
CUBE = BASE / "current-free-c3d20-matrix-export-native-attempt01"
ORACLE_DIR = BASE / "current-free-body-elastic-condensation-fixture-attempt01"
PARSER = BASE / "current-native-elastic-operator-export-preflight-attempt01" / "matrix_export_oracle.py"
HELPER = BASE / "current-frame-free-body-condensation-preflight-attempt01" / "condensation.py"
QUOTIENT = BASE / "current-elastic-quotient-method-preflight-attempt01" / "quotient_method.py"
QUOTIENT_ASSESSMENT = BASE / "current-elastic-quotient-method-preflight-attempt01" / "assessment.json"
ROTATION_SCALE_MM = 1000.0
FORCE_REL_TOL = 1.0e-10
GAUGE_ATOL_MM = 2.0e-10
LEGACY_IDENTITY_ATOL_N = 2.0e-10
ORDER_ATOL_N = 1.0e-10
ORDER_RTOL = 1.0e-10


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mod(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def maxabs(x) -> float:
    value = np.asarray(x)
    return float(np.max(np.abs(value))) if value.size else 0.0


def equation_terms(K, R, p, u, lam):
    """Return direct KKT residual and separately contracted six-mode identity."""
    ld = np.longdouble
    Kld = K.astype(ld)
    Rld = np.asarray(R, dtype=ld)
    pld, uld, lld = (np.asarray(x, dtype=ld) for x in (p, u, lam))
    Ku = Kld @ uld
    RtKu = Rld.T @ Ku
    RtRLambda = (Rld.T @ Rld) @ lld
    Rtp = Rld.T @ pld
    nodal = Ku + Rld @ lld - pld
    from_nodal = Rld.T @ nodal
    from_terms = RtKu + RtRLambda - Rtp
    order_defect = from_terms - from_nodal
    return nodal, from_nodal, from_terms, order_defect, (RtKu, RtRLambda, Rtp)


def run() -> dict:
    assessor = mod(CUBE / "assess.py", "wrench_scaling_cube_assessor")
    oracle = mod(ORACLE_DIR / "verify_condensation.py", "wrench_scaling_cube_oracle")
    parser = mod(PARSER, "wrench_scaling_cube_parser")
    helper = mod(HELPER, "wrench_scaling_rigid_helper")
    quotient = mod(QUOTIENT, "wrench_scaling_quotient_method")
    authenticated = assessor.assess()
    saved_assessment = json.loads((CUBE / "assessment.json").read_text())
    if (authenticated != saved_assessment
            or authenticated["status"] != "PASS_FREE_C3D20_MATRIX_EXPORT_ORACLE"):
        raise ValueError("native cube operator assessment did not replay")
    old_oracle = oracle.run()
    if old_oracle != json.loads((ORACLE_DIR / "assessment.json").read_text()):
        raise ValueError("analytic cube traction known answer did not replay")
    if sha(QUOTIENT) != json.loads(QUOTIENT_ASSESSMENT.read_text())["source_sha256"]["quotient_method.py"]:
        raise ValueError("pinned quotient method changed after attempt01 freeze")

    packet = json.loads((CUBE / "model.json").read_text())
    labels = parser.read_dof_map(CUBE / "model.dof")
    dense_k, _ = parser.read_symmetric_triplets(CUBE / "model.sti", len(labels))
    K = sp.csr_matrix(dense_k, dtype=np.float64)
    xyz = {int(node): np.asarray(pos, dtype=np.float64)
           for node, pos in packet["nodes"].items()}
    center, R, Qr = helper.rigid_basis(labels, xyz, ROTATION_SCALE_MM)
    Qe = la.null_space(Qr.T)

    E = float(packet["material"]["E_N_per_mm2"])
    nu = float(packet["material"]["nu"])
    lame = nu * E / ((1.0 + nu) * (1.0 - 2.0 * nu))
    shear = E / (2.0 * (1.0 + nu))
    strains = oracle.strain_basis()
    stresses = [lame * np.trace(eps) * np.eye(3) + 2.0 * shear * eps for eps in strains]
    P = np.column_stack([oracle.face_traction_load(labels, sigma) for sigma in stresses])
    factor, system = helper.factor_bordered(K, R)
    solved = quotient.solve_quotient_chunk(factor, system, K, R, P)
    if solved["status"] != quotient.PASS_ELASTIC_QUOTIENT_SCREEN:
        raise ValueError(f"known balanced traction solve failed: {solved['status']}")

    # ||R.T||_inf is the largest absolute column sum of R. With this helper's
    # 1000 mm rotational scale, all six generalized load coordinates have N
    # units; reported physical moments are those coordinates times 1000 mm.
    Rld = np.asarray(R, dtype=np.longdouble)
    rt_inf = np.max(np.sum(np.abs(Rld), axis=0))
    force_scale = max(1.0, maxabs(P))
    nodal_force_tol = FORCE_REL_TOL * force_scale
    derived_identity_tol = rt_inf * np.longdouble(nodal_force_tol)
    if rt_inf <= 0.0 or derived_identity_tol <= 0.0:
        raise ValueError("induced infinity norm or derived tolerance is invalid")

    U = np.asarray(solved["displacement_mm"], dtype=np.float64)
    Lambda = np.asarray(solved["lambda_scaled_N"], dtype=np.float64)
    nodal, aggregate_nodal, aggregate_terms, order_defect, terms = equation_terms(
        K, R, P, U, Lambda)
    actual_nodal_inf = maxabs(nodal)
    actual_identity_inf = maxabs(aggregate_terms)
    order_error = maxabs(order_defect)
    term_scale = max(1.0, *(maxabs(term) for term in terms))
    order_tolerance = ORDER_ATOL_N + ORDER_RTOL * term_scale
    actual_scale_gate = actual_identity_inf <= float(derived_identity_tol)
    if (actual_nodal_inf > nodal_force_tol or not actual_scale_gate
            or order_error > order_tolerance):
        raise ValueError("solved cube residual failed propagated, nodal, or order gate")

    # Construct an algebraic residual aligned with the row that attains
    # ||R.T||_inf. It reaches 90% of the derived aggregate tolerance while
    # satisfying the unchanged nodal gate, so the old 2e-10 N aggregate-only
    # gate fails even though the propagated gate passes.
    attaining_mode = int(np.argmax(np.sum(np.abs(Rld), axis=0)))
    sign = np.sign(Rld[:, attaining_mode])
    epsilon = np.longdouble(0.9) * np.longdouble(nodal_force_tol)
    constructed_r = epsilon * sign
    constructed_Ku = np.asarray(P[:, 0], dtype=np.longdouble) + constructed_r
    constructed_p = np.asarray(P[:, 0], dtype=np.longdouble)
    constructed_lambda = np.zeros(6, dtype=np.longdouble)
    synthetic_nodal = constructed_Ku + Rld @ constructed_lambda - constructed_p
    synthetic_from_nodal = Rld.T @ synthetic_nodal
    synthetic_from_terms = (Rld.T @ constructed_Ku
                            + (Rld.T @ Rld) @ constructed_lambda
                            - Rld.T @ constructed_p)
    synthetic_order = synthetic_from_terms - synthetic_from_nodal
    synthetic_nodal_inf = maxabs(synthetic_nodal)
    synthetic_aggregate_inf = maxabs(synthetic_from_terms)
    synthetic_order_inf = maxabs(synthetic_order)
    legacy_absolute_status = ("PASS" if synthetic_aggregate_inf <= LEGACY_IDENTITY_ATOL_N
                              else "FAIL")
    derived_status = ("PASS" if synthetic_aggregate_inf <= float(derived_identity_tol)
                      else "FAIL")
    attaining_component = float(synthetic_from_terms[attaining_mode])
    selected_mode_bound = float(np.sum(np.abs(Rld[:, attaining_mode])) * np.longdouble(nodal_force_tol))
    attained_fraction = abs(attaining_component) / selected_mode_bound
    if (synthetic_nodal_inf > nodal_force_tol or derived_status != "PASS"
            or legacy_absolute_status != "FAIL"
            or abs(attained_fraction - 0.9) > 1.0e-9
            or synthetic_order_inf > order_tolerance):
        raise ValueError(f"constructed bound mismatch: nodal={synthetic_nodal_inf}, nodal_tol={nodal_force_tol}, "
                         f"aggregate={synthetic_aggregate_inf}, derived_tol={derived_identity_tol}, "
                         f"derived={derived_status}, old={legacy_absolute_status}, fraction={attained_fraction}, "
                         f"order={synthetic_order_inf}, order_tol={order_tolerance}")

    # A true elastic displacement corruption violates force accuracy while
    # staying in the gauge plane; a rigid displacement corruption violates
    # the unchanged gauge gate while its KR-scale force residual stays small.
    u0 = U[:, 0]
    lam0 = Lambda[:, 0]
    p0 = np.asarray(P[:, 0], dtype=np.float64)
    v = Qe[:, 0]
    q = Qr[:, 0]

    def gates(test_u):
        r, _, _, _, _ = equation_terms(K, R, p0, test_u, lam0)
        force_rel = maxabs(r) / force_scale
        gauge = maxabs(Rld.T @ np.asarray(test_u, dtype=np.longdouble))
        return {
            "force_residual_relative": force_rel,
            "force_gate": force_rel <= FORCE_REL_TOL,
            "gauge_max_mm": gauge,
            "gauge_gate": gauge <= GAUGE_ATOL_MM,
        }

    force_corrupt = gates(u0 + 1.0e-4 * v)
    gauge_corrupt = gates(u0 + 1.0e-4 * q)
    if force_corrupt["force_gate"] or not force_corrupt["gauge_gate"]:
        raise ValueError("elastic corruption did not fail only the force gate")
    if not gauge_corrupt["force_gate"] or gauge_corrupt["gauge_gate"]:
        raise ValueError("rigid corruption did not fail only the gauge gate")

    # Convert the scaled generalized wrench to physical force and moment units.
    generalized_moment_scale = ROTATION_SCALE_MM
    return {
        "schema": "rigid_wrench_residual_scaling_fixture/v1",
        "status": "PASS_RIGID_WRENCH_RESIDUAL_SCALING_FIXTURE",
        "source_sha256": {
            "verify_scaling.py": sha(Path(__file__)),
            "native_cube_sti": sha(CUBE / "model.sti"),
            "native_cube_dof": sha(CUBE / "model.dof"),
            "native_cube_freeze": sha(CUBE / "freeze.json"),
            "native_cube_assessment": sha(CUBE / "assessment.json"),
            "quotient_method_attempt01": sha(QUOTIENT),
            "quotient_assessment_attempt01": sha(QUOTIENT_ASSESSMENT),
            "cube_oracle": sha(ORACLE_DIR / "verify_condensation.py"),
            "cube_parser": sha(PARSER),
            "rigid_helper": sha(HELPER),
        },
        "known_cube": {
            "equations": len(labels),
            "nodes": 20,
            "balanced_analytic_face_traction_columns": int(P.shape[1]),
            "loads_formed_as_K_times_u": False,
            "center_mm": center.tolist(),
            "force_scale_N": force_scale,
            "nodal_force_relative_tolerance": FORCE_REL_TOL,
            "nodal_force_absolute_tolerance_N": nodal_force_tol,
            "max_actual_nodal_KKT_residual_N": actual_nodal_inf,
            "actual_aggregate_identity_max_scaled_N": actual_identity_inf,
            "derived_identity_tolerance_scaled_N": float(derived_identity_tol),
            "actual_derived_identity_gate": "PASS",
            "old_absolute_identity_tolerance_N": LEGACY_IDENTITY_ATOL_N,
            "old_absolute_identity_gate": "PASS" if actual_identity_inf <= LEGACY_IDENTITY_ATOL_N else "FAIL",
            "max_order_defect_N": order_error,
            "order_defect_tolerance_N": order_tolerance,
            "order_defect_gate": "PASS",
        },
        "induced_infinity_bound": {
            "matrix_norm": "||R.T||_infinity = max_j sum_i |R[i,j]|",
            "R_transpose_inf": float(rt_inf),
            "inequality": "||R.T r||_infinity <= ||R.T||_infinity * ||r||_infinity",
            "derived_tolerance": "||R.T||_infinity * (1e-10 * max(1 N, ||p||_infinity))",
            "constructed_residual_mode": attaining_mode,
            "constructed_residual_nodal_inf_N": synthetic_nodal_inf,
            "constructed_residual_nodal_gate": "PASS",
            "constructed_aggregate_scaled_N": synthetic_aggregate_inf,
            "constructed_aggregate_bound_scaled_N": float(derived_identity_tol),
            "attaining_coordinate_bound_scaled_N": selected_mode_bound,
            "constructed_attained_component_scaled_N": attaining_component,
            "constructed_fraction_of_derived_bound": attained_fraction,
            "derived_aggregate_gate": derived_status,
            "old_2e-10N_absolute_aggregate_gate": legacy_absolute_status,
            "constructed_order_defect_N": synthetic_order_inf,
            "constructed_order_gate": "PASS",
        },
        "units_and_sign": {
            "nodal_r": "K u + R lambda - p, force residual in N",
            "aggregate": "R.T r; first three generalized coordinates are N; scaled rotational coordinates are also N",
            "physical_moment_conversion": f"multiply each rotational generalized coordinate by {generalized_moment_scale:g} mm to report N mm",
            "KKT_multiplier_sign": "R lambda is added to K u - p in the top residual",
            "bound_applies_to": "scaled generalized coordinates in the selected rigid basis",
        },
        "negative_fixtures": {
            "elastic_force_corruption": force_corrupt,
            "rigid_gauge_corruption": gauge_corrupt,
        },
        "disposition": {
            "nodal_force_gate_changed": False,
            "physical_native_force_or_moment_tolerances_changed": False,
            "old_absolute_aggregate_result_retained_as_diagnostic": True,
            "order_defect_checked_separately": True,
            "all_300_global_Dt_f_equals_W_checks_changed": False,
            "full_frame_computed": False,
            "actual_frame_body_factor_or_solve_performed": False,
            "native_run_performed": False,
            "mechanical_acceptance": False,
        },
        "limits": [
            "This proves a norm propagation rule on one authenticated cube and a constructed residual, not a new actual-frame response.",
            "The scale is a numerical residual tolerance; it does not relax the nodal force residual, gauge, order-consistency, raw D.T f = W, or native force/moment checks.",
            "No current-frame H, physical state, native run, or mechanical acceptance is established.",
        ],
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    result = run()
    target = HERE / "assessment.json"
    if args.verify:
        if json.loads(target.read_text()) != result:
            raise SystemExit("stored wrench-scaling fixture does not replay")
        print("PASS_REPLAY_RIGID_WRENCH_RESIDUAL_SCALING_FIXTURE")
    else:
        target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
