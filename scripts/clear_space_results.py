"""Current actual-force checks for separate floor-rail and exterior-brace candidates.

Retains the selected design's conditional resistance basis and explicit group,
net-section, stability and catalog hardware gates. No ideal-pin substitution.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from fea.compact_assumption_checks import compare_bolt
from fea.compact_rail_checks import assess, hardware_assumptions
from fea.current_response_resistance import (
    VALIDITY,
    angle_comparisons,
    member_comparisons,
)
from scripts.compact_knee_results import sampled_sections
from scripts.compact_splice_results import (
    actual_root_comparison,
    local_groups,
    overlap_contact_check,
)
from scripts.compact_thick_results import base_comparisons

PREFIXES = ('lumber_leg_bolt_', 'knee_bolt_', 'knee_splice_bolt_', 'rail_front_bolt_', 'rail_rear_bolt_')


def floor_bearing_check(report, geometry):
    """Check each explicit floor cell's timber bearing, including open cells."""
    support = report['parameters'].get('floor_rail_support', {})
    names = {'base_floor_left', 'base_floor_right'}
    grid = support.get('grid_yx', ())
    if set(support.get('members', ())) != names or len(grid) != 2 or any(type(v) is not int or v < 2 for v in grid):
        raise ValueError('Require explicit floor-rail support grid and members')
    count = grid[0]*grid[1]
    physical = report['physical_connection_forces']
    bearings = {row['name']:row for row in report['bearings']}
    cells = {}
    for name in sorted(names):
        expected = {f'floor_{name}_{index}' for index in range(count)}
        actual = {n for n,r in physical.items() if r['first'] == name and r['second'] == 'floor' and 'scalar_normal' in r}
        if actual != expected or not expected <= bearings.keys() or f'floor_{name}_friction' not in physical:
            raise ValueError('Floor contact inventory differs from support grid')
        member = geometry['members'][name]
        stations = [point[0] for point in member['profile_sq_mm']]
        area = member['width_mm']*(max(stations)-min(stations))/count
        for n in sorted(expected):
            if not math.isclose(physical[n]['normal_stiffness_fraction'], 1./count, rel_tol=1.e-9):
                raise ValueError('Unexpected floor cell weighting')
            force = max(0., bearings[n]['compression_force_n'])
            cells[n] = {'active':bearings[n]['active'], 'tributary_area_mm2':area,
                'compression_n':force, 'wood_bearing_ratio':force/(area*625*.006894757293168361)}
    return {'cells':cells, 'peak_ratio':max(row['wood_bearing_ratio'] for row in cells.values()),
        'scope':'625 psi perpendicular-grain timber bearing on each modeled equal-area floor cell; not measured floor pressure or friction.'}


def expected_joint_inventory(rows, exterior):
    expected = {}
    for side in ('left', 'right'):
        rim, leg = f'base_side_{side}', f'lumber_leg_{side}'
        pairs = [(rim, leg, 2)]
        if exterior:
            a,b = f'base_knee_{side}_rim', f'base_knee_{side}_leg'
            pairs += [(rim,a,2), (leg,b,2), (a,b,4)]
        else:
            rail = f'base_floor_{side}'
            pairs += [(f'base_post_outer_{side}',rail,2), (leg,rail,2)]
        expected.update({tuple(sorted((a,b))):count for a,b,count in pairs})
    actual = {}
    for row in rows.values():
        pair = tuple(sorted((row['first'],row['second'])))
        actual[pair] = actual.get(pair,0)+1
    return actual == expected


