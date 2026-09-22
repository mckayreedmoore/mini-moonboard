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
    assert "rim-first removal is required but not physically verified" in page
    assert "cut-derived header" in page
    assert (
        "eight rim-receiver screws, two leg/rim bolts and ten trial rim-joint bolts"
        in page
    )
    assert "green wood pieces are kicker-screw backers, not joint blocks" in page
    barrel_documents = page.split("const ownerBarrelDocuments = [", 1)[1].split(
        "];", 1
    )[0]
    assert "owner-barrel-outer-header-cut-integrity.md" in barrel_documents
    assert "owner-barrel-mvp-preliminary.md" in barrel_documents
    assert "owner-barrel-mvp-retail-cost.md" in barrel_documents
    assert "owner-barrel-retail-thread-evidence.md" in barrel_documents
    assert "no structural release" in barrel_documents
    assert "no purchase release" in barrel_documents
    assert "owner-barrel-rim-withdrawal-hardware-probe.md" in barrel_documents
    assert "owner-barrel-native-connector-inventory.md" in barrel_documents
    assert "Six outer-rail joints show nominal 6 in bolts" in page
    assert "owner-barrel-outer-rail-setback-probe.md" in barrel_documents
    assert "owner-barrel-backer-layout.md" in barrel_documents
    assert "owner-corner-viewer.md" not in barrel_documents
    overlay = (
        Path(__file__).resolve().parents[1] / "site/owner-barrel-overlay.mjs"
    ).read_text()
    assert "wireframe: counterbore" in overlay
    assert "derived_cut_header" in overlay
    assert "conditional_outer_header_recess_envelopes" in overlay
    assert (
        "part.fabrication.owner_corner_overlay || part.fabrication.owner_barrel_overlay"
        in page
    )
    assert "event.altKey && model === 'owner-barrel-layout'" in page
    assert (
        "rejectOwnerConceptBaseline?.(new Error(`Baseline mesh ${part.name} failed`))"
        in page
    )
    assert "incomplete baseline context with old joints hidden" in page
    scene = (
        Path(__file__).resolve().parents[1] / "site/owner-barrel-layout-scene.json"
    ).read_bytes()
    assert hashlib.sha256(scene).hexdigest() in page
