"""Conditional 2024 NDS six-mode wood-main/steel-side bolt reference.

This is a single fastener with one shear plane, contacting member faces,
no gap, and load perpendicular to the bolt axis. It does not check required
edge/end distance, spacing, splitting, steel plate resistance, bolt axial
action, group effects, service adjustments, or a formed connector assembly.
The candidate shared center-header bolt stack has two steel flanges around
wood with potentially unequal actions. This two-member single-shear helper
must not be applied directly to that shared stack.
"""

import math

from fea.dowel_yield import single_shear
from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi


def wood_steel_single_shear_reference(
    *,
    bolt_full_body_diameter_in: float,
    bolt_thread_root_diameter_in: float,
    wood_thread_bearing_length_in: float,
    steel_thread_bearing_length_in: float,
    bolt_bending_yield_psi: float,
    steel_bearing_psi: float,
    wood_bearing_length_in: float,
    steel_thickness_in: float,
    grain_load_angle_degrees: float,
) -> dict:
    """Return unadjusted six-mode Z for solid DF-L wood and one steel side plate.

    Supply product-specific steel dowel-bearing strength, bolt bending yield,
    full-body and root diameters, and thread exposure in each member. NDS
    12.3.7 permits full-body D only when threads occupy at most one-quarter
    of the bearing length in each member holding them; otherwise root D is
    used. An effective D below 1/4 inch needs different reduction terms and
    is rejected. Wood bearing uses the existing DF-L solid-wood helper.
    """
    positives = (
        bolt_full_body_diameter_in,
        bolt_thread_root_diameter_in,
        bolt_bending_yield_psi,
        steel_bearing_psi,
        wood_bearing_length_in,
        steel_thickness_in,
    )
    if any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
        or value <= 0
        for value in positives
    ):
        raise ValueError(
            "bolt, steel, and bearing-length inputs must be positive finite numbers"
        )
    if bolt_thread_root_diameter_in > bolt_full_body_diameter_in:
        raise ValueError("thread root cannot exceed full-body diameter")
    thread_lengths = (wood_thread_bearing_length_in, steel_thread_bearing_length_in)
    if any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
        or value < 0
        for value in thread_lengths
    ):
        raise ValueError("thread bearing lengths must be finite and nonnegative")
    if (
        wood_thread_bearing_length_in > wood_bearing_length_in
        or steel_thread_bearing_length_in > steel_thickness_in
    ):
        raise ValueError("thread bearing length exceeds member bearing length")
    full_body_allowed = (
        wood_thread_bearing_length_in <= wood_bearing_length_in / 4
        and steel_thread_bearing_length_in <= steel_thickness_in / 4
    )
    diameter = (
        bolt_full_body_diameter_in
        if full_body_allowed
        else bolt_thread_root_diameter_in
    )
    if not 0.25 <= diameter <= 1:
        raise ValueError(
            "effective bolt diameter must be 1/4 to 1 inch for this Rd table"
        )
    if (
        not isinstance(grain_load_angle_degrees, (int, float))
        or isinstance(grain_load_angle_degrees, bool)
        or not math.isfinite(grain_load_angle_degrees)
        or not 0 <= grain_load_angle_degrees <= 90
    ):
        raise ValueError("grain/load angle must be 0 to 90 degrees")

    wood_bearing_psi = dfl_dowel_bearing_psi(diameter, grain_load_angle_degrees)
    angle_factor = 1 + 0.25 * grain_load_angle_degrees / 90
    moment = bolt_bending_yield_psi * diameter**3 / 6
    result = single_shear(
        main_length_in=wood_bearing_length_in,
        side_length_in=steel_thickness_in,
        main_bearing_lb_in=wood_bearing_psi * diameter,
        side_bearing_lb_in=steel_bearing_psi * diameter,
        main_yield_moment_lb_in=moment,
        side_yield_moment_lb_in=moment,
        gap_in=0,
        reduction_terms={
            "Im": 4 * angle_factor,
            "Is": 4 * angle_factor,
            "II": 3.6 * angle_factor,
            "IIIm": 3.2 * angle_factor,
            "IIIs": 3.2 * angle_factor,
            "IV": 3.2 * angle_factor,
        },
    )
    return {
        "wood_bearing_psi": wood_bearing_psi,
        "effective_bolt_diameter_in": diameter,
        "reference_values_lbf": result["reference_values_lbf"],
        "governing_mode": result["governing_mode"],
        "reference_lateral_lbf": result["reference_lateral_lbf"],
        "limits": "2024 NDS unadjusted single-fastener lateral yield reference only; "
        "not an adjusted joint or connector resistance",
    }
