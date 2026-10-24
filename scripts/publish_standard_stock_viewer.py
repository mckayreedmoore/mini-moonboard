"""Compose portable current-stock display assets from frozen exports; no CAD or solve."""
from __future__ import annotations

import argparse
import copy
import gzip
import json
import math
from pathlib import Path

from scripts.publish_eoere_v10 import deterministic_gzip, local_path, sha

MODEL = 'eoere-standard-4x6-top-and-sides-preview'
REVISION = 'v10-standard-4x6-top-and-sides-development-v1'
SCENE = 'site/eoere-standard-stock-scene.json.gz'
STATUS = 'site/eoere-standard-stock-status.json'
PROVENANCE = 'site/eoere-standard-stock-provenance.json'
PROVENANCE_SHA = '5364ab82cf3ae1afc90b5b099376211b06b592c20a3640e73fad44c9291e30ea'
GEOMETRY_SHA = 'c06d790aaed7d915cc729afaf3f5e58c456429c18a79555f1faf182775129a37'
RECEIPT_SHA = 'd9df40fe76e08f008391cb276b8c2136abae09820273b541d10d49b5648d9ef2'
PARENT = {'path': 'site/eoere-v10-scene-13.json.gz', 'sha256': '32abbcfcd2552d3df189ea35ab8c1c49d738f447e0dca5d1596eae310766b99f'}
FROZEN = {
    'top_geometry': {'path': 'fea/generated/v10-standard-top-stock-v1/viewer-proposal/export-v2/scene-delta.json.gz',
                     'sha256': '598e07493e959f785da3f1874456e9d528051f277b9fb81a54ccf8ee6c57c6bb'},
    'side_geometry': {'path': 'fea/generated/v10-standard-side-stock-v1/viewer/export-v1/scene-delta.json.gz',
                      'sha256': 'a63ee4273ddbe54eda092f1c175a79a25741562677e06c922af69c0fb6090184'},
    'results': {'path': 'fea/generated/v10-standard-side-stock-v1/viewer/export-v2/status-manifest.json',
                'sha256': '7d69296b0216a1dd51657dde6316f9609a064c7ec43bacd50dce215c75eda717'},
}
CASES = {'a12-forward', 'a12-left', 'a12-rear', 'k12-right', 'k12-rear', 'a1-rear'}
COUNTS = {'Hillman_axes': 66, 'angles': 24, 'bolt_stacks': 116, 'occupied_parts': 1151,
          'panels': 6, 'plywood_cleats': 4, 'sawn_members': 22, 'spacer_pieces': 44}
FALSE_FLAGS = ('structural_acceptance', 'complete_joint_qualified', 'complete_group_qualified', 'top_grid_qualified',
               'physical_force_bounds_established', 'fabrication_released', 'climbing_released', 'purchase_authorized',
               'physical_changes_authorized', 'current_alias_promoted', 'custom_packers_approved', 'old_side_indices_or_group_acceptance_transferred')
DOC_PREFIX = 'docs/bolted-frame-development/owner-frame-v10/standard-side-stock/'
EVIDENCE_SHAS = {'geometry_receipt': RECEIPT_SHA,
                'response_bank': '41f76a1ab0c66a1e5c7056e572f32f5627a11290ce2ed2f3b7e611a72a4a2393',
                'reference_review': 'ff06a91e51028061737743e3f4b873f7ec7a3e4789d1b331dd62cfb66c25419e',
                'diagnostic_inventory': '6282b51057b903d3cc0be8846d899363be04e6bb6094015027b7babc7032ef8f'}


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def bound(root, ref):
    raw = local_path(root, ref['path']).read_bytes()
    if sha(raw) != ref['sha256']:
        raise ValueError('Source bytes differ: '+ref['path'])
    return raw


def rigid(values):
    if not isinstance(values, list) or len(values) != 16 or not all(math.isfinite(x) for x in values) or values[12:] != [0, 0, 0, 1]:
        raise ValueError('Rigid finite matrix required')
    rows = [values[4*i:4*i+3] for i in range(3)]
    if any(abs(sum(a*b for a, b in zip(rows[i], rows[j], strict=True))-(i == j)) > 1e-8 for i in range(3) for j in range(3)):
        raise ValueError('Rigid reuse cannot scale or shear')
    determinant = sum(rows[0][i]*(rows[1][(i+1)%3]*rows[2][(i+2)%3]-rows[1][(i+2)%3]*rows[2][(i+1)%3]) for i in range(3))
    if abs(determinant-1) > 1e-8:
        raise ValueError('Rigid reuse cannot reflect')


