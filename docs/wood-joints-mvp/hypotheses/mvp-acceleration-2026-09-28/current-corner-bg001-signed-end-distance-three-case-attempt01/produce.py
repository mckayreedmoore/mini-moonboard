#!/usr/bin/env python3
"""Source-bound BG001 historical C_delta sensitivity across accepted cases."""

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
SERVICE = ROOT / "docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30"
OUTPUT = HERE / "screen.json"
PINS_OUTPUT = HERE / "source-pins.json"

SOURCES = {
    "three_case_producer": BASE / "current-bg001-three-case-resultant-reference-attempt01/produce.py",
    "three_case_screen": BASE / "current-bg001-three-case-resultant-reference-attempt01/screen.json",
    "three_case_source_pins": BASE / "current-bg001-three-case-resultant-reference-attempt01/source-pins.json",
    "legacy_signed_end_producer": BASE / "current-corner-bg001-signed-end-distance-attempt01/produce.py",
    "legacy_signed_end_screen": BASE / "current-corner-bg001-signed-end-distance-attempt01/signed-end-distance-screen.json",
    "legacy_signed_end_readme": BASE / "current-corner-bg001-signed-end-distance-attempt01/README.md",
    "legacy_signed_end_sums": BASE / "current-corner-bg001-signed-end-distance-attempt01/SHA256SUMS",
    "method_correction": SERVICE / "method-correction.md",
    "historical_end_branch_helper": SERVICE / "end_branch.py",
    "historical_end_branch_freeze": SERVICE / "end-branch-freeze.json",
    "profile_query": BASE / "current-knee-finished-profile-attempt01/query.json",
    "bolt_groups": BASE / "bolt-groups/bolt-groups.json",
    "group_action_helper": ROOT / "mini_moonboard/nds_2024_group_action.py",
}

EXPECTED_SHA256 = {
    "three_case_producer": "7af02f47ef059efb2ac583cd52d451c14b88044e089f47a37f9b10312d3581b6",
    "three_case_screen": "fe7cbb6f211dd35f2aa68b23819446b5f832cc4fcc16f0ac7635bd883a20ce2f",
    "three_case_source_pins": "d20a4ae22f3abc16a9df38556102226372831c08a754400217454eeffd1e062a",
    "legacy_signed_end_producer": "cdd69ff54c031c5b2cadd9771525ee9860234752bd6b667d8c4ef06787412348",
    "legacy_signed_end_screen": "04df4147f276e1b866b076ea428d5d16e31007219653e395990aa2083a2d239e",
    "legacy_signed_end_readme": "8e67b392102de7399c74b6f806700333964027ceaf6d6df4ee6710f534de7af2",
    "legacy_signed_end_sums": "9ccba2d606ef4ef109b0142ab8a9493c6f52d67c7f8fa604ed03f278d8a2e89a",
    "method_correction": "ad31605a35a1090928cb4911b745a880aed86c1170d600e55d66b3cdc95a8983",
    "historical_end_branch_helper": "958270887b128e70a0d763ae318182c014fa63a038b74dc8529a1a794c97ad47",
    "historical_end_branch_freeze": "48a3cf0e5f03134d99abf0bf1d2e0d18cd141d2f0bc019949ec88169b3ca21b1",
    "profile_query": "32d3eb326cbd4e12e91f10418f340f2a9f21509f593e3f91421f10ae6aa574d2",
    "bolt_groups": "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4",
    "group_action_helper": "121ec9d5399aa3e856b4038232e6d61c628aac42ce2addf8d1ff7e3a0e4c3df9",
}

EXPECTED_CASES = ("a1-rear", "a12-rear", "k12-rear")
EXPECTED_AXES = ("knee_outer_left_post_1", "knee_outer_left_post_2")
EXPECTED_LOAD_FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
POST = "base_post_outer_left"
SPINE = "knee_outer_left_spine"
MEMBERS = (POST, SPINE)
TOL = 1.0e-8
MM_PER_IN = 25.4

