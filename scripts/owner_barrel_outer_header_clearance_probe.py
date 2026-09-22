"""Bounded, detached outer-header/post barrel poses; geometry is not a drill plan."""

import json
from itertools import combinations

import cadquery as cq

from scripts import owner_barrel_outer_top_layout as producer
from scripts import owner_layout_protected as protected
from scripts import simple_cross_dowel_continuation as hardware
from scripts import simple_owner_duty_ledger as ledger
from scripts.owner_barrel_layout_assembly import build_assembly

SCHEMA = "owner_barrel_outer_header_clearance_probe/v1"
STATIONS = {
    "left": "clip_timber_header_outer_left",
    "right": "clip_timber_header_outer_right",
}
TOL = protected.HIT_TOL_MM3
WASHER_OD_MM = 19.05  # Provisional trial envelope; not verified Hillman/retail fit.
HEAD_ENVELOPE_D_MM = 13.0  # Diagnostic circular hex-head envelope only.
HEAD_ENVELOPE_H_MM = 5.0
ACCESS_D_MM = 20.0
ACCESS_REACH_MM = 40.0
NOMINAL_EDGE_RESERVE_MM = 3.75  # Half provisional 7.5-mm machine bore.


def _cylinder(start, direction, length, diameter):
    return cq.Solid.makeCylinder(diameter / 2, length, start, direction)


def _hits(shape, targets):
    return {
        name: round(volume, 6)
        for name, target in targets.items()
        if (volume := protected._volume(shape, target)) > TOL
    }


def _other_station_solids(assembly, station):
    physical = {
        f"barrel/{name}": shape
        for name, shape in assembly["barrels"].items()
        if assembly["barrel_station"][name] != station
    }
    physical.update(
        {
            f"bolt/{name}/{role}": shape
            for name, roles in assembly["stacks"].items()
            if assembly["bolt_station"][name] != station
            for role, shape in roles.items()
        }
    )
    prefix = f"barrel_trial_{station}_"
    paths = {
        f"drill/{name}": shape
        for name, shape in assembly["drilling_paths"].items()
        if not name.startswith(prefix)
    }
    paths.update(
        {
            f"access/{name}": shape
            for name, shape in assembly["access_paths"].items()
            if not name.startswith(prefix)
        }
    )
    return physical, paths


def _poses(side, post, rim):
    pb, rb = post.BoundingBox(), rim.BoundingBox()
    xmid = (pb.xmin + pb.xmax) / 2
    inner = pb.xmax if side == "left" else pb.xmin
    rim_inner = rb.xmax if side == "left" else rb.xmin
    sign = 1 if side == "left" else -1
    yield "baseline", "vertical_top", xmid, xmid, (-135.0, -75.0), 70.0
    for y_pair in ((-145.0, -85.0), (-125.0, -65.0)):
        for x_offset in (-8.0, 0.0, 8.0):
            yield (
                f"top_y{int(-y_pair[0])}_{int(-y_pair[1])}_x{int(x_offset)}",
                "vertical_top",
                xmid + x_offset,
                xmid + x_offset,
                y_pair,
                70.0,
            )
    for depth in (45.0, 70.0):
        for axis_x, label in ((xmid, "mid"), (inner - sign * 12.0, "inner12")):
            yield (
                f"oblique_depth{int(depth)}_{label}",
                "oblique_top_inboard",
                rim_inner + sign * 10.0,
                axis_x,
                (-135.0, -75.0),
                depth,
            )
    yield "bottom_5in", "vertical_bottom", xmid, xmid, (-135.0, -75.0), 0.0


