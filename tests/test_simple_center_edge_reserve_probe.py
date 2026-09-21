"""PB-02 one-pose edge-reserve geometry regression."""

from scripts.simple_center_edge_reserve_probe import probe


def test_outward_four_by_four_and_wider_single_cleat():
    trial = probe()
    assert trial["post_bounds_mm"] == [88.75, 177.65, -175.7, -86.8, 0, 238.9]
    assert trial["cleat_bounds_mm"]["rear"] == [89.05, 177.95, -213.8, -175.7, 0, 460]
    assert trial["post_bolt_x_mm"] == 140.0
    assert trial["cleat_link_x_mm"] == 114.45
    assert trial["actual_edge_end_mm"]["post_bolts_x_edges"] == [51.25, 37.65]
    assert trial["actual_edge_end_mm"]["rear_cleat_post_bolts_x_edges"] == [
        50.95,
        37.95,
    ]
    assert trial["actual_edge_end_mm"]["cleat_link_x_edges"] == [25.4, 63.5]
    assert trial["minimum_post_bolt_x_reserve_mm"] == 12.25
    assert trial["post_to_backer_x_gap_mm"] == 0
    assert trial["post_to_backer_x_face_contact_mm2"] == 9102.09
    assert trial["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert trial["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert set(trial["center_kicker_screw_receiver_fraction"].values()) == {1.0}
    assert trial["solid_overlaps_mm3"] == {}
    assert trial["fixed_screw_hits_mm3"] == {}
    assert trial["bore_unintended_wood_hits_mm3"] == {}
    assert trial["bore_pair_hits_mm3"] == {}
    assert set(trial["bore_received_fraction"].values()) == {1.0}
    assert set(trial["washer_bearing_fraction"].values()) == {1.0}
    assert trial["no_pocket_front_short_tool_clear"] is True
    assert trial["trial_20mm_radius_tool_wood_hits_mm3"] == {}
    assert trial["post_to_rear_cleat_contact_mm2"] > 15000
    assert trial["removed_legacy_stations"] == [
        "clip_split_base_center_right",
        "clip_split_header_center_right",
    ]
