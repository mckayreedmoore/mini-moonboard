#!/usr/bin/env python3
"""Apply the unchanged original left-LEG component methods to fresh K12 forces.

This bounded screen covers only the two original left-LEG bolt axes that share
the changed ``base_side_left`` receiver. It derives force actions from the
fresh source-bound K12 corner report and compares them state-by-state with the
prior A12 register. It does not run a solver or qualify the new ten-hole group.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
OUT = HERE / "affected-demand-screen.json"

LEGACY_PACKET = BASE / "current-corner-left-leg-affected-demand-screen-attempt01"
LEGACY_PRODUCER = LEGACY_PACKET / "produce.py"
K12_PACKET = BASE / "current-corner-k12-rear-case-bound-export-attempt01"
K12_REPORT_PATH = K12_PACKET / "corner-demand-report.json"
K12_FREEZE_PATH = K12_PACKET / "projection-freeze.json"
K12_EXPORTER_PATH = K12_PACKET / "project_k12_corner.py"
REGISTER = BASE / "current-corner-left-leg-onward-transfer-register-attempt01/register.json"
MAP_DIR = BASE / "current-corner-left-leg-baseline-evidence-map-attempt01"
MAP_PATH = MAP_DIR / "baseline-evidence-map.json"

CASE_ID = "k12-rear"
PRIOR_CASE_ID = "a12-rear"
BOLTS = ("lumber_leg_bolt_left_1", "lumber_leg_bolt_left_2")
ROLES = ("retained_bolt_lateral_plane", "physical_bolt_outer_seat_tension")
LOAD_FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
AXIS = (-1.0, 0.0, 0.0)
RECEIVERS = ("base_side_left", "lumber_leg_left")
EXPECTED_K12_AXIAL_PEAKS_N = {
    "lumber_leg_bolt_left_1": 241.9659,
    "lumber_leg_bolt_left_2": 530.5748,
}

PINNED = {
    str(LEGACY_PRODUCER): "864a3478792f9bed37029b6475930b6560045c5ed6f52a575d7caa3e72beb8f3",
    str(K12_REPORT_PATH): "a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0",
    str(K12_FREEZE_PATH): "ccc1a92a1b70b8ab9b8a2d6b291b84d0ba8fa3b7b7b0b1ec3faa15d1c237e763",
    str(K12_EXPORTER_PATH): "f095da83a1597185e69205eaacfaee0302a3faad88e7ad0d3b1d55316ab7ff42",
    str(REGISTER): "b435f23d059d8b8399bcc5ab4afdbaa71171bac476b3a50953d68f8189cac8b0",
    str(MAP_PATH): "d072c67cfaa3a656b6ad17e83c73af001882a1a283589548fa81d074e78ef9fa",
}


class ScreenError(ValueError):
    pass


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, name: str) -> None:
    if not condition:
        raise ScreenError(name)


def import_legacy_producer():
    path = ROOT / LEGACY_PRODUCER
    require(path.is_file() and digest(path) == PINNED[str(LEGACY_PRODUCER)], "pinned_original_component_method_producer")
    spec = importlib.util.spec_from_file_location("pinned_original_left_leg_component_methods", path)
    require(spec is not None and spec.loader is not None, "legacy_component_method_module_importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify_k12_projection() -> tuple[dict[str, Any], dict[str, str]]:
    observed: dict[str, str] = {}
    for relative, expected in PINNED.items():
        path = ROOT / relative
        require(path.is_file(), f"pinned_source_exists:{relative}")
        actual = digest(path)
        require(actual == expected, f"pinned_source_sha256:{relative}")
        observed[relative] = actual

    report = load_json(ROOT / K12_REPORT_PATH)
    freeze = load_json(ROOT / K12_FREEZE_PATH)
    require(report.get("schema") == "current_corner_k12_rear_spr489_direct_master_case_bound_demand_report/v1"
            and report.get("status") == "PASS_K12_REAR_NUMERICAL_CORNER_DEMAND_REPORT_ONLY"
            and report.get("case_id") == CASE_ID,
            "fresh_k12_case_bound_corner_report_schema_and_status")
    require(report.get("method_variant") == "spr489_direct_c3d20_master_interpolation/v1"
            and report.get("actual_case_demand_usable_for_conditional_joint_checks") is True
            and report.get("qualification_boundary", {}).get("complete_joint_accepted") is False
            and report.get("qualification_boundary", {}).get("joint_resistance_accepted") is False,
            "fresh_k12_report_method_and_nonacceptance_boundary")
    freeze_ref = report.get("projection_input_freeze", {})
    require(freeze_ref.get("path") == str(K12_FREEZE_PATH)
            and freeze_ref.get("sha256") == digest(ROOT / K12_FREEZE_PATH),
            "k12_report_binds_its_projection_freeze")
    require(freeze.get("schema") == "current_corner_k12_rear_case_bound_projection_freeze/v1"
            and freeze.get("status") == "FROZEN_AFTER_PARENT_RESPONSE_AND_ALL50_GATES_BEFORE_EXPORT"
            and freeze.get("case_id") == CASE_ID
            and freeze.get("mechanical_acceptance") is False
            and freeze.get("joint_accepted") is False,
            "k12_projection_freeze_scope")
    source_map = freeze.get("source_file_sha256", {})
    require(len(source_map) == freeze.get("source_file_count")
            and canonical_sha256(dict(sorted(source_map.items()))) == freeze.get("source_file_set_canonical_sha256"),
            "k12_projection_freeze_source_set_digest")
    for relative, expected in source_map.items():
        path = ROOT / relative
        require(path.is_file() and digest(path) == expected, f"k12_projection_frozen_source:{relative}")
        observed[relative] = expected
    response_pins = report.get("authenticated_sources", {})
    for path_key, sha_key in (
        ("native_model_path", "native_model_sha256"), ("native_deck_path", "native_deck_sha256"),
        ("native_dat_path", "native_dat_sha256"), ("response_audit_path", "response_audit_sha256"),
        ("all_body_audit_path", "all_body_audit_sha256"),
        ("parent_terminal_assessment_path", "parent_terminal_assessment_sha256"),
        ("fresh_case_register_path", "fresh_case_register_sha256"),
    ):
        path = Path(response_pins[path_key])
        path = path if path.is_absolute() else ROOT / path
        require(path.is_file() and digest(path) == response_pins[sha_key], f"k12_report_source_binding:{path_key}")
        observed[str(path.relative_to(ROOT))] = response_pins[sha_key]

    count = report.get("all_increment_count_summary", {})
    require(count.get("corner_interfaces_per_increment") == 338
            and count.get("contact_rows_per_increment") == 232
            and count.get("physical_bolts") == 6 and count.get("lateral_plane_actions") == 8
            and count.get("outer_seat_ties") == 6 and count.get("washer_seats") == 12
            and count.get("retained_original_arrangements") == 12
            and count.get("new_candidate_axis_count_separate_from_retained") == 92
            and count.get("hillman_panel_kicker_axes") == 66,
            "corner_report_preserves_reviewed_6_8_6_12_and_92_12_66_counts")
    require(report.get("source_contract", {}).get("interface_inventory_count") == 338
            and report.get("source_contract", {}).get("new_block_axis_count") == 92
            and report.get("source_contract", {}).get("retained_original_leg_runner_axis_count") == 12,
            "corner_source_contract_inventory")
    require(report.get("parent_independent_all_50_body_audit", {}).get("status") == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS"
            and report.get("parent_independent_all_50_body_audit", {}).get("all_body_and_global_interval_sums_passed") is True
            and report.get("parent_terminal_assessment", {}).get("status") == "PASS_PARENT_K12_REAR_DIRECT_RESPONSE_AND_ALL50"
            and report.get("parent_terminal_assessment", {}).get("conditional_case_forces_usable") is True,
            "fresh_response_and_all_50_body_gates_are_passed")

    increments = report.get("onward_transfer_scope", {}).get("per_increment_action_rows", [])
    require(len(increments) == len(LOAD_FACTORS), "k12_report_seven_affected_axis_increments")
    for i, (increment, factor) in enumerate(zip(increments, LOAD_FACTORS, strict=True)):
        require(math.isclose(float(increment.get("load_factor", -1)), factor, rel_tol=0.0, abs_tol=1e-12),
                f"k12_report_increment_load_factor_{i}")
        axes = increment.get("axes", {})
        require(set(axes) == set(BOLTS), f"k12_report_increment_{i}_only_two_affected_original_bolt_axes")
        for bolt in BOLTS:
            rows = axes[bolt]
            require(len(rows) == 2, f"k12_report_increment_{i}_{bolt}_two_source_interfaces")
            by_role = {row.get("role"): row for row in rows}
            require(set(by_role) == set(ROLES), f"k12_report_increment_{i}_{bolt}_roles")
            for role, source_name in (("retained_bolt_lateral_plane", f"{bolt}/wood-interface"),
                                      ("physical_bolt_outer_seat_tension", f"{bolt}/outer-seat-axial-tie")):
                row = by_role[role]
                require(row.get("source_connection_name") == source_name
                        and row.get("first") == RECEIVERS[0] and row.get("second") == RECEIVERS[1]
                        and len(row.get("force_on_first_xyz_n", [])) == 3
                        and len(row.get("force_on_second_xyz_n", [])) == 3
                        and len(row.get("force_rounding_radius_xyz_n", [])) == 3,
                        f"k12_report_increment_{i}_{bolt}_{role}_identity_vectors_and_bounds")
                action_sum = [row["force_on_first_xyz_n"][j] + row["force_on_second_xyz_n"][j] for j in range(3)]
                require(max(map(abs, action_sum)) < 1e-9
                        and all(math.isfinite(float(v)) and float(v) >= 0.0 for v in row["force_rounding_radius_xyz_n"]),
                        f"k12_report_increment_{i}_{bolt}_{role}_action_reaction_and_finite_bounds")
    return report, observed


def load_baseline(legacy: Any) -> tuple[dict[str, Any], dict[str, Any], dict[tuple, dict[str, Any]], dict[str, str]]:
    source_pins = legacy.verify_pins()
    register = legacy.load_json(ROOT / legacy.REGISTER)
    mapping = legacy.load_json(ROOT / legacy.MAP)
    source_pins.update(legacy.verify_embedded_pins(register.get("source_sha256", {}), label="onward register"))
    source_pins.update(legacy.verify_embedded_pins(mapping.get("source_pins_sha256", {}), label="baseline evidence map"))
    indexed = legacy.validate_register(register)
    geometries, checks = {}, {}
    for case in legacy.CASES:
        case_dir = ROOT / "fea/results/floor-runner-mvp" / case
        geometries[case] = legacy.load_json(case_dir / "geometry.json")
        checks[case] = legacy.load_json(case_dir / "checks.json")
    legacy.validate_baseline_inputs(mapping, geometries, checks)
    dependency = mapping.get("geometry_and_demand_dependency", {})
    require("ten new candidate bolt axes" in dependency.get("changed_receiver", "")
            and "New holes in base_side_left affect the local net-section, group tear-out/splitting" in dependency.get("changed_receiver", "")
            and dependency.get("reuse_boundary", "").find("no blanket claim") >= 0,
            "baseline_map_preserves_ten_bore_group_net_and_splitting_gap")
    return mapping, geometries[PRIOR_CASE_ID], indexed, source_pins


def require_axis_rows(row: dict[str, Any], *, case: str, bolt: str, factor: float,
                      lateral: bool) -> tuple[list[float], list[float], list[float], dict[str, Any]]:
    force_key = "force_on_base_side_left_xyz_N"
    first = row.get(force_key)
    second = row.get("force_on_lumber_leg_left_xyz_N")
    interface = row.get("source_interface", {})
    radius = interface.get("force_rounding_radius_xyz_n", [0.0, 0.0, 0.0])
    require(len(first or []) == len(second or []) == len(radius) == 3,
            f"{case}_{bolt}_{factor}_source_action_vectors_and_rounding_radius")
    require(interface.get("first") == RECEIVERS[0] and interface.get("second") == RECEIVERS[1]
            and interface.get("force_on_first_xyz_n") == first
            and interface.get("force_on_second_xyz_n") == second,
            f"{case}_{bolt}_{factor}_source_interface_pairing")
    if lateral:
        require(abs(float(first[0])) <= 1e-8, f"{case}_{bolt}_{factor}_lateral_plane_transverse")
    else:
        require(abs(float(first[1])) <= 1e-8 and abs(float(first[2])) <= 1e-8,
                f"{case}_{bolt}_{factor}_axial_tie_aligned")
    return list(map(float, first)), list(map(float, second)), list(map(float, radius)), interface


def result_for_state(legacy: Any, *, geometry: dict[str, Any], bolt: str,
                     lateral_first: list[float], lateral_second: list[float], lateral_radius: list[float],
                     axial_first: list[float], axial_second: list[float], axial_radius: list[float],
                     factor: float, new_sources: dict[str, Any], prior_sources: dict[str, Any]) -> dict[str, Any]:
    bolt_geometry = geometry["geometries_by_bolt_name"][bolt]
    hardware = legacy.hardware_for(geometry, bolt)
    tension = sum(AXIS[i] * axial_first[i] for i in range(3))
    signed_tension = sum(AXIS[i] * axial_first[i] for i in range(3))
    require(tension >= -1e-8 and math.isclose(tension, signed_tension, rel_tol=1e-10, abs_tol=1e-8),
            f"k12_{bolt}_{factor}_axial_tie_tension_sign")
    require(abs(lateral_first[0]) <= 1e-8, f"k12_{bolt}_{factor}_lateral_force_transverse")
    combined_first = [lateral_first[i] + axial_first[i] for i in range(3)]
    combined_second = [lateral_second[i] + axial_second[i] for i in range(3)]
    combined_radius = [lateral_radius[i] + axial_radius[i] for i in range(3)]
    demand_row = {
        "axis": list(AXIS), "first": RECEIVERS[0], "second": RECEIVERS[1],
        "force_on_first_xyz_n": combined_first, "force_on_second_xyz_n": combined_second,
    }
    result = legacy.bolt_check(demand_row, bolt_geometry, hardware)
    lateral = [combined_first[i] - sum(combined_first[j] * AXIS[j] for j in range(3)) * AXIS[i]
               for i in range(3)]
    lateral_magnitude = legacy.norm(lateral)
    require(legacy.close(result["lateral_demand_n"], lateral_magnitude)
            and legacy.close(result["hardware"]["absolute_axial_increment_n"], abs(tension)),
            f"k12_{bolt}_{factor}_reused_component_method_matches_signed_split")

    prior_lateral_first = prior_sources["lateral_force_on_base_side_left_xyz_N"]
    prior_axial_first = prior_sources["outer_seat_tension_force_on_base_side_left_xyz_N"]
    prior_lateral_radius = prior_sources["lateral_force_rounding_radius_xyz_N"]
    prior_axial_radius = prior_sources["axial_force_rounding_radius_xyz_N"]
    prior_tension = sum(AXIS[i] * prior_axial_first[i] for i in range(3))
    prior_lateral = [prior_lateral_first[0], prior_lateral_first[1], prior_lateral_first[2]]
    prior_lateral[0] = 0.0
    prior_lateral_magnitude = legacy.norm(prior_lateral)
    lateral_delta = [lateral_first[i] - prior_lateral_first[i] for i in range(3)]
    axial_delta = tension - prior_tension
    lateral_delta_radius = [lateral_radius[i] + prior_lateral_radius[i] for i in range(3)]
    axial_delta_radius = abs(AXIS[0]) * (axial_radius[0] + prior_axial_radius[0])
    lateral_norm_delta_radius = legacy.norm(lateral_delta_radius)
    prior_lateral_norm_radius = legacy.norm(prior_lateral_radius)
    new_lateral_norm_radius = legacy.norm(lateral_radius)

    angles = {
        member: legacy.directional_angle_deg(lateral, bolt_geometry["members"][member]["grain"])
        for member in RECEIVERS
    }
    return {
        "load_factor": factor,
        "source_connection_names": new_sources["connection_names"],
        "source_row_ids": new_sources["source_row_ids"],
        "k12_response_force_rounding_radius_xyz_N": {
            "lateral": lateral_radius,
            "axial": axial_radius,
            "combined": combined_radius,
        },
        "prior_a12_register_force_rounding_radius_xyz_N": {
            "lateral": prior_lateral_radius,
            "axial": prior_axial_radius,
        },
        "lateral_force_on_base_side_left_xyz_N": lateral_first,
        "lateral_force_on_lumber_leg_left_xyz_N": lateral_second,
        "outer_seat_tension_force_on_base_side_left_xyz_N": axial_first,
        "outer_seat_tension_force_on_lumber_leg_left_xyz_N": axial_second,
        "signed_outer_seat_tension_N": tension,
        "combined_per_bolt_force_on_base_side_left_xyz_N": combined_first,
        "combined_per_bolt_force_on_lumber_leg_left_xyz_N": combined_second,
        "combined_force_rounding_radius_xyz_N": combined_radius,
        "lateral_resultant_N": lateral_magnitude,
        "lateral_resultant_rounding_radius_N": new_lateral_norm_radius,
        "lateral_load_to_grain_acute_angle_deg": angles,
        "lateral_reference_N": result["lateral_reference_n"],
        "lateral_ratio_with_fixed_legacy_Ktheta_1_25": result["lateral_ratio"],
        "governing_yield_mode": result["dowel_reference"]["governing_mode"],
        "all_six_yield_mode_references_lbf": result["dowel_reference"]["reference_values_lbf"],
        "directional_bearing_psi_by_member": {
            member: value for member, value in zip(RECEIVERS, result["bearing_psi"], strict=True)
        },
        "external_edge_screen_by_member": result["placement"],
        "direct_steel_interaction_ratio_with_provisional_hardware": result["hardware"]["steel_direct_ratio"],
        "washer_wood_bearing_ratio_by_face_with_provisional_hardware": [
            item["wood_bearing_ratio"] for item in result["hardware"]["washers"]
        ],
        "washer_elastic_bending_ratio_by_face_with_provisional_hardware": [
            item["elastic_bending_ratio"] for item in result["hardware"]["washers"]
        ],
        "prior_a12_lateral_force_on_base_side_left_xyz_N": prior_lateral_first,
        "prior_a12_lateral_resultant_N": prior_lateral_magnitude,
        "prior_a12_outer_seat_tension_force_on_base_side_left_xyz_N": prior_axial_first,
        "prior_a12_signed_outer_seat_tension_N": prior_tension,
        "change_from_prior_a12_same_load_factor": {
            "lateral_force_vector_xyz_N": lateral_delta,
            "lateral_force_vector_component_radius_xyz_N": lateral_delta_radius,
            "lateral_resultant_delta_N": lateral_magnitude - prior_lateral_magnitude,
            "lateral_resultant_delta_radius_N": new_lateral_norm_radius + prior_lateral_norm_radius,
            "signed_axial_tension_delta_N": axial_delta,
            "signed_axial_tension_delta_radius_N": axial_delta_radius,
            "axial_percent_change_vs_prior_a12": (100.0 * axial_delta / prior_tension) if prior_tension else None,
        },
        "source_bounds_interpretation": "Componentwise printed-token rounding radii from each response/register source row; delta radius uses the sum of source radii, not a physical uncertainty or design factor.",
        "method_qualified_for_design": result["qualified_for_design"],
    }


def build_report() -> dict[str, Any]:
    legacy = import_legacy_producer()
    report, k12_source_hashes = verify_k12_projection()
    mapping, geometry, indexed, legacy_source_hashes = load_baseline(legacy)
    source_hashes = {**legacy_source_hashes, **k12_source_hashes}
    # Pin the evidence map and old producer again in the merged output inventory.
    source_hashes[str(MAP_PATH)] = digest(ROOT / MAP_PATH)
    source_hashes[str(LEGACY_PRODUCER)] = digest(ROOT / LEGACY_PRODUCER)
    source_hashes[str(REGISTER)] = digest(ROOT / REGISTER)

    dependency = mapping["geometry_and_demand_dependency"]
    require(dependency.get("changed_receiver") and dependency.get("criteria_or_input_not_supplied_by_legacy_map")
            and dependency.get("reuse_boundary"), "source_map_geometry_and_evidence_boundary_present")

    geometries = {}
    checks = {}
    for case in legacy.CASES:
        case_dir = ROOT / "fea/results/floor-runner-mvp" / case
        geometries[case] = legacy.load_json(case_dir / "geometry.json")
        checks[case] = legacy.load_json(case_dir / "checks.json")
    legacy.validate_baseline_inputs(mapping, geometries, checks)

    method_inputs_by_bolt: dict[str, Any] = {}
    results = []
    summaries = []
    increments = report["onward_transfer_scope"]["per_increment_action_rows"]
    for bolt in BOLTS:
        bolt_geometry = geometry["geometries_by_bolt_name"][bolt]
        hardware = legacy.hardware_for(geometry, bolt)
        method_inputs_by_bolt[bolt] = {
            "nominal_diameter_mm": bolt_geometry["diameter_mm"],
            "bolt_bending_yield_psi": bolt_geometry["bending_yield_psi"],
            "receivers": list(RECEIVERS),
            "member_inputs": {
                member: {
                    key: bolt_geometry["members"][member][key]
                    for key in ("grain", "bearing_length_mm", "specific_gravity", "parallel_bearing_psi", "edge_distances_mm")
                }
                for member in RECEIVERS
            },
            "hardware_assumptions": hardware,
            "selected_hardware_row_is_provisional": geometry["hardware_by_name"][bolt]["provisional"],
            "source_geometry_applicability": "Original source map verifies this named axis, receiver pair, station, schedule, and hardware remain unchanged; ten new bores are in base_side_left only and their group/net/splitting effects remain unresolved.",
        }
        states = []
        for increment in increments:
            factor = float(increment["load_factor"])
            axes = increment["axes"][bolt]
            by_role = {row["role"]: row for row in axes}
            lateral_row = by_role["retained_bolt_lateral_plane"]
            axial_row = by_role["physical_bolt_outer_seat_tension"]
            lateral_first = list(map(float, lateral_row["force_on_first_xyz_n"]))
            lateral_second = list(map(float, lateral_row["force_on_second_xyz_n"]))
            lateral_radius = list(map(float, lateral_row["force_rounding_radius_xyz_n"]))
            axial_first = list(map(float, axial_row["force_on_first_xyz_n"]))
            axial_second = list(map(float, axial_row["force_on_second_xyz_n"]))
            axial_radius = list(map(float, axial_row["force_rounding_radius_xyz_n"]))
            prior_lateral_row = indexed[(PRIOR_CASE_ID, bolt, factor, "retained_bolt_lateral_plane")]
            prior_axial_row = indexed[(PRIOR_CASE_ID, bolt, factor, "physical_bolt_outer_seat_tension")]
            prior_lateral_first, prior_lateral_second, prior_lateral_radius, _ = require_axis_rows(
                prior_lateral_row, case=PRIOR_CASE_ID, bolt=bolt, factor=factor, lateral=True)
            prior_axial_first, prior_axial_second, prior_axial_radius, _ = require_axis_rows(
                prior_axial_row, case=PRIOR_CASE_ID, bolt=bolt, factor=factor, lateral=False)
            new_sources = {
                "connection_names": [lateral_row["source_connection_name"], axial_row["source_connection_name"]],
                "source_row_ids": list(lateral_row["source_row_ids"]) + list(axial_row["source_row_ids"]),
            }
            prior_sources = {
                "lateral_force_on_base_side_left_xyz_N": prior_lateral_first,
                "lateral_force_on_lumber_leg_left_xyz_N": prior_lateral_second,
                "lateral_force_rounding_radius_xyz_N": prior_lateral_radius,
                "outer_seat_tension_force_on_base_side_left_xyz_N": prior_axial_first,
                "outer_seat_tension_force_on_lumber_leg_left_xyz_N": prior_axial_second,
                "axial_force_rounding_radius_xyz_N": prior_axial_radius,
            }
            state = result_for_state(
                legacy, geometry=geometry, bolt=bolt,
                lateral_first=lateral_first, lateral_second=lateral_second, lateral_radius=lateral_radius,
                axial_first=axial_first, axial_second=axial_second, axial_radius=axial_radius,
                factor=factor, new_sources=new_sources, prior_sources=prior_sources,
            )
            states.append(state)

        max_lateral_state = max(states, key=lambda row: row["lateral_resultant_N"])
        max_axial_state = max(states, key=lambda row: row["signed_outer_seat_tension_N"])
        max_steel_state = max(states, key=lambda row: row["direct_steel_interaction_ratio_with_provisional_hardware"])
        max_washer_bearing_state = max(states, key=lambda row: max(row["washer_wood_bearing_ratio_by_face_with_provisional_hardware"]))
        max_washer_bending_state = max(states, key=lambda row: max(row["washer_elastic_bending_ratio_by_face_with_provisional_hardware"]))
        minimum_edge = min(
            (
                (member, edge, state["external_edge_screen_by_member"][member]["margins_mm"][edge], state["load_factor"])
                for state in states for member in RECEIVERS
                for edge in state["external_edge_screen_by_member"][member]["margins_mm"]
            ),
            key=lambda item: item[2],
        )
        peak_axial = max(state["signed_outer_seat_tension_N"] for state in states)
        require(legacy.close(peak_axial, EXPECTED_K12_AXIAL_PEAKS_N[bolt]), f"K12_{bolt}_expected_peak_axial_source_value")
        summary = {
            "case_id": CASE_ID,
            "prior_same_factor_comparator_case_id": PRIOR_CASE_ID,
            "axis_id": bolt,
            "load_factor_count": len(states),
            "peak_lateral_demand_N": max_lateral_state["lateral_resultant_N"],
            "peak_lateral_rounding_radius_N": max_lateral_state["lateral_resultant_rounding_radius_N"],
            "peak_lateral_demand_load_factor": max_lateral_state["load_factor"],
            "conditional_original_method_lateral_reference_at_governing_state_N": max_lateral_state["lateral_reference_N"],
            "conditional_original_method_lateral_ratio_with_fixed_Ktheta_1_25": max_lateral_state["lateral_ratio_with_fixed_legacy_Ktheta_1_25"],
            "lateral_governing_yield_mode": max_lateral_state["governing_yield_mode"],
            "peak_axial_tension_N": peak_axial,
            "peak_axial_tension_rounding_radius_N": max_axial_state["k12_response_force_rounding_radius_xyz_N"]["axial"][0],
            "peak_axial_tension_load_factor": max_axial_state["load_factor"],
            "prior_a12_peak_axial_tension_N": max(state["prior_a12_signed_outer_seat_tension_N"] for state in states),
            "peak_axial_change_from_prior_a12_N": max_axial_state["change_from_prior_a12_same_load_factor"]["signed_axial_tension_delta_N"],
            "peak_axial_percent_change_from_prior_a12": max_axial_state["change_from_prior_a12_same_load_factor"]["axial_percent_change_vs_prior_a12"],
            "peak_direct_steel_interaction_ratio_with_provisional_hardware": max_steel_state["direct_steel_interaction_ratio_with_provisional_hardware"],
            "peak_steel_load_factor": max_steel_state["load_factor"],
            "peak_washer_wood_bearing_ratio_with_provisional_hardware": max(max_washer_bearing_state["washer_wood_bearing_ratio_by_face_with_provisional_hardware"]),
            "peak_washer_bending_ratio_with_provisional_hardware": max(max_washer_bending_state["washer_elastic_bending_ratio_by_face_with_provisional_hardware"]),
            "minimum_old_external_edge_screen_margin_mm": minimum_edge[2],
            "minimum_edge_screen_location": {"member": minimum_edge[0], "edge": minimum_edge[1], "load_factor": minimum_edge[3]},
            "existing_individual_component_bounds_met": all([
                max_lateral_state["lateral_ratio_with_fixed_legacy_Ktheta_1_25"] < 1.0,
                max_steel_state["direct_steel_interaction_ratio_with_provisional_hardware"] < 1.0,
                max(max_washer_bearing_state["washer_wood_bearing_ratio_by_face_with_provisional_hardware"]) < 1.0,
                max(max_washer_bending_state["washer_elastic_bending_ratio_by_face_with_provisional_hardware"]) < 1.0,
                minimum_edge[2] >= 0.0,
            ]),
            "qualified_for_design": False,
            "states": states,
        }
        results.append(summary)
        summaries.append({key: value for key, value in summary.items() if key != "states"})

    report_a12_rows = [row for row in indexed.values() if row.get("case_id") == PRIOR_CASE_ID and row.get("axis_id") in BOLTS]
    require(len(report_a12_rows) == 28, "prior_a12_comparison_is_limited_to_28_two_axis_rows")
    geometry_summary = mapping["geometry_and_demand_dependency"]
    old_geometry = mapping["existing_selected_baseline_geometry"]
    require(geometry_summary.get("changed_receiver") and geometry_summary.get("retained_bolt_axis_identity")
            and old_geometry.get("dimension_interpretation", {}).get("nominal_bolt_diameter_mm") == 12.7,
            "source_map_proves_original_axis_geometry_hardware_method_basis")

    return {
        "schema": "current_corner_left_leg_k12_affected_demand_screen/v1",
        "status": "CONDITIONAL_ORIGINAL_LEFT_LEG_COMPONENT_METHODS_APPLIED_TO_FRESH_K12_FORCES",
        "candidate": "compact-floor-flush-wood-joints-development",
        "case_id": CASE_ID,
        "prior_comparator_case_id": PRIOR_CASE_ID,
        "screen_scope": "Only two retained original left LEG bolts at the changed base_side_left receiver; seven fresh K12 states each. No other retained arrangement or new corner bolt is screened here.",
        "source_sha256": dict(sorted(source_hashes.items())),
        "fresh_k12_corner_report": {
            "path": str(K12_REPORT_PATH),
            "sha256": digest(ROOT / K12_REPORT_PATH),
            "native_model_sha256": report["authenticated_sources"]["native_model_sha256"],
            "native_deck_sha256": report["authenticated_sources"]["native_deck_sha256"],
            "native_dat_sha256": report["authenticated_sources"]["native_dat_sha256"],
            "response_audit_sha256": report["authenticated_sources"]["response_audit_sha256"],
            "parent_all_50_audit_sha256": report["authenticated_sources"]["all_body_audit_sha256"],
            "parent_terminal_assessment_sha256": report["authenticated_sources"]["parent_terminal_assessment_sha256"],
            "parent_status": report["parent_terminal_assessment"]["status"],
            "historical_forces_or_states_reused": False,
        },
        "prior_a12_force_comparator": {
            "register_path": str(REGISTER),
            "register_sha256": digest(ROOT / REGISTER),
            "same_load_factor_only": True,
            "used_for_resistance_or_capacity": False,
            "historical_component_methods_reused_from": str(LEGACY_PRODUCER),
        },
        "geometry_applicability": {
            "baseline_evidence_map_path": str(MAP_PATH),
            "baseline_evidence_map_sha256": digest(ROOT / MAP_PATH),
            "retained_original_axes": list(BOLTS),
            "receiver_pair": list(RECEIVERS),
            "source_map_axis_and_hardware_identity": geometry_summary["retained_bolt_axis_identity"],
            "ten_new_bores_in_base_side_left": 10,
            "new_bores_in_lumber_leg_left": 0,
            "specific_changed_receiver": geometry_summary["changed_receiver"],
            "preserved_unresolved_evidence_gaps": geometry_summary["criteria_or_input_not_supplied_by_legacy_map"],
            "reuse_boundary": geometry_summary["reuse_boundary"],
            "original_selected_baseline_geometry_details": {
                "nominal_diameter_mm": old_geometry["dimension_interpretation"]["nominal_bolt_diameter_mm"],
                "bearing_lengths_mm": old_geometry["dimension_interpretation"]["per_member_bearing_length_mm"],
                "nominal_length_mm": old_geometry["dimension_interpretation"]["nominal_length_mm"],
                "wood_grip_mm": old_geometry["dimension_interpretation"]["wood_grip_mm"],
                "washer_od_mm": old_geometry["dimension_interpretation"]["washer_od_mm"],
                "washer_thickness_mm": old_geometry["dimension_interpretation"]["washer_thickness_mm"],
                "thread_and_purchased_length_status": old_geometry["dimension_interpretation"]["purchased_length_and_thread_dimensions"],
                "schedule_axis_rows": old_geometry["axis_rows"],
                "hardware_rows": old_geometry["hardware_rows"],
            },
            "group_net_section_tearout_splitting_around_added_bores_assessed": False,
        },
        "method": {
            "lateral": "Reused the original pinned fea.thick_leg_checks.bolt_check and fea.dowel_yield.single_shear branch; one single-shear plane, nominal 12.7 mm diameter, 88.9 mm bearing in both solid members, SG 0.5, Fe_parallel 5600 psi, the existing Fe_perp equation and fixed original NDS yield-reduction terms (Im/Is 5, II 4.5, IIIm/IIIs/IV 4), with recorded legacy Ktheta 1.25. No new angle branch was added.",
            "axial_and_hardware": "Reused original fea.compact_rail_checks.hardware_assumptions and fea.thick_leg_checks.hardware_check. Same-factor axial tie and lateral plane are paired by the retained bolt ID in the existing force-only direct steel interaction and axial-only washer component formulas.",
            "hardware_status": "Provisional Grade 5 bolt and washer assumptions from the pinned baseline evidence map; delivered part dimensions/thread transition remain unverified.",
            "partial_thread_condition": "Nominal-diameter screen remains conditional on delivered thread/runout leaving at most one quarter of each 88.9 mm wood bearing length threaded, per existing NDS 12.3.7.2; schedule thread dimensions and purchased length remain blank.",
            "edge_screen": "Original external stock-boundary 7D grain-end and force-directed 4D/1.5D depth-edge screen only. Clearance margins exclude the ten added bores and are not group/section checks.",
            "force_bounds": "New and A12 source component rounding radii are retained. Same-factor force-delta component bounds conservatively sum the two source radii; they are printed-token bounds, not material or engineering uncertainty.",
            "screen_only": True,
            "no_prestress_prying_or_moment_inferred": True,
        },
        "method_inputs_by_bolt": method_inputs_by_bolt,
        "per_bolt_results": results,
        "two_axis_summary": summaries,
        "scope_boundary": {
            "retained_original_arrangements_total": 12,
            "arrangements_screened_here": 2,
            "other_ten_arrangements_reopened": False,
            "new_92_axis_candidate_resistance_qualified": False,
            "group_capacity_established": False,
            "joint_accepted": False,
            "qualified_for_design": False,
            "full_thread_root_sensitivity_adopted": False,
            "mechanical_acceptance": False,
        },
        "limits": [
            "This reuses the existing individual-bolt component equations on two new signed force histories. It does not inherit either A12 baseline demand, ratio, group result or case status.",
            "The K12 lateral and axial actions remain separate physical source rows; they are paired only by matching bolt ID and load factor for the original force-only component screen. No couple, bolt bending, prying or preload is inferred.",
            "The two original bolt stations, receiver pair and baseline hardware/method record are source-mapped unchanged. Ten additional base_side_left bores create the specific unresolved local net-section/group tear-out/splitting dependency; this screen does not resolve it.",
            "The provisional hardware assumption is not a delivered-part verification. Axial checks do not establish wood withdrawal, pull-through, splitting or manufacturer-rated resistance.",
            "Below-one individual component ratios are not joint acceptance. No blanket requalification of the other ten original LEG/FLOOR-RUNNER arrangements is implied.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="reproduce and compare the source-bound screen")
    args = parser.parse_args()
    result = build_report()
    if args.verify:
        require(OUT.is_file() and load_json(OUT) == result, "saved_k12_affected_demand_screen_matches_reproduction")
        print("PASS: pinned K12 demand, A12 same-factor comparison, geometry map, and two original-bolt component screens reproduced")
    else:
        require(not OUT.exists(), "screen_output_write_once")
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        print(str(OUT.relative_to(ROOT)))


if __name__ == "__main__":
    try:
        main()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError) as error:
        print(f"BLOCKED_K12_AFFECTED_LEFT_LEG_SCREEN: {error}", file=sys.stderr)
        raise
