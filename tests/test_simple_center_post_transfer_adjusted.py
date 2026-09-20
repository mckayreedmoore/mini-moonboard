"""One bounded geometry attempt for the shifted right-post transfer."""

from scripts.simple_center_post_transfer_adjusted import probe


def test_adjusted_transfer_reports_actual_margins_and_limits():
    result = probe()
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["right_post_shift_mm"] == 37.8
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert result["unintended_solid_overlaps_mm3"] == {}
    assert result["fixed_screw_hits_mm3"] == {}
    assert result["bore_unintended_wood_hits_mm3"] == {}
    assert result["bore_pair_hits_mm3"] == {}
    assert all(v == 1.0 for v in result["bore_received_fraction"].values())
    assert result["removed_legacy_stations"] == [
        "clip_split_base_center_right",
        "clip_split_header_center_right",
    ]
    assert result["legacy_clip_wood_hits_mm3"]
    assert result["legacy_clip_screw_wood_hits_mm3"]
    assert result["actual_edge_end_mm"]["post_bolts_x_edges"] == [19.05, 19.05]
    assert result["actual_edge_end_mm"]["rear_cleat_post_bolts_x_edges"] == [
        18.75,
        32.05,
    ]
    assert result["actual_edge_end_mm"]["cleat_link_x_edges"] == [25.4, 25.4]
    assert result["actual_edge_end_mm"]["upright_bolt_side_y_edges"] == [28.4, 28.4]
    assert result["actual_edge_end_mm"]["upright_bolt_side_z_ends"] == [73.0, 110.0]
    assert result["conditional_4d_mm"] == 25.4
    assert result["conditional_post_x_edge_shortfall_mm"] == 6.35
    assert result["upright_washer_bearing_fraction"] == 1.0
    assert all(v == 1.0 for v in result["washer_bearing_fraction"].values())
    assert set(result["trial_20mm_radius_tool_wood_hits_mm3"]) == {
        "post_front_low/kicker_right",
        "post_front_high/kicker_right",
    }
    assert result["conditional_geometry_pass"] is False
