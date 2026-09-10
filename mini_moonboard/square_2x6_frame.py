"""Single 2x6 principals and square lower rails; unqualified fit candidate."""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import base_frame as base
from . import box_frame as b
from . import screw_mvp_frame as previous
from . import timber_connections as hardware
from . import timber_frame as timber
from . import wide_frame as wide

KEY = 'square-2x6-development'
LIMITS = ('Single-member 2x6 development; no lower principal housing or continuous bottom backing; '
          'connection resistance, panel-edge support and floor stability unqualified; NOT build-ready')
UPRIGHTS = base.UPRIGHTS
CENTERS = {side: sum(bounds)/2 for side, bounds in UPRIGHTS.items()}
LOWER_S = (40., 78.1)


@cache
def stations():
    result = list(hardware.stations())
    tangent = (b.point(0., 1., 0.)-b.point(0., 0., 0.)).normalized()
    for side, x0, x1 in (('left', -base.INNER_EDGE, UPRIGHTS['left'][0]),
                        ('right', UPRIGHTS['right'][1], base.INNER_EDGE)):
        for index, (x, sign, upright) in enumerate(
                ((x0, 1., f'base_side_{side}'), (x1, -1., f'base_principal_{side}'))
                if side == 'left' else
                ((x0, 1., f'base_principal_{side}'), (x1, -1., f'base_side_{side}')), 1):
            result.append((f'clip_square_bottom_{side}_{index}', b.point(x, LOWER_S[1], 88.9),
                           cq.Vector(sign, 0., 0.), tangent, f'base_rail_bottom_{side}', upright))
    for name, origin, u, v, beam, upright in wide.stations():
        if 'header_' not in name:
            continue
        if 'header_center_' in name:
            side = 'left' if '_left_' in name else 'right'
            x = UPRIGHTS[side][0 if side == 'left' else 1]
            origin = cq.Vector(x, origin.y, origin.z)
        result.append((name, origin, u, v, beam, upright))
    return tuple(result)


@cache
def wood_parts():
    result = {p.name: p for p in previous.wood_parts()}
    del result['timber_bottom_backing']
    for name, p in tuple(result.items()):
        if name.startswith('base_side_'):
            tool = b.block(-2000., 2000., -1000., 4000., 0., 139.7)
        elif name == 'base_header' or name.startswith('base_post_outer_'):
            tool = base._world_box(-2000., 2000., base.HEADER_FRONT_Y-139.7,
                                   base.HEADER_FRONT_Y, -1000., 4000.)
        else:
            continue
        result[name] = replace(p, shape=p.shape.intersect(tool).clean(),
                               blank=(p.blank[0], 139.7, 38.1),
                               description='Single 2x6 direct substitution; retained axes may fail fit; '+LIMITS)
    fresh = {p.name: p for p in base.parts(True)}
    cutters = timber.service_envelopes()
    for name, p in fresh.items():
        if not name.startswith(('base_principal_', 'base_rail_mid_')):
            continue
        shape = p.shape
        bb = shape.BoundingBox()
        for cutter in cutters:
            cb = cutter.BoundingBox()
            if all(getattr(bb, a+'max') >= getattr(cb, a+'min') and
                   getattr(cb, a+'max') >= getattr(bb, a+'min') for a in 'xyz'):
                shape = shape.cut(cutter)
        result[name] = replace(p, shape=shape.clean(), description=LIMITS)
    for side, (x0, x1) in UPRIGHTS.items():
        for end, (y0, y1) in wide.POST_Y.items():
            name = f'base_post_center_{side}_{end}'
            result[name] = b.Part(name, base._world_box(x0, x1, y0, y1, 0., base.HEADER_BOTTOM),
                                 (base.HEADER_BOTTOM, 139.7, 38.1),
                                 'Square-cut single 2x6 vertical-grain post; '+LIMITS, 1)
        xa, xb = (-base.INNER_EDGE, x0) if side == 'left' else (x1, base.INNER_EDGE)
        name = f'base_rail_bottom_{side}'
        result[name] = b.Part(name, b.block(xa, xb, *LOWER_S, 0., 139.7),
                             (xb-xa, 139.7, 38.1),
                             'Square-cut single 2x6 rail; no hold/LED relief cuts; grain X; '+LIMITS, 1)
    return tuple(result.values())


@cache
def connections():
    result = list(hardware.clip_connections(stations()))
    for c in previous.connections():
        if c.name.startswith(('clip_', 'timber_backing_bolt_')):
            continue
        if isinstance(c, timber.PanelScrew):
            side = 'left' if '_left_' in c.name else 'right'
            panel, receiver = c.members
            start = c.start
            if abs(start.x-wide.CENTERS[side]) < 1e-6:
                start = cq.Vector(CENTERS[side], start.y, start.z)
            if receiver == 'timber_bottom_backing':
                if abs(start.x-CENTERS[side]) < 1e-6:
                    receiver = f'base_principal_{side}'
                else:
                    receiver = f'base_rail_bottom_{side}'
                    start = b.point(start.x, sum(LOWER_S)/2, -wide.PANEL)
            c = replace(c, start=start, members=(panel, receiver))
        result.append(c)
    return tuple(result)


@cache
def parts():
    """Display clearance cuts only; no insert or insert-pilot machining."""
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
