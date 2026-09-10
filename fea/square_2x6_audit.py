"""Preserve passing and failed geometry checks of the single-2x6 starting design."""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

from fea.screw_insert_repair_reserve import assess as repair_assess
from fea.screw_insert_repair_reserve import overlaps
from mini_moonboard import square_2x6_frame as model
from mini_moonboard.connection_geometry import material_intervals


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
    body_collisions = [{'members': [a.name, z.name]} for a, z in combinations(raw.values(), 2)
                       if overlaps(a.shape, z.shape)]
    failures.extend({'gate': 'lower_rail_service_collision', **row} for row in service_collisions)
    failures.extend({'gate': 'wood_collision', **row} for row in body_collisions)
    reserve = repair_assess(raw, hardware)
    failures.extend({'gate': 'future_insert_reserve', 'connection': r['connection']}
                    for r in reserve['schedule'] if not r['passes_nominal_reserve'])
    sources = [Path(__file__).resolve(), Path('fea/screw_insert_repair_reserve.py').resolve(),
               Path('docs/panel-insert-reference.json').resolve(), Path('docs/ml24z-reference.json').resolve(),
               *sorted(Path('mini_moonboard').resolve().glob('*.py'))]
    return {'candidate': model.KEY, 'status': 'DEVELOPMENT BASELINE RETAINED WITH FAILURES',
            'qualified_for_design': False, 'structural_analysis_run': False,
            'limits': 'Fit screens only; no stiffness, strength, buckling, floor contact or repair qualification. '
                      'Existing leg geometry and several base hardware axes are deliberately retained even where they fail. '
                      'Full-bearing fractions are nominal geometry, not load distribution or capacity. '
                      'Future insert reserves exclude damaged wood and do not approve thread engagement, countersinks or repair.',
            'inventory': {'wood_parts': len(raw), 'single_2x6_members': [n for n, p in raw.items()
                          if sorted(p.blank[1:]) == sorted((38.1, 139.7))],
                          'panel_kicker_screws': sum(isinstance(c, model.timber.PanelScrew) for c in hardware),
                          'bolts': sum(c.kind == 'bolt' for c in hardware),
                          'brackets': len(model.stations()), 'installed_inserts': 0},
            'lower_rail_service_collisions': service_collisions,
            'lower_panel_edge_overhang_mm': model.LOWER_S[0],
            'principal_housing_removed': all(raw[f'base_principal_{side}'].shape.isInside(
                model.b.point(model.CENTERS[side], 40., 20.), 1e-6) for side in model.UPRIGHTS),
            'receiver_checks': receiver_checks, 'rim_edge_checks': edge_checks,
            'header_support': supports, 'wood_collisions': body_collisions,
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
