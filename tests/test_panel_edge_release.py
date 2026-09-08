"""Small conforming straight C3D10 interface meshes; no CAD or solver."""
import copy

import pytest

from fea.panel_edge_release import cross, release


def fixture_mesh():
    nodes, elements, indexed = {}, {}, {}

    def node(p):
        p = tuple(p)
        if p not in indexed:
            indexed[p] = len(indexed)+1
            nodes[indexed[p]] = p
        return indexed[p]

    for corners in (
        [(0, 0, -1), (0, 1, 0), (0, 0, 0), (1, 0, 0)],
        [(0, 0, 1), (0, 0, 0), (0, 1, 0), (1, 0, 0)],
        [(0, 0, -1), (0, 1, 0), (0, 0, 0), (-1, 0, 0)],
        [(0, 0, 1), (0, 0, 0), (0, 1, 0), (-1, 0, 0)],
    ):
        vectors = [[p[i]-corners[0][i] for i in range(3)] for p in corners[1:]]
        if sum(a*b for a, b in zip(vectors[0], cross(vectors[1], vectors[2]), strict=True)) < 0:
            corners[1], corners[2] = corners[2], corners[1]
        midpoints = [tuple((corners[i][k]+corners[j][k])/2 for k in range(3))
                     for i, j in ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))]
        elements[len(elements)+1] = tuple(node(p) for p in corners+midpoints)
    return nodes, elements


def apply(nodes, elements, **kwargs):
    return release(nodes, elements, {"left": {1, 2}}, {"left": 0.}, (0., 0., 0.), (0., 0., 1.), **kwargs)


def test_exact_material_preservation_release_and_retained_rim():
    nodes, elements = fixture_mesh()
    before = copy.deepcopy((nodes, elements))
    new_nodes, new_elements, report = apply(nodes, elements)
    assert (nodes, elements) == before
    assert report["added_node_count"] == 3
    side = report["legs"]["left"]
    assert side["released_panel_face_count"] == side["retained_rim_face_count"] == 1
    assert side["released_panel_area_mm2"] == side["retained_rim_area_mm2"] == .5
    assert len(side["retained_common_edge_nodes"]) == 3
    assert all(nodes[n][2] < 0 for n in side["node_map"])
    assert sorted(side["node_map"].values()) == list(range(max(nodes)+1, max(nodes)+4))
    for e, ids in elements.items():
        assert tuple(new_nodes[n] for n in new_elements[e]) == tuple(nodes[n] for n in ids)
    assert new_elements[3] == elements[3] and new_elements[4] == elements[4]
    assert apply(nodes, elements) == (new_nodes, new_elements, report)


@pytest.mark.parametrize("protected", ["floor_nodes", "load_nodes"])
def test_protected_node_rejected(protected):
    nodes, elements = fixture_mesh()
    n = next(n for n, p in nodes.items() if p == (0, 0, -1))
    with pytest.raises(ValueError, match="protected"):
        apply(nodes, elements, **{protected: [n]})


def test_bad_connectivity_and_missing_rim_are_rejected():
    nodes, elements = fixture_mesh()
    broken = dict(elements)
    broken[1] = (elements[1][0],)*10
    with pytest.raises(ValueError, match="connectivity"):
        apply(nodes, broken)
    with pytest.raises(ValueError, match="interface"):
        release(nodes, elements, {"left": {1}}, {"left": 0}, (0, 0, 0), (0, 0, 1))
    with pytest.raises(ValueError, match="geometry"):
        apply(nodes, elements, tolerance=.1)


def test_face_straddling_release_boundary_rejected():
    nodes, elements = fixture_mesh()
    with pytest.raises(ValueError, match="straddles"):
        release(nodes, elements, {"left": {1, 2}}, {"left": 0}, (0, 0, -.25), (0, 0, 1))
