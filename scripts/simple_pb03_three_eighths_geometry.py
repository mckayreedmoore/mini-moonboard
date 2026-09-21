"""Isolated 3/8-inch rescreen of the eight integrated PB03 stations; no release."""

import math
from itertools import combinations

import cadquery as cq

from scripts import simple_pb03_bottom_outer_pair as bottom
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_upper_outer_pair as upper

BOLT_DIAMETER_MM = 9.525
BORE_DIAMETER_MM = 11.1125
TARGET_STATIONS = (
    *lower.ALL_TARGET_STATIONS,
    *upper.TARGET_STATIONS,
    *bottom.TARGET_STATIONS,
)
COLLISION_RESULT_KEYS = (
    "block_unrelated_timber_hits_mm3",
    "block_finished_panel_hits_mm3",
    "block_fixed_axis_hits_mm3",
    "bore_unrelated_timber_hits_mm3",
    "bore_finished_panel_hits_mm3",
    "bore_fixed_axis_hits_mm3",
    "same_station_bore_hits_mm3",
    "stack_unrelated_timber_hits_mm3",
    "stack_finished_panel_hits_mm3",
    "stack_fixed_axis_hits_mm3",
    "tool_unrelated_timber_hits_mm3",
    "tool_finished_panel_hits_mm3",
    "tool_fixed_axis_hits_mm3",
    "tool_intended_host_intrusion_mm3",
    "cross_station_bore_hits_mm3",
    "cross_station_block_hits_mm3",
    "cross_station_stack_block_hits_mm3",
    "cross_station_stack_component_hits_mm3",
    "cross_station_tool_opposite_hits_mm3",
    "tool_tool_overlaps_mm3",
)
BLOCKING_COLLISION_RESULT_KEYS = tuple(
    key for key in COLLISION_RESULT_KEYS if key != "tool_tool_overlaps_mm3"
)


def _source_inventory():
    return lower._source_inventory()


def _station_declarations():
    return (
        *(
            (name, lower.STATION_SPECS[name], lower.RAIL_N_OFFSET_MM)
            for name in lower.ALL_TARGET_STATIONS
        ),
        *(
            (name, upper.STATION_SPECS[name], upper.UPPER_RAIL_N_OFFSET_MM)
            for name in upper.TARGET_STATIONS
        ),
        *(
            (name, bottom.STATION_SPECS[name], bottom.RAIL_N_OFFSET_MM)
            for name in bottom.TARGET_STATIONS
        ),
    )


def _build_with_diameters(bolt_diameter_mm, bore_diameter_mm):
    parts, finished, panels, stations, connections = _source_inventory()
    station_names = {row[0] for row in stations}
    target_sds = [
        row
        for row in connections
        if any(row.name.startswith(f"{name}_") for name in TARGET_STATIONS)
    ]
    if (
        lower.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT
        or len(station_names) != 22
        or not set(TARGET_STATIONS) <= station_names
        or len(target_sds) != 48
        or any(row.kind != "screw" for row in target_sds)
        or len(panels) != 66
        or len({row.name for row in panels}) != 66
        or set(parts) != set(finished)
    ):
        raise ValueError("PB03 3/8-inch source inventory changed")
    fixed_axes = lower._fixed_axis_solids(panels)
    geometries = {
        name: lower._build_station(
            spec,
            parts,
            finished,
            fixed_axes,
            rail_n_offset_mm=rail_offset,
            bolt_diameter_mm=bolt_diameter_mm,
            bore_diameter_mm=bore_diameter_mm,
        )
        for name, spec, rail_offset in _station_declarations()
    }
    if tuple(geometries) != TARGET_STATIONS:
        raise ValueError("PB03 3/8-inch station order changed")
    return geometries


def build_geometries():
    """Build a detached candidate copy without changing PB03Native or its viewer."""
    return _build_with_diameters(BOLT_DIAMETER_MM, BORE_DIAMETER_MM)


def _same_vector(first, second):
    return all(
        math.isclose(left, right, abs_tol=1.0e-8)
        for left, right in zip(
            cq.Vector(first).toTuple(), cq.Vector(second).toTuple(), strict=True
        )
    )


