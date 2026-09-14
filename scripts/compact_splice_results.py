"""Finite conditional checks for the four unnotched knee-splice members.

Consumes an archived response and actual geometry; never constructs CAD or runs
a solver. Endpoint groups and overlap groups remain distinct. Every piece's
complete hole inventory is included in its net-section comparisons.
"""
import argparse
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path

from fea.compact_assumption_checks import compare_bolt
from fea.compact_rail_checks import assess, hardware_assumptions
from fea.compact_thick_checks import (
    conservative_group_factor,
    fully_threaded_sensitivity,
    layout_check,
)
from fea.current_response_resistance import VALIDITY, member_comparisons
from fea.dowel_yield import single_shear
from fea.thick_leg_checks import vector
from fea.wider_leg_wood_checks import joint_local_checks
from scripts.compact_knee_results import dot, sampled_sections
from scripts.compact_thick_results import base_comparisons

CANDIDATE = 'compact-spliced-knee-development'
PREFIXES = ('lumber_leg_bolt_', 'knee_bolt_', 'knee_splice_bolt_')
PIECES = {f'base_knee_{side}_{end}' for side in ('left', 'right') for end in ('rim', 'leg')}


def actual_root_comparison(nominal, geometry, actual_angle, root_diameter_mm):
    """Full-root strength with actual Ktheta; keep nominal-D wood bearing/edges.

    Nominal-D perpendicular bearing is lower than the root-D value. Retaining
    it is conservative while root diameter reduces bearing width and Fyb D³/6.
    This must reproduce the archived fixed-K root branch before comparison.
    """
    fixed = fully_threaded_sensitivity(nominal, geometry, root_diameter_mm)
    original = nominal['fully_threaded_sensitivity']
    if not math.isclose(fixed['lateral_ratio'], original['lateral_ratio'], rel_tol=1.e-10, abs_tol=1.e-12):
        raise ValueError('Fixed-K full-root branch no longer matches original comparison')
    root = root_diameter_mm/25.4
    lengths = [value/25.4 for value in nominal['bearing_lengths_mm']]
    bearing = nominal['bearing_psi']
    moment = geometry['bending_yield_psi']*root**3/6
    reduction = actual_angle['comparisons']['actual_angle']['reduction_terms']
    result = single_shear(main_length_in=lengths[0], side_length_in=lengths[1],
        main_bearing_lb_in=bearing[0]*root, side_bearing_lb_in=bearing[1]*root,
        main_yield_moment_lb_in=moment, side_yield_moment_lb_in=moment,
        gap_in=0., reduction_terms=reduction)
    reference = result['reference_lateral_lbf']*4.4482216152605
    return {'root_diameter_mm':root_diameter_mm, 'nominal_diameter_mm':geometry['diameter_mm'],
        'Ktheta':actual_angle['comparisons']['actual_angle']['Ktheta'],
        'fixed_Ktheta_root_ratio':fixed['lateral_ratio'],
        'actual_Ktheta_root_ratio_CD_1':nominal['lateral_demand_n']/reference,
        'actual_Ktheta_root_reference_n_CD_1':reference, 'dowel_reference':result,
        'scope':'Entire bearing length and yield moment use supplied root diameter; nominal-D bearing stress, holes, spacing and edge criteria retained. Cd=1. Root dimension and Fyb remain specified material inputs.'}


def connection_groups(rows):
    """Group by physical member pair, not all fasteners touching one member."""
    groups = {}
    for name, row in rows.items():
        pair = tuple(sorted((row['first'], row['second'])))
        if pair[0] == pair[1]:
            raise ValueError('A bolt must connect two different members')
        groups.setdefault(pair, []).append(name)
    if any(len(names) not in (2, 4) for names in groups.values()):
        raise ValueError('This candidate requires two-bolt endpoints and four-bolt splices')
    return groups


