#!/usr/bin/env python3
"""Produce a source-pinned Step 6 tool/operation feasibility screen."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = next(
    parent
    for parent in HERE.parents
    if (parent / "site/owner-wood-joints-wj24-scene.json").is_file()
)
DOCS = REPO / "docs/wood-joints-mvp"
EVAL = DOCS / "hypotheses/evaluation-resume-2026-09-24"
REGISTER_PATH = (
    EVAL
    / "step6-operation-coverage-attempt01/operation-coverage.json"
)
ACCESS_PATH = EVAL / "access-screen-attempt03-exact-components.json"
CAPTURE_PATH = EVAL / "captured-nut-motion-attempt02/motion.json"
RETAINED_PATH = EVAL / "retained-access-attempt03/access.json"
WIRE_NOTE_PATH = DOCS / "current-retained-wire-sequence.md"
OUTPUT_PATH = HERE / "tool-route-feasibility.json"

GEOMETRY_ID = "led-clearance-2x6-runner-seated-blocks-v1"
TARGET_AXES = (
    "bottom_center/clip_horizontal_bottom_left_2/rail_2",
    "bottom_center/clip_horizontal_bottom_right_1/rail_2",
    "bottom_outer/clip_horizontal_bottom_left_1/rail_2",
    "bottom_outer/clip_horizontal_bottom_right_2/rail_2",
)
FRAME_AXES = (
    "lumber_leg_bolt_left_1",
    "lumber_leg_bolt_left_2",
    "lumber_leg_bolt_right_1",
    "lumber_leg_bolt_right_2",
)

INPUTS = (
    REGISTER_PATH,
    ACCESS_PATH,
    CAPTURE_PATH,
    RETAINED_PATH,
    DOCS / "current-access-screen.md",
    DOCS / "current-hardware-schedule.md",
    DOCS / "current-bolt-thread-boundary-screen-2026-09-27.md",
    WIRE_NOTE_PATH,
    REPO / "docs/led-wiring-reference.json",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def relative(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def one_by(items: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {item[key]: item for item in items}


def hit_rows(access: dict[str, Any]) -> list[dict[str, Any]]:
    rows = one_by(access["axis_operations"], "axis_id")
    hits: list[dict[str, Any]] = []
    for axis_id in TARGET_AXES:
        row = rows[axis_id]
        for role in ("nut", "nut_washer"):
            operation = row["operations"][role]
            screen = operation["removal"]["collision_screen"]
            hit_map = screen["external_envelope_hits_mm3"]
            intersections = [
                {"blocker_id": blocker, "volume_mm3": volume}
                for blockers in hit_map.values()
                for blocker, volume in blockers.items()
            ]
            if intersections:
                hits.append(
                    {
                        "axis_id": axis_id,
                        "component_role": role,
                        "travel_mm": operation["derived_axial_travel_mm"],
                        "screen_result": "proxy_envelope_intersection",
                        "intersections": intersections,
                        "physical_access_established": screen[
                            "physical_access_established"
                        ],
                        "thread_disengagement_established": False,
                    }
                )
    return hits


def captured_rows(captured: dict[str, Any]) -> list[dict[str, Any]]:
    rows = one_by(captured["axis_operations"], "axis_id")
    result: list[dict[str, Any]] = []
    for axis_id in TARGET_AXES:
        row = rows[axis_id]
        clear_options = [
            option
            for option in row["lateral_then_axial_options"]
            if option["two_stage_cad_motion_clear"]
        ]
        result.append(
            {
                "axis_id": axis_id,
                "headward_bolt_travel_mm": row["headward_travel_mm"],
                "headward_terminal_allowance_mm": row[
                    "headward_terminal_allowance_mm"
                ],
                "clear_local_option_count": len(clear_options),
                "clear_local_option": (
                    {
                        "lateral_displacement_xyz_mm": clear_options[0][
                            "lateral_displacement_xyz_mm"
                        ],
                        "following_nutward_displacement_xyz_mm": clear_options[0][
                            "following_nutward_displacement_xyz_mm"
                        ],
                        "following_nutward_travel_mm": 25.0,
                        "external_geometry_clear": clear_options[0][
                            "lateral_collision"
                        ]["external_envelope_clear"]
                        and clear_options[0]["following_nutward_collision"][
                            "external_envelope_clear"
                        ],
                    }
                    if len(clear_options) == 1
                    else None
                ),
                "shaft_nut_display_envelope_overlap_mm3": row[
                    "shaft_nut_display_envelope_initial_overlap_mm3"
                ],
                "thread_compatible_unthreading_assumed": True,
                "nut_and_washer_capture_established": False,
                "full_part_staging_established": False,
                "reverse_assembly_screened": False,
            }
        )
    return result


def retained_rows(retained: dict[str, Any]) -> list[dict[str, Any]]:
    rows = one_by(retained["axis_operations"], "axis_id")
    result: list[dict[str, Any]] = []
    for axis_id in FRAME_AXES:
        op = rows[axis_id]["operations"]["head_side_bolt"]
        screen = op["withdrawal"]["collision_screen"]
        hit_map = screen["external_envelope_hits_mm3"]
        components = []
        for component_name, blockers in hit_map.items():
            for blocker, volume in blockers.items():
                components.append(
                    {
                        "component_sweep": component_name,
                        "blocker_id": blocker,
                        "intersection_volume_mm3": volume,
                    }
                )
        result.append(
            {
                "axis_id": axis_id,
                "modeled_withdrawal_mm": op["derived_travel_mm"],
                "motion_direction": op["withdrawal"]["motion_direction"],
                "component_intersections": components,
                "modeled_wire_overlap_count": len(components),
                "physical_cable_blockage_established": False,
                "flexible_cable_service_route_established": False,
                "reverse_insertion_screened": True,
                "reverse_insertion_physical_route_established": False,
            }
        )
    return result


def proxy_rows(register: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {row["entity_id"]: row for row in register["axis_records"]}
    result: list[dict[str, Any]] = []
    for axis_id in TARGET_AXES + FRAME_AXES:
        row = by_id[axis_id]
        sides = {}
        for side, profile in row["tool_proxy_screens"].items():
            sides[side] = {
                "candidate_id": profile["profile_source"]["candidate_id"],
                "manufacturer": profile["profile_source"]["manufacturer"],
                "profile_is_current_selected_tool_or_fit": profile[
                    "profile_source"]["profile_is_current_selected_tool_or_fit"
                ],
                "approach_proxy_clear_count": profile["approach_proxy"][
                    "proxy_clear_count"
                ],
                "approach_proxy_check_count": profile["approach_proxy"]["checks"],
                "turn_pose_clear_count": profile["discrete_turn_pose_proxies"][
                    "proxy_clear_count"
                ],
                "turn_pose_check_count": profile["discrete_turn_pose_proxies"][
                    "checks"
                ],
                "scope": profile["scope"],
            }
        result.append({"axis_id": axis_id, "sides": sides})
    return result


def build() -> dict[str, Any]:
    register = read_json(REGISTER_PATH)
    access = read_json(ACCESS_PATH)
    captured = read_json(CAPTURE_PATH)
    retained = read_json(RETAINED_PATH)
    for source in (register, access, captured, retained):
        if source.get("geometry_revision_id") not in (None, GEOMETRY_ID):
            raise ValueError("Unexpected geometry revision in a pinned input")

    slides = hit_rows(access)
    if len(slides) != 6:
        raise ValueError(f"Expected six direct candidate slide hits, got {len(slides)}")
    captured_result = captured_rows(captured)
    if any(row["clear_local_option_count"] != 1 for row in captured_result):
        raise ValueError("Expected one selected clear local motion per target axis")
    wires = retained_rows(retained)
    if any(row["modeled_wire_overlap_count"] != 3 for row in wires):
        raise ValueError("Expected three retained wire-sweep intersections per axis")

    pins = [
        {
            "path": relative(path),
            "sha256": sha256(path),
        }
        for path in INPUTS
    ]
    return {
        "schema": "mini-moonboard.step6-tool-route-feasibility.v1",
        "screen_id": "step6-tool-route-feasibility-attempt01",
        "screened_on": "2026-09-27",
        "geometry_revision_id": GEOMETRY_ID,
        "status": "no_complete_reversible_route_demonstrated",
        "scope": {
            "geometry_or_axes_changed": False,
            "existing_operation_register_edited": False,
            "cad_or_solver_run": False,
            "physical_operation_performed": False,
            "purpose": "Assess whether cited source geometry and public tool evidence establish a reversible tool/operation route for the six candidate slide overlaps and four retained frame-bolt/wire withdrawals.",
        },
        "input_pins": pins,
        "candidate_nut_slide_hits": {
            "direct_axial_hit_count": len(slides),
            "axis_count": len({row["axis_id"] for row in slides}),
            "basis": "Current exact-component source BRep axial-slide report; zero terminal allowance; thread motion omitted.",
            "hits": slides,
        },
        "candidate_captured_nut_local_route": {
            "status": "local_source_cad_path_clear_after_assumed_unthreading",
            "sequence": [
                "Unthread the nut in place while counterholding the bolt; neither operation has been screened for a selected hardware stack/tool pair.",
                "Capture the nut and nut washer at their seats; no capture method or support is modeled.",
                "Withdraw head, head washer, and shaft 151.368 mm headward (150.368 mm source travel plus a diagnostic 1 mm terminal allowance).",
                "Translate the captured nut/washer pair laterally by the axis-specific vector.",
                "Continue 25 mm nutward; this is only a local continuation, not a verified hand-accessible staging location.",
            ],
            "rows": captured_result,
            "source_limit": "Existing CAD report checks rigid modeled part envelopes only. It retains all external scene geometry but treats coaxial shaft/boreless-nut overlap as unchanged under assumed thread release. It does not check thread disengagement, tool access, capture, support, staging, or the reverse sequence.",
            "reverse_sequence_status": "not_demonstrated",
        },
        "blocker_removal_alternative": {
            "status": "not_screened",
            "members": [
                {
                    "member_id": member_id,
                    "candidate_fastener_axes": [
                        row["entity_id"]
                        for row in register["axis_records"]
                        if row["record_type"] == "candidate_bolt_stack"
                        and member_id in row.get("receiver_ids", [])
                    ],
                }
                for member_id in (
                    "center_principal_cleat_left",
                    "center_principal_cleat_right",
                    "knee_outer_left_inner_frame_block",
                    "knee_outer_right_inner_frame_block",
                )
            ],
            "missing_checks": [
                "block fastener tool access and reversible removal",
                "block bodily extraction and insertion path",
                "supported frame state while each blocker is absent",
                "replacement sequence with the unchanged final geometry and axes",
            ],
        },
        "retained_frame_bolt_wire_hits": {
            "axis_count": len(wires),
            "component_sweep_hit_count": sum(
                row["modeled_wire_overlap_count"] for row in wires
            ),
            "wire_span_ids": [
                "protected/wires/wire_010_A10_A11",
                "protected/wires/wire_130_K10_K11",
            ],
            "rows": wires,
            "service_sequence_status": "hypothesis_only",
            "service_sequence_note": "The wire-follow-up note proposes isolating/staging string 1 and the installed portion of string 3, but requires actual boundary connectors, the PWR1 branch route, fixation/slack/bend data, and a refeeding/reconnection path. The model's 18-LED unused-tail arithmetic also differs from the manufacturer's 16-spare text. The manufacturer guide describes installation through push-fit connectors and damaged-LED replacement by cutting/splicing; it does not specify reversible whole-string service removal.",
        },
        "tool_profile_candidates": [
            {
                "id": "facom_34_7_16",
                "manufacturer": "FACOM",
                "size": "7/16 in",
                "type": "double open-end midget wrench, 15 and 75 degree inclined heads",
                "published_profile": {
                    "head_width_mm": 22.0,
                    "head_thickness_mm": 3.0,
                    "overall_length_mm": 100.0,
                },
                "evidence": ["FACOM official product page", "FACOM official inch-series dimension table"],
                "disposition": "Real manufacturer profile matches dimensions of the existing synthetic proxy, but the full wrench shape is not modeled and the tool is not selected. Existing proxy rows still have approach/turn intersections on target axes.",
                "numeric_torque_capacity_published_in_cited_record": False,
            },
            {
                "id": "wera_6000_05073282001",
                "manufacturer": "Wera",
                "size": "7/16 in",
                "type": "ratcheting combination wrench",
                "published_profile": {
                    "overall_length_mm": 165.0,
                    "open_end_external_width_mm": 25.0,
                    "open_end_thickness_mm": 6.3,
                    "ring_end_width_mm": 22.0,
                    "ring_end_max_height_mm": 7.5,
                    "open_end_return_angle_degrees": 30,
                    "ring_teeth": 80,
                },
                "disposition": "Could match a selected 1/4-20 hex stack of the cited 7/16 across-flats type. Its larger/thicker profile has not been fit-screened; the cited page gives no numeric torque capacity.",
                "numeric_torque_capacity_published_in_cited_record": False,
            },
            {
                "id": "wera_6000_05073287001",
                "manufacturer": "Wera",
                "size": "3/4 in",
                "type": "ratcheting combination wrench",
                "published_profile": {
                    "overall_length_mm": 246.0,
                    "open_end_external_width_mm": 42.0,
                    "open_end_thickness_mm": 9.5,
                    "ring_end_width_mm": 34.8,
                    "ring_end_max_height_mm": 11.0,
                    "open_end_return_angle_degrees": 30,
                    "ring_teeth": 80,
                },
                "disposition": "Relevant size comparator for the current 1/2-13 lumber-leg bolt catalog reference, whose listed hex head is 3/4 in across flats. This real profile is much larger than the reused 7/16 synthetic wrench proxy; no fit or torque screen exists.",
                "numeric_torque_capacity_published_in_cited_record": False,
            },
        ],
        "separated_operation_findings": {
            "geometric_path": "The direct candidate nut/nut-washer axial path has six source-solid intersections. The existing captured-nut diagnostic clears one local lateral-then-axial option per affected axis, but it does not reach a hand-accessible staging position. The four frame-bolt sweeps intersect modeled wire segments; those fixed-wire intersections do not prove that real flexible cable blocks withdrawal.",
            "tool_fit_and_torque": "No selected hardware or tool. The current proxy uses a 7/16 in FACOM envelope. FACOM publishes a 7/16 thin wrench profile; Wera publishes 7/16 and 3/4 combination-wrench dimensions and small-angle behavior. None has a current geometry-fit result or a numeric tool torque limit in the cited records.",
            "thread_disengagement": "The four candidate axes are in the current 152.4 mm ordinary-length category. The thread-boundary note's conditional 1/4-20 class comparison places the earliest nut bearing plane 4.7592 mm short of LG,max. Catalog class limits/minimum thread length do not establish delivered full-thread/runout coordinates or matched-nut functional engagement; unthreading travel is unproven.",
            "counterhold": "The register screens head and nut ends separately and assigns no simultaneous turning/counterhold pair, hand workspace, force, or target tightening torque.",
            "part_capture_and_staging": "The captured-nut motion assumes the nut/washer remain captured at the receiver and then travel together. No restraint, catch, hand clearance, or destination is represented; the 25 mm segment is not full extraction.",
            "flex_wire_handling": "Wire centerline-solid hits identify two affected spans. The candidate service stage needs both end-string areas and a verified reversible connector/LED/panel route. Current dimensions, connectors, attachments, slack, bend radius, and PWR1 extension placement are not qualified.",
            "reversibility": "The captured-nut report does not screen reverse assembly with selected parts/tools. Wire restoration/reconnection is likewise not defined. No complete reversible route is demonstrated.",
        },
        "minimum_missing_evidence": [
            "Selected, matched bolt/nut/washer products for the four candidate axes, with delivered dimensions and thread-transition bounds (first complete thread, last thread scratch/runout, tip, and matched nut active-thread/chamfer bounds) sufficient to prove full engagement and disengagement.",
            "Selected correctly sized tools for both turning and counterhold sides, complete manufacturer profiles or measured tool geometry, exact approach and motion clearances at the affected axes, and an assigned installation/removal torque or force method.",
            "A continuous captured-part route from the nut seat through the existing lateral/axial escape to a reachable restrained staging point, plus a separately screened reverse installation path and support-transfer sequence.",
            "If blocker removal is the chosen alternative, a reversible member-removal/insertion path for each center/knee blocker, its own accessible fasteners, and supported frame states; no such member-motion sequence is screened here.",
            "For the retained frame bolts, the exact harness/connector BOM and boundary/PWR1 routing, attachments and strain reliefs, free slack and bend limits, a manufacturer-supported disconnect/refeed procedure, part restraint during service, and a staged-scene withdrawal/reverse-insertion check.",
            "A correctly sized 3/4 in tool profile and simultaneous counterhold/access screen for the four retained 1/2 in lumber-leg bolts; the existing 7/16 in proxy is not the scheduled catalog-reference head size.",
        ],
        "existing_synthetic_tool_proxy_rows": proxy_rows(register),
        "public_sources": [
            {
                "id": "facom_34_7_16_product",
                "publisher": "FACOM",
                "url": "https://www.facom.com/product/34716/double-open-end-wrench-34-midget-15-and-75-inclined-ends-716",
                "supports": "34.7/16 product identity, 15/75 degree inclined heads, 100 mm length, ASME B107.100.",
                "checked": "2026-09-27",
            },
            {
                "id": "facom_34_inch_dimensions",
                "publisher": "FACOM France",
                "url": "https://www.facom.fr/products/34-cles-a-fourches-micromecanique-tetes-inclinees-en-pouces",
                "supports": "34.7/16 table dimensions: 22 mm head width, 3 mm thickness, 100 mm length.",
                "checked": "2026-09-27",
            },
            {
                "id": "wera_6000_imperial",
                "publisher": "Wera",
                "url": "https://www.wera.de/en/tools/6000-joker-ratcheting-combination-wrenches-imperial",
                "supports": "7/16 and 3/4 in wrench sizes, dimensions, 30 degree open-end return angle, 80-tooth ring ratchet.",
                "checked": "2026-09-27",
            },
            {
                "id": "boltdepot_2569",
                "publisher": "Bolt Depot",
                "url": "https://boltdepot.com/Product-Details?product=2569",
                "supports": "Unselected 1/4-20 Grade 5 nut comparator: 7/16 in across flats and nominal 7/32 in height.",
                "checked": "2026-09-27",
            },
            {
                "id": "boltdepot_407",
                "publisher": "Bolt Depot",
                "url": "https://boltdepot.com/Product-Details?product=407",
                "supports": "Unselected 1/2-13 Grade 5 bolt comparator: 3/4 in head across flats; schedule reference only.",
                "checked": "2026-09-27",
            },
            {
                "id": "moonboard_led_v5_guide",
                "publisher": "Moon Climbing",
                "url": "https://moonclimbing.com/media/moonboard-pdf/MB_LED_Installation_V5%2050%20LED%20Nov%202025.pdf",
                "supports": "String installation uses push-fit connectors; the damaged-LED repair procedure cuts and splices; no whole-string reversible service procedure is specified.",
                "checked": "2026-09-27",
            },
        ],
        "conclusion": "The current evidence supports two bounded hypotheses: a local captured-nut geometric escape on four candidate axes, and a possible flexible-wire service state for four retained frame-bolt axes. Exact tool fit/torque, thread release, counterhold, component capture/staging, harness service, and the reverse sequence remain unestablished. No geometry-safe reversible operation clear can be recorded from the available sources.",
    }


def rendered() -> bytes:
    return (json.dumps(build(), indent=2, sort_keys=True) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    expected = rendered()
    if args.write:
        OUTPUT_PATH.write_bytes(expected)
        print(f"wrote {relative(OUTPUT_PATH)} sha256={hashlib.sha256(expected).hexdigest()}")
        return 0
    actual = OUTPUT_PATH.read_bytes()
    if actual != expected:
        raise SystemExit("tool-route-feasibility.json is stale; run produce.py --write")
    print(f"verified {relative(OUTPUT_PATH)} sha256={hashlib.sha256(actual).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
