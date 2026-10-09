"""Independent source/census/interval audit; no CAD, native, or producer writes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import platform
import runpy
from decimal import Decimal as D
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1"
PROPOSAL = PACKET / "bolt-window-followup-v1"
ISSUED_SHA = "c3b1e839f0204862f5455d8b4b29bec024f2102fc42e573ba7528b4204d302d8"
PDF_SHA = "c3b36b05e45149816941ae0d3e3e17c808831ce4d93f9f082424d9ecebaaa0a6"
# Independently read Table 12 rows and Table 13 tolerances in the pinned PDF.
PRIMARY_ROWS = {368: ("4.75", "3.75", "3.44", ".10"),
                371: ("6.5", "5.25", "4.94", ".18"),
                407: ("8.5", "7.00", "6.62", ".18")}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def check(ok, why):
    if not ok:
        raise AssertionError(why)


def close(a, b, why):
    check(abs(float(a) - float(b)) < 1e-8, why)


def verify(pins):
    check(all(digest(ROOT / p) == h for p, h in pins.items()), "source hash mismatch")


def rejection_controls(evaluate):
    """Inject only in-memory values; all repository source files stay unchanged."""
    namespace = evaluate.__globals__
    real_loads = json.loads
    results = []
    for mode, expected in [
        ("source", "changed source:"),
        ("axis", "current complete axis records differ"),
        ("census", "current physical shaft census"),
        ("release", "release changed"),
    ]:
        def loads(raw, *args, **kwargs):
            value = real_loads(raw, *args, **kwargs)
            if isinstance(value, dict):
                revision = value.get("revision")
                if mode == "axis" and revision == "eoere-grid-aligned-wire-cutouts-v1":
                    value["axes"][0]["point_xyz_mm"][0] += 1
                if mode == "census" and "axes" in value and revision in {
                    "eoere-grid-aligned-wire-cutouts-v1", "eoere-bottom-rail-tnut-clearance-v1"
                }:
                    value["axes"][1]["id"] = value["axes"][0]["id"]
                if mode == "release" and value.get("schema") == "eoere_intermediate_bolt_dimension_inputs/v1":
                    value["release"]["strength"] = True
            return value

        try:
            if mode == "source":
                real_sha = namespace["sha"]
                namespace["sha"] = lambda p: "0" * 64 if str(p).endswith("/occupied-aligned-wire-v1.json") else real_sha(p)
                try:
                    evaluate()
                finally:
                    namespace["sha"] = real_sha
            else:
                with patch("json.loads", loads):
                    evaluate()
        except ValueError as error:
            check(expected in str(error), "unexpected rejection: " + str(error))
            results.append({"control": mode, "rejected": True, "message": str(error)})
        else:
            raise AssertionError("accepted negative control: " + mode)
    return results


def review(pdf, reproduced, snapshot):
    baseline = json.loads(snapshot.read_bytes())
    check(len(baseline) == 18, "expected fourteen shop and four proposal files")
    verify(baseline)
    check(digest(PROPOSAL / "result.json") == ISSUED_SHA, "reviewed result changed")
    check(digest(pdf) == PDF_SHA, "primary PDF changed")
    issued = json.loads((PROPOSAL / "result.json").read_bytes())
    spec = json.loads((PROPOSAL / "inputs.json").read_bytes())
    pins = issued["source_sha256"]
    check(len(pins) == issued["source_pin_count"] == 879, "source census")
    verify(pins)
    method = runpy.run_path(str(PROPOSAL / "analyze.py"))["evaluate"]
    fresh = method()
    check(fresh == issued and digest(reproduced) == ISSUED_SHA,
          "in-memory or fresh-file reproduction differs")
    current = json.loads((ROOT / spec["sources"]["current_geometry"]["path"]).read_bytes())
    raised = json.loads((PACKET.parent / "occupied-bottom-rail-v1.json").read_bytes())
    check(current["axes"] == raised["axes"], "complete current/raised axis equality")
    axes = {a["id"]: a for a in current["axes"]}
    with (PACKET / "bolt-stacks.csv").open(newline="") as stream:
        records = list(csv.DictReader(stream))
    worksheet = {r["axis_id"]: r for r in records}
    check(len(records) == len(worksheet) == len(axes) == 100 and set(worksheet) == set(axes),
          "physical worksheet census")
    check(all(r[k] == "" for r in records for k in r
              if k.startswith("Actual") or k == "Disposition"), "actual observations filled")
    prior = json.loads((PACKET / "hardware-result.json").read_bytes())
    covered = [a for g in prior["nominal_stack_groups"] for a in g["axis_ids"]]
    check(len(covered) == len(set(covered)) == 100 and set(covered) == set(axes), "prior group census")
    shorts = set()
    for row in records:
        axis = axes[row["axis_id"]]
        close(row["receiver_plus_plate_mm"], sum(axis[k] for k in ["grip_mm", "before_plate_mm", "after_plate_mm"]),
              "saved receiver stack")
        close(row["nominal_diameter_mm"], axis["diameter_mm"], "saved diameter")
        close(row["nominal_underhead_length_mm"], axis["nominal_under_head_length_mm"], "saved nominal length")
        check(row["receiver_member_ids"].split(";") == axis["receivers"], "receiver identity")
        # Decimal worksheet endpoint reconstruction independently identifies all old shorts.
        pitch = D("25.4") / D(row["UNC_threads_per_inch"])
        old_margin = (D(row["catalog_underhead_min_mm"]) - D(row["receiver_plus_plate_mm"])
                      - 2 * D(row["catalog_each_washer_max_mm"])
                      - D(row["catalog_nut_height_max_mm"]) - 2 * pitch)
        close(old_margin, row["catalog_min_length_max_stack_two_pitch_margin_mm"], "old worksheet margin")
        if old_margin < 0:
            shorts.add(row["axis_id"])
    selected = [a["axis_id"] for g in issued["groups"] for a in g["own_axes"]]
    check(len(selected) == len(set(selected)) == 24 and set(selected) == shorts
          == set(prior["catalog_short_stack_axis_ids"]), "all twenty-four old shorts covered")
    comparisons, total, bought, corner_count = [], D("0"), 0, 0
    for group in issued["groups"]:
        product = group["proposal"]
        row = worksheet[group["own_axes"][0]["axis_id"]]
        table = PRIMARY_ROWS[group["old_sku"]]
        for key, value in zip(["nominal_length_in", "Lg_max_in", "Lb_min_in", "length_tolerance_minus_in"], table):
            check(D(str(product[key])) == D(value), "primary table transcription")
        stack = D(row["receiver_plus_plate_mm"])
        length, lg, lb, tolerance = (D(v) * D("25.4") for v in table)
        w = tuple(D(row[k]) for k in ["catalog_each_washer_min_mm", "catalog_each_washer_max_mm"])
        nut = tuple(D(row[k]) for k in ["catalog_nut_height_min_mm", "catalog_nut_height_max_mm"])
        pitch = D("25.4") / D(row["UNC_threads_per_inch"])
        corners = list(itertools.product([length-tolerance, length], w, w, nut, [D("0"), lg]))
        tip_min = min(l-stack-wh-wn-n-2*pitch for l, wh, wn, n, g in corners)
        seat_min = min(stack+wh+wn-g for l, wh, wn, n, g in corners)
        corner_count += len(corners)
        close(tip_min, group["intermediate_window"]["catalog_min_length_max_stack_two_tip_margin_mm"], "two-pitch interval minimum")
        close(seat_min, group["intermediate_window"]["nut_near_minus_Lg_max_bounds_mm"][0], "gage interval minimum")
        check(tip_min > 0 and seat_min > 0, "conditional comparison")
        deficits = set()
        for proof in group["own_axes"]:
            own_row, axis = worksheet[proof["axis_id"]], axes[proof["axis_id"]]
            check(int(own_row["comparison_bolt_SKU"]) == group["old_sku"], "proposal own SKU")
            target = D(own_row["model_body_to_farthest_bearing_target_mm"])
            close(target, stack+D(own_row["model_each_washer_thickness_mm"]), "farthest bearing target datum")
            close(target-lb, proof["target_minus_proposed_Lb_min_mm"], "minimum body deficit")
            close(target-lg, proof["target_minus_proposed_Lg_max_mm"], "gage/profile distinction")
            deficits.add(str(target-lb))
            delta = length-D(own_row["nominal_underhead_length_mm"])
            close(delta, group["nominal_underhead_tip_and_withdrawal_increment_mm"], "underhead tip increment")
            for d, shift in zip(axis["direction_xyz"], proof["nominal_tip_extension_delta_xyz_mm"]):
                close(float(delta)*d, shift, "tip direction")
        packs = -(-product["quantity"] // product["pack_quantity"])
        spend = packs * D(str(product["observed_pack_price_usd"]))
        check(packs == group["buy_packs"] and spend == D(str(group["pack_spend_usd_before_shipping_tax"])), "pack arithmetic")
        total += spend
        bought += packs * product["pack_quantity"]
        check(all(group[k] is False for k in ["adopted", "smooth_body_or_resistance_accepted", "new_tip_and_tool_clearance_verified"]), "group acceptance")
        comparisons.append({"old_sku": group["old_sku"], "quantity": len(group["own_axes"]),
                            "minimum_two_pitch_margin_mm": str(tip_min),
                            "minimum_nut_near_minus_Lg_mm": str(seat_min),
                            "minimum_body_deficit_mm": sorted(deficits), "pack_spend_usd": str(spend)})
    check(total == D("55.94") and bought-24 == 11 and corner_count == 96, "total price/spare/corner arithmetic")
    check(all(v is False for v in issued["release"].values()), "release flags")
    controls = rejection_controls(method)
    verify(pins)
    verify(baseline)
    return {"schema": "eoere_intermediate_bolt_independent_review/v1",
            "status": "PASS_BOUNDED_SOURCE_CENSUS_AND_DIMENSION_REVIEW_WITH_ONE_LISTING_ACCESS_LIMIT",
            "issued_result_sha256": ISSUED_SHA, "review_source_sha256": digest(OWN),
            "frozen_shop14_and_proposal4_sha256": baseline,
            "all18_frozen_files_verified_before_after": True,
            "source_pin_count": len(pins), "source_map_canonical_sha256": canonical(pins),
            "all879_pins_verified_before_after": True,
            "fresh_output_byte_identical": True, "complete100_axis_records_exact": True,
            "all100_worksheet_and_prior_group_census_pass": True,
            "all24_original_shorts_covered": True, "decimal_box_corners_checked": corner_count,
            "comparisons": comparisons, "pack_total_usd": str(total), "spare_count": bought-24,
            "negative_controls": controls, "confirmed_blockers": [],
            "primary_standard_review": {"pdf_sha256": PDF_SHA,
                "visual_table_rows_and_definitions_match": True,
                "locators": "Table12 printed21-22/PDF pages31-32 (indices30-31); Table13 printed23/PDF page33 (index32); sections1.3/1.5/4.7",
                "limit": "Uncoated full-body hex cap screws only; finished zinc dimensions require applicable agreement; Lg is special ring-gage reach and Lb ends at last scratch/extrusion angle, neither is actual full-form thread onset."},
            "primary_listing_review": [
                {"sku": "38WP04", "url": "https://www.grainger.com/product/Hex-Head-Cap-Screw-Steel-38WP04",
                 "matching_specs_and_price": True, "partially_threaded": True, "price_usd_per10": "22.49"},
                {"sku": "G0340956", "url": "https://www.zoro.com/zoro-select-grade-5-12-13-hex-head-cap-screw-zinc-plated-steel-8-12-in-l-5-pk-n012000500850/i/G0340956/",
                 "matching_specs_and_price": True, "partially_threaded": True, "price_usd_per5": "15.15"},
                {"sku": "G0341148", "url": "https://www.zoro.com/zoro-select-grade-5-38-16-hex-head-cap-screw-zinc-plated-steel-4-34-in-l-10-pk-n012000370475/i/G0341148/",
                 "matching_specs_and_price": None, "access_limit": "Web exact URL and /i alias unavailable; direct HTTP403. Author reports an earlier primary observation of matching product/specs and $9.15 per ten; this reviewer cannot freshly reproduce that page. Pack arithmetic independently checked."}],
            "explicit_limits_preserved": ["Nominal receiver-plus-plate dimensions and independent catalog boxes only.",
                "No full smooth-bearing pass: saved minimum-body deficits remain 10.5156/10.5156/12.827 mm.",
                "Actual thread/runout, active nut threads, coating, washer/fillet seating, thread-bearing resistance, new tip/tool/removal paths remain unknown.",
                "No product adoption, force/strength/access transfer, fabrication or climbing release."],
            "execution": {"python_version": platform.python_version(), "dependencies": "Python standard library",
                          "command": "uv run python -B fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/catalog-hardware-strength-v1/shop-window-v1/intermediate-review-v1/review.py --pdf /tmp/mini-moonboard-asme-b18-2-1-2012-review.pdf --reproduced FRESH_REPRODUCED_JSON --snapshot fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/catalog-hardware-strength-v1/shop-window-v1/intermediate-review-v1/source-files.json --out FRESH_REVIEW_JSON",
                          "CAD": False, "native": False, "force_fields": False,
                          "producer_overwrite": False, "repository_mutation_in_controls": False}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--reproduced", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    check(not args.out.exists(), "preserve issued review output")
    result = review(args.pdf, args.reproduced, args.snapshot)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n")
    print(json.dumps({"out": str(args.out), "sha256": digest(args.out), "status": result["status"]}))