NDS_2024 = {
    "title": "ANSI/AWC NDS-2024, Chapter 12 specification",
    "url": "https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf",
    "sha256": "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a",
    "scope": "Pinned public Chapter 12 specification text only; it contains no Commentary C12.5.1.2 or verified oblique-grain tension-end interpolation wording.",
}
HISTORICAL_COMMENTARY = {
    "title": "ANSI/AWC NDS-2018 Commentary, Chapter 12",
    "url": "https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf",
    "sha256": "3402c7703cddef3e6693741ebaef9bfd0c1b0ddf075762c6f411fe1916751f7d",
    "printed_page": 263,
    "use": "Historical primary-source support for the angle interpolation and end-distance tension-branch definition (fasteners bearing toward the member end); neither is promoted to an NDS-2024 requirement.",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def close(a: float, b: float, tol: float = TOL) -> bool:
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def norm(vector: list[float]) -> float:
    return math.hypot(*vector)


def unit(vector: list[float]) -> list[float]:
    magnitude = norm(vector)
    require(math.isfinite(magnitude) and magnitude > 0.0, "finite nonzero vector required")
    return [component / magnitude for component in vector]


def dot(left: list[float], right: list[float]) -> float:
    return math.fsum(a * b for a, b in zip(left, right, strict=True))


def cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load pinned helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify_direct_source_pins() -> dict[str, str]:
    observed = {}
    for name, path in SOURCES.items():
        require(path.is_file(), f"pinned source missing: {path}")
        actual = sha256(path)
        require(actual == EXPECTED_SHA256[name],
                f"source pin mismatch {name}: expected {EXPECTED_SHA256[name]}, got {actual}")
        observed[relative(path)] = actual
    return observed


def add_transitive_pins(observed: dict[str, str], pins: dict[str, str]) -> None:
    for path, digest in pins.items():
        absolute = ROOT / path
        require(absolute.is_file(), f"transitive pinned source missing: {path}")
        actual = sha256(absolute)
        require(actual == digest, f"transitive source pin mismatch {path}")
        if path in observed:
            require(observed[path] == actual, f"conflicting source digest for {path}")
        observed[path] = actual


def validate_replayed_inputs(observed: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any], Any, Any, Any]:
    current_module = load_module("bg001_three_case_pinned_replay", SOURCES["three_case_producer"])
    current_document, current_pins = current_module.produce()
    stored_current = load_json(SOURCES["three_case_screen"])
    stored_current_pins = load_json(SOURCES["three_case_source_pins"])
    require(stored_current == current_document, "three-case screen differs from its deterministic producer replay")
    require(stored_current_pins == current_pins, "three-case source pins differ from deterministic replay")
    require(current_document["source_state_inventory"]["case_ids"] == list(EXPECTED_CASES),
            "three-case inventory changed")
    require(current_document["source_state_inventory"]["load_factors"] == list(EXPECTED_LOAD_FACTORS),
            "three-case increment inventory changed")
    require(current_document["source_state_inventory"]["case_load_states"] == 21
            and current_document["source_state_inventory"]["BG001_paired_bolt_state_records"] == 42,
            "three-case inventory is not 21 states / 42 paired physical-bolt rows")
    require(current_document["joint_accepted"] is False,
            "source three-case packet acceptance boundary changed")
    require("no oblique-grain CΔ interpolation is adopted" in current_document["method_applicability"]["edge_end_limit"],
            "three-case source packet no longer records the 2024 CΔ evidence gap")
    add_transitive_pins(observed, current_pins["local_sha256"])

    legacy_module = load_module("bg001_legacy_signed_end_replay", SOURCES["legacy_signed_end_producer"])
    legacy_document = legacy_module.build_screen()
    stored_legacy = load_json(SOURCES["legacy_signed_end_screen"])
    require(stored_legacy == legacy_document, "prior A12 signed-end screen differs from deterministic producer replay")
    require(legacy_document["case_id"] == "a12-rear"
            and legacy_document["mechanical_acceptance"] is False,
            "prior signed-end screen identity or acceptance boundary changed")
    add_transitive_pins(observed, legacy_document["input_provenance"]["source_sha256"])

    correction = " ".join(SOURCES["method_correction"].read_text(encoding="utf-8").split())
    freeze = load_json(SOURCES["historical_end_branch_freeze"])
    require(freeze["current_2024_commentary_interpolation_verified"] is False,
            "corrected method record no longer marks 2024 interpolation unverified")
    require(freeze["historical_interpolation_source"]["sha256"] == HISTORICAL_COMMENTARY["sha256"]
            and freeze["historical_interpolation_source"]["url"] == HISTORICAL_COMMENTARY["url"]
            and freeze["historical_interpolation_source"]["status"].startswith("Official historical primary source"),
            "historical Commentary identity/source changed")
    require("The corresponding **2024 Commentary has not been directly verified**" in correction,
            "method-correction record does not preserve the exact 2024 source gap")
    require("does not adopt the historical interpolation as a current design rule" in correction,
            "method-correction record no longer limits use to sensitivity")

    end_module = load_module("bg001_historical_end_branch_helper", SOURCES["historical_end_branch_helper"])
    require(current_document["external_source_pins"]["nds_2024_chapter_12"]["sha256"] == NDS_2024["sha256"]
            and current_document["external_source_pins"]["nds_2024_chapter_12"]["url"] == NDS_2024["url"],
            "current primary NDS Chapter 12 identity changed")
    require("not Commentary" in current_document["external_source_pins"]["nds_2024_chapter_12"]["use"],
            "pinned NDS-2024 chapter scope changed")
    return current_document, legacy_document, current_module, legacy_module, end_module


