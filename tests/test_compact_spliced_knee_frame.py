import pytest

from mini_moonboard import compact_spliced_knee_frame as model


def test_independent_splice_connections_and_complete_stacks():
    connections = model.connections()
    splice = [c for c in connections if c.name.startswith('knee_splice_bolt_')]
    end = [c for c in connections if c.name.startswith('knee_bolt_')]
    assert len(splice) == len(end) == 8
    assert len(model.KNEE_NAMES) == 4
    assert model.additional_machining_cutters() == ()
    assert min(b-a for a,b in zip(sorted(model.splice_stations()),sorted(model.splice_stations())[1:],strict=False)) >= 4*9.525
    for c in splice+end:
        assert c.grip == pytest.approx(76.2 if c in splice else 127.)
        dims = model.bolt_dimensions(c)
        nut_start = c.grip+2*dims['washer_thickness_mm']
        assert nut_start >= dims['thread_start_mm']
        assert c.length-nut_start-dims['nut_height_mm'] >= 2*25.4/16
        assert abs(model.bolt_interface_point(c).x) == pytest.approx(model.b.HALF)


def test_splice_contact_samples_use_net_area_and_actual_interface():
    import math

    rows = model.overlap_contact_datums()
    assert len(rows) == 18
    overlap = model.knee_datums()[3]-340.
    expected_area = overlap*139.7-4*math.pi*(11.1125/2)**2
    for side,sign in (('left',-1),('right',1)):
        selected = [r for r in rows if r['first'] == f'base_knee_{side}_rim']
        assert len(selected) == 9
        assert sum(r['tributary_area_mm2'] for r in selected) == pytest.approx(expected_area)
        assert all(r['point_xyz_mm'][0] == sign*model.b.HALF for r in selected)
        assert all(r['normal_xyz'] == (sign,0.,0.) for r in selected)


def test_56mm_upper_pattern_preserves_centre_with_toleranced_edge_reserve():
    import cadquery as cq

    points = model.bolt_points()
    old = model.previous.bolt_points()
    assert (sum(points,cq.Vector())-sum(old,cq.Vector())).Length < 1e-8
    assert (points[1]-points[0]).Length == pytest.approx(56.)
    _,foot,leg,_,rim = model.axes()
    for point in points:
        for grain,datum in ((leg,foot),(rim,model.b.point(0.,0.,69.85))):
            normal = cq.Vector(0.,grain.z,-grain.y)
            assert 69.85-abs((point-datum).dot(normal))-4*12.7-3. >= 3.
    assert 56.-4*12.7 == pytest.approx(5.2)
    for connection in model.connections():
        if connection.name.startswith('lumber_leg_bolt_'):
            point = points[int(connection.name.rsplit('_',1)[1])-1]
            assert connection.start.y == pytest.approx(point.y)
            assert connection.start.z == pytest.approx(point.z)
