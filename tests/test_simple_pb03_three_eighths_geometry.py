"""Bounded 3/8-inch PB03 geometry rescreen; never an active-design release."""

from dataclasses import replace

import pytest

from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_three_eighths_geometry as rescreen


@pytest.fixture(scope="module")
def geometries():
    return rescreen.build_geometries()


@pytest.fixture(scope="module")
def result(geometries):
    return rescreen.screen(geometries)


def test_existing_pb03_defaults_are_unchanged():
    pair = lower.build_pair()
    for geometry in pair.values():
        assert geometry.report["bolt_diameter_mm"] == pytest.approx(6.35)
        assert geometry.report["bore_diameter_mm"] == pytest.approx(7.5)
        assert {bolt.diameter for bolt in geometry.bolts} == {6.35}


def test_builds_only_the_eight_integrated_stations_at_candidate_diameters(geometries):
    assert tuple(geometries) == rescreen.TARGET_STATIONS
    assert len(geometries) == 8
    assert sum(len(item.bolts) for item in geometries.values()) == 32
    assert {bolt.diameter for item in geometries.values() for bolt in item.bolts} == {
        rescreen.BOLT_DIAMETER_MM
    }
    assert all(
        item.report["bore_diameter_mm"] == pytest.approx(rescreen.BORE_DIAMETER_MM)
        for item in geometries.values()
    )


def test_rescreen_preserves_layout_and_passes_bounded_geometry_gates(result):
    assert result["inventory"] == {
        "stations": 8,
        "blocks": 8,
        "bolt_stacks": 32,
        "fixed_panel_kicker_axes": 66,
    }
    assert result["exact_offsets_blocks_preserved"] is True
    assert result["fixed_axes_unchanged"] is True
    assert result["all_local_and_cross_family_collision_gates_pass"] is True
    assert result["all_edge_end_unloaded_minima_pass"] is True
    assert result["all_geometry_gates_pass"] is True
    assert result["governing_clearance"]["kind"] == "bore_wall_to_member_edge"
    assert result["governing_clearance"]["clearance_mm"] == pytest.approx(9.14375)
    assert result["governing_unloaded_edge_margin_mm"] == pytest.approx(0.4125)
    assert result["governing_loaded_edge_margin_mm"] == pytest.approx(-23.4)


def test_rescreen_records_every_collision_family_and_stays_non_releasing(result):
    for key in rescreen.COLLISION_RESULT_KEYS:
        assert result[key] == {}
    assert result["loaded_edge_end_directions_assigned"] is False
    assert result["loaded_edge_end_qualification"] is False
    assert result["exact_retail_hardware_selected"] is False
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False


def test_invalid_diameter_and_synthetic_collision_fail_closed(geometries):
    with pytest.raises(ValueError, match="positive bore larger"):
        lower.build_pair(bolt_diameter_mm=9.525, bore_diameter_mm=9.525)

    first_name, second_name = rescreen.TARGET_STATIONS[:2]
    first = geometries[first_name]
    second = geometries[second_name]
    stack_name = next(iter(second.stacks))
    stacks = {name: dict(parts) for name, parts in second.stacks.items()}
    stacks[stack_name]["shaft"] = next(iter(first.stacks.values()))["shaft"]
    changed = {**geometries, second_name: replace(second, stacks=stacks)}

    changed_result = rescreen.screen(changed)

    assert changed_result["cross_station_stack_component_hits_mm3"]
    assert changed_result["all_geometry_gates_pass"] is False
