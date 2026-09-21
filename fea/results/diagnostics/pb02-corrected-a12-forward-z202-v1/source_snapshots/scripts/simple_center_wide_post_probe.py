"""PB-02 solid-stock right-post substitution; nominal geometry only."""

import csv
import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.simple_center_post_transfer_adjusted import (
    BORE_RADIUS,
    REMOVED_STATIONS,
)
from scripts.simple_center_post_transfer_probe import (
    AXES,
    PROFILES,
    TOL,
    bounds,
    frame,
    hit_volume,
)

POST_X = 88.75
POST_REAR_Y = -175.7
POST_TOP = 238.9
BOLT_X = 114.45
BOLT_Z = (110.0, 190.0)
BACKER = cq.Solid.makeBox(139.7, 88.9, POST_TOP, cq.Vector(-50.95, -124.9, 0))
REAR = cq.Solid.makeBox(50.8, 38.1, 460, cq.Vector(89.05, -213.8, 0))
SIDE = cq.Solid.makeBox(50.8, 56.8, 183, cq.Vector(89.05, -175.7, 277))


def _hits(solids, parts, excluded=()):
    return {
        f"{solid_name}/{part_name}": round(volume, 5)
        for solid_name, solid in solids.items()
        for part_name, part in parts.items()
        if part_name not in excluded
        if (volume := hit_volume(solid, part)) > TOL
    }


def _distances(center, low, high):
    return [round(center - low, 5), round(high - center, 5)]


