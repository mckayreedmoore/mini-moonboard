"""Regression for the bounded hybrid HL35 installed-geometry trial."""

import json
from pathlib import Path

from scripts.hardware_first_center_hybrid import screen_hybrid

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/bolted-candidate-prototypes/hardware_first_center_hybrid.json"


def test_hybrid_rejects_real_toe_and_neighbor_clashes_without_losing_screw_wood():
    result = screen_hybrid()
    assert result["status"] == "rejected_installed_geometry_trial"
    assert result["protected_axis_count"] == 66
    assert result["retained_frame_bolt_axis_count"] == 12
    assert result["principal_bounds_mm"]["base_principal_center_left"][:2] == [
        -114.45,
        -25.55,
    ]
    assert result["principal_bounds_mm"]["base_principal_center_right"][:2] == [
        25.55,
        114.45,
    ]
    assert result["principal_screw_receiver_loss_mm3"] == {}
    assert result["protected_screw_receiver_missing"] == {}
    assert len(result["kicker_center_receivers_mm3"]) == 4
    assert all(v > 400 for v in result["kicker_center_receivers_mm3"].values())
    assert result["independent_upper_lower_bore_crossings_mm3"] == {}
    assert all(
        v == 0
        for n, v in result["bore_missing_receiver_wood_mm3"].items()
        if n.startswith("lower_")
    )
    assert (
        result["upper_principal_toe_bore_missing_wood_mm3"]["upper_left_principal_1"]
        > 12000
    )
    assert (
        result["upper_principal_toe_bore_missing_wood_mm3"]["upper_right_principal_1"]
        > 12000
    )
    assert (
        result["plate_adjacent_wood_clashes_mm3"]["upper_left_vertical"][
            "base_rail_bottom_left"
        ]
        > 8000
    )
    assert (
        result["new_wood_adjacent_clashes_mm3"]["base_principal_center_left"][
            "base_rail_bottom_left"
        ]
        > 100000
    )
    assert result["protected_screw_plate_clashes_mm3"] == {}
    assert result["protected_screw_bore_clashes_mm3"] == {}
    assert result["existing_frame_axis_hardware_clashes_mm3"] == {}


def test_hybrid_one_piece_blank_gate_and_report():
    result = screen_hybrid()
    assert all(result["one_piece_cad_solid"].values())
    assert result["minimum_sampled_blank_envelope_mm"]["header"][0] > 2400
    assert (
        result["minimum_sampled_blank_envelope_mm"]["base_principal_center_left"][2]
        > 2400
    )
    assert all(result["ordinary_stock_example_dimension_fit"].values())
    assert result["no_considered_ordinary_stock_blank_can_contain_shape"] is False
    assert (
        result["eight_foot_4x10_header_comparison"]["remaining_total_length_mm"]
        == 3.175
    )
    assert (
        result["eight_foot_4x10_header_comparison"]["production_blank_feasible"]
        is False
    )
    assert result["eight_foot_principal_length_shortfall_mm"] > 27
    assert "delivered one-piece blanks are unverified" in result["retail_blank_status"]
    assert json.loads(REPORT.read_text()) == result
