"""Detached kerf-right ±180 mm center-post layout; owner review, not a drill plan.

Only the two original 38.1 mm posts move. Two nominal 4x4 kicker backers
provide screw landings and continuous inner-edge backing; their frame attachment
and any bracket relocation or load path remain unresolved.
"""

import csv
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard import panel_grid_v2
from mini_moonboard.model import V1_SELECTED_TNUT_FLANGE_DIAMETER_MM

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
PROFILES = ROOT / "docs/floor-flush-construction-kerf-right/stock-profiles.json"
CANDIDATE_ID = "kerf-right-center-posts-x180-owner-review-layout"
POST_CENTER_X_MM = 180.0
BACKER_SECTION_MM = 88.9  # Nominal 4x4, two pieces meeting at the kerf-right seam.
BACKER_REAR_Y_MM = -124.9
BACKER_FRONT_Y_MM = -36.0
BACKER_TOP_Z_MM = 238.9  # Meet the header underside without overlapping its wood.
PANEL_BACK_Y_MM = -36.0
TOL = 1e-6
PROTECTED_3D_GATES = (
    "all_hold_tnuts_and_unused_hold_holes",
    "hold_bolt_protrusion",
    "led_bodies_and_wiring",
    "all_66_installed_panel_screws",
    "twelve_retained_frame_bolt_stacks",
)


def _bounds(profile):
    vertices = profile["vertices_world_mm"]
    return tuple(
        (min(v[i] for v in vertices), max(v[i] for v in vertices)) for i in range(3)
    )


def _box(bounds):
    (x0, x1), (y0, y1), (z0, z1) = bounds
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def _station(name):
    for suffix in ("_beam_", "_upright_"):
        if suffix in name:
            return name.rsplit(suffix, 1)[0]
    raise ValueError(f"Unrecognized bracket screw name: {name}")


