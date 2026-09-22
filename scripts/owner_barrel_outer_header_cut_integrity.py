"""Detached nominal cut-solid screen for four recessed outer-header bolt rows.

Only intended header/post hosts are cut. Viewer solids and source fastener axes
remain unmodified; Boolean connectedness is not a wood-strength calculation.
"""

import json
from math import inf

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import export_owner_barrel_scene as viewer
from scripts import owner_layout_protected as protected

SCHEMA = "owner_barrel_outer_header_cut_integrity/v1"
SIDES = ("left", "right")
ROLES = ("counterbore", "machine_bore", "barrel_bore")
HIT_TOL_MM3 = 1.0


def _axis_key(row):
    return (
        row.name,
        tuple(row.start.toTuple()),
        tuple(row.direction.toTuple()),
        row.length,
        row.diameter,
        tuple(row.members),
    )


def _fixed_axes_unchanged(assembly):
    source = variant(KERF_RIGHT)
    panel = tuple(source.panel_connections())
    frame = tuple(row for row in source.connections() if row.kind == "bolt")
    if (
        len(panel) != 66
        or len(frame) != 12
        or tuple(map(_axis_key, assembly["panel_connections"]))
        != tuple(map(_axis_key, panel))
        or tuple(map(_axis_key, assembly["frame_connections"]))
        != tuple(map(_axis_key, frame))
    ):
        raise ValueError("Fixed 66/12 source axes changed")


def _rows(assembly):
    """Require the exact current viewer rows, and assign paths to hosts."""
    paths = assembly["drilling_paths"]
    rows = {}
    for side in SIDES:
        station = f"clip_timber_header_outer_{side}"
        prefixes = sorted(
            name
            for name, owner in assembly["barrel_station"].items()
            if owner == station
        )
        if len(prefixes) != 2:
            raise ValueError(f"{station}: expected two barrel rows")
        for index, prefix in enumerate(prefixes, 1):
            bolt = f"{prefix}_bolt"
            expected_prefix = f"barrel_trial_{station}_{index}"
            expected_paths = {f"{prefix}/{role}" for role in ROLES}
            actual_paths = {name for name in paths if name.startswith(f"{prefix}/")}
            if (
                prefix != expected_prefix
                or assembly["bolt_station"].get(bolt) != station
                or actual_paths != expected_paths
                or set(assembly["stacks"][bolt]) != {"shaft", "washer", "head"}
            ):
                raise ValueError(f"{station}: outer-header path inventory changed")
            rows[prefix] = {
                "station": station,
                "side": side,
                "paths": {role: paths[f"{prefix}/{role}"] for role in ROLES},
            }
    if len(rows) != 4:
        raise ValueError("Outer-header row inventory changed")
    return rows


def _radial_residuals(host, cutter, role):
    """Axis-aligned modeled edge stock; excludes penetrated entry/exit faces."""
    wood, path = host.BoundingBox(), cutter.BoundingBox()
    dimensions = ("y", "z") if role == "barrel_bore" else ("x", "y")
    return {
        f"{axis}_minus": round(
            getattr(path, f"{axis}min") - getattr(wood, f"{axis}min"), 6
        )
        for axis in dimensions
    } | {
        f"{axis}_plus": round(
            getattr(wood, f"{axis}max") - getattr(path, f"{axis}max"), 6
        )
        for axis in dimensions
    }


def _bounds_gap(first, second):
    return (
        sum(
            max(
                getattr(first, f"{axis}min") - getattr(second, f"{axis}max"),
                getattr(second, f"{axis}min") - getattr(first, f"{axis}max"),
                0.0,
            )
            ** 2
            for axis in "xyz"
        )
        ** 0.5
    )


def _axis_proximity(removed, fixed):
    """Exact nearest finite-axis distance, plus nontrivial solid intersections."""
    result = {}
    removed_box = removed.BoundingBox()
    for family in ("panel_screws", "frame_bolts"):
        axes = fixed["solids"][family]
        boxes = fixed["bounds"][family]
        ranked = sorted((_bounds_gap(removed_box, boxes[name]), name) for name in axes)
        nearest_distance, nearest_name = inf, None
        intersections = {}
        for lower_bound, name in ranked:
            axis = axes[name]
            if lower_bound <= nearest_distance:
                distance = removed.distance(axis)
                if distance < nearest_distance:
                    nearest_distance, nearest_name = distance, name
            if lower_bound == 0:
                volume = protected._volume(removed, axis, removed_box, boxes[name])
                if volume > HIT_TOL_MM3:
                    intersections[name] = round(volume, 6)
        if nearest_name is None:
            raise ValueError(f"No fixed {family} axis to compare")
        result[family] = {
            "nearest": {
                "name": nearest_name,
                "distance_mm": round(nearest_distance, 6),
            },
            "intersections_mm3": intersections,
        }
    return result


