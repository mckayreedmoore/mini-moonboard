"""Detached PB03 upper-outer loaded-edge revision; no integration or release."""

import hashlib
import json
import math
from pathlib import Path

import cadquery as cq

from scripts import simple_pb03_bottom_outer_pair as bottom
from scripts import simple_pb03_cross_family as cross_family
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_upper_outer_pair as upper
from scripts import simple_rail_joint_comparison as pb01

ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_REPORT = ROOT / (
    "fea/results/diagnostics/pb03-eight-station-a12-forward-v1/attempts/"
    "a12-forward-01-all-unseeded/report.json"
)
ACCEPTED_REPORT_SHA256 = (
    "a2f203541c52cff205e432d4043c722c0b1df4cfc3b850c2fae4dbae9688c93e"
)
BOLT_DIAMETER_MM = lower.BOLT_DIAMETER_MM
BORE_DIAMETER_MM = lower.BORE_DIAMETER_MM
RAIL_DEPTH_MM = lower.BLOCK_X_MM
LOADED_EDGE_REQUIREMENT_MM = 4 * BOLT_DIAMETER_MM
UNLOADED_EDGE_REQUIREMENT_MM = 1.5 * BOLT_DIAMETER_MM
MINIMUM_RESERVE_MM = 3.0
CURRENT_OFFSET_MM = upper.UPPER_RAIL_N_OFFSET_MM
SELECTED_OFFSET_MM = RAIL_DEPTH_MM - LOADED_EDGE_REQUIREMENT_MM - MINIMUM_RESERVE_MM
LOWER_OUTER_OFFSET_MM = lower.RAIL_N_OFFSET_MM
TOOL_TO_STACK_RADIAL_CLEARANCE_MM = (
    lower.TOOL_DIAMETER_MM + lower.HEAD_NUT_DIAMETER_MM
) / 2
TARGET_STATIONS = (
    *lower.ALL_TARGET_STATIONS,
    *upper.TARGET_STATIONS,
    *bottom.TARGET_STATIONS,
)


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _accepted_edge_forces():
    """Recover the four accepted host-side rail forces along the rail N axis."""
    if _sha256(ACCEPTED_REPORT) != ACCEPTED_REPORT_SHA256:
        raise ValueError("accepted PB03 a12-forward report SHA-256 changed")
    report = json.loads(ACCEPTED_REPORT.read_text())
    if (
        report.get("numerically_accepted") is not True
        or report.get("global_equilibrium_passed") is not True
        or report.get("member_equilibrium_passed") is not True
        or report.get("diagnostic_scope", {}).get("case") != "a12-forward"
    ):
        raise ValueError("PB03 a12-forward report is not accepted evidence")
    names = {
        f"pb03_upper_outer_{side}_rail_{index}"
        for side in ("left", "right")
        for index in (1, 2)
    }
    physical = report.get("physical_connection_forces", {})
    if not names <= set(physical):
        raise ValueError("accepted PB03 upper-outer rail force inventory changed")
    edge_axis = (0.0, *pb01.N)
    return {
        name: math.fsum(
            value * axis
            for value, axis in zip(
                physical[name]["force_on_first_xyz_n"], edge_axis, strict=True
            )
        )
        for name in sorted(names)
    }


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
    if not math.isfinite(offset_mm) or not 0 <= offset_mm <= RAIL_DEPTH_MM:
        raise ValueError("PB03 rail-bore N offset must lie within the rail depth")
    parts, panels, kwargs = _source()
    fixed_axes = lower._fixed_axis_solids(panels)
    revised = {
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
        **lower.build_core_slice(**kwargs),
        **revised,
        **bottom.build_pair(**kwargs),
    }
    if tuple(geometries) != TARGET_STATIONS:
        raise ValueError("PB03 upper-edge revision station inventory changed")
    return geometries


def build_baseline_geometries():
    """Build the unchanged active eight-station geometry for comparison only."""
    return _build(CURRENT_OFFSET_MM)


def build_geometries(offset_mm=SELECTED_OFFSET_MM):
    """Build a detached copy with only the two upper rail-bore rows shifted."""
    return _build(offset_mm)


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


