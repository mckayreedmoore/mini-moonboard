"""Scenario identity guards; all response fixtures here are synthetic."""
import ast
import copy
import math
from pathlib import Path

import pytest

from scripts.clear_space_case_contract import (
    NO_SLIP_SCOPE,
    validate_case_identity,
    validate_floor_model,
)

CANDIDATE = 'compact-floor-flush-development'
CASES = {
    'a12-left': ('A12', (-300., 0.)),
    'a12-rear': ('A12', (0., 300.)),
    'a12-forward': ('A12', (0., -300.)),
    'k12-right': ('K12', (300., 0.)),
    'k12-rear': ('K12', (0., 300.)),
    'a1-rear': ('A1', (0., 300.)),
}


def response(case='a12-left', mu=None):
    hold, (fx, fy) = CASES[case]
    result = {
        'candidate': CANDIDATE, 'numerically_accepted': True,
        'floor_scope': NO_SLIP_SCOPE,
        'parameters': {'hold': hold, 'pounds': 250., 'force_xyz_n': [fx, fy, -2224.]},
        'bearings': [{'name': 'floor_test_0', 'active': True},
                     {'name': 'floor_test_1', 'active': False}],
    }
    if mu is not None:
        result['parameters']['floor_friction_assumption'] = {
            'mu': mu, 'per_cell_coulomb': True, 'centroid_tangent_springs_removed': True}
        result['floor_friction_law'] = {'feet': {
            'floor_test_0_friction': {'next_secant_n_per_mm': 100.}}}
    return result


def validate(report, case='a12-left', mu=None):
    hold, force = CASES[case]
    validate_case_identity(report, expected_candidate=CANDIDATE,
        expected_hold=hold, expected_pounds=250., expected_horizontal_force=force,
        friction_mu=mu)


@pytest.mark.parametrize('case', CASES)
def test_each_matching_no_slip_case_is_accepted(case):
    validate(response(case), case)


@pytest.mark.parametrize('actual', CASES)
@pytest.mark.parametrize('requested', CASES)
def test_only_same_case_can_be_reused(actual, requested):
    if actual == requested:
        validate(response(actual), requested)
    else:
        with pytest.raises(ValueError):
            validate(response(actual), requested)


@pytest.mark.parametrize('mu', [.2, .4, .8])
def test_matching_finite_friction_is_supported(mu):
    validate(response(mu=mu), mu=mu)


def test_finite_friction_cannot_be_promoted_to_no_slip():
    with pytest.raises(ValueError, match='finite-friction'):
        validate(response(mu=.4))


def test_no_slip_cannot_be_promoted_to_finite_friction():
    with pytest.raises(ValueError, match='floor_friction_assumption'):
        validate(response(), mu=.4)


def test_changed_friction_coefficient_is_rejected():
    with pytest.raises(ValueError, match='mu'):
        validate(response(mu=.4), mu=.6)


@pytest.mark.parametrize('field', ['per_cell_coulomb', 'centroid_tangent_springs_removed'])
@pytest.mark.parametrize('value', [False, None, 1, 'true'])
def test_missing_or_nonboolean_friction_flags_fail(field, value):
    report = response(mu=.4)
    report['parameters']['floor_friction_assumption'][field] = value
    with pytest.raises(ValueError):
        validate(report, mu=.4)


@pytest.mark.parametrize('value', [None, '', 'no slip', 'finite friction'])
def test_no_slip_scope_is_explicit(value):
    report = response()
    report['floor_scope'] = value
    with pytest.raises(ValueError, match='scope'):
        validate(report)


@pytest.mark.parametrize('field,value', [
    ('candidate', 'historical-candidate'), ('numerically_accepted', False),
    ('numerically_accepted', 1), ('numerically_accepted', None),
])
def test_candidate_and_numerical_status_fail_closed(field, value):
    report = response()
    report[field] = value
    with pytest.raises(ValueError):
        validate(report)


@pytest.mark.parametrize('field,value', [
    ('hold', 'K12'), ('pounds', 150.), ('pounds', None), ('pounds', True),
    ('pounds', float('nan')), ('pounds', float('inf')), ('pounds', '250'),
    ('force_xyz_n', [0., 300., -2224.]), ('force_xyz_n', [-300., 0.]),
    ('force_xyz_n', [-300., 0., float('nan')]), ('force_xyz_n', [-300., False, -2224.]),
    ('force_xyz_n', None),
])
def test_malformed_or_wrong_parameters_are_rejected(field, value):
    report = response()
    report['parameters'][field] = value
    with pytest.raises(ValueError):
        validate(report)


@pytest.mark.parametrize('value', [None, [], 'parameters'])
def test_malformed_parameter_container_is_rejected(value):
    report = response()
    report['parameters'] = value
    with pytest.raises(ValueError):
        validate(report)


@pytest.mark.parametrize('value', [0., -1., float('nan'), float('inf'), True, '0.4'])
def test_invalid_requested_friction_is_rejected(value):
    with pytest.raises(ValueError):
        validate(response(mu=.4), mu=value)


