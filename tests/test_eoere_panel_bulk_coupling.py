"""Independent work/objectivity controls for the finite numerical interface."""
import copy
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts import eoere_panel_bulk_coupling as model

SOURCES = {name: {'path': path, 'sha256': digest} for name, path, digest in (
    ('definition_loader', 'scripts/eoere_cleat_traction_witness.py', '941cdd505e60e0e4275aa3b71fb5434d80d26a2f1c8d8f0ec96a6d87f5ae8dce'),
    ('panel_basis', 'scripts/thin_bolted_panel_mechanics.py', '472eef63a8af59367533028008c68e4f7e32780e49891499154ba2950559a3aa'),
    ('finite_plate', 'scripts/thin_bolted_finite_plate.py', '2b0de347d0ef35d08ab7a8d4078fa2e26a50cee6e7c2f708560dd1f0979b9180'),
    ('panel_adapter', 'scripts/thin_bolted_finite_panel_adapter.py', 'c0e2534158d10ca49e6e1ee20db7b8a7e72b746b49618a18bf5ab08a9526064b'),
    ('current_finite_frame', 'scripts/eoere_current_finite_frame.py', 'b42e91768c211c661918239f1223accbee574e8a18e299d1fda43f89c88b3788'),
    ('connectors', 'scripts/thin_bolted_finite_connectors.py', '6bf2c5ca9006e474d8b10642e8e4dbbfc657070c0d221b98abfbc1d2d6e03060'))}


def source_api():
    pins = {}; remaining = model.bootstrap(pins); gravity = remaining.bootstrap(pins); contact = gravity.bootstrap(pins)
    material = contact.bootstrap(pins); prior = material.bootstrap(pins); boot = prior.bootstrap(pins)
    return model.methods(SOURCES, boot.producer(pins), pins)


@pytest.fixture(scope='module')
def api():
    return source_api()


def fixture(api):
    descriptor = {'intervals': 8, 'basis_order_per_direction': 11, 'indices': list(range(363)),
        'width_mm': 1200., 'height_mm': 1000., 'thickness_mm': 18.25625,
        'knots_normalized': [0.]*4+[i/8 for i in range(1, 8)]+[1.]*4,
        'geometry': {'name': 'panel', 'origin': [0., 0., 0.], 'axes': np.eye(3).tolist()}}
    panel, _ = model.panel_adapter(descriptor, api)
    screw = {'id': 'axis', 'first': 'panel', 'second': 'wood', 'ka': 1000., 'kl': 1000., 'clearance': 0.,
        'tension_only': True, 'physical_Hillman_stiffness_or_capacity_qualified': False,
        'point_xyz_mm': [100., 100., 0.], 'basis': np.eye(3)[[2, 0, 1]].tolist(),
        'source_screw_descriptor': {'axis_id': 'axis', 'panel': 'panel', 'receiver': 'wood', 'origin_xyz_mm': [100., 100., 9.128125]}}
    return panel, screw, np.array([100., 100., -31.])


def test_radical_quadrature_matches_legendre_moments_without_factorization():
    nodes, weights = model.closed_gauss4(4)
    for power in range(8):
        assert abs(weights@nodes**power-(2/(power+1) if power % 2 == 0 else 0.)) < 1e-15


@pytest.mark.parametrize('order', [True, 3, 5, 4.])
def test_other_quadrature_orders_are_not_silently_admitted(order):
    with pytest.raises(ValueError): model.closed_gauss4(order)


def test_bulk_port_is_affine_exact_and_objective_for_arbitrary_mean_gradient():
    center = np.array([2., -3., 5.]); target = np.array([-4., 8., 9.])
    gradient = np.array([[1.1, .2, -.1], [.3, .9, .4], [0., -.2, 1.2]]); shift = np.array([7., 1., -2.])
    port = model.bulk_port(gradient@center+shift, gradient, center, target)
    assert np.max(abs(port['position_xyz_mm']-(gradient@target+shift))) < 1e-14
    rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    translation = np.array([1., 3., 2.])
    mean = np.array([4., 2., 1.])
    old = model.bulk_port(mean, gradient, center, target)
    new = model.bulk_port(rotation@mean+translation, rotation@gradient, center, target)
    assert np.max(abs(new['position_xyz_mm']-(rotation@old['position_xyz_mm']+translation))) < 1e-14


