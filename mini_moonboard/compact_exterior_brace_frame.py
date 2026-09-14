"""Exterior-only spliced knees for the current compact frame.

Each rim-end knee is one solid 4x6; each leg-end knee is one solid 2x6.
Their contacting splice plane lies at the outside face of the 4x6 leg. This
moves all knee wood outside the panel edge without spacers, air gaps or
built-up vertical members. Fresh native forces and actual joint checks are
required; the selected inboard-knee evidence does not qualify this candidate.
"""
import math
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import compact_base_finish as previous
from . import compact_knee_frame as knee_geometry

KEY = 'compact-exterior-brace-development'
RIM_KNEE_THICKNESS_MM = 88.9
LEG_KNEE_THICKNESS_MM = 38.1
SPLICE_PITCH_MM = 51.
LAP_START_MM = 120.
RIM_PIECE_END_SHORT_OF_LEG_MM = 180.
KNEE_NAMES = previous.KNEE_NAMES
NATIVE_SQUARE_END_MEMBERS = KNEE_NAMES
NATIVE_RECTANGULAR_KNEES = True
EXPECTED_BEARING_LENGTHS_MM = {}
MEMBER_AXES = dict(previous.MEMBER_AXES)
LIMITS = 'Exterior spliced-knee candidate; fresh connection and frame checks required'
parameters = dict(previous.parameters,
    knee_type='exterior solid 4x6 rim piece and solid 2x6 leg piece',
    knee_splice_plane_abs_x_mm=previous.b.HALF+RIM_KNEE_THICKNESS_MM,
    climbing_space_knee_intrusion_mm=0., knee_end_finish='square unnotched ends',
    knee_splice_pitch_mm=SPLICE_PITCH_MM, knee_lap_start_mm=LAP_START_MM,
    rim_knee_end_short_of_leg_mm=RIM_PIECE_END_SHORT_OF_LEG_MM)


def __getattr__(name):
    return getattr(previous, name)


def splice_stations():
    """Four evenly spaced bolts centered on the extended common overlap."""
    length = previous.knee_datums()[3]
    centre = (LAP_START_MM+length-RIM_PIECE_END_SHORT_OF_LEG_MM)/2
    return tuple(centre+multiple*SPLICE_PITCH_MM for multiple in (-1.5, -0.5, 0.5, 1.5))


def trim_planes():
    return {name: plane for name, plane in previous.trim_planes().items()
            if name.startswith('lumber_leg_')}


@cache
def raw_changed_parts():
    originals = {p.name: p for p in previous.uncut_wood_parts()}
    length = previous.knee_datums()[3]
    result = []
    for side, sign in (('left', -1), ('right', 1)):
        for end, slo, shi, lo, hi in (
            ('rim', -110., length-RIM_PIECE_END_SHORT_OF_LEG_MM, 0., RIM_KNEE_THICKNESS_MM),
            ('leg', LAP_START_MM, length+110., RIM_KNEE_THICKNESS_MM,
             RIM_KNEE_THICKNESS_MM+LEG_KNEE_THICKNESS_MM),
        ):
            name = f'base_knee_{side}_{end}'
            xlo, xhi = sorted((sign*lo, sign*hi))
            shape = knee_geometry._prism(side, xlo, xhi, slo, shi)
            result.append(replace(originals[name], shape=shape,
                blank=(shi-slo, 139.7, hi-lo), description=LIMITS))
    return tuple(result)


@cache
def uncut_wood_parts():
    changed = {p.name: p for p in raw_changed_parts()}
    return tuple(changed.get(p.name, p) for p in previous.uncut_wood_parts())


def additional_machining_cutters():
    return ()


