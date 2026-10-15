"""Saved finite load potentials and full geometric work; Python sources only."""
import copy
from pathlib import Path

import numpy as np
import pytest
import test_eoere_panel_bulk_coupling as reference

from scripts import eoere_finite_panel_loads as model

GATES = {'mass_sum': 1e-12, 'mass_mean_mm': 1e-7, 'reference_rhs_n': 1e-5,
         'energy_nmm': 1e-5, 'force_n': 1e-7, 'moment_nmm': 1e-5}


def source_api():
    pins = {}; consumer = model.bootstrap(pins); producer, base = consumer.context(pins)
    return model.load_api(reference.SOURCES, producer, consumer, base, pins), producer


def fixture(api):
    panel, _, _ = reference.fixture(api)
    saved = {'global_dof_indices': list(range(363)), 'axes_columns_xyz': panel.axes.tolist(),
        'origin_xyz_mm': panel.origin.tolist(), 'basis_width_mm': panel.basis.width, 'basis_height_mm': panel.basis.height,
        'basis_order': 11, 'basis_knots_normalized': panel.basis.knots.tolist(),
        'mass_coefficient_row': np.full(121, 1/121).tolist(), 'mass_reference_xy_mm': [600., 500.]}
    loads = [{'id': 'self-weight/panel', 'body': 'panel', 'force_xyz_n': [0., 0., -20.], 'point_xyz_mm': [600., 500., 0.]},
             {'id': 'climber/point', 'body': 'panel', 'force_xyz_n': [4., -5., -6.], 'point_xyz_mm': [100., 200., 10.]},
             {'id': 'accessory/gap', 'body': 'panel', 'force_xyz_n': [0., 0., -7.], 'point_xyz_mm': [-.4, 400., 30.]}]
    corrections = []
    for i, kind in enumerate(('retained_rigid_RHS', 'reference_port_alignment')):
        force = np.zeros(363); force[i] = i+1.; force[-1-i] = -.5
        corrections.append({'panel': 'panel', 'kind': kind, 'case_id': 'case', 'state_id': 'state',
            'global_coefficient_indices': list(range(363)), 'physical_point_forces_or_pressure_representation': False,
            'local_generalized_force_n': force.tolist()})
    return panel, saved, loads, corrections


def restored(api):
    panel, saved, loads, corrections = fixture(api)
    return model.restore_load(panel, saved, loads, corrections, 'case', 'state', api, GATES)[0]


def test_translation_and_finite_rotation_have_known_physical_potential_work():
    api, producer = source_api(); load = restored(api)
    zero, controls = model.controls(load, producer, GATES)
    assert controls['translation_potential_error_nmm'] < 1e-9
    assert controls['common_rotation_physical_potential_error_nmm'] < 1e-8
    assert zero['reference_port_alignment_potential_nmm'] == zero['retained_rigid_correction_potential_nmm'] == 0.
    assert len(load.point_loads) == 2 and 'mass_weights' not in load.adapter.measure


def test_both_correction_potentials_and_current_wrenches_stay_separate():
    api, _ = source_api(); load = restored(api)
    q = np.linspace(-.1, .2, 363)
    result = load.external(q, tangent=False, reference=np.array([0., 750., 1100.]))
    assert result['retained_rigid_correction_potential_nmm'] == -load.retained_rigid_correction_n@q
    assert result['reference_port_alignment_potential_nmm'] == -load.reference_port_alignment_correction_n@q
    assert result['correction_potential_nmm'] == -load.correction_n@q
    assert abs(result['energy_nmm']-result['physical_load_potential_nmm']-result['correction_potential_nmm']) < 1e-12
    assert max(abs(result['generalized_correction_wrench_n_nmm']-result['retained_rigid_correction_wrench_n_nmm']
                   -result['reference_port_alignment_wrench_n_nmm'])) < 1e-9
    assert max(abs(result['wrench_residual_n_nmm'])) < 1e-8


def test_finite_point_load_gradient_and_complete_geometric_hessian():
    api, _ = source_api(); load = restored(api); panel = load.adapter
    x, y = panel.reference_nodes[:, 0]/1200., panel.reference_nodes[:, 1]/1000.
    q = np.r_[.2*x*y, -.1*x*x, .5*x*y+.2*x*x]
    direction = np.random.default_rng(981).normal(size=363); step = 1e-5
    own = load.external(q, tangent=True); high, low = [load.external(q+sign*step*direction, tangent=False) for sign in (1, -1)]
    assert abs((high['energy_nmm']-low['energy_nmm'])/(2*step)-own['local_gradient_n']@direction) < 1e-6
    assert max(abs((high['local_gradient_n']-low['local_gradient_n'])/(2*step)-own['local_hessian_csr']@direction)) < 1e-5
    assert np.max(abs((own['local_hessian_csr']-own['local_hessian_csr'].T).data), initial=0.) < 1e-10
    assert own['gradient_n'].shape == (375,) and not any(own['gradient_n'][363:])
    assert own['hessian_csr'].shape == (375, 375) and own['hessian_csr'][363:, :].nnz == 0


