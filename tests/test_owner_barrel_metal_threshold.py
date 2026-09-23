"""Pin the provisional STAFAST metal requirement calculation."""

import pytest

from scripts import owner_barrel_metal_threshold as metal


def test_metal_threshold_geometry_and_equations_are_reproducible():
    report = metal.build_report()
    inputs = report["inputs"]
    assert inputs["old_topology_proxy_tension_n"] == pytest.approx(301.493967)
    assert inputs["adverse_body_diameter_mm"] == pytest.approx(9.6012)
    assert inputs["adverse_body_length_mm"] == pytest.approx(16.4084)
    assert inputs["adverse_axis_offset_mm"] == pytest.approx(6.4008)
    assert inputs["assumed_complete_thread_length_mm"] == pytest.approx(7.0612)
    geometry = report["derived_geometry"]
    assert geometry["net_two_lobe_area_mm2"] == pytest.approx(16.227763)
    assert geometry["net_second_moment_mm4"] == pytest.approx(44.08833)
    assert geometry["net_section_modulus_mm3"] == pytest.approx(12.244333)
    assert geometry["endpoint_supported_moment_nmm"] == pytest.approx(1177.000338)


def test_thresholds_remain_requirements_not_selected_properties():
    report = metal.build_report()
    requirements = report["requirements_per_unit_demand_factor"]
    assert requirements[
        "whole_barrel_design_resistance_n_before_preload"
    ] == pytest.approx(301.493967)
    assert requirements["female_thread_shear_strength_mpa"] == pytest.approx(7.379561)
    assert requirements["illustrative_lobe_average_shear_mpa"] == pytest.approx(
        18.578899
    )
    assert requirements[
        "illustrative_lobe_bending_yield_mpa_before_kt"
    ] == pytest.approx(96.126131)
    assert report["decision"]["finite_decision"] == "EVIDENCE_BLOCKED"
    assert not report["decision"]["selected_barrel_property_pass"]
    assert not report["decision"]["diy_ready"]
    assert not report["decision"]["structural_released"]
