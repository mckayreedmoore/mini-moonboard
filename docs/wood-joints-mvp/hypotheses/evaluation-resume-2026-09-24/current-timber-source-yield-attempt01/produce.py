#!/usr/bin/env python3
"""Build a source-bound timber schedule for the reviewed wood-joint candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
OUT_DIR = Path(__file__).resolve().parent
INVENTORY_PATH = ROOT / "docs/wood-joints-mvp/source-inventory.json"
MANIFEST_PATH = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    / "current-full-frame-input-manifest-attempt02"
    / "current-full-frame-input-manifest.json"
)
STOCK_REVIEW_PATH = ROOT / "docs/wood-joints-mvp/corner-block-stock-review-2026-09-24.md"
MATERIAL_SCENARIOS_PATH = ROOT / "docs/wood-joints-mvp/current-material-scenarios.md"
OUTPUT_PATH = OUT_DIR / "current-timber-source-yield.json"
REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_MANIFEST_DIGEST = "1ad6b404c8658147e9d10f54daf4ebd393116c1934654f5521421dc96667e0a0"
LOOKUP_DATE = "2026-09-27"


BLOCK_GROUPS: list[dict[str, Any]] = [
    {
        "group_id": "main_common_4x4",
        "stock_class": "4x4",
        "quantity": 15,
        "cross_section_mm": [88.9, 88.9],
        "stock_length_mm": 119.7,
        "length_axis": "source_N",
        "part_ids": [
            "bottom_center_left_cleat",
            "bottom_center_right_cleat",
            "bottom_outer_left_cleat",
            "bottom_outer_right_cleat",
            "left_service_inner_lower_cleat",
            "left_service_inner_upper_cleat",
            "left_service_outer_lower_cleat",
            "left_service_outer_upper_cleat",
            "top_center_left_cleat",
            "top_center_right_cleat",
            "top_outer_left_cleat",
            "top_outer_right_cleat",
            "wj04_lower_full_stock_cleat",
            "wj06_outer_lower_right_cleat",
            "wj06_outer_upper_right_cleat",
        ],
        "basis": "Current seven-pattern stock review; proposed blank, not released cut list.",
    },
    {
        "group_id": "upper_g7_short_4x4",
        "stock_class": "4x4",
        "quantity": 1,
        "cross_section_mm": [88.9, 88.9],
        "stock_length_mm": 86.9,
        "length_axis": "source_N",
        "part_ids": ["wj04_upper_g7_crosscut_full_stock_cleat"],
        "basis": "Current seven-pattern stock review; proposed blank, not released cut list.",
    },
    {
        "group_id": "center_post_4x4",
        "stock_class": "4x4",
        "quantity": 2,
        "cross_section_mm": [88.9, 88.9],
        "stock_length_mm": 128.9,
        "length_axis": "global_Z",
        "part_ids": ["center_post_cleat_left", "center_post_cleat_right"],
        "basis": "Current seven-pattern stock review; proposed blank, not released cut list.",
    },
    {
        "group_id": "central_principal_header_4x6_ripped",
        "stock_class": "4x6",
        "quantity": 2,
        "cross_section_mm": [83.9, 139.7],
        "stock_length_mm": 134.7,
        "length_axis": "global_Z",
        "part_ids": ["center_principal_cleat_left", "center_principal_cleat_right"],
        "basis": "Current seven-pattern stock review; 5 mm section rip proposed.",
    },
    {
        "group_id": "outer_inner_frame_4x6_ripped",
        "stock_class": "4x6",
        "quantity": 2,
        "cross_section_mm": [88.9, 133.35],
        "stock_length_mm": 139.0,
        "length_axis": "global_Z",
        "part_ids": [
            "knee_outer_left_inner_frame_block",
            "knee_outer_right_inner_frame_block",
        ],
        "basis": "Current seven-pattern stock review; 6.35 mm section rip proposed.",
    },
    {
        "group_id": "exterior_spine_2x6",
        "stock_class": "2x6",
        "quantity": 2,
        "cross_section_mm": [38.1, 139.7],
        "stock_length_mm": 276.3,
        "length_axis": "global_Z",
        "part_ids": ["knee_outer_left_spine", "knee_outer_right_spine"],
        "basis": "Current seven-pattern stock review; proposed 2x6 blank with reliefs.",
    },
]


SUPPLIER_SOURCES = [
    {
        "source_id": "front_range_lumber_metro_denver",
        "vendor": "Front Range Lumber Company",
        "source_type": "local supplier product and location pages",
        "urls": [
            "https://www.frlco.com/product-info/timbers/",
            "https://www.frlco.com/product-info/framing-lumber/",
            "https://www.frlco.com/locations/lakewood-colorado/",
            "https://www.frlco.com/fast-delivery/",
        ],
        "observations": {
            "market": "Lakewood / Metro Denver, Colorado",
            "4x4_douglas_fir_published_lengths_ft": [8, 10, 12, 16, 20],
            "4x6_douglas_fir_published_lengths_ft": [8, 10, 12, 16],
            "2x6_framing_lumber_class_listed": True,
            "stock_is_guaranteed": False,
            "price_usd": None,
            "live_on_hand_count": None,
            "species_group": None,
            "grade_for_this_candidate": None,
            "treatment": None,
            "moisture_content": None,
            "receiving_condition": None,
            "inspector_or_regrade_basis": None,
            "delivery": {
                "published_fee_usd": 99,
                "published_minimum_order_usd": 500,
                "coverage": "Extended Metro Denver and Northern Colorado",
                "candidate_order_applicability": "unresolved",
            },
        },
        "lookup_note": (
            "Published product-size guidance is not a live stock check. The supplier "
            "says exact stock varies by location and directs customers to call. No "
            "candidate-specific quote or receiving/grade inspection was available."
        ),
    },
    {
        "source_id": "home_depot_4x4_lead",
        "vendor": "The Home Depot",
        "source_type": "product page; store-specific price and stock not returned",
        "urls": ["https://www.homedepot.com/p/300874740"],
        "observations": {
            "listed_product": "4x4x8 Douglas Fir, No. 2",
            "listed_actual_section_in": [3.5, 3.5],
            "listed_actual_length_ft": 8,
            "price_usd": None,
            "denver_store_availability": None,
            "species_group": None,
            "treatment": "product representative answered untreated; verify item/lot",
            "candidate_selection": False,
        },
        "lookup_note": (
            "Page states product may vary by store and does not return a Denver quote "
            "or live quantity. A dimensional/grade lead only."
        ),
    },
    {
        "source_id": "lowes_4x4_lead",
        "vendor": "Lowe's",
        "source_type": "product page; pricing and availability require location",
        "urls": [
            "https://www.lowes.com/pd/4-in-x-4-in-x-8-ft-Douglas-Fir-Lumber-"
            "Common-3-562-in-x-3-562-in-x-8-ft-Actual/1000028905"
        ],
        "observations": {
            "listed_product": "4x4x8 #2 Better Douglas Fir, green",
            "listed_actual_section_in": [3.562, 3.562],
            "price_usd": None,
            "denver_store_availability": None,
            "anti_stain_treatment_listed": True,
            "candidate_selection": False,
        },
        "lookup_note": (
            "The product page prompts for ZIP/city for price and availability. "
            "Its section is larger than the 88.9 mm proposed block blank and it "
            "lists anti-stain treatment."
        ),
    },
    {
        "source_id": "lowes_4x6_lead",
        "vendor": "Lowe's",
        "source_type": "product page; pricing and availability require location",
        "urls": [
            "https://www.lowes.com/pd/4-in-x-6-in-x-8-ft-Douglas-Fir-Lumber-"
            "Common-3-562-in-x-5-625-in-x-8-ft-Actual/1000028917"
        ],
        "observations": {
            "listed_product": "4x6x8 #2 Better Douglas Fir, green",
            "listed_actual_section_in": [3.562, 5.625],
            "anti_stain_treatment_listed": True,
            "price_usd": None,
            "denver_store_availability": None,
            "candidate_selection": False,
        },
        "lookup_note": (
            "Actual dimensions exceed the proposed 88.9 x 139.7 mm source section; "
            "surfacing/ripping and grade effects are not established. The page "
            "prompts for a location before showing price or availability."
        ),
    },
    {
        "source_id": "lowes_2x6_lead",
        "vendor": "Lowe's",
        "source_type": "product page; pricing and availability require location",
        "urls": [
            "https://www.lowes.com/pd/Top-Choice-2-in-x-6-in-x-8-ft-Douglas-Fir-"
            "Lumber-Common-1-5-in-x-5-5-in-x-8-ft-Actual/1000571215",
            "https://www.lowes.com/pd/2-in-x-6-in-x-16-ft-Douglas-Fir-S4S-Green-Lumber/1000028937",
        ],
        "observations": {
            "listed_products": [
                "2x6x8 #2 Prime Douglas Fir, kiln-dried; actual 1.5 x 5.5 in",
                "2x6x16 #2 Better Douglas Fir, green; actual 1.562 x 5.625 in",
            ],
            "anti_stain_treatment_listed_on_8ft_product": True,
            "price_usd": None,
            "denver_store_availability": None,
            "candidate_selection": False,
        },
        "lookup_note": (
            "An exact nominal actual-section 8-ft product lead exists, but its page "
            "lists anti-stain treatment and location-gated pricing. The longer green "
            "product is oversize relative to the 38.1 x 139.7 mm source section."
        ),
    },
]


GRADE_SOURCES = [
    {
        "source_id": "alsc_lumber_enforcement_regulations_2023",
        "url": "https://alsc.org/uploaded/2023%20Lumber%20Program_Enforcement%20Regs.pdf",
        "relevant_rule": "Sections 5.9 and 5.10.1",
        "application": (
            "For grade-stamped lumber resawn/remanufactured in a way that may alter "
            "grade, the original grade mark must be removed/obliterated except for "
            "listed exceptions. The short-length exception requires cross-section "
            "to remain otherwise unmodified."
        ),
    },
    {
        "source_id": "wwpa_dimensional_lumber",
        "url": "https://www.wwpa.org/western-lumber/structural-lumber/dimensional-lumber/",
        "relevant_rule": "Dimensional lumber grade classes and grading description",
        "application": (
            "Supports that a specific grade/species designation must be tied to "
            "grade-rule identity; it does not certify any proposed or delivered piece."
        ),
    },
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    return sha256(path.read_bytes())


def round_mm(value: float) -> float:
    return round(float(value), 3)


def stock_class(section: list[float]) -> str:
    dims = sorted(round(float(value), 1) for value in section)
    if dims == [88.9, 139.7]:
        return "4x6"
    if dims == [38.1, 139.7]:
        return "2x6"
    raise ValueError(f"Unrecognized source inventory section: {section}")


def source_record(path: Path, role: str) -> dict[str, str]:
    return {"path": path.relative_to(ROOT).as_posix(), "role": role, "sha256": file_digest(path)}


def build_payload() -> dict[str, Any]:
    inventory_bytes = INVENTORY_PATH.read_bytes()
    manifest_bytes = MANIFEST_PATH.read_bytes()
    inventory = json.loads(inventory_bytes)
    manifest = json.loads(manifest_bytes)

    if inventory.get("candidate") != "compact-floor-flush-wood-joints-development":
        raise ValueError("Unexpected source inventory candidate")
    if manifest.get("geometry_revision_id") != REVISION_ID:
        raise ValueError("Current full-frame manifest revision changed")
    if manifest.get("manifest_sha256") != EXPECTED_MANIFEST_DIGEST:
        raise ValueError("Attempt02 manifest identity changed")
    if manifest.get("inventory_counts", {}).get("candidate_blocks") != 24:
        raise ValueError("Current candidate block count is not 24")
    if manifest.get("inventory_counts", {}).get("candidate_bolt_axes") != 92:
        raise ValueError("Current candidate bolt-axis count is not 92")

    parts = inventory.get("parts", [])
    timber_parts = [part for part in parts if part.get("kind") == "timber"]
    if len(timber_parts) != 20:
        raise ValueError(f"Expected 20 source frame timbers; got {len(timber_parts)}")

    physical_by_id = {row["member_id"]: row for row in manifest["physical_members"]}
    frame_rows: list[dict[str, Any]] = []
    frame_totals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"member_count": 0, "source_blank_length_sum_mm": 0.0, "part_ids": []}
    )
    for part in sorted(timber_parts, key=lambda row: row["part_id"]):
        member_id = part["part_id"]
        current_member = physical_by_id.get(member_id)
        if current_member is None or current_member.get("member_kind") != "timber":
            raise ValueError(f"Source timber missing from attempt02 manifest: {member_id}")
        dims = [float(value) for value in part["source_blank_dimensions_mm"]]
        if len(dims) != 3:
            raise ValueError(f"Expected three source blank dimensions for {member_id}")
        section = [float(value) for value in part["actual_source_section_mm"]]
        cls = stock_class(section)
        length = dims[0]
        totals = frame_totals[cls]
        totals["member_count"] += 1
        totals["source_blank_length_sum_mm"] += length
        totals["part_ids"].append(member_id)
        frame_rows.append(
            {
                "part_id": member_id,
                "nominal_stock_class_inferred_from_source_section": cls,
                "actual_source_section_mm": section,
                "source_blank_dimensions_mm_recorded": dims,
                "source_blank_length_axis_mm_recorded_as_first_dimension": round_mm(length),
                "source_grain_axis_global_xyz": part.get("grain_axis_global_xyz"),
                "source_species_grade_basis": part.get("species_grade_basis"),
                "delivered_species_group": None,
                "delivered_grade": None,
                "treatment": None,
                "moisture_content": None,
                "receiving_condition": None,
                "inspector_or_regrade_basis": None,
                "delivery_and_price": None,
                "source_shape_sha256": part.get("source_shape_sha256"),
                "source_shape_record_sha256": part.get("source_shape_record_sha256"),
                "current_composition_roles": current_member.get("composition_roles", []),
                "current_graph_finished_geometry_summary": current_member.get(
                    "graph_finished_geometry_summary"
                ),
                "exact_current_finished_solid_available_in_manifest_sources": current_member.get(
                    "exact_current_finished_brep_or_step_available_in_manifest_sources"
                ),
                "delivered_stock_observed": bool(part.get("delivered_stock_observed")),
            }
        )

    manifest_blocks = {row["part_id"]: row for row in manifest.get("candidate_blocks", [])}
    expected_block_ids = [part_id for group in BLOCK_GROUPS for part_id in group["part_ids"]]
    if len(expected_block_ids) != 24 or len(set(expected_block_ids)) != 24:
        raise ValueError("Block-group mapping must contain 24 unique part IDs")
    if set(manifest_blocks) != set(expected_block_ids):
        raise ValueError("Block-group IDs do not exactly match attempt02 candidate blocks")

    block_rows: list[dict[str, Any]] = []
    block_totals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"block_count": 0, "proposed_blank_length_sum_mm": 0.0, "part_ids": []}
    )
    for group in BLOCK_GROUPS:
        dims = [float(value) for value in group["cross_section_mm"]]
        length = float(group["stock_length_mm"])
        for part_id in group["part_ids"]:
            row = manifest_blocks[part_id]
            summary = row["finished_geometry_summary"]["finished"]
            bounds_min = [float(value) for value in summary["min_xyz_mm"]]
            bounds_max = [float(value) for value in summary["max_xyz_mm"]]
            bbox_dims = [round_mm(bounds_max[i] - bounds_min[i]) for i in range(3)]
            totals = block_totals[group["stock_class"]]
            totals["block_count"] += 1
            totals["proposed_blank_length_sum_mm"] += length
            totals["part_ids"].append(part_id)
            block_rows.append(
                {
                    "part_id": part_id,
                    "pattern_group": group["group_id"],
                    "proposed_stock_class": group["stock_class"],
                    "proposed_blank_cross_section_mm": dims,
                    "proposed_blank_stock_length_mm": round_mm(length),
                    "proposed_stock_length_axis": group["length_axis"],
                    "blank_basis": group["basis"],
                    "finished_geometry_bounds_dimensions_xyz_mm": bbox_dims,
                    "finished_geometry_volume_mm3": round_mm(summary["volume_mm3"]),
                    "finished_geometry_bounds_are_not_stock_blank_dimensions": True,
                    "proposed_delivered_species_group": None,
                    "proposed_delivered_grade": None,
                    "treatment": None,
                    "moisture_content": None,
                    "receiving_condition": None,
                    "inspector_or_regrade_basis": None,
                    "unit_price_usd": None,
                    "cut_yield": None,
                    "owner_report_finished_shape_sha256": row.get(
                        "owner_report_finished_shape_sha256"
                    ),
                    "exact_current_export_status": row.get("exact_export_status"),
                    "material_frame_status": row.get("material_frame_status"),
                    "release": bool(row.get("release")),
                }
            )

    if len(block_rows) != 24 or sum(row["quantity"] for row in BLOCK_GROUPS) != 24:
        raise ValueError("Expected exactly 24 current candidate block records")

    yield_rows: list[dict[str, Any]] = []
    for cls in ("4x4", "4x6", "2x6"):
        frame = frame_totals.get(cls, {"member_count": 0, "source_blank_length_sum_mm": 0.0})
        blocks = block_totals.get(cls, {"block_count": 0, "proposed_blank_length_sum_mm": 0.0})
        frame_length = frame["source_blank_length_sum_mm"]
        block_length = blocks["proposed_blank_length_sum_mm"]
        yield_rows.append(
            {
                "stock_class": cls,
                "frame_source_member_count": frame["member_count"],
                "frame_recorded_source_blank_length_sum_mm": round_mm(frame_length),
                "candidate_block_count": blocks["block_count"],
                "candidate_block_proposed_blank_length_sum_mm": round_mm(block_length),
                "combined_arithmetic_length_sum_mm": round_mm(frame_length + block_length),
                "linear_length_is_not_a_stock_order_or_cut_yield": True,
            }
        )

    unresolved = [
        "No product/SKU is selected for any frame member or candidate block.",
        (
            "Delivered species group, grade, treatment, moisture, and receiving "
            "condition are unverified."
        ),
        (
            "Cut optimization, kerf, end trim, defect screening, section cleanup, "
            "and usable yield are not established."
        ),
        (
            "The source inventory gives starting blank dimensions; 16 current frame "
            "hosts are rebuilt in the reviewed geometry, so current stock-removal "
            "and cut effects are not captured by those dimensions."
        ),
        (
            "The four 4x6-derived blocks require cross-section ripping; the current "
            "grade mark and regrading/inspection path are unresolved."
        ),
        (
            "No current lumber quote, Denver store stock count, inspector appointment, "
            "or candidate delivery arrangement is confirmed."
        ),
    ]

    return {
        "schema": "wood_joint_current_timber_source_yield/v1",
        "attempt_id": "current-timber-source-yield-attempt01",
        "created_date": LOOKUP_DATE,
        "lookup_date": LOOKUP_DATE,
        "status": "source_bound_preliminary_screen",
        "candidate": inventory["candidate"],
        "geometry_revision_id": REVISION_ID,
        "reviewed_repository_commit": manifest.get("reviewed_repository_commit"),
        "attempt02_manifest_sha256": manifest["manifest_sha256"],
        "inventory_candidate": inventory["candidate"],
        "inventory_source_candidate": inventory.get("source_candidate"),
        "inventory_source_commit": inventory.get("source_commit"),
        "inventory_counts": {
            "source_inventory_frame_timbers": len(frame_rows),
            "attempt02_candidate_blocks": len(block_rows),
            "attempt02_candidate_bolt_axes": manifest["inventory_counts"][
                "candidate_bolt_axes"
            ],
            "attempt02_retained_frame_bolt_axes": manifest["inventory_counts"][
                "retained_starting_frame_bolt_axes"
            ],
        },
        "revision_reconciliation": {
            "basis": "Only the reviewed attempt02 24-block / 92-axis revision is used.",
            "excluded_prior_basis": (
                "Historical 28-blank / 104-axis WJ24 inventory and cost screen."
            ),
            "prior_blank_allocations_or_axis_quantities_imported": False,
            "candidate_block_ids_match_manifest_exactly": True,
        },
        "source_artifacts": [
            source_record(INVENTORY_PATH, "20 preserved source frame timber records"),
            source_record(
                MANIFEST_PATH, "reviewed 24-block, 92-axis current revision authority"
            ),
            source_record(
                STOCK_REVIEW_PATH, "proposed blank sizes and current stock-pattern grouping"
            ),
            source_record(
                MATERIAL_SCENARIOS_PATH,
                "conditional pattern grain/stock-length scenarios",
            ),
        ],
        "producer_sha256": file_digest(Path(__file__).resolve()),
        "frame_member_records": frame_rows,
        "candidate_block_blank_groups": [
            {
                key: value
                for key, value in group.items()
                if key != "basis"
            }
            | {"basis": group["basis"]}
            for group in BLOCK_GROUPS
        ],
        "candidate_block_records": sorted(block_rows, key=lambda row: row["part_id"]),
        "arithmetic_linear_length_screen": yield_rows,
        "suppliers_checked": SUPPLIER_SOURCES,
        "grade_agency_sources": GRADE_SOURCES,
        "ripped_4x6_blocks": {
            "part_ids": [
                "center_principal_cleat_left",
                "center_principal_cleat_right",
                "knee_outer_left_inner_frame_block",
                "knee_outer_right_inner_frame_block",
            ],
            "count": 4,
            "proposed_source_stock": "4x6",
            "proposed_section_rips": [
                {"quantity": 2, "from_cross_section_mm": [88.9, 139.7], "to_mm": [83.9, 139.7]},
                {"quantity": 2, "from_cross_section_mm": [88.9, 139.7], "to_mm": [88.9, 133.35]},
            ],
            "grade_status": "unresolved_after_cross_section_remanufacture",
            "rule_implication": (
                "ALSC 2023 Lumber Enforcement Regulations 5.10.1 address grade-stamped "
                "lumber remanufactured in a way that could alter grade; the under-two-foot "
                "trim exception requires the cross-section otherwise remain unmodified. "
                "These proposed section rips do not fit that exception. Do not rely on an "
                "original 4x6 grade mark for the ripped pieces without a documented, "
                "applicable grading/inspection disposition."
            ),
            "current_grade_stamp_removed_or_replaced": None,
            "accredited_agency_or_inspector_path_confirmed": False,
            "receiving_and_post_rip_checks": [
                (
                    "Record supplier, mill, species/species group, grade, seasoning, "
                    "treatment, and all visible marks before modification."
                ),
                (
                    "Confirm the remanufacturing and regrade/remark route with the "
                    "grade-mark supervising agency before cross-section ripping."
                ),
                (
                    "Retain the accepted grade/inspection record for each finished "
                    "piece and verify final section and condition at receiving."
                ),
            ],
        },
        "unknowns": unresolved,
        "release": {
            "candidate_accepted": False,
            "purchasing_authorized": False,
            "cutting_authorized": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
            "climbing_released": False,
        },
        "claim_limits": [
            (
                "This is an arithmetic quantity/sourcing screen, not a lumber order, "
                "cut list, accepted material specification, or fabrication release."
            ),
            (
                "Supplier pages establish product leads or published size ranges only; "
                "they do not establish Denver stock, price, suitability, or delivery "
                "of the exact candidate lumber."
            ),
            (
                "Frame source blank totals and proposed block blank totals must not "
                "be interpreted as net purchased stock or usable yield."
            ),
            (
                "No material property, strength, structural capacity, joint acceptance, "
                "or product fit is inferred."
            ),
        ],
    }


def encode(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the source-bound JSON schedule")
    mode.add_argument(
        "--verify",
        action="store_true",
        help="compare the JSON with live pinned inputs",
    )
    args = parser.parse_args()
    expected = encode(build_payload())
    if args.write:
        OUTPUT_PATH.write_bytes(expected)
        print(f"wrote {OUTPUT_PATH.relative_to(ROOT)} sha256={sha256(expected)}")
        return 0
    if not OUTPUT_PATH.exists():
        raise SystemExit(f"missing {OUTPUT_PATH}; run --write")
    actual = OUTPUT_PATH.read_bytes()
    if actual != expected:
        raise SystemExit("verification failed: schedule differs from live pinned inputs")
    print(f"verified {OUTPUT_PATH.relative_to(ROOT)} sha256={sha256(actual)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
