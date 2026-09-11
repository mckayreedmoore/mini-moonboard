"""Fresh round-passage frame with 56 modeled insert/machine-screw attachments.

Preserves the source round frame and all structural connections. The display
cuts reserve insert bodies, not literal installation pilots or damaged wood.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import round_insert_hardware as insert_hardware
from . import round_service_frame as previous

KEY = 'round-insert-development'
LIMITS = insert_hardware.LIMITS
REFERENCE = insert_hardware.REFERENCE_PATH
INSERT, SCREW, PANEL = insert_hardware.INSERT, insert_hardware.SCREW, insert_hardware.PANEL
PanelMachineScrew = insert_hardware.PanelMachineScrew
b, base, hardware, timber, wide, leg = (previous.b, previous.base, previous.hardware,
                                      previous.timber, previous.wide, previous.leg)
HEADER_DEPTH, LOWER_S, BAYS = previous.HEADER_DEPTH, previous.LOWER_S, previous.BAYS
CENTER_SPLIT, ADDED_CENTERS = previous.CENTER_SPLIT, previous.ADDED_CENTERS
CENTERS, UPRIGHTS = previous.CENTERS, previous.UPRIGHTS
CENTER_CLEAR_GAP, CENTER_PANEL_OVERHANG = previous.CENTER_CLEAR_GAP, previous.CENTER_PANEL_OVERHANG
RAIL_SPANS, REMOVED_NAMES = previous.RAIL_SPANS, previous.REMOVED_NAMES
stations, bore_records = previous.stations, previous.bore_records
uncut_wood_parts = previous.uncut_wood_parts
wiring, electrical_parts = previous.wiring, previous.electrical_parts
bolt_points, bottom_bays = previous.bolt_points, previous.bottom_bays


@cache
def connections():
    return tuple(PanelMachineScrew(c.name, c.start, c.direction,
                    insert_hardware.SCREW['nominal_overall_length'],
                    insert_hardware.SCREW['nominal_thread_diameter'], c.members)
                 if isinstance(c, timber.PanelScrew) else c for c in previous.connections())


def panel_connections():
    return tuple(c for c in connections() if isinstance(c, PanelMachineScrew))


@cache
def wood_parts():
    """Round-bored timber before attachment machining; preserve parent API."""
    return tuple(replace(p, description=p.description+'; '+LIMITS) for p in previous.wood_parts())


@cache
def insert_parts():
    return tuple(b.Part('insert_'+c.name, c.insert_shape(),
                 (insert_hardware.INSERT['nominal_length'],
                  insert_hardware.INSERT['nominal_outer_diameter'],
                  insert_hardware.INSERT['nominal_outer_diameter']),
                 'Modeled zinc insert; simplified thread annulus; '+LIMITS, 1)
                 for c in panel_connections())


@cache
def parts():
    result = {p.name: p for p in wood_parts()}
    result.update({p.name: p for p in hardware.clip_parts(stations())})
    for c in connections():
        if isinstance(c, PanelMachineScrew):
            panel, receiver = c.members
            result[panel] = replace(result[panel], shape=result[panel].shape.cut(c.panel_cut()).clean())
            result[receiver] = replace(result[receiver], shape=result[receiver].shape.cut(c.receiver_cut()).clean())
            continue
        for index, name in enumerate(c.members):
            if name.startswith('clip_'):
                continue
            diameter = 11.1125 if c.kind == 'bolt' else c.diameter
            shape = result[name].shape.cut(cq.Solid.makeCylinder(diameter/2, c.length+2,
                c.start-c.direction, c.direction))
            if index == 0 and c.kind == 'screw':
                shape = shape.cut(c.components()[1])
            result[name] = replace(result[name], shape=shape.clean())
    result.update({p.name: p for p in insert_parts()})
    return tuple(result.values())
