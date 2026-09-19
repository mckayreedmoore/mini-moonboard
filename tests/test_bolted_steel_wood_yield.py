"""2024 NDS Table 12.3.1A independent equations and Table 12B spot check."""

import math

import pytest

from fea.dowel_yield import single_shear
from mini_moonboard.bolted_steel_wood_yield import wood_steel_single_shear_reference


def nds_2024_modes(d, lm, ls, fem, fes, fyb, angle):
    """Directly transcribe 2024 Table 12.3.1A, with wood as main member."""
    re = fem / fes
    rt = lm / ls
    k1 = (
        math.sqrt(re + 2 * re**2 * (1 + rt + rt**2) + rt**2 * re**3) - re * (1 + rt)
    ) / (1 + re)
    k2 = -1 + math.sqrt(
        2 * (1 + re) + 2 * fyb * (1 + 2 * re) * d**2 / (3 * fem * lm**2)
    )
    k3 = -1 + math.sqrt(
        2 * (1 + re) / re + 2 * fyb * (2 + re) * d**2 / (3 * fem * ls**2)
    )
    kt = 1 + 0.25 * angle / 90
    return {
        "Im": d * lm * fem / (4 * kt),
        "Is": d * ls * fes / (4 * kt),
        "II": k1 * d * ls * fes / (3.6 * kt),
        "IIIm": k2 * d * lm * fem / ((1 + 2 * re) * 3.2 * kt),
        "IIIs": k3 * d * ls * fem / ((2 + re) * 3.2 * kt),
        "IV": d**2 * math.sqrt(2 * fem * fyb / (3 * (1 + re))) / (3.2 * kt),
    }


@pytest.mark.parametrize(
    "d,lm,ls,fem,fes,fyb,angle",
    [
        (0.5, 1.5, 0.25, 5600, 87000, 45000, 0),
        (0.5, 1.5, 0.25, 3300, 87000, 45000, 90),
        (0.375, 2.0, 0.125, 4800, 61000, 65000, 35),
        (0.75, 3.5, 0.5, 3900, 45000, 90000, 70),
    ],
)
def test_existing_solver_matches_all_six_2024_equations(
    d, lm, ls, fem, fes, fyb, angle
):
    kt = 1 + 0.25 * angle / 90
    result = single_shear(
        main_length_in=lm,
        side_length_in=ls,
        main_bearing_lb_in=d * fem,
        side_bearing_lb_in=d * fes,
        main_yield_moment_lb_in=fyb * d**3 / 6,
        side_yield_moment_lb_in=fyb * d**3 / 6,
        gap_in=0,
        reduction_terms={
            "Im": 4 * kt,
            "Is": 4 * kt,
            "II": 3.6 * kt,
            "IIIm": 3.2 * kt,
            "IIIs": 3.2 * kt,
            "IV": 3.2 * kt,
        },
    )
    assert result["reference_values_lbf"] == pytest.approx(
        nds_2024_modes(d, lm, ls, fem, fes, fyb, angle), rel=1e-12
    )


def test_2024_table_12b_df_l_cell_under_exact_table_assumptions():
    # AWC 2024 NDS p.103: t_m=1.5, t_s=0.25 A36, D=0.5 full body,
    # Fyb=45 ksi, steel Fe=87 ksi; DF-L G=.50 column: 580/310 lbf.
    for angle, published in ((0, 580), (90, 310)):
        result = wood_steel_single_shear_reference(
            bolt_full_body_diameter_in=0.5,
            bolt_thread_root_diameter_in=0.4,
            wood_thread_bearing_length_in=0,
            steel_thread_bearing_length_in=0,
            bolt_bending_yield_psi=45000,
            steel_bearing_psi=87000,
            wood_bearing_length_in=1.5,
            steel_thickness_in=0.25,
            grain_load_angle_degrees=angle,
        )
        assert result["reference_lateral_lbf"] == pytest.approx(published, abs=6)
        assert result["reference_lateral_lbf"] == min(
            result["reference_values_lbf"].values()
        )


