"""The bounded side-cleat trial preserves fixed geometry and exposes its gate."""

from scripts.simple_center_header_post_side_cleat_probe import probe


def test_one_side_cleat_header_post_pose():
    result = probe()
    assert result["header_bounds_mm"] == [-1219.2, 1219.2, -175.7, -36.0, 238.9, 277.0]
    assert result["post_bounds_mm"] == [88.75, 177.65, -175.7, -86.8, 0.0, 238.9]
    assert result["cleat_bounds_mm"] == [177.65, 266.55, -175.7, -86.8, 110.0, 238.9]
    assert result["bolt_axes"] == {
        "post_cleat_yz_mm": [-150.0, 160.0],
        "cleat_header_xy_mm": [222.1, -130.0],
    }
    assert result["bolt_spans_mm"] == {
        "post_cleat_x": [88.75, 266.55],
        "cleat_header_z": [110, 277],
    }
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["inherited_pose_clear"] is True
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert set(result["center_kicker_screw_receiver_fraction"].values()) == {1.0}
    assert len(result["header_screw_receiver_fraction"]) == 10
    assert set(result["header_screw_receiver_fraction"].values()) == {0.7125}
    assert result["cleat_wood_overlaps_mm3"] == {}
    assert result["bore_received_fraction"] == {"post_cleat": 1.0, "cleat_header": 1.0}
    for key in (
        "bore_other_wood_hits_mm3",
        "bore_fixed_screw_hits_mm3",
        "bore_pair_hits_mm3",
    ):
        assert result[key] == {}
    assert set(result["washer_bearing_fraction"].values()) == {1.0}
    for key in (
        "external_hardware_wood_hits_mm3",
        "tool_wood_hits_mm3",
        "external_hardware_fixed_screw_hits_mm3",
        "tool_fixed_screw_hits_mm3",
    ):
        assert all(not hits for hits in result[key].values())
    assert result["nut_or_tool_on_installed_kicker_front"] is False
    assert result["post_y_edges_mm"] == [25.7, 63.2]
    assert result["cleat_post_bolt_z_ends_mm"] == [50.0, 78.9]
    assert result["cleat_header_bolt_x_edges_mm"] == [44.45, 44.45]
    assert result["header_bolt_y_edges_mm"] == [45.7, 94.0]
    assert result["header_bolt_x_grain_ends_mm"] == [1441.3, 997.1]
    assert result["new_crossed_bore_axis_spacing_mm"] == 20.0
    assert result["new_crossed_bore_wall_gap_mm"] == 12.7
    assert result["inherited_post_high_crossed_axis_spacing_mm"] == 30.0
    assert result["inherited_post_high_crossed_bore_wall_gap_mm"] == 22.7
    assert result["inherited_post_high_group_and_splitting_qualified"] is False
    assert result["conditional_4d_mm"] == 25.4
    assert result["conditional_7d_mm"] == 44.45
    length = result["vertical_bolt_length_screen"]
    assert length["candidates"]["7_in"]["tip_past_nut_mm"] == 1.148
    assert length["seven_in_short_of_provisional_0_05in_full_thread_mm"] == 0.122
    assert length["candidates"]["8_in"]["tip_past_nut_mm"] == 26.548
    assert length["candidates"]["8_in"]["top_projection_mm"] == 34.549
    assert length["candidates"]["8_in"]["beyond_original_20mm_tool_mm"] == 14.549
    assert length["nut_bearing_plane_under_head_in"] == 6.7048
    assert length["illustrative_eight_in_thread_start_past_bearing_plane_in"] == 0.2952
    for candidate in length["candidates"].values():
        for key in (
            "top_shaft_wood_hits_mm3",
            "top_shaft_fixed_screw_hits_mm3",
            "top_washer_nut_wood_hits_mm3",
            "extended_top_tool_wood_hits_mm3",
            "extended_top_tool_fixed_screw_hits_mm3",
        ):
            assert candidate[key] == {}
    assert result["vertical_bolt_stack_selected"] is False
    assert result["nominal_geometry"] == "accepted"
    assert "end grain" in result["joint_mechanics_gate"]
    assert result["fabrication_ready"] is False
    assert result["rating_or_drilling_release"] is False
