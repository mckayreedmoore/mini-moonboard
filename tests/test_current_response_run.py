"""Physical-coordinate force recovery checks for the current response model."""
import numpy as np

from fea.current_response_run import physical_forces


def test_rotated_connector_preserves_force_and_action_reaction():
    root = 2**-.5
    basis = [[root, 0., root], [0., 1., 0.], [-root, 0., root]]
    owner = {'first': 'leg', 'second': 'rim', 'point': [1., 2., 3.],
             'axis': basis[0], 'force_basis': basis}
    record = {'connection_ownership': {'bolt': owner}}
    native = {'connector_forces': {'bolt': {'force_on_first_xyz_n': [10., 20., 30.]}}}
    actual = physical_forces(record, native)['bolt']
    np.testing.assert_allclose(actual['force_on_first_xyz_n'], [-20*root, 20., 40*root])
    np.testing.assert_allclose(np.array(actual['force_on_first_xyz_n'])+
                               actual['force_on_second_xyz_n'], 0.)
    assert np.isclose(actual['axial_along_installation_direction_n'], 10.)
    assert np.isclose(actual['transverse_shear_n'], np.hypot(20., 30.))


def test_floor_scalar_recovery_has_physical_vertical_reaction():
    record = {'connection_ownership': {'floor': {
        'first': 'leg', 'second': 'floor', 'point': [0., 0., 0.],
        'scalar_normal': [0., 0., 1.]}}}
    native = {'connector_forces': {'floor': {'force_on_first_xyz_n': [800., 0., 0.]}}}
    actual = physical_forces(record, native)['floor']
    assert actual['force_on_first_xyz_n'] == [0., 0., 800.]
    assert actual['force_on_second_xyz_n'] == [0., 0., -800.]


def test_native_printing_uncertainty_rotates_and_open_contact_has_zero_force_error():
    record = {'springs': [
        {'name': 'bolt', 'nodes': [1, 2], 'dof': 1, 'stiffness_n_per_mm': 1000., 'active': True},
        {'name': 'floor', 'nodes': [3, 4], 'dof': 1, 'stiffness_n_per_mm': 1.e6, 'active': False}],
        'connection_ownership': {
            'bolt': {'first': 'leg', 'second': 'rim', 'point': [0., 0., 0.],
                     'force_basis': [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]],
                     'axis': [0., 0., 1.]},
            'floor': {'first': 'leg', 'second': 'floor', 'point': [0., 0., 0.],
                      'scalar_normal': [0., 0., 1.]}}}
    native = {'connector_forces': {
        'bolt': {'force_on_first_xyz_n': [500., 0., 0.]},
        'floor': {'force_on_first_xyz_n': [0., 0., 0.]}}}
    precision = {n: [5.e-6]*3 for n in (1, 2, 3, 4)}
    actual = physical_forces(record, native, precision)
    np.testing.assert_allclose(actual['bolt']['force_rounding_radius_xyz_n'], [0., 0., .01])
    assert actual['floor']['force_rounding_radius_xyz_n'] == [0., 0., 0.]


def test_solver_rejects_source_changes_after_import_before_building(tmp_path, monkeypatch):
    import pytest

    from fea import current_response_run

    monkeypatch.setattr(current_response_run, 'source_hashes', lambda: {'changed.py': 'different'})
    with pytest.raises(ValueError, match='Sources changed after this process imported'):
        current_response_run.run(tmp_path/'rejected')
    assert not (tmp_path/'rejected'/'model.pkl').exists()
