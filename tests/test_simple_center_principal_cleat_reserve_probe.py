"""Nominal 4x6 side-cleat reserve and full-envelope regression screen."""

from scripts.simple_center_principal_cleat_reserve_probe import probe


def test_one_rectangular_grain_across_vertical_bolt_pose():
    result = probe()
    assert result["cleat_grain_axis"] == "Y"
    assert result["bolt_axes"]["header_cleat"][:2] == [15.475, -145.3]
    assert result["minimum_conditional_4d_transverse_reserve_mm"] == 5.0
    assert result["face_center_distances_mm"]["vertical_header_y_transverse"] == [
        30.4,
        109.3,
    ]
    assert result["face_center_distances_mm"]["vertical_cleat_x_transverse"] == [
        35.475,
        35.475,
    ]
    assert (
        min(result["face_center_distances_mm"]["cross_principal_z_section_transverse"])
        > 30.4
    )
    assert result["header_bottom_tool_to_backer_y_gap_mm"] == 0.4
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["inherited_pose_clear"] is True
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert len(result["center_kicker_screw_receiver_fraction"]) == 4
    assert set(result["center_kicker_screw_receiver_fraction"].values()) == {1.0}
    assert result["bore_received_fraction"] == {
        "header_cleat": 1.0,
        "cleat_principal": 1.0,
    }
    assert set(result["washer_bearing_fraction"].values()) == {1.0}
    for field in (
        "new_wood_overlaps_mm3",
        "fixed_screw_hits_mm3",
        "unintended_bore_wood_hits_mm3",
        "bore_pair_hits_mm3",
        "tool_wood_hits_mm3",
        "tool_panel_kicker_hits_mm3",
    ):
        assert result[field] == {}
    assert result["nominal_geometry"] == "accepted"
    assert result["fabrication_ready"] is False
    assert result["rating_or_drilling_release"] is False
