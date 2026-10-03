#!/usr/bin/env python3
"""Verify a tiny free-body condensation map against the authenticated C3D20 K."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import scipy
from scipy.linalg import null_space, solve


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
UPSTREAM = HERE.parent / "current-free-c3d20-matrix-export-native-attempt01"
PARSER = HERE.parent / "current-native-elastic-operator-export-preflight-attempt01" / "matrix_export_oracle.py"
STRAIN_PAIRS = ((0, 0), (1, 1), (2, 2), (0, 1), (0, 2), (1, 2))
WRENCH_ATOL = 5.0e-10


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_rigid_modes(labels: list[tuple[int, int]], nodes: dict[str, list[float]]):
    xyz = {int(node): np.asarray(position, dtype=np.float64)
           for node, position in nodes.items()}
    center = np.mean(np.asarray(list(xyz.values())), axis=0)
    row = {label: i for i, label in enumerate(labels)}
    modes = np.zeros((len(labels), 6), dtype=np.float64)
    for node, point in xyz.items():
        relative = point - center
        for axis in range(3):
            modes[row[(node, axis + 1)], axis] = 1.0
        for axis, angular_velocity in enumerate(np.eye(3)):
            displacement = np.cross(angular_velocity, relative)
            for direction in range(3):
                modes[row[(node, direction + 1)], 3 + axis] = displacement[direction]
    return xyz, center, modes


def body_wrench(load: np.ndarray, modes: np.ndarray) -> dict[str, list[float]]:
    generalized = modes.T @ load
    return {
        "force_N": generalized[:3].tolist(),
        "moment_about_centroid_N_mm": generalized[3:].tolist(),
        "rigid_generalized_load_R_transpose_F": generalized.tolist(),
    }


def balanced(load: np.ndarray, modes: np.ndarray) -> tuple[bool, dict[str, list[float]]]:
    wrench = body_wrench(load, modes)
    force = np.asarray(wrench["force_N"])
    moment = np.asarray(wrench["moment_about_centroid_N_mm"])
    scale = max(1.0, float(np.linalg.norm(load, ord=1)))
    return bool(np.max(np.abs(force)) <= WRENCH_ATOL * scale
                and np.max(np.abs(moment)) <= WRENCH_ATOL * scale), wrench


def affine_field(labels, xyz, center, strain):
    rows = {label: i for i, label in enumerate(labels)}
    displacement = np.zeros(len(labels), dtype=np.float64)
    for node, point in xyz.items():
        u = strain @ (point - center)
        for direction in range(3):
            displacement[rows[(node, direction + 1)]] = u[direction]
    return displacement


def face_traction_load(labels, stress):
    """Integrate constant face traction with exact C3D20 face shape weights."""
    rows = {label: i for i, label in enumerate(labels)}
    # Each face has area 1 mm^2; corner integrals are -1/12 and midside
    # integrals are +1/3. The node order within each group is immaterial.
    faces = (
        ((1, 4, 8, 5), (12, 16, 20, 17), (-1.0, 0.0, 0.0)),
        ((2, 3, 7, 6), (10, 19, 14, 18), (1.0, 0.0, 0.0)),
        ((1, 2, 6, 5), (9, 18, 13, 17), (0.0, -1.0, 0.0)),
        ((4, 3, 7, 8), (11, 19, 15, 20), (0.0, 1.0, 0.0)),
        ((1, 2, 3, 4), (9, 10, 11, 12), (0.0, 0.0, -1.0)),
        ((5, 6, 7, 8), (13, 14, 15, 16), (0.0, 0.0, 1.0)),
    )
    load = np.zeros(len(labels), dtype=np.float64)
    area_mm2 = 1.0
    for corners, midsides, normal in faces:
        assert len(corners) == len(midsides) == 4
        assert 4 * (-1.0 / 12.0) + 4 * (1.0 / 3.0) == 1.0
        traction = stress @ np.asarray(normal, dtype=np.float64)
        for node in corners:
            for direction in range(3):
                load[rows[(node, direction + 1)]] += area_mm2 * (-1.0 / 12.0) * traction[direction]
        for node in midsides:
            for direction in range(3):
                load[rows[(node, direction + 1)]] += area_mm2 * (1.0 / 3.0) * traction[direction]
    return load


def strain_basis():
    fields = []
    for i, j in STRAIN_PAIRS:
        strain = np.zeros((3, 3), dtype=np.float64)
        if i == j:
            strain[i, j] = 1.0
        else:
            # Unit engineering shear gamma gives tensor strain gamma/2.
            strain[i, j] = strain[j, i] = 0.5
        fields.append(strain)
    return fields


def run() -> dict:
    # Authenticate the already completed engine-backed export before using K.
    upstream_assessor = load_module(UPSTREAM / "assess.py", "authenticated_free_c3d20_assessor")
    authenticated = upstream_assessor.assess()
    saved_assessment = json.loads((UPSTREAM / "assessment.json").read_text())
    if authenticated != saved_assessment or authenticated["status"] != "PASS_FREE_C3D20_MATRIX_EXPORT_ORACLE":
        raise ValueError("upstream free C3D20 assessment does not replay exactly")

    packet = json.loads((UPSTREAM / "model.json").read_text())
    parser = load_module(PARSER, "authenticated_free_matrix_parser")
    labels = parser.read_dof_map(UPSTREAM / "model.dof")
    stiffness, _ = parser.read_symmetric_triplets(UPSTREAM / "model.sti", len(labels))
    if stiffness.shape != (60, 60) or not np.allclose(stiffness, stiffness.T, rtol=0.0, atol=0.0):
        raise ValueError("authenticated stiffness export is not a symmetric 60-by-60 matrix")

    xyz, center, rigid = make_rigid_modes(labels, packet["nodes"])
    if np.linalg.matrix_rank(rigid) != 6:
        raise ValueError("six rigid modes are not independent")
    stiffness_scale = float(np.linalg.norm(stiffness, ord=2))
    rigid_residual = float(np.linalg.norm(stiffness @ rigid, ord=2)
                           / (stiffness_scale * np.linalg.norm(rigid, ord=2)))
    if rigid_residual > 1.0e-10:
        raise ValueError(f"native stiffness does not preserve rigid modes: {rigid_residual}")

    # Q spans the six-mode orthogonal complement. This is the reaction-free
    # inverse; loads with R^T F != 0 are rejected before applying it.
    q_basis = null_space(rigid.T)
    if q_basis.shape != (60, 54):
        raise ValueError(f"unexpected elastic subspace shape: {q_basis.shape}")
    reduced_stiffness = q_basis.T @ stiffness @ q_basis
    reduced_eigenvalues = np.linalg.eigvalsh(reduced_stiffness)
    if float(np.min(reduced_eigenvalues)) <= 0.0:
        raise ValueError("projected stiffness is not positive definite")
    stiffness_plus = q_basis @ solve(reduced_stiffness, q_basis.T, assume_a="pos")
    elastic_projector = q_basis @ q_basis.T
    inverse_errors = {
        "symmetry_relative": float(np.linalg.norm(stiffness_plus - stiffness_plus.T, ord=np.inf)
                                    / max(1.0, np.linalg.norm(stiffness_plus, ord=np.inf))),
        "left_projector_relative": float(np.linalg.norm(stiffness @ stiffness_plus - elastic_projector, ord=np.inf)
                                          / max(1.0, np.linalg.norm(elastic_projector, ord=np.inf))),
        "right_projector_relative": float(np.linalg.norm(stiffness_plus @ stiffness - elastic_projector, ord=np.inf)
                                           / max(1.0, np.linalg.norm(elastic_projector, ord=np.inf))),
        "rigid_annihilation_relative": float(np.linalg.norm(stiffness_plus @ rigid, ord=np.inf)
                                              / max(1.0, np.linalg.norm(stiffness_plus, ord=np.inf)
                                                    * np.linalg.norm(rigid, ord=np.inf))),
    }
    if max(inverse_errors.values()) > 2.0e-9:
        raise ValueError(f"projected inverse identities failed: {inverse_errors}")

    # The free native cube has E=1 N/mm^2, nu=0.25, and a 1 mm^3 volume.
    youngs_modulus = float(packet["material"]["E_N_per_mm2"])
    poisson = float(packet["material"]["nu"])
    lam = poisson * youngs_modulus / ((1.0 + poisson) * (1.0 - 2.0 * poisson))
    shear = youngs_modulus / (2.0 * (1.0 + poisson))
    strains = strain_basis()
    stresses = [lam * np.trace(eps) * np.eye(3) + 2.0 * shear * eps for eps in strains]
    affine = np.column_stack([affine_field(labels, xyz, center, eps) for eps in strains])
    tractions = np.column_stack([face_traction_load(labels, stress) for stress in stresses])

    responses = []
    projected_affine = []
    wrench_residuals = []
    equilibrium_residuals = []
    for column in range(6):
        load = tractions[:, column]
        is_balanced, wrench = balanced(load, rigid)
        if not is_balanced:
            raise ValueError(f"constant-stress traction failed free-body balance: {wrench}")
        response = stiffness_plus @ load
        projected = elastic_projector @ affine[:, column]
        responses.append(response)
        projected_affine.append(projected)
        wrench_residuals.append(wrench)
        equilibrium_residuals.append(float(np.linalg.norm(stiffness @ response - load, ord=np.inf)
                                           / max(1.0, np.linalg.norm(load, ord=np.inf))))
    response = np.column_stack(responses)
    projected_affine = np.column_stack(projected_affine)
    displacement_relative = float(np.linalg.norm(response - projected_affine, ord=np.inf)
                                  / max(1.0, np.linalg.norm(projected_affine, ord=np.inf)))

    observed_cross_energy = response.T @ tractions
    expected_cross_energy = np.asarray([
        [float(np.sum(strains[i] * stresses[j])) for j in range(6)]
        for i in range(6)
    ])  # unit cube volume = 1 mm^3
    cross_energy_error = float(np.max(np.abs(observed_cross_energy - expected_cross_energy)))
    basis_energy_error = float(max(
        abs(0.5 * tractions[:, i] @ response[:, i]
            - 0.5 * float(np.sum(strains[i] * stresses[i])))
        for i in range(6)
    ))
    affine_load_work_error = float(np.max(np.abs(affine.T @ tractions - expected_cross_energy)))
    if (displacement_relative > 2.0e-9 or cross_energy_error > 2.0e-9
            or basis_energy_error > 2.0e-9 or affine_load_work_error > 2.0e-9):
        raise ValueError("traction-driven affine response or energy known answer failed")

    # Two source rows let us check q = B R a + B K^+(F - B^T f).
    row_map = {label: i for i, label in enumerate(labels)}
    source_rows = ((1, 1), (2, 1))
    selector = np.zeros((2, 60), dtype=np.float64)
    for i, label in enumerate(source_rows):
        selector[i, row_map[label]] = 1.0
    compliance = selector @ stiffness_plus @ selector.T
    compliance_eigenvalues = np.linalg.eigvalsh(0.5 * (compliance + compliance.T))
    source_force = np.asarray([0.7, -0.7], dtype=np.float64)  # N, body-on-interface sign
    other_load = np.zeros(60, dtype=np.float64)
    body_load = other_load - selector.T @ source_force
    source_balanced, source_wrench = balanced(body_load, rigid)
    if not source_balanced:
        raise ValueError(f"chosen source-row force pair is not self-equilibrated: {source_wrench}")
    rigid_amplitudes = np.asarray([0.10, -0.05, 0.03, 0.01, -0.015, 0.02])
    body_displacement = rigid @ rigid_amplitudes + stiffness_plus @ body_load
    source_displacement = selector @ body_displacement
    formula_displacement = (selector @ rigid @ rigid_amplitudes
                            + selector @ stiffness_plus @ (other_load - selector.T @ source_force))
    row_work = float(source_force @ source_displacement)
    equivalent_nodal_work = float((selector.T @ source_force) @ body_displacement)
    if (not np.allclose(source_displacement, formula_displacement, rtol=0.0, atol=1.0e-12)
            or abs(row_work - equivalent_nodal_work) > 1.0e-12
            or np.max(np.abs(compliance - compliance.T)) > 1.0e-10
            or float(np.min(compliance_eigenvalues)) < -1.0e-10):
        raise ValueError("two-row condensation, reciprocity, or projected compliance check failed")

    # A point load has nonzero net force/couple. Return its full wrench and
    # reject it before K^+; a gauge multiplier must not become a fake support.
    point_load = np.zeros(60, dtype=np.float64)
    point_load[row_map[(1, 1)]] = 1.0
    point_balanced, point_wrench = balanced(point_load, rigid)
    expected_point_wrench = np.asarray([1.0, 0.0, 0.0, 0.0, -0.5, 0.5])
    observed_point_wrench = np.asarray(point_wrench["rigid_generalized_load_R_transpose_F"])
    if point_balanced or not np.allclose(observed_point_wrench, expected_point_wrench, rtol=0.0, atol=1.0e-12):
        raise ValueError(f"unbalanced point-load diagnostic failed: {point_wrench}")

    execution = json.loads((UPSTREAM / "execution.json").read_text())
    return {
        "status": "PASS_FREE_BODY_ELASTIC_CONDENSATION_KNOWN_ANSWER",
        "method": "Six-rigid-mode nullspace projection followed by positive-definite elastic-subspace solve; unbalanced loads are rejected before K+.",
        "fixture_source_sha256": digest(Path(__file__)),
        "upstream_parser_sha256": digest(PARSER),
        "upstream_native_evidence": {
            "assessment_status": authenticated["status"],
            "native_run_id": execution["run_id"],
            "input_freeze_sha256": digest(UPSTREAM / "freeze.json"),
            "execution_sha256": digest(UPSTREAM / "execution.json"),
            "assessment_sha256": digest(UPSTREAM / "assessment.json"),
            "stiffness_sha256": digest(UPSTREAM / "model.sti"),
            "dof_sha256": digest(UPSTREAM / "model.dof"),
            "native_provenance_replayed": True,
        },
        "model": {
            "nodes": 20,
            "equations": 60,
            "rigid_modes": 6,
            "elastic_coordinates": 54,
            "E_N_per_mm2": youngs_modulus,
            "poisson_ratio": poisson,
            "cube_side_mm": 1.0,
            "volume_mm3": 1.0,
            "centroid_mm": center.tolist(),
            "force_units": "N",
            "displacement_units": "mm",
            "stiffness_units": "N/mm",
        },
        "projected_inverse": {
            "basis_shape": list(q_basis.shape),
            "projected_min_eigenvalue_N_per_mm": float(np.min(reduced_eigenvalues)),
            "projected_max_eigenvalue_N_per_mm": float(np.max(reduced_eigenvalues)),
            "rigid_residual_relative": rigid_residual,
            "identity_errors": inverse_errors,
        },
        "constant_stress_traction_known_answer": {
            "face_shape_integrals_mm2": {"each_corner": -1.0 / 12.0, "each_edge_midpoint": 1.0 / 3.0, "face_sum": 1.0},
            "independent_load_source": "Uniform analytic stress traction on all six faces; no load was formed as K times displacement.",
            "engineering_strain_basis": ["xx", "yy", "zz", "gamma_xy", "gamma_xz", "gamma_yz"],
            "max_traction_body_wrench_force_N": float(max(
                np.max(np.abs(np.asarray(w["force_N"]))) for w in wrench_residuals)),
            "max_traction_body_wrench_moment_N_mm": float(max(
                np.max(np.abs(np.asarray(w["moment_about_centroid_N_mm"]))) for w in wrench_residuals)),
            "max_Ku_minus_F_relative": float(max(equilibrium_residuals)),
            "max_affine_displacement_error_modulo_rigid_relative": displacement_relative,
            "max_cross_energy_error_N_mm": cross_energy_error,
            "max_basis_energy_error_N_mm": basis_energy_error,
            "max_direct_face_work_error_N_mm": affine_load_work_error,
            "traction_load_body_wrenches": wrench_residuals,
            "observed_cross_energy_N_mm": observed_cross_energy.tolist(),
            "expected_cross_energy_N_mm": expected_cross_energy.tolist(),
        },
        "two_source_row_condensation": {
            "source_rows": ["1.1", "2.1"],
            "source_force_convention": "f is force exerted by the body on the interface; the force on the body is -B^T f.",
            "equation": "q = B R a + B K^+ (F - B^T f)",
            "required_global_equilibrium": "R^T (F - B^T f) = 0 for all six rigid modes.",
            "test_source_force_N": source_force.tolist(),
            "body_wrench_after_source_force": source_wrench,
            "max_source_displacement_formula_error_mm": float(np.max(np.abs(source_displacement - formula_displacement))),
            "source_row_work_fTBu_N_mm": row_work,
            "equivalent_nodal_work_(B^Tf)Tu_N_mm": equivalent_nodal_work,
            "projected_compliance_mm_per_N": compliance.tolist(),
            "projected_compliance_eigenvalues_mm_per_N": compliance_eigenvalues.tolist(),
            "individual_unit_source_row_wrenches": [
                body_wrench(-selector[i, :], rigid) for i in range(2)
            ],
            "individual_unit_row_loads_are_free_body_equilibrated": False,
            "interpretation": "The two-row compliance is a projected elastic block. The tested equal-and-opposite source force is balanced; the assembled global problem must still enforce the six rigid equilibrium equations.",
        },
        "unbalanced_point_load_fixture": {
            "status": "REJECT_UNBALANCED_BODY_LOAD_EXPECTED",
            "load": "+1 N at node 1, global X",
            "body_wrench": point_wrench,
            "expected_body_wrench": {"force_N": [1.0, 0.0, 0.0], "moment_about_centroid_N_mm": [0.0, -0.5, 0.5]},
            "equilibrium_required": True,
            "K_plus_applied": False,
            "gauge_multiplier_used_as_support": False,
            "rigid_wrench_discarded": False,
            "required_balancing_wrench_N_and_N_mm": [-1.0, 0.0, 0.0, 0.0, 0.5, -0.5],
        },
        "limits": [
            "This method is authenticated only against the one free isotropic unit C3D20 operator and analytic constant-traction answers.",
            "The two source rows illustrate the condensation identity; this does not assemble or solve an actual frame controller or 50-body system.",
            "No gravity/contact state, current-frame response, joint acceptance, construction, or climbing release is established.",
        ],
        "mechanical_acceptance": False,
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="compare a fresh result with assessment.json")
    args = parser.parse_args()
    result = run()
    target = HERE / "assessment.json"
    if args.verify:
        if json.loads(target.read_text()) != result:
            raise SystemExit("stored condensation assessment does not replay exactly")
        print("PASS_REPLAY_FREE_BODY_ELASTIC_CONDENSATION_FIXTURE")
    else:
        target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
