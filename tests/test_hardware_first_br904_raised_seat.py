"""Regression for the sourced, bounded BR904 nominal geometry screen."""

import json

import pytest

from scripts.hardware_first_br904_raised_seat import (
    OUTPUT,
    PITCH,
    SEAT_NEAR,
    VERTICAL_NEAR,
    screen_raised_seat,
)


@pytest.fixture(scope="module")
def report():
    return screen_raised_seat()


def test_nominal_br904_dimensions_are_sourced_and_not_drilling_data(report):
    nominal = report["factory_nominal_mm"]
    assert "325186317" in report["product"]
    assert report["retailer_nominal_drawing"].endswith("66922570.jpeg")
    assert nominal["hole_diameter_advertised"] == pytest.approx(14.2875)
    assert nominal["pitch_advertised"] == pytest.approx(PITCH)
    assert nominal["vertical_near_from_drawing_arithmetic"] == pytest.approx(
        VERTICAL_NEAR, abs=0.001
    )
    assert nominal["horizontal_near_from_drawing_arithmetic"] == pytest.approx(
        SEAT_NEAR, abs=0.001
    )
    assert report["material_or_rating_adopted"] is False
    assert report["drilling_released"] is False


def test_full_pair_and_fixed_geometry_checked(report):
    assert report["fixed_panel_kicker_axes"] == 66
    assert report["existing_frame_axes"] == 12
    assert report["fixed_panel_solids"] >= 2
    assert len(report["poses"]) == 3
    for pose in report["poses"]:
        assert pose["bore_count"] == 12  # two per leg, both legs, three brackets
        assert len(pose["kicker_center_receivers_mm3"]) == 4
        assert all(v > 0 for v in pose["kicker_center_receivers_mm3"].values())
        assert all(pose["one_piece_cad_solid"].values())
        assert pose["fixed_screw_receiver_loss_mm3"] == {}
        assert pose["checks_mm3"]["plate_panel"] == {}
        assert pose["checks_mm3"]["screw_hardware"] == {}
        assert pose["checks_mm3"]["frame_hardware"] == {}


def test_lower_post_bores_are_full_section_after_centering_fix(report):
    for pose in report["poses"]:
        missing = pose["bore_missing_receiver_wood_mm3"]
        assert missing["lower_post_1"] == 0
        assert missing["lower_post_2"] == 0


def test_nominal_failures_are_distinguished_from_bore_modeling_error(report):
    assert report["status"] == "rejected_bounded_raised_seat"
    for pose in report["poses"]:
        assert pose["lower_wood_filters"][
            "post_vertical_end_3_5d_play_margin_mm"
        ] < 0
        assert pose["lower_wood_filters"][
            "header_rear_edge_4d_play_margin_mm"
        ] < 0
        assert "lower_wood_search_filter" in pose["failures"]
    assert json.loads(OUTPUT.read_text()) == report
