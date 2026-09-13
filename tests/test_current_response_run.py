"""Physical-coordinate force recovery checks for the current response model."""
import numpy as np

from fea.current_response_run import physical_forces


def test_inclined_square_brace_keeps_actual_normal_end_stations():
    from types import SimpleNamespace

    import cadquery as cq

    from fea.current_response_model import gross_member_record

    grain, across = cq.Vector(0., .6, .8), cq.Vector(1., 0., 0.)
    origin = cq.Vector(20., 300., 800.)
    plane = cq.Plane(origin=origin, xDir=across, normal=grain)
    shape = cq.Workplane(plane).rect(88.9, 139.7).extrude(900.).val()
    record = gross_member_record(SimpleNamespace(name='knee', shape=shape), grain, across, square_ends=True)
    np.testing.assert_allclose(record['start'], origin.toTuple(), atol=1.e-6)
    np.testing.assert_allclose(record['end'], (origin+grain*900.).toTuple(), atol=1.e-6)


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


def test_mixed_bolts_use_their_own_stiffness_and_reject_invalid_values():
    import pytest

    from fea.current_response_model import named_bolt_properties

    upper = {'axial_n_per_mm': 200., 'lateral_n_per_mm': 100.}
    rail = {'axial_n_per_mm': 90., 'lateral_n_per_mm': 60.}
    properties = {**upper, 'by_name': {'upper': upper, 'rail': rail}}
    assert named_bolt_properties(properties, 'rail', 'post', 'rail', 2.) == rail
    scaled = named_bolt_properties(properties, 'upper', 'lumber_leg_left', 'rim', 2.)
    assert scaled['lateral_n_per_mm'] == 200.
    assert upper['lateral_n_per_mm'] == 100.
    with pytest.raises(ValueError, match='positive finite'):
        named_bolt_properties({'by_name': {'rail': {**rail, 'lateral_n_per_mm': -1.}}},
                              'rail', 'post', 'rail', 1.)


def test_floor_contact_search_changes_one_corner_without_relaxing_other_contacts():
    import pytest

    from fea.current_response_run import next_contact_names

    rows = [{'name': 'floor_post_1', 'active': False, 'opening_mm': -.05},
            {'name': 'floor_post_3', 'active': False, 'opening_mm': -.2},
            {'name': 'floor_other_1', 'active': True, 'opening_mm': .1},
            {'name': 'seating_1', 'active': False, 'opening_mm': -.3}]
    assert next_contact_names(rows) == {'floor_post_1', 'floor_post_3', 'seating_1'}
    assert next_contact_names(rows, 'one_per_floor_body') == {'floor_post_3', 'seating_1'}
    with pytest.raises(ValueError, match='Unknown contact'):
        next_contact_names(rows, 'ignore_contacts')
