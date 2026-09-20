"""Conditional three-solid-wood-member symmetric double-shear component."""

import math

import pytest

from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi
from mini_moonboard.bolted_wood_wood_double_shear import (
    wood_wood_double_shear_reference,
)


def case():
    return {
        "main_bearing_length_in": 5.5,
        "side_a_bearing_length_in": 1.5,
        "side_b_bearing_length_in": 1.5,
        "main_load_to_grain_degrees": 0.0,
        "side_a_load_to_grain_degrees": 90.0,
        "side_b_load_to_grain_degrees": 90.0,
        "main_bolt_axis_parallel_to_grain": False,
        "side_a_bolt_axis_parallel_to_grain": False,
        "side_b_bolt_axis_parallel_to_grain": False,
        "bolt_full_body_diameter_in": 0.375,
        "bolt_thread_root_diameter_in": 0.30,
        "main_thread_bearing_length_in": 0.0,
        "side_a_thread_bearing_length_in": 0.0,
        "side_b_thread_bearing_length_in": 0.0,
        "bolt_bending_yield_strength_psi": 45_000.0,
        "side_a_gap_in": 0.0,
        "side_b_gap_in": 0.0,
        "symmetric_side_actions_established": True,
    }


def test_four_2024_nds_modes_are_distinct_and_use_two_side_members():
    inputs = case()
    result = wood_wood_double_shear_reference(**inputs)
    d = inputs["bolt_full_body_diameter_in"]
    fe_m = dfl_dowel_bearing_psi(d, 0)
    fe_s = dfl_dowel_bearing_psi(d, 90)
    ktheta = 1.25
    lm, ls = 5.5, 1.5
    assert result["main_bearing_psi"] == pytest.approx(fe_m)
    assert result["side_bearing_psi"] == pytest.approx(fe_s)
    assert result["effective_bolt_diameter_in"] == d
    assert result["effective_side_bearing_length_in"] == ls
    assert set(result["reference_values_lbf"]) == {"Im", "Is", "IIIs", "IV"}
    assert result["reference_values_lbf"]["Im"] == pytest.approx(
        d * lm * fe_m / (4 * ktheta)
    )
    assert result["reference_values_lbf"]["Is"] == pytest.approx(
        2 * d * ls * fe_s / (4 * ktheta)
    )
    # Independent arithmetic fixture for the remaining Table 12.3.1A modes.
    assert result["reference_values_lbf"]["IIIs"] == pytest.approx(498.329031094)
    assert result["reference_values_lbf"]["IV"] == pytest.approx(572.483200066)
    assert result["reference_lateral_lbf"] == pytest.approx(
        min(result["reference_values_lbf"].values())
    )
    assert result["connection_qualified"] is False


def test_lesser_side_length_governs_both_sides_and_threads_select_root():
    inputs = case() | {
        "side_b_bearing_length_in": 1.25,
        "side_b_thread_bearing_length_in": 0.4,
    }
    result = wood_wood_double_shear_reference(**inputs)
    assert result["effective_side_bearing_length_in"] == 1.25
    assert result["effective_bolt_diameter_in"] == 0.30


@pytest.mark.parametrize(
    "changed",
    [
        {"symmetric_side_actions_established": False},
        {"side_a_gap_in": 0.01},
        {"side_b_gap_in": 0.01},
        {"main_bolt_axis_parallel_to_grain": True},
        {"side_b_bolt_axis_parallel_to_grain": True},
        {"side_a_load_to_grain_degrees": 80},
        {"bolt_bending_yield_strength_psi": math.nan},
        {"side_b_bearing_length_in": 0},
        {"side_a_thread_bearing_length_in": 1.6},
        {"bolt_thread_root_diameter_in": 0.20, "side_a_thread_bearing_length_in": 0.5},
    ],
)
def test_nonapplicable_or_invalid_inputs_rejected(changed):
    with pytest.raises(ValueError):
        wood_wood_double_shear_reference(**(case() | changed))
