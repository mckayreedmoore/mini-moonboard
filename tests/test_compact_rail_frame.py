"""Focused raised-rail geometry and interface contracts."""
import pytest

from mini_moonboard import compact_rail_frame as model


def test_rail_interfaces_and_complete_separate_stacks():
    bolts = [c for c in model.connections() if isinstance(c, model.RailBolt)]
    assert len(bolts) == 16
    assert len([c for c in model.connections() if c.name.startswith('lumber_leg_bolt_')]) == 6
    for c in bolts:
        front = c.name.startswith('rail_front_')
        assert abs(model.bolt_interface_point(c).x) == pytest.approx(model.b.HALF-38.1 if front else model.b.HALF)
        assert c.length == pytest.approx(101.6 if front else 152.4)
        assert c.grip == pytest.approx(76.2 if front else 127.)
    assert len(bolts[0].components()) == len(bolts[-1].components()) == 5
    assert model.base.HEADER_BOTTOM-model.RAIL_TOP_Z == pytest.approx(2.)
    for name,(grain,section) in model.MEMBER_AXES.items():
        assert name.startswith('base_rail_tie_')
        assert grain.toTuple() == (0.,1.,0.)
        assert section.toTuple() == (1.,0.,0.)


def test_outer_post_connections_move_consistently_and_panel_count_stays_66():
    old = {c.name:c for c in model.previous.connections()}
    moved = [c for c in model.panel_connections() if c.members[1].startswith('base_post_outer_')]
    assert len(moved) == 4
    for c in moved:
        sign = -1 if c.name.endswith('left') or c.members[0].endswith('left') else 1
        assert c.start.x-old[c.name].start.x == pytest.approx(-sign*38.1)
    assert len(model.panel_connections()) == 66
    for point in model.front_points():
        assert abs(point.z-model.RAIL_CENTER_Z) == pytest.approx(25.)
    assert sum(p.z for p in model.rear_points())/4 == pytest.approx(model.RAIL_CENTER_Z)


def test_actual_new_wood_and_fresh_kicker_geometry():
    raw = {p.name:p for p in model.raw_changed_parts()}
    for side,sign in (('left',-1),('right',1)):
        rail = raw['base_rail_tie_'+side].shape
        post = raw['base_post_outer_'+side].shape
        kicker = raw['kicker_'+side].shape
        assert rail.isValid() and post.isValid() and kicker.isValid()
        assert rail.intersect(kicker).Volume() < .01
        assert rail.intersect(post).Volume() < .01
        assert rail.intersect(raw['base_header'].shape).Volume() < .01
        bounds = post.BoundingBox()
        assert (bounds.xmin if sign<0 else bounds.xmax) == pytest.approx(sign*(model.b.HALF-38.1))
    for c in model.panel_connections():
        if c.members[1].startswith('base_post_outer_'):
            tip = c.start+c.direction*(c.length-1.)
            assert raw[c.members[1]].shape.isInside(tip,1e-5)
