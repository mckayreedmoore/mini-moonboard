"""Known-answer controls for the elastic serial-row benchmark."""

from __future__ import annotations

import math

import pytest

from mini_moonboard.serial_row_benchmark import (
    IN_TO_MM,
    LBF_TO_N,
    compare_serial_row_to_nds,
    imperial_row_inputs_to_si,
    solve_serial_row,
)


def test_caltrans_example_12_serial_distribution_matches_nds_equation():
    # Caltrans Falsework Manual Appendix D, Example 12, printed D-12-4/5.
    result = compare_serial_row_to_nds(
        fastener_count=3,
        diameter_in=0.625,
        pitch_in=2.5,
        elastic_modulus_main_psi=1_600_000.0,
        area_main_in2=144.0,
        elastic_modulus_side_psi=1_600_000.0,
        area_side_in2=10.88,
    )

    assert result.nds_gamma_lbf_per_in == pytest.approx(88939.05919223567)
    assert result.nds_cg == pytest.approx(0.9806318451462117, rel=1e-13)
    assert result.distribution.bolt_force_fractions == pytest.approx(
        (0.32826923206889, 0.33181387151048, 0.33991689642063), rel=1e-11
    )
    assert result.distribution.max_force_fastener_index == 3
    assert result.distribution.cg_from_distribution == pytest.approx(
        0.9806318451462125, rel=1e-12
    )
    assert result.matches_within_tolerance
    assert result.distribution.total_transferred_force == pytest.approx(1.0)
    assert result.distribution.force_balance_relative_residual < 1e-12
    assert result.distribution.boundary_condition == (
        "+P on main at first row station; -P on side at last row station"
    )
    assert result.comparison_scope == (
        "synthetic two-member wood-to-wood elastic serial row only; no candidate Cg"
    )


def test_imperial_to_si_conversion_preserves_caltrans_force_fractions():
    imperial = compare_serial_row_to_nds(
        fastener_count=3,
        diameter_in=0.625,
        pitch_in=2.5,
        elastic_modulus_main_psi=1_600_000.0,
        area_main_in2=144.0,
        elastic_modulus_side_psi=1_600_000.0,
        area_side_in2=10.88,
    )
    si_inputs = imperial_row_inputs_to_si(
        pitch_in=2.5,
        ea_main_lbf=1_600_000.0 * 144.0,
        ea_side_lbf=1_600_000.0 * 10.88,
        slip_modulus_lbf_per_in=imperial.nds_gamma_lbf_per_in,
    )
    si = solve_serial_row(fastener_count=3, **si_inputs)

    assert si_inputs["pitch"] == pytest.approx(2.5 * IN_TO_MM)
    assert si_inputs["ea_main"] == pytest.approx(1_600_000.0 * 144.0 * LBF_TO_N)
    assert si_inputs["slip_modulus"] == pytest.approx(
        imperial.nds_gamma_lbf_per_in * LBF_TO_N / IN_TO_MM
    )
    assert si.bolt_force_fractions == pytest.approx(
        imperial.distribution.bolt_force_fractions, rel=2e-12, abs=2e-14
    )
    assert si.cg_from_distribution == pytest.approx(
        imperial.distribution.cg_from_distribution, rel=2e-12
    )
    assert si.total_transferred_force == pytest.approx(LBF_TO_N)


def test_single_connector_is_unit_sharing_mechanics_control():
    result = solve_serial_row(
        fastener_count=1,
        pitch=50.0,
        ea_main=2.0e6,
        ea_side=0.5e6,
        slip_modulus=120_000.0,
        load=750.0,
    )

    assert result.bolt_forces == pytest.approx((750.0,))
    assert result.bolt_force_fractions == pytest.approx((1.0,))
    assert result.cg_from_distribution == pytest.approx(1.0)
    assert result.force_balance_residual == pytest.approx(0.0, abs=1e-12)


def test_swapping_member_ea_reverses_distribution_without_changing_factor():
    shared = {
        "fastener_count": 5,
        "pitch": 63.5,
        "slip_modulus": 225_000.0,
        "load": 1000.0,
    }
    original = solve_serial_row(
        **shared, ea_main=180_000_000.0, ea_side=37_000_000.0
    )
    swapped = solve_serial_row(
        **shared, ea_main=37_000_000.0, ea_side=180_000_000.0
    )

    assert swapped.bolt_force_fractions == pytest.approx(
        tuple(reversed(original.bolt_force_fractions)), rel=1e-11
    )
    assert swapped.cg_from_distribution == pytest.approx(
        original.cg_from_distribution, rel=1e-11
    )


@pytest.mark.parametrize(
    ("count", "diameter", "pitch", "em", "am", "es", "area_s"),
    [
        (2, 0.5, 3.0, 1_400_000.0, 12.0, 1_100_000.0, 4.5),
        (4, 0.375, 2.0, 1_000_000.0, 80.0, 1_600_000.0, 21.0),
    ],
)
def test_unequal_ea_rows_of_two_or_more_bolts_match_nds_equation(
    count, diameter, pitch, em, am, es, area_s
):
    result = compare_serial_row_to_nds(
        fastener_count=count,
        diameter_in=diameter,
        pitch_in=pitch,
        elastic_modulus_main_psi=em,
        area_main_in2=am,
        elastic_modulus_side_psi=es,
        area_side_in2=area_s,
        load_lbf=1375.0,
    )

    assert result.matches_within_tolerance
    assert result.distribution.fastener_count == count
    assert math.fsum(result.distribution.bolt_force_fractions) == pytest.approx(1.0)
    assert result.distribution.force_balance_relative_residual < 1e-11
    assert result.distribution.cg_from_distribution == pytest.approx(
        result.nds_cg, rel=1e-10, abs=1e-12
    )


@pytest.mark.parametrize(
    ("override",),
    [
        ({"fastener_count": 0},),
        ({"fastener_count": True},),
        ({"fastener_count": 2.5},),
        ({"pitch": 0.0},),
        ({"pitch": math.inf},),
        ({"ea_main": 0.0},),
        ({"ea_side": -1.0},),
        ({"slip_modulus": math.nan},),
        ({"slip_modulus": 0.0},),
        ({"load": 0.0},),
    ],
)
def test_serial_solver_rejects_invalid_inputs(override):
    inputs = {
        "fastener_count": 3,
        "pitch": 2.5,
        "ea_main": 230_400_000.0,
        "ea_side": 17_408_000.0,
        "slip_modulus": 88_939.05919223567,
        "load": 1.0,
    }
    inputs.update(override)

    with pytest.raises(ValueError):
        solve_serial_row(**inputs)


@pytest.mark.parametrize("diameter", [0.0, 0.249, 1.001, math.inf])
def test_nds_comparison_rejects_diameter_outside_equation_boundary(diameter):
    with pytest.raises(ValueError):
        compare_serial_row_to_nds(
            fastener_count=3,
            diameter_in=diameter,
            pitch_in=2.5,
            elastic_modulus_main_psi=1_600_000.0,
            area_main_in2=144.0,
            elastic_modulus_side_psi=1_600_000.0,
            area_side_in2=10.88,
        )
