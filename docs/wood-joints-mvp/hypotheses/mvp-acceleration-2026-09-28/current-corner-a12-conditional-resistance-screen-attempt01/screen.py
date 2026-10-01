#!/usr/bin/env python3
"""Reproduce the bounded conditional BG001/BG003/BG045 resistance screen.

This is an arithmetic/reproducibility script only. It does not run a solver,
change source mechanics, derive a new resistance equation, or qualify a joint.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
DEMAND_PATH = PACKET / "current-corner-native-demand-export-attempt03/corner-demand-report.json"
RESPONSE_PATH = PACKET / "current-springa-selected-floor-a12-rear-attempt03/response.json"
MODEL_PATH = PACKET / "current-springa-selected-floor-a12-rear-attempt03/model.json"
PARENT_ASSESSMENT_PATH = PACKET / "current-springa-selected-floor-a12-rear-attempt03/parent-terminal-assessment.json"
PARENT_BODY_PATH = PACKET / "current-springa-selected-floor-a12-rear-attempt03/parent-all-body-response-audit.json"

EXPECTED = {
    "demand_report": "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    "response": "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274",
    "model": "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
    "source_manifest": "9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a",
    "contract": "f09d341924b2aa4e50ad8ecea43e4fcd1a36d838c99ab4e0fb85712e7dfd6c74",
    "interface_map": "c5ce97cbe1fffbb18dfaf1a544fa9a300991b06056b21b37ba3e08b8a1c6aec8",
    "bg001_bolt": "adbedaceec692936dcd2b2393c04fc985c5590a1a5a557b74868cee94eb3175c",
    "bg001_group": "9ea64b4160d95ad97e3cdb745eb7799111e55392ffc099b28c8f17c25b469ba7",
    "bg003_three_member": "fb7fba30fdcdabf44c90a5ac7cfe167b6a9f659af8543a8070066f15ad45c5b1",
    "bg045_endgrain": "2c4e3cac2c1b951ccd99cff69c5678cc605651b752ff5f9f5cc5b2f7ee3eff28",
    "section_geometry": "22209a82b0bda6dfc5c140ccc4e481717e0e7c71d30a5827271c81ac71070564",
    "washer_seats": "67dda5964a9c2a864cdb5ee0e898bae3c9e6bea212e2eeb71d5b33f765481ef0",
}
SOURCE_FILES = {
    "bg001_bolt": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-post-conditional-bolt-screen-attempt01/conditional-screen.json",
    "bg001_group": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-post-group-factor-attempt01/conditional-group-factor.json",
    "bg003_three_member": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-three-member-transfer-attempt01/calculation.json",
    "bg045_endgrain": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-header-endgrain-screen-attempt01/conditional-screen.json",
    "section_geometry": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-local-wood-screen-attempt01/section-screen.json",
    "washer_seats": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-washer-seat-screen-attempt01/seat-screen.json",
}
N_PER_LBF = 4.4482216152605


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def close(a: float, b: float, tol: float = 1e-8) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def norm(vec: list[float]) -> float:
    return math.sqrt(sum(v * v for v in vec))


def action_for(bolt: dict, suffix: str) -> dict:
    matches = [a for a in bolt["actions"] if a["source_connection_name"].endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"expected one action ending {suffix!r}, got {len(matches)}")
    return matches[0]


def force_on(action: dict, member: str) -> list[float]:
    if action["first"] == member:
        return action["force_on_first_xyz_n"]
    if action["second"] == member:
        return action["force_on_second_xyz_n"]
    raise ValueError(f"{member!r} is not an endpoint of {action['source_connection_name']}")


def source_evidence(report: dict, key: str, root: Path) -> tuple[dict, str]:
    item = report["conditional_reference_evidence"][key]
    expected_key = {
        "BG001_individual_bolt": "bg001_bolt",
        "BG001_group_factor": "bg001_group",
        "BG003_two_three_member_bolts": "bg003_three_member",
        "BG045_endgrain": "bg045_endgrain",
        "geometry_only_splitting_and_net_section": "section_geometry",
        "washer_seats": "washer_seats",
    }[key]
    path = root / item["path"]
    actual = sha256(path)
    if item["sha256"] != EXPECTED[expected_key] or actual != EXPECTED[expected_key]:
        raise ValueError(f"source pin mismatch for {key}: report={item['sha256']} actual={actual}")
    return load(path), actual


def main() -> None:
    for name, path, expected in (
        ("demand_report", DEMAND_PATH, EXPECTED["demand_report"]),
        ("response", RESPONSE_PATH, EXPECTED["response"]),
        ("model", MODEL_PATH, EXPECTED["model"]),
    ):
        if sha256(path) != expected:
            raise ValueError(f"{name} changed: {sha256(path)} != {expected}")

    report = load(DEMAND_PATH)
    response = load(RESPONSE_PATH)
    model = load(MODEL_PATH)
    parent_assessment = load(PARENT_ASSESSMENT_PATH)
    parent_body = load(PARENT_BODY_PATH)
    if report["status"] != "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY":
        raise ValueError("corner demand report is not its expected pass status")
    if not report["actual_case_demand_usable_for_conditional_joint_checks"]:
        raise ValueError("source report does not permit conditional demand screening")
    if report["authenticated_source_case"]["case_id"] != "a12-rear":
        raise ValueError("unexpected source case")
    if report["authenticated_source_case"]["input_model_json_sha256"] != EXPECTED["model"]:
        raise ValueError("model hash is not bound by the demand report")
    if report["authenticated_source_case"]["response_audit_json_sha256"] != EXPECTED["response"]:
        raise ValueError("response hash is not bound by the demand report")
    if not all(report["response_audit_root_gates"].values()):
        raise ValueError("a corner response root gate is false")
    if response.get("schema") != "current_springa_selected_floor_physical_response_audit/v1":
        raise ValueError("unexpected selected-floor response schema")
    if model.get("schema") != "current_springa_selected_floor_input_model/v1":
        raise ValueError("unexpected selected-floor input schema")
    if parent_assessment["status"] != "PASS_CONDITIONAL_NUMERICAL_RESPONSE" or not parent_assessment["conditional_case_forces_usable"]:
        raise ValueError("parent terminal assessment does not bind usable conditional demands")
    if parent_body["status"] != "PASS_PARENT_ALL_BODY_RESPONSE_SUMS":
        raise ValueError("parent all-body assessment did not pass")
    if parent_body["source_model_sha256"] != EXPECTED["model"] or parent_body["source_response_sha256"] != EXPECTED["response"]:
        raise ValueError("parent body audit is bound to different source inputs")
    if len(report["increments"]) != 7 or len(parent_body["increments"]) != 7:
        raise ValueError("expected the seven accepted increments for this case")
    for inc, parent_inc in zip(report["increments"], parent_body["increments"]):
        if not all(inc["response_audit_gates"].values()):
            raise ValueError(f"response gate failure at time {inc['time']}")
        if not inc["all_five_corner_bodies_raw_and_interval_balance_passed"]:
            raise ValueError(f"five-body balance failure at time {inc['time']}")
        if parent_inc["body_count"] != 50 or not all(
            b["printed_resultants_passed"] and b["interval_resultants_passed"]
            for b in parent_inc["body_equilibrium"].values()
        ):
            raise ValueError(f"parent all-body balance failure at time {inc['time']}")
    final = report["increments"][-1]
    if final["time"] != 1.0 or final["load_factor"] != 1.0:
        raise ValueError("the final full-load increment is missing")
    if any(i["load_factor"] > final["load_factor"] for i in report["increments"]):
        raise ValueError("an increment exceeds the selected final load factor")

    refs = {}
    source_hashes = {}
    for key in report["conditional_reference_evidence"]:
        if key in ("BG001_individual_bolt", "BG001_group_factor", "BG003_two_three_member_bolts", "BG045_endgrain", "geometry_only_splitting_and_net_section", "washer_seats"):
            refs[key], source_hashes[key] = source_evidence(report, key, ROOT)

    bg001_scenarios = {
        x["case_id"]: x["reference_lateral_N"]
        for x in refs["BG001_individual_bolt"]["conditional_single_bolt_basis"]["scenarios"]
    }
    bg003_scenarios = refs["BG003_two_three_member_bolts"]["scenarios"]
    bg045_scenarios = {x["direction"]: x for x in refs["BG045_endgrain"]["rows"]}

    groups = final["primary_physical_bolt_groups"]
    results: dict[str, object] = {}

    post_rows = []
    for bolt in groups["BG001"]["bolts"]:
        tie = action_for(bolt, "/outer-seat-axial-tie")
        plane = next(a for a in bolt["actions"] if a["role"] == "candidate_bolt_lateral_plane")
        on_post = force_on(plane, "base_post_outer_left")
        ry = bg001_scenarios["global_y_lateral_load_perpendicular_to_proposed_grain"]
        rz = bg001_scenarios["global_z_lateral_load_parallel_to_proposed_grain"]
        post_rows.append({
            "axis_id": bolt["axis_id"],
            "plane_connection": plane["source_connection_name"],
            "physical_lateral_action_on_base_post_outer_left_xyz_N": on_post,
            "lateral_resultant_N": norm(on_post),
            "opposite_action_on_spine_xyz_N": force_on(plane, "knee_outer_left_spine"),
            "outer_seat_tension_N": norm(force_on(tie, tie["first"])),
            "conditional_single_bolt_references_unadjusted_N": {"global_Y": ry, "global_Z": rz},
            "component_to_reference_ratios": {"abs_Y_over_Y_reference": abs(on_post[1]) / ry, "abs_Z_over_Z_reference": abs(on_post[2]) / rz},
            "comparison_limit": "separate component/reference ratios only; no mixed-axis interaction, group resistance, bolt axial check, or acceptance",
        })

    three_rows = []
    for bolt in groups["BG003"]["bolts"]:
        tie = action_for(bolt, "/outer-seat-axial-tie")
        planes = [a for a in bolt["actions"] if a["role"] == "candidate_bolt_lateral_plane"]
        by_suffix = {a["source_connection_name"].rsplit("/", 1)[-1]: a for a in planes}
        if bolt["axis_id"].endswith("side_1"):
            action_spine, action_block = by_suffix["plane-37"], by_suffix["plane-38"]
        else:
            action_spine, action_block = by_suffix["plane-39"], by_suffix["plane-40"]
        on_spine = force_on(action_spine, "knee_outer_left_spine")
        on_block = force_on(action_block, "knee_outer_left_inner_frame_block")
        dot = sum(a * b for a, b in zip(on_spine, on_block))
        angle = math.degrees(math.acos(max(-1.0, min(1.0, dot / (norm(on_spine) * norm(on_block))))))
        three_rows.append({
            "axis_id": bolt["axis_id"],
            "spine_plane_connection": action_spine["source_connection_name"],
            "physical_lateral_action_on_spine_xyz_N": on_spine,
            "spine_plane_resultant_N": norm(on_spine),
            "block_plane_connection": action_block["source_connection_name"],
            "physical_lateral_action_on_inner_frame_block_xyz_N": on_block,
            "block_plane_resultant_N": norm(on_block),
            "outer_plane_resultant_ratio_spine_over_block": norm(on_spine) / norm(on_block),
            "outer_action_vector_angle_deg": angle,
            "outer_seat_tension_N": norm(force_on(tie, tie["first"])),
            "middle_member": "base_side_left",
            "middle_member_plane_actions_xyz_N": {
                action_spine["source_connection_name"]: force_on(action_spine, "base_side_left"),
                action_block["source_connection_name"]: force_on(action_block, "base_side_left"),
            },
            "symmetric_double_shear_reference_scenarios_N": [
                {"scenario_id": x["scenario_id"], "reference_N": x["one_bolt_three_member_reference_Z_lbf"] * N_PER_LBF}
                for x in bg003_scenarios
            ],
            "comparison_limit": "not comparable to existing symmetric equal-outer-action three-member double-shear scenarios; no single-plane, summed-plane, or summed-bolt capacity ratio is computed",
        })

    header_rows = []
    for bolt in groups["BG045"]["bolts"]:
        tie = action_for(bolt, "/outer-seat-axial-tie")
        plane = next(a for a in bolt["actions"] if a["role"] == "candidate_bolt_lateral_plane")
        on_header = force_on(plane, "base_header")
        xrow = bg045_scenarios["global X: parallel to header grain"]
        yrow = bg045_scenarios["global Y: perpendicular to header grain"]
        header_rows.append({
            "axis_id": bolt["axis_id"],
            "plane_connection": plane["source_connection_name"],
            "physical_lateral_action_on_base_header_xyz_N": on_header,
            "lateral_resultant_N": norm(on_header),
            "outer_seat_tension_N": norm(force_on(tie, tie["first"])),
            "conditional_directional_single_bolt_references_N": {
                "global_X_unadjusted": xrow["unadjusted_single_bolt_reference_N"],
                "global_X_Ceg_only": xrow["Ceg_only_reference_N"],
                "global_Y_unadjusted": yrow["unadjusted_single_bolt_reference_N"],
                "global_Y_Ceg_only": yrow["Ceg_only_reference_N"],
            },
            "component_to_reference_ratios": {
                "abs_X_over_X_Ceg_only": abs(on_header[0]) / xrow["Ceg_only_reference_N"],
                "abs_Y_over_Y_Ceg_only": abs(on_header[1]) / yrow["Ceg_only_reference_N"],
                "abs_X_over_X_unadjusted": abs(on_header[0]) / xrow["unadjusted_single_bolt_reference_N"],
                "abs_Y_over_Y_unadjusted": abs(on_header[1]) / yrow["unadjusted_single_bolt_reference_N"],
            },
            "comparison_limit": "separate X/Y component/reference ratios only, retaining the prior conditional main/side, Fe and Ceg assumptions; no mixed-axis interaction, group resistance, axial resistance, or acceptance",
        })

    washer_basis = refs["washer_seats"]["reference_basis"]
    seats = []
    for seat in final["outer_washer_seats"]:
        area = seat["modeled_outer_washer_annular_area_mm2"]
        tension = seat["signed_outer_seat_tie_action_n"]
        pressure = tension / area
        if not close(pressure, seat["conditional_full_annulus_uniform_average_pressure_mpa"], 1e-8):
            raise ValueError(f"washer pressure round trip failed for {seat['axis_id']} / {seat['physical_member']}")
        ref = seat["conditional_fc_perp_reference_n"]
        seats.append({
            "axis_id": seat["axis_id"],
            "member": seat["physical_member"],
            "seat_role": seat["seat_role"],
            "seat_point_global_xyz_mm": seat["seat_point_global_xyz_mm"],
            "outer_tie_N": tension,
            "modeled_full_annulus_area_mm2": area,
            "uniform_average_pressure_MPa": pressure,
            "conditional_Fc_perp_reference_N": ref,
            "conditional_Fc_perp_reference_status": seat["conditional_fc_perp_reference_status"],
            "pressure_to_Fc_perp_reference": (pressure / washer_basis["wood_fc_perp_mpa"]) if ref is not None else None,
            "tie_to_Fc_perp_force_reference": (tension / ref) if ref is not None else None,
            "full_annulus_supported_seat_ratio": (tension / washer_basis["reference_force_N_per_eligible_full_annulus_seat"]) if seat["physical_member"] in washer_basis["eligible_current_seat_members"] else None,
            "comparison_limit": "uniform average only; full annulus and sound eligible DF-L No.2 transverse-to-grain wood are unverified; no washer bending/spreading or actual seat-pressure check",
        })

    # Compute BG003 asymmetry from the generated, endpoint-specific actions.
    bg003_asymmetry = []
    for row in three_rows:
        bg003_asymmetry.append({
            "axis_id": row["axis_id"],
            "spine_to_block_resultant_ratio": row["outer_plane_resultant_ratio_spine_over_block"],
            "spine_vs_block_action_angle_deg": row["outer_action_vector_angle_deg"],
        })

    screen = {
        "schema": "current_corner_a12_conditional_resistance_screen/v1",
        "status": "PASS_SOURCE_BOUND_CONDITIONAL_COMPARABILITY_SCREEN_ONLY",
        "mechanical_acceptance": False,
        "design_qualification": False,
        "fabrication_or_climbing_release": False,
        "native_solve_launched_by_this_screen": False,
        "scope": "one authenticated a12-rear response, final accepted load factor 1.0; BG001, BG003, BG045 and six bolt-axis outer-seat ties only",
        "provenance": {
            "demand_report_path": str(DEMAND_PATH.relative_to(ROOT)),
            "demand_report_sha256": sha256(DEMAND_PATH),
            "response_path": str(RESPONSE_PATH.relative_to(ROOT)),
            "response_sha256": sha256(RESPONSE_PATH),
            "model_path": str(MODEL_PATH.relative_to(ROOT)),
            "model_sha256": sha256(MODEL_PATH),
            "case_id": "a12-rear",
            "final_time": final["time"],
            "final_load_factor": final["load_factor"],
            "accepted_increment_count": len(report["increments"]),
            "all_7_increment_root_and_corner_balance_gates_passed": True,
            "parent_50_body_all_increment_balance_passed": True,
            "source_manifest_sha256": report["authenticated_source_case"]["source_case_manifest_sha256"],
            "contract_sha256": report["source_contract"]["contract_sha256"],
            "interface_map_sha256": report["source_contract"]["interface_map_sha256"],
            "parent_terminal_status": parent_assessment["status"],
            "parent_body_status": parent_body["status"],
        },
        "demand_and_reference_results": {
            "BG001_two_post_bolts": post_rows,
            "BG003_two_three_member_bolts": three_rows,
            "BG003_outer_plane_asymmetry_summary": bg003_asymmetry,
            "BG045_two_header_bolts": header_rows,
            "six_bolts_twelve_outer_washer_seats": seats,
        },
        "existing_reference_evidence": {
            "BG001_individual_bolt": {"path": SOURCE_FILES["bg001_bolt"], "sha256": source_hashes["BG001_individual_bolt"], "mechanical_acceptance": False},
            "BG001_group_factor": {"path": SOURCE_FILES["bg001_group"], "sha256": source_hashes["BG001_group_factor"], "mechanical_acceptance": False},
            "BG003_three_member_transfer": {"path": SOURCE_FILES["bg003_three_member"], "sha256": source_hashes["BG003_two_three_member_bolts"], "mechanical_acceptance": False},
            "BG045_endgrain": {"path": SOURCE_FILES["bg045_endgrain"], "sha256": source_hashes["BG045_endgrain"], "mechanical_acceptance": False},
            "geometry_only_splitting_net_section": {"path": SOURCE_FILES["section_geometry"], "sha256": source_hashes["geometry_only_splitting_and_net_section"], "mechanical_acceptance": False},
            "washer_seat_geometry_and_Fc_perp_reference": {"path": SOURCE_FILES["washer_seats"], "sha256": source_hashes["washer_seats"], "mechanical_acceptance": False},
        },
        "applicability_conclusions": {
            "BG001": "The existing two-member single-bolt references permit separate global-Y and global-Z component-to-reference comparisons under their explicit 1/4-in full-body-shank, 38.1-mm bearing, zero-gap, SG 0.5 and Fe assumptions. They do not establish mixed-axis interaction, a group capacity, bolt axial resistance, or acceptance.",
            "BG003": "Both physical three-member bolts have unequal, non-collinear actions on their two outer receivers. Existing double-shear scenarios assume equal same-direction outer actions. They are not directly applicable; no capacity ratio is calculated and neither plane nor bolt capacities are added.",
            "BG045": "Existing single-bolt X/Y lateral references permit separate component ratios only under the prior conditional main/side, Fe and Ceg assumptions. A combined-axis equation, group resistance, bolt axial capacity and acceptance remain unavailable.",
            "outer_seat_bearing": "Six positive outer-seat axial tie demands are converted to full-annulus uniform-average pressure. Conditional Fc-perp ratios are shown only for base_post_outer_left and base_header, for which the source geometry screen supplies a conditional DF-L No.2 reference. No block Fc-perp comparison is made; BG045 inner-frame-block seats are parallel to proposed grain.",
        },
        "section_and_joint_limits": [
            "Whole-body balance is not used as internal section action. This report uses exporter-recovered local bolt-plane actions; no splitting, row shear, tear-out, or net-section demand/capacity ratio is computed.",
            "The existing splitting/net-section artifact supplies geometry-only void areas and uniform-stress coefficients, not a supported failure-plane model, signed section action, wood strengths, or a resistance criterion.",
            "No actual wood grade/condition, bolt grade or delivered shank/root/thread geometry, hole fit, bolt tensile resistance, washers, washer opening, supported seat polygon, contact distribution, preload, or installer condition is verified.",
            "No adjustment combination, complete group capacity, axial/lateral interaction, or joint acceptance is inferred from the displayed conditional references.",
            "This is one case only and does not establish the remaining cases, sensitivities, floor qualification, uniqueness of selected floor branch, or climbing/fabrication release.",
        ],
        "source_file_sha256": {"screen.py": sha256(HERE / "screen.py")},
    }
    output = HERE / "screen.json"
    output.write_text(json.dumps(screen, indent=2, sort_keys=True) + "\n")
    print(f"wrote {output.relative_to(ROOT)}")
    print(f"screen.py sha256={sha256(HERE / 'screen.py')}")
    print(f"screen.json sha256={sha256(output)}")


if __name__ == "__main__":
    main()
