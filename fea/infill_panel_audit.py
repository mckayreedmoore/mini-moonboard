"""Additional panel screw fit; unchanged framing and no strength inheritance."""
import argparse
import hashlib
import json
from dataclasses import fields
from itertools import combinations, pairwise
from pathlib import Path

import cadquery as cq

from fea import paired_rail_audit as shared
from fea import screw_insert_repair_reserve as repair
from fea import split_center_audit as previous_audit
from fea.split_center_audit import (
    bearing_geometry,
    bolt_components,
    split_center_clearance,
)
from fea.vertical_principal_audit import aligned_supports, repair_reserves, seam_support
from mini_moonboard.connection_geometry import material_intervals


def sources():
    paths = set(previous_audit.sources()) | {'fea/infill_panel_audit.py'}
    return {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(paths)}


def connection_unchanged(a, z):
    """Same concrete geometry type and all dataclass inputs except prose status."""
    if type(a) is not type(z):
        return False
    for field in fields(a):
        if field.name == 'product_status':
            continue
        x, y = getattr(a, field.name), getattr(z, field.name)
        if isinstance(x, cq.Vector):
            if (x-y).Length > 1e-8:
                return False
        elif x != y:
            return False
    return True


def retained_geometry(old_raw, raw, old_connections, connections):
    current = {c.name: c for c in connections}
    changed = [c.name for c in old_connections if c.name not in current or not connection_unchanged(c, current[c.name])]
    wood = []
    for name, p in old_raw.items():
        if name not in raw:
            wood.append(name)
            continue
        z = raw[name]
        if p.blank != z.blank or p.laminations != z.laminations or not (p.shape.isSame(z.shape) or
                p.shape.cut(z.shape).Volume()+z.shape.cut(p.shape).Volume() < .01):
            wood.append(name)
    extra = sorted(set(raw)-set(old_raw))
    return {'old_connection_count': len(old_connections), 'changed_or_missing_connections': changed,
            'changed_or_missing_raw_wood': wood, 'extra_raw_wood': extra,
            'passed': not changed and not wood and not extra,
            'limits': 'Raw bodies and retained fastener geometry only; new drilled holes are intentional.'}


def infill_intervals(model, original, current):
    """All six receiver lines, bounded by retained endpoint screws per panel."""
    tangent = (model.b.point(0., 1., 0.)-model.b.point(0., 0., 0.)).normalized()
    receivers = {f'base_principal_{s}' for s in model.ADDED_CENTERS}
    def grouped(connections):
        result = {}
        for c in connections:
            if isinstance(c, model.timber.PanelScrew) and c.members[0].startswith('main_') and c.members[1] in receivers:
                result.setdefault(c.members, []).append(c)
        return result
    old, new = grouped(original), grouped(current)
    if set(old) != set(new) or {members[1] for members in new} != receivers:
        raise ValueError('Missing or added panel/principal screw line')
    rows = []
    for members, screws in sorted(new.items()):
        screws = sorted(screws, key=lambda c: c.start.dot(tangent))
        original_screws = sorted(old[members], key=lambda c: c.start.dot(tangent))
        stations = [c.start.dot(tangent) for c in screws]
        original_stations = [c.start.dot(tangent) for c in original_screws]
        gaps = [z-a for a, z in pairwise(stations)]
        line_error = max((c.start-screws[0].start).cross(tangent).Length for c in screws)
        endpoint_error = max(abs(stations[0]-original_stations[0]), abs(stations[-1]-original_stations[-1]))
        uniform = []
        for a, z in pairwise(original_stations):
            subdivision = [s for s in stations if a-1e-6 <= s <= z+1e-6]
            lengths = [end-start for start, end in pairwise(subdivision)]
            uniform.append(max(lengths)-min(lengths) if lengths else 151.)
        row = {'panel': members[0], 'receiver': members[1], 'connection_names': [c.name for c in screws],
               'original_connection_names': [c.name for c in original_screws],
               'intervals_mm': gaps, 'maximum_interval_mm': max(gaps, default=0.),
               'minimum_interval_mm': min(gaps, default=0.), 'maximum_line_error_mm': line_error,
               'endpoint_shift_mm': endpoint_error, 'maximum_within_old_interval_nonuniformity_mm': max(uniform, default=0.),
               'specified_maximum_interval_mm': 150.,
               'passed': bool(gaps) and min(gaps) > 0. and max(gaps) <= 150.+1e-6 and
                         line_error <= 1e-6 and endpoint_error <= 1e-6 and max(uniform, default=0.) <= 1e-6,
               'strength_qualified': False,
               'limits': 'Interval between retained first and last screws only; panel-edge distances and connection resistance are separate checks.'}
        rows.append(row)
    return rows


def build():
    from mini_moonboard import infill_panel_frame as model
    from mini_moonboard import split_center_frame as previous

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
    retention = retained_geometry(old_raw, raw, previous.connections(), connections)
    if not retention['passed']:
        failures.append({'gate': 'retained_raw_wood_and_connections', **retention})
    intervals = infill_intervals(model, previous.connections(), connections)
    failures.extend({'gate': 'principal_screw_interval', **r} for r in intervals if not r['passed'])
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
            'retained_geometry': retention, 'principal_screw_intervals': intervals,
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
                         'Raw wood and seam backing are unchanged from the split-center candidate. '
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
