"""Synthetic ownership and conditional free-body checks; no CAD construction."""
import math

import pytest

from fea import timber_joint_demand as demand


def synthetic_mesh():
    nodes = {n: (1.5, 10.+n/100, 1.) for n in range(1, 11)}
    nodes.update({n+10: (1.5, -10.+n/100, 1.) for n in range(1, 11)})
    return nodes, {1: tuple(range(1, 11)), 2: tuple(range(11, 21))}


def test_whole_leg_selection_excludes_base_gusset_in_same_x_slab():
    nodes, elements = synthetic_mesh()
    selected = demand.select_leg(nodes, elements, [1, 9, 0, 2, 12, 2], lambda p: p[1] > 0)
    assert selected == {1: elements[1]}
    nodes[10] = (1.5, 10., 3.)
    with pytest.raises(ValueError, match="crosses"):
        demand.select_leg(nodes, elements, [1, 9, 0, 2, 12, 2], lambda p: True)


def test_all_ten_nodes_must_match_actual_profile_and_connectivity():
    nodes, elements = synthetic_mesh()
    with pytest.raises(ValueError, match="profile"):
        demand.select_leg(nodes, elements, [1, 9, 0, 2, 12, 2], lambda p: p != nodes[10])
    with pytest.raises(ValueError, match="connectivity"):
        demand.select_leg(nodes, {1: (*range(1, 10), 99)}, [1, 9, 0, 2, 12, 2], lambda p: True)
    with pytest.raises(ValueError, match="Missing"):
        demand.select_leg(nodes, elements, [3, 9, 0, 4, 12, 2], lambda p: True)


def test_shared_nodes_must_be_on_rim_and_floor_ownership_complete():
    nodes = {1: (1., 2., 0.), 2: (1., 3., 4.), 3: (0., 3., 4.), 4: (1., 9., 0.)}
    elements = {1: (1, 2), 2: (2, 3), 3: (4,)}
    chosen = {1: elements[1]}
    args = (nodes, elements, chosen, {1, 4}, {3})
    assert demand.ownership(*args, lambda p: p == nodes[2], lambda p: p == nodes[1]) == ({1, 2}, {2}, {1})
    with pytest.raises(ValueError, match="interface"):
        demand.ownership(*args, lambda p: False, lambda p: p == nodes[1])
    with pytest.raises(ValueError, match="ownership"):
        demand.ownership(*args, lambda p: True, lambda p: True)
    with pytest.raises(ValueError, match="ownership"):
        demand.ownership(nodes, elements, chosen, {1}, {2}, lambda p: True, lambda p: True)


def test_free_body_sign_moment_reference_and_local_axes():
    nodes = {1: (-1., 0., 0.), 2: (1., 0., 0.)}
    reaction = {1: (0., 3., 20.), 2: (0., -3., 20.)}
    world = demand.resultant(nodes, reaction, (0., 2., 0.))
    assert world == pytest.approx([0, 0, 40, -80, 0, -6])
    axes = ((1., 0., 0.), (0., 0., 1.), (0., -1., 0.))
    assert demand.local_components(world, axes) == pytest.approx([0, 40, 0, -80, -6, 0])
    assert "zero gravity" in demand.LIMITS and "Not actual unanchored" in demand.LIMITS


def test_panel_edge_contact_cannot_be_reported_as_rim_only_transfer():
    nodes = {1: (1., 2., 0.), 2: (1., 3., 4.), 3: (0., 3., 4.),
             4: (1., 4., 5.), 5: (0., 4., 5.)}
    elements = {1: (1, 2, 4), 2: (2, 3), 3: (4, 5)}
    args = (nodes, elements, {1: elements[1]}, {1}, {3, 5})
    with pytest.raises(ValueError, match="interface"):
        demand.ownership(*args, lambda p: p == nodes[2], lambda p: p == nodes[1])
    assert demand.ownership(*args, lambda p: p in (nodes[2], nodes[4]),
                            lambda p: p == nodes[1])[1] == {2, 4}
    assert "not an isolated rim/bolt demand" in demand.LIMITS


@pytest.mark.parametrize("reaction", [{}, {1: (0., math.nan, 1.)}, {1: (0., 1.)}])
def test_invalid_or_incomplete_reactions_reject(reaction):
    with pytest.raises(ValueError, match="complete"):
        demand.resultant({1: (0., 0., 0.)}, reaction, (0., 0., 0.))


def test_existing_output_refuses_before_archive_or_geometry(tmp_path, monkeypatch):
    output = tmp_path/"report.json"
    output.write_text("retain")
    monkeypatch.setattr(demand, "OUTPUT", output)
    monkeypatch.setattr(demand, "authenticated_inputs", lambda: pytest.fail("Must not read archives"))
    with pytest.raises(FileExistsError, match="overwrite"):
        demand.main()
    assert output.read_text() == "retain"
