"""Exact saved layout and complete two-bolt trial inventory."""
import json
from pathlib import Path

import pytest

from mini_moonboard import compact_two_frame as model


def test_layout_exactly_matches_selected_saved_screen():
    screen = json.loads(Path(model.SCREEN_SOURCE).read_text())
    trial = next(r for r in screen['results'] if r['bolt_count_per_leg'] == 2 and r['diameter_in'] == .75)
    centre = model.previous.pivot_reference.bolt_points()[0]
    assert trial['best']['ratio'] > 1
    for point, saved in zip(model.bolt_points(), trial['best']['points_relative_depth_center'], strict=True):
        assert (point-centre).toTuple() == pytest.approx(saved)
    assert (model.bolt_points()[1]-model.bolt_points()[0]).Length == pytest.approx(77.)


def test_four_complete_new_bolts_and_other_connections_preserved():
    old = {c.name:c for c in model.previous.connections() if not c.name.startswith('lumber_leg_bolt_')}
    new = {c.name:c for c in model.connections() if not isinstance(c, model.TwoLegBolt)}
    assert new == old
    bolts = [c for c in model.connections() if isinstance(c, model.TwoLegBolt)]
    assert len(bolts) == 4
    for c in bolts:
        assert c.diameter == 19.05 and c.length == 228.6
        assert abs(model.bolt_interface_point(c).x) == pytest.approx(model.b.HALF)
    assert len(bolts[0].components()) == 5
    assert len(model.panel_connections()) == 66
    assert model.previous.KEY == 'compact-thick-development'
    assert model.KEY == 'compact-two-development'
