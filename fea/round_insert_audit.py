"""Audit assembled insert geometry without transferring screw qualification."""
import argparse
import hashlib
import json
from collections import Counter
from dataclasses import replace
from itertools import combinations
from pathlib import Path

import cadquery as cq

from fea.paired_rail_audit import hardware_collisions
from fea.round_service_audit import electrical_fit, seam_support
from fea.round_service_audit import sources as preceding_sources
from fea.screw_insert_repair_reserve import overlaps
from fea.split_center_audit import bearing_geometry, bolt_components
from mini_moonboard.connection_geometry import material_intervals


def sources():
    paths = set(preceding_sources()) | {'fea/round_insert_audit.py',
        'docs/round-insert-hardware-reference.json'}
    paths -= {'mini_moonboard/round_insert_exports.py',
              'mini_moonboard/round_insert_drilling.py'}
    return {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(paths)}


def layout_gate(connections):
    """Check named receiver ownership and the current candidate attachment axes."""
    from mini_moonboard import round_insert_frame as model

    expected = {}
    for row in model.attachment_datums():
        start = (model.b.point(row['x'], row['s'], -model.PANEL)
                 if row['panel'].startswith('main_') else
                 cq.Vector(row['x'], model.base.HEADER_FRONT_Y+model.PANEL, row['s']))
        direction = model.b.normal() if row['panel'].startswith('main_') else cq.Vector(0, -1, 0)
        expected[row['name']] = (row['panel'], row['receiver']), start, direction
    actual = {c.name: c for c in connections}
    changed = [name for name in expected.keys() & actual.keys()
               if expected[name][0] != actual[name].members
               or (expected[name][1]-actual[name].start).Length > 1.e-7
               or (expected[name][2]-actual[name].direction).Length > 1.e-7]
    counts = dict(Counter(c.members[0] for c in connections))
    expected_counts = dict(Counter(c[0][0] for c in expected.values()))
    return {'passed': actual.keys() == expected.keys() and not changed
            and len(actual) == len(connections) == 56 and counts == expected_counts,
            'changed_axes_or_members': sorted(changed),
            'missing': sorted(expected.keys()-actual.keys()),
            'extra': sorted(actual.keys()-expected.keys()), 'counts_by_panel': counts}


def insert_fit_metrics(expected, actual, receiver, envelope, reserve):
    """Compare the actual exported body and both full-solid cut reservations."""
    row = {'actual_insert_shape_mismatch_mm3': actual.cut(expected).Volume()+expected.cut(actual).Volume(),
           'actual_insert_outside_receiver_mm3': actual.cut(receiver).Volume(),
           'maximum_envelope_outside_receiver_mm3': envelope.cut(receiver).Volume(),
           'receiver_cut_outside_receiver_mm3': reserve.cut(receiver).Volume()}
    row['passed'] = all(value <= .01 for value in row.values())
    return row


def hold_reservations(model):
    """Explicit 40 mm access keepouts through panels and 45 mm behind them.

    These are service reservations, not dimensions of every installed hold.
    Extending through the plywood lets the screen detect head-seat conflicts.
    """
    radius, depth = model.timber.SERVICE_DIAMETER/2, model.timber.SERVICE_DEPTH+model.PANEL
    rows = [('main_'+name, cq.Solid.makeCylinder(radius, depth,
            model.b.point(x-model.b.HALF, station, -model.PANEL), model.b.normal()))
            for name, (x, station) in model.timber.grid.main_tnut_datums().items()]
    rows.extend(('kicker_'+name, cq.Solid.makeCylinder(radius, depth,
                cq.Vector(x-model.b.HALF, model.base.HEADER_FRONT_Y+model.PANEL,
                          model.b.V1_KICKER_HEIGHT_MM+z), cq.Vector(0., -1., 0.)))
                for name, (x, z) in model.timber.grid.kicker_foothold_datums().items())
    return rows


