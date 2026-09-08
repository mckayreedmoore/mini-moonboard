"""Pure corrected-grid feature routing; full cutter checks run with parent CAD export."""
from collections import Counter

import cadquery as cq
import pytest

from mini_moonboard import panel_grid_v2 as grid
from mini_moonboard import wide_machining_features as features


def test_every_official_hole_maps_to_exact_actual_panel():
    tnut = Counter(features.panel_name(x, s) for x, s in grid.main_tnut_datums().values())
    led = Counter(features.panel_name(x, s) for x, s in grid.main_led_datums().values())
    kicker = Counter(features.panel_name(x) for x, _ in grid.kicker_foothold_datums().values())
    assert sum(tnut.values())+sum(kicker.values()) == 142
    assert sum(led.values()) == 132
    assert kicker == {"kicker_left": 5, "kicker_right": 5}
    for label in ("A7", "F7", "K7"):
        assert "lower" in features.panel_name(*grid.main_led_datums()[label])
        assert "upper" in features.panel_name(*grid.main_tnut_datums()[label])


@pytest.mark.parametrize("x,s", [(-1., 20.), (2438.4, 20.), (200., -1.), (200., 2438.4), (float("nan"), 20.)])
def test_unknown_grid_targets_fail(x, s):
    with pytest.raises(ValueError):
        features.panel_name(x, s)


def test_actual_plane_uses_face_geometry_not_blank_origin():
    shape = cq.Solid.makeBox(10., 20., 30., cq.Vector(5., 7., 225.))
    centre, normal, area, count = features.lower_bearing_plane(shape)
    assert centre.toTuple() == pytest.approx((10., 17., 225.))
    assert normal.toTuple() == (0., 0., -1.)
    assert area == pytest.approx(200.) and count == 1


def test_corner_only_ground_contact_is_not_a_bearing_plane():
    shape = cq.Solid.makeBox(10., 20., 30.).rotate((0, 0, 0), (1, 0, 0), 15.)
    with pytest.raises(ValueError, match="horizontal"):
        features.lower_bearing_plane(shape)
