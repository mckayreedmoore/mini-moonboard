"""Publish the frozen packer-free geometry preview without CAD or force results."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from scripts.publish_eoere_v10 import local_path, sha

MODEL = 'eoere-packer-free-standard-stock-preview'
REVISION = 'v10-packer-free-flush-return-far-row-only-v1'
STATUS = 'Packer-free standard 4×6 geometry trial · results pending. 112 bolt stacks, 24 angles and 66 Hillman screws. Nominal occupied clearance checked; complete connections and actual installation remain unqualified. No fabrication or climbing release.'
SCENE = 'site/eoere-packer-free-scene.json.gz'
EXPORT = 'site/eoere-packer-free-export.json'
PROVENANCE = 'site/eoere-packer-free-provenance.json'
PROVENANCE_SHA = '6730ce627aa2a44c1048d357b4d36dbdd379127cf75e0f6df0fd1a08a9e57ca0'
GEOMETRY_SHA = '9510653b41d2c0c710f4eea02c9867c44367cd2909d6b3af56716c74cfd68bde'
RECEIPT = {'path': 'docs/bolted-frame-development/owner-frame-v10/packer-free/geometry-receipt.json',
           'sha256': '73b097d9bcc364748ca08f897fca38cc2bdb7869cc04586e6706afb9b9d3d527'}
PARENT = {'path': 'site/eoere-standard-stock-provenance.json',
          'sha256': '5364ab82cf3ae1afc90b5b099376211b06b592c20a3640e73fad44c9291e30ea'}
FROZEN_EXPORT = {'path': 'fea/generated/v10-packer-free-v1/viewer/export-v1/viewer-manifest.json',
                 'sha256': 'e19aa1ac5dacde0d9346dd76ecdf3eb5f24740e8ab321a96d943371d5f4c8944'}
FROZEN_SCENE = {'path': 'fea/generated/v10-packer-free-v1/viewer/export-v1/scene-delta.json.gz',
                'sha256': 'd411401ab67f5d29ce509800fcb0beac0dfed26188b90fc0af76bc05fa2ddd07'}
DECODED_SHA = '5bd6dc85faa6a764a5abd37327d8813870b98e3be00ffe678dc848daebb6cd61'
CLEARANCE_SHA = '94c383b75d1223cc87813bd70a011d26da4e384064dec348b34bc1cf3eae0057'
BUILD_SHA = '04d8fb2f125a5f9f9b9aa75bc47ec3f9d93a631ceb863a2920d4243687df3a94'
COUNTS = {'Hillman_axes': 66, 'angles': 24, 'bolt_stacks': 112, 'occupied_parts': 1125,
          'panels': 6, 'plywood_cleats': 4, 'sawn_members': 20, 'spacer_pieces': 40}
FALSE_FLAGS = ('packers_present', 'current_response_computed', 'current_own_response_bank_recorded',
               'historical_capacity_transferred', 'structural_acceptance', 'complete_joint_qualified',
               'complete_group_qualified', 'top_grid_qualified', 'physical_force_bounds_established',
               'fabrication_released', 'climbing_released', 'purchase_authorized', 'physical_changes_authorized',
               'current_alias_promoted')
DOCUMENTS = [
    {'label': 'Packer-free geometry receipt', 'path': RECEIPT['path']},
    {'label': 'Development status and remaining work', 'path': 'docs/bolted-frame-development/README.md'},
    {'label': 'Owner direction: no wood packers', 'path': 'docs/bolted-frame-development/owner-frame-v10/owner-no-wood-packers-v1.json'},
    {'label': 'Builder scope and holds', 'path': 'docs/bolted-frame-development/builder-plan.md'},
]


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def bound(root, ref):
    raw = local_path(root, ref['path']).read_bytes()
    if sha(raw) != ref['sha256']:
        raise ValueError('Source bytes differ: '+ref['path'])
    return raw


def geometry_contract(export, scene, receipt):
    if (export.get('schema') != 'eoere_packer_free_preview/v1' or export.get('key') != MODEL
            or export.get('revision') != REVISION or export.get('matched_results_pending') is not True
            or export.get('current_alias_promoted') is not False or export['scene']['sha256'] != FROZEN_SCENE['sha256']
            or export['scene']['decoded_sha256'] != DECODED_SHA or export['receipt']['sha256'] != RECEIPT['sha256']):
        raise ValueError('Frozen geometry-only export differs')
    if (scene.get('schema') != 'eoere_packer_free_scene_delta/v1' or scene.get('key') != MODEL or scene.get('revision') != REVISION
            or scene.get('counts') != COUNTS or scene.get('part_count') != 1125 or scene.get('matched_results_pending') is not True
            or any(scene.get(flag) is not False for flag in FALSE_FLAGS if flag != 'top_grid_qualified')
            or scene['parent_provenance'] != PARENT or scene['geometry_source']['sha256'] != GEOMETRY_SHA
            or scene['geometry_receipt']['sha256'] != RECEIPT['sha256'] or scene['clearance_source']['sha256'] != CLEARANCE_SHA
            or scene['build_manifest']['sha256'] != BUILD_SHA or len(scene['reuses']) != 42 or len(scene['removals']) != 26
            or len(scene['replacements']) != 1 or scene['replacements'][0]['name'] != 'base_rail_top'
            or len(scene['stack_updates']) != 112 or scene['unchanged_mesh_bytes_copied'] != 0):
        raise ValueError('Packer-free delta/source contract differs')
    if (receipt.get('nominal_geometry_clear') is not True or receipt.get('revision') != REVISION
            or receipt['checked_geometry']['sha256'] != GEOMETRY_SHA or receipt['checked_clearance']['sha256'] != CLEARANCE_SHA
            or receipt['counts']['occupied_parts_checked'] != 1125 or receipt['counts']['bolts'] != 112
            or receipt['counts']['panel_screw_axes'] != 66 or receipt['counts']['angles'] != 24
            or receipt['counts']['spacer_pieces'] != 40
            or any(receipt.get(flag) is not False for flag in ('structural_acceptance', 'fabrication_released', 'climbing_released'))):
        raise ValueError('Checked nominal geometry receipt differs')


def prepare_payloads(source_root):
    export_raw, scene_raw = (bound(source_root, ref) for ref in (FROZEN_EXPORT, FROZEN_SCENE))
    decoded = gzip.decompress(scene_raw)
    if sha(decoded) != DECODED_SHA:
        raise ValueError('Frozen decoded delta differs')
    scene, export = json.loads(decoded), json.loads(export_raw)
    receipt = json.loads(bound(source_root, RECEIPT))
    geometry_contract(export, scene, receipt)
    manifest = {'schema': 'eoere_packer_free_viewer_provenance/v1', 'model': MODEL, 'geometry_revision': REVISION,
                'geometry_sha256': GEOMETRY_SHA, 'geometry_receipt': RECEIPT, 'checked_clearance_sha256': CLEARANCE_SHA,
                'build_manifest_sha256': BUILD_SHA, 'parent_provenance': PARENT, 'counts': COUNTS,
                'source_export_manifest': FROZEN_EXPORT, 'source_scene': FROZEN_SCENE,
                'frozen_export': {'path': EXPORT, 'sha256': sha(export_raw), 'bytes': len(export_raw)},
                'scene': {'path': SCENE, 'sha256': sha(scene_raw), 'decoded_sha256': DECODED_SHA, 'bytes': len(scene_raw)},
                'status': STATUS, 'geometry_only': True, 'matched_results_pending': True,
                'nominal_geometry_clear': True, 'actual_Cg_adopted': None, 'actual_Cdelta_adopted': None,
                'complete_connection_capacity': None, 'fresh_mesh_payloads': 1, 'rigid_mesh_reuses': 42,
                'removed_parts': 26, 'unchanged_mesh_bytes_copied': 0, 'ignored_runtime_dependencies': False,
                'raw_case_operator_banks_copied': False, 'producer': 'scripts/publish_packer_free_viewer.py',
                'documents': DOCUMENTS, **{flag: False for flag in FALSE_FLAGS}}
    return {SCENE: scene_raw, EXPORT: export_raw, PROVENANCE: encode(manifest)}


def check(root):
    raw = local_path(root, PROVENANCE).read_bytes()
    if PROVENANCE_SHA and sha(raw) != PROVENANCE_SHA:
        raise ValueError('Portable provenance bytes differ')
    manifest = json.loads(raw)
    if (manifest.get('schema') != 'eoere_packer_free_viewer_provenance/v1' or manifest.get('model') != MODEL
            or manifest.get('geometry_revision') != REVISION or manifest.get('geometry_sha256') != GEOMETRY_SHA
            or manifest.get('geometry_receipt') != RECEIPT or manifest.get('parent_provenance') != PARENT
            or manifest.get('counts') != COUNTS or manifest.get('source_export_manifest') != FROZEN_EXPORT
            or manifest.get('source_scene') != FROZEN_SCENE or manifest.get('status') != STATUS
            or manifest.get('geometry_only') is not True or manifest.get('matched_results_pending') is not True
            or any(manifest.get(flag) is not False for flag in FALSE_FLAGS)
            or any(manifest.get(key) is not None for key in ('actual_Cg_adopted', 'actual_Cdelta_adopted', 'complete_connection_capacity'))):
        raise ValueError('Portable geometry-only contract differs')
    bound(root, PARENT)
    export_raw, scene_raw = (bound(root, manifest[name]) for name in ('frozen_export', 'scene'))
    decoded = gzip.decompress(scene_raw)
    if (sha(export_raw) != FROZEN_EXPORT['sha256'] or sha(scene_raw) != FROZEN_SCENE['sha256']
            or sha(decoded) != DECODED_SHA or manifest['scene']['decoded_sha256'] != DECODED_SHA):
        raise ValueError('Frozen asset bytes differ')
    geometry_contract(json.loads(export_raw), json.loads(decoded), json.loads(bound(root, RECEIPT)))
    return {'status': 'portable_packer_free_geometry_verified', 'model': MODEL, 'parts': 1125, 'bolt_stacks': 112,
            'mesh_payloads': 1, 'rigid_reuses': 42, 'removed_parts': 26, 'new_stl_files': 0,
            'new_asset_bytes': sum(local_path(root, name).stat().st_size for name in (SCENE, EXPORT, PROVENANCE)),
            'ignored_inputs_read': False, 'matched_results_pending': True, 'structural_acceptance': False}


def publish(source_root, root):
    payloads = prepare_payloads(source_root)
    bound(root, PARENT)
    bound(root, RECEIPT)
    for name, raw in payloads.items():
        destination = local_path(root, name)
        if destination.exists() and destination.read_bytes() != raw:
            raise ValueError('Preserve existing differing file: '+name)
    for name, raw in payloads.items():
        destination = local_path(root, name)
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
