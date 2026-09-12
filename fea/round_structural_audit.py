"""Structural-screw candidate fit and tip containment; no strength qualification."""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import cadquery as cq

from fea import horizontal_service_audit as previous_audit
from fea import paired_rail_audit as shared
from fea import screw_insert_repair_reserve as repair
from fea.split_center_audit import bearing_geometry, bolt_components
from fea.vertical_principal_audit import (
    aligned_supports,
    free_intervals,
    repair_reserves,
)
from mini_moonboard.connection_geometry import material_intervals


def sources():
    paths = set(previous_audit.sources()) | {
        'fea/round_service_audit.py', 'fea/round_structural_audit.py',
        'mini_moonboard/round_structural_frame.py', 'mini_moonboard/round_structural_wiring.py',
        'docs/round-service-wiring-reference.json',
        'docs/round-panel-countersink-reference.json'}
    # These consumers authenticate themselves; neither produces audited geometry.
    paths -= {'mini_moonboard/round_service_exports.py', 'mini_moonboard/round_service_drilling.py'}
    paths -= {f'mini_moonboard/round_insert_{name}.py'
              for name in ('exports', 'drilling')}
    paths -= {'mini_moonboard/round_structural_exports.py',
              'mini_moonboard/round_structural_drilling.py'}
    return {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(paths)}



def screw_tip_checks(raw, connections):
    """Trace every screw through its actual net receiver, beyond the screw tip.

    Receiver shapes include the LED passages but exclude the screw's own bore.
    The first receiver interval must continuously contain the tip; reaching a
    second interval after crossing a void is not accepted. Nominal geometry
    only: these distances do not include driving or manufacturing tolerances.
    """
    rows = []
    for connection in connections:
        if connection.kind != 'screw':
            continue
        receiver = connection.members[-1]
        if receiver not in raw:
            raise ValueError('Missing screw timber receiver: '+connection.name)
        shape = raw[receiver].shape
        axis = connection.direction.normalized()
        projections = [(v.Center()-connection.start).dot(axis) for v in shape.Vertices()]
        if not projections:
            raise ValueError('Receiver has no vertices: '+receiver)
        upper = max(max(projections), connection.length)+1.
        intervals = material_intervals(shape, connection.start, axis, 0., upper)
        entry, exit = intervals[0] if intervals else (None, None)
        margin = exit-connection.length if exit is not None else None
        passed = (entry is not None and entry < connection.length
                  and margin > 1.e-5)
        rows.append({'connection': connection.name, 'receiver': receiver,
                     'product_status': connection.product_status,
                     'screw_length_mm': connection.length,
                     'receiver_intervals_mm': intervals,
                     'receiver_entry_mm': entry, 'receiver_first_exit_mm': exit,
                     'gross_penetration_mm': connection.length-entry if entry is not None else None,
                     'tip_to_first_exit_mm': margin,
                     'passed': passed,
                     'limits': 'Nominal axial tip containment only; no tolerance, resistance or installation qualification.'})
    if len({row['connection'] for row in rows}) != len(rows):
        raise ValueError('Duplicate screw identity')
    return rows


