"""Whole-timber outer-header trials must keep both rows and fixed receivers."""

from scripts.owner_barrel_outer_header_wide_post_probe import search


def test_bounded_wide_post_screen_has_no_clear_fixed_axis_pose():
    result = search()
    assert result["schema"] == "owner_barrel_outer_header_wide_post_probe/v1"
    assert result["width_option"] == "kerf-right"
    assert result["fixed_axes"] == {"panel_screws": 66, "frame_bolts": 12}
    assert result["candidate_count"] == 12
    assert result["geometry_clear_poses"] == []
    assert not result["viewer_changed"]
    assert not result["drilling_released"]
    assert not result["fabrication_released"]
    assert not result["structural_released"]

    for side in ("left", "right"):
        rows = {
            (row["section"], row["shift_inward_mm"]): row
            for row in result["candidates"]
            if row["side"] == side
        }
        assert len(rows) == 6
        rotated = rows[("2x6_rotated", 0.0)]
        assert rotated["nominal_section_mm"] == [139.7, 38.1]
        assert rotated["row_y_mm"] == [-135.0, -75.0]
        assert rotated["row_spacing_mm"] == 60.0
        assert rotated["minimum_y_depth_for_two_20mm_rows_mm"] == 80.0
        assert rotated["row_edge_margins_y_mm"] == [-10.1, -11.8]
        assert rotated["fixed_kicker_axis_post_overlap_mm"] == [0.0, 0.0]
        assert rotated["fixed_front_axis_post_y_margin_mm"][1] < 0
        assert "20mm_y_support_both_rows" in rotated["failed_gates"]
        assert "fixed_kicker_centerlines_enter_post" in rotated["failed_gates"]

        four_by_six = rows[("4x6", 0.0)]
        assert four_by_six["nominal_section_mm"] == [88.9, 139.7]
        assert four_by_six["minimum_x_width_for_tool_and_fixed_screw_mm"] == 89.85
        assert four_by_six["tool_center_corridor_width_mm"] == 0.0
        assert four_by_six["outer_header"] is None
        assert "20mm_x_corridor" in four_by_six["failed_gates"]

        six_by_six = rows[("6x6", 0.0)]
        assert six_by_six["nominal_section_mm"] == [139.7, 139.7]
        assert six_by_six["tool_center_corridor_width_mm"] == 30.8
        assert six_by_six["row_edge_margins_y_mm"] == [40.7, 39.0]
        assert six_by_six["fixed_kicker_axis_post_overlap_mm"] == [32.54375] * 2
        assert six_by_six["fixed_front_axis_post_overlap_mm"] == [40.132] * 2
        assert (
            six_by_six["unexpected_protected_hits_mm3"]["tnuts"][
                f"hold_tnut_kicker_{1 if side == 'left' else 10}"
            ]
            == 804.105091
        )
        assert six_by_six["outer_header"]["shaft_side_rim_hits_mm3"] == [0.0, 0.0]
        assert six_by_six["outer_header"]["access_side_rim_hits_mm3"] == [0.0, 0.0]
        assert "protected_inventory" in six_by_six["outer_header"]["failed_gates"]
        assert "new_post_protected" in six_by_six["failed_gates"]


def test_modest_shift_does_not_rescue_any_section():
    result = search()
    shifted = [row for row in result["candidates"] if row["shift_inward_mm"] == 10.0]
    assert len(shifted) == 6
    assert all(not row["nominal_geometry_clear"] for row in shifted)
    for row in shifted:
        if row["section"] == "2x6_rotated":
            assert not row["both_20mm_access_rows_within_post_y"]
        elif row["section"] == "4x6":
            assert row["tool_center_corridor_width_mm"] == 0.0
        else:
            assert row["section"] == "6x6"
            assert "new_post_protected" in row["failed_gates"]
