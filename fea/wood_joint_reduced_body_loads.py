"""Consistent C3D20 self-weight with exact source mass and first moment.

Uniform gravity over each modeled body is scaled to its source mass. A separate
zero-resultant nodal couple reconciles omitted-hole/cut centroid differences;
that correction is recorded rather than presented as exact local mass geometry.
"""
from __future__ import annotations

from itertools import product

import numpy as np

from fea.floor_recess_mesh import shape20
from fea.horizontal_panel_frame import add_load, distribute_wrench, traction_wrench
from fea.wood_joint_reduced_members import _inverse_shape20, shape20_derivatives


def body_volume_weights(structure, body):
    if body in structure.members:
        groups = [body]
    elif body in structure.panels:
        groups = structure.panel_layer_groups[body]
    else:
        raise ValueError("Unknown physical body: " + body)
    abscissae, weights = np.polynomial.legendre.leggauss(3)
    quadrature = []
    for indices in product(range(3), repeat=3):
        natural = abscissae[list(indices)]
        quadrature.append((shape20(natural), shape20_derivatives(natural),
                           float(np.prod(weights[list(indices)]))))
    nodal = {}
    minimum_jacobian = float("inf")
    elements = set()
    for group in groups:
        for eid in structure.groups[group]:
            if eid in elements:
                raise ValueError("Repeated body element")
            elements.add(eid)
            kind, ids, _ = structure.elements[eid]
            if kind != "C3D20":
                raise ValueError("Body gravity requires native C3D20 solids")
            positions = np.array([structure.nodes[n] for n in ids])
            for shape, derivatives, weight in quadrature:
                determinant = float(np.linalg.det(positions.T @ derivatives))
                minimum_jacobian = min(minimum_jacobian, determinant)
                if not np.isfinite(determinant) or determinant <= 0:
                    raise ValueError(f"Invalid {body} element {eid} Jacobian")
                dv = determinant * weight
                for n, value in zip(ids, shape*dv, strict=True):
                    nodal[n] = nodal.get(n, 0.) + float(value)
    volume = sum(nodal.values())
    if volume <= 0 or not elements:
        raise ValueError("Empty body volume")
    centroid = sum((v*np.array(structure.nodes[n]) for n, v in nodal.items()), np.zeros(3))/volume
    return nodal, {"body": body, "element_count": len(elements), "mesh_volume_mm3": volume,
                   "mesh_centroid_xyz_mm": centroid.tolist(), "minimum_gauss_jacobian_mm3": minimum_jacobian}


def add_body_self_weight(structure, body, mass_kg, source_centroid_xyz_mm):
    if not np.isfinite(mass_kg) or mass_kg <= 0:
        raise ValueError("Positive source body mass required")
    nodal, audit = body_volume_weights(structure, body)
    ids = list(nodal)
    positions = np.array([structure.nodes[n] for n in ids])
    fractions = np.array([nodal[n] for n in ids])/audit["mesh_volume_mm3"]
    source_centroid = np.array(source_centroid_xyz_mm, dtype=float)
    if source_centroid.shape != (3,) or not np.isfinite(source_centroid).all():
        raise ValueError("Source centroid must be a finite triplet")
    force = np.array([0., 0., -9.80665*mass_kg])
    values = traction_wrench(positions, fractions, force, [0., 0., 0.], source_centroid)
    correction = values-fractions[:, None]*force
    for node, load in zip(ids, values, strict=True):
        add_load(structure, node, load)
    force_residual = np.sum(values, axis=0)-force
    moment_residual = np.sum(np.cross(positions-source_centroid, values), axis=0)
    if max(abs(force_residual)) > 1e-7 or max(abs(moment_residual)) > 1e-6:
        raise ValueError("Body self-weight lost source resultant")
    return {**audit, "source_mass_kg": mass_kg, "source_centroid_xyz_mm": source_centroid.tolist(),
        "force_residual_xyz_n": force_residual.tolist(), "moment_residual_xyz_nmm": moment_residual.tolist(),
        "centroid_correction_total_absolute_nodal_force_n": float(np.linalg.norm(correction, axis=1).sum()),
        "loads": [{"node": n, "point_xyz_mm": structure.nodes[n], "force_xyz_n": f.tolist()}
                  for n, f in zip(ids, values, strict=True)],
        "limit": "Consistent uniform self-weight on reduced geometry plus exact source-first-moment correction; omitted local mass detail is not reproduced."}


