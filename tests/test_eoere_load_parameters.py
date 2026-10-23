"""Load-contract controls independent of any structural capacity formulas."""

import copy
import json

import numpy as np
import pytest

from scripts import eoere_weight_study as study
from scripts.eoere_load_parameters import (
    BASELINE_DOWNWARD_N,
    KG_PER_LB,
    LoadParameters,
    parameterize_case,
    parameterize_inputs,
    wrench,
)
from scripts.eoere_paired_frame_basis import CASES, ROOT
from scripts.eoere_weight_study import INPUTS, REFERENCE, compact_comparison


def example(name='a12-forward'):
    loads = [
        {'id': 'self-weight/frame', 'body': 'frame', 'point_xyz_mm': [10., 20., 30.],
         'force_xyz_n': [0., 0., -100.]},
        {'id': 'accessory/panel', 'body': 'panel', 'point_xyz_mm': [40., 50., 60.],
         'force_xyz_n': [0., 0., -25. * 9.80665]},
        {'id': 'climber/A12', 'body': 'panel', 'point_xyz_mm': [100., 200., 300.],
         'force_xyz_n': [0., -300., -BASELINE_DOWNWARD_N]},
    ]
    hold = {'label': 'A12', 'panel': 'panel', 'load_point_xyz_mm': [100., 200., 300.],
            'panel_midplane_xyz_mm': [100., 150., 250.], 'force_xyz_n': loads[-1]['force_xyz_n'],
            'moment_about_panel_midplane_xyz_nmm': np.cross([0., 50., 50.], loads[-1]['force_xyz_n']).tolist()}
    total = wrench(loads)
    return {'case_id': name, 'primary_load_basis': True, 'loads': loads, 'hold': hold,
            'applied_force_xyz_n': total[:3].tolist(),
            'applied_moment_about_global_origin_xyz_nmm': total[3:].tolist()}


def test_baseline_is_exact_identity_and_does_not_mutate():
    source = example()
    frozen = copy.deepcopy(source)
    changed = parameterize_case(source, LoadParameters())
    assert changed == source == frozen
    changed['loads'][0]['force_xyz_n'][2] = 1.
    assert source == frozen


def test_weight_change_preserves_dead_loads_and_updates_both_moments():
    source = example()
    changed = parameterize_case(source, LoadParameters(80., 'kg', 2.5, 400.))
    expected_force = np.array([0., -400., -80. * 2.5 * 9.80665])
    assert changed['loads'][:-1] == source['loads'][:-1]
    assert changed['loads'][-1]['force_xyz_n'] == expected_force.tolist()
    assert changed['hold']['force_xyz_n'] == expected_force.tolist()
    assert changed['hold']['moment_about_panel_midplane_xyz_nmm'] == np.cross([0., 50., 50.], expected_force).tolist()
    delta = expected_force - source['loads'][-1]['force_xyz_n']
    np.testing.assert_allclose(np.array(changed['applied_force_xyz_n']) - source['applied_force_xyz_n'], delta)
    np.testing.assert_allclose(np.array(changed['applied_moment_about_global_origin_xyz_nmm'])
                               - source['applied_moment_about_global_origin_xyz_nmm'],
                               np.cross([100., 200., 300.], delta))


def test_kg_and_lb_match_and_horizontal_can_be_zero():
    kg = LoadParameters(200. * KG_PER_LB, 'kg', horizontal_force_n=0.)
    lb = LoadParameters(200., 'lb', horizontal_force_n=0.)
    assert parameterize_case(example(), kg) == parameterize_case(example(), lb)
    assert parameterize_case(example(), kg)['hold']['force_xyz_n'][:2] == [0., 0.]


@pytest.mark.parametrize('kwargs', [
    {'weight': 0.}, {'weight': -1.}, {'weight': float('nan')}, {'weight': float('inf')},
    {'weight': True}, {'unit': 'lbs'}, {'downward_multiplier': 0.},
    {'downward_multiplier': -1.}, {'horizontal_force_n': -1.},
    {'horizontal_force_n': float('inf')}, {'weight': 1e308, 'downward_multiplier': 1e308},
])
def test_invalid_parameters_rejected(kwargs):
    with pytest.raises(ValueError):
        LoadParameters(**kwargs)


