"""Physical leg-side footprint variants of the shallow 2x8 candidate.

Only the lower leg profile changes. These nominal CAD variants do not establish
stability or connection capacity; the baseline remains available at zero offset.
"""
import math
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import hybrid
from . import shallow_frame as shallow

EXTENSIONS_MM = (0, 50, 100, 150, 200)


def _validate(extension_mm):
    if not math.isfinite(extension_mm) or not 0 <= extension_mm <= 200:
        raise ValueError("Leg foot-center extension must be finite and within 0–200 mm")


def foot_center(extension_mm):
    """Return the lower leg centerline's floor intersection, in world mm."""
    _validate(extension_mm)
    reference = b.point(0, 1480, b.LEG_NORMAL)
    return cq.Vector(0, reference.y + reference.z / math.tan(math.radians(70)) + extension_mm, 0)


def lower_angle(extension_mm):
    bend = b.point(0, 1480, hybrid.leg_normal('2x8'))
    return math.degrees(math.atan2(bend.z, foot_center(extension_mm).y - bend.y))


def _leg(sign, extension_mm):
    # Same union and floor clipping as b._leg; only the floor center moves.
    normal = hybrid.leg_normal('2x8')
    bend, upper = b.point(0, 1480, normal), b.point(0, 1880, normal)
    foot = foot_center(extension_mm)
    x = sign * (b.HALF + 1.5 * b.THICKNESS)

    def member(start, end):
        delta = end - start
        return (cq.Workplane('XY').box(b.THICKNESS, b.V1_SUPPORT_WIDTH_MM, delta.Length,
                                     centered=(True, True, False))
                .rotate((0, 0, 0), (1, 0, 0), -math.degrees(math.atan2(delta.y, delta.z)))
                .translate((x, start.y, start.z)).val())

    extended = foot + (foot - bend).normalized() * 120
    knee = cq.Solid.makeCylinder(b.V1_SUPPORT_WIDTH_MM / 2, b.THICKNESS,
                                cq.Vector(x - b.THICKNESS / 2, bend.y, bend.z), cq.Vector(1, 0, 0))
    shape = member(bend, upper).fuse(member(bend, extended), knee).clean()
    floor = cq.Workplane('XY').box(10000, 10000, 10000, centered=(True, True, False)).val()
    return shape.intersect(floor).clean()


def connections():
    return shallow.connections()


@cache
def parts(extension_mm, drilled=True):
    _validate(extension_mm)
    if extension_mm == 0:
        return shallow.parts(drilled)
    result = []
    for p in shallow.parts(drilled):
        if p.name.startswith('leg_'):
            shape = _leg(-1 if p.name == 'leg_left' else 1, extension_mm)
            bounds = shape.BoundingBox()
            blank = (bounds.zlen, bounds.ylen, b.THICKNESS)
            if drilled:
                for c in connections():
                    if p.name in c.members:
                        shape = shape.cut(cq.Solid.makeCylinder(5, c.length + 2,
                                                               c.start - c.direction, c.direction))
            p = replace(p, shape=shape, blank=blank,
                        description=f'Two glued 19.05 mm plywood layers; foot center +{extension_mm:g} mm leg-side; '
                                    '180 mm profile width; level floor cut; bounding blank, STEP profile governs')
        result.append(p)
    return tuple(result)
