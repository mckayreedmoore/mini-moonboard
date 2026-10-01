#!/usr/bin/env python3
"""Build source-bound T08 fastener and stock/cost registers from frozen inputs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent

PINNED_INPUTS = [
    ("current-candidate.json", "f4505746a0a33eac1771708fbc376686b801e2c2af3053d9447fbbc6e22491a4", "selected-candidate authority; confirms the preserved selected baseline"),
    ("wood-joints-candidate.json", "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d", "separate wood-joints candidate identity"),
    ("docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/revision.json", "148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695", "owner-reviewed geometry revision record"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt02/current-full-frame-input-manifest.json", "21073d852474d4443f61f2172cd9eabc3ce49ee86414facb105773822e3c60f3", "catalog/yield source manifest identity"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json", "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11", "latest source-prepared owner-reviewed candidate inventory"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json", "9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a", "92 candidate-axis coverage and geometry family source"),
    ("docs/wood-joints-mvp/source-inventory.json", "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78", "20 preserved source frame-timber records and source fastener identity"),
    ("docs/wood-joints-mvp/current-hardware-schedule.md", "47a1de21705570cfd23fb493c640d8983945ee410623e15484cf53ed7596bffa", "current quantity and specification-gap schedule"),
    ("docs/wood-joints-mvp/current-hardware-coverage.md", "6bda5d032d52c8da38e069548153dbfe93c6bdfeea6f8ded1ba4f650cf75dd8c", "current 92/12/66/144 hardware-count bridge"),
    ("docs/wood-joints-mvp/current-hardware-coverage.json", "011dcf33c8a99d5072623db06388ffc0e409c8824be15015e68b454c31e7305d", "machine-readable candidate/retained fastener axis IDs"),
    ("docs/wood-joints-mvp/current-frame-bolt-review.md", "20067540bd318a3639e90278874bf793445a14c34bd316e18c6e508c2a518c89", "retained frame arrangement disposition"),
    ("docs/wood-joints-mvp/wj24-retained-frame-bolt-audit.md", "05f534b8a616e65fd6be1d3d6533b1e59ad16e43db1059a1d92e1334bbca6ff9", "retained bolt axis audit"),
    ("docs/floor-flush-construction-kerf-right/bolt-hardware.csv", "a3081ca72f92271ae21967684c5b7a459619dc0cf5c00ac53e7d8cecd748afd8", "12 separate starting frame hardware catalog references"),
    ("docs/floor-flush-construction-kerf-right/connection-axes.csv", "174033945a2136b094bf99360cb2c6dfa409accef423ab12538ef289b5d36a58", "retained frame bolt axis identities"),
    ("docs/current-panel-screw-purchase.md", "68840b1b9d5d566e7ff179b28aab8954e56129738721d8ce164ff02fe987df95", "owner-purchased Hillman 42605 policy for 66 axes"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-bolt-catalog-screen-attempt01/README.md", "63f1527f55ecc9610b000303420ed3d1b3b467d1d4dbc269fd14ca56fb1b6193", "completed 92-axis vendor screen summary"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-bolt-catalog-screen-attempt01/catalog-screen.json", "0184e45a3991c3dfbd236696a5d6a50417299177e23e287b9279240b53adc3a8", "completed candidate product, source, price, and axis registry"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-bolt-catalog-screen-attempt01/verification.json", "9a116dfdcb4430ce526ebc8b679529f61f41d3913d29fa7da3e6c1e700bc9dc1", "completed 9-row/92-axis catalog-screen verification result"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-bolt-catalog-screen-attempt01/verify.py", "484662cc8f9323f82275a787853ba4f2e201c3b235537184f78dc32a8f87dec6", "prior read-only catalog-screen verifier"),
    ("docs/wood-joints-mvp/current-bolt-thread-boundary-screen-2026-09-27.md", "27397d18eb1f6d3039295210b72ab04ed5b16a30f3625303212c519c60a6afd5", "latest catalog-class versus delivered-thread limitation"),
    ("docs/wood-joints-mvp/current-bolt-thread-alternative-spec-research-2026-09-27.md", "658b1e141b5548b94631ff8f399f45d5796aa03c1e4bea36c8e3ef5b093b786a", "latest bolt/nut transition-source search"),
    ("docs/wood-joints-mvp/current-cost-coverage-2026-09-27.md", "cc6573512996a6a9757a880275ed8e2eece142aa51a29d3c0d726b4342b73197", "current cost-status bridge and predecessor exclusions"),
    ("docs/wood-joints-mvp/current-material-map-status-2026-09-27.md", "0ad2c85c9fdc6f3cd17a46c57639b4e63c6fd0119d565b45121715f1c1831e6f", "read-only current material-map status; no panel-property remapping"),
    ("docs/wood-joints-mvp/current-material-scenarios.md", "dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4", "existing conditional material/stock scenarios"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/README.md", "fe8d8ef513b03aedaee6acdc81aa53891c2dbfde2f2d0d90a993d9402423e442", "completed 20-frame/24-block stock and length schedule"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/current-timber-source-yield.json", "2c710708d5e775d742375e28fadd323ecfe7f8e81c186c6028704c903a65266c", "completed source-yield machine record"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/produce.py", "8b2b33e591dcb287dc9f7f05405a09b739b0c6770a919a55a30649af2ee44ad6", "prior yield producer; read-only input"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-price-research-attempt01/README.md", "5a7baa2a1dfcf5b6aa8a908b048f4cb613fde3454f2aa4fd26a197e053a5422f", "completed local-source price attempt; no matching price found"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-price-research-attempt02/README.md", "9c88c0c784d1389e5b3caec31c207b70e87a7588bca6dd70c3e0812a0e7b2a9a", "completed incremental listing-price attempt; no candidate quote"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-grade-disposition-attempt01/README.md", "7266a00f72dbe46ac6917cfc7ee3588f85ca5d42d9daf4a916ff6fa529a873b0", "completed post-rip grade disposition"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-grade-disposition-attempt01/grade-disposition.json", "c0e5c0bb9a32403a6fe047a3b995667f2d35df81b1333a68f773c318ed560e86", "machine-recorded four-rip grade uncertainty"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-grade-disposition-attempt01/verify.py", "f9511af9a94bb07c6874bae38475e9b92e8ba78c03999720822a2bec6431ef5e", "prior read-only grade disposition verifier"),
    ("docs/wood-joints-mvp/hypotheses/current-hardware-coverage-review-2026-09-25.md", "b3ce06b7d69a9b07bb48649c3f0859cad20baf1dbddcd5cad7046e1d97228c3c", "historical independent count review; reviewed older coverage hashes"),
    ("docs/wood-joints-mvp/wj24-development-costs.md", "f862191ad53e180f4876412217f2c339c57e6e087437c5762db73a124b69c661", "historical 104-candidate-axis/28-blank cost screen; excluded from current total"),
    ("docs/wood-joints-mvp/hardware-budget-2026-09-24.md", "97a0c0186bb6ca61383d19f4505848728f8424e6834b0f04d1d0f4931690e327", "historical 11.5-inch/previous-length budget; excluded from current total"),
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def read_json(rel: str):
    return json.loads((ROOT / rel).read_text())

def write_json(name: str, payload):
    (OUT / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

def main() -> int:
    source_pins = []
    mismatches = []
    for rel, expected, role in PINNED_INPUTS:
        path = ROOT / rel
        actual = sha256(path) if path.is_file() else None
        record = {
            "path": rel,
            "role": role,
            "expected_sha256_at_inventory": expected,
            "actual_sha256_at_build": actual,
            "status": "match" if actual == expected else "mismatch_or_missing",
        }
        source_pins.append(record)
        if actual != expected:
            mismatches.append(record)
    if mismatches:
        print(json.dumps({"status": "blocked_stale_inputs", "mismatches": mismatches}, indent=2))
        return 2

    current_candidate = read_json("current-candidate.json")
    wood_candidate = read_json("wood-joints-candidate.json")
    revision = read_json("docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/revision.json")
    manifest = read_json("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json")
    coverage = read_json("docs/wood-joints-mvp/current-hardware-coverage.json")
    catalog = read_json("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-bolt-catalog-screen-attempt01/catalog-screen.json")
    yield_data = read_json("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/current-timber-source-yield.json")
    prices = read_json("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/current-timber-source-yield.json")

    expected_candidate = "compact-floor-flush-wood-joints-development"
    expected_revision = "led-clearance-2x6-runner-seated-blocks-v1"
    if wood_candidate.get("candidate") != expected_candidate:
        raise SystemExit("candidate identity mismatch")
    if revision.get("revision_id") != expected_revision:
        raise SystemExit("geometry revision mismatch")
    if manifest.get("candidate") != expected_candidate:
        raise SystemExit("manifest candidate mismatch")
    if manifest.get("inventory_counts", {}).get("candidate_bolt_axes") != 92:
        raise SystemExit("manifest candidate axis count mismatch")
    if manifest.get("inventory_counts", {}).get("retained_starting_frame_bolt_axes") != 12:
        raise SystemExit("manifest retained axis count mismatch")
    if manifest.get("inventory_counts", {}).get("panel_kicker_screw_axes") != 66:
        raise SystemExit("manifest Hillman axis count mismatch")
    if manifest.get("inventory_counts", {}).get("replaced_historical_SDS_axes_removed_from_candidate") != 144:
        raise SystemExit("manifest removed SDS count mismatch")

    coverage_groups = coverage["candidate_family_coverage"]
    catalog_rows = catalog["axis_rows"]
    coverage_by_ids = {frozenset(g["axis_ids"]): g for g in coverage_groups}
    if len(coverage_by_ids) != len(coverage_groups):
        raise SystemExit("duplicate coverage family axis sets")
    product_by_id = {p["id"]: p for p in catalog["products"]}
    candidate_axis_rows = []
    for row in catalog_rows:
        group = coverage_by_ids.get(frozenset(row["axis_ids"]))
        if group is None:
            raise SystemExit("catalog row does not exactly match a coverage family")
        row_product_ids = list(row["product_ids"])
        if any(product_id not in product_by_id for product_id in row_product_ids):
            raise SystemExit("unresolved candidate product reference")
        candidate_axis_rows.extend(
            {
                "axis_id": axis_id,
                "family_id": group["family_id"],
                "catalog_row_id": row["row_id"],
                "modeled_underhead_to_tip_mm": row["modeled_underhead_to_tip_mm"],
                "modeled_wood_grip_mm": row["modeled_wood_grip_mm"],
                "candidate_product_lead_ids": [
                    product_id for product_id in row_product_ids
                    if product_by_id[product_id]["role"] == "bolt"
                ],
                "conditional_nut_lead_ids": [
                    product_id for product_id in row_product_ids
                    if product_by_id[product_id]["role"] == "nut"
                ],
                "conditional_washer_lead_ids": [
                    product_id for product_id in row_product_ids
                    if product_by_id[product_id]["role"] == "washer"
                ],
                "conditional_spacer_lead_ids": [
                    product_id for product_id in row_product_ids
                    if product_by_id[product_id]["role"] == "conditional_spacer"
                ],
                "selected_product": None,
                "delivered_shank_bounds": None,
                "delivered_full_thread_interval": None,
                "matched_nut_active_thread_interval": None,
                "fit_status": "pending_no_delivered_lot_or_matched_functional_thread_interval",
            }
            for axis_id in row["axis_ids"]
        )
    candidate_ids = [r["axis_id"] for r in candidate_axis_rows]
    if len(candidate_ids) != 92 or len(set(candidate_ids)) != 92:
        raise SystemExit("candidate axis rows are not a unique 92-axis inventory")

    retained_rows = []
    retained_map = {
        "retained_lumber_leg_4": ("407", "2573", "15025"),
        "retained_rail_front_4": ("367", "2571", "15023"),
        "retained_rail_rear_4": ("368", "2571", "15023"),
    }
    retained_ids = set()
    for group in coverage["retained_family_coverage"]:
        if group["family_id"] not in retained_map:
            raise SystemExit("unmapped retained bolt family")
        bolt_id, nut_id, washer_id = retained_map[group["family_id"]]
        for axis_id in group["axis_ids"]:
            if axis_id in retained_ids:
                raise SystemExit("duplicate retained frame bolt axis")
            retained_ids.add(axis_id)
            retained_rows.append({
                "axis_id": axis_id,
                "family_id": group["family_id"],
                "catalog_reference": {
                    "bolt_bolt_depot_product": bolt_id,
                    "nut_bolt_depot_product": nut_id,
                    "two_separate_washer_product": washer_id,
                    "purchased_piece_count": {"bolts": 1, "nuts": 1, "washers": 2},
                },
                "source_status": "preserved_selected_baseline_catalog_reference_only",
                "delivered_identity_or_ownership": "unverified",
                "current_candidate_recheck": "required",
                "selected_for_wood_joints": False,
            })
    if len(retained_rows) != 12:
        raise SystemExit("retained axis rows are not 12")

    hillman_rows = []
    for axis in manifest["panel_kicker_screw_axes"]:
        hillman_rows.append({
            "axis_id": axis["axis_id"],
            "product": "Hillman/Fas-n-Tite 42605; Lowe's item 755741",
            "quantity_policy": "one owner-purchased screw per fixed axis; preserve 66 count",
            "purchase_policy": "owner-selected lead-hole pilot plus panel-face countersink; see docs/current-panel-screw-purchase.md",
            "owner_moved_axis": axis.get("owner_moved_axis_record") is not None,
            "new_purchase_cost": None,
            "receipt_cost": None,
            "material_capacity_property_map": "outside this T08 closeout; do not transfer other screw-family values",
        })
    if len(hillman_rows) != 66:
        raise SystemExit("Hillman axis rows are not 66")
    moved_count = sum(r["owner_moved_axis"] for r in hillman_rows)
    if moved_count != 8:
        raise SystemExit(f"expected 8 previously owner-directed moved Hillman axes, got {moved_count}")

    removed = manifest["removed_historical_structural_axes"]["axis_ids"]
    if len(removed) != 144 or len(set(removed)) != 144:
        raise SystemExit("legacy removed SDS axes are not 144 unique IDs")

    fastener_register = {
        "schema": "wood_joint_t08_fastener_axis_register/v1",
        "prepared_date_local": "2026-09-27",
        "candidate": expected_candidate,
        "geometry_revision_id": expected_revision,
        "reviewed_repository_commit": manifest.get("reviewed_repository_commit"),
        "selected_candidate_authority_preserved": current_candidate["candidate"],
        "status": "source_bound_identity_and_count_register_only; no product or delivered stack accepted",
        "source_pins_file": "source-pins.json",
        "counts": {
            "candidate_bolt_axes": len(candidate_axis_rows),
            "retained_starting_frame_bolt_axes": len(retained_rows),
            "structural_stack_total": len(candidate_axis_rows) + len(retained_rows),
            "candidate_nuts": 92,
            "candidate_separate_washer_roles": 184,
            "retained_nuts": 12,
            "retained_separate_washer_roles": 24,
            "structural_separate_washers": 208,
            "hillman_42605_panel_kicker_axes": len(hillman_rows),
            "hillman_owner_moved_axes_previously": moved_count,
            "hillman_axes_unchanged": len(hillman_rows) - moved_count,
            "removed_legacy_sds25112_axes": len(removed),
            "fit_qualified_candidate_stacks": 0,
            "fit_qualified_retained_stacks": 0,
        },
        "candidate_axis_rows": sorted(candidate_axis_rows, key=lambda r: r["axis_id"]),
        "retained_axis_rows": sorted(retained_rows, key=lambda r: r["axis_id"]),
        "hillman_axis_rows": sorted(hillman_rows, key=lambda r: r["axis_id"]),
        "removed_legacy_sds25112_axis_ids": sorted(removed),
        "catalog_product_records": catalog["products"],
        "shared_candidate_nut_washer_lead_ids": catalog["shared_hardware_roles"],
        "global_limits": [
            "Candidate modeled 6.35 mm shaft envelopes and modeled lengths are not drill sizes, delivered shanks, or purchase lengths.",
            "Catalog minimum thread length, LT, LG, LB, and Y references do not bound delivered first full thread, last scratch, runout, or a matched nut's active unchamfered interval.",
            "No axis has a selected, received, matched, or fit-qualified product stack; catalog material/grade/finish labels are not lot certificates or capacities.",
            "The 12 retained bolts remain selected-baseline catalog references and require WJ24 recheck; their prior evidence does not transfer.",
            "The 66 Hillman 42605 panel/kicker screws are a separate purchased policy and do not inherit SPAX or SDS25112 properties.",
            "The 144 SDS25112 axes belonged to removed ML24Z duties and are not current WJ24 bolts or cost lines.",
            "This register records no tool-fit, installation-sweep, access, member-transport, geometry, CAD, or native-solver result."
        ],
    }

    block_groups = yield_data["candidate_block_blank_groups"]
    yield_rows = []
    for group in block_groups:
        yield_rows.append({
            "group_id": group["group_id"],
            "stock_class": group["stock_class"],
            "quantity": group["quantity"],
            "proposed_blank_length_mm": group["stock_length_mm"],
            "proposed_cross_section_mm": group["cross_section_mm"],
            "length_axis": group["length_axis"],
            "part_ids": group["part_ids"],
            "status": "proposed_blank_pattern_only",
        })
    frame_rows = []
    for row in yield_data["frame_member_records"]:
        frame_rows.append({
            "part_id": row["part_id"],
            "nominal_stock_class_inferred": row["nominal_stock_class_inferred_from_source_section"],
            "recorded_source_blank_length_mm": row["source_blank_length_axis_mm_recorded_as_first_dimension"],
            "source_species_grade_basis": row["source_species_grade_basis"],
            "current_composition_roles": row["current_composition_roles"],
            "current_finished_geometry_available": row["exact_current_finished_solid_available_in_manifest_sources"],
            "delivered_stock_observed": row["delivered_stock_observed"],
            "delivered_grade": row["delivered_grade"],
            "delivered_species_group": row["delivered_species_group"],
            "treatment": row["treatment"],
            "moisture_content": row["moisture_content"],
            "receiving_condition": row["receiving_condition"],
            "delivery_and_price": row["delivery_and_price"],
        })
    length_scenarios = []
    for stock_class, count, length_sum in (("4x4", 18, 2140.2), ("4x6", 4, 547.4), ("2x6", 2, 552.6)):
        kerf_mm = 3.175
        trim_mm = 25.4
        nominal_8ft_mm = 2438.4
        required = length_sum + count * kerf_mm + trim_mm
        length_scenarios.append({
            "stock_class": stock_class,
            "proposed_block_blank_count": count,
            "proposed_block_blank_length_sum_mm": length_sum,
            "assumed_crosscut_kerf_per_blank_mm": kerf_mm,
            "assumed_end_trim_mm_per_stock_piece": trim_mm,
            "arithmetic_consumed_length_mm": round(required, 3),
            "nominal_8ft_length_mm": nominal_8ft_mm,
            "arithmetic_residual_mm": round(nominal_8ft_mm - required, 3),
            "conditional_linear_board_count": 1 if required <= nominal_8ft_mm else None,
            "board_count_status": "length_only_sensitivity; excludes defects, section cleanup, receiving loss, and frame-member cuts",
        })
    if any(r["arithmetic_residual_mm"] < 0 for r in length_scenarios):
        raise SystemExit("8-foot block-only arithmetic does not fit")

    # Current date public listing observations. A row can be a price comparison
    # while remaining excluded from a selected product cost or purchase total.
    cost_lines = [
        {"id":"candidate-bolt-4in-grade5-bd334","scope":"candidate_outer_post_4","quantity":4,"unit_price_usd":0.45,"display_extension_usd":1.80,"package_offer":"$32.23 / 100; $284.00 / 1000","source_url":"https://boltdepot.com/Product-Details?product=334","source_observation":"public Bolt Depot listing; opened 2026-09-27 local, crawler reported 4 days old","price_class":"conditional Grade 5 comparison","included_in_current_total":False,"exclusion_reason":"no SKU selection, no delivered lot, and no thread-start or matched-nut active-thread bounds"},
        {"id":"candidate-bolt-5p5in-grade5-bd337","scope":"candidate_center_principal_5_5in","quantity":4,"unit_price_usd":0.72,"display_extension_usd":2.88,"package_offer":"$51.76 / 100; $456.00 / 1000","source_url":"https://boltdepot.com/Product-Details?product=337","source_observation":"public Bolt Depot listing; opened 2026-09-27 local, crawler reported 3 days old","price_class":"conditional Grade 5 comparison","included_in_current_total":False,"exclusion_reason":"no SKU selection, no delivered lot, and no thread-start or matched-nut active-thread bounds"},
        {"id":"candidate-bolt-6in-grade5-bd338","scope":"candidate_ordinary_48","quantity":48,"unit_price_usd":0.77,"display_extension_usd":36.96,"package_offer":"$55.13 / 100; $485.00 / 1000","source_url":"https://boltdepot.com/Product-Details?product=338","source_observation":"public Bolt Depot listing; opened 2026-09-27 local, crawler reported 3 days old","price_class":"conditional Grade 5 comparison","included_in_current_total":False,"exclusion_reason":"no SKU selection, no delivered lot, and no thread-start or matched-nut active-thread bounds"},
        {"id":"candidate-bolt-6in-grade5-bd338-centerpost-alternative","scope":"candidate_center_post_6in_alternative","quantity":4,"unit_price_usd":0.77,"display_extension_usd":3.08,"package_offer":"$55.13 / 100; $485.00 / 1000","source_url":"https://boltdepot.com/Product-Details?product=338","source_observation":"public Bolt Depot listing; opened 2026-09-27 local, crawler reported 3 days old","price_class":"conditional longer-length alternative","included_in_current_total":False,"exclusion_reason":"6-inch alternative length is not selected for this 5.48-inch modeled envelope; geometry/fit and delivered thread remain pending"},
        {"id":"candidate-bolt-6in-lowcarbon-bd10","scope":"candidate_ordinary_48","quantity":48,"unit_price_usd":0.39,"display_extension_usd":18.72,"package_offer":"$26.12 / 100; $209.00 / 1000","source_url":"https://boltdepot.com/Product-Details?product=10","source_observation":"public Bolt Depot listing; opened 2026-09-27 local, crawler reported 2 days old","price_class":"low-carbon Grade 2 or A307A comparator","included_in_current_total":False,"exclusion_reason":"not the Grade 5 candidate route shown in the current catalog screen; price only"},
        {"id":"candidate-bolt-8in-lowcarbon-bd14","scope":"candidate_side_16","quantity":16,"unit_price_usd":0.90,"display_extension_usd":14.40,"package_offer":"$59.92 / 100; $479.00 / 1000","source_url":"https://boltdepot.com/Product-Details?product=14","source_observation":"public Bolt Depot listing; opened 2026-09-27 local, crawler reported today","price_class":"low-carbon Grade 2 or A307A comparator","included_in_current_total":False,"exclusion_reason":"not the Grade 5 candidate route shown in the current catalog screen; price only"},
        {"id":"candidate-bolt-7p5in-hs104049","scope":"candidate_center_headers_8_axes","quantity":8,"unit_price_usd":2.54,"display_extension_usd":20.32,"package_offer":"one each displayed; package quantity 1 in the catalog record","source_url":"https://histrength.com/104-049","source_observation":"2026-09-27 catalog-screen indexed capture; direct product page inaccessible, not live-verified","price_class":"cached conditional Grade 5 lead","included_in_current_total":False,"exclusion_reason":"price is indexed/cached, SKU is not selected, and full thread transition/nut engagement are unresolved"},
        {"id":"candidate-bolt-7p5in-fss412254-carton","scope":"candidate_center_headers_8_axes","quantity":8,"unit_price_usd":None,"display_extension_usd":None,"package_price_usd":382.42,"package_quantity":275,"source_url":"https://www.fastenersuperstore.com/products/412254/hex-cap-screws","source_observation":"2026-09-27 catalog-screen page capture; carton listing, no public stock quantity","price_class":"conditional Grade 5 carton alternative","included_in_current_total":False,"exclusion_reason":"carton price is an alternative to HiStrength and must not be summed with it; no fit or purchase selection"},
        {"id":"candidate-bolt-8in-hs104051-side","scope":"candidate_side_16","quantity":16,"unit_price_usd":1.36,"display_extension_usd":21.76,"package_offer":"package quantity 1 in indexed catalog record","source_url":"https://histrength.com/104-051","source_observation":"2026-09-27 catalog-screen indexed capture; direct product page inaccessible, not live-verified","price_class":"cached conditional Grade 5 lead","included_in_current_total":False,"exclusion_reason":"indexed price only; no lot, delivery, or thread transition bounds"},
        {"id":"candidate-bolt-8in-hs104051-innerheader-alternative","scope":"candidate_knee_inner_header_4","quantity":4,"unit_price_usd":1.36,"display_extension_usd":5.44,"package_offer":"package quantity 1 in indexed catalog record","source_url":"https://histrength.com/104-051","source_observation":"2026-09-27 catalog-screen indexed capture; direct product page inaccessible, not live-verified","price_class":"cached longer-length alternative","included_in_current_total":False,"exclusion_reason":"8-inch alternative is not the screened 7.75-inch class; no delivered fit or full-thread engagement"},
        {"id":"candidate-nut-1q20-grade5-bd2569","scope":"all_92_candidate_axes_if_1q20_path_selected","quantity":92,"unit_price_usd":0.07,"display_extension_usd":6.44,"package_price_usd":4.86,"package_quantity":100,"surplus_if_bag_bought":8,"source_url":"https://boltdepot.com/Product-Details?product=2569","source_observation":"public Bolt Depot listing; opened 2026-09-27 local, crawler reported today","price_class":"conditional Grade 5 nut price comparison","included_in_current_total":False,"exclusion_reason":"no universal 1/4-20 nut selection or matched functional-thread check across candidate axes"},
        {"id":"candidate-washer-1q-grade5-uss-bd15021","scope":"all_184_candidate_washer_roles_if_1q20_path_selected","quantity":184,"unit_price_usd":0.09,"display_extension_usd":16.56,"package_price_usd":6.19,"package_quantity":100,"packages_for_quantity":2,"package_total_usd":12.38,"surplus_if_bags_bought":16,"source_url":"https://boltdepot.com/Product-Details?product=15021","source_observation":"public Bolt Depot listing; opened 2026-09-27 local, crawler reported today","price_class":"conditional Grade 5 USS washer price comparison","included_in_current_total":False,"exclusion_reason":"modeled washer role diameters/support are not qualified against one universal washer product"},
        {"id":"candidate-nut-kljack-capture","scope":"candidate_92_shared_nut_lead","quantity":92,"unit_price_usd":None,"display_extension_usd":None,"package_price_usd":4.71,"package_quantity":100,"surplus_if_bag_bought":8,"source_url":"https://www.kljack.com/products/25cnfh5z/","source_observation":"prior indexed capture summarized in the 2026-09-27 catalog screen; direct page timed out; last displayed package amount not current-verified","price_class":"aged package comparison","included_in_current_total":False,"exclusion_reason":"price and public offer are aged; nut active-thread interval and lot remain unknown"},
        {"id":"candidate-washer-kljack-capture","scope":"candidate_184_shared_washer_lead","quantity":184,"unit_price_usd":None,"display_extension_usd":None,"package_price_usd":3.47,"package_quantity":100,"packages_for_quantity":2,"package_total_usd":6.94,"surplus_if_bags_bought":16,"source_url":"https://www.kljack.com/products/25nwus/","source_observation":"prior indexed capture summarized in the 2026-09-27 catalog screen; direct page timed out; last displayed package amount not current-verified","price_class":"aged package comparison","included_in_current_total":False,"exclusion_reason":"price and public offer are aged; washer strength and axis support remain unresolved"},
        {"id":"hillman-42605-receipt","scope":"panel_kicker_66","quantity":66,"unit_price_usd":None,"display_extension_usd":None,"source_url":"https://www.lowes.com/pd/Hillman-10-x-2-1-2-in-Ceramic-Deck-Screws-50-Count/999995042","source_observation":"owner purchase identity and policy are pinned locally; 2026-09-27 retailer page shows 50-count package but no amount used here","price_class":"already purchased; historical receipt unknown","included_in_current_total":False,"exclusion_reason":"receipt total was not recorded; replacement pricing would not equal owner's purchase cost"},
        {"id":"legacy-sds25112-removed","scope":"removed_ml24z_axes_144","quantity":0,"source_url":"https://www.strongtie.com/","source_observation":"144 former ML24Z SDS25112 axis IDs are marked removed by current attempt04 manifest","price_class":"outside current candidate","included_in_current_total":False,"exclusion_reason":"no current WJ24 purchase quantity; do not transfer the old angle/screw cost or behavior"},
        {"id":"candidate-connector-block-stock","scope":"24_current_block_blanks","quantity":24,"unit_price_usd":None,"display_extension_usd":None,"source_url":None,"source_observation":"current timber-price attempts and supplier pages were checked 2026-09-27; no candidate-matching local price/quote returned","price_class":"unpriced source stock","included_in_current_total":False,"exclusion_reason":"no supplier, compatible DF-L/species group, grade, actual section/condition, cut yield, or delivered quote"},
        {"id":"candidate-current-frame-stock","scope":"20_current_source_frame_records","quantity":20,"unit_price_usd":None,"display_extension_usd":None,"source_url":None,"source_observation":"source-yield schedule records 20 members; 16 are rebuilt by current composition, and source lengths do not define a current purchase cut list","price_class":"unpriced source stock","included_in_current_total":False,"exclusion_reason":"current frame cut stock, owner-stock disposition, whole-board yield, price and delivery are not reconciled"},
        {"id":"excluded-denver-fence-4x4-grade-a","scope":"4x4_price_comparator_only","quantity":1,"unit_price_usd":22.50,"display_extension_usd":None,"source_url":"https://denverfencesupply.com/","source_observation":"timber price attempt02 reports seller page at $22.50; no species, grading rule, actual size, treatment, or location stock quantity","price_class":"excluded mismatch comparator","included_in_current_total":False,"exclusion_reason":"seller-labeled Grade A cannot be matched to the candidate's source grade/species/material and final section"},
        {"id":"excluded-denver-fence-4x6-wrc","scope":"4x6_price_comparator_only","quantity":1,"unit_price_usd":41.45,"display_extension_usd":None,"source_url":"https://denverfencesupply.com/","source_observation":"timber price attempt02 reports WRC listing; actual section, grade, treatment, and local on-hand count absent","price_class":"excluded mismatch comparator","included_in_current_total":False,"exclusion_reason":"WRC listing is not the source DF-L No. 2 basis and cannot establish post-rip grade"},
        {"id":"excluded-denver-fence-2x6-wrc","scope":"2x6_price_comparator_only","quantity":1,"unit_price_usd":16.88,"display_extension_usd":None,"source_url":"https://denverfencesupply.com/","source_observation":"timber price attempt02 reports WRC listing; actual section, grade, treatment, and local on-hand count absent","price_class":"excluded mismatch comparator","included_in_current_total":False,"exclusion_reason":"WRC listing is not the candidate's source material basis"},
        {"id":"excluded-cedar-fence-4x4-wrc","scope":"4x4_price_comparator_only","quantity":1,"unit_price_usd":24.99,"display_extension_usd":None,"source_url":"https://www.cedarfencedirect.com/","source_observation":"timber price attempt02 reports local WRC fencing listing","price_class":"excluded mismatch comparator","included_in_current_total":False,"exclusion_reason":"WRC fencing item does not establish candidate species group, grade, section, or use"},
        {"id":"historical-wj24-cost-screen","scope":"predecessor_104_candidate_axes_28_blanks","quantity":0,"unit_price_usd":None,"display_extension_usd":71.72,"source_url":"docs/wood-joints-mvp/wj24-development-costs.md","source_observation":"historical 2026-09-24 partial by-each subtotal; pinned to predecessor layout","price_class":"historical excluded total","included_in_current_total":False,"exclusion_reason":"104-candidate-axis/216-washer/28-blank predecessor, not the owner-reviewed current 92-axis/24-blank revision"},
        {"id":"historical-2026-09-24-hardware-budget","scope":"predecessor_length_distribution","quantity":0,"unit_price_usd":None,"display_extension_usd":130.64,"upper_displayed_usd":178.00,"source_url":"docs/wood-joints-mvp/hardware-budget-2026-09-24.md","source_observation":"historical allowance included four 11.5-inch modeled bolt envelopes","price_class":"historical excluded range","included_in_current_total":False,"exclusion_reason":"predecessor length distribution and geometry; do not carry forward"},
    ]

    retained_price_lines = [
        {"component":"bolt","product_number":"407","quantity":4,"unit_price_usd":4.03,"extension_usd":16.12,"source_url":"https://boltdepot.com/Product-Details?product=407"},
        {"component":"bolt","product_number":"367","quantity":4,"unit_price_usd":0.81,"extension_usd":3.24,"source_url":"https://boltdepot.com/Product-Details?product=367"},
        {"component":"bolt","product_number":"368","quantity":4,"unit_price_usd":0.94,"extension_usd":3.76,"source_url":"https://boltdepot.com/Product-Details?product=368"},
        {"component":"nut","product_number":"2573","quantity":4,"unit_price_usd":0.30,"extension_usd":1.20,"source_url":"https://boltdepot.com/Product-Details?product=2573"},
        {"component":"nut","product_number":"2571","quantity":8,"unit_price_usd":0.11,"extension_usd":0.88,"source_url":"https://boltdepot.com/Product-Details?product=2571"},
        {"component":"washer","product_number":"15025","quantity":8,"unit_price_usd":0.36,"extension_usd":2.88,"source_url":"https://boltdepot.com/Product-Details?product=15025"},
        {"component":"washer","product_number":"15023","quantity":16,"unit_price_usd":0.19,"extension_usd":3.04,"source_url":"https://boltdepot.com/Product-Details?product=15023"},
    ]
    retained_each_total = round(sum(x["extension_usd"] for x in retained_price_lines), 2)

    source_attempts = [
        {"name":"current-bolt-catalog-screen-attempt01","status":"verification.json passed; 9 rows / 92 unique axes; catalog leads only; 0 fit-qualified","files":["docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-bolt-catalog-screen-attempt01/README.md","docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-bolt-catalog-screen-attempt01/catalog-screen.json","docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-bolt-catalog-screen-attempt01/verification.json"]},
        {"name":"current-timber-source-yield-attempt01","status":"reconciles 20 preserved frame records and 24 current block IDs; length sums only, no usable yield or purchase cut list","files":["docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/README.md","docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/current-timber-source-yield.json"]},
        {"name":"current-timber-price-research-attempt01","status":"no usable local product price or inventory observed","files":["docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-price-research-attempt01/README.md"]},
        {"name":"current-timber-price-research-attempt02","status":"public local listings priced, but no candidate-compatible material/section/grade/quantity quote","files":["docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-price-research-attempt02/README.md"]},
        {"name":"current-timber-grade-disposition-attempt01","status":"no grade assigned; four 4x6 rips require traceable post-rip inspection/regrade before grade-specific values","files":["docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-grade-disposition-attempt01/README.md","docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-grade-disposition-attempt01/grade-disposition.json"]},
        {"name":"current-hardware-coverage-review-2026-09-25","status":"historical review only: its recorded covered MD/JSON hashes are older than the live coverage hashes pinned here","files":["docs/wood-joints-mvp/hypotheses/current-hardware-coverage-review-2026-09-25.md"]},
        {"name":"current-bolt-thread-boundary-screen-2026-09-27.md","status":"auxiliary source note: ASME class references do not bound delivered thread start/runout or matched nut active interval","files":["docs/wood-joints-mvp/current-bolt-thread-boundary-screen-2026-09-27.md"]},
        {"name":"current-bolt-thread-alternative-spec-research-2026-09-27.md","status":"auxiliary source note: no exact named-bolt thread-transition drawing or matched-nut active interval found","files":["docs/wood-joints-mvp/current-bolt-thread-alternative-spec-research-2026-09-27.md"]},
        {"name":"current-cost-coverage-2026-09-27.md","status":"source-bound bridge only; does not produce a current candidate total","files":["docs/wood-joints-mvp/current-cost-coverage-2026-09-27.md"]},
    ]

    material_register = {
        "schema": "wood_joint_t08_material_cost_register/v1",
        "prepared_date_local": "2026-09-27",
        "candidate": expected_candidate,
        "geometry_revision_id": expected_revision,
        "status": "conditional_price_and_length_screens_only; no complete current purchase total",
        "source_pins_file": "source-pins.json",
        "quantities": {
            "candidate_bolt_stacks": 92,
            "retained_frame_bolt_stacks": 12,
            "total_structural_stacks": 104,
            "candidate_nuts": 92,
            "candidate_washer_roles": 184,
            "retained_nuts": 12,
            "retained_washer_roles": 24,
            "hillman_42605_screws_already_purchased_policy": 66,
            "former_sds25112_axes_removed": 144,
            "current_connector_block_blanks": 24,
            "preserved_frame_source_records": 20,
        },
        "candidate_catalog_leads": catalog["products"],
        "current_web_price_and_spec_observations": [
            {"product_number":"334","role":"candidate conditional 1/4-20 x 4 in bolt","grade_finish":"Grade 5, zinc-plated steel; SAE J429; ASME B18.2.1","displayed_price_usd_each":0.45,"package":{"quantity":100,"displayed_price_usd":32.23},"length_tolerance_in":"+0.00/-0.06","catalog_thread_length":"minimum 3/4 in; not a thread-start coordinate","source_url":"https://boltdepot.com/Product-Details?product=334","retrieval_date_local":"2026-09-27","crawler_age":"4 days","status":"price/spec comparison only"},
            {"product_number":"337","role":"candidate conditional 1/4-20 x 5-1/2 in bolt","grade_finish":"Grade 5, zinc-plated steel; SAE J429; ASME B18.2.1","displayed_price_usd_each":0.72,"package":{"quantity":100,"displayed_price_usd":51.76},"length_tolerance_in":"+0.00/-0.10","catalog_thread_length":"minimum 3/4 in; not a thread-start coordinate","source_url":"https://boltdepot.com/Product-Details?product=337","retrieval_date_local":"2026-09-27","crawler_age":"3 days","status":"price/spec comparison only"},
            {"product_number":"338","role":"candidate conditional 1/4-20 x 6 in bolt","grade_finish":"Grade 5, zinc-plated steel; SAE J429; ASME B18.2.1","displayed_price_usd_each":0.77,"package":{"quantity":100,"displayed_price_usd":55.13},"length_tolerance_in":"+0.00/-0.10","catalog_thread_length":"minimum 3/4 in; not a thread-start coordinate","source_url":"https://boltdepot.com/Product-Details?product=338","retrieval_date_local":"2026-09-27","crawler_age":"3 days","status":"price/spec comparison only"},
            {"product_number":"10","role":"low-carbon 1/4-20 x 6 in price comparator; candidate ordinary axes 48","grade_finish":"low-carbon steel, Grade 2 or A307A; zinc-plated; ASME B18.2.1","displayed_price_usd_each":0.39,"package":{"quantity":100,"displayed_price_usd":26.12},"length_tolerance_in":"+0.06/-0.10","catalog_thread_length":"minimum 3/4 in; not a thread-start coordinate","source_url":"https://boltdepot.com/Product-Details?product=10","retrieval_date_local":"2026-09-27","crawler_age":"2 days","status":"excluded price comparator only"},
            {"product_number":"14","role":"low-carbon 1/4-20 x 8 in price comparator; candidate side axes 16","grade_finish":"low-carbon steel, Grade 2 or A307A; zinc-plated; ASME B18.2.1","displayed_price_usd_each":0.90,"package":{"quantity":100,"displayed_price_usd":59.92},"length_tolerance_in":"+0.10/-0.18","catalog_thread_length":"minimum 1 in; not a thread-start coordinate","source_url":"https://boltdepot.com/Product-Details?product=14","retrieval_date_local":"2026-09-27","crawler_age":"today","status":"excluded price comparator only"},
            {"product_number":"2569","role":"conditional candidate 1/4-20 hex nut","grade_finish":"Grade 5, zinc-plated steel; SAE J995; ASME B18.2.2","displayed_price_usd_each":0.07,"package":{"quantity":100,"displayed_price_usd":4.86},"dimension_bounds":"7/16 in AF; 0.212-0.226 in thickness","source_url":"https://boltdepot.com/Product-Details?product=2569","retrieval_date_local":"2026-09-27","crawler_age":"today","status":"price/spec comparison only; active nut thread interval not published"},
            {"product_number":"15021","role":"conditional candidate 1/4 in USS washer","grade_finish":"Grade 5, zinc-plated steel; ASME B18.21.1","displayed_price_usd_each":0.09,"package":{"quantity":100,"displayed_price_usd":6.19},"dimension_bounds":"OD 0.727-0.749 in; ID 0.307-0.327 in; thickness 0.051-0.080 in","source_url":"https://boltdepot.com/Product-Details?product=15021","retrieval_date_local":"2026-09-27","crawler_age":"today","status":"price/spec comparison only; supported bearing footprint/capacity not established"},
            {"product_number":"407","role":"retained baseline 1/2-13 x 8 in bolt reference","grade_finish":"Grade 5, zinc-plated steel; SAE J429; ASME B18.2.1","displayed_price_usd_each":4.03,"package":{"quantity":25,"displayed_price_usd":72.03},"length_tolerance_in":"+0.00/-0.18","catalog_thread_length":"minimum 1-1/2 in; not a thread-start coordinate","dimension_bounds":"3/4 in AF; head height 0.302-0.323 in","source_url":"https://boltdepot.com/Product-Details?product=407","retrieval_date_local":"2026-09-27","crawler_age":"2 days","status":"retained catalog-reference comparison only"},
            {"product_number":"367","role":"retained baseline 3/8-16 x 4 in bolt reference","grade_finish":"Grade 5, zinc-plated steel; SAE J429; ASME B18.2.1","displayed_price_usd_each":0.81,"package":{"quantity":50,"displayed_price_usd":29.10},"length_tolerance_in":"+0.00/-0.06","catalog_thread_length":"minimum 1 in; not a thread-start coordinate","dimension_bounds":"9/16 in AF; head height 0.226-0.243 in","source_url":"https://boltdepot.com/Product-Details?product=367","retrieval_date_local":"2026-09-27","crawler_age":"last week","status":"retained catalog-reference comparison only"},
            {"product_number":"368","role":"retained baseline 3/8-16 x 4-1/2 in bolt reference","grade_finish":"Grade 5, zinc-plated steel; SAE J429; ASME B18.2.1","displayed_price_usd_each":0.94,"package":{"quantity":50,"displayed_price_usd":33.54},"length_tolerance_in":"+0.00/-0.10","catalog_thread_length":"minimum 1 in; not a thread-start coordinate","dimension_bounds":"9/16 in AF; head height 0.226-0.243 in","source_url":"https://boltdepot.com/Product-Details?product=368","retrieval_date_local":"2026-09-27","crawler_age":"today","status":"retained catalog-reference comparison only"},
            {"product_number":"2573","role":"retained baseline 1/2-13 Grade 5 nut reference","grade_finish":"Grade 5, zinc-plated steel; SAE J995; ASME B18.2.2","displayed_price_usd_each":0.30,"package":{"quantity":50,"displayed_price_usd":10.02},"dimension_bounds":"3/4 in AF; height 0.427-0.448 in","source_url":"https://boltdepot.com/Product-Details?product=2573","retrieval_date_local":"2026-09-27","crawler_age":"today","status":"retained catalog-reference comparison only"},
            {"product_number":"2571","role":"retained baseline 3/8-16 Grade 5 nut reference","grade_finish":"Grade 5, zinc-plated steel; SAE J995; ASME B18.2.2","displayed_price_usd_each":0.11,"package":{"quantity":100,"displayed_price_usd":7.53},"dimension_bounds":"9/16 in AF; height 0.320-0.337 in","source_url":"https://boltdepot.com/Product-Details?product=2571","retrieval_date_local":"2026-09-27","crawler_age":"today","status":"retained catalog-reference comparison only"},
            {"product_number":"15025","role":"retained baseline 1/2 in USS Grade 5 washer reference","grade_finish":"Grade 5, zinc-plated steel; ASME B18.21.1","displayed_price_usd_each":0.36,"package":{"quantity":50,"displayed_price_usd":12.11},"dimension_bounds":"OD 1.368-1.380 in; ID 0.547-0.577 in; thickness 0.086-0.132 in","source_url":"https://boltdepot.com/Product-Details?product=15025","retrieval_date_local":"2026-09-27","crawler_age":"today","status":"retained catalog-reference comparison only"},
            {"product_number":"15023","role":"retained baseline 3/8 in USS Grade 5 washer reference","grade_finish":"Grade 5, zinc-plated steel; ASME B18.21.1","displayed_price_usd_each":0.19,"package":{"quantity":100,"displayed_price_usd":12.78},"source_url":"https://boltdepot.com/Product-Details?product=15023","retrieval_date_local":"2026-09-27","crawler_age":"today","status":"retained catalog-reference comparison only"},
        ],
        "candidate_cost_lines": cost_lines,
        "retained_frame_price_comparison": {
            "basis": "Current displayed by-piece prices for preserved catalog references; no ownership/receipt/received fit claim.",
            "line_items": retained_price_lines,
            "displayed_by_each_subtotal_usd": retained_each_total,
            "included_in_current_candidate_total": False,
            "tax_shipping_availability": "not quoted or verified",
        },
        "block_stock_schedule": {
            "source_yield_attempt": "current-timber-source-yield-attempt01",
            "block_blank_groups": yield_rows,
            "length_only_8ft_sensitivity": length_scenarios,
            "preserved_frame_source_records": frame_rows,
            "recorded_frame_source_length_sums_mm": yield_data["arithmetic_linear_length_screen"],
            "block_whole_board_cost": None,
            "current_frame_whole_board_cost": None,
            "status": "no candidate-compatible whole-board price, quote, source inventory, defect yield, or current frame cut list",
            "excluded_public_prices": [
                {"item":"Denver Fence Supply 4x4 Grade A listing","price_usd":22.50,"reason":"no species, grading rule, actual section, treatment, or yard quantity; not a DF-L No.2 match"},
                {"item":"Denver Fence Supply 4x6 WRC listing","price_usd":41.45,"reason":"WRC is not the conditional DF-L basis; no actual section/grade/treatment/quantity; cannot assign post-rip grade"},
                {"item":"Denver Fence Supply 2x6 WRC listing","price_usd":16.88,"reason":"WRC is not the conditional DF-L basis; no actual section/grade/treatment/quantity"},
                {"item":"Cedar Fence Direct 4x4 WRC listing","price_usd":24.99,"reason":"WRC fencing listing is not the required source material/grade/section record"},
                {"item":"Lowe's/Home Depot Douglas-fir/fir pages","price_usd":None,"reason":"location/ZIP prompt or store selection required; no public amount displayed in the checked view"},
                {"item":"Front Range Lumber local size pages","price_usd":None,"reason":"length classes listed; no item price or guaranteed inventory"},
            ],
            "4x6_ripped_block_grade_disposition": "pending_traceable_source_board_and_final_section_post-rip inspection/regrade; original grade/design values do not transfer",
            "current_frame_stock_limitation": "20 preserved source records are 4 nominal 4x6 plus 16 nominal 2x6; current composition rebuilds 16 hosts, so these historical source lengths are not a current purchase cut list",
        },
        "total_cost_status": {
            "current_candidate_selected_product_total_usd": None,
            "candidate_cost_range_usd": None,
            "why_not_computable": [
                "No SKU or matched delivered 92-axis bolt/nut/washer set has been selected or fit-qualified.",
                "28 candidate bolt axes do not have an exact existing nominal length class in the current hardware schedule; catalog alternatives remain unselected.",
                "No candidate-compatible stock quote supplies the required material identity, grade/section/condition, usable stock count and price.",
                "Four section-ripped 4x6 blanks have no post-rip grade disposition.",
                "The 20 source frame records lack a current purchase/cut/owner-stock schedule after 16 hosts were rebuilt.",
                "The Hillman receipt amount is unknown; the 144 SDS25112 axes are removed and excluded.",
                "Tax, freight, delivery, live availability and product-specific weights are not quoted.",
            ],
            "no_total_lower_bound_or_cost_range_inferred": True,
        },
        "weight_status": {
            "candidate_selected_fastener_weight": None,
            "current_frame_hardware_weight": None,
            "status": "No accepted product schedule or source-supported per-piece/received-lot weights support a current fastener weight total. The 224.4207767 kg full-frame dead-load scenario and separate 25 kg accessory allowance are analysis mass scenarios, not product-specific fastener weights or purchase weights.",
        },
        "claim_limits": [
            "Catalog dimensions and stock patterns are product-listing or model/source scenarios, not delivered measurements or accepted construction instructions.",
            "No capacity, stiffness, wood/screw resistance, bearing acceptance, structural acceptance, or assembly fit is inferred.",
            "No selection is made among mutually exclusive product/length options, and product alternatives are never summed.",
            "No current total, lower bound, or cost range is reported.",
            "No receipt cost, stock ownership, purchase, delivery, inspection, or supplier contact is represented.",
            "This attempt does not evaluate T07 tool fit/transport and does not remap panel properties.",
        ],
    }

    source_pin_payload = {
        "schema": "wood_joint_t08_source_state/v1",
        "captured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "capture_policy": "Read-only input inventory. Every included local source hash was checked against its expected start-of-closeout value before any output file was written. Existing attempts listed below remain unmodified.",
        "candidate": expected_candidate,
        "geometry_revision_id": expected_revision,
        "selected_candidate_authority_preserved": current_candidate["candidate"],
        "source_files": source_pins,
        "completed_attempts_and_prior_records": source_attempts,
        "prior_hardware_coverage_review_limit": "current-hardware-coverage-review-2026-09-25 reviewed historical MD/JSON hashes 40aadf989a3d6d797f1ff1958aeba94389b72ea36d33ad36bcc39c9c424b1e60 and 8e1a5325d99aa83a82cfd7dba1e6767ea2e2ba484be38e5fb12df39b227afdea; those are not the live coverage hashes pinned in this closeout",
        "local_write_scope": "this new attempt directory only",
    }

    write_json("source-pins.json", source_pin_payload)
    write_json("fastener-axis-register.json", fastener_register)
    write_json("material-cost-register.json", material_register)
    print(json.dumps({
        "status": "built",
        "source_file_count": len(source_pins),
        "candidate_axis_count": len(candidate_axis_rows),
        "retained_axis_count": len(retained_rows),
        "hillman_axis_count": len(hillman_rows),
        "removed_sds_axis_count": len(removed),
        "block_group_count": len(yield_rows),
        "block_length_only_8ft_scenarios": len(length_scenarios),
        "retained_catalog_reference_by_each_usd": retained_each_total,
        "outputs": ["source-pins.json", "fastener-axis-register.json", "material-cost-register.json"],
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