def panel_layout_gate(screws):
    """Require every explicit shared datum, with twelve face/four kicker screws."""
    from collections import Counter

    from mini_moonboard import round_structural_frame as layout

    expected = {c.name: c for c in layout.panel_connections()}
    actual = {c.name: c for c in screws}
    missing, extra = sorted(expected.keys()-actual.keys()), sorted(actual.keys()-expected.keys())
    changed = [name for name in sorted(expected.keys() & actual.keys())
               if actual[name].members != expected[name].members
               or (actual[name].start-expected[name].start).Length > 1.e-7
               or (actual[name].direction-expected[name].direction).Length > 1.e-7
               or abs(actual[name].length-expected[name].length) > 1.e-7
               or abs(actual[name].diameter-expected[name].diameter) > 1.e-7]
    counts = dict(Counter(c.members[0] for c in screws))
    expected_counts = {f'main_{band}_{side}': 12 for band in ('lower', 'upper')
                       for side in ('left', 'right')}
    expected_counts.update({f'kicker_{side}': 4 for side in ('left', 'right')})
    from math import hypot

    rows = layout.attachment_datums()
    main = [r for r in rows if r['panel'].startswith('main_')]
    service = [(name, x-layout.b.HALF, station)
               for mapping in (layout.timber.grid.main_tnut_datums(),
                               layout.timber.grid.main_led_datums())
               for name, (x, station) in mapping.items()]
    nearest = min((hypot(row['x']-x, row['s']-station), row['name'], name)
                  for row in main for name, x, station in service)
    by_name = {row['name']: row for row in rows}
    mirror_failures = []
    for row in rows:
        if '_left_' not in row['name']:
            continue
        partner = by_name.get(row['name'].replace('_left_', '_right_'))
        if partner is None or abs(row['x']+partner['x']) > 1.e-7 or abs(row['s']-partner['s']) > 1.e-7:
            mirror_failures.append(row['name'])
    planar = {'minimum_service_axis_distance_mm': nearest[0],
              'service_clearance_witness': list(nearest[1:]),
              'required_service_axis_distance_mm': 28.,
              'service_axis_check_passed': nearest[0] >= 28.,
              'mirror_failures': mirror_failures,
              'mirrored_pairs': sum('_left_' in r['name'] for r in rows),
              'qualified_for_design': False}
    return {'passed': not (missing or extra or changed) and len(actual) == len(screws)
            and counts == expected_counts and planar['service_axis_check_passed']
            and not mirror_failures,
            'counts_by_panel': counts, 'missing': missing, 'extra': extra, 'changed': changed,
            'duplicate_names': len(actual) != len(screws), 'planar_checks': planar,
            'qualified_for_design': False}


def seam_support(model, raw):
    """Actual round-bored support at each independent panel's seam edge."""
    result = []
    for label, station in (('lower_panel_top', model.b.HALF-.001), ('upper_panel_bottom', model.b.HALF+.001)):
        backing = []
        for name, part in raw.items():
            if not name.startswith(('base_side_', 'base_principal_', 'base_rail_')):
                continue
            intervals = material_intervals(part.shape, model.b.point(0., station, .001), cq.Vector(1, 0, 0),
                                          -model.b.HALF, model.b.HALF)
            if intervals:
                backing.append({'member': name, 'backing_intervals_x_mm': intervals})
        gaps = free_intervals([interval for row in backing for interval in row['backing_intervals_x_mm']],
                              -model.b.HALF, model.b.HALF)
        result.append({'edge': label, 'station_s_mm': station, 'probe_depth_n_mm': .001,
                       'backing': backing, 'unsupported_intervals_x_mm': gaps,
                       'maximum_clear_span_mm': max((z-a for a, z in gaps), default=0.)})
    return result


