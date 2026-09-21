"""Bounded nominal header-to-shifted-post rear-cleat through-bolt trial."""

import csv
import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_link_edge_probe as link
from scripts import simple_center_wide_post_probe as wide


def probe():
    """Try one Y-axis bolt through the existing continuous rear cleat and header."""
    base = link.probe()
    parts = {part.name: part.shape for part in wide.frame.uncut_wood_parts()}
    parts.pop("base_post_center_right")
    parts.update(
        shifted_right_post=cq.Solid.makeBox(
            88.9, 88.9, wide.POST_TOP, cq.Vector(wide.POST_X, wide.POST_REAR_Y, 0)
        ),
        backer=wide.BACKER,
        rear_cleat=cq.Solid.makeBox(88.9, 38.1, 460, cq.Vector(89.05, -213.8, 0)),
        upright_side_cleat=link.SIDE,
    )
    # The existing rear cleat is one solid rectangular member across the
    # post/header Z joint. The post-to-cleat bolts belong to the prior pose.
    x, z = 140.0, 257.95
    bore = cq.Solid.makeCylinder(
        wide.BORE_RADIUS, 177.8, cq.Vector(x, -213.8, z), cq.Vector(0, 1, 0)
    )
    intended = ("rear_cleat", "base_header")
    received = {
        name: round(wide.hit_volume(bore, parts[name]) / bore.Volume(), 8)
        for name in intended
    }
    received_total = round(sum(received.values()), 8)
    expected_rear_fraction = round(38.1 / 177.8, 8)
    expected_header_fraction = round(139.7 / 177.8, 8)
    full_intended_bore = (
        received_total == 1
        and received["rear_cleat"] == expected_rear_fraction
        and received["base_header"] == expected_header_fraction
    )
    header_z_edge = round(min(z - 238.9, 277 - z), 5)
    unintended = {
        name: round(volume, 5)
        for name, wood in parts.items()
        if name not in intended
        if (volume := wide.hit_volume(bore, wood)) > wide.TOL
    }
    fixed = {}
    count = 0
    for row in csv.DictReader(wide.AXES.open(newline="")):
        name = row["name"]
        if not name.startswith(("round_panel_", "round_kicker_", "kicker_header_")):
            continue
        count += 1
        screw = cq.Solid.makeCylinder(
            float(row["modeled_diameter_mm"]) / 2,
            float(row["shop_purchased_length_mm"]),
            cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz")),
            cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz")),
        )
        if (volume := wide.hit_volume(bore, screw)) > wide.TOL:
            fixed[name] = round(volume, 5)
    ends = {
        "rear": (cq.Vector(x, -213.8, z), cq.Vector(0, -1, 0), "rear_cleat"),
        "front": (cq.Vector(x, -36, z), cq.Vector(0, 1, 0), "base_header"),
    }
    tools = {}
    bearing = {}
    external_hardware_hits = {}
    for end, (point, direction, owner) in ends.items():
        tool = cq.Solid.makeCylinder(20, 20, point, direction)
        tools[end] = {
            name: round(volume, 5)
            for name, wood in parts.items()
            if (volume := wide.hit_volume(tool, wood)) > wide.TOL
        }
        washer = cq.Solid.makeCylinder(10, 0.01, point, direction.multiply(-1))
        bearing[end] = round(wide.hit_volume(washer, parts[owner]) / washer.Volume(), 8)
        # Illustrative washer/nut occupation outside the timber face.
        hardware = cq.Solid.makeCylinder(10, 5, point, direction)
        external_hardware_hits[end] = {
            name: round(volume, 5)
            for name, wood in parts.items()
            if (volume := wide.hit_volume(hardware, wood)) > wide.TOL
        }
    existing = {
        "post_low": (140, 110),
        "post_high": (140, 190),
        "cleat_link": (133.5, 370),
    }
    bores = {
        name: cq.Solid.makeCylinder(
            wide.BORE_RADIUS,
            127 if name.startswith("post") else 94.9,
            cq.Vector(axis_x, -213.8, axis_z),
            cq.Vector(0, 1, 0),
        )
        for name, (axis_x, axis_z) in existing.items()
    }
    bores["upright"] = cq.Solid.makeCylinder(
        wide.BORE_RADIUS,
        127,
        cq.Vector(50.95, -147.3, 350),
        cq.Vector(1, 0, 0),
    )
    bore_hits = {
        name: round(volume, 5)
        for name, other in bores.items()
        if (volume := wide.hit_volume(bore, other)) > wide.TOL
    }
    # Front-end access is required after the fixed kicker is installed.
    accepted = (
        base["fixed_axes"] == {"panel": 48, "kicker": 18}
        and all(base["inner_kicker_edges_supported"].values())
        and count == 66
        and set(base["removed_legacy_stations"])
        == {"clip_split_base_center_right", "clip_split_header_center_right"}
        and full_intended_bore
        and not unintended
        and not fixed
        and not bore_hits
        and all(value == 1 for value in bearing.values())
        and not any(external_hardware_hits.values())
        and not any(tools.values())
    )
    return {
        "pose": "existing full-section rear cleat, one header Y-through-bolt",
        "accepted_geometry": accepted,
        "header_bolt_axis_xyz_mm": [x, -213.8, z],
        "illustrative_bore_diameter_mm": 2 * wide.BORE_RADIUS,
        "header_bolt_span_y_mm": [-213.8, -36],
        "continuous_rear_cleat_bounds_mm": wide.bounds(parts["rear_cleat"]),
        "post_bounds_mm": wide.bounds(parts["shifted_right_post"]),
        "header_bounds_mm": wide.bounds(parts["base_header"]),
        "existing_post_bolt_axes_xz_mm": [
            list(axis) for axis in list(existing.values())[:2]
        ],
        "fixed_axes": base["fixed_axes"],
        "fixed_axes_checked": count,
        "inner_kicker_edges_supported": base["inner_kicker_edges_supported"],
        "removed_legacy_stations": base["removed_legacy_stations"],
        "bore_received_fraction_by_member": received,
        "bore_received_fraction_total": received_total,
        "full_intended_bore_received": full_intended_bore,
        "bore_unintended_wood_hits_mm3": unintended,
        "bore_fixed_screw_hits_mm3": fixed,
        "bore_existing_bore_hits_mm3": bore_hits,
        "washer_bearing_fraction": bearing,
        "trial_external_10mm_radius_5mm_hardware_wood_hits_mm3": external_hardware_hits,
        "trial_20mm_radius_tool_wood_hits_mm3": tools,
        "front_end_blocked_by_installed_kicker": (
            "kicker_right" in external_hardware_hits["front"]
            or "kicker_right" in tools["front"]
        ),
        "conditional_header_nearest_z_edge_mm": header_z_edge,
        "conditional_4d_mm": 25.4,
        "conditional_4d_header_z_shortfall_mm": round(25.4 - header_z_edge, 5),
        "conditional_1_5d_mm": 9.525,
        "conditional_reversible_required_header_z_mm": 50.8,
        "conditional_one_direction_required_header_z_mm": 34.925,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