def result_contract(status, records):
    if status.get('key') != MODEL or status.get('geometry_revision') != REVISION or status.get('geometry_sha256') != GEOMETRY_SHA:
        raise ValueError('Current result identity differs')
    if any(status.get(flag) is not False for flag in FALSE_FLAGS):
        raise ValueError('Result claim boundary differs')
    if any(status.get(key) is not None for key in ('actual_Cg_adopted', 'actual_Cdelta_adopted', 'complete_connection_capacity')):
        raise ValueError('Actual group factors and complete capacity remain unqualified')
    bank, review, inventory, receipt = (records[name] for name in ('response_bank', 'reference_review', 'diagnostic_inventory', 'geometry_receipt'))
    for name, digest in EVIDENCE_SHAS.items():
        if status['sources'][name]['sha256'] != digest or not status['sources'][name]['path'].startswith(DOC_PREFIX):
            raise ValueError('Portable result source differs')
    for record in records.values():
        if any(record.get(flag) is not False for flag in ('structural_acceptance', 'fabrication_released', 'climbing_released')):
            raise ValueError('Source claim boundary differs')
    if (receipt.get('nominal_geometry_clear') is not True or receipt['checked_geometry']['sha256'] != GEOMETRY_SHA
            or bank['physical_geometry']['sha256'] != RECEIPT_SHA or review['physical_geometry']['sha256'] != RECEIPT_SHA
            or review['response_bank']['sha256'] != EVIDENCE_SHAS['response_bank']
            or review['analysis_geometry'] != bank['analysis_geometry'] or inventory['analysis_geometry'] != bank['analysis_geometry']):
        raise ValueError('Own geometry/bank joins differ')
    load = {'accessory_mass_kg': 25, 'downward_multiplier': 2, 'duration_factor_CD': 1, 'horizontal_force_N': 300, 'weight_lb': 250}
    cases = bank['cases']
    if (bank['load_contract'] != load or review['load_contract'] != load or len(cases) != 6
            or {row['case_id'] for row in cases} != CASES or len({row['field']['sha256'] for row in cases}) != 6
            or set(bank['case_ids']) != CASES or set(review['case_ids']) != CASES or not bank['all_six_cases_admitted']
            or bank['admission_gate_N'] != 1e-5 or bank['historical_force_pass_transferred'] is not False
            or bank['physical_force_bounds_established'] is not False):
        raise ValueError('Six own admitted cases under the retained load contract required')
    for row in cases:
        if (row['both_independent_replays_admitted'] is not True or not math.isfinite(row['gradient_inf_N'])
                or row['gradient_inf_N'] > 1e-5 or row['independent_replay']['sha256'] == row['independent_plywood_replay']['sha256']
                or any(record['field_bindings'][row['case_id']] != row['field'] for record in (review, inventory))):
            raise ValueError('Own field/replay joins differ')
    if bank['maximum_gradient_inf_N'] != max(row['gradient_inf_N'] for row in cases):
        raise ValueError('Gradient maximum differs')
    vector = review['numerical_reference_maxima']['timber_net_shear_torsion']
    if (vector['index'] != 0.9985001243183798 or vector['metric'] != 'maximum_shear_torsion_reference_upper'
            or vector['component'] != 'base_side_left' or vector['above_reference'] is not False
            or any(status['declared_vector_reference'][key] != vector[key] for key in ('index', 'metric', 'component', 'case_id'))):
        raise ValueError('Declared conditional vector criterion differs')
    rows, maxima = inventory['above_reference_case_rows'], inventory['component_maxima']
    if (len(rows) != 15 or inventory['count_above_reference_case_rows'] != 15 or len(maxima) != 8
            or len({row['component'] for row in rows}) != 8 or len({(r['component'], r['criterion'], r['case_id']) for r in rows}) != 15
            or any(r['criterion'] != 'wood_bearing_whole_affine' or not math.isfinite(r['index']) or r['index'] <= 1 for r in rows)
            or any(r['index'] != max(x['index'] for x in rows if x['component'] == r['component']) for r in maxima)
            or review['all_declared_numerical_references_below_one'] is not False):
        raise ValueError('Fifteen diagnostic rows/eight components must remain disclosed')
    return {'load_contract': load, 'case_rows': [{key: row[key] for key in ('case_id', 'field', 'gradient_inf_N', 'both_independent_replays_admitted',
             'independent_replay', 'independent_plywood_replay')} for row in cases], 'maximum_gradient_inf_N': bank['maximum_gradient_inf_N'],
            'admission_gate_N': 1e-5, 'declared_vector_reference': status['declared_vector_reference'],
            'diagnostic_case_rows': 15, 'diagnostic_components': 8, 'actual_Cg_adopted': None,
            'actual_Cdelta_adopted': None, 'complete_connection_capacity': None}


