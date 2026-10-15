import copy

import pytest

from scripts import eoere_front_bolt_row_factor as audit


@pytest.mark.parametrize('cross,expected', [(0., True), (9.999, True), (10., False), (10.001, False), (40., False)])
def test_strict_quarter_rule_and_aligned_pair(cross, expected):
    result = audit.row_classification([40., cross, 0.], [5., 0., 0.], [0., 0., 1.])
    assert result['strict_quarter_rule_merges_rows'] is expected
    assert result['quarter_parallel_offset_mm'] == 10.
    assert result['between_load_aligned_rows_mm'] == cross
    assert result['component_Cg'] == (None if expected else 1.)


def test_force_and_pair_reversal_and_force_scaling_preserve_classification():
    first = audit.row_classification([28., 28., 0.], [1., -2., 0.], [0., 0., 1.])
    second = audit.row_classification([-28., -28., 0.], [-10., 20., 0.], [0., 0., -1.])
    for key in ('component_Cg', 'strict_quarter_rule_merges_rows', 'fasteners_per_Cg_row'):
        assert first[key] == second[key]
    assert first['unmerged_row_margin_mm'] == pytest.approx(second['unmerged_row_margin_mm'])


def test_perpendicular_pair_gives_two_singleton_rows():
    result = audit.row_classification([0., 40., 0.], [5., 0., 0.], [0., 0., 1.])
    assert result['parallel_to_load_offset_mm'] == 0.
    assert result['component_Cg'] == 1.


def test_zero_resultant_never_receives_an_assumed_direction_or_factor():
    result = audit.row_classification([40., 10., 0.], [0., 0., 0.], [0., 0., 1.])
    assert result['component_Cg'] is None and result['load_direction_xyz'] is None


@pytest.mark.parametrize('delta,force,axis', [
    ([0., 0., 0.], [1., 0., 0.], [0., 0., 1.]),
    ([40., 1., 1.], [1., 0., 0.], [0., 0., 1.]),
    ([40., 1., 0.], [1., 0., 1.], [0., 0., 1.]),
    ([40., float('nan'), 0.], [1., 0., 0.], [0., 0., 1.]),
    ([40., 1., 0.], [1., 0., 0.], [0., 0., 2.]),
])
def test_unsupported_or_nonfinite_vectors_are_refused(delta, force, axis):
    with pytest.raises(ValueError): audit.row_classification(delta, force, axis)


def shafts():
    return [{'axis_id': str(i), 'surfaces': [{'kind': 'wood', 'host': 'main'}, {'kind': 'wood', 'host': 'side'}]}
            for i in range(2)]


def test_isolated_pair_uses_complete_physical_connector_census_without_mutation():
    data = shafts(); before = copy.deepcopy(data)
    assert audit.isolated_pair(data, ['main', 'side'], ['0', '1']) == ['0', '1']
    assert data == before


def test_additional_shared_receiver_shaft_prevents_two_bolt_classification():
    data = shafts(); data.append({**copy.deepcopy(data[0]), 'axis_id': '2'})
    with pytest.raises(ValueError): audit.isolated_pair(data, ['main', 'side'], ['0', '1'])


def test_only_one_present_physical_shaft_is_not_an_isolated_pair():
    with pytest.raises(ValueError): audit.isolated_pair(shafts()[:1], ['main', 'side'], ['0', '1'])


def test_third_bearing_member_is_not_treated_as_the_two_wood_component():
    data = shafts(); data[0]['surfaces'].append({'kind': 'steel', 'host': 'plate'})
    with pytest.raises(ValueError): audit.isolated_pair(data, ['main', 'side'], ['0', '1'])


def test_mathematical_singleton_factor_does_not_require_matching_EA():
    from fea.reinforced_timber_resistance import group_factor
    assert group_factor(1, 4., 1.e6, 2.e5) == 1.
    assert group_factor(1, 40., 2.e5, 1.e6, steel_side=True) == 1.


@pytest.mark.parametrize('case,expected', [('consistent', 1.), ('opposed', None), ('mixed', None)])
def test_factor_credit_requires_group_and_both_own_direction_classifications(case, expected):
    geometry = {'member': 'post', 'axis_ids': ['0', '1'], 'grain_axis_xyz': [0., 0., 1.],
                'cross_grain_axis_xyz': [0., 1., 0.], 'own_bearing_midpoints_xyz_mm': [[0., 0., 0.], [0., 40., 10.]]}
    forces = [[0., 0., 5.], [0., 0., 5.]]
    if case == 'opposed': forces = [[0., 0., 10.], [0., 0., -10.]]
    elif case == 'mixed': forces = [[0., 40., 10.], [0., -40., 0.]]
    complete = {'force_xyz_n': [sum(f[i] for f in forces) for i in range(3)], 'moment_xyz_nmm': [7., 8., 9.]}
    saved = {'complete_group_wrench_scope': complete, 'own_signed_action_scope': [
        {'axis_id': str(i), 'force_xyz_n': f} for i, f in enumerate(forces)]}
    before = copy.deepcopy(saved)
    result = audit.member_row_scope(geometry, saved)
    assert result['isolated_lateral_component_Cg'] == expected
    assert result['complete_group_wrench_retained'] == complete
    assert saved == before
