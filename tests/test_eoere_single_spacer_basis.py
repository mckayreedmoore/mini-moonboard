import copy

import pytest

from scripts.eoere_single_spacer_basis import window


@pytest.fixture
def cleat():
    return {"grip_mm": 127., "before_plate_mm": 0., "after_plate_mm": 6.35,
            "hardware_scenario": {"washer_thickness_mm": 2.6416, "nut_height_mm": 8.5598,
                                  "threads_per_inch": 16}}


def test_seven_inch_catalog_body_does_not_cover_the_steel(cleat):
    checked = window(cleat, 177.8, 12.7, 131.826, 146.05)
    assert checked["wood_body_margin_mm"] == pytest.approx(2.1844)
    assert checked["wood_and_steel_body_margin_mm"] == pytest.approx(-4.1656)
    assert not checked["all_nominal_reference_margins_positive"]


def test_selected_stack_has_body_seating_and_tip_allowances(cleat):
    checked = window(cleat, 190.5, 25.4, 144.272, 158.75)
    assert checked["wood_and_steel_body_margin_mm"] == pytest.approx(8.2804)
    assert checked["free_nut_seating_margin_mm"] == pytest.approx(5.2832)
    assert checked["two_pitch_margin_mm"] == pytest.approx(11.684)
    assert checked["all_nominal_reference_margins_positive"]
    thin = window(cleat, 190.5, 25.4, 144.272, 158.75, washer=1.6256)
    assert thin["free_nut_seating_margin_mm"] == pytest.approx(3.2512)
    assert thin["all_nominal_reference_margins_positive"]


def test_a_shorter_spacer_can_prevent_nut_seating(cleat):
    checked = window(cleat, 190.5, 19.05, 144.272, 158.75)
    assert checked["free_nut_seating_margin_mm"] == pytest.approx(-1.0668)
    assert not checked["all_nominal_reference_margins_positive"]


def test_support_and_seating_windows_use_opposite_thickness_limits(cleat):
    thin_stock = copy.deepcopy(cleat)
    thin_stock["grip_mm"] -= 3.3
    assert window(thin_stock, 190.5, 25.4, 144.272, 158.75, washer=1.6256)["free_nut_seating_margin_mm"] < 0
    thick_stock = copy.deepcopy(cleat)
    thick_stock["grip_mm"] += 8.3
    assert window(thick_stock, 190.5, 25.4, 144.272, 158.75)["wood_and_steel_body_margin_mm"] < 0
