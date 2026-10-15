"""Retain exact floor remainders in the frozen equilibrium-functional driver."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BASE = {'path': 'scripts/eoere_normal_patch_functionals.py',
        'sha256': '221bd5ff7313815cac7cc61825403187e32e95ab8c6fc9ba14f8a6b17c189d07'}
EXPRESSIONS = [('action[j] == -1', 'action[j] < 0'),
               ("components[j]['kind'] == 'common_shaft_bearing'",
                "components[j]['kind'] in ('common_shaft_bearing', 'floor_normal')")]
MESSAGES = [('exact downward-compression translation sign required', 'own downward-compression translation sign required'),
            ('this equivalent leg functional must use unchanged bearing laws only',
             'this equivalent leg functional must use unchanged bearing/floor laws only')]
SCOPE = ('schema', 'geometry_revision', 'hardware_revision', 'current_bolt_count', 'current_screw_count',
         'extra_grid', 'actual_observations', 'structural_acceptance', 'reaction_result', 'primary_methods')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def captured(reference, pins):
    path = (ROOT/reference['path']).resolve()
    require(path.is_relative_to(ROOT), 'repository source required')
    data = path.read_bytes(); digest = hashlib.sha256(data).hexdigest()
    require(digest == reference['sha256'] and pins.get(reference['path'], digest) == digest,
            'preserved functional source changed: '+reference['path'])
    pins[reference['path']] = digest
    return data


def rewrite(tree, *, reverse=False):
    pairs = [(ast.parse(a, mode='eval').body, ast.parse(b, mode='eval').body) for a, b in EXPRESSIONS]
    pairs += [(ast.Constant(a), ast.Constant(b)) for a, b in MESSAGES]
    if reverse:
        pairs = [(b, a) for a, b in pairs]
    replacements = {ast.dump(a): (i, b) for i, (a, b) in enumerate(pairs)}
    counts = [0]*len(pairs)
    class Gates(ast.NodeTransformer):
        def visit_Compare(self, node):
            self.generic_visit(node)
            return self.replace(node)
        def visit_Constant(self, node):
            return self.replace(node)
        def replace(self, node):
            found = replacements.get(ast.dump(node))
            if found is None:
                return node
            i, replacement = found; counts[i] += 1
            return ast.copy_location(replacement, node)
    result = Gates().visit(tree)
    require(counts == [1, 1, 1, 1], 'exactly two declared gates and two messages must change')
    return ast.fix_missing_locations(result)


def producer(pins):
    data = captured(BASE, pins)
    module = ModuleType('_eoere_verified_functional_remainder_driver')
    module.__file__ = str(ROOT/BASE['path'])
    exec(compile(rewrite(ast.parse(data)), module.__file__, 'exec'), module.__dict__)  # noqa: S102 - pinned two-gate delta
    return module


def same_scope(inputs, original):
    require(all(inputs[key] == original[key] for key in SCOPE), 'same frozen functional scope and gap source required')
    require(all(row in inputs['execution_sources'] for row in original['execution_sources']),
            'all preserved execution references required')


def run(reference):
    pins = {}; driver = producer(pins)
    inputs = json.loads(captured(reference, pins))
    require(inputs['consumer_schema'] == 'eoere_equilibrium_functional_exact_remainders/v2', 'declared exact-remainder consumer required')
    original = json.loads(captured(inputs['preserved_v1_inputs'], pins))
    same_scope(inputs, original)
    stopped = json.loads(captured(inputs['preserved_stopped_preflight'], pins))
    require(stopped['engineering_result_issued'] is False
            and stopped['inputs']['path'] == inputs['preserved_v1_inputs']['path']
            and stopped['inputs']['sha256'] == inputs['preserved_v1_inputs']['sha256'],
            'preserved own stopped preflight required')
    for ref in inputs['execution_sources']:
        captured(ref, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing remainder adapter required')
    result = driver.run(reference)
    for path, digest in result['source_sha256'].items():
        captured({'path': path, 'sha256': digest}, pins)
    result.update({'schema': 'eoere_continuous_normal_equilibrium_functionals/v2', 'source_sha256': pins,
                   'execution_driver': {'path': str(OWN.relative_to(ROOT)), 'sha256': LOADED_SHA},
                   'transformed_driver_source': BASE, 'preserved_v1_inputs': inputs['preserved_v1_inputs'],
                   'preserved_stopped_preflight': inputs['preserved_stopped_preflight'],
                   'verified_AST_delta': {'expressions': EXPRESSIONS, 'messages': MESSAGES},
                   'all_nonzero_transformed_coefficients_retained': True})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'preserve issued exact-remainder functional evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(),
                      'positive_leg_resultants_certified': result['positive_leg_resultants_certified']}))


if __name__ == '__main__':
    main()
