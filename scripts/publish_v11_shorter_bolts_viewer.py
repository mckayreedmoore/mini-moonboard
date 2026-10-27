"""Publish/check the gated shorter-bolt geometry delta; no CAD or mechanics."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from scripts.publish_packer_free_viewer import bound, encode, local_path, sha

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'eoere-v11-shorter-bolts-preview'
SCENE = 'site/eoere-v11-shorter-bolts-scene.json.gz'
PROVENANCE = 'site/eoere-v11-shorter-bolts-provenance.json'
OVERLAY = 'site/eoere-v11-shorter-bolts-overlay.mjs'
OVERLAY_SHA = '57c6031a1208b5d2aeee4a739913238f97b890e2068ada0b2faeeb5b88f53f8e'
PROVENANCE_SHA = '92a70022aa149945bac3a548f7b68af1cf03e30c7223f51fd38cd3a28bbc7cbc'
EXPORT = {'path': 'fea/generated/v11-shorter-bolts-v1/viewer/export-v1/export-manifest.json', 'sha256': 'dc9aeb2818e011072a8006fa8177dcf6339628f3099d55cf8f0c5e6891ab405b'}
TEMPLATE = {'path': 'fea/generated/v11-shorter-bolts-v1/viewer/overlay-proposal.mjs', 'sha256': '33118fc2c56aca00333182a1976b0a76d806978f21894a64170ad08f91916775'}
PARENT = {'path': 'site/eoere-v11-v9-eight-bolt-provenance.json', 'sha256': '29be7c0dac1813ccf251bb2ead1829db5d1498f3710302a8f22ccabf0eef590b'}
OWNER = {'path': 'docs/bolted-frame-development/owner-frame-v11/owner-shorter-bolt-exemption.json', 'sha256': 'e9b7942904ad9a8f24d0b79d3e07f40814b42f0591ffd1dd9dc4255cb4a599e7'}
RECEIPT = {'path': 'docs/bolted-frame-development/owner-frame-v11/shorter-bolts/geometry-receipt.json', 'sha256': 'cc2a1688270cd56a36176ff1957ef769d1a84c54eba8c8d255d2b65ec8bcfee9'}
FLAGS = ('current_response_computed', 'current_own_response_bank_recorded', 'historical_capacity_transferred', 'complete_joint_qualified',
         'complete_group_qualified', 'physical_force_bounds_established', 'structural_acceptance', 'fabrication_released', 'climbing_released',
         'purchase_authorized', 'physical_changes_authorized', 'current_alias_promoted')


def contract(data):
    if (data.get('schema') != 'eoere_v11_shorter_bolt_scene/v1' or data.get('key') != MODEL
            or data.get('parent_provenance') != PARENT or data.get('owner_exemption') != OWNER
            or data.get('geometry_receipt', {}).get('sha256') != RECEIPT['sha256']
            or data.get('part_count') != 1089 or data['counts']['bolt_stacks'] != 112 or data['counts']['spacer_pieces'] != 4
            or data.get('geometry_only') is not True or data.get('analysis_pending') is not True
            or data.get('planning_mass_kg') is not None or any(data.get(key) is not False for key in FLAGS)
            or any(key in data for key in ('response_bank', 'case_rows', 'load_contract', 'force_only', 'standard_cg', 'weight_response'))):
        raise ValueError('Own shorter-bolt geometry-only contract required')
    if (len(data['removals']) != 20 or len(data['replacements']) != 20 or len(data['reuses']) != 20
            or len(set(data['all_axis_ids'])) != 112 or len(data['stack_updates']) != 20):
        raise ValueError('Exactly 20 sleeve removals,20 short shafts,20 translated nuts and 112 current stacks required')


def prepare(root):
    exported = json.loads(bound(root, EXPORT))
    raw = bound(root, {'path': str(Path(EXPORT['path']).parent / exported['scene']['path']), 'sha256': exported['scene']['sha256']})
    decoded = gzip.decompress(raw)
    if sha(decoded) != exported['scene']['decoded_sha256']:
        raise ValueError('Frozen decoded shorter-bolt export differs')
    data = json.loads(decoded)
    contract(data)
    for ref in (PARENT, OWNER, RECEIPT):
        bound(root, ref)
    record = {'schema': 'eoere_v11_shorter_bolt_provenance/v1', 'model': MODEL, 'revision': data['revision'],
              'geometry_sha256': data['geometry_source']['sha256'], 'geometry_receipt': RECEIPT,
              'clearance_source': data['clearance_source'], 'build_manifest': data['build_manifest'], 'owner_exemption': OWNER,
              'parent_provenance': PARENT, 'source_export': EXPORT, 'overlay_template': TEMPLATE,
              'scene': {'path': SCENE, 'sha256': sha(raw), 'decoded_sha256': sha(decoded), 'bytes': len(raw)},
              'counts': data['counts'], 'changed_stack_count': 20, 'removed_sleeves': 20,
              'fresh_shaft_meshes': 20, 'translated_nut_meshes': 20, 'unchanged_mesh_bytes_copied': 0,
              'geometry_only': True, 'analysis_pending': True, 'planning_mass_kg': None, 'ignored_runtime_dependencies': False,
              'status': data['status'], 'producer': 'scripts/publish_v11_shorter_bolts_viewer.py', **{key: False for key in FLAGS}}
    provenance = encode(record)
    module = bound(root, TEMPLATE).decode().replace('../../../../site/', './')
    for key, value in {'PROVENANCE_SHA': sha(provenance), 'GEOMETRY_SHA': data['geometry_source']['sha256'],
                       'RECEIPT_SHA': RECEIPT['sha256'], 'SCENE_SHA': sha(raw), 'DECODED_SHA': sha(decoded)}.items():
        module = module.replace('@@'+key+'@@', value)
    if '@@' in module:
        raise ValueError('Final checked sources must replace every preview token')
    return {SCENE: raw, PROVENANCE: provenance, OVERLAY: module.encode()}


def check(root):
    bound(root, {'path': OVERLAY, 'sha256': OVERLAY_SHA})
    record = json.loads(bound(root, {'path': PROVENANCE, 'sha256': PROVENANCE_SHA}))
    for ref in (PARENT, OWNER, RECEIPT):
        bound(root, ref)
    data = json.loads(gzip.decompress(bound(root, record['scene'])))
    contract(data)
    if (record['model'] != MODEL or record['geometry_receipt'] != RECEIPT or record['parent_provenance'] != PARENT
            or record['counts'] != data['counts'] or record['geometry_sha256'] != data['geometry_source']['sha256']
            or sha(encode(data)) != record['scene']['decoded_sha256'] or record['ignored_runtime_dependencies'] is not False):
        raise ValueError('Public shorter-bolt provenance joins differ')
    return {'status': 'shorter_bolt_geometry_only_viewer_verified', 'parts': 1089, 'stacks': 112, 'spacers': 4,
            'ignored_inputs_read': False, 'analysis_pending': True, 'historical_capacity_transferred': False}


def publish(source_root, root):
    payloads = prepare(source_root)
    for ref in (PARENT, OWNER, RECEIPT):
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
