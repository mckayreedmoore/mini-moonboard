"""Paired-rail/base-connection fit and product geometry, never strength approval."""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import cadquery as cq

from fea import selective_connection_strength as product
from fea.screw_insert_repair_reserve import assess as repair_assess
from fea.screw_insert_repair_reserve import overlaps
from mini_moonboard.connection_geometry import material_intervals


def hardware_collisions(connections, drilled):
    """Only own screw threads and own fastener component overlaps are exempt."""
    components = {c.name: tuple(c.components()) for c in connections}
    if len(components) != len(connections):
        raise ValueError('Duplicate fastener identity')
    body, between = [], []
    for c in connections:
        if not set(c.members) <= drilled.keys():
            raise ValueError('Unknown connection member: '+c.name)
        for index, shape in enumerate(components[c.name]):
            if not shape.isValid():
                raise ValueError('Invalid hardware component: '+c.name)
            for name, part in drilled.items():
                if index == 0 and c.kind == 'screw' and name in c.members:
                    continue
                if overlaps(shape, part.shape):
                    body.append({'connection': c.name, 'component': index, 'member': name})
    for (name, shapes), (other, others) in combinations(components.items(), 2):
        for i, a in enumerate(shapes):
            for j, z in enumerate(others):
                if overlaps(a, z):
                    between.append({'connections': [name, other], 'components': [i, j]})
    return body, between


def screw_product_geometry(raw, screws, distances):
    rows, failures = [], []
    for c in screws:
        receiver = c.members[1]
        shape = raw[receiver].shape
        grain, across = product.receiver_axes(receiver)
        runs = material_intervals(shape, c.start, c.direction, 0., c.length)
        if len(runs) != 1:
            failures.append({'gate': 'continuous_screw_receiver', 'connection': c.name,
                             'raw_intervals_mm': runs})
            continue
        entry = c.start+c.direction*(runs[0][0]+.001)
        ends, grain_runs = product.boundary_distances(shape, entry, grain)
        edges, edge_runs = product.boundary_distances(shape, entry, across)
        row = {'connection': c.name, 'receiver': receiver,
               'grain_xyz': list(grain.toTuple()), 'entry_section_offset_mm': .001,
               'end_distances_mm': ends, 'edge_distances_mm': edges,
               'gross_penetration_mm': runs[0][1]-runs[0][0],
               'entry_section_grain_material_runs_mm': grain_runs,
               'entry_section_cross_material_runs_mm': edge_runs,
               'passes_end_away_or_perpendicular': min(ends) >= distances['end_away_or_perpendicular']-1e-5,
               'passes_reversible_end': min(ends) >= distances['end_toward']-1e-5,
               'passes_edge': min(edges) >= distances['edge_any_direction']-1e-5}
        rows.append(row)
        for gate in ('passes_end_away_or_perpendicular', 'passes_reversible_end', 'passes_edge'):
            if not row[gate]:
                failures.append({'gate': gate, 'connection': c.name, 'receiver': receiver})
    spacing = product.spacing_checks(screws, distances)
    failures.extend({'gate': 'screw_spacing', **r} for r in spacing if not r['passed'])
    return rows, spacing, failures


