"""Two-bolt compact-frame trial preserving the preferred three-bolt candidate.

Exact screened 3/4-inch axes are modeled in fresh leg/rim stock. Two point
connections release a model rotation; this is not an installed hinge claim.
The fixed-wrench screen failed, so only a new assembled solve can evaluate
changed force distribution. Hardware dimensions remain provisional.
"""
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq

from . import compact_thick_frame as previous
from .bolted_frame import FrameBolt

KEY = 'compact-two-development'
BOLT_COUNT_PER_LEG = 2
BOLT_DIAMETER_MM = 19.05
BOLT_LENGTH_MM = 228.6
HOLE_DIAMETER = 20.6375
WASHER_OD_MM = 50.8
WASHER_THICKNESS_MM = 3.81
NUT_HEIGHT_MM = 16.891
HEAD_HEIGHT_MM = 12.268
HEX_CORNER_DIAMETER_MM = 32.995
CHANGED_NAMES = ('base_side_left', 'base_side_right', 'lumber_leg_left', 'lumber_leg_right')
SCREEN_SOURCE = 'fea/results/compact-thick-study/layout-screen.json'
POINTS_RELATIVE_DEPTH_CENTER_MM = ((0., -36.91356989014752, -5.8879853514857174),
                                  (0., 40.08643010985248, -5.8879853514857174))
LIMITS = ('Isolated two 3/4-inch bolts per 4x6 leg; compact 2x6 base retained; '
          'fresh receiver drilling, provisional complete hardware; not selected '
          'or construction qualified; no physical hinge or zero-friction claim')
b, base = previous.b, previous.base
hardware, timber, wide, leg_source = previous.hardware, previous.timber, previous.wide, previous.leg_source
axes = previous.axes
stations, service_cutters = previous.stations, previous.service_cutters
electrical_parts, attachment_datums = previous.electrical_parts, previous.attachment_datums
COMPONENT_LABELS = ('shaft_envelope', 'head_washer', 'nut_washer', 'head_envelope', 'nut_envelope')


def __getattr__(name):
    return getattr(previous, name)


def bolt_points():
    centre = previous.pivot_reference.bolt_points()[0]
    return tuple(centre+cq.Vector(*point) for point in POINTS_RELATIVE_DEPTH_CENTER_MM)


@cache
def raw_changed_parts():
    return tuple(replace(p, description=p.description+'; '+LIMITS)
                 for p in previous.uncut_wood_parts() if p.name in CHANGED_NAMES)


@dataclass(frozen=True)
class TwoLegBolt(FrameBolt):
    """Complete assumed 3/4-inch Grade 5 bolt, two washers, head and nut."""

    def components(self):
        d = self.direction.normalized()

        def washer(station):
            start = self.start+d*station
            return cq.Solid.makeCylinder(WASHER_OD_MM/2, WASHER_THICKNESS_MM, start, d).cut(
                cq.Solid.makeCylinder(HOLE_DIAMETER/2, WASHER_THICKNESS_MM, start, d))

        start = self.start+d*(self.grip+2*WASHER_THICKNESS_MM)
        nut = cq.Solid.makeCylinder(HEX_CORNER_DIAMETER_MM/2, NUT_HEIGHT_MM, start, d).cut(
            cq.Solid.makeCylinder(self.diameter/2, NUT_HEIGHT_MM, start, d))
        return (cq.Solid.makeCylinder(self.diameter/2, self.length, self.start, d),
                washer(0.), washer(WASHER_THICKNESS_MM+self.grip),
                cq.Solid.makeCylinder(HEX_CORNER_DIAMETER_MM/2, HEAD_HEIGHT_MM, self.start, -d), nut)


@cache
def connections():
    result = [c for c in previous.connections() if not c.name.startswith('lumber_leg_bolt_')]
    for side, sign in (('left', -1), ('right', 1)):
        for index, point in enumerate(bolt_points(), 1):
            result.append(TwoLegBolt(f'lumber_leg_bolt_{side}_{index}',
                cq.Vector(sign*(b.HALF+previous.THICKNESS+WASHER_THICKNESS_MM), point.y, point.z),
                cq.Vector(-sign, 0., 0.), BOLT_LENGTH_MM, BOLT_DIAMETER_MM,
                (f'lumber_leg_{side}', f'base_side_{side}'), 'bolt', 2*previous.THICKNESS,
                product_status=LIMITS))
    return tuple(result)


def bolt_interface_point(c):
    return c.start+c.direction*(WASHER_THICKNESS_MM+previous.THICKNESS)


def bolt_dimensions(c):
    return {'diameter_mm':c.diameter, 'length_mm':c.length, 'grip_mm':c.grip,
        'hole_diameter_mm':HOLE_DIAMETER, 'washer_od_mm':WASHER_OD_MM,
        'washer_thickness_mm':WASHER_THICKNESS_MM, 'nut_height_mm':NUT_HEIGHT_MM,
        'provisional':True}


def panel_connections():
    return tuple(c for c in connections() if c.members[0].startswith(('main_', 'kicker_')))


@cache
def uncut_wood_parts():
    changed = {p.name:p for p in raw_changed_parts()}
    return tuple(changed.get(p.name, p) for p in previous.uncut_wood_parts())


@cache
def parts():
    result = {p.name:p for p in previous.parts()}
    result.update({p.name:p for p in raw_changed_parts()})
    for name, _, cutter in service_cutters():
        if name in CHANGED_NAMES:
            result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for c in connections():
        for index, name in enumerate(c.members):
            if name not in CHANGED_NAMES:
                continue
            diameter = HOLE_DIAMETER if isinstance(c, TwoLegBolt) else 11.1125 if c.kind == 'bolt' else c.diameter
            cutter = cq.Solid.makeCylinder(diameter/2, c.length+2, c.start-c.direction, c.direction)
            shape = result[name].shape.cut(cutter)
            if index == 0 and c.kind == 'screw':
                shape = shape.cut(c.components()[1])
            result[name] = replace(result[name], shape=shape.clean())
    return tuple(result.values())
