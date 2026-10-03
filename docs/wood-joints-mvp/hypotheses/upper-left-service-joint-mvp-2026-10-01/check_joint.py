#!/usr/bin/env python3
"""Bound one complete service-cleat duty without promoting reference values."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = "docs/wood-joints-mvp/hypotheses/"
BLOCK = "left_service_outer_upper_cleat"
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
PREFIX = (
    "left_service/left_service_mirrored_inner_outer_hypothesis/"
    "clip_horizontal_upper_left_1/"
)
AXES = tuple(PREFIX + suffix for suffix in (
    "upper_rail_1", "upper_rail_2", "upper_side_1", "upper_side_2"
))
BOUNDARY_SOURCES = {
    "base_rail_service_upper_left": {
        *(f"contact_74_{i}" for i in range(4)),
        AXES[0] + "/plane-57", AXES[1] + "/plane-58",
        AXES[0] + "/outer-seat-axial-tie", AXES[1] + "/outer-seat-axial-tie",
    },
    "base_side_left": {
        *(f"contact_92_{i}" for i in range(4)),
        AXES[2] + "/plane-59", AXES[3] + "/plane-60",
        AXES[2] + "/outer-seat-axial-tie", AXES[3] + "/outer-seat-axial-tie",
    },
}
CASES = ("a1-rear", "a12-rear", "k12-rear")
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
LBF_N = 4.4482216152605
PSI_MPA = 0.006894757293168

# These are a proposed independent local action contract, not missing frame cases.
LATERAL_LIMIT_N = 100.0
TENSION_LIMIT_N = 150.0
FYB_SCENARIO_PSI = 45000.0
RESISTANCE_BUDGET = 0.25  # Arithmetic sensitivity, not adopted Cg or C-delta.

PINS = {
    BASE + "service-upper-frame-joint-review-2026-09-30/upper-joints.json":
        "f4c92d874dcb0f40e5e900971deaff9580e99063b453e1984e9b1ba660a2be9f",
    BASE + "service-upper-frame-joint-review-2026-09-30/freeze.json":
        "c7669530756bcdb24662c879b86545e23934fa9ea810c00b66fa08d91d051f4f",
    BASE + "upper-block-strength-2026-10-01/geometry.json":
        "2ba66f4242b59e73a7dfc14a0b21d20d1f2710b9f835d60fce569eb73353fe91",
    BASE + "upper-block-strength-2026-10-01/seats.json":
        "4463f581490842095224afefd0b355428f82668f039b2e6035dfe4ec879c96c1",
    BASE + "hardware-material-specification-2026-09-30/requirements.json":
        "15ec799c4ad02e1f8900537fad56eef2000afec4c9474d0e6c5591017f6ed100",
    "mini_moonboard/bolted_wood_wood_yield.py":
        "efefbe55279776bc42844cb0aa260bfdd2604f2599dbf9278f6b1754a33c7379",
    "mini_moonboard/bolted_timber_checks.py":
        "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13",
    "fea/dowel_yield.py":
        "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_pin(relative: str, expected: str) -> None:
    with (ROOT / relative).open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    require(actual == expected, f"Source changed: {relative}")


def norm(vector: list[float]) -> float:
    require(len(vector) == 3, "Expected three force components")
    require(all(type(x) in (int, float) and math.isfinite(x) for x in vector),
            "Nonfinite force vector")
    return math.hypot(*vector)


def force_upper_bound(vector: list[float], radii: list[float]) -> float:
    norm(vector)  # Validate the original components before abs/add transforms.
    require(all(type(x) in (int, float) and math.isfinite(x) and x >= 0
                for x in radii), "Invalid rounding radii")
    # The Euclidean norm is maximized at the sign-outward interval corner.
    return norm([abs(x) + radius for x, radius in zip(vector, radii, strict=True)])


def select_states(report: dict) -> list[dict]:
    rows = [r for r in report["bolt_actions"] if r["block"] == BLOCK]
    expected = {(axis, case, i) for axis in AXES for case in CASES for i in range(7)}
    keys = [(r["axis_id"], r["case"], r["increment_index"]) for r in rows]
    require(len(keys) == len(set(keys)), "Duplicate joint state")
    require(set(keys) == expected, "Missing or unexpected joint state")
    for row in rows:
        require(row["load_factor"] == FACTORS[row["increment_index"]],
                "Unexpected source load factor")
    return rows


def require_scope(report: dict) -> None:
    require(report["candidate"] == CANDIDATE, "Wrong candidate lane")
    require(report["geometry_revision_id"] == REVISION, "Wrong geometry revision")


def select_boundaries(report: dict) -> list[dict]:
    rows = [r for r in report["block_balances"] if r["block"] == BLOCK]
    keys = [(r["case"], r["increment_index"]) for r in rows]
    require(len(keys) == len(set(keys)) == 21
            and set(keys) == {(c, i) for c in CASES for i in range(7)},
            "Incomplete whole-cleat boundary")
    for row in rows:
        require(row["load_factor"] == FACTORS[row["increment_index"]],
                "Wrong boundary load factor")
        require(row["source_balance_reproduced"] is True
                and row["incident_connection_count"] == 16
                and row["source_load_node_count"] == 20,
                "Incomplete or unauthenticated joint balance")
        receivers = row["receiver_actions_on_block"]
        require(set(receivers) == set(BOUNDARY_SOURCES), "Wrong boundary receiver identity")
        for name, expected in BOUNDARY_SOURCES.items():
            actual = receivers[name]["source_names"]
            require(len(actual) == 8 and set(actual) == expected,
                    "Missing, duplicated or wrong boundary source")
            norm(receivers[name]["force_n"])
            norm(receivers[name]["moment_at_block_datum_nmm"])
        for field, radius in (("force_residual_n", "force_rounding_radius_n"),
                              ("moment_residual_nmm", "moment_rounding_radius_nmm")):
            norm(row[field])
            norm(row[radius])
            require(all(r >= 0 and abs(x) <= r for x, r in
                        zip(row[field], row[radius], strict=True)),
                    "Joint balance outside source rounding interval")
    return rows


def lateral_reference(lengths: tuple[float, float], angles: tuple[float, float]) -> dict:
    # ponytail: reuse the qualified arithmetic helper; do not create a joint solver.
    from mini_moonboard.bolted_wood_wood_yield import (
        dowel_bending_yield_moment_lb_in,
        wood_wood_single_shear_reference,
    )

    angle_factor = 1 + 0.25 * max(angles) / 90
    return wood_wood_single_shear_reference(
        main_bearing_length_in=lengths[0] / 25.4,
        side_bearing_length_in=lengths[1] / 25.4,
        main_load_to_grain_degrees=angles[0],
        side_load_to_grain_degrees=angles[1],
        main_bolt_axis_parallel_to_grain=False,
        side_bolt_axis_parallel_to_grain=False,
        bolt_full_body_diameter_in=0.25,
        bolt_thread_root_diameter_in=0.189,
        main_thread_bearing_length_in=0.0,
        side_thread_bearing_length_in=0.0,
        bolt_bending_yield_moment_lb_in=dowel_bending_yield_moment_lb_in(
            bending_yield_strength_psi=FYB_SCENARIO_PSI, effective_diameter_in=0.25
        ),
        gap_in=0.0,
        reduction_terms=dict(zip(MODES, (x * angle_factor for x in
                                       (4, 4, 3.6, 3.2, 3.2, 3.2)), strict=True)),
        bolt_bending_yield_strength_psi=FYB_SCENARIO_PSI,
    )


def profile_screen(hardware: dict, *, runout_start: float,
                   full_form_interval: tuple[float, float], tip: float) -> dict:
    """Screen a declared profile, keeping functional nut fit separate."""
    require(all(type(x) in (int, float) and math.isfinite(x)
                for x in (runout_start, *full_form_interval, tip)),
            "Invalid declared thread coordinates")
    require(0 <= runout_start <= full_form_interval[0] < full_form_interval[1] <= tip,
            "Inconsistent declared thread profile")
    fractions = []
    for member in hardware["member_requirements"]:
        a, b = member["conservative_interval_underhead_mm_at_max_published_head_washer"]
        fractions.append(max(0.0, b - max(a, runout_start)) / (b - a))
    nut = hardware["nut_and_tip_requirements"]
    required = nut["full_thread_sufficient_profile_condition"]
    a, b = required["continuous_full_form_interval_must_cover_mm"]
    return {
        "status": "specified_geometry_only_not_matched_nut_fit",
        "earliest_runout_mm": runout_start, "full_form_interval_mm": list(full_form_interval),
        "physical_tip_mm": tip, "thread_bearing_fractions": fractions,
        "quarter_thread_condition_met": max(fractions) <= 0.25,
        "sufficient_external_nut_envelope_coverage_met": full_form_interval[0] <= a
                                                        and full_form_interval[1] >= b,
        "physical_tip_requirement_met": tip >= nut["minimum_physical_tip_target_underhead_mm"],
        "matched_nut_functional_fit_established": False,
    }


def produce() -> dict:
    for relative, expected in PINS.items():
        verify_pin(relative, expected)
    sys.path.insert(0, str(ROOT))
    reports = {
        Path(relative).name: json.loads((ROOT / relative).read_text())
        for relative in PINS if relative.endswith(".json")
    }
    action = reports["upper-joints.json"]
    for name in ("upper-joints.json", "freeze.json", "geometry.json", "seats.json"):
        require_scope(reports[name])
    rows = select_states(action)
    # Bind the referenced raw source files and exact solids. This authenticates
    # archived evidence; it does not independently reinterpret native RF tokens.
    source_pins = dict(PINS)
    for case in reports["freeze.json"]["cases"].values():
        for record in case.values():
            verify_pin(record["path"], record["sha256"])
            source_pins[record["path"]] = record["sha256"]
    geometries = {axis: action["geometry_by_axis"][axis] for axis in AXES}
    for geometry in geometries.values():
        require(geometry["block"] == BLOCK, "Wrong cleat geometry")
        for member in geometry["members"].values():
            verify_pin(member["finished_step"], member["finished_step_sha256"])
            source_pins[member["finished_step"]] = member["finished_step_sha256"]

    balances = select_boundaries(action)

    seats = [r for r in reports["seats.json"]["geometry_seats"] if r["axis_id"] in AXES]
    require({(r["axis_id"], r["seat_role"]) for r in seats}
            == {(axis, side) for axis in AXES for side in ("head", "nut")}
            and len(seats) == 8, "Incomplete head/nut seat inventory")
    support = all(s["scenario_support"]["catalog_minimum_area"]
                  ["support_status"] == "full_modeled_support" for s in seats)
    washer_area = math.pi * (18.4658**2 - 8.3058**2) / 4
    timber_seat_reference_n = washer_area * 625 * PSI_MPA
    steel_root_area = math.pi * (0.189 * 25.4)**2 / 4

    components = []
    for row in rows:
        geometry = geometries[row["axis_id"]]
        lengths = tuple(geometry["members"][role]["bearing_length_mm"]
                        for role in ("block", "host"))
        angles = tuple(row["member_directions"][role]["unsigned_load_to_grain_degrees"]
                       for role in ("block", "host"))
        ref = min(lateral_reference(lengths, angles)["reference_lateral_lbf"],
                  lateral_reference(lengths[::-1], angles[::-1])["reference_lateral_lbf"])
        lateral = force_upper_bound(row["lateral_force_on_block_n"],
                                    row["lateral_force_rounding_radius_n"])
        tension = force_upper_bound(row["axial_force_on_block_n"],
                                    row["axial_force_rounding_radius_n"])
        require(math.isclose(norm(row["axial_force_on_block_n"]), row["axial_tension_n"],
                             abs_tol=1e-8), "Axial action/scalar inconsistency")
        components.append({
            "axis_id": row["axis_id"], "case": row["case"],
            "increment_index": row["increment_index"],
            "lateral_upper_n": lateral, "tension_upper_n": tension,
            "lateral_45ksi_reference_n": ref * LBF_N,
            "lateral_reference_ratio_at_25_percent_budget": lateral / (ref * LBF_N * RESISTANCE_BUDGET),
            "ideal_wood_seat_ratio_at_quarter_area": tension / (timber_seat_reference_n / 4),
            "nominal_same_root_axial_shear_first_yield_ratio":
                math.hypot(tension, math.sqrt(3) * lateral) / (steel_root_area * 92000 * PSI_MPA),
        })
    hardware = [r for r in reports["requirements.json"]["axis_requirements"]
                if r["axis_id"] in AXES]
    require({r["axis_id"] for r in hardware} == set(AXES) and len(hardware) == 4,
            "Incomplete hardware requirements")
    hardware_rows = [{
        "axis_id": r["axis_id"],
        "receiver_ids_head_to_nut": r["raw_receiver_ids_head_to_nut"],
        "nominal_length_class_in": r["source_backed_length_comparisons"][0]["nominal_class_in"],
        "earliest_thread_or_runout_required_min_mm": r["NDS_nominal_D_quarter_thread_screen"]
            ["minimum_LB_underhead_to_last_thread_scratch_mm_for_all_members"],
        "required_continuous_external_full_form_interval_mm": r["nut_and_tip_requirements"]
            ["full_thread_sufficient_profile_condition"]["continuous_full_form_interval_must_cover_mm"],
        "physical_tip_required_min_mm": r["nut_and_tip_requirements"]
            ["minimum_physical_tip_target_underhead_mm"],
    } for r in hardware]
    for raw, row in zip(hardware, hardware_rows, strict=True):
        # Hypothetical profiles inside the conditional length-class space;
        # these are specifications to source, not claims about a catalog item.
        six_inch = row["nominal_length_class_in"] == 6.0
        row["declared_profile_screen"] = profile_screen(
            raw, runout_start=127.0 if six_inch else 171.45,
            full_form_interval=(128.0, 148.0) if six_inch else (173.0, 196.0),
            tip=149.86 if six_inch else 198.628,
        )
    worst_direction = lateral_reference((88.9, 38.1), (90.0, 90.0))["reference_lateral_lbf"] * LBF_N
    return {
        "schema": "one-service-joint-mvp-disposition/v1", "block": BLOCK,
        "candidate": action["candidate"], "geometry_revision_id": REVISION,
        "status": "HOLD_COMPLETE_JOINT_EVIDENCE_MISSING",
        "source_pins": source_pins,
        "source_cases": list(CASES), "missing_frame_cases": ["a12-forward", "a12-left", "k12-right"],
        "counts": {"bolt_states": len(rows), "whole_boundary_states": len(balances),
                   "incident_ports_per_state": 16, "nominal_washer_seats": len(seats)},
        "assumed_local_contract": {
            "status": "proposed_not_a_joint_rating", "per_bolt_lateral_limit_n": LATERAL_LIMIT_N,
            "per_bolt_tension_limit_n": TENSION_LIMIT_N,
            "all_saved_states_inside_force_box": all(r["lateral_upper_n"] <= LATERAL_LIMIT_N
                                                      and r["tension_upper_n"] <= TENSION_LIMIT_N
                                                      for r in components),
            "limitations": "No bound on prying, local bolt bending, contact tractions, slip or member stress."
        },
        "component_scenario": {
            "status": "arithmetic_only_not_adopted_resistance", "Fyb_psi": FYB_SCENARIO_PSI,
            "lateral_resistance_multiplier_budget": RESISTANCE_BUDGET,
            "force_box_to_worst_direction_reference_budget_ratio":
                LATERAL_LIMIT_N / (worst_direction * RESISTANCE_BUDGET),
            "tension_box_to_quarter_area_ideal_wood_seat_ratio":
                TENSION_LIMIT_N / (timber_seat_reference_n / 4),
            "all_eight_nominal_seats_supported_in_source_CAD": support,
            "limitations": "Nominal full-D, zero-gap, DF-L No.2, G=.50, dry/normal; "
                          "Fyb=45ksi and 25% budget are unadopted scenarios. Steel excludes bending; "
                          "quarter-area average compression does not qualify washer metal/contact."
        },
        "components": components, "complete_same_state_receiver_wrenches": balances,
        "hardware_requirements": hardware_rows,
        "remaining_joint_gates": [
            "coupled_bolt_head_nut_washer_contact_and_metal_resistance",
            "finished_member_sections_local_splitting_and_group_applicability",
            "selected_hardware_functional_thread_fit_and_material_basis",
            "joint_slip_rotation_and_frame_compatibility",
            "finite_installed_clearance_tools_removal_and_cost",
            "supported_shop_sequence_and_individual_member_transport",
            "authenticated_missing_frame_cases_or_adopted_local_envelope_coverage",
        ],
        "local_joint_mvp_complete": False, "complete_joint_accepted": False,
        "six_case_envelope_established": False, "geometry_changed": False,
        "native_solve_executed": False, "fabrication_released": False,
        "drilling_released": False, "structural_released": False, "climbing_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(produce(), indent=2, sort_keys=True))
