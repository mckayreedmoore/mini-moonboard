"""One bounded rectangular-cleat header/principal geometry screen."""

from scripts.simple_center_header_principal_cleat_probe import probe


def test_opposite_side_cleat_joint_geometry():
    result = probe()
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["inherited_pose_clear"] is True
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert set(result["center_kicker_screw_receiver_fraction"]) == {
        "round_kicker_left_center_1",
        "round_kicker_left_center_2",
        "round_kicker_right_center_1",
        "round_kicker_right_center_2",
    }
    assert set(result["center_kicker_screw_receiver_fraction"].values()) == {1.0}
    assert result["new_wood_overlaps_mm3"] == {}
    assert result["fixed_screw_hits_mm3"] == {}
    assert result["unintended_bore_wood_hits_mm3"] == {}
    assert result["bore_pair_hits_mm3"] == {}
    assert result["washer_bearing_fraction"] == {
        "header_bottom": 1.0,
        "cleat_top": 1.0,
        "cleat_left": 1.0,
        "principal_right": 1.0,
    }
    assert result["tool_wood_hits_mm3"] == {}
    assert result["tool_panel_kicker_hits_mm3"] == {}
    assert result["bore_received_fraction"] == {
        "header_cleat": 1.0,
        "cleat_principal": 1.0,
    }
    assert result["face_center_distances_mm"]["vertical_cleat_x_edges"] == [
        25.475,
        25.475,
    ]
    assert result["face_center_distances_mm"]["vertical_cleat_y_edges"][0] == 25.7
    assert result["conditional_nds_2024_4d_mm"] == 25.4
    assert result["nominal_geometry"] == "accepted"
    assert result["fabrication_ready"] is False
    assert "One bolt per interface" in result["strength_mechanism_gate"]
    assert result["rating_or_drilling_release"] is False
