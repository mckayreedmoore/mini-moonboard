"""One mirrored outward BR904 upper-seat pose, with fixed kerf-right interfaces."""

import json

import pytest

from scripts.hardware_first_br904_outward_seat import OUTPUT, screen_outward_seat


@pytest.fixture(scope="module")
def result():
    return screen_outward_seat()


def test_sourced_product_and_one_pose(result):
    assert result["product_id"] == "Newhouse/Adamax BR904; Home Depot 325186317"
    assert result["upper_y_center_mm"] == -100.0
    assert result["nominal_mm"]["factory_hole_diameter"] == pytest.approx(14.2875)
    assert result["nominal_mm"]["factory_pitch"] == pytest.approx(47.625)
    assert result["nominal_mm"]["vertical_near"] == pytest.approx(36.83)
    assert result["nominal_mm"]["seat_near"] == pytest.approx(20.32)
    assert result["plate_bounds_mm"]["upper_left_seat"][0] < -114.45
    assert result["plate_bounds_mm"]["upper_left_seat"][1] == pytest.approx(-114.45)
    assert result["plate_bounds_mm"]["upper_right_seat"][0] == pytest.approx(114.45)
    assert result["plate_bounds_mm"]["upper_right_seat"][1] > 114.45
    assert result["drilling_released"] is False
    assert result["material_or_rating_adopted"] is False


def test_two_complete_upper_brackets_and_fixed_geometry(result):
    assert result["upper_bracket_count"] == 2
    assert result["wood_bore_count"] == 8
    assert result["bolt_path_count"] == 8
    assert result["fixed_panel_kicker_axis_count"] == 66
    assert result["fixed_panel_solid_count"] == 6
    assert result["existing_frame_axis_count"] == 12
    assert len(result["kicker_center_receivers_mm3"]) == 4
    assert all(v > 0 for v in result["kicker_center_receivers_mm3"].values())
    assert all(result["one_piece_cad_solid"].values())
    assert result["fixed_screw_receiver_loss_mm3"] == {}
    assert result["frame_receiver_changed"] == []


def test_full_occupancy_and_filters_are_reported(result):
    assert set(result["checks_mm3"]) >= {
        "plate_panel", "plate_wood", "bolt_path_panel", "bolt_path_other_wood",
        "bolt_path_other_plate", "fixed_screw_hardware", "frame_axis_hardware",
        "changed_wood_panel", "changed_wood_adjacent", "changed_wood_pairs",
    }
    assert len(result["intended_plate_bolt_path_overlap_mm3"]) == 8
    assert all(v > 0 for v in result["intended_plate_bolt_path_overlap_mm3"].values())
    assert all(not clash for clash in result["checks_mm3"].values())
    assert len(result["principal_wood_filters"]) == 4
    assert len(result["header_wood_filters"]) == 4
    assert all(v == 0 for v in result["bore_missing_receiver_wood_mm3"].values())
    assert all(min(v.values()) > 0 for v in result["header_wood_filters"].values())
    assert "principal_wood_search_filter" in result["failures"]
    assert result["status"] == "rejected_nominal_geometry"
    assert json.loads(OUTPUT.read_text()) == result
