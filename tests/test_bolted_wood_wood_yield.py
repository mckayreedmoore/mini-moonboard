"""Conditional 2024 NDS single-fastener, two-solid-DF-L-member component tests."""

import math

import pytest

from fea.dowel_yield import single_shear
from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi
from mini_moonboard.bolted_wood_wood_yield import wood_wood_single_shear_reference


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


def test_subquarter_root_rejected_when_threads_require_it():
    with pytest.raises(ValueError, match="effective bolt diameter"):
        wood_wood_single_shear_reference(
            **(case() | {"bolt_thread_root_diameter_in": 0.2,
                        "main_thread_bearing_length_in": 0.5})
        )


def test_every_parameter_is_required():
    inputs = case()
    for missing in inputs:
        with pytest.raises(TypeError):
            wood_wood_single_shear_reference(
                **{name: value for name, value in inputs.items() if name != missing}
            )
