"""Current PB02 BOM/cut-list record bound to the active viewer geometry."""

import json
from pathlib import Path

from scripts.simple_center_pb02_current_bom import report

ROOT = Path(__file__).resolve().parents[1]


def test_current_inventory_matches_active_ten_bolt_geometry():
    result = report()

    assert result["geometry_binding"] == {
        "baseline": "compact-floor-flush-kerf-right",
        "pb02_variant_id": "ligament_priority",
        "pb02_source_fingerprint": (
            "46da45226acf9660643cb88c76e80680a262efb38f0142d3156925cd2089a4e2"
        ),
        "pb02_bolt_axes": 10,
        "fixed_panel_kicker_screw_axes": 66,
    }
    assert result["hardware"]["bolts_by_length_in"] == {"5": 3, "6": 3, "8": 4}
    assert result["hardware"]["bolt_count"] == 10
    assert result["hardware"]["nut_count"] == 10
    assert result["hardware"]["washer_count"] == 20


def test_current_piece_dimensions_are_bound_to_viewer_boxes():
    pieces = {row["id"]: row for row in report()["pieces"]}
    assert {name: row["dimensions_mm"] for name, row in pieces.items()} == {
        "shifted_post": [88.9, 88.9, 238.9],
        "post_header_block": [88.9, 88.9, 143.9],
        "upright_side_cleat": [88.9, 61.6, 183.0],
        "header_side_cleat": [70.95, 145.0, 67.0],
        "rear_cleat": [88.9, 38.1, 460.0],
        "kicker_backer": [139.7, 88.9, 238.9],
    }
    assert all(row["matches_active_viewer"] for row in pieces.values())


def test_current_cost_and_stock_arithmetic_are_reproducible():
    result = report()
    assert result["hardware"]["cost_usd"] == {
        "bolts": "7.75",
        "allocated": "11.88",
        "first_checkout_excluding_lumber": "13.69",
    }

    stock = result["stock"]
    assert stock["4x4_8ft"] == {
        "cut_lengths_mm": [238.9, 183.0, 143.9],
        "crosscut_kerf_mm": 3.2,
        "consumed_mm": 575.4,
        "remainder_mm": 1863.0,
    }
    assert stock["2x4_8ft"] == {
        "cut_lengths_mm": [460.0],
        "crosscut_kerf_mm": 3.2,
        "consumed_mm": 463.2,
        "remainder_mm": 1975.2,
    }
    assert stock["4x6_8ft"] == {
        "cut_lengths_mm": [238.9, 145.0],
        "crosscut_kerf_mm": 3.2,
        "consumed_mm": 390.3,
        "remainder_mm": 2048.1,
    }
    assert stock["illustrative_rip_offcuts_mm"] == {
        "upright_side_from_4x4": 24.1,
        "header_side_from_4x6_first_rip": 14.75,
        "header_side_from_4x6_second_rip": 69.5,
    }


def test_record_and_ledger_keep_all_release_gates_closed():
    result = report()
    assert result["release"] == {
        "procurement": False,
        "drilling": False,
        "fabrication": False,
        "structural": False,
    }

    ledger = json.loads((ROOT / "docs/bolted-candidate-task-ledger.json").read_text())
    latest = ledger["latest_center_pb02_current_bom"]
    assert "ten bolts" in latest
    assert "66 fixed" in latest
    assert "No purchase, drilling, fabrication or structural release" in latest

    document = (
        ROOT / "docs/bolted-candidate-prototypes/simple-center-pb02-current-bom.md"
    ).read_text()
    assert "Current PB02 BOM and cut-list" in document
    assert "Historical eight-bolt" in document
    assert "No purchase, drilling, fabrication, or structural release" in document
