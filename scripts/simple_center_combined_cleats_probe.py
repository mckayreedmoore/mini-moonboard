"""Simultaneous PB-02 center cleats in the right-only shifted-post pose."""

import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_header_post_side_cleat_probe as post
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_link_edge_probe as link
from scripts import simple_center_principal_cleat_reserve_probe as principal
from scripts import simple_center_wide_post_probe as wide

NEW_WOOD = {
    "header_post_side_cleat": post.CLEAT,
    "header_side_cleat": principal.CLEAT,
}
INTENDED = {
    "post_cleat": ("shifted_right_post", "header_post_side_cleat"),
    "cleat_header": ("header_post_side_cleat", "base_header"),
    "header_cleat": ("base_header", "header_side_cleat"),
    "cleat_principal": ("header_side_cleat", "base_principal_center_right"),
}


def cylinder(radius, length, point, direction):
    return cq.Solid.makeCylinder(
        radius, length, cq.Vector(*point), cq.Vector(*direction)
    )


def hits(shapes, targets):
    return {
        f"{name}/{target}": round(volume, 5)
        for name, shape in shapes.items()
        for target, solid in targets.items()
        if (volume := wide.hit_volume(shape, solid)) > wide.TOL
    }


def new_bores():
    r = wide.BORE_RADIUS
    return {
        "post_cleat": cylinder(r, 177.8, (88.75, -150, 160), (1, 0, 0)),
        "cleat_header": cylinder(r, 167, (222.1, -130, 110), (0, 0, 1)),
        "header_cleat": cylinder(r, 141.1, (15.475, -145.3, 238.9), (0, 0, 1)),
        "cleat_principal": cylinder(r, 109.05, (-20, -95, 330), (1, 0, 0)),
    }


def inherited_bores():
    r = wide.BORE_RADIUS
    return {
        "post_low": cylinder(r, 127, (140, -213.8, 110), (0, 1, 0)),
        "post_high": cylinder(r, 127, (140, -213.8, 190), (0, 1, 0)),
        "upright": cylinder(r, 127, (50.95, -147.3, 350), (1, 0, 0)),
        "cleat_link": cylinder(r, 94.9, (133.5, -213.8, 370), (0, 1, 0)),
    }


# Point, outward direction, and wood owner at each exposed end.
NEW_ENDS = {
    "post_left": ((88.75, -150, 160), (-1, 0, 0), "shifted_right_post"),
    "post_cleat_right": ((266.55, -150, 160), (1, 0, 0), "header_post_side_cleat"),
    "post_cleat_bottom": ((222.1, -130, 110), (0, 0, -1), "header_post_side_cleat"),
    "post_header_top": ((222.1, -130, 277), (0, 0, 1), "base_header"),
    "principal_header_bottom": ((15.475, -145.3, 238.9), (0, 0, -1), "base_header"),
    "principal_cleat_top": ((15.475, -145.3, 380), (0, 0, 1), "header_side_cleat"),
    "principal_cleat_left": ((-20, -95, 330), (-1, 0, 0), "header_side_cleat"),
    "principal_right": ((89.05, -95, 330), (1, 0, 0), "base_principal_center_right"),
}
INHERITED_ENDS = {
    **{
        f"post_front_{label}": ((140, -86.8, z), (0, 1, 0), "shifted_right_post")
        for label, z in (("low", 110), ("high", 190))
    },
    **{
        f"post_rear_{label}": ((140, -213.8, z), (0, -1, 0), "rear_cleat")
        for label, z in (("low", 110), ("high", 190))
    },
    "upright_left": ((50.95, -147.3, 350), (-1, 0, 0), "base_principal_center_right"),
    "upright_right": ((177.95, -147.3, 350), (1, 0, 0), "upright_side_cleat"),
    "link_rear": ((133.5, -213.8, 370), (0, -1, 0), "rear_cleat"),
    "link_front": ((133.5, -118.9, 370), (0, 1, 0), "upright_side_cleat"),
}


def end_envelopes(ends, parts):
    washers, washer_seats, hardware, tools = {}, {}, {}, {}
    for name, (point, outward, owner) in ends.items():
        inward = tuple(-component for component in outward)
        disk = cylinder(10, 0.01, point, inward)
        washers[name] = round(wide.hit_volume(disk, parts[owner]) / disk.Volume(), 8)
        washer_seats[name] = cylinder(10, 0.01, point, outward)
        hardware[name] = cylinder(10, 5, point, outward)
        tools[name] = cylinder(20, 20, point, outward)
    return washers, washer_seats, hardware, tools


