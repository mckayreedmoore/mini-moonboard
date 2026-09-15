"""Outside runner interfaces and actual material removed at the leg foot."""
import cadquery as cq
import pytest

from mini_moonboard import compact_floor_recess_frame as model


def test_recess_candidate_keeps_complete_kickers_and_real_laps():
    connections = model.connections()
    assert len(connections) == 222
    assert sum(c.kind == 'bolt' for c in connections) == 12
    assert len(model.panel_connections()) == 66
    assert model.panel_edge_cutouts() == {}
    for c in connections:
        if c.name.startswith('rail_'):
            front = '_front_' in c.name
            assert abs(model.bolt_interface_point(c).x) == pytest.approx(1219.2 if front else 1257.3)
            assert c.grip == pytest.approx(76.2 if front else 88.9)
            assert c.length == pytest.approx(101.6 if front else 114.3)
            assert c.start.x*c.direction.x > 0
            if not front:
                assert model.EXPECTED_BEARING_LENGTHS_MM[c.name][c.members[1]] == pytest.approx(50.8)
        if c.name.startswith('round_kicker_') and '_rim_' in c.name:
            assert abs(c.start.x) == pytest.approx(1200.15)
            assert c.start.z in (60., 192.)


@pytest.mark.parametrize('side', ['left', 'right'])
def test_recess_leaves_two_inch_leg_and_two_mm_shoulder_gap(side):
    x0 = -1308.1 if side == 'left' else 1219.2
    stock = cq.Solid.makeBox(88.9, 100., 220., cq.Vector(x0, 1500., 0.))
    removed = stock.intersect(model.recess_cutter(side))
    retained = stock.cut(model.recess_cutter(side))
    assert removed.Volume() == pytest.approx(38.1*100.*141.7)
    foot_slice = retained.intersect(cq.Solid.makeBox(90., 100., 10., cq.Vector(x0-.1, 1500., 0.)))
    assert foot_slice.BoundingBox().xlen == pytest.approx(50.8)
    assert model.NOTCH_TOP_Z_MM-model.RAIL_TOP_Z == pytest.approx(2.)
    assert len(retained.Solids()) == 1
    metadata = model.recess_metadata()['lumber_leg_'+side]
    assert metadata['transverse_clearance_mm'] == 0.
    assert metadata['shoulder_bearing_credited'] is False


def test_rear_bolt_threads_allow_full_nut_seating_and_wood_bearing():
    for bolt in model.connections():
        if not bolt.name.startswith('rail_rear_bolt_'):
            continue
        dimensions = model.bolt_dimensions(bolt)
        nut_start = bolt.grip+2*dimensions['washer_thickness_mm']
        nut_end = nut_start+dimensions['nut_height_mm']
        assert dimensions['thread_start_mm'] <= nut_start
        assert bolt.length-nut_end >= 2*25.4/16
        required_body = bolt.grip+2.6416-model.REMAINING_LEG_THICKNESS_MM/4
        assert dimensions['thread_start_mm'] >= required_body
        assert dimensions['thread_start_mm'] == pytest.approx(88.9)
        assert nut_start == pytest.approx(92.964)
        # The rejected 5-inch bolt with the same thread length cannot seat.
        assert 127.-dimensions['thread_length_mm'] > nut_start


def test_native_side_profiles_use_physical_vertices_not_padded_bounds():
    for row in model.floor_recess_geometry().values():
        assert len(row['side_profile_yz_mm']) >= 4
        assert min(z for y,z in row['side_profile_yz_mm']) == pytest.approx(0.)
        assert row['raw_bounds_xyz_mm'][0][1]-row['raw_bounds_xyz_mm'][0][0] == pytest.approx(88.9)
