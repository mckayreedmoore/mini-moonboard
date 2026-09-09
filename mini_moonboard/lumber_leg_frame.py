"""Straight, grain-aligned leg comparison; new rim holes, not a retrofit.

Four-bolt groups are provisional geometry, not approved spacing/resistance.
The current wide candidate and its archived machining remain unchanged.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import footprint_frame as footprint
from . import wide_frame as parent
from .bolted_frame import WASHER, FrameBolt

WIDTHS = {"2x6": 139.7, "2x8": 184.15, "2x10": 234.95, "2x12": 285.75}
EXTENSIONS = (0., 150., 300.)
LIMITS = "Straight-leg comparison; new rim drilling, joint and stability checks required; NOT build-ready"


def geometry(size, extension=0.):
    if size not in WIDTHS or extension not in EXTENSIONS:
        raise ValueError("Select 2x6/8/10/12 and 0/150/300 mm extra footprint")
    # Centre the new group in the actual 184.15 mm deep rim (N=0..184.15).
    centre = b.point(0., 1680., 184.15/2)
    foot = footprint.foot_center(100.)+cq.Vector(0., extension, 0.)
    along = (centre-foot).normalized()
    across = cq.Vector(0., along.z, -along.y)
    return centre, foot, along, across


def bolt_points(size, extension=0.):
    centre, _, along, _ = geometry(size, extension)
    tangent = (b.point(0., 1., 0.)-b.point(0., 0., 0.)).normalized()
    # A parallelogram gives two grain-parallel rows in BOTH joined members.
    # A leg-local rectangle instead creates closely spaced skew rows in the rim.
    return tuple(centre+along*s+tangent*t for s in (-25., 25.) for t in (-25., 25.))


@cache
def connections(size, extension=0.):
    points = bolt_points(size, extension)
    result = [c for c in parent.connections()
              if not c.name.startswith(("analysis_leg_wall_bolt_", "leg_stitch_"))]
    for side, sign in (("left", -1), ("right", 1)):
        for index, point in enumerate(points, 1):
            result.append(FrameBolt(f"lumber_leg_bolt_{side}_{index}",
                cq.Vector(sign*(b.HALF-38.1-WASHER), point.y, point.z),
                cq.Vector(sign, 0., 0.), 95.25, 9.525,
                (f"base_side_{side}", f"lumber_leg_{side}"), "bolt", 76.2,
                product_status="Existing 3/8-16 x3.75in family; revised two-member joint unqualified"))
    return tuple(result)


def leg(size, extension, side):
    centre, foot, along, across = geometry(size, extension)
    width = WIDTHS[size]
    # Square top cut 120 mm past the bolt centroid; horizontal floor cut.
    top = centre+along*120.
    corners = []
    for offset in (-width/2, width/2):
        bottom = foot+across*offset
        bottom = bottom-along*(bottom.z/along.z)
        corners.append((bottom, top+across*offset))
    points = [corners[0][0], corners[1][0], corners[1][1], corners[0][1]]
    x0 = b.HALF if side == "right" else -b.HALF-38.1
    plane = cq.Plane(origin=(x0, 0., 0.), xDir=(0., 1., 0.), normal=(1., 0., 0.))
    shape = cq.Workplane(plane).polyline([(p.y, p.z) for p in points]).close().extrude(38.1).val()
    # Stock-axis bounding length includes the long point of the floor bevel.
    length = max(p.dot(along) for p in points)-min(p.dot(along) for p in points)
    return b.Part(f"lumber_leg_{side}", shape, (length, width, 38.1),
        f"Nominal {size} straight lumber; grain along length; square top and level foot cut; "+LIMITS, 1)


@cache
def parts(size, extension=0., drilled=True):
    geometry(size, extension)
    # Reuse all unchanged machining. Rebuild the rims from their pre-fastener
    # shapes so the obsolete leg holes are absent, rather than plugging them.
    result = {p.name: p for p in parent.parts(drilled) if not p.name.startswith("leg_")}
    raw = {p.name: p for p in parent.wood_parts(drilled)}
    for side in ("left", "right"):
        name = f"base_side_{side}"
        result[name] = raw[name]
        p = leg(size, extension, side)
        result[p.name] = p
    if drilled:
        for c in connections(size, extension):
            for name in c.members:
                if not name.startswith(("base_side_", "lumber_leg_")):
                    continue
                p = result[name]
                if isinstance(c, parent.PanelMachineScrew):
                    tolerance = parent.INSERT["drawing_general_tolerance_plus_minus"]
                    cutters = [cq.Solid.makeCylinder((parent.INSERT["nominal_outer_diameter"]+tolerance)/2,
                        parent.INSERT["nominal_length"]+tolerance, c.insert_start, c.direction),
                        cq.Solid.makeCylinder(parent.INSERT["pilot_diameter_inch_recommendation"]/2,
                            parent.ASSUMPTIONS["pilot_tip_clearance_depth"], c.insert_start, c.direction)]
                else:
                    diameter = 11.1125 if c.kind == "bolt" else c.diameter
                    cutters = [cq.Solid.makeCylinder(diameter/2, c.length+2,
                                                    c.start-c.direction, c.direction)]
                shape = p.shape
                for cutter in cutters:
                    shape = shape.cut(cutter)
                result[name] = replace(p, shape=shape.clean())
    return tuple(result.values())
