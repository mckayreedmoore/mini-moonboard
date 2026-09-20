"""Conditional 2024 NDS single-fastener, two-solid-DF-L-member component tests."""

import math

import pytest

from fea.dowel_yield import single_shear
from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi
from mini_moonboard.bolted_wood_wood_yield import (
    dowel_bending_yield_moment_lb_in,
    wood_wood_single_shear_reference,
)


def test_dowel_bending_moment_uses_tr12_effective_diameter_cubed():
    assert dowel_bending_yield_moment_lb_in(
        bending_yield_strength_psi=45_000, effective_diameter_in=0.5
    ) == pytest.approx(937.5)
    assert dowel_bending_yield_moment_lb_in(
        bending_yield_strength_psi=45_000, effective_diameter_in=0.4
    ) == pytest.approx(480)


@pytest.mark.parametrize("strength,diameter", [
    (0, 0.5), (math.nan, 0.5), (45_000, 0), (45_000, math.inf),
    (True, 0.5), (45_000, False), (1e308, 1e308),
])
def test_dowel_bending_moment_rejects_unqualified_numeric_inputs(strength, diameter):
    with pytest.raises(ValueError):
        dowel_bending_yield_moment_lb_in(
            bending_yield_strength_psi=strength,
            effective_diameter_in=diameter,
        )


def case():
    angle_factor = 1 + 0.25 * 90 / 90
    return {
        "main_bearing_length_in": 1.5,
        "side_bearing_length_in": 1.5,
        "main_load_to_grain_degrees": 0,
        "side_load_to_grain_degrees": 90,
        "main_bolt_axis_parallel_to_grain": False,
        "side_bolt_axis_parallel_to_grain": False,
        "bolt_full_body_diameter_in": 0.5,
        "bolt_thread_root_diameter_in": 0.4,
        "main_thread_bearing_length_in": 0,
        "side_thread_bearing_length_in": 0,
        "bolt_bending_yield_moment_lb_in": 45_000 * 0.5**3 / 6,
        "gap_in": 0,
        "reduction_terms": {
            "Im": 4 * angle_factor,
            "Is": 4 * angle_factor,
            "II": 3.6 * angle_factor,
            "IIIm": 3.2 * angle_factor,
            "IIIs": 3.2 * angle_factor,
            "IV": 3.2 * angle_factor,
        },
    }


def test_matches_explicit_two_member_six_mode_solver():
    inputs = case()
    result = wood_wood_single_shear_reference(**inputs)
    main_fe = dfl_dowel_bearing_psi(0.5, 0)
    side_fe = dfl_dowel_bearing_psi(0.5, 90)
    direct = single_shear(
        main_length_in=1.5,
        side_length_in=1.5,
        main_bearing_lb_in=main_fe * 0.5,
        side_bearing_lb_in=side_fe * 0.5,
        main_yield_moment_lb_in=inputs["bolt_bending_yield_moment_lb_in"],
        side_yield_moment_lb_in=inputs["bolt_bending_yield_moment_lb_in"],
        gap_in=0,
        reduction_terms=inputs["reduction_terms"],
    )
    assert result["main_bearing_psi"] == main_fe
    assert result["side_bearing_psi"] == side_fe
    assert result["effective_bearing_diameter_in"] == 0.5
    assert result["reference_values_lbf"] == pytest.approx(direct["reference_values_lbf"])
    assert result["governing_mode"] == direct["governing_mode"]
    assert result["reference_lateral_lbf"] == pytest.approx(direct["reference_lateral_lbf"])


def test_separate_angles_and_member_lengths_change_their_mode_values():
    inputs = case()
    baseline = wood_wood_single_shear_reference(**inputs)
    reversed_grain = wood_wood_single_shear_reference(
        **(inputs | {"main_load_to_grain_degrees": 90,
                     "side_load_to_grain_degrees": 0})
    )
    shorter_side = wood_wood_single_shear_reference(
        **(inputs | {"side_bearing_length_in": 0.75})
    )
    assert reversed_grain["main_bearing_psi"] != baseline["main_bearing_psi"]
    assert reversed_grain["side_bearing_psi"] != baseline["side_bearing_psi"]
    assert shorter_side["reference_values_lbf"]["Is"] < baseline["reference_values_lbf"]["Is"]


def test_thread_exposure_in_either_member_selects_root_diameter():
    inputs = case()
    boundary = wood_wood_single_shear_reference(
        **(inputs | {"side_thread_bearing_length_in": 1.5 / 4})
    )
    threaded = wood_wood_single_shear_reference(
        **(inputs | {"side_thread_bearing_length_in": 1.5 / 4 + 0.001,
                     "bolt_bending_yield_moment_lb_in": 45_000 * 0.4**3 / 6})
    )
    assert boundary["effective_bearing_diameter_in"] == 0.5
    assert threaded["effective_bearing_diameter_in"] == 0.4
    assert threaded["reference_values_lbf"] != boundary["reference_values_lbf"]


