"""Current PB02 ten-bolt BOM and illustrative cut-list; no release."""

import json
import math
from decimal import Decimal

from scripts.export_v4_viewer_scene import build_scene

INCH_MM = Decimal("25.4")
STOCK_LENGTH_MM = 8 * 12 * INCH_MM
CROSSCUT_KERF_MM = Decimal("3.2")

PIECES = {
    "shifted_post": (
        "PB02 shifted right center post",
        (Decimal("88.9"), Decimal("88.9"), Decimal("238.9")),
    ),
    "post_header_block": (
        "PB02 post/header block",
        (Decimal("88.9"), Decimal("88.9"), Decimal("143.9")),
    ),
    "upright_side_cleat": (
        "PB02 revised upright-side cleat",
        (Decimal("88.9"), Decimal("61.6"), Decimal(183)),
    ),
    "header_side_cleat": (
        "PB02 revised header-side cleat",
        (Decimal("70.95"), Decimal(145), Decimal(67)),
    ),
    "rear_cleat": (
        "PB02 rear return block",
        (Decimal("88.9"), Decimal("38.1"), Decimal(460)),
    ),
    "kicker_backer": (
        "PB02 kicker backer",
        (Decimal("139.7"), Decimal("88.9"), Decimal("238.9")),
    ),
}

BOLTS_BY_LENGTH_IN = {"5": 3, "6": 3, "8": 4}
BOLT_UNIT_COST_USD = {
    "5": Decimal("0.62"),
    "6": Decimal("0.71"),
    "8": Decimal("0.94"),
}
NUT_PACK = (12, Decimal("1.98"))
WASHER_PACK = (16, Decimal("1.98"))


def _money(value):
    return str(value.quantize(Decimal("0.01")))


def _cut_row(lengths):
    cuts = [Decimal(str(value)) for value in lengths]
    consumed = sum(cuts) + len(cuts) * CROSSCUT_KERF_MM
    return {
        "cut_lengths_mm": [float(value) for value in cuts],
        "crosscut_kerf_mm": float(CROSSCUT_KERF_MM),
        "consumed_mm": float(consumed),
        "remainder_mm": float(STOCK_LENGTH_MM - consumed),
    }


def _bound_pieces(scene):
    boxes = {row["name"]: row for row in scene["boxes"] if row["station"] == "PB02"}
    rows = []
    for piece_id, (viewer_name, dimensions) in PIECES.items():
        expected = [float(value) for value in dimensions]
        actual = boxes[viewer_name]["size_mm"]
        matches = len(actual) == 3 and all(
            math.isclose(value, target, abs_tol=1e-6)
            for value, target in zip(actual, expected)
        )
        if not matches:
            raise ValueError(
                f"{piece_id}: active viewer size {actual} does not match {expected}"
            )
        rows.append(
            {
                "id": piece_id,
                "viewer_box": viewer_name,
                "dimensions_mm": expected,
                "matches_active_viewer": True,
            }
        )
    return rows


def report():
    """Return the source-bound current inventory and illustrative stock arithmetic."""
    scene = build_scene()
    pb02_axes = [axis for axis in scene["axes"] if axis["station"] == "PB02"]
    if len(pb02_axes) != 10:
        raise ValueError("active PB02 viewer no longer contains ten bolt axes")
    if scene["fixed_panel_kicker_screw_axes"] != 66:
        raise ValueError("active viewer no longer preserves 66 panel/kicker screw axes")
    if scene["fabrication_released"]:
        raise ValueError("active viewer unexpectedly claims fabrication release")

    bolt_count = sum(BOLTS_BY_LENGTH_IN.values())
    nut_count = bolt_count
    washer_count = 2 * bolt_count
    bolt_cost = sum(
        BOLT_UNIT_COST_USD[length] * count
        for length, count in BOLTS_BY_LENGTH_IN.items()
    )
    allocated = (
        bolt_cost
        + Decimal(nut_count) * NUT_PACK[1] / NUT_PACK[0]
        + Decimal(washer_count) * WASHER_PACK[1] / WASHER_PACK[0]
    )
    first_checkout = bolt_cost + NUT_PACK[1] + 2 * WASHER_PACK[1]

    return {
        "status": "current_development_inventory",
        "geometry_binding": {
            "baseline": scene["baseline"],
            "pb02_variant_id": scene["pb02_variant_id"],
            "pb02_source_fingerprint": scene["pb02_source_fingerprint"],
            "pb02_bolt_axes": len(pb02_axes),
            "fixed_panel_kicker_screw_axes": scene["fixed_panel_kicker_screw_axes"],
        },
        "hardware": {
            "bolts_by_length_in": BOLTS_BY_LENGTH_IN,
            "bolt_count": bolt_count,
            "nut_count": nut_count,
            "washer_count": washer_count,
            "cost_usd": {
                "bolts": _money(bolt_cost),
                "allocated": _money(allocated),
                "first_checkout_excluding_lumber": _money(first_checkout),
            },
        },
        "pieces": _bound_pieces(scene),
        "stock": {
            "assumptions": {
                "stock_length_mm": float(STOCK_LENGTH_MM),
                "crosscut_kerf_mm": float(CROSSCUT_KERF_MM),
                "end_trim_mm": 0.0,
                "defect_allowance_mm": 0.0,
            },
            "4x4_8ft": _cut_row(("238.9", "183", "143.9")),
            "2x4_8ft": _cut_row(("460",)),
            "4x6_8ft": _cut_row(("238.9", "145")),
            "illustrative_rip_offcuts_mm": {
                "upright_side_from_4x4": 24.1,
                "header_side_from_4x6_first_rip": 14.75,
                "header_side_from_4x6_second_rip": 69.5,
            },
            "rip_offcuts_are_illustrative": True,
        },
        "release": {
            "procurement": False,
            "drilling": False,
            "fabrication": False,
            "structural": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True))
