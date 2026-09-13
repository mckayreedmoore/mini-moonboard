"""Force orientation and scope regressions for current resistance recovery."""
import pytest

from fea.current_response_resistance import (
    angle_comparisons,
    assess,
    bolt_comparison,
    member_comparisons,
)


def member_record(width=38.1, depth=139.7):
    return {'member': {'width_mm': width, 'depth_mm': depth, 'axis': [0., 0., 1.]},
            'length_mm': 1500., 'section_valid_from_mm': 100.,
            'force_residual_n': [0., 0., 0.], 'moment_residual_nmm': [0., 0., 0.],
            'sections': [{'station_along_grain_mm': 700., 'include_station_loads': True,
                          'axial_n_tension_positive': 0., 'moment_u_nmm': 1.e5,
                          'moment_v_nmm': 2.e4, 'shear_u_n': 0., 'shear_v_n': 0.,
                          'torsion_nmm': 0.}]}


def test_actual_full_length_and_swapped_section_axes():
    original = member_record()
    swapped = member_record(139.7, 38.1)
    section = swapped['sections'][0]
    section['moment_u_nmm'], section['moment_v_nmm'] = section['moment_v_nmm'], section['moment_u_nmm']
    results = member_comparisons({'member_section_demands': {'a': original, 'b': swapped}})
    first, second = (results[k]['checks'][0] for k in ('a', 'b'))
    assert results['a']['gross_length_mm'] == 1500.
    assert first['column_slenderness_strong_weak'][1] == pytest.approx(1500/38.1)
    assert first['stress_mpa']['bending_strong'] == pytest.approx(second['stress_mpa']['bending_strong'])
    assert first['stress_mpa']['bending_weak'] == pytest.approx(second['stress_mpa']['bending_weak'])


def test_bolt_uses_current_member_axes_and_retains_axial_increment():
    row = {'first': 'rim', 'second': 'leg', 'axis': [1., 0., 0.],
           'force_on_first_xyz_n': [50., 100., 0.]}
    parallel = {'rim': {'axis': [0., 1., 0.]}, 'leg': {'axis': [0., 1., 0.]}}
    perpendicular = {'rim': {'axis': [0., 0., 1.]}, 'leg': {'axis': [0., 0., 1.]}}
    a, b = bolt_comparison(row, parallel), bolt_comparison(row, perpendicular)
    assert a['lateral_demand_n'] == 100.
    assert a['axial_increment_n'] == 50.
    assert a['reference']['bearing_strengths_main_side_psi'] == [5600., 5600.]
    assert b['reference']['bearing_strengths_main_side_psi'] == [3650., 3650.]
    assert a['lateral_ratio'] < b['lateral_ratio']
    assert a['individual_root_ratio_without_second_group_factor'] < a['lateral_ratio']
    assert a['conditional_nominal_diameter_ratio'] < a['individual_root_ratio_without_second_group_factor']
    assert a['conditional_nominal_diameter_reference_n'] > a['individual_root_reference_n']


def test_angle_retains_transfer_despite_balanced_free_body():
    name = 'clip_angle_base_left'
    station = {'name': name, 'origin': [0., 0., 277.], 'u': [1., 0., 0.], 'v': [0., 0., 1.]}
    forces = {}
    for flange, sign in (('beam', 1.), ('upright', -1.)):
        for index in (1, 2, 3):
            forces[f'{name}_{flange}_{index}'] = {
                'first': flange, 'second': name, 'point': [0., 0., 277.],
                'force_on_first_xyz_n': [0., sign*100., 0.],
                'force_on_second_xyz_n': [0., -sign*100., 0.]}
    check = angle_comparisons(forces, [station])[name]
    assert check['all_six_screw_residual']['force_xyz_n'] == [0., 0., 0.]
    assert abs(check['projected_loaded_flange_force_n']['F1']) == 300.
    assert check['rated_force_component_unity'] > 0.
    assert check['unlisted_separation_demand_n'] == 0.
    assert not check['qualified_for_design']


def test_invalid_response_cannot_be_labeled_valid():
    report = {'candidate': 'no-shoes-development', 'member_section_demands': {},
              'physical_connection_forces': {}}
    assert assess(report)['response_status'] == 'INVALID_RESPONSE_DIAGNOSTIC_ONLY'
    with pytest.raises(ValueError, match='current shoe-free'):
        assess({**report, 'candidate': 'round-reinforcement-development'})


def test_member_equilibrium_and_overall_acceptance_are_mandatory():
    report = {'candidate': 'no-shoes-development', 'member_section_demands': {},
              'physical_connection_forces': {}, 'global_equilibrium_passed': True,
              'mpc_check_passed': True, 'contact_active_set_converged': True,
              'closed_bearing_assumption_passed': True}
    assert assess(report)['response_status'] == 'INVALID_RESPONSE_DIAGNOSTIC_ONLY'
    report['member_equilibrium_passed'] = True
    assert assess(report)['response_status'] == 'INVALID_RESPONSE_DIAGNOSTIC_ONLY'
    report['numerically_accepted'] = True
    assert assess(report)['response_status'] == 'converged_conditional_model'
