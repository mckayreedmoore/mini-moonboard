#!/usr/bin/env python3
"""Independent parent audit for the conditional T07/T08 envelope packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
E = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
PACKET = HERE / "critical-envelopes.json"
OUT = HERE / "parent-review.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_sha(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def pointer(value: object, path: str) -> object:
    current = value
    for part in path.lstrip("/").split("/") if path else []:
        part = part.replace("~1", "/").replace("~0", "~")
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def review() -> dict:
    packet = load(ROOT / PACKET)
    require(packet["status"] == "SOURCE_BOUND_NOMINAL_ENVELOPE_COMPARISON_ONLY", "packet scope/status changed")
    require(packet["source_authority"]["all_prior_physical_operation_gates_remain_open"] is True, "physical gate boundary changed")

    # Rehash the complete transitive source union independently of the producer.
    transitive = packet["source_authority"]["transitive_source_pins"]
    require(len(transitive) == 72, f"expected 72 unique transitive sources, got {len(transitive)}")
    source_paths = [row["path"] for row in transitive]
    require(len(set(source_paths)) == len(source_paths), "transitive source list contains duplicate paths")
    for row in transitive:
        require(sha(ROOT / row["path"]) == row["sha256"], f"transitive source changed: {row['path']}")

    t07_review = load(ROOT / E / "current-fit-transport-closeout-attempt02/parent-review.json")
    cross_review = load(ROOT / E / "current-fit-transport-option-crosswalk-attempt01/parent-review.json")
    t08_review = load(ROOT / E / "current-hardware-material-cost-closeout-attempt01/parent-review.json")
    require(t07_review["status"] == packet["source_authority"]["T07_parent_status"], "T07 review status mismatch")
    require(cross_review["status"] == packet["source_authority"]["crosswalk_parent_status"], "crosswalk review status mismatch")
    require(t08_review["status"] == packet["source_authority"]["T08_parent_status"], "T08 review status mismatch")
    require(cross_review["status"] == "PASS_SOURCE_BOUND_OPTION_CROSSWALK_ONLY_ALL_PHYSICAL_GATES_OPEN", "crosswalk is not identity-only pass")

    evidence_path = E / "current-fit-transport-closeout-attempt02/evidence-register.json"
    tool_path = E / "step6-operation-coverage-attempt01/tool-route-feasibility-attempt01/tool-route-feasibility.json"
    access_path = E / "access-screen-attempt03-exact-components.json"
    captured_path = E / "captured-nut-motion-attempt02/motion.json"
    retained_path = E / "retained-access-attempt03/access.json"
    t08_path = E / "current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json"
    evidence, tool, access, captured, retained, t08 = [
        load(ROOT / path) for path in (evidence_path, tool_path, access_path, captured_path, retained_path, t08_path)
    ]

    candidate_axes = packet["scope"]["candidate_axes"]
    retained_axes = packet["scope"]["retained_leg_bolt_axes"]
    require(len(candidate_axes) == 4 and len(set(candidate_axes)) == 4, "candidate axis scope is not four unique axes")
    require(len(retained_axes) == 4 and len(set(retained_axes)) == 4, "retained axis scope is not four unique axes")
    cross = load(ROOT / E / "current-fit-transport-option-crosswalk-attempt01/option-crosswalk.json")
    cross_by_axis = {row["axis_id"]: row for row in cross["rows"]}
    require(len(cross_by_axis) == 170, "crosswalk operation count changed")
    for axis in candidate_axes + retained_axes:
        require(cross_by_axis[axis]["physical_clearance"] == "unresolved", f"crosswalk physical status changed: {axis}")

    # Independently resolve each candidate component pointer and compare it to T07.
    candidate_hits = tool["candidate_nut_slide_hits"]["hits"]
    candidate_rows = packet["candidate_direct_hit_matrix"]
    require(len(candidate_hits) == len(candidate_rows) == 6, "candidate hit count mismatch")
    hit_keys: set[tuple[str, str]] = set()
    for row in candidate_rows:
        src = row["source_pointer"]["t07_focused_report"]
        require(src["path"] == str(E / "step6-operation-coverage-attempt01/tool-route-feasibility-attempt01/tool-route-feasibility.json"), "candidate source path mismatch")
        require(src["file_sha256"] == sha(ROOT / tool_path), "candidate source file hash mismatch")
        hit = pointer(tool, src["json_pointer"])
        require(hit["axis_id"] == row["axis_id"], "candidate axis pointer mismatch")
        require(hit["component_role"] == row["component_role"], "candidate component pointer mismatch")
        exact = hit["intersections"]
        require(len(exact) == 1, "candidate source hit does not identify exactly one blocker")
        require(exact[0]["blocker_id"] == row["obstacle_id"], "candidate blocker mismatch")
        require(exact[0]["volume_mm3"] == row["source_cad_proxy_intersection_volume_mm3"], "candidate intersection volume mismatch")
        require(hit["travel_mm"] == row["modeled_axial_slide_travel_mm"], "candidate travel mismatch")
        require(hit["screen_result"] == row["screen_result"], "candidate screen result mismatch")
        axis_ref = row["source_pointer"]["t07_attempt02_axis_register"]
        axis_record = pointer(evidence, axis_ref["json_pointer"])
        require(axis_record["axis_id"] == row["axis_id"], "candidate T07 register axis mismatch")
        require(canonical_sha(axis_record) == axis_ref["record_sha256_canonical_json"], "candidate T07 record hash mismatch")
        axis_access_ref = row["source_pointer"]["t07_exact_axis_access"]
        axis_access = pointer(access, axis_access_ref["json_pointer"])
        require(axis_access["axis_id"] == row["axis_id"], "candidate T07 access axis mismatch")
        require(row["crosswalk_direct_removal_external_envelope_clear"] is False, "candidate direct removal unexpectedly clear")
        require(row["crosswalk_reverse_insertion_external_envelope_clear"] is False, "candidate reverse insertion unexpectedly clear")
        require(row["tool_proxy_is_selected_or_physical_access"] is False, "candidate tool proxy overstated")
        require(row["captured_route_requires_unthreading_assumption"] is True, "candidate local route lost unthreading assumption")
        require(row["captured_route_component_capture_established"] is False, "candidate capture was overstated")
        require(row["captured_route_part_staging_established"] is False, "candidate staging was overstated")
        key = (row["axis_id"], row["component_role"])
        require(key not in hit_keys, f"duplicate candidate axis/component row: {key}")
        hit_keys.add(key)
    require({axis for axis, _ in hit_keys} == set(candidate_axes), "candidate hits do not cover the exact four-axis set")

    # Recheck the four local two-stage routes and their limiting assumptions.
    route_rows = packet["candidate_existing_local_route_matrix"]
    require(len(route_rows) == 4 and {row["axis_id"] for row in route_rows} == set(candidate_axes), "candidate route coverage mismatch")
    motion_by_axis = {row["axis_id"]: row for row in captured["axis_operations"]}
    summary_by_axis = {row["axis_id"]: row for row in evidence["candidate_nut_slide_findings"]["captured_local_route"]["rows"]}
    for row in route_rows:
        axis = row["axis_id"]
        motion = motion_by_axis[axis]
        summary = summary_by_axis[axis]
        options = [option for option in motion["lateral_then_axial_options"] if option["two_stage_cad_motion_clear"] is True]
        require(len(options) == 1, f"expected one source-CAD clear local route for {axis}")
        option = options[0]
        require(option["lateral_displacement_xyz_mm"] == row["lateral_first_displacement_xyz_mm"], "candidate lateral route vector mismatch")
        require(option["following_nutward_displacement_xyz_mm"] == row["second_nutward_displacement_xyz_mm"], "candidate nutward route vector mismatch")
        require(row["external_geometry_clear"] is True and row["thread_compatible_unthreading_assumed"] is True, "candidate local route interpretation changed")
        require(row["component_capture_established"] is False and row["full_part_staging_established"] is False, "candidate route support/staging overstated")
        require(row["reverse_assembly_screened"] is False, "candidate reverse route overstated")
        route_ref = row["source_pointer"]["t07_attempt02_route_summary"]
        source_summary = pointer(evidence, route_ref["json_pointer"])
        require(source_summary["axis_id"] == axis, "candidate route summary axis mismatch")
        require(source_summary["clear_local_option"]["lateral_displacement_xyz_mm"] == summary["clear_local_option"]["lateral_displacement_xyz_mm"], "candidate route summary record mismatch")

    # Check every modeled retained wire sweep against its source row.
    retained_hits = packet["retained_wire_component_hit_matrix"]
    source_retained = {row["axis_id"]: row for row in tool["retained_frame_bolt_wire_hits"]["rows"]}
    require(len(retained_hits) == 12 and set(source_retained) == set(retained_axes), "retained hit/axis coverage mismatch")
    components: dict[str, set[str]] = {axis: set() for axis in retained_axes}
    for row in retained_hits:
        src = row["source_pointer"]["t07_focused_report"]
        require(src["file_sha256"] == sha(ROOT / tool_path), "retained source hash mismatch")
        source = pointer(tool, src["json_pointer"])
        require(source["blocker_id"] == row["obstacle_id"], "retained blocker mismatch")
        require(source["intersection_volume_mm3"] == row["source_cad_proxy_intersection_volume_mm3"], "retained volume mismatch")
        require(source["component_sweep"] == row["component_role"], "retained component mismatch")
        require(row["withdrawal_wire_envelope_clear"] is False and row["reverse_insertion_wire_envelope_clear"] is False, "wire envelope collision status changed")
        require(row["wire_is_flexible_physical_cable_blockage_established"] is False, "modeled wire was overstated as physical blockage")
        require(row["T07_proxy_head_size_mismatch_to_3_4_in_reference"] is True, "T07 size-mismatch caveat lost")
        require(row["correct_size_profile_fit_screened"] is False and row["selected_tool_or_physical_access_established"] is False, "retained tool comparator overstated")
        axis_ref = row["source_pointer"]["t07_attempt02_axis_register"]
        axis_record = pointer(evidence, axis_ref["json_pointer"])
        require(axis_record["axis_id"] == row["axis_id"], "retained T07 register axis mismatch")
        require(canonical_sha(axis_record) == axis_ref["record_sha256_canonical_json"], "retained T07 record hash mismatch")
        components[row["axis_id"]].add(row["component_role"])
    require(all(len(value) == 3 for value in components.values()), "each retained axis must have head, washer, and shaft sweeps")

    retained_routes = packet["retained_existing_withdrawal_and_reverse_route_matrix"]
    require(len(retained_routes) == 4 and {row["axis_id"] for row in retained_routes} == set(retained_axes), "retained route coverage mismatch")
    retained_access_by_axis = {row["axis_id"]: row for row in retained["axis_operations"]}
    for row in retained_routes:
        axis = row["axis_id"]
        access_row = retained_access_by_axis[axis]
        require(row["modeled_nut_axial_removal_mm"] == 19.05, "retained nut travel changed")
        require(row["modeled_nut_washer_axial_removal_mm"] == 22.225, "retained nut/washer travel changed")
        require(row["modeled_nut_axial_removal_envelope_clear"] == access_row["operations"]["nut"]["removal"]["collision_screen"]["external_envelope_clear"], "retained nut slide mismatch")
        require(row["modeled_nut_washer_axial_removal_envelope_clear"] == access_row["operations"]["nut_washer"]["removal"]["collision_screen"]["external_envelope_clear"], "retained washer slide mismatch")
        require(row["component_capture_support_transfer_established"] is False and row["flexible_wire_service_route_established"] is False, "retained operation gate overstated")

    # Validate source-record joins and conditional product/tool boundary.
    t08_rows = {row["axis_id"]: row for row in t08["candidate_axis_rows"] + t08["retained_axis_rows"]}
    for axis in candidate_axes + retained_axes:
        cross_ptr = cross_by_axis[axis]["t08_fastener_axis_pointer"]
        indexed = pointer(t08, cross_ptr["json_pointer"])
        require(indexed["axis_id"] == axis and canonical_sha(indexed) == cross_ptr["record_sha256_canonical_json"], f"T08 axis join failed: {axis}")
        require(axis in t08_rows, f"T08 axis absent: {axis}")
    for lead in packet["candidate_catalog_leads"].values():
        ptr = lead["pointer"]
        indexed = pointer(t08, ptr["json_pointer"])
        require(ptr["file_sha256"] == sha(ROOT / t08_path), "conditional catalog lead file pin mismatch")
        require(indexed["id"] == lead["lead_id"], "conditional catalog lead ID mismatch")
        require(canonical_sha(indexed) == ptr["record_sha256_canonical_json"], "conditional catalog lead record hash mismatch")
        require(lead["conditional_only"] is True and lead["selected_product"] is None, "catalog lead was selected")

    for name, clear in packet["release_boundary"].items():
        require(clear is False, f"release boundary was cleared: {name}")
    require("all eight affected stacks" == packet["missing_evidence"][2]["scope"], "affected stack count mismatch")

    return {
        "schema": "wood_joint_current_fit_transport_critical_envelopes_parent_review/v1",
        "status": "PASS_SOURCE_BOUND_NOMINAL_ENVELOPES_ONLY_ALL_PHYSICAL_GATES_OPEN",
        "attempt": "current-fit-transport-critical-envelopes-attempt01",
        "reviewed_artifact_sha256": sha(ROOT / PACKET),
        "reviewed_producer_sha256": sha(HERE / "build_envelopes.py"),
        "reviewed_readme_sha256": sha(HERE / "README.md"),
        "parent_review_script_sha256": sha(HERE / "parent_review.py"),
        "transitive_source_unique_paths_rehashed": len(transitive),
        "crosswalk_rows_rechecked": len(cross["rows"]),
        "candidate_axes": candidate_axes,
        "candidate_direct_component_hits_rechecked": len(candidate_rows),
        "retained_leg_bolt_axes": retained_axes,
        "retained_component_wire_sweeps_rechecked": len(retained_hits),
        "selected_product_or_tool": False,
        "physical_fit_access_service_capture_support_staging_or_transport_cleared": False,
        "native_execution": False,
        "geometry_changed": False,
        "acceptance_changed": False,
        "finding": "This is a source-bound nominal CAD/proxy envelope comparison only. Candidate direct nut/washer hits and retained wire-span sweeps are reproduced from pinned records; every physical fit, access, cable-service, capture/support, staging, sequence, and transport operation remains unresolved.",
    }


if __name__ == "__main__":
    result = review()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PASS {OUT.relative_to(ROOT)} sha256={sha(OUT)}")
    print("PASS exact 6 candidate hits / 4 axes and 12 retained sweeps / 4 axes; all physical gates remain open")
