"""Conditional PB03 component capacities; no demand or joint verdict."""

import math

from mini_moonboard.bolted_timber_checks import (
    dfl_axial_wood_bearing_reference_lbf,
    dfl_parallel_row_tear_out_reference_lbf,
)
from mini_moonboard.bolted_wood_wood_yield import (
    dowel_bending_yield_moment_lb_in,
    wood_wood_single_shear_reference,
)
from scripts.simple_pb03_lower_center_pair import BORE_DIAMETER_MM
from scripts.simple_pb03_native import SOURCE_ID, PB03Native

MM_PER_IN = 25.4
N_PER_LBF = 4.4482216152605
NOMINAL_DIAMETER_IN = 0.375
ROOT_DIAMETER_IN = 0.298
BOLT_BENDING_YIELD_PSI = 45_000.0
TENSILE_STRESS_AREA_IN2 = 0.0775
WASHER_OD_SENSITIVITY_IN = 1.0
WASHER_CLEARANCE_ID_SENSITIVITY_IN = 13 / 32
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
REPRESENTATIVE_STATIONS = {
    "lower_inner": "clip_horizontal_lower_left_2",
    "lower_outer": "clip_horizontal_lower_left_1",
    "upper_outer": "clip_horizontal_upper_left_1",
    "bottom_outer": "clip_horizontal_bottom_left_1",
}


def _reductions(angle_degrees: float) -> dict[str, float]:
    factor = 1 + 0.25 * angle_degrees / 90
    return dict(
        zip(
            MODES,
            (
                4 * factor,
                4 * factor,
                3.6 * factor,
                3.2 * factor,
                3.2 * factor,
                3.2 * factor,
            ),
        )
    )


def _wood_yield(lengths_in: tuple[float, float], angle_degrees: float) -> dict:
    moment = dowel_bending_yield_moment_lb_in(
        bending_yield_strength_psi=BOLT_BENDING_YIELD_PSI,
        effective_diameter_in=ROOT_DIAMETER_IN,
    )
    result = wood_wood_single_shear_reference(
        main_bearing_length_in=lengths_in[0],
        side_bearing_length_in=lengths_in[1],
        main_load_to_grain_degrees=angle_degrees,
        side_load_to_grain_degrees=angle_degrees,
        main_bolt_axis_parallel_to_grain=False,
        side_bolt_axis_parallel_to_grain=False,
        bolt_full_body_diameter_in=NOMINAL_DIAMETER_IN,
        bolt_thread_root_diameter_in=ROOT_DIAMETER_IN,
        main_thread_bearing_length_in=lengths_in[0],
        side_thread_bearing_length_in=lengths_in[1],
        bolt_bending_yield_moment_lb_in=moment,
        bolt_bending_yield_strength_psi=BOLT_BENDING_YIELD_PSI,
        gap_in=0.0,
        reduction_terms=_reductions(angle_degrees),
    )
    return {
        "load_to_grain_degrees_each_member": angle_degrees,
        "bearing_psi": {
            "first_member": result["main_bearing_psi"],
            "block": result["side_bearing_psi"],
        },
        "yield_values_lbf": result["yield_values_lbf"],
        "reference_values_lbf": result["reference_values_lbf"],
        "governing_mode": result["governing_mode"],
        "reference_lateral_n": result["reference_lateral_lbf"] * N_PER_LBF,
    }


def _bolt_steel() -> dict:
    return {
        "threaded_tensile_stress_area_in2": TENSILE_STRESS_AREA_IN2,
        "threaded_tension_asd_reference_n": (
            45_000 / 2 * TENSILE_STRESS_AREA_IN2 * N_PER_LBF
        ),
        "threaded_single_shear_asd_reference_n": (
            27_000 / 2 * TENSILE_STRESS_AREA_IN2 * N_PER_LBF
        ),
        "basis": (
            "Existing PB02 A307 comparator stresses, applied to the published "
            "3/8-16 tensile-stress area; product and long-grip applicability open"
        ),
        "long_grip_adjustment_qualified": False,
        "combined_tension_shear_qualified": False,
        "product_specific_strength_qualified": False,
    }


def _washer_bearing() -> dict:
    reference_lbf = dfl_axial_wood_bearing_reference_lbf(
        WASHER_OD_SENSITIVITY_IN,
        WASHER_CLEARANCE_ID_SENSITIVITY_IN,
        WASHER_CLEARANCE_ID_SENSITIVITY_IN,
    )
    return {
        "outside_diameter_sensitivity_in": WASHER_OD_SENSITIVITY_IN,
        "unsupported_diameter_sensitivity_in": (WASHER_CLEARANCE_ID_SENSITIVITY_IN),
        "one_inch_od_sensitivity_n": reference_lbf * N_PER_LBF,
        "actual_washer_qualified": False,
        "washer_metal_bending_qualified": False,
        "limits": "Ideal full-contact DF-L Fc-perp annulus only; not bolt capacity.",
    }


