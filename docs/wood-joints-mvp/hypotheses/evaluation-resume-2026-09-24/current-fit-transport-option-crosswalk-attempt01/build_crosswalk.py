#!/usr/bin/env python3
"""Build/verify the source-bound T07/T08 axis-to-option crosswalk."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / "AGENTS.md").is_file())
OUTPUT = HERE / "option-crosswalk.json"
README = HERE / "README.md"
E = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
T07 = E + "current-fit-transport-closeout-attempt02/"
T08 = E + "current-hardware-material-cost-closeout-attempt01/"

T07_REGISTER = T07 + "evidence-register.json"
T07_README = T07 + "README.md"
T07_PRODUCER = T07 + "prepare.py"
T08_FASTENERS = T08 + "fastener-axis-register.json"
T08_MATERIAL_COST = T08 + "material-cost-register.json"
T08_SOURCE_PINS = T08 + "source-pins.json"
T08_README = T08 + "README.md"
T08_PARENT_REVIEW = T08 + "parent-review.json"
T08_VERIFICATION = T08 + "verification.json"
T08_BUILDER = T08 + "build_register.py"
T08_VERIFIER = T08 + "verify.py"

PACKET_HASHES = {
    T07_REGISTER: "dbfe1049d01f936bb034531699ff333d07916240c367851239fb665c1b4f17dc",
    T07_README: "ba330faae47bc5ab0fe23e5c512e490b49295bb0627f94c28263cb85a47bba03",
    T07_PRODUCER: "27baaa1602d26b71e1c0b0ddcbac928ef34fa7330de8c0bc0d79b9a0fc0cc6c1",
    T08_FASTENERS: "c1e53e9a08599d13a992fc11a493853c1695f697f3fe99b45af20795c430240a",
    T08_MATERIAL_COST: "7fdb44ea35449f3d6e9cdddb115cadd6f5763cf97c4403e71b9993f3d476ed3c",
    T08_SOURCE_PINS: "49c5a245fe67efaa192d280ef3e7eab3356e1571a19110c02ac94345cb1f7912",
    T08_README: "203f884837ab76a9d6de40ec497e6fc3052d08f52bbfa849687c44b1a8aee66c",
    T08_PARENT_REVIEW: "d9467f654743e640335248a1a785e5c6bc579e583e25cf747f585dd1a5b7f4c3",
    T08_VERIFICATION: "1fe1a286ae2cf7e97394a829dec1b451bf1532d7145d7c27bfe1ad6aef1abdf4",
    T08_BUILDER: "c6c75229b362031567b83195d2b7217ec6d1a18485140b8258e6d88fc982abfb",
    T08_VERIFIER: "1ef9b37d3db1ab1296f8f05f96c910cc0fb3a8c047e148bcfb3c8def61cd31cd",
}

CURRENT_HARDWARE_COVERAGE = "docs/wood-joints-mvp/current-hardware-coverage.json"
RETAINED_BOLT_CSV = "docs/floor-flush-construction-kerf-right/bolt-hardware.csv"
PANEL_SCREW_POLICY = "docs/current-panel-screw-purchase.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def record_pointer(path: str, file_hash: str, collection: str, index: int, row: dict) -> dict:
    return {
        "path": path,
        "file_sha256": file_hash,
        "json_pointer": f"/{collection}/{index}",
        "record_sha256_canonical_json": canonical_sha256(row),
    }


def collision_summary(phase_row: dict) -> dict:
    screen = phase_row.get("collision_screen") or {}
    if not screen:
        return {"screen_status": phase_row.get("status", "not_reported")}
    hits = screen.get("external_envelope_hits_mm3") or {}
    return {
        "screen_status": phase_row.get("status", "not_reported"),
        "external_envelope_clear": screen.get("external_envelope_clear"),
        "hit_ids": sorted(hits),
        "hit_volumes_mm3": hits,
        "physical_access_established": screen.get("physical_access_established"),
        "scope": "source-CAD/proxy envelope screen only; not physical fit or tool access",
    }


def bolt_component_screen(detail: dict) -> dict:
    operations = detail.get("operations", {})
    head_bolt = operations.get("head_side_bolt", {})
    nut = operations.get("nut", {})
    nut_washer = operations.get("nut_washer", {})
    return {
        "modeled_component_role_ids": detail.get("hardware_role_ids", detail.get("physical_role_shape_ids", [])),
        "head_side_bolt": {
            "modeled_travel_mm": head_bolt.get("derived_travel_mm"),
            "withdrawal": collision_summary(head_bolt.get("withdrawal", {})),
            "reverse_insertion": collision_summary(head_bolt.get("reverse_assembly", {})),
        },
        "nut": {
            "modeled_axial_travel_mm": nut.get("derived_axial_travel_mm"),
            "removal": collision_summary(nut.get("removal", {})),
            "reverse_insertion": collision_summary(nut.get("reverse_assembly", {})),
            "thread_disengagement_or_capture_established": nut.get("threaded_disengagement_or_part_capture_established"),
        },
        "nut_washer": {
            "modeled_axial_travel_mm": nut_washer.get("derived_axial_travel_mm"),
            "removal": collision_summary(nut_washer.get("removal", {})),
            "reverse_insertion": collision_summary(nut_washer.get("reverse_assembly", {})),
            "thread_disengagement_or_capture_established": nut_washer.get("threaded_disengagement_or_part_capture_established"),
        },
        "model_limit": "component paths use current source BReps and assumptions; delivered parts, tolerance, thread motion, and full staged sequence are not represented",
    }


def wrench_proxy_summary(operation: dict) -> dict:
    profiles = operation.get("profile_source") or {}
    heading_rows = []
    for pose in operation.get("pose_rows", []):
        approach = pose.get("approach_proxy", {})
        discrete = pose.get("discrete_turn_pose_samples", [])
        continuous = pose.get("continuous_30_degree_AABB_enclosures", [])
        discrete_clear = sum(bool((sample.get("collision_screen") or {}).get("external_envelope_clear")) for sample in discrete)
        continuous_hits = sorted({
            blocker
            for sample in continuous
            for blocker in ((sample.get("collision_screen") or {}).get("external_envelope_hits_mm3") or {})
        })
        approach_screen = approach.get("collision_screen") or {}
        heading_rows.append({
            "synthetic_heading_sample_degrees": pose.get("synthetic_heading_sample_degrees"),
            "axial_approach_proxy": collision_summary(approach),
            "discrete_turn_pose_samples": len(discrete),
            "discrete_turn_proxy_clear_count": discrete_clear,
            "continuous_30_degree_aabb_enclosure_count": len(continuous),
            "continuous_enclosure_hit_ids": continuous_hits,
            "physical_tool_access_established": approach_screen.get("physical_access_established"),
        })
    return {
        "profile_source": profiles,
        "sampled_turn_angles_degrees": operation.get("sampled_turn_angles_degrees", []),
        "heading_sample_count": len(heading_rows),
        "heading_rows": heading_rows,
        "actual_tool_access_established": operation.get("actual_tool_access_established"),
        "unthreading_or_torque_screened": operation.get("unthreading_or_torque_screened"),
        "scope": "manufacturer/profile dimensions feed a synthetic proxy; no actual selected tool, jaw engagement, full hand/workspace, torque, or paired counterhold is established",
    }


def extract_head_dimension_phrases(spec: str) -> list[str]:
    number = r"(?:\d+\s+)?\d+\s*/\s*\d+|\d+(?:\.\d+)?"
    value = rf"(?:{number})"
    dimension = rf"{value}(?:\s*-\s*{value})?\s*(?:in(?:ch(?:es)?)?\s*)?"
    return [match.group(0).strip(" ,;") for match in re.finditer(
        rf"{dimension}(?:across flats|head width|hex)", spec, flags=re.IGNORECASE
    )]


def extract_head_height_phrases(spec: str) -> list[str]:
    number = r"(?:\d+\s+)?\d+\s*/\s*\d+|\d+(?:\.\d+)?"
    value = rf"(?:{number})"
    dimension = rf"{value}(?:\s*-\s*{value})?\s*(?:in(?:ch(?:es)?)?\s*)?"
    return [match.group(0).strip(" ,;") for match in re.finditer(
        rf"{dimension}head height", spec, flags=re.IGNORECASE
    )]


def family_record(coverage: dict, family_id: str) -> tuple[int, dict]:
    for index, row in enumerate(coverage.get("candidate_family_coverage", [])):
        if row.get("family_id") == family_id:
            return index, row
    for index, row in enumerate(coverage.get("retained_family_coverage", [])):
        if row.get("family_id") == family_id:
            return index, row
    raise ValueError(f"hardware-coverage family not found: {family_id}")


def missing_fields(kind: str, record: dict) -> list[dict]:
    if kind == "candidate_bolt_axis":
        gaps = [
            {"field": "selected exact bolt SKU and delivered lot identity", "needed_source": "approved product/lot identifier plus lot documentation; T08 selected_product is null"},
            {"field": "delivered shank and complete-thread interval including thread start, last full thread, runout/point and tolerance", "needed_source": "exact selected bolt drawing/specification plus traceable lot measurements or certificate"},
            {"field": "matched nut active-thread interval, chamfer and tolerance", "needed_source": "exact matched nut drawing/specification and lot measurement"},
            {"field": "selected washer/spacer identity, dimensions/tolerance and supported footprint", "needed_source": "axis-assigned product/lot record and bearing-footprint evidence"},
            {"field": "actual turning/counterhold tool size, jaw profile and workspace", "needed_source": "selected head/nut tool IDs with dimensioned profiles and a current assembled-scene access screen including hands/counterhold"},
            {"field": "part capture, support transfer, staging and reversible member sequence", "needed_source": "named supported operation states, capture/staging locations, and screened reverse path using bound parts/tools"},
        ]
        if not record.get("conditional_nut_lead_ids") or not record.get("conditional_washer_lead_ids"):
            gaps.append({"field": "axis-specific nut/washer lead assignment", "needed_source": "T08 family-specific matched component references; shared conditional leads are not an axis assignment"})
        if record.get("conditional_spacer_lead_ids"):
            gaps.append({"field": "conditional spacer acceptance", "needed_source": "axis/family selection plus delivered dimensions/tolerance and support evaluation; listed ID remains conditional"})
        return gaps
    if kind == "retained_frame_bolt_axis":
        return [
            {"field": "current WJ24 product/ownership and delivered lot identity", "needed_source": "current shop/source inventory or receipt tied to retained axis and exact item/lot"},
            {"field": "delivered bolt thread transition/shank, matched nut active thread/chamfer, washer dimensions and tolerances", "needed_source": "exact #367/#368/#407 and #2571/#2573/#15023/#15025 drawings/specs plus delivered-lot measurements"},
            {"field": "axis-specific head/nut across-flats and actual tool match", "needed_source": "dimensioned bolt/nut product record and selected tool profile; current T07 7/16-in proxy does not qualify access"},
            {"field": "tool approach, working room and paired counterhold", "needed_source": "selected dimensioned tools and current assembled-scene access/workspace screen"},
            {"field": "support/capture and reversible bolt withdrawal/insertion", "needed_source": "supported state sequence with retained service wiring and screened forward/reverse operations"},
        ]
    return [
        {"field": "delivered Hillman 42605 dimensions/tolerances for major/root/shank, head, thread length and lot", "needed_source": "exact model/lot dimensional drawing or traceable lot measurements"},
        {"field": "actual #2 Phillips driver and working access envelope", "needed_source": "selected dimensioned driver/bit and screen against the current assembled geometry, panel and hand workspace"},
        {"field": "verified pilot/countersink and screw installation/withdrawal in actual receiver", "needed_source": "the owner-selected Kobalt offcut trial recorded on the shop checklist plus actual receiver measurements"},
        {"field": "panel capture, support transfer, and reversible panel/screw sequence", "needed_source": "named supported panel state and screened withdrawal/reinstallation sequence"},
        {"field": "screw resistance/material property map", "needed_source": "exact Hillman 42605 model- and condition-specific structural data or a bounded joint test basis; T08 marks this outside its map"},
    ]


def build_crosswalk() -> dict:
    t07 = read_json(T07_REGISTER)
    t08 = read_json(T08_FASTENERS)
    t08_cost = read_json(T08_MATERIAL_COST)
    t08_pins = read_json(T08_SOURCE_PINS)
    t08_review = read_json(T08_PARENT_REVIEW)
    hardware_coverage = read_json(CURRENT_HARDWARE_COVERAGE)
    with (ROOT / RETAINED_BOLT_CSV).open(newline="", encoding="utf-8") as stream:
        csv_rows = list(csv.DictReader(stream))
    csv_by_name = {row["name"]: (index, row) for index, row in enumerate(csv_rows)}

    t07_rows = t07["axis_operation_status_register"]["rows"]
    t07_by_id = {row["axis_id"]: (index, row) for index, row in enumerate(t07_rows)}
    if len(t07_by_id) != 170 or len(t07_rows) != 170:
        raise ValueError("T07 attempt02 no longer has exactly 170 unique operation rows")
    t08_groups = {
        "candidate_bolt_axis": t08["candidate_axis_rows"],
        "retained_frame_bolt_axis": t08["retained_axis_rows"],
        "hillman_panel_kicker_axis": t08["hillman_axis_rows"],
    }
    expected_counts = {"candidate_bolt_axis": 92, "retained_frame_bolt_axis": 12, "hillman_panel_kicker_axis": 66}
    if {kind: len(rows) for kind, rows in t08_groups.items()} != expected_counts:
        raise ValueError("T08 axis-row counts changed")
    t08_by_id = {row["axis_id"]: (kind, index, row) for kind, rows in t08_groups.items() for index, row in enumerate(rows)}
    if len(t08_by_id) != 170 or set(t08_by_id) != set(t07_by_id):
        raise ValueError("T07 and T08 axis identities do not join exactly")
    if t07.get("geometry_revision_id") != t08.get("geometry_revision_id"):
        raise ValueError("T07/T08 geometry revision IDs differ")
    if t08.get("candidate") != "compact-floor-flush-wood-joints-development":
        raise ValueError("T08 candidate identity changed")
    if t08.get("selected_candidate_authority_preserved") != "compact-floor-flush-development":
        raise ValueError("T08 no longer records the selected baseline as preserved")
    if t08_review.get("status") != "PASS_SOURCE_BOUND_REGISTER_ONLY_WITH_PENDING_PRODUCT_MATERIAL_PRICE_GATES":
        raise ValueError("T08 parent review no longer has the expected source-bound pending status")
    if t08_review.get("authority_and_release", {}).get("candidate_product_selected") is not False:
        raise ValueError("T08 now indicates a candidate product selection")
    if t08.get("status") != "source_bound_identity_and_count_register_only; no product or delivered stack accepted":
        raise ValueError("T08 fastener register status changed")
    if t08.get("counts", {}).get("fit_qualified_candidate_stacks") != 0 or t08.get("counts", {}).get("fit_qualified_retained_stacks") != 0:
        raise ValueError("T08 fit-qualified stack counts changed")

    # Verify all nested input hashes rather than relying only on the packet files.
    source_hash_rows = []
    for group, path, expected in [("T07_packet", p, h) for p, h in PACKET_HASHES.items() if p.startswith(T07)]:
        actual = sha256(ROOT / path)
        if actual != expected:
            raise ValueError(f"T07 packet hash changed: {path}")
        source_hash_rows.append({"consumer": group, "path": path, "sha256": expected, "role": "reviewed T07 attempt02 packet"})
    for group, path, expected in [("T08_packet", p, h) for p, h in PACKET_HASHES.items() if p.startswith(T08)]:
        actual = sha256(ROOT / path)
        if actual != expected:
            raise ValueError(f"T08 packet hash changed: {path}")
        source_hash_rows.append({"consumer": group, "path": path, "sha256": expected, "role": "parent-reviewed T08 attempt01 packet"})

    t07_source_pins = t07.get("source_pins", [])
    for pin in t07_source_pins:
        path, expected = pin["path"], pin["sha256"]
        actual_path = ROOT / path
        if not actual_path.is_file() or sha256(actual_path) != expected:
            raise ValueError(f"T07 transitive source pin changed: {path}")
        source_hash_rows.append({"consumer": "T07_attempt02_transitive", "path": path, "sha256": expected, "role": pin.get("role")})
    t08_source_pins = t08_pins.get("source_files", [])
    for pin in t08_source_pins:
        path, expected = pin["path"], pin.get("expected_sha256_at_inventory")
        actual_path = ROOT / path
        if pin.get("status") != "match" or pin.get("actual_sha256_at_build") != expected or not actual_path.is_file() or sha256(actual_path) != expected:
            raise ValueError(f"T08 transitive source pin changed: {path}")
        source_hash_rows.append({"consumer": "T08_attempt01_transitive", "path": path, "sha256": expected, "role": pin.get("role")})
    for filename, expected in t08_review.get("reviewed_hashes", {}).items():
        path = T08 + filename
        if sha256(ROOT / path) != expected:
            raise ValueError(f"T08 parent-reviewed artifact hash changed: {path}")
    # The T07 source list itself binds the exact full-frame and operation geometry sources;
    # source rows stay separate by consuming packet even when files overlap.
    source_hash_rows = sorted(source_hash_rows, key=lambda row: (row["consumer"], row["path"], row["sha256"]))

    t07_sources_by_path = {row["path"]: row["sha256"] for row in t07_source_pins}
    t08_sources_by_path = {row["path"]: row["expected_sha256_at_inventory"] for row in t08_source_pins}
    product_rows = t08.get("catalog_product_records", [])
    product_by_id = {row["id"]: (index, row) for index, row in enumerate(product_rows)}
    if len(product_by_id) != len(product_rows):
        raise ValueError("T08 catalog lead IDs are not unique")
    candidate_families = {row["family_id"]: row for row in hardware_coverage["candidate_family_coverage"]}
    retained_families = {row["family_id"]: row for row in hardware_coverage["retained_family_coverage"]}
    coverage_path = CURRENT_HARDWARE_COVERAGE
    coverage_hash = t08_sources_by_path.get(coverage_path)
    csv_hash = t08_sources_by_path.get(RETAINED_BOLT_CSV)
    panel_policy_hash = t08_sources_by_path.get(PANEL_SCREW_POLICY)
    if not all((coverage_hash, csv_hash, panel_policy_hash)):
        raise ValueError("required T08 pinned geometry/coverage/purchase-policy source missing")

    report_cache = {}
    def report_row(path: str, index: int, expected_digest: str) -> dict:
        if path not in report_cache:
            report_cache[path] = read_json(path)
        rows = report_cache[path]["axis_operations"]
        row = rows[index]
        if canonical_sha256(row) != expected_digest:
            raise ValueError(f"T07 detailed screen record hash mismatch at {path}#{index}")
        return row

    crosswalk_rows = []
    for axis_id, (t08_kind, t08_index, t08_row) in t08_by_id.items():
        t07_index, t07_row = t07_by_id[axis_id]
        if not all(value == "unresolved" for value in t07_row["unresolved_physical_status"].values()):
            raise ValueError(f"T07 physical status was not left unresolved for {axis_id}")
        t07_pointer = record_pointer(T07_REGISTER, PACKET_HASHES[T07_REGISTER], "axis_operation_status_register/rows", t07_index, t07_row)
        t08_collection = {
            "candidate_bolt_axis": "candidate_axis_rows",
            "retained_frame_bolt_axis": "retained_axis_rows",
            "hillman_panel_kicker_axis": "hillman_axis_rows",
        }[t08_kind]
        t08_pointer = record_pointer(T08_FASTENERS, PACKET_HASHES[T08_FASTENERS], t08_collection, t08_index, t08_row)
        common = {
            "axis_id": axis_id,
            "inventory_class": t08_kind,
            "geometry_revision_id": t08["geometry_revision_id"],
            "t07_pointer": t07_pointer,
            "t08_fastener_axis_pointer": t08_pointer,
            "t07_model_or_access_evidence": {
                "operation_coverage_record": t07_row["evidence_links"]["operation_coverage_record"],
                "axis_specific_screen_record": t07_row["evidence_links"].get("axis_specific_screen_record"),
                "focused_tool_route_source": t07_row["evidence_links"].get("focused_tool_route_source"),
                "source_operation_statuses": t07_row["source_operation_statuses"],
                "source_fit_and_use_limits": t07_row["source_fit_and_use_limits"],
                "unresolved_physical_status": t07_row["unresolved_physical_status"],
                "source_geometry_findings": t07_row["source_geometry_findings"],
            },
            "physical_status_after_crosswalk": dict(t07_row["unresolved_physical_status"]),
            "physical_clearance": "unresolved",
            "fit_or_tool_acceptance": "not established",
        }

        if t08_kind == "candidate_bolt_axis":
            family = candidate_families.get(t08_row["family_id"])
            if not family or axis_id not in family.get("axis_ids", []):
                raise ValueError(f"candidate coverage family does not include {axis_id}")
            lead_groups = {
                "bolt_leads": t08_row.get("candidate_product_lead_ids", []),
                "conditional_nut_leads": t08_row.get("conditional_nut_lead_ids", []),
                "conditional_washer_leads": t08_row.get("conditional_washer_lead_ids", []),
                "conditional_spacer_leads": t08_row.get("conditional_spacer_lead_ids", []),
            }
            lead_refs = {}
            for lead_kind, ids in lead_groups.items():
                lead_refs[lead_kind] = []
                for lead_id in ids:
                    if lead_id not in product_by_id:
                        raise ValueError(f"T08 catalog lead missing: {lead_id}")
                    lead_index, lead = product_by_id[lead_id]
                    spec = lead.get("spec", "")
                    lead_refs[lead_kind].append({
                        "id": lead_id,
                        "role": lead.get("role"),
                        "vendor": lead.get("vendor"),
                        "part_number": lead.get("part_number"),
                        "spec": spec,
                        "thread_field": lead.get("thread_field"),
                        "explicit_head_hex_dimension_phrases": extract_head_dimension_phrases(spec),
                        "explicit_head_height_phrases": extract_head_height_phrases(spec),
                        "record_pointer": record_pointer(T08_FASTENERS, PACKET_HASHES[T08_FASTENERS], "catalog_product_records", lead_index, lead),
                    })
            detail_link = t07_row["evidence_links"]["axis_specific_screen_record"]
            detailed = report_row(detail_link["path"], detail_link["index"], detail_link["record_sha256_canonical_json"])
            operations = detailed.get("operations", {})
            common.update({
                "catalog_option": {
                    "family_id": t08_row["family_id"],
                    "catalog_row_id": t08_row["catalog_row_id"],
                    "candidate_product_lead_ids": lead_groups["bolt_leads"],
                    "conditional_component_lead_ids": {key: value for key, value in lead_groups.items() if key != "bolt_leads"},
                    "lead_records": lead_refs,
                    "selected_product": t08_row.get("selected_product"),
                    "fit_status": t08_row.get("fit_status"),
                    "delivered_shank_bounds": t08_row.get("delivered_shank_bounds"),
                    "delivered_full_thread_interval": t08_row.get("delivered_full_thread_interval"),
                    "matched_nut_active_thread_interval": t08_row.get("matched_nut_active_thread_interval"),
                    "modeled_underhead_to_tip_mm": t08_row.get("modeled_underhead_to_tip_mm"),
                    "modeled_wood_grip_mm": t08_row.get("modeled_wood_grip_mm"),
                    "family_coverage_pointer": record_pointer(CURRENT_HARDWARE_COVERAGE, coverage_hash, "candidate_family_coverage", list(hardware_coverage["candidate_family_coverage"]).index(family), family),
                },
                "component_envelope_fields": {
                    "t07_reported_role_ids": detailed.get("hardware_role_ids", []),
                    "t08_modeled_length_mm": t08_row.get("modeled_underhead_to_tip_mm"),
                    "t08_modeled_wood_grip_mm": t08_row.get("modeled_wood_grip_mm"),
                    "t07_bolt_nut_washer_motion_screens": bolt_component_screen(detailed),
                    "component_dimensions_are_delivered": False,
                },
                "tool_envelope_fields": {
                    "head_end_proxy": wrench_proxy_summary(operations.get("head_wrench", {})),
                    "nut_end_proxy": wrench_proxy_summary(operations.get("nut_wrench", {})),
                    "usable_for_physical_clearance": False,
                    "reason": "T07 uses a 7/16-in FACOM synthetic profile as a geometric comparator; it is not an axis-selected wrench, complete jaw/hand/counterhold envelope, or physical operation proof.",
                },
                "catalog_comparator_assessment": {
                    "status": "lead_dimensions_only_unusable_for_fit_or_operation_clearance",
                    "limitation": "Some lead records state nominal hex/head and washer/nut dimensions; the axis has no selected product, delivered lot, full dimensional tolerance stack, complete-thread/runout position, matched active nut-thread bound, actual tool/workspace, or support/staging proof.",
                    "exact_missing_source": "Exact final item/lot dimensional records and measurements for bolt, matched nut, washer/spacer, plus selected dimensioned tools and the current full-workspace/reverse-path screen.",
                },
                "missing_data": missing_fields("candidate_bolt_axis", t08_row),
            })
        elif t08_kind == "retained_frame_bolt_axis":
            family = retained_families.get(t08_row["family_id"])
            if not family or axis_id not in family.get("axis_ids", []):
                raise ValueError(f"retained coverage family does not include {axis_id}")
            if axis_id not in csv_by_name:
                raise ValueError(f"retained source axis missing from bolt-hardware.csv: {axis_id}")
            csv_index, csv_row = csv_by_name[axis_id]
            detail_link = t07_row["evidence_links"]["axis_specific_screen_record"]
            detailed = report_row(detail_link["path"], detail_link["index"], detail_link["record_sha256_canonical_json"])
            operations = detailed.get("operations", {})
            family_index, family_row = family_record(hardware_coverage, t08_row["family_id"])
            common.update({
                "catalog_option": {
                    "family_id": t08_row["family_id"],
                    "catalog_reference_ids": t08_row["catalog_reference"],
                    "source_status": t08_row.get("source_status"),
                    "selected_for_wood_joints": t08_row.get("selected_for_wood_joints"),
                    "current_candidate_recheck": t08_row.get("current_candidate_recheck"),
                    "delivered_identity_or_ownership": t08_row.get("delivered_identity_or_ownership"),
                    "family_reference_summary": family_row,
                    "family_reference_pointer": record_pointer(CURRENT_HARDWARE_COVERAGE, coverage_hash, "retained_family_coverage", family_index, family_row),
                },
                "component_envelope_fields": {
                    "source_geometry_row": csv_row,
                    "source_geometry_pointer": {
                        "path": RETAINED_BOLT_CSV,
                        "file_sha256": csv_hash,
                        "csv_record_index_zero_based": csv_index,
                        "csv_line_number": csv_index + 2,
                        "record_sha256_canonical_json": canonical_sha256(csv_row),
                    },
                    "t07_modeled_stack": {
                        "modeled_nominal_length_mm": detailed.get("modeled_nominal_length_mm"),
                        "modeled_grip_mm": detailed.get("modeled_grip_mm"),
                        "source_occupied_diameter_mm": detailed.get("source_occupied_diameter_mm"),
                        "source_occupied_length_mm": detailed.get("source_occupied_length_mm"),
                        "modeled_component_count": detailed.get("modeled_component_count"),
                    },
                    "t07_bolt_nut_washer_motion_screens": bolt_component_screen(detailed),
                    "component_dimensions_are_delivered": False,
                },
                "tool_envelope_fields": {
                    "head_end_proxy": wrench_proxy_summary(operations.get("head_wrench", {})),
                    "nut_end_proxy": wrench_proxy_summary(operations.get("nut_wrench", {})),
                    "unapplied_t07_alternative_profiles": t07.get("tool_profile_evidence", {}).get("candidate_profiles", []),
                    "usable_for_physical_clearance": False,
                    "reason": "The applied T07 per-axis proxy is a synthetic 7/16-in FACOM profile. It is a size mismatch to the 3/4-in hex reference called out for the #407 lumber-leg bolt; for the 3/8-in bolt references, the pinned T08 axis row does not provide an exact head-across-flats dimension or matched selected tool. Alternative published profiles were not fit-screened on these axes.",
                },
                "catalog_comparator_assessment": {
                    "status": "selected_baseline_reference_only_unusable_for_current_fit_clearance",
                    "limitation": "T08 explicitly preserves these IDs as selected-baseline catalog references, with ownership/delivery unverified and current-candidate recheck required. Nominal catalog IDs and source geometry fields do not establish current delivered fit, transitions, tolerances, tool access, support, or WJ24 acceptance.",
                    "exact_missing_source": "Current item/lot identity and receipts plus exact #367/#368/#407 and matched nut/washer dimension/tolerance records and delivered measurements, together with selected matched tool/workspace and reversible-support evidence.",
                },
                "missing_data": missing_fields("retained_frame_bolt_axis", t08_row),
            })
        else:
            coverage_ptr = t07_row["evidence_links"]["operation_coverage_record"]
            coverage_rows = read_json(coverage_ptr["path"])["axis_records"]
            t07_coverage_record = coverage_rows[coverage_ptr["index"]]
            common.update({
                "catalog_option": {
                    "fixed_product_policy": t08_row["product"],
                    "purchase_policy": t08_row["purchase_policy"],
                    "quantity_policy": t08_row["quantity_policy"],
                    "owner_moved_axis": t08_row["owner_moved_axis"],
                    "receipt_cost": t08_row["receipt_cost"],
                    "new_purchase_cost": t08_row["new_purchase_cost"],
                    "material_capacity_property_map": t08_row["material_capacity_property_map"],
                    "product_policy_pointer": t08_pointer,
                    "selected_product_policy_source": {
                        "path": PANEL_SCREW_POLICY,
                        "file_sha256": panel_policy_hash,
                        "section_locator": "Purchased panel screw record / Current disposition",
                        "supported_interface": "#10 x 2-1/2-in Hillman/Fas-n-Tite 42605; #2 Phillips drive; owner-selected Kobalt #10 1/8-in pilot and 3/8-in face countersink",
                    },
                },
                "component_envelope_fields": {
                    "t07_modeled_axis_envelope": t07_coverage_record.get("modeled_axis_envelope"),
                    "receiver_axis_screen": t07_row["source_geometry_findings"].get("receiver_axis_envelope"),
                    "envelope_limit": "T07 current occupied CAD axis against raw/finished receiver; diameter is a historical proxy, not measured Hillman geometry",
                },
                "tool_envelope_fields": {
                    "pilot_countersink_tool": "Kobalt 80277 is the owner-selected pilot/countersink set only; the local purchase note does not bind a #2 Phillips driver or its access envelope.",
                    "drive_interface_source": "#2 Phillips product drive, from the pinned current-panel-screw-purchase.md note",
                    "actual_driver_or_workspace_screened": False,
                    "usable_for_physical_clearance": False,
                },
                "catalog_comparator_assessment": {
                    "status": "fixed_purchase_policy_no_dimensioned_comparator_for_actual_envelope",
                    "limitation": "T08 keeps the purchased 42605 policy on these 66 axes, but actual major/root/shank/head dimensions, thread length/tolerances, driver dimensions and physical access are not measured or screened.",
                    "exact_missing_source": "Exact model/lot drawing or delivered-lot measurements for Hillman 42605, plus a selected #2 Phillips driver/bit and current-axis hand/workspace screen; record the selected pilot/countersink offcut trial on the shop checklist.",
                },
                "missing_data": missing_fields("hillman_panel_kicker_axis", t08_row),
            })
            common["t07_model_or_access_evidence"]["operation_coverage_record"]["record_sha256_canonical_json"] = canonical_sha256(t07_coverage_record)
        crosswalk_rows.append(common)

    if len(crosswalk_rows) != 170 or len({row["axis_id"] for row in crosswalk_rows}) != 170:
        raise ValueError("crosswalk is not a one-to-one 170-axis join")
    if any(row["physical_clearance"] != "unresolved" for row in crosswalk_rows):
        raise ValueError("crosswalk must leave every physical clearance unresolved")

    catalog_lead_index = []
    for index, lead in enumerate(product_rows):
        spec = lead.get("spec", "")
        catalog_lead_index.append({
            "id": lead["id"],
            "role": lead.get("role"),
            "vendor": lead.get("vendor"),
            "part_number": lead.get("part_number"),
            "spec": spec,
            "thread_field": lead.get("thread_field"),
            "explicit_head_hex_dimension_phrases": extract_head_dimension_phrases(spec),
            "explicit_head_height_phrases": extract_head_height_phrases(spec),
            "pointer": record_pointer(T08_FASTENERS, PACKET_HASHES[T08_FASTENERS], "catalog_product_records", index, lead),
        })

    return {
        "schema": "wood_joint_t07_t08_option_crosswalk/v1",
        "status": "source_bound_option_crosswalk_physical_fit_and_transport_unresolved",
        "candidate_id": t08["candidate"],
        "selected_candidate_authority_preserved": t08["selected_candidate_authority_preserved"],
        "geometry_revision_id": t07["geometry_revision_id"],
        "exchange_packet_ids": {
            "t07": {
                "option_id": "current-fit-transport-closeout-attempt02",
                "artifact_schema": t07["schema"],
                "register_path": T07_REGISTER,
                "register_sha256": PACKET_HASHES[T07_REGISTER],
            },
            "t08": {
                "option_id": "current-hardware-material-cost-closeout-attempt01",
                "artifact_schema": t08["schema"],
                "fastener_register_schema": t08.get("schema"),
                "register_path": T08_FASTENERS,
                "register_sha256": PACKET_HASHES[T08_FASTENERS],
                "parent_review_status": t08_review["status"],
                "parent_review_path": T08_PARENT_REVIEW,
            "parent_review_sha256": PACKET_HASHES[T08_PARENT_REVIEW],
            },
        },
        "t08_cost_scope": {
            "path": T08_MATERIAL_COST,
            "file_sha256": PACKET_HASHES[T08_MATERIAL_COST],
            "status": t08_cost.get("status"),
            "total_cost_status": t08_cost.get("total_cost_status"),
            "candidate_cost_lines_included": sum(bool(row.get("included_in_current_total")) for row in t08_cost.get("candidate_cost_lines", [])),
            "interpretation": "T08 cost observations do not select or qualify a hardware product and do not change any T07 fit/transport status.",
        },
        "source_hashes_verified": source_hash_rows,
        "counts": {
            "candidate_bolt_axes": 92,
            "retained_frame_bolt_axes": 12,
            "hillman_panel_kicker_axes": 66,
            "total_crosswalk_rows": len(crosswalk_rows),
            "candidate_selected_products": 0,
            "candidate_fit_qualified_stacks": 0,
            "retained_fit_qualified_stacks": 0,
            "physical_access_or_transport_clearances": 0,
        },
        "source_supported_tool_profile_comparators": t07.get("tool_profile_evidence", {}).get("candidate_profiles", []),
        "shared_conditional_candidate_accessory_pool": t08.get("shared_candidate_nut_washer_lead_ids"),
        "candidate_catalog_lead_record_index": catalog_lead_index,
        "global_limits": [
            "Catalog lead/reference IDs are not selected products, delivered lots, matched stacks, or accepted tool choices.",
            "T07 source-CAD dimensions and envelopes are model/component-role screens, not delivered-hardware or physical-workspace dimensions.",
            "No product/tool was selected, no current geometry was altered, no vendor source was newly researched, and no fit, installation, removal, support, capture, service, or transport operation was cleared.",
            "T08 leaves fit-qualified candidate and retained stacks at zero; all 170 T07 physical-status fields remain unresolved.",
        ],
        "rows": crosswalk_rows,
    }


def build_readme(crosswalk: dict) -> str:
    return f"""# T07/T08 fit and option crosswalk — attempt01

