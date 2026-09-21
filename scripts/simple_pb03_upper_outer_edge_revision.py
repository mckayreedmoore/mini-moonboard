"""Detached PB03 upper-outer loaded-edge revision; geometry only, no release."""

import math

import cadquery as cq

from scripts import simple_pb03_bottom_outer_pair as bottom
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_three_eighths_geometry as edge_geometry
from scripts import simple_pb03_upper_outer_pair as upper
from scripts import simple_rail_joint_comparison as pb01

BOLT_DIAMETER_MM = lower.BOLT_DIAMETER_MM
LOADED_EDGE_REQUIREMENT_MM = 4 * BOLT_DIAMETER_MM
MINIMUM_RESERVE_MM = 3.0
NOMINAL_UPPER_RAIL_N_OFFSET_MM = upper.UPPER_RAIL_N_OFFSET_MM
REVISED_UPPER_RAIL_N_OFFSET_MM = 111.3
INWARD_SHIFT_MM = NOMINAL_UPPER_RAIL_N_OFFSET_MM - REVISED_UPPER_RAIL_N_OFFSET_MM
TARGET_STATIONS = (
    *lower.ALL_TARGET_STATIONS,
    *upper.TARGET_STATIONS,
    *bottom.TARGET_STATIONS,
)


def _source():
    parts, finished, panels, stations, connections = lower._source_inventory()
    kwargs = {
        "parts": parts,
        "finished_parts": finished,
        "panel_connections": panels,
        "stations": stations,
        "connections": connections,
    }
    return parts, panels, kwargs


def _build(offset_mm):
    parts, panels, kwargs = _source()
    lower_geometries = lower.build_core_slice(**kwargs)
    # Calling the existing builder retains its complete source authentication.
    nominal_upper = upper.build_pair(**kwargs)
    if math.isclose(offset_mm, NOMINAL_UPPER_RAIL_N_OFFSET_MM, abs_tol=1.0e-9):
        upper_geometries = nominal_upper
    else:
        fixed_axes = lower._fixed_axis_solids(panels)
        upper_geometries = {
            name: lower._build_station(
                upper.STATION_SPECS[name],
                parts,
                kwargs["finished_parts"],
                fixed_axes,
                rail_n_offset_mm=offset_mm,
            )
            for name in upper.TARGET_STATIONS
        }
    geometries = {
        **lower_geometries,
        **upper_geometries,
        **bottom.build_pair(**kwargs),
    }
    if tuple(geometries) != TARGET_STATIONS:
        raise ValueError("PB03 upper-edge revision station inventory changed")
    return geometries


def build_baseline_geometries():
    """Build the unchanged active eight-station geometry for comparison only."""
    return _build(NOMINAL_UPPER_RAIL_N_OFFSET_MM)


def build_geometries():
    """Build a detached copy with only the two upper rail bore rows shifted."""
    return _build(REVISED_UPPER_RAIL_N_OFFSET_MM)


def _same_vector(first, second):
    return (cq.Vector(first) - cq.Vector(second)).Length <= 1.0e-8


def _bolt_metadata_same(first, second):
    return (
        first.name == second.name
        and first.members == second.members
        and first.kind == second.kind
        and _same_vector(first.direction, second.direction)
        and math.isclose(first.length, second.length, abs_tol=1.0e-9)
        and math.isclose(first.diameter, second.diameter, abs_tol=1.0e-9)
        and math.isclose(first.grip, second.grip, abs_tol=1.0e-9)
    )


def _only_requested_axes_moved(candidate, baseline):
    inward = cq.Vector(0.0, *pb01.N) * -INWARD_SHIFT_MM
    for name in TARGET_STATIONS:
        revised = candidate[name]
        original = baseline[name]
        if (
            revised.block_name != original.block_name
            or revised.report["block_dimensions_mm"]
            != original.report["block_dimensions_mm"]
            or revised.block.distance(original.block) > 1.0e-8
            or not math.isclose(
                revised.block.Volume(), original.block.Volume(), abs_tol=1.0e-6
            )
        ):
            return False
        for bolt, old_bolt in zip(revised.bolts, original.bolts, strict=True):
            if not _bolt_metadata_same(bolt, old_bolt):
                return False
            expected_move = (
                inward
                if name in upper.TARGET_STATIONS and "_rail_" in bolt.name
                else cq.Vector(0, 0, 0)
            )
            if not _same_vector(bolt.start - old_bolt.start, expected_move):
                return False
    return True


