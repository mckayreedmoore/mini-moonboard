"""Numerical-only adaptive continuation of the frozen convex contact potential.

The material matrix, physical contact/spring laws and final force tolerance are
unchanged. Levenberg damping belongs only to a scaled Newton step. The original
energy accepts each step, and the original gradient determines convergence.
An inactive, unloaded rigid mode needs no invented physical support or gauge.
"""

from __future__ import annotations

import json
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, diags, eye, vstack
from scipy.sparse.linalg import MatrixRankWarning, spsolve

from scripts import thin_bolted_frame_mechanics as frame

LOADED_PRODUCER_SHA256 = frame.sha(Path(__file__))
FRAME_SHA = "05cdf6897645fe7ee1b72b5b5125c04c68d758108f4860f995cef6aa1b676448"


def physical_fields(K, applied, groups, C, ck, state, *, tangent=False):
    """Exactly the frozen conservative potential, force gradient and Hessian."""
    gradient = K @ state - applied
    energy = .5 * state @ (K @ state) - applied @ state
    H = K.copy() if tangent else None
    forces = []
    for group in groups:
        B = group["B"]
        displacement = np.asarray(B @ state).ravel()
        force, jacobian, spring_energy = frame.spring_constitutive(
            displacement, group["ka"], group["kl"], group["clearance"], group["tension_only"])
        energy += spring_energy
        gradient += B.T @ force
        if tangent:
            H += B.T @ csr_matrix(jacobian) @ B
        forces.append(force)
    displacement = np.asarray(C @ state).ravel()
    normal = ck * np.maximum(displacement, 0.)
    gradient += C.T @ normal
    energy += .5 * np.dot(ck, np.maximum(displacement, 0.) ** 2)
    if tangent:
        active = displacement > 0.
        H += C[active].T @ diags(ck[active]) @ C[active]
    return gradient, float(energy), H, forces, normal, displacement


