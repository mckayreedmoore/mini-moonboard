"""The owner viewer must show one full, explicitly unqualified layout."""

from scripts.export_owner_corner_scene import build_scene


def test_complete_layout_scene_inventory_and_release_boundary():
    scene = build_scene()
    assert scene["schema"] == "owner_corner_layout_scene/v1"
    assert scene["status"] == "complete_layout_concept_not_qualified"
    assert scene["inventory"] == {
        "replaced_angle_duties": 24,
        "removed_structural_sds": 144,
        "corner_blocks": 24,
        "moved_center_posts": 2,
        "kicker_screw_backers": 2,
        "new_diagnostic_bolt_axes": 92,
        "fixed_panel_kicker_screw_axes": 66,
        "retained_frame_bolt_axes": 12,
    }
    assert len(scene["hidden_baseline_visual_names"]) == 170
    assert len(scene["solids"]) == 28
    assert all(row["mesh"]["triangles"] for row in scene["solids"])
    assert len(scene["diagnostic_bolt_axes"]) == 92
    assert all(row["diagnostic_only"] for row in scene["diagnostic_bolt_axes"])
    assert "cross_family_hits_mm3" in scene["assembly_diagnostics"]
    assert scene["layout_clearance_approved"] is False
    assert scene["drilling_released"] is False
    assert scene["fabrication_released"] is False
    assert scene["structural_released"] is False
