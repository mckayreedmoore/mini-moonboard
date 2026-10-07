"""Declared finite circular-shaft energy with exact common material-roll symmetry.

This midpoint Reissner-style extension uses a condensed shear coefficient to
recover the existing closed-form Timoshenko matrix at reference. It is not an
exact large-curvature continuum element. Frozen timber/fitting methods remain
unchanged, and no candidate solve, geometry rebuild or physical clamp is added.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import block_diag
from scipy.sparse import coo_matrix, csr_matrix

from scripts import thin_bolted_finite_mechanics as mechanical
from scripts.thin_bolted_common_shaft import circular_properties
from scripts.thin_bolted_corotational_methods import (
    BRANCH_MARGIN,
    ROTATION_SCALE,
    check_rotation,
    skew,
    so3_exp,
    so3_left_jacobian,
    so3_left_jacobian_inverse,
    so3_log,
    vector,
)

FROZEN_ADAPTER_SHA = "8c2bf2f27538fc1d599db9ddee2efbbb6344687393781bd689de09a4998772a2"
GAUGE_ANTIPARALLEL_MARGIN = 1e-8
SOURCES = [
    {"url": "https://arxiv.org/pdf/1611.06436", "locator": "Meier et al. (2016), section2.2.1 equations6-8 and AppendixA.4",
     "use": "Material axial/shear and bending/torsion strain energy; objective relative-triad interpolation. The condensed midpoint finite extension here is a separately declared scenario."},
    {"url": "https://arxiv.org/pdf/1812.01537", "locator": "Sola et al., AppendixB SO(3) exp/log, adjoint and Jacobians",
     "use": "Finite rotation composition, conjugation and work-conjugate analytic strain derivatives."},
]


def source_pins(additional=None):
    if (additional or {}).get("scripts/thin_bolted_finite_mechanics.py", FROZEN_ADAPTER_SHA) != FROZEN_ADAPTER_SHA:
        raise ValueError("parent pins conflict with frozen finite mechanical adapter")
    return mechanical.source_pins({"scripts/thin_bolted_finite_mechanics.py": FROZEN_ADAPTER_SHA, **(additional or {})})


@dataclass(frozen=True)
class IsotropicShaftBeam:
    """Circular two-node beam; each node stores WORLD (u_mm,1000theta_rad).

    Material triads are Ri=Exp(theta_world_i)*B. The strain vector is
    (v_x-1,v_y,v_z,Omega_x/L,Omega_y/L,Omega_z/L), where
    Omega=Log(R0.T*R1), Rmid=R0*Exp(Omega/2), v=Rmid.T*(x1-x0)/L.
    The shear term is a condensed finite extension, not a literal continuum
    shear modulus. At reference its analytic Hessian recovers closed Timo K.
    """

    reference_positions: np.ndarray
    reference_basis: np.ndarray
    diameter_mm: float
    elastic_modulus_mpa: float
    shear_modulus_mpa: float
    shear_factor: float = .9
    tangent_step_mm: float = 1e-3

    def __post_init__(self):
        positions = np.asarray(self.reference_positions, dtype=float)
        basis = check_rotation(self.reference_basis)
        if positions.shape != (2, 3) or not np.isfinite(positions).all():
            raise ValueError("two finite reference shaft positions required")
        chord = positions[1] - positions[0]
        length = np.linalg.norm(chord)
        if length <= 1e-8 or np.linalg.norm(chord/length - basis[:, 0]) > 1e-8:
            raise ValueError("positive shaft length and matching proper basis required")
        properties = [self.diameter_mm, self.elastic_modulus_mpa, self.shear_modulus_mpa,
                      self.shear_factor, self.tangent_step_mm]
        if not np.isfinite(properties).all() or min(properties) <= 0:
            raise ValueError("positive finite circular shaft properties required")
        object.__setattr__(self, "reference_positions", positions.copy())
        object.__setattr__(self, "reference_basis", basis.copy())

    @property
    def length_mm(self):
        return float(np.linalg.norm(self.reference_positions[1] - self.reference_positions[0]))

    @property
    def section_diagonal(self):
        area, inertia, torsion = circular_properties(self.diameter_mm)
        e, g, length = self.elastic_modulus_mpa, self.shear_modulus_mpa, self.length_mm
        condensed_shear = 12*e*inertia/(length**2*(1 + 12*e*inertia/(self.shear_factor*g*area*length**2)))
        return np.array([e*area, condensed_shear, condensed_shear, g*torsion, e*inertia, e*inertia])

    def measures(self, q):
        state = vector(q, 12).reshape(2, 6)
        theta = state[:, 3:]/ROTATION_SCALE
        triads = [so3_exp(t) @ self.reference_basis for t in theta]
        omega = so3_log(triads[0].T @ triads[1])
        if np.linalg.norm(omega) >= np.pi/2 - BRANCH_MARGIN:
            raise ValueError("90-degree local shaft turn is unsupported; refine/assess the finite extension")
        chord = self.reference_positions[1] - self.reference_positions[0] + state[1, :3] - state[0, :3]
        if np.linalg.norm(chord) <= 1e-8:
            raise ValueError("collapsed shaft chord is unsupported")
        length = self.length_mm
        midpoint = triads[0] @ so3_exp(.5*omega)
        v = midpoint.T @ chord/length
        strain = np.r_[v - [1., 0., 0.], omega/length]
        nodal_angular = [so3_left_jacobian(t)/ROTATION_SCALE for t in theta]
        domega = np.zeros((3, 12))
        inverse = so3_left_jacobian_inverse(omega) @ triads[0].T
        domega[:, 3:6], domega[:, 9:12] = -inverse @ nodal_angular[0], inverse @ nodal_angular[1]
        midpoint_angular = triads[0] @ so3_left_jacobian(.5*omega) @ (.5*domega)
        midpoint_angular[:, 3:6] += nodal_angular[0]
        dchord = np.zeros((3, 12)); dchord[:, :3], dchord[:, 6:9] = -np.eye(3), np.eye(3)
        dv = midpoint.T @ (dchord + skew(chord) @ midpoint_angular)/length
        jacobian = np.vstack((dv, domega/length))
        return strain, jacobian, {"material_relative_rotation_rad": omega,
                                  "local_director_turn_rad": float(np.linalg.norm(omega)),
                                  "midpoint_material_triad_world": midpoint,
                                  "chord_projection_per_reference_length": v,
                                  "current_chord_length_mm": float(np.linalg.norm(chord))}

    def energy(self, q):
        strain = self.measures(q)[0]
        return float(.5*self.length_mm*strain @ (self.section_diagonal*strain))

    def residual(self, q):
        strain, jacobian, _ = self.measures(q)
        return self.length_mm*jacobian.T @ (self.section_diagonal*strain)

    def reference_tangent(self):
        jacobian = self.measures(np.zeros(12))[1]
        return self.length_mm*jacobian.T @ (self.section_diagonal[:, None]*jacobian)

    def tangent(self, q, step_mm=None):
        q = vector(q, 12)
        step = self.tangent_step_mm if step_mm is None else float(step_mm)
        if not np.isfinite(step) or step <= 0:
            raise ValueError("positive finite shaft tangent difference step required")
        return np.column_stack([(self.residual(q + h) - self.residual(q - h))/(2*step)
                                for h in np.eye(12)*step])

    def response(self, q, tangent=True):
        strain, jacobian, metadata = self.measures(q)
        result = {"energy_nmm": float(.5*self.length_mm*strain @ (self.section_diagonal*strain)),
                  "gradient_n": self.length_mm*jacobian.T @ (self.section_diagonal*strain),
                  "strain": strain, **metadata}
        if tangent:
            result["hessian_n_per_mm"] = self.tangent(q)
        return result


def common_roll_local(nodes, angle_rad):
    """Ri -> Ri*Qx for a complete shaft in its fixed local storage basis."""
    nodes = np.asarray(nodes, dtype=float)
    if nodes.ndim != 2 or nodes.shape[1] != 6 or not np.isfinite(nodes).all() or not np.isfinite(angle_rad):
        raise ValueError("finite local shaft node states and roll angle required")
    result = nodes.copy()
    roll = so3_exp([angle_rad, 0., 0.])
    for i, state in enumerate(nodes):
        result[i, 3:] = ROTATION_SCALE*so3_log(so3_exp(state[3:]/ROTATION_SCALE) @ roll)
    return result


def minimal_director_gauge_local(nodes):
    """Choose first local theta_x=0 without changing any axial director.

    The shortest rotation taking e1 to the first material axial director has
    an axis perpendicular to e1. The remaining first-node orientation differs
    only by a RIGHT roll about e1; that same roll is removed at every node.
    This is a coordinate representative of the verified circular symmetry,
    not a torque support. The antiparallel director/chart is unsupported.
    """
    nodes = np.asarray(nodes, dtype=float)
    if nodes.ndim != 2 or nodes.shape[1] != 6 or len(nodes) < 2 or not np.isfinite(nodes).all():
        raise ValueError("at least two finite local shaft node states required")
    first = so3_exp(nodes[0, 3:]/ROTATION_SCALE)
    director = first[:, 0]
    if director[0] <= -1 + GAUGE_ANTIPARALLEL_MARGIN:
        raise ValueError("minimal director gauge near antiparallel is unsupported")
    cross = np.cross([1., 0., 0.], director)
    sine = np.linalg.norm(cross)
    theta = np.zeros(3) if sine < 1e-14 else cross/sine*np.arctan2(sine, director[0])
    swing = so3_exp(theta)
    twist = swing.T @ first
    if np.linalg.norm(twist[:, 0] - [1., 0., 0.]) > 1e-9:
        raise ValueError("minimal director gauge twist decomposition failed")
    roll_angle = float(np.arctan2(twist[2, 1], twist[1, 1]))
    gauged = common_roll_local(nodes, -roll_angle)
    if abs(gauged[0, 3]) > 1e-8:
        raise ValueError("minimal director gauge failed first local theta_x=0")
    return gauged, {"removed_common_right_roll_rad": roll_angle,
                    "first_local_scaled_theta_x_after_gauge": float(gauged[0, 3]),
                    "first_axial_director_local": director}


class IsotropicShaftAdapter:
    """Only the seventy shaft elasticities, over the unchanged full global state.

    ``replacement_response`` explicitly includes frozen timber/fitting methods
    once and the new shaft energy once. ``response`` is shaft-only. Port and
    director implementations are reused byte-for-byte from the frozen adapter.
    Gauge invariance applies to on-axis points/axial directors and the declared
    circular elastic law; real off-axis sources must be assessed separately.
    """

    def __init__(self, mechanics, common_system, *, derivative_step_mm=1e-3, source_sha256=None):
        self.mechanics, self.ndof = mechanics, mechanics.ndof
        self.source_sha256 = source_pins(source_sha256)
        self.parameters = dict(common_system.parameters)
        e = self.parameters["shaft_steel_E_mpa"]
        g = e/(2*(1 + self.parameters["shaft_steel_nu"]))
        diameter_scale = self.parameters["shaft_diameter_scale"]
        shear = self.parameters["circular_shear_factor_scenario"]
        self.elements = []
        self.reference_matrix_relative_errors = []
        for body, row in mechanics.shafts.items():
            if body not in common_system.shafts:
                raise ValueError("new shaft adapter body differs from original common system")
            basis = row["storage_basis"]
            transform = block_diag(*([basis] * 4))
            for i, old_element in enumerate(row["elements"]):
                positions = np.asarray(row["point"])[None, :] + row["stations"][i:i+2, None]*basis[:, 0]
                beam = IsotropicShaftBeam(positions, basis, row["diameter_mm"]*diameter_scale, e, g, shear, derivative_step_mm)
                old_transform = block_diag(basis.T, basis.T/ROTATION_SCALE, basis.T, basis.T/ROTATION_SCALE)
                expected = old_transform.T @ old_element["local_K"] @ old_transform
                error = np.linalg.norm(beam.reference_tangent() - expected)/np.linalg.norm(expected)
                if error > 1e-9:
                    raise ValueError("new finite shaft law differs from frozen reference matrix/properties")
                self.reference_matrix_relative_errors.append(float(error))
                self.elements.append({"body": body, "dofs": row["index"][i:i+2].ravel(), "beam": beam, "world_transform": transform})
        timber_indices = {int(index) for row in mechanics.members.values() for index in row["index"].ravel()}
        shaft_indices = {int(index) for row in mechanics.shafts.values() for index in row["index"].ravel()}
        self.timber_elements = []
        for element in mechanics.beams:
            if all(int(index) in timber_indices for index in element.dofs):
                self.timber_elements.append(element)
            elif not all(int(index) in shaft_indices for index in element.dofs):
                raise ValueError("mechanical beam is neither timber nor shaft; replacement would omit a law")

    def state(self, q):
        return vector(q, self.ndof)

    def response(self, q, tangent=True):
        q = self.state(q)
        energy, gradient = 0., np.zeros(self.ndof)
        rows, columns, values = [], [], []
        for element in self.elements:
            index, transform = element["dofs"], element["world_transform"]
            result = element["beam"].response(transform @ q[index], tangent)
            energy += result["energy_nmm"]
            np.add.at(gradient, index, transform.T @ result["gradient_n"])
            if tangent:
                block = transform.T @ result["hessian_n_per_mm"] @ transform
                i, j = np.nonzero(block)
                rows.extend(index[i]); columns.extend(index[j]); values.extend(block[i, j])
        return {"energy_nmm": float(energy), "gradient_n": gradient,
                "hessian_csr": coo_matrix((values, (rows, columns)), shape=(self.ndof, self.ndof)).tocsr() if tangent else None,
                "scope": "shaft elasticity only", "physical_twist_constraints_added": 0}

    def replacement_response(self, q, tangent=True):
        """Frozen timber/fitting response plus new shafts; no double count."""
        q = self.state(q)
        result = self.response(q, tangent)
        blocks = [(element.dofs, element.response(q, tangent)) for element in self.timber_elements]
        blocks.extend((fitting["index"].ravel(), fitting["model"].response(q[fitting["index"].ravel()], tangent))
                      for fitting in self.mechanics.fittings.values())
        for index, block in blocks:
            result["energy_nmm"] += block["energy_nmm"]
            np.add.at(result["gradient_n"], index, block["gradient_n"])
            if tangent:
                result["hessian_csr"] += mechanical.sparse_local(block["hessian_n_per_mm"], index, self.ndof)
        result["scope"] = "frozen timber/fittings once plus new circular shaft energy once; panels separate"
        return result

    def common_roll(self, q, angle_rad):
        q = self.state(q).copy()
        for body, row in self.mechanics.shafts.items():
            angle = angle_rad[body] if isinstance(angle_rad, dict) else angle_rad
            q[row["index"]] = common_roll_local(q[row["index"]], angle)
        return q

    def minimal_director_gauge(self, q):
        q = self.state(q).copy()
        metadata = {}
        for body, row in self.mechanics.shafts.items():
            gauged, metadata[body] = minimal_director_gauge_local(q[row["index"]])
            q[row["index"]] = gauged
        return q, metadata

    def material_roll_generators(self, q):
        """One complete shaft mode per body; physical axis is Ri*B[:,0]."""
        q = self.state(q)
        generators = {}
        for body, row in self.mechanics.shafts.items():
            mode = np.zeros(self.ndof)
            basis = row["storage_basis"]
            for index in row["index"]:
                theta = basis @ q[index[3:]]/ROTATION_SCALE
                axial = so3_exp(theta) @ basis[:, 0]
                mode[index[3:]] = ROTATION_SCALE*basis.T @ so3_left_jacobian_inverse(theta) @ axial
            generators[body] = mode
        return generators

    def quotient_world_rigid_generators(self, q, reference_point_xyz_mm=None):
        """World rigid generators with the compensating common material roll.

        Only for an already minimal-gauged representative. A world rotation
        changes its first local theta_x unless the same RIGHT roll correction
        is applied at every shaft node. These generators preserve the chart
        and world point/axial-director work. Full duals still supply physical
        nodal moments; this method does not discard or manufacture a dual.
        """
        q = self.state(q)
        reference = np.zeros(3) if reference_point_xyz_mm is None else vector(reference_point_xyz_mm, 3)
        rolls = self.material_roll_generators(q)
        result = {}
        for body, row in self.mechanics.shafts.items():
            missing = row["appended_first_twist_dof"]
            if abs(q[missing]) > 1e-8:
                raise ValueError("quotient rigid generator requires minimal first local theta_x=0")
            basis, full = row["storage_basis"], np.zeros((self.ndof, 6))
            for index, station in zip(row["index"], row["stations"], strict=True):
                theta = basis @ q[index[3:]]/ROTATION_SCALE
                center = row["point"] + station*basis[:, 0] + basis @ q[index[:3]]
                full[index[:3]] = np.c_[basis.T, -basis.T @ skew(center - reference)]
                full[index[3:], 3:] = ROTATION_SCALE*basis.T @ so3_left_jacobian_inverse(theta)
            mode = rolls[body]
            if abs(mode[missing]) < 1e-6:
                raise ValueError("minimal director quotient generator is singular")
            correction = -full[missing]/mode[missing]
            quotient = full + mode[:, None]*correction[None, :]
            result[body] = {"full_world_rigid_G_csr": csr_matrix(full), "quotient_world_rigid_G_csr": csr_matrix(quotient),
                            "compensating_common_right_roll_per_world_rigid_component": correction,
                            "first_local_theta_x_increment_after_correction": quotient[missing].copy()}
        return result

    def port(self, body, point, q, flange=None, tangent=True):
        if body not in self.mechanics.shafts:
            raise ValueError("isotropic shaft port requires a shaft body")
        return self.mechanics.port(body, point, q, flange, tangent)

    def director(self, body, point, q, reference_vector, flange=None, tangent=True):
        if body not in self.mechanics.shafts:
            raise ValueError("isotropic shaft director requires a shaft body")
        return self.mechanics.director(body, point, q, reference_vector, flange, tangent)


def source_axis_gauge_audit():
    """Synthetic finite poses on all original350metal centroids; no projection.

    Pure frozen JSON sources only. This does not build a candidate assembly or
    evaluate its state. Pressure/bearing point formulas are exactly on-axis;
    the actual CAD centroids retain their small source precision offsets.
    """
    from scripts import thin_bolted_common_shaft as common

    rows = common.read_inputs()
    pins = common.source_pins()
    reference_normals = []
    point_errors, radial_offsets, gravity_work = [], [], []
    original = np.array([[.2, -.1, .3, 350., 200., -150.], [-.3, .2, -.1, 500., 100., 100.]])
    gauged, gauge = minimal_director_gauge_local(original)
    for row in rows:
        basis, p = row["basis"].T, np.asarray(row["point"])
        g = basis[:, 0]
        endpoints = p[None, :] + np.array(row["shaft_interval_mm"])[:, None]*g
        length = row["shaft_interval_mm"][1] - row["shaft_interval_mm"][0]
        for role in row["metal_roles"]:
            point = np.array(role["center_of_mass_xyz_mm"])
            arm = point - p
            radial_offsets.append(float(np.linalg.norm(arm - g*(g @ arm))))
            t = float(np.clip(((point - endpoints[0]) @ g)/length, 0., 1.))
            before = mechanical.interpolated_point(point, endpoints, original.ravel(), t, basis)[0]
            after = mechanical.interpolated_point(point, endpoints, gauged.ravel(), t, basis)[0]
            difference = after - before
            point_errors.append(float(np.linalg.norm(difference)))
            mass = role["volume_mm3"]*7850e-9
            gravity_work.append(float(np.array([0., 0., -9.80665*mass]) @ difference))
        for t in (0., .37, 1.):
            before = mechanical.interpolated_director(g, original.ravel(), t, basis)[0]
            after = mechanical.interpolated_director(g, gauged.ravel(), t, basis)[0]
            reference_normals.append(float(np.linalg.norm(after - before)))
    return {"source_sha256": pins, "physical_shafts": len(rows), "original_metal_load_centroids": len(point_errors),
            "centroids_projected_to_axis": 0, "maximum_original_centroid_radial_offset_mm": max(radial_offsets),
            "maximum_unprojected_centroid_gauge_position_change_mm": max(point_errors),
            "maximum_axial_director_gauge_change": max(reference_normals),
            "sum_gravity_work_change_nmm": float(sum(gravity_work)),
            "sum_absolute_gravity_work_change_nmm": float(sum(abs(value) for value in gravity_work)),
            "synthetic_local_node_states": original.tolist(), "minimal_gauge": gauge,
            "candidate_state_evaluated": False}


def chord_refinement_coupon():
    length, radius, diameter, e, g = 120., 1000., 8., 200000., 76923.
    area, inertia, _ = circular_properties(diameter)
    records = []
    for count in (1, 2, 4):
        stations = np.linspace(0., length, count + 1)
        reference = np.c_[stations, np.zeros((count+1, 2))]
        current = np.c_[radius*np.sin(stations/radius), radius*(1 - np.cos(stations/radius)), np.zeros(count+1)]
        q = np.zeros((count+1, 6)); q[:, :3] = current - reference; q[:, 5] = ROTATION_SCALE*stations/radius
        energy, axial, shear = 0., 0., 0.
        for i in range(count):
            beam = IsotropicShaftBeam(reference[i:i+2], np.eye(3), diameter, e, g)
            result = beam.response(q[i:i+2].ravel(), False)
            energy += result["energy_nmm"]
            axial += .5*beam.length_mm*e*area*result["strain"][0]**2
            shear += .5*beam.length_mm*beam.section_diagonal[1]*np.sum(result["strain"][1:3]**2)
        records.append({"elements": count, "local_director_turn_rad": length/count/radius,
                        "energy_nmm": float(energy), "spurious_chord_axial_energy_nmm": float(axial),
                        "shear_energy_nmm": float(shear), "bending_energy_nmm": float(energy - axial - shear)})
    return {"radius_mm": radius, "arc_length_mm": length, "expected_bending_energy_nmm": .5*e*inertia*length/radius**2,
            "records": records, "candidate_local_curvature_refinement_established": False}
