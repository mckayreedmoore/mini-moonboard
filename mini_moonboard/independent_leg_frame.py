"""Separate two-ply mechanical leg experiment; no glue or friction credit.

Stitches are internal connectors, not external restraints. Hardware is nominal
inspection geometry, not a selected product or a verified fastening schedule.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import footprint_frame as footprint
from . import hybrid
from . import joint_frame as baseline

KEY = "independent-leg-development"
PLY_THICKNESS = 19.05
STATIONS = (.2, .5, .8)
STITCH_LENGTH = 57.15


def stitch_point(q):
    bend = b.point(0, 1480, hybrid.leg_normal("2x8"))
    return bend + (footprint.foot_center(100) - bend) * q


@cache
def connections():
    result = []
    for connection in baseline.connections():
        members = tuple(ply for name in connection.members
                        for ply in ((name + "_inner", name + "_outer")
                                    if name in ("leg_left", "leg_right") else (name,)))
        result.append(replace(connection, members=members) if members != connection.members else connection)
    for side, sign in (("left", -1), ("right", 1)):
        for index, q in enumerate(STATIONS, 1):
            point = stitch_point(q)
            # Head-side washer starts 2 mm before the inner face. This generic
            # 2 mm washer / 9 mm nut stack leaves 6.05 mm nominal projection;
            # actual products, thread extent and resistance remain unresolved.
            start = cq.Vector(sign * (b.HALF + b.THICKNESS - 2), point.y, point.z)
            result.append(b.Connection(f"leg_stitch_{side}_{index}", start,
                cq.Vector(sign, 0, 0), STITCH_LENGTH, 9.525,
                (f"leg_{side}_inner", f"leg_{side}_outer"), "bolt", 2 * PLY_THICKNESS))
    return tuple(result)


@cache
def parts(drilled=True):
    result = []
    stitches = [c for c in connections() if c.name.startswith("leg_stitch_")]
    for part in baseline.parts(drilled):
        if part.name not in ("leg_left", "leg_right"):
            result.append(part)
            continue
        bounds = part.shape.BoundingBox()
        split = (bounds.xmin + bounds.xmax) / 2
        for layer, x0 in (("inner", bounds.xmin if part.name == "leg_right" else split),
                          ("outer", split if part.name == "leg_right" else bounds.xmin)):
            clip = cq.Solid.makeBox(PLY_THICKNESS, bounds.ylen + 2, bounds.zlen + 2,
                                    cq.Vector(x0, bounds.ymin - 1, bounds.zmin - 1))
            shape = part.shape.intersect(clip).clean()
            name = part.name + "_" + layer
            if drilled:
                for connection in stitches:
                    if name in connection.members:
                        shape = shape.cut(cq.Solid.makeCylinder(5, connection.length + 2,
                            connection.start - connection.direction, connection.direction)).clean()
            result.append(b.Part(name, shape, (*part.blank[:2], PLY_THICKNESS),
                "PROVISIONAL independent 19.05 mm plywood profile; no adhesive or interface-friction credit; "
                "continuous knee, own floor face, three internal stitch stations; "
                "panel axes follow lower centreline; material, hardware and resistance unresolved; "
                "bounding blank, STEP profile governs", 1))
    return tuple(result)
