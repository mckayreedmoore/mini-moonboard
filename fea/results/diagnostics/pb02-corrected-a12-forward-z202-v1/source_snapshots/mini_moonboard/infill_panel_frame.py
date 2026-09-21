"""Infill existing interior-principal panel screw intervals to at most 150 mm.

All existing axes and raw wood are retained. The interval rule ends at the
existing first and last screws; it does not add edge or end connections and
does not establish strength or a permitted panel load.
"""
import itertools
from dataclasses import replace
from functools import cache
from math import ceil

import cadquery as cq

from . import split_center_frame as previous

b, base, hardware, timber, wide, leg = (previous.b, previous.base, previous.hardware,
                                      previous.timber, previous.wide, previous.leg)
KEY = 'infill-panel-development'
HEADER_DEPTH, LOWER_S = previous.HEADER_DEPTH, previous.LOWER_S
CENTER_SPLIT, ADDED_CENTERS = previous.CENTER_SPLIT, previous.ADDED_CENTERS
UPRIGHTS, CENTERS, BAYS = previous.UPRIGHTS, previous.CENTERS, previous.BAYS
CENTER_CLEAR_GAP, CENTER_PANEL_OVERHANG = previous.CENTER_CLEAR_GAP, previous.CENTER_PANEL_OVERHANG
MAX_INTERVAL_MM = 150.
LIMITS = ('Interior-principal panel screws infilled to at most 150 mm between existing '
          'endpoint screws; retained geometry and old axes; screw spacing, repair reserves, '
          'connection resistance and load qualification require verification; NOT build-ready')

bolt_points = previous.bolt_points
bottom_bays = previous.bottom_bays
stations = previous.stations
wood_parts = previous.wood_parts


@cache
def connections():
    """Subdivide intervals independently for each panel and interior receiver."""
    original = previous.connections()
    result = list(original)
    tangent = (b.point(0., 1., 0.)-b.point(0., 0., 0.)).normalized()
    groups = {}
    receivers = {f'base_principal_{suffix}' for suffix in ADDED_CENTERS}
    for c in original:
        if isinstance(c, timber.PanelScrew) and c.members[0].startswith('main_') and c.members[1] in receivers:
            groups.setdefault(c.members, []).append(c)
    for members, screws in sorted(groups.items()):
        ordered = sorted(screws, key=lambda c: c.start.dot(tangent))
        for interval, (first, last) in enumerate(itertools.pairwise(ordered), 1):
            delta = last.start-first.start
            segments = ceil(delta.dot(tangent)/MAX_INTERVAL_MM)
            for index in range(1, segments):
                result.append(replace(first,
                    name=f'infill_{members[0]}_{members[1]}_{interval}_{index}',
                    start=first.start+delta*(index/segments),
                    product_status=timber.PanelScrew.product_status+'; interval infill; '+LIMITS))
    return tuple(result)


@cache
def parts():
    """Cut the complete new connection set from unchanged raw panels and wood."""
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
