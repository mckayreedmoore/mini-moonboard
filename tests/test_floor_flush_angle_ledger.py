"""Synthetic fixtures only: these tests do not contain or qualify a native solve."""
import copy
import hashlib
import json
import math
import random

import pytest

from fea.reinforced_fastener_checks import wrench as repository_wrench
from scripts.clear_space_case_contract import NO_SLIP_SCOPE
from scripts.floor_flush_angle_ledger import (
    CANDIDATE,
    CASES,
    VALIDITY,
    build_ledger,
    inspect_case,
    main,
    read_json,
    verify_manifest,
    wrench_diagnostic,
)


def row(force, point=(0., 0., 0.), name='fixture', receiver='fixture_wood'):
    return {'first': receiver, 'second': name, 'point': list(point),
        'force_on_first_xyz_n': [-v for v in force],
        'force_on_second_xyz_n': list(force)}


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_case(root, case, *, source=b'# SYNTHETIC SOURCE; not a structural model\n'):
    native = root/case
    native.mkdir(parents=True)
    snapshot = native/'source_snapshots'/'fixture.py'
    snapshot.parent.mkdir()
    snapshot.write_bytes(source)
    artifact = native/'cycle-00'/'frame.inp'
    artifact.parent.mkdir()
    artifact.write_text('SYNTHETIC HASH FIXTURE; not a solver deck\n')
    hold, force = CASES[case]
    report = {
        'candidate': CANDIDATE, 'floor_scope': NO_SLIP_SCOPE,
        **{key: True for key in VALIDITY},
        'parameters': {'hold': hold, 'pounds': 250., 'force_xyz_n': [*force, -2224.],
                       'fixture': 'SYNTHETIC; not a solved model'},
        'source_sha256': {'fixture.py': sha(snapshot)},
        'artifact_sha256': {'cycle-00/frame.inp': sha(artifact),
                           'source_snapshots/fixture.py': sha(snapshot)},
        'angle_stations': [], 'physical_connection_forces': {},
    }
    assessment = {'candidate': CANDIDATE, 'commercial_angles': {}}
    for index in range(24):
        name = f'clip_synthetic_{index:02}'
        origin = [float(index), 0., 0.]
        report['angle_stations'].append({'name': name, 'origin_mm': origin})
        groups = {}
        for flange, sign in [('beam', 1), ('upright', -1)]:
            group = []
            for i, (f, p) in enumerate([
                    ((100., 0., 0.), (0., 10., 0.)),
                    ((0., 100., 0.), (0., 20., 0.)),
                    ((0., 0., 100.), (0., 30., 1.))], 1):
                record = row(tuple(sign*v for v in f), p, name, 'wood_'+flange)
                report['physical_connection_forces'][f'{name}_{flange}_{i}'] = record
                group.append(record)
            groups[flange] = group
        flanges = {key: repository_wrench(group, origin) for key, group in groups.items()}
        bearing = index % 2 == 0
        loaded = flanges['upright' if bearing else 'beam']['force_xyz_n']
        assessment['commercial_angles'][name] = {
            'origin_mm': origin, 'flange_member_on_bracket_wrenches': flanges,
            'all_six_screw_residual': repository_wrench(groups['beam']+groups['upright'], origin),
            'bearing_like': bearing,
            'projected_loaded_flange_force_n': {'F1': loaded[1], 'F2': loaded[2], 'F34': loaded[0]},
            'rated_force_component_unity': .2,
            'unlisted_separation_demand_n': max(0., loaded[2]) if bearing else None,
        }
    report_path, assessment_path = native/'report.json', native/'assessment.json'
    save_json(report_path, report)
    save_json(assessment_path, assessment)
    return case, native, assessment_path


def fixtures(root):
    return [fixture_case(root, case) for case in CASES]


def test_six_case_ledger_reconstructs_288_flange_records_and_never_releases(tmp_path):
    result = build_ledger(fixtures(tmp_path))
    assert result['case_count'] == 6
    assert result['flange_case_records'] == 288
    assert result['construction_release'] is False
    assert result['connection_resistance_established'] is False
    for case in result['cases'].values():
        assert case['source_snapshot_count_verified'] == 1
        assert case['manifest_declared_artifact_count_verified'] == 2
        assert not case['native_solver_replayed']
        for angle in case['angles'].values():
            assert angle['unlisted_separation_capacity_n'] is None
            assert not angle['connection_qualified']
            assert angle['all_six_screw_equilibrium_residual']['force_xyz_n'] == [0., 0., 0.]
            assert angle['flanges']['beam']['force_norm_n'] > 0
            assert angle['flanges']['beam']['moment_capacity_nmm'] is None


