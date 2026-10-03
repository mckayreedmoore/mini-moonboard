#!/usr/bin/env python3
"""Reproduce the BG001 Appendix E parallel-component screen across 21 states."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / ".git").exists())
ACCEL = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
THREE_CASE = ACCEL / "current-bg001-three-case-resultant-reference-attempt01"
PRIOR = ACCEL / "current-bg001-appendix-e-parallel-row-screen-attempt01"
SECTION_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "current-corner-local-wood-screen-attempt01/section-screen.json"
)
HELPER_REL = Path("mini_moonboard/bolted_timber_checks.py")
OUTPUT = HERE / "screen.json"
PINS_OUTPUT = HERE / "source-pins.json"

INPUTS = {
    "three_case_producer": (
        THREE_CASE / "produce.py",
        "7af02f47ef059efb2ac583cd52d451c14b88044e089f47a37f9b10312d3581b6",
    ),
    "three_case_screen": (
        THREE_CASE / "screen.json",
        "fe7cbb6f211dd35f2aa68b23819446b5f832cc4fcc16f0ac7635bd883a20ce2f",
    ),
    "three_case_source_pins": (
        THREE_CASE / "source-pins.json",
        "d20a4ae22f3abc16a9df38556102226372831c08a754400217454eeffd1e062a",
    ),
    "prior_method_producer": (
        PRIOR / "produce.py",
        "2f4b735626007971156d919073be1f5aa1256bba90b10387eb766a3627452a58",
    ),
    "prior_method_readme": (
        PRIOR / "README.md",
        "184c5736a417466c7b24cdceaf835a3867baf2661cb68d735380aadbdfd097eb",
    ),
    "prior_a12_screen": (
        PRIOR / "screen.json",
        "3df6bf97fd4dfd07e81f17fa76bf4d7a841e055fa895f2d474984cfef030b488",
    ),
    "section_geometry_screen": (
        ROOT / SECTION_REL,
        "22209a82b0bda6dfc5c140ccc4e481717e0e7c71d30a5827271c81ac71070564",
    ),
    "reference_helper": (
        ROOT / HELPER_REL,
        "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13",
    ),
}

EXPECTED_CASES = ("a1-rear", "a12-rear", "k12-rear")
EXPECTED_FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
EXPECTED_MEMBERS = ("knee_outer_left_spine", "base_post_outer_left")
EXPECTED_AXES = ("knee_outer_left_post_1", "knee_outer_left_post_2")
N_PER_LBF = 4.4482216152605
MM_PER_IN = 25.4
BASE_FV_PSI = 180.0
BASE_FT_PSI = 575.0
TOL = 1e-8


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def close(actual: float, expected: float, *, atol: float = TOL) -> bool:
    return math.isclose(actual, expected, rel_tol=1e-10, abs_tol=atol)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_helper():
    path = ROOT / HELPER_REL
    spec = importlib.util.spec_from_file_location("pinned_bg001_appendix_e_helper", path)
    require(spec is not None and spec.loader is not None, "cannot load pinned timber helper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def vector_sum(vectors: list[list[float]]) -> list[float]:
    require(bool(vectors), "cannot sum an empty action set")
    return [math.fsum(float(vector[i]) for vector in vectors) for i in range(3)]


def norm(vector: list[float]) -> float:
    return math.sqrt(math.fsum(component * component for component in vector))


def member_field(member: str) -> tuple[str, str]:
    if member == EXPECTED_MEMBERS[0]:
        return "force_on_first_xyz_N", "force_on_side_spine_xyz_N"
    if member == EXPECTED_MEMBERS[1]:
        return "force_on_second_xyz_N", "force_on_main_post_xyz_N"
    raise ValueError(f"unexpected receiver {member}")


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    observed: dict[str, str] = {}
    for label, (path, expected) in INPUTS.items():
        actual = sha256(path)
        require(actual == expected, f"{label} hash mismatch: {actual} != {expected}")
        observed[path.relative_to(ROOT).as_posix()] = actual

    source_pins = load_json(THREE_CASE / "source-pins.json")
    source = load_json(THREE_CASE / "screen.json")
    prior = load_json(PRIOR / "screen.json")
    section = load_json(ROOT / SECTION_REL)

    # Re-run the authenticated source packet's read-only verifier. This checks
    # all 42 receiver action pairs, ties, finished-profile rays and raw modes.
    verify_env = os.environ.copy()
    verify_env["PYTHONDONTWRITEBYTECODE"] = "1"
    replay = subprocess.run(
        [sys.executable, str(THREE_CASE / "produce.py"), "--verify"],
        cwd=ROOT,
        env=verify_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    require(replay.returncode == 0, f"three-case source replay failed: {replay.stdout.strip()}")

    require(source_pins.get("schema") == "current_bg001_three_case_resultant_reference_source_pins/v1",
            "unexpected three-case source pin schema")
    require(source.get("schema") == "current_bg001_three_case_resultant_reference/v1",
            "unexpected three-case result schema")
    require(source.get("joint_accepted") is False,
            "three-case source acceptance boundary changed")
    require(source.get("candidate") == "compact-floor-flush-wood-joints-development",
            "candidate identity changed")
    require(source.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1",
            "geometry revision changed")
    inventory = source["source_state_inventory"]
    require(inventory.get("case_load_states") == 21
            and inventory.get("BG001_per_state_physical_bolts") == 2
            and inventory.get("BG001_paired_bolt_state_records") == 42,
            "authenticated state/axis inventory changed")
    checks = source.get("checks", {})
    require(checks and all(value is True for value in checks.values()),
            "one or more three-case source checks are not true")

    # Verify all raw inputs transitively pinned by the 42-row producer.
    for rel, expected in source.get("source_sha256", {}).items():
        path = ROOT / rel
        actual = sha256(path)
        require(actual == expected, f"three-case input hash mismatch: {rel}")
        observed[rel] = actual
    require(source.get("source_sha256") == source_pins.get("local_sha256"),
            "three-case source-pins file and screen disagree")

    require(prior.get("schema") == "current_bg001_appendix_e_parallel_row_screen/v1",
            "unexpected A12 Appendix E oracle schema")
    require(prior.get("status") == "CONDITIONAL_PARALLEL_COMPONENT_SCREEN_ONLY"
            and prior.get("mechanical_acceptance") is False,
            "prior method acceptance boundary changed")
    require(prior.get("case_id") == "a12-rear"
            and close(float(prior["increment"]["load_factor"]), 1.0),
            "prior Appendix E oracle is not A12 full factor")
    require(prior["method_applicability"]["parallel_component_calculation_is_defensible"] is True
            and prior["method_applicability"]["full_appendix_e1_loading_condition_proven_for_real_BG001"] is False,
            "prior method scope changed")

    # The previous A12 packet carries direct pins to its model, response,
    # section, helper, material-basis and NDS scenario inputs. Check all of them.
    for rel, expected in prior.get("source_hashes", {}).items():
        path = ROOT / rel
        actual = sha256(path)
        require(actual == expected, f"prior A12 source hash mismatch: {rel}")
        observed[rel] = actual

    basis = source["conditional_reference_basis"]
    grain = basis["grain_axes"]
    for member in EXPECTED_MEMBERS:
        require(all(close(float(value), expected) for value, expected in
                       zip(grain[member], (0.0, 0.0, 1.0), strict=True)),
                f"proposed +Z grain changed for {member}")
    require(close(float(basis["diameter_in"]), 0.25)
            and close(float(basis["bolt_bending_yield_psi"]), 45000.0)
            and close(float(basis["Fe_endpoints_psi_parallel_perpendicular"][0]), 5600.0)
            and close(float(basis["Fe_endpoints_psi_parallel_perpendicular"][1]), 4450.0)
            and all(close(float(value), 1.5) for value in basis["bearing_lengths_in_main_side"])
            and close(float(basis["interface_gap_in"]), 0.0)
            and basis.get("actual_stock_or_hardware_observed") is False
            and basis.get("wood") == "DF-L No. 2, SG 0.50 proposed scenario; not stock observation",
            "conditional material/hardware hypotheses changed")
    require(close(float(prior["material_scenario"]["base_values"]["Fv_psi"]), BASE_FV_PSI)
            and close(float(prior["material_scenario"]["base_values"]["Ft_psi"]), BASE_FT_PSI)
            and prior["material_scenario"].get("service_scenario") == "dry, proposed conditional scenario",
            "prior dry DF-L No. 2 base material scenario changed")

    geometry = source["geometry_profile"]
    profile = geometry["profile_distances_mm_by_axis_and_receiver"]
    require(geometry.get("source_query_sha256") == "32d3eb326cbd4e12e91f10418f340f2a9f21509f593e3f91421f10ae6aa574d2",
            "finished-profile query pin changed")
    require(set(profile) == set(EXPECTED_AXES), "BG001 geometry axis inventory changed")
    for axis in EXPECTED_AXES:
        require(set(profile[axis]) == set(EXPECTED_MEMBERS), f"receiver geometry missing for {axis}")
        for member in EXPECTED_MEMBERS:
            require(all(ray in profile[axis][member] for ray in ("g-", "g+")),
                    f"grain-end profile rays missing for {axis}/{member}")

    prior_rows = {row["member_id"]: row for row in prior["row_tear_out_component_screens"]}
    require(set(prior_rows) == set(EXPECTED_MEMBERS), "prior A12 row oracle receiver inventory changed")
    spine_net = prior["spine_candidate_net_section_reference"]
    require(spine_net["member_id"] == EXPECTED_MEMBERS[0], "net-section oracle receiver changed")
    section_row = next(
        row for row in section["candidate_net_section_inputs"]
        if row["member_id"] == EXPECTED_MEMBERS[0]
        and set(EXPECTED_AXES).issubset(set(row["applies_to_axes"]))
    )
    geometry_inputs = section["modeled_geometry_inputs"]
    thickness_mm, width_mm = map(float, geometry_inputs["spine_XY_envelope_mm"])
    bore_mm = float(geometry_inputs["modeled_bore_diameter_mm_from_profile_void_intervals"])
    require(close(float(section_row["candidate_net_area_mm2"]), float(spine_net["candidate_net_area_mm2"])),
            "pinned spine net-section areas disagree")
    require(close(thickness_mm * (width_mm - bore_mm), float(section_row["candidate_net_area_mm2"])),
            "spine net-section geometry no longer reconstructs")
    require(set(EXPECTED_AXES).issubset(set(section_row["applies_to_axes"])),
            "pinned spine net plane no longer applies to both BG001 axes")

    thicknesses = [float(row["member_thickness_along_bolt_axis_mm"]) for row in prior_rows.values()]
    widths = [float(row["member_width_mm"]) for row in prior_rows.values()]
    pitches = [float(row["row_pitch_mm"]) for row in prior_rows.values()]
    require(all(close(value, thickness_mm) for value in thicknesses), "receiver bolt-axis thickness changed")
    require(all(close(value, width_mm) for value in widths), "receiver width differs from pinned section geometry")
    require(all(close(value, pitches[0]) for value in pitches), "prior receiver row pitches disagree")
    pitch_mm = pitches[0]
    require(close(pitch_mm, 42.05), "BG001 row pitch changed")
    bolt_z = {
        row["axis_id"]: float(row["axis_z_mm"])
        for row in prior["bg001_group_resultants"]["per_bolt_lateral_actions"]
    }
    require(set(bolt_z) == set(EXPECTED_AXES)
            and close(max(bolt_z.values()) - min(bolt_z.values()), pitch_mm),
            "A12 oracle bolt centers do not reproduce row pitch")

    helper = load_helper()
    thickness_in = thickness_mm / MM_PER_IN
    width_in = width_mm / MM_PER_IN
    bore_in = bore_mm / MM_PER_IN
    pitch_in = pitch_mm / MM_PER_IN
    row_reference_by_member: dict[str, dict[str, float]] = {}
    for member in EXPECTED_MEMBERS:
        row_reference = helper.dfl_parallel_row_tear_out_reference_lbf(
            thickness_in, 2,
            float(prior_rows[member]["loaded_end_distance_mm"]) / MM_PER_IN,
            pitch_in,
        )
        previous = prior_rows[member]
        require(close(row_reference, float(previous["base_unadjusted_row_reference_lbf"])),
                f"prior A12 row reference does not reproduce for {member}")
        require(close(float(previous["base_reference_inputs"]["Fv_psi"]), BASE_FV_PSI)
                and not previous["base_reference_inputs"]["Fv_adjusted_factors_applied"],
                "prior base Fv input or adjustment scope changed")
        row_reference_by_member[member] = {
            "base_reference_lbf": row_reference,
            "base_reference_N": row_reference * N_PER_LBF,
        }

    net_reference_lbf = helper.dfl_net_parallel_tension_reference_lbf(
        thickness_in, width_in, (bore_in,)
    )
    require(close(net_reference_lbf, float(spine_net["base_unadjusted_net_tension_reference_lbf"])),
            "prior A12 spine net-tension reference does not reproduce")
    require(close(float(spine_net["base_reference_inputs"]["Ft_psi"]), BASE_FT_PSI)
            and not spine_net["base_reference_inputs"]["Ft_adjusted_factors_applied"],
            "prior base Ft input or adjustment scope changed")

    states = source["records_by_same_case_load_state"]
    require(len(states) == 21, "expected 21 accepted rear case/load-factor states")
    actual_states = {(row["case_id"], float(row["load_factor"])) for row in states}
    expected_states = {(case, factor) for case in EXPECTED_CASES for factor in EXPECTED_FACTORS}
    require(actual_states == expected_states, "rear case/load-factor state inventory changed")

    records: list[dict[str, Any]] = []
    for state in states:
        case_id = state["case_id"]
        factor = float(state["load_factor"])
        bolt_rows = state["bolt_rows"]
        require({row["axis_id"] for row in bolt_rows} == set(EXPECTED_AXES)
                and len(bolt_rows) == 2, f"BG001 bolt inventory changed in {case_id}/{factor}")
        member_results: list[dict[str, Any]] = []
        bolt_actions: list[dict[str, Any]] = []
        summed_lateral: dict[str, list[float]] = {}
        summed_tie: dict[str, list[float]] = {}

        for member in EXPECTED_MEMBERS:
            force_key, tie_key = member_field(member)
            lateral_vectors: list[list[float]] = []
            tie_vectors: list[list[float]] = []
            for bolt in bolt_rows:
                pair = bolt["same_physical_bolt_lateral_action_pair"]
                tie = bolt["same_state_outer_seat_tie_out_of_lateral_reference"]
                require(pair["force_pair_closes"] is True, "source lateral force pair not closed")
                require(tie["retained_same_case_load_factor_and_bolt"] is True
                        and tie["combined_with_lateral_reference"] is False,
                        "same-state axial tie binding changed")
                force = [float(value) for value in pair[force_key]]
                tie_force = [float(value) for value in tie[tie_key]]
                lateral_vectors.append(force)
                tie_vectors.append(tie_force)
                if member == EXPECTED_MEMBERS[0]:
                    bolt_actions.append({
                        "axis_id": bolt["axis_id"],
                        "force_on_spine_xyz_N": [float(v) for v in pair["force_on_first_xyz_N"]],
                        "force_on_post_xyz_N": [float(v) for v in pair["force_on_second_xyz_N"]],
                        "separate_axial_tie_on_spine_xyz_N": [float(v) for v in tie["force_on_side_spine_xyz_N"]],
                        "separate_axial_tie_on_post_xyz_N": [float(v) for v in tie["force_on_main_post_xyz_N"]],
                    })
            group_force = vector_sum(lateral_vectors)
            group_tie = vector_sum(tie_vectors)
            summed_lateral[member] = group_force
            summed_tie[member] = group_tie

            signed_parallel = group_force[2]  # proposed grain is +Z
            require(abs(signed_parallel) > 1e-7, f"zero grain-parallel demand: {case_id}/{factor}/{member}")
            ray = "g-" if signed_parallel < 0 else "g+"
            end_distance_by_axis = {
                axis: float(profile[axis][member][ray]) for axis in EXPECTED_AXES
            }
            end_distance_mm = min(end_distance_by_axis.values())
            loaded_axis = min(end_distance_by_axis, key=end_distance_by_axis.get)
            critical_spacing_mm = min(end_distance_mm, pitch_mm)
            ref_lbf = helper.dfl_parallel_row_tear_out_reference_lbf(
                thickness_in, 2, end_distance_mm / MM_PER_IN, pitch_in
            )
            ref = {"base_reference_lbf": ref_lbf, "base_reference_N": ref_lbf * N_PER_LBF}
            parallel_demand_lbf = abs(signed_parallel) / N_PER_LBF
            parallel_demand_N = abs(signed_parallel)
            crossgrain = [group_force[0], group_force[1], 0.0]
            require(norm(crossgrain) > 1e-7,
                    f"mixed-action cross-grain component unexpectedly zero: {case_id}/{factor}/{member}")
            require(norm(summed_tie[member]) > 1e-7,
                    f"separate axial tie unexpectedly zero: {case_id}/{factor}/{member}")
            crossgrain_individual = [
                {"axis_id": row["axis_id"], "force_xyz_N": [
                    float(row["same_physical_bolt_lateral_action_pair"][member_field(member)[0]][0]),
                    float(row["same_physical_bolt_lateral_action_pair"][member_field(member)[0]][1]),
                    0.0,
                ]}
                for row in bolt_rows
            ]
            ratio = parallel_demand_lbf / ref["base_reference_lbf"]
            member_results.append({
                "case_id": case_id,
                "load_factor": factor,
                "member_id": member,
                "proposed_grain_global_xyz": [0.0, 0.0, 1.0],
                "signed_group_lateral_force_xyz_N": group_force,
                "signed_group_grain_parallel_force_along_plus_Z_N": signed_parallel,
                "parallel_component_demand_N": parallel_demand_N,
                "parallel_component_demand_lbf": parallel_demand_lbf,
                "group_cross_grain_force_xyz_N": crossgrain,
                "group_cross_grain_resultant_N": norm(crossgrain),
                "per_bolt_cross_grain_actions_xyz_N": crossgrain_individual,
                "parallel_to_group_crossgrain_angle_deg": math.degrees(
                    math.atan2(norm(crossgrain), abs(signed_parallel))
                ),
                "separate_group_axial_outer_seat_tie_force_xyz_N": summed_tie[member],
                "separate_group_axial_outer_seat_tie_resultant_N": norm(summed_tie[member]),
                "loaded_grain_end_ray": ray,
                "nearest_loaded_end_axis_id": loaded_axis,
                "loaded_end_distance_by_axis_mm": end_distance_by_axis,
                "loaded_end_distance_mm": end_distance_mm,
                "row_pitch_mm": pitch_mm,
                "critical_spacing_min_end_or_pitch_mm": critical_spacing_mm,
                "member_thickness_along_bolt_axis_mm": thickness_mm,
                "member_width_mm": width_mm,
                "n_bolts_in_row": 2,
                "row_reference_method": "NDS-2024 Appendix E.3-1/E.3.1, E.3-2; one row, two shear lines, reused conditional parallel-component method",
                "base_reference_inputs": {
                    "Fv_psi": BASE_FV_PSI,
                    "Fv_adjusted_factors_applied": [],
                    "adjusted_Fv_prime": "unresolved; apply applicable Chapter 4 sawn-lumber factors when material and service inputs are established",
                    "Cvr_applied": False,
                },
                "base_unadjusted_row_reference_lbf": ref["base_reference_lbf"],
                "base_unadjusted_row_reference_N": ref["base_reference_N"],
                "parallel_component_ratio_to_base_unadjusted_reference": ratio,
                "interpretation": "parallel-component/reference screen only; mixed cross-grain and separate axial tie are not combined, and this ratio is not a DCR or acceptance",
            })

        # Candidate E.2 net section is source-mapped only for the spine X-bore
        # plane. This reuses the prior A12 component comparison, not a recovered
        # member internal force or post net-section claim.
        spine_force = summed_lateral[EXPECTED_MEMBERS[0]]
        spine_parallel = spine_force[2]
        net_demand_lbf = abs(spine_parallel) / N_PER_LBF
        net_screen = {
            "case_id": case_id,
            "load_factor": factor,
            "member_id": EXPECTED_MEMBERS[0],
            "section_plane": section_row["section_plane"],
            "candidate_net_area_mm2": float(section_row["candidate_net_area_mm2"]),
            "pinned_section_screen_net_area_mm2": float(section_row["candidate_net_area_mm2"]),
            "one_modeled_bore_diameter_mm": bore_mm,
            "proposed_grain_direction": "+Z",
            "signed_group_parallel_force_along_plus_Z_N": spine_parallel,
            "same_parallel_component_demand_N": abs(spine_parallel),
            "same_parallel_component_demand_lbf": net_demand_lbf,
            "base_reference_inputs": {"Ft_psi": BASE_FT_PSI, "Ft_adjusted_factors_applied": []},
            "base_unadjusted_net_tension_reference_lbf": net_reference_lbf,
            "base_unadjusted_net_tension_reference_N": net_reference_lbf * N_PER_LBF,
            "parallel_component_ratio_to_base_unadjusted_reference": net_demand_lbf / net_reference_lbf,
            "qualification": "candidate E.2 spine net-section reference only; not a recovered internal section force, adjustment incomplete, post net plane not source-mapped",
        }
        records.append({
            "case_id": case_id,
            "load_factor": factor,
            "physical_BG001_bolt_count": 2,
            "same_state_per_bolt_lateral_and_axial_actions": bolt_actions,
            "receiver_parallel_row_component_screens": member_results,
            "spine_candidate_net_section_component_screen": net_screen,
            "full_mixed_action_method_proven": False,
        })

    # Explicit A12 factor-one oracle against the previously source-reviewed
    # single-state calculation: per-bolt actions, signed member group vectors,
    # ties, row geometry/references/ratios and the spine E.2 component.
    a12 = next(row for row in records if row["case_id"] == "a12-rear" and row["load_factor"] == 1.0)
    old_group = prior["bg001_group_resultants"]
    for member, key in ((EXPECTED_MEMBERS[0], "lateral_plane_force_on_spine_xyz_N"),
                        (EXPECTED_MEMBERS[1], "lateral_plane_force_on_post_xyz_N")):
        for actual, expected in zip(
            next(row for row in a12["receiver_parallel_row_component_screens"] if row["member_id"] == member)["signed_group_lateral_force_xyz_N"],
            old_group[key], strict=True,
        ):
            require(close(float(actual), float(expected), atol=1e-6), f"A12 group action oracle mismatch: {member}")
    for member, key in ((EXPECTED_MEMBERS[0], "separate_axial_outer_seat_tie_resultant_on_spine_xyz_N"),
                        (EXPECTED_MEMBERS[1], "separate_axial_outer_seat_tie_resultant_on_post_xyz_N")):
        actual = next(row for row in a12["receiver_parallel_row_component_screens"] if row["member_id"] == member)["separate_group_axial_outer_seat_tie_force_xyz_N"]
        for value, expected in zip(actual, old_group[key], strict=True):
            require(close(float(value), float(expected), atol=1e-6), f"A12 axial tie oracle mismatch: {member}")
    old_per_bolt = {row["axis_id"]: row for row in old_group["per_bolt_lateral_actions"]}
    for action in a12["same_state_per_bolt_lateral_and_axial_actions"]:
        old = old_per_bolt[action["axis_id"]]
        for key in ("force_on_spine_xyz_N", "force_on_post_xyz_N"):
            for actual, expected in zip(action[key], old[key], strict=True):
                require(close(float(actual), float(expected), atol=1e-6),
                        f"A12 per-bolt action oracle mismatch: {action['axis_id']}/{key}")
    for member in EXPECTED_MEMBERS:
        now = next(row for row in a12["receiver_parallel_row_component_screens"] if row["member_id"] == member)
        old = prior_rows[member]
        for key_new, key_old in (
            ("signed_group_grain_parallel_force_along_plus_Z_N", "signed_group_parallel_force_along_plus_Z_N"),
            ("loaded_end_distance_mm", "loaded_end_distance_mm"),
            ("row_pitch_mm", "row_pitch_mm"),
            ("critical_spacing_min_end_or_pitch_mm", "critical_spacing_mm"),
            ("base_unadjusted_row_reference_lbf", "base_unadjusted_row_reference_lbf"),
            ("parallel_component_ratio_to_base_unadjusted_reference", "component_ratio_to_base_unadjusted_reference"),
        ):
            require(close(float(now[key_new]), float(old[key_old]), atol=1e-6),
                    f"A12 row screen oracle mismatch: {member}/{key_new}")
    net_old = prior["spine_candidate_net_section_reference"]
    net_now = a12["spine_candidate_net_section_component_screen"]
    for key_new, key_old in (
        ("candidate_net_area_mm2", "candidate_net_area_mm2"),
        ("base_unadjusted_net_tension_reference_lbf", "base_unadjusted_net_tension_reference_lbf"),
        ("parallel_component_ratio_to_base_unadjusted_reference", "component_ratio_to_base_unadjusted_reference"),
    ):
        require(close(float(net_now[key_new]), float(net_old[key_old]), atol=1e-6),
                f"A12 E.2 net screen oracle mismatch: {key_new}")

    factor_one = [row for row in records if close(float(row["load_factor"]), 1.0)]
    row_screens = [item for row in records for item in row["receiver_parallel_row_component_screens"]]
    net_screens = [row["spine_candidate_net_section_component_screen"] for row in records]
    max_row = max(row_screens, key=lambda row: row["parallel_component_ratio_to_base_unadjusted_reference"])
    max_net = max(net_screens, key=lambda row: row["parallel_component_ratio_to_base_unadjusted_reference"])

    observed[HERE.joinpath("produce.py").relative_to(ROOT).as_posix()] = sha256(HERE / "produce.py")
    checks_document = {
        "direct_source_hashes_match": True,
        "three_case_42_row_source_packet_replays_read_only": True,
        "three_case_packet_contains_21_authenticated_states": True,
        "all_42_lateral_action_pairs_and_separate_ties_are_closed_by_source": True,
        "both_receivers_proposed_grain_plus_Z_and_bolt_axis_normality_confirmed_by_source": True,
        "finished_profile_terminal_rays_and_prior_A12_geometry_reconcile": True,
        "all_21_states_have_both_receiver_group_parallel_components": True,
        "all_mixed_crossgrain_actions_and_separate_axial_ties_retained": True,
        "all_21_two_row_E3_references_recomputed_with_Fv_180_no_adjustments": True,
        "all_21_spine_E2_candidate_net_references_recomputed_with_Ft_575_no_adjustments": True,
        "A12_factor_one_per_bolt_actions_group_vectors_ties_and_E3_E2_values_reproduce_prior_packet": True,
        "no_Cvr_applied": True,
        "no_combined_mixed_action_ratio_or_acceptance_established": True,
    }

    result = {
        "schema": "current_bg001_appendix_e_parallel_row_three_case_screen/v1",
        "status": "CONDITIONAL_DIRECTIONAL_COMPONENT_SCREEN_ONLY",
        "mechanical_acceptance": False,
        "candidate": source["candidate"],
        "geometry_revision_id": source["geometry_revision_id"],
        "source_state_inventory": {
            "cases": list(EXPECTED_CASES),
            "load_factors": list(EXPECTED_FACTORS),
            "authenticated_same_case_load_factor_states": len(records),
            "physical_BG001_bolts_per_state": 2,
            "lateral_receiver_actions": len(records) * 2 * 2,
        },
        "method_and_source_basis": {
            "standard": "NDS-2024 Appendix E, E.1-E.3 and E.6; source-reused method only",
            "appendix_pdf_url": "https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf",
            "appendix_pdf_sha256": "99b0a54e7133b3cf6dd156d8fe864c1717c951487bf5baa99c34da9a68a6bbb7",
            "appendix_printed_pages": [174, 175],
            "appendix_pdf_pages_zero_based": [8, 9],
            "appendix_E1_condition": "group loaded parallel to grain; the actual BG001 actions also carry substantial cross-grain components and separate axial ties, so full-condition applicability is unproven",
            "screened_demand": "signed receiver group force projected on proposed +Z grain; cross-grain lateral vectors and outer-seat axial ties stay explicitly separate",
            "E3_reference": "two-fastener single row, two shear lines; n=2, thickness 38.1 mm, pitch 42.05 mm, s_critical=min(loaded-end distance,pitch)",
            "E2_reference": "candidate spine XY net section through one modeled 7.5 mm X-bore; demand is the same signed-group grain-parallel component magnitude, not a recovered internal section force",
            "material_scenario": "conditional dry DF-L No. 2 base values only; Fv=180 psi and Ft=575 psi",
            "adjustments": "no NDS adjustment factors applied; adjusted Fv prime/Ft prime remain unresolved",
            "cvr_scope_review": prior["standard_source"]["cvr_scope_review"],
            "Cvr": False,
            "physical_stock_or_hardware_observed": False,
        },
        "conditional_geometry": {
            "proposed_grain_global_xyz": {member: [0.0, 0.0, 1.0] for member in EXPECTED_MEMBERS},
            "bolt_axis": "global X; lateral actions are bolt-normal in Y-Z",
            "finished_profile_source": geometry,
            "row_pitch_mm": pitch_mm,
            "member_thickness_along_bolt_axis_mm": thickness_mm,
            "member_width_mm": width_mm,
            "two_bolts_per_row": 2,
            "candidate_spine_net_section": {
                "source_screen": SECTION_REL.as_posix(),
                "plane": section_row["section_plane"],
                "candidate_area_mm2": float(section_row["candidate_net_area_mm2"]),
                "one_modeled_bore_diameter_mm": bore_mm,
                "post_net_section_mapped": False,
            },
            "geometry_claim_boundary": "finished modeled CAD inputs only; actual stock, cuts, holes and continuous-profile extrema not inspected",
        },
        "method_applicability": {
            "conditional_parallel_component_arithmetic_reused": True,
            "full_E1_parallel_only_condition_established": False,
            "reason": "At the bolt planes the group carries cross-grain actions, and each physical bolt also has a separate axial outer-seat tie. This packet reports components and conditional references only; it does not define a mixed-action interaction or infer cancellation as a splitting check.",
            "row_reference_is_not_a_group_acceptance": True,
            "net_reference_is_not_a_recovered_internal_force": True,
            "capacities_not_summed_or_transferred": True,
        },
        "records_by_same_case_load_state": records,
        "factor_one_three_case_summary": [
            {
                "case_id": state["case_id"],
                "receivers": [
                    {
                        "member_id": row["member_id"],
                        "signed_parallel_group_force_N": row["signed_group_grain_parallel_force_along_plus_Z_N"],
                        "parallel_demand_N": row["parallel_component_demand_N"],
                        "group_crossgrain_vector_xyz_N": row["group_cross_grain_force_xyz_N"],
                        "separate_group_axial_tie_vector_xyz_N": row["separate_group_axial_outer_seat_tie_force_xyz_N"],
                        "row_reference_N_unadjusted": row["base_unadjusted_row_reference_N"],
                        "parallel_component_reference_ratio": row["parallel_component_ratio_to_base_unadjusted_reference"],
                    }
                    for row in state["receiver_parallel_row_component_screens"]
                ],
                "spine_candidate_net_reference_N_unadjusted": state["spine_candidate_net_section_component_screen"]["base_unadjusted_net_tension_reference_N"],
                "spine_parallel_component_net_reference_ratio": state["spine_candidate_net_section_component_screen"]["parallel_component_ratio_to_base_unadjusted_reference"],
                "mixed_action_combination": "not performed",
            }
            for state in factor_one
        ],
        "envelope_summaries": {
            "largest_receiver_row_parallel_component_ratio": {
                "case_id": max_row["case_id"],
                "load_factor": max_row["load_factor"],
                "member_id": max_row["member_id"],
                "ratio": max_row["parallel_component_ratio_to_base_unadjusted_reference"],
                "classification": "unadjusted parallel-component/reference ratio only; not a DCR",
            },
            "largest_spine_net_parallel_component_ratio": {
                "case_id": max_net["case_id"],
                "load_factor": max_net["load_factor"],
                "ratio": max_net["parallel_component_ratio_to_base_unadjusted_reference"],
                "classification": "candidate unadjusted E.2 reference ratio only; not an internal section force or DCR",
            },
        },
        "unresolved_checks": [
            "The full Appendix E parallel-only loading condition is not established for BG001's mixed lateral actions and separate axial ties; no mixed-action interaction is defined here.",
            "Applicable adjusted Fv prime and Ft prime with actual wood species/grade, service conditions, and all Chapter 4 factors; no Cvr factor is imported.",
            "Mixed cross-grain and axial/tie interaction, splitting/tension-perpendicular, row/group tear-out under the actual mixed action, member stress, and complete load transfer.",
            "Post net-section plane/cuts and full member section actions across the corner path remain outside this source mapping.",
            "Actual stock, bore, cuts, grain, moisture, and delivered bolt/thread placement are not inspected.",
        ],
        "checks": checks_document,
        "source_sha256": dict(sorted(observed.items())),
        "combined_mixed_action_ratio_established": False,
        "adjusted_design_DCR_established": False,
        "Cvr_applied": False,
    }
    pins = {
        "schema": "current_bg001_appendix_e_parallel_row_three_case_source_pins/v1",
        "local_sha256": dict(sorted(observed.items())),
        "external_primary_source": {
            "standard": "ANSI/AWC NDS-2024 Appendix E",
            "title": "AWC NDS-2024 with Commentary, Appendix E",
            "url": "https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf",
            "sha256": "99b0a54e7133b3cf6dd156d8fe864c1717c951487bf5baa99c34da9a68a6bbb7",
            "printed_pages": [174, 175],
            "use": "Reuse of the prior packet's E.1-E.3/E.6 conditional one-row and candidate net-section component method; no mixed-action rule or capacity acceptance added.",
        },
        "errata_scope_source": prior["standard_source"]["cvr_scope_review"],
        "method_reuse": {
            "prior_A12_packet": PRIOR.relative_to(ROOT).as_posix(),
            "prior_A12_screen_sha256": INPUTS["prior_a12_screen"][1],
            "prior_A12_factor_one_oracle_checked": True,
            "Fv_base_psi": BASE_FV_PSI,
            "Ft_base_psi": BASE_FT_PSI,
            "Cvr_applied": False,
        },
        "scope": "All 21 authenticated rear-case states for BG001 only; signed grain-parallel component ratios, cross-grain actions and axial outer-seat ties remain separate; no combined pass or design DCR.",
    }
    return result, pins


def serialize(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result, pins = build()
    expected = {OUTPUT: serialize(result), PINS_OUTPUT: serialize(pins)}
    if args.write:
        for path, content in expected.items():
            path.write_text(content, encoding="utf-8")
        print("wrote 21 BG001 rear-state parallel-component records; mixed action remains separate")
    else:
        for path, content in expected.items():
            require(path.is_file() and path.read_text(encoding="utf-8") == content,
                    f"output differs from deterministic replay: {path}")
        print("verified 21 states, 42 bolt actions, row/net references, mixed-load separation, and A12 oracle")


if __name__ == "__main__":
    main()
