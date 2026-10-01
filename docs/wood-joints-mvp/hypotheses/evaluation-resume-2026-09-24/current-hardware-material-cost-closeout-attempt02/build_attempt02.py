#!/usr/bin/env python3
"""Build the append-only, source-pinned T08 public-cost closeout packet."""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
ATTEMPT01 = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt01"
TIMBER = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01"
GRADE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-grade-disposition-attempt01"
PLYWOOD = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-plywood-product-crosswalk-attempt05"
FRAME = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04"


def load(path: Path):
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


pins = load(HERE / "source-pins.json")
pin_check = []
for item in pins["sources"]:
    source = ROOT / item["path"]
    actual = sha(source)
    pin_check.append({"path": item["path"], "expected_sha256": item["sha256"], "actual_sha256": actual, "matches": actual == item["sha256"]})
if not all(row["matches"] for row in pin_check):
    raise SystemExit("source pin mismatch; refusing to generate closeout")

reg = load(ATTEMPT01 / "fastener-axis-register.json")
cost = load(ATTEMPT01 / "material-cost-register.json")
material = load(TIMBER / "current-timber-source-yield.json")
grade = load(GRADE / "grade-disposition.json")
ply = load(PLYWOOD / "source-observations.json")
manifest = load(FRAME / "current-full-frame-input-manifest.json")
prices = load(HERE / "public-price-observations.json")

candidate = reg["candidate_axis_rows"]
retained = reg["retained_axis_rows"]
hillman = reg["hillman_axis_rows"]
removed = reg["removed_legacy_sds25112_axis_ids"]

row_groups = defaultdict(list)
for row in candidate:
    row_groups[row["catalog_row_id"]].append(row)
lead_axes = defaultdict(list)
for row in candidate:
    for lead in row["candidate_product_lead_ids"]:
        lead_axes[lead].append(row["axis_id"])

candidate_axis_ids = sorted(row["axis_id"] for row in candidate)
retained_axis_ids = sorted(row["axis_id"] for row in retained)
hillman_axis_ids = sorted(row["axis_id"] for row in hillman)
removed_ids = sorted(removed)
moved = sorted(row["axis_id"] for row in hillman if row["owner_moved_axis"])
unchanged = sorted(row["axis_id"] for row in hillman if not row["owner_moved_axis"])

if len(candidate_axis_ids) != 92 or len(set(candidate_axis_ids)) != 92:
    raise SystemExit("candidate bolt-axis count/identity mismatch")
if len(retained_axis_ids) != 12 or len(set(retained_axis_ids)) != 12:
    raise SystemExit("retained frame-bolt count/identity mismatch")
if len(hillman_axis_ids) != 66 or len(set(hillman_axis_ids)) != 66 or (len(moved), len(unchanged)) != (8, 58):
    raise SystemExit("Hillman axis count/move reconciliation mismatch")
if len(removed_ids) != 144 or len(set(removed_ids)) != 144:
    raise SystemExit("removed SDS reference count/identity mismatch")

