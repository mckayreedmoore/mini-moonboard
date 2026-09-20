"""Wider HL53 rib spacing and one thick one-piece rail-joint trial."""

import json

import pytest

from scripts.hardware_first_hl53_wide_ribs import OUTPUT, screen_wide_ribs


@pytest.fixture(scope="module")
def report():
    return screen_wide_ribs()


def test_wide_header_links_preserve_protected_geometry(report):
    assert [case["rib_spacing_mm"] for case in report["cases"]] == [620, 660, 700]
    assert report["fixed_panel_kicker_axis_count"] == 66
    assert report["fixed_panel_solid_count"] == 6
    assert [case["status"] for case in report["cases"]] == [
        "partial_nominal_header_fit",
        "partial_nominal_header_fit",
        "rejected_nominal_geometry",
    ]
    for case in report["cases"]:
        assert case["front_carrier_rib_overlaps_mm3"] == {}
        assert case["fixed_screw_receiver_loss_mm3"] == {}
        assert case["kicker_seam_supported"] is True
        assert case["header_links_have_holes_and_receivers"] is True
        assert case["below_hl53_minimum_wood_thickness"] == []
        assert case["connected_architecture_verdict"] is False
        assert case["assembly_status"] == "incomplete_connected_assembly"


def test_representative_factory_rail_joint_is_screened(report):
    joint = report["rail_joint"]
    assert joint["rib_spacing_mm"] == 660
    assert joint["bracket_model"] == "HL53"
    assert len(joint["bolt_checks"]) == 4
    assert all(v["own_hole_corridor_mm3"] > 0 for v in joint["bolt_checks"])
    assert all(v["receiver_overlap_mm3"] > 0 for v in joint["bolt_checks"])
    assert all(v["wood_thickness_along_bolt_mm"] >= 88.89 for v in joint["bolt_checks"])
    assert joint["fixed_screw_receiver_loss_mm3"] == {}
    assert joint["one_piece_rail"] is True
    assert joint["status"] == "isolated_bolt_geometry_unsupported_seat"
    assert joint["seat_leading_unsupported_mm"] == pytest.approx(15)
    assert joint["seat_supported_length_mm"] == pytest.approx(131.05)
    assert "unsupported_hl53_seat" in joint["failure_classes"]
    assert joint["checks_mm3"]["rail_panel"] == {}
    assert joint["checks_mm3"]["tool_panel"] == {}
    assert joint["one_piece_stock_status"].startswith("unverified")
    assert joint["actual_head_nut_stack_verified"] is False
    assert joint["actual_tool_access_verified"] is False
    assert joint["catalog_applicability_verified"] is False
    assert joint["parent_neighbor_integration_checked"] is False
    assert len(joint["not_screened_against"]) == 3
    assert joint["all_66_axes_preserved"] is True
    zero = report["zero_gap_probe"]
    assert zero["rail_to_rib_gap_mm"] == 0
    assert zero["seat_leading_unsupported_mm"] == pytest.approx(0)
    assert zero["seat_supported_length_mm"] == pytest.approx(146.05)
    assert len(zero["bolt_checks"]) == 4
    assert all(v["own_hole_corridor_mm3"] > 0 for v in zero["bolt_checks"])
    assert all(v["receiver_overlap_mm3"] > 0 for v in zero["bolt_checks"])
    assert all(v["bore_missing_receiver_mm3"] == 0 for v in zero["bolt_checks"])
    assert all(v["wood_thickness_along_bolt_mm"] >= 88.89 for v in zero["bolt_checks"])
    assert all(v["bolt_hits_own_steel_mm3"] == 0 for v in zero["bolt_checks"])
    assert zero["fixed_screw_receiver_loss_mm3"] == {}
    assert zero["all_66_axes_preserved"] is True
    assert zero["one_piece_rail"] is True
    assert set(zero["checks_mm3"]) >= {
        "rail_panel",
        "rail_rib",
        "bracket_panel",
        "bracket_wood",
        "bolt_panel",
        "screw_hardware",
        "washer_panel",
        "tool_panel",
        "washer_wood",
        "tool_wood",
    }
    assert all(not found for found in zero["checks_mm3"].values())
    assert zero["catalog_applicability_verified"] is False
    assert zero["status"] == "isolated_joint_geometry_clear"
    assert zero["parent_neighbor_integration_checked"] is False
    assert report["connected_architecture_verdict"] is False
    assert report["material_or_rating_adopted"] is False
    assert report["drilling_released"] is False
    assert json.loads(OUTPUT.read_text()) == report


def test_zero_gap_square_blank_has_only_a_nominal_retail_comparator(report):
    zero = report["zero_gap_probe"]
    blank = zero["sampled_square_rail_blank"]
    assert blank["sample_step_deg"] == 0.001
    assert blank["rotation_about_x_deg"] == pytest.approx(4.885, abs=0.001)
    assert blank["x_length_mm"] == pytest.approx(752.675)
    assert blank["yz_extents_mm"] == pytest.approx([125.8675, 125.8684], abs=0.001)
    assert blank["max_yz_extent_mm"] == pytest.approx(125.8684, abs=0.001)
    stock = zero["retail_blank_comparator"]
    assert stock["model"] == "637643"
    assert stock["grade"] == "#2 Better"
    assert stock["listed_actual_mm"] == pytest.approx([143.5608, 143.5608, 2438.4])
    assert stock["nominal_dimensions_enclose_sampled_blank"] is True
    assert stock["stock_accepted"] is False
    assert set(stock["open_checks"]) >= {
        "local availability",
        "delivered dimensions",
        "moisture and drying",
        "grade verification",
        "machining allowance",
        "treatment suitability",
    }
    assert zero["catalog_applicability_verified"] is False
    assert zero["connected_architecture_verdict"] is False
