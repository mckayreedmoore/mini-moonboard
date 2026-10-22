"""Read the evaluated paired-frame detail and its twelve authenticated fields."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = Path('fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/single-leg-header-integration-v1/coherent-return-paired-foot-v1')
PACKET = Path('docs/bolted-frame-development/paired-frame-v1')
EVALUATION = Path('docs/bolted-frame-development/coherent-three-pin-cleat-evaluation-v1.json')
REVISION = 'eoere-paired-cleats-frame-v1'
FROZEN_REVISION = 'unadopted-coherent-three-pin-shift-v1'
CASES = ('a12-forward', 'a12-left', 'a12-rear', 'k12-right', 'k12-rear', 'a1-rear')


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path).resolve().relative_to(ROOT) if Path(path).is_absolute() else Path(path)
    return {'path': str(path), 'sha256': sha(path)}


def read(path, pins, expected=None):
    binding = ref(path)
    assert expected is None or binding['sha256'] == expected, str(path)
    assert binding['path'] not in pins or pins[binding['path']] == binding['sha256'], str(path)
    pins[binding['path']] = binding['sha256']
    return json.loads((ROOT / path).read_bytes())


def load():
    pins = {str(Path(__file__).relative_to(ROOT)): sha(Path(__file__))}
    evaluation = read(EVALUATION, pins, '7ff7c9d5797d5fef348e3f7e359f879bec09940d34699a425acece0e439f246c')
    assert evaluation['complete_conditional_engineering_evaluation']
    assert not evaluation['required_analysis_duties_left_open_on_declared_basis']
    geometry_path = RAW / 'three-pin-shift-geometry-v1/geometry.json'
    geometry = read(geometry_path, pins, '6bc7c9c5ee1a3f03234ffc0ec2976cbe55f9fc8f38facd35967ed4682e9deecb')
    assert geometry['revision'] == FROZEN_REVISION and len(geometry['axes']) == 106
    fields = []
    for scenario, bank in [('nominal', 'runner-roller-comparison-v1'), ('soft', 'short-span-stiffness-v1')]:
        summary = read(RAW / bank / 'cleat-six-case-summary-v1.json', pins)
        assert tuple(c['case_id'] for c in summary['cases']) == CASES
        for case in summary['cases']:
            field_ref = case['field']
            field = read(field_ref['path'], pins, field_ref['sha256'])
            folder = Path(field_ref['path']).parent
            replay = read(folder / 'independent-replay.json', pins)
            plywood = read(folder / 'independent-replay-plywood.json', pins)
            assert replay['field'] == plywood['field'] == field_ref
            assert replay['false_screw_and_floor_forces_rejected']
            assert replay['same_state_corner_normal_activation_replayed']
            assert replay['equilibrium']['gradient_inf_n'] < 1e-5
            assert replay['equilibrium']['physical_body_count'] == 166
            assert len(plywood['raw_operator_checks']) == 4
            assert field['trial_parent_geometry'] == ref(geometry_path)
            assert field['counts']['shaft'] == 106 and field['counts']['fitting'] == 26
            assert len(field['panel_screw_actions']) == len(geometry['screw_axes']) == 66
            fields.append((scenario, case['case_id'], field_ref, field))
    return geometry, fields, pins


def selections(geometry):
    """Merge unchanged purchase columns, then apply the evaluated material choice."""
    path = ROOT / 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/leg-header-v3/hardware-selection.csv'
    old = {r['axis_id']: r for r in csv.DictReader(path.open())}
    proposed = {r['axis_id']: r for r in geometry['selected_stack_overrides']}
    grade8 = {'eoere_bolt_071', 'eoere_bolt_074'} | {f'cleat_post_bolt_{s}_{i}' for s in ('left', 'right') for i in (1, 2)}
    rows = []
    for axis in geometry['axes']:
        identity = axis['id']
        row = {**old.get(identity, {}), **proposed[identity]}
        row.update(selected_diameter_mm=axis['diameter_mm'],
                   receiver_member_ids=';'.join(axis['receivers']),
                   model_underhead_length_mm=axis['nominal_under_head_length_mm'],
                   nut_side_spacer_mm=axis.get('nut_side_spacer_mm', 0.),
                   spacer_piece_count=round(axis.get('nut_side_spacer_mm', 0.) / 12.7),
                   spacer_piece_length_mm=12.7 if axis.get('nut_side_spacer_mm', 0.) else 0.,
                   selected_spacer_SKU='13731' if axis.get('nut_side_spacer_mm', 0.) else '',
                   selected_bolt_grade='SAE J429 Grade 8' if identity in grade8 else 'SAE J429 Grade 5; specified F606 bending reference 92 ksi',
                   selected_nut_grade='SAE J995 Grade 8' if identity in grade8 else 'SAE J995 Grade 5',
                   selected_nut_SKU='2584' if identity in grade8 else ('2573' if axis['diameter_mm'] > 10 else '2571'),
                   selected_washer_SKU='15025' if axis['diameter_mm'] > 10 else '15023',
                   threads_per_inch=13 if axis['diameter_mm'] > 10 else 16,
                   minimum_body_mm=float(row.get('minimum_full_body_mm') or row['minimum_body_mm']),
                   Actual='', Disposition='')
        if identity in grade8:
            row.update(selected_product='7194', selected_product_url='https://boltdepot.com/Product-Details?product=7194')
        assert float(row['selected_underhead_length_mm']) > 0 and row['minimum_body_mm'] > 0
        rows.append(row)
    assert len(rows) == 106 and len({r['axis_id'] for r in rows}) == 106
    assert sum('Grade 8' in r['selected_bolt_grade'] for r in rows) == 6
    return rows
