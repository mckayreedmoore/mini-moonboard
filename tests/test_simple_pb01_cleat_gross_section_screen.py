"""Focused gross-section arithmetic and evidence-boundary checks."""

import pytest

from scripts.simple_pb01_cleat_gross_section_screen import screen, stress_components


def test_rectangular_component_arithmetic():
    row = stress_components(
        {
            "station_along_grain_mm": 20.0,
            "include_station_loads": False,
            "axial_n_tension_positive": -60.0,
            "shear_u_n": 20.0,
            "shear_v_n": -30.0,
            "moment_u_nmm": 120.0,
            "moment_v_nmm": -240.0,
            "torsion_nmm": 10.0,
        },
        width_mm=10.0,
        depth_mm=6.0,
    )
    assert row["axial_mpa"] == pytest.approx(-1.0)
    assert row["bending_u_mpa"] == pytest.approx(2.0)
    assert row["bending_v_mpa"] == pytest.approx(-2.4)
    assert row["shear_u_peak_mpa"] == pytest.approx(0.5)
    assert row["shear_v_peak_mpa"] == pytest.approx(-0.75)
    assert row["normal_tension_corner_mpa"] == pytest.approx(3.4)
    assert row["normal_compression_corner_mpa"] == pytest.approx(5.4)
    assert row["transverse_shear_center_mpa"] == pytest.approx(0.9013878189)
    assert row["torsion_nmm"] == 10.0
    assert row["torsional_stress_mpa"] is None


def test_preserved_case_reports_components_and_explicit_non_rating():
    result = screen()
    assert result["case"] == "a12-left"
    assert result["scope"] == "diagnostic_only"
    assert result["geometry_mm"]["width_u"] == pytest.approx(139.7)
    assert result["geometry_mm"]["depth_v"] == pytest.approx(57.15)
    assert len(result["sections"]) == 20
    assert result["maxima"]["torsion_abs_nmm"]["value"] > 0
    assert result["maxima"]["bending_u_abs_mpa"]["value"] > 0
    assert result["maxima"]["bending_v_abs_mpa"]["value"] > 0
    assert result["maxima"]["axial_compression_mpa"]["value"] > 0
    assert result["maxima"]["normal_tension_corner_mpa"]["value"] > 0
    assert result["maxima"]["normal_compression_corner_mpa"]["value"] > 0
    assert result["maxima"]["transverse_shear_center_mpa"]["value"] > 0
    assert result["reference_design_values_mpa"] is None
    assert result["net_section_stress_mpa"] is None
    assert result["combined_stress_mpa"] is None
    assert result["capacity_n"] is None
    assert result["utilization"] is None
    assert result["complete_joint_pass"] is None


def test_rejects_nonfinite_section_load():
    with pytest.raises(ValueError, match="moment_u_nmm"):
        stress_components(
            {
                "station_along_grain_mm": 0,
                "include_station_loads": True,
                "axial_n_tension_positive": 0,
                "shear_u_n": 0,
                "shear_v_n": 0,
                "moment_u_nmm": float("nan"),
                "moment_v_nmm": 0,
                "torsion_nmm": 0,
            },
            width_mm=10,
            depth_mm=6,
        )
