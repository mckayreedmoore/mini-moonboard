"""Authenticate and summarize six frozen floor-runner no-slip case archives."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from scripts.clear_space_case_contract import validate_case_identity
from scripts.floor_flush_angle_ledger import CASES
from scripts.floor_flush_checks import FROZEN_ADOPTED_CRITERIA

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = 'compact-floor-flush-development'
ARCHIVE = Path('fea/results/floor-runner-mvp')
OUTPUT = Path('docs/floor-runner-mvp-evidence.json')
PRODUCER_VALIDITY = frozenset({
    'global_equilibrium_passed', 'mpc_check_passed',
    'contact_active_set_converged', 'closed_bearing_assumption_passed',
    'member_equilibrium_passed', 'numerically_accepted',
})


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_case(root, label):
    archive = root/ARCHIVE/label
    manifest_path = archive/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    required = {'report.json.gz', 'geometry.json', 'sources.zip',
                'checks.json', 'flush-checks.json'}
    if manifest.get('candidate') != CANDIDATE or set(manifest.get('files', {})) != required:
        raise ValueError('Wrong case manifest identity or inventory: '+label)
    for name, expected in manifest['files'].items():
        if digest(archive/name) != expected:
            raise ValueError('Archive hash differs: '+label+'/'+name)
    raw = gzip.decompress((archive/'report.json.gz').read_bytes())
    if hashlib.sha256(raw).hexdigest() != manifest['native_report_sha256']:
        raise ValueError('Native report hash differs: '+label)
    report = json.loads(raw)
    hold, force = CASES[label]
    validate_case_identity(report, expected_candidate=CANDIDATE,
        expected_hold=hold, expected_pounds=250., expected_horizontal_force=force)
    if not all(report.get(key) is True for key in (
            'numerically_accepted', 'global_equilibrium_passed',
            'member_equilibrium_passed', 'mpc_check_passed',
            'contact_active_set_converged', 'closed_bearing_assumption_passed')):
        raise ValueError('Native case is not numerically accepted: '+label)
    with ZipFile(archive/'sources.zip') as sources:
        if set(sources.namelist()) != set(report['source_sha256']):
            raise ValueError('Native source inventory differs: '+label)
        for name, expected in report['source_sha256'].items():
            if hashlib.sha256(sources.read(name)).hexdigest() != expected:
                raise ValueError('Native source differs: '+label+'/'+name)
    geometry = json.loads((archive/'geometry.json').read_text())
    checks = json.loads((archive/'checks.json').read_text())
    assessment = json.loads((archive/'flush-checks.json').read_text())
    if (geometry.get('candidate') != CANDIDATE or checks.get('candidate') != CANDIDATE
            or assessment.get('candidate') != CANDIDATE
            or checks.get('status') != 'LISTED_FIRST_STAGE_SCREENS_MET_WITH_OPEN_LIMITS'
            or not isinstance(checks.get('producer_validity'), dict)
            or set(checks['producer_validity']) != PRODUCER_VALIDITY
            or not all(value is True for value in checks['producer_validity'].values())
            or set(assessment.get('criteria', {})) != FROZEN_ADOPTED_CRITERIA
            or not all(assessment['criteria'].values())
            or assessment.get('qualified_for_design') is not False
            or len(assessment.get('commercial_angles', {})) != 24):
        raise ValueError('Frozen case checks do not pass: '+label)
    relative = ARCHIVE/label
    if any(assessment.get('assessment_input_sha256', {}).get(str(relative/name))
           != manifest['files'][name] for name in ('report.json.gz', 'geometry.json')):
        raise ValueError('Assessment inputs differ from archive: '+label)
    angles = assessment['commercial_angles']
    return {
        'archive': str(relative), 'manifest_sha256': digest(manifest_path),
        'geometry_sha256': manifest['files']['geometry.json'],
        'native_report_sha256': manifest['native_report_sha256'],
        'checks_sha256': manifest['files']['checks.json'],
        'flush_checks_sha256': manifest['files']['flush-checks.json'],
        'load': {'hold': hold, 'horizontal_force_xy_n': list(force)},
        'contact_cycles': len(report['contact_cycles']),
        'contact_update_strategy': report['contact_update_strategy'],
        'criteria_met': len(FROZEN_ADOPTED_CRITERIA),
        'criteria_total': len(FROZEN_ADOPTED_CRITERIA),
        'metrics': assessment['metrics'],
        'first_stage_metrics': checks['metrics'],
        'angle_count': len(angles),
        'angles': {name: {
            'listed_force_interaction': row['rated_force_component_unity'],
            'unlisted_separation_demand_n': row['unlisted_separation_demand_n'],
            'unlisted_parallel_couple_demand_nmm': max(
                abs(flange['parallel_couple_nmm']) for flange in
                row['flange_member_on_bracket_wrenches'].values()),
        } for name, row in angles.items()},
    }


def maximum(cases, field, category='metrics'):
    label = max(cases, key=lambda key: cases[key][category][field])
    return {'case': label, 'value': cases[label][category][field]}


def build(root=ROOT):
    root = Path(root)
    angle_path = root/'docs/floor-runner-mvp-angle-demands.json'
    angle_ledger = json.loads(angle_path.read_text())
    if (angle_ledger.get('candidate') != CANDIDATE
            or angle_ledger.get('case_order') != list(CASES)
            or angle_ledger.get('station_case_records') != 144
            or angle_ledger.get('connection_resistance_established') is not False):
        raise ValueError('Angle-demand ledger identity or limits differ')
    cases = {label: read_case(root, label) for label in CASES}
    geometry = {case['geometry_sha256'] for case in cases.values()}
    stations = {frozenset(case['angles']) for case in cases.values()}
    if len(geometry) != 1 or len(stations) != 1:
        raise ValueError('Cases do not share exact geometry and 24 angle stations')
    angle_rows = [(label, name, row) for label, case in cases.items()
                  for name, row in case['angles'].items()]
    def angle_max(field):
        label, name, row = max(angle_rows, key=lambda item: item[2][field] or 0.)
        return {'case': label, 'station': name, 'value': row[field] or 0.}
    return {
        'candidate': CANDIDATE,
        'status': 'ALL_SIX_FROZEN_CRITERIA_MET_WITH_DISCLOSED_LIMITS',
        'qualified_for_design': False,
        'geometry_sha256': geometry.pop(),
        'source_sha256': {name: digest(root/name) for name in (
            'scripts/floor_runner_mvp_evidence.py',
            'scripts/floor_flush_angle_ledger.py',
            'scripts/floor_flush_checks.py',
            'scripts/clear_space_case_contract.py')},
        'angle_demand_ledger': {
            'path': 'docs/floor-runner-mvp-angle-demands.json',
            'sha256': digest(angle_path)},
        'case_order': list(CASES), 'cases': cases,
        'governing_adopted': {field: maximum(cases, field) for field in (
            'actual_angle_lateral_CD_1', 'sampled_net_member',
            'header_gross_full_length_stability', 'base_end_notch_shear',
            'angle_rated_force_components', 'flush_face_wood_bearing')},
        'governing_first_stage': {'nominal_lateral': maximum(cases,
            'nominal_lateral', 'first_stage_metrics')},
        'minimum_reserves': {'directional_edge_end_mm': {
            'case': min(cases, key=lambda key: cases[key]['first_stage_metrics'][
                'minimum_directional_edge_end_margin_mm']),
            'value': min(case['first_stage_metrics'][
                'minimum_directional_edge_end_margin_mm'] for case in cases.values())}},
        'angle_station_case_records': len(angle_rows),
        'angle_demand_governing': {
            field: angle_max(field) for field in (
                'listed_force_interaction', 'unlisted_separation_demand_n',
                'unlisted_parallel_couple_demand_nmm')},
        'non_adopted_full_root_sensitivity': maximum(cases,
            'full_root_lateral_sensitivity', 'first_stage_metrics'),
        'disclosed_limits': [
            'ML24Z/SDS catalog does not rate the saved separation and parallel couple demands.',
            'Full-root bolt sensitivity is not the specified partially threaded bolt basis.',
            'Contact quadrature is finite sampling, not a continuum convergence proof.',
            'Actual delivered hardware, cut quality, jigged holes and installation require inspection.',
            'No-slip support is an explicit assumption, not a measured floor property.',
        ],
        'scope': 'Six exact current floor-runner cases under recorded loads, materials and conditional no-slip support; engineer-unreviewed DIY evidence, not fabrication release or climber rating.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = build()
    output = ROOT/args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'status': result['status'],
                      'governing_adopted': result['governing_adopted'],
                      'angle_demand_governing': result['angle_demand_governing']}, indent=2))


if __name__ == '__main__':
    main()
