"""Changed consumed buffers must not be authenticated by restored disk bytes."""
import hashlib
import sys
from pathlib import Path
from types import ModuleType

import pytest

from scripts import eoere_curved_bend_consumer as consumer


def install_transient(monkeypatch, path, consumed):
    original = Path.read_bytes
    calls = []

    def read(item):
        if item.resolve() == path:
            calls.append(item)
            if len(calls) == 1:
                return consumed
        return original(item)

    monkeypatch.setattr(Path, 'read_bytes', read)
    return calls


def test_json_parses_the_same_once_captured_and_hashed_buffer(tmp_path, monkeypatch):
    path = tmp_path/'source.json'
    good = b'{"value": 1}'
    path.write_bytes(good)
    monkeypatch.setattr(consumer, 'ROOT', tmp_path)
    calls = install_transient(monkeypatch, path, good)
    pins = {}
    ref = {'path': path.name, 'sha256': hashlib.sha256(good).hexdigest()}
    assert consumer.read_json(ref, pins) == {'value': 1}
    assert pins == {path.name: ref['sha256']} and len(calls) == 1


@pytest.mark.parametrize('consumed', [b'{"value": 2}', b'not JSON'])
def test_transient_changed_json_is_refused_before_parsing(tmp_path, monkeypatch, consumed):
    path = tmp_path/'source.json'
    good = b'{"value": 1}'
    path.write_bytes(good)
    monkeypatch.setattr(consumer, 'ROOT', tmp_path)
    calls = install_transient(monkeypatch, path, consumed)
    with pytest.raises(ValueError, match='consumed source buffer changed'):
        consumer.read_json({'path': path.name, 'sha256': hashlib.sha256(good).hexdigest()}, {})
    assert len(calls) == 1


def test_transient_input_is_refused_before_mechanics(tmp_path, monkeypatch):
    path = tmp_path/'inputs.json'
    path.write_bytes(b'{"schema": "on disk"}')
    monkeypatch.setattr(consumer, 'ROOT', tmp_path)
    install_transient(monkeypatch, path, b'{"schema": "consumed instead"}')
    called = []
    monkeypatch.setattr(consumer, 'frozen_mechanics', lambda *args: called.append(args))
    with pytest.raises(ValueError, match='source changed since capture'):
        consumer.run(path)
    assert called == []


def test_transient_python_source_is_refused_before_compile(tmp_path, monkeypatch):
    path = tmp_path/'source.py'
    good = b'VALUE = 1\n'
    path.write_bytes(good)
    monkeypatch.setattr(consumer, 'ROOT', tmp_path)
    install_transient(monkeypatch, path, b'raise AssertionError("must not execute")\n')
    with pytest.raises(ValueError, match='consumed source buffer changed'):
        consumer.captured_module({'path': path.name, 'sha256': hashlib.sha256(good).hexdigest()}, 'unit', {})


def test_valid_captured_module_executes_its_authenticated_bytes(tmp_path, monkeypatch):
    path = tmp_path/'source.py'
    good = b'VALUE = 7\n'
    path.write_bytes(good)
    monkeypatch.setattr(consumer, 'ROOT', tmp_path)
    module = consumer.captured_module({'path': path.name, 'sha256': hashlib.sha256(good).hexdigest()}, 'unit', {})
    assert module.VALUE == 7 and module.__file__ == str(path)


def test_contradictory_pins_and_outside_paths_are_refused(tmp_path, monkeypatch):
    path = tmp_path/'source.json'
    good = b'{}'
    path.write_bytes(good)
    monkeypatch.setattr(consumer, 'ROOT', tmp_path)
    ref = {'path': path.name, 'sha256': hashlib.sha256(good).hexdigest()}
    with pytest.raises(ValueError, match='contradictory'):
        consumer.read_json(ref, {path.name: '0'*64})
    with pytest.raises(ValueError, match='outside repository'):
        consumer.read_json({'path': '../outside.json', 'sha256': '0'*64}, {})


def test_frozen_mechanics_reuses_definitions_without_running_other_module_code(tmp_path, monkeypatch):
    path = tmp_path/'mechanics.py'
    good = (b'ROTATION = np.eye(3)\nraise AssertionError("unselected module code")\n'
            b'def gravity_partition(*args): return ROTATION[0,0]\n'
            b'def reduce(*args): return gravity_partition()+6\n')
    path.write_bytes(good)
    monkeypatch.setattr(consumer, 'ROOT', tmp_path)
    methods = consumer.frozen_mechanics({'path': path.name, 'sha256': hashlib.sha256(good).hexdigest()}, {})
    assert methods.reduce() == 7


def test_captured_calculator_uses_its_own_core_and_restores_global_binding(tmp_path, monkeypatch):
    monkeypatch.setattr(consumer, 'ROOT', tmp_path)
    original = ModuleType('original_core')
    monkeypatch.setitem(sys.modules, 'core', original)
    refs = {}
    for name, source in [('core', b'VALUE = 7\n'), ('calculator', b'import core\nVALUE = core.VALUE\n')]:
        path = tmp_path/(name+'.py')
        path.write_bytes(source)
        refs[name] = {'path': path.name, 'sha256': hashlib.sha256(source).hexdigest()}
    module = consumer.calculator(refs, {})
    assert module.VALUE == 7 and module.core is not original
    assert sys.modules['core'] is original
