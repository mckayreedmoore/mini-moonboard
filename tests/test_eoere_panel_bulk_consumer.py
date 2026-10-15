"""Complete finite datum transport, retaining original numerical gates."""
import copy

import numpy as np
import pytest
import test_eoere_panel_bulk_coupling as reference

from scripts import eoere_panel_bulk_consumer as consumer
from scripts import eoere_panel_bulk_coupling as model


@pytest.fixture
def fixture():
    api = reference.source_api(); producer, base = consumer.context({})
    consumer.install_point_port(api, producer, reference.SOURCES, base, {})
    panel, screw, center = reference.fixture(api)
    screw = copy.deepcopy(screw); screw['point_xyz_mm'][2] = 4.5e-7
    return api, panel, screw, center


def patch(api, target):
    original = api.adapter.screw_port
    def mapped(panel, q, screw, tangent=True):
        return consumer.datum_port(panel, q, screw, target, original, tangent=tangent)
    api.adapter.screw_port = mapped
    return original


def test_original_frozen_datum_gate_rejects_then_explicit_map_preserves_it(fixture):
    api, panel, screw, center = fixture
    with pytest.raises(ValueError, match='datum precision'):
        model.interaction(panel, screw, center, center, np.eye(3), np.zeros(363), api)
    patch(api, screw['point_xyz_mm'])
    port, _, result = model.interaction(panel, screw, center, center, np.eye(3), np.zeros(363), api)
    assert np.array_equal(port['reference_position_xyz_mm'], screw['point_xyz_mm'])
    assert np.linalg.norm(port['position_xyz_mm']-screw['point_xyz_mm']) < 1e-12
    assert abs(result['energy_nmm']) < 1e-18


@pytest.mark.parametrize('handedness', [1., -1.])
def test_source_datum_map_retains_full_finite_rotation_work(fixture, handedness):
    api, panel, screw, center = fixture
    if handedness < 0:
        panel.axes[:, 2] *= -1; panel.geometry['axes'][:, 2] *= -1
        screw['basis'][0] = [0., 0., -1.]
    patch(api, screw['point_xyz_mm'])
    _, checked = model.controls(panel, screw, center, api,
        {'position_mm': 1e-8, 'energy_nmm': 1e-6, 'force_n': 1e-6, 'moment_nmm': 1e-5})
    assert checked['common_rigid_position_error_mm'] < 1e-8
    assert max(row['errors']['owner_rotation_work_nmm'] for row in checked['slip_controls']) < 1e-5


def test_nonzero_datum_extension_has_complete_gradient_and_hessian(fixture):
    api, panel, screw, center = fixture
    # A larger synthetic offset makes omitted offset-normal derivatives
    # detectable; it changes no candidate datum or numerical acceptance gate.
    screw['point_xyz_mm'][2] = .3
    patch(api, screw['point_xyz_mm'])
    rng = np.random.default_rng(829)
    q = model.panel_state(panel, np.eye(3), [.2, -.04, -.25]); q[242:] += .05*np.sin(panel.reference_nodes[:, 0]/1200.)
    state = np.r_[q, center, np.eye(3).ravel()]; direction = rng.normal(size=375); direction[363:] *= .003
    def result(x): return model.interaction(panel, screw, center, x[363:366], x[366:].reshape(3, 3), x[:363], api)[2]
    own = result(state); step = 1e-5; high, low = result(state+step*direction), result(state-step*direction)
    assert abs((high['energy_nmm']-low['energy_nmm'])/(2*step)-own['gradient_n']@direction) < 1e-5
    assert max(abs((high['gradient_n']-low['gradient_n'])/(2*step)-own['hessian_csr']@direction)) < 1e-3
    assert max(abs(model.rigid_work(panel, q, center, np.eye(3), own))) < 1e-5


def test_point_port_difference_transports_both_tangential_and_normal_offsets(fixture):
    api, panel, screw, _ = fixture; target = np.array([100.001, 99.998, .3]); raw = api.adapter.screw_port
    rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]]); translation = np.array([8., -3., 5.])
    q = model.panel_state(panel, rotation, translation)
    result = consumer.datum_port(panel, q, screw['source_screw_descriptor'], target, raw)
    assert max(abs(result['position_xyz_mm']-(rotation@target+translation))) < 1e-10
    assert not any(key.startswith('compact_') for key in result)
    assert len(result['H_xyz_csr']) == 3


def test_gradient_only_datum_port_and_changed_source_pin(fixture):
    api, panel, screw, _ = fixture
    result = consumer.datum_port(panel, np.zeros(363), screw['source_screw_descriptor'], screw['point_xyz_mm'], api.adapter.screw_port, tangent=False)
    assert result['H_xyz_csr'] is None and result['normal_H_xyz_csr'] is None
    with pytest.raises(ValueError): consumer.context({consumer.PRODUCER['path']: '0'*64})
