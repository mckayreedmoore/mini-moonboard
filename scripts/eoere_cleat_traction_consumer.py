"""Exact scenario adapter for the preserved continuous-traction certificate."""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction as F
from functools import cache
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
V1_PATH = 'scripts/eoere_cleat_traction_witness.py'
V1_SHA = '941cdd505e60e0e4275aa3b71fb5434d80d26a2f1c8d8f0ec96a6d87f5ae8dce'


def captured(reference):
    path = (ROOT/reference['path']).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('repository source required')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != reference['sha256']:
        raise ValueError('source buffer changed: '+reference['path'])
    return data


def exact_positive(value):
    if isinstance(value, bool):
        raise TypeError('positive exact real scenario required')
    try:
        result = F(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError('positive exact real scenario required') from exc
    if result <= 0:
        raise ValueError('positive exact real scenario required')
    return result


@cache
def _producer():
    data = captured({'path': V1_PATH, 'sha256': V1_SHA})
    module = ModuleType('_eoere_verified_traction_v1')
    module.__file__ = str(ROOT/V1_PATH)
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102 - verified repository buffer
    module.LOADED_SHA = V1_SHA
    original = module.certify

    def exact_certify(band, degrees, quarter, interval, method, divisor=F(2), load_factor=F(1)):
        return original(band, degrees, quarter, interval, method,
                        exact_positive(divisor), exact_positive(load_factor))

    module.certify = exact_certify
    return module


def certify(band, degrees, quarter, interval, method, divisor=F(2), load_factor=F(1)):
    return _producer().certify(band, degrees, quarter, interval, method, divisor, load_factor)


def run(reference):
    inputs = json.loads(captured(reference))
    own = str(OWN.relative_to(ROOT))
    refs = {r['path']: r['sha256'] for r in inputs['execution_sources']}
    if refs.get(own) != LOADED_SHA or refs.get(V1_PATH) != V1_SHA:
        raise ValueError('exact executing driver and preserved producer required')
    result = _producer().run(reference)
    old = json.loads(captured(inputs['preserved_v1_result']))
    captured(inputs['preserved_v1_inputs'])
    for key in ('rows', 'summary', 'geometry_revision', 'hardware_revision', 'current_bolt_count', 'current_screw_count'):
        if result[key] != old[key]:
            raise ValueError('exact-scenario adapter changed current result: '+key)
    for key in ('preserved_v1_inputs', 'preserved_v1_result', 'threshold_counterexample'):
        captured(inputs[key])
        result['source_sha256'][inputs[key]['path']] = inputs[key]['sha256']
    result['execution_driver'] = {'path': own, 'sha256': LOADED_SHA}
    result['exact_scenario_binding'] = 'All divisor/load factors become positive exact Fractions before certificate arithmetic; float arguments retain their stored binary values.'
    result['preserved_v1_rows_and_summaries_equal'] = True
    if hashlib.sha256(OWN.read_bytes()).hexdigest() != LOADED_SHA:
        raise ValueError('executing driver changed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve issued boundary-witness evidence')
    data = args.inputs.read_bytes()
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest()}
    result = run(reference)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(), 'comparisons': len(result['rows'])}))


if __name__ == '__main__':
    main()
