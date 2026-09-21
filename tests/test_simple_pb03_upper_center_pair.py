"""PB03 upper-center pair is isolated geometry-development evidence only."""

from dataclasses import replace

import pytest

from scripts import simple_pb03_upper_center_pair as upper_center


@pytest.fixture(scope="module")
def pair():
    return upper_center.build_pair()


def test_pair_uses_actual_kerf_right_upper_center_members(pair):
    assert tuple(pair) == upper_center.TARGET_STATIONS
    left, right = (pair[name] for name in upper_center.TARGET_STATIONS)
    assert (left.upright_name, left.rail_name) == (
        "base_principal_center_left",
        "base_rail_service_upper_left",
    )
    assert (right.upright_name, right.rail_name) == (
        "base_principal_center_right",
        "base_rail_service_upper_right",
    )
    assert left.source_rail_length_mm == pytest.approx(1041.25)
    assert right.source_rail_length_mm == pytest.approx(1038.075)
    assert left.report["butt_faces_x_mm"] == pytest.approx(
        {"upright": -89.05, "rail": -89.05}
    )
    assert right.report["butt_faces_x_mm"] == pytest.approx(
        {"upright": 89.05, "rail": 89.05}
    )
    assert left.report["butt_faces_coincident"] is True
    assert right.report["butt_faces_coincident"] is True


def test_each_station_has_full_section_block_and_four_complete_stacks(pair):
    names = set()
    for geometry in pair.values():
        assert geometry.report["block_dimensions_mm"] == [139.7, 57.15, 300.0]
        assert geometry.report["rail_bore_n_offset_mm"] == pytest.approx(125.0)
        assert len(geometry.bolts) == len(geometry.stacks) == 4
        assert geometry.report["complete_bores"] is True
        upright = [
            bolt for bolt in geometry.bolts if bolt.members[0] == geometry.upright_name
        ]
        rail = [
            bolt for bolt in geometry.bolts if bolt.members[0] == geometry.rail_name
        ]
        assert [bolt.grip for bolt in upright] == pytest.approx([177.8, 177.8])
        assert [bolt.grip for bolt in rail] == pytest.approx([95.25, 95.25])
        assert {bolt.kind for bolt in geometry.bolts} == {"bolt"}
        names.update(bolt.name for bolt in geometry.bolts)
    assert len(names) == 8


def test_screen_passes_local_and_all_eight_existing_geometry_gates(pair):
    result = upper_center.screen(pair)

    assert result["reference_station_count"] == 8
    assert result["inventory"] == {
        "target_legacy_stations": 2,
        "removed_legacy_sds_axes": 12,
        "added_timber_blocks": 2,
        "added_through_bolt_stacks": 8,
        "fixed_panel_kicker_axes": 66,
    }
    assert result["fixed_axes_unchanged"] is True
    assert result["all_fixed_axes_have_positive_receiver_support"] is True
    assert result["all_upper_center_pair_geometry_gates_pass"] is True
    assert result["all_cross_family_collision_gates_pass"] is True
    assert result["all_geometry_gates_pass"] is True
    for key in (
        "cross_family_bore_hits_mm3",
        "cross_family_block_hits_mm3",
        "cross_family_stack_block_hits_mm3",
        "cross_family_stack_component_hits_mm3",
        "cross_family_tool_block_hits_mm3",
        "cross_family_tool_stack_hits_mm3",
    ):
        assert result[key] == {}
    assert result["nearest_existing_block_clearance_mm"] == pytest.approx(
        {
            "clip_horizontal_upper_left_2": 86.9,
            "clip_horizontal_upper_right_1": 86.9,
        }
    )
    for key in (
        "cross_station_bore_hits_mm3",
        "cross_station_block_hits_mm3",
        "cross_station_stack_block_hits_mm3",
        "cross_station_stack_component_hits_mm3",
        "cross_station_tool_opposite_hits_mm3",
    ):
        assert result[key] == {}
    assert result["exact_retail_hardware_selected"] is False
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False


def test_synthetic_cross_family_collision_fails_closed(pair):
    references = upper_center.build_existing_reference()
    reference_stack = next(iter(next(iter(references.values())).stacks.values()))
    station_name = upper_center.TARGET_STATIONS[1]
    station = pair[station_name]
    stack_name = next(iter(station.stacks))
    stacks = {name: dict(parts) for name, parts in station.stacks.items()}
    stacks[stack_name]["shaft"] = reference_stack["shaft"]
    changed = {**pair, station_name: replace(station, stacks=stacks)}

    result = upper_center.screen(changed, existing_reference=references)

    assert result["cross_family_stack_component_hits_mm3"]
    assert result["all_cross_family_collision_gates_pass"] is False
    assert result["all_geometry_gates_pass"] is False


def test_incomplete_inventory_and_changed_butt_face_fail_closed():
    parts, finished, panels, stations, connections = upper_center._source_inventory()
    with pytest.raises(ValueError, match="supplied completely"):
        upper_center.build_pair(parts=parts)

    rail_name = "base_rail_service_upper_left"
    changed = {**parts, rail_name: parts[rail_name].translate((1.0, 0, 0))}
    with pytest.raises(ValueError, match="butt faces changed"):
        upper_center.build_pair(
            parts=changed,
            finished_parts={**finished, rail_name: changed[rail_name]},
            panel_connections=panels,
            stations=stations,
            connections=connections,
        )
