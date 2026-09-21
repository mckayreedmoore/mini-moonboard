"""Detached simultaneous narrow outer station regression."""

import pytest

from scripts import simple_pb05_narrow_outer_screen as trial


def test_six_outer_screen_preserves_source_and_reports_each_station():
    original = (trial.lower.BLOCK_X_MM, trial.lower.RAIL_X_OFFSETS_MM)
    result = trial.screen()
    assert (trial.lower.BLOCK_X_MM, trial.lower.RAIL_X_OFFSETS_MM) == original
    assert set(result["stations"]) == set(trial.OUTER_STATIONS)
    assert result["inventory"] == {
        "outer_stations": 6,
        "unchanged_center_stations": 2,
        "outer_bolt_axes": 24,
        "fixed_panel_kicker_axes": 66,
        "original_frame_bolt_axes": 12,
        "legacy_duties": 14,
    }
    assert result["counterbores"] == 0
    assert "PB02" in result["fixed_axis_source"]
    assert "PB04" in result["outer_geometry_source"]
    for row in result["stations"].values():
        assert row["block_dimensions_mm"] == pytest.approx([95.25, 57.15, 300])
        assert row["rail_x_offsets_from_butt_mm"] == pytest.approx([25, 70])
        assert row["upright_grip_mm"] == pytest.approx(184.15)
        assert row["rail_grip_mm"] == pytest.approx(95.25)
        assert row["contact_area_change_mm2"].keys() == {"rail", "upright"}
        assert set(row["end_edge_gates"]) == {"grain_end", "rail_x_edge"}
        assert not any(row["obstructions_mm3"].values())
        assert row["decision"] == "PASS_GEOMETRY_ONLY"
        assert all(row["gates"].values())
    assert result["decision"] == "ADVANCE_GEOMETRY_ONLY"
    assert result["force_transfer"] is False
    assert result["native_solve"] is False