@pytest.mark.parametrize('tamper', ['two_climbers', 'different_force', 'resultant', 'nonbaseline'])
def test_incompatible_source_rejected(tamper):
    source = example()
    if tamper == 'two_climbers':
        source['loads'].append(copy.deepcopy(source['loads'][-1]))
    elif tamper == 'different_force':
        source['hold']['force_xyz_n'] = [1., 2., 3.]
    elif tamper == 'resultant':
        source['applied_force_xyz_n'][0] += 1.
    else:
        source['loads'][-1]['force_xyz_n'][2] = -100.
    with pytest.raises(ValueError):
        parameterize_case(source, LoadParameters())


def test_complete_bank_and_selected_case_are_required():
    source = {'cases': [example(c) for c in CASES], 'case': example(), 'scenario': {}}
    changed = parameterize_inputs(source, LoadParameters(90., 'kg'))
    assert changed['case'] == changed['cases'][0]
    assert source['case'] == example()
    source['cases'].pop()
    with pytest.raises(ValueError, match='complete six-case'):
        parameterize_inputs(source, LoadParameters())


def test_captured_baseline_is_exact_and_fixed_loads_stay_fixed():
    if not INPUTS.exists():
        pytest.skip('requires recovered current-frame input bank')
    source = json.loads(INPUTS.read_bytes())
    result = parameterize_inputs(source, LoadParameters())
    assert result['cases'] == source['cases']
    assert result['case'] == source['case']
    result = parameterize_inputs(source, LoadParameters(90., 'kg'))
    for old, new in zip(source['cases'], result['cases'], strict=True):
        assert old['loads'][:-1] == new['loads'][:-1]
        assert old['hold']['load_point_xyz_mm'] == new['hold']['load_point_xyz_mm']
        assert new['hold']['force_xyz_n'][2] == -1765.197
    assert source['gravity'] == result['gravity']
    assert source['geometry'] == result['geometry']


def test_compact_reduction_reports_each_current_exceedance_family():
    reference = json.loads(REFERENCE.read_bytes())['scenarios']['four_hosts']
    if not (ROOT / reference['shaft82_geometry_source']['path']).exists():
        pytest.skip('requires recovered current-frame worksheets')
    table = compact_comparison(reference)
    assert len(table) == 14
    assert max(r['value'] for r in table if r['component'] == 'left front post/runner') < 1.
    assert max(r['value'] for r in table if r['component'] == 'left upper long support/side rim') > 1.
    assert max(r['value'] for r in table) == pytest.approx(1.3437079665760525)


def test_preparation_captures_the_sources_needed_by_independent_replay(tmp_path, monkeypatch):
    source = {'cases': [example(c) for c in CASES], 'case': example(), 'scenario': {},
              'source_sha256': {}, 'geometry': {}, 'plywood_material': {}}
    mechanics = tmp_path / 'scripts/eoere_leg_header_mechanics.py'
    mechanics.parent.mkdir()
    mechanics.write_text('# independent replay requires this exact source\n')
    inputs = tmp_path / 'baseline.json'
    inputs.write_text(json.dumps(source))
    producer = tmp_path / 'weight.py'
    producer.write_bytes(study.OWN.read_bytes())
    monkeypatch.setattr(study, 'ROOT', tmp_path)
    monkeypatch.setattr(study, 'OWN', producer)
    monkeypatch.setattr(study, 'INPUTS', inputs)
    monkeypatch.setattr(study, 'REFERENCE', inputs)
    monkeypatch.setattr(study, 'baseline', lambda: copy.deepcopy(source))
    monkeypatch.setattr(study, 'ref', lambda p: {'path': str(p), 'sha256': study.sha(p)})
    out = tmp_path / 'fea/generated/study'
    study.prepare(out, LoadParameters(90., 'kg'))
    assert (out / 'preparation/producer-snapshot.py').read_bytes() == mechanics.read_bytes()
    assert (out / 'preparation/weight-study-producer.py').read_bytes() == producer.read_bytes()
    captured = json.loads((out / 'preparation/inputs.json').read_bytes())
    assert str(out / 'preparation/producer-snapshot.py') in captured['source_sha256']
    with pytest.raises(FileExistsError):
        study.prepare(out, LoadParameters())