def compose(top, sides, status):
    if top['parent_scene']['sha256'] != PARENT['sha256'] or sides['geometry_source']['sha256'] != GEOMETRY_SHA or sides['part_count'] != 1151:
        raise ValueError('Frozen geometry chain differs')
    meshes = {row['name']: copy.deepcopy(row) for row in top['replacements']}
    if len(meshes) != 11 or {row['name'] for row in sides['replacements']} != {'base_side_left', 'base_side_right'}:
        raise ValueError('Current eleven-mesh selection differs')
    meshes.update({row['name']: copy.deepcopy(row) for row in sides['replacements']})
    reuses, removals = copy.deepcopy(top['reuses']), top['removals']
    if len(reuses) != 128 or len(removals) != 16 or len(set(removals)) != 16 or sides['counts'] != COUNTS:
        raise ValueError('Current reuse/removal/census differs')
    for row in reuses:
        rigid(row['matrix_row_major'])
    names = [*meshes, *(row['name'] for row in reuses), *removals]
    if len(names) != len(set(names)):
        raise ValueError('Current patch identities overlap')
    topologies = {**top['triangle_topologies'], **sides['triangle_topologies']}
    used = {row['mesh']['triangle_topology_sha256'] for row in meshes.values()}
    topology_rows = {key: topologies[key] for key in sorted(used)}
    scene = {'schema': 'eoere_standard_stock_geometry_patch/v1', 'key': MODEL, 'revision': REVISION,
             'parent_scene': {'path': 'eoere-v10-scene-13.json.gz', 'sha256': PARENT['sha256']},
             'parent_part_count': 1167, 'part_count': 1151, 'counts': COUNTS, 'geometry_sha256': GEOMETRY_SHA,
             'geometry_receipt_sha256': RECEIPT_SHA, 'replacements': [meshes[key] for key in sorted(meshes)],
             'reuses': reuses, 'removals': removals, 'triangle_topologies': topology_rows,
             'stack_updates': sides['stack_updates'], 'axis_updates': sides['axis_updates'],
             'screw_axis_updates': top['screw_axis_updates'], 'custom_packers_approved': False,
             'historical_capacity_transferred': False, 'structural_acceptance': False, 'actual_parts_verified': False,
             'complete_joint_qualified': False, 'fabrication_released': False, 'climbing_released': False}
    witnesses = []
    for row in scene['replacements']:
        source = 'side_geometry' if row['name'] in {'base_side_left', 'base_side_right'} else 'top_geometry'
        witnesses.append({'name': row['name'], 'original_export': FROZEN[source], 'mesh_payload_sha256': sha(encode(row['mesh'])),
                          'triangle_topology_sha256': row['mesh']['triangle_topology_sha256'], 'brep_source': row['source']})
    return scene, witnesses


