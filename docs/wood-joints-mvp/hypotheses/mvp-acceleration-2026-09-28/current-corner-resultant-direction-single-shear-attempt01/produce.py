#!/usr/bin/env python3
"""Produce four source-pinned, actual-resultant-direction bolt references.

This conditional arithmetic screen uses the accepted a12-rear corner demand
report and existing NDS/TR12 single-shear helpers. It does not qualify a joint
or treat a demand/reference ratio as a design pass.
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
HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / ".git").exists())
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
EVAL = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
DEMAND = BASE / "current-corner-native-demand-export-attempt03/corner-demand-report.json"
RESPONSE = BASE / "current-springa-selected-floor-a12-rear-attempt03/response.json"
MODEL = BASE / "current-springa-selected-floor-a12-rear-attempt03/model.json"
PREVIOUS_DIRECTION_SCREEN = BASE / "current-corner-a12-conditional-resistance-screen-attempt01/screen.json"
BG001_REFERENCE_SCREEN = BASE / "current-knee-post-conditional-bolt-screen-attempt01/conditional-screen.json"
BG045_REFERENCE_SCREEN = BASE / "current-knee-header-endgrain-screen-attempt01/conditional-screen.json"
BOLT_GROUPS = BASE / "bolt-groups/bolt-groups.json"
TIMBER_GRAIN_MAP = EVAL / "current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json"
BLOCK_GRAIN_MAP = EVAL / "current-block-material-frame-map-attempt02/material-frame-map.json"
NDS_PRODUCER = BASE / "nds-screen/produce.py"
NDS_SCENARIOS = BASE / "nds-screen/single-bolt-scenarios.json"
TR12_HELPER = ROOT / "fea/dowel_yield.py"
FE_HELPER = ROOT / "mini_moonboard/bolted_timber_checks.py"
OUTPUT = HERE / "resultant-direction-screen.json"
N_PER_LBF = 4.4482216152605
MM_PER_IN = 25.4
EXPECTED = {
    "demand_report": "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    "response": "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274",
    "model": "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
    "previous_direction_screen": "ee247af7e2271e63dcf1f8d8b86ef5eeca203f3dec3e37c55f2f6a8addb1e5cb",
    "bg001_reference_screen": "adbedaceec692936dcd2b2393c04fc985c5590a1a5a557b74868cee94eb3175c",
    "bg045_reference_screen": "2c4e3cac2c1b951ccd99cff69c5678cc605651b752ff5f9f5cc5b2f7ee3eff28",
    "bolt_groups": "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4",
    "timber_grain_map": "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409",
    "block_grain_map": "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480",
    "nds_producer": "21d3b2b254b1ceb9a6cf777b98eb492b52f989cc019afa2209b92be3e4a3cdb0",
    "nds_scenarios": "130041246af11fc8e3568a7091f585d0d75581b2e1fbb3a3f4b97b750d68a7ea",
    "tr12_helper": "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    "fe_helper": "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13",
}
SOURCE_PATHS = {
    "demand_report": DEMAND,
    "response": RESPONSE,
    "model": MODEL,
    "previous_direction_screen": PREVIOUS_DIRECTION_SCREEN,
    "bg001_reference_screen": BG001_REFERENCE_SCREEN,
    "bg045_reference_screen": BG045_REFERENCE_SCREEN,
    "bolt_groups": BOLT_GROUPS,
    "timber_grain_map": TIMBER_GRAIN_MAP,
    "block_grain_map": BLOCK_GRAIN_MAP,
    "nds_producer": NDS_PRODUCER,
    "nds_scenarios": NDS_SCENARIOS,
    "tr12_helper": TR12_HELPER,
    "fe_helper": FE_HELPER,
}
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
EXPECTED_AXES = {
    "BG001": ("knee_outer_left_post_1", "knee_outer_left_post_2"),
    "BG045": ("knee_outer_left_inner_header_1", "knee_outer_left_inner_header_2"),
}
MEMBER_ROLES = {
    "BG001": {"main": "base_post_outer_left", "side": "knee_outer_left_spine"},
    "BG045": {"main": "knee_outer_left_inner_frame_block", "side": "base_header"},
}
GRAIN_SOURCE_FOR_MEMBER = {
    "base_post_outer_left": "current-frame-timber-material-frame-map-attempt01",
    "base_header": "current-frame-timber-material-frame-map-attempt01",
    "knee_outer_left_spine": "current-block-material-frame-map-attempt02",
    "knee_outer_left_inner_frame_block": "current-block-material-frame-map-attempt02",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def close(left: float, right: float, tol: float = 1.0e-8) -> bool:
    return math.isfinite(left) and math.isfinite(right) and abs(left - right) <= tol * max(1.0, abs(left), abs(right))


def norm(vector: list[float]) -> float:
    return math.sqrt(math.fsum(value * value for value in vector))


def unit(vector: list[float]) -> list[float]:
    magnitude = norm(vector)
    if not math.isfinite(magnitude) or magnitude <= 0.0:
        raise ValueError("finite nonzero vector required")
    return [value / magnitude for value in vector]


def vector_close(left: list[float], right: list[float], tol: float = 1.0e-8) -> bool:
    return len(left) == len(right) and all(close(float(a), float(b), tol) for a, b in zip(left, right, strict=True))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"source module not importable: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def action_for(bolt: dict[str, Any], role: str) -> dict[str, Any]:
    matches = [row for row in bolt["actions"] if row.get("role") == role]
    if len(matches) != 1:
        raise ValueError(f"{bolt.get('axis_id')}: expected one {role} action")
    return matches[0]


def force_on(action: dict[str, Any], member: str) -> list[float]:
    if action["first"] == member:
        return [float(value) for value in action["force_on_first_xyz_n"]]
    if action["second"] == member:
        return [float(value) for value in action["force_on_second_xyz_n"]]
    raise ValueError(f"{member} is not an endpoint of {action.get('source_connection_name')}")


def angle_to_grain_deg(force: list[float], grain: list[float]) -> float:
    force_unit = unit(force)
    grain_unit = unit(grain)
    cosine = abs(math.fsum(a * b for a, b in zip(force_unit, grain_unit, strict=True)))
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def grain_maps(frame_map: dict[str, Any], block_map: dict[str, Any]) -> dict[str, list[float]]:
    frame_rows = {row["member_id"]: row for row in frame_map["members"]}
    block_rows = {row["part_id"]: row for row in block_map["members"]}
    result = {
        member: [float(value) for value in frame_rows[member]["conditional_grain_assignment"]["proposed_global_xyz"]]
        for member in ("base_post_outer_left", "base_header")
    }
    result.update({
        member: [float(value) for value in block_rows[member]["conditional_grain_assignment"]["grain_direction_global_xyz"]]
        for member in ("knee_outer_left_spine", "knee_outer_left_inner_frame_block")
    })
    return {member: unit(vector) for member, vector in result.items()}


def validate_and_load_sources() -> dict[str, Any]:
    observed_hashes: dict[str, str] = {}
    failed_hashes = []
    for name, path in SOURCE_PATHS.items():
        if not path.is_file():
            observed_hashes[name] = "missing"
            failed_hashes.append(name)
            continue
        observed_hashes[name] = sha256(path)
        if observed_hashes[name] != EXPECTED[name]:
            failed_hashes.append(name)
    if failed_hashes:
        raise ValueError("pinned source hash mismatch: " + ", ".join(failed_hashes))

    report = load_json(DEMAND)
    response = load_json(RESPONSE)
    model = load_json(MODEL)
    prior = load_json(PREVIOUS_DIRECTION_SCREEN)
    bg001_source = load_json(BG001_REFERENCE_SCREEN)
    bg045_source = load_json(BG045_REFERENCE_SCREEN)
    geometry = load_json(BOLT_GROUPS)
    frame_map = load_json(TIMBER_GRAIN_MAP)
    block_map = load_json(BLOCK_GRAIN_MAP)
    nds_scenarios = load_json(NDS_SCENARIOS)

    gates: dict[str, bool] = {
        "report_is_pinned_conditional_corner_demand_pass": (
            report.get("schema") == "current_corner_native_demand_report/v1"
            and report.get("status") == "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY"
            and report.get("actual_case_demand_usable_for_conditional_joint_checks") is True
        ),
        "report_binds_a12_rear_response_and_model": (
            report.get("case_id") == "a12-rear"
            and report.get("authenticated_source_case", {}).get("case_id") == "a12-rear"
            and report.get("authenticated_source_case", {}).get("response_audit_json_sha256") == EXPECTED["response"]
            and report.get("authenticated_source_case", {}).get("input_model_json_sha256") == EXPECTED["model"]
        ),
        "accepted_final_load_factor_one_and_all_root_gates": (
            len(report.get("increments", [])) == 7
            and report["increments"][-1].get("load_factor") == 1.0
            and all(value is True for value in report.get("response_audit_root_gates", {}).values())
        ),
        "response_status_is_the_pinned_physical_audit_only": (
            response.get("status") == "PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY"
            and response.get("case_id") == "a12-rear"
            and response.get("qualified_for_design") is False
            and response.get("mechanical_acceptance") is False
        ),
        "model_case_and_revision_match_conditional_screens": (
            model.get("candidate") == "compact-floor-flush-wood-joints-development"
            and model.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1"
            and report.get("geometry_revision_id") == model.get("geometry_revision_id")
        ),
        "prior_a12_directional_screen_is_nonacceptance": (
            prior.get("status") == "PASS_SOURCE_BOUND_CONDITIONAL_COMPARABILITY_SCREEN_ONLY"
            and prior.get("mechanical_acceptance") is False
            and prior.get("design_qualification") is False
        ),
        "nds_scenario_preserves_endpoint_values_and_helper_pin": (
            nds_scenarios.get("inputs", {}).get("bolt_bending_yield_psi") == 45000
            and nds_scenarios.get("inputs", {}).get("wood_specific_gravity_scenario") == 0.5
            and nds_scenarios.get("sources", {}).get("helper", {}).get("sha256") == EXPECTED["tr12_helper"]
        ),
        "pinned_grain_map_statuses_are_proposals_not_stock_observations": (
            frame_map.get("status") == "conditional_source_bound_current_timber_grain_map_geometry_crosschecked"
            and block_map.get("status") == "conditional_source_bound_candidate_block_frames_geometry_only"
            and frame_map.get("release") is not True
            and block_map.get("release") is not True
        ),
    }
    failures = [name for name, passed in gates.items() if not passed]
    if failures:
        raise ValueError("conditional input gate failed: " + ", ".join(failures))

    grain_by_member = grain_maps(frame_map, block_map)
    geometry_grains: dict[str, dict[str, dict[str, Any]]] = {"BG001": {}, "BG045": {}}
    for row in geometry["candidate_axis_receiver_grain_angles"]:
        group = row.get("group_id")
        if group not in geometry_grains:
            continue
        axis = row["axis_id"]
        member = row["receiver_member_id"]
        if member in geometry_grains[group].setdefault(axis, {}):
            raise ValueError(f"duplicate source grain row for {group}/{axis}/{member}")
        direct = grain_by_member[member]
        if not vector_close(list(row["source_proposed_grain_unit_global_xyz"]), direct):
            raise ValueError(f"bolt-group grain row does not match pinned source grain map: {member}")
        if row.get("grain_map_source") != GRAIN_SOURCE_FOR_MEMBER[member]:
            raise ValueError(f"unexpected grain map source for {member}")
        geometry_grains[group][axis][member] = row

    for group, axes in EXPECTED_AXES.items():
        if set(geometry_grains[group]) != set(axes):
            raise ValueError(f"unexpected source grain axes for {group}")
        for axis in axes:
            if set(geometry_grains[group][axis]) != set(MEMBER_ROLES[group].values()):
                raise ValueError(f"incomplete two-member grain map for {group}/{axis}")

    bg001_basis = bg001_source["conditional_single_bolt_basis"]
    if (
        not close(bg001_basis["diameter_in"], 0.25)
        or bg001_basis["bolt_bending_yield_psi_assumption"] != 45000
        or bg001_basis["interface_gap_in"] != 0
        or not close(bg001_basis["fe_parallel_to_grain_psi_assumption"], 5600)
        or not close(bg001_basis["fe_perpendicular_to_grain_psi_assumption"], 4450)
        or not close(bg001_basis["main_and_side_bearing_lengths_in"][0], 1.5)
        or not close(bg001_basis["main_and_side_bearing_lengths_in"][1], 1.5)
        or "full-body smooth" not in bg001_basis["shank_assumption"]
    ):
        raise ValueError("BG001 pinned shank, length, gap, Fyb, or Fe endpoint assumptions changed")

    bg045_roles = bg045_source["role_scenario"]
    if (
        bg045_roles.get("main") != MEMBER_ROLES["BG045"]["main"]
        or bg045_roles.get("side") != MEMBER_ROLES["BG045"]["side"]
        or bg045_source.get("group_id") != "BG045"
        or bg045_source.get("mechanical_acceptance") is not False
        or not any("45000 psi" in item for item in bg045_source.get("assumptions", []))
        or not any("1/4 inch smooth shank" in item for item in bg045_source.get("assumptions", []))
        or not any("Zero gap" in item for item in bg045_source.get("assumptions", []))
        or any(not close(row.get("Ceg", -1), 0.67) for row in bg045_source.get("rows", []))
    ):
        raise ValueError("BG045 pinned end-grain scenario or Ceg factor changed")
    lengths_045 = {row["axis_id"]: row for row in bg045_source["lengths"]}
    if set(lengths_045) != set(EXPECTED_AXES["BG045"]) or any(
        not close(row["main_mm"], 139.0) or not close(row["side_mm"], 38.1)
        for row in lengths_045.values()
    ):
        raise ValueError("BG045 pinned receiver bearing lengths changed")

    endpoint_rows = {(row["main_load_to_grain_degrees"], row["side_load_to_grain_degrees"]): row
                     for row in nds_scenarios["rows"]}
    if (
        endpoint_rows[(0, 0)]["main_bearing_psi"] != 5600
        or endpoint_rows[(90, 90)]["main_bearing_psi"] != 4450
        or endpoint_rows[(0, 0)]["side_bearing_psi"] != 5600
        or endpoint_rows[(90, 90)]["side_bearing_psi"] != 4450
    ):
        raise ValueError("pinned single-bolt scenario endpoints are not 5600/4450 psi")

    return {
        "observed_hashes": observed_hashes,
        "gates": gates,
        "report": report,
        "response": response,
        "model": model,
        "prior_screen": prior,
        "bg001_source": bg001_source,
        "bg045_source": bg045_source,
        "geometry": geometry,
        "geometry_grains": geometry_grains,
        "grain_by_member": grain_by_member,
        "nds_scenarios": nds_scenarios,
    }


def produce() -> dict[str, Any]:
    sources = validate_and_load_sources()
    nds = load_module("pinned_nds_single_bolt_producer", NDS_PRODUCER)
    fe_helper = load_module("pinned_dfl_dowel_bearing_helper", FE_HELPER)
    report = sources["report"]
    final = report["increments"][-1]
    prior = sources["prior_screen"]["demand_and_reference_results"]
    bg001_basis = sources["bg001_source"]["conditional_single_bolt_basis"]
    endpoint_parallel = float(bg001_basis["fe_parallel_to_grain_psi_assumption"])
    endpoint_perpendicular = float(bg001_basis["fe_perpendicular_to_grain_psi_assumption"])
    diameter_in = float(bg001_basis["diameter_in"])
    fyb_psi = float(bg001_basis["bolt_bending_yield_psi_assumption"])
    fe_at_zero = float(fe_helper.dfl_dowel_bearing_psi(diameter_in, 0.0))
    fe_at_ninety = float(fe_helper.dfl_dowel_bearing_psi(diameter_in, 90.0))
    if not close(fe_at_zero, endpoint_parallel) or not close(fe_at_ninety, endpoint_perpendicular):
        raise ValueError("angle interpolation helper does not preserve existing rounded Fe endpoints")

    group_results: dict[str, list[dict[str, Any]]] = {"BG001": [], "BG045": []}
    axes_by_group = final["primary_physical_bolt_groups"]
    for group in ("BG001", "BG045"):
        roles = MEMBER_ROLES[group]
        main_member, side_member = roles["main"], roles["side"]
        bolts = axes_by_group[group]["bolts"]
        if {bolt["axis_id"] for bolt in bolts} != set(EXPECTED_AXES[group]):
            raise ValueError(f"accepted report has unexpected bolts in {group}")
        historical_rows = {
            row["axis_id"]: row
            for row in prior["BG001_two_post_bolts" if group == "BG001" else "BG045_two_header_bolts"]
        }
        for bolt in bolts:
            axis_id = bolt["axis_id"]
            plane = action_for(bolt, "candidate_bolt_lateral_plane")
            tie = action_for(bolt, "physical_bolt_outer_seat_tension")
            force_by_member = {
                main_member: force_on(plane, main_member),
                side_member: force_on(plane, side_member),
            }
            magnitude_by_member = {member: norm(vector) for member, vector in force_by_member.items()}
            if not close(magnitude_by_member[main_member], magnitude_by_member[side_member]):
                raise ValueError(f"action/reaction resultant magnitudes differ for {axis_id}")
            if not vector_close(force_by_member[main_member], [-value for value in force_by_member[side_member]]):
                raise ValueError(f"action/reaction vectors do not close for {axis_id}")

            prior_row = historical_rows[axis_id]
            prior_key = (
                "physical_lateral_action_on_base_post_outer_left_xyz_N"
                if group == "BG001" else "physical_lateral_action_on_base_header_xyz_N"
            )
            prior_member = "base_post_outer_left" if group == "BG001" else "base_header"
            if not vector_close(force_by_member[prior_member], prior_row[prior_key]):
                raise ValueError(f"accepted vector differs from prior source-bound screen for {axis_id}")
            if not close(magnitude_by_member[main_member], prior_row["lateral_resultant_N"]):
                raise ValueError(f"resultant magnitude differs from prior source-bound screen for {axis_id}")

            tie_force_by_member = {
                main_member: force_on(tie, main_member),
                side_member: force_on(tie, side_member),
            }
            tie_magnitude = norm(tie_force_by_member[main_member])
            if not vector_close(tie_force_by_member[main_member], [-value for value in tie_force_by_member[side_member]]):
                raise ValueError(f"outer-seat tie action/reaction vectors do not close for {axis_id}")
            if not close(tie_magnitude, float(prior_row["outer_seat_tension_N"])):
                raise ValueError(f"outer-seat tie resultant differs from prior source-bound screen for {axis_id}")

            member_angles = {
                member: angle_to_grain_deg(force_by_member[member], sources["grain_by_member"][member])
                for member in (main_member, side_member)
            }
            member_fe = {
                member: float(fe_helper.dfl_dowel_bearing_psi(diameter_in, member_angles[member]))
                for member in (main_member, side_member)
            }
            theta_for_reduction = max(member_angles.values())

            if group == "BG001":
                basis = bg001_basis
                main_length_in, side_length_in = map(float, basis["main_and_side_bearing_lengths_in"])
                ceg = 1.0
                ceg_note = "not applied; BG001 is the existing two-member side-grain scenario"
            else:
                length_row = next(row for row in sources["bg045_source"]["lengths"] if row["axis_id"] == axis_id)
                main_length_in = float(length_row["main_mm"]) / MM_PER_IN
                side_length_in = float(length_row["side_mm"]) / MM_PER_IN
                ceg_rows = sources["bg045_source"]["rows"]
                ceg = float(ceg_rows[0]["Ceg"])
                ceg_note = "existing conditional main-member end-grain factor; applied once to the governing lateral reference"

            result = nds.calculate(
                diameter_in,
                main_length_in,
                side_length_in,
                member_fe[main_member],
                member_fe[side_member],
                theta_for_reduction,
            )
            references_lbf = {mode: float(result["reference_values_lbf"][mode]) for mode in MODES}
            yields_lbf = {mode: float(result["yield_values_lbf"][mode]) for mode in MODES}
            if set(references_lbf) != set(MODES) or set(yields_lbf) != set(MODES):
                raise ValueError("single-shear helper did not return all six lateral yield modes")
            governing_mode = min(references_lbf, key=references_lbf.get)
            if governing_mode != result["governing_mode"]:
                raise ValueError(f"governing-mode label mismatch for {axis_id}")
            ktheta = 1.0 + 0.25 * theta_for_reduction / 90.0
            direct_iv = (
                diameter_in**2 / (3.2 * ktheta)
                * math.sqrt(
                    2.0 * member_fe[main_member] * fyb_psi
                    / (3.0 * (1.0 + member_fe[main_member] / member_fe[side_member]))
                )
            )
            if not close(references_lbf["IV"], direct_iv, 1.0e-11):
                raise ValueError(f"independent closed-form mode IV check failed for {axis_id}")

            resultant_n = magnitude_by_member[main_member]
            reference_mode_n = {mode: references_lbf[mode] * N_PER_LBF for mode in MODES}
            per_mode_ratios = {
                mode: resultant_n / reference_mode_n[mode]
                for mode in MODES
            }
            governing_reference_n = reference_mode_n[governing_mode]
            ceg_only_governing_reference_n = governing_reference_n * ceg
            group_results[group].append({
                "axis_id": axis_id,
                "lateral_plane_connection": plane["source_connection_name"],
                "main_member": main_member,
                "side_member": side_member,
                "reported_lateral_action_on_main_xyz_N": force_by_member[main_member],
                "reported_lateral_action_on_side_xyz_N": force_by_member[side_member],
                "lateral_resultant_demand_N": resultant_n,
                "load_to_grain_angle_deg": member_angles,
                "source_proposed_grain_unit_global_xyz": {
                    member: sources["grain_by_member"][member]
                    for member in (main_member, side_member)
                },
                "grain_proposal_source": {
                    member: next(
                        row["grain_map_source"]
                        for row in sources["geometry_grains"][group][axis_id].values()
                        if row["receiver_member_id"] == member
                    )
                    for member in (main_member, side_member)
                },
                "bearing_basis": {
                    "material_scenario": "conditional DF-L No. 2, SG 0.50; actual wood and delivered grade unobserved",
                    "parallel_Fe_endpoint_psi": endpoint_parallel,
                    "perpendicular_Fe_endpoint_psi": endpoint_perpendicular,
                    "Fe_by_member_psi": member_fe,
                    "interpolation": "Pinned dfl_dowel_bearing_psi helper; NDS angle interpolation, with 0/90 degree outputs verified exactly against the existing rounded 5600/4450 psi endpoints.",
                },
                "single_shear_method_inputs": {
                    "diameter_full_body_smooth_shank_in": diameter_in,
                    "main_bearing_length_in": main_length_in,
                    "side_bearing_length_in": side_length_in,
                    "interface_gap_in": 0.0,
                    "bolt_bending_yield_psi": fyb_psi,
                    "member_angles_deg_for_reduction_theta_max": theta_for_reduction,
                    "theta_factor": ktheta,
                },
                "six_lateral_yield_modes": {
                    "yield_values_lbf": yields_lbf,
                    "unadjusted_reference_values_lbf": references_lbf,
                    "unadjusted_reference_values_N": reference_mode_n,
                    "resultant_demand_over_unadjusted_reference_by_mode": per_mode_ratios,
                },
                "governing_mode": governing_mode,
                "governing_unadjusted_reference_N": governing_reference_n,
                "Ceg_factor": ceg,
                "Ceg_applicability_and_use": ceg_note,
                "conditional_governing_reference_after_Ceg_only_N": ceg_only_governing_reference_n,
                "resultant_demand_over_governing_reference_after_Ceg_only": resultant_n / ceg_only_governing_reference_n,
                "outer_seat_axial_tie_action_on_main_xyz_N_out_of_scope": tie_force_by_member[main_member],
                "outer_seat_axial_tie_magnitude_N_out_of_scope": tie_magnitude,
                "independent_mode_IV_reference_lbf": direct_iv,
                "comparison_scope": "one reported lateral resultant against the conditional single-bolt reference for its actual proposed-grain direction; no component capacity sums or group capacity",
            })

    if any(len(rows) != 2 for rows in group_results.values()):
        raise ValueError("expected exactly four individual bolt results")
    all_results = [row for group in ("BG001", "BG045") for row in group_results[group]]
    if any(row["governing_mode"] != "IV" for row in all_results):
        raise ValueError("unexpected governing mode in the four bounded cases")

    previous_screen_hash = sources["observed_hashes"]["previous_direction_screen"]
    return {
        "schema": "current_corner_resultant_direction_single_shear_screen/v1",
        "status": "PASS_SOURCE_BOUND_CONDITIONAL_RESULTANT_DIRECTION_SCREEN_ONLY",
        "candidate": report["candidate"],
        "geometry_revision_id": report["geometry_revision_id"],
        "case_id": report["case_id"],
        "scope": "BG001 and BG045 only; four physical bolts; final accepted a12-rear load-factor-one lateral resultant vectors",
        "input_provenance": {
            "demand_report_path": str(DEMAND.relative_to(ROOT)),
            "demand_report_sha256": sources["observed_hashes"]["demand_report"],
            "response_sha256": sources["observed_hashes"]["response"],
            "source_model_sha256": sources["observed_hashes"]["model"],
            "final_time": report["increments"][-1]["time"],
            "final_load_factor": report["increments"][-1]["load_factor"],
            "previous_component_screen_sha256": previous_screen_hash,
            "previous_screen_vector_and_resultant_crosschecks_passed": True,
            "all_source_hashes_match": True,
            "source_sha256": {
                str(path.relative_to(ROOT)): sources["observed_hashes"][name]
                for name, path in SOURCE_PATHS.items()
            },
        },
        "method": {
            "single_shear_helper_path": str(NDS_PRODUCER.relative_to(ROOT)),
            "single_shear_helper_sha256": sources["observed_hashes"]["nds_producer"],
            "TR12_single_shear_helper_path": str(TR12_HELPER.relative_to(ROOT)),
            "TR12_single_shear_helper_sha256": sources["observed_hashes"]["tr12_helper"],
            "Fe_angle_helper_path": str(FE_HELPER.relative_to(ROOT)),
            "Fe_angle_helper_sha256": sources["observed_hashes"]["fe_helper"],
            "NDS_2024_chapter_12_source_identity": sources["nds_scenarios"]["sources"]["NDS_2024_chapter_12"],
            "material_endpoint_check": {
                "specific_gravity_scenario": 0.5,
                "parallel_psi": endpoint_parallel,
                "perpendicular_psi": endpoint_perpendicular,
                "helper_at_zero_degrees_psi": fe_at_zero,
                "helper_at_ninety_degrees_psi": fe_at_ninety,
                "existing_rounded_endpoints_preserved": True,
            },
            "direction_rule": "For each member separately, theta=acos(abs(unit_force dot unit_source_proposed_grain)); force/action-reaction signs do not change the unoriented grain-axis angle.",
            "two_member_reduction_angle_rule": "Use max(main-member angle, side-member angle) in the existing NDS theta reduction term; BG045 main end-grain member remains theta=90 degrees.",
            "comparison_rule": "Compare the scalar lateral resultant magnitude to each single-bolt lateral-mode reference for that resultant direction. Report per-mode ratios and the governing reference; do not sum axis-component references or bolt references.",
        },
        "results": group_results,
        "checks": {
            **sources["gates"],
            "four_reported_vectors_match_previous_screen": True,
            "all_four_action_reaction_pairs_close": True,
            "all_four_tie_action_reaction_and_magnitude_crosschecks_passed": True,
            "all_four_modes_reproduced_all_six_yield_modes": True,
            "independent_mode_IV_check_passed_for_all_four": True,
            "all_four_governing_mode_IV": True,
        },
        "limits": [
            "The DF-L No. 2, SG 0.50 and longitudinal grain directions are source-proposed conditional scenarios, not observations of delivered wood.",
            "The NDS reference assumes a smooth full-body 1/4-in bolt throughout each modeled bearing length, zero gap, and Fyb=45,000 psi; actual bolt, threads, holes and fit are unverified.",
            "The 5600/4450 psi material endpoints are unchanged. Intermediate Fe values use the pinned NDS angle interpolation at each member's resultant direction.",
            "BG045 Ceg=0.67 remains the existing conditional end-grain assumption and is applied once to the governing reference; no other adjustment factors are applied.",
            "Ratios compare individual lateral resultant demand to one conditional individual-bolt reference only; they are not design DCRs or joint passes.",
            "No axial bolt/washer resistance, bolt group action, load redistribution, splitting, row shear, tear-out, net section, or complete connection transfer is evaluated.",
            "No bolt capacities are summed across components, planes, or axes. BG003, all twelve original LEG/RUNNER arrangements, and all other cases are outside scope.",
            "No material/product qualification, mechanical acceptance, fabrication approval, floor qualification, or climbing release is established.",
        ],
        "mechanical_acceptance": False,
        "design_qualification": False,
        "native_solve_launched": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true", help="write the fresh result in this folder")
    modes.add_argument("--verify", action="store_true", help="compare recomputed JSON exactly with the saved result")
    args = parser.parse_args()
    result = produce()
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)}")
    else:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
            raise SystemExit("saved resultant-direction screen differs from recomputed output")
        print("verified four source-bound BG001/BG045 resultant-direction comparisons")


if __name__ == "__main__":
    main()