def load_seed_function():
    """Execute the real batch helper without loading its CAD/solver imports."""
    path = Path(__file__).resolve().parents[1]/'scripts/clear_space_batch.py'
    tree = ast.parse(path.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == 'next_case_seed')
    namespace = {'validate_floor_model': validate_floor_model}
    # Execute only the parsed helper definition so this dependency-free unit test
    # exercises production control flow without importing CAD/solver modules.
    exec(  # noqa: S102
        compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace
    )
    return namespace['next_case_seed']


def test_actual_batch_seed_rejects_finite_friction_for_no_slip():
    with pytest.raises(ValueError, match='finite-friction'):
        load_seed_function()(response(mu=.4), None)


def test_actual_batch_seed_retains_only_active_normal_contacts():
    assert load_seed_function()(response()) == {'initial_contact_names': ['floor_test_0']}


def test_actual_batch_seed_retains_matching_friction_search_state():
    seed = load_seed_function()(response(mu=.4), .4)
    assert seed['initial_tangent_secants'] == {'floor_test_0_friction': 100.}


def test_batch_calls_identity_validator_before_archive():
    path = Path(__file__).resolve().parents[1]/'scripts/clear_space_batch.py'
    tree = ast.parse(path.read_text())
    calls = [(n.lineno, n.func.id) for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
    identity = [line for line, name in calls if name == 'validate_case_identity']
    archive = [line for line, name in calls if name == 'archive']
    assert len(identity) == len(archive) == 1
    assert identity[0] < archive[0]


def test_validation_does_not_modify_report():
    report = response()
    saved = copy.deepcopy(report)
    validate(report)
    assert report == saved


def test_no_relative_tolerance_permits_changed_magnitude():
    report = response()
    report['parameters']['force_xyz_n'][0] -= .000001
    with pytest.raises(ValueError, match='horizontal'):
        validate(report)


def test_minimal_serialization_roundoff_is_allowed():
    report = response()
    report['parameters']['pounds'] += 1.e-10
    validate(report)
    assert math.isfinite(report['parameters']['pounds'])


@pytest.mark.parametrize('case,mu,raises', [
    ('a12-left', None, False),
    ('a12-rear', None, True),
    ('k12-right', None, True),
    ('a12-left', .4, True),
])
def test_existing_first_cli_path_checks_before_archive(tmp_path, monkeypatch, case, mu, raises):
    """Run the real batch CLI with explicit synthetic CAD/solver dependencies."""
    import json
    import runpy
    import subprocess
    import sys
    import types

    called = []
    fake_modules = {
        'fea.current_response_run': types.ModuleType('fea.current_response_run'),
        'scripts.clear_space_results': types.ModuleType('scripts.clear_space_results'),
        'scripts.clear_space_study': types.ModuleType('scripts.clear_space_study'),
        'scripts.compact_rail_study': types.ModuleType('scripts.compact_rail_study'),
        'mini_moonboard.contract_fixture': types.ModuleType('mini_moonboard.contract_fixture'),
    }
    fake_modules['fea.current_response_run'].run = lambda *a, **k: pytest.fail('No native run expected')
    fake_modules['scripts.clear_space_results'].PREFIXES = ('fixture_bolt',)
    fake_modules['scripts.clear_space_results'].checks = lambda *a: {
        'criteria': {'SYNTHETIC_ONLY': True}, 'status': 'SYNTHETIC_ONLY'}
    fake_modules['scripts.clear_space_study'].MODELS = {'fixture': 'contract_fixture'}
    fake_modules['scripts.clear_space_study'].geometry = lambda model: {
        'candidate': CANDIDATE, 'receiver_fit_pass': True}
    fake_modules['scripts.compact_rail_study'].bolt_properties = lambda c: {}
    model = fake_modules['mini_moonboard.contract_fixture']
    model.KEY = CANDIDATE
    model.__file__ = str(Path.cwd()/'mini_moonboard/contract_fixture.py')
    model.connections = list
    model.overlap_contact_datums = list
    for name, module in fake_modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    native = tmp_path/'native'
    native.mkdir()
    (native/'report.json').write_text(json.dumps(response(case, mu)))
    out = tmp_path/'archive'
    (out/'a12-left').mkdir(parents=True)
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: called.append(a))
    monkeypatch.setattr(sys, 'argv', [
        'clear_space_batch', 'fixture', '--cases', 'a12-left',
        '--native-prefix', str(tmp_path/'unused'), '--archive-root', str(out),
        '--geometry', str(tmp_path/'geometry.json'), '--existing-first', str(native)])
    path = Path(__file__).resolve().parents[1]/'scripts/clear_space_batch.py'
    if raises:
        with pytest.raises(ValueError):
            runpy.run_path(str(path), run_name='__main__')
        assert called == []
        assert not (out/'a12-left'/'assessment.json').exists()
    else:
        runpy.run_path(str(path), run_name='__main__')
        assert len(called) == 1
        assert (out/'a12-left'/'assessment.json').exists()
