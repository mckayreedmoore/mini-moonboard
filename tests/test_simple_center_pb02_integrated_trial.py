"""Pin the viable Z370 pose and the rejected Z390 comparison."""

import pytest

from scripts.simple_center_pb02_integrated_trial import (
    COMPARISON_LINK_Z,
    probe,
    working_geometry,
)


def test_combined_ten_bore_trial_and_rejected_link_comparison():
    result = probe()
    assert result["coordinates_mm"]["post_cleat_2_z"] == 176
    assert result["coordinates_mm"]["cleat_link_z"] == 370
    assert result["side_bounds_mm"] == [89.05, 177.95, -175.7, -114.1, 277, 460]
    assert result["bore_count"] == 10
    assert set(result["bore_received_fraction"].values()) == {1.0}
    assert len(result["washer_bearing_fraction"]) == 20
    assert result["all_20_washer_seats_full"]
    assert result["all_66_fixed_axes_preserved"]
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert result["one_insertion_end_per_bolt_clear"]
    assert result["clear_insertion_ends_by_bolt"]["cleat_link"] == ["link_rear"]
    assert result["side_checks"] == {
        "side_other_wood_hits_mm3": {},
        "side_screw_hits_mm3": {},
    }
    assert not any(result["full_center_collision_checks"].values())
    assert (
        result["finite_shared_member_bore_ligaments_mm"]["post_high/post_cleat_2"]
        == 6.7
    )
    assert result["finite_shared_member_bore_ligaments_mm"]["upright/cleat_link"] == 6.7
    assert result["minimum_finite_shared_member_bore_ligament_mm"] == 6.7
    assert result["side_y_conditional_4d_plus_project_5_reserve_mm"] == 0
    assert result["side_z_conditional_7d_plus_5_reserve_mm"] == 29.55
    assert result["post_pair_conditional_4d_plus_5_reserve_mm"] == 0.6
    assert result["conditional_subset_minimum_reserve_mm"] == -2.9
    assert len(result["conditional_negative_rows"]) == 3
    assert result["header_side_cleat_header_contact_area_mm2"] > 0
    assert sum(result["header_cleat_bore_reception_fraction"].values()) == 1
    assert result["integrated_nominal_cad_clear"]
    assert not result["whole_center_classification_complete"]
    assert not result["rating_or_drilling_release"]

    rejected = probe(COMPARISON_LINK_Z)
    assert rejected["coordinates_mm"]["cleat_link_z"] == 390
    assert rejected["full_center_collision_checks"]["socket_body_wood_hits_mm3"] == {
        "link_front/base_rail_bottom_right": pytest.approx(471.14874)
    }
    assert (
        rejected["finite_shared_member_bore_ligaments_mm"]["upright/cleat_link"] == 26.7
    )
    assert not rejected["integrated_nominal_cad_clear"]


def test_viewer_geometry_uses_the_checked_working_pose():
    parts, bores, ends = working_geometry()
    assert len(bores) == 10
    assert parts["upright_side_cleat"].BoundingBox().ymax == -114.1
    assert parts["header_side_cleat"].BoundingBox().zmax == 344
    assert ends["post_cleat_2_left"][0][2] == 176
    assert ends["link_rear"][0][2] == 370
