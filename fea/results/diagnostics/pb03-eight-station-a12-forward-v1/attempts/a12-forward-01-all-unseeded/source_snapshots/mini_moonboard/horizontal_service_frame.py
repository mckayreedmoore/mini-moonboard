"""Horizontal service rails replace four intermediate vertical principals.

The two separated center principals, outer rims, full-depth support posts and
base angles remain. The lower service rail sits below the lower panel's top
hold row; the upper rail sits immediately inside the upper panel's lower edge.
These explicit provisional locations do not establish panel or frame strength.
"""
from dataclasses import replace
from functools import cache
from math import hypot

import cadquery as cq

from . import angle_base_frame as previous
from . import horizontal_service_wiring as wiring

b, base, hardware, timber, wide, leg = (previous.b, previous.base, previous.hardware,
                                      previous.timber, previous.wide, previous.leg)
KEY = 'horizontal-service-development'
HEADER_DEPTH, LOWER_S, BAYS = previous.HEADER_DEPTH, previous.LOWER_S, previous.BAYS
CENTER_SPLIT = previous.CENTER_SPLIT
ADDED_CENTERS = dict(CENTER_SPLIT)
CENTERS = dict(CENTER_SPLIT)
UPRIGHTS = {name: previous.UPRIGHTS[name] for name in CENTER_SPLIT}
CENTER_CLEAR_GAP, CENTER_PANEL_OVERHANG = previous.CENTER_CLEAR_GAP, previous.CENTER_PANEL_OVERHANG
RAIL_SPANS = {'lower': (1031.1, 1069.2), 'upper': (1219.2, 1257.3)}
REMOVED_NAMES = {f'base_{kind}_{side}_{index}' for kind in ('principal', 'post')
                 for side in ('left', 'right') for index in (1, 2)}
LIMITS = ('Four horizontal single 2x6 service rails replace four intermediate principals '
          'and posts; split center pair and outer base angles retained; provisional rail '
          'placement, panel spans, wiring access, connections and stability unqualified; NOT build-ready')

bolt_points = previous.bolt_points


def bottom_bays():
    return tuple((f'base_rail_bottom_{side}', x0, x1,
        f'base_side_{side}' if side == 'left' else 'base_principal_center_right',
        'base_principal_center_left' if side == 'left' else f'base_side_{side}')
        for side, x0, x1 in BAYS)


@cache
def stations():
    result = [station for station in previous.stations()
              if station[5] not in REMOVED_NAMES and not station[4].startswith('base_rail_bottom_')]
    tangent = (b.point(0., 1., 0.)-b.point(0., 0., 0.)).normalized()
    for bottom, x0, x1, first, second in bottom_bays():
        side = bottom.rsplit('_', 1)[1]
        for level, span in (('bottom', LOWER_S), *RAIL_SPANS.items()):
            beam = bottom if level == 'bottom' else f'base_rail_service_{level}_{side}'
            s, v = (span[0], -tangent) if level == 'lower' else (span[1], tangent)
            for index, (x, sign, upright) in enumerate(((x0, 1., first), (x1, -1., second)), 1):
                result.append((f'clip_horizontal_{level}_{side}_{index}', b.point(x, s, 88.9),
                    cq.Vector(sign, 0., 0.), v, beam, upright))
    return tuple(result)


@cache
def uncut_wood_parts():
    result = {p.name: replace(p, description=p.description.replace(previous.LIMITS, LIMITS))
              for p in previous.wood_parts()
              if p.name not in REMOVED_NAMES and not p.name.startswith('base_rail_bottom_')}
    for side, x0, x1 in BAYS:
        for level, span in (('bottom', LOWER_S), *RAIL_SPANS.items()):
            name = f'base_rail_bottom_{side}' if level == 'bottom' else f'base_rail_service_{level}_{side}'
            result[name] = b.Part(name, b.block(x0, x1, *span, 0., 139.7),
                (x1-x0, 139.7, 38.1), 'Independent square-cut single 2x6 horizontal rail; '
                'grain X; no inherited service pockets; '+LIMITS, 1)
    return tuple(result.values())


@cache
def cutout_records():
    return wiring.cutout_records(uncut_wood_parts())


@cache
def wood_parts():
    result = {p.name: p for p in uncut_wood_parts()}
    for record in cutout_records():
        part = result[record['member']]
        result[part.name] = replace(part, shape=part.shape.cut(wiring.cutout_shape(record)).clean(),
            description=part.description+'; open-front cable channel, provisional dimensions')
    return tuple(result.values())


electrical_parts = wiring.parts


@cache
def connections():
    """Keep supported axes; replace removed-principal screws with rail screws."""
    result = list(hardware.clip_connections(stations()))
    for c in previous.connections():
        if c.name.startswith('clip_') or any(name in REMOVED_NAMES for name in c.members):
            continue
        if isinstance(c, timber.PanelScrew) and c.members[1].startswith('base_rail_bottom_'):
            side = 'left' if c.members[0].endswith('left') else 'right'
            c = replace(c, members=(c.members[0], f'base_rail_bottom_{side}'))
        result.append(c)
    service = [(x-b.HALF, s) for x, s in
               (*timber.grid.main_tnut_datums().values(), *timber.grid.main_led_datums().values())]
    shifts = (0., *[v for k in range(1, 81) for v in (k, -k)])
    for side, x0, x1 in BAYS:
        for level, span in RAIL_SPANS.items():
            s = sum(span)/2
            for index, fraction in enumerate((.2, .4, .6, .8), 1):
                target = x0+(x1-x0)*fraction
                x = next(target+d for d in shifts if x0+44.45 <= target+d <= x1-44.45
                         and all(hypot(target+d-hx, s-hs) >= 28. for hx, hs in service))
                result.append(timber.PanelScrew(f'horizontal_panel_{level}_{side}_{index}',
                    b.point(x, s, -wide.PANEL), b.normal(), 50.8, 4.1402,
                    (f'main_{level}_{side}', f'base_rail_service_{level}_{side}'),
                    product_status=timber.PanelScrew.product_status+'; fresh drilling; '+LIMITS))
    return tuple(result)


@cache
def parts():
    """Fresh machining from revised raw members; no orphan screw or clip holes."""
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
