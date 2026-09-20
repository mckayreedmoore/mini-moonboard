"""Reproducible geometry gates for one nominal HL53 center trial."""

import json
from pathlib import Path

import pytest

from scripts.hardware_first_center_hl53 import screen_hl53_center

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs/bolted-candidate-prototypes/hardware_first_center_hl53.json"


def test_hl53_paired_x_face_trial_is_rejected_by_installed_geometry():
    result = screen_hl53_center()
    assert result["status"] == "rejected_installed_geometry_trial"
    assert result["all_66_panel_axes_unchanged"] is True
    assert result["hl53_nominal_pattern_mm"]["hole_offsets_across_each_flange"] == [50.8, 114.3]
    assert result["header_z_mm"] == [238.9, 327.8]
    assert result["upper_lower_y_separation_mm"] == 76.2
    assert len(result["bores"]) == 16
    assert all(b["vertical_missing_wood_mm3"] <= 0.05 and
               b["header_missing_wood_mm3"] <= 0.05 for b in result["bores"])
    assert result["panel_receivers_with_nominal_intersection"] == 66
    assert result["panel_bore_clashes"] == []
    assert result["full_kicker_inner_edge_support"] is False
    assert result["remaining_kicker_inner_edge_overhang_mm"]["right"] > 1.7
    assert result["maximum_gap_if_posts_alone_support_inner_kicker_edges_mm"] == 0
    assert result["two_inner_gauge7_plates_nominal_mm"] > 9
    assert result["nominal_inner_plate_shortfall_mm"] > 9
    assert json.loads(RESULT.read_text()) == result


def test_outward_header_hole_is_on_the_outward_seat() -> None:
    result = screen_hl53_center()
    by_id = {bore["id"]: bore for bore in result["bores"]}
    assert by_id["left_outer_upper_1"]["header_center_mm"][0] == pytest.approx(-190.65)
    assert by_id["right_outer_upper_1"]["header_center_mm"][0] == pytest.approx(190.65)
    assert by_id["left_inner_upper_1"]["header_center_mm"][0] == pytest.approx(50.65)
    assert by_id["right_inner_upper_1"]["header_center_mm"][0] == pytest.approx(-50.65)
