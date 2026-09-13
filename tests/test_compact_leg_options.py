"""Lightweight physical-datum contracts for the bounded leg-angle trials."""
from pathlib import Path

import pytest

from mini_moonboard import compact_leg_options as model


def test_candidate_identity_cannot_hide_different_geometry():
    assert len({c.KEY for c in model.OPTIONS}) == 5
    for c in model.OPTIONS:
        assert Path(c.__file__).name == 'compact_leg_options.py'
        with pytest.raises(ValueError, match='exact bounded parameters'):
            model.Candidate(c.label, c.attachment_shift_s_mm+1., c.foot_shift_y_mm)


def test_real_leg_axes_preserve_floor_and_original_depth_offset():
    control = model.option('control')
    _, foot0, grain0, _, _, offset0, top0 = control.leg_datums()
    assert grain0.toTuple() == pytest.approx(model.previous.axes()[2].toTuple())
    assert foot0.y == pytest.approx(1418.009014811115)
    assert top0 > 175.
    for c in model.OPTIONS:
        centre, foot, grain, normal, top, offset, top_extension = c.leg_datums()
        assert foot.z == pytest.approx(0.)
        assert foot.y-foot0.y == pytest.approx(c.foot_shift_y_mm)
        assert (centre-foot).dot(normal) == pytest.approx(offset0, abs=1e-8)
        assert (top-foot).dot(normal) == pytest.approx(0., abs=1e-8)
        assert offset == pytest.approx(offset0)
        assert top_extension == pytest.approx(top0)
        assert grain.Length == pytest.approx(1.)
    assert model.option('upper150').axes()[2].toTuple() != pytest.approx(grain0.toTuple())


def test_only_actual_leg_bolt_axes_move_with_attachment_station():
    old = {c.name:c for c in model.previous.connections()}
    rim = model.previous.axes()[4]
    for option in model.OPTIONS:
        assert len(option.bolt_points()) == 2
        for c in option.connections():
            if c.name.startswith('lumber_leg_bolt_'):
                assert (c.start-old[c.name].start).toTuple() == pytest.approx((rim*option.attachment_shift_s_mm).toTuple())
            else:
                assert c == old[c.name]
