"""Objective mechanical adapter over frozen timber, fitting and shaft data.

No geometry, contact law or candidate solve is created here. Existing indices
are preserved; the seventy omitted first shaft twists are appended as full
coordinates. The frozen circular corotational proxy has no authenticated
finite common-roll gauge, so this adapter imposes no gauge or torque support.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.linalg import block_diag
from scipy.sparse import coo_matrix, csr_matrix

from scripts.thin_bolted_corotational_methods import (
    BRANCH_MARGIN,
    ROTATION_SCALE,
    CorotationalBeam,
    check_rotation,
    rigid_port,
    skew,
    so3_exp,
    so3_left_jacobian,
    so3_left_jacobian_inverse,
    so3_log,
    vector,
)

ROOT = Path(__file__).resolve().parents[1]
FROZEN_SOURCES = {
    "scripts/thin_bolted_corotational_methods.py": "7638a09c145135a19dcccb7cd84a01b8a01d2a4465b02ebfc33372e672e5ebc8",
    "scripts/thin_bolted_frame_mechanics.py": "05cdf6897645fe7ee1b72b5b5125c04c68d758108f4860f995cef6aa1b676448",
    "scripts/thin_bolted_common_shaft.py": "0ff8c52a36f168cba0bd3fed2d592daa9e5d9de5facbc650b151f64c2f23f4eb",
    "scripts/thin_bolted_steel_resistance.py": "5a41c7d4a46bf1857e4c756fb35c12cc4253d2fd74f49de01a95c275a8c80602",
}


def source_pins(additional=None):
    """Authenticate reused primitives and any parent-supplied input pins."""
    if any(key in FROZEN_SOURCES and value != FROZEN_SOURCES[key]
           for key, value in (additional or {}).items()):
        raise ValueError("parent pins conflict with a frozen mechanics primitive")
    pins = {**FROZEN_SOURCES, **(additional or {})}
    for path, expected in pins.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError("finite mechanics source/input differs: " + path)
    return pins


def derivative_hessian(jacobian, q, step_mm=1e-3):
    """Central derivative of an analytic Jacobian; no symmetrization.

    Coordinates are mm or 1000*rad. The default rotation difference is
    therefore 1e-6 rad. Unsupported SO(3) branches propagate as errors.
    """
    q = np.asarray(q, dtype=float)
    if q.ndim != 1 or not np.isfinite(q).all() or not np.isfinite(step_mm) or step_mm <= 0:
        raise ValueError("finite state and positive derivative step required")
    return np.stack([(jacobian(q + h) - jacobian(q - h)) / (2 * step_mm)
                     for h in np.eye(len(q)) * step_mm], axis=2)


def interpolated_rotation(q, t, basis=None):
    """R(t)=R0 Exp[t Log(R0.T R1)] and its spatial angular-work map.

    The 3x12 map sends coordinate increments to a WORLD spatial infinitesimal
    rotation. Translational columns are zero. This interpolation is objective
    under superposed proper world rotation; linear rotation-vector averaging
    would not have that property.
    """
    q = vector(q, 12).reshape(2, 6)
    if not np.isfinite(t) or not 0 <= t <= 1:
        raise ValueError("interpolation station in [0,1] required")
    basis = np.eye(3) if basis is None else check_rotation(basis)
    theta = [basis @ row[3:] / ROTATION_SCALE for row in q]
    rotations = [so3_exp(row) for row in theta]
    relative = so3_log(rotations[0].T @ rotations[1])
    if np.linalg.norm(relative) >= np.pi / 2 - BRANCH_MARGIN:
        raise ValueError("90-degree neighboring director turn is unsupported; refine/check the local deformation")
    rotation = rotations[0] @ so3_exp(t * relative)
    mixing = rotations[0] @ so3_left_jacobian(t * relative) @ (
        t * so3_left_jacobian_inverse(relative)) @ rotations[0].T
    angular = np.zeros((3, 12))
    angular[:, 3:6] = (np.eye(3) - mixing) @ so3_left_jacobian(theta[0]) @ basis / ROTATION_SCALE
    angular[:, 9:12] = mixing @ so3_left_jacobian(theta[1]) @ basis / ROTATION_SCALE
    return rotation, angular


def interpolated_point(point, centers, q, t, basis=None):
    """Linearly interpolated center plus a properly rotated eccentric arm.

    Centers follow the current straight segment. This is a discretization of
    a flexible beam, not an exact curved centerline or a beam refinement pass.
    The undeformed Jacobian reproduces the frozen linear point operator.
    """
    point = vector(point, 3)
    centers = np.asarray(centers, dtype=float)
    if centers.shape != (2, 3) or not np.isfinite(centers).all():
        raise ValueError("two finite reference centers required")
    state = vector(q, 12).reshape(2, 6)
    basis = np.eye(3) if basis is None else check_rotation(basis)
    rotation, angular = interpolated_rotation(state.ravel(), t, basis)
    center = (1 - t) * centers[0] + t * centers[1]
    current = center + basis @ ((1 - t) * state[0, :3] + t * state[1, :3])
    arm = rotation @ (point - center)
    jacobian = -skew(arm) @ angular
    jacobian[:, :3], jacobian[:, 6:9] = (1 - t) * basis, t * basis
    return current + arm, jacobian


def interpolated_director(reference_vector, q, t, basis=None):
    rotation, angular = interpolated_rotation(q, t, basis)
    current = rotation @ vector(reference_vector, 3)
    return current, -skew(current) @ angular


@dataclass(frozen=True)
class ObjectiveCondensedFitting:
    """Co-rotating use of the unchanged two-port condensed strip matrix.

    The first flange is only the coordinate anchor. Its pose is removed, not
    clamped. The remaining deformation is expressed in the reference WORLD
    axes used by the frozen matrix. Its six rigid modes must be null in that
    matrix. This is an objective small-local-deformation strip surrogate,
    not bend/heel/hole or actual connector stiffness qualification.
    """

    reference_positions: np.ndarray
    condensed_stiffness: np.ndarray
    tangent_step_mm: float = 1e-3

    def __post_init__(self):
        positions = np.asarray(self.reference_positions, dtype=float)
        stiffness = np.asarray(self.condensed_stiffness, dtype=float)
        if positions.shape != (2, 3) or not np.isfinite(positions).all():
            raise ValueError("two finite fitting port positions required")
        if stiffness.shape != (12, 12) or not np.isfinite(stiffness).all():
            raise ValueError("finite 12x12 condensed fitting stiffness required")
        if not np.isfinite(self.tangent_step_mm) or self.tangent_step_mm <= 0:
            raise ValueError("positive fitting tangent difference step required")
        rigid = np.zeros((12, 6))
        for i, point in enumerate(positions):
            rigid[6*i:6*i+3] = np.c_[np.eye(3), -skew(point - positions[0])]
            rigid[6*i+3:6*i+6, 3:] = np.eye(3)
        denominator = max(np.linalg.norm(stiffness) * np.linalg.norm(rigid), 1.)
        if np.linalg.norm(stiffness @ rigid) / denominator > 1e-10:
            raise ValueError("condensed fitting matrix supplies a rigid-motion clamp")
        if np.linalg.norm(stiffness - stiffness.T) / max(np.linalg.norm(stiffness), 1.) > 1e-10:
            raise ValueError("symmetric fitting energy matrix required")

    def deformation(self, q):
        q = vector(q, 12).reshape(2, 6)
        theta = q[:, 3:] / ROTATION_SCALE
        rotations = [so3_exp(t) for t in theta]
        angular = [so3_left_jacobian(t) / ROTATION_SCALE for t in theta]
        chord = self.reference_positions[1] - self.reference_positions[0] + q[1, :3] - q[0, :3]
        relative = so3_log(rotations[0].T @ rotations[1])
        if np.linalg.norm(relative) >= np.pi / 2 - BRANCH_MARGIN:
            raise ValueError("90-degree fitting relative rotation is unsupported")
        d, jacobian = np.zeros(12), np.zeros((12, 12))
        d[6:9] = rotations[0].T @ chord - (self.reference_positions[1] - self.reference_positions[0])
        d[9:] = relative
        jacobian[6:9, :3], jacobian[6:9, 6:9] = -rotations[0].T, rotations[0].T
        jacobian[6:9, 3:6] = rotations[0].T @ skew(chord) @ angular[0]
        inverse = so3_left_jacobian_inverse(relative) @ rotations[0].T
        jacobian[9:, 3:6], jacobian[9:, 9:] = -inverse @ angular[0], inverse @ angular[1]
        return d, jacobian

    def residual(self, q):
        d, jacobian = self.deformation(q)
        return jacobian.T @ self.condensed_stiffness @ d

    def response(self, q, tangent=True):
        d, jacobian = self.deformation(q)
        result = {"energy_nmm": float(.5 * d @ self.condensed_stiffness @ d),
                  "gradient_n": jacobian.T @ self.condensed_stiffness @ d}
        if tangent:
            q = vector(q, 12)
            step = self.tangent_step_mm
            result["hessian_n_per_mm"] = np.column_stack([
                (self.residual(q + h) - self.residual(q - h)) / (2 * step)
                for h in np.eye(12) * step])
        return result


@dataclass(frozen=True)
class IndexedBeam:
    dofs: np.ndarray
    beam: CorotationalBeam
    storage_basis: np.ndarray

    def response(self, q, tangent=True):
        transform = block_diag(*([self.storage_basis] * 4))
        result = self.beam.response(transform @ q[self.dofs], tangent)
        response = {"energy_nmm": result["energy_nmm"],
                    "gradient_n": transform.T @ result["residual_work_conjugate_q"]}
        if tangent:
            response["hessian_n_per_mm"] = transform.T @ result["tangent_work_conjugate_q"] @ transform
        return response


def checked_beam(positions, basis, stiffness, step):
    positions, basis = np.asarray(positions, dtype=float), check_rotation(basis)
    stiffness = np.asarray(stiffness, dtype=float)
    if positions.shape != (2, 3) or not np.isfinite(positions).all():
        raise ValueError("two finite reference beam positions required")
    chord = positions[1] - positions[0]
    length = np.linalg.norm(chord)
    if length <= 1e-8 or np.linalg.norm(chord / length - basis[:, 0]) > 1e-8:
        raise ValueError("reference beam chord and basis differ")
    if stiffness.shape != (12, 12) or not np.isfinite(stiffness).all():
        raise ValueError("finite 12x12 beam stiffness required")
    return CorotationalBeam(positions.copy(), basis.copy(), stiffness.copy(), step)


def sparse_local(matrix, indices, ndof):
    matrix, indices = np.asarray(matrix), np.asarray(indices, dtype=int)
    row, col = np.nonzero(matrix)
    if matrix.shape[0] == 3:
        return csr_matrix((matrix[row, col], (row, indices[col])), shape=(3, ndof))
    return csr_matrix((matrix[row, col], (indices[row], indices[col])), shape=(ndof, ndof))


class FiniteMechanicsAdapter:
    """Read existing assembly data without mutating or duplicating its laws.

    Panels are handled by their separate finite adapter. ``response`` includes
    only timber, fittings and physical shaft elasticity. ``port``/``director``
    return exact interpolation positions/vectors and full local-support jets.
    H is a central derivative of analytic J; no whole assembly differencing is
    used. No gauge is supplied: ``finite_shaft_twist_gauge_qualified`` is false.
    """

    finite_shaft_twist_gauge_qualified = False

    def __init__(self, assembly, common_system=None, *, derivative_step_mm=1e-3, source_sha256=None):
        if not np.isfinite(derivative_step_mm) or derivative_step_mm <= 0:
            raise ValueError("positive finite derivative step required")
        self.old_ndof, self.ndof = assembly.ndof, assembly.ndof
        self.source_sha256 = source_pins(source_sha256)
        self.step = derivative_step_mm
        self.members, self.fittings, self.shafts = {}, {}, {}
        self.beams = []
        for name, member in assembly.members.items():
            basis = np.array([member["source"][key] for key in ("axis", "section_u", "section_v")]).T
            self.members[name] = {**member, "storage_basis": np.eye(3)}
            for element in member["elements"]:
                beam = checked_beam([element["start"], element["end"]], basis, element["local_K"], self.step)
                self.beams.append(IndexedBeam(np.asarray(element["dofs"]), beam, np.eye(3)))
        for name, fitting in assembly.fittings.items():
            points = np.array([fitting["points"][key] for key in ("beam", "post")])
            source_points = np.array([row["point_xyz_mm"] for row in fitting["source"]["ports"]])
            if np.max(abs(points - source_points)) > 1e-7:
                raise ValueError("fitting frozen stiffness ports and installed ports differ")
            model = ObjectiveCondensedFitting(points, np.asarray(fitting["source"]["global_port_stiffness_n_mm_rad"]), self.step)
            self.fittings[name] = {**fitting, "model": model}
        if common_system is not None:
            for name, row in common_system.shafts.items():
                index = np.array(row["index"], copy=True)
                if np.count_nonzero(index < 0) != 1 or index[0, 3] != -1:
                    raise ValueError("expected exactly one omitted first shaft twist")
                index[0, 3] = self.ndof
                self.ndof += 1
                basis = check_rotation(np.asarray(row["basis"]).T)
                self.shafts[name] = {**row, "index": index, "storage_basis": basis,
                                     "appended_first_twist_dof": int(index[0, 3])}
                for i, element in enumerate(row["elements"]):
                    centers = np.asarray(row["point"])[None, :] + row["stations"][i:i+2, None] * basis[:, 0]
                    beam = checked_beam(centers, basis, element["local_K"], self.step)
                    self.beams.append(IndexedBeam(index[i:i+2].ravel(), beam, basis))

    def state(self, q):
        return vector(q, self.ndof)

    def prolong_state(self, q):
        """Append zeros as an initial guess; not a finite gauge representative."""
        return np.r_[vector(q, self.old_ndof), np.zeros(self.ndof - self.old_ndof)]

    def response(self, q, tangent=True):
        q = self.state(q)
        energy, gradient = 0., np.zeros(self.ndof)
        rows, cols, values = [], [], []
        blocks = [(element.dofs, element.response(q, tangent)) for element in self.beams]
        blocks.extend((fitting["index"].ravel(), fitting["model"].response(q[fitting["index"].ravel()], tangent))
                      for fitting in self.fittings.values())
        for index, block in blocks:
            energy += block["energy_nmm"]
            np.add.at(gradient, index, block["gradient_n"])
            if tangent:
                i, j = np.nonzero(block["hessian_n_per_mm"])
                rows.extend(index[i]); cols.extend(index[j]); values.extend(block["hessian_n_per_mm"][i, j])
        return {"energy_nmm": float(energy), "gradient_n": gradient,
                "hessian_csr": coo_matrix((values, (rows, cols)), shape=(self.ndof, self.ndof)).tocsr() if tangent else None,
                "finite_shaft_twist_gauge_qualified": False,
                "physical_or_numerical_twist_constraints_added": 0}

    def _segment(self, body, point):
        row = self.members.get(body, self.shafts.get(body))
        if row is None:
            raise ValueError("mechanical body is missing: " + body)
        start = np.asarray(row["start"] if body in self.members else row["point"])
        axis = np.asarray(row["axis"] if body in self.members else row["basis"][0])
        station = float((point - start) @ axis)
        i = int(np.clip(np.searchsorted(row["stations"], station) - 1, 0, len(row["stations"]) - 2))
        a, b = row["stations"][i:i+2]
        t = float(np.clip((station - a) / (b - a), 0., 1.))
        return row["index"][i:i+2].ravel(), start + np.array([a, b])[:, None] * axis, t, row["storage_basis"]

    def _jet(self, index, q, evaluator, tangent):
        selected = q[index]
        value, jacobian = evaluator(selected)
        hessian = derivative_hessian(lambda state: evaluator(state)[1], selected, self.step) if tangent else None
        return {"position_xyz_mm": value, "J_csr": sparse_local(jacobian, index, self.ndof),
                "H_xyz_csr": [sparse_local(row, index, self.ndof) for row in hessian] if tangent else None,
                "support_indices": index.copy(), "local_J": jacobian, "local_H_xyz": hessian}

    def port(self, body, point, q, flange=None, tangent=True):
        q, point = self.state(q), vector(point, 3)
        if body == "floor":
            return {"position_xyz_mm": point, "J_csr": csr_matrix((3, self.ndof)),
                    "H_xyz_csr": [csr_matrix((self.ndof, self.ndof)) for _ in range(3)] if tangent else None,
                    "support_indices": np.array([], dtype=int), "local_J": np.zeros((3, 0)),
                    "local_H_xyz": np.zeros((3, 0, 0)) if tangent else None}
        if body in self.fittings:
            row = self.fittings[body]
            if flange is None:
                first = self.port(body, point, q, "beam", tangent)
                second = self.port(body, point, q, "post", tangent)
                index = np.r_[first["support_indices"], second["support_indices"]]
                jacobian = .5 * np.hstack((first["local_J"], second["local_J"]))
                hessian = np.zeros((3, 12, 12)) if tangent else None
                if tangent:
                    hessian[:, :6, :6], hessian[:, 6:, 6:] = .5*first["local_H_xyz"], .5*second["local_H_xyz"]
                return {"position_xyz_mm": .5*(first["position_xyz_mm"] + second["position_xyz_mm"]),
                        "J_csr": sparse_local(jacobian, index, self.ndof),
                        "H_xyz_csr": [sparse_local(row, index, self.ndof) for row in hessian] if tangent else None,
                        "support_indices": index, "local_J": jacobian, "local_H_xyz": hessian}
            if flange not in ("beam", "post"):
                raise ValueError("beam or post flange required")
            i = 0 if flange == "beam" else 1
            return self._jet(row["index"][i], q, lambda value: rigid_port(point, row["points"][flange], value), tangent)
        index, centers, t, basis = self._segment(body, point)
        return self._jet(index, q, lambda value: interpolated_point(point, centers, value, t, basis), tangent)

    def director(self, body, point, q, reference_vector, flange=None, tangent=True):
        """Rotate a material vector with full jets; unit input stays unit.

        The reference vector is a polar material direction chosen by the
        caller, not an automatically inferred cross-product/normal sign.
        Fitting directions need their specific flange; an averaged flange
        vector would not be a rigid material director.
        """
        q, point, direction = self.state(q), vector(point, 3), vector(reference_vector, 3)
        if body == "floor":
            result = self.port(body, point, q, tangent=tangent)
            result["position_xyz_mm"] = direction
        elif body in self.fittings:
            if flange not in ("beam", "post"):
                raise ValueError("specific fitting flange required for a material director")
            row, i = self.fittings[body], 0 if flange == "beam" else 1

            def evaluator(value):
                theta = value[3:] / ROTATION_SCALE
                current = so3_exp(theta) @ direction
                jacobian = np.zeros((3, 6))
                jacobian[:, 3:] = -skew(current) @ so3_left_jacobian(theta) / ROTATION_SCALE
                return current, jacobian

            result = self._jet(row["index"][i], q, evaluator, tangent)
        else:
            index, _, t, basis = self._segment(body, point)
            result = self._jet(index, q, lambda value: interpolated_director(direction, value, t, basis), tangent)
        result["current_vector_xyz"] = result.pop("position_xyz_mm")
        return result


def circular_material_roll_coupon():
    """Distinct failed gauge question on a bent TWO-element circular beam.

    This checks common RIGHT material roll, not a superposed WORLD rotation.
    The latter remains objective. The saved nonzero work means no material-roll
    nullspace or torque-free finite gauge may be inferred from this primitive.
    """
    positions = np.array([[0., 0., 0.], [50., 0., 0.], [100., 0., 0.]])
    beams = [CorotationalBeam.from_properties(positions[i:i+2], np.eye(3), 50., 400., 400., 800., 200000., 76923., .9)
             for i in range(2)]
    q = np.zeros((3, 6))
    q[:, :3] = [[0., 0., 0.], [-1., 3., 2.], [-4., 12., 7.]]
    q[:, 3:] = [[30., 150., 100.], [80., 200., 280.], [100., 250., 400.]]
    initial = sum(beam.energy(q[i:i+2].ravel()) for i, beam in enumerate(beams))
    residual = np.zeros_like(q)
    for i, beam in enumerate(beams):
        residual[i:i+2] += beam.residual(q[i:i+2].ravel()).reshape(2, 6)
    generator = np.zeros_like(q)
    for i, theta in enumerate(q[:, 3:]/ROTATION_SCALE):
        generator[i, 3:] = ROTATION_SCALE * so3_left_jacobian_inverse(theta) @ so3_exp(theta)[:, 0]
    rows = []
    for angle in (20., 70.):
        rolled = q.copy()
        for i in range(3):
            rolled[i, 3:] = ROTATION_SCALE * so3_log(so3_exp(q[i, 3:]/ROTATION_SCALE) @ so3_exp([np.deg2rad(angle), 0., 0.]))
        changed = sum(beam.energy(rolled[i:i+2].ravel()) for i, beam in enumerate(beams))
        rows.append({"material_roll_deg": angle, "energy_nmm": changed,
                     "relative_energy_change": (changed - initial)/initial})
    return {"initial_energy_nmm": initial, "common_material_roll_virtual_work_nmm_per_rad": float(np.sum(residual*generator)),
            "finite_material_roll_gauge_established": False, "constraints_added": 0, "rolls": rows}


def chord_refinement_coupon():
    """Exact circular centerline against straight corotational segments.

    Local curvature is constant and the physical arc has zero axial strain.
    The proxy measures chord shortening. Its spurious axial energy should
    decrease approximately as segment length**4 under refinement. This is a
    known geometry approximation, not a candidate-specific convergence gate.
    """
    length, radius, area, inertia, elastic, shear = 120., 1000., 50., 400., 200000., 76923.
    results = []
    for count in (1, 2, 4):
        stations = np.linspace(0., length, count + 1)
        current = np.c_[radius*np.sin(stations/radius), radius*(1 - np.cos(stations/radius)), np.zeros(count+1)]
        reference = np.c_[stations, np.zeros((count+1, 2))]
        q = np.zeros((count+1, 6)); q[:, :3] = current - reference
        q[:, 5] = ROTATION_SCALE * stations/radius
        energy, axial = 0., 0.
        for i in range(count):
            beam = CorotationalBeam.from_properties(reference[i:i+2], np.eye(3), area, inertia, inertia, 2*inertia, elastic, shear, .9)
            d = beam.deformation(q[i:i+2].ravel())[0]
            energy += beam.energy(q[i:i+2].ravel())
            axial += .5*elastic*area/(length/count)*d[6]**2
        expected_chord = 2*radius*np.sin(length/count/(2*radius))
        expected_axial = count*.5*elastic*area/(length/count)*(expected_chord - length/count)**2
        results.append({"elements": count, "segment_reference_length_mm": length/count,
                        "local_director_turn_rad": length/count/radius,
                        "total_energy_nmm": float(energy), "spurious_axial_energy_nmm": float(axial),
                        "exact_chord_shortening_axial_energy_nmm": float(expected_axial),
                        "bending_energy_nmm": float(energy - axial)})
    return {"physical_zero_axial_strain_arc_length_mm": length, "radius_mm": radius,
            "expected_pure_bending_energy_nmm": .5*elastic*inertia*length/radius**2,
            "records": results, "candidate_refinement_established": False}
