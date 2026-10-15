"""Controls for the single frozen strength-input admission correction."""
import ast
import sys
from types import SimpleNamespace

import pytest

from scripts import eoere_continuum_material_consumer as model


@pytest.mark.parametrize('value', [2, '2', '4/2', '2.0'])
def test_exact_integer_and_text_representations_preserve_the_retained_divisor(value):
    assert model.strength_divisor(value) == 2


@pytest.mark.parametrize('value', [True, False, 2., None, '3', 1, '1/0', 'nan', ''])
def test_nonexact_types_other_values_and_invalid_rationals_are_refused(value):
    with pytest.raises(ValueError):
        model.strength_divisor(value)


def test_single_admission_correction_preserves_every_other_ast_node():
    source = "strength={'working_strength_divisor':'2'}\nadmitted=strength['working_strength_divisor'] == 2\nenergy=3*7/2\n"
    adapted = model.adapt_admission(source)
    actual = {}
    exec(compile(adapted, '<guard-control>', 'exec'), {'_verified_strength_divisor': model.strength_divisor}, actual)  # noqa: S102 - literal test input
    assert actual['admitted'] is True and actual['energy'] == 10.5
    call, = [node for node in ast.walk(adapted) if isinstance(node, ast.Call)]
    for node in ast.walk(adapted):
        if isinstance(node, ast.Compare):
            node.left = call.args[0]
    assert ast.dump(adapted) == ast.dump(ast.parse(source))


@pytest.mark.parametrize('source', ['admitted=True', model.COMPARISON+'\n'+model.COMPARISON,
    '_verified_strength_divisor=1\n'+model.COMPARISON])
def test_missing_duplicated_or_shadowed_guard_is_refused(source):
    with pytest.raises(ValueError):
        model.adapt_admission(source)


def test_captured_driver_ignores_poisoned_cache_preserves_material_law_and_refuses_conflicting_pin(monkeypatch):
    monkeypatch.setitem(sys.modules, 'scripts.eoere_continuum_material_law', SimpleNamespace(run=None))
    driver = model.producer({})
    assert callable(driver.run) and driver.LOADED_SHA == model.DRIVER['sha256']
    assert driver.green_strain([[1, 0, 0], [0, 1, 0], [0, 0, 1]]) == [0]*6
    assert driver._verified_strength_divisor('2') == 2
    with pytest.raises(ValueError, match='driver changed'):
        model.producer({model.DRIVER['path']: '0'*64})
