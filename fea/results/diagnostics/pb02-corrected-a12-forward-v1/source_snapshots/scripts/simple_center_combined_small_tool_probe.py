"""Independent PB-02 combined cleat trial with a catalog socket body envelope."""

import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_combined_cleats_probe as combined
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_link_edge_probe as link
from scripts import simple_center_wide_post_probe as wide

# GEARWRENCH 80112, Dim A/B = .618 in, overall length = .965 in.
SOCKET_RADIUS = 0.618 * 25.4 / 2
SOCKET_LENGTH = 0.965 * 25.4
DIAMETER = 6.35
EDGE_RESERVE = 4 * DIAMETER + 5
END_RESERVE = 7 * DIAMETER

# Grain follows Y. Lowering the top clears the fixed upright's end hardware.
CLEAT_BOUNDS = (-20.0, 50.95, -190.0, -45.0, 277.0, 338.0)
VERTICAL_Y = -145.3
CROSS_Y = -95.0
CROSS_Z = 307.5


def _fraction(shape, wood):
    return round(wide.hit_volume(shape, wood) / shape.Volume(), 8)


def _pair_hits(shapes):
    items = list(shapes.items())
    return {
        f"{name}/{other}": round(volume, 5)
        for index, (name, shape) in enumerate(items)
        for other, second in items[index + 1 :]
        if (volume := wide.hit_volume(shape, second)) > wide.TOL
    }


