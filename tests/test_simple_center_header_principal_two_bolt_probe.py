"""Regression for the bounded two-bolt PB-02 header/principal co-design."""

from scripts.simple_center_header_principal_two_bolt_probe import VARIANTS, probe


def test_bounded_variants_screen_both_serial_faces_and_fixed_geometry():
    result = probe()
    assert result["pose_coordinates_mm"]["top_z"] == 348
    assert result["baseline_nominal_geometry"] == "feasible"
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["fixed_screw_axes_checked"] == 66
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert len(result["variants"]) == len(VARIANTS)
    assert result["rating_or_drilling_release"] is False
    for name, trial in result["variants"].items():
        assert trial["block_bounds_mm"] == VARIANTS[name]["bounds"]
        assert set(trial["faces"]) == {"header_cleat", "cleat_principal"}
        for face in trial["faces"].values():
            assert len(face["axes"]) == 2
            assert face["spacing_mm"] >= 25.4
            assert len(face["second_bolt_checks"]["washer_bearing_fraction"]) == 2
            assert set(face["second_bolt_checks"]) >= {
                "intended_wood_fraction",
                "other_bore_hits_mm3",
                "fixed_screw_hits_mm3",
                "hardware_wood_hits_mm3",
                "socket_wood_hits_mm3",
                "insertion_clear_ends",
            }
            if face["name"] == "cleat_principal":
                assert "oblique" in face["principal_grain_note"]
        assert "original_bore_wood_hits_mm3" in trial["checks"]
        assert "original_hardware_wood_hits_mm3" in trial["checks"]
        assert "new_bore_pair_hits_mm3" in trial["checks"]
        assert "first_bore_fixed_screw_hits_mm3" in trial["checks"]
        assert "original_insertion_screw_hits_mm3" in trial["checks"]
        assert trial["first_bore_received_fraction"] == {
            "header_cleat": 1.0,
            "cleat_principal": 1.0,
        }
        assert not trial["both_second_bolts_collision_fit"]
        assert (
            "block/base_principal_center_left"
            in trial["checks"]["block_other_wood_hits_mm3"]
        )
        assert (
            "cleat_principal/base_principal_center_left"
            in trial["checks"]["first_bore_unintended_wood_hits_mm3"]
        )
