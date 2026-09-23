"""Fail-closed tests for nominal vertical-barrel breakout mapping."""

import pytest

from scripts import owner_barrel_vertical_center_breakout as breakout


@pytest.fixture(scope="module")
def report():
    return breakout.build_report()


def test_complete_host_cut_inventory_is_applied(report):
    assert report["cut_inventory"] == {
        "base_header": {
            "candidate_service": 0,
            "additional_machining": 0,
            "panel_screws": 10,
            "retained_frame_bolts": 0,
            "candidate_joint": 4,
        },
        "base_principal_center_left": {
            "candidate_service": 1,
            "additional_machining": 0,
            "panel_screws": 8,
            "retained_frame_bolts": 0,
            "candidate_joint": 4,
        },
        "base_principal_center_right": {
            "candidate_service": 1,
            "additional_machining": 0,
            "panel_screws": 8,
            "retained_frame_bolts": 0,
            "candidate_joint": 4,
        },
    }


def test_rows_are_grain_staggered_and_clear(report):
    geometry = report["row_geometry"]
    assert geometry["global_y_pitch_mm"] == pytest.approx(80.0)
    assert geometry["grain_t_stagger_mm"] == pytest.approx(51.423009)
    assert geometry["cross_grain_n_stagger_mm"] == pytest.approx(61.283556)
    assert geometry["bolt_bore_clear_gap_mm"] == pytest.approx(72.5)
    assert geometry["barrel_bore_clear_gap_mm"] == pytest.approx(69.9924)
    assert geometry["mixed_bore_clear_gap_mm"] == pytest.approx(71.2462)
    assert geometry["minimum_candidate_service_bore_clear_gap_mm"] == pytest.approx(
        26.029795, abs=1e-5
    )


def test_signed_rays_and_nominal_sections_are_pinned(report):
    assert len(report["rows"]) == 4
    for row in report["rows"]:
        assert row["signed_raw_face_rays_mm"]["grain_negative_mm"] == pytest.approx(
            36.551404
        )
        assert row["two_plane_area_mm2"] == pytest.approx(2716.48722, abs=1e-5)
        assert row["awc_appendix_e_unadjusted_reference_n"] == pytest.approx(
            1685.656806, abs=1e-5
        )
        assert row["center_split_plane_area_mm2"] == pytest.approx(
            1245.159307, abs=1e-5
        )
        assert row["minimum_raw_face_clear_ligament_mm"] == pytest.approx(31.547604)
        expected_net = 2955.649188 if row["bolt"].endswith("_1") else 5031.774372
        assert row["grain_normal_net_section_area_mm2"] == pytest.approx(
            expected_net, abs=1e-5
        )


def test_geometry_map_does_not_claim_resistance_or_release(report):
    quality = report["mapping_quality"]
    assert (
        quality["maximum_last_step_change_mm2"]
        < quality["accepted_maximum_last_step_change_mm2"]
    )
    assert quality["all_mapped_areas_positive"]
    decision = report["decision"]
    assert decision["nominal_geometry_map"] == "MAPPED"
    assert decision["bearing_row_and_net_section"] == "REFERENCE_ONLY"
    assert decision["group_tearout"] == "UNRESOLVED_NOT_ENUMERATED"
    assert decision["tension_perpendicular_splitting"] == "UNSUPPORTED_RESISTANCE"
    assert decision["adverse_tolerance_geometry"] == "UNRESOLVED"
    assert decision["finite_decision"] == "EVIDENCE_BLOCKED"
    assert not decision["diy_ready"]
    assert not decision["drilling_released"]
    assert not decision["fabrication_released"]
    assert not decision["structural_released"]
