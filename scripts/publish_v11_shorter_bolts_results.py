"""Project the source-authored shorter-bolt results without reading raw runs."""
from __future__ import annotations

import argparse
import gzip
import json
import math
import re
from pathlib import Path

from scripts.publish_packer_free_viewer import bound, encode, local_path, sha
from scripts.publish_v11_shorter_bolts_viewer import (
    MODEL,
    PROVENANCE,
    PROVENANCE_SHA,
    RECEIPT,
)

ROOT = Path(__file__).resolve().parents[1]
ASSET = 'site/eoere-v11-shorter-bolts-results.json'
ASSET_SHA = '1997d3a0fb2309e6e1e9f9233c401658db8b1d235228a06d2712f634e55f52b5'
OVERLAY = 'site/eoere-v11-shorter-bolts-results.mjs'
OVERLAY_SHA = '593994c3da69eb8de52258e9c855f6d86f40f1aab841259ce773eba349079419'
PREFIX = 'docs/bolted-frame-development/owner-frame-v11/shorter-bolts/'
SOURCES = {
    'response_bank': {'path': PREFIX+'response-bank.json', 'sha256': '0ac9bb41342279c536e955e30bc2b5588e07c235843186820982e7a60455c35c'},
    'reference_review': {'path': PREFIX+'reference-review.json', 'sha256': '9a95d840a81205e2ef6c9cb6924f8b0f27811339b4eaceff9359d0833cf70c72'},
}
GEOMETRY = '73ce1f19ce97959d3867984cc813c178895b50212128fce6a976548ad6bce4c8'
ANALYSIS = 'fea/generated/v11-shorter-bolts-v1/mechanics/analysis-v3/'
CASES = {'a12-forward', 'a12-left', 'a12-rear', 'k12-right', 'k12-rear', 'a1-rear'}
LOAD = {'accessory_mass_kg': 25, 'downward_multiplier': 2, 'duration_factor_CD': 1, 'horizontal_force_N': 300, 'weight_lb': 250}
FALSE_FLAGS = ('historical_capacity_transferred', 'complete_joint_qualified', 'complete_group_qualified', 'physical_force_bounds_established',
               'actual_property_adopted', 'structural_acceptance', 'purchase_authorized', 'fabrication_released', 'climbing_released',
               'physical_changes_authorized', 'current_alias_promoted')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def validate_bank(bank):
    require(bank.get('schema') == 'eoere_v11_shorter_bolts_response_bank/v1' and bank.get('geometry_revision') == 'v11-shorter-bolts-v1'
            and bank['physical_geometry']['sha256'] == GEOMETRY and bank['physical_receipt'] == RECEIPT
            and bank['analysis_geometry']['path'] == ANALYSIS+'geometry/geometry.json'
            and bank['analysis_geometry']['sha256'] == '56b543fdc83ce40bcd2088431bc6caf15f0b491f8297d91b8e0926c38b2f8596'
            and bank['load_contract'] == LOAD, 'Own shorter geometry, preparation and fixed load contract required')
    rows = bank['cases']
    require(bank['all_six_cases_admitted'] is True and bank['fresh_fields_only'] is True and bank['historical_force_or_field_transfer'] is False
            and bank['admission_gate_N'] == 1e-5 and len(rows) == 6 and len(set(bank['case_ids'])) == 6
            and set(bank['case_ids']) == {row['case_id'] for row in rows} == CASES, 'Six own admitted fresh cases required')
    refs = []
    for row in rows:
        require(row['both_independent_replays_admitted'] is True and type(row['gradient_inf_N']) in (float, int)
                and math.isfinite(row['gradient_inf_N']) and 0 <= row['gradient_inf_N'] <= 1e-5,
                'Both independent admitted replays and finite residuals required')
        for key, filename in [('field', 'field.json'), ('independent_replay', 'independent-replay.json'),
                              ('independent_plywood_replay', 'independent-replay-plywood.json')]:
            require(row[key]['path'] == ANALYSIS+'four-hosts/'+row['case_id']+'/'+filename
                    and re.fullmatch('[a-f0-9]{64}', row[key]['sha256']), 'Own field/replay case join differs')
            refs.append(row[key]['sha256'])
    require(len(set(refs)) == 18 and max(row['gradient_inf_N'] for row in rows) == bank['maximum_gradient_inf_N'], 'Distinct fields/replays and current maximum required')
    require(all(bank[key] is False for key in ('structural_acceptance', 'fabrication_released', 'climbing_released', 'physical_force_bounds_established')),
            'Case admission cannot transfer structural or physical acceptance')
    return bank


