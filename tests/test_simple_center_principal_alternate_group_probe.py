"""PB-02 bounded alternatives must screen the complete revised bolt group."""

from scripts.simple_center_principal_alternate_group_probe import VARIANTS, probe


def test_alternatives_keep_left_principal_and_fixed_receivers():
    result = probe()
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["fixed_screw_axes_checked"] == 66
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert set(result["center_kicker_screw_receiver_fraction"].values()) == {1.0}
    assert result["rating_or_drilling_release"] is False
    assert set(result["variants"]) == set(VARIANTS)
    for name, trial in result["variants"].items():
        assert trial["block_bounds_mm"] == VARIANTS[name]["bounds"]
        assert (
            "block/base_principal_center_left"
            not in trial["checks"]["wood_overlaps_mm3"]
        )
        assert len(trial["bores_checked"]) == 10
        assert set(trial["bore_intended_wood_fraction"]) == set(trial["bores_checked"])
        assert all(
            all(value > 0 for value in woods.values()) and sum(woods.values()) == 1
            for woods in trial["bore_intended_wood_fraction"].values()
        )
        assert len(trial["bolt_groups"]["header_cleat"]["axes"]) == 2
        assert len(trial["bolt_groups"]["cleat_principal"]["axes"]) == 2
        assert len(trial["washer_bearing_fraction"]) == 20
        assert set(trial["checks"]) >= {
            "wood_overlaps_mm3",
            "bore_unintended_wood_hits_mm3",
            "bore_pair_hits_mm3",
            "bore_screw_hits_mm3",
            "hardware_wood_hits_mm3",
            "hardware_screw_hits_mm3",
            "hardware_pair_hits_mm3",
            "washer_other_wood_hits_mm3",
            "washer_screw_hits_mm3",
            "socket_wood_hits_mm3",
            "socket_screw_hits_mm3",
            "socket_hardware_hits_mm3",
            "insertion_wood_hits_mm3",
            "insertion_screw_hits_mm3",
        }
        assert all(
            "base_principal_center_left" not in key
            for key in trial["checks"]["bore_unintended_wood_hits_mm3"]
            if key.startswith("cleat_principal")
        )
        for group in trial["bolt_groups"].values():
            assert group["conditional_4d_pitch_margin_mm"] >= 0
            assert group["conditional_7d_pitch_comparator_mm"] is not None
        assert trial["principal_grain_status"] == "oblique grain/end unclassified"
        assert trial["conditional_header_rear_y_window_mm"] == (-150.3, -134.9)
        assert trial["nominal_collision_fit"] is False

    compact = result["variants"]["compact_y"]
    assert compact["checks"]["wood_overlaps_mm3"] == {}
    assert compact["checks"]["bore_pair_hits_mm3"] == {}
    assert "header_cleat_2_near/backer" in compact["checks"]["hardware_wood_hits_mm3"]
    assert compact["insertion_clear_ends"]["cleat_principal_1"] == []
    assert compact["conditional_principal_front_y_window_mm"] == (-108.9, -89.45)
    for name in ("forward_reach", "rightward_stock"):
        assert set(result["variants"][name]["checks"]["wood_overlaps_mm3"]) == {
            "block/main_lower_left",
            "block/main_lower_right",
        }
