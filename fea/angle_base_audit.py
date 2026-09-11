"""Direct outer base angles replacing gussets; fit is not equivalent strength."""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import cadquery as cq

from fea import infill_panel_audit as previous_audit
from fea import paired_rail_audit as shared
from fea import screw_insert_repair_reserve as repair
from fea.infill_panel_audit import (
    connection_unchanged,
    infill_intervals,
    retained_geometry,
)
from fea.split_center_audit import (
    bearing_geometry,
    bolt_components,
    split_center_clearance,
)
from fea.vertical_principal_audit import aligned_supports, repair_reserves, seam_support
from mini_moonboard.connection_geometry import material_intervals


def sources():
    paths = set(previous_audit.sources()) | {'fea/angle_base_audit.py'}
    return {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(paths)}


def replacement_geometry(model, previous, raw, drilled, connections, stations):
    old_raw = {p.name: p for p in previous.wood_parts()}
    removed = {name for name in old_raw if name.startswith('timber_base_gusset_')}
    old = tuple(previous.connections())
    removed_bolts = [c for c in old if any(name in removed for name in c.members)]
    names = {c.name for c in connections}
    retained = [c for c in old if c not in removed_bolts]
    retention = retained_geometry({n: p for n, p in old_raw.items() if n not in removed}, raw, retained, connections)
    paths = []
    for side in ('left', 'right'):
        rim, post = 'base_side_'+side, 'base_post_outer_'+side
        direct = [s[0] for s in stations if set(s[-2:]) == {rim, 'base_header'}]
        supporting = [s[0] for s in stations if set(s[-2:]) == {post, 'base_header'}]
        screws = [c for c in connections if any(c.name.startswith(name+'_') for name in direct)]
        paths.append({'side': side, 'rim_to_header_angles': direct, 'header_to_post_angles': supporting,
                      'direct_angle_screw_count': len(screws),
                      'passed': len(direct) == 1 and bool(supporting) and len(screws) == 6})
    restoration = []
    for old_bolt in removed_bolts:
        for name in old_bolt.members:
            if name in removed:
                continue
            # Restore the former complete clearance bore, except material cut by
            # the declared new connections. This catches stale legacy pilots.
            probe = cq.Solid.makeCylinder(11.1125/2, old_bolt.length+2,
                                           old_bolt.start-old_bolt.direction, old_bolt.direction)
            expected = probe.intersect(raw[name].shape)
            for c in connections:
                if name not in c.members:
                    continue
                diameter = 11.1125 if c.kind == 'bolt' else c.diameter
                cut = cq.Solid.makeCylinder(diameter/2, c.length+2, c.start-c.direction, c.direction)
                eb, cb = expected.BoundingBox(), cut.BoundingBox()
                if all(getattr(eb, axis+'max') > getattr(cb, axis+'min') and
                       getattr(cb, axis+'max') > getattr(eb, axis+'min') for axis in 'xyz'):
                    expected = expected.cut(cut)
                if c.kind == 'screw' and c.members[0] == name:
                    expected = expected.cut(c.components()[1])
            volume = expected.Volume()
            missing = expected.cut(drilled[name].shape).Volume()
            restoration.append({'removed_connection': old_bolt.name, 'member': name,
                                'expected_restored_volume_mm3': volume,
                                'missing_restored_volume_mm3': missing,
                                'passed': volume > 1. and missing <= .01})
    result = {'removed_gusset_names': sorted(removed), 'removed_gusset_bolt_names': [c.name for c in removed_bolts],
              'outer_connection_paths': paths,
              'passed': len(removed) == 2 and len(removed_bolts) == 8 and not (removed & raw.keys()) and
                        not ({c.name for c in removed_bolts} & names) and all(r['passed'] for r in paths),
              'equivalent_stiffness_or_strength_established': False,
              'limits': 'Two direct rim/header angles replace gussets geometrically. Mixed-axis bracket demands, '
                        'cross-grain timber response, racking and floor stability require new analysis.'}
    return result, retention, restoration


