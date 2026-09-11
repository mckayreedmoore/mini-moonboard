"""Split-center geometry and visible fastener inventory; no structural approval."""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import cadquery as cq

from fea import paired_rail_audit as shared
from fea import screw_insert_repair_reserve as repair
from fea import vertical_principal_audit as previous_audit
from fea.vertical_principal_audit import aligned_supports, repair_reserves, seam_support
from mini_moonboard.connection_geometry import material_intervals
from mini_moonboard.selected_hardware import BoltSpec


def sources():
    paths = set(previous_audit.sources()) | {'fea/split_center_audit.py'}
    return {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(paths)}


def bearing_geometry(model, raw):
    """All principal/rim footprints, without assuming a center-line member."""
    header = raw['base_header'].shape
    eps = .01
    slab = model.base._world_box(-2000., 2000., -2000., 4000., model.base.HEADER_TOP, model.base.HEADER_TOP+eps)
    rows, transfers = [], []
    for name, p in raw.items():
        if name.startswith(('base_side_', 'base_principal_')):
            footprint = p.shape.intersect(slab)
            full = footprint.Volume()
            supported = p.shape.intersect(header.translate((0, 0, eps))).Volume()
            bounds = p.shape.BoundingBox()
            posts = [(n, z.shape) for n, z in raw.items() if n.startswith('base_post_') and
                     abs(z.shape.BoundingBox().xmin-bounds.xmin) < 1e-5 and
                     abs(z.shape.BoundingBox().xmax-bounds.xmax) < 1e-5]
            if len(posts) == 1:
                post_name, post = posts[0]
                projected = post.translate((0, 0, model.base.HEADER_TOP-post.BoundingBox().zmax+eps))
                fraction = footprint.intersect(projected).Volume()/full if full > 0 else 0.
                faces = [f for f in p.shape.Faces() if f.BoundingBox().zlen < 1e-6 and
                         abs(f.Center().z-model.base.HEADER_TOP) < 1e-6]
                rear = min(f.BoundingBox().ymin for f in faces)
                transfers.append({'member': name, 'aligned_post': post_name,
                                  'footprint_over_post_fraction': fraction,
                                  'footprint_rear_overhang_beyond_post_mm': max(0., post.BoundingBox().ymin-rear),
                                  'strength_assessed': False})
        elif name.startswith('base_post_'):
            bounds = p.shape.BoundingBox()
            full = bounds.xlen*bounds.ylen*eps
            supported = p.shape.translate((0, 0, eps)).intersect(header).Volume()
        else:
            continue
        if full <= 0:
            raise ValueError('Missing bearing face: '+name)
        fraction = supported/full
        rows.append({'member': name, 'gap_mm': p.shape.distance(header),
                     'nominal_contact_area_fraction': fraction,
                     'passes_full_bearing_geometry': fraction >= 1-1e-5})
    return rows, {'member_transfers': transfers, 'strength_assessed': False,
                  'limits': 'New full-depth posts remove the split principals projected rear overhang. '
                            'Retained outer-rim/post transfer and all actual contact loads/header stresses remain unqualified.'}


def split_center_clearance(model, raw):
    tools = tuple(model.timber.service_envelopes())
    rows = []
    for label, center in model.CENTER_SPLIT.items():
        name = 'base_principal_'+label
        shape = raw[name].shape
        distance = min(shape.distance(tool) for tool in tools)
        collisions = [i for i, tool in enumerate(tools) if repair.overlaps(shape, tool)]
        uncut, _ = model.base._sloped_bearing_member(center-19.05, center+19.05, 139.7, model.b.LENGTH-38.1)
        difference = uncut.cut(shape).Volume()+shape.cut(uncut).Volume()
        rows.append({'member': name, 'minimum_full_service_envelope_clearance_mm': distance,
                     'intersecting_service_envelopes': collisions,
                     'difference_from_uncut_principal_mm3': difference,
                     'passed': not collisions and difference <= .01 and distance > 0.})
    return rows


def bolt_components(connections):
    """Check complete stack roles and signed axial extents on both frame sides."""
    rows = []
    for c in connections:
        if c.kind != 'bolt':
            continue
        shapes = tuple(c.components())
        spec = BoltSpec('Geometric stack audit', c.length, c.grip, 0.)
        washer = spec.washer_thickness_max_mm
        expected = [(0., c.length), (0., washer), (washer+c.grip, 2*washer+c.grip),
                    (-spec.head_height_max_mm, 0.),
                    (2*washer+c.grip, 2*washer+c.grip+spec.nut_height_max_mm)]
        components = []
        if len(shapes) == 5:
            for role, shape, limits in zip(('shaft', 'head_washer', 'nut_washer', 'head', 'nut'), shapes, expected, strict=True):
                # All bolt axes are X-directed; exact axis-aligned bounds include
                # curved rings and do not miss their axial extrema.
                if abs(abs(c.direction.x)-1.) > 1e-8:
                    raise ValueError('Axial envelope audit currently requires X-directed bolt')
                bb = shape.BoundingBox()
                measured = sorted((x-c.start.x)*c.direction.x for x in (bb.xmin, bb.xmax))
                passed = shape.isValid() and shape.Volume() > .01 and all(abs(a-z) < 1e-5 for a, z in zip(measured, limits, strict=True))
                components.append({'role': role, 'volume_mm3': shape.Volume(),
                                   'axial_interval_mm': measured, 'expected_axial_interval_mm': list(limits), 'passed': passed})
        rows.append({'connection': c.name, 'component_count': len(shapes), 'components': components,
                     'passed': len(components) == 5 and all(r['passed'] for r in components),
                     'limits': 'Component presence and geometry only; no bolt steel, torque, clamp friction or connection resistance qualification.'})
    return rows


