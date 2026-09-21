"""Owner-review geometry for the two outer header/post exception duties."""

from scripts import owner_layout_outer_header_pair as layout


def test_outer_header_pair_is_same_side_and_keeps_original_frame():
    result = layout.screen()
    assert result["stations"] == [
        "clip_timber_header_outer_left",
        "clip_timber_header_outer_right",
    ]
    assert result["candidate_blocks"] == 2
    assert result["candidate_bolts"] == 8
    assert result["source_panel_kicker_axes"] == 66
    assert result["source_frame_bolts"] == 12
    assert result["block_section_mm"] == [139.7, 88.9, 139.7]
    assert result["block_y_bounds_mm"] == [-150.3, -61.4]
    assert result["block_z_bounds_mm"] == [99.2, 238.9]
    assert all(row["same_side_as_original_clip"] for row in result["pairs"].values())
    assert all(row["post_contact_area_mm2"] > 0 for row in result["pairs"].values())
    assert all(row["header_contact_area_mm2"] > 0 for row in result["pairs"].values())
    assert all(row["complete_bores"] for row in result["pairs"].values())
    assert all(not row["unrelated_timber_hits_mm3"] for row in result["pairs"].values())
    assert result["decision"] == "GEOMETRY_TRIAL_ONLY"
    assert result["hold_tnut_led_clearance_checked"] is False
    assert result["installed_stack_and_tool_checked"] is False
    assert result["legacy_angle_removed_from_candidate"] is False
    assert result["drilling_released"] is False
    assert result["structural_released"] is False
