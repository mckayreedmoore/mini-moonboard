import cadquery as cq
import pytest

from mini_moonboard import compact_floor_flush_frame as flush_layout
from mini_moonboard import compact_spliced_flush_top as model
from mini_moonboard import compact_spliced_kicker as previous


def test_candidate_relocates_only_upper_pair_to_authorized_flush_layout():
    old = {connection.name: connection for connection in previous.connections()}
    new = {connection.name: connection for connection in model.connections()}
    assert model.KEY == 'compact-spliced-flush-top-development'
    assert old.keys() == new.keys()
    assert sum(connection.kind == 'bolt' for connection in new.values()) == 20

    moved = {
        name for name, connection in new.items()
        if (connection.start-old[name].start).Length > 1.e-8
    }
    assert moved == {
        f'lumber_leg_bolt_{side}_{index}'
        for side in ('left', 'right') for index in (1, 2)
    }
    assert model.bolt_points() == flush_layout.bolt_points()
    delta = model.bolt_points()[1]-model.bolt_points()[0]
    assert delta.Length == pytest.approx(56.)
    assert ((model.bolt_points()[0]+model.bolt_points()[1])/2).toTuple() == pytest.approx(
        (0., 1134.25, 1761.5))
    assert delta.normalized().toTuple() == pytest.approx(
        cq.Vector(0., 18., 53.).normalized().toTuple())
    for connection in new.values():
        if connection.name in moved:
            assert connection.diameter == pytest.approx(12.7)
            point = model.bolt_points()[int(connection.name.rsplit('_', 1)[1])-1]
            assert connection.start.y == pytest.approx(point.y)
            assert connection.start.z == pytest.approx(point.z)
            assert connection.start.x*connection.direction.x > 0
            assert model.bolt_interface_point(connection).y == pytest.approx(point.y)
            assert model.bolt_interface_point(connection).z == pytest.approx(point.z)
        else:
            assert connection is old[connection.name]


def test_candidate_retains_knees_kicker_rows_and_rim_overhang():
    assert model.REAR_OVERHANG_MM == 7.
    assert model.LEG_TOP_PROJECTION_MM == 0.
    assert len([name for name in model.KNEE_NAMES if name.startswith('base_knee_')]) == 4
    assert len(model.panel_connections()) == 66
    lower = [connection for connection in model.panel_connections()
             if connection.name in model.MOVED_NAMES]
    assert len(lower) == 4
    assert {connection.start.z for connection in lower} == {60.}
    for connection in model.connections():
        if connection.kind == 'bolt':
            assert connection.start.x*connection.direction.x > 0


@pytest.mark.parametrize('side', ['left', 'right'])
def test_rear_leg_top_is_flush_to_retained_rim_face(side):
    raw = {part.name: part for part in model.uncut_wood_parts()}
    leg = raw[f'lumber_leg_{side}'].shape
    rim = raw[f'base_side_{side}'].shape
    rim_grain = model.axes()[4]
    rim_normal = cq.Vector(0., rim_grain.z, -rim_grain.y).normalized()
    assert min(vertex.Center().dot(rim_normal) for vertex in leg.Vertices()) == pytest.approx(
        min(vertex.Center().dot(rim_normal) for vertex in rim.Vertices()))
    assert len(leg.Solids()) == 1


def test_changed_leg_and_rim_stock_has_only_relocated_upper_bores():
    old_connections = {connection.name: connection for connection in previous.connections()}
    raw = {part.name: part for part in model.uncut_wood_parts()}
    drilled = {part.name: part for part in model.parts()}
    for connection in model.connections():
        if not connection.name.startswith('lumber_leg_bolt_'):
            continue
        old = old_connections[connection.name]
        for name in connection.members:
            bounds = raw[name].shape.BoundingBox()
            old_point = cq.Vector((bounds.xmin+bounds.xmax)/2, old.start.y, old.start.z)
            new_point = cq.Vector((bounds.xmin+bounds.xmax)/2,
                                  connection.start.y, connection.start.z)
            probe = cq.Solid.makeSphere(.5, old_point)
            assert drilled[name].shape.intersect(probe).Volume() == pytest.approx(
                probe.Volume(), rel=1.e-5)
            probe = cq.Solid.makeSphere(.5, new_point)
            assert drilled[name].shape.intersect(probe).Volume() == pytest.approx(0., abs=1.e-8)

        for component in connection.components()[1:3]:
            centre = component.Center()
            assert centre.y == pytest.approx(connection.start.y)
            assert centre.z == pytest.approx(connection.start.z)

        direction = connection.direction.normalized()
        washer = previous.bolt_dimensions(connection)['washer_thickness_mm']
        first = raw[connection.members[0]].shape
        second = raw[connection.members[1]].shape
        assert min((vertex.Center()-connection.start).dot(direction)
                   for vertex in first.Vertices()) == pytest.approx(washer)
        assert max((vertex.Center()-connection.start).dot(direction)
                   for vertex in second.Vertices()) == pytest.approx(connection.grip+washer)
