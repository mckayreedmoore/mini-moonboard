"""Lower the four bottom kicker screws on the selected trimmed assembly.

Fresh-stock geometry restores the former occupied screw envelopes. The frozen
native model and its load evidence remain unchanged; this local placement
revision retains the owner's accepted panel-construction basis.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import compact_spliced_trimmed as previous

KEY = previous.KEY
LOWER_KICKER_Z_MM = 60.
MOVED_NAMES = frozenset(f'round_kicker_{side}_{role}_1'
                        for side in ('left', 'right') for role in ('rim', 'center'))
CHANGED_NAMES = frozenset(('kicker_left', 'kicker_right',
    'base_post_outer_left', 'base_post_outer_right',
    'base_post_center_left', 'base_post_center_right'))
parameters = dict(previous.parameters, lower_kicker_screw_height_mm=LOWER_KICKER_Z_MM)


def __getattr__(name):
    return getattr(previous, name)


@cache
def connections():
    return tuple(replace(c, start=cq.Vector(c.start.x, c.start.y, LOWER_KICKER_Z_MM))
                 if c.name in MOVED_NAMES else c for c in previous.connections())


def panel_connections():
    return tuple(c for c in connections() if c.members[0].startswith(('main_', 'kicker_')))


def attachment_datums():
    return tuple({**row, 's': LOWER_KICKER_Z_MM} if row['name'] in MOVED_NAMES else dict(row)
                 for row in previous.attachment_datums())


@cache
def revised_parts():
    """Rebuild affected receivers/panels with retained service and hold openings.

    The uncut panel stock already contains the hold and LED openings. Cut all
    current occupied connection envelopes into that stock, rather than keeping
    the previous screw holes or filling over unrelated machining.
    """
    result = {p.name: p for p in previous.uncut_wood_parts() if p.name in CHANGED_NAMES}
    if result.keys() != CHANGED_NAMES:
        raise ValueError('Require both kicker panels and four posts')
    for name, _, cutter in previous.service_cutters():
        if name in result:
            result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for c in connections():
        for index, name in enumerate(c.members):
            if name not in result:
                continue
            part = result[name]
            if index == 0 and name.startswith('kicker_'):
                shaft, head = c.components()
                shape = part.shape.cut(shaft).cut(head)
            else:
                diameter = previous.bolt_dimensions(c)['hole_diameter_mm'] if c.kind == 'bolt' else c.diameter
                cutter = cq.Solid.makeCylinder(diameter/2, c.length+2., c.start-c.direction, c.direction)
                shape = part.shape.cut(cutter)
                if index == 0 and c.kind == 'screw':
                    shape = shape.cut(c.components()[1])
            result[name] = replace(part, shape=shape.clean())
    return tuple(result.values())


@cache
def parts():
    changed = {p.name: p for p in revised_parts()}
    return tuple(changed.get(p.name, p) for p in previous.parts())
