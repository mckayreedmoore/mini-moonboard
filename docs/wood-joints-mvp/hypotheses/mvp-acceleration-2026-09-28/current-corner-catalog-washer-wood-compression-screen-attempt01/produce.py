#!/usr/bin/env python3
"""Replay conditional wood-seat stress/reference comparisons for all 252 states."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HARDWARE = ROOT / "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30"
SOURCE_PINS = HERE / "source-pins.json"
SOURCE_PINS_SHA256 = "37b2c98c0bb0f60c9f4b7d5d683a0376d3200f8cd8e8b83a340409ca0e039fde"
INPUT_SEATS = PACKET / "current-corner-three-case-axial-seat-register-attempt01/axial-seat-register.json"
MATERIAL_INPUTS = HARDWARE / "material-inputs.json"
FASTENER_INPUTS = HARDWARE / "fastener-inputs.json"
WASHER_GEOMETRY = PACKET / "current-corner-washer-seat-screen-attempt01/seat-screen.json"
OUTPUT = HERE / "seat-compression-screen.json"

PSI_TO_MPA = 0.006894757293168361
IN_TO_MM = 25.4
SIGN_EPSILON_N = 1e-9
TOL = 2e-7
EXPECTED_CASES = {"a12-rear", "a1-rear", "k12-rear"}
EXPECTED_GROUP_AXES = {
    "BG001": {"knee_outer_left_post_1", "knee_outer_left_post_2"},
    "BG003": {"knee_outer_left_side_1", "knee_outer_left_side_2"},
    "BG045": {"knee_outer_left_inner_header_1", "knee_outer_left_inner_header_2"},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"washer wood-compression source/method gate failed: {message}")


def close(a: float, b: float, tol: float = TOL) -> bool:
    return math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=tol)


def unit(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(float(x) * float(x) for x in vector))
    require(norm > 0.0 and math.isfinite(norm), "finite nonzero seat force normal")
    return [float(x) / norm for x in vector]


def verify_source_pins() -> dict:
    require(sha256(SOURCE_PINS) == SOURCE_PINS_SHA256, "source-pins.json hash changed")
    pins = read_json(SOURCE_PINS)
    require(pins.get("schema") == "current_corner_catalog_washer_wood_compression_source_pins/v1",
            "source pin manifest schema")
    pinned_paths = {}
    for item in pins.get("files", []):
        path = ROOT / item["path"]
        require(path.is_file(), f"pinned file missing: {item['path']}")
        actual = sha256(path)
        require(actual == item["sha256"], f"pinned file changed: {item['path']} ({actual})")
        pinned_paths[item["path"]] = actual
    for record in (pins["input_case_register"],):
        require(pinned_paths.get(record["path"]) == record["sha256"],
                f"input axial-seat register is pinned: {record['path']}")
        require(pinned_paths.get(record["source_pin_manifest_path"]) ==
                record["source_pin_manifest_sha256"], "input axial-seat source pin manifest is pinned")
    require(pinned_paths.get("docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/material-inputs.json") ==
            sha256(MATERIAL_INPUTS), "material input packet is pinned")
    require(pinned_paths.get("docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/fastener-inputs.json") ==
            sha256(FASTENER_INPUTS), "fastener input packet is pinned")
    return pins


def build_grain_map(materials: dict) -> dict[str, list[float]]:
    by_member: dict[str, list[float]] = {}
    for rows in materials["primary_corner_members"].values():
        for row in rows:
            member = row["member_id"]
            grain = [float(x) for x in row["proposed_grain_global_xyz"]]
            if member in by_member:
                require(all(close(a, b, 1e-12) for a, b in zip(by_member[member], grain)),
                        f"consistent proposed grain vector for {member}")
            by_member[member] = grain
    return by_member


def classify_bearing_direction(normal: list[float], grain: list[float]) -> tuple[str, float]:
    n = unit(normal)
    g = unit(grain)
    cosine = abs(sum(a * b for a, b in zip(n, g)))
    cosine = min(1.0, max(0.0, cosine))
    if cosine >= 1.0 - 1e-7:
        return "parallel_to_proposed_grain", cosine
    if cosine <= 1e-7:
        return "perpendicular_to_proposed_grain", cosine
    raise SystemExit(f"bearing direction is oblique to proposed grain (|cos(theta)|={cosine:.12g}); no method adopted")


def selected_material_reference(materials: dict, member_id: str, direction: str) -> tuple[float, str, str]:
    base = materials["conditional_DF_L_No2_base_row"]["base_properties"]
    if direction == "perpendicular_to_proposed_grain":
        if member_id == "knee_outer_left_inner_frame_block":
            scenarios = [row for row in materials["ripped_section_scenarios"]
                         if member_id in row["member_ids"]]
            require(len(scenarios) == 1, "one explicit ripped-block scenario for transverse seat")
            scenario = scenarios[0]
            require(scenario["study_only_CF"] == 1.0 and
                    scenario["Table4A_nominal_class_and_CF"] is None,
                    "ripped-block transverse seat keeps CFstudy=1.0 study-only label")
            fc_perp = float(scenario["base_row_properties_psi"]["Fc_perpendicular"])
            require(fc_perp == float(base["Fc_perpendicular"]),
                    "ripped-block Fc-perpendicular value matches declared base No.2 row")
            return fc_perp, "Fc_perpendicular", scenario["scenario_id"]
        return float(base["Fc_perpendicular"]), "Fc_perpendicular", "conditional DF-L No.2 Table 4A base-row reference"
    require(direction == "parallel_to_proposed_grain", f"supported bearing direction for {member_id}")
    require(member_id == "knee_outer_left_inner_frame_block",
            "only BG045 ripped block has a parallel washer-normal seat in this source scope")
    scenarios = [row for row in materials["ripped_section_scenarios"]
                 if member_id in row["member_ids"]]
    require(len(scenarios) == 1, "one explicit ripped-block scenario")
    scenario = scenarios[0]
    require(scenario["study_only_CF"] == 1.0 and
            scenario["Table4A_nominal_class_and_CF"] is None,
            "ripped-block CFstudy=1.0 remains a non-code study assumption")
    return float(scenario["base_row_properties_psi"]["Fc_parallel"]), "Fc_parallel", scenario["scenario_id"]


def build_screen() -> dict:
    pins = verify_source_pins()
    seat_register = read_json(INPUT_SEATS)
    materials = read_json(MATERIAL_INPUTS)
    fasteners = read_json(FASTENER_INPUTS)
    washer_geometry = read_json(WASHER_GEOMETRY)

    require(seat_register.get("schema") == "current_corner_three_case_axial_seat_register/v1" and
            seat_register.get("status") == "PASS_AUTHENTICATED_AXIAL_TIE_AND_OUTER_SEAT_DEMAND_COVERAGE_ONLY",
            "reused axial-seat register status/schema")
    require(seat_register["scope"].get("load_increment_states") == 21 and
            seat_register["scope"].get("physical_tie_state_rows") == 126 and
            seat_register["scope"].get("outer_washer_seat_state_rows") == 252,
            "reused exact 21/126/252 source coverage")
    require(set(case["case_id"] for case in seat_register["authenticated_cases"]) == EXPECTED_CASES,
            "accepted A12/A1/K12 source cases")
    require(seat_register.get("source_response_register", {}).get("usable_corner_demand_cases") == 3 and
            seat_register.get("scope", {}).get("joint_or_product_accepted") is False,
            "conditional source scope only")

    base = materials["conditional_DF_L_No2_base_row"]
    require(base["species_group_scenario"] == "Douglas Fir-Larch (not Douglas Fir-Larch (North))" and
            base["commercial_grade_scenario"] == "No. 2" and
            base["base_properties"]["Fc_perpendicular"] == 625 and
            base["base_properties"]["Fc_parallel"] == 1350,
            "conditional DF-L No.2 reference properties")
    require("normal load duration" in base["base_properties"]["conditions"] and
            "dry service" in base["base_properties"]["conditions"],
            "normal-duration/dry-service base-row conditions")
    factors = materials["adjustment_factor_inputs"]
    require("no CF applies" in factors["CF"] and "Fc_perpendicular" in factors["CF"],
            "Fc-perpendicular CF exclusion in material packet")

    washer = fasteners["dimension_inputs"]["washer"]
    od_min_in = float(washer["od_in"][0])
    id_max_in = float(washer["id_in"][1])
    od_min_mm = od_min_in * IN_TO_MM
    id_max_mm = id_max_in * IN_TO_MM
    min_uss_area_mm2 = math.pi / 4.0 * (od_min_mm**2 - id_max_mm**2)
    require(close(od_min_mm, 18.4658, 1e-9) and close(id_max_mm, 8.3058, 1e-9),
            "declared full-ring minimum OD/maximum ID conversion")
    bore_diameter_mm = 2.0 * float(washer_geometry["axes"][0]["outer_seats"][0]["modeled_finished_wood_bore_radius_mm"])
    require(id_max_mm > bore_diameter_mm,
            "catalog maximum washer ID clears the modeled 7.5-mm wood bore")
    cad_area_by_axis = {row["axis_id"]: float(row["modeled_outer_washer_annular_area_mm2"])
                        for row in washer_geometry["axes"]}
    require(set(cad_area_by_axis) == set().union(*EXPECTED_GROUP_AXES.values()),
            "washer CAD geometry covers the exact six corner axes")

    grain_by_member = build_grain_map(materials)
    member_rows = {row["member_id"]: row for row in materials["members"]}
    expected_axes = set().union(*EXPECTED_GROUP_AXES.values())
    states = []
    physical_seat_max: dict[tuple[str, str, str], dict] = {}
    ratios_by_direction_area: dict[tuple[str, str], dict] = {}
    counts = {"perpendicular_to_proposed_grain": 0, "parallel_to_proposed_grain": 0}
    tie_sign_counts = {"tension": 0, "compression": 0, "zero": 0}
    case_hashes = {case["case_id"]: case["demand_report_sha256"]
                   for case in seat_register["authenticated_cases"]}
    require(len(case_hashes) == 3, "three bound source report hashes")

    for state in seat_register["states"]:
        case_id = state["case_id"]
        require(case_id in EXPECTED_CASES and
                state["source_demand_report_sha256"] == case_hashes[case_id],
                f"{case_id} state retains accepted report hash")
        require(state.get("all_five_corner_bodies_raw_and_interval_balance_passed") is True,
                f"{case_id} state remains under its existing response gates")
        ties_out = []
        require(len(state["ties"]) == 6, f"six source ties in {case_id} increment {state['increment_ordinal']}")
        for tie in state["ties"]:
            axis_id = tie["axis_id"]
            group_id = tie["group_id"]
            require(group_id in EXPECTED_GROUP_AXES and axis_id in EXPECTED_GROUP_AXES[group_id],
                    f"{axis_id} belongs to its exact source group")
            signed_t = float(tie["signed_tie_action_n"])
            if signed_t > SIGN_EPSILON_N:
                sign_state = "tension"
            elif signed_t < -SIGN_EPSILON_N:
                sign_state = "compression"
            else:
                sign_state = "zero"
            tie_sign_counts[sign_state] += 1
            tie_seats = []
            require(len(tie["seats"]) == 2, f"two physical seats on {axis_id}")
            require({row["seat_role"] for row in tie["seats"]} == {"head_washer_seat", "nut_washer_seat"},
                    f"head/nut seat roles on {axis_id}")
            require({row["physical_member"] for row in tie["seats"]} ==
                    {tie["first_receiver_member"], tie["second_receiver_member"]},
                    f"seat members match the physical tie receivers on {axis_id}")

            for seat in tie["seats"]:
                member_id = seat["physical_member"]
                require(member_id in grain_by_member and member_id in member_rows,
                        f"{member_id} appears in material/grain source packet")
                force = [float(x) for x in seat["source_force_on_member_xyz_n"]]
                force_norm = math.sqrt(sum(x*x for x in force))
                require(close(force_norm, abs(signed_t), 2e-7),
                        f"source seat vector magnitude matches tie on {axis_id}/{member_id}")
                require(close(float(seat["signed_tie_action_n"]), signed_t, 1e-9),
                        f"source seat scalar matches signed tie on {axis_id}/{member_id}")
                cad_area = float(seat["modeled_full_annulus_area_mm2"])
                require(close(cad_area, cad_area_by_axis[axis_id], 2e-7),
                        f"{axis_id} seat CAD area matches frozen washer geometry")
                source_pressure = float(seat["source_signed_uniform_average_pressure_mpa"])
                pressure_cad = abs(signed_t) / cad_area
                require(close(abs(source_pressure), pressure_cad, 2e-12),
                        f"{axis_id} prior CAD average pressure equals |T|/A")

                direction, abs_cos = classify_bearing_direction(force, grain_by_member[member_id])
                reference_psi, reference_property, material_scenario = selected_material_reference(
                    materials, member_id, direction)
                reference_mpa = reference_psi * PSI_TO_MPA
                pressure_uss = abs(signed_t) / min_uss_area_mm2
                ratio_uss = pressure_uss / reference_mpa
                ratio_cad = pressure_cad / reference_mpa
                counts[direction] += 1

                member = member_rows[member_id]
                if member_id == "knee_outer_left_inner_frame_block":
                    material_basis = {
                        "conditional_material_scenario": material_scenario,
                        "source_grade_inheritance_permitted": False,
                        "post_rip_grade_observed": False,
                        "code_table4a_CF": None,
                        "CFstudy": 1.0,
                        "CFstudy_is_code_factor": False,
                    }
                else:
                    material_basis = {
                        "conditional_material_scenario": "conditional_DF-L_No.2_standard_section_base_row",
                        "conditional_nominal_stock_class": member.get("conditional_nominal_stock_class"),
                        "delivered_species_grade_observed": False,
                        "code_table4a_CF_applied_to_selected_property": False,
                        "CF_reason": "Fc⊥ is outside Table 4A CF scope; no standard-section parallel-grain washer seat occurs in this corner packet.",
                    }
                method_status = (
                    "stress_reference_comparison_only_no_local_parallel_washer_bearing_method_adopted"
                    if direction == "parallel_to_proposed_grain" else
                    "conditional_Fc_perpendicular_stress_reference_ratio_only"
                )
                seat_result = {
                    "axis_id": axis_id,
                    "group_id": group_id,
                    "physical_member": member_id,
                    "seat_role": seat["seat_role"],
                    "seat_point_global_xyz_mm": seat["seat_point_global_xyz_mm"],
                    "source_force_on_member_xyz_n": force,
                    "source_signed_tie_action_n": signed_t,
                    "source_tie_state": sign_state,
                    "source_report_path": state["source_demand_report_path"],
                    "source_report_sha256": state["source_demand_report_sha256"],
                    "source_increment_ordinal": state["increment_ordinal"],
                    "source_time": state["time"],
                    "load_factor": state["load_factor"],
                    "proposed_grain_global_xyz": grain_by_member[member_id],
                    "abs_cosine_of_seat_normal_and_proposed_grain": abs_cos,
                    "load_to_grain_relation": direction,
                    "conditional_material_basis": material_basis,
                    "compression_reference_property": reference_property,
                    "compression_reference_psi": reference_psi,
                    "compression_reference_mpa": reference_mpa,
                    "catalog_uss_full_sound_annulus_minimum": {
                        "area_mm2": min_uss_area_mm2,
                        "pressure_magnitude_mpa": pressure_uss,
                        "stress_to_reference_value_ratio": ratio_uss,
                    },
                    "frozen_cad_annulus": {
                        "area_mm2": cad_area,
                        "pressure_magnitude_mpa": pressure_cad,
                        "stress_to_reference_value_ratio": ratio_cad,
                    },
                    "bearing_area_increase_credited": False,
                    "method_status": method_status,
                    "local_contact_area_assumption": "full annular area, uniformly loaded, sound wood and complete support; a scenario only, not verified contact or washer load distribution",
                    "conditional_adjustment_case": "normal-duration, dry-service, unincised, normal-temperature baseline; CD=CM=Ct=Ci=1.0 assumed",
                }
                tie_seats.append(seat_result)

                for area_case, pressure, ratio in (
                    ("catalog_uss_full_sound_annulus_minimum", pressure_uss, ratio_uss),
                    ("frozen_cad_annulus", pressure_cad, ratio_cad),
                ):
                    key = (direction, area_case)
                    old = ratios_by_direction_area.get(key)
                    if old is None or ratio > old["stress_to_reference_value_ratio"]:
                        ratios_by_direction_area[key] = {
                            "load_to_grain_relation": direction,
                            "area_case": area_case,
                            "axis_id": axis_id,
                            "group_id": group_id,
                            "physical_member": member_id,
                            "seat_role": seat["seat_role"],
                            "case_id": case_id,
                            "load_factor": state["load_factor"],
                            "source_increment_ordinal": state["increment_ordinal"],
                            "pressure_magnitude_mpa": pressure,
                            "compression_reference_property": reference_property,
                            "compression_reference_psi": reference_psi,
                            "stress_to_reference_value_ratio": ratio,
                            "method_status": method_status,
                        }

                physical_key = (axis_id, member_id, seat["seat_role"])
                prior_peak = physical_seat_max.get(physical_key)
                if prior_peak is None or pressure_uss > prior_peak["maximum_catalog_uss_average_pressure_mpa"]:
                    physical_seat_max[physical_key] = {
                        "axis_id": axis_id,
                        "group_id": group_id,
                        "physical_member": member_id,
                        "seat_role": seat["seat_role"],
                        "load_to_grain_relation": direction,
                        "compression_reference_property": reference_property,
                        "compression_reference_psi": reference_psi,
                        "case_id": case_id,
                        "load_factor": state["load_factor"],
                        "source_increment_ordinal": state["increment_ordinal"],
                        "maximum_catalog_uss_average_pressure_mpa": pressure_uss,
                        "maximum_catalog_uss_stress_to_reference_value_ratio": ratio_uss,
                        "corresponding_frozen_cad_average_pressure_mpa": pressure_cad,
                        "corresponding_frozen_cad_stress_to_reference_value_ratio": ratio_cad,
                        "method_status": method_status,
                    }

            ties_out.append({
                "axis_id": axis_id,
                "group_id": group_id,
                "signed_tie_action_n": signed_t,
                "signed_tie_state": sign_state,
                "source_connection_name": tie["source_connection_name"],
                "first_receiver_member": tie["first_receiver_member"],
                "second_receiver_member": tie["second_receiver_member"],
                "seat_count": len(tie_seats),
                "seat_compression_screens": tie_seats,
            })
        states.append({
            "case_id": case_id,
            "source_demand_report_path": state["source_demand_report_path"],
            "source_demand_report_sha256": state["source_demand_report_sha256"],
            "increment_ordinal": state["increment_ordinal"],
            "time": state["time"],
            "load_factor": state["load_factor"],
            "response_balance_gate_preserved": True,
            "tie_count": len(ties_out),
            "ties": ties_out,
        })

    require(len(states) == 21, "21 reused case-increment states")
    require(sum(len(state["ties"]) for state in states) == 126, "126 repeated source tie states")
    require(sum(len(tie["seat_compression_screens"]) for state in states for tie in state["ties"]) == 252,
            "252 seat compression records")
    require(tie_sign_counts == {"tension": 126, "compression": 0, "zero": 0},
            "observed signed source tie states unchanged")
    require(counts == {"perpendicular_to_proposed_grain": 210,
                       "parallel_to_proposed_grain": 42},
            "ten transverse and two parallel physical seats per state")
    require(len(physical_seat_max) == 12, "12 physical seat/member identities")

    source_refs = [{"path": item["path"], "sha256": item["sha256"]} for item in pins["files"]]
    source_refs.append({"path": rel(SOURCE_PINS), "sha256": SOURCE_PINS_SHA256})
    source_refs.append({"path": rel(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())})
    max_pressure_uss = max(row["maximum_catalog_uss_average_pressure_mpa"]
                           for row in physical_seat_max.values())
    max_pressure_cad = max(row["corresponding_frozen_cad_average_pressure_mpa"]
                           for row in physical_seat_max.values())
    return {
        "schema": "current_corner_catalog_washer_wood_compression_screen/v1",
        "status": "PASS_REPLAYABLE_CONDITIONAL_WOOD_SEAT_STRESS_REFERENCE_SCREEN_ONLY",
        "scope": {
            "input_case_ids": ["a12-rear", "a1-rear", "k12-rear"],
            "case_increment_states": 21,
            "tie_state_rows": 126,
            "outer_seat_state_rows": 252,
            "physical_seat_member_identities": 12,
            "source_tie_sign_counts": tie_sign_counts,
            "seat_normal_grain_counts": counts,
            "native_solve_run": False,
            "geometry_or_frozen_source_changed": False,
            "wood_or_hardware_received_or_selected": False,
            "joint_or_connection_accepted": False,
        },
        "source_axial_register": {
            "path": pins["input_case_register"]["path"],
            "sha256": pins["input_case_register"]["sha256"],
            "source_pin_manifest_path": pins["input_case_register"]["source_pin_manifest_path"],
            "source_pin_manifest_sha256": pins["input_case_register"]["source_pin_manifest_sha256"],
            "source_case_hashes": case_hashes,
            "demand_scope": "reused 252 same-state seat records from the accepted A12-rear, A1-rear and K12-rear source reports; not a six-case envelope",
        },
        "declared_contact_area_scenarios": {
            "catalog_uss_full_sound_annulus_minimum": {
                "area_mm2": min_uss_area_mm2,
                "minimum_od_in": od_min_in,
                "maximum_id_in": id_max_in,
                "minimum_od_mm": od_min_mm,
                "maximum_id_mm": id_max_mm,
                "modeled_wood_bore_diameter_mm": bore_diameter_mm,
                "opening_clears_modeled_bore": True,
                "basis": "pi/4 * (minimum catalog USS OD^2 - maximum catalog USS ID^2); full, sound, continuously supported ring assumed",
                "selection_or_delivery_status": "catalog envelope only; no washer selected or delivered",
            },
            "frozen_cad_annulus": {
                "area_mm2_by_axis": cad_area_by_axis,
                "area_basis": "source-frozen washer CAD volume divided by modeled thickness, as retained by prior seat geometry screen",
                "interpretation": "frozen modeled CAD area comparison; not a verified product or actual contact area",
            },
        },
        "conditional_material_and_adjustment_scenario": {
            "scenario_id": "DF-L_No2_normal-duration_dry-service_unincised_normal-temperature; ripped-BG045-block-CFstudy-1.0-only",
            "material_source_path": rel(MATERIAL_INPUTS),
            "material_source_sha256": sha256(MATERIAL_INPUTS),
            "wood_base_row": {
                "species_group": base["species_group_scenario"],
                "grade_scenario": base["commercial_grade_scenario"],
                "Fc_perpendicular_psi": float(base["base_properties"]["Fc_perpendicular"]),
                "Fc_perpendicular_mpa": float(base["base_properties"]["Fc_perpendicular"]) * PSI_TO_MPA,
                "Fc_parallel_psi": float(base["base_properties"]["Fc_parallel"]),
                "Fc_parallel_mpa": float(base["base_properties"]["Fc_parallel"]) * PSI_TO_MPA,
                "conditions_from_Table4A": base["base_properties"]["conditions"],
            },
            "adjustment_selection": {
                "CD": {"value": 1.0, "reason": "normal load-duration base-row scenario; no duration increase credited"},
                "CM": {"value": 1.0, "reason": "dry-service baseline; wet-service not assigned or observed"},
                "Ct": {"value": 1.0, "reason": "normal-temperature condition is an explicit scenario assumption, not an observation"},
                "Ci": {"value": 1.0, "reason": "unincised condition is an explicit scenario assumption, not an observation"},
                "CF_on_Fc_perpendicular": {"value": None, "reason": "Table 4A CF does not apply to Fc_perpendicular"},
                "CF_on_BG045_ripped_block_Fc_parallel": {"value": 1.0, "reason": "explicit CFstudy=1.0 arithmetic scenario only; not a Table 4A code CF or post-rip grade assignment"},
                "Cb_bearing_area_increase": {"value": 1.0, "reason": "no increase credited; exact support patch and member-end eligibility are unverified"},
                "CP_compression_stability": {"value": None, "reason": "not part of this washer-seat average-stress screen; no member stability check is claimed"},
                "other_adjustments_or_increases": "none applied",
            },
            "interpretation": "Fc_perpendicular ratios are conditional base-row stress/reference comparisons. The two BG045 block seats use Fc_parallel=1350 psi only as the packet's hypothetical final-section DF-L No.2, CFstudy=1.0 comparator; no local parallel washer-bearing code method is adopted, so those values are stress/reference comparisons only, not code passes.",
        },
        "maximum_reference_ratios_by_direction_and_area": [
            ratios_by_direction_area[key]
            for key in sorted(ratios_by_direction_area)
        ],
        "maximum_pressure_magnitude_mpa": {
            "catalog_uss_full_sound_annulus_minimum": max_pressure_uss,
            "frozen_cad_annulus": max_pressure_cad,
        },
        "maximum_by_physical_seat_across_reused_cases": [
            physical_seat_max[key] for key in sorted(physical_seat_max)
        ],
        "explicit_open_inputs": [
            "No selected/delivered washer, actual washer material strength, flexural stiffness, bending/spreading capacity or head/nut contact footprint is established.",
            "The catalog minimum USS ring and frozen CAD annulus are alternative full-area scenarios; the finished wood support polygon, edge/end distance, cuts, gaps, flatness, and actual bearing distribution are unknown. No local pressure field, pull-through resistance or splitting resistance is calculated.",
            "DF-L No.2 properties and proposed grain axes are conditional inputs only. Actual species, grade, moisture/service condition, treatment/incising, normal temperature, physical grain and growth-ring orientation remain unobserved; the inner-frame block's source 4x6 grade does not transfer after ripping.",
            "The BG045 block's 1350-psi Fc comparator uses the specified hypothetical ripped-final-section CFstudy=1.0 scenario, but no applicable local washer-on-end-grain parallel compression design method is adopted. It is not a pass/capacity check.",
            "No Cb or other local bearing increase is credited; confirming its bearing geometry/end-location conditions and completing a physical bearing check remain open.",
        ],
        "limits": [
            "Every pressure is |source signed tie action| divided by a declared full annular area and assumes uniform stress over sound, fully supported wood; it is a mean stress, not a pressure distribution solution.",
            "The ten perpendicular-to-grain seats are compared only with the conditional Fc_perpendicular reference. The two parallel BG045 inner-block seats are stress/reference comparisons only; no local parallel washer-bearing method or code pass is claimed.",
            "No material/hardware, washer, complete connection, full-corner, six-case, floor, or climber acceptance is made. Missing evidence is not inferred physical failure.",
        ],
        "source_pins": source_refs,
        "states": states,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="replay and compare against the saved JSON")
    parser.add_argument("--write", action="store_true", help="write the rebuilt JSON (default behavior)")
    args = parser.parse_args()
    result = build_screen()
    if args.verify:
        require(OUTPUT.is_file(), "saved seat-compression-screen.json exists")
        require(read_json(OUTPUT) == result, "saved seat-compression-screen.json matches source replay")
        print("Verified 21 states, 126 ties, 252 seats; 210 transverse and 42 parallel seat states")
    else:
        OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print("Wrote source-bound conditional washer-seat wood compression screen")


if __name__ == "__main__":
    main()
