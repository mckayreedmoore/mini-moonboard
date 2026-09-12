"""Signed panel demands and flange transfer must survive free-body cancellation."""
import copy

import pytest

from fea.reinforced_fastener_checks import (
    HEAD_N,
    VALIDITY,
    assess,
    panel_check,
    wrench,
)


def physical(first, second, force, point=(0., 0., 0.), axis=(0., 0., 1.)):
    return {'first': first, 'second': second, 'point': list(point), 'axis': list(axis),
            'force_on_first_xyz_n': list(force),
            'force_on_second_xyz_n': [-x for x in force]}


def fixture(bearing=False):
    rows = {'panel_screw': physical('wood', 'panel', (0., 0., -HEAD_N))}
    panel_geometry = {name: {k: row[k] for k in ('first', 'second', 'point', 'axis')}
                      for name, row in rows.items()}
    clips = {}
    for flange, sign in [('beam', 1), ('upright', -1)]:
        for i in (1, 2, 3):
            name = f'clip_test_{flange}_{i}'
            row = physical(flange, 'clip_test', (100.*sign, 20.*sign, 50.*sign),
                           point=(0., i*10., 0.))
            rows[name] = row
            clips[name] = {k: row[k] for k in ('first', 'second', 'point', 'axis')}
    stations = [{'name': 'clip_test', 'origin_mm': [0., 0., 0.],
                 'first_member': 'beam', 'second_member': 'upright',
                 'F1_axis': [0., 0., 1.], 'F2_separation_axis': [1., 0., 0.],
                 'F3_F4_axis_unsigned': [0., 1., 0.],
                 'F2_catalog_allowable_lbf': None if bearing else 450}]
    report = {'physical_connection_forces': rows, **{k: True for k in VALIDITY}}
    return report, (panel_geometry, clips, stations)


def test_receiver_axis_tension_sign_and_no_compression_capacity_claim():
    tension = panel_check(physical('wood', 'panel', (0., 0., -HEAD_N)))
    assert tension['head_pull_through_ratio'] == pytest.approx(1.)
    assert tension['tension_n'] == HEAD_N
    compression = panel_check(physical('wood', 'panel', (0., 0., HEAD_N)))
    assert compression['tension_n'] == 0.
    assert compression['compression_n'] == HEAD_N
    assert not compression['compression_action_accepted']


def test_force_reconstruction_and_no_invented_steel_interaction():
    checked = panel_check(physical('wood', 'panel', (300., 400., -100.)))
    assert checked['shear_n'] == pytest.approx(500.)
    assert checked['tension_n'] == 100.
    assert not checked['combined_steel_resistance_established']
    with pytest.raises(ValueError, match='unit'):
        panel_check(physical('wood', 'panel', (0., 0., 1.), axis=(0., 0., 2.)))


def test_flange_transfer_is_not_cancelled_by_all_six_screw_residual():
    report, geo = fixture()
    result = assess(report, geo)['ML24Z_checks'][0]
    assert result['all_six_screw_free_body_residual']['force_xyz_n'] == [0., 0., 0.]
    assert result['all_six_screw_free_body_residual']['moment_xyz_nmm'] == [0., 0., 0.]
    assert result['flange_member_on_bracket_wrenches']['beam']['force_xyz_n'] == [-300., -60., -150.]
    assert result['single_end_conservative_absolute_force_unity'] > 0
    assert not result['independent_couple_resolved'] and not result['connection_rating_passed']


def test_wrench_translation_changes_cross_moment_not_parallel_couple():
    rows = [physical('wood', 'clip', (0., -100., -50.), point=(20., 10., 30.))]
    a, b = wrench(rows, [0., 0., 0.]), wrench(rows, [5., 7., 11.])
    assert a['force_xyz_n'] == b['force_xyz_n']
    assert a['moment_xyz_nmm'] != b['moment_xyz_nmm']
    assert a['parallel_couple_nmm'] == pytest.approx(b['parallel_couple_nmm'], abs=1e-9)


def test_bearing_separation_has_no_made_up_capacity():
    report, geo = fixture(bearing=True)
    row = assess(report, geo)['ML24Z_checks'][0]
    assert row['bearing_separation_demand_n'] == 300.
    assert row['bearing_separation_capacity_n'] is None
    assert row['single_end_conservative_absolute_force_unity'] is None


def test_nonconverged_response_cannot_be_promoted_by_component_checks():
    report, geo = fixture()
    report['contact_active_set_converged'] = False
    result = assess(report, geo)
    assert result['response_status'] == 'INVALID_RESPONSE_DIAGNOSTIC_ONLY'
    assert not result['qualified_for_design']


def test_missing_and_reversed_receiver_inputs_fail():
    report, geo = fixture()
    bad = copy.deepcopy(report)
    del bad['physical_connection_forces']['panel_screw']
    with pytest.raises(ValueError, match='Missing'):
        assess(bad, geo)
    report['physical_connection_forces']['panel_screw']['first'] = 'panel'
    with pytest.raises(ValueError, match='ownership'):
        assess(report, geo)