def test_pure_couple_is_not_lost_when_resultant_force_is_zero():
    rows = [row((100., 0., 0.)), row((-100., 0., 0.), (0., 10., 0.))]
    result = wrench_diagnostic(rows, [0., 0., 0.])
    assert result['force_norm_n'] == 0
    assert result['signed_parallel_couple_nmm'] is None
    assert result['moment_xyz_nmm'] == [0., 0., 1000.]
    assert result['independent_or_near_zero_force_moment_norm_nmm'] == 1000.
    assert result['moment_capacity_nmm'] is None


def test_near_zero_force_retains_full_origin_moment():
    rows = [row((100., 0., 0.)), row((-100.+1.e-10, 0., 0.), (0., 10., 0.))]
    result = wrench_diagnostic(rows, [0., 0., 0.])
    assert result['force_direction_unresolved']
    assert result['moment_norm_nmm'] == pytest.approx(1000.)


def test_nonparallel_origin_moment_is_preserved():
    result = wrench_diagnostic([row((0., 0., 10.), (2., 0., 0.))], [0., 0., 0.])
    assert result['moment_xyz_nmm'] == [0., -20., 0.]
    assert result['independent_or_near_zero_force_moment_norm_nmm'] == 0.
    assert result['moment_norm_nmm'] == 20.


def test_1000_random_wrenches_match_actual_repository_helper_and_translation_invariant():
    rng = random.Random(619)
    for _ in range(1000):
        rows = [row(tuple(rng.uniform(-500, 500) for _ in range(3)),
                    tuple(rng.uniform(-100, 100) for _ in range(3))) for _ in range(3)]
        origin = [rng.uniform(-100, 100) for _ in range(3)]
        other = [rng.uniform(-100, 100) for _ in range(3)]
        actual = wrench_diagnostic(rows, origin)
        expected = repository_wrench(rows, origin)
        translated = wrench_diagnostic(rows, other)
        assert actual['force_xyz_n'] == pytest.approx(expected['force_xyz_n'])
        assert actual['moment_xyz_nmm'] == pytest.approx(expected['moment_xyz_nmm'])
        assert actual['signed_parallel_couple_nmm'] == pytest.approx(expected['parallel_couple_nmm'], abs=1.e-7)
        assert actual['signed_parallel_couple_nmm'] == pytest.approx(translated['signed_parallel_couple_nmm'], abs=1.e-7)


@pytest.mark.parametrize('field', ['force_on_first_xyz_n', 'force_on_second_xyz_n', 'point'])
def test_nonfinite_force_rows_fail(field):
    record = row((1., 2., 3.))
    record[field][0] = float('nan')
    with pytest.raises(ValueError):
        wrench_diagnostic([record], [0., 0., 0.])


def test_action_reaction_error_is_rejected():
    record = row((1., 2., 3.))
    record['force_on_first_xyz_n'][0] = 99.
    with pytest.raises(ValueError, match='action/reaction'):
        wrench_diagnostic([record], [0., 0., 0.])


@pytest.mark.parametrize('count', [0, 1, 5])
def test_missing_cases_are_not_called_complete(tmp_path, count):
    entries = fixtures(tmp_path)[:count]
    with pytest.raises(ValueError, match='six distinct'):
        build_ledger(entries)


def test_duplicate_case_is_rejected(tmp_path):
    entries = fixtures(tmp_path)
    entries[-1] = entries[0]
    with pytest.raises(ValueError, match='six distinct'):
        build_ledger(entries)


def test_input_order_does_not_change_required_case_order(tmp_path):
    result = build_ledger(list(reversed(fixtures(tmp_path))))
    assert result['case_order'] == list(CASES)


def test_mixed_source_revisions_fail_even_when_each_hash_is_valid(tmp_path):
    entries = [fixture_case(tmp_path, case, source=(b'new synthetic\n' if i else b'old synthetic\n'))
               for i, case in enumerate(CASES)]
    with pytest.raises(ValueError, match='Mixed source'):
        build_ledger(entries)


