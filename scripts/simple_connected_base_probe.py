"""Combined kerf-right center-backup and lower-right cleat CAD diagnostic.

No fastener layout, resistance, tolerance, or construction release is implied.
"""

import csv
import json
import math
from itertools import combinations
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.simple_rail_joint_comparison import (
    RAIL,
    UPRIGHT,
    N,
    T,
    _contact_area,
    _yz,
)

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
PROFILES = ROOT / "docs/floor-flush-construction-kerf-right/stock-profiles.json"
HILLMAN = ROOT / "docs/bolted-candidate-hillman-42605-dimensions.json"
VOLUME_TOL_MM3 = 0.01


def _bounds_overlap(first, second):
    a, b = first.BoundingBox(), second.BoundingBox()
    return all(
        (
            getattr(a, f"{axis}min") < getattr(b, f"{axis}max")
            and getattr(b, f"{axis}min") < getattr(a, f"{axis}max")
        )
        for axis in "xyz"
    )


def _intersection_mm3(first, second):
    if not _bounds_overlap(first, second):
        return 0.0
    return first.intersect(second).Volume()


def _pairwise_clashes(parts):
    result = {}
    for (a_name, a), (b_name, b) in combinations(parts.items(), 2):
        volume = _intersection_mm3(a, b)
        if volume > VOLUME_TOL_MM3:
            result[f"{a_name}|{b_name}"] = round(volume, 3)
    return result


def _split_clashes(parts):
    wood = {
        name: solid
        for name, solid in parts.items()
        if not name.startswith(("main_", "kicker_"))
    }
    panels = {
        name: solid
        for name, solid in parts.items()
        if name.startswith(("main_", "kicker_"))
    }
    panel_hits = {}
    for wood_name, solid in wood.items():
        for panel_name, panel in panels.items():
            volume = _intersection_mm3(solid, panel)
            if volume > VOLUME_TOL_MM3:
                panel_hits[f"{wood_name}|{panel_name}"] = round(volume, 3)
    return {
        "wood_wood_mm3": _pairwise_clashes(wood),
        "wood_panel_mm3": panel_hits,
        "panel_panel_mm3": _pairwise_clashes(panels),
    }


def _cleat(rail, upright, length_n):
    """Reproduce the current grain-N 4x6 single/group *wood solid* only."""
    rail_t = [v.Y * T[0] + v.Z * T[1] for v in rail.Vertices()]
    rail_n = [v.Y * N[0] + v.Z * N[1] for v in rail.Vertices()]
    y, z = _yz(max(rail_t), min(rail_n))
    shape = (
        cq.Solid.makeBox(
            139.7, 57.15, length_n, cq.Vector(upright.BoundingBox().xmax, 0, 0)
        )
        .rotate((0, 0, 0), (1, 0, 0), 50)
        .translate((0, y, z))
    )
    return shape, {
        "x_width_mm": 139.7,
        "t_width_mm": 57.15,
        "n_length_mm": length_n,
        "t_near_mm": round(max(rail_t), 3),
        "n_front_mm": round(min(rail_n), 3),
    }


def _screw(row, length, diameter):
    return cq.Solid.makeCylinder(
        diameter / 2,
        length,
        cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz")),
        cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz")),
    )


def _receiver_path(row, length, diameter):
    """Screw portion behind its panel back, through the purchased tip datum."""
    start = cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz"))
    direction = cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz"))
    if row["name"].startswith(("round_kicker_", "kicker_header_")):
        panel_back = -36.0
        if direction != cq.Vector(0, -1, 0):
            raise ValueError("kicker screw direction changed")
        panel_depth = start.y - panel_back
    else:
        # The main panel's 18.25625-mm thickness is measured along its
        # installed normal. This is a comparison path, not a shaft profile.
        panel_depth = 18.25625
    if not 0 < panel_depth < length:
        raise ValueError("purchased screw has no receiver segment")
    return cq.Solid.makeCylinder(
        diameter / 2, length - panel_depth, start + direction * panel_depth, direction
    )