reconciliation = {
    "schema": "wood_joint_t08_axis_count_reconciliation/v1",
    "candidate": reg["candidate"],
    "geometry_revision_id": reg["geometry_revision_id"],
    "source_register": {
        "path": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json",
        "sha256": sha(ATTEMPT01 / "fastener-axis-register.json"),
    },
    "reconciled_counts": {
        "candidate_bolt_axes": 92,
        "candidate_nut_roles": 92,
        "candidate_separate_washer_roles": 184,
        "retained_starting_frame_bolt_axes": 12,
        "retained_nut_roles": 12,
        "retained_separate_washer_roles": 24,
        "hillman_42605_panel_kicker_screw_axes": 66,
        "hillman_axes_unchanged": 58,
        "hillman_owner_moved_axes_previously": 8,
        "removed_legacy_sds25112_reference_axes": 144,
        "candidate_plus_retained_structural_bolt_stacks": 104,
    },
    "candidate_axis_ids": candidate_axis_ids,
    "candidate_axes_by_catalog_row": {
        key: {"count": len(rows), "axis_ids": sorted(row["axis_id"] for row in rows)}
        for key, rows in sorted(row_groups.items())
    },
    "candidate_bolt_lead_axis_coverage": {
        key: {"axis_reference_count": len(axis_ids), "axis_ids": sorted(axis_ids), "means_product_is_not_selected": True}
        for key, axis_ids in sorted(lead_axes.items())
    },
    "candidate_nut_and_washer_leads": reg["shared_candidate_nut_washer_lead_ids"],
    "retained_starting_frame_bolt_axes": [
        {
            "axis_id": row["axis_id"],
            "family_id": row["family_id"],
            "catalog_reference_only": row["catalog_reference"],
            "selected_for_wood_joints": row["selected_for_wood_joints"],
            "delivered_identity_or_ownership": row["delivered_identity_or_ownership"],
        }
        for row in sorted(retained, key=lambda item: item["axis_id"])
    ],
    "hillman_42605_policy": {
        "count": len(hillman),
        "axis_ids": hillman_axis_ids,
        "unchanged_axis_ids": unchanged,
        "previously_owner_moved_axis_ids": moved,
        "purchase_policy": "one owner-purchased Hillman/Fas-n-Tite 42605 screw per current fixed axis; preserve 66 axes and existing pilot/countersink policy",
        "receipt_amount_usd": None,
        "replacement_listing_comparator_is_separate": True,
    },
    "removed_sds25112_policy": {
        "count": len(removed_ids),
        "reference_axis_ids": removed_ids,
        "status": "former 24-angle/144-SDS reference axes are removed from this bolted candidate; no new purchase, repricing, substitution, or Hillman policy transfer is inferred",
        "included_in_current_candidate_cost": False,
    },
    "claim_limits": [
        "Axis references reconcile candidate and retained quantities; alternative catalog lead coverage is not a selected item or order quantity.",
        "No part fit, delivered shank/full-thread interval, nut engagement, receipt, physical inspection, weight, or criterion pass follows from these counts.",
    ],
}
dump(HERE / "axis-count-reconciliation.json", reconciliation)

stock_groups = []
for group in material["candidate_block_blank_groups"]:
    stock_groups.append({
        "group_id": group["group_id"],
        "stock_class": group["stock_class"],
        "quantity": group["quantity"],
        "proposed_blank_length_mm": group["stock_length_mm"],
        "proposed_blank_cross_section_mm": group["cross_section_mm"],
        "part_ids": group["part_ids"],
        "basis": group["basis"],
        "status": "proposed blank pattern only; not stock purchase quantity or cut yield",
    })

price_sources = [
    {"id": "Front Range Lumber timbers", "url": "https://www.frlco.com/product-info/timbers/", "access_date_local": "2026-09-28", "outcome": "Size/length classes only; no item price displayed; local availability not guaranteed."},
    {"id": "Front Range Lumber framing", "url": "https://www.frlco.com/product-info/framing-lumber/", "access_date_local": "2026-09-28", "outcome": "Size/length classes only; no item price displayed; local availability not guaranteed."},
    {"id": "Lowe's 2x6x8 Douglas-fir listing", "url": "https://www.lowes.com/pd/Top-Choice-2-in-x-6-in-x-8-ft-Douglas-Fir-Lumber-Common-1-5-in-x-5-5-in-x-8-ft-Actual/1000571215", "access_date_local": "2026-09-28", "outcome": "ZIP/city pricing gate; no price extracted, location not selected."},
    {"id": "Lowe's 4x4x8 listing", "url": "https://www.lowes.com/pd/4-in-x-4-in-x-8-ft-Lumber/5002102005", "access_date_local": "2026-09-28", "outcome": "ZIP/city pricing gate; no price extracted, location not selected."},
    {"id": "Lowe's 4x6x8 Douglas-fir listing", "url": "https://www.lowes.com/pd/4-in-x-6-in-x-8-ft-Douglas-Fir-Lumber-Common-3-562-in-x-5-625-in-x-8-ft-Actual/1000028917", "access_date_local": "2026-09-28", "outcome": "ZIP/city pricing gate; no price extracted, location not selected."},
    {"id": "Home Depot 2x6x8 listing", "url": "https://www.homedepot.com/p/313837070", "access_date_local": "2026-09-28", "outcome": "Select-store prompt; no price extracted, store not selected."},
    {"id": "Home Depot 4x4x8 listing", "url": "https://www.homedepot.com/p/300874740", "access_date_local": "2026-09-28", "outcome": "Select-store prompt; no price extracted, store not selected."},
    {"id": "Home Depot 4x6x8 listing", "url": "https://www.homedepot.com/p/202083085", "access_date_local": "2026-09-28", "outcome": "Select-store prompt; no price extracted, store not selected."},
]

