"""One 1/4-in, wider-cleat geometry trial; no structural capacity verdict."""

import csv
import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.simple_center_post_transfer_probe import (
    AXES,
    PROFILES,
    TOL,
    bounds,
    frame,
    hit_volume,
)

BOLT_DIAMETER = 6.35
BORE_RADIUS = 3.65  # 7.30 mm illustrative hole, 0.95 mm over nominal shank.
SEAT_RADIUS = 12.5  # Diagnostic front pocket; hardware not selected.
REMOVED_STATIONS = (
    "clip_split_base_center_right",
    "clip_split_header_center_right",
)


def probe():
    """Measure the sole adjusted pose and expose its conditional 4D failure."""
    parts = {part.name: part.shape for part in frame.uncut_wood_parts()}
    post = parts.pop("base_post_center_right").translate(cq.Vector(37.8, 0, 0))
    backer = cq.Solid.makeBox(139.7, 88.9, 238.9, cq.Vector(-50.95, -124.9, 0))
    rear = cq.Solid.makeBox(50.8, 38.1, 460, cq.Vector(89.05, -213.8, 0))
    side = cq.Solid.makeBox(50.8, 56.8, 183, cq.Vector(89.05, -175.7, 277))
    parts.update(
        shifted_right_post=post, backer=backer, rear_cleat=rear, upright_side_cleat=side
    )

    legacy_stations = tuple(
        station for station in frame.stations() if station[0] in REMOVED_STATIONS
    )
    assert {station[0] for station in legacy_stations} == set(REMOVED_STATIONS)
    legacy_clips = {
        part.name: part.shape for part in frame.hardware.clip_parts(legacy_stations)
    }
    legacy_clip_hits = {}
    legacy_screw_hits = {}
    new_names = ("shifted_right_post", "rear_cleat", "upright_side_cleat")
    for name in new_names:
        for clip_name, clip in legacy_clips.items():
            volume = hit_volume(parts[name], clip)
            if volume > TOL:
                legacy_clip_hits[f"{name}/{clip_name}"] = round(volume, 5)
    for connection in frame.connections():
        if not any(connection.name.startswith(name + "_") for name in REMOVED_STATIONS):
            continue
        shaft, head = connection.components()
        for name in new_names:
            volume = hit_volume(parts[name], shaft.fuse(head))
            if volume > TOL:
                legacy_screw_hits[f"{name}/{connection.name}"] = round(volume, 5)

    bores = {
        "post_low": cq.Solid.makeCylinder(
            BORE_RADIUS, 167.8, cq.Vector(107.8, -213.8, 110), cq.Vector(0, 1, 0)
        ),
        "post_high": cq.Solid.makeCylinder(
            BORE_RADIUS, 167.8, cq.Vector(107.8, -213.8, 190), cq.Vector(0, 1, 0)
        ),
        "upright": cq.Solid.makeCylinder(
            BORE_RADIUS, 88.9, cq.Vector(50.95, -147.3, 350), cq.Vector(1, 0, 0)
        ),
        "cleat_link": cq.Solid.makeCylinder(
            BORE_RADIUS, 94.9, cq.Vector(114.45, -213.8, 370), cq.Vector(0, 1, 0)
        ),
    }
    seats = {
        name: cq.Solid.makeCylinder(
            SEAT_RADIUS, 10, cq.Vector(107.8, -46, z), cq.Vector(0, 1, 0)
        )
        for name, z in (("post_low", 110), ("post_high", 190))
    }
    intended = {
        "post_low": {"shifted_right_post", "rear_cleat"},
        "post_high": {"shifted_right_post", "rear_cleat"},
        "upright": {"base_principal_center_right", "upright_side_cleat"},
        "cleat_link": {"rear_cleat", "upright_side_cleat"},
    }
    received = {}
    unintended = {}
    for name, bore in bores.items():
        received[name] = round(
            sum(hit_volume(bore, parts[wood]) for wood in intended[name])
            / bore.Volume(),
            8,
        )
        for wood_name, wood in parts.items():
            if wood_name in intended[name]:
                continue
            volume = hit_volume(bore, wood)
            if volume > TOL:
                unintended[f"{name}/{wood_name}"] = round(volume, 5)
    bore_pairs = {}
    for i, (name, bore) in enumerate(bores.items()):
        for other_name, other in list(bores.items())[i + 1 :]:
            volume = hit_volume(bore, other)
            if volume > TOL:
                bore_pairs[f"{name}/{other_name}"] = round(volume, 5)

    overlaps = {}
    for cleat_name in ("rear_cleat", "upright_side_cleat"):
        for name, wood in parts.items():
            if name == cleat_name:
                continue
            volume = hit_volume(parts[cleat_name], wood)
            if volume > TOL:
                overlaps[f"{cleat_name}/{name}"] = round(volume, 5)

    axes = list(csv.DictReader(AXES.open(newline="")))
    fixed = {"panel": 0, "kicker": 0}
    screw_hits = {}
    for row in axes:
        name = row["name"]
        if name.startswith("round_panel_"):
            fixed["panel"] += 1
        elif name.startswith(("round_kicker_", "kicker_header_")):
            fixed["kicker"] += 1
        else:
            continue
        screw = cq.Solid.makeCylinder(
            float(row["modeled_diameter_mm"]) / 2,
            float(row["shop_purchased_length_mm"]),
            cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz")),
            cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz")),
        )
        for group, solids in (
            ("cleat", {"rear": rear, "side": side}),
            ("bore", bores),
            ("seat", seats),
        ):
            for item_name, solid in solids.items():
                volume = hit_volume(screw, solid)
                if volume > TOL:
                    screw_hits[f"{group}/{item_name}/{name}"] = round(volume, 5)

    profiles = json.loads(PROFILES.read_text())
    edge_x = {
        name: (max if name.endswith("left") else min)(
            vertex[0] for vertex in profiles[name]["vertices_world_mm"]
        )
        for name in ("kicker_left", "kicker_right")
    }
    edge_support = {
        name.removeprefix("kicker_"): backer.isInside(cq.Vector(x, -36.1, 120), TOL)
        for name, x in edge_x.items()
    }

    tool_ends = {
        "post_front_low": (107.8, -36, 110, 0, 1, 0),
        "post_front_high": (107.8, -36, 190, 0, 1, 0),
        "post_rear_low": (107.8, -213.8, 110, 0, -1, 0),
        "post_rear_high": (107.8, -213.8, 190, 0, -1, 0),
        "upright_left": (50.95, -147.3, 350, -1, 0, 0),
        "upright_right": (139.85, -147.3, 350, 1, 0, 0),
        "link_rear": (114.45, -213.8, 370, 0, -1, 0),
        "link_front": (114.45, -118.9, 370, 0, 1, 0),
    }
    tool_hits = {}
    for name, (x, y, z, dx, dy, dz) in tool_ends.items():
        tool = cq.Solid.makeCylinder(20, 20, cq.Vector(x, y, z), cq.Vector(dx, dy, dz))
        for wood_name, wood in parts.items():
            volume = hit_volume(tool, wood)
            if volume > TOL:
                tool_hits[f"{name}/{wood_name}"] = round(volume, 5)

    washer_faces = {
        "post_front_low": ("shifted_right_post", 107.8, -46, 110, 0, -1, 0),
        "post_front_high": ("shifted_right_post", 107.8, -46, 190, 0, -1, 0),
        "post_rear_low": ("rear_cleat", 107.8, -213.8, 110, 0, 1, 0),
        "post_rear_high": ("rear_cleat", 107.8, -213.8, 190, 0, 1, 0),
        "upright_left": ("base_principal_center_right", 50.95, -147.3, 350, 1, 0, 0),
        "upright_right": ("upright_side_cleat", 139.85, -147.3, 350, -1, 0, 0),
        "link_rear": ("rear_cleat", 114.45, -213.8, 370, 0, 1, 0),
        "link_front": ("upright_side_cleat", 114.45, -118.9, 370, 0, -1, 0),
    }
    washer_bearing = {}
    for name, (wood, x, y, z, dx, dy, dz) in washer_faces.items():
        washer = cq.Solid.makeCylinder(
            10, 0.01, cq.Vector(x, y, z), cq.Vector(dx, dy, dz)
        )
        washer_bearing[name] = round(
            hit_volume(washer, parts[wood]) / washer.Volume(), 8
        )
    post_box = post.BoundingBox()
    rear_box = rear.BoundingBox()
    side_box = side.BoundingBox()

    def distances(value, low, high):
        return [round(value - low, 5), round(high - value, 5)]

    edges = {
        "post_bolts_x_edges": distances(107.8, post_box.xmin, post_box.xmax),
        "rear_cleat_post_bolts_x_edges": distances(107.8, rear_box.xmin, rear_box.xmax),
        "post_low_z_ends": distances(110, post_box.zmin, post_box.zmax),
        "post_high_z_ends": distances(190, post_box.zmin, post_box.zmax),
        "cleat_link_x_edges": distances(114.45, rear_box.xmin, rear_box.xmax),
        "cleat_link_rear_z_ends": distances(370, rear_box.zmin, rear_box.zmax),
        "cleat_link_side_z_ends": distances(370, side_box.zmin, side_box.zmax),
        "upright_bolt_side_y_edges": distances(-147.3, side_box.ymin, side_box.ymax),
        "upright_bolt_side_z_ends": distances(350, side_box.zmin, side_box.zmax),
    }
    return {
        "fixed_axes": fixed,
        "right_post_shift_mm": 37.8,
        "bolt_diameter_mm": BOLT_DIAMETER,
        "bore_diameter_mm": 2 * BORE_RADIUS,
        "cleat_bounds_mm": {"rear": bounds(rear), "upright_side": bounds(side)},
        "removed_legacy_stations": sorted(REMOVED_STATIONS),
        "legacy_clip_wood_hits_mm3": legacy_clip_hits,
        "legacy_clip_screw_wood_hits_mm3": legacy_screw_hits,
        "unintended_solid_overlaps_mm3": overlaps,
        "fixed_screw_hits_mm3": screw_hits,
        "inner_kicker_edges_supported": edge_support,
        "bore_received_fraction": received,
        "bore_unintended_wood_hits_mm3": unintended,
        "bore_pair_hits_mm3": bore_pairs,
        "front_seats_flush_below_kicker_back": all(
            seat.BoundingBox().ymax <= -36 + TOL for seat in seats.values()
        ),
        "washer_bearing_fraction": washer_bearing,
        "upright_washer_bearing_fraction": washer_bearing["upright_left"],
        "trial_20mm_radius_tool_wood_hits_mm3": tool_hits,
        "actual_edge_end_mm": edges,
        "conditional_4d_mm": 4 * BOLT_DIAMETER,
        "conditional_7d_mm": 7 * BOLT_DIAMETER,
        "conditional_post_x_edge_shortfall_mm": round(
            max(0, 4 * BOLT_DIAMETER - min(edges["post_bolts_x_edges"])), 5
        ),
        "conditional_geometry_pass": min(
            edges["post_bolts_x_edges"] + edges["rear_cleat_post_bolts_x_edges"]
        )
        >= 4 * BOLT_DIAMETER,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
