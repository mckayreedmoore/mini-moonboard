"""PB03 lower-center pair is a bounded, non-releasing CAD slice."""

from dataclasses import replace

import pytest

from scripts import simple_pb03_lower_center_pair as pb03
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT
from scripts.simple_pb03_lower_center_pair import (
    BLOCK_LENGTH_MM,
    BLOCK_NAMES,
    TARGET_STATIONS,
    build_pair,
    screen,
)


@pytest.fixture(scope="module")
def pair():
    return build_pair()


def test_pair_is_built_independently_from_actual_kerf_right_members(pair):
    assert tuple(pair) == TARGET_STATIONS
    left, right = (pair[name] for name in TARGET_STATIONS)

    assert left.side == "left"
    assert right.side == "right"
    assert left.rail_name == "base_rail_service_lower_left"
    assert right.rail_name == "base_rail_service_lower_right"
    assert left.upright_name == "base_principal_center_left"
    assert right.upright_name == "base_principal_center_right"
    assert left.block_name == BLOCK_NAMES[TARGET_STATIONS[0]]
    assert right.block_name == BLOCK_NAMES[TARGET_STATIONS[1]]
    assert left.source_rail_length_mm == pytest.approx(1041.25)
    assert right.source_rail_length_mm == pytest.approx(1038.075)
    assert left.source_rail_length_mm - right.source_rail_length_mm == pytest.approx(
        3.175
    )
    assert left.block_length_mm == right.block_length_mm == BLOCK_LENGTH_MM == 300.0
    assert left.block.Center().x < 0 < right.block.Center().x


def test_each_station_has_four_complete_unselected_through_bolt_stacks(pair):
    names = set()
    for station in pair.values():
        assert len(station.bolts) == len(station.stacks) == 4
        assert {bolt.kind for bolt in station.bolts} == {"bolt"}
        assert {bolt.diameter for bolt in station.bolts} == {6.35}
        for bolt in station.bolts:
            names.add(bolt.name)
            assert bolt.name in station.stacks
            assert tuple(station.stacks[bolt.name]) == (
                "shaft",
                "head",
                "near_washer",
                "far_washer",
                "nut",
            )
            assert len(bolt.components()) == 5
    assert len(names) == 8


def test_pair_screen_passes_all_geometry_gates_without_release(pair):
    result = screen(pair)

    assert result["pb02_source_fingerprint"] == ACTIVE_FINGERPRINT
    assert result["target_stations"] == list(TARGET_STATIONS)
    assert result["inventory"] == {
        "target_legacy_stations": 2,
        "removed_legacy_sds_axes": 12,
        "added_timber_blocks": 2,
        "added_through_bolt_stacks": 8,
        "fixed_panel_kicker_axes": 66,
    }
    assert result["all_geometry_gates_pass"] is True
    assert result["fixed_axes_unchanged"] is True
    assert result["all_fixed_axes_have_positive_receiver_support"] is True
    assert all(row["contact_verified"] for row in result["stations"].values())
    assert all(row["complete_bores"] for row in result["stations"].values())
    assert all(row["collision_clear"] for row in result["stations"].values())
    assert all(row["access_clear"] for row in result["stations"].values())
    assert result["all_bore_pairs_clear"] is True
    assert result["cross_station_bore_hits_mm3"] == {}
    assert result["cross_station_block_hits_mm3"] == {}
    assert result["cross_station_stack_block_hits_mm3"] == {}
    assert result["cross_station_stack_component_hits_mm3"] == {}
    assert result["cross_station_tool_opposite_hits_mm3"] == {}
    assert result["all_eight_stacks_mutually_clear"] is True
    assert result["all_cross_station_access_paths_clear"] is True
    for row in result["stations"].values():
        assert row["block_finished_panel_hits_mm3"] == {}
        assert not any(row["bore_finished_panel_hits_mm3"].values())
        assert not any(row["bore_unrelated_timber_hits_mm3"].values())
        assert not any(row["same_station_bore_hits_mm3"].values())
        assert not any(
            any(hits.values())
            for hits in row["tool_intended_host_intrusion_mm3"].values()
        )
        assert row["tool_seat_paths_clear"] is True
    assert result["exact_retail_hardware_selected"] is False
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False


def _build_with_finished_change(change):
    parts, finished, panels, stations, connections = pb03._source_inventory()
    changed = dict(finished)
    change(changed)
    return build_pair(
        parts=parts,
        finished_parts=changed,
        panel_connections=panels,
        stations=stations,
        connections=connections,
    )


def test_synthetic_finished_panel_collision_is_rejected(pair):
    left = pair[TARGET_STATIONS[0]]
    altered = _build_with_finished_change(
        lambda finished: finished.__setitem__("main_lower_left", left.block)
    )
    result = screen(altered)
    row = result["stations"][TARGET_STATIONS[0]]

    assert row["block_finished_panel_hits_mm3"]["main_lower_left"] > 0
    assert row["collision_clear"] is False
    assert result["all_geometry_gates_pass"] is False


def test_synthetic_unrelated_timber_bore_collision_is_rejected(pair):
    left = pair[TARGET_STATIONS[0]]
    bore = next(iter(left.bores.values()))
    altered = _build_with_finished_change(
        lambda finished: finished.__setitem__("base_rail_service_upper_left", bore)
    )
    result = screen(altered)
    row = result["stations"][TARGET_STATIONS[0]]

    assert any(
        hits.get("base_rail_service_upper_left", 0) > 0
        for hits in row["bore_unrelated_timber_hits_mm3"].values()
    )
    assert row["collision_clear"] is False
    assert result["all_geometry_gates_pass"] is False


def test_synthetic_bore_to_bore_collision_is_rejected(monkeypatch):
    monkeypatch.setattr(pb03, "UPRIGHT_N_OFFSETS_MM", (55.159, 55.159))
    altered = build_pair()
    result = screen(altered)
    row = result["stations"][TARGET_STATIONS[0]]

    assert any(row["same_station_bore_hits_mm3"].values())
    assert result["all_bore_pairs_clear"] is False
    assert result["all_geometry_gates_pass"] is False


def test_synthetic_cross_station_stack_collision_is_rejected(pair):
    left, right = (pair[name] for name in TARGET_STATIONS)
    left_stack = next(iter(left.stacks.values()))
    right_name = next(iter(right.stacks))
    changed_stacks = {
        name: dict(components) for name, components in right.stacks.items()
    }
    changed_stacks[right_name]["shaft"] = left_stack["shaft"]
    altered = dict(pair)
    altered[TARGET_STATIONS[1]] = replace(right, stacks=changed_stacks)

    result = screen(altered)

    assert result["cross_station_stack_component_hits_mm3"]
    assert result["all_eight_stacks_mutually_clear"] is False
    assert result["all_geometry_gates_pass"] is False
