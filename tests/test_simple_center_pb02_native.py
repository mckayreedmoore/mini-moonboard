"""PB02 native adapter preserves kerf-right scope and canonical spring rows."""

import pytest

from scripts.simple_center_connected_kinematics import EDGES
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT
from scripts.simple_center_pb02_native import (
    NEW_MEMBERS,
    REMOVED_POST,
    REMOVED_STATIONS,
    RETARGETED_PANEL_CONNECTIONS,
    PB02Native,
    native_row_inventory,
    screen,
)


@pytest.fixture(scope="module")
def module():
    return PB02Native()


def test_candidate_overlays_only_pb02_members_on_kerf_right_frame(module):
    raw = {part.name: part for part in module.raw.uncut_wood_parts()}
    actual = {part.name: part for part in module.uncut_wood_parts()}

    assert len(actual) == 31
    assert REMOVED_POST not in actual
    assert set(NEW_MEMBERS) <= set(actual)
    for name in set(raw) - {REMOVED_POST}:
        before, after = raw[name].shape, actual[name].shape
        assert after.Volume() == pytest.approx(before.Volume(), abs=1e-3)
        assert after.Center().toTuple() == pytest.approx(before.Center().toTuple())
        assert (
            after.BoundingBox().xmin,
            after.BoundingBox().xmax,
        ) == pytest.approx((before.BoundingBox().xmin, before.BoundingBox().xmax))
    assert module.current_response_wood_parts() == module.uncut_wood_parts()


def test_only_displaced_clips_are_removed_and_panel_axes_are_frozen(module):
    connections = module.connections()
    panels = {row.name: row for row in module.panel_connections()}
    baseline = {row.name: row for row in module.raw.panel_connections()}
    stations = {row[0] for row in module.stations()}

    assert len(stations) == 22
    assert not (stations & REMOVED_STATIONS)
    assert sum(row.name.startswith("clip_") for row in connections) == 132
    assert sum(row.kind == "bolt" for row in connections) == 12
    assert len(panels) == len(baseline) == 66
    for name, before in baseline.items():
        after = panels[name]
        assert type(after) is type(before)
        assert after.name == before.name
        assert after.start == before.start
        assert after.direction == before.direction
        assert after.length == before.length
        assert after.diameter == before.diameter
        if name in RETARGETED_PANEL_CONNECTIONS:
            assert after.members == ("kicker_right", "backer")
        else:
            assert after.members == before.members


def test_native_rows_match_shared_connected_kinematics():
    rows = native_row_inventory()
    assert len(rows) == 58
    assert {row["edge"] for row in rows} == set(EDGES)
    assert sum(row["kind"] == "bolt_shear" for row in rows) == 20
    assert sum(row["kind"] == "bolt_tension" for row in rows) == 10
    assert sum(row["kind"] == "contact_compression" for row in rows) == 28
    for row in rows:
        assert {"first_part", "second_part", "point_mm", "direction"} <= set(row)


def test_screen_keeps_claim_boundary(module):
    result = screen()
    assert result["active_fingerprint"] == ACTIVE_FINGERPRINT
    assert result["moved_panel_kicker_axes"] == []
    assert set(result["changed_panel_kicker_receivers"]) == (
        RETARGETED_PANEL_CONNECTIONS
    )
    assert result["native_rows"] == {
        "bolt_shear": 20,
        "bolt_tension": 10,
        "contact_compression": 28,
    }
    assert result["developmental_only"] is True
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
