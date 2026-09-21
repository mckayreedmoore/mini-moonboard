"""PB02 bore-aware net-section screen remains authenticated and bounded."""

import pytest

from scripts.simple_center_pb02_bore_net_section_screen import screen


def test_active_a12_forward_bore_net_sections_are_bounded():
    result = screen()

    assert result["authentication"] == {
        "candidate": "pb02-kerf-right-native-development-only",
        "case": "a12-forward",
        "active_geometry_fingerprint": (
            "4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb"
        ),
        "report_sha256": (
            "4e8f9c193c225fe3d28002ab93ed3258d7560558ed089f27a49752adeea36023"
        ),
        "numerically_accepted": True,
        "actual_joint_demands_qualified": False,
    }
    assert result["bore_basis"] == {
        "diagnostic_bore_diameter_mm": 7.3,
        "stiffness_basis_bore_diameter_mm": 7.5,
        "diameter_mismatch_mm": -0.2,
        "diameters_match": False,
        "drill_instruction": False,
    }

    cuts = result["cuts"]
    assert set(cuts) == {
        "principal_at_upright_bore",
        "side_cleat_at_upright_bore",
        "side_cleat_at_link_bore",
        "rear_cleat_at_link_bore",
    }
    assert cuts["principal_at_upright_bore"]["gross_size_u_v_mm"] == pytest.approx(
        [38.1, 139.7]
    )
    assert cuts["side_cleat_at_upright_bore"]["gross_size_u_v_mm"] == pytest.approx(
        [88.9, 61.6]
    )
    assert cuts["side_cleat_at_link_bore"]["station_along_grain_mm"] == pytest.approx(
        51.5
    )
    assert cuts["rear_cleat_at_link_bore"]["gross_size_u_v_mm"] == pytest.approx(
        [88.9, 38.1]
    )
    assert cuts["side_cleat_at_upright_bore"]["station_along_grain_mm"] - cuts[
        "side_cleat_at_link_bore"
    ]["station_along_grain_mm"] == pytest.approx(27.5)

    for name, cut in cuts.items():
        assert [row["include_station_loads"] for row in cut["cut_sides"]] == [
            False,
            True,
        ]
        assert cut["net_section"]["net_area_mm2"] < cut["net_section"]["gross_area_mm2"]
        assert cut["net_section"]["removed_area_mm2"] > 0
        for side in cut["cut_sides"]:
            assert side["transverse_shear_resultant_n"] == pytest.approx(
                (side["shear_u_n"] ** 2 + side["shear_v_n"] ** 2) ** 0.5
            )
            assert set(side["corner_normal_mpa"]) == {
                "x0_t0",
                f"x0_t{cut['gross_size_u_v_mm'][1]:g}",
                f"x{cut['gross_size_u_v_mm'][0]:g}_t0",
                (f"x{cut['gross_size_u_v_mm'][0]:g}_t{cut['gross_size_u_v_mm'][1]:g}"),
            }
            assert side["torsion_nmm"] == pytest.approx(side["torsion_separate_nmm"])
            assert side["torsion_combined_with_normal_or_shear"] is False

    principal = cuts["principal_at_upright_bore"]
    assert principal["report_rows_exact_at_cut"] is False
    assert principal["within_report_valid_full_section_interval"] is False
    assert principal["action_provenance"]["extrapolation_mm"] == pytest.approx(
        5.691328257757535
    )
    for name in cuts.keys() - {"principal_at_upright_bore"}:
        assert cuts[name]["report_rows_exact_at_cut"] is True
        assert cuts[name]["within_report_valid_full_section_interval"] is True

    assert result["capacity_checked"] is False
    assert result["complete_joint_utilization"] is None
    assert result["rating_or_drilling_release"] is False
    assert result["unqualified"] == [
        "torsion_and_transverse_shear_interaction",
        "local_crossed_bore_interaction",
        "near_hole_stress_concentrations",
        "principal_bore_cut_outside_report_valid_full_section_interval",
        "material_resistance_and_capacity",
        "other_five_load_cases",
    ]
