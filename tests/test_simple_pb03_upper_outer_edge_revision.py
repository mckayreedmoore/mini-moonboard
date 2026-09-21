"""PB03 upper-outer edge revision stays isolated and development-only."""

import pytest

from scripts import simple_pb03_upper_outer_edge_revision as revision


@pytest.fixture(scope="module")
def result():
    return revision.analyze_revision()


def test_accepted_direction_source_and_feasible_intervals_are_pinned(result):
    assert result["case"] == "a12-forward"
    assert result["report_sha256"] == revision.ACCEPTED_REPORT_SHA256
    assert result["accepted_rail_edge_forces_n"] == pytest.approx(
        {
            "pb03_upper_outer_left_rail_1": -12.937479,
            "pb03_upper_outer_left_rail_2": 12.164866,
            "pb03_upper_outer_right_rail_1": 3.399433,
            "pb03_upper_outer_right_rail_2": 1.689067,
        },
        abs=1.0e-6,
    )
    assert result["feasible_offset_intervals_mm"][0] == pytest.approx(
        [28.4, 51.159], abs=1.0e-6
    )
    assert result["feasible_offset_intervals_mm"][1] == pytest.approx(
        [109.159, 111.3], abs=1.0e-6
    )


def test_selects_smallest_move_from_current_with_three_mm_reserve(result):
    assert result["current_rail_bore_n_offset_mm"] == pytest.approx(125.0)
    assert result["selected_rail_bore_n_offset_mm"] == pytest.approx(111.3)
    assert result["rail_bore_move_mm"] == pytest.approx(-13.7)
    assert result["minimum_clearances_mm"] == pytest.approx(
        {
            "loaded_edge_reserve": 3.0,
            "unloaded_edge_reserve": 18.875,
            "bore_wall_to_rail_edge": 24.65,
            "cross_family_tool_to_stack": 2.141,
            "same_side_lower_block": 86.9,
        },
        abs=1.0e-6,
    )


def test_revision_preserves_every_out_of_scope_geometry(result):
    assert result["inventory"] == {
        "revised_stations": 2,
        "preserved_pb03_stations": 6,
        "total_pb03_stations": 8,
        "total_pb03_bolt_stacks": 32,
        "fixed_panel_kicker_axes": 66,
    }
    assert result["preservation"] == {
        "block_geometry_unchanged": True,
        "upright_bores_unchanged": True,
        "rail_x_offsets_unchanged": True,
        "other_six_pb03_stations_unchanged": True,
        "panel_kicker_axes_unchanged": True,
    }


def test_selected_geometry_and_sequential_tool_paths_clear(result):
    assert result["selected_geometry"]["local_geometry_gates_pass"] is True
    assert result["selected_geometry"]["cross_family_collision_gates_pass"] is True
    assert result["selected_geometry"]["sequential_tool_paths_clear"] is True
    assert result["selected_geometry"]["blocking_collision_hits"] == {}
    assert result["selected_geometry"]["tool_tool_overlap_is_nonblocking"] is True
    assert result["selected_geometry"]["tool_tool_overlap_count"] == 4
    assert result["geometry_revision_passes"] is True


def test_revision_never_claims_hardware_or_structural_release(result):
    assert result["remaining_gates"] == [
        "integrate the revised pair into the active PB03 candidate",
        "rerun and authenticate the native frame cases after integration",
        "complete same-case resistance, group, splitting, and member checks",
        "select exact retail bolts, nuts, and washers for every grip",
        "integrate and resistance-check the isolated eight-inch-bolt counterbores",
        "review tolerances and issue an explicit fabrication decision",
    ]
    assert result["exact_retail_hardware_selected"] is False
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
