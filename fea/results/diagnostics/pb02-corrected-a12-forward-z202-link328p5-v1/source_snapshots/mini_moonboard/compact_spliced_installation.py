"""Outward-facing bolt installation for the frozen spliced-knee analysis model.

Wood, drilling axes and structural connection interfaces are unchanged. Keep
that analysis definition intact; this adapter records head/nut placement.
"""
from dataclasses import replace
from functools import cache

from . import compact_spliced_knee_frame as structural

KEY = structural.KEY
parameters = dict(structural.parameters, bolt_installation='heads inside; nuts and tips outside')


def __getattr__(name):
    return getattr(structural, name)


@cache
def connections():
    result = []
    for connection in structural.connections():
        if connection.kind == 'bolt' and connection.start.x*connection.direction.x < 0:
            washer = structural.bolt_dimensions(connection)['washer_thickness_mm']
            connection = replace(connection,
                start=connection.start+connection.direction*(connection.grip+2*washer),
                direction=-connection.direction,
                members=tuple(reversed(connection.members)))
        result.append(connection)
    return tuple(result)


def bolt_interface_point(connection):
    original = next(c for c in structural.connections() if c.name == connection.name)
    return structural.bolt_interface_point(original)
