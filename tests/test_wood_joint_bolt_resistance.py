"""Unit checks for conditional bolt and washer references."""

import math

import pytest

from mini_moonboard.wood_joint_bolt_resistance import (
    bolt_first_yield_reference,
    nds_effective_bolt_diameter_in,
    nds_fyb_basis_status,
    washer_steel_resistance_status,
    wood_washer_annulus_reference_lbf,
)


def test_nds_thread_bearing_limit_uses_full_body_only_at_quarter_boundary():
    common = {
        "full_body_diameter_in": 0.25,
        "thread_root_diameter_in": 0.189,
        "threaded_full_body_fastener": True,
        "main_bearing_length_in": 1.5,
        "side_bearing_length_in": 1.5,
        "main_thread_bearing_length_in": 0.375,
        "side_thread_bearing_length_in": 0.375,
    }
    boundary = nds_effective_bolt_diameter_in(**common)
    beyond = nds_effective_bolt_diameter_in(
        **(common | {"side_thread_bearing_length_in": 0.376})
    )

    assert boundary["diameter_case"] == "full_body_D"
    assert boundary["effective_lateral_diameter_in"] == 0.25
    assert boundary["sub_quarter_inch_reduction_required"] is False
    assert beyond["diameter_case"] == "thread_root_Dr"
    assert beyond["effective_lateral_diameter_in"] == 0.189
    assert beyond["sub_quarter_inch_reduction_required"] is True


def test_nds_non_full_body_fastener_uses_root_even_with_short_threads():
    result = nds_effective_bolt_diameter_in(
        full_body_diameter_in=0.5,
        thread_root_diameter_in=0.4,
        threaded_full_body_fastener=False,
        main_bearing_length_in=2.0,
        side_bearing_length_in=2.0,
        main_thread_bearing_length_in=0.0,
        side_thread_bearing_length_in=0.0,
    )
    assert result["effective_lateral_diameter_in"] == 0.4
    assert result["full_body_rule_applied"] is False


def test_fyb_scenario_and_delivered_conformance_are_separate():
    scenario_only = nds_fyb_basis_status(
        fyb_psi=106_000,
        test_method=None,
        evidence_reference="documented Grade 5 Commentary estimate",
        scenario_id="grade-5-commentary-estimate-1/4-in",
    )
    test_basis = nds_fyb_basis_status(
        fyb_psi=72_000,
        test_method="ASTM F1575",
        evidence_reference="test report 24-017",
        scenario_id="lot-24-017-test-result",
    )

    assert scenario_only["status"] == "specified_scenario_recorded"
    assert scenario_only["specified_scenario"]["fyb_psi"] == 106_000
    assert scenario_only["nds_test_basis"]["status"] == "unresolved"
    assert scenario_only["delivered_fastener_conformance"]["status"] == "not_assessed"
    assert test_basis["nds_test_basis"]["status"] == "recorded"
    assert test_basis["delivered_fastener_conformance"]["status"] == "not_assessed"


def test_f606_requires_an_explicit_fyb_derivation_reference():
    result = nds_fyb_basis_status(
        fyb_psi=72_000,
        test_method="ASTM F606",
        evidence_reference="tensile test report 24-017",
        scenario_id="lot-24-017-test-result",
    )
    with_derivation = nds_fyb_basis_status(
        fyb_psi=72_000,
        test_method="ASTM F606",
        evidence_reference="tensile test report 24-017",
        scenario_id="lot-24-017-test-result",
        fyb_derivation_reference="evaluation note 24-017-A",
    )

    assert result["nds_test_basis"]["status"] == "unresolved"
    assert result["nds_test_basis"]["missing"] == [
        "supported F606 tensile-yield-to-Fyb derivation"
    ]
    assert with_derivation["nds_test_basis"]["status"] == "recorded"


def test_bolt_component_references_and_common_section_interaction():
    result = bolt_first_yield_reference(
        axial_force_n=5_000,
        lateral_shear_vector_n=(3_000, 4_000),
        minimum_tensile_area_mm2=100,
        shear_plane_area_mm2=80,
        specified_min_yield_mpa=250,
        property_scenario_id="example-grade-property-scenario",
        material_basis="certified ASTM product standard; lot report 24-017",
        tensile_area_basis="minimum measured threaded section area",
        shear_area_basis="root area at wood shear plane, measured lot report 24-017",
        combined_action_area_mm2=100,
        combined_action_section_basis=(
            "illustrative same threaded section; uniform nominal average shear"
        ),
    )

    assert result["status"] == "material_first_yield_reference_only"
    assert result["lateral_shear_demand_n"] == pytest.approx(5_000)
    assert result["tension_first_yield_reference_n"] == pytest.approx(25_000)
    assert result["shear_first_yield_reference_n"] == pytest.approx(
        80 * 250 / math.sqrt(3)
    )
    assert result["tension_first_yield_utilization"] == pytest.approx(0.2)
    assert result["shear_first_yield_utilization"] == pytest.approx(
        5_000 / (80 * 250 / math.sqrt(3))
    )
    assert result["interaction_rule"] == "nominal_von_mises_same_section_average_shear"
    assert result["interaction_equivalent_stress_mpa"] == pytest.approx(100)
    assert result["interaction_utilization"] == pytest.approx(0.4)
    assert result["delivered_fastener_conformance"]["status"] == "not_assessed"
    assert result["bending_first_yield_status"] == "unresolved_not_evaluated"


