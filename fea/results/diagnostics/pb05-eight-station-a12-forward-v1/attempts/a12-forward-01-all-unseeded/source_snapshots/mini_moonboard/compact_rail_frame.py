"""Raised timber side-rail trial with physical bolted laps at both ends.

Outer posts move inward; kicker attachment holes are freshly relocated. The
rails pass through explicit open-edge kicker clearances with a 2 mm gap below
the header. New connection forces and loaded gap closure require assessment.
"""
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq

from . import compact_thick_frame as previous
from .bolted_frame import FrameBolt

KEY = 'compact-rail-development'
RAIL_THICKNESS_MM = 38.1
RAIL_DEPTH_MM = 139.7
RAIL_FRONT_Y = -210.0
RAIL_REAR_Y = 1510.0
RAIL_BOTTOM_Z = 97.2
RAIL_TOP_Z = RAIL_BOTTOM_Z+RAIL_DEPTH_MM
RAIL_CENTER_Z = (RAIL_BOTTOM_Z+RAIL_TOP_Z)/2
POST_SHIFT_MM = 38.1
KICKER_CLEARANCE_MM = 2.0
RAIL_BOLT_DIAMETER_MM = 9.525
RAIL_HOLE_DIAMETER_MM = 11.1125
RAIL_WASHER_OD_MM = 25.4
RAIL_WASHER_THICKNESS_MM = 2.032
RAIL_HEX_DIAMETER_MM = 16.4973
RAIL_HEAD_HEIGHT_MM = 6.1722
RAIL_NUT_HEIGHT_MM = 8.5598
CHANGED_NAMES = ('base_header', 'base_post_outer_left', 'base_post_outer_right',
                 'lumber_leg_left', 'lumber_leg_right', 'kicker_left', 'kicker_right',
                 'base_rail_tie_left', 'base_rail_tie_right')
MEMBER_AXES = {name:(cq.Vector(0, 1, 0), cq.Vector(1, 0, 0))
               for name in ('base_rail_tie_left', 'base_rail_tie_right')}
LIMITS = ('Isolated raised single-2x6 side-rail trial; moved posts and fresh kicker '
          'edge clearances/attachment holes; finite bolted laps and header contact '
          'require current assessment; not selected or construction qualified')
b, base = previous.b, previous.base
hardware, timber, wide, leg_source = previous.hardware, previous.timber, previous.wide, previous.leg_source
axes, bolt_points = previous.axes, previous.bolt_points
electrical_parts, service_cutters = previous.electrical_parts, previous.service_cutters


def __getattr__(name):
    return getattr(previous, name)


def front_points():
    centre = cq.Vector(0., (base.HEADER_FRONT_Y+previous.HEADER_BACK_Y)/2, RAIL_CENTER_Z)
    return tuple(centre+cq.Vector(0., y, z) for y in (-25., 25.) for z in (-25., 25.))


def rear_points():
    centre, _, grain, _, _ = axes()
    point = centre+grain*((RAIL_CENTER_Z-centre.z)/grain.z)
    return tuple(point+grain*s+cq.Vector(0., t, 0.) for s in (-21., 21.) for t in (-23., 23.))


def kicker_clearance_shape(side):
    width = RAIL_THICKNESS_MM+KICKER_CLEARANCE_MM
    x0 = -b.HALF-1. if side == 'left' else b.HALF-width
    return cq.Solid.makeBox(width+1., wide.PANEL+2., RAIL_DEPTH_MM+2*KICKER_CLEARANCE_MM,
        cq.Vector(x0, base.HEADER_FRONT_Y-1., RAIL_BOTTOM_Z-KICKER_CLEARANCE_MM))


@cache
def raw_changed_parts():
    old = {p.name:p for p in previous.uncut_wood_parts()}
    result = []
    for name in CHANGED_NAMES:
        side = 'left' if name.endswith('left') else 'right'
        sign = -1 if side == 'left' else 1
        if name.startswith('base_rail_tie_'):
            x0 = -b.HALF if side == 'left' else b.HALF-RAIL_THICKNESS_MM
            shape = cq.Solid.makeBox(RAIL_THICKNESS_MM, RAIL_REAR_Y-RAIL_FRONT_Y, RAIL_DEPTH_MM,
                cq.Vector(x0, RAIL_FRONT_Y, RAIL_BOTTOM_Z))
            result.append(b.Part(name, shape, (RAIL_REAR_Y-RAIL_FRONT_Y, RAIL_DEPTH_MM, RAIL_THICKNESS_MM), LIMITS, 1))
            continue
        part = old[name]
        if name.startswith('base_post_outer_'):
            part = replace(part, shape=part.shape.translate(cq.Vector(-sign*POST_SHIFT_MM, 0., 0.)))
        elif name.startswith('kicker_'):
            # The predecessor raw panel contains hold bores, but no panel screw
            # holes. Thus neither old outer screw axes nor closed plugs remain.
            part = replace(part, shape=part.shape.cut(kicker_clearance_shape(side)).clean())
        result.append(replace(part, description=part.description+'; '+LIMITS))
    return tuple(result)


@cache
def stations():
    result = []
    for name, origin, u, v, first, second in previous.stations():
        if name.startswith('clip_timber_header_outer_'):
            sign = -1 if name.endswith('left') else 1
            origin = origin+cq.Vector(-sign*POST_SHIFT_MM, 0., 0.)
        result.append((name, origin, u, v, first, second))
    return tuple(result)


