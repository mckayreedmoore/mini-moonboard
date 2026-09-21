"""A short-block comparison cannot silently change PB04 or release fabrication."""

import pytest

from scripts import simple_pb04_six_inch_block_screen as short


@pytest.fixture(scope="module")
def result():
    return short.screen()


def test_actual_pb04_stations_and_lengths(result):
    assert result["source_id"] == "pb04-upper-edge-plus-outer-counterbores-v1"
    assert result["upper_outer_offset_mm"] == pytest.approx(35.709)
    assert set(result["stations"]) == {
        "clip_horizontal_lower_left_2",
        "clip_horizontal_upper_left_1",
    }
    assert result["lengths_mm"] == [152.4, 300.0]
    assert result["fixed_panel_kicker_axes"] == 66


def test_rebuilds_geometry_without_shortening_bolt_grip(result):
    for station in result["stations"].values():
        small, current = station["lengths"]["152.4"], station["lengths"]["300.0"]
        assert small["gross_volume_mm3"] == pytest.approx(
            current["gross_volume_mm3"] * 152.4 / 300.0, abs=0.01
        )
        assert small["upright_wood_grip_mm"] == current["upright_wood_grip_mm"]
        assert small["rail_wood_grip_mm"] == current["rail_wood_grip_mm"]
        assert small["rail_contact_area_mm2"] > 0
        assert small["upright_contact_area_mm2"] > 0
        assert small["rail_contact_area_mm2"] == current["rail_contact_area_mm2"]
        assert small["upright_contact_area_mm2"] == current["upright_contact_area_mm2"]
        assert small["complete_bores"]
        assert small["grain_end_ligament_mm"] < current["grain_end_ligament_mm"]


def test_every_short_length_gate_and_no_release(result):
    assert result["strength_checked"] is False
    assert result["active_design_integrated"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False
    for station in result["stations"].values():
        small = station["lengths"]["152.4"]
        assert set(small["gates"]) == {
            "complete_bores",
            "local_collision_clear",
            "local_access_clear",
            "adjacent_blocks_clear",
            "adjacent_bores_stacks_clear",
            "adjacent_tool_paths_clear",
            "counterbores_clear",
            "counterbore_tool_paths_clear",
            "grain_end_screen_clear",
        }
        assert small["geometric_pass"] == all(small["gates"].values())
        assert small["geometric_pass"] is True
        assert station["six_inch_decision"] == "PASS_GEOMETRY_ONLY"
        assert small["grain_end_ligament_mm"] == pytest.approx(39.541)
        assert station["required_length_mm"] == pytest.approx(125.559)