sheet_source = next(item for item in ply["sources"] if item["id"] == "lowes_item_12235_model_119055")
roseburg_source = next(item for item in ply["sources"] if item["id"] == "roseburg_exterior_core_live_page")
status = {
    "schema": "wood_joint_t08_material_stock_price_status/v1",
    "candidate": reg["candidate"],
    "geometry_revision_id": reg["geometry_revision_id"],
    "source_yield_register": {
        "path": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/current-timber-source-yield.json",
        "sha256": sha(TIMBER / "current-timber-source-yield.json"),
    },
    "timber_schedule": {
        "preserved_historical_frame_source_records": 20,
        "nominal_stock_classes": {"4x6": 4, "2x6": 16},
        "historical_source_records_define_current_purchase_list": False,
        "current_composition_rebuilds_frame_hosts": 16,
        "current_candidate_connector_block_blanks": {
            "count": 24,
            "by_stock_class": {"4x4": 18, "4x6_ripped": 4, "2x6": 2},
            "groups": stock_groups,
        },
        "linear_length_sums_mm_by_stock_class": {
            row["stock_class"]: row["combined_arithmetic_length_sum_mm"]
            for row in material["arithmetic_linear_length_screen"]
        },
        "length_sums_are_order_quantities": False,
        "cut_yield_known": False,
        "yield_missing_inputs": [
            "finished blank-to-stock nesting and per-piece orientation",
            "cutting kerf and end trim for a finalized cut plan",
            "defects, surfacing/section cleanup, damage, and receiving loss",
            "actual delivered stick lengths, sections, species/grade marks, treatment, moisture and condition",
            "post-rip inspection/regrade basis for the four 4x6-to-smaller-section blocks",
            "material assignment from proposed blocks to delivered boards",
        ],
        "four_ripped_4x6_blocks_grade_disposition": grade["status"],
        "observed_compatible_public_unit_price": None,
        "public_source_observations": price_sources,
        "excluded_mismatched_public_listing_examples": [
            {"listing": "Denver Fence Supply 4x4 Grade A", "displayed_price_usd": 22.50, "url": "https://denverfencesupply.com/product/4x4x8-grade-a/", "exclusion": "No species, grading rule, actual section, treatment or verified quantity; not a DF-L No. 2 match."},
            {"listing": "Denver Fence Supply 4x6 WRC", "displayed_price_usd": 41.45, "url": "https://denverfencesupply.com/product/4x6x8-wrc/", "exclusion": "Seller-labeled WRC, not conditional DF-L basis; no grade/actual section/treatment or post-rip grade."},
            {"listing": "Denver Fence Supply 2x6 WRC", "displayed_price_usd": 16.88, "url": "https://denverfencesupply.com/product/2x6x8-wrc/", "exclusion": "Seller-labeled WRC, not conditional DF-L basis; no grade/actual section/treatment."},
        ],
        "bounded_stock_cost": None,
    },
    "plywood": {
        "modeled_panel_count": manifest["inventory_counts"]["source_plywood_panels"],
        "retailer_reference": {
            "item": ply["identity_and_assignment_boundary"]["retailer_item_number"],
            "model": ply["identity_and_assignment_boundary"]["retailer_model_number"],
            "url": sheet_source["url"],
            "access_date_local": sheet_source["retrieved"],
            "listed_descriptors": "Lowe's listing title/descriptors say 23/32-in x 4-ft x 8-ft Douglas Fir; price/availability required ZIP/city; no amount captured.",
            "extraction_outcome": "Product page opened, but public price not returned before location selection; no location selected.",
        },
        "manufacturer_reference": {
            "publisher": roseburg_source["publisher"],
            "title": roseburg_source["title"],
            "url": roseburg_source["url"],
            "access_date_local": roseburg_source["retrieved"],
            "listed_descriptors": "Current Roseburg product card says AC Sanded, 23/32-in, five ply; family description says western-wood veneers.",
        },
        "lowes_to_roseburg_exact_product_identity": ply["identity_and_assignment_boundary"]["manufacturer_product_identity_crosswalk"],
        "exact_model_species": ply["identity_and_assignment_boundary"]["exact_model_species"],
        "exact_model_layup": ply["identity_and_assignment_boundary"]["exact_model_layup"],
        "physical_sheet_identity_and_lot": ply["identity_and_assignment_boundary"]["physical_sheet_identity"],
        "sheet_to_panel_map": ply["identity_and_assignment_boundary"]["sheet_to_body_map"],
        "price_or_procurement_quantity_observed": None,
        "bounded_sheet_cost": None,
        "unsupported": [
            "No observed price for item 12235/model 119055 in the public page without a ZIP/city selection.",
            "No source-backed identity crosswalk from that retailer model to a specific Roseburg product/layup.",
            "Six modeled panels do not establish how many sheets must be purchased or which physical sheets/lot are assigned.",
            "No price may be transferred from a similar thickness/face descriptor to the distinct manufacturer product family.",
        ],
    },
    "cost_bound_conclusion": {
        "source_backed_material_unit_prices_for_required_grade_and_identity": False,
        "yield_and_purchase_quantities_known": False,
        "material_lower_bound_usd": None,
        "material_upper_bound_usd": None,
        "full_candidate_total_or_range_supported": False,
        "why": "No accepted compatible timber unit price or cut yield/order quantity, and no plywood price/product identity/sheet order quantity; public numbers for non-matching stock or generic descriptors cannot close the gap.",
    },
}
dump(HERE / "material-stock-and-panel-status.json", status)