@dataclass(frozen=True)
class RailBolt(FrameBolt):
    """Provisional complete 3/8-inch USS washer/head/nut envelopes."""

    def components(self):
        d = self.direction.normalized()

        def washer(station):
            start = self.start+d*station
            return cq.Solid.makeCylinder(RAIL_WASHER_OD_MM/2, RAIL_WASHER_THICKNESS_MM, start, d).cut(
                cq.Solid.makeCylinder(RAIL_HOLE_DIAMETER_MM/2, RAIL_WASHER_THICKNESS_MM, start, d))

        nut_start = self.start+d*(self.grip+2*RAIL_WASHER_THICKNESS_MM)
        nut = cq.Solid.makeCylinder(RAIL_HEX_DIAMETER_MM/2, RAIL_NUT_HEIGHT_MM, nut_start, d).cut(
            cq.Solid.makeCylinder(self.diameter/2, RAIL_NUT_HEIGHT_MM, nut_start, d))
        return (cq.Solid.makeCylinder(self.diameter/2, self.length, self.start, d),
                washer(0.), washer(RAIL_WASHER_THICKNESS_MM+self.grip),
                cq.Solid.makeCylinder(RAIL_HEX_DIAMETER_MM/2, RAIL_HEAD_HEIGHT_MM, self.start, -d), nut)


@cache
def connections():
    result = []
    for c in previous.connections():
        if c.name.startswith('clip_'):
            continue
        if c.members[0].startswith('kicker_') and c.members[1].startswith('base_post_outer_'):
            sign = -1 if c.members[0].endswith('left') else 1
            c = replace(c, start=c.start+cq.Vector(-sign*POST_SHIFT_MM, 0., 0.))
        result.append(c)
    result.extend(hardware.clip_connections(stations()))
    for side, sign in (('left', -1), ('right', 1)):
        for kind, points, first, second, first_thickness, length in (
            ('front', front_points(), f'base_rail_tie_{side}', f'base_post_outer_{side}', RAIL_THICKNESS_MM, 101.6),
            ('rear', rear_points(), f'lumber_leg_{side}', f'base_rail_tie_{side}', previous.THICKNESS, 152.4)):
            outer_x = b.HALF if kind == 'front' else b.HALF+previous.THICKNESS
            grip = 2*RAIL_THICKNESS_MM if kind == 'front' else previous.THICKNESS+RAIL_THICKNESS_MM
            for index, point in enumerate(points, 1):
                result.append(RailBolt(f'rail_{kind}_bolt_{side}_{index}',
                    cq.Vector(sign*(outer_x+RAIL_WASHER_THICKNESS_MM), point.y, point.z),
                    cq.Vector(-sign, 0., 0.), length, RAIL_BOLT_DIAMETER_MM,
                    (first, second), 'bolt', grip, product_status=LIMITS+'; provisional 3/8-inch stack'))
    return tuple(result)


def bolt_interface_point(c):
    if not isinstance(c, RailBolt):
        return previous.bolt_interface_point(c)
    first_thickness = previous.THICKNESS if c.members[0].startswith('lumber_leg_') else RAIL_THICKNESS_MM
    return c.start+c.direction*(RAIL_WASHER_THICKNESS_MM+first_thickness)


def bolt_dimensions(c):
    rail = isinstance(c, RailBolt)
    return {'diameter_mm':c.diameter, 'length_mm':c.length, 'grip_mm':c.grip,
        'hole_diameter_mm':RAIL_HOLE_DIAMETER_MM if rail else previous.HOLE_DIAMETER,
        'washer_od_mm':RAIL_WASHER_OD_MM if rail else previous.WASHER_OD_MM,
        'washer_thickness_mm':RAIL_WASHER_THICKNESS_MM if rail else previous.WASHER_THICKNESS_MM,
        'nut_height_mm':RAIL_NUT_HEIGHT_MM if rail else previous.NUT_HEIGHT_MM,
        'provisional':True}


def panel_connections():
    return tuple(c for c in connections() if c.members[0].startswith(('main_', 'kicker_')))


def attachment_datums():
    positions = {c.name:c.start.x for c in panel_connections()}
    return tuple({**row, 'x':positions[row['name']]} for row in previous.attachment_datums())


@cache
def uncut_wood_parts():
    changed = {p.name:p for p in raw_changed_parts()}
    result = [changed.pop(p.name, p) for p in previous.uncut_wood_parts()]
    return tuple(result)+tuple(changed.values())


@cache
def parts():
    result = {p.name:p for p in previous.parts()}
    result.update({p.name:p for p in raw_changed_parts()})
    result.update({p.name:p for p in hardware.clip_parts(stations())})
    for name, _, cutter in service_cutters():
        if name in CHANGED_NAMES:
            result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for c in connections():
        for index, name in enumerate(c.members):
            if name not in CHANGED_NAMES:
                continue
            part = result[name]
            if index == 0 and c.members[0].startswith('kicker_'):
                shaft, head = c.components()
                shape = part.shape.cut(shaft).cut(head)
            else:
                diameter = bolt_dimensions(c)['hole_diameter_mm'] if c.kind == 'bolt' else c.diameter
                cutter = cq.Solid.makeCylinder(diameter/2, c.length+2, c.start-c.direction, c.direction)
                shape = part.shape.cut(cutter)
                if index == 0 and c.kind == 'screw':
                    shape = shape.cut(c.components()[1])
            result[name] = replace(part, shape=shape.clean())
    return tuple(result.values())
