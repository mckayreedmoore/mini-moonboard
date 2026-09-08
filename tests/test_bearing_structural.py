"""Numeric mesh and frozen-output guards; never launch CAD or a solver."""
import builtins
import math

import pytest

from fea import prepare_bearing_structural as prepare
from fea import solve_bearing_frame as solve


def tetrahedron(corners=None):
    corners = corners or ((0., 0., 0.), (1., 0., 0.),
                          (0., 1., 0.), (0., 0., 1.))
    edges = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))
    points = [*corners, *(tuple((corners[a][k]+corners[b][k])/2
                               for k in range(3)) for a, b in edges)]
    return dict(enumerate(points, 1)), {17: tuple(range(1, 11))}


def forbid_heavy_imports(monkeypatch):
    original = builtins.__import__

    def checked(name, *args, **kwargs):
        if name.split(".")[0] in {"gmsh", "cadquery", "mini_moonboard"}:
            pytest.fail(f"Guard unexpectedly imported {name}")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", checked)


def test_straight_quadratic_tetrahedron_has_analytic_volume():
    nodes, elements = tetrahedron()
    volume, midpoint_error = solve.straight_mesh_volume(nodes, elements)
    assert volume == pytest.approx(1/6)
    assert midpoint_error == 0
    shifted = {n+10: tuple(2*x+3 for x in p) for n, p in nodes.items()}
    volume, midpoint_error = solve.straight_mesh_volume(
        nodes | shifted, elements | {18: tuple(range(11, 21))})
    assert volume == pytest.approx(9/6)
    assert midpoint_error == 0


@pytest.mark.parametrize("corners", [
    ((0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1)),
    ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, -1)),
    ((0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)),
])
def test_reversed_inverted_or_flat_tetrahedron_rejected(corners):
    with pytest.raises(ValueError, match="Nonpositive.*Jacobian"):
        solve.straight_mesh_volume(*tetrahedron(corners))


@pytest.mark.parametrize("node", range(5, 11))
def test_each_midside_must_be_at_its_own_edge_midpoint(node):
    nodes, elements = tetrahedron()
    x, y, z = nodes[node]
    nodes[node] = (x+0.001, y, z)
    with pytest.raises(ValueError, match="not straight-sided"):
        solve.straight_mesh_volume(nodes, elements)


@pytest.mark.parametrize("node", [1, 5])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_nonfinite_corner_or_midside_rejected(node, bad):
    nodes, elements = tetrahedron()
    nodes[node] = (bad, 0, 0)
    with pytest.raises(ValueError, match="Finite nonempty"):
        solve.straight_mesh_volume(nodes, elements)


@pytest.mark.parametrize("bad_ids", [
    tuple(range(1, 10)), tuple(range(1, 12)),
    (*range(1, 10), 9), (*range(1, 10), 99),
])
def test_missing_duplicate_or_wrong_connectivity_count_rejected(bad_ids):
    nodes, _ = tetrahedron()
    with pytest.raises(ValueError, match="Invalid C3D10 connectivity"):
        solve.straight_mesh_volume(nodes, {17: bad_ids})


@pytest.mark.parametrize("bad_point", [(), (0, 0), (0, 0, 0, 0)])
def test_wrong_coordinate_count_rejected(bad_point):
    nodes, elements = tetrahedron()
    nodes[1] = bad_point
    with pytest.raises(ValueError, match="Finite nonempty"):
        solve.straight_mesh_volume(nodes, elements)


@pytest.mark.parametrize("empty", ["nodes", "elements"])
def test_empty_mesh_rejected(empty):
    nodes, elements = tetrahedron()
    with pytest.raises(ValueError, match="Finite nonempty"):
        solve.straight_mesh_volume({} if empty == "nodes" else nodes,
                                   {} if empty == "elements" else elements)


@pytest.mark.parametrize("size,modulus", [
    (0, 7000), (20, 7000), (math.nan, 7000), (math.inf, 7000),
    (60, 0), (40, -1), (60, math.nan), (40, math.inf), (60, -math.inf),
])
def test_invalid_solver_parameters_reject_before_gmsh(monkeypatch, size, modulus):
    forbid_heavy_imports(monkeypatch)
    with pytest.raises(ValueError, match="mesh size 60/40.*positive finite"):
        solve.run(size, modulus)


@pytest.mark.parametrize("existing", ["directory", "stability"])
def test_preparation_preserves_existing_evidence_without_construction(
        monkeypatch, tmp_path, existing):
    directory = tmp_path/"generated"
    stability = tmp_path/"stability.json"
    if existing == "directory":
        directory.mkdir()
        evidence = directory/"existing.json"
    else:
        evidence = stability
    evidence.write_text("retain exact evidence")
    monkeypatch.setattr(prepare, "DIRECTORY", directory)
    monkeypatch.setattr(prepare, "STABILITY", stability)
    def unexpected_construction(*args, **kwargs):
        pytest.fail("Refusal must precede CAD preparation")

    monkeypatch.setattr(prepare, "locations", unexpected_construction)
    monkeypatch.setattr(prepare, "mass_state", unexpected_construction)
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        prepare.main()
    assert evidence.read_text() == "retain exact evidence"
    assert directory.exists() == (existing == "directory")
    assert stability.exists() == (existing == "stability")
