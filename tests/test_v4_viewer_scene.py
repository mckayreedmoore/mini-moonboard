"""The development overlay must follow the maintained PB01/PB02 poses."""

import json
from pathlib import Path

from scripts.export_v4_viewer_scene import build_scene


def test_v4_overlay_uses_current_short_blocks_and_ten_center_axes():
    scene = build_scene()
    assert scene["status"] == "partial_development_visualization"
    assert scene["baseline"] == "compact-floor-flush-kerf-right"
    assert scene["fixed_panel_kicker_screw_axes"] == 66
    blocks = {part["name"]: part for part in scene["boxes"]}
    assert blocks["PB01 short rail block"]["size_mm"] == [139.7, 57.15, 152.4]
    assert blocks["PB02 post/header block"]["size_mm"] == [88.9, 88.9, 143.9]
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
