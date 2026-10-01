#!/usr/bin/env python3
"""Independent source and identity checks for the T07/T08 crosswalk."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
HERE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-fit-transport-option-crosswalk-attempt01"
CROSSWALK = HERE / "option-crosswalk.json"
T07_REVIEW = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-fit-transport-closeout-attempt02/parent-review.json"
T08_REVIEW = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt01/parent-review.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return sha256_bytes(encoded)


def json_pointer(value: Any, pointer: str) -> Any:
    current = value
    if not pointer:
        return current
    for token in pointer.lstrip("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def check_lead_record(root: Path, lead: dict[str, Any], pointer_key: str) -> list[str]:
    errors: list[str] = []
    pointer = lead[pointer_key]
    path = root / pointer["path"]
    if not path.is_file() or sha256_file(path) != pointer["file_sha256"]:
        return [f"lead file hash mismatch: {lead.get('id')}" ]
    source = json.loads(path.read_text(encoding="utf-8"))
    record = json_pointer(source, pointer["json_pointer"])
    if canonical_sha256(record) != pointer["record_sha256_canonical_json"]:
        errors.append(f"lead record hash mismatch: {lead.get('id')}")
    for key in ("id", "role", "part_number", "spec", "thread_field", "vendor"):
        if lead.get(key) != record.get(key):
            errors.append(f"lead {key} mismatch: {lead.get('id')}")
    return errors


def main() -> int:
    packet = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    t07_review = json.loads(T07_REVIEW.read_text(encoding="utf-8"))
    t08_review = json.loads(T08_REVIEW.read_text(encoding="utf-8"))
    assert t07_review["status"] == "PASS_IDENTITY_REGISTER_ONLY_OPERATION_GATES_OPEN"
    assert t08_review["status"] == "PASS_SOURCE_BOUND_REGISTER_ONLY_WITH_PENDING_PRODUCT_MATERIAL_PRICE_GATES"
    assert packet["candidate_id"] == "compact-floor-flush-wood-joints-development"
    assert packet["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1"
    assert packet["selected_candidate_authority_preserved"] == "compact-floor-flush-development"
    assert packet["status"] == "source_bound_option_crosswalk_physical_fit_and_transport_unresolved"

    errors: list[str] = []
    for pin in packet["source_hashes_verified"]:
        path = ROOT / pin["path"]
        if not path.is_file() or sha256_file(path) != pin["sha256"]:
            errors.append(f"source hash mismatch: {pin['path']}")

    lead_index: dict[str, dict[str, Any]] = {}
    for lead in packet["candidate_catalog_lead_record_index"]:
        if lead["id"] in lead_index:
            errors.append(f"duplicate catalog lead ID: {lead['id']}")
        lead_index[lead["id"]] = lead
        errors.extend(check_lead_record(ROOT, lead, "pointer"))

    expected_counts = {
        "candidate_bolt_axis": 92,
        "retained_frame_bolt_axis": 12,
        "hillman_panel_kicker_axis": 66,
    }
    category_rows = {
        category: [row for row in packet["rows"] if row["inventory_class"] == category]
        for category in expected_counts
    }
    for category, expected in expected_counts.items():
        rows = category_rows[category]
        if len(rows) != expected or len({row["axis_id"] for row in rows}) != expected:
            errors.append(f"{category}: expected {expected} unique rows, got {len(rows)}")

    for index, row in enumerate(packet["rows"]):
        if row["geometry_revision_id"] != packet["geometry_revision_id"]:
            errors.append(f"row {index}: wrong geometry revision")
        for key in ("t07_pointer", "t08_fastener_axis_pointer"):
            pointer = row[key]
            source_path = ROOT / pointer["path"]
            if not source_path.is_file() or sha256_file(source_path) != pointer["file_sha256"]:
                errors.append(f"row {index}: {key} file hash mismatch")
                continue
            source = json.loads(source_path.read_text(encoding="utf-8"))
            record = json_pointer(source, pointer["json_pointer"])
            if canonical_sha256(record) != pointer["record_sha256_canonical_json"]:
                errors.append(f"row {index}: {key} record hash mismatch")
            if record.get("axis_id") != row["axis_id"]:
                errors.append(f"row {index}: {key} axis mismatch")

        physical = row["physical_status_after_crosswalk"]
        if set(physical.values()) != {"unresolved"}:
            errors.append(f"row {index}: physical status was resolved")
        if row["physical_clearance"] != "unresolved":
            errors.append(f"row {index}: physical clearance was asserted")
        if row["fit_or_tool_acceptance"] != "not established":
            errors.append(f"row {index}: fit/tool acceptance was asserted")

        if row["inventory_class"] == "candidate_bolt_axis":
            if row["catalog_option"].get("selected_product") is not None:
                errors.append(f"row {index}: candidate product selected")
            option = row["catalog_option"]
            lead_records = option["lead_records"]
            lead_groups = {
                "candidate_product_lead_ids": ("bolt_leads", "bolt"),
                "conditional_nut_leads": ("conditional_nut_leads", "nut"),
                "conditional_washer_leads": ("conditional_washer_leads", "washer"),
                "conditional_spacer_leads": ("conditional_spacer_leads", "conditional_spacer"),
            }
            component_ids = option["conditional_component_lead_ids"]
            for id_key, (records_key, expected_role) in lead_groups.items():
                lead_ids = option[id_key] if id_key == "candidate_product_lead_ids" else component_ids[id_key]
                records = lead_records[records_key]
                if sorted(lead_ids) != sorted(lead["id"] for lead in records):
                    errors.append(f"row {index}: lead ID/record coverage mismatch for {id_key}")
                for lead in records:
                    if lead.get("role") != expected_role:
                        errors.append(f"row {index}: wrong role for lead {lead.get('id')}")
                    errors.extend(check_lead_record(ROOT, lead, "record_pointer"))
            for key in ("delivered_shank_bounds", "delivered_full_thread_interval", "matched_nut_active_thread_interval"):
                if option.get(key) is not None:
                    errors.append(f"row {index}: unsupported delivered dimension asserted for {key}")
        elif row["inventory_class"] == "retained_frame_bolt_axis":
            if row["catalog_option"].get("selected_for_wood_joints") is not False:
                errors.append(f"row {index}: retained reference treated as selected")

    counts = Counter(row["inventory_class"] for row in packet["rows"])
    declared = packet["counts"]
    if len(packet["rows"]) != 170 or declared["total_crosswalk_rows"] != 170:
        errors.append("total row count is not 170")
    for category, expected in expected_counts.items():
        if counts[category] != expected:
            errors.append(f"declared row count mismatch: {category}")
    if declared["candidate_selected_products"] != 0:
        errors.append("crosswalk declares candidate products selected")
    if declared["candidate_fit_qualified_stacks"] != 0:
        errors.append("crosswalk declares candidate stacks fit-qualified")
    if declared["retained_fit_qualified_stacks"] != 0:
        errors.append("crosswalk declares retained stacks fit-qualified")
    if declared["physical_access_or_transport_clearances"] != 0:
        errors.append("crosswalk declares a physical clearance")

    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors[:20]))
    print(
        "PASS independent source/identity review: 74 pinned source rows, "
        "340 T07/T08 record pointers, 92 candidate + 12 retained + 66 Hillman "
        "axes; all 170 physical operation statuses unresolved; no candidate "
        "product selected and no fit/access/transport clearance asserted."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
