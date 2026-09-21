"""Isolated nine-bolt candidate with a real, centered finite sole land.

Five-millimeter timber relief leaves a 75 mm long floor-bearing land. This is a
fresh-stock development detail, not an installed hinge or construction release.
The gross-beam response idealization does not resolve the short relieved neck;
local bearing/shear and loaded clearance of the relieved ends need checks.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import leg_mvp_frame as previous

KEY = 'leg-mvp-sole-development'
FOOT_LAND_LENGTH_MM = 75.0
FOOT_RELIEF_MM = 5.0
FOOT_RELIEF_TOLERANCE_MM = 1.0
FOOT_CENTER_Y_MM = 1418.009
LIMITS = ('Exploratory centered 75 mm timber sole land with 5 mm end relief; '
          'single 2x10 upper leg/rim stock and nine 1/2-inch bolts per leg; '
          'local neck, bearing and loaded relief clearance unqualified; not selected or build-ready')
LEG_NAMES = frozenset(('lumber_leg_left', 'lumber_leg_right'))


def __getattr__(name):
    """Share unchanged candidate APIs without changing the full-sole baseline."""
    return getattr(previous, name)


def relieve_sole(shape):
    """Physically remove both sole ends, retaining the centered bearing land."""
    bounds = shape.BoundingBox()
    low = FOOT_CENTER_Y_MM-FOOT_LAND_LENGTH_MM/2
    high = FOOT_CENTER_Y_MM+FOOT_LAND_LENGTH_MM/2
    if not bounds.ymin < low < high < bounds.ymax or abs(bounds.zmin) > 1e-6:
        raise ValueError('Require floor-bearing stock containing the requested sole land')
    for y0, y1 in ((bounds.ymin-1., low), (high, bounds.ymax+1.)):
        cutter = cq.Solid.makeBox(bounds.xlen+2., y1-y0, FOOT_RELIEF_MM+1.,
                                 cq.Vector(bounds.xmin-1., y0, -1.))
        shape = shape.cut(cutter)
    return shape.clean()


def _revised(part):
    if part.name not in LEG_NAMES:
        return part
    return replace(part, shape=relieve_sole(part.shape),
                   description=part.description+'; '+LIMITS)


@cache
def raw_changed_parts():
    return tuple(_revised(part) for part in previous.raw_changed_parts())


@cache
def uncut_wood_parts():
    return tuple(_revised(part) for part in previous.uncut_wood_parts())


@cache
def parts():
    return tuple(_revised(part) for part in previous.parts())


def geometry_review():
    """Do not silently reuse the full-sole candidate's geometry review."""
    raise NotImplementedError(
        "Full-sole geometry review does not evaluate this relieved sole. "
        "Use original_foot_bounds() for separate contact geometry checks; "
        "local neck resistance and loaded relief clearance remain unresolved.")


def original_foot_bounds():
    """Record full-sole and relieved-sole contact polygons in world coordinates."""
    result = {}
    for part in previous.raw_changed_parts():
        if part.name not in LEG_NAMES:
            continue
        points = [v.Center() for v in part.shape.Vertices() if abs(v.Z) < 1e-6]
        if len(points) != 4:
            raise ValueError('Require four original planar foot corners')
        revised = relieve_sole(part.shape)
        land = [v.Center() for v in revised.Vertices() if abs(v.Z) < 1e-6]
        if len(land) != 4:
            raise ValueError('Require four finite sole-land corners')
        result[part.name] = {'original_xyz_mm':[p.toTuple() for p in points],
            'original_y_bounds_mm':[min(p.y for p in points), max(p.y for p in points)],
            'land_xyz_mm':[p.toTuple() for p in land],
            'land_y_bounds_mm':[FOOT_CENTER_Y_MM-FOOT_LAND_LENGTH_MM/2,
                                FOOT_CENTER_Y_MM+FOOT_LAND_LENGTH_MM/2],
            'land_nominal_area_mm2':FOOT_LAND_LENGTH_MM*previous.THICKNESS,
            'relief_mm':FOOT_RELIEF_MM, 'relief_tolerance_mm':FOOT_RELIEF_TOLERANCE_MM,
            'gross_neck_stiffness_is_approximate':True}
    return result