def probe():
    """Screen one nominal assembly; no bought bolt stack or wrench swing is assumed."""
    baseline = link.probe()
    cleat = cq.Solid.makeBox(70.95, 145, 61, cq.Vector(-20, -190, 277))
    new_wood = {
        "header_post_side_cleat": combined.NEW_WOOD["header_post_side_cleat"],
        "header_side_cleat": cleat,
    }
    parts = frame._parts() | new_wood
    counts, screws = frame._fixed_screws()
    bores = combined.new_bores() | {
        "header_cleat": combined.cylinder(
            wide.BORE_RADIUS, 99.1, (15.475, VERTICAL_Y, 238.9), (0, 0, 1)
        ),
        "cleat_principal": combined.cylinder(
            wide.BORE_RADIUS, 109.05, (-20, CROSS_Y, CROSS_Z), (1, 0, 0)
        ),
    }
    old_bores = combined.inherited_bores()
    new_ends = combined.NEW_ENDS | {
        "principal_header_bottom": (
            (15.475, VERTICAL_Y, 238.9),
            (0, 0, -1),
            "base_header",
        ),
        "principal_cleat_top": (
            (15.475, VERTICAL_Y, 338),
            (0, 0, 1),
            "header_side_cleat",
        ),
        "principal_cleat_left": (
            (-20, CROSS_Y, CROSS_Z),
            (-1, 0, 0),
            "header_side_cleat",
        ),
        "principal_right": (
            (89.05, CROSS_Y, CROSS_Z),
            (1, 0, 0),
            "base_principal_center_right",
        ),
    }
    old_ends = combined.INHERITED_ENDS
    new_washers, new_seats, new_hardware, _ = combined.end_envelopes(new_ends, parts)
    old_washers, old_seats, old_hardware, old_tools = combined.end_envelopes(
        old_ends, parts
    )
    all_ends = new_ends | old_ends
    sockets = {
        name: combined.cylinder(SOCKET_RADIUS, SOCKET_LENGTH, point, outward)
        for name, (point, outward, _) in all_ends.items()
    }
    intended = combined.INTENDED | {
        "post_low": ("rear_cleat", "shifted_right_post"),
        "post_high": ("rear_cleat", "shifted_right_post"),
        "upright": ("base_principal_center_right", "upright_side_cleat"),
        "cleat_link": ("rear_cleat", "upright_side_cleat"),
    }
    all_bores = bores | old_bores
    received = {
        name: round(
            sum(wide.hit_volume(bore, parts[wood]) for wood in intended[name])
            / bore.Volume(),
            8,
        )
        for name, bore in all_bores.items()
    }
    header_receivers = {
        name: _fraction(screw, parts["base_header"])
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
        center_receivers[name] = _fraction(screws[name].cut(kicker), parts[wood])
    x0, x1, y0, y1, z0, z1 = CLEAT_BOUNDS
    distances = {
        "vertical_cleat_x_transverse_mm": [15.475 - x0, x1 - 15.475],
        "vertical_header_y_transverse_mm": [VERTICAL_Y + 175.7, -36 - VERTICAL_Y],
        "vertical_cleat_y_grain_ends_mm": [VERTICAL_Y - y0, y1 - VERTICAL_Y],
        "cross_cleat_z_transverse_mm": [CROSS_Z - z0, z1 - CROSS_Z],
        "cross_cleat_y_grain_ends_mm": [CROSS_Y - y0, y1 - CROSS_Y],
        "cross_principal_rear_y_grain_offset_mm": CROSS_Y + 182.7,
    }
    transverse = [
        value
        for key, values in distances.items()
        if key.endswith("transverse_mm")
        for value in values
    ]
    grain_ends = [
        value
        for key, values in distances.items()
        if key.endswith("grain_ends_mm")
        for value in values
    ]
    reserves_pass = (
        min(transverse) >= EDGE_RESERVE - 1e-6 and min(grain_ends) >= END_RESERVE - 1e-6
    )
    checks = {
        "wood_overlaps_mm3": combined.hits(
            new_wood, {k: v for k, v in parts.items() if k not in new_wood}
        )
        | combined.hits(
            {"header_side_cleat": cleat},
            {"header_post_side_cleat": new_wood["header_post_side_cleat"]},
        ),
        "bore_unintended_wood_hits_mm3": {
            key: volume
            for name, bore in all_bores.items()
            for key, volume in combined.hits(
                {name: bore},
                {
                    wood: solid
                    for wood, solid in parts.items()
                    if wood not in intended[name]
                },
            ).items()
        },
        "bore_pair_hits_mm3": _pair_hits(all_bores),
        "wood_screw_hits_mm3": combined.hits(new_wood, screws),
        "bore_screw_hits_mm3": combined.hits(all_bores, screws),
        "hardware_wood_hits_mm3": combined.hits(new_hardware | old_hardware, parts),
        "hardware_screw_hits_mm3": combined.hits(new_hardware | old_hardware, screws),
        "washer_face_wood_hits_mm3": combined.hits(new_seats | old_seats, parts),
        "socket_body_wood_hits_mm3": combined.hits(sockets, parts),
        "socket_body_screw_hits_mm3": combined.hits(sockets, screws),
        "socket_body_cross_hardware_hits_mm3": {
            key: volume
            for key, volume in combined.hits(
                sockets, new_hardware | old_hardware
            ).items()
            if key.split("/")[0] != key.split("/")[1]
        },
        "socket_body_pair_hits_mm3": _pair_hits(sockets),
    }
    accepted = (
        baseline["fixed_axes"] == counts == {"panel": 48, "kicker": 18}
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
        and len(screws) == 66
        and all(baseline["inner_kicker_edges_supported"].values())
        and len(header_receivers) == 10
        and set(header_receivers.values()) == {0.7125}
        and len(center_receivers) == 4
        and set(center_receivers.values()) == {1.0}
        and all(value == 1 for value in received.values())
        and all(value == 1 for value in (new_washers | old_washers).values())
        and reserves_pass
        and all(not value for value in checks.values())
    )
    return {
        "pose": "shortened/repositioned principal cleat; inherited upright unchanged",
        "cleat_bounds_mm": CLEAT_BOUNDS,
        "principal_axes_mm": {
            "header_cleat_xy": [15.475, VERTICAL_Y],
            "cleat_principal_yz": [CROSS_Y, CROSS_Z],
        },
        "upright_axis_yz_mm": [-147.3, 350],
        "fixed_axes": counts,
        "fixed_screw_axes_checked": len(screws),
        "inner_kicker_edges_supported": baseline["inner_kicker_edges_supported"],
        "header_screw_receiver_fraction": header_receivers,
        "center_kicker_screw_receiver_fraction": center_receivers,
        "bore_received_fraction": received,
        "washer_bearing_fraction": new_washers | old_washers,
        "conditional_distances_mm": distances,
        "conditional_4d_plus_5mm_edge_reserve_mm": EDGE_RESERVE,
        "conditional_7d_cleat_end_reserve_mm": END_RESERVE,
        "conditional_reserves_pass": reserves_pass,
        "socket_body_radius_mm": round(SOCKET_RADIUS, 4),
        "socket_body_length_mm": round(SOCKET_LENGTH, 3),
        "upright_20mm_tool_new_wood_hits_mm3": combined.hits(
            {"upright_left": old_tools["upright_left"]}, new_wood
        ),
        **checks,
        "nominal_socket_body_geometry": "feasible" if accepted else "rejected",
        "ratchet_or_extension_sweep_verified": False,
        "fabrication_ready": False,
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
