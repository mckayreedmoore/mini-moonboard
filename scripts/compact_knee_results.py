"""Conditional all-bolt and sampled net-section checks for one knee-brace trial.

Consume an immutable compact_two_results archive made with both upper and knee
bolt prefixes. Archived gross-brace and actual-tab mesh runs remain distinct.
Postprocessed net sections do not correct native stiffness or qualify shoulders.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from fea.compact_assumption_checks import compare_bolt
from fea.compact_rail_checks import assess, hardware_assumptions
from fea.current_response_resistance import VALIDITY
from fea.thick_leg_checks import (
    bounded_section_check,
    bounded_section_properties,
    vector,
)

PREFIXES = ('lumber_leg_bolt_', 'knee_bolt_')
ACTUAL_TAB_BASIS = 'Conforming solid half-width strips with actual opposite end-tab removals'


def dot(a, b):
    return sum(x*y for x, y in zip(a, b, strict=True))


def native_tab_basis(report):
    """Require a consistent native brace formulation across both sides."""
    knees = {name: data['member'] for name, data in report['member_section_demands'].items()
             if name.startswith('base_knee_')}
    if set(knees) != {'base_knee_left', 'base_knee_right'}:
        raise ValueError('Require both native knee member records')
    formulations = {member.get('native_section_geometry') for member in knees.values()}
    if formulations == {None}:
        return False
    if formulations != {ACTUAL_TAB_BASIS}:
        raise ValueError('Require consistent recognized native tab meshing on both knees')
    for member in knees.values():
        if (len(member.get('tab_cut_boxes_sxq_mm', ())) != 2 or
                len(member.get('additional_recovery_stations_mm', ())) != 2):
            raise ValueError('Actual tab mesh requires recorded cuts and shoulder stations')
    return True


def cut_inventory(name, member, rows, hardware):
    """Bound every machining record and every upper/knee bore in CAD axes."""
    grain = vector(member['grain'], unit=True)
    normal = [0., grain[2], -grain[1]]
    centre = vector(member['centre_mm'])
    cuts = []
    for record in member['opening_records']:
        cuts.append({'source': record['source'], 'kind': record['kind'],
                     'box_sxq_mm': list(record['section_box_sxq_mm'])})
    for bolt, row in rows.items():
        if name not in (row['first'], row['second']):
            continue
        offset = [a-b for a, b in zip(vector(row['point']), centre, strict=True)]
        station, depth = dot(offset, grain), dot(offset, normal)
        radius = hardware[bolt]['hole_diameter_mm']/2
        cuts.append({'source': bolt, 'kind': 'bolt_bore', 'box_sxq_mm':
                     [station-radius, station+radius, -member['width_mm']/2,
                      member['width_mm']/2, depth-radius, depth+radius]})
    return cuts


def sampled_sections(report, geometry, rows):
    """Use actual sampled actions; identify every unsampled notch shoulder."""
    result = {}
    expected = {r[key] for r in rows.values() for key in ('first', 'second')}
    if set(geometry['members']) != expected:
        raise ValueError('Require geometry for every upper and knee bolt member')
    for name, member in geometry['members'].items():
        data = report['member_section_demands'][name]
        native = data['member']
        grain = vector(member['grain'], unit=True)
        normal = [0., grain[2], -grain[1]]
        if not all(math.isclose(native[k], member[k], abs_tol=1.e-5)
                   for k in ('width_mm', 'depth_mm')):
            raise ValueError('Native/CAD section dimensions differ: '+name)
        if dot(vector(native['axis'], unit=True), grain) < 1-1.e-8:
            raise ValueError('Native/CAD grain directions differ: '+name)
        orientation = dot(vector(native['section_u'], unit=True), [1., 0., 0.])
        if (abs(orientation) < 1-1.e-8 or
                dot(vector(native['section_v'], unit=True), normal)*orientation < 1-1.e-8):
            raise ValueError('Native section axes incompatible with CAD cut boxes: '+name)
        cuts = cut_inventory(name, member, rows, geometry['hardware_by_name'])
        checks = []
        for section in data['sections']:
            station = dot([a-b for a, b in zip(section['origin_xyz_mm'],
                                              member['centre_mm'], strict=True)], grain)
            active = [c for c in cuts if c['box_sxq_mm'][0]-1.e-7 <= station
                      <= c['box_sxq_mm'][1]+1.e-7]
            properties = bounded_section_properties(member['width_mm'], member['depth_mm'],
                                                    [c['box_sxq_mm'][2:] for c in active])
            checks.append({'station_mm_from_cad_centre': station,
                           'active_cut_sources': [c['source'] for c in active],
                           'actual_cut_box_properties': properties,
                           'comparison': bounded_section_check(data, member, section, properties)})
        if not checks:
            raise ValueError('Require native sampled sections: '+name)
        stations = [c['station_mm_from_cad_centre'] for c in checks]
        coverage = []
        for cut in cuts:
            low, high = cut['box_sxq_mm'][:2]
            targets = [low, high] if cut['kind'] == 'tab_notch' else [(low+high)/2]
            coverage.append({**cut, 'required_diagnostic_stations_mm': targets,
                             'unsampled_stations_mm': [s for s in targets
                                 if not any(abs(s-t) < 1.e-5 for t in stations)],
                             'intersects_any_sample': any(low-1.e-7 <= s <= high+1.e-7 for s in stations)})
        result[name] = {'sampled_net_peak': max(checks, key=lambda c:
                       c['comparison']['conservative_net_section_envelope_ratio']),
                       'sampled_sections': checks, 'cut_coverage': coverage,
                       'unsampled_notch_records': [c for c in coverage
                           if c['kind'] == 'tab_notch' and c['unsampled_stations_mm']],
                       'all_openings_represented': member.get('all_openings_represented') is True,
                       'local_splitting_and_notch_resistance_evaluated': False,
                       'qualified_for_design': False}
    return result


def checks(report, geometry):
    """Recompute stage one and actual Ktheta for the entire bolt inventory."""
    if report['candidate'] != geometry['candidate']:
        raise ValueError('Native and geometry candidates differ')
    for path, sha in geometry['source_sha256'].items():
        if path.startswith('mini_moonboard/') and report['source_sha256'].get(path) != sha:
            raise ValueError('Native and geometry model sources differ: '+path)
    if not all(report.get(key) is True for key in VALIDITY):
        return {'candidate': report['candidate'], 'status': 'INVALID_RESPONSE_DIAGNOSTIC_ONLY',
                'qualified_for_design': False}
    rows = {name: row for name, row in report['physical_connection_forces'].items()
            if name.startswith(PREFIXES)}
    if any(not any(name.startswith(prefix) for name in rows) for prefix in PREFIXES):
        raise ValueError('Require both upper and knee bolt families')
    actual_tabs = native_tab_basis(report)
    hardware = {name: hardware_assumptions(row['diameter_mm'],
                washer_od_mm=row['washer_od_mm'], hole_diameter_mm=row['hole_diameter_mm'],
                washer_thickness_mm=row['washer_thickness_mm'])
                for name, row in geometry['hardware_by_name'].items()}
    stage = assess(report, geometry['geometries_by_bolt_name'], hardware, bolt_prefixes=PREFIXES)
    actual = {name: compare_bolt(row, geometry['geometries_by_bolt_name'][name],
                                stage['bolts'][name]['lateral_ratio'])
              for name, row in rows.items()}
    groups = {}
    for name, group in stage['joint_resultants'].items():
        names = group['bolt_names']
        groups[name] = {**group,
            'actual_angle_peak_ratio_CD_1': max(actual[n]['comparisons']['actual_angle']['ratio_CD_1'] for n in names),
            'minimum_directional_edge_end_margin_mm': min(p['minimum_margin_mm']
                for n in names for p in stage['bolts'][n]['placement'].values()),
            'hardware_by_bolt': {n: stage['bolts'][n]['hardware'] for n in names}}
    return {'candidate': report['candidate'], 'status':
            'ACTUAL_TAB_MESH_KNEE_SCREEN_ONLY' if actual_tabs else 'GROSS_STIFFNESS_KNEE_SCREEN_ONLY',
            'stage_one': stage, 'actual_angle_all_bolts': actual, 'joint_groups': groups,
            'sampled_net_members': sampled_sections(report, geometry, rows),
            'receiver_fit_pass': geometry['receiver_fit_pass'],
            'native_brace_stiffness_basis': ACTUAL_TAB_BASIS if actual_tabs else
                'Gross section; reduced end tabs not represented in stiffness.',
            'limits': [('Native stiffness includes tab removals; bores and local notch-root resistance remain separate.'
                        if actual_tabs else 'Postprocessing net stresses does not correct the gross-stiffness native force distribution.'),
                       'Cut boxes bound all recorded machining and bolt holes; only actual sampled native stations receive stress comparisons.',
                       'Unsampled tab shoulders, notch stress concentration, splitting, local contact and prying remain unqualified.',
                       'Actual Ktheta retains Cd1.0; nominal bolt diameter and provisional hardware assumptions do not establish delivered properties.'],
            'qualified_for_design': False}


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
               Path('fea/compact_assumption_checks.py'), Path('fea/compact_rail_checks.py'),
               Path('fea/thick_leg_checks.py'), Path('fea/compact_thick_checks.py'), Path('fea/dowel_yield.py'),
               Path('fea/reinforced_timber_resistance.py')]
    result['source_sha256'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    output = args.output or args.archive/'knee-checks.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({name: group['actual_angle_peak_ratio_CD_1']
                     for name, group in result.get('joint_groups', {}).items()}, indent=2))


if __name__ == '__main__':
    main()