def probe():
    """Screen both committed cleat poses against one complete nominal assembly."""
    baseline = link.probe()
    parts = frame._parts() | NEW_WOOD
    counts, screws = frame._fixed_screws()
    bores = new_bores()
    old_bores = inherited_bores()
    new_washers, new_seats, new_hardware, new_tools = end_envelopes(NEW_ENDS, parts)
    old_washers, old_seats, old_hardware, old_tools = end_envelopes(
        INHERITED_ENDS, parts
    )

    overlaps = hits(NEW_WOOD, {k: v for k, v in parts.items() if k not in NEW_WOOD})
    overlaps.update(
        hits(
            {"header_side_cleat": principal.CLEAT},
            {"header_post_side_cleat": post.CLEAT},
        )
    )
    received = {
        name: round(
            sum(wide.hit_volume(bore, parts[wood]) for wood in INTENDED[name])
            / bore.Volume(),
            8,
        )
        for name, bore in bores.items()
    }
    other_wood = {
        key: value
        for name, bore in bores.items()
        for key, value in hits(
            {name: bore}, {k: v for k, v in parts.items() if k not in INTENDED[name]}
        ).items()
    }
    all_bores = bores | old_bores
    bore_pairs = {
        f"{name}/{other}": round(volume, 5)
        for i, (name, bore) in enumerate(all_bores.items())
        for other, second in list(all_bores.items())[i + 1 :]
        if name in bores or other in bores
        if (volume := wide.hit_volume(bore, second)) > wide.TOL
    }
    screw_hits = hits(NEW_WOOD | bores, screws)
    header_receivers = {
        name: round(wide.hit_volume(screw, parts["base_header"]) / screw.Volume(), 8)
        for name, screw in screws.items()
        if name.startswith("kicker_header_")
    }
    center_receivers = {}
    for name, wood in (
        ("round_kicker_left_center_1", "base_post_center_left"),
        ("round_kicker_left_center_2", "base_post_center_left"),
        ("round_kicker_right_center_1", "backer"),
        ("round_kicker_right_center_2", "backer"),
    ):
        kicker = parts["kicker_left" if "_left_" in name else "kicker_right"]
        exposed = screws[name].cut(kicker)
        center_receivers[name] = round(
            wide.hit_volume(exposed, parts[wood]) / exposed.Volume(), 8
        )
    old_new_wood = hits(old_bores, NEW_WOOD)
    inherited_clear = (
        counts == baseline["fixed_axes"] == {"panel": 48, "kicker": 18}
        and all(baseline["inner_kicker_edges_supported"].values())
        and center_receivers == baseline["center_kicker_screw_receiver_fraction"]
        and len(center_receivers) == 4
        and set(center_receivers.values()) == {1.0}
        and set(baseline["removed_legacy_stations"])
        == {"clip_split_base_center_right", "clip_split_header_center_right"}
        and all(
            not baseline[key]
            for key in (
                "solid_overlaps_mm3",
                "fixed_screw_hits_mm3",
                "bore_unintended_wood_hits_mm3",
                "bore_pair_hits_mm3",
                "trial_20mm_radius_tool_wood_hits_mm3",
            )
        )
    )
    checks = {
        "new_wood_overlaps_mm3": overlaps,
        "new_bore_other_wood_hits_mm3": other_wood,
        "new_bore_pair_hits_mm3": bore_pairs,
        "new_screw_hits_mm3": screw_hits,
        "new_hardware_wood_hits_mm3": hits(new_hardware, parts),
        "new_washer_unintended_wood_hits_mm3": hits(new_seats, parts),
        "new_hardware_screw_hits_mm3": hits(new_hardware, screws),
        "new_tool_wood_hits_mm3": hits(new_tools, parts),
        "new_tool_screw_hits_mm3": hits(new_tools, screws),
        "inherited_hardware_new_wood_hits_mm3": hits(old_hardware, NEW_WOOD),
        "inherited_washer_new_wood_hits_mm3": hits(old_seats, NEW_WOOD),
        "inherited_tool_new_wood_hits_mm3": hits(old_tools, NEW_WOOD),
        "inherited_bore_new_wood_hits_mm3": old_new_wood,
        "new_hardware_inherited_hardware_hits_mm3": hits(new_hardware, old_hardware),
        "new_tool_inherited_hardware_hits_mm3": hits(new_tools, old_hardware),
        "inherited_tool_new_hardware_hits_mm3": hits(old_tools, new_hardware),
    }
    accepted = (
        inherited_clear
        and len(screws) == 66
        and len(header_receivers) == 10
        and set(header_receivers.values()) == {0.7125}
        and all(value == 1 for value in received.values())
        and all(value == 1 for value in new_washers.values())
        and all(value == 1 for value in old_washers.values())
        and all(not value for value in checks.values())
    )
    return {
        "pose": "right-only shifted post/link-edge with both committed PB-02 cleats",
        "new_cleat_bounds_mm": {k: wide.bounds(v) for k, v in NEW_WOOD.items()},
        "fixed_axes": counts,
        "fixed_screw_axes_checked": len(screws),
        "inherited_pose_clear": inherited_clear,
        "inner_kicker_edges_supported": baseline["inner_kicker_edges_supported"],
        "center_kicker_screw_receiver_fraction": center_receivers,
        "header_screw_receiver_fraction": header_receivers,
        "new_bore_received_fraction": received,
        "new_washer_bearing_fraction": new_washers,
        "inherited_washer_bearing_fraction": old_washers,
        "new_joint_ends": {
            "header_post": list(NEW_ENDS)[:4],
            "header_principal": list(NEW_ENDS)[4:],
        },
        "inherited_ends_checked": list(INHERITED_ENDS),
        "intended_serial_paths": [
            ["shifted_right_post", "header_post_side_cleat", "base_header"],
            ["base_principal_center_right", "header_side_cleat", "base_header"],
        ],
        "old_clips_displaced": baseline["removed_legacy_stations"],
        **checks,
        "nominal_geometry": "accepted" if accepted else "rejected",
        "fabrication_ready": False,
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