def _member(name, wood, assigned, fixed):
    uncut = wood[name]
    cut = uncut
    path_rows = []
    for prefix, side, role, cutter in assigned:
        clipped = cutter.intersect(uncut)
        host_intersection = clipped.Volume()
        if host_intersection <= HIT_TOL_MM3:
            raise ValueError(f"{name}: intended {prefix}/{role} misses host")
        before = cut.Volume()
        cut = cut.cut(clipped)
        residuals = _radial_residuals(uncut, cutter, role)
        path_rows.append(
            {
                "path": f"{prefix}/{role}",
                "side": side,
                "role": role,
                "host_intersection_mm3": round(host_intersection, 6),
                "incremental_removed_mm3": round(before - cut.Volume(), 6),
                "radial_edge_residuals_mm": residuals,
                "closed_end_residual_mm": round(
                    cutter.BoundingBox().zmin - uncut.BoundingBox().zmin, 6
                )
                if role == "counterbore"
                or (role == "machine_bore" and name != "base_header")
                else None,
            }
        )
    removed = uncut.cut(cut)
    if abs((uncut.Volume() - cut.Volume()) - removed.Volume()) > 0.1:
        raise ValueError(
            f"{name}: Boolean volume conservation failed: "
            f"delta={uncut.Volume() - cut.Volume():.6f}, "
            f"removed={removed.Volume():.6f}"
        )
    radial = [
        margin
        for row in path_rows
        for margin in row["radial_edge_residuals_mm"].values()
    ]
    return {
        "uncut_volume_mm3": round(uncut.Volume(), 6),
        "cut_volume_mm3": round(cut.Volume(), 6),
        "removed_volume_mm3": round(removed.Volume(), 6),
        "uncut_solid_count": len(uncut.Solids()),
        "cut_solid_count": len(cut.Solids()),
        "cut_is_valid": cut.isValid(),
        "intended_paths": path_rows,
        "minimum_modeled_radial_edge_residual_mm": min(radial),
        "counterbore_floor_residual_mm": min(
            (
                row["closed_end_residual_mm"]
                for row in path_rows
                if row["role"] == "counterbore"
            ),
            default=None,
        ),
        "fixed_axis_proximity": _axis_proximity(removed, fixed),
        "disposition": "REVISE",
        "clearance_approved": False,
    }


def probe(*, assembly=None):
    """Cut copies of three wood solids only; preserve the complete viewer."""
    assembly = viewer.build_viewer_assembly() if assembly is None else assembly
    _fixed_axes_unchanged(assembly)
    if any(assembly["release_flags"].values()):
        raise ValueError("Current viewer unexpectedly carries release approval")
    rows = _rows(assembly)
    wood = assembly["wood"]
    host_names = {"base_header", *(f"base_post_outer_{side}" for side in SIDES)}
    if not host_names <= set(wood):
        raise ValueError("Outer-header timber inventory changed")
    assigned = {name: [] for name in host_names}
    for prefix, row in rows.items():
        side, paths = row["side"], row["paths"]
        for role in ("counterbore", "machine_bore"):
            assigned["base_header"].append((prefix, side, role, paths[role]))
        for role in ("barrel_bore", "machine_bore"):
            assigned[f"base_post_outer_{side}"].append(
                (prefix, side, role, paths[role])
            )
    fixed = protected.inventory()
    members = {
        name: _member(name, wood, assigned[name], fixed) for name in sorted(host_names)
    }
    return {
        "schema": SCHEMA,
        "source_assembly": "export_owner_barrel_scene.build_viewer_assembly",
        "baseline": "compact-floor-flush-kerf-right",
        "inventory": {
            "stations": 2,
            "bolt_rows": len(rows),
            "fixed_panel_screws": len(assembly["panel_connections"]),
            "retained_frame_bolts": len(assembly["frame_connections"]),
        },
        "members": members,
        "disposition": "REVISE",
        "clearance_approved": False,
        "release_flags": dict(assembly["release_flags"]),
        "cutting_or_drilling_released": False,
        "limits": (
            "Nominal Boolean subtraction only. Connectedness is not strength, edge-distance "
            "acceptance, splitting resistance, washer bearing, barrel resistance, service "
            "access, tolerance validation, or a drilling instruction. Fixed axes are "
            "preserved, not removed. All release gates remain false."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
