"""The one relocated inherited upright bolt must be judged in the full pose."""

from scripts.simple_center_combined_upright_relocation_probe import probe


def test_relocated_upright_station_is_rejected_with_all_fixed_screws_preserved():
    result = probe()
    assert result["old_upright_axis_yz_mm"] == [-147.3, 350]
    assert result["trial_upright_axis_yz_mm"] == [-129, 400]
    assert result["upright_x_span_mm"] == [50.95, 177.95]
    assert result["old_bore_present_in_candidate"] is False
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["fixed_screw_axes_checked"] == 66
    assert len(result["fixed_screw_receiver_fraction"]) == 66
    assert set(result["fixed_screw_receiver_fraction"].values()) == {1.0}
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert result["inherited_baseline_clear"] is True
    assert len(result["bore_received_fraction"]) == 8
    assert result["bore_received_fraction"]["upright"] == 0.7
    assert set(result["bore_received_fraction"].values()) == {0.7, 1.0}
    assert result["upright_member_bore_fraction"] == {
        "base_principal_center_right": 0.0,
        "upright_side_cleat": 0.7,
    }
    assert len(result["washer_bearing_fraction"]) == 16
    assert result["washer_bearing_fraction"]["upright_left"] < 0.13
    assert all(
        fraction == 1.0
        for name, fraction in result["washer_bearing_fraction"].items()
        if name != "upright_left"
    )
    assert result["conditional_nds_distances"]["side_y_transverse_mm"] == [46.7, 10.1]
    assert result["conditional_nds_markers_mm"]["reversible_loaded_edge_4d"] == 25.4
    assert result["tool_wood_hits_mm3"] == {
        "upright_right/base_rail_bottom_right": 78.63629
    }
    for key in (
        "wood_overlaps_mm3",
        "bore_unintended_wood_hits_mm3",
        "bore_pair_hits_mm3",
        "wood_screw_hits_mm3",
        "bore_screw_hits_mm3",
        "hardware_wood_hits_mm3",
        "washer_face_wood_hits_mm3",
        "hardware_screw_hits_mm3",
        "washer_face_screw_hits_mm3",
        "tool_screw_hits_mm3",
        "hardware_hardware_hits_mm3",
        "bore_hardware_hits_mm3",
        "bore_tool_hits_mm3",
        "washer_face_hardware_hits_mm3",
        "tool_hardware_hits_mm3",
    ):
        assert result[key] == {}, key
    assert result["nominal_geometry"] == "rejected"
    assert result["stack_strength_or_drilling_release"] is False