def _preservation(candidate, baseline):
    inward = cq.Vector(0.0, *pb01.N) * (SELECTED_OFFSET_MM - CURRENT_OFFSET_MM)
    blocks_same = True
    upright_same = True
    rail_x_same = True
    other_six_same = True
    for name in TARGET_STATIONS:
        revised = candidate[name]
        original = baseline[name]
        blocks_same = blocks_same and (
            revised.block.distance(original.block) <= 1.0e-8
            and math.isclose(
                revised.block.Volume(), original.block.Volume(), abs_tol=1.0e-6
            )
        )
        if name not in upper.TARGET_STATIONS:
            other_six_same = other_six_same and all(
                _bolt_metadata_same(new, old) and _same_vector(new.start, old.start)
                for new, old in zip(revised.bolts, original.bolts, strict=True)
            )
            continue
        for new, old in zip(revised.bolts, original.bolts, strict=True):
            if not _bolt_metadata_same(new, old):
                return {}
            move = new.start - old.start
            if "_rail_" in new.name:
                rail_x_same = rail_x_same and math.isclose(
                    new.start.toTuple()[0], old.start.toTuple()[0], abs_tol=1.0e-9
                )
                rail_x_same = rail_x_same and _same_vector(move, inward)
            else:
                upright_same = upright_same and _same_vector(move, (0, 0, 0))
    return {
        "block_geometry_unchanged": blocks_same,
        "upright_bores_unchanged": upright_same,
        "rail_x_offsets_unchanged": rail_x_same,
        "other_six_pb03_stations_unchanged": other_six_same,
        "panel_kicker_axes_unchanged": True,
    }


def _edge_rows(edge_forces, offset_mm):
    rows = []
    for name, force in edge_forces.items():
        if math.isclose(force, 0.0, abs_tol=1.0e-9):
            raise ValueError(f"{name}: accepted edge-force direction is neutral")
        loaded = RAIL_DEPTH_MM - offset_mm if force > 0 else offset_mm
        unloaded = offset_mm if force > 0 else RAIL_DEPTH_MM - offset_mm
        rows.append(
            {
                "bolt": name,
                "accepted_edge_force_n": force,
                "loaded_edge_distance_mm": loaded,
                "loaded_edge_reserve_mm": loaded - LOADED_EDGE_REQUIREMENT_MM,
                "unloaded_edge_distance_mm": unloaded,
                "unloaded_edge_reserve_mm": unloaded - UNLOADED_EDGE_REQUIREMENT_MM,
            }
        )
    return rows


def _feasible_offset_intervals(edge_forces):
    """Partition the full rail depth at every edge and collision boundary."""
    low = BORE_DIAMETER_MM / 2
    high = RAIL_DEPTH_MM - BORE_DIAMETER_MM / 2
    for force in edge_forces.values():
        required = LOADED_EDGE_REQUIREMENT_MM + MINIMUM_RESERVE_MM
        if force > 0:
            high = min(high, RAIL_DEPTH_MM - required)
        else:
            low = max(low, required)
    blocked_low = LOWER_OUTER_OFFSET_MM - TOOL_TO_STACK_RADIAL_CLEARANCE_MM
    blocked_high = LOWER_OUTER_OFFSET_MM + TOOL_TO_STACK_RADIAL_CLEARANCE_MM
    candidates = ((low, min(high, blocked_low)), (max(low, blocked_high), high))
    return [
        [round(start, 6), round(end, 6)] for start, end in candidates if end >= start
    ]


def _blocking_hits(local, cross):
    keys = (
        "cross_family_bore_hits_mm3",
        "cross_family_block_hits_mm3",
        "cross_family_stack_block_hits_mm3",
        "cross_family_stack_component_hits_mm3",
        "cross_family_tool_block_hits_mm3",
        "cross_family_tool_stack_hits_mm3",
    )
    hits = {key: cross[key] for key in keys if cross[key]}
    if not local["all_geometry_gates_pass"]:
        hits["local_or_eight_station_gate"] = True
    return hits


