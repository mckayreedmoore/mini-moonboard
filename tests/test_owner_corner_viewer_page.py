"""The published viewer binds the full owner scene to a pinned export."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_owner_corner_viewer_has_pinned_full_scene():
    scene_bytes = (ROOT / "site/owner-corner-layout-scene.json").read_bytes()
    scene = json.loads(scene_bytes)
    html = (ROOT / "site/index.html").read_text()
    assert scene["schema"] == "owner_corner_layout_scene/v1"
    assert scene["inventory"]["replaced_angle_duties"] == 24
    assert scene["inventory"]["removed_structural_sds"] == 144
    assert scene["inventory"]["fixed_panel_kicker_screw_axes"] == 66
    assert scene["inventory"]["retained_frame_bolt_axes"] == 12
    assert len(scene["hidden_baseline_visual_names"]) == 170
    assert f"'{hashlib.sha256(scene_bytes).hexdigest()}'" in html
    assert "'owner-corner-layout'" in html
    assert "fetch('owner-corner-layout-scene.json')" in html
    assert "validateOwnerCornerScene(JSON.parse(raw), ownerConceptHiddenNames)" in html
    assert "renderOwnerCornerScene(THREE, data, climberView, meshes)" in html
    assert "Complete layout concept — not structurally qualified or build-ready" in html
    assert scene["drilling_released"] is False
    assert scene["fabrication_released"] is False
    assert scene["structural_released"] is False
