"""Printing uncertainty must reduce a claimed necessary failure, never increase it."""
import pytest

from fea.reinforced_timber_roundoff import assess


def fixture():
    native = {'member_section_demands': {'beam': {
        'member': {'width_mm': 38.1, 'depth_mm': 139.7},
        'sections': [{'station_along_grain_mm': 1., 'include_station_loads': False,
                      'axial_n_tension_positive': 0., 'moment_u_nmm': 2.e6,
                      'moment_v_nmm': 0.}]}}, 'physical_connection_forces': {}}
    uncertainty = {'member_print_roundoff': {'beam': {'sections': [{
        'station_along_grain_mm': 1., 'include_station_loads': False,
        'axial_n_radius': 0., 'moment_u_nmm_radius': 0., 'moment_v_nmm_radius': 0.}]}},
        'physical_connection_force_radius_xyz_n': {}}
    return native, uncertainty


def test_rounding_interval_can_remove_an_apparent_failure():
    native, uncertainty = fixture()
    assert assess(native, uncertainty)['members']['beam']['failure_even_fully_braced_and_after_roundoff']
    uncertainty['member_print_roundoff']['beam']['sections'][0]['moment_u_nmm_radius'] = 2.e6
    result = assess(native, uncertainty)['members']['beam']
    assert result['maximum_necessary_interaction_lower_bound'] == 0.
    assert not result['failure_even_fully_braced_and_after_roundoff']


def test_reject_uncertainty_for_another_cut():
    native, uncertainty = fixture()
    uncertainty['member_print_roundoff']['beam']['sections'][0]['station_along_grain_mm'] = 2.
    with pytest.raises(ValueError, match='ordering mismatch'):
        assess(native, uncertainty)