def _row_geometry(side, orientation, seat_x, axis_x, y, depth, wood):
    post_name = f"base_post_outer_{side}"
    post, header = wood[post_name], wood["base_header"]
    pb, hb = post.BoundingBox(), header.BoundingBox()
    if orientation == "vertical_bottom":
        seat = cq.Vector(seat_x, y, pb.zmin)
        axis = cq.Vector(axis_x, y, (hb.zmin + hb.zmax) / 2)
        barrel_host = header
        barrel_entry_x = hb.xmin if side == "left" else hb.xmax
    else:
        seat = cq.Vector(seat_x, y, hb.zmax)
        axis = cq.Vector(axis_x, y, pb.zmax - depth)
        barrel_host = post
        barrel_entry_x = pb.xmin if side == "left" else pb.xmax
    direction = (axis - seat).normalized()
    outward = -direction
    washer_t = hardware.WASHER_THICKNESS_SENSITIVITY_MM
    shaft_start = seat + outward * washer_t
    barrel_entry = cq.Vector(barrel_entry_x, y, axis.z)
    barrel_dir = (axis - barrel_entry).normalized()
    barrel_start = axis - barrel_dir * (hardware.BARREL_LENGTH_MM / 2)
    barrel_recess = (barrel_start - barrel_entry).dot(barrel_dir)
    reach = hardware.BOLT_LENGTH_MM - washer_t
    shaft = _cylinder(
        shaft_start, direction, hardware.BOLT_LENGTH_MM, hardware.THREAD_MAJOR_MM
    )
    machine = _cylinder(seat, direction, reach, producer.MACHINE_BORE_D_MM)
    barrel = _cylinder(
        barrel_start, barrel_dir, hardware.BARREL_LENGTH_MM, hardware.BARREL_OD_MM
    )
    cross = _cylinder(
        barrel_entry,
        barrel_dir,
        barrel_recess + hardware.BARREL_LENGTH_MM,
        hardware.BARREL_OD_MM,
    )
    washer = _cylinder(seat, outward, washer_t, WASHER_OD_MM)
    head = _cylinder(shaft_start, outward, HEAD_ENVELOPE_H_MM, HEAD_ENVELOPE_D_MM)
    bolt_access = _cylinder(seat, outward, ACCESS_REACH_MM, ACCESS_D_MM)
    barrel_access = _cylinder(barrel_entry, -barrel_dir, ACCESS_REACH_MM, ACCESS_D_MM)
    paths = {
        "machine_bore": machine,
        "barrel_bore": cross,
        "bolt_access": bolt_access,
        "barrel_access": barrel_access,
    }
    physical = {"shaft": shaft, "barrel": barrel, "washer": washer, "head": head}
    # A line crossing the actual butt plane outside the post is not a post/header bolt.
    fraction = (pb.zmax - seat.z) / (axis.z - seat.z)
    seam_x = seat.x + fraction * (axis.x - seat.x)
    seam_y = seat.y + fraction * (axis.y - seat.y)
    seam_inside = (
        pb.xmin + NOMINAL_EDGE_RESERVE_MM <= seam_x <= pb.xmax - NOMINAL_EDGE_RESERVE_MM
        and pb.ymin + NOMINAL_EDGE_RESERVE_MM
        <= seam_y
        <= pb.ymax - NOMINAL_EDGE_RESERVE_MM
    )
    hosts = (post, header)
    coverage = (
        sum(protected._volume(machine, host) for host in hosts) / machine.Volume()
    )
    body_contained = (
        abs(protected._volume(barrel, barrel_host) - barrel.Volume()) <= TOL
    )
    return {
        "seat_xyz_mm": [round(v, 4) for v in seat.toTuple()],
        "axis_xyz_mm": [round(v, 4) for v in axis.toTuple()],
        "seam_x_mm": round(seam_x, 4),
        "seam_inside_post": seam_inside,
        "bolt_reach_past_axis_mm": round(reach - (axis - seat).Length, 4),
        "machine_bore_meets_barrel_mm3": round(protected._volume(machine, barrel), 6),
        "machine_wood_coverage": round(coverage, 6),
        "barrel_body_contained": body_contained,
        "barrel_recess_mm": round(barrel_recess, 4),
        "physical": physical,
        "paths": paths,
    }


