"""Adversarial execution-buffer controls, without recovered candidate inputs."""
import hashlib
import json
import sys
import types

import pytest

from scripts import eoere_cleat_surface_consumer as consumer


def ref(path, root):
    return {'path': str(path.relative_to(root)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def test_private_compile_executes_captured_buffer_after_path_change(tmp_path, monkeypatch):
    monkeypatch.setattr(consumer, 'ROOT', tmp_path)
    path = tmp_path/'source.py'
    path.write_bytes(b'VALUE=17\n')
    data = consumer.capture(ref(path, tmp_path))
    path.write_bytes(b'raise RuntimeError("different disk code")\n')
    assert consumer.compile_private(data, 'source.py').VALUE == 17


def test_capture_rejects_changed_source_and_external_path(tmp_path, monkeypatch):
    monkeypatch.setattr(consumer, 'ROOT', tmp_path)
    path = tmp_path/'source.py'
    path.write_bytes(b'VALUE=17\n')
    source = ref(path, tmp_path)
    path.write_bytes(b'VALUE=18\n')
    with pytest.raises(ValueError, match='source changed'):
        consumer.capture(source)
    with pytest.raises(ValueError, match='repository source'):
        consumer.capture({'path': '../outside.py', 'sha256': '0'*64})


def test_cached_helpers_are_bypassed_and_sys_modules_untouched(tmp_path, monkeypatch):
    monkeypatch.setattr(consumer, 'ROOT', tmp_path)
    paths = [consumer.PRODUCER, *(path for _, path in consumer.HELPERS.values())]
    source = {
        consumer.PRODUCER: b'from pathlib import Path\ndef actual():\n from fea import wood_joint_reduced_contacts as p\n from scripts import wood_joint_current_face_pair_atlas_attempt01 as a\n return p.VALUE,a.VALUE\n',
        paths[1]: b'VALUE=11\n', paths[2]: b'VALUE=23\n'}
    refs = []
    for name, data in source.items():
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        refs.append(ref(path, tmp_path))
    fake = {}
    for package, (member, _) in consumer.HELPERS.items():
        module = types.ModuleType(package+'.'+member)
        module.VALUE = 'unverified cached module'
        fake[package+'.'+member] = module
        monkeypatch.setitem(sys.modules, package+'.'+member, module)
    producer, helpers = consumer.verified_modules(refs)
    assert producer.actual() == (11, 23)
    for name, module in fake.items():
        assert sys.modules[name] is module
    assert helpers['fea'] is not fake['fea.wood_joint_reduced_contacts']
    importer = producer.__dict__['__builtins__']['__import__']
    with pytest.raises(ValueError, match='unexpected'):
        importer('fea', fromlist=('other',))
    with pytest.raises(ValueError, match='unbound'):
        importer('fea.unbound')


def test_driver_refuses_input_without_exact_executing_consumer(tmp_path, monkeypatch):
    monkeypatch.setattr(consumer, 'ROOT', tmp_path)
    monkeypatch.setattr(consumer, 'OWN', tmp_path/'driver.py')
    path = tmp_path/'input.json'
    path.write_text(json.dumps({'execution_sources': []}))
    with pytest.raises(ValueError, match='exact executing consumer'):
        consumer.run(ref(path, tmp_path))