def prepare(root):
    bank = validate_bank(json.loads(bound(root, SOURCES['response_bank'])))
    review = json.loads(bound(root, SOURCES['reference_review']))
    require(review['revision'] == 'v11-shorter-bolts-v1' and review['physical_geometry']['sha256'] == GEOMETRY
            and review['geometry_receipt'] == RECEIPT and review['response_bank'] == SOURCES['response_bank']
            and review['analysis_geometry'] == bank['analysis_geometry'] and review['load_contract'] == LOAD
            and review['all_six_cases_and_both_replays_admitted'] is True and review['historical_force_or_capacity_result_transferred'] is False,
            'Canonical fresh review must join its exact own bank and inputs')
    require(set(review['fields']) == CASES, 'Only the exact six own reviewed case fields may be projected')
    for row in bank['cases']:
        require(review['fields'][row['case_id']] == row['field'], 'Review must join its own case field')
    require(all(review.get(key) is None for key in ('actual_Cg_adopted', 'actual_Cdelta_adopted', 'complete_connection_acceptance'))
            and all(review[key] is False for key in ('complete_joint_qualified', 'structural_acceptance', 'fabrication_released', 'climbing_released')),
            'No actual group factor or complete acceptance can be invented')
    provenance = json.loads(bound(root, {'path': PROVENANCE, 'sha256': PROVENANCE_SHA}))
    geometry = json.loads(gzip.decompress(bound(root, provenance['scene'])))
    axis_ids = set(geometry['all_axis_ids'])
    presentation = review['viewer_presentation']
    require(isinstance(presentation['status'], str) and presentation['status'].strip(), 'Canonical source-authored result wording required')
    require(isinstance(presentation['reference_flags'], list) and all(isinstance(row['label'], str) and isinstance(row['scope'], str)
            and isinstance(row['status'], str) and (row['count'] is None or type(row['count']) is int and row['count'] >= 0)
            for row in presentation['reference_flags']), 'Explicit reference flag scopes required; unevaluated does not mean zero')
    texts = presentation.get('axis_reference_texts', {})
    require(isinstance(texts, dict) and set(texts) <= axis_ids and all(isinstance(value, str) and value.strip() for value in texts.values()),
            'Only explicit own per-axis conditional/unresolved wording may be displayed')
    require(set(review['member_vector_maxima']) == {'base_side_left', 'base_side_right', 'base_rail_top', 'base_header'},
            'Four own conditional member references required')
    for rows in (review['member_vector_maxima'], review['family_maxima']):
        require(isinstance(rows, dict) and bool(rows), 'Own nonempty reference summary required')
        for row in rows.values():
            require(type(row['index']) in (float, int) and math.isfinite(row['index']) and row['index'] >= 0
                    and row['case_id'] in CASES and isinstance(row['component'], str) and bool(row['component']),
                    'Finite own conditional reference and case witness required')
    case_keys = ('case_id', 'gradient_inf_N', 'both_independent_replays_admitted', 'field', 'independent_replay', 'independent_plywood_replay')
    return {'schema': 'eoere_v11_shorter_bolt_viewer_results/v1', 'model': MODEL, 'geometry_revision': 'v11-shorter-bolts-v1', 'geometry_sha256': GEOMETRY,
            'geometry_receipt': RECEIPT, 'geometry_provenance': {'path': PROVENANCE, 'sha256': PROVENANCE_SHA},
            'sources': SOURCES, 'counts': provenance['counts'], 'analysis_geometry': bank['analysis_geometry'], 'load_contract': LOAD,
            'cases': [{key: row[key] for key in case_keys} for row in bank['cases']], 'independent_replays': 12,
            'all_six_cases_and_both_replays_admitted': True, 'admission_gate_N': 1e-5, 'maximum_gradient_inf_N': bank['maximum_gradient_inf_N'],
            'viewer_presentation': presentation, 'member_vector_maxima': review['member_vector_maxima'], 'family_maxima': review['family_maxima'],
            'actual_Cg_adopted': None, 'actual_Cdelta_adopted': None, 'actual_Fyb_adopted': None, 'complete_connection_capacity': None,
            'geometry_only': False, 'analysis_pending': False, 'current_response_computed': True, 'current_own_response_bank_recorded': True,
            'fixed_load_only': True, 'weight_interpolation_available': False, 'planning_mass_kg': None,
            'producer': 'scripts/publish_v11_shorter_bolts_results.py', **{key: False for key in FALSE_FLAGS}}


def check(root):
    raw = local_path(root, ASSET).read_bytes()
    require(sha(raw) == ASSET_SHA and raw == encode(prepare(root)), 'Presentation differs from the exact canonical fresh review')
    bound(root, {'path': OVERLAY, 'sha256': OVERLAY_SHA})
    return {'status': 'fresh_shorter_bolt_results_verified', 'asset_bytes': len(raw), 'cases': 6, 'independent_replays': 12,
            'reference_flag_families': 7, 'separate_diagnostic_scenario_rows': 110, 'ignored_inputs_read': False, 'structural_acceptance': False}


def publish(root):
    raw, destination = encode(prepare(root)), local_path(root, ASSET)
    require(not destination.exists() or destination.read_bytes() == raw, 'Preserve existing differing file: '+ASSET)
    if not destination.exists():
        with destination.open('xb') as stream:
            stream.write(raw)
    return check(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    print(json.dumps(publish(args.root) if args.write else check(args.root), indent=2))
