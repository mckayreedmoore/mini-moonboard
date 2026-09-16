import hashlib
import json
from pathlib import Path

import pytest


def test_a12_left_launch_uses_selected_candidate_and_no_slip_runner(tmp_path, monkeypatch):
    from scripts import compact_spliced_flush_top_study as study

    captured = {}

    def fake_run(output, **kwargs):
        captured.update(output=output, **kwargs)
        return {'candidate': study.candidate.KEY, 'numerically_accepted': False}

    monkeypatch.setattr(study, 'run', fake_run)
    output = tmp_path / 'native-a12-left'
    result = study.launch(output)
    assert result['candidate'] == 'compact-spliced-flush-top-development'
    assert captured['output'] == output
    assert captured['hold'] == 'A12'
    assert captured['horizontal_force'] == (-300., 0.)
    assert captured['pounds'] == 250.
    assert captured['leg_floor_grid'] == 3
    assert captured['patch_size'] == 20.
    assert 'module' not in captured
    assert 'expected_candidate' not in captured
    assert 'prepare_factory' not in captured
    assert 'mu' not in captured
    assert set(captured['bolt_stiffness']['by_name']) == {
        connection.name for connection in study.candidate.connections()
        if connection.kind == 'bolt'
    }
    assert captured['member_contacts']


def test_case_launch_accepts_explicit_hold_direction_and_current_contact_seed(tmp_path, monkeypatch):
    from scripts import compact_spliced_flush_top_study as study

    captured = {}
    monkeypatch.setattr(study, 'run', lambda output, **kwargs: captured.update(kwargs) or {})
    seed = tmp_path / 'seed.json'
    seed.write_text(json.dumps({'candidate': study.candidate.KEY, 'numerically_accepted': True,
        'bearings': [{'name': 'seat_a', 'active': True}, {'name': 'seat_b', 'active': False}]}))
    study.launch(tmp_path / 'native', hold='K12', horizontal=(300., 0.), contact_seed=seed)
    assert captured['hold'] == 'K12'
    assert captured['horizontal_force'] == (300., 0.)
    assert captured['initial_contact_names'] == ['seat_a']


def test_case_matrix_is_the_frozen_six_case_envelope():
    from scripts.compact_spliced_flush_top_study import CASES

    assert CASES == {
        'a12-left': ('A12', (-300., 0.)),
        'a12-rear': ('A12', (0., 300.)),
        'a12-forward': ('A12', (0., -300.)),
        'k12-right': ('K12', (300., 0.)),
        'k12-rear': ('K12', (0., 300.)),
        'a1-rear': ('A1', (0., 300.)),
    }


def test_selected_candidate_requests_exact_prisms_for_trimmed_members():
    from mini_moonboard import compact_spliced_flush_top as candidate

    assert candidate.NATIVE_SQUARE_END_MEMBERS == ()
    assert candidate.runner_end_geometry() == {}


def test_geometry_adapter_records_candidate_and_its_own_source(tmp_path, monkeypatch):
    from scripts import compact_spliced_flush_top_geometry as geometry

    monkeypatch.setattr(geometry, 'build', lambda model: {
        'candidate': model.KEY,
        'geometries_by_bolt_name': {},
        'source_sha256': {str(Path(model.__file__).resolve().relative_to(Path.cwd())): 'model'},
    })
    monkeypatch.setattr(geometry.candidate, 'connections', lambda: ())
    monkeypatch.setattr(geometry.candidate, 'overlap_contact_datums', list)
    reference = tmp_path / 'reference.json'
    reference.write_text(json.dumps({
        'hardware_by_name': {},
        'hardware_resistance_bounds_by_name': {},
    }))
    monkeypatch.setattr(geometry, 'HARDWARE_REFERENCE', reference)
    output = tmp_path / 'geometry.json'
    result = geometry.generate(output)
    adapter = str(Path(geometry.__file__).resolve().relative_to(Path.cwd()))
    assert json.loads(output.read_text()) == result
    assert result['candidate'] == geometry.candidate.KEY
    assert result['source_sha256'][adapter] == hashlib.sha256(Path(geometry.__file__).read_bytes()).hexdigest()


def test_real_geometry_contains_complete_splice_resistance_inputs(tmp_path):
    from scripts import compact_spliced_flush_top_geometry as geometry

    result = geometry.generate(tmp_path / 'geometry.json')
    bolts = {
        connection.name for connection in geometry.candidate.connections()
        if connection.kind == 'bolt'
    }
    assert result['receiver_fit_pass'] is True
    assert set(result['hardware_by_name']) == bolts
    assert set(result['hardware_resistance_bounds_by_name']) == bolts
    assert len(result['splice_contact_datums']) == 18
    assert result['bolt_material_basis']['bending_yield_psi'] == 90000.


