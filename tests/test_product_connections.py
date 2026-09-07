"""Selected hardware datum/envelope checks, independent of frame booleans."""
import math

import cadquery as cq
import pytest

from mini_moonboard.box_frame import Connection
from mini_moonboard.product_connections import selected_connection
from mini_moonboard.selected_hardware import spec_for


@pytest.mark.parametrize("direction", [(1, 0, 0), (0, -1, 0), (0, .6, .8)])
def test_bolt_conversion_preserves_grip_and_annular_washers(direction):
    old = Connection("leg_stitch_left_1", cq.Vector(11, 20, 30),
                     cq.Vector(*direction), 57.15, 9.525, ("a", "b"), "bolt", 38.1)
    new = selected_connection(old)
    assert selected_connection(new) is new
    spec = spec_for(new)
    t = spec.washer_thickness_nominal_mm
    assert (new.start+new.direction*t-old.start-old.direction*2).Length < 1e-8
    assert new.grip == old.grip
    shaft, first, last, head, nut = new.components()
    expected = math.pi/4*(spec.washer_od_max_mm**2-spec.washer_id_min_mm**2)*t
    assert first.Volume() == pytest.approx(expected)
    assert last.Volume() == pytest.approx(expected)
    assert first.intersect(shaft).Volume() < 1e-8
    assert last.intersect(shaft).Volume() < 1e-8
    assert nut.intersect(shaft).Volume() < 1e-8
    assert all(s.isValid() for s in (shaft, first, last, head, nut))
    assert (last.Center()-first.Center()).dot(new.direction) == pytest.approx(t+old.grip)
    assert "inspection envelope" in new.product_status


@pytest.mark.parametrize("name, length, seating", [
    ("panel_1", 50.8, "flush"),
    ("transition_main_left_screw_1", 38.1, "flat"),
])
def test_screw_length_datum_and_head_allowance(name, length, seating):
    old = Connection(name, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1),
                     30, 3.75, ("a", "b"))
    new = selected_connection(old)
    spec = spec_for(new)
    shaft, head = new.components()
    assert new.start == old.start
    assert new.length == length
    assert shaft.BoundingBox().zmax == pytest.approx(length)
    bounds = head.BoundingBox()
    if seating == "flush":
        assert bounds.zmin == pytest.approx(0)
        assert bounds.zmax == pytest.approx(spec.head_allowance_height_mm)
    else:
        assert bounds.zmax == pytest.approx(0)
        assert bounds.zmin == pytest.approx(-spec.head_allowance_height_mm)
    assert bounds.xlen == pytest.approx(spec.head_allowance_diameter_mm)
