"""Four-bolt staggered 2x12 leg trial preserving the original row trial.

The revised centers satisfy the retained 127 mm cross-grain spread screen.
Fresh raw receivers remove the former row holes; no force result transfers.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import compact_2x12_leg_frame as previous

KEY = 'compact-2x12-staggered-development'
RIM_LOCAL_OFFSETS_SQ_MM = ((-81., 13.), (-27., 3.), (27., -3.), (81., -13.))
LIMITS = 'Unbraced staggered 2x12 leg trial; four half-inch bolts per leg; not the selected build package'
parameters = {**previous.parameters, 'bolt_pitch_mm': None,
              'rim_local_bolt_offsets_sq_mm': RIM_LOCAL_OFFSETS_SQ_MM}


def __getattr__(name):
    return getattr(previous, name)


def bolt_points():
    centre, _, _, _, rim = previous.axes()
    normal = cq.Vector(0., rim.z, -rim.y)
    return tuple(centre + rim * s + normal * q for s, q in RIM_LOCAL_OFFSETS_SQ_MM)


@cache
def connections():
    points = bolt_points()
    result = []
    for connection in previous.connections():
        if connection.kind == 'bolt':
            point = points[int(connection.name.rsplit('_', 1)[1]) - 1]
            connection = replace(connection, start=cq.Vector(connection.start.x, point.y, point.z),
                                 product_status=LIMITS)
        result.append(connection)
    return tuple(result)


@cache
def parts():
    result = {part.name: part for part in previous.parts()}
    result.update({part.name: part for part in previous.raw_changed_parts()})
    for name, _, cutter in previous.service_cutters():
        if name in previous.CHANGED:
            result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for connection in connections():
        for index, name in enumerate(connection.members):
            if name not in previous.CHANGED:
                continue
            diameter = (previous.bolt_dimensions(connection)['hole_diameter_mm']
                        if connection.kind == 'bolt' else connection.diameter)
            cutter = cq.Solid.makeCylinder(diameter / 2, connection.length + 2,
                                          connection.start - connection.direction, connection.direction)
            shape = result[name].shape.cut(cutter)
            if index == 0 and connection.kind == 'screw':
                shape = shape.cut(connection.components()[1])
            result[name] = replace(result[name], shape=shape.clean(), description=LIMITS)
    return tuple(result.values())
