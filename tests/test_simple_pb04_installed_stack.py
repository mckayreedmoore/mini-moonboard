"""Source-distinct installed PB04 outer-upright stack screen."""

import pytest

from scripts import simple_pb04_installed_stack as installed


@pytest.fixture(scope="module")
def result():
    return installed.screen()


def test_installed_inventory_and_source(result):
    assert result["schema"] == "simple_pb04_installed_stack/v1"
    assert result["source_id"] == "pb04-upper-edge-plus-outer-counterbores-v1"
    assert len(result["stacks"]) == 12
    assert result["fixed_panel_kicker_axes"] == 66
    assert result["gross_bores_preserved"] is True


def test_axial_stack_and_threading(result):
    axial = result["axial_mm"]
    assert axial["nominal_under_head_length"] == pytest.approx(203.2)
    assert axial["usable_thread_length"] == pytest.approx(152.4)
    assert axial["wood_grip"] == pytest.approx(191.6176)
    assert axial["pocket_depth"] == pytest.approx(36.9824)
    assert axial["thread_pitch"] == pytest.approx(1.27)
    assert axial["nut_engagement_threads"] == pytest.approx(5.7404 / 1.27)
    assert axial["end_projection_threads"] == pytest.approx(2.0)
    assert axial["nominal_length_margin"] == pytest.approx(0.0, abs=1e-9)
    assert axial["required_tolerance_reserve"] > 0
    assert axial["tolerance_reserve_pass"] is False


def test_installed_geometry_and_access_separated(result):
    assert result["permanent_collision_hits_mm3"] == {}
    assert result["tool_permanent_hits_mm3"] == {}
    assert result["socket_outside_pocket_mm3"] == {}
    assert isinstance(result["tool_removable_panel_hits_mm3"], dict)
    assert all(
        row["gross_bore_length_mm"] == pytest.approx(233.6)
        for row in result["stacks"].values()
    )
    assert all(
        row["bore_start_to_near_face_mm"] == pytest.approx(2.5)
        for row in result["stacks"].values()
    )
    assert all(
        row["bolt_end_from_under_head_mm"] == pytest.approx(203.2)
        for row in result["stacks"].values()
    )
    assert all(row["far_washer_at_pocket_floor"] for row in result["stacks"].values())
    assert all(row["near_washer_at_original_face"] for row in result["stacks"].values())
    assert result["decision"] == "REVISE"
    assert result["qualified_for_design"] is False
    assert result["fabrication_released"] is False


def test_zero_requested_reserve_still_cannot_pass():
    with pytest.raises(ValueError, match="positive"):
        installed.screen(required_tolerance_reserve_mm=0)
