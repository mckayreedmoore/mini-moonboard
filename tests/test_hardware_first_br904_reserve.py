"""Reserve screen keeps the fixed outward BR904 pose and reports its limits."""

import json

import pytest

from scripts.hardware_first_br904_reserve import OUTPUT, screen_reserve


@pytest.fixture(scope="module")
def result():
    return screen_reserve()


def test_rear_edge_and_header_shoulder_reach_ten_mm(result):
    assert result["rearward_deepening_mm"] == 80.0
    assert result["header_raised_half_width_mm"] == 242.0
    assert result["minimum_principal_transverse_reserve_mm"] >= 10
    assert result["minimum_header_shoulder_reserve_mm"] >= 10
    assert result["fixed_panel_kicker_axis_count"] == 66
    assert result["existing_frame_axis_count"] == 12
    assert result["wood_bore_count"] == result["bolt_path_count"] == 8
    assert all(result["one_piece_cad_solid"].values())


def test_complete_nominal_clash_screen_and_stock_limit(result):
    assert result["failures"] == []
    assert all(not found for found in result["checks_mm3"].values())
    assert all(v == 0 for v in result["bore_missing_receiver_wood_mm3"].values())
    assert all(v > 0 for v in result["intended_plate_bolt_path_overlap_mm3"].values())
    assert result["fixed_screw_receiver_loss_mm3"] == {}
    assert result["frame_receiver_changed"] == []
    assert result["status"] == "geometry_only_stock_unverified"
    assert result["minimum_principal_oblique_toe_reserve_mm"] < 10
    assert all(result["lowes_dimensional_lead"]["geometric_envelope_fit_only"].values())
    assert result["ordinary_big_box_blank_verified"] is False
    assert result["material_or_rating_adopted"] is False
    assert result["drilling_released"] is False
    assert json.loads(OUTPUT.read_text()) == result
