"""The exterior upper-joint revision changes real stock, bores and washer basis."""
import copy

import cadquery as cq
import pytest

from mini_moonboard import compact_exterior_brace_frame as exterior
from mini_moonboard import compact_floor_rail_frame as floor
from scripts import clear_space_study
from scripts import compact_thick_geometry as geometry_builder


def test_upper_bolt_axes_and_interfaces_use_actual_64_mm_pattern():
    expected = exterior.bolt_points()
    assert (expected[1]-expected[0]).Length == pytest.approx(64.)
    old = exterior.previous.bolt_points()
    assert ((expected[0]+expected[1])/2-(old[0]+old[1])/2).Length < 1.e-7
    connections = exterior.connections()
    assert sum(c.kind == 'bolt' for c in connections) == 20
    assert len(exterior.panel_connections()) == 66
    for side in ('left', 'right'):
        bolts = [c for c in connections if c.name.startswith('lumber_leg_bolt_'+side)]
        assert len(bolts) == 2
        assert (bolts[1].start-bolts[0].start).Length == pytest.approx(64.)
        for bolt, point in zip(bolts, expected, strict=True):
            interface = exterior.bolt_interface_point(bolt)
            assert (interface.y, interface.z) == pytest.approx((point.y, point.z))
            assert abs(interface.x) == pytest.approx(1219.2)
            assert bolt.start.x*bolt.direction.x > 0


@pytest.fixture(scope='module')
def current_stock_and_drilling():
    return ({p.name:p for p in exterior.uncut_wood_parts()},
            {p.name:p for p in exterior.parts()},
            {p.name:p for p in exterior.previous.uncut_wood_parts()})


def test_24_mm_tail_restores_stock_and_preserves_square_outboard_knees(current_stock_and_drilling):
    raw, _, old = current_stock_and_drilling
    planes = exterior.trim_planes()
    assert set(planes) == {'lumber_leg_left', 'lumber_leg_right'}
    for name, plane in planes.items():
        normal = cq.Vector(*plane['keep_normal_xyz'])
        old_plane = exterior.previous.trim_planes()[name]
        assert old_plane['offset_mm']-plane['offset_mm'] == pytest.approx(6.)
        vertices = [v.Center() for v in raw[name].shape.Vertices()]
        assert min(v.dot(normal) for v in vertices) == pytest.approx(plane['offset_mm'])
        assert raw[name].shape.Volume() > old[name].shape.Volume()
        assert old[name].shape.cut(raw[name].shape).Volume() < .01
    assert exterior.LEG_TOP_PROJECTION_MM == 24.
    assert len(exterior.KNEE_NAMES) == 4
    for name in exterior.KNEE_NAMES:
        part = raw[name]
        box = part.shape.BoundingBox()
        assert min(abs(box.xmin), abs(box.xmax)) >= 1219.2-1.e-6
        assert part.blank[1] == pytest.approx(139.7)
        assert part.blank[2] == pytest.approx(88.9 if name.endswith('_rim') else 38.1)
        # A square-ended independent prism has its complete rectangular blank volume.
        assert part.shape.Volume() == pytest.approx(part.blank[0]*part.blank[1]*part.blank[2])


def test_rebuilt_receivers_restore_crescents_of_previous_upper_bores(current_stock_and_drilling):
    raw, drilled, _ = current_stock_and_drilling
    old_points = exterior.previous.bolt_points()
    direction = (old_points[1]-old_points[0]).normalized()
    for side in ('left', 'right'):
        for index, bolt_point in enumerate(exterior.bolt_points()):
            bolt = next(c for c in exterior.connections()
                        if c.name == f'lumber_leg_bolt_{side}_{index+1}')
            radius = exterior.bolt_dimensions(bolt)['hole_diameter_mm']/2
            # Old and new bores overlap. Probe the inward old-only crescent,
            # not the old axis, which is still inside the new clearance bore.
            old_only = old_points[index]+direction*(radius-1.)*(1 if index == 0 else -1)
            for name in bolt.members:
                bounds = raw[name].shape.BoundingBox()
                x = (bounds.xmin+bounds.xmax)/2
                probe = cq.Vector(x, old_only.y, old_only.z)
                new_axis = cq.Vector(x, bolt_point.y, bolt_point.z)
                assert raw[name].shape.isInside(probe)
                assert drilled[name].shape.isInside(probe)
                assert not drilled[name].shape.isInside(new_axis)


def test_thick_washer_procurement_applies_only_to_revised_exterior(monkeypatch):
    def fake_build(candidate):
        return {'candidate':candidate.KEY, 'source_sha256':{},
                'geometries_by_bolt_name':{
                    c.name:{'diameter_mm':c.diameter}
                    for c in candidate.connections() if c.kind == 'bolt'}}
    monkeypatch.setattr(geometry_builder, 'build', fake_build)
    original = clear_space_study.geometry(floor)
    revised = clear_space_study.geometry(exterior)
    repeated = clear_space_study.geometry(floor)
    for name, bounds in revised['hardware_resistance_bounds_by_name'].items():
        if name.startswith('lumber_leg_bolt_'):
            assert bounds['washer_thickness_mm'] == pytest.approx(3.)
    for candidate in (original, repeated):
        for name, bounds in candidate['hardware_resistance_bounds_by_name'].items():
            if name.startswith('lumber_leg_bolt_'):
                assert bounds['washer_thickness_mm'] == pytest.approx(2.1844)
    assert copy.deepcopy(original['hardware_resistance_bounds_by_name']) == repeated['hardware_resistance_bounds_by_name']
