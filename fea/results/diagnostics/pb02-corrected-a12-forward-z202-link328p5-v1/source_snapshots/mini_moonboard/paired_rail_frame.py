"""Paired independent seam rails and direct center-principal retention.

Only the horizontal seam rails are paired. The center principal and post
remain single nominal 3x6 members; the header remains one nominal 2x10.
No composite action, new insert hardware or connection qualification is assumed.
"""
from dataclasses import replace
from functools import cache
from math import hypot

import cadquery as cq

from . import selective_2x6_frame as previous

b, base, hardware, timber, wide, leg = (previous.b, previous.base, previous.hardware,
                                      previous.timber, previous.wide, previous.leg)
KEY = 'paired-rail-base-development'
SHARED_WIDTH = previous.SHARED_WIDTH
HEADER_DEPTH = previous.HEADER_DEPTH
UPRIGHTS, CENTERS, BAYS = previous.UPRIGHTS, previous.CENTERS, previous.BAYS
LOWER_S = previous.LOWER_S
SEAM_S = (b.HALF-38.1, b.HALF+38.1)
SEAM_SPANS = {'lower': (SEAM_S[0], b.HALF), 'upper': (b.HALF, SEAM_S[1])}
LIMITS = ('Separate paired horizontal 2x6 seam rails with independent end clips; single '
          '3x6 center principal/post and single 2x10 header; no composite action; '
          'service pockets, header bending, connection strength and stability '
          'unqualified; NOT build-ready')


def bolt_points():
    return previous.bolt_points()


@cache
def stations():
    """Each seam rail has two clips; opposing center screw rows are staggered."""
    result = [station for station in previous.stations()
              if not station[4].startswith('base_rail_mid_')]
    tangent = (b.point(0., 1., 0.)-b.point(0., 0., 0.)).normalized()
    for side, x0, x1 in BAYS:
        ends = ((x0, 1., f'base_side_{side}'), (x1, -1., 'base_principal_center')) if side == 'left' else (
                (x0, 1., 'base_principal_center'), (x1, -1., f'base_side_{side}'))
        for level, (low, high) in SEAM_SPANS.items():
            s, v = (low, -tangent) if level == 'lower' else (high, tangent)
            for index, (x, sign, upright) in enumerate(ends, 1):
                depth = 69.85 if side == 'right' and upright == 'base_principal_center' else 88.9
                result.append((f'clip_paired_mid_{level}_{side}_{index}', b.point(x, s, depth),
                    cq.Vector(sign, 0., 0.), v, f'base_rail_mid_{level}_{side}', upright))
    # The vertical side face and level header top are perpendicular. No clip
    # is forced between the inclined rear face and the horizontal header.
    result.append(('clip_paired_base_center', cq.Vector(SHARED_WIDTH/2, -115., base.HEADER_TOP),
        cq.Vector(1., 0., 0.), cq.Vector(0., 0., 1.), 'base_header', 'base_principal_center'))
    return tuple(result)


@cache
def wood_parts():
    result = {p.name: replace(p, description=p.description.replace(previous.LIMITS, LIMITS))
              for p in previous.wood_parts() if not p.name.startswith('base_rail_mid_')}
    for side, x0, x1 in BAYS:
        for level, span in SEAM_SPANS.items():
            name = f'base_rail_mid_{level}_{side}'
            shape = previous.previous._service_cut(b.block(x0, x1, *span, 0., 139.7))
            result[name] = b.Part(name, shape, (x1-x0, 139.7, 38.1),
                'Independent square-cut nominal 2x6 seam rail; grain X; front service pockets; '
                'two end clips; no assumed load sharing with adjacent rail; '+LIMITS, 1)
    return tuple(result.values())


@cache
def connections():
    """Keep panel screws; assign each seam screw to its own independent rail."""
    result = list(hardware.clip_connections(stations()))
    service = [(x-b.HALF, s) for x, s in
               (*timber.grid.main_tnut_datums().values(), *timber.grid.main_led_datums().values())]
    shifts = (0., *[v for k in range(1, 81) for v in (k, -k)])
    tangent = (b.point(0., 1., 0.)-b.point(0., 0., 0.)).normalized()
    for c in previous.connections():
        if c.name.startswith('clip_'):
            continue
        if isinstance(c, timber.PanelScrew):
            panel, receiver = c.members
            start = c.start
            if receiver.startswith('base_rail_mid_'):
                level = 'lower' if 'lower' in panel else 'upper'
                side = 'left' if panel.endswith('left') else 'right'
                receiver = f'base_rail_mid_{level}_{side}'
                s = sum(SEAM_SPANS[level])/2
                _, x0, x1 = next(bay for bay in BAYS if bay[0] == side)
                x = next(start.x+d for d in shifts if x0+30. <= start.x+d <= x1-30. and
                         all(hypot(start.x+d-hx, s-hs) >= 28. for hx, hs in service))
                start = b.point(x, s, -wide.PANEL)
            elif receiver == 'base_post_center' and abs(start.z-160.) < 1e-6:
                start = cq.Vector(start.x, start.y, 140.)
            elif c.name == 'timber_panel_upper_right_2':
                start = start-tangent*5.
            c = replace(c, start=start, members=(panel, receiver),
                        product_status=timber.PanelScrew.product_status+'; fresh drilling; '+LIMITS)
        result.append(c)
    return tuple(result)


@cache
def parts():
    """Fresh occupied screw/bolt holes; future insert reservations stay solid."""
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