def local_groups(rows, geometry, actual):
    """NDS parallel checks and supplemental EC5 splitting for each actual joint."""
    result = {}
    for pair, names in connection_groups(rows).items():
        diameters = {geometry['geometries_by_bolt_name'][name]['diameter_mm'] for name in names}
        holes = {geometry['hardware_by_name'][name]['hole_diameter_mm'] for name in names}
        if len(diameters) != 1 or len(holes) != 1:
            raise ValueError('A connection group must have one bolt and hole diameter')
        diameter, hole = diameters.pop(), holes.pop()
        points = [vector(rows[name]['point']) for name in names]
        pitch = max(math.dist(a, b) for a, b in itertools.combinations(points, 2))
        area = min(geometry['members'][name]['width_mm']*geometry['members'][name]['depth_mm'] for name in pair)
        cg = conservative_group_factor(len(names), diameter, pitch, area)
        per_member = {}
        for member_name in pair:
            member = geometry['members'][member_name]
            grain, centre = vector(member['grain'], unit=True), vector(member['centre_mm'])
            normal = [0., grain[2], -grain[1]]
            extra = list(member['additional_section_boxes'])
            for other, row in rows.items():
                if other in names or member_name not in (row['first'], row['second']):
                    continue
                offset = [a-b for a, b in zip(row['point'], centre, strict=True)]
                extra.append([dot(offset, grain), dot(offset, normal), geometry['hardware_by_name'][other]['hole_diameter_mm']])
            forces = [vector(rows[name]['force_on_first_xyz_n'] if rows[name]['first'] == member_name
                             else rows[name]['force_on_second_xyz_n']) for name in names]
            local = joint_local_checks(points, forces, grain=grain, centre=centre,
                end_stations_mm=member['end_stations_mm'], depth_mm=member['depth_mm'],
                width_mm=member['width_mm'], hole_mm=hole, additional_section_boxes=extra)
            per_member[member_name] = {'wood':local, 'layout':layout_check(points, member, diameter),
                                     'other_group_holes_in_net_envelope':len(extra)-len(member['additional_section_boxes'])}
        peak = max(actual[name]['comparisons']['actual_angle']['ratio_CD_1'] for name in names)
        result[' / '.join(pair)] = {'members':list(pair), 'bolt_names':names,
            'member_checks':per_member, 'actual_angle_peak_ratio_CD_1':peak,
            'additional_group_factor_sensitivity':cg,
            'peak_with_additional_group_reduction':peak/cg,
            'group_factor_scope':'Additional conservative equal-EA, total-count row sensitivity; individual native sharing is retained.'}
    return result


def overlap_contact_check(report):
    """Require recorded independent pieces and explicit unilateral contact."""
    assumptions = report.get('splice_assumptions', {})
    required = ('independent_members', 'compression_only_overlap', 'no_tensile_tie', 'no_composite_action')
    contacts = [row for row in report.get('member_contacts', [])
                if row['name'].startswith('knee_splice_contact_')]
    names = [row['name'] for row in contacts]
    bearings = {row['name']:row for row in report.get('bearings', [])}
    records = [bearings[name] for name in names if name in bearings]
    pairs = {(f'base_knee_{side}_rim', f'base_knee_{side}_leg') for side in ('left', 'right')}
    actual_pairs = {frozenset((row['first'], row['second'])) for row in contacts}
    pressures = []
    for contact in contacts:
        area = contact['tributary_area_mm2']
        if not math.isfinite(area) or area <= 0:
            raise ValueError('Overlap contact requires positive tributary area')
        name = contact['name']
        if name in bearings:
            pressures.append({'name':name, 'area_mm2':area,
                'compression_force_n':bearings[name]['compression_force_n'],
                'wood_bearing_ratio':max(0.,bearings[name]['compression_force_n'])/(area*625*.006894757293168361)})
    passed = (all(assumptions.get(key) is True for key in required) and bool(names)
              and actual_pairs == {frozenset(pair) for pair in pairs}
              and len(set(names)) == len(names) and len(records) == len(names)
              and all(row.get('compression_only_assumption_satisfied') is True
                      and math.isfinite(row['compression_force_n']) and row['compression_force_n'] >= -1.e-6
                      for row in records)
              and all(row['wood_bearing_ratio'] <= 1 for row in pressures))
    return {'passes':passed, 'assumptions':assumptions, 'contact_records':records,
            'expected_contact_names':names, 'wood_bearing':pressures,
            'basis':'Bolts resist signed relative opening; overlap contact transmits compression only, with no friction or composite wood tie credited.'}


