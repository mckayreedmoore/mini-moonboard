"""Publish the separate unselected matching-rear trial from frozen sources."""
from __future__ import annotations

import argparse
import gzip
import json
import math
import re
from pathlib import Path

from scripts.publish_packer_free_viewer import bound, encode, local_path, sha
from scripts.publish_v11_shorter_bolts_results import CASES, FALSE_FLAGS, LOAD
from scripts.publish_v11_shorter_bolts_viewer import (
    PROVENANCE as PARENT_PATH,
)
from scripts.publish_v11_shorter_bolts_viewer import (
    PROVENANCE_SHA as PARENT_SHA,
)

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'eoere-v11-matching-rear-bolts-preview'
BASE = 'site/eoere-v11-matching-rear-bolts-'
SCENE, RESULTS, PROVENANCE, OVERLAY = (BASE+suffix for suffix in ('scene.json.gz', 'results.json', 'provenance.json', 'overlay.mjs'))
PROVENANCE_SHA, OVERLAY_SHA = '9e101e7ea3871299f4dd9b30df5ef799a51423b94863c5b56d431fe8bd0f39b0', 'b399066fac1adbc7bae375d14b134065e3dc087d79b6c7a4454281ff9ed44875'
PUBLIC = 'docs/bolted-frame-development/owner-frame-v11/matching-rear-bolts/'
RAW = 'fea/generated/v11-matching-rear-bolts-v1/'
ANALYSIS = RAW+'mechanics/analysis-v3/'
GEOMETRY = {'path': RAW+'geometry-v1/geometry.json', 'sha256': '28bf006c24fe2c57bd2b2a942f34954ef23a294789fd9676cdf5c49b48b35a48'}
RECEIPT = {'path': PUBLIC+'geometry-receipt.json', 'sha256': 'd9e4fc220a5827c45405faa4e8f4e13066e384ecec30dcb259c66d8b70cf677f'}
PARENT = {'path': PARENT_PATH, 'sha256': PARENT_SHA}
SOURCES = {'response_bank': {'path': PUBLIC+'response-bank.json', 'sha256': 'b364c9b572960a23c6566575abf3b791a326ab5ac35e263a770dd6e2fe891a46'},
           'reference_completion': {'path': PUBLIC+'reference-completion.json', 'sha256': '38eceab51e314607bd94663b7130dc6149167724f70d6f5e034ba939e844adf4'}}
EXPORT = {'path': RAW+'viewer/export-v1/export-manifest.json', 'sha256': 'fd24fa5b62d51bdc6ed17b2333b31ece10f01adea42a5125e46eeeafd63b4257'}
TEMPLATE = RAW+'viewer/overlay-template.mjs'
HOSTS = {'base_side_left', 'base_side_right', 'lumber_leg_left', 'lumber_leg_right'}
AXES = {'proposal_upper_rear_'+side+'_added_half_in' for side in ('left', 'right')}
ROLES = {'head', 'head_washer', 'shaft', 'nut_washer', 'nut'}
COUNTS = {'occupied_parts': 1099, 'bolt_stacks': 114, 'washer_pieces': 228, 'spacer_pieces': 4,
          'Hillman_axes': 66, 'angles': 24, 'sawn_members': 20, 'plywood_cleats': 4, 'panels': 6}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def contract(data):
    require(data['schema'] == 'eoere_v11_matching_rear_scene/v1' and data['key'] == MODEL and data['geometry_source'] == GEOMETRY
            and data['geometry_receipt'] == RECEIPT and data['parent_provenance'] == PARENT and data['counts'] == COUNTS
            and data['part_count'] == 1099 and data['unchanged_mesh_bytes_copied'] == 0, 'Exact own checked geometry and shared parent required')
    require(len(data['replacements']) == 4 and {row['name'] for row in data['replacements']} == HOSTS
            and len(data['reuses']) == 10 and {row['name'] for row in data['reuses']} == {axis+'_'+role for axis in AXES for role in ROLES}
            and len(set(data['all_axis_ids'])) == len(data['all_axis_ids']) == 114 and set(data['new_axis_ids']) == AXES,
            'Only four replacement wood meshes and ten new hardware roles are permitted')
    require(data['geometry_only'] is True and all(data[key] is False for key in
            ('historical_capacity_transferred', 'trial_selected', 'structural_acceptance', 'fabrication_released', 'climbing_released')),
            'The exported geometry remains an unselected trial without inherited acceptance')
    return data


