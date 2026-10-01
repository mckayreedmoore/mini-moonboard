#!/usr/bin/env python3
"""Source-pinned axial tie, washer pressure, and component-reference screen."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKET_ROOT = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"

INPUTS = {
    "corner_demand_report": (
        PACKET_ROOT / "current-corner-native-demand-export-attempt03/corner-demand-report.json",
        "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    ),
    "existing_conditional_resistance_screen": (
        PACKET_ROOT / "current-corner-a12-conditional-resistance-screen-attempt01/screen.json",
        "ee247af7e2271e63dcf1f8d8b86ef5eeca203f3dec3e37c55f2f6a8addb1e5cb",
    ),
    "washer_geometry_and_candidate_register": (
        PACKET_ROOT / "current-corner-washer-seat-screen-attempt01/seat-screen.json",
        "67dda5964a9c2a864cdb5ee0e898bae3c9e6bea212e2eeb71d5b33f765481ef0",
    ),
    "wood_bearing_helper": (
        ROOT / "mini_moonboard/bolted_timber_checks.py",
        "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13",
    ),
    "bolt_first_yield_helper": (
        ROOT / "mini_moonboard/wood_joint_bolt_resistance.py",
        "488e58bbd58fbc2f22af5d4122e734732bae09de79dad71bbf2623eeca60b166",
    ),
    "bolt_resistance_method_note": (
        ROOT / "docs/wood-joints-mvp/bolt-resistance-basis.md",
        "1b5e1a261735f7630c0c45fe505a4755227dd88d52091f112141f0c1332f0d80",
    ),
    "conditional_grade5_bolt_scenario": (
        ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-bolt-steel-reference-attempt01/README.md",
        "8f14fbd47e1571ff8dae3a2907fc8c46f49b2a61216cc2c6525b7e4c87dae310",
    ),
    "washer_dimension_scenario": (
        ROOT / "docs/wood-joints-mvp/current-ordinary-nut-washer-property-basis.md",
        "98a151ae040232aa1f2485826ba4c29dc0e0d0fb1ce6ac87ddd9bf062eeb6bcf",
    ),
    "current_candidate_hardware_coverage": (
        ROOT / "docs/wood-joints-mvp/current-hardware-coverage.md",
        "6bda5d032d52c8da38e069548153dbfe93c6bdfeea6f8ded1ba4f650cf75dd8c",
    ),
}

MODEL_INPUT = (
    PACKET_ROOT / "current-springa-selected-floor-a12-rear-attempt03/model.json",
    "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
)

AXES = {
    "knee_outer_left_post_1": "BG001",
    "knee_outer_left_post_2": "BG001",
    "knee_outer_left_side_1": "BG003",
    "knee_outer_left_side_2": "BG003",
    "knee_outer_left_inner_header_1": "BG045",
    "knee_outer_left_inner_header_2": "BG045",
}

PSI_TO_MPA = 0.006894757293168361
LBF_TO_N = 4.4482216152605
IN_TO_MM = 25.4


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"source or method gate failed: {message}")


def load_bearing_helper():
    path = ROOT / "mini_moonboard/bolted_timber_checks.py"
    spec = importlib.util.spec_from_file_location("pinned_bolted_timber_checks", path)
    if spec is None or spec.loader is None:
        raise SystemExit("could not load pinned wood bearing helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.dfl_axial_wood_bearing_reference_lbf


def source_pins() -> dict:
    result = {}
    for name, (path, expected) in INPUTS.items():
        actual = sha256(path)
        require(actual == expected, f"{name} SHA-256 changed ({actual})")
        result[name] = {"path": path.relative_to(ROOT).as_posix(), "sha256": actual}
    model_path, expected_model = MODEL_INPUT
    actual_model = sha256(model_path)
    require(actual_model == expected_model, f"a12-rear model SHA-256 changed ({actual_model})")
    result["a12_rear_source_model"] = {
        "path": model_path.relative_to(ROOT).as_posix(),
        "sha256": actual_model,
    }
    producer = Path(__file__).resolve()
    result["producer"] = {
        "path": producer.relative_to(ROOT).as_posix(),
        "sha256": sha256(producer),
    }
    return result


def build_report() -> dict:
    pins = source_pins()
    report = read_json(INPUTS["corner_demand_report"][0])
    prior = read_json(INPUTS["existing_conditional_resistance_screen"][0])
    geometry = read_json(INPUTS["washer_geometry_and_candidate_register"][0])
    model = read_json(MODEL_INPUT[0])

    require(report.get("schema") == "current_corner_native_demand_report/v1", "corner report schema")
    require(report.get("status") == "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY", "corner report status")
    require(report.get("actual_case_demand_usable_for_conditional_joint_checks") is True,
            "corner demand source is not marked usable")
    auth = report["authenticated_source_case"]
    require(auth.get("case_id") == "a12-rear", "source case is not a12-rear")
    require(auth.get("input_model_json_sha256") == pins["a12_rear_source_model"]["sha256"],
            "corner report model binding")
    require(report.get("qualification_boundary", {}).get("complete_joint_accepted") is False,
            "source does not preserve the no-acceptance boundary")
    require(prior.get("status") == "PASS_SOURCE_BOUND_CONDITIONAL_COMPARABILITY_SCREEN_ONLY", "prior screen status")

    final_rows = [row for row in report["increments"] if row.get("load_factor") == 1.0]
    require(len(final_rows) == 1, "expected exactly one full-load increment")
    final = final_rows[0]
    gates = final["response_audit_gates"]
    required_gates = (
        "mpc_interval_checks_passed",
        "springa_law_checks_passed",
        "retained_bilateral_checks_passed",
        "selected_floor_complementarity_passed",
        "inactive_floor_tangent_no_restraint_or_reaction_passed",
        "raw_balance_passed",
        "rounding_interval_balance_passed",
    )
    require(all(gates.get(key) is True for key in required_gates), "full-load response gates")
    require(final.get("all_five_corner_bodies_raw_and_interval_balance_passed") is True,
            "five-body corner balance")
    global_gates = final.get("audited_global_equilibrium", {})
    require(global_gates.get("printed_resultants_passed") is True and
            global_gates.get("interval_resultants_passed") is True,
            "all-body/global balance")

    geometry_by_axis = {row["axis_id"]: row for row in geometry["axes"]}
    require(set(AXES).issubset(geometry_by_axis), "washer geometry missing one of six corner axes")
    seats_by_axis: dict[str, list[dict]] = {axis: [] for axis in AXES}
    for row in final["outer_washer_seats"]:
        if row.get("axis_id") in seats_by_axis:
            seats_by_axis[row["axis_id"]].append(row)
    require(all(len(rows) == 2 for rows in seats_by_axis.values()), "expected two outer seats per bolt")
    require(len(final["outer_washer_seats"]) == 12, "expected exactly twelve outer washer seats")

    helper = load_bearing_helper()
    # Existing 25NWUS dimensional scenario: Type A Wide size envelope; use
    # minimum OD and maximum ID as the minimum full-annulus geometry scenario.
    washer_min_od_in = 0.727
    washer_max_id_in = 0.327
    type_a_dims = geometry_by_axis["knee_outer_left_post_1"]["outer_seats"][0]
    wood_bore_radius_mm = type_a_dims["modeled_finished_wood_bore_radius_mm"]
    wood_bore_diameter_in = 2.0 * wood_bore_radius_mm / IN_TO_MM
    conditional_area_in2 = math.pi / 4.0 * (
        washer_min_od_in**2 - max(washer_max_id_in, wood_bore_diameter_in) ** 2
    )
    conditional_area_mm2 = conditional_area_in2 * IN_TO_MM**2
    fc_ref_lbf = helper(washer_min_od_in, wood_bore_diameter_in, washer_max_id_in)
    fc_ref_n = fc_ref_lbf * LBF_TO_N

    axes_out = []
    seats_out = []
    pressure_limitations = [
        "All pressure values are full-annulus uniform averages, not local contact-pressure fields.",
        "The CAD-derived annular plan area is not the verified effective wood contact area.",
        "The 25NWUS dimensions are an unselected candidate range, not delivered washer measurements.",
        "Full annular support on sound, flat wood is conditional; finished support polygons, cuts, gaps, and flatness are unresolved.",
    ]
    fy_mpa = 92000.0 * PSI_TO_MPA
    at_mm2 = 0.0318 * IN_TO_MM**2
    bolt_yield_ref_n = fy_mpa * at_mm2

    for axis_id, group in AXES.items():
        source_axis = geometry_by_axis[axis_id]
        lead_ids = source_axis.get("conditional_washer_lead_ids_in_axis_register", [])
        product_lead = "kl-25nwus" in lead_ids
        require(source_axis.get("washer_product_status") == "not_selected_or_delivered",
                f"washer selection status changed on {axis_id}")
        rows = sorted(seats_by_axis[axis_id], key=lambda row: row["seat_role"])
        ties = [float(row["signed_outer_seat_tie_action_n"]) for row in rows]
        require(min(ties) > 0 and abs(ties[0] - ties[1]) <= 1e-9,
                f"two seat demands do not match on {axis_id}")
        force_components = [row["seat_force_on_member_xyz_n"] for row in rows]
        axis_force_magnitudes = [math.sqrt(sum(float(v) ** 2 for v in vec)) for vec in force_components]
        require(all(abs(mag - ties[0]) <= 1e-6 for mag in axis_force_magnitudes),
                f"seat force vector magnitude does not match tie on {axis_id}")
        require(all(abs(float(force_components[0][j]) + float(force_components[1][j])) <= 1e-6
                     for j in range(3)), f"outer seat actions are not equal and opposite on {axis_id}")
        areas = [float(row["modeled_outer_washer_annular_area_mm2"]) for row in rows]
        require(max(areas) - min(areas) <= 1e-6, f"paired CAD washer areas differ on {axis_id}")
        tension = ties[0]
        axis_seats = []
        for row in rows:
            member = row["physical_member"]
            source_seat = next(
                seat for seat in source_axis["outer_seats"]
                if seat["outer_receiver_member_id"] == member and seat["seat_role"] == row["seat_role"]
            )
            cad_area = float(row["modeled_outer_washer_annular_area_mm2"])
            cad_pressure = tension / cad_area
            candidate_pressure = tension / conditional_area_mm2 if product_lead else None
            is_dfl2_fc_perp_eligible = (
                member in {"base_post_outer_left", "base_header"}
                and source_seat.get("member_kind") == "timber"
                and source_seat.get("load_grain_relation") == "perpendicular_to_proposed_grain"
                and product_lead
            )
            if is_dfl2_fc_perp_eligible:
                ref_status = "conditional_unadjusted_full_annulus_DF_L_No2_Fc_perp_reference"
                wood_ref_n = fc_ref_n
                wood_ratio = tension / wood_ref_n
                wood_area_mm2 = conditional_area_mm2
                wood_pressure = candidate_pressure
            else:
                wood_ref_n = None
                wood_ratio = None
                wood_area_mm2 = None
                wood_pressure = None
                if source_seat.get("load_grain_relation") == "parallel_to_proposed_grain":
                    ref_status = "Fc_perp_inapplicable_parallel_to_proposed_grain"
                elif source_seat.get("member_kind") == "candidate_block":
                    ref_status = "not_applied_candidate_block_strength_grade_not_assigned"
                elif not product_lead:
                    ref_status = "no_25NWUS_washer_lead_for_axis"
                else:
                    ref_status = "no_applicable_Fc_perp_reference"

            hypothetical_block = None
            if source_seat.get("member_kind") == "candidate_block":
                if source_seat.get("load_grain_relation") == "perpendicular_to_proposed_grain":
                    # This is a separate, non-adopted material scenario. Where
                    # there is no washer product lead, it uses the modeled CAD
                    # washer annulus and explicitly assumes full wood support.
                    block_area = conditional_area_mm2 if product_lead else cad_area
                    if product_lead:
                        block_ref_n = fc_ref_n
                        area_basis = "25NWUS Type A minimum-annulus dimensional scenario"
                    else:
                        block_ref_n = 625.0 * PSI_TO_MPA * block_area
                        area_basis = "modeled CAD washer annular plan area; opening and effective wood area are not separately dimensioned"
                    hypothetical_block = {
                        "status": "hypothetical_DF_L_No2_only_not_assigned_to_candidate_block",
                        "assumed_material": "sound DF-L No. 2 with Fc_perp=625 psi",
                        "assumed_load_direction": "perpendicular_to_proposed_grain",
                        "full_supported_annulus_area_mm2": block_area,
                        "area_basis": area_basis,
                        "unadjusted_Fc_perp_reference_n": block_ref_n,
                        "demand_over_reference_component_ratio": tension / block_ref_n,
                        "uniform_average_pressure_mpa": tension / block_area,
                        "limit": "separate what-if arithmetic only; model binds candidate_block to an elastic Douglas-fir diagnostic without a strength grade",
                    }
                else:
                    hypothetical_block = {
                        "status": "Fc_perp_not_applicable_parallel_to_proposed_grain",
                        "assumed_material": None,
                        "limit": "no parallel-to-grain bearing strength or comparison is assigned here",
                    }

            seat_out = {
                "group_id": group,
                "axis_id": axis_id,
                "physical_member": member,
                "seat_role": row["seat_role"],
                "seat_point_global_xyz_mm": row["seat_point_global_xyz_mm"],
                "seat_force_on_member_xyz_n": row["seat_force_on_member_xyz_n"],
                "positive_bolt_tension_tie_demand_n": tension,
                "wood_receiver_kind": source_seat["member_kind"],
                "load_grain_relation": source_seat["load_grain_relation"],
                "conditional_washer_lead_ids": lead_ids,
                "modeled_cad_annular_plan_area_mm2": cad_area,
                "modeled_cad_full_annulus_uniform_average_pressure_mpa": cad_pressure,
                "conditional_25nwus_minimum_annulus_scenario": (
                    {
                        "status": "candidate_dimensions_only_not_selected_or_delivered",
                        "minimum_od_in": washer_min_od_in,
                        "maximum_id_in": washer_max_id_in,
                        "modeled_wood_bore_diameter_in": wood_bore_diameter_in,
                        "governing_inner_diameter_in": max(washer_max_id_in, wood_bore_diameter_in),
                        "full_annulus_area_mm2": conditional_area_mm2,
                        "uniform_average_pressure_mpa": candidate_pressure,
                    }
                    if product_lead else None
                ),
                "conditional_wood_bearing_component": {
                    "status": ref_status,
                    "conditional_full_annulus_area_mm2": wood_area_mm2,
                    "unadjusted_Fc_perp_reference_n": wood_ref_n,
                    "demand_over_reference_component_ratio": wood_ratio,
                    "conditional_uniform_average_pressure_mpa": wood_pressure,
                    "limit": "wood-bearing component comparison only; no washer-steel, bolt, member, or joint resistance is implied",
                },
                "separate_hypothetical_block_DF_L_No2_scenario": hypothetical_block,
            }
            axis_seats.append(seat_out)
            seats_out.append(seat_out)

        axes_out.append({
            "group_id": group,
            "axis_id": axis_id,
            "receiver_members": [row["physical_member"] for row in rows],
            "positive_outer_seat_tie_tension_demand_n": tension,
            "outer_seat_count": 2,
            "washer_lead_ids": lead_ids,
            "washer_selected_or_delivered": False,
            "conditional_1_4_20_unc_grade5_bolt_material_screen": {
                "status": "conditional_material_first_yield_reference_only",
                "assumptions": {
                    "nominal_thread": "1/4-20 UNC",
                    "project_specified_minimum_yield_psi": 92000.0,
                    "thread_tensile_stress_area_in2": 0.0318,
                    "thread_tensile_stress_area_mm2": at_mm2,
                },
                "unadjusted_tensile_first_yield_reference_n": bolt_yield_ref_n,
                "axial_tension_demand_over_reference_component_ratio": tension / bolt_yield_ref_n,
                "basis": "Fy * At from the pinned ordinary 1/4-20 Grade 5 conditional scenario; not a selected product, delivered-property claim, design resistance, or acceptance ratio",
                "actual_product_axis_status": (
                    "K.L. Jack 1/4-20 x 4 in Grade 5 cap-screw and 25NWUS washer are candidate leads; neither selected nor delivered, and fit remains unresolved"
                    if group == "BG001" else
                    "modeled 9.25 in length has no exact bolt SKU; a 9.5 in Ro-Brand listing is an unresolved lead and is not confirmed to the Grade 5 scenario; no washer lead"
                    if group == "BG003" else
                    "7.75 in length has no exact bolt SKU; Lawson/FalconGrip 1/4-20 x 8 in Grade 5 is an alternate lead, with a 25NWUS washer lead; neither selected/delivered nor fit-confirmed"
                ),
                "combined_axial_shear_interaction": "not_calculated; no common controlling section or applicable interaction rule supplied",
            },
            "seats": axis_seats,
        })

    require(len(seats_out) == 12, "output seat count")
    return {
        "schema": "current_corner_axial_tie_and_washer_seat_component_screen/v1",
        "status": "CONDITIONAL_COMPONENT_SCREENS_ONLY",
        "scope": {
            "candidate": report["candidate"],
            "geometry_revision_id": report["geometry_revision_id"],
            "case_id": auth["case_id"],
            "load_factor": 1.0,
            "groups": ["BG001", "BG003", "BG045"],
            "axis_count": len(axes_out),
            "end_seat_count": len(seats_out),
            "retained_original_leg_runner_arrangements_reopened": False,
            "native_solve_launched_by_this_screen": False,
            "geometry_or_model_changed": False,
            "joint_acceptance": False,
        },
        "source_pins": pins,
        "authenticated_response_scope": {
            "corner_demand_report_status": report["status"],
            "response_sha256": auth["response_audit_json_sha256"],
            "source_model_sha256": auth["input_model_json_sha256"],
            "parent_terminal_assessment_status": auth["adjacent_native_execution_evidence"]["parent_terminal_assessment"]["status"],
            "parent_all_body_balance_passed": auth["adjacent_native_execution_evidence"]["parent_terminal_assessment"]["independent_parent_all_body_pass"],
            "response_and_corner_balance_gates_passed_at_factor_1": True,
            "floor_branch": report["selected_floor_response_scope"]["branch_id"],
            "floor_branch_remains_diagnostic_only": report["selected_floor_response_scope"]["branch_is_diagnostic_not_floor_or_joint_acceptance"],
        },
        "conditional_material_and_hardware_scenarios": {
            "wood": {
                "base_member_scenario": "DF-L No. 2 table reference Fc_perp=625 psi for sound wood, full-supported annulus and transverse loading only",
                "base_timber_model_assignment": model["material_binding"]["material_categories"]["timber"],
                "candidate_block_model_assignment": model["material_binding"]["material_categories"]["candidate_block"],
                "candidate_blocks": "model binds a distinct elastic diagnostic category with no strength grade/Fc_perp; separately labeled DF-L No. 2 what-if arithmetic is present only for transverse seats",
                "helper": "mini_moonboard.bolted_timber_checks.dfl_axial_wood_bearing_reference_lbf",
            },
            "washer": {
                "candidate": "K.L. Jack 25NWUS / ASME B18.21.1 Type A Wide dimensional scenario",
                "dimensional_envelope_used_for_minimum_annulus": {
                    "minimum_outer_diameter_in": washer_min_od_in,
                    "maximum_outer_diameter_in": 0.749,
                    "minimum_inner_diameter_in": 0.307,
                    "maximum_inner_diameter_in": washer_max_id_in,
                    "thickness_range_in": [0.051, 0.080],
                    "modeled_wood_bore_diameter_in": wood_bore_diameter_in,
                    "full_annulus_area_mm2": conditional_area_mm2,
                },
                "product_selected_or_delivered": False,
                "steel_bending_spreading_resistance": "unresolved; no numeric yield basis or supported washer-on-timber plate/contact method",
            },
            "bolt": {
                "scenario_id": "conditional_1_4_20_unc_grade5_project_requirement",
                "minimum_yield_psi": 92000.0,
                "tensile_stress_area_in2": 0.0318,
                "tensile_stress_area_mm2": at_mm2,
                "unadjusted_direct_tension_first_yield_reference_n": bolt_yield_ref_n,
                "specific_product_or_delivered_conformance": False,
                "helper_note": "bolt_first_yield_reference requires a lateral shear-plane area and basis before returning any result; this screen uses only the separately documented Fy*At tension component and does not invent a shear area or interaction.",
            },
        },
        "axis_hardware_context_from_existing_coverage": {
            "BG001_post_pair": "4 in Grade 5 1/4-20 cap-screw candidate and 25NWUS washer lead; no delivered conformance or fitted stack is established",
            "BG003_side_pair": "9.25 in modeled length has no exact bolt SKU; 9.5 in Ro-Brand lead is not confirmed to the Grade 5 scenario; no washer lead is listed",
            "BG045_inner_header_pair": "7.75 in modeled length has no exact bolt SKU; Lawson/FalconGrip 8 in Grade 5 cap screw and 25NWUS washer are alternate leads; no delivered conformance or fitted stack is established",
            "scope_note": "The same explicit hypothetical 1/4-20 UNC Grade 5 performance scenario is shown for arithmetic on all six model axes, but it does not imply that six matching, installable products are sourced.",
        },
        "calculation_notes": {
            "cad_pressure_equation": "signed tie tension magnitude (N) / CAD-derived annular plan area (mm^2) = MPa uniform-average scenario",
            "washer_candidate_area_equation": "pi/4 * (minimum Type A Wide OD^2 - max(maximum ID, modeled bore diameter)^2), converted from in^2 to mm^2",
            "wood_reference_helper_inputs": {
                "minimum_outer_diameter_in": washer_min_od_in,
                "wood_bore_diameter_in": wood_bore_diameter_in,
                "maximum_washer_inner_diameter_in": washer_max_id_in,
                "Fc_perp_psi": 625.0,
                "reference_force_n": fc_ref_n,
            },
            "bolt_tension_equation": "Fy * At = 92,000 psi * 0.0318 in^2 = unadjusted first-yield material reference",
            "pressure_limits": pressure_limitations,
        },
        "axes": axes_out,
        "seat_inventory": seats_out,
        "overall_limits": [
            "A12-rear at load factor 1.0 is one conditional numerical demand case, not a six-case envelope or adopted-joint acceptance.",
            "Only the two base-post and two base-header seats receive conditional DF-L No. 2 Fc-perp component references; candidate-block strength is not sourced, and the BG045 inner-block seats load parallel to the proposed grain.",
            "25NWUS is a dimensional candidate lead on BG001 and BG045 axes only; none of the six washer pairs is selected or delivered. BG003 has no listed washer lead.",
            "Actual net washer contact area still needs delivered ID/OD/thickness, head/nut footprint, finished bore, support polygon, cuts, flatness, and fit; CAD annular plan area is not this evidence.",
            "No washer steel bending/spreading, head/nut pull-through, nut stripping/engagement, bolt fracture, or combined tension-shear interaction is checked.",
            "The conditional Grade 5 bolt first-yield comparison is a material component reference only. Exact bolt/thread identity, actual conformance, controlling section/thread placement, nut engagement, other load cases, and a design resistance method remain open.",
            "No preload, friction, or unmodeled load sharing is credited.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    output = HERE / "screen.json"
    generated = json.dumps(build_report(), indent=2, sort_keys=True) + "\n"
    if args.write:
        output.write_text(generated)
        print(f"wrote {output.relative_to(ROOT)}")
    else:
        require(output.exists(), "screen.json is missing; run --write first")
        require(output.read_text() == generated, "screen.json differs from regenerated result")
        print("PASS: source pins and reproducible axial tie/washer component calculations")
    print(f"screen_sha256={sha256(output) if output.exists() else 'written'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
