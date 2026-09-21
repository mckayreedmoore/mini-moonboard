"""One nominal PB-02 solid deep-header and shifted-post geometry screen."""

import csv
import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_link_edge_probe as link
from scripts import simple_center_wide_post_probe as wide

HEADER_BOTTOM = 188.1
HEADER_FRONT = -61.4
BOLT_X = 140.0
BOLT_Z = 232.55
POST_BOLT_Z = (80.0, 140.0)
NOMINAL_D = 6.35


def _hits(solid, parts, exclude=()):
    return {
        name: round(volume, 5)
        for name, wood in parts.items()
        if name not in exclude
        if (volume := wide.hit_volume(solid, wood)) > wide.TOL
    }


def probe():
    """Screen the one 4x4-depth pose without treating geometry as design approval."""
    parts = {part.name: part.shape for part in wide.frame.uncut_wood_parts()}
    original_header = parts["base_header"]
    parts.pop("base_post_center_right")
    header = cq.Solid.makeBox(
        2438.4, HEADER_FRONT + 175.7, 88.9, cq.Vector(-1219.2, -175.7, HEADER_BOTTOM)
    )
    post = cq.Solid.makeBox(
        88.9, 88.9, HEADER_BOTTOM, cq.Vector(wide.POST_X, wide.POST_REAR_Y, 0)
    )
    parts.update(
        base_header=header,
        shifted_right_post=post,
        backer=wide.BACKER,
        rear_cleat=cq.Solid.makeBox(88.9, 38.1, 460, cq.Vector(89.05, -213.8, 0)),
        upright_side_cleat=link.SIDE,
    )
    header_overlap = _hits(header, parts, ("base_header",))
    post_overlap = _hits(post, parts, ("shifted_right_post",))
    bore = cq.Solid.makeCylinder(
        wide.BORE_RADIUS,
        HEADER_FRONT + 213.8,
        cq.Vector(BOLT_X, -213.8, BOLT_Z),
        cq.Vector(0, 1, 0),
    )
    intended = ("rear_cleat", "base_header")
    received = {
        name: round(wide.hit_volume(bore, parts[name]) / bore.Volume(), 8)
        for name in intended
    }
    post_bores = {
        f"post_{label}": cq.Solid.makeCylinder(
            wide.BORE_RADIUS, 127, cq.Vector(BOLT_X, -213.8, z), cq.Vector(0, 1, 0)
        )
        for label, z in zip(("low", "high"), POST_BOLT_Z)
    }
    prior_bores = {
        **post_bores,
        "cleat_link": cq.Solid.makeCylinder(
            wide.BORE_RADIUS, 94.9, cq.Vector(133.5, -213.8, 370), cq.Vector(0, 1, 0)
        ),
        "upright": cq.Solid.makeCylinder(
            wide.BORE_RADIUS, 127, cq.Vector(50.95, -147.3, 350), cq.Vector(1, 0, 0)
        ),
    }
    all_bores = {"header": bore, **prior_bores}
    bore_pairs = {
        f"{name}/{other_name}": round(volume, 5)
        for i, (name, occupied) in enumerate(all_bores.items())
        for other_name, other in list(all_bores.items())[i + 1 :]
        if (volume := wide.hit_volume(occupied, other)) > wide.TOL
    }
    post_bore_received = {
        name: round(
            sum(
                wide.hit_volume(occupied, parts[wood])
                for wood in ("rear_cleat", "shifted_right_post")
            )
            / occupied.Volume(),
            8,
        )
        for name, occupied in post_bores.items()
    }
    post_bore_unintended = {
        name: _hits(occupied, parts, ("rear_cleat", "shifted_right_post"))
        for name, occupied in post_bores.items()
    }
    counts = {"panel": 0, "kicker": 0}
    screw_hits = {}
    header_receivers = {}
    original_header_receivers = {}
    center_kicker_receivers = {}
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
        for bore_name, occupied in {"header": bore, **post_bores}.items():
            if (volume := wide.hit_volume(occupied, screw)) > wide.TOL:
                screw_hits[f"{bore_name}/{name}"] = round(volume, 5)
        if name.startswith("kicker_header_"):
            header_receivers[name] = round(
                wide.hit_volume(screw, header) / screw.Volume(), 8
            )
            original_header_receivers[name] = round(
                wide.hit_volume(screw, original_header) / screw.Volume(), 8
            )
        if name in {
            "round_kicker_left_center_1",
            "round_kicker_left_center_2",
            "round_kicker_right_center_1",
            "round_kicker_right_center_2",
        }:
            side = "left" if "_left_" in name else "right"
            exposed = screw.cut(parts[f"kicker_{side}"])
            receiver = "base_post_center_left" if side == "left" else "backer"
            center_kicker_receivers[name] = round(
                wide.hit_volume(exposed, parts[receiver]) / exposed.Volume(), 8
            )
    washers, hardware_hits, tool_hits = {}, {}, {}
    for end, (y, direction, owner) in {
        "rear": (-213.8, -1, "rear_cleat"),
        "front": (HEADER_FRONT, 1, "base_header"),
    }.items():
        point = cq.Vector(BOLT_X, y, BOLT_Z)
        outward = cq.Vector(0, direction, 0)
        washer = cq.Solid.makeCylinder(10, 0.01, point, outward.multiply(-1))
        washers[end] = round(wide.hit_volume(washer, parts[owner]) / washer.Volume(), 8)
        hardware_hits[end] = _hits(cq.Solid.makeCylinder(10, 5, point, outward), parts)
        tool_hits[end] = _hits(cq.Solid.makeCylinder(20, 20, point, outward), parts)
    # Each fixed inner edge needs the header's original front contact plane.
    edge_support = {
        side: header.isInside(cq.Vector(-1.5875, -36.1, 257.95), wide.TOL)
        for side in ("left", "right")
    }
    z_edges = [round(BOLT_Z - HEADER_BOTTOM, 5), round(277 - BOLT_Z, 5)]
    accepted = (
        counts == {"panel": 48, "kicker": 18}
        and not header_overlap
        and not post_overlap
        and all(edge_support.values())
        and all(value == 1 for value in header_receivers.values())
        and all(value == 1 for value in center_kicker_receivers.values())
        and all(value == 1 for value in post_bore_received.values())
        and not any(post_bore_unintended.values())
        and received
        == {
            "rear_cleat": round(38.1 / 152.4, 8),
            "base_header": round(114.3 / 152.4, 8),
        }
        and not _hits(bore, parts, intended)
        and not bore_pairs
        and not screw_hits
        and all(value == 1 for value in washers.values())
        and not any(hardware_hits.values())
        and not any(tool_hits.values())
        and min(z_edges) >= 4 * NOMINAL_D
    )
    return {
        "pose": "one full-length solid 114.3 x 88.9 mm header, front recess, shortened right post",
        "accepted_geometry": accepted,
        "header_bounds_mm": wide.bounds(header),
        "original_header_bounds_mm": wide.bounds(original_header),
        "shifted_post_bounds_mm": wide.bounds(post),
        "post_bolt_z_mm": list(POST_BOLT_Z),
        "header_bolt_axis_xyz_mm": [BOLT_X, -213.8, BOLT_Z],
        "header_bolt_span_y_mm": [-213.8, HEADER_FRONT],
        "header_new_overlap_mm3": header_overlap,
        "shifted_post_unintended_wood_overlap_mm3": post_overlap,
        "relocated_post_bore_received_fraction": post_bore_received,
        "relocated_post_bore_unintended_wood_hits_mm3": post_bore_unintended,
        "fixed_axes": counts,
        "inner_kicker_edges_supported": edge_support,
        "header_screw_receiver_fraction": header_receivers,
        "original_header_screw_receiver_fraction": original_header_receivers,
        "center_kicker_screw_receiver_fraction": center_kicker_receivers,
        "header_bore_received_fraction_by_member": received,
        "header_bore_unintended_wood_hits_mm3": _hits(bore, parts, intended),
        "new_bore_pair_hits_mm3": bore_pairs,
        "new_bore_fixed_screw_hits_mm3": screw_hits,
        "washer_bearing_fraction": washers,
        "external_hardware_wood_hits_mm3": hardware_hits,
        "tool_wood_hits_mm3": tool_hits,
        "front_nut_tool_clear": not hardware_hits["front"] and not tool_hits["front"],
        "header_z_edge_distances_mm": z_edges,
        "conditional_4d_mm": 4 * NOMINAL_D,
        "conditional_reversible_z_edges_pass": min(z_edges) >= 4 * NOMINAL_D,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
