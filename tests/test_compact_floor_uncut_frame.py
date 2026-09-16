"""New runner offset must create full-stock contacts and complete bolt grips."""
import cadquery as cq
import pytest

from mini_moonboard import compact_floor_flush_frame as previous
from mini_moonboard import compact_floor_uncut_frame as model


@pytest.mark.parametrize('side, sign', [('left', -1), ('right', 1)])
def test_outboard_runner_contacts_full_stock_and_keeps_kicker_axes(side, sign):
    raw = {p.name: p for p in model.uncut_wood_parts()}
    old = {p.name: p for p in previous.uncut_wood_parts()}
    runner = raw['base_floor_'+side].shape
    post = raw['base_post_outer_'+side].shape
    leg = raw['lumber_leg_'+side].shape
    assert leg.Volume() == pytest.approx(old['lumber_leg_'+side].shape.Volume())
    assert leg.BoundingBox().xlen == pytest.approx(88.9)
    assert post.BoundingBox().xlen == pytest.approx(139.7)
    assert post.BoundingBox().zmin == pytest.approx(0.)
    for member in (post, leg):
        assert runner.intersect(member).Volume() < 1.e-5
        assert runner.distance(member) < 1.e-7
    assert raw['base_header'].shape.BoundingBox().xlen == pytest.approx(2616.2)
    for old_connection in previous.panel_connections():
        current = next(c for c in model.panel_connections() if c.name == old_connection.name)
        assert current.start.toTuple() == old_connection.start.toTuple()
    assert model.additional_machining_cutters() == ()
    assert model.floor_recess_geometry() == {}
    assert model.KEY != previous.KEY


def test_runner_stacks_follow_actual_receiver_order_and_nominal_threads_seat():
    raw = {p.name: p for p in model.uncut_wood_parts()}
    bolts = [c for c in model.connections() if c.kind == 'bolt']
    assert len(bolts) == 12
    for connection in bolts:
        assert connection.direction.x*connection.start.x > 0
        if not connection.name.startswith('rail_'):
            continue
        spec = model.bolt_dimensions(connection)
        assert spec['thread_start_mm'] < connection.grip+2*spec['washer_thickness_mm']
        assert connection.length > connection.grip+2*spec['washer_thickness_mm']+spec['nut_height_mm']
        axis = cq.Solid.makeCylinder(.1, connection.length, connection.start, connection.direction)
        lengths = [raw[name].shape.intersect(axis).Volume()/(3.141592653589793*.1**2)
                   for name in connection.members]
        assert sum(lengths) == pytest.approx(connection.grip, abs=1.e-4)
        expected = model.EXPECTED_BEARING_LENGTHS_MM[connection.name]
        for name, length in zip(connection.members, lengths):
            assert length == pytest.approx(expected[name], abs=1.e-4)
        interface = model.bolt_interface_point(connection)
        assert abs(interface.x) == pytest.approx(1308.1)


def test_full_bevel_preserves_support_and_front_pitch_survives_drill_errors():
    raw = {p.name: p for p in model.uncut_wood_parts()}
    header = raw['base_header'].shape.BoundingBox()
    for side in ('left', 'right'):
        rim = raw['base_side_'+side].shape
        foot = [v.Center() for v in rim.Vertices() if abs(v.Center().z-277.) < 1.e-6]
        assert min(v.y for v in foot) == pytest.approx(-223.862729528, abs=1.e-6)
        assert max(v.y for v in foot) == pytest.approx(-41.497331208, abs=1.e-6)
        assert max(v.y for v in foot)-header.ymin == pytest.approx(134.202668792, abs=1.e-6)
        assert rim.intersect(raw['base_header'].shape).Volume() < 1.e-5
    a, b = model.front_points()
    assert (b-a).Length-2*1.0 > 4*9.525


def test_header_post_angles_mount_on_the_new_inner_faces():
    raw = {p.name: p for p in model.uncut_wood_parts()}
    for name, origin, _, _, _, second in model.stations():
        if name.startswith('clip_timber_header_outer_'):
            bounds = raw[second].shape.BoundingBox()
            assert origin.x == pytest.approx(bounds.xmax if name.endswith('left') else bounds.xmin)
