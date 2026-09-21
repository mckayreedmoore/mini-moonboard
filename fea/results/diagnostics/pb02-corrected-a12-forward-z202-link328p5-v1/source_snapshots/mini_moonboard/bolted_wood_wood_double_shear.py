"""Conditional 2024 NDS symmetric double-shear reference for three DF-L pieces.

This is one dowel's lateral-yield component, not a center/backer joint rating.
"""

import math

from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def wood_wood_double_shear_reference(
    *,
    main_bearing_length_in: float,
    side_a_bearing_length_in: float,
    side_b_bearing_length_in: float,
    main_load_to_grain_degrees: float,
    side_a_load_to_grain_degrees: float,
    side_b_load_to_grain_degrees: float,
    main_bolt_axis_parallel_to_grain: bool,
    side_a_bolt_axis_parallel_to_grain: bool,
    side_b_bolt_axis_parallel_to_grain: bool,
    bolt_full_body_diameter_in: float,
    bolt_thread_root_diameter_in: float,
    main_thread_bearing_length_in: float,
    side_a_thread_bearing_length_in: float,
    side_b_thread_bearing_length_in: float,
    bolt_bending_yield_strength_psi: float,
    side_a_gap_in: float,
    side_b_gap_in: float,
    symmetric_side_actions_established: bool,
) -> dict:
    """Return four unadjusted lateral modes only for contacting symmetric sides.

    Both side pieces must actually be solid DF-L with the same load-to-grain
    angle and bearing properties. The caller must prove symmetric side forces;
    this function does not infer them from the presence of three members.
    """
    if symmetric_side_actions_established is not True:
        raise ValueError("symmetric side actions must be established")
    if (
        type(main_bolt_axis_parallel_to_grain) is not bool
        or type(side_a_bolt_axis_parallel_to_grain) is not bool
        or type(side_b_bolt_axis_parallel_to_grain) is not bool
        or main_bolt_axis_parallel_to_grain
        or side_a_bolt_axis_parallel_to_grain
        or side_b_bolt_axis_parallel_to_grain
    ):
        raise ValueError("axis-parallel grain needs separate analysis")
    lengths = (
        main_bearing_length_in,
        side_a_bearing_length_in,
        side_b_bearing_length_in,
    )
    if any(not _finite(v) or v <= 0 for v in lengths):
        raise ValueError("bearing lengths must be positive and finite")
    if any(not _finite(v) or v != 0 for v in (side_a_gap_in, side_b_gap_in)):
        raise ValueError("2024 NDS double-shear route requires contacting faces")
    angles = (
        main_load_to_grain_degrees,
        side_a_load_to_grain_degrees,
        side_b_load_to_grain_degrees,
    )
    if any(not _finite(v) or not 0 <= v <= 90 for v in angles):
        raise ValueError("load-to-grain angles must be between 0 and 90 degrees")
    if side_a_load_to_grain_degrees != side_b_load_to_grain_degrees:
        raise ValueError("unequal side grain/load angles need asymmetric analysis")
    if (
        not _finite(bolt_full_body_diameter_in)
        or not 0.25 <= bolt_full_body_diameter_in <= 1
        or not _finite(bolt_thread_root_diameter_in)
        or not 0 < bolt_thread_root_diameter_in <= bolt_full_body_diameter_in
        or not _finite(bolt_bending_yield_strength_psi)
        or bolt_bending_yield_strength_psi <= 0
    ):
        raise ValueError("bolt geometry and sourced bending yield are invalid")
    bearing_and_thread = (
        (main_bearing_length_in, main_thread_bearing_length_in),
        (side_a_bearing_length_in, side_a_thread_bearing_length_in),
        (side_b_bearing_length_in, side_b_thread_bearing_length_in),
    )
    if any(
        not _finite(thread) or not 0 <= thread <= length
        for length, thread in bearing_and_thread
    ):
        raise ValueError("thread exposure must fit every bearing length")
    full_body_allowed = all(
        thread <= length / 4 for length, thread in bearing_and_thread
    )
    diameter = (
        bolt_full_body_diameter_in
        if full_body_allowed
        else bolt_thread_root_diameter_in
    )
    if diameter < 0.25:
        raise ValueError("effective root diameter below 1/4 inch needs other terms")

    side_length = min(side_a_bearing_length_in, side_b_bearing_length_in)
    fe_m = dfl_dowel_bearing_psi(diameter, main_load_to_grain_degrees)
    fe_s = dfl_dowel_bearing_psi(diameter, side_a_load_to_grain_degrees)
    ratio = fe_m / fe_s
    k3 = -1 + math.sqrt(
        2 * (1 + ratio) / ratio
        + 2
        * bolt_bending_yield_strength_psi
        * (2 + ratio)
        * diameter**2
        / (3 * fe_m * side_length**2)
    )
    ktheta = 1 + 0.25 * max(angles) / 90
    reference = {
        "Im": diameter * main_bearing_length_in * fe_m / (4 * ktheta),
        "Is": 2 * diameter * side_length * fe_s / (4 * ktheta),
        "IIIs": 2 * k3 * diameter * side_length * fe_m / ((2 + ratio) * 3.2 * ktheta),
        "IV": 2
        * diameter**2
        / (3.2 * ktheta)
        * math.sqrt(2 * fe_m * bolt_bending_yield_strength_psi / (3 * (1 + ratio))),
    }
    if any(not math.isfinite(value) or value <= 0 for value in reference.values()):
        raise ValueError("nonfinite or nonpositive yield-mode reference")
    governing = min(reference, key=reference.get)
    return {
        "main_bearing_psi": fe_m,
        "side_bearing_psi": fe_s,
        "effective_bolt_diameter_in": diameter,
        "effective_side_bearing_length_in": side_length,
        "reference_values_lbf": reference,
        "governing_mode": governing,
        "reference_lateral_lbf": reference[governing],
        "connection_qualified": False,
        "limits": "Conditional one-bolt symmetric wood/wood/wood double-shear "
        "lateral yield only; actual symmetry, placement, group, "
        "axial, washer, member and same-case checks remain open",
    }
