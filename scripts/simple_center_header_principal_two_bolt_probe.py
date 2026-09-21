"""Finite PB-02 header/principal two-bolt block trials; geometry only."""

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
from scripts import simple_center_second_bolt_tolerance_probe as prior
from scripts import simple_center_tolerance_pose_probe as tolerance
from scripts import simple_center_wide_post_probe as wide

# All dimensions are global mm. The first axes and every other part stay at POSE.
# These are physical crosscuts/rips of solid stock, with grain along Y.
VARIANTS = {
    "left_and_front": {
        "bounds": (-55.0, 50.95, -190.0, -5.0, 277.0, 348.0),
        "vertical_second": (-19.525, -139.0),
        "cross_second": (-50.0, 312.5),
    },
    "left_and_rear": {
        "bounds": (-55.0, 50.95, -225.0, -45.0, 277.0, 348.0),
        "vertical_second": (-19.525, -139.0),
        "cross_second": (-140.0, 312.5),
    },
    "left_and_tall": {
        "bounds": (-55.0, 50.95, -190.0, -45.0, 277.0, 385.0),
        "vertical_second": (-19.525, -139.0),
        "cross_second": (-95.0, 352.5),
    },
}


def _hits(shapes, targets):
    return combined.hits(shapes, targets)


def _fraction(shape, wood):
    return round(wide.hit_volume(shape, wood) / shape.Volume(), 8)


def _pair_hits(shapes):
    entries = list(shapes.items())
    return {
        f"{name}/{other}": round(volume, 5)
        for index, (name, solid) in enumerate(entries)
        for other, second in entries[index + 1 :]
        if (volume := wide.hit_volume(solid, second)) > wide.TOL
    }


def _markers(center, direction, owners, parts):
    """Centerline trial reserves; the inclined principal remains unclassified."""
    return prior.prior._member_markers(center, direction, owners, parts)


def _face(name, first, second, ends, parts, bores, screws, old_hardware, old_sockets):
    intended = combined.INTENDED[name]
    axis = (0, 0, 1) if name == "header_cleat" else (1, 0, 0)
    start, finish = second
    length = sum(abs(b - a) for a, b in zip(start, finish))
    new_ends = {
        f"{name}_near": (start, tuple(-v for v in axis), intended[0]),
        f"{name}_far": (finish, axis, intended[1]),
    }
    bore = combined.cylinder(wide.BORE_RADIUS, length, start, axis)
    washers, seats, hardware, _ = combined.end_envelopes(new_ends, parts)
    sockets = {
        key: combined.cylinder(small.SOCKET_RADIUS, small.SOCKET_LENGTH, point, out)
        for key, (point, out, _) in new_ends.items()
    }
    insertion = {
        key: combined.cylinder(
            wide.BORE_RADIUS, length + tolerance.INSERTION_ALLOWANCE, point, out
        )
        for key, (point, out, _) in new_ends.items()
    }
    insertion_hits = (
        _hits(insertion, parts)
        | _hits(insertion, screws)
        | _hits(insertion, old_hardware)
    )
    markers = _markers(start, axis, intended, parts)
    offset = tuple(b - a for a, b in zip(first[0], start))
    spacing = round(sum(v * v for v in offset) ** 0.5, 5)
    checks = {
        "intended_wood_fraction": {
            wood: _fraction(bore, parts[wood]) for wood in intended
        },
        "washer_bearing_fraction": washers,
        "unintended_wood_hits_mm3": _hits(
            {"second": bore}, {k: v for k, v in parts.items() if k not in intended}
        ),
        "other_bore_hits_mm3": _hits({"second": bore}, bores),
        "fixed_screw_hits_mm3": _hits({"second": bore}, screws),
        "hardware_wood_hits_mm3": _hits(hardware, parts),
        "hardware_screw_hits_mm3": _hits(hardware, screws),
        "hardware_other_hardware_hits_mm3": _hits(hardware, old_hardware),
        "hardware_other_socket_hits_mm3": _hits(hardware, old_sockets),
        "washer_other_wood_hits_mm3": _hits(
            seats, {k: v for k, v in parts.items() if k not in intended}
        ),
        "washer_screw_hits_mm3": _hits(seats, screws),
        "washer_other_hardware_hits_mm3": _hits(seats, old_hardware),
        "socket_wood_hits_mm3": _hits(sockets, parts),
        "socket_screw_hits_mm3": _hits(sockets, screws),
        "socket_other_hardware_hits_mm3": _hits(sockets, old_hardware),
        "socket_other_socket_hits_mm3": _hits(sockets, old_sockets),
        "insertion_clear_ends": [
            key
            for key in new_ends
            if not any(hit.startswith(f"{key}/") for hit in insertion_hits)
        ],
    }
    margins = [
        detail["minimum_margin_mm"]
        for member in markers.values()
        for detail in member.get("distances", {}).values()
    ]
    fit = (
        all(value > 0 for value in checks["intended_wood_fraction"].values())
        and abs(sum(checks["intended_wood_fraction"].values()) - 1) < 1e-6
        and all(value == 1 for value in washers.values())
        and bool(checks["insertion_clear_ends"])
        and not any(value for key, value in checks.items() if key.endswith("hits_mm3"))
    )
    return (
        {
            "name": name,
            "axes": [first, second],
            "spacing_mm": spacing,
            "conditional_4d_pitch_margin_mm": round(spacing - 4 * small.DIAMETER, 5),
            "member_edge_end_trial_markers": markers,
            "minimum_measured_marker_margin_mm": min(margins) if margins else None,
            "principal_grain_note": (
                "oblique principal grain/end unclassified; box coordinates are not an NDS verdict"
                if name == "cleat_principal"
                else "no principal in this face"
            ),
            "second_bolt_checks": checks,
            "second_bolt_collision_fit": fit,
        },
        bore,
        hardware,
        sockets,
        seats,
    )


