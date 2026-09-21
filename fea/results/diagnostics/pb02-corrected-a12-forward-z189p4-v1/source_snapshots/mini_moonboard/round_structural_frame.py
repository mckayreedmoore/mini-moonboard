"""Structural panel screws on the latest rail layout, with future insert space.

The insert candidate supplies raw timber and attachment datums only. No insert
bodies or future insert reserve holes are cut in this screw-based candidate.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import round_insert_frame as layout
from . import round_service_frame as previous
from . import round_structural_wiring as wiring
from .round_panel_hardware import CountersunkPanelScrew

KEY = 'round-structural-development'
LIMITS = ('56 SPAX structural panel/kicker screws; future inserts optional and unqualified; '
          '38.1 mm LED passages in nominal 2x6 stock, 25.4 mm in other stock; '
          'frame, connections, residual sections and stability unqualified; NOT build-ready')
b, base, hardware, timber, wide, leg = (previous.b, previous.base, previous.hardware,
                                      previous.timber, previous.wide, previous.leg)
HEADER_DEPTH, LOWER_S, BAYS = previous.HEADER_DEPTH, previous.LOWER_S, previous.BAYS
CENTER_SPLIT, ADDED_CENTERS = previous.CENTER_SPLIT, previous.ADDED_CENTERS
CENTERS, UPRIGHTS = previous.CENTERS, previous.UPRIGHTS
CENTER_CLEAR_GAP, CENTER_PANEL_OVERHANG = previous.CENTER_CLEAR_GAP, previous.CENTER_PANEL_OVERHANG
RAIL_SPANS, SERVICE_S, REMOVED_NAMES = layout.RAIL_SPANS, layout.SERVICE_S, layout.REMOVED_NAMES
KICKER_ROWS = layout.KICKER_ROWS
LOWER_SERVICE_S, UPPER_SERVICE_S = layout.LOWER_SERVICE_S, layout.UPPER_SERVICE_S
bolt_points, bottom_bays = previous.bolt_points, previous.bottom_bays
stations, uncut_wood_parts = layout.stations, layout.uncut_wood_parts
# Spread the two interior columns equally around their existing midpoint.
# A 400 mm separation clears the enlarged routing bores on both mirrored faces.
INNER_COLUMN_GAP_MM = 400.
INNER_COLUMN_MIDPOINT_MM = sum(layout.historical_layout.INNER_X)/2
INNER_X = (INNER_COLUMN_MIDPOINT_MM-INNER_COLUMN_GAP_MM/2,
           INNER_COLUMN_MIDPOINT_MM+INNER_COLUMN_GAP_MM/2)
electrical_parts = wiring.parts


def attachment_datums():
    rows = []
    for original in layout.attachment_datums():
        row = dict(original)
        if row['role'] in ('edge', 'service'):
            sign = -1. if row['x'] < 0. else 1.
            row['x'] = sign*INNER_X[int(row['name'].rsplit('_', 1)[1])-1]
        rows.append(row)
    return tuple(rows)


@cache
def connections():
    """Retain specified structural screws and bolt stacks at revised stations."""
    old_panels = {c.name: c for c in previous.connections()
                  if isinstance(c, CountersunkPanelScrew)}
    datums = {row['name']: row for row in attachment_datums()}
    result = []
    for c in layout.connections():
        if isinstance(c, layout.PanelMachineScrew):
            x = datums[c.name]['x']
            c = replace(old_panels[c.name], start=c.start+cq.Vector(x-c.start.x, 0., 0.),
                        direction=c.direction)
        result.append(c)
    return tuple(result)


def panel_connections():
    return tuple(c for c in connections() if isinstance(c, CountersunkPanelScrew))


@cache
def bore_records():
    return wiring.bore_records(uncut_wood_parts())


@cache
def wood_parts():
    result = {p.name: replace(p, description=p.description+'; '+LIMITS)
              for p in uncut_wood_parts()}
    for record in bore_records():
        part = result[record['member']]
        result[part.name] = replace(part, shape=part.shape.cut(wiring.bore_shape(record)).clean(),
            description=part.description+f'; enclosed {record["diameter_mm"]:g} mm strand passage')
    return tuple(result.values())


@cache
def parts():
    """Cut occupied screw geometry only; future inserts require separate machining."""
    result = {p.name: p for p in wood_parts()}
    result.update({p.name: p for p in hardware.clip_parts(stations())})
    for c in connections():
        for index, name in enumerate(c.members):
            if name.startswith('clip_'):
                continue
            p = result[name]
            if index == 0 and isinstance(c, CountersunkPanelScrew):
                shaft, head = c.components()
                result[name] = replace(p, shape=p.shape.cut(shaft).cut(head).clean())
                continue
            diameter = 11.1125 if c.kind == 'bolt' else c.diameter
            shape = p.shape.cut(cq.Solid.makeCylinder(diameter/2, c.length+2,
                                                     c.start-c.direction, c.direction))
            if index == 0 and c.kind == 'screw':
                shape = shape.cut(c.components()[1])
            result[name] = replace(p, shape=shape.clean())
    return tuple(result.values())