def test_generalized_corrections_change_work_even_when_physical_loads_are_unchanged():
    api, _ = source_api(); load = restored(api); q = np.ones(363)*.1
    full = load.external(q, tangent=True)
    load.correction_n = load.retained_rigid_correction_n.copy()
    missing = load.external(q, tangent=True)
    assert abs(full['energy_nmm']-missing['energy_nmm']) > .1
    assert max(abs(full['gradient_n']-missing['gradient_n'])) == 2.
    assert (full['hessian_csr']-missing['hessian_csr']).nnz == 0


@pytest.mark.parametrize('change', ['case', 'state', 'index', 'physical_claim', 'duplicate', 'missing', 'vector_shape'])
def test_missing_cross_owned_or_reinterpreted_corrections_are_refused(change):
    api, _ = source_api(); panel, saved, loads, corrections = fixture(api)
    if change == 'case': corrections[0]['case_id'] = 'other'
    if change == 'state': corrections[0]['state_id'] = 'other'
    if change == 'index': corrections[0]['global_coefficient_indices'][0] = 4
    if change == 'physical_claim': corrections[0]['physical_point_forces_or_pressure_representation'] = True
    if change == 'duplicate': corrections[1] = copy.deepcopy(corrections[0])
    if change == 'missing': corrections.pop()
    if change == 'vector_shape': corrections[0]['local_generalized_force_n'].pop()
    with pytest.raises(ValueError): model.restore_load(panel, saved, loads, corrections, 'case', 'state', api, GATES)


@pytest.mark.parametrize('change', ['axes', 'mass_sum', 'mass_mean', 'knots', 'dimension', 'nonfinite'])
def test_changed_saved_mass_measure_or_panel_chart_is_refused(change):
    api, _ = source_api(); panel, saved, loads, corrections = fixture(api)
    if change == 'axes': saved['axes_columns_xyz'][0][0] = -1.
    if change == 'mass_sum': saved['mass_coefficient_row'][0] += .1
    if change == 'mass_mean': saved['mass_reference_xy_mm'][0] += 1.
    if change == 'knots': saved['basis_knots_normalized'][4] += .01
    if change == 'dimension': saved['basis_width_mm'] += 1.
    if change == 'nonfinite': saved['mass_coefficient_row'][0] = float('nan')
    with pytest.raises(ValueError): model.restore_load(panel, saved, loads, corrections, 'case', 'state', api, GATES)


@pytest.mark.parametrize('change', ['duplicate_id', 'point_couple', 'no_selfweight', 'other_selfweight'])
def test_original_unique_physical_inventory_and_selfweight_are_required(change):
    api, _ = source_api(); panel, saved, loads, corrections = fixture(api)
    if change == 'duplicate_id': loads.append(copy.deepcopy(loads[1]))
    if change == 'point_couple': loads[1]['moment_xyz_nmm'] = [0, 0, 1]
    if change == 'no_selfweight': loads.pop(0)
    if change == 'other_selfweight': loads.append({**loads[0], 'id': 'self-weight/other'})
    with pytest.raises(ValueError): model.restore_load(panel, saved, loads, corrections, 'case', 'state', api, GATES)


def test_pure_controls_read_only_python_sources_and_need_no_factorization(monkeypatch):
    read_bytes = Path.read_bytes
    def python_sources_only(path):
        assert path.suffix == '.py', 'pure controls must not read production inputs or assets'
        return read_bytes(path)
    def prohibited(*args, **kwargs): raise AssertionError('inverse/factorization/quadrature eigensystem forbidden')
    monkeypatch.setattr(Path, 'read_bytes', python_sources_only)
    for name in ('solve', 'inv', 'pinv', 'lstsq', 'cholesky', 'qr', 'svd', 'eig', 'eigh', 'eigvals', 'eigvalsh', 'det', 'slogdet'):
        monkeypatch.setattr(np.linalg, name, prohibited)
    monkeypatch.setattr(np.polynomial.legendre, 'leggauss', prohibited)
    api, producer = source_api(); load = restored(api)
    _, observed = model.controls(load, producer, GATES)
    assert observed['all_evaluated_poses_are_synthetic_method_controls'] is True


def test_bootstrap_conflict_is_refused():
    with pytest.raises(ValueError): model.bootstrap({model.BOOT['path']: '0'*64})