**Status:** source-bound identity and comparator crosswalk only. This joins
T07 `current-fit-transport-closeout-attempt02` to T08
`current-hardware-material-cost-closeout-attempt01` for candidate
`{crosswalk['candidate_id']}`, revision
`{crosswalk['geometry_revision_id']}`. It makes no new product or tool
selection; candidate bolt/nut/washer/spacer options and tools remain
unselected, while the 66 screw axes retain the existing Hillman 42605 policy.
All 170 physical fit/access/reversible-operation/support and transport outcomes
remain unresolved.

The [machine-readable crosswalk](option-crosswalk.json) contains one row for
each of the 92 candidate bolt axes, 12 retained starting frame-bolt stacks, and
66 fixed Hillman 42605 panel/kicker axes. Each row has exact JSON record
pointers and canonical-record hashes into both T07/T08 registers; it joins
candidate leads by stable T08 catalog-lead IDs, retained arrangements by the
selected-baseline Bolt Depot reference IDs, and panel axes to the fixed Hillman
purchase policy. Its `source_hashes_verified` list includes all transitive
T07 source pins and all 35 T08 source pins, as well as the reviewed packet
files. The producer re-hashes and checks these before writing.
The linked T08 material/cost register remains pending; it records no candidate
product selection or current candidate total, and its price observations do
not qualify a product for fit or transport.

