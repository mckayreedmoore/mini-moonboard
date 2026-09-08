"""Independent aggregate wrench/complete-history controls; no capacity claim."""
import pytest

from fea.publish_wide_asymmetric import group_actions, replay, status_complete


def test_groups_use_distinct_references_and_complete_floor_union():
    nodes = {1: (-10., 0., 0.), 2: (10., 0., 0.), 3: (0., 20., 0.)}
    reactions = {1: (2., 3., 5.), 2: (-1., 4., 6.), 3: (0., -7., 9.)}
    own = {"local_axes_world": ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.)),
           "legs": {"left": {"floor_nodes": [1], "reference_world_mm": (-10., 0., 10.)},
                    "right": {"floor_nodes": [2], "reference_world_mm": (10., 0., 10.)}},
           "base": {"floor_nodes": [3], "reference_world_mm": (0., 10., 0.)}}
    result = group_actions(nodes, reactions, own)
    assert result["left"]["on_board_world_n_nmm"] == [2., 3., 5., 30., -20., 0.]
    assert result["right"]["on_board_world_n_nmm"] == [-1., 4., 6., 40., 10., 0.]
    assert result["base"]["on_board_world_n_nmm"] == [0., -7., 9., 90., 0., 0.]
    own["base"]["floor_nodes"] = [2, 3]
    with pytest.raises(ValueError, match="ownership"):
        group_actions(nodes, reactions, own)
    own["base"]["floor_nodes"] = [3]
    reactions[4] = (0., 0., 0.)
    with pytest.raises(ValueError, match="every floor"):
        group_actions(nodes, reactions, own)


def test_complete_basis_history_and_rejection():
    text = "\n".join(f"{i} 1 1 1 {i} 1 1" for i in (1, 2, 3))
    status_complete(text)
    with pytest.raises(ValueError, match="Incomplete"):
        status_complete(text.splitlines()[0])
    with pytest.raises(ValueError, match="Unexpected"):
        status_complete(text.replace("3 1 1 1 3 1 1", "3 1 1 1 2 1 1"))


def test_missing_evidence_rejects_before_reconstruction():
    with pytest.raises(ValueError, match="Incomplete wide"):
        replay({})
