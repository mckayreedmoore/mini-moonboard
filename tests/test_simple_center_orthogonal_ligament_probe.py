"""Regression for the bounded PB02 ligament lead and its stated limit."""

from scripts.simple_center_orthogonal_ligament_probe import probe


def test_bounded_shift_keeps_axes_and_improves_both_nominal_ligaments():
    result = probe()
    old = result["samples"]["current"]
    new = result["samples"]["bounded_adjustment"]
    assert old["nominal_wood_ligament_mm"] == {
        "post_high/post_cleat_2": 2.7,
        "upright/cleat_link": 2.7,
    }
    assert new["nominal_wood_ligament_mm"] == {
        "post_high/post_cleat_2": 6.7,
        "upright/cleat_link": 22.7,
    }
    assert result["post_fixed_block_gap_cap_with_5mm_mm"] == 15.15
    assert new["post_pair_pitch_reserve_with_5mm_mm"] == 0.6
    assert new["bore_count"] == 10
    assert new["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert new["fixed_screw_axes_checked"] == 66
    assert set(new["receiver_fraction"].values()) == {1.0}
    assert set(new["moved_washer_bearing_fraction"].values()) == {1.0}
    for key in (
        "unintended_wood_hits_mm3",
        "bore_pair_hits_mm3",
        "fixed_screw_hits_mm3",
        "moved_hardware_wood_hits_mm3",
        "moved_hardware_screw_hits_mm3",
    ):
        assert new[key] == {}
    assert result["strength_or_nds_pass"] is False
