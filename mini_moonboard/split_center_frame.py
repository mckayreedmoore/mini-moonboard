"""Two separated single 2x6 center principals with an open service corridor.

The historical single-center model remains unchanged. Each new principal has
its own full-depth post and independent clips. The 101.9 mm clear corridor
leaves 50.95 mm unsupported panel edges at the vertical joint; panel behavior
and connection resistance remain qualification tasks.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import vertical_principal_frame as previous
from .split_center_hardware import with_hex_ends

b, base, hardware, timber, wide, leg = (previous.b, previous.base, previous.hardware,
                                      previous.timber, previous.wide, previous.leg)
KEY = 'split-center-development'
HEADER_DEPTH, LOWER_S = previous.HEADER_DEPTH, previous.LOWER_S
CENTER_SPLIT = {'center_left': -70., 'center_right': 70.}
ADDED_CENTERS = {**previous.ADDED_CENTERS, **CENTER_SPLIT}
CENTERS = dict(ADDED_CENTERS)
UPRIGHTS = {name: (x-19.05, x+19.05) for name, x in CENTERS.items()}
BAYS = (('left', -base.INNER_EDGE, -89.05), ('right', 89.05, base.INNER_EDGE))
CENTER_CLEAR_GAP = 101.9
CENTER_PANEL_OVERHANG = 50.95
LIMITS = ('Six independent single 2x6 interior principals; separated center pair with '
          'open service corridor and single 2x10 support posts; retained outer gussets; '
          'panel joint overhang, connections, header and stability unqualified; NOT build-ready')


def bolt_points():
    return previous.bolt_points()


def bottom_bays():
    result = []
    for name, x0, x1, first, second in previous.bottom_bays():
        if first == 'base_principal_center':
            x0, first = UPRIGHTS['center_right'][1], 'base_principal_center_right'
        if second == 'base_principal_center':
            x1, second = UPRIGHTS['center_left'][0], 'base_principal_center_left'
        result.append((name, x0, x1, first, second))
    return tuple(result)


@cache
def stations():
    removed = {'base_principal_center', 'base_post_center'}
    result = [station for station in previous.stations() if station[5] not in removed]
    tangent = (b.point(0., 1., 0.)-b.point(0., 0., 0.)).normalized()
    for suffix, x in CENTER_SPLIT.items():
        sign = -1. if x < 0. else 1.
        edge, u = x+sign*19.05, cq.Vector(sign, 0., 0.)
        principal, post = f'base_principal_{suffix}', f'base_post_{suffix}'
        result.append((f'clip_split_top_{suffix}', b.point(edge, b.LENGTH-38.1, 88.9),
            u, -tangent, 'base_rail_top', principal))
        result.append((f'clip_split_base_{suffix}', cq.Vector(edge, -135., base.HEADER_TOP),
            u, cq.Vector(0., 0., 1.), 'base_header', principal))
        result.append((f'clip_split_header_{suffix}',
            cq.Vector(edge, base.HEADER_FRONT_Y-HEADER_DEPTH/2, base.HEADER_BOTTOM),
            u, cq.Vector(0., 0., -1.), 'base_header', post))
        beam = 'base_rail_bottom_left_3' if x < 0. else 'base_rail_bottom_right_1'
        # Above the rail keeps the lower principal region clear for retention.
        result.append((f'clip_split_bottom_{suffix}', b.point(edge, LOWER_S[1], 88.9),
            u, tangent, beam, principal))
    return tuple(result)


@cache
def wood_parts():
    result = {p.name: replace(p, description=p.description.replace(previous.LIMITS, LIMITS))
              for p in previous.wood_parts() if p.name not in ('base_principal_center', 'base_post_center')}
    for suffix, x in CENTER_SPLIT.items():
        shape, blank = base._sloped_bearing_member(x-19.05, x+19.05, 139.7, b.LENGTH-38.1)
        principal = f'base_principal_{suffix}'
        result[principal] = b.Part(principal, shape, (*blank[:2], 38.1),
            'Independent single nominal 2x6 center principal; no service pockets or housing; '
            'level bearing cut; grain along slope; '+LIMITS, 1)
        post = f'base_post_{suffix}'
        result[post] = b.Part(post, base._world_box(x-19.05, x+19.05,
            base.HEADER_FRONT_Y-HEADER_DEPTH, base.HEADER_FRONT_Y, 0., base.HEADER_BOTTOM),
            (base.HEADER_BOTTOM, HEADER_DEPTH, 38.1),
            'Independent single nominal 2x10 center post; vertical grain; full-depth header support; '+LIMITS, 1)
    for side in ('left', 'right'):
        name = f'base_post_outer_{side}'
        bounds = result[name].shape.BoundingBox()
        result[name] = b.Part(name, base._world_box(bounds.xmin, bounds.xmax,
            base.HEADER_FRONT_Y-HEADER_DEPTH, base.HEADER_FRONT_Y, 0., base.HEADER_BOTTOM),
            (base.HEADER_BOTTOM, HEADER_DEPTH, 38.1),
            'Single nominal 2x10 outer post; full-depth header support; retained gusset bolt grips; '+LIMITS, 1)
    for name, x0, x1, _, _ in bottom_bays():
        if name not in ('base_rail_bottom_left_3', 'base_rail_bottom_right_1'):
            continue
        result[name] = b.Part(name, b.block(x0, x1, *LOWER_S, 0., 139.7),
            (x1-x0, 139.7, 38.1), 'Shortened square-cut 2x6 bottom segment; no service pockets; '+LIMITS, 1)
    return tuple(result.values())


@cache
def connections():
    """Keep 80 panel/kicker screws; split the former center receiver by panel."""
    result = list(hardware.clip_connections(stations()))
    for c in previous.connections():
        if c.name.startswith('clip_'):
            continue
        if isinstance(c, timber.PanelScrew):
            panel, receiver = c.members
            if receiver in ('base_principal_center', 'base_post_center'):
                side = 'left' if panel.endswith('left') else 'right'
                receiver += '_'+side
                c = replace(c, start=cq.Vector(CENTER_SPLIT['center_'+side], c.start.y, c.start.z),
                            members=(panel, receiver))
            c = replace(c, product_status=timber.PanelScrew.product_status+'; fresh drilling; '+LIMITS)
        result.append(with_hex_ends(c))
    return tuple(result)


@cache
def parts():
    """Fresh occupied screw/bolt holes only; no installed inserts or repair pilots."""
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
