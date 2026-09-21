"""Isolated 100x50 bolt-group / 150mm top experiment; NOT qualified geometry.

New-build rim drilling, not plugged old bores or an approved retrofit.
No native response, resistance, exports or viewer are supplied by this module.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import lumber_leg_frame as original

WIDTHS = original.WIDTHS
EXTENSIONS = original.EXTENSIONS
geometry = original.geometry
ALONG_LEG_PITCH = 100.
ALONG_RIM_PITCH = 50.
TOP_EXTENSION = 150.
LIMITS = "Spread-group experiment; geometry only, NOT build-ready or strength-qualified"


def bolt_points(size, extension=0.):
    centre, _, along, _ = geometry(size, extension)
    tangent = (original.b.point(0., 1., 0.)-original.b.point(0., 0., 0.)).normalized()
    return tuple(centre+along*s+tangent*t for s in (-ALONG_LEG_PITCH/2, ALONG_LEG_PITCH/2)
                 for t in (-ALONG_RIM_PITCH/2, ALONG_RIM_PITCH/2))


@cache
def connections(size, extension=0.):
    points = bolt_points(size, extension)
    result = []
    for connection in original.connections(size, extension):
        if connection.name.startswith("lumber_leg_bolt_"):
            point = points[int(connection.name.rsplit("_", 1)[1])-1]
            connection = replace(connection,
                start=cq.Vector(connection.start.x, point.y, point.z),
                product_status=LIMITS+"; existing 3/8-16 x3.75in dimensional family")
        result.append(connection)
    return tuple(result)


def leg(size, extension, side):
    centre, foot, along, across = geometry(size, extension)
    if side not in ("left", "right"):
        raise ValueError("Select left or right leg")
    top = centre+along*TOP_EXTENSION
    corners = []
    for offset in (-WIDTHS[size]/2, WIDTHS[size]/2):
        bottom = foot+across*offset
        bottom = bottom-along*(bottom.z/along.z)
        corners.append((bottom, top+across*offset))
    points = [corners[0][0], corners[1][0], corners[1][1], corners[0][1]]
    x0 = original.b.HALF if side == "right" else -original.b.HALF-38.1
    plane = cq.Plane(origin=(x0, 0., 0.), xDir=(0., 1., 0.), normal=(1., 0., 0.))
    shape = cq.Workplane(plane).polyline([(p.y, p.z) for p in points]).close().extrude(38.1).val()
    length = max(p.dot(along) for p in points)-min(p.dot(along) for p in points)
    return original.b.Part(f"lumber_leg_{side}", shape, (length, WIDTHS[size], 38.1),
        f"Nominal {size}; grain along length; square top150mm past bolt centroid; level foot; "+LIMITS, 1)


@cache
def parts(size, extension=0., drilled=True):
    geometry(size, extension)
    # Keep unrelated machining verbatim. Obtain rims BEFORE any connection
    # machining, then apply only this experiment's actual connection list.
    result = {p.name: p for p in original.parent.parts(drilled) if not p.name.startswith("leg_")}
    raw = {p.name: p for p in original.parent.wood_parts(drilled)}
    for side in ("left", "right"):
        name = f"base_side_{side}"
        result[name] = raw[name]
        part = leg(size, extension, side)
        result[part.name] = part
    if drilled:
        for connection in connections(size, extension):
            for name in connection.members:
                if not name.startswith(("base_side_", "lumber_leg_")):
                    continue
                if isinstance(connection, original.parent.PanelMachineScrew):
                    tolerance = original.parent.INSERT["drawing_general_tolerance_plus_minus"]
                    cutters = [cq.Solid.makeCylinder(
                        (original.parent.INSERT["nominal_outer_diameter"]+tolerance)/2,
                        original.parent.INSERT["nominal_length"]+tolerance,
                        connection.insert_start, connection.direction),
                        cq.Solid.makeCylinder(original.parent.INSERT["pilot_diameter_inch_recommendation"]/2,
                            original.parent.ASSUMPTIONS["pilot_tip_clearance_depth"],
                            connection.insert_start, connection.direction)]
                else:
                    diameter = 11.1125 if connection.kind == "bolt" else connection.diameter
                    cutters = [cq.Solid.makeCylinder(diameter/2, connection.length+2,
                        connection.start-connection.direction, connection.direction)]
                part = result[name]
                shape = part.shape
                for cutter in cutters:
                    shape = shape.cut(cutter)
                result[name] = replace(part, shape=shape.clean())
    return tuple(result.values())
