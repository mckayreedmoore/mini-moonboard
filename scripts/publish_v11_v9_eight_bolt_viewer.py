"""Publish/check the frozen V11 geometry-only viewer; no CAD or mechanics."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from scripts.publish_packer_free_viewer import bound, encode, local_path, sha

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'eoere-v11-v9-eight-bolt-preview'
SCENE = 'site/eoere-v11-v9-eight-bolt-scene.json.gz'
PROVENANCE = 'site/eoere-v11-v9-eight-bolt-provenance.json'
OVERLAY = 'site/eoere-v11-v9-eight-bolt-overlay.mjs'
OVERLAY_SHA = 'ff95c5d61d706f2ff4b64ea55dba3fac9531211222b62268e3d21337f729752e'
PROVENANCE_SHA = '29be7c0dac1813ccf251bb2ead1829db5d1498f3710302a8f22ccabf0eef590b'
EXPORT = {'path': 'fea/generated/v11-v9-eight-bolt-v1/viewer/export-v1/export-manifest.json', 'sha256': 'd6ee18af0f8eeaefd5a9e839d04ea24966a3f105fb5f011e284bf2f0b9ce2a11'}
TEMPLATE = {'path': 'fea/generated/v11-v9-eight-bolt-v1/viewer/overlay-proposal.mjs', 'sha256': '89554a1462d8fba89bf7725ec614426a53cf8dbfce0d76d0b5ed064e87fa1613'}
OWNER = {'path': 'docs/bolted-frame-development/owner-frame-v11/owner-v9-eight-bolt-request.json',
         'sha256': '8704cdfba23c59ea2a56d87bddf8f1123caedfbaad3c5163d6196eda2234fde0'}
V9_SCENE = {'path': 'site/eoere-single-spacer-scene.json', 'sha256': '250f8fb4e6fc965ebf77dc9a5822ece646a3163fb85878d15c265673275f4058'}
V9_LAYOUT = {'path': 'docs/bolted-frame-development/owner-frame-v9/geometry.json',
             'sha256': '29db14a7cb6aaf37e5f65ab23f6c9362b1429456a29d4ca02c0e1d5266af00ef'}
PUBLIC_RECEIPT = {'path': 'docs/bolted-frame-development/owner-frame-v11/geometry-receipt.json',
                  'sha256': '576159eb2dcd791cf1a983165728e173fa594015fd7ab39ed9d69c1cb591a330'}
FLAGS = ('current_response_computed', 'current_own_response_bank_recorded', 'historical_capacity_transferred',
         'complete_joint_qualified', 'complete_group_qualified', 'physical_force_bounds_established', 'structural_acceptance',
         'actual_bond_qualified', 'fabrication_released', 'climbing_released', 'purchase_authorized', 'physical_changes_authorized', 'current_alias_promoted')


def geometry_contract(data):
    if (data.get('schema') != 'eoere_v11_v9_eight_bolt_scene/v1' or data.get('key') != MODEL or data.get('owner_request') != OWNER
            or data.get('parent_scene') != V9_SCENE or data.get('parent_layout') != V9_LAYOUT
            or data.get('geometry_receipt', {}).get('sha256') != PUBLIC_RECEIPT['sha256']
            or data.get('geometry_only') is not True or data.get('analysis_pending') is not True
            or data.get('planning_mass_kg') is not None or any(data.get(flag) is not False for flag in FLAGS)
            or any(key in data for key in ('response_bank', 'case_rows', 'declared_vector_references', 'weight_response', 'load_contract'))):
        raise ValueError('Own geometry-only source/claim contract required')
    counts = data['counts']
    if (counts['bolt_stacks'] != 112 or counts['Hillman_axes'] != 66 or counts['angles'] != 24 or counts['plywood_cleats'] != 4
            or counts['sawn_members'] != 20 or counts['panels'] != 6 or counts['spacer_pieces'] != 24
            or data['part_count'] != 1109 or data['part_count'] != counts['occupied_parts']
            or len(data['stack_updates']) != 112 or len({row['axis_id'] for row in data['stack_updates']}) != 112):
        raise ValueError('Actual V11 physical inventory required')
    joints = data['joint_contract']
    if (joints['physical_bolt_axes'] != 112 or len(joints['cleat_joints']) != 2 or len(joints['top_joints']) != 2
            or len(joints['center_top_joints']) != 2 or joints['outer_top_scope_explicitly_confirmed'] is not True):
        raise ValueError('Confirmed cleat/outer-only top joint contract required')
    for row in joints['cleat_joints']:
        if (row['leaf_count'] != 2 or row['nominal_leaf_thickness_mm'] != 19.05 or row['nominal_combined_thickness_mm'] != 38.1
                or row['outline_unchanged_from_v9'] is not True or any(len(ids) != 4 for ids in row['axis_groups'].values())
                or len(set(row['axis_ids'])) != 8 or row['actual_bond_qualified'] is not False):
            raise ValueError('Actual eight-stack cleat/two-leaf contract required')


def prepare(source_root):
    exported = json.loads(bound(source_root, EXPORT))
    raw = bound(source_root, {'path': 'fea/generated/v11-v9-eight-bolt-v1/viewer/export-v1/'+exported['scene']['path'], 'sha256': exported['scene']['sha256']})
    decoded = gzip.decompress(raw)
    if sha(decoded) != exported['scene']['decoded_sha256']:
        raise ValueError('Decoded frozen display export differs')
    data = json.loads(decoded)
    geometry_contract(data)
    for ref in (OWNER, V9_SCENE, V9_LAYOUT, PUBLIC_RECEIPT):
        bound(source_root, ref)
    provenance = {'schema': 'eoere_v11_v9_eight_bolt_provenance/v1', 'model': MODEL, 'revision': data['revision'],
                  'owner_request': OWNER, 'geometry_sha256': data['geometry_source']['sha256'], 'geometry_receipt': data['geometry_receipt'],
                  'geometry_source': data['geometry_source'], 'clearance_source': data['clearance_source'], 'build_manifest': data['build_manifest'],
                  'parent_scene': V9_SCENE, 'parent_layout': V9_LAYOUT, 'source_export': EXPORT, 'overlay_template': TEMPLATE,
                  'scene': {'path': SCENE, 'sha256': sha(raw), 'decoded_sha256': sha(decoded), 'bytes': len(raw)},
                  'counts': data['counts'], 'joint_contract': data['joint_contract'], 'status': data['status'], 'documents': data['documents'],
                  'geometry_only': True, 'analysis_pending': True, 'planning_mass_kg': None, 'ignored_runtime_dependencies': False,
                  'fresh_mesh_payloads': len(data['replacements']), 'rigid_mesh_reuses': len(data['reuses']), 'unchanged_mesh_bytes_copied': 0,
                  'producer': 'scripts/publish_v11_v9_eight_bolt_viewer.py', **{flag: False for flag in FLAGS}}
    provenance_raw = encode(provenance)
    module = bound(source_root, TEMPLATE).decode().replace('../../../../site/', './')
    for token, value in {'PROVENANCE_SHA': sha(provenance_raw), 'GEOMETRY_SHA': data['geometry_source']['sha256'],
                         'RECEIPT_SHA': data['geometry_receipt']['sha256'], 'SCENE_SHA': sha(raw), 'DECODED_SHA': sha(decoded)}.items():
        module = module.replace('@@'+token+'@@', value)
    if '@@' in module:
        raise ValueError('Unbound source token in final viewer module')
    return {SCENE: raw, PROVENANCE: provenance_raw, OVERLAY: module.encode()}


def check(root):
    bound(root, {'path': OVERLAY, 'sha256': OVERLAY_SHA})
    raw = local_path(root, PROVENANCE).read_bytes()
    if sha(raw) != PROVENANCE_SHA:
        raise ValueError('Frozen V11 provenance bytes differ')
    record = json.loads(raw)
    if (record.get('schema') != 'eoere_v11_v9_eight_bolt_provenance/v1' or record['model'] != MODEL or record['owner_request'] != OWNER
            or record['source_export'] != EXPORT or record['parent_scene'] != V9_SCENE or record['parent_layout'] != V9_LAYOUT
            or record['geometry_only'] is not True or record['analysis_pending'] is not True or record['ignored_runtime_dependencies'] is not False
            or any(record.get(flag) is not False for flag in FLAGS)):
        raise ValueError('Frozen geometry-only metadata/source contract differs')
    for ref in (OWNER, V9_SCENE, V9_LAYOUT, PUBLIC_RECEIPT):
        bound(root, ref)
    scene_raw = bound(root, record['scene'])
    decoded = gzip.decompress(scene_raw)
    if sha(decoded) != record['scene']['decoded_sha256']:
        raise ValueError('Decoded scene bytes differ')
    data = json.loads(decoded)
    geometry_contract(data)
    if (data['geometry_source']['sha256'] != record['geometry_sha256'] or data['geometry_receipt'] != record['geometry_receipt']
            or data['counts'] != record['counts'] or data['joint_contract'] != record['joint_contract']):
        raise ValueError('Public geometry/provenance joins differ')
    return {'status': 'v11_geometry_only_viewer_verified', 'model': MODEL, 'parts': data['part_count'], 'bolt_stacks': 112,
            'fresh_mesh_payloads': len(data['replacements']), 'rigid_mesh_reuses': len(data['reuses']), 'ignored_inputs_read': False,
            'new_site_bytes': sum(local_path(root, path).stat().st_size for path in (SCENE, PROVENANCE, OVERLAY)),
            'analysis_pending': True, 'historical_capacity_transferred': False}


def publish(source_root, root):
    payloads = prepare(source_root)
    for ref in (OWNER, V9_SCENE, V9_LAYOUT, PUBLIC_RECEIPT):
        bound(root, ref)
    for name, raw in payloads.items():
        target = local_path(root, name)
        if target.exists() and target.read_bytes() != raw:
            raise ValueError('Preserve existing differing file: '+name)
    for name, raw in payloads.items():
        target = local_path(root, name)
        if not target.exists():
            with target.open('xb') as stream:
                stream.write(raw)
    return check(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--source-root', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    print(json.dumps(publish(args.source_root or args.root, args.root) if args.write else check(args.root), indent=2))
