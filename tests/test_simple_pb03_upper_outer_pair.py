"""PB03 upper outer pair is isolated geometry-development evidence only."""

from dataclasses import replace

import pytest

from scripts import simple_pb03_upper_outer_pair as upper


@pytest.fixture(scope="module")
def pair():
    return upper.build_pair()


def test_pair_uses_actual_kerf_right_upper_outer_members(pair):
    assert tuple(pair) == upper.TARGET_STATIONS
    left, right = (pair[name] for name in upper.TARGET_STATIONS)

    assert left.upright_name == "base_side_left"
    assert right.upright_name == "base_side_right"
    assert left.rail_name == "base_rail_service_upper_left"
    assert right.rail_name == "base_rail_service_upper_right"
    assert left.source_rail_length_mm == pytest.approx(1041.25)
    assert right.source_rail_length_mm == pytest.approx(1038.075)
    assert left.report["butt_faces_x_mm"] == pytest.approx(
        {"upright": -1130.3, "rail": -1130.3}
    )
    assert right.report["butt_faces_x_mm"] == pytest.approx(
        {"upright": 1127.125, "rail": 1127.125}
    )
    assert left.report["butt_faces_coincident"] is True
    assert right.report["butt_faces_coincident"] is True


def test_each_station_has_four_generic_complete_stack_envelopes(pair):
    names = set()
    for geometry in pair.values():
        assert geometry.report["block_dimensions_mm"] == [139.7, 57.15, 300.0]
        assert geometry.report["rail_bore_n_offset_mm"] == pytest.approx(125.0)
        assert len(geometry.bolts) == len(geometry.stacks) == 4
        assert geometry.report["complete_bores"] is True
        assert upper.UPPER_RAIL_N_OFFSET_MM == 125.0
        upright = [
            bolt for bolt in geometry.bolts if bolt.members[0] == geometry.upright_name
        ]
        rail = [
            bolt for bolt in geometry.bolts if bolt.members[0] == geometry.rail_name
        ]
        assert [bolt.grip for bolt in upright] == pytest.approx([228.6, 228.6])
        assert [bolt.grip for bolt in rail] == pytest.approx([95.25, 95.25])
        assert {bolt.kind for bolt in geometry.bolts} == {"bolt"}
        names.update(bolt.name for bolt in geometry.bolts)
    assert len(names) == 8


def test_screen_passes_every_local_and_lower_family_gate_without_release(pair):
    result = upper.screen(pair)

    assert result["inventory"] == {
        "target_legacy_stations": 2,
        "removed_legacy_sds_axes": 12,
        "added_timber_blocks": 2,
        "added_through_bolt_stacks": 8,
        "fixed_panel_kicker_axes": 66,
    }
    assert result["fixed_axes_unchanged"] is True
    assert result["all_fixed_axes_have_positive_receiver_support"] is True
    assert result["all_upper_pair_geometry_gates_pass"] is True
    assert result["all_lower_family_collision_gates_pass"] is True
    assert result["all_geometry_gates_pass"] is True
    assert result["lower_family_bore_hits_mm3"] == {}
    assert result["lower_family_block_hits_mm3"] == {}
    assert result["lower_family_stack_block_hits_mm3"] == {}
    assert result["lower_family_stack_component_hits_mm3"] == {}
    assert result["lower_family_tool_hits_mm3"] == {}
    assert result["same_side_lower_block_clearance_mm"] == pytest.approx(
        {"left": 86.9, "right": 86.9}, abs=1e-6
    )
    assert all(row["contact_verified"] for row in result["stations"].values())
    assert all(row["complete_bores"] for row in result["stations"].values())
    assert all(row["collision_clear"] for row in result["stations"].values())
    assert all(row["access_clear"] for row in result["stations"].values())
    assert result["exact_retail_hardware_selected"] is False
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False


def test_synthetic_upper_to_lower_stack_collision_fails_closed(pair):
    lower = upper.build_lower_reference()
    lower_stack = next(iter(next(iter(lower.values())).stacks.values()))
    right = pair[upper.TARGET_STATIONS[1]]
    stack_name = next(iter(right.stacks))
    changed = {name: dict(parts) for name, parts in right.stacks.items()}
    changed[stack_name]["shaft"] = lower_stack["shaft"]
    altered = dict(pair)
    altered[upper.TARGET_STATIONS[1]] = replace(right, stacks=changed)

    result = upper.screen(altered, lower_reference=lower)

    assert result["lower_family_stack_component_hits_mm3"]
    assert result["all_lower_family_collision_gates_pass"] is False
    assert result["all_geometry_gates_pass"] is False


def test_synthetic_changed_butt_face_fails_during_build():
    parts, finished, panels, stations, connections = upper._source_inventory()
    changed = dict(parts)
    rail_name = "base_rail_service_upper_left"
    changed[rail_name] = changed[rail_name].translate((1.0, 0, 0))

    with pytest.raises(ValueError, match="butt faces changed"):
        upper.build_pair(
            parts=changed,
            finished_parts={**finished, rail_name: changed[rail_name]},
            panel_connections=panels,
            stations=stations,
            connections=connections,
        )
