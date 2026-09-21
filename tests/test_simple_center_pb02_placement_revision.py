"""Pin the bounded PB02 conditional placement co-design."""

import pytest

from scripts.simple_center_pb02_placement_revision import probe


def test_front_stagger_clears_target_reserves_and_keeps_nominal_fit():
    results = probe()
    selected = results["front_stagger"]

    assert selected["variant_id"] == "front_stagger"
    assert selected["post_high_z_mm"] == 189
    assert selected["vertical_x_mm"] == (208.35, 236.0)
    assert selected["vertical_y_mm"] == (-130.5, -117.5)
    assert selected["target_conditional_reserves_mm"] == {
        "cleat_header_1/base_header/cleat_header_2": pytest.approx(0.1536),
        "cleat_header_1/header_post_side_cleat/cleat_header_2": pytest.approx(0.1536),
        "post_high/shifted_right_post/z_high": pytest.approx(0.45),
    }
    assert selected["conditional_minimum_reserve_mm"] == 0
    assert selected["conditional_negative_rows"] == []
    assert selected["fixed_screw_axes_preserved"]
    assert set(selected["bore_received_fraction"].values()) == {1.0}
    assert set(selected["washer_bearing_fraction"].values()) == {1.0}
    assert all(selected["clear_insertion_ends_by_bolt"].values())
    assert not any(selected["full_center_collision_checks"].values())
    assert not any(selected["side_checks"].values())
    assert selected["nominal_cad_clear"]
    assert not selected["whole_center_classification_complete"]
    assert not selected["rating_or_drilling_release"]


def test_active_ordinary_hardware_revision_trades_end_factor_for_ligament():
    selected = probe()["ligament_priority"]

    assert selected["post_high_z_mm"] == 202
    assert selected["post_high_loaded_end_distance_mm"] == 36.9
    assert selected["post_high_conditional_3_5d_reserve_mm"] == 14.675
    assert selected["post_high_conditional_c_delta"] == pytest.approx(0.83015)
    assert selected["target_conditional_reserves_mm"][
        "post_high/shifted_right_post/z_high"
    ] == pytest.approx(-12.55)
    assert selected["conditional_negative_rows"] == [
        {
            "bolt": "post_high",
            "member": "shifted_right_post",
            "feature": "z_high",
            "reserve_mm": -12.55,
        }
    ]
    assert selected["fixed_screw_axes_preserved"]
    assert selected["nominal_cad_clear"]


def test_historical_end_distance_factors_are_capped_at_one():
    results = probe()
    for name in ("working_reference", "rear_stagger", "front_stagger"):
        assert results[name]["post_high_conditional_c_delta"] == 1.0


def test_bounded_controls_reproduce_reference_and_reject_rear_stagger():
    results = probe()
    reference = results["working_reference"]
    rejected = results["rear_stagger"]

    assert reference["conditional_minimum_reserve_mm"] == -2.9
    assert len(reference["conditional_negative_rows"]) == 3
    assert reference["nominal_cad_clear"]

    assert rejected["conditional_negative_rows"] == []
    assert rejected["full_center_collision_checks"]["bore_pair_hits_mm3"] == {
        "post_cleat_1/cleat_header_2": pytest.approx(238.42571),
        "post_cleat_2/cleat_header_2": pytest.approx(238.42571),
    }
    assert not rejected["nominal_cad_clear"]
