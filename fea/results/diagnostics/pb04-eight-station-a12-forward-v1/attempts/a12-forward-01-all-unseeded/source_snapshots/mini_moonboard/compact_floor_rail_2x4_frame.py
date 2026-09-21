"""Isolated 2x4 floor-rail trial with three front and two rear quarter-inch bolts.

The floor rails replace both diagonal knees. Outer posts move inward by one
rail thickness; fresh kicker edge clearances permit the rails to pass through.
This separate candidate requires its own frame and connection assessment.
"""
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq

from . import compact_base_finish as previous
from .bolted_frame import FrameBolt

KEY = 'compact-floor-rail-2x4-development'
RAIL_THICKNESS_MM = 38.1
RAIL_DEPTH_MM = 88.9
RAIL_FRONT_Y = -210.
RAIL_REAR_Y = 1670.
RAIL_BOTTOM_Z = 0.
RAIL_TOP_Z = RAIL_DEPTH_MM
POST_SHIFT_MM = RAIL_THICKNESS_MM
KICKER_CLEARANCE_MM = 2.
KNEE_NAMES = ()
NATIVE_RECTANGULAR_KNEES = False
RAIL_NAMES = tuple(f'base_floor_{side}' for side in ('left', 'right'))
NATIVE_SQUARE_END_MEMBERS = RAIL_NAMES
FLOOR_RAIL_NAMES = RAIL_NAMES
FLOOR_RAIL_GRID = (7, 2)
REMOVED_NAMES = previous.KNEE_NAMES
CHANGED_NAMES = (*RAIL_NAMES, 'base_post_outer_left', 'base_post_outer_right',
                 'lumber_leg_left', 'lumber_leg_right', 'base_side_left', 'base_side_right',
                 'kicker_left', 'kicker_right', 'base_header')
MEMBER_AXES = {name: axes for name, axes in previous.MEMBER_AXES.items()
               if name not in REMOVED_NAMES}
MEMBER_AXES.update({name: (cq.Vector(0., 1., 0.), cq.Vector(1., 0., 0.))
                    for name in RAIL_NAMES})
LIMITS = 'Isolated 2x4 floor-rail trial; quarter-inch hardware assumptions and current resistance require assessment'
parameters = dict(previous.parameters, knee_type='none; two continuous floor rails',
                  floor_rail_stock='2x4', floor_rail_bottom_mm=0.,
                  floor_rail_depth_mm=RAIL_DEPTH_MM, floor_rail_front_bolts_per_side=3, floor_rail_rear_bolts_per_side=2,
                  outer_post_inward_shift_mm=POST_SHIFT_MM)


QUARTER_WASHER_OD_MM = 19.0
QUARTER_WASHER_THICKNESS_MM = 1.6
QUARTER_HOLE_DIAMETER_MM = 7.9375
QUARTER_HEX_CORNER_DIAMETER_MM = 12.827
QUARTER_HEAD_HEIGHT_MM = 4.1402
QUARTER_NUT_HEIGHT_MM = 5.69


@dataclass(frozen=True)
class QuarterRailBolt(FrameBolt):
    """Complete provisional quarter-inch Grade 5 bolt and washer envelopes."""

    def components(self):
        direction = self.direction.normalized()

        def washer(station):
            start = self.start+direction*station
            return cq.Solid.makeCylinder(QUARTER_WASHER_OD_MM/2,
                QUARTER_WASHER_THICKNESS_MM, start, direction).cut(
                    cq.Solid.makeCylinder(QUARTER_HOLE_DIAMETER_MM/2,
                        QUARTER_WASHER_THICKNESS_MM, start, direction))

        nut_start = self.start+direction*(self.grip+2*QUARTER_WASHER_THICKNESS_MM)
        nut = cq.Solid.makeCylinder(QUARTER_HEX_CORNER_DIAMETER_MM/2,
            QUARTER_NUT_HEIGHT_MM, nut_start, direction).cut(
                cq.Solid.makeCylinder(self.diameter/2, QUARTER_NUT_HEIGHT_MM, nut_start, direction))
        return (cq.Solid.makeCylinder(self.diameter/2, self.length, self.start, direction),
                washer(0.), washer(QUARTER_WASHER_THICKNESS_MM+self.grip),
                cq.Solid.makeCylinder(QUARTER_HEX_CORNER_DIAMETER_MM/2,
                    QUARTER_HEAD_HEIGHT_MM, self.start, -direction), nut)


def __getattr__(name):
    return getattr(previous, name)


def front_points():
    return tuple(cq.Vector(0., y, 54.) for y in (-146., -110., -74.))


def rear_points():
    centre, _, grain, _, _ = previous.axes()
    centre = centre+grain*((54.-centre.z)/grain.z)
    return tuple(centre+cq.Vector(0., 20.*sign, 0.) for sign in (-1, 1))


def panel_edge_cutouts():
    width = RAIL_THICKNESS_MM+KICKER_CLEARANCE_MM
    half = previous.b.HALF
    return {'kicker_left': [(-half, -half+width, 0., RAIL_DEPTH_MM+KICKER_CLEARANCE_MM)],
            'kicker_right': [(half-width, half, 0., RAIL_DEPTH_MM+KICKER_CLEARANCE_MM)]}


def kicker_clearance_shape(side):
    width = RAIL_THICKNESS_MM+KICKER_CLEARANCE_MM
    x0 = -previous.b.HALF-1. if side == 'left' else previous.b.HALF-width
    return cq.Solid.makeBox(width+1., previous.wide.PANEL+2., RAIL_DEPTH_MM+KICKER_CLEARANCE_MM+1.,
        cq.Vector(x0, previous.base.HEADER_FRONT_Y-1., -1.))