@pytest.mark.parametrize("field,value", [
    ("main_bearing_length_in", 0),
    ("side_bearing_length_in", math.nan),
    ("main_load_to_grain_degrees", -1),
    ("side_load_to_grain_degrees", 91),
    ("bolt_full_body_diameter_in", 0.249),
    ("bolt_full_body_diameter_in", 1.01),
    ("bolt_thread_root_diameter_in", 0),
    ("bolt_thread_root_diameter_in", 0.51),
    ("main_thread_bearing_length_in", -0.01),
    ("side_thread_bearing_length_in", 1.51),
    ("bolt_bending_yield_moment_lb_in", math.inf),
    ("main_bolt_axis_parallel_to_grain", True),
    ("side_bolt_axis_parallel_to_grain", True),
    ("gap_in", 0.01),
    ("reduction_terms", {"Im": 5}),
    ("reduction_terms", {"Im": 1, "Is": 5, "II": 4.5,
                         "IIIm": 4, "IIIs": 4, "IV": 4}),
])
def test_out_of_scope_or_invalid_inputs_rejected(field, value):
    with pytest.raises(ValueError):
        wood_wood_single_shear_reference(**(case() | {field: value}))


def test_reduction_terms_use_maximum_of_two_grain_angles():
    inputs = case()
    with pytest.raises(ValueError, match="reduction terms"):
        wood_wood_single_shear_reference(
            **(inputs | {"reduction_terms": {
                "Im": 4, "Is": 4, "II": 3.6,
                "IIIm": 3.2, "IIIs": 3.2, "IV": 3.2,
            }})
        )


@pytest.mark.parametrize("root,kd", [
    (0.1699, 2.2), (0.17, 2.2), (0.1701, 2.201), (0.2, 2.5), (0.2499, 2.999),
])
@pytest.mark.parametrize("threaded_member", ["main", "side"])
def test_subquarter_root_uses_small_dowel_bearing_and_all_mode_reductions(
    root, kd, threaded_member
):
    inputs = case() | {
        "bolt_full_body_diameter_in": 0.25,
        "bolt_thread_root_diameter_in": root,
        f"{threaded_member}_thread_bearing_length_in": 0.5,
        "bolt_bending_yield_strength_psi": 45_000,
        "bolt_bending_yield_moment_lb_in": 45_000 * root**3 / 6,
    }
    kt = 1.25
    reductions = dict.fromkeys(("Im", "Is", "II", "IIIm", "IIIs", "IV"), kd * kt)
    inputs["reduction_terms"] = reductions
    result = wood_wood_single_shear_reference(**inputs)
    direct = single_shear(
        main_length_in=1.5, side_length_in=1.5,
        main_bearing_lb_in=4650 * root, side_bearing_lb_in=4650 * root,
        main_yield_moment_lb_in=inputs["bolt_bending_yield_moment_lb_in"],
        side_yield_moment_lb_in=inputs["bolt_bending_yield_moment_lb_in"],
        gap_in=0, reduction_terms=reductions,
    )
    assert result["effective_bearing_diameter_in"] == root
    assert result["main_bearing_psi"] == result["side_bearing_psi"] == 4650
    assert result["reference_values_lbf"] == pytest.approx(direct["reference_values_lbf"])


def test_thread_exposure_boundary_preserves_full_body_diameter_and_old_reductions():
    inputs = case() | {
        "bolt_full_body_diameter_in": 0.25,
        "bolt_thread_root_diameter_in": 0.2,
        "main_thread_bearing_length_in": 1.5 / 4,
    }
    assert wood_wood_single_shear_reference(**inputs)["effective_bearing_diameter_in"] == 0.25


@pytest.mark.parametrize("override", [
    {},
    {"bolt_bending_yield_strength_psi": 0},
    {"bolt_bending_yield_strength_psi": 45_000, "bolt_bending_yield_moment_lb_in": 1},
])
def test_subquarter_root_requires_sourced_strength_and_matching_moment(override):
    inputs = case() | {
        "bolt_thread_root_diameter_in": 0.2,
        "main_thread_bearing_length_in": 0.5,
        "bolt_bending_yield_moment_lb_in": 45_000 * 0.2**3 / 6,
        "reduction_terms": dict.fromkeys(("Im", "Is", "II", "IIIm", "IIIs", "IV"), 2.5 * 1.25),
    }
    with pytest.raises(ValueError, match="bending yield"):
        wood_wood_single_shear_reference(**(inputs | override))


def test_subquarter_root_rejects_large_dowel_reduction_terms_and_axis_parallel():
    inputs = case() | {
        "bolt_thread_root_diameter_in": 0.2,
        "main_thread_bearing_length_in": 0.5,
        "bolt_bending_yield_strength_psi": 45_000,
        "bolt_bending_yield_moment_lb_in": 45_000 * 0.2**3 / 6,
    }
    with pytest.raises(ValueError, match="reduction terms"):
        wood_wood_single_shear_reference(**inputs)
    with pytest.raises(ValueError, match="axis-parallel"):
        wood_wood_single_shear_reference(**(inputs | {"main_bolt_axis_parallel_to_grain": True}))


def test_every_parameter_is_required():
    inputs = case()
    for missing in inputs:
        with pytest.raises(TypeError):
            wood_wood_single_shear_reference(
                **{name: value for name, value in inputs.items() if name != missing}
            )
