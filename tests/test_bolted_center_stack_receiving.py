"""Receiving geometry only; these fixtures do not describe purchased parts."""

import pytest

from scripts.bolted_center_stack_receiving import check_stack


def illustrative_stack(**changes):
    values = {
        "inventory": "left-center shared-header AB205",
        "bolt_underhead_length_mm": 88.9,  # illustrative 3-1/2 in
        "plain_shank_end_mm": 54.0,
        "first_usable_thread_mm": 56.0,
        "top_plate_mm": 6.35,
        "header_mm": 38.1,
        "bottom_plate_mm": 6.35,
        "head_washer_mm": 2.5,
        "nut_washer_mm": 2.5,
        "nut_side_washer_count": 3,
        "nut_mm": 11.0,
        "required_protrusion_mm": 3.0,
        "axial_tolerance_mm": 0.5,
        "shear_allowance_mm": 0.5,
    }
    values.update(changes)
    return check_stack(**values)


def test_illustrative_three_washer_stack_is_conditional_only():
    result = illustrative_stack()
    assert result["status"] == "CONDITIONAL"
    assert result["shear_planes_mm"] == pytest.approx((8.85, 46.95))
    assert result["nut_start_mm"] == pytest.approx(60.8)
    assert result["nut_end_mm"] == pytest.approx(71.8)
    assert result["protrusion_mm"] == pytest.approx(17.1)
    assert result["both_shear_planes_plain"] is True
    assert result["nut_on_usable_threads"] is True
    assert result["full_nut_engagement_and_protrusion"] is True
    assert result["washer_stack_selected"] is False
    assert result["joint_accepted"] is False
    assert result["drill_release"] is False


def test_threaded_far_shear_plane_fails():
    result = illustrative_stack(plain_shank_end_mm=46.0, first_usable_thread_mm=48.0)
    assert result["status"] == "FULL_SHANK_ASSUMPTION_FAILED"
    assert result["both_shear_planes_plain"] is False
    assert result["nut_on_usable_threads"] is True
    assert result["root_diameter_design_unassessed"] is True
    assert result["joint_accepted"] is False


def test_shank_bottomed_nut_fails():
    result = illustrative_stack(plain_shank_end_mm=62.0, first_usable_thread_mm=64.0)
    assert result["status"] == "STACK_GEOMETRY_FAILED"
    assert result["nut_on_usable_threads"] is False
    assert result["full_nut_engagement_and_protrusion"] is False


def test_insufficient_engagement_and_protrusion_fails():
    result = illustrative_stack(bolt_underhead_length_mm=72.0)
    assert result["status"] == "STACK_GEOMETRY_FAILED"
    assert result["full_nut_engagement_and_protrusion"] is False
    assert result["protrusion_mm"] == pytest.approx(0.2)


def test_missing_data_is_unresolved():
    result = illustrative_stack(plain_shank_end_mm=None)
    assert result["status"] == "UNRESOLVED"
    assert result["missing_inputs"] == ("plain_shank_end_mm",)
    assert result["both_shear_planes_plain"] is None


def test_no_inputs_cannot_pass():
    result = check_stack()
    assert result["status"] == "UNRESOLVED"
    assert "bolt_underhead_length_mm" in result["missing_inputs"]
    assert result["joint_accepted"] is False


def test_wrong_inventory_is_rejected():
    result = illustrative_stack(inventory="outer AB205 single-flange")
    assert result["status"] == "WRONG_INVENTORY"
    assert result["inventory_matches"] is False


def test_br904_shared_header_stack_requires_received_plate_dimensions():
    result = illustrative_stack(
        inventory="left-center shared-header BR904",
        top_plate_mm=None,
        bottom_plate_mm=None,
    )
    assert result["status"] == "UNRESOLVED"
    assert result["inventory_matches"] is True
    assert result["missing_inputs"] == ("top_plate_mm", "bottom_plate_mm")
    assert result["joint_accepted"] is False


def test_br904_illustrative_stack_is_not_product_acceptance():
    result = illustrative_stack(
        inventory="left-center shared-header BR904",
        top_plate_mm=5.0,
        bottom_plate_mm=5.0,
    )
    assert result["status"] == "CONDITIONAL"
    assert result["washer_stack_selected"] is False
    assert result["joint_accepted"] is False
    assert result["drill_release"] is False


@pytest.mark.parametrize(
    "changes",
    [
        {"nut_side_washer_count": -1},
        {"nut_side_washer_count": 1.5},
        {"axial_tolerance_mm": -0.1},
        {"first_usable_thread_mm": 53.0},
        {"bolt_underhead_length_mm": float("nan")},
    ],
)
def test_invalid_measurements_raise(changes):
    with pytest.raises(ValueError):
        illustrative_stack(**changes)