@cache
def stations():
    result = []
    for name, origin, u, v, first, second in previous.stations():
        if name.startswith('clip_timber_header_outer_'):
            sign = -1 if name.endswith('left') else 1
            origin = origin+cq.Vector(-sign*POST_SHIFT_MM, 0., 0.)
        result.append((name, origin, u, v, first, second))
    return tuple(result)


@cache
def raw_changed_parts():
    raw = {p.name: p for p in previous.uncut_wood_parts()}
    result = []
    for name in CHANGED_NAMES:
        side = 'left' if name.endswith('left') else 'right'
        sign = -1 if side == 'left' else 1
        if name in RAIL_NAMES:
            x0 = -previous.b.HALF if sign < 0 else previous.b.HALF-RAIL_THICKNESS_MM
            shape = cq.Solid.makeBox(RAIL_THICKNESS_MM, RAIL_REAR_Y-RAIL_FRONT_Y, RAIL_DEPTH_MM,
                                    cq.Vector(x0, RAIL_FRONT_Y, 0.))
            result.append(previous.b.Part(name, shape,
                (RAIL_REAR_Y-RAIL_FRONT_Y, RAIL_DEPTH_MM, RAIL_THICKNESS_MM), LIMITS, 1))
            continue
        part = raw[name]
        if name.startswith('base_post_outer_'):
            part = replace(part, shape=part.shape.translate(cq.Vector(-sign*POST_SHIFT_MM, 0., 0.)))
        elif name.startswith('kicker_'):
            part = replace(part, shape=part.shape.cut(kicker_clearance_shape(side)).clean())
        result.append(replace(part, description=part.description+'; '+LIMITS))
    return tuple(result)


@cache
def uncut_wood_parts():
    changed = {p.name: p for p in raw_changed_parts()}
    result = [changed.pop(p.name, p) for p in previous.uncut_wood_parts() if p.name not in REMOVED_NAMES]
    return tuple(result)+tuple(changed.values())


@cache
def connections():
    result = []
    for c in previous.connections():
        if c.name.startswith(('knee_', 'clip_')):
            continue
        if c.members[0].startswith('kicker_') and c.members[1].startswith('base_post_outer_'):
            sign = -1 if c.members[0].endswith('left') else 1
            c = replace(c, start=c.start+cq.Vector(-sign*POST_SHIFT_MM, 0., 0.))
        result.append(c)
    result.extend(previous.hardware.clip_connections(stations()))
    washer = QUARTER_WASHER_THICKNESS_MM
    for side, sign in (('left', -1), ('right', 1)):
        for kind, points, first, second, first_thickness, length in (
            ('front', front_points(), f'base_post_outer_{side}', f'base_floor_{side}', 38.1, 101.6),
            ('rear', rear_points(), f'base_floor_{side}', f'lumber_leg_{side}', 38.1, 152.4)):
            inner_x = previous.b.HALF-(2*RAIL_THICKNESS_MM if kind == 'front' else RAIL_THICKNESS_MM)
            grip = 76.2 if kind == 'front' else 127.
            for index, point in enumerate(points, 1):
                result.append(QuarterRailBolt(f'rail_{kind}_bolt_{side}_{index}',
                    cq.Vector(sign*(inner_x-washer), point.y, point.z), cq.Vector(sign, 0., 0.),
                    length, 6.35, (first, second), 'bolt', grip, product_status=LIMITS))
    return tuple(result)


def bolt_dimensions(c):
    if not c.name.startswith('rail_'):
        return previous.bolt_dimensions(c)
    return {'diameter_mm': c.diameter, 'length_mm': c.length, 'grip_mm': c.grip,
            'hole_diameter_mm': QUARTER_HOLE_DIAMETER_MM, 'washer_od_mm': QUARTER_WASHER_OD_MM,
            'washer_thickness_mm': QUARTER_WASHER_THICKNESS_MM, 'nut_height_mm': QUARTER_NUT_HEIGHT_MM,
            'thread_length_mm': 25.4, 'thread_start_mm': c.length-25.4, 'provisional': True}


def bolt_interface_point(c):
    if c.name.startswith('rail_'):
        return c.start+c.direction*(38.1+QUARTER_WASHER_THICKNESS_MM)
    return previous.bolt_interface_point(c)


def panel_connections():
    return tuple(c for c in connections() if c.members[0].startswith(('main_', 'kicker_')))


def attachment_datums():
    positions = {c.name: c.start.x for c in panel_connections()}
    return tuple({**row, 'x': positions[row['name']]} for row in previous.attachment_datums())


def additional_machining_cutters():
    return ()


def overlap_contact_datums():
    return ()


@cache
def parts():
    result = {p.name: p for p in previous.parts() if p.name not in REMOVED_NAMES}
    result.update({p.name: p for p in raw_changed_parts()})
    result.update({p.name: p for p in previous.hardware.clip_parts(stations())})
    for name, _, cutter in previous.service_cutters():
        if name in CHANGED_NAMES:
            result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for c in connections():
        for index, name in enumerate(c.members):
            if name not in CHANGED_NAMES:
                continue
            diameter = bolt_dimensions(c)['hole_diameter_mm'] if c.kind == 'bolt' else c.diameter
            cutter = cq.Solid.makeCylinder(diameter/2, c.length+2., c.start-c.direction, c.direction)
            shape = result[name].shape.cut(cutter)
            if index == 0 and c.kind == 'screw':
                shape = shape.cut(c.components()[1])
            result[name] = replace(result[name], shape=shape.clean())
    return tuple(result.values())
