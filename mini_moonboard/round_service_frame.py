"""Enclosed round wiring passages in the horizontal-service timber candidate.

Lights are installed after the panels. Historical front-open channels remain
preserved in their own variant; this model starts from uncut receiver timber.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import horizontal_service_frame as previous
from . import round_service_wiring as wiring
from .bolted_frame import WASHER
from .round_panel_hardware import CountersunkPanelScrew, with_countersunk_head
from .round_panel_layout import panel_connections

b, base, hardware, timber, wide, leg = (previous.b, previous.base, previous.hardware,
                                      previous.timber, previous.wide, previous.leg)
KEY = 'round-bore-service-development'
HEADER_DEPTH, LOWER_S, BAYS = previous.HEADER_DEPTH, previous.LOWER_S, previous.BAYS
CENTER_SPLIT, ADDED_CENTERS = previous.CENTER_SPLIT, previous.ADDED_CENTERS
CENTERS, UPRIGHTS = previous.CENTERS, previous.UPRIGHTS
CENTER_CLEAR_GAP, CENTER_PANEL_OVERHANG = previous.CENTER_CLEAR_GAP, previous.CENTER_PANEL_OVERHANG
RAIL_SPANS, REMOVED_NAMES = previous.RAIL_SPANS, previous.REMOVED_NAMES
LIMITS = ('Enclosed provisional 25.4 mm round strand passages; measured maximum harness '
          'diameter 12.7 mm; lights installed after panels; feeding access, bore residual '
          'sections, connections and stability unqualified; NOT build-ready')

bolt_points = previous.bolt_points
bottom_bays = previous.bottom_bays
stations = previous.stations
uncut_wood_parts = previous.uncut_wood_parts
electrical_parts = wiring.parts


@cache
def connections():
    """Use mirrored panel axes and face retained leg-bolt nuts inward."""
    result = []
    for c in previous.connections():
        if isinstance(c, timber.PanelScrew):
            continue
        if c.name.startswith('lumber_leg_bolt_'):
            c = replace(c, start=c.start+c.direction*(c.grip+2*WASHER), direction=-c.direction,
                product_status=c.product_status+'; head outside, nut inside; two washers retained')
        result.append(with_countersunk_head(c))
    result.extend(with_countersunk_head(c) for c in panel_connections())
    return tuple(result)


@cache
def bore_records():
    return wiring.bore_records(uncut_wood_parts())


@cache
def wood_parts():
    result = {p.name: replace(p, description=p.description.replace(previous.LIMITS, LIMITS))
              for p in uncut_wood_parts()}
    for record in bore_records():
        part = result[record['member']]
        result[part.name] = replace(part, shape=part.shape.cut(wiring.bore_shape(record)).clean(),
            description=part.description+'; enclosed round strand passage, provisional diameter')
    return tuple(result.values())


@cache
def parts():
    """Fresh hardware drilling after round passages; no historical groove cuts."""
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
