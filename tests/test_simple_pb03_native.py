"""PB03 native adapter changes only the first lower-center pair."""

import pytest

from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT
from scripts.simple_center_pb02_native import PB02Native
from scripts.simple_pb03_lower_center_pair import BLOCK_NAMES, TARGET_STATIONS
from scripts.simple_pb03_native import PB03Native, screen


@pytest.fixture(scope="module")
def module():
    return PB03Native()


def test_native_replaces_exactly_two_angles_with_two_blocks(module):
    prior = PB02Native()
    before = {part.name: part for part in prior.uncut_wood_parts()}
    after = {part.name: part for part in module.uncut_wood_parts()}

    assert len(before) == 31
    assert len(after) == 33
    assert set(BLOCK_NAMES.values()) <= set(after)
    for name, part in before.items():
        assert after[name].shape.Volume() == pytest.approx(
            part.shape.Volume(), abs=1e-3
        )
        assert after[name].shape.Center().toTuple() == pytest.approx(
            part.shape.Center().toTuple()
        )

    finished = {part.name for part in module.parts()}
    assert not (set(TARGET_STATIONS) & finished)
    assert set(BLOCK_NAMES.values()) <= finished


def test_native_removes_twelve_sds_axes_and_adds_eight_bolts(module):
    connections = module.connections()
    stations = {row[0] for row in module.stations()}
    pb03_bolts = [row for row in connections if row.name.startswith("pb03_")]

    assert len(stations) == 20
    assert not (stations & set(TARGET_STATIONS))
    assert sum(row.name.startswith("clip_") for row in connections) == 120
    assert not any(
        row.name.startswith(tuple(f"{name}_" for name in TARGET_STATIONS))
        for row in connections
    )
    assert len(pb03_bolts) == 8
    assert sum(row.kind == "bolt" for row in connections) == 20
    assert len(connections) == 206
    assert all(len(row.components()) == 5 for row in pb03_bolts)


def test_native_preserves_all_fixed_axes_and_pb02_geometry(module):
    prior = PB02Native()
    before = {row.name: row for row in prior.panel_connections()}
    after = {row.name: row for row in module.panel_connections()}

    assert len(before) == len(after) == 66
    for name, old in before.items():
        new = after[name]
        assert new.start == old.start
        assert new.direction == old.direction
        assert new.length == old.length
        assert new.diameter == old.diameter
        assert new.members == old.members
    assert module.ACTIVE_FINGERPRINT == ACTIVE_FINGERPRINT


def test_native_fails_closed_and_never_releases(module):
    result = screen(module)

    assert result["pb02_source_fingerprint"] == ACTIVE_FINGERPRINT
    assert result["legacy_proxy_stations"] == 20
    assert result["legacy_sds_axes"] == 120
    assert result["new_timber_blocks"] == 2
    assert result["new_through_bolt_stacks"] == 8
    assert result["fixed_panel_kicker_axes"] == 66
    assert result["geometry_gates_pass"] is True
    assert result["exact_retail_hardware_selected"] is False
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