def test_product_inputs_change_result_and_include_all_modes():
    case = {
        "bolt_full_body_diameter_in": 0.375,
        "bolt_thread_root_diameter_in": 0.3,
        "wood_thread_bearing_length_in": 0,
        "steel_thread_bearing_length_in": 0,
        "bolt_bending_yield_psi": 45000,
        "steel_bearing_psi": 87000,
        "wood_bearing_length_in": 1.5,
        "steel_thickness_in": 0.25,
        "grain_load_angle_degrees": 30,
    }
    result = wood_steel_single_shear_reference(**case)
    assert set(result["reference_values_lbf"]) == {
        "Im",
        "Is",
        "II",
        "IIIm",
        "IIIs",
        "IV",
    }
    assert result["wood_bearing_psi"] > 0
    for name, changed in (
        ("steel_bearing_psi", 40000),
        ("steel_thickness_in", 0.125),
        ("bolt_bending_yield_psi", 90000),
        ("grain_load_angle_degrees", 90),
    ):
        assert (
            wood_steel_single_shear_reference(**(case | {name: changed}))[
                "reference_values_lbf"
            ]
            != result["reference_values_lbf"]
        )


def test_thread_exposure_selects_root_diameter_when_quarter_limit_exceeded():
    case = {
        "bolt_full_body_diameter_in": 0.375,
        "bolt_thread_root_diameter_in": 0.3,
        "wood_thread_bearing_length_in": 0,
        "steel_thread_bearing_length_in": 0,
        "bolt_bending_yield_psi": 45000,
        "steel_bearing_psi": 87000,
        "wood_bearing_length_in": 1.5,
        "steel_thickness_in": 0.25,
        "grain_load_angle_degrees": 0,
    }
    full = wood_steel_single_shear_reference(**case)
    boundary = wood_steel_single_shear_reference(
        **(case | {"steel_thread_bearing_length_in": 0.25 / 4})
    )
    threaded = wood_steel_single_shear_reference(
        **(case | {"steel_thread_bearing_length_in": 0.25 / 4 + 0.001})
    )
    assert (
        full["effective_bolt_diameter_in"]
        == boundary["effective_bolt_diameter_in"]
        == 0.375
    )
    assert threaded["effective_bolt_diameter_in"] == 0.3
    assert threaded["reference_values_lbf"] != full["reference_values_lbf"]


def test_subquarter_thread_root_rejected_if_required():
    with pytest.raises(ValueError, match="effective bolt diameter"):
        wood_steel_single_shear_reference(
            bolt_full_body_diameter_in=0.25,
            bolt_thread_root_diameter_in=0.2,
            wood_thread_bearing_length_in=0.5,
            steel_thread_bearing_length_in=0,
            bolt_bending_yield_psi=45000,
            steel_bearing_psi=87000,
            wood_bearing_length_in=1.5,
            steel_thickness_in=0.25,
            grain_load_angle_degrees=0,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("bolt_full_body_diameter_in", 0.249),
        ("bolt_full_body_diameter_in", 1.01),
        ("bolt_thread_root_diameter_in", 0),
        ("bolt_thread_root_diameter_in", 0.5),
        ("wood_thread_bearing_length_in", -0.1),
        ("steel_thread_bearing_length_in", 0.3),
        ("bolt_bending_yield_psi", 0),
        ("steel_bearing_psi", math.nan),
        ("wood_bearing_length_in", -1),
        ("steel_thickness_in", 0),
        ("grain_load_angle_degrees", 91),
        ("grain_load_angle_degrees", math.inf),
    ],
)
def test_invalid_inputs_rejected(field, value):
    case = {
        "bolt_full_body_diameter_in": 0.375,
        "bolt_thread_root_diameter_in": 0.3,
        "wood_thread_bearing_length_in": 0,
        "steel_thread_bearing_length_in": 0,
        "bolt_bending_yield_psi": 45000,
        "steel_bearing_psi": 87000,
        "wood_bearing_length_in": 1.5,
        "steel_thickness_in": 0.25,
        "grain_load_angle_degrees": 0,
    }
    with pytest.raises(ValueError):
        wood_steel_single_shear_reference(**(case | {field: value}))


def test_missing_product_property_rejected():
    case = {
        "bolt_full_body_diameter_in": 0.375,
        "bolt_thread_root_diameter_in": 0.3,
        "wood_thread_bearing_length_in": 0,
        "steel_thread_bearing_length_in": 0,
        "bolt_bending_yield_psi": 45000,
        "steel_bearing_psi": 87000,
        "wood_bearing_length_in": 1.5,
        "steel_thickness_in": 0.25,
        "grain_load_angle_degrees": 0,
    }
    for missing in case:
        with pytest.raises(TypeError):
            wood_steel_single_shear_reference(
                **{k: v for k, v in case.items() if k != missing}
            )
