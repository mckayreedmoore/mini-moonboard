"""Bounded, non-selected center-header row-Y geometry screen."""

import json
from pathlib import Path

import pytest

from scripts.bolted_candidate_center_y_stagger import screen_center_y_stagger


def test_fixed_axes_and_actual_post_band():
    result = screen_center_y_stagger()
    assert result["status"] == "geometry_screen_only"
    assert result["selected_row_y_mm"] is None
    assert result["drilling_released"] is False
    assert result["top_row_y_mm"] == pytest.approx(-95.382052)
    assert result["post_4d_y_band_mm"][0] < -95.382052 < result["post_4d_y_band_mm"][1]
    assert result["retained_axis_counts"] == {"hillman_panel": 66, "bolt_clearance": 12}
    assert result["physical_kicker_width_option"] == "kerf-right"
    assert result["maximum_possible_y_stagger_mm"] == pytest.approx(29.517948)
    assert result["parallel_minimum_reachable_in_band"] is True
    assert result["perpendicular_minimum_reachable_in_band"] is False
    assert result["conditional_distinct_row_y_intervals_mm"] == {
        "parallel": [[-124.9, -114.432052]],
        "perpendicular": [],
    }
    assert len(result["samples"]) == 5
    assert result["samples"][0]["underside_row_y_mm"] == pytest.approx(
        result["post_4d_y_band_mm"][0]
    )
    assert result["samples"][-1]["underside_row_y_mm"] == pytest.approx(
        result["post_4d_y_band_mm"][1]
    )


def test_each_row_reports_bore_overlap_spacing_and_noncontact():
    result = screen_center_y_stagger()
    assert result["table_12_5_1d_conditional_minimum_mm"] == {
        "parallel": pytest.approx(19.05),
        "perpendicular": pytest.approx(39.6875),
    }
    for sample in result["samples"]:
        for side in sample["sides"]:
            assert side["top_header_x_mm"] == side["underside_header_x_mm"]
            assert side["minimum_axis_distance_mm"] == pytest.approx(
                abs(sample["underside_row_y_mm"] - result["top_row_y_mm"])
            )
            assert side["minimum_bore_web_mm"] == pytest.approx(
                side["minimum_axis_distance_mm"] - 14.2875
            )
            expected_overlap = 2 if side["minimum_axis_distance_mm"] < 14.2875 else 0
            assert side["overlapping_header_bore_pairs"] == expected_overlap
            assert (side["maximum_header_bore_overlap_mm3"] > 0) is bool(
                expected_overlap
            )
            assert side["post_bore_full_section_fractions"] == pytest.approx([1, 1])
            assert side["header_bore_full_section_fractions"] == pytest.approx([1, 1])
            assert side["top_principal_bore_full_section_fractions"] == pytest.approx(
                [1, 1]
            )
            assert side["top_header_bore_full_section_fractions"] == pytest.approx(
                [1, 1]
            )
            assert side["retained_axis_hits"] == []
            assert side["parallel_row_spacing_category"] == (
                "coincident_axes"
                if side["minimum_axis_distance_mm"] < 1e-6
                else "at_or_above_conditional_minimum"
                if side["minimum_axis_distance_mm"] >= 19.05
                else "below_conditional_minimum"
            )
            assert side["perpendicular_row_spacing_category"] in (
                "coincident_axes",
                "below_conditional_minimum",
            )
            assert side["angle_body_overlap_mm3"] == pytest.approx(0)
            assert side["angle_bodies_on_opposite_header_faces"] is True
            assert side["nds_row_accepted"] is False


def test_rejects_rows_outside_bounded_band():
    with pytest.raises(ValueError):
        screen_center_y_stagger((-130,))
    with pytest.raises(ValueError):
        screen_center_y_stagger((float("nan"),))


def test_parallel_interval_midpoint_is_still_only_a_conditional_trial():
    result = screen_center_y_stagger((-119.666026,))
    assert result["selected_row_y_mm"] is None
    assert result["drilling_released"] is False
    sample = result["samples"][0]
    assert sample["underside_row_y_mm"] == pytest.approx(-119.666026)
    for side in sample["sides"]:
        assert side["minimum_axis_distance_mm"] == pytest.approx(24.283974)
        assert side["minimum_bore_web_mm"] == pytest.approx(9.996474)
        assert side["parallel_row_spacing_category"] == (
            "at_or_above_conditional_minimum"
        )
        assert side["perpendicular_row_spacing_category"] == (
            "below_conditional_minimum"
        )
        assert side["overlapping_header_bore_pairs"] == 0
        assert side["retained_axis_hits"] == []


def test_record_matches_screen_without_releasing_layout():
    record = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs/bolted-candidate-prototypes/center-y-stagger.json"
        ).read_text()
    )
    result = screen_center_y_stagger()
    lower = result["samples"][0]
    left = lower["sides"][0]
    assert record["top_row_y_mm"] == result["top_row_y_mm"]
    assert (
        record["underside_post_conditional_4d_band_y_mm"] == result["post_4d_y_band_mm"]
    )
    assert (
        record["maximum_possible_y_stagger_mm"]
        == result["maximum_possible_y_stagger_mm"]
    )
    assert (
        record["conditional_distinct_row_y_intervals_mm"]
        == result["conditional_distinct_row_y_intervals_mm"]
    )
    midpoint = record["conditional_parallel_interval_midpoint_trial"]
    assert midpoint["underside_row_y_mm"] == pytest.approx(
        sum(result["conditional_distinct_row_y_intervals_mm"]["parallel"][0]) / 2
    )
    assert midpoint["spacing_to_fixed_top_row_mm"] == pytest.approx(
        result["top_row_y_mm"] - midpoint["underside_row_y_mm"]
    )
    assert midpoint["lower_4d_band_edge_reserve_mm"] == pytest.approx(
        midpoint["underside_row_y_mm"] - result["post_4d_y_band_mm"][0]
    )
    assert midpoint["selected"] is False
    assert record["conditional_distinct_row_minimum_mm"]["parallel_loading"] == (
        pytest.approx(result["table_12_5_1d_conditional_minimum_mm"]["parallel"])
    )
    assert record["conditional_distinct_row_minimum_mm"][
        "perpendicular_loading_assuming_38_1_mm_lesser_wood_bearing"
    ] == pytest.approx(result["table_12_5_1d_conditional_minimum_mm"]["perpendicular"])
    assert (
        record["sample_at_lower_band_edge"]["underside_row_y_mm"]
        == lower["underside_row_y_mm"]
    )
    assert (
        record["sample_at_lower_band_edge"]["minimum_bore_web_mm"]
        == left["minimum_bore_web_mm"]
    )
    assert (
        record["sample_at_lower_band_edge"]["overlapping_header_bore_pairs_per_side"]
        == left["overlapping_header_bore_pairs"]
    )
    assert (
        record["sample_at_lower_band_edge"]["retained_axis_hits"]
        == left["retained_axis_hits"]
    )
    assert record["selected_underside_row_y_mm"] is None
    assert record["nds_row_accepted"] is False
    assert record["drilling_released"] is False
