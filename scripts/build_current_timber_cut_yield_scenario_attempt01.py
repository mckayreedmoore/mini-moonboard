#!/usr/bin/env python3
"""Build and verify arithmetic cut-length scenarios for the current 24 blocks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKET_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    "/current-timber-cut-yield-scenario-attempt01"
)
REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_SELECTED_AUTHORITY = "compact-floor-flush-development"
REPORT_NAME = "current-timber-cut-yield-scenarios.json"
VERIFICATION_NAME = "verification.json"
SOURCE_ROLES = {
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/current-timber-source-yield.json": "block_schedule",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json": "manifest",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-grade-disposition-attempt01/grade-disposition.json": "grade",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt02/material-stock-and-panel-status.json": "cost_status",
    "docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/revision.json": "revision",
    "current-candidate.json": "selected_authority",
}
RIPPED_4X6_IDS = {
    "center_principal_cleat_left",
    "center_principal_cleat_right",
    "knee_outer_left_inner_frame_block",
    "knee_outer_right_inner_frame_block",
}
FEET_TO_MM = 304.8


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def read_pinned_sources(root: Path = ROOT) -> tuple[dict[str, Any], list[dict[str, str]]]:
    packet = root / PACKET_REL
    pins = _read_json(packet / "source-pins.json")
    entries = pins.get("sources")
    if pins.get("schema") != "wood_joint_timber_cut_yield_source_pins/v1" or not isinstance(entries, list):
        raise ValueError("source-pins.json has an unsupported schema")
    by_path: dict[str, dict[str, str]] = {}
    for row in entries:
        path, expected = row.get("path"), row.get("sha256")
        if not isinstance(path, str) or not isinstance(expected, str) or path in by_path:
            raise ValueError("source pins must have unique paths and SHA-256 values")
        by_path[path] = row
    if set(by_path) != set(SOURCE_ROLES):
        raise ValueError("source-pins.json paths differ from the bounded input contract")

    sources: dict[str, Any] = {}
    checked: list[dict[str, str]] = []
    for rel_path, role in SOURCE_ROLES.items():
        content = (root / rel_path).read_bytes()
        actual = hashlib.sha256(content).hexdigest()
        expected = by_path[rel_path]["sha256"]
        if actual != expected:
            raise ValueError(
                f"source hash drift for {rel_path}: expected {expected}, got {actual}"
            )
        try:
            sources[role] = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"pinned source is not valid JSON: {rel_path}") from exc
        checked.append({"path": rel_path, "sha256": actual})
    return sources, checked


def _validate_and_read_blanks(
    sources: dict[str, Any], verified_pins: list[dict[str, str]]
) -> tuple[list[dict[str, Any]], list[str]]:
    schedule = sources["block_schedule"]
    manifest = sources["manifest"]
    grade = sources["grade"]
    cost_status = sources["cost_status"]
    authority = sources["selected_authority"]

    if schedule.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError("source-yield schedule names the wrong development candidate")
    if manifest.get("candidate") != EXPECTED_CANDIDATE or manifest.get("geometry_revision_id") != REVISION_ID:
        raise ValueError("attempt04 manifest is not the reviewed candidate revision")
    if grade.get("candidate") != EXPECTED_CANDIDATE or grade.get("geometry_revision_id") != REVISION_ID:
        raise ValueError("grade disposition is not bound to the reviewed candidate revision")
    if cost_status.get("candidate") != EXPECTED_CANDIDATE or cost_status.get("geometry_revision_id") != REVISION_ID:
        raise ValueError("T08 material status is not bound to the reviewed candidate revision")
    # Attempt04 extends the older manifest. Bind this packet through exact IDs;
    # do not transfer the older manifest hash as current geometry evidence.
    if (
        schedule.get("attempt02_manifest_sha256") != manifest.get("manifest_sha256")
        and schedule.get("revision_reconciliation", {}).get("candidate_block_ids_match_manifest_exactly") is not True
    ):
        raise ValueError("source-yield schedule has no exact manifest identity reconciliation")
    if authority.get("candidate") != EXPECTED_SELECTED_AUTHORITY:
        raise ValueError("selected-baseline authority unexpectedly changed")
    if manifest.get("selected_candidate_authority_preserved") != EXPECTED_SELECTED_AUTHORITY:
        raise ValueError("current manifest does not preserve selected-candidate authority")
    schedule_path = next(path for path, role in SOURCE_ROLES.items() if role == "block_schedule")
    expected_schedule_hash = next(row["sha256"] for row in verified_pins if row["path"] == schedule_path)
    if cost_status.get("source_yield_register", {}).get("sha256") != expected_schedule_hash:
        raise ValueError("T08 source-yield register reference differs from the pinned source")

    records = schedule.get("candidate_block_records")
    block_rows = manifest.get("candidate_blocks")
    if not isinstance(records, list) or not isinstance(block_rows, list):
        raise TypeError("source schedule or current manifest lacks candidate block records")
    schedule_ids = [row.get("part_id") for row in records]
    manifest_ids = [row.get("part_id") for row in block_rows]
    if len(schedule_ids) != 24 or len(set(schedule_ids)) != 24 or set(schedule_ids) != set(manifest_ids):
        raise ValueError("proposed blank IDs do not match the current 24 manifest block IDs")

    grade_ids = {
        part_id
        for rip in grade.get("proposed_ripped_blocks", [])
        for part_id in rip.get("part_ids", [])
    }
    source_rip_ids = set(schedule.get("ripped_4x6_blocks", {}).get("part_ids", []))
    if grade_ids != RIPPED_4X6_IDS or source_rip_ids != RIPPED_4X6_IDS:
        raise ValueError("the four proposed 4x6 rip IDs differ across current source records")
    if grade.get("grade_disposition", {}).get("grade_claimed") is not False:
        raise ValueError("ripped 4x6 source disposition no longer blocks grade transfer")
    if grade.get("grade_disposition", {}).get("assigned_grade") is not None:
        raise ValueError("ripped 4x6 source has an assigned grade; this scenario requires review")

    class_counts: dict[str, int] = defaultdict(int)
    blanks: list[dict[str, Any]] = []
    for row in records:
        part_id = row.get("part_id")
        stock_class = row.get("proposed_stock_class")
        section = row.get("proposed_blank_cross_section_mm")
        length = row.get("proposed_blank_stock_length_mm")
        pattern_group = row.get("pattern_group")
        if (
            not isinstance(part_id, str)
            or stock_class not in {"4x4", "4x6", "2x6"}
            or not isinstance(section, list)
            or len(section) != 2
            or not all(isinstance(value, (int, float)) and value > 0 for value in section)
            or not isinstance(length, (int, float))
            or length <= 0
            or not isinstance(pattern_group, str)
            or not pattern_group
        ):
            raise ValueError(f"invalid proposed blank record: {part_id!r}")
        ripped = part_id in RIPPED_4X6_IDS
        if ripped and stock_class != "4x6":
            raise ValueError(f"ripped block {part_id} is not on the proposed 4x6 source class")
        if not ripped and stock_class == "4x6":
            raise ValueError(f"unrecognized 4x6 blank {part_id}; update the reviewed rip contract first")
        class_counts[stock_class] += 1
        blanks.append(
            {
                "part_id": part_id,
                "stock_class": stock_class,
                "proposed_blank_cross_section_mm": [float(section[0]), float(section[1])],
                "proposed_blank_length_mm": float(length),
                "pattern_group": pattern_group,
                "post_rip_grade_status": (
                    "unresolved_after_cross_section_remanufacture" if ripped else "not_a_ripped_4x6_blank"
                ),
                "grade_assigned": False,
            }
        )
    if dict(class_counts) != {"4x4": 18, "4x6": 4, "2x6": 2}:
        raise ValueError(f"unexpected proposed blank count by stock class: {dict(class_counts)}")
    if sum(1 for row in blanks if row["part_id"] in RIPPED_4X6_IDS) != 4:
        raise ValueError("not all four proposed 4x6 rips were preserved")
    return sorted(blanks, key=lambda row: row["part_id"]), sorted(grade_ids)


def _supplier_observations(schedule: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = schedule.get("suppliers_checked")
    if not isinstance(rows, list):
        raise TypeError("source-yield supplier observations are missing")
    by_id = {row.get("source_id"): row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("supplier source IDs are not unique")
    return by_id


def _stock_options(scenario_inputs: dict[str, Any], schedule: dict[str, Any]) -> list[dict[str, Any]]:
    if scenario_inputs.get("geometry_revision_id") != REVISION_ID:
        raise ValueError("scenario inputs are bound to a different geometry revision")
    suppliers = _supplier_observations(schedule)
    options: list[dict[str, Any]] = []
    for row in scenario_inputs.get("stock_length_options", []):
        stock_class = row.get("stock_class")
        source_id = row.get("source_supplier_id")
        source = suppliers.get(source_id)
        if source is None or row.get("product_selection") is not False:
            raise ValueError("stock-length scenarios must cite a source lead and remain unselected")
        observations = source.get("observations", {})
        if stock_class == "4x4":
            if source_id != "front_range_lumber_metro_denver" or row.get("published_lengths_ft") != observations.get("4x4_douglas_fir_published_lengths_ft"):
                raise ValueError("4x4 length scenarios differ from the pinned published length observation")
            descriptor = "published Douglas-fir 4x4 length guidance; live stock not guaranteed"
            length_options = row["published_lengths_ft"]
        elif stock_class == "4x6":
            if source_id != "front_range_lumber_metro_denver" or row.get("published_lengths_ft") != observations.get("4x6_douglas_fir_published_lengths_ft"):
                raise ValueError("4x6 length scenarios differ from the pinned published length observation")
            descriptor = "published Douglas-fir 4x6 length guidance; live stock not guaranteed"
            length_options = row["published_lengths_ft"]
        elif stock_class == "2x6":
            if source_id != "lowes_2x6_lead":
                raise ValueError("2x6 lengths must preserve their distinct Lowe's listing leads")
            products = observations.get("listed_products", [])
            product = row.get("listed_product_text")
            if product not in products:
                raise ValueError("2x6 scenario product descriptor differs from pinned source")
            match = re.match(r"^2x6x(\d+)\b", product)
            if match is None or row.get("published_lengths_ft") != [int(match.group(1))]:
                raise ValueError("2x6 scenario length does not match its own listing descriptor")
            descriptor = product
            length_options = row["published_lengths_ft"]
        else:
            raise ValueError(f"unrecognized stock class scenario: {stock_class!r}")
        if not isinstance(length_options, list) or not length_options:
            raise ValueError(f"no published arithmetic length scenarios for {stock_class}")
        for length_ft in length_options:
            if not isinstance(length_ft, (int, float)) or length_ft <= 0:
                raise ValueError("stock lengths must be positive numeric feet")
            options.append(
                {
                    "stock_class": stock_class,
                    "published_length_ft": float(length_ft),
                    "stock_length_mm": round(float(length_ft) * FEET_TO_MM, 6),
                    "source_supplier_id": source_id,
                    "source_descriptor": descriptor,
                    "product_selected": False,
                    "on_hand_stock_established": False,
                }
            )
    if {row["stock_class"] for row in options} != {"4x4", "4x6", "2x6"}:
        raise ValueError("published scenario lengths do not cover each proposed stock class")
    if not any(row["stock_class"] == "2x6" and row["published_length_ft"] == 8 for row in options):
        raise ValueError("the distinct 2x6 kiln-dried 8 ft listing scenario is missing")
    if not any(row["stock_class"] == "2x6" and row["published_length_ft"] == 16 for row in options):
        raise ValueError("the distinct 2x6 green 16 ft listing scenario is missing")
    return options


def pack_arithmetic_group(
    blanks: list[dict[str, Any]],
    stock_length_mm: float,
    kerf_mm: float,
    end_trim_mm: float,
) -> dict[str, Any]:
    """First-fit-decreasing length arithmetic; no stock or cut operation is implied."""
    if not blanks or stock_length_mm <= 0 or kerf_mm < 0 or end_trim_mm < 0:
        raise ValueError("packing requires blanks, positive stock length, and nonnegative allowances")
    capacity = stock_length_mm - end_trim_mm
    if capacity <= 0:
        raise ValueError("end trim consumes the full hypothetical stock length")
    rows = sorted(blanks, key=lambda row: (-row["proposed_blank_length_mm"], row["part_id"]))
    bins: list[dict[str, Any]] = []
    too_long: list[str] = []
    for blank in rows:
        used = blank["proposed_blank_length_mm"] + kerf_mm
        if used > capacity + 1e-9:
            too_long.append(blank["part_id"])
            continue
        for arithmetic_bin in bins:
            if arithmetic_bin["used_cut_length_mm"] + used <= capacity + 1e-9:
                arithmetic_bin["parts"].append(blank)
                arithmetic_bin["used_cut_length_mm"] += used
                break
        else:
            bins.append({"parts": [blank], "used_cut_length_mm": used})
    rendered_bins = []
    for index, arithmetic_bin in enumerate(bins, start=1):
        rendered_bins.append(
            {
                "arithmetic_bin": index,
                "part_ids": [row["part_id"] for row in arithmetic_bin["parts"]],
                "pattern_groups": sorted({row["pattern_group"] for row in arithmetic_bin["parts"]}),
                "used_cut_length_mm": round(arithmetic_bin["used_cut_length_mm"], 6),
                "end_trim_mm": round(end_trim_mm, 6),
                "remaining_length_mm": round(capacity - arithmetic_bin["used_cut_length_mm"], 6),
                "blank_sections_mm": [
                    list(section)
                    for section in sorted(
                        {tuple(row["proposed_blank_cross_section_mm"]) for row in arithmetic_bin["parts"]}
                    )
                ],
                "stock_classes": sorted({row["stock_class"] for row in arithmetic_bin["parts"]}),
            }
        )
    return {
        "status": "arithmetic_fit_in_hypothetical_length" if not too_long else "arithmetic_infeasible_for_length",
        "arithmetic_bin_count": len(rendered_bins),
        "bins": rendered_bins,
        "unfitted_part_ids": too_long,
        "not_a_purchase_quantity": True,
    }


def build_report(root: Path = ROOT) -> dict[str, Any]:
    sources, verified_pins = read_pinned_sources(root)
    packet = root / PACKET_REL
    scenario_path = packet / "scenario-inputs.json"
    scenario_inputs = _read_json(scenario_path)
    blanks, ripped_ids = _validate_and_read_blanks(sources, verified_pins)
    stock_options = _stock_options(scenario_inputs, sources["block_schedule"])
    cut_losses = scenario_inputs.get("cut_loss_scenarios", [])
    if not cut_losses or len({row.get("scenario_id") for row in cut_losses}) != len(cut_losses):
        raise ValueError("cut-loss scenarios must be nonempty and uniquely named")
    for row in cut_losses:
        if not isinstance(row.get("kerf_mm"), (int, float)) or row["kerf_mm"] < 0:
            raise ValueError("kerf inputs must be nonnegative millimetres")
        if not isinstance(row.get("end_trim_per_arithmetic_bin_mm"), (int, float)) or row["end_trim_per_arithmetic_bin_mm"] < 0:
            raise ValueError("end-trim inputs must be nonnegative millimetres")

    cohorts: dict[tuple[str, tuple[float, float]], list[dict[str, Any]]] = defaultdict(list)
    for blank in blanks:
        cohorts[(blank["stock_class"], tuple(blank["proposed_blank_cross_section_mm"]))].append(blank)
    results = []
    for stock_option in stock_options:
        class_cohorts = [key for key in sorted(cohorts) if key[0] == stock_option["stock_class"]]
        for stock_class, section in class_cohorts:
            group_blanks = cohorts[(stock_class, section)]
            for cut_loss in cut_losses:
                packing = pack_arithmetic_group(
                    group_blanks,
                    stock_option["stock_length_mm"],
                    float(cut_loss["kerf_mm"]),
                    float(cut_loss["end_trim_per_arithmetic_bin_mm"]),
                )
                results.append(
                    {
                        "scenario_id": f"{stock_class}-{stock_option['published_length_ft']:g}ft-{section[0]:g}x{section[1]:g}mm-{cut_loss['scenario_id']}",
                        "stock_class": stock_class,
                        "proposed_blank_cross_section_mm": [section[0], section[1]],
                        "published_stock_length_ft": stock_option["published_length_ft"],
                        "stock_length_mm": stock_option["stock_length_mm"],
                        "stock_source_supplier_id": stock_option["source_supplier_id"],
                        "stock_source_descriptor": stock_option["source_descriptor"],
                        "product_selected": False,
                        "on_hand_stock_established": False,
                        "kerf_mm": float(cut_loss["kerf_mm"]),
                        "kerf_convention": scenario_inputs["accounting_convention"]["kerf_charge"],
                        "end_trim_per_arithmetic_bin_mm": float(cut_loss["end_trim_per_arithmetic_bin_mm"]),
                        "blank_count": len(group_blanks),
                        "proposed_blank_length_total_mm": round(sum(row["proposed_blank_length_mm"] for row in group_blanks), 6),
                        "proposed_blanks": group_blanks,
                        "packing": packing,
                    }
                )
    results.sort(key=lambda row: row["scenario_id"])
    unique_ids = [row["part_id"] for row in blanks]
    return {
        "schema": "wood_joint_current_timber_cut_yield_scenarios/v1",
        "candidate": EXPECTED_CANDIDATE,
        "selected_candidate_authority_preserved": EXPECTED_SELECTED_AUTHORITY,
        "geometry_revision_id": REVISION_ID,
        "input_scope": "24 proposed candidate block blanks only; source-frame member purchase lengths are excluded",
        "source_pins": verified_pins,
        "scenario_inputs_sha256": hashlib.sha256(scenario_path.read_bytes()).hexdigest(),
        "inventory_reconciliation": {
            "count": len(blanks),
            "part_ids": unique_ids,
            "by_stock_class": {
                stock_class: sum(row["stock_class"] == stock_class for row in blanks)
                for stock_class in ("4x4", "4x6", "2x6")
            },
            "ripped_4x6_part_ids": ripped_ids,
            "exact_ids_match_attempt04_manifest": True,
        },
        "packing_policy": {
            "algorithm": "stable first-fit-decreasing length arithmetic",
            "partition_key": "stock_class plus exact proposed_blank_cross_section_mm",
            "cross_section_mixing": False,
            "shared_unsawn_4x6_stock_before_ripping": False,
            "pattern_group_preserved_per_blank": True,
            "optimization_claim": False,
        },
        "scenario_result_count": len(results),
        "scenarios": results,
        "claim_boundary": {
            "arithmetic_scenarios_only": True,
            "purchase_quantity_established": False,
            "product_selected": False,
            "price_or_cost_established": False,
            "material_identity_or_grade_accepted": False,
            "post_rip_grade_resolved": False,
            "physical_fit_established": False,
            "physical_cutting_authorized": False,
            "candidate_or_climbing_release": False,
        },
    }


def verify_packet(root: Path = ROOT) -> dict[str, Any]:
    packet = root / PACKET_REL
    report_path = packet / REPORT_NAME
    verification_path = packet / VERIFICATION_NAME
    expected = build_report(root)
    actual = _read_json(report_path)
    if actual != expected:
        raise ValueError(f"{REPORT_NAME} differs from the source-pinned scenario build")
    actual_bytes = report_path.read_bytes()
    actual_digest = hashlib.sha256(actual_bytes).hexdigest()
    verification = _read_json(verification_path)
    if verification.get("report_sha256") != actual_digest:
        raise ValueError("verification report hash does not match the scenario report")
    if verification.get("source_pins_status") != "PASS" or verification.get("source_count") != len(SOURCE_ROLES):
        raise ValueError("verification record does not show all pinned sources passing")
    if verification.get("scenario_count") != expected["scenario_result_count"]:
        raise ValueError("verification scenario count differs from the generated report")
    return verification


def write_packet(root: Path = ROOT) -> dict[str, Any]:
    packet = root / PACKET_REL
    report = build_report(root)
    report_bytes = _json_bytes(report)
    (packet / REPORT_NAME).write_bytes(report_bytes)
    verification = {
        "schema": "wood_joint_current_timber_cut_yield_verification/v1",
        "source_pins_status": "PASS",
        "source_count": len(report["source_pins"]),
        "source_pins": report["source_pins"],
        "scenario_inputs_sha256": report["scenario_inputs_sha256"],
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "scenario_count": report["scenario_result_count"],
        "blank_count": report["inventory_reconciliation"]["count"],
        "physical_or_purchase_claims": False,
    }
    (packet / VERIFICATION_NAME).write_bytes(_json_bytes(verification))
    return verification


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", action="store_true", help="write derived scenario report and verification")
    action.add_argument("--check", action="store_true", help="verify source pins and stored derived report")
    args = parser.parse_args()
    try:
        if args.write:
            result = write_packet()
            print(f"WROTE: {result['scenario_count']} arithmetic scenarios; {result['blank_count']} source-bound blanks")
        else:
            result = verify_packet()
            print(f"PASS: {result['source_count']} source pins; {result['scenario_count']} arithmetic scenarios; {result['blank_count']} blanks")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
