"""Assess unchanged Eoere structural evidence without a solve or a remedy.

The thread calculation bounds possible thread/runout occupancy beyond minimum
catalog smooth body. It does not identify actual threads or calculate capacity.
"""

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = Path('docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1')
PACKET = DOC / 'selected-hardware-v1'
SHOP = DOC / 'shop-assembly-v1/extended-cleat-followup-v1'
CURRENT_SHOP = SHOP / 'current-model-followup-v1'
COMPONENTS = Path('fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-component-results-v1/summary.json')
NDS_PDF = Path('docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache/chapter12-2024-awc-20260911.pdf')
NDS_SHA256 = '53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f'
NDS_URL = 'https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    require(type(value) in (str, int, float), 'Expected a finite dimension')
    result = float(value)
    require(math.isfinite(result), 'Expected a finite dimension')
    return result


def potential_thread_fraction(low, high, minimum_body):
    """Intersect a bearing interval with the region beyond guaranteed smooth body."""
    low, high, minimum_body = map(number, (low, high, minimum_body))
    require(0 <= low < high and minimum_body >= 0, 'Invalid bearing/body interval')
    length = high - max(low, min(high, minimum_body))
    return length, length / (high - low)


def thread_inventory(selections, stacks, receivers):
    """Join all wood intervals to the selected underhead datum, including plates."""
    selected = {row['axis_id']: row for row in selections}
    original = {row['axis_id']: row for row in stacks}
    require(len(selected) == len(selections) == len(original) == len(stacks), 'Duplicate or missing stack')
    require(selected.keys() == original.keys(), 'Stack inventories differ')
    by_axis = defaultdict(list)
    for row in receivers:
        by_axis[row['axis_id']].append(row)
    require(by_axis.keys() == selected.keys(), 'Receiver axis inventories differ')
    result = []
    for axis, row in selected.items():
        old, layers = original[axis], by_axis[axis]
        names = row['receiver_member_ids'].split(';')
        require(len(names) == len(layers) == len({r['receiver'] for r in layers})
                and set(names) == {r['receiver'] for r in layers}, 'Receiver member inventories differ')
        require(row['receiver_member_ids'] == old['receiver_member_ids'], 'Receiver identities changed')
        body = number(row['minimum_body_mm'])
        require(body <= number(row['selected_underhead_length_mm']), 'Body exceeds selected bolt length')
        washer = number(old['catalog_each_washer_max_mm'])
        head_plate = number(old['head_side_plate_mm'])
        nut_plate = number(old['nut_side_plate_mm'])
        require(min(washer, head_plate, nut_plate) >= 0, 'Negative fitting dimension')
        origin = min(number(r['entry_from_axis_point_mm']) for r in layers)
        offset = washer + head_plate - origin
        measured = []
        for layer in sorted(layers, key=lambda r: number(r['entry_from_axis_point_mm'])):
            low = number(layer['entry_from_axis_point_mm']) + offset
            high = number(layer['exit_from_axis_point_mm']) + offset
            length, fraction = potential_thread_fraction(low, high, body)
            require(abs(high - low - number(layer['saved_full_wall_length_mm'])) < 1e-5,
                    'Saved receiver wall interval differs')
            measured.append({'receiver': layer['receiver'], 'underhead_interval_mm': [low, high],
                             'bearing_length_mm': high - low,
                             'potential_thread_or_runout_mm': length,
                             'potential_thread_or_runout_fraction': fraction})
        far = max(layer['underhead_interval_mm'][1] for layer in measured) + nut_plate
        require(abs(body - far - number(row['body_to_farthest_wood_plate_end_margin_mm'])) < 1e-5,
                'Selected far-interface datum differs')
        maximum = max(layer['potential_thread_or_runout_fraction'] for layer in measured)
        disposition = ('POTENTIAL_OCCUPANCY_EXCEEDS_QUARTER' if maximum > .25 + 1e-9 else
                       'POTENTIAL_OCCUPANCY_WITHIN_QUARTER' if maximum > 1e-9 else
                       'NOMINAL_SMOOTH_BODY_COVERS_WOOD')
        result.append({'axis_id': axis, 'selected_underhead_length_mm': number(row['selected_underhead_length_mm']),
                       'minimum_body_mm': body, 'maximum_head_washer_mm': washer,
                       'head_plate_mm': head_plate, 'nut_plate_mm': nut_plate,
                       'members': measured, 'maximum_potential_fraction': maximum,
                       'catalog_envelope_disposition': disposition,
                       'actual_thread_fraction': None, 'current_capacity': None})
    return result


