"""Explicit scalar axial/contact and two-component lateral reduced joints.

Lateral planes do not restrain axial translation. Outer-seat axial ties do
not restrain lateral translation. Properties and physical ownership are inputs;
this module supplies neither fastener capacities nor measured stiffnesses.
"""
from __future__ import annotations

import numpy as np

from fea.round_insert_frame import normal_contact


def _unit(value):
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,) or not np.isfinite(vector).all() or np.linalg.norm(vector) < 1e-12:
        raise ValueError("Require a finite nonzero direction")
    return vector / np.linalg.norm(vector)


def lateral_plane(structure, first, second, *, name, axis, stiffness_n_per_mm,
                  owner, radial_gap_mm=0.):
    """Independent coincident timber translations, two lateral SPRING2 DOFs."""
    if radial_gap_mm < 0 or not np.isfinite(radial_gap_mm):
        raise ValueError("Require a finite nonnegative radial gap")
    if np.linalg.norm(np.asarray(structure.nodes[first])-structure.nodes[second]) > 1e-7:
        raise ValueError("Lateral shear-plane attachments must be coincident")
    axis = _unit(axis)
    tangent = np.cross(axis, np.eye(3)[int(np.argmin(abs(axis)))])
    tangent /= np.linalg.norm(tangent)
    basis = np.array([axis, tangent, np.cross(axis, tangent)])
    auxiliary = [structure.node(structure.nodes[n]) for n in (first, second)]
    for node, source in zip(auxiliary, (first, second), strict=True):
        # The unused local axial auxiliary is zero, not tied to either timber.
        structure.equations.append([(node, 1, 1.)])
        for i in (1, 2):
            structure.equations.append([(node, i+1, 1.)] + [
                (source, j+1, -float(value)) for j, value in enumerate(basis[i])
                if abs(value) > 1e-13])
    start = len(structure.springs)
    structure.spring(*auxiliary, stiffness_n_per_mm, name, dofs=(2, 3), bearing=radial_gap_mm > 0)
    for spring in structure.springs[start:]:
        spring.update(connector_name=name, connector_local_dof=spring["dof"])
        if radial_gap_mm > 0:
            spring.update(radial_clearance_assumption=True, radial_clearance_mm=float(radial_gap_mm))
    structure.rotation_masters.update(auxiliary)
    owner.update(force_basis=basis.tolist(), axis=axis.tolist(),
                 point=list(structure.nodes[first]))
    return auxiliary


def axial_outer_seats(structure, first, second, *, name, axis, stiffness_n_per_mm, owner):
    """One tension-only tie along the common line of two outside washer seats."""
    axis = _unit(axis)
    first_point = np.asarray(structure.nodes[first])
    second_point = np.asarray(structure.nodes[second])
    span = second_point-first_point
    if float(span @ axis) <= 0 or np.linalg.norm(np.cross(span, axis)) > 1e-6:
        raise ValueError("Ordered washer seats must lie on the positive bolt-axis line")
    # Scalar auxiliary points are coincident; their source points need not be.
    # Collinearity makes relative axial displacement invariant to rigid rotation.
    nodes = normal_contact(structure, name, first, [second], [1.], first_point, axis,
                           stiffness_n_per_mm)
    structure.springs[-1]["tension_only_assumption"] = True
    owner.update(point=first_point.tolist(), first_point=first_point.tolist(),
                 second_point=second_point.tolist(), axis=axis.tolist(), scalar_normal=axis.tolist())
    return nodes


def compression_contact(structure, first, second, *, name, inward, stiffness_n_per_mm, owner):
    """One unilateral inward force resultant for a distributed contact area cell."""
    normal = _unit(inward)
    point = np.asarray(structure.nodes[first])
    if np.linalg.norm(point-structure.nodes[second]) > 1e-6:
        raise ValueError("Normal contact resultants must use one common physical point")
    nodes = normal_contact(structure, name, first, [second], [1.], point, normal,
                           stiffness_n_per_mm)
    owner.update(point=point.tolist(), scalar_normal=normal.tolist())
    return nodes


def self_check():
    """Verify omitted axial restraint and rigid motion at eccentric seat points."""
    from fea.horizontal_panel_frame import Structure

    structure = Structure()
    axis = _unit([1., 2., 3.])
    first_point = np.array([7., 11., 13.])
    first = structure.node(first_point)
    second = structure.node(first_point+83.*axis)
    owner = {"first": "head_receiver", "second": "nut_receiver"}
    auxiliary = axial_outer_seats(structure, first, second, name="axial", axis=axis,
                                 stiffness_n_per_mm=1000., owner=owner)
    translation = np.array([.3, -.5, .7])
    rotation = np.array([.001, -.003, .002])
    motion = {n: translation + np.cross(rotation, structure.nodes[n]) for n in (first, second)}
    projected = [float(motion[n] @ axis) for n in (first, second)]
    if abs(projected[1]-projected[0]) > 1e-12:
        raise AssertionError("Axial seat tie responds to rigid rotation")
    for n, u in zip(auxiliary, projected, strict=True):
        motion[n] = np.array([u, 0., 0.])
    if max(abs(sum(c*motion[n][d-1] for n, d, c in terms)) for terms in structure.equations) > 1e-12:
        raise AssertionError("Axial tie projection equations violate rigid motion")
    structure = Structure()
    first, second = structure.node(first_point), structure.node(first_point)
    owner = {"first": "one", "second": "two"}
    lateral_plane(structure, first, second, name="lateral", axis=axis, stiffness_n_per_mm=500., owner=owner)
    basis = np.array(owner["force_basis"])
    if np.linalg.norm(basis[1:] @ axis) > 1e-12 or len(structure.springs) != 2:
        raise AssertionError("Lateral-only plane incorrectly restrains axial slip")
    return {"rigid_motion_passed": True, "lateral_only_passed": True, "native_solve_executed": False}


if __name__ == "__main__":
    print(self_check())
