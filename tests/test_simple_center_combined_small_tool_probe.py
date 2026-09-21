"""Independent small-socket combined PB-02 trial."""

from scripts.simple_center_combined_small_tool_probe import probe


def test_small_socket_trial_preserves_fixed_geometry_and_reports_access():
    result = probe()
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["fixed_screw_axes_checked"] == 66
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert len(result["header_screw_receiver_fraction"]) == 10
    assert set(result["header_screw_receiver_fraction"].values()) == {0.7125}
    assert len(result["center_kicker_screw_receiver_fraction"]) == 4
    assert set(result["center_kicker_screw_receiver_fraction"].values()) == {1.0}
    assert result["upright_axis_yz_mm"] == [-147.3, 350]
    assert result["conditional_reserves_pass"] is True
    assert result["cleat_bounds_mm"] == (-20.0, 50.95, -190.0, -45.0, 277.0, 338.0)
    assert result["principal_axes_mm"] == {
        "header_cleat_xy": [15.475, -145.3],
        "cleat_principal_yz": [-95.0, 307.5],
    }
    assert result["socket_body_radius_mm"] == 7.8486
    assert result["socket_body_length_mm"] == 24.511
    assert set(result["bore_received_fraction"].values()) == {1.0}
    assert set(result["washer_bearing_fraction"].values()) == {1.0}
    for key, value in result.items():
        if (
            key.endswith("hits_mm3") and key != "upright_20mm_tool_new_wood_hits_mm3"
        ) or key == "wood_overlaps_mm3":
            assert value == {}, key
    assert result["upright_20mm_tool_new_wood_hits_mm3"] == {
        "upright_left/header_side_cleat": 3578.36174
    }
    assert result["nominal_socket_body_geometry"] == "feasible"
    assert result["ratchet_or_extension_sweep_verified"] is False
    assert result["fabrication_ready"] is False
    assert result["rating_or_drilling_release"] is False
