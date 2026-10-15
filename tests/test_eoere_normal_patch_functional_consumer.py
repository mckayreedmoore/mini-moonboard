"""Exact-remainder and captured-gate controls, without candidate assets."""
import ast
import sys
from copy import deepcopy
from fractions import Fraction as F
from types import SimpleNamespace

import pytest

from scripts import eoere_normal_patch_functional_consumer as model
from scripts import eoere_original_load_bounds as bounds


def test_complete_ast_restores_with_only_the_declared_two_gate_delta():
    original = ast.parse((model.ROOT/model.BASE['path']).read_bytes())
    changed = model.rewrite(deepcopy(original))
    restored = model.rewrite(deepcopy(changed), reverse=True)
    assert ast.dump(restored) == ast.dump(original)
    assert ast.dump(changed) != ast.dump(original)


def test_preserved_exact_unit_guard_is_not_silently_rewritten_on_disk():
    data = (model.ROOT/model.BASE['path']).read_text()
    assert 'all(action[j] == -1 for j in js)' in data
    assert "components[j]['kind'] == 'common_shaft_bearing'" in data
    assert model.captured(model.BASE, {}) == data.encode()


def test_registered_floor_remainders_remain_in_the_exact_metric():
    driver = model.producer({}); epsilon = F(1, 2**55)
    coefficients = driver.equivalent([1, 0], [-1-epsilon, 1], -1)
    assert coefficients == [-epsilon, 1]
    result = driver.shifted_scalar(2, dict(enumerate(coefficients)), [0, 0], [0, 0], [100000, 1], F(1, 2),
                                    SimpleNamespace(functional=bounds.functional))
    gram = F(result['unchanged_metric_enclosure']['exact_weighted_Gram_spectral_upper'])
    assert gram == 1+100000*epsilon**2 and gram > 1
    assert F(result['unchanged_metric_enclosure']['exact_equilibrium_change_norm_upper']) > 1


def gate(message):
    tree = model.rewrite(ast.parse((model.ROOT/model.BASE['path']).read_bytes()))
    call, = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id == 'require' and len(n.args) == 2 and isinstance(n.args[1], ast.Constant)
             and n.args[1].value == message]
    return compile(ast.Expression(call.args[0]), '<verified-guard>', 'eval')


def test_revised_floor_gate_accepts_exact_remainder_and_refuses_wrong_sign():
    condition = gate(model.MESSAGES[0][1]); action = [-1-F(1, 2**55), -1, -1, -1]
    assert eval(condition, {'action': action, 'js': set(range(4))})
    action[2] = 0
    assert not eval(condition, {'action': action, 'js': set(range(4))})


def test_revised_metric_gate_retains_floor_terms_and_refuses_continuous_flange():
    condition = gate(model.MESSAGES[1][1])
    for kind, expected in [('common_shaft_bearing', True), ('floor_normal', True), ('flange_contact', False)]:
        assert bool(eval(condition, {'sparse': {0: F(1)}, 'components': [{'kind': kind}]})) is expected


def test_signed_registered_offset_is_not_rounded_to_a_body_weight():
    driver = model.producer({}); epsilon = F(7, 2**51)
    result = driver.shifted_scalar(2+epsilon, {1: 1}, [0, 0], [0, 0], [1, 1], 0,
                                    SimpleNamespace(functional=bounds.functional))
    assert F(result['exact_signed_lower_n']) == 2+epsilon


def test_poisoned_ordinary_driver_cache_does_not_execute(monkeypatch):
    def poison(*args, **kwargs):
        raise AssertionError('cached driver must not execute')
    cached = SimpleNamespace(run=poison, equivalent=poison)
    monkeypatch.setitem(sys.modules, 'scripts.eoere_normal_patch_functionals', cached)
    driver = model.producer({})
    assert driver is not cached and driver.equivalent([1, 0], [-1, 1], -1) == [0, 1]


def test_unexpected_source_shape_cannot_bypass_the_declared_delta():
    with pytest.raises(ValueError, match='exactly two declared gates'):
        model.rewrite(ast.parse('answer = 1'))


def test_conflicting_frozen_driver_pin_is_refused():
    with pytest.raises(ValueError, match='source changed'):
        model.producer({model.BASE['path']: '0'*64})


def test_same_scope_rejects_a_changed_gap_source_and_omitted_execution_ref():
    original = {key: key for key in model.SCOPE}; original['execution_sources'] = [{'path': 'old', 'sha256': 'same'}]
    model.same_scope(deepcopy(original), original)
    changed = deepcopy(original); changed['reaction_result'] = 'changed'
    with pytest.raises(ValueError, match='same frozen functional scope'):
        model.same_scope(changed, original)
    changed = deepcopy(original); changed['execution_sources'] = []
    with pytest.raises(ValueError, match='preserved execution references'):
        model.same_scope(changed, original)
