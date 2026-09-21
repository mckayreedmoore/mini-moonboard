"""A small detached coordinate trial must not become a PB05 release."""

import pytest

from scripts.simple_pb05_outer_rail_revision import _shift_signed, screen


def test_signed_translation_preserves_loaded_and_unloaded_sides():
    old = {
        "grain_end": {
            "applicable": True,
            "sign": "negative",
            "loaded_distance_mm": 25.0,
            "unloaded_distance_mm": 80.0,
            "loaded_required_mm": 25.4,
            "unloaded_required_mm": 20.0,
            "passes": False,
        },
        "cross_grain_edge": {"applicable": False, "passes": True},
    }
    direction = {"grain_axis_xyz": (1, 0, 0), "edge_axis_xyz": (0, 1, 0)}
    moved = _shift_signed(old, direction, (1, 0, 0))
    assert moved["grain_end"]["loaded_distance_mm"] == 26.0
    assert moved["grain_end"]["loaded_margin_mm"] == pytest.approx(0.6)
    assert moved["passes"] is True


@pytest.fixture(scope="module")
def result():
    return screen()


def test_six_outer_rail_failures_have_detached_geometry_trial(result):
    assert result["inventory"]["fixed_panel_kicker_axes"] == 66
    assert result["inventory"]["original_frame_bolt_axes"] == 12
    assert result["inventory"]["legacy_duties"] == 14
    assert len(result["signed_end_edge"]) == 12
    assert (
        sum(not row["original_passes"] for row in result["signed_end_edge"].values())
        == 6
    )
    assert all(row["trial_passes"] for row in result["signed_end_edge"].values())
    assert result["geometry_pass"] is True
    assert result["decision"] == "ADVANCE_TO_NEW_NATIVE_SOLVE"
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
