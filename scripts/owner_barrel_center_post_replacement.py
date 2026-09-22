"""Detached, source-bound 4x6 center-post replacement geometry; no release.

The two posts are the kicker screw receivers. This model does not modify the
viewer producers, choose cross-dowels, cut bores, or verify structural capacity.
"""

import csv
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import owner_layout_protected as protected
from scripts.export_owner_barrel_scene import build_viewer_assembly

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
SCHEMA = "owner_barrel_center_post_replacement/v1"
STOCK_OPTIONS_MM = (
    ("4x6_depth", 88.9, 139.7),
    ("4x6_face", 139.7, 88.9),
    ("4x4", 88.9, 88.9),
)
TOL_MM = 1e-5
SIDES = ("left", "right")
POSTS = tuple(f"base_post_center_{side}" for side in SIDES)
BACKERS = tuple(f"inner_kicker_backer_{side}" for side in SIDES)
RELEASE_FLAGS = {
    "drilling_released": False,
    "fabrication_released": False,
    "structural_released": False,
}


def _bounds(shape):
    b = shape.BoundingBox()
    return [round(v, 6) for v in (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)]


def _hits(shape, targets):
    box = shape.BoundingBox()
    return {
        name: round(volume, 6)
        for name, other in targets.items()
        if (volume := protected._volume(shape, other, box, other.BoundingBox()))
        > protected.HIT_TOL_MM3
    }


def _purchased_center_screws(source):
    model_rows = {
        row.name: row
        for row in source.panel_connections()
        if row.name.startswith("round_kicker_") and "_center_" in row.name
    }
    with AXES.open(newline="") as stream:
        csv_rows = {
            row["name"]: row
            for row in csv.DictReader(stream)
            if row["name"] in model_rows
        }
    if len(model_rows) != 4 or set(csv_rows) != set(model_rows):
        raise ValueError("Four fixed center-kicker screw sources changed")
    for name, row in model_rows.items():
        source_row = csv_rows[name]
        point = row.start.toTuple()
        direction = row.direction.normalized().toTuple()
        if (
            any(
                abs(point[i] - float(source_row[f"start_{axis}_mm"])) > TOL_MM
                or abs(direction[i] - float(source_row[f"direction_{axis}"])) > TOL_MM
                for i, axis in enumerate("xyz")
            )
            or abs(row.diameter - float(source_row["modeled_diameter_mm"])) > TOL_MM
        ):
            raise ValueError(f"{name}: model and shop source axes disagree")
    return model_rows, csv_rows


def _current_hardware(assembly):
    """Collect the 24 current station envelopes, excluding retired backer duties."""
    result = {}
    for name, shape in assembly["barrels"].items():
        result[f"barrel/{name}"] = shape
    for name, stack in assembly["stacks"].items():
        for role, shape in stack.items():
            result[f"stack/{name}/{role}"] = shape
    return result


