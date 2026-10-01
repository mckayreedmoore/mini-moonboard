#!/usr/bin/env python3
"""Bounded nonlinear radial-gap beam-on-foundation fixture; no strength check."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
OWNER = ROOT / "docs/wood-joints-mvp/hypotheses/support-corner-review-2026-09-30"
INPUT_DIR = BASE / "current-bg003-compatible-elastic-method-inputs-attempt01"
INPUT_PATH = INPUT_DIR / "inputs.json"
INPUT_SHA256 = "008d9b1d790d7994e0d72d6002baa479f82bb80143e936f6d328f334fdcd37d9"
INPUT_PRODUCER_SHA256 = "f7f45c9b01ec792449f7feff077fb58720b07fb8a4ac8000bb6c573b87538a96"
INPUT_MANIFEST_SHA256 = "544e1b3fb3875e26a09a4224d1742e9e9222b26b284b68db356e9c7a2551ae7c"
OWNER_PINS = {
    "diagnose.py": "8ab5615b9e2bc80ac56f3d5002bc7053981a3ad4387a9a39e2088273f073be59",
    "diagnostics.json": "174f8f945e41a273318a41fc401f1ef484160b500d624d80f57cd3480a343c98",
    "README.md": "b9cfe28dfed2205da3f2375f7563e2d8839bd0588dba85bdf7e3777ab01c9250",
}
ROTATED_DIR = BASE / "current-bg003-rotated-foundation-diagnostic-attempt01"
ROTATED_PINS = {
    "run_diagnostic.py": "4a5d3a785aac34905608f4255af4f9075e7a910e32e1acc6e0058c20d8ef063b",
    "diagnostics.json": "4299919a3d3bfa8ef56589e8741ca62f3e88cb7b6077d46053ac3ba06af12918",
    "README.md": "3de0bf9642ca9f8aefacfbc41a71000088c203792666a2ff14aa10a2e1e550ab",
}
CASE_ID = "a12-rear"
AXIS_ID = "knee_outer_left_side_1"
MEMBERS = [
    "knee_outer_left_spine",
    "base_side_left",
    "knee_outer_left_inner_frame_block",
]
LENGTHS_MM = np.array([38.1, 88.9, 88.9], dtype=float)
LENGTH_MM = float(np.sum(LENGTHS_MM))
EDGES_MM = np.r_[0.0, np.cumsum(LENGTHS_MM)]
CENTERS_MM = (EDGES_MM[:-1] + EDGES_MM[1:]) / 2.0
MIDDLE_CUT_MM = 38.1 + 44.45
DIAMETER_MM = 6.35
HOLE_DIAMETER_MM = 7.5
RADIAL_GAP_MM = (HOLE_DIAMETER_MM - DIAMETER_MM) / 2.0
STEEL_E_MPA = 190000.0
I_MM4 = math.pi * DIAMETER_MM**4 / 64.0
EI_NMM2 = STEEL_E_MPA * I_MM4
K_VALUES_N_PER_MM2 = [100.0, 1000.0]
DIVISIONS = [16, 32]
GAUSS_X, GAUSS_W = np.polynomial.legendre.leggauss(4)
MAX_HOMOTOPY_ACCEPTED_STEPS = 80
MAX_HOMOTOPY_ATTEMPTS = 160
INITIAL_GAP_STEPS = 8
MAX_GAP_HALVINGS = 16
MAX_NEWTON_PER_STEP = 20
MAX_LINESEARCH_HALVINGS = 12
RESIDUAL_TOL = 1e-9
CHOLESKY_PIVOT_RATIO_TOL = 1e-12


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def beam_matrix(h: float) -> np.ndarray:
    return np.array(
        [
            [12, 6 * h, -12, 6 * h],
            [6 * h, 4 * h * h, -6 * h, 2 * h * h],
            [-12, -6 * h, 12, -6 * h],
            [6 * h, 2 * h * h, -6 * h, 4 * h * h],
        ],
        dtype=float,
    ) / h**3


def shapes(t: float, h: float) -> np.ndarray:
    return np.array(
        [1 - 3 * t * t + 2 * t**3, h * (t - 2 * t * t + t**3),
         3 * t * t - 2 * t**3, h * (-t * t + t**3)],
        dtype=float,
    )


def radial_potential(relative: np.ndarray, gap: float, k: float) -> float:
    excess = max(float(np.linalg.norm(relative)) - gap, 0.0)
    return 0.5 * k * excess * excess


def radial_force_tangent(
    relative: np.ndarray, gap: float, k: float
) -> tuple[np.ndarray, np.ndarray]:
    rho = float(np.linalg.norm(relative))
    if gap == 0.0:
        return k * relative, k * np.eye(2)
    if rho <= gap:
        return np.zeros(2), np.zeros((2, 2))
    direction = relative / rho
    force = k * (rho - gap) * direction
    tangent = k * ((1.0 - gap / rho) * np.eye(2) + (gap / rho) * np.outer(direction, direction))
    return force, tangent


def check_single_spring_oracles() -> dict:
    k = 100.0
    gap = RADIAL_GAP_MM
    force = np.array([3.0, 4.0])
    magnitude = float(np.linalg.norm(force))
    displacement = (gap + magnitude / k) * force / magnitude
    spring_force, spring_tangent = radial_force_tangent(displacement, gap, k)
    exact = np.array([0.375, 0.5])
    assert np.allclose(displacement, exact, rtol=0, atol=1e-14)
    assert np.allclose(spring_force, force, rtol=0, atol=1e-13)

    angle = 0.731
    rotation = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
    rotated_force, rotated_tangent = radial_force_tangent(rotation @ displacement, gap, k)
    assert np.allclose(radial_potential(rotation @ displacement, gap, k),
                       radial_potential(displacement, gap, k), rtol=0, atol=1e-13)
    assert np.allclose(rotated_force, rotation @ spring_force, rtol=0, atol=1e-12)
    assert np.allclose(rotated_tangent, rotation @ spring_tangent @ rotation.T, rtol=0, atol=1e-12)

    test_r = np.array([0.8, 0.4])
    test_gap = 0.2
    test_k = 13.0
    analytic_force, analytic_tangent = radial_force_tangent(test_r, test_gap, test_k)
    h = 1e-6
    fd_gradient = np.array([
        (radial_potential(test_r + np.eye(2)[j] * h, test_gap, test_k)
         - radial_potential(test_r - np.eye(2)[j] * h, test_gap, test_k)) / (2 * h)
        for j in range(2)
    ])
    fd_tangent = np.column_stack([
        (radial_force_tangent(test_r + np.eye(2)[j] * h, test_gap, test_k)[0]
         - radial_force_tangent(test_r - np.eye(2)[j] * h, test_gap, test_k)[0]) / (2 * h)
        for j in range(2)
    ])
    assert np.max(np.abs(fd_gradient - analytic_force)) < 2e-8
    assert np.max(np.abs(fd_tangent - analytic_tangent)) < 2e-8
    inactive = np.array([0.1, -0.2])
    inactive_force, inactive_tangent = radial_force_tangent(inactive, gap, k)
    assert np.max(np.abs(inactive_force)) == 0.0 and np.max(np.abs(inactive_tangent)) == 0.0

    zero_gap_u = force / k
    zero_gap_force, zero_gap_tangent = radial_force_tangent(zero_gap_u, 0.0, k)
    assert np.allclose(zero_gap_force, force, rtol=0, atol=1e-13)
    assert np.allclose(zero_gap_tangent, k * np.eye(2), rtol=0, atol=0)
    return {
        "single_spring_input": {"P_N": force.tolist(), "point_spring_stiffness_N_per_mm": k, "gap_mm": gap},
        "oracle_displacement_mm": exact.tolist(),
        "computed_displacement_mm": displacement.tolist(),
        "recovered_force_N": spring_force.tolist(),
        "rotation_invariance_passed": True,
        "energy_gradient_finite_difference_max_error": float(np.max(np.abs(fd_gradient - analytic_force))),
        "tangent_finite_difference_max_error": float(np.max(np.abs(fd_tangent - analytic_tangent))),
        "inactive_gap_force_and_tangent_zero": True,
        "zero_gap_reduces_to_linear_isotropic_spring": True,
        "passed": True,
    }


def assemble_base(divisions: int) -> tuple[np.ndarray, int, np.ndarray, list[tuple[float, float, np.ndarray, np.ndarray, int]]]:
    nodes = np.concatenate(
        [np.linspace(EDGES_MM[j], EDGES_MM[j + 1], divisions + 1)[:-1] for j in range(3)]
        + [np.array([LENGTH_MM])]
    )
    beam_dofs = 4 * len(nodes)
    size = beam_dofs + 12
    beam_stiffness = np.zeros((size, size), dtype=float)
    samples: list[tuple[float, float, np.ndarray, np.ndarray, int]] = []
    for element, (left, right) in enumerate(zip(nodes[:-1], nodes[1:])):
        h = float(right - left)
        owner = int(np.searchsorted(EDGES_MM[1:], (left + right) / 2.0, side="right"))
        y_ids = np.array([4 * element, 4 * element + 1, 4 * (element + 1), 4 * (element + 1) + 1])
        z_ids = y_ids + 2
        beam_stiffness[np.ix_(y_ids, y_ids)] += EI_NMM2 * beam_matrix(h)
        beam_stiffness[np.ix_(z_ids, z_ids)] += EI_NMM2 * beam_matrix(h)
        body = beam_dofs + 4 * owner
        for point, weight in zip(GAUSS_X, GAUSS_W):
            t = (float(point) + 1.0) / 2.0
            x = left + h * t
            w = h * float(weight) / 2.0
            shape = shapes(t, h)
            relative = np.zeros((2, size), dtype=float)
            relative[0, y_ids] = shape
            relative[0, [body, body + 1]] = [-1.0, -(x - CENTERS_MM[owner])]
            relative[1, z_ids] = shape
            relative[1, [body + 2, body + 3]] = [-1.0, -(x - CENTERS_MM[owner])]
            active_columns = np.flatnonzero(np.any(relative != 0.0, axis=0))
            samples.append((float(x), w, active_columns, relative[:, active_columns].copy(), owner))
    assert np.allclose(beam_stiffness, beam_stiffness.T, rtol=0, atol=1e-8)
    return nodes, beam_dofs, beam_stiffness, samples


def load_vector(bolt: dict, beam_dofs: int) -> tuple[np.ndarray, np.ndarray]:
    expected = np.zeros((3, 2, 2), dtype=float)  # receiver, [force, moment], [Y,Z]
    for j, member in enumerate(MEMBERS):
        wrench = bolt["derived_member_wrenches_at_receiver_interval_midpoints"][member]
        force = np.array(wrench["force_xyz_n"], dtype=float)
        moment = np.array(wrench["moment_xyz_nmm"], dtype=float)
        assert abs(moment[0]) < 1e-7
        expected[j, 0, :] = [force[1], force[2]]
        expected[j, 1, :] = [moment[2], -moment[1]]
    assert np.max(np.abs(np.sum(expected[:, 0, :], axis=0))) < 1e-8
    assert np.max(np.abs(np.sum(expected[:, 1, :] + CENTERS_MM[:, None] * expected[:, 0, :], axis=0))) < 1e-7
    loads = np.zeros(beam_dofs + 12, dtype=float)
    for j in range(3):
        body = beam_dofs + 4 * j
        # Connector actions on source wood are balanced by opposite external
        # receiver loads. No copy of these loads is placed on the bolt beam.
        loads[[body, body + 1, body + 2, body + 3]] = [
            -expected[j, 0, 0], -expected[j, 1, 0],
            -expected[j, 0, 1], -expected[j, 1, 1],
        ]
    return loads, expected


def evaluate(
    q: np.ndarray,
    loads: np.ndarray,
    beam_stiffness: np.ndarray,
    samples: list[tuple[float, float, np.ndarray, np.ndarray, int]],
    k: float,
    gap: float,
) -> tuple[float, np.ndarray, np.ndarray, list[tuple[float, float, np.ndarray, int, np.ndarray]]]:
    tangent = beam_stiffness.copy()
    residual = beam_stiffness @ q - loads
    potential = 0.5 * float(q @ beam_stiffness @ q) - float(loads @ q)
    fields = []
    for x, weight, active_columns, relative_map, owner in samples:
        relative = relative_map @ q[active_columns]
        force, local_tangent = radial_force_tangent(relative, gap, k)
        potential += weight * radial_potential(relative, gap, k)
        residual[active_columns] += weight * relative_map.T @ force
        tangent[np.ix_(active_columns, active_columns)] += weight * relative_map.T @ local_tangent @ relative_map
        fields.append((x, weight, force, owner, relative))
    assert np.allclose(tangent, tangent.T, rtol=0, atol=1e-7)
    return potential, residual, tangent, fields


def solve_gap_case(bolt: dict, k: float, target_gap: float, divisions: int) -> dict:
    nodes, beam_dofs, beam_stiffness, samples = assemble_base(divisions)
    loads, expected = load_vector(bolt, beam_dofs)
    q = np.zeros_like(loads)
    pinned = np.arange(4)
    free = np.arange(4, len(q))
    force_scale = max(1.0, float(np.max(np.abs(loads[0::4]))), float(np.max(np.abs(loads[2::4]))))
    moment_scale = max(1.0, float(np.max(np.abs(loads[1::4]))), float(np.max(np.abs(loads[3::4]))))
    scale = np.tile([force_scale, moment_scale, force_scale, moment_scale], len(q) // 4)
    iteration_log = []
    attempted_steps = []
    failure_detail_examples = []
    seen_failure_types = set()
    min_scaled_cholesky_pivot = float("inf")
    total_iterations = 0
    terminal_failure = None
    gap_zero_seed_residual = None

    def dof_label(index: int) -> str:
        components = ["wY_mm", "slopeY", "wZ_mm", "slopeZ"]
        if index < beam_dofs:
            return f"beam_node_{index // 4}_{components[index % 4]}"
        body_index = (index - beam_dofs) // 4
        return f"{MEMBERS[body_index]}_{components[index % 4]}"

    def summarized_failure(fail):
        if fail is None:
            return None
        return {key: value for key, value in fail.items()
                if key not in ("zero_tangent_dofs_with_residual", "receiver_engaged_length_at_predictor_mm")}

    def keep_failure_example(fail):
        if fail is not None and fail.get("type") not in seen_failure_types:
            seen_failure_types.add(fail.get("type"))
            failure_detail_examples.append(fail)

    def newton_at_gap(start: np.ndarray, step_gap: float):
        nonlocal min_scaled_cholesky_pivot
        trial_q = start.copy()
        for iteration in range(1, MAX_NEWTON_PER_STEP + 1):
            energy, residual, hessian, stage_fields = evaluate(
                trial_q, loads, beam_stiffness, samples, k, step_gap
            )
            residual_norm = float(np.max(np.abs(residual[free] / scale[free])))
            if residual_norm <= RESIDUAL_TOL:
                return trial_q, iteration - 1, residual_norm, None

            h_free = hessian[np.ix_(free, free)]
            diagonal = np.diag(h_free)
            if np.any(~np.isfinite(diagonal)) or np.any(diagonal <= 0.0):
                active_lengths = np.zeros(3)
                for _, weight, _, owner, relative in stage_fields:
                    if np.linalg.norm(relative) > step_gap:
                        active_lengths[owner] += weight
                zero_diagonal = free[(~np.isfinite(diagonal)) | (diagonal <= 0.0)]
                finite_diagonal = diagonal[np.isfinite(diagonal)]
                minimum_diagonal = float(np.min(finite_diagonal)) if finite_diagonal.size else None
                fail = {
                    "type": "nonpositive_or_nonfinite_tangent_diagonal",
                    "gap_mm": step_gap,
                    "iteration": iteration,
                    "minimum_tangent_diagonal": minimum_diagonal,
                    "receiver_engaged_length_at_predictor_mm": active_lengths.tolist(),
                    "zero_tangent_dofs_with_residual": [
                        {"dof": dof_label(int(i)), "residual_N_or_Nmm": float(residual[i]),
                         "external_load_N_or_Nmm": float(loads[i])}
                        for i in zero_diagonal
                    ],
                }
                return trial_q, iteration, residual_norm, fail

            dof_scale = 1.0 / np.sqrt(diagonal)
            scaled_hessian = h_free * dof_scale[:, None] * dof_scale[None, :]
            try:
                lower = np.linalg.cholesky(scaled_hessian)
            except np.linalg.LinAlgError:
                return trial_q, iteration, residual_norm, {
                    "type": "singular_or_indefinite_tangent_internal_mechanism",
                    "gap_mm": step_gap, "iteration": iteration,
                }
            pivots = np.diag(lower) ** 2
            pivot_ratio = float(np.min(pivots) / max(float(np.max(pivots)), 1.0))
            min_scaled_cholesky_pivot = min(min_scaled_cholesky_pivot, pivot_ratio)
            if pivot_ratio <= CHOLESKY_PIVOT_RATIO_TOL:
                return trial_q, iteration, residual_norm, {
                    "type": "near_singular_tangent_internal_mechanism",
                    "gap_mm": step_gap, "iteration": iteration,
                    "scaled_pivot_ratio": pivot_ratio,
                }

            scaled_rhs = -dof_scale * residual[free]
            y = np.linalg.solve(lower.T, np.linalg.solve(lower, scaled_rhs))
            delta_free = dof_scale * y
            descent = float(residual[free] @ delta_free)
            if not math.isfinite(descent) or descent >= 0.0:
                return trial_q, iteration, residual_norm, {
                    "type": "newton_direction_not_descent", "gap_mm": step_gap,
                    "iteration": iteration, "directional_derivative": descent,
                }

            accepted = False
            alpha = 1.0
            for _ in range(MAX_LINESEARCH_HALVINGS + 1):
                candidate = trial_q.copy()
                candidate[free] += alpha * delta_free
                candidate_energy, _, _, _ = evaluate(
                    candidate, loads, beam_stiffness, samples, k, step_gap
                )
                if math.isfinite(candidate_energy) and candidate_energy <= energy + 1e-4 * alpha * descent:
                    trial_q = candidate
                    accepted = True
                    break
                alpha *= 0.5
            if not accepted:
                return trial_q, iteration, residual_norm, {
                    "type": "bounded_line_search_failure", "gap_mm": step_gap,
                    "iteration": iteration, "halvings": MAX_LINESEARCH_HALVINGS,
                }
        _, residual, _, _ = evaluate(trial_q, loads, beam_stiffness, samples, k, step_gap)
        return trial_q, MAX_NEWTON_PER_STEP, float(np.max(np.abs(residual[free] / scale[free]))), {
            "type": "newton_iteration_budget_exhausted", "gap_mm": step_gap,
            "iterations": MAX_NEWTON_PER_STEP,
        }

    # A positive-gap run starts from its exactly solved g=0 field. This is a
    # numerical seed, not a physical loading/contact history.
    if target_gap > 0.0:
        _, _, zero_gap_tangent, _ = evaluate(q, loads, beam_stiffness, samples, k, 0.0)
        q[free] = np.linalg.solve(zero_gap_tangent[np.ix_(free, free)], loads[free])
        _, seed_residual, _, _ = evaluate(q, loads, beam_stiffness, samples, k, 0.0)
        gap_zero_seed_residual = float(np.max(np.abs(seed_residual[free] / scale[free])))
        if gap_zero_seed_residual > RESIDUAL_TOL:
            terminal_failure = {"type": "gap_zero_initial_seed_failed_equilibrium_check",
                                "scaled_residual": gap_zero_seed_residual}

    if target_gap == 0.0 and terminal_failure is None:
        candidate, iters, residual_norm, fail = newton_at_gap(q, 0.0)
        total_iterations += iters + (1 if fail is None else 0)
        attempted_steps.append({"from_gap_mm": 0.0, "to_gap_mm": 0.0,
                                "accepted": fail is None, "newton_iterations": iters,
                                "scaled_residual": residual_norm, "failure": summarized_failure(fail)})
        keep_failure_example(fail)
        if fail is None:
            q = candidate
            iteration_log.append({"gap_mm": 0.0, "iterations": iters, "scaled_residual": residual_norm})
            current_gap = 0.0
        else:
            terminal_failure = fail
            current_gap = 0.0
    elif target_gap > 0.0 and terminal_failure is None:
        current_gap = 0.0
        initial_step = target_gap / INITIAL_GAP_STEPS
        step_size = initial_step
        minimum_step = target_gap / (2 ** MAX_GAP_HALVINGS)
        accepted_count = 0
        while current_gap < target_gap - 1e-14:
            if accepted_count >= MAX_HOMOTOPY_ACCEPTED_STEPS:
                terminal_failure = {"type": "accepted_homotopy_step_budget_exhausted",
                                    "current_gap_mm": current_gap, "accepted_steps": accepted_count}
                break
            if len(attempted_steps) >= MAX_HOMOTOPY_ATTEMPTS:
                terminal_failure = {"type": "homotopy_attempt_budget_exhausted",
                                    "current_gap_mm": current_gap,
                                    "attempts": len(attempted_steps)}
                break
            next_gap = min(target_gap, current_gap + step_size)
            candidate, iters, residual_norm, fail = newton_at_gap(q, next_gap)
            total_iterations += iters + (1 if fail is None else 0)
            attempted_steps.append({"from_gap_mm": current_gap, "to_gap_mm": next_gap,
                                    "attempted_step_mm": next_gap - current_gap,
                                    "accepted": fail is None, "newton_iterations": iters,
                                    "scaled_residual": residual_norm, "failure": summarized_failure(fail)})
            keep_failure_example(fail)
            if fail is not None:
                if step_size / 2.0 < minimum_step:
                    terminal_failure = {
                        "type": "minimum_gap_increment_reached_after_newton_tangent_failure",
                        "current_gap_mm": current_gap,
                        "smallest_failed_increment_mm": next_gap - current_gap,
                        "minimum_increment_mm": minimum_step,
                        "last_failure": fail,
                    }
                    break
                step_size = max(step_size / 2.0, minimum_step)
                continue

            q = candidate
            current_gap = next_gap
            accepted_count += 1
            iteration_log.append({"gap_mm": current_gap, "iterations": iters,
                                  "scaled_residual": residual_norm})
            if step_size < initial_step:
                step_size = min(initial_step, 2.0 * step_size)

    else:
        current_gap = 0.0

    if target_gap == 0.0:
        accepted_gaps = [0.0] if terminal_failure is None else []
    else:
        accepted_gaps = [row["gap_mm"] for row in iteration_log]

    if terminal_failure is not None:
        _, last_residual, _, _ = evaluate(q, loads, beam_stiffness, samples, k, current_gap)
        last_residual_norm = float(np.max(np.abs(last_residual[free] / scale[free])))
        attempted_gap_steps = [row["attempted_step_mm"] for row in attempted_steps if "attempted_step_mm" in row]
        accepted_gap_steps = [row["attempted_step_mm"] for row in attempted_steps
                              if row.get("accepted") and "attempted_step_mm" in row]
        return {
            "status": "BOUNDED_FAILURE",
            "failure": terminal_failure,
            "k_line_N_per_mm2": k,
            "gap_mm": target_gap,
            "mesh_divisions_per_receiver": divisions,
            "homotopy_accepted_gaps_mm": accepted_gaps,
            "homotopy_attempt_log": attempted_steps,
            "homotopy_failure_detail_examples": failure_detail_examples,
            "homotopy_attempt_count": len(attempted_steps),
            "accepted_gap_step_count": len(accepted_gaps),
            "minimum_attempted_gap_increment_mm": min(attempted_gap_steps) if attempted_gap_steps else None,
            "minimum_accepted_gap_increment_mm": min(accepted_gap_steps) if accepted_gap_steps else None,
            "homotopy_newton_iteration_log": iteration_log,
            "total_newton_iterations": total_iterations,
            "minimum_gap_increment_mm": target_gap / (2 ** MAX_GAP_HALVINGS) if target_gap else None,
            "gap_zero_linear_seed_scaled_residual": gap_zero_seed_residual,
            "last_accepted_homotopy_gap_mm": current_gap,
            "last_accepted_state_scaled_residual": last_residual_norm,
            "target_gap_middle_cut_internal_force_on_left_YZ_N": None,
            "target_gap_middle_cut_internal_couple_on_left_My_Mz_Nmm": None,
            "target_gap_response_available": False,
            "physical_bolt_ends_free": True,
            "no_stabilizing_spring_or_regularization": True,
        }

    final_energy, final_residual, _, fields = evaluate(q, loads, beam_stiffness, samples, k, target_gap)
    active_length = np.zeros(3)
    reactions = np.zeros_like(expected)
    cut_fields = []
    for x, weight, force, owner, relative in fields:
        if np.linalg.norm(relative) > target_gap:
            active_length[owner] += weight
        reactions[owner, 0] += weight * force
        reactions[owner, 1] += weight * (x - CENTERS_MM[owner]) * force
        cut_fields.append((x, weight, force))
    receiver_force_moment_error = float(np.max(np.abs(reactions - expected)))

    def cut(x: float) -> tuple[np.ndarray, np.ndarray]:
        shear = sum((weight * force for s, weight, force in cut_fields if s < x), start=np.zeros(2))
        couple_arms = sum((weight * (x - s) * force for s, weight, force in cut_fields if s < x), start=np.zeros(2))
        return shear, couple_arms

    middle_shear, middle_arms = cut(MIDDLE_CUT_MM)
    middle_couple = np.array([middle_arms[1], -middle_arms[0]])
    end_shear, end_arms = cut(LENGTH_MM)
    end_couple = np.array([end_arms[1], -end_arms[0]])
    peak_couple = max(float(np.linalg.norm(cut(float(x))[1])) for x in nodes)
    gauge_force_residual = final_residual[pinned[[0, 2]]]
    gauge_moment_residual = final_residual[pinned[[1, 3]]]
    gauge_force = float(np.max(np.abs(gauge_force_residual)))
    gauge_moment = float(np.max(np.abs(gauge_moment_residual)))
    end_force = float(np.linalg.norm(end_shear))
    end_moment = float(np.linalg.norm(end_couple))
    final_scaled_residual = float(np.max(np.abs(final_residual[free] / scale[free])))
    assert gauge_force < force_scale * 2e-7
    assert gauge_moment < moment_scale * 2e-7
    assert receiver_force_moment_error < max(force_scale, moment_scale / LENGTH_MM) * 5e-7
    assert end_force < force_scale * 5e-7
    assert end_moment < moment_scale * 5e-7
    attempted_gap_steps = [row["attempted_step_mm"] for row in attempted_steps if "attempted_step_mm" in row]
    accepted_gap_steps = [row["attempted_step_mm"] for row in attempted_steps
                          if row.get("accepted") and "attempted_step_mm" in row]
    return {
        "status": "CONVERGED",
        "failure": None,
        "k_line_N_per_mm2": k,
        "gap_mm": target_gap,
        "mesh_divisions_per_receiver": divisions,
        "homotopy_accepted_gaps_mm": accepted_gaps,
        "homotopy_attempt_log": attempted_steps,
        "homotopy_failure_detail_examples": failure_detail_examples,
        "homotopy_attempt_count": len(attempted_steps),
        "accepted_gap_step_count": len(accepted_gaps),
        "minimum_attempted_gap_increment_mm": min(attempted_gap_steps) if attempted_gap_steps else None,
        "minimum_accepted_gap_increment_mm": min(accepted_gap_steps) if accepted_gap_steps else None,
        "gap_zero_linear_seed_scaled_residual": gap_zero_seed_residual,
        "homotopy_newton_iteration_log": iteration_log,
        "total_newton_iterations": total_iterations,
        "min_scaled_cholesky_pivot_ratio_seen": min_scaled_cholesky_pivot if math.isfinite(min_scaled_cholesky_pivot) else None,
        "scaled_free_dof_residual": final_scaled_residual,
        "potential_energy_Nmm": final_energy,
        "minimum_gap_increment_mm": target_gap / (2 ** MAX_GAP_HALVINGS) if target_gap else None,
        "last_accepted_homotopy_gap_mm": current_gap,
        "radial_engaged_lengths_by_receiver_mm": active_length.tolist(),
        "radial_engaged_fractions_by_receiver": (active_length / LENGTHS_MM).tolist(),
        "radial_engaged_share_of_total_stack_by_receiver": (active_length / LENGTH_MM).tolist(),
        "middle_cut_internal_force_on_left_YZ_N": middle_shear.tolist(),
        "middle_cut_internal_couple_on_left_My_Mz_Nmm": middle_couple.tolist(),
        "middle_cut_shear_magnitude_N": float(np.linalg.norm(middle_shear)),
        "middle_cut_couple_magnitude_Nmm": float(np.linalg.norm(middle_couple)),
        "sampled_peak_couple_magnitude_Nmm": peak_couple,
        "receiver_force_and_normalized_first_moment_closure_max_N_equivalent": receiver_force_moment_error,
        "free_end_shear_closure_N": end_force,
        "free_end_couple_closure_Nmm": end_moment,
        "gauge_translation_reaction_max_N": gauge_force,
        "gauge_rotation_reaction_max_Nmm": gauge_moment,
        "physical_bolt_ends_free": True,
        "source_lateral_wrenches_applied_once_at_receivers": True,
    }


def load_owner_method():
    sys.dont_write_bytecode = True
    path = OWNER / "diagnose.py"
    spec = importlib.util.spec_from_file_location("pinned_owner_bg003_diagnostic", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    source_hashes = {}
    assert digest(INPUT_PATH) == INPUT_SHA256
    source_hashes[str(INPUT_PATH.relative_to(ROOT))] = INPUT_SHA256
    input_producer = INPUT_DIR / "prepare_inputs.py"
    assert digest(input_producer) == INPUT_PRODUCER_SHA256
    source_hashes[str(input_producer.relative_to(ROOT))] = INPUT_PRODUCER_SHA256
    input_manifest = INPUT_DIR / "SHA256SUMS"
    assert digest(input_manifest) == INPUT_MANIFEST_SHA256
    source_hashes[str(input_manifest.relative_to(ROOT))] = INPUT_MANIFEST_SHA256
    for name, expected in OWNER_PINS.items():
        path = OWNER / name
        actual = digest(path)
        assert actual == expected, f"owner source changed: {path}"
        source_hashes[str(path.relative_to(ROOT))] = actual
    for name, expected in ROTATED_PINS.items():
        path = ROTATED_DIR / name
        actual = digest(path)
        assert actual == expected, f"rotated operator source changed: {path}"
        source_hashes[str(path.relative_to(ROOT))] = actual

    input_packet = json.loads(INPUT_PATH.read_text())
    for pin in input_packet["source_pins"]["case_reports"].values():
        path = ROOT / pin["path"]
        actual = digest(path)
        assert actual == pin["sha256"], f"pinned report changed: {path}"
        source_hashes[str(path.relative_to(ROOT))] = actual
    for pin_name in ("three_member_geometry", "prior_continuous_dowel_method_candidate",
                     "prior_constructed_bearing_profile_result"):
        pin = input_packet["source_pins"][pin_name]
        path = ROOT / pin["path"]
        actual = digest(path)
        assert actual == pin["sha256"], f"pinned geometry/method changed: {path}"
        source_hashes[str(path.relative_to(ROOT))] = actual
    case = next(c for c in input_packet["cases"] if c["case_id"] == CASE_ID)
    assert case["report_status"] == "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY"
    report_pin = input_packet["source_pins"]["case_reports"][CASE_ID]
    report_path = ROOT / report_pin["path"]
    report_sha = digest(report_path)
    assert report_sha == report_pin["sha256"]
    source_hashes[str(report_path.relative_to(ROOT))] = report_sha
    raw_report = json.loads(report_path.read_text())
    assert raw_report["case_id"] == CASE_ID
    assert raw_report["actual_case_demand_usable_for_conditional_joint_checks"] is True
    assert len(raw_report["increments"]) == 7
    raw_full_load = raw_report["increments"][-1]
    assert raw_full_load["load_factor"] == 1.0
    assert raw_full_load["all_five_corner_bodies_raw_and_interval_balance_passed"] is True
    raw_bolt = next(
        b for b in raw_full_load["primary_physical_bolt_groups"]["BG003"]["bolts"]
        if b["axis_id"] == AXIS_ID
    )
    packed_bolt = next(
        b for b in case["increments"][-1]["BG003_bolts"] if b["axis_id"] == AXIS_ID
    )
    assert packed_bolt["axis_id"] == AXIS_ID

    owner_method = load_owner_method()
    beta_values = {str(k): k * LENGTH_MM**4 / EI_NMM2 for k in K_VALUES_N_PER_MM2}
    rows = []
    for k in K_VALUES_N_PER_MM2:
        for gap in (0.0, RADIAL_GAP_MM):
            for divisions in DIVISIONS:
                rows.append(solve_gap_case(packed_bolt, k, gap, divisions))

    g0_matches = []
    owner_refs = {}
    for row in rows:
        if row["status"] != "CONVERGED" or row["gap_mm"] != 0.0:
            continue
        beta = beta_values[str(row["k_line_N_per_mm2"])]
        reference = owner_method.solve_bolt(raw_bolt, beta, row["mesh_divisions_per_receiver"])
        owner_refs[(row["k_line_N_per_mm2"], row["mesh_divisions_per_receiver"])] = reference
        errors = {}
        for key, actual_key in (
            ("middle_cut_internal_force_on_left_YZ_N", "middle_cut_internal_force_on_left_YZ_N"),
            ("middle_cut_internal_couple_on_left_My_Mz_Nmm", "middle_cut_internal_couple_on_left_My_Mz_Nmm"),
        ):
            actual = np.asarray(row[actual_key], dtype=float)
            target = np.asarray(reference[key], dtype=float)
            errors[key] = float(np.linalg.norm(actual - target) / max(float(np.linalg.norm(target)), 1.0))
        for key in ("middle_cut_shear_magnitude_N", "middle_cut_bending_magnitude_Nmm", "sampled_peak_bending_magnitude_Nmm"):
            new_key = {
                "middle_cut_bending_magnitude_Nmm": "middle_cut_couple_magnitude_Nmm",
                "sampled_peak_bending_magnitude_Nmm": "sampled_peak_couple_magnitude_Nmm",
            }.get(key, key)
            errors[key] = abs(row[new_key] - reference[key]) / max(abs(reference[key]), 1.0)
        max_error = max(errors.values())
        g0_matches.append({
            "k_line_N_per_mm2": row["k_line_N_per_mm2"],
            "dimensionless_beta_kL4_over_EI": beta,
            "mesh_divisions_per_receiver": row["mesh_divisions_per_receiver"],
            "max_relative_error_vs_owner_isotropic_solver": max_error,
            "component_errors": errors,
        })
        assert max_error < 2e-7

    refinement = []
    for k in K_VALUES_N_PER_MM2:
        for gap in (0.0, RADIAL_GAP_MM):
            coarse = next(r for r in rows if r["k_line_N_per_mm2"] == k and r["gap_mm"] == gap and r["mesh_divisions_per_receiver"] == 16)
            fine = next(r for r in rows if r["k_line_N_per_mm2"] == k and r["gap_mm"] == gap and r["mesh_divisions_per_receiver"] == 32)
            if coarse["status"] != "CONVERGED" or fine["status"] != "CONVERGED":
                refinement.append({"k_line_N_per_mm2": k, "gap_mm": gap, "status": "NOT_ASSESSABLE_SOLVE_FAILURE"})
                continue
            signed_shear = float(
                np.linalg.norm(np.asarray(coarse["middle_cut_internal_force_on_left_YZ_N"])
                               - np.asarray(fine["middle_cut_internal_force_on_left_YZ_N"]))
                / max(float(np.linalg.norm(fine["middle_cut_internal_force_on_left_YZ_N"])), 1.0)
            )
            signed_moment = float(
                np.linalg.norm(np.asarray(coarse["middle_cut_internal_couple_on_left_My_Mz_Nmm"])
                               - np.asarray(fine["middle_cut_internal_couple_on_left_My_Mz_Nmm"]))
                / max(float(np.linalg.norm(fine["middle_cut_internal_couple_on_left_My_Mz_Nmm"])), 1.0)
            )
            peak = abs(coarse["sampled_peak_couple_magnitude_Nmm"] - fine["sampled_peak_couple_magnitude_Nmm"]) / max(fine["sampled_peak_couple_magnitude_Nmm"], 1.0)
            refinement.append({
                "k_line_N_per_mm2": k,
                "gap_mm": gap,
                "signed_shear_difference_fraction_16_to_32": signed_shear,
                "signed_couple_difference_fraction_16_to_32": signed_moment,
                "sampled_peak_couple_difference_fraction_16_to_32": peak,
                "under_1_percent_all": max(signed_shear, signed_moment, peak) < 0.01,
            })

    all_converged = all(r["status"] == "CONVERGED" for r in rows)
    all_refined = all(r.get("under_1_percent_all", False) for r in refinement)
    output = {
        "status": "PASS_BOUNDED_RADIAL_GAP_DIAGNOSTIC_ONLY" if all_converged and all_refined else "BOUNDED_FAILURE_OR_REFINEMENT_LIMIT",
        "source_sha256": dict(sorted(source_hashes.items())),
        "producer_sha256": digest(Path(__file__)),
        "single_spring_oracles": check_single_spring_oracles(),
        "physical_and_conditional_parameters": {
            "bolt_diameter_mm": DIAMETER_MM,
            "modeled_hole_diameter_mm": HOLE_DIAMETER_MM,
            "radial_clearance_mm": RADIAL_GAP_MM,
            "steel_E_MPa_hypothetical": STEEL_E_MPA,
            "circular_section_I_mm4": I_MM4,
            "EI_Nmm2": EI_NMM2,
            "line_foundation_k_values_N_per_mm2_hypothetical": K_VALUES_N_PER_MM2,
            "radial_potential_per_unit_length": "0.5*k*max(norm(w-u)-g,0)^2",
            "force_per_unit_length": "k*max(rho-g,0)*(w-u)/rho when rho>g; zero otherwise",
            "foundation_inputs_are_physical_calibrations_or_bounds": False,
        },
        "source_case": {
            "case_id": CASE_ID,
            "report_sha256": report_sha,
            "response_increment_count": 7,
            "selected_increment_load_factor": 1.0,
            "selected_increment_all_five_corner_body_balance_passed": True,
            "axis_id": AXIS_ID,
            "exact_source_midpoint_wrenches_from_pinned_input_packet": packed_bolt["derived_member_wrenches_at_receiver_interval_midpoints"],
            "only_this_case_and_bolt_used": True,
        },
        "model": {
            "receiver_order_head_to_nut": MEMBERS,
            "receiver_lengths_mm": LENGTHS_MM.tolist(),
            "continuous_three_receiver_stack": True,
            "middle_receiver_has_no_seam_or_hinge": True,
            "source_lateral_wrenches_applied_once_to_rigid_receivers": True,
            "source_lateral_wrenches_also_applied_to_beam": False,
            "source_axial_X_tie_not_in_lateral_foundation_model": True,
            "physical_bolt_ends_free": True,
            "common_translation_and_slope_gauge_only": True,
            "gauge_reactions_checked": True,
            "nonlinear_gap_homotopy_is_numerical_only": True,
            "no_stabilizing_spring_or_regularization": True,
            "mesh_divisions_per_receiver": DIVISIONS,
        },
        "nonlinear_solve_budget": {
            "accepted_gap_continuation_steps_max": MAX_HOMOTOPY_ACCEPTED_STEPS,
            "gap_continuation_attempts_max": MAX_HOMOTOPY_ATTEMPTS,
            "initial_gap_subdivisions": INITIAL_GAP_STEPS,
            "minimum_increment_bisection_exponent": MAX_GAP_HALVINGS,
            "minimum_gap_increment_at_target_mm": RADIAL_GAP_MM / (2 ** MAX_GAP_HALVINGS),
            "newton_iterations_per_step_max": MAX_NEWTON_PER_STEP,
            "line_search_halvings_max": MAX_LINESEARCH_HALVINGS,
            "scaled_residual_tolerance": RESIDUAL_TOL,
            "near_singular_scaled_cholesky_pivot_ratio_stop": CHOLESKY_PIVOT_RATIO_TOL,
            "tangent_or_newton_step_failure_policy": "reject continuation increment and halve gap step; stop if failure persists at minimum increment",
            "attempt_or_accepted_step_budget_exhaustion_stops": True,
        },
        "g0_agreement_with_established_owner_elastic_solver": g0_matches,
        "scenario_results": rows,
        "signed_refinement": refinement,
        "joint_accepted": False,
        "capacity_calculated": False,
        "native_solve_run": False,
        "actual_bearing_law_or_contact_history_established": False,
        "strength_group_or_full_frame_behavior_established": False,
    }
    text = json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n"
    target = HERE / "diagnostics.json"
    if args.verify:
        assert target.read_text() == text
        print("PASS_BYTE_IDENTICAL_RADIAL_GAP_DIAGNOSTICS")
    else:
        target.write_text(text)
        print(output["status"], len(rows), "bounded scenarios")


if __name__ == "__main__":
    main()