## What the current records support

For 92 candidate axes, T08 supplies per-axis catalog-lead IDs, conditional
nut/washer/spacer IDs where actually assigned, a model length/grip, and null
delivered shank, thread-interval, matched-nut interval, and selected-product
fields. The linked lead records retain their published spec and thread text;
some state nominal hex/head or washer/nut dimensions. These are lead-level
comparators only. T07 links each candidate to its modeled head/washer/nut/
shaft path screens and the synthetic 7/16-in FACOM profile with sampled poses.
The proxy has no selected wrench, real jaw engagement, hand/workspace,
counterhold, tolerance, matched thread, support or capture proof. Where an
axis has no T08 nut/washer lead IDs, the crosswalk does not assign the shared
conditional accessory pool to it.

For 12 retained stacks, T08 preserves the selected-baseline Bolt Depot
references: `#407/#2573/#15025` for the four 1/2-in leg bolts,
`#367/#2571/#15023` for the four front 3/8-in bolts, and
`#368/#2571/#15023` for the four rear 3/8-in bolts. Its source rows and the
matching retained-axis CSV rows include nominal/model dimensions, while T08
still says ownership/delivery is unverified and a current-candidate recheck is
required. T07’s per-axis access study applies a synthetic 7/16-in FACOM tool
proxy. For the #407 leg-bolt reference the T07 tool proxy is 7/16 in while the
pinned source describes the bolt hex as 3/4 in; the separate 3/4-in Wera
profile is only an unapplied comparator. For the 3/8-in refs the pinned T08
axis rows do not bind a precise head-across-flats dimension to an actual tool.
None of these proxy results clears fit or access.