def tolerance_and_hold_checks(model, raw, drilled, panels, connections):
    components = [(c.name, index, shape) for c in connections
                  for index, shape in enumerate(c.components())]
    maximum = {c.name: c.maximum_insert_envelope() for c in panels}
    rows, collisions = [], []
    electrical = tuple(model.electrical_parts())
    for c in panels:
        name = 'insert_'+c.name
        actual = drilled[name].shape
        row = {'connection': c.name, 'receiver': c.members[1],
               **insert_fit_metrics(c.insert_shape(), actual, raw[c.members[1]].shape,
                                    maximum[c.name], c.receiver_cut())}
        rows.append(row)
        for role, tool in (('maximum_envelope', maximum[c.name]), ('receiver_cut', c.receiver_cut())):
            for other, index, shape in components:
                if other != c.name and overlaps(tool, shape):
                    collisions.append({'insert': name, 'envelope_role': role,
                                       'other_connection': other, 'component': index})
            for part in electrical:
                if overlaps(tool, part.shape):
                    collisions.append({'insert': name, 'envelope_role': role,
                                       'electrical_part': part.name})
        for other, part in drilled.items():
            if other not in (*c.members, name) and not other.startswith('insert_') and overlaps(maximum[c.name], part.shape):
                collisions.append({'insert': name, 'other_part': other})
    for first, second in combinations(panels, 2):
        if overlaps(maximum[first.name], maximum[second.name]):
            collisions.append({'insert': 'insert_'+first.name, 'other_insert': 'insert_'+second.name})
    # Bored raw containment above detects envelope/bores and stock-edge failures.
    # Keep explicit witnesses for the passage causing an interference.
    for c in panels:
        for bore in model.bore_records():
            if overlaps(maximum[c.name], model.wiring.bore_shape(bore)):
                collisions.append({'insert': 'insert_'+c.name, 'bore': bore['name']})
    keepouts = hold_reservations(model)
    if len(keepouts) != 142:
        raise ValueError('Require all 132 main and ten kicker hold reservations')
    checked = [(name, str(index), shape) for name, index, shape in components]
    checked += [('insert_'+c.name, 'actual', drilled['insert_'+c.name].shape) for c in panels]
    checked += [('insert_'+c.name, 'maximum_envelope', maximum[c.name]) for c in panels]
    checked += [('insert_'+c.name, 'receiver_cut', c.receiver_cut()) for c in panels]
    holds = [{'hardware': name, 'component': role, 'hold': hold}
             for name, role, shape in checked for hold, reservation in keepouts
             if overlaps(shape, reservation)]
    return rows, collisions, holds