def test_geometry_rejects_historical_bound_when_hardware_metadata_differs():
    from scripts.compact_spliced_flush_top_geometry import resistance_bounds

    current = {'bolt_1': {'diameter_mm': 12.7, 'length_mm': 215.9}}
    reference = {
        'hardware_by_name': {'bolt_1': {'diameter_mm': 12.7, 'length_mm': 203.2}},
        'hardware_resistance_bounds_by_name': {'bolt_1': {'actual_angle_n': 1000.}},
    }
    with pytest.raises(ValueError, match='metadata differs for bolt_1'):
        resistance_bounds(current, reference)


def test_results_adapter_invokes_generic_archive_and_splice_checks_explicitly(tmp_path, monkeypatch):
    from scripts import compact_spliced_flush_top_results as results

    native = tmp_path / 'native'
    native.mkdir()
    (native / 'report.json').write_text(json.dumps({'candidate': results.CANDIDATE}))
    geometry = tmp_path / 'geometry.json'
    geometry.write_text(json.dumps({'candidate': results.CANDIDATE}))
    output = tmp_path / 'archive'
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        output.mkdir(exist_ok=True)
        if command[2] == 'scripts.compact_two_results':
            for name in ('report.json.gz', 'geometry.json', 'sources.zip'):
                (output / name).write_text(name)
            (output / 'checks.json').write_text(json.dumps({'candidate': results.CANDIDATE}))
            (output / 'manifest.json').write_text(json.dumps({
                'candidate': results.CANDIDATE,
                'files': {
                    name: results.digest(output / name)
                    for name in ('report.json.gz', 'geometry.json', 'sources.zip')
                },
            }))
        else:
            (output / 'splice-checks.json').write_text(json.dumps({
                'candidate': results.CANDIDATE,
            }))

    monkeypatch.setattr(results.subprocess, 'run', run)
    results.archive_and_check(native, geometry, output)
    assert len(calls) == 2
    archive, splice = (row[0] for row in calls)
    assert archive[2] == 'scripts.compact_two_results'
    assert archive[archive.index('--expected-candidate') + 1] == results.CANDIDATE
    assert archive[archive.index('--model-source') + 1] == results.MODEL_SOURCE
    assert splice[2] == 'scripts.compact_splice_results'
    assert splice[splice.index('--expected-candidate') + 1] == results.CANDIDATE
    assert all(row[1]['check'] is True for row in calls)
    manifest = json.loads((output / 'manifest.json').read_text())
    assert set(manifest['files']) == {
        'report.json.gz', 'geometry.json', 'sources.zip', 'checks.json',
        'splice-checks.json',
    }
    assert all(manifest['files'][name] == results.digest(output / name)
               for name in manifest['files'])


def test_results_adapter_refuses_mismatched_inputs_or_existing_archive(tmp_path, monkeypatch):
    from scripts import compact_spliced_flush_top_results as results

    native = tmp_path / 'native'
    native.mkdir()
    geometry = tmp_path / 'geometry.json'
    output = tmp_path / 'archive'
    monkeypatch.setattr(results.subprocess, 'run', lambda *args, **kwargs: pytest.fail('must reject first'))

    (native / 'report.json').write_text(json.dumps({'candidate': 'compact-spliced-knee-development'}))
    geometry.write_text(json.dumps({'candidate': results.CANDIDATE}))
    with pytest.raises(ValueError, match='selected flush-top candidate'):
        results.archive_and_check(native, geometry, output)

    (native / 'report.json').write_text(json.dumps({'candidate': results.CANDIDATE}))
    output.mkdir()
    with pytest.raises(FileExistsError):
        results.archive_and_check(native, geometry, output)


def test_splice_checks_require_explicit_flush_top_identity():
    from scripts import compact_splice_results as splice

    report = {'candidate': 'compact-spliced-flush-top-development'}
    geometry = {'candidate': 'compact-spliced-flush-top-development'}
    with pytest.raises(ValueError, match='spliced-knee candidate identities'):
        splice.checks(report, geometry)
    assert splice.checks(report, geometry, expected_candidate=report['candidate']) == {
        'candidate': report['candidate'],
        'status': 'INVALID_RESPONSE_DIAGNOSTIC_ONLY',
        'qualified_for_design': False,
    }
