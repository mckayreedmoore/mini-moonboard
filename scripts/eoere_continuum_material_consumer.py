"""Read the retained textual strength divisor in the frozen bulk-law checker.

Only one input admission comparison is adapted; constitutive arithmetic and
all captured input bytes are preserved. This computes no assembled response.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
DRIVER = {'path': 'scripts/eoere_continuum_material_law.py',
          'sha256': '33a5fc73e4ab33290412dcec07d03a2bc3c5f55c65942db3dcb11a17057b9b82'}
COMPARISON = "strength['working_strength_divisor'] == 2"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def strength_divisor(value):
    require(type(value) in (int, str), 'integer or exact rational text strength divisor required')
    try:
        parsed = F(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError('valid exact strength divisor required') from error
    require(parsed == 2, 'retained working strength divisor must equal two')
    return 2


def adapt_admission(data):
    """Replace exactly one captured comparison; do not execute imported caches."""
    tree = ast.parse(data)
    target = ast.dump(ast.parse(COMPARISON, mode='eval').body)
    matches = [node for node in ast.walk(tree) if isinstance(node, ast.Compare) and ast.dump(node) == target]
    require(len(matches) == 1, 'exactly one retained strength admission comparison required')
    require(not any(isinstance(node, ast.Name) and node.id == '_verified_strength_divisor'
                    for node in ast.walk(tree)), 'private admission helper must not shadow captured code')
    node = matches[0]
    node.left = ast.copy_location(ast.Call(func=ast.Name(id='_verified_strength_divisor', ctx=ast.Load()),
                                          args=[node.left], keywords=[]), node.left)
    return ast.fix_missing_locations(tree)


def producer(pins):
    data = (ROOT/DRIVER['path']).read_bytes()
    require(hashlib.sha256(data).hexdigest() == DRIVER['sha256']
            and pins.get(DRIVER['path'], DRIVER['sha256']) == DRIVER['sha256'], 'frozen material driver changed')
    pins[DRIVER['path']] = DRIVER['sha256']
    module = ModuleType('_eoere_verified_material_admission_driver')
    module.__file__ = str(ROOT/DRIVER['path']); module._verified_strength_divisor = strength_divisor
    exec(compile(adapt_admission(data), module.__file__, 'exec'), module.__dict__)  # noqa: S102 - verified single-guard adaptation
    return module


def run(reference):
    pins = {}; driver = producer(pins); prior = driver.bootstrap(pins)
    boot = prior.bootstrap(pins); base = boot.producer(pins)
    inputs = json.loads(base.captured(reference, pins))
    require(inputs['consumer_schema'] == 'eoere_continuum_material_admission_consumer/v1'
            and inputs['frozen_driver'] == DRIVER, 'same frozen bulk-law driver required')
    for row in inputs['execution_sources']:
        base.captured(row, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing material consumer required')
    stopped = json.loads(base.captured(inputs['preserved_stopped_preflight'], pins))
    require(stopped['engineering_result_issued'] is False and stopped['exit_code'] == 1
            and stopped['inputs'] == inputs['preserved_v1_inputs'], 'preserved unissued v1 admission stop required')
    original = json.loads(base.captured(inputs['preserved_v1_inputs'], pins))
    strength = json.loads(base.captured(original['retained_strength_input'], pins))
    value = strength['working_strength_divisor']
    require(type(value) is str and value == '2', 'unchanged retained textual divisor required')
    result = driver.run(inputs['preserved_v1_inputs'])
    for path, digest in result['source_sha256'].items():
        base.captured({'path': path, 'sha256': digest}, pins)
    for path, digest in tuple(pins.items()):
        base.captured({'path': path, 'sha256': digest}, pins)
    result.update(source_sha256=pins, consumer_inputs=reference,
        execution_consumer={'path': str(OWN.relative_to(ROOT)), 'sha256': LOADED_SHA},
        frozen_material_driver=DRIVER, preserved_stopped_preflight=inputs['preserved_stopped_preflight'],
        input_admission_adaptation={'comparison': COMPARISON, 'matched_comparisons': 1,
            'stored_type': 'str', 'stored_value': value, 'exact_numeric_value': str(F(value)),
            'normalization': 'integer-or-rational-text equal to two before this admission comparison only',
            'captured_input_bytes_changed': False, 'bulk_material_arithmetic_changed': False})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); require(not args.out.exists(), 'preserve issued material-law evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference); args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(), 'inventory': result['inventory']}))


if __name__ == '__main__':
    main()
