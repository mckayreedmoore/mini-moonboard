"""Conditional 2024 NDS symmetric double-shear wood-main/steel-side reference.

One bolt, two contacting steel side plates, solid DF-L wood main member, load
perpendicular to the bolt axis. Caller establishes symmetric side actions.
This does not establish that condition for the actual AB205 shared bolt, or
check spacing, splitting, steel plate resistance, group action, adjustments,
or the complete joint.
"""

import math

from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi


def wood_steel_double_shear_reference(
    *,
    bolt_full_body_diameter_in: float,
    bolt_thread_root_diameter_in: float,
    wood_thread_bearing_length_in: float,
    steel_side_a_thread_bearing_length_in: float,
    steel_side_b_thread_bearing_length_in: float,
    bolt_bending_yield_psi: float,
    steel_bearing_psi: float,
    wood_bearing_length_in: float,
    steel_side_a_bearing_length_in: float,
    steel_side_b_bearing_length_in: float,
    grain_load_angle_degrees: float,
    symmetric_side_actions_established: bool,
) -> dict:
    """Return unadjusted one-bolt four-mode Z, conditional on symmetric actions.

    Supply product-specific steel bearing strength and bolt bending yield.
    Per NDS 12.3.7, full-body D requires threads in no more than one-quarter
    of the bearing length of every member holding them. Table 12.3.1A uses
    the lesser side bearing length for both steel sides when unequal.
    """
    if symmetric_side_actions_established is not True:
        raise ValueError("symmetric side actions must be explicitly established")

    positive = (
        bolt_full_body_diameter_in,
        bolt_thread_root_diameter_in,
        bolt_bending_yield_psi,
        steel_bearing_psi,
        wood_bearing_length_in,
        steel_side_a_bearing_length_in,
        steel_side_b_bearing_length_in,
    )
    if any(
        type(value) not in (int, float) or not math.isfinite(value) or value <= 0
        for value in positive
    ):
        raise ValueError(
            "bolt, steel, and bearing lengths must be positive finite numbers"
        )
    if bolt_thread_root_diameter_in > bolt_full_body_diameter_in:
        raise ValueError("thread root cannot exceed full-body diameter")

    members = (
        (wood_thread_bearing_length_in, wood_bearing_length_in),
        (steel_side_a_thread_bearing_length_in, steel_side_a_bearing_length_in),
        (steel_side_b_thread_bearing_length_in, steel_side_b_bearing_length_in),
    )
    for thread_length, bearing_length in members:
        if (
            type(thread_length) not in (int, float)
            or not math.isfinite(thread_length)
            or thread_length < 0
            or thread_length > bearing_length
        ):
            raise ValueError("thread bearing lengths must fit their member")

    diameter = (
        bolt_full_body_diameter_in
        if all(
            thread_length <= bearing_length / 4
            for thread_length, bearing_length in members
        )
        else bolt_thread_root_diameter_in
    )
    if not 0.25 <= diameter <= 1:
        raise ValueError("effective bolt diameter must be 1/4 to 1 inch")
    if (
        type(grain_load_angle_degrees) not in (int, float)
        or not math.isfinite(grain_load_angle_degrees)
        or not 0 <= grain_load_angle_degrees <= 90
    ):
        raise ValueError("grain/load angle must be 0 to 90 degrees")

    side_length = min(steel_side_a_bearing_length_in, steel_side_b_bearing_length_in)
    wood_bearing = dfl_dowel_bearing_psi(diameter, grain_load_angle_degrees)
    ratio = wood_bearing / steel_bearing_psi
    k3 = -1 + math.sqrt(
        2 * (1 + ratio) / ratio
        + 2
        * bolt_bending_yield_psi
        * (2 + ratio)
        * diameter**2
        / (3 * wood_bearing * side_length**2)
    )
    ktheta = 1 + 0.25 * grain_load_angle_degrees / 90
    reference = {
        "Im": diameter * wood_bearing_length_in * wood_bearing / (4 * ktheta),
        "Is": 2 * diameter * side_length * steel_bearing_psi / (4 * ktheta),
        "IIIs": 2
        * k3
        * diameter
        * side_length
        * wood_bearing
        / ((2 + ratio) * 3.2 * ktheta),
        "IV": 2
        * diameter**2
        / (3.2 * ktheta)
        * math.sqrt(2 * wood_bearing * bolt_bending_yield_psi / (3 * (1 + ratio))),
    }
    if any(not math.isfinite(value) or value <= 0 for value in reference.values()):
        raise ValueError("nonfinite or nonpositive calculated reference value")
    governing = min(reference, key=reference.get)
    return {
        "wood_bearing_psi": wood_bearing,
        "effective_bolt_diameter_in": diameter,
        "effective_steel_side_bearing_length_in": side_length,
        "reference_values_lbf": reference,
        "governing_mode": governing,
        "reference_lateral_lbf": reference[governing],
        "limits": "2024 NDS unadjusted one-bolt symmetric double-shear lateral yield "
        "reference only; not the actual AB205 shared bolt and not a complete joint",
    }
