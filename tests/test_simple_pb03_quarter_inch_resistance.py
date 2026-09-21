"""Active-geometry quarter-inch PB03 conditional resistance screen."""

import json

import pytest

from scripts.simple_pb03_quarter_inch_resistance import (
    DEFAULT_REPORT,
    REPORT_SHA256,
    screen,
)


@pytest.fixture(scope="module")
def result():
    return screen()


def test_authenticates_active_geometry_and_retained_a12_forward_report(result):
    assert result["schema"] == "simple_pb03_quarter_inch_resistance/v1"
    assert result["case"] == "a12-forward"
    assert result["candidate"] == ("pb03-lower-service-plus-upper-and-bottom-outer-v1")
    assert result["report_sha256"] == REPORT_SHA256
    assert result["source"]["report_numerically_accepted"] is True
    assert result["source"]["bolt_count"] == 32
    assert result["source"]["station_count"] == 8
    assert result["source"]["shaft_diameter_mm"] == pytest.approx(6.35)
    assert result["source"]["bore_diameter_mm"] == pytest.approx(7.5)
    assert len(result["bolts"]) == 32


def test_uses_quarter_thread_and_a307_inputs_without_combining_components(result):
    inputs = result["conditional_inputs"]
    assert inputs["nominal_diameter_in"] == pytest.approx(0.25)
    assert inputs["thread_root_diameter_in"] == pytest.approx(0.189)
    assert inputs["tensile_stress_area_in2"] == pytest.approx(0.0318)
    assert inputs["astm_a307_grade_a_minimum_tensile_psi"] == pytest.approx(60_000)
    assert inputs["conditional_bending_yield_psi"] == pytest.approx(45_000)

    expected = {
        "wood_yield_bearing",
        "bolt_shear",
        "bolt_tension",
        "washer_wood_bearing",
        "end_edge_direction",
    }
    for row in result["bolts"]:
        assert set(row["separate_checks"]) == expected
        assert "combined_ratio" not in row
        assert "joint_capacity_n" not in row
        wood = row["separate_checks"]["wood_yield_bearing"]
        assert wood["effective_bearing_diameter_in"] == pytest.approx(0.189)
        assert wood["governing_mode"] in {"Im", "Is", "II", "IIIm", "IIIs", "IV"}

    assert result["capacity_aggregation"] == (
        "prohibited_serial_components_not_combined"
    )


def test_distinguishes_factory_hex_bolts_from_cut_rod_procurement_gate(result):
    hardware = result["hardware_leads"]
    assert hardware["five_inch"]["product"] == "Everbilt 805426"
    assert hardware["five_inch"]["form"] == "factory_hex_bolt"
    assert hardware["eight_inch"]["product"] == "Everbilt 800696"
    assert hardware["eight_inch"]["form"] == "factory_hex_bolt"
    assert hardware["outer_ten_inch_sensitivity"]["product"] == (
        "National Hardware N179-416"
    )
    assert hardware["outer_ten_inch_sensitivity"]["form"] == (
        "cut_threaded_rod_sensitivity"
    )
    assert hardware["outer_ten_inch_sensitivity"]["selected"] is False
    assert hardware["outer_ten_inch_sensitivity"]["scope_procurement_gate"] is True
    assert (
        hardware["outer_ten_inch_sensitivity"][
            "current_ordinary_store_availability_verified"
        ]
        is False
    )

    outer = [
        row
        for row in result["bolts"]
        if row["hardware_length_class"] == "outer_ten_inch_sensitivity"
    ]
    assert outer
    assert all(row["hardware_selected"] is False for row in outer)


def test_reports_demands_directions_group_effects_and_separate_maxima(result):
    summary = result["summary"]
    assert summary["maximum_transverse_shear_n"] == pytest.approx(110.3996, rel=1e-4)
    assert summary["maximum_axial_tension_n"] == pytest.approx(54.929, rel=1e-4)
    assert set(summary["maximum_separate_ratios"]) == {
        "wood_yield_bearing",
        "bolt_shear",
        "bolt_tension",
        "washer_wood_bearing",
        "end_edge_geometry",
        "parallel_row_tear_out_sensitivity",
    }
    assert all(value >= 0 for value in summary["maximum_separate_ratios"].values())
    assert summary["maximum_separate_ratios"]["end_edge_geometry"] > 1
    assert result["group_effects"]["rows"]
    assert result["group_effects"]["load_sharing_qualified"] is False
    assert result["group_effects"]["group_factor_qualified"] is False
    assert any(
        not member["passes"]
        for row in result["bolts"]
        for member in row["separate_checks"]["end_edge_direction"]["members"].values()
    )


def test_development_verdict_is_revise_with_no_release(result):
    assert result["summary"]["development_verdict"] == "REVISE"
    assert result["summary"]["verdict_scope"] == "development_only"
    assert "loaded-edge" in " ".join(result["summary"]["gates"])
    assert "threaded-rod" in " ".join(result["summary"]["gates"])
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False


def test_rejects_mutated_retained_report(tmp_path):
    changed = json.loads(DEFAULT_REPORT.read_text())
    changed["parameters"]["force_xyz_n"][1] += 1
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="report SHA-256"):
        screen(path)
