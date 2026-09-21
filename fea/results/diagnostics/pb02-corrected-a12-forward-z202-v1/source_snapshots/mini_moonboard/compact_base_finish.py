"""Center the two outer base angles on the selected compact header.

Fresh stock is redrilled at the revised angle stations. The seven millimetre
inclined-member rear reserve is retained: a flush cut fails the current
quarter-depth end-cut geometry comparison, including its installation allowance.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import compact_spliced_kicker as previous

KEY = previous.KEY
MOVED_CLIPS = frozenset(('clip_angle_base_left', 'clip_angle_base_right'))
CHANGED_RECEIVERS = frozenset(('base_header', 'base_side_left', 'base_side_right'))
CLIP_CENTER_Y_MM = previous.HEADER_BACK_Y + previous.HEADER_DEPTH/2
parameters = dict(previous.parameters, outer_base_clip_center_y_mm=CLIP_CENTER_Y_MM,
                  rear_inclined_member_overhang_mm=previous.REAR_OVERHANG_MM)


def __getattr__(name):
    return getattr(previous, name)


@cache
def stations():
    return tuple((name, cq.Vector(origin.x, CLIP_CENTER_Y_MM, origin.z), u, v, first, second)
                 if name in MOVED_CLIPS else (name, origin, u, v, first, second)
                 for name, origin, u, v, first, second in previous.stations())


@cache
def connections():
    moved = {c.name: c for c in previous.hardware.clip_connections(
        tuple(s for s in stations() if s[0] in MOVED_CLIPS))}
    return tuple(moved.get(c.name, c) for c in previous.connections())


def outer_base_angles():
    return previous.hardware.clip_parts(tuple(s for s in stations() if s[0] in MOVED_CLIPS))


@cache
def revised_parts():
    result = {p.name: p for p in previous.uncut_wood_parts() if p.name in CHANGED_RECEIVERS}
    if result.keys() != CHANGED_RECEIVERS:
        raise ValueError('Require header and both outer rims')
    for name, _, cutter in previous.service_cutters():
        if name in result:
            result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for connection in connections():
        for index, name in enumerate(connection.members):
            if name not in result:
                continue
            diameter = (previous.bolt_dimensions(connection)['hole_diameter_mm']
                        if connection.kind == 'bolt' else connection.diameter)
            cutter = cq.Solid.makeCylinder(diameter/2, connection.length+2.,
                                           connection.start-connection.direction,
                                           connection.direction)
            part = result[name]
            shape = part.shape.cut(cutter)
            if index == 0 and connection.kind == 'screw':
                shape = shape.cut(connection.components()[1])
            result[name] = replace(part, shape=shape.clean())
    return tuple(result.values()) + outer_base_angles()


@cache
def parts():
    changed = {p.name: p for p in revised_parts()}
    return tuple(changed.get(p.name, p) for p in previous.parts())
