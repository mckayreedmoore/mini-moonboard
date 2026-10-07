"""Conditional finite-rotation beam and rigid-arm primitives; no frame solver.

World node state is (u_mm, 1000*theta_rad). Local elastic constitutive behavior
reuses the existing small-strain Timoshenko beam. The corotational frame follows
the current chord and averaged nodal second directors. Energy and residual are
analytic; tangent is a documented central derivative of the analytic residual.
This is a method utility, not nonlinear assembly or physical-joint acceptance.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scripts.thin_bolted_frame_mechanics import beam_stiffness

ROTATION_SCALE = 1000.
BRANCH_MARGIN = 1e-6
SOURCES = [
    {"url": "https://kth.diva-portal.org/smash/get/diva2:526302/FULLTEXT02.pdf",
     "locator": "Thanh Nam Le (2012), chapter 3.1-3.3: moving chord/director frame, local rotations and work-conjugate transformations",
     "use": "Corotational kinematic construction; this utility uses the existing local Timoshenko matrix, not the thesis's complete dynamic/warping element."},
    {"url": "https://arxiv.org/pdf/1812.01537",
     "locator": "Sola, Deray and Atchuthan, A micro Lie theory, Appendix B, SO(3) exp/log and Jacobians, equations 143-146",
     "use": "SO(3) left exponential-map Jacobian, inverse and adjoint conventions."},
]


def vector(value, length: int) -> np.ndarray:
    out = np.asarray(value, dtype=float)
    if out.shape != (length,) or not np.isfinite(out).all():
        raise ValueError(f"finite vector of length {length} required")
    return out


def skew(value) -> np.ndarray:
    x, y, z = vector(value, 3)
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def check_rotation(matrix) -> np.ndarray:
    out = np.asarray(matrix, dtype=float)
    if (out.shape != (3, 3) or not np.isfinite(out).all()
            or np.linalg.norm(out.T @ out - np.eye(3)) > 1e-8
            or abs(np.linalg.det(out) - 1.) > 1e-8):
        raise ValueError("proper orthonormal right-handed rotation required")
    return out


def so3_exp(theta) -> np.ndarray:
    theta = vector(theta, 3)
    angle = np.linalg.norm(theta)
    if angle >= np.pi - BRANCH_MARGIN:
        raise ValueError("rotation-vector chart near/beyond pi is unsupported")
    a = skew(theta)
    if angle < 1e-4:
        x = angle * angle
        sine = 1. - x / 6. + x * x / 120. - x**3 / 5040.
        cosine = .5 - x / 24. + x * x / 720. - x**3 / 40320.
    else:
        sine, cosine = np.sin(angle) / angle, (1. - np.cos(angle)) / angle**2
    return np.eye(3) + sine * a + cosine * a @ a


def so3_log(matrix) -> np.ndarray:
    rotation = check_rotation(matrix)
    sine_axis = .5 * np.array([rotation[2, 1] - rotation[1, 2],
                               rotation[0, 2] - rotation[2, 0],
                               rotation[1, 0] - rotation[0, 1]])
    sine = np.linalg.norm(sine_axis)
    cosine = .5 * (np.trace(rotation) - 1.)
    angle = np.arctan2(sine, cosine)
    if angle >= np.pi - BRANCH_MARGIN:
        raise ValueError("SO(3) logarithm near pi is unsupported")
    if angle < 1e-4:
        x = angle * angle
        return sine_axis * (1. + x / 6. + 7. * x * x / 360.)
    return sine_axis * (angle / sine)


def so3_left_jacobian(theta) -> np.ndarray:
    theta = vector(theta, 3)
    angle = np.linalg.norm(theta)
    if angle >= np.pi - BRANCH_MARGIN:
        raise ValueError("rotation-vector chart near/beyond pi is unsupported")
    a = skew(theta)
    if angle < 1e-4:
        x = angle**2
        b, c = .5 - x / 24. + x*x / 720., 1./6. - x / 120. + x*x / 5040.
    else:
        b, c = (1. - np.cos(angle)) / angle**2, (angle - np.sin(angle)) / angle**3
    return np.eye(3) + b * a + c * a @ a


def so3_left_jacobian_inverse(theta) -> np.ndarray:
    theta = vector(theta, 3)
    angle = np.linalg.norm(theta)
    if angle >= np.pi - BRANCH_MARGIN:
        raise ValueError("rotation-vector chart near/beyond pi is unsupported")
    a = skew(theta)
    if angle < 1e-4:
        x = angle**2
        c = 1./12. + x / 720. + x*x / 30240.
    else:
        c = (1. - .5 * angle / np.tan(.5 * angle)) / angle**2
    return np.eye(3) - .5 * a + c * a @ a


def rigid_port(point, center, q, basis=None) -> tuple[np.ndarray, np.ndarray]:
    """Exact world point and world 3x6 Jacobian for world or local-basis q.

    basis columns map local translation/rotation coordinates to world. State
    rotations are absolute rotation vectors about the reference center. Force
    dual is J.T@F; its rotation block is NOT physical moment divided by1000
    unless the exponential-map Jacobian is identity.
    """
    point, center, q = vector(point, 3), vector(center, 3), vector(q, 6)
    transform = np.eye(3) if basis is None else check_rotation(basis)
    theta = transform @ q[3:] / ROTATION_SCALE
    arm = so3_exp(theta) @ (point - center)
    jacobian = np.column_stack((transform,
                               -skew(arm) @ so3_left_jacobian(theta) @ transform / ROTATION_SCALE))
    return center + transform @ q[:3] + arm, jacobian


def rigid_port_force_dual(point, center, q, force, basis=None) -> np.ndarray:
    return rigid_port(point, center, q, basis)[1].T @ vector(force, 3)


def rigid_port_wrench_dual(point, center, q, force, moment, basis=None) -> np.ndarray:
    """Point force and world spatial couple mapped by the exact arm/rotation dual.

    Physical center moment is arm cross force plus the point couple. The
    exponential-map Jacobian converts that spatial moment to coordinate work.
    """
    q = vector(q, 6)
    transform = np.eye(3) if basis is None else check_rotation(basis)
    dual = rigid_port_force_dual(point, center, q, force, basis)
    theta = transform @ q[3:] / ROTATION_SCALE
    dual[3:] += transform.T @ so3_left_jacobian(theta).T @ vector(moment, 3) / ROTATION_SCALE
    return dual


def physical_rotation_moment(theta, scaled_rotation_dual) -> np.ndarray:
    """Recover world spatial moment from work-conjugate world q-rot dual."""
    return so3_left_jacobian_inverse(theta).T @ vector(scaled_rotation_dual, 3) * ROTATION_SCALE


@dataclass(frozen=True)
class CorotationalBeam:
    """Objective small-local-deformation elastic beam on a bounded SO(3) chart.

    reference_basis columns are [grain/chord, section_u, section_v], whereas the
    existing linear frame's R stores those axes as ROWS. Pass R.T here. Each
    q is world [u,1000*theta] per node, flattened node1 then node2.
    """

    reference_positions: np.ndarray
    reference_basis: np.ndarray
    local_stiffness: np.ndarray
    tangent_step_mm: float = 1e-3

    @classmethod
    def from_properties(cls, positions, basis, area, inertia_y, inertia_z,
                        torsion_j, elastic_modulus, shear_modulus, shear_factor=5./6.,
                        tangent_step_mm=1e-3):
        positions = np.asarray(positions, dtype=float)
        basis = check_rotation(basis)
        if positions.shape != (2, 3) or not np.isfinite(positions).all():
            raise ValueError("two finite world reference positions required")
        chord = positions[1] - positions[0]
        length = np.linalg.norm(chord)
        if length <= 1e-8 or np.linalg.norm(chord / length - basis[:, 0]) > 1e-8:
            raise ValueError("positive chord and matching reference basis required")
        if tangent_step_mm <= 0 or not np.isfinite(tangent_step_mm):
            raise ValueError("positive finite tangent difference step required")
        stiffness = beam_stiffness(length, area, inertia_y, inertia_z, torsion_j,
                                   elastic_modulus, shear_modulus, shear_factor)
        return cls(positions.copy(), basis.copy(), stiffness, tangent_step_mm)

    def deformation(self, q) -> tuple[np.ndarray, np.ndarray, dict]:
        q = vector(q, 12).reshape(2, 6)
        positions = self.reference_positions + q[:, :3]
        theta = q[:, 3:] / ROTATION_SCALE
        rotations = [so3_exp(t) for t in theta]
        nodal_jacobians = [so3_left_jacobian(t) for t in theta]
        chord = positions[1] - positions[0]
        length = np.linalg.norm(chord)
        if length <= 1e-8:
            raise ValueError("collapsed chord is unsupported")
        e1 = chord / length
        directors = [r @ self.reference_basis[:, 1] for r in rotations]
        average = .5 * (directors[0] + directors[1])
        projected = average - e1 * (e1 @ average)
        director_norm = np.linalg.norm(projected)
        if director_norm <= 1e-8:
            raise ValueError("averaged director parallel to chord or cancels; unsupported")
        e2 = projected / director_norm
        e3 = np.cross(e1, e2)
        frame = np.column_stack((e1, e2, e3))
        local_rotations = [so3_log(frame.T @ r @ self.reference_basis) for r in rotations]
        if max(np.linalg.norm(r) for r in local_rotations) >= np.pi / 2. - BRANCH_MARGIN:
            raise ValueError("90-degree local director/rotation region is unsupported")
        reference_length = np.linalg.norm(self.reference_positions[1] - self.reference_positions[0])
        d = np.zeros(12)
        d[6] = length - reference_length
        d[3:6], d[9:12] = local_rotations
        jacobian = np.zeros((12, 12))
        inverses = [so3_left_jacobian_inverse(r) for r in local_rotations]
        for column in range(12):
            node, coordinate = divmod(column, 6)
            dc = np.zeros(3)
            omega = [np.zeros(3), np.zeros(3)]
            if coordinate < 3:
                dc[coordinate] = -1. if node == 0 else 1.
            else:
                omega[node] = nodal_jacobians[node][:, coordinate - 3] / ROTATION_SCALE
            de1 = (np.eye(3) - np.outer(e1, e1)) @ dc / length
            da = .5 * (np.cross(omega[0], directors[0]) + np.cross(omega[1], directors[1]))
            dp = da - de1 * (e1 @ average) - e1 * (de1 @ average + e1 @ da)
            de2 = (np.eye(3) - np.outer(e2, e2)) @ dp / director_norm
            de3 = np.cross(de1, e2) + np.cross(e1, de2)
            frame_omega = .5 * (np.cross(e1, de1) + np.cross(e2, de2) + np.cross(e3, de3))
            jacobian[6, column] = e1 @ dc
            jacobian[3:6, column] = inverses[0] @ frame.T @ (omega[0] - frame_omega)
            jacobian[9:12, column] = inverses[1] @ frame.T @ (omega[1] - frame_omega)
        return d, jacobian, {"current_length_mm": length, "frame_columns_world": frame,
                              "local_rotations_rad": np.asarray(local_rotations),
                              "projected_average_director_norm": director_norm}

    def energy(self, q) -> float:
        d = self.deformation(q)[0]
        return float(.5 * d @ self.local_stiffness @ d)

    def residual(self, q) -> np.ndarray:
        d, jacobian, _ = self.deformation(q)
        return jacobian.T @ (self.local_stiffness @ d)

    def tangent(self, q, step_mm=None) -> np.ndarray:
        """Central derivative of analytic residual; no hidden symmetrization."""
        q = vector(q, 12)
        step = self.tangent_step_mm if step_mm is None else float(step_mm)
        if not np.isfinite(step) or step <= 0:
            raise ValueError("positive finite tangent difference step required")
        eye = np.eye(12) * step
        return np.column_stack([(self.residual(q + h) - self.residual(q - h)) / (2. * step)
                                for h in eye])

    def response(self, q, tangent=True) -> dict:
        d, jacobian, metadata = self.deformation(q)
        result = {"energy_nmm": float(.5 * d @ self.local_stiffness @ d),
                  "residual_work_conjugate_q": jacobian.T @ self.local_stiffness @ d,
                  "deformation_local": d, **metadata}
        if tangent:
            result["tangent_work_conjugate_q"] = self.tangent(q)
            result["tangent_method"] = "central difference of analytic residual; default q-step1e-3mm, rotation step1e-6rad"
        return result
