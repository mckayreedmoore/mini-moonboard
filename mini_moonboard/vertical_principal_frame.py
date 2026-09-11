"""Four additional single 2x6 principals replace the paired horizontal seam rails.

New full-height receivers avoid the reserved service cylinders without pockets.
Their aligned single 2x10 posts support the complete bearing footprint. Existing
outer gussets and center members remain; no joint resistance is qualified.
"""
from dataclasses import replace
from functools import cache
from math import hypot

import cadquery as cq

from . import paired_rail_frame as previous

b, base, hardware, timber, wide, leg = (previous.b, previous.base, previous.hardware,
                                      previous.timber, previous.wide, previous.leg)
KEY = 'vertical-principal-development'
SHARED_WIDTH, HEADER_DEPTH = previous.SHARED_WIDTH, previous.HEADER_DEPTH
LOWER_S, BAYS = previous.LOWER_S, previous.BAYS
ADDED_CENTERS = {'left_1': -770., 'left_2': -370., 'right_1': 430., 'right_2': 830.}
UPRIGHTS = {**previous.UPRIGHTS, **{name: (x-19.05, x+19.05) for name, x in ADDED_CENTERS.items()}}
CENTERS = {**previous.CENTERS, **ADDED_CENTERS}
LIMITS = ('Four additional independent single 2x6 principals; no horizontal seam rails; '
          'single 2x10 posts below added principals; retained center and outer members; '
          'panel spans, connections, header bending and stability unqualified; NOT build-ready')


def bolt_points():
    return previous.bolt_points()


def bottom_bays():
    """Three independent bottom-rail segments in each panel bay."""
    result = []
    for side, low, high in BAYS:
        added = [(name, x) for name, x in ADDED_CENTERS.items() if name.startswith(side)]
        edges = [(low, f'base_side_{side}' if side == 'left' else 'base_principal_center')]
        for name, x in added:
            edges.extend(((x-19.05, f'base_principal_{name}'), (x+19.05, f'base_principal_{name}')))
        edges.append((high, 'base_principal_center' if side == 'left' else f'base_side_{side}'))
        for index in range(3):
            (x0, first), (x1, second) = edges[2*index:2*index+2]
            result.append((f'base_rail_bottom_{side}_{index+1}', x0, x1, first, second))
    return tuple(result)


@cache
def stations():
    result = [station for station in previous.stations()
              if not station[4].startswith(('base_rail_mid_', 'base_rail_bottom_'))]
    tangent = (b.point(0., 1., 0.)-b.point(0., 0., 0.)).normalized()
    for beam, x0, x1, first, second in bottom_bays():
        for index, (x, sign, upright) in enumerate(((x0, 1., first), (x1, -1., second)), 1):
            upper = index == 2
            if upright.startswith('base_side_'):
                upper = True
            elif upright == 'base_principal_center':
                upper = x > 0.
            s, v = (LOWER_S[1], tangent) if upper else (LOWER_S[0], -tangent)
            result.append((beam.replace('base_rail_', 'clip_vertical_')+f'_{index}',
                b.point(x, s, 88.9), cq.Vector(sign, 0., 0.), v, beam, upright))
    for name, x in ADDED_CENTERS.items():
        principal, post = f'base_principal_{name}', f'base_post_{name}'
        result.append((f'clip_vertical_top_{name}', b.point(x+19.05, b.LENGTH-38.1, 88.9),
            cq.Vector(1., 0., 0.), -tangent, 'base_rail_top', principal))
        # The right-side lower-rail clip occupies the lower principal region.
        # Put base retention on the opposite face, below its upper-rail clip.
        result.append((f'clip_vertical_base_{name}', cq.Vector(x-19.05, -135., base.HEADER_TOP),
            cq.Vector(-1., 0., 0.), cq.Vector(0., 0., 1.), 'base_header', principal))
        result.append((f'clip_vertical_header_{name}',
            cq.Vector(x+19.05, base.HEADER_FRONT_Y-HEADER_DEPTH/2, base.HEADER_BOTTOM),
            cq.Vector(1., 0., 0.), cq.Vector(0., 0., -1.), 'base_header', post))
    return tuple(result)