def test_bulk_first_derivative_includes_every_mean_gradient_coordinate():
    rng = np.random.default_rng(751); x = rng.normal(size=12); d = rng.normal(size=12)
    center, target = [1., 2., -3.], [3., -1., 9.]
    step = 1e-5
    def port(value): return model.bulk_port(value[:3], value[3:].reshape(3, 3), center, target)
    exact = port(x)['J_csr'][:, 363:]@d
    assert np.max(abs((port(x+step*d)['position_xyz_mm']-port(x-step*d)['position_xyz_mm'])/(2*step)-exact)) < 1e-9
    assert all(a.nnz == 0 for a in port(x)['H_xyz_csr'])


@pytest.mark.parametrize('bad', ['mean_shape', 'gradient_shape', 'nan'])
def test_invalid_bulk_coordinates_are_refused(bad):
    mean, gradient = np.zeros(3), np.eye(3)
    if bad == 'mean_shape': mean = np.zeros(2)
    if bad == 'gradient_shape': gradient = np.zeros((2, 3))
    if bad == 'nan': gradient[0, 0] = np.nan
    with pytest.raises(ValueError): model.bulk_port(mean, gradient, [0, 0, 0], [1, 2, 3])


@pytest.mark.parametrize('radius', [F(1, 2), F(1), F(2)])
def test_exact_distributed_pullback_recovers_force_moment_and_polynomial_work(radius):
    center = [F(2), F(-3), F(4)]; target = [F(7), F(1), F(9)]; volume = 8*radius**3
    law = model.bulk_definition(center, target, {'half_width_mm': str(radius), 'volume_mm3': str(volume), 'cube_center_xyz_mm': center})
    force = [F(3), F(-5), F(7)]; offset = [p-c for p, c in zip(target, center, strict=True)]
    assert F(law['H1_bound_L2_coefficient_per_mm3']) == 1/volume
    assert F(law['H1_bound_gradient_coefficient_per_mm']) == sum(d*d for d in offset)/volume
    area = 4*radius**2
    face_forces = [[force[j]*F(law['face_traction_scalar_per_mm3'][i][side])*area for j in range(3)]
                   for i in range(3) for side in range(2)]
    points = [[c+(sign*radius if j == i else 0) for j, c in enumerate(center)] for i in range(3) for sign in (-1, 1)]
    assert [sum(row[j] for row in face_forces) for j in range(3)] == [0]*3
    cross = lambda a, b: [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    moments = [cross(p, f) for p, f in zip(points, face_forces, strict=True)]
    body_moment = cross(center, force)
    assert [body_moment[j]+sum(row[j] for row in moments) for j in range(3)] == cross(target, force)
    # v=(X_0^2,0,0): exact cube body mean plus the two X-face works.
    body_work = force[0]*(center[0]**2+radius**2/3)
    face_work = sum(f[0]*p[0]**2 for p, f in zip(points, face_forces, strict=True))
    expected = force[0]*(center[0]**2+radius**2/3+2*center[0]*offset[0])
    assert body_work+face_work == expected
    assert body_work+face_work != force[0]*target[0]**2


def test_spread_sensitivity_is_retained_for_nonaffine_placements():
    # mean(X_0^2)=C_0^2+r^2/3; extrapolating the mean gradient does
    # not silently restore literal point evaluation for nonaffine fields.
    values = []
    for radius in (.5, 1., 2.):
        mean = [4+radius**2/3, 0, 0]; gradient = np.array([[4., 0, 0], [0, 0, 0], [0, 0, 0]])
        values.append(model.bulk_port(mean, gradient, [2, 0, 0], [7, 0, 0])['position_xyz_mm'][0])
    assert abs(values[1]-values[0]-.25) < 1e-14 and abs(values[2]-values[1]-1) < 1e-14


def test_known_slip_and_common_rigid_motion_controls(api):
    panel, screw, center = fixture(api)
    gates = {'position_mm': 1e-8, 'energy_nmm': 1e-6, 'force_n': 1e-6, 'moment_nmm': 1e-5}
    _, result = model.controls(panel, screw, center, api, gates)
    assert [r['known_energy_nmm'] for r in result['slip_controls']] == [65., 20.000000000000004]
    assert result['common_rigid_position_error_mm'] < 1e-8


def test_full_panel_bulk_energy_gradient_and_tangent_include_normal_work(api):
    panel, screw, center = fixture(api); rng = np.random.default_rng(395)
    q = model.panel_state(panel, np.eye(3), [.2, -.07, -.3])
    q[242:] += .05*(panel.reference_nodes[:, 0]/1200.)**2
    state = np.r_[q, center, np.eye(3).ravel()]
    direction = rng.normal(size=375); direction[363:] *= .005
    def response(x): return model.interaction(panel, screw, center, x[363:366], x[366:].reshape(3, 3), x[:363], api)[2]
    result = response(state); step = 1e-5
    high, low = response(state+step*direction), response(state-step*direction)
    derivative = (high['energy_nmm']-low['energy_nmm'])/(2*step)
    assert abs(derivative-result['gradient_n']@direction) < 1e-5
    assert np.max(abs((high['gradient_n']-low['gradient_n'])/(2*step)-result['hessian_csr']@direction)) < 1e-3
    assert np.max(abs((result['hessian_csr']-result['hessian_csr'].T).data), initial=0.) < 1e-8
    work = model.rigid_work(panel, q, center, np.eye(3), result)
    assert max(abs(work[:3])) < 1e-8 and max(abs(work[3:])) < 1e-6


def test_omitted_director_work_is_detected_by_owner_moment_control(api):
    panel, screw, center = fixture(api); q = model.panel_state(panel, np.eye(3), [.2, 0, -.3])
    first, second, good = model.interaction(panel, screw, center, center, np.eye(3), q, api)
    frozen = api.connectors.normal_field(first)
    frozen.update(J_csr=csr_matrix((3, 375)), H_xyz_csr=[csr_matrix((375, 375)) for _ in range(3)])
    bad = api.connectors.connector_response(api.connectors.position_field(first), api.connectors.position_field(second), frozen,
        axial_stiffness_n_mm=1000., lateral_stiffness_n_mm=1000.)
    assert max(abs(model.rigid_work(panel, q, center, np.eye(3), good))) < 1e-6
    assert max(abs(model.rigid_work(panel, q, center, np.eye(3), bad))) > 59.


@pytest.mark.parametrize('change', ['stiffness', 'clearance', 'bilateral', 'product_claim', 'wrong_axis'])
def test_altered_source_law_and_axis_are_refused(api, change):
    panel, screw, center = fixture(api); screw = copy.deepcopy(screw)
    if change == 'stiffness': screw['ka'] = 2000.
    if change == 'clearance': screw['clearance'] = .2
    if change == 'bilateral': screw['tension_only'] = False
    if change == 'product_claim': screw['physical_Hillman_stiffness_or_capacity_qualified'] = True
    if change == 'wrong_axis': screw['point_xyz_mm'][0] += 1.
    with pytest.raises(ValueError): model.interaction(panel, screw, center, center, np.eye(3), np.zeros(363), api)


def test_port_preparation_and_controls_need_no_matrix_factorization(api, monkeypatch):
    def prohibited(*args, **kwargs): raise AssertionError('prohibited inverse/factorization/quadrature eigensystem')
    for name in ('solve', 'inv', 'pinv', 'lstsq', 'cholesky', 'qr', 'svd', 'eig', 'eigh', 'eigvals', 'eigvalsh', 'det', 'slogdet'):
        monkeypatch.setattr(np.linalg, name, prohibited)
    monkeypatch.setattr(np.polynomial.legendre, 'leggauss', prohibited)
    panel, screw, center = fixture(api)
    _, result = model.controls(panel, screw, center, api,
        {'position_mm': 1e-8, 'energy_nmm': 1e-6, 'force_n': 1e-6, 'moment_nmm': 1e-5})
    assert len(result['slip_controls']) == 2


def test_class_capture_rejects_missing_or_duplicate_definitions():
    for source in ('class A:\n def x(self): pass\n', 'class A:\n def x(self): pass\n def x(self): pass\n'):
        base = SimpleNamespace(captured=lambda ref, pins, data=source: data.encode())
        with pytest.raises(ValueError): model.class_subset({'path': 'fixture.py'}, 'A', ('x', 'y'), {}, base, {})


def test_changed_bootstrap_pin_is_refused():
    with pytest.raises(ValueError): model.bootstrap({model.BOOT['path']: '0'*64})


def test_known_answer_controls_run_without_ignored_production_inputs(monkeypatch):
    original = Path.read_bytes
    def source_only(path):
        assert path.suffix == '.py', 'known-answer controls must not read a production JSON or candidate asset'
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', source_only)
    panel, screw, center = fixture(source_api())
    port = panel.screw_port(np.zeros(363), screw['source_screw_descriptor'])
    assert np.max(abs(port['position_xyz_mm']-[100, 100, 0])) < 1e-12
    assert center[2] == -31
