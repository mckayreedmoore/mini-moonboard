"""Nominal two-cleat center post transfer; geometry only, not a strength verdict."""

import csv
import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mini_moonboard import compact_floor_flush_frame as frame

AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
PROFILES = ROOT / "docs/floor-flush-construction-kerf-right/stock-profiles.json"
BORE_RADIUS = 5.25  # Illustrated 10.5 mm bore for a nominal 3/8 in bolt.
SEAT_RADIUS = 12.5  # Diagnostic 25 mm washer/driver pocket, not a drill callout.
TOL = 0.001


def bounds(shape):
    box = shape.BoundingBox()
    return [
        round(v, 5)
        for v in (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
    ]


def hit_volume(a, b):
    return a.intersect(b).Volume()


def probe():
    """Check a rear cleat, side cleat, and three ordinary through-bolt groups."""
    parts = {part.name: part.shape for part in frame.uncut_wood_parts()}
    post = parts.pop("base_post_center_right").translate(cq.Vector(37.8, 0, 0))
    parts["shifted_right_post"] = post
    backer = cq.Solid.makeBox(139.7, 88.9, 238.9, cq.Vector(-50.95, -124.9, 0))
    rear = cq.Solid.makeBox(38.1, 38.1, 460.0, cq.Vector(89.05, -213.8, 0.0))
    side = cq.Solid.makeBox(38.1, 50.8, 183.0, cq.Vector(89.05, -175.7, 277.0))
    parts.update(backer=backer, rear_cleat=rear, upright_side_cleat=side)

    # Historical hardware is not retained by this V4 concept. Record the
    # collisions explicitly so a wood-only fit cannot imply installability.
    legacy_names = {
        "clip_split_header_center_right",
        "clip_split_base_center_right",
    }
    legacy_stations = tuple(
        station for station in frame.stations() if station[0] in legacy_names
    )
    legacy_clips = {
        part.name: part.shape for part in frame.hardware.clip_parts(legacy_stations)
    }
    legacy_clip_hits = {}
    for wood_name in ("shifted_right_post", "rear_cleat", "upright_side_cleat"):
        for clip_name, clip in legacy_clips.items():
            volume = hit_volume(parts[wood_name], clip)
            if volume > TOL:
                legacy_clip_hits[f"{wood_name}/{clip_name}"] = round(volume, 5)
    legacy_screw_hits = {}
    for connection in frame.connections():
        if not any(connection.name.startswith(name + "_") for name in legacy_names):
            continue
        shaft, head = connection.components()
        for wood_name in ("shifted_right_post", "rear_cleat", "upright_side_cleat"):
            volume = hit_volume(parts[wood_name], shaft.fuse(head))
            if volume > TOL:
                legacy_screw_hits[f"{wood_name}/{connection.name}"] = round(volume, 5)

    # A thin contact slice measures the actual inclined upright, not its box.
    upright = parts["base_principal_center_right"]
    upright_contact_slice = cq.Solid.makeBox(
        0.01, 50.8, 183.0, cq.Vector(89.04, -175.7, 277.0)
    )
    contacts = {
        "post_rear": round((126.85 - 89.05) * 238.9, 5),
        "upright_side": round(hit_volume(upright, upright_contact_slice) / 0.01, 5),
        "cleat_pair": round(38.1 * 183.0, 5),
    }

    overlaps = {}
    for cleat_name in ("rear_cleat", "upright_side_cleat"):
        for name, wood in parts.items():
            if name == cleat_name:
                continue
            volume = hit_volume(parts[cleat_name], wood)
            if volume > TOL:
                overlaps[f"{cleat_name}/{name}"] = round(volume, 5)

    bores = {
        "post_low": cq.Solid.makeCylinder(
            BORE_RADIUS, 167.8, cq.Vector(108.0, -213.8, 110.0), cq.Vector(0, 1, 0)
        ),
        "post_high": cq.Solid.makeCylinder(
            BORE_RADIUS, 167.8, cq.Vector(108.0, -213.8, 190.0), cq.Vector(0, 1, 0)
        ),
        "upright": cq.Solid.makeCylinder(
            BORE_RADIUS, 76.2, cq.Vector(50.95, -148.5, 344.5), cq.Vector(1, 0, 0)
        ),
        "cleat_link": cq.Solid.makeCylinder(
            BORE_RADIUS, 88.9, cq.Vector(110.5, -213.8, 370.0), cq.Vector(0, 1, 0)
        ),
    }
    seats = {
        name: cq.Solid.makeCylinder(
            SEAT_RADIUS, 10.0, cq.Vector(108.0, -46.0, z), cq.Vector(0, 1, 0)
        )
        for name, z in (("post_low", 110.0), ("post_high", 190.0))
    }
    intended = {
        "post_low": {"shifted_right_post", "rear_cleat"},
        "post_high": {"shifted_right_post", "rear_cleat"},
        "upright": {"base_principal_center_right", "upright_side_cleat"},
        "cleat_link": {"rear_cleat", "upright_side_cleat"},
    }
    unintended = {}
    received = {}
    for bore_name, bore in bores.items():
        received[bore_name] = round(
            sum(hit_volume(bore, parts[name]) for name in intended[bore_name])
            / bore.Volume(),
            8,
        )
        for name, wood in parts.items():
            if name in intended[bore_name]:
                continue
            volume = hit_volume(bore, wood)
            if volume > TOL:
                unintended[f"{bore_name}/{name}"] = round(volume, 5)
    pair_hits = {}
    bore_items = list(bores.items())
    for i, (name, bore) in enumerate(bore_items):
        for other_name, other in bore_items[i + 1 :]:
            volume = hit_volume(bore, other)
            if volume > TOL:
                pair_hits[f"{name}/{other_name}"] = round(volume, 5)

    axes = list(csv.DictReader(AXES.open(newline="")))
    fixed = {"panel": 0, "kicker": 0}
    bore_screw_hits = {}
    seat_screw_hits = {}
    cleat_screw_hits = {}
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
        for cleat_name, cleat in (("rear", rear), ("upright_side", side)):
            volume = hit_volume(cleat, screw)
            if volume > TOL:
                cleat_screw_hits[f"{cleat_name}/{name}"] = round(volume, 5)
        for group, solids, hits in (
            ("bore", bores, bore_screw_hits),
            ("seat", seats, seat_screw_hits),
        ):
            for bolt_name, solid in solids.items():
                volume = hit_volume(solid, screw)
                if volume > TOL:
                    hits[f"{bolt_name}/{name}"] = round(volume, 5)

    profiles = json.loads(PROFILES.read_text())
    edge_x = {
        name: (max if name.endswith("left") else min)(
            vertex[0] for vertex in profiles[name]["vertices_world_mm"]
        )
        for name in ("kicker_left", "kicker_right")
    }
    edge_support = {
        name.removeprefix("kicker_"): backer.isInside(cq.Vector(x, -36.1, 120.0), TOL)
        for name, x in edge_x.items()
    }
    washer_slice = cq.Solid.makeCylinder(
        10.0, 0.01, cq.Vector(50.95, -148.5, 344.5), cq.Vector(1, 0, 0)
    )
    tool_envelopes = {
        "post_front_low": cq.Solid.makeCylinder(
            20.0, 20.0, cq.Vector(108, -36, 110), cq.Vector(0, 1, 0)
        ),
        "post_front_high": cq.Solid.makeCylinder(
            20.0, 20.0, cq.Vector(108, -36, 190), cq.Vector(0, 1, 0)
        ),
        "post_rear_low": cq.Solid.makeCylinder(
            20.0, 20.0, cq.Vector(108, -213.8, 110), cq.Vector(0, -1, 0)
        ),
        "post_rear_high": cq.Solid.makeCylinder(
            20.0, 20.0, cq.Vector(108, -213.8, 190), cq.Vector(0, -1, 0)
        ),
        "upright_left": cq.Solid.makeCylinder(
            20.0, 20.0, cq.Vector(50.95, -148.5, 344.5), cq.Vector(-1, 0, 0)
        ),
        "upright_right": cq.Solid.makeCylinder(
            20.0, 20.0, cq.Vector(127.15, -148.5, 344.5), cq.Vector(1, 0, 0)
        ),
        "link_rear": cq.Solid.makeCylinder(
            20.0, 20.0, cq.Vector(110.5, -213.8, 370), cq.Vector(0, -1, 0)
        ),
        "link_front": cq.Solid.makeCylinder(
            20.0, 20.0, cq.Vector(110.5, -124.9, 370), cq.Vector(0, 1, 0)
        ),
    }
    tool_hits = {}
    for station, envelope in tool_envelopes.items():
        for name, wood in parts.items():
            volume = hit_volume(envelope, wood)
            if volume > TOL:
                tool_hits[f"{station}/{name}"] = round(volume, 5)
    return {
        "fixed_axes": fixed,
        "right_post_shift_mm": 37.8,
        "cleat_bounds_mm": {"rear": bounds(rear), "upright_side": bounds(side)},
        "legacy_clip_wood_hits_mm3": legacy_clip_hits,
        "legacy_clip_screw_wood_hits_mm3": legacy_screw_hits,
        "contacts_mm2": contacts,
        "unintended_solid_overlaps_mm3": overlaps,
        "inner_kicker_edges_supported": edge_support,
        "bolt_bore_fixed_screw_hits_mm3": bore_screw_hits,
        "seat_fixed_screw_hits_mm3": seat_screw_hits,
        "cleat_fixed_screw_hits_mm3": cleat_screw_hits,
        "bolt_bore_unintended_wood_hits_mm3": unintended,
        "bolt_bore_received_fraction": received,
        "bolt_bore_pair_hits_mm3": pair_hits,
        "front_seats_flush_below_kicker_back": all(
            seat.BoundingBox().ymax <= -36.0 + TOL for seat in seats.values()
        ),
        "upright_washer_bearing_fraction": round(
            hit_volume(washer_slice, upright) / washer_slice.Volume(), 8
        ),
        "trial_20mm_radius_tool_wood_hits_mm3": tool_hits,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
