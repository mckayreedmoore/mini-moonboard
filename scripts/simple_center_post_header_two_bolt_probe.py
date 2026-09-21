"""Finite PB-02 post/header solid-block co-design; geometry only."""

import json
from functools import lru_cache
from itertools import combinations

import cadquery as cq

from scripts import simple_center_combined_cleats_probe as combined
from scripts import simple_center_combined_small_tool_probe as small
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_second_bolt_probe as second
from scripts import simple_center_second_bolt_tolerance_probe as prior
from scripts import simple_center_tolerance_pose_probe as tolerance
from scripts import simple_center_wide_post_probe as wide

VARIANTS = {
    "reference": (110, -150, (160, 205), (222.1, 235)),
    "lowered_block": (75, -150, (160, 205), (222.1, 235)),
    "relocated_pairs": (75, -150, (130, 180), (205, 235)),
    "post_axis_forward_5": (75, -145, (130, 180), (205, 235)),
    "balanced_pair_5": (75, -145, (130, 180), (208.35, 235.85)),
}
INSERTION_ALLOWANCE = 35.0  # Illustrative protrusion beyond wood grip.


def _pair_hits(shapes):
    return {
        f"{a}/{b}": round(volume, 5)
        for (a, left), (b, right) in combinations(shapes.items(), 2)
        if (volume := wide.hit_volume(left, right)) > wide.TOL
    }


