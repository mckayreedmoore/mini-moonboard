"""Geometry audit of the single-member seam and center-post revision."""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import cadquery as cq

from fea.screw_insert_repair_reserve import assess as repair_assess
from fea.screw_insert_repair_reserve import overlaps
from mini_moonboard import selective_2x6_frame as model
from mini_moonboard.connection_geometry import material_intervals


def touching_parallel_lumber(raw):
    """Detect touching side-by-side members, including zero-volume face contact."""
    groups = {}
    for name, part in raw.items():
        if name.startswith(('main_', 'kicker_', 'timber_base_gusset_')):
            continue
        family = ('rail' if name.startswith('base_rail_') or name == 'base_header' else
                  'upright' if name.startswith(('base_side_', 'base_principal_')) else
                  'post' if name.startswith('base_post_') else 'leg')
        groups.setdefault(family, []).append(part)
    axes = {'rail': cq.Vector(1, 0, 0), 'post': cq.Vector(0, 0, 1),
            'upright': (model.b.point(0, 1, 0)-model.b.point(0, 0, 0)).normalized(),
            'leg': model.leg.geometry('2x6', 0.)[2]}
    rows = []
    for family, parts in groups.items():
        axis = axes[family]
        for a, z in combinations(parts, 2):
            intervals = [sorted(v.Center().dot(axis) for v in p.shape.Vertices()) for p in (a, z)]
            shared = min(i[-1] for i in intervals)-max(i[0] for i in intervals)
            if shared > .8*min(p.blank[0] for p in (a, z)) and a.shape.distance(z.shape) < 1e-5:
                rows.append({'members': [a.name, z.name], 'shared_length_mm': shared})
    return rows


