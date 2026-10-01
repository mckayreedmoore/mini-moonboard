#!/usr/bin/env python3
"""Reproduce the bounded BG045 axis-2-only geometry comparison.

Reads authenticated case-bound demand exports and existing geometry records.
It does not modify a model, query/rebuild CAD, or launch a structural solver.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists())
HERE = Path(__file__).resolve().parent
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
BLOCK_ID = "knee_outer_left_inner_frame_block"
HEADER_ID = "base_header"
AXIS_IDS = ("knee_outer_left_inner_header_1", "knee_outer_left_inner_header_2")
EXPECTED_CASES = {
    "a1-rear": "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json",
    "a12-rear": "current-corner-native-demand-export-attempt03/corner-demand-report.json",
    "k12-rear": "current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json",
}

PINNED_SOURCE_SHA256 = {
    "docs/wood-joints-mvp/hypotheses/support-corner-review-2026-09-30/README.md": "b9cfe28dfed2205da3f2375f7563e2d8839bd0588dba85bdf7e3777ab01c9250",
    "docs/wood-joints-mvp/hypotheses/support-corner-review-2026-09-30/diagnostics.json": "174f8f945e41a273318a41fc401f1ef484160b500d624d80f57cd3480a343c98",
    f"{BASE}/current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json": "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce",
    f"{BASE}/current-corner-native-demand-export-attempt03/corner-demand-report.json": "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    f"{BASE}/current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json": "a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0",
    f"{BASE}/current-bg045-edge-applicability-dependency-attempt01/README.md": "84631f7eefbefe13a778914c87bb157bf66a7f53c07d2c942e26b5e71f902f88",
    f"{BASE}/current-bg045-edge-applicability-dependency-attempt01/dependency.json": "98916b15d05b3ed023e6d099b1643f7155693eb10b780ac12ca2dfa9fc57d772",
    f"{BASE}/current-corner-bg045-two-case-wood-mode-screen-attempt01/README.md": "565f686f6d4d0bdca6eee747c9f682f4277847abd31db6f6aef178bcafb6685c",
    f"{BASE}/current-corner-bg045-two-case-wood-mode-screen-attempt01/screen.json": "6b63e59dbbc1e77ad46eb582b97fead1a6d874a0df8e01353f0ff049065d864b",
    f"{BASE}/current-bg045-conditional-detailing-exception-attempt01/README.md": "cb216cd4b653e80a9245ac6ffc31f62d7a3294955be7b73182ec593379b30f80",
    f"{BASE}/current-bg045-conditional-detailing-exception-attempt01/detail-screen.json": "0d295b5790ecb707c12effe3f51a850177269b8533e93bdc792ed1058e34b0db",
    f"{BASE}/current-corner-local-wood-screen-attempt01/README.md": "3e50086cea176a3dc282f3da4fcc9c2d3ddfee20d7867d4f6dec512e5dc56006",
    f"{BASE}/current-corner-local-wood-screen-attempt01/section-screen.json": "22209a82b0bda6dfc5c140ccc4e481717e0e7c71d30a5827271c81ac71070564",
    f"{BASE}/current-knee-three-member-profile-attempt01/README.md": "0809625dad5c960854c1a2657989ff121ab115888d9dedd6f12e0b4a2fd22321",
    f"{BASE}/current-knee-three-member-profile-attempt01/query.json": "5c820231ac4434e896ee708c72128672424ff158b3ee4458197cdadc1a4b0854",
    f"{BASE}/current-knee-three-member-profile-attempt01/source-pins.json": "629552eba2b3dd2639df245dde56afb46dae7c01d2b2b9b1d774f98ca4a846c7",
    f"{BASE}/current-corner-washer-seat-screen-attempt01/README.md": "6faede5b5473d30295b3a65047d44c30dcd91112b661cabd512e95e7ea94d645",
    f"{BASE}/current-corner-washer-seat-screen-attempt01/seat-screen.json": "67dda5964a9c2a864cdb5ee0e898bae3c9e6bea212e2eeb71d5b33f765481ef0",
    f"{BASE}/current-knee-header-endgrain-screen-attempt01/README.md": "d17ed87202d56c0cf1d1a71c0cf2c19e882dae32f4645fa7ab8e5034fda279f2",
    f"{BASE}/current-knee-header-endgrain-screen-attempt01/conditional-screen.json": "2c4e3cac2c1b951ccd99cff69c5678cc605651b752ff5f9f5cc5b2f7ee3eff28",
    f"{BASE}/bolt-groups/bolt-groups.json": "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4",
    "docs/floor-flush-construction-kerf-right/connection-axes.csv": "174033945a2136b094bf99360cb2c6dfa409accef423ab12538ef289b5d36a58",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json": "c1e53e9a08599d13a992fc11a493853c1695f697f3fe99b45af20795c430240a",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(relative_path: str | Path) -> dict[str, Any]:
    return json.loads((ROOT / relative_path).read_text())


def rounded(value: float, digits: int = 9) -> float:
    return round(float(value), digits)


def sign(value: float, tol: float = 1e-8) -> int:
    return 1 if value > tol else (-1 if value < -tol else 0)


def face_distances(y: float, bounds: list[float]) -> dict[str, float]:
    return {"minus_y": y - float(bounds[0]), "plus_y": float(bounds[1]) - y}


def rectangle_ray_first_face(
    xy: tuple[float, float], vector: tuple[float, float],
    x_bounds: list[float], y_bounds: list[float],
) -> dict[str, Any]:
    x, y = xy
    fx, fy = vector
    candidates: list[tuple[float, str, float]] = []
    if fx > 1e-12:
        candidates.append(((float(x_bounds[1]) - x) / fx, "+X", float(x_bounds[1]) - x))
    elif fx < -1e-12:
        candidates.append(((x - float(x_bounds[0])) / -fx, "-X", x - float(x_bounds[0])))
    if fy > 1e-12:
        candidates.append(((float(y_bounds[1]) - y) / fy, "+Y", float(y_bounds[1]) - y))
    elif fy < -1e-12:
        candidates.append(((y - float(y_bounds[0])) / -fy, "-Y", y - float(y_bounds[0])))
    if not candidates:
        return {"first_face": None, "normal_distance_mm": None, "ray_travel_mm": None, "status": "zero_in_plane_vector"}
    t, face, normal_distance = min(candidates, key=lambda row: row[0])
    return {
        "first_face": face,
        "normal_distance_mm": normal_distance,
        "ray_parameter_mm_per_n": t,
        "ray_travel_mm": math.hypot(fx, fy) * t,
        "interpretation": "rectangular-envelope ray geometry only; not an NDS oblique-load rule",
    }


def point_segment_xy_distance(
    point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]
) -> tuple[float, float, tuple[float, float]]:
    dx, dy = end[0] - start[0], end[1] - start[1]
    den = dx * dx + dy * dy
    t = 0.0 if den == 0.0 else max(0.0, min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / den))
    nearest = (start[0] + t * dx, start[1] + t * dy)
    return math.hypot(point[0] - nearest[0], point[1] - nearest[1]), t, nearest


def axis_force_by_member(increment: dict[str, Any], axis_id: str, member: str) -> list[float]:
    bolts = increment["primary_physical_bolt_groups"]["BG045"]["bolts"]
    bolt = next(row for row in bolts if row["axis_id"] == axis_id)
    actions = [row for row in bolt["actions"] if row["role"] == "candidate_bolt_lateral_plane"]
    if len(actions) != 1:
        raise SystemExit(f"expected one BG045 lateral action for {axis_id}")
    action = actions[0]
    if action["first"] == member:
        return [float(v) for v in action["force_on_first_xyz_n"]]
    if action["second"] == member:
        return [float(v) for v in action["force_on_second_xyz_n"]]
    raise SystemExit(f"member {member} absent from {axis_id} lateral action")


def main() -> None:
    observed_pins = {rel: sha256(ROOT / rel) for rel in PINNED_SOURCE_SHA256}
    mismatches = {
        rel: {"expected": PINNED_SOURCE_SHA256[rel], "observed": observed_pins[rel]}
        for rel in PINNED_SOURCE_SHA256 if observed_pins[rel] != PINNED_SOURCE_SHA256[rel]
    }
    if mismatches:
        raise SystemExit(f"pinned inputs changed; stop and re-review: {json.dumps(mismatches, sort_keys=True)}")

    evidence_path = BASE / "current-corner-bg045-two-case-wood-mode-screen-attempt01/screen.json"
    dep_path = BASE / "current-bg045-edge-applicability-dependency-attempt01/dependency.json"
    prior_path = BASE / "current-bg045-conditional-detailing-exception-attempt01/detail-screen.json"
    section_path = BASE / "current-corner-local-wood-screen-attempt01/section-screen.json"
    profile_path = BASE / "current-knee-three-member-profile-attempt01/query.json"
    groups_path = BASE / "bolt-groups/bolt-groups.json"
    seat_path = BASE / "current-corner-washer-seat-screen-attempt01/seat-screen.json"
    helper_path = BASE / "current-knee-header-endgrain-screen-attempt01/conditional-screen.json"

    evidence = read_json(evidence_path)
    dep = read_json(dep_path)
    prior = read_json(prior_path)
    section = read_json(section_path)
    profile = read_json(profile_path)
    groups = read_json(groups_path)
    seats = read_json(seat_path)
    helper = read_json(helper_path)
    if evidence["geometry_revision_id"] != "led-clearance-2x6-runner-seated-blocks-v1":
        raise SystemExit("reviewed BG045 direction screen geometry revision changed")
    if dep["status"] != "CONDITIONAL_EDGE_RULE_APPLICABILITY_PENDING":
        raise SystemExit("conditional edge-rule applicability status changed")
    if groups["geometry_revision_id"] != evidence["geometry_revision_id"] or len(groups["candidate_axes"]) != 92:
        raise SystemExit("reviewed 92-axis candidate geometry identity changed")
    if profile["scope"]["physical_stack_group_id"] != "BG003" or profile["scope"]["ray_count"] != 72:
        raise SystemExit("pinned BG003 profile-query scope changed")
    if helper["group_id"] != "BG045" or helper["native_solve_run"] is not False:
        raise SystemExit("existing BG045 helper scenario identity changed")

    diameter = float(dep["recorded_quarter_inch_scenario_diameter_mm"])
    loaded_4d = float(dep["perpendicular_loaded_edge_reference_mm"])
    unloaded_15d = 1.5 * diameter
    if abs(diameter - 6.35) > 1e-9 or abs(loaded_4d - 4.0 * diameter) > 1e-9 or abs(loaded_4d - 25.4) > 1e-9:
        raise SystemExit("named conditional 1/4-in / 4D comparator changed")

    axes_all = {row["axis_id"]: row for row in groups["candidate_axes"]}
    axes = {axis_id: axes_all[axis_id] for axis_id in AXIS_IDS}
    if any(abs(float(axes[a]["shaft_center_global_xyz_mm"][0]) + 1085.85) > 1e-6 for a in AXIS_IDS):
        raise SystemExit("BG045 X stations changed")
    current_y = {axis_id: float(axes[axis_id]["shaft_center_global_xyz_mm"][1]) for axis_id in AXIS_IDS}

    old_axes = prior["unapproved_both_y_face_band_sensitivity"]["axes"]
    both_face_y = {axis_id: float(old_axes[axis_id]["proposed_y_mm"]) for axis_id in AXIS_IDS}
    axis2_only_y = {AXIS_IDS[0]: current_y[AXIS_IDS[0]], AXIS_IDS[1]: current_y[AXIS_IDS[1]] + 5.4}
    if abs(axis2_only_y[AXIS_IDS[1]] - (-150.3)) > 1e-8:
        raise SystemExit("axis-2-only target is not current Y + 5.4 mm")
    if abs(both_face_y[AXIS_IDS[0]] - (-67.75)) > 1e-8 or abs(both_face_y[AXIS_IDS[1]] - (-150.3)) > 1e-8:
        raise SystemExit("previous both-face sensitivity coordinates changed")
    scenarios = {
        "current_reviewed": current_y,
        "axis2_only_plus_5_4mm": axis2_only_y,
        "prior_both_face_4d_band_unapproved": both_face_y,
    }

    member_frames = evidence["member_frames_and_source_envelopes"]
    block = member_frames[BLOCK_ID]
    header = member_frames[HEADER_ID]
    block_x_bounds = [float(v) for v in block["x_edge_bounds_mm"]]
    block_y_bounds = [float(v) for v in block["y_edge_bounds_mm"]]
    header_x_bounds = [float(v) for v in header["x_end_bounds_mm"]]
    header_y_bounds = [float(v) for v in header["y_edge_bounds_mm"]]
    if any(abs(a - b) > 1e-8 for a, b in zip(block_y_bounds, [-175.7, -42.35])) or any(abs(a - b) > 1e-8 for a, b in zip(header_y_bounds, [-175.7, -36.0])):
        raise SystemExit("pinned block/header Y source envelopes changed")
    x_by_axis = {axis_id: float(axes[axis_id]["shaft_center_global_xyz_mm"][0]) for axis_id in AXIS_IDS}

    scenario_geometry: dict[str, Any] = {}
    for scenario_id, y_values in scenarios.items():
        axis_rows = {}
        for axis_id in AXIS_IDS:
            y = y_values[axis_id]
            axis_rows[axis_id] = {
                "center_xyz_mm": [x_by_axis[axis_id], y, float(axes[axis_id]["shaft_center_global_xyz_mm"][2])],
                "block_center_to_y_faces_mm": face_distances(y, block_y_bounds),
                "base_header_center_to_y_faces_mm": face_distances(y, header_y_bounds),
                "shift_from_reviewed_y_mm": y - current_y[axis_id],
            }
        pitch = abs(y_values[AXIS_IDS[0]] - y_values[AXIS_IDS[1]])
        scenario_geometry[scenario_id] = {"axes": axis_rows, "y_center_pitch_mm": pitch}

    if abs(scenario_geometry["current_reviewed"]["y_center_pitch_mm"] - 93.35) > 1e-8:
        raise SystemExit("current BG045 pitch changed")

    # Source-demand vectors remain conditional direction screens for each case.
    demand_summary: dict[str, Any] = {}
    raw_case_forces: dict[str, dict[str, dict[str, Any]]] = {}
    reports_for_case: dict[str, dict[str, Any]] = {}
    for case_id, rel in EXPECTED_CASES.items():
        report_path = BASE / rel
        report = read_json(report_path)
        if report["case_id"] != case_id or report["geometry_revision_id"] != evidence["geometry_revision_id"]:
            raise SystemExit(f"{case_id} identity or geometry revision changed")
        if not report["actual_case_demand_usable_for_conditional_joint_checks"]:
            raise SystemExit(f"{case_id} source report no longer permits conditional demand use")
        if len(report["increments"]) != 7 or abs(float(report["increments"][-1]["load_factor"]) - 1.0) > 1e-10:
            raise SystemExit(f"{case_id} lacks the authenticated seven-increment LF=1 endpoint")
        root_gates = report.get("response_audit_root_gates")
        if root_gates is None:
            root_gates = report["direct_master_response_audit"]["root_gates"]
        if not all(root_gates.values()):
            raise SystemExit(f"{case_id} has a failed root response gate")
        if case_id == "a1-rear" and not report["parent_independent_all_body_response_audit"]["body_and_global_resultants_passed_each_increment"]:
            raise SystemExit("a1-rear parent all-body audit is not passing")
        if case_id == "a12-rear" and not report["authenticated_source_case"]["adjacent_native_execution_evidence"]["parent_terminal_assessment"]["independent_parent_all_body_pass"]:
            raise SystemExit("a12-rear parent all-body audit is not passing")
        if case_id == "k12-rear" and not report["parent_independent_all_50_body_audit"]["all_body_and_global_interval_sums_passed"]:
            raise SystemExit("k12-rear parent all-50-body audit is not passing")
        if not report["increments"][-1]["all_five_corner_bodies_raw_and_interval_balance_passed"]:
            raise SystemExit(f"{case_id} terminal source increment does not pass corner-body balance")

        case_forces: dict[str, dict[str, Any]] = {}
        per_axis_out = []
        for axis_id in AXIS_IDS:
            block_vectors = [axis_force_by_member(inc, axis_id, BLOCK_ID) for inc in report["increments"]]
            header_vectors = [axis_force_by_member(inc, axis_id, HEADER_ID) for inc in report["increments"]]
            if any(max(abs(block_vectors[j][k] + header_vectors[j][k]) for k in range(3)) > 1e-8 for j in range(7)):
                raise SystemExit(f"{case_id} {axis_id} raw block/header lateral actions are not equal/opposite")
            fy_signs = [sign(v[1]) for v in block_vectors]
            if len(set(fy_signs)) != 1:
                raise SystemExit(f"{case_id} {axis_id} source block Y direction changes during load ramp")
            final_block = block_vectors[-1]
            final_header = header_vectors[-1]
            axis_force = {"block": block_vectors, "base_header": header_vectors}
            case_forces[axis_id] = axis_force
            per_axis_out.append({
                "axis_id": axis_id,
                "source_geometry_axis_center_xyz_mm": [float(v) for v in axes[axis_id]["shaft_center_global_xyz_mm"]],
                "increment_load_factors": [float(inc["load_factor"]) for inc in report["increments"]],
                "source_block_lateral_force_xyz_n_all_7_increments": block_vectors,
                "source_header_lateral_force_xyz_n_all_7_increments": header_vectors,
                "block_Y_sign_all_increments": fy_signs,
                "final_block_Y_direction": "+Y" if final_block[1] > 0 else ("-Y" if final_block[1] < 0 else "zero"),
                "final_header_Y_direction": "+Y" if final_header[1] > 0 else ("-Y" if final_header[1] < 0 else "zero"),
            })
        raw_case_forces[case_id] = case_forces

        # The case reports differ in schema. Record their exact source identity
        # and final acceptance boundary without promoting a joint pass.
        if "authenticated_source_case" in report:
            auth = report["authenticated_source_case"]
            source_record = {k: auth[k] for k in auth if k in (
                "case_id", "source_case_manifest_sha256", "case_record_sha256",
                "input_model_json_sha256", "response_audit_json_sha256", "audited_deck_sha256",
                "native_dat_sha256", "selected_input_model_sha256", "selected_input_deck_sha256",
            )}
        else:
            auth = report["authenticated_sources"]
            source_record = {
                "case_id": case_id,
                "case_record_sha256": report["fresh_source_case"]["case_record_sha256"],
                "source_model_inputs_sha256": report["fresh_source_case"]["source_model_inputs_sha256"],
                "input_deck_sha256": auth["input_deck_sha256"],
                "native_deck_sha256": auth["native_deck_sha256"],
                "response_audit_sha256": auth["response_audit_sha256"],
                "parent_terminal_assessment_sha256": auth["parent_terminal_assessment_sha256"],
            }
        demand_summary[case_id] = {
            "report_path": str(report_path),
            "report_sha256": observed_pins[str(report_path)],
            "status": report["status"],
            "actual_case_demand_usable_for_conditional_joint_checks": True,
            "geometry_revision_id": report["geometry_revision_id"],
            "increment_count": len(report["increments"]),
            "terminal_load_factor": float(report["increments"][-1]["load_factor"]),
            "root_response_gates_all_true": True,
            "authenticated_source_case_record": source_record,
            "joint_acceptance": False,
            "axes": per_axis_out,
        }
        reports_for_case[case_id] = report

    y_direction_screens: dict[str, Any] = {}
    for case_id, forces in raw_case_forces.items():
        case_rows = {}
        for axis_id in AXIS_IDS:
            case_rows[axis_id] = {}
            for member, xbounds, ybounds in (
                (BLOCK_ID, block_x_bounds, block_y_bounds),
                (HEADER_ID, header_x_bounds, header_y_bounds),
            ):
                force = forces[axis_id]["block" if member == BLOCK_ID else "base_header"][-1]
                y = scenarios["current_reviewed"][axis_id]
                xy = (x_by_axis[axis_id], y)
                fy = force[1]
                face = "+Y" if fy > 0 else ("-Y" if fy < 0 else None)
                edge = face_distances(y, ybounds)
                loaded_distance = edge["plus_y" if face == "+Y" else "minus_y"] if face else None
                opposite_distance = edge["minus_y" if face == "+Y" else "plus_y"] if face else None
                ray_by_scenario = {}
                conditional_by_scenario = {}
                for scenario_id, ys in scenarios.items():
                    sy = ys[axis_id]
                    ray_by_scenario[scenario_id] = rectangle_ray_first_face(
                        (x_by_axis[axis_id], sy), (force[0], force[1]), xbounds, ybounds
                    )
                    dist = face_distances(sy, ybounds)
                    loaded = dist["plus_y" if face == "+Y" else "minus_y"] if face else None
                    opposite = dist["minus_y" if face == "+Y" else "plus_y"] if face else None
                    conditional_by_scenario[scenario_id] = {
                        "loaded_y_component_face": face,
                        "loaded_y_component_distance_mm": loaded,
                        "conditional_4d_comparator_mm": loaded_4d,
                        "loaded_component_is_at_or_above_4d": None if loaded is None else loaded + 1e-8 >= loaded_4d,
                        "opposite_y_face_distance_mm": opposite,
                        "conditional_unloaded_1_5d_comparator_mm": unloaded_15d,
                        "opposite_face_is_at_or_above_1_5d": None if opposite is None else opposite + 1e-8 >= unloaded_15d,
                    }
                case_rows[axis_id][member] = {
                    "source_force_xyz_n_on_member_at_reviewed_geometry": force,
                    "proposed_grain": "+Z" if member == BLOCK_ID else "+X",
                    "Y_component_direction": face,
                    "conditional_loaded_y_face_4d_screen_by_geometry_scenario": conditional_by_scenario,
                    "rectangular_ray_first_face_by_geometry_scenario": ray_by_scenario,
                    "full_header_action_is_oblique_to_proposed_plus_x_grain": member == HEADER_ID and abs(force[0]) > 1e-8 and abs(force[1]) > 1e-8,
                    "interpretation": "The signed Y component is a conditional face-direction sensitivity. Rectangular ray data are geometric only; no universal NDS oblique ray/component rule is asserted.",
                }
        y_direction_screens[case_id] = case_rows

    conditional_edge_findings: dict[str, Any] = {}
    for case_id, case_rows in y_direction_screens.items():
        findings = []
        for axis_id in AXIS_IDS:
            for member in (BLOCK_ID, HEADER_ID):
                record = case_rows[axis_id][member]
                distances = record["conditional_loaded_y_face_4d_screen_by_geometry_scenario"]
                current = distances["current_reviewed"]["loaded_y_component_distance_mm"]
                if current is None or current + 1e-8 >= loaded_4d:
                    continue
                axis2 = distances["axis2_only_plus_5_4mm"]["loaded_y_component_distance_mm"]
                both = distances["prior_both_face_4d_band_unapproved"]["loaded_y_component_distance_mm"]
                findings.append({
                    "axis_id": axis_id,
                    "member": member,
                    "source_loaded_y_face": record["Y_component_direction"],
                    "current_source_envelope_loaded_face_distance_mm": current,
                    "axis2_only_distance_mm": axis2,
                    "axis2_only_clears_only_the_conditional_signed_y_component_comparator": axis2 + 1e-8 >= loaded_4d,
                    "prior_both_face_distance_mm": both,
                    "prior_both_face_clears_only_the_conditional_signed_y_component_comparator": both + 1e-8 >= loaded_4d,
                    "current_rectangular_ray_first_face": record["rectangular_ray_first_face_by_geometry_scenario"]["current_reviewed"]["first_face"],
                    "axis2_only_rectangular_ray_first_face": record["rectangular_ray_first_face_by_geometry_scenario"]["axis2_only_plus_5_4mm"]["first_face"],
                    "full_header_vector_oblique_to_proposed_grain": record["full_header_action_is_oblique_to_proposed_plus_x_grain"],
                    "interpretation": "A comparator transition is not an NDS applicability ruling, strength result, or accepted design check.",
                })
        conditional_edge_findings[case_id] = findings

    # Same-section orthogonal bore web screen. The source profile's BG003 X
    # bores intersect the modeled BG045 Z-axis spans; shortest axis separation
    # is therefore the absolute Y-center separation for these source intervals.
    section_geom = section["modeled_geometry_inputs"]
    bore_d = float(section_geom["modeled_bore_diameter_mm_from_profile_void_intervals"])
    bore_centers = section_geom["same_section_plane_void_reconciliation"]["bg003_x_bore_centers_xyz_mm"]
    bg003 = [{"bore_id": f"BG003_x_bore_{i + 1}", "center_xyz_mm": [float(v) for v in row]} for i, row in enumerate(bore_centers)]
    if len(bg003) != 2 or abs(bore_d - 7.5) > 1e-8:
        raise SystemExit("reviewed BG003 orthogonal-bore section input changed")
    block_x_min, block_x_max = block_x_bounds
    axis_intersections = {}
    for axis_id in AXIS_IDS:
        axis = axes[axis_id]
        cx = float(axis["shaft_center_global_xyz_mm"][0])
        cz = float(axis["shaft_center_global_xyz_mm"][2])
        half_len = float(axis["modeled_shaft_occupied_length_mm"]) / 2.0
        axis_z_span = [cz - half_len, cz + half_len]
        for bore in bg003:
            bx, by, bz = bore["center_xyz_mm"]
            if not (block_x_min <= cx <= block_x_max and axis_z_span[0] <= bz <= axis_z_span[1]):
                raise SystemExit(f"source BG045 modeled shaft does not span {bore['bore_id']} coordinate")
    bore_scenarios = {}
    for scenario_id, ys in scenarios.items():
        rows = {}
        for axis_id in AXIS_IDS:
            rows[axis_id] = {}
            for bore in bg003:
                by = bore["center_xyz_mm"][1]
                centerline = abs(ys[axis_id] - by)
                rows[axis_id][bore["bore_id"]] = {
                    "BG003_bore_center_xyz_mm": bore["center_xyz_mm"],
                    "BG045_center_y_mm": ys[axis_id],
                    "orthogonal_axis_centerline_distance_mm": rounded(centerline),
                    "modeled_envelope_web_mm": rounded(centerline - bore_d),
                }
        minimum_web = min(v["modeled_envelope_web_mm"] for row in rows.values() for v in row.values())
        bore_scenarios[scenario_id] = {"pairwise": rows, "minimum_pairwise_modeled_envelope_web_mm": minimum_web}
    expected_minima = {
        "current_reviewed": 7.452644216,
        "axis2_only_plus_5_4mm": 7.452644216,
        "prior_both_face_4d_band_unapproved": 2.052644216,
    }
    for scenario_id, expected in expected_minima.items():
        if abs(bore_scenarios[scenario_id]["minimum_pairwise_modeled_envelope_web_mm"] - expected) > 2e-8:
            raise SystemExit(f"BG003/BG045 bore-web result changed for {scenario_id}")

    # Only the ten existing Hillman source axes that enter base_header are in
    # scope. Projection distance is a 2D lower-bound coordinate screen.
    register_rel = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json"
    register = read_json(register_rel)
    register_by_id = {row["axis_id"]: row for row in register["hillman_axis_rows"]}
    screw_rows = []
    csv_path = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
    with csv_path.open(newline="") as file:
        for row in csv.DictReader(file):
            if row["kind"] != "screw" or row["shop_opening_kind"] != "hillman_panel" or row["second_member"] != HEADER_ID:
                continue
            if row["name"] not in register_by_id or register_by_id[row["name"]].get("owner_moved_axis") is not False:
                raise SystemExit(f"base_header Hillman axis is not confirmed unchanged in the register: {row['name']}")
            start = tuple(float(row[f"start_{axis}_mm"]) for axis in "xyz")
            direction = tuple(float(row[f"direction_{axis}"]) for axis in "xyz")
            length = float(row["occupied_length_mm"])
            end = tuple(start[i] + direction[i] * length for i in range(3))
            screw_rows.append({
                "axis_id": row["name"], "receiver": row["second_member"],
                "start_xyz_mm": start, "end_xyz_mm": end,
                "source_occupied_envelope_diameter_mm": float(row["occupied_diameter_mm"]),
            })
    if len(screw_rows) != 10:
        raise SystemExit(f"expected exactly ten base_header Hillman axes; found {len(screw_rows)}")

    screw_screen: dict[str, Any] = {}
    for scenario_id, ys in scenarios.items():
        axis_screens = {}
        for axis_id in AXIS_IDS:
            point = (x_by_axis[axis_id], ys[axis_id])
            candidates = []
            for screw in screw_rows:
                start = (screw["start_xyz_mm"][0], screw["start_xyz_mm"][1])
                end = (screw["end_xyz_mm"][0], screw["end_xyz_mm"][1])
                dist, t, q = point_segment_xy_distance(point, start, end)
                candidates.append((dist, screw, t, q))
            dist, nearest, t, projection = min(candidates, key=lambda row: row[0])
            axis_screens[axis_id] = {
                "minimum_xy_projected_centerline_distance_mm": rounded(dist),
                "nearest_hillman_axis_id": nearest["axis_id"],
                "receiver": nearest["receiver"],
                "nearest_segment_fraction": rounded(t),
                "nearest_xy_projection_mm": [rounded(v) for v in projection],
                "nearest_source_occupied_envelope_diameter_mm": nearest["source_occupied_envelope_diameter_mm"],
            }
        screw_screen[scenario_id] = axis_screens

    seat_by_axis = {row["axis_id"]: row for row in seats["axes"] if row["axis_id"] in AXIS_IDS}
    if set(seat_by_axis) != set(AXIS_IDS):
        raise SystemExit("reviewed BG045 washer seat rows are incomplete")
    washer_scope = {
        axis_id: {
            "fit_status": seat_by_axis[axis_id]["fit_status"],
            "selected_product": seat_by_axis[axis_id].get("selected_product"),
            "unresolved_limits": list(seat_by_axis[axis_id]["limits"]),
            "outer_seat_points_xyz_mm_current": [row["seat_point_xyz_mm"] for row in seat_by_axis[axis_id]["outer_seats"]],
            "axis2_only_y_translation_mm": axis2_only_y[axis_id] - current_y[axis_id],
            "no_washer_fit_or_support_claim": True,
        }
        for axis_id in AXIS_IDS
    }

    result = {
        "schema": "current_bg045_axis2_only_proposal_screen/v1",
        "status": "PASS_SOURCE_BOUND_CONDITIONAL_GEOMETRY_COMPARISON_ONLY",
        "candidate": evidence["candidate"],
        "geometry_revision_id": evidence["geometry_revision_id"],
        "scope": "BG045 axes 1 and 2; compare current reviewed coordinates, a conditional axis-2-only +5.4 mm Y proposal, and the prior unapproved both-face 4D band using three authenticated rear-case source direction records.",
        "execution_boundary": {
            "native_solver_run": False,
            "CAD_query_or_rebuild_run": False,
            "reviewed_model_or_axis_files_modified": False,
            "production_axis_move_approved": False,
            "source_case_forces_reused_after_relocation_as_demands": False,
        },
        "conditional_edge_reference": {
            "standard_scenario": "NDS 2024 Table 12.5.1C, conditional smooth 1/4-in bolt scenario only",
            "assumed_bolt_diameter_mm": diameter,
            "conditional_loaded_perpendicular_to_grain_edge_4d_mm": loaded_4d,
            "conditional_unloaded_edge_1_5d_mm": unloaded_15d,
            "applicability_status": dep["status"],
            "interpretation_boundary": "Current source directions select conditional signed-face comparisons. For an oblique resultant, rectangular-envelope first-ray output is geometry context; this screen does not assert a universal NDS ray/component rule or settle applicability to the completed end-grain-axis detail.",
        },
        "source_case_exports": demand_summary,
        "source_direction_and_conditional_face_screens": y_direction_screens,
        "current_under_4d_signed_y_component_findings": conditional_edge_findings,
        "geometry_scenarios": {
            "reviewed_current_axis_y_mm": current_y,
            "axis2_only_conditional_proposal_y_mm": axis2_only_y,
            "prior_both_face_band_unapproved_y_mm": both_face_y,
            "proposals_are_conditional_coordinates_not_approved_changes": True,
            "edge_distances_and_pitch": scenario_geometry,
        },
        "bg003_orthogonal_bore_web": {
            "modeled_bore_diameter_mm_each": bore_d,
            "bg003_bore_centers_xyz_mm": [row["center_xyz_mm"] for row in bg003],
            "BG003_finished_profile_ray_count": int(profile["scope"]["ray_count"]),
            "scenario_results": bore_scenarios,
            "axis2_only_avoids_axis1_both_face_web_consequence": {
                "axis1_remains_reviewed_y_mm": current_y[AXIS_IDS[0]],
                "current_and_axis2_only_minimum_modeled_web_mm": bore_scenarios["current_reviewed"]["minimum_pairwise_modeled_envelope_web_mm"],
                "both_face_minimum_modeled_web_mm": bore_scenarios["prior_both_face_4d_band_unapproved"]["minimum_pairwise_modeled_envelope_web_mm"],
                "governing_both_face_pair": "BG045 axis 1 / BG003 orthogonal bore 2",
                "web_is_geometry_only_not_strength_or_splitting_criterion": True,
            },
            "profile_limit": "Existing query samples 72 rays at the current finished profile. This arithmetic reuses the source section bore centers and modeled diameter; it is not a continuous-profile or tolerance check for a relocated axis.",
        },
        "ten_base_header_hillman_receiver_projection_screen": {
            "source_axis_count": len(screw_rows),
            "axes": [row["axis_id"] for row in screw_rows],
            "all_ten_are_register_confirmed_unchanged": True,
            "scenario_minima_by_BG045_axis": screw_screen,
            "interpretation": "XY projection to the ten existing Hillman axes entering base_header only. It omits Z separation; 4.1402 mm source occupied envelopes are legacy CAD geometry, not a delivered screw diameter. This does not establish receiver clearance, backing, installation, or load transfer.",
            "inventory": "Preserve all 66 Hillman panel/kicker screws; only these ten base_header receivers were screened because these are the affected corner receiver dependencies identified in the source.",
        },
        "washer_seat_and_existing_helper_evidence": {
            "washer_seats": washer_scope,
            "washer_scope_limit": "Washer product remains unselected; exact support polygon/opening radius and relocated fit/support are unresolved.",
            "existing_BG045_helper_record": {
                "path": str(helper_path),
                "sha256": observed_pins[str(helper_path)],
                "use": "Pinned prior conditional end-grain/helper evidence only; its strength outputs are not transferred to either relocated proposal.",
                "mechanical_acceptance": helper.get("mechanical_acceptance"),
                "accepted_case_demands": helper.get("accepted_case_demands"),
            },
        },
        "remaining_applicability_and_strength_gaps": [
            "Map NDS 2024 Table 12.5.1C loaded/unloaded edge language to the completed BG045 end-grain-axis block/header topology and its group/action direction; NDS does not provide a universal oblique-ray/component selection rule here.",
            "Header full lateral actions combine along-grain +X and cross-grain Y components. The Y-face values are conditional component sensitivities, not a complete header detailing check.",
            "Verify actual finished edge distances, profile, bore union, tolerances, spacing, bearing, washer seating/access, receiver backing and load transfer at any proposed coordinate before implementing it.",
            "Establish the applicable complete-joint lateral/axial interaction, net-section/row tear-out, and supported splitting method for this geometry; the 2.053 mm nominal web is not a splitting criterion.",
            "A moved axis changes stiffness and load distribution. Rerun the affected authenticated case(s) on separately reviewed/frozen geometry before using any force as a relocated-axis demand.",
        ],
        "source_pins": {rel: {"sha256": observed_pins[rel]} for rel in sorted(observed_pins)},
        "producer_sha256": sha256(HERE / "produce.py"),
    }
    out = HERE / "detail-screen.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(out.relative_to(ROOT)), "sha256": sha256(out), "case_count": len(demand_summary), "scenario_count": len(scenarios)}, sort_keys=True))


if __name__ == "__main__":
    main()
