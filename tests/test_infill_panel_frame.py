"""Uniform infill retains old axes and stops at each panel's existing endpoints."""
import itertools
from collections import defaultdict

import pytest

from mini_moonboard import infill_panel_frame as model


def groups(connections):
    result = defaultdict(list)
    for c in connections:
        if isinstance(c, model.timber.PanelScrew) and c.members[0].startswith('main_') and c.members[1].startswith('base_principal_'):
            result[c.members].append(c)
    return result


def test_original_connections_and_raw_geometry_are_retained():
    original, revised = model.previous.connections(), model.connections()
    assert all(old is revised[index] for index, old in enumerate(original))
    assert model.wood_parts is model.previous.wood_parts
    assert model.stations is model.previous.stations
    assert len({c.name for c in revised}) == len(revised)
    assert sum(isinstance(c, model.timber.PanelScrew) for c in revised) == 151
    assert sum(c.name.startswith('infill_') for c in revised) == 71


def test_every_panel_receiver_interval_is_infilled_without_extending_endpoints():
    tangent = (model.b.point(0., 1., 0.)-model.b.point(0., 0., 0.)).normalized()
    before, after = groups(model.previous.connections()), groups(model.connections())
    assert before.keys() == after.keys() and len(after) == 12
    for members, connections in after.items():
        old = sorted(c.start.dot(tangent) for c in before[members])
        new = sorted(c.start.dot(tangent) for c in connections)
        assert new[0] == pytest.approx(old[0]) and new[-1] == pytest.approx(old[-1])
        assert max(end-start for start, end in itertools.pairwise(new)) <= model.MAX_INTERVAL_MM+1e-8
        assert min(end-start for start, end in itertools.pairwise(new)) >= 44.45
        for c in connections:
            assert c.start.x == before[members][0].start.x
            assert c.direction.toTuple() == before[members][0].direction.toTuple()
            assert c.length == 50.8 and c.diameter == 4.1402
