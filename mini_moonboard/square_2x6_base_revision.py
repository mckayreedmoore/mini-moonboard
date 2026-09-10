"""Base fit revision of the preserved single-2x6 development candidate.

The flat header remains one nominal 2x6. Front 2x6 posts, square
principals, panel screws and their future repair reserves remain unchanged.
The retained shallow header still fails full bearing; no structural approval.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import base_frame as base
from . import box_frame as b
from . import square_2x6_frame as previous
from . import timber_connections as hardware

HEADER_DEPTH = 139.7  # Keep the first revised candidate entirely single 2x6 stock.
POST_DEPTH = 139.7
REMOVED_NAMES = tuple(f'base_post_center_{side}_rear' for side in ('left', 'right'))
LIMITS = ('Geometric fit revision only; header bending, post load distribution, '
          'fastener resistance and floor stability unqualified; NOT build-ready')


@cache
def base_parts():
    """Wood replacements; callers separately remove REMOVED_NAMES."""
    name = 'base_header'
    return {name: b.Part(name, base._world_box(-b.HALF, b.HALF,
        base.HEADER_FRONT_Y-HEADER_DEPTH, base.HEADER_FRONT_Y,
        base.HEADER_BOTTOM, base.HEADER_TOP), (2*b.HALF, HEADER_DEPTH, 38.1),
        'Single nominal 2x6 flat header; grain X; 2x6 sloped bearing footprint '
        'requires 187.863 mm depth from retained kicker datum, exceeding the '
        '139.7 mm retained header; incomplete bearing deliberately preserved; '+LIMITS, 1)}


@cache
def base_stations():
    """Four header retention clips centered on the remaining 2x6 posts."""
    result = []
    for name, origin, u, v, beam, upright in hardware.stations(True):
        if 'header_' not in name:
            continue
        if 'center_' in name:
            upright += '_front'
        result.append((name, cq.Vector(origin.x, base.HEADER_FRONT_Y-POST_DEPTH/2,
                                       origin.z), u, v, beam, upright))
    return tuple(result)


@cache
def base_connections():
    """Replace both outer-post gusset bolt axes; retain selected bolt product."""
    replacements = {}
    for c in previous.connections():
        if c.name not in tuple(f'timber_base_{side}_{index}'
                               for side in ('left', 'right') for index in (3, 4)):
            continue
        fraction = .3 if c.name.endswith('_3') else .7
        replacements[c.name] = replace(c, start=cq.Vector(c.start.x,
            base.HEADER_FRONT_Y-POST_DEPTH*fraction, c.start.z))
    return replacements
