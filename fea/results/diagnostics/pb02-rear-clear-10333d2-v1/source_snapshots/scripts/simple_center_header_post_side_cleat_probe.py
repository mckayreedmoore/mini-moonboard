"""One PB-02 solid side-cleat header/post geometry trial; no drilling release."""

import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_header_principal_probe as prior
from scripts import simple_center_link_edge_probe as link
from scripts import simple_center_wide_post_probe as wide

NOMINAL_D = 6.35
CLEAT = cq.Solid.makeBox(88.9, 88.9, 128.9, cq.Vector(177.65, -175.7, 110))
POST_AXIS = (-150.0, 160.0)  # Y, Z; transverse X bolt.
HEADER_AXIS = (222.1, -130.0)  # X, Y; vertical Z bolt.


def _cylinder(radius, length, start, direction):
    return cq.Solid.makeCylinder(
        radius, length, cq.Vector(*start), cq.Vector(*direction)
    )


def _hits(shape, named):
    return {
        name: round(volume, 5)
        for name, other in named.items()
        if (volume := wide.hit_volume(shape, other)) > wide.TOL
    }


def _vertical_bolt_length_screen(parts, screws):
    """Illustrative under-head lengths; delivered threads and grip are unknown."""
    grip = 167.0
    washers = 0.13 * 25.4  # Assumed combined thickness of two washers.
    nut = 0.25 * 25.4
    result = {}
    for inches in (7, 8):
        length = inches * 25.4
        tip_past_nut = length - grip - washers - nut
        top_projection = length - grip - washers / 2
        shaft = _cylinder(
            wide.BORE_RADIUS, top_projection, (222.1, -130, 277), (0, 0, 1)
        )
        top_stack = _cylinder(10, washers / 2 + nut, (222.1, -130, 277), (0, 0, 1))
        extended_tool = _cylinder(
            20, max(20, top_projection), (222.1, -130, 277), (0, 0, 1)
        )
        result[f"{inches}_in"] = {
            "tip_past_nut_mm": round(tip_past_nut, 5),
            "tip_past_nut_in": round(tip_past_nut / 25.4, 5),
            "top_projection_mm": round(top_projection, 5),
            "beyond_original_20mm_tool_mm": round(max(0, top_projection - 20), 5),
            "top_shaft_wood_hits_mm3": _hits(shaft, parts),
            "top_shaft_fixed_screw_hits_mm3": _hits(shaft, screws),
            "top_washer_nut_wood_hits_mm3": _hits(top_stack, parts),
            "extended_top_tool_wood_hits_mm3": _hits(extended_tool, parts),
            "extended_top_tool_fixed_screw_hits_mm3": _hits(extended_tool, screws),
        }
    nut_bearing_plane_in = (grip + washers) / 25.4
    return {
        "candidates": result,
        "nut_bearing_plane_under_head_in": round(nut_bearing_plane_in, 5),
        "seven_in_short_of_provisional_0_05in_full_thread_mm": round(
            max(0, 0.05 * 25.4 - result["7_in"]["tip_past_nut_mm"]), 5
        ),
        "illustrative_eight_in_one_in_thread_start_in": 7.0,
        "illustrative_eight_in_thread_start_past_bearing_plane_in": round(
            7.0 - nut_bearing_plane_in, 5
        ),
    }


