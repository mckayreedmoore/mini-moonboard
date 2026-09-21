"""Six-case PB02 bore-member checks remain source-bound and developmental."""

import copy

import pytest

from fea.reinforced_timber_resistance import PSI_MPA
from scripts import simple_center_pb02_six_case_member_envelope as envelope


def test_member_envelope_preserves_all_cases_cut_sides_and_provenance():
    result = envelope.screen()

    assert result["status"] == "authenticated_six_case_bore_member_envelope"
    assert result["authentication"]["accepted_case_count"] == 6
    assert result["case_order"] == [
        "a12-forward",
        "a12-rear",
        "a12-left",
        "k12-right",
        "k12-rear",
        "a1-rear",
    ]
    assert set(result["cuts"]) == set(envelope.bore_screen.CUTS)
    for cut in result["cuts"].values():
        assert list(cut["cases"]) == result["case_order"]
        for case in cut["cases"].values():
            assert set(case["cut_sides"]) == {
                "station_loads_excluded",
                "station_loads_included",
            }
            for side in case["cut_sides"].values():
                assert (
                    side["report_rows_exact_at_cut"] is case["report_rows_exact_at_cut"]
                )
                assert side["action_provenance"] == case["action_provenance"]
                assert side["necessary_fully_braced_normal_interaction"] >= 0
                assert side["average_net_shear_ratio"] >= 0
                assert side["torsion_resistance_evaluated"] is False
                assert side["stability_qualified"] is False
                assert side["stability_used_for_disposition"] is False

    principal = result["cuts"]["principal_at_upright_bore"]
    assert principal["exact_cut_applicable_to_disposition"] is False
    for case in principal["cases"].values():
        assert case["report_rows_exact_at_cut"] is False
        assert case["action_provenance"]["kind"] == (
            "free_body_extrapolation_from_first_valid_report_plane"
        )
    for name in set(result["cuts"]) - {"principal_at_upright_bore"}:
        assert result["cuts"][name]["exact_cut_applicable_to_disposition"] is True
        assert all(
            case["report_rows_exact_at_cut"] is True
            for case in result["cuts"][name]["cases"].values()
        )


def test_sorted_axes_and_centered_hole_orientation_are_explicit():
    result = envelope.screen()
    cuts = result["cuts"]

    expected = {
        "principal_at_upright_bore": (38.1, 139.7, "width"),
        "side_cleat_at_upright_bore": (61.6, 88.9, "depth"),
        "side_cleat_at_link_bore": (61.6, 88.9, "width"),
        "rear_cleat_at_link_bore": (38.1, 88.9, "width"),
    }
    for name, (width, depth, hole_axis) in expected.items():
        section = cuts[name]["sorted_section"]
        assert section["width_mm"] == pytest.approx(width)
        assert section["depth_mm"] == pytest.approx(depth)
        assert section["centered_hole_diameter_mm"] == pytest.approx(7.3)
        assert section["centered_hole_spans_section_axis"] == hole_axis
        for case in cuts[name]["cases"].values():
            for side in case["cut_sides"].values():
                assert side["member_check"]["net_area_mm2"] == pytest.approx(
                    case["net_section"]["net_area_mm2"]
                )
                assert (
                    side["member_check"]["centered_hole_spans_section_axis"]
                    == hole_axis
                )


def test_material_references_are_conservative_and_stock_specific():
    result = envelope.screen()
    dimension = {
        "Fb_star_mpa": 900 * PSI_MPA,
        "Ft_mpa": 575 * PSI_MPA,
        "Fc_star_mpa": 1350 * PSI_MPA,
        "Fv_mpa": 180 * PSI_MPA,
        "Fc_perp_mpa": 625 * PSI_MPA,
        "Emin_mpa": 580_000 * PSI_MPA,
    }
    assert result["cuts"]["principal_at_upright_bore"]["reference_values_mpa"] == (
        pytest.approx(dimension)
    )
    assert result["cuts"]["rear_cleat_at_link_bore"]["reference_values_mpa"] == (
        pytest.approx(dimension)
    )
    side = result["cuts"]["side_cleat_at_upright_bore"]
    assert side["reference_basis"] == "2024_NDS_Table_4D_DF-L_No.2_Posts_and_Timbers"
    assert side["reference_values_mpa"] == pytest.approx(
        envelope.df_l_no2_post_timber()["reference_override"]
    )


def test_exact_cut_ratios_govern_development_disposition_only():
    result = envelope.screen()

    assert set(result["governing"]["by_case"]) == set(result["case_order"])
    assert set(result["governing"]["by_cut"]) == set(envelope.bore_screen.CUTS)
    assert result["governing"]["exact_cut_only"]["applicable"] is True
    governing = result["governing"]["exact_cut_only"]
    assert governing["case"] == "k12-rear"
    assert governing["cut"] == "rear_cleat_at_link_bore"
    assert governing["side"] == "station_loads_included"
    assert governing["normal_interaction"] == pytest.approx(0.0433475359)
    assert governing["average_net_shear_ratio"] == pytest.approx(0.0013396087)
    assert governing["ratio"] < 1
    assert result["governing"]["exact_cut_only"]["case"] == "k12-rear"
    assert result["governing"]["exact_cut_only"]["cut"] == ("rear_cleat_at_link_bore")
    assert result["governing"]["exact_cut_only"]["side"] == ("station_loads_included")
    assert result["governing"]["exact_cut_only"]["ratio"] == pytest.approx(
        0.04334753587
    )
    assert result["disposition"]["decision"] == "ADVANCE"
    assert result["disposition"]["scope"] == "development_only"
    assert result["disposition"]["uses_exact_cuts_only"] is True
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False
    assert result["boundaries"]["torsion_resistance_evaluated"] is False
    assert result["boundaries"]["local_splitting_qualified"] is False
    assert result["boundaries"]["extrapolated_principal_accepted"] is False


def test_member_envelope_fails_closed_if_evidence_boundary_changes(monkeypatch):
    original = envelope.six_case_evidence.screen

    def changed():
        result = copy.deepcopy(original())
        result["drilling_released"] = True
        return result

    monkeypatch.setattr(envelope.six_case_evidence, "screen", changed)

    with pytest.raises(ValueError, match="six-case evidence boundary changed"):
        envelope.screen()
