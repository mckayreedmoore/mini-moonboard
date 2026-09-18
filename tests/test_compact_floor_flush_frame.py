"""Requested finish uses actual adjoining planes without changing old geometry."""
import cadquery as cq
import pytest

from mini_moonboard import compact_floor_flush_frame as model
from mini_moonboard import compact_floor_taper_frame as previous


@pytest.mark.parametrize('side', ['left', 'right'])
def test_flush_faces_and_retained_stock(side):
    raw = {p.name: p for p in model.uncut_wood_parts()}
    old = {p.name: p for p in previous.uncut_wood_parts()}
    runner, post, leg, rim = [raw[n+'_'+side].shape for n in
                             ('base_floor', 'base_post_outer', 'lumber_leg', 'base_side')]
    assert runner.BoundingBox().ymin == pytest.approx(post.BoundingBox().ymin)
    assert rim.BoundingBox().ymin == pytest.approx(post.BoundingBox().ymin)
    leg_grain, rim_grain = model.axes()[2], model.axes()[4]
    leg_normal = cq.Vector(0., leg_grain.z, -leg_grain.y).normalized()
    rim_normal = cq.Vector(0., rim_grain.z, -rim_grain.y).normalized()
    assert max(v.Center().dot(leg_normal) for v in runner.Vertices()) == pytest.approx(
        max(v.Center().dot(leg_normal) for v in leg.Vertices()))
    assert min(v.Center().dot(rim_normal) for v in leg.Vertices()) == pytest.approx(
        min(v.Center().dot(rim_normal) for v in rim.Vertices()))
    for prefix in ('base_floor', 'base_side', 'lumber_leg'):
        name = prefix+'_'+side
        assert len(raw[name].shape.Solids()) == 1
        assert 0 < raw[name].shape.Volume() < old[name].shape.Volume()
        assert raw[name].shape.cut(old[name].shape).Volume() < 1.e-4
    # Upper trim must not inadvertently change the lower taper definition.
    record = model.floor_recess_geometry()['lumber_leg_'+side]
    assert record['taper_run_mm'] == 457.2
    assert record['max_recess_depth_mm'] == 38.1
    assert record['expected_retained_volume_mm3'] < record['expected_removed_volume_mm3']+leg.Volume()


def test_hardware_and_kickers_are_retained_but_acceptance_is_not_inherited():
    old = {c.name: c for c in previous.connections()}
    for c in model.connections():
        if c.name.startswith('lumber_leg_bolt_'):
            assert c.start.z < old[c.name].start.z
        elif c.name.startswith('rail_'):
            assert c.start.toTuple() != old[c.name].start.toTuple()
        elif c.name.startswith('clip_split_base_center_'):
            assert c.start.x == pytest.approx(old[c.name].start.x)
            assert c.start.y != old[c.name].start.y
        else:
            assert c is old[c.name]
    assert (model.bolt_points()[1]-model.bolt_points()[0]).Length == pytest.approx(56.)
    assert len([c for c in model.connections() if c.kind == 'bolt']) == 12
    assert model.panel_edge_cutouts() == {}
    assert model.LEG_TOP_PROJECTION_MM == 0.
    assert previous.LEG_TOP_PROJECTION_MM == 18.
    assert previous.REAR_OVERHANG_MM == 7.
    assert model.KEY != previous.KEY
    assert model.FLUSH_NATIVE_GEOMETRY_REQUIRED
    assert model.NATIVE_SQUARE_END_MEMBERS == ()


def test_relocated_upper_bolts_fit_full_end_and_directed_edge_screens():
    from scripts.thick_leg_geometry import edge_rays

    raw = {p.name: p for p in model.uncut_wood_parts()}
    for c in model.connections():
        if not c.name.startswith('lumber_leg_bolt_'):
            continue
        point = model.bolt_interface_point(c)
        for name in c.members:
            grain = model.axes()[2 if name.startswith('lumber_leg') else 4]
            _, edge = edge_rays(raw[name], point, grain)
            assert min(edge['grain_positive'], edge['grain_negative']) >= 7*c.diameter
            assert edge['depth_negative'] >= 4*c.diameter
            required = 4 if name.startswith('lumber_leg') else 1.5
            assert edge['depth_positive'] >= required*c.diameter


def test_relocated_runner_pairs_meet_all_direction_edge_and_end_screen():
    from scripts.thick_leg_geometry import edge_rays

    raw = {p.name: p for p in model.uncut_wood_parts()}
    for c in model.connections():
        if not c.name.startswith('rail_'):
            continue
        point = model.bolt_interface_point(c)
        for name in c.members:
            grain = (cq.Vector(0., 0., 1.) if name.startswith('base_post_') else
                     model.MEMBER_AXES[name][0] if name in model.MEMBER_AXES else model.axes()[2])
            _, edges = edge_rays(raw[name], point, grain)
            assert min(edges['grain_positive'], edges['grain_negative']) >= 7*c.diameter
            assert min(edges['depth_positive'], edges['depth_negative']) >= 4*c.diameter
    for points in (model.front_points(), model.rear_points()):
        assert (points[1]-points[0]).Length >= 4*9.525