All 66 panel/kicker rows keep the owner-purchased Hillman/Fas-n-Tite 42605
policy and the lead-hole plus face-countersink instruction. The pinned local
purchase note says #10 x 2-1/2 in, #2 Phillips drive, and names the Kobalt
80277 #10 pilot/countersink set. That set is the pilot/countersink choice; it
does not identify a #2 Phillips driver or show driver/hand clearance. T07’s
receiver-axis envelope is a historical CAD proxy, not actual Hillman
dimensions. The receipt amount and Hillman structural-property map remain
outside T08.

## Exact missing inputs

The row-level `missing_data` fields name the needed source for every axis. In
summary, candidate stacks need final product/lot identities; dimensioned
records or traceable measurements for the bolt thread transition/shank, matched
nut active thread/chamfer, washer/spacer dimensions and tolerances; selected
tools and current assembled-scene workspace; and a supported capture/reverse
sequence. The retained axes additionally need current WJ24 product/ownership
confirmation and current-candidate rechecks. The Hillman axes need exact
42605 lot dimensions/tolerances, a selected #2 Phillips driver/access screen,
and the checklist-recorded pilot/countersink offcut trial. These are named
source requirements, not requests to assume a clearance or select hardware.

## Reproduction

From the repository root:

```sh
python3 {HERE.relative_to(ROOT)}/build_crosswalk.py --write
python3 {HERE.relative_to(ROOT)}/build_crosswalk.py --check
```

