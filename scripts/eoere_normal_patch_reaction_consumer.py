"""Exact scalar-input adapter for the preserved continuous-normal dual bound."""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction as F
from functools import cache, partial
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
V1 = {'path': 'scripts/eoere_normal_patch_reactions.py',
      'sha256': '2453ea37c5b6f36db193518ebf0e42cc09dc33d9ffc9f2e1d2f69854ed9fc3cd'}


def captured(reference):
    path = (ROOT/reference['path']).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('repository source required')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != reference['sha256']:
        raise ValueError('source changed: '+reference['path'])
    return data


def exact_gap(original, primal, columns, components, candidate, radius, movement):
    """Normalize before any quotient; preserve the existing gap construction."""
    rows = list(components)
    for j in columns:
        rows[j] = dict(rows[j], stiffness=F(rows[j]['stiffness']))
    return original(F(primal), columns, rows, list(map(F, candidate)), list(map(F, radius)), list(map(F, movement)))


@cache
def producer():
    module = ModuleType('_eoere_verified_normal_reactions_v1')
    module.__file__ = str(ROOT/V1['path'])
    exec(compile(captured(V1), module.__file__, 'exec'), module.__dict__)  # noqa: S102 - pinned source buffer
    if module.LOADED_SHA != V1['sha256']:
        raise ValueError('preserved producer changed')
    module.distributed_gap = partial(exact_gap, module.distributed_gap)
    return module


def run(reference):
    inputs = json.loads(captured(reference))
    own = {'path': str(OWN.relative_to(ROOT)), 'sha256': LOADED_SHA}
    if (inputs['execution_adapter_schema'] != 'eoere_continuous_normal_reaction_adapter/v2'
            or own not in inputs['execution_sources'] or V1 not in inputs['execution_sources']):
        raise ValueError('exact scalar adapter and preserved producer required')
    refs = (*inputs['execution_sources'], inputs['preserved_v1_inputs'], inputs['preserved_v1_result'], inputs['integer_boundary_counterexample'])
    for ref in refs:
        captured(ref)
    result = producer().run(reference)
    prior = json.loads(captured(inputs['preserved_v1_result']))
    for key in ('shared_material_box_records', 'shared_perturbed_rank_certificate', 'shared_exact_old_rigid_matrix_sha256',
                'shared_exact_new_rigid_matrix_sha256', 'cases'):
        if result[key] != prior[key]:
            raise ValueError('exact input adapter changed an issued engineering result: '+key)
    for ref in refs:
        captured(ref)
        result['source_sha256'][ref['path']] = ref['sha256']
    if hashlib.sha256(OWN.read_bytes()).hexdigest() != LOADED_SHA:
        raise ValueError('executing scalar adapter changed')
    result.update(schema='eoere_continuous_normal_reactions/v2', execution_driver=own,
                  scalar_input_adapter='Normalize primal, stiffness, candidate, radius and movement to exact Fractions before the preserved distributed gap.',
                  preserved_v1_inputs=inputs['preserved_v1_inputs'], preserved_v1_result=inputs['preserved_v1_result'],
                  integer_boundary_counterexample=inputs['integer_boundary_counterexample'],
                  all_issued_v1_engineering_rows_unchanged=True)
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