def reference_comparisons(summary):
    """Retain own-case witnesses; never combine actions or transfer their passes."""
    rows, other_disclosures = [], []
    for case in summary['cases']:
        label = case['case_id']
        coarse = case['coarse']['findings']
        head = coarse['generic_screw_references']['generic_head_ratio_CD1']
        rows.append({'case': label, 'family': 'generic_screw_head_CD1',
                     'ratio': head['generic_head_ratio_CD1'], 'witness': head})
        withdrawal = coarse['generic_screw_references']['generic_withdrawal_required_effective_thread_mm_CD1']
        rows.append({'case': label, 'family': 'generic_required_thread_over_gross_penetration_CD1',
                     'ratio': withdrawal['generic_withdrawal_required_effective_thread_mm_CD1'] /
                              withdrawal['gross_nominal_length_after_panel_mm'], 'witness': withdrawal})
        for panel in coarse['panels']['per_panel']:
            for family, comparison in panel['section_components'].items():
                rows.append({'case': label, 'family': 'panel_' + family + '_CD1',
                             'ratio': comparison['sampled_ratio_CD1'],
                             'witness': {'panel': panel['panel'], **comparison}})
        rich = case['rich']['findings']
        for scenario in rich['steel_scenarios']:
            comparison = scenario['summary']['radius_conditioned_heel_component_with_gravity']['worst']
            rows.append({'case': label, 'family': 'heel_' + scenario['comparison']['id'],
                         'ratio': comparison['conditional_combined_yield_reference_ratio'],
                         'witness': comparison})
        other_disclosures.append({
            'case': label,
            'generic_head_all_reported_exceedance_axis_ids': coarse['generic_screw_references']['generic_CD1_head_exceedance_axis_ids'],
            'timber_unadjusted_exceedance_axis_ids': rich['timber']['summary']['unadjusted_exceedance_axis_ids'],
            'timber_Cdelta0p5_Cg1_CD1_unadopted_sensitivity': {
                'exceedance_axis_ids': rich['timber']['summary']['Cdelta0p5_Cg1_CD1_sensitivity_exceedance_axis_ids'],
                'own_worst_component': rich['timber']['summary']['worst_component']},
            'shaft_first_yield_reference_exceedances': rich['shaft']['first_yield_reference_exceedances'],
            'washer_reference_diagnostics': rich['washers']['exceeded_reference_diagnostics'],
            'steel_reported_exceedances': [{
                'scenario': scenario['comparison']['id'],
                'categories': {name: category['exceedances'] for name, category in scenario['summary'].items()
                               if category['exceedance_count'] > 0},
            } for scenario in rich['steel_scenarios']],
        })
    governing = {}
    for row in rows:
        require(math.isfinite(row['ratio']) and row['ratio'] >= 0, 'Invalid saved reference ratio')
        if row['family'] not in governing or row['ratio'] > governing[row['family']]['ratio']:
            governing[row['family']] = row
    return {'recorded_geometry': summary['current_geometry'],
            'applies_to_current_model': False,
            'governing_own_case_witnesses': list(governing.values()),
            'saved_reference_exceedances': [row for row in rows if row['ratio'] > 1],
            'other_saved_exceedance_and_sensitivity_disclosures': other_disclosures,
            'complete_joint_resistance': None}


