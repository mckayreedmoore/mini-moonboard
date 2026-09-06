"""Pure mesh topology checks, without importing Gmsh or launching a solver."""
import pytest

from fea.floor_contact import FACES
from fea.stitch_joint_mesh import (
    GMSH_TO_CCX,
    append_body,
    external_faces,
    surface_faces,
    validate_ownership,
)


def test_quadratic_exterior_maps_every_face_and_rejects_wrong_midside_nodes():
    elements = {17: tuple(range(1, 11))}
    exterior = external_faces(elements)
    triangles = [tuple(elements[17][i] for i in face) for face in FACES]
    assert surface_faces(triangles, exterior) == {
        "faces": [[17, i] for i in range(1, 5)], "nodes": list(range(1, 11))}
    triangle = triangles[0]
    with pytest.raises(ValueError, match="does not match"):
        surface_faces([(*triangle[:3], triangle[4], triangle[3], triangle[5])], exterior)
    with pytest.raises(ValueError, match="duplicate"):
        surface_faces([triangle, triangle], exterior)
    with pytest.raises(ValueError, match="exterior"):
        surface_faces([(1, 2, 11, 5, 12, 13)], exterior)


def test_gmsh_last_two_edge_conversion_and_nonmanifold_rejection():
    assert tuple(range(1, 11))[8:] == (9, 10)
    converted = tuple(tuple(range(1, 11))[i] for i in GMSH_TO_CCX)
    assert converted == (1, 2, 3, 4, 5, 6, 7, 8, 10, 9)
    with pytest.raises(ValueError, match="Nonmanifold"):
        external_faces({i: converted for i in (1, 2, 3)})
    with pytest.raises(ValueError, match="distinct"):
        external_faces({1: (1,) * 10})


def test_separate_body_ids_preserve_coincident_coordinates_and_reject_shared_ids():
    local_nodes = {i: (float(i), 0., 0.) for i in range(1, 11)}
    local_elements = {1: tuple(local_nodes)}
    nodes, elements, bodies = {}, {}, {}
    for name in ("inner", "outer"):
        ns, es = append_body(nodes, elements, local_nodes, local_elements)
        bodies[name] = {"nodes": list(ns.values()), "elements": list(es.values())}
    assert len(nodes) == 20 and nodes[1] == nodes[11]
    assert not set(bodies["inner"]["nodes"]) & set(bodies["outer"]["nodes"])
    validate_ownership(nodes, elements, bodies)
    with pytest.raises(ValueError, match="ownership"):
        validate_ownership(nodes, elements, {"inner": bodies["inner"], "outer": bodies["inner"]})
    with pytest.raises(ValueError, match="cover"):
        validate_ownership(nodes, elements, {"inner": bodies["inner"]})
    with pytest.raises(ValueError, match="ownership"):
        append_body({}, {}, {**local_nodes, 11: (0., 0., 0.)}, local_elements)
