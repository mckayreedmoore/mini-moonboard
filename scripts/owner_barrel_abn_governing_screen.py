"""Focused governing screen for the ABN 7015_10PACK trial barrel.

The ABN dimensions and material wording are retail evidence.  S355 is a named
hypothetical sensitivity only.  This screen binds prior CAD/fixture results to
their producer hashes and does not qualify hardware or release fabrication.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "owner_barrel_abn_governing_screen/v1"
MPA_PER_PSI = 0.006894757293168

SOURCES = {
    "amazon": "https://www.amazon.com/dp/B01N3QW1JS",
    "exact_sku_reseller": "https://angola.desertcart.com/products/177938153-cross-dowel-barrel-nuts-1-4-20-16mm-x-10mm",
    "six_mm_family_reseller": "https://www.noon.com/uae-en/50-cross-dowels-barrel-nuts-1-4-20-16mm-x-10mm-zinc-plated-off-centered-cnc/Z8D593A3030DC081A4881Z/p/",
    "fabbri_2022": "https://sfera.unife.it/retrieve/9559c37b-7c3c-4ee0-b1a9-19090373d783/Fabbri_Tullini_Minghini_2022%20-%20pre-print.pdf",
}

SOURCE_SHA256 = {
    "scripts/owner_barrel_vertical_center_joint_fixture.py": "a0caa488c700d761e5e7e5d9abc290de563242ea47c835bcb1411f9cdc58f0a2",
    "scripts/owner_barrel_vertical_center_probe.py": "6bab27dcd72a03838d684cbf94c7f4eb8423bb853f1002ded875a6f8f9fd8d31",
    "scripts/owner_barrel_vertical_center_breakout.py": "8f11a88016d08b85c82982a0b7b18e7e48537974bb084d5cd6994ecedcdf9543",
    "scripts/owner_barrel_metal_threshold.py": "ee4c1558720b75a107aeaa19f290b70dce8f670265814a530fb16a18cbb6b040",
    "docs/barrel-nut-selected-hardware.json": "8c65618d3edd56f745a8f180ca6ada583e7e19551b6cc5d8a59598eababd7698",
    "docs/bolted-candidate-material-basis.json": "d64ccbeb482f5082e6f5b9a059dbc86489a00d681eedda146c728cf03af85ee7",
}

# Extracted from the source-bound compatibility fixture and nominal combined-cut
# map.  They are old-topology screening actions, not fresh candidate demands.
SCREEN_INPUTS = {
    "old_static_witness_row_tension_n": 220.475915,
    "old_precompatibility_proxy_row_tension_n": 301.493967,
    "reference_isolated_my_row_tension_n": 318.318054,
    "reference_isolated_mx_governing_row_n": 496.391286,
    "accepted_default_combined_maximum_row_tension_n": 733.840362,
    "valid_subset_maximum_row_tension_n": 846.705806,
    "valid_subset_maximum_two_row_total_tension_n": 1156.374276,
    "valid_subset_maximum_row_shear_n": 136.053023,
    "valid_subset_maximum_combined_row_resultant_n": 852.008835,
    "valid_subset_maximum_cell_average_pressure_mpa": 5.012591,
    "valid_subset_rear_axial_share_range": [0.163594, 0.969572],
    "outside_small_kinematics_case_count": 75,
    "minimum_grain_end_center_distance_mm": 36.551404,
    "individual_two_plane_unadjusted_reference_n": 1685.657,
    "rear_net_section_area_mm2": 2955.648,
    "forward_net_section_area_mm2": 5031.773,
    "center_split_plane_area_mm2": 1245.159,
}

ABN = {
    "brand": "ABN",
    "part_number": "7015_10PACK",
    "asin": "B01N3QW1JS",
    "pack_count": 10,
    "thread": "1/4-20",
    "nominal_body_diameter_mm": 10.0,
    "nominal_body_length_mm": 16.0,
    "retail_family_end_to_thread_axis_mm": 6.0,
    "advertised_material": "alloy steel",
    "finish": "zinc plated",
    "availability_checked_date": "2026-09-22",
    "availability": "CURRENTLY_UNAVAILABLE_NO_FEATURED_OFFER",
}


def _round(value, digits=6):
    return round(float(value), digits)


def _validate_sources():
    mismatches = {}
    for relative, expected in SOURCE_SHA256.items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if actual != expected:
            mismatches[relative] = {"expected": expected, "actual": actual}
    if mismatches:
        raise ValueError(f"ABN screen source drift: {mismatches}")


def _geometry_screen():
    axis_depth_mm = 19.05
    principal_width_mm = 38.1
    six_mm = ABN["retail_family_end_to_thread_axis_mm"]

    def orientation(end_to_axis_mm):
        recess = axis_depth_mm - end_to_axis_mm
        depth = recess + ABN["nominal_body_length_mm"]
        return {
            "proximal_end_to_axis_mm": _round(end_to_axis_mm),
            "body_recess_from_entry_mm": _round(recess),
            "blind_bore_depth_mm": _round(depth),
            "far_side_stock_mm": _round(principal_width_mm - depth),
            "nominal_collision_screen": "PASS",
        }

    return {
        "pose": "NOT_FROZEN_END_DATUM_UNVERIFIED",
        "thread_and_bolt_axes_unchanged": True,
        "existing_modeled_offset_mm": 5.9944,
        "abn_retail_family_offset_mm": six_mm,
        "offset_change_mm": _round(
            six_mm - 5.9944
        ),
        "orientation_cases": {
            "six_mm_end_proximal": orientation(six_mm),
            "ten_mm_end_proximal": orientation(
                ABN["nominal_body_length_mm"] - six_mm
            ),
        },
        "slot_end_to_axis_mm": None,
        "plain_end_to_axis_mm": None,
        "barrel_radial_x_ligament_mm": 14.05,
        "minimum_raw_face_clear_ligament_mm": 31.551404,
        "clear_wood_between_rows_mm": 70.0,
        "minimum_complete_thread_endpoint_past_axis_mm": 16.704,
        "nominal_collision_screen": "BOTH_END_ORIENTATIONS_PASS_NOMINAL_CAD",
        "controlled_geometry": False,
        "status": "PLAUSIBLE_NOMINAL_BOTH_ORIENTATIONS_PENDING_SAMPLE_DATUM",
    }


def _wood_screen():
    demand = SCREEN_INPUTS["valid_subset_maximum_row_tension_n"]
    diameter = ABN["nominal_body_diameter_mm"]
    length = ABN["nominal_body_length_mm"]
    bolt_bore = 7.5
    angle = 40.0
    fe_mpa = dfl_dowel_bearing_psi(diameter / 25.4, angle) * MPA_PER_PSI
    projected_area = diameter * length - math.pi * bolt_bore**2 / 4
    rectangular_area = diameter * (length - bolt_bore)
    mode_i_reduction = 4 * (1 + 0.25 * angle / 90)
    distance_factor = min(
        1.0,
        SCREEN_INPUTS["minimum_grain_end_center_distance_mm"] / (7 * diameter),
    )
    nds_fabbri = fe_mpa * projected_area / mode_i_reduction * distance_factor
    fpl_form = fe_mpa * rectangular_area / 4 * distance_factor
    fc_perp_mpa = 625 * MPA_PER_PSI
    face_pressure = SCREEN_INPUTS["valid_subset_maximum_cell_average_pressure_mpa"]
    washer_reference = 920.57

    def margin(capacity):
        return {
            "reference_n": _round(capacity),
            "capacity_over_demand": _round(capacity / demand),
            "demand_over_reference": _round(demand / capacity),
            "shortfall_n": _round(capacity - demand),
            "screen": "FAIL" if capacity < demand else "PASS_REFERENCE_ONLY",
        }

    net_sections = {}
    for name, area in (
        ("rear", SCREEN_INPUTS["rear_net_section_area_mm2"]),
        ("forward", SCREEN_INPUTS["forward_net_section_area_mm2"]),
    ):
        reference = area * 575 * MPA_PER_PSI
        net_sections[name] = {
            "area_mm2": area,
            "unadjusted_parallel_tension_reference_n": _round(reference),
            "reference_over_row_demand": _round(reference / demand),
            "status": "REFERENCE_ONLY_OBLIQUE_AND_SPLITTING_NOT_CLOSED",
        }
    return {
        "screen_row_demand_n": demand,
        "dfl_bearing_stress_mpa": _round(fe_mpa),
        "projected_area_mm2": _round(projected_area),
        "provisional_end_distance_factor": _round(distance_factor),
        "nds_fabbri_adapted_bearing": margin(nds_fabbri),
        "fpl_form_adapted_bearing": margin(fpl_form),
        "individual_two_plane_tearout": margin(
            SCREEN_INPUTS["individual_two_plane_unadjusted_reference_n"]
        ),
        "individual_two_plane_status": "PASS_REFERENCE_ONLY_NOT_ADOPTED_FOR_40_DEG_BLIND_GROUP",
        "header_washer_bearing": margin(washer_reference),
        "header_washer_status": "NARROW_REFERENCE_ONLY_BEFORE_PRELOAD_FLEXURE_AND_ADJUSTMENTS",
        "face_cell_pressure": {
            "screen_average_mpa": face_pressure,
            "unadjusted_fc_perp_reference_mpa": _round(fc_perp_mpa),
            "reference_over_screen": _round(fc_perp_mpa / face_pressure),
            "screen": "FAIL",
            "status": "COARSE_CELL_AVERAGE_NOT_LOCAL_ELASTIC_PEAK",
        },
        "net_sections": net_sections,
        "center_split_plane": {
            "area_mm2": SCREEN_INPUTS["center_split_plane_area_mm2"],
            "resistance_n": None,
            "status": "UNSUPPORTED_NO_ADOPTED_TENSION_PERPENDICULAR_RESISTANCE",
        },
        "two_row_group_tearout": {
            "resistance_n": None,
            "status": "UNRESOLVED_NOT_ENUMERATED",
        },
        "finite_screen": "NO_GO_AS_SCREENED_WOOD_BEARING_AND_FACE_PRESSURE",
    }


def _metal_geometry(diameter_mm, length_mm, offset_mm, demand_n):
    thread_hole_mm = 6.35
    pitch_mm = 25.4 / 20
    radius = diameter_mm / 2
    hole_radius = thread_hole_mm / 2
    lobe_half_height = math.sqrt(radius**2 - hole_radius**2)
    removed_area = 2 * (
        hole_radius * lobe_half_height
        + radius**2 * math.asin(hole_radius / radius)
    )
    lobe_area = math.pi * radius**2 - removed_area
    full_i = math.pi * radius**4 / 4
    removed_i = hole_radius / 6 * (
        5 * radius**2 - 2 * hole_radius**2
    ) * lobe_half_height + radius**4 / 2 * math.asin(hole_radius / radius)
    section_modulus = (full_i - removed_i) / lobe_half_height
    moment = demand_n * offset_mm * (length_mm - offset_mm) / length_mm
    pitch_diameter = (0.25 - 0.64951905 / 20) * 25.4
    complete_thread = diameter_mm - 2 * pitch_mm
    return {
        "female_thread_shear_mpa_times_gamma": _round(
            3 * demand_n / (math.pi * pitch_diameter * complete_thread)
        ),
        "illustrative_lobe_average_shear_mpa_times_gamma": _round(
            demand_n / lobe_area
        ),
        "illustrative_lobe_bending_mpa_times_gamma_kt": _round(
            moment / section_modulus
        ),
    }


def _metal_screen():
    demand = SCREEN_INPUTS["valid_subset_maximum_row_tension_n"]
    nominal = _metal_geometry(10.0, 16.0, 6.0, demand)
    scale = demand / SCREEN_INPUTS["old_precompatibility_proxy_row_tension_n"]
    adverse = {
        "female_thread_shear_mpa_times_gamma": _round(7.379561 * scale),
        "illustrative_lobe_average_shear_mpa_times_gamma": _round(
            18.578899 * scale
        ),
        "illustrative_lobe_bending_mpa_times_gamma_kt": _round(96.126131 * scale),
        "basis": "STAFAST generic +/-0.016-in tolerance sensitivity; not controlled ABN tolerances",
    }
    s355_yield = 355.0
    return {
        "required_complete_barrel_resistance": {
            "formula": "installation_preload_n + gamma * 846.705806 N",
            "before_preload_and_gamma_n": demand,
        },
        "advertised_abn_material_lower_bound_mpa": None,
        "advertised_abn_status": "EVIDENCE_BLOCKED_GENERIC_ALLOY_STEEL_IS_NOT_A_GRADE",
        "nominal_geometry_requirements": nominal,
        "adverse_geometry_sensitivity": adverse,
        "hypothetical_s355": {
            "assumption": "ABN body behaves as S355 with 355 MPa yield; unverified hypothetical only",
            "nominal_bending_margin_formula": "1.782707 / (gamma * Kt)",
            "adverse_bending_margin_formula": "1.315022 / (gamma * Kt)",
            "nominal_margin_at_gamma_1_kt_1p5": _round(
                s355_yield
                / (1.5 * nominal["illustrative_lobe_bending_mpa_times_gamma_kt"])
            ),
            "nominal_margin_at_gamma_1_kt_2": _round(
                s355_yield
                / (2 * nominal["illustrative_lobe_bending_mpa_times_gamma_kt"])
            ),
            "adverse_margin_at_gamma_1_kt_1p5": _round(
                s355_yield
                / (
                    1.5
                    * adverse["illustrative_lobe_bending_mpa_times_gamma_kt"]
                )
            ),
            "adverse_margin_at_gamma_1_kt_2": _round(
                s355_yield
                / (2 * adverse["illustrative_lobe_bending_mpa_times_gamma_kt"])
            ),
            "status": "NOMINAL_PLAUSIBLE_BUT_ADVERSE_SENSITIVITY_FAILS_AT_MODEST_KT",
        },
    }


def build_report():
    _validate_sources()
    geometry = _geometry_screen()
    wood = _wood_screen()
    metal = _metal_screen()
    return {
        "schema": SCHEMA,
        "candidate": "compact-floor-flush-bolted-development",
        "scope": "ABN trial at governing two-vertical-bolt principal/header joint",
        "source_sha256": SOURCE_SHA256,
        "sources": SOURCES,
        "retail_hardware": {
            **ABN,
            "direct_amazon_verified": True,
            "direct_amazon_numeric_offset_verified": False,
            "six_mm_offset_basis": "reseller-family listing plus photo inference",
            "strength_grade_or_rating_published": False,
            "geometry_freeze_allowed": False,
        },
        "demand_screen": {
            **SCREEN_INPUTS,
            "basis": "source-bound old-topology compatibility fixture, reversals, clearance and stiffness sensitivities",
            "fresh_48_pair_demand": False,
            "is_bounded_design_demand": False,
        },
        "cad_geometry": geometry,
        "wood": wood,
        "metal": metal,
        "study_transfer": {
            "s355_and_class_12p9_peak_load_transfer_allowed": False,
            "fabbri_specimen": "50x50 mm beech LVL; M12 rod; custom centered 20x50 mm barrel; axial grain-parallel load",
            "current_difference": "DF-L No.2; 1/4-20; offset and slotted 10x16 mm barrel; 40-degree action, twist, reversals and two-row group",
            "allowed_use": "failure-mode taxonomy, projected-area analogy, and explicit hypothetical S355 material sensitivity only",
        },
        "decision": {
            "nominal_cad_fit": "PLAUSIBLE_BOTH_ORIENTATIONS_PENDING_SAMPLE_MEASUREMENT",
            "governing_principal_header_strength_screen": "CONDITIONAL_NO_GO_IF_846P7_N_SCREEN_AND_ADAPTED_WOOD_REFERENCES_ARE_ADOPTED",
            "actual_abn_metal": "EVIDENCE_BLOCKED",
            "complete_design": "EVIDENCE_BLOCKED",
            "reason": "Both nominal orientations fit, but the slot-end datum is unverified. Under the current hypothetical screen, unequal-row action is 2.00x and 2.45x the two adapted wood-bearing references; edge-cell face pressure also exceeds raw Fc-perp. Neither action nor resistance is adopted, and generic alloy steel supplies no metal lower bound.",
            "smallest_correction_trigger": "Do not freeze this SKU for the structural frame unless sample geometry is measured and a changed joint lowers bounded row demand below an adopted wood resistance with tolerance margin, or member/barrel geometry changes and is rechecked.",
            "diy_ready": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, sort_keys=True))
