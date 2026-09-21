"""Finite PB-02 principal corner-block alternatives; occupied geometry only."""

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
from scripts import simple_center_second_bolt_probe as markers
from scripts import simple_center_second_bolt_tolerance_probe as prior
from scripts import simple_center_tolerance_pose_probe as tolerance
from scripts import simple_center_wide_post_probe as wide

# Plain rectangular crosscuts/rips, grain along Y. Both bolts on both faces
# are specified explicitly; these are finite trials, not an optimizer.
VARIANTS = {
    "compact_y": {
        "bounds": (-20.0, 50.95, -200.0, -45.0, 277.0, 348.0),
        "header_y": (-145.0, -80.0),
        "principal_y": (-155.0, -95.0),
        "principal_z": 312.5,
    },
    "rear_reach": {
        "bounds": (-20.0, 50.95, -235.0, -45.0, 277.0, 348.0),
        "header_y": (-150.0, -90.0),
        "principal_y": (-170.0, -100.0),
        "principal_z": 312.5,
    },
    "forward_reach": {
        "bounds": (-20.0, 50.95, -205.0, 5.0, 277.0, 348.0),
        "header_y": (-155.0, -95.0),
        "principal_y": (-130.0, -50.0),
        "principal_z": 312.5,
    },
    "rightward_stock": {
        "bounds": (-15.0, 50.95, -205.0, 0.0, 277.0, 348.0),
        "header_y": (-150.0, -95.0),
        "principal_y": (-125.0, -55.0),
        "principal_z": 312.5,
    },
}

BASE_ENDS = {
    "post_cleat": ("post_left", "post_cleat_right"),
    "cleat_header": ("post_cleat_bottom", "post_header_top"),
    "post_low": ("post_rear_low", "post_front_low"),
    "post_high": ("post_rear_high", "post_front_high"),
    "upright": ("upright_left", "upright_right"),
    "cleat_link": ("link_rear", "link_front"),
}
INTENDED = combined.INTENDED | {
    "post_low": ("rear_cleat", "shifted_right_post"),
    "post_high": ("rear_cleat", "shifted_right_post"),
    "upright": ("base_principal_center_right", "upright_side_cleat"),
    "cleat_link": ("rear_cleat", "upright_side_cleat"),
}


def _pair_hits(shapes):
    items = list(shapes.items())
    return {
        f"{name}/{other}": round(volume, 5)
        for index, (name, solid) in enumerate(items)
        for other, second in items[index + 1 :]
        if (volume := wide.hit_volume(solid, second)) > wide.TOL
    }


def _fraction(shape, wood):
    return round(wide.hit_volume(shape, wood) / shape.Volume(), 8)


def _layout(spec, base_parts, original_bores, original_ends):
    x0, x1, y0, y1, z0, z1 = spec["bounds"]
    block = cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))
    parts = base_parts | {"header_side_cleat": block}
    bores = {name: original_bores[name] for name in BASE_ENDS}
    ends = {end: original_ends[end] for pair in BASE_ENDS.values() for end in pair}
    end_pairs = dict(BASE_ENDS)
    groups = {}
    for face, positions in (
        ("header_cleat", spec["header_y"]),
        ("cleat_principal", spec["principal_y"]),
    ):
        names = []
        for number, y in enumerate(positions, 1):
            name = f"{face}_{number}"
            if face == "header_cleat":
                start, finish = (15.475, y, 238.9), (15.475, y, z1)
                direction = (0, 0, 1)
                owners = ("base_header", "header_side_cleat")
            else:
                z = spec["principal_z"]
                start, finish = (x0, y, z), (89.05, y, z)
                direction = (1, 0, 0)
                owners = ("header_side_cleat", "base_principal_center_right")
            length = sum(abs(b - a) for a, b in zip(start, finish))
            bores[name] = combined.cylinder(wide.BORE_RADIUS, length, start, direction)
            near, far = f"{name}_near", f"{name}_far"
            ends[near] = (start, tuple(-value for value in direction), owners[0])
            ends[far] = (finish, direction, owners[1])
            end_pairs[name] = (near, far)
            names.append(name)
        separation = abs(positions[1] - positions[0])
        groups[face] = {
            "axes": names,
            "axis_y_mm": positions,
            "spacing_mm": separation,
            "conditional_4d_pitch_margin_mm": round(separation - 4 * small.DIAMETER, 5),
            "conditional_7d_pitch_comparator_mm": round(
                separation - 7 * small.DIAMETER, 5
            ),
            "member_edge_end_trial_markers": {
                name: markers._member_markers(
                    ends[end_pairs[name][0]][0],
                    (0, 0, 1) if face == "header_cleat" else (1, 0, 0),
                    INTENDED[face],
                    parts,
                )
                for name in names
            },
        }
    return parts, block, bores, ends, end_pairs, groups


