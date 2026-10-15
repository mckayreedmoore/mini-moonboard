"""Replayable column adapter for the preserved exact-scalar reaction consumer."""
from __future__ import annotations

import argparse
import hashlib
import json
from functools import cache, partial
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
V2 = {'path': 'scripts/eoere_normal_patch_reaction_consumer.py',
      'sha256': 'bd4f0fcb81de08ea6d0ba53912f1c590b1c4320c0661a1b53b724afe34665c8b'}


def captured(reference):
    path = (ROOT/reference['path']).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('repository source required')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != reference['sha256']:
        raise ValueError('source changed: '+reference['path'])
    return data


def replayable_gap(normalize, original, primal, columns, components, candidate, radius, movement):
    # Normalize once for the two preserved traversals; retain order/duplicates.
    return normalize(original, primal, tuple(columns), components, candidate, radius, movement)


@cache
def adapter():
    module = ModuleType('_eoere_verified_normal_reactions_v2')
    module.__file__ = str(ROOT/V2['path'])
    exec(compile(captured(V2), module.__file__, 'exec'), module.__dict__)  # noqa: S102 - pinned buffer
    if module.LOADED_SHA != V2['sha256']:
        raise ValueError('preserved exact-scalar consumer changed')
    module.exact_gap = partial(replayable_gap, module.exact_gap)
    return module


def run(reference):
    inputs = json.loads(captured(reference))
    own = {'path': str(OWN.relative_to(ROOT)), 'sha256': LOADED_SHA}
    if (inputs['execution_iterable_adapter_schema'] != 'eoere_continuous_normal_reaction_adapter/v3'
            or own not in inputs['execution_sources'] or V2 not in inputs['execution_sources']):
        raise ValueError('exact iterable adapter and preserved scalar consumer required')
    refs = (*inputs['execution_sources'], inputs['preserved_v2_inputs'], inputs['preserved_v2_result'], inputs['iterator_boundary_counterexample'])
    for ref in refs:
        captured(ref)
    result = adapter().run(reference)
    prior = json.loads(captured(inputs['preserved_v2_result']))
    for key in ('shared_material_box_records', 'shared_perturbed_rank_certificate', 'shared_exact_old_rigid_matrix_sha256',
                'shared_exact_new_rigid_matrix_sha256', 'cases'):
        if result[key] != prior[key]:
            raise ValueError('iterable adapter changed an issued engineering result: '+key)
    for ref in refs:
        captured(ref)
        result['source_sha256'][ref['path']] = ref['sha256']
    if hashlib.sha256(OWN.read_bytes()).hexdigest() != LOADED_SHA:
        raise ValueError('executing iterable adapter changed')
    result.update(schema='eoere_continuous_normal_reactions/v3', execution_driver=own,
                  iterable_input_adapter='Materialize columns once as a tuple before both exact-scalar traversals; retain order and duplicates.',
                  preserved_v2_inputs=inputs['preserved_v2_inputs'], preserved_v2_result=inputs['preserved_v2_result'],
                  iterator_boundary_counterexample=inputs['iterator_boundary_counterexample'],
                  all_issued_v2_engineering_rows_unchanged=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve issued continuous-normal reaction evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size, 'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