checks = {
    "schema": "wood_joint_t08_attempt02_verification/v1",
    "verified_on_local_date": "2026-09-28",
    "source_pin_count": len(pin_check),
    "source_pin_checks": pin_check,
    "queue_sha256_preserved": pins["task_queue_sha256_at_freeze"] == "e624e043f15b3fd361dc99b05be6a37ff625b6bcb0e1da2cccaf3cb557a0a35c",
    "reconciled_axis_counts": {
        "candidate_bolts": len(candidate_axis_ids),
        "retained_frame_bolts": len(retained_axis_ids),
        "hillman": len(hillman_axis_ids),
        "hillman_unchanged": len(unchanged),
        "hillman_moved": len(moved),
        "removed_sds_references": len(removed_ids),
    },
    "candidate_bolt_public_numeric_price_lead_count": sum(
        1 for item in prices["candidate_catalog_lead_rechecks"]
        if item.get("displayed_prices")
    ),
    "candidate_bolt_page_display_envelope_reproduces": False,
    "candidate_total_usd": None,
    "candidate_cost_range_usd": None,
    "candidate_product_selected": False,
    "received_identity_or_receipt_asserted": False,
    "product_specific_weight_claimed": False,
    "full_candidate_fit_or_criterion_pass_claimed": False,
    "hillman_receipt_cost_usd": prices["separate_hillman_panel_kicker_purchase_reference"]["receipt_cost_usd"],
    "hillman_replacement_listing_formula_reproduces": (
        prices["separate_hillman_panel_kicker_purchase_reference"]["conditional_full_replacement_arithmetic"]["boxes"]
        == math.ceil(66 / 50)
        and round(math.ceil(66 / 50) * prices["separate_hillman_panel_kicker_purchase_reference"]["displayed_price"]["amount"], 2)
        == prices["separate_hillman_panel_kicker_purchase_reference"]["conditional_full_replacement_arithmetic"]["arithmetic_usd"]
    ),
    "retained_reference_formula_reproduces_31_12": round(sum(x["extension_usd"] for x in cost["retained_frame_price_comparison"]["line_items"]), 2) == 31.12,
    "material_cost_bounds_remain_null": status["cost_bound_conclusion"]["material_lower_bound_usd"] is None and status["cost_bound_conclusion"]["material_upper_bound_usd"] is None,
    "only_new_attempt02_paths_written": True,
}
unit_prices = []
for lead in prices["candidate_catalog_lead_rechecks"]:
    for shown in lead.get("displayed_prices", []):
        basis = shown["basis"]
        if basis == "each":
            divisor = 1
        else:
            match = re.search(r"(\d+)-piece", basis)
            if not match:
                continue
            divisor = int(match.group(1))
        unit_prices.append(shown["amount"] / divisor)
envelope = prices["descriptive_candidate_bolt_display_envelope"]
checks["candidate_bolt_page_display_envelope_reproduces"] = (
    len([x for x in prices["candidate_catalog_lead_rechecks"] if x.get("displayed_prices")]) == 8
    and round(min(unit_prices), 4) == envelope["min_per_bolt_displayed_price"] == 0.2314
    and round(max(unit_prices), 2) == envelope["max_per_bolt_displayed_price"] == 2.54
)
if not all((
    checks["queue_sha256_preserved"],
    checks["hillman_replacement_listing_formula_reproduces"],
    checks["retained_reference_formula_reproduces_31_12"],
    checks["candidate_bolt_page_display_envelope_reproduces"],
    checks["material_cost_bounds_remain_null"],
)):
    raise SystemExit("closeout check failure")
dump(HERE / "verification.json", checks)
print(json.dumps({k: v for k, v in checks.items() if k != "source_pin_checks"}, indent=2))
