"""Nominal retail hardware stack screen for the paired HL33 center-post axis."""

import json

MM_PER_IN = 25.4
POST_MM = 190.5
PLATE_MM = 4.55
WASHER_IN = 0.109  # Home Depot Everbilt 802294, nominal listing value
NUT_THICKNESS_IN = (0.427, 0.448)  # Lindstrom ASME B18.2.2 full 1/2-in hex nut

SOURCES = {
    "pose": "docs/bolted-candidate-prototypes/hardware_first_center_tongue.json",
    "bolt_8": "https://www.homedepot.com/p/204273630",
    "bolt_10": "https://www.homedepot.com/p/204281591",
    "bolt_12": "https://www.homedepot.com/p/204633168",
    "washer": "https://www.homedepot.com/p/204276406",
    "nut_thread": "https://www.lowes.com/pd/1-2-in-x-13-Galvanized-Steel-Hex-Nut/3037536",
    "nut_dimensions": "https://cdn.mscdirect.com/global/images/ProductDataSheet/pds_sku_254996_productbrochure_manual%20data%20sheet.pdf#page=85",
}


def calculate():
    """Bound end position from nominal grip; do not certify delivered fit."""
    wood_plates = POST_MM + 2 * PLATE_MM
    under_nut = wood_plates + 2 * WASHER_IN * MM_PER_IN
    candidates = []
    for length in (8, 10, 12):
        length_mm = round(length * MM_PER_IN, 4)
        thread_in = 6 if length in (8, 12) else None
        end = [
            round(length_mm - under_nut - thickness * MM_PER_IN, 4)
            for thickness in reversed(NUT_THICKNESS_IN)
        ]
        candidates.append(
            {
                "length_in": length,
                "length_mm": length_mm,
                "bolt_source": SOURCES[f"bolt_{length}"],
                "end_beyond_nut_mm": end,
                "length_status": (
                    "too_short_with_two_washers_and_full_nut"
                    if end[1] < 0
                    else "nominal_length_only"
                ),
                "published_thread_length_in": thread_in,
                "nominal_thread_start_from_bearing_face_mm": (
                    round(length_mm - thread_in * MM_PER_IN, 4) if thread_in else None
                ),
                "nominal_thread_start_before_nut_face_mm": (
                    round(under_nut - (length_mm - thread_in * MM_PER_IN), 4)
                    if thread_in
                    else None
                ),
                "thread_engagement_status": (
                    "no_full_nut_length"
                    if length == 8
                    else "unresolved_thread_start_and_runout"
                    if length == 10
                    else "nominal_thread_span_only_runout_unresolved"
                ),
            }
        )
    return {
        "status": "screen_only_no_selection",
        "axis": "center-tongue paired HL33 shared post through-bolt",
        "bolt": "1/2-13 Everbilt hex bolts listed A307; Grade A subtype unverified",
        "wood_mm": POST_MM,
        "plate_each_mm": PLATE_MM,
        "wood_and_plates_mm": wood_plates,
        "washers": "one under head and one under nut; nominal 0.109 in each",
        "under_nut_grip_mm": round(under_nut, 4),
        "minimum_10in_usable_thread_to_reach_nut_face_mm": round(
            10 * MM_PER_IN - under_nut, 4
        ),
        "full_hex_nut_thickness_in": list(NUT_THICKNESS_IN),
        "candidates": candidates,
        "sources": SOURCES,
        "unresolved": [
            "10-in SKU thread length/start is unpublished; runout and minimum usable nut engagement are unverified for all SKUs",
            "listed nominal bolt and washer dimensions have no delivered tolerance bound here",
            "zinc-plated and galvanized candidate finishes differ; exact coating and nut pairing require confirmation",
            "head height, installed washer/head/nut position, nearby solids, and wrench/socket sweep lack a qualified spatial envelope",
            "no connector, wood, bolt, or joint capacity or fabrication approval is inferred",
            "Everbilt listing says A307 but not Grade A; these examples do not yet meet the HL catalog's explicit Grade A identification requirement",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(calculate(), indent=2))
