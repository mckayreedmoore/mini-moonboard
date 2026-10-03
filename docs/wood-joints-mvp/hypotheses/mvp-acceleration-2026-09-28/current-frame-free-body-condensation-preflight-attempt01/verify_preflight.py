#!/usr/bin/env python3
"""Replay the sparse bordered/rigid-lift condensation known-answer fixture."""

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

from condensation import (
    PASS_BALANCED_FREE_BODY,
    PASS_RIGID_LIFT_SPD,
    REJECT_NOT_POSITIVE_DEFINITE,
    REJECT_UNBALANCED_BODY_WRENCH,
    UNRESOLVED_NEAR_SINGULAR,
    audit_rigid_lift,
    factor_bordered,
    rigid_basis,
    solve_bordered,
    solve_bordered_chunk,
)


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
CUBE = PARENT / "current-free-c3d20-matrix-export-native-attempt01"
KNOWN_ANSWER = PARENT / "current-free-body-elastic-condensation-fixture-attempt01"
KNOWN_ANSWER_SCRIPT = KNOWN_ANSWER / "verify_condensation.py"
PARSER = PARENT / "current-native-elastic-operator-export-preflight-attempt01" / "matrix_export_oracle.py"
ROTATION_SCALE_MM = 1000.0


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run() -> dict:
    # Replay the previously authenticated native cube and independent analytic
    # traction oracle before reusing its K. This does not launch an FE kernel.
    known_answer = load_module(KNOWN_ANSWER_SCRIPT, "free_body_condensation_known_answer")
    upstream_result = known_answer.run()
    saved_upstream = json.loads((KNOWN_ANSWER / "assessment.json").read_text())
    if upstream_result != saved_upstream:
        raise ValueError("authenticated free-body cube fixture no longer replays exactly")

    parser = load_module(PARSER, "free_body_condensation_matrix_parser")
    labels = parser.read_dof_map(CUBE / "model.dof")
    K, _ = parser.read_symmetric_triplets(CUBE / "model.sti", len(labels))
    K = sp.csr_matrix(K, dtype=np.float64)
    if K.shape != (60, 60):
        raise ValueError(f"expected authenticated 60-by-60 cube K, got {K.shape}")
    packet = json.loads((CUBE / "model.json").read_text())
    node_xyz = {int(node): xyz for node, xyz in packet["nodes"].items()}
    center, R, Q = rigid_basis(labels, node_xyz, ROTATION_SCALE_MM)

    base_audit = audit_rigid_lift(K, R)
    if base_audit["status"] != PASS_RIGID_LIFT_SPD:
        raise ValueError(f"known-answer cube did not pass rigid-lift audit: {base_audit}")

    # Reject a deliberately inserted elastic mechanism and a negative elastic
    # direction. This tiny dense eigensolve is fixture-only, never the frame.
    elastic = la.null_space(R.T)
    dense_K = K.toarray()
    reduced = elastic.T @ dense_K @ elastic
    values, vectors = la.eigh(0.5 * (reduced + reduced.T), check_finite=True)
    minimum = float(values[0])
    if minimum <= 0.0:
        raise ValueError(f"authenticated cube elastic fixture is not positive: {minimum}")
    soft_mode = elastic @ vectors[:, 0]
    exact_mechanism = sp.csr_matrix(dense_K - minimum * np.outer(soft_mode, soft_mode))
    negative_mode = sp.csr_matrix(dense_K - 1.2 * minimum * np.outer(soft_mode, soft_mode))
    mechanism_audit = audit_rigid_lift(exact_mechanism, R)
    negative_audit = audit_rigid_lift(negative_mode, R)
    if mechanism_audit["status"] == PASS_RIGID_LIFT_SPD:
        raise ValueError(f"inserted exact elastic mechanism passed the audit: {mechanism_audit}")
    if negative_audit["status"] != REJECT_NOT_POSITIVE_DEFINITE:
        raise ValueError(f"inserted negative elastic mode was not rejected: {negative_audit}")
    if mechanism_audit["status"] not in {UNRESOLVED_NEAR_SINGULAR, REJECT_NOT_POSITIVE_DEFINITE}:
        raise ValueError(f"unexpected exact-mechanism audit state: {mechanism_audit}")

    # Sparse physical solve: factor original K, bordered only by the six gauge
    # columns. All six external loads are integrated analytically as face
    # tractions; none is formed from K times an imposed displacement.
    factor, system = factor_bordered(K, R)
    strains = known_answer.strain_basis()
    youngs = float(packet["material"]["E_N_per_mm2"])
    poisson = float(packet["material"]["nu"])
    lame_lambda = poisson * youngs / ((1.0 + poisson) * (1.0 - 2.0 * poisson))
    shear = youngs / (2.0 * (1.0 + poisson))
    stresses = [lame_lambda * np.trace(eps) * np.eye(3) + 2.0 * shear * eps for eps in strains]
    loads = np.column_stack([known_answer.face_traction_load(labels, stress) for stress in stresses])
    solved = solve_bordered_chunk(factor, system, R, loads, ROTATION_SCALE_MM)
    if solved["status"] != PASS_BALANCED_FREE_BODY:
        raise ValueError(f"balanced analytic traction block was rejected: {solved}")
    response = np.asarray(solved["displacement_mm"])
    affine = np.column_stack([
        known_answer.affine_field(labels, {n: np.asarray(x) for n, x in node_xyz.items()}, center, eps)
        for eps in strains
    ])
    elastic_affine = affine - Q @ (Q.T @ affine)
    displacement_error = float(np.linalg.norm(response - elastic_affine, ord=np.inf)
                               / max(1.0, np.linalg.norm(elastic_affine, ord=np.inf)))
    observed_cross_work = response.T @ loads
    expected_cross_work = np.asarray([
        [float(np.sum(strains[i] * stresses[j])) for j in range(6)]
        for i in range(6)
    ])  # unit cube volume, 1 mm^3
    cross_work_error = float(np.max(np.abs(observed_cross_work - expected_cross_work)))
    traction_wrench_error = float(max(
        np.max(np.abs(np.asarray(wrench["scaled_generalized_load_N"])))
        for wrench in solved["body_wrenches"]
    ))
    if (displacement_error > 2.0e-9 or cross_work_error > 2.0e-9
            or solved["max_kkt_relative_residual"] > 2.0e-10
            or solved["max_gauge_multiplier_N"] > 2.0e-9
            or traction_wrench_error > 2.0e-9):
        raise ValueError("sparse bordered affine traction known answer failed")

    class CorruptFactor:
        """Test double proving the KKT residual gate is active."""

        def solve(self, rhs):
            solution = np.array(factor.solve(rhs), copy=True)
            if solution.ndim == 1:
                solution[0] += 1.0e-4
            else:
                solution[0, 0] += 1.0e-4
            return solution

    corrupt_result = solve_bordered(CorruptFactor(), system, R, loads[:, 0], ROTATION_SCALE_MM)
    if corrupt_result["status"] != "UNRESOLVED_BORDERED_KKT_RESIDUAL":
        raise ValueError(f"corrupt bordered solve bypassed residual gate: {corrupt_result}")

    # A small two-row balanced pair exercises q = B R a + B K+ (F-B.T f).
    row_for = {label: i for i, label in enumerate(labels)}
    selector = np.zeros((2, len(labels)), dtype=np.float64)
    for i, label in enumerate(((1, 1), (2, 1))):
        selector[i, row_for[label]] = 1.0
    source_force = np.asarray([0.7, -0.7])  # body-on-interface, N
    body_load = -selector.T @ source_force
    source_solution = solve_bordered(factor, system, R, body_load, ROTATION_SCALE_MM)
    if source_solution["status"] != PASS_BALANCED_FREE_BODY:
        raise ValueError(f"balanced source-row pair was rejected: {source_solution}")
    rigid_amplitudes_mm = np.asarray([0.10, -0.05, 0.03, 10.0, -15.0, 20.0])
    body_displacement = R @ rigid_amplitudes_mm + source_solution["displacement_mm"]
    source_q = selector @ body_displacement
    kplus = elastic @ la.solve(reduced, elastic.T, assume_a="pos")
    formula_q = selector @ (R @ rigid_amplitudes_mm + kplus @ body_load)
    source_formula_error = float(np.max(np.abs(source_q - formula_q)))
    source_row_work = float(source_force @ source_q)
    nodal_dual_work = float((selector.T @ source_force) @ body_displacement)
    if source_formula_error > 2.0e-10 or abs(source_row_work - nodal_dual_work) > 2.0e-10:
        raise ValueError("sparse bordered two-row condensation identity failed")

    # The unit point load is not free-body equilibrated. The helper must report
    # its wrench and reject before invoking the already-built sparse factor.
    point_load = np.zeros(len(labels), dtype=np.float64)
    point_load[row_for[(1, 1)]] = 1.0
    point_result = solve_bordered(factor, system, R, point_load, ROTATION_SCALE_MM)
    if point_result["status"] != REJECT_UNBALANCED_BODY_WRENCH:
        raise ValueError(f"unbalanced point load was not rejected: {point_result}")
    expected_point_wrench = np.asarray([1.0, 0.0, 0.0, 0.0, -0.5, 0.5])
    observed_point_wrench = np.asarray(
        point_result["body_wrenches"][0]["force_N"]
        + point_result["body_wrenches"][0]["moment_about_source_centroid_N_mm"]
    )
    if not np.allclose(observed_point_wrench, expected_point_wrench, rtol=0.0, atol=1.0e-12):
        raise ValueError(f"unbalanced point-load wrench mismatch: {point_result}")

    frame_dir = PARENT / "current-frame-pure-solid-matrix-export-native-attempt01"
    projection_dir = PARENT / "current-frame-physical-connector-projection-contract-attempt01"
    frame_assessment = json.loads((frame_dir / "assessment.json").read_text())
    execution = json.loads((frame_dir / "execution.json").read_text())
    index_map = json.loads((projection_dir / "physical-index-map.json").read_text())
    projection_contract = json.loads((projection_dir / "projection-contract.json").read_text())
    body_nodes: dict[str, int] = {}
    for record in index_map:
        body_nodes[record["body"]] = body_nodes.get(record["body"], 0) + 1
    body_dofs = sorted((3 * count for count in body_nodes.values()), reverse=True)
    if (len(body_nodes) != 50 or sum(body_dofs) != 37647
            or frame_assessment["stiffness"]["dimension"] != 37647
            or frame_assessment["body_rigid_mode_screen"]["full_stiffness_rank_claimed"]):
        raise ValueError("current-frame source inventory or assessment does not match expected scope")

    return {
        "status": "PASS_SPARSE_FREE_BODY_CONDENSATION_PREFLIGHT_FIXTURE",
        "helper_source_sha256": digest(HERE / "condensation.py"),
        "fixture_source_sha256": digest(Path(__file__)),
        "known_answer_fixture_sha256": digest(KNOWN_ANSWER_SCRIPT),
        "authenticated_free_cube": {
            "native_freeze_sha256": digest(CUBE / "freeze.json"),
            "native_execution_sha256": digest(CUBE / "execution.json"),
            "native_assessment_sha256": digest(CUBE / "assessment.json"),
            "stiffness_sha256": digest(CUBE / "model.sti"),
            "dof_sha256": digest(CUBE / "model.dof"),
            "known_answer_status": upstream_result["status"],
        },
        "rigid_lift_audit_fixture": {
            "base_cube": base_audit,
            "exact_added_elastic_mechanism": {
                **mechanism_audit,
                "required_action": "stop; classify as unresolved/rejected, never accept as SPD",
            },
            "negative_elastic_direction": {
                **negative_audit,
                "required_action": "reject before constructing a physical compliance inverse",
            },
            "rcond_floor": 1.0e-12,
            "interpretation": "A pass is a numerical positivity/conditioning screen only. A low-rcond real thin-panel body is unresolved, not automatically a physical failure.",
        },
        "sparse_bordered_known_answer": {
            "system": "[K R; R.T 0] using original K and six scaled source rigid columns",
            "rotation_generalized_coordinate": "1000 mm * radians",
            "analytic_face_traction_loads": 6,
            "load_source": "uniform continuum stress traction with exact quadratic-face weights; never K*u",
            "face_shape_integrals_mm2": {"each_corner": -1.0 / 12.0, "each_edge_midpoint": 1.0 / 3.0},
            "maximum_scaled_rigid_load_N": traction_wrench_error,
            "maximum_affine_displacement_error_modulo_rigid_relative": displacement_error,
            "maximum_cross_work_error_N_mm": cross_work_error,
            "maximum_kkt_relative_residual": solved["max_kkt_relative_residual"],
            "kkt_residual_tolerance": solved["kkt_residual_tolerance"],
            "maximum_gauge_multiplier_N": solved["max_gauge_multiplier_N"],
            "gauge_multiplier_tolerance_N": solved["gauge_multiplier_tolerance_N"],
            "maximum_gauge_constraint_mm": solved["max_gauge_constraint_mm"],
            "gauge_constraint_tolerance_mm": solved["gauge_constraint_tolerance_mm"],
            "corrupt_factor_gate_fixture": {
                "status": corrupt_result["status"],
                "expected_status": "UNRESOLVED_BORDERED_KKT_RESIDUAL",
                "reported_relative_residual": corrupt_result["max_kkt_relative_residual"],
                "declared_tolerance": corrupt_result["kkt_residual_tolerance"],
            },
            "source_rows": ["1.1", "2.1"],
            "source_force_body_on_interface_N": source_force.tolist(),
            "source_condensation_formula_error_mm": source_formula_error,
            "source_dual_work_error_N_mm": abs(source_row_work - nodal_dual_work),
            "unbalanced_point_load": {
                "status": point_result["status"],
                "load": "+1 N at node 1, global X",
                "wrench": point_result["body_wrenches"][0],
                "displacement_returned": point_result["displacement_mm"] is not None,
                "gauge_multiplier_used_as_support": point_result["gauge_multiplier_used_as_support"],
                "rigid_wrench_discarded": point_result["rigid_wrench_discarded"],
            },
        },
        "source_inventory_only": {
            "parent_export_status": frame_assessment["status"],
            "parent_export_run_id": execution["run_id"],
            "parent_export_freeze_sha256": digest(frame_dir / "freeze.json"),
            "parent_export_assessment_sha256": digest(frame_dir / "assessment.json"),
            "parent_export_stiffness_sha256": frame_assessment["stiffness"]["sha256"],
            "physical_index_map_sha256": projection_contract["physical_coordinate_map"]["physical_index_map_sha256"],
            "physical_body_count": len(body_nodes),
            "physical_coordinate_count": sum(body_dofs),
            "largest_body_dofs": body_dofs[:5],
            "largest_one_body_dense_lift_bytes": max(n * n * 8 for n in body_dofs),
            "largest_one_body_dense_lift_MiB": max(n * n * 8 for n in body_dofs) / (1024.0 ** 2),
            "sum_sequential_dense_cholesky_leading_flops": sum(n ** 3 / 3.0 for n in body_dofs),
            "scope": "counts/pins only; no current-frame K extraction, lift, factorization, inversion, connector compliance, gravity, or state computation",
            "gravity_mapping_note": "No gravity file was read or used. The projection contract's source-gravity-nodal-map.json was later found to contain combined gravity+climber loads; use the separately decomposed source-load-maps.json in the pure-solid export preflight for any future gravity case.",
        },
        "limits": [
            "The only executed SPD audit and sparse bordered solve here use the authenticated 60-DOF free isotropic C3D20 cube.",
            "The current 37,647-DOF source export passed its rigid-field screen and has no cross-body couplings, but full elastic rank and positive definiteness remain unproved until parent runs a per-body audit.",
            "A near-singular real-body lift below rcond 1e-12 must stop as unresolved; it is not a declaration of physical failure. The threshold needs parent review before any frame audit.",
            "The parent must retain all 300 physical rigid coordinates and enforce R.T(F-B.T f)=0 globally. KKT multipliers are gauge diagnostics, never floor or connector support reactions.",
            "No gravity/contact state, frame response, joint acceptance, construction, or climbing release is established.",
        ],
        "mechanical_acceptance": False,
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="compare a fresh fixture result to assessment.json")
    args = parser.parse_args()
    result = run()
    target = HERE / "assessment.json"
    if args.verify:
        if json.loads(target.read_text()) != result:
            raise SystemExit("stored sparse free-body preflight assessment does not replay exactly")
        print("PASS_REPLAY_SPARSE_FREE_BODY_CONDENSATION_PREFLIGHT")
    else:
        target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