def probe():
    """Evaluate three finite cut/coordinate sets against the complete pose."""
    baseline = tolerance.evaluate(prior.POSE)
    base_parts, original_bores, original_ends = prior._geometry()
    counts, screws = frame._fixed_screws()
    trials = {}
    for name, spec in VARIANTS.items():
        x0, x1, y0, y1, z0, z1 = spec["bounds"]
        block = cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))
        parts = base_parts | {"header_side_cleat": block}
        ends = original_ends | {
            "principal_cleat_top": ((15.475, -139, z1), (0, 0, 1), "header_side_cleat"),
            "principal_cleat_left": ((x0, -95, 312.5), (-1, 0, 0), "header_side_cleat"),
        }
        bores = original_bores | {
            "header_cleat": combined.cylinder(
                wide.BORE_RADIUS, z1 - 238.9, (15.475, -139, 238.9), (0, 0, 1)
            ),
            "cleat_principal": combined.cylinder(
                wide.BORE_RADIUS, 89.05 - x0, (x0, -95, 312.5), (1, 0, 0)
            ),
        }
        original_washers, original_seats, old_hardware, _ = combined.end_envelopes(
            ends, parts
        )
        old_sockets = {
            key: combined.cylinder(small.SOCKET_RADIUS, small.SOCKET_LENGTH, point, out)
            for key, (point, out, _) in ends.items()
        }
        second = {
            "header_cleat": (
                (spec["vertical_second"][0], spec["vertical_second"][1], 238.9),
                (spec["vertical_second"][0], spec["vertical_second"][1], z1),
            ),
            "cleat_principal": (
                (x0, spec["cross_second"][0], spec["cross_second"][1]),
                (89.05, spec["cross_second"][0], spec["cross_second"][1]),
            ),
        }
        faces, new_bores, new_hardware, new_sockets, new_seats = {}, {}, {}, {}, {}
        for face_name, second_axis in second.items():
            first = (
                ((15.475, -139, 238.9), (15.475, -139, z1))
                if face_name == "header_cleat"
                else ((x0, -95, 312.5), (89.05, -95, 312.5))
            )
            face, bore, hardware, sockets, seats = _face(
                face_name,
                first,
                second_axis,
                ends,
                parts,
                bores | new_bores,
                screws,
                old_hardware | new_hardware,
                old_sockets | new_sockets,
            )
            faces[face_name] = face
            new_bores[face_name] = bore
            new_hardware.update(hardware)
            new_sockets.update(sockets)
            new_seats.update(seats)
        other_wood = {k: v for k, v in parts.items() if k != "header_side_cleat"}
        first_received = {
            key: round(
                sum(
                    wide.hit_volume(bore, parts[wood])
                    for wood in combined.INTENDED[key]
                )
                / bore.Volume(),
                8,
            )
            for key, bore in bores.items()
            if key in ("header_cleat", "cleat_principal")
        }
        original_insertion = {}
        for end_names in prior.prior.ENDS.values():
            start, finish = (ends[key][0] for key in end_names)
            length = sum(abs(b - a) for a, b in zip(start, finish))
            for key in end_names:
                point, outward, _ = ends[key]
                original_insertion[key] = combined.cylinder(
                    wide.BORE_RADIUS,
                    length + tolerance.INSERTION_ALLOWANCE,
                    point,
                    outward,
                )
        checks = {
            "block_other_wood_hits_mm3": _hits({"block": block}, other_wood),
            "block_fixed_screw_hits_mm3": _hits({"block": block}, screws),
            "first_bore_unintended_wood_hits_mm3": {
                hit: volume
                for key in ("header_cleat", "cleat_principal")
                for hit, volume in _hits(
                    {key: bores[key]},
                    {
                        wood: solid
                        for wood, solid in parts.items()
                        if wood not in combined.INTENDED[key]
                    },
                ).items()
            },
            "first_bore_fixed_screw_hits_mm3": _hits(
                {key: bores[key] for key in ("header_cleat", "cleat_principal")},
                screws,
            ),
            "original_bore_wood_hits_mm3": _hits(
                {
                    k: v
                    for k, v in bores.items()
                    if k not in ("header_cleat", "cleat_principal")
                },
                {"header_side_cleat": block},
            ),
            "original_hardware_wood_hits_mm3": _hits(old_hardware, parts),
            "original_hardware_screw_hits_mm3": _hits(old_hardware, screws),
            "original_socket_wood_hits_mm3": _hits(old_sockets, parts),
            "original_socket_screw_hits_mm3": _hits(old_sockets, screws),
            "original_washer_other_wood_hits_mm3": _hits(original_seats, other_wood),
            "original_insertion_new_block_hits_mm3": _hits(
                original_insertion, {"header_side_cleat": block}
            ),
            "original_insertion_screw_hits_mm3": _hits(original_insertion, screws),
            "new_bore_pair_hits_mm3": _pair_hits(new_bores),
            "new_hardware_pair_hits_mm3": _pair_hits(new_hardware),
            "new_socket_pair_hits_mm3": _pair_hits(new_sockets),
            "new_washer_pair_hits_mm3": _pair_hits(new_seats),
        }
        trials[name] = {
            "block_bounds_mm": spec["bounds"],
            "first_bore_received_fraction": first_received,
            "original_washer_bearing_fraction": original_washers,
            "faces": faces,
            "checks": checks,
            "both_second_bolts_collision_fit": all(
                face["second_bolt_collision_fit"] for face in faces.values()
            ),
        }
    return {
        "pose_coordinates_mm": asdict(prior.POSE),
        "baseline_nominal_geometry": baseline["nominal_geometry"],
        "fixed_axes": counts,
        "fixed_screw_axes_checked": len(screws),
        "inner_kicker_edges_supported": baseline["inner_kicker_edges_supported"],
        "conditional_markers_only": True,
        "variants": trials,
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