def build():
    from mini_moonboard import split_center_frame as model
    from mini_moonboard import vertical_principal_frame as previous

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
    if len(new_members) != 6 or any(sorted(p.blank[1:]) != [38.1, 139.7] or p.laminations != 1 for p in new_members):
        failures.append({'gate': 'six_independent_2x6_principals'})
    if 'base_principal_center' in raw or 'base_post_center' in raw:
        failures.append({'gate': 'old_center_member_removed'})
    if any(n.startswith('base_rail_mid_') for n in raw):
        failures.append({'gate': 'interior_horizontal_seam_rails_removed'})
    bracket_inventory = []
    for s in stations:
        cs = [c for c in connections if c.name.startswith(s[0]+'_')]
        counts = {name: sum(name in c.members for c in cs) for name in s[-2:]}
        row = {'bracket': s[0], 'receiver_screw_counts': counts,
               'passed': len(cs) == 6 and all(n == 3 for n in counts.values())}
        bracket_inventory.append(row)
        if not row['passed']:
            failures.append({'gate': 'bracket_screw_ownership', **row})
    gussets = []
    for name, p in old_raw.items():
        if name.startswith('timber_base_gusset_'):
            same = name in raw and (p.shape.isSame(raw[name].shape) or
                    p.shape.cut(raw[name].shape).Volume()+raw[name].shape.cut(p.shape).Volume() < .01)
            gussets.append({'member': name, 'raw_shape_unchanged': same})
    old_bolts = {c.name: c for c in previous.connections() if any(n.startswith('timber_base_gusset_') for n in c.members)}
    current = {c.name: c for c in connections}
    bolt_identity = all(n in current and all(getattr(c, k) == getattr(current[n], k)
                        for k in ('members', 'kind', 'length', 'diameter', 'grip')) and
                        (c.start-current[n].start).Length < 1e-8 and (c.direction-current[n].direction).Length < 1e-8
                        for n, c in old_bolts.items())
    if not gussets or not all(r['raw_shape_unchanged'] for r in gussets) or not bolt_identity:
        failures.append({'gate': 'retained_gusset_geometry_and_axes'})
    clearances = split_center_clearance(model, raw)
    failures.extend({'gate': 'split_center_service_clearance', **r} for r in clearances if not r['passed'])
    bolts = bolt_components(connections)
    failures.extend({'gate': 'bolt_component_envelopes', **r} for r in bolts if not r['passed'])
    seam_overhangs = [-raw['base_principal_center_left'].shape.BoundingBox().xmax,
                      raw['base_principal_center_right'].shape.BoundingBox().xmin]
    seam_previous, seam_current = seam_support(previous, old_raw), seam_support(model, raw)
    if sources() != hashes:
        raise ValueError('Audit source changed during build')
    return {'candidate': model.KEY, 'qualified_for_design': False, 'structural_analysis_run': False,
            'joint_strength_passed': False, 'floor_qualified': False,
            'limits': 'Fit and topology only. Horizontal panel seams are separate free edges between discrete '
                      'principal supports; no invisible tie, panel diaphragm, composite or load-sharing credit. '
                      'Added connections do not establish reduced base-gusset demands. Full support projection '
                      'does not determine contact pressure or connection capacity.',
            'inventory': {'wood_parts': len(raw), 'panel_kicker_screws': len(screws),
                          'bolts': sum(c.kind == 'bolt' for c in connections), 'brackets': len(stations),
                          'bracket_screws': sum(c.name.startswith('clip_') for c in connections),
                          'installed_inserts': 0, 'new_single_2x6_principals': [p.name for p in new_members],
                          'interior_horizontal_seam_rails': [n for n in raw if n.startswith('base_rail_mid_')]},
            'connection_ownership': ledger, 'bracket_screw_ownership': bracket_inventory,
            'receiver_checks': receivers, 'drilled_axis_checks': holes,
            'hardware_body_collisions': body, 'distinct_fastener_collisions': between,
            'wood_collisions': wood, 'bracket_body_collisions': brackets,
            'future_insert_reserves': reserves, 'panel_kicker_screws': product_rows,
            'screw_spacing': spacing, 'product_reference': reference,
            'header_support': bearing, 'new_principal_support_paths': supports,
            'header_transverse_transfer': transfer,
            'split_center_service_clearance': clearances, 'bolt_component_envelopes': bolts,
            'vertical_panel_seam': {'backing_edge_distances_left_right_mm': seam_overhangs,
                                    'panel_edges_supported_continuously': False,
                                    'strength_qualified': False,
                                    'limits': 'Each panel extends 50.95mm from its nearest center-principal edge to the seam; '
                                              'no seam tie, edge support or panel-strength pass is assumed.'},
            'horizontal_seam_comparison': {'previous': seam_previous, 'current': seam_current,
                'basis': 'Actual net backing along both seam edges at N=0.001mm; service-pocket gaps included. '
                         'Previous center member provided continuous vertical seam backing with service pockets. '
                         'Current principal contacts provide discrete backing; clear spans are unsupported panel edges, not capacity.'},
            'retained_gussets': {'members': gussets, 'bolt_count': len(old_bolts), 'bolt_axes_and_grips_unchanged': bolt_identity,
                                'current_forces_available': False, 'force_reduction_established': False},
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
