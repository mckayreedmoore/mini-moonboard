"""Current horizontal-service fit inventory; no inherited structural qualification."""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import cadquery as cq

from fea import angle_base_audit as previous_audit
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
    paths = set(previous_audit.sources()) | {'fea/horizontal_service_audit.py', 'docs/led-wiring-reference.json'}
    # These consumers authenticate themselves; neither produces audited geometry.
    paths -= {'mini_moonboard/horizontal_service_exports.py', 'mini_moonboard/horizontal_service_drilling.py'}
    return {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(paths)}


def seam_support(model, raw):
    """Actual groove-cut support at each independent panel's seam edge."""
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
    cutouts = []
    for cut in model.wiring.cutout_records(model.uncut_wood_parts()):
        remaining = model.wiring.cutout_shape(cut).intersect(drilled[cut['member']].shape).Volume()
        row = {**cut, 'remaining_cutout_volume_mm3': remaining,
               'passed': cut['entry_face'].startswith('front N=0') and remaining <= .01}
        cutouts.append(row)
    return {'light_count': len(lights), 'wire_count': len(wires), 'collisions': collisions,
            'hold_service_collisions': hold_collisions,
            'front_cutouts': cutouts, 'segments': segments,
            'electrical_mass_included': False, 'electrical_qualified': False,
            'limits': 'Provisional body, cable and connector envelopes only. Adjacent electrical '
                      'parts intentionally meet; their mutual contact is not a collision failure. '
                      'Actual kit fit, strain relief, electrical operation and groove strength remain unqualified.'}


def build():
    from mini_moonboard import angle_base_frame as previous
    from mini_moonboard import horizontal_service_frame as model

    hashes = sources()
    raw, drilled = ({p.name: p for p in parts} for parts in (model.wood_parts(), model.parts()))
    old_raw = {p.name: p for p in previous.wood_parts()}
    for name, part in (*raw.items(), *drilled.items()):
        if not part.shape.isValid() or len(part.shape.Solids()) != 1:
            raise ValueError('Require valid single-solid part: '+name)
    connections, stations = tuple(model.connections()), tuple(model.stations())
    screws = [c for c in connections if isinstance(c, model.timber.PanelScrew)]
    failures, receivers, holes, ledger = [], [], [], []
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
    seam_overhangs = [-raw['base_principal_center_left'].shape.BoundingBox().xmax,
                      raw['base_principal_center_right'].shape.BoundingBox().xmin]
    seam_previous, seam_current = seam_support(previous, old_raw), seam_support(model, raw)
    electrical = electrical_fit(model, drilled, connections)
    failures.extend({'gate': 'electrical_assembly_collision', **row} for row in electrical['collisions'])
    failures.extend({'gate': 'electrical_hold_service_collision', **row} for row in electrical['hold_service_collisions'])
    failures.extend({'gate': 'front_service_cutout', **row} for row in electrical['front_cutouts'] if not row['passed'])
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
                      'interrupted by front wiring grooves; the center corridor remains unsupported. '
                      'The two panel edges are independent: no seam tie, panel diaphragm, composite or load-sharing credit. '
                      'Replacing gussets with angle brackets does not establish equivalent stiffness or strength. Full support projection '
                      'does not determine contact pressure or connection capacity.',
            'inventory': {'wood_parts': len(raw), 'panel_kicker_screws': len(screws),
                          'bolts': sum(c.kind == 'bolt' for c in connections), 'brackets': len(stations),
                          'bracket_screws': sum(c.name.startswith('clip_') for c in connections),
                          'installed_inserts': 0, 'new_single_2x6_principals': [p.name for p in new_members],
                          'service_rails': [p.name for p in rails],
                          'lights': electrical['light_count'], 'wires': electrical['wire_count'],
                          'legacy_mid_rail_members': [n for n in raw if n.startswith('base_rail_mid_')],
                          'upper_panel_edge_rails': [n for n in raw if n.startswith('base_rail_service_upper_')]},
            'connection_ownership': ledger, 'bracket_screw_ownership': bracket_inventory,
            'receiver_checks': receivers, 'drilled_axis_checks': holes,
            'hardware_body_collisions': body, 'distinct_fastener_collisions': between,
            'wood_collisions': wood, 'bracket_body_collisions': brackets,
            'future_insert_reserves': reserves, 'panel_kicker_screws': product_rows,
            'screw_spacing': spacing, 'product_reference': reference,
            'header_support': bearing, 'new_principal_support_paths': supports,
            'header_transverse_transfer': transfer,
            'bolt_component_envelopes': bolts,
            'electrical_fit': electrical,
            'vertical_panel_seam': {'backing_edge_distances_left_right_mm': seam_overhangs,
                                    'panel_edges_supported_continuously': False,
                                    'strength_qualified': False,
                                    'limits': 'Each panel extends 50.95mm from its nearest center-principal edge to the seam; '
                                              'no seam tie, edge support or panel-strength pass is assumed.'},
            'horizontal_seam_comparison': {'previous': seam_previous, 'current': seam_current,
                'basis': 'Actual net backing along both seam edges at N=0.001mm; service-pocket gaps included. '
                         'Horizontal service rails replace intermediate principal supports. '
                         'Lower-panel top backing is discrete. Upper-panel bottom backing includes the '
                         'two service rails with groove interruptions; the center corridor remains unsupported. '
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
