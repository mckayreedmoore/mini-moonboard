"""Exact body preservation and changed stock-normal layout of the final trial."""
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard import compact_three_leg_225_refined as model


def test_refinement_preserves_body_datums_and_changes_only_bolt_layout():
    candidate = model.CANDIDATE
    old = model.original.option('upper225')
    assert candidate.KEY != old.KEY
    assert Path(candidate.__file__).name == 'compact_three_leg_225_refined.py'
    for actual,expected in zip(candidate.leg_datums(),old.leg_datums(),strict=True):
        assert (actual.toTuple() if isinstance(actual,cq.Vector) else actual) == pytest.approx(expected.toTuple() if isinstance(expected,cq.Vector) else expected)
    _,foot,leg,*_ = candidate.leg_datums()
    rim = candidate.axes()[4]
    mean = sum(candidate.bolt_points(),cq.Vector())/3
    assert (mean-foot).dot(cq.Vector(0.,leg.z,-leg.y)) == pytest.approx(10.)
    assert (mean-candidate.b.point(0.,0.,candidate.DEPTH/2)).dot(cq.Vector(0.,rim.z,-rim.y)) == pytest.approx(25.)
    assert candidate.parameters['layout_parameters'] == [76.,68.,3,10.,25.]
    with pytest.raises(ValueError,match='unchanged upper225'):
        model.Candidate('upper300',300.,225.)
