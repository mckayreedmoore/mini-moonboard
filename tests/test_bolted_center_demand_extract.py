"""Signed center interface recovery from a synthetic native response."""

import copy
import hashlib
import json

import pytest

from scripts.bolted_center_demand_extract import extract, extract_files


def fixture():
    owners = {
        'bearing_p_h': ('principal', 'header', [1, 0, 0]),
        'base_upright_1': ('principal', 'base', [0, 1, 0]),
        'base_beam_1': ('header', 'base', [0, 1, 0]),
        'bearing_h_s': ('header', 'post', [11, 0, 0]),
        'head_upright_1': ('post', 'head', [10, 1, 0]),
        'head_beam_1': ('header', 'head', [10, 1, 0]),
    }
    forces = {
        'bearing_p_h': [0, 4, 0], 'base_upright_1': [0, 6, 0],
        'base_beam_1': [0, -6, 0], 'bearing_h_s': [0, 4, 0],
        'head_upright_1': [0, -6, 0], 'head_beam_1': [0, 6, 0],
    }
    record = {'candidate': 'compact-floor-flush-development',
              'connection_ownership': {name: {'first': first, 'second': second, 'point': point}
                                       for name, (first, second, point) in owners.items()},
              'angle_stations': [
                  {'name': 'base', 'members': ['header', 'principal'], 'origin': [0, 0, 0]},
                  {'name': 'head', 'members': ['header', 'post'], 'origin': [10, 0, 0]}]}
    report = {'candidate': record['candidate'], 'physical_connection_forces': {
        name: dict(**record['connection_ownership'][name], force_on_first_xyz_n=force,
                   force_on_second_xyz_n=[-x for x in force])
        for name, force in forces.items()}}
    return report, record


def test_signed_simultaneous_interface_wrenches_and_action_reaction():
    report, record = fixture()
    result = extract(report, record, 'principal', 'post', 'header')
    assert result['classification'] == 'provisional_baseline_ML24Z_SDS'
    p = result['interfaces']['principal_header']
    assert p['origin_xyz_mm'] == [0, 0, 0]
    assert p['on_center_member']['force_xyz_n'] == [0, 10, 0]
    assert p['on_center_member']['moment_xyz_nmm'] == [0, 0, 4]
    assert p['on_center_member_components']['direct']['force_xyz_n'] == [0, 4, 0]
    assert p['on_center_member_components']['direct']['moment_xyz_nmm'] == [0, 0, 4]
    assert p['on_center_member_components']['via_clip']['force_xyz_n'] == [0, 6, 0]
    assert p['on_header']['force_xyz_n'] == [0, -10, 0]
    assert p['on_header']['moment_xyz_nmm'] == [0, 0, -4]
    assert p['residual']['passed']
    s = result['interfaces']['post_header']
    assert s['on_center_member']['force_xyz_n'] == [0, -10, 0]
    assert s['on_center_member']['moment_xyz_nmm'] == [0, 0, -4]
    assert s['residual']['passed']


def test_missing_owner_and_unbalanced_clip_are_visible():
    report, record = fixture()
    del report['physical_connection_forces']['base_beam_1']
    with pytest.raises(ValueError, match='Missing physical connection'):
        extract(report, record, 'principal', 'post', 'header')
    report, record = fixture()
    report['physical_connection_forces']['base_beam_1']['force_on_first_xyz_n'] = [0, -5, 0]
    report['physical_connection_forces']['base_beam_1']['force_on_second_xyz_n'] = [0, 5, 0]
    result = extract(report, record, 'principal', 'post', 'header')
    assert not result['interfaces']['principal_header']['residual']['passed']
    assert result['interfaces']['principal_header']['residual']['force_xyz_n'] == [0, 1, 0]


def test_rejects_bad_endpoint_sign_and_candidate_mismatch():
    report, record = fixture()
    report['physical_connection_forces']['bearing_p_h']['force_on_second_xyz_n'] = [0, 4, 0]
    with pytest.raises(ValueError, match='action-reaction'):
        extract(report, record, 'principal', 'post', 'header')
    report, record = fixture()
    changed = copy.deepcopy(report)
    changed['candidate'] = 'compact-floor-flush-bolted-development'
    with pytest.raises(ValueError, match='Candidate mismatch'):
        extract(changed, record, 'principal', 'post', 'header')


def test_kerf_proxy_classification_names_baseline_connectors():
    report, record = fixture()
    report['candidate'] = record['candidate'] = 'bolted-kerf-right-diagnostic-proxy'
    result = extract(report, record, 'principal', 'post', 'header')
    assert result['classification'] == 'provisional_kerf_right_ML24Z_SDS_proxy'