def test_changed_common_model_parameters_fail(tmp_path):
    entries = fixtures(tmp_path)
    path = entries[-1][1]/'report.json'
    report = read_json(path)
    report['parameters']['fixture'] = 'different synthetic stiffness model'
    save_json(path, report)
    with pytest.raises(ValueError, match='Mixed source'):
        build_ledger(entries)


@pytest.mark.parametrize('relative', ['cycle-00/frame.inp', 'source_snapshots/fixture.py'])
def test_changed_artifact_or_source_bytes_are_rejected(tmp_path, relative):
    case, native, assessment = fixture_case(tmp_path, 'a12-left')
    (native/relative).write_text('tampered\n')
    with pytest.raises(ValueError, match='checksum'):
        inspect_case(case, native, assessment)


@pytest.mark.parametrize('path', ['../outside', '/etc/passwd', 'a/../../outside', './a', 'a\\b', 'C:/a'])
def test_manifest_paths_cannot_escape_root(tmp_path, path):
    with pytest.raises(ValueError):
        verify_manifest(tmp_path, {path: '0'*64})


def test_manifest_symlink_escape_fails(tmp_path):
    inside = tmp_path/'inside'
    inside.mkdir()
    outside = tmp_path/'outside'
    outside.write_text('secret')
    (inside/'link').symlink_to(outside)
    with pytest.raises(ValueError, match='escaping'):
        verify_manifest(inside, {'link': sha(outside)})


@pytest.mark.parametrize('value', [{}, None, {'a': 'bad-digest'}])
def test_absent_or_malformed_manifests_fail(tmp_path, value):
    with pytest.raises(ValueError):
        verify_manifest(tmp_path, value)


@pytest.mark.parametrize('text', ['{"x": 1, "x": 2}', '{"x": NaN}', '{"x": Infinity}'])
def test_duplicate_or_nonfinite_json_is_not_silently_accepted(tmp_path, text):
    path = tmp_path/'bad.json'
    path.write_text(text)
    with pytest.raises(ValueError):
        read_json(path)


@pytest.mark.parametrize('mutation', ['candidate', 'hold', 'nonconverged', 'station_count', 'station_duplicate', 'missing_screw', 'ownership', 'finite_friction'])
def test_invalid_native_evidence_is_rejected(tmp_path, mutation):
    case, native, assessment = fixture_case(tmp_path, 'a12-left')
    path = native/'report.json'
    report = read_json(path)
    if mutation == 'candidate':
        report['candidate'] = 'old-candidate'
    elif mutation == 'hold':
        report['parameters']['hold'] = 'K12'
    elif mutation == 'nonconverged':
        report['member_equilibrium_passed'] = False
    elif mutation == 'station_count':
        report['angle_stations'].pop()
    elif mutation == 'station_duplicate':
        report['angle_stations'][-1] = copy.deepcopy(report['angle_stations'][0])
    elif mutation == 'missing_screw':
        report['physical_connection_forces'].pop('clip_synthetic_00_beam_1')
    elif mutation == 'ownership':
        report['physical_connection_forces']['clip_synthetic_00_beam_1']['second'] = 'other_angle'
    elif mutation == 'finite_friction':
        report['parameters']['floor_friction_assumption'] = {'mu': .4}
    save_json(path, report)
    with pytest.raises(ValueError):
        inspect_case(case, native, assessment)


@pytest.mark.parametrize('mutation', ['origin', 'moment', 'force', 'residual', 'inventory', 'ratio_nan', 'separation'])
def test_stale_or_invalid_assessment_fields_fail(tmp_path, mutation):
    case, native, path = fixture_case(tmp_path, 'a12-left')
    assessment = read_json(path)
    angle = assessment['commercial_angles']['clip_synthetic_00']
    if mutation == 'origin':
        angle['origin_mm'][0] += 1.
    elif mutation in ('moment', 'force'):
        angle['flange_member_on_bracket_wrenches']['beam'][mutation+'_xyz_'+('nmm' if mutation == 'moment' else 'n')][0] += 1.
    elif mutation == 'residual':
        angle['all_six_screw_residual']['moment_xyz_nmm'][1] += 1.
    elif mutation == 'inventory':
        assessment['commercial_angles'].pop('clip_synthetic_01')
    elif mutation == 'ratio_nan':
        angle['rated_force_component_unity'] = 'nan'
    elif mutation == 'separation':
        angle['unlisted_separation_demand_n'] = 1.
    save_json(path, assessment)
    with pytest.raises(ValueError):
        inspect_case(case, native, path)


