"""Screw-first compact candidate; larger stock retained where direct swaps fail."""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import lumber_leg_spread_frame as compact
from . import wide_frame as wide
from .bolted_frame import WASHER

KEY = 'screw-first-compact-development'
LIMITS = 'Development only; screw resistance, joints and unanchored stability unqualified'


@cache
def connections():
    """Existing wood-screw family at current panel/kicker coordinates, no inserts."""
    return tuple(wide.timber.PanelScrew(c.name, c.start, c.direction, 50.8, 4.1402, c.members)
                 if isinstance(c, wide.PanelMachineScrew) else c
                 for c in compact.connections('2x6', 0.))


@cache
def wood_parts():
    parts = {p.name: p for p in wide.wood_parts(True) if not p.name.startswith('leg_')}
    for side in ('left', 'right'):
        p = compact.leg('2x6', 0., side)
        parts[p.name] = p
    return tuple(parts.values())


@cache
def parts():
    """Occupied screw/bolt display cuts, never final receiver-pilot instructions."""
    result = {p.name: p for p in wood_parts()}
    result.update({p.name: p for p in wide.hardware.clip_parts(tuple(wide.stations()))})
    for c in connections():
        for index, name in enumerate(c.members):
            if name.startswith('clip_'):
                continue
            p = result[name]
            diameter = 11.1125 if c.kind == 'bolt' else c.diameter
            shape = p.shape.cut(cq.Solid.makeCylinder(diameter/2, c.length+2,
                                                     c.start-c.direction, c.direction))
            if index == 0 and c.kind == 'screw':
                shape = shape.cut(c.components()[1])
            if name == 'timber_bottom_backing' and c.name.startswith('timber_backing_bolt_'):
                shape = shape.cut(cq.Solid.makeCylinder(28.575/2, 10.+WASHER,
                    c.start-wide.b.normal()*10., wide.b.normal()))
            result[name] = replace(p, shape=shape.clean())
    return tuple(result.values())
