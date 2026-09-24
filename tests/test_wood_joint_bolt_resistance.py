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


def test_fyb_requires_f1575_or_f606_evidence_for_delivered_fastener():
    missing = nds_fyb_basis_status(
        fyb_psi=None,
        test_method=None,
        evidence_reference=None,
        applies_to_delivered_fastener=None,
    )
    grade_only = nds_fyb_basis_status(
        fyb_psi=45_000,
        test_method="SAE J429 Grade 5 catalog",
        evidence_reference="catalog listing",
        applies_to_delivered_fastener=True,
    )
    sourced = nds_fyb_basis_status(
        fyb_psi=72_000,
        test_method="ASTM F1575",
        evidence_reference="lot report 24-017",
        applies_to_delivered_fastener=True,
    )

    assert missing["status"] == "unresolved"
    assert missing["fyb_psi"] is None
    assert grade_only["status"] == "unresolved"
    assert grade_only["fyb_psi"] is None
    assert sourced["status"] == "basis_recorded"
    assert sourced["fyb_psi"] == 72_000


def test_bolt_tension_and_shear_yield_references_are_separate():
    result = bolt_first_yield_reference(
        axial_force_n=5_000,
        lateral_shear_vector_n=(3_000, 4_000),
        minimum_tensile_area_mm2=100,
        shear_plane_area_mm2=80,
        certified_min_yield_mpa=250,
        material_basis="certified ASTM product standard; lot report 24-017",
        tensile_area_basis="minimum measured threaded section area",
        shear_area_basis="root area at wood shear plane, measured lot report 24-017",
    )

    assert result["status"] == "component_references_only"
    assert result["lateral_shear_demand_n"] == pytest.approx(5_000)
    assert result["tension_first_yield_reference_n"] == pytest.approx(25_000)
    assert result["shear_first_yield_reference_n"] == pytest.approx(
        80 * 250 / math.sqrt(3)
    )
    assert result["tension_first_yield_utilization"] == pytest.approx(0.2)
    assert result["shear_first_yield_utilization"] == pytest.approx(
        5_000 / (80 * 250 / math.sqrt(3))
    )
    assert result["interaction_rule"] == "unresolved"
    assert result["interaction_utilization"] is None


def test_missing_bolt_material_inputs_fail_closed():
    result = bolt_first_yield_reference(
        axial_force_n=-1_000,
        lateral_shear_vector_n=(0, 0),
        minimum_tensile_area_mm2=None,
        shear_plane_area_mm2=None,
        certified_min_yield_mpa=None,
        material_basis=None,
        tensile_area_basis=None,
        shear_area_basis=None,
    )

    assert result["status"] == "unresolved"
    assert result["axial_tension_demand_n"] == 0
    assert result["tension_first_yield_reference_n"] is None
    assert result["shear_first_yield_reference_n"] is None
    assert result["interaction_utilization"] is None
    assert len(result["missing"]) == 6


def test_washer_annulus_only_reports_idealized_wood_reference():
    result = wood_washer_annulus_reference_lbf(
        washer_outer_diameter_in=1.0,
        washer_inner_diameter_in=0.438,
        wood_bore_diameter_in=0.438,
    )

    assert result["status"] == "conditional_wood_reference_only"
    assert result["wood_bearing_reference_lbf"] == pytest.approx(397, abs=1)
    assert result["washer_steel_bending_spreading"] == "unresolved"
    assert washer_steel_resistance_status()["resistance_n"] is None


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
