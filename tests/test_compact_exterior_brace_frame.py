"""Connection topology and clearance intent for the exterior-only knee trial."""
from itertools import pairwise

import pytest

from mini_moonboard import compact_base_finish as selected
from mini_moonboard import compact_exterior_brace_frame as model


def test_exterior_brace_preserves_selected_nonbrace_connections():
    before = {c.name: c for c in selected.connections()}
    after = {c.name: c for c in model.connections()}
    assert before.keys() == after.keys()
    assert sum(c.kind == 'bolt' for c in after.values()) == 20
    for name, c in after.items():
        if name.startswith(('knee_bolt_', 'knee_splice_bolt_')):
            continue
        original = before[name]
        assert c.start.toTuple() == original.start.toTuple()
        assert c.direction.toTuple() == original.direction.toTuple()
        assert c.members == original.members
        assert c.length == original.length
    assert all(after[name].start.z == 60. for name in selected.MOVED_NAMES)


def test_exterior_brace_interfaces_are_contiguous_and_tips_outward():
    for c in model.connections():
        if c.kind != 'bolt':
            continue
        assert c.start.x*c.direction.x > 0
        if not c.name.startswith(('knee_bolt_', 'knee_splice_bolt_')):
            continue
        expected_interface = model.b.HALF if '_rim_' in c.name else model.b.HALF+88.9
        assert abs(model.bolt_interface_point(c).x) == pytest.approx(expected_interface)
        hardware = model.bolt_dimensions(c)
        first_face = c.start+c.direction*hardware['washer_thickness_mm']
        assert abs(model.bolt_interface_point(c).x-first_face.x) == pytest.approx(88.9)
        outer_face = first_face+c.direction*c.grip
        expected_outer = model.b.HALF+88.9 if '_rim_' in c.name else model.b.HALF+127.
        assert abs(outer_face.x) == pytest.approx(expected_outer)
        assert c.length > c.grip+2*hardware['washer_thickness_mm']+hardware['nut_height_mm']
    contacts = model.overlap_contact_datums()
    assert len(contacts) == 18
    assert all(abs(row['point_xyz_mm'][0]) == pytest.approx(model.b.HALF+88.9) for row in contacts)
    assert all(row['tributary_area_mm2'] > 0 for row in contacts)


def test_exterior_splice_spacing_and_loaded_end_reserves():
    rim, _, grain, length = model.knee_datums()
    stations = model.splice_stations()
    assert len(stations) == 4
    assert [(b-a) for a, b in pairwise(stations)] == pytest.approx([51.]*3)
    assert min(b-a for a, b in pairwise(stations)) > 5*9.525+3.
    lap_start, lap_end = 120., length-180.
    assert (stations[0]+stations[-1])/2 == pytest.approx((lap_start+lap_end)/2)
    assert min(stations[0]-lap_start, lap_end-stations[-1]) > 7*9.525+3.
    for c in model.connections():
        if not c.name.startswith('knee_splice_bolt_'):
            continue
        point = model.bolt_interface_point(c)
        station = (point-rim).dot(grain)
        expected = stations[int(c.name.rsplit('_', 1)[1])-1]
        assert station == pytest.approx(expected)
    for contact in model.overlap_contact_datums():
        xyz = contact['point_xyz_mm']
        station = sum((value-origin)*direction for value, origin, direction in
                      zip(xyz, rim.toTuple(), grain.toTuple()))
        assert lap_start < station < lap_end