def bearing_geometry(model, raw):
    """Nominal contact coverage and unresolved transverse support transfer."""
    header = raw['base_header'].shape
    eps = .01
    slab = model.base._world_box(-2000., 2000., -2000., 4000.,
                                 model.base.HEADER_TOP, model.base.HEADER_TOP+eps)
    rows = []
    for name, p in raw.items():
        if name.startswith(('base_side_', 'base_principal_')):
            full = p.shape.intersect(slab).Volume()
            supported = p.shape.intersect(header.translate((0, 0, eps))).Volume()
        elif name.startswith('base_post_'):
            bounds = p.shape.BoundingBox()
            full = bounds.xlen*bounds.ylen*eps
            supported = p.shape.translate((0, 0, eps)).intersect(header).Volume()
        else:
            continue
        if full <= 0:
            raise ValueError('Missing nominal bearing face: '+name)
        fraction = supported/full
        rows.append({'member': name, 'gap_mm': p.shape.distance(header),
                     'nominal_contact_area_fraction': fraction,
                     'passes_full_bearing_geometry': fraction >= 1-1e-5})
    principal = raw['base_principal_center'].shape
    faces = [f for f in principal.Faces() if f.BoundingBox().zlen < 1e-6 and
             abs(f.Center().z-model.base.HEADER_TOP) < 1e-6]
    if not faces:
        raise ValueError('Missing principal horizontal bearing face')
    rear = min(f.BoundingBox().ymin for f in faces)
    post_rear = raw['base_post_center'].shape.BoundingBox().ymin
    return rows, {'principal_bearing_rear_y_mm': rear, 'post_rear_y_mm': post_rear,
                  'principal_footprint_beyond_post_mm': max(0., post_rear-rear),
                  'header_rear_overhang_beyond_post_mm': max(0., post_rear-header.BoundingBox().ymin),
                  'strength_assessed': False,
                  'status': 'Unresolved cross-grain header bending/shear and contact load distribution; '
                            'a retention bracket does not create vertical support beneath this footprint.'}


