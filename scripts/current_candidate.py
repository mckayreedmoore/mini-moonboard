"""Check selected configuration and dispatch its reproducible generated checks.

This is configuration verification, not numerical or mechanical acceptance.
Recorded assessments are references to their own geometry revision, not passes
transferred to the selected model. No native solver is run.
"""
import argparse
import ast
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_CASES = (
    'a12-left', 'a12-rear', 'a12-forward',
    'k12-right', 'k12-rear', 'a1-rear',
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def module_path(root, name):
    return root / (name.replace('.', '/') + '.py')


def recorded_assessments(root, selection):
    records = {}
    for case, name in selection.get('recorded_assessments', {}).items():
        report = read_json(root / name)
        if report['candidate'] != selection['candidate'] or report['qualified_for_design'] is not False:
            raise ValueError(f'Assessment is not an unqualified selected-candidate record: {name}')
        geometry = selection['geometry']
        input_hashes = report.get('assessment_input_sha256', {})
        source_hashes = report.get('source_sha256', {})
        geometry_sha256 = digest(root / geometry)
        source_geometry_matches = any(
            Path(name).name == 'geometry.json' and value == geometry_sha256
            for hashes in (source_hashes, input_hashes)
            for name, value in hashes.items())
        records[case] = {
            'assessment': name, 'sha256': digest(root / name), 'status': report['status'],
            'criteria_met': sum(value is True for value in report['criteria'].values()),
            'criteria_count': len(report['criteria']),
            'matches_selected_geometry_snapshot': (
                input_hashes.get(geometry) == geometry_sha256
                or source_geometry_matches),
            'completion_gates': report.get('completion_gates', {}),
            'scope': 'Recorded result only; geometry-hash agreement does not verify force sources, method applicability or release.'}
    return records


def authenticated_aggregate(root, selection):
    name = selection.get('aggregate_evidence')
    if name is None:
        if selection.get('recorded_assessments'):
            raise ValueError('Pending evidence authority cannot list recorded assessments')
        return None
    path = root / name
    aggregate = read_json(path)
    key = selection['candidate']
    if aggregate.get('candidate') != key or aggregate.get('qualified_for_design') is not False:
        raise ValueError('Aggregate is not an unqualified selected-candidate record')
    floor_runner = key == 'compact-floor-flush-development'
    if floor_runner:
        if (aggregate.get('status') != 'ALL_SIX_FROZEN_CRITERIA_MET_WITH_DISCLOSED_LIMITS'
                or not aggregate.get('disclosed_limits')):
            raise ValueError('Floor-runner aggregate does not retain disclosed limits')
        angle_record = aggregate.get('angle_demand_ledger', {})
        angle_path = root / angle_record.get('path', '')
        if (angle_record.get('path') != 'docs/floor-runner-mvp-angle-demands.json'
                or not angle_path.is_file()
                or digest(angle_path) != angle_record.get('sha256')):
            raise ValueError('Floor-runner angle-demand ledger differs from aggregate')
        assessment_name, assessment_hash = 'flush-checks.json', 'flush_checks_sha256'
    else:
        if (aggregate.get('status') !=
                'ALL_SIX_LISTED_SPLICE_MEMBER_CRITERIA_MET_WITH_OPEN_ANGLE_GATE'
                or not aggregate.get('open_completion_gates')):
            raise ValueError('Aggregate does not retain the open completion gate')
        assessment_name, assessment_hash = 'splice-checks.json', 'splice_checks_sha256'
    if (set(aggregate.get('cases', {})) != set(CANONICAL_CASES)
            or set(selection.get('recorded_assessments', {})) != set(CANONICAL_CASES)):
        raise ValueError('Aggregate and authority require exactly six canonical cases')

    geometry_sha256 = digest(root / selection['geometry'])
    if aggregate.get('geometry_sha256') != geometry_sha256:
        raise ValueError('Aggregate geometry differs from selected geometry')
    for source_name, expected in aggregate.get('source_sha256', {}).items():
        source = root / source_name
        if not source.is_file() or digest(source) != expected:
            raise ValueError('Stale aggregate source snapshot: ' + source_name)

    for label in CANONICAL_CASES:
        case = aggregate['cases'][label]
        archive = root / case['archive']
        assessment = root / selection['recorded_assessments'][label]
        if assessment != archive / assessment_name:
            raise ValueError('Assessment path differs from aggregate archive: ' + label)
        artifacts = {
            'manifest_sha256': archive / 'manifest.json',
            'geometry_sha256': archive / 'geometry.json',
            'checks_sha256': archive / 'checks.json',
            assessment_hash: assessment,
        }
        for field, artifact in artifacts.items():
            if not artifact.is_file() or digest(artifact) != case.get(field):
                raise ValueError(f'Aggregate {field} differs: {label}')
        if case['geometry_sha256'] != geometry_sha256:
            raise ValueError('Aggregate cases do not share selected geometry: ' + label)

        manifest = read_json(archive / 'manifest.json')
        if manifest.get('candidate') != key:
            raise ValueError('Archive manifest candidate differs: ' + label)
        required = {
            'report.json.gz', 'geometry.json', 'sources.zip', 'checks.json',
            assessment_name,
        }
        if set(manifest.get('files', {})) != required:
            raise ValueError('Archive manifest inventory differs: ' + label)
        for artifact_name, expected in manifest['files'].items():
            artifact = archive / artifact_name
            if not artifact.is_file() or digest(artifact) != expected:
                raise ValueError('Archive artifact differs: ' + label + '/' + artifact_name)
        native = gzip.decompress((archive / 'report.json.gz').read_bytes())
        native_sha256 = hashlib.sha256(native).hexdigest()
        if (native_sha256 != case.get('native_report_sha256')
                or native_sha256 != manifest.get('native_report_sha256')):
            raise ValueError('Aggregate native report differs: ' + label)

    return {
        'path': name,
        'sha256': digest(path),
        'status': aggregate['status'],
        'case_labels': list(CANONICAL_CASES),
    }


def status_markdown(selection, records):
    package = Path(os.path.relpath(selection['build_package'], Path(selection['status_document']).parent)).as_posix()
    plan = Path(os.path.relpath(selection['completion_plan'], Path(selection['status_document']).parent)).as_posix()
    lines = ['# Selected candidate: recorded evidence', '',
             f"Selected configuration: `{selection['candidate']}`.", '',
             'Generated by `uv run python -m scripts.current_candidate --write-status`.',
             'These are recorded assessments, not a verified current load-case envelope or fabrication release.',
             'Geometry-hash agreement alone does not authenticate force sources or establish method applicability.', '']
    if selection.get('aggregate_evidence'):
        aggregate = Path(os.path.relpath(selection['aggregate_evidence'], Path(selection['status_document']).parent)).as_posix()
        lines.extend([f'Authenticated six-case summary: [aggregate evidence]({aggregate}).',
                      'Each saved assessment still describes one case; its local "full case set" gate is superseded by the authenticated aggregate, not rewritten.', ''])
    else:
        lines.extend([('Authenticated six-case selected-candidate aggregate: **pending**. '
                       'See completion plan for partial-case work; historical cases are not promoted here.'), ''])
    packet = []
    for field, title in (('shop_checklist', 'shop checklist'),
                         ('assembly_guide', 'assembly guide'),
                         ('working_set', 'working set')):
        name = selection.get(field)
        if name:
            packet.append(f'[{title}]({Path(os.path.relpath(name, Path(selection["status_document"]).parent)).as_posix()})')
    if packet:
        lines.extend(['Shop packet: ' + '; '.join(packet) + '.', ''])
    lines.extend([f'Full scope and remaining checks: [build package]({package}) and [completion plan]({plan}).', '',
             '| Recorded case | Implemented criteria met | Matches selected geometry snapshot | Recorded status |',
             '| --- | --- | --- | --- |'])
    for case, record in records.items():
        target = Path(os.path.relpath(record['assessment'], Path(selection['status_document']).parent)).as_posix()
        match = 'yes' if record['matches_selected_geometry_snapshot'] else 'no'
        lines.append(f"| [{case}]({target}) | {record['criteria_met']}/{record['criteria_count']} | {match} | `{record['status']}` |")
    for case, record in records.items():
        lines.extend(['', f'## {case}: recorded completion gates', '',
                      f"Assessment SHA-256: `{record['sha256']}`.", ''])
        lines.extend(f'- **{name}:** {value}' for name, value in record['completion_gates'].items())
    return '\n'.join(lines).rstrip() + '\n'


def check(root=ROOT):
    selection = read_json(root / 'current-candidate.json')
    key = selection['candidate']
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    model_path = module_path(root, selection['model_module'])
    assignments = [node for node in ast.parse(model_path.read_text()).body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'KEY' for t in node.targets)]
    require(len(assignments) == 1 and ast.literal_eval(assignments[0].value) == key,
            'Selected model KEY differs from candidate authority')
    for field in ('export_module', 'construction_module'):
        path = module_path(root, selection[field])
        tree = ast.parse(path.read_text())
        model_imports = [f'{node.module}.{alias.name}'
                         for node in tree.body if isinstance(node, ast.ImportFrom)
                         for alias in node.names if alias.asname == 'model']
        require(model_imports == [selection['model_module']],
                f'{field} does not bind the selected model')
    for field in ('build_package', 'completion_plan', 'hardware_schedule'):
        require((root / selection[field]).is_file(), f'Missing {field}')
    for field in ('shop_checklist', 'assembly_guide', 'decision_log', 'working_set'):
        name = selection.get(field)
        if name:
            require((root / name).is_file(), f'Missing {field}')

    viewer_path = root / selection['viewer_manifest']
    drawing_path = root / selection['construction_manifest']
    viewer, drawing = read_json(viewer_path), read_json(drawing_path)
    inventory = read_json(viewer_path.with_name('parts.json'))
    require(inventory['design'] == viewer['design'],
            'Viewer inventory metadata differs from its manifest')
    require(viewer['design']['key'] == key, 'Viewer candidate differs from authority')
    require(viewer['design']['build_package'] == selection['build_package'],
            'Viewer build-package reference differs from authority')
    require(drawing['candidate'] == key, 'Drawing candidate differs from authority')
    require(viewer['design']['qualified_for_design'] is False,
            'This development authority does not authorize design qualification')
    for field, manifest in (('export_module', viewer), ('construction_module', drawing)):
        producer = module_path(root, selection[field])
        name = producer.relative_to(root).as_posix()
        require(manifest['source_sha256'].get(name) == digest(producer),
                f'Manifest does not identify selected {field} revision')
    for path, manifest in ((viewer_path, viewer), (drawing_path, drawing)):
        require(bool(manifest['artifact_sha256']), f'Empty artifact inventory: {path}')
        for name, expected in manifest['artifact_sha256'].items():
            artifact = path.parent / name
            require(artifact.is_file() and digest(artifact) == expected,
                    f'Stale or missing artifact: {artifact.relative_to(root)}')
        for name, expected in manifest['source_sha256'].items():
            source = root / name
            require(source.is_file() and digest(source) == expected,
                    f'Stale source snapshot: {name} ({path.relative_to(root)})')
    for path in (viewer_path, viewer_path.with_name('parts.json')):
        name = path.relative_to(root).as_posix()
        require(drawing['source_sha256'].get(name) == digest(path),
                f'Drawing is not linked to selected viewer revision: {name}')
    require(selection['hardware_schedule'].split('/')[-1] in drawing['artifact_sha256']
            and (root / selection['hardware_schedule']).parent == drawing_path.parent,
            'Hardware schedule is not authenticated by drawing manifest')

    geometry_path = root / selection['geometry']
    geometry = read_json(geometry_path)
    require(geometry['candidate'] == key, 'Geometry candidate differs from authority')
    for name, expected in geometry['source_sha256'].items():
        source = root / name
        require(source.is_file() and digest(source) == expected,
                f'Stale geometry source snapshot: {name}')
    model_name = model_path.relative_to(root).as_posix()
    for label, manifest in (('viewer', viewer), ('geometry', geometry)):
        require(manifest['source_sha256'].get(model_name) == digest(model_path),
                f'{label} does not identify current model revision')

    # Check the existing viewer selection without adding another runtime fetch.
    html = (root / 'site/index.html').read_text()
    fallback = re.search(r'\? requestedModel : [\'\"]([^\'\"]+)[\'\"]', html)
    require(fallback is not None and fallback[1] == key,
            'Viewer default differs from candidate authority')
    current_group = re.search(
        r'option\.value === [\'\"]([^\'\"]+)[\'\"] \? currentDesigns', html)
    require(current_group is not None and current_group[1] == key,
            'Viewer current-design group differs from candidate authority')
    documents = selection.get('viewer_documents')
    if documents:
        require(inventory['design'].get('documents') == documents,
                'Viewer documents differ from candidate authority')
        if selection.get('aggregate_evidence'):
            require(any(row.get('path') == selection['aggregate_evidence'] for row in documents),
                    'Viewer documents omit aggregate evidence')
        require(any(row.get('path') == selection.get('shop_checklist') for row in documents),
                'Viewer documents omit the shop checklist')
    elif selection.get('aggregate_evidence'):
        aggregate_reference = re.search(
            rf'[\'\"]{re.escape(selection["aggregate_evidence"])}[\'\"]', html)
        require(aggregate_reference is not None,
                'Viewer aggregate-evidence link differs from candidate authority')
    checklist = selection.get('shop_checklist')
    if checklist:
        text = (root / checklist).read_text()
        require(f'`{key}`' in text, 'Shop checklist candidate differs from authority')
        require(selection['construction_manifest'] in text
                and selection['viewer_manifest'] in text,
                'Shop checklist does not name the selected manifests')
    leading = ['README.md', 'AGENTS.md', selection['build_package'], selection['completion_plan']]
    if checklist:
        leading.append(checklist)
    for name in leading:
        path = root / name
        if not path.is_file():
            continue
        candidates = re.findall(r'`([a-z0-9-]+-development)`', path.read_text())
        require(bool(candidates) and candidates[0] == key,
                f'Leading candidate reference differs from authority: {name}')

    if errors:
        raise ValueError('\n'.join(errors))
    aggregate = authenticated_aggregate(root, selection)
    records = recorded_assessments(root, selection)
    status_path = root / selection['status_document']
    require(status_path.is_file() and status_path.read_text() == status_markdown(selection, records),
            'Recorded status summary is stale; review inputs, then run scripts.current_candidate --write-status')
    if errors:
        raise ValueError('\n'.join(errors))
    return {
        'candidate': key,
        'configuration_consistent': True,
        'qualified_for_design': False,
        'viewer_manifest_sha256': digest(viewer_path),
        'construction_manifest_sha256': digest(drawing_path),
        'aggregate_evidence': aggregate,
        'recorded_assessments': records,
        'scope': selection['scope'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-exports', action='store_true',
                        help='Also rebuild selected CAD, construction and aggregate outputs')
    parser.add_argument('--write-status', action='store_true',
                        help='Refresh only the recorded-evidence summary; does not verify configuration or design')
    args = parser.parse_args()
    try:
        if args.write_status:
            if args.check_exports:
                parser.error('--write-status and --check-exports are separate operations')
            selection = read_json(ROOT / 'current-candidate.json')
            path = ROOT / selection['status_document']
            path.write_text(status_markdown(selection, recorded_assessments(ROOT, selection)))
            print(path)
            return
        report = check()
        if args.check_exports:
            selection = read_json(ROOT / 'current-candidate.json')
            subprocess.run([sys.executable, '-m', selection['export_module'], '--check'],
                           cwd=ROOT, check=True)
            subprocess.run([sys.executable, '-m', selection['construction_module'], '--check'],
                           cwd=ROOT, check=True)
            if selection.get('aggregate_evidence'):
                with tempfile.TemporaryDirectory() as directory:
                    rebuilt = Path(directory) / 'aggregate.json'
                    subprocess.run([
                        sys.executable, '-m', selection.get(
                            'aggregate_module', 'scripts.compact_spliced_flush_top_evidence'),
                        '--output', str(rebuilt),
                    ], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
                    expected = ROOT / selection['aggregate_evidence']
                    if rebuilt.read_bytes() != expected.read_bytes():
                        raise ValueError('Aggregate evidence differs from deterministic rebuild')
        print(json.dumps(report, indent=2))
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f'Current candidate check failed: {error}\n')


if __name__ == '__main__':
    main()
