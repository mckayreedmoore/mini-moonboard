"""One member per framing line; shared panel seams remain unqualified.

Unlike the preceding single-stock candidate, there are no paired seam rails or
closely spaced center principals/posts. New occupied fastener holes are cut
from raw panels and receivers; this is not a retrofit drilling schedule.
"""
from dataclasses import replace
from functools import cache
from math import hypot

import cadquery as cq

from . import square_2x6_revised_frame as previous

b, base, hardware, timber, wide, leg = (previous.b, previous.base, previous.hardware,
                                      previous.timber, previous.wide, previous.leg)
KEY = 'single-2x6-development'
LIMITS = ('One single 2x6 per framing line, including header; shared seam screw '
          'margins, service pockets, bearing, connections and stability unqualified; NOT build-ready')
UPRIGHTS = {'center': (-19.05, 19.05)}
CENTERS = {'center': 0.}
LOWER_S = previous.LOWER_S
SEAM_S = (b.HALF-19.05, b.HALF+19.05)
BAYS = (('left', -base.INNER_EDGE, -19.05), ('right', 19.05, base.INNER_EDGE))


def bolt_points():
    return previous.bolt_points()


@cache
def stations():
    """Stagger opposing rail clips; use one center clip on continuous beams.

Opposite faces of a 38.1 mm principal cannot receive coincident 35.54 mm
connector-screw penetrations. The left/right seam and bottom clips use opposite
rail faces. Continuous top rail and header each have only one center clip.
This geometry does not transfer a predecessor's connection capacity.
"""
    result = []
    tangent = (b.point(0., 1., 0.)-b.point(0., 0., 0.)).normalized()
    for level, low, high in (('top', b.LENGTH-38.1, b.LENGTH),
                             ('mid', *SEAM_S), ('bottom', *LOWER_S)):
        for side, x0, x1 in BAYS:
            station, v = (high, tangent) if side == 'right' and level != 'top' else (low, -tangent)
            beam = 'base_rail_top' if level == 'top' else f'base_rail_{level}_{side}'
            ends = ((x0, 1., f'base_side_{side}'), (x1, -1., 'base_principal_center')) if side == 'left' else (
                    (x0, 1., 'base_principal_center'), (x1, -1., f'base_side_{side}'))
            for index, (x, sign, upright) in enumerate(ends, 1):
                if level == 'top' and side == 'right' and upright == 'base_principal_center':
                    continue
                # Keep outer lower clips above the rail to clear the
                # retained gusset bolts. Only center clips need staggering.
                clip_station, clip_v = ((high, tangent) if level == 'bottom' and
                                        upright.startswith('base_side_') else (station, v))
                result.append((f'clip_single_{level}_{side}_{index}', b.point(x, clip_station, 88.9),
                               cq.Vector(sign, 0., 0.), clip_v, beam, upright))
    for name, origin, u, v, beam, upright in previous.stations():
        if 'header_outer_' in name:
            result.append((name, origin, u, v, beam, upright))
        elif 'header_center_left' in name:
            result.append(('clip_single_header_center', cq.Vector(-19.05, origin.y, origin.z),
                           u, v, beam, 'base_post_center'))
    return tuple(result)


def _service_cut(shape):
    bounds = shape.BoundingBox()
    for cutter in timber.service_envelopes():
        cb = cutter.BoundingBox()
        if all(getattr(bounds, a+'max') >= getattr(cb, a+'min') and
               getattr(cb, a+'max') >= getattr(bounds, a+'min') for a in 'xyz'):
            shape = shape.cut(cutter)
    return shape.clean()


@cache
def wood_parts():
    removed = ('base_principal_', 'base_post_center_', 'base_rail_mid_', 'base_rail_bottom_')
    result = {p.name: p for p in previous.wood_parts() if not p.name.startswith(removed)}
    # Hold and LED bores only: no predecessor screw locations or insert pilots.
    result.update({p.name: p for p in base.parts(True) if p.name.startswith(('main_', 'kicker_'))})
    shape, blank = base._sloped_bearing_member(-19.05, 19.05, 139.7, b.LENGTH-38.1)
    result['base_principal_center'] = b.Part('base_principal_center', _service_cut(shape), blank,
        'One centered 2x6; no lower housing; front hold/LED service pockets remain; '+LIMITS, 1)
    result['base_post_center'] = b.Part('base_post_center', base._world_box(-19.05, 19.05,
        base.HEADER_FRONT_Y-139.7, base.HEADER_FRONT_Y, 0., base.HEADER_BOTTOM),
        (base.HEADER_BOTTOM, 139.7, 38.1), 'One square-cut central 2x6 post; '+LIMITS, 1)
    for side, x0, x1 in BAYS:
        for level, span in (('mid', SEAM_S), ('bottom', LOWER_S)):
            name = f'base_rail_{level}_{side}'
            shape = b.block(x0, x1, *span, 0., 139.7)
            if level == 'mid':
                shape = _service_cut(shape)
            result[name] = b.Part(name, shape, (x1-x0, 139.7, 38.1),
                ('One shared seam rail; front LED service pockets; ' if level == 'mid' else
                 'Square-cut lower rail between members; no light relief cuts; ')+LIMITS, 1)
    return tuple(result.values())


@cache
def connections():
    result = list(hardware.clip_connections(stations()))
    service = [(x-b.HALF, s) for x, s in
               (*timber.grid.main_tnut_datums().values(), *timber.grid.main_led_datums().values())]
    for c in previous.connections():
        if c.name.startswith('clip_'):
            continue
        if not isinstance(c, timber.PanelScrew):
            result.append(c)
            continue
        panel, receiver = c.members
        side = 'left' if '_left_' in c.name else 'right'
        sign = -1. if side == 'left' else 1.
        start = c.start
        if panel.startswith('main_'):
            origin = b.point(0., 0., 0.)
            tangent = (b.point(0., 1., 0.)-origin).normalized()
            s = (start-origin).dot(tangent)
            x = start.x
            if receiver.startswith('base_principal_'):
                x, receiver = sign*9.525, 'base_principal_center'
                # Stagger left/right shared-member screws, retaining the face
                # panel ownership and clearing every reserved service cylinder.
                target = s + (20. if side == 'right' else -20.)
                low, high = (0., b.HALF) if 'lower' in panel else (b.HALF, b.LENGTH)
                s = next(target+d for d in (0., *[v for k in range(1, 81) for v in (k, -k)])
                         if low+30. <= target+d <= high-30. and
                         all(hypot(x-hx, target+d-hs) >= 28. for hx, hs in service))
            elif receiver.startswith('base_rail_mid_'):
                receiver = f'base_rail_mid_{side}'
                s = b.HALF + (-9.525 if 'lower' in panel else 9.525)
                target = x + (-15. if 'lower' in panel else 15.)
                x = next(target+d for d in (0., *[v for k in range(1, 81) for v in (k, -k)])
                         if all(hypot(target+d-hx, s-hs) >= 28. for hx, hs in service))
            start = b.point(x, s, -wide.PANEL)
        elif receiver.startswith('base_post_center_'):
            receiver = 'base_post_center'
            start = cq.Vector(sign*9.525, start.y, start.z+(20. if side == 'right' else -10.))
        result.append(replace(c, start=start, members=(panel, receiver),
                              product_status=c.product_status+'; new shared-member drilling; '+LIMITS))
    return tuple(result)


@cache
def parts():
    """Fresh occupied screw/bolt cuts; future insert reserves are not machined."""
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
