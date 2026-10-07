"""Finite-motion spring potentials built from exact position/director jets.

The constitutive scenarios match the existing axial, circular-gap and
compression laws. This helper changes their kinematics, not their stiffness
or resistance. Director work produces an explicit spatial couple; dropping
that couple would violate rigid-motion equilibrium.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix


@dataclass(frozen=True)
class ScalarJet:
    value: float
    gradient: np.ndarray
    hessian: np.ndarray

    def scaled(self, factor):
        return ScalarJet(self.value * factor, self.gradient * factor, self.hessian * factor)


@dataclass(frozen=True)
class VectorJet:
    value: np.ndarray
    jacobian: np.ndarray
    hessian: np.ndarray

    def minus(self, other):
        return VectorJet(self.value - other.value, self.jacobian - other.jacobian,
                         self.hessian - other.hessian)

    def times(self, scalar):
        jacobian = self.jacobian * scalar.value + np.outer(self.value, scalar.gradient)
        hessian = self.hessian * scalar.value + np.einsum("i,ab->iab", self.value, scalar.hessian)
        hessian += np.einsum("ia,b->iab", self.jacobian, scalar.gradient)
        hessian += np.einsum("ib,a->iab", self.jacobian, scalar.gradient)
        return VectorJet(self.value * scalar.value, jacobian, hessian)

    def dot(self, other):
        gradient = self.jacobian.T @ other.value + other.jacobian.T @ self.value
        hessian = np.einsum("i,iab->ab", self.value, other.hessian)
        hessian += np.einsum("i,iab->ab", other.value, self.hessian)
        hessian += self.jacobian.T @ other.jacobian + other.jacobian.T @ self.jacobian
        return ScalarJet(float(self.value @ other.value), gradient, hessian)


def aligned_jets(fields: list[dict]) -> tuple[list[VectorJet], np.ndarray, int]:
    """Embed only the nonzero support of source port/director derivatives."""
    if not fields:
        raise ValueError("at least one position/director field required")
    ndof = fields[0]["J_csr"].shape[1]
    support = set()
    for field in fields:
        j = csr_matrix(field["J_csr"])
        h = [csr_matrix(a) for a in field["H_xyz_csr"]]
        if j.shape != (3, ndof) or len(h) != 3 or any(a.shape != (ndof, ndof) for a in h):
            raise ValueError("position/director derivative dimensions differ")
        if not np.isfinite(np.asarray(field["value_xyz"], dtype=float)).all():
            raise ValueError("nonfinite position/director")
        if not np.isfinite(j.data).all() or any(not np.isfinite(a.data).all() for a in h):
            raise ValueError("nonfinite position/director derivatives")
        support.update(j.nonzero()[1])
        for a in h:
            r, c = a.nonzero()
            support.update(r)
            support.update(c)
    indices = np.array(sorted(support), dtype=int)
    result = []
    for field in fields:
        value = np.asarray(field["value_xyz"], dtype=float)
        if value.shape != (3,):
            raise ValueError("three-vector field required")
        j = csr_matrix(field["J_csr"])[:, indices].toarray()
        h = np.asarray([csr_matrix(a)[indices][:, indices].toarray() for a in field["H_xyz_csr"]])
        result.append(VectorJet(value, j, h))
    return result, indices, ndof


def position_field(port: dict) -> dict:
    return {"value_xyz": port["position_xyz_mm"], "J_csr": port["J_csr"], "H_xyz_csr": port["H_xyz_csr"]}


def normal_field(port: dict) -> dict:
    return {"value_xyz": port["normal_xyz"], "J_csr": port["normal_J_csr"],
            "H_xyz_csr": port["normal_H_xyz_csr"]}


def _square_energy(scalar: ScalarJet, stiffness: float) -> ScalarJet:
    return ScalarJet(.5 * stiffness * scalar.value**2,
                     stiffness * scalar.value * scalar.gradient,
                     stiffness * (np.outer(scalar.gradient, scalar.gradient) + scalar.value * scalar.hessian))


def _radius(radial: VectorJet) -> ScalarJet:
    squared = radial.dot(radial)
    radius = float(np.sqrt(max(0., squared.value)))
    if radius <= 0.:
        raise ValueError("radius derivative undefined at zero; use squared zero-gap energy")
    gradient = squared.gradient / (2 * radius)
    hessian = squared.hessian / (2 * radius) - np.outer(squared.gradient, squared.gradient) / (4 * radius**3)
    return ScalarJet(radius, gradient, hessian)


def connector_response(first: dict, second: dict, director: dict, *,
                       axial_stiffness_n_mm=0., lateral_stiffness_n_mm=0.,
                       radial_gap_mm=0., axial_tension_only=True,
                       axial_sign=1., reference_axial_projection_mm=0.) -> dict:
    """Conservative axial/radial potential and spatial force/couple actions.

    Positions can have distinct reference datums, such as a shaft washer
    pressure plane and its actual timber support face. Subtract their signed
    reference projection once; current director transport preserves an exact
    common rigid motion. A unilateral compression contact uses sign=-1.

    The director belongs to the caller's declared host. The returned couple
    is its physical spatial action, separate from exponential-coordinate
    work duals. No washer rotational clamp or friction is introduced.
    """
    values = [axial_stiffness_n_mm, lateral_stiffness_n_mm, radial_gap_mm,
              axial_sign, reference_axial_projection_mm]
    if not np.isfinite(values).all() or min(values[:3]) < 0. or axial_sign not in (-1., 1.):
        raise ValueError("finite nonnegative stiffness/gap and a signed axial direction required")
    (p, other, n), indices, ndof = aligned_jets([first, second, director])
    if abs(np.linalg.norm(n.value) - 1.) > 1e-8:
        raise ValueError("unit material director required")
    relative = p.minus(other)
    projection = n.dot(relative)
    axial = projection.scaled(axial_sign)
    axial = ScalarJet(axial.value - reference_axial_projection_mm, axial.gradient, axial.hessian)
    radial = relative.minus(n.times(projection))
    size = len(indices)
    energy = ScalarJet(0., np.zeros(size), np.zeros((size, size)))
    force_derivative = np.zeros(3)
    director_derivative = np.zeros(3)
    axial_force = 0.
    if axial_stiffness_n_mm and (not axial_tension_only or axial.value > 0.):
        part = _square_energy(axial, axial_stiffness_n_mm)
        energy = ScalarJet(energy.value + part.value, energy.gradient + part.gradient, energy.hessian + part.hessian)
        axial_force = axial_stiffness_n_mm * axial.value
        force_derivative += axial_sign * axial_force * n.value
        director_derivative += axial_sign * axial_force * relative.value
    radius = float(np.linalg.norm(radial.value))
    radial_force = np.zeros(3)
    if lateral_stiffness_n_mm and (radial_gap_mm == 0. or radius > radial_gap_mm):
        if radial_gap_mm == 0.:
            part = radial.dot(radial).scaled(.5 * lateral_stiffness_n_mm)
            radial_force = lateral_stiffness_n_mm * radial.value
        else:
            extension = _radius(radial)
            extension = ScalarJet(extension.value - radial_gap_mm, extension.gradient, extension.hessian)
            part = _square_energy(extension, lateral_stiffness_n_mm)
            radial_force = lateral_stiffness_n_mm * (1 - radial_gap_mm / radius) * radial.value
        energy = ScalarJet(energy.value + part.value, energy.gradient + part.gradient, energy.hessian + part.hessian)
        force_derivative += radial_force
        director_derivative -= projection.value * radial_force + relative.value * float(n.value @ radial_force)
    gradient = np.zeros(ndof)
    gradient[indices] = energy.gradient
    row, col = np.nonzero(energy.hessian)
    hessian = coo_matrix((energy.hessian[row, col], (indices[row], indices[col])), shape=(ndof, ndof)).tocsr()
    couple = -np.cross(n.value, director_derivative)
    force_on_first = -force_derivative
    spatial_residual = np.cross(relative.value, force_on_first) + couple
    return {"energy_nmm": energy.value, "gradient_n": gradient, "hessian_csr": hessian,
            "support_indices": indices, "local_gradient_n": energy.gradient,
            "local_hessian_n_per_mm": energy.hessian,
            "signed_axial_extension_mm": axial.value, "radial_distance_mm": radius,
            "axial_scalar_force_n": axial_force,
            "force_on_first_xyz_n": force_on_first, "force_on_second_xyz_n": force_derivative,
            "moment_on_director_owner_xyz_nmm": couple,
            "pair_spatial_moment_residual_nmm": spatial_residual,
            "director_owner_is_declared_by_caller": True,
            "physical_stiffness_or_resistance_qualified": False}