def test_supplied_failed_ratio_is_not_hidden_or_called_a_pass(tmp_path):
    case, native, path = fixture_case(tmp_path, 'a12-left')
    assessment = read_json(path)
    assessment['commercial_angles']['clip_synthetic_00']['rated_force_component_unity'] = 1.5
    save_json(path, assessment)
    angle = inspect_case(case, native, path)['angles']['clip_synthetic_00']
    assert angle['rated_force_component_unity_as_reported'] == 1.5
    assert not angle['rated_resistance_recomputed']
    assert not angle['connection_qualified']


def test_optional_current_source_check(tmp_path):
    case, native, path = fixture_case(tmp_path/'cases', 'a12-left')
    current = tmp_path/'current'
    current.mkdir()
    (current/'fixture.py').write_bytes((native/'source_snapshots/fixture.py').read_bytes())
    assert inspect_case(case, native, path, current_source_root=current)['current_sources_checked']
    (current/'fixture.py').write_text('changed producer')
    with pytest.raises(ValueError, match='checksum'):
        inspect_case(case, native, path, current_source_root=current)


def test_cli_creates_only_diagnostic_json_and_refuses_overwrite(tmp_path):
    entries = fixtures(tmp_path/'cases')
    output = tmp_path/'ledger.json'
    args = ['--output', str(output)]
    for name, native, assessment in entries:
        args += ['--case', name, str(native), str(assessment)]
    main(args)
    result = read_json(output)
    assert result['construction_release'] is False
    assert math.isfinite(result['case_count'])
    saved = output.read_bytes()
    with pytest.raises(FileExistsError):
        main(args)
    assert output.read_bytes() == saved


def test_extra_screw_is_not_silently_ignored(tmp_path):
    case, native, assessment = fixture_case(tmp_path, 'a12-left')
    path = native/'report.json'
    report = read_json(path)
    report['physical_connection_forces']['clip_synthetic_00_beam_4'] = copy.deepcopy(
        report['physical_connection_forces']['clip_synthetic_00_beam_1'])
    save_json(path, report)
    with pytest.raises(ValueError, match='exactly six'):
        inspect_case(case, native, assessment)


def test_changed_station_origin_between_cases_is_rejected(tmp_path):
    entries = fixtures(tmp_path)
    case, native, assessment_path = entries[-1]
    report = read_json(native/'report.json')
    assessment = read_json(assessment_path)
    station = report['angle_stations'][0]
    station['origin_mm'][0] += 1.
    angle = assessment['commercial_angles'][station['name']]
    angle['origin_mm'] = station['origin_mm']
    groups = {flange: [report['physical_connection_forces'][f"{station['name']}_{flange}_{i}"]
                      for i in (1, 2, 3)] for flange in ('beam', 'upright')}
    angle['flange_member_on_bracket_wrenches'] = {
        flange: repository_wrench(rows, station['origin_mm']) for flange, rows in groups.items()}
    angle['all_six_screw_residual'] = repository_wrench(groups['beam']+groups['upright'], station['origin_mm'])
    save_json(native/'report.json', report)
    save_json(assessment_path, assessment)
    inspect_case(case, native, assessment_path)  # individually self-consistent
    with pytest.raises(ValueError, match='Mixed source'):
        build_ledger(entries)


def test_input_changed_after_read_is_rejected(tmp_path, monkeypatch):
    import scripts.floor_flush_angle_ledger as module
    case, native, assessment_path = fixture_case(tmp_path, 'a12-left')
    original = module.verify_manifest
    def changed(root, manifest):
        result = original(root, manifest)
        assessment = read_json(assessment_path)
        assessment['changed_during_audit'] = True
        save_json(assessment_path, assessment)
        return result
    monkeypatch.setattr(module, 'verify_manifest', changed)
    with pytest.raises(ValueError, match='changed during'):
        inspect_case(case, native, assessment_path)


def test_loaded_consumer_source_identity_is_enforced(tmp_path, monkeypatch):
    import scripts.floor_flush_angle_ledger as module
    entries = fixtures(tmp_path)
    monkeypatch.setattr(module, '_consumer_hashes', lambda: {'wrong': 'identity'})
    with pytest.raises(ValueError, match='Consumer sources changed'):
        build_ledger(entries)
