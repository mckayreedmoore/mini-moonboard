"""Saved-layout fidelity and exact identities for two higher three-bolt trials."""
import json
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard import compact_three_leg_options as model


def test_layout_algorithm_reproduces_saved_upper150_triangle():
    screen = json.loads(Path(model.REFERENCE_SCREEN_SOURCE).read_text())
    trial = next(row for row in screen['results'] if row['bolt_count_per_leg'] == 3 and row['diameter_in'] == .5)
    saved = trial['best_hypothetical_fyb_90ksi']
    assert saved['parameters'] == [76,56,0]
    points = model.layout_offsets(cq.Vector(*screen['actual_grain_axes']['leg']), cq.Vector(*screen['actual_grain_axes']['rim']))
    for point, expected in zip(points,saved['points_relative_depth_center'],strict=True):
        assert point.toTuple() == pytest.approx(expected)


def test_two_exact_parameter_identities_and_real_leg_datums():
    assert set(model.PARAMETERS) == {'upper225','upper300'}
    assert len({c.KEY for c in model.OPTIONS}) == 2
    for c in model.OPTIONS:
        assert Path(c.__file__).name == 'compact_three_leg_options.py'
        with pytest.raises(ValueError,match='exact bounded parameters'):
            model.Candidate(c.label,c.attachment_shift_s_mm+1,c.foot_shift_y_mm)
        _centre,foot,grain,normal,top,_offset,extension = c.leg_datums()
        assert foot.z == pytest.approx(0.)
        assert foot.y == pytest.approx(1418.009014811115+c.foot_shift_y_mm)
        assert (top-foot).dot(normal) == pytest.approx(0.,abs=1e-8)
        assert extension > 175.
        points = c.bolt_points()
        mean = sum(points,cq.Vector())/3
        rim = c.axes()[4]
        rim_normal = cq.Vector(0.,rim.z,-rim.y)
        assert (mean-foot).dot(normal) == pytest.approx(model.LAYOUT_PARAMETERS[c.label][3],abs=1e-8)
        assert (mean-c.b.point(0,0,c.DEPTH/2)).dot(rim_normal) == pytest.approx(model.LAYOUT_PARAMETERS[c.label][4])
        assert grain.Length == pytest.approx(1.)


def test_three_complete_half_inch_stacks_and_other_axes_preserved():
    old = {c.name:c for c in model.previous.connections()}
    for candidate in model.OPTIONS:
        bolts = [c for c in candidate.connections() if c.kind == 'bolt']
        assert len(bolts) == 6
        assert all(c.diameter == 12.7 and c.length == 203.2 for c in bolts)
        assert len(bolts[0].components()) == 5
        for c in candidate.connections():
            if c.kind != 'bolt':
                assert c == old[c.name]


def test_new_axis_coordinates_match_bounded_eligible_layouts():
    saved = json.loads(Path(model.SCREEN_SOURCE).read_text())
    for candidate in model.OPTIONS:
        case = next(case for case in saved['cases'] if case['candidate'] == candidate.KEY)
        layout = case['results'][0]['best_hypothetical_fyb_90ksi']
        for point,expected in zip(candidate.bolt_points(),layout['left_axes_xyz_mm'],strict=True):
            assert (point.y,point.z) == pytest.approx(expected[1:])