@cache
def connections():
    result = []
    for c in previous.connections():
        if not c.name.startswith(('knee_bolt_', 'knee_splice_bolt_')):
            result.append(c)
            continue
        side = 'left' if '_left_' in c.name else 'right'
        sign = -1 if side == 'left' else 1
        direction = cq.Vector(sign, 0., 0.)
        point = c.start
        if c.name.startswith('knee_splice_bolt_'):
            rim, _, grain, _ = previous.knee_datums()
            station = splice_stations()[int(c.name.rsplit('_', 1)[1])-1]
            point = rim+grain*station
            members = (f'base_knee_{side}_rim', f'base_knee_{side}_leg')
            inner_x = previous.b.HALF
            grip, length = 127., 152.4
        elif '_rim_' in c.name:
            members = (f'base_side_{side}', f'base_knee_{side}_rim')
            inner_x = previous.b.HALF-88.9
            grip, length = 177.8, 203.2
        else:
            members = (f'lumber_leg_{side}', f'base_knee_{side}_leg')
            inner_x = previous.b.HALF
            grip, length = 127., 152.4
        start = cq.Vector(sign*(inner_x-2.032), point.y, point.z)
        result.append(replace(c, start=start, direction=direction, members=members,
            grip=grip, length=length, product_status=LIMITS))
    return tuple(result)


def bolt_dimensions(c):
    if not c.name.startswith(('knee_bolt_', 'knee_splice_bolt_')):
        return previous.bolt_dimensions(c)
    thread = 31.75 if c.length > 152.4 else 25.4
    return {'diameter_mm': c.diameter, 'length_mm': c.length, 'grip_mm': c.grip,
        'hole_diameter_mm': 11.1125, 'washer_od_mm': 25.4,
        'washer_thickness_mm': 2.032, 'nut_height_mm': 8.5598,
        'thread_length_mm': thread, 'thread_start_mm': c.length-thread,
        'provisional': True}


def bolt_interface_point(c):
    if c.name.startswith(('knee_bolt_', 'knee_splice_bolt_')):
        return c.start+c.direction*(2.032+88.9)
    return previous.bolt_interface_point(c)


@cache
def parts():
    changed_names = set(KNEE_NAMES) | set(previous.CHANGED_HOSTS)
    result = {p.name: p for p in previous.parts()}
    result.update({p.name: p for p in uncut_wood_parts() if p.name in changed_names})
    for name, _, cutter in previous.service_cutters():
        if name in changed_names:
            result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for c in connections():
        for index, name in enumerate(c.members):
            if name not in changed_names:
                continue
            diameter = bolt_dimensions(c)['hole_diameter_mm'] if c.kind == 'bolt' else c.diameter
            cutter = cq.Solid.makeCylinder(diameter/2, c.length+2., c.start-c.direction, c.direction)
            shape = result[name].shape.cut(cutter)
            if index == 0 and c.kind == 'screw':
                shape = shape.cut(c.components()[1])
            result[name] = replace(result[name], shape=shape.clean())
    return tuple(result.values())


def overlap_contact_datums():
    """Actual exterior lap faces; nine compression-only quadrature points."""
    rim, _, grain, length = previous.knee_datums()
    across = cq.Vector(0., grain.z, -grain.y)
    slo, shi, depth = LAP_START_MM, length-RIM_PIECE_END_SHORT_OF_LEG_MM, 139.7
    area = ((shi-slo)*depth-4*math.pi*(11.1125/2)**2)/9
    if area <= 0:
        raise ValueError('Splice requires positive net contact area')
    result = []
    for side, sign in (('left', -1), ('right', 1)):
        members = (f'base_knee_{side}_rim', f'base_knee_{side}_leg')
        for i in range(3):
            for j in range(3):
                station = slo+(i+0.5)*(shi-slo)/3
                q = -depth/2+(j+0.5)*depth/3
                p = rim+grain*station+across*q+cq.Vector(sign*(previous.b.HALF+88.9), 0., 0.)
                for c in connections():
                    if not any(member in c.members for member in members):
                        continue
                    d = c.direction.normalized()
                    delta = p-c.start
                    radius = bolt_dimensions(c)['hole_diameter_mm']/2 if c.kind == 'bolt' else c.diameter/2
                    if (delta-d*delta.dot(d)).Length <= radius:
                        raise ValueError('Contact sample lies inside a modeled bore')
                result.append({'name': f'knee_splice_contact_{side}_{i}_{j}',
                    'first': members[0], 'second': members[1],
                    'point_xyz_mm': p.toTuple(), 'normal_xyz': (sign, 0., 0.),
                    'tributary_area_mm2': area})
    return tuple(result)
