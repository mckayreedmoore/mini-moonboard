"""Prepare the combined development viewer and nominal shop tables."""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts import eoere_builder_layout as shop
from scripts.eoere_current_shop_followup import ROOT, csv_bytes, encoded, require, sha
from scripts.eoere_leg_header_revision import DOC, REVISION

FOLDER = DOC/'leg-header-v3'
SCENE = Path('site/eoere-leg-header-v3-scene.json.gz')
KEY = 'eoere-leg-header-frame-development'


def binding(path):
    return {'path': str(Path(path).resolve().relative_to(ROOT)), 'sha256': sha(path)}


def publish(geometry_path, mechanics_path, clearance_path):
    import cadquery as cq

    from scripts.export_wood_joint_wj24_scene import (
        _deduplicate_triangle_topologies,
        _shape_mesh,
    )

    require(not FOLDER.exists() and not SCENE.exists(), 'fresh publication required')
    geometry, mechanics, clearance = [json.loads(p.read_bytes()) for p in (geometry_path, mechanics_path, clearance_path)]
    parent = json.loads(shop.INDEX.read_bytes())
    require(parent['geometry'] == geometry['parent_geometry'] and geometry['revision'] == REVISION,
            'current enclosed parent and combined revision required')
    require(mechanics['geometry'] == binding(geometry_path) == clearance['geometry']
            and clearance['nominal_geometry_clear'] and not clearance['collisions'] and not clearance['missing_candidates'],
            'matched fresh geometry, mechanics and clear occupied receipt required')
    data = shop.load_sources()
    shop.validate(data)
    FOLDER.mkdir()
    profiles = geometry['profiles']
    axes = {r['id']: r for r in geometry['axes']}
    overrides = {r['axis_id']: r for r in geometry['selected_stack_overrides']}
    selected = [{**r, **overrides.get(r['axis_id'], {})} for r in data['selected'] if r['axis_id'] in axes]
    for row in selected:
        a = axes[row['axis_id']]
        spacer = float(a.get('nut_side_spacer_mm', 0.))
        pieces = round(spacer/12.7)
        require(abs(spacer-pieces*12.7) < 1e-8, 'factory spacer lengths differ')
        row.update(nut_side_spacer_mm=spacer, spacer_piece_count=pieces,
                   spacer_piece_length_mm=12.7 if pieces else 0.,
                   selected_spacer_SKU='13731' if pieces else '')
        row['head_side_fitting_ids'] = ';'.join(r['angle_id'] for r in a['attachments'] if np.linalg.norm(np.asarray(r['point'])-a['point_xyz_mm']) < 1e-6)
        row['nut_side_fitting_ids'] = ';'.join(r['angle_id'] for r in a['attachments'] if np.linalg.norm(np.asarray(r['point'])-a['point_xyz_mm']) > 1e-6)
        if row['axis_id'] in overrides:
            row['model_underhead_length_mm'] = a['nominal_under_head_length_mm']
            # Replace every purchase-window field: none may inherit the
            # previous length or omit spacers from the old template row.
            length = float(row['selected_underhead_length_mm'])
            row['minimum_length_mm'] = length-(.06 if length < 100 else .18)*25.4
            row['selected_spacer_SKU'] = '13731'
            row['selected_tip_delta_mm'] = 0.
            stack_min = a['grip_mm']+a['before_plate_mm']+a['after_plate_mm']+a['nut_side_spacer_mm']
            if any(n.startswith('eoere_cleat_') for n in a['receivers']):
                stack_min -= 28.575-27.
            row['minimum_nut_socket_cavity_depth_mm'] = length-stack_min-2*1.6256-8.128
            row['selected_recipe'] = 'head/head_washer/'+('head_plate/' if a['before_plate_mm'] else '')+'receivers/'+('nut_plate/' if a['after_plate_mm'] else '')+'nut_washer/'+('spacer/'*round(a.get('nut_side_spacer_mm', 0)/12.7))+'nut'
            row['reason'] = 'Combined lower-angle/plywood revision; own catalog dimensional window; delivered stack remains unobserved.'
            row['hardware_model_updated'] = True
            row['nominated_smooth_body_target_mm'] = a['before_plate_mm']+2.6416+a['grip_mm']
            row['minimum_body_to_nominated_target_margin_mm'] = float(row['minimum_body_mm'])-row['nominated_smooth_body_target_mm']
            row['body_to_farthest_wood_plate_end_margin_mm'] = row['minimum_body_to_nominated_target_margin_mm']-a['after_plate_mm']
    old_holes = {(r['axis_id'], r['receiver']): r for r in data['holes']}
    holes = []
    paths = {}
    for wall in mechanics['finished_receiver_wall_queries']:
        identity, name = wall['axis_id'], wall['receiver']
        a, g = axes[identity], profiles[name]
        intervals = wall['finished_full_wall_intervals_from_axis_point_mm']
        require(len(intervals) == 1, 'one contiguous issued receiver interval required')
        low, high = intervals[0]
        row = copy.deepcopy(old_holes[(identity, name)])
        p, d = np.asarray(a['point_xyz_mm']), np.asarray(a['direction_xyz'])
        basis, origin = np.asarray(g['basis_grain_u_v_xyz']), np.asarray(g['datum_xyz_mm'])
        for key, value in [('nominal_shaft_diameter_mm', a['diameter_mm']), ('modeled_bore_envelope_diameter_mm', a['bore_diameter_mm']),
                           ('modeled_underhead_length_mm', a['nominal_under_head_length_mm']),
                           ('entry_from_axis_point_mm', low), ('exit_from_axis_point_mm', high), ('saved_full_wall_length_mm', high-low)]:
            row[key] = value
        for j, label in enumerate('xyz'):
            row['axis_point_'+label+'_mm'] = p[j]
            row['axis_direction_'+label+'_unitless'] = d[j]
        for prefix, point in (('axis_point', p), ('entry', p+d*low), ('exit', p+d*high)):
            local = basis@(point-origin)
            for j, label in enumerate('luv'):
                row[prefix+'_in_receiver_'+label+'_mm'] = float(local[j])
        row['source'] = 'Fresh exact finished-wall extraction for '+REVISION
        holes.append(row)
        paths[identity] = paths.get(identity, 0.)+high-low
    drilling = [copy.deepcopy(r) for r in data['drilling'] if r['axis_id'] in axes]
    for row in drilling:
        row['nominal_wood_path_mm'] = paths[row['axis_id']]
        row['minimum_usable_bit_projection_mm'] = paths[row['axis_id']]+float(row['proposed_guide_mm'])+float(row['proposed_backer_travel_mm'])
    members = copy.deepcopy(data['members'])
    for row in members:
        g = profiles[row['member']]
        for key, value in zip(('nominal_blank_length_mm', 'nominal_blank_depth_mm', 'nominal_blank_thickness_mm'), g['blank_mm'], strict=True):
            row[key] = value
        for j, label in enumerate('xyz'):
            row['datum_'+label+'_mm'] = g['datum_xyz_mm'][j]
            for k, coordinate in enumerate('luv'):
                row['basis_'+coordinate+'_'+label+'_unitless'] = g['basis_grain_u_v_xyz'][k][j]
        row['current_finished_source_path'] = g['finished']['path']
        row['current_finished_source_sha256'] = g['finished']['sha256']
    result_data = {'profiles': profiles, 'members': members, 'selected': selected, 'drilling': drilling,
                   'holes': holes, 'expected_bolt_count': 96, 'expected_receiver_count': 112}
    require(len(axes) == len(selected) == len(drilling) == 96 and len(holes) == 112, 'combined shop census differs')
    require(sum(r['spacer_piece_count'] for r in selected) == 24, 'combined spacer inventory differs')
    # Preserve heterogeneous existing worksheet columns without silently
    # dropping the new catalog/spacer margins.
    def worksheet(rows):
        keys = list(dict.fromkeys(k for row in rows for k in row))
        return csv_bytes([{k: row.get(k, '') for k in keys} for row in rows])
    files = {}
    for name, value in [('current_profiles.json', encoded(profiles)), ('members.csv', worksheet(members)),
                        ('hardware-selection.csv', worksheet(selected)), ('drilling-requirements.csv', worksheet(drilling)),
                        ('receiver-holes.csv', worksheet(holes))]:
        path = FOLDER/name
        path.write_bytes(value)
        files[name] = binding(path)
    report = {'schema': 'eoere_leg_header_revision/v3', 'revision': REVISION, 'candidate': parent['evidence_candidate'],
              'status': 'NOMINAL_GEOMETRY_CLEAR_STRENGTH_UNQUALIFIED', 'parent_geometry': parent['geometry'],
              'checked_geometry': binding(geometry_path), 'checked_clearance': binding(clearance_path),
              'fresh_mechanics_inputs': binding(mechanics_path), 'inputs': binding('docs/bolted-frame-development/single-bolt-legs-header-angles-inputs-v3.json'),
              'profile_overrides': {r['id']: profiles[r['id']] for r in geometry['changed_finished_solids'] if r['kind'] == 'timber'},
              'changed_finished_solids': geometry['changed_finished_solids'], 'axes': geometry['axes'],
              'screw_axes': geometry['screw_axes'], 'fitting_poses': geometry['fitting_poses'],
              'removed_axes': geometry['removed_axes'], 'post_row_Z_mm': geometry['post_row_Z_mm'],
              'counts': {'sawn_members': 20, 'plywood_cleats': 2, 'panels': 6, 'angles': 24, 'bolt_stacks': 96,
                         'Hillman_axes': 66, 'receiver_occurrences': 112, 'occupied_parts': 1027, 'spacer_pieces': 24},
              'files': files, 'physical_installation_qualified': False, 'complete_joint_qualified': False,
              'native_FEA_performed': False, 'release': geometry['release'], 'actual_observations': None,
              'source_sha256': {str(Path(__file__).relative_to(ROOT)): sha(__file__)}}
    receipt = FOLDER/'geometry.json'
    receipt.write_bytes(encoded(report))
    replacements = []
    for row in geometry['changed_finished_solids']:
        require(sha(row['path']) == row['sha256'], 'finished shape changed: '+row['id'])
        shape = cq.Shape.importBrep(row['path'])
        fabrication = {'kind': 'bracket' if row['kind'] == 'angle' else row['kind'],
                       'leg_header_revision': REVISION,
                       'dimensions_mm': [row['bounds_xyz_mm'][2*i+1]-row['bounds_xyz_mm'][2*i] for i in range(3)],
                       'description': 'Combined single-leg-bolt/header-angle/plywood development; strength unqualified'}
        if row['kind'] == 'bolt':
            axis = next(a for a in axes.values() if row['id'].startswith(a['id']+'_'))
            role = row['id'][len(axis['id'])+1:]
            fabrication.update(connection_name=axis['id'], hardware_role=role,
                selected_underhead_length_mm=axis['nominal_under_head_length_mm'],
                nominal_underhead_length_mm=axis['nominal_under_head_length_mm'],
                diameter_mm=axis['diameter_mm'], nut_side_spacer_mm=axis['nut_side_spacer_mm'],
                stack_roles=['shaft', 'head', 'head_washer', 'nut_washer',
                             *(['spacer'] if axis['nut_side_spacer_mm'] else []),
                             *(['spacer_2'] if axis['nut_side_spacer_mm'] > 12.7 else []), 'nut'],
                delivered_part_verified=False)
        elif row['id'].startswith('eoere_cleat_'):
            fabrication.update(material='Proposed APA48oc PS1 plywood,5plies minimum; Group1 bearing basis',
                blank_mm=profiles[row['id']]['blank_mm'], panel_strength_axis='worldZ',
                description='Factory8x24inch plywood leaf, nominal1-1/8inch; four bolt holes; material and joint unqualified')
        replacements.append({'id': row['id'], 'name': row['id'], 'mesh': _shape_mesh(shape), 'fabrication': fabrication})
    patch = {'schema': 'eoere_leg_header_patch/v3', 'revision': REVISION, 'key': KEY,
             'parent_scene': parent['geometry']['scene'], 'parent_layout': parent['geometry']['receipt'],
             'layout_report': binding(receipt), 'part_count': 1027, 'replacements': replacements,
             'removals': [identity+'_'+role for identity in geometry['removed_axes'] for role in ('shaft', 'head', 'head_washer', 'nut_washer', 'nut')],
             'release': geometry['release'], 'historical_capacity_transferred': False}
    patch['triangle_topologies'] = _deduplicate_triangle_topologies(replacements)
    decoded = json.dumps(patch, separators=(',', ':'), allow_nan=False).encode()
    SCENE.write_bytes(gzip.compress(decoded, mtime=0))
    publication = {'geometry': {'revision': REVISION, 'viewer': KEY, 'receipt': binding(receipt),
                   'scene': {**binding(SCENE), 'decoded_sha256': hashlib.sha256(decoded).hexdigest()}},
                   'shop': {'revision': REVISION, 'geometry': binding(receipt), 'result': binding(receipt),
                            'packet': 'docs/bolted-frame-development/builder-plan.md', 'shop_planning_only': True,
                            'affected_installation_qualified': False}, 'parent_geometry': parent['geometry']}
    destination = geometry_path.parent/'publication.json'
    destination.write_bytes(encoded(publication))
    print(json.dumps({'publication': str(destination), 'geometry': publication['geometry'],
                      'permanent_bytes': sum(p.stat().st_size for p in FOLDER.iterdir())+SCENE.stat().st_size}), flush=True)
    return result_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('geometry', type=Path)
    parser.add_argument('mechanics', type=Path)
    parser.add_argument('clearance', type=Path)
    args = parser.parse_args()
    publish(args.geometry.resolve(), args.mechanics.resolve(), args.clearance.resolve())