def checks(report, geometry):
    if report.get('candidate') != CANDIDATE or geometry.get('candidate') != CANDIDATE:
        raise ValueError('Require matching spliced-knee candidate identities')
    if not all(report.get(key) is True for key in VALIDITY):
        return {'candidate':CANDIDATE, 'status':'INVALID_RESPONSE_DIAGNOSTIC_ONLY', 'qualified_for_design':False}
    for path, sha in geometry['source_sha256'].items():
        if path.startswith('mini_moonboard/') and report['source_sha256'].get(path) != sha:
            raise ValueError('Native and geometry model sources differ: '+path)
    rows = {name:row for name, row in report['physical_connection_forces'].items() if name.startswith(PREFIXES)}
    members = geometry['members']
    if {name for name in members if name.startswith('base_knee_')} != PIECES:
        raise ValueError('Require all four separate knee members')
    for name in PIECES:
        member = members[name]
        if not (math.isclose(member['width_mm'], 38.1, abs_tol=1.e-5)
                and math.isclose(member['depth_mm'], 139.7, abs_tol=1.e-5)):
            raise ValueError('Require unnotched standard 2x6 knee pieces')
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
        result['notch_check_applicable'] = False if name in PIECES else None
    base = base_comparisons(report, geometry)
    header = member_comparisons(dict(report, member_section_demands={
        'base_header':report['member_section_demands']['base_header']}))['base_header']
    contact = overlap_contact_check(report)
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
    return {'candidate':CANDIDATE, 'status':'LISTED_CONDITIONAL_SPLICE_CRITERIA_MET' if all(criteria.values()) else 'LISTED_SPLICE_CRITERIA_NOT_MET',
        'criteria':criteria, 'metrics':metrics, 'stage_one':stage, 'actual_angle_all_bolts':actual,
        'actual_root':root_summary,
        'joint_groups':groups, 'sampled_net_members':sections, 'base':base, 'header_gross':header,
        'overlap_contact':contact, 'duration_factor_adopted':1.,
        'scope':'Current leg/brace/attachment and retained base comparisons under recorded loads and material/hardware assumptions; no panel or floor-friction requalification.',
        'limits':['Supplemental EC5 splitting is reported separately from NDS checks; no unreinforced tab-notch resistance is used.',
                  'Hardware is conditional on specified material, delivered dimensions and nominal-diameter thread coverage; full-root sensitivity remains separately reported.',
                  'The listed criteria are not a climber weight rating or acceptance of unmodeled installation conditions.'],
        'qualified_for_design':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.archive/'manifest.json').read_text())
    for name, sha in manifest['files'].items():
        if hashlib.sha256((args.archive/name).read_bytes()).hexdigest() != sha:
            raise ValueError('Archive changed: '+name)
    raw = gzip.decompress((args.archive/'report.json.gz').read_bytes())
    if hashlib.sha256(raw).hexdigest() != manifest['native_report_sha256']:
        raise ValueError('Native report changed')
    result = checks(json.loads(raw), json.loads((args.archive/'geometry.json').read_text()))
    sources = [args.archive/'report.json.gz', args.archive/'geometry.json', Path(__file__),
               Path('scripts/compact_knee_results.py'), Path('scripts/compact_thick_results.py'),
               Path('fea/compact_rail_checks.py'), Path('fea/compact_thick_checks.py'),
               Path('fea/thick_leg_checks.py'), Path('fea/wider_leg_wood_checks.py'),
               Path('fea/compact_assumption_checks.py'), Path('fea/current_response_resistance.py'),
               Path('fea/reinforced_timber_resistance.py'), Path('fea/dowel_yield.py')]
    result['source_sha256'] = {str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    output = args.output or args.archive/'splice-checks.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({key:result.get(key) for key in ('status', 'criteria', 'metrics')}, indent=2))


if __name__ == '__main__':
    main()