def build():
    from mini_moonboard import round_insert_frame as model
    from mini_moonboard import round_service_frame as historical

    hashes = sources()
    raw = {p.name: p for p in model.wood_parts()}
    parts = tuple(model.parts())
    drilled = {p.name: p for p in parts}
    if len(parts) != len(drilled) or any(not p.shape.isValid()
            or len(p.shape.Solids()) != 1 for p in parts):
        raise ValueError('Require unique, valid single-solid model parts')
    connections = tuple(model.connections())
    panels = tuple(model.panel_connections())
    panel_names = {c.name for c in panels}
    inserts = {name: p for name, p in drilled.items() if name.startswith('insert_')}
    failures, holes, receiver_checks = [], [], []
    layout = layout_gate(panels)
    if not layout['passed']:
        failures.append({'gate': 'preserved_mirrored_layout', **layout})
    if set(inserts) != {'insert_'+name for name in panel_names}:
        failures.append({'gate': 'one_modeled_insert_per_panel_connection'})
    retained = {c.name: c for c in historical.connections() if c.name not in panel_names}
    # The four lower clips and both sets of their screws follow the moved rails.
    shift = model.b.point(0., model.LOWER_SERVICE_S, 0.)-model.b.point(
        0., sum(historical.RAIL_SPANS['lower'])/2, 0.)
    retained = {name: replace(c, start=c.start+shift)
                if name.startswith('clip_horizontal_lower_') else c
                for name, c in retained.items()}
    current_retained = {c.name: c for c in connections if c.name not in panel_names}
    changed = [name for name in retained.keys() & current_retained.keys()
               if retained[name] != current_retained[name]]
    if retained.keys() != current_retained.keys() or changed:
        failures.append({'gate': 'retained_structural_connections', 'changed': changed})
    for c in connections:
        if len(set(c.members)) != len(c.members) or not set(c.members) <= drilled.keys():
            raise ValueError('Invalid connection ownership: '+c.name)
        core = cq.Solid.makeCylinder(.25, c.length, c.start, c.direction)
        for name in c.members:
            blocked = core.intersect(drilled[name].shape).Volume()
            row = {'connection': c.name, 'member': name,
                   'blocked_core_volume_mm3': blocked, 'passed': blocked <= .01}
            holes.append(row)
            if not row['passed']:
                failures.append({'gate': 'drilled_axis', **row})
        if c.name in panel_names:
            shape = c.insert_shape()
            available = shape.intersect(raw[c.members[1]].shape).Volume()
            row = {'connection': c.name, 'receiver': c.members[1],
                   'insert_volume_mm3': shape.Volume(),
                   'insert_volume_inside_raw_receiver_mm3': available,
                   'passed': abs(shape.Volume()-available) <= .01,
                   'raw_axial_intervals_mm': material_intervals(
                       raw[c.members[1]].shape, c.start, c.direction, 0., c.length+20.)}
            receiver_checks.append(row)
            if not row['passed']:
                failures.append({'gate': 'insert_inside_receiver', **row})
    tolerance_rows, tolerance_collisions, hold_collisions = tolerance_and_hold_checks(
        model, raw, drilled, panels, connections)
    failures.extend({'gate': 'actual_insert_and_tolerance_containment', **row}
                    for row in tolerance_rows if not row['passed'])
    failures.extend({'gate': 'maximum_insert_envelope_collision', **row}
                    for row in tolerance_collisions)
    failures.extend({'gate': 'hardware_hold_service_collision', **row} for row in hold_collisions)
    body, between = hardware_collisions(connections, drilled)
    failures.extend({'gate': 'hardware_body_collision', **row} for row in body)
    failures.extend({'gate': 'distinct_fastener_collision', **row} for row in between)
    insert_collisions = []
    for name, insert in inserts.items():
        for other, part in drilled.items():
            if other == name or (other.startswith('insert_') and other < name):
                continue
            if overlaps(insert.shape, part.shape):
                insert_collisions.append({'insert': name, 'part': other})
    failures.extend({'gate': 'insert_body_collision', **row} for row in insert_collisions)
    wood_collisions = [{'members': [a.name, b.name]} for a, b in combinations(raw.values(), 2)
                       if overlaps(a.shape, b.shape)]
    failures.extend({'gate': 'wood_collision', **row} for row in wood_collisions)
    brackets = [p for p in drilled.values() if p.name.startswith('clip_')]
    bracket_collisions = [{'members': [a.name, b.name]}
                          for a in brackets for b in drilled.values()
                          if a.name != b.name and not b.name.startswith('insert_')
                          and (not b.name.startswith('clip_') or a.name < b.name)
                          and overlaps(a.shape, b.shape)]
    failures.extend({'gate': 'bracket_collision', **row} for row in bracket_collisions)
    electrical = electrical_fit(model, drilled, connections)
    failures.extend({'gate': 'electrical_collision', **row} for row in electrical['collisions'])
    failures.extend({'gate': 'electrical_hold_service_collision', **row}
                    for row in electrical['hold_service_collisions'])
    failures.extend({'gate': 'round_bore', **row} for row in electrical['round_bores'] if not row['passed'])
    if len(electrical['round_bores']) != 32:
        failures.append({'gate': 'thirty_two_round_bores'})
    bolts = bolt_components(connections)
    failures.extend({'gate': 'bolt_components', **row} for row in bolts if not row['passed'])
    inward = [{'connection': c.name,
               'passed': abs(c.components()[-1].Center().x) < abs(c.components()[-2].Center().x)}
              for c in connections if c.kind == 'bolt']
    if len(inward) != 8 or not all(row['passed'] for row in inward):
        failures.append({'gate': 'eight_inward_leg_nuts'})
    bearing, transfer = bearing_geometry(model, raw)
    failures.extend({'gate': 'header_support', **row} for row in bearing
                    if not row['passes_full_bearing_geometry'])
    if hashes != sources():
        raise ValueError('Sources changed during insert audit')
    return {'candidate': model.KEY, 'source_sha256': hashes,
            'qualified_for_design': False, 'joint_strength_passed': False,
            'floor_qualified': False, 'physical_tests_performed': False,
            'inventory': {'wood_parts': len(raw), 'panel_machine_screws': len(panels),
                          'modeled_inserts': len(inserts), 'bolts': len(inward),
                          'brackets': len(brackets),
                          'bracket_screws': sum(c.name.startswith('clip_') for c in connections),
                          'round_bores': len(electrical['round_bores']),
                          'lights': electrical['light_count'], 'wires': electrical['wire_count']},
            'layout_gate': layout, 'drilled_axis_checks': holes,
            'receiver_checks': receiver_checks, 'insert_body_collisions': insert_collisions,
            'insert_tolerance_checks': tolerance_rows, 'maximum_insert_envelope_collisions': tolerance_collisions,
            'hardware_hold_service_collisions': hold_collisions,
            'hold_reservation_count': 142,
            'recess_sensitivity': [model.insert_hardware.recess_sensitivity(recess)
                                  for recess in (0., .25, .5, .75, 1.)],
            'hardware_body_collisions': body, 'distinct_fastener_collisions': between,
            'wood_collisions': wood_collisions, 'bracket_body_collisions': bracket_collisions,
            'electrical_fit': electrical, 'bolt_component_envelopes': bolts,
            'inward_leg_bolt_checks': inward, 'header_support': bearing,
            'header_transverse_transfer': transfer, 'seam_support': seam_support(model, raw),
            'geometry_failures': failures, 'all_tested_geometry_gates_passed': not failures,
            'product_strength_or_installation_qualified': False,
            'limits': 'Assembled nominal CAD and explicit clearance reservations only. '
                      'No installed hardware or full internal thread engagement is established. '
                      'SPAX spacing and strength references do not qualify wood inserts. '
                      'Display receiver cuts are occupied-envelope reservations, not pilot holes. '
                      'Historical seam ties, composite action and strength acceptance are not inherited.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
