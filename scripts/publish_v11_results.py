"""Publish the small fixed-load V11 presentation from its public records."""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path

from scripts.publish_packer_free_viewer import bound, encode, local_path, sha
from scripts.publish_v11_v9_eight_bolt_viewer import (
    MODEL,
    PROVENANCE,
    PROVENANCE_SHA,
    PUBLIC_RECEIPT,
)

ASSET = 'site/eoere-v11-results.json'
ASSET_SHA = 'd729953d54f9b7f989c5155e115758cbd4845bff0795ab27a496b3188c9e2aaf'
REVISION = 'v11-v9-eight-bolt-v4'
GEOMETRY = 'befcf54de15984fcf05c5ede053d622afb249c0c2279f291ae65f06763b542a7'
PREFIX = 'docs/bolted-frame-development/owner-frame-v11/'
SOURCES = {
    'response_bank': {'path': PREFIX+'response-bank.json', 'sha256': '482d8e5cf5eec0566a7eb637666137350cbf90f1674f909241c78a103f615963'},
    'reference_review': {'path': PREFIX+'reference-review.json', 'sha256': '8551209039282dff8f3fdd2329b2d3d4396972ed1b74a19e0e5287fbb74c53aa'},
    'property_comparison': {'path': PREFIX+'grade5-property-comparison.json', 'sha256': '06e30473a693f1701f65889507590d16d872950137991d5c267d75ba8825d581'},
    'preserved_generic_rows': {'path': PREFIX+'connection-capacity-followthrough.json', 'sha256': 'c19c4a4e7c195dcc7e294090bb0307dd24c87d41adad6ead09eae4a1c0108dcc'},
    'row_comparison': {'path': PREFIX+'grade5-row-comparison.json', 'sha256': 'a61f5592607b972b734b753b53971cb845a174c3b28cf1008232a5f3d1072f88'},
}
LOAD = {'accessory_mass_kg': 25, 'downward_multiplier': 2, 'duration_factor_CD': 1, 'horizontal_force_N': 300, 'weight_lb': 250}
CASES = {'a12-forward', 'a12-left', 'a12-rear', 'k12-right', 'k12-rear', 'a1-rear'}
FALSE_FLAGS = ('historical_capacity_transferred', 'complete_joint_qualified', 'complete_group_qualified', 'physical_force_bounds_established',
               'actual_property_adopted', 'structural_acceptance', 'purchase_authorized', 'fabrication_released', 'climbing_released',
               'physical_changes_authorized', 'current_alias_promoted')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def prepare(root):
    records = {name: json.loads(bound(root, ref)) for name, ref in SOURCES.items()}
    bank, review, prop, generic, rows = (records[name] for name in SOURCES)
    index = json.loads(local_path(root, 'docs/bolted-frame-development/development-revisions.json').read_bytes())
    require(index['geometry']['revision'] == REVISION and index['response_bank'] == SOURCES['response_bank']
            and index['engineering_review'] == SOURCES['reference_review']
            and index['grade5_property_comparison'] == SOURCES['property_comparison'], 'Current development authority differs')
    receipt = json.loads(bound(root, PUBLIC_RECEIPT))
    provenance = json.loads(bound(root, {'path': PROVENANCE, 'sha256': PROVENANCE_SHA}))
    scene = json.loads(gzip.decompress(bound(root, provenance['scene'])))
    axes = {row['axis_id'] for row in scene['stack_updates']}
    require(len(axes) == 112 and receipt['geometry']['sha256'] == GEOMETRY and receipt['nominal_geometry_clear'] is True,
            'The exact frozen112-stack geometry is required')
    require(bank['geometry_revision'] == review['revision'] == REVISION and bank['physical_geometry'] == review['physical_geometry']
            and bank['physical_geometry']['sha256'] == GEOMETRY and bank['physical_receipt'] == review['geometry_receipt'] == PUBLIC_RECEIPT
            and bank['analysis_geometry'] == review['analysis_geometry'] and review['response_bank'] == SOURCES['response_bank']
            and bank['load_contract'] == review['load_contract'] == prop['load_contract'] == LOAD,
            'Own geometry, bank, reference and fixed load joins required')
    require(bank['all_six_cases_admitted'] is True and review['all_six_cases_and_both_replays_admitted'] is True
            and bank['admission_gate_N'] == review['unchanged_admission_gate_N'] == 1e-5
            and set(bank['case_ids']) == set(review['case_ids']) == CASES, 'Six admitted current cases required')
    case_rows = bank['cases']
    require(len(case_rows) == 6 and {row['case_id'] for row in case_rows} == CASES, 'Distinct case rows required')
    refs = []
    for row in case_rows:
        require(row['both_independent_replays_admitted'] is True and math.isfinite(row['gradient_inf_N'])
                and 0 <= row['gradient_inf_N'] <= 1e-5 and review['fields'][row['case_id']] == row['field'],
                'Own field join and both independent admitted replays required')
        refs.extend(row[key]['sha256'] for key in ('field', 'independent_replay', 'independent_plywood_replay'))
    require(len(set(refs)) == 18 and max(row['gradient_inf_N'] for row in case_rows)
            == bank['maximum_gradient_inf_N'] == review['maximum_gradient_inf_N'], 'Distinct fields/replays and exact residual maximum required')
    for item in (prop, rows):
        source = item['source_bindings']
        require(source['response_bank']['sha256'] == SOURCES['response_bank']['sha256']
                and source['physical_geometry']['sha256'] == GEOMETRY and source['geometry_receipt'] == PUBLIC_RECEIPT
                and source['analysis_geometry'] == bank['analysis_geometry'], 'Property scenarios must use the exact same geometry and force bank')
        qualifications = item['qualifications']
        require(all(qualifications[key] is None for key in ('actual_Cg', 'actual_Cdelta', 'actual_Fyb', 'complete_joint_capacity', 'complete_group_pass'))
                and all(qualifications[key] is False for key in ('structural_acceptance', 'fabrication_released', 'climbing_released', 'physical_force_bounds_established')),
                'Property comparisons cannot adopt actual properties or complete capacity')
    require(prop['property_specification']['Fyb_psi'] == 92000 and prop['property_specification']['automatic_actual_property_adoption'] is False
            and prop['source_force_receiver_couples_media_D_Dr_thread_exposure_exactly_unchanged'] is True
            and rows['all_raw_forces_couples_and_row_classifications_unchanged'] is True
            and rows['source_bindings']['explicit_property_comparison']['sha256'] == SOURCES['property_comparison']['sha256'],
            'Conditional92ksi comparison and unchanged forces required')
    require(rows['unchanged_force_only_comparison']['explicit92_maximum'] == prop['explicit92_maximum']
            and rows['unchanged_force_only_comparison']['generic45_maximum'] == prop['generic45_maximum']
            and generic['response_bank']['sha256'] == SOURCES['response_bank']['sha256']
            and rows['source_bindings']['preserved_generic45_summary']['sha256'] == SOURCES['preserved_generic_rows']['sha256'],
            'Current force-only comparisons differ')
    axis_rows = []
    for item in prop['all_two_media_axis_maxima']:
        row = item['explicit92_maximum']
        require(item['axis_id'] == row['axis_id'] and row['case_id'] in CASES and math.isfinite(row['demand_over_Z'])
                and row['demand_over_Z'] >= 0, 'Finite source-bound per-axis conditional reference required')
        axis_rows.append({'axis_id': row['axis_id'], 'case_id': row['case_id'], 'index': row['demand_over_Z'],
                          'governing_mode': row['governing_mode'], 'class_code': row['class_code'],
                          'conditional_steel_Fe_unassigned': row['actual_candidate_steel_Fe_psi'] is None})
    mapped = {row['axis_id'] for row in axis_rows}
    unsupported = prop['unsupported_mixed_axes']
    require(len(axis_rows) == len(mapped) == 88 and len(set(unsupported)) == len(unsupported) == 24
            and mapped.isdisjoint(unsupported) and mapped | set(unsupported) == axes
            and sorted(unsupported) == sorted(rows['unsupported_mixed_axes']), '88mapped and24unsupported axes must partition this geometry')
    require(sum('Fyb92' in row['class_code'] for row in axis_rows) == 84
            and max(row['index'] for row in axis_rows) == prop['explicit92_maximum']['demand_over_Z']
            and len(prop['explicit92_exceedances']) == 0 and len(generic['conditional_case_direction_force_only_exceedances']) == 4,
            'Own force-only maximum, eligibility and comparison disclosures required')
    require(len(rows['explicit92_inconclusive_flags']) == rows['counts']['explicit92_partition_upper_bounds_at_or_above_one'] == 21
            and rows['counts']['explicit92_flagged_interface_groups'] == 10
            and rows['counts']['explicit92_partition_upper_bounds_below_one'] == 231, 'Fresh partition bounds remain inconclusive')
    for record in (bank, review, receipt):
        require(all(record.get(flag) is False for flag in ('structural_acceptance', 'fabrication_released', 'climbing_released')),
                'Release boundary differs')
    require(review['actual_Cg_adopted'] is None and review['actual_Cdelta_adopted'] is None
            and review['complete_connection_acceptance'] is None, 'Complete connection acceptance remains unresolved')
    return {'schema': 'eoere_v11_viewer_results/v1', 'model': MODEL, 'geometry_revision': REVISION,
            'geometry_sha256': GEOMETRY, 'geometry_receipt': PUBLIC_RECEIPT,
            'geometry_provenance': {'path': PROVENANCE, 'sha256': PROVENANCE_SHA}, 'counts': scene['counts'], 'sources': SOURCES,
            'load_contract': LOAD, 'analysis_geometry': bank['analysis_geometry'], 'cases': case_rows,
            'maximum_gradient_inf_N': bank['maximum_gradient_inf_N'], 'admission_gate_N': 1e-5,
            'all_six_cases_and_both_replays_admitted': True, 'independent_replays': 12,
            'member_vector_maxima': review['member_vector_maxima'], 'family_maxima': review['family_maxima'],
            'bearing_diagnostic_case_rows': review['bearing_diagnostic_case_rows'], 'bearing_diagnostic_components': review['bearing_diagnostic_components'],
            'force_only': {'conditional_property_maximum': prop['explicit92_maximum']['demand_over_Z'], 'conditional_property_flag_rows': 0,
                           'generic45_maximum': prop['generic45_maximum']['demand_over_Z'], 'generic45_flag_rows': 4,
                           'mapped_axes': 88, 'Grade5_92ksi_mapped_axes': 84, 'unchanged_A574_mapped_axes': 4,
                           'property_specification': prop['property_specification']},
            'axis_force_only_maxima': sorted(axis_rows, key=lambda row: row['axis_id']), 'unsupported_mixed_axes': sorted(unsupported),
            'row_bounds': {'conditional_property_maximum': rows['explicit92_maximum_inconclusive_partition_bound']['conditional_index_upper'],
                           'inconclusive_flag_rows': 21, 'flagged_interfaces': 10, 'below_one_rows': 231, 'property92_recalculated': True,
                           'preserved_generic45_maximum': rows['generic45_maximum_inconclusive_partition_bound']['conditional_index_upper'],
                           'above_one_is_inconclusive': True, 'complete_group_pass': None},
            'actual_Cg_adopted': None, 'actual_Cdelta_adopted': None, 'actual_Fyb_adopted': None, 'complete_connection_capacity': None,
            'fixed_load_only': True, 'weight_interpolation_available': False, 'planning_mass_kg': None,
            'geometry_only': False, 'analysis_pending': False, 'current_response_computed': True, 'current_own_response_bank_recorded': True,
            'producer': 'scripts/publish_v11_results.py', **{flag: False for flag in FALSE_FLAGS}}


def check(root):
    raw = local_path(root, ASSET).read_bytes()
    require((not ASSET_SHA or sha(raw) == ASSET_SHA) and raw == encode(prepare(root)), 'Results must match exact own public sources')
    return {'status': 'portable_v11_results_verified', 'cases': 6, 'independent_replays': 12, 'mapped_axes': 88,
            'unsupported_mixed_axes': 24, 'inconclusive_row_bounds': 21, 'asset_bytes': len(raw), 'ignored_inputs_read': False,
            'structural_acceptance': False}


def publish(root):
    raw, destination = encode(prepare(root)), local_path(root, ASSET)
    require(not destination.exists() or destination.read_bytes() == raw, 'Preserve existing differing file: '+ASSET)
    if not destination.exists():
        with destination.open('xb') as stream:
            stream.write(raw)
    return check(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    print(json.dumps(publish(args.root) if args.write else check(args.root), indent=2))