def add_body_point_wrench(structure, body, point_xyz_mm, force_xyz_n, couple_xyz_nmm):
    """Apply a condensed hardware wrench through one containing solid element.

    The caller establishes the physical receiver and local application point.
    This does not select a nearest body or move an outside point into the mesh.
    Point force uses C3D20 interpolation; any couple uses the same element cloud.
    """
    point = np.asarray(point_xyz_mm, dtype=float)
    force = np.asarray(force_xyz_n, dtype=float)
    couple = np.asarray(couple_xyz_nmm, dtype=float)
    if any(v.shape != (3,) or not np.isfinite(v).all() for v in (point, force, couple)):
        raise ValueError("Point wrench requires finite triplets")
    groups = [body] if body in structure.members else structure.panel_layer_groups[body]
    for group in groups:
        for eid in structure.groups[group]:
            kind, ids, _ = structure.elements[eid]
            if kind != "C3D20":
                continue
            positions = np.array([structure.nodes[n] for n in ids])
            if np.any(point < positions.min(axis=0)-1e-6) or np.any(point > positions.max(axis=0)+1e-6):
                continue
            inverse = _inverse_shape20(point, positions)
            if inverse is None:
                continue
            nodal_force = inverse[1][:, None]*force
            remaining = couple-np.sum(np.cross(positions-point, nodal_force), axis=0)
            if np.linalg.norm(remaining) > 1e-12:
                nodal_force += distribute_wrench(positions, [0., 0., 0.], remaining, point)
            force_error = np.sum(nodal_force, axis=0)-force
            moment_error = np.sum(np.cross(positions-point, nodal_force), axis=0)-couple
            if max(abs(force_error)) > 1e-7 or max(abs(moment_error)) > 1e-6:
                raise ValueError("Local condensed wrench lost its resultant")
            for node, value in zip(ids, nodal_force, strict=True):
                add_load(structure, node, value)
            return {"body": body, "element": eid, "point_xyz_mm": point.tolist(),
                "force_xyz_n": force.tolist(), "couple_xyz_nmm": couple.tolist(),
                "force_residual_xyz_n": force_error.tolist(), "moment_residual_xyz_nmm": moment_error.tolist(),
                "nodal_forces": [{"node": n, "point_xyz_mm": structure.nodes[n], "force_xyz_n": f.tolist()}
                                 for n, f in zip(ids, nodal_force, strict=True)],
                "scope": "Local statically equivalent omitted-hardware load on one reduced solid element; no added constraint"}
    raise ValueError(f"{body}: hardware application point lies outside retained solid cells")


def self_check():
    from fea.horizontal_panel_frame import Structure

    structure = Structure()
    structure.member({"name": "bar", "start": [0., 0., 0.], "end": [0., 0., 1000.],
                      "section_u": [1., 0., 0.], "width_mm": 100., "depth_mm": 50.}, size=200.)
    result = add_body_self_weight(structure, "bar", 2.5, [1., -2., 499.])
    if abs(result["mesh_volume_mm3"]-5e6) > 1e-5 or np.linalg.norm(np.array(result["mesh_centroid_xyz_mm"])-[0, 0, 500]) > 1e-8:
        raise AssertionError("Known rectangular volume or first moment failed")
    add_body_point_wrench(structure, "bar", [12., -7., 387.], [1., 2., -3.], [7., -11., 13.])
    # A consistent load includes negative corner weights for quadratic solids;
    # do not replace it with unsigned/equal loads merely to remove that feature.
    return {"known_volume_passed": True, "source_wrench_passed": True,
            "native_solve_executed": False, "minimum_jacobian_mm3": result["minimum_gauss_jacobian_mm3"]}


if __name__ == "__main__":
    print(self_check())
