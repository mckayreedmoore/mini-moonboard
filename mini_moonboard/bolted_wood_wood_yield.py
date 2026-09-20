"""Conditional two-solid-DF-L-member single-bolt lateral-yield component.

This maps AWC 2024 NDS Chapter 12 bearing inputs to the existing six-mode
solver. It does not establish the prerequisites or adjustments for a joint.
"""

import math

from fea.dowel_yield import single_shear
from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi

_MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")


def _finite_number(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def wood_wood_single_shear_reference(
    *,
    main_bearing_length_in: float,
    side_bearing_length_in: float,
    main_load_to_grain_degrees: float,
    side_load_to_grain_degrees: float,
    main_bolt_axis_parallel_to_grain: bool,
    side_bolt_axis_parallel_to_grain: bool,
    bolt_full_body_diameter_in: float,
    bolt_thread_root_diameter_in: float,
    main_thread_bearing_length_in: float,
    side_thread_bearing_length_in: float,
    bolt_bending_yield_moment_lb_in: float,
    gap_in: float,
    reduction_terms: dict[str, float],
) -> dict:
    """Return six conditional, unadjusted one-bolt yield-mode values in lbf.

    The caller must establish the actual bearing lengths, delivered bolt's
    full-body and thread-root diameters, thread exposure in each member, and
    corresponding bending-yield moment,
    and both grain/load angles. Only a contacting, two-member, single-shear
    lateral connection with neither bolt axis parallel to grain is supported.
    The explicitly supplied reduction terms must match 2024 NDS Table 12.3.1B
    for the larger of the two grain/load angles. No end/edge or group check is
    performed here.
    """
    lengths = (main_bearing_length_in, side_bearing_length_in)
    angles = (main_load_to_grain_degrees, side_load_to_grain_degrees)
    if any(not _finite_number(value) or value <= 0 for value in lengths):
        raise ValueError("bearing lengths must be positive finite numbers")
    if any(not _finite_number(value) or not 0 <= value <= 90 for value in angles):
        raise ValueError("load-to-grain angles must be finite and 0 to 90 degrees")
    if (type(main_bolt_axis_parallel_to_grain) is not bool
            or type(side_bolt_axis_parallel_to_grain) is not bool):
        raise ValueError("bolt-axis/grain flags must be explicit booleans")
    if main_bolt_axis_parallel_to_grain or side_bolt_axis_parallel_to_grain:
        raise ValueError("axis-parallel/end-grain bearing needs separate analysis")
    if (not _finite_number(bolt_full_body_diameter_in)
            or not 0.25 <= bolt_full_body_diameter_in <= 1
            or not _finite_number(bolt_thread_root_diameter_in)
            or not 0 < bolt_thread_root_diameter_in <= bolt_full_body_diameter_in):
        raise ValueError("bolt shank/root diameters are invalid")
    if (not _finite_number(main_thread_bearing_length_in)
            or not 0 <= main_thread_bearing_length_in <= main_bearing_length_in
            or not _finite_number(side_thread_bearing_length_in)
            or not 0 <= side_thread_bearing_length_in <= side_bearing_length_in):
        raise ValueError("thread exposure must fit each bearing length")
    full_body_allowed = (
        main_thread_bearing_length_in <= main_bearing_length_in / 4
        and side_thread_bearing_length_in <= side_bearing_length_in / 4
    )
    effective_bearing_diameter_in = (
        bolt_full_body_diameter_in if full_body_allowed
        else bolt_thread_root_diameter_in
    )
    if effective_bearing_diameter_in < 0.25:
        raise ValueError("effective bolt diameter below 1/4 inch needs other terms")
    if (not _finite_number(bolt_bending_yield_moment_lb_in)
            or bolt_bending_yield_moment_lb_in <= 0):
        raise ValueError("bolt bending-yield moment must be positive and finite")
    if not _finite_number(gap_in) or gap_in != 0:
        raise ValueError("2024 NDS 12.3.1 requires contacting member faces (zero gap)")

    angle_factor = 1 + 0.25 * max(angles) / 90
    expected_reductions = dict(zip(
        _MODES, (4 * angle_factor, 4 * angle_factor,
                 3.6 * angle_factor, 3.2 * angle_factor,
                 3.2 * angle_factor, 3.2 * angle_factor),
    ))
    if (not isinstance(reduction_terms, dict)
            or set(reduction_terms) != set(_MODES)
            or any(not _finite_number(reduction_terms[mode])
                   or not math.isclose(reduction_terms[mode], expected_reductions[mode],
                                       rel_tol=1e-12, abs_tol=1e-12)
                   for mode in _MODES)):
        raise ValueError("reduction terms must match 2024 NDS Table 12.3.1B")

    main_bearing_psi = dfl_dowel_bearing_psi(
        effective_bearing_diameter_in, main_load_to_grain_degrees
    )
    side_bearing_psi = dfl_dowel_bearing_psi(
        effective_bearing_diameter_in, side_load_to_grain_degrees
    )
    result = single_shear(
        main_length_in=main_bearing_length_in,
        side_length_in=side_bearing_length_in,
        main_bearing_lb_in=main_bearing_psi * effective_bearing_diameter_in,
        side_bearing_lb_in=side_bearing_psi * effective_bearing_diameter_in,
        main_yield_moment_lb_in=bolt_bending_yield_moment_lb_in,
        side_yield_moment_lb_in=bolt_bending_yield_moment_lb_in,
        gap_in=gap_in,
        reduction_terms=reduction_terms,
    )
    return {
        "main_bearing_psi": main_bearing_psi,
        "side_bearing_psi": side_bearing_psi,
        "effective_bearing_diameter_in": effective_bearing_diameter_in,
        "yield_values_lbf": result["yield_values_lbf"],
        "reference_values_lbf": result["reference_values_lbf"],
        "governing_mode": result["governing_mode"],
        "reference_lateral_lbf": result["reference_lateral_lbf"],
        "limits": "Conditional 2024 NDS single-bolt lateral yield component only; "
        "not adjusted group or joint resistance, same-case demand, or drilling release",
    }
