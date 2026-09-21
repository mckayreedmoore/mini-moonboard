"""PB03 native adapter composes the eight converted rail stations."""

import pytest

from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT
from scripts.simple_center_pb02_native import PB02Native
from scripts.simple_pb03_bottom_outer_pair import (
    BLOCK_NAMES as BOTTOM_BLOCK_NAMES,
)
from scripts.simple_pb03_bottom_outer_pair import (
    TARGET_STATIONS as BOTTOM_TARGET_STATIONS,
)
from scripts.simple_pb03_lower_center_pair import (
    ALL_BLOCK_NAMES as LOWER_BLOCK_NAMES,
)
from scripts.simple_pb03_lower_center_pair import (
    ALL_TARGET_STATIONS as LOWER_TARGET_STATIONS,
)
from scripts.simple_pb03_native import (
    BLOCK_NAMES,
    REPLACED_STATIONS,
    SOURCE_ID,
    PB03Native,
    screen,
)
from scripts.simple_pb03_upper_outer_pair import (
    BLOCK_NAMES as UPPER_BLOCK_NAMES,
)
from scripts.simple_pb03_upper_outer_pair import (
    TARGET_STATIONS as UPPER_TARGET_STATIONS,
)


@pytest.fixture(scope="module")
def module():
    return PB03Native()


def test_native_replaces_exactly_eight_angles_with_eight_blocks(module):
    prior = PB02Native()
    before = {part.name: part for part in prior.uncut_wood_parts()}
    after = {part.name: part for part in module.uncut_wood_parts()}

    assert len(before) == 31
    assert len(after) == 39
    assert set(BLOCK_NAMES.values()) == (
        set(LOWER_BLOCK_NAMES.values())
        | set(UPPER_BLOCK_NAMES.values())
        | set(BOTTOM_BLOCK_NAMES.values())
    )
    assert set(BLOCK_NAMES.values()) <= set(after)
    for name, part in before.items():
        assert after[name].shape.Volume() == pytest.approx(
            part.shape.Volume(), abs=1e-3
        )
        assert after[name].shape.Center().toTuple() == pytest.approx(
            part.shape.Center().toTuple()
        )

    finished = {part.name for part in module.parts()}
    assert not (set(REPLACED_STATIONS) & finished)
    assert set(BLOCK_NAMES.values()) <= finished


def test_native_removes_forty_eight_sds_axes_and_adds_thirty_two_bolts(module):
    connections = module.connections()
    stations = {row[0] for row in module.stations()}
    pb03_bolts = [row for row in connections if row.name.startswith("pb03_")]

    assert len(stations) == 14
    assert not (stations & set(REPLACED_STATIONS))
    assert sum(row.name.startswith("clip_") for row in connections) == 84
    assert not any(
        row.name.startswith(tuple(f"{name}_" for name in REPLACED_STATIONS))
        for row in connections
    )
    assert len(pb03_bolts) == 32
    assert len({row.name for row in pb03_bolts}) == 32
    assert sum(row.kind == "bolt" for row in connections) == 44
    assert len(connections) == 194
    assert all(len(row.components()) == 5 for row in pb03_bolts)


def test_native_exposes_one_authenticated_eight_station_geometry_map(module):
    geometries = module.pb03_geometries()

    assert tuple(geometries) == REPLACED_STATIONS
    assert set(REPLACED_STATIONS) == (
        set(LOWER_TARGET_STATIONS)
        | set(UPPER_TARGET_STATIONS)
        | set(BOTTOM_TARGET_STATIONS)
    )
    assert {geometry.block_name for geometry in geometries.values()} == set(
        BLOCK_NAMES.values()
    )
    geometries.clear()
    assert tuple(module.pb03_geometries()) == REPLACED_STATIONS


def test_native_block_part_dimensions_follow_each_geometry_record(module):
    geometries = module.pb03_geometries()
    blocks = {
        part.name: part
        for part in module.uncut_wood_parts()
        if part.name in BLOCK_NAMES.values()
    }

    for geometry in geometries.values():
        x, thickness, length = geometry.report["block_dimensions_mm"]
        assert blocks[geometry.block_name].blank == (length, x, thickness)


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
    assert module.KEY == SOURCE_ID


def test_native_fails_closed_and_never_releases(module):
    result = screen(module)

    assert result["pb02_source_fingerprint"] == ACTIVE_FINGERPRINT
    assert result["pb03_source_id"] == SOURCE_ID
    assert result["replaced_legacy_stations"] == list(REPLACED_STATIONS)
    assert result["legacy_proxy_stations"] == 14
    assert result["legacy_sds_axes"] == 84
    assert result["new_timber_blocks"] == 8
    assert result["new_through_bolt_stacks"] == 32
    assert result["total_connections"] == 194
    assert result["total_bolt_connections"] == 44
    assert result["fixed_panel_kicker_axes"] == 66
    assert result["lower_service_geometry_gates_pass"] is True
    assert result["upper_outer_geometry_gates_pass"] is True
    assert result["bottom_outer_geometry_gates_pass"] is True
    assert result["cross_family_collision_gates_pass"] is True
    assert result["geometry_gates_pass"] is True
    assert result["exact_retail_hardware_selected"] is False
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
