"""Reference-volume C3D10 momentum; units follow coordinates, time and density.

The consistent scalar mass blocks retain the quadratic interpolation products
needed for angular momentum and kinetic energy. They must not be row-lumped:
quadratic tetrahedron corner row sums can be negative.
The physical Gauss8 and source-reconstructed CalculiX 2.21 four-point operators
are distinct. Neither has yet been qualified against native solver ELKE output.
"""

import math


def calculix_221_quadrature():
    """Source literals from CalculiX 2.21 gauss.f:142 and :339 (not Gmsh's rule)."""
    a, b = .138196601125011, .585410196624968
    return [(a,a,a), (b,a,a), (a,b,a), (a,a,b)], [.041666666666667]*4


def _vectors(values, label):
    if not values or any(len(v) != 3 or not all(map(math.isfinite, v)) for v in values.values()):
        raise ValueError(f"Finite three-component {label} required")


def mass_block(basis, weights, determinants, density):
    """Integrate one scalar 10x10 mass block from quadrature data."""
    if not math.isfinite(density) or density <= 0:
        raise ValueError("Positive finite density required")
    if not weights or len(basis) != len(weights) or len(determinants) != len(weights):
        raise ValueError("Matching nonempty quadrature arrays required")
    if any(len(row) != 10 or not all(map(math.isfinite, row)) for row in basis):
        raise ValueError("Finite ten-component basis required")
    if not all(map(math.isfinite, weights)):
        raise ValueError("Finite quadrature weights required")
    if any(not math.isfinite(d) or d <= 0 for d in determinants):
        raise ValueError("Nonpositive or nonfinite integration Jacobian")
    factors = [density*w*d for w, d in zip(weights, determinants)]
    block = tuple(tuple(math.fsum(f*row[i]*row[j] for f, row in zip(factors, basis))
                        for j in range(10)) for i in range(10))
    if not all(math.isfinite(v) for row in block for v in row) or math.fsum(map(math.fsum, block)) <= 0:
        raise ValueError("Nonfinite or nonpositive integrated mass")
    return block


def consistent_mass(elements, nodes, density, integration_rule="Gauss8"):
    """Physical mass: {element: (node_ids, scalar_mass_block)}, Gmsh node order.

    Input connectivity is CalculiX/Abaqus C3D10. Gauss8 integrates N_i*N_j
    (degree four) times the quadratic geometry Jacobian determinant (degree
    three). The rule argument permits independent quadrature refinement checks.
    Reference Jacobians are checked at every integration point.
    This is not the CalculiX 2.21 four-point solver mass operator.
    """
    return _integrated_mass(elements, nodes, density, integration_rule)


def calculix_221_mass(elements, nodes, density):
    """Reconstruct the untransformed implicit C3D10 four-point reference mass.

    This source-based reconstruction is NOT yet solver-output qualified. It
    excludes mortar basis transformations, mass scaling and explicit lumping.
    Return format matches consistent_mass. See docs/dynamic-momentum-qualification.md.
    """
    return _integrated_mass(elements, nodes, density, None)


def _integrated_mass(elements, nodes, density, integration_rule):
    _vectors(nodes, "node coordinates")
    if not math.isfinite(density) or density <= 0:
        raise ValueError("Positive finite density required")
    if not elements or any(len(ids) != 10 or len(set(ids)) != 10 or
                           any(not isinstance(n, int) or isinstance(n, bool) or n not in nodes
                               for n in ids) for ids in elements.values()):
        raise ValueError("Complete ten-distinct-node C3D10 connectivity required")
    if any(not isinstance(tag, int) or isinstance(tag, bool) or tag <= 0 for tag in (*nodes, *elements)):
        raise ValueError("Positive integer node and element tags required")
    import gmsh

    if gmsh.isInitialized():
        raise ValueError("Momentum mesh integration requires its own Gmsh session")
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Verbosity", 1)
        gmsh.model.add("momentum_reference_mesh")
        entity = gmsh.model.addDiscreteEntity(3)
        gmsh.model.mesh.addNodes(3, entity, list(nodes), [v for xyz in nodes.values() for v in xyz])
        # CalculiX and Gmsh swap the last two midside nodes.
        gmsh.model.mesh.addElementsByType(entity, 11, list(elements),
                                        [ids[i] for ids in elements.values() for i in (0,1,2,3,4,5,6,7,9,8)])
        if integration_rule is None:
            coordinates, weights = calculix_221_quadrature()
            points = [v for xyz in coordinates for v in xyz]
        else:
            points, weights = gmsh.model.mesh.getIntegrationPoints(11, integration_rule)
        _, flat_basis, _ = gmsh.model.mesh.getBasisFunctions(11, points, "Lagrange")
        basis = [flat_basis[q*10:q*10+10] for q in range(len(weights))]
        tags, ids = gmsh.model.mesh.getElementsByType(11, entity)
        _, determinants, _ = gmsh.model.mesh.getJacobians(11, points, entity)
        count = len(weights)
        return {int(tag): (tuple(map(int, ids[e*10:e*10+10])),
                           mass_block(basis, list(weights), determinants[e*count:(e+1)*count], density))
                for e, tag in enumerate(tags)}
    finally:
        gmsh.finalize()


def momentum(nodes, blocks, displacements, velocities):
    """Compute mass, P, H about the origin, and KE from consistent mass blocks.

    H uses current position X+u and reference density/volume. Every participating
    node needs both U and V; extra nodes (e.g. a rigid floor) are ignored.
    Shared nodes contribute once per incident element, as required by assembly.
    """
    if not blocks:
        raise ValueError("Nonempty consistent mass blocks required")
    used = {n for ids, _ in blocks.values() for n in ids}
    if any(not used <= set(field) for field in (nodes, displacements, velocities)):
        raise ValueError("Incomplete coordinates, displacements or velocities")
    for field, label in ((nodes, "coordinates"), (displacements, "displacements"), (velocities, "velocities")):
        _vectors({n: field[n] for n in used}, label)
    positions = {n: tuple(x+u for x, u in zip(nodes[n], displacements[n])) for n in used}
    mass, kinetic = [], []
    linear, angular = [[], [], []], [[], [], []]
    for ids, block in blocks.values():
        if len(ids) != 10 or len(block) != 10 or any(len(row) != 10 or not all(map(math.isfinite, row)) for row in block):
            raise ValueError("Finite ten-by-ten consistent mass block required")
        mass.append(math.fsum(map(math.fsum, block)))
        for i, n in enumerate(ids):
            mv = tuple(math.fsum(block[i][j]*velocities[k][a] for j, k in enumerate(ids)) for a in range(3))
            x, v = positions[n], velocities[n]
            for a in range(3):
                linear[a].append(mv[a])
                angular[a].append(x[(a+1)%3]*mv[(a+2)%3]-x[(a+2)%3]*mv[(a+1)%3])
            kinetic.append(.5*math.fsum(v[a]*mv[a] for a in range(3)))
    result = {"mass": math.fsum(mass), "linear_momentum": tuple(map(math.fsum, linear)),
              "angular_momentum": tuple(map(math.fsum, angular)), "kinetic_energy": math.fsum(kinetic)}
    if not all(math.isfinite(v) for v in (result["mass"], result["kinetic_energy"],
                                          *result["linear_momentum"], *result["angular_momentum"])) or result["mass"] <= 0:
        raise ValueError("Nonfinite state integral or nonpositive mass")
    return result
