"""Targeted base and bolt-layout revision; geometric fit is not strength approval."""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import lumber_leg_spread_frame as leg
from . import square_2x6_base_revision as base_revision
from . import square_2x6_frame as previous

b, base, hardware, timber, wide = previous.b, previous.base, previous.hardware, previous.timber, previous.wide
UPRIGHTS, CENTERS, LOWER_S = previous.UPRIGHTS, previous.CENTERS, previous.LOWER_S
KEY = 'square-2x6-revised-development'
LIMITS = ('All single 2x6 lumber, including the shallow header; revised bolt layout; geometric development only, '
          'connection resistance, header bending, panel overhang and floor stability unqualified')


def bolt_points():
    old, _, along, _ = leg.geometry('2x6', 0.)
    # Keep the group centered on the existing leg, moving downhill until its
    # rim-normal coordinate is halfway through the narrower 139.7 mm rim.
    n = (old-b.point(0., 0., 0.)).dot(b.normal())
    centre = old+along*((139.7/2-n)/along.dot(b.normal()))
    tangent = (b.point(0., 1., 0.)-b.point(0., 0., 0.)).normalized()
    return tuple(centre+along*s+tangent*t for s in (-35., 35.) for t in (-25., 25.))


@cache
def stations():
    return tuple(s for s in previous.stations() if 'header_' not in s[0])+base_revision.base_stations()


@cache
def wood_parts():
    result = {p.name: p for p in previous.wood_parts() if p.name not in base_revision.REMOVED_NAMES}
    result.update(base_revision.base_parts())
    return tuple(result.values())


@cache
def connections():
    result = list(hardware.clip_connections(stations()))
    base_bolts, points = base_revision.base_connections(), bolt_points()
    for c in previous.connections():
        if c.name.startswith('clip_'):
            continue
        if c.name in base_bolts:
            c = base_bolts[c.name]
        if c.name.startswith('lumber_leg_bolt_'):
            p = points[int(c.name.rsplit('_', 1)[1])-1]
            c = replace(c, start=cq.Vector(c.start.x, p.y, p.z),
                        product_status=c.product_status+'; NEW 70x50 group, not retrofit drilling')
        elif c.name in tuple(f'timber_base_{side}_{i}' for side in ('left', 'right') for i in (1, 2)):
            s = -12. if c.name.endswith('_1') else 28.
            c = replace(c, start=b.point(c.start.x, s, 95.),
                        product_status=c.product_status+'; new below-rail rim axes; strength/spacing unqualified')
        result.append(c)
    return tuple(result)


@cache
def parts():
    result = {p.name: p for p in wood_parts()}
    result.update({p.name: p for p in hardware.clip_parts(stations())})
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
            result[name] = replace(p, shape=shape.clean())
    return tuple(result.values())