def profile_inventory(profile: dict[str, Any], current_module: Any) -> dict[str, dict[str, dict[str, float]]]:
    result = {}
    for axis in EXPECTED_AXES:
        result[axis] = {}
        for member in MEMBERS:
            result[axis][member] = current_module.profile_distances(profile, axis, member)
    return result


def selected_profile_face(profile: dict[str, Any], axis: str, member: str, ray_label: str) -> dict[str, Any]:
    hits = [
        row for row in profile["rays"]
        if row["group_id"] == "BG001" and row["bolt_id"] == axis
        and row["member_id"] == member and row["ray_label"] == ray_label
    ]
    require(len(hits) == 3, f"expected 3 finished-profile axial stations: {axis}/{member}/{ray_label}")
    terminals = [row["terminal_face_candidates"] for row in hits]
    require(all(len(items) == 1 and items[0]["surface_type"] == "PLANE"
                and float(items[0]["abs_normal_dot_ray"]) >= 1.0 - 1.0e-8
                for items in terminals),
            f"loaded end is not a station-invariant orthogonal planar profile ray: {axis}/{member}/{ray_label}")
    distances = {float(row["center_to_last_material_exit_mm"]) for row in hits}
    require(len(distances) == 1, f"loaded end distance varies across thickness stations: {axis}/{member}/{ray_label}")
    return {
        "profile_ray": ray_label,
        "distance_mm": distances.pop(),
        "axial_station_labels": sorted(row["axial_station_label"] for row in hits),
        "terminal_face_indices_1based": [int(items[0]["face_index_1based"]) for items in terminals],
        "terminal_surface_types": [items[0]["surface_type"] for items in terminals],
        "terminal_abs_normal_dot_ray": [float(items[0]["abs_normal_dot_ray"]) for items in terminals],
    }


