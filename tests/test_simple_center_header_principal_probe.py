"""Bounded nominal screen for the displaced right header/principal clip."""

from scripts.simple_center_header_principal_probe import probe


def test_one_full_section_vertical_bolt_is_rejected_for_sloped_bearing():
    trial = probe()
    assert trial["station"] == "clip_split_base_center_right"
    assert trial["pose"] == "simple_center_link_edge_probe"
    assert len(trial["trials"]) == 1
    candidate = trial["trials"][0]
    assert candidate["axis_xyz_mm"][:2] == [65.0, -160.0]
    assert candidate["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert candidate["baseline_clear"] is True
    assert candidate["wood_overlap_mm3"] == {}
    assert candidate["bore_fixed_screw_hits_mm3"] == {}
    assert candidate["bore_other_wood_hits_mm3"] == {}
    assert candidate["bore_existing_bore_hits_mm3"] == {}
    assert candidate["bottom_tool_wood_hits_mm3"] == {}
    assert candidate["header_bore_envelope_received_fraction"] == 1.0
    assert candidate["principal_bore_envelope_received_fraction"] == 0.9459368
    assert candidate["principal_top_slope_abs_dz_dy"] > 1.19
    assert candidate["top_face_z_variation_across_20mm_washer_mm"] > 23.8
    assert (
        candidate["top_vertical_tool_wood_hits_mm3"]["base_principal_center_right"] > 0
    )
    assert set(candidate["top_vertical_tool_wood_hits_mm3"]) == {
        "base_principal_center_right"
    }
    assert candidate["status"] == "rejected"
    assert "sloped" in candidate["rejection_reason"]
    assert trial["rating_or_drilling_release"] is False
    edge = trial["untried_y_axis_header_bolt_conditional_edge_limit"]
    assert edge["header_z_thickness_mm"] == 38.1
    assert edge["minimum_for_reversible_loaded_z_edges_mm"] == 50.8
    assert edge["shortfall_at_each_symmetric_loaded_edge_mm"] == 6.35
    assert trial["old_proxy_forces_are_new_demand"] is False
