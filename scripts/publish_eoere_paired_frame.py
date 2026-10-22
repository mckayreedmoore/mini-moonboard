"""Publish the corrected paired frame from frozen BReps and receiver queries."""

from __future__ import annotations

import copy
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path

import numpy as np

from scripts.eoere_current_shop_followup import csv_bytes, encoded
from scripts.eoere_paired_frame_basis import ROOT, RAW, PACKET, EVALUATION, read, ref, selections, sha

OWN = Path(__file__).resolve()
WORK = RAW/'frame-completion-v1'
GEOMETRY = WORK/'upper-leg-up15-geometry-v1/geometry.json'
INPUT = WORK/'upper-leg-up15-cases-v1/geometry-preparation/inputs.json'
OLD = Path('docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/leg-header-v3/geometry.json')
SCENE = Path('site/eoere-paired-cleats-frame-v1-scene.json.gz')
KEY = 'eoere-paired-cleats-frame-development'
INDEX = Path('docs/bolted-frame-development/development-revisions.json')


def publish():
    import cadquery as cq
    from scripts.export_wood_joint_wj24_scene import _deduplicate_triangle_topologies, _shape_mesh

    assert not (ROOT/PACKET).exists() and not (ROOT/SCENE).exists(), 'fresh publication required'
    pins = {ref(OWN)['path']: sha(OWN), 'scripts/eoere_paired_frame_basis.py': sha('scripts/eoere_paired_frame_basis.py')}
    geometry = read(GEOMETRY, pins, 'ab07d52c99c41e84b5a75e3bb812015d7bdb6204cfa6acbb127e22f5c2c007a7')
    preparation = read(INPUT, pins)
    clearance = read(GEOMETRY.parent/'clearance.json', pins)
    assert preparation['geometry'] == clearance['geometry'] == ref(GEOMETRY)
    assert clearance['nominal_geometry_clear'] and clearance['occupied_part_count'] == 1097
    assert len(clearance['newly_checked_part_ids']) == 14 and not clearance['collisions'] and not clearance['missing_candidates']
    old = read(OLD, pins)
    index_bytes = (ROOT/INDEX).read_bytes()
    previous = json.loads(index_bytes)
    assert previous['schema'] == 'bolted_frame_development_revisions/v5'
    assert previous['geometry']['receipt'] == ref(OLD)
    stage = ROOT/WORK/'publication-stage-v1'
    assert not stage.exists(), 'preserve previous staging evidence'
    stage.mkdir()
    (stage/'preceding-index.json').write_bytes(index_bytes)
    files = {}

    def put(name, value):
        payload = value if isinstance(value, bytes) else encoded(value)
        (stage/name).write_bytes(payload)
        binding = {'path': str(PACKET/name), 'sha256': hashlib.sha256(payload).hexdigest()}
        files[name] = binding
        return binding

    def worksheet(rows):
        keys = list(dict.fromkeys(k for row in rows for k in row))
        return csv_bytes([{k: row.get(k, '') for k in keys} for row in rows])

    def old_rows(name):
        binding = old['files'][name]
        assert sha(binding['path']) == binding['sha256']
        pins[binding['path']] = binding['sha256']
        return list(csv.DictReader(io.StringIO((ROOT/binding['path']).read_text())))

    profiles = copy.deepcopy(geometry['profiles'])
    original_members = {r['member']: r for r in old_rows('members.csv')}
    members = []
    for name, profile in profiles.items():
        row = copy.deepcopy(original_members.get(name, {}))
        blank = list(profile['blank_mm'])
        # Issued angled raw blanks include material beyond the finished L
        # extent. Retain that allowance when only their bores changed.
        if name in original_members:
            blank[0] = max(blank[0], float(original_members[name]['nominal_blank_length_mm']))
        for j in (1, 2):
            for nominal in (18.25625, 28.575, 38.1, 88.9, 139.7):
                if abs(blank[j]-nominal) < 1e-5:
                    blank[j] = nominal
                    break
        profile['blank_mm'] = blank
        row.update(member=name, kind=profile['kind'], Actual='', Disposition='')
        for key, value in zip(('nominal_blank_length_mm', 'nominal_blank_depth_mm', 'nominal_blank_thickness_mm'), blank):
            row[key] = value
        for j, label in enumerate('xyz'):
            row['datum_'+label+'_mm'] = profile['datum_xyz_mm'][j]
            for i, local in enumerate('luv'):
                row['basis_'+local+'_'+label+'_unitless'] = profile['basis_grain_u_v_xyz'][i][j]
        row['current_finished_source_path'] = profile['finished']['path']
        row['current_finished_source_sha256'] = profile['finished']['sha256']
        members.append(row)
    selected = selections(geometry)
    for row in selected:
        a = next(a for a in geometry['axes'] if a['id'] == row['axis_id'])
        row['hardware_model_updated'] = True
        row['head_side_fitting_ids'] = ';'.join(r['angle_id'] for r in a['attachments']
            if np.linalg.norm(np.asarray(r['point'])-a['point_xyz_mm']) < 1e-6)
        row['nut_side_fitting_ids'] = ';'.join(r['angle_id'] for r in a['attachments']
            if np.linalg.norm(np.asarray(r['point'])-a['point_xyz_mm']) >= 1e-6)
        row['selected_recipe'] = 'head/head_washer/'+('head_plate/' if a['before_plate_mm'] else '')+'receivers/'+('nut_plate/' if a['after_plate_mm'] else '')+'nut_washer/'+('spacer/'*row['spacer_piece_count'])+'nut'
        row['reason'] = 'Coordinated paired frame; six long cleat bolts use the evaluated Grade8/matching-nut requirement. Actual delivery is unobserved.'
    axes = {a['id']: a for a in geometry['axes']}
    old_holes = old_rows('receiver-holes.csv')
    hole_template = old_holes[0]
    holes, lengths = [], {}
    for wall in preparation['finished_receiver_wall_queries']:
        identity, name = wall['axis_id'], wall['receiver']
        intervals = wall['finished_full_wall_intervals_from_axis_point_mm']
        assert len(intervals) == 1
        lo, hi = intervals[0]
        a, profile = axes[identity], profiles[name]
        shaft = next(s for s in preparation['shafts'] if s['axis_id'] == identity)
        point, direction = np.asarray(shaft['point']), np.asarray(shaft['basis'][0])
        row = {k: '' for k in hole_template}
        row.update(axis_id=identity, receiver=name, nominal_shaft_diameter_mm=a['diameter_mm'],
            modeled_bore_envelope_diameter_mm=a['bore_diameter_mm'], modeled_underhead_length_mm=a['nominal_under_head_length_mm'],
            entry_from_axis_point_mm=lo, exit_from_axis_point_mm=hi, saved_full_wall_length_mm=hi-lo,
            source='Fresh exact corrected paired-frame receiver query', Actual='', Disposition='')
        for j, label in enumerate('xyz'):
            row['axis_point_'+label+'_mm'] = point[j]
            row['axis_direction_'+label+'_unitless'] = direction[j]
        for prefix, p in [('axis_point', point), ('entry', point+direction*lo), ('exit', point+direction*hi)]:
            local = np.asarray(profile['basis_grain_u_v_xyz'])@(p-profile['datum_xyz_mm'])
            for j, label in enumerate('luv'):
                row[prefix+'_in_receiver_'+label+'_mm'] = float(local[j])
        holes.append(row)
        lengths[identity] = lengths.get(identity, 0.)+hi-lo
    old_drilling = {r['axis_id']: r for r in old_rows('drilling-requirements.csv')}
    drilling = []
    for identity, a in axes.items():
        row = copy.deepcopy(old_drilling.get(identity, next(iter(old_drilling.values()))))
        row.update(axis_id=identity, nominal_wood_path_mm=lengths[identity], Actual='', Disposition='')
        row['minimum_usable_bit_projection_mm'] = lengths[identity]+float(row['proposed_guide_mm'])+float(row['proposed_backer_travel_mm'])
        row['proposed_bit_in'] = '17/32' if a['diameter_mm'] > 10 else '13/32'
        drilling.append(row)
    assert len(members) == 34 and len(holes) == 134 and len(drilling) == len(selected) == 106
    assert sum(r['spacer_piece_count'] for r in selected) == 36
    put('current_profiles.json', profiles)
    put('members.csv', worksheet(members))
    put('hardware-selection.csv', worksheet(selected))
    put('receiver-holes.csv', worksheet(holes))
    put('drilling-requirements.csv', worksheet(drilling))
    put('axes.json', {'axes': geometry['axes'], 'screw_axes': geometry['screw_axes'], 'fitting_poses': geometry['fitting_poses']})
    grade8_path = Path('fea/generated/selected-hardware-followup-v1/engineering-closure-v1/cleat-senior-review-v1/plywood-gusset-v1/sources/grade8-bolt-nut-option-facts-v1.json')
    grade8 = read(grade8_path, pins)
    assert grade8['bolt']['product'] == '7194' and grade8['nut']['product'] == '2584'
    report = {'schema': 'eoere_paired_frame_revision/v1', 'revision': geometry['revision'],
        'candidate': previous['evidence_candidate'], 'parent_geometry': previous['geometry'],
        'checked_geometry': ref(GEOMETRY), 'checked_clearance': ref(GEOMETRY.parent/'clearance.json'),
        'fresh_mechanics_inputs': ref(INPUT), 'files': files,
        'counts': {'sawn_members': 24, 'plywood_cleats': 4, 'panels': 6, 'angles': 26,
            'bolt_stacks': 106, 'nuts': 106, 'washers': 212, 'spacer_pieces': 36,
            'Hillman_axes': 66, 'receiver_occurrences': 134, 'occupied_parts': 1097},
        'upper_leg_edge_correction': geometry['upper_leg_edge_correction'],
        'source_cleat_evaluation': ref(EVALUATION), 'old_force_pass_transferred': False,
        'changed_finished_solids': [{k: r[k] for k in ('id', 'kind', 'sha256', 'bounds_xyz_mm')} for r in geometry['changed_finished_solids']],
        'source_sha256': pins, 'development_model_integrated': True,
        'complete_frame_qualified': False, 'panel_Hillman_resolution_deferred': True,
        'fabrication_released': False, 'climbing_released': False, 'actual_observations': None}
    receipt = put('geometry.json', report)
    replacements = []
    for row in geometry['changed_finished_solids']:
        assert sha(row['path']) == row['sha256']
        shape = cq.Shape.importBrep(str(ROOT/row['path']))
        fabrication = {'kind': 'bracket' if row['kind'] == 'angle' else row['kind'],
            'paired_frame_revision': geometry['revision'],
            'dimensions_mm': [row['bounds_xyz_mm'][2*i+1]-row['bounds_xyz_mm'][2*i] for i in range(3)],
            'description': 'Paired-cleat development frame; panel/Hillman strength unresolved and deferred'}
        if row['kind'] == 'bolt':
            axis = next(a for identity, a in axes.items() if row['id'].startswith(identity+'_'))
            choice = next(r for r in selected if r['axis_id'] == axis['id'])
            fabrication.update(connection_name=axis['id'], hardware_role=row['id'][len(axis['id'])+1:],
                diameter_mm=axis['diameter_mm'], selected_underhead_length_mm=choice['selected_underhead_length_mm'],
                nominal_underhead_length_mm=axis['nominal_under_head_length_mm'], selected_bolt_grade=choice['selected_bolt_grade'],
                selected_nut_grade=choice['selected_nut_grade'], nut_side_spacer_mm=axis.get('nut_side_spacer_mm', 0.),
                stack_roles=['shaft', 'head', 'head_washer', 'nut_washer',
                    *(['spacer'] if choice['spacer_piece_count'] else []),
                    *(['spacer_2'] if choice['spacer_piece_count'] == 2 else []), 'nut'], delivered_part_verified=False)
        elif row['id'] in profiles:
            fabrication.update(blank_mm=profiles[row['id']]['blank_mm'])
            if row['id'].startswith('eoere_cleat_'):
                fabrication.update(material='APA48oc PS1 plywood, five plies minimum, Group1 bearing basis',
                    panel_strength_axis='worldZ', minimum_credited_actual_thickness_mm=27.)
        replacements.append({'id': row['id'], 'name': row['id'], 'mesh': _shape_mesh(shape), 'fabrication': fabrication})
    patch = {'schema': 'eoere_paired_frame_patch/v1', 'revision': geometry['revision'], 'key': KEY,
        'parent_scene': geometry['parent_geometry']['scene'], 'parent_layout': geometry['parent_geometry']['receipt'],
        'layout_report': receipt, 'part_count': 1097, 'replacements': replacements,
        'removals': sorted(set(clearance['removed_parent_parts'])-{r['id'] for r in replacements}),
        'historical_capacity_transferred': False,
        'fabrication_released': False, 'climbing_released': False, 'panel_Hillman_resolution_deferred': True}
    patch['triangle_topologies'] = _deduplicate_triangle_topologies(replacements)
    decoded = json.dumps(patch, separators=(',', ':'), allow_nan=False).encode()
    compressed = gzip.compress(decoded, mtime=0)
    (stage/'scene.json.gz').write_bytes(compressed)
    scene_ref = {'path': str(SCENE), 'sha256': hashlib.sha256(compressed).hexdigest(), 'decoded_sha256': hashlib.sha256(decoded).hexdigest()}
    new_geometry = {'revision': report['revision'], 'viewer': KEY, 'receipt': receipt, 'scene': scene_ref}
    index = {'schema': 'bolted_frame_development_revisions/v6', 'candidate': previous['candidate'],
        'evidence_candidate': previous['evidence_candidate'], 'geometry': new_geometry,
        'hardware_model': {'revision': report['revision'], 'receipt': receipt, 'actual_parts_verified': False, 'analysis_pass_transferred': False},
        'shop': {'revision': report['revision'], 'geometry': receipt, 'result': receipt,
            'packet': 'docs/bolted-frame-development/builder-plan.md', 'shop_planning_only': True},
        'conditional_frame_evaluation': None, 'panel_Hillman_resolution_deferred': True,
        'fabrication_released': False, 'climbing_released': False, 'selected_baseline': previous['selected_baseline'],
        'optional_grid': {**previous['optional_grid'], 'applies_to_current_geometry': False},
        'preceding_revision': previous}
    for path, digest in pins.items():
        assert sha(path) == digest, path
    assert (ROOT/INDEX).read_bytes() == index_bytes, 'current index changed during publication'
    (ROOT/PACKET).mkdir()
    for name in files:
        with (ROOT/PACKET/name).open('xb') as stream:
            stream.write((stage/name).read_bytes())
    with (ROOT/SCENE).open('xb') as stream:
        stream.write(compressed)
    (ROOT/INDEX).write_bytes(encoded(index))
    print(json.dumps({'geometry': new_geometry, 'counts': report['counts'],
        'permanent_bytes': sum((ROOT/PACKET/name).stat().st_size for name in files)+len(compressed)}), flush=True)


if __name__ == '__main__':
    publish()