def build_layout():
    """Check only nominal placement and purchased kicker-screw receiver geometry."""
    profiles = json.loads(PROFILES.read_text())
    with AXES.open(newline="") as file:
        axes = list(csv.DictReader(file))
    fixed = {
        row["name"]: row
        for row in axes
        if row["name"].startswith(("round_panel_", "round_kicker_", "kicker_header_"))
    }
    if len(fixed) != 66 or sum(n.startswith("round_panel_") for n in fixed) != 48:
        raise ValueError("Fixed 66-axis kerf-right inventory changed")
    fixed_axes = {
        name: (
            tuple(float(row[f"start_{axis}_mm"]) for axis in "xyz"),
            tuple(float(row[f"direction_{axis}"]) for axis in "xyz"),
            float(row["shop_purchased_length_mm"]),
        )
        for name, row in fixed.items()
    }
    receiver_map = {name: row["second_member"] for name, row in fixed.items()}
    screws = {
        name: row
        for name, row in fixed.items()
        if name.startswith("round_kicker_") and "_center_" in name
    }
    if len(screws) != 4 or {
        float(row["shop_purchased_length_mm"]) for row in screws.values()
    } != {63.5}:
        raise ValueError("Four purchased center-kicker screw lengths changed")

    seam_left = _bounds(profiles["kicker_left"])[0][1]
    seam_right = _bounds(profiles["kicker_right"])[0][0]
    if abs(seam_left - seam_right) > TOL:
        raise ValueError("Kerf-right kicker inner edges do not meet")
    header_bounds = _bounds(profiles["base_header"])
    if abs(header_bounds[2][0] - BACKER_TOP_Z_MM) > TOL:
        raise ValueError("Backer no longer meets header underside")
    backer_bounds = {
        "left": (
            (seam_left - BACKER_SECTION_MM, seam_left),
            (BACKER_REAR_Y_MM, BACKER_FRONT_Y_MM),
            (0.0, BACKER_TOP_Z_MM),
        ),
        "right": (
            (seam_right, seam_right + BACKER_SECTION_MM),
            (BACKER_REAR_Y_MM, BACKER_FRONT_Y_MM),
            (0.0, BACKER_TOP_Z_MM),
        ),
    }
    backers = {side: _box(bounds) for side, bounds in backer_bounds.items()}
    post_solids = {}
    post_shift = {}
    for side, sign in (("left", -1), ("right", 1)):
        original = _box(_bounds(profiles[f"base_post_center_{side}"]))
        center = (original.BoundingBox().xmin + original.BoundingBox().xmax) / 2
        shift = sign * POST_CENTER_X_MM - center
        if abs(shift) != 110.0 or abs(original.BoundingBox().xlen - 38.1) > TOL:
            raise ValueError("Expected original 38.1 mm posts at X ±70 mm")
        post_solids[side] = original.translate(cq.Vector(shift, 0, 0))
        post_shift[side] = shift

    radius = V1_SELECTED_TNUT_FLANGE_DIAMETER_MM / 2
    kickers = panel_grid_v2.kicker_foothold_datums()
    flange_bounds = {
        label: (
            kickers[str(index)][0] - panel_grid_v2.PANEL_HEIGHT_MM - radius,
            kickers[str(index)][0] - panel_grid_v2.PANEL_HEIGHT_MM + radius,
        )
        for label, index in (("KICK5", 5), ("KICK6", 6))
    }
    post_bounds = {
        side: (solid.BoundingBox().xmin, solid.BoundingBox().xmax)
        for side, solid in post_solids.items()
    }
    clearances = {
        "KICK5": flange_bounds["KICK5"][0] - post_bounds["left"][1],
        "KICK6": post_bounds["right"][0] - flange_bounds["KICK6"][1],
    }
    if min(clearances.values()) <= 0:
        raise ValueError("Shifted post intersects a kicker T-nut flange in X")
    overlap = sum(
        post.intersect(backer).Volume()
        for post in post_solids.values()
        for backer in backers.values()
    )
    if overlap > TOL:
        raise ValueError("Outward post intersects an inner-edge backer")

    received = {}
    for name, row in screws.items():
        side = "left" if "_left_" in name else "right"
        (x, y, z), direction, length = fixed_axes[name]
        if direction != (0.0, -1.0, 0.0) or y <= PANEL_BACK_Y_MM:
            raise ValueError(f"Changed kicker screw direction or start: {name}")
        tip_y = y - length
        embed = cq.Solid.makeCylinder(
            float(row["modeled_diameter_mm"]) / 2,
            PANEL_BACK_Y_MM - tip_y,
            cq.Vector(x, PANEL_BACK_Y_MM, z),
            cq.Vector(0, -1, 0),
        )
        receiver = backers[side]
        full = abs(embed.intersect(receiver).Volume() - embed.Volume()) < TOL
        received[name] = {
            "receiver": f"inner_kicker_backer_{side}",
            "purchased_length_mm": length,
            "embedded_wood_length_mm": PANEL_BACK_Y_MM - tip_y,
            "tip_to_backer_rear_mm": tip_y - BACKER_REAR_Y_MM,
            "full_shaft_received": full,
        }
        receiver_map[name] = f"inner_kicker_backer_{side}"
    if not all(row["full_shaft_received"] for row in received.values()):
        raise ValueError("A fixed purchased kicker screw is not fully received")

    header = _box(header_bounds)
    edges = {}
    for side in ("left", "right"):
        edge_x = seam_left + (-0.5 if side == "left" else 0.5)
        edges[side] = all(
            backers[side].isInside(cq.Vector(edge_x, -36.1, z), 1e-4)
            for z in (0.5, 112.5, 238.4)
        ) and header.isInside(cq.Vector(edge_x, -36.1, 250.0), 1e-4)
    if not all(edges.values()):
        raise ValueError("A kicker inner edge lacks full-height nominal backing")

    clip_rows = [row for row in axes if row["name"].startswith("clip_")]
    bracket_map = {}
    for row in clip_rows:
        bracket_map.setdefault(_station(row["name"]), []).append(
            (row["name"], row["first_member"], row["second_member"])
        )
    if len(bracket_map) != 24 or any(len(rows) != 6 for rows in bracket_map.values()):
        raise ValueError("Original 24-bracket/144-SDS duty inventory changed")
    # Preserve the historical duty identities, but explicitly expose the two
    # stations whose old screw axes no longer enter their moved post receiver.
    unresolved_stations = set()
    for row in clip_rows:
        receiver = row["second_member"]
        if receiver not in ("base_post_center_left", "base_post_center_right"):
            continue
        side = receiver.removeprefix("base_post_center_")
        start = cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz"))
        direction = cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz"))
        shaft = cq.Solid.makeCylinder(
            float(row["modeled_diameter_mm"]) / 2,
            float(row["modeled_length_mm"]),
            start,
            direction,
        )
        if shaft.intersect(post_solids[side]).Volume() < TOL:
            unresolved_stations.add(_station(row["name"]))
    frame_bolts = {row["name"] for row in axes if row["kind"] == "bolt"}
    if len(frame_bolts) != 12:
        raise ValueError("Original twelve frame-bolt axes changed")
    return {
        "candidate_id": CANDIDATE_ID,
        "disposition": "OWNER_REVIEW_LAYOUT_ONLY",
        "post_bounds_x_mm": {
            side: list(bounds) for side, bounds in post_bounds.items()
        },
        "post_shift_x_mm": post_shift,
        "flange_bounds_x_mm": {
            name: list(bounds) for name, bounds in flange_bounds.items()
        },
        "post_to_flange_x_clearance_mm": clearances,
        "backer_bounds_x_mm": {
            side: list(bounds[0]) for side, bounds in backer_bounds.items()
        },
        "post_backer_overlap_mm3": overlap,
        "inner_edge_backed": {f"kicker_{side}": value for side, value in edges.items()},
        "center_kicker_screws": received,
        "fixed_panel_axes": fixed_axes,
        "panel_receiver_map": receiver_map,
        "bracket_duty_map": {name: tuple(rows) for name, rows in bracket_map.items()},
        "bracket_station_names": set(bracket_map),
        "unresolved_bracket_stations": unresolved_stations,
        "frame_bolt_names": frame_bolts,
        "backer_frame_attachment_qualified": False,
        "protected_3d_gates": {
            name: {"status": "UNVERIFIED", "clearance_mm": None}
            for name in PROTECTED_3D_GATES
        },
        "limits": "Nominal layout only: two original header/post bracket stations miss moved posts; "
        "backer attachment, wood resistance, "
        "tolerances, load path and drilling all unresolved; historical analysis does not transfer.",
    }


if __name__ == "__main__":
    result = build_layout()
    print(
        json.dumps(
            {
                "candidate_id": result["candidate_id"],
                "disposition": result["disposition"],
                "post_bounds_x_mm": result["post_bounds_x_mm"],
                "post_to_flange_x_clearance_mm": result[
                    "post_to_flange_x_clearance_mm"
                ],
                "backer_bounds_x_mm": result["backer_bounds_x_mm"],
                "unresolved_bracket_stations": sorted(
                    result["unresolved_bracket_stations"]
                ),
                "protected_3d_gates": result["protected_3d_gates"],
            },
            indent=2,
            sort_keys=True,
        )
    )
