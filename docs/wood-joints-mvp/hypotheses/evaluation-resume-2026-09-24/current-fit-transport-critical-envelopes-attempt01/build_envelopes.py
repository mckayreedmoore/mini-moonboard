#!/usr/bin/env python3
"""Rebuild the narrow T07/T08 critical-envelope comparison from pinned inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
E = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
OUT = HERE / "critical-envelopes.json"

T07 = E / "current-fit-transport-closeout-attempt02"
T07_EVIDENCE = T07 / "evidence-register.json"
T07_REVIEW = T07 / "parent-review.json"
T07_PREPARE = T07 / "prepare.py"
T07_README = T07 / "README.md"
T07_CAND_ACCESS = E / "access-screen-attempt03-exact-components.json"
T07_RETAINED_ACCESS = E / "retained-access-attempt03/access.json"
T07_CAPTURED = E / "captured-nut-motion-attempt02/motion.json"
T07_TOOL = E / "step6-operation-coverage-attempt01/tool-route-feasibility-attempt01/tool-route-feasibility.json"

CROSS = E / "current-fit-transport-option-crosswalk-attempt01"
CROSS_JSON = CROSS / "option-crosswalk.json"
CROSS_README = CROSS / "README.md"
CROSS_BUILD = CROSS / "build_crosswalk.py"
CROSS_REVIEW = CROSS / "parent-review.json"

T08 = E / "current-hardware-material-cost-closeout-attempt01"
T08_REGISTER = T08 / "fastener-axis-register.json"
T08_SOURCE_PINS = T08 / "source-pins.json"
T08_REVIEW = T08 / "parent-review.json"
T08_README = T08 / "README.md"

EXPECTED_PARENT_HASHES = {
    "T07_attempt02_evidence": "dbfe1049d01f936bb034531699ff333d07916240c367851239fb665c1b4f17dc",
    "T07_attempt02_readme": "ba330faae47bc5ab0fe23e5c512e490b49295bb0627f94c28263cb85a47bba03",
    "T07_attempt02_prepare": "27baaa1602d26b71e1c0b0ddcbac928ef34fa7330de8c0bc0d79b9a0fc0cc6c1",
    "T07_attempt02_parent_review": "16ebe051397ff8270977a05c14ad0d99941cae6b97bdc1caede1fb68383bd950",
    "crosswalk_json": "3752fe2c47053dbcb4161d0a17b1fc9a5a1bd422fd2f9a35f3c8d05ddf791827",
    "crosswalk_readme": "2623c2a465f278e14ca75d615527c44a814af926a0e845d8da5eba83c30eef01",
    "crosswalk_build": "ee4c64314bf530997c380a06b8dda79253748db02ada4c577d71eeea089ddec4",
    "crosswalk_parent_review": "ef237bdda46071218c8777cd7613f1e406157f91f9801ca28d3dcf5137deb123",
    "T08_register": "c1e53e9a08599d13a992fc11a493853c1695f697f3fe99b45af20795c430240a",
    "T08_source_pins": "49c5a245fe67efaa192d280ef3e7eab3356e1571a19110c02ac94345cb1f7912",
    "T08_parent_review": "d9467f654743e640335248a1a785e5c6bc579e583e25cf747f585dd1a5b7f4c3",
    "T08_readme": "203f884837ab76a9d6de40ec497e6fc3052d08f52bbfa849687c44b1a8aee66c",
}

CANDIDATE_AXES = [
    "bottom_center/clip_horizontal_bottom_left_2/rail_2",
    "bottom_center/clip_horizontal_bottom_right_1/rail_2",
    "bottom_outer/clip_horizontal_bottom_left_1/rail_2",
    "bottom_outer/clip_horizontal_bottom_right_2/rail_2",
]
RETAINED_AXES = [
    "lumber_leg_bolt_left_1",
    "lumber_leg_bolt_left_2",
    "lumber_leg_bolt_right_1",
    "lumber_leg_bolt_right_2",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_path(path: str | Path) -> Path:
    return ROOT / Path(path)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def pointer_get(value: object, pointer: str) -> object:
    if pointer == "":
        return value
    current = value
    for part in pointer.lstrip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current[part]
        else:
            raise ValueError(f"JSON pointer traverses scalar at {part!r}: {pointer}")
    return current


def verify_parent_hashes() -> dict[str, str]:
    paths = {
        "T07_attempt02_evidence": T07_EVIDENCE,
        "T07_attempt02_readme": T07_README,
        "T07_attempt02_prepare": T07_PREPARE,
        "T07_attempt02_parent_review": T07_REVIEW,
        "crosswalk_json": CROSS_JSON,
        "crosswalk_readme": CROSS_README,
        "crosswalk_build": CROSS_BUILD,
        "crosswalk_parent_review": CROSS_REVIEW,
        "T08_register": T08_REGISTER,
        "T08_source_pins": T08_SOURCE_PINS,
        "T08_parent_review": T08_REVIEW,
        "T08_readme": T08_README,
    }
    actual: dict[str, str] = {}
    for key, relpath in paths.items():
        path = repo_path(relpath)
        require(path.is_file(), f"missing pinned authority file: {relpath}")
        actual[key] = digest(path)
        require(actual[key] == EXPECTED_PARENT_HASHES[key], f"pinned authority changed: {relpath}")
    t07_review = load(repo_path(T07_REVIEW))
    cross_review = load(repo_path(CROSS_REVIEW))
    t08_review = load(repo_path(T08_REVIEW))
    require(t07_review["status"] == "PASS_IDENTITY_REGISTER_ONLY_OPERATION_GATES_OPEN", "unexpected T07 review status")
    require(cross_review["status"] == "PASS_SOURCE_BOUND_OPTION_CROSSWALK_ONLY_ALL_PHYSICAL_GATES_OPEN", "unexpected crosswalk review status")
    require(t08_review["status"] == "PASS_SOURCE_BOUND_REGISTER_ONLY_WITH_PENDING_PRODUCT_MATERIAL_PRICE_GATES", "unexpected T08 review status")
    return actual


def collect_source_hashes() -> tuple[list[dict[str, str]], dict[str, int]]:
    """Rehash every transitive source pin in T07, T08 and the reviewed crosswalk."""
    t07 = load(repo_path(T07_EVIDENCE))
    t08 = load(repo_path(T08_SOURCE_PINS))
    cross = load(repo_path(CROSS_JSON))
    by_path: dict[str, dict[str, str]] = {}

    def add(path: str, expected: str, role: str, owner: str) -> None:
        target = repo_path(path)
        require(target.is_file(), f"missing source pin {path} ({owner})")
        actual = digest(target)
        require(actual == expected, f"source hash mismatch for {path}: expected {expected}, got {actual}")
        prior = by_path.get(path)
        if prior:
            require(prior["sha256"] == actual, f"conflicting source pin for {path}")
            prior["roles"] = prior["roles"] + f"; {owner}: {role}"
        else:
            by_path[path] = {"path": path, "sha256": actual, "roles": f"{owner}: {role}"}

    for pin in t07["source_pins"]:
        add(pin["path"], pin["sha256"], pin["role"], "T07 attempt02")
    for pin in t08["source_files"]:
        require(pin["status"] == "match", f"T08 source pin was not matching: {pin['path']}")
        require(pin["expected_sha256_at_inventory"] == pin["actual_sha256_at_build"], f"T08 pin mismatch in register: {pin['path']}")
        add(pin["path"], pin["expected_sha256_at_inventory"], pin["role"], "T08 attempt01")
    for pin in cross["source_hashes_verified"]:
        add(pin["path"], pin["sha256"], pin["role"], "T07/T08 crosswalk")
    counts = {"T07_attempt02_pins": len(t07["source_pins"]), "T08_attempt01_pins": len(t08["source_files"]), "crosswalk_pins": len(cross["source_hashes_verified"]), "unique_source_paths": len(by_path)}
    return sorted(by_path.values(), key=lambda row: row["path"]), counts


def inch(value: str) -> Decimal:
    """Exact fractional or decimal inch to millimetre conversion."""
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        inches = Decimal(numerator) / Decimal(denominator)
    else:
        inches = Decimal(value)
    return inches * Decimal("25.4")


def conversion(value: str) -> str:
    return format(inch(value), "f")


def catalog_record_index(t08: dict, lead_id: str) -> tuple[int, dict]:
    matches = [(i, row) for i, row in enumerate(t08["catalog_product_records"]) if row["id"] == lead_id]
    require(len(matches) == 1, f"expected one catalog record for {lead_id}")
    return matches[0]


def lead_pointer(t08: dict, lead_id: str, file_hash: str) -> dict:
    i, rec = catalog_record_index(t08, lead_id)
    return {
        "path": str(T08_REGISTER),
        "file_sha256": file_hash,
        "json_pointer": f"/catalog_product_records/{i}",
        "record_sha256_canonical_json": canonical_digest(rec),
    }


def build() -> dict:
    pinned_control_hashes = verify_parent_hashes()
    source_hashes, source_counts = collect_source_hashes()
    evidence = load(repo_path(T07_EVIDENCE))
    cross = load(repo_path(CROSS_JSON))
    t08 = load(repo_path(T08_REGISTER))
    candidate_access = load(repo_path(T07_CAND_ACCESS))
    retained_access = load(repo_path(T07_RETAINED_ACCESS))
    captured = load(repo_path(T07_CAPTURED))
    tool_route = load(repo_path(T07_TOOL))

    require(cross["status"] == "source_bound_option_crosswalk_physical_fit_and_transport_unresolved", "unexpected crosswalk payload status")
    require(cross["geometry_revision_id"] == evidence["geometry_revision_id"] == t08["geometry_revision_id"], "geometry revision mismatch")
    require(t08["counts"]["candidate_bolt_axes"] == 92 and t08["counts"]["retained_starting_frame_bolt_axes"] == 12, "unexpected T08 axis inventory")

    cross_by_axis = {row["axis_id"]: row for row in cross["rows"]}
    require(len(cross_by_axis) == 170, "crosswalk row count changed")
    t07_access_by_axis = {row["axis_id"]: row for row in candidate_access["axis_operations"]}
    retained_access_by_axis = {row["axis_id"]: row for row in retained_access["axis_operations"]}
    captured_by_axis = {row["axis_id"]: row for row in captured["axis_operations"]}
    captured_summary_by_axis = {row["axis_id"]: row for row in evidence["candidate_nut_slide_findings"]["captured_local_route"]["rows"]}
    t08_candidate_by_axis = {row["axis_id"]: row for row in t08["candidate_axis_rows"]}
    t08_retained_by_axis = {row["axis_id"]: row for row in t08["retained_axis_rows"]}
    proxy_by_axis = {row["axis_id"]: row for row in tool_route["existing_synthetic_tool_proxy_rows"]}

    candidate_hit_rows = tool_route["candidate_nut_slide_hits"]["hits"]
    require(len(candidate_hit_rows) == 6, "expected six direct candidate nut/washer hits")
    require(sorted({row["axis_id"] for row in candidate_hit_rows}) == sorted(CANDIDATE_AXES), "candidate hit axis set changed")
    require(len(tool_route["retained_frame_bolt_wire_hits"]["rows"]) == 4, "expected four retained wire stack reports")
    retained_hit_count = sum(len(row["component_intersections"]) for row in tool_route["retained_frame_bolt_wire_hits"]["rows"])
    require(retained_hit_count == 12, "expected twelve retained wire component sweeps")

    t07_file_hashes = {
        str(T07_EVIDENCE): digest(repo_path(T07_EVIDENCE)),
        str(T07_CAND_ACCESS): digest(repo_path(T07_CAND_ACCESS)),
        str(T07_RETAINED_ACCESS): digest(repo_path(T07_RETAINED_ACCESS)),
        str(T07_CAPTURED): digest(repo_path(T07_CAPTURED)),
        str(T07_TOOL): digest(repo_path(T07_TOOL)),
        str(CROSS_JSON): digest(repo_path(CROSS_JSON)),
        str(T08_REGISTER): digest(repo_path(T08_REGISTER)),
    }
    require(t07_file_hashes[str(T07_CAND_ACCESS)] == "bd2b97c0677b2e0ab5b09898ba7f2227758088744cd93f7e3c9b266bce5c5215", "candidate access report changed")
    require(t07_file_hashes[str(T07_RETAINED_ACCESS)] == "fffa0027926a57583cc13ffbcef552fc8e5f8da96964d50c64ef63ffd4ce4c97", "retained access report changed")
    require(t07_file_hashes[str(T07_CAPTURED)] == "83c905bec64010695c769a73d7b8923869ef1aef5bda9b8591cdad0d443b21a4", "captured motion report changed")
    require(t07_file_hashes[str(T07_TOOL)] == "f7848741b4e3edbc15b36084bc5a89f884cea38e1f39c8edfe26527e4eb1b292", "focused tool route report changed")

    # Crosswalk pointers are checked against their actual T08 source row, not labels alone.
    for axis in CANDIDATE_AXES + RETAINED_AXES:
        row = cross_by_axis[axis]
        ptr = row["t08_fastener_axis_pointer"]
        require(ptr["file_sha256"] == t07_file_hashes[str(T08_REGISTER)], f"crosswalk T08 file pin mismatch for {axis}")
        indexed_row = pointer_get(t08, ptr["json_pointer"])
        require(indexed_row["axis_id"] == axis, f"crosswalk T08 pointer identity mismatch for {axis}")
        require(canonical_digest(indexed_row) == ptr["record_sha256_canonical_json"], f"crosswalk T08 record hash mismatch for {axis}")
        require(row["physical_clearance"] == "unresolved", f"crosswalk fit unexpectedly cleared for {axis}")
        require(all(value == "unresolved" for value in row["physical_status_after_crosswalk"].values()), f"physical status unexpectedly cleared for {axis}")
        require(row["catalog_option"].get("selected_product") is None, f"product unexpectedly selected for {axis}")
        if row["inventory_class"] == "candidate_bolt_axis":
            require(indexed_row["selected_product"] is None, f"T08 selected product unexpectedly set for {axis}")
        else:
            require(indexed_row["selected_for_wood_joints"] is False, f"retained reference unexpectedly selected for WJ use: {axis}")

    # Pull exact catalog lead texts and separately expose only dimensions in those texts.
    catalog_leads = {}
    for lead_id in ["kl-25cnfh5z", "kl-25nwus", "mcmaster-91201a029", "kl-25c600hcs5z", "hs-104-044", "wurth-072-14-6"]:
        i, record = catalog_record_index(t08, lead_id)
        catalog_leads[lead_id] = {
            "lead_id": lead_id,
            "vendor": record["vendor"],
            "part_number": record["part_number"],
            "role": record["role"],
            "spec": record["spec"],
            "thread_field": record["thread_field"],
            "conditional_only": True,
            "selected_product": None,
            "pointer": lead_pointer(t08, lead_id, t07_file_hashes[str(T08_REGISTER)]),
        }
    require("7/16 in hex" in catalog_leads["kl-25cnfh5z"]["spec"] and "7/32 in nominal thickness" in catalog_leads["kl-25cnfh5z"]["spec"], "candidate nut dimensions no longer match the declared comparator")
    require(all(token in catalog_leads["kl-25nwus"]["spec"] for token in ["0.312 in", "47/64 in", "0.051-0.080 in"]), "candidate washer dimensions no longer match the declared comparator")
    require(all(token in catalog_leads["mcmaster-91201a029"]["spec"] for token in ["0.281 in", "0.625 in", "0.120-0.130 in"]), "conditional spacer dimensions no longer match the declared comparator")
    for axis in CANDIDATE_AXES:
        option = cross_by_axis[axis]["catalog_option"]
        require(option["family_id"] == "candidate_ordinary_48", f"unexpected candidate family for {axis}")
        require(option["conditional_component_lead_ids"]["conditional_nut_leads"] == ["kl-25cnfh5z"], f"candidate nut lead join mismatch for {axis}")
        require(option["conditional_component_lead_ids"]["conditional_washer_leads"] == ["kl-25nwus"], f"candidate washer lead join mismatch for {axis}")
        require(option["candidate_product_lead_ids"] == ["kl-25c600hcs5z", "hs-104-044", "wurth-072-14-6"], f"candidate bolt lead join mismatch for {axis}")
    candidate_catalog_dimensions = {
        "nut_lead": "kl-25cnfh5z",
        "nut": {"across_flats_in": "7/16", "across_flats_mm": conversion("7/16"), "nominal_thickness_in": "7/32", "nominal_thickness_mm": conversion("7/32")},
        "washer_lead": "kl-25nwus",
        "washer": {"inside_diameter_in": "0.312", "inside_diameter_mm": conversion("0.312"), "outside_diameter_in": "47/64", "outside_diameter_mm": conversion("47/64"), "thickness_in": ["0.051", "0.080"], "thickness_mm": [conversion("0.051"), conversion("0.080")]},
        "conditional_spacer_lead": "mcmaster-91201a029",
        "conditional_spacer": {"inside_diameter_in": "0.281", "inside_diameter_mm": conversion("0.281"), "outside_diameter_in": "0.625", "outside_diameter_mm": conversion("0.625"), "thickness_in": ["0.120", "0.130"], "thickness_mm": [conversion("0.120"), conversion("0.130")], "role_status": "conditional_geometry_lead_only_not_accepted_support"},
        "bolt_leads": ["kl-25c600hcs5z", "hs-104-044", "wurth-072-14-6"],
        "bolt_lead_dimension_summary": "Each listed lead states a 7/16-in hex/head width and provides a head-height phrase; the lead descriptions differ and none is selected. Exact source wording is preserved under catalog_leads.",
        "comparability_limit": "These source dimensions do not establish that the current T07 BRep component proxies match any listed lead. No BRep rescaling or product-to-model identity is asserted.",
    }

    profile_by_id = {row["id"]: row for row in cross["source_supported_tool_profile_comparators"]}
    candidate_profiles = [profile_by_id["facom_34_7_16"], profile_by_id["wera_6000_05073282001"]]
    retained_profile = profile_by_id["wera_6000_05073287001"]
    require(profile_by_id["facom_34_7_16"]["size"] == "7/16 in" and profile_by_id["wera_6000_05073282001"]["size"] == "7/16 in", "candidate tool comparator size changed")
    require(retained_profile["size"] == "3/4 in", "retained size-matched comparator changed")

    candidate_component_matrix = []
    for i, hit in enumerate(candidate_hit_rows):
        axis = hit["axis_id"]
        cross_row = cross_by_axis[axis]
        t07_axis = t07_access_by_axis[axis]
        hit_pointer = f"/candidate_nut_slide_hits/hits/{i}"
        comp = hit["component_role"]
        env = cross_row["component_envelope_fields"]["t07_bolt_nut_washer_motion_screens"][comp]
        removal = env["removal"]
        require(removal["external_envelope_clear"] is False, f"candidate crosswalk component no longer has direct hit: {axis}/{comp}")
        exact_intersection = hit["intersections"]
        require(len(exact_intersection) == 1, f"unexpected blocker count: {axis}/{comp}")
        cross_volumes = removal["hit_volumes_mm3"][f"{comp}_axial_slide_enclosure"]
        require(cross_volumes.get(exact_intersection[0]["blocker_id"]) == exact_intersection[0]["volume_mm3"], f"candidate overlap does not match crosswalk source: {axis}/{comp}")
        require(env["modeled_axial_travel_mm"] == hit["travel_mm"], f"candidate component travel mismatch: {axis}/{comp}")
        tool_summary = proxy_by_axis[axis]["sides"]
        local = captured_summary_by_axis[axis]
        row_index = candidate_access["axis_operations"].index(t07_axis)
        candidate_component_matrix.append({
            "axis_id": axis,
            "component_role": comp,
            "obstacle_id": exact_intersection[0]["blocker_id"],
            "source_cad_proxy_intersection_volume_mm3": exact_intersection[0]["volume_mm3"],
            "modeled_axial_slide_travel_mm": hit["travel_mm"],
            "screen_result": hit["screen_result"],
            "crosswalk_direct_removal_external_envelope_clear": removal["external_envelope_clear"],
            "crosswalk_reverse_insertion_external_envelope_clear": env["reverse_insertion"]["external_envelope_clear"],
            "component_to_catalog_comparator": "conditional 1/4-20 stack leads listed separately; current BRep-to-lead equivalence absent",
            "tool_proxy_profile_id": tool_summary["nut_end"]["candidate_id"],
            "tool_proxy_approach_checks": tool_summary["nut_end"]["approach_proxy_check_count"],
            "tool_proxy_approach_clear_count": tool_summary["nut_end"]["approach_proxy_clear_count"],
            "tool_proxy_turn_pose_checks": tool_summary["nut_end"]["turn_pose_check_count"],
            "tool_proxy_turn_pose_clear_count": tool_summary["nut_end"]["turn_pose_clear_count"],
            "synthetic_tool_proxy_sides": {side: {k: v for k, v in fields.items() if k in ["candidate_id", "approach_proxy_check_count", "approach_proxy_clear_count", "turn_pose_check_count", "turn_pose_clear_count", "profile_is_current_selected_tool_or_fit"]} for side, fields in tool_summary.items()},
            "tool_proxy_is_selected_or_physical_access": False,
            "existing_captured_local_route_id": axis,
            "captured_local_route_external_geometry_clear": local["clear_local_option"]["external_geometry_clear"],
            "captured_route_requires_unthreading_assumption": local["thread_compatible_unthreading_assumed"],
            "captured_route_part_staging_established": local["full_part_staging_established"],
            "captured_route_component_capture_established": local["nut_and_washer_capture_established"],
            "source_pointer": {
                "t07_focused_report": {"path": str(T07_TOOL), "file_sha256": t07_file_hashes[str(T07_TOOL)], "json_pointer": hit_pointer},
                "t07_exact_axis_access": {"path": str(T07_CAND_ACCESS), "file_sha256": t07_file_hashes[str(T07_CAND_ACCESS)], "json_pointer": f"/axis_operations/{row_index}"},
                "t07_captured_motion": {"path": str(T07_CAPTURED), "file_sha256": t07_file_hashes[str(T07_CAPTURED)], "json_pointer": f"/axis_operations/{captured['axis_operations'].index(captured_by_axis[axis])}"},
                "t07_attempt02_axis_register": {"path": str(T07_EVIDENCE), "file_sha256": t07_file_hashes[str(T07_EVIDENCE)], "json_pointer": cross_row["t07_pointer"]["json_pointer"], "record_sha256_canonical_json": cross_row["t07_pointer"]["record_sha256_canonical_json"]},
                "t08_fastener_axis": cross_row["t08_fastener_axis_pointer"],
            },
        })

    retained_component_matrix = []
    retained_tool_rows = {row["axis_id"]: row for row in tool_route["retained_frame_bolt_wire_hits"]["rows"]}
    for axis in RETAINED_AXES:
        cross_row = cross_by_axis[axis]
        t07_axis = retained_access_by_axis[axis]
        t08_axis = t08_retained_by_axis[axis]
        hit_row = retained_tool_rows[axis]
        retained_access_index = retained_access["axis_operations"].index(t07_axis)
        source_geometry = cross_row["component_envelope_fields"]["source_geometry_row"]
        ref_summary = cross_row["catalog_option"]["family_reference_summary"]
        max_match = re.search(r"#2573 noted maximum ([0-9.]+) mm", ref_summary["disposition"])
        require(max_match is not None, f"source #2573 dimensional comparator missing for {axis}")
        cited_nut_max_mm = float(max_match.group(1))
        cad_nut_height_mm = float(source_geometry["nut_height_mm"])
        operation = t07_axis["operations"]["head_side_bolt"]
        withdrawal = operation["withdrawal"]["collision_screen"]
        reverse = operation["reverse_assembly"]["collision_screen"]
        require(operation["derived_travel_mm"] == 200.025, f"retained withdrawal changed for {axis}")
        require(withdrawal["external_envelope_clear"] is False and reverse["external_envelope_clear"] is False, f"retained modeled route unexpectedly clear for {axis}")
        require(hit_row["physical_cable_blockage_established"] is False and hit_row["flexible_cable_service_route_established"] is False, f"physical cable status unexpectedly cleared for {axis}")
        for j, hit in enumerate(hit_row["component_intersections"]):
            withdrawal_component_volumes = withdrawal["external_envelope_hits_mm3"].get(hit["component_sweep"], {})
            reverse_component_volumes = reverse["external_envelope_hits_mm3"].get(hit["component_sweep"], {})
            require(withdrawal_component_volumes.get(hit["blocker_id"]) == hit["intersection_volume_mm3"], f"retained withdrawal intersection mismatch: {axis}/{hit['component_sweep']}")
            require(reverse_component_volumes.get(hit["blocker_id"]) == hit["intersection_volume_mm3"], f"retained reverse intersection mismatch: {axis}/{hit['component_sweep']}")
            retained_component_matrix.append({
                "axis_id": axis,
                "component_role": hit["component_sweep"],
                "obstacle_id": hit["blocker_id"],
                "source_cad_proxy_intersection_volume_mm3": hit["intersection_volume_mm3"],
                "modeled_joint_stack_withdrawal_mm": operation["derived_travel_mm"],
                "modeled_motion": operation["withdrawal"]["motion_direction"],
                "withdrawal_wire_envelope_clear": withdrawal["external_envelope_clear"],
                "reverse_insertion_wire_envelope_clear": reverse["external_envelope_clear"],
                "wire_is_flexible_physical_cable_blockage_established": hit_row["physical_cable_blockage_established"],
                "T08_reference_only": t08_axis["catalog_reference"],
                "catalog_bolt_head_across_flats_in": "3/4",
                "catalog_bolt_head_across_flats_mm": conversion("3/4"),
                "catalog_nut_comparator_limit": "#2573 is a baseline catalog reference only; the T08 family record does not assign a current WJ product or delivered lot.",
                "cad_nut_envelope_height_mm": cad_nut_height_mm,
                "cited_2573_max_height_mm": cited_nut_max_mm,
                "cad_minus_cited_nut_max_height_mm": round(cad_nut_height_mm - cited_nut_max_mm, 4),
                "T07_applied_proxy_profile_id": "facom_34_7_16",
                "T07_proxy_head_size_mismatch_to_3_4_in_reference": True,
                "correct_size_profile_comparator_id": retained_profile["id"],
                "correct_size_profile_comparator_dimensions": retained_profile["published_profile"],
                "correct_size_profile_fit_screened": False,
                "selected_tool_or_physical_access_established": False,
                "source_pointer": {
                    "t07_focused_report": {"path": str(T07_TOOL), "file_sha256": t07_file_hashes[str(T07_TOOL)], "json_pointer": f"/retained_frame_bolt_wire_hits/rows/{tool_route['retained_frame_bolt_wire_hits']['rows'].index(hit_row)}/component_intersections/{j}"},
                    "t07_retained_access": {"path": str(T07_RETAINED_ACCESS), "file_sha256": t07_file_hashes[str(T07_RETAINED_ACCESS)], "json_pointer": f"/axis_operations/{retained_access_index}/operations/head_side_bolt"},
                    "t07_attempt02_axis_register": {"path": str(T07_EVIDENCE), "file_sha256": t07_file_hashes[str(T07_EVIDENCE)], "json_pointer": cross_row["t07_pointer"]["json_pointer"], "record_sha256_canonical_json": cross_row["t07_pointer"]["record_sha256_canonical_json"]},
                    "t08_fastener_axis": cross_row["t08_fastener_axis_pointer"],
                    "retained_catalog_reference": cross_row["catalog_option"]["family_reference_pointer"],
                    "T07_geometry_csv_row": cross_row["component_envelope_fields"]["source_geometry_pointer"],
                },
            })

    require(len(candidate_component_matrix) == 6, "candidate output matrix must contain six direct hits")
    require(len(retained_component_matrix) == 12, "retained output matrix must contain twelve component hits")

    candidate_routes = []
    for axis in CANDIDATE_AXES:
        summary = captured_summary_by_axis[axis]
        motion = captured_by_axis[axis]
        clear_options = [option for option in motion["lateral_then_axial_options"] if option["two_stage_cad_motion_clear"] is True]
        require(len(clear_options) == 1, f"expected exactly one clear two-stage CAD option for {axis}")
        option = clear_options[0]
        require(option["lateral_collision"]["external_envelope_clear"] is True and option["following_nutward_collision"]["external_envelope_clear"] is True, f"two-stage route collision component mismatch for {axis}")
        require(motion["headward_external_collision"]["external_envelope_clear"] is True, f"separate headward path no longer CAD-clear for {axis}")
        require(summary["clear_local_option"]["external_geometry_clear"] is True, f"attempt02 route summary no longer clear for {axis}")
        require(option["lateral_displacement_xyz_mm"] == summary["clear_local_option"]["lateral_displacement_xyz_mm"], f"local route vector mismatch for {axis}")
        require(option["following_nutward_displacement_xyz_mm"] == summary["clear_local_option"]["following_nutward_displacement_xyz_mm"], f"local route nutward vector mismatch for {axis}")
        candidate_routes.append({
            "axis_id": axis,
            "route_status": "bounded source-CAD local route; not complete install/removal route",
            "lateral_first_displacement_xyz_mm": option["lateral_displacement_xyz_mm"],
            "second_nutward_displacement_xyz_mm": option["following_nutward_displacement_xyz_mm"],
            "second_nutward_travel_mm": summary["clear_local_option"]["following_nutward_travel_mm"],
            "external_geometry_clear": summary["clear_local_option"]["external_geometry_clear"],
            "separate_headward_bolt_path_external_geometry_clear": motion["headward_external_collision"]["external_envelope_clear"],
            "headward_bolt_travel_mm_in_separate_screen": summary["headward_bolt_travel_mm"],
            "headward_terminal_allowance_mm_in_diagnostic": summary["headward_terminal_allowance_mm"],
            "thread_compatible_unthreading_assumed": summary["thread_compatible_unthreading_assumed"],
            "shaft_nut_display_envelope_overlap_mm3": summary["shaft_nut_display_envelope_overlap_mm3"],
            "component_capture_established": summary["nut_and_washer_capture_established"],
            "full_part_staging_established": summary["full_part_staging_established"],
            "reverse_assembly_screened": summary["reverse_assembly_screened"],
            "source_pointer": {
                "t07_attempt02_route_summary": {"path": str(T07_EVIDENCE), "file_sha256": t07_file_hashes[str(T07_EVIDENCE)], "json_pointer": f"/candidate_nut_slide_findings/captured_local_route/rows/{evidence['candidate_nut_slide_findings']['captured_local_route']['rows'].index(summary)}"},
                "t07_captured_motion": {"path": str(T07_CAPTURED), "file_sha256": t07_file_hashes[str(T07_CAPTURED)], "json_pointer": f"/axis_operations/{captured['axis_operations'].index(motion)}/lateral_then_axial_options/{motion['lateral_then_axial_options'].index(option)}"},
            },
        })

    retained_routes = []
    for axis in RETAINED_AXES:
        row = retained_tool_rows[axis]
        access_axis = retained_access_by_axis[axis]
        nut_travel = access_axis["operations"]["nut"]["derived_axial_travel_mm"]
        washer_travel = access_axis["operations"]["nut_washer"]["derived_axial_travel_mm"]
        require(nut_travel == 19.05 and washer_travel == 22.225, f"retained nut/washer axial travel changed for {axis}")
        proxy_sides = proxy_by_axis[axis]["sides"]
        retained_routes.append({
            "axis_id": axis,
            "head_headwasher_shaft_withdrawal_mm": 200.025,
            "head_side_wire_obstacle_ids": sorted({hit["blocker_id"] for hit in row["component_intersections"]}),
            "head_side_component_sweeps_clear": False,
            "modeled_nut_axial_removal_mm": nut_travel,
            "modeled_nut_axial_removal_envelope_clear": retained_access_by_axis[axis]["operations"]["nut"]["removal"]["collision_screen"]["external_envelope_clear"],
            "modeled_nut_washer_axial_removal_mm": washer_travel,
            "modeled_nut_washer_axial_removal_envelope_clear": retained_access_by_axis[axis]["operations"]["nut_washer"]["removal"]["collision_screen"]["external_envelope_clear"],
            "component_capture_support_transfer_established": False,
            "reverse_insertion_physical_route_established": row["reverse_insertion_physical_route_established"],
            "flexible_wire_service_route_established": row["flexible_cable_service_route_established"],
            "applied_7_16_in_tool_proxy_screen_summary": {side: {k: v for k, v in fields.items() if k in ["approach_proxy_check_count", "approach_proxy_clear_count", "turn_pose_check_count", "turn_pose_clear_count", "profile_is_current_selected_tool_or_fit"]} for side, fields in proxy_sides.items()},
            "source_pointer": {"path": str(T07_TOOL), "file_sha256": t07_file_hashes[str(T07_TOOL)], "json_pointer": f"/retained_frame_bolt_wire_hits/rows/{tool_route['retained_frame_bolt_wire_hits']['rows'].index(row)}"},
        })

    return {
        "schema": "wood_joint_current_fit_transport_critical_envelopes/v1",
        "attempt": "current-fit-transport-critical-envelopes-attempt01",
        "status": "SOURCE_BOUND_NOMINAL_ENVELOPE_COMPARISON_ONLY",
        "geometry_revision_id": evidence["geometry_revision_id"],
        "source_authority": {
            "T07_parent_status": load(repo_path(T07_REVIEW))["status"],
            "crosswalk_parent_status": load(repo_path(CROSS_REVIEW))["status"],
            "T08_parent_status": load(repo_path(T08_REVIEW))["status"],
            "all_prior_physical_operation_gates_remain_open": True,
            "control_artifact_hashes": pinned_control_hashes,
            "transitive_source_pins": source_hashes,
            "verified_source_pin_counts": source_counts,
            "critical_input_hashes": t07_file_hashes,
        },
        "scope": {
            "candidate_axes": CANDIDATE_AXES,
            "candidate_direct_component_hit_count": 6,
            "retained_leg_bolt_axes": RETAINED_AXES,
            "retained_component_sweep_hit_count": 12,
            "interpretation": "Reported volumes and clearances are source-CAD/proxy sweep results for the pinned current geometry and assumptions. They are not physical interference/clearance, delivered-part fit, selected-tool fit, hand workspace, or installation/removal acceptance.",
            "excluded": ["product/tool selection", "geometry edits", "vendor contact", "physical activity", "native solves", "fit or transport acceptance changes"],
        },
        "conditional_candidate_component_dimensions": candidate_catalog_dimensions,
        "candidate_catalog_leads": catalog_leads,
        "conditional_tool_profile_comparators": {
            "candidate_nut_7_16_in_profile_comparators": candidate_profiles,
            "retained_bolt_3_4_in_profile_comparator": retained_profile,
            "interpretation": "Nominal size match is only a comparator. Full tool geometry, engagement, approach/turning, hands, counterhold and workspace remain unscreened for the right-sized comparators.",
        },
        "candidate_direct_hit_matrix": candidate_component_matrix,
        "retained_wire_component_hit_matrix": retained_component_matrix,
        "candidate_existing_local_route_matrix": candidate_routes,
        "retained_existing_withdrawal_and_reverse_route_matrix": retained_routes,
        "missing_evidence": [
            {"scope": "candidate four axes", "needed": "Axis-assigned selected/delivered bolt, matched nut and washer/spacer identity; actual dimensional/tolerance records and measurements, including functional thread interval; source BRep-to-delivered-part reconciliation; then rerun the direct and local-route sweeps with a selected, dimensioned tool and tolerance margin.", "physical_status": "unresolved"},
            {"scope": "retained four leg-bolt axes", "needed": "Current delivered #407/#2573/#15025 stack dimensions/lot fit and selected 3/4-in tool plus counterhold profiles; a source-supported, reversible wire/harness service state or measured flexible-cable envelope; rerun the three component sweeps, wire service route, support/capture and reverse insertion in that state.", "physical_status": "unresolved"},
            {"scope": "all eight affected stacks", "needed": "Part capture, support transfer, loose-part staging, hand/tool workspace, tolerance allowance and a complete two-way sequence tied to exact operation states; current local/axial envelope findings do not cover these.", "physical_status": "unresolved"},
        ],
        "release_boundary": {
            "selected_product_or_tool": False,
            "delivered_fit_established": False,
            "physical_tool_access_established": False,
            "installation_or_removal_established": False,
            "cable_service_established": False,
            "part_capture_support_or_staging_established": False,
            "full_frame_transport_cleared": False,
            "fabrication_or_physical_work_authorized": False,
            "candidate_acceptance_changed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        data = build()
        rendered = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        if args.write:
            OUT.write_text(rendered, encoding="utf-8")
            print(f"WROTE {OUT.relative_to(ROOT)} sha256={digest(OUT)}")
            return 0
        if not OUT.is_file():
            raise ValueError(f"missing generated output: {OUT}")
        existing = OUT.read_text(encoding="utf-8")
        if existing != rendered:
            raise ValueError("generated critical-envelopes.json differs; run --write in this owned folder")
        print(f"PASS {OUT.relative_to(ROOT)} sha256={digest(OUT)}")
        print("PASS 6 candidate hits / 4 candidate axes; 12 retained wire sweeps / 4 retained axes")
        print(f"PASS {len(data['source_authority']['transitive_source_pins'])} unique transitive source pins rehashed")
        print("PASS right-sized profiles are retained as comparators only; all physical-operation/release flags remain false")
        return 0
    except (OSError, KeyError, TypeError, ValueError, IndexError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
