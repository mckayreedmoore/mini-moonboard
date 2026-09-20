"""HL53 spaced-rib component comparison and protected-axis gates."""

import json

import pytest

from scripts.hardware_first_hl53_spaced_ribs import OUTPUT, screen_spaced_ribs


@pytest.fixture(scope="module")
def report():
    return screen_spaced_ribs()


def test_three_coarse_cases_and_correct_header_hole_sign(report):
    assert [case["rib_spacing_mm"] for case in report["cases"]] == [480, 520, 560]
    assert report["fixed_panel_kicker_axis_count"] == 66
    assert report["fixed_panel_solid_count"] == 6
    assert [case["bracket_count"] for case in report["cases"]] == [8, 9, 8]
    for case in report["cases"]:
        assert case["wrong_side_header_holes"] == []
        assert case["bolt_missing_own_hole_corridor"] == []
        assert case["bolt_missing_receiver"] == []
        assert case["header_links_have_holes_and_receivers"] is True
        assert case["front_carrier_rib_overlaps_mm3"] == {}
        assert len(case["bolt_checks"]) == 4 * case["bracket_count"]
        assert all(v["own_steel_clash_mm3"] == 0 for v in case["bolt_checks"])
        assert all(
            v["meets_hl53_minimum_wood_thickness"]
            for v in case["bolt_checks"]
            if not v["id"].startswith("rail_probe_")
        )
        assert all(
            v["wood_thickness_along_bolt_mm"] == 184.15
            for v in case["bolt_checks"]
            if v["receiver"] == "base_post_center" and "_vertical_" in v["id"]
        )


def test_classified_fit_and_unqualified_disposition(report):
    for case in report["cases"]:
        assert case["failure_classes"] == sorted(set(case["failure_classes"]))
        assert case["fixed_screw_receiver_loss_mm3"] == {}
        assert case["kicker_seam_supported"] is True
        assert case["connected_architecture_verdict"] is False
        assert "rail_to_rib_connection_open" in case["failure_classes"]
        assert "bracket_wood" in case["failure_classes"]
        assert all(case["one_piece_wood"].values())
        assert case["status"] in {"nominal_fit_only", "rejected_nominal_geometry"}
    assert report["material_or_rating_adopted"] is False
    assert report["drilling_released"] is False
    probe = report["cases"][1]["rail_connection_probe"]
    assert probe["all_bolts_meet_hole_and_receiver"] is True
    assert probe["all_bores_contained"] is False
    assert probe["original_rail_section_thickness_mm"] == 38.1
    assert probe["rail_retains_original_1_5_in_section"] is True
    assert probe["all_receivers_meet_88_9_mm_minimum"] is False
    assert report["cases"][1]["below_hl53_minimum_wood_thickness"] == [
        "rail_probe_bottom_right_seat_1",
        "rail_probe_bottom_right_seat_2",
    ]
    assert (
        "catalog_inapplicable_wood_thickness" in report["cases"][1]["failure_classes"]
    )
    assert report["cases"][1]["hl53_wood_thickness_catalog_applicable"] is False
    assert report["cases"][0]["hl53_wood_thickness_catalog_applicable"] is True
    assert report["cases"][2]["hl53_wood_thickness_catalog_applicable"] is True
    assert "access_panel" in report["cases"][1]["failure_classes"]
    assert json.loads(OUTPUT.read_text()) == report
