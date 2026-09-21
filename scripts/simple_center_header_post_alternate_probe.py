"""One nominal PB-02 recessed-header/rear-cleat bolt geometry trial."""

import csv
import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_link_edge_probe as link
from scripts import simple_center_wide_post_probe as wide

HEADER_FRONT_Y = -61.4
BOLT_X = 140.0
BOLT_Z = 251.6
D = 6.35


def probe():
    """Check one ordinary Y bolt after a full-length rectangular header rip."""
    prior = link.probe()
    parts = {part.name: part.shape for part in wide.frame.uncut_wood_parts()}
    parts.pop("base_post_center_right")
    original_header = parts["base_header"]
    header = cq.Solid.makeBox(
        2438.4,
        HEADER_FRONT_Y + 175.7,
        38.1,
        cq.Vector(-1219.2, -175.7, 238.9),
    )
    parts.update(
        base_header=header,
        shifted_right_post=cq.Solid.makeBox(
            88.9, 88.9, wide.POST_TOP, cq.Vector(wide.POST_X, wide.POST_REAR_Y, 0)
        ),
        backer=wide.BACKER,
        rear_cleat=cq.Solid.makeBox(88.9, 38.1, 460, cq.Vector(89.05, -213.8, 0)),
        upright_side_cleat=link.SIDE,
    )
    bore = cq.Solid.makeCylinder(
        wide.BORE_RADIUS,
        HEADER_FRONT_Y + 213.8,
        cq.Vector(BOLT_X, -213.8, BOLT_Z),
        cq.Vector(0, 1, 0),
    )
    intended = ("rear_cleat", "base_header")
    received = {
        name: round(wide.hit_volume(bore, parts[name]) / bore.Volume(), 8)
        for name in intended
    }
    expected = {
        "rear_cleat": round(38.1 / 152.4, 8),
        "base_header": round(114.3 / 152.4, 8),
    }
    full_bore = received == expected and round(sum(received.values()), 8) == 1
    unintended = {
        name: round(volume, 5)
        for name, wood in parts.items()
        if name not in intended
        if (volume := wide.hit_volume(bore, wood)) > wide.TOL
    }
    fixed_hits = {}
    counts = {"panel": 0, "kicker": 0}
    header_screw_receiver = {}
    for row in csv.DictReader(wide.AXES.open(newline="")):
        name = row["name"]
        if name.startswith("round_panel_"):
            counts["panel"] += 1
        elif name.startswith(("round_kicker_", "kicker_header_")):
            counts["kicker"] += 1
        else:
            continue
        screw = cq.Solid.makeCylinder(
            float(row["modeled_diameter_mm"]) / 2,
            float(row["shop_purchased_length_mm"]),
            cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz")),
            cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz")),
        )
        if (volume := wide.hit_volume(bore, screw)) > wide.TOL:
            fixed_hits[name] = round(volume, 5)
        if name.startswith("kicker_header_"):
            header_screw_receiver[name] = round(
                wide.hit_volume(screw, header) / screw.Volume(), 8
            )
    existing = {
        "post_low": (140, 110, 127),
        "post_high": (140, 190, 127),
        "cleat_link": (133.5, 370, 94.9),
    }
    other_bores = {
        name: cq.Solid.makeCylinder(
            wide.BORE_RADIUS,
            length,
            cq.Vector(x, -213.8, z),
            cq.Vector(0, 1, 0),
        )
        for name, (x, z, length) in existing.items()
    }
    other_bores["upright"] = cq.Solid.makeCylinder(
        wide.BORE_RADIUS, 127, cq.Vector(50.95, -147.3, 350), cq.Vector(1, 0, 0)
    )
    bore_hits = {
        name: round(volume, 5)
        for name, other in other_bores.items()
        if (volume := wide.hit_volume(bore, other)) > wide.TOL
    }
    washers, hardware_hits, tool_hits = {}, {}, {}
    for end, (y, direction, owner) in {
        "rear": (-213.8, -1, "rear_cleat"),
        "front": (HEADER_FRONT_Y, 1, "base_header"),
    }.items():
        point = cq.Vector(BOLT_X, y, BOLT_Z)
        outward = cq.Vector(0, direction, 0)
        washer = cq.Solid.makeCylinder(10, 0.01, point, outward.multiply(-1))
        washers[end] = round(wide.hit_volume(washer, parts[owner]) / washer.Volume(), 8)
        for target, radius, length in ((hardware_hits, 10, 5), (tool_hits, 20, 20)):
            cylinder = cq.Solid.makeCylinder(radius, length, point, outward)
            target[end] = {
                name: round(volume, 5)
                for name, wood in parts.items()
                if (volume := wide.hit_volume(cylinder, wood)) > wide.TOL
            }
    header_edges = [round(BOLT_Z - 238.9, 5), round(277 - BOLT_Z, 5)]
    # The original header alone provided the strip behind both inner kicker edges.
    edge_support = {
        side: header.isInside(cq.Vector(-1.5875, -36.1, 257.95), wide.TOL)
        and prior["inner_kicker_edges_supported"][side]
        for side in ("left", "right")
    }
    one_direction = header_edges[0] >= 1.5 * D and header_edges[1] >= 4 * D
    reversible_edges = min(header_edges) >= 4 * D
    accepted = (
        counts == {"panel": 48, "kicker": 18}
        and all(edge_support.values())
        and full_bore
        and not unintended
        and not fixed_hits
        and not bore_hits
        and all(value == 1 for value in washers.values())
        and not any(hardware_hits.values())
        and not any(tool_hits.values())
        and reversible_edges
    )
    return {
        "pose": "rectangular full-length header front-Y rip, one rear-cleat Y bolt",
        "accepted_geometry": accepted,
        "header_bounds_mm": wide.bounds(header),
        "original_header_bounds_mm": wide.bounds(original_header),
        "header_bolt_axis_xyz_mm": [BOLT_X, -213.8, BOLT_Z],
        "header_bolt_span_y_mm": [-213.8, HEADER_FRONT_Y],
        "illustrative_bore_diameter_mm": 2 * wide.BORE_RADIUS,
        "fixed_axes": counts,
        "inner_kicker_edges_supported": edge_support,
        "header_screw_receiver_fraction": header_screw_receiver,
        "removed_legacy_stations": prior["removed_legacy_stations"],
        "bore_received_fraction_by_member": received,
        "full_intended_bore_received": full_bore,
        "bore_unintended_wood_hits_mm3": unintended,
        "bore_fixed_screw_hits_mm3": fixed_hits,
        "bore_existing_bore_hits_mm3": bore_hits,
        "washer_bearing_fraction": washers,
        "external_hardware_wood_hits_mm3": hardware_hits,
        "tool_wood_hits_mm3": tool_hits,
        "header_z_edge_distances_mm": header_edges,
        "conditional_4d_mm": 4 * D,
        "conditional_1_5d_mm": 1.5 * D,
        "conditional_one_direction_z_edges_pass": one_direction,
        "conditional_reversible_z_edges_pass": reversible_edges,
        "cleat_x_edge_distances_mm": [50.95, 37.95],
        "cleat_z_end_distances_mm": [BOLT_Z, 460 - BOLT_Z],
        "nearest_existing_bolt_z_separation_mm": BOLT_Z - 190,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
