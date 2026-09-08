"""Unselected ML23Z backing-end screw-axis trial; does not change current CAD."""
import json
import math
from pathlib import Path

import cadquery as cq

from . import base_frame as base
from . import box_frame as b
from .timber_connections import SDS, ConnectorScrew

REFERENCE = json.loads((Path(__file__).resolve().parents[1]/"docs/ml23z-reference.json").read_text())


def screws():
    for side, sign in (("left", 1), ("right", -1)):
        origin = b.point(-sign*base.INNER_EDGE, 44.45, 38.1)
        u, v = cq.Vector(sign, 0, 0), b.normal()
        w = u.cross(v)
        for flange, along, inward, offsets, member in (
            ("backing", u, v, REFERENCE["front_flange_offsets_mm"], "timber_bottom_backing"),
            ("rim", v, u, REFERENCE["opposite_flange_offsets_mm"], f"base_side_{side}"),
        ):
            for i, (station, offset) in enumerate(zip(REFERENCE["width_stations_mm"], offsets, strict=True), 1):
                yield ConnectorScrew(f"trial_end_{side}_{flange}_{i}",
                    origin+w*station+along*offset+inward*REFERENCE["thickness_mm"],
                    -inward, SDS["underhead_length"], 6.35,
                    (f"trial_ml23_{side}", member))


def brackets():
    """Nominal bent, chamfered and drilled solids; independent of current parts."""
    width, t, reach = (REFERENCE[k] for k in ("width_mm", "thickness_mm", "outside_reach_mm"))
    outer, inner = (REFERENCE[k] for k in ("outside_bend_radius_mm", "inside_bend_radius_mm"))
    chamfer = REFERENCE["outer_corner_chamfer_mm"]
    holes = tuple(screws())
    for side, sign in (("left", 1), ("right", -1)):
        name = f"trial_ml23_{side}"
        origin = b.point(-sign*base.INNER_EDGE, 44.45, 38.1)
        u, v = cq.Vector(sign, 0, 0), b.normal()
        w = u.cross(v)
        plane = cq.Plane(origin=origin-w*(width/2), xDir=u, normal=w)
        shape = (cq.Workplane(plane).moveTo(0, reach).lineTo(0, outer)
            .threePointArc((outer-outer/math.sqrt(2), outer-outer/math.sqrt(2)), (outer, 0))
            .lineTo(reach, 0).lineTo(reach, t).lineTo(outer, t)
            .threePointArc((outer-inner/math.sqrt(2), outer-inner/math.sqrt(2)), (t, outer))
            .lineTo(t, reach).close().extrude(width).val())
        for width_axis, normal in ((w, v), (-w, u)):
            cut_plane = cq.Plane(origin=origin-normal, xDir=width_axis, normal=normal)
            for edge in (-1, 1):
                cutter = (cq.Workplane(cut_plane)
                    .polyline([(edge*width/2, reach), (edge*(width/2-chamfer), reach),
                               (edge*width/2, reach-chamfer)])
                    .close().extrude(t+2).val())
                shape = shape.cut(cutter)
        for c in holes:
            if c.members[0] == name:
                shape = shape.cut(cq.Solid.makeCylinder(REFERENCE["hole_diameter_mm"]/2,
                    t+2, c.start-c.direction, c.direction))
        yield b.Part(name, shape.clean(), (width, reach, reach),
            "Unselected manufacturer-nominal ML23Z backing-end trial; no resistance qualification", 1)
