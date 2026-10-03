#!/usr/bin/env python3
"""Known-answer preflight for the separate elastic-quotient audit method."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import scipy
import scipy.linalg as la
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
CUBE = BASE / "current-free-c3d20-matrix-export-native-attempt01"
ORACLE_DIR = BASE / "current-free-body-elastic-condensation-fixture-attempt01"
PARSER = BASE / "current-native-elastic-operator-export-preflight-attempt01" / "matrix_export_oracle.py"
HELPER = BASE / "current-frame-free-body-condensation-preflight-attempt01" / "condensation.py"
KICKER = BASE / "current-kicker-rigid-leakage-diagnostic-attempt01"
ROTATION_SCALE_MM = 1000.0


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def maxabs(x) -> float:
    a = np.asarray(x)
    return float(np.max(np.abs(a))) if a.size else 0.0


def run() -> dict:
    qmethod = module(HERE / "quotient_method.py", "elastic_quotient_method")
    helper = module(HELPER, "elastic_quotient_rigid_helper")
    parser = module(PARSER, "elastic_quotient_cube_parser")
    oracle = module(ORACLE_DIR / "verify_condensation.py", "elastic_quotient_cube_oracle")
    authenticated = module(CUBE / "assess.py", "elastic_quotient_cube_assessor").assess()
    saved_auth = json.loads((CUBE / "assessment.json").read_text())
    cube_result = oracle.run()
    saved_cube_result = json.loads((ORACLE_DIR / "assessment.json").read_text())
    if authenticated != saved_auth or authenticated["status"] != "PASS_FREE_C3D20_MATRIX_EXPORT_ORACLE":
        raise ValueError("authenticated native cube export did not replay")
    if cube_result != saved_cube_result or cube_result["status"] != "PASS_FREE_BODY_ELASTIC_CONDENSATION_KNOWN_ANSWER":
        raise ValueError("independent analytic-traction cube oracle did not replay")

    packet = json.loads((CUBE / "model.json").read_text())
    labels = parser.read_dof_map(CUBE / "model.dof")
    dense_k, _ = parser.read_symmetric_triplets(CUBE / "model.sti", len(labels))
    K = sp.csr_matrix(dense_k, dtype=np.float64)
    xyz = {int(node): np.asarray(pos, dtype=np.float64) for node, pos in packet["nodes"].items()}
    center, R, Qr = helper.rigid_basis(labels, xyz, ROTATION_SCALE_MM)
    Qe = la.null_space(Qr.T)
    if K.shape != (60, 60) or R.shape != (60, 6) or Qe.shape != (60, 54):
        raise ValueError("unexpected authenticated C3D20 dimensions")

    # Check the recorded CalculiX decimal writer on every serialized coefficient.
    sti_tokens = [line.split()[2] for line in (CUBE / "model.sti").read_text().splitlines() if line.strip()]
    if not sti_tokens or any(format(float(token), ".13e") != token.lower() for token in sti_tokens):
        raise ValueError("native .sti coefficient tokens do not match the pinned 14-digit decimal writer")
    old_diag = json.loads((KICKER / "equation-assessment.json").read_text())
    writer = old_diag["writer_source_pin"]
    if (writer["printf_format"] != "%20.13e" or writer["significant_decimal_digits"] != 14
            or writer["archive_sha256"] != "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
            or writer["member_sha256"] != "2b2a502637761a7663e50e43a7f5afe9322c6c775aa6c44fd7b433976bbe59c4"):
        raise ValueError("previously authenticated writer-source pin changed")

    young = float(packet["material"]["E_N_per_mm2"])
    nu = float(packet["material"]["nu"])
    lame = nu * young / ((1.0 + nu) * (1.0 - 2.0 * nu))
    shear = young / (2.0 * (1.0 + nu))
    strains = oracle.strain_basis()
    stresses = [lame * np.trace(eps) * np.eye(3) + 2.0 * shear * eps for eps in strains]
    P = np.column_stack([oracle.face_traction_load(labels, sig) for sig in stresses])
    affine = np.column_stack([oracle.affine_field(labels, xyz, center, eps) for eps in strains])
    reduced = Qe.T @ (K @ Qe)
    # This dense 54-DOF solve is the independent reference for the one cube.
    reference = Qe @ la.solve(reduced, Qe.T @ P, assume_a="pos")
    factor, system = helper.factor_bordered(K, R)
    solved = qmethod.solve_quotient_chunk(factor, system, K, R, P)
    if solved["status"] != qmethod.PASS_ELASTIC_QUOTIENT_SCREEN:
        raise ValueError(f"cube bordered quotient solve failed: {solved['status']} {solved['failed_gates']}")
    U = np.asarray(solved["displacement_mm"])
    expected_affine = Qe @ (Qe.T @ affine)
    displacement_rel = float(la.norm(U - reference, np.inf) / max(1.0, la.norm(reference, np.inf)))
    affine_rel = float(la.norm(U - expected_affine, np.inf) / max(1.0, la.norm(expected_affine, np.inf)))
    observed_cross = U.T @ P
    expected_cross = np.asarray([[float(np.sum(strains[i] * stresses[j])) for j in range(6)] for i in range(6)])
    energy_error = float(np.max(np.abs(observed_cross - expected_cross)))
    if max(displacement_rel, affine_rel, energy_error) > 2.0e-9:
        raise ValueError("cube quotient displacement or independent traction-work oracle failed")
    if (solved["KKT_upper_force_residual_relative"] > 1.0e-10
            or solved["projected_elastic_force_residual_relative"] > 1.0e-10
            or solved["max_gauge_R_transpose_u_mm"] > 2.0e-10
            or solved["rigid_identity_closure"]["max_abs_actual_RtKu_plus_RtRlambda_minus_Rtp_N"]
            > solved["rigid_identity_closure"]["actual_identity_tolerance_N"]):
        raise ValueError("cube strict force, gauge, or rigid-identity gate failed")

    # Add only rigid-elastic coupling. Qe.T DeltaK Qe is zero, so the quotient
    # displacement and energy are invariant while original KKT lambda changes.
    q = Qr[:, 0]
    v = Qe[:, 0]
    coupling = np.outer(q, v) + np.outer(v, q)
    k_inf = float(np.max(np.asarray(np.abs(K).sum(axis=1)).reshape(-1)))
    r_inf = float(np.max(np.sum(np.abs(R), axis=1)))
    coupling_kr_inf = float(np.max(np.sum(np.abs(coupling @ R), axis=1)))
    alpha = 2.0e-14 * k_inf * r_inf / max(coupling_kr_inf, np.finfo(float).tiny)
    delta_k = alpha * coupling
    Kpert = sp.csr_matrix(K.toarray() + delta_k)
    projected_delta = Qe.T @ delta_k @ Qe
    projected_delta_rel = float(la.norm(projected_delta, np.inf) / max(1.0, la.norm(reduced, np.inf)))
    pert_factor, pert_system = helper.factor_bordered(Kpert, R)
    pert = qmethod.solve_quotient_chunk(pert_factor, pert_system, Kpert, R, P)
    if pert["status"] != qmethod.PASS_ELASTIC_QUOTIENT_SCREEN:
        raise ValueError(f"deterministic leakage solve failed: {pert['status']} {pert['failed_gates']}")
    Up = np.asarray(pert["displacement_mm"])
    pert_displacement_rel = float(la.norm(Up - reference, np.inf) / max(1.0, la.norm(reference, np.inf)))
    pert_energy_error = float(np.max(np.abs(Up.T @ P - expected_cross)))
    if max(projected_delta_rel, pert_displacement_rel, pert_energy_error) > 2.0e-9:
        raise ValueError("rigid-leakage perturbation changed elastic quotient answer")

    # Deliberate corruptions must be caught by the strict, unrelaxed checks.
    elastic_corrupt = qmethod.audit_quotient_solution(K, R, P, U + 1.0e-4 * v[:, None],
                                                      np.asarray(solved["lambda_scaled_N"]).reshape(6, -1))
    rigid_corrupt = qmethod.audit_quotient_solution(K, R, P, U + 1.0e-4 * q[:, None],
                                                    np.asarray(solved["lambda_scaled_N"]).reshape(6, -1))
    if (qmethod.REJECT_PROJECTED_ELASTIC_FORCE_RESIDUAL not in elastic_corrupt["failed_gates"]
            or qmethod.REJECT_GAUGE_CONSTRAINT not in rigid_corrupt["failed_gates"]):
        raise ValueError("known corrupt elastic or gauge displacement escaped its strict gate")

    # Unbalanced raw point loads are rejected before any solve call. The raw
    # body wrench is retained; no projection is treated as physical balance.
    row = {tuple(label): i for i, label in enumerate(labels)}
    point = np.zeros(60)
    point[row[(1, 1)]] = 1.0

    class SentinelFactor:
        called = False
        def solve(self, rhs):
            self.called = True
            raise AssertionError("unbalanced load reached factor.solve")

    sentinel = SentinelFactor()
    unbalanced = qmethod.solve_quotient_chunk(sentinel, system, K, R, point)
    if (unbalanced["status"] != qmethod.REJECT_UNBALANCED_BODY_WRENCH
            or sentinel.called or unbalanced["factor_called"] is not False):
        raise ValueError("unbalanced raw load was not rejected before factorization")

    # The saved kicker_left chunk illustrates why lambda is now diagnostic:
    # quotient gates pass for this saved iterate, but its original zero-lambda
    # gate still explicitly fails. No new factorization or H is computed.
    saved_K = sp.load_npz(KICKER / "body-K.npz").tocsr()
    with np.load(KICKER / "basis.npz", allow_pickle=False) as data:
        saved_R = data["R"].copy()
        saved_p = data["projected"].copy()
    with np.load(KICKER / "parent-iterate.npz", allow_pickle=False) as data:
        saved_u = data["displacement_mm"].copy()
        saved_lam = data["gauge_multiplier_N"].copy()
    saved_audit = qmethod.audit_quotient_solution(saved_K, saved_R, saved_p, saved_u, saved_lam)
    if (saved_audit["status"] != qmethod.PASS_ELASTIC_QUOTIENT_SCREEN
            or saved_audit["legacy_zero_lambda_gate"]["status"] != "FAIL"
            or saved_audit["legacy_zero_lambda_gate"]["max_abs_lambda_scaled_N"] <= 2.0e-10):
        raise ValueError("saved exact kicker chunk did not preserve quotient-pass / legacy-zero-lambda-fail semantics")

    return {
        "schema": "elastic_quotient_method_known_answer/v1",
        "status": "PASS_ELASTIC_QUOTIENT_METHOD_KNOWN_ANSWER",
        "method": "Original unmodified [K R; R.T 0] solve, audited as a balanced elastic quotient with strict projected force/gauge and induced-infinity KR screens.",
        "source_sha256": {
            "verify_quotient.py": sha(Path(__file__)),
            "quotient_method.py": sha(HERE / "quotient_method.py"),
            "condensation.py": sha(HELPER),
            "bounded_refinement.py": sha(BASE / "current-bordered-refinement-diagnostic-attempt01" / "bounded_refinement.py"),
            "cube_oracle.py": sha(ORACLE_DIR / "verify_condensation.py"),
            "cube_parser.py": sha(PARSER),
            "cube_assessor.py": sha(CUBE / "assess.py"),
            "native_cube_sti": sha(CUBE / "model.sti"),
            "native_cube_dof": sha(CUBE / "model.dof"),
            "native_cube_freeze": sha(CUBE / "freeze.json"),
            "native_cube_assessment": sha(CUBE / "assessment.json"),
            "kicker_equation_assessment": sha(KICKER / "equation-assessment.json"),
        },
        "writer": {
            "source_pin": writer,
            "format_token_check": "%20.13e / 14 significant decimal digits verified against every native cube stiffness coefficient",
            "coefficient_token_count": len(sti_tokens),
            "assembly_roundoff_bound": "Not established; the writer pin bounds decimal serialization only.",
        },
        "known_cube": {
            "dimensions": {"equations": 60, "rigid_modes": 6, "elastic_coordinates": 54},
            "centroid_mm": center.tolist(),
            "balanced_analytic_face_tractions_only": True,
            "loads_formed_as_K_times_displacement": False,
            "operator_status": solved["operator"]["status"],
            "relative_KR_inf": solved["operator"]["relative_KR_inf"],
            "strict_gates": {
                "KKT_relative": solved["KKT_upper_force_residual_relative"],
                "projected_elastic_relative": solved["projected_elastic_force_residual_relative"],
                "gauge_mm": solved["max_gauge_R_transpose_u_mm"],
                "identity_defect_N": solved["rigid_identity_closure"]["max_abs_actual_RtKu_plus_RtRlambda_minus_Rtp_N"],
                "identity_tolerance_N": solved["rigid_identity_closure"]["actual_identity_tolerance_N"],
            },
            "max_reference_displacement_relative": displacement_rel,
            "max_affine_displacement_error_modulo_rigid_relative": affine_rel,
            "cross_energy_error_N_mm": energy_error,
            "original_Ku_minus_p_max_N": solved["max_abs_original_Ku_minus_p_N"],
            "original_Ku_minus_p_body_wrenches": solved["original_Ku_minus_p_body_wrenches"],
            "lambda_max_scaled_N": solved["legacy_zero_lambda_gate"]["max_abs_lambda_scaled_N"],
            "legacy_zero_lambda_gate": solved["legacy_zero_lambda_gate"]["status"],
        },
        "rigid_leakage_perturbation": {
            "construction": "DeltaK = alpha (q v.T + v q.T), q in span(R), v orthogonal to span(R); hence Qe.T DeltaK Qe = 0.",
            "alpha_N_per_mm": float(alpha),
            "projected_delta_K_relative": projected_delta_rel,
            "operator_status": pert["operator"]["status"],
            "relative_KR_inf": pert["operator"]["relative_KR_inf"],
            "max_reference_displacement_relative": pert_displacement_rel,
            "cross_energy_error_N_mm": pert_energy_error,
            "lambda_max_scaled_N": pert["legacy_zero_lambda_gate"]["max_abs_lambda_scaled_N"],
            "legacy_zero_lambda_gate": pert["legacy_zero_lambda_gate"]["status"],
            "same_quotient_answer": True,
        },
        "negative_fixtures": {
            "elastic_corruption_failed_gates": elastic_corrupt["failed_gates"],
            "rigid_gauge_corruption_failed_gates": rigid_corrupt["failed_gates"],
            "unbalanced_point_load_status": unbalanced["status"],
            "unbalanced_point_load_wrench": unbalanced["p_body_wrenches"],
            "unbalanced_factor_called": sentinel.called,
        },
        "saved_kicker_left_diagnostic": {
            "is_new_factorization_or_response": False,
            "quotient_audit_status": saved_audit["status"],
            "relative_KR_inf": saved_audit["operator"]["relative_KR_inf"],
            "max_projected_elastic_force_relative": saved_audit["projected_elastic_force_residual_relative"],
            "max_gauge_mm": saved_audit["max_gauge_R_transpose_u_mm"],
            "max_original_Ku_minus_p_N": saved_audit["max_abs_original_Ku_minus_p_N"],
            "original_Ku_minus_p_body_wrenches": saved_audit["original_Ku_minus_p_body_wrenches"],
            "max_lambda_scaled_N": saved_audit["legacy_zero_lambda_gate"]["max_abs_lambda_scaled_N"],
            "legacy_zero_lambda_gate": saved_audit["legacy_zero_lambda_gate"]["status"],
            "saved_iterate_sha256": sha(KICKER / "parent-iterate.npz"),
            "full_H_computed": False,
        },
        "physical_contract": {
            "raw_source_balance_required": "Retain all 300 source wrench/equilibrium coordinates and require global D.T @ f = W before any physical solve.",
            "projection_scope": "Only balanced projected elastic basis RHS columns are passed to this quotient solve; raw gravity/point-load wrenches remain separate.",
            "native_force_tolerance_N": 0.1,
            "native_moment_tolerance_N_mm": 2.0,
            "these_global_checks_were_recomputed_here": False,
            "mechanical_acceptance": False,
            "physical_response_accepted": False,
            "full_frame_computed": False,
            "native_run_performed": False,
        },
        "limits": [
            "This is a method known-answer fixture on one authenticated isotropic C3D20 cube plus a saved, already rejected kicker chunk.",
            "The 5e-14 induced-infinity KR limit is a numerical screening limit; source formatting does not certify finite-element assembly error.",
            "A passing quotient audit does not set lambda to zero or erase original Ku-p rigid-wrench diagnostics.",
            "No current-frame H, physical state, native run, mechanical acceptance, fabrication, or climbing release is established.",
        ],
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
    }


def main() -> int:
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("--verify", action="store_true")
    args = argp.parse_args()
    result = run()
    target = HERE / "assessment.json"
    if args.verify:
        if json.loads(target.read_text()) != result:
            raise SystemExit("stored quotient-method assessment does not replay exactly")
        print("PASS_REPLAY_ELASTIC_QUOTIENT_METHOD_KNOWN_ANSWER")
    else:
        target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
