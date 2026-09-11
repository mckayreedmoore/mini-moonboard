"""Recorded CI roundoff is accepted; material or identity drift remains an error."""
import copy

import pytest
from replay_roundoff import assert_roundoff_equal


def evidence():
    return {'sha256': 'original', 'nodes': [12, 17],
            'weights': [-0.10816072601736357, 0.7539524161123258]}


def test_recorded_ci_last_digit_difference_without_mutating_evidence():
    expected = evidence()
    actual = copy.deepcopy(expected)
    actual['weights'] = [-0.10816072601736353, 0.7539524161123261]
    before = copy.deepcopy(actual)
    assert actual != expected
    assert_roundoff_equal(actual, expected, paths=[('weights',)])
    assert actual == before


@pytest.mark.parametrize('field,value', [
    ('sha256', 'changed'), ('nodes', [12, 18]), ('nodes', [17, 12]),
    ('weights', [-0.108160716, 0.7539524161123258]),
    ('weights', [float('nan'), 0.7539524161123258]),
    ('weights', [True, 0.7539524161123258]), ('weights', [0.0]),
])
def test_roundoff_scope_rejects_changed_evidence(field, value):
    expected = evidence()
    actual = {**expected, field: value}
    with pytest.raises(AssertionError):
        assert_roundoff_equal(actual, expected, paths=[('weights',)])


def test_unselected_numeric_field_and_integer_ids_stay_exact():
    with pytest.raises(AssertionError):
        assert_roundoff_equal({'value': 1.0000000000000002}, {'value': 1.0}, paths=[])
    with pytest.raises(AssertionError):
        assert_roundoff_equal({'node': 12}, {'node': 12}, paths=[('node',)])
