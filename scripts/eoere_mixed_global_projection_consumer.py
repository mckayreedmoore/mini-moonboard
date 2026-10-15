"""Run the frozen global proof with a bounded exact-fraction text policy."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
DRIVER = {'path': 'scripts/eoere_mixed_global_projection_limit.py',
          'sha256': '025355ed0238f24a12dbf6433447e7d2cc97d54242a6727302b463fc82fc4d7f'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


@contextmanager
def integer_text_policy(limit):
    require(type(limit) is int and limit == 20000, 'declared finite 20000-digit limit required')
    previous = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(limit)
    try:
        yield
    finally:
        sys.set_int_max_str_digits(previous)


def producer(pins):
    data = (ROOT/DRIVER['path']).read_bytes()
    require(hashlib.sha256(data).hexdigest() == DRIVER['sha256']
            and pins.get(DRIVER['path'], DRIVER['sha256']) == DRIVER['sha256'], 'frozen global driver changed')
    pins[DRIVER['path']] = DRIVER['sha256']
    module = ModuleType('_eoere_verified_global_projection_driver')
    module.__file__ = str(ROOT/DRIVER['path'])
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102 - verified frozen buffer
    return module


def run(reference):
    pins = {}; driver = producer(pins); prior = driver.prior_method(pins)
    boot = prior.bootstrap(pins); base = boot.producer(pins)
    inputs = json.loads(base.captured(reference, pins))
    require(inputs['consumer_schema'] == 'eoere_mixed_global_projection_integer_consumer/v1'
            and inputs['mathematical_driver'] == DRIVER and inputs['initial_integer_string_digit_limit'] == 4300
            and sys.get_int_max_str_digits() == 4300, 'same frozen driver and initial text policy required')
    for row in inputs['execution_sources']:
        base.captured(row, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing global consumer required')
    stopped = json.loads(base.captured(inputs['preserved_stopped_preflight'], pins))
    require(stopped['engineering_result_issued'] is False and stopped['exit_code'] == 1
            and stopped['inputs'] == inputs['preserved_v1_inputs'], 'preserved unissued v1 export stop required')
    base.captured(inputs['preserved_v1_inputs'], pins)
    with integer_text_policy(inputs['integer_string_digit_limit']):
        result = driver.run(inputs['preserved_v1_inputs'])
    require(sys.get_int_max_str_digits() == 4300, 'initial text policy must be restored')
    sizes = {key: list(map(len, result[key].split('/'))) for key in
             ('exact_dual_density_norm_square_upper', 'exact_full_metric_lower_for_every_registered_kernel_projection')}
    require(all(1 <= value <= 20000 for values in sizes.values() for value in values),
            'issued exact-fraction components must fit the declared text bound')
    for path, digest in result['source_sha256'].items():
        base.captured({'path': path, 'sha256': digest}, pins)
    for path, digest in tuple(pins.items()):
        base.captured({'path': path, 'sha256': digest}, pins)
    result.update(source_sha256=pins, consumer_inputs=reference,
                  execution_consumer={'path': str(OWN.relative_to(ROOT)), 'sha256': LOADED_SHA},
                  mathematical_execution_driver=DRIVER,
                  preserved_stopped_preflight=inputs['preserved_stopped_preflight'],
                  exact_fraction_text_policy={'initial_limit': 4300, 'scoped_limit': 20000, 'restored_limit': 4300,
                                              'unbounded_conversion_enabled': False},
                  exact_large_fraction_component_digit_counts=sizes,
                  mathematical_source_inputs_arithmetic_or_rounding_changed=False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); require(not args.out.exists(), 'preserve issued global-limit evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference); args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(),
                      'necessary_lower_endpoint_ceiling': result['necessary_lower_endpoint_ceiling']}))


if __name__ == '__main__':
    main()
