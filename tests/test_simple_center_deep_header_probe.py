"""The single deep-header pose must expose its geometric stops."""

from scripts.simple_center_deep_header_probe import probe


def test_deep_header_pose():
    trial = probe()
    assert trial["header_bounds_mm"] == [-1219.2, 1219.2, -175.7, -61.4, 188.1, 277.0]
    assert trial["shifted_post_bounds_mm"] == [88.75, 177.65, -175.7, -86.8, 0.0, 188.1]
    assert trial["post_bolt_z_mm"] == [80.0, 140.0]
    assert trial["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert trial["conditional_reversible_z_edges_pass"] is True
    assert trial["header_z_edge_distances_mm"] == [44.45, 44.45]
    assert trial["front_nut_tool_clear"] is True
    assert trial["header_bore_received_fraction_by_member"] == {
        "rear_cleat": 0.25,
        "base_header": 0.75,
    }
    assert trial["header_bore_unintended_wood_hits_mm3"] == {}
    assert trial["new_bore_pair_hits_mm3"] == {}
    assert trial["new_bore_fixed_screw_hits_mm3"] == {}
    assert trial["washer_bearing_fraction"] == {"rear": 1.0, "front": 1.0}
    assert trial["inner_kicker_edges_supported"] == {"left": False, "right": False}
    assert trial["header_screw_receiver_fraction"] == {
        name: 0.3125 for name in trial["header_screw_receiver_fraction"]
    }
    assert len(trial["header_screw_receiver_fraction"]) == 10
    assert set(trial["original_header_screw_receiver_fraction"].values()) == {0.7125}
    assert trial["header_new_overlap_mm3"]["base_post_center_left"] > 0
    assert trial["header_new_overlap_mm3"]["backer"] > 0
    assert trial["header_new_overlap_mm3"]["base_post_outer_left"] > 0
    assert trial["header_new_overlap_mm3"]["base_post_outer_right"] > 0
    assert trial["shifted_post_unintended_wood_overlap_mm3"] == {}
    assert trial["relocated_post_bore_received_fraction"] == {
        "post_low": 1.0,
        "post_high": 1.0,
    }
    assert trial["relocated_post_bore_unintended_wood_hits_mm3"] == {
        "post_low": {},
        "post_high": {},
    }
    assert trial["center_kicker_screw_receiver_fraction"] == {
        name: 1.0 for name in trial["center_kicker_screw_receiver_fraction"]
    }
    assert len(trial["center_kicker_screw_receiver_fraction"]) == 4
    assert trial["accepted_geometry"] is False
