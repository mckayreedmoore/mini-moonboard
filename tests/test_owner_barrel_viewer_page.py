"""The comparison viewer must use the kerf-right frame and no-release overlay."""

import hashlib
from pathlib import Path


def test_barrel_viewer_is_selectable_and_keeps_baseline_parts():
    page = (Path(__file__).resolve().parents[1] / "site/index.html").read_text()
    assert "'owner-barrel-layout'" in page
    assert "owner-barrel-layout-scene.json" in page
    assert "validateOwnerBarrelScene" in page
    assert "renderOwnerBarrelScene" in page
    assert "['owner-corner-layout', 'owner-barrel-layout'].includes(model)" in page
    assert "No drilling or fabrication release." in page
    assert (
        "part.fabrication.owner_corner_overlay || part.fabrication.owner_barrel_overlay"
        in page
    )
    assert "event.altKey && model === 'owner-barrel-layout'" in page
    assert (
        "rejectOwnerCornerBaseline?.(new Error(`Baseline mesh ${part.name} failed`))"
        in page
    )
    assert "incomplete baseline context with old joints hidden" in page
    scene = (
        Path(__file__).resolve().parents[1] / "site/owner-barrel-layout-scene.json"
    ).read_bytes()
    assert hashlib.sha256(scene).hexdigest() in page