def validate_bank(bank):
    require(bank['schema'] == 'eoere_v11_matching_rear_bolts_response_bank/v1' and bank['candidate_revision'] == 'v11-matching-rear-bolts-v1'
            and bank['physical_geometry'] == GEOMETRY and bank['physical_receipt']['sha256'] == RECEIPT['sha256']
            and bank['physical_receipt']['path'] == RAW+'geometry-v1/checked-receipt-v1.json'
            and bank['analysis_geometry'] == {'path': ANALYSIS+'geometry/geometry.json', 'sha256': '1ee6c3693925e7e2026d7a3b1c79b138f35f4c1640cc90f718ea545f7d407ecc'}
            and bank['load_contract'] == LOAD, 'Own114 geometry, preparation and fixed load contract required')
    rows = bank['cases']
    require(bank['all_six_cases_admitted'] is True and bank['two_independent_replays_per_case'] is True
            and bank['fresh_fields_only'] is True and bank['historical_field_or_force_transfer'] is False
            and bank['admission_gate_N'] == 1e-5 and len(rows) == len(set(bank['case_ids'])) == 6
            and set(bank['case_ids']) == {row['case_id'] for row in rows} == CASES, 'Six own fresh admitted cases required')
    hashes = []
    for row in rows:
        require(row['both_independent_replays_admitted'] is True and type(row['gradient_inf_N']) in (int, float)
                and math.isfinite(row['gradient_inf_N']) and 0 <= row['gradient_inf_N'] <= 1e-5, 'Both replays and finite admitted residual required')
        for key, name in [('field', 'field.json'), ('independent_replay', 'independent-replay.json'), ('independent_plywood_replay', 'independent-replay-plywood.json')]:
            require(row[key]['path'] == ANALYSIS+'four-hosts/'+row['case_id']+'/'+name and re.fullmatch('[a-f0-9]{64}', row[key]['sha256']), 'Own case/replay join required')
            hashes.append(row[key]['sha256'])
    require(len(set(hashes)) == 18 and max(row['gradient_inf_N'] for row in rows) == bank['maximum_gradient_inf_N'] == 2.246134017003243e-6,
            'Own distinct fields/replays and exact maximum required')
    require(all(bank[key] is False for key in ('physical_force_bounds_established', 'structural_acceptance', 'fabrication_released', 'climbing_released')),
            'Admission does not establish complete or physical acceptance')
    return bank


def result_projection(root):
    bank = validate_bank(json.loads(bound(root, SOURCES['response_bank'])))
    completion = json.loads(bound(root, SOURCES['reference_completion']))
    sources = completion['source_bindings']
    require(completion['schema'] == 'v11_matching_rear_fresh_reference_completion/v1' and completion['revision'] == 'v11-matching-rear-bolts-v1'
            and sources['response_bank']['sha256'] == SOURCES['response_bank']['sha256'] and sources['response_bank']['path'] == ANALYSIS+'response-bank.json'
            and sources['physical_geometry'] == GEOMETRY and sources['physical_receipt'] == bank['physical_receipt']
            and sources['analysis_geometry'] == bank['analysis_geometry'] and completion['execution']['historical_trial_forces_or_indices_transferred'] is False,
            'Current reference completion must join the exact own bank and physical/analysis geometry')
    require(all(completion[key] is None for key in ('actual_Cg', 'actual_Cdelta', 'actual_Fe', 'actual_Fy', 'actual_Fyb'))
            and all(completion[key] is False for key in ('complete_joint_qualified', 'structural_acceptance', 'fabrication_released', 'climbing_released')),
            'Actual factors, properties and complete capacity remain unresolved')
    families = {key: {name: row[name] for name in ('maximum', 'above_one_count')} for key, row in completion['families']['outputs'].items()}
    for row in families.values():
        require(math.isfinite(row['maximum']['index']) and row['maximum']['index'] >= 0 and row['maximum']['case_id'] in CASES,
                'Own finite reference summary and case witness required')
    connection = completion['connections']
    rear = completion['rear']
    require(rear['axis_case_states'] == rear['projected_cases_independently_replayed'] == 36 and rear['receiver_case_certificates'] == 72
            and rear['projected_summary']['reference_index_above_one_count'] == 0 and rear['projected_summary']['full_NDS_connection_capacity'] is None,
            'Own36 projected cases and72receiver certificates are conditional material references')
    case_keys = ('case_id', 'gradient_inf_N', 'both_independent_replays_admitted', 'field', 'independent_replay', 'independent_plywood_replay')
    return {'schema': 'eoere_v11_matching_rear_viewer_results/v1', 'model': MODEL, 'revision': completion['revision'],
            'geometry': GEOMETRY, 'geometry_receipt': RECEIPT, 'sources': SOURCES, 'analysis_geometry': bank['analysis_geometry'], 'load_contract': LOAD,
            'cases': [{key: row[key] for key in case_keys} for row in bank['cases']], 'independent_replays': 12,
            'maximum_gradient_inf_N': bank['maximum_gradient_inf_N'], 'family_references': families,
            'connections': {key: connection[key] for key in ('Grade5_F60692_force', 'generic45_force', 'Grade5_F60692_rawport_partition_bounds',
                            'generic45_rawport_partition_bounds', 'individual_Cg_floor_maximum', 'individual_Cg_floor_above_one_count',
                            'standard_Cg_maxima', 'standard_Cg_above_one_counts', 'mixed_plane_maximum', 'mixed_plane_above_one_count',
                            'nominal_singleton_interface_cases', 'remaining_row_application_interface_cases')},
            'rear': {key: rear[key] for key in ('axis_count', 'axis_case_states', 'receiver_case_certificates', 'projected_cases_independently_replayed',
                                              'maximum_case_reference_bracket', 'projected_summary', 'continuous_summary')},
            'unresolved_scope': completion['unresolved_scope'], 'counts': COUNTS, 'trial_selected': False,
            'actual_Cg_adopted': None, 'actual_Cdelta_adopted': None, 'actual_Fyb_adopted': None, 'complete_connection_capacity': None,
            'current_response_computed': True, 'fixed_load_only': True, 'weight_interpolation_available': False,
            'planning_mass_kg': None, **{key: False for key in FALSE_FLAGS}}