def _build_trial(assembly, stock_name, face_mm, depth_mm):
    """Screen one ordinary stock orientation against the same fixed source."""
    source = variant(KERF_RIGHT)
    source_wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    assembly = build_viewer_assembly() if assembly is None else assembly
    current = assembly["wood"]
    if (
        not set(POSTS + BACKERS) <= set(current)
        or assembly.get("post_placement") != "outward"
        or len(assembly.get("barrels", {})) != 48
        or len(assembly.get("stacks", {})) != 48
    ):
        raise ValueError("Expected current outward-post, separate-backer viewer pose")
    seam_left = source_wood["kicker_left"].BoundingBox().xmax
    seam_right = source_wood["kicker_right"].BoundingBox().xmin
    if abs(seam_left - seam_right) > TOL_MM:
        raise ValueError("Kerf-right kicker seam is no longer closed")
    seam = (seam_left + seam_right) / 2
    header = source_wood["base_header"].BoundingBox()
    wood = {name: shape for name, shape in current.items() if name not in BACKERS}
    replacements = {}
    for side in SIDES:
        name = f"base_post_center_{side}"
        original = source_wood[name].BoundingBox()
        x0 = seam - face_mm if side == "left" else seam
        x1 = seam if side == "left" else seam + face_mm
        if (
            abs(original.ymin - header.ymin) > TOL_MM
            or abs(original.ymax - header.ymax) > TOL_MM
            or abs(original.ylen - 139.7) > TOL_MM
            or abs(original.zmax - header.zmin) > TOL_MM
            or abs(original.xlen - 38.1) > TOL_MM
        ):
            raise ValueError(f"{name}: source post/header stock geometry changed")
        replacement = cq.Solid.makeBox(
            x1 - x0,
            depth_mm,
            original.zlen,
            cq.Vector(x0, original.ymax - depth_mm, original.zmin),
        )
        wood[name] = replacements[name] = replacement

    model_screws, shop_screws = _purchased_center_screws(source)
    screw_report = {}
    expected_screw_hits = {}
    inner_edge_backed = {}
    for side in SIDES:
        name = f"base_post_center_{side}"
        edge_x = seam + (-0.5 if side == "left" else 0.5)
        inner_edge_backed[side] = all(
            replacements[name].isInside(cq.Vector(edge_x, header.ymax - 0.1, z), 1e-4)
            for z in (0.5, (header.zmin / 2), header.zmin - 0.5)
        )
    for name, row in model_screws.items():
        side = "left" if "_left_" in name else "right"
        if f"base_post_center_{side}" != row.members[1]:
            raise ValueError(f"{name}: source screw receiver changed")
        start = row.start.toTuple()
        purchased = float(shop_screws[name]["shop_purchased_length_mm"])
        front = replacements[f"base_post_center_{side}"].BoundingBox().ymax
        tip_y = start[1] - purchased
        if (
            row.direction.normalized().toTuple() != (0.0, -1.0, 0.0)
            or not tip_y < front < start[1]
        ):
            raise ValueError(f"{name}: purchased screw no longer enters post front")
        embedded = cq.Solid.makeCylinder(
            row.diameter / 2,
            front - tip_y,
            cq.Vector(start[0], front, start[2]),
            cq.Vector(0, -1, 0),
        )
        receiver = replacements[f"base_post_center_{side}"]
        full = abs(embedded.intersect(receiver).Volume() - embedded.Volume()) < 1e-4
        if not full or not inner_edge_backed[side]:
            raise ValueError(f"{name}: integrated post misses fixed kicker geometry")
        screw_report[name] = {
            "receiver": f"base_post_center_{side}",
            "axis_x_mm": start[0],
            "axis_z_mm": start[2],
            "purchased_length_mm": purchased,
            "wood_embed_length_mm": round(front - tip_y, 6),
            "full_embedded_shaft_received": full,
            "axis_to_nearest_x_edge_mm": round(
                min(
                    start[0] - receiver.BoundingBox().xmin,
                    receiver.BoundingBox().xmax - start[0],
                ),
                6,
            ),
        }
        expected_screw_hits[name] = side

    fixed = protected.inventory()
    if fixed["counts"]["panel_screws"] != 66 or fixed["counts"]["frame_bolts"] != 12:
        raise ValueError("Protected fixed screw or frame bolt inventory changed")
    all_protected = protected.hits(replacements, fixed)
    other_wood = {name: shape for name, shape in wood.items() if name not in POSTS}
    wood_hits = {name: _hits(shape, other_wood) for name, shape in replacements.items()}
    hardware = _current_hardware(assembly)
    hardware_hits = {
        name: _hits(shape, hardware) for name, shape in replacements.items()
    }
    unexpected_protected = {}
    for post_name, families in all_protected.items():
        side = post_name.removeprefix("base_post_center_")
        unexpected_protected[post_name] = {
            family: {
                name: volume
                for name, volume in hits.items()
                if family != "panel_screws" or expected_screw_hits.get(name) != side
            }
            for family, hits in families.items()
            if any(
                family != "panel_screws" or expected_screw_hits.get(name) != side
                for name in hits
            )
        }
    # Current barrel stations were built for narrower posts at X±180. Report
    # their physical intersection; any station reassignment needs a fresh bore
    # and load-path study in the parent integration.
    current_post_stations = {}
    for side in SIDES:
        station = f"clip_split_header_center_{side}"
        names = [
            name
            for name, owning in assembly["barrel_station"].items()
            if owning == station
        ]
        current_post_stations[station] = {
            name: round(
                protected._volume(
                    replacements[f"base_post_center_{side}"], assembly["barrels"][name]
                ),
                6,
            )
            for name in names
        }

    fixed_conflicts = any(unexpected_protected.values()) or any(wood_hits.values())
    current_hardware_conflicts = any(hardware_hits.values())
    report = {
        "schema": SCHEMA,
        "source": "kerf-right uncut wood, fixed connection axes and current barrel viewer",
        "stock_name": stock_name,
        "stock_actual_section_mm": [face_mm, depth_mm],
        "original_post_header_y_support_preserved": abs(depth_mm - 139.7) < TOL_MM,
        "kicker_seam_x_mm": round(seam, 6),
        "replacement_bounds_xyz_mm": {
            name: _bounds(shape) for name, shape in replacements.items()
        },
        "inner_edge_backed": inner_edge_backed,
        "center_kicker_screws": screw_report,
        "protected_inventory_counts": fixed["counts"],
        "screens": {
            "protected": all_protected,
            "other_wood": wood_hits,
            "current_barrel_hardware": hardware_hits,
        },
        "unexpected_protected_hits_mm3": unexpected_protected,
        "current_post_station_barrel_overlap_mm3": current_post_stations,
        "fixed_geometry_disposition": "CONFLICT" if fixed_conflicts else "CLEAR",
        "current_barrel_hardware_disposition": (
            "CONFLICT" if current_hardware_conflicts else "CLEAR_OCCUPANCY"
        ),
        "potential_route": (
            "Redesign the principal/header bolt entry so its head, washer and shaft "
            "do not enter either full-depth center post; a header-top entry into "
            "the principal is a candidate to screen. Relocate the current "
            "X±180 center-post barrel stations to the integrated posts and "
            "independently verify bores, tool access and the complete joint."
        ),
        "retained_barrel_station_fit_verified": False,
        "release_flags": dict(RELEASE_FLAGS),
        "limits": (
            "Finite nominal CAD occupancy only. T-nuts/electrical are display solids; "
            "hold-bolt projection is a 50.8 mm trial. Current barrel station "
            "locations, bore clearance, load path, capacities, tolerances and "
            "assembly sequence require separate integration."
        ),
    }
    return {"wood": wood, "report": report}


