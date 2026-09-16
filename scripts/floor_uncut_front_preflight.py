"""Reproduce the bounded dimensional preflight for the uncut front joint.

This does not build CAD, run a native solve, or calculate connection capacity.
Catalog dimensions that are not guaranteed minima or maxima remain sensitivities.
"""

import json
import math

MM_PER_IN = 25.4


def build():
    diameter = 0.375 * MM_PER_IN
    wood_bore = 0.4375 * MM_PER_IN
    grip = 177.8
    runner_bearing = 38.1
    pitch = 40.5
    drill_error = 1.0
    cut_error = 2.0

    washer_od_min = 25.2222
    washer_od_nominal = 25.4
    washer_od_max = 26.1620
    washer_id_max = 11.5062
    washer_thickness_min = 4.5
    washer_thickness_nominal = 0.1875 * MM_PER_IN
    washer_thickness_max = 5.0

    bolt_length_nominal = 8.5 * MM_PER_IN
    bolt_length_min = bolt_length_nominal - 0.18 * MM_PER_IN
    minimum_thread = 1.25 * MM_PER_IN
    transition_sensitivity = 0.312 * MM_PER_IN
    nut_height_max = 0.337 * MM_PER_IN

    closest_boundary = 41.243587681
    worst_pitch = pitch - 2 * drill_error
    placement_boundary = closest_boundary - drill_error - cut_error
    max_washer_float = (washer_id_max - diameter) / 2
    nominal_bore_radial_clearance = (wood_bore - diameter) / 2
    bore_axis_registration_limit = wood_bore - diameter
    independent_bore_error = 2 * drill_error
    worst_washer_to_wood_eccentricity = max_washer_float + nominal_bore_radial_clearance
    equivalent_unsupported_diameter = wood_bore + 2 * worst_washer_to_wood_eccentricity

    required_body = grip + washer_thickness_max - runner_bearing / 4
    latest_usable_thread = grip + 2 * washer_thickness_min
    minimum_tip_projection = (
        bolt_length_min - grip - 2 * washer_thickness_max - nut_height_max
    )
    nominal_thread_start = bolt_length_nominal - minimum_thread
    catalog_sensitivity_body = bolt_length_min - minimum_thread - transition_sensitivity

    def response(outer_diameter):
        area = math.pi * (outer_diameter**2 - wood_bore**2) / 4
        steel = 200_000 * math.pi * diameter**2 / 4 / grip
        psi_mpa = 0.006894757293168361
        seat_compliance = 139.7 / (0.05 * 1_300_000 * psi_mpa * area) + 38.1 / (
            0.05 * 1_600_000 * psi_mpa * area
        )
        return {
            "effective_seat_area_mm2": area,
            "assumed_axial_spring_n_per_mm": 1 / (1 / steel + seat_compliance),
        }

    result = {
        "candidate": "compact-floor-uncut-development",
        "arrangement": "head / CL-8-FW / 6x6 post / runner / CL-8-FW / nut",
        "placement": {
            "worst_pair_spacing_mm": worst_pitch,
            "pair_spacing_margin_over_4D_mm": worst_pitch - 4 * diameter,
            "worst_boundary_after_stated_errors_mm": placement_boundary,
            "boundary_margin_over_4D_mm": placement_boundary - 4 * diameter,
            "boundary_margin_over_7D_mm": 66.818587681 - 7 * diameter,
        },
        "washer_and_registration": {
            "boundary_margin_including_max_od_and_float_mm": (
                closest_boundary
                - drill_error
                - cut_error
                - washer_od_max / 2
                - max_washer_float
            ),
            "adjacent_washer_gap_including_max_od_and_float_mm": (
                worst_pitch - washer_od_max - 2 * max_washer_float
            ),
            "nominal_parallel_bore_axis_registration_limit_mm": bore_axis_registration_limit,
            "independent_one_mm_axis_error_envelope_mm": independent_bore_error,
            "registration_margin_mm": bore_axis_registration_limit
            - independent_bore_error,
            "maximum_uncontrolled_washer_float_about_bolt_mm": max_washer_float,
            "maximum_washer_to_wood_bore_eccentricity_mm": worst_washer_to_wood_eccentricity,
            "concentric_equivalent_unsupported_diameter_mm": equivalent_unsupported_diameter,
            "minimum_remaining_radial_seat_width_mm": (
                washer_od_min - equivalent_unsupported_diameter
            )
            / 2,
        },
        "stack": {
            "required_first_reduced_section_no_earlier_than_mm": required_body,
            "required_first_complete_usable_thread_no_later_than_mm": latest_usable_thread,
            "minimum_tip_projection_after_maximum_stack_mm": minimum_tip_projection,
            "nominal_minimum_thread_start_mm": nominal_thread_start,
            "nominal_thread_start_margin_at_nominal_washers_mm": (
                grip + 2 * washer_thickness_nominal - nominal_thread_start
            ),
            "short_bolt_min_thread_max_transition_body_sensitivity_mm": catalog_sensitivity_body,
            "sensitivity_margin_to_receiving_body_limit_mm": catalog_sensitivity_body
            - required_body,
        },
        "diagnostic_response": {
            "accepted_minimum_od": response(washer_od_min),
            "nominal_od": response(washer_od_nominal),
            "accepted_maximum_od": response(washer_od_max),
            "current_model_nominal_is_equivalent": True,
            "equivalence_scope": (
                "Same nominal bolt diameter, wood grip, washer OD, effective wood opening, "
                "and mixed-material seat paths; bolt length and washer thickness are absent "
                "from the current spring analogy."
            ),
        },
        "qualified_for_design": False,
    }

    assert math.isclose(result["placement"]["pair_spacing_margin_over_4D_mm"], 0.4)
    assert 0.1435 < result["placement"]["boundary_margin_over_4D_mm"] < 0.1437
    assert result["washer_and_registration"]["registration_margin_mm"] < 0
    assert result["stack"]["sensitivity_margin_to_receiving_body_limit_mm"] < 0
    return result


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, allow_nan=False))