def prepare_payloads(source_root):
    raw_sources = {name: bound(source_root, ref) for name, ref in FROZEN.items()}
    decoded = {name: json.loads(gzip.decompress(raw) if name != 'results' else raw) for name, raw in raw_sources.items()}
    status = decoded['results']
    evidence = {name: json.loads(bound(source_root, ref)) for name, ref in status['sources'].items()}
    contract = result_contract(status, evidence)
    bound(source_root, PARENT)
    scene, witnesses = compose(decoded['top_geometry'], decoded['side_geometry'], status)
    original = encode(scene)
    stored = deterministic_gzip(original)
    manifest = {'schema': 'eoere_standard_stock_viewer_provenance/v1', 'model': MODEL, 'geometry_revision': REVISION,
                'geometry_sha256': GEOMETRY_SHA, 'geometry_receipt_sha256': RECEIPT_SHA, 'counts': COUNTS,
                'parent_scene': PARENT, 'frozen_sources': FROZEN, 'scene': {'path': SCENE, 'sha256': sha(stored),
                'decoded_sha256': sha(original), 'bytes': len(stored)}, 'status': {'path': STATUS, 'sha256': sha(raw_sources['results']),
                'bytes': len(raw_sources['results'])}, 'result_sources': status['sources'], 'result_contract': contract,
                'mesh_sources': witnesses, 'fresh_mesh_payloads': 11, 'rigid_mesh_reuses': 128, 'removed_spacer_parts': 16,
                'unchanged_mesh_bytes_copied': 0, 'ignored_runtime_dependencies': False, 'raw_case_operator_banks_copied': False,
                'producer': 'scripts/publish_standard_stock_viewer.py',
                'documents': [{'label': label, 'path': DOC_PREFIX+name} for label, name in (
                  ('Current geometry receipt', 'geometry-receipt.json'), ('Own six-case response bank', 'response-bank.json'),
                  ('Conditional component references', 'reference-review.json'), ('Retained bearing diagnostics', 'diagnostic-inventory.json'),
                  ('Current numerical methods and open qualifications', 'connection-method-evaluation.json'))],
                **{key: False for key in FALSE_FLAGS}}
    return {SCENE: stored, STATUS: raw_sources['results'], PROVENANCE: encode(manifest)}


def check(root):
    raw = local_path(root, PROVENANCE).read_bytes()
    if PROVENANCE_SHA and sha(raw) != PROVENANCE_SHA:
        raise ValueError('Portable provenance bytes differ')
    manifest = json.loads(raw)
    if manifest.get('schema') != 'eoere_standard_stock_viewer_provenance/v1' or manifest.get('model') != MODEL or manifest.get('counts') != COUNTS:
        raise ValueError('Portable model/census differs')
    if manifest.get('frozen_sources') != FROZEN or any(manifest.get(flag) is not False for flag in FALSE_FLAGS):
        raise ValueError('Frozen source or claim boundary differs')
    bound(root, PARENT)
    stored = bound(root, manifest['scene'])
    original = gzip.decompress(stored)
    if sha(original) != manifest['scene']['decoded_sha256']:
        raise ValueError('Decoded scene differs')
    scene = json.loads(original)
    status = json.loads(bound(root, manifest['status']))
    evidence = {name: json.loads(bound(root, ref)) for name, ref in manifest['result_sources'].items()}
    if result_contract(status, evidence) != manifest['result_contract']:
        raise ValueError('Portable numerical contract differs')
    rows = {row['name']: row for row in scene['replacements']}
    if len(rows) != 11 or len(scene['reuses']) != 128 or len(scene['removals']) != 16:
        raise ValueError('Portable patch census differs')
    for witness in manifest['mesh_sources']:
        row = rows[witness['name']]
        if (sha(encode(row['mesh'])) != witness['mesh_payload_sha256'] or row['source'] != witness['brep_source']
                or row['mesh']['triangle_topology_sha256'] != witness['triangle_topology_sha256']):
            raise ValueError('Original mesh payload witness differs')
    for row in scene['reuses']:
        rigid(row['matrix_row_major'])
    return {'status': 'portable_standard_stock_viewer_verified', 'model': MODEL, 'parts': 1151, 'mesh_payloads': 11,
            'rigid_reuses': 128, 'new_stl_files': 0, 'new_asset_bytes': sum(local_path(root, path).stat().st_size for path in (SCENE, STATUS, PROVENANCE)),
            'ignored_inputs_read': False, 'structural_acceptance': False}


def publish(source_root, root):
    payloads = prepare_payloads(source_root)
    for path, raw in payloads.items():
        destination = local_path(root, path)
        if destination.exists() and destination.read_bytes() != raw:
            raise ValueError('Preserve existing differing file: '+path)
    for path, raw in payloads.items():
        destination = local_path(root, path)
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as stream:
                stream.write(raw)
    return check(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source-root', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    print(json.dumps(publish(args.source_root or args.root, args.root) if args.write else check(args.root), indent=2))
