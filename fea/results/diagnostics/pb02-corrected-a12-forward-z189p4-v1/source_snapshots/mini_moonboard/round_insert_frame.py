"""Fresh round-passage frame with 56 modeled insert/machine-screw attachments.

Revises service rail and kicker attachment heights independently of the
historical screw frame. The display cuts reserve insert bodies, not literal
installation pilots or damaged wood.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import round_insert_hardware as insert_hardware
from . import round_panel_layout as historical_layout
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
LOWER_SERVICE_S = historical_layout.FACE_ROWS[-1]
UPPER_SERVICE_S = historical_layout.HALF+historical_layout.FACE_ROWS[0]
SERVICE_S = {'lower': LOWER_SERVICE_S, 'upper': UPPER_SERVICE_S}
RAIL_SPANS = {level: (s-19.05, s+19.05) for level, s in SERVICE_S.items()}
REMOVED_NAMES = previous.REMOVED_NAMES
KICKER_ROWS = (60., 140.)
wiring, electrical_parts = previous.wiring, previous.electrical_parts
bolt_points, bottom_bays = previous.bolt_points, previous.bottom_bays


def rail_translation(level):
    return b.point(0., SERVICE_S[level], 0.)-b.point(0., sum(previous.RAIL_SPANS[level])/2, 0.)


def lower_rail_translation():
    return rail_translation('lower')


def attachment_datums():
    """Candidate attachment positions; historical row dictionaries stay untouched."""
    rows = []
    for original in historical_layout.datums():
        row = dict(original)
        if row['receiver'].startswith('base_rail_service_'):
            row['s'] = SERVICE_S[row['receiver'].split('_')[-2]]
        elif row['panel'].startswith('kicker_'):
            row['s'] = KICKER_ROWS[int(row['name'].rsplit('_', 1)[1])-1]
        rows.append(row)
    return tuple(rows)


@cache
def stations():
    return tuple((name, origin+rail_translation(beam.split('_')[-2]), u, v, beam, upright)
                 if beam.startswith('base_rail_service_')
                 else (name, origin, u, v, beam, upright)
                 for name, origin, u, v, beam, upright in previous.stations())


@cache
def uncut_wood_parts():
    return tuple(replace(p, shape=p.shape.translate(rail_translation(p.name.split('_')[-2])))
                 if p.name.startswith('base_rail_service_') else p
                 for p in previous.uncut_wood_parts())


@cache
def bore_records():
    return wiring.bore_records(uncut_wood_parts())


@cache
def connections():
    datums = {row['name']: row for row in attachment_datums()}
    result = []
    for c in previous.connections():
        if isinstance(c, timber.PanelScrew):
            row = datums[c.name]
            start = (b.point(row['x'], row['s'], -wide.PANEL)
                     if row['panel'].startswith('main_') else
                     cq.Vector(row['x'], base.HEADER_FRONT_Y+wide.PANEL, row['s']))
            c = PanelMachineScrew(c.name, start, c.direction,
                insert_hardware.SCREW['nominal_overall_length'],
                insert_hardware.SCREW['nominal_thread_diameter'], c.members)
        elif c.name.startswith(('clip_horizontal_lower_', 'clip_horizontal_upper_')):
            c = replace(c, start=c.start+rail_translation(c.name.split('_')[2]))
        result.append(c)
    return tuple(result)


def panel_connections():
    return tuple(c for c in connections() if isinstance(c, PanelMachineScrew))


@cache
def wood_parts():
    """Recompute passages in moved raw timber before attachment machining."""
    result = {p.name: replace(p, description=p.description+'; '+LIMITS)
              for p in uncut_wood_parts()}
    for record in bore_records():
        part = result[record['member']]
        result[part.name] = replace(part, shape=part.shape.cut(wiring.bore_shape(record)).clean(),
            description=part.description+'; enclosed round strand passage, provisional diameter')
    return tuple(result.values())


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