def electrical_fit(model, drilled, connections):
    """Check provisional electrical envelopes against the actually machined assembly."""
    electrical = tuple(model.electrical_parts())
    names = [part.name for part in electrical]
    if len(names) != len(set(names)) or set(names) & drilled.keys():
        raise ValueError('Duplicate electrical identity')
    lights = [p for p in electrical if p.kind == 'light']
    wires = [p for p in electrical if p.kind == 'wire']
    if len(lights) != 132 or len(wires) != 131 or len(electrical) != len(lights)+len(wires):
        raise ValueError('Require 132 lights and 131 inter-light connections')
    hardware = [(c.name, shape) for c in connections for shape in c.components()]
    collisions = []
    segments = model.wiring.segments()
    endpoints = {row['name']: set(row['datums']) for row in segments}
    endpoints.update({p.name: {p.name.removeprefix('light_')} for p in lights})
    for part in electrical:
        if not part.shape.isValid() or part.shape.Volume() <= 0:
            raise ValueError('Invalid electrical envelope: '+part.name)
        for name, shape in [(n, p.shape) for n, p in drilled.items()]+hardware:
            if repair.overlaps(part.shape, shape):
                collisions.append({'electrical_part': part.name, 'assembly_part': name})
    for first, second in combinations(electrical, 2):
        if not endpoints[first.name] & endpoints[second.name] and repair.overlaps(first.shape, second.shape):
            collisions.append({'electrical_part': first.name, 'assembly_part': second.name})
    hold_collisions = []
    for datum, (x, station) in model.timber.grid.main_tnut_datums().items():
        reservation = cq.Solid.makeCylinder(model.timber.SERVICE_DIAMETER/2, model.timber.SERVICE_DEPTH,
            model.b.point(x-model.b.HALF, station, 0.), model.b.normal())
        for part in electrical:
            if repair.overlaps(part.shape, reservation):
                hold_collisions.append({'electrical_part': part.name, 'hold_datum': datum})
    bores = []
    uncut = {p.name: p for p in model.uncut_wood_parts()}
    origin, normal = model.b.point(0., 0., 0.), model.b.normal()
    records = model.bore_records()
    if len({r['name'] for r in records}) != len(records):
        raise ValueError('Duplicate round bore identity')
    for bore in records:
        tool = model.wiring.bore_shape(bore)
        remaining = tool.intersect(drilled[bore['member']].shape).Volume()
        removed = tool.intersect(uncut[bore['member']].shape).Volume()
        depths = [(v.Center()-origin).dot(normal) for v in uncut[bore['member']].shape.Vertices()]
        front = bore['center_n_mm']-bore['diameter_mm']/2-min(depths)
        rear = max(depths)-bore['center_n_mm']-bore['diameter_mm']/2
        row = {**bore, 'remaining_bore_volume_mm3': remaining, 'removed_timber_volume_mm3': removed,
               'front_ligament_mm': front, 'rear_ligament_mm': rear,
               'passed': remaining <= .01 and removed > .01 and min(front, rear) > 0.
                         and bore['diameter_mm'] == model.wiring.bore_diameter_mm(uncut[bore['member']])
                         and bore['diameter_mm'] > model.wiring.MEASURED_MAXIMUM_DIAMETER_MM}
        bores.append(row)
    return {'light_count': len(lights), 'wire_count': len(wires), 'collisions': collisions,
            'hold_service_collisions': hold_collisions,
            'round_bores': bores, 'segments': segments,
            'electrical_mass_included': False, 'electrical_qualified': False,
            'limits': 'Provisional body, cable and connector envelopes only. Adjacent electrical '
                      'parts intentionally meet; their mutual contact is not a collision failure. '
                      'Actual kit fit, strain relief, electrical operation, feeding access and bore residual-section strength remain unqualified.'}


