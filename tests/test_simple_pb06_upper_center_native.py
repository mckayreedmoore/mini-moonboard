"""PB06 upper-center replacement is source-bound geometry preparation only."""

import pytest

from fea.floor_flush_run import face_contacts
from scripts import simple_pb05_upper_center_detached as trial
from scripts import simple_pb06_upper_center_native as pb06
from scripts.simple_center_pb02_native import PB02Native, prepare_case
from scripts.simple_pb05_native import PB05Native


@pytest.fixture(scope="module")
def candidates():
    return PB05Native(), pb06.PB06Native()


def test_replacement_and_fingerprint(candidates):
    source, candidate = candidates
    result = pb06.screen(candidate)
    assert result["source_id"] == pb06.SOURCE_ID != source.KEY
    assert len(result["source_fingerprint_sha256"]) == 64
    assert (
        result["source_fingerprint_sha256"] != result["pb05_source_fingerprint_sha256"]
    )
    assert result["inventory"] == {
        "blocks": 10,
        "original_frame_bolt_axes": 12,
        "panel_kicker_axes": 66,
        "legacy_sds_duties": 12,
        "legacy_sds_axes": 72,
        "pb05_bolt_axes": 32,
        "upper_center_bolt_axes": 8,
    }
    assert len(candidate.connections()) == len(source.connections()) - 12 + 8
    assert set(source.legacy_proxy_stations()) - set(
        candidate.legacy_proxy_stations()
    ) == set(pb06.TARGET_STATIONS)
    assert result["original_target_sds_authenticated"] is True
    assert all(
        result[field] is False
        for field in (
            "native_solve",
            "force_transfer",
            "acceptance",
            "drilling_released",
            "fabrication_released",
            "structural_released",
        )
    )


def test_actual_solids_match_detached_trial(candidates):
    source, candidate = candidates
    pair, reference = trial.build_inputs()
    detached = trial.screen(pair=pair, module=reference)
    assert detached["geometry_decision"] == "ADVANCE_GEOMETRY_ONLY"
    actual = {part.name: part.shape for part in candidate.wood_parts()}
    source_parts = {part.name: part.shape for part in source.wood_parts()}
    for name, shape in source_parts.items():
        assert trial._same_shape(actual[name], shape)
    for row in pair.values():
        assert trial._same_shape(actual[row.block_name], row.block)
        assert [
            pb06._axis(bolt) for bolt in candidate.pb03_geometries()[row.station].bolts
        ] == [pb06._axis(bolt) for bolt in row.bolts]


def test_unsolved_preparation(candidates):
    _, candidate = candidates
    _, metadata = prepare_case(
        "a12-forward",
        bolt_axial_n_per_mm=700.0,
        bolt_lateral_n_per_mm=1200.0,
        face_normal_total_n_per_mm=2400.0,
        module=candidate,
        expected_candidate=pb06.SOURCE_ID,
        member_contacts=face_contacts(PB02Native()),
        expected_legacy_station_count=12,
        post_prepare=candidate.validate_prepared_case,
    )
    assert metadata["pb06_preparation_validated"] is True
    assert len(metadata["legacy_proxy_stations"]) == 12
    assert all(
        metadata[field] is False
        for field in (
            "solved",
            "force_transfer",
            "qualified_for_design",
            "acceptance",
            "drilling_released",
            "fabrication_released",
            "structural_released",
        )
    )
