"""Independent closed-form and failing-demand checks for current timber equations."""
import pytest

from fea.reinforced_timber_resistance import (
    bearing_check,
    cross_grain_group_check,
    member_check,
    stability_factor,
)


def action(**overrides):
    values = {'width_mm': 38.1, 'depth_mm': 139.7, 'axial_n': 0.,
              'moment_strong_nmm': 0., 'moment_weak_nmm': 0., 'shear_strong_n': 0.,
              'shear_weak_n': 0., 'torsion_nmm': 0., 'column_effective_strong_mm': 1000.,
              'column_effective_weak_mm': 1000., 'beam_effective_mm': 1840.}
    return member_check(**(values|overrides))


def test_stability_root_satisfies_nds_quadratic():
    for ratio in (.01, 1., 100.):
        for c in (.8, .95):
            x = stability_factor(ratio, c)
            assert c*x*x-(1+ratio)*x+ratio == pytest.approx(0., abs=1.e-12)
            assert 0 < x <= 1


def test_compression_shear_and_instability_failures_are_not_hidden():
    assert action(axial_n=-100000)['conditional_checked_failure']
    assert action(shear_strong_n=10000)['conditional_checked_failure']
    assert action(axial_n=-1, column_effective_weak_mm=2000)['conditional_checked_failure']
    assert not action()['conditional_checked_failure']
    assert not action()['qualified_for_design']


def test_center_hole_removes_transverse_rectangle_not_circle():
    result = action(centered_hole_diameter_mm=38.1)
    assert result['net_area_mm2'] == pytest.approx(3870.96)
    assert result['section_moduli_strong_weak_mm3'][0] == pytest.approx(121413.24690909)
    assert not result['local_opening_resistance_evaluated']


def test_bearing_end_angles_and_actual_shoe_row_failure():
    parallel = bearing_check(100, 100, 0, 139.7)
    transverse = bearing_check(100, 100, 90, 139.7)
    assert parallel['adjusted_bearing_mpa'] > transverse['adjusted_bearing_mpa']
    assert not cross_grain_group_check(130)['passed']
    assert cross_grain_group_check(127)['passed']


def test_boring_rule_keeps_both_ligaments_under_center_error():
    from fea.reinforced_timber_resistance import boring_limit
    diameter = boring_limit(139.7, .5)
    assert diameter == pytest.approx(37.1)
    assert (139.7-diameter)/2-.5 == pytest.approx(50.8)


def test_group_factor_single_bolt_and_two_equal_ea_rows():
    from fea.reinforced_timber_resistance import group_factor
    assert group_factor(1, 2., 1.e6, 1.e6) == 1.
    # NDS expression simplifies to Cg=1 for two equal-EA fasteners.
    assert group_factor(2, 2., 1.e6, 1.e6) == pytest.approx(1.)
    assert 0 < group_factor(4, 2., 1.e6, 1.e6) < 1.


def test_header_section_axes_swap_and_no_invented_washer_area():
    from fea.reinforced_timber_resistance import connection_report, section_report
    raw = {'member': {'width_mm': 234.95, 'depth_mm': 38.1}, 'length_mm': 100.,
           'section_valid_from_mm': 0., 'force_residual_n': [0., 0., 0.],
           'moment_residual_nmm': [0., 0., 0.], 'sections': [{
               'station_along_grain_mm': 50., 'include_station_loads': False,
               'axial_n_tension_positive': 0., 'moment_u_nmm': 1000., 'moment_v_nmm': 0.,
               'shear_u_n': 0., 'shear_v_n': 0., 'torsion_nmm': 0.}]}
    check = section_report({'member_section_demands': {'header': raw}})['header']['checks'][0]
    assert check['stress_mpa']['bending_strong'] == 0.
    assert check['stress_mpa']['bending_weak'] > 0.
    force = {'force_on_first_xyz_n': [100., 100., 100.],
             'axial_along_installation_direction_n': 100., 'transverse_shear_n': 141.421}
    result = connection_report({'physical_connection_forces': {'lumber_leg_bolt_left_1': force}})
    area = result['lumber_leg_bolt_left_1']['wood_bearing']['net_area_mm2']
    assert 230 < area < 232  # Minimum20.447mm OD minus actual11.1125mm timber hole.
