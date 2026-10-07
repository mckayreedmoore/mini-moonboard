"""Reproduce an assumed aluminum cube takeoff; no structural/cut-list authority.

Run from the repository root with the existing Python environment:
  .venv/bin/python scripts/aluminum_cube_estimate.py
Only cost/mass arithmetic and a schematic are generated. No CAD or solve runs.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/wood-joints-mvp/hypotheses/aluminum-cube-concept"
LB_KG = 0.45359237
IN_M = 0.0254

# Owner reports a cube surrounding the board; its dimensions were not observed.
CUBE_M = 2.6
BOARD_M = 2.4384
KICKER_M = 0.277
RAILS = 5
PROFILE_M = 0.04
ROW_CLEAR_M = BOARD_M - RAILS * PROFILE_M
ANGLE_DEG = 40
LENGTH_RANGE_M = [55.0, 70.0]
HARDWARE_MASS_RANGE_KG = [10.0, 20.0]  # Allowance, not a weighed inventory.
TAX_RATE = 0.08  # Planning assumption; destination and taxable freight unknown.

TAKEOFF = [
    ("outer cube", 12, CUBE_M),
    ("sloped backing rails", RAILS, BOARD_M),
    ("main panel crosspieces: 3 rows, 4 pieces each", 12, ROW_CLEAR_M / 4),
    ("kicker uprights", RAILS, KICKER_M),
    ("kicker crosspieces: 2 rows, 4 pieces each", 8, ROW_CLEAR_M / 4),
    ("side ties at the board top", 2, CUBE_M),
    ("short corner braces: allowance", 8, 0.5),
    ("short board/frame standoffs: allowance", 4, 0.15),
]

SOURCES = {
    "video": {
        "url": "https://www.youtube.com/watch?v=Kj_uVZF9Wwk",
        "observed": False,
        "owner_description": "outer cube with Mini MoonBoard inside",
        "supplied_creator_comments": "SUS SF series; 40x40 mm; Frame DIY Lab cut to length",
        "capture": "YouTube web retrieval failed; local Chrome returned -5, setsockopt Operation not permitted; no screenshot exists",
    },
    "sus_4040": {
        "url": "https://fa.sus.co.jp/service/detail?ItemNo=SFF-424",
        "kg_per_m": 1.65,
        "price": None,
        "note": "Current example SFF-424, not identified as the video's exact part; US quote absent",
    },
    "sus_4080": {
        "url": "https://fa.sus.co.jp/service/detail?ItemNo=SFF-434",
        "kg_per_m": 2.80,
    },
    "tnutz_1515": {
        "url": "https://www.tnutz.com/product/ex-1515/",
        "kg_per_m": 2.140,
        "listed_variable_price_usd": [0.55, 50.42],
        "assumed_usd_per_in": 0.55,
        "note": "Per-inch scaling is an estimate, not a verified configured price; 38.1 mm system, not SUS; 2.6 m member availability needs confirmation",
    },
    "8020_lite": {
        "url": "https://8020.net/40-4040-lite.html",
        "lb_per_in": 0.0998,
        "usd_per_mm": 0.0370,
        "cut_charge_usd": 3.00,
    },
    "8020_heavy": {
        "url": "https://8020.net/40-4040.html",
        "lb_per_in": 0.1321,
        "usd_per_mm": 0.0441,
        "cut_charge_usd": 3.00,
    },
    "8020_4080": {
        "url": "https://8020.net/40-4080.html",
        "lb_per_in": 0.2317,
        "usd_per_mm": 0.0821,
        "cut_charge_usd": 3.79,
    },
    "tnutz_gusset": {"url": "https://www.tnutz.com/product/cb-015-a/", "usd": 3.55},
    "tnutz_nut": {"url": "https://www.tnutz.com/product/et-015/", "usd": 0.19},
    "tnutz_screw": {
        "url": "https://www.tnutz.com/product-category/15-series-hardware/",
        "assumed_usd": 0.20,
        "note": "Screw-price allowance; thread/length remain unselected",
    },
    "8020_gusset": {"url": "https://8020.net/40-4332.html", "usd": 7.73},
    "8020_bolt_nut": {"url": "https://8020.net/75-3422.html", "usd": 1.14},
}


def hardware(economical: bool, end: int) -> dict:
    """Inventories are planning allowances, not selected connection details."""
    standard_set = 3.55 + 2 * (0.19 + 0.20) if economical else 7.73 + 2 * 1.14
    angled_set = ([8.0, 20.0] if economical else [16.0, 30.0])[end]
    panel_set = ([1.0, 3.0] if economical else [2.0, 4.0])[end]
    return {
        "80_standard_bracket_sets_usd": 80 * standard_set,
        "20_angled_or_plate_connection_sets_usd": 20 * angled_set,
        "66_panel_mount_sets_usd": 66 * panel_set,
        "pads_caps_miscellaneous_usd": [75.0, 150.0][end],
    }


def estimate(
    name: str, kg_m: float, usd_m: float, economical: bool, pieces: int
) -> dict:
    endpoints = []
    for end, length in enumerate(LENGTH_RANGE_M):
        hw = hardware(economical, end)
        cutting = (
            [150.0, 350.0][end] if economical else pieces * 3.0 + [100.0, 250.0][end]
        )
        freight = [250.0, 600.0][end]
        subtotal = length * usd_m + sum(hw.values()) + cutting + freight
        mass = length * kg_m + HARDWARE_MASS_RANGE_KG[end]
        endpoints.append(
            {
                "length_m": length,
                "extrusions_usd": length * usd_m,
                "hardware_breakdown_usd": hw,
                "cutting_and_additional_machining_usd": cutting,
                "freight_allowance_usd": freight,
                "tax_allowance_usd": subtotal * TAX_RATE,
                "total_usd": subtotal * (1 + TAX_RATE),
                "frame_kg": mass,
                "frame_lb": mass / LB_KG,
            }
        )
    length = sum(count * size for _, count, size in TAKEOFF)
    middle_hw = sum(sum(hardware(economical, end).values()) for end in (0, 1)) / 2
    middle_cut = 250.0 if economical else pieces * 3.0 + 175.0
    return {
        "profile": name,
        "kg_per_m": kg_m,
        "usd_per_m": usd_m,
        "endpoints": endpoints,
        "representative_total_usd": (length * usd_m + middle_hw + middle_cut + 425)
        * (1 + TAX_RATE),
        "representative_frame_lb": (length * kg_m + 15) / LB_KG,
    }


def schematic(path: Path) -> None:
    """Gross centerline illustration; joints/end offsets are not dimensioned."""
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',
        '<rect width="1400" height="900" fill="#f8fafc"/>',
        '<g font-family="DejaVu Sans, sans-serif" fill="#172a3a">',
    ]

    def txt(x, y, value, size=19):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}">{escape(value)}</text>')

    def xy(p):
        x, y, z = p
        return 160 + 150 * x + 80 * y, 750 - 155 * z - 65 * y

    def line(a, b, color, width=3, dash=False):
        x1, y1 = xy(a)
        x2, y2 = xy(b)
        attr = ' stroke-dasharray="8 6"' if dash else ""
        parts.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}"{attr}/>'
        )

    blue, orange, green = "#3178a6", "#cb7133", "#537f5b"
    txt(45, 48, "Aluminum cube: preliminary quantity estimate", 30)
    txt(
        45,
        80,
        "Assumed geometry. No video frames retrieved. No structural or fabrication approval.",
        19,
    )
    n = CUBE_M
    for axis in range(3):
        other = [k for k in range(3) if k != axis]
        for i in (0, n):
            for j in (0, n):
                a = [0.0] * 3
                a[other[0]], a[other[1]] = i, j
                b = a.copy()
                b[axis] = n
                line(a, b, blue, 3)

    theta = math.radians(ANGLE_DEG)
    x0, y0 = (n - BOARD_M) / 2, 0.35

    def board(x, s):
        return x0 + x, y0 + s * math.sin(theta), KICKER_M + s * math.cos(theta)

    corners = [
        board(0, 0),
        board(BOARD_M, 0),
        board(BOARD_M, BOARD_M),
        board(0, BOARD_M),
    ]
    points = " ".join(f"{xy(p)[0]:.2f},{xy(p)[1]:.2f}" for p in corners)
    parts.append(f'<polygon points="{points}" fill="#e8c899" fill-opacity="0.30"/>')
    for i in range(RAILS):
        x = BOARD_M * i / (RAILS - 1)
        line(board(x, 0), board(x, BOARD_M), orange, 4)
        a = board(x, 0)
        line((a[0], a[1], 0), a, orange, 4)
    for s in (0, BOARD_M / 2, BOARD_M):
        line(board(0, s), board(BOARD_M, s), orange, 4)
    line((x0, y0, 0), (x0 + BOARD_M, y0, 0), orange, 4)
    top = board(0, BOARD_M)
    for x in (0, n):
        line((x, 0, top[2]), (x, n, top[2]), blue, 3)
    for z, y in ((0, y0), (top[2], top[1])):
        for left in (True, False):
            a, b = (0, x0) if left else (x0 + BOARD_M, n)
            line((a, y, z), (b, y, z), blue, 2)
    leg = 0.5 / math.sqrt(2)
    # Eight short brace symbols. Plane/size and complete racking detail unselected.
    for x in (0, n):
        for y in (0, n):
            for z in (0, n):
                sign_y, sign_z = (1 if y == 0 else -1), (1 if z == 0 else -1)
                line((x, y + sign_y * leg, z), (x, y, z + sign_z * leg), green, 4)

    txt(55, 815, "Outer cube assumed: 2.6 m each way (8.53 ft).")
    txt(
        55,
        846,
        "Board: 8 ft wide × 8 ft sloped length; 40° from vertical; 277 mm kicker.",
    )
    txt(855, 157, "Representative takeoff", 25)
    txt(855, 195, "Outer cube: 12 members / 31.2 m")
    txt(855, 231, "Main backing: 5 rails / 12.2 m")
    txt(855, 267, "Panel crosspieces: 3 rows / 6.7 m")
    txt(855, 303, "Kicker frame: about 5.9 m")
    txt(855, 339, "Top side ties: 2 members / 5.2 m")
    txt(855, 375, "Brace/standoff allowance: 4.6 m")
    txt(855, 418, "Total: 56 pieces / 65.8 m", 24)
    txt(855, 465, "Price/weight range uses 55–70 m.")
    txt(855, 503, "Blue: cube and frame ties")
    txt(855, 535, "Orange: panel backing and kicker")
    txt(855, 567, "Green: bracing allowance")
    txt(855, 620, "Connector choices and quantities")
    txt(855, 650, "are allowances, not tested details.")
    txt(855, 689, "Hold/LED clearance, panel fasteners,")
    txt(855, 719, "racking and floor stability remain open.")
    parts.append("</g></svg>\n")
    path.write_text("\n".join(parts))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    length = sum(count * size for _, count, size in TAKEOFF)
    pieces = sum(count for _, count, _ in TAKEOFF)
    profiles = [
        estimate(
            "TNUTZ EX-1515, 38.1 mm, assumed price scaling",
            2.140,
            0.55 / IN_M,
            True,
            pieces,
        ),
        estimate("80/20 40-4040-Lite", 0.0998 * LB_KG / IN_M, 37.0, False, pieces),
        estimate("80/20 40-4040", 0.1321 * LB_KG / IN_M, 44.1, False, pieces),
    ]
    # Nominal 3/4 inch is used for this weight allowance; actual thickness/mass unknown.
    volume = (BOARD_M**2 + BOARD_M * KICKER_M) * 0.01905
    report = {
        "scope": "owner-directed aluminum cube concept; quantity, price and mass estimate only",
        "lookup_date": "2026-10-05",
        "python_version": platform.python_version(),
        "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sources": SOURCES,
        "takeoff": [
            {
                "description": label,
                "pieces": count,
                "nominal_piece_m": size,
                "total_m": count * size,
            }
            for label, count, size in TAKEOFF
        ],
        "representative_pieces": pieces,
        "representative_length_m": length,
        "length_range_m": LENGTH_RANGE_M,
        "range_note": "55–70 m is a planning sensitivity, not observed lower/upper bounds or a validated cut list",
        "tax_assumption": TAX_RATE,
        "profiles": profiles,
        "sus_4040_frame_mass_lb_range": [
            (size * 1.65 + HARDWARE_MASS_RANGE_KG[i]) / LB_KG
            for i, size in enumerate(LENGTH_RANGE_M)
        ],
        "sus_4040_representative_frame_lb": (length * 1.65 + 15) / LB_KG,
        "sus_4040_member_2_6m_lb": CUBE_M * 1.65 / LB_KG,
        "plywood_volume_m3_nominal_3_4in": volume,
        "plywood_density_assumption_kg_m3": [450, 650],
        "plywood_mass_lb_range": [volume * density / LB_KG for density in (450, 650)],
        "upgrade_five_sloped_rails": {
            "length_m": RAILS * BOARD_M,
            "sus_4040_to_4080_extra_lb": RAILS * BOARD_M * (2.8 - 1.65) / LB_KG,
            "8020_heavy_4040_to_4080_extra_lb": RAILS
            * BOARD_M
            * (0.2317 - 0.1321)
            / IN_M,
            "8020_heavy_4040_to_4080_extra_usd_with_tax_and_cut_difference": (
                RAILS * BOARD_M * (82.1 - 44.1) + RAILS * (3.79 - 3.00)
            )
            * (1 + TAX_RATE),
        },
        "limits": [
            "No video screenshots or observed member/connector count",
            "Cube dimensions assumed; room dimensions pending",
            "No configured TNUTZ/SUS quote, verified freight or tax",
            "SUS mass must not be paired with TNUTZ/80/20 price as a quoted product",
            "No structural capacities, new load demands, solves, CAD or candidate adoption",
            "Cost excludes owned plywood/holds/LEDs, landing pads, labor/tools and design services",
            "Frame weight excludes plywood/holds/LEDs/pads; hardware mass is an allowance",
            "Repeated assembly sequence, long-member transport and joint access not yet checked",
            "Shared members and further bracing can change the inventory; no acceptance transfers from wood",
        ],
    }
    (OUT / "estimate.json").write_text(json.dumps(report, indent=2) + "\n")
    schematic(OUT / "assumed-cube.svg")
    print(
        json.dumps(
            {
                "length_m": length,
                "pieces": pieces,
                "profiles": [
                    {
                        "profile": p["profile"],
                        "total_usd": [e["total_usd"] for e in p["endpoints"]],
                        "frame_lb": [e["frame_lb"] for e in p["endpoints"]],
                        "representative_usd": p["representative_total_usd"],
                    }
                    for p in profiles
                ],
                "sus_lb": report["sus_4040_frame_mass_lb_range"],
                "plywood_lb": report["plywood_mass_lb_range"],
                "upgrade": report["upgrade_five_sloped_rails"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
