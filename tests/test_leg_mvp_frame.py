"""Fast isolated candidate checks; full CAD fit runs explicitly in the review."""
import pytest

from mini_moonboard import leg_mvp_frame as model


def test_pattern_has_nine_axes_and_preserves_current_datum():
    centre, _, along, across, rim = model.axes()
    points = model.bolt_points()
    assert len(points) == 9
    assert ((sum(points, model.cq.Vector())/9)-(centre+along*50)).Length < 1.e-8
    assert model.b.V1_KICKER_HEIGHT_MM == 277
    assert model.DEPTH == 234.95
    assert model.TOP_EXTENSION == 260
    assert (points[1]-points[0]).toTuple() == pytest.approx((rim*75).toTuple())
    assert (points[3]-points[0]).toTuple() == pytest.approx((along*65).toTuple())
    plate_half = model.catalog.PLATE_SIDE/2*(abs(rim.dot(across))+abs(model.b.normal().dot(across)))
    for row in model.drilling_records():
        if row['member'].startswith('lumber_leg_'):
            assert plate_half < row['depth_coordinate_mm'] < model.DEPTH-plate_half
            assert model.TOP_EXTENSION-row['grain_station_mm'] >= 7*12.7+10


def test_complete_catalog_stacks_and_unchanged_other_connections():
    old = {c.name: c for c in model.previous.connections() if not c.name.startswith('lumber_leg_bolt_')}
    new = {c.name: c for c in model.connections() if not isinstance(c, model.LegMvpBolt)}
    assert new == old
    bolts = [c for c in model.connections() if isinstance(c, model.LegMvpBolt)]
    assert len(bolts) == 18
    assert all(c.length == 127 and c.diameter == 12.7 and c.grip == 76.2 for c in bolts)
    assert len(bolts[0].components()) == 8
    for bolt in bolts:
        assert abs(model.bolt_interface_point(bolt).x) == pytest.approx(model.b.HALF)
    assert model.catalog.dimensional_window()['dimensional_pass']


def test_plate_axes_have_positive_separation():
    _, _, along, _, rim = model.axes()
    # Both stacks use rim-aligned BP1/2 plates, not the historical leg alignment.
    gap = model.PATTERN_ALONG_LEG*(1-along.dot(rim)**2)**.5-model.catalog.PLATE_SIDE
    assert gap > 2.49
