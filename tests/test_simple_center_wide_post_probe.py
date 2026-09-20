"""PB-02 solid-stock substitution geometry regression."""

from scripts.simple_center_wide_post_probe import probe


def test_solid_four_by_four_preserves_nominal_path_with_zero_edge_reserve():
    result = probe()
    square = result["four_by_four"]
    wider = result["four_by_six"]
    assert square["post_bounds_mm"] == [88.75, 177.65, -175.7, -86.8, 0, 238.9]
    assert wider["post_bounds_mm"] == [88.75, 177.65, -175.7, -36.0, 0, 238.9]
    for trial in result.values():
        assert trial["fixed_axes"] == {"panel": 48, "kicker": 18}
        assert trial["inner_kicker_edges_supported"] == {"left": True, "right": True}
        assert set(trial["center_kicker_screw_receiver_fraction"].values()) == {1.0}
        assert trial["solid_overlaps_mm3"] == {}
        assert trial["fixed_screw_hits_mm3"] == {}
        assert trial["bore_unintended_wood_hits_mm3"] == {}
        assert trial["bore_pair_hits_mm3"] == {}
        assert set(trial["bore_received_fraction"].values()) == {1.0}
        assert set(trial["washer_bearing_fraction"].values()) == {1.0}
        assert trial["post_to_rear_cleat_contact_mm2"] > 12000
        assert trial["removed_legacy_stations"] == [
            "clip_split_base_center_right",
            "clip_split_header_center_right",
        ]
        assert trial["legacy_clip_wood_hits_mm3"]
        assert trial["legacy_clip_screw_wood_hits_mm3"]
        assert trial["actual_edge_end_mm"]["post_bolts_x_edges"] == [25.7, 63.2]
        assert trial["actual_edge_end_mm"]["rear_cleat_post_bolts_x_edges"] == [
            25.4,
            25.4,
        ]
        assert trial["conditional_4d_mm"] == 25.4
    assert square["post_to_backer_contact_y_mm"] == 38.1
    assert square["post_front_to_kicker_back_gap_mm"] == 50.8
    assert square["no_pocket_front_short_tool_clear"] is True
    assert square["trial_20mm_radius_tool_wood_hits_mm3"] == {}
    assert wider["post_front_to_kicker_back_gap_mm"] == 0.0
    assert wider["no_pocket_front_short_tool_clear"] is False
    assert set(wider["trial_20mm_radius_tool_wood_hits_mm3"]) == {
        "post_front_low/kicker_right",
        "post_front_high/kicker_right",
    }
