"""Trace the former kicker-backer duty through integrated center posts.

This verifies fixed screw receipt and modeled post/header hardware presence,
not wood, fastener or whole-frame resistance.
"""

import csv
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
SIDES = ("left", "right")
TOL_MM = 1e-5


def _shop_rows():
    with AXES.open(newline="") as stream:
        return {
            row["name"]: row
            for row in csv.DictReader(stream)
            if row["name"].startswith("round_kicker_") and "_center_" in row["name"]
        }


def report(assembly):
    """Bind four unchanged purchased screw axes to two current post/header joints."""
    if assembly["post_placement"] != "integrated" or any(
        name.startswith("inner_kicker_backer_") for name in assembly["wood"]
    ):
        raise ValueError("Expected integrated center posts without separate backers")
    screws = {
        row.name: row
        for row in assembly["panel_connections"]
        if row.name.startswith("round_kicker_") and "_center_" in row.name
    }
    shop = _shop_rows()
    if len(screws) != 4 or set(screws) != set(shop):
        raise ValueError("The four fixed center kicker screws changed")
    seam = assembly["wood"]["kicker_left"].BoundingBox().xmax
    if abs(seam - assembly["wood"]["kicker_right"].BoundingBox().xmin) > TOL_MM:
        raise ValueError("The fixed kicker seam changed")

    posts = {}
    for side in SIDES:
        post_name = f"base_post_center_{side}"
        post = assembly["wood"][post_name]
        bounds = post.BoundingBox()
        if abs((bounds.xmax if side == "left" else bounds.xmin) - seam) > TOL_MM:
            raise ValueError(f"{post_name}: post no longer backs kicker seam")
        station = f"clip_split_header_center_{side}"
        bolts = sorted(
            name for name, owner in assembly["bolt_station"].items() if owner == station
        )
        if len(bolts) != 2 or any(
            name.removesuffix("_bolt") not in assembly["barrels"]
            or set(assembly["bolts"][name].members) != {"base_header", post_name}
            or abs(
                assembly["barrels"][name.removesuffix("_bolt")].intersect(post).Volume()
                - assembly["barrels"][name.removesuffix("_bolt")].Volume()
            )
            > 1e-4
            for name in bolts
        ):
            raise ValueError(
                f"{station}: transferred backing lacks its post/header pair"
            )
        rows = []
        for name in sorted(screws):
            if f"round_kicker_{side}_center_" not in name:
                continue
            connection, datum = screws[name], shop[name]
            start = connection.start.toTuple()
            direction = connection.direction.normalized().toTuple()
            if (
                connection.members[1] != post_name
                or any(
                    abs(start[index] - float(datum[f"start_{axis}_mm"])) > TOL_MM
                    or abs(direction[index] - float(datum[f"direction_{axis}"]))
                    > TOL_MM
                    for index, axis in enumerate("xyz")
                )
                or abs(connection.diameter - float(datum["modeled_diameter_mm"]))
                > TOL_MM
                or direction != (0.0, -1.0, 0.0)
            ):
                raise ValueError(f"{name}: fixed screw axis or receiver changed")
            purchased_length = float(datum["shop_purchased_length_mm"])
            tip_y = start[1] - purchased_length
            embed_length = bounds.ymax - tip_y
            if not tip_y < bounds.ymax < start[1] or embed_length <= 0:
                raise ValueError(f"{name}: purchased shaft misses integrated post")
            embedded = cq.Solid.makeCylinder(
                connection.diameter / 2,
                embed_length,
                cq.Vector(start[0], bounds.ymax, start[2]),
                cq.Vector(0, -1, 0),
            )
            full = abs(embedded.intersect(post).Volume() - embedded.Volume()) < 1e-4
            if not full:
                raise ValueError(f"{name}: purchased shaft exits receiver")
            rows.append(
                {
                    "name": name,
                    "purchased_length_mm": purchased_length,
                    "wood_embed_length_mm": round(embed_length, 4),
                    "axis_to_nearest_x_edge_mm": round(
                        min(start[0] - bounds.xmin, bounds.xmax - start[0]), 4
                    ),
                    "full_purchased_shaft_in_post": full,
                }
            )
        if len(rows) != 2:
            raise ValueError(f"{post_name}: expected two kicker screw receivers")
        posts[post_name] = {
            "kicker_screws": rows,
            "post_header_station": station,
            "post_header_bolts": bolts,
            "continuous_to_kicker_seam_in_model": True,
        }
    return {
        "schema": "owner_barrel_integrated_backing/v1",
        "status": "geometric_receiver_and_post_header_path_only",
        "separate_backer_count": 0,
        "fixed_center_kicker_screw_count": len(screws),
        "post_header_barrel_pair_count": sum(
            len(post["post_header_bolts"]) for post in posts.values()
        ),
        "posts": posts,
        "panel_screw_resistance_verified": False,
        "post_header_joint_resistance_verified": False,
        "complete_backing_load_path_verified": False,
        "drilling_released": False,
        "structural_released": False,
    }
