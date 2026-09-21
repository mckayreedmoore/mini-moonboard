"""Direct rim-to-header angles replace the two plywood base gussets.

The eight gusset bolts are omitted from fresh machining. Existing leg bolts,
panel screws, timber bearing cuts and support posts remain unchanged. Angle
geometry does not transfer the removed gussets' stiffness or resistance.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import infill_panel_frame as previous

b, base, hardware, timber, wide, leg = (previous.b, previous.base, previous.hardware,
                                      previous.timber, previous.wide, previous.leg)
KEY = 'angle-base-development'
HEADER_DEPTH, LOWER_S = previous.HEADER_DEPTH, previous.LOWER_S
CENTER_SPLIT, ADDED_CENTERS = previous.CENTER_SPLIT, previous.ADDED_CENTERS
UPRIGHTS, CENTERS, BAYS = previous.UPRIGHTS, previous.CENTERS, previous.BAYS
CENTER_CLEAR_GAP, CENTER_PANEL_OVERHANG = previous.CENTER_CLEAR_GAP, previous.CENTER_PANEL_OVERHANG
MAX_INTERVAL_MM = previous.MAX_INTERVAL_MM
LIMITS = ('Direct commercial ML24Z rim-to-header angles replace plywood gussets and their '
          'eight bolts; selected SDS25112 screws retained; geometry, local stiffness, '
          'connection resistance and global stability require verification; NOT build-ready')

bolt_points = previous.bolt_points
bottom_bays = previous.bottom_bays


@cache
def stations():
    result = list(previous.stations())
    for side, sign in (('left', -1.), ('right', 1.)):
        result.append((f'clip_angle_base_{side}', cq.Vector(sign*base.INNER_EDGE, -135., base.HEADER_TOP),
            cq.Vector(-sign, 0., 0.), cq.Vector(0., 0., 1.), 'base_header', f'base_side_{side}'))
    return tuple(result)


@cache
def wood_parts():
    """Undrilled receiver geometry; no gusset bodies or inherited gusset holes."""
    return tuple(replace(p, description=p.description.replace(previous.previous.LIMITS, LIMITS))
                 for p in previous.wood_parts() if not p.name.startswith('timber_base_gusset_'))


@cache
def connections():
    """Keep all existing non-gusset axes and add twelve specified angle screws."""
    result = [c for c in previous.connections()
              if not c.name.startswith(('timber_base_left_', 'timber_base_right_'))]
    result.extend(hardware.clip_connections(tuple(s for s in stations() if s[0].startswith('clip_angle_base_'))))
    return tuple(result)


@cache
def parts():
    """Machine the revised hardware set from raw wood, leaving old bolt axes solid."""
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
