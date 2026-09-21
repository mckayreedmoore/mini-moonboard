"""The bounded outer-base revision reports measured geometry and no release."""

import pytest

from scripts import simple_pb05_outer_base_revision as trial


@pytest.fixture(scope="module")
def result():
    return trial.screen()


def test_source_and_retained_inventory(result):
    assert result["source_id"] == trial.pb05.SOURCE_ID
    assert result["source_preserved"]
    assert result["inventory"] == {
        "original_frame_bolts": 12,
        "panel_kicker_axes": 66,
        "other_legacy_sds_axes": 72,
        "pb05_blocks": 8,
        "candidate_cleats": 2,
        "candidate_bolts": 4,
    }


def test_exact_fit_and_no_release(result):
    assert set(result["stations"]) == set(trial.TARGET_STATIONS)
    assert all(not hits for hits in result["collisions"].values())
    assert result["gates"] == {
        "protected_cad_clear": True,
        "nominal_washer_seats": True,
        "conditional_4d_edge_target": False,
    }
    assert result["minimum_cleat_edge_margin_mm"] == pytest.approx(12.7)
    assert result["decision"] == "REVISE"
    assert not result["strength_checked"]
    assert not result["drilling_released"]
    assert not result["fabrication_released"]


def test_source_identity_guard():
    class WrongSource:
        KEY = "wrong"

    with pytest.raises(ValueError, match="source identity"):
        trial.screen(module=WrongSource())