def build_model(*, assembly=None):
    """Prefer 4x6 when fixed geometry clears; report current hardware separately."""
    assembly = build_viewer_assembly() if assembly is None else assembly
    trials = {
        name: _build_trial(assembly, name, face, depth)
        for name, face, depth in STOCK_OPTIONS_MM
    }
    selected = next(
        (
            name
            for name, trial in trials.items()
            if trial["report"]["fixed_geometry_disposition"] == "CLEAR"
        ),
        STOCK_OPTIONS_MM[0][0],
    )
    result = trials[selected]
    result["report"]["stock_trials"] = {
        name: {
            "stock_actual_section_mm": trial["report"]["stock_actual_section_mm"],
            "original_post_header_y_support_preserved": trial["report"][
                "original_post_header_y_support_preserved"
            ],
            "fixed_geometry_disposition": trial["report"]["fixed_geometry_disposition"],
            "current_barrel_hardware_disposition": trial["report"][
                "current_barrel_hardware_disposition"
            ],
            "replacement_bounds_xyz_mm": trial["report"]["replacement_bounds_xyz_mm"],
            "unexpected_protected_hits_mm3": trial["report"][
                "unexpected_protected_hits_mm3"
            ],
            "other_wood_hits_mm3": trial["report"]["screens"]["other_wood"],
            "current_barrel_hardware_hits_mm3": trial["report"]["screens"][
                "current_barrel_hardware"
            ],
        }
        for name, trial in trials.items()
    }
    return result
