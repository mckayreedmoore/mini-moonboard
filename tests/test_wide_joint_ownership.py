"""Pure wide ownership contracts; actual CAD recovery is separately serialized."""
import pytest

from fea import wide_joint_ownership as model


def tetra():
    corners = [(0., 0., 0.), (1., 0., 0.), (0., 1., 0.), (0., 0., 1.)]
    mids = [tuple((corners[i][k]+corners[j][k])/2 for k in range(3))
            for i, j in ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))]
    return dict(enumerate(corners+mids, 1)), {1: tuple(range(1, 11))}


def test_exact_quadratic_volume_and_centroid_translate():
    nodes, elements = tetra()
    v, centre, error = model.mesh_moments(nodes, elements)
    assert v == pytest.approx(1/6)
    assert centre == pytest.approx([.25]*3)
    assert error == 0
    shifted = {n: tuple(p[i]+(4., -3., 2.)[i] for i in range(3)) for n, p in nodes.items()}
    assert model.mesh_moments(shifted, elements)[1] == pytest.approx([4.25, -2.75, 2.25])


def test_malformed_quadratic_mesh_rejected():
    nodes, elements = tetra()
    nodes[5] = (9., 9., 9.)
    with pytest.raises(ValueError):
        model.mesh_moments(nodes, elements)


def test_exact_wide_base_inventory_has_six_posts_and_no_old_center_posts():
    names = model.base_member_names()
    assert len(names) == 11
    assert len([n for n in names if n.startswith("base_post_")]) == 6
    assert {"kicker_left", "kicker_right", "base_header"} <= names
    assert "base_post_center_left" not in names and "base_post_center_right" not in names
    assert "not isolated bolts" in model.LIMITS