def test_other_header_attachments_and_external_load_close_free_body():
    report, record = fixture()
    extras = {
        'other_first': ('header', 'neighbor', [0, 2, 0], [5, 0, 0]),
        'other_second': ('neighbor', 'header', [2, 0, 0], [0, -3, 0]),
    }
    for name, (first, second, point, force) in extras.items():
        record['connection_ownership'][name] = {'first': first, 'second': second,
                                                'point': point}
        report['physical_connection_forces'][name] = {
            'first': first, 'second': second, 'point': point,
            'force_on_first_xyz_n': force,
            'force_on_second_xyz_n': [-x for x in force]}
    record['gravity_points'] = {'header': {'point': [32, 0, 0], 'force': [-5, -3, 0]}}
    result = extract(report, record, 'principal', 'post', 'header')
    header = result['header_free_body']
    assert header['origin_xyz_mm'] == [0, 0, 0]
    assert header['other_attachments']['connection_names'] == list(extras)
    assert header['other_attachments']['wrench']['force_xyz_n'] == [5, 3, 0]
    assert header['other_attachments']['wrench']['moment_xyz_nmm'] == [0, 0, -4]
    assert header['selected_interfaces']['wrench']['moment_xyz_nmm'] == [0, 0, 100]
    assert header['external_load']['moment_xyz_nmm'] == [0, 0, -96]
    assert header['residual']['force_xyz_n'] == [0, 0, 0]
    assert header['residual']['moment_xyz_nmm'] == [0, 0, 0]
    assert header['residual']['passed']
    shifted = extract(report, record, 'principal', 'post', 'header', [1, 0, 0])
    assert shifted['header_free_body']['origin_xyz_mm'] == [1, 0, 0]
    assert shifted['header_free_body']['other_attachments']['wrench']['moment_xyz_nmm'] == [0, 0, -7]
    assert shifted['header_free_body']['residual']['moment_xyz_nmm'] == [0, 0, 0]


def test_header_free_body_requires_external_record_and_all_header_rows():
    report, record = fixture()
    result = extract(report, record, 'principal', 'post', 'header')
    assert result['header_free_body']['residual']['available'] is False
    assert result['header_free_body']['other_attachments']['connection_names'] == []
    record['connection_ownership']['other'] = {'first': 'header', 'second': 'neighbor',
                                                'point': [0, 0, 0]}
    with pytest.raises(ValueError, match='Missing physical connection: other'):
        extract(report, record, 'principal', 'post', 'header')
    report['physical_connection_forces']['unexpected'] = {
        'first': 'header', 'second': 'neighbor', 'point': [0, 0, 0],
        'force_on_first_xyz_n': [0, 0, 1], 'force_on_second_xyz_n': [0, 0, -1]}
    del record['connection_ownership']['other']
    with pytest.raises(ValueError, match='absent from record'):
        extract(report, record, 'principal', 'post', 'header')


def test_header_free_body_reports_unbalanced_external_force():
    report, record = fixture()
    record['gravity_points'] = {'header': {'point': [0, 0, 0], 'force': [0, 0, -1]}}
    result = extract(report, record, 'principal', 'post', 'header')
    assert result['header_free_body']['residual']['available']
    assert not result['header_free_body']['residual']['passed']
    assert result['header_free_body']['residual']['force_xyz_n'] == [0, 0, -1]


def file_fixture(tmp_path):
    tmp_path = tmp_path / 'a12-rear'
    tmp_path.mkdir()
    report, record = fixture()
    report.update(numerically_accepted=True, contact_active_set_converged=True,
                  global_equilibrium_passed=True, member_equilibrium_passed=True,
                  mpc_check_passed=True, contact_cycles=[{'directory': 'cycle-01',
                                                          'contact_passed': True}],
                  diagnostic_scope={'case': 'a12-rear',
                                    'source_geometry': 'compact-floor-flush-bolted-development-kerf-right',
                                    'connector_proxy': 'baseline ML24Z angles and SDS screws',
                                    'bolted_joint_demands': False, 'acceptance': False},
                  parameters={'hold': 'A12', 'force_xyz_n': [0, 300, -1]})
    report['candidate'] = record['candidate'] = 'bolted-kerf-right-diagnostic-proxy'
    record.update(hold='A12', force_xyz_n=[0, 300, -1], diagnostic_only=True,
                  provisional_structural_connectors='baseline ML24Z angles and SDS screws',
                  bolted_joint_demands=False,
                  kerf_panel_bounds={f'{name}_{side}': {
                      'actual_x_mm': width, 'mesh_x_mm': width}
                      for name in ('main_lower', 'main_upper', 'kicker')
                      for side, width in (('left', [-1219.2, -1.5875]),
                                          ('right', [-1.5875, 1216.025]))})
    cycle = tmp_path / 'cycle-01'
    cycle.mkdir()
    record_path = cycle / 'input.json'
    record_path.write_text(json.dumps(record))
    report['source_sha256'] = {}
    report['artifact_sha256'] = {'cycle-01/input.json': hashlib.sha256(record_path.read_bytes()).hexdigest()}
    for name in ('fea/current_response_run.py', 'scripts/bolted_kerf_diagnostic_probe.py',
                 'scripts/bolted_kerf_native_diagnostic.py'):
        source = tmp_path / 'source_snapshots' / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(name.encode())
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        report['source_sha256'][name] = source_hash
        report['artifact_sha256'][f'source_snapshots/{name}'] = source_hash
    sidecar = tmp_path / 'diagnostic-scope.json'
    sidecar.write_text(json.dumps(report['diagnostic_scope']))
    report['artifact_sha256'][sidecar.name] = hashlib.sha256(sidecar.read_bytes()).hexdigest()
    report_path = tmp_path / 'report.json'
    report_path.write_text(json.dumps(report))
    return report_path, record_path, report, record