def build():
    from mini_moonboard import horizontal_service_frame as previous
    from mini_moonboard import round_structural_frame as model

    hashes = sources()
    raw, drilled = ({p.name: p for p in parts} for parts in (model.wood_parts(), model.parts()))
    old_raw = {p.name: p for p in previous.wood_parts()}
    for name, part in (*raw.items(), *drilled.items()):
        if not part.shape.isValid() or len(part.shape.Solids()) != 1:
            raise ValueError('Require valid single-solid part: '+name)
    connections, stations = tuple(model.connections()), tuple(model.stations())
    screws = [c for c in connections if isinstance(c, model.timber.PanelScrew)]
    failures, receivers, holes, ledger = [], [], [], []
    layout_gate = panel_layout_gate(screws)
    if not layout_gate['passed']:
        failures.append({'gate': 'mirrored_twelve_per_face_layout', **layout_gate})
    for c in connections:
        if not set(c.members) <= drilled.keys() or len(set(c.members)) != len(c.members):
            raise ValueError('Invalid member ownership: '+c.name)
        ledger.append({'connection': c.name, 'kind': c.kind, 'members': list(c.members)})
        core = cq.Solid.makeCylinder(.25, c.length, c.start, c.direction)
        for name in c.members:
            blocked = core.intersect(drilled[name].shape).Volume()
            row = {'connection': c.name, 'member': name, 'blocked_core_volume_mm3': blocked, 'passed': blocked <= .01}
            holes.append(row)
            if not row['passed']:
                failures.append({'gate': 'blocked_drilled_axis', **row})
            if name not in raw:
                continue
            runs = material_intervals(raw[name].shape, c.start, c.direction, 0., c.length)
            length = sum(z-a for a, z in runs)
            required = (model.hardware.SDS['gross_penetration_through_nominal_ml24z'] if c.name.startswith('clip_') else
                        c.length-model.wide.PANEL if c in screws and name == c.members[1] else 0.)
            row = {'connection': c.name, 'member': name, 'raw_intervals_mm': runs,
                   'axial_material_mm': length, 'required_gross_material_mm': required,
                   'passed': len(runs) == 1 and length >= required-1e-5}
            receivers.append(row)
            if not row['passed']:
                failures.append({'gate': 'receiver_material', **row})
    tip_checks = screw_tip_checks(raw, connections)
    failures.extend({'gate': 'screw_tip_containment', **row}
                    for row in tip_checks if not row['passed'])
    body, between = shared.hardware_collisions(connections, drilled)
    wood = [{'members': [a.name, z.name]} for a, z in combinations(raw.values(), 2) if repair.overlaps(a.shape, z.shape)]
    brackets = [{'members': [a.name, z.name]} for a, z in combinations(drilled.values(), 2)
                if (a.name.startswith('clip_') or z.name.startswith('clip_')) and repair.overlaps(a.shape, z.shape)]
    for gate, rows in (('hardware_body_collision', body), ('distinct_fastener_collision', between),
                       ('wood_collision', wood), ('bracket_body_collision', brackets)):
        failures.extend({'gate': gate, **r} for r in rows)
    reserves = repair_reserves(raw, screws, connections)
    failures.extend({'gate': 'future_insert_reserve', 'connection': r['connection']}
                    for r in reserves['schedule'] if not r['passes_nominal_reserve'])
    reference = json.loads(shared.product.REFERENCE.read_text())
    product_rows, spacing, product_failures = shared.screw_product_geometry(raw, screws, reference['spax']['table_19_mm'])
    bearing, transfer = bearing_geometry(model, raw)
    failures.extend({'gate': 'header_bearing', **r} for r in bearing if not r['passes_full_bearing_geometry'])
    supports = aligned_supports(model, raw, stations)
    failures.extend({'gate': 'new_principal_support_path', **r} for r in supports if not r['passed'])
    new_members = [raw[r['principal']] for r in supports]
    if len(new_members) != 2 or any(sorted(p.blank[1:]) != [38.1, 139.7] or p.laminations != 1 for p in new_members):
        failures.append({'gate': 'two_independent_center_principals'})
    if 'base_principal_center' in raw or 'base_post_center' in raw:
        failures.append({'gate': 'old_center_member_removed'})
    if any(n.startswith('base_rail_mid_') for n in raw):
        failures.append({'gate': 'legacy_mid_rail_members_removed'})
    bracket_inventory = []
    for s in stations:
        cs = [c for c in connections if c.name.startswith(s[0]+'_')]
        counts = {name: sum(name in c.members for c in cs) for name in s[-2:]}
        row = {'bracket': s[0], 'receiver_screw_counts': counts,
               'passed': len(cs) == 6 and all(n == 3 for n in counts.values())}
        bracket_inventory.append(row)
        if not row['passed']:
            failures.append({'gate': 'bracket_screw_ownership', **row})
    bolts = bolt_components(connections)
    failures.extend({'gate': 'bolt_component_envelopes', **r} for r in bolts if not r['passed'])
    inward_bolts = []
    for c in connections:
        if c.kind != 'bolt':
            continue
        head, nut = c.components()[-2:]
        row = {'connection': c.name, 'head_center_x_mm': head.Center().x,
               'nut_center_x_mm': nut.Center().x,
               'passed': c.name.startswith('lumber_leg_bolt_') and abs(nut.Center().x) < abs(head.Center().x)}
        inward_bolts.append(row)
        if not row['passed']:
            failures.append({'gate': 'leg_bolt_nut_inward', **row})
    if len(inward_bolts) != 8:
        failures.append({'gate': 'eight_retained_leg_bolts'})
    seam_overhangs = [-raw['base_principal_center_left'].shape.BoundingBox().xmax,
                      raw['base_principal_center_right'].shape.BoundingBox().xmin]
    seam_previous, seam_current = seam_support(previous, old_raw), seam_support(model, raw)
    electrical = electrical_fit(model, drilled, connections)
    if len(electrical['round_bores']) != 32:
        failures.append({'gate': 'thirty_two_round_passages'})
    failures.extend({'gate': 'electrical_assembly_collision', **row} for row in electrical['collisions'])
    failures.extend({'gate': 'electrical_hold_service_collision', **row} for row in electrical['hold_service_collisions'])
    failures.extend({'gate': 'enclosed_round_service_bore', **row} for row in electrical['round_bores'] if not row['passed'])
    failures.extend({'gate': 'approximate_wire_path_budget', 'wire': row['name']}
                    for row in electrical['segments'] if not row['within_approximate_budget'])
    rails = [p for name, p in raw.items() if name.startswith('base_rail_service_')]
    if len(rails) != 4 or set(raw) & model.REMOVED_NAMES:
        failures.append({'gate': 'horizontal_service_replacement_inventory'})
    if sources() != hashes:
        raise ValueError('Audit source changed during build')
    return {'candidate': model.KEY, 'qualified_for_design': False, 'structural_analysis_run': False,
            'joint_strength_passed': False, 'floor_qualified': False,
            'limits': 'Fit and topology only. The lower panels\' top edges have discrete rim/principal backing. '
                      'The upper panels\' bottom edges also have service-rail backing across each bay, '
                      'with enclosed wiring bores behind the front face; the center corridor remains unsupported. '
                      'The two panel edges are independent: no seam tie, panel diaphragm, composite or load-sharing credit. '
                      'Replacing gussets with angle brackets does not establish equivalent stiffness or strength. Full support projection '
                      'does not determine contact pressure or connection capacity.',
            'inventory': {'wood_parts': len(raw), 'panel_kicker_screws': len(screws),
                          'bolts': sum(c.kind == 'bolt' for c in connections), 'brackets': len(stations),
                          'bracket_screws': sum(c.name.startswith('clip_') for c in connections),
                          'installed_inserts': 0, 'new_single_2x6_principals': [p.name for p in new_members],
                          'service_rails': [p.name for p in rails],
                          'lights': electrical['light_count'], 'wires': electrical['wire_count'],
                          'round_bores': len(electrical['round_bores']), 'front_open_wiring_grooves': 0,
                          'legacy_mid_rail_members': [n for n in raw if n.startswith('base_rail_mid_')],
                          'upper_panel_edge_rails': [n for n in raw if n.startswith('base_rail_service_upper_')]},
            'panel_layout_gate': layout_gate,
            'connection_ownership': ledger, 'bracket_screw_ownership': bracket_inventory,
            'receiver_checks': receivers, 'drilled_axis_checks': holes,
            'screw_tip_checks': tip_checks,
            'all_screw_tips_contained': bool(tip_checks) and all(r['passed'] for r in tip_checks),
            'hardware_body_collisions': body, 'distinct_fastener_collisions': between,
            'wood_collisions': wood, 'bracket_body_collisions': brackets,
            'future_insert_reserves': {**reserves, 'limits': repair.LIMITS}, 'panel_kicker_screws': product_rows,
            'screw_spacing': spacing, 'product_reference': reference,
            'header_support': bearing, 'new_principal_support_paths': supports,
            'header_transverse_transfer': transfer,
            'bolt_component_envelopes': bolts, 'inward_leg_bolt_checks': inward_bolts,
            'electrical_fit': electrical,
            'vertical_panel_seam': {'backing_edge_distances_left_right_mm': seam_overhangs,
                                    'panel_edges_supported_continuously': False,
                                    'strength_qualified': False,
                                    'limits': 'Each panel extends 50.95mm from its nearest center-principal edge to the seam; '
                                              'no seam tie, edge support or panel-strength pass is assumed.'},
            'horizontal_seam_comparison': {'previous': seam_previous, 'current': seam_current,
                'basis': 'Actual net backing along both seam edges at N=0.001mm; actual machined geometry included. '
                         'Enclosed round bores replace the preceding front-open wiring grooves. '
                         'Lower-panel top backing is discrete. Upper-panel bottom backing includes the '
                         'two service rails; the center corridor remains unsupported. '
                         'Listed clear spans are unsupported edge intervals, not capacity or seam coupling.'},
            'geometry_failures': failures, 'product_geometry_failures': product_failures,
            'all_tested_geometry_gates_passed': not failures,
            'all_tested_product_geometry_gates_passed': not product_failures, 'source_sha256': hashes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