`--check` reconstructs both outputs from the pinned T07/T08 packets, verifies
the transitive local-source hashes, enforces exact 92/12/66 identity joins,
and fails if any per-axis physical status is no longer unresolved. This
crosswalk is an evidence join, not a fit or engineering acceptance.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for path, expected in PACKET_HASHES.items():
        source = ROOT / path
        if not source.is_file() or sha256(source) != expected:
            print(f"packet hash mismatch: {path}", file=sys.stderr)
            return 2
    try:
        crosswalk = build_crosswalk()
    except (KeyError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"crosswalk verification failed: {exc}", file=sys.stderr)
        return 2
    json_text = json.dumps(crosswalk, indent=2, sort_keys=True) + "\n"
    readme_text = build_readme(crosswalk)
    if args.write:
        OUTPUT.write_text(json_text, encoding="utf-8")
        README.write_text(readme_text, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)} and {README.relative_to(ROOT)}")
        return 0
    if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != json_text:
        print("option-crosswalk.json differs from pinned-source reconstruction", file=sys.stderr)
        return 1
    if not README.is_file() or README.read_text(encoding="utf-8") != readme_text:
        print("README.md differs from pinned-source reconstruction", file=sys.stderr)
        return 1
    print("PASS T07/T08 option crosswalk; 92 candidate + 12 retained + 66 Hillman rows, all physical statuses unresolved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