def test_file_entry_binds_accepted_report_and_record(tmp_path):
    report_path, record_path, report, _ = file_fixture(tmp_path)
    report['diagnostic_scope']['connection_stiffness_scale'] = 0.1
    report['parameters']['contact_penalty_n_per_mm'] = 1234.0
    sidecar = report_path.parent / 'diagnostic-scope.json'
    sidecar.write_text(json.dumps(report['diagnostic_scope']))
    report['artifact_sha256'][sidecar.name] = hashlib.sha256(sidecar.read_bytes()).hexdigest()
    report_path.write_text(json.dumps(report))
    result = extract_files(report_path, record_path, 'principal', 'post', 'header')
    assert result['source']['report_sha256'] == hashlib.sha256(report_path.read_bytes()).hexdigest()
    assert result['source']['record_sha256'] == hashlib.sha256(record_path.read_bytes()).hexdigest()
    assert result['source']['case'] == 'a12-rear'
    assert result['source']['diagnostic_scope'] == report['diagnostic_scope']
    assert result['source']['parameters'] == report['parameters']
    assert result['source']['candidate'] == report['candidate']
    assert result['status']['convergence'] == 'passed'
    assert result['status']['source'] == 'verified'
    assert result['status']['equilibrium'] == 'unavailable'


@pytest.mark.parametrize('change, message', [
    (lambda r, i: r.update(numerically_accepted=False), 'numerically accepted'),
    (lambda r, i: r.update(contact_active_set_converged=False), 'convergence'),
    (lambda r, i: r['diagnostic_scope'].update(case='a1-rear'), 'case'),
    (lambda r, i: r['artifact_sha256'].update({'cycle-01/input.json': '0' * 64}), 'digest'),
    (lambda r, i: r['source_sha256'].update({'fea/current_response_run.py': '0' * 64}), 'source'),
    (lambda r, i: r['source_sha256'].update({'scripts/bolted_kerf_diagnostic_probe.py': '0' * 64}), 'source'),
    (lambda r, i: r['contact_cycles'].append({'directory': 'cycle-02', 'contact_passed': True}), 'final report cycle'),
    (lambda r, i: i.pop('kerf_panel_bounds'), 'width'),
    (lambda r, i: r.pop('diagnostic_scope'), 'scope'),
    (lambda r, i: r['physical_connection_forces'].pop('base_beam_1'), 'Missing physical connection'),
])
def test_file_entry_rejects_unfit_evidence(tmp_path, change, message):
    report_path, record_path, report, record = file_fixture(tmp_path)
    change(report, record)
    report_path.write_text(json.dumps(report))
    record_path.write_text(json.dumps(record))
    if 'diagnostic_scope' in report:
        sidecar = report_path.parent / 'diagnostic-scope.json'
        sidecar.write_text(json.dumps(report['diagnostic_scope']))
        report['artifact_sha256'][sidecar.name] = hashlib.sha256(sidecar.read_bytes()).hexdigest()
        report_path.write_text(json.dumps(report))
    if 'kerf_panel_bounds' not in record:
        report['artifact_sha256']['cycle-01/input.json'] = hashlib.sha256(record_path.read_bytes()).hexdigest()
        report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match=message):
        extract_files(report_path, record_path, 'principal', 'post', 'header')


def test_file_entry_rejects_scope_sidecar_mismatch(tmp_path):
    report_path, record_path, report, _ = file_fixture(tmp_path)
    sidecar = report_path.parent / 'diagnostic-scope.json'
    sidecar.write_text('{}')
    with pytest.raises(ValueError, match='scope sidecar or digest'):
        extract_files(report_path, record_path, 'principal', 'post', 'header')
    report['artifact_sha256'][sidecar.name] = hashlib.sha256(sidecar.read_bytes()).hexdigest()
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match='scope sidecar or digest'):
        extract_files(report_path, record_path, 'principal', 'post', 'header')