def _trial(label, post_depth):
    post_front = POST_REAR_Y + post_depth
    post = cq.Solid.makeBox(
        88.9, post_depth, POST_TOP, cq.Vector(POST_X, POST_REAR_Y, 0)
    )
    parts = {part.name: part.shape for part in frame.uncut_wood_parts()}
    original = parts.pop("base_post_center_right")
    parts.update(
        shifted_right_post=post, backer=BACKER, rear_cleat=REAR, upright_side_cleat=SIDE
    )
    new = {
        name: parts[name]
        for name in ("shifted_right_post", "backer", "rear_cleat", "upright_side_cleat")
    }
    overlaps = {}
    for name, solid in new.items():
        for other_name, other in parts.items():
            if other_name == name or (other_name in new and other_name < name):
                continue
            volume = hit_volume(solid, other)
            if volume > TOL:
                overlaps[f"{name}/{other_name}"] = round(volume, 5)

    stations = frame.stations()
    assert set(REMOVED_STATIONS) <= {s[0] for s in stations}
    clips = {p.name: p.shape for p in frame.hardware.clip_parts(stations)}
    old_screws = {}
    for connection in frame.connections():
        if connection.name.startswith("clip_"):
            shaft, head = connection.components()
            old_screws[connection.name] = shaft.fuse(head)
    clip_hits = _hits(clips, new)
    clip_screw_hits = _hits(old_screws, new)
    colliding_stations = {
        station[0]
        for station in stations
        if any(key.startswith(station[0] + "/") for key in clip_hits)
        or any(key.startswith(station[0] + "_") for key in clip_screw_hits)
    }

    bores = {
        f"post_{name}": cq.Solid.makeCylinder(
            BORE_RADIUS,
            post_front + 213.8,
            cq.Vector(BOLT_X, -213.8, z),
            cq.Vector(0, 1, 0),
        )
        for name, z in zip(("low", "high"), BOLT_Z)
    }
    bores["upright"] = cq.Solid.makeCylinder(
        BORE_RADIUS, 88.9, cq.Vector(50.95, -147.3, 350), cq.Vector(1, 0, 0)
    )
    bores["cleat_link"] = cq.Solid.makeCylinder(
        BORE_RADIUS, 94.9, cq.Vector(BOLT_X, -213.8, 370), cq.Vector(0, 1, 0)
    )
    intended = {
        "post_low": ("shifted_right_post", "rear_cleat"),
        "post_high": ("shifted_right_post", "rear_cleat"),
        "upright": ("base_principal_center_right", "upright_side_cleat"),
        "cleat_link": ("rear_cleat", "upright_side_cleat"),
    }
    bore_received = {
        name: round(
            sum(hit_volume(bore, parts[wood]) for wood in intended[name])
            / bore.Volume(),
            8,
        )
        for name, bore in bores.items()
    }
    bore_unintended = {
        f"{name}/{wood}": round(volume, 5)
        for name, bore in bores.items()
        for wood, solid in parts.items()
        if wood not in intended[name]
        if (volume := hit_volume(bore, solid)) > TOL
    }
    bore_pairs = {
        f"{name}/{other}": round(volume, 5)
        for i, (name, bore) in enumerate(bores.items())
        for other, second in list(bores.items())[i + 1 :]
        if (volume := hit_volume(bore, second)) > TOL
    }

    axes = list(csv.DictReader(AXES.open(newline="")))
    screws = {}
    counts = {"panel": 0, "kicker": 0}
    for row in axes:
        name = row["name"]
        if name.startswith("round_panel_"):
            counts["panel"] += 1
        elif name.startswith(("round_kicker_", "kicker_header_")):
            counts["kicker"] += 1
        else:
            continue
        screws[name] = cq.Solid.makeCylinder(
            float(row["modeled_diameter_mm"]) / 2,
            float(row["shop_purchased_length_mm"]),
            cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz")),
            cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz")),
        )
    fixed_hits = _hits(
        {
            **{f"bore/{n}": s for n, s in bores.items()},
            "post": post,
            "rear_cleat": REAR,
            "side_cleat": SIDE,
        },
        screws,
    )
    # Post/cleat screw intersections are reported separately from bores: the
    # post may intentionally receive a fixed screw in another stock pose.
    profiles = json.loads(PROFILES.read_text())
    inner_edges = {
        side: (max if side == "left" else min)(
            vertex[0] for vertex in profiles[f"kicker_{side}"]["vertices_world_mm"]
        )
        for side in ("left", "right")
    }
    support = {
        side: BACKER.isInside(cq.Vector(x, -36.1, 120), TOL)
        for side, x in inner_edges.items()
    }
    center_screw_receivers = {}
    for name, wood in (
        ("round_kicker_left_center_1", "base_post_center_left"),
        ("round_kicker_left_center_2", "base_post_center_left"),
        ("round_kicker_right_center_1", "backer"),
        ("round_kicker_right_center_2", "backer"),
    ):
        panel = parts["kicker_left" if "_left_" in name else "kicker_right"]
        exposed = screws[name].cut(panel)
        center_screw_receivers[name] = round(
            hit_volume(exposed, parts[wood]) / exposed.Volume(), 8
        )
    ends = {
        **{
            f"post_front_{name}": (BOLT_X, post_front, z, 0, 1, 0)
            for name, z in zip(("low", "high"), BOLT_Z)
        },
        **{
            f"post_rear_{name}": (BOLT_X, -213.8, z, 0, -1, 0)
            for name, z in zip(("low", "high"), BOLT_Z)
        },
        "upright_left": (50.95, -147.3, 350, -1, 0, 0),
        "upright_right": (139.85, -147.3, 350, 1, 0, 0),
        "link_rear": (BOLT_X, -213.8, 370, 0, -1, 0),
        "link_front": (BOLT_X, -118.9, 370, 0, 1, 0),
    }
    tools = {
        name: cq.Solid.makeCylinder(20, 20, cq.Vector(x, y, z), cq.Vector(dx, dy, dz))
        for name, (x, y, z, dx, dy, dz) in ends.items()
    }
    tool_hits = _hits(tools, parts)
    washer_owners = {
        **{f"post_front_{name}": "shifted_right_post" for name in ("low", "high")},
        **{f"post_rear_{name}": "rear_cleat" for name in ("low", "high")},
        "upright_left": "base_principal_center_right",
        "upright_right": "upright_side_cleat",
        "link_rear": "rear_cleat",
        "link_front": "upright_side_cleat",
    }
    washers = {}
    for name, (x, y, z, dx, dy, dz) in ends.items():
        inward = cq.Vector(-dx, -dy, -dz)
        washer = cq.Solid.makeCylinder(10, 0.01, cq.Vector(x, y, z), inward)
        washers[name] = round(
            hit_volume(washer, parts[washer_owners[name]]) / washer.Volume(), 8
        )
    post_box, rear_box, side_box = (
        post.BoundingBox(),
        REAR.BoundingBox(),
        SIDE.BoundingBox(),
    )
    margins = {
        "post_bolts_x_edges": _distances(BOLT_X, post_box.xmin, post_box.xmax),
        "rear_cleat_post_bolts_x_edges": _distances(
            BOLT_X, rear_box.xmin, rear_box.xmax
        ),
        "post_low_z_ends": _distances(110, post_box.zmin, post_box.zmax),
        "post_high_z_ends": _distances(190, post_box.zmin, post_box.zmax),
        "cleat_link_x_edges": _distances(BOLT_X, rear_box.xmin, rear_box.xmax),
        "cleat_link_rear_z_ends": _distances(370, rear_box.zmin, rear_box.zmax),
        "cleat_link_side_z_ends": _distances(370, side_box.zmin, side_box.zmax),
        "upright_bolt_side_y_edges": _distances(-147.3, side_box.ymin, side_box.ymax),
        "upright_bolt_side_z_ends": _distances(350, side_box.zmin, side_box.zmax),
    }
    return {
        "stock": label,
        "post_bounds_mm": bounds(post),
        "original_post_bounds_mm": bounds(original),
        "backer_bounds_mm": bounds(BACKER),
        "cleat_bounds_mm": {"rear": bounds(REAR), "side": bounds(SIDE)},
        "fixed_axes": counts,
        "center_kicker_screw_receiver_fraction": center_screw_receivers,
        "inner_kicker_edges_supported": support,
        "solid_overlaps_mm3": overlaps,
        "removed_legacy_stations": sorted(colliding_stations),
        "legacy_clip_wood_hits_mm3": clip_hits,
        "legacy_clip_screw_wood_hits_mm3": clip_screw_hits,
        "fixed_screw_hits_mm3": fixed_hits,
        "bore_received_fraction": bore_received,
        "bore_unintended_wood_hits_mm3": bore_unintended,
        "bore_pair_hits_mm3": bore_pairs,
        "post_front_to_kicker_back_gap_mm": round(-36 - post_front, 5),
        "no_pocket_front_short_tool_clear": (
            -36 - post_front >= 20
            and not any(name.startswith("post_front_") for name in tool_hits)
        ),
        "washer_bearing_fraction": washers,
        "trial_20mm_radius_tool_wood_hits_mm3": tool_hits,
        "actual_edge_end_mm": margins,
        "conditional_4d_mm": 25.4,
        "post_to_backer_contact_y_mm": round(
            max(0, min(post_front, -36) - max(POST_REAR_Y, -124.9)), 5
        ),
        "post_to_rear_cleat_contact_mm2": round(
            hit_volume(
                post,
                cq.Solid.makeBox(50.8, 0.01, POST_TOP, cq.Vector(89.05, -175.7, 0)),
            )
            / 0.01,
            5,
        ),
        "floor_footprint_xy_mm": [
            POST_X,
            round(POST_X + 88.9, 5),
            POST_REAR_Y,
            round(post_front, 5),
        ],
    }


def probe():
    """Test a square 4x4 at the rear cleat and one 4x6 with the old Y depth."""
    return {
        "four_by_four": _trial("nominal 4x4 solid 88.9 x 88.9", 88.9),
        "four_by_six": _trial("nominal 4x6 solid 88.9 x 139.7", 139.7),
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
