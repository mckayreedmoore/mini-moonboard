"""Diagnostic kerf-right center-post offset; not a joint design or drill plan."""

import csv
import json
import math
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mini_moonboard import compact_floor_flush_frame as frame

AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
PROFILES = ROOT / "docs/floor-flush-construction-kerf-right/stock-profiles.json"
TOL = 1e-3
TRIAL_NOMINAL_BOLT_DIAMETER_MM = 9.525
TRIAL_BORE_DIAMETER_MM = 10.5
NDS_HOLE_MIN_MM = TRIAL_NOMINAL_BOLT_DIAMETER_MM + 0.79375
NDS_HOLE_MAX_MM = TRIAL_NOMINAL_BOLT_DIAMETER_MM + 1.5875


def bounds(shape):
    box = shape.BoundingBox()
    return [
        round(value, 5)
        for value in (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
    ]


def probe():
    """Measure a 37.8 mm right-post move with a full-section 4x6 backer."""
    assert NDS_HOLE_MIN_MM <= TRIAL_BORE_DIAMETER_MM <= NDS_HOLE_MAX_MM
    parts = {part.name: part.shape for part in frame.uncut_wood_parts()}
    axes = list(csv.DictReader(AXES.open(newline="")))
    profiles = json.loads(PROFILES.read_text())
    panel_axes = [row for row in axes if row["name"].startswith("round_panel_")]
    kicker_axes = [
        row
        for row in axes
        if row["name"].startswith(("round_kicker_", "kicker_header_"))
    ]
    assert len(panel_axes) == 48 and len(kicker_axes) == 18

    left = parts["base_post_center_left"]
    shifted = parts["base_post_center_right"].translate(cq.Vector(37.8, 0, 0))
    # Owner-specified Home Depot 4x6 actual section, with grain vertical.
    backer = cq.Solid.makeBox(139.7, 88.9, 238.9, cq.Vector(-50.95, -124.9, 0))
    other = {
        name: solid for name, solid in parts.items() if name != "base_post_center_right"
    }
    collisions = {}
    for trial_name, trial in (("shifted_post", shifted), ("backer", backer)):
        hits = {
            name: round(trial.intersect(solid).Volume(), 5)
            for name, solid in other.items()
        }
        collisions[trial_name] = {
            name: volume for name, volume in hits.items() if volume > TOL
        }

    screws = {}
    occupied_kicker_screws = {}
    for row in kicker_axes:
        x = float(row["start_x_mm"])
        z = float(row["start_z_mm"])
        start_y = float(row["start_y_mm"])
        direction = cq.Vector(
            float(row["direction_x"]),
            float(row["direction_y"]),
            float(row["direction_z"]),
        )
        assert direction == cq.Vector(0, -1, 0)
        panel_back_y = -36.0
        purchased_length = float(row["shop_purchased_length_mm"])
        assert purchased_length == 63.5
        end_y = start_y - purchased_length
        occupied_kicker_screws[row["name"]] = cq.Solid.makeCylinder(
            float(row["modeled_diameter_mm"]) / 2,
            purchased_length,
            cq.Vector(x, start_y, z),
            direction,
        )
        embed = cq.Solid.makeCylinder(
            float(row["modeled_diameter_mm"]) / 2,
            panel_back_y - end_y,
            cq.Vector(x, panel_back_y, z),
            cq.Vector(0, -1, 0),
        )
        receiver_name = (
            "backer"
            if row["name"].startswith("round_kicker_right_center_")
            else row["second_member"]
        )
        receiver = backer if receiver_name == "backer" else parts[receiver_name]
        received = embed.intersect(receiver).Volume()
        screws[row["name"]] = {
            "receiver": receiver_name,
            "start_xyz_mm": [x, start_y, z],
            "direction_xyz": list(direction.toTuple()),
            "x_z_mm": [x, z],
            "purchased_length_mm": purchased_length,
            "modeled_length_mm": float(row["modeled_length_mm"]),
            "purchased_tip_y_mm": round(end_y, 5),
            "receiving_wood_length_mm": round(panel_back_y - end_y, 5),
            "full_length_bore_received_fraction": round(received / embed.Volume(), 8),
            "tip_inside_receiver": receiver.isInside(cq.Vector(x, end_y, z), TOL),
            "tip_to_receiver_rear_face_mm": round(
                end_y - receiver.BoundingBox().ymin, 5
            ),
        }

    edges = {}
    for name in ("kicker_left", "kicker_right"):
        x_coordinates = [vertex[0] for vertex in profiles[name]["vertices_world_mm"]]
        inner = max(x_coordinates) if name.endswith("left") else min(x_coordinates)
        edges[name] = {
            "inner_x_mm": inner,
            "backer_under_edge": backer.isInside(cq.Vector(inner, -36.1, 120), TOL),
            "backer_contact_z_mm": [0, 238.9],
            "header_under_top_segment": parts["base_header"].isInside(
                cq.Vector(inner, -36.1, 257.95), TOL
            ),
            "header_contact_z_mm": [238.9, 277.0],
        }

    # A 10.5 mm diagnostic bore for an illustrated 3/8 in nominal bolt.
    # The 20 mm radius side-access cylinders are also diagnostic only.
    # Purchased bolts, washers, nuts and realistic tool engagement are open.
    bolt_checks = {}
    for z in (105.0, 145.0):
        bore = cq.Solid.makeCylinder(
            TRIAL_BORE_DIAMETER_MM / 2,
            216.2,
            cq.Vector(-89.2, -80.0, z),
            cq.Vector(1, 0, 0),
        )
        access = {
            "left": cq.Solid.makeCylinder(
                20.0, 20.0, cq.Vector(-109.05, -80.0, z), cq.Vector(1, 0, 0)
            ),
            "right": cq.Solid.makeCylinder(
                20.0, 20.0, cq.Vector(126.85, -80.0, z), cq.Vector(1, 0, 0)
            ),
        }
        access_hits = {
            side: {
                name: round(envelope.intersect(solid).Volume(), 5)
                for name, solid in other.items()
                if envelope.intersect(solid).Volume() > TOL
            }
            for side, envelope in access.items()
        }
        bolt_checks[str(z)] = {
            "illustrated_nominal_bolt_diameter_mm": TRIAL_NOMINAL_BOLT_DIAMETER_MM,
            "diagnostic_bore_diameter_mm": TRIAL_BORE_DIAMETER_MM,
            "nds_2024_nominal_hole_interval_mm": [
                NDS_HOLE_MIN_MM,
                NDS_HOLE_MAX_MM,
            ],
            "diagnostic_bore_within_interval": (
                NDS_HOLE_MIN_MM <= TRIAL_BORE_DIAMETER_MM <= NDS_HOLE_MAX_MM
            ),
            "received_fraction_by_member": {
                "left_post": round(
                    bore.intersect(left).Volume()
                    / (math.pi * (TRIAL_BORE_DIAMETER_MM / 2) ** 2 * 38.1),
                    8,
                ),
                "backer": round(
                    bore.intersect(backer).Volume()
                    / (math.pi * (TRIAL_BORE_DIAMETER_MM / 2) ** 2 * 139.7),
                    8,
                ),
                "shifted_right_post": round(
                    bore.intersect(shifted).Volume()
                    / (math.pi * (TRIAL_BORE_DIAMETER_MM / 2) ** 2 * 38.1),
                    8,
                ),
            },
            "nearby_fixed_kicker_screw_z_clearance_mm": min(abs(z - 60), abs(z - 192)),
            "backer_y_axis_to_front_edge_mm": 44.0,
            "backer_y_axis_to_rear_edge_mm": 44.9,
            "purchased_kicker_screw_envelope_hits_mm3": {
                name: round(bore.intersect(screw).Volume(), 5)
                for name, screw in occupied_kicker_screws.items()
                if bore.intersect(screw).Volume() > TOL
            },
            "trial_access_radius_mm": 20.0,
            "trial_access_front_panel_clearance_mm": 24.0,
            "access_envelope_hits_mm3": access_hits,
        }

    return {
        "fixed_axes_count": {"panel": len(panel_axes), "kicker": len(kicker_axes)},
        "left_post_bounds_xyz_mm": bounds(left),
        "shifted_right_post_bounds_xyz_mm": bounds(shifted),
        "backer_bounds_xyz_mm": bounds(backer),
        "post_to_backer_gap_mm": {
            "left": round(backer.BoundingBox().xmin - left.BoundingBox().xmax, 5),
            "right": round(shifted.BoundingBox().xmin - backer.BoundingBox().xmax, 5),
        },
        "solid_overlap_mm3": collisions,
        "kicker_screws": screws,
        "inner_kicker_edges": edges,
        "trial_bolts": bolt_checks,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
