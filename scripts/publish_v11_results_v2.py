"""Add the public standard-Cg and mixed-plane method update to V11 results."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts import publish_v11_results as previous
from scripts.publish_packer_free_viewer import bound, encode, local_path, sha

ASSET = 'site/eoere-v11-results-v2.json'
ASSET_SHA = '53ff172e2607f41eeeabf85519b88ecbaf1beb53bfcc642735e2b48a94f1eb48'
BASE = {'path': previous.ASSET, 'sha256': previous.ASSET_SHA}
STANDARD = {'path': previous.PREFIX+'standard-cg-comparison.json', 'sha256': 'f04eeb1c3b4cb166f92befc77f1c7515d2e8b5800f0a289cb9d13702de404801'}
CRITERION = {'path': previous.PREFIX+'criterion-followthrough.json', 'sha256': 'f71c425ab7aa795183329cc6782924e3f1ee8e28aa644f4ffac2fd27c0e18001'}


def prepare(root):
    base = json.loads(bound(root, BASE))
    previous.check(root)
    standard, criterion = (json.loads(bound(root, ref)) for ref in (STANDARD, CRITERION))
    source = standard['source_bindings']
    previous.require(standard['schema'] == 'v11_standard_Cg_net_lateral_summary/v1'
                     and source['response_bank']['sha256'] == base['sources']['response_bank']['sha256']
                     and source['physical_geometry']['sha256'] == base['geometry_sha256']
                     and source['geometry_receipt'] == base['geometry_receipt'], 'Standard-Cg update must use the same own geometry and force bank')
    cases = {row['case_id']: row for row in base['cases']}
    previous.require(len(source['six_cases']) == 6 and {row['case_id'] for row in source['six_cases']} == cases.keys()
                     and all(all(row[key] == cases[row['case_id']][key]
                     for key in ('field', 'independent_replay', 'independent_plywood_replay')) for row in source['six_cases']),
                     'Standard-Cg update must retain every own field and replay')
    q = standard['qualifications']
    previous.require(standard['no_actual_partition_or_Cg_selected'] is True
                     and all(q[key] is None for key in ('actual_Cg', 'actual_Cdelta', 'actual_Fyb', 'complete_joint_capacity', 'complete_group_pass'))
                     and all(q[key] is False for key in ('structural_acceptance', 'fabrication_released', 'climbing_released', 'physical_failure_inferred')),
                     'Fixed hypotheses cannot adopt physical properties, actualCg or full capacity')
    mixed = criterion['mixed_planes']
    planes, mq = mixed['component_reference_summaries'], mixed['qualification']
    previous.require(criterion['response_bank'] == base['sources']['response_bank']
                     and criterion['physical_geometry']['sha256'] == base['geometry_sha256']
                     and criterion['geometry_receipt'] == base['geometry_receipt'] and criterion['load_contract'] == base['load_contract']
                     and all(mq[key] is None for key in ('actual_Cg', 'actual_Cdelta', 'complete_three_member_capacity', 'complete_group_capacity'))
                     and all(mq[key] is False for key in ('structural_acceptance', 'fabrication_released', 'climbing_released')),
                     'Mixed-plane references cannot become full mixed capacity')
    mixed_projection = {'axes': mixed['counts']['mixed_axes'],
                        'plywood_sawn_plane_references': mixed['counts']['plywood_sawn_pair_plane_references'],
                        'steel_wood_plane_references': mixed['counts']['steel_wood_pair_plane_references'],
                        'plywood_sawn_maximum': planes['plywood_sawn_single_shear_plane']['maximum']['demand_over_Z'],
                        'steel_wood_maximum': planes['steel_wood_single_shear_plane']['maximum']['demand_over_Z'],
                        'above_one': sum(planes[key]['conditional_reference_ratio_above_1_count'] for key in
                                         ('plywood_sawn_single_shear_plane', 'steel_wood_single_shear_plane')),
                        'complete_capacity_qualified': False}
    maxima, counts = standard['maxima'], standard['above_one_counts']
    return {'schema': 'eoere_v11_viewer_results/v2', 'model': previous.MODEL, 'base_results': BASE,
            'geometry_sha256': base['geometry_sha256'], 'response_bank': base['sources']['response_bank'],
            'standard_cg_source': STANDARD, 'criterion_source': CRITERION,
            'standard_cg': {
                'aggregate_directional_index': maxima['aggregate_directional_index']['aggregate_directional_index'],
                'aggregate_directional_flags': counts['aggregate_directional_index'],
                'individual_over_Cg_index': maxima['resolved_individual_extra_conservative_index']['resolved_individual_extra_conservative_index'],
                'individual_over_Cg_flags': counts['resolved_individual_extra_conservative_index'],
                'Fe90_net_floor_index': maxima['aggregate_direction_independent_floor_index']['aggregate_direction_independent_floor_index'],
                'Fe90_net_floor_flags': counts['aggregate_direction_independent_floor_index'],
                'fixed_row_and_area_hypotheses_only': True, 'actual_Cg_selected': False,
            },
            'preserved_raw_port_bounds': {'source': base['sources']['row_comparison'], 'index_upper': base['row_bounds']['conditional_property_maximum'],
                                          'inconclusive_flags': base['row_bounds']['inconclusive_flag_rows'], 'conservative_inconclusive_not_new_method_failures': True},
            'mixed_plane_references': mixed_projection,
            'actual_Cg_adopted': None, 'actual_Cdelta_adopted': None, 'complete_connection_capacity': None,
            'complete_joint_qualified': False, 'structural_acceptance': False, 'fabrication_released': False, 'climbing_released': False,
            'producer': 'scripts/publish_v11_results_v2.py'}


def check(root):
    raw = local_path(root, ASSET).read_bytes()
    previous.require((not ASSET_SHA or sha(raw) == ASSET_SHA) and raw == encode(prepare(root)), 'Method update differs from its exact public sources')
    return {'status': 'portable_v11_results_v2_verified', 'asset_bytes': len(raw), 'ignored_inputs_read': False, 'structural_acceptance': False}


def publish(root):
    raw, path = encode(prepare(root)), local_path(root, ASSET)
    previous.require(not path.exists() or path.read_bytes() == raw, 'Preserve existing differing file: '+ASSET)
    if not path.exists():
        with path.open('xb') as stream:
            stream.write(raw)
    return check(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    print(json.dumps(publish(args.root) if args.write else check(args.root), indent=2))