def _axis_checks(original, assembled, rows, purchased_length, proxy_diameter):
    kicker, main = {}, {}
    for row in rows:
        name = row["name"]
        if float(row["shop_purchased_length_mm"]) != purchased_length:
            raise ValueError(f"purchased length mismatch: {name}")
        receiver_name = (
            "center_backer"
            if name.startswith("round_kicker_right_center_")
            else row["second_member"]
        )
        receiver = assembled[receiver_name]
        bore_diameter = float(row["modeled_diameter_mm"])
        legacy_path = _receiver_path(row, purchased_length, bore_diameter)
        proxy_path = _receiver_path(row, purchased_length, proxy_diameter)
        received = _intersection_mm3(legacy_path, receiver)
        proxy_received = _intersection_mm3(proxy_path, receiver)
        record = {
            "receiver": receiver_name,
            "purchased_length_mm": purchased_length,
            "legacy_diameter_mm_not_delivered_shaft": bore_diameter,
            "received_length_mm": round(
                legacy_path.Volume() / (math.pi * (bore_diameter / 2) ** 2), 5
            ),
            "legacy_path_received_fraction": round(received / legacy_path.Volume(), 8),
            "nominal_head_diameter_full_length_proxy_fraction": round(
                proxy_received / proxy_path.Volume(), 8
            ),
        }
        if name.startswith(("round_kicker_", "kicker_header_")):
            kicker[name] = record
        else:
            old_receiver = original[row["second_member"]]
            old_fraction = (
                _intersection_mm3(legacy_path, old_receiver) / legacy_path.Volume()
            )
            record["baseline_receiver_fraction"] = round(old_fraction, 8)
            record["baseline_to_assembled_intersection_delta_mm3"] = round(
                received - _intersection_mm3(legacy_path, old_receiver), 6
            )
            main[name] = record
    return kicker, main


