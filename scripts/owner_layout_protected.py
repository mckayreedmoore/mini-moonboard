"""Shared finite protected geometry for owner-review layout concepts.

The hold-bolt rear projection is a stated provisional screen, not a delivered
hardware limit. An empty collision result alone cannot release construction.
"""

from functools import lru_cache

import cadquery as cq

from mini_moonboard import hold_tnut_reinforcement as holds
from mini_moonboard.floor_flush_width import KERF_RIGHT, variant

HOLD_HOLE_DIAMETER_MM = 11.1125
TRIAL_HOLD_REAR_PROJECTION_MM = 50.8
HIT_TOL_MM3 = 1.0


def _axis(row):
    return cq.Solid.makeCylinder(
        row.diameter / 2,
        row.length,
        row.start,
        row.direction.normalized(),
    )


@lru_cache(maxsize=1)
def inventory():
    """Return actual maintained solids plus an explicit hold-projection trial."""
    model = variant(KERF_RIGHT)
    parts = model.parts()
    tnut_solids = {
        part.name: part.shape for part in parts if part.name.startswith("hold_tnut_")
    }
    electrical = model.electrical_parts()
    lights = {part.name: part.shape for part in electrical if part.kind == "light"}
    wires = {part.name: part.shape for part in electrical if part.kind == "wire"}
    datums = holds.datums(model)
    hold_paths = {}
    for datum in datums:
        rear = cq.Vector(*datum["rear_seating_xyz_mm"])
        into_panel = cq.Vector(*datum["barrel_into_panel_direction"])
        hold_paths[datum["name"]] = cq.Solid.makeCylinder(
            HOLD_HOLE_DIAMETER_MM / 2,
            TRIAL_HOLD_REAR_PROJECTION_MM,
            rear,
            -into_panel,
        )
    panel = {row.name: _axis(row) for row in model.panel_connections()}
    frame = {row.name: _axis(row) for row in model.connections() if row.kind == "bolt"}
    solids = {
        "tnuts": tnut_solids,
        "hold_hole_and_trial_projection": hold_paths,
        "lights": lights,
        "wires": wires,
        "panel_screws": panel,
        "frame_bolts": frame,
    }
    expected = {
        "tnuts": 142,
        "hold_hole_and_trial_projection": 142,
        "lights": 132,
        "wires": 131,
        "panel_screws": 66,
        "frame_bolts": 12,
    }
    counts = {name: len(rows) for name, rows in solids.items()}
    if counts != expected:
        raise ValueError(f"Protected kerf-right source inventory changed: {counts}")
    return {
        "schema": "owner_layout_protected/v1",
        "counts": counts,
        "solids": solids,
        "bounds": {
            family: {name: shape.BoundingBox() for name, shape in rows.items()}
            for family, rows in solids.items()
        },
        "hold_rear_projection_mm": TRIAL_HOLD_REAR_PROJECTION_MM,
        "delivered_hold_bolt_lengths_verified": False,
        "receiving_clearance_verified": False,
        "limitation": (
            "T-nut and electrical solids are maintained display geometries; "
            "50.8-mm hold-hole/rear-bolt projection is a provisional envelope, "
            "not a selected bolt length, wiring bend radius, or build clearance."
        ),
    }


def _volume(first, second, a=None, b=None):
    a = first.BoundingBox() if a is None else a
    b = second.BoundingBox() if b is None else b
    if (
        a.xmax < b.xmin
        or b.xmax < a.xmin
        or a.ymax < b.ymin
        or b.ymax < a.ymin
        or a.zmax < b.zmin
        or b.zmax < a.zmin
    ):
        return 0.0
    return first.intersect(second).Volume()


def hits(candidate_solids, protected=None):
    """Report 3D intersection volumes without granting clearance approval."""
    protected = inventory() if protected is None else protected
    candidate_bounds = {
        name: shape.BoundingBox() for name, shape in candidate_solids.items()
    }
    fixed_bounds = protected.get("bounds") or {
        family: {name: shape.BoundingBox() for name, shape in rows.items()}
        for family, rows in protected["solids"].items()
    }
    return {
        candidate: {
            family: collisions
            for family, members in protected["solids"].items()
            if (
                collisions := {
                    name: round(volume, 6)
                    for name, fixed in members.items()
                    if (
                        volume := _volume(
                            shape,
                            fixed,
                            candidate_bounds[candidate],
                            fixed_bounds[family][name],
                        )
                    ) > HIT_TOL_MM3
                }
            )
        }
        for candidate, shape in candidate_solids.items()
    }
