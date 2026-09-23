"""Reproducible metal-property thresholds for the selected STAFAST barrel.

These are demand-derived sensitivities, not STAFAST properties, accepted
allowables, or a complete-part qualification.
"""

from __future__ import annotations

import json
import math

from scripts import owner_barrel_vertical_center_capacity as capacity

SCHEMA = "owner_barrel_metal_threshold/v1"
THREADS_PER_INCH = 20.0
NOMINAL_THREAD_MAJOR_DIAMETER_IN = 0.25
UNC_PITCH_DIAMETER_CONSTANT = 0.64951905


def _round(value, digits=6):
    return round(float(value), digits)


def build_report():
    _material, _hardware, proxy, barrel, _washer, _bolt = capacity._load_inputs()
    demand = capacity._proxy_demands(proxy)["maximum_bolt_tension_row_n"]
    tolerance_in = barrel["catalog_default_decimal_tolerance_in"]
    pitch_mm = 25.4 / THREADS_PER_INCH
    body_diameter_mm = (barrel["nominal_body_od_mm"] / 25.4 - tolerance_in) * 25.4
    body_radius_mm = body_diameter_mm / 2
    hole_diameter_mm = NOMINAL_THREAD_MAJOR_DIAMETER_IN * 25.4
    hole_radius_mm = hole_diameter_mm / 2
    length_mm = (barrel["nominal_body_length_mm"] / 25.4 + tolerance_in) * 25.4
    axis_offset_mm = (
        barrel["nominal_thread_axis_from_slotted_end_mm"] / 25.4 + tolerance_in
    ) * 25.4
    far_span_mm = length_mm - axis_offset_mm
    lobe_half_height_mm = math.sqrt(body_radius_mm**2 - hole_radius_mm**2)
    removed_area_mm2 = 2 * (
        hole_radius_mm * lobe_half_height_mm
        + body_radius_mm**2 * math.asin(hole_radius_mm / body_radius_mm)
    )
    net_lobe_area_mm2 = math.pi * body_radius_mm**2 - removed_area_mm2
    full_second_moment_mm4 = math.pi * body_radius_mm**4 / 4
    removed_second_moment_mm4 = hole_radius_mm / 6 * (
        5 * body_radius_mm**2 - 2 * hole_radius_mm**2
    ) * lobe_half_height_mm + body_radius_mm**4 / 2 * math.asin(
        hole_radius_mm / body_radius_mm
    )
    net_second_moment_mm4 = full_second_moment_mm4 - removed_second_moment_mm4
    net_section_modulus_mm3 = net_second_moment_mm4 / lobe_half_height_mm
    endpoint_beam_moment_nmm = demand * axis_offset_mm * far_span_mm / length_mm
    effective_thread_mm = body_diameter_mm - 2 * pitch_mm
    basic_pitch_diameter_mm = (
        NOMINAL_THREAD_MAJOR_DIAMETER_IN
        - UNC_PITCH_DIAMETER_CONSTANT / THREADS_PER_INCH
    ) * 25.4
    return {
        "schema": SCHEMA,
        "candidate": "compact-floor-flush-bolted-development",
        "scope": "selected STAFAST barrel metal requirement sensitivity",
        "inputs": {
            "old_topology_proxy_tension_n": _round(demand),
            "catalog_decimal_tolerance_in": tolerance_in,
            "adverse_body_diameter_mm": _round(body_diameter_mm),
            "adverse_body_length_mm": _round(length_mm),
            "adverse_axis_offset_mm": _round(axis_offset_mm),
            "modeled_full_hole_strip_diameter_mm": _round(hole_diameter_mm),
            "unc_pitch_mm": _round(pitch_mm),
            "assumed_complete_thread_length_mm": _round(effective_thread_mm),
            "basic_unc_pitch_diameter_mm": _round(basic_pitch_diameter_mm),
        },
        "derived_geometry": {
            "net_two_lobe_area_mm2": _round(net_lobe_area_mm2),
            "net_second_moment_mm4": _round(net_second_moment_mm4),
            "net_section_modulus_mm3": _round(net_section_modulus_mm3),
            "endpoint_supported_moment_nmm": _round(endpoint_beam_moment_nmm),
        },
        "requirements_per_unit_demand_factor": {
            "whole_barrel_design_resistance_n_before_preload": _round(demand),
            "female_thread_shear_strength_mpa": _round(
                3 * demand / (math.pi * basic_pitch_diameter_mm * effective_thread_mm)
            ),
            "illustrative_lobe_average_shear_mpa": _round(demand / net_lobe_area_mm2),
            "illustrative_lobe_bending_yield_mpa_before_kt": _round(
                endpoint_beam_moment_nmm / net_section_modulus_mm3
            ),
        },
        "scaling": {
            "whole_barrel": "installation_preload_n + demand_factor * reported value",
            "thread_and_lobe_shear": "demand_factor * reported value",
            "lobe_bending": "demand_factor * stress_concentration_Kt * reported value",
        },
        "decision": {
            "finite_decision": "EVIDENCE_BLOCKED",
            "selected_barrel_property_pass": False,
            "reason": (
                "Public STAFAST evidence supplies no controlled material minima, "
                "usable complete thread, preload bound, wall method, or complete-part rating."
            ),
            "diy_ready": False,
            "structural_released": False,
        },
        "limits": [
            "The 0.016-inch catalog tolerance is a provisional sensitivity; STAFAST requires a current print.",
            "The lobe model is an illustrative endpoint-supported net-section beam, not a validated barrel-wall method.",
            "The full 0.250-inch hole strip omits actual thread-flank distribution, slot, local contact, yielding, and stress concentration.",
            "The thread equation assumes complete female thread across the adverse body diameter minus two pitches.",
            "The demand is an old-topology service proxy, not a fresh candidate design action.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, sort_keys=True))
