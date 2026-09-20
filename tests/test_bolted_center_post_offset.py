"""The post-only AB205 offset is a bounded geometry trial, not a layout."""

import json
from pathlib import Path

import pytest

from scripts.bolted_candidate_center_post_offset import (
    fixed_pattern_header_min_pair_spacing_mm,
    screen_center_post_offsets,
)


def test_post_only_offsets_keep_top_axes_fixed_and_separate_underside_axes():
    result = screen_center_post_offsets()
    assert result["status"] == "geometry_screen_only"
    assert result["selected_offset_mm"] is None
    assert result["drilling_released"] is False
    assert [case["offset_mm"] for case in result["samples"]] == [0, 5, 10, 15]
    for case in result["samples"]:
        left, right = case["sides"]
        assert left["top_header_x_mm"] == [-125.5625, -173.1875]
        assert right["top_header_x_mm"] == [125.5625, 173.1875]
        for side in (left, right):
            sign = -1 if side["side"] == "left" else 1
            assert side["post_shift_x_mm"] == sign * case["offset_mm"]
            assert side["underside_header_x_mm"] == pytest.approx(
                [x + sign * case["offset_mm"] for x in side["top_header_x_mm"]]
            )
            assert side["post_bore_full_section_fractions"] == pytest.approx([1, 1])
            assert side["nominal_panel_axis_hits"] == []
            assert side["retained_bore_axis_hits"] == []
            kerf_overhang = 49.3625 if side["side"] == "left" else 52.5375
            assert side["kicker_interior_seam_overhang_mm"] == pytest.approx(
                kerf_overhang + case["offset_mm"]
            )
            assert side["kicker_interior_edge_x_mm"] == pytest.approx(-1.5875)
            assert (
                side["kicker_seam_overhang_increase_from_raw_baseline_mm"]
                == case["offset_mm"]
            )
            assert side["kicker_interior_edge_directly_supported_by_post"] is False
            assert side["kicker_edge_support_verified"] is False
            assert side["kicker_support_degraded_vs_baseline"] is (
                case["offset_mm"] > 0
            )
            assert len(side["kicker_screw_support_engagement"]) == 2
            assert all(
                screw["occupied_axis_intersects_shifted_post"]
                for screw in side["kicker_screw_support_engagement"]
            )
            assert all(
                screw["modeled_occupied_axis_inside_post_width"]
                for screw in side["kicker_screw_support_engagement"]
            )
            assert side["drilling_released"] is False


def test_header_bore_overlap_and_web_are_recomputed_at_each_offset():
    samples = screen_center_post_offsets()["samples"]
    for case in samples:
        for side in case["sides"]:
            assert side["minimum_top_underside_axis_spacing_mm"] == pytest.approx(
                case["offset_mm"]
            )
            assert side[
                "conditional_separate_header_bolts_minimum_3d_mm"
            ] == pytest.approx(38.1)
            assert side["separate_header_bolt_spacing_screen"] == (
                "shared_axis_not_this_check"
                if case["offset_mm"] == 0
                else "below_3d_minimum"
            )
            assert side["minimum_top_underside_bore_web_mm"] == pytest.approx(
                case["offset_mm"] - 14.2875
            )
            assert side["overlapping_top_underside_bore_pairs"] == (
                2 if case["offset_mm"] < 14.2875 else 0
            )
            assert side["header_bore_full_section_fractions"] == pytest.approx([1, 1])
    assert samples[0]["sides"][0]["coincident_header_axes"] == 2
    assert all(
        side["coincident_header_axes"] == 0
        for case in samples[1:]
        for side in case["sides"]
    )


def test_fixed_ab205_pattern_has_no_post_only_offset_preserving_kicker_axes():
    threshold = screen_center_post_offsets()["fixed_pattern_offset_threshold"]
    assert threshold[
        "necessary_lower_bound_from_coincident_factory_pair_mm"
    ] == pytest.approx(38.1)
    assert fixed_pattern_header_min_pair_spacing_mm(38.1) == pytest.approx(9.525)
    assert threshold["cross_pair_spacing_at_that_lower_bound_mm"] == pytest.approx(
        9.525
    )
    assert threshold[
        "minimum_shift_for_all_distinct_header_pairs_3d_mm"
    ] == pytest.approx(85.725)
    assert threshold[
        "minimum_extra_factory_pattern_shift_at_axis_center_limit_mm"
    ] == pytest.approx(66.675)
    assert threshold["axis_center_margin_at_assumed_post_shift_mm"] == pytest.approx(0)
    assert threshold["different_factory_pattern_verified"] is False
    assert fixed_pattern_header_min_pair_spacing_mm(85.724) < 38.1
    assert fixed_pattern_header_min_pair_spacing_mm(85.725) == pytest.approx(38.1)
    assert threshold[
        "maximum_shift_before_frozen_kicker_screw_axis_reaches_post_edge_mm"
    ] == pytest.approx(19.05)
    assert threshold[
        "maximum_shift_before_modeled_screw_occupancy_reaches_post_edge_mm"
    ] == pytest.approx(16.9799)
    assert threshold["required_shift_exceeds_axis_center_limit_mm"] == pytest.approx(
        19.05
    )
    assert (
        threshold["simultaneous_nominal_3d_and_frozen_axis_engagement_possible"]
        is False
    )
    assert threshold["applies_to_other_factory_hole_patterns"] is False


def test_scope_and_unresolved_gates_are_explicit():
    result = screen_center_post_offsets()
    assert result["top_trial_row_y_mm"] == pytest.approx(-95.382052)
    assert result["retained_axis_counts"] == {"hillman_panel": 66, "bolt_clearance": 12}
    assert result["kerf_official_relevant_panel_axes_identical"] is True
    assert result["physical_kicker_width_option"] == "kerf-right"
    assert set(result["missing_checks"]) >= {"loads", "access", "ratings"}
    with pytest.raises(ValueError):
        screen_center_post_offsets((-1,))
    with pytest.raises(ValueError):
        screen_center_post_offsets((20,))


def test_published_kerf_right_post_only_decision_matches_geometry():
    record = json.loads(
        Path(
            "docs/bolted-candidate-prototypes/center-post-only-offset.json"
        ).read_text()
    )
    result = screen_center_post_offsets()
    assert record["status"] == "bounded_trial_no_qualifying_offset"
    assert result["physical_kicker_width_option"] == "kerf-right"
    assert record["selected_offset_mm"] is None
    assert record["drilling_released"] is False
    assert (
        record["fixed_pattern_offset_threshold"]
        == result["fixed_pattern_offset_threshold"]
    )
    for published, calculated in zip(record["samples"], result["samples"], strict=True):
        assert published["post_outward_shift_each_side_mm"] == calculated["offset_mm"]
        for side in calculated["sides"]:
            assert (
                published["top_underside_header_axis_distance_mm"]
                == side["minimum_top_underside_axis_spacing_mm"]
            )
            assert (
                published["header_bore_web_mm"]
                == side["minimum_top_underside_bore_web_mm"]
            )
            assert side["separate_header_bolt_spacing_screen"] != "meets_3d_minimum"
            assert (
                published[f"kerf_kicker_inner_edge_overhang_{side['side']}_mm"]
                == side["kicker_interior_seam_overhang_mm"]
            )
            assert all(
                screw["modeled_occupied_axis_edge_reserve_mm"]
                == published["kicker_screw_modeled_occupied_axis_edge_reserve_mm"]
                for screw in side["kicker_screw_support_engagement"]
            )