def probe():
    """Measure both alternative cleat solids inside one modified center frame."""
    original = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    with AXES.open(newline="") as stream:
        rows = [
            row
            for row in csv.DictReader(stream)
            if row["shop_opening_kind"] == "hillman_panel"
        ]
    if (
        len(rows) != 66
        or len({row["name"] for row in rows}) != 66
        or sum(row["name"].startswith("round_panel_") for row in rows) != 48
    ):
        raise ValueError("fixed 48-main/18-kicker axis set changed")
    hillman = json.loads(HILLMAN.read_text())
    purchased_length = float(hillman["purchased_length_mm"])
    proxy_diameter = float(hillman["retailer_listed_nominal_head_diameter_mm"])

    baseline_clashes = _split_clashes(original)
    assembled = dict(original)
    assembled["base_post_center_right"] = original["base_post_center_right"].translate(
        cq.Vector(37.8, 0, 0)
    )
    assembled["center_backer"] = cq.Solid.makeBox(
        139.7, 88.9, 238.9, cq.Vector(-50.95, -124.9, 0)
    )
    center_clashes = _split_clashes(assembled)
    center_contacts = {
        "backer_to_left_post": _contact_area(
            assembled["center_backer"], assembled["base_post_center_left"], (-1, 0, 0)
        ),
        "backer_to_shifted_right_post": _contact_area(
            assembled["center_backer"], assembled["base_post_center_right"], (1, 0, 0)
        ),
        "backer_to_header": _contact_area(
            assembled["center_backer"], assembled["base_header"], (0, 0, 1)
        ),
    }
    kicker, main = _axis_checks(
        original, assembled, rows, purchased_length, proxy_diameter
    )
    profiles = json.loads(PROFILES.read_text())
    edge_support = {}
    for panel_name in ("kicker_left", "kicker_right"):
        xs = [point[0] for point in profiles[panel_name]["vertices_world_mm"]]
        inner_x = max(xs) if panel_name.endswith("left") else min(xs)
        edge_support[panel_name] = {
            "inner_x_mm": inner_x,
            "backer_under_edge_at_z120": assembled["center_backer"].isInside(
                cq.Vector(inner_x, -36.1, 120), VOLUME_TOL_MM3
            ),
            "header_under_edge_at_z257_95": assembled["base_header"].isInside(
                cq.Vector(inner_x, -36.1, 257.95), VOLUME_TOL_MM3
            ),
        }

    alternatives = {}
    for name, length_n in (("grain_n_4x6_single", 200.0), ("grain_n_4x6_group", 300.0)):
        shape, datums = _cleat(assembled[RAIL], assembled[UPRIGHT], length_n)
        joined = {**assembled, "rail_cleat": shape}
        clashes = _split_clashes(joined)
        screw_hits = {}
        for row in rows:
            proxy = _screw(row, purchased_length, proxy_diameter)
            volume = _intersection_mm3(shape, proxy)
            if volume > VOLUME_TOL_MM3:
                screw_hits[row["name"]] = round(volume, 3)
        alternatives[name] = {
            "cleat_datums": datums,
            "face_contact_area_mm2": {
                "cleat_to_upright": round(
                    _contact_area(shape, assembled[UPRIGHT], (-1, 0, 0)), 3
                ),
                "cleat_to_rail": round(
                    _contact_area(shape, assembled[RAIL], (0, -T[0], -T[1])), 3
                ),
            },
            "cleat_center_backer_overlap_mm3": round(
                _intersection_mm3(shape, assembled["center_backer"]), 3
            ),
            "cleat_shifted_post_overlap_mm3": round(
                _intersection_mm3(shape, assembled["base_post_center_right"]), 3
            ),
            "cleat_to_backer_bbox_z_separation_mm": round(
                shape.BoundingBox().zmin
                - assembled["center_backer"].BoundingBox().zmax,
                3,
            ),
            "positive_volume_clashes": clashes,
            "new_wood_wood_clashes_mm3": {
                pair: volume
                for pair, volume in clashes["wood_wood_mm3"].items()
                if pair not in center_clashes["wood_wood_mm3"]
            },
            "new_wood_panel_clashes_mm3": {
                pair: volume
                for pair, volume in clashes["wood_panel_mm3"].items()
                if pair not in center_clashes["wood_panel_mm3"]
            },
            "cleat_vs_full_length_nominal_head_proxy_screws_mm3": screw_hits,
        }
    return {
        "physical_width": "kerf-right",
        "raw_wood_and_panel_part_count": len(original),
        "fixed_axes_count": {"main": len(main), "kicker": len(kicker)},
        "center_post_shift_x_mm": 37.8,
        "center_backer_xyz_size_mm": [139.7, 88.9, 238.9],
        "baseline_positive_volume_clashes": baseline_clashes,
        "center_assembly_positive_volume_clashes": center_clashes,
        "new_center_wood_wood_clashes_mm3": {
            pair: volume
            for pair, volume in center_clashes["wood_wood_mm3"].items()
            if pair not in baseline_clashes["wood_wood_mm3"]
        },
        "new_center_wood_panel_clashes_mm3": {
            pair: volume
            for pair, volume in center_clashes["wood_panel_mm3"].items()
            if pair not in baseline_clashes["wood_panel_mm3"]
        },
        "center_face_contact_area_mm2": {
            name: round(area, 3) for name, area in center_contacts.items()
        },
        "full_purchased_kicker_receiver_paths": kicker,
        "main_receiver_paths_unchanged": main,
        "kicker_inner_edge_support": edge_support,
        "alternatives": alternatives,
        "screw_proxy_scope": "63.5-mm full-length cylinder at retailer nominal 9.017-mm head diameter; over-width shaft proxy, not controlled product dimensions or installed fit",
        "bolt_selection": None,
        "load_rating_adopted": False,
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
