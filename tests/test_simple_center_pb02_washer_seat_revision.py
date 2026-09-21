"""Check the working PB-02 nominal pose and raised-bottom counterexample."""

from scripts.simple_center_pb02_washer_seat_revision import TRIALS, evaluate


def test_working_pose_has_complete_ten_bore_nominal_cad_fit():
    result = evaluate(TRIALS["working_61p6_depth"])
    assert result["bore_count"] == 10
    assert result["fixed_screw_count"] == 66
    assert result["all_66_fixed_axes_preserved"]
    assert result["header_side_cleat_header_contact_area_mm2"] > 0
    assert all(
        fraction > 0
        for fraction in result["header_cleat_bore_reception_fraction"].values()
    )
    assert len(result["washer_bearing_fraction"]) == 20
    assert result["all_20_washer_seats_full"]
    assert result["one_insertion_end_per_bolt_clear"]
    assert result["side_y_conditional_4d_plus_project_5_reserve_mm"] >= 0
    assert result["side_z_conditional_7d_plus_5_reserve_mm"] >= 0
    assert result["inner_kicker_edges_supported"]
    assert not any(result["side_checks"].values())
    assert not any(result["full_center_collision_checks"].values())
    assert result["nominal_cad_clear"]
    assert result["conditional_negative_rows"]
    assert not result["whole_center_classification_complete"]
    assert not result["rating_or_drilling_release"]


def test_raised_bottom_does_not_remove_high_rail_collision():
    result = evaluate(TRIALS["deeper_raised_bottom"])
    assert result["side_z_conditional_7d_plus_5_reserve_mm"] >= 0
    assert result["all_20_washer_seats_full"]
    assert (
        "upright_side_cleat/base_rail_bottom_right"
        in result["side_checks"]["side_other_wood_hits_mm3"]
    )
    assert not result["nominal_cad_clear"]
