"""Publish the unselected 108-bolt display from one frozen rail export and own results."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from scripts.publish_packer_free_results import LOAD
from scripts.publish_packer_free_viewer import bound, encode, local_path, sha

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'eoere-packer-free-center-far-row-preview'
REVISION = 'v10-packer-free-center-far-row-only-development-v1'
BASE = 'fea/generated/v10-packer-free-center-far-row-v1/'
RUN = BASE+'reference-readiness/runs/analysis-v2-center-far-row-v4/'
SCENE = 'site/eoere-center-far-row-scene.json.gz'
PROVENANCE = 'site/eoere-center-far-row-provenance.json'
PROVENANCE_SHA = '0d869dfe6e6cbc80c5fdd7683f469486d732f56710411c6e8f524a9fad6382f2'
GEOMETRY_SHA = 'ef95c7e8c6727e3fd4051c2de0ff70e8947466ec15d2809d5df5a67c309330bd'
SOURCES = {
    'geometry_receipt': {'path': BASE+'geometry-v1/checked-receipt-v2.json', 'sha256': '608451425411001f14c768d5ee881fdf686d1d2296749b921390f0a1b7689a79'},
    'response_bank': {'path': BASE+'mechanics/analysis-v2/response-bank.json', 'sha256': '0175c7882231a24a35fd44b15b21919143f6c6a2abc9e91e623a9b6215c70bdd'},
    'reference_provenance': {'path': RUN+'authoritative-reference-provenance-v1.json', 'sha256': '9b8608dc66ec0e41aa12077ced0a6d92ab8487acc1337a69bd12f343097c96ac'},
    'display_export': {'path': BASE+'viewer/export-v1/export-manifest.json', 'sha256': '86ec5f9538a05b0ea0e8c9bb5286931500d92f82ec92bd08015c968d30b97e66'},
}
PARENT = {'path': 'site/eoere-packer-free-results.json', 'sha256': '5b78a854d61d0e15dd7ddf84cb7c8b70e052443c4e79571d429158e970d1b6fc'}
COUNTS = {'Hillman_axes': 66, 'angles': 24, 'bolt_stacks': 108, 'occupied_parts': 1105,
          'panels': 6, 'plywood_cleats': 4, 'sawn_members': 20, 'spacer_pieces': 40, 'washers': 216}
STATUS = ('Unselected trial · center far rows · 108 bolts. Own six-case conditional references recorded; complete connection audits unfinished. '
          'Declared vector section references: left 0.924493, right 0.881709, top 0.591046, header 0.588552. '
          'Fifteen bearing diagnostic rows across eight bolts remain above trial references. Actual Cg/Cdelta and complete capacity remain unqualified. '
          'No fabrication or climbing release.')
FLAGS = ('geometry_adopted', 'current_alias_promoted', 'structural_acceptance', 'complete_joint_qualified', 'complete_group_qualified',
         'complete_connection_audits_finished', 'top_grid_qualified', 'physical_force_bounds_established', 'fabrication_released',
         'climbing_released', 'purchase_authorized', 'physical_changes_authorized', 'historical_capacity_transferred')


def relative_ref(ref):
    p = Path(ref['path'])
    return {'path': str(p.relative_to(ROOT)) if p.is_absolute() else str(p), 'sha256': ref['sha256']}


def prepare(source_root):
    receipt, bank, references, exported = (json.loads(bound(source_root, SOURCES[name]))
                                           for name in ('geometry_receipt', 'response_bank', 'reference_provenance', 'display_export'))
    if (receipt.get('nominal_geometry_clear') is not True or receipt['checked_geometry']['sha256'] != GEOMETRY_SHA
            or bank['physical_geometry']['sha256'] != SOURCES['geometry_receipt']['sha256']
            or references['six_case_bank'] != SOURCES['response_bank'] or bank['load_contract'] != LOAD
            or bank['geometry_revision'] != REVISION or bank['all_six_cases_admitted'] is not True
            or bank['admission_gate_N'] != 1e-5 or bank['historical_force_pass_transferred'] is not False
            or len(bank['cases']) != 6 or not all(row['both_independent_replays_admitted'] is True for row in bank['cases'])):
        raise ValueError('Own checked geometry and admitted six-case sources required')
    stored = bound(source_root, {'path': BASE+'viewer/export-v1/'+exported['scene']['path'], 'sha256': exported['scene']['sha256']})
    decoded = gzip.decompress(stored)
    if sha(decoded) != exported['scene']['decoded_sha256']:
        raise ValueError('Frozen decoded rail export differs')
    scene = json.loads(decoded)
    if scene['counts'] != COUNTS or scene['geometry_source']['sha256'] != GEOMETRY_SHA or scene['parent_results'] != PARENT:
        raise ValueError('Own scene/parent inventory differs')
    family_sources = {name: relative_ref(row['family_output']) for name, row in references['family_reference_maxima'].items()}
    families = {name: json.loads(bound(source_root, ref)) for name, ref in family_sources.items()}
    for family in families.values():
        if family['load_contract'] != LOAD or family['analysis_geometry']['sha256'] != bank['analysis_geometry']['sha256']:
            raise ValueError('Own reference-family geometry/load required')
        if any(family['field_bindings'][row['case_id']] != row['field'] for row in bank['cases']):
            raise ValueError('Own field bindings required in each reference family')
    vectors = {name: max((row for row in families['timber_net_shear_torsion']['rows'] if row['component'] == name), key=lambda row: row['index'])
               for name in ('base_side_left', 'base_side_right', 'base_rail_top', 'base_header')}
    diagnostics = [row for row in families['wood_bearing_whole_affine']['rows'] if row['index'] > 1]
    if len(diagnostics) != 15 or len({row['component'] for row in diagnostics}) != 8:
        raise ValueError('Retain all current trial-bearing disclosures')
    maxima = {name: {key: row['maximum'][key] for key in ('component', 'case_id', 'index')}
              for name, row in references['family_reference_maxima'].items()}
    provenance = {'schema': 'eoere_center_far_row_viewer/v1', 'model': MODEL, 'revision': REVISION, 'geometry_sha256': GEOMETRY_SHA,
                  'sources': SOURCES, 'family_sources': family_sources, 'parent_results': PARENT, 'counts': COUNTS,
                  'scene': {'path': SCENE, 'sha256': sha(stored), 'decoded_sha256': sha(decoded), 'bytes': len(stored)},
                  'load_contract': LOAD, 'analysis_geometry': bank['analysis_geometry'], 'cases': bank['cases'],
                  'admission_gate_N': 1e-5, 'maximum_gradient_inf_N': bank['maximum_gradient_inf_N'],
                  'declared_vector_references': vectors, 'declared_family_maxima': maxima,
                  'bearing_diagnostic_case_rows': 15, 'bearing_diagnostic_components': 8,
                  'diagnostic_factor_basis': 'Receiver-signature 1/n diagnostic factors; not actual Cg or complete capacity.',
                  'actual_Cg_adopted': None, 'actual_Cdelta_adopted': None, 'complete_connection_capacity': None,
                  'status': STATUS, 'unselected_trial': True, 'current_own_response_bank_recorded': True,
                  'fresh_mesh_payloads': 1, 'removed_parts': 20, 'unchanged_mesh_bytes_copied': 0, 'ignored_runtime_dependencies': False,
                  'producer': 'scripts/publish_center_far_row_viewer.py', **{flag: False for flag in FLAGS}}
    return {SCENE: stored, PROVENANCE: encode(provenance)}


def check(root):
    raw = local_path(root, PROVENANCE).read_bytes()
    if PROVENANCE_SHA and sha(raw) != PROVENANCE_SHA:
        raise ValueError('Unselected trial provenance bytes differ')
    record = json.loads(raw)
    if (record['schema'] != 'eoere_center_far_row_viewer/v1' or record['model'] != MODEL or record['sources'] != SOURCES
            or record['geometry_sha256'] != GEOMETRY_SHA or record['counts'] != COUNTS or record['unselected_trial'] is not True
            or any(record.get(flag) is not False for flag in FLAGS) or record['ignored_runtime_dependencies'] is not False):
        raise ValueError('Unselected trial source/claim contract differs')
    bound(root, PARENT)
    scene_raw = bound(root, record['scene'])
    if sha(gzip.decompress(scene_raw)) != record['scene']['decoded_sha256']:
        raise ValueError('Decoded scene bytes differ')
    return {'status': 'unselected_center_far_row_viewer_verified', 'parts': 1105, 'bolt_stacks': 108, 'new_mesh_payloads': 1,
            'new_asset_bytes': len(raw)+len(scene_raw), 'ignored_inputs_read': False, 'geometry_adopted': False}


def publish(source_root, root):
    payloads = prepare(source_root)
    bound(root, PARENT)
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
