"""Publish a small packer-free results presentation from exact public summaries."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from scripts.publish_packer_free_viewer import (
    COUNTS,
    GEOMETRY_SHA,
    MODEL,
    PROVENANCE,
    PROVENANCE_SHA,
    RECEIPT,
    REVISION,
    bound,
    encode,
    local_path,
    sha,
)

ASSET = 'site/eoere-packer-free-results.json'
ASSET_SHA = '5b78a854d61d0e15dd7ddf84cb7c8b70e052443c4e79571d429158e970d1b6fc'
PREFIX = 'docs/bolted-frame-development/owner-frame-v10/packer-free/'
SOURCES = {
    'evaluation': {'path': PREFIX+'evaluation.json', 'sha256': '41863a95230b64a67f3b8aeffd6874fcf75cb81891b4872459d0bd7bb87f4017'},
    'response_bank': {'path': PREFIX+'response-bank.json', 'sha256': '976ee8d8ac593f978edf03d9eda028755751fd69b540fb8a01cdd073a242bdc3'},
}
CASES = {'a12-forward', 'a12-left', 'a12-rear', 'k12-right', 'k12-rear', 'a1-rear'}
LOAD = {'accessory_mass_kg': 25, 'downward_multiplier': 2, 'duration_factor_CD': 1, 'horizontal_force_N': 300, 'weight_lb': 250}
STATUS = ('Packer-free standard 4×6 frame · own six-case references available; complete connections unresolved. '
          'Declared conditional vector section references: left 0.914625, right 0.872071, top 0.613288, header 0.577484. '
          'Fifteen bearing diagnostic rows remain across eight components. Actual Cg/Cdelta and complete capacity remain unqualified. '
          'No fabrication or climbing release.')
FALSE_FLAGS = ('packers_present', 'historical_capacity_transferred', 'structural_acceptance', 'complete_joint_qualified',
               'complete_group_qualified', 'top_grid_qualified', 'physical_force_bounds_established', 'fabrication_released',
               'climbing_released', 'purchase_authorized', 'physical_changes_authorized', 'current_alias_promoted')


def prepare(root):
    evaluation, bank = (json.loads(bound(root, SOURCES[name])) for name in ('evaluation', 'response_bank'))
    receipt = json.loads(bound(root, RECEIPT))
    bound(root, {'path': PROVENANCE, 'sha256': PROVENANCE_SHA})
    if (evaluation.get('schema') != 'eoere_packer_free_matched_reference_evaluation/v1' or evaluation.get('revision') != REVISION
            or bank.get('geometry_revision') != REVISION or evaluation['physical_geometry']['sha256'] != GEOMETRY_SHA
            or receipt['checked_geometry']['sha256'] != GEOMETRY_SHA or receipt.get('nominal_geometry_clear') is not True
            or evaluation['geometry_receipt'] != RECEIPT or bank['physical_geometry']['sha256'] != RECEIPT['sha256']
            or evaluation['response_bank'] != SOURCES['response_bank'] or evaluation['analysis_geometry'] != bank['analysis_geometry']
            or evaluation['load_contract'] != LOAD or bank['load_contract'] != LOAD):
        raise ValueError('Own packer-free source or load contract differs')
    rows = bank['cases']
    if (len(rows) != 6 or {row['case_id'] for row in rows} != CASES or set(bank['case_ids']) != CASES
            or set(evaluation['case_ids']) != CASES or len({row['field']['sha256'] for row in rows}) != 6
            or bank['all_six_cases_admitted'] is not True or evaluation['all_six_cases_and_both_replays_admitted'] is not True
            or bank['admission_gate_N'] != 1e-5 or evaluation['unchanged_admission_gate_N'] != 1e-5
            or bank['historical_force_pass_transferred'] is not False or bank['physical_force_bounds_established'] is not False):
        raise ValueError('Six own admitted cases under the unchanged gate required')
    for row in rows:
        if (row['both_independent_replays_admitted'] is not True or not math.isfinite(row['gradient_inf_N'])
                or not 0 <= row['gradient_inf_N'] <= 1e-5
                or row['independent_replay']['sha256'] == row['independent_plywood_replay']['sha256']):
            raise ValueError('Both independent replays and finite admitted residuals required')
    maximum = max(row['gradient_inf_N'] for row in rows)
    if maximum != bank['maximum_gradient_inf_N'] or maximum != evaluation['maximum_gradient_inf_N']:
        raise ValueError('Own maximum gradient differs')
    diagnostics = evaluation['bearing_diagnostic_rows']
    if (len(diagnostics) != evaluation['bearing_diagnostic_case_rows'] or len(diagnostics) != 15
            or len({row['component'] for row in diagnostics}) != evaluation['bearing_diagnostic_components']
            or evaluation['bearing_diagnostic_components'] != 8
            or any(not math.isfinite(row['index']) or row['index'] <= 1 or row['complete_Cdelta'] is not None for row in diagnostics)
            or evaluation['actual_Cg_adopted'] is not None or evaluation['actual_Cdelta_adopted'] is not None
            or evaluation['complete_connection_acceptance'] is not None):
        raise ValueError('Retained trial diagnostics or unresolved complete capacity differs')
    for record in (evaluation, bank, receipt):
        if any(record.get(flag) is not False for flag in ('structural_acceptance', 'fabrication_released', 'climbing_released')):
            raise ValueError('Source release boundary differs')
    return {'schema': 'eoere_packer_free_viewer_results/v1', 'model': MODEL, 'geometry_revision': REVISION,
            'geometry_sha256': GEOMETRY_SHA, 'geometry_receipt': RECEIPT,
            'geometry_provenance': {'path': PROVENANCE, 'sha256': PROVENANCE_SHA}, 'counts': COUNTS,
            'sources': SOURCES, 'analysis_geometry': bank['analysis_geometry'], 'load_contract': LOAD,
            'cases': rows, 'all_six_cases_and_both_replays_admitted': True, 'admission_gate_N': 1e-5,
            'maximum_gradient_inf_N': maximum, 'declared_vector_references': evaluation['member_vector_maxima'],
            'bearing_diagnostic_case_rows': 15, 'bearing_diagnostic_components': 8,
            'actual_Cg_adopted': None, 'actual_Cdelta_adopted': None, 'complete_connection_capacity': None,
            'status': STATUS, 'geometry_only': False, 'matched_results_pending': False,
            'current_response_computed': True, 'current_own_response_bank_recorded': True,
            'producer': 'scripts/publish_packer_free_results.py', **{flag: False for flag in FALSE_FLAGS}}


def check(root):
    raw = local_path(root, ASSET).read_bytes()
    if (ASSET_SHA and sha(raw) != ASSET_SHA) or raw != encode(prepare(root)):
        raise ValueError('Portable results differ from the exact own public summaries')
    return {'status': 'portable_packer_free_results_verified', 'model': MODEL, 'cases': 6, 'independent_replays': 12,
            'asset_bytes': len(raw), 'ignored_inputs_read': False, 'matched_results_pending': False,
            'structural_acceptance': False}


def publish(root):
    raw, destination = encode(prepare(root)), local_path(root, ASSET)
    if destination.exists():
        if destination.read_bytes() != raw:
            raise ValueError('Preserve existing differing file: '+ASSET)
    else:
        with destination.open('xb') as stream:
            stream.write(raw)
    return check(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    print(json.dumps(publish(args.root) if args.write else check(args.root), indent=2))
