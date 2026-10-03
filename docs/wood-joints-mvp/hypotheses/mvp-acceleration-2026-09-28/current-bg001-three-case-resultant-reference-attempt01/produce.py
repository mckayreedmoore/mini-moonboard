#!/usr/bin/env python3
"""Extend the reviewed BG001 resultant-direction method to three cases.

The output is a conditional, unadjusted per-bolt lateral reference screen. It
does not produce an adjusted resistance or complete-joint acceptance.
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

SOURCES = {
    "signed_demands": BASE / "current-corner-complete-resistance-register-attempt01/signed-demands.json",
    "signed_demands_producer": BASE / "current-corner-complete-resistance-register-attempt01/produce.py",
    "resultant_direction_method": BASE / "current-corner-resultant-direction-single-shear-attempt01/produce.py",
    "a1_resultant_producer": BASE / "current-bg001-a1-resultant-reference-attempt01/produce.py",
    "a1_resultant_screen": BASE / "current-bg001-a1-resultant-reference-attempt01/screen.json",
    "profile_query": BASE / "current-knee-finished-profile-attempt01/query.json",
    "profile_readme": BASE / "current-knee-finished-profile-attempt01/README.md",
    "report_a1": BASE / "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json",
    "report_a12": BASE / "current-corner-native-demand-export-attempt03/corner-demand-report.json",
    "report_k12": BASE / "current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json",
    "bg001_conditional_basis": BASE / "current-knee-post-conditional-bolt-screen-attempt01/conditional-screen.json",
    "bolt_groups": BASE / "bolt-groups/bolt-groups.json",
    "frame_grain_map": EVAL / "current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json",
    "block_grain_map": EVAL / "current-block-material-frame-map-attempt02/material-frame-map.json",
    "nds_yield_producer": BASE / "nds-screen/produce.py",
    "nds_scenarios": BASE / "nds-screen/single-bolt-scenarios.json",
    "tr12_helper": ROOT / "fea/dowel_yield.py",
    "fe_helper": ROOT / "mini_moonboard/bolted_timber_checks.py",
    "profile_manifest": EVAL / "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json",
    "post_step": EVAL / "current-full-frame-member-solids-attempt01/bundle/members/base_post_outer_left.step",
    "spine_step": EVAL / "current-full-frame-member-solids-attempt01/bundle/members/knee_outer_left_spine.step",
    "member_geometry": BASE / "reduced-static-attempt01/member-geometry.json",
    "geometry_helper": ROOT / "mini_moonboard/connection_geometry.py",
}

EXPECTED = {
    "signed_demands": "557b994f7600ceb7c958d50dd01350724d7ea86c671a086677b6f3044ecc2f48",
    "signed_demands_producer": "756e397f7e34c05eee6dfd7b25473033c10e81d1ca3424db2ef5f9f99a1e7b10",
    "resultant_direction_method": "d14ece8fd0d32e790e4f3de67aa8d860e6881231d6421b650e5b47f699aab57f",
    "a1_resultant_producer": "c20228930fd43457c51eeb9348ad375582502bf2d5f044fe6e8cf844be489b3b",
    "a1_resultant_screen": "bd5fc8d2fcc7167b4764ea7d2c60e0ef0a04c7a5343b4f573766bdfb161126fe",
    "profile_query": "32d3eb326cbd4e12e91f10418f340f2a9f21509f593e3f91421f10ae6aa574d2",
    "profile_readme": "7cd5a76210e5e9343a115829167472a4d11f53738efcc42b57d156f9fcc23f29",
    "report_a1": "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce",
    "report_a12": "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    "report_k12": "a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0",
    "bg001_conditional_basis": "adbedaceec692936dcd2b2393c04fc985c5590a1a5a557b74868cee94eb3175c",
    "bolt_groups": "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4",
    "frame_grain_map": "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409",
    "block_grain_map": "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480",
    "nds_yield_producer": "21d3b2b254b1ceb9a6cf777b98eb492b52f989cc019afa2209b92be3e4a3cdb0",
    "nds_scenarios": "130041246af11fc8e3568a7091f585d0d75581b2e1fbb3a3f4b97b750d68a7ea",
    "tr12_helper": "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    "fe_helper": "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13",
    "profile_manifest": "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    "post_step": "cdf9bb35e7ff2fda58bfdd604f69dedcba88b6b34149f874c03335abe90a1dce",
    "spine_step": "081a3930dd1334e317fc0116a24d80b4b70e9cb3f36b928cda403f66194bb5c0",
    "member_geometry": "121f1940d0180367f953a1f92443964ded901ca775536750a9b028e37d6c8187",
    "geometry_helper": "f729bc64e7ea7fb9df9308411df07e02f98fc309efcf26038809a9e7bd4bc4a4",
}

NDS_PDF = {
    "title": "AWC NDS-2024 Chapter 12, Dowel-type fasteners",
    "url": "https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf",
    "sha256": "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a",
    "use": "§§12.3.1, 12.3.3–12.3.4 and Tables 12.3.3, 12.3.1A/12.3.1B, 12.5.1A/C; this pinned PDF contains the specification text, not Commentary C12.5.1.2.",
}

HISTORICAL_COMMENTARY = {
    "title": "AWC NDS-2018 Commentary, Chapter 12",
    "url": "https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf",
    "status": "historical-method context only; no 2018 wording is adopted as a verified 2024 rule",
}

EXPECTED_CASES = ("a1-rear", "a12-rear", "k12-rear")
EXPECTED_AXES = ("knee_outer_left_post_1", "knee_outer_left_post_2")
EXPECTED_LOAD_FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
MEMBER_MAIN = "base_post_outer_left"
MEMBER_SIDE = "knee_outer_left_spine"
MM_PER_IN = 25.4
N_PER_LBF = 4.4482216152605
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
TOL = 1.0e-8


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def close(a: float, b: float, tol: float = TOL) -> bool:
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def norm(v: list[float]) -> float:
    return math.sqrt(math.fsum(x * x for x in v))


def dot(a: list[float], b: list[float]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def unit(v: list[float]) -> list[float]:
    magnitude = norm(v)
    if not math.isfinite(magnitude) or magnitude <= 0.0:
        raise ValueError("finite nonzero vector required")
    return [x / magnitude for x in v]


def cross(a: list[float], b: list[float]) -> list[float]:
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def assert_vector_close(a: list[float], b: list[float], tol: float = TOL) -> None:
    if len(a) != len(b) or not all(close(float(x), float(y), tol) for x, y in zip(a, b, strict=True)):
        raise ValueError(f"vector mismatch: {a} vs {b}")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"module could not be loaded: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def pin_sources() -> dict[str, str]:
    observed: dict[str, str] = {}
    for name, path in SOURCES.items():
        if not path.is_file():
            raise ValueError(f"required source missing: {path}")
        actual = sha256(path)
        if actual != EXPECTED[name]:
            raise ValueError(f"source pin mismatch {name}: expected {EXPECTED[name]}, got {actual}")
        observed[rel(path)] = actual
    return observed


def profile_distances(profile: dict[str, Any], axis: str, member: str) -> dict[str, float]:
    result: dict[str, float] = {}
    expected_stations = {"near_headward", "mid_depth", "near_nutward"}
    for ray in ("g-", "g+", "e-", "e+"):
        hits = [row for row in profile["rays"] if row["group_id"] == "BG001"
                and row["bolt_id"] == axis and row["member_id"] == member
                and row["ray_label"] == ray]
        if len(hits) != 3 or {row["axial_station_label"] for row in hits} != expected_stations:
            raise ValueError(f"profile query does not have three through-thickness stations: {axis}/{member}/{ray}")
        distances = {float(row["center_to_last_material_exit_mm"]) for row in hits}
        if len(distances) != 1:
            raise ValueError(f"profile distances vary over the three stations: {axis}/{member}/{ray}")
        for hit in hits:
            terminal = hit["terminal_face_candidates"]
            if (len(terminal) != 1 or terminal[0].get("surface_type") != "PLANE"
                    or float(terminal[0].get("abs_normal_dot_ray", 0.0)) < 1.0 - 1.0e-8):
                raise ValueError(f"terminal profile is not one plane normal to the ray: {axis}/{member}/{ray}")
        result[ray] = distances.pop()
    return result


def source_demands(method: Any) -> tuple[dict[str, Any], dict[str, str], dict[str, Any]]:
    pins = pin_sources()
    method_sources = method.validate_and_load_sources()
    signed = json.loads(SOURCES["signed_demands"].read_text(encoding="utf-8"))
    if (signed.get("schema") != "three_case_corner_signed_component_register/v1"
            or signed.get("status") != "AUTHENTICATED_CONDITIONAL_DEMANDS_COMPLETE_RESISTANCE_OPEN"
            or signed.get("plane_count") != 8 or signed.get("plane_state_count") != 168
            or len(signed.get("rows", [])) != 168):
        raise ValueError("three-case signed-demand register is not the pinned complete inventory")
    if signed.get("producer_sha256") != EXPECTED["signed_demands_producer"]:
        raise ValueError("signed-demand register no longer binds its producer")
    report_pin_map = {rel(SOURCES[name]): EXPECTED[name] for name in ("report_a1", "report_a12", "report_k12")}
    if signed.get("source_pins") != report_pin_map:
        raise ValueError("signed-demand register's three report pins changed")

    cases = {
        "a1-rear": (SOURCES["report_a1"], EXPECTED["report_a1"]),
        "a12-rear": (SOURCES["report_a12"], EXPECTED["report_a12"]),
        "k12-rear": (SOURCES["report_k12"], EXPECTED["report_k12"]),
    }
    reports: dict[str, dict[str, Any]] = {}
    for case_id, (path, expected_hash) in cases.items():
        report = json.loads(path.read_text(encoding="utf-8"))
        if (sha256(path) != expected_hash or report.get("case_id") != case_id
                or report.get("actual_case_demand_usable_for_conditional_joint_checks") is not True
                or len(report.get("increments", [])) != 7
                or not all(value is True for value in report.get("response_audit_root_gates", {}).values())):
            raise ValueError(f"accepted source report validation failed: {case_id}")
        reports[case_id] = report

    rows = [row for row in signed["rows"] if row.get("group") == "BG001"]
    expected_states = {(case, lf) for case in EXPECTED_CASES for lf in EXPECTED_LOAD_FACTORS}
    actual_states = {(row["case_id"], float(row["load_factor"])) for row in rows}
    if len(rows) != 42 or actual_states != expected_states:
        raise ValueError("BG001 inventory is not both bolts across exactly 21 accepted case/load states")
    if any(row.get("axis_id") not in EXPECTED_AXES for row in rows):
        raise ValueError("unexpected BG001 physical axis")
    for state in sorted(expected_states):
        state_rows = [row for row in rows if (row["case_id"], float(row["load_factor"])) == state]
        if {row["axis_id"] for row in state_rows} != set(EXPECTED_AXES) or len(state_rows) != 2:
            raise ValueError(f"incomplete same-state BG001 bolt pair: {state}")
    return signed, pins, {"method_sources": method_sources, "reports": reports, "rows": rows}


def make_record(
    row: dict[str, Any], profile: dict[str, Any], geometry_axes: dict[str, dict[str, Any]],
    grains: dict[str, list[float]], basis: dict[str, Any], nds: Any, fe_helper: Any,
) -> dict[str, Any]:
    axis = row["axis_id"]
    case = row["case_id"]
    factor = float(row["load_factor"])
    if row.get("first_receiver") != MEMBER_SIDE or row.get("second_receiver") != MEMBER_MAIN:
        raise ValueError(f"unexpected BG001 receiver order for {axis}")
    forces = {
        MEMBER_SIDE: [float(x) for x in row["force_on_first_xyz_N"]],
        MEMBER_MAIN: [float(x) for x in row["force_on_second_xyz_N"]],
    }
    if not close(norm([forces[MEMBER_MAIN][i] + forces[MEMBER_SIDE][i] for i in range(3)]), 0.0, 1.0e-7):
        raise ValueError(f"BG001 lateral actions do not close for {case}/{axis}/{factor}")
    action_rows = row.get("both_same_bolt_plane_actions", [])
    if len(action_rows) != 1:
        raise ValueError(f"expected exactly one same-bolt lateral action: {case}/{axis}/{factor}")
    action = action_rows[0]
    if action.get("role") != "candidate_bolt_lateral_plane" or action.get("source_connection_name") != row.get("source_connection_name"):
        raise ValueError(f"unexpected source plane action: {case}/{axis}/{factor}")
    assert_vector_close([float(x) for x in action["force_on_first_xyz_n"]], forces[MEMBER_SIDE])
    assert_vector_close([float(x) for x in action["force_on_second_xyz_n"]], forces[MEMBER_MAIN])

    axis_vector = unit([float(x) for x in geometry_axes[axis]["axis_head_to_nut_unit_global_xyz"]])
    if not close(abs(axis_vector[0]), 1.0) or abs(axis_vector[1]) > TOL or abs(axis_vector[2]) > TOL:
        raise ValueError(f"BG001 bolt axis is no longer global X: {axis}")
    if max(abs(dot(forces[member], axis_vector)) for member in forces) > 1.0e-7:
        raise ValueError(f"source lateral actions are not normal to the bolt axis: {case}/{axis}/{factor}")

    grains_for_member = {member: unit(grains[member]) for member in (MEMBER_MAIN, MEMBER_SIDE)}
    if any(abs(grains_for_member[member][2]) < 1.0 - TOL for member in grains_for_member):
        raise ValueError("BG001 source-proposed receiver grain is not global Z")
    e_axes = {member: unit(cross(grains_for_member[member], axis_vector)) for member in grains_for_member}
    if any(abs(e_axes[member][1]) < 1.0 - TOL for member in e_axes):
        raise ValueError("BG001 cross-grain edge axis is not global Y")

    diam_in = float(basis["diameter_in"])
    main_length_in, side_length_in = map(float, basis["main_and_side_bearing_lengths_in"])
    fyb = float(basis["bolt_bending_yield_psi_assumption"])
    angle_by_member = {
        member: math.degrees(math.acos(max(-1.0, min(1.0, abs(dot(unit(forces[member]), grains_for_member[member]))))))
        for member in (MEMBER_MAIN, MEMBER_SIDE)
    }
    fe_by_member = {
        member: float(fe_helper.dfl_dowel_bearing_psi(diam_in, angle_by_member[member]))
        for member in (MEMBER_MAIN, MEMBER_SIDE)
    }
    theta = max(angle_by_member.values())
    nds_result = nds.calculate(diam_in, main_length_in, side_length_in,
                                fe_by_member[MEMBER_MAIN], fe_by_member[MEMBER_SIDE], theta)
    if set(nds_result["reference_values_lbf"]) != set(MODES) or set(nds_result["yield_values_lbf"]) != set(MODES):
        raise ValueError("pinned single-shear helper did not return all six modes")
    references_lbf = {mode: float(nds_result["reference_values_lbf"][mode]) for mode in MODES}
    yields_lbf = {mode: float(nds_result["yield_values_lbf"][mode]) for mode in MODES}
    mode = min(references_lbf, key=references_lbf.get)
    if nds_result.get("governing_mode") != mode:
        raise ValueError("NDS/TR12 governing-mode label mismatch")

    # Check Mode IV independently from the reference-mode helper.
    ktheta = 1.0 + 0.25 * theta / 90.0
    ratio_fe = fe_by_member[MEMBER_MAIN] / fe_by_member[MEMBER_SIDE]
    direct_iv_lbf = (diam_in**2 / (3.2 * ktheta)
                     * math.sqrt(2.0 * fe_by_member[MEMBER_MAIN] * fyb
                                 / (3.0 * (1.0 + ratio_fe))))
    if not close(references_lbf["IV"], direct_iv_lbf, 1.0e-11):
        raise ValueError("independent NDS Mode IV check failed")

    demand = math.hypot(forces[MEMBER_MAIN][1], forces[MEMBER_MAIN][2])
    full_norm = norm(forces[MEMBER_MAIN])
    if not close(float(row["lateral_resultant_N"]), full_norm) or not close(demand, full_norm, 1.0e-9):
        raise ValueError("reported source resultant differs from paired Y/Z vector magnitude")
    references_n = {mode: references_lbf[mode] * N_PER_LBF for mode in MODES}
    yields_n = {mode: yields_lbf[mode] * N_PER_LBF for mode in MODES}
    ratios = {mode: demand / references_n[mode] for mode in MODES}

    tie = row["simultaneous_outer_tie"]
    if tie.get("role") != "physical_bolt_outer_seat_tension" or tie.get("first") != MEMBER_SIDE or tie.get("second") != MEMBER_MAIN:
        raise ValueError(f"same-state outer tie is not attached to this BG001 pair: {case}/{axis}/{factor}")
    tie_side = [float(x) for x in tie["force_on_first_xyz_n"]]
    tie_main = [float(x) for x in tie["force_on_second_xyz_n"]]
    assert_vector_close(tie_side, [-x for x in tie_main])
    tie_magnitude = norm(tie_main)
    if not close(tie_magnitude, float(row["simultaneous_tie_force_magnitude_N"])):
        raise ValueError("same-state tie magnitude differs from register")

    distances = {member: profile_distances(profile, axis, member) for member in grains_for_member}
    detailing: dict[str, dict[str, Any]] = {}
    for member in (MEMBER_MAIN, MEMBER_SIDE):
        g_component = dot(forces[member], grains_for_member[member])
        e_component = dot(forces[member], e_axes[member])
        if abs(g_component) < 1.0e-9 or abs(e_component) < 1.0e-9:
            raise ValueError(f"oblique signed end/edge ray unresolved for {case}/{axis}/{factor}/{member}")
        loaded_end = "g+" if g_component > 0.0 else "g-"
        loaded_edge = "e+" if e_component > 0.0 else "e-"
        unloaded_edge = "e-" if loaded_edge == "e+" else "e+"
        end_distance = distances[member][loaded_end]
        loaded_edge_distance = distances[member][loaded_edge]
        unloaded_edge_distance = distances[member][unloaded_edge]
        detailing[member] = {
            "grain_axis_unit_global_xyz": grains_for_member[member],
            "cross_grain_axis_unit_global_xyz": e_axes[member],
            "signed_grain_parallel_force_N": g_component,
            "loaded_grain_end_ray": loaded_end,
            "loaded_grain_end_profile_distance_mm": end_distance,
            "loaded_grain_end_profile_distance_D": end_distance / (diam_in * MM_PER_IN),
            "signed_cross_grain_force_N": e_component,
            "loaded_edge_ray_from_cross_grain_component": loaded_edge,
            "loaded_edge_profile_distance_mm": loaded_edge_distance,
            "loaded_edge_profile_distance_D": loaded_edge_distance / (diam_in * MM_PER_IN),
            "opposite_edge_ray": unloaded_edge,
            "opposite_edge_profile_distance_mm": unloaded_edge_distance,
            "opposite_edge_profile_distance_D": unloaded_edge_distance / (diam_in * MM_PER_IN),
            "all_four_profile_rays_mm": distances[member],
            "edge_numeric_comparison_only": {
                "loaded_edge_listed_4D_distance_mm": 4.0 * diam_in * MM_PER_IN,
                "opposite_edge_listed_1_5D_distance_mm": 1.5 * diam_in * MM_PER_IN,
                "both_ray_distances_exceed_listed_numeric_values": (
                    loaded_edge_distance >= 4.0 * diam_in * MM_PER_IN
                    and unloaded_edge_distance >= 1.5 * diam_in * MM_PER_IN
                ),
                "interpretation": "geometric comparison to Table 12.5.1C values only; this does not resolve a full oblique-grain detailing factor or splitting check",
            },
        }

    return {
        "case_id": case,
        "load_factor": factor,
        "axis_id": axis,
        "source_connection_name": row["source_connection_name"],
        "same_physical_bolt_lateral_action_pair": {
            "first_receiver": MEMBER_SIDE,
            "force_on_first_xyz_N": forces[MEMBER_SIDE],
            "second_receiver": MEMBER_MAIN,
            "force_on_second_xyz_N": forces[MEMBER_MAIN],
            "force_pair_closes": True,
            "bolt_axis_unit_global_xyz": axis_vector,
            "max_axial_component_of_lateral_force_N": max(abs(dot(forces[member], axis_vector)) for member in forces),
        },
        "paired_lateral_resultant": {
            "force_on_main_post_YZ_N": forces[MEMBER_MAIN][1:3],
            "force_on_side_spine_YZ_N": forces[MEMBER_SIDE][1:3],
            "resultant_demand_N": demand,
            "source_full_vector_norm_N": full_norm,
        },
        "receiver_direction_and_end_edge": {
            member: {
                **detailing[member],
                "lateral_load_to_proposed_grain_angle_deg": angle_by_member[member],
                "source_proposed_grain_unit_global_xyz": grains_for_member[member],
            }
            for member in (MEMBER_MAIN, MEMBER_SIDE)
        },
        "conditional_fe_basis": {
            "wood_scenario": "DF-L No. 2, SG 0.50; proposed grain only, not observed stock",
            "parallel_endpoint_psi": float(basis["fe_parallel_to_grain_psi_assumption"]),
            "perpendicular_endpoint_psi": float(basis["fe_perpendicular_to_grain_psi_assumption"]),
            "Fe_by_member_psi": fe_by_member,
            "angle_method": "NDS-2024 §12.3.4 Equation 12.3-11 Hankinson form via pinned dfl_dowel_bearing_psi helper",
        },
        "conditional_six_mode_reference": {
            "method_inputs": {
                "diameter_full_body_smooth_shank_in": diam_in,
                "main_member": MEMBER_MAIN,
                "side_member": MEMBER_SIDE,
                "main_bearing_length_in": main_length_in,
                "side_bearing_length_in": side_length_in,
                "interface_gap_in": float(basis["interface_gap_in"]),
                "bolt_bending_yield_psi": fyb,
                "theta_max_deg_for_reduction_term": theta,
                "theta_factor": ktheta,
                "end_grain_factor_Ceg_applied": False,
            },
            "yield_values_lbf": yields_lbf,
            "unadjusted_references_lbf": references_lbf,
            "unadjusted_references_N": references_n,
            "independent_mode_IV_reference_lbf": direct_iv_lbf,
            "governing_mode": mode,
            "governing_unadjusted_reference_N": references_n[mode],
            "raw_individual_bolt_demand_over_reference_by_mode": ratios,
            "raw_governing_demand_over_unadjusted_reference": demand / references_n[mode],
            "not_a_design_DCR": True,
        },
        "same_state_outer_seat_tie_out_of_lateral_reference": {
            "source_connection_name": tie["source_connection_name"],
            "force_on_side_spine_xyz_N": tie_side,
            "force_on_main_post_xyz_N": tie_main,
            "magnitude_N": tie_magnitude,
            "retained_same_case_load_factor_and_bolt": True,
            "combined_with_lateral_reference": False,
        },
    }


def produce() -> tuple[dict[str, Any], dict[str, Any]]:
    local_pins = pin_sources()
    method = load_module("reviewed_resultant_direction_method", SOURCES["resultant_direction_method"])
    nds = method.load_module("bg001_three_case_nds_method", method.NDS_PRODUCER)
    fe_helper = method.load_module("bg001_three_case_fe_helper", method.FE_HELPER)
    signed, _pins, loaded = source_demands(method)
    profile = json.loads(SOURCES["profile_query"].read_text(encoding="utf-8"))
    geometry = loaded["method_sources"]["geometry"]
    basis = loaded["method_sources"]["bg001_source"]["conditional_single_bolt_basis"]
    grains = loaded["method_sources"]["grain_by_member"]

    nds_source = loaded["method_sources"]["nds_scenarios"].get("sources", {}).get("NDS_2024_chapter_12", {})
    if (nds_source.get("url") != NDS_PDF["url"]
            or nds_source.get("downloaded_pdf_sha256") != NDS_PDF["sha256"]):
        raise ValueError("pinned NDS-2024 primary-source URL or checksum changed")

    if profile.get("candidate") != "compact-floor-flush-wood-joints-development" or profile.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError("finished-profile query does not bind the reviewed candidate geometry")
    # The profile query embeds exact STEP, geometry helper, and source-manifest pins.
    profile_embedded = profile.get("source_sha256_verified", {})
    for path, digest in profile_embedded.items():
        if path == "manifest_embedded_manifest_sha256":
            continue
        absolute = ROOT / path
        if not absolute.is_file() or sha256(absolute) != digest:
            raise ValueError(f"profile query embedded source pin mismatch: {path}")

    geometry_axes = {row["axis_id"]: row for row in geometry["candidate_axes"] if row.get("group_id") == "BG001"}
    if set(geometry_axes) != set(EXPECTED_AXES):
        raise ValueError("pinned geometry does not have the two reviewed BG001 axes")
    if (not close(float(basis["diameter_in"]), 0.25)
            or len(basis["main_and_side_bearing_lengths_in"]) != 2
            or any(not close(float(value), 1.5) for value in basis["main_and_side_bearing_lengths_in"])
            or float(basis["interface_gap_in"]) != 0.0
            or int(basis["bolt_bending_yield_psi_assumption"]) != 45000
            or float(basis["wood_specific_gravity_scenario"]) != 0.50
            or float(basis["fe_parallel_to_grain_psi_assumption"]) != 5600
            or float(basis["fe_perpendicular_to_grain_psi_assumption"]) != 4450
            or "full-body smooth" not in basis["shank_assumption"]):
        raise ValueError("reviewed conditional BG001 reference basis changed")
    if not close(float(fe_helper.dfl_dowel_bearing_psi(0.25, 0.0)), 5600.0) or not close(float(fe_helper.dfl_dowel_bearing_psi(0.25, 90.0)), 4450.0):
        raise ValueError("pinned Fe helper no longer reproduces the recorded rounded endpoints")

    # The A1 extension must reproduce the prior unadjusted arithmetic exactly
    # at its two full-load vectors before any other case rows are accepted.
    old_screen = json.loads(SOURCES["a1_resultant_screen"].read_text(encoding="utf-8"))
    if old_screen.get("status") != "CONDITIONAL_UNADJUSTED_SINGLE_SHEAR_REFERENCES_ONLY" or old_screen.get("joint_accepted") is not False:
        raise ValueError("A1 comparison packet no longer retains its non-acceptance boundary")

    rows = loaded["rows"]
    records = [make_record(row, profile, geometry_axes, grains, basis, nds, fe_helper) for row in rows]
    records.sort(key=lambda row: (EXPECTED_CASES.index(row["case_id"]), EXPECTED_LOAD_FACTORS.index(row["load_factor"]), EXPECTED_AXES.index(row["axis_id"])))
    if len(records) != 42 or any(row["conditional_six_mode_reference"]["governing_mode"] != "IV" for row in records):
        raise ValueError("expected all 42 individual BG001 records and Mode IV governing")

    # Independently tie the A1 factor-one pair to the original source arithmetic.
    a1_old_rows = {row["axis_id"]: row for row in old_screen["rows"]}
    a1_full = [row for row in records if row["case_id"] == "a1-rear" and row["load_factor"] == 1.0]
    if {row["axis_id"] for row in a1_full} != set(EXPECTED_AXES):
        raise ValueError("A1 full-load paired rows are missing")
    for row in a1_full:
        old = a1_old_rows[row["axis_id"]]
        main = row["same_physical_bolt_lateral_action_pair"]["force_on_second_xyz_N"]
        old_force = old["force_on_members_xyz_N"][MEMBER_MAIN]
        assert_vector_close(main, old_force)
        if (not close(row["paired_lateral_resultant"]["resultant_demand_N"], old["lateral_resultant_N"])
                or not close(row["conditional_six_mode_reference"]["governing_unadjusted_reference_N"], old["unadjusted_reference_N"])
                or not close(row["conditional_six_mode_reference"]["raw_governing_demand_over_unadjusted_reference"], old["demand_to_unadjusted_reference"])):
            raise ValueError(f"A1 reference-method extension changed its full-load result: {row['axis_id']}")

    states = []
    for case in EXPECTED_CASES:
        for load_factor in EXPECTED_LOAD_FACTORS:
            bolt_rows = [row for row in records if row["case_id"] == case and row["load_factor"] == load_factor]
            if len(bolt_rows) != 2 or {row["axis_id"] for row in bolt_rows} != set(EXPECTED_AXES):
                raise ValueError(f"same-state BG001 two-bolt pair incomplete: {case}/{load_factor}")
            states.append({"case_id": case, "load_factor": load_factor, "bolt_rows": bolt_rows})

    final_rows = [row for row in records if row["load_factor"] == 1.0]
    final_summary = [
        {
            "case_id": row["case_id"],
            "axis_id": row["axis_id"],
            "resultant_demand_N": row["paired_lateral_resultant"]["resultant_demand_N"],
            "load_to_grain_angle_deg": row["receiver_direction_and_end_edge"][MEMBER_MAIN]["lateral_load_to_proposed_grain_angle_deg"],
            "Fe_psi_each_receiver": row["conditional_fe_basis"]["Fe_by_member_psi"],
            "governing_mode": row["conditional_six_mode_reference"]["governing_mode"],
            "raw_unadjusted_individual_bolt_reference_N": row["conditional_six_mode_reference"]["governing_unadjusted_reference_N"],
            "raw_demand_over_unadjusted_reference": row["conditional_six_mode_reference"]["raw_governing_demand_over_unadjusted_reference"],
            "same_state_axial_tie_magnitude_N_not_combined": row["same_state_outer_seat_tie_out_of_lateral_reference"]["magnitude_N"],
        }
        for row in final_rows
    ]
    peak = max(records, key=lambda row: row["conditional_six_mode_reference"]["raw_governing_demand_over_unadjusted_reference"])

    # All end and edge rays are queried at three axial stations in the existing
    # finished source profile; dimensions remain geometry, not inspection.
    profile_inventory = {
        axis: {
            member: profile_distances(profile, axis, member)
            for member in (MEMBER_MAIN, MEMBER_SIDE)
        }
        for axis in EXPECTED_AXES
    }

    document = {
        "schema": "current_bg001_three_case_resultant_reference/v1",
        "status": "CONDITIONAL_RAW_INDIVIDUAL_BOLT_REFERENCES_ONLY",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "source_state_inventory": {
            "signed_register_path": rel(SOURCES["signed_demands"]),
            "signed_register_sha256": EXPECTED["signed_demands"],
            "authenticated_accepted_reports": {
                case: {"path": rel(path), "sha256": EXPECTED[name]}
                for case, (name, path) in {
                    "a1-rear": ("report_a1", SOURCES["report_a1"]),
                    "a12-rear": ("report_a12", SOURCES["report_a12"]),
                    "k12-rear": ("report_k12", SOURCES["report_k12"]),
                }.items()
            },
            "case_ids": list(EXPECTED_CASES),
            "load_factors": list(EXPECTED_LOAD_FACTORS),
            "case_load_states": 21,
            "BG001_per_state_physical_bolts": 2,
            "BG001_paired_bolt_state_records": len(records),
            "full_signed_register_plane_states": signed["plane_state_count"],
        },
        "conditional_reference_basis": {
            "source_path": rel(SOURCES["bg001_conditional_basis"]),
            "wood": "DF-L No. 2, SG 0.50 proposed scenario; not stock observation",
            "grain_axes": {
                MEMBER_MAIN: grains[MEMBER_MAIN],
                MEMBER_SIDE: grains[MEMBER_SIDE],
                "source_status": "proposed geometry/material-map directions, not observed wood",
            },
            "bolt_axis": "modeled global X; lateral actions are in the transverse Y-Z plane",
            "diameter_in": float(basis["diameter_in"]),
            "bearing_lengths_in_main_side": [float(x) for x in basis["main_and_side_bearing_lengths_in"]],
            "interface_gap_in": float(basis["interface_gap_in"]),
            "bolt_bending_yield_psi": float(basis["bolt_bending_yield_psi_assumption"]),
            "Fe_endpoints_psi_parallel_perpendicular": [float(basis["fe_parallel_to_grain_psi_assumption"]), float(basis["fe_perpendicular_to_grain_psi_assumption"])],
            "shank": "full-body smooth 1/4-inch diameter assumed through both receiver bearing lengths",
            "actual_stock_or_hardware_observed": False,
        },
        "method_applicability": {
            "resultant_yield_method": "Same two-member single-shear setup as the A1 reference packet. Both receiver grain axes remain global +Z; bolt axes remain global X; all accepted candidate-bolt lateral actions remain bolt-normal. NDS 2024 §12.3.4 angle-dependent Fe and the six §12.3.1 yield modes therefore apply to each signed Y/Z resultant under the stated conditional inputs.",
            "fe_angle_equation": "NDS-2024 §12.3.4 Equation 12.3-11 (Hankinson form), using the existing pinned angle helper and recorded rounded 5600/4450 psi endpoints.",
            "reference_scope": "One lateral Y/Z resultant per physical bolt, compared only with that bolt's six unadjusted single-shear references. No planes, component capacities, bolts, or independent maxima are summed.",
            "mode_change_from_A1": "None in connection topology, bolt-axis orientation, receiver roles, proposed grains, diameter, bearing lengths, gap, or conditional Fyb/Fe basis. Only source case/load factor and resultant direction/magnitude vary.",
            "edge_end_limit": "All rows have both a nonzero grain-parallel and nonzero cross-grain force component. NDS-2024 Table 12.5.1A lists parallel tension/compression and perpendicular-to-grain end cases but the pinned Chapter 12 PDF has no Commentary C12.5.1.2; therefore no oblique-grain CΔ interpolation is adopted. §12.5.1.2(b)'s loading-at-an-angle-to-fastener-axis shear-area case does not apply: these actions are bolt-normal, although oblique to grain.",
            "edge_detailing": "Signed cross-grain components select candidate loaded-edge rays for geometry bookkeeping; opposing rays are recorded as opposite edges. Distances are compared numerically with Table 12.5.1C 4D/1.5D values only; no full mixed-direction edge/detailing acceptance or splitting conclusion follows.",
            "historical_commentary": "The official 2018 Commentary may support angle interpolation as historical method context, but this artifact does not treat it as verified 2024 Commentary or use it to adjust references.",
            "Ceg": "Not applied: proposed bolt axis is perpendicular to both receiver grain axes, not parallel to the main-member fibers as required by the end-grain-axis provision.",
            "same_state_tie": "The source's physical_bolt_outer_seat_tension action is retained on the same bolt/case/load-factor record; it is reported separately and not combined with the lateral reference.",
        },
        "geometry_profile": {
            "source_query_path": rel(SOURCES["profile_query"]),
            "source_query_sha256": EXPECTED["profile_query"],
            "method": "Pinned finished STEP ray query at three through-thickness stations; each selected terminal ray has one planar exterior face and a station-invariant distance.",
            "distance_basis": "proposed CAD profile distances from each bolt axis along +/- proposed grain and +/- e=grain cross bolt-axis; not inspected stock or manufacturing tolerance",
            "profile_distances_mm_by_axis_and_receiver": profile_inventory,
            "comparison_values_at_D_6_35_mm": {
                "Table_12_5_1A_parallel_softwood_tension_full_endpoint_7D_mm": 7.0 * 6.35,
                "Table_12_5_1A_parallel_softwood_tension_half_endpoint_3_5D_mm": 3.5 * 6.35,
                "Table_12_5_1A_perpendicular_or_parallel_compression_full_endpoint_4D_mm": 4.0 * 6.35,
                "Table_12_5_1A_perpendicular_or_parallel_compression_half_endpoint_2D_mm": 2.0 * 6.35,
                "Table_12_5_1C_loaded_edge_4D_mm": 4.0 * 6.35,
                "Table_12_5_1C_opposite_edge_1_5D_mm": 1.5 * 6.35,
                "status": "numeric table endpoint comparators only; no oblique-grain CΔ adoption or physical conformity claim",
            },
        },
        "records_by_same_case_load_state": states,
        "factor_one_individual_bolt_screen": final_summary,
        "largest_raw_individual_bolt_ratio_same_state": {
            "case_id": peak["case_id"],
            "load_factor": peak["load_factor"],
            "axis_id": peak["axis_id"],
            "resultant_demand_N": peak["paired_lateral_resultant"]["resultant_demand_N"],
            "unadjusted_reference_N": peak["conditional_six_mode_reference"]["governing_unadjusted_reference_N"],
            "raw_ratio": peak["conditional_six_mode_reference"]["raw_governing_demand_over_unadjusted_reference"],
            "same_state_tie_magnitude_N_reported_separately": peak["same_state_outer_seat_tie_out_of_lateral_reference"]["magnitude_N"],
            "note": "This is a single physical-bolt row from one accepted state, not a combined or group comparison.",
        },
        "checks": {
            "all_local_source_hashes_match": True,
            "all_embedded_finished_profile_source_hashes_match": True,
            "register_contains_all_168_authenticated_plane_states": True,
            "BG001_contains_42_bolt_rows_across_21_case_load_states": True,
            "both_lateral_receiver_actions_close_in_every_row": True,
            "all_lateral_forces_are_normal_to_pinned_global_X_bolt_axes": True,
            "same_bolt_plane_records_match_register_action_pairs": True,
            "same_state_ties_close_and_match_source_magnitudes_in_every_row": True,
            "all_profile_rays_have_three_station_invariant_planar_terminals": True,
            "A1_factor_one_reproduces_existing_reference_resultant_screen": True,
            "all_six_modes_computed_for_each_individual_bolt_row": True,
            "independent_mode_IV_calculation_matches_every_row": True,
            "all_42_raw_governing_references_are_mode_IV": True,
        },
        "remaining_gates": [
            "No adopted/applicable oblique-grain NDS-2024 CΔ end-distance interpretation has been verified for these vectors; retain raw references without CΔ adjustment.",
            "No applicable mixed-direction BG001 Cg/group action is established; the existing row-alignment method rejects the actual resultant directions.",
            "No bolt tension/axial-seat plus lateral interaction, washer/seat resistance, or same-bolt combined action check is included.",
            "No NDS splitting, local tension-perpendicular, row/group tear-out, net-section, shear, or cross-grain failure resistance is established from these individual-bolt ratios.",
            "No load-duration, wet-service, temperature, or other adjustment factors are applied; actual grade, species, moisture, bolt shank/thread placement, bore, and fit are unobserved.",
            "These references are not adjusted capacities, design DCRs, joint passes, candidate acceptance, fabrication approval, or climbing release.",
        ],
        "source_sha256": local_pins,
        "external_source_pins": {"nds_2024_chapter_12": NDS_PDF, "2018_commentary_historical_only": HISTORICAL_COMMENTARY},
        "joint_accepted": False,
    }
    source_pins_document = {
        "schema": "current_bg001_three_case_resultant_reference_source_pins/v1",
        "local_sha256": local_pins,
        "external_primary_source": NDS_PDF,
        "historical_context_only": HISTORICAL_COMMENTARY,
        "method_scope": "The NDS-2024 Chapter 12 checksum and identity are reused from the reviewed scenario packet; no claim that its Chapter 12 PDF contains Commentary is made.",
    }
    return document, source_pins_document


def serialized(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    document, pins = produce()
    expected_outputs = {
        HERE / "screen.json": serialized(document),
        HERE / "source-pins.json": serialized(pins),
    }
    if args.write:
        for path, content in expected_outputs.items():
            path.write_text(content, encoding="utf-8")
        print("Wrote the 42-row BG001 source-bound three-case resultant screen.")
    else:
        for path, content in expected_outputs.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"artifact differs from deterministic source recomputation: {path}")
        print("Verified source pins, 21 same-state pairs, all six modes, tie bindings, profile rays, A1 reproduction and output bytes.")


if __name__ == "__main__":
    main()
