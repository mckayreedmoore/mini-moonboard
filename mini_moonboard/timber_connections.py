"""Nominal purchased connector geometry for the timber-base development.

Manufacturer drawing dimensions, not certified fit or resistance. No old clip
hole pattern, pilot instruction, or predecessor capacity is transferred.
"""
import json
import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

from . import base_frame as base
from . import bearing_frame as baseline
from . import box_frame as b
from .bolted_frame import WASHER, FrameBolt

REFERENCE = Path(__file__).resolve().parents[1]/"docs/ml24z-reference.json"
DATA = json.loads(REFERENCE.read_text())
ML = DATA["ml24z_nominal_mm"]
SDS = DATA["sds25112_nominal_mm"]
LIMITS = "Manufacturer nominal geometry; actual fit, installation and resistance unqualified; NOT build-ready"


def stations(include_header=False):
    """Twelve upper-frame clips, optionally four header-to-post retention clips.

No angle is forced into the non-right-angle sloped-member/header joint.
The lower face backing and sloped-base retention need separate connections.
"""
    tangent = (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized()
    spans = (("left", -base.INNER_EDGE, -76.2),
             ("right", 38.1, base.INNER_EDGE))
    levels = (("top", b.LENGTH-38.1, -tangent),
              ("mid_lower", b.HALF-38.1, -tangent),
              ("mid_upper", b.HALF+38.1, tangent))
    for level, station, v in levels:
        for side, x0, x1 in spans:
            endpoints = ((x0, 1., f"base_side_{side}"),
                         (x1, -1., f"base_principal_{side}")) if side == "left" else (
                         (x0, 1., f"base_principal_{side}"),
                         (x1, -1., f"base_side_{side}"))
            beam = "base_rail_top" if level == "top" else f"base_rail_{level}_{side}"
            for index, (x, sign, upright) in enumerate(endpoints, 1):
                yield (f"clip_timber_{level}_{side}_{index}", b.point(x, station, 88.9),
                       cq.Vector(sign, 0., 0.), v, beam, upright)
    if not include_header:
        return
    y = base.HEADER_FRONT_Y-base.HEADER_DEPTH/2
    for name, x, sign in (("outer_left", -base.INNER_EDGE, 1.),
                          ("center_left", -76.2, -1.),
                          ("center_right", 38.1, 1.),
                          ("outer_right", base.INNER_EDGE, -1.)):
        yield (f"clip_timber_header_{name}", cq.Vector(x, y, base.HEADER_BOTTOM),
               cq.Vector(sign, 0., 0.), cq.Vector(0., 0., -1.),
               "base_header", f"base_post_{name}")


@dataclass(frozen=True)
class ConnectorScrew(b.Connection):
    product_status: str = (
        "Simpson SDS25112, separately purchased; manufacturer nominal underhead/head geometry; "
        "simplified unthreaded shaft; no pilot instruction or capacity assignment"
    )

    def components(self):
        return (cq.Solid.makeCylinder(self.diameter/2, self.length, self.start, self.direction),
                cq.Solid.makeCylinder(SDS["maximum_head_diameter"]/2,
                                      SDS["head_height"], self.start, -self.direction))


def connector(origin, u, v):
    """ML24Z in the open positive-u/v quadrant of two wood-contact planes.

The first flange lies along u and connects the beam; the second lies along v
and connects the upright. Width follows u cross v. Only rigid placement is used.
"""
    if not math.isclose(u.Length, 1., abs_tol=1e-8) or not math.isclose(v.Length, 1., abs_tol=1e-8) or abs(u.dot(v)) > 1e-8:
        raise ValueError("Connector axes must be orthonormal")
    w = u.cross(v)
    width, t, reach = ML["width"], ML["thickness"], ML["outside_flange_reach"]
    outer, inner = ML["outside_bend_radius"], ML["inside_bend_radius"]
    plane = cq.Plane(origin=origin-w*(width/2), xDir=u, normal=w)
    shape = (cq.Workplane(plane).moveTo(0., reach).lineTo(0., outer)
        .threePointArc((outer-outer/math.sqrt(2), outer-outer/math.sqrt(2)), (outer, 0.))
        .lineTo(reach, 0.).lineTo(reach, t).lineTo(outer, t)
        .threePointArc((outer-inner/math.sqrt(2), outer-inner/math.sqrt(2)), (t, outer))
        .lineTo(t, reach).close().extrude(width).val())
    holes = []
    for index, (station, offset) in enumerate(zip(ML["width_stations"], ML["front_flange_offsets"], strict=True), 1):
        holes.append((f"beam_{index}", origin+w*station+u*offset+v*t, -v))
    for index, (station, offset) in enumerate(zip(ML["width_stations"], ML["opposite_flange_offsets"], strict=True), 1):
        holes.append((f"upright_{index}", origin+w*station+v*offset+u*t, -u))
    for _, start, direction in holes:
        shape = shape.cut(cq.Solid.makeCylinder(ML["hole_diameter"]/2, t+2.,
                                               start-direction, direction))
    return shape.clean(), holes


def clip_parts(stations):
    """Stations: (name, origin, u, v, beam name, upright name)."""
    return tuple(b.Part(name, connector(origin, u, v)[0],
        (ML["width"], ML["outside_flange_reach"], ML["outside_flange_reach"]),
        "Purchased ML24Z; six separately purchased SDS25112 screws; "+LIMITS, 1)
        for name, origin, u, v, _, _ in stations)


def clip_connections(stations):
    result = []
    for name, origin, u, v, beam, upright in stations:
        _, holes = connector(origin, u, v)
        for suffix, start, direction in holes:
            result.append(ConnectorScrew(f"{name}_{suffix}", start, direction,
                SDS["underhead_length"], 6.35,
                (name, beam if suffix.startswith("beam_") else upright)))
    return tuple(result)


def leg_connections():
    """Preserve the established axes, but resize grips after removing infills.

Four removable 3/8-inch bolts per leg and three ply stitches per leg. Lengths
are provisional Conquest-family nominal choices, not approved joint schedules.
"""
    result = []
    for old in baseline.connections():
        if not old.name.startswith(("analysis_leg_wall_bolt_", "leg_stitch_")):
            continue
        side = "left" if "_left_" in old.name else "right"
        sign = -1 if side == "left" else 1
        wall = old.name.startswith("analysis_leg_wall_bolt_")
        # Under-head origin is one maximum washer thickness inside the receiver.
        start = cq.Vector(sign*((b.HALF-38.1 if wall else b.HALF)-WASHER),
                          old.start.y, old.start.z)
        members = ((f"base_side_{side}", f"leg_{side}_inner", f"leg_{side}_outer")
                   if wall else (f"leg_{side}_inner", f"leg_{side}_outer"))
        result.append(FrameBolt(old.name, start, cq.Vector(sign, 0., 0.),
            95.25 if wall else 63.5, 9.525, members, "bolt", 76.2 if wall else 38.1,
            product_status=("Selected Conquest HBA-38X334 3/8-16 x3.75in" if wall else
                            "Provisional Conquest-family 3/8-16 x2.5in")+
            " with selected maximum nut/washer envelopes; grip and strength require validation"))
    if len(result) != 14:
        raise ValueError("Expected eight leg-wall bolts and six ply stitches")
    return tuple(result)
