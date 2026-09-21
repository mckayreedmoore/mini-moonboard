"""Family-neutral PB03 geometry collision checks; no design qualification."""

from collections.abc import Mapping
from itertools import product

from scripts import simple_pb03_lower_center_pair as geometry


def _record_hit(hits, key, first, second):
    volume = geometry._intersection_volume(first, second)
    if volume > geometry.TOL_MM3:
        hits[key] = round(volume, 6)


def screen_cross_family(candidate, reference):
    """Check every interaction between two disjoint station collections."""
    if (
        not isinstance(candidate, Mapping)
        or not isinstance(reference, Mapping)
        or not candidate
        or not reference
    ):
        raise ValueError("cross-family station inventories must be nonempty mappings")
    if set(candidate) & set(reference):
        raise ValueError("cross-family station inventories must be disjoint")
    if any(
        name != item.station for name, item in (*candidate.items(), *reference.items())
    ):
        raise ValueError("cross-family station identity changed")
    bore_hits = {}
    block_hits = {}
    stack_block_hits = {}
    stack_component_hits = {}
    tool_block_hits = {}
    tool_stack_hits = {}
    tool_tool_hits = {}

    for first, second in product(candidate.values(), reference.values()):
        _record_hit(
            block_hits,
            f"{first.block_name}|{second.block_name}",
            first.block,
            second.block,
        )
        for first_name, first_bore in first.bores.items():
            for second_name, second_bore in second.bores.items():
                _record_hit(
                    bore_hits,
                    f"{first_name}|{second_name}",
                    first_bore,
                    second_bore,
                )

        for source, opposite in ((first, second), (second, first)):
            for stack_name, components in source.stacks.items():
                for role, component in components.items():
                    _record_hit(
                        stack_block_hits,
                        f"{stack_name}/{role}|{opposite.block_name}",
                        component,
                        opposite.block,
                    )
            for tool_name, ends in source.tools.items():
                for end, tool in ends.items():
                    _record_hit(
                        tool_block_hits,
                        f"{tool_name}/{end}|{opposite.block_name}",
                        tool,
                        opposite.block,
                    )
                    for stack_name, components in opposite.stacks.items():
                        for role, component in components.items():
                            _record_hit(
                                tool_stack_hits,
                                f"{tool_name}/{end}|{stack_name}/{role}",
                                tool,
                                component,
                            )

        for first_name, first_components in first.stacks.items():
            for second_name, second_components in second.stacks.items():
                for first_role, first_component in first_components.items():
                    for second_role, second_component in second_components.items():
                        _record_hit(
                            stack_component_hits,
                            f"{first_name}/{first_role}|{second_name}/{second_role}",
                            first_component,
                            second_component,
                        )
        for first_name, first_ends in first.tools.items():
            for second_name, second_ends in second.tools.items():
                for first_end, first_tool in first_ends.items():
                    for second_end, second_tool in second_ends.items():
                        _record_hit(
                            tool_tool_hits,
                            f"{first_name}/{first_end}|{second_name}/{second_end}",
                            first_tool,
                            second_tool,
                        )

    result = {
        "cross_family_bore_hits_mm3": bore_hits,
        "cross_family_block_hits_mm3": block_hits,
        "cross_family_stack_block_hits_mm3": stack_block_hits,
        "cross_family_stack_component_hits_mm3": stack_component_hits,
        "cross_family_tool_block_hits_mm3": tool_block_hits,
        "cross_family_tool_stack_hits_mm3": tool_stack_hits,
        "cross_family_tool_tool_hits_mm3": tool_tool_hits,
        "tool_tool_overlap_blocks_sequential_installation": False,
    }
    result["all_cross_family_collision_gates_pass"] = not any(
        result[key]
        for key in (
            "cross_family_bore_hits_mm3",
            "cross_family_block_hits_mm3",
            "cross_family_stack_block_hits_mm3",
            "cross_family_stack_component_hits_mm3",
            "cross_family_tool_block_hits_mm3",
            "cross_family_tool_stack_hits_mm3",
        )
    )
    return result
