#!/usr/bin/env python3
"""Reproduce the bounded, source-bound BG001 NDS Cg scenarios.

This driver binds inputs for mini_moonboard.nds_2024_group_action without
reimplementing its equation. It intentionally produces no resistance or
acceptance result. All writes are confined to this attempt directory.
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


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
REL = HERE.relative_to(ROOT).as_posix()

GEOMETRY_PATH = "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/bolt-groups/bolt-groups.json"
MEMBER_SCENARIOS_PATH = f"{REL}/member-section-scenarios.json"
FASTENER_SCENARIO_PATH = "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/nds-screen/single-bolt-scenarios.json"
UNIT_ACTION_PATH = f"{REL}/unit-global-z-lateral-action.json"
COORDINATOR_PATH = f"{REL}/coordinator-inputs.json"
HELPER_PATH = "mini_moonboard/nds_2024_group_action.py"

MATERIAL_DOC_PATH = "docs/wood-joints-mvp/current-material-scenarios.md"
BASE_MATERIAL_MAP_PATH = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json"
SPINE_MATERIAL_MAP_PATH = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/material-frame-map.json"
FRAME_MANIFEST_PATH = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
SINGLE_BOLT_SCREEN_PATH = f"{REL.rsplit('/', 1)[0]}/current-knee-post-conditional-bolt-screen-attempt01/conditional-screen.json"
CDELTA_PROFILE_PATH = f"{REL.rsplit('/', 1)[0]}/current-knee-finished-profile-attempt01/README.md"

PINNED_HASHES = {
    GEOMETRY_PATH: "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4",
    FASTENER_SCENARIO_PATH: "130041246af11fc8e3568a7091f585d0d75581b2e1fbb3a3f4b97b750d68a7ea",
    HELPER_PATH: "121ec9d5399aa3e856b4038232e6d61c628aac42ce2addf8d1ff7e3a0e4c3df9",
    MATERIAL_DOC_PATH: "dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4",
    BASE_MATERIAL_MAP_PATH: "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409",
    SPINE_MATERIAL_MAP_PATH: "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480",
    FRAME_MANIFEST_PATH: "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    SINGLE_BOLT_SCREEN_PATH: "adbedaceec692936dcd2b2393c04fc985c5590a1a5a557b74868cee94eb3175c",
    CDELTA_PROFILE_PATH: "7cd5a76210e5e9343a115829167472a4d11f53738efcc42b57d156f9fcc23f29",
}

EXPECTED_AXIS_IDS = ("knee_outer_left_post_1", "knee_outer_left_post_2")
EXPECTED_MEMBER_IDS = ("base_post_outer_left", "knee_outer_left_spine")
EXPECTED_SCENARIO_IDS = (
    "BG001-globalZ-ring_R_on_X-conditional-E_L-1.6e6-psi",
    "BG001-globalZ-ring_R_on_T-conditional-E_L-1.6e6-psi",
)
EXPECTED_SINGLE_BOLT_REFERENCE_N = 796.2621976511778


def fail(message: str) -> None:
    raise RuntimeError(message)


def close(actual: float, expected: float, *, abs_tol: float = 1.0e-9) -> bool:
    return math.isclose(actual, expected, rel_tol=0.0, abs_tol=abs_tol)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(relative_path: str) -> str:
    return sha256_bytes((ROOT / relative_path).read_bytes())


def read_json(relative_path: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"expected JSON object at {relative_path}")
    return value


def strict_canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256_bytes(encoded)


def unit(vector: list[float]) -> list[float]:
    length = math.sqrt(sum(component * component for component in vector))
    if not math.isfinite(length) or length == 0.0:
        fail("invalid zero or non-finite geometry direction")
    return [component / length for component in vector]


def load_reviewed_helper():
    expected_sha = PINNED_HASHES[HELPER_PATH]
    actual_sha = file_sha256(HELPER_PATH)
    if actual_sha != expected_sha:
        fail(f"reviewed helper hash drift: expected {expected_sha}, got {actual_sha}")
    spec = importlib.util.spec_from_file_location(
        "reviewed_nds_2024_group_action", ROOT / HELPER_PATH
    )
    if spec is None or spec.loader is None:
        fail("could not load reviewed NDS group-action helper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify_source_hashes() -> dict[str, str]:
    observed: dict[str, str] = {}
    for path, expected in PINNED_HASHES.items():
        actual = file_sha256(path)
        if actual != expected:
            fail(f"source hash drift for {path}: expected {expected}, got {actual}")
        observed[path] = actual

    local_pins = read_json(MEMBER_SCENARIOS_PATH)["source_pins"]
    for source in local_pins.values():
        path = source["path"]
        expected = source["sha256"]
        actual = file_sha256(path)
        if actual != expected:
            fail(f"member scenario source pin drift for {path}")
        observed[path] = actual

    for path in (MEMBER_SCENARIOS_PATH, UNIT_ACTION_PATH):
        observed[path] = file_sha256(path)
    return observed


def validate_member_scenarios() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    scenarios = read_json(MEMBER_SCENARIOS_PATH)
    frame_map = read_json(BASE_MATERIAL_MAP_PATH)
    block_map = read_json(SPINE_MATERIAL_MAP_PATH)
    manifest = read_json(FRAME_MANIFEST_PATH)
    material_text = (ROOT / MATERIAL_DOC_PATH).read_text(encoding="utf-8")
    if "1.6 × 10^6 psi" not in material_text or "E_L" not in material_text:
        fail("pinned material document no longer states the named E_L scenario")

    frame_members = {member["member_id"]: member for member in frame_map["members"]}
    block_members = {member["part_id"]: member for member in block_map["members"]}
    physical = {member["member_id"]: member for member in manifest["physical_members"]}
    step_bindings = {
        member["member_id"]: member
        for member in manifest["finished_member_step_bindings"]
    }

    input_members = {member["member_id"]: member for member in scenarios["members"]}
    if set(input_members) != set(EXPECTED_MEMBER_IDS):
        fail("conditional member-section scenario member identity drift")
    if input_members[EXPECTED_MEMBER_IDS[0]]["role"] != "main":
        fail("main-member role mismatch")
    if input_members[EXPECTED_MEMBER_IDS[1]]["role"] != "side":
        fail("side-member role mismatch")

    base_grain = frame_members[EXPECTED_MEMBER_IDS[0]]["conditional_grain_assignment"]["proposed_global_xyz"]
    spine_grain = block_members[EXPECTED_MEMBER_IDS[1]]["conditional_grain_assignment"]["grain_direction_global_xyz"]
    if base_grain != [0.0, 0.0, 1.0] or spine_grain != [0.0, 0.0, 1.0]:
        fail("BG001 source grain assignment changed from proposed +Z")

    expected_section = [38.1, 139.7]
    for member_id in EXPECTED_MEMBER_IDS:
        record = physical[member_id]
        bounds = record["reviewed_snapshot_summary"]["finished"]["min_xyz_mm"] + record["reviewed_snapshot_summary"]["finished"]["max_xyz_mm"]
        dims_xy = [bounds[3] - bounds[0], bounds[4] - bounds[1]]
        step = step_bindings[member_id]
        if any(not close(actual, expected, abs_tol=1.0e-8) for actual, expected in zip(dims_xy, expected_section, strict=True)):
            fail(f"unexpected current finished section for {member_id}: {dims_xy}")
        if any(not close(actual, expected, abs_tol=1.0e-8) for actual, expected in zip(input_members[member_id]["modeled_section_mm"], dims_xy, strict=True)):
            fail(f"scenario section does not match pinned full-frame manifest for {member_id}")
        area_in2 = dims_xy[0] * dims_xy[1] / (25.4**2)
        if not close(area_in2, input_members[member_id]["gross_section_area_in2"], abs_tol=1.0e-12):
            fail(f"scenario gross area does not follow modeled section for {member_id}")
        if file_sha256(step["path"]) != step["file_sha256"]:
            fail(f"finished STEP hash mismatch for {member_id}")
        expected_grain = base_grain if member_id == EXPECTED_MEMBER_IDS[0] else spine_grain
        if input_members[member_id]["grain_axis_xyz"] != expected_grain:
            fail(f"grain scenario does not match the pinned material map for {member_id}")

    e_psi = scenarios["scenario_basis"]["elastic_modulus_psi"]
    if e_psi != 1600000 or scenarios["scenario_basis"]["actual_species_grade_or_modulus_observed"]:
        fail("material input is not the expected named conditional E_L scenario")

    block_ring_cases = {
        case["scenario_id"]: case["material_axes_global_xyz"]
        for case in block_members[EXPECTED_MEMBER_IDS[1]]["transverse_assignment_cases"]
    }
    local_ring_cases = {
        case["scenario_id"]: {
            "L": case["L_global_xyz"],
            "R": case["R_global_xyz"],
            "T": case["T_global_xyz"],
        }
        for case in scenarios["supported_transverse_orientation_cases"]
    }
    if set(block_ring_cases) != set(local_ring_cases):
        fail("supported transverse orientation scenario IDs changed")
    for scenario_id, axes in local_ring_cases.items():
        if axes != block_ring_cases[scenario_id]:
            fail(f"transverse orientation scenario drift for {scenario_id}")
        if axes["L"] != [0.0, 0.0, 1.0]:
            fail(f"longitudinal direction is not +Z in {scenario_id}")
    return scenarios, input_members, frame_map


def build_group_geometry() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source = read_json(GEOMETRY_PATH)
    axes = [
        axis for axis in source["candidate_axes"]
        if axis.get("group_id") == "BG001"
        and axis.get("axis_id") in EXPECTED_AXIS_IDS
    ]
    axes.sort(key=lambda item: item["axis_id"])
    if tuple(axis["axis_id"] for axis in axes) != EXPECTED_AXIS_IDS:
        fail("BG001 does not resolve to the two expected current axes")
    for axis in axes:
        member_pair = axis["receiver_member_ids"]
        if tuple(member_pair) != EXPECTED_MEMBER_IDS:
            fail("BG001 receiver member IDs changed")
        if axis["receiver_member_count"] != 2:
            fail("BG001 member count changed")
        bolt_axis = axis["axis_head_to_nut_unit_global_xyz"]
        if not close(abs(bolt_axis[0]), 1.0) or abs(bolt_axis[1]) > 1.0e-8 or abs(bolt_axis[2]) > 1.0e-8:
            fail("BG001 modeled bolt axes are no longer parallel to global X")

    centers = [axis["shaft_center_global_xyz_mm"] for axis in axes]
    delta_mm = [centers[1][index] - centers[0][index] for index in range(3)]
    if abs(delta_mm[0]) > 1.0e-8 or abs(delta_mm[1]) > 1.0e-8 or delta_mm[2] <= 0.0:
        fail(f"BG001 axes do not form the expected vertical global-Z row: {delta_mm}")
    row_axis = unit(delta_mm)
    diameter_mm = axes[0]["modeled_shaft_diameter_mm"]
    if any(not close(axis["modeled_shaft_diameter_mm"], diameter_mm, abs_tol=1.0e-10) for axis in axes):
        fail("BG001 modeled shaft diameters are not uniform")
    diameter_in = diameter_mm / 25.4
    pitch_in = math.sqrt(sum(value * value for value in delta_mm)) / 25.4
    fasteners = []
    for axis, center in zip(axes, centers, strict=True):
        relative_in = [(center[index] - centers[0][index]) / 25.4 for index in range(3)]
        fasteners.append({
            "fastener_id": axis["axis_id"],
            "center_in": relative_in,
            "nominal_diameter_in": diameter_in,
            "type": "dowel",
        })
    if not close(pitch_in, delta_mm[2] / 25.4, abs_tol=1.0e-12):
        fail("derived BG001 pitch is not parallel to +Z")
    return {"row_axis_xyz": row_axis, "fasteners": fasteners}, axes


def expected_bindings_from_sources(observed_hashes: dict[str, str]) -> dict[str, Any]:
    return {
        "geometry": {
            "source_id": GEOMETRY_PATH,
            "sha256": observed_hashes[GEOMETRY_PATH],
        },
        "member_sections": {
            "source_id": MEMBER_SCENARIOS_PATH + "#conditional-geometry-and-E-scenarios-only",
            "sha256": observed_hashes[MEMBER_SCENARIOS_PATH],
            "main_member_id": EXPECTED_MEMBER_IDS[0],
            "side_member_ids": [EXPECTED_MEMBER_IDS[1]],
            "shear_planes": 1,
        },
        "fastener_product": {
            "source_id": FASTENER_SCENARIO_PATH + "#conditional-full-body-quarter-inch-scenario-not-delivered-product",
            "sha256": observed_hashes[FASTENER_SCENARIO_PATH],
        },
        "load_cases": {
            "source_id": UNIT_ACTION_PATH + "#direction-only-not-joint-demand",
            "sha256": observed_hashes[UNIT_ACTION_PATH],
        },
    }


def make_payloads(
    observed_hashes: dict[str, str],
    coordinator: dict[str, Any],
) -> list[dict[str, Any]]:
    scenario_doc, member_inputs, _ = validate_member_scenarios()
    group_geometry, _ = build_group_geometry()
    unit_case = read_json(UNIT_ACTION_PATH)
    if unit_case.get("is_actual_joint_demand") is not False:
        fail("unit global-Z case must remain direction-only, not an actual demand")
    if unit_case.get("lateral_resultant_xyz_lbf") != [0.0, 0.0, 1.0]:
        fail("unit global-Z helper direction case changed")

    actual_bindings = expected_bindings_from_sources(observed_hashes)
    expected_bindings = coordinator.get("expected_source_bindings")
    if actual_bindings != expected_bindings:
        fail("source-derived input bindings do not match the independent coordinator manifest")

    members: dict[str, Any] = {
        "main": {
            "member_id": EXPECTED_MEMBER_IDS[0],
            "material": "wood",
            "elastic_modulus_psi": scenario_doc["scenario_basis"]["elastic_modulus_psi"],
            "grain_axis_xyz": member_inputs[EXPECTED_MEMBER_IDS[0]]["grain_axis_xyz"],
            "gross_section_area_in2": member_inputs[EXPECTED_MEMBER_IDS[0]]["gross_section_area_in2"],
        },
        "side_members": [{
            "member_id": EXPECTED_MEMBER_IDS[1],
            "material": "wood",
            "elastic_modulus_psi": scenario_doc["scenario_basis"]["elastic_modulus_psi"],
            "grain_axis_xyz": member_inputs[EXPECTED_MEMBER_IDS[1]]["grain_axis_xyz"],
            "gross_section_area_in2": member_inputs[EXPECTED_MEMBER_IDS[1]]["gross_section_area_in2"],
        }],
        "shear_planes": 1,
    }
    payloads = []
    ring_ids = [case["scenario_id"] for case in scenario_doc["supported_transverse_orientation_cases"]]
    for ring_id, scenario_id in zip(ring_ids, EXPECTED_SCENARIO_IDS, strict=True):
        payloads.append({
            "schema": "awc_nds_2024_group_action_input/v1",
            "candidate_id": "compact-floor-flush-wood-joints-development",
            "revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
            "group_id": "BG001",
            "scenario_id": scenario_id,
            "source_bindings": actual_bindings,
            "group_geometry": group_geometry,
            "load_case": {
                "case_id": unit_case["case_id"],
                "lateral_resultant_xyz_lbf": unit_case["lateral_resultant_xyz_lbf"],
            },
            "members": members,
        })
    return payloads


def load_single_bolt_and_cdelta() -> tuple[float, dict[str, Any]]:
    fastener = read_json(FASTENER_SCENARIO_PATH)
    screen = read_json(SINGLE_BOLT_SCREEN_PATH)
    profile_text = (ROOT / CDELTA_PROFILE_PATH).read_text(encoding="utf-8")
    if fastener["mechanical_acceptance"] is not False:
        fail("conditional full-body fastener input must remain non-acceptance evidence")
    if fastener["inputs"]["diameter_in"] != 0.25 or fastener["inputs"]["shank_basis"] != "Full-body smooth diameter throughout both bearing lengths":
        fail("conditional quarter-inch fastener scenario changed")
    row = next(
        item for item in screen["conditional_single_bolt_basis"]["scenarios"]
        if item["case_id"] == "global_z_lateral_load_parallel_to_proposed_grain"
    )
    reference_n = row["reference_lateral_N"]
    if not close(reference_n, EXPECTED_SINGLE_BOLT_REFERENCE_N, abs_tol=1.0e-9):
        fail("prior conditional single-bolt global-Z reference changed")
    if "4/7" not in profile_text or "5/7" not in profile_text or "reversed directions" not in profile_text:
        fail("pinned conditional Cdelta branch evidence not found")
    return reference_n, row


def produce() -> dict[str, Any]:
    observed_hashes = verify_source_hashes()
    coordinator = read_json(COORDINATOR_PATH)
    if coordinator.get("schema") != "conditional_group_factor_coordinator_inputs/v1":
        fail("unsupported coordinator manifest schema")
    helper = load_reviewed_helper()
    payloads = make_payloads(observed_hashes, coordinator)
    expected_records = {
        item["scenario_id"]: item["expected_payload_sha256"]
        for item in coordinator["group_records"]
    }
    if set(expected_records) != set(EXPECTED_SCENARIO_IDS):
        fail("coordinator record identities do not match the supported sensitivity cases")

    outputs = []
    for payload in payloads:
        scenario_id = payload["scenario_id"]
        independently_computed_digest = strict_canonical_sha256(payload)
        helper_computed_digest = helper.canonical_group_record_sha256(payload)
        if independently_computed_digest != helper_computed_digest:
            fail(f"independent/helper canonical digest mismatch for {scenario_id}")
        expected_digest = expected_records[scenario_id]
        if expected_digest == "TBD":
            fail("coordinator expected payload digest is unfinished")
        if independently_computed_digest != expected_digest:
            fail(f"payload digest does not match independent coordinator record for {scenario_id}")

        result = helper.evaluate_group_action_factor(
            payload,
            expected_bindings=coordinator["expected_source_bindings"],
            expected_payload_sha256=expected_digest,
        )
        if result.get("status") != "calculated_method_only" or result.get("capacity") is not None or result.get("criterion_disposition") != "pending":
            fail(f"reviewed helper did not return the bounded Cg-only result: {result}")
        outputs.append({
            "scenario_id": scenario_id,
            "ring_orientation_scenario_id": scenario_id.split("-conditional", 1)[0].replace("BG001-globalZ-", ""),
            "input_record": payload,
            "independent_payload_sha256": independently_computed_digest,
            "helper_result": result,
        })

    single_bolt_n, single_bolt_row = load_single_bolt_and_cdelta()
    cg_values = [row["helper_result"]["cg"] for row in outputs]
    main_ea = [row["helper_result"]["main_ea_lbf"] for row in outputs]
    side_ea = [row["helper_result"]["side_ea_lbf"] for row in outputs]
    if not all(close(value, 1.0, abs_tol=1.0e-12) for value in cg_values):
        fail(f"matched conditional BG001 cases did not reproduce Cg=1: {cg_values}")
    if any(not close(a, b, abs_tol=1.0e-8) for a, b in zip(main_ea, side_ea, strict=True)):
        fail("conditional member EA terms are not matched")
    if not close(max(cg_values) - min(cg_values), 0.0, abs_tol=1.0e-12):
        fail("supported R/T cases unexpectedly changed Cg")

    delta_cases = [
        {
            "branch_id": "opposed-parallel-grain-tension-end-distance",
            "c_delta": 4.0 / 7.0,
            "source_location": "current-knee-finished-profile-attempt01/README.md; post end 4D controls over spine end 5D",
        },
        {
            "branch_id": "reversed-parallel-grain-tension-end-distance",
            "c_delta": 1.0,
            "source_location": "current-knee-finished-profile-attempt01/README.md; reversed sampled ends exceed 7D",
        },
    ]
    reference_sensitivity = []
    for delta in delta_cases:
        for row in outputs:
            cg = row["helper_result"]["cg"]
            reference_sensitivity.append({
                "ring_orientation_scenario_id": row["ring_orientation_scenario_id"],
                "end_distance_branch_id": delta["branch_id"],
                "cg": cg,
                "c_delta": delta["c_delta"],
                "single_bolt_reference_N": single_bolt_n,
                "cg_c_delta_scaled_single_bolt_reference_N": cg * delta["c_delta"] * single_bolt_n,
                "classification": "Cg/Cdelta-only scaled individual-bolt reference; not adjusted resistance, group capacity, or criterion result",
            })

    geometry, axes = build_group_geometry()
    pitch_mm = math.sqrt(sum(
        (axes[1]["shaft_center_global_xyz_mm"][i] - axes[0]["shaft_center_global_xyz_mm"][i]) ** 2
        for i in range(3)
    ))
    coordinator_hash = file_sha256(COORDINATOR_PATH)
    return {
        "artifact": "BG001 current-knee post conditional NDS group-action factor screen",
        "status": "reproduced_conditional_method_row_result_only",
        "candidate_id": "compact-floor-flush-wood-joints-development",
        "revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "priority_scope": "BG001 new block attachment between base_post_outer_left and knee_outer_left_spine; the 12 retained baseline frame-bolt arrangements are separate and not requalified here",
        "method": {
            "helper_path": HELPER_PATH,
            "helper_sha256": PINNED_HASHES[HELPER_PATH],
            "scope": "Reviewed AWC NDS 2024 Eq. 11.3-1 Cg method only for one uniform straight row of same-diameter dowels and two members.",
            "not_produced": ["fastener resistance", "group capacity", "bolt force sharing", "demand/capacity", "criterion disposition"],
        },
        "coordinator_contract": {
            "path": COORDINATOR_PATH,
            "sha256": coordinator_hash,
            "expected_bindings_are_separately_supplied": True,
            "expected_payload_digests_are_static_in_manifest": True,
            "authority_note": "Hash equality is a reproducibility contract and does not independently establish source authority or engineering review.",
        },
        "geometry_summary": {
            "source_path": GEOMETRY_PATH,
            "source_sha256": observed_hashes[GEOMETRY_PATH],
            "axis_ids": [axis["axis_id"] for axis in axes],
            "modeled_shaft_diameter_mm": axes[0]["modeled_shaft_diameter_mm"],
            "bolt_axis_global": "+X",
            "group_row_axis_global": geometry["row_axis_xyz"],
            "pitch_mm": pitch_mm,
            "pitch_in": outputs[0]["helper_result"]["uniform_pitch_in"],
            "actual_joint_force_supplied": False,
        },
        "supported_material_area_sensitivity": {
            "source_basis": "DF-L No. 2 E_L=1.6e6 psi diagnostic scenario; both current receiver sections 38.1 x 139.7 mm (8.25 in^2 gross); both proposed grain axes +Z; actual stock not observed.",
            "rows": [
                {
                    "ring_orientation_scenario_id": row["ring_orientation_scenario_id"],
                    "main_EA_lbf": row["helper_result"]["main_ea_lbf"],
                    "side_EA_lbf": row["helper_result"]["side_ea_lbf"],
                    "Cg": row["helper_result"]["cg"],
                }
                for row in outputs
            ],
            "Cg_range": [min(cg_values), max(cg_values)],
            "Cg_absolute_spread": max(cg_values) - min(cg_values),
            "interpretation": "The supported R/T ring orientations do not change longitudinal E_L for the +Z-aligned action; equal modeled gross areas and the same conditional E_L give matched EA. For N=2 with matched EA the Eq. 11.3-1 expression algebraically reduces to Cg=1; no numerical unequal-E or unequal-area sensitivity is source-supported here, so none is fabricated.",
        },
        "scenario_results": outputs,
        "single_bolt_reference_source": {
            "screen_path": SINGLE_BOLT_SCREEN_PATH,
            "screen_sha256": PINNED_HASHES[SINGLE_BOLT_SCREEN_PATH],
            "fastener_scenario_path": FASTENER_SCENARIO_PATH,
            "fastener_scenario_sha256": observed_hashes[FASTENER_SCENARIO_PATH],
            "reference_case_id": single_bolt_row["case_id"],
            "reference_lateral_N": single_bolt_n,
            "classification": "conditional unadjusted individual-bolt reference under full-body quarter-inch scenario; source does not represent a delivered product",
        },
        "end_distance_branches": {
            "source_path": CDELTA_PROFILE_PATH,
            "source_sha256": PINNED_HASHES[CDELTA_PROFILE_PATH],
            "branches": delta_cases,
            "signed_branch_selection": "No accepted signed joint wrench is present; retain both conditional branches and do not select one as controlling for an actual case.",
        },
        "cg_cdelta_only_reference_envelope": {
            "rows": reference_sensitivity,
            "limits": [
                "These values only multiply the existing individual-bolt reference by the helper's Cg and the conditional end-distance Cdelta.",
                "They are not adjusted group capacity, not an NDS design value, and not a pass/fail comparison.",
                "Do not multiply by two or infer accepted equal bolt force sharing.",
            ],
        },
        "minimum_pending_inputs": [
            "Accepted signed BG001 cut wrench [F_x, V_y, V_z, M_x, M_y, M_z] at the modeled group midpoint [-1208.151, -137.6, 192.475] mm global XYZ, with load case, cut side, coordinate/sign convention, and source; the unit +Z vector here is direction-only, not a force demand.",
            "Delivered fastener identity and dimensions (including shank/thread layout), actual holes, gap, bearing planes, and effective engagement; the full-body 1/4-inch shaft is scenario-only.",
            "Actual receiver species/grade, moisture and applicable design/property adjustments; proposed grain and DF-L No. 2 E_L are conditional inputs, not observed stock.",
            "Verified hole centers plus each receiver's loaded/unloaded edge and end distances, row spacing and local net section, with signed load direction, to close spacing, splitting, row-shear and tear-out checks.",
            "Washer/head/nut dimensions and bearing/seating, axial tie and contact behavior, and a verified load path through downstream members; Cg does not qualify these modes or the complete joint.",
        ],
        "compatibility_exclusions": {
            "action_class": "Only the +Z lateral direction is passed to the Cg helper. No actual force or moment is supplied.",
            "bolt_axis_global": "+X",
            "axial_Fx_and_separation": "Not included; requires bolt tension, washer/nut bearing, anchorage and contact checks.",
            "My": "Not included; a possible axial couple across the Z pitch is unqualified without tension and anchorage transfer.",
            "Mz": "A collinear-Z bolt pair has no axial-force lever arm for Mz; transfer would require unresolved contact, bearing or other geometry.",
            "other_lateral_and_torsional_actions": "Vy and Mx demand mapping from the prior conditional packet is separate; no combined-action equation is evaluated here.",
        },
        "source_hashes_checked": observed_hashes,
    }


def write_results(result: dict[str, Any]) -> Path:
    output = HERE / "conditional-group-factor.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="recompute and compare the checked-in result")
    parser.add_argument("--write-results", action="store_true", help="write only conditional-group-factor.json")
    parser.add_argument("--print-input-digests", action="store_true", help="print canonical input record digests for coordinator audit")
    args = parser.parse_args()

    try:
        if args.print_input_digests:
            hashes = verify_source_hashes()
            coordinator = read_json(COORDINATOR_PATH)
            payloads = make_payloads(hashes, coordinator)
            for payload in payloads:
                print(payload["scenario_id"], strict_canonical_sha256(payload))
            return 0
        result = produce()
        output = HERE / "conditional-group-factor.json"
        if args.write_results:
            write_results(result)
            print(f"wrote {output.relative_to(ROOT)}")
            return 0
        if args.verify:
            if not output.exists():
                fail("conditional-group-factor.json does not exist; run --write-results once")
            current = json.loads(output.read_text(encoding="utf-8"))
            if current != result:
                fail("stored conditional group-factor packet differs from reproduced result")
            print("BG001 conditional Cg result and source bindings verified")
            return 0
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except (KeyError, IndexError, OSError, ValueError, TypeError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
