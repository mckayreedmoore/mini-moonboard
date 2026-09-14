"""The small-rail trial preserves installed interfaces and avoids screw axes."""
import math
from itertools import pairwise

import pytest

from mini_moonboard import compact_floor_rail_2x4_frame as model


def test_complete_joint_inventory_and_face_interfaces():
    connections = model.connections()
    bolts = [c for c in connections if c.kind == 'bolt']
    assert len(connections) == 224
    assert len(bolts) == 14
    assert len(model.panel_connections()) == 66
    assert not any(name.startswith('base_knee_') for c in connections for name in c.members)
    for c in bolts:
        assert c.start.x*c.direction.x > 0
        if c.name.startswith('rail_'):
            expected_interface = 1181.1 if '_front_' in c.name else 1219.2
            assert abs(model.bolt_interface_point(c).x) == pytest.approx(expected_interface)
            assert c.diameter == 6.35
            assert c.grip == pytest.approx(76.2 if '_front_' in c.name else 127.)
            first_wood_face = abs(c.start.x)+model.QUARTER_WASHER_THICKNESS_MM
            assert abs(model.bolt_interface_point(c).x)-first_wood_face == pytest.approx(38.1)
    assert sum('_front_' in c.name for c in bolts) == 6
    assert sum('_rear_' in c.name for c in bolts) == 4


def test_low_bolt_pattern_and_notch_preserve_placement_reserves():
    points = model.front_points()
    diameter = 6.35
    assert min((b-a).Length for a,b in pairwise(points))-5*diameter >= 3.
    for point in points:
        assert point.z-7*diameter >= 3.
        assert model.RAIL_DEPTH_MM-point.z-4*diameter >= 3.
        assert min(point.y-model.HEADER_BACK_Y, model.base.HEADER_FRONT_Y-point.y)-4*diameter >= 3.
    grain = model.axes()[2]
    for point in model.rear_points():
        assert point.z/grain.z-7*diameter >= 3.
        assert model.RAIL_DEPTH_MM-point.z-4*diameter >= 3.
    # The third front bore stays beyond the lower kicker screw tip.
    screw = next(c for c in model.panel_connections() if c.name == 'round_kicker_right_rim_1')
    tip = screw.start+screw.direction*screw.length
    last_bolt_y = max(p.y for p in points)
    assert tip.y-last_bolt_y > model.QUARTER_HOLE_DIAMETER_MM/2
    assert screw.start.x == pytest.approx(1162.05)
    assert screw.start.z == 60.
    for cutouts in model.panel_edge_cutouts().values():
        xmin,xmax,zmin,zmax = cutouts[0]
        assert xmax-xmin == pytest.approx(40.1)
        assert zmax-zmin == pytest.approx(90.9)


def test_quarter_stack_has_both_washers_head_and_outward_nut():
    bolt = next(c for c in model.connections() if c.name == 'rail_front_bolt_right_1')
    shaft, head_washer, nut_washer, head, nut = bolt.components()
    assert all(part.Volume() > 0 for part in (shaft, head_washer, nut_washer, head, nut))
    assert head.Center().x < head_washer.Center().x < nut_washer.Center().x < nut.Center().x
    assert shaft.Volume() == pytest.approx(math.pi*(6.35/2)**2*101.6)
    assert model.bolt_dimensions(bolt)['thread_start_mm'] == pytest.approx(76.2)
