"""PB05 native geometry identity and unsolved preparation."""

import pytest

from fea.floor_flush_run import face_contacts
from scripts import simple_pb04_native as pb04
from scripts import simple_pb05_narrow_outer_screen as detached
from scripts.simple_center_pb02_native import PB02Native, prepare_case
from scripts.simple_pb05_native import (
    BLOCK_X_MM,
    OUTER_STATIONS,
    RAIL_X_OFFSETS_MM,
    SOURCE_ID,
    PB05Native,
    screen,
)


@pytest.fixture(scope="module")
def module():
    return PB05Native()


@pytest.fixture(scope="module")
def parent():
    return pb04.PB04Native()


def _axis(row):
    return (
        row.name,
        row.start.toTuple(),
        row.direction.toTuple(),
        row.length,
        row.diameter,
        row.members,
        row.kind,
        row.grip,
    )


def test_pb05_blocks_and_fixed_axes_are_source_distinct(module, parent):
    assert OUTER_STATIONS == detached.OUTER_STATIONS
    assert BLOCK_X_MM == detached.BLOCK_X_MM
    assert RAIL_X_OFFSETS_MM == detached.RAIL_X_OFFSETS_MM
    parts = {part.name: part.shape for part in module.wood_parts()}
    parent_parts = {part.name: part.shape for part in parent.wood_parts()}
    geometry = module.pb03_geometries()
    for station, row in geometry.items():
        actual = parts[row.block_name]
        assert actual.Volume() == pytest.approx(row.block.Volume(), abs=1e-5)
        if station in module.OUTER_STATIONS:
            assert row.report["block_dimensions_mm"] == pytest.approx(
                [95.25, 57.15, 300]
            )
            assert actual.BoundingBox().xlen == pytest.approx(95.25)
            assert actual.Volume() > 0
            assert actual.BoundingBox().xlen != pytest.approx(
                parent_parts[row.block_name].BoundingBox().xlen
            )
        else:
            assert actual.distance(parent_parts[row.block_name]) <= 1e-8
            assert [_axis(bolt) for bolt in row.bolts] == [
                _axis(bolt) for bolt in parent.pb03_geometries()[station].bolts
            ]
    assert len(module.legacy_proxy_stations()) == 14
    assert len(module.panel_connections()) == 66
    assert [_axis(row) for row in module.panel_connections()] == [
        _axis(row) for row in PB02Native().panel_connections()
    ]
    assert sum(row.name.startswith("clip_") for row in module.connections()) == 84
    assert sum(row.name.startswith("pb03_") for row in module.connections()) == 32
    assert (
        sum(
            row.kind == "bolt" and not row.name.startswith("pb03_")
            for row in module.connections()
        )
        == 12
    )


def test_pb05_fingerprint_and_no_release(module, parent):
    result = screen(module)
    assert module.KEY == result["source_id"] == SOURCE_ID
    assert result["source_id"] != pb04.SOURCE_ID
    assert result["source_fingerprint_sha256"] != pb04._source_fingerprint(parent)
    assert len(result["source_fingerprint_sha256"]) == 64
    assert len(result["block_axis_fingerprint_sha256"]) == 64
    assert result["inventory"] == {
        "outer_blocks": 6,
        "unchanged_center_blocks": 2,
        "outer_pockets": 0,
        "panel_kicker_axes": 66,
        "frame_bolt_axes": 12,
        "legacy_sds_duties": 14,
        "legacy_sds_axes": 84,
        "new_bolt_axes": 32,
    }
    assert result["native_solve"] is False
    assert result["force_transfer"] is False
    assert result["qualified_for_design"] is False
    assert result["acceptance"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False


def test_pb05_preparation_metadata_stays_unsolved(module):
    _, metadata = prepare_case(
        "a12-forward",
        bolt_axial_n_per_mm=700.0,
        bolt_lateral_n_per_mm=1200.0,
        face_normal_total_n_per_mm=2400.0,
        module=module,
        expected_candidate=SOURCE_ID,
        member_contacts=face_contacts(PB02Native()),
        expected_legacy_station_count=14,
        post_prepare=module.validate_prepared_case,
    )
    assert metadata["pb05_candidate"] == SOURCE_ID
    assert metadata["pb05_preparation_validated"] is True
    for field in (
        "solved",
        "force_transfer",
        "qualified_for_design",
        "acceptance",
        "drilling_released",
        "fabrication_released",
        "structural_released",
    ):
        assert metadata[field] is False