def prepare(source_root, root):
    for ref in (PARENT, RECEIPT):
        bound(root, ref)
    export = json.loads(bound(source_root, EXPORT))
    scene_raw = local_path(source_root, RAW+'viewer/export-v1/scene-delta.json.gz').read_bytes()
    require(sha(scene_raw) == export['scene']['sha256'], 'Frozen export scene bytes changed')
    decoded = gzip.decompress(scene_raw)
    data = contract(json.loads(decoded))
    require(sha(decoded) == export['scene']['decoded_sha256'] and export['geometry'] == GEOMETRY and export['receipt'] == RECEIPT,
            'Exact frozen export joins required')
    results_raw = encode(result_projection(root))
    record = {'schema': 'eoere_v11_matching_rear_viewer_provenance/v1', 'model': MODEL, 'geometry': GEOMETRY, 'geometry_receipt': RECEIPT,
              'parent_provenance': PARENT, 'scene': {'path': SCENE, 'sha256': sha(scene_raw), 'decoded_sha256': sha(decoded)},
              'results': {'path': RESULTS, 'sha256': sha(results_raw)}, 'counts': COUNTS, 'source_export': EXPORT,
              'new_wood_meshes': 4, 'translated_hardware_parts': 10, 'unchanged_mesh_bytes_copied': 0,
              'ignored_runtime_dependencies': False, 'trial_selected': False, 'structural_acceptance': False}
    record_raw = encode(record)
    module = local_path(source_root, TEMPLATE).read_text().replace('9e101e7ea3871299f4dd9b30df5ef799a51423b94863c5b56d431fe8bd0f39b0', sha(record_raw))
    require('@@' not in module, 'All final source pins must be present')
    require(data['counts'] == record['counts'], 'Scene census differs')
    return {SCENE: scene_raw, RESULTS: results_raw, PROVENANCE: record_raw, OVERLAY: module.encode()}


def check(root):
    bound(root, {'path': OVERLAY, 'sha256': OVERLAY_SHA})
    record = json.loads(bound(root, {'path': PROVENANCE, 'sha256': PROVENANCE_SHA}))
    bound(root, PARENT)
    receipt = json.loads(bound(root, RECEIPT))
    scene = bound(root, record['scene'])
    data = contract(json.loads(gzip.decompress(scene)))
    require(sha(gzip.decompress(scene)) == record['scene']['decoded_sha256'] and record['geometry'] == GEOMETRY
            and record['parent_provenance'] == PARENT and record['counts'] == data['counts']
            and record['trial_selected'] is False and record['ignored_runtime_dependencies'] is False
            and receipt['geometry'] == GEOMETRY and receipt['counts']['occupied_parts'] == 1099 and receipt['nominal_geometry_clear'] is True,
            'Public own geometry/provenance/receipt joins differ')
    require(bound(root, record['results']) == encode(result_projection(root)), 'The compact own results projection differs')
    return {'status': 'unselected_matching_rear_viewer_verified', 'parts': 1099, 'stacks': 114, 'washers': 228,
            'spacers': 4, 'new_wood_meshes': 4, 'translated_hardware_parts': 10, 'cases': 6, 'independent_replays': 12,
            'ignored_inputs_read': False, 'trial_selected': False, 'structural_acceptance': False}


def publish(source_root, root):
    payloads = prepare(source_root, root)
    for name, raw in payloads.items():
        destination = local_path(root, name)
        require(not destination.exists() or destination.read_bytes() == raw, 'Preserve existing differing file: '+name)
    for name, raw in payloads.items():
        destination = local_path(root, name)
        if not destination.exists():
            with destination.open('xb') as stream:
                stream.write(raw)
    return check(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--source-root', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    print(json.dumps(publish(args.source_root or args.root, args.root) if args.write else check(args.root), indent=2))
