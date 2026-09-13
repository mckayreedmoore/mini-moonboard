import pytest

from mini_moonboard import compact_knee_frame as model


def test_knee_datums_and_hardware_have_explicit_physical_stack():
    _rim,leg,axis,length = model.knee_datums()
    assert length > model.RIM_TAB_REACH_MM+model.LEG_TAB_REACH_MM
    assert axis.x == 0
    assert leg.z == pytest.approx(1050.)
    assert model.END_EXTENSION_MM > 7*12.7+3
    bolts = [c for c in model.connections() if c.name.startswith('knee_bolt_')]
    assert len(bolts) == 8
    for bolt in bolts:
        interface = model.bolt_interface_point(bolt)
        assert abs(interface.x) == pytest.approx(model.b.HALF)
        assert bolt.grip == pytest.approx(133.35)
        dims = model.bolt_dimensions(bolt)
        nut_start = bolt.grip+2*dims['washer_thickness_mm']
        assert nut_start > model.bolt_dimensions(bolt)['thread_start_mm']
        assert bolt.length-nut_start-dims['nut_height_mm'] > 2*25.4/16
        assert model.EXPECTED_BEARING_LENGTHS_MM[bolt.name][bolt.members[0]] == 44.45


def test_opposite_tabs_retain_half_width_and_full_middle():
    import cadquery as cq

    rim,_,grain,length = model.knee_datums()
    for side,sign in (('left',-1),('right',1)):
        shape = model._prism(side,-44.45,44.45,-110.,length+110.)
        for member,_,_,cut in model.additional_machining_cutters():
            if member == f'base_knee_{side}':
                shape = shape.cut(cut)
        interface = sign*model.b.HALF
        for station,retained_sign in ((0.,sign),(length,-sign)):
            point = rim+grain*station
            assert shape.isInside(cq.Vector(interface+retained_sign*22.,point.y,point.z))
            assert not shape.isInside(cq.Vector(interface-retained_sign*22.,point.y,point.z))
        middle = rim+grain*(length/2)
        for offset in (-22.,22.):
            assert shape.isInside(cq.Vector(interface+offset,middle.y,middle.z))


def test_tab_shoulders_clear_actual_leg_profiles():
    raw = {p.name:p for p in model.raw_changed_parts()}
    for side in ('left','right'):
        name = f'base_knee_{side}'
        knee = raw[name].shape
        for member,_,_,cut in model.additional_machining_cutters():
            if member == name:
                knee = knee.cut(cut)
        overlap = knee.intersect(raw[f'lumber_leg_{side}'].shape)
        assert overlap.Volume() < 1e-5


def test_four_endpoint_points_remove_free_rigid_body_roll():
    import numpy as np

    for side in ('left','right'):
        points = [np.array(model.bolt_interface_point(c).toTuple()) for c in model.connections()
                  if c.name.startswith(f'knee_bolt_{side}_')]
        centre = np.mean(points,axis=0)
        rows = []
        for point in points:
            x,y,z = point-centre
            skew = np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
            rows.append(np.column_stack((np.eye(3),-skew)))
        assert np.linalg.matrix_rank(np.vstack(rows)) == 6