def member_end_sensitivity(
    action: list[float], grain: list[float], bolt_axis: list[float],
    axis_id: str, member_id: str, distances: dict[str, float], profile: dict[str, Any],
    legacy_module: Any, end_module: Any, diameter_mm: float,
) -> dict[str, Any]:
    action_norm = norm(action)
    require(action_norm > 0.0 and abs(action[0]) <= 1.0e-7,
            f"BG001 lateral force is zero or not bolt-normal: {axis_id}/{member_id}")
    grain_axis = unit(grain)
    e_axis = unit(cross(grain_axis, bolt_axis))
    grain_force = dot(action, grain_axis)
    cross_force = dot(action, e_axis)
    require(abs(grain_force) > 1.0e-9 and abs(cross_force) > 1.0e-9,
            f"signed grain/end or cross-grain component is zero: {axis_id}/{member_id}")
    angle_deg = math.degrees(math.atan2(abs(cross_force), abs(grain_force)))
    end_ray = "g+" if grain_force > 0.0 else "g-"
    profile_hit = selected_profile_face(profile, axis_id, member_id, end_ray)
    helper_distance = legacy_module.unique_profile_distance(profile, axis_id, member_id, end_ray)
    require(close(helper_distance, profile_hit["distance_mm"]),
            f"existing signed-end helper and direct profile ray disagree: {axis_id}/{member_id}")
    require(close(helper_distance, distances[end_ray]),
            f"existing profile-distance inventory disagrees: {axis_id}/{member_id}/{end_ray}")

    full_reference_mm = float(end_module.end_reference(diameter_mm, angle_deg))
    half_floor_mm = full_reference_mm / 2.0
    ratio = helper_distance / full_reference_mm
    require(ratio >= 0.5 - 1.0e-10,
            f"historical end branch falls below its 0.5 floor: {axis_id}/{member_id}")
    factor = min(1.0, ratio)
    return {
        "member_id": member_id,
        "force_xyz_N": action,
        "proposed_grain_unit_global_xyz": grain_axis,
        "cross_grain_axis_unit_global_xyz": e_axis,
        "signed_grain_parallel_force_N": grain_force,
        "signed_cross_grain_force_N": cross_force,
        "load_to_grain_angle_deg": angle_deg,
        "loaded_grain_end_ray": end_ray,
        "finished_profile_loaded_end": profile_hit,
        "modeled_nominal_diameter_mm": diameter_mm,
        "historical_method_full_tension_end_reference_mm": full_reference_mm,
        "historical_method_half_end_floor_mm": half_floor_mm,
        "profile_distance_over_historical_full_requirement": ratio,
        "historical_method_member_Cdelta_sensitivity": factor,
        "at_or_above_historical_half_floor": ratio >= 0.5,
        "historical_method_only_not_NDS_2024_adoption": True,
    }


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    observed = verify_direct_source_pins()
    current, legacy, current_module, legacy_module, end_module = validate_replayed_inputs(observed)
    profile = load_json(SOURCES["profile_query"])
    geometry = load_json(SOURCES["bolt_groups"])

    require(current["candidate"] == "compact-floor-flush-wood-joints-development"
            and current["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1",
            "current accepted case-bound screen candidate/revision changed")
    axes = {
        row["axis_id"]: row for row in geometry["candidate_axes"]
        if row.get("group_id") == "BG001"
    }
    require(set(axes) == set(EXPECTED_AXES), "pinned BG001 geometry axes changed")
    centers = [axes[axis]["shaft_center_global_xyz_mm"] for axis in EXPECTED_AXES]
    row_delta = [float(b) - float(a) for a, b in zip(centers[0], centers[1], strict=True)]
    row_axis = unit(row_delta)
    require(abs(row_axis[0]) <= TOL and abs(row_axis[1]) <= TOL and row_axis[2] >= 1.0 - TOL,
            "BG001 source centers no longer form the +Z bolt row")
    bolt_axes = {}
    for axis_id, row in axes.items():
        bolt_axis = unit([float(x) for x in row["axis_head_to_nut_unit_global_xyz"]])
        require(abs(abs(bolt_axis[0]) - 1.0) <= TOL and abs(bolt_axis[1]) <= TOL and abs(bolt_axis[2]) <= TOL,
                f"BG001 source bolt axis is no longer global X: {axis_id}")
        require(close(float(row["modeled_shaft_diameter_mm"]), 6.35),
                f"BG001 modeled nominal diameter differs: {axis_id}")
        bolt_axes[axis_id] = bolt_axis

    basis_diameter_in = float(current["conditional_reference_basis"]["diameter_in"])
    diameter_mm = basis_diameter_in * MM_PER_IN
    require(close(diameter_mm, 6.35), "conditional model diameter changed")
    require(all(close(float(axes[axis]["modeled_shaft_diameter_mm"]), diameter_mm) for axis in EXPECTED_AXES),
            "case reference basis and pinned finished geometry disagree on nominal bolt diameter")
    # The 2018 official Commentary supports this sensitivity formula. The
    # known answers are arithmetic oracles, not evidence of 2024 applicability.
    known_answers = {0.0: 44.45, 45.0: 34.925, 90.0: 25.4}
    for angle, answer in known_answers.items():
        require(close(float(end_module.end_reference(diameter_mm, angle)), answer, 1.0e-12),
                f"historical end-reference known answer changed at {angle} degrees")

    basis_grains = current["conditional_reference_basis"]["grain_axes"]
    grains = {member: unit([float(x) for x in basis_grains[member]]) for member in MEMBERS}
    require(all(abs(grains[member][2]) >= 1.0 - TOL for member in MEMBERS),
            "source-proposed BG001 grain is no longer global Z")
    profiles = profile_inventory(profile, current_module)

    all_rows = []
    state_rows = []
    for state in current["records_by_same_case_load_state"]:
        case = state["case_id"]
        load_factor = float(state["load_factor"])
        require(case in EXPECTED_CASES and load_factor in EXPECTED_LOAD_FACTORS,
                f"unexpected source case/increment: {case}/{load_factor}")
        bolt_rows = state["bolt_rows"]
        require(len(bolt_rows) == 2 and {row["axis_id"] for row in bolt_rows} == set(EXPECTED_AXES),
                f"same-state BG001 physical bolt pair incomplete: {case}/{load_factor}")
        member_rows = []
        state_force_sum = [0.0, 0.0, 0.0]
        for source_row in bolt_rows:
            axis_id = source_row["axis_id"]
            pair = source_row["same_physical_bolt_lateral_action_pair"]
            require(pair["force_pair_closes"] is True,
                    f"source bolt actions no longer close: {case}/{load_factor}/{axis_id}")
            action_by_member = {
                POST: [float(x) for x in pair["force_on_second_xyz_N"]],
                SPINE: [float(x) for x in pair["force_on_first_xyz_N"]],
            }
            require(all(close(action_by_member[POST][i], -action_by_member[SPINE][i], 1.0e-7)
                        for i in range(3)),
                    f"same-bolt receiver actions fail closure: {case}/{load_factor}/{axis_id}")
            for component in range(3):
                state_force_sum[component] += action_by_member[POST][component]

            reference = source_row["conditional_six_mode_reference"]
            require(reference["governing_mode"] == "IV"
                    and set(reference["unadjusted_references_N"]) == {"Im", "Is", "II", "IIIm", "IIIs", "IV"},
                    f"source raw-reference method changed: {case}/{load_factor}/{axis_id}")
            demand = float(source_row["paired_lateral_resultant"]["resultant_demand_N"])
            raw_reference = float(reference["governing_unadjusted_reference_N"])
            raw_ratio = float(reference["raw_governing_demand_over_unadjusted_reference"])
            require(close(demand / raw_reference, raw_ratio),
                    f"source raw individual-bolt ratio mismatch: {case}/{load_factor}/{axis_id}")

            member_end_rows = {}
            for member in MEMBERS:
                member_row = member_end_sensitivity(
                    action_by_member[member], grains[member], bolt_axes[axis_id],
                    axis_id, member, profiles[axis_id][member], profile,
                    legacy_module, end_module, diameter_mm,
                )
                # Reconcile signs and angles with the already accepted paired
                # three-case direction record before applying the historical formula.
                accepted_direction = source_row["receiver_direction_and_end_edge"][member]
                require(accepted_direction["loaded_grain_end_ray"] == member_row["loaded_grain_end_ray"]
                        and close(float(accepted_direction["lateral_load_to_proposed_grain_angle_deg"]),
                                  member_row["load_to_grain_angle_deg"])
                        and close(float(accepted_direction["loaded_grain_end_profile_distance_mm"]),
                                  member_row["finished_profile_loaded_end"]["distance_mm"]),
                        f"signed vector/profile differs from accepted source receiver branch: {case}/{load_factor}/{axis_id}/{member}")
                member_end_rows[member] = member_row

            bolt_minimum = min(
                member_end_rows[POST]["historical_method_member_Cdelta_sensitivity"],
                member_end_rows[SPINE]["historical_method_member_Cdelta_sensitivity"],
            )
            tie = source_row["same_state_outer_seat_tie_out_of_lateral_reference"]
            require(tie["combined_with_lateral_reference"] is False
                    and tie["retained_same_case_load_factor_and_bolt"] is True,
                    f"same-state physical-bolt axial tie no longer remains separate: {case}/{load_factor}/{axis_id}")
            member_rows.append({
                "case_id": case,
                "load_factor": load_factor,
                "axis_id": axis_id,
                "source_connection_name": source_row["source_connection_name"],
                "same_physical_bolt_lateral_action_pair": pair,
                "member_end_sensitivities": member_end_rows,
                "per_bolt_minimum_member_Cdelta_sensitivity": bolt_minimum,
                "raw_unadjusted_mode_IV_reference_N": raw_reference,
                "raw_lateral_resultant_demand_N": demand,
                "raw_demand_over_unadjusted_reference": raw_ratio,
                "same_state_axial_tie": {
                    "force_on_spine_xyz_N": tie["force_on_side_spine_xyz_N"],
                    "force_on_post_xyz_N": tie["force_on_main_post_xyz_N"],
                    "magnitude_N": float(tie["magnitude_N"]),
                    "kept_separate_from_lateral_resultant": True,
                },
                "cg_applied": False,
            })

        historical_group_min = min(row["per_bolt_minimum_member_Cdelta_sensitivity"] for row in member_rows)
        controlling_bolt = min(member_rows, key=lambda row: row["per_bolt_minimum_member_Cdelta_sensitivity"])
        controlling_member = min(
            controlling_bolt["member_end_sensitivities"].values(),
            key=lambda row: row["historical_method_member_Cdelta_sensitivity"],
        )
        group_action_sine = norm(cross(unit(state_force_sum), row_axis))
        require(group_action_sine > 1.0e-8,
                f"source BG001 group lateral resultant unexpectedly aligns with its bolt row: {case}/{load_factor}")
        require(all(row["same_state_axial_tie"]["kept_separate_from_lateral_resultant"] for row in member_rows),
                "same-state tie was combined with the lateral reference")
        for row in member_rows:
            sensitivity_reference = row["raw_unadjusted_mode_IV_reference_N"] * historical_group_min
            row["conditional_historical_group_min_Cdelta"] = historical_group_min
            row["conditional_historical_Cdelta_only_reference_N"] = sensitivity_reference
            row["conditional_historical_Cdelta_only_demand_over_reference"] = (
                row["raw_lateral_resultant_demand_N"] / sensitivity_reference
            )
            row["comparison_classification"] = (
                "historical-Commentary Cdelta-only individual-bolt reference sensitivity; "
                "not verified as NDS-2024, not an adjusted DCR or acceptance"
            )
            all_rows.append(row)
        state_rows.append({
            "case_id": case,
            "load_factor": load_factor,
            "provisional_group_scope": "both BG001 bolts and both receiver end branches in this same case/load-factor state",
            "historical_group_min_Cdelta_sensitivity": historical_group_min,
            "controlling_axis_id": controlling_bolt["axis_id"],
            "controlling_member_id": controlling_member["member_id"],
            "controlling_loaded_end_ray": controlling_member["loaded_grain_end_ray"],
            "controlling_end_distance_mm": controlling_member["finished_profile_loaded_end"]["distance_mm"],
            "controlling_load_to_grain_angle_deg": controlling_member["load_to_grain_angle_deg"],
            "conditional_group_lateral_resultant_on_post_xyz_N": state_force_sum,
            "sine_to_fastener_row": group_action_sine,
            "Cg_status": "pending",
            "Cg_reason_code": "load_direction_not_aligned_with_fastener_row",
            "bolt_rows": member_rows,
            "group_min_is_not_a_group_capacity": True,
        })

    require(len(state_rows) == 21 and len(all_rows) == 42,
            "expected exactly 21 state records and 42 same-state BG001 bolt rows")
    require([(row["case_id"], row["load_factor"]) for row in state_rows]
            == [(case, factor) for case in EXPECTED_CASES for factor in EXPECTED_LOAD_FACTORS],
            "case/load-factor state order or count changed")

    # A12 factor one is a known-answer arithmetic tie to the earlier two-bolt
    # screen. Its result is used only to check computation, not its superseded
    # claim that the interpolation had been verified for the 2024 Commentary.
    prior_a12 = {row["axis_id"]: row for row in legacy["signed_direction_results"]}
    prior_group_factor = float(legacy["group_angle_interpolated_Cdelta"])
    a12_state = next(row for row in state_rows if row["case_id"] == "a12-rear" and row["load_factor"] == 1.0)
    require(close(a12_state["historical_group_min_Cdelta_sensitivity"], prior_group_factor),
            "A12 factor-one group-min arithmetic no longer reproduces the previous conditional screen")
    for row in a12_state["bolt_rows"]:
        old = prior_a12[row["axis_id"]]
        for member in MEMBERS:
            require(close(row["member_end_sensitivities"][member]["historical_method_member_Cdelta_sensitivity"],
                          float(old["member_geometry"][member]["angle_interpolated_Cdelta"])),
                    f"A12 factor-one member Cdelta arithmetic mismatch: {row['axis_id']}/{member}")
        old_scale = next(item for item in legacy["reference_scalings"] if item["axis_id"] == row["axis_id"])
        require(close(row["conditional_historical_Cdelta_only_reference_N"],
                      float(old_scale["group_Cdelta_only_reference_N"]))
                and close(row["conditional_historical_Cdelta_only_demand_over_reference"],
                          float(old_scale["demand_over_group_Cdelta_only_reference"])),
                f"A12 factor-one scaled reference known-answer mismatch: {row['axis_id']}")

    factor_one = [row for row in all_rows if row["load_factor"] == 1.0]
    peak_raw = max(all_rows, key=lambda row: row["raw_demand_over_unadjusted_reference"])
    peak_sensitivity = max(all_rows, key=lambda row: row["conditional_historical_Cdelta_only_demand_over_reference"])
    producer_path = Path(__file__).resolve()
    observed[relative(producer_path)] = sha256(producer_path)
    checks = {
        "all_direct_source_hashes_match": True,
        "three_case_source_packet_replays_exactly": True,
        "legacy_A12_signed_end_packet_replays_exactly_arithmetic_only": True,
        "corrected_source_status_marks_2024_commentary_interpolation_unverified": True,
        "official_2018_commentary_identity_matches_corrected_method_record": True,
        "all_21_case_increment_states_have_both_physical_bolts": True,
        "all_42_same_bolt_receiver_force_pairs_close": True,
        "all_42_receiver_actions_are_bolt_normal": True,
        "all_84_loaded_end_ray_hits_are_three_station_invariant_square_planes": True,
        "all_84_historical_member_end_factors_meet_half_floor": True,
        "every_state_uses_minimum_over_both_bolts_and_both_receivers": True,
        "every_state_axial_tie_is_retained_separately": True,
        "A12_factor_one_group_min_and_scaled_references_reproduce_prior_screen": True,
        "all_21_group_lateral_resultants_are_oblique_to_fastener_row": True,
        "all_21_states_leave_Cg_pending": True,
        "no_Cg_applied": True,
        "no_NDS_2024_oblique_Cdelta_adopted": True,
        "no_adjusted_design_DCR_or_joint_acceptance_established": True,
    }
    document = {
        "schema": "current_bg001_signed_end_distance_three_case_sensitivity/v1",
        "status": "CONDITIONAL_HISTORICAL_CDELTA_SENSITIVITY_ONLY_CG_PENDING",
        "candidate": current["candidate"],
        "geometry_revision_id": current["geometry_revision_id"],
        "source_state_inventory": {
            "cases": list(EXPECTED_CASES),
            "load_factors": list(EXPECTED_LOAD_FACTORS),
            "same_case_load_factor_states": len(state_rows),
            "physical_BG001_bolts_per_state": 2,
            "paired_bolt_rows": len(all_rows),
        },
        "primary_source_status": {
            "NDS_2024_specification": NDS_2024,
            "exact_2024_commentary_interpolation_verified": False,
            "official_historical_commentary_interpolation_source": HISTORICAL_COMMENTARY,
            "method_application": "The angle formula and group-min arithmetic are replayed only as a historical-method sensitivity. They are not an adopted NDS-2024 Cdelta or design rule.",
            "branch_assumption": "Official 2018 Commentary C12.5.1.2, printed page 263, defines tension loads for end-distance requirements as fasteners bearing toward the member end. The signed receiver bearing force selects the modeled end toward which that receiver is loaded for this historical sensitivity. This does not establish the 2024 branch wording or applicability; member stress and local failure checks remain separate.",
            "source_gap": "The pinned official NDS-2024 Chapter 12 extract contains specification and table text but no Commentary C12.5.1.2. AWC's official 2024 NDS page lists Commentary only as part of its package. No exact authenticated 2024 commentary text supporting this interpolation was available in the reviewed packet.",
        },
        "conditional_geometry_and_reference_basis": {
            "group_id": "BG001",
            "axes": list(EXPECTED_AXES),
            "members": list(MEMBERS),
            "bolt_axis": "modeled global X",
            "row_axis_unit_global_xyz": row_axis,
            "proposed_grain_unit_global_xyz": grains,
            "modeled_nominal_diameter_mm": diameter_mm,
            "conditional_reference_method": "Existing case-bound paired resultant screen; six raw unadjusted NDS single-shear modes, Mode IV governs all 42 rows.",
            "end_distance_source": "Pinned current finished STEP profile query, three through-thickness stations; actual timber and continuous-span minima unobserved.",
            "group_min_scope": "For each simultaneous state, minimum historical sensitivity across both BG001 physical bolts and both receiver loaded-end branches; used only to scale each bolt's own raw reference.",
            "same_state_outer_seat_ties": "Preserved on each physical bolt/state and kept separate from lateral actions and references.",
        },
        "records_by_same_case_load_state": state_rows,
        "factor_one_same_state_individual_bolt_screen": [
            {
                "case_id": row["case_id"],
                "axis_id": row["axis_id"],
                "lateral_resultant_demand_N": row["raw_lateral_resultant_demand_N"],
                "raw_unadjusted_mode_IV_reference_N": row["raw_unadjusted_mode_IV_reference_N"],
                "raw_demand_over_unadjusted_reference": row["raw_demand_over_unadjusted_reference"],
                "state_group_min_historical_Cdelta_sensitivity": row["conditional_historical_group_min_Cdelta"],
                "historical_Cdelta_only_reference_sensitivity_N": row["conditional_historical_Cdelta_only_reference_N"],
                "historical_Cdelta_only_demand_over_reference_sensitivity": row["conditional_historical_Cdelta_only_demand_over_reference"],
                "same_state_axial_tie_magnitude_N_separate": row["same_state_axial_tie"]["magnitude_N"],
                "not_an_adjusted_DCR": True,
            }
            for row in factor_one
        ],
        "envelope_summaries": {
            "largest_raw_individual_bolt_ratio": {
                "case_id": peak_raw["case_id"],
                "load_factor": peak_raw["load_factor"],
                "axis_id": peak_raw["axis_id"],
                "ratio": peak_raw["raw_demand_over_unadjusted_reference"],
                "classification": "raw unadjusted individual-bolt comparison only",
            },
            "largest_historical_Cdelta_only_sensitivity_ratio": {
                "case_id": peak_sensitivity["case_id"],
                "load_factor": peak_sensitivity["load_factor"],
                "axis_id": peak_sensitivity["axis_id"],
                "group_min_Cdelta_sensitivity": peak_sensitivity["conditional_historical_group_min_Cdelta"],
                "ratio": peak_sensitivity["conditional_historical_Cdelta_only_demand_over_reference"],
                "classification": "historical-method sensitivity, not a design DCR or adopted NDS-2024 result",
            },
            "Cg": "pending for each state because the summed same-state lateral action is not aligned with the fastener row; no Cg or group capacity is applied",
        },
        "remaining_dependencies": [
            "Exact authenticated NDS-2024 Commentary C12.5.1.2 text or other official current-edition source confirming oblique-to-grain tension-end interpolation and its application to this load case; until then the calculated Cdelta values remain historical-method sensitivities only.",
            "A source-bound, applicable mixed-direction Cg/group-action method. All 21 summed lateral resultants are oblique to the global-Z fastener row, so the current reviewed row-aligned helper returns pending with load_direction_not_aligned_with_fastener_row.",
            "Complete NDS adjustment factors and verified wood species, grade, moisture/service conditions, delivered fastener dimensions/thread placement, actual bore and fit; none is included in these raw references.",
            "Same-bolt lateral plus axial outer-seat tie resistance and interaction, including head/nut/washer bearing and tension-path evidence; each source tie remains separate here.",
            "Member stress at connections, local splitting/tension-perpendicular, row/group tear-out, net section, member shear, and complete joint transfer remain separate uncomputed checks; no capacity is derived from the individual-bolt ratio or profile distance.",
            "Confirmed end-distance group membership and spacing applicability, observed stock/end dimensions, and continuous profile extrema; this packet uses only the scoped BG001 pair and the three pinned through-thickness profile stations.",
        ],
        "checks": checks,
        "source_sha256": dict(sorted(observed.items())),
        "joint_accepted": False,
        "adjusted_design_DCR_established": False,
        "NDS_2024_Cdelta_adopted": False,
        "Cg_applied": False,
    }
    pin_document = {
        "schema": "current_bg001_signed_end_distance_three_case_source_pins/v1",
        "local_sha256": dict(sorted(observed.items())),
        "external_primary_source": NDS_2024,
        "historical_interpolation_source_only": HISTORICAL_COMMENTARY,
        "source_boundary": "Historical 2018 Commentary supports the computed sensitivity; no inference that identical wording applies in NDS-2024.",
    }
    return document, pin_document


def serialize(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    document, pins = build()
    expected = {OUTPUT: serialize(document), PINS_OUTPUT: serialize(pins)}
    if args.write:
        for path, text in expected.items():
            path.write_text(text, encoding="utf-8")
        print(f"wrote {len(document['records_by_same_case_load_state'])} states / {document['source_state_inventory']['paired_bolt_rows']} BG001 bolt rows; historical Cdelta sensitivity only")
    else:
        for path, text in expected.items():
            require(path.is_file() and path.read_text(encoding="utf-8") == text,
                    f"deterministic replay differs from saved output: {path}")
        print("verified 21 paired states, 42 bolt rows, historical-method attribution, A12 known-answer, separate ties, and Cg pending")


if __name__ == "__main__":
    main()
