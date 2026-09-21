"""The development overlay must follow the maintained PB01/PB02 poses."""

import json
from pathlib import Path

import pytest

from scripts.export_v4_viewer_scene import build_scene


def test_v4_overlay_uses_current_short_blocks_and_ten_center_axes():
    scene = build_scene()
    assert scene["status"] == "partial_development_visualization"
    assert scene["baseline"] == "compact-floor-flush-kerf-right"
    assert scene["fixed_panel_kicker_screw_axes"] == 66
    assert scene["pb02_variant_id"] == "ligament_priority"
    assert scene["pb02_source_fingerprint"] == (
        "4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb"
    )
    blocks = {part["name"]: part for part in scene["boxes"]}
    assert blocks["PB01 short rail block"]["size_mm"] == [139.7, 57.15, 152.4]
    assert blocks["PB02 post/header block"]["size_mm"] == [88.9, 88.9, 143.9]
    assert blocks["PB02 revised upright-side cleat"]["size_mm"] == pytest.approx(
        [88.9, 61.6, 183]
    )
    assert blocks["PB02 revised header-side cleat"]["origin_mm"][2] == 277
    assert blocks["PB02 revised header-side cleat"]["size_mm"][2] == 67
    assert blocks["PB02 shifted right center post"]["origin_mm"] == [
        88.75,
        -175.7,
        0,
    ]
    rear_cleat = blocks["PB02 rear return block"]
    assert rear_cleat["origin_mm"] == pytest.approx([89.05, -213.8, 5])
    assert rear_cleat["size_mm"] == pytest.approx([88.9, 38.1, 455])
    assert rear_cleat["origin_mm"][2] + rear_cleat["size_mm"][2] == 460
    assert blocks["PB02 kicker backer"]["size_mm"] == [139.7, 88.9, 238.9]
    assert len([axis for axis in scene["axes"] if axis["station"] == "PB01"]) == 4
    assert len([axis for axis in scene["axes"] if axis["station"] == "PB02"]) == 10
    assert {axis["name"] for axis in scene["axes"] if axis["station"] == "PB02"} == {
        "post_cleat_1",
        "post_cleat_2",
        "cleat_header_1",
        "cleat_header_2",
        "header_cleat",
        "cleat_principal",
        "post_low",
        "post_high",
        "upright",
        "cleat_link",
    }
    axes = {axis["name"]: axis for axis in scene["axes"] if axis["station"] == "PB02"}
    assert axes["post_cleat_2"]["start_mm"][2] == 176
    assert axes["post_high"]["start_mm"][2] == 202
    assert axes["cleat_header_1"]["start_mm"][:2] == [208.35, -130.5]
    assert axes["cleat_header_2"]["start_mm"][:2] == [236.0, -117.5]
    assert axes["cleat_link"]["start_mm"][2] == 328.5
    assert axes["upright"]["start_mm"][1:] == [-144.5, 356]
    assert scene["fabrication_released"] is False


def test_viewer_scene_artifact_matches_producer():
    root = Path(__file__).resolve().parents[1]
    assert (
        json.loads((root / "site/v4-diagnostic-scene.json").read_text())
        == build_scene()
    )
    html = (root / "site/index.html").read_text()
    assert "DEVELOPMENT V4 · PB01/PB02 partial 3D scene" in html
    assert "fetch('v4-diagnostic-scene.json')" in html
    assert "data.pb02_variant_id !== 'ligament_priority'" in html
