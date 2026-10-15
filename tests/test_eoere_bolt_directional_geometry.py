"""Load reversal, end categories, complete connection minima and claim guards."""
import copy

import numpy as np
import pytest

from scripts import eoere_bolt_directional_geometry as directions
from scripts.thin_bolted_timber_resistance import end_geometry_factor


def inputs():
    return directions.current.read(directions.current.ref(directions.INPUT))


def fixture(grain=10., edge=3.):
    row = {'axis_id': 'ownbolt', 'host': 'ownwood', 'nominal_diameter_mm': 10.,
           'bearing_interval_mm': [0., 20.], 'bore_transverse_dimension': 1, 'edge_transverse_dimension': 2,
           'grain_end_distances': [
               {'end_sign': -1, 'outward_normal_luv': [-1., 0., 0.], 'minimum_axis_to_end_along_grain_mm': 160.},
               {'end_sign': 1, 'outward_normal_luv': [1., 0., 0.], 'minimum_axis_to_end_along_grain_mm': 40.}],
           'outer_edge_distances': [
               {'edge_sign': -1, 'minimum_axis_to_outer_edge_mm': 30.},
               {'edge_sign': 1, 'minimum_axis_to_outer_edge_mm': 70.}]}
    profile = {'member': 'ownwood', 'basis_grain_u_v_xyz': np.eye(3).tolist()}
    shaft = {'axis_id': 'ownbolt', 'diameter_mm': 10., 'point': [100., 0., 40.], 'basis': [[0., 1., 0.]]}
    action = {'axis_id': 'ownbolt', 'host': 'ownwood', 'surface_index': 0, 'surface_interval_mm': [0., 20.],
              'force_on_host_xyz_n': [grain, 37., edge], 'moment_on_host_at_point_xyz_nmm': [11., 22., 33.],
              'point_xyz_mm': [100., 10., 40.], 'grain_axis_xyz': [1., 0., 0.]}
    return row, profile, shaft, action


def evaluate(*args):
    return directions.directional(*args, end_geometry_factor, inputs())


def test_actual_loaded_side_passes_even_when_the_shorter_unloaded_edge_is_below_4D():
    result = evaluate(*fixture())
    screen = result['edge_component_screen']
    assert screen['loaded_edge_sign'] == 1
    assert screen['loaded_edge_distance_mm'] == 70. and screen['unloaded_edge_distance_mm'] == 30.
    assert screen['loaded_requirement_mm'] == 40. and screen['unloaded_requirement_mm'] == 15.
    assert screen['loaded_marker_pass'] and screen['unloaded_marker_pass']
    assert result['own_force_on_host_xyz_n'] == [10., 37., 3.]
    assert result['own_free_couple_on_host_about_action_point_xyz_nmm'] == [11., 22., 33.]
    assert result['declared_bore_direction_force_component_n'] == 37.
    assert result['complete_Cdelta'] is None and result['complete_joint_resistance'] is None


def test_load_reversal_selects_the_short_edge_and_records_a_component_miss_without_failure_claim():
    result = evaluate(*fixture(edge=-3.))
    screen = result['edge_component_screen']
    assert screen['loaded_edge_sign'] == -1
    assert not screen['loaded_marker_pass'] and screen['unloaded_marker_pass']
    assert screen['loaded_requirement_over_distance'] == pytest.approx(4/3)
    assert result['physical_or_complete_code_failure_established'] is False


def test_parallel_reversal_changes_near_end_tension_to_compression_with_other_end_retained():
    forward = evaluate(*fixture())
    reverse = evaluate(*fixture(grain=-10.))
    assert forward['minimum_signed_force_end_trial'] == pytest.approx(40/70)
    assert reverse['minimum_signed_force_end_trial'] == 1.
    assert {r['category'] for r in forward['end_component_trials'] if r['end_sign'] == 1} == {
        'softwood_parallel_tension', 'perpendicular'}
    assert {r['category'] for r in reverse['end_component_trials'] if r['end_sign'] == 1} == {
        'parallel_compression', 'perpendicular'}


@pytest.mark.parametrize('edge', [0., 1e-6, -1e-6, 1e-5, -1e-5])
def test_unresolved_cross_component_keeps_raw_force_and_null_direction_instead_of_passing(edge):
    result = evaluate(*fixture(edge=edge))
    assert result['edge_component_screen'] is None
    assert result['perpendicular_component_direction_resolved'] is False
    assert result['declared_cross_edge_force_component_n'] == edge


def test_unresolved_parallel_sign_retains_reversible_tension_requirement_at_both_ends():
    result = evaluate(*fixture(grain=1e-6))
    assert result['declared_grain_force_component_n'] == 1e-6
    assert result['minimum_signed_force_end_trial'] == pytest.approx(40/70)
    assert all(not r['parallel_sign_resolved'] for r in result['end_component_trials'])


def test_sloping_partial_end_is_a_trial_without_a_square_factor_or_complete_adoption():
    args = copy.deepcopy(fixture())
    args[0]['grain_end_distances'][1]['outward_normal_luv'] = [.8, 0., .6]
    result = evaluate(*args)
    partial = next(r for r in result['end_component_trials'] if r['category'] == 'softwood_parallel_tension')
    assert not partial['source_end_plane_square']
    assert partial['reference_trial']['end_factor_only'] == pytest.approx(40/70)
    assert partial['square_end_component_factor_if_plane_applies'] is None
    assert result['any_partial_sloping_end_trial'] is True
    assert partial['factor_is_complete_Cdelta'] is False


