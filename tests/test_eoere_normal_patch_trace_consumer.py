"""Sparse-row coordinate controls without any candidate response calculation."""
import ast
import hashlib
import json
import sys
from fractions import Fraction as F
from types import SimpleNamespace

import pytest

from scripts import eoere_normal_patch_trace_consumer as consumer


def miniature(extra=''):
    return ('def run(coefficients, columns, q):\n'
            '    stored = '+consumer.STORED_EXPRESSION+'\n'+extra+
            '    return stored\n')


@pytest.mark.parametrize('compression', [F(1, 8), -F(3, 16), F(0), F(1, 2**100)])
def test_actual_dispatch_converts_compression_into_opening_exactly(compression):
    original, adapted = {'F': F}, {'F': F}
    source = miniature()
    exec(compile(source, '<original>', 'exec'), original)  # noqa: S102 - miniature test function
    exec(compile(consumer.opening_tree(source), '<adapted>', 'exec'), adapted)  # noqa: S102
    coefficients, columns, q = [2., -1.], [0, 2], [compression/2, F(0), F(0)]
    assert original['run'](coefficients, columns, q) == compression
    assert adapted['run'](coefficients, columns, q) == -compression


def test_only_the_declared_assignment_changes_in_the_real_captured_source():
    source = consumer.captured({'path': consumer.V1_PATH, 'sha256': consumer.V1_SHA})
    original, adapted = ast.parse(source), consumer.opening_tree(source)
    run = next(n for n in adapted.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
    assignment = next(n for n in ast.walk(run) if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'stored' for t in n.targets))
    assert isinstance(assignment.value, ast.UnaryOp) and isinstance(assignment.value.op, ast.USub)
    assignment.value = assignment.value.operand
    assert ast.dump(adapted) == ast.dump(original)


@pytest.mark.parametrize('opening', [F(1, 8), -F(3, 16), F(0)])
def test_original_contact_construction_uses_the_opposite_relative_displacement(opening):
    path = 'scripts/thin_bolted_frame_mechanics.py'
    data = consumer.captured({'path': path,
                             'sha256': '05cdf6897645fe7ee1b72b5b5125c04c68d758108f4860f995cef6aa1b676448'})
    function = next(n for n in ast.parse(data).body if isinstance(n, ast.FunctionDef) and n.name == 'elastic_connections')
    loop = next(n for n in function.body if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == 'edge')
    statement = next(n for n in loop.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'row' for t in n.targets))
    assembly = SimpleNamespace(scalar_port=lambda name, *_: opening if name == 'fitting' else F(0))
    env = {'assembly': assembly, 'normal': [0, 0, 1],
           'edge': {'first': 'fitting', 'second': 'wood', 'point_xyz_mm': [0, 0, 0], 'flange': 'own'}}
    exec(compile(ast.Module(body=[statement], type_ignores=[]), path, 'exec'), env)  # noqa: S102 - one source assignment
    assert env['row'] == -opening


@pytest.mark.parametrize('source', [
    'def other():\n    return 0\n',
    'def run():\n    return 0\n',
    miniature('    stored = 0\n'),
    miniature().replace('F(float(v))', 'F(v)'),
    miniature().replace('stored =', 'stored = other =')])
def test_refuses_missing_duplicate_or_changed_assignment(source):
    with pytest.raises(ValueError, match='preserved'):
        consumer.opening_tree(source)


def test_preserved_producer_is_private_and_independent_of_cached_module(monkeypatch):
    name = 'scripts.eoere_normal_patch_trace'
    sentinel = SimpleNamespace(LOADED_SHA='foreign', run=lambda _: 'foreign')
    monkeypatch.setitem(sys.modules, name, sentinel)
    consumer._producer.cache_clear()
    try:
        module = consumer._producer()
        assert module is not sentinel and module.LOADED_SHA == consumer.V1_SHA
        assert sys.modules[name] is sentinel
    finally:
        consumer._producer.cache_clear()


def test_capture_refuses_changed_source_buffer():
    with pytest.raises(ValueError, match='source buffer changed'):
        consumer.captured({'path': consumer.V1_PATH, 'sha256': '0'*64})
    assert hashlib.sha256(consumer.captured({'path': consumer.V1_PATH, 'sha256': consumer.V1_SHA})).hexdigest() == consumer.V1_SHA


def test_result_keeps_raw_compression_and_normalized_opening_unambiguously(tmp_path, monkeypatch):
    driver = tmp_path/'driver.py'; driver.write_text('adapter fixture\n')
    digest = hashlib.sha256(driver.read_bytes()).hexdigest()
    own = {'path': 'driver.py', 'sha256': digest}
    producer_ref = {'path': consumer.V1_PATH, 'sha256': consumer.V1_SHA}
    inputs = {'execution_adapter_schema': 'eoere_current_normal_patch_trace_adapter/v2',
              'execution_sources': [own, producer_ref], 'source_coordinate_convention': consumer.CONVENTION,
              'preserved_v1_inputs': own, 'stopped_v1_execution': own}
    reference = {'path': 'inputs.json', 'sha256': 'fixture'}
    buffers = {'inputs.json': json.dumps(inputs).encode(), own['path']: driver.read_bytes(), producer_ref['path']: b'fixture'}
    fake = SimpleNamespace(F=F, run=lambda _: {'records': [{'source_centroids': [{'exact_gap_mm': '1/8',
                            'exact_stored_Bq_mm': '1/8', 'exact_map_error_mm': '0'}]}], 'source_sha256': {}})
    monkeypatch.setattr(consumer, 'ROOT', tmp_path); monkeypatch.setattr(consumer, 'OWN', driver)
    monkeypatch.setattr(consumer, 'LOADED_SHA', digest)
    monkeypatch.setattr(consumer, 'captured', lambda ref: buffers[ref['path']])
    monkeypatch.setattr(consumer, '_producer', lambda: fake)
    result = consumer.run(reference)
    row = result['records'][0]['source_centroids'][0]
    assert 'exact_stored_Bq_mm' not in row
    assert row['exact_original_stored_compression_Bq_mm'] == '-1/8'
    assert row['exact_negative_stored_compression_Bq_mm'] == row['exact_gap_mm'] == '1/8'
    assert result['source_coordinate_convention'] == consumer.CONVENTION
    assert result['execution_driver'] == own
    assert result['source_sha256'] == {own['path']: digest, consumer.V1_PATH: consumer.V1_SHA}
