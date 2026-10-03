#!/usr/bin/env python3
"""Audit the saved kicker_left iterate against rigid and elastic equations."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import tarfile
from pathlib import Path

import numpy as np
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
ARCHIVE = Path("/tmp/ccx_2.23.src.tar.bz2")
ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
MATRIXSTORAGE_MEMBER = "./CalculiX/ccx_2.23/src/matrixstorage.c"
MATRIXSTORAGE_SHA256 = "2b2a502637761a7663e50e43a7f5afe9322c6c775aa6c44fd7b433976bbe59c4"
PARENT = BASE / "current-frame-connector-compliance-attempt02"
CUBE = BASE / "current-free-c3d20-matrix-export-native-attempt01"
CUBE_ORACLE = BASE / "current-free-body-elastic-condensation-fixture-attempt01"
CUBE_PARSER = BASE / "current-native-elastic-operator-export-preflight-attempt01" / "matrix_export_oracle.py"
BODY_AUDIT = BASE / "current-frame-body-elastic-positivity-audit-attempt01" / "assessment.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(value)
    return value


def maxabs(value) -> float:
    return float(np.max(np.abs(value))) if np.size(value) else 0.0


def infinity_norm(matrix) -> float:
    return float(np.max(np.asarray(np.abs(matrix).sum(axis=1)).reshape(-1)))


def row_sum_infinity(value) -> float:
    return float(np.max(np.sum(np.abs(value), axis=1)))


def decimal_writer_rounding_bound(matrix: sp.spmatrix, basis: np.ndarray) -> dict:
    """Bound coefficient serialization error for %20.13e, not assembly error."""
    matrix = sp.csr_matrix(matrix, dtype=np.float64)
    if not np.all(np.isfinite(matrix.data)):
        raise ValueError("non-finite matrix coefficient")
    decimals = [format(float(value), ".13e") for value in matrix.data]
    exponents = np.asarray([int(value.rsplit("e", 1)[1]) for value in decimals], dtype=np.int32)
    # Thirteen fractional digits in scientific notation give fourteen
    # significant decimal digits; half a last-place unit bounds rounding.
    per_entry = 0.5 * np.power(10.0, exponents.astype(np.float64) - 13.0)
    error_pattern = matrix.copy()
    error_pattern.data = per_entry
    matrix_inf = infinity_norm(matrix)
    error_inf_bound = infinity_norm(error_pattern)
    basis_inf = float(np.linalg.norm(basis, ord=np.inf))
    return {
        "format": "%20.13e",
        "significant_decimal_digits": 14,
        "nonzero_coefficients": int(matrix.nnz),
        "max_entry_relative_rounding_bound": 5.0e-14,
        "coefficient_matrix_inf_norm": matrix_inf,
        "coefficient_rounding_matrix_inf_norm_bound": error_inf_bound,
        "relative_matrix_inf_norm_bound": error_inf_bound / max(matrix_inf, np.finfo(float).tiny),
        "basis_inf_norm": basis_inf,
        "induced_KR_inf_norm_bound": error_inf_bound * basis_inf,
        "observed_KR_inf_norm": None,
        "scope": "Decimal text serialization only; does not bound prior finite-element assembly error or prove it is the sole source of observed leakage.",
    }


def cube_known_answer() -> dict:
    oracle = module(CUBE_ORACLE / "verify_condensation.py", "kicker_cube_known_answer")
    replayed = oracle.run()
    saved = json.loads((CUBE_ORACLE / "assessment.json").read_text())
    if replayed != saved:
        raise ValueError("authenticated cube known-answer fixture does not replay")
    parser = module(CUBE_PARSER, "kicker_cube_matrix_parser")
    helper = module(BASE / "current-frame-free-body-condensation-preflight-attempt01" / "condensation.py",
                    "kicker_cube_rigid_helper")
    packet = json.loads((CUBE / "model.json").read_text())
    labels = parser.read_dof_map(CUBE / "model.dof")
    stiffness, _ = parser.read_symmetric_triplets(CUBE / "model.sti", len(labels))
    _, R, _ = helper.rigid_basis(labels, {int(k): v for k, v in packet["nodes"].items()}, 1000.0)
    K = sp.csr_matrix(stiffness)
    K_ld = K.astype(np.longdouble)
    R_ld = np.asarray(R, dtype=np.longdouble)
    KR = K_ld @ R_ld
    gamma = infinity_norm(K)
    rel_inf = row_sum_infinity(KR) / (gamma * float(np.linalg.norm(R, ord=np.inf)))
    rounding = decimal_writer_rounding_bound(K, R)
    rounding["observed_KR_inf_norm"] = row_sum_infinity(KR)
    return {
        "status": saved["status"],
        "native_free_cube_stiffness_sha256": sha(CUBE / "model.sti"),
        "native_free_cube_dof_sha256": sha(CUBE / "model.dof"),
        "relative_rigid_residual_inf_common_metric": rel_inf,
        "saved_oracle_relative_rigid_residual_2norm": saved["projected_inverse"]["rigid_residual_relative"],
        "known_answer_max_Ku_minus_F_relative": saved["constant_stress_traction_known_answer"]["max_Ku_minus_F_relative"],
        "known_answer_max_cross_energy_error_N_mm": saved["constant_stress_traction_known_answer"]["max_cross_energy_error_N_mm"],
        "writer_rounding_bound": rounding,
        "scope": "Small authenticated known-answer only; evidence that the pinned decimal writer coexists with an accurate cube oracle, not acceptance of frame-body KKT multipliers.",
    }


def run() -> dict:
    packet = json.loads((HERE / "packet.json").read_text())
    parent_result = json.loads((HERE / "parent-result.json").read_text())
    parent = PARENT / "assessment.json"
    attempt = json.loads(parent.read_text())
    numerical = attempt["stopping_gate"]["numerical_result"]
    parent_inputs = json.loads((PARENT / "inputs.json").read_text())
    if packet["status"] != "PASS_EXACT_KICKER_CHUNK_PREPARED_NO_SOLVE":
        raise ValueError("exact source-bound packet status changed")
    if parent_result["packet_sha256"] != sha(HERE / "packet.json"):
        raise ValueError("parent solve result does not pin this exact packet")
    if parent_result["iterate_sha256"] != sha(HERE / "parent-iterate.npz"):
        raise ValueError("saved iterate hash differs from parent result")
    if parent_result["status"] != "UNRESOLVED_REFINEMENT_STAGNATION":
        raise ValueError("parent exact replay status changed")
    if parent_result["history"] != numerical["history"]:
        raise ValueError("saved parent replay history differs from immutable attempt02 result")
    for rel, expected in parent_inputs["source_sha256"].items():
        if sha(ROOT / rel) != expected:
            raise ValueError(f"parent source pin changed: {rel}")

    K64 = sp.load_npz(HERE / "body-K.npz").tocsr()
    with np.load(HERE / "basis.npz", allow_pickle=False) as z:
        R64, Q64, projected64 = (z[k].copy() for k in ("R", "Q", "projected"))
    with np.load(HERE / "parent-iterate.npz", allow_pickle=False) as z:
        u64, lambda64 = (z[k].copy() for k in ("displacement_mm", "gauge_multiplier_N"))
    for name, expected in (("body-K.npz", packet["body_K_sha256"]),
                           ("basis.npz", packet["basis_sha256"]),
                           ("source-rows.json", packet["source_rows_sha256"])):
        if sha(HERE / name) != expected:
            raise ValueError(f"source-bound packet member changed: {name}")
    if K64.shape != (1515, 1515) or R64.shape != (1515, 6) or projected64.shape != (1515, 16):
        raise ValueError("exact stopped-chunk packet shapes changed")
    if u64.shape != projected64.shape or lambda64.shape != (6, 16):
        raise ValueError("saved parent iterate shapes changed")

    ld = np.longdouble
    K = K64.astype(ld)
    R = np.asarray(R64, dtype=ld)
    Q = np.asarray(Q64, dtype=ld)
    p = np.asarray(projected64, dtype=ld)
    u = np.asarray(u64, dtype=ld)
    lam = np.asarray(lambda64, dtype=ld)
    ku = K @ u
    kr = K @ R
    gram = R.T @ R
    rtku = R.T @ ku
    gram_lambda = gram @ lam
    rtp = R.T @ p
    top = ku + R @ lam - p
    rt_top = R.T @ top
    identity_defect = rtku + gram_lambda - rtp
    krtu = kr.T @ u
    krtu_difference = rtku - krtu
    gauge = R.T @ u

    # The small 6x6 Gram reconstruction checks the multiplier identity only;
    # no physical-body inverse or response is computed here.
    lambda_from_operator = np.linalg.solve(
        np.asarray(gram, dtype=np.float64),
        np.asarray(rtp - rtku, dtype=np.float64),
    )
    lambda_difference = np.asarray(lambda_from_operator, dtype=np.longdouble) - lam
    # Match the parent's independent mixed-precision contraction order as a
    # second replay of the same 6x6 identity; this is not a body solve.
    lambda_from_operator_parent_contraction = np.linalg.solve(
        R64.T @ R64,
        R64.T @ projected64 - np.asarray(kr.T @ u, dtype=np.float64),
    )
    lambda_difference_parent_contraction = lambda_from_operator_parent_contraction - lambda64

    elastic_residual = ku - p
    projected_elastic_residual = elastic_residual - Q @ (Q.T @ elastic_residual)
    force_scale = max(1.0, maxabs(p))
    projected_elastic_relative = maxabs(projected_elastic_residual) / force_scale

    K_asym = K64 - K64.T
    K_asym_max = maxabs(K_asym.data) if K_asym.nnz else 0.0
    rounding = decimal_writer_rounding_bound(K64, R64)
    rounding["observed_KR_inf_norm"] = row_sum_infinity(kr)
    gamma = infinity_norm(K64)
    R_inf = float(np.linalg.norm(R64, ord=np.inf))
    observed_rigid_relative = row_sum_infinity(kr) / (gamma * R_inf)
    body_audit = json.loads(BODY_AUDIT.read_text())
    body_audit_row = next(row for row in body_audit["bodies"] if row["body"] == "kicker_left")

    if ARCHIVE.exists():
        if sha(ARCHIVE) != ARCHIVE_SHA256:
            raise ValueError("source archive hash differs from the pinned CalculiX archive")
        with tarfile.open(ARCHIVE, "r:bz2") as tar:
            member = tar.extractfile(MATRIXSTORAGE_MEMBER)
            if member is None:
                raise ValueError("pinned matrixstorage.c member is absent")
            writer_bytes = member.read()
        writer_sha = hashlib.sha256(writer_bytes).hexdigest()
        writer_lines = writer_bytes.decode("utf-8").splitlines()
        format_lines = {str(i): line.strip() for i, line in enumerate(writer_lines, 1)
                        if "%20.13e" in line and "fprintf" in line}
        if writer_sha != MATRIXSTORAGE_SHA256 or set(format_lines) != {"304", "543"}:
            raise ValueError("pinned matrixstorage.c bytes or expected writer statements changed")
        writer_pin = {
            "archive_path": str(ARCHIVE), "archive_sha256": sha(ARCHIVE),
            "member": MATRIXSTORAGE_MEMBER, "member_sha256": writer_sha,
            "printf_format": "%20.13e", "significant_decimal_digits": 14,
            "writer_statements": format_lines,
            "interpretation": "Serialization permits per-coefficient decimal rounding bounded by half a last-place unit; unknown pre-serialization assembly error is not bounded by this record.",
        }
    else:
        raise ValueError("pinned source archive unavailable")

    G64 = np.asarray(gram, dtype=np.float64)
    pred_lambda = np.asarray(lambda_from_operator, dtype=np.float64)
    max_gram_lambda = maxabs(gram_lambda)
    quotient = {
        "method_under_assessment_only": "P K P u = P p with Q.T u = 0, P = I - Q Q.T",
        "projected_elastic_force_residual_relative": projected_elastic_relative,
        "original_unprojected_KKT_gate_status": parent_result["status"],
        "raw_R_transpose_p_preserved_N": maxabs(rtp),
        "physical_Dt_f_equal_W_contract_preserved_by_existing_frame_method": True,
        "adoption_or_compliance_output": False,
        "qualification": "A distinct elastic quotient method would suppress the frozen matrix's rigid-subspace leakage. Its gate and error accounting need separate review; this diagnostic does not rerun or accept H.",
    }

    return {
        "schema": "kicker_left_rigid_leakage_equation_diagnostic/v1",
        "status": "PASS_OPERATOR_LEAKAGE_EXPLAINS_NONZERO_GAUGE_MULTIPLIER",
        "inputs": {
            "packet_sha256": sha(HERE / "packet.json"),
            "body_K_sha256": sha(HERE / "body-K.npz"),
            "basis_sha256": sha(HERE / "basis.npz"),
            "parent_result_sha256": sha(HERE / "parent-result.json"),
            "parent_iterate_sha256": sha(HERE / "parent-iterate.npz"),
            "attempt02_assessment_sha256": sha(parent),
        },
        "saved_iterate_semantics": parent_result["saved_iterate_semantics"],
        "equation_convention": "A = K u + R lambda - p. Therefore R.T A = R.T K u + (R.T R) lambda - R.T p.",
        "operator_diagnostics": {
            "symmetry_max_abs_N_per_mm": K_asym_max,
            "gamma_inf_N_per_mm": gamma,
            "max_abs_KR_N_per_mm": maxabs(kr),
            "KR_matrix_inf_norm_N_per_mm": row_sum_infinity(kr),
            "relative_KR_inf": observed_rigid_relative,
            "relative_KR_inf_definition": "max-row-sum(KR) / (max-row-sum(|K|) * max-row-sum(|R|)), evaluated in longdouble",
            "body_rigid_lift_audit_relative_reference_float64": body_audit_row["rigid_residual_relative"],
            "packet_prep_original_max_entry_ratio_not_matrix_inf": packet["K_rigid_residual_relative_inf"],
            "max_abs_RtKR_N_per_mm": maxabs(R.T @ kr),
            "max_abs_projected_Rt_p_N": maxabs(rtp),
        },
        "saved_iterate_equation_diagnostics": {
            "max_abs_upper_force_residual_N": maxabs(top),
            "parent_recorded_upper_force_residual_max_N": parent_result["saved_iterate_upper_force_residual_max_N"],
            "max_abs_Rt_u_mm": maxabs(gauge),
            "parent_recorded_gauge_displacement_max_mm": parent_result["saved_iterate_gauge_displacement_max_mm"],
            "max_abs_lambda_N": maxabs(lam),
            "parent_recorded_gauge_multiplier_max_N": parent_result["saved_iterate_gauge_multiplier_max_N"],
            "max_abs_RtKu_N": maxabs(rtku),
            "max_abs_RtRlambda_N": max_gram_lambda,
            "max_abs_RtK_u_plus_RtRlambda_minus_Rtp_N": maxabs(identity_defect),
            "max_abs_Rt_upper_residual_N": maxabs(rt_top),
            "identity_defect_minus_Rt_upper_residual_N": maxabs(identity_defect - rt_top),
            "max_abs_RtKu_minus_KRt_u_N": maxabs(krtu_difference),
            "max_abs_KRt_u_N": maxabs(krtu),
            "max_abs_lambda_from_6x6_rigid_identity_N": maxabs(pred_lambda),
            "max_abs_lambda_prediction_error_N": maxabs(lambda_difference),
            "max_abs_lambda_from_parent_contraction_N": maxabs(lambda_from_operator_parent_contraction),
            "max_abs_parent_contraction_lambda_prediction_error_N": maxabs(lambda_difference_parent_contraction),
            "max_abs_RtKu_plus_RtRlambda_N": maxabs(rtku + gram_lambda),
            "R_transpose_Ku_per_rigid_coordinate_N": np.asarray(rtku, dtype=np.float64).tolist(),
            "R_transpose_R_lambda_per_rigid_coordinate_N": np.asarray(gram_lambda, dtype=np.float64).tolist(),
            "R_transpose_p_per_rigid_coordinate_N": np.asarray(rtp, dtype=np.float64).tolist(),
            "lambda_from_rigid_identity_N": pred_lambda.tolist(),
        },
        "writer_source_pin": writer_pin,
        "writer_rounding_bound_for_kicker_matrix": rounding,
        "known_cube_writer_oracle": cube_known_answer(),
        "quotient_method_alternative": quotient,
        "disposition": {
            "existing_zero_multiplier_gate": "FAILS; retain STOP for attempt02 under its declared method.",
            "attribution": "Saved iterate's multiplier is quantitatively predicted by nonzero K R coupling in the frozen exported K; projected load wrench and KKT residual are negligible in the rigid identity. This is an operator/nullspace representation effect, not evidence of an inaccurate factor solve.",
            "cause_limit": "The 14-significant-digit writer allows enough coefficient error to explain the observed K R scale, and the known cube oracle has comparable roundoff-scale rigid leakage. This does not prove serialization is the sole cause; pre-export finite-element assembly contributions are not available.",
            "next_method_choice": "Stop current KKT route for this chunk. If desired, parent may separately review an elastic quotient solve P K P with Q.T u=0 and explicit projected-residual/error gates, while preserving raw source maps and global D.T f=W balance. Do not treat lambda as support or call this a pass under the original gate.",
            "no_retry_or_native_export_change": True,
        },
        "native_or_full_frame_run": False,
        "physical_response_computed": False,
        "full_H_computed": False,
        "mechanical_acceptance": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = run()
    output = HERE / "equation-assessment.json"
    if args.verify:
        if json.loads(output.read_text()) != result:
            raise SystemExit("equation diagnostic does not replay")
        print("PASS_REPLAY_KICKER_RIGID_LEAKAGE_EQUATION_DIAGNOSTIC")
    else:
        output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(result["status"])


if __name__ == "__main__":
    main()