def _hardware(role: str, family: str) -> dict:
    if role == "rail":
        return {
            "retailer": "Home Depot",
            "brand": "Everbilt",
            "model": "805606",
            "nominal_length_in": 5.0,
            "listing_grade": "ASTM A307",
            "thread_basis": "fully_threaded",
            "exact_product_selected": False,
        }
    if family != "lower_inner":
        return {
            "retailer": "Lowe's",
            "brand": "Hillman",
            "model": "190231",
            "nominal_length_in": 10.0,
            "listing_grade": "Grade 1",
            "thread_basis": "unknown_transition_root_diameter_through_both_members",
            "exact_product_selected": False,
        }
    return {
        "retailer": None,
        "brand": None,
        "model": None,
        "nominal_length_in": None,
        "listing_grade": None,
        "thread_basis": "unselected_product_root_diameter_sensitivity",
        "exact_product_selected": False,
    }


def _placement(geometry, role: str, index: int) -> dict:
    diameter_mm = NOMINAL_DIAMETER_IN * MM_PER_IN
    minima = {
        "loaded_end_7d_mm": 7 * diameter_mm,
        "unloaded_end_4d_mm": 4 * diameter_mm,
        "loaded_edge_4d_mm": 4 * diameter_mm,
        "unloaded_edge_1p5d_mm": 1.5 * diameter_mm,
    }
    if role == "upright":
        along = (55.159, 100.159)[index - 1]
        distances = {
            "block_grain_end_candidates_mm": [along, 300 - along],
            "block_cross_grain_edge_candidates_mm": [28.575, 28.575],
            "upright_grain_end_candidates_mm": None,
            "upright_cross_grain_edge_candidates_mm": None,
        }
    else:
        along = (70.0, 110.0)[index - 1]
        normal = geometry.report["rail_bore_n_offset_mm"]
        distances = {
            "rail_grain_end_candidates_mm": [
                along,
                geometry.report["source_rail_length_mm"] - along,
            ],
            "rail_cross_grain_edge_candidates_mm": [normal, 139.7 - normal],
            "block_grain_end_candidates_mm": [normal, 300 - normal],
            "block_cross_grain_edge_candidates_mm": [along, 139.7 - along],
        }
    return {
        "physical_distances": distances,
        "conditional_minima": minima,
        "loaded_direction_assigned": False,
        "geometry_factor_qualified": False,
        "limits": (
            "Distances are not a pass/fail check until the same-case lateral "
            "force assigns loaded ends and edges in each member."
        ),
    }


def _group_row(role: str, lengths_in: tuple[float, float]) -> dict:
    if role == "rail":
        spacing_in = 40 / MM_PER_IN
        row_lbf = dfl_parallel_row_tear_out_reference_lbf(
            lengths_in[0], 2, 70 / MM_PER_IN, spacing_in
        )
        row_reference = row_lbf * N_PER_LBF
        applicable_member = "rail"
    else:
        spacing_in = 45 / MM_PER_IN
        row_lbf = dfl_parallel_row_tear_out_reference_lbf(
            lengths_in[1], 2, 55.159 / MM_PER_IN, spacing_in
        )
        row_reference = row_lbf * N_PER_LBF
        applicable_member = "block"
    return {
        "pair_spacing_mm": spacing_in * MM_PER_IN,
        "conditional_parallel_row_tear_out_reference_n": row_reference,
        "conditional_member": applicable_member,
        "force_parallel_to_row_established": False,
        "load_share_established": False,
        "group_factor": None,
        "qualified": False,
        "limits": "Separate Appendix E row sensitivity; not added to dowel yield.",
    }


