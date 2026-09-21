"""Bounded nominal second-bolt geometry screen for four PB-02 serial interfaces."""

import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_combined_cleats_probe as combined
from scripts import simple_center_combined_small_tool_probe as small
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_wide_post_probe as wide

OFFSETS = {
    "post_cleat": {
        "rear_y": (0, -35, 0),
        "front_y": (0, 35, 0),
        "low_z": (0, 0, -45),
        "high_z": (0, 0, 45),
    },
    "cleat_header": {
        "left_x": (-35, 0, 0),
        "right_x": (35, 0, 0),
        "rear_y": (0, -35, 0),
        "front_y": (0, 35, 0),
    },
    "header_cleat": {
        "left_x": (-35, 0, 0),
        "right_x": (35, 0, 0),
        "rear_y": (0, -35, 0),
        "front_y": (0, 35, 0),
    },
    "cleat_principal": {
        "rear_y": (0, -45, 0),
        "front_y": (0, 45, 0),
        "low_z": (0, 0, -30),
        "high_z": (0, 0, 30),
    },
}

# First-bolt start/end planes are inherited from maintained geometry producers.
ENDS = {
    "post_cleat": ("post_left", "post_cleat_right"),
    "cleat_header": ("post_cleat_bottom", "post_header_top"),
    "header_cleat": ("principal_header_bottom", "principal_cleat_top"),
    "cleat_principal": ("principal_cleat_left", "principal_right"),
}
GRAIN_AXIS = {
    "shifted_right_post": "z",
    "header_post_side_cleat": "z",
    "base_header": "x",
    "header_side_cleat": "y",
}


def _member_markers(center, direction, owners, parts):
    """Report box-boundary centerline distances; rules remain unclassified."""
    result = {}
    for owner in owners:
        if owner not in GRAIN_AXIS:
            result[owner] = {"status": "oblique grain/end unclassified"}
            continue
        bounds = wide.bounds(parts[owner])
        distances = {}
        for index, axis in enumerate("xyz"):
            if direction[index]:
                continue  # Entry/exit faces lie along the bolt, not its row plane.
            low, high = bounds[2 * index : 2 * index + 2]
            marker = (
                7 * small.DIAMETER if axis == GRAIN_AXIS[owner] else 4 * small.DIAMETER
            )
            distances[axis] = {
                "kind": "grain_end" if axis == GRAIN_AXIS[owner] else "transverse_edge",
                "centerline_to_low_high_mm": [
                    round(center[index] - low, 5),
                    round(high - center[index], 5),
                ],
                "conditional_marker_mm": marker,
                "minimum_margin_mm": round(
                    min(center[index] - low, high - center[index]) - marker, 5
                ),
            }
        result[owner] = {
            "status": "box centerline trial markers only",
            "distances": distances,
        }
    return result


def _hits(shapes, targets, exclude_same=False):
    return {
        key: volume
        for key, volume in combined.hits(shapes, targets).items()
        if not exclude_same or key.split("/")[0] != key.split("/")[1]
    }


