"""Finite second-bolt geometry screen at the PB-02 tolerance pose; no drill release."""

import json
import sys
from dataclasses import asdict
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_combined_cleats_probe as combined
from scripts import simple_center_combined_small_tool_probe as small
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_second_bolt_probe as prior
from scripts import simple_center_tolerance_pose_probe as tolerance
from scripts import simple_center_wide_post_probe as wide

# Tangential shifts chosen near one bolt pitch in the available member faces.
# This finite set is a bounded sample, not a continuous optimization.
OFFSETS = prior.OFFSETS
POSE = tolerance.Pose(
    vertical_y=-139, top_z=348, cross_z=312.5, upright_y=-135, upright_z=360
)


def _hits(shapes, targets):
    return combined.hits(shapes, targets)


def _fraction(shape, wood):
    return round(wide.hit_volume(shape, wood) / shape.Volume(), 8)


def _geometry():
    """Recreate the eight axes and end planes used by the maintained pose producer."""
    p = POSE
    cleat = cq.Solid.makeBox(
        70.95, -45 - p.rear_y, p.top_z - 277, cq.Vector(-20, p.rear_y, 277)
    )
    parts = frame._parts() | {
        "header_post_side_cleat": combined.NEW_WOOD["header_post_side_cleat"],
        "header_side_cleat": cleat,
    }
    bores = combined.new_bores() | {
        "header_cleat": combined.cylinder(
            wide.BORE_RADIUS, p.top_z - 238.9, (15.475, p.vertical_y, 238.9), (0, 0, 1)
        ),
        "cleat_principal": combined.cylinder(
            wide.BORE_RADIUS, 109.05, (-20, -95, p.cross_z), (1, 0, 0)
        ),
    }
    bores |= combined.inherited_bores() | {
        "upright": combined.cylinder(
            wide.BORE_RADIUS, 127, (50.95, p.upright_y, p.upright_z), (1, 0, 0)
        ),
        "cleat_link": combined.cylinder(
            wide.BORE_RADIUS, 94.9, (p.link_x, -213.8, 370), (0, 1, 0)
        ),
    }
    ends = combined.NEW_ENDS | {
        "principal_header_bottom": (
            (15.475, p.vertical_y, 238.9),
            (0, 0, -1),
            "base_header",
        ),
        "principal_cleat_top": (
            (15.475, p.vertical_y, p.top_z),
            (0, 0, 1),
            "header_side_cleat",
        ),
        "principal_cleat_left": (
            (-20, -95, p.cross_z),
            (-1, 0, 0),
            "header_side_cleat",
        ),
        "principal_right": (
            (89.05, -95, p.cross_z),
            (1, 0, 0),
            "base_principal_center_right",
        ),
    }
    ends |= combined.INHERITED_ENDS | {
        "upright_left": (
            (50.95, p.upright_y, p.upright_z),
            (-1, 0, 0),
            "base_principal_center_right",
        ),
        "upright_right": (
            (177.95, p.upright_y, p.upright_z),
            (1, 0, 0),
            "upright_side_cleat",
        ),
        "link_rear": ((p.link_x, -213.8, 370), (0, -1, 0), "rear_cleat"),
        "link_front": ((p.link_x, -118.9, 370), (0, 1, 0), "upright_side_cleat"),
    }
    return parts, bores, ends


