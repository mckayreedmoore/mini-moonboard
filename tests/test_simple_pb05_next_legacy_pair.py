"""Detached outer-base cleats remain a bounded PB05 development screen."""

import pytest

from scripts import simple_pb05_next_legacy_pair as trial


@pytest.fixture(scope="module")
def result():
    return trial.screen()


def test_source_inventory_and_pair(result):
    assert result["source_id"] == trial.pb05.SOURCE_ID
    assert result["legacy_stations_exact"] == list(trial.EXPECTED_LEGACY)
    assert result["candidate_stations"] == list(trial.TARGET_STATIONS)
    assert all(
        name in result["legacy_stations_exact"] for name in trial.TARGET_STATIONS
    )
    assert result["inventory"] == {
        "pb05_blocks": 8,
        "original_frame_bolts": 12,
        "panel_kicker_axes": 66,
        "target_legacy_sds_axes_retained": 12,
        "other_legacy_sds_axes_retained": 72,
        "candidate_blocks": 2,
        "candidate_bolts": 8,
    }


def test_bounded_geometry_and_no_release(result):
    assert result["source_preserved"]
    assert all(
        row["full_section_mm"] == [38.1, 139.7] for row in result["stations"].values()
    )
    assert set(result["collision_hits_mm3"]) >= {
        "pb05_blocks",
        "frame_bolt_axes",
        "panel_kicker_axes",
        "panels",
        "other_legacy_axes",
        "other_legacy_angles",
        "unrelated_timber",
    }
    hits = result["collision_hits_mm3"]
    for station, side in zip(trial.TARGET_STATIONS, ("left", "right"), strict=True):
        assert any(
            key.startswith(f"block/{station}|")
            and key.endswith(f"pb03_bottom_outer_{side}_block")
            for key in hits["pb05_blocks"]
        )
        assert any(
            key.startswith(f"block/{station}|")
            and key.endswith(f"base_rail_bottom_{side}")
            for key in hits["unrelated_timber"]
        )
        assert any(
            key.startswith(f"tool/{station}/")
            and key.endswith(f"clip_timber_header_outer_{side}")
            for key in hits["other_legacy_angles"]
        )
    assert hits["frame_bolt_axes"] == {}
    assert hits["panel_kicker_axes"] == {}
    assert hits["panels"] == {}
    assert result["decision"] == "REVISE"
    assert result["native_source_changed"] is False
    assert result["strength_checked"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False


def test_identity_guard():
    class WrongSource:
        KEY = "wrong"

    with pytest.raises(ValueError, match="source identity"):
        trial.screen(module=WrongSource())
