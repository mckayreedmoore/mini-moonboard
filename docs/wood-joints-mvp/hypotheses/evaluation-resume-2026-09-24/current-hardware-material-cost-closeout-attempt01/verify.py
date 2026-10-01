#!/usr/bin/env python3
"""Verify T08 source pins, fastener counts, stock arithmetic, and cost exclusions."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(name: str):
    return json.loads((HERE / name).read_text())


def main() -> int:
    pins = load("source-pins.json")
    fasteners = load("fastener-axis-register.json")
    costs = load("material-cost-register.json")
    checks: list[dict] = []

    def record(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"check": name, "status": "pass" if passed else "fail", "detail": detail})

    source_results = []
    for source in pins["source_files"]:
        path = ROOT / source["path"]
        actual = sha256(path) if path.is_file() else None
        source_results.append({
            "path": source["path"],
            "expected_sha256": source["expected_sha256_at_inventory"],
            "captured_sha256": source["actual_sha256_at_build"],
            "actual_sha256_at_verification": actual,
            "status": "match" if actual == source["expected_sha256_at_inventory"] == source["actual_sha256_at_build"] else "mismatch_or_missing",
        })
    record(
        "all inventoried source hashes remain current",
        bool(source_results) and all(row["status"] == "match" for row in source_results),
        f"{sum(row['status'] == 'match' for row in source_results)}/{len(source_results)} match",
    )
    record("expected source inventory size", len(source_results) == 35, str(len(source_results)))
    record(
        "selected authority and separate candidate identities",
        pins["selected_candidate_authority_preserved"] == "compact-floor-flush-development"
        and fasteners["selected_candidate_authority_preserved"] == "compact-floor-flush-development"
        and fasteners["candidate"] == "compact-floor-flush-wood-joints-development"
        and fasteners["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1",
        "selected baseline remains authoritative; T08 registers the reviewed separate candidate revision",
    )

    counts = fasteners["counts"]
    row_sets = {
        "candidate": fasteners["candidate_axis_rows"],
        "retained": fasteners["retained_axis_rows"],
        "hillman": fasteners["hillman_axis_rows"],
        "removed_sds": fasteners["removed_legacy_sds25112_axis_ids"],
    }
    for key, expected in (("candidate", 92), ("retained", 12), ("hillman", 66), ("removed_sds", 144)):
        rows = row_sets[key]
        ids = [row["axis_id"] if isinstance(row, dict) else row for row in rows]
        record(f"{key} unique axis count", len(ids) == expected and len(set(ids)) == expected, f"{len(ids)} rows")
    candidate_products = {product["id"] for product in fasteners["catalog_product_records"]}
    candidate_rows = fasteners["candidate_axis_rows"]
    candidate_refs_resolve = all(
        set(row["candidate_product_lead_ids"] + row["conditional_nut_lead_ids"]
            + row["conditional_washer_lead_ids"] + row["conditional_spacer_lead_ids"]).issubset(candidate_products)
        for row in candidate_rows
    )
    record("all candidate catalog references resolve", candidate_refs_resolve, f"{len(candidate_products)} catalog records")
    record(
        "candidate product and delivered-stack status remains pending",
        all(row["selected_product"] is None
            and row["delivered_shank_bounds"] is None
            and row["delivered_full_thread_interval"] is None
            and row["matched_nut_active_thread_interval"] is None
            and row["fit_status"].startswith("pending")
            for row in candidate_rows)
        and counts["fit_qualified_candidate_stacks"] == 0,
        "no SKU or delivered thread/engagement bound accepted",
    )
    record(
        "structural stack and separate washer-role arithmetic",
        counts["structural_stack_total"] == 104
        and counts["candidate_nuts"] == 92
        and counts["candidate_separate_washer_roles"] == 184
        and counts["retained_nuts"] == 12
        and counts["retained_separate_washer_roles"] == 24
        and counts["structural_separate_washers"] == 208,
        "92 candidate + 12 retained; two separate washer roles per stack",
    )
    retained_roles_ok = all(
        row["catalog_reference"]["purchased_piece_count"] == {"bolts": 1, "nuts": 1, "washers": 2}
        and row["current_candidate_recheck"] == "required"
        for row in fasteners["retained_axis_rows"]
    )
    record("retained 12 arrangements stay recheck-pending", retained_roles_ok, "selected-baseline reference only")
    hillman_rows = fasteners["hillman_axis_rows"]
    record(
        "Hillman purchase policy remains separate and fixed at 66",
        all(row["product"].startswith("Hillman/Fas-n-Tite 42605")
            and row["new_purchase_cost"] is None
            and row["receipt_cost"] is None
            and "outside this T08 closeout" in row["material_capacity_property_map"]
            for row in hillman_rows)
        and counts["hillman_owner_moved_axes_previously"] == 8
        and counts["hillman_axes_unchanged"] == 58,
        "66 screws; 8 prior owner-directed moves; no SPAX/SDS transfer",
    )
    removed_ids = set(fasteners["removed_legacy_sds25112_axis_ids"])
    record(
        "removed historical SDS axes are not current cost/quantity",
        len(removed_ids) == 144 and counts["removed_legacy_sds25112_axes"] == 144,
        "removed former ML24Z SDS25112 duties",
    )

    stock = costs["block_stock_schedule"]
    groups = stock["block_blank_groups"]
    record("current block blanks total 24", sum(group["quantity"] for group in groups) == 24, f"{sum(group['quantity'] for group in groups)} blanks")
    stock_counts = {
        stock_class: sum(group["quantity"] for group in groups if group["stock_class"] == stock_class)
        for stock_class in ("4x4", "4x6", "2x6")
    }
    record("block stock-class quantities", stock_counts == {"4x4": 18, "4x6": 4, "2x6": 2}, str(stock_counts))
    frame_records = stock["preserved_frame_source_records"]
    record("preserved frame source-record count", len(frame_records) == 20, f"{len(frame_records)} source records")
    record(
        "ripped 4x6 grade remains pending",
        "pending" in stock["4x6_ripped_block_grade_disposition"].lower(),
        stock["4x6_ripped_block_grade_disposition"],
    )
    sensitivity = stock["length_only_8ft_sensitivity"]
    expected_classes = {"4x4", "4x6", "2x6"}
    sensitivity_ok = {row["stock_class"] for row in sensitivity} == expected_classes
    for row in sensitivity:
        calculated = (
            row["proposed_block_blank_length_sum_mm"]
            + row["proposed_block_blank_count"] * row["assumed_crosscut_kerf_per_blank_mm"]
            + row["assumed_end_trim_mm_per_stock_piece"]
        )
        sensitivity_ok = sensitivity_ok and abs(calculated - row["arithmetic_consumed_length_mm"]) < 0.001
        sensitivity_ok = sensitivity_ok and abs(
            row["nominal_8ft_length_mm"] - row["arithmetic_consumed_length_mm"] - row["arithmetic_residual_mm"]
        ) < 0.001
        sensitivity_ok = sensitivity_ok and row["conditional_linear_board_count"] == 1
        sensitivity_ok = sensitivity_ok and "length_only_sensitivity" in row["board_count_status"]
    record("8-foot block arithmetic reproduces with explicit limits", sensitivity_ok, "length-only; no frame cuts or usable-yield claim")

    cost_lines = costs["candidate_cost_lines"]
    record(
        "all candidate, Hillman, lumber, comparator and historical price lines excluded",
        bool(cost_lines) and all(line["included_in_current_total"] is False for line in cost_lines),
        f"{len(cost_lines)} register lines; none included",
    )
    arithmetic_ok = True
    for line in cost_lines:
        if line.get("unit_price_usd") is not None and line.get("display_extension_usd") is not None:
            arithmetic_ok = arithmetic_ok and abs(
                round(line["quantity"] * line["unit_price_usd"] + 1e-9, 2) - line["display_extension_usd"]
            ) < 0.001
    record("displayed by-each extensions reconcile", arithmetic_ok, "comparison arithmetic only")

    retained = costs["retained_frame_price_comparison"]
    retained_sum = round(sum(line["extension_usd"] for line in retained["line_items"]), 2)
    retained_arithmetic_ok = all(
        round(line["quantity"] * line["unit_price_usd"] + 1e-9, 2) == line["extension_usd"]
        for line in retained["line_items"]
    )
    record(
        "retained-reference price comparison arithmetic",
        retained_arithmetic_ok
        and retained_sum == retained["displayed_by_each_subtotal_usd"] == 31.12
        and retained["included_in_current_candidate_total"] is False,
        "$" + format(retained_sum, ".2f") + "; catalog references only",
    )
    totals = costs["total_cost_status"]
    record(
        "no unsupported total, lower bound or cost range",
        totals["current_candidate_selected_product_total_usd"] is None
        and totals["candidate_cost_range_usd"] is None
        and totals["no_total_lower_bound_or_cost_range_inferred"] is True,
        f"{len(totals['why_not_computable'])} unresolved cost reasons",
    )
    record(
        "no product-specific fastener weight asserted",
        costs["weight_status"]["candidate_selected_fastener_weight"] is None
        and costs["weight_status"]["current_frame_hardware_weight"] is None,
        costs["weight_status"]["status"],
    )
    record(
        "T07 and panel-property scope remain excluded",
        "does not evaluate T07" in " ".join(costs["claim_limits"])
        and "does not remap panel properties" in " ".join(costs["claim_limits"]),
        "fit/transport and panel-property work stay in their assigned lanes",
    )

    passed = all(row["status"] == "pass" for row in checks)
    report = {
        "schema": "wood_joint_t08_hardware_material_cost_verification/v1",
        "verified_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "candidate": fasteners["candidate"],
        "geometry_revision_id": fasteners["geometry_revision_id"],
        "selected_candidate_authority_preserved": fasteners["selected_candidate_authority_preserved"],
        "verification_status": "PASS_SOURCE_BOUND_REGISTER_ONLY_WITH_PENDING_PRODUCT_MATERIAL_PRICE_GATES" if passed else "FAIL_REGISTER_OR_SOURCE_CHECK",
        "t08_terminal_status": "PENDING_PRODUCT_DELIVERY_MATERIAL_SOURCE_AND_COST_CLOSEOUT",
        "source_pin_count": len(source_results),
        "source_pin_results": source_results,
        "checks": checks,
        "unresolved_gates": [
            "Exact selected and delivered bolt/nut/washer identities, lot dimensions, usable shank, thread start/runout, and matched-nut active engagement interval.",
            "Supported washer footprint and product/material condition evidence for the selected delivered stacks.",
            "Current local compatible lumber quote and availability with species, grade, actual section, treatment, condition, length, quantity, delivery, and price.",
            "Current full-frame cut/owner-stock reconciliation and realistic whole-board yield including defects and section cleanup.",
            "Traceable post-rip grade/section disposition for four 4x6-derived blanks.",
            "Owner receipt or cost record for already-purchased Hillman 42605 screws if historical spend is required.",
            "Tax, freight, delivery, product-specific weights, and package-surplus calculations after product/stock choices exist.",
        ],
        "exact_next_action": [
            "Obtain authoritative selected-part and delivered-lot documents or measurements for bolts, matched nuts, washers and any spacer; keep each unknown pending.",
            "Obtain a current local lumber quote and inventory record for the required species/grade/sections, then reconcile it to the full 20-member frame cut list and 24 block blanks.",
            "Record traceable source-board and post-rip grade/section disposition for the four ripped 4x6 blanks.",
            "Recover the existing Hillman purchase receipt if historical spend is needed.",
            "Refresh this attempt's source pins and rerun build_register.py and verify.py after authoritative records are available.",
        ],
        "closeout_artifacts": [
            {"path": name, "sha256": sha256(HERE / name)}
            for name in (
                "README.md",
                "build_register.py",
                "source-pins.json",
                "fastener-axis-register.json",
                "material-cost-register.json",
                "verify.py",
            )
        ],
        "limit": "This verifies source/register consistency and arithmetic, not product acceptance, structural capacity, delivered fit, construction readiness, or climbing release.",
    }
    (HERE / "verification.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["verification_status"])
    for row in checks:
        if row["status"] != "pass":
            print(f"FAIL {row['check']}: {row['detail']}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
