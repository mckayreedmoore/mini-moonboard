"""Validate a complete versioned v10 delivery without changing historical evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CASES = {'a12-forward', 'a12-left', 'a12-rear', 'k12-right', 'k12-rear', 'a1-rear'}
LOAD = {'weight_lb': 250, 'downward_multiplier': 2, 'horizontal_force_N': 300,
        'accessory_mass_kg': 25, 'duration_factor_CD': 1}
FALSE_FLAGS = ('fabrication_released', 'climbing_released', 'structural_acceptance',
               'complete_joint_qualified', 'physical_force_bounds_established')
REQUIRED = {'geometry', 'clearance', 'response_bank', 'reference_review',
            'joint_applicability', 'viewer_scene', 'readiness', 'builder_plan',
            'hardware_bom', 'cut_plan', 'drill_plan'}


def read_bound(root, ref):
    if not isinstance(ref, dict) or not isinstance(ref.get('path'), str):
        raise TypeError('A repository-relative path/hash binding is required')
    path = Path(ref['path'])
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Binding escapes the repository')
    full = root / path
    actual = hashlib.sha256(full.read_bytes()).hexdigest()
    if actual != ref.get('sha256'):
        raise ValueError('Binding mismatch: '+str(path))
    return full.read_bytes()


def validate(manifest, root):
    if manifest.get('schema') != 'eoere_v10_delivery_bundle/v1':
        raise ValueError('Unknown v10 delivery schema')
    if not isinstance(manifest.get('geometry_revision'), str) or 'v10' not in manifest['geometry_revision']:
        raise ValueError('Explicit v10 revision required')
    if manifest.get('load_contract') != LOAD:
        raise ValueError('Load contract changed')
    if set(manifest.get('case_ids', [])) != CASES or len(manifest['case_ids']) != 6:
        raise ValueError('Exactly the six retained cases are required')
    artifacts = manifest.get('artifacts', {})
    if not REQUIRED <= set(artifacts):
        raise ValueError('Missing delivery artifacts: '+str(sorted(REQUIRED-set(artifacts))))
    for flag in FALSE_FLAGS:
        if manifest.get(flag) is not False:
            raise ValueError('Unqualified delivery claim: '+flag)
    if manifest.get('physical_operations_authorized') is not False:
        raise ValueError('This bundle does not authorize physical operations')
    documents = {}
    for name, ref in artifacts.items():
        raw = read_bound(root, ref)
        if ref['path'].endswith('.json'):
            documents[name] = json.loads(raw)
    for name in ('geometry', 'response_bank', 'reference_review', 'joint_applicability', 'readiness'):
        doc = documents[name]
        revision = doc.get('geometry_revision', doc.get('revision'))
        if revision != manifest['geometry_revision']:
            raise ValueError('Artifact revision mismatch: '+name)
        if name not in ('geometry', 'readiness') and doc.get('physical_geometry') != artifacts['geometry']:
            raise ValueError('Artifact physical-geometry mismatch: '+name)
        for flag in ('fabrication_released', 'climbing_released', 'structural_acceptance'):
            if doc.get(flag) is not False:
                raise ValueError('Artifact claim boundary: '+name+'/'+flag)
    for name in ('response_bank', 'reference_review'):
        doc = documents[name]
        if set(doc.get('case_ids', [])) != CASES or len(doc['case_ids']) != 6:
            raise ValueError('Artifact case mismatch: '+name)
        if doc.get('load_contract') != LOAD:
            raise ValueError('Artifact load mismatch: '+name)
    bank = documents['response_bank']
    if bank.get('all_six_cases_admitted') is not True:
        raise ValueError('Six cases are not admitted')
    if bank.get('historical_force_pass_transferred') is not False:
        raise ValueError('Historical force transfer is forbidden')
    if len(bank.get('cases', [])) != 6 or {r.get('case_id') for r in bank['cases']} != CASES:
        raise ValueError('Response-bank rows mismatch')
    field_refs = {}
    for row in bank['cases']:
        if row.get('both_independent_replays_admitted') is not True:
            raise ValueError('Unadmitted replay: '+row['case_id'])
        for key in ('field', 'independent_replay', 'independent_plywood_replay'):
            read_bound(root, row[key])
        field_refs[row['case_id']] = row['field']
    if documents['reference_review'].get('field_bindings') != field_refs:
        raise ValueError('Reference review does not use the same six fields')
    if documents['reference_review'].get('response_bank') != artifacts['response_bank']:
        raise ValueError('Reference response-bank join differs')
    preparation = manifest.get('preparation_source_bindings', {})
    helper = 'scripts/eoere_load_parameters.py'
    if helper not in preparation:
        raise ValueError('Load parameterization dependency is not frozen')
    for name, digest in preparation.items():
        read_bound(root, {'path': name, 'sha256': digest})
    if manifest.get('extra_top_bolt_duties', {}).get('added_axis_ids') is None:
        raise ValueError('Requested top-bolt duties must be explicit')
    if not isinstance(manifest.get('remaining_numerical_exceedances'), list):
        raise TypeError('Remaining numerical comparisons must be explicit')
    if not isinstance(manifest.get('unresolved_qualifications'), list):
        raise TypeError('Physical qualification gaps must be explicit')
    return {'status': 'validated_conditional_delivery', 'geometry_revision': manifest['geometry_revision'],
            'artifacts_checked': len(artifacts), 'cases_checked': 6,
            'remaining_numerical_exceedances': manifest['remaining_numerical_exceedances'],
            'fabrication_released': False, 'climbing_released': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(validate(json.loads(args.manifest.read_bytes()), args.root.resolve()), indent=2))
