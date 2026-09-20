"""Nominal CAD regression for the two-cleat post-to-upright transfer path."""

from scripts.simple_center_post_transfer_probe import probe


def test_post_transfer_has_contacting_bolted_members_and_clear_fixed_screws():
    result = probe()
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["right_post_shift_mm"] == 37.8
    assert result["cleat_bounds_mm"] == {
        "rear": [89.05, 127.15, -213.8, -175.7, 0.0, 460.0],
        "upright_side": [89.05, 127.15, -175.7, -124.9, 277.0, 460.0],
    }
    assert result["unintended_solid_overlaps_mm3"] == {}
    assert result["legacy_clip_wood_hits_mm3"] == {
        "shifted_right_post/clip_split_header_center_right": 21944.06212,
        "upright_side_cleat/clip_split_base_center_right": 11008.93288,
    }
    assert len(result["legacy_clip_screw_wood_hits_mm3"]) == 10
    assert result["contacts_mm2"]["post_rear"] > 0
    assert result["contacts_mm2"]["upright_side"] > 0
    assert result["contacts_mm2"]["cleat_pair"] > 0
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert result["bolt_bore_fixed_screw_hits_mm3"] == {}
    assert result["seat_fixed_screw_hits_mm3"] == {}
    assert result["cleat_fixed_screw_hits_mm3"] == {}
    assert result["bolt_bore_unintended_wood_hits_mm3"] == {}
    assert result["bolt_bore_pair_hits_mm3"] == {}
    assert result["bolt_bore_received_fraction"] == {
        "post_low": 1.0,
        "post_high": 1.0,
        "upright": 1.0,
        "cleat_link": 1.0,
    }
    assert result["front_seats_flush_below_kicker_back"]
    assert result["upright_washer_bearing_fraction"] > 0.999
    assert set(result["trial_20mm_radius_tool_wood_hits_mm3"]) == {
        "post_front_low/kicker_right",
        "post_front_high/kicker_right",
    }