def test_below_minimum_end_is_retained_as_null_not_clamped_to_half():
    args = copy.deepcopy(fixture())
    args[0]['grain_end_distances'][1]['minimum_axis_to_end_along_grain_mm'] = 30.
    result = evaluate(*args)
    assert result['minimum_signed_force_end_trial'] is None
    assert any(r['reference_trial']['status'] == 'below_minimum' for r in result['end_component_trials'])


@pytest.mark.parametrize('distance,passes', [(40., True), (40.-.5e-6, True), (40.-2e-6, False)])
def test_loaded_marker_uses_the_recorded_distance_gate_without_hiding_a_shortfall(distance, passes):
    args = copy.deepcopy(fixture())
    args[0]['outer_edge_distances'][1]['minimum_axis_to_outer_edge_mm'] = distance
    result = evaluate(*args)
    assert result['edge_component_screen']['loaded_marker_pass'] is passes


def test_force_and_couple_projections_are_invariant_under_rigid_world_rotation_translation():
    args = copy.deepcopy(fixture())
    rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    shift = np.array([1000., -2000., 300.])
    args[1]['basis_grain_u_v_xyz'] = rotation.T.tolist()
    args[2]['point'] = (rotation@args[2]['point']+shift).tolist()
    args[2]['basis'][0] = (rotation@args[2]['basis'][0]).tolist()
    args[3]['point_xyz_mm'] = (rotation@args[3]['point_xyz_mm']+shift).tolist()
    for key in ('force_on_host_xyz_n', 'moment_on_host_at_point_xyz_nmm', 'grain_axis_xyz'):
        args[3][key] = (rotation@args[3][key]).tolist()
    result = evaluate(*args)
    assert result['declared_grain_force_component_n'] == 10.
    assert result['declared_cross_edge_force_component_n'] == 3.
    assert result['declared_bore_direction_force_component_n'] == 37.
    assert result['own_free_couple_on_host_about_action_point_xyz_nmm'] == [-22., 11., 33.]


@pytest.mark.parametrize('change', ['axis', 'host', 'interval', 'midpoint', 'grain', 'diameter', 'force', 'couple', 'basis', 'edge'])
def test_foreign_or_invalid_source_action_cannot_enter_a_directional_screen(change):
    args = copy.deepcopy(fixture())
    if change == 'axis':
        args[3]['axis_id'] = 'other'
    elif change == 'host':
        args[3]['host'] = 'other'
    elif change == 'interval':
        args[3]['surface_interval_mm'][1] += 1.
    elif change == 'midpoint':
        args[3]['point_xyz_mm'][0] += 1.
    elif change == 'grain':
        args[3]['grain_axis_xyz'] = [0., 0., 1.]
    elif change == 'diameter':
        args[2]['diameter_mm'] = 9.
    elif change == 'force':
        args[3]['force_on_host_xyz_n'][0] = np.nan
    elif change == 'couple':
        args[3]['moment_on_host_at_point_xyz_nmm'][0] = np.inf
    elif change == 'basis':
        args[1]['basis_grain_u_v_xyz'][0][0] = 2.
    else:
        args[0]['outer_edge_distances'][0]['minimum_axis_to_outer_edge_mm'] = 0.
    with pytest.raises(ValueError):
        evaluate(*args)


def test_connected_pair_minimum_covers_both_shafts_and_both_wood_members():
    groups = [{'physical_axis_ids': ['first', 'second'], 'bearing_members': [
        {'kind': 'wood', 'host': 'a'}, {'kind': 'wood', 'host': 'b'}]}]
    rows = [{'axis_id': axis, 'host': host, 'minimum_signed_force_end_trial': value,
             'any_partial_sloping_end_trial': host == 'b'}
            for axis, host, value in [('first', 'a', 1.), ('first', 'b', .9), ('second', 'a', .6), ('second', 'b', .8)]]
    result = directions.ordinary_minima(groups, rows)[0]
    assert result['own_wood_occurrences_considered'] == 4
    assert result['smallest_force_component_end_trial_for_entire_connection'] == .6
    assert result['partial_sloping_end_trial_present'] is True
    assert result['complete_Cdelta'] is None
    rows[2]['minimum_signed_force_end_trial'] = None
    assert directions.ordinary_minima(groups, rows)[0]['smallest_force_component_end_trial_for_entire_connection'] is None
    with pytest.raises(ValueError):
        directions.ordinary_minima(groups, rows+[rows[0]])


@pytest.mark.parametrize('key,value', [('structural_acceptance', True), ('physical_demand_bounds_established', True),
                                    ('actual_observations', 'assumed'), ('current_bolt_count', 102),
                                    ('loaded_perpendicular_edge_multiplier', 1.5), ('force_direction_gate_n', 1.),
                                    ('distance_gate_mm', .1)])
def test_frozen_scope_and_marker_hypotheses_cannot_be_promoted_or_weakened(key, value):
    data = inputs()
    directions.validate(data)
    data[key] = value
    with pytest.raises(ValueError):
        directions.validate(data)


@pytest.mark.parametrize('module', [directions.ordinary, directions.ordinary.front, directions.ordinary.front.prior])
def test_transitive_execution_helpers_must_be_declared_and_match_the_loaded_source(module, monkeypatch):
    data = inputs()
    directions.helper_sources(data)
    ref = directions.current.ref(module.OWN)
    missing = copy.deepcopy(data)
    missing['references'] = [r for r in missing['references'] if r['path'] != ref['path']]
    with pytest.raises(ValueError):
        directions.helper_sources(missing)
    changed = copy.deepcopy(data)
    next(r for r in changed['references'] if r['path'] == ref['path'])['sha256'] = '0'*64
    with pytest.raises(ValueError):
        directions.helper_sources(changed)
    monkeypatch.setattr(module, 'LOADED_SHA', '0'*64)
    with pytest.raises(ValueError):
        directions.helper_sources(data)
