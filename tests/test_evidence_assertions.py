"""Platform-rounding allowances reject changed physical evidence and gates."""
import copy
import math

import pytest
from evidence_assertions import assert_replay_value, assert_stress_replay


def stress_result():
    witness = {'element': 7, 'integration_point': 2, 'coordinate_xyz_mm': [1., 2., 3.],
               'global_components_mpa': [1., 2., 3., .1, .2, .3],
               'local_tensor_mpa': [[1., .1, .2], [.1, 2., .3], [.2, .3, 3.]], 'value_mpa': 1.}
    return {'qualified_for_design': False, 'groups': [{'axes_xyz': [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]],
             'axis_labels': ['x', 'y', 'z'], 'extrema': {'normal_x': {'maximum': witness}}}]}


def test_stress_accepts_rounding_but_rejects_physics_identity_and_gate_changes():
    saved = stress_result()
    replay = copy.deepcopy(saved)
    value = replay['groups'][0]['extrema']['normal_x']['maximum']
    value['value_mpa'] = value['local_tensor_mpa'][0][0] = math.nextafter(1., 2.)
    assert_stress_replay(saved, replay)
    for field, changed in [('element', 8), ('global_components_mpa', [1.00001, 2., 3., .1, .2, .3]),
                           ('value_mpa', -1.), ('local_tensor_mpa', [[1.000001, .1, .2], [.1, 2., .3], [.2, .3, 3.]])]:
        bad = copy.deepcopy(replay)
        bad['groups'][0]['extrema']['normal_x']['maximum'][field] = changed
        with pytest.raises(AssertionError):
            assert_stress_replay(saved, bad)
    replay['qualified_for_design'] = True
    with pytest.raises(AssertionError):
        assert_stress_replay(saved, replay)


def test_work_bound_accounts_for_cancellation_without_allowing_changed_work(monkeypatch):
    monkeypatch.setattr('evidence_assertions.frame.panel_kernel.read_blocks',
                        lambda _: {'displacements': {1: [1., 1., 1.]}})
    record = {'loads': {'1': [1., -1., 1.e-10]}}
    assert_replay_value(1.e-10, 1.e-10+1.e-16, 'load_work_nmm', record, '')
    with pytest.raises(AssertionError):
        assert_replay_value(1.e-10, 1.e-8, 'load_work_nmm', record, '')


def test_signed_connector_components_and_gate_cannot_use_norm_tolerance():
    saved = {'joint': {'force_magnitude_n': 1., 'force_on_first_xyz_n': [1., 0., 0.]}}
    replay = copy.deepcopy(saved)
    replay['joint']['force_magnitude_n'] = math.nextafter(1., 2.)
    assert_replay_value(saved, replay, 'connector_forces')
    replay['joint']['force_on_first_xyz_n'][0] = math.nextafter(1., 2.)
    with pytest.raises(AssertionError):
        assert_replay_value(saved, replay, 'connector_forces')
    with pytest.raises(AssertionError):
        assert_replay_value(False, True, 'mpc_check_passed')