def _layout_preserved(candidate):
    reference = _build_with_diameters(lower.BOLT_DIAMETER_MM, lower.BORE_DIAMETER_MM)
    if tuple(candidate) != tuple(reference):
        return False
    for name, geometry in candidate.items():
        baseline = reference[name]
        if (
            geometry.block_name != baseline.block_name
            or geometry.report["block_dimensions_mm"]
            != baseline.report["block_dimensions_mm"]
            or geometry.report["rail_bore_n_offset_mm"]
            != baseline.report["rail_bore_n_offset_mm"]
            or geometry.block.distance(baseline.block) > 1.0e-8
            or not math.isclose(
                geometry.block.Volume(), baseline.block.Volume(), abs_tol=1.0e-6
            )
            or len(geometry.bolts) != len(baseline.bolts)
        ):
            return False
        for bolt, original in zip(geometry.bolts, baseline.bolts, strict=True):
            if (
                bolt.name != original.name
                or bolt.members != original.members
                or not _same_vector(bolt.start, original.start)
                or not _same_vector(bolt.direction, original.direction)
                or not math.isclose(bolt.length, original.length, abs_tol=1.0e-9)
                or not math.isclose(bolt.grip, original.grip, abs_tol=1.0e-9)
            ):
                return False
    return True


def _merge_station_hits(rows, key):
    merged = {}
    for station, row in rows.items():
        value = row[key]
        for name, hits in value.items():
            if isinstance(hits, dict):
                for detail, volume in hits.items():
                    if isinstance(volume, dict):
                        for leaf, amount in volume.items():
                            merged[f"{station}/{name}/{detail}/{leaf}"] = amount
                    else:
                        merged[f"{station}/{name}/{detail}"] = volume
            else:
                merged[f"{station}/{name}"] = hits
    return merged


def _member_distances(shape, point, grain, bolt_direction):
    grain = grain.normalized()
    bolt_direction = bolt_direction.normalized()
    if abs(grain.dot(bolt_direction)) > 1.0e-8:
        raise ValueError("PB03 edge/end screen requires bolts normal to member grain")
    edge = grain.cross(bolt_direction).normalized()
    grain_positions = [vertex.Center().dot(grain) for vertex in shape.Vertices()]
    edge_positions = [vertex.Center().dot(edge) for vertex in shape.Vertices()]
    point_grain = point.dot(grain)
    point_edge = point.dot(edge)
    return {
        "end_centerline_distances_mm": (
            point_grain - min(grain_positions),
            max(grain_positions) - point_grain,
        ),
        "edge_centerline_distances_mm": (
            point_edge - min(edge_positions),
            max(edge_positions) - point_edge,
        ),
    }


def _edge_end_rows(geometries):
    parts, _, _, _, _ = _source_inventory()
    rows = []
    block_grain = cq.Vector(0.0, *lower.pb01.N)
    for geometry in geometries.values():
        shapes = {**parts, geometry.block_name: geometry.block}
        for bolt in geometry.bolts:
            point = cq.Vector(bolt.start)
            for member in bolt.members:
                grain = (
                    block_grain
                    if member == geometry.block_name
                    else (cq.Vector(1, 0, 0) if "rail_" in member else block_grain)
                )
                distances = _member_distances(
                    shapes[member], point, grain, cq.Vector(bolt.direction)
                )
                end_min = min(distances["end_centerline_distances_mm"])
                edge_min = min(distances["edge_centerline_distances_mm"])
                rows.append(
                    {
                        "station": geometry.station,
                        "bolt": bolt.name,
                        "member": member,
                        **distances,
                        "minimum_end_centerline_mm": end_min,
                        "minimum_edge_centerline_mm": edge_min,
                        "minimum_bore_wall_clearance_mm": min(end_min, edge_min)
                        - BORE_DIAMETER_MM / 2,
                        "unloaded_end_margin_mm": end_min - 4 * BOLT_DIAMETER_MM,
                        "unloaded_edge_margin_mm": edge_min - 1.5 * BOLT_DIAMETER_MM,
                        "loaded_end_margin_mm": end_min - 7 * BOLT_DIAMETER_MM,
                        "loaded_edge_margin_mm": edge_min - 4 * BOLT_DIAMETER_MM,
                    }
                )
    return rows


