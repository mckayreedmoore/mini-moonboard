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
OUT = HERE / "rawlocal/working-order/attempt03"
ENG = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/hardware-engagement"
FIT = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/hardware-length-fit/saved-source-attempt02"
TRAVEL = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/upper-screw-travel/attempt01"
PKG = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package"
CATALOG = f"{PKG}/catalog-costs.md"
TOP_WASHER_SETUP = f"{PKG}/rawlocal/top-washer-fit/prepare-attempt02/setup.json"
TOP_WASHER_RESULT = f"{PKG}/rawlocal/top-washer-fit/run-attempt01/result.json"
RETAIL_WASHER_CHECKS = "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/retail-washer-suite/attempt01-fine/checks.json"
TOP_RAIL_FAMILY = "candidate_top_rail_quarter_8in_4"
WASHER_HEAD_DATUM_OFFSET_MM = 0.468

PINNED = {
    f"{ENG}/hardware-engagement.json": "93c24fe5fb421152b0294cc35106bfb6d595b558f45e0be826406405084c111a",
    f"{ENG}/hardware-engagement-axes.csv": "9fd9f2f70dbaf347bf174925f21cc3d589c2640a7b42501e3b81f4533ab42cac",
    f"{FIT}/setup.json": "c49b72d742e1bce7c876860ec6c8c1d50e1d1c80bab6585636387df5f08a4529",
    f"{FIT}/result.json": "df5271e4c65f90a620dff4630cfa5d0dec303456fa1bb4a1185fc950dbaf2aa5",
    f"{TRAVEL}/result.json": "76379eb78eb73fbdcf9c6d4b5a0edf5497a0fcb67129f5d0eb956144b4dfb925",
    CATALOG: "140950afbb2ea2aa3018ddf3db1371de2df86228f4e826410bc422c68bf9ffdd",
    TOP_WASHER_SETUP: "d5b885bf3e023ca4efdcecd219453a288294d264692beb4d4bce100702928128",
    TOP_WASHER_RESULT: "bc1bbfd01d6c002ffc7a9da4b14b44e47bb98c4809ef5059c7b3e10bddd1d797",
    RETAIL_WASHER_CHECKS: "3e2dee327dbd81d8584955de3c4918c9acc695b0386fa46abd568ba767c64f74",
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
ADOPTED_WORKING_LENGTH_FAMILIES = {
    "candidate_center_post_4",
    "candidate_center_principal_header_4",
    "candidate_knee_inner_header_4",
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
    ("washer_25NWUS", "K.L. Jack", "25NWUS", NUT_SPECS[0][3], None, None, None),
    ("washer_hillman_885522", "Lowe's", "885522", [TOP_RAIL_FAMILY], "Hillman", "755754", 4),
    ("washer_2995", "Bolt Depot", "2995", NUT_SPECS[2][3], None, None, None),
    ("washer_15023", "Bolt Depot", "15023", NUT_SPECS[3][3], None, None, None),
    ("washer_15025", "Bolt Depot", "15025", NUT_SPECS[4][3], None, None, None),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def load_sources() -> tuple[list[dict], dict, dict, dict, dict, dict, list[dict], list[dict]]:
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
    washer_setup = json.loads(paths[TOP_WASHER_SETUP].read_text())
    washer_result = json.loads(paths[TOP_WASHER_RESULT].read_text())
    retail_checks = json.loads(paths[RETAIL_WASHER_CHECKS].read_text())
    if fit.get("setup_sha256") != digest(paths[f"{FIT}/setup.json"]):
        raise ValueError("length-fit result does not bind saved setup")
    if travel.get("source_sha256", {}).get(f"{FIT}/result.json") != digest(paths[f"{FIT}/result.json"]):
        raise ValueError("upper-screw result does not bind saved length-fit result")
    if washer_result.get("setup_sha256") != digest(paths[TOP_WASHER_SETUP]):
        raise ValueError("top-washer result does not bind saved setup")
    if washer_result.get("status") != "BOUNDED_NOMINAL_ENCLOSURES_CLEAR" or washer_result.get("overlap_pairs") or washer_result.get("undecided_pairs"):
        raise ValueError("top-washer bounded enclosure result is not clear")
    if washer_result.get("counts", {}).get("pairs") != 37352 or washer_result.get("counts", {}).get("washers") != 8 or washer_result.get("counts", {}).get("rail_axes") != 4:
        raise ValueError("top-washer bounded enclosure census changed")
    if retail_checks.get("status") != "FINITE_RETAIL_WASHER_SUITE_HYPOTHESIS" or retail_checks.get("counts", {}).get("completed_end_states") != 48 or retail_checks.get("counts", {}).get("end_states") != 48:
        raise ValueError("saved retail-washer mechanics suite is incomplete or changed")
    model = retail_checks.get("model", {})
    if (model.get("family", {}).get("inner_radius_mm") * 2,
            model.get("family", {}).get("outer_radius_mm") * 2,
            model.get("family", {}).get("thickness_mm"), model.get("E_mpa_hypothesis"),
            model.get("Fy_mpa_hypothesis")) != (8.3058, 25.4, 2.5, 200000.0, 250.0):
        raise ValueError("saved retail-washer model hypotheses changed")
    return axes, fit, travel, washer_setup, washer_result, retail_checks, pins, list(engagement["families"])


def build(axes: list[dict], fit: dict, travel: dict, washer_setup: dict, washer_result: dict,
          retail_checks: dict, pins: list[dict], families: list[dict]) -> tuple[bytes, bytes]:
    family_by_id = {f["family_id"]: f for f in families}
    counts = {fid: f["axis_count"] for fid, f in family_by_id.items()}
    if len(axes) != 104 or len({r["axis_id"] for r in axes}) != 104 or len(families) != 14:
        raise ValueError("engagement axes/family census changed")
    if sum(f["nuts"] for f in families) != 104 or sum(f["separate_washers"] for f in families) != 208:
        raise ValueError("engagement nut/washer census changed")
    if set(FAMILY_LINE) != set(family_by_id):
        raise ValueError("working route map does not cover exact family set")
    if set(family_by_id) != {fid for spec in WASHER_SPECS for fid in spec[3]}:
        raise ValueError("washer route map does not cover exact family set")
    axis_counts = {fid: sum(row["family_id"] == fid for row in axes) for fid in family_by_id}
    if axis_counts != counts:
        raise ValueError("axis rows do not reconcile to engagement family counts")
    fit_targets = {x["axis_id"]: x for x in fit["target_axes"]}
    planned = ADOPTED_WORKING_LENGTH_FAMILIES
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
    conditional = washer_setup.get("conditional_engagement_mm", {})
    expected_top_profile = {
        "Lmin": 192.3504,
        "required_LB": 145.375,
        "full_form_window": [182.8, 188.5404],
        "wood_grip": 177.8,
        "nominal_length": 203.2,
    }
    if conditional != expected_top_profile:
        raise ValueError("saved top-washer engagement profile changed")

    working_profiles = {}
    top_axis_rows = [row for row in axes if row["family_id"] == TOP_RAIL_FAMILY]
    if len(top_axis_rows) != 4:
        raise ValueError("top-rail working profile requires exactly four axes")
    for source in axes:
        fid = source["family_id"]
        intervals = json.loads(source["member_bearing_intervals"])
        shear_planes = json.loads(source["shear_planes"])
        if fid == TOP_RAIL_FAMILY:
            if not intervals or abs(intervals[0]["underhead_interval_mm"][0] - 2.032) > 1e-9:
                raise ValueError("top-rail source head-washer datum changed")
            for member in intervals:
                member["underhead_interval_mm"] = [round(float(value) + WASHER_HEAD_DATUM_OFFSET_MM, 9)
                                                    for value in member["underhead_interval_mm"]]
                key = "nds_nominal_D_quarter_thread_LB_min_mm"
                if key in member:
                    member[key] = round(float(member[key]) + WASHER_HEAD_DATUM_OFFSET_MM, 9)
            for plane in shear_planes:
                plane["underhead_coordinate_mm"] = round(float(plane["underhead_coordinate_mm"]) + WASHER_HEAD_DATUM_OFFSET_MM, 9)
                plane["smooth_shank_requirement_LB_mm"] = round(float(plane["smooth_shank_requirement_LB_mm"]) + WASHER_HEAD_DATUM_OFFSET_MM, 9)
            profile = {
                "minimum_physical_length_mm": conditional["Lmin"],
                "required_LB_each_member_max_mm": conditional["required_LB"],
                "full_form_male_thread_required_interval_mm": conditional["full_form_window"],
                "smooth_shank_LB_through_all_shear_planes_mm": max((p["smooth_shank_requirement_LB_mm"] for p in shear_planes), default=0.0),
                "wood_grip_mm": conditional["wood_grip"],
                "nominal_length_mm": conditional["nominal_length"],
                "source_head_washer_thickness_mm": 2.032,
                "working_head_washer_thickness_mm": 2.5,
                "head_datum_offset_mm": WASHER_HEAD_DATUM_OFFSET_MM,
                "member_bearing_intervals": intervals,
                "shear_planes": shear_planes,
                "basis": "saved conditional top-washer profile; head-datum bearing/shear positions shifted +0.468 mm",
            }
        else:
            profile = {
                "minimum_physical_length_mm": float(source["physical_three_pitch_length_min_mm"]),
                "required_LB_each_member_max_mm": float(source["required_LB_each_member_max_mm"]),
                "full_form_male_thread_required_interval_mm": json.loads(source["full_form_male_thread_required_interval_mm"]),
                "smooth_shank_LB_through_all_shear_planes_mm": float(source["smooth_shank_LB_through_all_shear_planes_mm"]),
                "wood_grip_mm": float(source["wood_grip_mm"]),
                "nominal_length_mm": (round(float(FAMILY_LINE[fid][3]) * 25.4, 6) if fid in ADOPTED_WORKING_LENGTH_FAMILIES
                                      else float(source["proposed_nominal_order_length_mm"])),
                "source_head_washer_thickness_mm": None,
                "working_head_washer_thickness_mm": None,
                "head_datum_offset_mm": 0.0,
                "member_bearing_intervals": intervals,
                "shear_planes": shear_planes,
                "basis": "frozen source engagement profile; unchanged",
            }
        working_profiles[source["axis_id"]] = profile
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
            line_id, supplier, item, family_ids = row[:4]
            brand, retailer_item, pack_quantity = row[4:] if kind == "washers" else (None, None, None)
            quantity = sum(counts[fid] * (2 if kind == "washers" else 1) for fid in family_ids)
            line = {
                "line_id": line_id, "supplier": supplier, "item": item, "category": kind,
                "family_allocations": [{"family_id": fid, "quantity": counts[fid] * (2 if kind == "washers" else 1)} for fid in family_ids],
                "quantity_required": quantity,
                "price": {"unit_price_usd": None, "package_price_usd": None},
                "delivery_conformity": None, "planning_status": "conditional working route; no physical selection or order",
            }
            if kind == "washers":
                line.update({
                    "brand": brand,
                    "retailer_item_number": retailer_item,
                    "listed_pack_quantity": pack_quantity,
                    "listed_package_basis": "listed 4-pack; nominal coverage arithmetic only" if pack_quantity else None,
                    "nominal_packs_to_cover": math.ceil(quantity / pack_quantity) if pack_quantity else None,
                })
            result.append(line)
        return result

    nuts = consumables(NUT_SPECS, "nuts")
    washers = consumables(WASHER_SPECS, "washers")
    if sum(x["quantity_required"] for x in nuts) != 104 or sum(x["quantity_required"] for x in washers) != 208:
        raise ValueError("nut/washer routes do not reconcile")
    washer_lines_by_id = {line["line_id"]: line for line in washers}
    retail_washer = washer_lines_by_id.get("washer_hillman_885522", {})
    if (retail_washer.get("quantity_required"), retail_washer.get("supplier"), retail_washer.get("item"),
            retail_washer.get("brand"), retail_washer.get("retailer_item_number"),
            retail_washer.get("listed_pack_quantity"), retail_washer.get("nominal_packs_to_cover")) != (
            8, "Lowe's", "885522", "Hillman", "755754", 4, 2):
        raise ValueError("top-rail Hillman washer route/package planning changed")
    if "washer_2994" in washer_lines_by_id or washer_lines_by_id["washer_2995"]["quantity_required"] != 8:
        raise ValueError("washer update changed a route beyond the eight top-rail washers")
    output_axes = []
    washer_by_family = {}
    for spec, line in zip(WASHER_SPECS, washers):
        line_id, supplier, item, family_ids, brand, retailer_item, pack_quantity = spec
        for fid in family_ids:
            washer_by_family[fid] = {
                "line_id": line_id,
                "supplier": supplier,
                "item": item,
                "brand": brand,
                "retailer_item_number": retailer_item,
                "listed_pack_quantity": pack_quantity,
                "washers_per_axis": 2,
                "quantity_required_for_family": counts[fid] * 2,
                "nominal_packs_to_cover_family": math.ceil(counts[fid] * 2 / pack_quantity) if pack_quantity else None,
                "planning_status": "conditional working route; no physical selection or order",
            }
    for source in axes:
        row = dict(source)
        fid = row["family_id"]
        line_id, supplier, item, length_in = FAMILY_LINE[fid]
        washer_route = washer_by_family[fid]
        profile = working_profiles[row["axis_id"]]
        row.update({
            "working_order_line_id": line_id,
            "working_order_supplier": supplier,
            "working_order_item": item,
            "working_order_nominal_length_in": length_in,
            "working_order_planning_status": "conditional working route; no physical selection or order",
            "working_order_delivery_conformity": "null",
            "working_order_washer_line_id": washer_route["line_id"],
            "working_order_washer_supplier": washer_route["supplier"],
            "working_order_washer_item": washer_route["item"],
            "working_order_washer_brand": washer_route["brand"] or "",
            "working_order_washer_retailer_item_number": washer_route["retailer_item_number"] or "",
            "working_order_washers_per_axis": washer_route["washers_per_axis"],
            "working_order_washer_listed_pack_quantity": washer_route["listed_pack_quantity"] or "",
            "working_order_washer_nominal_packs_to_cover_family": washer_route["nominal_packs_to_cover_family"] or "",
            "working_profile_minimum_physical_length_mm": profile["minimum_physical_length_mm"],
            "working_profile_required_LB_each_member_max_mm": profile["required_LB_each_member_max_mm"],
            "working_profile_full_form_male_thread_required_interval_mm": json.dumps(profile["full_form_male_thread_required_interval_mm"], separators=(",", ":")),
            "working_profile_smooth_shank_LB_through_all_shear_planes_mm": profile["smooth_shank_LB_through_all_shear_planes_mm"],
            "working_profile_wood_grip_mm": profile["wood_grip_mm"],
            "working_profile_nominal_length_mm": profile["nominal_length_mm"],
            "working_profile_member_bearing_intervals": json.dumps(profile["member_bearing_intervals"], separators=(",", ":"), sort_keys=True),
            "working_profile_shear_planes": json.dumps(profile["shear_planes"], separators=(",", ":"), sort_keys=True),
        })
        output_axes.append(row)
    fields = list(axes[0]) + [
        "working_order_line_id", "working_order_supplier", "working_order_item", "working_order_nominal_length_in",
        "working_order_planning_status", "working_order_delivery_conformity", "working_order_washer_line_id",
        "working_order_washer_supplier", "working_order_washer_item", "working_order_washer_brand",
        "working_order_washer_retailer_item_number", "working_order_washers_per_axis",
        "working_order_washer_listed_pack_quantity", "working_order_washer_nominal_packs_to_cover_family",
        "working_profile_minimum_physical_length_mm", "working_profile_required_LB_each_member_max_mm",
        "working_profile_full_form_male_thread_required_interval_mm",
        "working_profile_smooth_shank_LB_through_all_shear_planes_mm", "working_profile_wood_grip_mm",
        "working_profile_nominal_length_mm", "working_profile_member_bearing_intervals", "working_profile_shear_planes",
    ]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(output_axes)

    family_output = []
    for family in families:
        fid = family["family_id"]
        if fid == TOP_RAIL_FAMILY:
            profile = {
                "minimum_physical_length_mm": conditional["Lmin"],
                "required_LB_each_member_max_mm": conditional["required_LB"],
                "full_form_male_thread_required_interval_mm": conditional["full_form_window"],
                "smooth_shank_LB_through_all_shear_planes_mm": max(
                    working_profiles[row["axis_id"]]["smooth_shank_LB_through_all_shear_planes_mm"]
                    for row in axes if row["family_id"] == TOP_RAIL_FAMILY
                ),
                "wood_grip_mm": conditional["wood_grip"],
                "nominal_length_mm": conditional["nominal_length"],
                "source_head_washer_thickness_mm": 2.032,
                "working_head_washer_thickness_mm": 2.5,
                "head_datum_offset_mm": WASHER_HEAD_DATUM_OFFSET_MM,
                "basis": "saved conditional top-washer profile; head-datum bearing/shear positions shifted +0.468 mm",
            }
        else:
            profile = {
                "minimum_physical_length_mm": family["physical_three_pitch_length_min_mm"],
                "required_LB_each_member_max_mm": family["required_LB_each_member_max_mm"],
                "full_form_male_thread_required_interval_mm": family["full_form_male_thread_required_interval_mm"],
                "smooth_shank_LB_through_all_shear_planes_mm": family["smooth_shank_LB_through_all_shear_planes_max_mm"],
                "wood_grip_mm": family["wood_grip_mm"],
                "nominal_length_mm": (round(float(FAMILY_LINE[fid][3]) * 25.4, 6) if fid in ADOPTED_WORKING_LENGTH_FAMILIES
                                      else family["nominal_order_length_mm"]),
                "source_head_washer_thickness_mm": None,
                "working_head_washer_thickness_mm": None,
                "head_datum_offset_mm": 0.0,
                "basis": "frozen source engagement profile; unchanged",
            }
        family_output.append({
            **family,
            "working_order_line_id": FAMILY_LINE[fid][0],
            "working_order_supplier": FAMILY_LINE[fid][1],
            "working_order_item": FAMILY_LINE[fid][2],
            "working_order_nominal_length_in": FAMILY_LINE[fid][3],
            "working_order_washer_route": washer_by_family[fid],
            "working_profile": profile,
            "planning_status": "conditional working route; no physical selection or order",
            "delivery_conformity": None,
        })

    washer_fit_context = {
        "setup_sha256": next(x["sha256"] for x in pins if x["path"] == TOP_WASHER_SETUP),
        "result_sha256": next(x["sha256"] for x in pins if x["path"] == TOP_WASHER_RESULT),
        "status": washer_result["status"],
        "rail_axes": washer_result["counts"]["rail_axes"],
        "washers": washer_result["counts"]["washers"],
        "pairs": washer_result["counts"]["pairs"],
        "overlap_pairs": len(washer_result["overlap_pairs"]),
        "undecided_pairs": len(washer_result["undecided_pairs"]),
        "source_pin_count": len(washer_result["source_sha256"]),
        "source_unchanged_after_run": washer_result["source_unchanged_after_run"],
        "full_fit_or_turning_acceptance": False,
    }
    washer_mechanics_context = {
        "checks_sha256": next(x["sha256"] for x in pins if x["path"] == RETAIL_WASHER_CHECKS),
        "status": retail_checks["status"],
        "completed_end_states": retail_checks["counts"]["completed_end_states"],
        "requested_end_states": retail_checks["counts"]["end_states"],
        "nominal_cases": retail_checks["counts"]["nominal_cases"],
        "actual_washer_capacity_n": retail_checks["actual_washer_capacity_n"],
        "actual_washer_stress_mpa": retail_checks["actual_washer_stress_mpa"],
        "complete_joint_acceptance": retail_checks["complete_joint_acceptance"],
        "formal_acceptance": retail_checks["formal_acceptance"],
        "physical_release": retail_checks["physical_release"],
        "changed_contact_compliance_fed_back": False,
    }
    order = {
        "schema": "conditional_mvp_working_order/v2",
        "scope": "conditional working planning only; no physical candidate or received hardware selected",
        "counts": {"unique_structural_bolt_axes": 104, "structural_families": 14, "nuts": 104, "separate_washers": 208, "separate_hillman_42605_screws_already_purchased": 66},
        "limitations": ["No hardware capacity or delivery conformity assigned.", "Nominal length and saved screens do not certify delivered profile or fit.", "Unknown prices and delivery conformity are null; no rolled-up cost is provided.", "Top-rail washer dimensions and material remain hypotheses; saved mechanics and enclosure results do not establish product conformity or full fit."],
        "adopted_working_lengths": [
            {"family_id": "candidate_center_post_4", "quantity": 4, "nominal_length_in": 6, "nominal_length_mm": 152.4, "planning_status": "conditional working route; no physical selection or order"},
            {"family_id": "candidate_center_principal_header_4", "quantity": 4, "nominal_length_in": 8, "nominal_length_mm": 203.2, "planning_status": "conditional working route; no physical selection or order"},
            {"family_id": "candidate_knee_inner_header_4", "quantity": 4, "nominal_length_in": 8, "nominal_length_mm": 203.2, "planning_status": "conditional working route; no physical selection or order"},
        ],
        "bolt_order_lines": bolt_lines, "nut_order_lines": nuts, "washer_order_lines": washers,
        "separate_inventory": [{"item": "Hillman 42605", "quantity": 66, "status": "already purchased; separate panel/kicker screws", "delivery_conformity": None}],
        "families": family_output,
        "saved_screen_context": {
            "length_fit_result_sha256": next(x["sha256"] for x in pins if x["path"] == f"{FIT}/result.json"),
            "length_fit_status": fit["status"], "length_fit_pair_count": fit["pair_count"],
            "length_fit_target_axes": len(fit_targets), "length_fit_overlaps": len(fit["overlap_pairs"]),
            "length_fit_undecided": len(fit["undecided_pairs"]),
            "upper_screw_travel_result_sha256": next(x["sha256"] for x in pins if x["path"] == f"{TRAVEL}/result.json"),
            "upper_screw_travel_status": travel["status"], "upper_screw_travel_pairs": travel["counts"]["pairs"],
            "upper_screw_travel_overlaps": len(travel["overlapping_box_candidates"]),
            "top_washer_fit": washer_fit_context,
            "retail_washer_saved_mechanics": washer_mechanics_context,
        },
        "conditional_washer_model_hypotheses": {
            "brand": "Hillman",
            "manufacturer_item": "885522",
            "retailer": "Lowe's",
            "retailer_item_number": "755754",
            "listed_pack_quantity": 4,
            "nominal_packs_to_cover": 2,
            "modeled_inside_diameter_mm": retail_checks["model"]["family"]["inner_radius_mm"] * 2,
            "modeled_outside_diameter_mm": retail_checks["model"]["family"]["outer_radius_mm"] * 2,
            "modeled_thickness_mm": retail_checks["model"]["family"]["thickness_mm"],
            "elastic_modulus_mpa_hypothesis": retail_checks["model"]["E_mpa_hypothesis"],
            "yield_strength_mpa_hypothesis": retail_checks["model"]["Fy_mpa_hypothesis"],
            "actual_dimensions_mm": None,
            "actual_material": None,
            "status": "conditional model only; dimensions and material not verified for delivered Hillman item",
        },
        "remaining_hypotheses": [
            "Delivered Hillman 885522 washer dimensions, tolerances, thickness and material remain unverified; E=200000 MPa and Fy=250 MPa are model hypotheses.",
            "Saved 48-end washer mechanics suite is a finite hypothesis screen; it assigns no actual capacity or stress and has no formal, complete-joint or physical acceptance.",
            "Saved top-washer result clears 37352 bounded nominal enclosure pairs only; full fit, turning, physical access and delivered-part conformity remain unestablished.",
            "Changed washer contact compliance was not fed back into joint or frame response.",
            "All prices, availability, delivery conformity and delivered package contents remain unknown; listed four-pack arithmetic is nominal planning only.",
        ],
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

    axes, fit, travel, washer_setup, washer_result, retail_checks, pins, families = load_sources()
    order_json, axes_csv = build(axes, fit, travel, washer_setup, washer_result, retail_checks, pins, families)
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
