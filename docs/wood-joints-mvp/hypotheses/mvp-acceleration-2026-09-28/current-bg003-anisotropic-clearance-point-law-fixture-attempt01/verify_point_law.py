#!/usr/bin/env python3
"""Known-answer anisotropic elastic embedding with circular clearance."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "point-law-fixture.json"
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
INPUT_DIR = BASE / "current-bg003-compatible-elastic-method-inputs-attempt01"
ROTATED_DIR = BASE / "current-bg003-rotated-foundation-diagnostic-attempt01"
RADIAL_DIR = BASE / "current-bg003-radial-clearance-diagnostic-attempt01"

PINNED_SOURCES = {
    INPUT_DIR / "inputs.json": "008d9b1d790d7994e0d72d6002baa479f82bb80143e936f6d328f334fdcd37d9",
    INPUT_DIR / "prepare_inputs.py": "f7f45c9b01ec792449f7feff077fb58720b07fb8a4ac8000bb6c573b87538a96",
    INPUT_DIR / "SHA256SUMS": "544e1b3fb3875e26a09a4224d1742e9e9222b26b284b68db356e9c7a2551ae7c",
    ROTATED_DIR / "run_diagnostic.py": "4a5d3a785aac34905608f4255af4f9075e7a910e32e1acc6e0058c20d8ef063b",
    ROTATED_DIR / "diagnostics.json": "4299919a3d3bfa8ef56589e8741ca62f3e88cb7b6077d46053ac3ba06af12918",
    ROTATED_DIR / "README.md": "3de0bf9642ca9f8aefacfbc41a71000088c203792666a2ff14aa10a2e1e550ab",
    RADIAL_DIR / "run_diagnostic.py": "65147beb92edda20137d2fd962594bb1d04a62f0593f0ab0beb2f12850057b2f",
    RADIAL_DIR / "diagnostics.json": "2a6ee00883ab242ddd5f6c144e07b618aa58a604a007fb24edeebeae5461fc77",
    RADIAL_DIR / "README.md": "2816523a6c718f6bedbe12fc6fe188b3140fe21284db03afb8cf954cc256bfc4",
}

TOL = 2e-9
MAX_BRACKET_DOUBLINGS = 64


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(x: float) -> float:
    if abs(float(x)) < 5e-13:
        return 0.0
    return round(float(x), 12)


def check_source_pins() -> dict[str, str]:
    actual = {str(path.relative_to(ROOT)): sha256(path) for path in PINNED_SOURCES}
    expected = {str(path.relative_to(ROOT)): value for path, value in PINNED_SOURCES.items()}
    assert actual == expected, "pinned BG003 elastic/rotation/gap source changed"
    return actual


def evaluate(delta: np.ndarray, K: np.ndarray, gap: float) -> dict:
    """Return energy, force, tangent and minimizer for the circular-gap law."""
    delta = np.asarray(delta, dtype=float)
    K = np.asarray(K, dtype=float)
    assert delta.shape == (2,) and K.shape == (2, 2)
    assert gap >= 0.0 and np.isfinite(gap)
    assert np.all(np.isfinite(delta)) and np.all(np.isfinite(K))
    assert np.max(np.abs(K - K.T)) <= 1e-12
    eigenvalues = np.linalg.eigvalsh(K)
    assert eigenvalues[0] > 0.0, "point stiffness must be SPD"
    rho = float(np.linalg.norm(delta))

    if gap == 0.0:
        v = np.zeros(2)
        p = K @ delta
        energy = 0.5 * float(delta @ p)
        tangent = K.copy()
        return {
            "branch": "zero_gap_linear",
            "lambda_N_per_mm": None,
            "v_mm": v,
            "p_N": p,
            "energy_Nmm": energy,
            "tangent_N_per_mm": tangent,
            "gap_feasibility_violation_mm": 0.0,
            "outside_boundary_residual_mm": None,
            "force_equals_lambda_v_residual_N": None,
            "root_iterations": 0,
            "bracket_doublings": 0,
        }

    if rho <= gap:
        return {
            "branch": "inside_or_at_gap_open",
            "lambda_N_per_mm": 0.0,
            "v_mm": delta.copy(),
            "p_N": np.zeros(2),
            "energy_Nmm": 0.0,
            "tangent_N_per_mm": np.zeros((2, 2)),
            "gap_feasibility_violation_mm": 0.0,
            "outside_boundary_residual_mm": None,
            "force_equals_lambda_v_residual_N": 0.0,
            "root_iterations": 0,
            "bracket_doublings": 0,
        }

    identity = np.eye(2)
    Kdelta = K @ delta

    def v_for(lam: float) -> np.ndarray:
        return np.linalg.solve(K + lam * identity, Kdelta)

    lo = 0.0
    hi = float(eigenvalues[-1] * (rho / gap - 1.0))
    assert np.isfinite(hi) and hi > 0.0
    bracket_doublings = 0
    for bracket_doublings in range(MAX_BRACKET_DOUBLINGS + 1):
        v_hi = v_for(hi)
        assert np.all(np.isfinite(v_hi)), "nonfinite displacement while bracketing lambda"
        norm_hi = float(np.linalg.norm(v_hi))
        assert np.isfinite(norm_hi), "nonfinite norm while bracketing lambda"
        if norm_hi <= gap:
            break
        assert bracket_doublings < MAX_BRACKET_DOUBLINGS, "lambda bracket expansion budget exhausted"
        hi *= 2.0
        assert np.isfinite(hi), "nonfinite lambda upper bracket"
    else:
        raise AssertionError("lambda bracket expansion budget exhausted")
    iterations = 0
    for iterations in range(1, 121):
        mid = 0.5 * (lo + hi)
        if mid == lo or mid == hi:
            break
        if np.linalg.norm(v_for(mid)) > gap:
            lo = mid
        else:
            hi = mid
    lam = 0.5 * (lo + hi)
    v = v_for(lam)
    A = K + lam * identity
    M = np.linalg.solve(A, identity)
    p = K @ (delta - v)
    energy = 0.5 * float((delta - v) @ p)

    # From d(v.T*v)=0, dλ=(v.T M K dδ)/(v.T M v). With b=K M v,
    # dp gives T=λ K M + b b.T/(v.T M v). This form is symmetric PSD and
    # avoids cancellation in K - K M K near first engagement.
    Mv = np.linalg.solve(A, v)
    denominator = float(v @ Mv)
    b = K @ Mv
    tangent = lam * (K @ M) + np.outer(b, b) / denominator
    asymmetry = float(np.max(np.abs(tangent - tangent.T)))
    assert asymmetry <= 1e-9
    tangent = 0.5 * (tangent + tangent.T)

    return {
        "branch": "outside_gap_engaged",
        "lambda_N_per_mm": lam,
        "v_mm": v,
        "p_N": p,
        "energy_Nmm": energy,
        "tangent_N_per_mm": tangent,
        "gap_feasibility_violation_mm": float(max(np.linalg.norm(v) - gap, 0.0)),
        "outside_boundary_residual_mm": float(abs(np.linalg.norm(v) - gap)),
        "force_equals_lambda_v_residual_N": float(np.max(np.abs(p - lam * v))),
        "root_iterations": iterations,
        "bracket_doublings": bracket_doublings,
    }


def clean_result(result: dict) -> dict:
    return {
        "branch": result["branch"],
        "lambda_N_per_mm": None if result["lambda_N_per_mm"] is None else clean(result["lambda_N_per_mm"]),
        "v_mm": [clean(x) for x in result["v_mm"]],
        "p_N": [clean(x) for x in result["p_N"]],
        "energy_Nmm": clean(result["energy_Nmm"]),
        "tangent_N_per_mm": [[clean(x) for x in row] for row in result["tangent_N_per_mm"]],
        "gap_feasibility_violation_mm": clean(result["gap_feasibility_violation_mm"]),
        "outside_boundary_residual_mm": (None if result["outside_boundary_residual_mm"] is None
                                         else clean(result["outside_boundary_residual_mm"])),
        "force_equals_lambda_v_residual_N": (None if result["force_equals_lambda_v_residual_N"] is None
                                             else clean(result["force_equals_lambda_v_residual_N"])),
        "root_iterations": result["root_iterations"],
        "bracket_doublings": result["bracket_doublings"],
    }


def evaluate_with_checks(delta: np.ndarray, K: np.ndarray, gap: float) -> dict:
    r = evaluate(delta, K, gap)
    if r["branch"] == "outside_gap_engaged":
        assert r["lambda_N_per_mm"] > 0.0
        assert r["gap_feasibility_violation_mm"] <= TOL
        assert r["outside_boundary_residual_mm"] <= TOL
        assert r["force_equals_lambda_v_residual_N"] <= 2e-7
        assert r["bracket_doublings"] <= MAX_BRACKET_DOUBLINGS
        assert np.linalg.eigvalsh(r["tangent_N_per_mm"]).min() >= -1e-8
    return clean_result(r)


def rotation(theta: float) -> np.ndarray:
    return np.array([[math.cos(theta), -math.sin(theta)],
                     [math.sin(theta), math.cos(theta)]], dtype=float)


def point_law_oracles() -> dict:
    # Mixed force and anisotropic compliance: the target force is not collinear
    # with delta because K has a genuine off-diagonal term.
    K = np.array([[300.0, 150.0], [150.0, 100.0]])  # N/mm
    gap = 0.575  # mm
    target_p = np.array([3.0, 4.0])  # N
    target_v = gap * target_p / np.linalg.norm(target_p)
    delta = target_v + np.linalg.solve(K, target_p)
    oracle = evaluate(delta, K, gap)
    assert np.allclose(oracle["p_N"], target_p, rtol=0.0, atol=2e-10)
    assert np.allclose(oracle["v_mm"], target_v, rtol=0.0, atol=2e-12)
    lambda_exact = float(np.linalg.norm(target_p) / gap)
    assert abs(float(oracle["lambda_N_per_mm"]) - lambda_exact) < 2e-10
    mixed_cross = float(delta[0] * target_p[1] - delta[1] * target_p[0])
    assert abs(mixed_cross) > 1e-4

    # Isotropic K reduces exactly to the previous radial point spring.
    k_iso = 100.0
    gap_iso = 0.575
    p_iso_target = np.array([3.0, 4.0])
    delta_iso = (gap_iso + np.linalg.norm(p_iso_target) / k_iso) * p_iso_target / np.linalg.norm(p_iso_target)
    K_iso = k_iso * np.eye(2)
    iso = evaluate(delta_iso, K_iso, gap_iso)
    rho = float(np.linalg.norm(delta_iso))
    direction = delta_iso / rho
    p_iso_ref = k_iso * (rho - gap_iso) * direction
    U_iso_ref = 0.5 * k_iso * (rho - gap_iso) ** 2
    T_iso_ref = k_iso * ((1.0 - gap_iso / rho) * np.eye(2)
                         + (gap_iso / rho) * np.outer(direction, direction))
    assert np.allclose(iso["p_N"], p_iso_ref, rtol=0.0, atol=2e-10)
    assert np.allclose(delta_iso, np.array([0.375, 0.5]), rtol=0.0, atol=2e-14)
    assert np.allclose(iso["p_N"], p_iso_target, rtol=0.0, atol=2e-10)
    assert abs(iso["energy_Nmm"] - U_iso_ref) < 2e-10
    assert np.allclose(iso["tangent_N_per_mm"], T_iso_ref, rtol=0.0, atol=2e-9)

    # With zero gap the same rotated anisotropic matrix is ordinary linear Kδ.
    K_rotated = np.array([[14.07, 0.0], [0.0, 35.19]])
    angle = math.radians(40.0)
    Rgrain = rotation(angle)
    K_rotated = Rgrain @ K_rotated @ Rgrain.T
    delta_zero_gap = np.array([0.4, -0.3])
    zero_gap = evaluate(delta_zero_gap, K_rotated, 0.0)
    p_zero_ref = K_rotated @ delta_zero_gap
    U_zero_ref = 0.5 * float(delta_zero_gap @ p_zero_ref)
    assert np.allclose(zero_gap["p_N"], p_zero_ref, rtol=0.0, atol=2e-12)
    assert np.allclose(zero_gap["tangent_N_per_mm"], K_rotated, rtol=0.0, atol=2e-12)
    assert abs(zero_gap["energy_Nmm"] - U_zero_ref) < 2e-12

    inside_delta = np.array([0.1, -0.2])
    inside = evaluate(inside_delta, K, gap)
    assert inside["branch"] == "inside_or_at_gap_open"
    assert np.max(np.abs(inside["p_N"])) == 0.0
    assert inside["energy_Nmm"] == 0.0
    assert np.max(np.abs(inside["tangent_N_per_mm"])) == 0.0

    # Finite-difference the gradient and exact outside-branch tangent.
    h = 1e-6
    grad_fd = np.array([
        (evaluate(delta + np.eye(2)[j] * h, K, gap)["energy_Nmm"]
         - evaluate(delta - np.eye(2)[j] * h, K, gap)["energy_Nmm"]) / (2.0 * h)
        for j in range(2)
    ])
    tangent_fd = np.column_stack([
        (evaluate(delta + np.eye(2)[j] * h, K, gap)["p_N"]
         - evaluate(delta - np.eye(2)[j] * h, K, gap)["p_N"]) / (2.0 * h)
        for j in range(2)
    ])
    gradient_error = float(np.max(np.abs(grad_fd - oracle["p_N"])))
    tangent_error = float(np.max(np.abs(tangent_fd - oracle["tangent_N_per_mm"])))
    assert gradient_error < 2e-7 and tangent_error < 2e-6

    # Covariance under simultaneous rigid rotation of δ and K.
    Q = rotation(0.731)
    rotated = evaluate(Q @ delta, Q @ K @ Q.T, gap)
    energy_rotation_error = abs(rotated["energy_Nmm"] - oracle["energy_Nmm"])
    force_rotation_error = float(np.max(np.abs(rotated["p_N"] - Q @ oracle["p_N"])))
    v_rotation_error = float(np.max(np.abs(rotated["v_mm"] - Q @ oracle["v_mm"])))
    tangent_rotation_error = float(np.max(np.abs(
        rotated["tangent_N_per_mm"] - Q @ oracle["tangent_N_per_mm"] @ Q.T
    )))
    assert energy_rotation_error < 2e-12
    assert force_rotation_error < 2e-10 and v_rotation_error < 2e-12
    assert tangent_rotation_error < 2e-9

    # A secant Jensen check supplements the infimal-convolution convexity proof.
    da = np.array([0.1, -0.2])
    db = delta
    theta = 0.37
    Ua = evaluate(da, K, gap)["energy_Nmm"]
    Ub = evaluate(db, K, gap)["energy_Nmm"]
    Um = evaluate((1.0 - theta) * da + theta * db, K, gap)["energy_Nmm"]
    jensen_slack = (1.0 - theta) * Ua + theta * Ub - Um
    assert jensen_slack >= -2e-12

    return {
        "anisotropic_known_force_oracle": {
            "K_point_N_per_mm": K.tolist(),
            "gap_mm": gap,
            "target_p_N": target_p.tolist(),
            "target_v_mm": target_v.tolist(),
            "constructed_delta_mm": delta.tolist(),
            "force_not_collinear_with_delta_cross_mmN": mixed_cross,
            "recovered": clean_result(oracle),
            "expected_lambda_N_per_mm": lambda_exact,
        },
        "isotropic_radial_equivalence": {
            "K_point_N_per_mm": K_iso.tolist(),
            "delta_mm": delta_iso.tolist(),
            "gap_mm": gap_iso,
            "target_p_N_from_prior_radial_oracle": p_iso_target.tolist(),
            "recovered_p_N": [clean(x) for x in iso["p_N"]],
            "radial_reference_p_N": [clean(x) for x in p_iso_ref],
            "recovered_energy_Nmm": clean(iso["energy_Nmm"]),
            "radial_reference_energy_Nmm": clean(U_iso_ref),
            "tangent_max_abs_error_N_per_mm": clean(float(np.max(np.abs(iso["tangent_N_per_mm"] - T_iso_ref)))),
        },
        "zero_gap_rotated_linear_equivalence": {
            "K_point_N_per_mm": [[clean(x) for x in row] for row in K_rotated],
            "delta_mm": delta_zero_gap.tolist(),
            "recovered_p_N": [clean(x) for x in zero_gap["p_N"]],
            "linear_K_delta_N": [clean(x) for x in p_zero_ref],
            "energy_Nmm": clean(zero_gap["energy_Nmm"]),
            "tangent_equals_K": True,
        },
        "zero_interior_force": {
            "delta_mm": inside_delta.tolist(),
            "gap_mm": gap,
            "branch": inside["branch"],
            "p_N": [clean(x) for x in inside["p_N"]],
            "energy_Nmm": clean(inside["energy_Nmm"]),
            "tangent_zero": bool(np.max(np.abs(inside["tangent_N_per_mm"])) == 0.0),
        },
        "outside_energy_gradient_and_tangent_finite_differences": {
            "step_mm": h,
            "gradient_max_abs_error_N": gradient_error,
            "tangent_max_abs_error_N_per_mm": tangent_error,
            "tangent_min_eigenvalue_N_per_mm": float(np.linalg.eigvalsh(oracle["tangent_N_per_mm"]).min()),
            "energy_jensen_slack_Nmm": jensen_slack,
        },
        "rigid_transverse_rotation_covariance": {
            "angle_rad": 0.731,
            "energy_abs_error_Nmm": energy_rotation_error,
            "force_max_abs_error_N": force_rotation_error,
            "v_max_abs_error_mm": v_rotation_error,
            "tangent_max_abs_error_N_per_mm": tangent_rotation_error,
        },
    }


def mesh_recipe(inputs: dict, radial: dict) -> dict:
    geom = inputs["geometry_and_available_conditional_scenarios"]
    published = inputs["published_elastic_embedment_inputs_non_adopted"]
    line_inputs = inputs["linear_operator_and_units"]
    rho_values = published["density_interval_kg_per_m3"]
    diameter = float(geom["diameter_mm"])
    grain_xyz = geom["proposed_grain_vectors_global_xyz"]
    members = geom["modeled_stack_order_head_to_nut"]
    lengths = geom["raw_modeled_bearing_lengths_mm"]
    radial_params = radial["physical_and_conditional_parameters"]
    gap = float(radial_params["radial_clearance_mm"])
    hole = float(radial_params["modeled_hole_diameter_mm"])
    assert abs(gap - (hole - diameter) / 2.0) <= 1e-12
    assert abs(diameter - 6.35) <= 1e-12
    assert radial["model"]["mesh_divisions_per_receiver"] == [16, 32]
    assert radial["model"]["receiver_lengths_mm"] == [lengths[m] for m in members]

    gauss_weights = np.polynomial.legendre.leggauss(4)[1]
    densities = []
    for rho in rho_values:
        kf_parallel = 0.1374 * float(rho) - 12.9
        kf_perp = 0.0922 * float(rho) - 18.20
        assert abs(kf_parallel - published["resulting_moduli_N_per_mm3"]["parallel"][rho_values.index(rho)]) < 1e-10
        assert abs(kf_perp - published["resulting_moduli_N_per_mm3"]["perpendicular"][rho_values.index(rho)]) < 1e-10
        Kline_diag = np.diag([diameter * kf_perp, diameter * kf_parallel])
        member_matrices = {}
        for member in members:
            grain = np.asarray(grain_xyz[member], dtype=float)[1:3]
            grain /= np.linalg.norm(grain)
            e_parallel = grain
            if member == "base_side_left":
                e_perp = np.array([e_parallel[1], -e_parallel[0]])
            else:
                assert np.allclose(e_parallel, np.array([0.0, 1.0]), atol=1e-12)
                e_perp = np.array([1.0, 0.0])
            R = np.column_stack((e_perp, e_parallel))
            Kline = R @ Kline_diag @ R.T
            member_matrices[member] = {
                "grain_parallel_unit_YZ": [clean(x) for x in e_parallel],
                "grain_perpendicular_unit_YZ": [clean(x) for x in e_perp],
                "K_line_global_YZ_N_per_mm2": [[clean(x) for x in row] for row in Kline],
                "K_line_eigenvalues_N_per_mm2": [clean(x) for x in np.linalg.eigvalsh(Kline)],
            }
        densities.append({
            "density_kg_per_m3_non_adopted": rho,
            "kf_parallel_N_per_mm3": clean(kf_parallel),
            "kf_perpendicular_N_per_mm3": clean(kf_perp),
            "K_line_parallel_N_per_mm2": clean(diameter * kf_parallel),
            "K_line_perpendicular_N_per_mm2": clean(diameter * kf_perp),
            "members": member_matrices,
        })

    meshes = []
    for divisions in radial["model"]["mesh_divisions_per_receiver"]:
        receiver_rows = []
        all_weights = []
        for member in members:
            element_length = float(lengths[member]) / int(divisions)
            weights = element_length * gauss_weights / 2.0
            all_weights.extend(weights.tolist())
            receiver_rows.append({
                "member": member,
                "length_mm": float(lengths[member]),
                "element_count": int(divisions),
                "element_length_mm": element_length,
                "gauss_points_per_element": len(gauss_weights),
                "integration_point_count": int(divisions) * len(gauss_weights),
                "quadrature_weight_values_mm": [clean(x) for x in weights],
            })
        wmin = min(all_weights)
        wmax = max(all_weights)
        mesh_density_ranges = {}
        for density in densities:
            kline_eigs = [density["K_line_perpendicular_N_per_mm2"],
                          density["K_line_parallel_N_per_mm2"]]
            mesh_density_ranges[str(int(density["density_kg_per_m3_non_adopted"]))] = {
                "point_K_principal_value_range_N_per_mm": [
                    clean(wmin * min(kline_eigs)), clean(wmax * max(kline_eigs))
                ],
                "meaning": "per-quadrature-point eigenvalue envelope: weight_mm * K_line_N_per_mm2",
            }
        meshes.append({
            "divisions_per_receiver": int(divisions),
            "receiver_mesh": receiver_rows,
            "quadrature_sample_count_one_bolt": 3 * int(divisions) * len(gauss_weights),
            "quadrature_weight_envelope_mm": [clean(wmin), clean(wmax)],
            "point_K_principal_envelopes_by_density": mesh_density_ranges,
        })

    return {
        "case_and_bolt": {
            "case_id": radial["source_case"]["case_id"],
            "axis_id": radial["source_case"]["axis_id"],
            "load_increment": radial["source_case"]["selected_increment_load_factor"],
            "only_source_scope_used": "A12-rear BG003 bolt1 full-load source wrench; do not transfer load across cases or bolts",
        },
        "clearance": {
            "modeled_bolt_diameter_mm": diameter,
            "modeled_hole_diameter_mm": hole,
            "radial_gap_mm": gap,
            "gap_scenarios_to_run_if_parent_ready": [0.0, gap],
            "interpretation": "modeled geometry only; physical gap/contact side not observed",
        },
        "published_density_sensitivities_non_adopted": densities,
        "mesh_scenarios": meshes,
        "finite_proxy_recipe_only": [
            "Use the existing 38.1/88.9/88.9 mm A12-rear bolt1 source-wrench register and the existing 4-point Gauss EB mesh at 16 and 32 divisions per receiver.",
            "At each quadrature point use delta=w_bolt(s)-u_receiver(s), K_point=weight_mm*K_line_global_YZ in N/mm, and the same circular-gap minimization with g=0 or 0.575 mm.",
            "When evaluating with K_point, add returned point energy, force, and tangent directly; do not multiply by the quadrature weight again. Equivalently evaluate per-length outputs with K_line and multiply energy/force/tangent by the weight exactly once.",
            "The scalar root implementation is a reference oracle (53 bisection iterations in the mixed-force case); before a finite run, use batched/eigenbasis 2x2 evaluation and validate its cost against the existing continuation budget.",
            "Assemble one vector force and one 2x2 tangent per quadrature point into the existing residual using its established relative-displacement sign; retain off-diagonal Y/Z terms and solve both planes together.",
            "Keep the three receiver wrenches applied once to receiver DOFs; do not add source interface actions again, and do not add capacities or solve independent plane limits.",
            "The eight requested sensitivity combinations are two illustrative densities by two meshes by two gaps. Parent owns readiness and execution; this packet runs none of them.",
        ],
        "unit_contract": {
            "published_kf": "N/mm^3 (stress/displacement foundation modulus)",
            "line_K": "d_mm*kf_N_per_mm3 = N/mm^2",
            "point_K": "quadrature_weight_mm*K_line_N_per_mm2 = N/mm",
            "delta_and_gap": "mm",
            "point_force": "N",
            "point_energy": "N*mm",
            "lambda": "N/mm",
        },
        "source_method_unit_strings": line_inputs,
    }


def produce() -> dict:
    source_sha256 = check_source_pins()
    inputs = json.loads((INPUT_DIR / "inputs.json").read_text())
    rotated = json.loads((ROTATED_DIR / "diagnostics.json").read_text())
    radial = json.loads((RADIAL_DIR / "diagnostics.json").read_text())
    assert inputs["status"] == "INPUT_REGISTER_AND_METHOD_FEASIBILITY_ONLY_NO_BG003_ELASTIC_SOLUTION"
    assert rotated["status"] == "PASS_SYNTHETIC_ROTATED_FOUNDATION_DIAGNOSTIC_ONLY"
    assert radial["status"] == "PASS_BOUNDED_RADIAL_GAP_DIAGNOSTIC_ONLY"
    oracles = point_law_oracles()
    recipe = mesh_recipe(inputs, radial)
    source_sha256[str(Path(__file__).relative_to(ROOT))] = sha256(Path(__file__))
    return {
        "schema": "bg003_anisotropic_circular_clearance_point_law_fixture/v1",
        "status": "PASS_POINT_LAW_KNOWN_ANSWERS_AND_APPLICABILITY_RECIPE_ONLY",
        "source_sha256": source_sha256,
        "candidate_law": {
            "classification": "constitutive hypothesis; not measured or calibrated for BG003",
            "potential": "U(delta)=min_{|v|<=g} 0.5*(delta-v).T*K*(delta-v)",
            "interior": "|delta|<=g: v=delta, p=0, U=0, tangent=0",
            "outside": "v=(K+lambda*I)^-1*K*delta, |v|=g, lambda>0, p=K*(delta-v)=lambda*v",
            "tangent_outside": "T=lambda*K*M + (K*M*v)*(K*M*v).T/(v.T*M*v), M=(K+lambda*I)^-1",
            "gap_zero": "g=0: v=0, p=K*delta, U=0.5*delta.T*K*delta, T=K",
            "root_controls": "lambda upper bracket kmax*(|delta|/g-1), at most 64 finite-checked doublings, at most 120 bisections; finite execution needs batched/eigenbasis evaluation",
            "units": "K point N/mm; delta,v,g mm; lambda N/mm; p N; U N*mm; tangent N/mm",
        },
        "point_law_known_answers": oracles,
        "applicability_and_finite_proxy_recipe": recipe,
        "limits": [
            "The circular clearance plus rotated anisotropic elasticity is a new path-independent constitutive hypothesis; Gikonyo's parallel/perpendicular regressions do not validate a 40-degree BG003 law or this circular free-clearance disk.",
            "Density 350/550 kg/m^3 values are non-adopted illustrative literature sensitivities, not actual member density or stiffness bounds; do not infer density from G or NDS bearing strength.",
            "No finite beam/joint response, current load-case run, capacity, strength, splitting, group, shared-timber compatibility, axial tie, steel yield, washer, or full-joint claim is computed.",
            "The point-law fixture checks convex energy and its smooth outside-gap tangent only. At first engagement the energy is C1 but its tangent has a branch jump; the exact boundary uses the zero-force interior convention.",
            "No actual contact history is represented; the law has no memory, damage, unloading hysteresis, or physical fit verification.",
        ],
        "finite_BG003_run_executed": False,
        "native_solve_run": False,
        "geometry_changed": False,
        "capacity_calculated": False,
        "joint_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(produce(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.verify:
        assert OUTPUT.read_text() == rendered, "saved point-law fixture differs from pinned replay"
        print("PASS_ANISOTROPIC_CIRCULAR_GAP_POINT_LAW: 7 known-answer gates; finite proxy not run")
    else:
        OUTPUT.write_text(rendered)
        print("Wrote anisotropic circular-gap point-law fixture")


if __name__ == "__main__":
    main()
