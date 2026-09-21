"""Aggregate and authenticate six saved compact spliced flush-top cases.

Reads archived results only. It does not construct CAD or run a solver.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from scripts.compact_spliced_flush_top_study import CASES as LOAD_CASES

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = 'compact-spliced-flush-top-development'
CASES = {label: 'fea/results/compact-spliced-flush-top/' +
         ('a12-left-07' if label == 'a12-left' else label + '-03')
         for label in LOAD_CASES}
OUTPUT = Path('docs/compact-spliced-flush-top-evidence.json')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def extreme(rows, field, *, lowest=False):
    function = min if lowest else max
    case, value = function(((case, values[field]) for case, values in rows.items()),
                           key=lambda item: item[1])
    return {'case': case, 'value': value}


def authenticate_archived_sources(archive, archive_name, report, geometry, splice, manifest):
    """Authenticate frozen producer sources without consulting today's tree."""
    expected = report.get('source_sha256', {})
    if not isinstance(expected, dict) or not expected:
        raise ValueError('Archived source identity is missing: ' + archive_name)
    with ZipFile(archive / 'sources.zip') as sources:
        names = sources.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError('Archived source inventory differs: ' + archive_name)
        for name, source_sha256 in expected.items():
            if hashlib.sha256(sources.read(name)).hexdigest() != source_sha256:
                raise ValueError('Archived source hash differs: ' + archive_name + '/' + name)

    # Geometry and splice records may name sources from the native closure.
    # When they do, require the same archived identity rather than a live file.
    for record_name, record in (('Geometry', geometry), ('Splice-check', splice)):
        for name, source_sha256 in record.get('source_sha256', {}).items():
            if name in expected and expected[name] != source_sha256:
                raise ValueError(record_name + ' archived source hash differs: ' + name)

    splice_sources = splice.get('source_sha256', {})
    for filename in ('report.json.gz', 'geometry.json'):
        inputs = [source_sha256 for name, source_sha256 in splice_sources.items()
                  if Path(name).name == filename]
        if inputs != [manifest['files'][filename]]:
            raise ValueError('Splice-check archived input hash differs: ' + filename)


def read_case(root, label, archive_name):
    archive = root / archive_name
    manifest_path = archive / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('candidate') != CANDIDATE:
        raise ValueError('Archive manifest candidate differs: ' + archive_name)
    for name, expected in manifest.get('files', {}).items():
        if digest(archive / name) != expected:
            raise ValueError('Archive manifest hash differs: ' + str(archive / name))
    required = {
        'report.json.gz', 'geometry.json', 'sources.zip', 'checks.json',
        'splice-checks.json',
    }
    if set(manifest.get('files', {})) != required:
        raise ValueError('Archive manifest inventory differs: ' + archive_name)

    raw = gzip.decompress((archive / 'report.json.gz').read_bytes())
    if hashlib.sha256(raw).hexdigest() != manifest.get('native_report_sha256'):
        raise ValueError('Native report hash differs: ' + archive_name)
    report = json.loads(raw)
    geometry = json.loads((archive / 'geometry.json').read_text())
    saved_first = json.loads((archive / 'checks.json').read_text())
    splice = json.loads((archive / 'splice-checks.json').read_text())
    authenticate_archived_sources(
        archive, archive_name, report, geometry, splice, manifest)
    first = splice.get('stage_one', {})
    if any(record.get('candidate') != CANDIDATE
           for record in (report, geometry, saved_first, splice, first)):
        raise ValueError('Candidate identity differs: ' + archive_name)
    if any(stage.get('status') != 'LISTED_FIRST_STAGE_SCREENS_MET_WITH_OPEN_LIMITS'
           or not all(stage.get('producer_validity', {}).values())
           for stage in (saved_first, first)):
        raise ValueError('Saved first-stage check identity or validity differs: ' + archive_name)
    if (report.get('numerically_accepted') is not True
            or splice.get('status') != 'LISTED_CONDITIONAL_SPLICE_CRITERIA_MET'
            or not splice.get('criteria') or not all(splice['criteria'].values())):
        raise ValueError('Saved conditional case does not pass: ' + archive_name)
    hold, horizontal = LOAD_CASES[label]
    parameters = report.get('parameters', {})
    force = parameters.get('force_xyz_n', [])
    if (parameters.get('hold') != hold or parameters.get('pounds') != 250.
            or force[:2] != list(horizontal) or len(force) != 3 or force[2] >= 0
            or report.get('floor_scope') !=
            'Conditional no sliding; normal contact may open; no friction coefficient qualification'):
        raise ValueError('Saved case load or no-slip scope differs: ' + archive_name)
    overlap = max((row['wood_bearing_ratio']
                   for row in splice['overlap_contact']['wood_bearing']), default=0.)
    metrics = {**splice['metrics'],
        'minimum_directional_edge_end_margin_mm':
            first['stage_one']['metrics']['minimum_directional_edge_end_margin_mm']
            if 'stage_one' in first else first['metrics']['minimum_directional_edge_end_margin_mm'],
        'steel_direct': first['metrics']['steel_direct'],
        'washer_bearing': first['metrics']['washer_bearing'],
        'washer_bending': first['metrics']['washer_bending'],
        'overlap_contact_wood_bearing': overlap,
        'maximum_timber_displacement_mm': report['maximum_timber_displacement_mm'],
        'maximum_panel_displacement_mm': report['maximum_panel_displacement_mm'],
    }
    return {
        'archive': archive_name,
        'manifest_sha256': digest(manifest_path),
        'geometry_sha256': manifest['files']['geometry.json'],
        'native_report_sha256': manifest['native_report_sha256'],
        'checks_sha256': manifest['files']['checks.json'],
        'splice_checks_sha256': manifest['files']['splice-checks.json'],
        'load': {'hold': hold, 'horizontal_force_xy_n': list(horizontal),
                 'vertical_force_n': force[2]},
        'criteria_met': sum(value is True for value in splice['criteria'].values()),
        'criteria_total': len(splice['criteria']),
        'metrics': metrics,
        'non_adopted_full_root': {
            'actual_Ktheta_ratio_CD_1': splice['actual_root']['peak_actual_Ktheta_root_ratio_CD_1'],
            'actual_Ktheta_with_additional_group_reduction':
                splice['actual_root']['peak_with_additional_group_reduction'],
            'fixed_maximum_Ktheta_ratio': first['metrics']['full_root_lateral_sensitivity'],
            'adopted_as_design_basis': splice['actual_root']['adopted_as_design_basis'],
        },
    }


