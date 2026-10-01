#!/usr/bin/env python3
"""Source-pinned A1-rear axial tie and washer-seat component screen."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"

INPUTS = {
    "a1_corner_demand_report": (
        PACKET / "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json",
        "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce",
    ),
    "a1_projection_freeze": (
        PACKET / "current-corner-a1-rear-case-bound-export-attempt01/projection-freeze.json",
        "34e019237ac44cd5c26b4fc3b982c503b198890bea45e170fe5a11f53f44c97c",
    ),
    "a1_selected_model": (
        PACKET / "current-springa-selected-floor-a1-rear-attempt02/model.json",
        "72d043e1a70702d8d464c21a039e897036e17c95e368ec776063584dac74f5fd",
    ),
    "a1_selected_deck": (
        PACKET / "current-springa-selected-floor-a1-rear-attempt02/model.inp",
        "f92db3851a6edc50bfba4f4eec0331d4f0e4bd4d7af4d2bf80780bdda52d13ab",
    ),
    "a1_native_dat": (
        PACKET / "current-springa-selected-floor-a1-rear-attempt02/model.dat",
        "b5b9997e299779f76697a84ff739f89d7757c97394144839f541944e98e929e2",
    ),
    "a1_case_context": (
        PACKET / "current-springa-selected-floor-a1-rear-attempt02/case-context.json",
        "8383c31145aaa1b85ba82f43ce2f12f3c12ff58e07bc191e5e2c7315f92922f6",
    ),
    "a1_response": (
        PACKET / "current-springa-selected-floor-a1-rear-attempt02/response-zero-u-token.json",
        "257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c",
    ),
    "a1_parent_all_body_audit": (
        PACKET / "current-springa-selected-floor-a1-rear-attempt02/parent-all-body-response-audit.json",
        "247845921630a092c3f7a79d9ac11c92d732f021d2cb1dc5214e54b1a344deca",
    ),
    "a1_parent_case_context_check": (
        PACKET / "current-springa-selected-floor-a1-rear-attempt02/parent-case-context-check.json",
        "ee8b628b9adbab22c114149a1e6e33ce5f5d500eaf03fc7858855aee7dcd7049",
    ),
    "a1_parent_terminal_assessment": (
        PACKET / "current-springa-selected-floor-a1-rear-attempt02/parent-terminal-assessment.json",
        "95e06dcfd7433a5273b12892b990c519ba4177801594f94f54e04726f6e79bc0",
    ),
    "a1_native_freeze": (
        PACKET / "current-springa-selected-floor-a1-rear-attempt02/freeze.json",
        "4a49b236f52d2cb863bd753b4d44d5b84bcd25b1269396b377717f8ef65f76d9",
    ),
    "a12_reference_model": (
        PACKET / "current-springa-selected-floor-a12-rear-attempt03/model.json",
        "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
    ),
    "a12_corner_demand_report": (
        PACKET / "current-corner-native-demand-export-attempt03/corner-demand-report.json",
        "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    ),
    "a12_axial_reference_screen": (
        PACKET / "current-corner-axial-tie-seat-screen-attempt01/screen.json",
        "cae5c67d1166205aaa442c8ae889c95245162b7d1569cf264b13bc260d712ac4",
    ),
    "washer_geometry_and_candidate_register": (
        PACKET / "current-corner-washer-seat-screen-attempt01/seat-screen.json",
        "67dda5964a9c2a864cdb5ee0e898bae3c9e6bea212e2eeb71d5b33f765481ef0",
    ),
    "existing_conditional_resistance_screen": (
        PACKET / "current-corner-a12-conditional-resistance-screen-attempt01/screen.json",
        "ee247af7e2271e63dcf1f8d8b86ef5eeca203f3dec3e37c55f2f6a8addb1e5cb",
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

AXES = {
    "knee_outer_left_post_1": "BG001",
    "knee_outer_left_post_2": "BG001",
    "knee_outer_left_side_1": "BG003",
    "knee_outer_left_side_2": "BG003",
    "knee_outer_left_inner_header_1": "BG045",
    "knee_outer_left_inner_header_2": "BG045",
}

STATIC_MODEL_FIELDS = (
    "candidate",
    "geometry_revision_id",
    "nodes",
    "fixed_nodes",
    "body_geometry",
    "geometry_audit",
    "source_geometry_hashes",
    "physical_body_nodes",
    "physical_body_elements",
    "elements",
    "material_binding",
    "connection_ownership",
    "source_carrier_inventory_rows",
    "raw_source_carrier_law_inventory_rows",
    "unilateral_springa_bindings",
    "springs",
    "source_spring_counts",
    "connection_scenario",
)

PSI_TO_MPA = 0.006894757293168361
LBF_TO_N = 4.4482216152605
IN_TO_MM = 25.4


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"source or method gate failed: {message}")


def load_bearing_helper():
    path = INPUTS["wood_bearing_helper"][0]
    spec = importlib.util.spec_from_file_location("pinned_bolted_timber_checks_a1", path)
    if spec is None or spec.loader is None:
        raise SystemExit("could not load pinned wood-bearing helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.dfl_axial_wood_bearing_reference_lbf


def verify_input_pins() -> dict:
    pins = {}
    for name, (path, expected) in INPUTS.items():
        actual = sha256(path)
        require(actual == expected, f"{name} hash changed ({actual})")
        pins[name] = {"path": path.relative_to(ROOT).as_posix(), "sha256": actual}
    producer = Path(__file__).resolve()
    pins["producer"] = {
        "path": producer.relative_to(ROOT).as_posix(),
        "sha256": sha256(producer),
    }
    return pins


def final_factor_row(report: dict) -> dict:
    rows = [row for row in report["increments"] if row.get("load_factor") == 1.0]
    require(len(rows) == 1, "expected one load-factor-1.0 increment")
    return rows[0]


def selected_seats(increment: dict) -> dict[str, list[dict]]:
    result = {axis: [] for axis in AXES}
    for row in increment["outer_washer_seats"]:
        if row.get("axis_id") in result:
            result[row["axis_id"]].append(row)
    require(all(len(rows) == 2 for rows in result.values()), "one or more axes do not have two seats")
    require(sum(map(len, result.values())) == 12, "expected exactly twelve selected seats")
    return result


def verify_response_and_context(report: dict, model: dict, context: dict,
                                audit: dict, terminal: dict) -> dict:
    require(report.get("schema") == "current_corner_case_bound_demand_report/v1", "A1 report schema")
    require(report.get("status") == "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY", "A1 report status")
    require(report.get("case_id") == "a1-rear" and model.get("case_id") == "a1-rear", "A1 case identity")
    require(report.get("actual_case_demand_usable_for_conditional_joint_checks") is True,
            "A1 report does not mark its exact-case demands usable")
    require(report.get("response_audit_final_load_factor") == 1.0 and
            report.get("response_audit_increment_count") == 7, "A1 response coverage")
    require(report.get("qualification_boundary", {}).get("complete_joint_accepted") is False,
            "A1 corner report acceptance boundary")
    require(report["qualification_boundary"].get("qualified_for_design") is False,
            "A1 design qualification boundary")

    auth = report["authenticated_source_case"]
    require(auth.get("selected_input_model_sha256") == INPUTS["a1_selected_model"][1],
            "A1 report model binding")
    require(auth.get("selected_input_deck_sha256") == INPUTS["a1_selected_deck"][1],
            "A1 report deck binding")
    require(auth.get("native_dat_sha256") == INPUTS["a1_native_dat"][1], "A1 report DAT binding")
    require(auth.get("external_case_context_sha256") == INPUTS["a1_case_context"][1],
            "A1 external case-context binding")
    require(context.get("case_id") == "a1-rear" and context.get("candidate") == report["candidate"],
            "A1 case context identity")
    require(context.get("geometry_revision_id") == report["geometry_revision_id"],
            "A1 context geometry revision")
    require(context.get("selected_input_model_json_sha256") == INPUTS["a1_selected_model"][1],
            "A1 context model binding")
    require(context.get("selected_input_deck_sha256") == INPUTS["a1_selected_deck"][1],
            "A1 context deck binding")
    require(context.get("screen_positive_forces_or_active_states_reused_as_response") is False,
            "A1 diagnostic-screen non-reuse condition")
    require(auth.get("diagnostic_screen_context_only", {}).get("screen_forces_or_states_reused") is False,
            "A1 report diagnostic-screen non-reuse condition")

    require(audit.get("status") == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS", "A1 parent all-body audit status")
    require(audit.get("source_model_sha256") == INPUTS["a1_selected_model"][1],
            "A1 parent audit model binding")
    require(audit.get("source_response_sha256") == auth["response_audit_sha256"],
            "A1 parent audit response binding")
    require(len(audit.get("increments", [])) == 7, "A1 parent audit increment count")
    for ix, inc in enumerate(audit["increments"], start=1):
        require(inc.get("body_count") == 50 and len(inc.get("body_equilibrium", {})) == 50,
                f"A1 parent audit body count at increment {ix}")
        require(inc.get("passed") is True, f"A1 parent audit overall gate at increment {ix}")
        require(inc.get("global_equilibrium", {}).get("printed_resultants_passed") is True and
                inc.get("global_equilibrium", {}).get("interval_resultants_passed") is True,
                f"A1 parent global balance at increment {ix}")
        require(all(body.get("printed_resultants_passed") is True and
                    body.get("interval_resultants_passed") is True
                    for body in inc["body_equilibrium"].values()),
                f"A1 parent 50-body balance at increment {ix}")

    root_gates = report.get("response_audit_root_gates", {})
    require(root_gates and all(value is True for value in root_gates.values()),
            "A1 response root gates")
    for ix, row in enumerate(report["increments"], start=1):
        gates = row.get("response_audit_gates", {})
        require(gates and all(value is True for value in gates.values()),
                f"A1 response gates at increment {ix}")
        require(row.get("all_five_corner_bodies_raw_and_interval_balance_passed") is True,
                f"A1 five-body corner balance at increment {ix}")
        global_row = row.get("audited_global_equilibrium", {})
        require(global_row.get("printed_resultants_passed") is True and
                global_row.get("interval_resultants_passed") is True,
                f"A1 corner-export global balance at increment {ix}")

    require(terminal.get("status") == "PASS_CONDITIONAL_NUMERICAL_RESPONSE" and
            terminal.get("case_id") == "a1-rear" and terminal.get("native_returncode") == 0,
            "A1 parent terminal assessment")
    require(terminal.get("conditional_case_forces_usable") is True and
            terminal.get("joint_accepted") is False and
            terminal.get("mechanical_acceptance") is False,
            "A1 parent terminal boundary")
    contract_check = read_json(INPUTS["a1_parent_case_context_check"][0])
    require(contract_check.get("status") == "PASS_FROZEN_CASE_BOUND_INPUT_CONTRACT_ONLY" and
            contract_check.get("native_response_consumed") is False,
            "A1 parent input-contract check")
    return {
        "case_id": "a1-rear",
        "corner_report_status": report["status"],
        "response_sha256": auth["response_audit_sha256"],
        "response_auditor_sha256": auth["response_auditor_sha256"],
        "source_model_sha256": auth["selected_input_model_sha256"],
        "source_deck_sha256": auth["selected_input_deck_sha256"],
        "native_dat_sha256": auth["native_dat_sha256"],
        "case_context_sha256": auth["external_case_context_sha256"],
        "parent_all_body_audit_status": audit["status"],
        "parent_all_body_audit_sha256": INPUTS["a1_parent_all_body_audit"][1],
        "parent_body_count_per_increment": 50,
        "parent_audit_increment_count": len(audit["increments"]),
        "parent_global_and_all_body_raw_and_interval_balances_passed_each_increment": True,
        "parent_terminal_assessment_status": terminal["status"],
        "conditional_case_forces_usable": True,
        "joint_accepted": False,
        "corner_response_increment_count": len(report["increments"]),
        "corner_response_all_root_and_increment_gates_passed": True,
        "selected_floor_scope": report["selected_floor_response_scope"],
        "diagnostic_screen_forces_or_states_reused": False,
        "case_bound_input_contract_check": {
            "status": contract_check["status"],
            "native_response_consumed": contract_check["native_response_consumed"],
            "inventory": contract_check["inventory"],
        },
    }


def build_report() -> dict:
    pins = verify_input_pins()
    a1_report = read_json(INPUTS["a1_corner_demand_report"][0])
    a1_model = read_json(INPUTS["a1_selected_model"][0])
    a1_context = read_json(INPUTS["a1_case_context"][0])
    a1_audit = read_json(INPUTS["a1_parent_all_body_audit"][0])
    a1_terminal = read_json(INPUTS["a1_parent_terminal_assessment"][0])
    a12_report = read_json(INPUTS["a12_corner_demand_report"][0])
    a12_model = read_json(INPUTS["a12_reference_model"][0])
    a12_screen = read_json(INPUTS["a12_axial_reference_screen"][0])
    seat_geometry = read_json(INPUTS["washer_geometry_and_candidate_register"][0])
    scenario_screen = read_json(INPUTS["a12_axial_reference_screen"][0])

    case_auth = verify_response_and_context(a1_report, a1_model, a1_context, a1_audit, a1_terminal)
    require(a12_report.get("case_id") == "a12-rear" and
            a12_report.get("status") == "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY",
            "a12 comparator report identity/status")
    require(a12_screen.get("schema") == "current_corner_axial_tie_and_washer_seat_component_screen/v1" and
            a12_screen.get("scope", {}).get("case_id") == "a12-rear",
            "a12 conditional scenario reference screen identity")

    # Confirm structural/material/connection equivalence while allowing the
    # explicitly case-bound load and floor branch to differ.
    compatibility = {}
    for key in STATIC_MODEL_FIELDS:
        require(key in a1_model and key in a12_model, f"missing static compatibility field {key}")
        require(a1_model[key] == a12_model[key], f"A1/A12 static input differs in {key}")
        compatibility[key] = canonical_sha(a1_model[key])
    require(a1_model.get("case_id") == "a1-rear" and a12_model.get("case_id") == "a12-rear",
            "model case IDs")
    require(a1_model.get("floor_selected_bearing_cells") != a12_model.get("floor_selected_bearing_cells") and
            a1_model.get("floor_inactive_cells") != a12_model.get("floor_inactive_cells"),
            "case-bound selected-floor masks unexpectedly match")

    a1_final = final_factor_row(a1_report)
    a12_final = final_factor_row(a12_report)
    a1_seats_by_axis = selected_seats(a1_final)
    a12_seats_by_axis = selected_seats(a12_final)
    a12_screen_axes = {row["axis_id"]: row for row in a12_screen["axes"]}
    require(set(AXES) == set(a12_screen_axes), "a12 tie comparator axes")
    geometry_by_axis = {row["axis_id"]: row for row in seat_geometry["axes"]}

    # Reuse the exact Type A dimensional / bolt material values from the
    # previously verified A12 calculation rather than making new assumptions.
    scenario = scenario_screen["conditional_material_and_hardware_scenarios"]
    washer_dims = scenario["washer"]["dimensional_envelope_used_for_minimum_annulus"]
    od_min = float(washer_dims["minimum_outer_diameter_in"])
    od_max = float(washer_dims["maximum_outer_diameter_in"])
    id_min = float(washer_dims["minimum_inner_diameter_in"])
    id_max = float(washer_dims["maximum_inner_diameter_in"])
    thickness_range = washer_dims["thickness_range_in"]
    bolt_scenario = scenario["bolt"]
    fy_psi = float(bolt_scenario["minimum_yield_psi"])
    at_in2 = float(bolt_scenario["tensile_stress_area_in2"])
    at_mm2 = at_in2 * IN_TO_MM**2
    bolt_first_yield_n = fy_psi * PSI_TO_MPA * at_mm2
    fc_psi = float(scenario_screen["calculation_notes"]["wood_reference_helper_inputs"]["Fc_perp_psi"])
    bearing_helper = load_bearing_helper()

    a1_final_row = final_factor_row(a1_report)
    a12_final_row = final_factor_row(a12_report)
    axes_out = []
    seats_out = []
    static_seat_match_count = 0

    for axis_id, group in AXES.items():
        static_axis = geometry_by_axis[axis_id]
        candidate_washer_leads = static_axis.get("conditional_washer_lead_ids_in_axis_register", [])
        has_25nwus_lead = "kl-25nwus" in candidate_washer_leads
        require(static_axis.get("washer_product_status") == "not_selected_or_delivered",
                f"A1 hardware disposition changed on {axis_id}")
        a1_rows = sorted(a1_seats_by_axis[axis_id], key=lambda row: row["seat_role"])
        a12_rows = sorted(a12_seats_by_axis[axis_id], key=lambda row: row["seat_role"])
        require([row["seat_role"] for row in a1_rows] == [row["seat_role"] for row in a12_rows],
                f"A1/A12 seat roles differ on {axis_id}")
        a1_ties = [float(row["signed_outer_seat_tie_action_n"]) for row in a1_rows]
        a12_ties = [float(row["signed_outer_seat_tie_action_n"]) for row in a12_rows]
        require(min(a1_ties) > 0 and abs(a1_ties[0] - a1_ties[1]) <= 1e-9,
                f"A1 outer tie pair inconsistent on {axis_id}")
        require(min(a12_ties) > 0 and abs(a12_ties[0] - a12_ties[1]) <= 1e-9,
                f"A12 comparator tie pair inconsistent on {axis_id}")
        force_a1 = [row["seat_force_on_member_xyz_n"] for row in a1_rows]
        force_a12 = [row["seat_force_on_member_xyz_n"] for row in a12_rows]
        for j in range(3):
            require(abs(float(force_a1[0][j]) + float(force_a1[1][j])) <= 1e-6,
                    f"A1 seat actions not equal/opposite on {axis_id}")
            require(abs(float(force_a12[0][j]) + float(force_a12[1][j])) <= 1e-6,
                    f"A12 comparator seat actions not equal/opposite on {axis_id}")
        a1_tension = a1_ties[0]
        a12_tension = a12_ties[0]
        require(abs(a12_tension - float(a12_screen_axes[axis_id]["positive_outer_seat_tie_tension_demand_n"])) <= 1e-9,
                f"A12 comparator screen does not match source export on {axis_id}")
        area_a1 = [float(row["modeled_outer_washer_annular_area_mm2"]) for row in a1_rows]
        area_a12 = [float(row["modeled_outer_washer_annular_area_mm2"]) for row in a12_rows]
        require(max(area_a1) - min(area_a1) <= 1e-6 and max(area_a12) - min(area_a12) <= 1e-6,
                f"paired seat areas differ on {axis_id}")

        axis_geometry_seats = static_axis["outer_seats"]
        axis_seat_results = []
        for row in a1_rows:
            geometry_seat = next(
                seat for seat in axis_geometry_seats
                if seat["outer_receiver_member_id"] == row["physical_member"] and
                   seat["seat_role"] == row["seat_role"]
            )
            prior_row = next(
                seat for seat in a12_rows
                if seat["physical_member"] == row["physical_member"] and
                   seat["seat_role"] == row["seat_role"]
            )
            require(row["seat_point_global_xyz_mm"] == prior_row["seat_point_global_xyz_mm"] == geometry_seat["seat_point_xyz_mm"],
                    f"seat point changed across A1/A12/static geometry at {axis_id}/{row['seat_role']}")
            area = float(row["modeled_outer_washer_annular_area_mm2"])
            require(abs(area - float(prior_row["modeled_outer_washer_annular_area_mm2"])) <= 1e-8,
                    f"seat area changed across A1/A12 at {axis_id}/{row['seat_role']}")
            require(abs(area - float(static_axis["modeled_outer_washer_annular_area_mm2"])) <= 1e-8,
                    f"seat area changed versus geometry screen at {axis_id}/{row['seat_role']}")
            static_seat_match_count += 1

            # Same numerical seat scenarios as the source-pinned A12 screen.
            modeled_pressure = a1_tension / area
            require(abs(modeled_pressure - float(row["conditional_full_annulus_uniform_average_pressure_mpa"])) <= 1e-9,
                    f"A1 report CAD pressure does not match recomputation at {axis_id}/{row['seat_role']}")
            candidate_annulus_area_mm2 = None
            candidate_pressure = None
            if has_25nwus_lead:
                bore_diameter_in = 2.0 * float(geometry_seat["modeled_finished_wood_bore_radius_mm"]) / IN_TO_MM
                candidate_annulus_area_mm2 = math.pi / 4.0 * (
                    od_min**2 - max(id_max, bore_diameter_in)**2
                ) * IN_TO_MM**2
                candidate_pressure = a1_tension / candidate_annulus_area_mm2
            kind = geometry_seat["member_kind"]
            grain_relation = geometry_seat["load_grain_relation"]
            fc_eligible = (
                row["physical_member"] in {"base_post_outer_left", "base_header"}
                and kind == "timber"
                and grain_relation == "perpendicular_to_proposed_grain"
                and has_25nwus_lead
            )
            if fc_eligible:
                fc_ref_lbf = bearing_helper(od_min, bore_diameter_in, id_max)
                fc_ref_n = fc_ref_lbf * LBF_TO_N
                fc_ratio = a1_tension / fc_ref_n
                fc_status = "conditional_unadjusted_DF_L_No2_Fc_perp_reference"
                fc_area = candidate_annulus_area_mm2
                fc_pressure = candidate_pressure
            else:
                fc_ref_n = None
                fc_ratio = None
                fc_area = None
                fc_pressure = None
                if grain_relation == "parallel_to_proposed_grain":
                    fc_status = "Fc_perp_inapplicable_parallel_to_proposed_grain"
                elif kind == "candidate_block":
                    fc_status = "not_assigned_candidate_block_has_no_strength_grade"
                elif not has_25nwus_lead:
                    fc_status = "no_25NWUS_candidate_lead_on_axis"
                else:
                    fc_status = "no_applicable_Fc_perp_reference"

            block_what_if = None
            if kind == "candidate_block":
                if grain_relation == "perpendicular_to_proposed_grain":
                    if has_25nwus_lead:
                        what_if_area = candidate_annulus_area_mm2
                        what_if_ref_n = bearing_helper(od_min, bore_diameter_in, id_max) * LBF_TO_N
                        what_if_basis = "same 25NWUS minimum-annulus scenario as A12; block grade not assigned"
                    else:
                        what_if_area = area
                        what_if_ref_n = fc_psi * PSI_TO_MPA * what_if_area
                        what_if_basis = "CAD annular plan area with full support; washer opening/effective wood area not otherwise dimensions-bound"
                    block_what_if = {
                        "status": "hypothetical_DF_L_No2_only_not_assigned_to_candidate_block",
                        "assumed_material": "sound DF-L No. 2 with Fc_perp=625 psi",
                        "area_mm2": what_if_area,
                        "area_basis": what_if_basis,
                        "unadjusted_reference_n": what_if_ref_n,
                        "demand_over_reference_component_ratio": a1_tension / what_if_ref_n,
                        "uniform_average_pressure_mpa": a1_tension / what_if_area,
                    }
                else:
                    block_what_if = {
                        "status": "Fc_perp_not_applicable_parallel_to_proposed_grain",
                        "assumed_material": None,
                    }

            seat_result = {
                "group_id": group,
                "axis_id": axis_id,
                "physical_member": row["physical_member"],
                "seat_role": row["seat_role"],
                "seat_point_global_xyz_mm": row["seat_point_global_xyz_mm"],
                "seat_force_on_member_xyz_n": row["seat_force_on_member_xyz_n"],
                "positive_bolt_tension_tie_demand_n": a1_tension,
                "modeled_cad_annular_plan_area_mm2": area,
                "modeled_cad_full_annulus_uniform_average_pressure_mpa": modeled_pressure,
                "wood_receiver_kind": kind,
                "load_grain_relation": grain_relation,
                "conditional_washer_lead_ids": candidate_washer_leads,
                "conditional_25nwus_min_annulus": (
                    {
                        "status": "candidate_dimensions_only_not_selected_or_delivered",
                        "minimum_od_in": od_min,
                        "maximum_id_in": id_max,
                        "wood_bore_diameter_in": bore_diameter_in,
                        "area_mm2": candidate_annulus_area_mm2,
                        "uniform_average_pressure_mpa": candidate_pressure,
                        "thickness_range_in": thickness_range,
                    }
                    if has_25nwus_lead else None
                ),
                "conditional_base_timber_fc_perp_component": {
                    "status": fc_status,
                    "full_annulus_area_mm2": fc_area,
                    "reference_n": fc_ref_n,
                    "demand_over_reference_component_ratio": fc_ratio,
                    "uniform_average_pressure_mpa": fc_pressure,
                },
                "separate_candidate_block_DF_L_No2_what_if": block_what_if,
            }
            axis_seat_results.append(seat_result)
            seats_out.append(seat_result)

        axes_out.append({
            "group_id": group,
            "axis_id": axis_id,
            "receiver_members_head_to_nut": [row["physical_member"] for row in a1_rows],
            "a1_rear_positive_tie_tension_demand_n": a1_tension,
            "a12_rear_comparison_only_tie_tension_n": a12_tension,
            "difference_a1_minus_a12_n": a1_tension - a12_tension,
            "ratio_a1_to_a12": a1_tension / a12_tension,
            "a1_rear_tie_exceeds_a12_rear_on_this_axis": a1_tension > a12_tension,
            "outer_seat_count": 2,
            "conditional_bolt_grade5_FyAt_component": {
                "status": "conditional_material_first_yield_reference_only",
                "scenario_id": bolt_scenario["scenario_id"],
                "minimum_yield_psi": fy_psi,
                "tensile_stress_area_in2": at_in2,
                "tensile_stress_area_mm2": at_mm2,
                "unadjusted_tensile_first_yield_reference_n": bolt_first_yield_n,
                "A1_tension_over_reference_component_ratio": a1_tension / bolt_first_yield_n,
                "A12_comparison_only_ratio": a12_tension / bolt_first_yield_n,
                "product_conformance": False,
                "combined_axial_shear_interaction": "not calculated; no common controlling section or applicable interaction rule is provided",
            },
            "seats": axis_seat_results,
        })

    require(static_seat_match_count == 12, "all 12 static seat geometry rows must match")
    group_comparisons = []
    for group in ("BG001", "BG003", "BG045"):
        a1_max = max(row["a1_rear_positive_tie_tension_demand_n"] for row in axes_out if row["group_id"] == group)
        a12_max = max(row["a12_rear_comparison_only_tie_tension_n"] for row in axes_out if row["group_id"] == group)
        group_comparisons.append({
            "group_id": group,
            "a1_rear_max_axis_tie_n": a1_max,
            "a12_rear_max_axis_tie_n_comparison_only": a12_max,
            "a1_group_max_is_lower": a1_max < a12_max,
            "limits": "maximum across the two axis ties only; not a group capacity or demand envelope",
        })

    return {
        "schema": "current_corner_a1_rear_axial_tie_and_washer_component_screen/v1",
        "status": "CONDITIONAL_A1_COMPONENT_SCREEN_ONLY",
        "scope": {
            "candidate": a1_report["candidate"],
            "geometry_revision_id": a1_report["geometry_revision_id"],
            "case_id": "a1-rear",
            "load_factor": 1.0,
            "groups": ["BG001", "BG003", "BG045"],
            "axis_count": len(axes_out),
            "seat_count": len(seats_out),
            "native_solve_launched_by_this_screen": False,
            "geometry_or_model_changed": False,
            "new_stock_or_hardware_assignment": False,
            "retained_original_leg_runner_arrangements_reopened": False,
            "joint_acceptance": False,
        },
        "source_pins": pins,
        "a1_case_authentication": case_auth,
        "cross_case_compatibility": {
            "reference_case_id": "a12-rear",
            "compared_model_fields_equal": list(STATIC_MODEL_FIELDS),
            "equal_field_canonical_sha256": compatibility,
            "material_binding_equal": True,
            "body_geometry_nodes_elements_and_connection_laws_equal": True,
            "all_12_outer_seat_member_role_point_and_CAD_area_rows_match_A12_and_geometry_source": True,
            "static_seat_rows_checked": static_seat_match_count,
            "same_conditional_material_hardware_and_resistance_scenario": True,
            "case_bound_differences_not_transferred": {
                "loads_and_body_wrenches_differ_by_case": True,
                "A1_selected_floor_cell_count": len(a1_model["floor_selected_bearing_cells"]),
                "A1_inactive_floor_cell_count": len(a1_model["floor_inactive_cells"]),
                "A12_selected_floor_cell_count": len(a12_model["floor_selected_bearing_cells"]),
                "A12_inactive_floor_cell_count": len(a12_model["floor_inactive_cells"]),
                "A1_floor_mask_is_case_bound_and_not_reused_for_A12": True,
                "A12 forces used only as per-axis comparison values; no A12 forces or states seed A1 results": True,
            },
        },
        "conditional_scenarios": {
            "washer": scenario["washer"],
            "base_wood": {
                "Fc_perp_psi": fc_psi,
                "method": "mini_moonboard.bolted_timber_checks.dfl_axial_wood_bearing_reference_lbf",
                "applicability": "DF-L No. 2 base-post/base-header seats only when transverse to grain, sound and fully supported; still conditional and unreceived",
            },
            "candidate_block_material_binding": a1_model["material_binding"]["material_categories"]["candidate_block"],
            "candidate_block_strength_assignment": "none; any DF-L No. 2 Fc_perp values are isolated what-if arithmetic, not a model material assignment",
            "bolt": scenario["bolt"],
            "scenario_source_screen_sha256": INPUTS["a12_axial_reference_screen"][1],
            "helper_source_sha256": INPUTS["wood_bearing_helper"][1],
        },
        "axes": axes_out,
        "group_max_comparison_only": group_comparisons,
        "seat_inventory": seats_out,
        "limits": [
            "A1-rear at load factor 1.0 is one conditional numerical response; this is not a six-case envelope, design qualification or complete-joint acceptance.",
            "A12-rear values appear only as explicit per-axis comparisons; A12 model, floor mask, response and native state are not transferred into this case.",
            "The 25NWUS dimensions are an unselected candidate range, not delivered washer measurements. Exact support polygons, head/nut footprints, actual bore, flatness, cuts and gaps remain unknown.",
            "Base-seat Fc_perp comparisons are unadjusted conditional DF-L No. 2 full-annulus component references. Candidate-block DF-L No. 2 ratios are what-if arithmetic only because the model binds blocks to a separate elastic diagnostic without strength grade; BG045 block seats are parallel to grain and receive no Fc_perp comparison.",
            "Washer-steel bending/spreading, bolt fracture, nut stripping/engagement, head/nut pull-through, and axial/lateral interaction are not calculated. No preload or friction is credited.",
            "No product selection, delivered conformance, new stock assignment, physical-floor qualification, fabrication release or climbing release is claimed.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    output = HERE / "screen.json"
    text = json.dumps(build_report(), indent=2, sort_keys=True) + "\n"
    if args.write:
        output.write_text(text)
        print(f"wrote {output.relative_to(ROOT)}")
    else:
        require(output.exists(), "screen.json missing; run --write first")
        require(output.read_text() == text, "screen.json differs from regenerated source-bound calculations")
        print("PASS: A1 case, context, parent 50-body proof, compatibility, and component calculations")
    print(f"screen_sha256={sha256(output) if output.exists() else 'written'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
