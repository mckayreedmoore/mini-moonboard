"""Development patch: ten extra kicker screws into the existing upper header.

The predecessor, independent panels and all vertical stock remain unchanged.
This geometry addresses a conditional pitch-equilibrium failure; actual panel,
head, header and connection resistance remain unqualified.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import round_structural_frame as previous

KEY = 'kicker-header-development'
LIMITS = ('Ten additional SPAX XFT08P-2000 kicker screws into the existing header; '
          'nine screws per independent kicker; conditional equilibrium revision only; '
          'actual head, panel, header, connections and floor unqualified; NOT build-ready')
ADDED_X_MAGNITUDES_MM = (200., 400., 600., 800., 1000.)
ADDED_ROW_Z_MM = 205.95


def __getattr__(name):
    """Preserve predecessor geometry APIs for this additive development variant."""
    return getattr(previous, name)


@cache
def added_datums():
    return tuple({'name': f'kicker_header_{side}_{index}', 'panel': 'kicker_'+side,
                  'receiver': 'base_header', 'role': 'kicker_header',
                  'x': sign*x, 's': ADDED_ROW_Z_MM}
                 for side, sign in (('left', -1.), ('right', 1.))
                 for index, x in enumerate(ADDED_X_MAGNITUDES_MM, 1))


@cache
def added_connections():
    """Retain the selected predecessor screw product and exact modeled head."""
    result = []
    templates = {side: next(c for c in previous.panel_connections()
                          if c.members[0] == 'kicker_'+side) for side in ('left', 'right')}
    for row in added_datums():
        side = row['panel'].rsplit('_', 1)[1]
        template = templates[side]
        result.append(replace(template, name=row['name'],
            start=cq.Vector(row['x'], template.start.y, row['s']),
            members=(row['panel'], row['receiver'])))
    return tuple(result)


def attachment_datums():
    return previous.attachment_datums()+added_datums()


def connections():
    return previous.connections()+added_connections()


def panel_connections():
    return previous.panel_connections()+added_connections()


def wood_parts():
    """Raw receiver geometry and existing passages are unchanged by this patch."""
    return previous.wood_parts()


def cut_added_connections(parts):
    """Apply only this patch to an existing candidate's already-cut part list.

    Reuses the predecessor's occupied screw/head geometry convention. These are
    not pilot-drilling instructions. Integration must check other new hardware.
    """
    result = {p.name: p for p in parts}
    required = {'base_header', 'kicker_left', 'kicker_right'}
    if not required <= result.keys():
        raise ValueError('Require header and both independent kicker parts')
    for c in added_connections():
        panel_name, receiver_name = c.members
        shaft, head = c.components()
        panel = result[panel_name]
        result[panel_name] = replace(panel,
            shape=panel.shape.cut(shaft).cut(head).clean())
        receiver = result[receiver_name]
        occupied = cq.Solid.makeCylinder(c.diameter/2, c.length+2,
                                         c.start-c.direction, c.direction)
        result[receiver_name] = replace(receiver,
            shape=receiver.shape.cut(occupied).clean())
    return tuple(replace(p, description=p.description+'; '+LIMITS)
                 if p.name in required else p for p in result.values())


@cache
def parts():
    return cut_added_connections(previous.parts())