def probe():
    """Check four named offsets per interface, retaining each nominal failure."""
    baseline = tolerance.evaluate(POSE)
    parts, bores, first_ends = _geometry()
    counts, screws = frame._fixed_screws()
    _, _, old_hardware, _ = combined.end_envelopes(first_ends, parts)
    old_sockets = {
        name: combined.cylinder(
            small.SOCKET_RADIUS, small.SOCKET_LENGTH, point, outward
        )
        for name, (point, outward, _) in first_ends.items()
    }
    interfaces = {}
    for name, offsets in OFFSETS.items():
        start_name, finish_name = prior.ENDS[name]
        start, _, start_owner = first_ends[start_name]
        finish, _, finish_owner = first_ends[finish_name]
        direction = tuple(
            1 if b > a else -1 if b < a else 0 for a, b in zip(start, finish)
        )
        length = sum(abs(b - a) for a, b in zip(start, finish))
        intended = combined.INTENDED[name]
        trials = []
        for label, offset in offsets.items():
            near = tuple(a + d for a, d in zip(start, offset))
            far = tuple(a + d for a, d in zip(finish, offset))
            ends = {
                "second_near": (near, tuple(-v for v in direction), start_owner),
                "second_far": (far, direction, finish_owner),
            }
            bore = combined.cylinder(wide.BORE_RADIUS, length, near, direction)
            washers, seats, hardware, _ = combined.end_envelopes(ends, parts)
            sockets = {
                key: combined.cylinder(
                    small.SOCKET_RADIUS, small.SOCKET_LENGTH, point, outward
                )
                for key, (point, outward, _) in ends.items()
            }
            insertion = {
                key: combined.cylinder(
                    wide.BORE_RADIUS,
                    length + tolerance.INSERTION_ALLOWANCE,
                    point,
                    outward,
                )
                for key, (point, outward, _) in ends.items()
            }
            insertion_hits = (
                _hits(insertion, parts)
                | _hits(insertion, screws)
                | _hits(insertion, old_hardware)
            )
            markers = prior._member_markers(near, direction, intended, parts)
            spacing = round(sum(v * v for v in offset) ** 0.5, 5)
            checks = {
                "intended_wood_fraction": {
                    wood: _fraction(bore, parts[wood]) for wood in intended
                },
                "washer_bearing_fraction": washers,
                "unintended_wood_hits_mm3": _hits(
                    {"second": bore},
                    {
                        wood: solid
                        for wood, solid in parts.items()
                        if wood not in intended
                    },
                ),
                "other_bore_hits_mm3": _hits({"second": bore}, bores),
                "fixed_screw_hits_mm3": _hits({"second": bore}, screws),
                "hardware_wood_hits_mm3": _hits(hardware, parts),
                "hardware_screw_hits_mm3": _hits(hardware, screws),
                "hardware_other_hardware_hits_mm3": _hits(hardware, old_hardware),
                "hardware_other_socket_hits_mm3": _hits(hardware, old_sockets),
                "washer_other_wood_hits_mm3": _hits(
                    seats,
                    {
                        wood: solid
                        for wood, solid in parts.items()
                        if wood not in intended
                    },
                ),
                "washer_screw_hits_mm3": _hits(seats, screws),
                "washer_other_hardware_hits_mm3": _hits(seats, old_hardware),
                "socket_wood_hits_mm3": _hits(sockets, parts),
                "socket_screw_hits_mm3": _hits(sockets, screws),
                "socket_other_hardware_hits_mm3": _hits(sockets, old_hardware),
                "socket_other_socket_hits_mm3": _hits(sockets, old_sockets),
                "insertion_clear_ends": [
                    end
                    for end in ends
                    if not any(key.startswith(f"{end}/") for key in insertion_hits)
                ],
            }
            marker_margins = [
                axis["minimum_margin_mm"]
                for member in markers.values()
                for axis in member.get("distances", {}).values()
            ]
            marker_status = (
                "fails measured trial marker"
                if any(value < 0 for value in marker_margins)
                else "incomplete: oblique member unclassified"
                if any(
                    member["status"] == "oblique grain/end unclassified"
                    for member in markers.values()
                )
                else "passes measured trial markers only"
            )
            collision_fit = (
                all(value > 0 for value in checks["intended_wood_fraction"].values())
                and abs(sum(checks["intended_wood_fraction"].values()) - 1) < 1e-6
                and all(value == 1 for value in washers.values())
                and bool(checks["insertion_clear_ends"])
                and not any(
                    value for key, value in checks.items() if key.endswith("hits_mm3")
                )
            )
            trials.append(
                {
                    "offset": label,
                    "offset_xyz_mm": offset,
                    "axis_start_xyz_mm": near,
                    "axis_end_xyz_mm": far,
                    "axis_spacing_mm": spacing,
                    "conditional_4d_pitch_margin_mm": round(
                        spacing - 4 * small.DIAMETER, 5
                    ),
                    "conditional_7d_distance_comparator_mm": round(
                        spacing - 7 * small.DIAMETER, 5
                    ),
                    "member_edge_end_trial_markers": markers,
                    "trial_marker_status": marker_status,
                    "minimum_measured_marker_margin_mm": min(marker_margins)
                    if marker_margins
                    else None,
                    "checks": checks,
                    "collision_fit": collision_fit,
                }
            )
        interfaces[name] = {
            "first_axis_start_xyz_mm": start,
            "first_axis_end_xyz_mm": finish,
            "intended_woods": intended,
            "trials": trials,
            "any_collision_fit": any(trial["collision_fit"] for trial in trials),
            "any_collision_fit_and_measured_markers": any(
                trial["collision_fit"]
                and trial["trial_marker_status"] == "passes measured trial markers only"
                for trial in trials
            ),
        }
    return {
        "pose_coordinates_mm": asdict(POSE),
        "baseline_nominal_geometry": baseline["nominal_geometry"],
        "fixed_axes": counts,
        "fixed_screw_axes_checked": len(screws),
        "inner_kicker_edges_supported": baseline["inner_kicker_edges_supported"],
        "existing_bores_checked": list(bores),
        "offset_bounds_mm": {
            name: {
                axis: [
                    min(offset[i] for offset in offsets.values()),
                    max(offset[i] for offset in offsets.values()),
                ]
                for i, axis in enumerate("xyz")
            }
            for name, offsets in OFFSETS.items()
        },
        "conditional_markers_only": True,
        "conditional_marker_D_mm": small.DIAMETER,
        "interfaces": interfaces,
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