@cache
def wood_parts():
    result = {p.name: replace(p, description=p.description.replace(previous.LIMITS, LIMITS))
              for p in previous.wood_parts() if not p.name.startswith(('base_rail_mid_', 'base_rail_bottom_'))}
    for name, x in ADDED_CENTERS.items():
        shape, blank = base._sloped_bearing_member(x-19.05, x+19.05, 139.7, b.LENGTH-38.1)
        principal = f'base_principal_{name}'
        result[principal] = b.Part(principal, shape, (*blank[:2], 38.1),
            'Independent single nominal 2x6 principal; no service pockets or lower housing; '
            'level full bearing cut; grain along slope; '+LIMITS, 1)
        post = f'base_post_{name}'
        result[post] = b.Part(post, base._world_box(x-19.05, x+19.05,
            base.HEADER_FRONT_Y-HEADER_DEPTH, base.HEADER_FRONT_Y, 0., base.HEADER_BOTTOM),
            (base.HEADER_BOTTOM, HEADER_DEPTH, 38.1),
            'Single nominal 2x10 vertical-grain post; full header-depth support beneath added principal; '+LIMITS, 1)
    for name, x0, x1, _, _ in bottom_bays():
        result[name] = b.Part(name, b.block(x0, x1, *LOWER_S, 0., 139.7),
            (x1-x0, 139.7, 38.1), 'Independent square-cut single 2x6 bottom-rail segment; '
            'no service pockets; '+LIMITS, 1)
    return tuple(result.values())


@cache
def connections():
    """Replace eight seam screws with 32 screws along the four new principals."""
    result = list(hardware.clip_connections(stations()))
    service = [(x-b.HALF, s) for x, s in
               (*timber.grid.main_tnut_datums().values(), *timber.grid.main_led_datums().values())]
    shifts = (0., *[v for k in range(1, 121) for v in (k, -k)])
    for c in previous.connections():
        if c.name.startswith('clip_'):
            continue
        if isinstance(c, timber.PanelScrew):
            panel, receiver = c.members
            if receiver.startswith('base_rail_mid_'):
                continue
            if receiver.startswith('base_rail_bottom_'):
                side = 'left' if panel.endswith('left') else 'right'
                s = sum(LOWER_S)/2
                choices = [(abs(d), name, c.start.x+d) for d in shifts
                           for name, x0, x1, _, _ in bottom_bays() if f'_{side}_' in name
                           and x0+44.45 <= c.start.x+d <= x1-44.45
                           and all(hypot(c.start.x+d-hx, s-hs) >= 28. for hx, hs in service)]
                _, receiver, x = min(choices, key=lambda row: row[0])
                c = replace(c, start=b.point(x, s, -wide.PANEL), members=(panel, receiver))
            c = replace(c, product_status=timber.PanelScrew.product_status+'; fresh drilling; '+LIMITS)
        result.append(c)
    for name, x in ADDED_CENTERS.items():
        side = name.split('_')[0]
        for row, band in enumerate(('lower', 'upper')):
            low, high = row*b.HALF, (row+1)*b.HALF
            for index, s in enumerate((low+80., low+400., low+800., high-100.), 1):
                result.append(timber.PanelScrew(f'vertical_panel_{band}_{name}_{index}',
                    b.point(x, s, -wide.PANEL), b.normal(), 50.8, 4.1402,
                    (f'main_{band}_{side}', f'base_principal_{name}'),
                    product_status=timber.PanelScrew.product_status+'; fresh drilling; '+LIMITS))
    return tuple(result)


@cache
def parts():
    """Fresh occupied screw/bolt holes only; no insert or repair pilots."""
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