def _upper_rail_edge_rows(geometries):
    parts, _, _ = _source()
    rows = []
    for name in upper.TARGET_STATIONS:
        geometry = geometries[name]
        rail = parts[geometry.rail_name]
        for bolt in geometry.bolts:
            if bolt.members[0] != geometry.rail_name:
                continue
            distances = edge_geometry._member_distances(
                rail,
                cq.Vector(bolt.start),
                cq.Vector(1, 0, 0),
                cq.Vector(bolt.direction),
            )
            spacing = min(distances["edge_centerline_distances_mm"])
            rows.append(
                {
                    "station": name,
                    "bolt": bolt.name,
                    "edge_spacing_mm": spacing,
                    "loaded_edge_requirement_mm": LOADED_EDGE_REQUIREMENT_MM,
                    "loaded_edge_margin_mm": spacing - LOADED_EDGE_REQUIREMENT_MM,
                }
            )
    if len(rows) != 4:
        raise ValueError("PB03 upper-edge revision requires four upper rail bolts")
    return rows


def screen(geometries=None):
    """Screen the exact detached revision against all eight PB03 stations."""
    geometries = build_geometries() if geometries is None else geometries
    if tuple(geometries) != TARGET_STATIONS:
        raise ValueError("PB03 upper-edge revision requires the exact eight stations")
    if any(
        not math.isclose(
            geometries[name].report["rail_bore_n_offset_mm"],
            REVISED_UPPER_RAIL_N_OFFSET_MM,
            abs_tol=1.0e-9,
        )
        for name in upper.TARGET_STATIONS
    ):
        raise ValueError("PB03 revised upper rail offset changed")

    base = lower._screen_targets(
        geometries, TARGET_STATIONS, "simple_pb03_upper_outer_edge_revision/v1"
    )
    edge_rows = _upper_rail_edge_rows(geometries)
    governing_spacing = min(row["edge_spacing_mm"] for row in edge_rows)
    governing_margin = min(row["loaded_edge_margin_mm"] for row in edge_rows)
    reserve_pass = governing_margin >= MINIMUM_RESERVE_MM - 1.0e-8
    preservation_pass = _only_requested_axes_moved(
        geometries, build_baseline_geometries()
    )
    collision_pass = base["all_geometry_gates_pass"]
    result = {
        **base,
        "schema": "simple_pb03_upper_outer_edge_revision/v1",
        "nominal_upper_rail_n_offset_mm": NOMINAL_UPPER_RAIL_N_OFFSET_MM,
        "revised_upper_rail_n_offset_mm": REVISED_UPPER_RAIL_N_OFFSET_MM,
        "inward_shift_mm": INWARD_SHIFT_MM,
        "loaded_edge_requirement_mm": LOADED_EDGE_REQUIREMENT_MM,
        "minimum_requested_reserve_mm": MINIMUM_RESERVE_MM,
        "upper_rail_edge_rows": edge_rows,
        "governing_upper_rail_edge_spacing_mm": governing_spacing,
        "governing_upper_rail_loaded_edge_margin_mm": governing_margin,
        "all_upper_rail_loaded_edge_reserves_pass": reserve_pass,
        "only_two_upper_outer_rail_rows_shifted": preservation_pass,
        "all_local_and_cross_family_collision_gates_pass": collision_pass,
        "active_pb03_integrated": False,
        "exact_retail_hardware_selected": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    result["all_geometry_gates_pass"] = (
        collision_pass
        and reserve_pass
        and preservation_pass
        and result["fixed_axes_unchanged"]
    )
    return result


if __name__ == "__main__":
    import json

    print(json.dumps(screen(), indent=2, sort_keys=True))
