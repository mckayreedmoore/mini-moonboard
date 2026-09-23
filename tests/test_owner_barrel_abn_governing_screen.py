"""Regression tests for focused ABN governing-joint screen."""

import pytest

from scripts import owner_barrel_abn_governing_screen as abn


@pytest.fixture(scope="module")
def report():
    return abn.build_report()


def test_abn_retail_claim_stays_bounded(report):
    hardware = report["retail_hardware"]
    assert hardware["part_number"] == "7015_10PACK"
    assert hardware["asin"] == "B01N3QW1JS"
    assert hardware["pack_count"] == 10
    assert hardware["availability"] == "CURRENTLY_UNAVAILABLE_NO_FEATURED_OFFER"
    assert not hardware["direct_amazon_numeric_offset_verified"]
    assert not hardware["strength_grade_or_rating_published"]
    assert not hardware["geometry_freeze_allowed"]


def test_nominal_offset_is_cad_equivalent_but_not_frozen(report):
    geometry = report["cad_geometry"]
    assert geometry["offset_change_mm"] == pytest.approx(0.0056)
    near = geometry["orientation_cases"]["six_mm_end_proximal"]
    far = geometry["orientation_cases"]["ten_mm_end_proximal"]
    assert near["body_recess_from_entry_mm"] == pytest.approx(13.05)
    assert near["blind_bore_depth_mm"] == pytest.approx(29.05)
    assert near["far_side_stock_mm"] == pytest.approx(9.05)
    assert far["body_recess_from_entry_mm"] == pytest.approx(9.05)
    assert far["blind_bore_depth_mm"] == pytest.approx(25.05)
    assert far["far_side_stock_mm"] == pytest.approx(13.05)
    assert geometry["slot_end_to_axis_mm"] is None
    assert geometry["clear_wood_between_rows_mm"] == pytest.approx(70.0)
    assert geometry["minimum_raw_face_clear_ligament_mm"] == pytest.approx(
        31.551404
    )
    assert geometry["status"] == (
        "PLAUSIBLE_NOMINAL_BOTH_ORIENTATIONS_PENDING_SAMPLE_DATUM"
    )


def test_updated_wood_screen_fails_with_explicit_margins(report):
    wood = report["wood"]
    assert wood["screen_row_demand_n"] == pytest.approx(846.705806)
    assert wood["nds_fabbri_adapted_bearing"]["reference_n"] == pytest.approx(
        424.184725
    )
    assert wood["nds_fabbri_adapted_bearing"]["capacity_over_demand"] == (
        pytest.approx(0.500982)
    )
    assert wood["fpl_form_adapted_bearing"]["reference_n"] == pytest.approx(
        345.893823
    )
    assert wood["fpl_form_adapted_bearing"]["capacity_over_demand"] == (
        pytest.approx(0.408517)
    )
    assert wood["face_cell_pressure"]["screen"] == "FAIL"
    assert wood["center_split_plane"]["resistance_n"] is None
    assert wood["two_row_group_tearout"]["resistance_n"] is None
    assert wood["finite_screen"] == "NO_GO_AS_SCREENED_WOOD_BEARING_AND_FACE_PRESSURE"


def test_s355_stays_hypothetical_and_adverse_sensitive(report):
    metal = report["metal"]
    assert metal["advertised_abn_material_lower_bound_mpa"] is None
    nominal = metal["nominal_geometry_requirements"]
    assert nominal["female_thread_shear_mpa_times_gamma"] == pytest.approx(19.616616)
    assert nominal["illustrative_lobe_average_shear_mpa_times_gamma"] == (
        pytest.approx(43.172557)
    )
    assert nominal["illustrative_lobe_bending_mpa_times_gamma_kt"] == (
        pytest.approx(199.135335)
    )
    s355 = metal["hypothetical_s355"]
    assert s355["nominal_margin_at_gamma_1_kt_1p5"] == pytest.approx(1.188471)
    assert s355["adverse_margin_at_gamma_1_kt_1p5"] == pytest.approx(0.876681)
    assert "unverified hypothetical" in s355["assumption"]


def test_finite_decision_is_no_go_screen_not_build_claim(report):
    decision = report["decision"]
    assert decision["nominal_cad_fit"] == (
        "PLAUSIBLE_BOTH_ORIENTATIONS_PENDING_SAMPLE_MEASUREMENT"
    )
    assert decision["governing_principal_header_strength_screen"] == (
        "CONDITIONAL_NO_GO_IF_846P7_N_SCREEN_AND_ADAPTED_WOOD_REFERENCES_ARE_ADOPTED"
    )
    assert decision["actual_abn_metal"] == "EVIDENCE_BLOCKED"
    assert decision["complete_design"] == "EVIDENCE_BLOCKED"
    assert not decision["diy_ready"]
    assert not decision["structural_released"]