def build(root=ROOT):
    paths = [DOC / 'occupied-selected-hardware-v1.json', CURRENT_SHOP / 'result.json',
             CURRENT_SHOP / 'hardware-selection.csv', SHOP / 'receiver-holes.csv',
             SHOP / 'bolt-stacks.csv', PACKET / 'mechanics-review.json',
             CURRENT_SHOP / 'mechanical-change-review.json', COMPONENTS, NDS_PDF,
             Path(__file__).resolve().relative_to(ROOT)]
    pins = {str(path): digest(root / path) for path in paths}
    require(pins[str(NDS_PDF)] == NDS_SHA256, 'Pinned NDS source differs')
    read = lambda path: json.loads((root / path).read_text())
    geometry = read(paths[0])
    require(geometry['revision'] == 'eoere-selected-purchase-hardware-v1'
            and geometry['wood_screw_revision'] == 'eoere-raised-kicker-screws-v1', 'Wrong current revision')
    for path in (CURRENT_SHOP / 'result.json', CURRENT_SHOP / 'hardware-selection.csv'):
        require(pins[str(path)] == geometry['direct_source_sha256'][str(path)], 'Current source binding differs')
    shop = read(CURRENT_SHOP / 'result.json')
    require(shop['revision'] == 'eoere-raised-kicker-screws-v1', 'Wrong shop revision')
    for name in ('receiver-holes.csv', 'bolt-stacks.csv'):
        require(pins[str(SHOP / name)] == shop['reused_files'][name]['sha256'], 'Reused source binding differs')
    require(pins[str(CURRENT_SHOP / 'hardware-selection.csv')] == shop['files']['hardware-selection.csv']['sha256'],
            'Hardware table binding differs')
    tables = []
    for path in (CURRENT_SHOP / 'hardware-selection.csv', SHOP / 'bolt-stacks.csv', SHOP / 'receiver-holes.csv'):
        with (root / path).open(newline='') as stream:
            tables.append(list(csv.DictReader(stream)))
    require([len(table) for table in tables] == [100, 100, 120], 'Current inventory count differs')
    threads = thread_inventory(*tables)
    require({row['axis_id'] for row in threads} == {row['axis_id'] for row in geometry['selected_stacks']},
            'Current hardware axis inventory differs')
    for row in tables[0]:
        require(all(value == '' for key, value in row.items() if key.startswith('Actual') or key == 'Disposition'),
                'Assessment must preserve unobserved hardware fields')
    previous = read(PACKET / 'mechanics-review.json')
    areas = previous['nominal_projection_areas_mm2']
    changes = read(CURRENT_SHOP / 'mechanical-change-review.json')
    summary = read(COMPONENTS)
    # Reuse the issued JSON-only authenticator, including its full source union.
    # It imports no force producer, matrix assembly, CAD or native solver.
    helper = COMPONENTS.with_name('summarize.py')
    expected = summary['source_sha256'][str(helper)]
    require(digest(root / helper) == expected, 'Saved summary helper differs')
    pins[str(helper)] = expected
    manifest = summary['source_manifest']
    require(digest(root / manifest['path']) == manifest['sha256'], 'Saved source manifest differs')
    pins[manifest['path']] = manifest['sha256']
    spec = importlib.util.spec_from_file_location('eoere_saved_component_summary', root / helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.build(read(manifest['path']), manifest) == summary, 'Saved component summary differs')
    references = reference_comparisons(summary)
    result = {
        'schema': 'eoere_current_structural_assessment/v1',
        'geometry_revision': geometry['wood_screw_revision'], 'hardware_revision': geometry['revision'],
        'extra_grid': False, 'source_sha256': pins,
        'assessment_status': 'BOUNDED_ASSESSMENT_COMPLETE_ACCEPTANCE_UNRESOLVED',
        'thread_method': {'source_url': NDS_URL, 'source_sha256': NDS_SHA256,
                          'locator': 'Printed p.95, PDF page17, NDS12.3.7.1-12.3.7.2',
                          'threshold': .25,
                          'basis': 'Potential thread/runout region after minimum smooth body, maximum head washer, nominal finished bearing intervals. Lg is not substituted for actual thread start.',
                          'interpretation': 'An upper-bound fraction above one quarter prevents guaranteeing the full-body D exception from these catalog windows alone. It does not prove actual thread exposure or a strength failure. Root diameter or detailed threaded-part mechanics needs its own verified inputs; no remedy is attempted.'},
        'thread_catalog_envelope_counts': dict(Counter(row['catalog_envelope_disposition'] for row in threads)),
        'thread_stacks': threads,
        'spacer_contact': {'nominal_projection_areas_mm2': areas,
                           'mean_pressure_mpa_per_1000n_centered_axial_force': {name: 1000 / area for name, area in areas.items()},
                           'limits': 'Ideal projected contact only, before chamfers, coating, eccentricity or washer bending. Unit-force pressure is not an allowable stress or a current axial action.',
                           'current_axial_actions': None, 'current_resistance': None},
        'raised_screw_placement': changes['screw_placement'],
        'current_unresolved_modes': previous['unresolved'],
        'preceding_reference_comparisons': references,
        'authenticated_preceding_source_union': summary['verified_source_union'],
        'restraint_and_finished_sections': 'Current simultaneous member/shaft/screw actions, cut-aware sections, panel participation and justified restraint/applicability are missing. Earlier gross-stock and fixed-rear-leg response cannot establish these current criteria.',
        'current_response_computed': False, 'historical_pass_transferred': False,
        'native_solve_performed': False, 'cad_rebuilt': False,
        'remedies_attempted': False, 'geometry_or_hardware_changed': False,
        'actual_build_fit_work_excluded_by_owner': True, 'actual_observations': None,
        'structural_acceptance': False, 'fabrication_released': False, 'climbing_released': False,
    }
    require(all(digest(root / path) == expected for path, expected in pins.items()), 'Sources changed during assessment')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = build()
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