def probe():
    """Measure one solid cleat and complete intersecting member bores."""
    baseline = link.probe()
    parts = prior._parts()
    parts["header_post_side_cleat"] = CLEAT
    counts, screws = prior._fixed_screws()
    post_y, post_z = POST_AXIS
    header_x, header_y = HEADER_AXIS
    bores = {
        "post_cleat": _cylinder(
            wide.BORE_RADIUS, 177.8, (88.75, post_y, post_z), (1, 0, 0)
        ),
        "cleat_header": _cylinder(
            wide.BORE_RADIUS, 167, (header_x, header_y, 110), (0, 0, 1)
        ),
    }
    intended = {
        "post_cleat": ("shifted_right_post", "header_post_side_cleat"),
        "cleat_header": ("header_post_side_cleat", "base_header"),
    }
    received = {
        name: round(
            sum(wide.hit_volume(bore, parts[wood]) for wood in intended[name])
            / bore.Volume(),
            8,
        )
        for name, bore in bores.items()
    }
    existing = {
        "post_low": _cylinder(wide.BORE_RADIUS, 127, (140, -213.8, 110), (0, 1, 0)),
        "post_high": _cylinder(wide.BORE_RADIUS, 127, (140, -213.8, 190), (0, 1, 0)),
        "cleat_link": _cylinder(
            wide.BORE_RADIUS, 94.9, (133.5, -213.8, 370), (0, 1, 0)
        ),
        "upright": _cylinder(wide.BORE_RADIUS, 127, (50.95, -147.3, 350), (1, 0, 0)),
    }
    ends = {
        "post_left": ((88.75, post_y, post_z), (-1, 0, 0), "shifted_right_post"),
        "cleat_right": ((266.55, post_y, post_z), (1, 0, 0), "header_post_side_cleat"),
        "cleat_bottom": (
            (header_x, header_y, 110),
            (0, 0, -1),
            "header_post_side_cleat",
        ),
        "header_top": ((header_x, header_y, 277), (0, 0, 1), "base_header"),
    }
    washers, hardware, tools = {}, {}, {}
    hardware_fixed_hits, tool_fixed_hits = {}, {}
    for name, (point, outward, owner) in ends.items():
        inward = tuple(-v for v in outward)
        disk = _cylinder(10, 0.01, point, inward)
        washers[name] = round(wide.hit_volume(disk, parts[owner]) / disk.Volume(), 8)
        hardware_solid = _cylinder(10, 5, point, outward)
        tool_solid = _cylinder(20, 20, point, outward)
        hardware[name] = _hits(hardware_solid, parts)
        tools[name] = _hits(tool_solid, parts)
        hardware_fixed_hits[name] = _hits(hardware_solid, screws)
        tool_fixed_hits[name] = _hits(tool_solid, screws)
    overlaps = _hits(
        CLEAT,
        {
            name: wood
            for name, wood in parts.items()
            if name != "header_post_side_cleat"
        },
    )
    fixed_hits = {
        f"{name}/{screw}": volume
        for name, solid in {"cleat": CLEAT, **bores}.items()
        for screw, volume in _hits(solid, screws).items()
    }
    other_wood = {
        f"{name}/{wood}": volume
        for name, bore in bores.items()
        for wood, volume in _hits(
            bore, {k: v for k, v in parts.items() if k not in intended[name]}
        ).items()
    }
    other_bores = {
        f"{name}/{old}": volume
        for name, bore in bores.items()
        for old, volume in _hits(bore, existing).items()
    }
    other_bores.update(
        {
            f"post_cleat/{name}": volume
            for name, volume in _hits(
                bores["post_cleat"], {"cleat_header": bores["cleat_header"]}
            ).items()
        }
    )
    header_receivers = {}
    for name, screw in screws.items():
        if name.startswith("kicker_header_"):
            header_receivers[name] = round(
                wide.hit_volume(screw, parts["base_header"]) / screw.Volume(), 8
            )
    supported = all(baseline["inner_kicker_edges_supported"].values())
    base_clear = (
        counts == baseline["fixed_axes"] == {"panel": 48, "kicker": 18}
        and supported
        and set(baseline["center_kicker_screw_receiver_fraction"].values()) == {1.0}
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
    accepted = (
        base_clear
        and not any((overlaps, fixed_hits, other_wood, other_bores))
        and all(value == 1 for value in received.values())
        and all(value == 1 for value in washers.values())
        and not any(hardware.values())
        and not any(tools.values())
        and not any(hardware_fixed_hits.values())
        and not any(tool_fixed_hits.values())
    )
    return {
        "pose": "one solid rectangular side cleat below original header, beside shifted right post",
        "cleat_bounds_mm": wide.bounds(CLEAT),
        "header_bounds_mm": wide.bounds(parts["base_header"]),
        "post_bounds_mm": wide.bounds(parts["shifted_right_post"]),
        "bolt_axes": {
            "post_cleat_yz_mm": [post_y, post_z],
            "cleat_header_xy_mm": [header_x, header_y],
        },
        "bolt_spans_mm": {
            "post_cleat_x": [88.75, 266.55],
            "cleat_header_z": [110, 277],
        },
        "nominal_bolt_diameter_mm": NOMINAL_D,
        "occupied_bore_diameter_mm": 2 * wide.BORE_RADIUS,
        "fixed_axes": counts,
        "inherited_pose_clear": base_clear,
        "inner_kicker_edges_supported": baseline["inner_kicker_edges_supported"],
        "center_kicker_screw_receiver_fraction": baseline[
            "center_kicker_screw_receiver_fraction"
        ],
        "header_screw_receiver_fraction": header_receivers,
        "cleat_wood_overlaps_mm3": overlaps,
        "bore_received_fraction": received,
        "bore_other_wood_hits_mm3": other_wood,
        "bore_fixed_screw_hits_mm3": fixed_hits,
        "bore_pair_hits_mm3": other_bores,
        "washer_bearing_fraction": washers,
        "external_hardware_wood_hits_mm3": hardware,
        "tool_wood_hits_mm3": tools,
        "external_hardware_fixed_screw_hits_mm3": hardware_fixed_hits,
        "tool_fixed_screw_hits_mm3": tool_fixed_hits,
        "nut_or_tool_on_installed_kicker_front": any(
            abs(point[1] + 36) < wide.TOL and outward[1] > 0
            for point, outward, _ in ends.values()
        ),
        "post_y_edges_mm": [round(post_y + 175.7, 5), round(-86.8 - post_y, 5)],
        "post_z_ends_mm": [post_z, round(238.9 - post_z, 5)],
        "cleat_post_bolt_z_ends_mm": [post_z - 110, round(238.9 - post_z, 5)],
        "header_bolt_y_edges_mm": [
            round(header_y + 175.7, 5),
            round(-36 - header_y, 5),
        ],
        "cleat_header_bolt_x_edges_mm": [
            round(header_x - 177.65, 5),
            round(266.55 - header_x, 5),
        ],
        "cleat_header_bolt_y_edges_mm": [
            round(header_y + 175.7, 5),
            round(-86.8 - header_y, 5),
        ],
        "header_bolt_x_grain_ends_mm": [
            round(header_x + 1219.2, 5),
            round(1219.2 - header_x, 5),
        ],
        "new_crossed_bore_axis_spacing_mm": abs(header_y - post_y),
        "new_crossed_bore_wall_gap_mm": round(
            abs(header_y - post_y) - 2 * wide.BORE_RADIUS, 5
        ),
        "inherited_post_high_crossed_axis_spacing_mm": abs(190 - post_z),
        "inherited_post_high_crossed_bore_wall_gap_mm": round(
            abs(190 - post_z) - 2 * wide.BORE_RADIUS, 5
        ),
        "inherited_post_high_group_and_splitting_qualified": False,
        "vertical_bolt_length_screen": _vertical_bolt_length_screen(parts, screws),
        "vertical_bolt_length_assumptions": {
            "wood_grip_mm": 167.0,
            "two_washers_total_in": 0.13,
            "nut_thickness_in": 0.25,
            "provisional_full_thread_past_nut_in": 0.05,
            "nut_at_header_top": True,
            "delivered_thread_length_verified": False,
        },
        "vertical_bolt_stack_selected": False,
        "conditional_4d_mm": 4 * NOMINAL_D,
        "conditional_7d_mm": round(7 * NOMINAL_D, 5),
        "nominal_geometry": "accepted" if accepted else "rejected",
        "fabrication_ready": False,
        "joint_mechanics_gate": (
            "Vertical cleat-header bolt enters cleat end grain; determine 2024 NDS "
            "end-grain factor, signed interface forces, eccentricity, bolt tension, "
            "lateral yield, wood bearing/splitting, and one-bolt moment path."
        ),
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
