"""Selective single-stock enlargement of the preserved all-2x6 baseline.

Four shared receivers use single 63.5 x 139.7 mm members and the flat header
uses one 38.1 x 234.95 mm member. No sisters, built-up members or insert pilots.
Nominal geometry only; supplier stock, connection resistance and loads unqualified.
"""
from dataclasses import replace
from functools import cache
from math import hypot

import cadquery as cq

from . import single_2x6_frame as previous

b, base, hardware, timber, wide, leg = (previous.b, previous.base, previous.hardware,
                                      previous.timber, previous.wide, previous.leg)
KEY = 'selective-2x6-development'
SHARED_WIDTH = 63.5
HEADER_DEPTH = 234.95
UPRIGHTS = {'center': (-SHARED_WIDTH/2, SHARED_WIDTH/2)}
CENTERS = {'center': 0.}
LOWER_S = previous.LOWER_S
SEAM_S = (b.HALF-SHARED_WIDTH/2, b.HALF+SHARED_WIDTH/2)
BAYS = (('left', -base.INNER_EDGE, -SHARED_WIDTH/2),
        ('right', SHARED_WIDTH/2, base.INNER_EDGE))
LIMITS = ('Single solid stock only: nine 2x6 members, four nominal 3x6 shared receivers '
          'and one flat 2x10 header; stock availability, service pockets, bearing, '
          'connections and stability unqualified; NOT build-ready')


def bolt_points():
    return previous.bolt_points()


@cache
def stations():
    """Retain stagger and rear clip depth; move origins to enlarged wood faces."""
    tangent = (b.point(0., 1., 0.)-b.point(0., 0., 0.)).normalized()
    result = []
    for name, origin, u, v, beam, upright in previous.stations():
        if upright in ('base_principal_center', 'base_post_center'):
            origin = cq.Vector((-1. if origin.x < 0. else 1.)*SHARED_WIDTH/2,
                               origin.y, origin.z)
        if beam.startswith('base_rail_mid_'):
            # The clip occupies the open side of its rail contact plane.
            origin = origin+v*((SHARED_WIDTH-38.1)/2)
            assert abs(abs(v.dot(tangent))-1.) < 1e-8
        result.append((name, origin, u, v, beam, upright))
    return tuple(result)


@cache
def wood_parts():
    """Replace raw members, preserving existing panel bores without old screw cuts."""
    result = {p.name: p for p in previous.wood_parts()}
    for name, part in tuple(result.items()):
        description = None
        if name.startswith('base_side_'):
            description = 'Single nominal 2x6 outer rim; grain along slope; level bearing cut'
        elif name.startswith('base_post_outer_'):
            description = 'Single nominal 2x6 outer post; vertical grain; square ends'
        elif name.startswith('lumber_leg_'):
            description = 'Single nominal 2x6 leg; retained square top and level foot; relocated bolt group'
        elif name == 'base_rail_top':
            description = 'Single nominal 2x6 top crossmember; grain X; square cut'
        if description:
            result[name] = replace(part, description=description+'; '+LIMITS)
    shape, blank = base._sloped_bearing_member(*UPRIGHTS['center'], 139.7, b.LENGTH-38.1)
    result['base_principal_center'] = b.Part('base_principal_center', previous._service_cut(shape), blank,
        'Single nominal 3x6 center principal; square lower bearing cut; front service pockets; '+LIMITS, 1)
    result['base_post_center'] = b.Part('base_post_center', base._world_box(*UPRIGHTS['center'],
        base.HEADER_FRONT_Y-139.7, base.HEADER_FRONT_Y, 0., base.HEADER_BOTTOM),
        (base.HEADER_BOTTOM, 139.7, SHARED_WIDTH), 'Single nominal 3x6 center post; '+LIMITS, 1)
    result['base_header'] = b.Part('base_header', base._world_box(-b.HALF, b.HALF,
        base.HEADER_FRONT_Y-HEADER_DEPTH, base.HEADER_FRONT_Y, base.HEADER_BOTTOM, base.HEADER_TOP),
        (2*b.HALF, HEADER_DEPTH, 38.1), 'Single nominal 2x10 flat header; retained front datum and height; '+LIMITS, 1)
    for side, x0, x1 in BAYS:
        for level, span in (('mid', SEAM_S), ('bottom', LOWER_S)):
            name = f'base_rail_{level}_{side}'
            shape = b.block(x0, x1, *span, 0., 139.7)
            if level == 'mid':
                shape = previous._service_cut(shape)
            result[name] = b.Part(name, shape, (x1-x0, 139.7, SHARED_WIDTH if level == 'mid' else 38.1),
                ('Single nominal 3x6 shared seam rail; front service pockets; ' if level == 'mid' else
                 'Single square-cut 2x6 bottom rail; no light relief cuts; ')+LIMITS, 1)
    return tuple(result.values())


@cache
def connections():
    """Relocate shared screw rows; reuse stagger once and regenerate occupied holes."""
    result = list(hardware.clip_connections(stations()))
    service = [(x-b.HALF, s) for x, s in
               (*timber.grid.main_tnut_datums().values(), *timber.grid.main_led_datums().values())]
    shifts = (0., *[v for k in range(1, 81) for v in (k, -k)])
    tangent = (b.point(0., 1., 0.)-b.point(0., 0., 0.)).normalized()
    for c in previous.connections():
        if c.name.startswith('clip_'):
            continue
        if not isinstance(c, timber.PanelScrew):
            result.append(c)
            continue
        panel, receiver = c.members
        start = c.start
        if panel.startswith('main_'):
            s = (start-b.point(0., 0., 0.)).dot(tangent)
            x = start.x
            if receiver == 'base_principal_center':
                x = (-1. if x < 0. else 1.)*SHARED_WIDTH/4
                low, high = (0., b.HALF) if 'lower' in panel else (b.HALF, b.LENGTH)
                s = next(s+d for d in shifts if low+30. <= s+d <= high-30. and
                         all(hypot(x-hx, s+d-hs) >= 28. for hx, hs in service))
            elif receiver.startswith('base_rail_mid_'):
                s = b.HALF+(-1. if 'lower' in panel else 1.)*SHARED_WIDTH/4
                _, x0, x1 = next(bay for bay in BAYS if receiver.endswith(bay[0]))
                x = next(x+d for d in shifts if x0+30. <= x+d <= x1-30. and
                         all(hypot(x+d-hx, s-hs) >= 28. for hx, hs in service))
            start = b.point(x, s, -wide.PANEL)
        elif receiver == 'base_post_center':
            start = cq.Vector((-1. if start.x < 0. else 1.)*SHARED_WIDTH/4, start.y, start.z)
        result.append(replace(c, start=start, product_status=timber.PanelScrew.product_status+
                              '; fresh shared-member drilling; future repair space not predrilled; '+LIMITS))
    return tuple(result)


@cache
def parts():
    """Cut new occupied screw/bolt holes only; repair reservations stay solid."""
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