def build(root=ROOT, cases=CASES):
    root = Path(root)
    records = {label: read_case(root, label, archive) for label, archive in cases.items()}
    if len(records) != 6 or set(records) != set(CASES):
        raise ValueError('Require exactly six named current load cases')
    geometry_hashes = {record['geometry_sha256'] for record in records.values()}
    if len(geometry_hashes) != 1:
        raise ValueError('Six cases do not share exact geometry')
    metrics = {case: record['metrics'] for case, record in records.items()}
    roots = {case: record['non_adopted_full_root'] for case, record in records.items()}
    maximum_fields = (
        'actual_angle_lateral_CD_1', 'additional_group_reduction_sensitivity',
        'local_parallel', 'supplemental_EC5_splitting', 'sampled_net_member',
        'header_gross_full_length_stability', 'base_bearing_average',
        'base_bearing_quarter_area_sensitivity', 'base_end_notch_shear',
        'steel_direct', 'washer_bearing', 'washer_bending',
        'overlap_contact_wood_bearing', 'maximum_timber_displacement_mm',
        'maximum_panel_displacement_mm',
    )
    return {
        'candidate': CANDIDATE,
        'status': 'ALL_SIX_LISTED_SPLICE_MEMBER_CRITERIA_MET_WITH_OPEN_ANGLE_GATE',
        'geometry_sha256': geometry_hashes.pop(),
        'source_sha256': {
            path: digest(root / path) for path in (
                'scripts/compact_spliced_flush_top_evidence.py',
                'scripts/compact_spliced_flush_top_study.py',
            )
        },
        'cases': records,
        'governing_adopted': {field: extreme(metrics, field) for field in maximum_fields},
        'minimum_reserves': {
            field: extreme(metrics, field, lowest=True) for field in (
                'minimum_group_spacing_margin_mm',
                'minimum_directional_edge_end_margin_mm',
            )
        },
        'non_adopted_full_root_sensitivity': {
            'actual_Ktheta': extreme(roots, 'actual_Ktheta_ratio_CD_1'),
            'actual_Ktheta_with_additional_group_reduction':
                extreme(roots, 'actual_Ktheta_with_additional_group_reduction'),
            'fixed_maximum_Ktheta': extreme(roots, 'fixed_maximum_Ktheta_ratio'),
            'adopted_as_design_basis': False,
            'interpretation': 'Reference-root sensitivity only; nominal-diameter strength and delivered full-body acceptance remain the adopted basis.',
        },
        'scope': 'Six fresh assembled cases for current leg, spliced knees, relocated upper joint and retained base under recorded loads, materials and conditional no-slip support.',
        'open_completion_gates': [
            'Retained ML24Z/SDS connection separation capacity and independent flange-couple applicability are not established.',
        ],
        'limits': [
            'Conditional engineer-unreviewed DIY evidence, not an unconditional climber rating.',
            'No floor-friction qualification, installed anchor or measured floor property is claimed.',
            'Panel and T-nut construction remain accepted scope and are not requalified here.',
            'Catalog hardware, specified lumber, drilling and assembly requirements remain mandatory.',
            'Full-root calculations are non-adopted sensitivities and include values above 1.0.',
        ],
        'qualified_for_design': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = build()
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'],
                      'governing_adopted': result['governing_adopted'],
                      'non_adopted_full_root_sensitivity':
                          result['non_adopted_full_root_sensitivity']}, indent=2))


if __name__ == '__main__':
    main()
