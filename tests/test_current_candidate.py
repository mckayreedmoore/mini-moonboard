"""Configuration drift must fail without confusing archived results with release."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from scripts.current_candidate import (
    check,
    digest,
    recorded_assessments,
    status_markdown,
)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def configuration(tmp_path):
    """Small complete artifact chain; no CAD or native solver needed."""
    selection = json.loads(Path('current-candidate.json').read_text())
    key = selection['candidate']
    write_json(tmp_path / 'current-candidate.json', selection)
    model = tmp_path / (selection['model_module'].replace('.', '/') + '.py')
    model.parent.mkdir(parents=True)
    model.write_text(f'KEY = {key!r}\n')
    for field in ('export_module', 'construction_module'):
        path = tmp_path / (selection[field].replace('.', '/') + '.py')
        path.parent.mkdir(parents=True, exist_ok=True)
        package, module = selection['model_module'].rsplit('.', 1)
        path.write_text(f'from {package} import {module} as model\n')
    for name in ('README.md', selection['build_package'], selection['completion_plan']):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'Current `{key}`.\n')
    viewer = tmp_path / selection['viewer_manifest']
    sources = {model.relative_to(tmp_path).as_posix(): digest(model)}
    producers = {field: selection[field].replace('.', '/') + '.py'
                 for field in ('export_module', 'construction_module')}
    design = {'key': key, 'build_package': selection['build_package'],
              'qualified_for_design': False}
    write_json(viewer.with_name('parts.json'), {'design': design})
    write_json(viewer, {'design': design,
                        'source_sha256': {**sources, producers['export_module']:
                                         digest(tmp_path / producers['export_module'])},
                        'artifact_sha256': {'parts.json': digest(viewer.with_name('parts.json'))}})
    drawing = tmp_path / selection['construction_manifest']
    hardware = tmp_path / selection['hardware_schedule']
    hardware.parent.mkdir(parents=True)
    hardware.write_text('name,quantity\nbolt,12\n')
    write_json(drawing, {'candidate': key,
                        'source_sha256': {**sources, producers['construction_module']:
                                         digest(tmp_path / producers['construction_module']),
                                         **{p.relative_to(tmp_path).as_posix(): digest(p)
                                                     for p in (viewer, viewer.with_name('parts.json'))}},
                        'artifact_sha256': {hardware.name: digest(hardware)}})
    geometry = tmp_path / selection['geometry']
    write_json(geometry, {'candidate': key, 'source_sha256': sources})
    for name in selection['recorded_assessments'].values():
        write_json(tmp_path / name, {'candidate': key, 'qualified_for_design': False,
                                    'status': 'IMPLEMENTED_FLUSH_CRITERIA_NOT_MET',
                                    'criteria': {'bearing': True, 'rim_cut': False},
                                    'assessment_input_sha256': {selection['geometry']: digest(geometry)},
                                    'completion_gates': {'local_resistance': 'OPEN'}})
    aggregate_cases = {}
    for label, name in selection['recorded_assessments'].items():
        archive = (tmp_path / name).parent
        (archive / 'geometry.json').write_bytes(geometry.read_bytes())
        write_json(archive / 'checks.json', {'candidate': key})
        native = json.dumps({'candidate': key}).encode()
        (archive / 'report.json.gz').write_bytes(gzip.compress(native))
        (archive / 'sources.zip').write_bytes(b'source snapshot')
        manifest = {
            'candidate': key,
            'native_report_sha256': hashlib.sha256(native).hexdigest(),
            'files': {artifact: digest(archive / artifact) for artifact in (
                'report.json.gz', 'geometry.json', 'sources.zip', 'checks.json',
                'splice-checks.json')},
        }
        write_json(archive / 'manifest.json', manifest)
        aggregate_cases[label] = {
            'archive': archive.relative_to(tmp_path).as_posix(),
            'manifest_sha256': digest(archive / 'manifest.json'),
            'geometry_sha256': digest(archive / 'geometry.json'),
            'native_report_sha256': manifest['native_report_sha256'],
            'checks_sha256': digest(archive / 'checks.json'),
            'splice_checks_sha256': digest(tmp_path / name),
        }
    write_json(tmp_path / selection['aggregate_evidence'], {
        'candidate': key,
        'status': 'ALL_SIX_LISTED_SPLICE_MEMBER_CRITERIA_MET_WITH_OPEN_ANGLE_GATE',
        'qualified_for_design': False,
        'open_completion_gates': ['commercial angle applicability'],
        'geometry_sha256': digest(geometry),
        'cases': aggregate_cases,
        'source_sha256': {},
    })
    (tmp_path / 'site/index.html').write_text(
        f"const model = ok ? requestedModel : '{key}';\n"
        f"(option.value === '{key}' ? currentDesigns : historicalDesigns).append(option);\n"
        f"<a href=\"{selection['aggregate_evidence']}\">Authenticated evidence</a>\n")
    (tmp_path / selection['status_document']).write_text(
        status_markdown(selection, recorded_assessments(tmp_path, selection)))
    return tmp_path, selection


def test_consistency_retains_negative_assessment_and_open_gates(configuration):
    root, _ = configuration
    result = check(root)
    assert result['configuration_consistent'] is True
    assert result['qualified_for_design'] is False
    assert result['recorded_assessments']['a12-left']['completion_gates'] == {'local_resistance': 'OPEN'}


def test_consistency_authenticates_six_case_aggregate(configuration):
    root, selection = configuration
    result = check(root)
    assert result['aggregate_evidence'] == {
        'path': selection['aggregate_evidence'],
        'sha256': digest(root / selection['aggregate_evidence']),
        'status': 'ALL_SIX_LISTED_SPLICE_MEMBER_CRITERIA_MET_WITH_OPEN_ANGLE_GATE',
        'case_labels': [
            'a12-left', 'a12-rear', 'a12-forward',
            'k12-right', 'k12-rear', 'a1-rear',
        ],
    }


def test_rejects_viewer_without_selected_aggregate_link(configuration):
    root, selection = configuration
    html = root / 'site/index.html'
    html.write_text(html.read_text().replace(selection['aggregate_evidence'], 'docs/old-evidence.json'))
    with pytest.raises(ValueError, match='Viewer aggregate-evidence link differs'):
        check(root)


def test_rejects_aggregate_for_different_candidate(configuration):
    root, selection = configuration
    path = root / selection['aggregate_evidence']
    aggregate = json.loads(path.read_text())
    aggregate['candidate'] = 'old-development'
    write_json(path, aggregate)
    with pytest.raises(ValueError, match='Aggregate is not an unqualified selected-candidate record'):
        check(root)


def test_rejects_aggregate_without_exact_canonical_cases(configuration):
    root, selection = configuration
    path = root / selection['aggregate_evidence']
    aggregate = json.loads(path.read_text())
    del aggregate['cases']['k12-rear']
    write_json(path, aggregate)
    with pytest.raises(ValueError, match='exactly six canonical cases'):
        check(root)


def test_rejects_aggregate_with_different_common_geometry(configuration):
    root, selection = configuration
    path = root / selection['aggregate_evidence']
    aggregate = json.loads(path.read_text())
    aggregate['geometry_sha256'] = '0' * 64
    write_json(path, aggregate)
    with pytest.raises(ValueError, match='Aggregate geometry differs from selected geometry'):
        check(root)


@pytest.mark.parametrize('field, message', [
    ('manifest_sha256', 'Aggregate manifest_sha256 differs'),
    ('checks_sha256', 'Aggregate checks_sha256 differs'),
    ('splice_checks_sha256', 'Aggregate splice_checks_sha256 differs'),
    ('native_report_sha256', 'Aggregate native report differs'),
])
def test_rejects_case_digest_not_authenticated_by_aggregate(configuration, field, message):
    root, selection = configuration
    path = root / selection['aggregate_evidence']
    aggregate = json.loads(path.read_text())
    aggregate['cases']['a12-left'][field] = '0' * 64
    write_json(path, aggregate)
    with pytest.raises(ValueError, match=message):
        check(root)


def test_source_authenticated_assessment_matches_selected_geometry(configuration):
    root, selection = configuration
    name = selection['recorded_assessments']['a12-left']
    path = root / name
    report = json.loads(path.read_text())
    del report['assessment_input_sha256']
    report['source_sha256'] = {
        'fea/results/another-case/geometry.json': digest(root / selection['geometry']),
    }
    write_json(path, report)
    manifest_path = path.with_name('manifest.json')
    manifest = json.loads(manifest_path.read_text())
    manifest['files']['splice-checks.json'] = digest(path)
    write_json(manifest_path, manifest)
    aggregate_path = root / selection['aggregate_evidence']
    aggregate = json.loads(aggregate_path.read_text())
    aggregate['cases']['a12-left']['splice_checks_sha256'] = digest(path)
    aggregate['cases']['a12-left']['manifest_sha256'] = digest(manifest_path)
    write_json(aggregate_path, aggregate)
    (root / selection['status_document']).write_text(
        status_markdown(selection, recorded_assessments(root, selection)))
    result = check(root)
    assert result['recorded_assessments']['a12-left']['matches_selected_geometry_snapshot'] is True


@pytest.mark.parametrize('field', ['export_module', 'construction_module'])
def test_same_model_different_producer_is_not_authenticated(configuration, field):
    root, selection = configuration
    selected = root / (selection[field].replace('.', '/') + '.py')
    alternate = selected.with_name('alternate.py')
    alternate.write_text(selected.read_text())
    selection[field] = alternate.relative_to(root).with_suffix('').as_posix().replace('/', '.')
    write_json(root / 'current-candidate.json', selection)
    with pytest.raises(ValueError, match=f'Manifest does not identify selected {field}'):
        check(root)


def test_stale_geometry_generator_is_rejected(configuration):
    root, selection = configuration
    source = root / 'scripts/geometry.py'
    source.write_text('# initial generator\n')
    path = root / selection['geometry']
    geometry = json.loads(path.read_text())
    geometry['source_sha256']['scripts/geometry.py'] = digest(source)
    write_json(path, geometry)
    source.write_text('# changed generator\n')
    with pytest.raises(ValueError, match='Stale geometry source snapshot'):
        check(root)


@pytest.mark.parametrize('mutation, message', [
    ('model', 'Selected model KEY'),
    ('exporter', 'export_module does not bind'),
    ('viewer', 'Viewer default'),
    ('viewer_group', 'Viewer current-design group'),
    ('hardware', 'Stale or missing artifact'),
    ('drawing_link', 'Drawing is not linked'),
    ('readme', 'Leading candidate reference'),
])
def test_rejects_wrong_candidate_and_stale_revision(configuration, mutation, message):
    root, selection = configuration
    if mutation == 'model':
        (root / (selection['model_module'].replace('.', '/') + '.py')).write_text("KEY = 'old-development'\n")
    elif mutation == 'exporter':
        (root / (selection['export_module'].replace('.', '/') + '.py')).write_text('from mini_moonboard import old as model\n')
    elif mutation == 'viewer':
        (root / 'site/index.html').write_text("const model = ok ? requestedModel : 'old-development';")
    elif mutation == 'viewer_group':
        (root / 'site/index.html').write_text(
            f"const model = ok ? requestedModel : '{selection['candidate']}';\n"
            "(option.value === 'old-development' ? currentDesigns : historicalDesigns).append(option);\n")
    elif mutation == 'hardware':
        (root / selection['hardware_schedule']).write_text('changed')
    elif mutation == 'drawing_link':
        path = root / selection['construction_manifest']
        manifest = json.loads(path.read_text())
        del manifest['source_sha256'][selection['viewer_manifest']]
        write_json(path, manifest)
    else:
        (root / 'README.md').write_text('Current `old-development`.')
    with pytest.raises(ValueError, match=message):
        check(root)


def test_changed_geometry_does_not_relabel_recorded_forces_as_current(configuration):
    root, selection = configuration
    path = root / selection['geometry']
    geometry = json.loads(path.read_text())
    geometry['revision_change'] = 'new cuts'
    write_json(path, geometry)
    with pytest.raises(ValueError, match='Aggregate geometry differs from selected geometry'):
        check(root)


def test_stale_criteria_claim_is_rejected(configuration):
    root, selection = configuration
    path = root / selection['recorded_assessments']['a12-left']
    report = json.loads(path.read_text())
    report['criteria']['bearing'] = False
    write_json(path, report)
    with pytest.raises(ValueError, match='Aggregate splice_checks_sha256 differs'):
        check(root)