def _screen(spec, base_parts, original_bores, original_ends, screws, baseline):
    parts, block, bores, ends, end_pairs, groups = _layout(
        spec, base_parts, original_bores, original_ends
    )
    intended = {
        name: INTENDED[name.rsplit("_", 1)[0]]
        if name.endswith(("_1", "_2"))
        else INTENDED[name]
        for name in bores
    }
    washers, seats, hardware, _ = combined.end_envelopes(ends, parts)
    sockets = {
        name: combined.cylinder(
            small.SOCKET_RADIUS, small.SOCKET_LENGTH, point, outward
        )
        for name, (point, outward, _) in ends.items()
    }
    insertion = {}
    end_bolt = {end: bolt for bolt, pair in end_pairs.items() for end in pair}
    for pair in end_pairs.values():
        start, finish = (ends[name][0] for name in pair)
        length = sum(abs(b - a) for a, b in zip(start, finish))
        for name in pair:
            point, outward, _ = ends[name]
            insertion[name] = combined.cylinder(
                wide.BORE_RADIUS, length + tolerance.INSERTION_ALLOWANCE, point, outward
            )
    received = {
        name: {wood: _fraction(bore, parts[wood]) for wood in intended[name]}
        for name, bore in bores.items()
    }
    center_receivers = {}
    for name, wood in (
        ("round_kicker_left_center_1", "base_post_center_left"),
        ("round_kicker_left_center_2", "base_post_center_left"),
        ("round_kicker_right_center_1", "backer"),
        ("round_kicker_right_center_2", "backer"),
    ):
        kicker = parts["kicker_left" if "_left_" in name else "kicker_right"]
        center_receivers[name] = _fraction(screws[name].cut(kicker), parts[wood])
    header_receivers = {
        name: _fraction(screw, parts["base_header"])
        for name, screw in screws.items()
        if name.startswith("kicker_header_")
    }
    checks = {
        "wood_overlaps_mm3": combined.hits(
            {"block": block},
            {k: v for k, v in parts.items() if k != "header_side_cleat"},
        ),
        "block_screw_hits_mm3": combined.hits({"block": block}, screws),
        "bore_unintended_wood_hits_mm3": {
            key: value
            for name, bore in bores.items()
            for key, value in combined.hits(
                {name: bore},
                {k: v for k, v in parts.items() if k not in intended[name]},
            ).items()
        },
        "bore_pair_hits_mm3": _pair_hits(bores),
        "bore_screw_hits_mm3": combined.hits(bores, screws),
        "hardware_wood_hits_mm3": combined.hits(hardware, parts),
        "hardware_screw_hits_mm3": combined.hits(hardware, screws),
        "hardware_pair_hits_mm3": _pair_hits(hardware),
        "washer_other_wood_hits_mm3": {
            key: value
            for name, seat in seats.items()
            for key, value in combined.hits(
                {name: seat}, {k: v for k, v in parts.items() if k != ends[name][2]}
            ).items()
        },
        "washer_screw_hits_mm3": combined.hits(seats, screws),
        "washer_pair_hits_mm3": _pair_hits(seats),
        "socket_wood_hits_mm3": combined.hits(sockets, parts),
        "socket_screw_hits_mm3": combined.hits(sockets, screws),
        "socket_pair_hits_mm3": _pair_hits(sockets),
        "socket_hardware_hits_mm3": {
            key: value
            for key, value in combined.hits(sockets, hardware).items()
            if key.split("/")[0] != key.split("/")[1]
        },
        "insertion_wood_hits_mm3": combined.hits(insertion, parts),
        "insertion_screw_hits_mm3": combined.hits(insertion, screws),
        "insertion_other_hardware_hits_mm3": {
            key: value
            for key, value in combined.hits(insertion, hardware).items()
            if key.split("/")[1] not in end_pairs[end_bolt[key.split("/")[0]]]
        },
    }
    insertion_clear = {
        bolt: [
            end
            for end in pair
            if not any(
                key.startswith(f"{end}/")
                for key in (
                    checks["insertion_wood_hits_mm3"]
                    | checks["insertion_screw_hits_mm3"]
                    | checks["insertion_other_hardware_hits_mm3"]
                )
            )
        ]
        for bolt, pair in end_pairs.items()
    }
    nominal_fit = (
        all(
            all(value > 0 for value in values.values()) and sum(values.values()) == 1
            for values in received.values()
        )
        and all(value == 1 for value in washers.values())
        and all(insertion_clear.values())
        and not any(
            value for key, value in checks.items() if not key.startswith("insertion_")
        )
        and set(center_receivers.values()) == {1.0}
        and header_receivers == baseline["header_screw_receiver_fraction"]
        and all(baseline["inner_kicker_edges_supported"].values())
    )
    # Conditional Y windows assume 4D header edge and 7D block grain-end
    # markers, a 4D pair pitch, and 10 mm exposed washer/hardware radius.
    header_rear = wide.bounds(parts["base_header"])[2]
    backer_rear = wide.bounds(parts["backer"])[2]
    principal_front_window = (
        wide.bounds(parts["upright_side_cleat"])[3] + 10,
        spec["bounds"][3] - 7 * small.DIAMETER,
    )
    return {
        "block_bounds_mm": spec["bounds"],
        "bores_checked": list(bores),
        "bolt_groups": groups,
        "bore_intended_wood_fraction": received,
        "washer_bearing_fraction": washers,
        "insertion_clear_ends": insertion_clear,
        "center_kicker_screw_receiver_fraction": center_receivers,
        "header_screw_receiver_fraction": header_receivers,
        "principal_grain_status": "oblique grain/end unclassified",
        "conditional_header_rear_y_window_mm": (
            round(header_rear + 4 * small.DIAMETER, 5),
            round(backer_rear - 10, 5),
        ),
        "conditional_principal_front_y_window_mm": tuple(
            round(value, 5) for value in principal_front_window
        ),
        "checks": checks,
        "nominal_collision_fit": nominal_fit,
    }


def probe():
    """Rebuild and recheck every inherited and changed axis for four stock cuts."""
    baseline = tolerance.evaluate(prior.POSE)
    base_parts, original_bores, original_ends = prior._geometry()
    counts, screws = frame._fixed_screws()
    trials = {
        name: _screen(spec, base_parts, original_bores, original_ends, screws, baseline)
        for name, spec in VARIANTS.items()
    }
    return {
        "pose_coordinates_mm": asdict(prior.POSE),
        "baseline_nominal_geometry": baseline["nominal_geometry"],
        "fixed_axes": counts,
        "fixed_screw_axes_checked": len(screws),
        "inner_kicker_edges_supported": baseline["inner_kicker_edges_supported"],
        "center_kicker_screw_receiver_fraction": baseline[
            "center_kicker_screw_receiver_fraction"
        ],
        "variants": trials,
        "conditional_markers_only": True,
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