def sources():
    paths = {*Path('mini_moonboard').glob('*.py'), Path(__file__), product.REFERENCE,
             *map(Path, ('fea/selective_connection_strength.py', 'fea/screw_insert_repair_reserve.py',
                         'fea/single_2x6_screen.py', 'fea/lumber_leg_resistance.py',
                         'fea/dowel_yield.py', 'fea/leg_stock_screen.py',
                         'docs/selective-stock-reference.json', 'docs/ml24z-reference.json',
                         'docs/panel-insert-reference.json', 'uv.lock'))}
    root = Path.cwd()
    return {str(p.resolve().relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def build():
    from mini_moonboard import paired_rail_frame as model

    hashes = sources()
    raw = {p.name: p for p in model.wood_parts()}
    drilled = {p.name: p for p in model.parts()}
    for name, part in (*raw.items(), *drilled.items()):
        if not part.shape.isValid() or len(part.shape.Solids()) != 1:
            raise ValueError('Require valid single-solid part: '+name)
    connections = tuple(model.connections())
    screws = [c for c in connections if isinstance(c, model.timber.PanelScrew)]
    if len(screws) != 56:
        raise ValueError('Expected all 56 panel/kicker screws')
    failures, receivers, pilot_checks = [], [], []
    for c in connections:
        for name in c.members:
            if name not in raw:
                continue
            runs = material_intervals(raw[name].shape, c.start, c.direction, 0., c.length)
            length = sum(z-a for a, z in runs)
            required = (model.hardware.SDS['gross_penetration_through_nominal_ml24z']
                        if c.name.startswith('clip_') else
                        c.length-model.wide.PANEL if c in screws and name == c.members[1] else 0.)
            row = {'connection': c.name, 'member': name, 'raw_intervals_mm': runs,
                   'axial_material_mm': length, 'required_gross_material_mm': required,
                   'passed': bool(runs) and length >= required-1e-5}
            receivers.append(row)
            if not row['passed']:
                failures.append({'gate': 'receiver_material', **row})
            # Every occupied axis must remain open after drilling, including new
            # header screws. A narrow core avoids treating threads as a blockage.
            core = cq.Solid.makeCylinder(.25, c.length, c.start, c.direction)
            volume = core.intersect(drilled[name].shape).Volume()
            pilot = {'connection': c.name, 'member': name, 'blocked_core_volume_mm3': volume,
                     'passed': volume <= .01}
            pilot_checks.append(pilot)
            if not pilot['passed']:
                failures.append({'gate': 'blocked_drilled_axis', **pilot})
    body, between = hardware_collisions(connections, drilled)
    failures.extend({'gate': 'hardware_body_collision', **r} for r in body)
    failures.extend({'gate': 'distinct_fastener_collision', **r} for r in between)
    wood_collisions = [{'members': [a.name, z.name]} for a, z in combinations(raw.values(), 2)
                       if overlaps(a.shape, z.shape)]
    failures.extend({'gate': 'wood_collision', **r} for r in wood_collisions)
    bracket_collisions = [{'members': [a.name, z.name]}
                          for a, z in combinations(drilled.values(), 2)
                          if (a.name.startswith('clip_') or z.name.startswith('clip_'))
                          and overlaps(a.shape, z.shape)]
    failures.extend({'gate': 'bracket_body_collision', **r} for r in bracket_collisions)
    reserve = repair_assess(raw, connections)
    failures.extend({'gate': 'future_insert_reserve', 'connection': r['connection']}
                    for r in reserve['schedule'] if not r['passes_nominal_reserve'])
    reference = json.loads(product.REFERENCE.read_text())
    product_rows, spacing, product_failures = screw_product_geometry(raw, screws, reference['spax']['table_19_mm'])
    support, transfer = bearing_geometry(model, raw)
    failures.extend({'gate': 'header_bearing', **r} for r in support if not r['passes_full_bearing_geometry'])
    stations = tuple(model.stations())
    center = [s for s in stations if s[0] == 'clip_paired_base_center']
    direct = len(center) == 1 and set(center[0][-2:]) == {'base_header', 'base_principal_center'}
    retained = any(set(s[-2:]) == {'base_header', 'base_post_center'} for s in stations)
    base_screws = [c for c in connections if c.name.startswith('clip_paired_base_center_')]
    connected = direct and retained and len(base_screws) == 6
    if not connected:
        failures.append({'gate': 'explicit_principal_header_post_bracket_path'})
    rails = [p for n, p in raw.items() if n.startswith('base_rail_mid_')]
    rail_inventory_ok = len(rails) == 4 and all(sorted(p.blank[1:]) == [38.1, 139.7] and p.laminations == 1 for p in rails)
    if not rail_inventory_ok:
        failures.append({'gate': 'four_independent_2x6_seam_rails'})
    if sources() != hashes:
        raise ValueError('Audit source changed during build')
    return {'candidate': model.KEY, 'qualified_for_design': False, 'structural_analysis_run': False,
            'joint_strength_passed': False, 'floor_qualified': False,
            'status': 'Raw and drilled geometric/product checks only; no structural acceptance',
            'limits': 'No transferred loads or capacities. Paired rails remain independent single members; '
                      'no composite action, load-sharing or paired capacity sum is credited. Bracket presence '
                      'does not qualify mixed-axis resistance or cross-grain header load transfer. Screw '
                      'entry-section product distances do not qualify splitting or service-pocket net sections.',
            'inventory': {'wood_parts': len(raw), 'panel_kicker_screws': len(screws),
                          'bolts': sum(c.kind == 'bolt' for c in connections), 'brackets': len(stations),
                          'bracket_screws': sum(c.name.startswith('clip_') for c in connections),
                          'installed_inserts': 0, 'independent_paired_rails': [p.name for p in rails]},
            'receiver_checks': receivers, 'drilled_axis_checks': pilot_checks,
            'hardware_body_collisions': body, 'distinct_fastener_collisions': between,
            'wood_collisions': wood_collisions, 'bracket_body_collisions': bracket_collisions,
            'future_insert_reserves': reserve,
            'header_support': support, 'unresolved_header_transfer': transfer,
            'base_bracket_path': {'principal_to_header': direct, 'header_to_post': retained,
                                  'center_bracket_screws': len(base_screws), 'explicit_path_present': connected,
                                  'strength_qualified': False},
            'panel_kicker_screws': product_rows, 'screw_spacing': spacing,
            'product_reference': reference, 'geometry_failures': failures,
            'product_geometry_failures': product_failures,
            'all_tested_geometry_gates_passed': not failures,
            'all_tested_product_geometry_gates_passed': not product_failures,
            'source_sha256': hashes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
