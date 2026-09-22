"""Regression guards for the assembled barrel viewer's nominal axial stacks."""

import pytest

from scripts import owner_barrel_installed_stack_audit as audit
from scripts import owner_barrel_rail_layout as rail


@pytest.fixture(scope="module")
def report():
    return audit.build_report()


def test_current_assembly_accounts_for_all_48_rows_without_release(report):
    assert report["schema"] == audit.SCHEMA
    assert report["row_count"] == 48
    assert len({row["bolt_name"] for row in report["rows"]}) == 48
    assert len({row["station"] for row in report["rows"]}) == 24
    assert report["counts"]["thread_engagement_unknown"] == 48
    assert all(row["thread_engagement"] == "UNKNOWN" for row in report["rows"])
    assert report["overall_pass"] is False
    assert report["fit_qualified"] is False
    assert report["structural_released"] is False
    assert report["drilling_released"] is False
    assert report["fabrication_released"] is False


def test_each_row_is_source_bound_and_has_a_signed_tip_bore_clearance(report):
    for row in report["rows"]:
        assert row["barrel_name"] + "_bolt" == row["bolt_name"]
        assert row["shaft_length_mm"] > 0
        assert row["barrel_body_od_mm"] > row["shaft_od_mm"]
        assert row["machine_bore_od_mm"] > row["shaft_od_mm"]
        assert (
            row["reach_to_barrel_near_wall_mm"]
            < row["assumed_thread_axis_reach_mm"]
            < row["reach_to_barrel_far_wall_mm"]
        )
        assert row["tip_to_bore_far_cap_clearance_mm"] == pytest.approx(
            row["machine_bore_far_cap_from_shaft_start_mm"] - row["shaft_length_mm"],
            abs=0.0002,
        )
        assert row["minimum_added_bore_depth_to_tip_mm"] == pytest.approx(
            max(0, -row["tip_to_bore_far_cap_clearance_mm"]), abs=0.0002
        )
        assert row["nominal_axial_flags"]
        assert row["maximum_body_overlap_with_fully_threaded_shaft_mm"] <= (
            row["barrel_body_od_mm"] + 0.0002
        )
        assert row["bolt_end_thread_length_needed_to_reach_near_wall_mm"] == (
            pytest.approx(
                max(
                    0,
                    row["shaft_length_mm"] - row["reach_to_barrel_near_wall_mm"],
                ),
                abs=0.0002,
            )
        )


def test_independent_short_and_overrun_flags_can_coexist():
    assert audit._classify(100, 90, 80) == [
        "SHORT_OF_ASSUMED_BARREL_AXIS",
        "BEYOND_MODELED_MACHINE_BORE",
    ]
    assert audit._classify(100, 90, 110) == ["SHORT_OF_ASSUMED_BARREL_AXIS"]
    assert audit._classify(100, 105, 102) == ["BEYOND_MODELED_MACHINE_BORE"]
    assert audit._classify(100, 105, 110) == ["AXIS_REACHED_WITHIN_MODELED_BORE"]


def test_six_inch_60_mm_outer_rail_revision_is_in_the_current_viewer(report):
    assert rail.VIEWER_OUTER_SETBACK_MM == 60.0
    assert len(rail.VIEWER_OUTER_STATIONS) == 6
    outer = [
        row for row in report["rows"] if row["station"] in rail.VIEWER_OUTER_STATIONS
    ]
    assert len(outer) == 12
    assert all(row["shaft_length_mm"] == pytest.approx(152.4) for row in outer)
    assert all(
        row["outer_rail_barrel_setback_from_nearest_end_mm"] == pytest.approx(60.0)
        for row in outer
    )
    assert all(
        row["nominal_axial_flags"] == ["AXIS_REACHED_WITHIN_MODELED_BORE"]
        for row in outer
    )
    assert all(
        row["maximum_body_overlap_with_fully_threaded_shaft_mm"]
        == pytest.approx(6.8528, abs=0.0002)
        for row in outer
    )


def test_exact_other_family_bore_overruns_are_not_hidden(report):
    expected_stations = {
        "clip_horizontal_lower_left_2",
        "clip_horizontal_lower_right_1",
        "clip_horizontal_upper_left_2",
        "clip_horizontal_upper_right_1",
    }
    expected_names = {
        f"{station}_barrel_{index}_bolt"
        for station in expected_stations
        for index in (1, 2)
    }
    assert report["counts"] == {
        "short_of_assumed_barrel_axis": 0,
        "beyond_modeled_machine_bore": 8,
        "axis_reached_within_modeled_bore": 40,
        "head_absent": 0,
        "washer_absent": 0,
        "thread_engagement_unknown": 48,
    }
    assert set(report["named_exceptions"]["beyond_modeled_machine_bore"]) == (
        expected_names
    )
    for row in report["rows"]:
        if row["bolt_name"] in expected_names:
            assert row["shaft_length_mm"] == 127.0
            assert row["tip_past_assumed_axis_mm"] == 17.249
            assert row["tip_past_barrel_far_wall_mm"] == 12.2452
            assert row["tip_to_bore_far_cap_clearance_mm"] == -10.2452
            assert row["minimum_added_bore_depth_to_tip_mm"] == 10.2452
        else:
            assert "BEYOND_MODELED_MACHINE_BORE" not in row["nominal_axial_flags"]


def test_all_48_assembled_rows_have_provisional_heads_and_washers(report):
    for role in ("head_absent", "washer_absent"):
        assert report["named_exceptions"][role] == []
    assert all(row["head_present_in_assembly"] for row in report["rows"])
    assert all(row["washer_present_in_assembly"] for row in report["rows"])