def _candidate(config):
    bottom, post_y, post_z, vertical_x = config
    parts, bores, ends = prior._geometry()
    block = cq.Solid.makeBox(
        88.9, 88.9, 238.9 - bottom, cq.Vector(177.65, -175.7, bottom)
    )
    parts["header_post_side_cleat"] = block
    _, screws = frame._fixed_screws()
    # The two first axes are explicitly replaced and all ten bores rechecked.
    for name in ("post_cleat", "cleat_header"):
        bores.pop(name)
    for name in (
        "post_left",
        "post_cleat_right",
        "post_cleat_bottom",
        "post_header_top",
    ):
        ends.pop(name)

    for index, z in enumerate(post_z, 1):
        name = f"post_cleat_{index}"
        bores[name] = combined.cylinder(
            wide.BORE_RADIUS, 177.8, (88.75, post_y, z), (1, 0, 0)
        )
        ends[f"{name}_left"] = ((88.75, post_y, z), (-1, 0, 0), "shifted_right_post")
        ends[f"{name}_right"] = (
            (266.55, post_y, z),
            (1, 0, 0),
            "header_post_side_cleat",
        )
    for index, x in enumerate(vertical_x, 1):
        name = f"cleat_header_{index}"
        bores[name] = combined.cylinder(
            wide.BORE_RADIUS, 277 - bottom, (x, -130, bottom), (0, 0, 1)
        )
        ends[f"{name}_bottom"] = (
            (x, -130, bottom),
            (0, 0, -1),
            "header_post_side_cleat",
        )
        ends[f"{name}_top"] = ((x, -130, 277), (0, 0, 1), "base_header")

    intended = (
        combined.INTENDED
        | {f"post_cleat_{index}": combined.INTENDED["post_cleat"] for index in (1, 2)}
        | {
            f"cleat_header_{index}": combined.INTENDED["cleat_header"]
            for index in (1, 2)
        }
    )
    intended.pop("post_cleat")
    intended.pop("cleat_header")
    intended |= {
        "post_low": ("rear_cleat", "shifted_right_post"),
        "post_high": ("rear_cleat", "shifted_right_post"),
        "upright": ("base_principal_center_right", "upright_side_cleat"),
        "cleat_link": ("rear_cleat", "upright_side_cleat"),
    }
    washers, seats, hardware, _ = combined.end_envelopes(ends, parts)
    sockets = {
        name: combined.cylinder(
            small.SOCKET_RADIUS, small.SOCKET_LENGTH, point, outward
        )
        for name, (point, outward, _) in ends.items()
    }
    insertion = {}
    insertion_pairs = {}
    lengths = {
        "post_cleat_1": 177.8,
        "post_cleat_2": 177.8,
        "cleat_header_1": 277 - bottom,
        "cleat_header_2": 277 - bottom,
        "header_cleat": prior.POSE.top_z - 238.9,
        "cleat_principal": 109.05,
        "post_low": 127,
        "post_high": 127,
        "upright": 127,
        "cleat_link": 94.9,
    }
    original_pairs = {
        "header_cleat": ("principal_header_bottom", "principal_cleat_top"),
        "cleat_principal": ("principal_cleat_left", "principal_right"),
        "post_low": ("post_rear_low", "post_front_low"),
        "post_high": ("post_rear_high", "post_front_high"),
        "upright": ("upright_left", "upright_right"),
        "cleat_link": ("link_rear", "link_front"),
    }
    insertion_pairs.update(original_pairs)
    insertion_pairs.update(
        {
            f"post_cleat_{i}": (f"post_cleat_{i}_left", f"post_cleat_{i}_right")
            for i in (1, 2)
        }
    )
    insertion_pairs.update(
        {
            f"cleat_header_{i}": (f"cleat_header_{i}_bottom", f"cleat_header_{i}_top")
            for i in (1, 2)
        }
    )
    for bolt, pair in insertion_pairs.items():
        for end in pair:
            point, outward, _ = ends[end]
            insertion[end] = combined.cylinder(
                wide.BORE_RADIUS,
                lengths[bolt] + INSERTION_ALLOWANCE,
                point,
                outward,
            )
    insertion_hits = combined.hits(insertion, parts) | combined.hits(insertion, screws)
    insertion_hardware_hits = {
        key: value
        for key, value in combined.hits(insertion, hardware).items()
        if not any(
            key.split("/")[0] in pair and key.split("/")[1] in pair
            for pair in insertion_pairs.values()
        )
    }
    insertion_hits |= insertion_hardware_hits
    insertion_clear = {
        bolt: [
            end
            for end in pair
            if not any(key.startswith(f"{end}/") for key in insertion_hits)
        ]
        for bolt, pair in insertion_pairs.items()
    }
    received = {
        name: round(
            sum(wide.hit_volume(bore, parts[wood]) for wood in intended[name])
            / bore.Volume(),
            8,
        )
        for name, bore in bores.items()
    }
    markers = {}
    for name in ("post_cleat_1", "post_cleat_2", "cleat_header_1", "cleat_header_2"):
        start = ends[insertion_pairs[name][0]][0]
        direction = (1, 0, 0) if name.startswith("post") else (0, 0, 1)
        markers[name] = second._member_markers(start, direction, intended[name], parts)
    margins = [
        axis["minimum_margin_mm"]
        for members in markers.values()
        for member in members.values()
        for axis in member.get("distances", {}).values()
    ]
    pitch = {
        "post_cleat": round(abs(post_z[1] - post_z[0]) - 4 * small.DIAMETER, 5),
        "cleat_header": round(
            abs(vertical_x[1] - vertical_x[0]) - 4 * small.DIAMETER, 5
        ),
    }
    new_wood = {"header_post_side_cleat": block}
    checks = {
        "wood_overlaps_mm3": combined.hits(
            new_wood, {k: v for k, v in parts.items() if k not in new_wood}
        ),
        "wood_screw_hits_mm3": combined.hits(new_wood, screws),
        "bore_unintended_wood_hits_mm3": {
            key: value
            for name, bore in bores.items()
            for key, value in combined.hits(
                {name: bore},
                {
                    wood: solid
                    for wood, solid in parts.items()
                    if wood not in intended[name]
                },
            ).items()
        },
        "bore_pair_hits_mm3": _pair_hits(bores),
        "bore_screw_hits_mm3": combined.hits(bores, screws),
        "hardware_wood_hits_mm3": combined.hits(hardware, parts),
        "hardware_screw_hits_mm3": combined.hits(hardware, screws),
        "hardware_pair_hits_mm3": _pair_hits(hardware),
        "washer_face_wood_hits_mm3": combined.hits(seats, parts),
        "washer_face_screw_hits_mm3": combined.hits(seats, screws),
        "socket_body_wood_hits_mm3": combined.hits(sockets, parts),
        "socket_body_screw_hits_mm3": combined.hits(sockets, screws),
        "socket_body_pair_hits_mm3": _pair_hits(sockets),
        "socket_body_cross_hardware_hits_mm3": {
            key: value
            for key, value in combined.hits(sockets, hardware).items()
            if key.split("/")[0] != key.split("/")[1]
        },
    }
    clear = (
        min(margins) >= 0
        and min(pitch.values()) >= 0
        and all(value == 1 for value in received.values())
        and all(value == 1 for value in washers.values())
        and all(insertion_clear.values())
        and all(not value for value in checks.values())
    )
    return {
        "block_bounds_mm": [177.65, 266.55, -175.7, -86.8, bottom, 238.9],
        "post_axis_y_mm": post_y,
        "post_axis_z_mm": post_z,
        "vertical_axis_x_mm": vertical_x,
        "new_bores": list(bores)[-4:],
        "all_bores_checked": list(bores),
        "bore_received_fraction": received,
        "washer_bearing_fraction": washers,
        "conditional_member_markers": markers,
        "conditional_4d_pitch_margin_mm": pitch,
        "minimum_conditional_edge_end_margin_mm": min(margins),
        "conditional_markers_pass": min(margins) >= 0 and min(pitch.values()) >= 0,
        "clear_insertion_ends_by_bolt": insertion_clear,
        "illustrative_insertion_allowance_mm": INSERTION_ALLOWANCE,
        "insertion_other_bolt_hardware_hits_mm3": insertion_hardware_hits,
        "collision_checks": checks,
        "nominal_geometry": "feasible" if clear else "rejected",
    }


@lru_cache(maxsize=1)
def probe():
    """Screen three named revisions without a continuous search or native solve."""
    baseline = tolerance.evaluate(prior.POSE)
    counts, screws = frame._fixed_screws()
    return {
        "pose_coordinates_mm": baseline["coordinates_mm"],
        "baseline_nominal_geometry": baseline["nominal_geometry"],
        "fixed_axes": counts,
        "fixed_screw_axes_checked": len(screws),
        "inner_kicker_edges_supported": baseline["inner_kicker_edges_supported"],
        "variants": {name: _candidate(config) for name, config in VARIANTS.items()},
        "conditional_markers_only": True,
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
