"""Analytical force, pressure and clearance witnesses for relieved-foot screens."""
import copy

import numpy as np
import pytest

from fea.leg_mvp_sole_checks import assess


def witness(slope=0.):
    forces, bearings = {}, []
    for index, (x, y) in enumerate((x, y) for x in (5., 15., 25.) for y in (10., 30., 50.)):
        name = f'floor_leg_{index}'
        opening = -.003+slope*(y-30.)
        forces[name] = {'first': 'leg', 'second': 'floor', 'point': [x, y, 0.],
                        'scalar_normal': [0., 0., 1.],
                        'force_on_first_xyz_n': [0., 0., max(0., -opening)*400000./9.]}
        bearings.append({'name': name, 'opening_mm': opening})
    report = {'candidate': 'test', 'numerically_accepted': True,
              'parameters': {'stiffnesses': {'floor': 100000.}},
              'physical_connection_forces': forces, 'bearings': bearings}
    geometry = {'tolerance_mm': 1., 'feet': {'leg': {
        'land_bounds_mm': [0., 30., 0., 60.], 'relief_mm': 5.,
        'relieved_corners_xyz_mm': [[0., -100., 5.], [30., 160., 5.]]}}}
    return report, geometry


def test_uniform_compression_recovers_pressure_and_neck_force():
    report, geometry = witness()
    result = assess(report, geometry)
    foot = result['feet']['leg']
    assert result['conditional_screen_passed']
    assert not result['qualified_for_design']
    np.testing.assert_allclose(foot['land_corner_pressure_mpa'], 1200./1800.)
    np.testing.assert_allclose(foot['floor_resultant_xyz_n'], [0., 0., 1200.])
    np.testing.assert_allclose(foot['neck_top_moment_xyz_nmm'], 0., atol=1.e-9)
    np.testing.assert_allclose(foot['relieved_corner_remaining_gaps_mm'], 3.997)


def test_extrapolation_catches_relief_collision_beyond_sampled_land():
    report, geometry = witness(slope=.04)
    result = assess(report, geometry)['feet']['leg']
    assert result['opening_fit_passed']
    assert min(result['relieved_corner_remaining_gaps_mm']) < 0
    assert not result['relief_clearance_with_cut_tolerance_passed']


def test_nonplanar_sample_openings_block_clearance_acceptance():
    report, geometry = witness()
    report['bearings'][4]['opening_mm'] += .001
    result = assess(report, geometry)['feet']['leg']
    assert not result['opening_fit_passed']
    assert not result['scalar_screen_passed']


def test_horizontal_force_moment_uses_actual_five_mm_neck_height():
    report, geometry = witness()
    report['physical_connection_forces']['friction'] = {
        'first': 'leg', 'second': 'floor', 'point': [15., 30., 0.],
        'force_on_first_xyz_n': [100., 0., 0.]}
    result = assess(report, geometry)['feet']['leg']
    np.testing.assert_allclose(result['neck_top_moment_xyz_nmm'], [0., -500., 0.], atol=1.e-9)
    assert result['neck_shear_mpa'] == pytest.approx(1.5*100/1800)
    bad = copy.deepcopy(report)
    bad['numerically_accepted'] = False
    assert not assess(bad, geometry)['conditional_screen_passed']