def panel_support_equivalence(model, previous, raw, drilled, connections):
    """Compare the exact four-panel, fixed-screw support problem only."""
    old_raw = {p.name: p for p in previous.wood_parts()}
    old_screws = {c.name: c for c in previous.connections() if isinstance(c, previous.timber.PanelScrew)}
    new_screws = {c.name: c for c in connections if isinstance(c, model.timber.PanelScrew)}
    equal_connections = old_screws.keys() == new_screws.keys() and all(
        connection_unchanged(c, new_screws[name]) for name, c in old_screws.items())
    rows = []
    for name, p in old_raw.items():
        if not name.startswith('main_'):
            continue
        old_drilled = p.shape
        for c in old_screws.values():
            if name in c.members:
                old_drilled = old_drilled.cut(cq.Solid.makeCylinder(c.diameter/2, c.length+2,
                                                                   c.start-c.direction, c.direction))
                if c.members[0] == name:
                    old_drilled = old_drilled.cut(c.components()[1])
        raw_difference = p.shape.cut(raw[name].shape).Volume()+raw[name].shape.cut(p.shape).Volume()
        drilled_difference = old_drilled.cut(drilled[name].shape).Volume()+drilled[name].shape.cut(old_drilled).Volume()
        rows.append({'panel': name, 'raw_symmetric_difference_mm3': raw_difference,
                     'drilled_symmetric_difference_mm3': drilled_difference,
                     'passed': raw_difference <= .01 and drilled_difference <= .01})
    return {'panels': rows, 'panel_kicker_connection_count': len(new_screws),
            'all_panel_kicker_connections_identical': equal_connections,
            'fixed_point_restraint_panel_geometry_equivalent': len(rows) == 4 and equal_connections and all(r['passed'] for r in rows),
            'whole_frame_equivalent': False, 'joint_force_transfer_authorized': False,
            'limits': 'Only the prior four-main-panel fixed-point-restraint diagnostic may be linked. '
                      'Same material/mesh/load assumptions remain necessary. No frame stiffness, base-angle '
                      'demand, gusset forces, real screw restraint or structural qualification transfers.'}


def build():
    from mini_moonboard import angle_base_frame as model
    from mini_moonboard import infill_panel_frame as previous

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
    replacement, retention, orphan_holes = replacement_geometry(model, previous, raw, drilled, connections, stations)
    if not replacement['passed']:
        failures.append({'gate': 'gusset_to_angle_replacement', **replacement})
    if not retention['passed']:
        failures.append({'gate': 'unrelated_geometry_retained', **retention})
    failures.extend({'gate': 'orphan_gusset_bolt_hole', **r} for r in orphan_holes if not r['passed'])
    clearances = split_center_clearance(model, raw)
    failures.extend({'gate': 'split_center_service_clearance', **r} for r in clearances if not r['passed'])
    bolts = bolt_components(connections)
    failures.extend({'gate': 'bolt_component_envelopes', **r} for r in bolts if not r['passed'])
    seam_overhangs = [-raw['base_principal_center_left'].shape.BoundingBox().xmax,
                      raw['base_principal_center_right'].shape.BoundingBox().xmin]
    seam_previous, seam_current = seam_support(previous, old_raw), seam_support(model, raw)
    intervals = infill_intervals(model, previous.connections(), connections)
    failures.extend({'gate': 'principal_screw_interval', **r} for r in intervals if not r['passed'])
    panel_equivalence = panel_support_equivalence(model, previous, raw, drilled, connections)
    if not panel_equivalence['fixed_point_restraint_panel_geometry_equivalent']:
        failures.append({'gate': 'bounded_panel_support_equivalence'})
    if sources() != hashes:
        raise ValueError('Audit source changed during build')
    return {'candidate': model.KEY, 'qualified_for_design': False, 'structural_analysis_run': False,
            'joint_strength_passed': False, 'floor_qualified': False,
            'limits': 'Fit and topology only. Horizontal panel seams are separate free edges between discrete '
                      'principal supports; no invisible tie, panel diaphragm, composite or load-sharing credit. '
                      'Replacing gussets with angle brackets does not establish equivalent stiffness or strength. Full support projection '
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
            'panel_support_equivalence': panel_equivalence,
            'base_angle_replacement': replacement, 'former_gusset_bore_restoration': orphan_holes,
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
