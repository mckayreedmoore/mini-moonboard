"""2024 NDS equation checks and an independent published-table cross-check."""

import math

import pytest

from mini_moonboard.bolted_steel_wood_double_shear import (
    wood_steel_double_shear_reference,
)
from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi

CASE = {
    "bolt_full_body_diameter_in": 0.5,
    "bolt_thread_root_diameter_in": 0.4,
    "wood_thread_bearing_length_in": 0,
    "steel_side_a_thread_bearing_length_in": 0,
    "steel_side_b_thread_bearing_length_in": 0,
    "bolt_bending_yield_psi": 45000,
    "steel_bearing_psi": 87000,
    "wood_bearing_length_in": 1.5,
    "steel_side_a_bearing_length_in": 0.25,
    "steel_side_b_bearing_length_in": 0.25,
    "grain_load_angle_degrees": 0,
    "symmetric_side_actions_established": True,
}


def expected_modes(
    diameter,
    wood_length,
    side_length,
    wood_bearing,
    steel_bearing,
    bending_yield,
    angle,
):
    """Direct transcription of double-shear equations 12.3-7 through 12.3-10."""
    ratio = wood_bearing / steel_bearing
    k3 = -1 + math.sqrt(
        2 * (1 + ratio) / ratio
        + 2
        * bending_yield
        * (2 + ratio)
        * diameter**2
        / (3 * wood_bearing * side_length**2)
    )
    ktheta = 1 + 0.25 * angle / 90
    return {
        "Im": diameter * wood_length * wood_bearing / (4 * ktheta),
        "Is": 2 * diameter * side_length * steel_bearing / (4 * ktheta),
        "IIIs": 2
        * k3
        * diameter
        * side_length
        * wood_bearing
        / ((2 + ratio) * 3.2 * ktheta),
        "IV": 2
        * diameter**2
        / (3.2 * ktheta)
        * math.sqrt(2 * wood_bearing * bending_yield / (3 * (1 + ratio))),
    }


@pytest.mark.parametrize("diameter,angle", [(0.5, 0), (0.5, 90), (0.375, 35)])
def test_four_modes_match_2024_nds_equations(diameter, angle):
    case = CASE | {
        "bolt_full_body_diameter_in": diameter,
        "bolt_thread_root_diameter_in": diameter * 0.8,
        "grain_load_angle_degrees": angle,
    }
    result = wood_steel_double_shear_reference(**case)
    expected = expected_modes(
        diameter,
        1.5,
        0.25,
        dfl_dowel_bearing_psi(diameter, angle),
        87000,
        45000,
        angle,
    )
    assert result["reference_values_lbf"] == pytest.approx(expected, rel=1e-12)
    assert result["reference_lateral_lbf"] == min(expected.values())
    assert result["governing_mode"] == min(expected, key=expected.get)
    assert result["effective_bolt_diameter_in"] == diameter
    assert "unadjusted" in result["limits"]
    assert "AB205" in result["limits"]
    assert "not a complete joint" in result["limits"]


@pytest.mark.parametrize("angle,published_rounded_lbf", [(0, 1050), (90, 470)])
def test_historical_awc_table_12g_cross_checks_formula_not_candidate(angle, published_rounded_lbf):
    """2018 AWC Table 12G's published DF-L row is independent QA, not design authority.

    Its 1.5-in wood / 1/4-in A36 sides / 1/2-in bolt row uses 87,000 psi
    steel bearing and 45,000 psi bolt bending yield. The implemented design
    equation edition remains 2024; these values are never AB205 defaults.
    Source: https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf
    """
    result = wood_steel_double_shear_reference(
        **(CASE | {"grain_load_angle_degrees": angle})
    )
    assert result["reference_lateral_lbf"] == pytest.approx(published_rounded_lbf, abs=5)


def test_unequal_side_lengths_use_lesser_for_both_sides():
    unequal = wood_steel_double_shear_reference(
        **(CASE | {"steel_side_b_bearing_length_in": 0.5})
    )
    equal = wood_steel_double_shear_reference(**CASE)
    assert unequal["effective_steel_side_bearing_length_in"] == 0.25
    assert unequal["reference_values_lbf"] == pytest.approx(
        equal["reference_values_lbf"]
    )


@pytest.mark.parametrize("member", ["wood", "steel_side_a", "steel_side_b"])
def test_thread_exposure_in_each_member_selects_root_diameter(member):
    field = f"{member}_thread_bearing_length_in"
    length = CASE[f"{member}_bearing_length_in"]
    boundary = wood_steel_double_shear_reference(**(CASE | {field: length / 4}))
    threaded = wood_steel_double_shear_reference(**(CASE | {field: length / 4 + 0.001}))
    assert boundary["effective_bolt_diameter_in"] == 0.5
    assert threaded["effective_bolt_diameter_in"] == 0.4


def test_rejected_without_explicit_symmetric_action_gate():
    with pytest.raises(TypeError):
        wood_steel_double_shear_reference(
            **{
                key: value
                for key, value in CASE.items()
                if key != "symmetric_side_actions_established"
            }
        )
    for value in (False, 1, "true"):
        with pytest.raises(ValueError, match="symmetric"):
            wood_steel_double_shear_reference(
                **(CASE | {"symmetric_side_actions_established": value})
            )


@pytest.mark.parametrize(
    "field,value",
    [
        ("bolt_full_body_diameter_in", 0.24),
        ("bolt_full_body_diameter_in", 1.01),
        ("bolt_thread_root_diameter_in", 0),
        ("bolt_thread_root_diameter_in", 0.6),
        ("wood_thread_bearing_length_in", -0.01),
        ("steel_side_a_thread_bearing_length_in", 0.3),
        ("steel_side_b_thread_bearing_length_in", 0.3),
        ("bolt_bending_yield_psi", 0),
        ("steel_bearing_psi", math.nan),
        ("wood_bearing_length_in", -1),
        ("steel_side_a_bearing_length_in", 0),
        ("steel_side_b_bearing_length_in", math.inf),
        ("grain_load_angle_degrees", 91),
        ("grain_load_angle_degrees", math.nan),
        ("steel_bearing_psi", True),
    ],
)
def test_invalid_inputs_rejected(field, value):
    with pytest.raises(ValueError):
        wood_steel_double_shear_reference(**(CASE | {field: value}))


def test_root_below_quarter_inch_rejected_when_threads_exceed_quarter_length():
    with pytest.raises(ValueError, match="effective bolt diameter"):
        wood_steel_double_shear_reference(
            **(
                CASE
                | {
                    "bolt_full_body_diameter_in": 0.25,
                    "bolt_thread_root_diameter_in": 0.2,
                    "steel_side_b_thread_bearing_length_in": 0.1,
                }
            )
        )


@pytest.mark.parametrize(
    "field", [key for key in CASE if key != "symmetric_side_actions_established"]
)
def test_all_product_and_geometry_inputs_required(field):
    with pytest.raises(TypeError):
        wood_steel_double_shear_reference(
            **{key: value for key, value in CASE.items() if key != field}
        )