def probe():
    """Check only named offsets in the maintained revised small-tool pose."""
    baseline = small.probe()
    cleat = cq.Solid.makeBox(70.95, 145, 61, cq.Vector(-20, -190, 277))
    parts = frame._parts() | {
        "header_post_side_cleat": combined.NEW_WOOD["header_post_side_cleat"],
        "header_side_cleat": cleat,
    }
    counts, screws = frame._fixed_screws()
    first_bores = combined.new_bores() | {
        "header_cleat": combined.cylinder(
            wide.BORE_RADIUS, 99.1, (15.475, small.VERTICAL_Y, 238.9), (0, 0, 1)
        ),
        "cleat_principal": combined.cylinder(
            wide.BORE_RADIUS, 109.05, (-20, small.CROSS_Y, small.CROSS_Z), (1, 0, 0)
        ),
    }
    all_bores = first_bores | combined.inherited_bores()
    first_ends = combined.NEW_ENDS | {
        "principal_cleat_top": (
            (15.475, small.VERTICAL_Y, 338),
            (0, 0, 1),
            "header_side_cleat",
        ),
        "principal_cleat_left": (
            (-20, small.CROSS_Y, small.CROSS_Z),
            (-1, 0, 0),
            "header_side_cleat",
        ),
        "principal_right": (
            (89.05, small.CROSS_Y, small.CROSS_Z),
            (1, 0, 0),
            "base_principal_center_right",
        ),
    }
    first_ends["principal_header_bottom"] = (
        (15.475, small.VERTICAL_Y, 238.9),
        (0, 0, -1),
        "base_header",
    )
    first_ends.update(combined.INHERITED_ENDS)
    _, _, old_hardware, _ = combined.end_envelopes(first_ends, parts)
    old_sockets = {
        name: combined.cylinder(
            small.SOCKET_RADIUS, small.SOCKET_LENGTH, point, outward
        )
        for name, (point, outward, _) in first_ends.items()
    }
    interfaces = {}
    for name, offsets in OFFSETS.items():
        start_name, finish_name = ENDS[name]
        start, _, start_owner = first_ends[start_name]
        finish, _, finish_owner = first_ends[finish_name]
        direction = tuple(
            (b - a) / abs(b - a) if b != a else 0 for a, b in zip(start, finish)
        )
        length = sum(abs(b - a) for a, b in zip(start, finish))
        trials = []
        for label, offset in offsets.items():
            low = tuple(a + d for a, d in zip(start, offset))
            high = tuple(a + d for a, d in zip(finish, offset))
            ends = {
                "second_near": (low, tuple(-v for v in direction), start_owner),
                "second_far": (high, direction, finish_owner),
            }
            bore = combined.cylinder(wide.BORE_RADIUS, length, low, direction)
            washers, _, hardware, _ = combined.end_envelopes(ends, parts)
            sockets = {
                key: combined.cylinder(
                    small.SOCKET_RADIUS, small.SOCKET_LENGTH, point, outward
                )
                for key, (point, outward, _) in ends.items()
            }
            spacing = round(sum(v * v for v in offset) ** 0.5, 5)
            markers = _member_markers(low, direction, combined.INTENDED[name], parts)
            checks = {
                "intended_wood_fraction": {
                    wood: round(wide.hit_volume(bore, parts[wood]) / bore.Volume(), 8)
                    for wood in combined.INTENDED[name]
                },
                "washer_bearing_fraction": washers,
                "unintended_wood_hits_mm3": combined.hits(
                    {"second": bore},
                    {
                        wood: solid
                        for wood, solid in parts.items()
                        if wood not in combined.INTENDED[name]
                    },
                ),
                "other_bore_hits_mm3": combined.hits({"second": bore}, all_bores),
                "fixed_screw_hits_mm3": combined.hits({"second": bore}, screws),
                "hardware_wood_hits_mm3": combined.hits(hardware, parts),
                "hardware_screw_hits_mm3": combined.hits(hardware, screws),
                "hardware_other_hardware_hits_mm3": combined.hits(
                    hardware, old_hardware
                ),
                "socket_wood_hits_mm3": combined.hits(sockets, parts),
                "socket_screw_hits_mm3": combined.hits(sockets, screws),
                "socket_other_hardware_hits_mm3": combined.hits(sockets, old_hardware),
                "socket_other_socket_hits_mm3": combined.hits(sockets, old_sockets),
            }
            collision_fit = (
                all(v > 0 for v in checks["intended_wood_fraction"].values())
                and abs(sum(checks["intended_wood_fraction"].values()) - 1) < 1e-6
                and all(v == 1 for v in washers.values())
                and not any(
                    value for key, value in checks.items() if key.endswith("hits_mm3")
                )
            )
            marker_margins = [
                detail["minimum_margin_mm"]
                for member in markers.values()
                for detail in member.get("distances", {}).values()
            ]
            marker_status = (
                "fails measured trial marker"
                if any(v < 0 for v in marker_margins)
                else "incomplete: oblique member unclassified"
                if any(
                    member["status"] == "oblique grain/end unclassified"
                    for member in markers.values()
                )
                else "passes measured trial markers only"
            )
            trials.append(
                {
                    "offset": label,
                    "offset_xyz_mm": offset,
                    "axis_start_xyz_mm": low,
                    "axis_end_xyz_mm": high,
                    "axis_spacing_mm": spacing,
                    "conditional_4d_pitch_margin_mm": round(
                        spacing - 4 * small.DIAMETER, 5
                    ),
                    "conditional_7d_distance_comparator_mm": round(
                        spacing - 7 * small.DIAMETER, 5
                    ),
                    "member_edge_end_trial_markers": markers,
                    "trial_marker_status": marker_status,
                    "checks": checks,
                    "collision_fit": collision_fit,
                }
            )
        interfaces[name] = {
            "first_axis_start_xyz_mm": start,
            "first_axis_end_xyz_mm": finish,
            "trials": trials,
            "any_collision_fit": any(t["collision_fit"] for t in trials),
            "any_collision_fit_and_measured_markers": any(
                t["collision_fit"]
                and t["trial_marker_status"] == "passes measured trial markers only"
                for t in trials
            ),
        }
    return {
        "pose": baseline["pose"],
        "fixed_axes": counts,
        "fixed_screw_axes_checked": len(screws),
        "baseline_nominal_socket_body_geometry": baseline[
            "nominal_socket_body_geometry"
        ],
        "conditional_markers_only": True,
        "conditional_marker_D_mm": small.DIAMETER,
        "interfaces": interfaces,
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