def numerical_solve(A, b):
    """Sparse direct numerical step; expose singularity through a finite check."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", MatrixRankWarning)
        value = spsolve(A.tocsc(), b)
    return np.asarray(value).ravel()


def compatible_contact_solve(K, applied, groups, contacts, tangents, max_iterations=500):
    """Adapt scaled step damping; preserve the original unilateral floor updates."""
    if frame.sha(Path(frame.__file__)) != FRAME_SHA or frame.sha(Path(__file__)) != LOADED_PRODUCER_SHA256:
        raise ValueError("numerical strategy or frozen physical producer changed")
    C = vstack([row["B"] for row in contacts], format="csr")
    ck = np.array([row["stiffness"] for row in contacts])
    identity = eye(K.shape[0], format="csc")
    q, preconditioner = None, None
    disabled, patterns, history = set(), [], []
    accepted_steps, rejected_trials, maximum_damping = 0, 0, 0.
    damping = 1e-6
    residual, energy = float(abs(applied).max()), None

    def failure(reason):
        return {"converged": False, "termination": reason, "gradient_inf_n": residual,
                "potential_energy_nmm": energy, "diagnostic_last_q": q,
                "numerical_step_strategy": "adaptive-scaled-Levenberg-original-potential",
                "accepted_numerical_steps": accepted_steps, "rejected_numerical_trials": rejected_trials,
                "iteration_history": history, "maximum_transient_scaled_step_regularization": maximum_damping,
                "generalized_residual_tolerance_n": frame.GENERALIZED_RESIDUAL_TOLERANCE_N,
                "physical_residual_uses_unmodified_laws": True,
                "diagnostic_last_q_is_a_converged_or_accepted_force_field": False}

    for floor_iteration in range(10):
        tangent_rows = [row for row in tangents if row["first"] not in disabled]
        linear = K.copy()
        for row in tangent_rows:
            linear += row["stiffness"] * (row["B"].T @ row["B"])
        if q is None:
            initial = linear + C.T @ diags(ck) @ C
            for group in groups:
                initial += group["B"].T @ diags([group["ka"], group["kl"], group["kl"]]) @ group["B"]
            q = numerical_solve(initial, applied)
            if not np.isfinite(q).all():
                q = None
                return failure("bilateral numerical initialization is singular")
            initial_force = applied.copy()
            for group in groups:
                displacement = np.asarray(group["B"] @ q).ravel()
                radius = float(np.linalg.norm(displacement[1:]))
                if group["clearance"] > 0. and radius > 1e-14:
                    offset = np.r_[0., group["kl"] * group["clearance"] * displacement[1:] / radius]
                    initial_force += group["B"].T @ offset
            q = numerical_solve(initial, initial_force)
            if not np.isfinite(q).all():
                q = None
                return failure("directed-gap numerical initialization is singular")
            preconditioner = diags(1. / np.sqrt(np.maximum(abs(initial.diagonal()), 1e-12)))
        converged = False
        for iteration in range(max_iterations):
            gradient, energy, H, forces, normal, displacement = physical_fields(
                linear, applied, groups, C, ck, q, tangent=True)
            residual = float(abs(gradient).max())
            if iteration % 10 == 0 or residual < frame.GENERALIZED_RESIDUAL_TOLERANCE_N:
                history.append({"floor_pattern": floor_iteration, "iteration": iteration,
                                "gradient_inf_n": residual, "physical_potential_energy_nmm": energy,
                                "step_damping": damping, "active_normal_contacts": int(np.count_nonzero(normal > 0.)),
                                "active_radial_groups": int(sum(np.linalg.norm(force[1:]) > 0. for force in forces)),
                                "active_axial_captures": int(sum(row["kind"] == "shaft_end_capture" and force > 0.
                                                                 for row, force in zip(contacts, normal, strict=True))),
                                "active_floor_ports": int(sum(row["kind"] == "floor_normal" and force > 0.
                                                              for row, force in zip(contacts, normal, strict=True)))})
            if residual < frame.GENERALIZED_RESIDUAL_TOLERANCE_N:
                converged = True
                break
            scaled_H = (preconditioner @ H @ preconditioner).tocsc()
            accepted = False
            for _ in range(20):
                scaled_step = numerical_solve(scaled_H + damping * identity, -preconditioner @ gradient)
                step = np.asarray(preconditioner @ scaled_step).ravel()
                if not np.isfinite(step).all():
                    damping *= 10.
                    rejected_trials += 1
                    continue
                largest = float(abs(step).max())
                if largest > 100.:
                    step *= 100. / largest
                slope = float(gradient @ step)
                if slope >= 0.:
                    damping *= 10.
                    rejected_trials += 1
                    continue
                alpha = 1.
                for _ in range(30):
                    candidate = q + alpha * step
                    trial_energy = physical_fields(linear, applied, groups, C, ck, candidate)[1]
                    if trial_energy <= energy + 1e-4 * alpha * slope + 1e-8:
                        prediction = -alpha * slope - .5 * alpha**2 * float(step @ (H @ step))
                        ratio = (energy - trial_energy) / prediction if prediction > 0. else 0.
                        q = candidate
                        maximum_damping = max(maximum_damping, damping)
                        accepted_steps += 1
                        accepted = True
                        if history[-1]["floor_pattern"] == floor_iteration and history[-1]["iteration"] == iteration:
                            history[-1].update(accepted_step_alpha=alpha, accepted_step_inf_mm=float(abs(alpha * step).max()),
                                               accepted_original_energy_nmm=trial_energy, original_model_reduction_ratio=ratio)
                        if ratio < .25 or alpha < .25:
                            damping = min(damping * 10., 1e8)
                        elif ratio > .75 and alpha >= .5:
                            damping = max(damping * .25, 1e-12)
                        break
                    rejected_trials += 1
                    alpha *= .5
                if accepted:
                    break
                damping *= 10.
                if damping > 1e8:
                    break
            if not accepted:
                return failure("adaptive original-potential numerical line search")
        if not converged:
            # Report the actual last accepted iterate, rather than stale pre-step fields.
            gradient, energy, _, _, _, _ = physical_fields(linear, applied, groups, C, ck, q)
            residual = float(abs(gradient).max())
            return failure("adaptive Newton iteration limit")
        floor_normal = defaultdict(float)
        for row, force in zip(contacts, normal, strict=True):
            if row["kind"] == "floor_normal":
                floor_normal[row["first"]] += force
        next_disabled = {name for name, force in floor_normal.items() if force <= 1e-7}
        if next_disabled == disabled:
            break
        pattern = tuple(sorted(next_disabled))
        if pattern in patterns:
            return failure("repeated floor-bearing pattern")
        patterns.append(pattern)
        disabled = next_disabled
    else:
        return failure("floor-bearing iteration limit")
    return {"converged": True, "q": q, "connector_local_force_n": forces,
            "normal_contact_force_n": normal, "normal_contact_displacement_mm": displacement,
            "gradient_inf_n": residual, "potential_energy_nmm": energy,
            "generalized_residual_tolerance_n": frame.GENERALIZED_RESIDUAL_TOLERANCE_N,
            "newton_iterations": iteration + 1, "floor_pattern_iterations": floor_iteration + 1,
            "accepted_numerical_steps": accepted_steps, "rejected_numerical_trials": rejected_trials,
            "iteration_history": history, "maximum_transient_scaled_step_regularization": maximum_damping,
            "physical_residual_uses_unmodified_laws": True, "nonbearing_no_slip_removed": sorted(disabled),
            "active_contacts": int(np.count_nonzero(normal > 0.)),
            "numerical_step_strategy": "adaptive-scaled-Levenberg-original-potential",
            "termination": "constitutive equilibrium and floor-bearing pattern converged"}


def source_pins():
    pins = {"scripts/thin_bolted_numerical_step.py": LOADED_PRODUCER_SHA256,
            "scripts/thin_bolted_frame_mechanics.py": FRAME_SHA}
    if any(frame.sha(frame.ROOT / path) != digest for path, digest in pins.items()):
        raise ValueError("numerical strategy source differs")
    return pins


def main():
    print(json.dumps({"source_sha256": source_pins(), "physical_laws_changed": False,
                      "force_tolerance_n": frame.GENERALIZED_RESIDUAL_TOLERANCE_N}))


if __name__ == "__main__":
    main()
