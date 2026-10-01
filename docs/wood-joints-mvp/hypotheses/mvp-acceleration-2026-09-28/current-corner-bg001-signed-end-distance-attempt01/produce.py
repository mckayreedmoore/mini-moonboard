#!/usr/bin/env python3
"""Reproduce the bounded BG001 signed-end and C_delta direction screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "signed-end-distance-screen.json"

SOURCES = {
    "direction_screen": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-resultant-direction-single-shear-attempt01/resultant-direction-screen.json",
    "direction_screen_readme": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-resultant-direction-single-shear-attempt01/README.md",
    "accepted_demand_report": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/corner-demand-report.json",
    "geometry": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/bolt-groups/bolt-groups.json",
    "finished_profile_query": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-finished-profile-attempt01/query.json",
    "finished_profile_readme": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-finished-profile-attempt01/README.md",
    "prior_group_factor": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-post-group-factor-attempt01/conditional-group-factor.json",
    "prior_group_factor_readme": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-post-group-factor-attempt01/README.md",
    "angle_interpolation_method_record": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-finished-end-edge-query-attempt01/README.md",
    "group_action_helper": "mini_moonboard/nds_2024_group_action.py",
}

PINNED_SHA256 = {
    "direction_screen": "d3b1ce4448ea90929b6410424f0212d86b4caee5130bca7c93209e06ad5b3c10",
    "direction_screen_readme": "997ab4db462244d00526f586fe2ee6b649291d224dd50a9fff9c8e120a1fd1f4",
    "accepted_demand_report": "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    "geometry": "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4",
    "finished_profile_query": "32d3eb326cbd4e12e91f10418f340f2a9f21509f593e3f91421f10ae6aa574d2",
    "finished_profile_readme": "7cd5a76210e5e9343a115829167472a4d11f53738efcc42b57d156f9fcc23f29",
    "prior_group_factor": "9ea64b4160d95ad97e3cdb745eb7799111e55392ffc099b28c8f17c25b469ba7",
    "prior_group_factor_readme": "6f9d19b9465b06be5efc47d8a3446196e080c0a71b00ba0cb600214adec0a20f",
    "angle_interpolation_method_record": "2d9f293e7d2374459a845bdf6c0acb986c18bb4a6bbcc0fa4da4421f788754ee",
    "group_action_helper": "121ec9d5399aa3e856b4038232e6d61c628aac42ce2addf8d1ff7e3a0e4c3df9",
}

POST = "base_post_outer_left"
SPINE = "knee_outer_left_spine"
AXES = ("knee_outer_left_post_1", "knee_outer_left_post_2")
MID_STATION = "mid_depth"
TOL = 1.0e-8


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_json(name: str) -> dict[str, Any]:
    value = json.loads((ROOT / SOURCES[name]).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"expected JSON object in {SOURCES[name]}")
    return value


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source_pins() -> dict[str, str]:
    observed: dict[str, str] = {}
    for name, relative in SOURCES.items():
        actual = sha256_path(ROOT / relative)
        expected = PINNED_SHA256[name]
        if actual != expected:
            fail(f"source pin drift for {relative}: expected {expected}, got {actual}")
        observed[relative] = actual
    return observed


def unit(vector: list[float]) -> list[float]:
    length = math.sqrt(sum(component * component for component in vector))
    if length == 0.0 or not math.isfinite(length):
        fail("zero or non-finite vector")
    return [component / length for component in vector]


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def norm(vector: list[float]) -> float:
    return math.sqrt(sum(component * component for component in vector))


def unique_profile_distance(
    profile: dict[str, Any], axis_id: str, member_id: str, ray_label: str
) -> float:
    matches = [
        ray
        for ray in profile["rays"]
        if ray["group_id"] == "BG001"
        and ray["bolt_id"] == axis_id
        and ray["member_id"] == member_id
        and ray["ray_label"] == ray_label
    ]
    if len(matches) != 3 or {ray["axial_station_label"] for ray in matches} != {
        "near_headward",
        MID_STATION,
        "near_nutward",
    }:
        fail(f"expected three through-thickness profile stations: {axis_id}/{member_id}/{ray_label}")
    distances = {float(ray["center_to_last_material_exit_mm"]) for ray in matches}
    if len(distances) != 1:
        fail(f"profile station distances differ: {axis_id}/{member_id}/{ray_label}")
    if any(
        not any(hit["surface_type"] == "PLANE" for hit in ray["terminal_face_candidates"])
        for ray in matches
    ):
        fail(f"terminal profile face is not a plane: {axis_id}/{member_id}/{ray_label}")
    return distances.pop()


def find_axis(geometry: dict[str, Any], axis_id: str) -> dict[str, Any]:
    matches = [axis for axis in geometry["candidate_axes"] if axis["axis_id"] == axis_id]
    if len(matches) != 1:
        fail(f"expected one geometry axis {axis_id}")
    return matches[0]


def build_screen() -> dict[str, Any]:
    observed_pins = verify_source_pins()
    directional = load_json("direction_screen")
    profile = load_json("finished_profile_query")
    geometry = load_json("geometry")
    group_factor = load_json("prior_group_factor")

    if directional.get("case_id") != "a12-rear":
        fail("direction references are not for accepted a12-rear")
    if directional.get("mechanical_acceptance") is not False:
        fail("source direction packet changed its non-acceptance boundary")
    if not all(directional.get("checks", {}).values()):
        fail("an accepted source-demand/vector check is false")
    if directional["input_provenance"]["demand_report_sha256"] != PINNED_SHA256["accepted_demand_report"]:
        fail("direction packet no longer binds the accepted a12-rear demand report")
    if directional["input_provenance"]["response_sha256"] != "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274":
        fail("direction packet no longer binds the accepted a12-rear response")

    geom_group = [group for group in geometry["candidate_groups"] if group["group_id"] == "BG001"]
    if len(geom_group) != 1:
        fail("expected one BG001 geometry group")
    geom_axes = [find_axis(geometry, axis_id) for axis_id in AXES]
    diameters = {float(axis["modeled_shaft_diameter_mm"]) for axis in geom_axes}
    if len(diameters) != 1:
        fail("BG001 modeled bolt diameters differ")
    diameter_mm = diameters.pop()
    if not math.isclose(diameter_mm, 6.35, abs_tol=1.0e-8, rel_tol=0.0):
        fail("expected the modeled 6.35 mm (1/4 in) diameter from pinned geometry")

    centers = [axis["shaft_center_global_xyz_mm"] for axis in geom_axes]
    center_delta = [b - a for a, b in zip(centers[0], centers[1], strict=True)]
    row_axis = unit(center_delta)
    pitch_mm = norm(center_delta)
    if not (abs(row_axis[0]) < TOL and abs(row_axis[1]) < TOL and row_axis[2] > 1.0 - TOL):
        fail("BG001 source geometry no longer forms a +Z fastener row")

    # NDS Table 12.5.1A softwood endpoints recorded in the pinned 2024 method
    # notes: parallel tension 7D/3.5D, perpendicular 4D/2D for C_delta=1/.5.
    records: list[dict[str, Any]] = []
    for source_row in directional["results"]["BG001"]:
        axis_id = source_row["axis_id"]
        if axis_id not in AXES:
            fail(f"unexpected BG001 axis in the resultant packet: {axis_id}")
        per_member: dict[str, dict[str, Any]] = {}
        source_grains = source_row["source_proposed_grain_unit_global_xyz"]
        for member_id, action_key in (
            (POST, "reported_lateral_action_on_main_xyz_N"),
            (SPINE, "reported_lateral_action_on_side_xyz_N"),
        ):
            grain = source_grains[member_id]
            if not all(math.isclose(a, b, abs_tol=TOL, rel_tol=0.0) for a, b in zip(grain, [0.0, 0.0, 1.0], strict=True)):
                fail(f"the proposed grain axis changed for {member_id}")
            action = [float(x) for x in source_row[action_key]]
            if abs(action[0]) > 1.0e-8:
                fail(f"BG001 lateral action has a material bolt-axis component for {axis_id}/{member_id}")
            action_unit = unit(action)
            theta_deg = math.degrees(math.acos(min(1.0, abs(dot(action_unit, grain)))))
            grain_sign = dot(action, grain)
            if abs(grain_sign) < 1.0e-8:
                fail(f"the signed grain-parallel component is zero for {axis_id}/{member_id}")
            grain_ray = "g+" if grain_sign > 0.0 else "g-"
            end_distance_mm = unique_profile_distance(profile, axis_id, member_id, grain_ray)

            # Commentary C12.5.1.2 allows tension end-distance requirements
            # at a grain angle to be linearly interpolated between the parallel
            # tension and perpendicular-to-grain values.
            interpolation = theta_deg / 90.0
            full_distance_d = (1.0 - interpolation) * 7.0 + interpolation * 4.0
            half_distance_d = (1.0 - interpolation) * 3.5 + interpolation * 2.0
            end_distance_d = end_distance_mm / diameter_mm
            if end_distance_d < half_distance_d - TOL:
                c_delta = None
                branch_status = "below_Cdelta_0.5_minimum"
            elif end_distance_d >= full_distance_d:
                c_delta = 1.0
                branch_status = "full_factor_end_distance"
            else:
                c_delta = end_distance_d / full_distance_d
                branch_status = "linear_Cdelta_between_0.5_and_1.0"

            e_axis = unit(cross(grain, [1.0, 0.0, 0.0]))
            crossgrain_sign = dot(action, e_axis)
            if abs(crossgrain_sign) < 1.0e-8:
                fail(f"the signed cross-grain component is zero for {axis_id}/{member_id}")
            edge_ray = "e+" if crossgrain_sign > 0.0 else "e-"
            other_edge_ray = "e-" if edge_ray == "e+" else "e+"
            loaded_edge_mm = unique_profile_distance(profile, axis_id, member_id, edge_ray)
            unloaded_edge_mm = unique_profile_distance(profile, axis_id, member_id, other_edge_ray)

            per_member[member_id] = {
                "member_action_xyz_N": action,
                "grain_axis_unit_global_xyz": grain,
                "signed_grain_parallel_action_N": grain_sign,
                "loaded_grain_end": grain_ray,
                "load_to_grain_angle_deg": theta_deg,
                "loaded_end_distance_mm": end_distance_mm,
                "loaded_end_distance_D": end_distance_d,
                "interpolated_minimum_end_distance_for_Cdelta_1_D": full_distance_d,
                "interpolated_minimum_end_distance_for_Cdelta_0_5_D": half_distance_d,
                "angle_interpolated_Cdelta": c_delta,
                "angle_interpolated_branch_status": branch_status,
                "cross_grain_axis_unit_global_xyz": e_axis,
                "signed_cross_grain_action_N": crossgrain_sign,
                "loaded_edge": edge_ray,
                "loaded_edge_distance_mm": loaded_edge_mm,
                "loaded_edge_distance_D": loaded_edge_mm / diameter_mm,
                "unloaded_edge": other_edge_ray,
                "unloaded_edge_distance_mm": unloaded_edge_mm,
                "unloaded_edge_distance_D": unloaded_edge_mm / diameter_mm,
                "table_12_5_1C_loaded_edge_minimum_D": 4.0,
                "table_12_5_1C_unloaded_edge_minimum_D": 1.5,
                "loaded_and_unloaded_edges_exceed_listed_minima": (
                    loaded_edge_mm / diameter_mm >= 4.0
                    and unloaded_edge_mm / diameter_mm >= 1.5
                ),
            }

        per_fastener_c = min(
            float(per_member[POST]["angle_interpolated_Cdelta"]),
            float(per_member[SPINE]["angle_interpolated_Cdelta"]),
        )
        vector_main = per_member[POST]["member_action_xyz_N"]
        alignment_sine = norm(cross(unit(vector_main), row_axis))
        reference_n = float(source_row["conditional_governing_reference_after_Ceg_only_N"])
        demand_n = float(source_row["lateral_resultant_demand_N"])
        records.append(
            {
                "axis_id": axis_id,
                "main_member": POST,
                "side_member": SPINE,
                "member_geometry": per_member,
                "per_fastener_minimum_Cdelta": per_fastener_c,
                "actual_lateral_resultant_not_aligned_with_row": alignment_sine > 1.0e-8,
                "sine_of_angle_between_main_action_and_row": alignment_sine,
                "unadjusted_actual_direction_governing_reference_N": reference_n,
                "resultant_demand_N": demand_n,
                "single_bolt_demand_over_unadjusted_reference": demand_n / reference_n,
            }
        )

    if [record["axis_id"] for record in records] != list(AXES):
        fail("the two BG001 axes are missing or out of the pinned order")
    group_c_delta = min(float(record["per_fastener_minimum_Cdelta"]) for record in records)
    if any(record["actual_lateral_resultant_not_aligned_with_row"] is not True for record in records):
        fail("expected both actual BG001 resultants to be off-axis from the row")

    old_cg_values = [
        scenario["helper_result"]["cg"]
        for scenario in group_factor["scenario_results"]
    ]
    if old_cg_values != [1.0, 1.0]:
        fail("prior row-aligned conditional Cg results changed")
    helper_source = (ROOT / SOURCES["group_action_helper"]).read_text(encoding="utf-8")
    if '"load_direction_not_aligned_with_fastener_row"' not in helper_source:
        fail("reviewed Cg helper no longer includes its off-row rejection reason")
    group_lateral_resultant = [
        sum(float(record["member_geometry"][POST]["member_action_xyz_N"][index]) for record in records)
        for index in range(3)
    ]
    group_alignment_sine = norm(cross(unit(group_lateral_resultant), row_axis))
    if group_alignment_sine <= 1.0e-8:
        fail("the summed BG001 lateral resultant unexpectedly aligns with the row")

    reference_scalings = []
    for record in records:
        reference = float(record["unadjusted_actual_direction_governing_reference_N"])
        demand = float(record["resultant_demand_N"])
        angle_reference = reference * group_c_delta
        parallel_branch_reference = reference * (4.0 / 7.0)
        reference_scalings.append(
            {
                "axis_id": record["axis_id"],
                "unadjusted_actual_direction_mode_IV_reference_N": reference,
                "group_angle_interpolated_Cdelta": group_c_delta,
                "group_Cdelta_only_reference_N": angle_reference,
                "demand_N": demand,
                "demand_over_group_Cdelta_only_reference": demand / angle_reference,
                "separate_legacy_pure_parallel_tension_Cdelta": 4.0 / 7.0,
                "legacy_pure_parallel_Cdelta_only_reference_N": parallel_branch_reference,
                "demand_over_legacy_pure_parallel_Cdelta_only_reference": demand / parallel_branch_reference,
                "Cg_applied": False,
                "classification": "conditional C_delta-only individual-bolt reference comparison; not adjusted resistance, group capacity, or acceptance",
            }
        )

    return {
        "artifact": "BG001 signed-end and resultant-direction geometry applicability screen",
        "candidate_id": directional["candidate"],
        "revision_id": directional["geometry_revision_id"],
        "case_id": "a12-rear",
        "source_case_status": "accepted numerical response and strict prior gates; this screen adds no acceptance",
        "status": "conditional_direction_specific_Cdelta_screen_Cg_not_transferable",
        "design_qualification": False,
        "mechanical_acceptance": False,
        "native_solve_launched": False,
        "input_provenance": {
            "source_sha256": observed_pins,
            "accepted_response_sha256": directional["input_provenance"]["response_sha256"],
            "accepted_source_model_sha256": directional["input_provenance"]["source_model_sha256"],
            "accepted_demand_report_sha256": directional["input_provenance"]["demand_report_sha256"],
            "all_prior_direction_packet_checks_passed": all(directional["checks"].values()),
        },
        "geometry": {
            "group_id": "BG001",
            "axis_ids": list(AXES),
            "member_ids": [POST, SPINE],
            "bolt_axis_global_xyz": [1.0, 0.0, 0.0],
            "row_axis_unit_global_xyz_from_pinned_center_delta": row_axis,
            "modeled_diameter_mm": diameter_mm,
            "modeled_pitch_mm": pitch_mm,
            "modeled_pitch_D": pitch_mm / diameter_mm,
            "profile_source": "pinned finished STEP finite-ray query, three through-thickness stations, identical queried terminal distances",
            "grain_basis": "source-proposed +Z in both BG001 receivers; not observed stock",
        },
        "method": {
            "NDS_source": {
                "standard": "ANSI/AWC NDS-2024 Chapter 12 and Commentary",
                "chapter_12_pdf_sha256": "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a",
                "official_pdf_url": "https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf",
                "geometry_clauses": "§12.5.1.2(a), Commentary C12.5.1.2, Table 12.5.1A, §12.5.1.3 and Table 12.5.1C",
                "method_record": SOURCES["angle_interpolation_method_record"],
                "interpretation": "For the tension component at the measured load-to-grain angle, linearly interpolate the end-distance requirements between parallel-grain tension (7D at Cdelta=1 and 3.5D at Cdelta=0.5) and perpendicular-to-grain loading (4D and 2D). The smallest applicable Cdelta in the group governs all fasteners.",
                "direction_interpretation": "Use the signed grain-parallel component to choose the physical loaded end; use the full resultant-to-grain angle for commentary interpolation. This is not the separate §12.5.1.2(b) load-angle-to-fastener-axis equivalent-shear-area case.",
            },
            "Cg_assessment": {
            "prior_conditional_Cg_values": old_cg_values,
            "prior_input_direction": "unit +Z row-aligned direction only",
            "actual_direction_status": "not transferable; reviewed helper requires the lateral resultant to align with the row and returns load_direction_not_aligned_with_fastener_row otherwise",
            "per_bolt_resultant_alignment_sines": [record["sine_of_angle_between_main_action_and_row"] for record in records],
            "summed_reported_group_lateral_resultant_xyz_N": group_lateral_resultant,
            "summed_group_resultant_alignment_sine": group_alignment_sine,
            "Cg_for_actual_direction": None,
            "reason": "Both accepted per-bolt resultants are angled to the row, and their summed group lateral resultant also has a nonzero global-Y component. The prior numeric Cg=1 does not establish a mixed-direction group factor.",
            },
        },
        "signed_direction_results": records,
        "group_angle_interpolated_Cdelta": group_c_delta,
        "group_Cdelta_status": "conditional geometry factor only from signed end-distance branch and Commentary angle interpolation; not a connection acceptance factor by itself",
        "reference_scalings": reference_scalings,
        "limits": [
            "The force vectors and actual-direction single-bolt Mode IV references are from accepted a12-rear case-bound numerical output; the wood grain axes, DF-L No. 2 properties, SG 0.50, full-body 1/4-in shank, bearing lengths, zero gap, and Fyb=45,000 psi remain conditional scenarios.",
            "The queried profile distances are sampled at three receiver-depth stations and agree there; they do not establish a continuous minimum or an inspected/as-built dimension.",
            "Cdelta interpolation is a conditional Chapter 12 geometry-factor screen. No splitting, row shear, tear-out, net-section, bearing, member shear, axial tie, bolt/washer, contact, or complete-transfer capacity is evaluated.",
            "No Cg is applied to the resultant-direction references because the existing reviewed helper rejects off-row action directions. This packet does not invent a mixed-direction Cg rule.",
            "The 4/7 values are shown only as the separate prior pure-parallel-tension branch, not as the exact mixed-direction geometry factor. They remain a conservative branch comparison for this input, not a general-purpose bound.",
            "Reference scaling is not adjusted resistance, group capacity, a design DCR, a pass/fail result, or mechanical acceptance.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true", help="write the reproducible JSON result")
    action.add_argument("--verify", action="store_true", help="verify source pins and compare the committed result")
    args = parser.parse_args()
    result = build_screen()
    encoded = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    if args.write:
        OUTPUT.write_text(encoded, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)}")
    else:
        actual = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expected = json.loads(encoded)
        if actual != expected:
            fail("signed-end-distance-screen.json does not match the pinned sources and arithmetic")
        print("verified pinned sources, accepted-vector signs, geometry, direction-specific Cdelta, and reference scaling")


if __name__ == "__main__":
    main()
