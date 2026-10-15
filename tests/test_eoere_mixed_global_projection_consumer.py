"""Exact large-fraction export and bounded-policy restoration controls."""
import sys
from fractions import Fraction as F
from types import SimpleNamespace

import pytest

from scripts import eoere_mixed_global_projection_consumer as model


def test_large_exact_fraction_round_trips_with_scoped_policy_and_restores_it():
    original = sys.get_int_max_str_digits()
    value = F(10**5000+7, 3)
    with model.integer_text_policy(20000):
        assert sys.get_int_max_str_digits() == 20000
        text = str(value)
        assert F(text) == value
    assert sys.get_int_max_str_digits() == original


def test_conversion_remains_bounded_and_body_failure_restores_the_prior_policy():
    original = sys.get_int_max_str_digits()
    with pytest.raises(RuntimeError), model.integer_text_policy(20000):
        with pytest.raises(ValueError, match='Exceeds the limit'):
            str(10**21000)
        raise RuntimeError('controlled body failure')
    assert sys.get_int_max_str_digits() == original


@pytest.mark.parametrize('limit', [0, -1, True, 20000., 1000000])
def test_unbounded_or_unreviewed_conversion_policy_is_refused(limit):
    original = sys.get_int_max_str_digits()
    with pytest.raises(ValueError, match='finite'), model.integer_text_policy(limit):
        pytest.fail('invalid policy admitted')
    assert sys.get_int_max_str_digits() == original


def test_producer_executes_captured_frozen_bytes_instead_of_a_module_cache(monkeypatch):
    monkeypatch.setitem(sys.modules, 'scripts.eoere_mixed_global_projection_limit', SimpleNamespace(run=None))
    driver = model.producer({})
    assert callable(driver.run) and driver.LOADED_SHA == model.DRIVER['sha256']
    assert driver.annihilator_floor([1, -1], [1, 0], [1, 1], [], 0)['exact_full_metric_lower_for_every_registered_kernel_projection'] == '1/2'
    with pytest.raises(ValueError, match='driver changed'):
        model.producer({model.DRIVER['path']: '0'*64})