def build():
    raw = {p.name: p for p in model.wood_parts()}
    hardware = model.connections()
    failures, receiver_checks = [], []
    for c in hardware:
        for name in c.members:
            if name not in raw:
                continue
            runs = material_intervals(raw[name].shape, c.start, c.direction, 0., c.length)
            length = sum(z-a for a, z in runs)
            required = 0.
            if c.name.startswith('clip_'):
                required = model.hardware.SDS['gross_penetration_through_nominal_ml24z']
            elif isinstance(c, model.timber.PanelScrew) and name == c.members[1]:
                required = c.length-model.wide.PANEL
            passed = bool(runs) and length >= required-1e-5
            row = {'connection': c.name, 'member': name, 'axial_material_mm': length,
                   'required_gross_material_mm': required, 'passed': passed}
            receiver_checks.append(row)
            if not passed:
                failures.append({'gate': 'receiver_material', **row})
    edge_checks = []
    for c in hardware:
        if c.kind != 'bolt' or not any(n.startswith('base_side_') for n in c.members):
            continue
        n = (c.start-model.b.point(0., 0., 0.)).dot(model.b.normal())
        edge = min(n, 139.7-n)
        row = {'connection': c.name, 'minimum_depth_edge_mm': edge,
               'reversible_cross_grain_screen_mm': 4*c.diameter,
               'passed': edge >= 4*c.diameter-1e-6}
        edge_checks.append(row)
        if not row['passed']:
            failures.append({'gate': 'rim_bolt_edge', **row})
    shared_edges = []
    for c in hardware:
        if isinstance(c, model.timber.PanelScrew) and c.members[1].startswith(
                ('base_principal_center', 'base_post_center', 'base_rail_mid_')):
            if c.members[1].startswith('base_rail_mid_'):
                tangent = (model.b.point(0, 1, 0)-model.b.point(0, 0, 0)).normalized()
                offset = abs((c.start-model.b.point(0, model.b.HALF, 0)).dot(tangent))
            else:
                offset = abs(c.start.x)
            edge = min(offset, model.SHARED_WIDTH/2-offset)
            row = {'connection': c.name, 'panel_and_receiver_edge_mm': edge,
                   'preliminary_2_5D_screen_mm': 2.5*c.diameter,
                   'passed': edge >= 2.5*c.diameter}
            shared_edges.append(row)
            if not row['passed']:
                failures.append({'gate': 'shared_seam_screw_edge_screen', **row})
    old, _, along, across = model.leg.geometry('2x6', 0.)
    leg_edges = []
    for c in hardware:
        if not c.name.startswith('lumber_leg_bolt_'):
            continue
        edge = 139.7/2-abs((c.start-old).dot(across))
        end = 150.-(c.start-old).dot(along)
        row = {'connection': c.name, 'leg_side_edge_mm': edge, 'leg_top_end_mm': end,
               'passes_4D_side_7D_top_screen': edge >= 4*c.diameter and end >= 7*c.diameter}
        leg_edges.append(row)
        if not row['passes_4D_side_7D_top_screen']:
            failures.append({'gate': 'leg_bolt_edge_end', **row})
    header = raw['base_header'].shape
    supports = []
    eps = .01
    slab = model.base._world_box(-2000., 2000., -2000., 4000.,
                                 model.base.HEADER_TOP, model.base.HEADER_TOP+eps)
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
        fraction = supported/full
        row = {'member': name, 'nominal_contact_area_fraction': fraction,
               'passes_full_bearing_geometry': fraction >= 1-1e-5}
        supports.append(row)
        if not row['passes_full_bearing_geometry']:
            failures.append({'gate': 'incomplete_header_bearing', **row})
    lower = [p for n, p in raw.items() if n.startswith('base_rail_bottom_')]
    service_collisions = []
    for p in lower:
        for index, tool in enumerate(model.timber.service_envelopes()):
            if overlaps(p.shape, tool):
                service_collisions.append({'member': p.name, 'reservation_index': index})
    pocketed = [p for n, p in raw.items() if n.startswith(('base_principal_', 'base_rail_mid_'))]
    pocket_collisions = [{'member': p.name, 'reservation_index': i}
                         for p in pocketed for i, tool in enumerate(model.timber.service_envelopes())
                         if overlaps(p.shape, tool)]
    failures.extend({'gate': 'shared_framing_service_collision', **row} for row in pocket_collisions)
    body_collisions = [{'members': [a.name, z.name]} for a, z in combinations(raw.values(), 2)
                       if overlaps(a.shape, z.shape)]
    failures.extend({'gate': 'lower_rail_service_collision', **row} for row in service_collisions)
    failures.extend({'gate': 'wood_collision', **row} for row in body_collisions)
    paired = touching_parallel_lumber(raw)
    failures.extend({'gate': 'touching_parallel_lumber', **row} for row in paired)
    reserve = repair_assess(raw, hardware)
    failures.extend({'gate': 'future_insert_reserve', 'connection': r['connection']}
                    for r in reserve['schedule'] if not r['passes_nominal_reserve'])
    sources = [Path(__file__).resolve(), Path('docs/selective-stock-reference.json').resolve(), Path('fea/screw_insert_repair_reserve.py').resolve(),
               Path('docs/panel-insert-reference.json').resolve(), Path('docs/ml24z-reference.json').resolve(),
               *sorted(Path('mini_moonboard').resolve().glob('*.py'))]
    return {'candidate': model.KEY, 'status': 'GEOMETRIC FIT CHECKS ONLY; NO STRUCTURAL APPROVAL',
            'qualified_for_design': False, 'structural_analysis_run': False,
            'limits': 'Fit screens only; no stiffness, strength, buckling, floor contact or repair qualification. '
                      'The leg outline is retained; bolt groups and base hardware have moved. '
                      'Full-bearing fractions are nominal geometry, not load distribution or capacity. '
                      'Future insert reserves exclude damaged wood and do not approve thread engagement, countersinks or repair.',
            'inventory': {'wood_parts': len(raw), 'single_2x6_members': [n for n, p in raw.items()
                          if sorted(p.blank[1:]) == sorted((38.1, 139.7))],
                          'single_3x6_members': [n for n, p in raw.items() if sorted(p.blank[1:]) == [63.5, 139.7]],
                          'single_2x10_members': [n for n, p in raw.items() if sorted(p.blank[1:]) == [38.1, 234.95]],
                          'panel_kicker_screws': sum(isinstance(c, model.timber.PanelScrew) for c in hardware),
                          'bolts': sum(c.kind == 'bolt' for c in hardware),
                          'brackets': len(model.stations()), 'installed_inserts': 0},
            'lower_rail_service_collisions': service_collisions,
            'shared_framing_service_collisions': pocket_collisions,
            'shared_seam_edge_checks': shared_edges,
            'shared_seam_edge_basis': 'Preliminary 2.5D wood-screw edge recommendation from AWC NDS commentary; '
                                    'not a product-specific resistance calculation or complete current-code check. '
                                    'https://awc.org/wp-content/uploads/2021/12/AWC-2015NDS-Updates-Errata_20240109.pdf',
            'shared_seam_margins': {
                'panel_bearing_width_each_mm': model.SHARED_WIDTH/2,
                'screw_axis_to_timber_edge_mm': min(r['panel_and_receiver_edge_mm'] for r in shared_edges),
                'repair_reserve_side_ligament_mm': min(r['panel_and_receiver_edge_mm'] for r in shared_edges)-reserve['schedule'][0]['reserve_diameter_mm']/2,
                'connection_resistance_qualified': False},
            'lower_panel_edge_overhang_mm': model.LOWER_S[0],
            'principal_housing_removed': all(raw[f'base_principal_{side}'].shape.isInside(
                model.b.point(model.CENTERS[side], 40., 20.), 1e-6) for side in model.UPRIGHTS),
            'touching_parallel_lumber': paired,
            'receiver_checks': receiver_checks, 'rim_edge_checks': edge_checks,
            'leg_edge_end_checks': leg_edges, 'header_support': supports, 'wood_collisions': body_collisions,
            'future_insert_reserves': reserve, 'failures': failures,
            'all_tested_geometry_gates_passed': not failures,
            'source_sha256': {str(p.relative_to(Path.cwd())): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build()
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
