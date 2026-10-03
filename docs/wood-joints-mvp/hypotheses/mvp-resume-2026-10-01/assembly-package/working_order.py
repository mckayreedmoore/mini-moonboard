#!/usr/bin/env python3
"""Export conditional working procurement rows from pinned assembly records."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
OUT = HERE / "rawlocal/working-order/attempt02"
ENG = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/hardware-engagement"
FIT = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/hardware-length-fit/saved-source-attempt02"
TRAVEL = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/upper-screw-travel/attempt01"
PKG = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package"
CATALOG = f"{PKG}/catalog-costs.md"

PINNED = {
    f"{ENG}/hardware-engagement.json": "93c24fe5fb421152b0294cc35106bfb6d595b558f45e0be826406405084c111a",
    f"{ENG}/hardware-engagement-axes.csv": "9fd9f2f70dbaf347bf174925f21cc3d589c2640a7b42501e3b81f4533ab42cac",
    f"{FIT}/setup.json": "c49b72d742e1bce7c876860ec6c8c1d50e1d1c80bab6585636387df5f08a4529",
    f"{FIT}/result.json": "df5271e4c65f90a620dff4630cfa5d0dec303456fa1bb4a1185fc950dbaf2aa5",
    f"{TRAVEL}/result.json": "76379eb78eb73fbdcf9c6d4b5a0edf5497a0fcb67129f5d0eb956144b4dfb925",
    CATALOG: "140950afbb2ea2aa3018ddf3db1371de2df86228f4e826410bc422c68bf9ffdd",
}

FAMILY_LINE = {
    "candidate_ordinary_48": ("kljack_25C600HCS5Z", "K.L. Jack", "25C600HCS5Z", "6"),
    "candidate_center_post_4": ("kljack_25C600HCS5Z", "K.L. Jack", "25C600HCS5Z", "6"),
    "candidate_side_16": ("lawson_FA21103", "Lawson", "FA21103", "8"),
    "candidate_top_rail_quarter_8in_4": ("lawson_FA21103", "Lawson", "FA21103", "8"),
    "candidate_knee_inner_header_4": ("lawson_FA21103", "Lawson", "FA21103", "8"),
    "candidate_center_principal_header_4": ("lawson_FA21103", "Lawson", "FA21103", "8"),
    "candidate_top_side_5_16_4": ("boltdepot_28650", "Bolt Depot", "28650", "8"),
    "candidate_outer_post_4": ("kljack_25C400HCS5Z", "K.L. Jack", "25C400HCS5Z", "4"),
    "candidate_center_principal_4": ("kljack_25C550HCS5Z", "K.L. Jack", "25C550HCS5Z", "5.5"),
    "candidate_center_post_header_4": ("his_104_049", "HiStrength", "104-049", "7.5"),
    "candidate_knee_side_4": ("robrand_HC5127", "Ro-Brand", "HC5127", "9.5"),
    "retained_rail_front_4": ("boltdepot_367", "Bolt Depot", "367", "4"),
    "retained_rail_rear_4": ("boltdepot_368", "Bolt Depot", "368", "4.5"),
    "retained_lumber_leg_4": ("boltdepot_407", "Bolt Depot", "407", "8"),
}
MIN_PACK = {"kljack_25C600HCS5Z": 100, "lawson_FA21103": 25, "kljack_25C400HCS5Z": 100}

NUT_SPECS = [
    ("nut_25CNFH5Z", "K.L. Jack", "25CNFH5Z", ["candidate_ordinary_48", "candidate_side_16", "candidate_outer_post_4", "candidate_center_post_4", "candidate_center_principal_4", "candidate_center_post_header_4", "candidate_center_principal_header_4", "candidate_knee_inner_header_4", "candidate_knee_side_4"]),
    ("nut_2569", "Bolt Depot", "2569", ["candidate_top_rail_quarter_8in_4"]),
    ("nut_2583", "Bolt Depot", "2583", ["candidate_top_side_5_16_4"]),
    ("nut_2571", "Bolt Depot", "2571", ["retained_rail_front_4", "retained_rail_rear_4"]),
    ("nut_2573", "Bolt Depot", "2573", ["retained_lumber_leg_4"]),
]
WASHER_SPECS = [
    ("washer_25NWUS", "K.L. Jack", "25NWUS", NUT_SPECS[0][3]),
    ("washer_2994", "Bolt Depot", "2994", NUT_SPECS[1][3]),
    ("washer_2995", "Bolt Depot", "2995", NUT_SPECS[2][3]),
    ("washer_15023", "Bolt Depot", "15023", NUT_SPECS[3][3]),
    ("washer_15025", "Bolt Depot", "15025", NUT_SPECS[4][3]),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def load_sources() -> tuple[list[dict], dict, dict, list[dict], list[dict]]:
    paths = {key: REPO / key for key in PINNED}
    pins = []
    for rel, path in sorted(paths.items()):
        actual = digest(path)
        expected = PINNED.get(rel)
        if expected and actual != expected:
            raise ValueError(f"pinned source changed: {rel}: {actual}")
        pins.append({"path": rel, "sha256": actual})

    engagement = json.loads(paths[f"{ENG}/hardware-engagement.json"].read_text())
    with paths[f"{ENG}/hardware-engagement-axes.csv"].open(newline="", encoding="utf-8") as stream:
        axes = list(csv.DictReader(stream))
    fit = json.loads(paths[f"{FIT}/result.json"].read_text())
    travel = json.loads(paths[f"{TRAVEL}/result.json"].read_text())
    if fit.get("setup_sha256") != digest(paths[f"{FIT}/setup.json"]):
        raise ValueError("length-fit result does not bind saved setup")
    if travel.get("source_sha256", {}).get(f"{FIT}/result.json") != digest(paths[f"{FIT}/result.json"]):
        raise ValueError("upper-screw result does not bind saved length-fit result")
    return axes, fit, travel, pins, list(engagement["families"])


def build(axes: list[dict], fit: dict, travel: dict, pins: list[dict], families: list[dict]) -> tuple[bytes, bytes]:
    family_by_id = {f["family_id"]: f for f in families}
    counts = {fid: f["axis_count"] for fid, f in family_by_id.items()}
    if len(axes) != 104 or len({r["axis_id"] for r in axes}) != 104 or len(families) != 14:
        raise ValueError("engagement axes/family census changed")
    if sum(f["nuts"] for f in families) != 104 or sum(f["separate_washers"] for f in families) != 208:
        raise ValueError("engagement nut/washer census changed")
    if set(FAMILY_LINE) != set(family_by_id):
        raise ValueError("working route map does not cover exact family set")
    axis_counts = {fid: sum(row["family_id"] == fid for row in axes) for fid in family_by_id}
    if axis_counts != counts:
        raise ValueError("axis rows do not reconcile to engagement family counts")
    fit_targets = {x["axis_id"]: x for x in fit["target_axes"]}
    planned = {"candidate_center_post_4", "candidate_center_principal_header_4", "candidate_knee_inner_header_4"}
    planned_axes = {r["axis_id"] for r in axes if r["family_id"] in planned}
    if set(fit_targets) != planned_axes or len(fit_targets) != 12:
        raise ValueError("saved length-fit targets differ from three adopted planning families")
    target_lengths = {"candidate_center_post_4": 152.4, "candidate_center_principal_header_4": 203.2, "candidate_knee_inner_header_4": 203.2}
    if any(target["proposed_nominal_length_mm"] != target_lengths[target["family_id"]] for target in fit_targets.values()):
        raise ValueError("saved length-fit lengths differ from adopted working plan")
    if fit["status"] != "completed_saved_source_pair_screen" or fit["overlap_pairs"] or fit["undecided_pairs"]:
        raise ValueError("saved length-fit screen is not complete/clear")
    if travel["status"] != "completed_overlay_pair_screen" or travel["counts"]["pairs"] != 192 or travel["overlapping_box_candidates"]:
        raise ValueError("saved upper-screw travel screen differs from recorded result")
    bolt_lines = []
    line_order = dict.fromkeys(spec[0] for spec in FAMILY_LINE.values())
    for line_id in line_order:
        family_ids = [fid for fid, spec in FAMILY_LINE.items() if spec[0] == line_id]
        _, supplier, item, _ = FAMILY_LINE[family_ids[0]]
        min_pack = MIN_PACK.get(line_id)
        quantity = sum(counts[fid] for fid in family_ids)
        allocations = [{"family_id": fid, "quantity": counts[fid]} for fid in family_ids]
        lengths = sorted({FAMILY_LINE[fid][3] for fid in family_ids}, key=float)
        packs = math.ceil(quantity / min_pack) if min_pack else None
        bolt_lines.append({
            "line_id": line_id, "supplier": supplier, "item": item, "category": "structural_bolts",
            "family_allocations": allocations, "quantity_required": quantity,
            "working_nominal_lengths_in": lengths, "minimum_order_pack_quantity": min_pack,
            "minimum_packs_to_cover": packs, "spare_if_minimum_packs_ordered": packs * min_pack - quantity if packs else None,
            "price": {"unit_price_usd": None, "package_price_usd": None}, "delivery_conformity": None,
            "planning_status": "conditional working route; no physical selection or order",
        })
    if sum(x["quantity_required"] for x in bolt_lines) != 104:
        raise ValueError("bolt order lines do not reconcile to 104")
    by_line = {x["line_id"]: x for x in bolt_lines}
    if (by_line["kljack_25C600HCS5Z"]["quantity_required"], by_line["kljack_25C600HCS5Z"]["minimum_order_pack_quantity"]) != (48, 100):
        raise ValueError("K.L. Jack pooled route changed")
    if (by_line["lawson_FA21103"]["quantity_required"], by_line["lawson_FA21103"]["minimum_order_pack_quantity"]) != (24, 25):
        raise ValueError("Lawson pooled route changed")
    def consumables(specs: list[tuple], kind: str) -> list[dict]:
        result = []
        for row in specs:
            line_id, supplier, item, family_ids = row
            quantity = sum(counts[fid] * (2 if kind == "washers" else 1) for fid in family_ids)
            result.append({
                "line_id": line_id, "supplier": supplier, "item": item, "category": kind,
                "family_allocations": [{"family_id": fid, "quantity": counts[fid] * (2 if kind == "washers" else 1)} for fid in family_ids],
                "quantity_required": quantity,
                "price": {"unit_price_usd": None, "package_price_usd": None},
                "delivery_conformity": None, "planning_status": "conditional working route; no physical selection or order",
            })
        return result

    nuts = consumables(NUT_SPECS, "nuts")
    washers = consumables(WASHER_SPECS, "washers")
    if sum(x["quantity_required"] for x in nuts) != 104 or sum(x["quantity_required"] for x in washers) != 208:
        raise ValueError("nut/washer routes do not reconcile")
    output_axes = []
    for source in axes:
        row = dict(source)
        fid = row["family_id"]
        line_id, supplier, item, length_in = FAMILY_LINE[fid]
        row.update({
            "working_order_line_id": line_id,
            "working_order_supplier": supplier,
            "working_order_item": item,
            "working_order_nominal_length_in": length_in,
            "working_order_planning_status": "conditional working route; no physical selection or order",
            "working_order_delivery_conformity": "null",
        })
        output_axes.append(row)
    fields = list(axes[0]) + ["working_order_line_id", "working_order_supplier", "working_order_item", "working_order_nominal_length_in", "working_order_planning_status", "working_order_delivery_conformity"]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(output_axes)

    order = {
        "schema": "conditional_mvp_working_order/v1",
        "scope": "conditional working planning only; no physical candidate or received hardware selected",
        "counts": {"unique_structural_bolt_axes": 104, "structural_families": 14, "nuts": 104, "separate_washers": 208, "separate_hillman_42605_screws_already_purchased": 66},
        "limitations": ["No hardware capacity or delivery conformity assigned.", "Nominal length and saved screens do not certify delivered profile or fit.", "Unknown prices and delivery conformity are null; no rolled-up cost is provided."],
        "adopted_working_lengths": [
            {"family_id": "candidate_center_post_4", "quantity": 4, "nominal_length_in": 6, "nominal_length_mm": 152.4, "planning_status": "conditional working route; no physical selection or order"},
            {"family_id": "candidate_center_principal_header_4", "quantity": 4, "nominal_length_in": 8, "nominal_length_mm": 203.2, "planning_status": "conditional working route; no physical selection or order"},
            {"family_id": "candidate_knee_inner_header_4", "quantity": 4, "nominal_length_in": 8, "nominal_length_mm": 203.2, "planning_status": "conditional working route; no physical selection or order"},
        ],
        "bolt_order_lines": bolt_lines, "nut_order_lines": nuts, "washer_order_lines": washers,
        "separate_inventory": [{"item": "Hillman 42605", "quantity": 66, "status": "already purchased; separate panel/kicker screws", "delivery_conformity": None}],
        "families": [{**f, "working_order_line_id": FAMILY_LINE[f["family_id"]][0], "working_order_supplier": FAMILY_LINE[f["family_id"]][1], "working_order_item": FAMILY_LINE[f["family_id"]][2], "working_order_nominal_length_in": FAMILY_LINE[f["family_id"]][3], "planning_status": "conditional working route; no physical selection or order", "delivery_conformity": None} for f in families],
        "saved_screen_context": {
            "length_fit_result_sha256": next(x["sha256"] for x in pins if x["path"] == f"{FIT}/result.json"),
            "length_fit_status": fit["status"], "length_fit_pair_count": fit["pair_count"],
            "length_fit_target_axes": len(fit_targets), "length_fit_overlaps": len(fit["overlap_pairs"]),
            "length_fit_undecided": len(fit["undecided_pairs"]),
            "upper_screw_travel_result_sha256": next(x["sha256"] for x in pins if x["path"] == f"{TRAVEL}/result.json"),
            "upper_screw_travel_status": travel["status"], "upper_screw_travel_pairs": travel["counts"]["pairs"],
            "upper_screw_travel_overlaps": len(travel["overlapping_box_candidates"]),
        },
        "source_pins": pins,
    }
    return json_bytes(order), buffer.getvalue().encode()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write deterministic working-order outputs")
    mode.add_argument("--verify", action="store_true", help="compare saved outputs with deterministic replay")
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()

    axes, fit, travel, pins, families = load_sources()
    order_json, axes_csv = build(axes, fit, travel, pins, families)
    producer = Path(__file__).read_bytes()
    snapshot_name = "producer.py.snapshot"
    generated = {"working-order.json": order_json, "working-order-axes.csv": axes_csv, snapshot_name: producer}
    producer_sha = hashlib.sha256(producer).hexdigest()
    receipt = {"schema": "working_order_receipt/v1",
               "producer": {"path": str(Path(__file__).resolve().relative_to(REPO)), "sha256": producer_sha, "snapshot": snapshot_name, "snapshot_sha256": producer_sha},
               "inputs": pins, "outputs": [{"path": name, "sha256": hashlib.sha256(data).hexdigest()} for name, data in sorted(generated.items())]}
    generated["receipt.json"] = json_bytes(receipt)
    if args.verify:
        problems = [name for name, data in generated.items() if not (args.output_dir / name).is_file() or (args.output_dir / name).read_bytes() != data]
        if problems:
            raise SystemExit("verify mismatch: " + ", ".join(problems))
        print(f"verified {len(generated)} outputs in {args.output_dir}")
    else:
        conflicts = [name for name, data in generated.items()
                     if (args.output_dir / name).exists()
                     and (not (args.output_dir / name).is_file() or (args.output_dir / name).read_bytes() != data)]
        if conflicts:
            raise SystemExit("refusing to overwrite differing outputs: " + ", ".join(conflicts))
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, data in generated.items():
            target = args.output_dir / name
            if not target.exists():
                target.write_bytes(data)
        print(f"wrote {len(generated)} outputs in {args.output_dir}")


if __name__ == "__main__":
    main()
