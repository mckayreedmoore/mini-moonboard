
import pytest

from fea import reinforced_steel_capacity as steel
from fea import reinforced_weld_capacity as weld


def test_a307_uses_rupture_and_reduces_both_long_grip_stresses():
    cap = steel.bolt_capacities()
    assert cap['long_grip_factor'] == pytest.approx(.96)
    assert cap['tension_asd_n'] == pytest.approx(10611.88620179)
    assert cap['single_shear_asd_n'] == pytest.approx(6367.13172108)


def test_axial_sign_and_prying_preserve_shear_interaction():
    cap = steel.bolt_capacities()
    f = (cap['single_shear_asd_n']/2, 0., cap['tension_asd_n']/2)
    result = steel.bolt_check(f, (0., 0., -1.))
    assert result['conservative_linear_interaction_ratio'] == pytest.approx(1.)
    assert steel.bolt_check((0., 0., -100.), (0., 0., -1.))['tension_n'] == 0
    assert steel.bolt_check(f, (0., 0., -1.), 100.)['tension_n'] == pytest.approx(f[2]+100)


def test_wrench_translation_and_cross_product():
    loads = [((10., 0., 20.), (3., 5., 7.))]
    f, m = steel.wrench(loads, (0., 0., 0.))
    assert f == [3., 5., 7.]
    assert m == [-100., -10., 50.]
    assert steel.wrench(loads, (10., 0., 20.))[1] == [0., 0., 0.]


def test_single_fillet_pure_longitudinal_moment_is_not_direct_force_capacity():
    zero = weld.evaluate_weld((0., 0., 0.), (0., 0., 0.), 'right')
    my = zero['pure_longitudinal_moment_diagnostic_nmm']
    assert my == pytest.approx(59538.085, rel=1.e-6)
    for side in ('left', 'right'):
        result = weld.evaluate_weld((0., 0., 0.), (0., my, 0.), side)
        assert result['utilization_diagnostic'] == pytest.approx(1.)
        assert not result['qualification_pass']


def test_plate_tearout_and_net_section_use_actual_hole():
    cap = steel.square_plate_capacities()
    assert cap['clear_distance_mm'] == pytest.approx(10.44375)
    assert cap['net_section_mm2'] == pytest.approx((32-12.7)*6.35)
    assert cap['governing_asd_n'] == pytest.approx(15912.133704766)
    assert cap['one_way_elastic_bending_screen_n'] == pytest.approx(2409.730833866)


def zero_report():
    values = {}
    for name, geometry in steel.connection_geometry().items():
        side = 'left' if '_left_' in name else 'right'
        values[name] = {'first': 'base_header' if '_header_' in name else 'base_side_'+side,
                        'second': 'clip_steel_shoe_'+side,
                        'point': geometry['point'], 'axis': geometry['axis'],
                        'force_on_first_xyz_n': [0., 0., 0.],
                        'force_on_second_xyz_n': [0., 0., 0.]}
    for side, sign in (('left', -1.), ('right', 1.)):
        for i, (x, y) in enumerate( (x, y) for x in (1181.1, 1219.2) for y in (-196., -59.) ):
            values[f'seat_clip_steel_shoe_{side}_{i}'] = {
                'point': [sign*x, y, 234.525], 'force_on_second_xyz_n': [0., 0., 0.]}
    return {'physical_connection_forces': values}


def test_full_zero_wrench_still_keeps_root_rotation_and_prying_conditions():
    result = steel.assess_report(zero_report())
    assert len(result['bolt_checks']) == 16
    assert result['max_bolt_interaction_ratio'] == 0
    assert not result['qualified']
    assert result['response_status'] == 'INVALID_RESPONSE_DIAGNOSTIC_ONLY'
    for shoe in result['shoe_checks']:
        lp = shoe['foot_prying_necessary_check']
        assert lp['solver_success']
        assert lp['minimum_possible_bolt_utilization'] == 0
        assert not lp['qualification_pass']


def test_foot_optimistic_equilibrium_still_rejects_gross_plate_overload():
    values = zero_report()['physical_connection_forces']
    values['seat_clip_steel_shoe_right_3']['force_on_second_xyz_n'] = [0., 0., 1.e8]
    checked = steel.foot_prying_necessary_check(values, 'right')
    assert not checked['necessary_bolt_and_foot_limits_satisfied']


def test_torsion_screen_is_symmetric_under_sign_and_rectangle_axis_swap():
    assert steel.rectangle_torsion_constant(100., 10.) == pytest.approx(steel.rectangle_torsion_constant(10., 100.))
    left = steel.rectangular_section_check((0., 0., 0.), (0., 0., 10000.), 100., 10.)
    right = steel.rectangular_section_check((0., 0., 0.), (0., 0., -10000.), 100., 10.)
    assert left['elastic_von_mises_screen_ratio'] == right['elastic_von_mises_screen_ratio']
    assert left['elastic_von_mises_screen_ratio'] > 0.


def test_missing_force_rejected_instead_of_zero_filled():
    report = zero_report()
    del report['physical_connection_forces']['steel_shoe_rim_right_1']
    with pytest.raises(ValueError, match='Missing shoe bolt'):
        steel.assess_report(report)


def test_wrong_interface_point_rejected():
    report = zero_report()
    report['physical_connection_forces']['steel_shoe_rim_right_1']['point'] = [0., 0., 0.]
    with pytest.raises(ValueError, match='interface'):
        steel.assess_report(report)


def test_contact_convergence_does_not_override_friction_failure():
    report = zero_report()
    report.update(global_equilibrium_passed=True, mpc_check_passed=True,
                  contact_active_set_converged=True,
                  floor_contact_demands=[{'body': 'post', 'normal_n': 100.}])
    report['physical_connection_forces']['floor_post_friction'] = {
        'first': 'post', 'second': 'floor', 'force_on_first_xyz_n': [50., 0., 0.]}
    result = steel.assess_report(report)
    assert result['response_status'] == 'converged_conditional_model'
    assert not result['physical_response_admissible_for_mu_0_4']
    assert result['physical_friction_gate']['contacts'][0]['required_mu'] == .5


def test_output_exclusive_and_empty_demands_rejected(tmp_path):
    output = tmp_path/'result.json'
    steel.main(['--output', str(output)])
    with pytest.raises(FileExistsError):
        steel.main(['--output', str(output)])
    source = tmp_path/'input.json'; source.write_text('{}')
    with pytest.raises(ValueError, match='No physical_connection_forces'):
        steel.main(['--demands', str(source), '--output', str(tmp_path/'bad.json')])
    assert not (tmp_path/'bad.json').exists()