def _stack_row(family: str, geometry, bolt) -> dict:
    role = "rail" if "_rail_" in bolt.name else "upright"
    index = int(bolt.name.rsplit("_", 1)[1])
    if role == "rail":
        lengths_mm = (38.1, 57.15)
    elif family == "lower_inner":
        lengths_mm = (38.1, 139.7)
    else:
        lengths_mm = (88.9, 139.7)
    if not math.isclose(sum(lengths_mm), bolt.grip, abs_tol=1e-6):
        raise ValueError(f"{bolt.name}: PB03 grip no longer matches member lengths")
    lengths_in = tuple(value / MM_PER_IN for value in lengths_mm)
    wood = {
        "member_bearing_lengths_mm": {
            bolt.members[0]: lengths_mm[0],
            bolt.members[1]: lengths_mm[1],
        },
        "full_body_diameter_in": NOMINAL_DIAMETER_IN,
        "thread_root_diameter_in": ROOT_DIAMETER_IN,
        "effective_bearing_diameter_in": ROOT_DIAMETER_IN,
        "root_used_in_both_members": True,
        "parallel_sensitivity": _wood_yield(lengths_in, 0),
        "perpendicular_sensitivity": _wood_yield(lengths_in, 90),
        "actual_load_to_grain_capacity_n": None,
        "limits": (
            "Two-member contacting single-shear sensitivity only; actual load "
            "angle, axis-to-grain applicability, and adjustments remain gates."
        ),
    }
    return {
        "family": family,
        "station": geometry.station,
        "name": bolt.name,
        "role": role,
        "members": list(bolt.members),
        "modeled_wood_grip_mm": bolt.grip,
        "source_geometry_authenticated": True,
        "hardware_lead": _hardware(role, family),
        "bolt_steel": _bolt_steel(),
        "wood_yield_bearing": wood,
        "end_edge_distance": _placement(geometry, role, index),
        "washer_bearing": _washer_bearing(),
        "group_row_effects": _group_row(role, lengths_in),
    }


def screen(module=None) -> dict:
    """Return source-bound component references without aggregating capacities."""
    module = PB03Native() if module is None else module
    geometries = module.pb03_geometries()
    if (
        module.KEY != SOURCE_ID
        or len(geometries) != 8
        or any(
            station not in geometries for station in REPRESENTATIVE_STATIONS.values()
        )
    ):
        raise ValueError("PB03 eight-station source identity changed")
    rows = []
    for family, station in REPRESENTATIVE_STATIONS.items():
        geometry = geometries[station]
        if len(geometry.bolts) != 4:
            raise ValueError(f"{station}: expected four PB03 stacks")
        for bolt in geometry.bolts:
            if not math.isclose(bolt.diameter, 6.35, abs_tol=1e-9):
                raise ValueError(f"{bolt.name}: modeled PB03 shaft changed")
            rows.append(_stack_row(family, geometry, bolt))

    governing = min(
        row["wood_yield_bearing"]["perpendicular_sensitivity"]["reference_lateral_n"]
        for row in rows
    )
    return {
        "schema": "simple_pb03_conditional_resistance/v1",
        "source": {
            "adapter": "scripts/simple_pb03_native.py",
            "pb03_source_id": SOURCE_ID,
            "modeled_bolt_diameter_mm": 6.35,
            "modeled_bore_diameter_mm": BORE_DIAMETER_MM,
            "candidate_bolt_diameter_mm": round(NOMINAL_DIAMETER_IN * MM_PER_IN, 6),
            "candidate_fits_modeled_bore": (
                NOMINAL_DIAMETER_IN * MM_PER_IN < BORE_DIAMETER_MM
            ),
        },
        "representative_stations": dict(REPRESENTATIVE_STATIONS),
        "stacks": rows,
        "governing_conditional_component": {
            "mechanism": "2024 NDS single-bolt lateral yield Mode IV",
            "case": "both_members_90_degrees_to_grain",
            "reference_n": governing,
        },
        "unsupported_mechanisms": [
            "same-case bolt force vectors and actual load-to-grain angles",
            "bolt-axis-parallel-to-grain and end-grain applicability",
            "block/member splitting, net section, and perpendicular tension",
            "eccentric block contact, prying, friction, preload, and withdrawal",
            "washer metal bending and nut/thread engagement or stripping",
            "combined bolt tension/shear and long-grip behavior",
            "joint-level load sharing, group action, cyclic response, and stiffness",
        ],
        "exact_unresolved_gates": [
            (
                "Current PB03 uses a 7.5 mm bore for a 6.35 mm modeled shaft; the "
                "9.525 mm candidate cannot fit until geometry, clearances, and tools "
                "are re-screened without loosening tolerances."
            ),
            (
                "Recover same-case PB03 forces before assigning loaded ends/edges, "
                "grain angles, group factors, or demand ratios."
            ),
            "Select and document an ordinary 7-inch-grip inner-upright bolt lead.",
            (
                "Measure or document Hillman 190231 thread transition and runout; "
                "root diameter is conservatively used through both members here."
            ),
            (
                "Authenticate delivered bolt root/body dimensions, bending yield, "
                "nuts, washers, and applicable long-grip treatment."
            ),
            (
                "Establish actual block stock species/grade, grain direction, "
                "moisture, duration, temperature, geometry, and group adjustments."
            ),
        ],
        "capacity_aggregation": "prohibited_serial_components_not_combined",
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(screen(), indent=2, sort_keys=True))