def checks(report, geometry):
    candidate = report.get('candidate')
    if candidate not in {'compact-floor-rail-development', 'compact-exterior-brace-development'} or geometry.get('candidate') != candidate:
        raise ValueError('Require matching clear-space candidate identities')
    if not all(report.get(key) is True for key in VALIDITY):
        return {'candidate':candidate, 'status':'INVALID_RESPONSE_DIAGNOSTIC_ONLY', 'qualified_for_design':False}
    for path, sha in geometry['source_sha256'].items():
        if path.startswith('mini_moonboard/') and report['source_sha256'].get(path) != sha:
            raise ValueError('Native and geometry model sources differ: '+path)
    rows = {name:row for name, row in report['physical_connection_forces'].items() if name.startswith(PREFIXES)}
    members = geometry['members']
    pieces = {f'base_knee_{side}_{end}' for side in ('left', 'right') for end in ('rim', 'leg')} if 'exterior' in candidate else set()
    if {name for name in members if name.startswith('base_knee_')} != pieces:
        raise ValueError('Require all four separate knee members')
    for name in pieces:
        member = members[name]
        if not (math.isclose(member['width_mm'], 88.9 if name.endswith('_rim') else 38.1, abs_tol=1.e-5)
                and math.isclose(member['depth_mm'], 139.7, abs_tol=1.e-5)):
            raise ValueError('Require specified exterior knee sections')
        if any(record['kind'] == 'tab_notch' for record in member['opening_records']):
            raise ValueError('Spliced knee must not inherit the old end notches')
        if report['member_section_demands'][name]['member'].get('native_section_geometry') != 'UNNOTCHED_RECTANGULAR':
            raise ValueError('Require native independent rectangular knee pieces')
        if sum(name in (row['first'], row['second']) for row in rows.values()) != 6:
            raise ValueError('Each knee piece needs two endpoint and four splice bolts')
    bounds = geometry.get('hardware_resistance_bounds_by_name', {})
    hardware = {name:hardware_assumptions(row['diameter_mm'],
        washer_od_mm=bounds.get(name, {}).get('washer_od_mm', row['washer_od_mm']),
        hole_diameter_mm=bounds.get(name, {}).get('washer_hole_diameter_mm', row['hole_diameter_mm']),
        washer_thickness_mm=bounds.get(name, {}).get('washer_thickness_mm', row['washer_thickness_mm']))
        for name, row in geometry['hardware_by_name'].items()}
    stage = assess(report, geometry['geometries_by_bolt_name'], hardware, bolt_prefixes=PREFIXES)
    actual = {name:compare_bolt(row, geometry['geometries_by_bolt_name'][name], stage['bolts'][name]['lateral_ratio'])
              for name, row in rows.items()}
    if set(rows) != set(geometry['geometries_by_bolt_name']) or not expected_joint_inventory(rows, bool(pieces)):
        raise ValueError('Require complete actual bolt inventory at every joint')
    groups = local_groups(rows, geometry, actual)
    root_bolts = {name:actual_root_comparison(stage['bolts'][name],
        geometry['geometries_by_bolt_name'][name], actual[name], hardware[name]['root_diameter_mm']) for name in rows}
    root_groups = {key:max(root_bolts[name]['actual_Ktheta_root_ratio_CD_1'] for name in group['bolt_names'])
                   /group['additional_group_factor_sensitivity'] for key, group in groups.items()}
    root_governing = max(root_bolts, key=lambda name:root_bolts[name]['actual_Ktheta_root_ratio_CD_1'])
    root_summary = {'bolts':root_bolts, 'governing_bolt':root_governing,
        'peak_actual_Ktheta_root_ratio_CD_1':root_bolts[root_governing]['actual_Ktheta_root_ratio_CD_1'],
        'peak_fixed_Ktheta_root_ratio':max(row['fixed_Ktheta_root_ratio'] for row in root_bolts.values()),
        'groups_with_additional_nominal_D_group_reduction':root_groups,
        'peak_with_additional_group_reduction':max(root_groups.values()),
        'passes_individual_and_additional_group_strength':all(value <= 1 for value in root_groups.values()),
        'adopted_as_design_basis':False}
    sections = sampled_sections(report, geometry, rows)
    for name, result in sections.items():
        result.pop('local_splitting_and_notch_resistance_evaluated')
        result['local_group_checks'] = [key for key, value in groups.items() if name in value['members']]
        result['notch_check_applicable'] = False if name in pieces else None
    base = base_comparisons(report, geometry)
    header = member_comparisons(dict(report, member_section_demands={
        'base_header':report['member_section_demands']['base_header']}))['base_header']
    contact = overlap_contact_check(report) if pieces else {'passes':True, 'applicable':False}
    all_local = [m for group in groups.values() for m in group['member_checks'].values()]
    metrics = {'actual_angle_lateral_CD_1':max(v['comparisons']['actual_angle']['ratio_CD_1'] for v in actual.values()),
        'additional_group_reduction_sensitivity':max(g['peak_with_additional_group_reduction'] for g in groups.values()),
        'local_parallel':max(m['wood']['parallel_peak_ratio'] for m in all_local),
        'supplemental_EC5_splitting':max(m['wood']['splitting_peak_ratio'] for m in all_local),
        'minimum_group_spacing_margin_mm':min(m['layout']['minimum_component_spacing_margin_mm'] for m in all_local),
        'sampled_net_member':max(v['sampled_net_peak']['comparison']['conservative_net_section_envelope_ratio'] for v in sections.values()),
        'header_gross_full_length_stability':header['full_length_unbraced_peak']['full_length_unbraced_ratio'],
        'base_bearing_average':max(v['average_header_bearing_ratio'] for v in base.values()),
        'base_bearing_quarter_area_sensitivity':max(v['quarter_area_corner_sensitivity_ratio'] for v in base.values()),
        'base_end_notch_shear':max(v['conservative_notched_shear_ratio'] for v in base.values())}
    criteria = {key:value <= 1. for key, value in metrics.items() if key != 'minimum_group_spacing_margin_mm'}
    criteria.update({'group_spacing':metrics['minimum_group_spacing_margin_mm'] >= 0,
        'catalog_washer_bounds':set(bounds) == set(hardware),
        'directional_edges':stage['metrics']['minimum_directional_edge_end_margin_mm'] >= 0,
        'steel_direct':stage['metrics']['steel_direct'] <= 1,
        'washer_bearing':stage['metrics']['washer_bearing'] <= 1,
        'washer_bending':stage['metrics']['washer_bending'] <= 1,
        'receiver_fit':geometry['receiver_fit_pass'] is True,
        'overlap_contact':contact['passes'],
        'all_machining_represented':all(v['all_openings_represented'] for v in sections.values()),
        'sampled_member_stability':all(section['comparison']['conditional_checked_failure'] is False
                                      for member in sections.values() for section in member['sampled_sections']),
        'all_bolt_centres_sampled':all(not c['unsampled_stations_mm'] for v in sections.values()
                                      for c in v['cut_coverage'] if c['kind'] == 'bolt_bore'),
        'base_end_cut_geometry':all(v['quarter_depth_margin_after_3mm_allowance_mm'] >= 0 for v in base.values())})
    angles = angle_comparisons(report['physical_connection_forces'], report['angle_stations'])
    if len(angles) != 24:
        raise ValueError('Require all 24 commercial angle force records')
    metrics['angle_rated_force_components'] = max(row['rated_force_component_unity'] for row in angles.values())
    criteria['angle_rated_force_components'] = metrics['angle_rated_force_components'] <= 1.
    floor = floor_bearing_check(report, geometry) if not pieces else None
    if floor is not None:
        metrics['floor_rail_wood_bearing'] = floor['peak_ratio']
        criteria['floor_rail_wood_bearing'] = floor['peak_ratio'] <= 1.
    if floor is not None:
        cutouts = report['parameters'].get('native_panel_cutouts', {})
        expected = {'kicker_left':[-1219.2,-1179.1,0.,141.7],
                    'kicker_right':[1179.1,1219.2,0.,141.7]}
        criteria['actual_kicker_cutouts'] = set(cutouts) == set(expected) and all(
            len(cutouts[name]['rectangles_xz_mm']) == 1
            and all(math.isclose(a,b,abs_tol=1.e-6) for a,b in zip(
                cutouts[name]['rectangles_xz_mm'][0], rectangle, strict=True))
            and math.isclose(cutouts[name]['retained_area_mm2'],1219.2*277.-40.1*141.7,abs_tol=1.e-5)
            for name, rectangle in expected.items())
    criteria['component_layouts'] = all(m['layout']['component_spacing_screen_passed'] for m in all_local)
    return {'candidate':candidate, 'status':'LISTED_CONDITIONAL_CRITERIA_MET' if all(criteria.values()) else 'LISTED_CRITERIA_NOT_MET',
        'criteria':criteria, 'metrics':metrics, 'stage_one':stage, 'actual_angle_all_bolts':actual,
        'actual_root':root_summary,
        'joint_groups':groups, 'sampled_net_members':sections, 'base':base, 'header_gross':header,
        'overlap_contact':contact, 'commercial_angles':angles, 'floor_rail_bearing':floor, 'duration_factor_adopted':1.,
        'scope':'Current leg/brace/attachment and retained base comparisons under recorded loads and material/hardware assumptions; no panel or floor-friction requalification.',
        'limits':['Supplemental EC5 splitting is reported separately from NDS checks; no unreinforced tab-notch resistance is used.',
                  'Hardware is conditional on specified material, delivered dimensions and nominal-diameter thread coverage; full-root sensitivity remains separately reported.',
                  'Commercial angle rated force components are checked; unlisted separation and independent flange moments are recorded, not assigned invented catalog capacities.',
                  'The listed criteria are not a climber weight rating or acceptance of unmodeled installation conditions.'],
        'qualified_for_design':False}



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.archive/'manifest.json').read_text())
    for name, sha in manifest['files'].items():
        if hashlib.sha256((args.archive/name).read_bytes()).hexdigest() != sha:
            raise ValueError('Archive checksum mismatch: '+name)
    report = json.loads(gzip.decompress((args.archive/'report.json.gz').read_bytes()))
    result = checks(report, json.loads((args.archive/'geometry.json').read_text()))
    (args.archive/'assessment.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(result['status'], result.get('metrics'), flush=True)
    if result.get('criteria'):
        print('Failed:', [key for key, value in result['criteria'].items() if not value], flush=True)
    else:
        print('Numerical acceptance failed; resistance decisions withheld.', flush=True)
