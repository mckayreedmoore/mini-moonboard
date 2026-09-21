"""Vertical-principal fit and support topology; no frame-strength inference."""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import cadquery as cq

from fea import paired_rail_audit as shared
from fea import screw_insert_repair_reserve as repair
from mini_moonboard.connection_geometry import material_intervals


def repair_reserves(raw, screws, connections):
    """Evaluate every current screw; no inherited fixed inventory count."""
    if len({c.name for c in screws}) != len(screws):
        raise ValueError('Duplicate panel screw identity')
    components = [(c.name, shape) for c in connections for shape in c.components()]
    rows = []
    for c in screws:
        entry, cylinder = repair.reserve(c)
        missing = cylinder.cut(raw[c.members[1]].shape).Volume()
        collisions = sorted({name for name, shape in components if name != c.name and repair.overlaps(cylinder, shape)})
        rows.append({'connection': c.name, 'panel': c.members[0], 'receiver': c.members[1],
                     'entry_xyz_mm': list(entry.toTuple()), 'direction_xyz': list(c.direction.toTuple()),
                     'reserve_diameter_mm': repair.DIAMETER, 'reserve_depth_mm': repair.DEPTH,
                     'missing_receiver_volume_mm3': missing, 'intersecting_other_fasteners': collisions,
                     'passes_nominal_reserve': missing <= repair.VOLUME_TOLERANCE and not collisions})
    return {'reserve_count': len(rows), 'passes_nominal_reserves': bool(rows) and all(r['passes_nominal_reserve'] for r in rows),
            'qualified_for_design': False, 'qualified_repair': False, 'schedule': rows}


def free_intervals(supports, low, high):
    """Complement of the clipped union, preserving separate unsupported spans."""
    cursor, result = low, []
    for a, z in sorted(supports):
        a, z = max(low, a), min(high, z)
        if z <= a:
            continue
        if a > cursor+1e-6:
            result.append([cursor, a])
        cursor = max(cursor, z)
    if cursor < high-1e-6:
        result.append([cursor, high])
    return result


def seam_support(model, raw):
    """Probe actual net backing at each seam edge, just behind the face."""
    rows = []
    for side, s in (('lower_panel_top', model.b.HALF-.001), ('upper_panel_bottom', model.b.HALF+.001)):
        ownership, runs = [], []
        for name, p in raw.items():
            if not name.startswith(('base_side_', 'base_principal_', 'base_rail_mid_')):
                continue
            intervals = material_intervals(p.shape, model.b.point(0., s, .001), cq.Vector(1, 0, 0),
                                          -model.b.HALF, model.b.HALF)
            if intervals:
                ownership.append({'member': name, 'backing_intervals_x_mm': intervals})
                runs.extend(intervals)
        free = free_intervals(runs, -model.b.HALF, model.b.HALF)
        rows.append({'edge': side, 'station_s_mm': s, 'probe_depth_n_mm': .001,
                     'backing': ownership, 'unsupported_intervals_x_mm': free,
                     'clear_spans_mm': [z-a for a, z in free],
                     'maximum_clear_span_mm': max((z-a for a, z in free), default=0.)})
    return rows


def aligned_supports(model, raw, stations):
    """Check physical support projection; bracket paths are topology, not capacity."""
    names = sorted(n for n in raw if n.startswith('base_principal_') and n != 'base_principal_center')
    rows = []
    eps = .01
    slab = model.base._world_box(-2000., 2000., -2000., 4000., model.base.HEADER_TOP, model.base.HEADER_TOP+eps)
    for name in names:
        principal = raw[name].shape
        bounds = principal.BoundingBox()
        posts = [(n, p.shape) for n, p in raw.items() if n.startswith('base_post_') and
                 abs(p.shape.BoundingBox().xmin-bounds.xmin) < 1e-5 and
                 abs(p.shape.BoundingBox().xmax-bounds.xmax) < 1e-5]
        if len(posts) != 1:
            rows.append({'principal': name, 'passed': False, 'reason': 'Missing unique aligned post'})
            continue
        post_name, post = posts[0]
        footprint = principal.intersect(slab)
        shifted_post = post.translate((0, 0, model.base.HEADER_TOP-post.BoundingBox().zmax+eps))
        full = footprint.Volume()
        fraction = footprint.intersect(shifted_post).Volume()/full if full > 0 else 0.
        base_clips = [s[0] for s in stations if set(s[-2:]) == {name, 'base_header'}]
        post_clips = [s[0] for s in stations if set(s[-2:]) == {post_name, 'base_header'}]
        top_clips = [s[0] for s in stations if set(s[-2:]) == {name, 'base_rail_top'}]
        rows.append({'principal': name, 'aligned_post': post_name,
                     'principal_x_mm': (bounds.xmin+bounds.xmax)/2,
                     'footprint_over_post_fraction': fraction,
                     'principal_to_header_clips': base_clips, 'header_to_post_clips': post_clips,
                     'principal_to_top_clips': top_clips,
                     'passed': fraction >= 1-1e-5 and bool(base_clips and post_clips and top_clips),
                     'strength_qualified': False})
    return rows


def sources():
    paths = set(shared.sources()) | {'fea/vertical_principal_audit.py'}
    return {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(paths)}


def build():
    from mini_moonboard import paired_rail_frame as previous
    from mini_moonboard import vertical_principal_frame as model

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
    bearing, transfer = shared.bearing_geometry(model, raw)
    failures.extend({'gate': 'header_bearing', **r} for r in bearing if not r['passes_full_bearing_geometry'])
    supports = aligned_supports(model, raw, stations)
    failures.extend({'gate': 'new_principal_support_path', **r} for r in supports if not r['passed'])
    new_members = [raw[r['principal']] for r in supports]
    if len(new_members) != 4 or any(sorted(p.blank[1:]) != [38.1, 139.7] or p.laminations != 1 for p in new_members):
        failures.append({'gate': 'four_single_2x6_principals'})
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
            'unresolved_original_header_transfer': transfer,
            'horizontal_seam_comparison': {'previous': seam_previous, 'current': seam_current,
                'basis': 'Actual net backing along both seam edges at N=0.001mm; service-pocket gaps included. '
                         'Previous spanning rails provided bay-length backing with local service openings. '
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
