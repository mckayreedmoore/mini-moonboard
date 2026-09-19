"""2018 NDS benchmarks only; these do not qualify a 2024 joint design.

Source: AWC, 2018 NDS, printed p. 94, Table 12A (DF-L, G=0.50),
https://plib.org/wp-content/uploads/2020/09/AWC-NDS2018.pdf.
Inputs follow 2018 Tables 12.3.3 and 12.3.1B. Table 12A rounds Z to 10 lbf.
No 2024 NDS or Supplement values are asserted or released by these tests.
"""

import math

import pytest

from fea.dowel_yield import single_shear

SPECIFIC_GRAVITY = 0.50
FYB_PSI = 45_000


def benchmark_inputs(
    main_length_in, side_length_in, diameter_in, main_angle_deg, side_angle_deg
):
    """Build the publisher's full-body, two-member, zero-gap comparison case."""
    fe_parallel_psi = 11_200 * SPECIFIC_GRAVITY
    fe_perpendicular_psi = 6_100 * SPECIFIC_GRAVITY**1.45 / math.sqrt(diameter_in)
    main_fe_psi = fe_parallel_psi if main_angle_deg == 0 else fe_perpendicular_psi
    side_fe_psi = fe_parallel_psi if side_angle_deg == 0 else fe_perpendicular_psi
    k_theta = 1 + 0.25 * max(main_angle_deg, side_angle_deg) / 90
    return {
        "main_length_in": main_length_in,
        "side_length_in": side_length_in,
        "main_bearing_lb_in": main_fe_psi * diameter_in,
        "side_bearing_lb_in": side_fe_psi * diameter_in,
        "main_yield_moment_lb_in": FYB_PSI * diameter_in**3 / 6,
        "side_yield_moment_lb_in": FYB_PSI * diameter_in**3 / 6,
        "gap_in": 0,
        "reduction_terms": {
            "Im": 4 * k_theta,
            "Is": 4 * k_theta,
            "II": 3.6 * k_theta,
            "IIIm": 3.2 * k_theta,
            "IIIs": 3.2 * k_theta,
            "IV": 3.2 * k_theta,
        },
    }


# (main, side, governing mode, parallel/parallel,
#  main parallel/side perpendicular, perpendicular/perpendicular), inches and
# lbf; directly transcribed from
# the DF-L G=0.50 column of the publisher's 2018 Table 12A.
PUBLISHED_2018_TABLE_12A = (
    (1.5, 1.5, "II", 480, 300, 220),
    (3.5, 1.5, "IIIs", 610, 370, 330),
    (3.5, 3.5, "IV", 720, 490, 430),
)


@pytest.mark.parametrize(
    "main,side,governing,parallel,mixed,perpendicular", PUBLISHED_2018_TABLE_12A
)
@pytest.mark.parametrize(
    "main_angle,side_angle,column",
    [
        (0, 0, "parallel"),
        (0, 90, "mixed"),
        (90, 90, "perpendicular"),
    ],
)
def test_2018_nds_table_12a_df_l_half_inch_bolt(
    main,
    side,
    governing,
    parallel,
    mixed,
    perpendicular,
    main_angle,
    side_angle,
    column,
):
    published_lbf = {
        "parallel": parallel,
        "mixed": mixed,
        "perpendicular": perpendicular,
    }[column]
    result = single_shear(**benchmark_inputs(main, side, 0.5, main_angle, side_angle))
    assert result["governing_mode"] == governing
    assert result["reference_lateral_lbf"] == pytest.approx(published_lbf, abs=6)
    assert result["reference_lateral_lbf"] == pytest.approx(
        min(result["reference_values_lbf"].values())
    )


def test_independent_three_eighths_inch_parallel_case():
    """Independent worksheet: q=2100 lbf/in, M=395.5078125 lbf-in.

    For equal 1.5-inch bearing lengths, mode II's quadratic reduces to
    P = q*l/(1 + sqrt(2)); Z = P/3.6 = 362.44 lbf.
    """
    diameter_in = 3 / 8
    inputs = benchmark_inputs(1.5, 1.5, diameter_in, 0, 0)
    assert inputs["main_bearing_lb_in"] == pytest.approx(2_100)
    assert inputs["main_yield_moment_lb_in"] == pytest.approx(395.5078125)
    assert inputs["reduction_terms"]["II"] == pytest.approx(3.6)
    result = single_shear(**inputs)
    independently_derived_lbf = 2_100 * 1.5 / (1 + math.sqrt(2)) / 3.6
    assert result["governing_mode"] == "II"
    assert result["reference_lateral_lbf"] == pytest.approx(
        independently_derived_lbf, abs=0.01
    )


def test_half_inch_mixed_grain_inputs_have_correct_units_and_angle_factor():
    inputs = benchmark_inputs(3.5, 1.5, 0.5, 0, 90)
    assert inputs["main_bearing_lb_in"] == pytest.approx(5_600 * 0.5)
    assert inputs["side_bearing_lb_in"] == pytest.approx(
        (6_100 * 0.50**1.45 / math.sqrt(0.5)) * 0.5
    )
    assert inputs["main_yield_moment_lb_in"] == pytest.approx(937.5)
    assert inputs["side_yield_moment_lb_in"] == pytest.approx(937.5)
    assert inputs["reduction_terms"] == {
        "Im": 5.0,
        "Is": 5.0,
        "II": 4.5,
        "IIIm": 4.0,
        "IIIs": 4.0,
        "IV": 4.0,
    }
