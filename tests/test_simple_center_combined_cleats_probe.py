"""Simultaneous PB-02 cleat geometry, with inherited fixed axes preserved."""

from scripts.simple_center_combined_cleats_probe import probe


def test_combined_nominal_pose():
    result = probe()
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["fixed_screw_axes_checked"] == 66
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert len(result["header_screw_receiver_fraction"]) == 10
    assert set(result["header_screw_receiver_fraction"].values()) == {0.7125}
    assert len(result["center_kicker_screw_receiver_fraction"]) == 4
    assert set(result["center_kicker_screw_receiver_fraction"].values()) == {1.0}
    assert len(result["new_bore_received_fraction"]) == 4
    assert set(result["new_bore_received_fraction"].values()) == {1.0}
    assert len(result["new_washer_bearing_fraction"]) == 8
    assert set(result["new_washer_bearing_fraction"].values()) == {1.0}
    assert len(result["inherited_washer_bearing_fraction"]) == 8
    assert set(result["inherited_washer_bearing_fraction"].values()) == {1.0}
    assert {joint: len(ends) for joint, ends in result["new_joint_ends"].items()} == {
        "header_post": 4,
        "header_principal": 4,
    }
    assert len(result["inherited_ends_checked"]) == 8
    for key in (
        "new_wood_overlaps_mm3",
        "new_bore_other_wood_hits_mm3",
        "new_bore_pair_hits_mm3",
        "new_screw_hits_mm3",
        "new_hardware_wood_hits_mm3",
        "new_washer_unintended_wood_hits_mm3",
        "new_hardware_screw_hits_mm3",
        "new_tool_wood_hits_mm3",
        "new_tool_screw_hits_mm3",
        "inherited_bore_new_wood_hits_mm3",
        "new_hardware_inherited_hardware_hits_mm3",
        "new_tool_inherited_hardware_hits_mm3",
        "inherited_tool_new_hardware_hits_mm3",
    ):
        assert result[key] == {}
    assert len(result["intended_serial_paths"]) == 2
    assert set(result["old_clips_displaced"]) == {
        "clip_split_base_center_right",
        "clip_split_header_center_right",
    }
    assert result["inherited_hardware_new_wood_hits_mm3"] == {
        "upright_left/header_side_cleat": 1570.79633
    }
    assert set(result["inherited_washer_new_wood_hits_mm3"]) == {
        "upright_left/header_side_cleat"
    }
    assert (
        result["inherited_washer_new_wood_hits_mm3"]["upright_left/header_side_cleat"]
        > 0
    )
    assert result["inherited_tool_new_wood_hits_mm3"] == {
        "upright_left/header_side_cleat": 25132.74123
    }
    assert result["nominal_geometry"] == "rejected"
    assert result["fabrication_ready"] is False
    assert result["rating_or_drilling_release"] is False
