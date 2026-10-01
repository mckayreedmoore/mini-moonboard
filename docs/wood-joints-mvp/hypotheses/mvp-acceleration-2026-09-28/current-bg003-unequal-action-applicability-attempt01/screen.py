#!/usr/bin/env python3
"""Reproduce BG003 unequal-plane demand and outer-member Mode-Is screens.

Read-only arithmetic on a pinned current corner demand export. This does not
solve a model, qualify actual materials/bolts, combine plane capacities, or
accept the connection.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))

from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi


PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
DEMAND_PATH = PACKET / "current-corner-native-demand-export-attempt03/corner-demand-report.json"
SYMMETRIC_REFERENCE_PATH = PACKET / "current-knee-three-member-transfer-attempt01/calculation.json"
FRAME_GRAIN_PATH = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json"
BLOCK_GRAIN_PATH = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/material-frame-map.json"
NDS_HELPER_PATH = ROOT / "mini_moonboard/nds_2024_multi_member_bolt_yield.py"
FE_HELPER_PATH = ROOT / "mini_moonboard/bolted_timber_checks.py"

EXPECTED_SHA256 = {
    "corner_demand_report": "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    "symmetric_reference_calculation": "fb7fba30fdcdabf44c90a5ac7cfe167b6a9f659af8543a8070066f15ad45c5b1",
    "frame_grain_map": "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409",
    "block_grain_map": "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480",
    "nds_2024_helper": "575d7de88d5f138412fef633ef946bccba884c1953b67e8d9211fc028d74ab89",
    "dfl_fe_helper": "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13",
}
N_PER_LBF = 4.4482216152605
MODE_ID = "NDS-2024 single-shear Mode Is component reference"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def norm(vector: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def unit(vector: list[float]) -> list[float]:
    length = norm(vector)
    if length <= 0:
        raise ValueError("grain or force vector has zero length")
    return [value / length for value in vector]


def unsigned_axis_angle_degrees(vector: list[float], axis: list[float]) -> float:
    """Acute angle between lateral action and sign-equivalent grain axis."""
    v = unit(vector)
    a = unit(axis)
    cosine = min(1.0, max(0.0, abs(sum(x * y for x, y in zip(v, a)))))
    return math.degrees(math.acos(cosine))


def member_action(action: dict[str, Any], member_id: str) -> list[float]:
    if action["first"] == member_id:
        return [float(x) for x in action["force_on_first_xyz_n"]]
    if action["second"] == member_id:
        return [float(x) for x in action["force_on_second_xyz_n"]]
    raise ValueError(f"{member_id} is not an endpoint of {action['source_connection_name']}")


def grain_by_member(frame_map: dict[str, Any], block_map: dict[str, Any]) -> dict[str, list[float]]:
    grains: dict[str, list[float]] = {}
    for member in frame_map["members"]:
        assignment = member["conditional_grain_assignment"]
        grains[member["member_id"]] = [float(x) for x in assignment["proposed_global_xyz"]]
    for member in block_map["members"]:
        assignment = member["conditional_grain_assignment"]
        grains[member["part_id"]] = [float(x) for x in assignment["grain_direction_global_xyz"]]
    return grains


def mode_is_component_lbf(*, diameter_in: float, side_length_in: float,
                           fe_side_psi: float, theta_max_degrees: float) -> tuple[float, float]:
    """Single-shear NDS Is term: Fe,s D ls / (4 Ktheta), D >= 1/4 in."""
    if diameter_in < 0.25:
        raise ValueError("this bounded calculation uses the NDS D >= 1/4 in reduction branch")
    k_theta = 1.0 + 0.25 * theta_max_degrees / 90.0
    reduction = 4.0 * k_theta
    return fe_side_psi * diameter_in * side_length_in / reduction, k_theta


def action_record(bolt: dict[str, Any], suffix: str) -> dict[str, Any]:
    matches = [a for a in bolt["actions"] if a["source_connection_name"].endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"expected one {suffix} action, got {len(matches)}")
    return matches[0]


def main() -> None:
    input_files = {
        "corner_demand_report": DEMAND_PATH,
        "symmetric_reference_calculation": SYMMETRIC_REFERENCE_PATH,
        "frame_grain_map": FRAME_GRAIN_PATH,
        "block_grain_map": BLOCK_GRAIN_PATH,
        "nds_2024_helper": NDS_HELPER_PATH,
        "dfl_fe_helper": FE_HELPER_PATH,
    }
    actual_hashes = {name: sha256(path) for name, path in input_files.items()}
    for name, expected in EXPECTED_SHA256.items():
        if actual_hashes[name] != expected:
            raise ValueError(f"pinned input changed: {name}: {actual_hashes[name]} != {expected}")

    report = load(DEMAND_PATH)
    old = load(SYMMETRIC_REFERENCE_PATH)
    frame_map = load(FRAME_GRAIN_PATH)
    block_map = load(BLOCK_GRAIN_PATH)
    if report.get("schema") != "current_corner_native_demand_report/v1":
        raise ValueError("unexpected corner report schema")
    if report.get("status") != "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY":
        raise ValueError("pinned corner demand report is not its pass status")
    if report.get("actual_case_demand_usable_for_conditional_joint_checks") is not True:
        raise ValueError("source report does not authorize conditional demand screening")
    if report.get("case_id") != "a12-rear" or report.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError("unexpected case or geometry revision")
    if old.get("group_id") != "BG003" or old.get("geometry_revision_id") != report["geometry_revision_id"]:
        raise ValueError("symmetric reference geometry is not the source BG003 revision")
    if old["conditional_scenario_inputs"]["standard"] != "ANSI/AWC NDS-2024":
        raise ValueError("unexpected reference edition")
    if old["modeled_geometry_inputs"]["nds_effective_double_shear_lengths"]["effective_side_bearing_length_each_in"] != 1.5:
        raise ValueError("expected the pinned 1.5-in minimum side-bearing length")

    final = report["increments"][-1]
    if final.get("time") != 1.0 or final.get("load_factor") != 1.0:
        raise ValueError("expected the final full-load accepted increment")
    if not final.get("all_five_corner_bodies_raw_and_interval_balance_passed"):
        raise ValueError("local five-body corner balance is not passed")
    groups = final["primary_physical_bolt_groups"]
    bolts = groups["BG003"]["bolts"]
    if len(bolts) != 2:
        raise ValueError("expected exactly two BG003 bolts")

    grains = grain_by_member(frame_map, block_map)
    spine = "knee_outer_left_spine"
    middle = "base_side_left"
    block = "knee_outer_left_inner_frame_block"
    if not all(key in grains for key in (spine, middle, block)):
        raise ValueError("pinned grain maps do not contain all three BG003 members")
    reference_grains = old["modeled_geometry_inputs"]["proposed_grain_vectors_global_xyz"]
    for member_id in (spine, middle, block):
        if any(abs(a - b) > 1e-12 for a, b in zip(grains[member_id], reference_grains[member_id])):
            raise ValueError(f"grain map differs from prior pinned BG003 scenario: {member_id}")

    scenario = old["conditional_scenario_inputs"]
    diameter_in = float(scenario["bolt_nominal_full_body_diameter_in"])
    specific_gravity = 0.50
    effective_side_length_in = float(old["modeled_geometry_inputs"]["nds_effective_double_shear_lengths"]["effective_side_bearing_length_each_in"])
    middle_length_in = float(old["modeled_geometry_inputs"]["nds_effective_double_shear_lengths"]["main_bearing_length_in"])
    bolt_axis = [float(x) for x in old["modeled_geometry_inputs"]["axis_direction_global_xyz"]]

    bolt_results: list[dict[str, Any]] = []
    all_plane_rows: list[dict[str, Any]] = []
    for bolt in bolts:
        suffixes = ("plane-37", "plane-38") if bolt["axis_id"].endswith("_1") else ("plane-39", "plane-40")
        outer_members = (spine, block)
        actions = [action_record(bolt, suffix) for suffix in suffixes]
        force_vectors = [member_action(action, outer) for action, outer in zip(actions, outer_members)]
        magnitudes = [norm(vector) for vector in force_vectors]
        if any(magnitude <= 0 for magnitude in magnitudes):
            raise ValueError("each physical plane action must be nonzero")
        for action, vector in zip(actions, force_vectors):
            axial = sum(x * y for x, y in zip(vector, unit(bolt_axis)))
            if abs(axial) > 1e-7:
                raise ValueError("BG003 lateral-plane action is not perpendicular to its bolt axis")

        dot = sum(x * y for x, y in zip(force_vectors[0], force_vectors[1]))
        vector_angle = math.degrees(math.acos(max(-1.0, min(1.0, dot / (magnitudes[0] * magnitudes[1])))))
        ratio = max(magnitudes) / min(magnitudes)
        middle_actions = [member_action(action, middle) for action in actions]
        middle_force = [sum(v[i] for v in middle_actions) for i in range(3)]
        reported_middle = bolt["physical_member_wrenches_at_axis_datum"][middle]
        if any(abs(a - b) > 2e-5 for a, b in zip(middle_force, reported_middle["force_xyz_n"])):
            raise ValueError("reconstructed middle-member plane action does not match the pinned wrench")

        plane_rows = []
        for action, outer, vector, middle_plane_action, suffix in zip(
            actions, outer_members, force_vectors, middle_actions, suffixes
        ):
            theta_side = unsigned_axis_angle_degrees(vector, grains[outer])
            theta_middle = unsigned_axis_angle_degrees(middle_plane_action, grains[middle])
            theta_max = max(theta_side, theta_middle)
            fe_side = dfl_dowel_bearing_psi(diameter_in, theta_side)
            reference_is, k_theta = mode_is_component_lbf(
                diameter_in=diameter_in,
                side_length_in=effective_side_length_in,
                fe_side_psi=fe_side,
                theta_max_degrees=theta_max,
            )
            demand_lbf = norm(vector) / N_PER_LBF
            row = {
                "source_plane": action["source_connection_name"],
                "outer_member": outer,
                "outer_action_xyz_N": vector,
                "middle_member_action_xyz_N": middle_plane_action,
                "outer_plane_demand_N": norm(vector),
                "outer_plane_demand_lbf": demand_lbf,
                "proposed_outer_grain_angle_deg": theta_side,
                "proposed_middle_grain_angle_deg": theta_middle,
                "nds_max_member_angle_for_reduction_deg": theta_max,
                "conditional_DF_L_specific_gravity": specific_gravity,
                "conditional_outer_Fe_theta_psi": fe_side,
                "mode_Is_reduction_K_theta": k_theta,
                "mode_Is_effective_side_length_in": effective_side_length_in,
                "mode_Is_reference_lbf": reference_is,
                "mode_Is_component_ratio": demand_lbf / reference_is,
                "comparison_scope": "outer-member embedment-mode component only; not full three-member capacity or pass",
            }
            plane_rows.append(row)
            all_plane_rows.append(row)

        bolt_results.append({
            "axis_id": bolt["axis_id"],
            "outer_plane_force_vectors_xyz_N": {
                actions[0]["source_connection_name"]: force_vectors[0],
                actions[1]["source_connection_name"]: force_vectors[1],
            },
            "outer_plane_resultants_N": magnitudes,
            "outer_plane_resultant_ratio_larger_to_smaller": ratio,
            "angle_between_outer_action_vectors_deg": vector_angle,
            "middle_member": middle,
            "middle_member_net_force_xyz_N_from_plane_actions": middle_force,
            "middle_member_net_lateral_resultant_N": norm(middle_force[1:]),
            "middle_member_wrench_at_axis_datum_from_pinned_report": reported_middle,
            "per_outer_plane_mode_Is_components": plane_rows,
            "symmetric_double_shear_action_condition_met": (
                math.isclose(magnitudes[0], magnitudes[1], rel_tol=1e-12, abs_tol=1e-12)
                and math.isclose(vector_angle, 0.0, abs_tol=1e-8)
            ),
        })

    max_ratio = max(row["mode_Is_component_ratio"] for row in all_plane_rows)
    output = {
        "schema": "current_bg003_unequal_action_applicability_screen/v1",
        "status": "PASS_CONDITIONAL_OUTER_MODE_IS_COMPONENT_SCREEN_NO_GROUP_CAPACITY",
        "scope": "One a12-rear full-load BG003 current corner response; NDS method applicability and outer-member embedment-mode component screen only.",
        "qualification": {
            "current_NDS_three_member_unequal_vector_rule_identified": False,
            "symmetric_double_shear_reference_applicable": False,
            "plane_capacities_summed": False,
            "bolt_capacities_summed": False,
            "full_joint_capacity_or_DCR_calculated": False,
            "acceptance_or_release": False,
            "native_solve_launched": False,
            "geometry_or_model_changed": False,
        },
        "method_applicability": {
            "NDS_2024_12_3_1_scope": "single shear and symmetric double shear; the three-member double-shear yield-mode route is not a rule for unequal non-collinear outer actions",
            "NDS_2024_12_3_5_4_scope": "shorter side bearing length applies to both side members for unequal-length double-shear geometry; it does not solve unequal demand vectors",
            "NDS_2024_12_3_8_scope": "four or more members; not the three-member BG003 stack",
            "historical_NDS_2018_12_3_8": "an older asymmetric three-member provision used shorter side bearing length/minimum diameter; its official commentary states that it assumes equivalent loads to both side members and that other distributions may need more complex analysis. This is historical context, not the 2024 design basis.",
            "result": "No current source-supported complete NDS lateral-yield method was found for BG003's measured unequal, non-collinear plane actions. A detailed coupled bearing/dowel model would need a validated method and material/fastener inputs; no independent-plane or equal-action shortcut is adopted.",
        },
        "conditional_inputs": {
            "geometry_revision_id": report["geometry_revision_id"],
            "case_id": report["case_id"],
            "full_load_factor": final["load_factor"],
            "bolt_nominal_diameter_in": diameter_in,
            "smooth_full_body_scenario": scenario["threaded"] is False,
            "DF_L_specific_gravity_scenario": specific_gravity,
            "effective_side_length_in_each_for_conservative_Mode_Is_component_screen": effective_side_length_in,
            "middle_member_bearing_length_in": middle_length_in,
            "proposed_grain_vectors_global_xyz": {member: grains[member] for member in (spine, middle, block)},
            "material_and_bolt_product_status": "conditional scenario only; delivered stock, grade, grain, product, thread interval, and Fyb are not verified",
            "Mode_Is_formula": "Z_Is = Fe,s(theta_s) * D * ell_s / (4*Ktheta), Ktheta=1+0.25*theta_max/90; only this single-shear outer-side bearing mode is screened. Use min side length 1.5 in for both outer members as a deliberately conservative component input.",
            "mode_Is_max_angle": "maximum of the proposed grain angles for the particular outer member and middle member at that plane",
            "mode_Is_reduction_source": "NDS-2024 Table 12.3.1B for D >= 1/4 in; Jan-2025 corrected small-D branch is not entered",
            "Fyb_used_for_reported_mode_Is": False,
        },
        "BG003_bolts": bolt_results,
        "necessary_component_screen_summary": {
            "screened_outer_plane_count": len(all_plane_rows),
            "maximum_outer_Mode_Is_component_ratio": max_ratio,
            "any_outer_Mode_Is_component_ratio_exceeds_1": any(row["mode_Is_component_ratio"] > 1.0 for row in all_plane_rows),
            "interpretation": "All four illustrative outer-member Mode Is component ratios are below 1.0. This is not sufficient for the coupled connection: no full double-shear capacity, main-member combined-bearing check, bolt-bending/interaction, group distribution, tension, brittle wood failure, adjustments, or acceptance is established.",
        },
        "source_pins": {
            "local_files": {
                name: {"path": str(path.relative_to(ROOT)), "sha256": actual_hashes[name]}
                for name, path in input_files.items()
            },
            "NDS_2024_official_chapter_12": {
                "url": "https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf",
                "sha256": "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a",
                "locator": "§§12.3.1, 12.3.5.4, 12.3.8; Table 12.3.1A and Table 12.3.1B",
                "source_status": "official AWC source pin recorded in prior current method packet; direct PDF was not locally included in this bounded packet",
            },
            "NDS_2024_consolidated_errata_2026-03-23": {
                "url": "https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf",
                "sha256": "b3f4f8b3b2e2ffa5eb618de9e1182614c329d9e4a135096667364dc9a8e473c0",
                "relevance": "checked; p. 6 correction concerns the 0.17 < D < 0.25 in KD expression, while this component uses D=0.25 in and the 4Ktheta row",
            },
            "NDS_2024_official_standard_page": "https://awc.org/resources/2024-nds/",
            "NDS_2018_official_chapter_12_historical_only": "https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf",
            "NDS_2018_official_commentary_historical_only": "https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf",
        },
    }
    (HERE / "screen.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(f"wrote {HERE / 'screen.json'}")


if __name__ == "__main__":
    main()
