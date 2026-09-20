"""One-piece rearward principal extension on the outward BR904 upper pose."""

import json

import pytest

from scripts.hardware_first_br904_deep_principal import OUTPUT, screen_deep_principal


@pytest.fixture(scope="module")
def result():
    return screen_deep_principal()


def test_two_one_piece_principals_reach_nominal_edge_filter(result):
    assert result["rearward_deepening_mm"] == 60.0
    assert result["parent_upper_y_center_mm"] == -100.0
    assert len(result["principal_wood_filters"]) == 4
    assert all(
        min(value["transverse_4d_play_margins_mm"]) >= 0
        for value in result["principal_wood_filters"].values()
    )
    assert all(result["one_piece_cad_solid"].values())
    assert result["fixed_panel_kicker_axis_count"] == 66
    assert result["existing_frame_axis_count"] == 12


def test_full_assembly_checks_and_receivers(result):
    assert result["wood_bore_count"] == 8
    assert result["bolt_path_count"] == 8
    assert all(v == 0 for v in result["bore_missing_receiver_wood_mm3"].values())
    assert all(v > 0 for v in result["intended_plate_bolt_path_overlap_mm3"].values())
    assert result["fixed_screw_receiver_loss_mm3"] == {}
    assert result["frame_receiver_changed"] == []
    assert len(result["kicker_center_receivers_mm3"]) == 4
    assert all(v > 0 for v in result["kicker_center_receivers_mm3"].values())
    assert set(result["checks_mm3"]) >= {
        "plate_panel", "plate_wood", "bolt_path_panel", "bolt_path_other_wood",
        "bolt_path_other_plate", "fixed_screw_hardware", "frame_axis_hardware",
        "changed_wood_panel", "changed_wood_adjacent", "changed_wood_pairs",
    }
    assert all(not clash for clash in result["checks_mm3"].values())


def test_stock_gate_and_no_release(result):
    for name in ("base_principal_center_left", "base_principal_center_right"):
        assert result["principal_minimum_sampled_blank_mm"][name] == pytest.approx(
            [88.9, 185.6627, 2504.8786], abs=0.002
        )
        assert result["ordinary_big_box_example"]["geometric_envelope_fit_only"][name]
    assert result["status"] == "geometry_only_stock_unverified"
    assert result["failures"] == []
    assert result["ordinary_big_box_blank_verified"] is False
    assert result["material_or_rating_adopted"] is False
    assert result["drilling_released"] is False
    assert json.loads(OUTPUT.read_text()) == result
