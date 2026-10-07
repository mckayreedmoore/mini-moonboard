"""Audit the retained aluminum concept's quantities and cheaper supplier prices.

Run: .venv/bin/python scripts/aluminum_cube_takeoff_audit.py
Reuses the original helper without changing its source-bound estimate or SVG.
These are assumed inventories and stock-packing examples, not shop cut lists.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
from collections import Counter
from pathlib import Path

import aluminum_cube_estimate as original

LOOKUP_DATE = "2026-10-05"
KERF_UM = 3000  # Assumed 3 mm per piece, including the final separating cut.
ORIGINAL_RECORD = original.OUT / "estimate.json"
SUPPLIERS = {
    "framing_tech_standard": {
        "url": "https://www.framingtech.com/shop/40x40-08-6m-40mm-x-40mm-t-slot-profile-4-8mm-32-tslots-403860",
        "sku": "40X40-08/6M",
        "stock_m": 6.0,
        "stock_usd": 195.0,
        "kg_per_m": 1.75,
        "inertia_cm4": 9.18,
        "alloy": "6063-T6",
        "note": "Published metric mass used; listed 1.200 lb/ft is not its exact conversion. Supplier specifications and configured availability need confirmation.",
    },
    "framing_tech_light": {
        "url": "https://www.framingtech.com/shop/40x40-08l-6m-40mm-x-40mm-light-t-slot-profile-4-8mm-32-tslots-403899",
        "sku": "40X40-08L/6M",
        "stock_m": 6.0,
        "stock_usd": 175.0,
        "kg_per_m": 1.49,
        "inertia_cm4": 8.12,
        "alloy": "6063-T6",
    },
    "framing_tech_standard_bundle": {
        "url": "https://www.framingtech.com/shop/40x40-08-6m-16pk-40mm-x-40mm-t-slot-profile-4-8mm-32-tslots-16-pack-592339",
        "stock_m": 6.0,
        "sticks": 16,
        "bundle_usd": 2380.0,
        "note": "96 m purchase; lower unit price does not reduce the total bill below eleven individual sticks.",
    },
    "framing_tech_shipping": {
        "url": "https://www.framingtech.com/shipping-returns",
        "note": "Shipping calculated after packaging by weight, size and destination; cut fees and delivered project quote absent.",
    },
    "automationdirect_light": {
        "url": "https://www.automationdirect.com/adc/shopping/catalog/structural_frames_-z-_rails/t-slotted_rails/40-4040cl",
        "sku": "40-4040CL",
        "usd_per_cm": 0.30,
        "max_length_m": 2.286,
        "note": "Live page price overrides cheaper indexed catalog prices. No cut charges; eligible free shipping advertised. Too short for assumed long members; no splices priced or qualified.",
    },
    "automationdirect_standard": {
        "url": "https://www.automationdirect.com/adc/shopping/catalog/structural_frames_-z-_rails/t-slotted_rails/40-4040c",
        "sku": "40-4040C",
        "usd_per_cm": 0.41,
        "max_length_m": 2.286,
        "note": "Same 90-inch maximum; short-member source only within this concept.",
    },
    "parco_standard_bundle": {
        "url": "https://parco-inc.com/product/e1515s-120-t-slotted-aluminum/",
        "sticks": 20,
        "stock_m": 120 * original.IN_M,
        "bundle_usd": 1879.20,
        "profile_width_mm": 38.1,
        "note": "Freight extra. Total 60.96 m is insufficient even before kerf/offcuts. Packaged shipping weight is not profile mass.",
    },
    "parco_light_bundle": {
        "url": "https://parco-inc.com/product/e1515lg-120-t-slotted-aluminum/",
        "sticks": 26,
        "stock_m": 120 * original.IN_M,
        "bundle_usd": 2049.84,
        "profile_width_mm": 38.1,
        "note": "79.248 m purchase; freight extra. Light section and 38.1 mm joint geometry require their own selection. This is not a structurally equivalent substitute.",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(shared_row: bool) -> list[tuple[str, int, float]]:
    """One explicit butt-joint example with four continuous cube uprights."""
    groups = []
    for label, count, length in original.TAKEOFF:
        if label == "outer cube":
            groups.append(("four continuous cube uprights", 4, original.CUBE_M))
            groups.append(
                (
                    "eight cube horizontals between uprights",
                    8,
                    original.CUBE_M - 2 * original.PROFILE_M,
                )
            )
        elif label == "side ties at the board top":
            groups.append(
                (label + ": between uprights", count, length - 2 * original.PROFILE_M)
            )
        elif label.startswith("kicker crosspieces") and shared_row:
            groups.append(
                (
                    "kicker bottom crosspieces: shared top row conditional",
                    count - 4,
                    length,
                )
            )
        else:
            groups.append((label, count, length))
    return groups


def pack(groups: list[tuple[str, int, float]], trim_um: int) -> dict:
    """Best fit decreasing in exact integer micrometres; feasible, not optimal."""
    stock_um = 6_000_000
    capacity = stock_um - trim_um
    lengths = [
        round(length * 1_000_000) for _, count, length in groups for _ in range(count)
    ]
    bins: list[list[int]] = []
    for length in sorted(lengths, reverse=True):
        needed = length + KERF_UM
        choices = [
            (capacity - sum(b) - needed, i)
            for i, b in enumerate(bins)
            if sum(b) + needed <= capacity
        ]
        if choices:
            bins[min(choices)[1]].append(needed)
        else:
            if needed > capacity:
                raise ValueError("Piece longer than usable stock")
            bins.append([needed])
    if Counter(x - KERF_UM for b in bins for x in b) != Counter(lengths):
        raise ValueError("Stock plan lost or duplicated pieces")
    if any(sum(b) > capacity for b in bins):
        raise ValueError("Stock plan overfilled a stick")
    patterns = Counter(tuple((x - KERF_UM) / 1000 for x in b) for b in bins)
    return {
        "method": "best fit decreasing; stock-count sufficiency for these assumed cuts only",
        "stock_length_m": stock_um / 1_000_000,
        "kerf_per_piece_mm": KERF_UM / 1000,
        "total_end_trim_per_stock_mm": trim_um / 1000,
        "sticks": len(bins),
        "purchased_length_m": len(bins) * stock_um / 1_000_000,
        "length_only_lower_bound_sticks": math.ceil(
            (sum(lengths) + len(lengths) * KERF_UM) / capacity
        ),
        "offcuts_plus_kerf_and_trim_m": (len(bins) * stock_um - sum(lengths))
        / 1_000_000,
        "patterns": [
            {"sticks": count, "piece_lengths_mm": list(pattern)}
            for pattern, count in patterns.items()
        ],
    }


def case(shared_row: bool, old_record: dict) -> dict:
    groups = inventory(shared_row)
    length = sum(count * size for _, count, size in groups)
    pieces = sum(count for _, count, _ in groups)
    profiles = []
    for index, profile in enumerate(old_record["profiles"]):
        economical = index == 0
        costs, weights = [], []
        for end in (0, 1):
            cutting = (
                [150.0, 350.0][end]
                if economical
                else pieces * 3.0 + [100.0, 250.0][end]
            )
            subtotal = (
                length * profile["usd_per_m"]
                + sum(original.hardware(economical, end).values())
                + cutting
                + [250.0, 600.0][end]
            )
            costs.append(subtotal * (1 + original.TAX_RATE))
            weights.append(
                (length * profile["kg_per_m"] + original.HARDWARE_MASS_RANGE_KG[end])
                / original.LB_KG
            )
        profiles.append(
            {
                "profile": profile["profile"],
                "total_usd_allowance_range": costs,
                "frame_lb_allowance_range": weights,
            }
        )
    return {
        "name": "conditional_shared_transition_row"
        if shared_row
        else "separate_transition_rows",
        "condition": "Sharing requires a connection/bearing detail supporting both panel edges, whose planes differ by 40 degrees."
        if shared_row
        else "Retains separate kicker-top and sloped-face-bottom rows.",
        "takeoff": [
            {
                "description": label,
                "pieces": count,
                "nominal_piece_m": size,
                "total_m": count * size,
            }
            for label, count, size in groups
        ],
        "pieces": pieces,
        "length_m": length,
        "reduction_from_original_m": old_record["representative_length_m"] - length,
        "retained_profile_cost_mass_sensitivities": profiles,
        "sus_frame_lb_allowance_range": [
            (length * 1.65 + h) / original.LB_KG
            for h in original.HARDWARE_MASS_RANGE_KG
        ],
        "stock_packing_examples": [pack(groups, trim) for trim in (0, 20_000)],
    }


def main() -> None:
    old_record = json.loads(ORIGINAL_RECORD.read_text())
    original_helper = Path(original.__file__)
    if sha256(original_helper) != old_record["helper_sha256"]:
        raise ValueError("Original source-bound helper changed")
    for supplier in SUPPLIERS.values():
        if "bundle_usd" in supplier:
            supplier["purchased_m"] = supplier["sticks"] * supplier["stock_m"]
            supplier["normalized_usd_per_m"] = (
                supplier["bundle_usd"] / supplier["purchased_m"]
            )
        elif "stock_usd" in supplier:
            supplier["normalized_usd_per_m"] = (
                supplier["stock_usd"] / supplier["stock_m"]
            )
            supplier["raw_stock_usd_11_to_12_sticks"] = [
                supplier["stock_usd"] * n for n in (11, 12)
            ]
            supplier["raw_price_reduction_fraction_against_8020_lite"] = (
                1 - supplier["normalized_usd_per_m"] / 37.0
            )
            supplier["inertia_ratio_against_8020_lite"] = (
                supplier["inertia_cm4"] / 9.3983
            )
        elif "usd_per_cm" in supplier:
            supplier["normalized_usd_per_m"] = supplier["usd_per_cm"] * 100
    cases = [case(shared, old_record) for shared in (False, True)]
    report = {
        "scope": "same unobserved 2.6 m cube concept; quantity audit and cheaper supplier comparison only",
        "lookup_date": LOOKUP_DATE,
        "python_version": platform.python_version(),
        "source_sha256": {
            str(path.relative_to(original.ROOT)): sha256(path)
            for path in (Path(__file__), original_helper, ORIGINAL_RECORD)
        },
        "original_pieces": old_record["representative_pieces"],
        "original_length_m": old_record["representative_length_m"],
        "cases": cases,
        "suppliers": SUPPLIERS,
        "limits": [
            "Video and room dimensions remain unobserved; actual required inventory is not established.",
            "2.6 m cube dimensions are outside dimensions in the audited butt-joint example. Actual connector offsets and cuts remain unknown.",
            "The original 55-70 m range is a planning sensitivity, not demonstrated inventory bounds.",
            "Five backing rails, cross rows, 4.6 m of braces/standoffs and all hardware inventories remain assumptions, without structural acceptance.",
            "Shared transition row is conditional; no flat-bearing square-profile connection to both differently oriented panels has been selected.",
            "Packing models square cuts and per-piece 3 mm kerf; delivered stock tolerance, end trim, mitres and machining are unverified. A 12-stick heuristic result does not prove eleven impossible.",
            "Finished-member mass excludes unused stock and uses original 10-20 kg hardware allowance. New supplier raw-stock prices exclude cutting, connectors, freight and tax.",
            "Price and inertia comparisons do not establish capacity, compatible connections or mixed-brand acceptance.",
            "TNUTZ cost retains unverified per-inch scaling; long-member availability remains unquoted.",
            "No contact with suppliers, purchase, model adoption, CAD or native mechanics runs.",
        ],
    }
    output = original.OUT / "takeoff-audit.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "output": str(output.relative_to(original.ROOT)),
                "cases": [
                    {
                        "name": c["name"],
                        "pieces": c["pieces"],
                        "length_m": c["length_m"],
                        "stocks_zero_or_20mm_trim": [
                            p["sticks"] for p in c["stock_packing_examples"]
                        ],
                    }
                    for c in cases
                ],
                "framing_tech_raw_stock_usd": {
                    key: supplier["raw_stock_usd_11_to_12_sticks"]
                    for key, supplier in SUPPLIERS.items()
                    if "raw_stock_usd_11_to_12_sticks" in supplier
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