def _tool_tool_overlaps(geometries):
    tools = [
        (f"{geometry.station}/{bolt_name}/{end}", shape)
        for geometry in geometries.values()
        for bolt_name, ends in geometry.tools.items()
        for end, shape in ends.items()
    ]
    hits = {}
    for (first_name, first), (second_name, second) in combinations(tools, 2):
        volume = lower._intersection_volume(first, second)
        if volume > lower.TOL_MM3:
            hits[f"{first_name}|{second_name}"] = round(volume, 6)
    return hits


def screen(geometries=None):
    """Fail closed on geometry while retaining unresolved load-direction gates."""
    geometries = build_geometries() if geometries is None else geometries
    if tuple(geometries) != TARGET_STATIONS:
        raise ValueError("PB03 3/8-inch screen requires the exact eight stations")
    if any(
        not math.isclose(bolt.diameter, BOLT_DIAMETER_MM, abs_tol=1.0e-9)
        or not math.isclose(
            geometry.report.get("bore_diameter_mm", math.nan),
            BORE_DIAMETER_MM,
            abs_tol=1.0e-9,
        )
        for geometry in geometries.values()
        for bolt in geometry.bolts
    ):
        raise ValueError("PB03 3/8-inch shaft or bore diameter changed")

    base = lower._screen_targets(
        geometries, TARGET_STATIONS, "simple_pb03_three_eighths_geometry/v1"
    )
    rows = base["stations"]
    collisions = {
        key: base[key]
        if key.startswith("cross_station_")
        else _merge_station_hits(rows, key)
        for key in BLOCKING_COLLISION_RESULT_KEYS
    }
    collisions["tool_tool_overlaps_mm3"] = _tool_tool_overlaps(geometries)
    edge_end = _edge_end_rows(geometries)
    governing = min(edge_end, key=lambda row: row["minimum_bore_wall_clearance_mm"])
    unloaded_pass = all(
        row["unloaded_end_margin_mm"] >= -1.0e-8
        and row["unloaded_edge_margin_mm"] >= -1.0e-8
        for row in edge_end
    )
    collision_pass = base["all_geometry_gates_pass"] and not any(
        collisions[key] for key in BLOCKING_COLLISION_RESULT_KEYS
    )
    layout_pass = _layout_preserved(geometries)
    result = {
        "schema": "simple_pb03_three_eighths_geometry/v1",
        "source_pb02_fingerprint": lower.ACTIVE_FINGERPRINT,
        "candidate_bolt_diameter_mm": BOLT_DIAMETER_MM,
        "candidate_bore_diameter_mm": BORE_DIAMETER_MM,
        "inventory": {
            "stations": len(geometries),
            "blocks": len({item.block_name for item in geometries.values()}),
            "bolt_stacks": sum(len(item.stacks) for item in geometries.values()),
            "fixed_panel_kicker_axes": 66,
        },
        **collisions,
        "edge_end_rows": edge_end,
        "governing_clearance": {
            "kind": "bore_wall_to_member_edge",
            "station": governing["station"],
            "bolt": governing["bolt"],
            "member": governing["member"],
            "clearance_mm": governing["minimum_bore_wall_clearance_mm"],
        },
        "governing_unloaded_edge_margin_mm": min(
            row["unloaded_edge_margin_mm"] for row in edge_end
        ),
        "governing_loaded_edge_margin_mm": min(
            row["loaded_edge_margin_mm"] for row in edge_end
        ),
        "all_edge_end_unloaded_minima_pass": unloaded_pass,
        "loaded_edge_end_directions_assigned": False,
        "loaded_edge_end_qualification": False,
        "all_local_and_cross_family_collision_gates_pass": collision_pass,
        "exact_offsets_blocks_preserved": layout_pass,
        "fixed_axes_unchanged": base["fixed_axes_unchanged"],
        "tool_tool_overlap_blocks_sequential_installation": False,
        "exact_retail_hardware_selected": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    result["all_geometry_gates_pass"] = (
        collision_pass
        and unloaded_pass
        and layout_pass
        and result["fixed_axes_unchanged"]
    )
    return result


if __name__ == "__main__":
    import json

    print(json.dumps(screen(), indent=2, sort_keys=True))