def analyze_revision():
    """Return the bounded interval search and exact selected-geometry screen."""
    edge_forces = _accepted_edge_forces()
    intervals = _feasible_offset_intervals(edge_forces)
    selected = build_geometries()
    baseline = build_baseline_geometries()
    revised_pair = {name: selected[name] for name in upper.TARGET_STATIONS}
    other_six = {
        name: geometry
        for name, geometry in selected.items()
        if name not in upper.TARGET_STATIONS
    }
    local = lower._screen_targets(
        selected, TARGET_STATIONS, "simple_pb03_upper_outer_edge_revision/v1"
    )
    cross = cross_family.screen_cross_family(revised_pair, other_six)
    blocking_hits = _blocking_hits(local, cross)
    rows = _edge_rows(edge_forces, SELECTED_OFFSET_MM)
    preservation = _preservation(selected, baseline)
    preservation["panel_kicker_axes_unchanged"] = local["fixed_axes_unchanged"]
    same_side_clearances = [
        selected[upper.TARGET_STATIONS[index]].block.distance(
            selected[lower.LOWER_OUTER_STATIONS[index]].block
        )
        for index in range(2)
    ]
    clearances = {
        "loaded_edge_reserve": min(row["loaded_edge_reserve_mm"] for row in rows),
        "unloaded_edge_reserve": min(row["unloaded_edge_reserve_mm"] for row in rows),
        "bore_wall_to_rail_edge": min(
            min(row["loaded_edge_distance_mm"], row["unloaded_edge_distance_mm"])
            - BORE_DIAMETER_MM / 2
            for row in rows
        ),
        "cross_family_tool_to_stack": abs(SELECTED_OFFSET_MM - LOWER_OUTER_OFFSET_MM)
        - TOOL_TO_STACK_RADIAL_CLEARANCE_MM,
        "same_side_lower_block": min(same_side_clearances),
    }
    selected_geometry = {
        "local_geometry_gates_pass": local["all_geometry_gates_pass"],
        "cross_family_collision_gates_pass": cross[
            "all_cross_family_collision_gates_pass"
        ],
        "sequential_tool_paths_clear": not blocking_hits,
        "blocking_collision_hits": blocking_hits,
        "tool_tool_overlap_is_nonblocking": cross[
            "tool_tool_overlap_blocks_sequential_installation"
        ]
        is False,
        "tool_tool_overlap_count": len(cross["cross_family_tool_tool_hits_mm3"]),
    }
    gates = (
        any(
            math.isclose(SELECTED_OFFSET_MM, end, abs_tol=1.0e-9)
            for _, end in intervals
        )
        and min(clearances.values()) >= -1.0e-8
        and all(preservation.values())
        and all(
            selected_geometry[key]
            for key in (
                "local_geometry_gates_pass",
                "cross_family_collision_gates_pass",
                "sequential_tool_paths_clear",
            )
        )
    )
    return {
        "schema": "simple_pb03_upper_outer_edge_revision/v1",
        "case": "a12-forward",
        "report_sha256": ACCEPTED_REPORT_SHA256,
        "accepted_rail_edge_forces_n": edge_forces,
        "search_domain_mm": [0.0, RAIL_DEPTH_MM],
        "search_basis": (
            "Exact partition at bore-wall, directional 4D-plus-3-mm, and "
            "existing lower-outer tool/stack tangency boundaries; selected "
            "geometry checked in CAD without changing the 1 mm^3 collision gate."
        ),
        "feasible_offset_intervals_mm": intervals,
        "current_rail_bore_n_offset_mm": CURRENT_OFFSET_MM,
        "selected_rail_bore_n_offset_mm": SELECTED_OFFSET_MM,
        "rail_bore_move_mm": SELECTED_OFFSET_MM - CURRENT_OFFSET_MM,
        "edge_direction_rows": rows,
        "minimum_clearances_mm": clearances,
        "inventory": {
            "revised_stations": 2,
            "preserved_pb03_stations": 6,
            "total_pb03_stations": 8,
            "total_pb03_bolt_stacks": sum(
                len(geometry.bolts) for geometry in selected.values()
            ),
            "fixed_panel_kicker_axes": 66,
        },
        "preservation": preservation,
        "selected_geometry": selected_geometry,
        "geometry_revision_passes": gates,
        "remaining_gates": [
            "integrate the revised pair into the active PB03 candidate",
            "rerun and authenticate the native frame cases after integration",
            "complete same-case resistance, group, splitting, and member checks",
            "select exact retail bolts, nuts, and washers for every grip",
            "integrate and resistance-check the isolated eight-inch-bolt counterbores",
            "review tolerances and issue an explicit fabrication decision",
        ],
        "active_pb03_integrated": False,
        "exact_retail_hardware_selected": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(analyze_revision(), indent=2, sort_keys=True))