def test_bolt_interaction_stays_open_without_a_common_section_basis():
    result = bolt_first_yield_reference(
        axial_force_n=5_000,
        lateral_shear_vector_n=(3_000, 4_000),
        minimum_tensile_area_mm2=100,
        shear_plane_area_mm2=80,
        specified_min_yield_mpa=250,
        property_scenario_id="example-grade-property-scenario",
        material_basis="explicitly specified steel scenario",
        tensile_area_basis="minimum tensile section",
        shear_area_basis="thread-root section at shear plane",
    )

    assert result["status"] == "material_first_yield_reference_only"
    assert result["interaction_rule"] == "unresolved"
    assert result["interaction_utilization"] is None
    assert "one co-located section area" in result["interaction_missing"][0]


def test_missing_bolt_material_inputs_fail_closed():
    result = bolt_first_yield_reference(
        axial_force_n=-1_000,
        lateral_shear_vector_n=(0, 0),
        minimum_tensile_area_mm2=None,
        shear_plane_area_mm2=None,
        specified_min_yield_mpa=None,
        property_scenario_id=None,
        material_basis=None,
        tensile_area_basis=None,
        shear_area_basis=None,
    )

    assert result["status"] == "unresolved"
    assert result["axial_tension_demand_n"] == 0
    assert result["tension_first_yield_reference_n"] is None
    assert result["shear_first_yield_reference_n"] is None
    assert result["interaction_utilization"] is None
    assert len(result["missing"]) == 7


def test_washer_annulus_only_reports_idealized_wood_reference():
    result = wood_washer_annulus_reference_lbf(
        washer_outer_diameter_in=1.0,
        washer_inner_diameter_in=0.438,
        wood_bore_diameter_in=0.438,
    )

    assert result["status"] == "conditional_wood_reference_only"
    assert result["wood_bearing_reference_lbf"] == pytest.approx(397, abs=1)
    assert result["washer_steel_bending_spreading"] == "unresolved"
    steel = washer_steel_resistance_status(
        scenario_id="type-a-wide-plain-steel-reference",
        washer_standard="ASME B18.21.1 Type A wide",
        material_basis="unspecified plain steel scenario",
        outer_diameter_in=0.75,
        inner_diameter_in=0.312,
        thickness_in=0.06,
        specified_yield_strength_psi=36_000,
        evidence_reference="illustrative dimensional/material scenario",
    )
    assert steel["status"] == "method_gap"
    assert steel["specified_scenario_status"] == "recorded"
    assert steel["resistance_n"] is None
    assert steel["delivered_washer_conformance"]["status"] == "not_assessed"
    assert steel["method_gap"]["id"] == "washer_steel_bending_and_load_spreading_on_timber"


def test_delivery_status_requires_evidence_and_never_authenticates_it():
    result = nds_fyb_basis_status(
        fyb_psi=72_000,
        test_method="ASTM F1575",
        evidence_reference="lot report 24-017",
        scenario_id="lot-24-017-test-result",
        delivered_conformance_status="conforming",
        delivered_evidence_reference="receiving inspection 2026-09-26",
    )

    assert result["specified_scenario"]["status"] == "recorded"
    assert result["delivered_fastener_conformance"]["status"] == "recorded_by_caller"
    assert result["delivered_fastener_conformance"]["recorded_conformance"] == "conforming"
    assert "does not authenticate" in result["delivered_fastener_conformance"]["limits"]
    with pytest.raises(ValueError, match="requires an evidence reference"):
        nds_fyb_basis_status(
            fyb_psi=72_000,
            test_method="ASTM F1575",
            evidence_reference="test report 24-017",
            scenario_id="lot-24-017-test-result",
            delivered_conformance_status="conforming",
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"main_thread_bearing_length_in": 1.6},
        {"threaded_full_body_fastener": 1},
        {"thread_root_diameter_in": math.nan},
    ],
)
def test_nds_diameter_rejects_invalid_measurements(changes):
    inputs = {
        "full_body_diameter_in": 0.25,
        "thread_root_diameter_in": 0.189,
        "threaded_full_body_fastener": True,
        "main_bearing_length_in": 1.5,
        "side_bearing_length_in": 1.5,
        "main_thread_bearing_length_in": 0.0,
        "side_thread_bearing_length_in": 0.0,
    }
    with pytest.raises(ValueError):
        nds_effective_bolt_diameter_in(**(inputs | changes))
