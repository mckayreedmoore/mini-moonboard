"""Generic PB03 cross-family collision screening."""

from dataclasses import replace

import cadquery as cq
import pytest

from scripts import simple_pb03_cross_family as cross
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_upper_outer_pair as upper


def test_clear_existing_families_report_every_interaction_class():
    result = cross.screen_cross_family(upper.build_pair(), lower.build_core_slice())

    assert result == {
        "cross_family_bore_hits_mm3": {},
        "cross_family_block_hits_mm3": {},
        "cross_family_stack_block_hits_mm3": {},
        "cross_family_stack_component_hits_mm3": {},
        "cross_family_tool_block_hits_mm3": {},
        "cross_family_tool_stack_hits_mm3": {},
        "cross_family_tool_tool_hits_mm3": {},
        "tool_tool_overlap_blocks_sequential_installation": False,
        "all_cross_family_collision_gates_pass": True,
    }


def test_synthetic_collisions_cover_every_geometry_interaction_class():
    candidate = upper.build_pair()
    references = lower.build_core_slice()
    reference_station = next(iter(references.values()))
    reference_bore = next(iter(reference_station.bores.values()))
    reference_stack = next(iter(reference_station.stacks.values()))
    reference_tool = next(iter(next(iter(reference_station.tools.values())).values()))
    station_name = upper.TARGET_STATIONS[1]
    station = candidate[station_name]
    bore_name = next(iter(station.bores))
    stack_name = next(iter(station.stacks))
    tool_name = next(iter(station.tools))
    tool_end = next(iter(station.tools[tool_name]))
    bores = dict(station.bores)
    bores[bore_name] = reference_bore
    stacks = {name: dict(parts) for name, parts in station.stacks.items()}
    stacks[stack_name]["shaft"] = reference_stack["shaft"]
    tools = {name: dict(ends) for name, ends in station.tools.items()}
    tools[tool_name][tool_end] = cq.Compound.makeCompound(
        [reference_station.block, reference_stack["shaft"], reference_tool]
    )
    changed = {
        **candidate,
        station_name: replace(
            station,
            block=reference_station.block,
            bores=bores,
            stacks=stacks,
            tools=tools,
        ),
    }

    result = cross.screen_cross_family(changed, references)

    for key in (
        "cross_family_bore_hits_mm3",
        "cross_family_block_hits_mm3",
        "cross_family_stack_block_hits_mm3",
        "cross_family_stack_component_hits_mm3",
        "cross_family_tool_block_hits_mm3",
        "cross_family_tool_stack_hits_mm3",
        "cross_family_tool_tool_hits_mm3",
    ):
        assert result[key], key
    assert result["all_cross_family_collision_gates_pass"] is False


def test_empty_overlapping_and_misidentified_families_fail_closed():
    candidate = upper.build_pair()
    references = lower.build_core_slice()

    with pytest.raises(ValueError, match="nonempty"):
        cross.screen_cross_family({}, references)
    with pytest.raises(ValueError, match="disjoint"):
        cross.screen_cross_family(candidate, candidate)
    wrong_name = {"wrong": next(iter(candidate.values()))}
    with pytest.raises(ValueError, match="identity"):
        cross.screen_cross_family(wrong_name, references)


def test_tool_sweeps_may_overlap_when_installations_are_sequential():
    candidate = upper.build_pair()
    references = lower.build_core_slice()
    shared_tool = cq.Solid.makeCylinder(
        10.0, 20.0, cq.Vector(10000.0, 10000.0, 10000.0)
    )

    def with_shared_tool(items):
        name, item = next(iter(items.items()))
        tool_name = next(iter(item.tools))
        end = next(iter(item.tools[tool_name]))
        tools = {key: dict(value) for key, value in item.tools.items()}
        tools[tool_name][end] = shared_tool
        return {**items, name: replace(item, tools=tools)}

    result = cross.screen_cross_family(
        with_shared_tool(candidate), with_shared_tool(references)
    )

    assert result["cross_family_tool_tool_hits_mm3"]
    assert result["cross_family_tool_block_hits_mm3"] == {}
    assert result["cross_family_tool_stack_hits_mm3"] == {}
    assert result["tool_tool_overlap_blocks_sequential_installation"] is False
    assert result["all_cross_family_collision_gates_pass"] is True