def _screen_pose(side, pose, wood, fixed, other_physical, other_paths):
    label, orientation, seat_x, axis_x, y_pair, depth = pose
    station = STATIONS[side]
    post_name = f"base_post_outer_{side}"
    rim_name = f"base_side_{side}"
    unrelated = {
        name: shape
        for name, shape in wood.items()
        if name not in (post_name, "base_header")
    }
    rows = []
    physical, paths = {}, {}
    for index, y in enumerate(y_pair, 1):
        row = _row_geometry(side, orientation, seat_x, axis_x, y, depth, wood)
        shapes = {**row["physical"], **row["paths"]}
        fixed_hits = {
            key: hits for key, hits in protected.hits(shapes, fixed).items() if hits
        }
        wood_hits = {
            key: hits
            for key, shape in shapes.items()
            if (hits := _hits(shape, unrelated))
        }
        row["protected_hits_mm3"] = fixed_hits
        row["unrelated_wood_hits_mm3"] = wood_hits
        for kind, shape in row["physical"].items():
            physical[f"row{index}/{kind}"] = shape
        for kind, shape in row["paths"].items():
            paths[f"row{index}/{kind}"] = shape
        del row["physical"], row["paths"]
        rows.append(row)
    internal_hits = {}
    for first, second in combinations((1, 2), 2):
        first_p = {k: v for k, v in physical.items() if k.startswith(f"row{first}/")}
        second_p = {k: v for k, v in physical.items() if k.startswith(f"row{second}/")}
        first_paths = {k: v for k, v in paths.items() if k.startswith(f"row{first}/")}
        second_paths = {k: v for k, v in paths.items() if k.startswith(f"row{second}/")}
        for name, shape in {**first_p, **first_paths}.items():
            internal_hits.update(
                {
                    f"{name}|{target}": volume
                    for target, volume in _hits(shape, second_p).items()
                }
            )
        for name, shape in second_paths.items():
            internal_hits.update(
                {
                    f"{name}|{target}": volume
                    for target, volume in _hits(shape, first_p).items()
                }
            )
    other_physical_hits = {
        name: hits
        for name, shape in {**physical, **paths}.items()
        if (hits := _hits(shape, other_physical))
    }
    other_path_hits = {
        name: hits
        for name, shape in physical.items()
        if (hits := _hits(shape, other_paths))
    }
    gates = {
        "seam_in_post": all(row["seam_inside_post"] for row in rows),
        "bolt_reaches_barrel": all(row["bolt_reach_past_axis_mm"] >= 0 for row in rows),
        "bore_meets_barrel": all(
            row["machine_bore_meets_barrel_mm3"] > TOL for row in rows
        ),
        "source_wood_coverage": all(
            row["machine_wood_coverage"] >= 0.999 for row in rows
        ),
        "barrel_contained": all(
            row["barrel_body_contained"] and row["barrel_recess_mm"] >= 0
            for row in rows
        ),
        "unrelated_wood": not any(row["unrelated_wood_hits_mm3"] for row in rows),
        "protected_inventory": not any(row["protected_hits_mm3"] for row in rows),
        "inter_row": not internal_hits,
        "other_trial_physical": not other_physical_hits,
        "other_trial_paths": not other_path_hits,
        # An oblique bolt needs an angled bearing seat absent from the exact wood.
        "square_head_seat": orientation != "oblique_top_inboard",
    }
    return {
        "side": side,
        "station": station,
        "pose": label,
        "orientation": orientation,
        "seat_x_mm": round(seat_x, 4),
        "axis_x_mm": round(axis_x, 4),
        "row_y_mm": list(y_pair),
        "axis_depth_below_post_top_mm": depth
        if orientation != "vertical_bottom"
        else None,
        "rows": rows,
        "shaft_side_rim_hits_mm3": [
            row["unrelated_wood_hits_mm3"].get("shaft", {}).get(rim_name, 0.0)
            for row in rows
        ],
        "access_side_rim_hits_mm3": [
            row["unrelated_wood_hits_mm3"].get("bolt_access", {}).get(rim_name, 0.0)
            for row in rows
        ],
        "inter_row_hits_mm3": internal_hits,
        "other_trial_physical_hits_mm3": other_physical_hits,
        "other_trial_path_hits_mm3": other_path_hits,
        "failed_gates": [name for name, passed in gates.items() if not passed],
        "geometry_gates_clear": all(gates.values()),
    }


def search():
    """Evaluate a fixed, reproducible pose grid on exact assembled owner wood."""
    assembly = build_assembly()
    wood, fixed = assembly["wood"], protected.inventory()
    if (
        len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
    ):
        raise ValueError("Owner's fixed screw/bolt inventory changed")
    duties = ledger.selected_duties()
    if any(
        duties[station]["timber"] != ("base_header", f"base_post_outer_{side}")
        for side, station in STATIONS.items()
    ):
        raise ValueError("Outer-header duty members changed")
    candidates = []
    for side, station in STATIONS.items():
        other_physical, other_paths = _other_station_solids(assembly, station)
        for pose in _poses(
            side, wood[f"base_post_outer_{side}"], wood[f"base_side_{side}"]
        ):
            candidates.append(
                _screen_pose(side, pose, wood, fixed, other_physical, other_paths)
            )
    clear = [
        f"{row['side']}/{row['pose']}"
        for row in candidates
        if row["geometry_gates_clear"]
    ]
    return {
        "schema": SCHEMA,
        "source": producer.SOURCE_ID,
        "wood_basis": assembly["diagnostics"]["wood_basis"],
        "sides": list(STATIONS),
        "candidate_count": len(candidates),
        "panel_screw_axes_preserved": 66,
        "retained_frame_bolt_axes_preserved": 12,
        "protected_inventory_counts": fixed["counts"],
        "candidates": candidates,
        "geometry_clear_poses": clear,
        "limits": "Finite nominal envelopes only; no delivered head/washer/tool, thread, tolerances, insertion sequence, wood resistance, or joint forces qualified",
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(search(), indent=2))
